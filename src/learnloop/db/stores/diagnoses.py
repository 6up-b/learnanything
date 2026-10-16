"""Slice 1 M2 persistence: blind grades, diagnoses, card taps and the job queue.

Everything here is a persisted input or a receipt. Replay reads the ledgers and
never calls a model (S7). Two pure helpers merge a diagnosis's stored causal
view into the error-event and feedback-metadata rows the causal consumers
read; the view itself is computed once by the diagnosis domain
(``diagnosis.split.live``) when the diagnosis is persisted, so this layer only
copies stored fields and never interprets a proposal.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from datetime import timedelta
from typing import Any

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.ids import new_ulid

#: Error-event keys a causal view may set (everything else stays grader-owned).
_EVENT_VIEW_KEYS = (
    "is_misconception",
    "misconception_statement",
    "misconception_consistent_answer",
    "registry_match",
    "causal_class",
)


def _dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _loads(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def merge_causal_view_into_events(
    events: Sequence[Mapping[str, Any]],
    view: Mapping[str, Any] | None,
    *,
    diagnosis_id: str | None = None,
) -> list[dict[str, Any]]:
    """Error events with a diagnosis's causal fields laid over them.

    Only events the view names (by error-event id) change; their grader-owned
    fields (error type, severity, targets, divergence, validity) are kept and
    the causal ones come from the diagnosis. ``None`` returns copies.
    """

    overlays = (view or {}).get("events") if isinstance(view, Mapping) else None
    merged: list[dict[str, Any]] = []
    for event in events:
        row = dict(event)
        overlay = overlays.get(str(row.get("id"))) if isinstance(overlays, Mapping) else None
        if isinstance(overlay, Mapping):
            for key in _EVENT_VIEW_KEYS:
                if key in overlay:
                    row[key] = overlay[key]
            plan = dict(row.get("repair_plan") or {}) if isinstance(row.get("repair_plan"), Mapping) else {}
            for key, value in (overlay.get("repair_plan") or {}).items():
                plan[key] = value
            row["repair_plan"] = plan or None
            row["diagnosis_id"] = diagnosis_id
        merged.append(row)
    return merged


def merge_causal_view_into_feedback(
    metadata: Mapping[str, Any] | None,
    view: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Feedback metadata whose repair suggestions come from the diagnosis."""

    if metadata is None:
        return None
    row = dict(metadata)
    if isinstance(view, Mapping) and isinstance(view.get("repair_suggestions"), list):
        row["repair_suggestions"] = [dict(value) for value in view["repair_suggestions"]]
    if isinstance(view, Mapping) and view.get("agent_run_id"):
        # The diagnoser's run generated these repairs and the hypotheses
        # materialized from them; the grading run stays in ``agent_run_id``.
        row["diagnosis_agent_run_id"] = view["agent_run_id"]
    return row


class DiagnosisStoreMixin:
    """Repository mixin; every method opens (or joins) one connection scope."""

    # -- blind grade records -------------------------------------------------

    def insert_blind_grade_record(
        self,
        *,
        attempt_id: str,
        agent_run_id: str | None,
        grading_prompt_version: str,
        output_schema_version: str,
        context_hash: str,
        record: Mapping[str, Any],
        supersedes_id: str | None = None,
        queue_diagnosis: bool | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Append a blind grade; a regrade's record also queues the diagnosis.

        ``queue_diagnosis`` defaults to "this record supersedes another" (the
        live practice door enqueues its own job through the post-attempt
        pipeline). A regrade passes True so its first blind record, too,
        queues the attempt's diagnosis in the same transaction.
        """

        record_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO blind_grade_records(
                    id, attempt_id, agent_run_id, grading_prompt_version,
                    output_schema_version, context_hash, record_json,
                    supersedes_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record_id, attempt_id, agent_run_id, grading_prompt_version,
                    output_schema_version, context_hash, _dumps(dict(record)),
                    supersedes_id, now,
                ),
            )
            if queue_diagnosis or (queue_diagnosis is None and supersedes_id is not None):
                # A superseding blind grade (a regrade) makes the attempt's
                # diagnosis stale: its diagnosis applies to the grade it read.
                # Re-queue it in the same transaction; the job decides whether
                # the new grade still needs one.
                completed = connection.execute(
                    "SELECT created_at FROM practice_attempts WHERE id = ?", (attempt_id,)
                ).fetchone()
                connection.execute(
                    """INSERT OR IGNORE INTO post_attempt_jobs(
                        id, attempt_id, kind, job_key, attempt_completed_at, state,
                        payload_json, created_at, updated_at
                    ) VALUES (?, ?, 'diagnose', ?, ?, 'queued', ?, ?, ?)""",
                    (
                        new_ulid(), attempt_id, f"{attempt_id}:{record_id}",
                        str(completed[0]) if completed is not None else now,
                        _dumps({"mode": "live", "blind_grade_record_id": record_id, "rediagnose": True}),
                        now, now,
                    ),
                )
            connection.commit()
        return record_id

    @staticmethod
    def _decode_blind_record(row: Any) -> dict[str, Any]:
        value = dict(row)
        value["record"] = _loads(value.pop("record_json"), {})
        return value

    def latest_blind_grade_record(self, attempt_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            # A pre-170 database (an attached copy, a historical fixture) has
            # no blind grades: every attempt in it is joint.
            if not _has_table(connection, "blind_grade_records"):
                return None
            row = connection.execute(
                "SELECT * FROM blind_grade_records WHERE attempt_id = ? "
                "ORDER BY created_at DESC, id DESC LIMIT 1",
                (attempt_id,),
            ).fetchone()
        return self._decode_blind_record(row) if row is not None else None

    def blind_record_max_points(self, attempt_id: str, agent_run_ids: Iterable[str]) -> int | None:
        """The maximum a grading recorded WITH its grade: the ``max_points`` of
        the attempt's latest blind record written by one of ``agent_run_ids``
        (the runs of one grading epoch), or None. Evidence rows store points
        awarded, never a maximum, so a blind record is the only place an epoch
        that cites no contract kept one (regrade contracts, mvp-0.26)."""

        runs = sorted({str(value) for value in agent_run_ids if value})
        if not runs:
            return None
        with self.connection() as connection:
            if not _has_table(connection, "blind_grade_records"):
                return None
            row = connection.execute(
                "SELECT * FROM blind_grade_records WHERE attempt_id = ? "
                f"AND agent_run_id IN ({','.join('?' for _ in runs)}) "
                "ORDER BY created_at DESC, id DESC LIMIT 1",
                (attempt_id, *runs),
            ).fetchone()
        if row is None:
            return None
        record = (self._decode_blind_record(row) or {}).get("record") or {}
        value = record.get("max_points") if isinstance(record, Mapping) else None
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            return None
        return int(value)

    def blind_graded_attempt_ids(self) -> set[str]:
        with self.connection() as connection:
            if not _has_table(connection, "blind_grade_records"):
                return set()
            return {
                str(row[0])
                for row in connection.execute("SELECT DISTINCT attempt_id FROM blind_grade_records")
            }

    def latest_blind_grade_records(self) -> dict[str, dict[str, Any]]:
        """attempt id -> its latest blind record (one ordered scan)."""

        with self.connection() as connection:
            return latest_blind_grade_rows(connection)

    # -- diagnoses -------------------------------------------------------------

    def insert_attempt_diagnosis(
        self,
        *,
        attempt_id: str,
        diagnosis_prompt_version: str,
        mode: str,
        history_mode: str,
        status: str,
        proposal: Mapping[str, Any] | None,
        causal_view: Mapping[str, Any] | None,
        validation_report: Mapping[str, Any] | None,
        receipt: Mapping[str, Any] | None,
        blind_grade_record_id: str | None = None,
        agent_run_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        error: str | None = None,
        latency_seconds: float | None = None,
        supersedes_id: str | None = None,
        diagnosis_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Append one diagnosis and (when given) its context receipt together."""

        diagnosis_id = diagnosis_id or new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO attempt_diagnoses(
                    id, attempt_id, blind_grade_record_id, agent_run_id,
                    diagnosis_prompt_version, provider, model, mode, history_mode,
                    status, proposal_json, causal_view_json, validation_report_json,
                    error, latency_seconds, supersedes_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    diagnosis_id, attempt_id, blind_grade_record_id, agent_run_id,
                    diagnosis_prompt_version, provider, model, mode, history_mode,
                    status,
                    _dumps(dict(proposal)) if proposal is not None else None,
                    _dumps(dict(causal_view)) if causal_view is not None else None,
                    _dumps(dict(validation_report or {})),
                    error, latency_seconds, supersedes_id, now,
                ),
            )
            if receipt is not None:
                connection.execute(
                    """INSERT INTO diagnosis_context_receipts(
                        id, diagnosis_id, context_hash, context_as_of_attempt_id,
                        lagged_attempts, failure_attempt_ids_json,
                        success_attempt_ids_json, hypothesis_ids_json,
                        registry_candidate_ids_json, prerequisite_refs_json,
                        retrieval_json, anchoring_suspect, validated_citations_json,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        new_ulid(), diagnosis_id, receipt.get("context_hash"),
                        receipt.get("context_as_of_attempt_id"),
                        receipt.get("lagged_attempts"),
                        _dumps(list(receipt.get("failure_attempt_ids") or [])),
                        _dumps(list(receipt.get("success_attempt_ids") or [])),
                        _dumps(list(receipt.get("hypothesis_ids") or [])),
                        _dumps(list(receipt.get("registry_candidate_ids") or [])),
                        _dumps(list(receipt.get("prerequisite_refs") or [])),
                        _dumps(dict(receipt.get("retrieval") or {})),
                        1 if receipt.get("anchoring_suspect") else 0,
                        _dumps(list(receipt.get("validated_citations") or [])),
                        now,
                    ),
                )
            connection.commit()
        return diagnosis_id

    @staticmethod
    def _decode_diagnosis(row: Any) -> dict[str, Any]:
        value = dict(row)
        value["proposal"] = _loads(value.pop("proposal_json"), None)
        value["causal_view"] = _loads(value.pop("causal_view_json"), None)
        value["validation_report"] = _loads(value.pop("validation_report_json"), {})
        return value

    def attempt_diagnoses_for_attempt(self, attempt_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            if not _has_table(connection, "attempt_diagnoses"):
                return []
            rows = connection.execute(
                "SELECT * FROM attempt_diagnoses WHERE attempt_id = ? ORDER BY created_at, id",
                (attempt_id,),
            ).fetchall()
        return [self._decode_diagnosis(row) for row in rows]

    def attempt_diagnosis(self, diagnosis_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM attempt_diagnoses WHERE id = ?", (diagnosis_id,)
            ).fetchone()
        return self._decode_diagnosis(row) if row is not None else None

    def latest_attempt_diagnosis(
        self,
        attempt_id: str,
        *,
        mode: str = "live",
        statuses: Iterable[str] | None = None,
    ) -> dict[str, Any] | None:
        wanted = tuple(statuses) if statuses is not None else None
        for row in reversed(self.attempt_diagnoses_for_attempt(attempt_id)):
            if row["mode"] != mode:
                continue
            if wanted is not None and row["status"] not in wanted:
                continue
            return row
        return None

    @staticmethod
    def _diagnosis_in_force(status: Any, record_id: Any, current_record_id: str | None) -> bool:
        """THE eligibility rule for a live diagnosis (one rule for every reader).

        The row must be the attempt's LATEST live diagnosis (the callers pick
        it) and it must have completed for the attempt's CURRENT blind grade:
        after a regrade (a superseding blind record) the old explanation no
        longer applies, and a later failed or skipped diagnosis retires it too;
        nothing applies until a new diagnosis of the current grade completes.
        """

        if status != "completed":
            return False
        return DiagnosisStoreMixin._diagnosis_concerns_grade(record_id, current_record_id)

    @staticmethod
    def _diagnosis_concerns_grade(record_id: Any, current_record_id: str | None) -> bool:
        """Whether a diagnosis row read the blind grade ``current_record_id``
        (the half of :meth:`_diagnosis_in_force` that does not look at status).
        Placement asks it of a row against the grade current when the row
        landed, to decide each miss once."""

        return record_id is None or current_record_id in (None, str(record_id))

    def current_live_diagnosis(self, attempt_id: str) -> dict[str, Any] | None:
        """The live diagnosis in force for an attempt, decoded, or None.

        Used by ``diagnosis_for_attempt`` and by the overlays (through
        :meth:`_live_views`), so the public accessor and the serving reads can
        never disagree.
        """

        with self.connection() as connection:
            if not _has_table(connection, "attempt_diagnoses"):
                return None
            row = connection.execute(
                "SELECT * FROM attempt_diagnoses WHERE attempt_id = ? AND mode = 'live' "
                "ORDER BY created_at DESC, id DESC LIMIT 1",
                (attempt_id,),
            ).fetchone()
            if row is None:
                return None
            current = connection.execute(
                "SELECT id FROM blind_grade_records WHERE attempt_id = ? "
                "ORDER BY created_at DESC, id DESC LIMIT 1",
                (attempt_id,),
            ).fetchone()
        if not self._diagnosis_in_force(
            row["status"], row["blind_grade_record_id"], str(current[0]) if current is not None else None
        ):
            return None
        return self._decode_diagnosis(row)

    def _live_views(self, connection: Any, attempt_ids: Sequence[str] | None) -> dict[str, tuple[str, dict[str, Any]]]:
        """The causal view in force per attempt (:meth:`_diagnosis_in_force`)."""

        query = (
            "SELECT id, attempt_id, status, blind_grade_record_id, causal_view_json "
            "FROM attempt_diagnoses WHERE mode = 'live'"
        )
        params: tuple[Any, ...] = ()
        if attempt_ids is not None:
            if not attempt_ids:
                return {}
            query += f" AND attempt_id IN ({', '.join('?' for _ in attempt_ids)})"
            params = tuple(attempt_ids)
        latest: dict[str, Any] = {}
        for row in connection.execute(query + " ORDER BY attempt_id, created_at, id", params):
            latest[str(row[1])] = row
        if not latest:
            return {}
        current: dict[str, str] = {}
        placeholders = ", ".join("?" for _ in latest)
        for row in connection.execute(
            f"SELECT attempt_id, id FROM blind_grade_records WHERE attempt_id IN ({placeholders}) "
            "ORDER BY attempt_id, created_at, id",
            tuple(latest),
        ):
            current[str(row[0])] = str(row[1])
        views: dict[str, tuple[str, dict[str, Any]]] = {}
        for attempt_id, row in latest.items():
            if row[4] is None or not self._diagnosis_in_force(row[2], row[3], current.get(attempt_id)):
                continue
            view = _loads(row[4], None)
            if isinstance(view, dict):
                views[attempt_id] = (str(row[0]), view)
        return views

    def live_causal_view(self, attempt_id: str) -> tuple[str, dict[str, Any]] | None:
        """(diagnosis id, causal view) of the latest completed live diagnosis."""

        with self.connection() as connection:
            if not _has_table(connection, "attempt_diagnoses"):
                return None
            return self._live_views(connection, [attempt_id]).get(attempt_id)

    def live_causal_views(
        self, attempt_ids: Iterable[str] | None = None
    ) -> dict[str, tuple[str, dict[str, Any]]]:
        """(diagnosis id, causal view) in force per attempt: for every attempt,
        or only for ``attempt_ids`` (batched: one diagnoses read and one
        blind-grade read for the whole batch, not one pair per attempt)."""

        ids = None if attempt_ids is None else sorted({str(value) for value in attempt_ids if value})
        if ids is not None and not ids:
            return {}
        with self.connection() as connection:
            if not _has_table(connection, "attempt_diagnoses"):
                return {}
            return self._live_views(connection, ids)

    def pending_live_diagnoses_for_active_errors(self, learning_object_ids: Iterable[str]) -> list[str]:
        """Attempts behind these LOs' active error events whose live diagnosis is pending.

        Pending is ``diagnosis_status``'s rule: an open (queued or leased)
        ``diagnose`` job in live mode. When it completes, the diagnosis overlay
        on those events changes, so a display that shows them (the Reader
        Guide) re-reads then. Shadow jobs never lay an overlay and failed ones
        never will, so neither is pending here. Sorted attempt ids, one read.
        """

        ids = sorted({str(value) for value in learning_object_ids if value})
        if not ids:
            return []
        with self.connection() as connection:
            if not _has_table(connection, "post_attempt_jobs"):
                return []
            rows = connection.execute(
                "SELECT DISTINCT job.attempt_id, job.payload_json FROM post_attempt_jobs AS job "
                "JOIN error_events AS event ON event.attempt_id = job.attempt_id "
                "WHERE job.kind = 'diagnose' AND job.state IN ('queued', 'leased') "
                "AND event.status = 'active' "
                f"AND event.learning_object_id IN ({', '.join('?' for _ in ids)})",
                tuple(ids),
            ).fetchall()
        pending: set[str] = set()
        for attempt_id, payload_json in rows:
            payload = _loads(payload_json, {})
            if (payload if isinstance(payload, dict) else {}).get("mode", "live") == "live":
                pending.add(str(attempt_id))
        return sorted(pending)

    def diagnosis_context_receipt(self, diagnosis_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM diagnosis_context_receipts WHERE diagnosis_id = ?",
                (diagnosis_id,),
            ).fetchone()
        if row is None:
            return None
        value = dict(row)
        for key in (
            "failure_attempt_ids",
            "success_attempt_ids",
            "hypothesis_ids",
            "registry_candidate_ids",
            "prerequisite_refs",
            "validated_citations",
        ):
            value[key] = _loads(value.pop(f"{key}_json"), [])
        value["retrieval"] = _loads(value.pop("retrieval_json"), {})
        value["anchoring_suspect"] = bool(value["anchoring_suspect"])
        return value

    def diagnosis_calls_since(self, since_iso: str) -> int:
        """Diagnoser calls ADMITTED since ``since_iso``, failures included.

        Counted at admission, not from the diagnosis ledger: every live
        diagnosis call opens its ``agent_runs`` row (purpose ``diagnosis``)
        before the request is sent, so a call that fails and backs off counts
        even though its diagnosis row is written only on the final attempt. A
        run refused or cancelled before anything was sent is ``cancelled`` and
        does not count.
        """

        with self.connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM agent_runs "
                "WHERE purpose = 'diagnosis' AND started_at >= ? AND status != 'cancelled'",
                (since_iso,),
            ).fetchone()
        return int(row[0] or 0)

    def all_attempt_diagnoses(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM attempt_diagnoses ORDER BY created_at, id"
            ).fetchall()
        return [self._decode_diagnosis(row) for row in rows]

    # -- card feedback -----------------------------------------------------------

    def insert_diagnosis_feedback(
        self,
        *,
        diagnosis_id: str,
        attempt_id: str,
        response: str,
        cited_attempt_id: str | None = None,
        forwarded_factor_id: str | None = None,
        shown_at: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        feedback_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO diagnosis_feedback(
                    id, diagnosis_id, attempt_id, response, cited_attempt_id,
                    forwarded_factor_id, shown_at, responded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    feedback_id, diagnosis_id, attempt_id, response, cited_attempt_id,
                    forwarded_factor_id, shown_at, utc_now_iso(clock),
                ),
            )
            connection.commit()
        return feedback_id

    def diagnosis_feedback_rows(self, diagnosis_id: str | None = None) -> list[dict[str, Any]]:
        with self.connection() as connection:
            if diagnosis_id is None:
                rows = connection.execute(
                    "SELECT * FROM diagnosis_feedback ORDER BY responded_at, id"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM diagnosis_feedback WHERE diagnosis_id = ? ORDER BY responded_at, id",
                    (diagnosis_id,),
                ).fetchall()
        return [dict(row) for row in rows]

    # -- would-merge log and wait receipts --------------------------------------

    def insert_would_merge(
        self,
        *,
        diagnosis_id: str | None,
        hypothesis_id: str,
        model_id: str,
        exact_key: str,
        exact_group_ids: Sequence[str],
        neighbors: Sequence[Mapping[str, Any]],
        clock: Clock | None = None,
    ) -> str | None:
        row_id = new_ulid()
        with self.connection() as connection:
            cursor = connection.execute(
                """INSERT OR IGNORE INTO diagnosis_would_merge_log(
                    id, diagnosis_id, hypothesis_id, model_id, exact_key,
                    exact_group_ids_json, neighbors_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row_id, diagnosis_id, hypothesis_id, model_id, exact_key,
                    _dumps(list(exact_group_ids)), _dumps([dict(value) for value in neighbors]),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return row_id if cursor.rowcount else None

    def would_merge_rows(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM diagnosis_would_merge_log ORDER BY created_at, id"
            ).fetchall()
        out = []
        for row in rows:
            value = dict(row)
            value["exact_group_ids"] = _loads(value.pop("exact_group_ids_json"), [])
            value["neighbors"] = _loads(value.pop("neighbors_json"), [])
            out.append(value)
        return out

    def insert_diagnosis_wait_receipt(
        self,
        *,
        session_id: str | None,
        pending_attempt_ids: Sequence[str],
        waited_seconds: float,
        served_without_diagnosis: bool,
        clock: Clock | None = None,
    ) -> str:
        row_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO diagnosis_wait_receipts(
                    id, session_id, pending_attempt_ids_json, waited_seconds,
                    served_without_diagnosis, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    row_id, session_id, _dumps(list(pending_attempt_ids)),
                    round(float(waited_seconds), 3), 1 if served_without_diagnosis else 0,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return row_id

    def diagnosis_wait_receipts(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM diagnosis_wait_receipts ORDER BY created_at, id"
            ).fetchall()
        out = []
        for row in rows:
            value = dict(row)
            value["pending_attempt_ids"] = _loads(value.pop("pending_attempt_ids_json"), [])
            value["served_without_diagnosis"] = bool(value["served_without_diagnosis"])
            out.append(value)
        return out

    # -- the post-attempt job queue ------------------------------------------------

    @staticmethod
    def _decode_job(row: Any) -> dict[str, Any]:
        value = dict(row)
        value["payload"] = _loads(value.pop("payload_json"), {})
        return value

    def enqueue_post_attempt_job(
        self,
        *,
        attempt_id: str,
        kind: str,
        job_key: str,
        attempt_completed_at: str,
        payload: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> str | None:
        """Insert a queued job once per ``(kind, job_key)``; returns its id when new."""

        job_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """INSERT OR IGNORE INTO post_attempt_jobs(
                    id, attempt_id, kind, job_key, attempt_completed_at, state,
                    payload_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'queued', ?, ?, ?)""",
                (
                    job_id, attempt_id, kind, job_key, attempt_completed_at,
                    _dumps(dict(payload or {})), now, now,
                ),
            )
            connection.commit()
        return job_id if cursor.rowcount else None

    def post_attempt_job(self, job_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM post_attempt_jobs WHERE id = ?", (job_id,)
            ).fetchone()
        return self._decode_job(row) if row is not None else None

    def post_attempt_jobs(
        self,
        *,
        attempt_id: str | None = None,
        kind: str | None = None,
        states: Iterable[str] | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if attempt_id is not None:
            clauses.append("attempt_id = ?")
            params.append(attempt_id)
        if kind is not None:
            clauses.append("kind = ?")
            params.append(kind)
        wanted = list(states) if states is not None else None
        if wanted is not None:
            clauses.append(f"state IN ({', '.join('?' for _ in wanted)})")
            params.extend(wanted)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connection() as connection:
            if not _has_table(connection, "post_attempt_jobs"):
                return []
            rows = connection.execute(
                f"SELECT * FROM post_attempt_jobs {where} "
                "ORDER BY attempt_completed_at, attempt_id, created_at, id",
                tuple(params),
            ).fetchall()
        return [self._decode_job(row) for row in rows]

    def lease_next_post_attempt_job(
        self,
        *,
        kind: str,
        owner: str,
        lease_seconds: float,
        clock: Clock | None = None,
        attempt_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Claim the next runnable job, or None.

        ``diagnose`` jobs run one at a time, strictly in attempt-completion
        order: while ANY diagnose job holds an unexpired lease nothing else is
        claimed (a regrade or retry can queue an earlier attempt ahead of the
        running one, so the head alone would not show it); otherwise only the
        head of the line can be claimed, and a head that is backing off blocks
        the jobs behind it. ``embed`` jobs are unordered. ``attempt_id``
        restricts the claim to one attempt's job and still respects the line
        (an earlier unfinished diagnosis blocks it).
        """

        now_iso = utc_now_iso(clock)
        now = parse_utc(now_iso)
        with self.atomic():
            connection = self.connection()
            rows = connection.execute(
                "SELECT * FROM post_attempt_jobs WHERE kind = ? AND state IN ('queued', 'leased') "
                "ORDER BY attempt_completed_at, attempt_id, created_at, id",
                (kind,),
            ).fetchall()
            if kind == "diagnose" and any(
                row["state"] == "leased"
                and row["lease_expires_at"]
                and parse_utc(row["lease_expires_at"]) > now
                for row in rows
            ):
                return None
            chosen = None
            for row in rows:
                lease_expires = parse_utc(row["lease_expires_at"]) if row["lease_expires_at"] else None
                not_before = parse_utc(row["not_before"]) if row["not_before"] else None
                runnable = (
                    row["state"] == "queued" and (not_before is None or not_before <= now)
                ) or (row["state"] == "leased" and (lease_expires is None or lease_expires <= now))
                if kind == "diagnose":
                    # The head of the line decides: nothing behind it may run.
                    if runnable and (attempt_id is None or row["attempt_id"] == attempt_id):
                        chosen = row
                    break
                if runnable and (attempt_id is None or row["attempt_id"] == attempt_id):
                    chosen = row
                    break
            if chosen is None:
                return None
            expires = (now + timedelta(seconds=float(lease_seconds))).replace(microsecond=0)
            connection.execute(
                """UPDATE post_attempt_jobs
                   SET state = 'leased', lease_owner = ?, lease_expires_at = ?,
                       lease_epoch = lease_epoch + 1, attempt_count = attempt_count + 1,
                       updated_at = ?
                   WHERE id = ? AND lease_epoch = ?""",
                (
                    owner,
                    expires.isoformat().replace("+00:00", "Z"),
                    now_iso,
                    chosen["id"],
                    chosen["lease_epoch"],
                ),
            )
            leased = connection.execute(
                "SELECT * FROM post_attempt_jobs WHERE id = ?", (chosen["id"],)
            ).fetchone()
        return self._decode_job(leased)

    def renew_post_attempt_lease(
        self, job_id: str, *, epoch: int, lease_seconds: float, clock: Clock | None = None
    ) -> bool:
        now = parse_utc(utc_now_iso(clock))
        expires = (now + timedelta(seconds=float(lease_seconds))).isoformat().replace("+00:00", "Z")
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE post_attempt_jobs SET lease_expires_at = ?, updated_at = ? "
                "WHERE id = ? AND lease_epoch = ? AND state = 'leased'",
                (expires, utc_now_iso(clock), job_id, epoch),
            )
            connection.commit()
            return cursor.rowcount > 0

    def owns_post_attempt_job(self, job_id: str, *, epoch: int) -> bool:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT 1 FROM post_attempt_jobs WHERE id = ? AND lease_epoch = ? AND state = 'leased'",
                (job_id, epoch),
            ).fetchone()
        return row is not None

    def finish_post_attempt_job(
        self,
        job_id: str,
        *,
        epoch: int,
        state: str,
        last_error: str | None = None,
        payload: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> bool:
        """Settle a leased job; a superseded lease writes nothing (fencing)."""

        if state not in {"done", "failed", "skipped"}:
            raise ValueError(f"cannot finish a job as {state!r}")
        with self.connection() as connection:
            cursor = connection.execute(
                """UPDATE post_attempt_jobs
                   SET state = ?, last_error = ?, lease_owner = NULL, lease_expires_at = NULL,
                       payload_json = COALESCE(?, payload_json), updated_at = ?
                   WHERE id = ? AND lease_epoch = ? AND state = 'leased'""",
                (
                    state, last_error,
                    _dumps(dict(payload)) if payload is not None else None,
                    utc_now_iso(clock), job_id, epoch,
                ),
            )
            connection.commit()
            return cursor.rowcount > 0

    def release_post_attempt_job(
        self,
        job_id: str,
        *,
        epoch: int,
        not_before: str | None,
        last_error: str | None = None,
        refund_attempt: bool = False,
        clock: Clock | None = None,
    ) -> bool:
        """Return a leased job to the queue (backoff, or provider not ready)."""

        with self.connection() as connection:
            cursor = connection.execute(
                f"""UPDATE post_attempt_jobs
                   SET state = 'queued', lease_owner = NULL, lease_expires_at = NULL,
                       not_before = ?, last_error = ?, updated_at = ?
                       {', attempt_count = MAX(attempt_count - 1, 0)' if refund_attempt else ''}
                   WHERE id = ? AND lease_epoch = ? AND state = 'leased'""",
                (not_before, last_error, utc_now_iso(clock), job_id, epoch),
            )
            connection.commit()
            return cursor.rowcount > 0

    def hold_queued_live_diagnoses(self, *, clock: Clock | None = None) -> int:
        """Stamp each queued LIVE diagnose job ``payload.split_held_at = now``.

        Called when the diagnosis split cannot run (its kill switch is off):
        the stamp records that the job was held, once. It is write-once (a
        stamped job is never stamped again, and nothing clears or moves it),
        it survives every later release, lease, settle and owner requeue (they
        keep ``payload_json``), and job rows are never deleted. Only ``queued``
        rows are stamped: a leased row's settle rewrites the payload it leased.
        Placement decides a held miss at its first stamp
        (``placement.state.load_miss_verdicts``). Returns the rows stamped.
        """

        unheld = (
            "kind = 'diagnose' AND state = 'queued' "
            "AND COALESCE(json_extract(payload_json, '$.mode'), 'live') = 'live' "
            "AND json_extract(payload_json, '$.split_held_at') IS NULL"
        )
        with self.connection() as connection:
            if not _has_table(connection, "post_attempt_jobs"):
                return 0
            # Read first: the worker's idle poll and every serving build call
            # this while the switch is off, and most find nothing to stamp.
            if connection.execute(f"SELECT 1 FROM post_attempt_jobs WHERE {unheld} LIMIT 1").fetchone() is None:
                return 0
            cursor = connection.execute(
                "UPDATE post_attempt_jobs "
                "SET payload_json = json_set(COALESCE(payload_json, '{}'), '$.split_held_at', ?) "
                f"WHERE {unheld}",
                (utc_now_iso(clock),),
            )
            connection.commit()
            return cursor.rowcount

    def requeue_post_attempt_job(self, job_id: str, *, clock: Clock | None = None) -> bool:
        """Owner retry: a settled job runs again with a fresh attempt count."""

        with self.connection() as connection:
            cursor = connection.execute(
                """UPDATE post_attempt_jobs
                   SET state = 'queued', attempt_count = 0, not_before = NULL,
                       lease_owner = NULL, lease_expires_at = NULL, updated_at = ?,
                       lease_epoch = lease_epoch + 1
                   WHERE id = ? AND state IN ('failed', 'skipped', 'done')""",
                (utc_now_iso(clock), job_id),
            )
            connection.commit()
            return cursor.rowcount > 0

    def pending_live_diagnoses_for_session(self, session_id: str) -> list[str]:
        """Attempts of this session whose LIVE diagnosis is queued or running."""

        with self.connection() as connection:
            if not _has_table(connection, "post_attempt_jobs"):
                return []
            rows = connection.execute(
                """SELECT j.attempt_id FROM post_attempt_jobs j
                   JOIN practice_attempts a ON a.id = j.attempt_id
                   WHERE j.kind = 'diagnose' AND j.state IN ('queued', 'leased')
                     AND a.session_id = ?
                     AND COALESCE(json_extract(j.payload_json, '$.mode'), 'live') = 'live'
                   ORDER BY j.attempt_completed_at, j.attempt_id""",
                (session_id,),
            ).fetchall()
        return [str(row[0]) for row in rows]

    def live_diagnosis_jobs_for_session(self, session_id: str) -> list[dict[str, Any]]:
        """Every LIVE diagnose job of this session's attempts, any state (E7 population)."""

        with self.connection() as connection:
            if not _has_table(connection, "post_attempt_jobs"):
                return []
            rows = connection.execute(
                """SELECT j.attempt_id, j.state FROM post_attempt_jobs j
                   JOIN practice_attempts a ON a.id = j.attempt_id
                   WHERE j.kind = 'diagnose' AND a.session_id = ?
                     AND COALESCE(json_extract(j.payload_json, '$.mode'), 'live') = 'live'
                   ORDER BY j.attempt_completed_at, j.attempt_id, j.created_at, j.id""",
                (session_id,),
            ).fetchall()
        return [{"attempt_id": str(row[0]), "state": str(row[1])} for row in rows]

    def post_attempt_job_counts(self) -> dict[str, dict[str, int]]:
        with self.connection() as connection:
            if not _has_table(connection, "post_attempt_jobs"):
                return {}
            counts: dict[str, dict[str, int]] = {}
            for row in connection.execute(
                "SELECT kind, state, COUNT(*) FROM post_attempt_jobs GROUP BY kind, state"
            ):
                counts.setdefault(str(row[0]), {})[str(row[1])] = int(row[2])
        return counts


def _has_table(connection: Any, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone() is not None


def latest_blind_grade_rows(connection: Any) -> dict[str, dict[str, Any]]:
    """attempt id -> its latest blind record, on the caller's connection (one
    ordered scan; a caller can read it in the same snapshot as other rows)."""

    latest: dict[str, dict[str, Any]] = {}
    if not _has_table(connection, "blind_grade_records"):
        return latest
    rows = connection.execute(
        "SELECT * FROM blind_grade_records ORDER BY attempt_id, created_at, id"
    ).fetchall()
    for row in rows:
        latest[str(row["attempt_id"])] = DiagnosisStoreMixin._decode_blind_record(row)
    return latest


__all__ = [
    "DiagnosisStoreMixin",
    "latest_blind_grade_rows",
    "merge_causal_view_into_events",
    "merge_causal_view_into_feedback",
]
