from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.migrate import apply_migrations
from learnloop.ids import new_ulid


def _json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _loads(value: str | None, default: Any) -> Any:
    if value is None:
        return default
    return json.loads(value)


def _queued_followup_action(action: Any) -> tuple[str, str] | None:
    if not isinstance(action, str):
        return None
    if action.startswith("negative_surprise_followup:"):
        return ("negative_surprise_followup", action.split(":", 1)[1])
    if action.startswith("intervention_followup:queued:"):
        return ("intervention_followup", action.split(":", 2)[2])
    return None


@dataclass(frozen=True)
class PracticeItemState:
    practice_item_id: str
    difficulty: float | None
    stability: float | None
    retrievability: float | None
    due_at: str | None
    active: bool
    content_hash: str | None
    last_attempt_at: str | None
    updated_at: str


@dataclass(frozen=True)
class MasteryState:
    learning_object_id: str
    logit_mean: float
    logit_variance: float
    evidence_count: int
    last_evidence_at: str | None
    algorithm_version: str
    updated_at: str


@dataclass(frozen=True)
class ActiveErrorEvent:
    id: str
    learning_object_id: str
    error_type: str
    severity: float
    is_misconception: bool
    created_at: str


@dataclass(frozen=True)
class ProbeState:
    learning_object_id: str
    status: str
    hypothesis_set_id: str | None


@dataclass(frozen=True)
class ProbeStateRecord:
    learning_object_id: str
    status: str
    probe_phase_id: str | None
    hypothesis_set_id: str | None
    probe_attempts_completed: int
    probe_attempts_target: int
    families_converged: list[str]
    entered_at: str | None
    completed_at: str | None
    algorithm_version: str
    updated_at: str


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
    created_at: str
    superseded_at: str | None


@dataclass(frozen=True)
class FacetRecallState:
    id: str
    learning_object_id: str
    facet_id: str
    practice_item_id: str | None
    recall_alpha: float
    recall_beta: float
    recall_mean: float
    recall_variance: float
    independent_evidence_mass: float
    raw_coverage_mass: float
    last_attempt_at: str | None
    last_error_at: str | None
    consecutive_failures: int
    algorithm_version: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class PracticeItemQualityState:
    practice_item_id: str
    bad_item_suspicion: float
    evidence_count: int
    suspicion_reasons: list[str]
    last_flagged_at: str | None
    algorithm_version: str
    updated_at: str


class Repository:
    def __init__(self, sqlite_path: Path):
        self.sqlite_path = sqlite_path
        apply_migrations(sqlite_path)

    def connection(self) -> sqlite3.Connection:
        return connect(self.sqlite_path)

    def practice_item_state(self, practice_item_id: str) -> PracticeItemState | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM practice_item_state WHERE practice_item_id = ?",
                (practice_item_id,),
            ).fetchone()
        return _practice_item_state(row) if row is not None else None

    def practice_item_states(self) -> dict[str, PracticeItemState]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM practice_item_state").fetchall()
        return {row["practice_item_id"]: _practice_item_state(row) for row in rows}

    def upsert_practice_item_state(
        self,
        practice_item_id: str,
        *,
        difficulty: float | None = None,
        stability: float | None = None,
        retrievability: float | None = None,
        due_at: str | None = None,
        active: bool = True,
        content_hash: str | None = None,
        last_attempt_at: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO practice_item_state(
                  practice_item_id, difficulty, stability, retrievability, due_at,
                  active, content_hash, last_attempt_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(practice_item_id) DO UPDATE SET
                  difficulty = excluded.difficulty,
                  stability = excluded.stability,
                  retrievability = excluded.retrievability,
                  due_at = excluded.due_at,
                  active = excluded.active,
                  content_hash = excluded.content_hash,
                  last_attempt_at = excluded.last_attempt_at,
                  updated_at = excluded.updated_at
                """,
                (
                    practice_item_id,
                    difficulty,
                    stability,
                    retrievability,
                    due_at,
                    1 if active else 0,
                    content_hash,
                    last_attempt_at,
                    now,
                ),
            )
            connection.commit()

    def mastery_state(self, learning_object_id: str) -> MasteryState | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM learning_object_mastery WHERE learning_object_id = ?",
                (learning_object_id,),
            ).fetchone()
        return _mastery_state(row) if row is not None else None

    def mastery_states(self) -> dict[str, MasteryState]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM learning_object_mastery").fetchall()
        return {row["learning_object_id"]: _mastery_state(row) for row in rows}

    def upsert_mastery_state(
        self,
        mastery: MasteryState,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO learning_object_mastery(
                  learning_object_id, logit_mean, logit_variance, evidence_count,
                  last_evidence_at, algorithm_version, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(learning_object_id) DO UPDATE SET
                  logit_mean = excluded.logit_mean,
                  logit_variance = excluded.logit_variance,
                  evidence_count = excluded.evidence_count,
                  last_evidence_at = excluded.last_evidence_at,
                  algorithm_version = excluded.algorithm_version,
                  updated_at = excluded.updated_at
                """,
                (
                    mastery.learning_object_id,
                    mastery.logit_mean,
                    mastery.logit_variance,
                    mastery.evidence_count,
                    mastery.last_evidence_at,
                    mastery.algorithm_version,
                    mastery.updated_at,
                ),
            )
            connection.commit()

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

    def list_recent_attempts_by_practice_item(self, practice_item_id: str, limit: int = 10) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM practice_attempts
                WHERE practice_item_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (practice_item_id, limit),
            ).fetchall()
        return [_decode_attempt(row) for row in rows]

    def list_recent_attempts_by_learning_object(self, learning_object_id: str, limit: int = 10) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM practice_attempts
                WHERE learning_object_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (learning_object_id, limit),
            ).fetchall()
        return [_decode_attempt(row) for row in rows]

    def list_attempts_by_learning_object(self, learning_object_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM practice_attempts
                WHERE learning_object_id = ?
                ORDER BY created_at ASC, id ASC
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
                )
                AND NOT EXISTS (
                  SELECT 1 FROM grading_evidence e2
                  WHERE e2.attempt_id = a.id
                    AND e2.grader_tier = 3
                    AND e2.superseded_at IS NULL
                )
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

    def record_deferred_regrade(
        self,
        *,
        attempt_id: str,
        new_evidence_rows: Iterable[Mapping[str, Any]],
        superseded_by_evidence_id: str,
        mastery_state: MasteryState,
        attempt_update: Mapping[str, Any],
        content_events: Iterable[Mapping[str, Any]] = (),
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            for row in new_evidence_rows:
                self._insert_grading_evidence(connection, attempt_id, row)
            connection.execute(
                """
                UPDATE grading_evidence
                SET superseded_at = ?, superseded_by_evidence_id = ?
                WHERE attempt_id = ? AND grader_tier = 1 AND superseded_at IS NULL
                """,
                (now, superseded_by_evidence_id, attempt_id),
            )
            connection.execute(
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
                    attempt_update["rubric_score"],
                    attempt_update["correctness"],
                    attempt_update["grader_confidence"],
                    1 if attempt_update.get("manual_review") else 0,
                    attempt_update.get("manual_review_reason"),
                    attempt_update.get("error_type"),
                    now,
                    attempt_id,
                ),
            )
            self._upsert_mastery_state_record(connection, mastery_state)
            for event in content_events:
                connection.execute(
                    """
                    INSERT INTO content_events(
                      id, change_batch_id, event_type, subject, entity_type,
                      entity_id, origin, review_status, summary, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event["id"],
                        event.get("change_batch_id"),
                        event["event_type"],
                        event.get("subject"),
                        event["entity_type"],
                        event["entity_id"],
                        event.get("origin", "codex"),
                        event.get("review_status", "accepted"),
                        event.get("summary"),
                        event["created_at"],
                    ),
                )
            connection.commit()

    def active_error_events(self) -> list[ActiveErrorEvent]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM error_events WHERE status = 'active' ORDER BY created_at DESC"
            ).fetchall()
        return [
            ActiveErrorEvent(
                id=row["id"],
                learning_object_id=row["learning_object_id"],
                error_type=row["error_type"],
                severity=row["severity"],
                is_misconception=bool(row["is_misconception"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def active_errors_by_learning_object(self, learning_object_id: str) -> list[ActiveErrorEvent]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM error_events
                WHERE status = 'active' AND learning_object_id = ?
                ORDER BY created_at DESC
                """,
                (learning_object_id,),
            ).fetchall()
        return [_active_error(row) for row in rows]

    def error_events_for_attempt(self, attempt_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM error_events
                WHERE attempt_id = ?
                ORDER BY created_at, id
                """,
                (attempt_id,),
            ).fetchall()
        return [_decode_error_event(row) for row in rows]

    def insert_error_event(self, event: Mapping[str, Any]) -> None:
        with self.connection() as connection:
            self._insert_error_event(connection, event)
            connection.commit()

    def resolve_error_event(self, event_id: str, *, clock: Clock | None = None) -> bool:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE error_events
                SET status = 'resolved', updated_at = ?
                WHERE id = ? AND status = 'active'
                """,
                (now, event_id),
            )
            connection.commit()
            return cursor.rowcount > 0

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
                SELECT a.practice_item_id AS practice_item_id,
                       a.learning_object_id AS learning_object_id,
                       a.rubric_score AS rubric_score,
                       s.predicted_score_dist_json AS predicted_score_dist_json
                FROM practice_attempts a
                JOIN attempt_surprise s ON s.attempt_id = a.id
                ORDER BY a.created_at
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def pending_followup_practice_item_ids(self) -> list[str]:
        """Return queued follow-up item ids that have not yet been attempted."""

        return [item["practice_item_id"] for item in self.pending_followup_practice_items()]

    def pending_followup_practice_items(self) -> list[dict[str, str]]:
        """Return queued follow-ups that have not yet been attempted.

        Follow-up insertion is represented in MVP as an action recorded on
        ``attempt_surprise``. The scheduler consumes those actions until a later
        attempt exists for the chosen Practice Item.
        """

        pending: list[dict[str, str]] = []
        seen: set[str] = set()
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT attempt_id, triggered_actions_json, created_at
                FROM attempt_surprise
                WHERE triggered_actions_json IS NOT NULL
                ORDER BY created_at DESC, attempt_id DESC
                """
            ).fetchall()
            for row in rows:
                for action in _loads(row["triggered_actions_json"], []):
                    parsed = _queued_followup_action(action)
                    if parsed is None:
                        continue
                    action_type, practice_item_id = parsed
                    if not practice_item_id or practice_item_id in seen:
                        continue
                    later_attempt = connection.execute(
                        """
                        SELECT 1 FROM practice_attempts
                        WHERE practice_item_id = ? AND created_at > ?
                        LIMIT 1
                        """,
                        (practice_item_id, row["created_at"]),
                    ).fetchone()
                    if later_attempt is not None:
                        continue
                    seen.add(practice_item_id)
                    pending.append({"practice_item_id": practice_item_id, "action_type": action_type})
        return pending

    def update_attempt_surprise_actions(
        self,
        attempt_id: str,
        *,
        triggered_actions: list[str] | None = None,
        suppressed_actions: list[str] | None = None,
    ) -> bool:
        assignments: list[str] = []
        parameters: list[Any] = []
        if triggered_actions is not None:
            assignments.append("triggered_actions_json = ?")
            parameters.append(_json(triggered_actions))
        if suppressed_actions is not None:
            assignments.append("suppressed_actions_json = ?")
            parameters.append(_json(suppressed_actions))
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

    def insert_observation_template(self, template: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        now = utc_now_iso(clock)
        template_id = str(template.get("id") or new_ulid())
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO observation_templates(
                  id, domain, version, title, template_yaml, emits_attempt,
                  active, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    template_id,
                    template["domain"],
                    template["version"],
                    template["title"],
                    template["template_yaml"],
                    1 if template.get("emits_attempt") else 0,
                    1 if template.get("active", True) else 0,
                    now,
                    now,
                ),
            )
            connection.commit()
        return template_id

    def observation_templates(self, *, active_only: bool = False) -> list[dict[str, Any]]:
        query = "SELECT * FROM observation_templates"
        if active_only:
            query += " WHERE active = 1"
        query += " ORDER BY created_at, id"
        with self.connection() as connection:
            rows = connection.execute(query).fetchall()
        return [_decode_observation_template(row) for row in rows]

    def fetch_observation_template(self, template_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM observation_templates WHERE id = ?",
                (template_id,),
            ).fetchone()
        return _decode_observation_template(row) if row is not None else None

    def insert_observation_event(self, event: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        now = event.get("created_at") or utc_now_iso(clock)
        event_id = str(event.get("id") or new_ulid())
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO observation_events(
                  id, template_id, subject, session_id, related_learning_object_id,
                  related_practice_item_id, binding_mode, response_json,
                  emitted_attempt_id, template_version, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    event["template_id"],
                    event.get("subject"),
                    event.get("session_id"),
                    event.get("related_learning_object_id"),
                    event.get("related_practice_item_id"),
                    event.get("binding_mode"),
                    _json(event.get("response", {})),
                    event.get("emitted_attempt_id"),
                    event["template_version"],
                    now,
                ),
            )
            connection.commit()
        return event_id

    def observation_events(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM observation_events ORDER BY created_at DESC"
            ).fetchall()
        return [_decode_observation_event(row) for row in rows]

    def insert_learner_claim(self, claim: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        claim_id = str(claim.get("id") or new_ulid())
        created_at = str(claim.get("created_at") or utc_now_iso(clock))
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO learner_claims(
                  id, claim_type, scope_type, scope_id, evidence_family,
                  claimed_level, prior_pseudo_count, source, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    claim_id,
                    claim["claim_type"],
                    claim["scope_type"],
                    claim.get("scope_id"),
                    claim.get("evidence_family"),
                    claim["claimed_level"],
                    claim["prior_pseudo_count"],
                    claim["source"],
                    created_at,
                ),
            )
            connection.commit()
        return claim_id

    def learner_claims(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM learner_claims
                ORDER BY created_at DESC, id
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def record_attempt_outcome(
        self,
        *,
        attempt: Mapping[str, Any],
        evidence_rows: Iterable[Mapping[str, Any]],
        error_events: Iterable[Mapping[str, Any]],
        surprise: Mapping[str, Any],
        practice_item_state: PracticeItemState,
        mastery_state: MasteryState,
        facet_recall_states: Iterable[Mapping[str, Any]] = (),
        quality_state: Mapping[str, Any] | None = None,
        ability_transition: Mapping[str, Any] | None = None,
        attempt_debug_payload: Mapping[str, Any] | None = None,
    ) -> None:
        with self.connection() as connection:
            self._insert_practice_attempt(connection, attempt)
            for row in evidence_rows:
                self._insert_grading_evidence(connection, attempt["id"], row)
            for event in error_events:
                self._insert_error_event(connection, event)
            self._insert_attempt_surprise(connection, surprise)
            self._upsert_practice_item_state_record(connection, practice_item_state)
            self._upsert_mastery_state_record(connection, mastery_state)
            for state in facet_recall_states:
                self._upsert_facet_recall_state(connection, state)
            if quality_state is not None:
                self._upsert_practice_item_quality_state(connection, quality_state)
            if ability_transition is not None:
                self._upsert_ability_transition_event(connection, ability_transition)
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
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            for row in new_evidence_rows:
                self._insert_grading_evidence(connection, attempt_id, row)
            connection.execute(
                """
                UPDATE grading_evidence
                SET superseded_at = ?, superseded_by_evidence_id = ?
                WHERE attempt_id = ? AND grader_tier = 1 AND superseded_at IS NULL
                """,
                (now, superseded_by_evidence_id, attempt_id),
            )
            connection.commit()

    def reset_learning_object_derived_state(self, learning_object_id: str) -> None:
        with self.connection() as connection:
            attempt_ids = [
                row["id"]
                for row in connection.execute(
                    "SELECT id FROM practice_attempts WHERE learning_object_id = ?",
                    (learning_object_id,),
                ).fetchall()
            ]
            item_ids = [
                row["practice_item_id"]
                for row in connection.execute(
                    "SELECT DISTINCT practice_item_id FROM practice_attempts WHERE learning_object_id = ?",
                    (learning_object_id,),
                ).fetchall()
            ]
            connection.execute(
                "DELETE FROM learning_object_mastery WHERE learning_object_id = ?",
                (learning_object_id,),
            )
            connection.execute(
                "DELETE FROM evidence_facet_recall_state WHERE learning_object_id = ?",
                (learning_object_id,),
            )
            if attempt_ids:
                placeholders = ",".join("?" for _ in attempt_ids)
                connection.execute(f"DELETE FROM error_events WHERE attempt_id IN ({placeholders})", attempt_ids)
                connection.execute(f"DELETE FROM attempt_surprise WHERE attempt_id IN ({placeholders})", attempt_ids)
                connection.execute(f"DELETE FROM attempt_debug_payloads WHERE attempt_id IN ({placeholders})", attempt_ids)
                connection.execute(f"DELETE FROM ability_transition_events WHERE attempt_id IN ({placeholders})", attempt_ids)
            if item_ids:
                placeholders = ",".join("?" for _ in item_ids)
                connection.execute(f"DELETE FROM practice_item_state WHERE practice_item_id IN ({placeholders})", item_ids)
                connection.execute(
                    f"DELETE FROM practice_item_quality_state WHERE practice_item_id IN ({placeholders})",
                    item_ids,
                )
            connection.commit()

    def replace_attempt_derived_outcome(
        self,
        *,
        attempt: Mapping[str, Any],
        error_events: Iterable[Mapping[str, Any]],
        surprise: Mapping[str, Any],
        practice_item_state: PracticeItemState,
        mastery_state: MasteryState,
        facet_recall_states: Iterable[Mapping[str, Any]] = (),
        quality_state: Mapping[str, Any] | None = None,
        ability_transition: Mapping[str, Any] | None = None,
        attempt_debug_payload: Mapping[str, Any] | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE practice_attempts
                SET rubric_score = ?,
                    correctness = ?,
                    confidence = ?,
                    latency_seconds = ?,
                    hints_used = ?,
                    error_type = ?,
                    grader_confidence = ?,
                    manual_review = ?,
                    manual_review_reason = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    attempt["rubric_score"],
                    attempt["correctness"],
                    attempt.get("confidence"),
                    attempt.get("latency_seconds"),
                    attempt.get("hints_used"),
                    attempt.get("error_type"),
                    attempt["grader_confidence"],
                    1 if attempt.get("manual_review") else 0,
                    attempt.get("manual_review_reason"),
                    attempt["updated_at"],
                    attempt["id"],
                ),
            )
            connection.execute("DELETE FROM error_events WHERE attempt_id = ?", (attempt["id"],))
            connection.execute("DELETE FROM attempt_surprise WHERE attempt_id = ?", (attempt["id"],))
            connection.execute("DELETE FROM attempt_debug_payloads WHERE attempt_id = ?", (attempt["id"],))
            connection.execute("DELETE FROM ability_transition_events WHERE attempt_id = ?", (attempt["id"],))
            for event in error_events:
                self._insert_error_event(connection, event)
            self._insert_attempt_surprise(connection, surprise)
            self._upsert_practice_item_state_record(connection, practice_item_state)
            self._upsert_mastery_state_record(connection, mastery_state)
            for state in facet_recall_states:
                self._upsert_facet_recall_state(connection, state)
            if quality_state is not None:
                self._upsert_practice_item_quality_state(connection, quality_state)
            if ability_transition is not None:
                self._upsert_ability_transition_event(connection, ability_transition)
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
            connection.execute("DELETE FROM learning_outcome_labels WHERE outcome_attempt_id = ?", (attempt["id"],))
            self._insert_learning_outcome_labels(
                connection,
                attempt,
                algorithm_version=surprise["algorithm_version"],
            )
            connection.commit()

    def facet_recall_state(
        self,
        learning_object_id: str,
        facet_id: str,
        practice_item_id: str | None = None,
    ) -> FacetRecallState | None:
        with self.connection() as connection:
            if practice_item_id is None:
                row = connection.execute(
                    """
                    SELECT * FROM evidence_facet_recall_state
                    WHERE learning_object_id = ? AND facet_id = ? AND practice_item_id IS NULL
                    """,
                    (learning_object_id, facet_id),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT * FROM evidence_facet_recall_state
                    WHERE learning_object_id = ? AND facet_id = ? AND practice_item_id = ?
                    """,
                    (learning_object_id, facet_id, practice_item_id),
                ).fetchone()
        return _facet_recall_state(row) if row is not None else None

    def facet_recall_states(self, learning_object_id: str | None = None) -> list[FacetRecallState]:
        with self.connection() as connection:
            if learning_object_id is None:
                rows = connection.execute(
                    "SELECT * FROM evidence_facet_recall_state ORDER BY learning_object_id, facet_id, practice_item_id"
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT * FROM evidence_facet_recall_state
                    WHERE learning_object_id = ?
                    ORDER BY facet_id, practice_item_id
                    """,
                    (learning_object_id,),
                ).fetchall()
        return [_facet_recall_state(row) for row in rows]

    def merge_facet_recall_aliases(
        self,
        alias_to_canonical: Mapping[str, str],
        *,
        algorithm_version: str,
        clock: Clock | None = None,
    ) -> int:
        merge_map = {
            str(alias): str(canonical)
            for alias, canonical in alias_to_canonical.items()
            if alias and canonical and alias != canonical
        }
        if not merge_map:
            return 0
        now = utc_now_iso(clock)
        merged_groups = 0
        with self.connection() as connection:
            for canonical in sorted(set(merge_map.values())):
                aliases = sorted(alias for alias, target in merge_map.items() if target == canonical)
                source_facets = [canonical, *aliases]
                placeholders = ",".join("?" for _ in source_facets)
                rows = connection.execute(
                    f"""
                    SELECT * FROM evidence_facet_recall_state
                    WHERE facet_id IN ({placeholders})
                    ORDER BY learning_object_id, practice_item_id, facet_id
                    """,
                    source_facets,
                ).fetchall()
                groups: dict[tuple[str, str | None], list[sqlite3.Row]] = {}
                for row in rows:
                    groups.setdefault((row["learning_object_id"], row["practice_item_id"]), []).append(row)
                for (learning_object_id, practice_item_id), group in groups.items():
                    if not any(row["facet_id"] != canonical for row in group):
                        continue
                    state = _merged_facet_recall_state(
                        group,
                        canonical_facet_id=canonical,
                        learning_object_id=learning_object_id,
                        practice_item_id=practice_item_id,
                        algorithm_version=algorithm_version,
                        updated_at=now,
                    )
                    ids = [row["id"] for row in group]
                    connection.execute(
                        f"DELETE FROM evidence_facet_recall_state WHERE id IN ({','.join('?' for _ in ids)})",
                        ids,
                    )
                    self._upsert_facet_recall_state(connection, state)
                    merged_groups += 1
            connection.commit()
        return merged_groups

    def practice_item_quality_state(self, practice_item_id: str) -> PracticeItemQualityState | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM practice_item_quality_state WHERE practice_item_id = ?",
                (practice_item_id,),
            ).fetchone()
        return _practice_item_quality_state(row) if row is not None else None

    def upsert_practice_item_quality_state(self, state: Mapping[str, Any]) -> None:
        with self.connection() as connection:
            self._upsert_practice_item_quality_state(connection, state)
            connection.commit()

    def attempt_debug_payload(self, attempt_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT payload_json FROM attempt_debug_payloads WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
        return _loads(row["payload_json"], {}) if row is not None else None

    def ability_transition_event(self, attempt_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM ability_transition_events WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
        return _decode_ability_transition_event(row) if row is not None else None

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

    def record_derived_state_rebuild(
        self,
        *,
        scope: str,
        learning_object_ids: list[str],
        algorithm_version: str,
        rebuilt_learning_objects: int,
        replayed_attempts: int,
        clock: Clock | None = None,
    ) -> str:
        rebuild_id = new_ulid()
        created_at = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO derived_state_rebuilds(
                  id, scope, learning_object_ids_json, algorithm_version,
                  rebuilt_learning_objects, replayed_attempts, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rebuild_id,
                    scope,
                    _json(learning_object_ids),
                    algorithm_version,
                    rebuilt_learning_objects,
                    replayed_attempts,
                    created_at,
                ),
            )
            connection.commit()
        return rebuild_id

    def latest_derived_state_rebuild(self) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM derived_state_rebuilds
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """
            ).fetchone()
        return _decode_derived_state_rebuild(row) if row is not None else None

    def upsert_intervention_need(self, need: Mapping[str, Any]) -> str:
        now = str(need["updated_at"])
        target_facets = sorted({str(facet) for facet in need.get("target_facets", [])})
        desired_intent = str(need["desired_intent"])
        learning_object_id = str(need["learning_object_id"])
        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT * FROM intervention_needs
                WHERE learning_object_id = ?
                  AND desired_intent = ?
                  AND target_facets_json = ?
                  AND status = 'pending'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (learning_object_id, desired_intent, _json(target_facets)),
            ).fetchone()
            if existing is not None:
                need_id = existing["id"]
                connection.execute(
                    """
                    UPDATE intervention_needs
                    SET attempt_id = ?, practice_item_id = ?, trigger_reason = ?,
                        error_types_json = ?, priority = ?, blocked_reason = ?,
                        candidate_requirements_json = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        need.get("attempt_id"),
                        need.get("practice_item_id"),
                        need["trigger_reason"],
                        _json(need.get("error_types", [])),
                        need.get("priority", 0.5),
                        need["blocked_reason"],
                        _json(need.get("candidate_requirements", {})),
                        now,
                        need_id,
                    ),
                )
            else:
                need_id = str(need.get("id") or new_ulid())
                connection.execute(
                    """
                    INSERT INTO intervention_needs(
                      id, attempt_id, learning_object_id, practice_item_id,
                      desired_intent, trigger_reason, target_facets_json,
                      error_types_json, priority, status, blocked_reason,
                      candidate_requirements_json, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        need_id,
                        need.get("attempt_id"),
                        learning_object_id,
                        need.get("practice_item_id"),
                        desired_intent,
                        need["trigger_reason"],
                        _json(target_facets),
                        _json(need.get("error_types", [])),
                        need.get("priority", 0.5),
                        need.get("status", "pending"),
                        need["blocked_reason"],
                        _json(need.get("candidate_requirements", {})),
                        need.get("created_at", now),
                        now,
                    ),
                )
            connection.commit()
        return need_id

    def pending_intervention_needs(self, learning_object_id: str | None = None) -> list[dict[str, Any]]:
        clauses = ["status = 'pending'"]
        parameters: list[Any] = []
        if learning_object_id is not None:
            clauses.append("learning_object_id = ?")
            parameters.append(learning_object_id)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM intervention_needs
                WHERE {' AND '.join(clauses)}
                ORDER BY priority DESC, created_at
                """,
                parameters,
            ).fetchall()
        return [_decode_intervention_need(row) for row in rows]

    def intervention_need_for_attempt(self, attempt_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM intervention_needs
                WHERE attempt_id = ?
                ORDER BY updated_at DESC, created_at DESC, id DESC
                LIMIT 1
                """,
                (attempt_id,),
            ).fetchone()
        return _decode_intervention_need(row) if row is not None else None

    def update_intervention_need_status(
        self,
        need_id: str,
        *,
        status: str,
        blocked_reason: str | None = None,
        clock: Clock | None = None,
    ) -> bool:
        if status not in {"pending", "fulfilled", "dismissed", "stale"}:
            raise ValueError("status must be one of pending, fulfilled, dismissed, stale")
        now = utc_now_iso(clock)
        assignments = ["status = ?", "updated_at = ?"]
        parameters: list[Any] = [status, now]
        if blocked_reason is not None:
            assignments.append("blocked_reason = ?")
            parameters.append(blocked_reason)
        parameters.append(need_id)
        with self.connection() as connection:
            cursor = connection.execute(
                f"UPDATE intervention_needs SET {', '.join(assignments)} WHERE id = ?",
                parameters,
            )
            connection.commit()
            return cursor.rowcount > 0

    def probe_states(self) -> dict[str, ProbeState]:
        with self.connection() as connection:
            rows = connection.execute("SELECT learning_object_id, status, hypothesis_set_id FROM lo_probe_state").fetchall()
        return {
            row["learning_object_id"]: ProbeState(
                learning_object_id=row["learning_object_id"],
                status=row["status"],
                hypothesis_set_id=row["hypothesis_set_id"],
            )
            for row in rows
        }

    def probe_state(self, learning_object_id: str) -> ProbeStateRecord | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM lo_probe_state WHERE learning_object_id = ?",
                (learning_object_id,),
            ).fetchone()
        return _probe_state_record(row) if row is not None else None

    def upsert_probe_state(
        self,
        *,
        learning_object_id: str,
        status: str,
        algorithm_version: str,
        probe_phase_id: str | None = None,
        hypothesis_set_id: str | None = None,
        probe_attempts_completed: int = 0,
        probe_attempts_target: int = 3,
        families_converged: list[str] | None = None,
        entered_at: str | None = None,
        completed_at: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO lo_probe_state(
                  learning_object_id, status, probe_phase_id, hypothesis_set_id,
                  probe_attempts_completed, probe_attempts_target,
                  families_converged_json, entered_at, completed_at,
                  algorithm_version, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(learning_object_id) DO UPDATE SET
                  status = excluded.status,
                  probe_phase_id = excluded.probe_phase_id,
                  hypothesis_set_id = excluded.hypothesis_set_id,
                  probe_attempts_completed = excluded.probe_attempts_completed,
                  probe_attempts_target = excluded.probe_attempts_target,
                  families_converged_json = excluded.families_converged_json,
                  entered_at = excluded.entered_at,
                  completed_at = excluded.completed_at,
                  algorithm_version = excluded.algorithm_version,
                  updated_at = excluded.updated_at
                """,
                (
                    learning_object_id,
                    status,
                    probe_phase_id,
                    hypothesis_set_id,
                    probe_attempts_completed,
                    probe_attempts_target,
                    _json(families_converged or []),
                    entered_at,
                    completed_at,
                    algorithm_version,
                    now,
                ),
            )
            connection.commit()

    def insert_hypothesis_set(
        self,
        *,
        learning_object_id: str,
        probe_phase_id: str | None,
        hypotheses: list[Mapping[str, Any]],
        prior: Mapping[str, float],
        algorithm_version: str,
        clock: Clock | None = None,
    ) -> str:
        now = utc_now_iso(clock)
        hypothesis_set_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO hypothesis_sets(
                  id, learning_object_id, probe_phase_id, hypotheses_json,
                  prior_json, algorithm_version, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    hypothesis_set_id,
                    learning_object_id,
                    probe_phase_id,
                    _json(list(hypotheses)),
                    _json(dict(prior)),
                    algorithm_version,
                    now,
                ),
            )
            connection.commit()
        return hypothesis_set_id

    def fetch_hypothesis_set(self, hypothesis_set_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM hypothesis_sets WHERE id = ?",
                (hypothesis_set_id,),
            ).fetchone()
        return _decode_hypothesis_set(row) if row is not None else None

    def upsert_state_belief(
        self,
        *,
        scope_type: str,
        scope_id: str,
        belief_key: str,
        mean: float,
        variance: float,
        evidence_count: int,
        algorithm_version: str,
        subject: str | None = None,
        last_surprise: float | None = None,
        last_evidence_at: str | None = None,
        stale_after_days: int | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Insert or update a `learner_state_beliefs` row.

        Keyed by the table's unique scope `(subject, scope_type, scope_id,
        belief_key)`. Done as an explicit select/update to avoid relying on an
        `ON CONFLICT` target over the COALESCE-based expression index.
        """

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM learner_state_beliefs
                WHERE COALESCE(subject, '') = COALESCE(?, '')
                  AND scope_type = ? AND scope_id = ? AND belief_key = ?
                """,
                (subject, scope_type, scope_id, belief_key),
            ).fetchone()
            if existing is not None:
                belief_id = existing["id"]
                connection.execute(
                    """
                    UPDATE learner_state_beliefs
                    SET mean = ?, variance = ?, evidence_count = ?, last_surprise = ?,
                        last_evidence_at = ?, stale_after_days = ?, algorithm_version = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        mean,
                        variance,
                        evidence_count,
                        last_surprise,
                        last_evidence_at,
                        stale_after_days,
                        algorithm_version,
                        now,
                        belief_id,
                    ),
                )
            else:
                belief_id = new_ulid()
                connection.execute(
                    """
                    INSERT INTO learner_state_beliefs(
                      id, subject, scope_type, scope_id, belief_key, mean, variance,
                      evidence_count, last_surprise, last_evidence_at, stale_after_days,
                      algorithm_version, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        belief_id,
                        subject,
                        scope_type,
                        scope_id,
                        belief_key,
                        mean,
                        variance,
                        evidence_count,
                        last_surprise,
                        last_evidence_at,
                        stale_after_days,
                        algorithm_version,
                        now,
                    ),
                )
            connection.commit()
        return belief_id

    def state_beliefs(
        self,
        *,
        subject: str | None = None,
        scope_type: str | None = None,
        scope_id: str | None = None,
        belief_key: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        parameters: list[Any] = []
        for column, value in (
            ("subject", subject),
            ("scope_type", scope_type),
            ("scope_id", scope_id),
            ("belief_key", belief_key),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                parameters.append(value)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM learner_state_beliefs{where} ORDER BY updated_at DESC, id",
                parameters,
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_elicitation_event(self, event: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        event_id = str(event.get("id") or new_ulid())
        now = event.get("created_at") or utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO elicitation_events(
                  id, session_id, selected_practice_item_id, target_scope_json,
                  policy, candidate_scores_json, entropy_before,
                  expected_information_gain, selected_reason, hypothesis_set_id,
                  hypothesis_set_json, trigger, fallback_outcome, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    event.get("session_id"),
                    event.get("selected_practice_item_id"),
                    _json(event.get("target_scope")) if event.get("target_scope") is not None else None,
                    event.get("policy", "probe_eig"),
                    _json(event.get("candidate_scores")) if event.get("candidate_scores") is not None else None,
                    event.get("entropy_before"),
                    event.get("expected_information_gain"),
                    event.get("selected_reason"),
                    event.get("hypothesis_set_id"),
                    _json(event.get("hypothesis_set")) if event.get("hypothesis_set") is not None else None,
                    event.get("trigger"),
                    event.get("fallback_outcome"),
                    now,
                ),
            )
            connection.commit()
        return event_id

    def elicitation_events(self, session_id: str | None = None) -> list[dict[str, Any]]:
        with self.connection() as connection:
            if session_id is None:
                rows = connection.execute(
                    "SELECT * FROM elicitation_events ORDER BY created_at DESC"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM elicitation_events WHERE session_id = ? ORDER BY created_at DESC",
                    (session_id,),
                ).fetchall()
        return [_decode_elicitation_event(row) for row in rows]

    def insert_scheduler_explanations(
        self,
        explanations: Iterable[dict[str, Any]],
        *,
        session_id: str | None,
        algorithm_version: str,
        retention_limit: int | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            for explanation in explanations:
                connection.execute(
                    """
                    INSERT INTO scheduler_explanations(
                      id, session_id, practice_item_id, selected_mode, priority,
                      components_json, readiness_factor, expected_information_gain,
                      target_scope_json, plain_english_json, algorithm_version, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_ulid(),
                        session_id,
                        explanation["practice_item_id"],
                        explanation.get("selected_mode", "review"),
                        explanation["priority"],
                        _json(explanation["components"]),
                        explanation.get("readiness_factor"),
                        explanation.get("expected_information_gain"),
                        _json(explanation.get("target_scope")) if explanation.get("target_scope") is not None else None,
                        _json(explanation.get("plain_english")) if explanation.get("plain_english") is not None else None,
                        algorithm_version,
                        now,
                    ),
                )
            if session_id is not None and retention_limit is not None and retention_limit > 0:
                connection.execute(
                    """
                    DELETE FROM scheduler_explanations
                    WHERE session_id = ?
                      AND id NOT IN (
                        SELECT id FROM scheduler_explanations
                        WHERE session_id = ?
                        ORDER BY created_at DESC, priority DESC, practice_item_id ASC, id DESC
                        LIMIT ?
                      )
                    """,
                    (session_id, session_id, retention_limit),
                )
            connection.commit()

    def record_scheduler_slate(
        self,
        explanations: Iterable[dict[str, Any]],
        *,
        session_id: str | None,
        algorithm_version: str,
        requested_limit: int | None = None,
        session_context: Mapping[str, Any] | None = None,
        config_snapshot: Mapping[str, Any] | None = None,
        selection_policy: str = "selection_reward_v1",
        clock: Clock | None = None,
    ) -> str:
        rows = list(explanations)
        now = utc_now_iso(clock)
        slate_id = new_ulid()
        returned = [
            row for row in rows if float((row.get("components") or {}).get("selected") or 0.0) > 0.0
        ]
        selected_practice_item_id = returned[0]["practice_item_id"] if returned else None
        returned_rank_by_id = {
            row["practice_item_id"]: rank
            for rank, row in enumerate(returned, start=1)
        }
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO scheduler_slates(
                  id, session_id, generated_at, requested_limit, returned_count,
                  candidate_count, chosen_practice_item_id, chosen_attempt_id,
                  selection_policy, session_context_json, config_snapshot_json,
                  algorithm_version, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, ?, ?, ?)
                """,
                (
                    slate_id,
                    session_id,
                    now,
                    requested_limit,
                    len(returned),
                    len(rows),
                    selection_policy,
                    _json(dict(session_context or {})),
                    _json(dict(config_snapshot or {})),
                    algorithm_version,
                    now,
                    now,
                ),
            )
            for rank, explanation in enumerate(rows, start=1):
                components = dict(explanation.get("components") or {})
                target_scope = explanation.get("target_scope") or {}
                reward_debug = target_scope.get("selection_reward") if isinstance(target_scope, Mapping) else None
                practice_item_id = explanation["practice_item_id"]
                returned_rank = returned_rank_by_id.get(practice_item_id)
                connection.execute(
                    """
                    INSERT INTO scheduler_slate_candidates(
                      id, slate_id, practice_item_id, learning_object_id, rank,
                      returned_rank, was_returned, chosen_attempt_id, selected_mode,
                      priority, selection_reward, predicted_correctness,
                      legacy_priority, expected_information_gain, readiness_factor,
                      components_json, reward_debug_json, target_scope_json,
                      plain_english_json, algorithm_version, created_at, chosen_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                    """,
                    (
                        new_ulid(),
                        slate_id,
                        practice_item_id,
                        _learning_object_id_from_target_scope(target_scope),
                        rank,
                        returned_rank,
                        1 if returned_rank is not None else 0,
                        explanation.get("selected_mode", "review"),
                        explanation["priority"],
                        components.get("selection_reward"),
                        components.get("predicted_correctness"),
                        components.get("legacy_priority"),
                        explanation.get("expected_information_gain"),
                        explanation.get("readiness_factor"),
                        _json(components),
                        _json(reward_debug) if reward_debug is not None else None,
                        _json(target_scope) if target_scope else None,
                        _json(explanation.get("plain_english")) if explanation.get("plain_english") is not None else None,
                        algorithm_version,
                        now,
                    ),
                )
            connection.commit()
        return slate_id

    def latest_scheduler_slate_by_session(self, session_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM scheduler_slates
                WHERE session_id = ?
                ORDER BY generated_at DESC, id DESC
                LIMIT 1
                """,
                (session_id,),
            ).fetchone()
        return _decode_scheduler_slate(row) if row is not None else None

    def scheduler_slate_candidates(self, slate_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM scheduler_slate_candidates
                WHERE slate_id = ?
                ORDER BY rank ASC, id ASC
                """,
                (slate_id,),
            ).fetchall()
        return [_decode_scheduler_slate_candidate(row) for row in rows]

    def latest_scheduler_explanation(self, practice_item_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM scheduler_explanations
                WHERE practice_item_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (practice_item_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "practice_item_id": row["practice_item_id"],
            "selected_mode": row["selected_mode"],
            "priority": row["priority"],
            "components": _loads(row["components_json"], {}),
            "readiness_factor": row["readiness_factor"],
            "expected_information_gain": row["expected_information_gain"],
            "target_scope": _loads(row["target_scope_json"], None),
            "plain_english": _loads(row["plain_english_json"], {}),
            "created_at": row["created_at"],
        }

    def latest_scheduler_explanations_by_session(self, session_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM scheduler_explanations
                WHERE session_id = ?
                ORDER BY created_at DESC, priority DESC, practice_item_id
                """,
                (session_id,),
            ).fetchall()
        return [_decode_scheduler_explanation(row) for row in rows]

    def create_session(
        self,
        *,
        energy: str | None = None,
        sleep_quality: float | None = None,
        available_minutes: int | None = None,
        notes_md_path: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        now = utc_now_iso(clock)
        session_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO sessions(
                  id, started_at, ended_at, energy, sleep_quality,
                  available_minutes, notes_md_path, updated_at
                )
                VALUES (?, ?, NULL, ?, ?, ?, ?, ?)
                """,
                (session_id, now, energy, sleep_quality, available_minutes, notes_md_path, now),
            )
            connection.commit()
        return session_id

    def fetch_session(self, session_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def most_recent_open_session(self) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM sessions
                WHERE ended_at IS NULL
                ORDER BY started_at DESC, id DESC
                LIMIT 1
                """
            ).fetchone()
        return dict(row) if row is not None else None

    def end_open_sessions_except(self, session_id: str, *, clock: Clock | None = None) -> int:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE sessions
                SET ended_at = ?, updated_at = ?
                WHERE ended_at IS NULL AND id != ?
                """,
                (now, now, session_id),
            )
            connection.commit()
            return cursor.rowcount

    def end_session(self, session_id: str, *, clock: Clock | None = None) -> dict[str, Any] | None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE sessions
                SET ended_at = COALESCE(ended_at, ?), updated_at = ?
                WHERE id = ?
                """,
                (now, now, session_id),
            )
            if cursor.rowcount == 0:
                connection.rollback()
                return None
            row = connection.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
            connection.commit()
        return dict(row) if row is not None else None

    def session_attempt_counts(self, session_id: str) -> dict[str, int] | None:
        session = self.fetch_session(session_id)
        if session is None:
            return None
        started_at = session["started_at"]
        ended_at = session["ended_at"] or utc_now_iso()
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS attempts_recorded,
                       COUNT(DISTINCT practice_item_id) AS items_reviewed
                FROM practice_attempts
                WHERE created_at >= ? AND created_at <= ?
                """,
                (started_at, ended_at),
            ).fetchone()
        return {
            "attempts_recorded": int(row["attempts_recorded"] if row is not None else 0),
            "items_reviewed": int(row["items_reviewed"] if row is not None else 0),
        }

    def update_session_checkpoint(
        self,
        session_id: str,
        *,
        current_practice_item_id: str | None = None,
        current_answer: str | None = None,
        focus_block_state: Mapping[str, Any] | None = None,
        pending_grading_proposal: Mapping[str, Any] | None = None,
        readiness: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO session_checkpoints(
                  session_id, current_practice_item_id, current_answer,
                  focus_block_state_json, pending_grading_proposal_json,
                  readiness_json, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                  current_practice_item_id = excluded.current_practice_item_id,
                  current_answer = excluded.current_answer,
                  focus_block_state_json = excluded.focus_block_state_json,
                  pending_grading_proposal_json = excluded.pending_grading_proposal_json,
                  readiness_json = excluded.readiness_json,
                  updated_at = excluded.updated_at
                """,
                (
                    session_id,
                    current_practice_item_id,
                    current_answer,
                    _json(focus_block_state) if focus_block_state is not None else None,
                    _json(pending_grading_proposal) if pending_grading_proposal is not None else None,
                    _json(readiness) if readiness is not None else None,
                    now,
                ),
            )
            connection.commit()

    def fetch_session_checkpoint(self, session_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM session_checkpoints WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["focus_block_state"] = _loads(payload.pop("focus_block_state_json"), None)
        payload["pending_grading_proposal"] = _loads(payload.pop("pending_grading_proposal_json"), None)
        payload["readiness"] = _loads(payload.pop("readiness_json"), None)
        return payload

    def clear_session_checkpoint(self, session_id: str) -> bool:
        with self.connection() as connection:
            cursor = connection.execute(
                "DELETE FROM session_checkpoints WHERE session_id = ?",
                (session_id,),
            )
            connection.commit()
            return cursor.rowcount > 0

    def insert_agent_run(self, run: Mapping[str, Any]) -> str:
        run_id = str(run.get("id") or new_ulid())
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO agent_runs(
                  id, purpose, model, provider, prompt_template, prompt_version,
                  sdk_version, codex_revision, provider_type, provider_revision,
                  input_context_hash, output_schema, started_at, completed_at,
                  status, error_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    run["purpose"],
                    run.get("model"),
                    run.get("provider", "codex"),
                    run.get("prompt_template"),
                    run.get("prompt_version"),
                    run.get("sdk_version"),
                    run.get("codex_revision"),
                    run.get("provider_type"),
                    run.get("provider_revision"),
                    run.get("input_context_hash"),
                    run.get("output_schema"),
                    run["started_at"],
                    run.get("completed_at"),
                    run.get("status", "running"),
                    run.get("error_message"),
                ),
            )
            connection.commit()
        return run_id

    def complete_agent_run(
        self,
        run_id: str,
        *,
        status: str = "completed",
        error_message: str | None = None,
        clock: Clock | None = None,
    ) -> bool:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE agent_runs
                SET completed_at = ?, status = ?, error_message = ?
                WHERE id = ?
                """,
                (now, status, error_message, run_id),
            )
            connection.commit()
            return cursor.rowcount > 0

    def completed_agent_run_by_context(self, purpose: str, input_context_hash: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM agent_runs
                WHERE purpose = ? AND input_context_hash = ? AND status = 'completed'
                ORDER BY completed_at DESC, started_at DESC
                LIMIT 1
                """,
                (purpose, input_context_hash),
            ).fetchone()
        return dict(row) if row is not None else None

    def agent_run(self, run_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM agent_runs WHERE id = ?",
                (run_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def proposal_batch_for_agent_run(self, agent_run_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM proposed_patches
                WHERE agent_run_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (agent_run_id,),
            ).fetchone()
        return _decode_proposal_batch(row) if row is not None else None

    def proposal_batch(self, patch_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM proposed_patches WHERE id = ?",
                (patch_id,),
            ).fetchone()
        return _decode_proposal_batch(row) if row is not None else None

    def persist_proposal_batch(
        self,
        batch: Mapping[str, Any],
        items: Iterable[Mapping[str, Any]],
    ) -> str:
        batch_id = str(batch.get("id") or new_ulid())
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO proposed_patches(
                  id, agent_run_id, purpose, source_refs_json, summary,
                  status_cache, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id,
                    batch["agent_run_id"],
                    batch["purpose"],
                    _json(batch.get("source_refs", [])),
                    batch.get("summary"),
                    batch.get("status_cache", "pending"),
                    batch["created_at"],
                    batch.get("updated_at", batch["created_at"]),
                ),
            )
            for item in items:
                connection.execute(
                    """
                    INSERT INTO proposed_patch_items(
                      id, proposed_patch_id, client_item_id, item_type, operation,
                      target_entity_type, target_entity_id, payload_json,
                      audit_json, edited_payload_json, decision, validation_status,
                      validation_errors_json, applied_change_batch_id,
                      decided_at, decided_by, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.get("id") or new_ulid(),
                        batch_id,
                        item["client_item_id"],
                        item["item_type"],
                        item["operation"],
                        item.get("target_entity_type"),
                        item.get("target_entity_id"),
                        _json(item["payload"]),
                        _json(item.get("audit")) if item.get("audit") is not None else None,
                        _json(item.get("edited_payload")) if item.get("edited_payload") is not None else None,
                        item.get("decision", "pending"),
                        item.get("validation_status", "valid"),
                        _json(item.get("validation_errors", [])),
                        item.get("applied_change_batch_id"),
                        item.get("decided_at"),
                        item.get("decided_by"),
                        item["created_at"],
                        item.get("updated_at", item["created_at"]),
                    ),
                )
            self._refresh_proposal_status(connection, batch_id, updated_at=batch.get("updated_at", batch["created_at"]))
            connection.commit()
        return batch_id

    def proposal_batches(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM proposed_patches ORDER BY created_at DESC"
            ).fetchall()
        return [_decode_proposal_batch(row) for row in rows]

    def proposal_items(self, patch_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM proposed_patch_items
                WHERE proposed_patch_id = ?
                ORDER BY created_at, client_item_id
                """,
                (patch_id,),
            ).fetchall()
        return [_decode_proposal_item(row) for row in rows]

    def proposal_item(self, item_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM proposed_patch_items WHERE id = ?",
                (item_id,),
            ).fetchone()
        return _decode_proposal_item(row) if row is not None else None

    def proposal_items_by_client_id(self, client_item_id: str) -> list[dict[str, Any]]:
        """All proposal items sharing a ``client_item_id`` (used to dedupe re-proposals)."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM proposed_patch_items WHERE client_item_id = ?",
                (client_item_id,),
            ).fetchall()
        return [_decode_proposal_item(row) for row in rows]

    def pending_invalid_proposal_items(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM proposed_patch_items
                WHERE decision = 'pending' AND validation_status = 'invalid'
                ORDER BY created_at, id
                """
            ).fetchall()
        return [_decode_proposal_item(row) for row in rows]

    def update_proposal_item_edited_payload(
        self,
        item_id: str,
        *,
        edited_payload: Mapping[str, Any],
        validation_status: str,
        validation_errors: list[str],
        clock: Clock | None = None,
    ) -> bool:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE proposed_patch_items
                SET edited_payload_json = ?,
                    validation_status = ?,
                    validation_errors_json = ?,
                    updated_at = ?
                WHERE id = ? AND decision = 'pending'
                """,
                (_json(edited_payload), validation_status, _json(validation_errors), now, item_id),
            )
            patch_row = connection.execute(
                "SELECT proposed_patch_id FROM proposed_patch_items WHERE id = ?",
                (item_id,),
            ).fetchone()
            if patch_row is not None:
                self._refresh_proposal_status(connection, patch_row["proposed_patch_id"], updated_at=now)
            connection.commit()
            return cursor.rowcount > 0

    def update_proposal_item_validation(
        self,
        item_id: str,
        *,
        validation_status: str,
        validation_errors: list[str],
        clock: Clock | None = None,
    ) -> bool:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE proposed_patch_items
                SET validation_status = ?,
                    validation_errors_json = ?,
                    updated_at = ?
                WHERE id = ? AND decision = 'pending'
                """,
                (validation_status, _json(validation_errors), now, item_id),
            )
            patch_row = connection.execute(
                "SELECT proposed_patch_id FROM proposed_patch_items WHERE id = ?",
                (item_id,),
            ).fetchone()
            if patch_row is not None:
                self._refresh_proposal_status(connection, patch_row["proposed_patch_id"], updated_at=now)
            connection.commit()
            return cursor.rowcount > 0

    def pending_proposal_items(self, patch_id: str, item_ids: list[str] | None = None) -> list[dict[str, Any]]:
        parameters: list[Any] = [patch_id]
        item_filter = ""
        if item_ids:
            placeholders = ",".join("?" for _ in item_ids)
            item_filter = f" AND id IN ({placeholders})"
            parameters.extend(item_ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM proposed_patch_items
                WHERE proposed_patch_id = ? AND decision = 'pending'{item_filter}
                ORDER BY created_at, client_item_id
                """,
                parameters,
            ).fetchall()
        return [_decode_proposal_item(row) for row in rows]

    def record_applied_proposal_item(
        self,
        *,
        proposal_item_id: str,
        change_batch: Mapping[str, Any],
        content_events: Iterable[Mapping[str, Any]],
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO change_batches(
                  id, proposed_patch_item_id, reason, origin, summary, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    change_batch["id"],
                    proposal_item_id,
                    change_batch.get("reason", "proposal_accept"),
                    change_batch.get("origin", "codex"),
                    change_batch.get("summary"),
                    change_batch["created_at"],
                ),
            )
            for event in content_events:
                connection.execute(
                    """
                    INSERT INTO content_events(
                      id, change_batch_id, event_type, subject, entity_type,
                      entity_id, origin, review_status, summary, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event["id"],
                        change_batch["id"],
                        event["event_type"],
                        event.get("subject"),
                        event["entity_type"],
                        event["entity_id"],
                        event.get("origin", "codex"),
                        event.get("review_status", "accepted"),
                        event.get("summary"),
                        event["created_at"],
                    ),
                )
            connection.execute(
                """
                UPDATE proposed_patch_items
                SET decision = 'accepted',
                    applied_change_batch_id = ?,
                    decided_at = ?,
                    decided_by = 'learner',
                    updated_at = ?
                WHERE id = ?
                """,
                (change_batch["id"], now, now, proposal_item_id),
            )
            patch_row = connection.execute(
                "SELECT proposed_patch_id FROM proposed_patch_items WHERE id = ?",
                (proposal_item_id,),
            ).fetchone()
            if patch_row is not None:
                self._refresh_proposal_status(connection, patch_row["proposed_patch_id"], updated_at=now)
            connection.commit()

    def record_content_events(self, events: Iterable[Mapping[str, Any]]) -> int:
        count = 0
        with self.connection() as connection:
            for event in events:
                connection.execute(
                    """
                    INSERT INTO content_events(
                      id, change_batch_id, event_type, subject, entity_type,
                      entity_id, origin, review_status, summary, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.get("id") or new_ulid(),
                        event.get("change_batch_id"),
                        event["event_type"],
                        event.get("subject"),
                        event["entity_type"],
                        event["entity_id"],
                        event.get("origin", "codex"),
                        event.get("review_status"),
                        event.get("summary"),
                        event["created_at"],
                    ),
                )
                count += 1
            connection.commit()
        return count

    def content_events_for_entity(self, entity_type: str, entity_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM content_events
                WHERE entity_type = ? AND entity_id = ?
                ORDER BY created_at DESC, id
                """,
                (entity_type, entity_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def active_source_events_for_entity(self, entity_type: str, entity_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT
                  content_events.rowid AS _rowid,
                  content_events.*,
                  proposed_patch_items.payload_json AS _proposal_payload_json,
                  proposed_patch_items.edited_payload_json AS _proposal_edited_payload_json
                FROM content_events
                LEFT JOIN change_batches ON change_batches.id = content_events.change_batch_id
                LEFT JOIN proposed_patch_items ON proposed_patch_items.id = change_batches.proposed_patch_item_id
                WHERE content_events.entity_type = ? AND content_events.entity_id = ?
                ORDER BY content_events.rowid
                """,
                (entity_type, entity_id),
            ).fetchall()
        last_grounding_rowid = 0
        for row in rows:
            if (
                row["event_type"] in {"created", "updated"}
                and row["review_status"] == "accepted"
                and _content_event_has_source_grounding(row)
            ):
                last_grounding_rowid = max(last_grounding_rowid, int(row["_rowid"]))
        active = []
        for row in rows:
            if row["event_type"] not in {"source_span_changed", "source_span_removed"}:
                continue
            if int(row["_rowid"]) <= last_grounding_rowid:
                continue
            payload = dict(row)
            payload.pop("_rowid", None)
            payload.pop("_proposal_payload_json", None)
            payload.pop("_proposal_edited_payload_json", None)
            active.append(payload)
        return active

    def reject_applied_proposal_item(
        self,
        proposal_item_id: str,
        *,
        content_event: Mapping[str, Any],
        decided_by: str = "learner",
        clock: Clock | None = None,
    ) -> bool:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            item_row = connection.execute(
                """
                SELECT proposed_patch_id FROM proposed_patch_items
                WHERE id = ? AND decision = 'accepted'
                """,
                (proposal_item_id,),
            ).fetchone()
            if item_row is None:
                return False
            connection.execute(
                """
                INSERT INTO content_events(
                  id, change_batch_id, event_type, subject, entity_type,
                  entity_id, origin, review_status, summary, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    content_event.get("id") or new_ulid(),
                    content_event.get("change_batch_id"),
                    content_event["event_type"],
                    content_event.get("subject"),
                    content_event["entity_type"],
                    content_event["entity_id"],
                    content_event.get("origin", "codex"),
                    content_event.get("review_status", "rejected"),
                    content_event.get("summary"),
                    content_event["created_at"],
                ),
            )
            connection.execute(
                """
                UPDATE proposed_patch_items
                SET decision = 'rejected',
                    decided_at = ?,
                    decided_by = ?,
                    updated_at = ?
                WHERE id = ? AND decision = 'accepted'
                """,
                (now, decided_by, now, proposal_item_id),
            )
            self._refresh_proposal_status(connection, item_row["proposed_patch_id"], updated_at=now)
            connection.commit()
        return True

    def set_proposal_item_decision(
        self,
        patch_id: str,
        decision: str,
        item_ids: list[str] | None = None,
        *,
        decided_by: str = "learner",
        clock: Clock | None = None,
    ) -> int:
        now = utc_now_iso(clock)
        parameters: list[Any] = [decision, now, decided_by, now, patch_id]
        item_filter = ""
        if item_ids:
            placeholders = ",".join("?" for _ in item_ids)
            item_filter = f" AND id IN ({placeholders})"
            parameters.extend(item_ids)
        with self.connection() as connection:
            cursor = connection.execute(
                f"""
                UPDATE proposed_patch_items
                SET decision = ?, decided_at = ?, decided_by = ?, updated_at = ?
                WHERE proposed_patch_id = ? AND decision = 'pending'{item_filter}
                """,
                parameters,
            )
            self._refresh_proposal_status(connection, patch_id, updated_at=now)
            connection.commit()
            return cursor.rowcount

    def delete_proposal_item(self, item_id: str, *, clock: Clock | None = None) -> bool:
        """Permanently remove a proposal item row, refreshing its batch status."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            row = connection.execute(
                "SELECT proposed_patch_id FROM proposed_patch_items WHERE id = ?",
                (item_id,),
            ).fetchone()
            if row is None:
                return False
            cursor = connection.execute(
                "DELETE FROM proposed_patch_items WHERE id = ?",
                (item_id,),
            )
            self._refresh_proposal_status(connection, row["proposed_patch_id"], updated_at=now)
            connection.commit()
            return cursor.rowcount > 0

    def reset_proposal_item_decision(
        self,
        patch_id: str,
        item_ids: list[str] | None = None,
        *,
        clock: Clock | None = None,
    ) -> int:
        """Reset a decided item back to ``pending`` — the inbox "undo" action.

        Scoped to the only reversible-without-side-effects case: a ``rejected`` item
        that was never applied to disk (``applied_change_batch_id IS NULL``). Accepted
        items (and rejected-after-revert items) carry a change batch and are excluded,
        so undo can never resurrect a proposal whose entity has already been written
        and would collide on re-accept.
        """

        now = utc_now_iso(clock)
        parameters: list[Any] = [now, patch_id]
        item_filter = ""
        if item_ids:
            placeholders = ",".join("?" for _ in item_ids)
            item_filter = f" AND id IN ({placeholders})"
            parameters.extend(item_ids)
        with self.connection() as connection:
            cursor = connection.execute(
                f"""
                UPDATE proposed_patch_items
                SET decision = 'pending', decided_at = NULL, decided_by = NULL, updated_at = ?
                WHERE proposed_patch_id = ?
                  AND decision = 'rejected'
                  AND applied_change_batch_id IS NULL{item_filter}
                """,
                parameters,
            )
            self._refresh_proposal_status(connection, patch_id, updated_at=now)
            connection.commit()
            return cursor.rowcount

    def find_record(self, identifier: str) -> tuple[str, dict[str, Any]] | None:
        tables: list[tuple[str, str, str, Any]] = [
            ("practice_attempt", "practice_attempts", "id", _decode_attempt),
            ("grading_evidence", "grading_evidence", "id", dict),
            ("error_event", "error_events", "id", _decode_error_event),
            ("attempt_surprise", "attempt_surprise", "attempt_id", _decode_surprise),
            ("practice_item_state", "practice_item_state", "practice_item_id", dict),
            ("learning_object_mastery", "learning_object_mastery", "learning_object_id", dict),
            ("learner_theta", "learner_theta", "id", dict),
            ("learner_claim", "learner_claims", "id", dict),
            ("lo_probe_state", "lo_probe_state", "learning_object_id", _probe_state_record),
            ("hypothesis_set", "hypothesis_sets", "id", _decode_hypothesis_set),
            ("learner_state_belief", "learner_state_beliefs", "id", dict),
            ("elicitation_event", "elicitation_events", "id", _decode_elicitation_event),
            ("proposal", "proposed_patches", "id", _decode_proposal_batch),
            ("proposal_item", "proposed_patch_items", "id", _decode_proposal_item),
            ("change_batch", "change_batches", "id", dict),
            ("content_event", "content_events", "id", dict),
            ("scheduler_explanation", "scheduler_explanations", "id", _decode_scheduler_explanation),
            ("scheduler_slate", "scheduler_slates", "id", _decode_scheduler_slate),
            ("scheduler_slate_candidate", "scheduler_slate_candidates", "id", _decode_scheduler_slate_candidate),
            ("learning_outcome_label", "learning_outcome_labels", "id", _decode_learning_outcome_label),
            ("session", "sessions", "id", dict),
            ("session_checkpoint", "session_checkpoints", "session_id", dict),
            ("observation_template", "observation_templates", "id", _decode_observation_template),
            ("observation_event", "observation_events", "id", _decode_observation_event),
            ("agent_run", "agent_runs", "id", dict),
        ]
        with self.connection() as connection:
            for label, table, column, decoder in tables:
                row = connection.execute(f"SELECT * FROM {table} WHERE {column} = ? LIMIT 1", (identifier,)).fetchone()
                if row is not None:
                    return label, decoder(row)
        return None

    def _refresh_proposal_status(self, connection: sqlite3.Connection, patch_id: str, *, updated_at: str) -> None:
        rows = connection.execute(
            """
            SELECT decision, validation_status, COUNT(*) AS count
            FROM proposed_patch_items
            WHERE proposed_patch_id = ?
            GROUP BY decision, validation_status
            """,
            (patch_id,),
        ).fetchall()
        if not rows:
            return
        total = sum(row["count"] for row in rows)
        accepted = sum(row["count"] for row in rows if row["decision"] == "accepted")
        rejected = sum(row["count"] for row in rows if row["decision"] == "rejected")
        pending = sum(row["count"] for row in rows if row["decision"] == "pending")
        invalid = sum(row["count"] for row in rows if row["validation_status"] == "invalid")
        if invalid == total:
            status = "invalid"
        elif accepted == total:
            status = "accepted"
        elif rejected == total:
            status = "rejected"
        elif accepted > 0 or rejected > 0:
            status = "partially_accepted"
        elif pending == total:
            status = "pending"
        else:
            status = "pending"
        connection.execute(
            "UPDATE proposed_patches SET status_cache = ?, updated_at = ? WHERE id = ?",
            (status, updated_at, patch_id),
        )

    def _insert_practice_attempt(self, connection: sqlite3.Connection, attempt: Mapping[str, Any]) -> None:
        connection.execute(
            """
            INSERT INTO practice_attempts(
              id, practice_item_id, learning_object_id, subject, concept, practice_mode,
              attempt_type, learner_answer_md, evidence_facets_json, evidence_weights_json,
              rubric_score, correctness, confidence, latency_seconds, hints_used,
              error_type, grader_confidence, manual_review, manual_review_reason,
              created_at, updated_at, session_id, scheduler_slate_id, scheduler_candidate_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attempt["id"],
                attempt["practice_item_id"],
                attempt["learning_object_id"],
                attempt.get("subject"),
                attempt.get("concept"),
                attempt["practice_mode"],
                attempt["attempt_type"],
                attempt.get("learner_answer_md"),
                _json(attempt.get("evidence_facets", [])),
                _json(attempt.get("evidence_weights", {})),
                attempt.get("rubric_score"),
                attempt.get("correctness"),
                attempt.get("confidence"),
                attempt.get("latency_seconds"),
                attempt.get("hints_used", 0),
                attempt.get("error_type"),
                attempt.get("grader_confidence"),
                1 if attempt.get("manual_review") else 0,
                attempt.get("manual_review_reason"),
                attempt["created_at"],
                attempt.get("updated_at"),
                attempt.get("session_id"),
                attempt.get("scheduler_slate_id"),
                attempt.get("scheduler_candidate_id"),
            ),
        )

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
              superseded_at, superseded_by_evidence_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            ),
        )

    def _insert_error_event(self, connection: sqlite3.Connection, event: Mapping[str, Any]) -> None:
        connection.execute(
            """
            INSERT INTO error_events(
              id, attempt_id, learning_object_id, error_type, severity,
              is_misconception, repair_plan_json, status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.get("id") or new_ulid(),
                event.get("attempt_id"),
                event["learning_object_id"],
                event["error_type"],
                event["severity"],
                1 if event.get("is_misconception") else 0,
                _json(event.get("repair_plan")) if event.get("repair_plan") is not None else None,
                event.get("status", "active"),
                event["created_at"],
                event.get("updated_at"),
            ),
        )

    def _insert_attempt_surprise(self, connection: sqlite3.Connection, surprise: Mapping[str, Any]) -> None:
        connection.execute(
            """
            INSERT INTO attempt_surprise(
              attempt_id, predicted_score_dist_json, predicted_error_type_dist_json,
              observed_joint_bucket_json, predictive_surprise, bayesian_surprise,
              surprise_direction, fsrs_interval_factor, posterior_delta_json,
              triggered_actions_json, suppressed_actions_json, algorithm_version, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                surprise["algorithm_version"],
                surprise["created_at"],
            ),
        )

    def _upsert_practice_item_state_record(
        self,
        connection: sqlite3.Connection,
        state: PracticeItemState,
    ) -> None:
        connection.execute(
            """
            INSERT INTO practice_item_state(
              practice_item_id, difficulty, stability, retrievability, due_at,
              active, content_hash, last_attempt_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(practice_item_id) DO UPDATE SET
              difficulty = excluded.difficulty,
              stability = excluded.stability,
              retrievability = excluded.retrievability,
              due_at = excluded.due_at,
              active = excluded.active,
              content_hash = excluded.content_hash,
              last_attempt_at = excluded.last_attempt_at,
              updated_at = excluded.updated_at
            """,
            (
                state.practice_item_id,
                state.difficulty,
                state.stability,
                state.retrievability,
                state.due_at,
                1 if state.active else 0,
                state.content_hash,
                state.last_attempt_at,
                state.updated_at,
            ),
        )

    def _upsert_mastery_state_record(
        self,
        connection: sqlite3.Connection,
        mastery: MasteryState,
    ) -> None:
        connection.execute(
            """
            INSERT INTO learning_object_mastery(
              learning_object_id, logit_mean, logit_variance, evidence_count,
              last_evidence_at, algorithm_version, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(learning_object_id) DO UPDATE SET
              logit_mean = excluded.logit_mean,
              logit_variance = excluded.logit_variance,
              evidence_count = excluded.evidence_count,
              last_evidence_at = excluded.last_evidence_at,
              algorithm_version = excluded.algorithm_version,
              updated_at = excluded.updated_at
            """,
            (
                mastery.learning_object_id,
                mastery.logit_mean,
                mastery.logit_variance,
                mastery.evidence_count,
                mastery.last_evidence_at,
                mastery.algorithm_version,
                mastery.updated_at,
            ),
        )

    def _upsert_facet_recall_state(self, connection: sqlite3.Connection, state: Mapping[str, Any]) -> None:
        existing = connection.execute(
            """
            SELECT id FROM evidence_facet_recall_state
            WHERE learning_object_id = ?
              AND facet_id = ?
              AND (
                (practice_item_id IS NULL AND ? IS NULL)
                OR practice_item_id = ?
              )
            """,
            (
                state["learning_object_id"],
                state["facet_id"],
                state.get("practice_item_id"),
                state.get("practice_item_id"),
            ),
        ).fetchone()
        state_id = str(state.get("id") or (existing["id"] if existing is not None else new_ulid()))
        if existing is not None:
            connection.execute(
                """
                UPDATE evidence_facet_recall_state
                SET recall_alpha = ?, recall_beta = ?, recall_mean = ?,
                    recall_variance = ?, independent_evidence_mass = ?,
                    raw_coverage_mass = ?, last_attempt_at = ?,
                    last_error_at = ?, consecutive_failures = ?,
                    algorithm_version = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    state["recall_alpha"],
                    state["recall_beta"],
                    state["recall_mean"],
                    state["recall_variance"],
                    state["independent_evidence_mass"],
                    state["raw_coverage_mass"],
                    state.get("last_attempt_at"),
                    state.get("last_error_at"),
                    state.get("consecutive_failures", 0),
                    state["algorithm_version"],
                    state["updated_at"],
                    state_id,
                ),
            )
            return
        connection.execute(
            """
            INSERT INTO evidence_facet_recall_state(
              id, learning_object_id, facet_id, practice_item_id, recall_alpha,
              recall_beta, recall_mean, recall_variance, independent_evidence_mass,
              raw_coverage_mass, last_attempt_at, last_error_at,
              consecutive_failures, algorithm_version, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                state_id,
                state["learning_object_id"],
                state["facet_id"],
                state.get("practice_item_id"),
                state["recall_alpha"],
                state["recall_beta"],
                state["recall_mean"],
                state["recall_variance"],
                state["independent_evidence_mass"],
                state["raw_coverage_mass"],
                state.get("last_attempt_at"),
                state.get("last_error_at"),
                state.get("consecutive_failures", 0),
                state["algorithm_version"],
                state.get("created_at", state["updated_at"]),
                state["updated_at"],
            ),
        )

    def _upsert_practice_item_quality_state(self, connection: sqlite3.Connection, state: Mapping[str, Any]) -> None:
        connection.execute(
            """
            INSERT INTO practice_item_quality_state(
              practice_item_id, bad_item_suspicion, evidence_count,
              suspicion_reasons_json, last_flagged_at, algorithm_version, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(practice_item_id) DO UPDATE SET
              bad_item_suspicion = excluded.bad_item_suspicion,
              evidence_count = excluded.evidence_count,
              suspicion_reasons_json = excluded.suspicion_reasons_json,
              last_flagged_at = excluded.last_flagged_at,
              algorithm_version = excluded.algorithm_version,
              updated_at = excluded.updated_at
            """,
            (
                state["practice_item_id"],
                state["bad_item_suspicion"],
                state["evidence_count"],
                _json(state.get("suspicion_reasons", [])),
                state.get("last_flagged_at"),
                state["algorithm_version"],
                state["updated_at"],
            ),
        )

    def _upsert_ability_transition_event(self, connection: sqlite3.Connection, event: Mapping[str, Any]) -> None:
        connection.execute(
            """
            INSERT INTO ability_transition_events(
              attempt_id, learning_object_id, practice_item_id, transition_type,
              expected_skill_gain, target_facets_json, reason,
              applied_to_belief_counts, applied_to_mastery, applied_to_facet_recall,
              process_noise, algorithm_version, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(attempt_id) DO UPDATE SET
              learning_object_id = excluded.learning_object_id,
              practice_item_id = excluded.practice_item_id,
              transition_type = excluded.transition_type,
              expected_skill_gain = excluded.expected_skill_gain,
              target_facets_json = excluded.target_facets_json,
              reason = excluded.reason,
              applied_to_belief_counts = excluded.applied_to_belief_counts,
              applied_to_mastery = excluded.applied_to_mastery,
              applied_to_facet_recall = excluded.applied_to_facet_recall,
              process_noise = excluded.process_noise,
              algorithm_version = excluded.algorithm_version,
              created_at = excluded.created_at
            """,
            (
                event["attempt_id"],
                event["learning_object_id"],
                event["practice_item_id"],
                event["transition_type"],
                event["expected_skill_gain"],
                _json(event.get("target_facets", [])),
                event["reason"],
                1 if event.get("applied_to_belief_counts") else 0,
                1 if event.get("applied_to_mastery") else 0,
                1 if event.get("applied_to_facet_recall") else 0,
                event.get("process_noise"),
                event["algorithm_version"],
                event["created_at"],
            ),
        )

    def _link_attempt_to_scheduler_candidate(
        self,
        connection: sqlite3.Connection,
        attempt: Mapping[str, Any],
    ) -> None:
        session_id = attempt.get("session_id")
        if not session_id:
            return
        row = connection.execute(
            """
            SELECT c.id AS candidate_id, c.slate_id AS slate_id
            FROM scheduler_slate_candidates c
            JOIN scheduler_slates s ON s.id = c.slate_id
            WHERE s.session_id = ?
              AND c.practice_item_id = ?
              AND s.generated_at <= ?
              AND (c.chosen_attempt_id IS NULL OR c.chosen_attempt_id = ?)
            ORDER BY s.generated_at DESC,
                     c.was_returned DESC,
                     COALESCE(c.returned_rank, 1000000) ASC,
                     c.rank ASC,
                     c.id DESC
            LIMIT 1
            """,
            (
                session_id,
                attempt["practice_item_id"],
                attempt["created_at"],
                attempt["id"],
            ),
        ).fetchone()
        if row is None:
            return
        connection.execute(
            """
            UPDATE practice_attempts
            SET scheduler_slate_id = ?, scheduler_candidate_id = ?
            WHERE id = ?
            """,
            (row["slate_id"], row["candidate_id"], attempt["id"]),
        )
        connection.execute(
            """
            UPDATE scheduler_slate_candidates
            SET chosen_attempt_id = COALESCE(chosen_attempt_id, ?),
                chosen_at = COALESCE(chosen_at, ?)
            WHERE id = ?
            """,
            (attempt["id"], attempt["created_at"], row["candidate_id"]),
        )
        connection.execute(
            """
            UPDATE scheduler_slates
            SET chosen_practice_item_id = COALESCE(chosen_practice_item_id, ?),
                chosen_attempt_id = COALESCE(chosen_attempt_id, ?),
                updated_at = ?
            WHERE id = ?
            """,
            (attempt["practice_item_id"], attempt["id"], attempt["created_at"], row["slate_id"]),
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
            SELECT * FROM practice_attempts
            WHERE learning_object_id = ?
              AND id != ?
              AND created_at <= ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (
                current["learning_object_id"],
                current["id"],
                current["created_at"],
                max_sources,
            ),
        ).fetchall()
        for source in sources:
            same_item = source["practice_item_id"] == current["practice_item_id"]
            label_type = "same_item_retention" if same_item else "same_learning_object_transfer"
            elapsed_seconds = _elapsed_seconds_between(source["created_at"], current["created_at"])
            intervening = connection.execute(
                """
                SELECT COUNT(*) AS n
                FROM practice_attempts
                WHERE learning_object_id = ?
                  AND id NOT IN (?, ?)
                  AND created_at > ?
                  AND created_at < ?
                """,
                (
                    current["learning_object_id"],
                    source["id"],
                    current["id"],
                    source["created_at"],
                    current["created_at"],
                ),
            ).fetchone()
            metadata = {
                "source": _attempt_label_snapshot(source),
                "outcome": _attempt_label_snapshot(current),
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
                    new_ulid(),
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
                    int(intervening["n"] if intervening is not None else 0),
                    _json(metadata),
                    algorithm_version,
                    current["created_at"],
                ),
            )


def _practice_item_state(row: sqlite3.Row) -> PracticeItemState:
    return PracticeItemState(
        practice_item_id=row["practice_item_id"],
        difficulty=row["difficulty"],
        stability=row["stability"],
        retrievability=row["retrievability"],
        due_at=row["due_at"],
        active=bool(row["active"]),
        content_hash=row["content_hash"],
        last_attempt_at=row["last_attempt_at"],
        updated_at=row["updated_at"],
    )


def _mastery_state(row: sqlite3.Row) -> MasteryState:
    return MasteryState(
        learning_object_id=row["learning_object_id"],
        logit_mean=row["logit_mean"],
        logit_variance=row["logit_variance"],
        evidence_count=row["evidence_count"],
        last_evidence_at=row["last_evidence_at"],
        algorithm_version=row["algorithm_version"],
        updated_at=row["updated_at"],
    )


def _facet_recall_state(row: sqlite3.Row) -> FacetRecallState:
    return FacetRecallState(
        id=row["id"],
        learning_object_id=row["learning_object_id"],
        facet_id=row["facet_id"],
        practice_item_id=row["practice_item_id"],
        recall_alpha=row["recall_alpha"],
        recall_beta=row["recall_beta"],
        recall_mean=row["recall_mean"],
        recall_variance=row["recall_variance"],
        independent_evidence_mass=row["independent_evidence_mass"],
        raw_coverage_mass=row["raw_coverage_mass"],
        last_attempt_at=row["last_attempt_at"],
        last_error_at=row["last_error_at"],
        consecutive_failures=row["consecutive_failures"],
        algorithm_version=row["algorithm_version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _merged_facet_recall_state(
    rows: list[sqlite3.Row],
    *,
    canonical_facet_id: str,
    learning_object_id: str,
    practice_item_id: str | None,
    algorithm_version: str,
    updated_at: str,
) -> dict[str, Any]:
    alpha = sum(float(row["recall_alpha"]) for row in rows)
    beta = sum(float(row["recall_beta"]) for row in rows)
    total = alpha + beta
    mean = alpha / total if total > 0 else 0.5
    variance = alpha * beta / (total**2 * (total + 1.0)) if total > 0 else 0.0
    canonical = next((row for row in rows if row["facet_id"] == canonical_facet_id), rows[0])
    last_attempts = [row["last_attempt_at"] for row in rows if row["last_attempt_at"]]
    last_errors = [row["last_error_at"] for row in rows if row["last_error_at"]]
    created_values = [row["created_at"] for row in rows if row["created_at"]]
    return {
        "id": canonical["id"],
        "learning_object_id": learning_object_id,
        "facet_id": canonical_facet_id,
        "practice_item_id": practice_item_id,
        "recall_alpha": alpha,
        "recall_beta": beta,
        "recall_mean": mean,
        "recall_variance": variance,
        "independent_evidence_mass": sum(float(row["independent_evidence_mass"]) for row in rows),
        "raw_coverage_mass": sum(float(row["raw_coverage_mass"]) for row in rows),
        "last_attempt_at": max(last_attempts) if last_attempts else None,
        "last_error_at": max(last_errors) if last_errors else None,
        "consecutive_failures": max(int(row["consecutive_failures"]) for row in rows),
        "algorithm_version": algorithm_version,
        "created_at": min(created_values) if created_values else updated_at,
        "updated_at": updated_at,
    }


def _practice_item_quality_state(row: sqlite3.Row) -> PracticeItemQualityState:
    return PracticeItemQualityState(
        practice_item_id=row["practice_item_id"],
        bad_item_suspicion=row["bad_item_suspicion"],
        evidence_count=row["evidence_count"],
        suspicion_reasons=_loads(row["suspicion_reasons_json"], []),
        last_flagged_at=row["last_flagged_at"],
        algorithm_version=row["algorithm_version"],
        updated_at=row["updated_at"],
    )


def _decode_ability_transition_event(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["target_facets"] = _loads(payload.pop("target_facets_json"), [])
    payload["applied_to_belief_counts"] = bool(payload["applied_to_belief_counts"])
    payload["applied_to_mastery"] = bool(payload["applied_to_mastery"])
    payload["applied_to_facet_recall"] = bool(payload["applied_to_facet_recall"])
    return payload


def _decode_learning_outcome_label(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["metadata"] = _loads(payload.pop("metadata_json"), {})
    return payload


def _decode_derived_state_rebuild(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["learning_object_ids"] = _loads(payload.pop("learning_object_ids_json"), [])
    return payload


def _probe_state_record(row: sqlite3.Row) -> ProbeStateRecord:
    return ProbeStateRecord(
        learning_object_id=row["learning_object_id"],
        status=row["status"],
        probe_phase_id=row["probe_phase_id"],
        hypothesis_set_id=row["hypothesis_set_id"],
        probe_attempts_completed=row["probe_attempts_completed"],
        probe_attempts_target=row["probe_attempts_target"],
        families_converged=_loads(row["families_converged_json"], []),
        entered_at=row["entered_at"],
        completed_at=row["completed_at"],
        algorithm_version=row["algorithm_version"],
        updated_at=row["updated_at"],
    )


def _decode_observation_template(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["emits_attempt"] = bool(payload["emits_attempt"])
    payload["active"] = bool(payload["active"])
    return payload


def _decode_observation_event(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["response"] = _loads(payload.pop("response_json"), {})
    return payload


def _decode_elicitation_event(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["target_scope"] = _loads(payload.pop("target_scope_json"), None)
    payload["candidate_scores"] = _loads(payload.pop("candidate_scores_json"), None)
    payload["hypothesis_set"] = _loads(payload.pop("hypothesis_set_json"), None)
    return payload


def _decode_hypothesis_set(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["hypotheses"] = _loads(payload.pop("hypotheses_json"), [])
    payload["prior"] = _loads(payload.pop("prior_json"), {})
    return payload


def _decode_intervention_need(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["target_facets"] = _loads(payload.pop("target_facets_json"), [])
    payload["error_types"] = _loads(payload.pop("error_types_json"), [])
    payload["candidate_requirements"] = _loads(payload.pop("candidate_requirements_json"), {})
    return payload


def _active_error(row: sqlite3.Row) -> ActiveErrorEvent:
    return ActiveErrorEvent(
        id=row["id"],
        learning_object_id=row["learning_object_id"],
        error_type=row["error_type"],
        severity=row["severity"],
        is_misconception=bool(row["is_misconception"]),
        created_at=row["created_at"],
    )


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
        created_at=row["created_at"],
        superseded_at=row["superseded_at"],
    )


def _decode_attempt(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["evidence_facets"] = _loads(payload.pop("evidence_facets_json"), [])
    payload["evidence_weights"] = _loads(payload.pop("evidence_weights_json"), {})
    payload["manual_review"] = bool(payload["manual_review"])
    return payload


def _decode_attempt_feedback_metadata(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["fatal_errors"] = _loads(payload.pop("fatal_errors_json"), [])
    payload["repair_suggestions"] = _loads(payload.pop("repair_suggestions_json"), [])
    return payload


def _decode_error_event(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["is_misconception"] = bool(payload["is_misconception"])
    payload["repair_plan"] = _loads(payload.pop("repair_plan_json"), None)
    return payload


def _decode_surprise(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["predicted_score_dist"] = _loads(payload.pop("predicted_score_dist_json"), None)
    payload["predicted_error_type_dist"] = _loads(payload.pop("predicted_error_type_dist_json"), None)
    payload["observed_joint_bucket"] = _loads(payload.pop("observed_joint_bucket_json"), {})
    payload["posterior_delta"] = _loads(payload.pop("posterior_delta_json"), None)
    payload["triggered_actions"] = _loads(payload.pop("triggered_actions_json"), [])
    payload["suppressed_actions"] = _loads(payload.pop("suppressed_actions_json"), [])
    return payload


def _decode_scheduler_explanation(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["components"] = _loads(payload.pop("components_json"), {})
    payload["target_scope"] = _loads(payload.pop("target_scope_json"), None)
    payload["plain_english"] = _loads(payload.pop("plain_english_json"), None)
    return payload


def _decode_scheduler_slate(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["session_context"] = _loads(payload.pop("session_context_json"), {})
    payload["config_snapshot"] = _loads(payload.pop("config_snapshot_json"), {})
    return payload


def _decode_scheduler_slate_candidate(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["was_returned"] = bool(payload["was_returned"])
    payload["components"] = _loads(payload.pop("components_json"), {})
    payload["reward_debug"] = _loads(payload.pop("reward_debug_json"), None)
    payload["target_scope"] = _loads(payload.pop("target_scope_json"), None)
    payload["plain_english"] = _loads(payload.pop("plain_english_json"), None)
    return payload


def _learning_object_id_from_target_scope(target_scope: Any) -> str | None:
    if not isinstance(target_scope, Mapping):
        return None
    value = target_scope.get("learning_object_id")
    return str(value) if value is not None else None


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
        "latency_seconds": row["latency_seconds"],
        "created_at": row["created_at"],
    }


def _decode_proposal_batch(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["source_refs"] = _loads(payload.pop("source_refs_json"), [])
    return payload


def _decode_proposal_item(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["payload"] = _loads(payload.pop("payload_json"), {})
    payload["audit"] = _loads(payload.pop("audit_json", None), None)
    payload["edited_payload"] = _loads(payload.pop("edited_payload_json"), None)
    payload["validation_errors"] = _loads(payload.pop("validation_errors_json"), [])
    return payload


def _content_event_has_source_grounding(row: sqlite3.Row) -> bool:
    payload = _loads(row["_proposal_edited_payload_json"], None)
    if payload is None:
        payload = _loads(row["_proposal_payload_json"], {})
    provenance = payload.get("provenance") if isinstance(payload, dict) else None
    if not isinstance(provenance, dict):
        return False
    source_refs = provenance.get("source_refs")
    return isinstance(source_refs, list) and bool(source_refs)
