"""Practice attempts, assessment contracts and cold-check receipts.

Owns attempt grading evidence and outcome labels, assessment contracts, and cold outcomes."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from dataclasses import field  # noqa: F401  Keeps the moved field-shadowing directives valid.
from datetime import UTC, date, timedelta
from typing import Any, Iterable, Mapping, Sequence

from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.db.records import (
    ItemParameterState,
    MasteryState,
    PracticeItemState,
    _decode_attempt,
    _decode_learning_outcome_label,
    _decode_surprise,
    _projection_id,
)
from learnloop.db.attempt_order import (
    APPLICATION_ORDER_TABLE,
    BASIS_APPLIED,
    BASIS_LEGACY_ORDER_UNKNOWN,
    LEGACY_ORDER,
    AttemptOrder,
)
from learnloop.db.attempt_lifecycle_inputs import LIFECYCLE_INPUTS_TABLE, LifecycleInputs
from learnloop.db.mastery_seed_inputs import MasterySeedInputs
from learnloop.db.stores.practice_state import insert_mastery_seed_inputs
from learnloop.db.row_serialization import _json, _loads
from learnloop.db.stores.diagnoses import merge_causal_view_into_feedback
from learnloop.db.stores.observation_ledger import load_effective_assessment_contracts
from learnloop.ids import new_ulid
from learnloop.outcome_contract import LABEL_VERSION


#: The code points ``str.isspace`` accepts, the whitespace an import's
#: ``answer_md.strip()`` removes when it decides an outcome is score-only.
#: SQLite's one-argument ``trim`` removes spaces only, so an old answer of
#: "\t\n" would read as learner work. ``tests/test_deferred_regrade.py`` pins the
#: list to Python's.
PYTHON_WHITESPACE_CODE_POINTS = (
    9, 10, 11, 12, 13, 28, 29, 30, 31, 32, 133, 160, 5760,
    8192, 8193, 8194, 8195, 8196, 8197, 8198, 8199, 8200, 8201, 8202,
    8232, 8233, 8239, 8287, 12288,
)
_PYTHON_WHITESPACE_SQL = "char(" + ", ".join(str(point) for point in PYTHON_WHITESPACE_CODE_POINTS) + ")"

# Only imports predating the work/score record need the answer-text fallback.
_EXAM_IMPORT_HAS_WORK = f"""(
    e.notes = 'learner_work'
    OR (e.notes IS NULL AND trim(a.learner_answer_md, {_PYTHON_WHITESPACE_SQL}) != ''
        AND a.learner_answer_md NOT LIKE '[imported exam outcome: score %]')
)"""


@dataclass(frozen=True)
class GradingEvidenceRecord:
    id: str
    attempt_id: str
    criterion_id: str
    points_awarded: float
    evidence: str | None
    notes: str | None
    grader_tier: int
    local_grader_id: str | None
    agent_run_id: str | None
    learner_confidence: str | None
    created_at: str
    superseded_at: str | None
    # Ruling A: the supersession pointer is the ledger's audit trail — which
    # revision replaced this row as the directional authority.
    superseded_by_evidence_id: str | None = None
    # KM1 observation lineage (§5.2); NULL on legacy rows and under mvp-0.6.
    observation_id: str | None = None
    grading_revision: int | None = None
    assessment_contract_version_id: str | None = None
    recipe_id: str | None = None
    attribution_json: str | None = None
    correlation_group: str | None = None


def _required_observation_scope(row: Mapping[str, Any]) -> str:
    """An A6 observation's scope, which the caller must state (Meas §3.A6)."""

    scope = row.get("observation_scope")
    if scope not in ("declared", "opportunistic"):
        raise ValueError(
            "trace-exercised facet rows must declare observation_scope "
            f"('declared' or 'opportunistic'); got {scope!r}"
        )
    return str(scope)


def _grading_evidence(row: sqlite3.Row) -> GradingEvidenceRecord:
    return GradingEvidenceRecord(
        id=row["id"],
        attempt_id=row["attempt_id"],
        criterion_id=row["criterion_id"],
        points_awarded=row["points_awarded"],
        evidence=row["evidence"],
        notes=row["notes"],
        grader_tier=row["grader_tier"],
        local_grader_id=row["local_grader_id"],
        agent_run_id=row["agent_run_id"],
        learner_confidence=row["learner_confidence"] if "learner_confidence" in row.keys() else None,
        created_at=row["created_at"],
        superseded_at=row["superseded_at"],
        superseded_by_evidence_id=(
            row["superseded_by_evidence_id"]
            if "superseded_by_evidence_id" in row.keys()
            else None
        ),
        observation_id=row["observation_id"] if "observation_id" in row.keys() else None,
        grading_revision=row["grading_revision"] if "grading_revision" in row.keys() else None,
        assessment_contract_version_id=(
            row["assessment_contract_version_id"]
            if "assessment_contract_version_id" in row.keys()
            else None
        ),
        recipe_id=row["recipe_id"] if "recipe_id" in row.keys() else None,
        attribution_json=row["attribution_json"] if "attribution_json" in row.keys() else None,
        correlation_group=row["correlation_group"] if "correlation_group" in row.keys() else None,
    )


def _decode_certification_cold_probe_outcome(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["certificate_receipt"] = _loads(payload.pop("certificate_receipt_json"), None)
    payload["excluded_surface_groups"] = _loads(
        payload.pop("excluded_surface_groups_json"), []
    )
    payload["avoided_affordances"] = _loads(payload.pop("avoided_affordances_json"), [])
    payload["parameters"] = _loads(payload.pop("parameters_json"), None)
    # `success` stays tri-state: True / False / None on the abstention arm. A
    # bool() here would launder "not measured" into "failed", which is the exact
    # collapse `false_certification_rate` exists to prevent (§5.7).
    raw_success = payload.get("success")
    payload["success"] = None if raw_success is None else bool(raw_success)
    payload["assisted"] = bool(payload["assisted"])
    return payload


def _decode_attempt_feedback_metadata(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["fatal_errors"] = _loads(payload.pop("fatal_errors_json"), [])
    payload["repair_suggestions"] = _loads(payload.pop("repair_suggestions_json"), [])
    return payload


def _elapsed_seconds_between(start: str | None, end: str | None) -> int | None:
    parsed_start = parse_utc(start)
    parsed_end = parse_utc(end)
    if parsed_start is None or parsed_end is None:
        return None
    return max(0, int((parsed_end - parsed_start).total_seconds()))


def _attempt_label_snapshot(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "attempt_id": row["id"],
        "session_id": row["session_id"],
        "scheduler_slate_id": row["scheduler_slate_id"],
        "scheduler_candidate_id": row["scheduler_candidate_id"],
        "practice_item_id": row["practice_item_id"],
        "learning_object_id": row["learning_object_id"],
        "attempt_type": row["attempt_type"],
        "rubric_score": row["rubric_score"],
        "correctness": row["correctness"],
        "hints_used": row["hints_used"],
        "primed": row["primed"],
        "manual_review": row["manual_review"],
        "collection_version": row["collection_version"],
        "entry_surface": row["entry_surface"],
        "evidence_origin": row["evidence_origin"],
        "latency_seconds": row["latency_seconds"],
        "created_at": row["created_at"],
    }


def reserve_application_sequence(
    connection: Any, attempt_id: str, *, algorithm_version: str, recorded_at: str
) -> int:
    """The attempt's sequence: the next one, reserved now, or the one it already has.

    Called inside the attempt's own write transaction (``BEGIN IMMEDIATE``), before anything is computed, so the
    sequence is the order the write lock admitted the applications in; a rollback takes the reservation with it."""

    connection.execute(
        f"INSERT INTO {APPLICATION_ORDER_TABLE}(attempt_id, basis, algorithm_version, recorded_at) "
        "VALUES (?, ?, ?, ?) ON CONFLICT(attempt_id) DO NOTHING",
        (attempt_id, BASIS_APPLIED, algorithm_version, recorded_at),
    )
    return int(
        connection.execute(
            f"SELECT sequence FROM {APPLICATION_ORDER_TABLE} WHERE attempt_id = ?", (attempt_id,)
        ).fetchone()[0]
    )


def rank_legacy_attempts(connection: Any, *, algorithm_version: str, recorded_at: str) -> int:
    """Give every attempt without a sequence one, in the predecessor's ``(created_at, id)`` order, after every
    sequence that exists; how many were ranked. Their basis says the order is not known, only kept."""

    attempt_ids = [
        str(row[0])
        for row in connection.execute(
            f"SELECT id FROM practice_attempts AS attempt WHERE NOT EXISTS (SELECT 1 FROM {APPLICATION_ORDER_TABLE} "
            "AS application_order WHERE application_order.attempt_id = attempt.id) ORDER BY created_at, id"
        )
    ]
    connection.executemany(
        f"INSERT INTO {APPLICATION_ORDER_TABLE}(attempt_id, basis, algorithm_version, recorded_at) VALUES (?, ?, ?, ?)",
        [(attempt_id, BASIS_LEGACY_ORDER_UNKNOWN, algorithm_version, recorded_at) for attempt_id in attempt_ids],
    )
    return len(attempt_ids)


def _insert_attempt_lifecycle_inputs(
    connection: Any, attempt_id: str, inputs: LifecycleInputs, *, recorded_at: str
) -> None:
    # A plain INSERT: a second row for one attempt is a writer's bug, and replacing one would rewrite what an
    # application read.
    connection.execute(
        f"INSERT INTO {LIFECYCLE_INPUTS_TABLE}(attempt_id, learning_object_id, required_facets_json, basis, "
        "policy_version, recorded_at) VALUES (?, ?, ?, ?, ?, ?)",
        (attempt_id, inputs.learning_object_id, inputs.required_facets_json(), inputs.basis, inputs.policy_version,
         recorded_at),
    )


def record_legacy_lifecycle_inputs(
    connection: Any, inputs_by_attempt: Mapping[str, LifecycleInputs], *, recorded_at: str
) -> int:
    """Record the upgrade's reconstructed inputs for attempts that have no row, in attempt id order; how many."""

    for attempt_id in sorted(inputs_by_attempt):
        _insert_attempt_lifecycle_inputs(connection, attempt_id, inputs_by_attempt[attempt_id], recorded_at=recorded_at)
    return len(inputs_by_attempt)


class AttemptStoreMixin:
    def attempt_lifecycle_inputs(self, attempt_id: str) -> LifecycleInputs | None:
        """The required facet set recorded for the attempt's grade application, or None."""

        with self.connection() as connection:
            row = connection.execute(
                f"SELECT * FROM {LIFECYCLE_INPUTS_TABLE} WHERE attempt_id = ?", (attempt_id,)
            ).fetchone()
        return LifecycleInputs.from_row(row) if row is not None else None

    def attempt_applied_at_version(self, attempt_id: str) -> str | None:
        """The tag the attempt pipeline applied the attempt at (its application-order reservation), or None when it
        was ranked by an upgrade or never reserved one."""

        with self.connection() as connection:
            row = connection.execute(
                f"SELECT algorithm_version FROM {APPLICATION_ORDER_TABLE} WHERE attempt_id = ? AND basis = ?",
                (attempt_id, BASIS_APPLIED),
            ).fetchone()
        return str(row["algorithm_version"]) if row is not None else None

    def insert_practice_attempt(self, attempt: Mapping[str, Any]) -> None:
        with self.connection() as connection:
            self._insert_practice_attempt(connection, attempt)
            connection.commit()

    def fetch_practice_attempt(self, attempt_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM practice_attempts WHERE id = ?",
                (attempt_id,),
            ).fetchone()
        return _decode_attempt(row) if row is not None else None

    def practice_attempt_by_submission_id(self, submission_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM practice_attempts WHERE submission_id = ?",
                (submission_id,),
            ).fetchone()
        return _decode_attempt(row) if row is not None else None

    def attempt_submission_receipt(self, submission_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM attempt_submission_receipts WHERE submission_id = ?",
                (submission_id,),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["result"] = _loads(payload.pop("result_json"), {})
        return payload

    def insert_attempt_submission_receipt(
        self,
        *,
        submission_id: str,
        attempt_id: str,
        practice_item_id: str,
        result: Mapping[str, Any],
        clock: Clock | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO attempt_submission_receipts(
                  submission_id, attempt_id, practice_item_id, result_json, created_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(submission_id) DO NOTHING
                """,
                (
                    submission_id,
                    attempt_id,
                    practice_item_id,
                    _json(result),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()

    def upsert_attempt_feedback_metadata(
        self,
        *,
        attempt_id: str,
        grading_source: str,
        fallback_reason: str | None = None,
        agent_run_id: str | None = None,
        fatal_errors: list[str] | None = None,
        feedback_md: str | None = None,
        repair_suggestions: list[Mapping[str, Any]] | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO attempt_feedback_metadata(
                  attempt_id, grading_source, fallback_reason, agent_run_id,
                  fatal_errors_json, feedback_md, repair_suggestions_json,
                  created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(attempt_id) DO UPDATE SET
                  grading_source = excluded.grading_source,
                  fallback_reason = excluded.fallback_reason,
                  agent_run_id = excluded.agent_run_id,
                  fatal_errors_json = excluded.fatal_errors_json,
                  feedback_md = excluded.feedback_md,
                  repair_suggestions_json = excluded.repair_suggestions_json,
                  updated_at = excluded.updated_at
                """,
                (
                    attempt_id,
                    grading_source,
                    fallback_reason,
                    agent_run_id,
                    _json(fatal_errors or []),
                    feedback_md,
                    _json(repair_suggestions or []),
                    now,
                    now,
                ),
            )
            connection.commit()

    def fetch_attempt_feedback_metadata(self, attempt_id: str) -> dict[str, Any] | None:
        """The attempt's feedback metadata, as the causal consumers read it.

        Slice 1 M2: for a blind-graded attempt with a completed live diagnosis
        the instructional repair suggestions are the diagnosis's (its stored
        causal view); the persisted row keeps only what the grader wrote.
        """

        metadata = self.raw_attempt_feedback_metadata(attempt_id)
        if metadata is None:
            return None
        view = self.live_causal_view(attempt_id)
        if view is None:
            return metadata
        return merge_causal_view_into_feedback(metadata, view[1])

    def raw_attempt_feedback_metadata(self, attempt_id: str) -> dict[str, Any] | None:
        """The persisted feedback row exactly as written (no diagnosis overlay)."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM attempt_feedback_metadata WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
        return _decode_attempt_feedback_metadata(row) if row is not None else None

    def record_feedback_shown(
        self,
        attempt_id: str,
        *,
        session_id: str | None = None,
        clock: Clock | None = None,
    ) -> bool:
        _ = session_id
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE attempt_feedback_metadata
                SET shown_count = shown_count + 1,
                    first_shown_at = COALESCE(first_shown_at, ?),
                    last_shown_at = ?,
                    updated_at = ?
                WHERE attempt_id = ?
                """,
                (now, now, now, attempt_id),
            )
            connection.commit()
            return cursor.rowcount > 0

    def attempts_with_feedback_shown_between(
        self, *, after: str, before: str
    ) -> list[dict[str, Any]]:
        """Attempts whose feedback screen was last opened inside the interval.

        The feedback surface re-reveals a graded answer, the grader's feedback
        and its repair suggestions, so a reopen is exposure in its own right —
        but `record_feedback_shown` keeps only a counter plus first/last
        timestamps, so this sees the LAST reopen and nothing between it and the
        first. Consumers that scan for intervening exposure (the coldness
        receipt) must declare the intermediate reopens as still unobserved.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT m.attempt_id AS attempt_id,
                       m.shown_count AS shown_count,
                       m.first_shown_at AS first_shown_at,
                       m.last_shown_at AS last_shown_at,
                       m.grading_source AS grading_source,
                       a.practice_item_id AS practice_item_id,
                       a.learning_object_id AS learning_object_id,
                       a.created_at AS attempt_created_at
                  FROM attempt_feedback_metadata m
                  JOIN practice_attempts a ON a.id = m.attempt_id
                 WHERE m.last_shown_at IS NOT NULL
                   AND m.last_shown_at > ?
                   AND m.last_shown_at < ?
                 ORDER BY m.last_shown_at, m.attempt_id
                """,
                (after, before),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_recent_attempts_by_practice_item(
        self,
        practice_item_id: str,
        limit: int = 10,
        *,
        until: str | None = None,
        before: tuple[str, str] | None = None,
        order: AttemptOrder = LEGACY_ORDER,
    ) -> list[dict[str, Any]]:
        """The item's latest attempts, newest first. ``until`` (inclusive)
        bounds them at a historical writer's instant (``serve_eligibility``,
        Q33); without it the query is unchanged.

        ``before`` is a ledger position ``(created_at, id)``: only attempts
        strictly earlier in the ledger's order (``order``,
        :mod:`learnloop.db.attempt_order`) are read. Replay passes the attempt
        it is recomputing, so it sees the ledger the live write saw (that
        attempt's row did not exist yet, and no later one did), never the
        attempts recorded after it. Under the application order the live
        window (no ``before``) breaks a tie the same way, newest applied first."""

        if before is not None:
            bound, bound_args = order.before_sql(before, attempt_id="practice_attempts.id")
            terms = (
                order.order_sql(attempt_id="practice_attempts.id", descending=True)
                if order.by_sequence else "created_at DESC, id DESC"
            )
            with self.connection() as connection:
                rows = connection.execute(
                    f"""
                    SELECT * FROM practice_attempts
                    WHERE practice_item_id = ?
                      AND {bound}
                    ORDER BY {terms}
                    LIMIT ?
                    """,
                    (practice_item_id, *bound_args, limit),
                ).fetchall()
            return [_decode_attempt(row) for row in rows]
        with self.connection() as connection:
            if until is None:
                terms = (
                    order.order_sql(attempt_id="practice_attempts.id", descending=True)
                    if order.by_sequence else "created_at DESC"
                )
                rows = connection.execute(
                    f"""
                    SELECT * FROM practice_attempts
                    WHERE practice_item_id = ?
                    ORDER BY {terms}
                    LIMIT ?
                    """,
                    (practice_item_id, limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT * FROM practice_attempts
                    WHERE practice_item_id = ? AND created_at <= ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (practice_item_id, until, limit),
                ).fetchall()
        return [_decode_attempt(row) for row in rows]

    def list_recent_attempts_by_learning_object(
        self,
        learning_object_id: str,
        limit: int = 10,
        *,
        before: tuple[str, str] | None = None,
        order: AttemptOrder = LEGACY_ORDER,
    ) -> list[dict[str, Any]]:
        return self.list_recent_attempts_by_learning_objects(
            (learning_object_id,), limit=limit, before=before, order=order
        ).get(learning_object_id, [])

    def list_recent_attempts_by_learning_objects(
        self,
        learning_object_ids: Iterable[str],
        *,
        limit: int = 10,
        before: tuple[str, str] | None = None,
        order: AttemptOrder = LEGACY_ORDER,
    ) -> dict[str, list[dict[str, Any]]]:
        """Load the latest ``limit`` attempts for each requested LO at once.

        The scheduler evaluates an entire goal frontier in one pass.  A
        partitioned rank keeps that pass to one database query instead of one
        query per learning object, while the ``id`` tie-break makes replay
        order deterministic for attempts sharing a timestamp.

        ``before`` (a ledger position ``(created_at, id)``) keeps only the
        attempts strictly earlier in the ledger's order (``order``): what the
        ledger held when the attempt at that position was recorded (see
        :meth:`list_recent_attempts_by_practice_item`).
        """

        ids = sorted(
            {
                str(learning_object_id)
                for learning_object_id in learning_object_ids
                if learning_object_id
            }
        )
        grouped: dict[str, list[dict[str, Any]]] = {
            learning_object_id: [] for learning_object_id in ids
        }
        if not ids or limit <= 0:
            return grouped
        placeholders = ",".join("?" for _ in ids)
        bound = ""
        bound_args: tuple[str, ...] = ()
        if before is not None:
            predicate, bound_args = order.before_sql(before, attempt_id="attempts.id")
            bound = f"\n                      AND {predicate}"
        terms = (
            order.order_sql(attempt_id="attempts.id", descending=True)
            if order.by_sequence else "created_at DESC, id DESC"
        )
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                WITH ranked AS (
                    SELECT attempts.*,
                           ROW_NUMBER() OVER (
                               PARTITION BY learning_object_id
                               ORDER BY {terms}
                           ) AS recency_rank
                    FROM practice_attempts AS attempts
                    WHERE learning_object_id IN ({placeholders}){bound}
                )
                SELECT * FROM ranked
                WHERE recency_rank <= ?
                ORDER BY learning_object_id, recency_rank
                """,
                (*ids, *bound_args, int(limit)),
            ).fetchall()
        for row in rows:
            attempt = _decode_attempt(row)
            attempt.pop("recency_rank", None)
            grouped[str(row["learning_object_id"])].append(attempt)
        return grouped

    def list_attempts_by_learning_object(
        self, learning_object_id: str, *, order: AttemptOrder = LEGACY_ORDER
    ) -> list[dict[str, Any]]:
        """The learning object's attempts in the ledger's order (``order``): the order replay applies them in."""

        terms = order.order_sql(attempt_id="practice_attempts.id") if order.by_sequence else "created_at ASC, id ASC"
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM practice_attempts
                WHERE learning_object_id = ?
                ORDER BY {terms}
                """,
                (learning_object_id,),
            ).fetchall()
        return [_decode_attempt(row) for row in rows]

    def learning_object_ids_with_attempts(self) -> list[str]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT learning_object_id
                FROM practice_attempts
                ORDER BY learning_object_id ASC
                """
            ).fetchall()
        return [str(row["learning_object_id"]) for row in rows]

    def list_attempt_history(self, *, order: AttemptOrder = LEGACY_ORDER) -> list[dict[str, Any]]:
        """Every attempt (in the ledger's order, ``order``) with its posterior delta, if recorded.

        One LEFT JOIN so the knowledge-map chronicle can reconstruct each
        learning object's mastery trajectory (``posterior_delta`` carries the
        logit-space prior/posterior of the mastery update) alongside the raw
        attempt events. Attempts without a surprise row (legacy, or types that
        never update mastery) come back with ``posterior_delta`` = None.
        """

        terms = (
            order.order_sql(created_at="a.created_at", attempt_id="a.id")
            if order.by_sequence else "a.created_at ASC, a.id ASC"
        )
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT a.id AS id,
                       a.practice_item_id AS practice_item_id,
                       a.learning_object_id AS learning_object_id,
                       a.attempt_type AS attempt_type,
                       a.correctness AS correctness,
                       a.rubric_score AS rubric_score,
                       a.hints_used AS hints_used,
                       a.primed AS primed,
                       a.created_at AS created_at,
                       s.posterior_delta_json AS posterior_delta_json,
                       a.reference_status AS reference_status
                FROM practice_attempts a
                LEFT JOIN attempt_surprise s ON s.attempt_id = a.id
                ORDER BY {terms}
                """
            ).fetchall()
        history: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(row)
            payload["posterior_delta"] = _loads(payload.pop("posterior_delta_json"), None)
            payload["primed"] = bool(payload["primed"])
            # Canonical sources S1: carried only when it says something.
            if payload.get("reference_status") in (None, "not_applicable"):
                payload.pop("reference_status", None)
            history.append(payload)
        return history

    def count_attempts_with_error_type(self, practice_item_id: str, error_type: str) -> int:
        """Attempts on an item carrying ``error_type`` — the §12.4 promotion signal."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS n FROM practice_attempts
                WHERE practice_item_id = ? AND error_type = ?
                """,
                (practice_item_id, error_type),
            ).fetchone()
        return int(row["n"]) if row is not None else 0

    def insert_grading_evidence(self, attempt_id: str, evidence_rows: Iterable[Mapping[str, Any]]) -> None:
        with self.connection() as connection:
            for row in evidence_rows:
                self._insert_grading_evidence(connection, attempt_id, row)
            connection.commit()

    def fetch_grading_evidence(
        self,
        attempt_id: str,
        *,
        include_superseded: bool = False,
    ) -> list[GradingEvidenceRecord]:
        superseded_filter = "" if include_superseded else " AND superseded_at IS NULL"
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM grading_evidence
                WHERE attempt_id = ?{superseded_filter}
                ORDER BY created_at, criterion_id
                """,
                (attempt_id,),
            ).fetchall()
        return [_grading_evidence(row) for row in rows]

    # -- A8 clarification channel (migration 142) -------------------------------

    def insert_grading_clarification(
        self, row: Mapping[str, Any], *, clock: Clock | None = None
    ) -> str | None:
        """Append one clarification request; None when the attempt already has one.

        ``INSERT OR IGNORE`` against ``UNIQUE(attempt_id)`` — §3.A8's "one
        question per attempt" bound enforced by the schema rather than by a
        check a second caller could forget.
        """

        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO grading_clarifications(
                  id, attempt_id, criterion_id, reason, trigger, question_md,
                  expires_at, grading_prompt_version, agent_run_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(row["id"]),
                    str(row["attempt_id"]),
                    row.get("criterion_id"),
                    str(row["reason"]),
                    str(row["trigger"]),
                    str(row["question_md"]),
                    str(row["expires_at"]),
                    row.get("grading_prompt_version"),
                    row.get("agent_run_id"),
                    now,
                ),
            )
            connection.commit()
        return str(row["id"]) if cursor.rowcount else None

    def grading_clarification_for_attempt(self, attempt_id: str) -> sqlite3.Row | None:
        with self.connection() as connection:
            return connection.execute(
                """
                SELECT c.*, r.answer_md, r.created_at AS answered_at, r.outcome,
                       r.resolved_grading_revision
                FROM grading_clarifications c
                LEFT JOIN grading_clarification_responses r
                  ON r.clarification_id = c.id
                WHERE c.attempt_id = ?
                """,
                (attempt_id,),
            ).fetchone()

    def unanswered_grading_clarifications(self) -> list[sqlite3.Row]:
        with self.connection() as connection:
            return connection.execute(
                """
                SELECT c.*, NULL AS answer_md, NULL AS answered_at, NULL AS outcome,
                       NULL AS resolved_grading_revision
                FROM grading_clarifications c
                LEFT JOIN grading_clarification_responses r
                  ON r.clarification_id = c.id
                WHERE r.id IS NULL
                ORDER BY c.expires_at, c.id
                """
            ).fetchall()

    def grading_clarifications_awaiting_regrade(
        self, *, limit: int | None = None
    ) -> list[sqlite3.Row]:
        """Clarifications whose answer landed but whose re-grade has not resolved.

        The retry queue for Meas §3.A8. ``outcome IS NULL`` covers the answer
        that was recorded while no grader was reachable; ``'regrade_failed'``
        covers the one whose re-grade was attempted and threw. Both are
        recoverable, and neither is visible to a route that looks for *pending*
        clarifications — which is precisely how a completed exchange came to sit
        unconsumed.
        """

        clause = "LIMIT ?" if limit else ""
        params: tuple[Any, ...] = (int(limit),) if limit else ()
        with self.connection() as connection:
            return connection.execute(
                f"""
                SELECT c.*, r.answer_md, r.created_at AS answered_at, r.outcome,
                       r.resolved_grading_revision
                FROM grading_clarifications c
                JOIN grading_clarification_responses r
                  ON r.clarification_id = c.id
                WHERE r.outcome IS NULL OR r.outcome = 'regrade_failed'
                ORDER BY r.created_at, c.id
                {clause}
                """,
                params,
            ).fetchall()

    def insert_grading_clarification_response(
        self, row: Mapping[str, Any], *, clock: Clock | None = None
    ) -> str:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO grading_clarification_responses(
                  id, clarification_id, answer_md, resolved_grading_revision,
                  outcome, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(row["id"]),
                    str(row["clarification_id"]),
                    str(row["answer_md"]),
                    row.get("resolved_grading_revision"),
                    row.get("outcome"),
                    now,
                ),
            )
            connection.commit()
        return str(row["id"])

    def stamp_grading_clarification_outcome(
        self,
        clarification_id: str,
        *,
        outcome: str,
        resolved_grading_revision: int | None,
    ) -> None:
        """Stamp the regrade result onto an already-recorded answer.

        The answer text is never touched — only the two columns that describe
        what the system then did with it. See migration 142 on why the answer is
        written first and stamped afterwards.
        """

        with self.connection() as connection:
            connection.execute(
                """
                UPDATE grading_clarification_responses
                SET outcome = ?, resolved_grading_revision = ?
                WHERE clarification_id = ?
                """,
                (outcome, resolved_grading_revision, clarification_id),
            )
            connection.commit()

    def attempts_pending_clarification_review(self) -> list[str]:
        """Attempts whose grade advertises a pending clarification (Meas §3.A8)."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT id FROM practice_attempts
                WHERE manual_review_reason = 'provisional_pending_clarification'
                ORDER BY id
                """
            ).fetchall()
        return [str(row["id"]) for row in rows]

    def clarification_rate_counts(self) -> dict[str, int]:
        """Counts for §3.A8's revert criterion.

        The denominator is *model-graded* attempts (``grader_tier >= 3``): a
        self-graded or deterministically graded attempt (tier 1, or the tier-2
        empty "I'm stuck" zero) has no grader that could have asked, and
        including it would dilute the rate toward zero — hiding exactly the
        over-asking the criterion watches for.
        """

        # Numerator and denominator range over the SAME set, by construction:
        # every attempt that could have been asked. Two arms, unioned —
        #
        #   * ever model-graded (`grader_tier >= 3`, INCLUDING superseded rows,
        #     because an attempt whose model evidence a later regrade replaced
        #     still went through a grader that could have asked); and
        #   * carries a clarification at all, which is direct proof it did,
        #     whatever tier its surviving evidence rows ended up at.
        #
        # The second arm is what makes the numerator a subset rather than a
        # parallel count. Restricting the numerator to the first arm alone would
        # have been the other way to make the two agree, and it is the wrong one:
        # it hides real questions instead of counting the attempts that produced
        # them.
        gradeable_sql = """
            SELECT attempt_id FROM grading_evidence WHERE grader_tier >= 3
            UNION
            SELECT attempt_id FROM grading_clarifications
        """
        with self.connection() as connection:
            gradeable = connection.execute(
                f"SELECT COUNT(*) AS n FROM ({gradeable_sql})"
            ).fetchone()
            asked = connection.execute(
                "SELECT COUNT(*) AS n FROM grading_clarifications"
            ).fetchone()
            answered = connection.execute(
                """
                SELECT COUNT(*) AS n FROM grading_clarification_responses r
                JOIN grading_clarifications c ON c.id = r.clarification_id
                """
            ).fetchone()
        return {
            "gradeable_attempts": int(gradeable["n"] if gradeable else 0),
            "clarifications": int(asked["n"] if asked else 0),
            "answered": int(answered["n"] if answered else 0),
        }

    # -- A6 opportunistic trace evidence (migration 141) ------------------------


    def insert_trace_exercised_facets(
        self,
        attempt_id: str,
        rows: Iterable[Mapping[str, Any]],
        *,
        clock: Clock | None = None,
    ) -> int:
        """Append A6 trace observations for one attempt; returns rows written.

        ``INSERT OR IGNORE`` against the ``(attempt_id, facet_id, source)``
        unique key, because the honest response to the grader naming a facet
        twice is one observation, not two — and because a regrade re-reports the
        same trace. Append-only by trigger, so a later re-report can never
        overwrite what the first run said it saw.
        """

        now = utc_now_iso(clock)
        written = 0
        with self.connection() as connection:
            for row in rows:
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO trace_exercised_facets(
                      id, attempt_id, facet_id, observation_scope, role, evidence,
                      criterion_id, source, agent_run_id, grading_prompt_version, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(row.get("id") or new_ulid()),
                        attempt_id,
                        str(row["facet_id"]),
                        # No default. `opportunistic` is the reward-eligible,
                        # A6-revert-criterion-counted arm, so defaulting to it
                        # would let a caller that forgot the field mint the
                        # generous reading. The validator upstream always sets
                        # it; a caller that does not has a bug, not a default.
                        _required_observation_scope(row),
                        "supporting",
                        str(row.get("evidence") or ""),
                        row.get("criterion_id"),
                        str(row.get("source") or "grader_trace"),
                        row.get("agent_run_id"),
                        row.get("grading_prompt_version"),
                        str(row.get("created_at") or now),
                    ),
                )
                written += int(cursor.rowcount or 0)
            connection.commit()
        return written

    def trace_exercised_facets(self, attempt_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM trace_exercised_facets
                WHERE attempt_id = ?
                ORDER BY facet_id, source
                """,
                (attempt_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def all_trace_exercised_facets(self) -> dict[str, list[dict[str, Any]]]:
        """Every A6 observation, grouped by attempt.

        The projection folds the whole ledger in one pass, so it must not issue
        one query per attempt the way the per-attempt reader would force.
        """

        grouped: dict[str, list[dict[str, Any]]] = {}
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM trace_exercised_facets ORDER BY attempt_id, facet_id, source"
            ).fetchall()
        for row in rows:
            grouped.setdefault(str(row["attempt_id"]), []).append(dict(row))
        return grouped

    def list_grading_evidence_history(
        self, *, include_superseded: bool = False
    ) -> list[GradingEvidenceRecord]:
        """Every grading-evidence row in stable replay order.

        Timeline/report surfaces replay the immutable grading ledger.  Their
        bulk path must not issue one query per attempt (and, historically, one
        such query per facet per session), so expose the same records as
        :meth:`fetch_grading_evidence` through one read.
        """

        superseded_filter = "" if include_superseded else " WHERE superseded_at IS NULL"
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM grading_evidence{superseded_filter}
                ORDER BY attempt_id, created_at,
                         COALESCE(grading_revision, -1), criterion_id, id
                """
            ).fetchall()
        return [_grading_evidence(row) for row in rows]

    def find_attempt_id_by_evidence_agent_run(
        self,
        *,
        practice_item_id: str,
        agent_run_id: str,
        attempt_type: str | None = None,
    ) -> str | None:
        """Latest attempt on an item whose grading evidence carries ``agent_run_id``.

        Used as the teach-back finish idempotency lookup: the conversation id is
        persisted as the evidence rows' ``agent_run_id``, so a retried finish can
        recover the already-recorded attempt instead of grading it twice.
        """

        type_filter = "" if attempt_type is None else " AND a.attempt_type = ?"
        parameters: list[Any] = [practice_item_id, agent_run_id]
        if attempt_type is not None:
            parameters.append(attempt_type)
        with self.connection() as connection:
            row = connection.execute(
                f"""
                SELECT a.id FROM practice_attempts a
                WHERE a.practice_item_id = ?
                  AND EXISTS (
                    SELECT 1 FROM grading_evidence e
                    WHERE e.attempt_id = a.id AND e.agent_run_id = ?
                  ){type_filter}
                ORDER BY a.created_at DESC, a.id DESC
                LIMIT 1
                """,
                parameters,
            ).fetchone()
        return row["id"] if row is not None else None

    def supersede_self_grade_rows(
        self,
        attempt_id: str,
        *,
        superseded_by_evidence_id: str,
        clock: Clock | None = None,
    ) -> int:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE grading_evidence
                SET superseded_at = ?, superseded_by_evidence_id = ?
                WHERE attempt_id = ? AND grader_tier = 1 AND superseded_at IS NULL
                """,
                (now, superseded_by_evidence_id, attempt_id),
            )
            connection.commit()
            return cursor.rowcount

    def is_score_only_exam_import(self, attempt_id: str) -> bool:
        """Whether the attempt is an exam import with no learner work to grade.

        The attempt says it is an import (``exam_evidence`` is written by exam
        seeding alone); its import rows say whether it carries work. One with
        no import row at all (seeded before an empty rubric was refused) is
        score-only: nothing records work for it. Superseded rows count, since
        an explicit regrade can come after the seeding rows were replaced."""

        with self.connection() as connection:
            row = connection.execute(
                f"""
                SELECT a.attempt_type AS attempt_type,
                       MAX(CASE WHEN e.id IS NOT NULL AND {_EXAM_IMPORT_HAS_WORK} THEN 1 ELSE 0 END) AS has_work
                FROM practice_attempts a
                LEFT JOIN grading_evidence e ON e.attempt_id = a.id AND e.local_grader_id = 'exam_import'
                WHERE a.id = ?
                GROUP BY a.id
                """,
                (attempt_id,),
            ).fetchone()
        return row is not None and row["attempt_type"] == "exam_evidence" and not row["has_work"]

    def pending_self_grade_regrade_attempts(self, limit: int | None = None) -> list[dict[str, Any]]:
        limit_clause = "" if limit is None else " LIMIT ?"
        parameters: list[Any] = [] if limit is None else [limit]
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT a.* FROM practice_attempts a
                WHERE EXISTS (
                  SELECT 1 FROM grading_evidence e
                  WHERE e.attempt_id = a.id
                    AND e.grader_tier = 1
                    AND e.superseded_at IS NULL
                    -- Tier 1 also includes simulated grades and imported scores.
                    -- Keep answer-bearing imports eligible, but grading the
                    -- seeder's score placeholder would overwrite real evidence.
                    AND (
                      e.local_grader_id = 'self'
                      OR (e.local_grader_id = 'exam_import' AND {_EXAM_IMPORT_HAS_WORK})
                    )
                )
                AND NOT EXISTS (
                  SELECT 1 FROM grading_evidence e2
                  WHERE e2.attempt_id = a.id
                    AND e2.grader_tier = 3
                    AND e2.superseded_at IS NULL
                )
                -- self_report rows are learner statements (rung-variant belief
                -- writes, deliberate self-ratings), not gradable responses: an
                -- AI regrade of their placeholder text can only produce
                -- nonsense grades and phantom assessment_ambiguity errors.
                AND a.attempt_type != 'self_report'
                ORDER BY a.created_at ASC, a.id ASC{limit_clause}
                """,
                parameters,
            ).fetchall()
        return [_decode_attempt(row) for row in rows]

    def update_attempt_grade(
        self,
        attempt_id: str,
        *,
        rubric_score: int,
        correctness: float,
        grader_confidence: float,
        manual_review: bool,
        manual_review_reason: str | None,
        error_type: str | None,
        clock: Clock | None = None,
    ) -> bool:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE practice_attempts
                SET rubric_score = ?,
                    correctness = ?,
                    grader_confidence = ?,
                    manual_review = ?,
                    manual_review_reason = ?,
                    error_type = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    rubric_score,
                    correctness,
                    grader_confidence,
                    1 if manual_review else 0,
                    manual_review_reason,
                    error_type,
                    now,
                    attempt_id,
                ),
            )
            connection.commit()
            return cursor.rowcount > 0

    def count_clean_attempts_since(
        self,
        learning_object_id: str,
        *,
        since: str,
        until: str,
        min_correctness: float,
        exclude_attempt_ids: Iterable[str] = (),
    ) -> int:
        """Count "clean" attempts on a learning object in ``(since, until]``.

        Clean = graded correctness at or above ``min_correctness``, no error
        attribution recorded on the attempt row (``error_type IS NULL`` is
        equivalent to "wrote no error events"), and not a ``dont_know``/``skip``
        self-diagnosis. Bounding by ``until`` (the triggering attempt's
        ``created_at``) keeps the count reproducible under replay, where future
        attempts still exist in ``practice_attempts``. ``exclude_attempt_ids``
        are never counted (the caller's held grades: no outcome at all).
        """

        excluded = sorted({str(value) for value in exclude_attempt_ids if value})
        exclusion = (
            f" AND id NOT IN ({','.join('?' for _ in excluded)})" if excluded else ""
        )
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS clean_count
                FROM practice_attempts
                WHERE learning_object_id = ?
                  AND created_at > ?
                  AND created_at <= ?
                  AND correctness >= ?
                  AND error_type IS NULL
                  AND attempt_type NOT IN ('dont_know', 'skip')
                """
                + exclusion,
                (learning_object_id, since, until, min_correctness, *excluded),
            ).fetchone()
        return int(row["clean_count"])

    def clean_attempt_ids_since(
        self,
        learning_object_id: str,
        *,
        since: str,
        until: str,
        min_correctness: float,
    ) -> list[str]:
        """The attempts :meth:`count_clean_attempts_since` would count."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT id FROM practice_attempts
                WHERE learning_object_id = ?
                  AND created_at > ?
                  AND created_at <= ?
                  AND correctness >= ?
                  AND error_type IS NULL
                  AND attempt_type NOT IN ('dont_know', 'skip')
                """,
                (learning_object_id, since, until, min_correctness),
            ).fetchall()
        return [str(row["id"]) for row in rows]

    def insert_attempt_surprise(self, surprise: Mapping[str, Any]) -> None:
        with self.connection() as connection:
            self._insert_attempt_surprise(connection, surprise)
            connection.commit()

    def latest_attempt_surprise(self, attempt_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM attempt_surprise WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
        return _decode_surprise(row) if row is not None else None

    def attempt_innovation_samples(self) -> list[dict[str, Any]]:
        """Per-attempt rows for the difficulty-miscalibration monitor (spec §7.4).

        Joins each recorded attempt to its surprise row and surfaces the predicted
        correctness (``predicted_score_dist_json.expected_correctness``) so the
        innovation ``y - p`` can be reconstructed without a new table.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT a.id AS id,
                       a.practice_item_id AS practice_item_id,
                       a.learning_object_id AS learning_object_id,
                       a.rubric_score AS rubric_score,
                       s.predicted_score_dist_json AS predicted_score_dist_json
                FROM practice_attempts a
                JOIN attempt_surprise s ON s.attempt_id = a.id
                ORDER BY a.created_at
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def update_attempt_surprise_actions(
        self,
        attempt_id: str,
        *,
        triggered_actions: list[str] | None = None,
        suppressed_actions: list[str] | None = None,
        gate_diagnostics: Mapping[str, Any] | None = None,
    ) -> bool:
        assignments: list[str] = []
        parameters: list[Any] = []
        if triggered_actions is not None:
            assignments.append("triggered_actions_json = ?")
            parameters.append(_json(triggered_actions))
        if suppressed_actions is not None:
            assignments.append("suppressed_actions_json = ?")
            parameters.append(_json(suppressed_actions))
        if gate_diagnostics is not None:
            assignments.append("gate_diagnostics_json = ?")
            parameters.append(_json(gate_diagnostics))
        if not assignments:
            return False
        parameters.append(attempt_id)
        with self.connection() as connection:
            cursor = connection.execute(
                f"UPDATE attempt_surprise SET {', '.join(assignments)} WHERE attempt_id = ?",
                parameters,
            )
            connection.commit()
            return cursor.rowcount > 0

    def record_attempt_outcome(
        self,
        *,
        attempt: Mapping[str, Any],
        evidence_rows: Iterable[Mapping[str, Any]],
        error_events: Iterable[Mapping[str, Any]],
        surprise: Mapping[str, Any],
        practice_item_state: PracticeItemState,
        mastery_state: MasteryState,
        facet_uncertainty_states: Iterable[Mapping[str, Any]] = (),
        quality_state: Mapping[str, Any] | None = None,
        ability_transition: Mapping[str, Any] | None = None,
        attempt_debug_payload: Mapping[str, Any] | None = None,
        item_parameter_state: ItemParameterState | None = None,
        lifecycle_inputs: LifecycleInputs | None = None,
        mastery_seed_inputs: MasterySeedInputs | None = None,
    ) -> None:
        """The live attempt's write. The item row takes only its scheduling columns
        (:meth:`_record_attempt_practice_item_state`): content sync owns the rest. ``lifecycle_inputs`` (from
        mvp-0.66): the required facet set the grade application read, recorded with the attempt.
        ``mastery_seed_inputs`` (from mvp-0.67): the seed the attempt's prior was built from when its learning
        object had no mastery row, recorded with the row this write persists."""

        with self.connection() as connection:
            self._insert_practice_attempt(connection, attempt)
            if lifecycle_inputs is not None:
                _insert_attempt_lifecycle_inputs(
                    connection, str(attempt["id"]), lifecycle_inputs, recorded_at=str(attempt["created_at"])
                )
            for row in evidence_rows:
                self._insert_grading_evidence(connection, attempt["id"], row)
            for event in error_events:
                self._insert_error_event(connection, event)
            self._insert_attempt_surprise(connection, surprise)
            self._record_attempt_practice_item_state(connection, practice_item_state)
            self._upsert_mastery_state_record(connection, mastery_state)
            if mastery_seed_inputs is not None:
                insert_mastery_seed_inputs(connection, mastery_seed_inputs, recorded_at=str(attempt["created_at"]))
            for state in facet_uncertainty_states:
                self._upsert_facet_uncertainty_state(connection, state)
            if quality_state is not None:
                self._upsert_practice_item_quality_state(connection, quality_state)
            if ability_transition is not None:
                self._upsert_ability_transition_event(connection, ability_transition)
            if item_parameter_state is not None:
                self._upsert_item_parameter_state_record(connection, item_parameter_state)
            if attempt_debug_payload is not None:
                connection.execute(
                    """
                    INSERT INTO attempt_debug_payloads(
                      attempt_id, payload_json, algorithm_version, created_at
                    )
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(attempt_id) DO UPDATE SET
                      payload_json = excluded.payload_json,
                      algorithm_version = excluded.algorithm_version,
                      created_at = excluded.created_at
                    """,
                    (
                        attempt["id"],
                        _json(attempt_debug_payload),
                        attempt_debug_payload.get("algorithm_version", ""),
                        attempt_debug_payload.get("created_at", attempt.get("created_at")),
                    ),
                )
            self._link_attempt_to_scheduler_candidate(connection, attempt)
            self._insert_learning_outcome_labels(
                connection,
                attempt,
                algorithm_version=surprise["algorithm_version"],
            )
            connection.commit()

    def insert_regrade_evidence(
        self,
        *,
        attempt_id: str,
        new_evidence_rows: Iterable[Mapping[str, Any]],
        superseded_by_evidence_id: str,
        supersede_tiers: tuple[int, ...] = (1,),
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        new_evidence_ids: list[str] = []
        with self.connection() as connection:
            for row in new_evidence_rows:
                self._insert_grading_evidence(connection, attempt_id, row)
                new_evidence_ids.append(str(row["id"]))
            tier_placeholders = ",".join("?" for _ in supersede_tiers)
            id_placeholders = ",".join("?" for _ in new_evidence_ids) or "''"
            connection.execute(
                f"""
                UPDATE grading_evidence
                SET superseded_at = ?, superseded_by_evidence_id = ?
                WHERE attempt_id = ? AND superseded_at IS NULL
                  AND grader_tier IN ({tier_placeholders})
                  AND id NOT IN ({id_placeholders})
                """,
                (now, superseded_by_evidence_id, attempt_id, *supersede_tiers, *new_evidence_ids),
            )
            connection.commit()

    def attempt_debug_payload(self, attempt_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT payload_json FROM attempt_debug_payloads WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
        return _loads(row["payload_json"], {}) if row is not None else None

    def learning_outcome_labels_for_source(self, attempt_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM learning_outcome_labels
                WHERE source_attempt_id = ?
                ORDER BY created_at ASC, outcome_attempt_id ASC
                """,
                (attempt_id,),
            ).fetchall()
        return [_decode_learning_outcome_label(row) for row in rows]

    def list_all_attempts(self) -> list[dict[str, Any]]:
        """Every practice attempt ordered for per-item replay (fitting jobs)."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM practice_attempts ORDER BY practice_item_id ASC, created_at ASC, id ASC"
            ).fetchall()
        return [dict(row) for row in rows]

    def attempt_count_for_learning_objects(self, learning_object_ids: list[str]) -> int:
        if not learning_object_ids:
            return 0
        placeholders = ",".join("?" for _ in learning_object_ids)
        with self.connection() as connection:
            row = connection.execute(
                f"SELECT COUNT(*) AS n FROM practice_attempts WHERE learning_object_id IN ({placeholders})",
                list(learning_object_ids),
            ).fetchone()
        return int(row["n"]) if row is not None else 0

    def daily_qualifying_attempt_counts_for_learning_objects(
        self,
        learning_object_ids: list[str],
        *,
        days: int = 14,
        not_before: str | None = None,
        clock: Clock | None = None,
    ) -> dict[date, int]:
        """Zero-filled, goal-scoped certification-capable attempts by local day."""

        days = max(days, 1)
        now = (clock or SystemClock()).now()
        today = now.astimezone().date()
        configured_start = today - timedelta(days=days - 1)
        goal_start = parse_utc(not_before)
        window_start = (
            max(configured_start, goal_start.astimezone().date())
            if goal_start is not None
            else configured_start
        )
        counts: dict[date, int] = {
            window_start + timedelta(days=offset): 0
            for offset in range(max((today - window_start).days + 1, 1))
        }
        if not learning_object_ids:
            return counts

        placeholders = ",".join("?" for _ in learning_object_ids)
        cutoff_iso = (
            now.astimezone(UTC) - timedelta(days=max((today - window_start).days + 2, 2))
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        params: list[Any] = [*learning_object_ids, cutoff_iso]
        not_before_clause = ""
        if not_before is not None:
            not_before_clause = "AND created_at >= ?"
            params.append(not_before)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT created_at
                FROM practice_attempts
                WHERE learning_object_id IN ({placeholders})
                  AND created_at >= ?
                  {not_before_clause}
                  AND COALESCE(primed, 0) = 0
                  AND COALESCE(hints_used, 0) = 0
                  AND attempt_type IN (
                    'independent_attempt', 'open_text', 'diagnostic_probe',
                    'exam_attempt', 'teach_back'
                  )
                """,
                params,
            ).fetchall()
        for row in rows:
            created = parse_utc(row["created_at"])
            if created is None:
                continue
            day = created.astimezone().date()
            if day in counts:
                counts[day] += 1
        return counts
    def practice_attempt_outcomes_for_items(self, item_ids: list[str]) -> list[dict[str, Any]]:
        """Time-ordered attempt outcomes for a set of practice items.

        Backs the graph editor's ambiguous-direction attempt-ordering evidence
        (success on the target's items before vs after first success on the
        source's items). Ordered by ``created_at`` so before/after bucketing is
        deterministic.
        """

        if not item_ids:
            return []
        placeholders = ",".join("?" for _ in item_ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id, practice_item_id, rubric_score, correctness, created_at
                FROM practice_attempts
                WHERE practice_item_id IN ({placeholders})
                ORDER BY created_at, id
                """,
                list(item_ids),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "practice_item_id": row["practice_item_id"],
                "rubric_score": row["rubric_score"],
                "correctness": row["correctness"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def grading_correction_count_between(self, started_at: str, ended_at: str) -> int:
        """Count grading epochs after the original grade in a time window."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT attempt_id, grading_revision, created_at
                FROM grading_evidence
                ORDER BY attempt_id, created_at,
                         COALESCE(grading_revision, -1), id
                """
            ).fetchall()
        epochs_by_attempt: dict[str, dict[str, str]] = {}
        for row in rows:
            epoch_key = (
                f"revision:{row['grading_revision']}"
                if row["grading_revision"] is not None
                else f"legacy:{row['created_at']}"
            )
            epochs_by_attempt.setdefault(str(row["attempt_id"]), {}).setdefault(
                epoch_key, str(row["created_at"])
            )
        count = 0
        for epochs in epochs_by_attempt.values():
            ordered = sorted(epochs.items(), key=lambda pair: (pair[1], pair[0]))
            count += sum(started_at <= at <= ended_at for _key, at in ordered[1:])
        return count

    def attempt_count(self) -> int:
        """Every attempt ever served — the "questions served" denominator.

        Meas §0's identity is `questions ~ (cells to clear) / (cells cleared per
        question)`, so `cells_cleared_per_question` divides by questions served
        vault-wide. `attempt_count_for_learning_objects` is the goal-scoped
        cousin; this is the unscoped one the scoreboard needs.
        """

        with self.connection() as connection:
            return int(
                connection.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()[0]
            )

    def ensure_assessment_contract_version(
        self,
        *,
        practice_item_id: str,
        contract_hash: str,
        contract_json: str,
        schema_version: int,
        clock: Clock | None = None,
    ) -> str:
        """Content-addressed assessment-contract snapshot (§5.2), idempotent.

        Returns the existing snapshot id when ``(practice_item_id, contract_hash)``
        already exists (identical item versions reuse one snapshot), else inserts
        and returns a new id.
        """

        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM assessment_contract_versions
                WHERE practice_item_id = ? AND contract_hash = ?
                """,
                (practice_item_id, contract_hash),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            version_id = new_ulid()
            connection.execute(
                """
                INSERT INTO assessment_contract_versions(
                  id, practice_item_id, contract_hash, contract_json,
                  schema_version, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    practice_item_id,
                    contract_hash,
                    contract_json,
                    schema_version,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return version_id

    def fetch_assessment_contract_version(self, version_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM assessment_contract_versions WHERE id = ?",
                (version_id,),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["contract"] = _loads(payload["contract_json"], {})
        return payload

    def fetch_assessment_contract_versions(
        self, version_ids: Iterable[str]
    ) -> dict[str, dict[str, Any]]:
        """Bulk-load content-addressed assessment contracts by id."""

        ids = sorted({str(version_id) for version_id in version_ids if version_id})
        if not ids:
            return {}
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM assessment_contract_versions WHERE id IN ({placeholders})",
                ids,
            ).fetchall()
        contracts: dict[str, dict[str, Any]] = {}
        for row in rows:
            payload = dict(row)
            payload["contract"] = _loads(payload["contract_json"], {})
            contracts[str(payload["id"])] = payload
        return contracts

    def assessment_contract_versions_for_practice_item(
        self, practice_item_id: str
    ) -> list[dict[str, Any]]:
        """Immutable contract snapshots ever presented for one PracticeItem."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM assessment_contract_versions
                WHERE practice_item_id = ?
                ORDER BY created_at, id
                """,
                (practice_item_id,),
            ).fetchall()
        versions: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(row)
            payload["contract"] = _loads(payload["contract_json"], {})
            versions.append(payload)
        return versions

    def append_measurement_contract_corrections(
        self,
        *,
        correction_set_id: str,
        source_practice_item_id: str,
        source_contract_version_ids: Iterable[str],
        corrected_practice_item_id: str,
        corrected_contract_version_id: str,
        consuming_projection_version: str,
        historical_evidence_policy: str,
        reason: str,
        correction: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> list[str]:
        """Append one immutable correction edge per historical contract version.

        A correction set is written transactionally. The database uniqueness
        constraint prevents a projection version from acquiring two competing
        meanings for the same historical contract.
        """

        if historical_evidence_policy not in {
            "preserve_original",
            "reinterpret_measurement",
        }:
            raise ValueError("unknown historical evidence policy")
        source_ids = sorted({str(value) for value in source_contract_version_ids})
        if not source_ids:
            raise ValueError("a measurement correction requires a source contract version")
        now = utc_now_iso(clock)
        correction_ids = [new_ulid() for _ in source_ids]
        with self.connection() as connection:
            for correction_id, source_version_id in zip(correction_ids, source_ids, strict=True):
                connection.execute(
                    """
                    INSERT INTO measurement_contract_corrections(
                      id, correction_set_id, source_practice_item_id,
                      source_contract_version_id, corrected_practice_item_id,
                      corrected_contract_version_id, consuming_projection_version,
                      historical_evidence_policy, reason, correction_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        correction_id,
                        correction_set_id,
                        source_practice_item_id,
                        source_version_id,
                        corrected_practice_item_id,
                        corrected_contract_version_id,
                        consuming_projection_version,
                        historical_evidence_policy,
                        reason,
                        _json(dict(correction)) if correction is not None else None,
                        now,
                    ),
                )
            connection.commit()
        return correction_ids

    def measurement_contract_corrections(
        self,
        *,
        source_practice_item_id: str | None = None,
        correction_set_id: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        parameters: list[Any] = []
        if source_practice_item_id is not None:
            clauses.append("source_practice_item_id = ?")
            parameters.append(source_practice_item_id)
        if correction_set_id is not None:
            clauses.append("correction_set_id = ?")
            parameters.append(correction_set_id)
        query = "SELECT * FROM measurement_contract_corrections"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, parameters).fetchall()
        corrections: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(row)
            payload["correction"] = _loads(payload.pop("correction_json"), None)
            corrections.append(payload)
        return corrections

    def effective_assessment_contract_version(
        self,
        source_version_id: str,
        *,
        projection_version: str,
    ) -> dict[str, Any] | None:
        """Resolve the contract a named projection is authorized to consume.

        `preserve_original` correction records remain visible to audit but do
        not alter replay. Only an exact projection-version match with an
        explicit `reinterpret_measurement` policy follows the correction edge.
        """

        with self.connection() as connection:
            correction = connection.execute(
                """
                SELECT corrected_contract_version_id
                FROM measurement_contract_corrections
                WHERE source_contract_version_id = ?
                  AND consuming_projection_version = ?
                  AND historical_evidence_policy = 'reinterpret_measurement'
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (source_version_id, projection_version),
            ).fetchone()
        effective_id = (
            str(correction["corrected_contract_version_id"])
            if correction is not None
            else source_version_id
        )
        return self.fetch_assessment_contract_version(effective_id)

    def effective_assessment_contract_versions(
        self,
        source_version_ids: Iterable[str],
        *,
        projection_version: str,
    ) -> dict[str, dict[str, Any]]:
        """Bulk form of :meth:`effective_assessment_contract_version`.

        The mapping stays keyed by the source contract id written on grading
        evidence.  Values are the contract snapshots the named projection is
        authorized to consume after applying any explicit reinterpretation
        edge.  Canonical replay uses this method once before its attempt loop.
        """

        with self.connection() as connection:
            if not connection.in_transaction:
                connection.execute("BEGIN")
            return load_effective_assessment_contracts(
                connection,
                source_version_ids,
                projection_version=projection_version,
            )

    def superseded_measurement_item_ids(self) -> set[str]:
        """Attempted item files superseded by an accepted correction set."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT source_practice_item_id
                FROM measurement_contract_corrections
                """
            ).fetchall()
        return {str(row["source_practice_item_id"]) for row in rows}

    def list_all_assessment_contract_versions(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM assessment_contract_versions ORDER BY created_at, id"
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_causal_cold_verification(
        self,
        *,
        verification_id: str,
        source_attempt_id: str,
        cold_attempt_id: str,
        repair_class_id: str,
        hypothesis_ids: Sequence[str],
        source_surface_family: str,
        cold_surface_family: str,
        avoided_affordances: Sequence[str],
        success: bool,
        capability_update: Mapping[str, Any],
        diagnosis_support_update: Mapping[str, Any],
        repair_effect_support: Mapping[str, Any],
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO causal_cold_verifications(
                  id, source_attempt_id, cold_attempt_id, repair_class_id,
                  hypothesis_ids_json, source_surface_family,
                  cold_surface_family, avoided_affordances_json, success,
                  capability_update_json, diagnosis_support_update_json,
                  repair_effect_support_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    verification_id,
                    source_attempt_id,
                    cold_attempt_id,
                    repair_class_id,
                    _json(list(hypothesis_ids)),
                    source_surface_family,
                    cold_surface_family,
                    _json(list(avoided_affordances)),
                    int(success),
                    _json(dict(capability_update)),
                    _json(dict(diagnosis_support_update)),
                    _json(dict(repair_effect_support)),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        result = self.causal_cold_verification_for_attempt(cold_attempt_id)
        assert result is not None
        expected = {
            "id": verification_id,
            "source_attempt_id": source_attempt_id,
            "repair_class_id": repair_class_id,
            "hypothesis_ids": list(hypothesis_ids),
            "source_surface_family": source_surface_family,
            "cold_surface_family": cold_surface_family,
            "avoided_affordances": list(avoided_affordances),
            "success": success,
            "capability_update": dict(capability_update),
            "diagnosis_support_update": dict(diagnosis_support_update),
            "repair_effect_support": dict(repair_effect_support),
        }
        if any(result.get(key) != value for key, value in expected.items()):
            raise ValueError(
                "cold attempt already belongs to a different verification receipt"
            )
        return result

    def causal_cold_verification_for_attempt(
        self, cold_attempt_id: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM causal_cold_verifications
                 WHERE cold_attempt_id = ?
                """,
                (cold_attempt_id,),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        for field in (  # noqa: F402  a local loop variable; this function never calls dataclasses.field()
            "hypothesis_ids",
            "avoided_affordances",
            "capability_update",
            "diagnosis_support_update",
            "repair_effect_support",
        ):
            payload[field] = _loads(payload.pop(f"{field}_json"), None)
        payload["success"] = bool(payload["success"])
        return payload

    # -- causal cold outcomes (migration 145) -------------------------------
    #
    # One append-only row per terminal disposition of a cold-verification
    # opportunity, measured or not (spec §4.3). INSERT OR IGNORE over a
    # content-addressed id, so replaying the same terminal event is one row.

    def insert_causal_cold_outcome(
        self,
        *,
        outcome_id: str,
        outcome: str,
        followup_task_id: str | None,
        remediation_episode_id: str | None,
        case_kind: str | None,
        case_ref: str | None,
        source_attempt_id: str | None,
        cold_attempt_id: str | None,
        repair_class_id: str | None,
        hypothesis_ids: Sequence[str],
        cold_verification_id: str | None,
        servable_opportunity: bool,
        duration_state: str | None,
        detail: Mapping[str, Any],
        store_version: str,
        scheduled_not_before: str | None,
        scheduled_expires_at: str | None,
        clock: Clock | None = None,
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO causal_cold_outcomes(
                  id, outcome, followup_task_id, remediation_episode_id,
                  case_kind, case_ref, source_attempt_id, cold_attempt_id,
                  repair_class_id, hypothesis_ids_json, cold_verification_id,
                  servable_opportunity, duration_state, detail_json,
                  store_version, scheduled_not_before, scheduled_expires_at,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    outcome_id,
                    outcome,
                    followup_task_id,
                    remediation_episode_id,
                    case_kind,
                    case_ref,
                    source_attempt_id,
                    cold_attempt_id,
                    repair_class_id,
                    _json(list(hypothesis_ids)),
                    cold_verification_id,
                    int(servable_opportunity),
                    duration_state,
                    _json(dict(detail)),
                    store_version,
                    scheduled_not_before,
                    scheduled_expires_at,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return self.causal_cold_outcome(outcome_id)

    @staticmethod
    def _decode_causal_cold_outcome(row: Any) -> dict[str, Any]:
        payload = dict(row)
        payload["hypothesis_ids"] = _loads(payload.pop("hypothesis_ids_json"), [])
        payload["detail"] = _loads(payload.pop("detail_json"), {})
        payload["servable_opportunity"] = bool(payload["servable_opportunity"])
        return payload

    def causal_cold_outcome(self, outcome_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM causal_cold_outcomes WHERE id = ?",
                (outcome_id,),
            ).fetchone()
        return self._decode_causal_cold_outcome(row) if row is not None else None

    def causal_cold_outcome_for_task(
        self, followup_task_id: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM causal_cold_outcomes WHERE followup_task_id = ?",
                (followup_task_id,),
            ).fetchone()
        return self._decode_causal_cold_outcome(row) if row is not None else None

    def causal_cold_outcomes(
        self,
        *,
        outcome: str | None = None,
        remediation_episode_id: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if outcome is not None:
            clauses.append("outcome = ?")
            params.append(outcome)
        if remediation_episode_id is not None:
            clauses.append("remediation_episode_id = ?")
            params.append(remediation_episode_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM causal_cold_outcomes {where} ORDER BY created_at, id",
                params,
            ).fetchall()
        return [self._decode_causal_cold_outcome(row) for row in rows]

    # -- coldness receipts (migration 149) ----------------------------------
    #
    # Append-only administration receipts for the cold retrieval lane: one
    # `administration` snapshot per follow-up task at serving time, one `final`
    # receipt per terminal disposition. INSERT OR IGNORE over content ids plus
    # the partial unique (task, stage) index makes both writes idempotent.

    def insert_coldness_receipt(
        self,
        *,
        receipt_id: str,
        lane: str,
        stage: str,
        measurement_opportunity_id: str | None = None,
        followup_task_id: str | None,
        remediation_episode_id: str | None,
        source_attempt_id: str | None,
        cold_attempt_id: str | None,
        cold_verification_id: str | None,
        dimensions: Mapping[str, Any],
        derived: Mapping[str, Any],
        telemetry_coverage: Mapping[str, Any],
        receipt_version: str,
        clock: Clock | None = None,
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO coldness_receipts(
                  id, lane, stage, measurement_opportunity_id,
                  followup_task_id, remediation_episode_id, source_attempt_id,
                  cold_attempt_id, cold_verification_id, dimensions_json,
                  derived_json, telemetry_coverage_json, receipt_version,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt_id,
                    lane,
                    stage,
                    measurement_opportunity_id,
                    followup_task_id,
                    remediation_episode_id,
                    source_attempt_id,
                    cold_attempt_id,
                    cold_verification_id,
                    _json(dict(dimensions)),
                    _json(dict(derived)),
                    _json(dict(telemetry_coverage)),
                    receipt_version,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        # The unique (task, stage) index may have kept an earlier row instead
        # of this id; return whichever row holds the slot.
        if followup_task_id is not None:
            return self.coldness_receipt_for_task_stage(followup_task_id, stage)
        if measurement_opportunity_id is not None:
            return self.coldness_receipt_for_opportunity_stage(
                measurement_opportunity_id, stage
            )
        return self.coldness_receipt(receipt_id)

    @staticmethod
    def _decode_coldness_receipt(row: Any) -> dict[str, Any]:
        payload = dict(row)
        payload["dimensions"] = _loads(payload.pop("dimensions_json"), {})
        payload["derived"] = _loads(payload.pop("derived_json"), {})
        payload["telemetry_coverage"] = _loads(
            payload.pop("telemetry_coverage_json"), {}
        )
        return payload

    def coldness_receipt(self, receipt_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM coldness_receipts WHERE id = ?", (receipt_id,)
            ).fetchone()
        return self._decode_coldness_receipt(row) if row is not None else None

    def coldness_receipt_for_task_stage(
        self, followup_task_id: str, stage: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM coldness_receipts
                 WHERE followup_task_id = ? AND stage = ?
                """,
                (followup_task_id, stage),
            ).fetchone()
        return self._decode_coldness_receipt(row) if row is not None else None

    def coldness_receipt_for_opportunity_stage(
        self, measurement_opportunity_id: str, stage: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM coldness_receipts
                 WHERE measurement_opportunity_id = ? AND stage = ?
                """,
                (measurement_opportunity_id, stage),
            ).fetchone()
        return self._decode_coldness_receipt(row) if row is not None else None

    def coldness_receipts_for_task(
        self, followup_task_id: str
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM coldness_receipts
                 WHERE followup_task_id = ?
                 ORDER BY created_at, id
                """,
                (followup_task_id,),
            ).fetchall()
        return [self._decode_coldness_receipt(row) for row in rows]

    def coldness_receipt_for_verification(
        self, cold_verification_id: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM coldness_receipts WHERE cold_verification_id = ?",
                (cold_verification_id,),
            ).fetchone()
        return self._decode_coldness_receipt(row) if row is not None else None

    def practice_attempts_between(
        self, *, after: str | None, before: str | None
    ) -> list[dict[str, Any]]:
        """Attempts in an open interval, oldest first — the exposure-scan read.

        Boundaries are EXCLUSIVE so the scan's anchor attempts (the primed
        source and the cold attempt itself, which sit exactly on the interval
        ends) never classify as their own intervening exposure; same-timestamp
        strangers are excluded by id in the service instead.
        """

        clauses: list[str] = []
        params: list[Any] = []
        if after is not None:
            clauses.append("created_at > ?")
            params.append(after)
        if before is not None:
            clauses.append("created_at < ?")
            params.append(before)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM practice_attempts {where}
                ORDER BY created_at, id
                """,
                params,
            ).fetchall()
        return [_decode_attempt(row) for row in rows]

    def practice_attempts_for_items_before(
        self,
        practice_item_ids: Sequence[str],
        *,
        before: str,
    ) -> list[dict[str, Any]]:
        """Prior administrations for a bounded candidate surface family.

        Receipt novelty checks know the finite set of item ids that resolve to
        the candidate's canonical surface group. Querying only those ids avoids
        replaying the learner's complete attempt history in a large vault.
        """

        item_ids = sorted({str(value) for value in practice_item_ids if value})
        if not item_ids:
            return []
        placeholders = ",".join("?" for _ in item_ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM practice_attempts
                 WHERE practice_item_id IN ({placeholders})
                   AND created_at < ?
                 ORDER BY created_at, id
                """,
                (*item_ids, before),
            ).fetchall()
        return [_decode_attempt(row) for row in rows]

    # -- certification cold probes (migration 139) --------------------------
    #
    # The §5.7 ground-truth store. Append-only: the table's triggers refuse an
    # UPDATE or DELETE, so the write is INSERT OR IGNORE over a content-addressed
    # id and re-recording the same probe is a no-op rather than a second label.

    def insert_certification_cold_probe_outcome(
        self,
        *,
        outcome_id: str,
        certificate_id: str,
        learning_object_id: str,
        blueprint_id: str,
        recipe_id: str,
        certificate_receipt: Mapping[str, Any],
        certified_at: str | None,
        followup_task_id: str,
        scheduled_not_before: str,
        scheduled_expires_at: str | None,
        horizon_days: float,
        window_days: float,
        probe_practice_item_id: str,
        probe_attempt_id: str,
        probe_surface_group: str,
        excluded_surface_groups: Sequence[str],
        held_out_basis: str,
        avoided_affordances: Sequence[str],
        verdict: str,
        indeterminate_reason: str | None,
        success: bool | None,
        correctness: float | None,
        success_threshold: float,
        assisted: bool,
        certificate_state_at_probe: str,
        store_version: str,
        policy_version: str,
        certification_algorithm_version: str | None,
        parameters: Mapping[str, Any],
        grading_source: str | None = None,
        grading_prompt_version: str | None = None,
        grader_model: str | None = None,
        grader_provider: str | None = None,
        grader_provider_revision: str | None = None,
        grading_agent_run_id: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO certification_cold_probe_outcomes(
                  id, certificate_id, learning_object_id, blueprint_id, recipe_id,
                  certificate_receipt_json, certified_at, followup_task_id,
                  scheduled_not_before, scheduled_expires_at, horizon_days,
                  window_days, probe_practice_item_id, probe_attempt_id,
                  probe_surface_group, excluded_surface_groups_json,
                  held_out_basis, avoided_affordances_json, verdict,
                  indeterminate_reason, success, correctness, success_threshold,
                  assisted, certificate_state_at_probe, store_version,
                  policy_version, certification_algorithm_version,
                  parameters_json, grading_source, grading_prompt_version,
                  grader_model, grader_provider, grader_provider_revision,
                  grading_agent_run_id, created_at
                ) VALUES (
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    outcome_id,
                    certificate_id,
                    learning_object_id,
                    blueprint_id,
                    recipe_id,
                    _json(dict(certificate_receipt)),
                    certified_at,
                    followup_task_id,
                    scheduled_not_before,
                    scheduled_expires_at,
                    float(horizon_days),
                    float(window_days),
                    probe_practice_item_id,
                    probe_attempt_id,
                    probe_surface_group,
                    _json(sorted({str(value) for value in excluded_surface_groups})),
                    held_out_basis,
                    _json(sorted({str(value) for value in avoided_affordances})),
                    verdict,
                    indeterminate_reason,
                    None if success is None else int(success),
                    None if correctness is None else float(correctness),
                    float(success_threshold),
                    int(bool(assisted)),
                    certificate_state_at_probe,
                    store_version,
                    policy_version,
                    certification_algorithm_version,
                    _json(dict(parameters)),
                    grading_source,
                    grading_prompt_version,
                    grader_model,
                    grader_provider,
                    grader_provider_revision,
                    grading_agent_run_id,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return self.certification_cold_probe_outcome_for_attempt(probe_attempt_id)

    def certification_cold_probe_outcome_for_attempt(
        self, probe_attempt_id: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM certification_cold_probe_outcomes
                 WHERE probe_attempt_id = ?
                """,
                (probe_attempt_id,),
            ).fetchone()
        return _decode_certification_cold_probe_outcome(row) if row is not None else None

    def certification_cold_probe_outcomes(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM certification_cold_probe_outcomes
                ORDER BY created_at, id
                """
            ).fetchall()
        return [_decode_certification_cold_probe_outcome(row) for row in rows]

    def _insert_grading_evidence(
        self,
        connection: sqlite3.Connection,
        attempt_id: str,
        row: Mapping[str, Any],
    ) -> None:
        connection.execute(
            """
            INSERT INTO grading_evidence(
              id, attempt_id, criterion_id, points_awarded, evidence, notes,
              agent_run_id, local_grader_id, grader_tier, created_at,
              superseded_at, superseded_by_evidence_id, learner_confidence,
              observation_id, grading_revision, assessment_contract_version_id,
              recipe_id, attribution_json, correlation_group
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("id") or new_ulid(),
                attempt_id,
                row["criterion_id"],
                row["points_awarded"],
                row.get("evidence"),
                row.get("notes"),
                row.get("agent_run_id"),
                row.get("local_grader_id"),
                row["grader_tier"],
                row["created_at"],
                row.get("superseded_at"),
                row.get("superseded_by_evidence_id"),
                row.get("learner_confidence"),
                # KM1 observation lineage: NULL under mvp-0.6 (unstamped rows),
                # so legacy replay reproduces byte-identical derived state.
                row.get("observation_id"),
                row.get("grading_revision"),
                row.get("assessment_contract_version_id"),
                row.get("recipe_id"),
                row.get("attribution_json"),
                row.get("correlation_group"),
            ),
        )

    def _insert_attempt_surprise(self, connection: sqlite3.Connection, surprise: Mapping[str, Any]) -> None:
        connection.execute(
            """
            INSERT INTO attempt_surprise(
              attempt_id, predicted_score_dist_json, predicted_error_type_dist_json,
              observed_joint_bucket_json, predictive_surprise, bayesian_surprise,
              surprise_direction, fsrs_interval_factor, posterior_delta_json,
              triggered_actions_json, suppressed_actions_json, gate_diagnostics_json,
              algorithm_version, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                surprise["attempt_id"],
                _json(surprise.get("predicted_score_dist")),
                _json(surprise.get("predicted_error_type_dist")),
                _json(surprise["observed_joint_bucket"]),
                surprise.get("predictive_surprise"),
                surprise.get("bayesian_surprise"),
                surprise.get("surprise_direction"),
                surprise.get("fsrs_interval_factor"),
                _json(surprise.get("posterior_delta")),
                _json(surprise.get("triggered_actions", [])),
                _json(surprise.get("suppressed_actions", [])),
                _json(surprise.get("gate_diagnostics")),
                surprise["algorithm_version"],
                surprise["created_at"],
            ),
        )

    def _insert_learning_outcome_labels(
        self,
        connection: sqlite3.Connection,
        attempt: Mapping[str, Any],
        *,
        algorithm_version: str,
        max_sources: int = 20,
    ) -> None:
        current = connection.execute(
            "SELECT * FROM practice_attempts WHERE id = ?",
            (attempt["id"],),
        ).fetchone()
        if current is None:
            return
        sources = connection.execute(
            """
            WITH sources AS (
                SELECT * FROM practice_attempts
                WHERE learning_object_id = ?
                  AND id != ?
                  AND created_at <= ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
            )
            SELECT sources.*, COUNT(intervening.id) AS intervening_attempt_count
            FROM sources
            LEFT JOIN practice_attempts AS intervening
              ON intervening.learning_object_id = ?
             AND intervening.id NOT IN (sources.id, ?)
             AND intervening.created_at > sources.created_at
             AND intervening.created_at < ?
            GROUP BY sources.id
            ORDER BY sources.created_at DESC, sources.id DESC
            """,
            (
                current["learning_object_id"],
                current["id"],
                current["created_at"],
                max_sources,
                current["learning_object_id"],
                current["id"],
                current["created_at"],
            ),
        ).fetchall()
        for source in sources:
            same_item = source["practice_item_id"] == current["practice_item_id"]
            label_type = "same_item_retention" if same_item else "same_learning_object_transfer"
            elapsed_seconds = _elapsed_seconds_between(source["created_at"], current["created_at"])
            metadata = {
                "source": _attempt_label_snapshot(source),
                "outcome": _attempt_label_snapshot(current),
                "label_version": LABEL_VERSION,
            }
            connection.execute(
                """
                INSERT OR IGNORE INTO learning_outcome_labels(
                  id, source_attempt_id, outcome_attempt_id, label_type,
                  practice_item_id, learning_object_id, label_value,
                  outcome_correctness, outcome_rubric_score, outcome_attempt_type,
                  outcome_hints_used, outcome_latency_seconds, elapsed_seconds,
                  intervening_attempt_count, metadata_json, algorithm_version, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _projection_id(
                        "lol",
                        source["id"],
                        current["id"],
                        label_type,
                    ),
                    source["id"],
                    current["id"],
                    label_type,
                    source["practice_item_id"],
                    source["learning_object_id"],
                    current["correctness"],
                    current["correctness"],
                    current["rubric_score"],
                    current["attempt_type"],
                    current["hints_used"],
                    current["latency_seconds"],
                    elapsed_seconds,
                    int(source["intervening_attempt_count"]),
                    _json(metadata),
                    algorithm_version,
                    current["created_at"],
                ),
            )

    # ------------------------------------------------------------------
    # Exam pool (held-out practice-exam item reservations)
    # ------------------------------------------------------------------

    def attempted_practice_item_ids(self) -> set[str]:
        """Practice item ids that have at least one recorded attempt."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT DISTINCT practice_item_id FROM practice_attempts"
            ).fetchall()
        return {row["practice_item_id"] for row in rows}

    # -- Learner Review changelog read models (§4.9) ----------------------
    #
    # Read models over grading_evidence / derived_state_rebuilds for the
    # system-authored Review changelog entries. Both reconstruct grading
    # "epochs" exactly as ``grading_correction_count_between`` does (distinct
    # ``grading_revision``, or legacy ``created_at``) so the regrade entries and
    # the per-session ``corrections`` count partition the same event set —
    # never double-counting a single regrade.

    def _grading_epoch_transitions(
        self, rows: list[sqlite3.Row]
    ) -> dict[str, list[dict[str, Any]]]:
        """Group ordered ``grading_evidence`` rows into per-attempt epochs and
        return, per attempt, the ordered old→new transitions (each grading epoch
        after the first). ``rows`` must already be ordered by attempt then time.
        """

        epochs_by_attempt: dict[str, dict[str, dict[str, Any]]] = {}
        for row in rows:
            attempt_id = str(row["attempt_id"])
            epoch_key = (
                f"revision:{row['grading_revision']}"
                if row["grading_revision"] is not None
                else f"legacy:{row['created_at']}"
            )
            epochs = epochs_by_attempt.setdefault(attempt_id, {})
            epoch = epochs.get(epoch_key)
            if epoch is None:
                epoch = {
                    "at": str(row["created_at"]),
                    "points": 0.0,
                    "practice_item_id": str(row["practice_item_id"]),
                    "learning_object_id": str(row["learning_object_id"]),
                }
                epochs[epoch_key] = epoch
            epoch["points"] += float(row["points_awarded"] or 0.0)
        transitions: dict[str, list[dict[str, Any]]] = {}
        for attempt_id, epochs in epochs_by_attempt.items():
            ordered = sorted(epochs.items(), key=lambda pair: (pair[1]["at"], pair[0]))
            attempt_transitions: list[dict[str, Any]] = []
            for (_prev_key, prev), (_curr_key, curr) in zip(ordered, ordered[1:], strict=False):
                attempt_transitions.append(
                    {
                        "attempt_id": attempt_id,
                        "practice_item_id": curr["practice_item_id"],
                        "learning_object_id": curr["learning_object_id"],
                        "old_points": prev["points"],
                        "new_points": curr["points"],
                        "at": curr["at"],
                    }
                )
            if attempt_transitions:
                transitions[attempt_id] = attempt_transitions
        return transitions

    def regrade_epoch_transitions(self) -> list[dict[str, Any]]:
        """Every post-original grading epoch across all attempts, as an old→new
        transition with the attempt's item/LO references and the epoch time.
        A regrade is a grading epoch after the first for an attempt.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT e.attempt_id, e.grading_revision, e.created_at,
                       e.points_awarded, a.practice_item_id, a.learning_object_id
                FROM grading_evidence e
                JOIN practice_attempts a ON a.id = e.attempt_id
                ORDER BY e.attempt_id, e.created_at,
                         COALESCE(e.grading_revision, -1), e.id
                """
            ).fetchall()
        transitions: list[dict[str, Any]] = []
        for attempt_transitions in self._grading_epoch_transitions(rows).values():
            transitions.extend(attempt_transitions)
        transitions.sort(key=lambda t: (t["at"], t["attempt_id"]))
        return transitions

    def attempt_regrade_marker(self, attempt_id: str) -> dict[str, Any] | None:
        """The most recent regrade (old→new score) persisted for one attempt, or
        ``None`` when the attempt has only its original grading epoch. Derived
        from ``grading_evidence`` epochs — a template-rendered ledger fact.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT e.attempt_id, e.grading_revision, e.created_at,
                       e.points_awarded, a.practice_item_id, a.learning_object_id
                FROM grading_evidence e
                JOIN practice_attempts a ON a.id = e.attempt_id
                WHERE e.attempt_id = ?
                ORDER BY e.created_at, COALESCE(e.grading_revision, -1), e.id
                """,
                (attempt_id,),
            ).fetchall()
        attempt_transitions = self._grading_epoch_transitions(rows).get(attempt_id)
        if not attempt_transitions:
            return None
        return attempt_transitions[-1]
