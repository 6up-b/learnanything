"""Commitments, goal contracts, exams and forecasts.

Owns commitments and their versions, targets, events and arcs; goal contracts,
heads and events; exam sessions, predictions and answers; forecasts."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Iterable, Mapping, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.row_serialization import _json, _loads
from learnloop.ids import new_ulid


class StaleContractHead(Exception):
    """The predecessor a successor was built against is no longer the head (L3,
    §3.4). A concurrent writer advanced the goal-contract head between the caller's
    read and its append; the caller must re-read the head and rebuild."""

    def __init__(self, goal_id: str, *, expected: str | None, actual: str | None):
        self.goal_id = goal_id
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"stale goal-contract head for {goal_id}: predecessor {expected!r} "
            f"is not the current head {actual!r}"
        )


def _decode_forecast(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["model_coverage"] = _loads(payload.pop("model_coverage_json"), {})
    return payload


def _decode_exam_session(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["item_order"] = _loads(payload.pop("item_order_json"), [])
    payload["report"] = _loads(payload.pop("report_json"), None)
    return payload


def _decode_exam_prediction(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["facet_projection"] = _loads(payload.pop("facet_projection_json"), None)
    return payload


def _decode_exam_answer(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["grade"] = _loads(payload.pop("grade_json"), None)
    return payload


class GoalStoreMixin:

    # -- Frozen forecast ledger -------------------------------------------

    def insert_forecast(self, values: Mapping[str, Any]) -> dict[str, Any]:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO forecasts(
                  id, goal_id, kind, issued_at, as_of_input_snapshot_hash,
                  algorithm_version, resolution_rule_version, horizon,
                  target_metric, predicted_value, model_coverage_json, status,
                  resolved_value, resolved_at, projection_drift
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    values["id"], values["goal_id"], values["kind"], values["issued_at"],
                    values["as_of_input_snapshot_hash"], values["algorithm_version"],
                    values["resolution_rule_version"], values["horizon"],
                    values["target_metric"], float(values["predicted_value"]),
                    _json(dict(values.get("model_coverage") or {})),
                    values.get("status", "open"), values.get("resolved_value"),
                    values.get("resolved_at"), values.get("projection_drift"),
                ),
            )
            row = connection.execute(
                """
                SELECT * FROM forecasts
                WHERE goal_id = ? AND kind = ? AND as_of_input_snapshot_hash = ?
                """,
                (
                    values["goal_id"], values["kind"],
                    values["as_of_input_snapshot_hash"],
                ),
            ).fetchone()
            connection.commit()
        assert row is not None
        return _decode_forecast(row)

    def forecast(self, forecast_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM forecasts WHERE id = ?", (forecast_id,)).fetchone()
        return _decode_forecast(row) if row is not None else None

    def due_forecasts(self, at: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM forecasts
                WHERE status = 'open' AND horizon <= ?
                ORDER BY horizon, issued_at, id
                """,
                (at,),
            ).fetchall()
        return [_decode_forecast(row) for row in rows]

    def update_forecast_resolution(
        self,
        forecast_id: str,
        *,
        status: str,
        resolved_at: str,
        resolved_value: float | None = None,
        projection_drift: float | None = None,
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE forecasts
                SET status = ?, resolved_value = ?, resolved_at = ?, projection_drift = ?
                WHERE id = ? AND status = 'open'
                """,
                (status, resolved_value, resolved_at, projection_drift, forecast_id),
            )
            connection.commit()
        return self.forecast(forecast_id)

    def list_forecasts(self, goal_id: str | None = None) -> list[dict[str, Any]]:
        with self.connection() as connection:
            if goal_id is None:
                rows = connection.execute(
                    "SELECT * FROM forecasts ORDER BY issued_at, id"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM forecasts WHERE goal_id = ? ORDER BY issued_at, id",
                    (goal_id,),
                ).fetchall()
        return [_decode_forecast(row) for row in rows]

    def open_forecasts(self, goal_id: str) -> list[dict[str, Any]]:
        """Read-only: open (unresolved) forecast rows for a goal, oldest first.

        Rendering reads these to reference the current issued forecast id; it
        never issues one (spec §4.1).
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM forecasts
                WHERE goal_id = ? AND status = 'open'
                ORDER BY issued_at, id
                """,
                (goal_id,),
            ).fetchall()
        return [_decode_forecast(row) for row in rows]

    # ------------------------------------------------------------------
    # Goal terminal contracts (§3.4, migration 068). Confirmed versions are
    # IMMUTABLE (never UPDATEd); the head is a rewritten projection; drafts are
    # non-pinnable. append_goal_contract_version does the version-row insert +
    # head-projection rewrite atomically so the head cannot skip a version.
    # ------------------------------------------------------------------

    def append_goal_contract_version(
        self,
        *,
        goal_id: str,
        version: int,
        predecessor_version_id: str | None,
        contract_json: str,
        content_hash: str,
        support_hash: str,
        contract_schema_version: int,
        change_class: str,
        envelope_version: str | None = None,
        predecessor_milestone: str | None = None,
        activated_edge_id: str | None = None,
        evidence_receipt_json: str | None = None,
        burden_delta_json: str | None = None,
        author: str,
        reason: str | None = None,
        head_envelope_version: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Append an immutable version row and rewrite the head projection in one
        transaction. On a byte-identical re-confirm (UNIQUE(goal_id, content_hash))
        returns the existing row with ``already_exists=True`` and leaves the head
        untouched."""

        now = utc_now_iso(clock)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM goal_contract_versions WHERE goal_id = ? AND content_hash = ?",
                (goal_id, content_hash),
            ).fetchone()
            if existing is not None:
                connection.execute("ROLLBACK")
                return {"version": dict(existing), "already_exists": True}
            # L3 (§3.4): verify the predecessor is still the head INSIDE the
            # transaction. A concurrent successor that advanced the head between the
            # caller's read and this append must fail as StaleContractHead, never
            # silently fork or clobber the head projection.
            head_row = connection.execute(
                "SELECT head_version_id FROM goal_contract_heads WHERE goal_id = ?",
                (goal_id,),
            ).fetchone()
            current_head_id = head_row["head_version_id"] if head_row else None
            if predecessor_version_id != current_head_id:
                connection.execute("ROLLBACK")
                raise StaleContractHead(
                    goal_id, expected=predecessor_version_id, actual=current_head_id
                )
            version_id = new_ulid()
            connection.execute(
                """
                INSERT INTO goal_contract_versions(
                  id, goal_id, version, predecessor_version_id, contract_json,
                  content_hash, support_hash, contract_schema_version, change_class,
                  envelope_version, predecessor_milestone, activated_edge_id,
                  evidence_receipt_json, burden_delta_json, author, reason, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id, goal_id, version, predecessor_version_id, contract_json,
                    content_hash, support_hash, contract_schema_version, change_class,
                    envelope_version, predecessor_milestone, activated_edge_id,
                    evidence_receipt_json, burden_delta_json, author, reason, now,
                ),
            )
            connection.execute(
                """
                INSERT INTO goal_contract_heads(
                  goal_id, head_version_id, head_version, head_content_hash,
                  head_support_hash, head_envelope_version, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(goal_id) DO UPDATE SET
                  head_version_id = excluded.head_version_id,
                  head_version = excluded.head_version,
                  head_content_hash = excluded.head_content_hash,
                  head_support_hash = excluded.head_support_hash,
                  head_envelope_version = excluded.head_envelope_version,
                  updated_at = excluded.updated_at
                """,
                (
                    goal_id, version_id, version, content_hash,
                    support_hash, head_envelope_version, now,
                ),
            )
            row = connection.execute(
                "SELECT * FROM goal_contract_versions WHERE id = ?", (version_id,)
            ).fetchone()
            connection.execute("COMMIT")
            return {"version": dict(row), "already_exists": False}
        except StaleContractHead:
            raise
        except sqlite3.IntegrityError:
            # L3: a racing successor slipped in between the head check and COMMIT
            # (UNIQUE(goal_id, version)). Re-read the head and surface it as a
            # StaleContractHead where the predecessor no longer matches.
            connection.execute("ROLLBACK")
            head_row = connection.execute(
                "SELECT head_version_id FROM goal_contract_heads WHERE goal_id = ?",
                (goal_id,),
            ).fetchone()
            actual = head_row["head_version_id"] if head_row else None
            if actual != predecessor_version_id:
                raise StaleContractHead(
                    goal_id, expected=predecessor_version_id, actual=actual
                )
            raise
        except Exception:
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def fetch_goal_contract_head(self, goal_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM goal_contract_heads WHERE goal_id = ?", (goal_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def fetch_goal_contract_version(self, version_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM goal_contract_versions WHERE id = ?", (version_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def goal_contract_versions_for_goal(self, goal_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM goal_contract_versions WHERE goal_id = ? ORDER BY version",
                (goal_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_goal_contract_draft(
        self,
        *,
        goal_id: str,
        predecessor_version_id: str | None,
        proposed_contract_json: str,
        proposed_change_class: str | None,
        rejection_reason: str,
        requires: str,
        author: str,
        evidence_receipt_json: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        draft_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO goal_contract_drafts(
                  id, goal_id, predecessor_version_id, proposed_contract_json,
                  proposed_change_class, rejection_reason, evidence_receipt_json,
                  requires, author, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    draft_id, goal_id, predecessor_version_id, proposed_contract_json,
                    proposed_change_class, rejection_reason, evidence_receipt_json,
                    requires, author, utc_now_iso(clock),
                ),
            )
            connection.commit()
        return draft_id

    def goal_contract_drafts_for_goal(self, goal_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM goal_contract_drafts WHERE goal_id = ? ORDER BY created_at, id",
                (goal_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # P3 slice 3 -- commitment arcs (migration 095, spec §10.1)
    # ------------------------------------------------------------------

    def create_commitment_arc(
        self, *, commitment_id: str, source_id: str | None = None, clock: Clock | None = None
    ) -> str:
        arc_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO commitment_arcs(id, commitment_id, source_id, created_at) "
                "VALUES (?, ?, ?, ?)",
                (arc_id, commitment_id, source_id, utc_now_iso(clock)),
            )
            connection.commit()
        return arc_id

    def append_commitment_arc_version(
        self, *, arc_id: str, version: Mapping[str, Any], clock: Clock | None = None
    ) -> dict[str, Any]:
        now = utc_now_iso(clock)
        version_id = new_ulid()
        connection = self.connection()
        try:
            # Immediate: a deferred read that later asks for the write lock fails at once ("database is locked", no
            # busy wait) when another connection committed in between.
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT id, version_ordinal FROM commitment_arc_versions "
                "WHERE arc_id = ? ORDER BY version_ordinal DESC LIMIT 1",
                (arc_id,),
            ).fetchone()
            ordinal = (int(row["version_ordinal"]) + 1) if row is not None else 1
            predecessor = row["id"] if row is not None else None
            connection.execute(
                """
                INSERT INTO commitment_arc_versions(
                  id, arc_id, version_ordinal, predecessor_version_id, pattern_refs_json,
                  stages_json, depth_policy_version_id, depth_envelope_version_id,
                  stage_milestone_map_json, content_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id, arc_id, ordinal, predecessor,
                    _json(version.get("pattern_refs", [])),
                    _json(version.get("stages", [])),
                    version.get("depth_policy_version_id"),
                    version.get("depth_envelope_version_id"),
                    _json(version.get("stage_milestone_map", {})),
                    version["content_hash"], now,
                ),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return {"version_id": version_id, "version_ordinal": ordinal}

    def append_commitment_arc_event(
        self, *, arc_id: str, kind: str, detail: Mapping[str, Any] | None = None,
        receipt_key: str | None = None, clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Append an arc event. Idempotent on (arc_id, receipt_key): a replayed
        decision receipt returns the existing event without appending (§10.2)."""

        now = utc_now_iso(clock)
        connection = self.connection()
        try:
            connection.execute("BEGIN IMMEDIATE")  # as in append_commitment_arc_version: it reads, then writes
            if receipt_key is not None:
                existing = connection.execute(
                    "SELECT id, event_ordinal FROM commitment_arc_events "
                    "WHERE arc_id = ? AND receipt_key = ?",
                    (arc_id, receipt_key),
                ).fetchone()
                if existing is not None:
                    connection.commit()
                    return {"event_id": existing["id"], "event_ordinal": existing["event_ordinal"],
                            "already": True}
            row = connection.execute(
                "SELECT COALESCE(MAX(event_ordinal), 0) AS m FROM commitment_arc_events WHERE arc_id = ?",
                (arc_id,),
            ).fetchone()
            ordinal = int(row["m"]) + 1
            event_id = new_ulid()
            connection.execute(
                "INSERT INTO commitment_arc_events("
                "id, arc_id, event_ordinal, kind, detail_json, receipt_key, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (event_id, arc_id, ordinal, kind,
                 _json(dict(detail)) if detail is not None else None, receipt_key, now),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return {"event_id": event_id, "event_ordinal": ordinal, "already": False}

    def commitment_arc_head_version(self, arc_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM commitment_arc_versions WHERE arc_id = ? "
                "ORDER BY version_ordinal DESC LIMIT 1",
                (arc_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def commitment_arc(self, arc_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM commitment_arcs WHERE id = ?", (arc_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def commitment_arc_events(self, arc_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM commitment_arc_events WHERE arc_id = ? ORDER BY event_ordinal",
                (arc_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def arcs_for_commitment(self, commitment_id: str) -> list[str]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT id FROM commitment_arcs WHERE commitment_id = ? ORDER BY created_at, id",
                (commitment_id,),
            ).fetchall()
        return [r["id"] for r in rows]

    def reserved_exam_pool_items(self, goal_id: str) -> list[dict[str, Any]]:
        """Unreleased pool reservations for a goal, in reservation order."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM exam_pool_items
                WHERE goal_id = ? AND released_at IS NULL
                ORDER BY reserved_at, id
                """,
                (goal_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def reserved_exam_pool_item_ids(self) -> set[str]:
        """All practice item ids currently reserved (unreleased) across goals."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT practice_item_id FROM exam_pool_items WHERE released_at IS NULL"
            ).fetchall()
        return {row["practice_item_id"] for row in rows}

    def insert_exam_pool_items(self, rows: Iterable[Mapping[str, Any]]) -> None:
        with self.connection() as connection:
            for row in rows:
                connection.execute(
                    """
                    INSERT INTO exam_pool_items(
                      id, goal_id, practice_item_id, facet_id, difficulty_stratum,
                      reserved_at, released_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"],
                        row["goal_id"],
                        row["practice_item_id"],
                        row.get("facet_id"),
                        row.get("difficulty_stratum"),
                        row["reserved_at"],
                        row.get("released_at"),
                    ),
                )
            connection.commit()

    def release_exam_pool(self, goal_id: str, *, clock: Clock | None = None) -> list[str]:
        """Release every unreleased reservation for a goal; return the item ids."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT practice_item_id FROM exam_pool_items WHERE goal_id = ? AND released_at IS NULL",
                (goal_id,),
            ).fetchall()
            item_ids = [row["practice_item_id"] for row in rows]
            connection.execute(
                "UPDATE exam_pool_items SET released_at = ? WHERE goal_id = ? AND released_at IS NULL",
                (now, goal_id),
            )
            connection.commit()
        return item_ids

    def release_exam_pool_items(
        self, goal_id: str, practice_item_ids: Iterable[str], *, clock: Clock | None = None
    ) -> list[str]:
        """Release some of a goal's unreleased reservations (the rows stay, with
        ``released_at``); return the item ids released."""

        wanted = sorted({str(item_id) for item_id in practice_item_ids})
        if not wanted:
            return []
        now = utc_now_iso(clock)
        marks = ", ".join("?" for _ in wanted)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT practice_item_id FROM exam_pool_items WHERE goal_id = ? AND released_at IS NULL "
                f"AND practice_item_id IN ({marks})",
                (goal_id, *wanted),
            ).fetchall()
            connection.execute(
                f"UPDATE exam_pool_items SET released_at = ? WHERE goal_id = ? AND released_at IS NULL "
                f"AND practice_item_id IN ({marks})",
                (now, goal_id, *wanted),
            )
            connection.commit()
        return [row["practice_item_id"] for row in rows]

    # ------------------------------------------------------------------
    # Exam sessions
    # ------------------------------------------------------------------

    def insert_exam_session(self, session: Mapping[str, Any]) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO exam_sessions(
                  id, goal_id, status, item_order_json, report_json,
                  started_at, updated_at, completed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session["id"],
                    session["goal_id"],
                    session["status"],
                    _json(session.get("item_order") or []),
                    _json(session["report"]) if session.get("report") is not None else None,
                    session["started_at"],
                    session["updated_at"],
                    session.get("completed_at"),
                ),
            )
            connection.commit()

    def exam_session(self, session_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM exam_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        return _decode_exam_session(row) if row is not None else None

    def exam_session_in_progress_for_goal(self, goal_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM exam_sessions
                WHERE goal_id = ? AND status = 'in_progress'
                ORDER BY started_at DESC, id DESC
                LIMIT 1
                """,
                (goal_id,),
            ).fetchone()
        return _decode_exam_session(row) if row is not None else None

    def latest_completed_exam_session(self, goal_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM exam_sessions
                WHERE goal_id = ? AND status = 'completed'
                ORDER BY completed_at DESC, id DESC
                LIMIT 1
                """,
                (goal_id,),
            ).fetchone()
        return _decode_exam_session(row) if row is not None else None

    def update_exam_session(
        self,
        session_id: str,
        *,
        status: str | None = None,
        report: Any | None = None,
        completed_at: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        sets = ["updated_at = ?"]
        params: list[Any] = [now]
        if status is not None:
            sets.append("status = ?")
            params.append(status)
        if report is not None:
            sets.append("report_json = ?")
            params.append(_json(report))
        if completed_at is not None:
            sets.append("completed_at = ?")
            params.append(completed_at)
        params.append(session_id)
        with self.connection() as connection:
            connection.execute(
                f"UPDATE exam_sessions SET {', '.join(sets)} WHERE id = ?",
                params,
            )
            connection.commit()

    def insert_exam_predictions(self, rows: Iterable[Mapping[str, Any]]) -> None:
        with self.connection() as connection:
            for row in rows:
                connection.execute(
                    """
                    INSERT INTO exam_predictions(
                      id, session_id, practice_item_id, predicted_correctness,
                      facet_projection_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"],
                        row["session_id"],
                        row["practice_item_id"],
                        float(row["predicted_correctness"]),
                        _json(row.get("facet_projection"))
                        if row.get("facet_projection") is not None
                        else None,
                        row["created_at"],
                    ),
                )
            connection.commit()

    def exam_predictions(self, session_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM exam_predictions WHERE session_id = ? ORDER BY created_at, id",
                (session_id,),
            ).fetchall()
        return [_decode_exam_prediction(row) for row in rows]

    def all_exam_predictions(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM exam_predictions ORDER BY session_id, created_at, id"
            ).fetchall()
        return [_decode_exam_prediction(row) for row in rows]

    def upsert_exam_answer(self, answer: Mapping[str, Any], *, clock: Clock | None = None) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO exam_answers(
                  id, session_id, practice_item_id, answer_md, rubric_score,
                  correctness, grade_json, attempt_id, answered_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id, practice_item_id) DO UPDATE SET
                  answer_md = excluded.answer_md,
                  rubric_score = excluded.rubric_score,
                  correctness = excluded.correctness,
                  grade_json = excluded.grade_json,
                  -- an answer's link is written once, by finish (``set_exam_answer_attempt_id``): never cleared here
                  attempt_id = COALESCE(exam_answers.attempt_id, excluded.attempt_id),
                  updated_at = excluded.updated_at
                """,
                (
                    answer.get("id") or new_ulid(),
                    answer["session_id"],
                    answer["practice_item_id"],
                    answer.get("answer_md"),
                    answer.get("rubric_score"),
                    answer.get("correctness"),
                    _json(answer.get("grade")) if answer.get("grade") is not None else None,
                    answer.get("attempt_id"),
                    answer.get("answered_at") or now,
                    now,
                ),
            )
            connection.commit()

    def set_exam_answer_attempt_id(self, session_id: str, practice_item_id: str, attempt_id: str) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE exam_answers SET attempt_id = ? WHERE session_id = ? AND practice_item_id = ?",
                (attempt_id, session_id, practice_item_id),
            )
            connection.commit()

    def exam_answer(
        self, session_id: str, practice_item_id: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM exam_answers
                WHERE session_id = ? AND practice_item_id = ?
                """,
                (session_id, practice_item_id),
            ).fetchone()
        return _decode_exam_answer(row) if row is not None else None

    def exam_answers(self, session_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM exam_answers WHERE session_id = ? ORDER BY answered_at, id",
                (session_id,),
            ).fetchall()
        return [_decode_exam_answer(row) for row in rows]

    # ------------------------------------------------------------------
    # P1 step 1 -- commitments + depth objects (migration 072)
    # ------------------------------------------------------------------

    def ensure_depth_policy_version(
        self, *, policy: str, body_json: str, content_hash: str, clock: Clock | None = None
    ) -> str:
        """Immutable, content-addressed depth policy version (idempotent on hash)."""

        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM depth_policy_versions WHERE content_hash = ?", (content_hash,)
            ).fetchone()
            if existing is not None:
                return existing["id"]
            version_id = new_ulid()
            connection.execute(
                """
                INSERT INTO depth_policy_versions(id, policy, body_json, content_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (version_id, policy, body_json, content_hash, utc_now_iso(clock)),
            )
            connection.commit()
        return version_id

    def ensure_depth_envelope_version(
        self,
        *,
        envelope_version: str,
        bounds_json: str,
        reviewed_edges_json: str,
        content_hash: str,
        clock: Clock | None = None,
    ) -> str:
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM depth_envelope_versions WHERE content_hash = ?", (content_hash,)
            ).fetchone()
            if existing is not None:
                return existing["id"]
            version_id = new_ulid()
            connection.execute(
                """
                INSERT INTO depth_envelope_versions(
                  id, envelope_version, bounds_json, reviewed_edges_json, content_hash, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id, envelope_version, bounds_json, reviewed_edges_json,
                    content_hash, utc_now_iso(clock),
                ),
            )
            connection.commit()
        return version_id

    def depth_policy_version(self, policy_version_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM depth_policy_versions WHERE id = ?", (policy_version_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def depth_envelope_version(self, envelope_version_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM depth_envelope_versions WHERE id = ?", (envelope_version_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    # --- depth-edge authoring (migration 107) --------------------------------

    def insert_depth_edge_template(
        self, *, template_slug: str, domain_scope: Mapping[str, Any] | None = None, clock: Clock | None = None
    ) -> str:
        template_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO depth_edge_templates(id, template_slug, domain_scope_json, created_at) "
                "VALUES (?, ?, ?, ?)",
                (template_id, template_slug, json.dumps(domain_scope) if domain_scope else None, utc_now_iso(clock)),
            )
            connection.commit()
        return template_id

    def depth_edge_template_by_slug(self, template_slug: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM depth_edge_templates WHERE template_slug = ?", (template_slug,)
            ).fetchone()
        return dict(row) if row is not None else None

    def depth_edge_templates(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM depth_edge_templates ORDER BY template_slug"
            ).fetchall()
        return [dict(r) for r in rows]

    def insert_depth_edge_template_version(
        self,
        *,
        template_id: str,
        version: int,
        body_json: str,
        content_hash: str,
        status: str = "draft",
        clock: Clock | None = None,
    ) -> str:
        version_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO depth_edge_template_versions(
                  id, template_id, version, body_json, content_hash, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (version_id, template_id, version, body_json, content_hash, status, utc_now_iso(clock)),
            )
            connection.commit()
        return version_id

    def depth_edge_template_version(self, version_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM depth_edge_template_versions WHERE id = ?", (version_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def depth_edge_template_versions_for(self, template_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM depth_edge_template_versions WHERE template_id = ? ORDER BY version",
                (template_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def review_depth_edge_template_version(
        self, version_id: str, *, status: str, reviewed_by: str, clock: Clock | None = None
    ) -> bool:
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE depth_edge_template_versions SET status = ?, reviewed_by = ?, reviewed_at = ? "
                "WHERE id = ?",
                (status, reviewed_by, utc_now_iso(clock), version_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    def insert_depth_edge_instance(self, instance: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        instance_id = str(instance.get("id") or new_ulid())
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO depth_edge_instances(
                  id, template_version_id, commitment_id, edge_id, predecessor_milestone,
                  successor_milestone_slug, successor_task_contract_json, entry_evidence_json,
                  exit_evidence_json, fresh_proof_json, expected_burden_json, activity_path_json,
                  status, admission_report_json, pinned_envelope_version_id, receipt_key,
                  author, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    instance_id,
                    instance["template_version_id"],
                    instance["commitment_id"],
                    instance["edge_id"],
                    instance["predecessor_milestone"],
                    instance["successor_milestone_slug"],
                    instance["successor_task_contract_json"],
                    instance.get("entry_evidence_json"),
                    instance.get("exit_evidence_json"),
                    instance.get("fresh_proof_json"),
                    instance.get("expected_burden_json"),
                    instance.get("activity_path_json"),
                    instance.get("status") or "proposed",
                    instance.get("admission_report_json"),
                    instance.get("pinned_envelope_version_id"),
                    instance.get("receipt_key"),
                    instance.get("author"),
                    now,
                    now,
                ),
            )
            connection.commit()
        return instance_id

    def depth_edge_instance(self, instance_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM depth_edge_instances WHERE id = ?", (instance_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def depth_edge_instances_for(
        self, commitment_id: str, *, status: str | None = None
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM depth_edge_instances WHERE commitment_id = ?"
        params: list[Any] = [commitment_id]
        if status is not None:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def update_depth_edge_instance_status(
        self,
        instance_id: str,
        *,
        status: str,
        admission_report_json: str | None = None,
        pinned_envelope_version_id: str | None = None,
        clock: Clock | None = None,
    ) -> bool:
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE depth_edge_instances
                SET status = ?,
                    admission_report_json = COALESCE(?, admission_report_json),
                    pinned_envelope_version_id = COALESCE(?, pinned_envelope_version_id),
                    updated_at = ?
                WHERE id = ?
                """,
                (status, admission_report_json, pinned_envelope_version_id, utc_now_iso(clock), instance_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    def depth_milestone_version_for(
        self, envelope_version_id: str, milestone_slug: str
    ) -> dict[str, Any] | None:
        """Latest milestone version for (envelope version, slug) — the rung
        projection seam (``learnloop.curriculum.depth_rungs``)."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM depth_milestone_versions
                WHERE envelope_version_id = ? AND milestone_slug = ?
                ORDER BY created_at DESC, id DESC LIMIT 1
                """,
                (envelope_version_id, milestone_slug),
            ).fetchone()
        return dict(row) if row is not None else None

    def insert_depth_milestone_version(
        self,
        *,
        envelope_version_id: str,
        milestone_slug: str,
        task_contract_json: str,
        entry_evidence_json: str | None = None,
        exit_evidence_json: str | None = None,
        fresh_proof_json: str | None = None,
        expected_burden_json: str | None = None,
        content_hash: str,
        clock: Clock | None = None,
    ) -> str:
        with self.connection() as connection:
            version_id = new_ulid()
            connection.execute(
                """
                INSERT INTO depth_milestone_versions(
                  id, envelope_version_id, milestone_slug, task_contract_json,
                  entry_evidence_json, exit_evidence_json, fresh_proof_json,
                  expected_burden_json, content_hash, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id, envelope_version_id, milestone_slug, task_contract_json,
                    entry_evidence_json, exit_evidence_json, fresh_proof_json,
                    expected_burden_json, content_hash, utc_now_iso(clock),
                ),
            )
            connection.commit()
        return version_id

    def _insert_commitment_version_rows(
        self,
        connection: sqlite3.Connection,
        *,
        commitment_id: str,
        predecessor_version_id: str | None,
        version: int,
        version_fields: Mapping[str, Any],
        targets: Sequence[Mapping[str, Any]],
        author: str,
        change_reason: str | None,
        events: Sequence[Mapping[str, Any]],
        now: str,
    ) -> str:
        version_id = new_ulid()
        connection.execute(
            """
            INSERT INTO commitment_versions(
              id, commitment_id, version, predecessor_version_id, intent_text,
              interpretation_text, goal_id, depth_preset, depth_policy_version_id,
              depth_envelope_version_id, attention_bounds_json, due_hint, hiatus_hint,
              reason, provenance_json, target_set_hash, version_hash, change_reason,
              author, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version_id, commitment_id, version, predecessor_version_id,
                version_fields["intent_text"], version_fields["interpretation_text"],
                version_fields["goal_id"], version_fields["depth_preset"],
                version_fields["depth_policy_version_id"],
                version_fields["depth_envelope_version_id"],
                version_fields["attention_bounds_json"], version_fields["due_hint"],
                version_fields["hiatus_hint"], version_fields["reason"],
                version_fields["provenance_json"], version_fields["target_set_hash"],
                version_fields["version_hash"], change_reason, author, now,
            ),
        )
        for target in targets:
            connection.execute(
                """
                INSERT INTO commitment_target_versions(
                  id, commitment_version_id, target_kind, target_ref, salience, role,
                  provenance_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_ulid(), version_id, target["target_kind"], target["target_ref"],
                    target.get("salience"), target["role"], target.get("provenance_json"), now,
                ),
            )
        for event in events:
            detail = event.get("detail")
            connection.execute(
                """
                INSERT INTO commitment_events(
                  id, commitment_id, commitment_version_id, kind, detail_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    new_ulid(), commitment_id, version_id, event["kind"],
                    _json(detail) if detail is not None else event.get("detail_json"), now,
                ),
            )
        return version_id

    def create_commitment(
        self,
        *,
        learner_id: str,
        created_action: str,
        idempotency_key: str | None,
        version_fields: Mapping[str, Any],
        targets: Sequence[Mapping[str, Any]],
        author: str,
        change_reason: str | None,
        clock: Clock | None = None,
    ) -> tuple[str, bool]:
        """Atomically insert the stable commitment, its v1 version, target rows, and
        the ``created`` event in one transaction. Returns ``(commitment_id, created)``.

        B6: when a client idempotency key collides with a concurrent create (the
        migration-080 partial UNIQUE index fires ``IntegrityError``), the transaction
        rolls back and the existing WINNER id is returned with ``created=False`` --
        one (learner, action, idempotency_key) yields exactly one commitment even
        under a race the service-level SELECT could miss."""

        now = utc_now_iso(clock)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("BEGIN IMMEDIATE")
            commitment_id = new_ulid()
            try:
                connection.execute(
                    """
                    INSERT INTO commitments(
                      id, learner_id, created_action, idempotency_key, created_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (commitment_id, learner_id, created_action, idempotency_key, now),
                )
            except sqlite3.IntegrityError:
                connection.execute("ROLLBACK")
                if idempotency_key is None:
                    raise
                winner = connection.execute(
                    """
                    SELECT id FROM commitments
                     WHERE learner_id = ? AND created_action = ? AND idempotency_key = ?
                     ORDER BY created_at, id LIMIT 1
                    """,
                    (learner_id, created_action, idempotency_key),
                ).fetchone()
                if winner is None:
                    raise
                return winner["id"], False
            self._insert_commitment_version_rows(
                connection,
                commitment_id=commitment_id,
                predecessor_version_id=None,
                version=1,
                version_fields=version_fields,
                targets=targets,
                author=author,
                change_reason=change_reason,
                events=[{"kind": "created", "detail": {"action": created_action}}],
                now=now,
            )
            connection.execute("COMMIT")
            return commitment_id, True
        except Exception:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise
        finally:
            connection.close()

    def append_commitment_version(
        self,
        *,
        commitment_id: str,
        predecessor_version_id: str | None,
        version: int,
        version_fields: Mapping[str, Any],
        targets: Sequence[Mapping[str, Any]],
        author: str,
        change_reason: str | None,
        events: Sequence[Mapping[str, Any]],
        clock: Clock | None = None,
    ) -> str:
        now = utc_now_iso(clock)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("BEGIN IMMEDIATE")
            version_id = self._insert_commitment_version_rows(
                connection,
                commitment_id=commitment_id,
                predecessor_version_id=predecessor_version_id,
                version=version,
                version_fields=version_fields,
                targets=targets,
                author=author,
                change_reason=change_reason,
                events=events,
                now=now,
            )
            connection.execute("COMMIT")
            return version_id
        except Exception:
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def append_commitment_event(
        self,
        *,
        commitment_id: str,
        commitment_version_id: str | None,
        kind: str,
        detail_json: str | None,
        clock: Clock | None = None,
    ) -> str:
        with self.connection() as connection:
            event_id = new_ulid()
            connection.execute(
                """
                INSERT INTO commitment_events(
                  id, commitment_id, commitment_version_id, kind, detail_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_id, commitment_id, commitment_version_id, kind, detail_json, utc_now_iso(clock)),
            )
            connection.commit()
        return event_id

    def commitment(self, commitment_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM commitments WHERE id = ?", (commitment_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def commitment_head(self, commitment_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM commitment_versions
                 WHERE commitment_id = ?
                 ORDER BY version DESC LIMIT 1
                """,
                (commitment_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def commitment_versions_for(self, commitment_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM commitment_versions WHERE commitment_id = ? ORDER BY version",
                (commitment_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def commitment_targets_for_version(self, commitment_version_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM commitment_target_versions
                 WHERE commitment_version_id = ? ORDER BY created_at, id
                """,
                (commitment_version_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def commitment_events_for(self, commitment_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM commitment_events
                 WHERE commitment_id = ? ORDER BY created_at, id
                """,
                (commitment_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def commitments_targeting(self, target_ref: str) -> list[str]:
        """Commitment ids whose HEAD version carries a target with this ref
        (any target kind). Used by rung_variants to authorize harder-than-
        default-trajectory work through a commitment's depth envelope."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT c.id FROM commitments c
                  JOIN commitment_versions v ON v.commitment_id = c.id
                  JOIN commitment_target_versions t ON t.commitment_version_id = v.id
                 WHERE t.target_ref = ?
                   AND v.version = (
                     SELECT MAX(version) FROM commitment_versions WHERE commitment_id = c.id
                   )
                 ORDER BY c.created_at, c.id
                """,
                (target_ref,),
            ).fetchall()
        return [row["id"] for row in rows]

    def find_commitment_by_idempotency(
        self, *, learner_id: str, created_action: str, target_set_hash: str, idempotency_key: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT c.* FROM commitments c
                  JOIN commitment_versions v
                    ON v.commitment_id = c.id AND v.version = 1
                 WHERE c.learner_id = ? AND c.created_action = ?
                   AND c.idempotency_key = ? AND v.target_set_hash = ?
                 ORDER BY c.created_at, c.id LIMIT 1
                """,
                (learner_id, created_action, idempotency_key, target_set_hash),
            ).fetchone()
        return dict(row) if row is not None else None

    def find_commitment_candidate(
        self, *, learner_id: str, created_action: str, target_set_hash: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT c.* FROM commitments c
                  JOIN commitment_versions v
                    ON v.commitment_id = c.id AND v.version = 1
                 WHERE c.learner_id = ? AND c.created_action = ?
                   AND v.target_set_hash = ?
                 ORDER BY c.created_at, c.id LIMIT 1
                """,
                (learner_id, created_action, target_set_hash),
            ).fetchone()
        return dict(row) if row is not None else None
