from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import closing, nullcontext
from dataclasses import dataclass, field, fields as dataclass_fields, replace
from datetime import UTC, timedelta
from typing import Any, Iterable, Mapping

from learnloop.attempt_types import NON_RECORDING_ATTEMPT_TYPES, SUPPORTED_ATTEMPT_TYPES, unsupported_attempt_types
from learnloop.ai.client import AIProviderClient
from learnloop.ai.runtime import AIRuntimeReport, legacy_codex_status
from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.ai.errors import CodexUnavailable
from learnloop.ai.spend import SpendLimitExceeded
from learnloop.attempts.ai_contracts import GRADING_PROMPT_VERSION, GradingProposal
from learnloop.ai.providers.codex import CodexRuntimeReport
from learnloop.db.repositories import (
    ActiveErrorEvent,
    FacetRecallState,
    FacetUncertaintyState,
    ItemParameterState,
    MasteryState,
    PracticeItemQualityState,
    PracticeItemState,
    Repository,
)
from learnloop.ids import new_ulid
from learnloop.ai.runs import finish_agent_run
from learnloop.params.fitted_params import resolve_fsrs_weights
from learnloop.scheduling.fsrs import (
    FSRS6_DEFAULT_WEIGHTS,
    MemoryState,
    Rating,
    apply_review,
    interval_for_retention,
    rating_from_score,
)
from learnloop.attempts.ability_transition import estimate_ability_transition
from learnloop.diagnosis.causal_activity_policy import classify_attempt_activity
from learnloop.attempts.grading import (
    GradingValidationError,
    ValidatedCodexGrade,
    ValidatedCriterionEvidence,
    ValidatedErrorAttribution,
    build_grading_context,
    confidence_to_grader_confidence,
    enforce_passed_target_firewall,
    evidence_coverage,
    grading_context_hash,
    resolved_rubric,
    validate_codex_grading_proposal,
)
from learnloop.diagnosis.error_taxonomy import persist_unknown_error_type_proposals
from learnloop.diagnosis.error_taxonomy_map import (
    ASSESSMENT_SIDE_ERROR_TYPES,
    map_legacy_error_type,
)
from learnloop.learner.facet_diagnostics import (
    apply_mastery_variance_floor,
    build_facet_uncertainty_updates,
    covered_required_fraction,
    lo_relative_coverage,
)
from learnloop.learner.mastery import (
    MasteryObservation,
    MasteryObservationTrace,
    display_mastery,
    initial_mastery_state_for_learning_object,
    item_irt_params,
    resolve_item_irt_params,
    update_item_difficulty,
    update_mastery_traced,
)
from learnloop.algorithm_versions import P0_PROJECTION_VERSIONS, SOURCE_REFERENCE_GATE_VERSIONS
from learnloop.db.connection import connect
from learnloop.db.stores.source_service import reference_status_for_item
from learnloop.attempts.blind_grading import (
    BLIND_CALIBRATION_PROMPT_VERSION,
    BLIND_GRADER_OUTPUT_SCHEMA_VERSION,
    split_grading_active,
)
from learnloop.attempts.evidence import attempt_evidence_mass
from learnloop.attempts.reveal_ledger import POST_ATTEMPT_REVEAL_KINDS
from learnloop.attempts.stuck import (
    EMPTY_STUCK_EVIDENCE,
    EMPTY_STUCK_FEEDBACK,
    EMPTY_STUCK_GRADER_TIER,
    EMPTY_STUCK_LOCAL_GRADER_ID,
    STUCK_READING_KEY,
    is_empty_stuck,
    record_stuck_reading_judgment,
    stuck_answer_prompt,
    stuck_prompt_active,
    verified_stuck_reading,
)
from learnloop.learner.assessment_contracts import (
    CANONICAL_STATE_VERSIONS,
    KM_ALGORITHM_VERSION,
    compile_assessment_contract,
    contract_required_method,
    rubric_from_contract,
)
from learnloop.learner.facet_state_reader import (
    CanonicalFacetStateReader,
    is_canonical_state_vault,
)
from learnloop.content.proposals.proposals import maybe_promote_self_tagged_fatal_error
from learnloop.learner.recall_coverage import (
    build_facet_recall_updates,
    build_facet_recall_updates_from_prior,
    build_quality_state_update,
    build_quality_state_update_from_prior,
    derive_facet_outcomes,
    event_local_severity,
    event_local_severity_from_attempts,
    familiarity_discount,
    familiarity_discount_from_attempts,
    predicted_correctness,
    predicted_correctness_from_prior,
    resolve_coverage,
    resolve_error_impact,
    resolve_reliability,
    scale_coverage_for_graded_criteria,
    target_criterion_facet_weights,
)
from learnloop.attempts.surprise import compute_surprise
from learnloop.vault.hashes import practice_item_hash
from learnloop.vault.models import LoadedVault, PracticeItem, Rubric


# Per spec §"Attempt-type handling": a `dont_know` attempt is deterministically
# attributed to a recall failure (score 0, no grading role invoked).
DONT_KNOW_ERROR_TYPE = "recall_failure"
SCAFFOLD_FAILURE_ERROR_TYPE = "scaffold_failure"

# Summed `reveal_events` amount (migration 154) on one item since its last
# attempt, above which the next attempt is recorded as primed whatever the
# client declared.
#
# A module constant, not config: this is a property of what the reveal scale
# MEANS, not a tuning dial. `amount` is calibrated so 1.0 is "the expected
# answer was restated" and a repair suggestion's `answer_reveal_budget` is the
# fraction of the solution that lane is licensed to show. 0.35 is the point
# where the accumulated exposure is more than a nudge — roughly a third of the
# solution — and an "unassisted" claim about the next attempt stops being
# honest. A vault that could raise it to 0.9 would be configuring away the
# integrity property the ledger exists to enforce, and one that could drop it to
# 0.05 would prime on incidental vocabulary overlap. Same reasoning as the
# causal-factor deferral bounds.
AUTO_PRIME_REVEAL_THRESHOLD = 0.35


@dataclass(frozen=True)
class AttemptDraft:
    practice_item_id: str
    learner_answer_md: str
    attempt_type: str = "independent_attempt"
    hints_used: int = 0
    latency_seconds: int | None = None
    session_id: str | None = None
    # Retry launched from the feedback screen's source-review panel: the
    # canonical source was just re-read, so the mastery update applies an IRT
    # easiness shift and the attempt does not advance last_evidence_at.
    primed: bool = False
    # Probe redesign §5.1: the committed presentation this submission consumes.
    # Required for qualifying diagnostic observations; an invalid or already
    # consumed reference downgrades the attempt to incidental evidence.
    probe_presentation_id: str | None = None
    # Probe redesign §7.1: the learner's committed answer confidence (1-5).
    # Logged-only observation feature — never consumed by grading or scheduling.
    answer_confidence: int | None = None
    # Immutable item/rubric contract captured when the item was presented. UI
    # callers round-trip this opaque id; non-interactive callers snapshot at the
    # attempt boundary as a compatibility fallback.
    assessment_contract_version_id: str | None = None
    # Client-generated retry identity. Persisted on the attempt under a unique
    # index so one submission cannot create two formal attempts.
    submission_id: str | None = None
    scheduler_candidate_id: str | None = None
    entry_surface: str = "unspecified"
    evidence_origin: str = "unknown"
    # False for doors that never run the post-attempt pipeline (exam seeding,
    # simulation, calibration, observation imports, rung-variant requests).
    # Their completion is recorded as done when the attempt is applied, so a
    # pending completion always means an interrupted one.
    awaits_completion: bool = True
    # A diagnostic presentation keeps its measurement attempt type while this
    # flag records the learner's explicit "I don't know" outcome.
    declared_dont_know: bool = False
    # mvp-0.13: the answer was written after "I'm stuck" ("Write what you can,
    # or what's confusing you"). It is an ORDINARY attempt of `attempt_type`
    # at the standard mass: graded when it has text (the blind grader also
    # reads it for confusion), a deterministic zero when empty. Persisted as
    # `practice_attempts.declared_stuck`; never combined with dont_know.
    declared_stuck: bool = False
    # Meas §3.A6: the one line the learner volunteered at a decision point, as
    # its OWN field rather than as text a client appended under an agreed
    # heading. `learner_answer_md` above still carries the composed trace — the
    # grader has to read one narrative, not two fields — but it is composed by
    # `trace_evidence.compose_learner_trace` on the way in, so no surface and no
    # consumer has to know the delimiter to write or detect a volunteered line.
    # None when nothing was volunteered; there is deliberately no value meaning
    # "offered and declined" (rule 3).
    elicited_explanation_md: str | None = None
    # Set by `auto_primed_draft` when `primed` was forced from the reveal ledger
    # rather than declared by the client: the summed exposure that triggered it.
    # None on every draft the learner (or a caller) primed honestly, so "was this
    # primed because we caught a reveal?" is answerable from the attempt's debug
    # payload alone.
    auto_primed_reveal_total: float | None = None
    # Canonical sources S1 (mvp-0.18, C3): the served item's answer-key status
    # when the attempt was made (``practice_attempts.reference_status``). None
    # derives it at attempt time from the item's effective key status; replay
    # passes the stored value and never re-derives it.
    reference_status: str | None = None


@dataclass(frozen=True)
class SelfGradeErrorAttribution:
    """One learner-attributed error from the self-grade form (spec §"self-grade").

    Mirrors a Codex ``error_attribution``: ``error_type`` is resolved against the
    vault taxonomy for severity / misconception status. ``criterion_id`` records
    which under-credited rubric criterion the learner tied the error to — surfaced
    in the attribution evidence, not persisted as a separate column (the persisted
    shape stays identical to Codex grading).
    """

    error_type: str
    criterion_id: str | None = None


@dataclass(frozen=True)
class SelfGradeInput:
    criterion_points: dict[str, float]
    confidence: int
    fatal_errors: list[str] | None = None
    error_type: str | None = None
    notes: str | None = None
    error_attributions: list[SelfGradeErrorAttribution] | None = None


@dataclass(frozen=True)
class GradeAttribution:
    error_type: str
    severity: float
    evidence: str | None = None
    is_misconception: bool = False
    # spec §2.1: structured belief captured by the grader; persisted on the
    # error event so the registry (Phase 2) and replay can read it losslessly.
    misconception_statement: str | None = None
    misconception_consistent_answer: str | None = None
    # spec §2.2: registry link written by normalization after persistence; carried
    # through replay (from the persisted error event) so the link survives rebuilds.
    misconception_id: str | None = None
    target_evidence_families: list[str] = field(default_factory=list)
    target_criterion_ids: list[str] = field(default_factory=list)
    resolution_status: str | None = None
    abstention_reason: str | None = None
    cause_scope: str | None = None
    target_ref: dict[str, Any] | None = None
    operation: str | None = None
    first_divergence: dict[str, Any] | None = None
    model_reported_localization_confidence: float | None = None
    model_reported_causal_confidence: float | None = None
    # Aug C3 harness-owned agreement, attached after proposal validation.
    diagnostic_sample_support: float | None = None
    facet_contrast: dict[str, Any] | None = None
    candidate_causes: list[dict[str, Any]] = field(default_factory=list)
    postdictive_claims: list[dict[str, Any]] = field(default_factory=list)
    soft_postdictive_claims: list[str] = field(default_factory=list)
    # Meas §3.A3 / §10: a typed reason the facet targets were cleared, carried to
    # the observation ledger so an emptied list cannot be read as an unfilled one.
    facet_write_blocked: str | None = None


@dataclass(frozen=True)
class ResolvedGrade:
    rubric_score: int
    criterion_points: dict[str, float]
    evidence_rows: list[dict[str, object]]
    error_attributions: list[GradeAttribution]
    grader_confidence: float
    confidence: int | None
    manual_review_reason: str | None
    feedback_md: str | None = None
    repair_suggestions: list[dict[str, Any]] = field(default_factory=list)
    fatal_errors: list[str] = field(default_factory=list)
    diagnosis_md: str | None = None
    attribution_audit_events: list[dict[str, Any]] = field(default_factory=list)
    # Meas §3.A6: facets the grader saw exercised in the trace. Carried on the
    # resolved grade rather than written from the validator so the whole attempt
    # commits or none of it does, like every other grading side effect.
    exercised_facets: list[dict[str, Any]] = field(default_factory=list)
    # Meas §3.A8: an accepted clarification request, if the grader made one.
    clarification: dict[str, Any] | None = None
    # Meas §3.A5: the typed profile judgement, including the `no_profile_applies`
    # and `no_profiles_offered` arms. Carried rather than re-derived so the
    # recorded outcome is the one the grade was validated with.
    discrimination_profile_match: dict[str, Any] | None = None
    # Meas §3.A3: the resolved error-hunt outcome, `None` off that instrument.
    error_hunt: dict[str, Any] | None = None


@dataclass(frozen=True)
class AttemptResult:
    attempt_id: str
    practice_item_id: str
    learning_object_id: str
    rubric_score: int
    correctness: float
    grader_confidence: float
    manual_review_reason: str | None
    fsrs_rating: str
    due_at: str
    mastery_mean: float
    mastery_variance: float
    surprise_direction: str
    predictive_surprise: float
    bayesian_surprise: float
    error_event_ids: list[str]
    grading_source: str = "self"
    fallback_reason: str | None = None
    agent_run_id: str | None = None
    feedback_md: str | None = None
    repair_suggestions: list[dict[str, Any]] = field(default_factory=list)
    fatal_errors: list[str] = field(default_factory=list)
    # IRT picture of the mastery update (spec §7.1); debug-only, excluded from as_dict.
    mastery_trace: MasteryObservationTrace | None = None
    debug_payload: dict[str, object] | None = None
    # Meas §3.A6: carried to the write site in `apply_attempt`. Empty on every
    # non-model grading path (self, deterministic, replay) — a channel whose
    # whole premise is "the grader read the trace" has nothing to report when
    # no grader ran.
    exercised_facets: list[dict[str, Any]] = field(default_factory=list)
    # Meas §3.A8: the accepted clarification request, carried to the same site.
    clarification: dict[str, Any] | None = None
    # Meas §3.A5 / §3.A3: carried to the same write site as A6 and A8, for the
    # same reason — the whole attempt commits or none of it does.
    discrimination_profile_match: dict[str, Any] | None = None
    error_hunt: dict[str, Any] | None = None
    # §5.7 block-end hook payload when this attempt closed a diagnostic block:
    # released feedback, open-set/completion outcome, and the route.
    probe_block_end: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "attempt_id": self.attempt_id,
            "practice_item_id": self.practice_item_id,
            "learning_object_id": self.learning_object_id,
            "rubric_score": self.rubric_score,
            "correctness": self.correctness,
            "grader_confidence": self.grader_confidence,
            "manual_review_reason": self.manual_review_reason,
            "fsrs_rating": self.fsrs_rating,
            "due_at": self.due_at,
            "mastery_mean": self.mastery_mean,
            "mastery_variance": self.mastery_variance,
            "surprise_direction": self.surprise_direction,
            "predictive_surprise": self.predictive_surprise,
            "bayesian_surprise": self.bayesian_surprise,
            "error_event_ids": self.error_event_ids,
            "grading_source": self.grading_source,
            "fallback_reason": self.fallback_reason,
            "agent_run_id": self.agent_run_id,
            "feedback_md": self.feedback_md,
            "repair_suggestions": self.repair_suggestions,
            "fatal_errors": self.fatal_errors,
            "probe_block_end": self.probe_block_end,
            "debug": self.debug_payload or {},
        }

    @classmethod
    def from_dict(cls, saved: Mapping[str, Any]) -> AttemptResult:
        """Rebuild a result saved with :meth:`as_dict`.

        Keys this version does not know are ignored and fields the saved copy
        lacks take their defaults, so a result saved by another app version
        still loads.
        """

        values = dict(saved)
        values["debug_payload"] = values.pop("debug", None) or {}
        known = {item.name for item in dataclass_fields(cls)}
        return cls(**{key: value for key, value in values.items() if key in known})


@dataclass(frozen=True)
class ApplyAttemptInput:
    """Resolved attempt payload consumed by the shared attempt step.

    Grading is deliberately outside this shape. Live self-grade, AI/Codex
    grading, replay, and regrade all hand an already-resolved grade to the same
    step so derived learner state is computed in one place.
    """

    draft: AttemptDraft
    attempt_id: str
    grade: ResolvedGrade
    replace_existing: bool = False
    record_probe_update: bool = True
    error_event_ids_override: list[str] | None = None
    # Probe redesign §5.8: the grading provider that produced this grade.
    # Qualifying diagnostic observations require an approved provider; a
    # self-graded submission can never advance an episode.
    grading_source: str = "self"
    # The model run that produced this grade. None for self-graded,
    # deterministic and replayed grades.
    grading_agent_run_id: str | None = None
    # Set only when a model grade failed and the learner's self-grade was
    # applied instead: why it failed and which run failed. The result carries
    # both so the completion saved inside the attempt transaction is the result
    # the learner is shown, not a provisional one.
    fallback_reason: str | None = None
    fallback_agent_run_id: str | None = None
    # Slice 1 M2: ``"blind"`` when the learner-blind grader produced this grade
    # (its validated record is in ``blind_grade_records``); None is the joint
    # grader or no model. Replay reads it from that ledger, never from config.
    grader_mode: str | None = None
    # The calibration identity (prompt version, output schema version) the
    # grade channel stamps; None keeps the joint grader's (§4.3).
    grader_identity: tuple[str, str] | None = None
    # PF-c: criteria the valid-alternative gate recorded as unverified. Their
    # evidence rows are stamped with the unverified block, with or without an
    # attribution. Owner decision 2026-10-12: they are UNASSESSED - the grade
    # already excludes them (``assessed_rubric_score``) and the shared step
    # gives them no facet mass and no outcome. Replay reads them back from the
    # stamped rows, so live, regrade and replay apply one rule.
    unverified_criterion_ids: tuple[str, ...] = ()
    # mvp-0.17 (re-review F9): the route check left nothing assessed and
    # nothing validated the answer, so the grade is the grader's own,
    # provisional and held for review. While no criterion is assessed the
    # attempt applies no FSRS review (the item's memory and due date stay as
    # they were) and is no prediction error; a regrade or an adjudication that
    # assesses a criterion releases it. Replay reads it from the blind record.
    grade_held_for_review: bool = False


@dataclass(frozen=True)
class AttemptPriorState:
    """Prior learner/item state read once before computing one attempt."""

    mastery: MasteryState
    active_errors: list[ActiveErrorEvent]
    practice_item_state: PracticeItemState | None
    practice_item_quality_state: PracticeItemQualityState | None
    recent_learning_object_attempts: list[dict[str, Any]]
    recent_practice_item_attempts: list[dict[str, Any]]
    aggregate_facet_recall: dict[str, FacetRecallState | None]
    item_facet_recall: dict[str, FacetRecallState | None]
    facet_uncertainty: dict[str, FacetUncertaintyState | None]
    item_parameter_state: ItemParameterState | None = None

    def facet_recall_state(self, facet_id: str, practice_item_id: str | None = None) -> FacetRecallState | None:
        if practice_item_id is None:
            return self.aggregate_facet_recall.get(facet_id)
        return self.item_facet_recall.get(facet_id)

    def facet_recall_by_scope(self, facets: Iterable[str], practice_item_id: str) -> dict[tuple[str, str | None], FacetRecallState | None]:
        return {
            (facet, item_scope): self.facet_recall_state(facet, item_scope)
            for facet in facets
            for item_scope in (None, practice_item_id)
        }


@dataclass(frozen=True)
class AttemptApplication:
    """Computed attempt outputs before they are persisted.

    This is the state-output boundary for the attempt pipeline. The computation
    still loads its prior snapshot through Repository today, but every row the
    attempt will write is materialized here before the persistence step runs.
    """

    attempt_record: dict[str, Any]
    evidence_rows: list[dict[str, object]]
    error_events: list[dict[str, Any]]
    surprise_record: dict[str, object]
    practice_item_state: PracticeItemState
    mastery_state: MasteryState
    facet_recall_states: list[dict[str, Any]]
    facet_uncertainty_states: list[dict[str, Any]]
    #: None when the grade is held (held-grade-evidence F10): no row is written.
    quality_state: dict[str, Any] | None
    ability_transition: dict[str, Any]
    attempt_debug_payload: dict[str, object]
    result: AttemptResult
    item_parameter_state: ItemParameterState | None = None
    #: held-grade-evidence: THE held predicate (``outcome_contract.
    #: grade_is_held``) evaluated in flight for the grade being applied. The
    #: attempt step's own readers (the certification cold probe, the probe
    #: episode, error-event auto-resolution) read it here, because the live
    #: door writes the blind record after this step; every later reader reads
    #: the ledger (``canonical_projection.held_for_review_attempts``).
    grade_held: bool = False


class AttemptServiceNotReady(RuntimeError):
    pass


class AttemptValidationError(ValueError):
    pass


#: Delayed follow-up lanes whose defining claim is an UNASSISTED attempt: the
#: repair-scoped cold retry (causal §6.2, migration 058) and the certification
#: cold probe (measurement §5.7, migration 139). Named here rather than importing
#: from either service, because this is the shared attempt validator and it must
#: not depend on which lane happens to be loaded.
COLD_FOLLOWUP_TASK_KINDS: frozenset[str] = frozenset(
    {"cold_retry", "certification_cold_probe"}
)


def complete_attempt_with_codex_fallback(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    fallback_grade: SelfGradeInput,
    *,
    runtime: CodexRuntimeReport,
    codex_client: AIProviderClient | None = None,
    clock: Clock | None = None,
) -> AttemptResult:
    return _complete_attempt_with_agent_fallback(
        vault,
        repository,
        draft,
        fallback_grade,
        runtime=runtime,
        ai_client=codex_client,
        grading_source="codex",
        missing_client_reason="codex_client_missing",
        failure_prefix="codex_failed",
        clock=clock,
    )


def complete_attempt_with_ai_fallback(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    fallback_grade: SelfGradeInput,
    *,
    runtime: AIRuntimeReport,
    ai_client: AIProviderClient | None = None,
    clock: Clock | None = None,
) -> AttemptResult:
    return _complete_attempt_with_agent_fallback(
        vault,
        repository,
        draft,
        fallback_grade,
        runtime=runtime,
        ai_client=ai_client,
        grading_source="ai",
        missing_client_reason="ai_client_missing",
        failure_prefix="ai_failed",
        clock=clock,
    )


def _complete_attempt_with_agent_fallback(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    fallback_grade: SelfGradeInput,
    *,
    runtime,
    ai_client: AIProviderClient | None = None,
    grading_source: str,
    missing_client_reason: str,
    failure_prefix: str,
    clock: Clock | None = None,
) -> AttemptResult:
    # `draft` is rebound: the resolver may have forced `primed` from the reveal
    # ledger, and everything downstream (grading context, the recorded row,
    # the IRT easiness shift) must use that draft, not the client's.
    item, _learning_object, rubric, draft = _resolve_attempt_target(vault, repository, draft)
    if is_empty_stuck(draft):
        # Nothing to grade, so no model and no self-grade: before any check.
        return complete_empty_stuck_attempt(vault, repository, draft, clock=clock)
    contract = _assessment_contract(repository, draft)
    deterministic = _try_deterministic_grade(vault, repository, draft, item, rubric, clock=clock)
    if deterministic is not None:
        return deterministic
    if not runtime.ready or ai_client is None:
        reason = runtime.status if not runtime.ready else missing_client_reason
        if grading_source == "codex":
            reason = legacy_codex_status(reason)
        return complete_self_graded_attempt(
            vault, repository, draft, fallback_grade, fallback_reason=reason, clock=clock,
        )

    attempt_id = new_ulid()
    context = build_grading_context(
        vault,
        item,
        attempt_id=attempt_id,
        learner_answer_md=draft.learner_answer_md,
        rubric=rubric,
        assessment_contract=contract,
    )
    blind = (
        _blind_grading_plan(
            vault, item, context, stuck=draft.declared_stuck,
            required_method=_graded_required_method(item, contract),
        )
        if split_grading_active(vault)
        else None
    )
    if blind is None:
        if draft.declared_stuck:
            # mvp-0.13 (review F3): the joint grader (split switched off)
            # reads a stuck answer under the same stuck rules.
            context = replace(context, answer_prompt=stuck_answer_prompt())
        context = _augmented_grading_context(vault, repository, item, context)
    now = utc_now_iso(clock)
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": "grading",
            **agent_run_provider_fields(ai_client, runtime),
            "prompt_template": "grading",
            **_grading_run_identity(context, blind),
            "started_at": now,
            "status": "running",
        }
    )
    try:
        if blind is not None:
            result = _complete_blind_graded_attempt(
                vault,
                repository,
                draft,
                blind,
                rubric=rubric,
                ai_client=ai_client,
                attempt_id=attempt_id,
                agent_run_id=agent_run_id,
                grading_source=grading_source,
                clock=clock,
            )
        else:
            result = _complete_joint_graded_attempt(
                vault,
                repository,
                draft,
                context,
                ai_client=ai_client,
                attempt_id=attempt_id,
                agent_run_id=agent_run_id,
                grading_source=grading_source,
                clock=clock,
            )
    except sqlite3.IntegrityError as exc:
        _finish_superseded_grading_run(repository, agent_run_id, ai_client, exc, clock=clock)
        raise
    except SpendLimitExceeded as exc:
        # A command's caps refused a retry or a later sample (re-review F7).
        # That is the command's over-budget answer, never a grading failure to
        # cover with the self-grade: close the run (its tokens are recorded)
        # and let the command report it. It subclasses ValueError, so it is
        # caught before the fallback below.
        _finish_run_after_grading_error(repository, agent_run_id, ai_client, attempt_id, exc, clock=clock)
        raise
    except (CodexUnavailable, TimeoutError, GradingValidationError, AttemptValidationError, ValueError) as exc:
        if _finish_run_after_grading_error(repository, agent_run_id, ai_client, attempt_id, exc, clock=clock):
            # A receipt/annotation failure after the model grade committed
            # cannot turn that grade into a second, self-graded attempt. The
            # caller resumes the committed attempt's saved completion.
            raise
        return complete_self_graded_attempt(
            vault, repository, draft, fallback_grade,
            fallback_reason=f"{failure_prefix}:{type(exc).__name__}",
            fallback_agent_run_id=agent_run_id,
            clock=clock,
        )
    finish_agent_run(repository, agent_run_id, ai_client, clock=clock)
    return result


def _finish_superseded_grading_run(
    repository: Repository,
    agent_run_id: str,
    ai_client: AIProviderClient,
    error: sqlite3.IntegrityError,
    *,
    clock: Clock | None = None,
) -> None:
    """Close a grading run whose attempt the database refused.

    The usual cause is a concurrent request that committed the same
    submission id first; its attempt is the answer, so this grade is
    discarded rather than replaced by a self-grade. The run's tokens are still
    recorded.
    """

    finish_agent_run(
        repository, agent_run_id, ai_client,
        status="failed", error_message=f"attempt not recorded: {error}", clock=clock,
    )


def _finish_run_after_grading_error(
    repository: Repository,
    agent_run_id: str,
    ai_client: AIProviderClient,
    attempt_id: str,
    error: Exception,
    *,
    clock: Clock | None = None,
) -> bool:
    """Close the grading run after an error; return whether its grade committed.

    A committed attempt means the model grade is authoritative and only a later
    annotation step failed, so the run completed. Otherwise the run failed, and
    its tokens are still recorded: C3's cost ratio needs the calls a fallback
    could not use in the numerator, or the augmented loop looks cheaper than it
    is (A7).
    """

    committed = repository.fetch_practice_attempt(attempt_id) is not None
    if committed:
        finish_agent_run(repository, agent_run_id, ai_client, clock=clock)
    else:
        finish_agent_run(
            repository, agent_run_id, ai_client,
            status="failed", error_message=str(error), clock=clock,
        )
    return committed


def complete_attempt_with_codex_required(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    *,
    runtime: CodexRuntimeReport,
    codex_client: AIProviderClient | None = None,
    clock: Clock | None = None,
) -> AttemptResult:
    return _complete_attempt_with_agent_required(
        vault,
        repository,
        draft,
        runtime=runtime,
        ai_client=codex_client,
        grading_source="codex",
        missing_client_reason="codex_client_missing",
        clock=clock,
    )


def complete_attempt_with_ai_required(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    *,
    runtime: AIRuntimeReport,
    ai_client: AIProviderClient | None = None,
    clock: Clock | None = None,
) -> AttemptResult:
    return _complete_attempt_with_agent_required(
        vault,
        repository,
        draft,
        runtime=runtime,
        ai_client=ai_client,
        grading_source="ai",
        missing_client_reason="ai_client_missing",
        clock=clock,
    )


def _try_deterministic_grade(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    item,
    rubric,
    *,
    clock: Clock | None = None,
) -> AttemptResult | None:
    """Grade an unambiguous option-letter selection without the model grader.

    Applies through the same proposal path as agent grades so every downstream
    projection sees a normal graded attempt — but with grading_source
    'deterministic' and grader_confidence 1.0, which the reliability resolver
    exempts from the calibration-channel discount. Runs before the runtime
    check: a constrained selection is gradable even when no agent is up. A
    declared-stuck answer (mvp-0.13) never takes it: it goes to the grader.
    """

    from learnloop.attempts.grading import deterministic_recognition_grade

    if draft.declared_stuck:
        # mvp-0.13 (review F1): text written under "I'm stuck" is the
        # learner's own words, not an option pick. "Confused about ..." must
        # never parse as option C; the grader reads it (and its confusion).
        return None
    attempt_id = new_ulid()
    proposal = deterministic_recognition_grade(
        item, rubric, draft.learner_answer_md, attempt_id=attempt_id
    )
    if proposal is None:
        return None
    result = complete_codex_graded_attempt(
        vault,
        repository,
        draft,
        proposal,
        attempt_id=attempt_id,
        agent_run_id=None,
        grading_source="deterministic",
        clock=clock,
    )
    return result


@dataclass(frozen=True)
class GradingCallPlan:
    """The model grading one answer would send, computed with no call and no write.

    Review F5: the paid command door (``learnloop attempt``) estimates and
    admits these calls before sending them. ``kind`` is ``empty_stuck`` or
    ``deterministic`` (no call), ``blind`` or ``joint`` (``calls`` samples,
    each about ``estimated_input_tokens_per_call`` input tokens).
    """

    kind: str
    calls: int
    prompt_version: str | None = None
    estimated_input_tokens_per_call: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "calls": self.calls,
            "prompt_version": self.prompt_version,
            "estimated_input_tokens_per_call": self.estimated_input_tokens_per_call,
        }


def plan_grading_calls(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    *,
    clock: Clock | None = None,
) -> GradingCallPlan:
    """What the practice door would send to a grader for ``draft`` (read-only).

    The same decisions as the completion doors, in the same order: an empty
    stuck answer and an unambiguous option letter make no call; otherwise the
    blind (split) or joint prompt is assembled exactly as it would be sent and
    its input tokens estimated, once per sample. Raises like the doors on an
    invalid draft.
    """

    from learnloop.attempts.grading import deterministic_recognition_grade
    from learnloop.attempts.grading_admission import estimated_prompt_tokens

    item, _learning_object, rubric, draft = _resolve_attempt_target(
        vault, repository, draft, clock=clock
    )
    if is_empty_stuck(draft):
        return GradingCallPlan(kind="empty_stuck", calls=0)
    if not draft.declared_stuck and deterministic_recognition_grade(
        item, rubric, draft.learner_answer_md, attempt_id="planned"
    ) is not None:
        return GradingCallPlan(kind="deterministic", calls=0)
    contract = _assessment_contract(repository, draft)
    context = build_grading_context(
        vault,
        item,
        attempt_id="planned",
        learner_answer_md=draft.learner_answer_md,
        rubric=rubric,
        assessment_contract=contract,
    )
    if split_grading_active(vault):
        from learnloop.attempts.blind_grading import blind_grading_prompt

        blind = _blind_grading_plan(
            vault, item, context, stuck=draft.declared_stuck,
            required_method=_graded_required_method(item, contract),
        )
        return GradingCallPlan(
            kind="blind",
            calls=_blind_sample_count(vault),
            prompt_version=blind.prompt_version,
            estimated_input_tokens_per_call=estimated_prompt_tokens(
                blind_grading_prompt(blind.context)
            ),
        )
    from learnloop.attempts.ai_contracts import grading_prompt_version
    from learnloop.attempts.grading import joint_grading_prompt_tokens

    if draft.declared_stuck:
        context = replace(context, answer_prompt=stuck_answer_prompt())
    context = _augmented_grading_context(vault, repository, item, context)
    return GradingCallPlan(
        kind="joint",
        calls=_joint_sample_count(vault),
        prompt_version=grading_prompt_version(context),
        estimated_input_tokens_per_call=joint_grading_prompt_tokens(context),
    )


def _complete_attempt_with_agent_required(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    *,
    runtime,
    ai_client: AIProviderClient | None = None,
    grading_source: str,
    missing_client_reason: str,
    clock: Clock | None = None,
) -> AttemptResult:
    # `draft` is rebound: the resolver may have forced `primed` from the reveal
    # ledger, and everything downstream (grading context, the recorded row,
    # the IRT easiness shift) must use that draft, not the client's.
    item, _learning_object, rubric, draft = _resolve_attempt_target(vault, repository, draft)
    if is_empty_stuck(draft):
        # Nothing to grade: an empty stuck answer never needs a provider.
        return complete_empty_stuck_attempt(vault, repository, draft, clock=clock)
    deterministic = _try_deterministic_grade(vault, repository, draft, item, rubric, clock=clock)
    if deterministic is not None:
        return deterministic

    if not runtime.ready or ai_client is None:
        reason = runtime.status if not runtime.ready else missing_client_reason
        if grading_source == "codex":
            reason = legacy_codex_status(reason)
        raise CodexUnavailable(reason)

    contract = _assessment_contract(repository, draft)
    attempt_id = new_ulid()
    context = build_grading_context(
        vault,
        item,
        attempt_id=attempt_id,
        learner_answer_md=draft.learner_answer_md,
        rubric=rubric,
        assessment_contract=contract,
    )
    blind = (
        _blind_grading_plan(
            vault, item, context, stuck=draft.declared_stuck,
            required_method=_graded_required_method(item, contract),
        )
        if split_grading_active(vault)
        else None
    )
    if blind is None:
        if draft.declared_stuck:
            # mvp-0.13 (review F3): the joint grader (split switched off)
            # reads a stuck answer under the same stuck rules.
            context = replace(context, answer_prompt=stuck_answer_prompt())
        context = _augmented_grading_context(vault, repository, item, context)
    now = utc_now_iso(clock)
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": "grading",
            **agent_run_provider_fields(ai_client, runtime),
            "prompt_template": "grading",
            **_grading_run_identity(context, blind),
            "started_at": now,
            "status": "running",
        }
    )
    try:
        if blind is not None:
            result = _complete_blind_graded_attempt(
                vault,
                repository,
                draft,
                blind,
                rubric=rubric,
                ai_client=ai_client,
                attempt_id=attempt_id,
                agent_run_id=agent_run_id,
                grading_source=grading_source,
                clock=clock,
            )
        else:
            result = _complete_joint_graded_attempt(
                vault,
                repository,
                draft,
                context,
                ai_client=ai_client,
                attempt_id=attempt_id,
                agent_run_id=agent_run_id,
                grading_source=grading_source,
                clock=clock,
            )
    except sqlite3.IntegrityError as exc:
        _finish_superseded_grading_run(repository, agent_run_id, ai_client, exc, clock=clock)
        raise
    except (CodexUnavailable, TimeoutError, GradingValidationError, AttemptValidationError, ValueError) as exc:
        _finish_run_after_grading_error(repository, agent_run_id, ai_client, attempt_id, exc, clock=clock)
        raise
    finish_agent_run(repository, agent_run_id, ai_client, clock=clock)
    return result


def complete_self_graded_attempt(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    grade: SelfGradeInput,
    *,
    fallback_reason: str | None = None,
    fallback_agent_run_id: str | None = None,
    clock: Clock | None = None,
) -> AttemptResult:
    """Record the learner's self-grade.

    ``fallback_reason``/``fallback_agent_run_id`` mark a self-grade applied
    because model grading failed or was unavailable.
    """

    if is_empty_stuck(draft):
        # An empty stuck answer has nothing to self-grade either: whatever
        # door it arrives through, it is the same deterministic zero.
        return complete_empty_stuck_attempt(vault, repository, draft, clock=clock)
    now_iso = utc_now_iso(clock)
    attempt_id = new_ulid()
    # `draft` is rebound: the resolver may have forced `primed` from the reveal
    # ledger, and everything downstream (grading context, the recorded row,
    # the IRT easiness shift) must use that draft, not the client's.
    item, _learning_object, rubric, draft = _resolve_attempt_target(vault, repository, draft)
    grader_confidence = confidence_to_grader_confidence(grade.confidence)
    manual_review_reason = "low_self_confidence" if grader_confidence < 0.4 else None
    manual_review_reason = _attempt_manual_review_reason(manual_review_reason, draft)
    criterion_points = _validated_criterion_points(rubric, grade.criterion_points)
    fatal_errors = grade.fatal_errors or []
    _validate_fatal_errors(rubric, fatal_errors)
    attribution_error_type = grade.error_type
    per_criterion_attributions = _validated_self_grade_attributions(rubric, grade.error_attributions)
    if draft.attempt_type == "dont_know" or draft.declared_dont_know:
        criterion_points = {criterion.id: 0.0 for criterion in rubric.criteria}
        fatal_errors = []
        per_criterion_attributions = []
        # A don't-know is deterministically attributed to recall_failure so it
        # writes an error event and feeds surprise / cross-LO propagation through
        # the standard pipeline (spec §"Attempt-type handling").
        attribution_error_type = _dont_know_error_type(vault, draft.hints_used)
    error_attributions = _self_grade_attributions(
        vault, fatal_errors, attribution_error_type, per_criterion_attributions
    )
    rubric_score = calculate_rubric_score(rubric, criterion_points, fatal_errors)
    evidence_rows = [
        {
            "id": new_ulid(),
            "criterion_id": criterion.id,
            "points_awarded": criterion_points[criterion.id],
            "evidence": f"Self-grade awarded {criterion_points[criterion.id]:g}/{criterion.points:g}.",
            "notes": grade.notes,
            "local_grader_id": "self",
            "grader_tier": 1,
            "learner_confidence": "hedged" if grade.confidence <= 2 else "confident",
            "created_at": now_iso,
        }
        for criterion in rubric.criteria
    ]
    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=draft,
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=rubric_score,
                criterion_points=criterion_points,
                evidence_rows=evidence_rows,
                error_attributions=error_attributions,
                grader_confidence=grader_confidence,
                confidence=grade.confidence,
                manual_review_reason=manual_review_reason,
                feedback_md=grade.notes,
                fatal_errors=fatal_errors,
            ),
            fallback_reason=fallback_reason,
            fallback_agent_run_id=fallback_agent_run_id,
        ),
        clock=clock,
    )
    # Durable-probe promotion (spec §12.4): a misconception the learner self-attached
    # often enough becomes a candidate rubric fatal error, queued for review only.
    # Runs across every distinct attributed error (legacy single tag, fatal errors,
    # and the per-criterion picks); the promotion gate itself ignores non-misconceptions.
    if draft.attempt_type != "dont_know" and not draft.declared_dont_know:
        for promoted_error_type in dict.fromkeys(
            attribution.error_type for attribution in error_attributions
        ):
            maybe_promote_self_tagged_fatal_error(
                vault, repository, item=item, error_type=promoted_error_type, clock=clock
            )
    return result


def complete_empty_stuck_attempt(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    *,
    clock: Clock | None = None,
) -> AttemptResult:
    """Record an empty "I'm stuck" answer: an ordinary attempt scored 0.

    There is nothing to grade, so no model is called and no self-grade is
    asked for. Every criterion gets 0 points from a deterministic grade
    (``grading_source = "deterministic"``, grader tier 2, so the deferred
    self-grade regrade never picks it up), at the attempt type's standard
    evidence mass: there is no separate "don't know" weight.

    Owner decision 2026-10-12: it is just a score of 0, with NO error tag. It
    writes no attribution (no ``retrieval_failure``, and no
    ``scaffold_failure`` after hints), so no error event: an empty answer says
    nothing about understanding beyond the learner being unable to write
    anything. Historical ``dont_know`` rows keep their deterministic tag.
    """

    if not is_empty_stuck(draft):
        raise AttemptValidationError("only an empty stuck answer is scored without a grader")
    now_iso = utc_now_iso(clock)
    attempt_id = new_ulid()
    item, _learning_object, rubric, draft = _resolve_attempt_target(vault, repository, draft)
    criterion_points = {criterion.id: 0.0 for criterion in rubric.criteria}
    evidence_rows = [
        {
            "id": new_ulid(),
            "criterion_id": criterion.id,
            "points_awarded": 0.0,
            "evidence": EMPTY_STUCK_EVIDENCE,
            "notes": None,
            "local_grader_id": EMPTY_STUCK_LOCAL_GRADER_ID,
            "grader_tier": EMPTY_STUCK_GRADER_TIER,
            "learner_confidence": None,
            "created_at": now_iso,
        }
        for criterion in rubric.criteria
    ]
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=draft,
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=calculate_rubric_score(rubric, criterion_points, []),
                criterion_points=criterion_points,
                evidence_rows=evidence_rows,
                # Owner decision 2026-10-12: a bare 0, no error tag.
                error_attributions=[],
                grader_confidence=1.0,
                confidence=None,
                manual_review_reason=None,
                feedback_md=EMPTY_STUCK_FEEDBACK,
            ),
            grading_source="deterministic",
        ),
        clock=clock,
    )


def complete_codex_graded_attempt(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    proposal: GradingProposal,
    *,
    attempt_id: str | None = None,
    agent_run_id: str | None = None,
    grading_source: str = "codex",
    diagnostic_sample_support: float | None = None,
    grader_mode: str | None = None,
    grader_identity: tuple[str, str] | None = None,
    manual_review_override: str | None = None,
    unverified_criterion_ids: Iterable[str] = (),
    grade_held_for_review: bool = False,
    clock: Clock | None = None,
) -> AttemptResult:
    # `draft` is rebound: the resolver may have forced `primed` from the reveal
    # ledger, and everything downstream (grading context, the recorded row,
    # the IRT easiness shift) must use that draft, not the client's.
    item, _learning_object, rubric, draft = _resolve_attempt_target(vault, repository, draft)
    expected_attempt_id = attempt_id or proposal.attempt_id
    try:
        validated = validate_codex_grading_proposal(
            proposal,
            attempt_id=expected_attempt_id,
            item=item,
            vault=vault,
            learner_answer_md=draft.learner_answer_md,
            rubric=rubric,
        )
    except GradingValidationError as exc:
        raise AttemptValidationError(str(exc)) from exc
    if diagnostic_sample_support is not None:
        support = max(0.0, min(1.0, float(diagnostic_sample_support)))
        validated = replace(
            validated,
            error_attributions=[
                replace(attribution, diagnostic_sample_support=support)
                for attribution in validated.error_attributions
            ],
        )
    if grader_mode == "blind":
        # The blind grade's repaired traces live in its blind record; the
        # instructional repairs (and guided redo) arrive with the diagnosis
        # (§8). Persisting the traces here as repair suggestions would offer
        # a repair the diagnoser never chose.
        validated = replace(validated, repair_suggestions=[])
    unverified = tuple(dict.fromkeys(str(value) for value in unverified_criterion_ids))
    if unverified:
        # PF-c: the attempt's grade is over the assessed criteria only. With
        # nothing assessed and nothing validated (a hold: mvp-0.17's route
        # check, mvp-0.20's own-route rule) it is the grader's own.
        validated = replace(
            validated,
            rubric_score=assessed_rubric_score(
                rubric,
                {row.criterion_id: row.points_awarded for row in validated.criterion_evidence},
                validated.fatal_errors,
                unassessed_criterion_ids=unverified,
                answer_validated=not grade_held_for_review,
            ),
        )
    manual_review_reason = manual_review_override or validated.manual_review_reason
    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=draft,
            attempt_id=expected_attempt_id,
            grade=resolved_codex_grade(
                validated,
                agent_run_id=agent_run_id,
                clock=clock,
                manual_review_reason=_attempt_manual_review_reason(manual_review_reason, draft),
            ),
            grading_source=grading_source,
            grading_agent_run_id=agent_run_id,
            grader_mode=grader_mode,
            grader_identity=grader_identity,
            unverified_criterion_ids=unverified,
            grade_held_for_review=grade_held_for_review,
        ),
        clock=clock,
    )
    learning_object = vault.learning_object_for_item(item)
    persist_unknown_error_type_proposals(
        vault,
        repository,
        attributions=validated.error_attributions,
        attempt_id=expected_attempt_id,
        agent_run_id=agent_run_id,
        related_concept_id=learning_object.concept if learning_object is not None else None,
        clock=clock,
    )
    return result


#: ``replay_existing_attempt``: read the calibration identity from the ledgers.
_REPLAY_IDENTITY_FROM_LEDGER: Any = object()


def replay_existing_attempt(
    vault: LoadedVault,
    repository: Repository,
    attempt: dict,
    *,
    clock: Clock | None = None,
    error_event_ids: list[str] | None = None,
    error_events: list[dict[str, Any]] | None = None,
    error_attributions: list[GradeAttribution] | None = None,
    grader_identity: Any = _REPLAY_IDENTITY_FROM_LEDGER,
) -> AttemptResult:
    """Recompute derived state for a persisted attempt without re-grading it.

    ``grader_identity`` overrides the calibration identity replay otherwise
    reads from the ledgers (:func:`replay_grader_identity`); a regrade passes
    the identity its new grade was produced under.
    """

    evidence = repository.fetch_grading_evidence(attempt["id"])
    criterion_points = {row.criterion_id: row.points_awarded for row in evidence}
    # PF-c: the live grade's unverified criteria, read back from the block its
    # evidence rows carry (never from config), so replay leaves them
    # unassessed exactly as the live grade did. Joint rows never carry it.
    from learnloop.substrate.canonical_projection import unassessed_evidence_row

    unverified = tuple(
        row.criterion_id for row in evidence if unassessed_evidence_row(row.attribution_json)
    )
    draft = AttemptDraft(
        practice_item_id=attempt["practice_item_id"],
        learner_answer_md=attempt.get("learner_answer_md") or "",
        attempt_type=attempt.get("attempt_type") or "independent_attempt",
        hints_used=int(attempt.get("hints_used") or 0),
        latency_seconds=attempt.get("latency_seconds"),
        session_id=attempt.get("session_id"),
        probe_presentation_id=attempt.get("probe_presentation_id"),
        answer_confidence=attempt.get("answer_confidence"),
        assessment_contract_version_id=next(
            (
                row.assessment_contract_version_id
                for row in evidence
                if row.assessment_contract_version_id is not None
            ),
            None,
        ),
        submission_id=attempt.get("submission_id"),
        declared_dont_know=bool(attempt.get("declared_dont_know")),
        # mvp-0.13: what the learner sent was a stuck answer (persisted, never
        # read from today's stuck_prompt switch).
        declared_stuck=bool(attempt.get("declared_stuck")),
        # mvp-0.18: the answer-key status recorded at attempt time, never
        # re-derived from today's checks (a later verification is not
        # retroactive).
        reference_status=attempt.get("reference_status") or "not_applicable",
        # Replay must reproduce the recorded assistance state, not re-derive it.
        # `primed` drives the IRT easiness shift, the EB-difficulty exclusion and
        # the repair-activity classification, so a replay that dropped it would
        # silently recompute a primed attempt as clean evidence — and now that
        # priming can be FORCED from the reveal ledger, whose window has moved on
        # by replay time, re-deriving is not an option either. Read what was
        # recorded.
        primed=bool(attempt.get("primed")),
        auto_primed_reveal_total=(
            (repository.attempt_debug_payload(attempt["id"]) or {}).get(
                "auto_primed_reveal_total"
            )
            if attempt.get("primed")
            else None
        ),
    )
    error_type = attempt.get("error_type")
    blind_record = repository.latest_blind_grade_record(attempt["id"])
    from learnloop.held_grades import record_held_for_review

    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=draft,
            attempt_id=attempt["id"],
            grade=ResolvedGrade(
                rubric_score=int(attempt.get("rubric_score") or 0),
                criterion_points=criterion_points,
                evidence_rows=[],
                error_attributions=error_attributions
                if error_attributions is not None
                else _replay_error_attributions(vault, error_type, error_events=error_events),
                grader_confidence=float(attempt.get("grader_confidence") or 1.0),
                confidence=attempt.get("confidence"),
                manual_review_reason=attempt.get("manual_review_reason"),
            ),
            replace_existing=True,
            record_probe_update=False,
            error_event_ids_override=error_event_ids,
            # Replay must re-enter the same observation lane the live write
            # used: an ai/codex attempt replays through the soft-score channel,
            # a self/deterministic one through the raw fraction.
            grading_source=(
                (repository.raw_attempt_feedback_metadata(attempt["id"]) or {}).get(
                    "grading_source", "self"
                )
            ),
            # Slice 1 §6.3: a blind-graded attempt replays as blind (its
            # grade-channel identity, no in-transaction materialization unless
            # its stored diagnosis exists), whatever the config says today.
            grader_mode="blind" if blind_record is not None else None,
            grader_identity=(
                replay_grader_identity(repository, attempt["id"], blind_record)
                if grader_identity is _REPLAY_IDENTITY_FROM_LEDGER
                else grader_identity
            ),
            unverified_criterion_ids=unverified,
            # A grade held for review (mvp-0.17's route check, mvp-0.20's
            # own-route rule) replays held, from the record it was written with.
            grade_held_for_review=record_held_for_review(blind_record),
        ),
        clock=clock,
    )


def replay_grader_identity(
    repository: Repository, attempt_id: str, blind_record: Mapping[str, Any] | None
) -> tuple[str, str] | None:
    """The calibration identity a persisted grade replays under, from the ledgers.

    A practice attempt graded blind carries it in its blind record. Graders
    outside the practice door (teach-back, exams) write no blind record, but
    in a split vault they grade blind too: their raw grade event carries the
    blind identity they were calibrated under, so replay reads it there
    (review F11). Anything else is the joint grader's (None), so joint vaults
    replay exactly as before.
    """

    if blind_record is not None:
        return _blind_record_identity(blind_record)
    stamped = repository.latest_raw_grade_identity(attempt_id)
    if stamped is not None and stamped[1] == BLIND_GRADER_OUTPUT_SCHEMA_VERSION and stamped[0]:
        return (str(stamped[0]), str(stamped[1]))
    return None


def _blind_record_identity(blind_record: Mapping[str, Any] | None) -> tuple[str, str] | None:
    if blind_record is None:
        return None
    record = blind_record.get("record") or {}
    return (
        str(record.get("calibration_prompt_version") or BLIND_CALIBRATION_PROMPT_VERSION),
        str(record.get("calibration_output_schema_version") or BLIND_GRADER_OUTPUT_SCHEMA_VERSION),
    )


def agent_run_provider_fields(client: AIProviderClient, runtime) -> dict[str, str | None]:
    """Provider columns for a grading ``agent_runs`` row, client first, then runtime."""

    provider = getattr(client, "provider_name", None) or getattr(runtime, "active_provider", None) or "codex"
    provider_type = getattr(client, "provider_type", None) or getattr(runtime, "provider_type", None)
    model = getattr(client, "model", None) or getattr(runtime, "model", None)
    provider_revision = getattr(runtime, "provider_revision", None) or getattr(runtime, "actual_revision", None)
    fields = {
        "provider": provider,
        "provider_type": provider_type,
        "model": model,
        "provider_revision": provider_revision,
    }
    if provider == "codex" or provider_type == "codex_sdk":
        fields["codex_revision"] = provider_revision
    return fields


def _diagnostic_augmentation_setting(
    vault: LoadedVault,
    key: str,
    default: int | bool,
) -> int | bool:
    """Read the optional forward-compatible config block.

    ``LearnLoopConfig`` permits extra blocks so a vault can temporarily step
    C3 back to one sample while a revert is investigated without teaching the
    core config model a permanent experiment flag.  The shipped default is the
    active rung (k=3).
    """

    settings = getattr(vault.config, "diagnostic_augmentation", None)
    if isinstance(settings, Mapping):
        value = settings.get(key, default)
    else:
        value = getattr(settings, key, default) if settings is not None else default
    if isinstance(default, bool):
        return bool(value)
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _augmented_grading_context(
    vault: LoadedVault,
    repository: Repository,
    item: PracticeItem,
    context: Any,
) -> Any:
    from learnloop.diagnosis.diagnostic_augmentation import (
        DEFAULT_HISTORY_LIMIT,
        augment_grading_context,
    )

    history_limit = max(
        0,
        int(
            _diagnostic_augmentation_setting(
                vault, "history_limit", DEFAULT_HISTORY_LIMIT
            )
        ),
    )
    return augment_grading_context(
        vault,
        repository,
        item,
        context,
        history_limit=history_limit,
    )


@dataclass(frozen=True)
class _BlindGradingPlan:
    """What a split vault's practice grading call is shown (§4.1, PF-c)."""

    context: Any  # BlindGradingContext
    prompt_version: str
    context_hash: str
    calibration_prompt_version: str


#: ``_blind_grading_plan``'s default: grade under the item's current required
#: method (the live doors pass the assessment contract's instead).
_CURRENT_ITEM_METHOD: Any = object()


def _graded_required_method(item: PracticeItem, contract: dict[str, Any] | None) -> dict[str, Any] | None:
    """The required method an answer is graded under (review F1).

    The one its assessment contract froze when the item was presented; a
    contract without one (the presented item required none, or the contract
    predates method-explicit items) gives none, whatever the item says now.
    Without a contract the submission snapshots the item as it is now, so the
    item's current method is the presented one.
    """

    if contract is not None:
        return contract_required_method(contract)
    method = getattr(item, "required_method", None)
    return {"name": method.name, "criterion_ids": list(method.criterion_ids)} if method is not None else None


@dataclass(frozen=True)
class GradedContract:
    """The assessment contract a recorded attempt was graded under (review F1)."""

    version_id: str
    contract: dict[str, Any]

    @property
    def required_method(self) -> dict[str, Any] | None:
        return contract_required_method(self.contract)

    def rubric(self) -> Rubric:
        return rubric_from_contract(self.contract)

    def _froze(self, compiled: dict[str, Any]) -> bool:
        keys = ("item_content_hash", "rubric_content_hash")
        return all(self.contract.get(key) is not None and self.contract.get(key) == compiled.get(key) for key in keys)

    def graded_reference_contents(
        self, vault: LoadedVault, item: PracticeItem, connection: Any,
    ) -> tuple[list[str], str]:
        """The answer-key revision(s) a regrade under this contract graded (review F13, F19).

        A key check binds one revision of an item: its
        ``reference_content_hash`` (statement, expected answer and the item's
        OWN rubric, inline or inherited). A method-explicit contract records
        that hash when it is frozen (review F19), and the regrade binds
        exactly that revision: ``([hash], "frozen")``.

        A historical contract (frozen before it recorded the hash) froze the
        statement and expected answer verbatim and the RESOLVED rubric only by
        hash, so the revision is rebuilt from the frozen statement and answer
        with each rubric the item is known to have had (its current one and
        its recorded snapshots'). An inline rubric resolves to itself, so
        whether it matches the frozen contract is exact. An INHERITED rubric
        (``None``, when the item is known to have had one) resolved to the
        vault's default at the time, which is not recorded: today's default
        recovers it exactly only when it reproduces the frozen rubric hash.

        * one revision matches (the inherited one recovered exactly, if it
          was possible): ``([hash], "frozen")``;
        * several do: the ones a key check recorded (a verified attempt's
          revision had one), else all of them: ``(hashes, "ambiguous")``,
          bound fail closed (any unverified one lowers the grade);
        * the item is known to have inherited a default that today's default
          does not reproduce (round 3, F13/F19 reopened): the default the
          answer was graded under cannot be recovered, so the revision graded
          may be the inherited one under a default nobody can check, whatever
          else matches. ``(hashes, "ambiguous_default")``, the inherited
          revision first, bound UNVERIFIED (never frozen, never verified from
          today's default);
        * none does (the rubric changed too and no snapshot recorded the old
          one): every revision a key check recorded may be it, the current
          one excepted when the frozen statement or answer differs from it:
          ``(hashes, "unresolved")``, bound fail closed.
        """

        from learnloop.db.stores.source_service import (
            AMBIGUOUS_DEFAULT_REVISION, checked_content_hashes, reference_content_hash,
        )

        recorded = self.contract.get("reference_content_hash")
        if isinstance(recorded, str) and recorded:
            return [recorded], "frozen"
        frozen = {"prompt": self.contract.get("prompt"), "expected_answer": self.contract.get("expected_answer")}
        base = item.model_dump(mode="json")
        rubrics: list[Any] = [base.get("grading_rubric")]
        try:
            stored = connection.execute(
                "SELECT item_json FROM practice_item_snapshots WHERE practice_item_id = ? ORDER BY created_at DESC",
                (item.id,),
            ).fetchall()
        except Exception:  # noqa: BLE001 - a vault without snapshots rebuilds from the others
            stored = []
        for (item_json,) in stored:
            try:
                rubrics.append(json.loads(item_json).get("grading_rubric"))
            except (TypeError, ValueError, AttributeError):
                continue
        # The item is known to have inherited a default rubric (now, or in a
        # recorded snapshot): the inherited revision may be the one graded.
        inherited_known = any(rubric is None for rubric in rubrics)
        rubrics.append(None)
        tried: list[str] = []
        matched: list[str] = []
        unrecovered: str | None = None
        for rubric in rubrics:
            key = json.dumps(rubric, sort_keys=True, default=str)
            if key in tried:
                continue
            tried.append(key)
            try:
                view = PracticeItem.model_validate({**base, **frozen, "grading_rubric": rubric})
            except Exception:  # noqa: BLE001 - not a revision this item can have had
                continue
            try:
                compiled = compile_assessment_contract(vault, view, rubric=resolved_rubric(vault, view))
            except Exception:  # noqa: BLE001 - no rubric resolves (no default for the mode today)
                compiled = None
            content = reference_content_hash(view)
            if compiled is not None and self._froze(compiled):
                if content not in matched:
                    matched.append(content)
            elif rubric is None and inherited_known:
                # Today's default does not reproduce the frozen rubric: the
                # default the inherited revision was graded under is unknown.
                unrecovered = content
        if unrecovered is not None:
            return [unrecovered, *[content for content in matched if content != unrecovered]], \
                AMBIGUOUS_DEFAULT_REVISION
        if len(matched) == 1:
            return matched, "frozen"
        if matched:
            checked = set(checked_content_hashes(connection, item.id))
            return [content for content in matched if content in checked] or matched, "ambiguous"
        current = reference_content_hash(item)
        same_text = frozen["prompt"] == item.prompt and frozen["expected_answer"] == item.expected_answer
        candidates = [content for content in checked_content_hashes(connection, item.id)
                      if same_text or content != current]
        if not candidates:
            # No check recorded the revision graded (it never verified): the
            # best rebuild, which no check matches either, binds unverified.
            try:
                candidates = [reference_content_hash(PracticeItem.model_validate({**base, **frozen}))]
            except Exception:  # noqa: BLE001 - an identity no check carries
                candidates = [f"unrebuilt:{self.contract.get('item_content_hash')}"]
        return candidates, "unresolved"


def attempt_graded_contract(repository: Repository, attempt_id: str) -> GradedContract | None:
    """The assessment contract a recorded attempt's evidence rows cite.

    The one frozen when the item was presented, or snapshotted when it was
    first graded; superseded rows included, since a regrade outside a
    method-explicit item writes rows that cite none. None for an attempt
    graded before contracts (or whose contract is missing).
    """

    evidence = repository.fetch_grading_evidence(attempt_id, include_superseded=True)
    version_id = next(
        (row.assessment_contract_version_id for row in evidence if row.assessment_contract_version_id is not None),
        None,
    )
    if version_id is None:
        return None
    stored = repository.fetch_assessment_contract_version(version_id)
    if stored is None:
        return None
    return GradedContract(version_id=str(version_id), contract=dict(stored.get("contract") or {}))


def regrade_reads_contract(vault: LoadedVault, item: PracticeItem, graded: GradedContract | None) -> bool:
    """Does a regrade grade the answer under its assessment contract (re-review F1)?

    Only for a method-explicit item while the required-method rules are on
    (:func:`~learnloop.attempts.grading_support.method_rules_active`): its
    contract froze a required method, or the item has one now. The method,
    the statement that required it and the rubric whose criteria it lists
    are one contract, so the regrade reads all three from it: mixing the
    frozen method with today's statement would drop a requirement the
    learner was given (or enforce one they never saw). Every other regrade
    reads the item as it is now, as before (canonical sources §7.3a), and so
    does every regrade with the kill switch off (mvp-0.20 exactly).
    """

    if graded is None:
        return False
    from learnloop.attempts.grading_support import method_rules_active

    if not method_rules_active(vault):
        return False
    return graded.required_method is not None or getattr(item, "required_method", None) is not None


def _blind_grading_plan(
    vault: LoadedVault,
    item: PracticeItem,
    context: Any,
    *,
    stuck: bool = False,
    required_method: Any = _CURRENT_ITEM_METHOD,
) -> _BlindGradingPlan:
    """The learner-blind context for one answer: item side + this answer only.

    C2 verifier observations read only the answer and the reference, so they
    stay; C4 history has no field to go into (S1). PF-c's reference policy is
    attached unless ``diagnosis.grading_support`` is off (its kill switch,
    which restores the mvp-2.0 blind prompt exactly). ``stuck`` (mvp-0.13)
    tells the grader the answer came from "I'm stuck" and asks for its
    reading; an ordinary answer's context is unchanged, and so is the
    calibration identity (the scoring rules are the same). At mvp-0.20 the
    policy carries the own-route rules (kill switch ``proof_check.enabled``),
    which change the scoring rules, so they also name the calibration
    identity (``+own-route-v1``). At the method-explicit successor they are
    ``own-route-v2`` (kill switch ``required_method.enabled``) and the policy
    also carries the ``required_method`` the answer is graded under (review
    F1): the doors pass the one frozen with its assessment contract
    (:func:`_graded_required_method`); left out, it is the item's current one.
    """

    from learnloop.attempts.blind_grading import (
        blind_context_from_grading_context,
        blind_grading_context_hash,
        blind_prompt_version,
    )
    from learnloop.attempts.grading_support import (
        ITEM_REQUIRED_METHOD,
        REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION,
        reference_policy,
        route_rules_suffix,
        route_rules_version,
    )
    from learnloop.diagnosis.diagnostic_augmentation import (
        diagnostic_verifier_observations,
    )

    support = bool(getattr(getattr(vault.config, "diagnosis", None), "grading_support", True))
    rules = route_rules_version(vault) if support else None
    rubric_ids = [
        str(criterion.get("id"))
        for criterion in (context.rubric or {}).get("criteria") or ()
        if isinstance(criterion, dict) and criterion.get("id")
    ]
    blind_context = blind_context_from_grading_context(
        context,
        verifier_observations=diagnostic_verifier_observations(
            context.learner_answer_md, context.expected_answer
        ),
        reference_policy=(
            reference_policy(
                item, context.learner_answer_md, route_rules=rules or False, rubric_criterion_ids=rubric_ids,
                # The field frozen with the answer's contract: the one
                # authority (the prompt is never read to decide it).
                required_method=(
                    ITEM_REQUIRED_METHOD if required_method is _CURRENT_ITEM_METHOD else required_method
                ),
            )
            if support else None
        ),
        answer_prompt=stuck_answer_prompt() if stuck else None,
    )
    calibration = REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION if support else BLIND_CALIBRATION_PROMPT_VERSION
    return _BlindGradingPlan(
        context=blind_context,
        prompt_version=blind_prompt_version(blind_context),
        context_hash=blind_grading_context_hash(blind_context),
        calibration_prompt_version=f"{calibration}{route_rules_suffix(rules)}" if rules else calibration,
    )


def _grading_run_identity(context: Any, blind: _BlindGradingPlan | None) -> dict[str, str]:
    if blind is None:
        from learnloop.attempts.ai_contracts import grading_prompt_version

        return {
            "prompt_version": grading_prompt_version(context),
            "input_context_hash": grading_context_hash(context),
            "output_schema": "GradingProposal",
        }
    return {
        "prompt_version": blind.prompt_version,
        "input_context_hash": blind.context_hash,
        "output_schema": "BlindGradingProposal",
    }


def _complete_joint_graded_attempt(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    context: Any,
    *,
    ai_client: AIProviderClient,
    attempt_id: str,
    agent_run_id: str,
    grading_source: str,
    clock: Clock | None = None,
) -> AttemptResult:
    """Grade jointly (split off), apply it, and record its augmentation receipt.

    A stuck answer's joint grade carries the grader's reading (mvp-0.13,
    review F3): it is verified against the answer and appended to
    ``judgment_ledger`` in the transaction that records the grade, so the
    confusion signal and :func:`learnloop.attempts.stuck.stuck_answers` read
    it in either grading mode. The applied proposal is the ordinary joint one.
    """

    from learnloop.attempts.ai_contracts import StuckGradingProposal, grading_prompt_version
    from learnloop.attempts.grading import grading_context_hash

    consensus = _run_augmented_diagnosis(vault, ai_client, context)
    proposal = consensus.proposal
    marker = None
    if isinstance(proposal, StuckGradingProposal):
        marker = verified_stuck_reading(proposal.stuck_reading, draft.learner_answer_md)
        proposal = proposal.as_grading_proposal()
    with repository.atomic() if marker is not None else nullcontext():
        result = complete_codex_graded_attempt(
            vault,
            repository,
            draft,
            proposal,
            attempt_id=attempt_id,
            agent_run_id=agent_run_id,
            grading_source=grading_source,
            diagnostic_sample_support=consensus.agreement_support,
            clock=clock,
        )
        if marker is not None:
            record_stuck_reading_judgment(
                repository.connection(),
                attempt_id=attempt_id,
                marker=marker,
                judge_model=_client_model(ai_client),
                prompt_version=grading_prompt_version(context),
                input_hash=grading_context_hash(context),
                created_at=utc_now_iso(clock),
            )
    _record_diagnostic_augmentation(
        repository,
        attempt_id=attempt_id,
        context=context,
        consensus=consensus,
        client=ai_client,
        clock=clock,
    )
    return result


def _complete_blind_graded_attempt(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    blind: _BlindGradingPlan,
    *,
    rubric: Rubric,
    ai_client: AIProviderClient,
    attempt_id: str,
    agent_run_id: str,
    grading_source: str,
    clock: Clock | None = None,
) -> AttemptResult:
    """Grade blind, apply the grade and its blind record in one transaction.

    Raises like the joint path (provider unavailable, invalid output), so both
    doors keep their fallback/required semantics. The diagnosis is NOT run
    here: the post-attempt pipeline enqueues it (§11).
    """

    from learnloop.attempts.blind_grading import (
        to_grading_proposal,
        validate_blind_grading_proposal,
    )
    from learnloop.attempts.grading_support import (
        family_key,
        gated_review_reason,
        grade_uncertainty_signal,
        record_route_rule_judgment,
        request_blind_grading_run,
        revalidated_support,
    )
    from learnloop.outcome_contract import grade_held_for_review

    item = vault.practice_items[draft.practice_item_id]
    sample_count = _blind_sample_count(vault)
    run = request_blind_grading_run(
        ai_client, blind.context, rubric=rubric, sample_count=sample_count
    )
    try:
        validated = validate_blind_grading_proposal(
            run.proposal,
            attempt_id=attempt_id,
            item=item,
            vault=vault,
            learner_answer_md=draft.learner_answer_md,
            rubric=rubric,
        )
        # PF-c's informational reason, unless the grade carries a review
        # concern of its own (review F7).
        review_override = gated_review_reason(
            run,
            attempt_id=attempt_id,
            item=item,
            vault=vault,
            learner_answer_md=draft.learner_answer_md,
            rubric=rubric,
        )
    except GradingValidationError as exc:
        raise AttemptValidationError(str(exc)) from exc
    record = validated.as_record()
    # held-grade-evidence F1: the shortfall over the grade validation kept.
    support = revalidated_support(run.grading_support, record, rubric)
    family = family_key(vault, item)
    prior_fractions: list[float] = []
    for row in repository.latest_blind_grade_records().values():
        prior_record = row.get("record") or {}
        prior_item = vault.practice_items.get(str(prior_record.get("practice_item_id") or ""))
        if prior_item is None or family_key(vault, prior_item) != family:
            continue
        maximum = float(prior_record.get("max_points") or 0.0)
        if maximum > 0:
            prior_fractions.append(float(prior_record.get("rubric_score") or 0.0) / maximum)
    support["uncertainty_signal"] = grade_uncertainty_signal(
        score_fraction=float(validated.grade.rubric_score) / max(float(rubric.max_points), 1.0),
        grader_confidence=float(validated.grade.grader_confidence),
        prior_fractions=prior_fractions,
        family=family,
    )
    record.update(
        prompt_version=run.prompt_version,
        practice_item_id=item.id,
        calibration_prompt_version=blind.calibration_prompt_version,
        calibration_output_schema_version=BLIND_GRADER_OUTPUT_SCHEMA_VERSION,
        samples=run.samples,
        grading_support=support,
    )
    if run.stuck_reading is not None:
        # mvp-0.13: the grader's reading of a stuck answer, on the blind
        # record (the measurement), where the confusion signal reads it.
        record[STUCK_READING_KEY] = verified_stuck_reading(
            run.stuck_reading, draft.learner_answer_md
        )
    identity = (blind.calibration_prompt_version, BLIND_GRADER_OUTPUT_SCHEMA_VERSION)
    with repository.atomic():
        result = complete_codex_graded_attempt(
            vault,
            repository,
            draft,
            to_grading_proposal(run.proposal, vault=vault),
            attempt_id=attempt_id,
            agent_run_id=agent_run_id,
            grading_source=grading_source,
            grader_mode="blind",
            grader_identity=identity,
            manual_review_override=review_override,
            unverified_criterion_ids=tuple(support.get("unverified_criterion_ids") or ()),
            # mvp-0.20: the own-route rule held it (the record half of THE
            # held predicate; the attempt step evaluates the rest in flight).
            grade_held_for_review=grade_held_for_review(support),
            clock=clock,
        )
        repository.insert_blind_grade_record(
            attempt_id=attempt_id,
            agent_run_id=agent_run_id,
            grading_prompt_version=run.prompt_version,
            output_schema_version=BLIND_GRADER_OUTPUT_SCHEMA_VERSION,
            context_hash=blind.context_hash,
            record=record,
            clock=clock,
        )
        # mvp-0.20 (review F4): the grader's route verdict and the rule's
        # outcome, a ledger verdict in the same transaction (no model call).
        record_route_rule_judgment(
            repository.connection(),
            attempt_id=attempt_id,
            grading_support=support,
            judge_model=_client_model(ai_client),
            prompt_version=run.prompt_version,
            input_hash=blind.context_hash,
            created_at=utc_now_iso(clock),
        )
        if STUCK_READING_KEY in record:
            # Review F6: the reading is the grader's classification verdict,
            # appended in the same transaction as the grade and its record.
            record_stuck_reading_judgment(
                repository.connection(),
                attempt_id=attempt_id,
                marker=record[STUCK_READING_KEY],
                judge_model=_client_model(ai_client),
                prompt_version=run.prompt_version,
                input_hash=blind.context_hash,
                created_at=utc_now_iso(clock),
            )
    _record_blind_grading_receipt(
        repository,
        attempt_id=attempt_id,
        blind=blind,
        run=run,
        client=ai_client,
        clock=clock,
    )
    return result


def _client_model(client: Any) -> str | None:
    """The resolved model a client graded with (receipts record the same)."""

    return getattr(client, "model", None) or getattr(client, "model_id", None)


def _record_blind_grading_receipt(
    repository: Repository,
    *,
    attempt_id: str,
    blind: _BlindGradingPlan,
    run: Any,
    client: AIProviderClient,
    clock: Clock | None,
) -> None:
    """The grading-context receipt, with ``grader_mode='blind'`` (§10).

    C4 history is structurally empty, which is what cold-verification blinding
    reads. Telemetry: a failure here never turns a committed grade into one.
    """

    from learnloop.diagnosis.diagnostic_augmentation import (
        PHASE_C_HYPOTHESES,
        PHASE_C_REVERT_CRITERIA,
    )

    try:
        sampling = (run.grading_support or {}).get("sampling") or {}
        samples = int(sampling.get("sample_count") or run.samples or 1)
        votes = int(sampling.get("winner_votes") or samples)
        repository.insert_diagnostic_augmentation_receipt(
            {
                "attempt_id": attempt_id,
                "grading_prompt_version": run.prompt_version,
                "grader_provider": getattr(client, "provider_name", None),
                "grader_model": getattr(client, "model", None),
                "c1_repair_before_structure": True,
                "c2_verifier_observations": list(blind.context.verifier_observations),
                "c3_sample_count": samples,
                "c3_agreement_support": votes / max(samples, 1),
                "c3_disagreement_causes": [],
                "c4_history_attempt_ids": [],
                "hypotheses": PHASE_C_HYPOTHESES,
                "revert_criteria": PHASE_C_REVERT_CRITERIA,
                "grader_mode": "blind",
            },
            clock=clock,
        )
    except Exception:  # pragma: no cover - defensive side-channel boundary
        logging.getLogger(__name__).warning(
            "failed to record blind grading receipt for attempt %s",
            attempt_id,
            exc_info=True,
        )


def _blind_sample_count(vault: LoadedVault) -> int:
    """Blind grading samples per answer (one unless sampling is configured)."""

    if not bool(_diagnostic_augmentation_setting(vault, "sampling_enabled", True)):
        return 1
    return max(1, int(_diagnostic_augmentation_setting(vault, "sample_count", 1)))


def _joint_sample_count(vault: LoadedVault) -> int:
    """Joint grading (C3) samples per answer."""

    from learnloop.diagnosis.diagnostic_augmentation import DEFAULT_DIAGNOSIS_SAMPLES

    enabled = bool(
        _diagnostic_augmentation_setting(vault, "sampling_enabled", True)
    )
    return (
        max(
            1,
            int(
                _diagnostic_augmentation_setting(
                    vault, "sample_count", DEFAULT_DIAGNOSIS_SAMPLES
                )
            ),
        )
        if enabled
        else 1
    )


def _run_augmented_diagnosis(
    vault: LoadedVault,
    client: AIProviderClient,
    context: Any,
) -> Any:
    from learnloop.diagnosis.diagnostic_augmentation import run_diagnosis_samples

    return run_diagnosis_samples(client, context, sample_count=_joint_sample_count(vault))


def _record_diagnostic_augmentation(
    repository: Repository,
    *,
    attempt_id: str,
    context: Any,
    consensus: Any,
    client: AIProviderClient,
    clock: Clock | None,
) -> None:
    """Telemetry must not be able to turn a committed grade into a failure."""

    from learnloop.diagnosis.diagnostic_augmentation import record_phase_c_receipt

    try:
        record_phase_c_receipt(
            repository,
            attempt_id=attempt_id,
            context=context,
            consensus=consensus,
            grader_provider=getattr(client, "provider_name", None),
            grader_model=getattr(client, "model", None),
            clock=clock,
        )
    except Exception:  # pragma: no cover - defensive side-channel boundary
        logging.getLogger(__name__).warning(
            "failed to record diagnostic augmentation receipt for attempt %s",
            attempt_id,
            exc_info=True,
        )


def _assessment_contract(
    repository: Repository, draft: AttemptDraft
) -> dict[str, Any] | None:
    if draft.assessment_contract_version_id is None:
        return None
    stored = repository.fetch_assessment_contract_version(
        draft.assessment_contract_version_id
    )
    if stored is None or stored.get("practice_item_id") != draft.practice_item_id:
        raise AttemptValidationError(
            "assessment contract is missing or does not belong to the presented item"
        )
    return stored.get("contract") or {}


def reveal_total_for_submission(
    repository: Repository, practice_item_id: str, *, until: str | None = None
) -> float:
    """Summed answer exposure on this item since the learner last attempted it.

    Same window as ``tutor_qa.hint_equivalents_for_submission``: everything
    after the most recent prior attempt on the item, because anything earlier
    was already absorbed into that attempt's evidence. A post-attempt display
    linked to that attempt (``POST_ATTEMPT_REVEAL_KINDS``: the worked answer
    after an empty stuck answer, re-review F8) came after it, so it counts
    even when stamped in the attempt's own second."""

    attempts = repository.list_recent_attempts_by_practice_item(practice_item_id, limit=1)
    since = attempts[0]["created_at"] if attempts else None
    return repository.total_reveal_amount(
        practice_item_id,
        since=since,
        until=until,
        linked_attempt_id=str(attempts[0]["id"]) if attempts else None,
        linked_kinds=POST_ATTEMPT_REVEAL_KINDS,
    )


def auto_primed_draft(
    repository: Repository, draft: AttemptDraft, *, clock: Clock | None = None
) -> tuple[AttemptDraft, float]:
    """Force ``primed`` on a draft whose answer has already been handed over.

    Returns ``(draft, reveal_total)``. The draft is returned unchanged when it
    was already primed or the ledger is under threshold; otherwise a primed
    copy is returned so the attempt is recorded for what it is — a retry taken
    with the answer in view — rather than as clean unassisted evidence.

    The client cannot be trusted to declare this: the UI sets ``primed`` only
    for the source-review retry, and the tutor/feedback/repair surfaces that
    reveal an answer are exactly the ones that never set it. Reading the
    persisted ledger instead of a client flag is what closes that hole.

    Best-effort by construction: a ledger read failure must not block a
    submission, so it degrades to "no evidence of a reveal" and logs."""

    if draft.primed:
        return draft, 0.0
    try:
        total = reveal_total_for_submission(repository, draft.practice_item_id)
    except Exception:  # pragma: no cover - defensive
        logging.getLogger(__name__).warning(
            "reveal ledger read failed for %s; not auto-priming",
            draft.practice_item_id,
            exc_info=True,
        )
        return draft, 0.0
    if total < AUTO_PRIME_REVEAL_THRESHOLD:
        return draft, total
    return replace(draft, primed=True, auto_primed_reveal_total=total), total


def _resolve_attempt_target(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    *,
    replay: bool = False,
    clock: Clock | None = None,
):
    unsupported = unsupported_attempt_types([draft.attempt_type])
    if unsupported:
        supported = ", ".join(SUPPORTED_ATTEMPT_TYPES)
        raise AttemptValidationError(f"Unsupported attempt_type {draft.attempt_type}. Supported: {supported}")
    if draft.attempt_type in NON_RECORDING_ATTEMPT_TYPES:
        raise AttemptValidationError(f"{draft.attempt_type} does not write a formal attempt")
    item = vault.practice_items.get(draft.practice_item_id)
    if item is None:
        raise AttemptValidationError(f"Unknown Practice Item {draft.practice_item_id}")
    learning_object = vault.learning_object_for_item(item)
    if learning_object is None:
        raise AttemptValidationError(f"{item.id} references missing Learning Object {item.learning_object_id}")
    # "dont_know" is a universal escape hatch: a learner can always declare they
    # don't know an item regardless of its configured attempt_types_allowed. It
    # is graded deterministically (all criteria zeroed) rather than via Codex, so
    # it never depends on the item's allowed content attempt types.
    # "exam_evidence" is likewise exempt: it is an import path (exam seeding),
    # not a learner-chosen mode, and replay must be able to re-apply seeded
    # attempts on items that only list live attempt types.
    # "teach_back" is implied by the item's practice mode: the conversation
    # service records it on teach_back items regardless of the authored
    # attempt_types_allowed list. At replay time the exemption is unconditional
    # on the attempt_type — an attempt that was valid when recorded must always
    # replay, even after the item was edited to another practice mode.
    # "exam_attempt" is a held-out practice-exam answer applied at exam finish.
    # The pooled item is a regular practice item that only lists its live
    # attempt types, so the exam attempt type is exempt (like exam_evidence).
    # "self_report" is a mode-agnostic learner self-assessment (e.g. the
    # rung-variant request evidence write) — it never depends on the item's
    # live attempt-type list, so it is exempt like the other recording types.
    exempt_attempt_types = {"dont_know", "exam_evidence", "exam_attempt", "self_report"}
    if draft.attempt_type == "teach_back" and (replay or item.practice_mode == "teach_back"):
        exempt_attempt_types.add("teach_back")
    # Probe redesign §12: an active diagnostic episode forces the recording
    # attempt type to diagnostic_probe on whatever item was committed, so the
    # type is exempt whenever the submission consumes a presentation (and at
    # replay, where a recorded attempt must always re-apply).
    if draft.attempt_type == "diagnostic_probe" and (replay or draft.probe_presentation_id is not None):
        exempt_attempt_types.add("diagnostic_probe")
    if (
        item.attempt_types_allowed
        and draft.attempt_type not in exempt_attempt_types
        and draft.attempt_type not in item.attempt_types_allowed
    ):
        raise AttemptValidationError(f"{draft.attempt_type} is not allowed for {item.id}")
    try:
        contract = _assessment_contract(repository, draft)
        if contract is not None:
            from learnloop.learner.assessment_contracts import rubric_from_contract

            rubric = rubric_from_contract(contract)
        else:
            rubric = resolved_rubric(vault, item)
    except GradingValidationError as exc:
        raise AttemptValidationError(str(exc)) from exc
    if draft.hints_used < 0:
        raise AttemptValidationError("hints_used must be non-negative")
    if draft.latency_seconds is not None and draft.latency_seconds < 0:
        raise AttemptValidationError("latency_seconds must be non-negative")
    if draft.answer_confidence is not None and not 1 <= draft.answer_confidence <= 5:
        raise AttemptValidationError("answer_confidence must be between 1 and 5")
    if draft.declared_stuck and (draft.attempt_type == "dont_know" or draft.declared_dont_know):
        raise AttemptValidationError("a stuck answer is an ordinary attempt, never dont_know")
    if draft.declared_stuck and not replay and not stuck_prompt_active(vault):
        raise AttemptValidationError(
            "this vault does not offer \"I'm stuck\" (mvp-0.13 with stuck_prompt.enabled)"
        )
    if not replay:
        # Force priming from the reveal ledger BEFORE the cold guard below. The
        # order is the point: a learner who was just shown the answer and then
        # submits with primed=False must not be able to burn a cold measurement
        # as if it were clean — the guard has to see the forced value and
        # reject. On replay the recorded attempt is authoritative and the
        # ledger window has already moved past it, so this is skipped.
        draft, _reveal_total = auto_primed_draft(repository, draft, clock=clock)
        cold_task = repository.active_followup_task_for_item(
            draft.practice_item_id, at=utc_now_iso(clock)
        )
        # Both delayed lanes are COLD by definition: the repair-scoped
        # `cold_retry` (§6.2) and the §5.7 certification probe, whose whole claim
        # is "unassisted performance on a held-out surface two-to-three weeks
        # later". A primed or hinted attempt cannot make that claim, so the guard
        # is on the lane class, not on one kind.
        if cold_task is not None and cold_task.get("kind") in COLD_FOLLOWUP_TASK_KINDS:
            if draft.primed or draft.hints_used > 0 or draft.attempt_type == "hinted_attempt":
                raise AttemptValidationError("a cold retry must be unassisted and unprimed")
    return item, learning_object, rubric, draft


def _dual_write_grade_channel(
    vault: LoadedVault,
    repository: Repository,
    attempt: ApplyAttemptInput,
    application: "AttemptApplication",
    *,
    clock: Clock | None = None,
) -> None:
    """P0.2 dual-write (spec_p0_measurement_correctness §4.1, §7.2): append a raw
    grade event + calibrated interpretation alongside the legacy attempt summary.

    Fail-safe: never raises into the legacy path (§7.3). Ordinary practice attempts
    only -- diagnostic-probe attempts (record_probe_update) and exam attempts are
    dual-written by their own entry points (probe_episodes / exam_session)."""

    try:
        attempt_type = attempt.draft.attempt_type
        # Diagnostic-probe attempts are dual-written by the probe-episode path when
        # they carry a presentation; exam attempts by exam_session. Everything else
        # routed through apply_attempt is an ordinary practice attempt.
        if attempt_type == "diagnostic_probe" or "exam" in attempt_type:
            return
        item = vault.practice_items.get(attempt.draft.practice_item_id)
        if item is None:
            return
        grade = attempt.grade
        rubric = vault.rubric_for_item(item)
        max_points = rubric.max_points if rubric is not None else 4
        criterion_max = (
            {c.id: c.points for c in rubric.criteria} if rubric is not None else None
        )
        criterion_points = grade.criterion_points
        if attempt.unverified_criterion_ids:
            # PF-c: an unassessed criterion has no observed class (it reads
            # ``unassessable``), as it has no outcome anywhere else.
            unassessed = set(attempt.unverified_criterion_ids)
            criterion_points = {
                cid: points for cid, points in criterion_points.items() if cid not in unassessed
            }
        from learnloop.attempts.grade_resolution import record_grade_dual_write

        record_grade_dual_write(
            vault,
            repository,
            item=item,
            purpose="practice",
            grading_source=attempt.grading_source or application.result.grading_source,
            attempt_id=application.result.attempt_id,
            response_text=attempt.draft.learner_answer_md,
            rubric_score=grade.rubric_score,
            max_points=max_points,
            grader_confidence=grade.grader_confidence,
            has_fatal=bool(grade.fatal_errors),
            signature_matched=_signature_matched(attempt),
            criterion_points=criterion_points,
            criterion_max=criterion_max,
            agent_run_id=attempt.grading_agent_run_id,
            domain=application.result.learning_object_id,
            grading_prompt_version=(
                attempt.grader_identity[0] if attempt.grader_identity else None
            ),
            grader_output_schema_version=(
                attempt.grader_identity[1] if attempt.grader_identity else None
            ),
            clock=clock,
        )
    except Exception:  # noqa: BLE001 - fail-safe dual-write (§7.3)
        # record_grade_dual_write anchors its own degradation telemetry; this outer
        # guard only catches failures BEFORE it is reached (item/rubric lookup).
        # Never silent: degradation is visible, recoverable debt (audit B2).
        logging.getLogger(__name__).warning(
            "grade dual-write channel degraded before resolution for attempt %s",
            getattr(getattr(attempt, "draft", None), "practice_item_id", None),
            exc_info=True,
        )


def _signature_matched(attempt: ApplyAttemptInput) -> bool:
    """``raw_grade_events.signature_matched`` for this grade.

    Joint grades keep the grader's misconception flag. A blind grade has no
    causal judgement (O2), so the pre-registered discrimination-profile match
    is the only signature it can report.
    """

    grade = attempt.grade
    if attempt.grader_mode == "blind":
        match = grade.discrimination_profile_match
        outcome = (
            match.get("outcome") if isinstance(match, Mapping) else getattr(match, "outcome", None)
        )
        return outcome == "matched"
    return any(
        getattr(a, "is_misconception", False) for a in (grade.error_attributions or [])
    )


def _persist_repair_mapping_source(
    repository: Repository,
    result: AttemptResult,
    stored: Mapping[str, Any],
    *,
    clock: Clock | None = None,
) -> None:
    """Keep a replayed attempt's authored repair suggestions durable.

    ``attempt_feedback_metadata`` is the only durable copy of the authored
    repair suggestions, and ``causal_attribution
    .record_unresolved_cause_self_report`` re-materializes the causal episode
    from it; without the row a learner confirmation re-mints every hypothesis
    with ``repair_class_id = None``. New grades write the whole row
    (``_persist_new_grade_feedback``); this is the replay path.

    Deliberately conditional.  A replay/regrade re-enters this step with a grade
    reconstructed from the attempt row, which carries no repair suggestions; an
    unconditional upsert would blank the very column this exists to protect.
    The other columns are merged rather than overwritten for the same reason:
    this write must never downgrade what the post-attempt pipeline recorded.
    """

    suggestions = list(result.repair_suggestions or [])
    if not suggestions or list(stored.get("repair_suggestions") or []) == suggestions:
        return
    repository.upsert_attempt_feedback_metadata(
        attempt_id=result.attempt_id,
        grading_source=str(stored.get("grading_source") or result.grading_source),
        fallback_reason=stored.get("fallback_reason") or result.fallback_reason,
        agent_run_id=stored.get("agent_run_id") or result.agent_run_id,
        fatal_errors=list(stored.get("fatal_errors") or result.fatal_errors or []),
        feedback_md=stored.get("feedback_md") or result.feedback_md,
        repair_suggestions=suggestions,
        clock=clock,
    )


def _persist_new_grade_feedback(
    repository: Repository, result: AttemptResult, *, clock: Clock | None = None
) -> None:
    """Write the feedback metadata of a newly applied grade.

    The post-attempt pipeline writes the same row again, filling learner notes
    from the self-grade form where the grade has none.
    """

    repository.upsert_attempt_feedback_metadata(
        attempt_id=result.attempt_id,
        grading_source=result.grading_source,
        fallback_reason=result.fallback_reason,
        agent_run_id=result.agent_run_id,
        fatal_errors=list(result.fatal_errors or []),
        feedback_md=result.feedback_md,
        repair_suggestions=list(result.repair_suggestions or []),
        clock=clock,
    )


def apply_attempt(
    vault: LoadedVault,
    repository: Repository,
    attempt: ApplyAttemptInput,
    *,
    clock: Clock | None = None,
) -> AttemptResult:
    """Apply one resolved attempt through the shared learner-state pipeline.

    This is the single step used by live recording and deterministic replay. It
    expects grading to have already happened, computes all output rows, then
    persists attempt, mastery, facet recall, item quality, surprise, error
    events, ability transition audit, and debug trace.
    """

    # Reading-signal firewall (§8.2, design §C.2): the evidence-ingestion chokepoint
    # hard-rejects any input carrying salience-only authority. Reading is never
    # evidence -- a salience signal can never reach the belief pipeline.
    from learnloop.attempts.salience_firewall import reject_salience

    reject_salience(attempt, context="apply_attempt")

    with repository.atomic():
        result = _apply_attempt_in_transaction(vault, repository, attempt, clock=clock)
        if not attempt.replace_existing:
            _save_completion_work(vault, repository, attempt.draft, result, clock=clock)
        return result


def _apply_attempt_in_transaction(
    vault: LoadedVault,
    repository: Repository,
    attempt: ApplyAttemptInput,
    *,
    clock: Clock | None = None,
) -> AttemptResult:
    """Compute and persist one attempt; the caller owns the transaction."""

    # Reveal accounting (migration 154). Every recording path funnels through
    # here — the graded entry points, exam seeding, teach-back, the sim — so the
    # forcing lives here as well as in `_resolve_attempt_target`, and a caller
    # that builds an `ApplyAttemptInput` directly cannot skip it. Idempotent:
    # an already-primed draft returns unchanged without touching the ledger.
    # Skipped on replay (`replace_existing`), where the recorded attempt is
    # authoritative and the ledger window has already moved past it.
    if not attempt.replace_existing:
        normalized_draft, _reveal_total = auto_primed_draft(
            repository, attempt.draft, clock=clock
        )
        if normalized_draft is not attempt.draft:
            attempt = replace(attempt, draft=normalized_draft)

    application = compute_attempt_application(vault, repository, attempt, clock=clock)
    application = _validate_probe_presentation(repository, application, attempt, clock=clock)
    probe_grading_source = (
        "deterministic"
        if attempt.draft.attempt_type == "dont_know"
        or attempt.draft.declared_dont_know
        else attempt.grading_source
    )
    _stamp_observation_lineage(vault, repository, application, attempt, clock=clock)
    # Canonical-state vaults own facet state through the projection; the per-LO
    # recall/uncertainty bridge is written only for legacy algorithm versions.
    _persist_attempt_application(
        repository,
        application,
        replace_existing=attempt.replace_existing,
        write_legacy_facet_state=not is_canonical_state_vault(vault),
    )
    _dual_write_grade_channel(vault, repository, attempt, application, clock=clock)
    # Meas §3.A6: append the grader's trace observations. After persistence
    # because the FK needs the attempt row, and before `_project_canonical_belief`
    # below because A1 guard 1 reads them to decide which supporting targets earn
    # anything — an observation written after the projection would first take
    # effect a rebuild later, silently.
    _record_exercised_facets(repository, application, clock=clock)
    _record_grading_clarification(repository, application, clock=clock)
    # Meas §3.A5 / §3.A3 (migration 143). Same position and same reasoning as the
    # two writers above: after persistence because both stores hold an
    # `attempt_id` foreign key, and before the canonical projection because the
    # A3 clean-solution path may have suppressed a facet write whose absence the
    # projection is about to observe.
    _record_discrimination_profile_match(repository, application, clock=clock)
    _record_error_hunt_outcome(repository, application, vault=vault, clock=clock)

    # Measurement §5.7: the delayed cold probe's ground-truth label. Sits here,
    # beside the repair-scoped cold retry and deliberately BEFORE
    # `_project_canonical_belief` below, because the certificate state it records
    # must be the one the probe was administered against — not the one this
    # attempt's own evidence produces. After projection, a failing probe would
    # have already withdrawn the certificate it just falsified, and the label
    # would abstain instead of recording the false certification.
    from learnloop.goals.certification_cold_probe import (
        record_certification_cold_probe_attempt,
    )

    record_certification_cold_probe_attempt(
        vault,
        repository,
        application.attempt_record,
        grading_source=application.result.grading_source,
        grading_agent_run_id=attempt.grading_agent_run_id,
        # held-grade-evidence F3: a held grade abstains from the label.
        grade_held_for_review=application.grade_held,
        clock=clock,
    )
    if attempt.draft.primed:
        # Priming IS the intervention, so the attempt is a repair activity
        # (§7). A primed *probe* is also a diagnostic administration; both
        # writers append and the repository derives the most-contaminated
        # class (§4.2).
        policy = classify_attempt_activity(
            attempt_type=attempt.draft.attempt_type,
            primed=True,
            hints_used=attempt.draft.hints_used,
            explicit_class="repair_activity",
        )
        repository.record_causal_activity_classification(
            attempt_id=application.result.attempt_id,
            contamination_class=policy.contamination_class,
            near_clone=policy.near_clone,
            near_clone_basis="no_source_item",
            source="apply_attempt.primed",
            detail={"practice_item_id": attempt.draft.practice_item_id},
            clock=clock,
        )
    if (
        attempt.record_probe_update
        and application.attempt_record.get("probe_presentation_id") is not None
    ):
        # The full probe observation is recorded after causal materialization,
        # but its activity policy is an INPUT to the canonical projection just
        # below. Persist the presentation-derived contamination/near-clone fact
        # first so live state and a later replay cannot disagree.
        from learnloop.diagnosis.probe_episodes import (
            record_presentation_activity_classification,
        )

        record_presentation_activity_classification(
            vault,
            repository,
            attempt_id=application.result.attempt_id,
            practice_item_id=attempt.draft.practice_item_id,
            attempt_type=attempt.draft.attempt_type,
            hints_used=attempt.draft.hints_used,
            probe_presentation_id=str(
                application.attempt_record["probe_presentation_id"]
            ),
            grading_source=probe_grading_source,
            clock=clock,
        )
    _auto_resolve_clean_error_events(vault, repository, application, clock=clock)
    _project_canonical_belief(vault, repository, clock=clock)
    from learnloop.diagnosis.causal_attribution import materialize_causal_episode

    if attempt.replace_existing:
        stored_feedback = repository.fetch_attempt_feedback_metadata(
            application.result.attempt_id
        ) or {}
        _persist_repair_mapping_source(
            repository, application.result, stored_feedback, clock=clock
        )
    else:
        # A new grade's metadata is complete here, before materialization and
        # episode accounting: a block this attempt closes normalizes the whole
        # block inside this transaction, and normalization reads the grading
        # run from this row. Without it, the block's hypotheses would be
        # re-versioned with no grader provenance.
        _persist_new_grade_feedback(repository, application.result, clock=clock)
        stored_feedback = {}
    repair_suggestions = (
        application.result.repair_suggestions
        or stored_feedback.get("repair_suggestions")
        or []
    )
    generation_agent_run_id = stored_feedback.get("diagnosis_agent_run_id") or next(
        (
            str(row["agent_run_id"])
            for row in application.evidence_rows
            if row.get("agent_run_id")
        ),
        None,
    )
    has_causal_episode = bool(
        application.error_events
        or repair_suggestions
        or repository.unresolved_cause_factors_for_attempt(
            application.result.attempt_id,
            status="open",
        )
    )
    if attempt.grader_mode == "blind" and (
        repository.live_causal_view(application.result.attempt_id) is None
    ):
        # Slice 1 §7.1: a blind grade carries no candidate causes or
        # instructional repairs, so nothing causal is materialized here. The
        # diagnosis worker materializes from the diagnosis once it completes;
        # replay of a diagnosed attempt materializes here from the same stored
        # diagnosis (the repository's causal overlay), and an undiagnosed or
        # failed one materializes nothing, exactly as live.
        has_causal_episode = False
    if has_causal_episode:
        materialize_causal_episode(
            vault,
            repository,
            attempt_id=application.result.attempt_id,
            repair_suggestions=list(repair_suggestions),
            generation_agent_run_id=generation_agent_run_id,
            clock=clock,
        )
        persisted_debug = repository.attempt_debug_payload(
            application.result.attempt_id
        )
        application = replace(
            application,
            attempt_debug_payload=(
                persisted_debug or application.attempt_debug_payload
            ),
            result=replace(
                application.result,
                debug_payload=persisted_debug
                or application.result.debug_payload,
            ),
        )
    # Repair-lane bookkeeping runs AFTER `materialize_causal_episode` on purpose.
    # The primed branch of `record_remediation_attempt` resolves the §6.2
    # cold-verification context, whose misconception-kind fallback reads THIS
    # attempt's diagnosis receipt out of `attempt_debug_payloads` — a receipt
    # materialize has only just written. Running the remediation hook earlier
    # leaves `context.repair_class_id` NULL for every misconception-kind
    # episode, and the delayed cold verification then refuses with
    # `missing_chain/no_repair_class` on consume. Nothing
    # above depends on remediation state: the certification lane consumes its
    # own task kind, and materialize/projection never read
    # `remediation_episodes` or `followup_tasks`.
    from learnloop.diagnosis.remediation import record_remediation_attempt

    record_remediation_attempt(repository, application.attempt_record, clock=clock)
    if attempt.record_probe_update:
        # Episode accounting owns probe advancement; `record_probe_attempt` is
        # kept only for pre-redesign replay. Belief updates and episode
        # advancement are separated inside `record_episode_evidence`.
        from learnloop.diagnosis.probe_episodes import record_episode_evidence

        block_end = record_episode_evidence(
            vault,
            repository,
            learning_object_id=application.result.learning_object_id,
            attempt_id=application.result.attempt_id,
            practice_item_id=attempt.draft.practice_item_id,
            attempt_type=attempt.draft.attempt_type,
            hints_used=attempt.draft.hints_used,
            probe_presentation_id=application.attempt_record.get("probe_presentation_id"),
            grading_source=probe_grading_source,
            # held-grade-evidence F11: a held probe answer moves no posterior.
            grade_held_for_review=application.grade_held,
            clock=clock,
        )
        if block_end is not None:
            application = replace(application, result=replace(application.result, probe_block_end=block_end))
    return application.result


def _save_completion_work(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    result: AttemptResult,
    *,
    clock: Clock | None = None,
) -> None:
    """Save the applied result in the attempt's own transaction.

    Completion routes the learner by the probe episode recorded here. It is
    read after this attempt's episode accounting, so an attempt that ended its
    episode records none, and a later resume cannot attach it to an episode
    opened afterwards. An unanswered opening episode placement ignores is not
    recorded (owner decision 2026-10-12): the attempt is ordinary new material.
    """

    if draft.awaits_completion:
        from learnloop.placement.state import servable_open_episode

        episode = servable_open_episode(vault, repository, result.learning_object_id)
        repository.save_attempt_completion(
            attempt_id=result.attempt_id,
            submission_id=draft.submission_id,
            session_id=draft.session_id,
            practice_item_id=result.practice_item_id,
            result=result.as_dict(),
            applied_probe_episode_id=episode.id if episode is not None else None,
            clock=clock,
        )
        return
    # Nothing resumes this row, so its debug trace (already stored in
    # attempt_debug_payloads) is not duplicated into it.
    repository.save_attempt_completion(
        attempt_id=result.attempt_id,
        submission_id=draft.submission_id,
        session_id=draft.session_id,
        practice_item_id=result.practice_item_id,
        result={**result.as_dict(), "debug": {}},
        awaits_completion=False,
        clock=clock,
    )


def _project_canonical_belief(
    vault: LoadedVault, repository: Repository, *, clock: Clock | None = None
) -> None:
    """Recompute the canonical shared belief cache after an attempt (mvp-0.7).

    A no-op on legacy vaults (the projection early-returns), so mvp-0.6 replay is
    byte-identical. The recompute is a deterministic fold over the immutable
    observation ledger, so live state and replayed state coincide by construction.
    """

    if vault.config.algorithms.algorithm_version not in CANONICAL_STATE_VERSIONS:
        return
    from learnloop.substrate.canonical_projection import project_canonical_facet_state

    project_canonical_facet_state(vault, repository, clock=clock)


def _validate_probe_presentation(
    repository: Repository,
    application: AttemptApplication,
    attempt: ApplyAttemptInput,
    *,
    clock: Clock | None = None,
) -> AttemptApplication:
    """Pre-persist §5.4 validation: an invalid, mismatched, ended, or already
    consumed presentation reference is stripped so the attempt records as
    incidental evidence (and the unique presentation index never rejects the
    row). A retried submission of the same attempt keeps its link (idempotent)."""

    presentation_id = application.attempt_record.get("probe_presentation_id")
    if not presentation_id:
        return application
    from learnloop.diagnosis.probe_episodes import validate_presentation_for_submission

    validation = validate_presentation_for_submission(
        repository,
        str(presentation_id),
        practice_item_id=attempt.draft.practice_item_id,
        attempt_id=attempt.attempt_id,
        clock=clock,
    )
    if validation.valid:
        return application
    stripped = dict(application.attempt_record)
    stripped["probe_presentation_id"] = None
    return replace(application, attempt_record=stripped)


def compute_attempt_application(
    vault: LoadedVault,
    repository: Repository,
    attempt: ApplyAttemptInput,
    *,
    clock: Clock | None = None,
    prior_state: AttemptPriorState | None = None,
) -> AttemptApplication:
    """Compute the rows and result for one resolved attempt without persisting.

    This is the testable state-output boundary for live recording, replay, and
    calibration. It reads the current prior state but does not write to storage.
    """

    return _compute_resolved_grade_application(
        vault,
        repository,
        attempt.draft,
        attempt_id=attempt.attempt_id,
        grade=attempt.grade,
        clock=clock,
        error_event_ids_override=attempt.error_event_ids_override,
        prior_state=prior_state,
        replay=attempt.replace_existing,
        grading_source=attempt.grading_source,
        agent_run_id=attempt.grading_agent_run_id or attempt.fallback_agent_run_id,
        fallback_reason=attempt.fallback_reason,
        grader_identity=attempt.grader_identity,
        unassessed_criterion_ids=attempt.unverified_criterion_ids,
        grade_held_for_review=attempt.grade_held_for_review,
    )


def _stamp_observation_lineage(
    vault: LoadedVault,
    repository: Repository,
    application: AttemptApplication,
    attempt: ApplyAttemptInput,
    *,
    clock: Clock | None = None,
) -> None:
    """Snapshot the assessment contract and stamp observation ids (KM §5.2).

    Only runs on canonical-state vaults, and only for freshly recorded grading evidence
    (not the replace/replay path, which reuses stored rows). Legacy vaults skip
    this entirely, so mvp-0.6 replay reproduces byte-identical derived state.
    """

    from learnloop.learner.assessment_contracts import (
        KM_ALGORITHM_VERSION,
        snapshot_for_presentation,
    )

    if vault.config.algorithms.algorithm_version not in CANONICAL_STATE_VERSIONS:
        return
    if attempt.replace_existing or not application.evidence_rows:
        return
    item = vault.practice_items.get(attempt.draft.practice_item_id)
    if item is None:
        return
    version_id = attempt.draft.assessment_contract_version_id
    if version_id is not None:
        stored = repository.fetch_assessment_contract_version(version_id)
        if (
            stored is None
            or stored.get("practice_item_id") != item.id
        ):
            raise AttemptValidationError(
                "assessment contract is missing or does not belong to the presented item"
            )
    else:
        version_id = snapshot_for_presentation(repository, vault, item, clock=clock)
    stored = repository.fetch_assessment_contract_version(version_id)
    contract = stored.get("contract") if stored is not None else {}
    criteria = {
        str(criterion.get("id")): criterion
        for criterion in contract.get("criteria") or []
    }
    attempt_id = application.result.attempt_id
    revision = 0
    unverified = {str(value) for value in attempt.unverified_criterion_ids}
    for row in application.evidence_rows:
        criterion_id = row.get("criterion_id")
        if criterion_id is None:
            continue
        if row.get("attribution_json") is None and str(criterion_id) in unverified:
            row["attribution_json"] = unverified_attribution_json()
        row.setdefault("assessment_contract_version_id", version_id)
        row.setdefault("grading_revision", revision)
        row.setdefault("observation_id", f"{attempt_id}:{criterion_id}:{revision}")
        if row.get("correlation_group") is None:
            historical = criteria.get(str(criterion_id)) or {}
            row["correlation_group"] = historical.get("correlation_group")
            if row["correlation_group"] is None:
                row["correlation_group"] = _criterion_correlation_group(item, str(criterion_id))
        if row.get("attribution_json") is None:
            criterion = criteria.get(str(criterion_id)) or {}
            targets = criterion.get("targets") or []
            target_keys = {
                (str(target.get("facet") or ""), str(target.get("capability") or ""))
                for target in targets
            }
            selected: set[tuple[str, str]] = set()
            machine_review_blocked = False
            blocked_reason = "machine_review_scope"
            for event in application.error_events:
                repair_plan = (
                    event.get("repair_plan")
                    if isinstance(event.get("repair_plan"), dict)
                    else {}
                )
                target_families = [
                    str(value)
                    for value in repair_plan.get("target_evidence_families") or []
                ]
                target_criteria = [
                    str(value)
                    for value in repair_plan.get("target_criterion_ids") or []
                ]
                target_ref = (
                    repair_plan.get("target_ref")
                    if isinstance(repair_plan.get("target_ref"), dict)
                    else None
                )
                machine_review_scope = repair_plan.get("cause_scope") in {
                    "item_contract",
                    "grader_interpretation",
                }
                # A deliberately cleared facet target list is a BLOCK, not an
                # absence. Without this the emptied attribution falls through to
                # `attribution_json = NULL`, and the projection's single-target
                # fallback then attributes the whole failure to the criterion's
                # own target — banking the facet failure the guard just removed.
                facet_write_blocked = repair_plan.get("facet_write_blocked")
                event_has_target = bool(
                    target_families
                    or target_criteria
                    or (
                        target_ref is not None
                        and target_ref.get("kind") != "none"
                    )
                )
                event_matches_criterion = (
                    not event_has_target
                    or str(criterion_id) in target_criteria
                    or bool(
                        set(target_families)
                        & {facet for facet, _capability in target_keys}
                    )
                    or (
                        target_ref is not None
                        and target_ref.get("kind") == "criterion"
                        and str(target_ref.get("criterion_id") or "")
                        == str(criterion_id)
                    )
                    or (
                        target_ref is not None
                        and target_ref.get("kind") == "facet_capability"
                        and str(target_ref.get("facet_id") or "")
                        in {facet for facet, _capability in target_keys}
                    )
                )
                if (machine_review_scope or facet_write_blocked) and event_matches_criterion:
                    machine_review_blocked = True
                    blocked_reason = (
                        str(facet_write_blocked)
                        if facet_write_blocked
                        else "machine_review_scope"
                    )
                    continue
                resolution_status = repair_plan.get("resolution_status")
                if resolution_status is None:
                    resolution_status = (
                        "resolved"
                        if target_families
                        or target_criteria
                        or (
                            target_ref is not None
                            and target_ref.get("kind") != "none"
                        )
                        else "unresolved"
                    )
                if resolution_status != "resolved":
                    continue
                if (
                    target_criteria
                    and str(criterion_id) not in target_criteria
                ):
                    continue
                for facet in target_families:
                    selected.update(key for key in target_keys if key[0] == facet)
            if selected:
                weight = 1.0 / len(selected)
                row["attribution_json"] = json.dumps(
                    {
                        "targets": [
                            {"facet": facet, "capability": capability, "weight": weight}
                            for facet, capability in sorted(selected)
                        ]
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
            elif machine_review_blocked:
                row["attribution_json"] = json.dumps(
                    {
                        "targets": [],
                        "negative_evidence_blocked": blocked_reason,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )


def unverified_attribution_json() -> str:
    """The persisted block of an unverified criterion (PF-c gate).

    It names the interpretation it is written under (the unassessed rule,
    owner decision 2026-10-12), so replay reads every row as it was written: a
    row from before the rule carries no mark and keeps its M2 reading
    (``canonical_projection.unassessed_evidence_row``).
    """

    from learnloop.substrate.canonical_projection import (
        UNASSESSED_INTERPRETATION,
        UNVERIFIED_CRITERION_BLOCK,
        UNVERIFIED_INTERPRETATION_KEY,
    )

    return json.dumps(
        {
            "targets": [],
            "negative_evidence_blocked": UNVERIFIED_CRITERION_BLOCK,
            UNVERIFIED_INTERPRETATION_KEY: UNASSESSED_INTERPRETATION,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _criterion_correlation_group(item: PracticeItem, criterion_id: str) -> str | None:
    rubric = item.grading_rubric
    if rubric is None:
        return None
    for criterion in rubric.criteria:
        if criterion.id == criterion_id:
            return criterion.correlation_group
    return None


def _persist_attempt_application(
    repository: Repository,
    application: AttemptApplication,
    *,
    replace_existing: bool,
    write_legacy_facet_state: bool = True,
) -> None:
    # mvp-0.7 retires the legacy per-LO facet-state bridge: the derived updates
    # are still computed (surprise/breadth/debug read them in memory) but never
    # persisted — the canonical projection owns that state. The empty iterables
    # also keep the repository hard-stop guard from ever tripping in normal flow.
    facet_recall_states = application.facet_recall_states if write_legacy_facet_state else ()
    facet_uncertainty_states = (
        application.facet_uncertainty_states if write_legacy_facet_state else ()
    )
    if replace_existing:
        repository.replace_attempt_derived_outcome(
            attempt=application.attempt_record,
            error_events=application.error_events,
            surprise=application.surprise_record,
            practice_item_state=application.practice_item_state,
            mastery_state=application.mastery_state,
            facet_recall_states=facet_recall_states,
            facet_uncertainty_states=facet_uncertainty_states,
            quality_state=application.quality_state,
            ability_transition=application.ability_transition,
            attempt_debug_payload=application.attempt_debug_payload,
            item_parameter_state=application.item_parameter_state,
        )
    else:
        repository.record_attempt_outcome(
            attempt=application.attempt_record,
            evidence_rows=application.evidence_rows,
            error_events=application.error_events,
            surprise=application.surprise_record,
            practice_item_state=application.practice_item_state,
            mastery_state=application.mastery_state,
            facet_recall_states=facet_recall_states,
            facet_uncertainty_states=facet_uncertainty_states,
            quality_state=application.quality_state,
            ability_transition=application.ability_transition,
            attempt_debug_payload=application.attempt_debug_payload,
            item_parameter_state=application.item_parameter_state,
        )


def _discrimination_profile_telemetry(match) -> dict[str, Any]:
    """A5's per-attempt tally, from the ONE implementation of the arm vocabulary.

    Imported lazily rather than at module scope because
    ``discrimination_profiles`` reaches back into grading, and a top-level import
    here closes the cycle.
    """

    from learnloop.diagnosis.discrimination_profiles import profile_match_telemetry

    return profile_match_telemetry(match)


def _record_discrimination_profile_match(
    repository: Repository,
    application: AttemptApplication,
    *,
    clock: Clock | None = None,
) -> str | None:
    """Persist the attempt's A5 judgement (Meas §3.A5, migration 143).

    Written for every arm including ``no_profiles_offered``, because §3.A5's
    revert criterion is a RATE and a rate needs the cases where the question was
    not asked to be distinguishable from the cases where it was asked and
    declined.

    ``attempt_failed`` is stamped here rather than recomputed later: the
    rejection rate is only meaningful over failures (a profile describes a wrong
    answer), and a later recomputation would key on a `rubric_score` a regrade
    can move — which would silently re-weight history.

    Nothing is written for a SELF-graded or replayed attempt: no diagnostician
    ran, so it was offered no candidate set, and recording
    ``no_profiles_offered`` there would pad the denominator with attempts that
    never asked the question. The arm means "the diagnostician was offered no
    profiles", not "no diagnostician ran".

    Failures are swallowed with a log line, matching the A5-note/A6/A8 writers: a
    diagnostic side channel must never be able to take a graded attempt down.
    """

    match = getattr(application.result, "discrimination_profile_match", None)
    if not match:
        return None
    from learnloop.attempts.ai_contracts import GRADING_PROMPT_VERSION

    try:
        return repository.insert_discrimination_profile_match(
            attempt_id=application.result.attempt_id,
            practice_item_id=application.result.practice_item_id,
            outcome=str(match.get("outcome") or ""),
            profile_id=match.get("profile_id"),
            misconception_id=match.get("misconception_id"),
            evidence=match.get("evidence") or None,
            attempt_failed=float(application.result.correctness or 0.0) < 0.5,
            grading_prompt_version=GRADING_PROMPT_VERSION,
            agent_run_id=application.result.agent_run_id,
            clock=clock,
        )
    except Exception:  # pragma: no cover - defensive, mirrors the A6 writer
        logging.getLogger(__name__).warning(
            "failed to record discrimination profile match for attempt %s",
            application.result.attempt_id,
            exc_info=True,
        )
        return None


def _record_error_hunt_outcome(
    repository: Repository,
    application: AttemptApplication,
    *,
    vault: LoadedVault | None = None,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Persist the attempt's A3 outcome and mint the §10 misconception candidate.

    The candidate write lives inside ``error_hunt.record_error_hunt_outcome``
    rather than here, so the two halves of §10's line — "writes a misconception
    candidate" and "not a facet failure" — are decided by the same module that
    suppressed the facet write, instead of one in the validator and one in the
    attempt pipeline.
    """

    payload = getattr(application.result, "error_hunt", None)
    if not payload:
        return None
    from learnloop.attempts.ai_contracts import GRADING_PROMPT_VERSION
    from learnloop.diagnosis.error_hunt import (
        FalsePositiveReport,
        PlantOutcome,
        PlantResult,
        ValidatedErrorHunt,
        record_error_hunt_outcome,
    )

    hunt = ValidatedErrorHunt(
        practice_item_id=str(payload.get("practice_item_id") or ""),
        clean_solution=bool(payload.get("clean_solution")),
        plants=tuple(
            PlantResult(
                planted_error_id=str(row.get("planted_error_id") or ""),
                outcome=PlantOutcome(str(row.get("outcome") or PlantOutcome.MISSED)),
                facet_id=row.get("facet_id"),
                misconception_id=row.get("misconception_id"),
                report_index=row.get("report_index"),
            )
            for row in (payload.get("plants") or [])
        ),
        false_positives=tuple(
            FalsePositiveReport(
                report_index=int(row.get("report_index") or 0),
                location=str(row.get("location") or ""),
                claim_md=str(row.get("claim_md") or ""),
                repair_md=str(row.get("repair_md") or ""),
            )
            for row in (payload.get("false_positives") or [])
        ),
        facet_failure_suppressed=bool(payload.get("facet_failure_suppressed")),
    )
    try:
        return record_error_hunt_outcome(
            repository,
            hunt,
            attempt_id=application.result.attempt_id,
            learning_object_id=application.result.learning_object_id,
            grading_prompt_version=GRADING_PROMPT_VERSION,
            vault=vault,
            clock=clock,
        )
    except Exception:  # pragma: no cover - defensive, mirrors the A6 writer
        logging.getLogger(__name__).warning(
            "failed to record error hunt outcome for attempt %s",
            application.result.attempt_id,
            exc_info=True,
        )
        return None


def _record_exercised_facets(
    repository: Repository,
    application: AttemptApplication,
    *,
    clock: Clock | None = None,
) -> int:
    """Append the attempt's A6 trace observations (Meas §3.A6, migration 141).

    Idempotent by the store's ``(attempt_id, facet_id, source)`` key, so a
    regrade re-reporting the same trace adds nothing and the first run's wording
    survives — the observation is a record of what the grader said it saw, and a
    record that can be rewritten afterwards is not evidence.

    Failures are swallowed with a log line for the same reason the A5 note
    writer swallows them: a bonus evidence channel must never be able to take a
    graded attempt down.
    """

    rows = list(getattr(application.result, "exercised_facets", None) or [])
    if not rows:
        return 0
    agent_run_id = application.result.agent_run_id
    from learnloop.attempts.ai_contracts import GRADING_PROMPT_VERSION

    payload = [
        {**row, "agent_run_id": agent_run_id, "grading_prompt_version": GRADING_PROMPT_VERSION}
        for row in rows
    ]
    try:
        return repository.insert_trace_exercised_facets(
            application.result.attempt_id, payload, clock=clock
        )
    except Exception:  # pragma: no cover - defensive, mirrors the A5 note writer
        logging.getLogger(__name__).warning(
            "failed to record trace-exercised facets for attempt %s",
            application.result.attempt_id,
            exc_info=True,
        )
        return 0


def _record_grading_clarification(
    repository: Repository,
    application: AttemptApplication,
    *,
    clock: Clock | None = None,
) -> str | None:
    """Persist the grader's clarification request, if it made a licensed one.

    The grade is already recorded as `provisional_pending_clarification` by the
    validator (it sets `manual_review_reason`), so this only stores the question.
    Swallowing failures is deliberate and matches the A5/A6 writers: a channel
    that exists to make abstention cheap must never make a graded attempt fail.
    """

    clarification = getattr(application.result, "clarification", None)
    if not clarification:
        return None
    from learnloop.attempts.ai_contracts import GRADING_PROMPT_VERSION
    from learnloop.attempts.clarification import record_clarification

    try:
        return record_clarification(
            repository,
            attempt_id=application.result.attempt_id,
            clarification=clarification,
            agent_run_id=application.result.agent_run_id,
            grading_prompt_version=GRADING_PROMPT_VERSION,
            clock=clock,
        )
    except Exception:  # pragma: no cover - defensive, mirrors the A5 note writer
        logging.getLogger(__name__).warning(
            "failed to record grading clarification for attempt %s",
            application.result.attempt_id,
            exc_info=True,
        )
        return None


def _auto_resolve_clean_error_events(
    vault: LoadedVault,
    repository: Repository,
    application: AttemptApplication,
    *,
    clock: Clock | None = None,
) -> list[str]:
    """Close the loop on stale error events (config ``[misconceptions]``).

    A "clean" attempt is one whose graded correctness is at or above
    ``auto_resolve_min_correctness``, that wrote no error events (equivalently
    ``error_type IS NULL`` on the attempt row), and that is not a
    ``dont_know``/``skip`` self-diagnosis. When an attempt completes clean, any
    active error event on the same learning object that has accumulated
    ``auto_resolve_clean_attempts`` clean attempts since its ``created_at`` is
    resolved. The hook runs inside ``apply_attempt`` after persistence, so live
    recording and deterministic replay (which resets error events to active and
    re-applies attempts in ``created_at`` order) reproduce the same resolutions.
    """

    config = vault.config.misconceptions
    if config.auto_resolve_clean_attempts <= 0:
        return []
    record = application.attempt_record
    if record.get("attempt_type") in ("dont_know", "skip"):
        return []
    if application.error_events:
        return []
    if application.grade_held:
        # held-grade-evidence: a held grade (no error event, maybe a high
        # provisional score) is not a clean attempt.
        return []
    if float(record.get("correctness") or 0.0) < config.auto_resolve_min_correctness:
        return []
    resolved: list[str] = []
    active = repository.active_errors_by_learning_object(record["learning_object_id"])
    held: frozenset[str] = frozenset()
    if active:
        # ... nor is an earlier one: THE held predicate, over the candidates.
        from learnloop.held_grades import held_attempt_ids

        held = held_attempt_ids(repository, repository.clean_attempt_ids_since(
            record["learning_object_id"],
            since=min(event.created_at for event in active),
            until=record["created_at"],
            min_correctness=config.auto_resolve_min_correctness,
        ))
    for event in active:
        clean_count = repository.count_clean_attempts_since(
            record["learning_object_id"],
            since=event.created_at,
            until=record["created_at"],
            min_correctness=config.auto_resolve_min_correctness,
            exclude_attempt_ids=held,
        )
        if clean_count >= config.auto_resolve_clean_attempts and repository.resolve_error_event(
            event.id, clock=clock
        ):
            resolved.append(event.id)
    return resolved


def load_attempt_prior_state(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_id: str,
    practice_item_id: str,
    facets: Iterable[str],
    now_iso: str,
) -> AttemptPriorState:
    """Read the prior-state snapshot used by one attempt computation."""

    facet_ids = list(dict.fromkeys(facets))
    mastery = repository.mastery_state(learning_object_id) or initial_mastery_state_for_learning_object(
        vault,
        repository,
        learning_object_id,
        now_iso,
    )
    # KM2b: the belief priors this attempt reads come from the canonical shared
    # state under mvp-0.7 (folded through aliases + merges) and from the legacy
    # per-LO table under mvp-0.6 (byte-identical). One reader build per attempt.
    if is_canonical_state_vault(vault):
        reader = CanonicalFacetStateReader(vault, repository)

        def _recall(facet: str, scope: str | None = None) -> FacetRecallState | None:
            return reader.state_for_facet(learning_object_id, facet, scope)

    else:

        def _recall(facet: str, scope: str | None = None) -> FacetRecallState | None:
            return repository.facet_recall_state(learning_object_id, facet, scope)

    # held-grade-evidence: the recent attempts keep every exposure, and each
    # one the held predicate holds carries ``HELD_ROW_KEY``, so the readers of
    # their scores (item quality, error severity, familiarity) never read a
    # held grade as a failure or a success. One ledger query for both lists.
    from learnloop.outcome_contract import HELD_ROW_KEY
    from learnloop.held_grades import held_attempt_ids

    recent_lo_attempts = repository.list_recent_attempts_by_learning_object(
        learning_object_id,
        limit=max(vault.config.recall_coverage.familiarity_recent_attempt_window, 20),
    )
    recent_item_attempts = repository.list_recent_attempts_by_practice_item(practice_item_id, limit=5)
    held = held_attempt_ids(
        repository, [row.get("id") for row in (*recent_lo_attempts, *recent_item_attempts)]
    )
    if held:
        recent_lo_attempts = [
            {**row, HELD_ROW_KEY: True} if row.get("id") in held else row for row in recent_lo_attempts
        ]
        recent_item_attempts = [
            {**row, HELD_ROW_KEY: True} if row.get("id") in held else row for row in recent_item_attempts
        ]
    return AttemptPriorState(
        mastery=mastery,
        active_errors=repository.active_errors_by_learning_object(learning_object_id),
        practice_item_state=repository.practice_item_state(practice_item_id),
        practice_item_quality_state=repository.practice_item_quality_state(practice_item_id),
        recent_learning_object_attempts=recent_lo_attempts,
        recent_practice_item_attempts=recent_item_attempts,
        aggregate_facet_recall={facet: _recall(facet) for facet in facet_ids},
        item_facet_recall={
            facet: _recall(facet, practice_item_id) for facet in facet_ids
        },
        facet_uncertainty={
            facet: repository.facet_uncertainty_state(learning_object_id, facet)
            for facet in facet_ids
        },
        item_parameter_state=(
            repository.item_parameter_state(practice_item_id)
            if vault.config.mastery.irt.eb_difficulty_enabled
            else None
        ),
    )


def _attempt_reference_status(vault: LoadedVault, repository: Repository, item: PracticeItem,
                              draft: AttemptDraft, *, replay: bool) -> str:
    """The attempt-time answer-key signal (canonical sources S1, C3).

    Read from the served item's effective key status at or above the gate's
    tag; ``not_applicable`` below it, for items that are not exercise imports,
    and on replay unless the stored row says otherwise.
    """

    if draft.reference_status is not None:
        return draft.reference_status
    if replay or vault.config.algorithms.algorithm_version not in SOURCE_REFERENCE_GATE_VERSIONS:
        return "not_applicable"
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return reference_status_for_item(connection, item)


def _compute_resolved_grade_application(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    *,
    attempt_id: str,
    grade: ResolvedGrade,
    clock: Clock | None = None,
    error_event_ids_override: list[str] | None = None,
    prior_state: AttemptPriorState | None = None,
    replay: bool = False,
    grading_source: str = "self",
    agent_run_id: str | None = None,
    fallback_reason: str | None = None,
    grader_identity: tuple[str, str] | None = None,
    unassessed_criterion_ids: Iterable[str] = (),
    grade_held_for_review: bool = False,
) -> AttemptApplication:
    item, learning_object, rubric, draft = _resolve_attempt_target(
        vault, repository, draft, replay=replay, clock=clock
    )
    observed_at = (clock or SystemClock()).now().astimezone(UTC)
    now_iso = utc_now_iso(clock)
    correctness = grade.rubric_score / max(rubric.max_points, 1)
    subjects = vault.subjects_for_item(item)
    subject = subjects[0] if subjects else None
    # PF-c (owner decision 2026-10-12): a criterion the valid-alternative gate
    # recorded unverified is UNASSESSED - neither credit nor failure. The grade
    # already excludes it (``assessed_rubric_score``); here it leaves the
    # criterion vector, so it certifies no facet mass and has no facet outcome
    # (as an ungraded teach-back criterion). With NO criterion assessed the
    # verified answer still schedules as correct, but the attempt is no
    # evidence at all: no facet mass and no learning-object mastery update.
    # Empty for every joint, self and deterministic grade (bit-for-bit).
    rubric_ids = {criterion.id for criterion in rubric.criteria}
    unassessed = frozenset(str(value) for value in unassessed_criterion_ids) & rubric_ids
    criterion_points = grade.criterion_points
    if unassessed:
        criterion_points = {
            cid: points for cid, points in grade.criterion_points.items() if cid not in unassessed
        }
    # No assessed criterion left in the vector (the learner field's test too):
    # never the legacy "no criterion information" reading of an empty vector.
    nothing_assessed = bool(unassessed) and not criterion_points
    # mvp-0.17 (re-review F9): nothing assessed AND nothing validated the
    # answer. The grade is the grader's provisional one, held for review: no
    # FSRS review and no prediction error until a regrade or an adjudication
    # assesses a criterion (which ends ``nothing_assessed`` and the hold).
    # held-grade-evidence: THE predicate, in flight (the ledger evaluates the
    # same one); nor is it any other evidence: no error event, no item-quality
    # move, no clean attempt, no probe observation, no certification label.
    from learnloop.outcome_contract import grade_is_held

    held = grade_is_held(record_held=grade_held_for_review, anything_assessed=bool(criterion_points))
    # Which facets the unassessed criteria alone account for comes from the
    # rubric's observation contract (the projection's map), never the item's
    # lexical inference: on most items that maps nothing and the attempt's
    # outcome would reach every facet, the unassessed one included (review F1).
    pfc_facet_weights = (
        target_criterion_facet_weights(item, rubric, resolve=vault.canonical_facet_id)
        if unassessed
        else None
    )
    coverage = resolve_coverage(
        item,
        rubric,
        attempt_type=draft.attempt_type,
        hints_used=draft.hints_used,
        learner_answer_md=draft.learner_answer_md,
        evidence=vault.config.evidence,
        declared_stuck=draft.declared_stuck,
    )
    # Asked-criteria evidence scaling: ungraded criteria certify no facet mass
    # (teach_back partial grading) and transfer-tier criterion evidence carries
    # the config multiplier. Both are symmetric mass effects, config-read at
    # apply time, so replay reproduces them. No-op for grades covering every
    # criterion of a core-only rubric (all existing modes).
    if draft.attempt_type != "dont_know":
        coverage = scale_coverage_for_graded_criteria(
            coverage,
            item,
            rubric,
            criterion_points=criterion_points,
            transfer_evidence_multiplier=vault.config.teach_back.transfer_evidence_multiplier,
            criterion_facet_weights=pfc_facet_weights,
        )
    if nothing_assessed:
        # An empty criterion vector reads as "no criterion information" above
        # (legacy full mass); here it means no criterion was assessed.
        coverage = replace(
            coverage,
            effective_coverage=0.0,
            covered_facets={},
            trace={**coverage.trace, "covered_facets": {}, "effective_coverage": 0.0},
        )
    if prior_state is None:
        prior_state = load_attempt_prior_state(
            vault,
            repository,
            learning_object_id=learning_object.id,
            practice_item_id=item.id,
            facets=[*item.evidence_facets, *coverage.covered_facets],
            now_iso=now_iso,
        )
    prior_mastery = prior_state.mastery
    grade_attributions = _canonicalized_grade_attributions(vault, grade.error_attributions)
    (
        grade_attributions,
        repair_suggestions,
        write_barrier_events,
    ) = enforce_passed_target_firewall(
        item,
        rubric,
        criterion_points=criterion_points,
        error_attributions=grade_attributions,
        repair_suggestions=grade.repair_suggestions,
        vault=vault,
    )
    attribution_audit_events = [
        *grade.attribution_audit_events,
        *write_barrier_events,
    ]
    if held:
        # held-grade-evidence: a held grade asserts no learner error. Its
        # attributions stay on the blind record (the grader's reading, shown
        # with the grade) but write no error event and no error type: an
        # active error would steer the scheduler, the probes and the
        # severity of later answers on a grade nothing validated.
        grade_attributions = []
    primary_error_type = _primary_error_type(grade_attributions)
    item_a, item_b = resolve_item_irt_params(
        item, learning_object, vault.config.mastery, prior_state.item_parameter_state
    )
    if draft.primed:
        # Source just re-read: the item is effectively easier. Shifting b (rather
        # than dampening the observation weight) keeps the evidence asymmetric —
        # a primed success barely moves mu, a primed failure moves it strongly.
        # Prediction and surprise read the same shifted b, staying consistent.
        item_b -= vault.config.mastery.irt.priming_b_offset
    expected_correctness, prediction_trace = predicted_correctness_from_prior(
        prior_state.aggregate_facet_recall,
        item,
        prior_mastery=prior_mastery,
        item_a=item_a,
        item_b=item_b,
        config=vault.config,
    )
    facet_outcomes = derive_facet_outcomes(
        item,
        rubric,
        criterion_points=criterion_points,
        covered_facets=coverage.covered_facets,
        correctness=correctness,
        attempt_type=draft.attempt_type,
        error_attributions=grade_attributions,
        criterion_facet_weights=pfc_facet_weights,
    )
    # Prediction lane, mean-preserving (P1 revision): the mastery EKF keeps the
    # RAW rubric fraction as its observation y and consumes the calibrated grade
    # channel only through Var[s(Z)|emission] added to measurement noise. Using
    # the channel mean as y (y = E[s(Z)|emission]) would shrink every
    # observation toward the channel prior mean, capping a perfect score near
    # 0.85 under the heuristic prior and moving mastery AGAINST the observed
    # direction on easy items (predicted p above the cap), so channel doubt
    # widens R and never biases y. Certification is untouched: canonical
    # projection consumes the channel through build_effective_observation.
    # Deterministic and self grades are not channel-interpreted, so they keep
    # the raw score and confidence with no extra noise. Every P0-projection
    # version (mvp-0.8 and its successors) takes this lane.
    grader_confidence_source = grade.grader_confidence
    interpretation_variance = 0.0
    if (
        vault.config.algorithms.algorithm_version in P0_PROJECTION_VERSIONS
        and draft.attempt_type != "dont_know"
        and grading_source in ("ai", "codex")
    ):
        try:
            from learnloop.attempts.grade_resolution import response_soft_score

            _channel_mean, interpretation_variance = response_soft_score(
                vault,
                repository,
                item=item,
                grading_source="ai",
                rubric_score=grade.rubric_score,
                max_points=rubric.max_points,
                grader_confidence=grade.grader_confidence,
                has_fatal=bool(grade.error_attributions),
                response_text=draft.learner_answer_md,
                domain=learning_object.id,
                grading_prompt_version=grader_identity[0] if grader_identity else None,
                grader_output_schema_version=grader_identity[1] if grader_identity else None,
                clock=clock,
            )
        except Exception:  # noqa: BLE001 - fail-safe reliability source (§7.3)
            interpretation_variance = 0.0
    reliability = resolve_reliability(
        item,
        attempt_type=draft.attempt_type,
        hints_used=draft.hints_used,
        grader_confidence=grader_confidence_source,
        evidence=vault.config.evidence,
    )
    familiarity = familiarity_discount_from_attempts(
        prior_state.recent_learning_object_attempts,
        item,
        covered_facets=coverage.covered_facets,
        config=vault.config,
        exclude_attempt_id=attempt_id,
    )
    lo_coverage, lo_coverage_trace = lo_relative_coverage(
        vault,
        repository,
        learning_object_id=learning_object.id,
        normalized_facet_weights=coverage.normalized_facet_weights,
        effective_item_coverage=coverage.effective_coverage,
    )
    prior_quality = prior_state.practice_item_quality_state
    prior_bad_item_suspicion = prior_quality.bad_item_suspicion if prior_quality is not None else 0.0
    severity_traces: dict[str, dict[str, object]] = {}
    resolved_attributions: list[GradeAttribution] = []
    for attribution in grade_attributions:
        severity, trace = event_local_severity_from_attempts(
            vault,
            prior_state.recent_learning_object_attempts,
            item,
            error_type=attribution.error_type,
            attempt_type=draft.attempt_type,
            hints_used=draft.hints_used,
            correctness=correctness,
            expected_correctness=expected_correctness,
            effective_coverage=coverage.effective_coverage,
            covered_facets=coverage.covered_facets,
            facet_outcomes=facet_outcomes,
            prior_bad_item_suspicion=prior_bad_item_suspicion,
            base_severity=attribution.severity,
            exclude_attempt_id=attempt_id,
        )
        severity_traces[attribution.error_type] = trace
        resolved_attributions.append(replace(attribution, severity=severity))
    primary_error_type = _primary_error_type(resolved_attributions)
    max_event_severity = max((attribution.severity for attribution in resolved_attributions), default=0.0)
    facet_recall_updates = build_facet_recall_updates_from_prior(
        prior_state.facet_recall_by_scope(coverage.covered_facets, item.id),
        learning_object_id=learning_object.id,
        practice_item_id=item.id,
        covered_facets=coverage.covered_facets,
        facet_outcomes=facet_outcomes,
        independent_evidence_discount=familiarity.independent_evidence_discount,
        attempt_type=draft.attempt_type,
        error_event_written=bool(resolved_attributions),
        algorithm_version=vault.config.algorithms.algorithm_version,
        now_iso=now_iso,
    )
    post_aggregate_facet_recall: dict[str, FacetRecallState | dict[str, Any] | None] = dict(
        prior_state.aggregate_facet_recall
    )
    for state in facet_recall_updates:
        if state.get("practice_item_id") is None:
            post_aggregate_facet_recall[str(state["facet_id"])] = state
    breadth_fraction, breadth_trace = covered_required_fraction(
        vault,
        repository,
        learning_object_id=learning_object.id,
        aggregate_facet_recall=post_aggregate_facet_recall,
    )
    error_impact = resolve_error_impact(
        vault.config,
        error_type=primary_error_type,
        max_event_severity=max_event_severity,
        effective_coverage=lo_coverage,
        observation_reliability=reliability.observation_reliability,
        independent_evidence_discount=familiarity.independent_evidence_discount,
    )
    mastery_observation = MasteryObservation(
        rubric_score=grade.rubric_score,
        max_points=rubric.max_points,
        evidence_coverage=coverage.effective_coverage,
        hint_dampening=1.0,
        grader_confidence=1.0,
        attempt_type=draft.attempt_type,
        observed_at=observed_at,
        item_coverage=coverage.item_coverage,
        effective_coverage=coverage.effective_coverage,
        covered_facets=coverage.covered_facets,
        facet_outcomes=facet_outcomes,
        independent_evidence_discount=familiarity.independent_evidence_discount,
        attempt_modifiers=coverage.trace["coverage_modifiers"],
        coverage_trace=coverage.trace,
        reliability_trace=reliability.trace,
        familiarity_trace=familiarity.trace,
        error_sharpening=error_impact.error_sharpening,
        observation_reliability=reliability.observation_reliability,
        observation_weight_override=error_impact.observation_weight,
        attempt_evidence_mass=attempt_evidence_mass(draft.attempt_type, vault.config.evidence),
        primed=draft.primed,
        soft_score_override=None,
        interpretation_variance=interpretation_variance,
    )
    # IRT (a, b) resolved once from static authored/LLM fields and shared by the
    # mastery EKF and the probability-space surprise (spec §4.3 / §8).
    mastery_trace: MasteryObservationTrace | None
    mastery_variance_floor: float | None
    if nothing_assessed:
        # PF-c: no criterion was assessed, so the learning object's belief
        # takes no evidence from this attempt (the projection and the learner
        # field record none either). Scheduling still reads the grade.
        posterior_mastery, mastery_trace, mastery_variance_floor = prior_mastery, None, None
    else:
        posterior_mastery, mastery_trace = update_mastery_traced(
            prior_mastery,
            mastery_observation,
            vault.config.mastery,
            vault.config.algorithms.algorithm_version,
            item_a=item_a,
            item_b=item_b,
            item_id=item.id,
        )
        posterior_mastery, mastery_variance_floor = apply_mastery_variance_floor(
            posterior_mastery,
            vault.config,
            covered_fraction=breadth_fraction,
        )
    # Empirical-Bayes per-item difficulty: alternating conditional update on b
    # using the learner's fresh posterior mean (dark unless eb_difficulty_enabled).
    next_item_parameters: ItemParameterState | None = None
    # Primed outcomes are conditioned on the source being fresh in working
    # memory — they must not move the fitted *cold* difficulty. An attempt
    # with nothing assessed (PF-c) observed nothing about it either.
    if vault.config.mastery.irt.eb_difficulty_enabled and not draft.primed and not nothing_assessed:
        _authored_a, authored_b = item_irt_params(item, learning_object, vault.config.mastery)
        next_item_parameters = update_item_difficulty(
            prior_state.item_parameter_state,
            practice_item_id=item.id,
            authored_b=authored_b,
            item_a=item_a,
            learner_mu_posterior=posterior_mastery.logit_mean,
            observation=mastery_observation,
            config=vault.config.mastery,
            algorithm_version=vault.config.algorithms.algorithm_version,
            updated_at=now_iso,
        )
    surprise = compute_surprise(
        prior=prior_mastery,
        posterior=posterior_mastery,
        observation=mastery_observation,
        observed_error_type=primary_error_type,
        prior_active_errors=prior_state.active_errors,
        config=vault.config,
        item_a=item_a,
        item_b=item_b,
    )
    if held:
        # A held grade rests on mark-downs nobody located (P1): it is no
        # prediction error, so neither the follow-up gate nor the re-probe
        # trigger reads it as one, and it stretches no interval.
        surprise = replace(surprise, surprise_direction="none", fsrs_interval_factor=1.0)

    previous_state = prior_state.practice_item_state
    fsrs_rating = fsrs_rating_for_attempt(item, grade.rubric_score, rubric.max_points, draft.hints_used)
    fsrs_weights = resolve_fsrs_weights(repository)
    fsrs_weights_fitted = fsrs_weights is not FSRS6_DEFAULT_WEIGHTS
    elapsed_days = _elapsed_days(previous_state, observed_at)
    previous_memory = _memory_state(previous_state)
    # P1 step 5/9 (§3.10, §7.4): purpose-specific administration adapter seam. The
    # purpose-adapter path is the LIVE scheduling authority for mvp-0.8 vaults (the
    # step-9 cutover); legacy vaults keep the purpose-blind path byte-identical.
    #
    # The REAL evidence eligibility of the practice observation is threaded into the
    # decision (§3.8): a practice administration is scheduling-eligible unless its
    # evidence is ineligible (feedback revealed before response, quarantined /
    # out-of-band). For an eligible practice attempt -- the common case that reaches
    # apply_attempt -- the review still applies, so both paths are byte-identical; on a
    # LIVE mvp-0.8 vault an INELIGIBLE observation now correctly leaves card scheduling
    # state EXACTLY as it was (no memory rewrite, no due-date recompute). A legacy vault
    # bypasses the decision entirely (unconditional write, characterization-pinned).
    from learnloop.substrate.activities import evidence_eligibility_for
    from learnloop.substrate.administration_adapters import hot_path_applies_practice_review

    evidence_eligibility, _eligibility_reason = evidence_eligibility_for(
        purpose="practice", feedback_condition=None
    )
    observation_eligible = evidence_eligibility == "practice"
    # P2 §4.4: the diagnostic/repair FSRS skip is the causal activity policy's
    # decision, not a local hardcode. See
    # ``learnloop.diagnosis.causal_activity_policy``.
    causal_activity = classify_attempt_activity(
        attempt_type=draft.attempt_type,
        primed=draft.primed,
        hints_used=draft.hints_used,
    )
    # A grade held for review (re-review F9) leaves the item's scheduling
    # state exactly as it was, as an ineligible observation does (§3.8),
    # until a regrade or an adjudication assesses a criterion.
    if not held and causal_activity.eligible_for_fsrs and hot_path_applies_practice_review(
        attempt_type=draft.attempt_type,
        eligible=observation_eligible,
        algorithm_version=vault.config.algorithms.algorithm_version,
    ):
        next_memory = apply_review(previous_memory, fsrs_rating, elapsed_days, fsrs_weights)
        interval_days = (
            interval_for_retention(next_memory.stability, weights=fsrs_weights)
            * surprise.fsrs_interval_factor
        )
        due_at = (observed_at + timedelta(days=interval_days)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    else:
        # LIVE mvp-0.8 + ineligible observation: scheduling state is left EXACTLY as it
        # was (§3.8). A first-ever ineligible observation creates NO memory state
        # (never apply_review(None, ...)); a retained prior memory keeps its stored
        # interval / due_at unchanged (never a rewritten due-date).
        next_memory = previous_memory
        interval_days = None
        due_at = previous_state.due_at if previous_state is not None else None

    attempt_record = {
        "id": attempt_id,
        "practice_item_id": item.id,
        "learning_object_id": learning_object.id,
        "subject": subject,
        "concept": learning_object.concept,
        "practice_mode": item.practice_mode,
        "attempt_type": draft.attempt_type,
        "learner_answer_md": draft.learner_answer_md,
        "evidence_facets": item.evidence_facets,
        "evidence_weights": item.evidence_weights,
        "rubric_score": grade.rubric_score,
        "correctness": correctness,
        "confidence": grade.confidence,
        "latency_seconds": draft.latency_seconds,
        "hints_used": draft.hints_used,
        "error_type": primary_error_type,
        "grader_confidence": grade.grader_confidence,
        "manual_review": grade.manual_review_reason is not None,
        "manual_review_reason": grade.manual_review_reason,
        "created_at": now_iso,
        "updated_at": now_iso,
        "session_id": draft.session_id,
        "primed": draft.primed,
        "probe_presentation_id": draft.probe_presentation_id,
        "answer_confidence": draft.answer_confidence,
        "submission_id": draft.submission_id,
        "scheduler_candidate_id": draft.scheduler_candidate_id,
        "entry_surface": draft.entry_surface,
        "evidence_origin": draft.evidence_origin,
        "declared_dont_know": draft.declared_dont_know,
        "declared_stuck": draft.declared_stuck,
        "reference_status": _attempt_reference_status(vault, repository, item, draft, replay=replay),
    }
    error_event_ids = [
        error_event_ids_override[index]
        if error_event_ids_override is not None and index < len(error_event_ids_override)
        else new_ulid()
        for index, _attribution in enumerate(resolved_attributions)
    ]
    error_events = []
    for event_id, base_attribution, attribution in zip(error_event_ids, grade_attributions, resolved_attributions, strict=True):
        error_events.append(
            {
                "id": event_id,
                "attempt_id": attempt_id,
                "learning_object_id": learning_object.id,
                "error_type": attribution.error_type,
                "severity": attribution.severity,
                "is_misconception": attribution.is_misconception,
                "misconception_statement": attribution.misconception_statement,
                "misconception_consistent_answer": attribution.misconception_consistent_answer,
                "misconception_id": attribution.misconception_id,
                "repair_plan": _error_event_repair_plan(vault, base_attribution),
                "status": "active",
                "created_at": now_iso,
                "updated_at": now_iso,
            }
        )
    facet_evidence_rows: Iterable[Any] = grade.evidence_rows
    if not grade.evidence_rows:
        facet_evidence_rows = repository.fetch_grading_evidence(attempt_id)
    if unassessed:
        facet_evidence_rows = [
            row
            for row in facet_evidence_rows
            if (row.get("criterion_id") if isinstance(row, Mapping) else getattr(row, "criterion_id", None))
            not in unassessed
        ]
    facet_uncertainty_updates, facet_uncertainty_trace = build_facet_uncertainty_updates(
        vault,
        item=item,
        rubric=rubric,
        learning_object_id=learning_object.id,
        attempt_id=attempt_id,
        facet_outcomes=facet_outcomes,
        normalized_facet_weights=coverage.normalized_facet_weights,
        evidence_rows=facet_evidence_rows,
        error_attributions=resolved_attributions,
        prior_uncertainties=prior_state.facet_uncertainty,
        prior_facet_recall=prior_state.aggregate_facet_recall,
        observed_error_type=primary_error_type,
        algorithm_version=vault.config.algorithms.algorithm_version,
        now_iso=now_iso,
    )
    from learnloop.outcome_contract import HELD_ROW_KEY

    recent_item_failures = sum(
        1
        for attempt in prior_state.recent_practice_item_attempts
        if attempt.get("id") != attempt_id
        # held-grade-evidence: a held grade is neither failure nor success.
        if not attempt.get(HELD_ROW_KEY)
        if attempt.get("attempt_type") == "dont_know" or float(attempt.get("correctness") or 0.0) <= 0.40
    )
    # held-grade-evidence (F10): a held grade is no evidence about the item
    # either; its quality state stays exactly as it was (no row is written).
    quality_state: dict[str, Any] | None = None
    if not held:
        quality_state = build_quality_state_update_from_prior(
            prior_state.practice_item_quality_state,
            recent_failures=recent_item_failures,
            item_id=item.id,
            prior_mastery=prior_mastery,
            correctness=correctness,
            grader_confidence=grade.grader_confidence,
            now_iso=now_iso,
            algorithm_version=vault.config.algorithms.algorithm_version,
            assessment_side_error=any(
                (map_legacy_error_type(attribution.error_type) or attribution.error_type)
                in ASSESSMENT_SIDE_ERROR_TYPES
                for attribution in resolved_attributions
            ),
        )
    ability_transition = estimate_ability_transition(
        item,
        correctness=correctness,
        attempt_type=draft.attempt_type,
        target_facets=list(coverage.covered_facets),
        error_event_written=bool(error_events),
    )
    ability_transition_event = {
        "attempt_id": attempt_id,
        "learning_object_id": learning_object.id,
        "practice_item_id": item.id,
        "transition_type": ability_transition["transition_type"],
        "expected_skill_gain": ability_transition["expected_skill_gain"],
        "target_facets": ability_transition["target_facets"],
        "reason": ability_transition["reason"],
        "applied_to_belief_counts": ability_transition["applied_to_belief_counts"],
        "applied_to_mastery": ability_transition["applied_to_mastery"],
        "applied_to_facet_recall": ability_transition["applied_to_facet_recall"],
        "process_noise": None,
        "algorithm_version": vault.config.algorithms.algorithm_version,
        "created_at": now_iso,
    }
    debug_payload = {
        "item_coverage": coverage.item_coverage,
        "effective_coverage": coverage.effective_coverage,
        "lo_relative_coverage": lo_coverage,
        "lo_relative_coverage_trace": lo_coverage_trace,
        "covered_required_fraction": breadth_fraction,
        "covered_required_fraction_trace": breadth_trace,
        "mastery_variance_floor": mastery_variance_floor,
        "coverage_trace": coverage.trace,
        "reliability_trace": reliability.trace,
        "familiarity_trace": familiarity.trace,
        "error_impact_trace": error_impact.trace,
        "observation_weight": error_impact.observation_weight,
        "covered_facets": coverage.covered_facets,
        "facet_outcomes": facet_outcomes,
        # PF-c: present only when the grade left criteria unassessed.
        **({"unassessed_criteria": sorted(unassessed)} if unassessed else {}),
        "causal_attribution": {
            # A blind grade names its own grader (its calibration identity),
            # never the joint prompt it did not run.
            "prompt_version": GRADING_PROMPT_VERSION if grader_identity is None else grader_identity[0],
            "diagnosis_present": bool((grade.diagnosis_md or "").strip()),
            "attribution_count": len(grade_attributions),
            "resolution_counts": {
                status: sum(
                    1
                    for attribution in grade_attributions
                    if (
                        attribution.resolution_status
                        or (
                            "resolved"
                            if attribution.target_evidence_families
                            or attribution.target_criterion_ids
                            or (
                                attribution.target_ref is not None
                                and attribution.target_ref.get("kind") != "none"
                            )
                            else "unresolved"
                        )
                    )
                    == status
                )
                for status in ("resolved", "unresolved", "abstained")
            },
            "facet_target_fill_count": sum(
                bool(attribution.target_evidence_families)
                for attribution in grade_attributions
            ),
            "criterion_target_fill_count": sum(
                bool(attribution.target_criterion_ids)
                for attribution in grade_attributions
            ),
            "judgment_fill_counts": {
                "cause_scope": sum(attribution.cause_scope is not None for attribution in grade_attributions),
                "operation": sum(attribution.operation is not None for attribution in grade_attributions),
                "first_divergence": sum(
                    attribution.first_divergence is not None for attribution in grade_attributions
                ),
                "facet_contrast": sum(
                    attribution.facet_contrast is not None for attribution in grade_attributions
                ),
                "localization_confidence": sum(
                    attribution.model_reported_localization_confidence is not None
                    for attribution in grade_attributions
                ),
                "causal_confidence": sum(
                    attribution.model_reported_causal_confidence is not None
                    for attribution in grade_attributions
                ),
            },
            "firewall_events": attribution_audit_events,
        },
        # Meas §3.A5: the profile channel's per-attempt tally, in the same debug
        # payload `causal_attribution_audit_report` already reads, so the
        # two-tailed fill telemetry covers it without a second traversal of the
        # attempt ledger. Written for EVERY attempt, including the
        # `no_profiles_offered` arm — a fill rate whose denominator excluded the
        # unprofiled items would measure authoring coverage instead of the
        # diagnostician's willingness to reject.
        "discrimination_profile": _discrimination_profile_telemetry(
            getattr(grade, "discrimination_profile_match", None)
        ),
        # Meas §3.A3: the resolved plant outcomes. Absent (not empty) on every
        # item that is not an error hunt, so the A3 population is countable.
        **(
            {"error_hunt": dict(getattr(grade, "error_hunt", None) or {})}
            if getattr(grade, "error_hunt", None)
            else {}
        ),
        "max_error_severity": max_event_severity,
        "primary_error_type": primary_error_type,
        "prior_bad_item_suspicion": prior_bad_item_suspicion,
        "bad_item_suspicion": (
            quality_state["bad_item_suspicion"] if quality_state is not None else prior_bad_item_suspicion
        ),
        "severity_traces": severity_traces,
        "predicted_correctness": expected_correctness,
        "prediction_trace": prediction_trace,
        "facet_recall_updates": facet_recall_updates,
        "facet_uncertainty_updates": facet_uncertainty_updates,
        "facet_uncertainty_trace": facet_uncertainty_trace,
        "ability_transition": ability_transition,
        "primed": draft.primed,
        # mvp-0.17 (re-review F9): a grade held for review applied no review.
        **({"grade_held_for_review": True} if held else {}),
        # Non-None only when the ledger forced it: the summed reveal amount on
        # this item since its last attempt. This is the audit trail for "why is
        # an attempt the learner submitted as unassisted recorded as primed?".
        "auto_primed_reveal_total": draft.auto_primed_reveal_total,
        "priming_b_offset": vault.config.mastery.irt.priming_b_offset if draft.primed else None,
        "fsrs_weights_fitted": fsrs_weights_fitted,
        "algorithm_version": vault.config.algorithms.algorithm_version,
        "created_at": now_iso,
    }
    practice_state = PracticeItemState(
        practice_item_id=item.id,
        difficulty=next_memory.difficulty if next_memory is not None else None,
        stability=next_memory.stability if next_memory is not None else None,
        retrievability=next_memory.retrievability if next_memory is not None else None,
        due_at=due_at,
        # A diagnostic probe is a single-use surface: it exists to carry exactly
        # one administration, and re-serving it would conflate memorization of
        # the question with understanding. The FSRS skip above already leaves it
        # unscheduled (due_at stays as it was); this closes the pool door too.
        # Living in the shared compute path, the flip replays identically under
        # `rebuild-derived-state`.
        active=item.practice_mode != "diagnostic_probe",
        content_hash=practice_item_hash(item),
        last_attempt_at=now_iso,
        updated_at=now_iso,
    )
    surprise_record = surprise.as_record(attempt_id, vault.config.algorithms.algorithm_version, now_iso)
    mastery_display = display_mastery(posterior_mastery)
    result = AttemptResult(
        attempt_id=attempt_id,
        practice_item_id=item.id,
        learning_object_id=learning_object.id,
        rubric_score=grade.rubric_score,
        correctness=correctness,
        grader_confidence=grade.grader_confidence,
        manual_review_reason=grade.manual_review_reason,
        fsrs_rating=fsrs_rating.name.lower(),
        due_at=due_at,
        mastery_mean=mastery_display.mastery_mean,
        mastery_variance=mastery_display.mastery_variance,
        surprise_direction=surprise.surprise_direction,
        predictive_surprise=surprise.predictive_surprise,
        bayesian_surprise=surprise.bayesian_surprise,
        error_event_ids=error_event_ids,
        grading_source=grading_source,
        fallback_reason=fallback_reason,
        agent_run_id=agent_run_id,
        feedback_md=grade.feedback_md,
        repair_suggestions=list(repair_suggestions),
        fatal_errors=list(grade.fatal_errors),
        mastery_trace=mastery_trace,
        debug_payload=debug_payload,
        exercised_facets=list(getattr(grade, "exercised_facets", None) or []),
        clarification=getattr(grade, "clarification", None),
        discrimination_profile_match=getattr(grade, "discrimination_profile_match", None),
        error_hunt=getattr(grade, "error_hunt", None),
    )
    return AttemptApplication(
        attempt_record=attempt_record,
        evidence_rows=grade.evidence_rows,
        error_events=error_events,
        surprise_record=surprise_record,
        practice_item_state=practice_state,
        mastery_state=posterior_mastery,
        facet_recall_states=facet_recall_updates,
        facet_uncertainty_states=facet_uncertainty_updates,
        quality_state=quality_state,
        ability_transition=ability_transition_event,
        attempt_debug_payload=debug_payload,
        result=result,
        item_parameter_state=next_item_parameters,
        grade_held=held,
    )


def _self_grade_attributions(
    vault: LoadedVault,
    fatal_errors: list[str],
    error_type: str | None,
    error_attributions: list[SelfGradeErrorAttribution] | None = None,
) -> list[GradeAttribution]:
    """Resolve the learner's self-grade selections into the same flat
    ``GradeAttribution`` list Codex grading produces.

    Sources are merged in priority order — rubric fatal errors, the legacy single
    ``error_type``, then the per-criterion picks — and de-duplicated by error type.
    Severity and misconception status come from the vault taxonomy (falling back to
    neutral defaults for unknown types, as elsewhere). When the learner tied an
    error to specific rubric criteria, those ids are recorded in the attribution
    ``evidence`` so the provenance mirrors a Codex grader's per-error note.
    """

    criteria_by_error: dict[str, list[str]] = {}
    order: list[str] = []

    def _register(selected_error_type: str | None, criterion_id: str | None) -> None:
        if not selected_error_type:
            return
        if selected_error_type not in criteria_by_error:
            criteria_by_error[selected_error_type] = []
            order.append(selected_error_type)
        if criterion_id and criterion_id not in criteria_by_error[selected_error_type]:
            criteria_by_error[selected_error_type].append(criterion_id)

    for fatal_error in fatal_errors:
        _register(fatal_error, None)
    _register(error_type, None)
    for attribution in error_attributions or []:
        _register(attribution.error_type, attribution.criterion_id)

    resolved: list[GradeAttribution] = []
    for selected_error_type in order:
        criteria = criteria_by_error[selected_error_type]
        evidence = (
            f"Self-attributed on criterion {', '.join(criteria)}." if criteria else None
        )
        resolved.append(
            GradeAttribution(
                error_type=selected_error_type,
                severity=_error_severity(vault, selected_error_type),
                is_misconception=_is_misconception(vault, selected_error_type),
                evidence=evidence,
                target_criterion_ids=list(criteria),
            )
        )
    return resolved


def _canonicalized_grade_attributions(
    vault: LoadedVault,
    attributions: list[GradeAttribution],
) -> list[GradeAttribution]:
    canonicalized: list[GradeAttribution] = []
    for attribution in attributions:
        target_evidence_families = list(
            dict.fromkeys(vault.canonical_facet_id(facet) for facet in attribution.target_evidence_families)
        )
        target_ref = dict(attribution.target_ref) if attribution.target_ref else None
        if target_ref and target_ref.get("kind") == "facet_capability":
            target_ref["facet_id"] = vault.canonical_facet_id(
                str(target_ref.get("facet_id") or "")
            )
        facet_contrast = (
            dict(attribution.facet_contrast)
            if attribution.facet_contrast
            else None
        )
        if facet_contrast:
            for key in ("target_facet", "confused_with_facet"):
                if facet_contrast.get(key):
                    facet_contrast[key] = vault.canonical_facet_id(
                        str(facet_contrast[key])
                    )
        candidate_causes: list[dict[str, Any]] = []
        for raw in attribution.candidate_causes:
            cause = dict(raw)
            cause_ref = cause.get("target_ref")
            if isinstance(cause_ref, dict) and cause_ref.get("kind") == "facet_capability":
                cause_ref = dict(cause_ref)
                cause_ref["facet_id"] = vault.canonical_facet_id(
                    str(cause_ref.get("facet_id") or "")
                )
                cause["target_ref"] = cause_ref
            candidate_causes.append(cause)
        canonicalized.append(
            replace(
                attribution,
                target_evidence_families=target_evidence_families,
                target_ref=target_ref,
                facet_contrast=facet_contrast,
                candidate_causes=candidate_causes,
            )
        )
    return canonicalized


def _primary_error_type(attributions: list[GradeAttribution]) -> str | None:
    if not attributions:
        return None
    return max(attributions, key=lambda attribution: attribution.severity).error_type


def _attempt_manual_review_reason(existing: str | None, draft: AttemptDraft) -> str | None:
    if existing is not None:
        return existing
    if (
        draft.attempt_type != "dont_know"
        and not draft.declared_stuck
        and not draft.learner_answer_md.strip()
    ):
        return "blank_answer"
    return None


def _dont_know_error_type(vault: LoadedVault, hints_used: int) -> str:
    legacy = SCAFFOLD_FAILURE_ERROR_TYPE if hints_used > 0 else DONT_KNOW_ERROR_TYPE
    # KM4 §10.1: under mvp-0.7 the deterministic attribution speaks the canonical
    # mechanism vocabulary (both recall_failure and scaffold_failure resolve to
    # retrieval_failure). mvp-0.6 keeps the legacy names, so replay is unchanged.
    if is_canonical_state_vault(vault):
        return map_legacy_error_type(legacy)
    return legacy


def _error_event_repair_plan(vault: LoadedVault, attribution: GradeAttribution) -> dict[str, object] | None:
    repair_plan: dict[str, object] = {}
    if attribution.evidence:
        repair_plan["evidence"] = attribution.evidence
    if attribution.target_evidence_families:
        repair_plan["target_evidence_families"] = list(attribution.target_evidence_families)
    if attribution.target_criterion_ids:
        repair_plan["target_criterion_ids"] = list(attribution.target_criterion_ids)
    for key in (
        "resolution_status",
        "abstention_reason",
        "cause_scope",
        "target_ref",
        "operation",
        "first_divergence",
        "facet_contrast",
        "facet_write_blocked",
    ):
        value = getattr(attribution, key)
        if value is not None:
            repair_plan[key] = value
    if attribution.model_reported_localization_confidence is not None:
        repair_plan["model_reported_localization_confidence"] = (
            attribution.model_reported_localization_confidence
        )
    if attribution.model_reported_causal_confidence is not None:
        repair_plan["model_reported_causal_confidence"] = (
            attribution.model_reported_causal_confidence
        )
    if attribution.diagnostic_sample_support is not None:
        repair_plan["diagnostic_sample_support"] = (
            attribution.diagnostic_sample_support
        )
    if attribution.candidate_causes:
        repair_plan["candidate_causes"] = list(attribution.candidate_causes)
    if attribution.postdictive_claims:
        repair_plan["postdictive_claims"] = list(attribution.postdictive_claims)
    if attribution.soft_postdictive_claims:
        repair_plan["soft_postdictive_claims"] = list(attribution.soft_postdictive_claims)
    if abs(attribution.severity - _error_severity(vault, attribution.error_type)) > 1e-9:
        repair_plan["base_severity"] = attribution.severity
    return repair_plan or None


def _replay_error_attributions(
    vault: LoadedVault,
    error_type: str | None,
    *,
    error_events: list[dict[str, Any]] | None = None,
) -> list[GradeAttribution]:
    if error_events:
        attributions: list[GradeAttribution] = []
        for event in error_events:
            event_error_type = event.get("error_type")
            if not event_error_type:
                continue
            repair_plan = event.get("repair_plan")
            if not isinstance(repair_plan, dict):
                repair_plan = {}
            raw_targets = repair_plan.get("target_evidence_families")
            target_evidence_families = raw_targets if isinstance(raw_targets, list) else []
            raw_criteria = repair_plan.get("target_criterion_ids")
            target_criterion_ids = raw_criteria if isinstance(raw_criteria, list) else []
            base_severity = repair_plan.get("base_severity")
            attributions.append(
                GradeAttribution(
                    error_type=str(event_error_type),
                    severity=float(base_severity) if isinstance(base_severity, (int, float)) else _error_severity(vault, str(event_error_type)),
                    evidence=repair_plan.get("evidence") if isinstance(repair_plan.get("evidence"), str) else None,
                    is_misconception=bool(event.get("is_misconception", _is_misconception(vault, str(event_error_type)))),
                    misconception_statement=event.get("misconception_statement"),
                    misconception_consistent_answer=event.get("misconception_consistent_answer"),
                    misconception_id=event.get("misconception_id"),
                    target_evidence_families=[str(facet) for facet in target_evidence_families],
                    target_criterion_ids=[str(criterion_id) for criterion_id in target_criterion_ids],
                    resolution_status=repair_plan.get("resolution_status"),
                    abstention_reason=repair_plan.get("abstention_reason"),
                    cause_scope=repair_plan.get("cause_scope"),
                    target_ref=(
                        dict(repair_plan["target_ref"])
                        if isinstance(repair_plan.get("target_ref"), dict)
                        else None
                    ),
                    operation=repair_plan.get("operation"),
                    first_divergence=(
                        dict(repair_plan["first_divergence"])
                        if isinstance(repair_plan.get("first_divergence"), dict)
                        else None
                    ),
                    model_reported_localization_confidence=repair_plan.get(
                        "model_reported_localization_confidence"
                    ),
                    model_reported_causal_confidence=repair_plan.get(
                        "model_reported_causal_confidence"
                    ),
                    diagnostic_sample_support=repair_plan.get(
                        "diagnostic_sample_support"
                    ),
                    facet_contrast=(
                        dict(repair_plan["facet_contrast"])
                        if isinstance(repair_plan.get("facet_contrast"), dict)
                        else None
                    ),
                    candidate_causes=[
                        dict(value)
                        for value in repair_plan.get("candidate_causes") or []
                        if isinstance(value, dict)
                    ],
                    postdictive_claims=[
                        dict(value)
                        for value in repair_plan.get("postdictive_claims") or []
                        if isinstance(value, dict)
                    ],
                    soft_postdictive_claims=[
                        str(value)
                        for value in repair_plan.get("soft_postdictive_claims") or []
                    ],
                )
            )
        if attributions:
            return attributions
    if not error_type:
        return []
    return [
        GradeAttribution(
            error_type=error_type,
            severity=_error_severity(vault, error_type),
            evidence=None,
            is_misconception=_is_misconception(vault, error_type),
        )
    ]


def resolved_codex_grade(
    validated: ValidatedCodexGrade,
    *,
    agent_run_id: str | None,
    clock: Clock | None,
    manual_review_reason: str | None = None,
) -> ResolvedGrade:
    now_iso = utc_now_iso(clock)
    criterion_points = {evidence.criterion_id: evidence.points_awarded for evidence in validated.criterion_evidence}
    evidence_rows = [
        {
            "id": new_ulid(),
            "criterion_id": evidence.criterion_id,
            "points_awarded": evidence.points_awarded,
            "evidence": evidence.evidence,
            "notes": evidence.notes,
            "agent_run_id": agent_run_id,
            "local_grader_id": None,
            "grader_tier": 3,
            "learner_confidence": evidence.learner_confidence,
            "created_at": now_iso,
        }
        for evidence in validated.criterion_evidence
    ]
    return ResolvedGrade(
        rubric_score=validated.rubric_score,
        criterion_points=criterion_points,
        evidence_rows=evidence_rows,
        error_attributions=[
            GradeAttribution(
                error_type=attribution.error_type,
                severity=attribution.severity,
                evidence=attribution.evidence,
                is_misconception=attribution.is_misconception,
                misconception_statement=attribution.misconception_statement,
                misconception_consistent_answer=attribution.misconception_consistent_answer,
                misconception_id=getattr(attribution, "misconception_id", None),
                target_evidence_families=list(attribution.target_evidence_families or []),
                target_criterion_ids=list(attribution.target_criterion_ids or []),
                resolution_status=attribution.resolution_status,
                abstention_reason=attribution.abstention_reason,
                cause_scope=attribution.cause_scope,
                target_ref=attribution.target_ref,
                operation=attribution.operation,
                first_divergence=attribution.first_divergence,
                model_reported_localization_confidence=(
                    attribution.model_reported_localization_confidence
                ),
                model_reported_causal_confidence=attribution.model_reported_causal_confidence,
                diagnostic_sample_support=attribution.diagnostic_sample_support,
                facet_contrast=attribution.facet_contrast,
                candidate_causes=list(attribution.candidate_causes or []),
                postdictive_claims=list(attribution.postdictive_claims or []),
                soft_postdictive_claims=list(attribution.soft_postdictive_claims or []),
                facet_write_blocked=getattr(attribution, "facet_write_blocked", None),
            )
            for attribution in validated.error_attributions
        ],
        grader_confidence=validated.grader_confidence,
        confidence=None,
        manual_review_reason=manual_review_reason if manual_review_reason is not None else validated.manual_review_reason,
        feedback_md=validated.feedback_md,
        repair_suggestions=list(validated.repair_suggestions or []),
        fatal_errors=list(validated.fatal_errors),
        diagnosis_md=validated.diagnosis_md,
        attribution_audit_events=list(validated.attribution_audit_events or []),
        exercised_facets=[
            {
                "facet_id": observation.facet,
                "evidence": observation.evidence,
                "observation_scope": observation.observation_scope,
                "criterion_id": observation.criterion_id,
            }
            for observation in (validated.exercised_facets or [])
        ],
        clarification=validated.clarification,
        discrimination_profile_match=validated.discrimination_profile_match,
        error_hunt=validated.error_hunt,
    )


def _validated_criterion_points(rubric: Rubric, points: dict[str, float]) -> dict[str, float]:
    criteria = {criterion.id: criterion for criterion in rubric.criteria}
    unknown = sorted(set(points) - set(criteria))
    if unknown:
        raise AttemptValidationError(f"Unknown rubric criteria: {', '.join(unknown)}")
    validated: dict[str, float] = {}
    for criterion in rubric.criteria:
        value = float(points.get(criterion.id, 0.0))
        if value < 0:
            raise AttemptValidationError(f"{criterion.id} points cannot be negative")
        if value > criterion.points:
            raise AttemptValidationError(f"{criterion.id} points exceed max {criterion.points:g}")
        validated[criterion.id] = value
    return validated


def _validated_self_grade_attributions(
    rubric: Rubric, attributions: list[SelfGradeErrorAttribution] | None
) -> list[SelfGradeErrorAttribution]:
    """Validate per-criterion self-grade error picks before they are resolved.

    Only the ``criterion_id`` link is checked (it must name a real rubric
    criterion); the ``error_type`` is intentionally left open — like Codex
    attributions, an unknown type resolves to neutral taxonomy defaults rather
    than failing the attempt.
    """

    if not attributions:
        return []
    known_criteria = {criterion.id for criterion in rubric.criteria}
    for attribution in attributions:
        if not attribution.error_type:
            raise AttemptValidationError("error attribution requires an error_type")
        if attribution.criterion_id is not None and attribution.criterion_id not in known_criteria:
            raise AttemptValidationError(
                f"Unknown rubric criterion {attribution.criterion_id} in error attribution"
            )
    return list(attributions)


def _validate_fatal_errors(rubric: Rubric, fatal_errors: list[str]) -> None:
    known = {fatal_error.id for fatal_error in rubric.fatal_errors}
    unknown = sorted(set(fatal_errors) - known)
    if unknown:
        raise AttemptValidationError(f"Unknown fatal errors: {', '.join(unknown)}")


def calculate_rubric_score(
    rubric: Rubric,
    criterion_points: dict[str, float],
    fatal_errors: list[str],
) -> int:
    score = int(round(sum(criterion_points.values())))
    score = max(0, min(int(rubric.max_points), score))
    fatal_by_id = {fatal_error.id: fatal_error for fatal_error in rubric.fatal_errors}
    for fatal_error_id in fatal_errors:
        score = min(score, fatal_by_id[fatal_error_id].max_grade)
    return max(0, min(score, int(rubric.max_points)))


def assessed_rubric_score(
    rubric: Rubric,
    criterion_points: Mapping[str, float],
    fatal_errors: Iterable[str],
    *,
    unassessed_criterion_ids: Iterable[str],
    answer_validated: bool = True,
) -> int:
    """The grade over the ASSESSED criteria only (PF-c, owner decision 2026-10-12).

    A criterion the valid-alternative gate recorded unverified was never
    exercised by the learner's route, so it is neither credit nor failure: it
    leaves both the numerator and the denominator. The assessed fraction is
    put back on the rubric's own ``0..max_points`` scale, because every reader
    of ``rubric_score`` (correctness, the FSRS rating, the grade channel, the
    feedback) reads it against ``rubric.max_points``; it is rounded like every
    derived score, then the fatal-error caps apply as usual (the teach-back
    asked-criteria score is the same construction). With NO criterion
    assessed, the deterministic final-answer check has verified the answer, so
    the fraction is 1: correct for scheduling (the attempt writes no facet
    evidence; see ``_compute_resolved_grade_application``).

    ``answer_validated = False`` (mvp-0.17, re-review F9): nothing validated
    the answer (no verified final answer, no criterion an independent check
    established), so an empty assessed set is not a verified answer. The
    grade is then the grader's own over every criterion, provisional and held
    for review: it earns no credit it was never shown to deserve, and the
    attempt step applies no review on it (``grade_held_for_review``).

    With nothing unassessed this is :func:`calculate_rubric_score` exactly.
    """

    unassessed = {str(value) for value in unassessed_criterion_ids}
    assessed = [criterion for criterion in rubric.criteria if criterion.id not in unassessed]
    if len(assessed) == len(rubric.criteria) or (not assessed and not answer_validated):
        return calculate_rubric_score(rubric, dict(criterion_points), list(fatal_errors))
    assessed_max = sum(max(float(criterion.points), 0.0) for criterion in assessed)
    fraction = 1.0
    if assessed_max > 0:
        awarded = sum(
            min(max(float(criterion_points.get(criterion.id, 0.0)), 0.0), float(criterion.points))
            for criterion in assessed
        )
        fraction = min(1.0, awarded / assessed_max)
    score = max(0, min(int(rubric.max_points), int(round(fraction * float(rubric.max_points)))))
    fatal_by_id = {fatal_error.id: fatal_error for fatal_error in rubric.fatal_errors}
    for fatal_error_id in fatal_errors:
        score = min(score, fatal_by_id[fatal_error_id].max_grade)
    return max(0, min(score, int(rubric.max_points)))


def _evidence_coverage(item: PracticeItem, criterion_points: dict[str, float]) -> float:
    return evidence_coverage(item, criterion_points)


def _hint_dampening(item: PracticeItem, hints_used: int) -> float:
    value = _hint_policy_value(item.hint_policy.mastery_alpha_dampening_by_hint, hints_used)
    return float(value) if value is not None else 1.0


def fsrs_rating_for_attempt(item: PracticeItem, rubric_score: int, max_points: int, hints_used: int) -> Rating:
    """FSRS rating for a graded attempt: score binning + the item's hint cap.

    Single source of truth shared by the live attempt path and offline fitting
    (review-log reconstruction must reproduce live semantics exactly).
    """

    return _capped_rating(rating_from_score(rubric_score, max_points), item, hints_used)


def _capped_rating(rating: Rating, item: PracticeItem, hints_used: int) -> Rating:
    cap_value = _hint_policy_value(item.hint_policy.fsrs_rating_cap_by_hint, hints_used)
    if cap_value is None:
        return rating
    cap = _rating_from_cap(cap_value)
    return Rating(min(int(rating), int(cap)))


def _hint_policy_value(mapping: dict[int | str, object], hints_used: int) -> object | None:
    if hints_used in mapping:
        return mapping[hints_used]
    string_key = str(hints_used)
    if string_key in mapping:
        return mapping[string_key]
    numeric_keys: list[int] = []
    for key in mapping:
        try:
            numeric_keys.append(int(key))
        except (TypeError, ValueError):
            continue
    eligible = [key for key in numeric_keys if key <= hints_used]
    if not eligible:
        return None
    return mapping.get(max(eligible)) or mapping.get(str(max(eligible)))


def _rating_from_cap(value: object) -> Rating:
    if isinstance(value, int):
        return Rating(max(1, min(4, value)))
    normalized = str(value).strip().lower()
    names = {
        "again": Rating.AGAIN,
        "hard": Rating.HARD,
        "good": Rating.GOOD,
        "easy": Rating.EASY,
        "1": Rating.AGAIN,
        "2": Rating.HARD,
        "3": Rating.GOOD,
        "4": Rating.EASY,
    }
    if normalized not in names:
        raise AttemptValidationError(f"Unknown FSRS rating cap {value!r}")
    return names[normalized]


def _memory_state(state: PracticeItemState | None) -> MemoryState | None:
    if state is None or state.difficulty is None or state.stability is None:
        return None
    retrievability = state.retrievability if state.retrievability is not None else 1.0
    return MemoryState(
        difficulty=state.difficulty,
        stability=state.stability,
        retrievability=retrievability,
    )


def _elapsed_days(state: PracticeItemState | None, observed_at) -> float:
    if state is None:
        return 0.0
    last_attempt_at = parse_utc(state.last_attempt_at)
    if last_attempt_at is None:
        return 0.0
    return max(0.0, (observed_at - last_attempt_at).total_seconds() / 86400)


def _error_severity(vault: LoadedVault, error_type: str) -> float:
    taxonomy = vault.error_types.get(error_type)
    return taxonomy.severity_default if taxonomy is not None else 0.5


def _is_misconception(vault: LoadedVault, error_type: str) -> bool:
    taxonomy = vault.error_types.get(error_type)
    return taxonomy.is_misconception if taxonomy is not None else False
