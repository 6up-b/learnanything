from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
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


class BlueprintNotReviewed(Exception):
    """A golden-path confirmation named a blueprint version that is not
    reviewed/active (spec_p2 §3.1 step 1). Nothing is activated."""

    def __init__(self, blueprint_version_id: str, *, status: str | None):
        self.blueprint_version_id = blueprint_version_id
        self.status = status
        super().__init__(
            f"blueprint version {blueprint_version_id} is {status!r}, not reviewed/active"
        )


class GoalAlreadyConfirmed(Exception):
    """The goal already has a confirmed contract head whose content differs from the
    v1 this confirmation would mint (spec_p2 §1.2 invariant 2). A fresh golden-path
    run must use a fresh goal id; an edit mints an append-only successor instead."""

    def __init__(self, goal_id: str, *, head_version_id: str | None):
        self.goal_id = goal_id
        self.head_version_id = head_version_id
        super().__init__(
            f"goal {goal_id} is already confirmed (head {head_version_id!r}); "
            "confirmation cannot re-mint v1"
        )


def _json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _loads(value: str | None, default: Any) -> Any:
    if value is None:
        return default
    return json.loads(value)


# measurement_events.kind is validated here rather than by a SQL CHECK, so later
# P0 packages (P0.2 grader channel, P0.3+) extend the vocabulary by appending to
# this set without a table rebuild (spec_p0_measurement_correctness §3.3, §4.1).
_MEASUREMENT_EVENT_KINDS: set[str] = {
    "administration_opened",
    "response_appended",
    "exposure_recorded",
    "raw_grade_appended",
    "grade_classified",
    "grade_interpreted",
    "projection_rebuilt",
    "correction_appended",
    # P0.2 grader-channel lifecycle kinds (spec §3.3, §4.4). Model/interpretation
    # heads are projections over these append-only transitions; rows never mutate.
    "model_activated",
    "model_retired",
    "grade_quarantined",
    "grade_adjudicated",
    "interpretation_activated",
    "measurement_reinterpretation",
}


def _decode_exposure_event(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["detail"] = _loads(payload.get("detail_json"), None)
    payload["consumes_unseen"] = bool(payload.get("consumes_unseen"))
    return payload


def _decode_surface(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["surface"] = _loads(payload.get("surface_json"), {})
    payload["legacy_surface_unverifiable"] = bool(payload.get("legacy_surface_unverifiable"))
    return payload


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
    # KM4 §10.2 compositional fields (NULL for legacy rows; populated when a
    # mvp-0.7 vault mints a compositional record).
    mechanism: str | None = None
    operation: str | None = None
    target_facet: str | None = None
    confused_with_facet: str | None = None
    trigger_conditions: list[str] = field(default_factory=list)
    expected_signatures: list[str] = field(default_factory=list)
    first_divergence: list[str] = field(default_factory=list)
    non_applicable_controls: list[str] = field(default_factory=list)
    promotion_reason: str | None = None
    correction_statement: str | None = None
    correction_source_span_ids: list[str] = field(default_factory=list)


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
    origin: str | None
    required_facets: list[str]
    minimum_independent_observations: int
    maximum_observations: int
    entered_at: str | None
    completed_at: str | None
    completion_reason: str | None
    algorithm_version: str
    created_at: str
    updated_at: str
    # mvp-0.8 robust cutover (migration 071): the calibration channel + coarse
    # mapping pinned at episode open. NULL for legacy mvp-0.6/0.7 episodes.
    calibration_model_id: str | None = None
    calibration_model_hash: str | None = None
    probe_mapping_version: str | None = None


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
    # KM1 observation lineage (§5.2); NULL on legacy rows and under mvp-0.6.
    observation_id: str | None = None
    grading_revision: int | None = None
    assessment_contract_version_id: str | None = None
    recipe_id: str | None = None
    attribution_json: str | None = None
    correlation_group: str | None = None


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
class CanonicalFacetRecallState:
    """Canonical shared facet belief (KM2 §7.1), keyed on the post-merge facet id
    and observed capability. ``practice_item_id=None`` is the shared aggregate."""

    id: str
    facet_id: str
    capability_key: str
    practice_item_id: str | None
    recall_alpha: float
    recall_beta: float
    recall_mean: float
    recall_variance: float
    independent_evidence_mass: float
    raw_coverage_mass: float
    last_observed_at: str | None
    last_error_at: str | None
    consecutive_failures: int
    algorithm_version: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class FacetCapabilityEvidence:
    """Capability-sliced certification ledger (KM2 §7.1). A replayable cache
    derived from immutable observations, not a new evidence source."""

    facet_id: str
    capability: str
    direct_positive_mass: float
    direct_negative_mass: float
    embedded_positive_mass: float
    embedded_negative_mass: float
    certification_credit: float
    independent_surface_groups: list[str]
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


class _InjectedLineageFault(RuntimeError):
    """Fault injected inside :meth:`Repository.write_administration_lineage_atomic` to
    prove the raw-event transaction rolls back as one unit (§7.4 fault injection)."""


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
        mechanism: str | None = None,
        operation: str | None = None,
        target_facet: str | None = None,
        confused_with_facet: str | None = None,
        trigger_conditions: Iterable[str] | None = None,
        expected_signatures: Iterable[str] | None = None,
        first_divergence: Iterable[str] | None = None,
        non_applicable_controls: Iterable[str] | None = None,
        promotion_reason: str | None = None,
        correction_statement: str | None = None,
        correction_source_span_ids: Iterable[str] | None = None,
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
                  created_at, updated_at, resolved_at,
                  mechanism, operation, target_facet, confused_with_facet,
                  trigger_conditions_json, expected_signatures_json,
                  first_divergence_json, non_applicable_controls_json,
                  promotion_reason, correction_statement,
                  correction_source_span_ids_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    mechanism,
                    operation,
                    target_facet,
                    confused_with_facet,
                    _json([str(t) for t in (trigger_conditions or [])]),
                    _json([str(s) for s in (expected_signatures or [])]),
                    _json([str(d) for d in (first_divergence or [])]),
                    _json([str(c) for c in (non_applicable_controls or [])]),
                    promotion_reason,
                    correction_statement,
                    _json([str(span) for span in (correction_source_span_ids or [])]),
                ),
            )
            connection.execute(
                """
                INSERT INTO misconception_transition_events(
                  id, misconception_id, from_status, to_status, at, source
                ) VALUES (?, ?, NULL, ?, ?, 'created')
                """,
                (new_ulid(), misconception_id, status, now),
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

    def active_misconception_facet_ids(self) -> set[str]:
        """Facet ids referenced by any active/resolving misconception (§12 locks)."""

        facets: set[str] = set()
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT facet_ids_json FROM misconceptions WHERE status IN ('active', 'resolving')"
            ).fetchall()
        for row in rows:
            for facet in _loads(row["facet_ids_json"], []):
                facets.add(str(facet))
        return facets

    def facet_ids_with_recall_evidence(self) -> set[str]:
        """Facet ids with legacy per-LO recall evidence (mvp-0.6 first-touch lock).

        Reads only the legacy table on purpose: canonical mvp-0.7 facets are NOT
        first-touch-locked (§3.4 — that would defeat the grace window). They lock
        through the independence gate in ``_facet_independence_locked`` (distinct
        surface groups / independent mass / active-goal scope) instead.
        """

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT DISTINCT facet_id FROM evidence_facet_recall_state"
            ).fetchall()
        return {str(row["facet_id"]) for row in rows}

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
        correction_statement: str | None = None,
        correction_source_span_ids: Iterable[str] | None = None,
        transition_source: str = "repository",
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
            new_correction = (
                correction_statement
                if correction_statement is not None
                else current.correction_statement
            )
            new_correction_spans = (
                [str(span) for span in correction_source_span_ids]
                if correction_source_span_ids is not None
                else current.correction_source_span_ids
            )
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
                    resolved_at = ?, correction_statement = ?,
                    correction_source_span_ids_json = ?
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
                    new_correction,
                    _json(new_correction_spans),
                    misconception_id,
                ),
            )
            if new_status != current.status:
                connection.execute(
                    """
                    INSERT INTO misconception_transition_events(
                      id, misconception_id, from_status, to_status, at, source
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_ulid(), misconception_id, current.status,
                        new_status, now, transition_source,
                    ),
                )
            connection.commit()
        return self.misconception(misconception_id)

    def misconception_transition_events(self, misconception_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM misconception_transition_events
                WHERE misconception_id = ? ORDER BY at, rowid
                """,
                (misconception_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # -- Misconception candidates (KM4 §10.3 promotion discipline) -----------

    def misconception_candidate_by_normalized(
        self, learning_object_id: str, statement_normalized: str
    ) -> dict[str, Any] | None:
        """The open candidate for one normalized statement on an LO, if any."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM misconception_candidates
                WHERE learning_object_id = ? AND statement_normalized = ?
                  AND status = 'candidate'
                ORDER BY created_at, id
                LIMIT 1
                """,
                (learning_object_id, statement_normalized),
            ).fetchone()
        return _decode_misconception_candidate(row) if row is not None else None

    def misconception_candidates_for_learning_object(
        self, learning_object_id: str, statuses: Iterable[str] = ("candidate",)
    ) -> list[dict[str, Any]]:
        status_list = list(statuses)
        placeholders = ",".join("?" for _ in status_list) or "''"
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM misconception_candidates
                WHERE learning_object_id = ? AND status IN ({placeholders})
                ORDER BY created_at, id
                """,
                (learning_object_id, *status_list),
            ).fetchall()
        return [_decode_misconception_candidate(row) for row in rows]

    def insert_misconception_candidate(
        self,
        *,
        learning_object_id: str,
        statement: str,
        statement_normalized: str,
        id: str | None = None,
        concept_id: str | None = None,
        signature: str | None = None,
        mechanism: str | None = None,
        operation: str | None = None,
        target_facet: str | None = None,
        confused_with_facet: str | None = None,
        facet_ids: Iterable[str] | None = None,
        source_error_event_ids: Iterable[str] | None = None,
        surface_families: Iterable[str] | None = None,
        item_ids: Iterable[str] | None = None,
        occurrence_count: int = 1,
        severity: float = 0.0,
        clock: Clock | None = None,
    ) -> str:
        candidate_id = id or new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO misconception_candidates(
                  id, learning_object_id, concept_id, statement, statement_normalized,
                  signature, mechanism, operation, target_facet, confused_with_facet,
                  facet_ids_json, source_error_event_ids_json, surface_families_json,
                  item_ids_json, occurrence_count, severity, status,
                  promoted_misconception_id, promotion_reason, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'candidate', NULL, NULL, ?, ?)
                """,
                (
                    candidate_id,
                    learning_object_id,
                    concept_id,
                    statement,
                    statement_normalized,
                    signature,
                    mechanism,
                    operation,
                    target_facet,
                    confused_with_facet,
                    _json(sorted({str(f) for f in (facet_ids or [])})),
                    _json([str(e) for e in (source_error_event_ids or [])]),
                    _json(sorted({str(s) for s in (surface_families or [])})),
                    _json(sorted({str(i) for i in (item_ids or [])})),
                    int(occurrence_count),
                    float(severity),
                    now,
                    now,
                ),
            )
            connection.commit()
        return candidate_id

    def update_misconception_candidate(
        self,
        candidate_id: str,
        *,
        severity: float | None = None,
        occurrence_count: int | None = None,
        append_source_error_event_ids: Iterable[str] | None = None,
        add_surface_families: Iterable[str] | None = None,
        add_item_ids: Iterable[str] | None = None,
        signature: str | None = None,
        mechanism: str | None = None,
        target_facet: str | None = None,
        confused_with_facet: str | None = None,
        status: str | None = None,
        promoted_misconception_id: str | None = None,
        promotion_reason: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any] | None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM misconception_candidates WHERE id = ?",
                (candidate_id,),
            ).fetchone()
            if row is None:
                return None
            current = _decode_misconception_candidate(row)
            source_ids = list(current["source_error_event_ids"])
            for event_id in append_source_error_event_ids or []:
                if str(event_id) not in source_ids:
                    source_ids.append(str(event_id))
            surfaces = set(current["surface_families"]) | {
                str(s) for s in (add_surface_families or [])
            }
            item_ids = set(current["item_ids"]) | {str(i) for i in (add_item_ids or [])}
            connection.execute(
                """
                UPDATE misconception_candidates
                SET severity = ?, occurrence_count = ?, source_error_event_ids_json = ?,
                    surface_families_json = ?, item_ids_json = ?, signature = ?,
                    mechanism = ?, target_facet = ?, confused_with_facet = ?,
                    status = ?, promoted_misconception_id = ?, promotion_reason = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    float(severity) if severity is not None else current["severity"],
                    int(occurrence_count) if occurrence_count is not None else current["occurrence_count"],
                    _json(source_ids),
                    _json(sorted(surfaces)),
                    _json(sorted(item_ids)),
                    signature if signature is not None else current["signature"],
                    mechanism if mechanism is not None else current["mechanism"],
                    target_facet if target_facet is not None else current["target_facet"],
                    confused_with_facet if confused_with_facet is not None else current["confused_with_facet"],
                    status if status is not None else current["status"],
                    promoted_misconception_id
                    if promoted_misconception_id is not None
                    else current["promoted_misconception_id"],
                    promotion_reason if promotion_reason is not None else current["promotion_reason"],
                    now,
                    candidate_id,
                ),
            )
            connection.commit()
        return self.misconception_candidate_by_id(candidate_id)

    def misconception_candidate_by_id(self, candidate_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM misconception_candidates WHERE id = ?",
                (candidate_id,),
            ).fetchone()
        return _decode_misconception_candidate(row) if row is not None else None

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

    def calibration_duel_pairs(self) -> list[dict[str, Any]]:
        """Matched pre-outcome learner/model predictions on ordinary cold attempts."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT a.id AS attempt_id,
                       a.answer_confidence AS answer_confidence,
                       a.correctness AS correctness,
                       c.predicted_correctness AS model_predicted_correctness
                FROM practice_attempts a
                JOIN scheduler_slate_candidates c
                  ON c.id = a.scheduler_candidate_id OR c.chosen_attempt_id = a.id
                WHERE a.answer_confidence IS NOT NULL
                  AND a.correctness IS NOT NULL
                  AND c.predicted_correctness IS NOT NULL
                  AND COALESCE(a.primed, 0) = 0
                  AND COALESCE(a.hints_used, 0) = 0
                  AND a.attempt_type NOT IN (
                    'hinted_attempt', 'guided_walkthrough', 'self_report',
                    'dont_know', 'skip'
                  )
                ORDER BY a.created_at, a.id
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def pending_followup_practice_item_ids(self, *, clock: Clock | None = None) -> list[str]:
        """Return queued follow-up item ids that have not yet been attempted."""

        return [
            item["practice_item_id"]
            for item in self.pending_followup_practice_items(clock=clock)
        ]

    def pending_followup_practice_items(
        self, *, clock: Clock | None = None
    ) -> list[dict[str, str]]:
        """Return queued follow-ups that have not yet been attempted.

        Follow-up insertion is represented in MVP as an action recorded on
        ``attempt_surprise``. The scheduler consumes those actions until a later
        attempt exists for the chosen Practice Item.
        """

        task_rows = self.due_followup_tasks(clock=clock)
        pending: list[dict[str, str]] = [
            {
                "practice_item_id": str(task["selected_item_id"]),
                "action_type": "cold_retry",
                "followup_task_id": str(task["id"]),
            }
            for task in task_rows
            if task.get("selected_item_id")
        ]
        seen: set[str] = {item["practice_item_id"] for item in pending}
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

    # -- Structured remediation episodes and delayed follow-ups -----------

    def create_remediation_episode(
        self,
        *,
        case_kind: str,
        case_ref: str,
        passages_shown: Sequence[Mapping[str, Any]] = (),
        state: str = "diagnosis",
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        episode_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO remediation_episodes(
                  id, case_kind, case_ref, state, passages_shown_json,
                  created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (episode_id, case_kind, case_ref, state, _json(list(passages_shown)), now, now),
            )
            connection.commit()
        episode = self.remediation_episode(episode_id)
        assert episode is not None
        return episode

    def remediation_episode(self, episode_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM remediation_episodes WHERE id = ?", (episode_id,)
            ).fetchone()
        return _decode_remediation_episode(row) if row is not None else None

    def update_remediation_episode(
        self, episode_id: str, *, clock: Clock | None = None, **changes: Any
    ) -> dict[str, Any] | None:
        allowed = {
            "state", "passages_shown", "primed_item_id", "cold_item_id",
            "primed_attempt_id", "cold_attempt_id", "completed_at",
        }
        values = {key: value for key, value in changes.items() if key in allowed}
        if not values:
            return self.remediation_episode(episode_id)
        assignments: list[str] = []
        params: list[Any] = []
        for key, value in values.items():
            column = "passages_shown_json" if key == "passages_shown" else key
            assignments.append(f"{column} = ?")
            params.append(_json(value) if key == "passages_shown" else value)
        assignments.append("updated_at = ?")
        params.extend([utc_now_iso(clock), episode_id])
        with self.connection() as connection:
            connection.execute(
                f"UPDATE remediation_episodes SET {', '.join(assignments)} WHERE id = ?",
                params,
            )
            connection.commit()
        return self.remediation_episode(episode_id)

    def open_remediation_episode_for_primed_item(self, practice_item_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM remediation_episodes
                WHERE primed_item_id = ? AND primed_attempt_id IS NULL
                  AND state = 'treatment'
                ORDER BY created_at DESC, id DESC LIMIT 1
                """,
                (practice_item_id,),
            ).fetchone()
        return _decode_remediation_episode(row) if row is not None else None

    def create_followup_task(
        self,
        *,
        kind: str,
        case_kind: str,
        case_ref: str,
        not_before: str,
        selected_item_id: str | None,
        source_attempt_id: str | None = None,
        remediation_episode_id: str | None = None,
        expires_at: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        task_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO followup_tasks(
                  id, kind, case_kind, case_ref, source_attempt_id,
                  remediation_episode_id, not_before, expires_at, status,
                  selected_item_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                """,
                (
                    task_id, kind, case_kind, case_ref, source_attempt_id,
                    remediation_episode_id, not_before, expires_at,
                    selected_item_id, now, now,
                ),
            )
            connection.commit()
        task = self.followup_task(task_id)
        assert task is not None
        return task

    def followup_task(self, task_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM followup_tasks WHERE id = ?", (task_id,)).fetchone()
        return dict(row) if row is not None else None

    def due_followup_tasks(self, *, clock: Clock | None = None) -> list[dict[str, Any]]:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE followup_tasks SET status = 'expired', updated_at = ?
                WHERE status IN ('pending', 'served') AND expires_at IS NOT NULL
                  AND expires_at < ?
                """,
                (now, now),
            )
            rows = connection.execute(
                """
                SELECT * FROM followup_tasks
                WHERE status IN ('pending', 'served') AND not_before <= ?
                  AND (expires_at IS NULL OR expires_at >= ?)
                ORDER BY not_before, created_at, id
                """,
                (now, now),
            ).fetchall()
            ids = [row["id"] for row in rows if row["status"] == "pending"]
            if ids:
                placeholders = ",".join("?" for _ in ids)
                connection.execute(
                    f"UPDATE followup_tasks SET status = 'served', updated_at = ? WHERE id IN ({placeholders})",
                    (now, *ids),
                )
            connection.commit()
        return [dict(row) | {"status": "served"} for row in rows]

    def active_followup_task_for_item(
        self, practice_item_id: str, *, at: str | None = None
    ) -> dict[str, Any] | None:
        now = at or utc_now_iso()
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM followup_tasks
                WHERE selected_item_id = ? AND status IN ('pending', 'served')
                  AND not_before <= ? AND (expires_at IS NULL OR expires_at >= ?)
                ORDER BY not_before, created_at, id LIMIT 1
                """,
                (practice_item_id, now, now),
            ).fetchone()
        return dict(row) if row is not None else None

    def consume_followup_task(
        self, task_id: str, attempt_id: str, *, clock: Clock | None = None
    ) -> dict[str, Any] | None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE followup_tasks
                SET status = 'consumed', consumed_attempt_id = ?, updated_at = ?
                WHERE id = ? AND status IN ('pending', 'served')
                """,
                (attempt_id, now, task_id),
            )
            connection.commit()
        return self.followup_task(task_id)

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

    def insert_source_exposure_event(
        self, event: Mapping[str, Any], *, clock: Clock | None = None
    ) -> str:
        """Record one Open-in-source view (§9.2). Called on every span view."""

        event_id = str(event.get("id") or new_ulid())
        now = event.get("created_at") or utc_now_iso(clock)
        section_path = event.get("section_path") or []
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_exposure_events(
                  id, context, extraction_id, span_id, revision_id, source_id,
                  entity_type, entity_id, page, locator, section_path_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    event.get("context") or "other",
                    event["extraction_id"],
                    event["span_id"],
                    event.get("revision_id"),
                    event.get("source_id"),
                    event.get("entity_type"),
                    event.get("entity_id"),
                    event.get("page"),
                    event.get("locator"),
                    _json(list(section_path)),
                    now,
                ),
            )
            connection.commit()
        return event_id

    def source_exposure_events(
        self,
        *,
        extraction_id: str | None = None,
        span_id: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if extraction_id is not None:
            clauses.append("extraction_id = ?")
            params.append(extraction_id)
        if span_id is not None:
            clauses.append("span_id = ?")
            params.append(span_id)
        if entity_type is not None:
            clauses.append("entity_type = ?")
            params.append(entity_type)
        if entity_id is not None:
            clauses.append("entity_id = ?")
            params.append(entity_id)
        query = "SELECT * FROM source_exposure_events"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC, id DESC"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        with self.connection() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        events: list[dict[str, Any]] = []
        for row in rows:
            data = dict(row)
            raw = data.pop("section_path_json", None)
            data["section_path"] = json.loads(raw) if raw else []
            events.append(data)
        return events

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
        resolution: str | None = None,
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
            ("resolution", resolution),
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
        resolution: str | None = None,
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
                resolution=resolution,
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

    def set_question_event_resolution(self, event_id: str, *, resolution: str) -> bool:
        """Learner-facing queue state (migration 102): open | resolved | dismissed."""

        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE question_events SET resolution = ? WHERE id = ?",
                (resolution, event_id),
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
                  UNION
                  -- Learner-requested rung variants (migration 108): an applied
                  -- easier/harder variant the learner explicitly asked for is a
                  -- requested item until first attempted.
                  SELECT created_practice_item_id AS item_id, MIN(created_at) AS first_requested_at
                  FROM rung_variant_requests
                  WHERE status = 'applied' AND created_practice_item_id IS NOT NULL
                  GROUP BY item_id
                )
                WHERE item_id NOT IN (SELECT DISTINCT practice_item_id FROM practice_attempts)
                GROUP BY item_id
                ORDER BY MIN(first_requested_at), item_id
                """
            ).fetchall()
        return [row["item_id"] for row in rows]

    # --- rung variant requests (migration 108) --------------------------------

    def insert_rung_variant_request(self, request: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        request_id = str(request.get("id") or new_ulid())
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO rung_variant_requests(
                  id, source_practice_item_id, learning_object_id, direction,
                  source_waypoint_slug, target_waypoint_slug, target_rung_json,
                  status, attempt_id, learner_claim_id, batch_id, patch_id,
                  created_practice_item_id, failure_reason, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    request["source_practice_item_id"],
                    request["learning_object_id"],
                    request["direction"],
                    request["source_waypoint_slug"],
                    request["target_waypoint_slug"],
                    request["target_rung_json"],
                    request.get("status") or "pending",
                    request.get("attempt_id"),
                    request.get("learner_claim_id"),
                    request.get("batch_id"),
                    request.get("patch_id"),
                    request.get("created_practice_item_id"),
                    request.get("failure_reason"),
                    now,
                    now,
                ),
            )
            connection.commit()
        return request_id

    def rung_variant_request(self, request_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM rung_variant_requests WHERE id = ?", (request_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def update_rung_variant_request(
        self, request_id: str, *, clock: Clock | None = None, **fields: Any
    ) -> bool:
        allowed = {
            "status", "attempt_id", "learner_claim_id", "batch_id", "patch_id",
            "created_practice_item_id", "failure_reason",
        }
        updates = {key: value for key, value in fields.items() if key in allowed}
        if not updates:
            return False
        assignments = ", ".join(f"{key} = ?" for key in updates)
        with self.connection() as connection:
            cursor = connection.execute(
                f"UPDATE rung_variant_requests SET {assignments}, updated_at = ? WHERE id = ?",
                (*updates.values(), utc_now_iso(clock), request_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    def pending_rung_variant_requests(self, source_practice_item_id: str) -> list[dict[str, Any]]:
        """Non-terminal requests for one item — the per-item request lock."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM rung_variant_requests
                WHERE source_practice_item_id = ? AND status IN ('pending', 'generating')
                ORDER BY created_at, id
                """,
                (source_practice_item_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def rung_variant_batch_dead(self, batch_id: str | None) -> bool:
        """True when a request's generation batch can no longer complete it:
        the batch id is unset/unknown or every rung_variant job in it is
        terminal without the service having updated the request row (job
        crashed, was cancelled, or predates a restart)."""

        if not batch_id:
            return True
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT status FROM ingest_jobs WHERE batch_id = ? AND job_type = 'rung_variant'",
                (batch_id,),
            ).fetchall()
        if not rows:
            return True
        return all(row["status"] in ("failed", "cancelled", "completed") for row in rows)

    def rung_variant_pending_source_ids(self) -> set[str]:
        """Source items with a LIVE non-terminal variant request — the
        scheduler's pending-variant hold: never re-serve the exact card the
        learner just asked to step away from while its variant is still being
        authored. Requests whose generation batch is dead (job failed/cancelled
        without the service updating the row) do NOT hold — a crashed job must
        never hide a card indefinitely."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT r.source_practice_item_id
                FROM rung_variant_requests r
                WHERE r.status IN ('pending', 'generating')
                  AND EXISTS (
                    SELECT 1 FROM ingest_jobs j
                    WHERE j.batch_id = r.batch_id AND j.job_type = 'rung_variant'
                      AND j.status NOT IN ('failed', 'cancelled', 'completed')
                  )
                """
            ).fetchall()
        return {row["source_practice_item_id"] for row in rows}

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

    def delete_learner_claims(
        self, *, source: str, scope_type: str, scope_id: str | None = None
    ) -> int:
        """Delete claims by (source, scope_type[, scope_id]) — the replace seam
        for init-wizard (global) and rung-variant (per-LO) re-claims.

        ``covering_learner_claim`` breaks specificity ties by highest
        claimed_level, so re-seeding a LOWER level must remove the old row
        rather than append beside it.
        """

        query = "DELETE FROM learner_claims WHERE source = ? AND scope_type = ?"
        params: list[Any] = [source, scope_type]
        if scope_id is not None:
            query += " AND scope_id = ?"
            params.append(scope_id)
        with self.connection() as connection:
            cursor = connection.execute(query, params)
            connection.commit()
        return cursor.rowcount

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

    # -- KM2 canonical shared facet state (§7.1) --------------------------------
    # These read/write the canonical `facet_recall_state`, `facet_capability_evidence`,
    # and `facet_merges` tables. They are consumed only under mvp-0.7; the legacy
    # per-LO `evidence_facet_recall_state` methods above stay untouched so mvp-0.6
    # replay reproduces byte-identical state.

    def canonical_facet_recall_states(self) -> list[CanonicalFacetRecallState]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM facet_recall_state ORDER BY facet_id, capability_key, practice_item_id"
            ).fetchall()
        return [_canonical_facet_recall_state(row) for row in rows]

    def canonical_facet_recall_state(
        self,
        facet_id: str,
        capability_key: str = "shared",
        practice_item_id: str | None = None,
    ) -> CanonicalFacetRecallState | None:
        with self.connection() as connection:
            if practice_item_id is None:
                row = connection.execute(
                    """
                    SELECT * FROM facet_recall_state
                    WHERE facet_id = ? AND capability_key = ? AND practice_item_id IS NULL
                    """,
                    (facet_id, capability_key),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT * FROM facet_recall_state
                    WHERE facet_id = ? AND capability_key = ? AND practice_item_id = ?
                    """,
                    (facet_id, capability_key, practice_item_id),
                ).fetchone()
        return _canonical_facet_recall_state(row) if row is not None else None

    def facet_capability_evidence(
        self, facet_id: str, capability: str
    ) -> FacetCapabilityEvidence | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM facet_capability_evidence WHERE facet_id = ? AND capability = ?",
                (facet_id, capability),
            ).fetchone()
        return _facet_capability_evidence(row) if row is not None else None

    def facet_capability_evidence_all(self) -> list[FacetCapabilityEvidence]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM facet_capability_evidence ORDER BY facet_id, capability"
            ).fetchall()
        return [_facet_capability_evidence(row) for row in rows]

    def facet_capability_evidence_for_facet(
        self, facet_id: str
    ) -> list[FacetCapabilityEvidence]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM facet_capability_evidence WHERE facet_id = ? ORDER BY capability",
                (facet_id,),
            ).fetchall()
        return [_facet_capability_evidence(row) for row in rows]

    def facet_independence_evidence(self, facet_id: str) -> tuple[int, float]:
        """(#distinct direct surface/correlation groups, independent mass) for the
        independence-gated lock trigger (§3.4). Direct evidence only."""

        groups: set[str] = set()
        for cell in self.facet_capability_evidence_for_facet(facet_id):
            groups.update(cell.independent_surface_groups)
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT COALESCE(SUM(independent_evidence_mass), 0.0) AS mass
                FROM facet_recall_state
                WHERE facet_id = ? AND practice_item_id IS NULL
                """,
                (facet_id,),
            ).fetchone()
        return len(groups), float(row["mass"] if row is not None else 0.0)

    def canonical_observation_ledger(self) -> list[dict[str, Any]]:
        """Every graded attempt in global chronological order with its
        non-superseded grading evidence (KM2 projection input).

        Chronological across LOs so the derived canonical belief state is
        deterministic regardless of per-LO replay order; beta masses accumulate
        additively so only timestamps/consecutive-failures depend on order.
        """

        with self.connection() as connection:
            attempts = connection.execute(
                """
                SELECT id, practice_item_id, learning_object_id, attempt_type,
                       practice_mode, hints_used, created_at
                FROM practice_attempts
                ORDER BY created_at ASC, id ASC
                """
            ).fetchall()
            ledger: list[dict[str, Any]] = []
            for attempt in attempts:
                evidence = connection.execute(
                    """
                    SELECT criterion_id, points_awarded, attribution_json,
                           correlation_group, recipe_id, observation_id,
                           grading_revision, assessment_contract_version_id
                    FROM grading_evidence
                    WHERE attempt_id = ? AND superseded_at IS NULL
                    ORDER BY created_at, criterion_id
                    """,
                    (attempt["id"],),
                ).fetchall()
                ledger.append(
                    {
                        "attempt_id": attempt["id"],
                        "practice_item_id": attempt["practice_item_id"],
                        "learning_object_id": attempt["learning_object_id"],
                        "attempt_type": attempt["attempt_type"],
                        "practice_mode": attempt["practice_mode"],
                        "hints_used": attempt["hints_used"] or 0,
                        "created_at": attempt["created_at"],
                        "evidence": [
                            {
                                **dict(row),
                                "attribution_json": _loads(row["attribution_json"], None),
                            }
                            for row in evidence
                        ],
                    }
                )
        return ledger

    def canonical_observation_ledger_v2(self) -> list[dict[str, Any]]:
        """P0.3 (§4.3) authoritative-events ledger. Extends the mvp-0.7 row with the
        administration, the ACTIVE calibrated grade interpretation/adjudication, the
        grader/calibration lineage, the target-contract pin, and quarantine state.

        The mvp-0.8 projection reads only these authoritative events; the legacy
        summary columns are never replay inputs. The base attempt/evidence shape is
        the byte-identical v1 shape so the projection loop stays shared; the P0.3
        lineage fields are ADDED (never removed) -- projector tests fail if a variant
        omits them (§9.2 bullet 3)."""

        ledger = self.canonical_observation_ledger()
        with self.connection() as connection:
            for attempt in ledger:
                observation = connection.execute(
                    "SELECT * FROM activity_observations WHERE attempt_id = ? LIMIT 1",
                    (attempt["attempt_id"],),
                ).fetchone()
                interpretation = None
                adjudication = None
                administration = None
                if observation is not None:
                    observation = dict(observation)
                    if observation.get("active_interpretation_id"):
                        interp_row = connection.execute(
                            "SELECT * FROM grade_interpretations WHERE id = ?",
                            (observation["active_interpretation_id"],),
                        ).fetchone()
                        interpretation = dict(interp_row) if interp_row is not None else None
                    adj_row = connection.execute(
                        """
                        SELECT * FROM grade_adjudications
                         WHERE observation_id = ? ORDER BY created_at DESC, id DESC LIMIT 1
                        """,
                        (observation["id"],),
                    ).fetchone()
                    adjudication = dict(adj_row) if adj_row is not None else None
                    admin_row = connection.execute(
                        "SELECT * FROM activity_administrations WHERE id = ?",
                        (observation["administration_id"],),
                    ).fetchone()
                    administration = dict(admin_row) if admin_row is not None else None

                lineage: list[str] = []
                if interpretation is not None and interpretation.get("reference_prior_ids_json"):
                    lineage = _loads(interpretation["reference_prior_ids_json"], [])
                attempt["administration_id"] = (
                    observation["administration_id"] if observation is not None else None
                )
                attempt["target_contract_version_id"] = (
                    administration.get("target_contract_version_id")
                    if administration is not None else None
                )
                attempt["active_interpretation"] = interpretation
                attempt["active_adjudication"] = adjudication
                attempt["adjudication_trust_weight"] = (
                    adjudication.get("bounded_trust_weight") if adjudication is not None else None
                )
                attempt["calibration_lineage"] = lineage
                attempt["calibration_model_id"] = (
                    interpretation.get("calibration_model_id") if interpretation is not None else None
                )
                attempt["calibration_model_hash"] = (
                    interpretation.get("calibration_model_hash") if interpretation is not None else None
                )
                attempt["quarantine_state"] = (
                    interpretation.get("quarantine_state") if interpretation is not None else None
                )
                attempt["projection_algorithm_version"] = (
                    interpretation.get("projection_algorithm_version")
                    if interpretation is not None else None
                )
        return ledger

    def replace_canonical_facet_state(
        self,
        *,
        recall_rows: Iterable[Mapping[str, Any]],
        capability_rows: Iterable[Mapping[str, Any]],
        algorithm_version: str,
        clock: Clock | None = None,
    ) -> None:
        """Replace the entire canonical belief cache from a derived projection.

        The canonical state is a pure, order-independent (beta masses accumulate
        additively) projection over the immutable observation ledger, so a full
        rebuild is the safe, replay-identical way to persist it: no per-LO reset
        can shear a facet shared across LOs. Idempotent.
        """

        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute("DELETE FROM facet_recall_state")
            connection.execute("DELETE FROM facet_capability_evidence")
            for state in recall_rows:
                connection.execute(
                    """
                    INSERT INTO facet_recall_state(
                      id, facet_id, capability_key, practice_item_id, recall_alpha,
                      recall_beta, recall_mean, recall_variance,
                      independent_evidence_mass, raw_coverage_mass, last_observed_at,
                      last_error_at, consecutive_failures, algorithm_version,
                      created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(state.get("id") or new_ulid()),
                        state["facet_id"],
                        state.get("capability_key", "shared"),
                        state.get("practice_item_id"),
                        state["recall_alpha"],
                        state["recall_beta"],
                        state["recall_mean"],
                        state["recall_variance"],
                        state.get("independent_evidence_mass", 0.0),
                        state.get("raw_coverage_mass", 0.0),
                        state.get("last_observed_at"),
                        state.get("last_error_at"),
                        int(state.get("consecutive_failures", 0)),
                        algorithm_version,
                        state.get("created_at", now),
                        now,
                    ),
                )
            for row in capability_rows:
                connection.execute(
                    """
                    INSERT INTO facet_capability_evidence(
                      facet_id, capability, direct_positive_mass, direct_negative_mass,
                      embedded_positive_mass, embedded_negative_mass, certification_credit,
                      independent_surface_groups_json, algorithm_version, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["facet_id"],
                        row["capability"],
                        row.get("direct_positive_mass", 0.0),
                        row.get("direct_negative_mass", 0.0),
                        row.get("embedded_positive_mass", 0.0),
                        row.get("embedded_negative_mass", 0.0),
                        row.get("certification_credit", 0.0),
                        _json(sorted(row.get("independent_surface_groups", []))),
                        algorithm_version,
                        row.get("created_at", now),
                        now,
                    ),
                )
            connection.commit()

    # -- capability residual activation (§4.2, KM5; DEFAULT OFF) -----------------

    def replace_capability_residual_state(
        self,
        *,
        rows: Iterable[Mapping[str, Any]],
        algorithm_version: str,
        clock: Clock | None = None,
    ) -> None:
        """Replace the derived capability-residual activation state (§4.2).

        Like :meth:`replace_canonical_facet_state`, this is a full DELETE+INSERT
        of a pure projection over the observation ledger + closed episodes, so a
        rebuild reproduces it byte-identically. When residual activation is
        disabled in config the projection passes ``rows=[]`` and the table stays
        empty — determinism holds with the feature on and off.
        """

        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute("DELETE FROM capability_residual_state")
            for row in rows:
                connection.execute(
                    """
                    INSERT INTO capability_residual_state(
                      id, facet_id, capability, active, activation_reason,
                      residual_alpha, residual_beta, residual_mean,
                      parent_alpha, parent_beta, parent_mean, divergence,
                      independent_groups, independent_mass, algorithm_version,
                      created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(row.get("id") or new_ulid()),
                        row["facet_id"],
                        row["capability"],
                        1 if row.get("active") else 0,
                        row.get("activation_reason"),
                        float(row["residual_alpha"]),
                        float(row["residual_beta"]),
                        float(row["residual_mean"]),
                        float(row["parent_alpha"]),
                        float(row["parent_beta"]),
                        float(row["parent_mean"]),
                        float(row.get("divergence", 0.0)),
                        int(row.get("independent_groups", 0)),
                        float(row.get("independent_mass", 0.0)),
                        algorithm_version,
                        row.get("created_at", now),
                        now,
                    ),
                )
            connection.commit()

    def capability_residual_states(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM capability_residual_state ORDER BY facet_id, capability"
            ).fetchall()
        return [_capability_residual_row(row) for row in rows]

    def capability_residual_state(
        self, facet_id: str, capability: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM capability_residual_state WHERE facet_id = ? AND capability = ?",
                (facet_id, capability),
            ).fetchone()
        return _capability_residual_row(row) if row is not None else None

    # -- pre-first-practice identifiability watermark (§11.3, KM5) ---------------

    def identifiability_watermark(self, subject_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM subject_identifiability_watermarks WHERE subject_id = ?",
                (subject_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "subject_id": row["subject_id"],
            "registry_hash": row["registry_hash"],
            "finding_count": int(row["finding_count"]),
            "checked_at": row["checked_at"],
        }

    def upsert_identifiability_watermark(
        self,
        *,
        subject_id: str,
        registry_hash: str,
        finding_count: int,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO subject_identifiability_watermarks(
                  subject_id, registry_hash, finding_count, checked_at
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(subject_id) DO UPDATE SET
                  registry_hash = excluded.registry_hash,
                  finding_count = excluded.finding_count,
                  checked_at = excluded.checked_at
                """,
                (subject_id, registry_hash, int(finding_count), now),
            )
            connection.commit()

    # -- facet_merges: transitive resolution, cycle-rejected at write (§3.4) ------

    def facet_merge_map(self) -> dict[str, str]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT retired_facet_id, surviving_facet_id FROM facet_merges"
            ).fetchall()
        return {str(r["retired_facet_id"]): str(r["surviving_facet_id"]) for r in rows}

    def resolve_facet_merge(self, facet_id: str, merge_map: Mapping[str, str] | None = None) -> str:
        """Resolve a facet id transitively to its terminal survivor (§7.1)."""

        table = dict(merge_map) if merge_map is not None else self.facet_merge_map()
        return _resolve_merge(facet_id, table)

    def insert_facet_merge(
        self,
        *,
        retired_facet_id: str,
        surviving_facet_id: str,
        proposal_item_id: str | None = None,
        rationale: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        """Record a pre-lock reviewed merge; reject a row that creates a cycle.

        A cycle would make transitive resolution non-terminating; it is rejected
        at write time so the map can always be resolved to a fixed point (§7.1).
        """

        if retired_facet_id == surviving_facet_id:
            raise ValueError("merge would create a cycle: a facet cannot be merged into itself")
        table = self.facet_merge_map()
        if retired_facet_id in table:
            raise ValueError(f"facet {retired_facet_id!r} is already retired by a merge")
        # Would (retired -> surviving) create a cycle? It does iff `retired` is
        # already reachable from `surviving` under the existing map.
        if _resolve_merge(surviving_facet_id, table) == retired_facet_id or _reaches(
            surviving_facet_id, retired_facet_id, table
        ):
            raise ValueError(
                f"merge {retired_facet_id!r} -> {surviving_facet_id!r} would create a cycle"
            )
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO facet_merges(
                  retired_facet_id, surviving_facet_id, merged_at, proposal_item_id, rationale
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (retired_facet_id, surviving_facet_id, now, proposal_item_id, rationale),
            )
            connection.commit()

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

    # ------------------------------------------------------------------
    # P0.5 parameter registry (migration 069). SQL-only; the definition and
    # projection logic live in services/parameter_registry.py.
    # ------------------------------------------------------------------

    def upsert_parameter_registry_entry(self, *, entry: dict[str, Any], clock: Clock | None = None) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO parameter_registry(
                  path, kind, param_class, effective_value_json, effective_value_hash,
                  source, status, lifecycle, rationale, scope, owner,
                  sensitivity_certificate_id, evidence_manifest_id, redundancy_proof_id,
                  promotion_evidence_id, last_review_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                  kind = excluded.kind,
                  param_class = excluded.param_class,
                  effective_value_json = excluded.effective_value_json,
                  effective_value_hash = excluded.effective_value_hash,
                  source = excluded.source,
                  status = excluded.status,
                  lifecycle = excluded.lifecycle,
                  rationale = excluded.rationale,
                  scope = excluded.scope,
                  owner = excluded.owner,
                  sensitivity_certificate_id = excluded.sensitivity_certificate_id,
                  evidence_manifest_id = excluded.evidence_manifest_id,
                  redundancy_proof_id = excluded.redundancy_proof_id,
                  promotion_evidence_id = excluded.promotion_evidence_id,
                  last_review_at = excluded.last_review_at,
                  updated_at = excluded.updated_at
                """,
                (
                    entry["path"],
                    entry["kind"],
                    entry["param_class"],
                    _json(entry["effective_value"]),
                    entry["effective_value_hash"],
                    entry["source"],
                    entry["status"],
                    entry["lifecycle"],
                    entry["rationale"],
                    entry["scope"],
                    entry["owner"],
                    entry.get("sensitivity_certificate_id"),
                    entry.get("evidence_manifest_id"),
                    entry.get("redundancy_proof_id"),
                    entry.get("promotion_evidence_id"),
                    entry.get("last_review_at"),
                    now,
                ),
            )
            connection.commit()

    def parameter_registry_entry(self, path: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM parameter_registry WHERE path = ?", (path,)
            ).fetchone()
        return dict(row) if row is not None else None

    def parameter_registry_entries(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM parameter_registry ORDER BY path"
            ).fetchall()
        return [dict(r) for r in rows]

    def insert_parameter_registry_manifest(
        self,
        *,
        algorithm_version: str,
        manifest_hash: str,
        entries: dict[str, Any],
        clock: Clock | None = None,
    ) -> str | None:
        """Freeze one immutable manifest per algorithm version. Idempotent: a
        second freeze of the same version is a no-op (returns None)."""

        manifest_id = new_ulid()
        frozen_at = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM parameter_registry_manifests WHERE algorithm_version = ?",
                (algorithm_version,),
            ).fetchone()
            if existing is not None:
                return None
            connection.execute(
                """
                INSERT INTO parameter_registry_manifests(
                  id, algorithm_version, manifest_hash, entries_json, frozen_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (manifest_id, algorithm_version, manifest_hash, _json(entries), frozen_at),
            )
            connection.commit()
        return manifest_id

    def parameter_registry_manifest(self, algorithm_version: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM parameter_registry_manifests WHERE algorithm_version = ?",
                (algorithm_version,),
            ).fetchone()
        return dict(row) if row is not None else None

    def insert_sensitivity_certificate(self, *, certificate: dict[str, Any], clock: Clock | None = None) -> str:
        cert_id = certificate.get("id") or new_ulid()
        produced_at = certificate.get("produced_at") or utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO parameter_sensitivity_certificates(
                  id, path, covered_value_hash, plausible_range_json, flip_points_json,
                  decision_stable, scenario_json, sim_report_hash, produced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cert_id,
                    certificate["path"],
                    certificate["covered_value_hash"],
                    _json(certificate["plausible_range"]),
                    _json(certificate["flip_points"]),
                    1 if certificate["decision_stable"] else 0,
                    _json(certificate["scenario"]),
                    certificate["sim_report_hash"],
                    produced_at,
                ),
            )
            connection.commit()
        return cert_id

    def sensitivity_certificates_for_path(self, path: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM parameter_sensitivity_certificates WHERE path = ? ORDER BY produced_at DESC",
                (path,),
            ).fetchall()
        return [dict(r) for r in rows]

    def record_parameter_bind_event(
        self,
        *,
        path: str,
        bound_context: dict[str, Any],
        observation_ref: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        event_id = new_ulid()
        created_at = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO parameter_bind_events(
                  id, path, bound_context_json, observation_ref, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (event_id, path, _json(bound_context), observation_ref, created_at),
            )
            connection.commit()
        return event_id

    def parameter_bind_events_for_path(self, path: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM parameter_bind_events WHERE path = ? ORDER BY created_at",
                (path,),
            ).fetchall()
        return [dict(r) for r in rows]

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
        origin: str | None = None,
        required_facets: list[str] | None = None,
        minimum_independent_observations: int = 2,
        maximum_observations: int = 4,
        entered_at: str | None = None,
        episode_id: str | None = None,
        target_contract_version_id: str | None = None,
        target_support_hash: str | None = None,
        calibration_model_id: str | None = None,
        calibration_model_hash: str | None = None,
        probe_mapping_version: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        episode_id = episode_id or new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO probe_episodes(
                  id, learning_object_id, status, trigger, hypothesis_set_id,
                  active_state_segment_id, target_decision_json, origin, required_facets_json,
                  minimum_independent_observations, maximum_observations,
                  entered_at, completed_at, completion_reason, algorithm_version,
                  target_contract_version_id, target_support_hash,
                  calibration_model_id, calibration_model_hash, probe_mapping_version,
                  created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    episode_id,
                    learning_object_id,
                    status,
                    trigger,
                    hypothesis_set_id,
                    active_state_segment_id,
                    _json(dict(target_decision)) if target_decision is not None else None,
                    origin,
                    _json(list(required_facets or [])),
                    minimum_independent_observations,
                    maximum_observations,
                    entered_at or now,
                    algorithm_version,
                    target_contract_version_id,
                    target_support_hash,
                    calibration_model_id,
                    calibration_model_hash,
                    probe_mapping_version,
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

    # --- synthesis-time generate-discriminator needs (ING M6, §8.7) ----------

    def upsert_synthesis_generation_need(
        self,
        *,
        subject_id: str,
        need_kind: str,
        target_key: str,
        missing_capability: str,
        facet_ids: list[str] | None = None,
        source_set_id: str | None = None,
        synthesis_run_id: str | None = None,
        detail: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Record one deduplicated synthesis-time generation/coarsen need.

        Mirrors ``upsert_probe_generation_need`` but synthesis-scoped: deduped on
        (subject_id, need_kind, target_key) since there is no probe episode yet.
        """

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM synthesis_generation_needs "
                "WHERE subject_id = ? AND need_kind = ? AND target_key = ?",
                (subject_id, need_kind, target_key),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            need_id = new_ulid()
            connection.execute(
                """
                INSERT INTO synthesis_generation_needs(
                  id, subject_id, source_set_id, synthesis_run_id, need_kind,
                  target_key, missing_capability, facet_ids_json, detail, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                """,
                (
                    need_id,
                    subject_id,
                    source_set_id,
                    synthesis_run_id,
                    need_kind,
                    target_key,
                    missing_capability,
                    _json(list(facet_ids or [])),
                    detail,
                    now,
                ),
            )
            connection.commit()
        return need_id

    def synthesis_generation_needs(
        self,
        *,
        subject_id: str | None = None,
        status: str | None = None,
        need_kind: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        parameters: list[Any] = []
        for column, value in (
            ("subject_id", subject_id),
            ("status", status),
            ("need_kind", need_kind),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                parameters.append(value)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM synthesis_generation_needs{where} ORDER BY created_at, id",
                parameters,
            ).fetchall()
        return [
            {
                "id": row["id"],
                "subject_id": row["subject_id"],
                "source_set_id": row["source_set_id"],
                "synthesis_run_id": row["synthesis_run_id"],
                "need_kind": row["need_kind"],
                "target_key": row["target_key"],
                "missing_capability": row["missing_capability"],
                "facet_ids": _loads(row["facet_ids_json"], []),
                "detail": row["detail"],
                "status": row["status"],
                "created_at": row["created_at"],
                "resolved_at": row["resolved_at"],
            }
            for row in rows
        ]

    def resolve_synthesis_generation_need(
        self, need_id: str, *, status: str = "resolved", clock: Clock | None = None
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                "UPDATE synthesis_generation_needs SET status = ?, resolved_at = ? WHERE id = ?",
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

    def all_scheduler_slates(self) -> list[dict[str, Any]]:
        """Every scheduler slate in chronological order (for shadow reports)."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM scheduler_slates ORDER BY generated_at ASC, id ASC"
            ).fetchall()
        return [_decode_scheduler_slate(row) for row in rows]

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

    def most_recent_ended_at(self) -> str | None:
        """The end timestamp of the most recently completed session, or None.

        Powers the F7 welcome-back diff (§4.4): the "time since last session
        end" gap the re-entry panel is gated on. Read-only, outside replay.
        """

        with self.connection() as connection:
            row = connection.execute(
                "SELECT MAX(ended_at) AS latest FROM sessions WHERE ended_at IS NOT NULL"
            ).fetchone()
        return row["latest"] if row is not None else None

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
                SELECT practice_item_id, rubric_score, correctness, created_at
                FROM practice_attempts
                WHERE practice_item_id IN ({placeholders})
                ORDER BY created_at, id
                """,
                list(item_ids),
            ).fetchall()
        return [
            {
                "practice_item_id": row["practice_item_id"],
                "rubric_score": row["rubric_score"],
                "correctness": row["correctness"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

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
                WHERE session_id = ?
                   OR (
                     session_id IS NULL
                     AND created_at >= ? AND created_at <= ?
                   )
                """,
                (session_id, started_at, ended_at),
            ).fetchone()
        return {
            "attempts_recorded": int(row["attempts_recorded"] if row is not None else 0),
            "items_reviewed": int(row["items_reviewed"] if row is not None else 0),
        }

    def review_session_rows(self) -> list[dict[str, Any]]:
        """Reverse-chronological session spine for the Review surface."""

        with self.connection() as connection:
            sessions = connection.execute(
                "SELECT * FROM sessions WHERE ended_at IS NOT NULL ORDER BY ended_at DESC, id DESC"
            ).fetchall()
            result: list[dict[str, Any]] = []
            for session in sessions:
                attempts = connection.execute(
                    """
                    SELECT a.id, a.practice_item_id, a.learning_object_id,
                           a.created_at, s.surprise_direction
                    FROM practice_attempts a
                    LEFT JOIN attempt_surprise s ON s.attempt_id = a.id
                    WHERE a.session_id = ? OR (
                      a.session_id IS NULL AND a.created_at >= ? AND a.created_at <= ?
                    )
                    ORDER BY a.created_at, a.id
                    """,
                    (session["id"], session["started_at"], session["ended_at"]),
                ).fetchall()
                result.append(
                    dict(session)
                    | {
                        "attempts": [dict(row) for row in attempts],
                        "predictions_up": sum(row["surprise_direction"] == "positive" for row in attempts),
                        "predictions_down": sum(row["surprise_direction"] == "negative" for row in attempts),
                    }
                )
        return result

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

    def misconception_transition_counts_between(
        self, started_at: str, ended_at: str
    ) -> dict[str, int]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT from_status, to_status
                FROM misconception_transition_events
                WHERE at >= ? AND at <= ?
                """,
                (started_at, ended_at),
            ).fetchall()
        return {
            "resolved": sum(row["to_status"] == "resolved" for row in rows),
            "returned": sum(
                row["from_status"] == "resolved"
                and row["to_status"] in {"active", "resolving"}
                for row in rows
            ),
        }

    # -- Typed learner-facing hypothesis events ---------------------------

    def insert_hypothesis_event(
        self,
        *,
        event_type: str,
        claim_class: str,
        claim_type: str,
        claim_ref: str,
        claim_version: str,
        producer_version: str,
        surface: str,
        temperature: str,
        presentation_id: str | None = None,
        visible_at: str | None = None,
        suppression_reason: str | None = None,
        response_payload: Mapping[str, Any] | None = None,
        session_id: str | None = None,
        visit_id: str | None = None,
        id: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        event_id = id or new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO hypothesis_events(
                  id, created_at, presentation_id, event_type, claim_class,
                  claim_type, claim_ref, claim_version, producer_version,
                  surface, temperature, visible_at, suppression_reason,
                  response_payload_json, session_id, visit_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    now,
                    presentation_id,
                    event_type,
                    claim_class,
                    claim_type,
                    claim_ref,
                    claim_version,
                    producer_version,
                    surface,
                    temperature,
                    visible_at,
                    suppression_reason,
                    _json(dict(response_payload)) if response_payload is not None else None,
                    session_id,
                    visit_id,
                ),
            )
            connection.commit()
        event = self.hypothesis_event(event_id)
        assert event is not None
        return event

    def hypothesis_event(self, event_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM hypothesis_events WHERE id = ?", (event_id,)
            ).fetchone()
        return _decode_hypothesis_event(row) if row is not None else None

    def find_hypothesis_presentation(
        self,
        *,
        claim_ref: str,
        claim_version: str,
        surface: str,
        session_id: str | None,
        visit_id: str | None,
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM hypothesis_events
                WHERE event_type = 'presented'
                  AND claim_ref = ? AND claim_version = ? AND surface = ?
                  AND COALESCE(session_id, '') = COALESCE(?, '')
                  AND COALESCE(visit_id, '') = COALESCE(?, '')
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (claim_ref, claim_version, surface, session_id, visit_id),
            ).fetchone()
        return _decode_hypothesis_event(row) if row is not None else None

    def mark_hypothesis_visible(self, presentation_id: str, visible_at: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE hypothesis_events
                SET visible_at = COALESCE(visible_at, ?)
                WHERE id = ? AND event_type = 'presented'
                """,
                (visible_at, presentation_id),
            )
            connection.commit()
        return self.hypothesis_event(presentation_id)

    def soliciting_hypothesis_count(
        self, *, session_id: str | None = None, visit_id: str | None = None
    ) -> int:
        if session_id is None and visit_id is None:
            return 0
        column = "session_id" if session_id is not None else "visit_id"
        value = session_id if session_id is not None else visit_id
        with self.connection() as connection:
            row = connection.execute(
                f"""
                SELECT COUNT(*) AS n FROM hypothesis_events
                WHERE event_type = 'presented'
                  AND suppression_reason IS NULL
                  AND {column} = ?
                """,
                (value,),
            ).fetchone()
        return int(row["n"] if row is not None else 0)

    def cold_hypothesis_count_for_visit(self, visit_id: str) -> int:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS n FROM hypothesis_events
                WHERE event_type = 'presented' AND visit_id = ?
                  AND temperature = 'cold' AND suppression_reason IS NULL
                """,
                (visit_id,),
            ).fetchone()
        return int(row["n"] if row is not None else 0)

    def last_hypothesis_response_at(self, claim_ref: str, claim_version: str) -> str | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT created_at FROM hypothesis_events
                WHERE event_type = 'responded'
                  AND claim_ref = ? AND claim_version = ?
                ORDER BY created_at DESC, id DESC LIMIT 1
                """,
                (claim_ref, claim_version),
            ).fetchone()
        return str(row["created_at"]) if row is not None else None

    def list_hypothesis_events(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM hypothesis_events ORDER BY created_at, id"
            ).fetchall()
        return [_decode_hypothesis_event(row) for row in rows]

    def purge_hypothesis_events(self) -> int:
        with self.connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS n FROM hypothesis_events").fetchone()
            count = int(row["n"] if row is not None else 0)
            connection.execute("DELETE FROM hypothesis_events")
            connection.commit()
        return count

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
        item_rows = list(items)
        client_ids = [str(item.get("client_item_id") or "") for item in item_rows]
        client_id_counts: dict[str, int] = {}
        for client_id in client_ids:
            client_id_counts[client_id] = client_id_counts.get(client_id, 0) + 1
        duplicate_client_ids = sorted(
            client_id
            for client_id, count in client_id_counts.items()
            if client_id and count > 1
        )
        if duplicate_client_ids:
            raise ValueError(
                "proposal contains duplicate client_item_id values: "
                + ", ".join(duplicate_client_ids)
            )
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
            # client_item_id -> DB id, so LLM-declared depends_on_client_item_ids
            # normalize into the dependency table (source-ingestion §10.2).
            client_to_db_id: dict[str, str] = {}
            dependency_edges: list[tuple[str, list[str]]] = []
            for item in item_rows:
                item_db_id = item.get("id") or new_ulid()
                client_to_db_id[str(item["client_item_id"])] = item_db_id
                depends_on = list(item.get("depends_on_client_item_ids") or [])
                if depends_on:
                    dependency_edges.append((item_db_id, [str(dep) for dep in depends_on]))
                connection.execute(
                    """
                    INSERT INTO proposed_patch_items(
                      id, proposed_patch_id, client_item_id, item_type, operation,
                      target_entity_type, target_entity_id, payload_json,
                      source_ref_ids_json, audit_json, edited_payload_json,
                      decision, validation_status, validation_errors_json,
                      applied_change_batch_id, decided_at, decided_by,
                      created_at, updated_at, dependency_status,
                      dependency_block_reason_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item_db_id,
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
                        item.get("dependency_status", "pending"),
                        _json(item.get("dependency_block_reason"))
                        if item.get("dependency_block_reason") is not None
                        else None,
                    ),
                )
            for item_db_id, depends_on in dependency_edges:
                for client_dep in depends_on:
                    dep_db_id = client_to_db_id.get(client_dep)
                    if dep_db_id is None or dep_db_id == item_db_id:
                        # An unknown or self-referential dependency is dropped
                        # rather than persisted as a dangling edge; the item's
                        # dependency_status carries any blocking reason.
                        continue
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO proposed_patch_item_dependencies(
                          proposed_patch_item_id, depends_on_patch_item_id
                        )
                        VALUES (?, ?)
                        """,
                        (item_db_id, dep_db_id),
                    )
            self._refresh_proposal_status(connection, batch_id, updated_at=batch.get("updated_at", batch["created_at"]))
            connection.commit()
        return batch_id

    def proposal_item_dependencies(self, item_id: str) -> list[str]:
        """DB ids this proposal item depends on (source-ingestion §10.2)."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT depends_on_patch_item_id
                FROM proposed_patch_item_dependencies
                WHERE proposed_patch_item_id = ?
                ORDER BY depends_on_patch_item_id
                """,
                (item_id,),
            ).fetchall()
        return [row["depends_on_patch_item_id"] for row in rows]

    def set_proposal_item_dependency_status(
        self,
        item_id: str,
        *,
        dependency_status: str,
        block_reason: Mapping[str, Any] | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE proposed_patch_items
                SET dependency_status = ?, dependency_block_reason_json = ?
                WHERE id = ?
                """,
                (
                    dependency_status,
                    _json(block_reason) if block_reason is not None else None,
                    item_id,
                ),
            )
            connection.commit()

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

    # ------------------------------------------------------------------
    # Activity lineage substrate (P0.1; migration 065;
    # spec_p0_measurement_correctness §3.5-§3.8). SQL only; business logic
    # lives in services/activities.py and services/activity_backfill.py.
    # ------------------------------------------------------------------

    def ensure_activity_family(
        self,
        *,
        purpose: str,
        legacy_kind: str | None,
        title: str | None,
        clock: Clock | None = None,
    ) -> str:
        """Content-addressed activity family, idempotent on ``(purpose, legacy_kind, title)``.

        Purpose is immutable for the life of a family (§3.5), so a re-run with the
        same authoring key reuses the existing family rather than transitioning it.
        """

        select_sql = """
            SELECT id FROM activity_families
             WHERE purpose = ?
               AND IFNULL(legacy_kind, '') = IFNULL(?, '')
               AND IFNULL(title, '') = IFNULL(?, '')
        """
        key = (purpose, legacy_kind, title)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(select_sql, key).fetchone()
            if existing is not None:
                connection.execute("ROLLBACK")
                return existing["id"]
            family_id = new_ulid()
            try:
                connection.execute(
                    """
                    INSERT INTO activity_families(id, purpose, legacy_kind, title, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (family_id, purpose, legacy_kind, title, utc_now_iso(clock)),
                )
                connection.execute("COMMIT")
                return family_id
            except sqlite3.IntegrityError:
                # A racing writer won the UNIQUE(authoring key) backstop (migration
                # 070); adopt its row rather than duplicating (M1).
                connection.execute("ROLLBACK")
                row = connection.execute(select_sql, key).fetchone()
                if row is None:
                    raise
                return row["id"]
        finally:
            connection.close()

    def ensure_activity_family_version(
        self,
        *,
        family_id: str,
        version: int,
        family_spec_json: str,
        clock: Clock | None = None,
    ) -> str:
        """Immutable family-spec snapshot, idempotent on ``(family_id, version)``."""

        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM activity_family_versions WHERE family_id = ? AND version = ?",
                (family_id, version),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            version_id = new_ulid()
            connection.execute(
                """
                INSERT INTO activity_family_versions(
                  id, family_id, version, family_spec_json, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (version_id, family_id, version, family_spec_json, utc_now_iso(clock)),
            )
            connection.commit()
        return version_id

    def ensure_activity_card(self, *, family_id: str, clock: Clock | None = None) -> str:
        """The family's canonical card (one card per family in the P0.1 legacy world).

        Idempotent: returns the family's existing card, creating one if absent.
        """

        select_sql = (
            "SELECT id FROM activity_cards WHERE family_id = ? ORDER BY created_at, id LIMIT 1"
        )
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(select_sql, (family_id,)).fetchone()
            if existing is not None:
                connection.execute("ROLLBACK")
                return existing["id"]
            card_id = new_ulid()
            try:
                connection.execute(
                    "INSERT INTO activity_cards(id, family_id, created_at) VALUES (?, ?, ?)",
                    (card_id, family_id, utc_now_iso(clock)),
                )
                connection.execute("COMMIT")
                return card_id
            except sqlite3.IntegrityError:
                # A racing writer won the UNIQUE(family_id) backstop (migration 070).
                connection.execute("ROLLBACK")
                row = connection.execute(select_sql, (family_id,)).fetchone()
                if row is None:
                    raise
                return row["id"]
        finally:
            connection.close()

    def ensure_activity_card_version(
        self,
        *,
        card_id: str,
        version: int,
        card_contract_hash: str,
        contract_json: str,
        schema_version: int,
        predecessor_card_version_id: str | None = None,
        lineage_kind: str | None = None,
        legacy_contract_version_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Content-addressed card version, idempotent on ``(card_id, card_contract_hash)``.

        Two presentations that make the same semantic claim reuse one card version
        (§3.5); the exact wording lives on the surface, not here.
        """

        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM activity_card_versions
                 WHERE card_id = ? AND card_contract_hash = ?
                """,
                (card_id, card_contract_hash),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            version_id = new_ulid()
            connection.execute(
                """
                INSERT INTO activity_card_versions(
                  id, card_id, version, card_contract_hash, contract_json,
                  schema_version, predecessor_card_version_id, lineage_kind,
                  legacy_contract_version_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    card_id,
                    version,
                    card_contract_hash,
                    contract_json,
                    schema_version,
                    predecessor_card_version_id,
                    lineage_kind,
                    legacy_contract_version_id,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return version_id

    def ensure_activity_surface(
        self,
        *,
        card_version_id: str,
        surface_hash: str,
        fingerprint: str | None,
        surface_json: str,
        legacy_practice_item_id: str | None = None,
        legacy_surface_unverifiable: bool = False,
        clock: Clock | None = None,
    ) -> str:
        """Content-addressed surface, idempotent on ``(card_version_id, surface_hash)``.

        surface_hash is the exact-presentation identity (§3.6 rule 1); fingerprint
        is the shared-stimulus near-clone key (§3.6 rule 2).
        """

        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM activity_surfaces
                 WHERE card_version_id = ? AND surface_hash = ?
                """,
                (card_version_id, surface_hash),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            surface_id = new_ulid()
            connection.execute(
                """
                INSERT INTO activity_surfaces(
                  id, card_version_id, surface_hash, fingerprint, surface_json,
                  legacy_practice_item_id, legacy_surface_unverifiable, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    surface_id,
                    card_version_id,
                    surface_hash,
                    fingerprint,
                    surface_json,
                    legacy_practice_item_id,
                    1 if legacy_surface_unverifiable else 0,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return surface_id

    def insert_surface_reservation(
        self,
        *,
        surface_id: str,
        goal_id: str | None,
        target_contract_version_id: str | None,
        target_support_hash: str | None,
        purpose: str,
        eligibility_json: str,
        clock: Clock | None = None,
    ) -> str:
        """Reserve a surface (§4.5). Raises ``sqlite3.IntegrityError`` when a live
        reservation already exists (partial unique index enforces at most one)."""

        reservation_id = new_ulid()
        now = utc_now_iso(clock)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT INTO activity_surface_reservations(
                  id, surface_id, goal_id, target_contract_version_id,
                  target_support_hash, purpose, status, eligibility_json,
                  administration_id, reserved_at, closed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'reserved', ?, NULL, ?, NULL)
                """,
                (
                    reservation_id,
                    surface_id,
                    goal_id,
                    target_contract_version_id,
                    target_support_hash,
                    purpose,
                    eligibility_json,
                    now,
                ),
            )
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()
        return reservation_id

    def close_surface_reservation(
        self,
        *,
        reservation_id: str,
        status: str,
        administration_id: str | None = None,
        expected_status: str | None = None,
        clock: Clock | None = None,
    ) -> bool:
        """Transition a reservation to a terminal status (the one permitted
        mutation on this append-mostly substrate).

        When ``expected_status`` is given the transition is a compare-and-set:
        it only fires ``WHERE status = expected_status`` (L8), so a caller that
        lost a race to a concurrent render/cancel gets ``False`` instead of
        clobbering the winner's terminal status. Returns whether a row transitioned.
        """

        clauses = "WHERE id = ?"
        params: list[Any] = [status, administration_id, utc_now_iso(clock), reservation_id]
        if expected_status is not None:
            clauses += " AND status = ?"
            params.append(expected_status)
        with self.connection() as connection:
            cursor = connection.execute(
                f"""
                UPDATE activity_surface_reservations
                   SET status = ?, administration_id = COALESCE(?, administration_id),
                       closed_at = ?
                 {clauses}
                """,
                params,
            )
            connection.commit()
            return cursor.rowcount > 0

    def open_administration_atomic(
        self,
        *,
        reservation_id: str | None,
        surface_id: str,
        card_version_id: str,
        family_id: str,
        purpose: str,
        surface_hash: str,
        fingerprint: str | None,
        snapshot_hash: str,
        snapshot_json: str,
        consumes_unseen: bool,
        pins: Mapping[str, Any] | None = None,
        algorithm_version: str,
        enforce_eligibility: bool = False,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """The render burn boundary (§4.5). Atomically: recheck no prior render,
        (when ``enforce_eligibility``) re-run the §3.6 collision checks INSIDE the
        lock and refuse on collision, insert the administration, insert the
        once-only ``rendered`` exposure, append ``expose`` (+ ``consume`` when
        consuming), and flip the reservation.

        Returns ``{"administration": <row dict>, "already_open": bool}``. Under a
        concurrent second render the loser observes the winner's rendered exposure
        and returns that same administration (expose-at-most-once, §9.5). When
        ``enforce_eligibility`` and a global exposure/fingerprint/quarantine
        collision is present, ROLLBACKs and returns
        ``{"administration": None, "refused": True, "refusal_reason": <reason>}``
        (§4.5, §7.3 row "exposure collision at render").
        """

        pins = dict(pins or {})
        now = utc_now_iso(clock)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("BEGIN IMMEDIATE")
            existing_render = connection.execute(
                """
                SELECT administration_id FROM activity_exposure_events
                 WHERE surface_id = ? AND kind = 'rendered'
                 LIMIT 1
                """,
                (surface_id,),
            ).fetchone()
            if existing_render is not None:
                admin_id = existing_render["administration_id"]
                admin = connection.execute(
                    "SELECT * FROM activity_administrations WHERE id = ?",
                    (admin_id,),
                ).fetchone()
                connection.execute("ROLLBACK")
                return {"administration": dict(admin) if admin else None, "already_open": True}

            if enforce_eligibility:
                # The §3.6 rules re-evaluated inside the burn lock (§4.5). A prior
                # render OF THIS surface was already handled above (concurrent
                # render -> winner). Any remaining exact-hash exposure is a
                # different surface; a fingerprint hit is a near-clone; a
                # quarantine disqualifies. Refuse rather than burn.
                refusal_reason: str | None = None
                exact = connection.execute(
                    "SELECT id FROM activity_exposure_events WHERE surface_hash = ? LIMIT 1",
                    (surface_hash,),
                ).fetchone()
                if exact is not None:
                    refusal_reason = "exact_surface_collision"
                elif fingerprint is not None:
                    near = connection.execute(
                        "SELECT id FROM activity_exposure_events WHERE fingerprint = ? LIMIT 1",
                        (fingerprint,),
                    ).fetchone()
                    if near is not None:
                        refusal_reason = "near_clone_collision"
                if refusal_reason is None:
                    quarantined = connection.execute(
                        """
                        SELECT id FROM activity_surface_lifecycle_events
                         WHERE surface_id = ? AND kind = 'quarantine' LIMIT 1
                        """,
                        (surface_id,),
                    ).fetchone()
                    if quarantined is not None:
                        refusal_reason = "assessment_disqualified"
                if refusal_reason is not None:
                    connection.execute("ROLLBACK")
                    return {
                        "administration": None,
                        "already_open": False,
                        "refused": True,
                        "refusal_reason": refusal_reason,
                    }

            administration_id = new_ulid()
            connection.execute(
                """
                INSERT INTO activity_administrations(
                  id, surface_id, card_version_id, family_id, purpose,
                  administration_snapshot_hash, snapshot_json,
                  target_contract_version_id, target_support_hash,
                  grader_model_version_id, selection_policy_version_id,
                  decision_params_hash, assistance_json, feedback_condition,
                  eligibility_json, reservation_id, legacy_backfilled, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    administration_id,
                    surface_id,
                    card_version_id,
                    family_id,
                    purpose,
                    snapshot_hash,
                    snapshot_json,
                    pins.get("target_contract_version_id"),
                    pins.get("target_support_hash"),
                    pins.get("grader_model_version_id"),
                    pins.get("selection_policy_version_id"),
                    pins.get("decision_params_hash"),
                    pins.get("assistance_json"),
                    pins.get("feedback_condition"),
                    pins.get("eligibility_json"),
                    reservation_id,
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO activity_exposure_events(
                  id, surface_id, administration_id, surface_hash, fingerprint,
                  kind, purpose, consumes_unseen, detail_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, 'rendered', ?, ?, NULL, ?)
                """,
                (
                    new_ulid(),
                    surface_id,
                    administration_id,
                    surface_hash,
                    fingerprint,
                    purpose,
                    1 if consumes_unseen else 0,
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO activity_surface_lifecycle_events(
                  id, surface_id, reservation_id, administration_id, kind,
                  reason, detail_json, created_at
                )
                VALUES (?, ?, ?, ?, 'expose', NULL, NULL, ?)
                """,
                (new_ulid(), surface_id, reservation_id, administration_id, now),
            )
            if consumes_unseen:
                connection.execute(
                    """
                    INSERT INTO activity_surface_lifecycle_events(
                      id, surface_id, reservation_id, administration_id, kind,
                      reason, detail_json, created_at
                    )
                    VALUES (?, ?, ?, ?, 'consume', NULL, NULL, ?)
                    """,
                    (new_ulid(), surface_id, reservation_id, administration_id, now),
                )
            connection.execute(
                """
                INSERT INTO measurement_events(
                  id, administration_id, observation_id, kind, algorithm_version,
                  payload_json, created_at
                )
                VALUES (?, ?, NULL, 'administration_opened', ?, NULL, ?)
                """,
                (new_ulid(), administration_id, algorithm_version, now),
            )
            if reservation_id is not None:
                connection.execute(
                    """
                    UPDATE activity_surface_reservations
                       SET status = 'rendered', administration_id = ?, closed_at = ?
                     WHERE id = ? AND status = 'reserved'
                    """,
                    (administration_id, now, reservation_id),
                )
            admin = connection.execute(
                "SELECT * FROM activity_administrations WHERE id = ?",
                (administration_id,),
            ).fetchone()
            connection.execute("COMMIT")
            return {"administration": dict(admin), "already_open": False}
        except Exception:
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def write_administration_lineage_atomic(
        self,
        *,
        surface_id: str,
        card_version_id: str,
        family_id: str,
        purpose: str,
        surface_hash: str,
        fingerprint: str | None,
        snapshot_hash: str,
        snapshot_json: str,
        consumes_unseen: bool,
        algorithm_version: str,
        evidence_eligibility: str | None,
        eligibility_reason: str | None,
        reading_phase: str | None = None,
        admin_context: Mapping[str, Any] | None = None,
        attempt_id: str | None = None,
        response_ref: str | None = None,
        response_ledger_json: str | None = None,
        fault_after: "frozenset[str]" = frozenset(),
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Write the full RAW-EVENT lineage for one administration as ONE transaction
        (§7.4/§7.5): administration (+ its context, folded in so no NULL-context window
        exists) + rendered & submitted exposures + expose/consume lifecycle +
        observation + measurement events (administration_opened, response_appended).

        A fault anywhere in this unit rolls the WHOLE thing back -- a partial raw-event
        set is impossible; the only write allowed to defer is the downstream projection
        (card_state), handled by the caller. Idempotent: a prior render of the surface
        reuses that administration and its submitted exposure / observation.

        ``fault_after`` injects a fault INSIDE the transaction after the named boundary
        (``administration`` / ``exposure``) to prove rollback leaves nothing.
        """

        now = utc_now_iso(clock)
        admin_context_json = (
            None if admin_context is None else json.dumps(dict(admin_context), sort_keys=True)
        )
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("BEGIN IMMEDIATE")
            existing_render = connection.execute(
                """
                SELECT administration_id FROM activity_exposure_events
                 WHERE surface_id = ? AND kind = 'rendered' LIMIT 1
                """,
                (surface_id,),
            ).fetchone()
            already_open = existing_render is not None
            if already_open:
                administration_id = existing_render["administration_id"]
            else:
                administration_id = new_ulid()
                connection.execute(
                    """
                    INSERT INTO activity_administrations(
                      id, surface_id, card_version_id, family_id, purpose,
                      administration_snapshot_hash, snapshot_json, reading_phase,
                      admin_context_json, legacy_backfilled, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                    """,
                    (
                        administration_id, surface_id, card_version_id, family_id, purpose,
                        snapshot_hash, snapshot_json, reading_phase, admin_context_json, now,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO activity_exposure_events(
                      id, surface_id, administration_id, surface_hash, fingerprint,
                      kind, purpose, consumes_unseen, detail_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, 'rendered', ?, ?, NULL, ?)
                    """,
                    (new_ulid(), surface_id, administration_id, surface_hash, fingerprint,
                     purpose, 1 if consumes_unseen else 0, now),
                )
                connection.execute(
                    """
                    INSERT INTO activity_surface_lifecycle_events(
                      id, surface_id, reservation_id, administration_id, kind,
                      reason, detail_json, created_at
                    )
                    VALUES (?, ?, NULL, ?, 'expose', NULL, NULL, ?)
                    """,
                    (new_ulid(), surface_id, administration_id, now),
                )
                if consumes_unseen:
                    connection.execute(
                        """
                        INSERT INTO activity_surface_lifecycle_events(
                          id, surface_id, reservation_id, administration_id, kind,
                          reason, detail_json, created_at
                        )
                        VALUES (?, ?, NULL, ?, 'consume', NULL, NULL, ?)
                        """,
                        (new_ulid(), surface_id, administration_id, now),
                    )
                connection.execute(
                    """
                    INSERT INTO measurement_events(
                      id, administration_id, observation_id, kind, algorithm_version,
                      payload_json, created_at
                    )
                    VALUES (?, ?, NULL, 'administration_opened', ?, NULL, ?)
                    """,
                    (new_ulid(), administration_id, algorithm_version, now),
                )
            if "administration" in fault_after:
                raise _InjectedLineageFault("administration")

            # Submitted exposure (idempotent reuse on retry).
            submitted = connection.execute(
                """
                SELECT id FROM activity_exposure_events
                 WHERE administration_id = ? AND kind = 'submitted' LIMIT 1
                """,
                (administration_id,),
            ).fetchone()
            if submitted is not None:
                submitted_exposure_id = submitted["id"]
            else:
                submitted_exposure_id = new_ulid()
                connection.execute(
                    """
                    INSERT INTO activity_exposure_events(
                      id, surface_id, administration_id, surface_hash, fingerprint,
                      kind, purpose, consumes_unseen, detail_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, 'submitted', ?, 0, NULL, ?)
                    """,
                    (submitted_exposure_id, surface_id, administration_id, surface_hash,
                     fingerprint, purpose, now),
                )
            if "exposure" in fault_after:
                raise _InjectedLineageFault("exposure")

            # Observation (idempotent reuse on retry) + response_appended measurement.
            existing_obs = connection.execute(
                "SELECT id FROM activity_observations WHERE administration_id = ? LIMIT 1",
                (administration_id,),
            ).fetchone()
            if existing_obs is not None:
                observation_id = existing_obs["id"]
            else:
                observation_id = new_ulid()
                connection.execute(
                    """
                    INSERT INTO activity_observations(
                      id, administration_id, surface_id, attempt_id, response_ref,
                      active_interpretation_id, evidence_eligibility, eligibility_reason,
                      created_at
                    )
                    VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?)
                    """,
                    (observation_id, administration_id, surface_id, attempt_id, response_ref,
                     evidence_eligibility, eligibility_reason, now),
                )
                connection.execute(
                    """
                    INSERT INTO measurement_events(
                      id, administration_id, observation_id, kind, algorithm_version,
                      payload_json, created_at
                    )
                    VALUES (?, ?, ?, 'response_appended', ?, ?, ?)
                    """,
                    (new_ulid(), administration_id, observation_id, algorithm_version,
                     response_ledger_json, now),
                )
            connection.execute("COMMIT")
            return {
                "administration_id": administration_id,
                "submitted_exposure_id": submitted_exposure_id,
                "observation_id": observation_id,
                "already_open": already_open,
            }
        except Exception:
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def append_exposure_event(
        self,
        *,
        surface_id: str,
        administration_id: str | None,
        surface_hash: str,
        fingerprint: str | None,
        kind: str,
        purpose: str,
        consumes_unseen: bool = False,
        detail_json: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO activity_exposure_events(
                  id, surface_id, administration_id, surface_hash, fingerprint,
                  kind, purpose, consumes_unseen, detail_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    surface_id,
                    administration_id,
                    surface_hash,
                    fingerprint,
                    kind,
                    purpose,
                    1 if consumes_unseen else 0,
                    detail_json,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return event_id

    def append_surface_lifecycle_event(
        self,
        *,
        surface_id: str,
        kind: str,
        reservation_id: str | None = None,
        administration_id: str | None = None,
        reason: str | None = None,
        detail_json: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO activity_surface_lifecycle_events(
                  id, surface_id, reservation_id, administration_id, kind,
                  reason, detail_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    surface_id,
                    reservation_id,
                    administration_id,
                    kind,
                    reason,
                    detail_json,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return event_id

    def insert_activity_observation(
        self,
        *,
        administration_id: str,
        surface_id: str,
        attempt_id: str | None = None,
        response_ref: str | None = None,
        evidence_eligibility: str | None = None,
        eligibility_reason: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        observation_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO activity_observations(
                  id, administration_id, surface_id, attempt_id, response_ref,
                  active_interpretation_id, evidence_eligibility, eligibility_reason,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?)
                """,
                (
                    observation_id,
                    administration_id,
                    surface_id,
                    attempt_id,
                    response_ref,
                    evidence_eligibility,
                    eligibility_reason,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return observation_id

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
            connection.execute("PRAGMA busy_timeout = 5000")
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

    def consumer_pins_for_versions(
        self, version_ids: Sequence[str]
    ) -> list[dict[str, Any]]:
        """UNION projection (§1.5) of every consumer pin whose
        ``target_contract_version_id`` is in ``version_ids``: probe episodes,
        assessment reservations, and administrations. Read-only."""

        if not version_ids:
            return []
        placeholders = ",".join("?" for _ in version_ids)
        pins: list[dict[str, Any]] = []
        with self.connection() as connection:
            for kind, table, id_col in (
                ("probe_episode", "probe_episodes", "id"),
                ("assessment_reserve", "activity_surface_reservations", "id"),
                ("administration", "activity_administrations", "id"),
            ):
                rows = connection.execute(
                    f"""
                    SELECT {id_col} AS consumer_id, target_contract_version_id,
                           target_support_hash
                      FROM {table}
                     WHERE target_contract_version_id IN ({placeholders})
                    """,
                    tuple(version_ids),
                ).fetchall()
                for row in rows:
                    pins.append(
                        {
                            "consumer_kind": kind,
                            "consumer_id": row["consumer_id"],
                            "target_contract_version_id": row["target_contract_version_id"],
                            "target_support_hash": row["target_support_hash"],
                        }
                    )
        return pins

    def insert_retirement_record(
        self,
        *,
        scope: str,
        family_id: str | None,
        card_version_id: str | None,
        surface_id: str | None,
        reason: str,
        provenance: str,
        replacement_proposal_json: str | None = None,
        lifecycle_event_id: str | None = None,
        interaction_event_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        record_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO retirement_records(
                  id, scope, family_id, card_version_id, surface_id, reason,
                  provenance, replacement_proposal_json, lifecycle_event_id,
                  interaction_event_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    scope,
                    family_id,
                    card_version_id,
                    surface_id,
                    reason,
                    provenance,
                    replacement_proposal_json,
                    lifecycle_event_id,
                    interaction_event_id,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return record_id

    def append_interaction_event(
        self,
        *,
        kind: str,
        origin: str,
        subject_type: str | None = None,
        subject_id: str | None = None,
        administration_id: str | None = None,
        surface_id: str | None = None,
        attempt_id: str | None = None,
        affect_tap_kind: str | None = None,
        attempt_duration_ms: int | None = None,
        payload_json: str | None = None,
        occurred_at: str | None = None,
        received_at: str | None = None,
        actor: str | None = None,
        client_id: str | None = None,
        session_id: str | None = None,
        visit_id: str | None = None,
        payload_schema_version: str | None = None,
        source_id: str | None = None,
        revision_id: str | None = None,
        render_view_id: str | None = None,
        locator_json: str | None = None,
        annotation_id: str | None = None,
        commitment_id: str | None = None,
        activity_id: str | None = None,
        payload_hash: str | None = None,
        client_idempotency_key: str | None = None,
        privacy_locality: str | None = None,
        consent_context: str | None = None,
        producer_version: str | None = None,
        app_version: str | None = None,
        policy_version: str | None = None,
        supersedes_event_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        # §8.1 reader-envelope columns are all nullable so P0/P1/P2 callers are
        # untouched. A UNIQUE index on client_idempotency_key dedupes retries.
        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO interaction_events(
                  id, kind, subject_type, subject_id, administration_id, surface_id,
                  attempt_id, affect_tap_kind, attempt_duration_ms, payload_json,
                  origin, created_at,
                  occurred_at, received_at, actor, client_id, session_id, visit_id,
                  payload_schema_version, source_id, revision_id, render_view_id,
                  locator_json, annotation_id, commitment_id, activity_id,
                  payload_hash, client_idempotency_key, privacy_locality,
                  consent_context, producer_version, app_version, policy_version,
                  supersedes_event_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    kind,
                    subject_type,
                    subject_id,
                    administration_id,
                    surface_id,
                    attempt_id,
                    affect_tap_kind,
                    attempt_duration_ms,
                    payload_json,
                    origin,
                    utc_now_iso(clock),
                    occurred_at,
                    received_at,
                    actor,
                    client_id,
                    session_id,
                    visit_id,
                    payload_schema_version,
                    source_id,
                    revision_id,
                    render_view_id,
                    locator_json,
                    annotation_id,
                    commitment_id,
                    activity_id,
                    payload_hash,
                    client_idempotency_key,
                    privacy_locality,
                    consent_context,
                    producer_version,
                    app_version,
                    policy_version,
                    supersedes_event_id,
                ),
            )
            connection.commit()
        return event_id

    # ------------------------------------------------------------------
    # P3 reader integration (spec_p3_reader_integration slice 1)
    # ------------------------------------------------------------------

    # -- render views + crosswalk (§3.2) --

    def insert_render_view(self, view: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        view_id = view.get("id") or new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_render_views(
                  id, source_id, revision_id, extraction_id, renderer, renderer_version,
                  model_version, config_version, schema_version, content_hash,
                  asset_manifest_hash, status, health_summary_json, predecessor_view_id,
                  predecessor_reason, output_ref, request_hash, result_hash,
                  created_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    view_id,
                    view["source_id"],
                    view["revision_id"],
                    view["extraction_id"],
                    view.get("renderer", "marker_markdown"),
                    view["renderer_version"],
                    view.get("model_version"),
                    view.get("config_version"),
                    view["schema_version"],
                    view["content_hash"],
                    view.get("asset_manifest_hash"),
                    view.get("status", "ready"),
                    _json(view.get("health_summary", {})),
                    view.get("predecessor_view_id"),
                    view.get("predecessor_reason"),
                    view.get("output_ref"),
                    view["request_hash"],
                    view.get("result_hash"),
                    now,
                    view.get("completed_at", now),
                ),
            )
            connection.commit()
        return view_id

    def get_render_view(self, render_view_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_render_views WHERE id = ?", (render_view_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def render_view_by_request_hash(self, request_hash: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_render_views WHERE request_hash = ?", (request_hash,)
            ).fetchone()
        return dict(row) if row is not None else None

    def latest_render_view_for_extraction(self, extraction_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_render_views WHERE extraction_id = ? "
                "ORDER BY created_at DESC, id DESC LIMIT 1",
                (extraction_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def insert_render_crosswalk_nodes(
        self, render_view_id: str, nodes: Sequence[Mapping[str, Any]], *, clock: Clock | None = None
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            for ordinal, node in enumerate(nodes):
                connection.execute(
                    """
                    INSERT INTO source_render_block_crosswalk(
                      id, render_view_id, display_node_id, display_ordinal, extraction_id,
                      span_id, block_content_hash, block_ordinal, display_start, display_end,
                      katex_node_ids_json, asset_ids_json, status, reason, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        node.get("id") or new_ulid(),
                        render_view_id,
                        node["display_node_id"],
                        node.get("display_ordinal", ordinal),
                        node["extraction_id"],
                        node.get("span_id"),
                        node.get("block_content_hash"),
                        node.get("block_ordinal"),
                        node.get("display_start"),
                        node.get("display_end"),
                        _json(node.get("katex_node_ids", [])),
                        _json(node.get("asset_ids", [])),
                        node.get("status", "mapped"),
                        node.get("reason"),
                        now,
                    ),
                )
            connection.commit()

    def render_crosswalk(self, render_view_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_render_block_crosswalk WHERE render_view_id = ? "
                "ORDER BY display_ordinal, id",
                (render_view_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # -- block health (§3.4) --

    def upsert_block_health(self, health: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        health_id = health.get("id") or new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_block_health(
                  id, extraction_id, span_id, analyzer_version, status, reason_flags_json,
                  signal_provenance_json, confidence, page_health_flags_json,
                  recommended_view, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(extraction_id, span_id, analyzer_version) DO UPDATE SET
                  status = excluded.status,
                  reason_flags_json = excluded.reason_flags_json,
                  signal_provenance_json = excluded.signal_provenance_json,
                  confidence = excluded.confidence,
                  page_health_flags_json = excluded.page_health_flags_json,
                  recommended_view = excluded.recommended_view
                """,
                (
                    health_id,
                    health["extraction_id"],
                    health["span_id"],
                    health["analyzer_version"],
                    health.get("status", "unknown"),
                    _json(health.get("reason_flags", [])),
                    _json(health.get("signal_provenance", {})),
                    health.get("confidence"),
                    _json(health.get("page_health_flags", [])),
                    health.get("recommended_view", "derived"),
                    now,
                ),
            )
            connection.commit()
        return health_id

    def block_health(self, extraction_id: str, span_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_block_health WHERE extraction_id = ? AND span_id = ? "
                "ORDER BY analyzer_version DESC, created_at DESC LIMIT 1",
                (extraction_id, span_id),
            ).fetchone()
        return dict(row) if row is not None else None

    def block_health_for_extraction(self, extraction_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_block_health WHERE extraction_id = ? ORDER BY span_id",
                (extraction_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # -- annotations (§4) --

    def create_annotation(self, *, source_id: str, clock: Clock | None = None) -> str:
        annotation_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO source_annotations(id, source_id, created_at) VALUES (?, ?, ?)",
                (annotation_id, source_id, utc_now_iso(clock)),
            )
            connection.commit()
        return annotation_id

    def next_annotation_version_ordinal(self, annotation_id: str) -> int:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT COALESCE(MAX(version_ordinal), 0) AS m FROM source_annotation_versions "
                "WHERE annotation_id = ?",
                (annotation_id,),
            ).fetchone()
        return int(row["m"]) + 1

    def annotation_head(self, annotation_id: str) -> dict[str, Any] | None:
        """Rebuildable annotation-head projection: the latest version + anchor + segments."""

        with self.connection() as connection:
            ann = connection.execute(
                "SELECT * FROM source_annotations WHERE id = ?", (annotation_id,)
            ).fetchone()
            if ann is None:
                return None
            version = connection.execute(
                "SELECT * FROM source_annotation_versions WHERE annotation_id = ? "
                "ORDER BY version_ordinal DESC LIMIT 1",
                (annotation_id,),
            ).fetchone()
            anchor = connection.execute(
                "SELECT * FROM source_annotation_anchor_versions WHERE annotation_id = ? "
                "ORDER BY version_ordinal DESC LIMIT 1",
                (annotation_id,),
            ).fetchone()
            segments: list[dict[str, Any]] = []
            if anchor is not None:
                seg_rows = connection.execute(
                    "SELECT * FROM source_annotation_anchor_segments WHERE anchor_version_id = ? "
                    "ORDER BY segment_ordinal",
                    (anchor["id"],),
                ).fetchall()
                segments = [dict(row) for row in seg_rows]
        return {
            "annotation": dict(ann),
            "version": dict(version) if version is not None else None,
            "anchor": dict(anchor) if anchor is not None else None,
            "segments": segments,
        }

    def annotations_for_source(self, source_id: str) -> list[dict[str, Any]]:
        """Annotation heads for a source, omitting delete-intended annotations.

        Deletion is a tombstone disposition event (§4.1) — history keeps every
        version and event, but the reading-surface listing honors the learner's
        delete intent."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT id FROM source_annotations WHERE source_id = ? "
                "AND id NOT IN ("
                "  SELECT annotation_id FROM source_annotation_events"
                "  WHERE event_type = 'delete_intent'"
                ") ORDER BY created_at, id",
                (source_id,),
            ).fetchall()
        return [self.annotation_head(row["id"]) for row in rows]

    def search_source_blocks(
        self, *, query: str, extraction_ids: Sequence[str], limit: int = 80
    ) -> list[dict[str, Any]]:
        """Case-insensitive substring search over document blocks of the given
        extractions (no FTS index exists; ``instr`` over ``text`` is adequate at
        local-vault scale). Ordered by extraction then document order."""

        needle = (query or "").strip().lower()
        ids = tuple(dict.fromkeys(extraction_id for extraction_id in extraction_ids if extraction_id))
        if not needle or not ids:
            return []
        marks = ", ".join("?" for _ in ids)
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT extraction_id, span_id, text, section_path_json, ordinal, page "
                f"FROM source_document_blocks WHERE extraction_id IN ({marks}) "
                "AND block_type NOT IN ('PageHeader', 'PageFooter', 'TableOfContents') "
                "AND instr(lower(text), ?) > 0 "
                "ORDER BY extraction_id, ordinal LIMIT ?",
                (*ids, needle, int(limit)),
            ).fetchall()
        return [dict(row) for row in rows]

    def annotation_history(self, annotation_id: str) -> dict[str, Any]:
        with self.connection() as connection:
            versions = [
                dict(r)
                for r in connection.execute(
                    "SELECT * FROM source_annotation_versions WHERE annotation_id = ? "
                    "ORDER BY version_ordinal",
                    (annotation_id,),
                ).fetchall()
            ]
            anchors = [
                dict(r)
                for r in connection.execute(
                    "SELECT * FROM source_annotation_anchor_versions WHERE annotation_id = ? "
                    "ORDER BY version_ordinal",
                    (annotation_id,),
                ).fetchall()
            ]
            events = [
                dict(r)
                for r in connection.execute(
                    "SELECT * FROM source_annotation_events WHERE annotation_id = ? "
                    "ORDER BY created_at, id",
                    (annotation_id,),
                ).fetchall()
            ]
        return {"versions": versions, "anchors": anchors, "events": events}

    def append_annotation_event(
        self, *, annotation_id: str, event_type: str, payload: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> str:
        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO source_annotation_events(id, annotation_id, event_type, payload_json, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (event_id, annotation_id, event_type, _json(dict(payload or {})), utc_now_iso(clock)),
            )
            connection.commit()
        return event_id

    def _write_annotation_version(
        self, connection: sqlite3.Connection, *, annotation_id: str, version_ordinal: int,
        version: Mapping[str, Any], now: str,
    ) -> str:
        version_id = new_ulid()
        connection.execute(
            """
            INSERT INTO source_annotation_versions(
              id, annotation_id, version_ordinal, annotation_type, learner_text,
              what_i_think_is_going_on, privacy_locality, authorship,
              client_idempotency_key, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version_id,
                annotation_id,
                version_ordinal,
                version["annotation_type"],
                version.get("learner_text", ""),
                version.get("what_i_think_is_going_on"),
                version.get("privacy_locality", "local_private"),
                version.get("authorship", "learner"),
                version.get("client_idempotency_key"),
                now,
            ),
        )
        return version_id

    def _write_anchor_version(
        self, connection: sqlite3.Connection, *, annotation_id: str, version_ordinal: int,
        anchor: Mapping[str, Any], now: str,
    ) -> str:
        anchor_id = new_ulid()
        connection.execute(
            """
            INSERT INTO source_annotation_anchor_versions(
              id, annotation_id, version_ordinal, source_id, revision_id, extraction_id,
              render_view_id, status, algo_version, confidence, raw_selection_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                anchor_id,
                annotation_id,
                version_ordinal,
                anchor["source_id"],
                anchor["revision_id"],
                anchor["extraction_id"],
                anchor.get("render_view_id"),
                anchor["status"],
                anchor.get("algo_version", "anchor-v1"),
                anchor.get("confidence"),
                _json(anchor["raw_selection"]) if anchor.get("raw_selection") is not None else None,
                now,
            ),
        )
        for seg_ordinal, seg in enumerate(anchor.get("segments", [])):
            connection.execute(
                """
                INSERT INTO source_annotation_anchor_segments(
                  id, anchor_version_id, segment_ordinal, span_id, block_content_hash,
                  codepoint_start, codepoint_end, exact_quote, prefix, suffix,
                  geometry_json, section_path_json, neighbor_hashes_json,
                  selection_text_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_ulid(),
                    anchor_id,
                    seg_ordinal,
                    seg["span_id"],
                    seg["block_content_hash"],
                    seg["codepoint_start"],
                    seg["codepoint_end"],
                    seg["exact_quote"],
                    seg.get("prefix", ""),
                    seg.get("suffix", ""),
                    _json(seg["geometry"]) if seg.get("geometry") is not None else None,
                    _json(seg.get("section_path", [])),
                    _json(seg.get("neighbor_hashes", [])),
                    seg["selection_text_hash"],
                    now,
                ),
            )
        return anchor_id

    def append_annotation_version(
        self, *, annotation_id: str, version: Mapping[str, Any], anchor: Mapping[str, Any],
        event_type: str = "edit", event_payload: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> dict[str, str]:
        now = utc_now_iso(clock)
        ordinal = self.next_annotation_version_ordinal(annotation_id)
        with self.connection() as connection:
            version_id = self._write_annotation_version(
                connection, annotation_id=annotation_id, version_ordinal=ordinal, version=version, now=now
            )
            anchor_id = self._write_anchor_version(
                connection, annotation_id=annotation_id, version_ordinal=ordinal, anchor=anchor, now=now
            )
            event_id = new_ulid()
            connection.execute(
                "INSERT INTO source_annotation_events(id, annotation_id, event_type, payload_json, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (event_id, annotation_id, event_type, _json(dict(event_payload or {})), now),
            )
            connection.commit()
        return {"version_id": version_id, "anchor_id": anchor_id, "event_id": event_id, "version_ordinal": str(ordinal)}

    # -- capture outbox (§5.3) --

    def capture_by_client_key(self, client_idempotency_key: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM reader_capture_outbox WHERE client_idempotency_key = ?",
                (client_idempotency_key,),
            ).fetchone()
        return dict(row) if row is not None else None

    def capture_local_transaction(
        self,
        *,
        source_id: str,
        client_idempotency_key: str,
        annotation: Mapping[str, Any] | None,
        anchor: Mapping[str, Any] | None,
        interaction_event: Mapping[str, Any],
        outbox: Mapping[str, Any],
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """The one local-first capture transaction (§5.3): create annotation +
        version + anchor + segments, append the typed interaction event, and write
        ONE durable outbox row -- all in a SINGLE SQLite transaction. On any error
        the whole thing rolls back (no acknowledgement, no orphan). Idempotent on
        client_idempotency_key: a retry returns the existing receipt untouched."""

        existing = self.capture_by_client_key(client_idempotency_key)
        if existing is not None:
            return {
                "annotation_id": existing["annotation_id"],
                "outbox_id": existing["id"],
                "interaction_event_id": existing["interaction_event_id"],
                "deduplicated": True,
            }

        now = utc_now_iso(clock)
        annotation_id: str | None = None
        event_id = new_ulid()
        outbox_id = new_ulid()
        connection = self.connection()
        try:
            connection.execute("BEGIN")
            if annotation is not None and anchor is not None:
                annotation_id = new_ulid()
                connection.execute(
                    "INSERT INTO source_annotations(id, source_id, created_at) VALUES (?, ?, ?)",
                    (annotation_id, source_id, now),
                )
                self._write_annotation_version(
                    connection, annotation_id=annotation_id, version_ordinal=1,
                    version=annotation, now=now,
                )
                self._write_anchor_version(
                    connection, annotation_id=annotation_id, version_ordinal=1, anchor=anchor, now=now
                )
                connection.execute(
                    "INSERT INTO source_annotation_events(id, annotation_id, event_type, payload_json, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (new_ulid(), annotation_id, "create", _json({"capture": True}), now),
                )
            ev = dict(interaction_event)
            connection.execute(
                """
                INSERT INTO interaction_events(
                  id, kind, subject_type, subject_id, administration_id, surface_id,
                  attempt_id, affect_tap_kind, attempt_duration_ms, payload_json,
                  origin, created_at, occurred_at, received_at, actor, client_id,
                  session_id, visit_id, payload_schema_version, source_id, revision_id,
                  render_view_id, locator_json, annotation_id, commitment_id, activity_id,
                  payload_hash, client_idempotency_key, privacy_locality, consent_context,
                  producer_version, app_version, policy_version, supersedes_event_id
                ) VALUES (?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, ?, ?, ?, ?, ?, NULL,
                          NULL, ?, NULL, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, NULL,
                          NULL, NULL, NULL, NULL)
                """,
                (
                    event_id,
                    ev["kind"],
                    ev.get("subject_type"),
                    ev.get("subject_id"),
                    _json(ev.get("payload", {})),
                    ev.get("origin", "learner"),
                    now,
                    now,
                    now,
                    ev.get("session_id"),
                    ev.get("payload_schema_version", "reader-capture-v1"),
                    source_id,
                    ev.get("revision_id"),
                    ev.get("render_view_id"),
                    _json(ev["locator"]) if ev.get("locator") is not None else None,
                    annotation_id,
                    ev.get("payload_hash"),
                    client_idempotency_key,
                    ev.get("privacy_locality", "local_private"),
                ),
            )
            connection.execute(
                """
                INSERT INTO reader_capture_outbox(
                  id, client_idempotency_key, capture_kind, state, payload_json,
                  annotation_id, commitment_id, source_id, revision_id, render_view_id,
                  interaction_event_id, target_ref, attempts, last_error,
                  created_at, updated_at, drained_at
                ) VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, NULL, 0, NULL, ?, ?, NULL)
                """,
                (
                    outbox_id,
                    client_idempotency_key,
                    outbox["capture_kind"],
                    _json(outbox.get("payload", {})),
                    annotation_id,
                    outbox.get("commitment_id"),
                    source_id,
                    outbox.get("revision_id"),
                    outbox.get("render_view_id"),
                    event_id,
                    now,
                    now,
                ),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return {
            "annotation_id": annotation_id,
            "outbox_id": outbox_id,
            "interaction_event_id": event_id,
            "deduplicated": False,
        }

    def pending_capture_outbox(self, *, limit: int = 100) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM reader_capture_outbox WHERE state = 'pending' "
                "ORDER BY created_at, id LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def recoverable_capture_outbox(self, *, limit: int = 100) -> list[dict[str, Any]]:
        """Rows a drain may claim: `pending` plus stale `draining` rows left behind
        by a crash mid-drain. Reclaiming a `draining` row is safe because conversion
        is idempotent (§15.2)."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM reader_capture_outbox WHERE state IN ('pending', 'draining') "
                "ORDER BY created_at, id LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_capture_outbox(self, outbox_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM reader_capture_outbox WHERE id = ?", (outbox_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def mark_capture_outbox(
        self, outbox_id: str, *, state: str, target_ref: str | None = None,
        last_error: str | None = None, bump_attempts: bool = False, clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        drained = now if state == "done" else None
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE reader_capture_outbox
                SET state = ?, target_ref = COALESCE(?, target_ref), last_error = ?,
                    attempts = attempts + ?, updated_at = ?,
                    drained_at = COALESCE(?, drained_at)
                WHERE id = ?
                """,
                (state, target_ref, last_error, 1 if bump_attempts else 0, now, drained, outbox_id),
            )
            connection.commit()

    # ------------------------------------------------------------------
    # P3 slice 2: reader_background_requests (demand-paged synthesis, §6).
    # Fenced-lease durable queue -- mirrors the migration-080 surface-mint
    # precedent (lease_epoch bumped on claim; guarded writes fenced on it).
    # ------------------------------------------------------------------

    _READER_REQUEST_TERMINAL = ("complete", "failed", "cancelled", "obsolete")

    def enqueue_reader_request(
        self, *, request_key: str, fields: Mapping[str, Any], clock: Clock | None = None
    ) -> dict[str, Any]:
        """Idempotent enqueue keyed on ``request_key`` (§6.2): the same contract reuses
        the standing row; a material version change has a different key -> a new row."""

        existing = self.reader_request_by_key(request_key)
        if existing is not None:
            return {"id": existing["id"], "deduplicated": True, "status": existing["status"]}
        now = utc_now_iso(clock)
        request_id = new_ulid()
        cols = {
            "id": request_id,
            "request_key": request_key,
            "source_id": fields["source_id"],
            "revision_id": fields["revision_id"],
            "extraction_id": fields["extraction_id"],
            "span_id": fields.get("span_id", ""),
            "window_json": _json(fields.get("window", {})),
            "preset": fields.get("preset", ""),
            "action": fields.get("action", ""),
            "inventory_profile": fields.get("inventory_profile", "semantic"),
            "inventory_schema_version": fields.get("inventory_schema_version", ""),
            "synthesis_schema_version": fields.get("synthesis_schema_version", ""),
            "prompt_version": fields.get("prompt_version", ""),
            "provider": fields.get("provider", ""),
            "model": fields.get("model", ""),
            "config_hash": fields.get("config_hash", ""),
            "priority_band": int(fields.get("priority_band", 0)),
            "est_input_tokens": int(fields.get("est_input_tokens", 0)),
            "est_output_tokens": int(fields.get("est_output_tokens", 0)),
            "token_cap": int(fields.get("token_cap", 0)),
            "cache_hit": 1 if fields.get("cache_hit") else 0,
            "reason": fields.get("reason"),
            "annotation_id": fields.get("annotation_id"),
            "commitment_id": fields.get("commitment_id"),
            "client_idempotency_key": fields.get("client_idempotency_key"),
            "created_at": now,
            "updated_at": now,
        }
        placeholders = ", ".join("?" for _ in cols)
        try:
            with self.connection() as connection:
                connection.execute(
                    f"INSERT INTO reader_background_requests({', '.join(cols)}) VALUES ({placeholders})",
                    tuple(cols.values()),
                )
                connection.commit()
        except sqlite3.IntegrityError:
            existing = self.reader_request_by_key(request_key)
            if existing is not None:
                return {"id": existing["id"], "deduplicated": True, "status": existing["status"]}
            raise
        return {"id": request_id, "deduplicated": False, "status": "queued"}

    def has_queued_reader_requests(self) -> bool:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT 1 FROM reader_background_requests WHERE status = 'queued' LIMIT 1"
            ).fetchone()
        return row is not None

    def reader_request_by_key(self, request_key: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM reader_background_requests WHERE request_key = ?", (request_key,)
            ).fetchone()
        return dict(row) if row is not None else None

    def get_reader_request(self, request_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM reader_background_requests WHERE id = ?", (request_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def reader_requests_for_source(self, source_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM reader_background_requests WHERE source_id = ? "
                "ORDER BY created_at, id",
                (source_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def claim_next_reader_request(
        self, *, worker_id: str, now_iso: str, lease_expires_at: str, lease_cutoff_iso: str
    ) -> dict[str, Any] | None:
        """Claim the highest-priority runnable request under a fenced lease. Bumps
        ``lease_epoch`` so a stale worker's later write is rejected. Only one live
        lease at a time (BEGIN IMMEDIATE + live-lease guard)."""

        connection = self.connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            live = connection.execute(
                "SELECT 1 FROM reader_background_requests "
                "WHERE status = 'running' AND lease_expires_at IS NOT NULL AND lease_expires_at >= ? LIMIT 1",
                (lease_cutoff_iso,),
            ).fetchone()
            if live is not None:
                connection.rollback()
                return None
            row = connection.execute(
                "SELECT * FROM reader_background_requests "
                "WHERE cancel_requested = 0 AND (status = 'queued' OR "
                "      (status = 'running' AND (lease_expires_at IS NULL OR lease_expires_at < ?))) "
                "ORDER BY priority_band DESC, created_at, id LIMIT 1",
                (lease_cutoff_iso,),
            ).fetchone()
            if row is None:
                connection.rollback()
                return None
            connection.execute(
                "UPDATE reader_background_requests "
                "SET status = 'running', lease_owner = ?, lease_expires_at = ?, "
                "    lease_epoch = lease_epoch + 1, attempt_count = attempt_count + 1, updated_at = ? "
                "WHERE id = ?",
                (worker_id, lease_expires_at, now_iso, row["id"]),
            )
            claimed = connection.execute(
                "SELECT * FROM reader_background_requests WHERE id = ?", (row["id"],)
            ).fetchone()
            connection.commit()
            return dict(claimed)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def resolve_reader_request(
        self, *, request_id: str, status: str, result: Mapping[str, Any] | None = None,
        error: Mapping[str, Any] | None = None, actual_input_tokens: int = 0,
        actual_output_tokens: int = 0, cache_hit: bool = False,
        expected_lease_epoch: int | None = None, clock: Clock | None = None,
    ) -> bool:
        """Terminal/complete transition; releases the lease. A stale-epoch write (the
        job was re-claimed by another worker) matches zero rows and returns False."""

        now = utc_now_iso(clock)
        completed = now if status in self._READER_REQUEST_TERMINAL else None
        clauses = ["id = ?", "status = 'running'"]
        params: list[Any] = [
            status, _json(result or {}), _json(error) if error is not None else None,
            int(actual_input_tokens), int(actual_output_tokens), 1 if cache_hit else 0, now, completed,
            request_id,
        ]
        if expected_lease_epoch is not None:
            clauses.append("lease_epoch = ?")
            params.append(expected_lease_epoch)
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE reader_background_requests "
                "SET status = ?, result_json = ?, error_json = ?, "
                "    actual_input_tokens = ?, actual_output_tokens = ?, cache_hit = ?, "
                "    lease_owner = NULL, lease_expires_at = NULL, updated_at = ?, completed_at = ? "
                f"WHERE {' AND '.join(clauses)}",
                tuple(params),
            )
            connection.commit()
            return cursor.rowcount > 0

    def cancel_reader_request(self, request_id: str, *, clock: Clock | None = None) -> dict[str, Any] | None:
        """Request cancellation. Never touches the local capture (§6.2). A non-terminal
        request flips to ``cancelled``; a running one is flagged so the worker stops."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                "UPDATE reader_background_requests "
                "SET cancel_requested = 1, "
                "    status = CASE WHEN status IN ('queued') THEN 'cancelled' ELSE status END, "
                "    updated_at = ? WHERE id = ? AND status NOT IN ('complete','failed','cancelled','obsolete')",
                (now, request_id),
            )
            connection.commit()
        return self.get_reader_request(request_id)

    def retry_reader_request(self, request_id: str, *, clock: Clock | None = None) -> dict[str, Any] | None:
        """Reset a failed request to ``queued`` for another drain."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                "UPDATE reader_background_requests "
                "SET status = 'queued', cancel_requested = 0, lease_owner = NULL, "
                "    lease_expires_at = NULL, error_json = NULL, updated_at = ? "
                "WHERE id = ? AND status = 'failed'",
                (now, request_id),
            )
            connection.commit()
        return self.get_reader_request(request_id)

    # ------------------------------------------------------------------
    # Reader quick-check producer: AI-authored section-boundary questions
    # (migration 105). The row is the record — statuses live here, never on
    # new interaction-event kinds; answering never touches attempts/mastery.
    # ------------------------------------------------------------------

    def insert_reader_authored_question(
        self, *, fields: Mapping[str, Any], clock: Clock | None = None
    ) -> str:
        now = utc_now_iso(clock)
        question_id = f"raq_{new_ulid()}"
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO reader_authored_questions("
                "  id, extraction_id, section_id, source_id, question_md,"
                "  expected_answer_md, span_ids_json, prompt_version, provider,"
                "  model, status, created_at, updated_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'proposed', ?, ?)",
                (
                    question_id,
                    fields["extraction_id"],
                    fields["section_id"],
                    fields.get("source_id"),
                    fields["question_md"],
                    fields["expected_answer_md"],
                    _json(list(fields.get("span_ids") or [])),
                    fields.get("prompt_version", ""),
                    fields.get("provider"),
                    fields.get("model"),
                    now,
                    now,
                ),
            )
            connection.commit()
        return question_id

    def get_reader_authored_question(self, question_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM reader_authored_questions WHERE id = ?", (question_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    # --- reader section progress (migration 106; reader-first seeding) --------

    def upsert_reader_section_progress(
        self,
        *,
        extraction_id: str,
        section_id: str,
        spans_seen: int | None = None,
        span_count: int | None = None,
        revealed: bool = False,
        completed: bool = False,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Monotone upsert: spans_seen/span_count only grow; revealed_at /
        completed_at stamp once and never clear; generation_batch_id untouched."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO reader_section_progress(
                  extraction_id, section_id, spans_seen, span_count,
                  revealed_at, completed_at, generation_batch_id, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, NULL, ?)
                ON CONFLICT(extraction_id, section_id) DO UPDATE SET
                  spans_seen = MAX(reader_section_progress.spans_seen, excluded.spans_seen),
                  span_count = MAX(reader_section_progress.span_count, excluded.span_count),
                  revealed_at = COALESCE(reader_section_progress.revealed_at, excluded.revealed_at),
                  completed_at = COALESCE(reader_section_progress.completed_at, excluded.completed_at),
                  updated_at = excluded.updated_at
                """,
                (
                    extraction_id,
                    section_id,
                    int(spans_seen or 0),
                    int(span_count or 0),
                    now if revealed else None,
                    now if completed else None,
                    now,
                ),
            )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM reader_section_progress WHERE extraction_id = ? AND section_id = ?",
                (extraction_id, section_id),
            ).fetchone()
        return dict(row)

    def reader_section_progress_for(self, extraction_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM reader_section_progress WHERE extraction_id = ? ORDER BY section_id",
                (extraction_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def mark_section_generation(
        self, *, extraction_id: str, section_id: str, batch_id: str, clock: Clock | None = None
    ) -> bool:
        """Stamp the generation batch id exactly once. Returns False when a
        stamp already exists (the trigger's idempotence check)."""

        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE reader_section_progress
                SET generation_batch_id = ?, updated_at = ?
                WHERE extraction_id = ? AND section_id = ? AND generation_batch_id IS NULL
                """,
                (batch_id, utc_now_iso(clock), extraction_id, section_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    def set_section_generation_batch(
        self, *, extraction_id: str, section_id: str, batch_id: str, clock: Clock | None = None
    ) -> None:
        """Unconditional stamp update (replaces the 'enqueuing' placeholder with
        the real batch id after a successful enqueue)."""

        with self.connection() as connection:
            connection.execute(
                """
                UPDATE reader_section_progress
                SET generation_batch_id = ?, updated_at = ?
                WHERE extraction_id = ? AND section_id = ?
                """,
                (batch_id, utc_now_iso(clock), extraction_id, section_id),
            )
            connection.commit()

    def reader_authored_questions_for_extraction(
        self, extraction_id: str
    ) -> list[dict[str, Any]]:
        """All authored questions for an extraction, newest first per section."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM reader_authored_questions WHERE extraction_id = ? "
                "ORDER BY section_id, created_at DESC, id DESC",
                (extraction_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def latest_reader_authored_question(
        self, *, extraction_id: str, section_id: str
    ) -> dict[str, Any] | None:
        """The newest authored question for one section, any status — the
        idempotency anchor: a dismissed row suppresses re-authoring."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM reader_authored_questions "
                "WHERE extraction_id = ? AND section_id = ? "
                "ORDER BY created_at DESC, id DESC LIMIT 1",
                (extraction_id, section_id),
            ).fetchone()
        return dict(row) if row is not None else None

    def transition_reader_authored_question(
        self,
        *,
        question_id: str,
        status: str,
        response_md: str | None = None,
        practice_item_id: str | None = None,
        clock: Clock | None = None,
    ) -> bool:
        """Row-status transition (proposed -> answered | dismissed | escalated).
        ``answered`` stamps the response; ``escalated`` pins the minted item."""

        now = utc_now_iso(clock)
        sets = ["status = ?", "updated_at = ?"]
        params: list[Any] = [status, now]
        if response_md is not None:
            sets.append("response_md = ?")
            params.append(response_md)
        if status == "answered":
            sets.append("answered_at = ?")
            params.append(now)
        if practice_item_id is not None:
            sets.append("practice_item_id = ?")
            params.append(practice_item_id)
        params.append(question_id)
        with self.connection() as connection:
            cursor = connection.execute(
                f"UPDATE reader_authored_questions SET {', '.join(sets)} WHERE id = ?",
                tuple(params),
            )
            connection.commit()
            return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # P3 slice 2: source objects, relations, canonical mapping proposals (§7).
    # ------------------------------------------------------------------

    def create_source_object(self, *, source_id: str, clock: Clock | None = None) -> str:
        object_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO source_objects(id, source_id, created_at) VALUES (?, ?, ?)",
                (object_id, source_id, utc_now_iso(clock)),
            )
            connection.commit()
        return object_id

    def append_source_object_version(
        self, *, source_object_id: str, version: Mapping[str, Any],
        citations: list[Mapping[str, Any]] | None = None, clock: Clock | None = None,
    ) -> dict[str, Any]:
        now = utc_now_iso(clock)
        version_id = new_ulid()
        connection = self.connection()
        try:
            connection.execute("BEGIN")
            ordinal_row = connection.execute(
                "SELECT COALESCE(MAX(version_ordinal), 0) AS m FROM source_object_versions "
                "WHERE source_object_id = ?",
                (source_object_id,),
            ).fetchone()
            version_ordinal = int(ordinal_row["m"]) + 1
            connection.execute(
                """
                INSERT INTO source_object_versions(
                  id, source_object_id, version_ordinal, revision_id, object_type,
                  authorial_role, salience_proposal, exact_text, content_json,
                  authorship, model_provenance_json, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id, source_object_id, version_ordinal, version["revision_id"],
                    version["object_type"], version.get("authorial_role"),
                    version.get("salience_proposal"), version.get("exact_text", ""),
                    _json(version.get("content", {})), version.get("authorship", "ai"),
                    _json(version["model_provenance"]) if version.get("model_provenance") is not None else None,
                    version.get("status", "proposed"), now,
                ),
            )
            for i, cite in enumerate(citations or [], start=1):
                connection.execute(
                    "INSERT INTO source_object_citations("
                    "id, source_object_version_id, citation_ordinal, revision_id, span_id, "
                    "block_content_hash, exact_quote, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        new_ulid(), version_id, i, cite.get("revision_id", version["revision_id"]),
                        cite["span_id"], cite.get("block_content_hash"), cite.get("exact_quote"), now,
                    ),
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return {"version_id": version_id, "version_ordinal": version_ordinal}

    def source_object_head(self, source_object_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            obj = connection.execute(
                "SELECT * FROM source_objects WHERE id = ?", (source_object_id,)
            ).fetchone()
            if obj is None:
                return None
            version = connection.execute(
                "SELECT * FROM source_object_versions WHERE source_object_id = ? "
                "ORDER BY version_ordinal DESC LIMIT 1",
                (source_object_id,),
            ).fetchone()
            citations: list[dict[str, Any]] = []
            if version is not None:
                citations = [
                    dict(r)
                    for r in connection.execute(
                        "SELECT * FROM source_object_citations WHERE source_object_version_id = ? "
                        "ORDER BY citation_ordinal",
                        (version["id"],),
                    ).fetchall()
                ]
        return {
            "object": dict(obj),
            "version": dict(version) if version is not None else None,
            "citations": citations,
        }

    def source_objects_for_source(self, source_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT id FROM source_objects WHERE source_id = ? ORDER BY created_at, id",
                (source_id,),
            ).fetchall()
        return [self.source_object_head(r["id"]) for r in rows]

    def create_source_object_relation(
        self, *, source_object_id: str, related_object_id: str | None, relation_type: str,
        learner_text: str | None = None, authorship: str = "learner",
        review_status: str = "proposed", clock: Clock | None = None,
    ) -> str:
        relation_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO source_object_relations("
                "id, source_object_id, related_object_id, version_ordinal, relation_type, "
                "learner_text, authorship, review_status, created_at) "
                "VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?)",
                (
                    relation_id, source_object_id, related_object_id, relation_type,
                    learner_text, authorship, review_status, utc_now_iso(clock),
                ),
            )
            connection.commit()
        return relation_id

    def relations_for_object(self, source_object_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_object_relations WHERE source_object_id = ? "
                "ORDER BY created_at, id",
                (source_object_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def create_mapping_proposal(
        self, *, source_object_id: str | None = None, annotation_id: str | None = None,
        target_kind: str, target_ref: str | None = None, confidence: float | None = None,
        rationale: str | None = None, provenance: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> str:
        proposal_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO canonical_mapping_proposals("
                "id, source_object_id, annotation_id, target_kind, target_ref, confidence, "
                "status, rationale, provenance_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, 'proposed', ?, ?, ?)",
                (
                    proposal_id, source_object_id, annotation_id, target_kind, target_ref,
                    confidence, rationale, _json(provenance or {}), utc_now_iso(clock),
                ),
            )
            connection.commit()
        return proposal_id

    def mapping_proposals(
        self, *, status: str | None = None, source_object_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        if source_object_id is not None:
            clauses.append("source_object_id = ?")
            params.append(source_object_id)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM canonical_mapping_proposals{where} ORDER BY created_at, id",
                tuple(params),
            ).fetchall()
        return [dict(r) for r in rows]

    def decide_mapping_proposal(
        self, *, proposal_id: str, status: str, clock: Clock | None = None
    ) -> dict[str, Any] | None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                "UPDATE canonical_mapping_proposals SET status = ?, decided_at = ? "
                "WHERE id = ? AND status = 'proposed'",
                (status, now, proposal_id),
            )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM canonical_mapping_proposals WHERE id = ?", (proposal_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def set_source_object_status(
        self, *, source_object_id: str, status: str, clock: Clock | None = None
    ) -> dict[str, Any]:
        """Append a status-only successor version carrying the head content forward."""

        head = self.source_object_head(source_object_id)
        if head is None or head["version"] is None:
            raise ValueError(f"unknown source object: {source_object_id!r}")
        prev = head["version"]
        result = self.append_source_object_version(
            source_object_id=source_object_id,
            version={
                "revision_id": prev["revision_id"],
                "object_type": prev["object_type"],
                "authorial_role": prev.get("authorial_role"),
                "salience_proposal": prev.get("salience_proposal"),
                "exact_text": prev.get("exact_text", ""),
                "content": json.loads(prev.get("content_json") or "{}"),
                "authorship": prev.get("authorship", "ai"),
                "status": status,
            },
            citations=[
                {"revision_id": c["revision_id"], "span_id": c["span_id"],
                 "block_content_hash": c.get("block_content_hash"), "exact_quote": c.get("exact_quote")}
                for c in head["citations"]
            ],
            clock=clock,
        )
        return {"source_object_id": source_object_id, "status": status, **result}

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
            connection.execute("BEGIN")
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
            connection.execute("BEGIN")
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

    def arcs_for_source(self, source_id: str) -> list[str]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT id FROM commitment_arcs WHERE source_id = ? ORDER BY created_at, id",
                (source_id,),
            ).fetchall()
        return [r["id"] for r in rows]

    def append_measurement_event(
        self,
        *,
        administration_id: str,
        kind: str,
        algorithm_version: str,
        observation_id: str | None = None,
        payload_json: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        if kind not in _MEASUREMENT_EVENT_KINDS:
            raise ValueError(f"unknown measurement_event kind: {kind!r}")
        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO measurement_events(
                  id, administration_id, observation_id, kind, algorithm_version,
                  payload_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    administration_id,
                    observation_id,
                    kind,
                    algorithm_version,
                    payload_json,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return event_id

    def measurement_events_for_administration(
        self, administration_id: str
    ) -> list[dict[str, Any]]:
        """The administration's measurement events in append order (ledger read)."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM measurement_events
                 WHERE administration_id = ?
                 ORDER BY created_at, id
                """,
                (administration_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # P0.2 grader channel (spec_p0_measurement_correctness §3.1-§3.3, §4.7).
    # All INSERT-only; model/schema/event rows never receive an UPDATE. The two
    # exceptions are pure projection-head pointers on activity_observations
    # (active_interpretation_id) which are not append-only event tables.
    # ------------------------------------------------------------------

    def ensure_outcome_schema(
        self, *, slug: str, kind: str, clock: Clock | None = None
    ) -> str:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT id FROM outcome_schemas WHERE slug = ?", (slug,)
            ).fetchone()
            if row is not None:
                return row["id"]
            schema_id = new_ulid()
            connection.execute(
                "INSERT INTO outcome_schemas(id, slug, kind, created_at) VALUES (?, ?, ?, ?)",
                (schema_id, slug, kind, utc_now_iso(clock)),
            )
            connection.commit()
            return schema_id

    def ensure_outcome_schema_version(
        self,
        *,
        schema_id: str,
        version: int,
        observed_classes_json: str,
        true_classes_json: str,
        has_signature_error: bool,
        has_unanswered: bool,
        score_fraction_json: str,
        content_hash: str,
        clock: Clock | None = None,
    ) -> str:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT id FROM outcome_schema_versions WHERE schema_id = ? AND content_hash = ?",
                (schema_id, content_hash),
            ).fetchone()
            if row is not None:
                return row["id"]
            version_id = new_ulid()
            connection.execute(
                """
                INSERT INTO outcome_schema_versions(
                  id, schema_id, version, observed_classes_json, true_classes_json,
                  has_signature_error, has_unanswered, score_fraction_json,
                  content_hash, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    schema_id,
                    version,
                    observed_classes_json,
                    true_classes_json,
                    1 if has_signature_error else 0,
                    1 if has_unanswered else 0,
                    score_fraction_json,
                    content_hash,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
            return version_id

    def fetch_outcome_schema_version(
        self, *, slug: str, version: int | None = None
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            if version is None:
                row = connection.execute(
                    """
                    SELECT v.* FROM outcome_schema_versions v
                      JOIN outcome_schemas s ON s.id = v.schema_id
                     WHERE s.slug = ?
                     ORDER BY v.version DESC LIMIT 1
                    """,
                    (slug,),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT v.* FROM outcome_schema_versions v
                      JOIN outcome_schemas s ON s.id = v.schema_id
                     WHERE s.slug = ? AND v.version = ?
                    """,
                    (slug, version),
                ).fetchone()
        return dict(row) if row is not None else None

    def fetch_outcome_schema_version_by_id(self, schema_id: str, version: int) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM outcome_schema_versions WHERE schema_id = ? AND version = ?",
                (schema_id, version),
            ).fetchone()
        return dict(row) if row is not None else None

    def find_calibration_model_by_hash(self, content_hash: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM grader_calibration_models WHERE content_hash = ? LIMIT 1",
                (content_hash,),
            ).fetchone()
        return dict(row) if row is not None else None

    def insert_calibration_model(
        self, *, model: Mapping[str, Any], alphas: Mapping[str, Mapping[str, float]],
        clock: Clock | None = None,
    ) -> str:
        """Insert one immutable model version + its per-Z Dirichlet alpha rows.

        Content-addressed: short-circuits on an existing ``content_hash`` (M1) so a
        check-then-act race can never mint a duplicate immutable model. The
        UNIQUE(content_hash) backstop (migration 070) is the hard guarantee."""

        existing = self.find_calibration_model_by_hash(model["content_hash"])
        if existing is not None:
            return existing["id"]

        model_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO grader_calibration_models(
                  id, grader_provider, grader_model_revision, grading_prompt_version,
                  grader_output_schema_version, grader_identity_hash, semver,
                  parent_model_id, content_hash, scope_level, outcome_schema_id,
                  outcome_schema_version, domain, length_bucket, backoff_chain_json,
                  status, count_heuristic_prior, count_planted_sim, count_exploratory_em,
                  count_adjudicated_anchor, count_held_out_evaluation,
                  prequential_log_loss, multiclass_brier, reliability_bins_json,
                  sample_count, eval_time_range_json, prior_concentration,
                  provenance_json, evidence_manifest_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model_id,
                    model.get("grader_provider"),
                    model.get("grader_model_revision"),
                    model.get("grading_prompt_version"),
                    model.get("grader_output_schema_version"),
                    model.get("grader_identity_hash"),
                    model["semver"],
                    model.get("parent_model_id"),
                    model["content_hash"],
                    model["scope_level"],
                    model.get("outcome_schema_id"),
                    model.get("outcome_schema_version"),
                    model.get("domain"),
                    model.get("length_bucket"),
                    model["backoff_chain_json"],
                    model["status"],
                    int(model.get("count_heuristic_prior", 0)),
                    int(model.get("count_planted_sim", 0)),
                    int(model.get("count_exploratory_em", 0)),
                    int(model.get("count_adjudicated_anchor", 0)),
                    int(model.get("count_held_out_evaluation", 0)),
                    model.get("prequential_log_loss"),
                    model.get("multiclass_brier"),
                    model.get("reliability_bins_json"),
                    model.get("sample_count"),
                    model.get("eval_time_range_json"),
                    model.get("prior_concentration"),
                    model.get("provenance_json"),
                    model.get("evidence_manifest_json"),
                    now,
                ),
            )
            for true_class, alpha in alphas.items():
                connection.execute(
                    """
                    INSERT INTO grader_calibration_alphas(
                      id, model_id, true_class, alpha_json, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (new_ulid(), model_id, true_class, _json(dict(alpha)), now),
                )
            connection.commit()
        return model_id

    def fetch_calibration_model(self, model_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM grader_calibration_models WHERE id = ?", (model_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def fetch_calibration_alphas(self, model_id: str) -> dict[str, dict[str, float]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT true_class, alpha_json FROM grader_calibration_alphas WHERE model_id = ?",
                (model_id,),
            ).fetchall()
        return {row["true_class"]: _loads(row["alpha_json"], {}) for row in rows}

    def find_calibration_models(
        self,
        *,
        scope_level: str | None = None,
        grader_identity_hash: Any = _UNSET,
        outcome_schema_id: Any = _UNSET,
        outcome_schema_version: Any = _UNSET,
        domain: Any = _UNSET,
        length_bucket: Any = _UNSET,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if scope_level is not None:
            clauses.append("scope_level = ?")
            params.append(scope_level)
        if grader_identity_hash is not _UNSET:
            clauses.append("grader_identity_hash IS ?" if grader_identity_hash is None else "grader_identity_hash = ?")
            params.append(grader_identity_hash)
        if outcome_schema_id is not _UNSET:
            clauses.append("outcome_schema_id IS ?" if outcome_schema_id is None else "outcome_schema_id = ?")
            params.append(outcome_schema_id)
        if outcome_schema_version is not _UNSET:
            clauses.append("outcome_schema_version IS ?" if outcome_schema_version is None else "outcome_schema_version = ?")
            params.append(outcome_schema_version)
        if domain is not _UNSET:
            clauses.append("domain IS ?" if domain is None else "domain = ?")
            params.append(domain)
        if length_bucket is not _UNSET:
            clauses.append("length_bucket IS ?" if length_bucket is None else "length_bucket = ?")
            params.append(length_bucket)
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM grader_calibration_models{where} ORDER BY created_at, id",
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_raw_grade_event(self, *, values: Mapping[str, Any], clock: Clock | None = None) -> str:
        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO raw_grade_events(
                  id, administration_id, observation_id, attempt_id, response_ref,
                  role, grader_provider, grader_model_revision, grading_prompt_version,
                  grader_output_schema_version, grader_identity_hash, agent_run_id,
                  raw_output_json, criterion_evidence_json, observed_class,
                  model_confidence, confidence_bucket, criterion_observed_classes_json,
                  response_classifier_version, criterion_classifier_version,
                  context_features_json, exact_word_count, declared_length_bucket,
                  predecessor_event_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    values["administration_id"],
                    values.get("observation_id"),
                    values.get("attempt_id"),
                    values.get("response_ref"),
                    values["role"],
                    values.get("grader_provider"),
                    values.get("grader_model_revision"),
                    values.get("grading_prompt_version"),
                    values.get("grader_output_schema_version"),
                    values.get("grader_identity_hash"),
                    values.get("agent_run_id"),
                    values["raw_output_json"],
                    values.get("criterion_evidence_json"),
                    values["observed_class"],
                    values.get("model_confidence"),
                    values["confidence_bucket"],
                    values.get("criterion_observed_classes_json"),
                    values["response_classifier_version"],
                    values.get("criterion_classifier_version"),
                    values["context_features_json"],
                    int(values["exact_word_count"]),
                    values["declared_length_bucket"],
                    values.get("predecessor_event_id"),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return event_id

    def raw_grade_events_for_observation(self, observation_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM raw_grade_events WHERE observation_id = ? ORDER BY created_at, id",
                (observation_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def raw_grade_event(self, event_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM raw_grade_events WHERE id = ?", (event_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def insert_grade_interpretation(self, *, values: Mapping[str, Any], clock: Clock | None = None) -> str:
        interpretation_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO grade_interpretations(
                  id, raw_grade_event_id, observation_id, administration_id,
                  calibration_model_id, calibration_model_hash,
                  projection_algorithm_version, channel_posterior_snapshot_id,
                  response_posterior_json, criterion_posteriors_json,
                  reference_prior_ids_json, certainty_discount, shared_certainty_lcb,
                  credible_interval_json,
                  review_flag, influence_flag, quarantine_state, fallback_reason,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    interpretation_id,
                    values["raw_grade_event_id"],
                    values.get("observation_id"),
                    values["administration_id"],
                    values["calibration_model_id"],
                    values["calibration_model_hash"],
                    values["projection_algorithm_version"],
                    values.get("channel_posterior_snapshot_id"),
                    values["response_posterior_json"],
                    values.get("criterion_posteriors_json"),
                    values.get("reference_prior_ids_json"),
                    float(values["certainty_discount"]),
                    (
                        float(values["shared_certainty_lcb"])
                        if values.get("shared_certainty_lcb") is not None
                        else None
                    ),
                    values.get("credible_interval_json"),
                    1 if values.get("review_flag") else 0,
                    1 if values.get("influence_flag") else 0,
                    values.get("quarantine_state", "active"),
                    values.get("fallback_reason"),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return interpretation_id

    def grade_interpretation(self, interpretation_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM grade_interpretations WHERE id = ?", (interpretation_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def grade_interpretations_for_observation(self, observation_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM grade_interpretations WHERE observation_id = ? ORDER BY created_at, id",
                (observation_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def set_active_interpretation(self, *, observation_id: str, interpretation_id: str) -> None:
        """Point the observation's projection head at an interpretation. This is a
        head pointer on activity_observations, NOT a mutation of an append-only
        event row (the interpretation itself is never updated)."""

        with self.connection() as connection:
            connection.execute(
                "UPDATE activity_observations SET active_interpretation_id = ? WHERE id = ?",
                (interpretation_id, observation_id),
            )
            connection.commit()

    def active_interpretation_for_observation(self, observation_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT gi.* FROM grade_interpretations gi
                  JOIN activity_observations o ON o.active_interpretation_id = gi.id
                 WHERE o.id = ?
                """,
                (observation_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def pending_grade_reviews(self) -> list[dict[str, Any]]:
        """Active-head grade interpretations flagged for review or quarantined
        (§4.4, §5). Joined to the observation + administration so the CLI can order
        by influence. Quarantined first, then influence-flagged, then oldest."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT gi.*, o.id AS observation_id_join,
                       o.attempt_id AS attempt_id,
                       o.surface_id AS surface_id,
                       o.evidence_eligibility AS evidence_eligibility
                  FROM grade_interpretations gi
                  JOIN activity_observations o ON o.active_interpretation_id = gi.id
                 WHERE gi.review_flag = 1 OR gi.quarantine_state = 'quarantined'
                 ORDER BY
                   CASE WHEN gi.quarantine_state = 'quarantined' THEN 0 ELSE 1 END,
                   CASE WHEN gi.influence_flag = 1 THEN 0 ELSE 1 END,
                   CASE WHEN o.evidence_eligibility = 'terminal' THEN 0
                        WHEN o.evidence_eligibility = 'diagnostic' THEN 1 ELSE 2 END,
                   gi.created_at ASC
                """
            ).fetchall()
        return [dict(r) for r in rows]

    def insert_grade_adjudication(self, *, values: Mapping[str, Any], clock: Clock | None = None) -> str:
        adjudication_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO grade_adjudications(
                  id, observation_id, administration_id, reviewed_raw_event_ids_json,
                  adjudicator_source, resolved_class, resolved_distribution_json,
                  rationale, provenance_json, bounded_trust_weight,
                  resulting_interpretation_id, superseded_adjudication_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    adjudication_id,
                    values.get("observation_id"),
                    values["administration_id"],
                    values["reviewed_raw_event_ids_json"],
                    values["adjudicator_source"],
                    values.get("resolved_class"),
                    values.get("resolved_distribution_json"),
                    values.get("rationale"),
                    values.get("provenance_json"),
                    values.get("bounded_trust_weight"),
                    values.get("resulting_interpretation_id"),
                    values.get("superseded_adjudication_id"),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return adjudication_id

    def insert_calibration_stream_sample(self, *, values: Mapping[str, Any], clock: Clock | None = None) -> str:
        sample_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO calibration_stream_samples(
                  id, observation_id, administration_id, raw_grade_event_id,
                  attempt_id, stream, stratum_json, inclusion_probability,
                  sampling_frame_id, selected, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sample_id,
                    values.get("observation_id"),
                    values.get("administration_id"),
                    values.get("raw_grade_event_id"),
                    values.get("attempt_id"),
                    values["stream"],
                    values["stratum_json"],
                    float(values["inclusion_probability"]),
                    values.get("sampling_frame_id"),
                    1 if values.get("selected", True) else 0,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return sample_id

    def calibration_stream_samples(
        self, *, stream: str | None = None, sampling_frame_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if stream is not None:
            clauses.append("stream = ?")
            params.append(stream)
        if sampling_frame_id is not None:
            clauses.append("sampling_frame_id = ?")
            params.append(sampling_frame_id)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM calibration_stream_samples{where} ORDER BY created_at, id",
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def list_all_probe_presentations(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM probe_presentations ORDER BY created_at, id"
            ).fetchall()
        return [dict(row) for row in rows]

    def administration_by_legacy_presentation(self, presentation_id: str) -> dict[str, Any] | None:
        """Idempotency lookup for the §7.1 step-3 presentation backfill: the
        synthetic administration stores the presentation id in its snapshot."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM activity_administrations
                 WHERE json_extract(snapshot_json, '$.legacy_presentation_id') = ?
                 LIMIT 1
                """,
                (presentation_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def exposures_for_surface(self, surface_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM activity_exposure_events
                 WHERE surface_id = ? ORDER BY created_at, id
                """,
                (surface_id,),
            ).fetchall()
        return [_decode_exposure_event(row) for row in rows]

    def exposures_by_surface_hash(self, surface_hash: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM activity_exposure_events
                 WHERE surface_hash = ? ORDER BY created_at, id
                """,
                (surface_hash,),
            ).fetchall()
        return [_decode_exposure_event(row) for row in rows]

    def exposures_by_fingerprint(self, fingerprint: str) -> list[dict[str, Any]]:
        if not fingerprint:
            return []
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM activity_exposure_events
                 WHERE fingerprint = ? ORDER BY created_at, id
                """,
                (fingerprint,),
            ).fetchall()
        return [_decode_exposure_event(row) for row in rows]

    def fetch_surface(self, surface_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM activity_surfaces WHERE id = ?", (surface_id,)
            ).fetchone()
        return _decode_surface(row) if row is not None else None

    def reserved_assessment_surfaces(self) -> list[dict[str, Any]]:
        """Surfaces holding a LIVE assessment reservation (§8.1). Used by reader
        server-side reveal detection (L3) to know which surfaces a reader answer must
        never leak; each row carries the decoded surface plus its hash/fingerprint."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT s.* FROM activity_surface_reservations r
                JOIN activity_surfaces s ON s.id = r.surface_id
                WHERE r.status = 'reserved' AND r.purpose = 'assessment'
                """,
            ).fetchall()
        return [_decode_surface(row) for row in rows]

    def fetch_surface_by_hash(
        self, card_version_id: str, surface_hash: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM activity_surfaces
                 WHERE card_version_id = ? AND surface_hash = ?
                """,
                (card_version_id, surface_hash),
            ).fetchone()
        return _decode_surface(row) if row is not None else None

    def fetch_administration(self, administration_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM activity_administrations WHERE id = ?",
                (administration_id,),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["snapshot"] = _loads(payload.get("snapshot_json"), {})
        return payload

    def observations_for_administration(self, administration_id: str) -> list[dict[str, Any]]:
        """All observation rows recorded under an administration, oldest first."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM activity_observations WHERE administration_id = ? "
                "ORDER BY created_at, id",
                (administration_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def fetch_reservation(self, reservation_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM activity_surface_reservations WHERE id = ?",
                (reservation_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def surface_lifecycle_history(self, surface_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM activity_surface_lifecycle_events
                 WHERE surface_id = ? ORDER BY created_at, id
                """,
                (surface_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def retirement_records_for_surface(self, surface_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM retirement_records WHERE surface_id = ? ORDER BY created_at, id",
                (surface_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def retirement_records_for_card_version(
        self, card_version_id: str
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM retirement_records WHERE card_version_id = ?
                 ORDER BY created_at, id
                """,
                (card_version_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def surfaces_for_card_version(self, card_version_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM activity_surfaces WHERE card_version_id = ? ORDER BY created_at, id",
                (card_version_id,),
            ).fetchall()
        return [_decode_surface(row) for row in rows]

    def surfaces_for_family(self, family_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT s.* FROM activity_surfaces s
                  JOIN activity_card_versions cv ON cv.id = s.card_version_id
                  JOIN activity_cards c ON c.id = cv.card_id
                 WHERE c.family_id = ?
                 ORDER BY s.created_at, s.id
                """,
                (family_id,),
            ).fetchall()
        return [_decode_surface(row) for row in rows]

    def observation_by_attempt(self, attempt_id: str) -> dict[str, Any] | None:
        """Idempotency key for backfill step 4: an attempt is replayed at most once."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM activity_observations WHERE attempt_id = ? LIMIT 1",
                (attempt_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def mark_surface_unverifiable(self, surface_id: str) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE activity_surfaces SET legacy_surface_unverifiable = 1 WHERE id = ?",
                (surface_id,),
            )
            connection.commit()

    def insert_legacy_administration(
        self,
        *,
        surface_id: str,
        card_version_id: str,
        family_id: str,
        purpose: str,
        snapshot_hash: str,
        snapshot_json: str,
        target_contract_version_id: str | None = None,
        target_support_hash: str | None = None,
        eligibility_json: str | None = None,
        created_at: str,
    ) -> str:
        """Direct (non-atomic) administration insert for §7.1 backfill, timestamped
        at the recorded historical time (never now()) so re-runs stay byte-stable."""

        administration_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO activity_administrations(
                  id, surface_id, card_version_id, family_id, purpose,
                  administration_snapshot_hash, snapshot_json,
                  target_contract_version_id, target_support_hash,
                  grader_model_version_id, selection_policy_version_id,
                  decision_params_hash, assistance_json, feedback_condition,
                  eligibility_json, reservation_id, legacy_backfilled, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, ?, NULL, 1, ?)
                """,
                (
                    administration_id,
                    surface_id,
                    card_version_id,
                    family_id,
                    purpose,
                    snapshot_hash,
                    snapshot_json,
                    target_contract_version_id,
                    target_support_hash,
                    eligibility_json,
                    created_at,
                ),
            )
            connection.commit()
        return administration_id

    def append_exposure_event_at(
        self,
        *,
        surface_id: str,
        administration_id: str | None,
        surface_hash: str,
        fingerprint: str | None,
        kind: str,
        purpose: str,
        consumes_unseen: bool,
        created_at: str,
        detail_json: str | None = None,
    ) -> str:
        """Exposure insert timestamped at a recorded historical time (backfill)."""

        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO activity_exposure_events(
                  id, surface_id, administration_id, surface_hash, fingerprint,
                  kind, purpose, consumes_unseen, detail_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    surface_id,
                    administration_id,
                    surface_hash,
                    fingerprint,
                    kind,
                    purpose,
                    1 if consumes_unseen else 0,
                    detail_json,
                    created_at,
                ),
            )
            connection.commit()
        return event_id

    def list_all_assessment_contract_versions(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM assessment_contract_versions ORDER BY created_at, id"
            ).fetchall()
        return [dict(row) for row in rows]

    def list_all_probe_instrument_cards(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM probe_instrument_cards ORDER BY created_at, id, version"
            ).fetchall()
        return [dict(row) for row in rows]

    def interaction_events_for_attempt(self, attempt_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM interaction_events WHERE attempt_id = ? ORDER BY created_at, id",
                (attempt_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_unresolved_cause_factor(
        self,
        *,
        attempt_id: str,
        candidate_causes: Any,
        algorithm_version: str,
        observation_id: str | None = None,
        status: str = "open",
        clock: Clock | None = None,
    ) -> str:
        now = utc_now_iso(clock)
        factor_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO unresolved_cause_factors(
                  id, attempt_id, observation_id, candidate_causes_json,
                  status, resolution_observation_ids_json, algorithm_version,
                  created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    factor_id,
                    attempt_id,
                    observation_id,
                    _json(candidate_causes),
                    status,
                    None,
                    algorithm_version,
                    now,
                    now,
                ),
            )
            connection.commit()
        return factor_id

    def open_unresolved_cause_observation_ids(self) -> set[str]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT observation_id FROM unresolved_cause_factors
                WHERE status = 'open' AND observation_id IS NOT NULL
                """
            ).fetchall()
        return {str(row["observation_id"]) for row in rows}

    def unresolved_cause_factors_for_attempt(
        self, attempt_id: str, *, status: str = "open"
    ) -> list[dict[str, Any]]:
        """Open unresolved-cause factors for an attempt (the §9.6 diagnostic card).

        Each row's ``candidate_causes`` is decoded to the list
        ``[{"facet", "capability"}, ...]`` — the ambiguous cause set a short
        diagnostic would discriminate.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, attempt_id, observation_id, candidate_causes_json,
                       status, algorithm_version, created_at, updated_at
                FROM unresolved_cause_factors
                WHERE attempt_id = ? AND status = ?
                ORDER BY created_at, id
                """,
                (attempt_id, status),
            ).fetchall()
        factors: list[dict[str, Any]] = []
        for row in rows:
            factors.append(
                {
                    "id": row["id"],
                    "attempt_id": row["attempt_id"],
                    "observation_id": row["observation_id"],
                    "candidate_causes": json.loads(row["candidate_causes_json"] or "[]"),
                    "status": row["status"],
                    "algorithm_version": row["algorithm_version"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
            )
        return factors

    def open_unresolved_cause_factors(self) -> list[dict[str, Any]]:
        """Every open positional-ambiguity factor for diagnostic surfaces."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, attempt_id, observation_id, candidate_causes_json,
                       status, algorithm_version, created_at, updated_at
                FROM unresolved_cause_factors
                WHERE status = 'open'
                ORDER BY created_at, id
                """
            ).fetchall()
        return [
            {
                "id": row["id"],
                "attempt_id": row["attempt_id"],
                "observation_id": row["observation_id"],
                "candidate_causes": _loads(row["candidate_causes_json"], []),
                "status": row["status"],
                "algorithm_version": row["algorithm_version"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def retire_unresolved_cause_factor(
        self, observation_id: str, *, clock: Clock | None = None
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE unresolved_cause_factors
                SET status = 'retired', updated_at = ?
                WHERE observation_id = ? AND status = 'open'
                """,
                (now, observation_id),
            )
            connection.commit()

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
              primed, probe_presentation_id, answer_confidence, submission_id,
              declared_dont_know
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                attempt.get("submission_id"),
                1 if attempt.get("declared_dont_know") else 0,
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
        _guard_legacy_facet_write(state)
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
        _guard_legacy_facet_write(state)
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
        display_title: str | None = None,
        reader_enabled: bool | None = None,
        clock: Clock | None = None,
    ) -> None:
        # ``reader_enabled=None`` means "no opinion": new rows default ON, and a
        # re-import that omits the flag never clobbers an explicit earlier choice.
        reader_flag = None if reader_enabled is None else int(reader_enabled)
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_artifacts(
                  id, acquisition_kind, canonical_uri, work_id,
                  current_revision_id, display_title, reader_enabled, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, COALESCE(?, 1), ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  acquisition_kind = excluded.acquisition_kind,
                  canonical_uri = excluded.canonical_uri,
                  work_id = excluded.work_id,
                  current_revision_id = COALESCE(excluded.current_revision_id, source_artifacts.current_revision_id),
                  display_title = COALESCE(excluded.display_title, source_artifacts.display_title),
                  reader_enabled = COALESCE(?, source_artifacts.reader_enabled),
                  updated_at = excluded.updated_at
                """,
                (
                    id, acquisition_kind, canonical_uri, work_id, current_revision_id,
                    display_title, reader_flag, now, now, reader_flag,
                ),
            )
            connection.commit()

    def set_source_reader_enabled(
        self, source_id: str, enabled: bool, *, clock: Clock | None = None
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE source_artifacts SET reader_enabled = ?, updated_at = ? WHERE id = ?",
                (int(enabled), utc_now_iso(clock), source_id),
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
        self,
        extraction_id: str,
        *,
        extraction_result_hash: str,
        status: str = "completed",
        health: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE source_extraction_runs
                   SET extraction_result_hash = ?, status = ?,
                       health_json = COALESCE(?, health_json), completed_at = ?
                 WHERE id = ?
                """,
                (
                    extraction_result_hash,
                    status,
                    _json(dict(health)) if health is not None else None,
                    utc_now_iso(clock),
                    extraction_id,
                ),
            )
            connection.commit()

    def persist_document_ir(self, extraction_id: str, ir: DocumentIR) -> None:
        with self.connection() as connection:
            # A worker may stop after persisting some/all IR but before marking
            # the run complete. Replacing the run-local children makes that
            # retry converge instead of colliding on primary keys or retaining
            # stale blocks from the interrupted output.
            connection.execute(
                "DELETE FROM source_document_assets WHERE extraction_id = ?",
                (extraction_id,),
            )
            connection.execute(
                "DELETE FROM source_document_blocks WHERE extraction_id = ?",
                (extraction_id,),
            )
            connection.execute(
                "DELETE FROM source_document_units WHERE extraction_id = ?",
                (extraction_id,),
            )
            connection.execute(
                "UPDATE source_extraction_runs SET health_json = ? WHERE id = ?",
                (_json(ir.health.model_dump(mode="json")), extraction_id),
            )
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
        from learnloop.ingest.ir import ExtractionHealth

        return DocumentIR(
            ir_schema_version=run["ir_schema_version"],
            extractor=run["extractor"],
            extractor_version=run["extractor_version"],
            blocks=[_decode_document_block(row) for row in block_rows],
            units=[_decode_document_unit(row) for row in unit_rows],
            assets=[_decode_document_asset(row) for row in asset_rows],
            health=ExtractionHealth.model_validate(run.get("health") or {}),
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
    # Unit selections (spec_source_ingestion_v2 §5.3, migration 040)
    # ------------------------------------------------------------------

    def upsert_unit_selection(
        self,
        *,
        extraction_id: str,
        source_id: str | None,
        revision_id: str | None,
        selected_unit_ids: list[str],
        boundary_overrides: list[dict] | None = None,
        needs_review: list[str] | None = None,
        exam_use_modes: Mapping[str, str] | None = None,
        exam_paper_metadata: Mapping[str, Any] | None = None,
        role_override: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_unit_selections(
                  extraction_id, source_id, revision_id, selected_unit_ids_json,
                  boundary_overrides_json, needs_review_json,
                  exam_use_modes_json, exam_paper_metadata_json, role_override,
                  created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(extraction_id) DO UPDATE SET
                  source_id = excluded.source_id,
                  revision_id = excluded.revision_id,
                  selected_unit_ids_json = excluded.selected_unit_ids_json,
                  boundary_overrides_json = excluded.boundary_overrides_json,
                  needs_review_json = excluded.needs_review_json,
                  exam_use_modes_json = excluded.exam_use_modes_json,
                  exam_paper_metadata_json = excluded.exam_paper_metadata_json,
                  role_override = excluded.role_override,
                  updated_at = excluded.updated_at
                """,
                (
                    extraction_id,
                    source_id,
                    revision_id,
                    _json(list(selected_unit_ids)),
                    _json(list(boundary_overrides or [])),
                    _json(list(needs_review or [])),
                    _json(dict(exam_use_modes or {})),
                    _json(dict(exam_paper_metadata or {})),
                    role_override,
                    now,
                    now,
                ),
            )
            connection.commit()

    def get_unit_selection(self, extraction_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_unit_selections WHERE extraction_id = ?", (extraction_id,)
            ).fetchone()
        return _decode_unit_selection(row) if row is not None else None

    def unit_selections_for_revision(self, revision_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_unit_selections WHERE revision_id = ? ORDER BY updated_at",
                (revision_id,),
            ).fetchall()
        return [_decode_unit_selection(row) for row in rows]

    # ------------------------------------------------------------------
    # Role-specific unit inventories (spec_source_ingestion_v2 §7)
    # ------------------------------------------------------------------

    def insert_unit_inventory(
        self,
        *,
        id: str,
        source_revision_id: str,
        extraction_id: str,
        unit_id: str,
        unit_semantic_hash: str,
        inventory_profile: str,
        inventory_schema_version: int,
        prompt_version: str,
        provider: str,
        model: str,
        inventory: Mapping[str, Any],
        usage: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_unit_inventories(
                  id, source_revision_id, extraction_id, unit_id, unit_semantic_hash,
                  inventory_profile, inventory_schema_version, prompt_version,
                  provider, model, inventory_json, usage_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_revision_id, unit_id, unit_semantic_hash,
                            inventory_profile, inventory_schema_version,
                            prompt_version, provider, model)
                  DO UPDATE SET
                    inventory_json = excluded.inventory_json,
                    usage_json = excluded.usage_json,
                    extraction_id = excluded.extraction_id
                """,
                (
                    id,
                    source_revision_id,
                    extraction_id,
                    unit_id,
                    unit_semantic_hash,
                    inventory_profile,
                    inventory_schema_version,
                    prompt_version,
                    provider,
                    model,
                    _json(dict(inventory)),
                    _json(dict(usage or {})),
                    now,
                ),
            )
            connection.commit()

    def reusable_unit_inventories(
        self,
        *,
        source_revision_id: str,
        unit_id: str,
        unit_semantic_hash: str,
        inventory_schema_version: int,
        prompt_version: str,
        provider: str,
        model: str,
    ) -> list[dict[str, Any]]:
        """Cached rows sharing the non-profile cache identity (§7). The service
        picks one whose profile satisfies the request via profile_satisfies."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM source_unit_inventories
                 WHERE source_revision_id = ? AND unit_id = ? AND unit_semantic_hash = ?
                   AND inventory_schema_version = ? AND prompt_version = ?
                   AND provider = ? AND model = ?
                 ORDER BY created_at
                """,
                (
                    source_revision_id,
                    unit_id,
                    unit_semantic_hash,
                    inventory_schema_version,
                    prompt_version,
                    provider,
                    model,
                ),
            ).fetchall()
        return [_decode_unit_inventory(row) for row in rows]

    def get_unit_inventory(self, inventory_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_unit_inventories WHERE id = ?", (inventory_id,)
            ).fetchone()
        return _decode_unit_inventory(row) if row is not None else None

    def unit_inventories_for_extraction(self, extraction_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_unit_inventories WHERE extraction_id = ? ORDER BY unit_id, created_at",
                (extraction_id,),
            ).fetchall()
        return [_decode_unit_inventory(row) for row in rows]

    def unit_inventories_for_revision(self, revision_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_unit_inventories WHERE source_revision_id = ? ORDER BY unit_id, created_at",
                (revision_id,),
            ).fetchall()
        return [_decode_unit_inventory(row) for row in rows]

    def source_unit_inventory_claims(self) -> list[dict[str, Any]]:
        """Facet-candidate harvesting seam (knowledge-model §3.3).

        Flattens every inventory row's claims/concept mentions into
        {text, unit_id, refs} candidates. Candidates only — never canonical."""

        candidates: list[dict[str, Any]] = []
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT id, unit_id, inventory_json FROM source_unit_inventories ORDER BY unit_id, id"
            ).fetchall()
        for row in rows:
            inventory = _loads(row["inventory_json"], {})
            unit_id = row["unit_id"]
            for claim in inventory.get("claims", []):
                statement = (claim.get("statement") or "").strip()
                if statement:
                    candidates.append(
                        {"text": statement, "unit_id": unit_id, "refs": [row["id"], claim.get("claim_id", "")]}
                    )
            for mention in inventory.get("concept_mentions", []):
                name = (mention.get("name") or "").strip()
                if name:
                    candidates.append(
                        {"text": name, "unit_id": unit_id, "refs": [row["id"], mention.get("mention_id", "")]}
                    )
        return candidates

    # ------------------------------------------------------------------
    # Deterministic exam profiles (spec_source_ingestion_v2 §7, §4.2)
    # ------------------------------------------------------------------

    def upsert_exam_profile(
        self,
        *,
        id: str,
        scope_kind: str,
        scope_id: str,
        profile_hash: str,
        profile: Mapping[str, Any],
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_exam_profiles(
                  id, scope_kind, scope_id, profile_hash, profile_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(scope_kind, scope_id, profile_hash) DO UPDATE SET
                  profile_json = excluded.profile_json
                """,
                (id, scope_kind, scope_id, profile_hash, _json(dict(profile)), now),
            )
            connection.commit()

    def get_exam_profile(self, scope_kind: str, scope_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM source_exam_profiles
                 WHERE scope_kind = ? AND scope_id = ?
                 ORDER BY created_at DESC LIMIT 1
                """,
                (scope_kind, scope_id),
            ).fetchone()
        return _decode_exam_profile(row) if row is not None else None

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
        priority: int = 0,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO ingest_batches(
                  id, workflow_type, payload_schema_version, subject_id,
                  source_set_id, status, priority, created_at, cancel_requested
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (id, workflow_type, payload_schema_version, subject_id, source_set_id, status, priority, now),
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
        clear_finished: bool = False,
        clock: Clock | None = None,
    ) -> None:
        """``clear_finished`` nulls a stale terminal timestamp when a batch
        returns to a non-terminal status (resume/retry) — a running batch must
        not keep reporting the prior failure's finished_at."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE ingest_batches
                   SET status = ?,
                       started_at = CASE WHEN ? AND started_at IS NULL THEN ? ELSE started_at END,
                       finished_at = CASE WHEN ? THEN ? WHEN ? THEN NULL ELSE finished_at END
                 WHERE id = ?
                """,
                (
                    status,
                    1 if mark_started else 0,
                    now,
                    1 if mark_finished else 0,
                    now,
                    1 if clear_finished else 0,
                    batch_id,
                ),
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
                 ORDER BY b.priority DESC, b.created_at, j.ordinal, j.id
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
                       current_window = COALESCE(?, current_window),
                       total_windows = COALESCE(?, total_windows)
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

    def delete_finished_ingest_batches(self, batch_ids: Sequence[str]) -> dict[str, int]:
        """Delete finished queue history without touching source-layer artifacts.

        Active batches are rejected. Job dependency edges must be removed before
        jobs because the queue schema intentionally uses restrictive foreign keys.
        """

        ids = list(dict.fromkeys(str(batch_id) for batch_id in batch_ids if batch_id))
        if not ids:
            return {"batches": 0, "jobs": 0, "dependencies": 0}
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as connection:
            active = connection.execute(
                f"SELECT id FROM ingest_batches WHERE id IN ({placeholders}) AND status IN ('queued','running','waiting_for_input')",
                ids,
            ).fetchall()
            if active:
                raise ValueError("active ingest batches cannot be deleted")
            job_rows = connection.execute(
                f"SELECT id FROM ingest_jobs WHERE batch_id IN ({placeholders})", ids
            ).fetchall()
            job_ids = [row["id"] for row in job_rows]
            dependencies = 0
            if job_ids:
                job_placeholders = ",".join("?" for _ in job_ids)
                cursor = connection.execute(
                    f"DELETE FROM ingest_job_dependencies WHERE job_id IN ({job_placeholders}) OR depends_on_job_id IN ({job_placeholders})",
                    [*job_ids, *job_ids],
                )
                dependencies = cursor.rowcount
                connection.execute(
                    f"DELETE FROM ingest_jobs WHERE id IN ({job_placeholders})", job_ids
                )
            cursor = connection.execute(
                f"DELETE FROM ingest_batches WHERE id IN ({placeholders})", ids
            )
            batches = cursor.rowcount
            connection.commit()
        return {"batches": batches, "jobs": len(job_ids), "dependencies": dependencies}

    def update_ingest_job_payload(self, job_id: str, payload: Mapping[str, Any]) -> None:
        """Replace a durable job payload before an explicit retry.

        Completed dependency jobs are never touched; this is used to adjust a
        failed stage's execution ceilings without replaying earlier work.
        """

        with self.connection() as connection:
            connection.execute(
                "UPDATE ingest_jobs SET payload_json = ? WHERE id = ?",
                (_json(dict(payload)), job_id),
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

    # --- ING M5: provenance, manifests, write-ahead apply intents -----------

    def insert_entity_source_link(
        self,
        *,
        entity_type: str,
        entity_id: str,
        locator: str,
        relation: str,
        source_id: str | None = None,
        revision_id: str | None = None,
        locator_scheme: str | None = None,
        extraction_id: str | None = None,
        asset_hash: str | None = None,
        span_hash: str | None = None,
        patch_id: str | None = None,
        status: str = "current",
        link_id: str | None = None,
        created_at: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Insert an entity_source_links row (§9.1). Idempotent on the UNIQUE key
        ``(entity_type, entity_id, revision_id, locator, relation)`` so recovery /
        re-application never duplicates provenance.
        """

        row_id = link_id or new_ulid()
        now = created_at or utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO entity_source_links(
                  id, entity_type, entity_id, source_id, revision_id,
                  locator, locator_scheme, relation, extraction_id, asset_hash,
                  span_hash, patch_id, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    entity_type,
                    entity_id,
                    source_id,
                    revision_id,
                    locator,
                    locator_scheme,
                    relation,
                    extraction_id,
                    asset_hash,
                    span_hash,
                    patch_id,
                    status,
                    now,
                ),
            )
            connection.commit()
        return row_id

    def entity_source_links(
        self, entity_type: str, entity_id: str
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM entity_source_links
                 WHERE entity_type = ? AND entity_id = ?
                 ORDER BY created_at, id
                """,
                (entity_type, entity_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def entity_source_links_for_revision(self, revision_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM entity_source_links WHERE revision_id = ? ORDER BY id",
                (revision_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_notation_mapping(
        self,
        *,
        entity_type: str,
        entity_id: str,
        canonical_notation: str,
        alternate_notation: str,
        subject_id: str | None = None,
        context: str | None = None,
        source_id: str | None = None,
        revision_id: str | None = None,
        locator: str | None = None,
        patch_id: str | None = None,
        status: str = "active",
        mapping_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        row_id = mapping_id or new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO notation_mappings(
                  id, subject_id, entity_type, entity_id, canonical_notation,
                  alternate_notation, context, source_id, revision_id, locator,
                  patch_id, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    subject_id,
                    entity_type,
                    entity_id,
                    canonical_notation,
                    alternate_notation,
                    context,
                    source_id,
                    revision_id,
                    locator,
                    patch_id,
                    status,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return row_id

    def notation_mappings_for_entity(
        self, entity_type: str, entity_id: str
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM notation_mappings
                 WHERE entity_type = ? AND entity_id = ?
                 ORDER BY created_at, id
                """,
                (entity_type, entity_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_source_conflict(
        self,
        *,
        entity_type: str,
        entity_id: str,
        statement: str,
        subject_id: str | None = None,
        left_source_id: str | None = None,
        left_revision_id: str | None = None,
        left_locator: str | None = None,
        right_source_id: str | None = None,
        right_revision_id: str | None = None,
        right_locator: str | None = None,
        status: str = "open",
        resolution: Any = None,
        patch_id: str | None = None,
        conflict_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        row_id = conflict_id or new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_conflicts(
                  id, subject_id, entity_type, entity_id,
                  left_source_id, left_revision_id, left_locator,
                  right_source_id, right_revision_id, right_locator,
                  statement, status, resolution_json, patch_id, created_at, resolved_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    subject_id,
                    entity_type,
                    entity_id,
                    left_source_id,
                    left_revision_id,
                    left_locator,
                    right_source_id,
                    right_revision_id,
                    right_locator,
                    statement,
                    status,
                    _json(resolution) if resolution is not None else None,
                    patch_id,
                    utc_now_iso(clock),
                    None,
                ),
            )
            connection.commit()
        return row_id

    def source_conflicts_for_entity(
        self, entity_type: str, entity_id: str
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM source_conflicts
                 WHERE entity_type = ? AND entity_id = ?
                 ORDER BY created_at, id
                """,
                (entity_type, entity_id),
            ).fetchall()
        return [_decode_source_conflict(row) for row in rows]

    def entity_source_links_for_sources(
        self, source_ids: list[str]
    ) -> list[dict[str, Any]]:
        """All entity_source_links whose ``source_id`` is in ``source_ids``.

        Used by append affected-neighborhood selection (§10.1 source scope): every
        entity the appended source already touches is a high-signal neighbor."""

        if not source_ids:
            return []
        placeholders = ",".join("?" for _ in source_ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM entity_source_links WHERE source_id IN ({placeholders}) ORDER BY id",
                tuple(source_ids),
            ).fetchall()
        return [dict(row) for row in rows]

    def stale_entity_source_links(
        self, statuses: tuple[str, ...] = ("stale", "needs_reanchor")
    ) -> list[dict[str, Any]]:
        """Links whose spans went stale / need re-anchoring (§10.4 revision refresh)."""

        placeholders = ",".join("?" for _ in statuses)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM entity_source_links WHERE status IN ({placeholders}) ORDER BY id",
                statuses,
            ).fetchall()
        return [dict(row) for row in rows]

    def mark_entity_source_link_status(
        self,
        link_id: str,
        *,
        status: str,
        superseded_by_link_id: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE entity_source_links
                   SET status = ?, stale_at = ?, superseded_by_link_id = ?
                 WHERE id = ?
                """,
                (
                    status,
                    utc_now_iso(clock) if status in {"stale", "removed", "needs_reanchor"} else None,
                    superseded_by_link_id,
                    link_id,
                ),
            )
            connection.commit()

    def all_notation_mappings(self, status: str | None = "active") -> list[dict[str, Any]]:
        query = "SELECT * FROM notation_mappings"
        params: tuple[Any, ...] = ()
        if status is not None:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY created_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def source_conflict(self, conflict_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_conflicts WHERE id = ?", (conflict_id,)
            ).fetchone()
        return _decode_source_conflict(row) if row else None

    def source_conflicts_by_status(self, status: str = "open") -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_conflicts WHERE status = ? ORDER BY created_at, id",
                (status,),
            ).fetchall()
        return [_decode_source_conflict(row) for row in rows]

    def resolve_source_conflict(
        self,
        conflict_id: str,
        *,
        status: str,
        resolution: Any,
        resolution_kind: str,
        actor: str | None = None,
        rationale: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Persist a conflict resolution + an immutable audit row (§10.2).

        The conflict row's status/resolution advance; ``source_conflict_resolutions``
        preserves every decision so audit history is never overwritten. Both
        evidence locators stay on the conflict row untouched."""

        now = utc_now_iso(clock)
        audit_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE source_conflicts
                   SET status = ?, resolution_json = ?, resolved_at = ?
                 WHERE id = ?
                """,
                (status, _json(resolution), now if status in {"resolved", "dismissed"} else None, conflict_id),
            )
            connection.execute(
                """
                INSERT INTO source_conflict_resolutions(
                  id, conflict_id, resolution_kind, resolution_json, actor, rationale, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (audit_id, conflict_id, resolution_kind, _json(resolution), actor, rationale, now),
            )
            connection.commit()
        return audit_id

    def source_conflict_resolutions(self, conflict_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM source_conflict_resolutions
                 WHERE conflict_id = ? ORDER BY created_at, id
                """,
                (conflict_id,),
            ).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            data = dict(row)
            data["resolution"] = _loads(data.pop("resolution_json", None), None)
            out.append(data)
        return out

    # --- maintenance feed (§11) --------------------------------------------

    def upsert_maintenance_notice(
        self,
        *,
        notice_type: str,
        dedup_key: str,
        title: str,
        action: Mapping[str, Any],
        aging_policy: str,
        severity: str = "info",
        subject_id: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        detail: Any = None,
        clock: Clock | None = None,
    ) -> str:
        """Insert or refresh a notice (idempotent on ``(notice_type, dedup_key)``).

        A live notice keeps its id, snooze_count, and snoozed_until across
        regeneration; only ``last_seen_at`` (and severity/detail) refresh, so
        deterministic re-generation never duplicates or resets a notice."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT * FROM maintenance_notices WHERE notice_type = ? AND dedup_key = ?",
                (notice_type, dedup_key),
            ).fetchone()
            if existing is not None:
                connection.execute(
                    """
                    UPDATE maintenance_notices
                       SET title = ?, action_json = ?, severity = ?, detail_json = ?,
                           last_seen_at = ?,
                           status = CASE WHEN status IN ('dismissed','resolved','expired','snoozed')
                                         THEN status ELSE 'active' END
                     WHERE id = ?
                    """,
                    (title, _json(action), severity, _json(detail), now, existing["id"]),
                )
                connection.commit()
                return existing["id"]
            row_id = new_ulid()
            connection.execute(
                """
                INSERT INTO maintenance_notices(
                  id, subject_id, notice_type, dedup_key, severity, aging_policy,
                  entity_type, entity_id, title, detail_json, action_json, status,
                  snooze_count, snoozed_until, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', 0, NULL, ?, ?)
                """,
                (
                    row_id, subject_id, notice_type, dedup_key, severity, aging_policy,
                    entity_type, entity_id, title, _json(detail), _json(action), now, now,
                ),
            )
            connection.commit()
            return row_id

    def maintenance_notices(
        self, *, subject_id: str | None = None, include_hidden: bool = False
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM maintenance_notices"
        clauses: list[str] = []
        params: list[Any] = []
        if not include_hidden:
            clauses.append("status IN ('active', 'snoozed')")
        if subject_id is not None:
            clauses.append("(subject_id = ? OR subject_id IS NULL)")
            params.append(subject_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY severity DESC, first_seen_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [_decode_maintenance_notice(row) for row in rows]

    def maintenance_notice(self, notice_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM maintenance_notices WHERE id = ?", (notice_id,)
            ).fetchone()
        return _decode_maintenance_notice(row) if row else None

    def live_maintenance_notice_keys(self) -> set[tuple[str, str]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT notice_type, dedup_key FROM maintenance_notices WHERE status IN ('active','snoozed')"
            ).fetchall()
        return {(row["notice_type"], row["dedup_key"]) for row in rows}

    def set_maintenance_notice_status(
        self,
        notice_id: str,
        *,
        status: str,
        snoozed_until: str | None = None,
        bump_snooze: bool = False,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                f"""
                UPDATE maintenance_notices
                   SET status = ?, snoozed_until = ?,
                       snooze_count = snooze_count + {1 if bump_snooze else 0},
                       resolved_at = CASE WHEN ? IN ('resolved','expired','dismissed') THEN ? ELSE resolved_at END
                 WHERE id = ?
                """,
                (status, snoozed_until, status, now, notice_id),
            )
            connection.commit()

    def insert_synthesis_manifest(self, manifest: Mapping[str, Any]) -> str:
        """Persist an immutable synthesis manifest (§8.4). Idempotent on
        ``manifest_hash`` — an identical manifest returns the existing id and is
        never re-inserted (the cache seam)."""

        manifest_hash = str(manifest["manifest_hash"])
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM synthesis_manifests WHERE manifest_hash = ?",
                (manifest_hash,),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            row_id = str(manifest.get("id") or new_ulid())
            connection.execute(
                """
                INSERT INTO synthesis_manifests(
                  id, manifest_hash, source_set_id, membership_json,
                  revision_ids_json, asset_hashes_json, extraction_ids_json,
                  unit_inventory_versions_json, scope_json, brief_json,
                  prompt_version, schema_version, provider, model,
                  extractor_versions_json, curriculum_snapshot_hash,
                  facet_registry_hash, task_graph_hash, assessment_schema_version,
                  learner_model_contract_version, lock_fingerprint,
                  token_budget_json, estimated_usage_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    manifest_hash,
                    manifest.get("source_set_id"),
                    _json(manifest.get("membership")),
                    _json(manifest.get("revision_ids")),
                    _json(manifest.get("asset_hashes")),
                    _json(manifest.get("extraction_ids")),
                    _json(manifest.get("unit_inventory_versions")),
                    _json(manifest.get("scope")),
                    _json(manifest.get("brief")),
                    manifest.get("prompt_version"),
                    manifest.get("schema_version"),
                    manifest.get("provider"),
                    manifest.get("model"),
                    _json(manifest.get("extractor_versions")),
                    manifest.get("curriculum_snapshot_hash"),
                    manifest.get("facet_registry_hash"),
                    manifest.get("task_graph_hash"),
                    manifest.get("assessment_schema_version"),
                    manifest.get("learner_model_contract_version"),
                    manifest.get("lock_fingerprint"),
                    _json(manifest.get("token_budget")),
                    _json(manifest.get("estimated_usage")),
                    manifest.get("created_at") or utc_now_iso(),
                ),
            )
            connection.commit()
        return row_id

    def synthesis_manifest(self, manifest_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM synthesis_manifests WHERE id = ?",
                (manifest_id,),
            ).fetchone()
        return _decode_synthesis_manifest(row) if row is not None else None

    def synthesis_manifest_by_hash(self, manifest_hash: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM synthesis_manifests WHERE manifest_hash = ?",
                (manifest_hash,),
            ).fetchone()
        return _decode_synthesis_manifest(row) if row is not None else None

    def insert_synthesis_run(
        self,
        *,
        manifest_id: str,
        mode: str,
        agent_run_id: str | None = None,
        proposal_id: str | None = None,
        span_request: Any = None,
        status: str = "created",
        run_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        row_id = run_id or new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO synthesis_runs(
                  id, manifest_id, mode, agent_run_id, proposal_id,
                  span_request_json, resolved_span_hashes_json,
                  coverage_decisions_json, actual_usage_json, status,
                  created_at, completed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    manifest_id,
                    mode,
                    agent_run_id,
                    proposal_id,
                    _json(span_request) if span_request is not None else None,
                    None,
                    None,
                    None,
                    status,
                    utc_now_iso(clock),
                    None,
                ),
            )
            connection.commit()
        return row_id

    def complete_synthesis_run(
        self,
        run_id: str,
        *,
        status: str,
        proposal_id: str | None = None,
        resolved_span_hashes: Any = None,
        coverage_decisions: Any = None,
        actual_usage: Any = None,
        clock: Clock | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE synthesis_runs
                   SET status = ?,
                       proposal_id = COALESCE(?, proposal_id),
                       resolved_span_hashes_json = COALESCE(?, resolved_span_hashes_json),
                       coverage_decisions_json = COALESCE(?, coverage_decisions_json),
                       actual_usage_json = COALESCE(?, actual_usage_json),
                       completed_at = ?
                 WHERE id = ?
                """,
                (
                    status,
                    proposal_id,
                    _json(resolved_span_hashes) if resolved_span_hashes is not None else None,
                    _json(coverage_decisions) if coverage_decisions is not None else None,
                    _json(actual_usage) if actual_usage is not None else None,
                    utc_now_iso(clock),
                    run_id,
                ),
            )
            connection.commit()

    def synthesis_run(self, run_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM synthesis_runs WHERE id = ?", (run_id,)
            ).fetchone()
        return _decode_synthesis_run(row) if row is not None else None

    def save_synthesis_candidate(self, run_id: str, candidate: Mapping[str, Any]) -> None:
        """Stage model output before gates and proposal persistence."""

        with self.connection() as connection:
            connection.execute(
                "UPDATE synthesis_runs SET candidate_output_json = ? WHERE id = ?",
                (_json(dict(candidate)), run_id),
            )
            connection.commit()

    def save_synthesis_shard_result(
        self,
        *,
        shard_key: str,
        shard_ordinal: int,
        shard_count: int,
        result: Mapping[str, Any],
        manifest_hash: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        """Persist one completed synthesis shard's model output (durable checkpoint).

        Keyed by the shard's full input identity so a retried synthesis reuses
        finished shards at zero model cost, including retries whose revised token
        ceilings mint a different manifest."""

        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO synthesis_shard_results(
                  shard_key, manifest_hash, shard_ordinal, shard_count, output_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(shard_key) DO UPDATE SET
                  manifest_hash = excluded.manifest_hash,
                  shard_ordinal = excluded.shard_ordinal,
                  shard_count = excluded.shard_count,
                  output_json = excluded.output_json
                """,
                (
                    shard_key,
                    manifest_hash,
                    shard_ordinal,
                    shard_count,
                    _json(dict(result)),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()

    def synthesis_shard_result(self, shard_key: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM synthesis_shard_results WHERE shard_key = ?", (shard_key,)
            ).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["output"] = _loads(data.pop("output_json", None), None)
        return data

    def finalize_stale_synthesis_runs(
        self, *, before_iso: str, clock: Clock | None = None
    ) -> list[str]:
        """Mark abandoned non-terminal synthesis runs failed (startup hygiene).

        Historical error paths did not always finalize the run row, leaving
        'created'/'running' rows behind forever. Only rows created before
        ``before_iso`` are touched, so a currently-executing synthesis (whose
        worker holds a live job lease) is never finalized under it. Preserved
        candidates stay in place — only the status/completed_at are stamped."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT id FROM synthesis_runs
                 WHERE status IN ('created', 'running') AND created_at < ?
                 ORDER BY created_at, id
                """,
                (before_iso,),
            ).fetchall()
            run_ids = [row["id"] for row in rows]
            if run_ids:
                now = utc_now_iso(clock)
                connection.executemany(
                    "UPDATE synthesis_runs SET status = 'failed', completed_at = ? WHERE id = ?",
                    [(now, run_id) for run_id in run_ids],
                )
            connection.commit()
        return run_ids

    def synthesis_run_introducing_entity(
        self, entity_type: str, entity_id: str
    ) -> dict[str, Any] | None:
        """The synthesis run whose proposal introduced an entity (patch -> run ->
        manifest lineage, §9.2). Resolved via the entity's applied content event's
        change batch -> proposal item -> proposed_patch -> synthesis_runs.proposal_id.
        """

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT synthesis_runs.*
                  FROM content_events
                  JOIN change_batches
                    ON change_batches.id = content_events.change_batch_id
                  JOIN proposed_patch_items
                    ON proposed_patch_items.id = change_batches.proposed_patch_item_id
                  JOIN synthesis_runs
                    ON synthesis_runs.proposal_id = proposed_patch_items.proposed_patch_id
                 WHERE content_events.entity_type = ?
                   AND content_events.entity_id = ?
                   AND content_events.event_type = 'created'
                 ORDER BY content_events.created_at
                 LIMIT 1
                """,
                (entity_type, entity_id),
            ).fetchone()
        return _decode_synthesis_run(row) if row is not None else None

    def insert_apply_intent(
        self,
        *,
        proposed_patch_id: str,
        item_ids: list[str],
        targets: list[Mapping[str, Any]],
        db_plan: list[Mapping[str, Any]],
        intent_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Durably commit the write-ahead apply intent BEFORE any YAML is staged
        (§10.2). Returns the intent id."""

        row_id = intent_id or new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO apply_intents(
                  id, proposed_patch_id, item_ids_json, targets_json,
                  db_plan_json, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, 'pending', ?)
                """,
                (
                    row_id,
                    proposed_patch_id,
                    _json(list(item_ids)),
                    _json([dict(t) for t in targets]),
                    _json([dict(p) for p in db_plan]),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return row_id

    def mark_apply_intent_applied(self, intent_id: str, *, clock: Clock | None = None) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE apply_intents SET status = 'applied', applied_at = ? WHERE id = ?",
                (utc_now_iso(clock), intent_id),
            )
            connection.commit()

    def mark_apply_intent_rolled_back(self, intent_id: str, *, clock: Clock | None = None) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE apply_intents SET status = 'rolled_back', rolled_back_at = ? WHERE id = ?",
                (utc_now_iso(clock), intent_id),
            )
            connection.commit()

    def apply_intent(self, intent_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM apply_intents WHERE id = ?", (intent_id,)
            ).fetchone()
        return _decode_apply_intent(row) if row is not None else None

    def pending_apply_intents(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM apply_intents WHERE status = 'pending' ORDER BY created_at, id"
            ).fetchall()
        return [_decode_apply_intent(row) for row in rows]

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
            for (_prev_key, prev), (_curr_key, curr) in zip(ordered, ordered[1:]):
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

    def derived_state_rebuild_version_changes(self) -> list[dict[str, Any]]:
        """Recalibration boundaries: each derived-state rebuild whose
        ``algorithm_version`` differs from the immediately preceding rebuild.
        Collapses consecutive same-version rebuilds so a version bump surfaces
        as exactly one entry, regardless of how many learning objects/facets it
        recomputed. Ordered oldest-first.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, algorithm_version, created_at
                FROM derived_state_rebuilds
                ORDER BY created_at, id
                """
            ).fetchall()
        changes: list[dict[str, Any]] = []
        previous_version: str | None = None
        for row in rows:
            version = str(row["algorithm_version"])
            if previous_version is not None and version != previous_version:
                changes.append(
                    {
                        "id": str(row["id"]),
                        "algorithm_version": version,
                        "previous_algorithm_version": previous_version,
                        "at": str(row["created_at"]),
                    }
                )
            previous_version = version
        return changes

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
        projection seam (services/depth_rungs)."""

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
            connection.execute("PRAGMA busy_timeout = 5000")
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
            connection.execute("PRAGMA busy_timeout = 5000")
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

    def record_depth_transition_atomic(
        self,
        *,
        commitment_id: str,
        milestone_slug: str,
        milestone_detail_json: str | None,
        transition_detail_json: str | None,
        receipt_key: str,
        fork_spec: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """B4: append the step-7 ``depth_milestone_reached`` + ``depth_transition_committed``
        events AND (when supplied) the step-6 fork lineage/edge/state in ONE transaction.

        Idempotent on ``receipt_key`` (the decision/evidence receipt id): a retry that
        replays the same decision finds the prior ``depth_transition_committed`` event
        and returns it WITHOUT appending a second milestone/transition or a second fork
        (no double-commit). Returns a dict with the event ids, any forked lineage/state
        ids, and ``already`` (True on the idempotent short-circuit)."""

        now = utc_now_iso(clock)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("BEGIN IMMEDIATE")
            prior = connection.execute(
                """
                SELECT id, detail_json FROM commitment_events
                 WHERE commitment_id = ? AND kind = 'depth_transition_committed'
                   AND json_extract(detail_json, '$.receipt_key') = ?
                 ORDER BY created_at, id LIMIT 1
                """,
                (commitment_id, receipt_key),
            ).fetchone()
            if prior is not None:
                connection.execute("ROLLBACK")
                detail = json.loads(prior["detail_json"] or "{}")
                return {
                    "already": True,
                    "transition_event_id": prior["id"],
                    "forked_lineage_id": detail.get("forked_lineage_id"),
                    "forked_state_id": detail.get("forked_state_id"),
                }

            forked_lineage_id: str | None = None
            forked_state_id: str | None = None
            if fork_spec is not None:
                forked_lineage_id = fork_spec.get("lineage_id") or new_ulid()
                connection.execute(
                    "INSERT INTO card_lineages(id, family_id, card_id, created_at) VALUES (?, ?, ?, ?)",
                    (forked_lineage_id, fork_spec.get("family_id"), fork_spec.get("card_id"), now),
                )
                connection.execute(
                    """
                    INSERT INTO card_lineage_edges(
                      id, lineage_id, from_card_version_id, to_card_version_id,
                      edge_kind, classifier_version, rationale_json, created_at
                    )
                    VALUES (?, ?, ?, ?, 'semantic_fork', ?, ?, ?)
                    """,
                    (
                        new_ulid(), forked_lineage_id,
                        fork_spec.get("predecessor_card_version_id"),
                        fork_spec["forked_card_version_id"],
                        fork_spec["classifier_version"],
                        json.dumps(dict(fork_spec.get("rationale") or {"reason": "semantic_fork"}),
                                   sort_keys=True),
                        now,
                    ),
                )
                forked_state_id = fork_spec.get("state_id") or new_ulid()
                projection_head = {
                    "reviews": [],
                    "forked_from_version": fork_spec.get("predecessor_card_version_id"),
                }
                connection.execute(
                    """
                    INSERT INTO activity_card_state(
                      id, learner_id, card_lineage_id, scheduler_algorithm_version,
                      model_label, difficulty, stability, retrievability, due_at,
                      last_eligible_review_at, lapse_episode_id, active,
                      projection_head_json, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, 1, ?, ?)
                    """,
                    (
                        forked_state_id, fork_spec.get("learner_id", "local"),
                        forked_lineage_id, fork_spec["scheduler_algorithm_version"],
                        fork_spec.get("model_label", "fsrs"),
                        fork_spec.get("informed_difficulty_prior"),
                        json.dumps(projection_head, sort_keys=True), now,
                    ),
                )

            milestone_event_id = new_ulid()
            connection.execute(
                """
                INSERT INTO commitment_events(
                  id, commitment_id, commitment_version_id, kind, detail_json, created_at
                )
                VALUES (?, ?, NULL, 'depth_milestone_reached', ?, ?)
                """,
                (milestone_event_id, commitment_id, milestone_detail_json, now),
            )
            transition_event_id = new_ulid()
            connection.execute(
                """
                INSERT INTO commitment_events(
                  id, commitment_id, commitment_version_id, kind, detail_json, created_at
                )
                VALUES (?, ?, NULL, 'depth_transition_committed', ?, ?)
                """,
                (transition_event_id, commitment_id, transition_detail_json, now),
            )
            connection.execute("COMMIT")
            return {
                "already": False,
                "milestone_event_id": milestone_event_id,
                "transition_event_id": transition_event_id,
                "forked_lineage_id": forked_lineage_id,
                "forked_state_id": forked_state_id,
            }
        except Exception:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise
        finally:
            connection.close()

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

    # ------------------------------------------------------------------
    # P1 step 2 -- capability aliases, task features, activity patterns (migration 073)
    # ------------------------------------------------------------------

    def upsert_capability_alias(
        self,
        *,
        registry_version: int,
        legacy_value: str,
        canonical: str | None,
        clock: Clock | None = None,
    ) -> str:
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM capability_aliases WHERE registry_version = ? AND legacy_value = ?",
                (registry_version, legacy_value),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            alias_id = new_ulid()
            connection.execute(
                """
                INSERT INTO capability_aliases(
                  id, registry_version, legacy_value, canonical, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (alias_id, registry_version, legacy_value, canonical, utc_now_iso(clock)),
            )
            connection.commit()
        return alias_id

    def capability_alias(self, *, registry_version: int, legacy_value: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM capability_aliases WHERE registry_version = ? AND legacy_value = ?",
                (registry_version, legacy_value),
            ).fetchone()
        return dict(row) if row is not None else None

    def ensure_task_feature_schema_version(
        self,
        *,
        schema_slug: str,
        version: int,
        dimensions_json: str,
        content_hash: str,
        clock: Clock | None = None,
    ) -> str:
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM task_feature_schema_versions WHERE schema_slug = ? AND version = ?",
                (schema_slug, version),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            schema_id = new_ulid()
            connection.execute(
                """
                INSERT INTO task_feature_schema_versions(
                  id, schema_slug, version, dimensions_json, content_hash, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (schema_id, schema_slug, version, dimensions_json, content_hash, utc_now_iso(clock)),
            )
            connection.commit()
        return schema_id

    def task_feature_schema_version(self, schema_version_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM task_feature_schema_versions WHERE id = ?", (schema_version_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def ensure_activity_pattern(self, *, pattern_slug: str, clock: Clock | None = None) -> str:
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM activity_patterns WHERE pattern_slug = ?", (pattern_slug,)
            ).fetchone()
            if existing is not None:
                return existing["id"]
            pattern_id = new_ulid()
            connection.execute(
                "INSERT INTO activity_patterns(id, pattern_slug, created_at) VALUES (?, ?, ?)",
                (pattern_id, pattern_slug, utc_now_iso(clock)),
            )
            connection.commit()
        return pattern_id

    def ensure_activity_pattern_version(
        self,
        *,
        pattern_id: str,
        version: int,
        content_hash: str,
        fields: Mapping[str, Any],
        status: str,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Content-addressed pattern version, idempotent on ``(pattern_id, content_hash)``.

        B8: the SELECT + INSERT race under ``BEGIN IMMEDIATE``; a lost race (two workers
        registering the same content) raises ``IntegrityError`` on the
        ``UNIQUE(pattern_id, content_hash)`` backstop and re-SELECTs the winner rather
        than surfacing an error or minting a duplicate."""

        def _existing(connection: sqlite3.Connection) -> dict[str, Any] | None:
            row = connection.execute(
                "SELECT * FROM activity_pattern_versions WHERE pattern_id = ? AND content_hash = ?",
                (pattern_id, content_hash),
            ).fetchone()
            return dict(row) if row is not None else None

        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("BEGIN IMMEDIATE")
            existing = _existing(connection)
            if existing is not None:
                connection.execute("ROLLBACK")
                return {"row": existing, "already_exists": True}
            version_id = new_ulid()
            try:
                connection.execute(
                    """
                    INSERT INTO activity_pattern_versions(
                      id, pattern_id, version, allowed_purposes_json, operation, learning_process,
                      allowed_target_kinds_json, allowed_capabilities_json, completion_semantics_json,
                      response_contract_json, progression_role, prerequisite_evidence_json,
                      feedback_strategy_json, assistance_strategy_json, evidence_semantics_by_context_json,
                      task_feature_bounds_json, variation_axes_json, rubric_shape_json, mint_gates_json,
                      burden_model_json, calibration_status, generator_version, content_hash, status,
                      created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        version_id, pattern_id, version, fields["allowed_purposes_json"],
                        fields["operation"], fields["learning_process"],
                        fields["allowed_target_kinds_json"], fields["allowed_capabilities_json"],
                        fields["completion_semantics_json"], fields["response_contract_json"],
                        fields.get("progression_role"), fields.get("prerequisite_evidence_json"),
                        fields.get("feedback_strategy_json"), fields.get("assistance_strategy_json"),
                        fields["evidence_semantics_by_context_json"], fields["task_feature_bounds_json"],
                        fields["variation_axes_json"], fields["rubric_shape_json"],
                        fields["mint_gates_json"], fields.get("burden_model_json"),
                        fields["calibration_status"], fields.get("generator_version"),
                        content_hash, status, utc_now_iso(clock),
                    ),
                )
            except sqlite3.IntegrityError:
                connection.execute("ROLLBACK")
                winner = _existing(connection)
                if winner is None:
                    raise
                return {"row": winner, "already_exists": True}
            row = connection.execute(
                "SELECT * FROM activity_pattern_versions WHERE id = ?", (version_id,)
            ).fetchone()
            connection.execute("COMMIT")
            return {"row": dict(row), "already_exists": False}
        finally:
            connection.close()

    def set_activity_pattern_version_status(
        self, *, pattern_version_id: str, status: str
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE activity_pattern_versions SET status = ? WHERE id = ?",
                (status, pattern_version_id),
            )
            connection.commit()

    def activity_pattern_version(self, pattern_version_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM activity_pattern_versions WHERE id = ?", (pattern_version_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def activity_pattern_versions(self, *, status: str | None = None) -> list[dict[str, Any]]:
        with self.connection() as connection:
            if status is None:
                rows = connection.execute(
                    "SELECT * FROM activity_pattern_versions ORDER BY created_at, id"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM activity_pattern_versions WHERE status = ? ORDER BY created_at, id",
                    (status,),
                ).fetchall()
        return [dict(row) for row in rows]

    def activity_pattern_version_by_slug(
        self, *, pattern_slug: str, status: str | None = None
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            if status is None:
                row = connection.execute(
                    """
                    SELECT v.* FROM activity_pattern_versions v
                      JOIN activity_patterns p ON p.id = v.pattern_id
                     WHERE p.pattern_slug = ? ORDER BY v.version DESC LIMIT 1
                    """,
                    (pattern_slug,),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT v.* FROM activity_pattern_versions v
                      JOIN activity_patterns p ON p.id = v.pattern_id
                     WHERE p.pattern_slug = ? AND v.status = ? ORDER BY v.version DESC LIMIT 1
                    """,
                    (pattern_slug, status),
                ).fetchone()
        return dict(row) if row is not None else None

    # ------------------------------------------------------------------
    # P1 step 3 -- family/card authoring side tables + progression policy (migration 074)
    # ------------------------------------------------------------------

    def ensure_progression_policy_version(
        self,
        *,
        policy_slug: str,
        version: int,
        body_json: str,
        content_hash: str,
        clock: Clock | None = None,
    ) -> str:
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM progression_policy_versions WHERE content_hash = ?", (content_hash,)
            ).fetchone()
            if existing is not None:
                return existing["id"]
            policy_id = new_ulid()
            connection.execute(
                """
                INSERT INTO progression_policy_versions(
                  id, policy_slug, version, body_json, content_hash, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (policy_id, policy_slug, version, body_json, content_hash, utc_now_iso(clock)),
            )
            connection.commit()
        return policy_id

    def progression_policy_version(self, policy_version_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM progression_policy_versions WHERE id = ?", (policy_version_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def upsert_activity_family_authoring(
        self, *, family_version_id: str, fields: Mapping[str, Any], clock: Clock | None = None
    ) -> None:
        """Insert/replace the authoring side row keyed by the immutable P0 family
        version id. The 065 ``activity_family_versions`` row is never touched."""

        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO activity_family_authoring(
                  family_version_id, commitment_id, commitment_target_version_id,
                  authoring_purpose, pattern_version_id, progression_policy_version_id,
                  goal_contract_version_id, depth_policy_version_id, depth_envelope_version_id,
                  served_milestone_edges_json, cross_purpose_links_json, angle_inventory_json,
                  coverage_targets_json, evidence_cap_policy_id, mint_policy_json,
                  retirement_policy_json, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(family_version_id) DO UPDATE SET
                  commitment_id = excluded.commitment_id,
                  commitment_target_version_id = excluded.commitment_target_version_id,
                  authoring_purpose = excluded.authoring_purpose,
                  pattern_version_id = excluded.pattern_version_id,
                  progression_policy_version_id = excluded.progression_policy_version_id,
                  goal_contract_version_id = excluded.goal_contract_version_id,
                  depth_policy_version_id = excluded.depth_policy_version_id,
                  depth_envelope_version_id = excluded.depth_envelope_version_id,
                  served_milestone_edges_json = excluded.served_milestone_edges_json,
                  cross_purpose_links_json = excluded.cross_purpose_links_json,
                  angle_inventory_json = excluded.angle_inventory_json,
                  coverage_targets_json = excluded.coverage_targets_json,
                  evidence_cap_policy_id = excluded.evidence_cap_policy_id,
                  mint_policy_json = excluded.mint_policy_json,
                  retirement_policy_json = excluded.retirement_policy_json,
                  status = excluded.status
                """,
                (
                    family_version_id, fields.get("commitment_id"),
                    fields.get("commitment_target_version_id"), fields["authoring_purpose"],
                    fields.get("pattern_version_id"), fields.get("progression_policy_version_id"),
                    fields.get("goal_contract_version_id"), fields.get("depth_policy_version_id"),
                    fields.get("depth_envelope_version_id"), fields.get("served_milestone_edges_json"),
                    fields.get("cross_purpose_links_json"), fields.get("angle_inventory_json"),
                    fields.get("coverage_targets_json"), fields.get("evidence_cap_policy_id"),
                    fields.get("mint_policy_json"), fields.get("retirement_policy_json"),
                    fields.get("status", "draft"), utc_now_iso(clock),
                ),
            )
            connection.commit()

    def set_activity_family_authoring_status(
        self, *, family_version_id: str, status: str
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE activity_family_authoring SET status = ? WHERE family_version_id = ?",
                (status, family_version_id),
            )
            connection.commit()

    def activity_family_authoring(self, family_version_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM activity_family_authoring WHERE family_version_id = ?",
                (family_version_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def upsert_activity_card_authoring(
        self, *, card_version_id: str, fields: Mapping[str, Any], clock: Clock | None = None
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO activity_card_authoring(
                  card_version_id, family_version_id, pattern_version_id,
                  task_feature_schema_version_id, task_features_json, capability,
                  outcome_schema_id, outcome_schema_version, surface_policy,
                  surface_variation_bounds_json, angle_identity_json, generator_version,
                  gate_policy_version, expected_burden_json, calibration_metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(card_version_id) DO UPDATE SET
                  family_version_id = excluded.family_version_id,
                  pattern_version_id = excluded.pattern_version_id,
                  task_feature_schema_version_id = excluded.task_feature_schema_version_id,
                  task_features_json = excluded.task_features_json,
                  capability = excluded.capability,
                  outcome_schema_id = excluded.outcome_schema_id,
                  outcome_schema_version = excluded.outcome_schema_version,
                  surface_policy = excluded.surface_policy,
                  surface_variation_bounds_json = excluded.surface_variation_bounds_json,
                  angle_identity_json = excluded.angle_identity_json,
                  generator_version = excluded.generator_version,
                  gate_policy_version = excluded.gate_policy_version,
                  expected_burden_json = excluded.expected_burden_json,
                  calibration_metadata_json = excluded.calibration_metadata_json
                """,
                (
                    card_version_id, fields.get("family_version_id"),
                    fields.get("pattern_version_id"), fields.get("task_feature_schema_version_id"),
                    fields.get("task_features_json"), fields.get("capability"),
                    fields.get("outcome_schema_id"), fields.get("outcome_schema_version"),
                    fields.get("surface_policy"), fields.get("surface_variation_bounds_json"),
                    fields.get("angle_identity_json"), fields.get("generator_version"),
                    fields.get("gate_policy_version"), fields.get("expected_burden_json"),
                    fields.get("calibration_metadata_json"), utc_now_iso(clock),
                ),
            )
            connection.commit()

    def activity_card_authoring(self, card_version_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM activity_card_authoring WHERE card_version_id = ?",
                (card_version_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def activity_card_authoring_for_family(self, family_version_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM activity_card_authoring WHERE family_version_id = ? ORDER BY created_at, card_version_id",
                (family_version_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def activity_family_authoring_purposes(self, family_id: str) -> dict[str, str]:
        """Authoring purposes across every version of one stable family (§1.1
        invariant 2 / §9.1 purpose-immutability check), keyed by family_version_id."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT a.family_version_id AS fvid, a.authoring_purpose AS purpose
                  FROM activity_family_authoring a
                  JOIN activity_family_versions v ON v.id = a.family_version_id
                 WHERE v.family_id = ?
                """,
                (family_id,),
            ).fetchall()
        return {row["fvid"]: row["purpose"] for row in rows}

    def activity_family_version_family_id(self, family_version_id: str) -> str | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT family_id FROM activity_family_versions WHERE id = ?", (family_version_id,)
            ).fetchone()
        return row["family_id"] if row is not None else None

    # ------------------------------------------------------------------
    # P1 step 4: card lineages, richer lineage edges, card-level state
    # (migration 075). Append-only edges; state keyed by learner x lineage x
    # scheduler algorithm version (§3.7, §3.8).
    # ------------------------------------------------------------------
    def create_card_lineage(
        self,
        *,
        card_id: str | None = None,
        family_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        lineage_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO card_lineages(id, family_id, card_id, created_at) VALUES (?, ?, ?, ?)",
                (lineage_id, family_id, card_id, utc_now_iso(clock)),
            )
            connection.commit()
        return lineage_id

    def card_lineage(self, lineage_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM card_lineages WHERE id = ?", (lineage_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def append_card_lineage_edge(
        self,
        *,
        lineage_id: str,
        to_card_version_id: str,
        edge_kind: str,
        classifier_version: str,
        from_card_version_id: str | None = None,
        rationale: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> str:
        edge_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO card_lineage_edges(
                  id, lineage_id, from_card_version_id, to_card_version_id,
                  edge_kind, classifier_version, rationale_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    edge_id,
                    lineage_id,
                    from_card_version_id,
                    to_card_version_id,
                    edge_kind,
                    classifier_version,
                    None if rationale is None else json.dumps(rationale, sort_keys=True),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return edge_id

    def card_lineage_edges(self, lineage_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM card_lineage_edges WHERE lineage_id = ? ORDER BY created_at, id",
                (lineage_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def lineage_for_card_version(self, card_version_id: str) -> str | None:
        """Resolve the lineage a card version belongs to via its lineage edges."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT lineage_id FROM card_lineage_edges
                 WHERE to_card_version_id = ? OR from_card_version_id = ?
                 ORDER BY created_at, id LIMIT 1
                """,
                (card_version_id, card_version_id),
            ).fetchone()
        return row["lineage_id"] if row is not None else None

    def upsert_activity_card_state(
        self,
        *,
        card_lineage_id: str,
        scheduler_algorithm_version: str,
        model_label: str,
        learner_id: str = "local",
        difficulty: float | None = None,
        stability: float | None = None,
        retrievability: float | None = None,
        due_at: str | None = None,
        last_eligible_review_at: str | None = None,
        lapse_episode_id: str | None = None,
        active: bool = True,
        projection_head: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> str:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM activity_card_state
                 WHERE learner_id = ? AND card_lineage_id = ? AND scheduler_algorithm_version = ?
                """,
                (learner_id, card_lineage_id, scheduler_algorithm_version),
            ).fetchone()
            state_id = existing["id"] if existing is not None else new_ulid()
            connection.execute(
                """
                INSERT INTO activity_card_state(
                  id, learner_id, card_lineage_id, scheduler_algorithm_version,
                  model_label, difficulty, stability, retrievability, due_at,
                  last_eligible_review_at, lapse_episode_id, active,
                  projection_head_json, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(learner_id, card_lineage_id, scheduler_algorithm_version)
                DO UPDATE SET
                  model_label = excluded.model_label,
                  difficulty = excluded.difficulty,
                  stability = excluded.stability,
                  retrievability = excluded.retrievability,
                  due_at = excluded.due_at,
                  last_eligible_review_at = excluded.last_eligible_review_at,
                  lapse_episode_id = excluded.lapse_episode_id,
                  active = excluded.active,
                  projection_head_json = excluded.projection_head_json,
                  updated_at = excluded.updated_at
                """,
                (
                    state_id,
                    learner_id,
                    card_lineage_id,
                    scheduler_algorithm_version,
                    model_label,
                    difficulty,
                    stability,
                    retrievability,
                    due_at,
                    last_eligible_review_at,
                    lapse_episode_id,
                    1 if active else 0,
                    None if projection_head is None else json.dumps(projection_head, sort_keys=True),
                    now,
                ),
            )
            connection.commit()
        return state_id

    def activity_card_state(
        self,
        *,
        card_lineage_id: str,
        scheduler_algorithm_version: str,
        learner_id: str = "local",
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM activity_card_state
                 WHERE learner_id = ? AND card_lineage_id = ? AND scheduler_algorithm_version = ?
                """,
                (learner_id, card_lineage_id, scheduler_algorithm_version),
            ).fetchone()
        return dict(row) if row is not None else None

    # ------------------------------------------------------------------
    # P1 step 5: administration purpose + context (migration 076 ALTER).
    # ------------------------------------------------------------------
    def activity_administration(self, administration_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM activity_administrations WHERE id = ?", (administration_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def all_activity_administrations(self) -> list[dict[str, Any]]:
        """Every administration row, oldest first. A pure-ledger read for the P1
        event-sufficiency replay (§9.8): the deferred psychometrics projection is
        buildable from ledger events ALONE, with zero live-table reads."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM activity_administrations ORDER BY created_at, id"
            ).fetchall()
        return [dict(row) for row in rows]

    def set_administration_context(
        self,
        *,
        administration_id: str,
        reading_phase: str | None = None,
        admin_context: Mapping[str, Any] | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE activity_administrations
                   SET reading_phase = ?, admin_context_json = ?
                 WHERE id = ?
                """,
                (
                    reading_phase,
                    None if admin_context is None else json.dumps(admin_context, sort_keys=True),
                    administration_id,
                ),
            )
            connection.commit()

    # ------------------------------------------------------------------
    # P1 step 6: namespaced fingerprint memberships, soft-kinship features,
    # surface authoring (migration 077). One familiarity namespace (§4.1/§4.2).
    # ------------------------------------------------------------------
    def record_fingerprint_membership(
        self,
        *,
        surface_id: str,
        namespace: str,
        value_hash: str,
        provenance: str | None = None,
        status: str | None = None,
        confidence: float | None = None,
        clock: Clock | None = None,
    ) -> str:
        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM surface_fingerprint_memberships
                 WHERE surface_id = ? AND namespace = ? AND value_hash = ?
                """,
                (surface_id, namespace, value_hash),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            membership_id = new_ulid()
            connection.execute(
                """
                INSERT INTO surface_fingerprint_memberships(
                  id, surface_id, namespace, value_hash, provenance, status, confidence, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    membership_id,
                    surface_id,
                    namespace,
                    value_hash,
                    provenance,
                    status,
                    confidence,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return membership_id

    def fingerprint_memberships_for_surface(self, surface_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM surface_fingerprint_memberships WHERE surface_id = ? ORDER BY namespace, value_hash",
                (surface_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def surfaces_sharing_membership(
        self, *, namespace: str, value_hash: str, exclude_surface_id: str | None = None
    ) -> list[str]:
        """All surfaces in a given (namespace, value_hash) hard group. Every membership
        is considered -- never first-field-wins (§4.1, fixing the legacy L58 bug)."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT surface_id FROM surface_fingerprint_memberships
                 WHERE namespace = ? AND value_hash = ?
                 ORDER BY surface_id
                """,
                (namespace, value_hash),
            ).fetchall()
        out = [row["surface_id"] for row in rows]
        if exclude_surface_id is not None:
            out = [s for s in out if s != exclude_surface_id]
        return out

    def upsert_soft_kinship_features(
        self,
        *,
        surface_id: str,
        feature_schema_version: str,
        features: Mapping[str, Any],
        clock: Clock | None = None,
    ) -> str:
        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM soft_kinship_features
                 WHERE surface_id = ? AND feature_schema_version = ?
                """,
                (surface_id, feature_schema_version),
            ).fetchone()
            feature_id = existing["id"] if existing is not None else new_ulid()
            connection.execute(
                """
                INSERT INTO soft_kinship_features(
                  id, surface_id, feature_schema_version, features_json, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(surface_id, feature_schema_version) DO UPDATE SET
                  features_json = excluded.features_json
                """,
                (
                    feature_id,
                    surface_id,
                    feature_schema_version,
                    json.dumps(features, sort_keys=True),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return feature_id

    def soft_kinship_features_for_surface(
        self, *, surface_id: str, feature_schema_version: str | None = None
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            if feature_schema_version is not None:
                row = connection.execute(
                    """
                    SELECT * FROM soft_kinship_features
                     WHERE surface_id = ? AND feature_schema_version = ?
                    """,
                    (surface_id, feature_schema_version),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT * FROM soft_kinship_features WHERE surface_id = ?
                     ORDER BY created_at DESC, id DESC LIMIT 1
                    """,
                    (surface_id,),
                ).fetchone()
        return dict(row) if row is not None else None

    def upsert_activity_surface_authoring(
        self, *, surface_id: str, fields: Mapping[str, Any], clock: Clock | None = None
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO activity_surface_authoring(
                  surface_id, surface_policy, generator_provenance_json, anchor_surface_id,
                  candidate_batch_id, seed, angle_coords_json, task_features_json,
                  gate_decision_json, reviewer, status, pinned_by_learner,
                  authorship_provenance_json, rotation_eligible, cache_state, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(surface_id) DO UPDATE SET
                  surface_policy = excluded.surface_policy,
                  generator_provenance_json = excluded.generator_provenance_json,
                  anchor_surface_id = excluded.anchor_surface_id,
                  candidate_batch_id = excluded.candidate_batch_id,
                  seed = excluded.seed,
                  angle_coords_json = excluded.angle_coords_json,
                  task_features_json = excluded.task_features_json,
                  gate_decision_json = excluded.gate_decision_json,
                  reviewer = excluded.reviewer,
                  status = excluded.status,
                  pinned_by_learner = excluded.pinned_by_learner,
                  authorship_provenance_json = excluded.authorship_provenance_json,
                  rotation_eligible = excluded.rotation_eligible,
                  cache_state = excluded.cache_state
                """,
                (
                    surface_id,
                    fields.get("surface_policy"),
                    fields.get("generator_provenance_json"),
                    fields.get("anchor_surface_id"),
                    fields.get("candidate_batch_id"),
                    fields.get("seed"),
                    fields.get("angle_coords_json"),
                    fields.get("task_features_json"),
                    fields.get("gate_decision_json"),
                    fields.get("reviewer"),
                    fields.get("status"),
                    1 if fields.get("pinned_by_learner") else 0,
                    fields.get("authorship_provenance_json"),
                    1 if fields.get("rotation_eligible") else 0,
                    fields.get("cache_state"),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()

    def activity_surface_authoring(self, surface_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM activity_surface_authoring WHERE surface_id = ?", (surface_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def activity_exposure_events_for_surface(self, surface_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM activity_exposure_events WHERE surface_id = ? ORDER BY created_at, id",
                (surface_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # P1 step 7: durable surface-mint requests (migration 078). Modeled on the
    # 033 ingest-job lease: exactly one worker drains at a time; an expired lease
    # is recovered. Enqueue is idempotent on the §5.6 key. Never blocks attempts.
    # ------------------------------------------------------------------
    def enqueue_surface_mint_request(
        self,
        *,
        card_version_id: str,
        generator_version: str,
        gate_policy_version: str,
        anchor_surface_id: str | None = None,
        requested_angle_json: str = "",
        token_cost_json: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Idempotent on ``(card_version, anchor, requested_angle, generator,
        gate_policy)`` (§5.6). Returns the existing request id when one already
        exists (any status), else inserts a fresh ``pending`` request.

        B2: ``anchor_surface_id`` is the ``''`` sentinel when absent (mirroring
        ``requested_angle_json``) so the UNIQUE idempotency index treats "no anchor"
        as one value. The insert races under ``BEGIN IMMEDIATE``; a lost race raises
        ``IntegrityError`` on the UNIQUE constraint and re-SELECTs the winner rather
        than enqueuing a duplicate."""

        angle = requested_angle_json or ""
        anchor = anchor_surface_id if anchor_surface_id is not None else ""

        def _existing(connection: sqlite3.Connection) -> dict[str, Any] | None:
            return connection.execute(
                """
                SELECT id FROM surface_mint_requests
                 WHERE card_version_id = ? AND anchor_surface_id = ?
                   AND requested_angle_json = ? AND generator_version = ?
                   AND gate_policy_version = ?
                """,
                (card_version_id, anchor, angle, generator_version, gate_policy_version),
            ).fetchone()

        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("BEGIN IMMEDIATE")
            existing = _existing(connection)
            if existing is not None:
                connection.execute("ROLLBACK")
                return existing["id"]
            request_id = new_ulid()
            now = utc_now_iso(clock)
            try:
                connection.execute(
                    """
                    INSERT INTO surface_mint_requests(
                      id, card_version_id, anchor_surface_id, requested_angle_json,
                      generator_version, gate_policy_version, status, token_cost_json,
                      created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                    """,
                    (request_id, card_version_id, anchor, angle,
                     generator_version, gate_policy_version, token_cost_json, now, now),
                )
            except sqlite3.IntegrityError:
                connection.execute("ROLLBACK")
                winner = _existing(connection)
                if winner is None:
                    raise
                return winner["id"]
            connection.execute("COMMIT")
            return request_id
        finally:
            connection.close()

    def surface_mint_request(self, request_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM surface_mint_requests WHERE id = ?", (request_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def surface_mint_requests_for_card_version(
        self, card_version_id: str, *, statuses: Sequence[str] | None = None
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            if statuses:
                placeholders = ",".join("?" for _ in statuses)
                rows = connection.execute(
                    f"""
                    SELECT * FROM surface_mint_requests
                     WHERE card_version_id = ? AND status IN ({placeholders})
                     ORDER BY created_at, id
                    """,
                    (card_version_id, *statuses),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM surface_mint_requests WHERE card_version_id = ? ORDER BY created_at, id",
                    (card_version_id,),
                ).fetchall()
        return [dict(row) for row in rows]

    def claim_next_surface_mint_request(
        self, *, worker_id: str, now_iso: str, lease_expires_at: str, lease_cutoff_iso: str
    ) -> dict[str, Any] | None:
        """Atomically claim the next ``pending`` mint request for ``worker_id``.

        Returns None when another worker holds a live running lease (exactly one
        worker drains at a time) or when no pending request exists. A ``running``
        request whose lease predates ``lease_cutoff_iso`` is treated as dead and
        does not block the claim.
        """

        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("BEGIN IMMEDIATE")
            live = connection.execute(
                """
                SELECT 1 FROM surface_mint_requests
                 WHERE status = 'running'
                   AND lease_expires_at IS NOT NULL
                   AND lease_expires_at >= ?
                 LIMIT 1
                """,
                (lease_cutoff_iso,),
            ).fetchone()
            if live is not None:
                connection.execute("ROLLBACK")
                return None
            candidate = connection.execute(
                """
                SELECT * FROM surface_mint_requests
                 WHERE status = 'pending'
                    OR (status = 'running' AND (lease_expires_at IS NULL
                                                OR lease_expires_at < ?))
                 ORDER BY created_at, id
                 LIMIT 1
                """,
                (lease_cutoff_iso,),
            ).fetchone()
            if candidate is None:
                connection.execute("ROLLBACK")
                return None
            # B1 fencing token: every (re)claim bumps lease_epoch so a late write from
            # the prior lease holder carries a stale epoch and is rejected.
            connection.execute(
                """
                UPDATE surface_mint_requests
                   SET status = 'running', lease_owner = ?, lease_expires_at = ?,
                       lease_epoch = lease_epoch + 1, updated_at = ?
                 WHERE id = ? AND status IN ('pending', 'running')
                """,
                (worker_id, lease_expires_at, now_iso, candidate["id"]),
            )
            claimed = connection.execute(
                "SELECT * FROM surface_mint_requests WHERE id = ?", (candidate["id"],)
            ).fetchone()
            connection.execute("COMMIT")
            return dict(claimed) if claimed is not None else None
        finally:
            connection.close()

    def set_surface_mint_candidate(
        self,
        *,
        request_id: str,
        candidate_surface_id: str,
        gate_results_json: str | None = None,
        token_cost_json: str | None = None,
        expected_lease_epoch: int | None = None,
        clock: Clock | None = None,
    ) -> bool:
        """Record the gated candidate and move the request to ``candidate_ready``.

        B1: guarded by ``status = 'running'`` and (when supplied) the fencing
        ``lease_epoch``. Returns True iff the write applied; a stale-lease worker's
        write is rejected (rowcount 0) so it can never advance a re-claimed job. The
        lease is deliberately RETAINED here (the same worker admits/rejects next);
        only the terminal transition releases it."""

        epoch_clause = "" if expected_lease_epoch is None else " AND lease_epoch = ?"
        params: list[Any] = [candidate_surface_id, gate_results_json, token_cost_json,
                             utc_now_iso(clock), request_id]
        if expected_lease_epoch is not None:
            params.append(expected_lease_epoch)
        with self.connection() as connection:
            cursor = connection.execute(
                f"""
                UPDATE surface_mint_requests
                   SET status = 'candidate_ready', candidate_surface_id = ?,
                       gate_results_json = COALESCE(?, gate_results_json),
                       token_cost_json = COALESCE(?, token_cost_json),
                       updated_at = ?
                 WHERE id = ? AND status = 'running'{epoch_clause}
                """,
                params,
            )
            connection.commit()
            return cursor.rowcount > 0

    def resolve_surface_mint_request(
        self,
        *,
        request_id: str,
        status: str,
        gate_results_json: str | None = None,
        failure_reason: str | None = None,
        candidate_surface_id: str | None = None,
        expected_lease_epoch: int | None = None,
        require_active: bool = False,
        clock: Clock | None = None,
    ) -> bool:
        """Terminal transition to ``admitted`` / ``rejected`` / ``failed``. Releases
        any lease. A failed/rejected candidate row is retained for audit.

        B1: when ``expected_lease_epoch`` is supplied the write is guarded by the
        fencing token, and when ``require_active`` is set only a ``running`` /
        ``candidate_ready`` request may transition (so an already-terminal request is
        never re-resolved by a re-run or a stale worker). Returns True iff applied."""

        clauses = ["id = ?"]
        params: list[Any] = [status, gate_results_json, failure_reason,
                             candidate_surface_id, utc_now_iso(clock), request_id]
        if require_active:
            clauses.append("status IN ('running', 'candidate_ready')")
        if expected_lease_epoch is not None:
            clauses.append("lease_epoch = ?")
            params.append(expected_lease_epoch)
        where = " AND ".join(clauses)
        with self.connection() as connection:
            cursor = connection.execute(
                f"""
                UPDATE surface_mint_requests
                   SET status = ?,
                       gate_results_json = COALESCE(?, gate_results_json),
                       failure_reason = COALESCE(?, failure_reason),
                       candidate_surface_id = COALESCE(?, candidate_surface_id),
                       lease_owner = NULL, lease_expires_at = NULL, updated_at = ?
                 WHERE {where}
                """,
                params,
            )
            connection.commit()
            return cursor.rowcount > 0

    def obsolete_surface_mint_requests_for_card_versions(
        self, card_version_ids: Sequence[str], *, clock: Clock | None = None
    ) -> int:
        """Mark all not-yet-terminal mint work for the given card versions ``obsolete``
        (§5.6: card/family retirement makes pending work obsolete). Returns the count."""

        if not card_version_ids:
            return 0
        placeholders = ",".join("?" for _ in card_version_ids)
        with self.connection() as connection:
            cursor = connection.execute(
                f"""
                UPDATE surface_mint_requests
                   SET status = 'obsolete', lease_owner = NULL, lease_expires_at = NULL,
                       updated_at = ?
                 WHERE card_version_id IN ({placeholders})
                   AND status IN ('pending', 'running', 'candidate_ready')
                """,
                (utc_now_iso(clock), *card_version_ids),
            )
            connection.commit()
            return cursor.rowcount

    # ------------------------------------------------------------------
    # P1 step 8: angle inventories, family evidence-cap policies, lapse episodes
    # (migration 079). Within-family angle progression + the family evidence cap +
    # post-lapse linked retries (§4.3, §5.4, §5.5).
    # ------------------------------------------------------------------
    def insert_angle_inventory(
        self,
        *,
        family_version_id: str | None,
        coordinates_json: str,
        coverage_targets_json: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        inventory_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO angle_inventories(
                  id, family_version_id, coordinates_json, coverage_targets_json, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (inventory_id, family_version_id, coordinates_json, coverage_targets_json,
                 utc_now_iso(clock)),
            )
            connection.commit()
        return inventory_id

    def angle_inventories_for_family(self, family_version_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM angle_inventories WHERE family_version_id = ? ORDER BY created_at, id",
                (family_version_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def ensure_family_evidence_cap_policy(
        self,
        *,
        policy_slug: str,
        version: int,
        caps_json: str,
        content_hash: str,
        clock: Clock | None = None,
    ) -> str:
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM family_evidence_cap_policies WHERE policy_slug = ? AND version = ?",
                (policy_slug, version),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            policy_id = new_ulid()
            connection.execute(
                """
                INSERT INTO family_evidence_cap_policies(
                  id, policy_slug, version, caps_json, content_hash, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (policy_id, policy_slug, version, caps_json, content_hash, utc_now_iso(clock)),
            )
            connection.commit()
        return policy_id

    def family_evidence_cap_policy(self, policy_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM family_evidence_cap_policies WHERE id = ?", (policy_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def open_lapse_episode(
        self,
        *,
        card_lineage_id: str,
        opened_administration_id: str | None = None,
        learner_id: str = "local",
        followup_due_at: str | None = None,
        derived_retrievability: float | None = None,
        clock: Clock | None = None,
    ) -> str:
        episode_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO lapse_episodes(
                  id, card_lineage_id, learner_id, opened_administration_id, status,
                  retry_observations_json, derived_retrievability, followup_due_at,
                  opened_at, closed_at
                )
                VALUES (?, ?, ?, ?, 'open', ?, ?, ?, ?, NULL)
                """,
                (episode_id, card_lineage_id, learner_id, opened_administration_id,
                 json.dumps([]), derived_retrievability, followup_due_at, utc_now_iso(clock)),
            )
            connection.commit()
        return episode_id

    def lapse_episode(self, episode_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM lapse_episodes WHERE id = ?", (episode_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def update_lapse_episode(
        self,
        *,
        episode_id: str,
        retry_observations_json: str | None = None,
        derived_retrievability: float | None = None,
        status: str | None = None,
        followup_due_at: str | None = None,
        closed_at: str | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE lapse_episodes
                   SET retry_observations_json = COALESCE(?, retry_observations_json),
                       derived_retrievability = COALESCE(?, derived_retrievability),
                       status = COALESCE(?, status),
                       followup_due_at = COALESCE(?, followup_due_at),
                       closed_at = COALESCE(?, closed_at)
                 WHERE id = ?
                """,
                (retry_observations_json, derived_retrievability, status, followup_due_at,
                 closed_at, episode_id),
            )
            connection.commit()

    def lapse_episodes_for_lineage(
        self, card_lineage_id: str, *, status: str | None = None
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            if status is not None:
                rows = connection.execute(
                    "SELECT * FROM lapse_episodes WHERE card_lineage_id = ? AND status = ? ORDER BY opened_at, id",
                    (card_lineage_id, status),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM lapse_episodes WHERE card_lineage_id = ? ORDER BY opened_at, id",
                    (card_lineage_id,),
                ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # P2 golden path -- task blueprints (spec_p2 §3.2, migration 081)
    # ------------------------------------------------------------------

    def ensure_task_blueprint(
        self,
        *,
        blueprint_slug: str,
        source_rev: str,
        unit_id: str,
        family_key: str,
        clock: Clock | None = None,
    ) -> str:
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM task_blueprints WHERE blueprint_slug = ?",
                (blueprint_slug,),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            blueprint_id = new_ulid()
            connection.execute(
                """
                INSERT INTO task_blueprints(
                  id, blueprint_slug, source_rev, unit_id, family_key, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (blueprint_id, blueprint_slug, source_rev, unit_id, family_key, utc_now_iso(clock)),
            )
            connection.commit()
        return blueprint_id

    def register_task_blueprint_version(
        self,
        *,
        blueprint_id: str,
        spec_json: str,
        content_hash: str,
        canonical_hash: str,
        authoring_version: str,
        model_version: str | None,
        provenance_version: str,
        exemplars: Sequence[Mapping[str, Any]],
        detail_json: str | None = None,
        author: str = "owner",
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Register an immutable, content-addressed draft blueprint version + its
        exemplar link rows + a ``registered`` review event, all in one transaction.
        Idempotent on ``UNIQUE(blueprint_id, content_hash)``."""

        now = utc_now_iso(clock)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM task_blueprint_versions WHERE blueprint_id = ? AND content_hash = ?",
                (blueprint_id, content_hash),
            ).fetchone()
            if existing is not None:
                connection.execute("ROLLBACK")
                return {"version": dict(existing), "already_exists": True}
            versions = connection.execute(
                "SELECT version FROM task_blueprint_versions WHERE blueprint_id = ?",
                (blueprint_id,),
            ).fetchall()
            next_version = max((row["version"] for row in versions), default=0) + 1
            version_id = new_ulid()
            connection.execute(
                """
                INSERT INTO task_blueprint_versions(
                  id, blueprint_id, version, status, spec_json, content_hash,
                  canonical_hash, authoring_version, model_version, provenance_version,
                  reviewed_at, activated_at, created_at
                )
                VALUES (?, ?, ?, 'draft', ?, ?, ?, ?, ?, ?, NULL, NULL, ?)
                """,
                (
                    version_id, blueprint_id, next_version, spec_json, content_hash,
                    canonical_hash, authoring_version, model_version, provenance_version, now,
                ),
            )
            for exemplar in exemplars:
                connection.execute(
                    """
                    INSERT INTO target_exemplars(
                      id, blueprint_version_id, exemplar_ref, weight, exposure_status,
                      held_out_weight, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_ulid(), version_id, exemplar["exemplar_ref"],
                        float(exemplar.get("weight", 1.0)),
                        exemplar.get("exposure_status", "familiar_anchor"),
                        float(exemplar.get("held_out_weight", 0.0)), now,
                    ),
                )
            connection.execute(
                """
                INSERT INTO task_blueprint_review_events(
                  id, blueprint_version_id, kind, detail_json, author, created_at
                )
                VALUES (?, ?, 'registered', ?, ?, ?)
                """,
                (new_ulid(), version_id, detail_json, author, now),
            )
            row = connection.execute(
                "SELECT * FROM task_blueprint_versions WHERE id = ?", (version_id,)
            ).fetchone()
            connection.execute("COMMIT")
            return {"version": dict(row), "already_exists": False}
        except Exception:
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def transition_task_blueprint_version(
        self,
        *,
        blueprint_version_id: str,
        status: str,
        event_kind: str,
        detail_json: str | None = None,
        author: str = "owner",
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Advance a blueprint version's status (reviewed/active/retired) and append
        the matching review event atomically. Returns the updated version row."""

        now = utc_now_iso(clock)
        stamp_column = {
            "reviewed": "reviewed_at",
            "active": "activated_at",
        }.get(status)
        with self.connection() as connection:
            if stamp_column is not None:
                connection.execute(
                    f"UPDATE task_blueprint_versions SET status = ?, {stamp_column} = ? WHERE id = ?",
                    (status, now, blueprint_version_id),
                )
            else:
                connection.execute(
                    "UPDATE task_blueprint_versions SET status = ? WHERE id = ?",
                    (status, blueprint_version_id),
                )
            connection.execute(
                """
                INSERT INTO task_blueprint_review_events(
                  id, blueprint_version_id, kind, detail_json, author, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (new_ulid(), blueprint_version_id, event_kind, detail_json, author, now),
            )
            row = connection.execute(
                "SELECT * FROM task_blueprint_versions WHERE id = ?", (blueprint_version_id,)
            ).fetchone()
            connection.commit()
        return dict(row) if row is not None else {}

    def append_task_blueprint_review_event(
        self,
        *,
        blueprint_version_id: str,
        kind: str,
        detail_json: str | None = None,
        author: str = "owner",
        clock: Clock | None = None,
    ) -> str:
        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO task_blueprint_review_events(
                  id, blueprint_version_id, kind, detail_json, author, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_id, blueprint_version_id, kind, detail_json, author, utc_now_iso(clock)),
            )
            connection.commit()
        return event_id

    def task_blueprint_version(self, blueprint_version_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM task_blueprint_versions WHERE id = ?", (blueprint_version_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def task_blueprint_versions_for(self, blueprint_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM task_blueprint_versions WHERE blueprint_id = ? ORDER BY version",
                (blueprint_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def target_exemplars_for(self, blueprint_version_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM target_exemplars WHERE blueprint_version_id = ? ORDER BY exemplar_ref",
                (blueprint_version_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def task_blueprint_review_events_for(self, blueprint_version_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM task_blueprint_review_events WHERE blueprint_version_id = ? ORDER BY created_at, id",
                (blueprint_version_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def reviewed_reading_question_placements(
        self,
        *,
        source_revs: Sequence[str],
        unit_ids: Sequence[str],
        blueprint_version_ids: Sequence[str] = (),
    ) -> list[dict[str, Any]]:
        """Return the reviewed blueprint artifacts that can appear in a Reader.

        P3 deliberately has no hot-path question planner: a question is eligible
        only when an owner placed it on a reviewed/active TaskBlueprint version.
        The optional version ids let an active golden-path contract resolve its
        pinned blueprint even when an older source used a semantic revision slug
        rather than the source-layer revision id.
        """

        source_values = tuple(dict.fromkeys(value for value in source_revs if value))
        unit_values = tuple(dict.fromkeys(value for value in unit_ids if value))
        version_values = tuple(dict.fromkeys(value for value in blueprint_version_ids if value))
        clauses: list[str] = []
        params: list[Any] = []
        if source_values and unit_values:
            source_marks = ", ".join("?" for _ in source_values)
            unit_marks = ", ".join("?" for _ in unit_values)
            clauses.append(f"(tb.source_rev IN ({source_marks}) AND tb.unit_id IN ({unit_marks}))")
            params.extend(source_values)
            params.extend(unit_values)
        if version_values:
            version_marks = ", ".join("?" for _ in version_values)
            clauses.append(f"tbv.id IN ({version_marks})")
            params.extend(version_values)
        if not clauses:
            return []

        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT
                  e.id AS placement_event_id,
                  e.detail_json AS placement_json,
                  e.created_at AS placement_created_at,
                  tbv.id AS blueprint_version_id,
                  tbv.version AS blueprint_version,
                  tbv.status AS blueprint_status,
                  tbv.spec_json AS blueprint_spec_json,
                  tb.id AS blueprint_id,
                  tb.source_rev,
                  tb.unit_id,
                  tb.family_key
                FROM task_blueprint_review_events e
                JOIN task_blueprint_versions tbv ON tbv.id = e.blueprint_version_id
                JOIN task_blueprints tb ON tb.id = tbv.blueprint_id
                WHERE e.kind = 'reading_question_placed'
                  AND tbv.status IN ('reviewed', 'active')
                  AND ({' OR '.join(clauses)})
                ORDER BY
                  CASE tbv.status WHEN 'active' THEN 0 ELSE 1 END,
                  tbv.version DESC,
                  e.created_at,
                  e.id
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # P2 golden path -- atomic confirmation + run events (spec_p2 §3.1, §4, 082)
    # ------------------------------------------------------------------

    def confirm_golden_path_atomic(
        self,
        *,
        receipt_key: str,
        blueprint_version_id: str,
        goal_id: str,
        goal_contract: Mapping[str, Any],
        commitment: Mapping[str, Any],
        run: Mapping[str, Any],
        reservation: Mapping[str, Any] | None = None,
        fault_hook: Any = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """The ONE atomic confirmation (spec_p2 §3.1). In a single transaction:
        activate the reviewed blueprint, append goal-contract v1 + head, insert the
        commitment (+v1 version/targets/created event), reserve the fresh assessment
        surface, and mint the run + ``run_started`` event. If ANY part fails the whole
        transaction rolls back and nothing becomes active.

        Idempotent on ``golden_path_runs.receipt_key`` -- a byte-identical re-confirm
        returns the existing run with ``already_exists=True``.

        ``fault_hook`` is a test-only seam: a callable invoked with a stage label
        after each internal write. Raising inside it proves the whole boundary rolls
        back (the §12.6 fault-injection acceptance) -- no partial confirmation.
        """

        def _fault(label: str) -> None:
            if fault_hook is not None:
                fault_hook(label)

        now = utc_now_iso(clock)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("BEGIN IMMEDIATE")

            existing_run = connection.execute(
                "SELECT * FROM golden_path_runs WHERE receipt_key = ?", (receipt_key,)
            ).fetchone()
            if existing_run is not None:
                connection.execute("ROLLBACK")
                return {"run": dict(existing_run), "already_exists": True}

            # Step 1: activate the reviewed blueprint (assert reviewed/active).
            bp = connection.execute(
                "SELECT status FROM task_blueprint_versions WHERE id = ?",
                (blueprint_version_id,),
            ).fetchone()
            if bp is None or bp["status"] not in ("reviewed", "active"):
                connection.execute("ROLLBACK")
                raise BlueprintNotReviewed(
                    blueprint_version_id, status=bp["status"] if bp else None
                )
            if bp["status"] == "reviewed":
                connection.execute(
                    "UPDATE task_blueprint_versions SET status = 'active', activated_at = ? WHERE id = ?",
                    (now, blueprint_version_id),
                )
                connection.execute(
                    """
                    INSERT INTO task_blueprint_review_events(
                      id, blueprint_version_id, kind, detail_json, author, created_at
                    )
                    VALUES (?, ?, 'activated', ?, 'owner', ?)
                    """,
                    (new_ulid(), blueprint_version_id, _json({"receipt_key": receipt_key}), now),
                )
            _fault("blueprint_activated")

            # Step 2: goal-contract v1 (idempotent on content_hash; fresh head only).
            head_row = connection.execute(
                "SELECT head_version_id FROM goal_contract_heads WHERE goal_id = ?",
                (goal_id,),
            ).fetchone()
            existing_gcv = connection.execute(
                "SELECT id FROM goal_contract_versions WHERE goal_id = ? AND content_hash = ?",
                (goal_id, goal_contract["content_hash"]),
            ).fetchone()
            if existing_gcv is not None:
                goal_contract_version_id = existing_gcv["id"]
            else:
                if head_row is not None:
                    connection.execute("ROLLBACK")
                    raise GoalAlreadyConfirmed(
                        goal_id, head_version_id=head_row["head_version_id"]
                    )
                goal_contract_version_id = new_ulid()
                connection.execute(
                    """
                    INSERT INTO goal_contract_versions(
                      id, goal_id, version, predecessor_version_id, contract_json,
                      content_hash, support_hash, contract_schema_version, change_class,
                      envelope_version, predecessor_milestone, activated_edge_id,
                      evidence_receipt_json, burden_delta_json, author, reason, created_at
                    )
                    VALUES (?, ?, 1, NULL, ?, ?, ?, ?, 'confirm', ?, NULL, NULL, NULL, NULL, ?, NULL, ?)
                    """,
                    (
                        goal_contract_version_id, goal_id, goal_contract["contract_json"],
                        goal_contract["content_hash"], goal_contract["support_hash"],
                        int(goal_contract["contract_schema_version"]),
                        goal_contract.get("head_envelope_version"),
                        goal_contract.get("author", "learner"), now,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO goal_contract_heads(
                      goal_id, head_version_id, head_version, head_content_hash,
                      head_support_hash, head_envelope_version, updated_at
                    )
                    VALUES (?, ?, 1, ?, ?, ?, ?)
                    """,
                    (
                        goal_id, goal_contract_version_id, goal_contract["content_hash"],
                        goal_contract["support_hash"], goal_contract.get("head_envelope_version"), now,
                    ),
                )
            _fault("goal_contract_appended")

            # Step 3: commitment + v1 version/targets/created event (reuses the shared
            # row-builder so the commitment shape stays identical to create_commitment).
            commitment_id = new_ulid()
            connection.execute(
                """
                INSERT INTO commitments(
                  id, learner_id, created_action, idempotency_key, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    commitment_id, commitment.get("learner_id", "local"),
                    commitment["created_action"], commitment.get("idempotency_key"), now,
                ),
            )
            commitment_version_id = self._insert_commitment_version_rows(
                connection,
                commitment_id=commitment_id,
                predecessor_version_id=None,
                version=1,
                version_fields=commitment["version_fields"],
                targets=commitment["targets"],
                author=commitment.get("author", "learner"),
                change_reason=None,
                events=[{"kind": "created", "detail": {"action": commitment["created_action"]}}],
                now=now,
            )
            _fault("commitment_created")

            # Step 4: reserve the fresh held-out assessment surface (§8.1).
            reservation_id: str | None = None
            if reservation is not None:
                reservation_id = new_ulid()
                connection.execute(
                    """
                    INSERT INTO activity_surface_reservations(
                      id, surface_id, goal_id, target_contract_version_id,
                      target_support_hash, purpose, status, eligibility_json,
                      administration_id, reserved_at, closed_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'reserved', ?, NULL, ?, NULL)
                    """,
                    (
                        reservation_id, reservation["surface_id"], goal_id,
                        goal_contract_version_id, reservation.get("target_support_hash"),
                        reservation.get("purpose", "assessment"),
                        reservation.get("eligibility_json", "{}"), now,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO activity_surface_lifecycle_events(
                      id, surface_id, reservation_id, administration_id, kind,
                      reason, detail_json, created_at
                    )
                    VALUES (?, ?, ?, NULL, 'reserve', ?, NULL, ?)
                    """,
                    (
                        new_ulid(), reservation["surface_id"], reservation_id,
                        "golden_path_confirm", now,
                    ),
                )
            _fault("reserve_created")

            # Step 5: mint the run + run_started event (written LAST -- the run row is
            # what makes the confirmation "active"; a partial failure never reaches it).
            run_id = new_ulid()
            mode = run.get("mode", "certifying")
            connection.execute(
                """
                INSERT INTO golden_path_runs(
                  id, receipt_key, learner_id, goal_id, commitment_id,
                  commitment_version_id, source_rev, unit_id, blueprint_version_id,
                  goal_contract_version_id, depth_policy_version_id,
                  depth_envelope_version_id, initial_milestone, reserved_reservation_id,
                  reserved_surface_id, reserved_support_hash, mode,
                  orchestration_policy_json, decision_param_manifest_json,
                  visible_caps_json, current_state, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ready', ?, ?)
                """,
                (
                    run_id, receipt_key, run.get("learner_id", "local"), goal_id,
                    commitment_id, commitment_version_id, run["source_rev"], run["unit_id"],
                    blueprint_version_id, goal_contract_version_id,
                    commitment["version_fields"].get("depth_policy_version_id"),
                    commitment["version_fields"].get("depth_envelope_version_id"),
                    run["initial_milestone"], reservation_id,
                    reservation["surface_id"] if reservation is not None else None,
                    reservation.get("target_support_hash") if reservation is not None else None,
                    mode, run.get("orchestration_policy_json"),
                    run.get("decision_param_manifest_json"), run.get("visible_caps_json"),
                    now, now,
                ),
            )
            connection.execute(
                """
                INSERT INTO golden_path_run_events(
                  id, run_id, seq, from_state, to_state, reason,
                  feasible_alternatives_json, evidence_ids_json,
                  goal_contract_head_version_id, depth_policy_version_id,
                  depth_envelope_version_id, predecessor_milestone, successor_milestone,
                  selected_activity_json, policy_calibration_json, burden_json,
                  expected_head_event_id, idempotency_key, created_at
                )
                VALUES (?, ?, 1, 'draft', 'ready', 'run_started', NULL, NULL, ?, ?, ?, NULL, ?, NULL, NULL, NULL, NULL, ?, ?)
                """,
                (
                    new_ulid(), run_id, goal_contract_version_id,
                    commitment["version_fields"].get("depth_policy_version_id"),
                    commitment["version_fields"].get("depth_envelope_version_id"),
                    run["initial_milestone"], receipt_key + ":start", now,
                ),
            )
            _fault("run_started")

            connection.execute("COMMIT")
            run_row = self.golden_path_run(run_id)
            return {
                "run": run_row,
                "already_exists": False,
                "goal_contract_version_id": goal_contract_version_id,
                "commitment_id": commitment_id,
                "commitment_version_id": commitment_version_id,
                "reservation_id": reservation_id,
            }
        except Exception:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise
        finally:
            connection.close()

    def golden_path_run(self, run_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM golden_path_runs WHERE id = ?", (run_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def golden_path_run_by_receipt(self, receipt_key: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM golden_path_runs WHERE receipt_key = ?", (receipt_key,)
            ).fetchone()
        return dict(row) if row is not None else None

    def golden_path_runs_all(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM golden_path_runs ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def golden_path_run_for_goal(self, goal_id: str) -> dict[str, Any] | None:
        """The earliest golden-path run for a goal (the golden path is one run per
        goal). Used by confirmation to detect a re-confirm that differs only in a
        run-shaping param (C4)."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM golden_path_runs WHERE goal_id = ? ORDER BY created_at, id LIMIT 1",
                (goal_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def golden_path_run_events_for(self, run_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM golden_path_run_events WHERE run_id = ? ORDER BY seq",
                (run_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def append_golden_path_run_event(
        self,
        *,
        run_id: str,
        to_state: str,
        reason: str,
        expected_head_event_id: str | None = None,
        idempotency_key: str | None = None,
        feasible_alternatives_json: str | None = None,
        evidence_ids_json: str | None = None,
        goal_contract_head_version_id: str | None = None,
        depth_policy_version_id: str | None = None,
        depth_envelope_version_id: str | None = None,
        predecessor_milestone: str | None = None,
        successor_milestone: str | None = None,
        selected_activity_json: str | None = None,
        policy_calibration_json: str | None = None,
        burden_json: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Append one transition event and update the run's cached head state, in one
        transaction. Fenced on ``expected_head_event_id`` (§4.3 optimistic head) and
        idempotent on ``UNIQUE(run_id, idempotency_key)`` (§12.6 exactly-once). On an
        idempotency-key replay returns the existing event with ``already_exists=True``;
        on a fence mismatch returns ``{"stale": True, ...}`` and writes nothing."""

        now = utc_now_iso(clock)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("BEGIN IMMEDIATE")
            if idempotency_key is not None:
                prior = connection.execute(
                    "SELECT * FROM golden_path_run_events WHERE run_id = ? AND idempotency_key = ?",
                    (run_id, idempotency_key),
                ).fetchone()
                if prior is not None:
                    connection.execute("ROLLBACK")
                    return {"event": dict(prior), "already_exists": True}
            head = connection.execute(
                "SELECT * FROM golden_path_run_events WHERE run_id = ? ORDER BY seq DESC LIMIT 1",
                (run_id,),
            ).fetchone()
            head_id = head["id"] if head is not None else None
            head_seq = head["seq"] if head is not None else 0
            from_state = head["to_state"] if head is not None else None
            if expected_head_event_id is not None and expected_head_event_id != head_id:
                connection.execute("ROLLBACK")
                return {"stale": True, "expected": expected_head_event_id, "actual": head_id}
            event_id = new_ulid()
            next_seq = head_seq + 1
            connection.execute(
                """
                INSERT INTO golden_path_run_events(
                  id, run_id, seq, from_state, to_state, reason,
                  feasible_alternatives_json, evidence_ids_json,
                  goal_contract_head_version_id, depth_policy_version_id,
                  depth_envelope_version_id, predecessor_milestone, successor_milestone,
                  selected_activity_json, policy_calibration_json, burden_json,
                  expected_head_event_id, idempotency_key, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id, run_id, next_seq, from_state, to_state, reason,
                    feasible_alternatives_json, evidence_ids_json,
                    goal_contract_head_version_id, depth_policy_version_id,
                    depth_envelope_version_id, predecessor_milestone, successor_milestone,
                    selected_activity_json, policy_calibration_json, burden_json,
                    expected_head_event_id, idempotency_key, now,
                ),
            )
            connection.execute(
                "UPDATE golden_path_runs SET current_state = ?, updated_at = ? WHERE id = ?",
                (to_state, now, run_id),
            )
            connection.execute("COMMIT")
            row = connection.execute(
                "SELECT * FROM golden_path_run_events WHERE id = ?", (event_id,)
            ).fetchone()
            return {"event": dict(row), "already_exists": False}
        except Exception:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise
        finally:
            connection.close()

    # ------------------------------------------------------------------
    # P2 DIAGNOSTIC track -- diagnostic pack + two-tier triage
    # (spec_p2 §5, §6, U-027, U-028; migration 083)
    # ------------------------------------------------------------------

    def ensure_diagnostic_pack(
        self,
        *,
        pack_slug: str,
        blueprint_version_id: str,
        content_hash: str,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Register/return the stable diagnostic pack row. Idempotent on ``pack_slug``
        AND content_hash: a re-register of the byte-identical pack returns the existing
        row (``already_exists=True``) so pack assembly is deterministic (§5.1)."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT * FROM diagnostic_packs WHERE pack_slug = ?", (pack_slug,)
            ).fetchone()
            if existing is not None:
                return {"pack": dict(existing), "already_exists": True}
            pack_id = new_ulid()
            connection.execute(
                """
                INSERT INTO diagnostic_packs(
                  id, pack_slug, blueprint_version_id, status, content_hash, created_at
                )
                VALUES (?, ?, ?, 'draft', ?, ?)
                """,
                (pack_id, pack_slug, blueprint_version_id, content_hash, now),
            )
            connection.execute(
                """
                INSERT INTO diagnostic_pack_events(
                  id, pack_id, card_slug, kind, detail_json, author, created_at
                )
                VALUES (?, ?, NULL, 'registered', ?, 'owner', ?)
                """,
                (new_ulid(), pack_id, _json({"content_hash": content_hash}), now),
            )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM diagnostic_packs WHERE id = ?", (pack_id,)
            ).fetchone()
            return {"pack": dict(row), "already_exists": False}

    def register_diagnostic_pack_card(
        self,
        *,
        pack_id: str,
        card_slug: str,
        coverage_json: str,
        content_hash: str,
        instrument_ref: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Register a candidate diagnostic-purpose card. Idempotent on
        ``UNIQUE(pack_id, card_slug)``."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM diagnostic_pack_cards WHERE pack_id = ? AND card_slug = ?",
                (pack_id, card_slug),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            card_id = new_ulid()
            connection.execute(
                """
                INSERT INTO diagnostic_pack_cards(
                  id, pack_id, card_slug, purpose, coverage_json, instrument_ref,
                  admission_status, content_hash, created_at
                )
                VALUES (?, ?, ?, 'diagnostic', ?, ?, 'candidate', ?, ?)
                """,
                (card_id, pack_id, card_slug, coverage_json, instrument_ref, content_hash, now),
            )
            connection.commit()
            return card_id

    def set_diagnostic_pack_card_admission(
        self,
        *,
        pack_id: str,
        card_slug: str,
        admission_status: str,
        detail_json: str | None = None,
        author: str = "owner",
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        kind = "admitted" if admission_status == "admitted" else "rejected"
        with self.connection() as connection:
            connection.execute(
                "UPDATE diagnostic_pack_cards SET admission_status = ? WHERE pack_id = ? AND card_slug = ?",
                (admission_status, pack_id, card_slug),
            )
            connection.execute(
                """
                INSERT INTO diagnostic_pack_events(
                  id, pack_id, card_slug, kind, detail_json, author, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (new_ulid(), pack_id, card_slug, kind, detail_json, author, now),
            )
            connection.commit()

    def transition_diagnostic_pack(
        self,
        *,
        pack_id: str,
        status: str,
        kind: str,
        detail_json: str | None = None,
        author: str = "owner",
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                "UPDATE diagnostic_packs SET status = ? WHERE id = ?", (status, pack_id)
            )
            connection.execute(
                """
                INSERT INTO diagnostic_pack_events(
                  id, pack_id, card_slug, kind, detail_json, author, created_at
                )
                VALUES (?, ?, NULL, ?, ?, ?, ?)
                """,
                (new_ulid(), pack_id, kind, detail_json, author, now),
            )
            connection.commit()

    def diagnostic_pack(self, pack_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM diagnostic_packs WHERE id = ?", (pack_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def diagnostic_pack_by_slug(self, pack_slug: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM diagnostic_packs WHERE pack_slug = ?", (pack_slug,)
            ).fetchone()
        return dict(row) if row is not None else None

    def diagnostic_packs_for_blueprint(self, blueprint_version_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM diagnostic_packs WHERE blueprint_version_id = ? ORDER BY created_at, id",
                (blueprint_version_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def diagnostic_pack_cards_for(self, pack_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM diagnostic_pack_cards WHERE pack_id = ? ORDER BY card_slug",
                (pack_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def diagnostic_pack_events_for(self, pack_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM diagnostic_pack_events WHERE pack_id = ? ORDER BY created_at, id",
                (pack_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def pin_diagnostic_pack(
        self,
        *,
        run_id: str,
        pack_id: str,
        goal_contract_version_id: str,
        visible_cap: int,
        probe_episode_id: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Pin exactly one reviewed pack to a run at diagnostic entry (§5.2).
        Idempotent on ``UNIQUE(run_id)`` -- a re-pin returns the existing pin."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT * FROM diagnostic_pack_pins WHERE run_id = ?", (run_id,)
            ).fetchone()
            if existing is not None:
                return {"pin": dict(existing), "already_exists": True}
            pin_id = new_ulid()
            connection.execute(
                """
                INSERT INTO diagnostic_pack_pins(
                  id, run_id, pack_id, goal_contract_version_id, probe_episode_id,
                  visible_cap, pinned_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (pin_id, run_id, pack_id, goal_contract_version_id, probe_episode_id, visible_cap, now),
            )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM diagnostic_pack_pins WHERE id = ?", (pin_id,)
            ).fetchone()
            return {"pin": dict(row), "already_exists": False}

    def diagnostic_pack_pin_for_run(self, run_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM diagnostic_pack_pins WHERE run_id = ?", (run_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    # --- failure triage -------------------------------------------------

    def failure_triage_routes(self, *, active_only: bool = True) -> list[dict[str, Any]]:
        with self.connection() as connection:
            if active_only:
                rows = connection.execute(
                    "SELECT * FROM failure_triage_routes WHERE active = 1 ORDER BY reason, route_version"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM failure_triage_routes ORDER BY reason, route_version"
                ).fetchall()
        return [dict(row) for row in rows]

    def failure_triage_route_for_reason(self, reason: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM failure_triage_routes WHERE reason = ? AND active = 1 "
                "ORDER BY route_version DESC LIMIT 1",
                (reason,),
            ).fetchone()
        return dict(row) if row is not None else None

    def append_failure_triage_event(
        self,
        *,
        run_id: str,
        kind: str,
        tier: str,
        decisive: bool,
        attempt_id: str | None = None,
        route_id: str | None = None,
        selected_reason: str | None = None,
        distribution_json: str | None = None,
        alternatives_json: str | None = None,
        inputs_snapshot_json: str | None = None,
        routing_prior_json: str | None = None,
        override_actor: str | None = None,
        override_reason: str | None = None,
        anchor_sample_id: str | None = None,
        auto_committed: bool = False,
        goal_contract_head_version_id: str | None = None,
        idempotency_key: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Append one triage decision to the append-only ledger (§6.1). ``seq`` is a
        monotone per-run ordinal computed inside the write transaction. When
        ``idempotency_key`` is supplied, a retried append with the same key returns the
        EXISTING event instead of writing a duplicate (§12.6 exactly-once)."""

        now = utc_now_iso(clock)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("BEGIN IMMEDIATE")
            if idempotency_key is not None:
                existing = connection.execute(
                    "SELECT * FROM failure_triage_events WHERE run_id = ? AND idempotency_key = ?",
                    (run_id, idempotency_key),
                ).fetchone()
                if existing is not None:
                    connection.execute("ROLLBACK")
                    return dict(existing)
            head = connection.execute(
                "SELECT COALESCE(MAX(seq), 0) AS s FROM failure_triage_events WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            seq = int(head["s"]) + 1
            event_id = new_ulid()
            connection.execute(
                """
                INSERT INTO failure_triage_events(
                  id, run_id, attempt_id, kind, tier, decisive, route_id, selected_reason,
                  distribution_json, alternatives_json, inputs_snapshot_json, routing_prior_json,
                  override_actor, override_reason, anchor_sample_id, auto_committed,
                  goal_contract_head_version_id, seq, idempotency_key, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id, run_id, attempt_id, kind, tier, 1 if decisive else 0, route_id,
                    selected_reason, distribution_json, alternatives_json, inputs_snapshot_json,
                    routing_prior_json, override_actor, override_reason, anchor_sample_id,
                    1 if auto_committed else 0, goal_contract_head_version_id, seq,
                    idempotency_key, now,
                ),
            )
            connection.execute("COMMIT")
            row = connection.execute(
                "SELECT * FROM failure_triage_events WHERE id = ?", (event_id,)
            ).fetchone()
            return dict(row)
        except Exception:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise
        finally:
            connection.close()

    def failure_triage_events_for(self, run_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM failure_triage_events WHERE run_id = ? ORDER BY seq",
                (run_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def failure_triage_event(self, event_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM failure_triage_events WHERE id = ?", (event_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    # ------------------------------------------------------------------
    # P2 step B.11 -- reader dialogue (U-033, §7.6). Reader events ride the P0
    # interaction_events envelope (migration 086 extends the kind vocabulary);
    # these read helpers back the reader service + the replay-derived routing
    # prior projection. No new event table.
    # ------------------------------------------------------------------

    def reader_interaction_events(
        self,
        *,
        kind: str | None = None,
        subject_id: str | None = None,
        subject_type: str | None = None,
        since: str | None = None,
    ) -> list[dict[str, Any]]:
        """Reader interaction events (payload_json decoded), oldest first."""

        query = "SELECT * FROM interaction_events WHERE 1 = 1"
        params: list[Any] = []
        if kind is not None:
            query += " AND kind = ?"
            params.append(kind)
        if subject_id is not None:
            query += " AND subject_id = ?"
            params.append(subject_id)
        if subject_type is not None:
            query += " AND subject_type = ?"
            params.append(subject_type)
        if since is not None:
            query += " AND created_at >= ?"
            params.append(since)
        query += " ORDER BY created_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            event = dict(row)
            event["payload"] = _loads(event.get("payload_json"), None)
            out.append(event)
        return out

    def first_cold_observation_for_target(
        self, target_contract_version_id: str
    ) -> str | None:
        """created_at of the FIRST cold administration pinned to this target
        contract version (design A.1 supersession). Cold = no reading phase, a
        measuring purpose (assessment/practice/diagnostic), and no
        ``source_visible`` in the recorded administration context. Returns None
        when no cold observation exists yet -- the reading-answer routing prior
        then still contributes."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT created_at, purpose, reading_phase, admin_context_json
                  FROM activity_administrations
                 WHERE target_contract_version_id = ?
                   AND reading_phase IS NULL
                   AND purpose IN ('assessment', 'practice', 'diagnostic')
                 ORDER BY created_at, id
                """,
                (target_contract_version_id,),
            ).fetchall()
        for row in rows:
            context = _loads(row["admin_context_json"], None) or {}
            if isinstance(context, Mapping) and context.get("source_visible") is True:
                continue
            return row["created_at"]
        return None

    # ------------------------------------------------------------------
    # P2 LEARNING track -- pattern-ladder policy (spec_p2 §7.1, §7.2;
    # migration 084). The ladder POLICY is reviewable DATA; ladder STATE lives on
    # golden_path_run_events (no parallel table).
    # ------------------------------------------------------------------

    def active_ladder_policy(self, policy_slug: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM p2_ladder_policies WHERE policy_slug = ? AND status = 'active' "
                "ORDER BY policy_version DESC LIMIT 1",
                (policy_slug,),
            ).fetchone()
        return dict(row) if row is not None else None

    def ladder_stages_for_policy(self, policy_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM p2_ladder_stages WHERE policy_id = ? ORDER BY ordinal, stage_key",
                (policy_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def activity_family_purpose_for_card_version(self, card_version_id: str) -> str | None:
        """The immutable family purpose backing a card version (§12.4 role check).
        Joins card_version -> card -> family; returns None when the row is absent."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT f.purpose AS purpose
                  FROM activity_card_versions cv
                  JOIN activity_cards c ON c.id = cv.card_id
                  JOIN activity_families f ON f.id = c.family_id
                 WHERE cv.id = ?
                """,
                (card_version_id,),
            ).fetchone()
        return row["purpose"] if row is not None else None

    # ------------------------------------------------------------------
    # P2 PRACTICE track -- rotating practice pool (spec_p2 §7.3, U-028;
    # migration 085).
    # ------------------------------------------------------------------

    def ensure_practice_pool(
        self,
        *,
        pool_slug: str,
        blueprint_version_id: str,
        content_hash: str,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Register/return the stable practice pool row. Idempotent on ``pool_slug``:
        a re-register returns the existing row (``already_exists=True``) so pool
        assembly is deterministic (§7.3)."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT * FROM practice_pools WHERE pool_slug = ?", (pool_slug,)
            ).fetchone()
            if existing is not None:
                return {"pool": dict(existing), "already_exists": True}
            pool_id = new_ulid()
            connection.execute(
                """
                INSERT INTO practice_pools(
                  id, pool_slug, blueprint_version_id, status, content_hash, created_at
                )
                VALUES (?, ?, ?, 'draft', ?, ?)
                """,
                (pool_id, pool_slug, blueprint_version_id, content_hash, now),
            )
            connection.execute(
                """
                INSERT INTO practice_pool_events(
                  id, pool_id, surface_slug, kind, detail_json, author, created_at
                )
                VALUES (?, ?, NULL, 'registered', ?, 'owner', ?)
                """,
                (new_ulid(), pool_id, _json({"content_hash": content_hash}), now),
            )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM practice_pools WHERE id = ?", (pool_id,)
            ).fetchone()
            return {"pool": dict(row), "already_exists": False}

    def register_practice_pool_surface(
        self,
        *,
        pool_id: str,
        surface_slug: str,
        angle: str,
        content_hash: str,
        provenance: str = "llm_within_bounds",
        surface_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Register a candidate practice surface. Idempotent on
        ``UNIQUE(pool_id, surface_slug)``."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM practice_pool_surfaces WHERE pool_id = ? AND surface_slug = ?",
                (pool_id, surface_slug),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            row_id = new_ulid()
            connection.execute(
                """
                INSERT INTO practice_pool_surfaces(
                  id, pool_id, surface_slug, angle, provenance, surface_id,
                  admission_status, content_hash, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'candidate', ?, ?)
                """,
                (row_id, pool_id, surface_slug, angle, provenance, surface_id, content_hash, now),
            )
            connection.commit()
            return row_id

    def set_practice_pool_surface_admission(
        self,
        *,
        pool_id: str,
        surface_slug: str,
        admission_status: str,
        surface_id: str | None = None,
        detail_json: str | None = None,
        author: str = "owner",
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        kind = "admitted" if admission_status == "admitted" else "rejected"
        with self.connection() as connection:
            if surface_id is not None:
                connection.execute(
                    "UPDATE practice_pool_surfaces SET admission_status = ?, surface_id = ? "
                    "WHERE pool_id = ? AND surface_slug = ?",
                    (admission_status, surface_id, pool_id, surface_slug),
                )
            else:
                connection.execute(
                    "UPDATE practice_pool_surfaces SET admission_status = ? "
                    "WHERE pool_id = ? AND surface_slug = ?",
                    (admission_status, pool_id, surface_slug),
                )
            connection.execute(
                """
                INSERT INTO practice_pool_events(
                  id, pool_id, surface_slug, kind, detail_json, author, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (new_ulid(), pool_id, surface_slug, kind, detail_json, author, now),
            )
            connection.commit()

    def transition_practice_pool(
        self,
        *,
        pool_id: str,
        status: str,
        kind: str,
        detail_json: str | None = None,
        author: str = "owner",
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                "UPDATE practice_pools SET status = ? WHERE id = ?", (status, pool_id)
            )
            connection.execute(
                """
                INSERT INTO practice_pool_events(
                  id, pool_id, surface_slug, kind, detail_json, author, created_at
                )
                VALUES (?, ?, NULL, ?, ?, ?, ?)
                """,
                (new_ulid(), pool_id, kind, detail_json, author, now),
            )
            connection.commit()

    def append_practice_pool_event(
        self,
        *,
        pool_id: str,
        kind: str,
        surface_slug: str | None = None,
        detail_json: str | None = None,
        author: str = "system",
        clock: Clock | None = None,
    ) -> str:
        """Append one pool ledger event (§7.3 audit) -- e.g. ``served`` / ``rotated``
        from ``next_practice_surface``. Pure ledger append; touches no pool status."""

        now = utc_now_iso(clock)
        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO practice_pool_events(
                  id, pool_id, surface_slug, kind, detail_json, author, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, pool_id, surface_slug, kind, detail_json, author, now),
            )
            connection.commit()
        return event_id

    def practice_pool(self, pool_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM practice_pools WHERE id = ?", (pool_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def practice_pool_by_slug(self, pool_slug: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM practice_pools WHERE pool_slug = ?", (pool_slug,)
            ).fetchone()
        return dict(row) if row is not None else None

    def practice_pools_for_blueprint(self, blueprint_version_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM practice_pools WHERE blueprint_version_id = ? ORDER BY created_at, id",
                (blueprint_version_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def practice_pool_surfaces_for(self, pool_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM practice_pool_surfaces WHERE pool_id = ? ORDER BY surface_slug",
                (pool_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def practice_pool_events_for(self, pool_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM practice_pool_events WHERE pool_id = ? ORDER BY created_at, id",
                (pool_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # P2 ASSESSMENT + RESTORATION + MILESTONE track (migration 087;
    # spec_p2 §8.2/§8.3/§8.4/§7.5; design B.8-B.10). Append-only inspectable
    # run artifacts -- NO measurement/posterior/FSRS/certification here.
    # ------------------------------------------------------------------

    def resolved_activity_for_surface(self, surface_id: str) -> dict[str, Any] | None:
        """Reconstruct the family/card identity of an existing surface (for opening a
        reserved assessment administration from the run's stored ``reserved_surface_id``
        alone). Returns the fields :class:`activities.ResolvedActivity` needs."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT s.id           AS surface_id,
                       s.surface_hash AS surface_hash,
                       s.fingerprint  AS fingerprint,
                       cv.id          AS card_version_id,
                       cv.card_id     AS card_id,
                       cv.card_contract_hash AS card_contract_hash,
                       c.family_id    AS family_id
                  FROM activity_surfaces s
                  JOIN activity_card_versions cv ON cv.id = s.card_version_id
                  JOIN activity_cards c ON c.id = cv.card_id
                 WHERE s.id = ?
                """,
                (surface_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def append_golden_path_artifact(
        self,
        *,
        run_id: str,
        kind: str,
        payload_json: str,
        idempotency_key: str | None = None,
        administration_id: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Append one inspectable run artifact (§8.4). Idempotent on
        ``UNIQUE(run_id, idempotency_key)``: a crash/retry collapses to exactly one
        artifact and returns the existing row with ``already_exists=True`` (§12.6)."""

        now = utc_now_iso(clock)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("BEGIN IMMEDIATE")
            if idempotency_key is not None:
                prior = connection.execute(
                    "SELECT * FROM golden_path_artifacts WHERE run_id = ? AND idempotency_key = ?",
                    (run_id, idempotency_key),
                ).fetchone()
                if prior is not None:
                    connection.execute("ROLLBACK")
                    return {"artifact": dict(prior), "already_exists": True}
            head = connection.execute(
                "SELECT seq FROM golden_path_artifacts WHERE run_id = ? ORDER BY seq DESC LIMIT 1",
                (run_id,),
            ).fetchone()
            next_seq = (head["seq"] if head is not None else 0) + 1
            artifact_id = new_ulid()
            connection.execute(
                """
                INSERT INTO golden_path_artifacts(
                  id, run_id, seq, kind, administration_id, payload_json,
                  idempotency_key, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact_id, run_id, next_seq, kind, administration_id,
                    payload_json, idempotency_key, now,
                ),
            )
            connection.execute("COMMIT")
            row = connection.execute(
                "SELECT * FROM golden_path_artifacts WHERE id = ?", (artifact_id,)
            ).fetchone()
            return {"artifact": dict(row), "already_exists": False}
        except Exception:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise
        finally:
            connection.close()

    def golden_path_artifacts_for(
        self, run_id: str, *, kind: str | None = None
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            if kind is None:
                rows = connection.execute(
                    "SELECT * FROM golden_path_artifacts WHERE run_id = ? ORDER BY seq",
                    (run_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM golden_path_artifacts WHERE run_id = ? AND kind = ? ORDER BY seq",
                    (run_id, kind),
                ).fetchall()
        return [dict(row) for row in rows]

    def latest_golden_path_artifact(
        self, run_id: str, *, kind: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM golden_path_artifacts WHERE run_id = ? AND kind = ? "
                "ORDER BY seq DESC LIMIT 1",
                (run_id, kind),
            ).fetchone()
        return dict(row) if row is not None else None


def _decode_source_conflict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["resolution"] = _loads(data.pop("resolution_json", None), None)
    return data


def _decode_maintenance_notice(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["detail"] = _loads(data.pop("detail_json", None), None)
    data["action"] = _loads(data.pop("action_json", None), {})
    return data


def _decode_synthesis_manifest(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    for key in (
        "membership",
        "revision_ids",
        "asset_hashes",
        "extraction_ids",
        "unit_inventory_versions",
        "scope",
        "brief",
        "extractor_versions",
        "token_budget",
        "estimated_usage",
    ):
        data[key] = _loads(data.pop(f"{key}_json", None), None)
    return data


def _decode_synthesis_run(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    for key in (
        "span_request",
        "resolved_span_hashes",
        "coverage_decisions",
        "actual_usage",
        "candidate_output",
    ):
        data[key] = _loads(data.pop(f"{key}_json", None), None)
    return data


def _decode_apply_intent(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["item_ids"] = _loads(data.pop("item_ids_json"), [])
    data["targets"] = _loads(data.pop("targets_json"), [])
    data["db_plan"] = _loads(data.pop("db_plan_json"), [])
    return data


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


def _guard_legacy_facet_write(state: Mapping[str, Any]) -> None:
    """KM2b hard stop (item 9): an mvp-0.7 vault must never write legacy per-LO
    facet state. The canonical projection is the single mvp-0.7 write mechanism;
    reaching this legacy upsert with an mvp-0.7 row is a re-key regression.

    Lazy import: repositories sits below the services layer, so importing the
    version constant at module scope would cycle back through grading/recall.
    """

    from learnloop.services.assessment_contracts import CANONICAL_STATE_VERSIONS

    if state.get("algorithm_version") in CANONICAL_STATE_VERSIONS:
        raise AssertionError(
            "legacy facet state (evidence_facet_recall_state / facet_uncertainty) "
            "must not be written under mvp-0.7/mvp-0.8; the canonical projection "
            "owns facet belief state (KM2b; P0.5 mvp-0.8 cutover)"
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


def _canonical_facet_recall_state(row: sqlite3.Row) -> CanonicalFacetRecallState:
    return CanonicalFacetRecallState(
        id=row["id"],
        facet_id=row["facet_id"],
        capability_key=row["capability_key"],
        practice_item_id=row["practice_item_id"],
        recall_alpha=row["recall_alpha"],
        recall_beta=row["recall_beta"],
        recall_mean=row["recall_mean"],
        recall_variance=row["recall_variance"],
        independent_evidence_mass=row["independent_evidence_mass"],
        raw_coverage_mass=row["raw_coverage_mass"],
        last_observed_at=row["last_observed_at"],
        last_error_at=row["last_error_at"],
        consecutive_failures=row["consecutive_failures"],
        algorithm_version=row["algorithm_version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _facet_capability_evidence(row: sqlite3.Row) -> FacetCapabilityEvidence:
    return FacetCapabilityEvidence(
        facet_id=row["facet_id"],
        capability=row["capability"],
        direct_positive_mass=row["direct_positive_mass"],
        direct_negative_mass=row["direct_negative_mass"],
        embedded_positive_mass=row["embedded_positive_mass"],
        embedded_negative_mass=row["embedded_negative_mass"],
        certification_credit=row["certification_credit"],
        independent_surface_groups=[str(g) for g in _loads(row["independent_surface_groups_json"], [])],
        algorithm_version=row["algorithm_version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _capability_residual_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "facet_id": row["facet_id"],
        "capability": row["capability"],
        "active": bool(row["active"]),
        "activation_reason": row["activation_reason"],
        "residual_alpha": row["residual_alpha"],
        "residual_beta": row["residual_beta"],
        "residual_mean": row["residual_mean"],
        "parent_alpha": row["parent_alpha"],
        "parent_beta": row["parent_beta"],
        "parent_mean": row["parent_mean"],
        "divergence": row["divergence"],
        "independent_groups": int(row["independent_groups"]),
        "independent_mass": row["independent_mass"],
        "algorithm_version": row["algorithm_version"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _resolve_merge(facet_id: str, merge_map: Mapping[str, str]) -> str:
    """Follow retired->surviving edges to the terminal survivor.

    Assumes the map is acyclic (enforced at write time by ``insert_facet_merge``);
    a defensive visited-set still guards against a malformed table."""

    seen: set[str] = set()
    current = facet_id
    while current in merge_map and current not in seen:
        seen.add(current)
        current = merge_map[current]
    return current


def _reaches(start: str, target: str, merge_map: Mapping[str, str]) -> bool:
    seen: set[str] = set()
    current = start
    while current in merge_map and current not in seen:
        if current == target:
            return True
        seen.add(current)
        current = merge_map[current]
    return current == target


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
        origin=row["origin"],
        required_facets=_loads(row["required_facets_json"], []),
        minimum_independent_observations=row["minimum_independent_observations"],
        maximum_observations=row["maximum_observations"],
        entered_at=row["entered_at"],
        completed_at=row["completed_at"],
        completion_reason=row["completion_reason"],
        algorithm_version=row["algorithm_version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        calibration_model_id=row["calibration_model_id"] if "calibration_model_id" in row.keys() else None,
        calibration_model_hash=row["calibration_model_hash"] if "calibration_model_hash" in row.keys() else None,
        probe_mapping_version=row["probe_mapping_version"] if "probe_mapping_version" in row.keys() else None,
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


def _decode_attempt(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["evidence_facets"] = _loads(payload.pop("evidence_facets_json"), [])
    payload["evidence_weights"] = _loads(payload.pop("evidence_weights_json"), {})
    payload["manual_review"] = bool(payload["manual_review"])
    payload["primed"] = bool(payload.get("primed", 0))
    payload["declared_dont_know"] = bool(payload.get("declared_dont_know", 0))
    return payload


def _decode_hypothesis_event(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["response_payload"] = _loads(payload.pop("response_payload_json"), None)
    return payload


def _decode_forecast(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["model_coverage"] = _loads(payload.pop("model_coverage_json"), {})
    return payload


def _decode_remediation_episode(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["passages_shown"] = _loads(payload.pop("passages_shown_json"), [])
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
        mechanism=_row_opt(row, "mechanism"),
        operation=_row_opt(row, "operation"),
        target_facet=_row_opt(row, "target_facet"),
        confused_with_facet=_row_opt(row, "confused_with_facet"),
        trigger_conditions=_loads(_row_opt(row, "trigger_conditions_json"), []),
        expected_signatures=_loads(_row_opt(row, "expected_signatures_json"), []),
        first_divergence=_loads(_row_opt(row, "first_divergence_json"), []),
        non_applicable_controls=_loads(_row_opt(row, "non_applicable_controls_json"), []),
        promotion_reason=_row_opt(row, "promotion_reason"),
        correction_statement=_row_opt(row, "correction_statement"),
        correction_source_span_ids=_loads(
            _row_opt(row, "correction_source_span_ids_json"), []
        ),
    )


def _row_opt(row: sqlite3.Row, key: str) -> Any:
    """Row value for ``key`` or ``None`` when the column is absent.

    Tolerates rows produced before migration 047 (KM4 additive columns).
    """

    try:
        return row[key]
    except (IndexError, KeyError):
        return None


def _decode_misconception_candidate(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "learning_object_id": row["learning_object_id"],
        "concept_id": row["concept_id"],
        "statement": row["statement"],
        "statement_normalized": row["statement_normalized"],
        "signature": row["signature"],
        "mechanism": row["mechanism"],
        "operation": row["operation"],
        "target_facet": row["target_facet"],
        "confused_with_facet": row["confused_with_facet"],
        "facet_ids": _loads(row["facet_ids_json"], []),
        "source_error_event_ids": _loads(row["source_error_event_ids_json"], []),
        "surface_families": _loads(row["surface_families_json"], []),
        "item_ids": _loads(row["item_ids_json"], []),
        "occurrence_count": row["occurrence_count"],
        "severity": row["severity"],
        "status": row["status"],
        "promoted_misconception_id": row["promoted_misconception_id"],
        "promotion_reason": row["promotion_reason"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


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
    if "dependency_block_reason_json" in payload:
        payload["dependency_block_reason"] = _loads(payload.pop("dependency_block_reason_json"), None)
    return payload


def _decode_extraction_run(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["model_versions"] = _loads(payload.pop("model_versions_json", None), {})
    payload["config"] = _loads(payload.pop("config_json", None), {})
    payload["page_selection"] = _loads(payload.pop("page_selection_json", None), None)
    payload["health"] = _loads(payload.pop("health_json", None), {})
    return payload


def _decode_unit_selection(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["selected_unit_ids"] = _loads(payload.pop("selected_unit_ids_json", None), [])
    payload["boundary_overrides"] = _loads(payload.pop("boundary_overrides_json", None), [])
    payload["needs_review"] = _loads(payload.pop("needs_review_json", None), [])
    payload["exam_use_modes"] = _loads(payload.pop("exam_use_modes_json", None), {})
    payload["exam_paper_metadata"] = _loads(payload.pop("exam_paper_metadata_json", None), {})
    return payload


def _decode_unit_inventory(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["inventory"] = _loads(payload.pop("inventory_json", None), {})
    payload["usage"] = _loads(payload.pop("usage_json", None), {})
    return payload


def _decode_exam_profile(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["profile"] = _loads(payload.pop("profile_json", None), {})
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
