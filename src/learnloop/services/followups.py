from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from learnloop.clock import Clock, parse_utc
from learnloop.services.misconceptions import normalize_and_resolve_attempt
from learnloop.db.repositories import MisconceptionRecord, Repository
from learnloop.services.facet_diagnostics import candidate_facet_support
from learnloop.services.gate_score import (
    GATE_FEATURE_VERSION,
    GateScoreResult,
    GateSignalValues,
    compute_gate_score,
    resolve_gate_weights,
)
from learnloop.services.predictive_eig import TargetItemModel, build_target_models, predictive_facet_eig
from learnloop.services.probes import (
    _BRIDGE_SENSITIVITY,
    _BRIDGE_SPECIFICITY,
    build_hypothesis_set,
    expected_information_gain,
    facet_expected_information_gain,
    item_registry_discrimination,
    probe_posterior,
    resolve_item_irt,
)
from learnloop.services.question_signal import (
    QuestionSignal,
    question_adjusted_uncertainty_states,
)
from learnloop.services.recall_coverage import familiarity_discount
from learnloop.services.signal_quantiles import ResolvedThreshold, resolve_followup_thresholds
from learnloop.vault.models import LoadedVault, PracticeItem

FOLLOWUP_ACTION = "negative_surprise_followup"
INTERVENTION_ACTION = "intervention_followup"


INTENT_PRIORITY = [
    "guided_reconstruction",
    "repair",
    "probe",
    "transfer",
    "review",
]


@dataclass(frozen=True)
class FollowupDecision:
    triggered: bool
    practice_item_id: str | None
    reason: str
    triggered_actions: list[str]
    suppressed_actions: list[str]
    intent: str | None = None
    need_id: str | None = None
    # Populated only for manual (user-forced) follow-ups: records what the
    # automatic intervention gate *would* have done, so surprise thresholds and
    # the suppression gates can be retuned against real override behaviour.
    gate_diagnostics: dict[str, Any] | None = None


@dataclass(frozen=True)
class InterventionSelection:
    candidate: PracticeItem | None
    dominant_target_facet: str | None
    diagnostic_gate_facets: list[str]
    diagnostic_gate_source: str | None
    diagnostic_focus: dict[str, Any] | None
    open_facets: list[str]
    slate: list[dict[str, Any]]
    # spec §4: misconception routing outcomes. ``misconception_gate_blocked`` is
    # True when an active misconception with no discriminating candidate forced
    # ``no_suitable_item`` even though a facet-eligible paraphrase existed;
    # ``eligible_slate_size`` is the count of gate-passing candidates after the
    # discrimination gate (surfaced as telemetry when < 2).
    misconception_gate_blocked: bool = False
    active_misconception_ids: list[str] | None = None
    eligible_slate_size: int = 0


@dataclass(frozen=True)
class AttemptFacetTargets:
    """Facet evidence roles for follow-up routing.

    ``selection_facets`` scopes candidate selection. ``failed_facets`` is the
    strictly smaller set supported by an actual failed facet outcome and is the
    only set allowed to receive failure evidence in diagnostic focus.
    """

    selection_facets: list[str]
    failed_facets: list[str]


def evaluate_intervention_followup(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    learning_object_id: str,
    practice_item_id: str,
    surprise_direction: str,
    bayesian_surprise: float,
    grader_confidence: float | None,
    error_event_written: bool,
    max_error_severity: float = 0.0,
    repeated_same_item_failure: bool | None = None,
    repeated_same_facet_failure: bool | None = None,
    probe_unfamiliar_probability: float | None = None,
    target_facets: list[str] | None = None,
    failed_facets: list[str] | None = None,
    bad_item_suspicion: float = 0.0,
    available_minutes: int | None = None,
    session_id: str | None = None,
    session_interventions_for_lo: int = 0,
    probe_phase_active: bool = False,
    lo_independent_evidence_mass: float = 0.0,
    lo_raw_attempt_count: int = 0,
    manual_override: bool = False,
    clock: Clock | None = None,
) -> FollowupDecision:
    """Intervention follow-up evaluator from the recall-coverage spec.

    It records all satisfied trigger reasons, queues at most one item, and
    persists an intervention need when a trigger has no suitable item.

    When ``manual_override`` is set (a user manually requesting a diagnostic
    follow-up from the feedback screen) every trigger and suppression gate is
    still *evaluated* — so the decision can report what the automatic policy
    would have done — but none of them are allowed to short-circuit the
    follow-up. The selection logic runs unchanged, queuing the best diagnostic
    item or recording an intervention need when none fits.
    """

    config = vault.config.scheduler.followup
    thresholds = resolve_followup_thresholds(repository, config, exclude_attempt_id=attempt_id)
    target_facets = target_facets or _attempt_target_facets(repository, practice_item_id)
    target_facets = _canonical_target_facets(vault, target_facets)
    failed_facets = target_facets if failed_facets is None else _canonical_target_facets(vault, failed_facets)
    # Raw failure streaks are kept (not just booleans) so score mode can grade
    # the margin; explicit boolean overrides map to synthetic counts at/below
    # the threshold to preserve the legacy parameter contract.
    if repeated_same_item_failure is None:
        item_failure_count = float(current_same_item_failure_streak(repository, practice_item_id))
    else:
        item_failure_count = float(config.tau_repeated_item_failures) if repeated_same_item_failure else 0.0
    if repeated_same_facet_failure is None:
        facet_failure_count = float(
            current_same_facet_failure_streak(repository, learning_object_id, target_facets)
        )
    else:
        facet_failure_count = float(config.tau_repeated_facet_failures) if repeated_same_facet_failure else 0.0
    repeated_same_item_failure = item_failure_count >= config.tau_repeated_item_failures
    repeated_same_facet_failure = facet_failure_count >= config.tau_repeated_facet_failures
    deterministic_dont_know = any(
        attempt.get("practice_item_id") == practice_item_id and attempt.get("attempt_type") == "dont_know"
        for attempt in repository.list_recent_attempts_by_practice_item(practice_item_id, limit=1)
    )
    signals = GateSignalValues(
        surprise_direction=surprise_direction,
        bayesian_surprise=bayesian_surprise,
        max_error_severity=max_error_severity,
        item_failure_count=item_failure_count,
        facet_failure_count=facet_failure_count,
        probe_unfamiliar_probability=probe_unfamiliar_probability,
        error_event_written=error_event_written,
        grader_confidence=grader_confidence,
        deterministic_dont_know=deterministic_dont_know,
    )
    gate_mode = config.gate_mode if config.gate_mode in ("cascade", "score") else "cascade"
    score_result: GateScoreResult | None = None
    if gate_mode == "score":
        weights, bias, weights_provenance = resolve_gate_weights(repository)
        score_result = compute_gate_score(
            signals=signals,
            thresholds=thresholds,
            weights=weights,
            bias=bias,
            gate_score_threshold=config.gate_score_threshold,
            steepness=config.gate_subscore_steepness,
            weights_provenance=weights_provenance,
        )
        triggered_reasons = score_result.triggered_reasons() if score_result.fired else []
        if score_result.fired and not triggered_reasons:
            triggered_reasons = ["gate_score"]
    else:
        triggered_reasons = []
        if surprise_direction == "negative" and bayesian_surprise > thresholds["tau_followup_nats"].value:
            triggered_reasons.append("negative_surprise")
        if max_error_severity >= thresholds["tau_severe_error"].value:
            triggered_reasons.append("severe_error_event")
        if repeated_same_item_failure:
            triggered_reasons.append("repeated_same_item_failure")
        if repeated_same_facet_failure:
            triggered_reasons.append("repeated_same_facet_failure")
        if (
            probe_unfamiliar_probability is not None
            and probe_unfamiliar_probability >= thresholds["tau_unfamiliar_intervention"].value
        ):
            triggered_reasons.append("high_unfamiliar_posterior")

    # Natural reasons (before any manual forcing) and the gates that would have
    # blocked the automatic policy. ``natural_trigger_reasons`` / ``would_suppress``
    # drive the manual-override tuning log; the per-attempt gate diagnostics built
    # below are always persisted so the feedback screen can name the decisive
    # signal even when nothing fired.
    natural_trigger_reasons = list(triggered_reasons)
    would_suppress: list[str] = []

    def _gate(outcome: str, decisive_reason: str, suppress: list[str]) -> dict[str, Any]:
        return _build_gate_diagnostics(
            outcome=outcome,
            decisive_reason=decisive_reason,
            natural_trigger_reasons=natural_trigger_reasons,
            triggered_reasons=triggered_reasons,
            would_suppress=suppress,
            manual_override=manual_override,
            bayesian_surprise=bayesian_surprise,
            surprise_direction=surprise_direction,
            grader_confidence=grader_confidence,
            max_error_severity=max_error_severity,
            probe_unfamiliar_probability=probe_unfamiliar_probability,
            session_interventions_for_lo=session_interventions_for_lo,
            available_minutes=available_minutes,
            target_facets=target_facets,
            config=config,
            thresholds=thresholds,
            gate_mode=gate_mode,
            score_result=score_result,
            item_failure_count=item_failure_count,
            facet_failure_count=facet_failure_count,
        )

    if gate_mode == "score":
        # Soft signals are already inside the score; only the budget gates
        # below (no_time, session cap) remain hard.
        if score_result is not None and not score_result.fired:
            if not manual_override:
                gate = _gate("not_triggered", "gate_score_below_threshold", ["gate_score_below_threshold"])
                repository.update_attempt_surprise_actions(attempt_id, gate_diagnostics=gate)
                return _decision(
                    False, None, "gate_score_below_threshold", [], [], intent=None, gate_diagnostics=gate
                )
            would_suppress.append("gate_score_below_threshold")
    else:
        if not triggered_reasons:
            if not manual_override:
                gate = _gate("not_triggered", "no_trigger", ["no_trigger"])
                repository.update_attempt_surprise_actions(attempt_id, gate_diagnostics=gate)
                return _decision(False, None, "no_trigger", [], [], intent=None, gate_diagnostics=gate)
            would_suppress.append("no_trigger")
        if not error_event_written and "high_unfamiliar_posterior" not in triggered_reasons:
            if not manual_override:
                gate = _gate("suppressed", "no_error_event", ["no_error_event"])
                repository.update_attempt_surprise_actions(attempt_id, gate_diagnostics=gate)
                return _decision(False, None, "no_error_event", [], [], intent=None, gate_diagnostics=gate)
            would_suppress.append("no_error_event")
        if grader_confidence is None or (
            grader_confidence < thresholds["gamma_min"].value and not deterministic_dont_know
        ):
            if not manual_override:
                suppressed = [f"{INTERVENTION_ACTION}:low_grader_confidence"]
                gate = _gate("suppressed", "low_grader_confidence", ["low_grader_confidence"])
                repository.update_attempt_surprise_actions(
                    attempt_id, suppressed_actions=suppressed, gate_diagnostics=gate
                )
                return _decision(False, None, suppressed[0], [], suppressed, intent=None, gate_diagnostics=gate)
            would_suppress.append("low_grader_confidence")
    if available_minutes is not None and available_minutes <= 0:
        if not manual_override:
            suppressed = [f"{INTERVENTION_ACTION}:no_time"]
            gate = _gate("suppressed", "no_time", ["no_time"])
            repository.update_attempt_surprise_actions(attempt_id, suppressed_actions=suppressed, gate_diagnostics=gate)
            return _decision(False, None, suppressed[0], [], suppressed, intent=None, gate_diagnostics=gate)
        would_suppress.append("no_time")
    if session_interventions_for_lo >= config.max_interventions_per_lo_per_session:
        if not manual_override:
            suppressed = [f"{INTERVENTION_ACTION}:session_cap_reached:{learning_object_id}"]
            triggered = [f"{INTERVENTION_ACTION}:{reason}:{practice_item_id}" for reason in triggered_reasons]
            gate = _gate("suppressed", "session_cap_reached", ["session_cap_reached"])
            repository.update_attempt_surprise_actions(
                attempt_id, triggered_actions=triggered, suppressed_actions=suppressed, gate_diagnostics=gate
            )
            return _decision(False, None, suppressed[0], triggered, suppressed, intent=None, gate_diagnostics=gate)
        would_suppress.append("session_cap_reached")

    if manual_override and not triggered_reasons:
        triggered_reasons = ["manual_trigger"]

    intent = _choose_intent(
        triggered_reasons,
        probe_phase_active=probe_phase_active,
        lo_independent_evidence_mass=lo_independent_evidence_mass,
        cold_start_min_lo_evidence=config.cold_start_min_lo_evidence,
    )
    selection = _choose_intervention_item(
        vault,
        repository,
        attempt_id=attempt_id,
        learning_object_id=learning_object_id,
        exclude_practice_item_id=practice_item_id,
        target_facets=target_facets,
        failed_facets=failed_facets,
        intent=intent,
        max_error_severity=max_error_severity,
        tau_severe_error=thresholds["tau_severe_error"].value,
        clock=clock,
    )
    candidate = selection.candidate
    triggered = [f"{INTERVENTION_ACTION}:{reason}:{practice_item_id}" for reason in triggered_reasons]
    if manual_override and not any(reason == "manual_trigger" for reason in triggered_reasons):
        # Always tag manual triggers so the scheduler/tuning queries can tell a
        # user-forced follow-up apart from one the automatic policy chose.
        triggered.append(f"{INTERVENTION_ACTION}:manual_trigger:{practice_item_id}")
    if candidate is None:
        now = _now_iso(clock)
        need_target_facets = selection.diagnostic_gate_facets or target_facets
        need_id = repository.upsert_intervention_need(
            {
                "attempt_id": attempt_id,
                "learning_object_id": learning_object_id,
                "practice_item_id": practice_item_id,
                "desired_intent": intent,
                "trigger_reason": triggered_reasons[0],
                "target_facets": need_target_facets,
                "error_types": [],
                "priority": min(1.0, 0.5 + max_error_severity / 2),
                "status": "pending",
                "blocked_reason": "no_suitable_item",
                "candidate_requirements": {
                    "same_learning_object": True,
                    "min_target_facet_overlap": config.min_target_facet_overlap,
                    "avoid_bad_item_suspicion_above": 0.65,
                },
                "diagnostic_focus": selection.diagnostic_focus,
                "created_at": now,
                "updated_at": now,
            }
        )
        suppressed = [f"{INTERVENTION_ACTION}:no_suitable_item:{need_id}"]
        gate = _gate("need_recorded", "no_suitable_item", would_suppress)
        repository.update_attempt_surprise_actions(
            attempt_id, triggered_actions=triggered, suppressed_actions=suppressed, gate_diagnostics=gate
        )
        # spec §4.1/§4.2: distinguish "the misconception discrimination gate demoted
        # the only facet-eligible candidate" from a plain empty candidate pool.
        need_outcome = (
            "created_need_no_discriminator"
            if selection.misconception_gate_blocked
            else "created_need_for_generation"
        )
        _record_followup_decision_features(
            vault,
            repository,
            attempt_id=attempt_id,
            learning_object_id=learning_object_id,
            selection=selection,
            outcome=need_outcome,
            need_id=need_id,
            selected_item_id=None,
            manual_trigger=gate if manual_override else None,
            clock=clock,
        )
        return _decision(
            False, None, suppressed[0], triggered, suppressed,
            intent=intent, need_id=need_id, gate_diagnostics=gate,
        )

    triggered.append(f"{INTERVENTION_ACTION}:queued:{candidate.id}")
    gate = _gate("queued", triggered_reasons[0], would_suppress)
    repository.update_attempt_surprise_actions(attempt_id, triggered_actions=triggered, gate_diagnostics=gate)
    _record_followup_decision_features(
        vault,
        repository,
        attempt_id=attempt_id,
        learning_object_id=learning_object_id,
        selection=selection,
        outcome="queued_diagnostic" if selection.open_facets else "queued_non_diagnostic_review",
        need_id=None,
        selected_item_id=candidate.id,
        manual_trigger=gate if manual_override else None,
        clock=clock,
    )
    return _decision(
        True, candidate.id, triggered_reasons[0], triggered, [],
        intent=intent, gate_diagnostics=gate,
    )


def evaluate_negative_surprise_followup(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    learning_object_id: str,
    practice_item_id: str,
    surprise_direction: str,
    bayesian_surprise: float,
    grader_confidence: float | None,
    error_event_written: bool,
    available_minutes: int | None = None,
    clock: Clock | None = None,
) -> FollowupDecision:
    """Decide whether a negative-surprise follow-up Practice Item should fire.

    Implements the §10 gate. When a follow-up fires, the chosen item id is
    recorded in ``attempt_surprise.triggered_actions_json``; when blocked, the
    reason is recorded in ``attempt_surprise.suppressed_actions_json``.
    """

    return evaluate_intervention_followup(
        vault,
        repository,
        attempt_id=attempt_id,
        learning_object_id=learning_object_id,
        practice_item_id=practice_item_id,
        surprise_direction=surprise_direction,
        bayesian_surprise=bayesian_surprise,
        grader_confidence=grader_confidence,
        error_event_written=error_event_written,
        max_error_severity=0.0,
        repeated_same_item_failure=False,
        repeated_same_facet_failure=False,
        probe_unfamiliar_probability=None,
        available_minutes=available_minutes,
        clock=clock,
    )


def evaluate_attempt_intervention_followup(
    vault: LoadedVault,
    repository: Repository,
    *,
    result: Any,
    available_minutes: int | None = None,
    session_id: str | None = None,
    manual_override: bool = False,
    ai_client: Any = None,
    clock: Clock | None = None,
) -> FollowupDecision:
    """Run the full post-attempt intervention policy for one attempt result.

    This is the shared UI/CLI entrypoint. It threads the derived attempt debug
    payload into the broader intervention gate so severe/repeated failures,
    target facets, probe state, and cold-start evidence are handled consistently
    outside the CLI.

    Registry normalization + resolution (spec §2.2/§4.3/§7) run here first, after
    error persistence and before evaluation, so a just-diagnosed belief is visible
    to routing and the hypothesis prior. Replay never re-normalizes (it does not
    run this path); persisted ``misconception_id`` links survive rebuilds.

    §5.7 block boundary semantics: for an attempt inside an active diagnostic
    block (a diagnostic submission that consumed a committed presentation),
    follow-up evaluation, follow-up queue insertion, and misconception
    normalization are DEFERRED to the block-end hook
    (probe_blocks.end_diagnostic_block) — a force-inserted follow-up mid-block
    would reveal that the previous answer was wrong, and normalization here
    would duplicate the block's diagnosis.
    """

    attempt_row = repository.fetch_practice_attempt(result.attempt_id) or {}
    open_episode = repository.open_probe_episode(result.learning_object_id)
    if (
        open_episode is not None
        and open_episode.status == "in_progress"
        and attempt_row.get("probe_presentation_id") is not None
    ):
        suppressed = [f"{INTERVENTION_ACTION}:deferred_to_block_end:{open_episode.id}"]
        repository.update_attempt_surprise_actions(
            result.attempt_id, suppressed_actions=suppressed
        )
        return _decision(
            False, None, "deferred_to_block_end", [], suppressed, intent=None
        )

    normalize_and_resolve_attempt(
        vault,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        ai_client=ai_client,
        clock=clock,
    )
    # §6.5 re-probe trigger: repeated prediction errors on a settled LO signal
    # model misspecification and reopen probing (live path only, never replay).
    from learnloop.services.probe_episodes import maybe_reprobe_for_predictive_failure

    maybe_reprobe_for_predictive_failure(
        vault, repository, result.learning_object_id, clock=clock
    )

    debug_payload = result.debug_payload or {}
    facet_targets = _facet_targets_from_debug(debug_payload)
    aggregate_facet_states = [
        state for state in repository.facet_recall_states(result.learning_object_id) if state.practice_item_id is None
    ]
    lo_independent_evidence_mass = sum(state.independent_evidence_mass for state in aggregate_facet_states)
    probe_state = repository.probe_state(result.learning_object_id)
    open_episode = repository.open_probe_episode(result.learning_object_id)
    probe_unfamiliar_probability = _probe_unfamiliar_probability(
        vault,
        repository,
        result,
        probe_state,
    )
    error_events = repository.error_events_for_attempt(result.attempt_id)
    max_error_severity = _max_error_severity(debug_payload, error_events)
    if available_minutes is None and session_id is not None:
        session = repository.fetch_session(session_id) or {}
        available_minutes = session.get("available_minutes")

    return evaluate_intervention_followup(
        vault,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction=result.surprise_direction,
        bayesian_surprise=result.bayesian_surprise,
        grader_confidence=result.grader_confidence,
        error_event_written=bool(result.error_event_ids or error_events),
        max_error_severity=max_error_severity,
        probe_unfamiliar_probability=probe_unfamiliar_probability,
        target_facets=facet_targets.selection_facets,
        failed_facets=facet_targets.failed_facets,
        bad_item_suspicion=float(debug_payload.get("bad_item_suspicion") or 0.0),
        available_minutes=available_minutes,
        session_id=session_id,
        session_interventions_for_lo=_session_interventions_for_lo(
            repository, session_id, result.learning_object_id
        ),
        probe_phase_active=(probe_state is not None and probe_state.status == "in_progress")
        or (open_episode is not None and open_episode.status == "in_progress"),
        lo_independent_evidence_mass=lo_independent_evidence_mass,
        lo_raw_attempt_count=len(
            repository.list_recent_attempts_by_learning_object(result.learning_object_id, limit=1000)
        ),
        manual_override=manual_override,
        clock=clock,
    )


def _probe_unfamiliar_probability(
    vault: LoadedVault,
    repository: Repository,
    result: Any,
    probe_state: Any,
) -> float | None:
    if float(result.correctness or 0.0) >= 1.0:
        return None
    # Probe redesign: live evidence flows through diagnostic episodes; the
    # legacy lo_probe_state branch below serves only frozen pre-redesign phases.
    episode = repository.open_probe_episode(result.learning_object_id)
    if episode is not None and episode.hypothesis_set_id is not None:
        from learnloop.services.probe_episodes import episode_posterior
        from learnloop.services.probe_hypotheses import H_OTHER, H_UNFAMILIAR

        posterior = episode_posterior(vault, repository, episode)
        if posterior is not None:
            # The reserved open-set mass counts toward "unfamiliar" here: both
            # states mean the learner is not demonstrably capable and route to
            # the same foundational/diagnostic intervention. Without it the
            # richer episode set mechanically dilutes the legacy-calibrated
            # threshold this trigger was tuned against.
            return float(
                posterior.posterior.get(H_UNFAMILIAR, 0.0) + posterior.posterior.get(H_OTHER, 0.0)
            )
    if probe_state is None or probe_state.hypothesis_set_id is None:
        return None
    if probe_state.status != "in_progress":
        completed_at = parse_utc(probe_state.completed_at)
        attempt = repository.fetch_practice_attempt(result.attempt_id) or {}
        attempt_at = parse_utc(attempt.get("created_at"))
        if completed_at is None or attempt_at is None or attempt_at > completed_at:
            return None
    posterior = probe_posterior(vault, repository, result.learning_object_id, probe_state=probe_state)
    if posterior is None:
        return None
    return float(posterior.posterior.get("unfamiliar", 0.0))


def _facet_targets_from_debug(debug_payload: dict[str, Any]) -> AttemptFacetTargets:
    facet_outcomes = debug_payload.get("facet_outcomes")
    if isinstance(facet_outcomes, dict):
        failed = [
            str(facet)
            for facet, outcome in facet_outcomes.items()
            if isinstance(outcome, (int, float)) and float(outcome) < 0.40
        ]
        if failed:
            return AttemptFacetTargets(selection_facets=failed, failed_facets=failed)
    covered = debug_payload.get("covered_facets")
    if isinstance(covered, dict):
        return AttemptFacetTargets(selection_facets=list(covered.keys()), failed_facets=[])
    coverage_trace = debug_payload.get("coverage_trace")
    if isinstance(coverage_trace, dict):
        traced = coverage_trace.get("covered_facets")
        if isinstance(traced, dict):
            return AttemptFacetTargets(selection_facets=list(traced.keys()), failed_facets=[])
    return AttemptFacetTargets(selection_facets=[], failed_facets=[])


def _max_error_severity(debug_payload: dict[str, Any], error_events: list[dict[str, Any]]) -> float:
    raw = debug_payload.get("max_error_severity")
    if isinstance(raw, (int, float)):
        return float(raw)
    severities = [float(event.get("severity") or 0.0) for event in error_events]
    return max(severities, default=0.0)


def _session_interventions_for_lo(
    repository: Repository,
    session_id: str | None,
    learning_object_id: str,
) -> int:
    if not session_id:
        return 0
    session = repository.fetch_session(session_id)
    started_at = session.get("started_at") if session else None
    count = 0
    for attempt in repository.list_recent_attempts_by_learning_object(learning_object_id, limit=1000):
        if started_at and attempt.get("created_at") and attempt["created_at"] < started_at:
            continue
        surprise = repository.latest_attempt_surprise(attempt["id"]) or {}
        if any(
            isinstance(action, str) and action.startswith(f"{INTERVENTION_ACTION}:queued:")
            for action in surprise.get("triggered_actions", [])
        ):
            count += 1
    return count


def _decision(
    triggered: bool,
    practice_item_id: str | None,
    reason: str,
    triggered_actions: list[str],
    suppressed_actions: list[str],
    *,
    intent: str | None = None,
    need_id: str | None = None,
    gate_diagnostics: dict[str, Any] | None = None,
) -> FollowupDecision:
    return FollowupDecision(
        triggered=triggered,
        practice_item_id=practice_item_id,
        reason=reason,
        triggered_actions=triggered_actions,
        suppressed_actions=suppressed_actions,
        intent=intent,
        need_id=need_id,
        gate_diagnostics=gate_diagnostics,
    )


def _build_gate_diagnostics(
    *,
    outcome: str,
    decisive_reason: str,
    natural_trigger_reasons: list[str],
    triggered_reasons: list[str],
    would_suppress: list[str],
    manual_override: bool,
    bayesian_surprise: float,
    surprise_direction: str,
    grader_confidence: float | None,
    max_error_severity: float,
    probe_unfamiliar_probability: float | None,
    session_interventions_for_lo: int,
    available_minutes: int | None,
    target_facets: list[str],
    config: Any,
    thresholds: dict[str, ResolvedThreshold],
    gate_mode: str = "cascade",
    score_result: GateScoreResult | None = None,
    item_failure_count: float | None = None,
    facet_failure_count: float | None = None,
) -> dict[str, Any]:
    """Per-attempt record of why the follow-up gate did (or did not) fire.

    Persisted on ``attempt_surprise`` for every evaluation so the feedback screen
    can name the single decisive signal. The ``natural_trigger_reasons`` /
    ``would_suppress`` / ``would_auto_fire`` fields preserve the manual-override
    tuning contract; ``decisive_reason`` + ``decisive_signal`` carry the one
    signal the UI renders. All keys added since migration 015 (``gate_mode``,
    ``thresholds``, score fields) are additive so old rows keep rendering.
    """

    payload = {
        "feature_version": GATE_FEATURE_VERSION,
        "outcome": outcome,
        "decisive_reason": decisive_reason,
        "decisive_signal": _decisive_signal(
            decisive_reason,
            bayesian_surprise=bayesian_surprise,
            surprise_direction=surprise_direction,
            grader_confidence=grader_confidence,
            max_error_severity=max_error_severity,
            probe_unfamiliar_probability=probe_unfamiliar_probability,
            session_interventions_for_lo=session_interventions_for_lo,
            available_minutes=available_minutes,
            config=config,
            thresholds=thresholds,
            score_result=score_result,
            item_failure_count=item_failure_count,
            facet_failure_count=facet_failure_count,
        ),
        "natural_trigger_reasons": natural_trigger_reasons,
        "triggered_reasons": list(triggered_reasons),
        "would_suppress": would_suppress,
        "would_auto_fire": bool(natural_trigger_reasons) and not would_suppress,
        "manual_override": manual_override,
        "bayesian_surprise": bayesian_surprise,
        "surprise_direction": surprise_direction,
        # Carries the *resolved* (possibly quantile) value; full provenance in
        # the "thresholds" block below.
        "tau_followup_nats": thresholds["tau_followup_nats"].value,
        "grader_confidence": grader_confidence,
        "max_error_severity": max_error_severity,
        "target_facets": list(target_facets),
        "gate_mode": gate_mode,
        "thresholds": {name: threshold.as_dict() for name, threshold in thresholds.items()},
    }
    if score_result is not None:
        payload.update(score_result.as_dict())
        payload["hard_gates"] = [
            reason for reason in would_suppress if reason in ("no_time", "session_cap_reached")
        ]
    return payload


def _threshold_fields(threshold: ResolvedThreshold) -> dict[str, Any]:
    return {
        "threshold": threshold.value,
        "threshold_source": threshold.source,
        "threshold_quantile": threshold.quantile,
        "threshold_sample_size": threshold.sample_size,
    }


def _decisive_signal(
    reason: str,
    *,
    bayesian_surprise: float,
    surprise_direction: str,
    grader_confidence: float | None,
    max_error_severity: float,
    probe_unfamiliar_probability: float | None,
    session_interventions_for_lo: int,
    available_minutes: int | None,
    config: Any,
    thresholds: dict[str, ResolvedThreshold],
    score_result: GateScoreResult | None = None,
    item_failure_count: float | None = None,
    facet_failure_count: float | None = None,
) -> dict[str, Any] | None:
    """Describe the single signal that decided this follow-up outcome.

    ``value``/``threshold``/``comparator`` let the UI render one line such as
    ``surprise 0.02 nats < τ 0.05`` without re-deriving thresholds client-side.
    ``satisfied`` is whether the signal's own condition held (a trigger that
    fired, or a suppression gate that blocked). Quantile-resolved thresholds
    additionally carry ``threshold_source`` / ``threshold_quantile`` /
    ``threshold_sample_size`` so the explanation stays truthful about where the
    number came from.
    """

    if reason in ("gate_score", "gate_score_below_threshold"):
        if score_result is None:
            return None
        return {
            "name": "gate_score",
            "value": score_result.score,
            "threshold": score_result.threshold,
            "comparator": ">=",
            "unit": "score",
            "satisfied": score_result.fired,
        }
    if reason in ("negative_surprise", "no_trigger"):
        tau = thresholds["tau_followup_nats"]
        return {
            "name": "bayesian_surprise",
            "value": bayesian_surprise,
            **_threshold_fields(tau),
            "comparator": ">",
            "unit": "nats",
            "satisfied": surprise_direction == "negative" and bayesian_surprise > tau.value,
            "surprise_direction": surprise_direction,
        }
    if reason == "severe_error_event":
        tau = thresholds["tau_severe_error"]
        return {
            "name": "max_error_severity",
            "value": max_error_severity,
            **_threshold_fields(tau),
            "comparator": ">=",
            "unit": "severity",
            "satisfied": max_error_severity >= tau.value,
        }
    if reason == "high_unfamiliar_posterior":
        tau = thresholds["tau_unfamiliar_intervention"]
        return {
            "name": "unfamiliar_posterior",
            "value": probe_unfamiliar_probability,
            **_threshold_fields(tau),
            "comparator": ">=",
            "unit": "probability",
            "satisfied": probe_unfamiliar_probability is not None
            and probe_unfamiliar_probability >= tau.value,
        }
    if reason == "repeated_same_item_failure":
        return {
            "name": "repeated_item_failures",
            "value": item_failure_count,
            "threshold": config.tau_repeated_item_failures,
            "comparator": ">=",
            "unit": "count",
            "satisfied": True,
        }
    if reason == "repeated_same_facet_failure":
        return {
            "name": "repeated_facet_failures",
            "value": facet_failure_count,
            "threshold": config.tau_repeated_facet_failures,
            "comparator": ">=",
            "unit": "count",
            "satisfied": True,
        }
    if reason == "no_error_event":
        return {
            "name": "error_event_written",
            "value": False,
            "threshold": True,
            "comparator": "==",
            "unit": None,
            "satisfied": False,
        }
    if reason == "low_grader_confidence":
        return {
            "name": "grader_confidence",
            "value": grader_confidence,
            "threshold": config.gamma_min,
            "comparator": "<",
            "unit": "confidence",
            "satisfied": True,
        }
    if reason == "no_time":
        return {
            "name": "available_minutes",
            "value": available_minutes,
            "threshold": 0,
            "comparator": "<=",
            "unit": "minutes",
            "satisfied": True,
        }
    if reason == "session_cap_reached":
        return {
            "name": "session_interventions",
            "value": session_interventions_for_lo,
            "threshold": config.max_interventions_per_lo_per_session,
            "comparator": ">=",
            "unit": "count",
            "satisfied": True,
        }
    if reason == "no_suitable_item":
        return {
            "name": "eligible_items",
            "value": 0,
            "threshold": 1,
            "comparator": ">=",
            "unit": "items",
            "satisfied": False,
        }
    if reason == "manual_trigger":
        return {
            "name": "manual_trigger",
            "value": None,
            "threshold": None,
            "comparator": None,
            "unit": None,
            "satisfied": True,
        }
    return None


def _choose_intent(
    reasons: list[str],
    *,
    probe_phase_active: bool,
    lo_independent_evidence_mass: float,
    cold_start_min_lo_evidence: float,
) -> str:
    if probe_phase_active or lo_independent_evidence_mass < cold_start_min_lo_evidence:
        return "probe"
    if "high_unfamiliar_posterior" in reasons:
        return "guided_reconstruction"
    if any(reason in reasons for reason in ("severe_error_event", "repeated_same_item_failure", "repeated_same_facet_failure")):
        return "repair"
    if "negative_surprise" in reasons:
        return "probe"
    return "review"


def _canonical_target_facets(vault: LoadedVault, facets: list[str]) -> list[str]:
    return sorted({vault.canonical_facet_id(facet) for facet in facets})


def _active_misconceptions(
    repository: Repository,
    learning_object_id: str,
    *,
    attempt_id: str | None,
    gate_facets: set[str],
    tau_severe_error: float,
) -> list[MisconceptionRecord]:
    """Active registry beliefs that gate diagnostic routing (spec §4.1).

    Status ``active``, severity >= ``tau_severe_error``, and ``facet_ids``
    intersecting the diagnostic gate facets — PLUS any belief attributed on *this*
    attempt (regardless of facets), because the just-diagnosed slip is exactly the
    one we must discriminate. Deduped by id, order-stable by insertion.
    """

    attempt_mc_ids: set[str] = set()
    if attempt_id:
        for event in repository.error_events_for_attempt(attempt_id):
            mc_id = event.get("misconception_id")
            if mc_id:
                attempt_mc_ids.add(str(mc_id))
    selected: dict[str, MisconceptionRecord] = {}
    for record in repository.misconceptions_for_learning_object(learning_object_id, statuses=("active",)):
        if record.id in attempt_mc_ids:
            selected[record.id] = record
            continue
        if record.severity < tau_severe_error:
            continue
        if gate_facets and not (set(record.facet_ids) & gate_facets):
            continue
        selected[record.id] = record
    return list(selected.values())


def _demonstrated_facets(repository: Repository, learning_object_id: str) -> list[str]:
    """Facets the learner has already passed, snapshotted for review (spec §5.3).

    Deterministic definition (the inverse of :func:`_is_known_gap_state`): a facet
    whose uncertainty state is ``resolved`` with its ``facet_solid`` hypothesis on
    top. Read once at need-creation and snapshotted into ``diagnostic_focus`` so
    the §5.3 review validates identically regardless of when it runs (replay-safe).
    """

    demonstrated: list[str] = []
    for state in repository.facet_uncertainty_states(learning_object_id, statuses=("resolved",)):
        marginal = getattr(state, "hypothesis_marginal", {}) or {}
        if not marginal:
            continue
        top_label = max(marginal, key=marginal.get)
        if top_label == f"facet_solid:{state.facet_id}":
            demonstrated.append(state.facet_id)
    return sorted(set(demonstrated))


def _augment_diagnostic_focus_with_misconceptions(
    diagnostic_focus: dict[str, Any] | None,
    vault: LoadedVault,
    repository: Repository,
    *,
    active_mcs: list[MisconceptionRecord],
    learning_object_id: str,
    source_practice_item_id: str,
) -> dict[str, Any]:
    """Snapshot belief + §5.3 prerequisite context into the need's focus (spec §4).

    Additive JSON keys (payload is already JSON): the active misconception ids and
    statements, their implicated facets, the demonstrated facets, and the source
    item id + ``surface_family`` — enough for review (§5.3) to validate without any
    live learner state.
    """

    focus = dict(diagnostic_focus) if diagnostic_focus else {}
    focus["misconception_ids"] = [record.id for record in active_mcs]
    focus["misconception_statements"] = {record.id: record.statement for record in active_mcs}
    focus["implicated_facets"] = sorted({facet for record in active_mcs for facet in record.facet_ids})
    focus["demonstrated_facets"] = _demonstrated_facets(repository, learning_object_id)
    focus["source_practice_item_id"] = source_practice_item_id
    source_item = vault.practice_items.get(source_practice_item_id)
    focus["source_surface_family"] = source_item.surface_family if source_item is not None else None
    return focus


def _misconception_discrimination(
    repository: Repository,
    vault: LoadedVault,
    item: PracticeItem,
    rubric: Any,
    hypothesis_set: Any,
    active_mcs: list[MisconceptionRecord],
    tau_power: float,
) -> tuple[bool, float, float]:
    """``(discriminates, best_J_lb, misconception_eig)`` for a candidate (spec §4.1).

    A candidate is diagnostic-eligible iff its Youden-J lower bound against >=1
    active belief clears ``tau_discrimination_power``. ``J_lb`` reads the estimated
    discrimination row when present, else the bridge default (a rubric fatal error
    that links the belief but has no estimated row yet — the same bridge probes.py
    uses). When eligible, the misconception dimension is fed into the ranking
    through the calibrated EIG conditionals (§3), NOT a flat bonus, so a 0.9/0.95
    discriminator outranks a 0.6/0.7 one; the facet-EIG terms are left untouched.
    """

    from learnloop.vault.models import discriminates

    bridge = discriminates(item, rubric)
    bridge_j_lb = _BRIDGE_SENSITIVITY + _BRIDGE_SPECIFICITY - 1.0
    best_j_lb = 0.0
    for record in active_mcs:
        row = repository.discrimination_row(item.id, record.id)
        if row is not None:
            best_j_lb = max(best_j_lb, row.youden_j_lb(0.25))
        elif record.id in bridge:
            best_j_lb = max(best_j_lb, bridge_j_lb)
    if best_j_lb < tau_power:
        return False, best_j_lb, 0.0
    discrimination, discriminated_ids = item_registry_discrimination(
        repository, vault, item, rubric, hypothesis_set
    )
    item_a, item_b, probe_irt = resolve_item_irt(vault, item)
    mc_eig = expected_information_gain(
        hypothesis_set,
        item,
        rubric,
        item_a=item_a,
        item_b=item_b,
        irt=probe_irt,
        discrimination=discrimination,
        discriminated_ids=discriminated_ids,
    )
    return True, best_j_lb, mc_eig


def _choose_intervention_item(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str | None,
    learning_object_id: str,
    exclude_practice_item_id: str,
    target_facets: list[str],
    failed_facets: list[str],
    intent: str,
    max_error_severity: float,
    tau_severe_error: float = 0.0,
    clock: Clock | None = None,
) -> InterventionSelection:
    candidates = [
        item
        for item in vault.practice_items.values()
        if item.learning_object_id == learning_object_id and item.id != exclude_practice_item_id
    ]
    # Tutor-question evidence (question_signal): substantive unresolved
    # questions update the marginals BEFORE gating/EIG, so questioned facets
    # carry more entropy (higher facet-EIG for items probing them) and
    # questioned-but-never-failed facets join as virtual open states. Pure
    # read-side adjustment of persisted question_events — replay-safe.
    adjusted_states, question_signal = question_adjusted_uncertainty_states(
        vault,
        repository,
        learning_object_id,
        exclude_attempt_id=attempt_id,
        clock=clock,
    )
    diagnostic_states = [
        state
        for state in adjusted_states
        if state.status in {"open", "resolving"} or _is_known_gap_state(state)
    ]
    severity = max(max_error_severity, 0.05)
    target = set(target_facets)
    dominant_pool = [
        state for state in diagnostic_states if not target or state.facet_id in target
    ] or diagnostic_states
    interim_dominant_state = max(
        dominant_pool,
        key=lambda state: (state.uncertainty * severity, state.uncertainty, state.facet_id),
        default=None,
    )
    interim_dominant_target_facet = (
        interim_dominant_state.facet_id
        if interim_dominant_state is not None
        else (sorted(target)[0] if target else None)
    )
    diagnostic_focus = _build_diagnostic_focus(
        vault,
        repository,
        attempt_id=attempt_id,
        failed_facets=failed_facets,
        diagnostic_states=diagnostic_states,
        max_error_severity=max_error_severity,
        fallback_dominant_target_facet=interim_dominant_target_facet,
        question_signal=question_signal,
    )
    dominant_target_facet = diagnostic_focus.get("primary_target_facet")
    diagnostic_gate_facets = list(diagnostic_focus.get("diagnostic_gate_facets") or [])
    diagnostic_gate_source = diagnostic_focus.get("diagnostic_gate_source")
    if not isinstance(dominant_target_facet, str):
        dominant_target_facet = interim_dominant_target_facet
    if not diagnostic_gate_facets and dominant_target_facet is not None:
        diagnostic_gate_facets = [dominant_target_facet]
    if not diagnostic_gate_facets and target:
        diagnostic_gate_facets = sorted(target)
    if not diagnostic_focus:
        diagnostic_focus = None
    elif not diagnostic_focus.get("primary_target_facet") and dominant_target_facet is not None:
        diagnostic_focus = {
            **diagnostic_focus,
            "primary_target_facet": dominant_target_facet,
            "diagnostic_gate_facets": diagnostic_gate_facets,
            "target_facets": diagnostic_gate_facets,
            "diagnostic_gate_source": diagnostic_gate_source or "singleton",
        }
    gate_reference = set(diagnostic_gate_facets)
    open_facets = sorted(state.facet_id for state in diagnostic_states)
    if diagnostic_focus is not None:
        diagnostic_focus = {
            **diagnostic_focus,
            "open_facets": open_facets,
            # Question-adjusted marginal snapshot per gate facet: the frozen
            # belief state a generated probe must discriminate (spec: authoring
            # designs the item whose outcomes separate these hypotheses).
            "target_facet_marginals": {
                state.facet_id: state.hypothesis_marginal
                for state in diagnostic_states
                if state.facet_id in gate_reference
            },
        }

    # spec §4.1: active registry beliefs that gate diagnostic routing for this LO.
    active_mcs = _active_misconceptions(
        repository,
        learning_object_id,
        attempt_id=attempt_id,
        gate_facets=gate_reference,
        tau_severe_error=tau_severe_error,
    )
    active_misconception_ids = [record.id for record in active_mcs]
    if active_mcs:
        # spec §4.1/§5.3: snapshot the belief ids/statements + the prerequisite
        # review context (demonstrated facets, source item/surface) into the need.
        diagnostic_focus = _augment_diagnostic_focus_with_misconceptions(
            diagnostic_focus,
            vault,
            repository,
            active_mcs=active_mcs,
            learning_object_id=learning_object_id,
            source_practice_item_id=exclude_practice_item_id,
        )

    if not candidates:
        return InterventionSelection(
            candidate=None,
            dominant_target_facet=dominant_target_facet,
            diagnostic_gate_facets=diagnostic_gate_facets,
            diagnostic_gate_source=diagnostic_gate_source,
            diagnostic_focus=diagnostic_focus,
            open_facets=open_facets,
            slate=[],
            misconception_gate_blocked=False,
            active_misconception_ids=active_misconception_ids,
            eligible_slate_size=0,
        )

    gate_applies = bool(diagnostic_states) and dominant_target_facet is not None
    followup_config = vault.config.scheduler.followup
    min_overlap = followup_config.min_target_facet_overlap
    predictive_weight = followup_config.predictive_eig_weight
    targets_by_facet: dict[str, list[TargetItemModel]] = {}
    if diagnostic_states and followup_config.predictive_eig_target_cap > 0:
        targets_by_facet = build_target_models(
            vault,
            learning_object_id=learning_object_id,
            exclude_item_ids={exclude_practice_item_id},
            facet_ids={state.facet_id for state in diagnostic_states},
            cap=followup_config.predictive_eig_target_cap,
        )
    slate: list[dict[str, Any]] = []
    for item in candidates:
        support = candidate_facet_support(item)
        target_precision = _target_precision(support, gate_reference)
        quality = repository.practice_item_quality_state(item.id)
        suspicion = quality.bad_item_suspicion if quality is not None else 0.0
        gate_passed = True
        filtered_reason = None
        if gate_applies and dominant_target_facet not in support:
            gate_passed = False
            filtered_reason = "missing_dominant_facet"
        if gate_applies and target_precision < min_overlap:
            gate_passed = False
            filtered_reason = "subthreshold_overlap"
        if suspicion >= 0.65:
            gate_passed = False
            filtered_reason = "bad_item_suspicion"
        facet_eig_by_facet: dict[str, float] = {}
        total_facet_eig = 0.0
        predictive_eig_by_facet: dict[str, float] = {}
        total_predictive_eig = 0.0
        if diagnostic_states:
            item_a, item_b, probe_irt = resolve_item_irt(vault, item)
            rubric = vault.rubric_for_item(item)
            fatal_error_ids = {fatal_error.id for fatal_error in rubric.fatal_errors} if rubric is not None else set()
            for state in diagnostic_states:
                uncertainty_boost = 1.0 + vault.config.recall_coverage.kappa_uncertain * state.uncertainty
                eig = facet_expected_information_gain(
                    state.hypothesis_marginal,
                    facet_id=state.facet_id,
                    candidate_facet_support=support,
                    fatal_error_ids=fatal_error_ids,
                    item_a=item_a,
                    item_b=item_b,
                    irt=probe_irt,
                )
                facet_eig_by_facet[state.facet_id] = eig
                total_facet_eig += uncertainty_boost * eig
                predictive = predictive_facet_eig(
                    state.hypothesis_marginal,
                    facet_id=state.facet_id,
                    candidate_support=support,
                    candidate_fatal_error_ids=fatal_error_ids,
                    candidate_a=item_a,
                    candidate_b=item_b,
                    targets=targets_by_facet.get(state.facet_id, []),
                    candidate_item_id=item.id,
                    irt=probe_irt,
                )
                predictive_eig_by_facet[state.facet_id] = predictive.eig_nats
                total_predictive_eig += uncertainty_boost * predictive.eig_nats
        familiarity = familiarity_discount(
            repository,
            item,
            learning_object_id=learning_object_id,
            covered_facets={facet: 1.0 for facet in support},
            config=vault.config,
        )
        scaffold = float(item.scaffold_level or 0.0)
        intent_bonus = scaffold if intent in {"repair", "guided_reconstruction"} else 0.0
        fallback_overlap = _jaccard(support, target) if target else 0.0
        rank_score = (
            familiarity.independent_evidence_discount
            * (total_facet_eig + predictive_weight * total_predictive_eig)
            + intent_bonus
            if diagnostic_states
            else fallback_overlap + intent_bonus
        )
        slate.append(
            {
                "practice_item_id": item.id,
                "candidate_facet_support": sorted(support),
                "dominant_target_facet": dominant_target_facet,
                "open_facets": open_facets,
                "diagnostic_gate_facets": diagnostic_gate_facets,
                "diagnostic_gate_source": diagnostic_gate_source,
                "target_precision": target_precision,
                "min_target_facet_overlap": min_overlap,
                "gate_passed": gate_passed,
                "filtered_reason": filtered_reason,
                "facet_eig_by_facet": facet_eig_by_facet,
                "total_facet_eig": total_facet_eig,
                "predictive_eig_by_facet": predictive_eig_by_facet,
                "total_predictive_eig": total_predictive_eig,
                "predictive_eig_weight": predictive_weight,
                "predictive_eig_targets": {
                    facet_id: [target.item_id for target in targets]
                    for facet_id, targets in targets_by_facet.items()
                },
                "familiarity_discount": familiarity.independent_evidence_discount,
                "bad_item_suspicion": suspicion,
                "intent_bonus": intent_bonus,
                "rank_score": rank_score,
                "selected": False,
                "final_rank": None,
            }
        )

    # spec §4.1: misconception discrimination gate — layered ON TOP of the facet
    # gates above. A candidate stays eligible only if it discriminates >=1 active
    # belief (J_lb >= tau_discrimination_power); passing candidates feed their
    # misconception EIG into the ranking so genuine discriminators outrank
    # coverage lookalikes. When it demotes the only facet-eligible candidate we
    # route to no_suitable_item rather than queue a paraphrase (§4.1).
    misconception_gate_active = bool(active_mcs) and vault.config.scheduler.followup.require_misconception_discrimination
    misconception_filtered = False
    if misconception_gate_active:
        hypothesis_set = build_hypothesis_set(vault, repository, learning_object_id, clock=clock)
        tau_power = vault.config.scheduler.followup.tau_discrimination_power
        item_by_id = {item.id: item for item in candidates}
        for row in slate:
            item = item_by_id[str(row["practice_item_id"])]
            rubric = vault.rubric_for_item(item)
            discriminates_mc, best_j_lb, mc_eig = _misconception_discrimination(
                repository, vault, item, rubric, hypothesis_set, active_mcs, tau_power
            )
            row["discriminates_target_misconception"] = discriminates_mc
            row["misconception_discrimination_j_lb"] = best_j_lb
            if discriminates_mc:
                row["misconception_eig"] = mc_eig
                row["rank_score"] = float(row["rank_score"]) + mc_eig
            elif row["gate_passed"]:
                row["gate_passed"] = False
                row["filtered_reason"] = "no_misconception_discrimination"
                misconception_filtered = True

    eligible = [row for row in slate if row["gate_passed"]]
    eligible.sort(
        key=lambda row: (
            -float(row["rank_score"]),
            float(row["bad_item_suspicion"]),
            str(row["practice_item_id"]),
        )
    )
    selected_id = str(eligible[0]["practice_item_id"]) if eligible else None
    rank_by_id = {
        str(row["practice_item_id"]): rank
        for rank, row in enumerate(eligible, start=1)
    }
    for row in slate:
        row["selected"] = row["practice_item_id"] == selected_id
        row["final_rank"] = rank_by_id.get(str(row["practice_item_id"]))
    selected = next((item for item in candidates if item.id == selected_id), None)
    # The gate "blocked" only when it demoted an otherwise-passing candidate and
    # left nothing eligible — a plain empty pool is created_need_for_generation.
    misconception_gate_blocked = misconception_gate_active and selected is None and misconception_filtered
    return InterventionSelection(
        candidate=selected,
        dominant_target_facet=dominant_target_facet,
        diagnostic_gate_facets=diagnostic_gate_facets,
        diagnostic_gate_source=diagnostic_gate_source,
        diagnostic_focus=diagnostic_focus,
        open_facets=open_facets,
        slate=slate,
        misconception_gate_blocked=misconception_gate_blocked,
        active_misconception_ids=active_misconception_ids,
        eligible_slate_size=len(eligible),
    )


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _target_precision(candidate_support: set[str], diagnostic_gate_facets: set[str]) -> float:
    if not candidate_support or not diagnostic_gate_facets:
        return 0.0
    return len(candidate_support & diagnostic_gate_facets) / len(candidate_support)


def _build_diagnostic_focus(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str | None,
    failed_facets: list[str],
    diagnostic_states: list[Any],
    max_error_severity: float,
    fallback_dominant_target_facet: str | None,
    question_signal: QuestionSignal | None = None,
) -> dict[str, Any]:
    scores: dict[str, float] = {}
    source_scores: dict[str, dict[str, Any]] = {}
    repair_rationales: list[dict[str, Any]] = []
    failed = _canonical_target_facets(vault, failed_facets)
    diagnostic_state_by_facet = {state.facet_id: state for state in diagnostic_states}

    def add_score(facet: str, score: float, source: str, payload: dict[str, Any] | None = None) -> None:
        canonical = vault.canonical_facet_id(facet)
        if not canonical:
            return
        scores[canonical] = scores.get(canonical, 0.0) + score
        entry = source_scores.setdefault(canonical, {"score": 0.0, "sources": []})
        entry["score"] = float(entry["score"]) + score
        source_payload = {"source": source, "score": score}
        if payload:
            source_payload.update(payload)
        entry["sources"].append(source_payload)

    for facet in failed:
        add_score(
            facet,
            2.0 + max(max_error_severity, 0.0),
            "failed_facet",
            {"failed": True},
        )
    for state in diagnostic_states:
        status = getattr(state, "status", None)
        if status not in {"open", "resolving"} and not _is_known_gap_state(state):
            continue
        uncertainty = float(getattr(state, "uncertainty", 0.0) or 0.0)
        add_score(
            state.facet_id,
            1.0 + uncertainty,
            "facet_uncertainty",
            {"status": status, "uncertainty": uncertainty},
        )

    structured_target_seen = False
    # Tutor-question source: each questioned facet earns a bounded score so it
    # can claim an "enriched" extras slot, but stays below the failed-facet
    # floor (2.0+severity) so the grader's signal keeps the primary slot.
    if question_signal is not None and question_signal.events_by_facet:
        for facet, events in sorted(question_signal.events_by_facet.items()):
            structured_target_seen = True
            add_score(
                facet,
                0.75 + 0.25 * min(len(events), 3),
                "tutor_question",
                {
                    "question_event_ids": [str(event.get("id")) for event in events],
                    "question_types": sorted({str(event.get("question_type")) for event in events}),
                    "unresolved_count": len(events),
                    "solid_likelihood_ratio": question_signal.likelihood.value,
                    "likelihood_source": question_signal.likelihood.source,
                },
            )

    if attempt_id:
        for event in repository.error_events_for_attempt(attempt_id):
            repair_plan = event.get("repair_plan")
            if not isinstance(repair_plan, dict):
                continue
            targets = repair_plan.get("target_evidence_families")
            if not isinstance(targets, list):
                continue
            severity = float(event.get("severity") or max_error_severity or 0.0)
            for raw_facet in targets:
                structured_target_seen = True
                add_score(
                    str(raw_facet),
                    1.5 + severity,
                    "error_attribution",
                    {
                        "error_event_id": event.get("id"),
                        "error_type": event.get("error_type"),
                        "severity": severity,
                    },
                )
        feedback = repository.fetch_attempt_feedback_metadata(attempt_id)
        if feedback is not None:
            for suggestion in feedback.get("repair_suggestions", []):
                if not isinstance(suggestion, dict):
                    continue
                raw_targets = suggestion.get("target_evidence_families")
                targets = (
                    [vault.canonical_facet_id(str(facet)) for facet in raw_targets]
                    if isinstance(raw_targets, list)
                    else []
                )
                targets = sorted({facet for facet in targets if facet})
                rationale = str(suggestion.get("rationale") or "").strip()
                if targets:
                    structured_target_seen = True
                    for facet in targets:
                        add_score(
                            facet,
                            1.25,
                            "repair_suggestion",
                            {"practice_mode": suggestion.get("practice_mode"), "rationale": rationale},
                        )
                if rationale:
                    entry: dict[str, Any] = {"rationale": rationale}
                    practice_mode = suggestion.get("practice_mode")
                    if practice_mode:
                        entry["practice_mode"] = str(practice_mode)
                    if targets:
                        entry["target_evidence_families"] = targets
                    repair_rationales.append(entry)

    primary_pool = set(failed) | set(diagnostic_state_by_facet)
    if primary_pool:
        # Failed rubric facets outrank everything for the primary slot: tutor
        # questions and uncertainty may only enrich the gate set, never demote
        # the grader's missed criterion from primary.
        primary = max(
            primary_pool,
            key=lambda facet: (
                1 if facet in set(failed) else 0,
                scores.get(facet, 0.0),
                float(getattr(diagnostic_state_by_facet.get(facet), "uncertainty", 0.0) or 0.0),
                facet,
            ),
        )
    elif scores:
        primary = max(scores, key=lambda facet: (scores[facet], facet))
    else:
        primary = fallback_dominant_target_facet

    if primary is not None and primary not in scores:
        add_score(primary, 0.5, "singleton_fallback", {})

    if structured_target_seen:
        gate_source = "enriched"
        base_facets = list(failed)
        if primary is not None and primary not in base_facets:
            base_facets.insert(0, primary)
        max_targets = max(1, int(vault.config.scheduler.followup.max_diagnostic_target_facets))
        cap = max(max_targets, len(base_facets))
        extras = [
            facet
            for facet in sorted(scores, key=lambda key: (-scores[key], key))
            if facet not in set(base_facets)
        ]
        diagnostic_gate_facets = sorted(
            dict.fromkeys([*base_facets, *extras[: max(0, cap - len(base_facets))]])
        )
    elif failed:
        gate_source = "failed-set"
        diagnostic_gate_facets = sorted(failed)
    elif primary is not None:
        gate_source = "singleton"
        diagnostic_gate_facets = [primary]
    else:
        gate_source = None
        diagnostic_gate_facets = []

    if primary is not None and diagnostic_gate_facets and primary not in diagnostic_gate_facets:
        diagnostic_gate_facets = sorted([primary, *diagnostic_gate_facets])

    focus = {
        "primary_target_facet": primary,
        "target_facets": diagnostic_gate_facets,
        "diagnostic_gate_facets": diagnostic_gate_facets,
        "diagnostic_gate_source": gate_source,
        "failed_facets": sorted(failed),
        "facet_source_scores": {
            facet: {
                "score": float(payload["score"]),
                "sources": payload["sources"],
            }
            for facet, payload in sorted(source_scores.items())
        },
        "repair_rationales": repair_rationales,
    }
    if question_signal is not None and (
        question_signal.events_by_facet or question_signal.unfaceted_events
    ):
        # The learner's own words are the least lossy record of the confusion;
        # authoring reads these to aim the probe (facets stay authoritative).
        focus["tutor_question_context"] = question_signal.context_entries()
        focus["question_likelihood"] = question_signal.likelihood.as_dict()
    return focus


def _is_known_gap_state(state: Any) -> bool:
    if getattr(state, "status", None) != "resolved":
        return False
    marginal = getattr(state, "hypothesis_marginal", {}) or {}
    if not marginal:
        return False
    top_label = max(marginal, key=marginal.get)
    return top_label != f"facet_solid:{getattr(state, 'facet_id', '')}"


def _attempt_target_facets(repository: Repository, practice_item_id: str) -> list[str]:
    attempts = repository.list_recent_attempts_by_practice_item(practice_item_id, limit=1)
    if not attempts:
        return []
    return list(attempts[0].get("evidence_facets", []))


def current_same_item_failure_streak(repository: Repository, practice_item_id: str) -> int:
    """Trailing attempt-level failure streak for one Practice Item.

    The repository returns newest first, so the first success is the natural
    boundary. Historical failures before that success no longer describe a
    *repeated current failure* and must not contribute to the intervention gate.
    """

    streak = 0
    for attempt in repository.list_recent_attempts_by_practice_item(practice_item_id, limit=20):
        if not _attempt_is_failure(attempt):
            break
        streak += 1
    return streak


def current_same_facet_failure_streak(
    repository: Repository,
    learning_object_id: str,
    facets: list[str],
) -> int:
    """Largest current aggregate failure streak among the target facets.

    Facet recall state is updated from facet outcomes on every relevant attempt
    and already resets ``consecutive_failures`` to zero on success. Taking the
    maximum answers whether *any* target facet is repeatedly failing without
    conflating unrelated historical errors on the same Learning Object.
    """

    streaks = [
        state.consecutive_failures
        for facet in sorted(set(facets))
        if (state := repository.facet_recall_state(learning_object_id, facet)) is not None
    ]
    return max(streaks, default=0)


def _attempt_is_failure(attempt: dict[str, Any]) -> bool:
    return (
        attempt.get("attempt_type") == "dont_know"
        or float(attempt.get("correctness") or 0.0) <= 0.40
        or bool(attempt.get("error_type"))
    )


def _record_followup_decision_features(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    learning_object_id: str,
    selection: InterventionSelection,
    outcome: str,
    need_id: str | None,
    selected_item_id: str | None,
    manual_trigger: dict[str, Any] | None = None,
    clock: Clock | None,
) -> None:
    uncertainties = repository.facet_uncertainty_states(
        learning_object_id, statuses=("open", "resolving", "resolved")
    )
    source_debug = repository.attempt_debug_payload(attempt_id) or {}
    uncertainty_trace = source_debug.get("facet_uncertainty_trace")
    drops: dict[str, float] = {}
    if isinstance(uncertainty_trace, dict):
        updates = uncertainty_trace.get("updates")
        if isinstance(updates, dict):
            for facet, payload in updates.items():
                if isinstance(payload, dict):
                    drops[str(facet)] = float(payload.get("uncertainty_drop") or 0.0)
    selected_row = next(
        (row for row in selection.slate if row.get("practice_item_id") == selected_item_id),
        None,
    )
    prior = {
        state.facet_id: state.hypothesis_marginal
        for state in uncertainties
        if not selection.open_facets or state.facet_id in set(selection.open_facets)
    }
    repository.record_decision_features(
        decision_id=attempt_id,
        decision_type="followup",
        ability_vector={
            "facet_hypothesis_prior": prior,
            "open_facets": selection.open_facets,
            "realized_facet_uncertainty_drop": drops,
        },
        item_demand_vector={
            "selected_practice_item_id": selected_item_id,
            "candidate_facet_support": selected_row.get("candidate_facet_support") if selected_row else None,
            "dominant_target_facet": selection.dominant_target_facet,
            "diagnostic_gate_facets": selection.diagnostic_gate_facets,
            "diagnostic_gate_source": selection.diagnostic_gate_source,
            "per_facet_eig": selected_row.get("facet_eig_by_facet") if selected_row else {},
            "total_facet_eig": selected_row.get("total_facet_eig") if selected_row else 0.0,
            "per_facet_predictive_eig": selected_row.get("predictive_eig_by_facet") if selected_row else {},
            "total_predictive_eig": selected_row.get("total_predictive_eig") if selected_row else 0.0,
        },
        context={
            "candidate_slate": selection.slate,
            "decision_outcome": outcome,
            "need_id": need_id,
            "generation_need_id": (
                need_id
                if outcome in ("created_need_for_generation", "created_need_no_discriminator")
                else None
            ),
            "diagnostic_focus": selection.diagnostic_focus,
            "manual_trigger": manual_trigger,
            # spec §4.2: surface a thin eligible slate (pool-of-one silently zeroes
            # predictive_eig) and the active-misconception context when routing gated.
            **(
                {
                    "eligible_slate_size": selection.eligible_slate_size,
                    "active_misconception_ids": selection.active_misconception_ids or [],
                }
                if selection.active_misconception_ids
                else {}
            ),
        },
        algorithm_version=vault.config.algorithms.algorithm_version,
        clock=clock,
    )


def _now_iso(clock: Clock | None) -> str:
    now = clock.now() if clock is not None else datetime.now(UTC)
    return now.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
