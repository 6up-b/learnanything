from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, date, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.migrate import apply_migrations
from learnloop.ids import new_ulid
from learnloop.ingest.ir import (
    DocumentAsset,
    DocumentBlock,
    DocumentIR,
    DocumentUnit,
)
from learnloop.ingest.locators import detect_locator_scheme
from learnloop.numeric import beta_mean, beta_quantile


_UNSET: Any = object()  # sentinel: "argument not supplied" vs an explicit None


def _json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _loads(value: str | None, default: Any) -> Any:
    if value is None:
        return default
    return json.loads(value)


def _insert_probe_presentation_row(
    connection: sqlite3.Connection,
    *,
    presentation_id: str,
    now: str,
    values: Mapping[str, Any],
) -> None:
    """Insert one frozen diagnostic assignment using the caller's transaction."""

    connection.execute(
        """
        INSERT INTO probe_presentations(
          id, probe_episode_id, practice_item_id, scheduler_candidate_id,
          state_segment_id, probe_family_template_id, probe_family_template_version,
          instrument_card_id, instrument_card_version, instrument_card_snapshot_json,
          target_hypothesis_pairs_json, target_facets_json, posterior_at_selection_json,
          entropy_at_selection, expected_information_gain, selection_policy_version,
          selection_components_json,
          status, end_reason, served_at, submitted_at, expires_at, ended_at,
          created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'selected',
                NULL, NULL, NULL, ?, NULL, ?, ?)
        """,
        (
            presentation_id,
            values["probe_episode_id"],
            values["practice_item_id"],
            values.get("scheduler_candidate_id"),
            values["state_segment_id"],
            values.get("probe_family_template_id"),
            values.get("probe_family_template_version"),
            values.get("instrument_card_id"),
            values.get("instrument_card_version"),
            _json(dict(values["instrument_card_snapshot"]))
            if values.get("instrument_card_snapshot") is not None
            else None,
            _json(list(values.get("target_hypothesis_pairs") or [])),
            _json(list(values.get("target_facets") or [])),
            _json(dict(values.get("posterior_at_selection") or {})),
            values.get("entropy_at_selection"),
            values.get("expected_information_gain"),
            values.get("selection_policy_version"),
            _json(dict(values["selection_components"]))
            if values.get("selection_components") is not None
            else None,
            values.get("expires_at"),
            now,
            now,
        ),
    )


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
class ItemParameterState:
    """Per-item empirical-Bayes difficulty posterior (b in the 2PL link)."""

    practice_item_id: str
    b_mean: float
    b_var: float
    evidence_count: int
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
    misconception_id: str | None = None
    misconception_statement: str | None = None


@dataclass(frozen=True)
class MisconceptionRecord:
    """A normalized, content-bearing belief scoped to a learning object.

    ``severity`` is the max over source events (decayed by consumers, not here);
    ``source_error_event_ids`` is append-only provenance. See spec §1.1.
    """

    id: str
    learning_object_id: str
    concept_id: str | None
    statement: str
    signature: str | None
    facet_ids: list[str]
    severity: float
    status: str
    source_error_event_ids: list[str]
    created_at: str | None
    updated_at: str | None
    resolved_at: str | None


@dataclass(frozen=True)
class ItemMisconceptionDiscrimination:
    """Estimated discrimination of an item's keyed fatal error vs a misconception.

    Beta posteriors over sensitivity = P(fatal fires | learner holds belief) and
    specificity = P(no fire | clean learner). Consumers read the lower bounds
    (``sensitivity_lb`` / ``specificity_lb``) so thin-evidence rows self-limit.
    See spec §1.3.
    """

    practice_item_id: str
    misconception_id: str
    sensitivity_alpha: float
    sensitivity_beta: float
    specificity_alpha: float
    specificity_beta: float
    n_planted_trials: int
    n_clean_trials: int
    source: str | None
    updated_at: str | None

    @property
    def sensitivity_mean(self) -> float:
        return beta_mean(self.sensitivity_alpha, self.sensitivity_beta)

    @property
    def specificity_mean(self) -> float:
        return beta_mean(self.specificity_alpha, self.specificity_beta)

    def sensitivity_lb(self, q: float = 0.25) -> float:
        return beta_quantile(q, self.sensitivity_alpha, self.sensitivity_beta)

    def specificity_lb(self, q: float = 0.25) -> float:
        return beta_quantile(q, self.specificity_alpha, self.specificity_beta)

    @property
    def youden_j(self) -> float:
        """Discrimination power J = E[sens] + E[spec] - 1."""
        return self.sensitivity_mean + self.specificity_mean - 1.0

    def youden_j_lb(self, q: float = 0.25) -> float:
        """Conservative J from the sensitivity/specificity lower bounds."""
        return self.sensitivity_lb(q) + self.specificity_lb(q) - 1.0


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
class ProbeEpisodeRecord:
    """One first-class diagnostic episode (probe redesign spec §5.1)."""

    id: str
    learning_object_id: str
    status: str
    trigger: str
    hypothesis_set_id: str | None
    active_state_segment_id: str | None
    target_decision: dict[str, Any] | None
    required_facets: list[str]
    minimum_independent_observations: int
    maximum_observations: int
    entered_at: str | None
    completed_at: str | None
    completion_reason: str | None
    algorithm_version: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ProbePresentationRecord:
    """A durable committed probe assignment (probe redesign spec §5.1)."""

    id: str
    probe_episode_id: str
    practice_item_id: str
    scheduler_candidate_id: str | None
    state_segment_id: str
    probe_family_template_id: str | None
    probe_family_template_version: int | None
    instrument_card_id: str | None
    instrument_card_version: int | None
    instrument_card_snapshot: dict[str, Any] | None
    target_hypothesis_pairs: list[list[str]]
    target_facets: list[str]
    posterior_at_selection: dict[str, float]
    entropy_at_selection: float | None
    expected_information_gain: float | None
    selection_policy_version: str | None
    selection_components: dict[str, Any]
    status: str
    end_reason: str | None
    served_at: str | None
    submitted_at: str | None
    expires_at: str | None
    ended_at: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ProbeObservationRecord:
    """The grading result + posterior transition for one consumed presentation (§5.1)."""

    id: str
    attempt_id: str
    posterior_before: dict[str, float]
    posterior_after: dict[str, float]
    entropy_before: float
    entropy_after: float
    realized_information_gain: float
    independent_evidence_discount: float | None
    contamination: dict[str, Any] | None
    grader_channel: dict[str, Any] | None
    updates_belief: bool
    eligible_for_completion: bool
    created_at: str
    # Logged-only observation features (§7.1) and the long-form structured
    # trace (§8.2). Never read by posterior replay.
    features: dict[str, Any] | None = None


@dataclass(frozen=True)
class ProbeStateSegmentRecord:
    """A learner-state segment boundary event (probe redesign spec §5.1)."""

    id: str
    learning_object_id: str
    probe_episode_id: str | None
    sequence: int
    reason: str
    opened_by_attempt_id: str | None
    created_at: str


@dataclass(frozen=True)
class ProbeFamilyTemplateRecord:
    id: str
    version: int
    status: str
    template: dict[str, Any]
    schema_hash: str
    created_at: str
    retired_at: str | None


@dataclass(frozen=True)
class ProbeInstrumentCardRecord:
    id: str
    version: int
    probe_family_template_id: str
    probe_family_template_version: int
    learning_object_id: str
    hypothesis_scope: list[str]
    card: dict[str, Any]
    compiled_likelihood_hash: str
    created_at: str
    retired_at: str | None


@dataclass(frozen=True)
class ProbeItemFamilyLinkRecord:
    practice_item_id: str
    instrument_card_id: str
    instrument_card_version: int
    generator_id: str | None
    generator_version: str | None
    generation_seed: str | None
    instance_metadata: dict[str, Any] | None
    created_at: str


@dataclass(frozen=True)
class ProbeGenerationNeedRecord:
    id: str
    probe_episode_id: str
    learning_object_id: str
    target_key: str
    missing_capability: str
    status: str
    created_at: str
    resolved_at: str | None


@dataclass(frozen=True)
class ProbeCalibrationSessionRecord:
    """A learner-initiated calibration session (probe redesign spec §5.9)."""

    id: str
    session_id: str
    goal_id: str | None
    learning_object_ids: list[str]
    planned_episode_ids: list[str]
    time_budget_minutes: int
    status: str
    started_at: str
    ended_at: str | None
    created_at: str
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
    learner_confidence: str | None
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
class FacetUncertaintyState:
    id: str
    learning_object_id: str
    facet_id: str
    hypothesis_marginal: dict[str, float]
    uncertainty: float
    status: str
    opened_by_attempt_id: str
    opened_reason: str
    last_evidence_at: str | None
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

    def set_practice_item_active(
        self, practice_item_id: str, *, active: bool, clock: Clock | None = None
    ) -> None:
        """Flip only the active flag, preserving scheduling state on the row."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE practice_item_state SET active = ?, updated_at = ? WHERE practice_item_id = ?",
                (1 if active else 0, now, practice_item_id),
            )
            if cursor.rowcount == 0:
                connection.execute(
                    """
                    INSERT INTO practice_item_state(practice_item_id, active, updated_at)
                    VALUES (?, ?, ?)
                    """,
                    (practice_item_id, 1 if active else 0, now),
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

    def list_attempt_history(self) -> list[dict[str, Any]]:
        """Every attempt (time-ordered) with its posterior delta, if recorded.

        One LEFT JOIN so the knowledge-map chronicle can reconstruct each
        learning object's mastery trajectory (``posterior_delta`` carries the
        logit-space prior/posterior of the mastery update) alongside the raw
        attempt events. Attempts without a surprise row (legacy, or types that
        never update mastery) come back with ``posterior_delta`` = None.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT a.id AS id,
                       a.practice_item_id AS practice_item_id,
                       a.learning_object_id AS learning_object_id,
                       a.attempt_type AS attempt_type,
                       a.correctness AS correctness,
                       a.rubric_score AS rubric_score,
                       a.hints_used AS hints_used,
                       a.created_at AS created_at,
                       s.posterior_delta_json AS posterior_delta_json
                FROM practice_attempts a
                LEFT JOIN attempt_surprise s ON s.attempt_id = a.id
                ORDER BY a.created_at ASC, a.id ASC
                """
            ).fetchall()
        history: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(row)
            payload["posterior_delta"] = _loads(payload.pop("posterior_delta_json"), None)
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
        return [_active_error(row) for row in rows]

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

    def set_error_event_misconception(
        self,
        event_id: str,
        misconception_id: str | None,
        *,
        clock: Clock | None = None,
    ) -> bool:
        """Link (or unlink) an error event to a normalized registry belief."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE error_events SET misconception_id = ?, updated_at = ? WHERE id = ?",
                (misconception_id, now, event_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    # -- Misconception registry (spec §1.1) ---------------------------------

    def insert_misconception(
        self,
        *,
        learning_object_id: str,
        statement: str,
        id: str | None = None,
        concept_id: str | None = None,
        signature: str | None = None,
        facet_ids: Iterable[str] | None = None,
        severity: float = 0.0,
        status: str = "active",
        source_error_event_ids: Iterable[str] | None = None,
        clock: Clock | None = None,
    ) -> str:
        if status not in {"active", "resolving", "resolved"}:
            raise ValueError("status must be one of active, resolving, resolved")
        misconception_id = id or new_ulid()
        now = utc_now_iso(clock)
        resolved_at = now if status == "resolved" else None
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO misconceptions(
                  id, learning_object_id, concept_id, statement, signature,
                  facet_ids_json, severity, status, source_error_event_ids_json,
                  created_at, updated_at, resolved_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    misconception_id,
                    learning_object_id,
                    concept_id,
                    statement,
                    signature,
                    _json(sorted({str(f) for f in (facet_ids or [])})),
                    float(severity),
                    status,
                    _json([str(e) for e in (source_error_event_ids or [])]),
                    now,
                    now,
                    resolved_at,
                ),
            )
            connection.commit()
        return misconception_id

    def misconception(self, misconception_id: str) -> MisconceptionRecord | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM misconceptions WHERE id = ?",
                (misconception_id,),
            ).fetchone()
        return _decode_misconception(row) if row is not None else None

    def misconceptions_for_learning_object(
        self,
        learning_object_id: str,
        statuses: Iterable[str] = ("active", "resolving"),
    ) -> list[MisconceptionRecord]:
        status_list = list(statuses)
        placeholders = ",".join("?" for _ in status_list) or "''"
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM misconceptions
                WHERE learning_object_id = ? AND status IN ({placeholders})
                ORDER BY created_at DESC, id DESC
                """,
                (learning_object_id, *status_list),
            ).fetchall()
        return [_decode_misconception(row) for row in rows]

    def misconceptions_for_concepts(
        self,
        concept_ids: Iterable[str],
        statuses: Iterable[str] = ("active", "resolving"),
    ) -> list[MisconceptionRecord]:
        concept_list = [str(c) for c in concept_ids]
        status_list = list(statuses)
        if not concept_list:
            return []
        concept_placeholders = ",".join("?" for _ in concept_list)
        status_placeholders = ",".join("?" for _ in status_list) or "''"
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM misconceptions
                WHERE concept_id IN ({concept_placeholders})
                  AND status IN ({status_placeholders})
                ORDER BY created_at DESC, id DESC
                """,
                (*concept_list, *status_list),
            ).fetchall()
        return [_decode_misconception(row) for row in rows]

    def update_misconception(
        self,
        misconception_id: str,
        *,
        statement: str | None = None,
        signature: str | None = None,
        facet_ids: Iterable[str] | None = None,
        severity: float | None = None,
        status: str | None = None,
        append_source_error_event_ids: Iterable[str] | None = None,
        clock: Clock | None = None,
    ) -> MisconceptionRecord | None:
        if status is not None and status not in {"active", "resolving", "resolved"}:
            raise ValueError("status must be one of active, resolving, resolved")
        now = utc_now_iso(clock)
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM misconceptions WHERE id = ?",
                (misconception_id,),
            ).fetchone()
            if row is None:
                return None
            current = _decode_misconception(row)
            new_statement = statement if statement is not None else current.statement
            new_signature = signature if signature is not None else current.signature
            new_facets = (
                sorted({str(f) for f in facet_ids})
                if facet_ids is not None
                else current.facet_ids
            )
            new_severity = float(severity) if severity is not None else current.severity
            new_status = status if status is not None else current.status
            source_ids = list(current.source_error_event_ids)
            if append_source_error_event_ids:
                for event_id in append_source_error_event_ids:
                    if event_id not in source_ids:
                        source_ids.append(str(event_id))
            # Resolution stamps resolved_at; any reactivation clears it.
            if new_status == "resolved":
                resolved_at = current.resolved_at or now
            else:
                resolved_at = None
            connection.execute(
                """
                UPDATE misconceptions
                SET statement = ?, signature = ?, facet_ids_json = ?, severity = ?,
                    status = ?, source_error_event_ids_json = ?, updated_at = ?,
                    resolved_at = ?
                WHERE id = ?
                """,
                (
                    new_statement,
                    new_signature,
                    _json(new_facets),
                    new_severity,
                    new_status,
                    _json(source_ids),
                    now,
                    resolved_at,
                    misconception_id,
                ),
            )
            connection.commit()
        return self.misconception(misconception_id)

    # -- Item/misconception discrimination (spec §1.3) ----------------------

    def upsert_item_misconception_discrimination(
        self,
        row: ItemMisconceptionDiscrimination,
        *,
        clock: Clock | None = None,
    ) -> None:
        now = row.updated_at or utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO item_misconception_discrimination(
                  practice_item_id, misconception_id,
                  sensitivity_alpha, sensitivity_beta,
                  specificity_alpha, specificity_beta,
                  n_planted_trials, n_clean_trials, source, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(practice_item_id, misconception_id) DO UPDATE SET
                  sensitivity_alpha = excluded.sensitivity_alpha,
                  sensitivity_beta = excluded.sensitivity_beta,
                  specificity_alpha = excluded.specificity_alpha,
                  specificity_beta = excluded.specificity_beta,
                  n_planted_trials = excluded.n_planted_trials,
                  n_clean_trials = excluded.n_clean_trials,
                  source = excluded.source,
                  updated_at = excluded.updated_at
                """,
                (
                    row.practice_item_id,
                    row.misconception_id,
                    row.sensitivity_alpha,
                    row.sensitivity_beta,
                    row.specificity_alpha,
                    row.specificity_beta,
                    row.n_planted_trials,
                    row.n_clean_trials,
                    row.source,
                    now,
                ),
            )
            connection.commit()

    def discrimination_row(
        self, practice_item_id: str, misconception_id: str
    ) -> ItemMisconceptionDiscrimination | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM item_misconception_discrimination
                WHERE practice_item_id = ? AND misconception_id = ?
                """,
                (practice_item_id, misconception_id),
            ).fetchone()
        return _decode_discrimination(row) if row is not None else None

    def discrimination_rows_for_item(
        self, practice_item_id: str
    ) -> list[ItemMisconceptionDiscrimination]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM item_misconception_discrimination WHERE practice_item_id = ?",
                (practice_item_id,),
            ).fetchall()
        return [_decode_discrimination(row) for row in rows]

    def discrimination_rows_for_misconceptions(
        self, misconception_ids: Iterable[str]
    ) -> list[ItemMisconceptionDiscrimination]:
        ids = [str(m) for m in misconception_ids]
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM item_misconception_discrimination
                WHERE misconception_id IN ({placeholders})
                """,
                ids,
            ).fetchall()
        return [_decode_discrimination(row) for row in rows]

    def count_clean_attempts_since(
        self,
        learning_object_id: str,
        *,
        since: str,
        until: str,
        min_correctness: float,
    ) -> int:
        """Count "clean" attempts on a learning object in ``(since, until]``.

        Clean = graded correctness at or above ``min_correctness``, no error
        attribution recorded on the attempt row (``error_type IS NULL`` is
        equivalent to "wrote no error events"), and not a ``dont_know``/``skip``
        self-diagnosis. Bounding by ``until`` (the triggering attempt's
        ``created_at``) keeps the count reproducible under replay, where future
        attempts still exist in ``practice_attempts``.
        """

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
                """,
                (learning_object_id, since, until, min_correctness),
            ).fetchone()
        return int(row["clean_count"])

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

    def followup_source_attempt(self, attempt_id: str) -> str | None:
        """Gate-decision attempt whose queued follow-up this attempt answered.

        Mirrors ``pending_followup_practice_items``: the newest earlier
        ``attempt_surprise`` row carrying a queued action for this attempt's
        practice item, with no intervening attempt on that item between the
        gate row and this attempt. None when this attempt is not a follow-up.
        """

        with self.connection() as connection:
            attempt = connection.execute(
                "SELECT practice_item_id, created_at FROM practice_attempts WHERE id = ?",
                (attempt_id,),
            ).fetchone()
            if attempt is None:
                return None
            rows = connection.execute(
                """
                SELECT s.attempt_id, s.triggered_actions_json, s.created_at
                FROM attempt_surprise s
                WHERE s.triggered_actions_json IS NOT NULL
                  AND s.created_at <= ?
                  AND s.attempt_id != ?
                ORDER BY s.created_at DESC, s.attempt_id DESC
                """,
                (attempt["created_at"], attempt_id),
            ).fetchall()
            for row in rows:
                for action in _loads(row["triggered_actions_json"], []):
                    parsed = _queued_followup_action(action)
                    if parsed is None or parsed[1] != attempt["practice_item_id"]:
                        continue
                    intervening = connection.execute(
                        """
                        SELECT 1 FROM practice_attempts
                        WHERE practice_item_id = ? AND created_at > ? AND created_at < ? AND id != ?
                        LIMIT 1
                        """,
                        (
                            attempt["practice_item_id"],
                            row["created_at"],
                            attempt["created_at"],
                            attempt_id,
                        ),
                    ).fetchone()
                    if intervening is None:
                        return row["attempt_id"]
        return None

    def upsert_followup_rating(
        self,
        *,
        attempt_id: str,
        gate_attempt_id: str | None,
        useful: bool,
        source: str = "user",
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO followup_ratings(attempt_id, gate_attempt_id, useful, source, rated_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(attempt_id) DO UPDATE SET
                  gate_attempt_id = excluded.gate_attempt_id,
                  useful = excluded.useful,
                  source = excluded.source,
                  updated_at = excluded.updated_at
                """,
                (attempt_id, gate_attempt_id, 1 if useful else 0, source, now, now),
            )
            connection.commit()

    def followup_rating(self, attempt_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM followup_ratings WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["useful"] = bool(payload["useful"])
        return payload

    def gate_training_rows(self) -> list[dict[str, Any]]:
        """Every persisted gate evaluation LEFT JOINed to its usefulness rating
        (via gate_attempt_id) — the gate fitter's raw input, oldest first."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT s.attempt_id, s.gate_diagnostics_json, s.created_at,
                       r.useful AS rating_useful, r.source AS rating_source
                FROM attempt_surprise s
                LEFT JOIN followup_ratings r ON r.gate_attempt_id = s.attempt_id
                WHERE s.gate_diagnostics_json IS NOT NULL
                ORDER BY s.created_at ASC, s.attempt_id ASC
                """
            ).fetchall()
        return [
            {
                "attempt_id": row["attempt_id"],
                "created_at": row["created_at"],
                "gate_diagnostics": _loads(row["gate_diagnostics_json"], None),
                "rating_useful": None if row["rating_useful"] is None else bool(row["rating_useful"]),
                "rating_source": row["rating_source"],
            }
            for row in rows
        ]

    # ── Tutor Q&A question events ─────────────────────────────────────────

    def insert_question_event(self, event: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        event_id = str(event.get("id") or new_ulid())
        now = event.get("created_at") or utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO question_events(
                  id, context, note_id, practice_item_id, attempt_id, session_id,
                  question_md, answer_md, question_type, facets_json,
                  hint_equivalent, leak_suspected, rating, seconds_into_attempt,
                  provider, answer_status,
                  preceding_tutor_move, scaffold_level, warning_state, learner_mode,
                  question_opportunity, hints_used_before, direct_explanation_request,
                  attempt_progress, signal_channel, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    event["context"],
                    event.get("note_id"),
                    event.get("practice_item_id"),
                    event.get("attempt_id"),
                    event.get("session_id"),
                    event["question_md"],
                    event.get("answer_md"),
                    event.get("question_type"),
                    _json(sorted({str(facet) for facet in event.get("facets", [])})),
                    1 if event.get("hint_equivalent") else 0,
                    1 if event.get("leak_suspected") else 0,
                    event.get("rating"),
                    event.get("seconds_into_attempt"),
                    event.get("provider"),
                    event.get("answer_status") or "answered",
                    event.get("preceding_tutor_move"),
                    event.get("scaffold_level"),
                    event.get("warning_state"),
                    event.get("learner_mode"),
                    event.get("question_opportunity"),
                    event.get("hints_used_before"),
                    1 if event.get("direct_explanation_request") else 0,
                    event.get("attempt_progress"),
                    event.get("signal_channel"),
                    now,
                ),
            )
            connection.commit()
        return event_id

    def update_question_event_answer(
        self,
        event_id: str,
        *,
        answer_md: str | None,
        question_type: str | None,
        facets: list[str] | None,
        hint_equivalent: bool,
        leak_suspected: bool,
        answer_status: str,
        signal_channel: str | None = None,
    ) -> bool:
        """Complete (or fail) a pending question event after the provider call.

        Second half of the two-phase write: the question row already exists
        with answer_status='pending'; this fills in the answer and the tutor's
        classification (including the §13.4 epistemic vs interaction-preference
        channel), or marks the turn 'failed' while keeping the question text as
        evidence."""

        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE question_events
                SET answer_md = ?, question_type = ?, facets_json = ?,
                    hint_equivalent = ?, leak_suspected = ?, answer_status = ?,
                    signal_channel = COALESCE(?, signal_channel)
                WHERE id = ?
                """,
                (
                    answer_md,
                    question_type,
                    _json(sorted({str(facet) for facet in facets})) if facets is not None else _json([]),
                    1 if hint_equivalent else 0,
                    1 if leak_suspected else 0,
                    answer_status,
                    signal_channel,
                    event_id,
                ),
            )
            connection.commit()
            return cursor.rowcount > 0

    def question_events(
        self,
        *,
        context: str | None = None,
        note_id: str | None = None,
        practice_item_id: str | None = None,
        attempt_id: str | None = None,
        session_id: str | None = None,
        since: str | None = None,
        answer_status: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM question_events"
        clauses: list[str] = []
        parameters: list[Any] = []
        for column, value in (
            ("context", context),
            ("note_id", note_id),
            ("practice_item_id", practice_item_id),
            ("attempt_id", attempt_id),
            ("session_id", session_id),
            ("answer_status", answer_status),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                parameters.append(value)
        if since is not None:
            clauses.append("created_at >= ?")
            parameters.append(since)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [_decode_question_event(row) for row in rows]

    def count_question_events(
        self,
        *,
        context: str | None = None,
        note_id: str | None = None,
        practice_item_id: str | None = None,
        attempt_id: str | None = None,
        session_id: str | None = None,
        since: str | None = None,
        answer_status: str | None = None,
    ) -> int:
        return len(
            self.question_events(
                context=context,
                note_id=note_id,
                practice_item_id=practice_item_id,
                attempt_id=attempt_id,
                session_id=session_id,
                since=since,
                answer_status=answer_status,
            )
        )

    def question_event(self, event_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM question_events WHERE id = ?", (event_id,)
            ).fetchone()
        return _decode_question_event(row) if row is not None else None

    def set_question_event_rating(self, event_id: str, *, useful: bool) -> bool:
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE question_events SET rating = ? WHERE id = ?",
                (1 if useful else 0, event_id),
            )
            connection.commit()
            return cursor.rowcount > 0

    def count_hint_equivalent_question_events(
        self,
        practice_item_id: str,
        session_id: str | None,
        *,
        since: str | None = None,
        until: str | None = None,
    ) -> int:
        """Substantive mid-attempt questions in the hint-equivalence window.

        Practice-context questions on this (item, session) newer than ``since``
        (typically the previous attempt on the item) and, when ``until`` is
        given, at or before it (for reconstructing the count post hoc)."""

        query = (
            "SELECT COUNT(*) AS n FROM question_events "
            "WHERE context = 'practice' AND hint_equivalent = 1 AND practice_item_id = ?"
        )
        parameters: list[Any] = [practice_item_id]
        if session_id is not None:
            query += " AND session_id = ?"
            parameters.append(session_id)
        if since is not None:
            query += " AND created_at > ?"
            parameters.append(since)
        if until is not None:
            query += " AND created_at <= ?"
            parameters.append(until)
        with self.connection() as connection:
            row = connection.execute(query, parameters).fetchone()
        return int(row["n"]) if row is not None else 0

    def question_counts_by_facet(self) -> dict[str, int]:
        """Total question_events touching each classified facet."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT facets_json FROM question_events WHERE facets_json IS NOT NULL"
            ).fetchall()
        counts: dict[str, int] = {}
        for row in rows:
            for facet in _loads(row["facets_json"], []):
                counts[str(facet)] = counts.get(str(facet), 0) + 1
        return counts

    def set_question_event_saved_note(self, event_id: str, note_id: str | None) -> bool:
        """Persist the tutor-turn -> saved-note link (migration 027, spec §5).

        Written by ``save_tutor_answer_note`` so the "saved" UI state survives a
        remount and ``get_tutor_transcript`` can surface it."""

        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE question_events SET saved_note_id = ? WHERE id = ?",
                (note_id, event_id),
            )
            connection.commit()
            return cursor.rowcount > 0

    # --- question_promotions (spec_tutor_promotion.md §5) ----------------------

    def insert_question_promotion(
        self,
        *,
        question_event_id: str,
        intent: str,
        route: str,
        attributed_facets: list[str] | None = None,
        question_nature: str | None = None,
        attempted_in_thread: bool | None = None,
        learner_claim_id: str | None = None,
        intervention_need_id: str | None = None,
        proposed_patch_id: str | None = None,
        saved_note_id: str | None = None,
        existing_practice_item_id: str | None = None,
        created_practice_item_id: str | None = None,
        created_learning_object_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Insert the promotion ledger row for a tutor turn (§4 step 4).

        Idempotency is the caller's contract: the PK is ``question_event_id``,
        so re-promoting an already-promoted turn raises IntegrityError — the
        promotion service checks ``question_promotion(event_id)`` first."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO question_promotions(
                  question_event_id, intent, attributed_facets_json, question_nature,
                  attempted_in_thread, learner_claim_id, intervention_need_id,
                  proposed_patch_id, saved_note_id, existing_practice_item_id,
                  created_practice_item_id, created_learning_object_id, route,
                  created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    question_event_id,
                    intent,
                    _json(list(attributed_facets)) if attributed_facets is not None else None,
                    question_nature,
                    None if attempted_in_thread is None else (1 if attempted_in_thread else 0),
                    learner_claim_id,
                    intervention_need_id,
                    proposed_patch_id,
                    saved_note_id,
                    existing_practice_item_id,
                    created_practice_item_id,
                    created_learning_object_id,
                    route,
                    now,
                    now,
                ),
            )
            connection.commit()
        return question_event_id

    def update_question_promotion(
        self,
        question_event_id: str,
        *,
        route: Any = _UNSET,
        attributed_facets: Any = _UNSET,
        question_nature: Any = _UNSET,
        attempted_in_thread: Any = _UNSET,
        learner_claim_id: Any = _UNSET,
        intervention_need_id: Any = _UNSET,
        proposed_patch_id: Any = _UNSET,
        saved_note_id: Any = _UNSET,
        existing_practice_item_id: Any = _UNSET,
        created_practice_item_id: Any = _UNSET,
        created_learning_object_id: Any = _UNSET,
        clock: Clock | None = None,
    ) -> bool:
        """Fill created ids / transition the route on an existing promotion row.

        Only the supplied fields are written (``_UNSET`` sentinel distinguishes
        "leave unchanged" from an explicit ``None``); ``updated_at`` always
        advances."""

        assignments: list[str] = []
        parameters: list[Any] = []

        def _set(column: str, value: Any) -> None:
            assignments.append(f"{column} = ?")
            parameters.append(value)

        if route is not _UNSET:
            _set("route", route)
        if attributed_facets is not _UNSET:
            _set(
                "attributed_facets_json",
                _json(list(attributed_facets)) if attributed_facets is not None else None,
            )
        if question_nature is not _UNSET:
            _set("question_nature", question_nature)
        if attempted_in_thread is not _UNSET:
            _set(
                "attempted_in_thread",
                None if attempted_in_thread is None else (1 if attempted_in_thread else 0),
            )
        if learner_claim_id is not _UNSET:
            _set("learner_claim_id", learner_claim_id)
        if intervention_need_id is not _UNSET:
            _set("intervention_need_id", intervention_need_id)
        if proposed_patch_id is not _UNSET:
            _set("proposed_patch_id", proposed_patch_id)
        if saved_note_id is not _UNSET:
            _set("saved_note_id", saved_note_id)
        if existing_practice_item_id is not _UNSET:
            _set("existing_practice_item_id", existing_practice_item_id)
        if created_practice_item_id is not _UNSET:
            _set("created_practice_item_id", created_practice_item_id)
        if created_learning_object_id is not _UNSET:
            _set("created_learning_object_id", created_learning_object_id)

        _set("updated_at", utc_now_iso(clock))
        parameters.append(question_event_id)
        with self.connection() as connection:
            cursor = connection.execute(
                f"UPDATE question_promotions SET {', '.join(assignments)} WHERE question_event_id = ?",
                parameters,
            )
            connection.commit()
            return cursor.rowcount > 0

    def question_promotion(self, event_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM question_promotions WHERE question_event_id = ?",
                (event_id,),
            ).fetchone()
        return _decode_question_promotion(row) if row is not None else None

    def question_promotions(self) -> list[dict[str, Any]]:
        """All promotion rows, oldest first (requested-floor + signal joins)."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM question_promotions ORDER BY created_at, question_event_id"
            ).fetchall()
        return [_decode_question_promotion(row) for row in rows]

    def question_promotions_for_events(self, event_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
        """Promotion rows keyed by question_event_id, for the tutor transcript.

        Returns a dict so the transcript can attach promotion state per turn in
        one query (empty when no ids are given)."""

        ids = [str(event_id) for event_id in event_ids]
        if not ids:
            return {}
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM question_promotions WHERE question_event_id IN ({placeholders})",
                ids,
            ).fetchall()
        return {row["question_event_id"]: _decode_question_promotion(row) for row in rows}

    def requested_practice_item_ids(self) -> list[str]:
        """Practice items a learner asked to chase that have never been attempted.

        *Requested items* (spec §4a) = practice items referenced by a
        ``question_promotions`` row (``created_practice_item_id`` or
        ``existing_practice_item_id``) with zero ``practice_attempts``, oldest
        promotion first. Consumed by the scheduler requested-items floor."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT item_id FROM (
                  SELECT
                    COALESCE(created_practice_item_id, existing_practice_item_id) AS item_id,
                    MIN(created_at) AS first_requested_at
                  FROM question_promotions
                  WHERE created_practice_item_id IS NOT NULL
                     OR existing_practice_item_id IS NOT NULL
                  GROUP BY item_id
                )
                WHERE item_id NOT IN (SELECT DISTINCT practice_item_id FROM practice_attempts)
                ORDER BY first_requested_at, item_id
                """
            ).fetchall()
        return [row["item_id"] for row in rows]

    def pending_gap_need_for_facets(self, facet_ids: Iterable[str]) -> dict[str, Any] | None:
        """A pending tutor-gap need already targeting any of ``facet_ids``.

        Need-filing dedup (spec §4b): skip filing a new
        ``tutor_gap_declaration`` intervention_need when a pending one already
        covers one of the attributed facets. Returns the first matching need (by
        priority then age) or ``None``."""

        wanted = {str(facet) for facet in facet_ids}
        if not wanted:
            return None
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM intervention_needs
                WHERE status = 'pending' AND trigger_reason = 'tutor_gap_declaration'
                ORDER BY priority DESC, created_at
                """
            ).fetchall()
        for row in rows:
            targets = {str(facet) for facet in _loads(row["target_facets_json"], [])}
            if targets & wanted:
                return _decode_intervention_need(row)
        return None

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
        facet_uncertainty_states: Iterable[Mapping[str, Any]] = (),
        quality_state: Mapping[str, Any] | None = None,
        ability_transition: Mapping[str, Any] | None = None,
        attempt_debug_payload: Mapping[str, Any] | None = None,
        item_parameter_state: ItemParameterState | None = None,
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
            connection.execute(
                "DELETE FROM facet_uncertainty WHERE learning_object_id = ?",
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
                # Derived EB difficulty posteriors are rebuilt by replay.
                # fitted_parameters is intentionally NOT cleared here: fitted
                # sets are inputs to replay, not derived state.
                connection.execute(
                    f"DELETE FROM item_parameter_state WHERE practice_item_id IN ({placeholders})",
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
        facet_uncertainty_states: Iterable[Mapping[str, Any]] = (),
        quality_state: Mapping[str, Any] | None = None,
        ability_transition: Mapping[str, Any] | None = None,
        attempt_debug_payload: Mapping[str, Any] | None = None,
        item_parameter_state: ItemParameterState | None = None,
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

    def facet_uncertainty_state(
        self,
        learning_object_id: str,
        facet_id: str,
    ) -> FacetUncertaintyState | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM facet_uncertainty
                WHERE learning_object_id = ? AND facet_id = ?
                """,
                (learning_object_id, facet_id),
            ).fetchone()
        return _facet_uncertainty_state(row) if row is not None else None

    def facet_uncertainty_states(
        self,
        learning_object_id: str | None = None,
        *,
        statuses: Iterable[str] | None = None,
    ) -> list[FacetUncertaintyState]:
        clauses: list[str] = []
        parameters: list[Any] = []
        if learning_object_id is not None:
            clauses.append("learning_object_id = ?")
            parameters.append(learning_object_id)
        status_values = list(statuses or [])
        if status_values:
            clauses.append(f"status IN ({','.join('?' for _ in status_values)})")
            parameters.extend(status_values)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM facet_uncertainty{where}
                ORDER BY learning_object_id, status, uncertainty DESC, facet_id
                """,
                parameters,
            ).fetchall()
        return [_facet_uncertainty_state(row) for row in rows]

    def upsert_facet_uncertainty_state(self, state: Mapping[str, Any]) -> None:
        with self.connection() as connection:
            self._upsert_facet_uncertainty_state(connection, state)
            connection.commit()

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

    def recent_surprise_signals(
        self, *, limit: int = 200, exclude_attempt_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Most recent attempt_surprise signal rows for quantile-threshold
        resolution (newest first)."""

        query = (
            "SELECT attempt_id, bayesian_surprise, surprise_direction, gate_diagnostics_json "
            "FROM attempt_surprise"
        )
        params: tuple[Any, ...] = ()
        if exclude_attempt_id is not None:
            query += " WHERE attempt_id != ?"
            params = (exclude_attempt_id,)
        query += " ORDER BY created_at DESC, attempt_id DESC LIMIT ?"
        params = (*params, limit)
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [
            {
                "attempt_id": row["attempt_id"],
                "bayesian_surprise": row["bayesian_surprise"],
                "surprise_direction": row["surprise_direction"],
                "gate_diagnostics": _loads(row["gate_diagnostics_json"], None),
            }
            for row in rows
        ]

    def chosen_candidate_outcomes(self) -> list[dict[str, Any]]:
        """Slate candidates joined to their realized attempts (`learnloop eval`
        prediction-calibration input), oldest first."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT c.id AS candidate_id, c.slate_id, c.practice_item_id, c.learning_object_id,
                       c.predicted_correctness, c.selection_propensity, c.exploration_flag,
                       c.selected_mode,
                       a.id AS attempt_id, a.correctness, a.rubric_score, a.attempt_type, a.created_at
                FROM scheduler_slate_candidates c
                JOIN practice_attempts a ON a.id = c.chosen_attempt_id
                WHERE c.predicted_correctness IS NOT NULL AND a.correctness IS NOT NULL
                ORDER BY a.created_at ASC, a.id ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def retention_label_rows(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM learning_outcome_labels
                WHERE label_type = 'same_item_retention'
                ORDER BY created_at ASC, id ASC
                """
            ).fetchall()
        return [_decode_learning_outcome_label(row) for row in rows]

    def item_attempt_history(self) -> list[dict[str, Any]]:
        """Graded attempts ordered for per-item FSRS replay (`learnloop eval`)."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, practice_item_id, rubric_score, hints_used, attempt_type, created_at
                FROM practice_attempts
                WHERE rubric_score IS NOT NULL
                ORDER BY practice_item_id ASC, created_at ASC, id ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def candidate_propensity_rows(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT slate_id, id, selection_propensity, selection_temperature,
                       exploration_flag, chosen_attempt_id, was_returned
                FROM scheduler_slate_candidates
                ORDER BY created_at ASC, id ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_fitted_parameters(
        self,
        *,
        scope: str,
        params: Mapping[str, Any],
        algorithm_version: str,
        training_rows_count: int,
        training_data_through: str | None = None,
        metrics: Mapping[str, Any] | None = None,
        activate: bool = True,
        clock: Clock | None = None,
    ) -> str:
        """Insert a fitted parameter set; when ``activate``, atomically replace
        the currently active set for the scope (history rows are kept)."""

        fitted_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            if activate:
                connection.execute(
                    "UPDATE fitted_parameters SET active = 0, deactivated_at = ? WHERE scope = ? AND active = 1",
                    (now, scope),
                )
            connection.execute(
                """
                INSERT INTO fitted_parameters(
                  id, scope, params_json, fitted_at, algorithm_version,
                  training_rows_count, training_data_through, metrics_json,
                  active, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fitted_id,
                    scope,
                    _json(dict(params)),
                    now,
                    algorithm_version,
                    training_rows_count,
                    training_data_through,
                    _json(dict(metrics)) if metrics is not None else None,
                    1 if activate else 0,
                    now,
                ),
            )
            connection.commit()
        return fitted_id

    def active_fitted_parameters(self, scope: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM fitted_parameters
                WHERE scope = ? AND active = 1
                ORDER BY fitted_at DESC, id DESC
                LIMIT 1
                """,
                (scope,),
            ).fetchone()
        return _decode_fitted_parameters(row) if row is not None else None

    def list_fitted_parameters(self, scope: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        query = "SELECT * FROM fitted_parameters"
        params: tuple[Any, ...] = ()
        if scope is not None:
            query += " WHERE scope = ?"
            params = (scope,)
        query += " ORDER BY fitted_at DESC, rowid DESC LIMIT ?"
        params = (*params, limit)
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [_decode_fitted_parameters(row) for row in rows]

    def deactivate_fitted_parameters(
        self, scope: str, *, fitted_id: str | None = None, clock: Clock | None = None
    ) -> int:
        now = utc_now_iso(clock)
        query = "UPDATE fitted_parameters SET active = 0, deactivated_at = ? WHERE scope = ? AND active = 1"
        params: tuple[Any, ...] = (now, scope)
        if fitted_id is not None:
            query += " AND id = ?"
            params = (*params, fitted_id)
        with self.connection() as connection:
            cursor = connection.execute(query, params)
            connection.commit()
            return cursor.rowcount

    def list_all_attempts(self) -> list[dict[str, Any]]:
        """Every practice attempt ordered for per-item replay (fitting jobs)."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM practice_attempts ORDER BY practice_item_id ASC, created_at ASC, id ASC"
            ).fetchall()
        return [dict(row) for row in rows]

    def item_parameter_state(self, practice_item_id: str) -> ItemParameterState | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM item_parameter_state WHERE practice_item_id = ?",
                (practice_item_id,),
            ).fetchone()
        return _decode_item_parameter_state(row) if row is not None else None

    def item_parameter_states(self) -> dict[str, ItemParameterState]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM item_parameter_state").fetchall()
        return {row["practice_item_id"]: _decode_item_parameter_state(row) for row in rows}

    def upsert_item_parameter_state(self, state: ItemParameterState) -> None:
        with self.connection() as connection:
            self._upsert_item_parameter_state_record(connection, state)
            connection.commit()

    def _upsert_item_parameter_state_record(
        self, connection: sqlite3.Connection, state: ItemParameterState
    ) -> None:
        connection.execute(
            """
            INSERT INTO item_parameter_state(
              practice_item_id, b_mean, b_var, evidence_count, algorithm_version, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(practice_item_id) DO UPDATE SET
              b_mean = excluded.b_mean,
              b_var = excluded.b_var,
              evidence_count = excluded.evidence_count,
              algorithm_version = excluded.algorithm_version,
              updated_at = excluded.updated_at
            """,
            (
                state.practice_item_id,
                state.b_mean,
                state.b_var,
                state.evidence_count,
                state.algorithm_version,
                state.updated_at,
            ),
        )

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
                        candidate_requirements_json = ?, diagnostic_focus_json = ?,
                        updated_at = ?
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
                        _json(need.get("diagnostic_focus")) if need.get("diagnostic_focus") is not None else None,
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
                      candidate_requirements_json, diagnostic_focus_json,
                      created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        _json(need.get("diagnostic_focus")) if need.get("diagnostic_focus") is not None else None,
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

    def intervention_need(self, need_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM intervention_needs WHERE id = ?",
                (need_id,),
            ).fetchone()
        return _decode_intervention_need(row) if row is not None else None

    def update_intervention_need_diagnostic_focus(
        self,
        need_id: str,
        diagnostic_focus: dict[str, Any] | None,
        *,
        clock: Clock | None = None,
    ) -> bool:
        """Replace a need's diagnostic_focus snapshot in place (spec §6 reopen).

        Used to attach the sim gate's ``last_gate_result`` estimates when a
        generated diagnostic is rejected, so the next generation round sees why
        the previous item failed. A direct UPDATE (not upsert) to avoid changing
        the upsert dedup key."""

        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE intervention_needs SET diagnostic_focus_json = ?, updated_at = ? WHERE id = ?",
                (
                    _json(diagnostic_focus) if diagnostic_focus is not None else None,
                    utc_now_iso(clock),
                    need_id,
                ),
            )
            connection.commit()
            return cursor.rowcount > 0

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

    def append_intervention_need_target_facets(
        self,
        need_id: str,
        facets: list[str],
        *,
        clock: Clock | None = None,
    ) -> bool:
        """Union extra facets into an existing need's target_facets in place.

        A direct UPDATE (not upsert): changing target_facets would change the
        upsert dedup key and spawn a duplicate pending need."""

        if not facets:
            return False
        with self.connection() as connection:
            row = connection.execute(
                "SELECT target_facets_json FROM intervention_needs WHERE id = ?",
                (need_id,),
            ).fetchone()
            if row is None:
                return False
            existing = {str(facet) for facet in _loads(row["target_facets_json"], [])}
            merged = sorted(existing | {str(facet) for facet in facets})
            if merged == sorted(existing):
                return False
            cursor = connection.execute(
                "UPDATE intervention_needs SET target_facets_json = ?, updated_at = ? WHERE id = ?",
                (_json(merged), utc_now_iso(clock), need_id),
            )
            connection.commit()
            return cursor.rowcount > 0

    def intervention_needs_for_diagnostic_proposal(self, patch_id: str) -> list[dict[str, Any]]:
        prefix = f"diagnostic_proposal_queued:{patch_id}"
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM intervention_needs
                WHERE status = 'fulfilled'
                  AND (blocked_reason = ? OR blocked_reason LIKE ?)
                ORDER BY created_at, id
                """,
                (prefix, f"{prefix}:%"),
            ).fetchall()
        return [_decode_intervention_need(row) for row in rows]

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

    # --- Probe episodes (probe redesign spec §5) -------------------------------

    def insert_probe_episode(
        self,
        *,
        learning_object_id: str,
        status: str,
        trigger: str,
        hypothesis_set_id: str | None,
        active_state_segment_id: str | None,
        algorithm_version: str,
        target_decision: Mapping[str, Any] | None = None,
        required_facets: list[str] | None = None,
        minimum_independent_observations: int = 2,
        maximum_observations: int = 4,
        entered_at: str | None = None,
        episode_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        episode_id = episode_id or new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO probe_episodes(
                  id, learning_object_id, status, trigger, hypothesis_set_id,
                  active_state_segment_id, target_decision_json, required_facets_json,
                  minimum_independent_observations, maximum_observations,
                  entered_at, completed_at, completion_reason, algorithm_version,
                  created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?)
                """,
                (
                    episode_id,
                    learning_object_id,
                    status,
                    trigger,
                    hypothesis_set_id,
                    active_state_segment_id,
                    _json(dict(target_decision)) if target_decision is not None else None,
                    _json(list(required_facets or [])),
                    minimum_independent_observations,
                    maximum_observations,
                    entered_at or now,
                    algorithm_version,
                    now,
                    now,
                ),
            )
            connection.commit()
        return episode_id

    def probe_episode(self, episode_id: str) -> ProbeEpisodeRecord | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM probe_episodes WHERE id = ?", (episode_id,)
            ).fetchone()
        return _probe_episode_record(row) if row is not None else None

    def open_probe_episode(self, learning_object_id: str) -> ProbeEpisodeRecord | None:
        """The single open (`pending_items` / `in_progress`) episode for an LO, if any."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM probe_episodes
                WHERE learning_object_id = ?
                  AND status IN ('pending_items', 'in_progress')
                ORDER BY created_at DESC LIMIT 1
                """,
                (learning_object_id,),
            ).fetchone()
        return _probe_episode_record(row) if row is not None else None

    def open_probe_episodes(self) -> dict[str, ProbeEpisodeRecord]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM probe_episodes WHERE status IN ('pending_items', 'in_progress')"
            ).fetchall()
        return {row["learning_object_id"]: _probe_episode_record(row) for row in rows}

    def probe_episodes_for_learning_object(self, learning_object_id: str) -> list[ProbeEpisodeRecord]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM probe_episodes WHERE learning_object_id = ? ORDER BY created_at, id",
                (learning_object_id,),
            ).fetchall()
        return [_probe_episode_record(row) for row in rows]

    def update_probe_episode_status(
        self,
        episode_id: str,
        *,
        status: str,
        completion_reason: str | None = None,
        completed_at: str | None = None,
        active_state_segment_id: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        assignments = ["status = ?", "updated_at = ?"]
        parameters: list[Any] = [status, now]
        if completion_reason is not None:
            assignments.append("completion_reason = ?")
            parameters.append(completion_reason)
        if completed_at is not None:
            assignments.append("completed_at = ?")
            parameters.append(completed_at)
        if active_state_segment_id is not None:
            assignments.append("active_state_segment_id = ?")
            parameters.append(active_state_segment_id)
        parameters.append(episode_id)
        with self.connection() as connection:
            connection.execute(
                f"UPDATE probe_episodes SET {', '.join(assignments)} WHERE id = ?",
                parameters,
            )
            connection.commit()

    # --- State segments (§5.1) -------------------------------------------------

    def open_state_segment(
        self,
        *,
        learning_object_id: str,
        probe_episode_id: str | None,
        reason: str,
        opened_by_attempt_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Mint the next state segment for an LO and persist its opening event."""

        segment_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            row = connection.execute(
                "SELECT COALESCE(MAX(sequence), 0) AS seq FROM probe_state_segments WHERE learning_object_id = ?",
                (learning_object_id,),
            ).fetchone()
            connection.execute(
                """
                INSERT INTO probe_state_segments(
                  id, learning_object_id, probe_episode_id, sequence, reason,
                  opened_by_attempt_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    segment_id,
                    learning_object_id,
                    probe_episode_id,
                    int(row["seq"]) + 1,
                    reason,
                    opened_by_attempt_id,
                    now,
                ),
            )
            if probe_episode_id is not None:
                connection.execute(
                    "UPDATE probe_episodes SET active_state_segment_id = ?, updated_at = ? WHERE id = ?",
                    (segment_id, now, probe_episode_id),
                )
            connection.commit()
        return segment_id

    def state_segments_for_learning_object(self, learning_object_id: str) -> list[ProbeStateSegmentRecord]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM probe_state_segments WHERE learning_object_id = ? ORDER BY sequence",
                (learning_object_id,),
            ).fetchall()
        return [_probe_state_segment_record(row) for row in rows]

    # --- Probe presentations (§5.1) ---------------------------------------------

    def insert_probe_presentation(
        self,
        *,
        probe_episode_id: str,
        practice_item_id: str,
        state_segment_id: str,
        scheduler_candidate_id: str | None = None,
        probe_family_template_id: str | None = None,
        probe_family_template_version: int | None = None,
        instrument_card_id: str | None = None,
        instrument_card_version: int | None = None,
        instrument_card_snapshot: Mapping[str, Any] | None = None,
        target_hypothesis_pairs: list[list[str]] | None = None,
        target_facets: list[str] | None = None,
        posterior_at_selection: Mapping[str, float] | None = None,
        entropy_at_selection: float | None = None,
        expected_information_gain: float | None = None,
        selection_policy_version: str | None = None,
        selection_components: Mapping[str, Any] | None = None,
        expires_at: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        presentation_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            _insert_probe_presentation_row(
                connection,
                presentation_id=presentation_id,
                now=now,
                values={
                    "probe_episode_id": probe_episode_id,
                    "practice_item_id": practice_item_id,
                    "scheduler_candidate_id": scheduler_candidate_id,
                    "state_segment_id": state_segment_id,
                    "probe_family_template_id": probe_family_template_id,
                    "probe_family_template_version": probe_family_template_version,
                    "instrument_card_id": instrument_card_id,
                    "instrument_card_version": instrument_card_version,
                    "instrument_card_snapshot": instrument_card_snapshot,
                    "target_hypothesis_pairs": target_hypothesis_pairs,
                    "target_facets": target_facets,
                    "posterior_at_selection": posterior_at_selection,
                    "entropy_at_selection": entropy_at_selection,
                    "expected_information_gain": expected_information_gain,
                    "selection_policy_version": selection_policy_version,
                    "selection_components": selection_components,
                    "expires_at": expires_at,
                },
            )
            connection.commit()
        return presentation_id

    def probe_presentation(self, presentation_id: str) -> ProbePresentationRecord | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM probe_presentations WHERE id = ?", (presentation_id,)
            ).fetchone()
        return _probe_presentation_record(row) if row is not None else None

    def probe_presentations_for_episode(self, probe_episode_id: str) -> list[ProbePresentationRecord]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM probe_presentations WHERE probe_episode_id = ? ORDER BY created_at, id",
                (probe_episode_id,),
            ).fetchall()
        return [_probe_presentation_record(row) for row in rows]

    def active_probe_presentation(
        self, probe_episode_id: str, practice_item_id: str | None = None
    ) -> ProbePresentationRecord | None:
        """The most recent committed-but-unconsumed presentation for an episode."""

        clauses = ["probe_episode_id = ?", "status IN ('selected', 'served')"]
        parameters: list[Any] = [probe_episode_id]
        if practice_item_id is not None:
            clauses.append("practice_item_id = ?")
            parameters.append(practice_item_id)
        with self.connection() as connection:
            row = connection.execute(
                f"""
                SELECT * FROM probe_presentations
                WHERE {' AND '.join(clauses)}
                ORDER BY created_at DESC, id DESC LIMIT 1
                """,
                parameters,
            ).fetchone()
        return _probe_presentation_record(row) if row is not None else None

    def active_probe_presentation_for_session(
        self, session_id: str
    ) -> ProbePresentationRecord | None:
        """The scheduler-backed assignment currently owned by one session."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT p.*
                FROM probe_presentations p
                JOIN scheduler_slate_candidates c ON c.id = p.scheduler_candidate_id
                JOIN scheduler_slates s ON s.id = c.slate_id
                WHERE s.session_id = ? AND p.status IN ('selected', 'served')
                ORDER BY p.created_at DESC, p.id DESC
                LIMIT 1
                """,
                (session_id,),
            ).fetchone()
        return _probe_presentation_record(row) if row is not None else None

    def mark_probe_presentation_served(self, presentation_id: str, *, clock: Clock | None = None) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE probe_presentations
                SET status = 'served', served_at = COALESCE(served_at, ?), updated_at = ?
                WHERE id = ? AND status = 'selected'
                """,
                (now, now, presentation_id),
            )
            connection.commit()

    def consume_probe_presentation(self, presentation_id: str, *, clock: Clock | None = None) -> bool:
        """Atomically move a presentation to `submitted`; False if not consumable."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE probe_presentations
                SET status = 'submitted', submitted_at = ?, updated_at = ?
                WHERE id = ? AND status IN ('selected', 'served')
                """,
                (now, now, presentation_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    def end_probe_presentation(
        self, presentation_id: str, *, end_reason: str, clock: Clock | None = None
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE probe_presentations
                SET status = 'ended', end_reason = ?, ended_at = ?, updated_at = ?
                WHERE id = ? AND status IN ('selected', 'served')
                """,
                (end_reason, now, now, presentation_id),
            )
            connection.commit()

    # --- Probe observations (§5.1) ----------------------------------------------

    def insert_probe_observation(
        self,
        *,
        attempt_id: str,
        posterior_before: Mapping[str, float],
        posterior_after: Mapping[str, float],
        entropy_before: float,
        entropy_after: float,
        realized_information_gain: float,
        independent_evidence_discount: float | None = None,
        contamination: Mapping[str, Any] | None = None,
        grader_channel: Mapping[str, Any] | None = None,
        updates_belief: bool = True,
        eligible_for_completion: bool = False,
        features: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> str:
        observation_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO probe_observations(
                  id, attempt_id, posterior_before_json, posterior_after_json,
                  entropy_before, entropy_after, realized_information_gain,
                  independent_evidence_discount, contamination_json, grader_channel_json,
                  updates_belief, eligible_for_completion, features_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    observation_id,
                    attempt_id,
                    _json(dict(posterior_before)),
                    _json(dict(posterior_after)),
                    entropy_before,
                    entropy_after,
                    realized_information_gain,
                    independent_evidence_discount,
                    _json(dict(contamination)) if contamination is not None else None,
                    _json(dict(grader_channel)) if grader_channel is not None else None,
                    1 if updates_belief else 0,
                    1 if eligible_for_completion else 0,
                    _json(dict(features)) if features is not None else None,
                    now,
                ),
            )
            connection.commit()
        return observation_id

    def qualifying_probe_observation_count_for_session(self, session_id: str) -> int:
        """Qualifying diagnostic observations recorded in one session (§5.9 cap)."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM probe_observations o
                JOIN practice_attempts a ON a.id = o.attempt_id
                WHERE a.session_id = ? AND o.eligible_for_completion = 1
                """,
                (session_id,),
            ).fetchone()
        return int(row["count"])

    def qualifying_probe_observation_count(self) -> int:
        """Qualifying diagnostic observations across the whole vault (§5.9
        time-to-first-ordinary-practice ceiling)."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM probe_observations WHERE eligible_for_completion = 1"
            ).fetchone()
        return int(row["count"])

    def ordinary_practice_attempt_count(self) -> int:
        """Attempts recorded outside the diagnostic/exam channels (§5.9): the
        signal that ordinary practice has started in this vault."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count FROM practice_attempts
                WHERE probe_presentation_id IS NULL
                  AND attempt_type NOT IN ('diagnostic_probe', 'exam_attempt', 'exam_evidence')
                """
            ).fetchone()
        return int(row["count"])

    def probe_observation_for_attempt(self, attempt_id: str) -> ProbeObservationRecord | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM probe_observations WHERE attempt_id = ?", (attempt_id,)
            ).fetchone()
        return _probe_observation_record(row) if row is not None else None

    def probe_observations_for_episode(self, probe_episode_id: str) -> list[dict[str, Any]]:
        """Observations joined through attempt → presentation → episode (§5.1).

        Episode progress is always derived from this join, never cached. Each row
        is the observation record dict plus its attempt and presentation context.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT o.*, a.practice_item_id, a.attempt_type, a.rubric_score,
                       a.error_type, a.hints_used, a.created_at AS attempt_created_at,
                       p.id AS presentation_id, p.state_segment_id, p.target_facets_json,
                       p.instrument_card_id, p.instrument_card_version,
                       p.probe_family_template_id, p.probe_family_template_version,
                       p.expected_information_gain, p.selection_components_json,
                       p.served_at, p.submitted_at, p.instrument_card_snapshot_json
                FROM probe_observations o
                JOIN practice_attempts a ON a.id = o.attempt_id
                JOIN probe_presentations p ON p.id = a.probe_presentation_id
                WHERE p.probe_episode_id = ?
                ORDER BY o.created_at, o.id
                """,
                (probe_episode_id,),
            ).fetchall()
        results: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(row)
            payload["observation"] = _probe_observation_record(row)
            payload["target_facets"] = _loads(row["target_facets_json"], [])
            payload["selection_components"] = _loads(row["selection_components_json"], {})
            payload["instrument_card_snapshot"] = _loads(row["instrument_card_snapshot_json"], None)
            results.append(payload)
        return results

    def list_probe_episodes(self, *, statuses: tuple[str, ...] | None = None) -> list[ProbeEpisodeRecord]:
        """All episodes, oldest first, optionally filtered by status."""

        query = "SELECT * FROM probe_episodes"
        params: tuple[Any, ...] = ()
        if statuses:
            placeholders = ", ".join("?" for _ in statuses)
            query += f" WHERE status IN ({placeholders})"
            params = tuple(statuses)
        query += " ORDER BY created_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [_probe_episode_record(row) for row in rows]

    # --- Probe families and Instrument Cards (§9) --------------------------------

    def upsert_probe_family_template(
        self,
        *,
        family_id: str,
        version: int,
        status: str,
        template: Mapping[str, Any],
        schema_hash: str,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO probe_family_templates(id, version, status, template_json, schema_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id, version) DO UPDATE SET
                  status = excluded.status
                """,
                (family_id, version, status, _json(dict(template)), schema_hash, now),
            )
            connection.commit()

    def probe_family_template(self, family_id: str, version: int) -> ProbeFamilyTemplateRecord | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM probe_family_templates WHERE id = ? AND version = ?",
                (family_id, version),
            ).fetchone()
        return _probe_family_template_record(row) if row is not None else None

    def latest_probe_family_template(
        self, family_id: str, *, statuses: tuple[str, ...] = ("provisional", "trusted")
    ) -> ProbeFamilyTemplateRecord | None:
        placeholders = ", ".join("?" for _ in statuses)
        with self.connection() as connection:
            row = connection.execute(
                f"""
                SELECT * FROM probe_family_templates
                WHERE id = ? AND status IN ({placeholders})
                ORDER BY version DESC LIMIT 1
                """,
                (family_id, *statuses),
            ).fetchone()
        return _probe_family_template_record(row) if row is not None else None

    def retire_probe_family_template(self, family_id: str, version: int, *, clock: Clock | None = None) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                "UPDATE probe_family_templates SET status = 'retired', retired_at = ? WHERE id = ? AND version = ?",
                (now, family_id, version),
            )
            connection.commit()

    def update_probe_family_template_status(
        self, family_id: str, version: int, *, status: str, clock: Clock | None = None
    ) -> None:
        """Lifecycle transition for one family version (§9.7, Checkpoint 4.7).

        ``retired_at`` is stamped when entering ``retired`` and cleared
        otherwise; historical observations keep replaying against the version
        they persisted (§9.1), so this never rewrites template_json.
        """

        now = utc_now_iso(clock)
        retired_at = now if status == "retired" else None
        with self.connection() as connection:
            connection.execute(
                "UPDATE probe_family_templates SET status = ?, retired_at = ? WHERE id = ? AND version = ?",
                (status, retired_at, family_id, version),
            )
            connection.commit()

    def all_probe_family_templates(self) -> list[ProbeFamilyTemplateRecord]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM probe_family_templates ORDER BY id, version"
            ).fetchall()
        return [_probe_family_template_record(row) for row in rows]

    def insert_probe_family_lifecycle_event(
        self,
        *,
        probe_family_template_id: str,
        probe_family_template_version: int,
        from_status: str,
        to_status: str,
        reason: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> str:
        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO probe_family_lifecycle_events(
                  id, probe_family_template_id, probe_family_template_version,
                  from_status, to_status, reason_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    probe_family_template_id,
                    probe_family_template_version,
                    from_status,
                    to_status,
                    _json(dict(reason)) if reason is not None else None,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return event_id

    def probe_family_lifecycle_events(
        self, probe_family_template_id: str, probe_family_template_version: int | None = None
    ) -> list[dict[str, Any]]:
        query = (
            "SELECT * FROM probe_family_lifecycle_events WHERE probe_family_template_id = ?"
        )
        params: tuple[Any, ...] = (probe_family_template_id,)
        if probe_family_template_version is not None:
            query += " AND probe_family_template_version = ?"
            params = (*params, probe_family_template_version)
        query += " ORDER BY created_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        results = []
        for row in rows:
            payload = dict(row)
            payload["reason"] = _loads(row["reason_json"], None)
            results.append(payload)
        return results

    def insert_probe_instrument_card(
        self,
        *,
        card_id: str,
        version: int,
        probe_family_template_id: str,
        probe_family_template_version: int,
        learning_object_id: str,
        hypothesis_scope: list[str],
        card: Mapping[str, Any],
        compiled_likelihood_hash: str,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO probe_instrument_cards(
                  id, version, probe_family_template_id, probe_family_template_version,
                  learning_object_id, hypothesis_scope_json, card_json,
                  compiled_likelihood_hash, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    card_id,
                    version,
                    probe_family_template_id,
                    probe_family_template_version,
                    learning_object_id,
                    _json(list(hypothesis_scope)),
                    _json(dict(card)),
                    compiled_likelihood_hash,
                    now,
                ),
            )
            connection.commit()

    def probe_instrument_card(self, card_id: str, version: int) -> ProbeInstrumentCardRecord | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM probe_instrument_cards WHERE id = ? AND version = ?",
                (card_id, version),
            ).fetchone()
        return _probe_instrument_card_record(row) if row is not None else None

    def probe_instrument_cards_for_learning_object(
        self, learning_object_id: str
    ) -> list[ProbeInstrumentCardRecord]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM probe_instrument_cards
                WHERE learning_object_id = ? AND retired_at IS NULL
                ORDER BY id, version
                """,
                (learning_object_id,),
            ).fetchall()
        return [_probe_instrument_card_record(row) for row in rows]

    def link_probe_item_family(
        self,
        *,
        practice_item_id: str,
        instrument_card_id: str,
        instrument_card_version: int,
        generator_id: str | None = None,
        generator_version: str | None = None,
        generation_seed: str | None = None,
        instance_metadata: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO probe_item_family_links(
                  practice_item_id, instrument_card_id, instrument_card_version,
                  generator_id, generator_version, generation_seed,
                  instance_metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    practice_item_id,
                    instrument_card_id,
                    instrument_card_version,
                    generator_id,
                    generator_version,
                    generation_seed,
                    _json(dict(instance_metadata)) if instance_metadata is not None else None,
                    now,
                ),
            )
            connection.commit()

    def probe_item_family_links(self, practice_item_id: str) -> list[ProbeItemFamilyLinkRecord]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM probe_item_family_links WHERE practice_item_id = ? ORDER BY created_at",
                (practice_item_id,),
            ).fetchall()
        return [_probe_item_family_link_record(row) for row in rows]

    def probe_items_for_card(self, instrument_card_id: str, instrument_card_version: int) -> list[str]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT practice_item_id FROM probe_item_family_links
                WHERE instrument_card_id = ? AND instrument_card_version = ?
                ORDER BY created_at
                """,
                (instrument_card_id, instrument_card_version),
            ).fetchall()
        return [row["practice_item_id"] for row in rows]

    def upsert_probe_family_calibration(
        self,
        *,
        probe_family_template_id: str,
        probe_family_template_version: int,
        evidence_source: str,
        parameter_posterior: Mapping[str, Any],
        sample_size: int,
        effective_sample_size: float | None = None,
        generator_version: str | None = None,
        grader_version: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM probe_family_calibrations
                WHERE probe_family_template_id = ? AND probe_family_template_version = ?
                  AND COALESCE(generator_version, '') = COALESCE(?, '')
                  AND COALESCE(grader_version, '') = COALESCE(?, '')
                  AND evidence_source = ?
                """,
                (
                    probe_family_template_id,
                    probe_family_template_version,
                    generator_version,
                    grader_version,
                    evidence_source,
                ),
            ).fetchone()
            if existing is not None:
                connection.execute(
                    """
                    UPDATE probe_family_calibrations
                    SET parameter_posterior_json = ?, sample_size = ?, effective_sample_size = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (_json(dict(parameter_posterior)), sample_size, effective_sample_size, now, existing["id"]),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO probe_family_calibrations(
                      id, probe_family_template_id, probe_family_template_version,
                      generator_version, grader_version, evidence_source,
                      parameter_posterior_json, sample_size, effective_sample_size, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_ulid(),
                        probe_family_template_id,
                        probe_family_template_version,
                        generator_version,
                        grader_version,
                        evidence_source,
                        _json(dict(parameter_posterior)),
                        sample_size,
                        effective_sample_size,
                        now,
                    ),
                )
            connection.commit()

    def probe_family_calibration(
        self,
        probe_family_template_id: str,
        probe_family_template_version: int,
        *,
        evidence_source: str,
        generator_version: str | None = None,
        grader_version: str | None = None,
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM probe_family_calibrations
                WHERE probe_family_template_id = ? AND probe_family_template_version = ?
                  AND COALESCE(generator_version, '') = COALESCE(?, '')
                  AND COALESCE(grader_version, '') = COALESCE(?, '')
                  AND evidence_source = ?
                """,
                (
                    probe_family_template_id,
                    probe_family_template_version,
                    generator_version,
                    grader_version,
                    evidence_source,
                ),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["parameter_posterior"] = _loads(row["parameter_posterior_json"], {})
        return payload

    def probe_family_calibrations_for_family(
        self, probe_family_template_id: str, probe_family_template_version: int
    ) -> list[dict[str, Any]]:
        """Every calibration row for one family version, all evidence sources."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM probe_family_calibrations
                WHERE probe_family_template_id = ? AND probe_family_template_version = ?
                ORDER BY evidence_source, COALESCE(grader_version, ''), COALESCE(generator_version, '')
                """,
                (probe_family_template_id, probe_family_template_version),
            ).fetchall()
        results = []
        for row in rows:
            payload = dict(row)
            payload["parameter_posterior"] = _loads(row["parameter_posterior_json"], {})
            results.append(payload)
        return results

    def upsert_probe_item_calibration(
        self,
        *,
        practice_item_id: str,
        probe_family_template_id: str,
        probe_family_template_version: int,
        evidence_source: str,
        parameter_posterior: Mapping[str, Any],
        sample_size: int,
        effective_sample_size: float | None = None,
        grader_version: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        """Item-instance residual layer under the family posterior (§9.7)."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM probe_item_calibrations
                WHERE practice_item_id = ?
                  AND probe_family_template_id = ? AND probe_family_template_version = ?
                  AND COALESCE(grader_version, '') = COALESCE(?, '')
                  AND evidence_source = ?
                """,
                (
                    practice_item_id,
                    probe_family_template_id,
                    probe_family_template_version,
                    grader_version,
                    evidence_source,
                ),
            ).fetchone()
            if existing is not None:
                connection.execute(
                    """
                    UPDATE probe_item_calibrations
                    SET parameter_posterior_json = ?, sample_size = ?, effective_sample_size = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (_json(dict(parameter_posterior)), sample_size, effective_sample_size, now, existing["id"]),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO probe_item_calibrations(
                      id, practice_item_id, probe_family_template_id, probe_family_template_version,
                      grader_version, evidence_source,
                      parameter_posterior_json, sample_size, effective_sample_size, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_ulid(),
                        practice_item_id,
                        probe_family_template_id,
                        probe_family_template_version,
                        grader_version,
                        evidence_source,
                        _json(dict(parameter_posterior)),
                        sample_size,
                        effective_sample_size,
                        now,
                    ),
                )
            connection.commit()

    def probe_item_calibration(
        self,
        practice_item_id: str,
        probe_family_template_id: str,
        probe_family_template_version: int,
        *,
        evidence_source: str,
        grader_version: str | None = None,
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM probe_item_calibrations
                WHERE practice_item_id = ?
                  AND probe_family_template_id = ? AND probe_family_template_version = ?
                  AND COALESCE(grader_version, '') = COALESCE(?, '')
                  AND evidence_source = ?
                """,
                (
                    practice_item_id,
                    probe_family_template_id,
                    probe_family_template_version,
                    grader_version,
                    evidence_source,
                ),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["parameter_posterior"] = _loads(row["parameter_posterior_json"], {})
        return payload

    # --- Probe regrade checks (§7.6, Checkpoint 4.4) ------------------------------

    def insert_probe_regrade_check(
        self,
        *,
        attempt_id: str,
        probe_family_template_id: str,
        probe_family_template_version: int,
        original_outcome: str,
        regrade_outcome: str,
        grader_version: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        check_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO probe_regrade_checks(
                  id, attempt_id, probe_family_template_id, probe_family_template_version,
                  grader_version, original_outcome, regrade_outcome, agreement, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    check_id,
                    attempt_id,
                    probe_family_template_id,
                    probe_family_template_version,
                    grader_version,
                    original_outcome,
                    regrade_outcome,
                    1 if original_outcome == regrade_outcome else 0,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return check_id

    def probe_regrade_checks(
        self,
        probe_family_template_id: str | None = None,
        probe_family_template_version: int | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM probe_regrade_checks"
        clauses: list[str] = []
        params: list[Any] = []
        if probe_family_template_id is not None:
            clauses.append("probe_family_template_id = ?")
            params.append(probe_family_template_id)
        if probe_family_template_version is not None:
            clauses.append("probe_family_template_version = ?")
            params.append(probe_family_template_version)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [dict(row) for row in rows]

    # --- Probe generation needs (§10) --------------------------------------------

    def upsert_probe_generation_need(
        self,
        *,
        probe_episode_id: str,
        learning_object_id: str,
        target_key: str,
        missing_capability: str,
        clock: Clock | None = None,
    ) -> str:
        """Create one deduplicated pending generation need per episode target."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM probe_generation_needs WHERE probe_episode_id = ? AND target_key = ?",
                (probe_episode_id, target_key),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            need_id = new_ulid()
            connection.execute(
                """
                INSERT INTO probe_generation_needs(
                  id, probe_episode_id, learning_object_id, target_key,
                  missing_capability, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, 'pending', ?)
                """,
                (need_id, probe_episode_id, learning_object_id, target_key, missing_capability, now),
            )
            connection.commit()
        return need_id

    def probe_generation_needs(
        self,
        *,
        learning_object_id: str | None = None,
        probe_episode_id: str | None = None,
        status: str | None = None,
    ) -> list[ProbeGenerationNeedRecord]:
        clauses: list[str] = []
        parameters: list[Any] = []
        for column, value in (
            ("learning_object_id", learning_object_id),
            ("probe_episode_id", probe_episode_id),
            ("status", status),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                parameters.append(value)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM probe_generation_needs{where} ORDER BY created_at, id",
                parameters,
            ).fetchall()
        return [_probe_generation_need_record(row) for row in rows]

    def resolve_probe_generation_need(
        self, need_id: str, *, status: str = "resolved", clock: Clock | None = None
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                "UPDATE probe_generation_needs SET status = ?, resolved_at = ? WHERE id = ?",
                (status, now, need_id),
            )
            connection.commit()

    def update_probe_item_family_metadata(
        self,
        *,
        practice_item_id: str,
        instrument_card_id: str,
        instrument_card_version: int,
        instance_metadata: Mapping[str, Any],
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE probe_item_family_links
                SET instance_metadata_json = ?
                WHERE practice_item_id = ? AND instrument_card_id = ? AND instrument_card_version = ?
                """,
                (_json(dict(instance_metadata)), practice_item_id, instrument_card_id, instrument_card_version),
            )
            connection.commit()

    def probe_instance_ids_with_review_status(self, review_status: str) -> set[str]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT practice_item_id FROM probe_item_family_links
                WHERE json_extract(instance_metadata_json, '$.review_status') = ?
                """,
                (review_status,),
            ).fetchall()
        return {row["practice_item_id"] for row in rows}

    # --- Calibration sessions (§5.9) ---------------------------------------------

    def insert_probe_calibration_session(
        self,
        *,
        session_id: str,
        learning_object_ids: list[str],
        planned_episode_ids: list[str],
        time_budget_minutes: int,
        goal_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        calibration_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO probe_calibration_sessions(
                  id, session_id, goal_id, learning_object_ids_json,
                  planned_episode_ids_json, time_budget_minutes, status,
                  started_at, ended_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'active', ?, NULL, ?, ?)
                """,
                (
                    calibration_id,
                    session_id,
                    goal_id,
                    _json(list(learning_object_ids)),
                    _json(list(planned_episode_ids)),
                    time_budget_minutes,
                    now,
                    now,
                    now,
                ),
            )
            connection.commit()
        return calibration_id

    def probe_calibration_session(self, calibration_id: str) -> ProbeCalibrationSessionRecord | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM probe_calibration_sessions WHERE id = ?", (calibration_id,)
            ).fetchone()
        return _probe_calibration_session_record(row) if row is not None else None

    def active_probe_calibration_session(self, session_id: str) -> ProbeCalibrationSessionRecord | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM probe_calibration_sessions WHERE session_id = ? AND status = 'active'",
                (session_id,),
            ).fetchone()
        return _probe_calibration_session_record(row) if row is not None else None

    def end_probe_calibration_session(
        self, calibration_id: str, *, status: str, clock: Clock | None = None
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE probe_calibration_sessions
                SET status = ?, ended_at = COALESCE(ended_at, ?), updated_at = ?
                WHERE id = ? AND status = 'active'
                """,
                (status, now, now, calibration_id),
            )
            connection.commit()

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

    def record_decision_features(
        self,
        *,
        decision_id: str,
        decision_type: str,
        ability_vector: Mapping[str, Any],
        item_demand_vector: Mapping[str, Any] | None = None,
        context: Mapping[str, Any] | None = None,
        algorithm_version: str,
        clock: Clock | None = None,
    ) -> str:
        feature_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM decision_features
                WHERE decision_id = ? AND decision_type = ?
                """,
                (decision_id, decision_type),
            ).fetchone()
            if existing is not None:
                feature_id = existing["id"]
            connection.execute(
                """
                INSERT INTO decision_features(
                  id, decision_id, decision_type, ability_vector_json,
                  item_demand_vector_json, context_json, algorithm_version, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(decision_id, decision_type) DO UPDATE SET
                  ability_vector_json = excluded.ability_vector_json,
                  item_demand_vector_json = excluded.item_demand_vector_json,
                  context_json = excluded.context_json,
                  algorithm_version = excluded.algorithm_version,
                  created_at = excluded.created_at
                """,
                (
                    feature_id,
                    decision_id,
                    decision_type,
                    _json(dict(ability_vector)),
                    _json(dict(item_demand_vector)) if item_demand_vector is not None else None,
                    _json(dict(context or {})),
                    algorithm_version,
                    now,
                ),
            )
            connection.commit()
        return feature_id

    def decision_features(self, *, decision_id: str, decision_type: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM decision_features
                WHERE decision_id = ? AND decision_type = ?
                """,
                (decision_id, decision_type),
            ).fetchone()
        return _decode_decision_features(row) if row is not None else None

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
        probe_presentation: Mapping[str, Any] | None = None,
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
        candidate_ids: dict[str, str] = {}
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
                candidate_id = new_ulid()
                candidate_ids[practice_item_id] = candidate_id
                returned_rank = returned_rank_by_id.get(practice_item_id)
                connection.execute(
                    """
                    INSERT INTO scheduler_slate_candidates(
                      id, slate_id, practice_item_id, learning_object_id, rank,
                      returned_rank, was_returned, chosen_attempt_id, selected_mode,
                      priority, selection_reward, predicted_correctness,
                      legacy_priority, expected_information_gain, readiness_factor,
                      components_json, reward_debug_json, target_scope_json,
                      plain_english_json, selection_propensity, exploration_flag,
                      selection_temperature, algorithm_version, created_at, chosen_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, NULL)
                    """,
                    (
                        candidate_id,
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
                        explanation.get("selection_propensity"),
                        int(explanation.get("exploration_flag") or 0),
                        algorithm_version,
                        now,
                    ),
                )
            if probe_presentation is not None:
                presentation_values = dict(probe_presentation)
                practice_item_id = str(presentation_values["practice_item_id"])
                candidate_id = candidate_ids.get(practice_item_id)
                if candidate_id is None or returned_rank_by_id.get(practice_item_id) != 1:
                    raise ValueError(
                        "probe presentation must bind the top returned scheduler candidate"
                    )
                episode = connection.execute(
                    """
                    SELECT status, active_state_segment_id
                    FROM probe_episodes WHERE id = ?
                    """,
                    (presentation_values["probe_episode_id"],),
                ).fetchone()
                if (
                    episode is None
                    or episode["status"] != "in_progress"
                    or episode["active_state_segment_id"]
                    != presentation_values["state_segment_id"]
                ):
                    raise ValueError(
                        "probe presentation episode changed before scheduler commitment"
                    )
                # Do not replace an assignment that may already be displayed.
                # A later explicit abandonment/consumption boundary owns that
                # transition; queue refreshes are observational only.
                active = connection.execute(
                    """
                    SELECT id FROM probe_presentations
                    WHERE probe_episode_id = ? AND status IN ('selected', 'served')
                    LIMIT 1
                    """,
                    (presentation_values["probe_episode_id"],),
                ).fetchone()
                if active is None:
                    presentation_values["scheduler_candidate_id"] = candidate_id
                    _insert_probe_presentation_row(
                        connection,
                        presentation_id=new_ulid(),
                        now=now,
                        values=presentation_values,
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

    def session_day_streak(self, *, clock: Clock | None = None) -> dict[str, Any]:
        """Consecutive-day study streak derived from session start timestamps.

        Days are counted in the machine's local timezone. ``current`` is the run
        of consecutive days ending today (or yesterday, if today has no session
        yet but the streak is still alive). ``active_today`` reports whether a
        session was already started today, and ``longest`` is the best run ever.
        """
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT started_at FROM sessions WHERE started_at IS NOT NULL"
            ).fetchall()

        days: set[date] = set()
        for row in rows:
            started = parse_utc(row["started_at"])
            if started is not None:
                days.add(started.astimezone().date())

        if not days:
            return {"current": 0, "active_today": False, "longest": 0}

        today = (clock or SystemClock()).now().astimezone().date()
        active_today = today in days

        anchor = today if active_today else today - timedelta(days=1)
        current = 0
        cursor = anchor
        while cursor in days:
            current += 1
            cursor -= timedelta(days=1)

        ordered = sorted(days)
        longest = 1
        run = 1
        for previous, day in zip(ordered, ordered[1:]):
            run = run + 1 if (day - previous).days == 1 else 1
            longest = max(longest, run)

        return {"current": current, "active_today": active_today, "longest": longest}

    def daily_attempt_counts(
        self, *, days: int = 14, clock: Clock | None = None
    ) -> dict[date, int]:
        """Attempts per local calendar day for the trailing ``days`` window.

        Zero-filled: every day in the window is present (today inclusive), so
        means over the values reflect idle days. Local timezone, matching
        ``session_day_streak``.
        """

        days = max(days, 1)
        now = (clock or SystemClock()).now()
        today = now.astimezone().date()
        # Over-fetch by one UTC day so local-date bucketing never clips the edge.
        cutoff_iso = (now.astimezone(UTC) - timedelta(days=days + 1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT created_at FROM practice_attempts WHERE created_at >= ?",
                (cutoff_iso,),
            ).fetchall()
        window_start = today - timedelta(days=days - 1)
        counts: dict[date, int] = {
            window_start + timedelta(days=offset): 0 for offset in range(days)
        }
        for row in rows:
            created = parse_utc(row["created_at"])
            if created is None:
                continue
            day = created.astimezone().date()
            if day in counts:
                counts[day] += 1
        return counts

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
                      source_ref_ids_json, audit_json, edited_payload_json,
                      decision, validation_status, validation_errors_json,
                      applied_change_batch_id, decided_at, decided_by,
                      created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        _json(item.get("source_ref_ids", [])),
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

    def update_proposal_item_audit(
        self,
        item_id: str,
        *,
        audit: Mapping[str, Any],
        validation_status: str,
        validation_errors: list[str],
        clock: Clock | None = None,
    ) -> bool:
        """Replace a pending proposal item's audit and its derived validation."""
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE proposed_patch_items
                SET audit_json = ?, validation_status = ?,
                    validation_errors_json = ?, updated_at = ?
                WHERE id = ? AND decision = 'pending'
                """,
                (_json(audit), validation_status, _json(validation_errors), now, item_id),
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
            ("facet_uncertainty", "facet_uncertainty", "id", _facet_uncertainty_state),
            ("learner_theta", "learner_theta", "id", dict),
            ("learner_claim", "learner_claims", "id", dict),
            ("lo_probe_state", "lo_probe_state", "learning_object_id", _probe_state_record),
            ("hypothesis_set", "hypothesis_sets", "id", _decode_hypothesis_set),
            ("learner_state_belief", "learner_state_beliefs", "id", dict),
            ("intervention_need", "intervention_needs", "id", _decode_intervention_need),
            ("elicitation_event", "elicitation_events", "id", _decode_elicitation_event),
            ("decision_feature", "decision_features", "id", _decode_decision_features),
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
              created_at, updated_at, session_id, scheduler_slate_id, scheduler_candidate_id,
              primed, probe_presentation_id, answer_confidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                1 if attempt.get("primed") else 0,
                attempt.get("probe_presentation_id"),
                attempt.get("answer_confidence"),
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
              superseded_at, superseded_by_evidence_id, learner_confidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            ),
        )

    def _insert_error_event(self, connection: sqlite3.Connection, event: Mapping[str, Any]) -> None:
        connection.execute(
            """
            INSERT INTO error_events(
              id, attempt_id, learning_object_id, error_type, severity,
              is_misconception, repair_plan_json, status, created_at, updated_at,
              misconception_id, misconception_statement, misconception_consistent_answer
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                event.get("misconception_id"),
                event.get("misconception_statement"),
                event.get("misconception_consistent_answer"),
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

    def _upsert_facet_uncertainty_state(self, connection: sqlite3.Connection, state: Mapping[str, Any]) -> None:
        marginal = {
            str(label): float(probability)
            for label, probability in dict(state.get("hypothesis_marginal") or {}).items()
        }
        existing = connection.execute(
            """
            SELECT id, created_at, opened_by_attempt_id, opened_reason
            FROM facet_uncertainty
            WHERE learning_object_id = ? AND facet_id = ?
            """,
            (state["learning_object_id"], state["facet_id"]),
        ).fetchone()
        state_id = str(state.get("id") or (existing["id"] if existing is not None else new_ulid()))
        opened_by_attempt_id = str(
            state.get("opened_by_attempt_id")
            or (existing["opened_by_attempt_id"] if existing is not None else "")
        )
        opened_reason = str(
            state.get("opened_reason")
            or (existing["opened_reason"] if existing is not None else "low_facet_outcome")
        )
        if existing is not None:
            connection.execute(
                """
                UPDATE facet_uncertainty
                SET hypothesis_marginal = ?, uncertainty = ?, status = ?,
                    opened_by_attempt_id = ?, opened_reason = ?,
                    last_evidence_at = ?, algorithm_version = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    _json(marginal),
                    state["uncertainty"],
                    state["status"],
                    opened_by_attempt_id,
                    opened_reason,
                    state.get("last_evidence_at"),
                    state["algorithm_version"],
                    state["updated_at"],
                    state_id,
                ),
            )
            return
        connection.execute(
            """
            INSERT INTO facet_uncertainty(
              id, learning_object_id, facet_id, hypothesis_marginal, uncertainty,
              status, opened_by_attempt_id, opened_reason, last_evidence_at,
              algorithm_version, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                state_id,
                state["learning_object_id"],
                state["facet_id"],
                _json(marginal),
                state["uncertainty"],
                state["status"],
                opened_by_attempt_id,
                opened_reason,
                state.get("last_evidence_at"),
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
                  attempt_id = excluded.attempt_id,
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

    def exam_answers(self, session_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM exam_answers WHERE session_id = ? ORDER BY answered_at, id",
                (session_id,),
            ).fetchall()
        return [_decode_exam_answer(row) for row in rows]

    # ------------------------------------------------------------------ #
    # Source layer v2 (spec_source_ingestion_v2 §2 / migration 032).
    # ------------------------------------------------------------------ #

    def upsert_source_artifact(
        self,
        *,
        id: str,
        acquisition_kind: str,
        canonical_uri: str | None = None,
        work_id: str | None = None,
        current_revision_id: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_artifacts(
                  id, acquisition_kind, canonical_uri, work_id,
                  current_revision_id, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  acquisition_kind = excluded.acquisition_kind,
                  canonical_uri = excluded.canonical_uri,
                  work_id = excluded.work_id,
                  current_revision_id = COALESCE(excluded.current_revision_id, source_artifacts.current_revision_id),
                  updated_at = excluded.updated_at
                """,
                (id, acquisition_kind, canonical_uri, work_id, current_revision_id, now, now),
            )
            connection.commit()

    def get_source_artifact(self, source_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_artifacts WHERE id = ?", (source_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def source_artifact_by_uri(self, acquisition_kind: str, canonical_uri: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_artifacts WHERE acquisition_kind = ? AND canonical_uri = ?",
                (acquisition_kind, canonical_uri),
            ).fetchone()
        return dict(row) if row is not None else None

    def set_source_current_revision(
        self, source_id: str, revision_id: str, *, clock: Clock | None = None
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE source_artifacts SET current_revision_id = ?, updated_at = ? WHERE id = ?",
                (revision_id, utc_now_iso(clock), source_id),
            )
            connection.commit()

    def insert_source_revision(
        self,
        *,
        id: str,
        source_id: str,
        asset_hash: str,
        note_id: str | None = None,
        original_uri: str | None = None,
        retrieved_at: str | None = None,
        supersedes_revision_id: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_revisions(
                  id, source_id, asset_hash, note_id, original_uri,
                  retrieved_at, supersedes_revision_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    id,
                    source_id,
                    asset_hash,
                    note_id,
                    original_uri,
                    retrieved_at,
                    supersedes_revision_id,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()

    def get_source_revision(self, revision_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_revisions WHERE id = ?", (revision_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def source_revision_by_asset_hash(self, source_id: str, asset_hash: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_revisions WHERE source_id = ? AND asset_hash = ?",
                (source_id, asset_hash),
            ).fetchone()
        return dict(row) if row is not None else None

    def source_revisions_for(self, source_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_revisions WHERE source_id = ? ORDER BY created_at, id",
                (source_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def all_source_artifacts(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_artifacts ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def extraction_runs_for_revision(self, revision_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_extraction_runs WHERE revision_id = ? ORDER BY created_at, id",
                (revision_id,),
            ).fetchall()
        return [_decode_extraction_run(row) for row in rows]

    def document_ir_counts(self, extraction_id: str) -> dict[str, int]:
        with self.connection() as connection:
            units = connection.execute(
                "SELECT COUNT(*) AS n FROM source_document_units WHERE extraction_id = ?",
                (extraction_id,),
            ).fetchone()["n"]
            blocks = connection.execute(
                "SELECT COUNT(*) AS n FROM source_document_blocks WHERE extraction_id = ?",
                (extraction_id,),
            ).fetchone()["n"]
        return {"unit_count": units, "block_count": blocks}

    def insert_extraction_run(
        self,
        *,
        id: str,
        revision_id: str,
        extractor: str,
        extractor_version: str,
        extraction_request_hash: str,
        ir_schema_version: str,
        model_versions: Mapping[str, str] | None = None,
        config: Mapping[str, Any] | None = None,
        page_selection: Iterable[int] | None = None,
        parent_extraction_id: str | None = None,
        status: str = "queued",
        clock: Clock | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_extraction_runs(
                  id, revision_id, parent_extraction_id, extractor, extractor_version,
                  model_versions_json, config_json, page_selection_json, ir_schema_version,
                  extraction_request_hash, extraction_result_hash, status,
                  created_at, completed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, NULL)
                """,
                (
                    id,
                    revision_id,
                    parent_extraction_id,
                    extractor,
                    extractor_version,
                    _json(dict(sorted((model_versions or {}).items()))),
                    _json(dict(config or {})),
                    _json(sorted(page_selection) if page_selection is not None else None),
                    ir_schema_version,
                    extraction_request_hash,
                    status,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()

    def get_extraction_run(self, extraction_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_extraction_runs WHERE id = ?", (extraction_id,)
            ).fetchone()
        return _decode_extraction_run(row) if row is not None else None

    def extraction_run_by_request_hash(
        self, revision_id: str, extraction_request_hash: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_extraction_runs WHERE revision_id = ? AND extraction_request_hash = ?",
                (revision_id, extraction_request_hash),
            ).fetchone()
        return _decode_extraction_run(row) if row is not None else None

    def complete_extraction_run(
        self, extraction_id: str, *, extraction_result_hash: str, status: str = "completed", clock: Clock | None = None
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE source_extraction_runs
                   SET extraction_result_hash = ?, status = ?, completed_at = ?
                 WHERE id = ?
                """,
                (extraction_result_hash, status, utc_now_iso(clock), extraction_id),
            )
            connection.commit()

    def persist_document_ir(self, extraction_id: str, ir: DocumentIR) -> None:
        with self.connection() as connection:
            for unit in ir.units:
                connection.execute(
                    """
                    INSERT INTO source_document_units(
                      extraction_id, unit_id, parent_unit_id, label, ordinal,
                      locator_json, semantic_hash, page_start, page_end, span_ids_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        extraction_id,
                        unit.unit_id,
                        unit.parent_unit_id,
                        unit.label,
                        unit.ordinal,
                        _json(unit.locator),
                        unit.semantic_hash,
                        unit.page_start,
                        unit.page_end,
                        _json(unit.span_ids),
                    ),
                )
            for block in ir.blocks:
                connection.execute(
                    """
                    INSERT INTO source_document_blocks(
                      extraction_id, span_id, extractor_block_id, block_type, role_hint,
                      page, bbox_json, polygon_json, section_path_json, text,
                      content_hash, asset_ids_json, ordinal
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        extraction_id,
                        block.span_id,
                        block.extractor_block_id,
                        block.block_type,
                        block.role_hint,
                        block.page,
                        _json(block.bbox),
                        _json(block.polygon),
                        _json(block.section_path),
                        block.text,
                        block.content_hash,
                        _json(block.asset_ids),
                        block.ordinal,
                    ),
                )
            for asset in ir.assets:
                connection.execute(
                    """
                    INSERT INTO source_document_assets(
                      id, extraction_id, media_type, content_hash, path,
                      caption, page, geometry_json, neighboring_span_ids_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        asset.id,
                        extraction_id,
                        asset.media_type,
                        asset.content_hash,
                        asset.path,
                        asset.caption,
                        asset.page,
                        _json(asset.geometry),
                        _json(asset.neighboring_span_ids),
                    ),
                )
            connection.commit()

    def load_document_ir(self, extraction_id: str) -> DocumentIR | None:
        run = self.get_extraction_run(extraction_id)
        if run is None:
            return None
        with self.connection() as connection:
            unit_rows = connection.execute(
                "SELECT * FROM source_document_units WHERE extraction_id = ? ORDER BY ordinal",
                (extraction_id,),
            ).fetchall()
            block_rows = connection.execute(
                "SELECT * FROM source_document_blocks WHERE extraction_id = ? ORDER BY ordinal",
                (extraction_id,),
            ).fetchall()
            asset_rows = connection.execute(
                "SELECT * FROM source_document_assets WHERE extraction_id = ? ORDER BY id",
                (extraction_id,),
            ).fetchall()
        return DocumentIR(
            ir_schema_version=run["ir_schema_version"],
            extractor=run["extractor"],
            extractor_version=run["extractor_version"],
            blocks=[_decode_document_block(row) for row in block_rows],
            units=[_decode_document_unit(row) for row in unit_rows],
            assets=[_decode_document_asset(row) for row in asset_rows],
        )

    def insert_span_reanchor(
        self,
        *,
        from_extraction_id: str,
        from_span_id: str,
        to_extraction_id: str,
        to_span_id: str,
        match_kind: str,
        confidence: float | None = None,
        clock: Clock | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_span_reanchors(
                  from_extraction_id, from_span_id, to_extraction_id, to_span_id,
                  match_kind, confidence, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    from_extraction_id,
                    from_span_id,
                    to_extraction_id,
                    to_span_id,
                    match_kind,
                    confidence,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()

    def span_reanchors_from(self, from_extraction_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_span_reanchors WHERE from_extraction_id = ? ORDER BY from_span_id",
                (from_extraction_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def backfill_locator_schemes(
        self, locators: Iterable[str], *, clock: Clock | None = None
    ) -> dict[str, str]:
        """Shape-detect and stamp a declared scheme onto each existing ref (§2.4).

        Already-declared refs are never re-detected/converted. Returns the
        locator -> scheme map for every ref with a recognized shape.
        """

        now = utc_now_iso(clock)
        stamped: dict[str, str] = {}
        with self.connection() as connection:
            for locator in locators:
                existing = connection.execute(
                    "SELECT scheme FROM source_locator_schemes WHERE locator = ?", (locator,)
                ).fetchone()
                if existing is not None:
                    stamped[locator] = existing["scheme"]
                    continue
                scheme = detect_locator_scheme(locator)
                if scheme is None:
                    continue
                connection.execute(
                    "INSERT INTO source_locator_schemes(locator, scheme, detected_at) VALUES (?, ?, ?)",
                    (locator, scheme, now),
                )
                stamped[locator] = scheme
            connection.commit()
        return stamped

    def locator_scheme(self, locator: str) -> str | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT scheme FROM source_locator_schemes WHERE locator = ?", (locator,)
            ).fetchone()
        if row is not None:
            return row["scheme"]
        return detect_locator_scheme(locator)

    # ------------------------------------------------------------------
    # Durable ingest batches/jobs (spec_source_ingestion_v2 §6.2)
    # ------------------------------------------------------------------

    def insert_ingest_batch(
        self,
        *,
        id: str,
        workflow_type: str,
        subject_id: str | None = None,
        source_set_id: str | None = None,
        payload_schema_version: int = 1,
        status: str = "queued",
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO ingest_batches(
                  id, workflow_type, payload_schema_version, subject_id,
                  source_set_id, status, created_at, cancel_requested
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (id, workflow_type, payload_schema_version, subject_id, source_set_id, status, now),
            )
            connection.commit()

    def get_ingest_batch(self, batch_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM ingest_batches WHERE id = ?", (batch_id,)
            ).fetchone()
        return _decode_ingest_batch(row) if row is not None else None

    def list_ingest_batches(self, limit: int | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM ingest_batches ORDER BY created_at DESC, id DESC"
        params: tuple[Any, ...] = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [_decode_ingest_batch(row) for row in rows]

    def update_ingest_batch_status(
        self,
        batch_id: str,
        status: str,
        *,
        mark_started: bool = False,
        mark_finished: bool = False,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE ingest_batches
                   SET status = ?,
                       started_at = CASE WHEN ? AND started_at IS NULL THEN ? ELSE started_at END,
                       finished_at = CASE WHEN ? THEN ? ELSE finished_at END
                 WHERE id = ?
                """,
                (status, 1 if mark_started else 0, now, 1 if mark_finished else 0, now, batch_id),
            )
            connection.commit()

    def request_ingest_batch_cancel(self, batch_id: str) -> None:
        """Flag the batch and every not-yet-terminal job for cancellation."""

        with self.connection() as connection:
            connection.execute(
                "UPDATE ingest_batches SET cancel_requested = 1 WHERE id = ?", (batch_id,)
            )
            connection.execute(
                """
                UPDATE ingest_jobs
                   SET cancel_requested = 1
                 WHERE batch_id = ?
                   AND status IN ('queued', 'running', 'waiting_for_input', 'blocked')
                """,
                (batch_id,),
            )
            connection.commit()

    def insert_ingest_job(
        self,
        *,
        id: str,
        batch_id: str,
        ordinal: int,
        job_type: str,
        payload: Mapping[str, Any] | None = None,
        payload_schema_version: int = 1,
        clock: Clock | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO ingest_jobs(
                  id, batch_id, ordinal, job_type, payload_schema_version,
                  payload_json, status, phase, message, attempt_count,
                  cancel_requested, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'queued', 'queued', 'Waiting to start', 0, 0, ?)
                """,
                (
                    id,
                    batch_id,
                    ordinal,
                    job_type,
                    payload_schema_version,
                    _json(dict(payload)) if payload is not None else None,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()

    def add_ingest_job_dependency(self, job_id: str, depends_on_job_id: str) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO ingest_job_dependencies(job_id, depends_on_job_id)
                VALUES (?, ?)
                """,
                (job_id, depends_on_job_id),
            )
            connection.commit()

    def get_ingest_job(self, job_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM ingest_jobs WHERE id = ?", (job_id,)
            ).fetchone()
        return _decode_ingest_job(row) if row is not None else None

    def ingest_jobs_for_batch(self, batch_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM ingest_jobs WHERE batch_id = ? ORDER BY ordinal, id",
                (batch_id,),
            ).fetchall()
        return [_decode_ingest_job(row) for row in rows]

    def ingest_job_dependency_ids(self, job_id: str) -> list[str]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT depends_on_job_id FROM ingest_job_dependencies WHERE job_id = ? ORDER BY depends_on_job_id",
                (job_id,),
            ).fetchall()
        return [row["depends_on_job_id"] for row in rows]

    def ingest_job_dependents(self, job_id: str) -> list[str]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT job_id FROM ingest_job_dependencies WHERE depends_on_job_id = ? ORDER BY job_id",
                (job_id,),
            ).fetchall()
        return [row["job_id"] for row in rows]

    def claim_next_ingest_job(
        self, *, worker_id: str, now_iso: str, lease_cutoff_iso: str
    ) -> dict[str, Any] | None:
        """Atomically claim the next eligible queued job for ``worker_id``.

        Returns None when another worker already holds a live running lease
        (exactly one worker drains at a time — no competing vault writes) or when
        no queued job has all of its dependencies completed. A ``running`` job
        whose heartbeat predates ``lease_cutoff_iso`` is treated as dead and does
        not block the claim; startup recovery converts it to failed(interrupted).
        """

        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("BEGIN IMMEDIATE")
            live = connection.execute(
                """
                SELECT 1 FROM ingest_jobs
                 WHERE status = 'running'
                   AND heartbeat_at IS NOT NULL
                   AND heartbeat_at >= ?
                 LIMIT 1
                """,
                (lease_cutoff_iso,),
            ).fetchone()
            if live is not None:
                connection.execute("ROLLBACK")
                return None
            candidate = connection.execute(
                """
                SELECT j.* FROM ingest_jobs j
                 JOIN ingest_batches b ON b.id = j.batch_id
                 WHERE j.status = 'queued'
                   AND b.cancel_requested = 0
                   AND NOT EXISTS (
                     SELECT 1 FROM ingest_job_dependencies d
                      JOIN ingest_jobs dep ON dep.id = d.depends_on_job_id
                      WHERE d.job_id = j.id AND dep.status != 'completed'
                   )
                 ORDER BY b.created_at, j.ordinal, j.id
                 LIMIT 1
                """
            ).fetchone()
            if candidate is None:
                connection.execute("ROLLBACK")
                return None
            connection.execute(
                """
                UPDATE ingest_jobs
                   SET status = 'running',
                       worker_id = ?,
                       heartbeat_at = ?,
                       started_at = COALESCE(started_at, ?),
                       attempt_count = attempt_count + 1,
                       phase = COALESCE(phase, 'acquired'),
                       error_json = NULL
                 WHERE id = ? AND status = 'queued'
                """,
                (worker_id, now_iso, now_iso, candidate["id"]),
            )
            claimed = connection.execute(
                "SELECT * FROM ingest_jobs WHERE id = ?", (candidate["id"],)
            ).fetchone()
            connection.execute("COMMIT")
            return _decode_ingest_job(claimed) if claimed is not None else None
        finally:
            connection.close()

    def heartbeat_ingest_job(
        self,
        job_id: str,
        *,
        worker_id: str,
        phase: str | None = None,
        message: str | None = None,
        current_window: int | None = None,
        total_windows: int | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE ingest_jobs
                   SET heartbeat_at = ?,
                       phase = COALESCE(?, phase),
                       message = COALESCE(?, message),
                       current_window = ?,
                       total_windows = ?
                 WHERE id = ? AND worker_id = ?
                """,
                (now, phase, message, current_window, total_windows, job_id, worker_id),
            )
            connection.commit()

    def finish_ingest_job(
        self,
        job_id: str,
        *,
        status: str,
        phase: str | None = None,
        message: str | None = None,
        result: Mapping[str, Any] | None = None,
        error: Mapping[str, Any] | None = None,
        usage: Mapping[str, Any] | None = None,
        release_lease: bool = True,
        clear_finished: bool = False,
        current_window: int | None = None,
        total_windows: int | None = None,
        clock: Clock | None = None,
    ) -> None:
        """Move a job to a new state and (optionally) release its lease.

        ``waiting_for_input`` and ``queued`` (resume/requeue) release the lease
        but leave ``finished_at`` NULL (``clear_finished=True``); terminal states
        stamp ``finished_at``.
        """

        now = utc_now_iso(clock)
        finished_at = None if clear_finished else now
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE ingest_jobs
                   SET status = ?,
                       phase = COALESCE(?, phase),
                       message = COALESCE(?, message),
                       result_json = COALESCE(?, result_json),
                       error_json = ?,
                       usage_json = COALESCE(?, usage_json),
                       current_window = COALESCE(?, current_window),
                       total_windows = COALESCE(?, total_windows),
                       worker_id = CASE WHEN ? THEN NULL ELSE worker_id END,
                       heartbeat_at = CASE WHEN ? THEN NULL ELSE heartbeat_at END,
                       finished_at = ?
                 WHERE id = ?
                """,
                (
                    status,
                    phase,
                    message,
                    _json(dict(result)) if result is not None else None,
                    _json(dict(error)) if error is not None else None,
                    _json(dict(usage)) if usage is not None else None,
                    current_window,
                    total_windows,
                    1 if release_lease else 0,
                    1 if release_lease else 0,
                    finished_at,
                    job_id,
                ),
            )
            connection.commit()

    def requeue_ingest_job(
        self, job_id: str, *, message: str = "Waiting to start", clock: Clock | None = None
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE ingest_jobs
                   SET status = 'queued', phase = 'queued', message = ?,
                       worker_id = NULL, heartbeat_at = NULL,
                       error_json = NULL, finished_at = NULL,
                       cancel_requested = 0
                 WHERE id = ?
                """,
                (message, job_id),
            )
            connection.commit()

    def set_ingest_job_cancel_requested(self, job_id: str) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE ingest_jobs SET cancel_requested = 1 WHERE id = ?", (job_id,)
            )
            connection.commit()

    def ingest_jobs_by_types(
        self, job_types: Sequence[str], *, limit: int | None = None
    ) -> list[dict[str, Any]]:
        placeholders = ",".join("?" for _ in job_types)
        query = (
            f"SELECT * FROM ingest_jobs WHERE job_type IN ({placeholders}) "
            "ORDER BY created_at DESC, id DESC"
        )
        params: list[Any] = list(job_types)
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [_decode_ingest_job(row) for row in rows]

    def expired_running_ingest_jobs(self, lease_cutoff_iso: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM ingest_jobs
                 WHERE status = 'running'
                   AND (heartbeat_at IS NULL OR heartbeat_at < ?)
                 ORDER BY ordinal, id
                """,
                (lease_cutoff_iso,),
            ).fetchall()
        return [_decode_ingest_job(row) for row in rows]


def _decode_ingest_batch(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["cancel_requested"] = bool(data.get("cancel_requested"))
    return data


def _decode_ingest_job(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["cancel_requested"] = bool(data.get("cancel_requested"))
    for key in ("payload", "result", "error", "usage"):
        raw = data.pop(f"{key}_json", None)
        data[key] = json.loads(raw) if raw else None
    return data


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


def _facet_uncertainty_state(row: sqlite3.Row) -> FacetUncertaintyState:
    return FacetUncertaintyState(
        id=row["id"],
        learning_object_id=row["learning_object_id"],
        facet_id=row["facet_id"],
        hypothesis_marginal={
            str(label): float(probability)
            for label, probability in _loads(row["hypothesis_marginal"], {}).items()
        },
        uncertainty=float(row["uncertainty"]),
        status=row["status"],
        opened_by_attempt_id=row["opened_by_attempt_id"],
        opened_reason=row["opened_reason"],
        last_evidence_at=row["last_evidence_at"],
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


def _decode_fitted_parameters(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["params"] = _loads(payload.pop("params_json"), {})
    payload["metrics"] = _loads(payload.pop("metrics_json"), None)
    payload["active"] = bool(payload["active"])
    return payload


def _decode_item_parameter_state(row: sqlite3.Row) -> ItemParameterState:
    return ItemParameterState(
        practice_item_id=row["practice_item_id"],
        b_mean=row["b_mean"],
        b_var=row["b_var"],
        evidence_count=row["evidence_count"],
        algorithm_version=row["algorithm_version"],
        updated_at=row["updated_at"],
    )


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


def _probe_episode_record(row: sqlite3.Row) -> ProbeEpisodeRecord:
    return ProbeEpisodeRecord(
        id=row["id"],
        learning_object_id=row["learning_object_id"],
        status=row["status"],
        trigger=row["trigger"],
        hypothesis_set_id=row["hypothesis_set_id"],
        active_state_segment_id=row["active_state_segment_id"],
        target_decision=_loads(row["target_decision_json"], None),
        required_facets=_loads(row["required_facets_json"], []),
        minimum_independent_observations=row["minimum_independent_observations"],
        maximum_observations=row["maximum_observations"],
        entered_at=row["entered_at"],
        completed_at=row["completed_at"],
        completion_reason=row["completion_reason"],
        algorithm_version=row["algorithm_version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _probe_presentation_record(row: sqlite3.Row) -> ProbePresentationRecord:
    return ProbePresentationRecord(
        id=row["id"],
        probe_episode_id=row["probe_episode_id"],
        practice_item_id=row["practice_item_id"],
        scheduler_candidate_id=row["scheduler_candidate_id"],
        state_segment_id=row["state_segment_id"],
        probe_family_template_id=row["probe_family_template_id"],
        probe_family_template_version=row["probe_family_template_version"],
        instrument_card_id=row["instrument_card_id"],
        instrument_card_version=row["instrument_card_version"],
        instrument_card_snapshot=_loads(row["instrument_card_snapshot_json"], None),
        target_hypothesis_pairs=_loads(row["target_hypothesis_pairs_json"], []),
        target_facets=_loads(row["target_facets_json"], []),
        posterior_at_selection=_loads(row["posterior_at_selection_json"], {}),
        entropy_at_selection=row["entropy_at_selection"],
        expected_information_gain=row["expected_information_gain"],
        selection_policy_version=row["selection_policy_version"],
        selection_components=_loads(
            row["selection_components_json"] if "selection_components_json" in row.keys() else None, {}
        ),
        status=row["status"],
        end_reason=row["end_reason"],
        served_at=row["served_at"],
        submitted_at=row["submitted_at"],
        expires_at=row["expires_at"],
        ended_at=row["ended_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _probe_observation_record(row: sqlite3.Row) -> ProbeObservationRecord:
    return ProbeObservationRecord(
        id=row["id"],
        attempt_id=row["attempt_id"],
        posterior_before=_loads(row["posterior_before_json"], {}),
        posterior_after=_loads(row["posterior_after_json"], {}),
        entropy_before=row["entropy_before"],
        entropy_after=row["entropy_after"],
        realized_information_gain=row["realized_information_gain"],
        independent_evidence_discount=row["independent_evidence_discount"],
        contamination=_loads(row["contamination_json"], None),
        grader_channel=_loads(row["grader_channel_json"], None),
        updates_belief=bool(row["updates_belief"]),
        eligible_for_completion=bool(row["eligible_for_completion"]),
        created_at=row["created_at"],
        features=_loads(row["features_json"], None) if "features_json" in row.keys() else None,
    )


def _probe_state_segment_record(row: sqlite3.Row) -> ProbeStateSegmentRecord:
    return ProbeStateSegmentRecord(
        id=row["id"],
        learning_object_id=row["learning_object_id"],
        probe_episode_id=row["probe_episode_id"],
        sequence=row["sequence"],
        reason=row["reason"],
        opened_by_attempt_id=row["opened_by_attempt_id"],
        created_at=row["created_at"],
    )


def _probe_family_template_record(row: sqlite3.Row) -> ProbeFamilyTemplateRecord:
    return ProbeFamilyTemplateRecord(
        id=row["id"],
        version=row["version"],
        status=row["status"],
        template=_loads(row["template_json"], {}),
        schema_hash=row["schema_hash"],
        created_at=row["created_at"],
        retired_at=row["retired_at"],
    )


def _probe_instrument_card_record(row: sqlite3.Row) -> ProbeInstrumentCardRecord:
    return ProbeInstrumentCardRecord(
        id=row["id"],
        version=row["version"],
        probe_family_template_id=row["probe_family_template_id"],
        probe_family_template_version=row["probe_family_template_version"],
        learning_object_id=row["learning_object_id"],
        hypothesis_scope=_loads(row["hypothesis_scope_json"], []),
        card=_loads(row["card_json"], {}),
        compiled_likelihood_hash=row["compiled_likelihood_hash"],
        created_at=row["created_at"],
        retired_at=row["retired_at"],
    )


def _probe_item_family_link_record(row: sqlite3.Row) -> ProbeItemFamilyLinkRecord:
    return ProbeItemFamilyLinkRecord(
        practice_item_id=row["practice_item_id"],
        instrument_card_id=row["instrument_card_id"],
        instrument_card_version=row["instrument_card_version"],
        generator_id=row["generator_id"],
        generator_version=row["generator_version"],
        generation_seed=row["generation_seed"],
        instance_metadata=_loads(row["instance_metadata_json"], None),
        created_at=row["created_at"],
    )


def _probe_generation_need_record(row: sqlite3.Row) -> ProbeGenerationNeedRecord:
    return ProbeGenerationNeedRecord(
        id=row["id"],
        probe_episode_id=row["probe_episode_id"],
        learning_object_id=row["learning_object_id"],
        target_key=row["target_key"],
        missing_capability=row["missing_capability"],
        status=row["status"],
        created_at=row["created_at"],
        resolved_at=row["resolved_at"],
    )


def _probe_calibration_session_record(row: sqlite3.Row) -> ProbeCalibrationSessionRecord:
    return ProbeCalibrationSessionRecord(
        id=row["id"],
        session_id=row["session_id"],
        goal_id=row["goal_id"],
        learning_object_ids=_loads(row["learning_object_ids_json"], []),
        planned_episode_ids=_loads(row["planned_episode_ids_json"], []),
        time_budget_minutes=row["time_budget_minutes"],
        status=row["status"],
        started_at=row["started_at"],
        ended_at=row["ended_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _decode_question_event(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["facets"] = _loads(payload.pop("facets_json"), [])
    payload["hint_equivalent"] = bool(payload["hint_equivalent"])
    payload["leak_suspected"] = bool(payload["leak_suspected"])
    # saved_note_id (migration 027) is a plain column and rides along in
    # dict(row); older DBs predating the transcript join surface it as None.
    payload.setdefault("saved_note_id", None)
    # §13.4 context columns (migration 030) ride along in dict(row); default
    # them for rows read before the migration applied.
    payload.setdefault("signal_channel", None)
    if payload.get("direct_explanation_request") is not None:
        payload["direct_explanation_request"] = bool(payload["direct_explanation_request"])
    return payload


def _decode_question_promotion(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["attributed_facets"] = _loads(payload.pop("attributed_facets_json"), [])
    attempted = payload.get("attempted_in_thread")
    payload["attempted_in_thread"] = None if attempted is None else bool(attempted)
    return payload


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


def _decode_decision_features(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["ability_vector"] = _loads(payload.pop("ability_vector_json"), {})
    payload["item_demand_vector"] = _loads(payload.pop("item_demand_vector_json"), None)
    payload["context"] = _loads(payload.pop("context_json"), {})
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
    payload["diagnostic_focus"] = _loads(payload.pop("diagnostic_focus_json", None), None)
    return payload


def _active_error(row: sqlite3.Row) -> ActiveErrorEvent:
    keys = row.keys()
    return ActiveErrorEvent(
        id=row["id"],
        learning_object_id=row["learning_object_id"],
        error_type=row["error_type"],
        severity=row["severity"],
        is_misconception=bool(row["is_misconception"]),
        created_at=row["created_at"],
        misconception_id=row["misconception_id"] if "misconception_id" in keys else None,
        misconception_statement=row["misconception_statement"] if "misconception_statement" in keys else None,
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
        learner_confidence=row["learner_confidence"] if "learner_confidence" in row.keys() else None,
        created_at=row["created_at"],
        superseded_at=row["superseded_at"],
    )


def _decode_attempt(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["evidence_facets"] = _loads(payload.pop("evidence_facets_json"), [])
    payload["evidence_weights"] = _loads(payload.pop("evidence_weights_json"), {})
    payload["manual_review"] = bool(payload["manual_review"])
    payload["primed"] = bool(payload.get("primed", 0))
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


def _decode_misconception(row: sqlite3.Row) -> MisconceptionRecord:
    return MisconceptionRecord(
        id=row["id"],
        learning_object_id=row["learning_object_id"],
        concept_id=row["concept_id"],
        statement=row["statement"],
        signature=row["signature"],
        facet_ids=_loads(row["facet_ids_json"], []),
        severity=row["severity"],
        status=row["status"],
        source_error_event_ids=_loads(row["source_error_event_ids_json"], []),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        resolved_at=row["resolved_at"],
    )


def _decode_discrimination(row: sqlite3.Row) -> ItemMisconceptionDiscrimination:
    return ItemMisconceptionDiscrimination(
        practice_item_id=row["practice_item_id"],
        misconception_id=row["misconception_id"],
        sensitivity_alpha=row["sensitivity_alpha"],
        sensitivity_beta=row["sensitivity_beta"],
        specificity_alpha=row["specificity_alpha"],
        specificity_beta=row["specificity_beta"],
        n_planted_trials=row["n_planted_trials"],
        n_clean_trials=row["n_clean_trials"],
        source=row["source"],
        updated_at=row["updated_at"],
    )


def _decode_surprise(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["predicted_score_dist"] = _loads(payload.pop("predicted_score_dist_json"), None)
    payload["predicted_error_type_dist"] = _loads(payload.pop("predicted_error_type_dist_json"), None)
    payload["observed_joint_bucket"] = _loads(payload.pop("observed_joint_bucket_json"), {})
    payload["posterior_delta"] = _loads(payload.pop("posterior_delta_json"), None)
    payload["triggered_actions"] = _loads(payload.pop("triggered_actions_json"), [])
    payload["suppressed_actions"] = _loads(payload.pop("suppressed_actions_json"), [])
    payload["gate_diagnostics"] = _loads(payload.pop("gate_diagnostics_json"), None)
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


def _decode_proposal_batch(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["source_refs"] = _loads(payload.pop("source_refs_json"), [])
    return payload


def _decode_proposal_item(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["payload"] = _loads(payload.pop("payload_json"), {})
    payload["source_ref_ids"] = _loads(payload.pop("source_ref_ids_json", None), [])
    payload["audit"] = _loads(payload.pop("audit_json", None), None)
    payload["edited_payload"] = _loads(payload.pop("edited_payload_json"), None)
    payload["validation_errors"] = _loads(payload.pop("validation_errors_json"), [])
    return payload


def _decode_extraction_run(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["model_versions"] = _loads(payload.pop("model_versions_json", None), {})
    payload["config"] = _loads(payload.pop("config_json", None), {})
    payload["page_selection"] = _loads(payload.pop("page_selection_json", None), None)
    return payload


def _decode_document_block(row: sqlite3.Row) -> DocumentBlock:
    return DocumentBlock(
        span_id=row["span_id"],
        extractor_block_id=row["extractor_block_id"],
        block_type=row["block_type"],
        role_hint=row["role_hint"],
        page=row["page"],
        bbox=_loads(row["bbox_json"], None),
        polygon=_loads(row["polygon_json"], None),
        section_path=_loads(row["section_path_json"], []),
        text=row["text"],
        content_hash=row["content_hash"],
        asset_ids=_loads(row["asset_ids_json"], []),
        ordinal=row["ordinal"],
    )


def _decode_document_unit(row: sqlite3.Row) -> DocumentUnit:
    return DocumentUnit(
        unit_id=row["unit_id"],
        parent_unit_id=row["parent_unit_id"],
        label=row["label"],
        ordinal=row["ordinal"],
        locator=_loads(row["locator_json"], {}),
        semantic_hash=row["semantic_hash"],
        page_start=row["page_start"],
        page_end=row["page_end"],
        span_ids=_loads(row["span_ids_json"], []),
    )


def _decode_document_asset(row: sqlite3.Row) -> DocumentAsset:
    return DocumentAsset(
        id=row["id"],
        media_type=row["media_type"],
        content_hash=row["content_hash"],
        path=row["path"],
        caption=row["caption"],
        page=row["page"],
        geometry=_loads(row["geometry_json"], None),
        neighboring_span_ids=_loads(row["neighboring_span_ids_json"], []),
    )


def _content_event_has_source_grounding(row: sqlite3.Row) -> bool:
    payload = _loads(row["_proposal_edited_payload_json"], None)
    if payload is None:
        payload = _loads(row["_proposal_payload_json"], {})
    provenance = payload.get("provenance") if isinstance(payload, dict) else None
    if not isinstance(provenance, dict):
        return False
    source_refs = provenance.get("source_refs")
    return isinstance(source_refs, list) and bool(source_refs)
