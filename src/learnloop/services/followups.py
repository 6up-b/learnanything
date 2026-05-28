from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from learnloop.clock import Clock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.services.probes import HypothesisSet, probe_eig_component, probe_posterior, resolve_item_irt
from learnloop.services.recall_coverage import familiarity_discount, resolve_coverage
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
    bad_item_suspicion: float = 0.0,
    available_minutes: int | None = None,
    session_id: str | None = None,
    session_interventions_for_lo: int = 0,
    probe_phase_active: bool = False,
    lo_independent_evidence_mass: float = 0.0,
    lo_raw_attempt_count: int = 0,
    clock: Clock | None = None,
) -> FollowupDecision:
    """Intervention follow-up evaluator from the recall-coverage spec.

    It records all satisfied trigger reasons, queues at most one item, and
    persists an intervention need when a trigger has no suitable item.
    """

    config = vault.config.scheduler.followup
    target_facets = target_facets or _attempt_target_facets(repository, practice_item_id)
    target_facets = _canonical_target_facets(vault, target_facets)
    repeated_same_item_failure = (
        repeated_same_item_failure
        if repeated_same_item_failure is not None
        else _current_inclusive_same_item_failures(repository, practice_item_id) >= config.tau_repeated_item_failures
    )
    repeated_same_facet_failure = (
        repeated_same_facet_failure
        if repeated_same_facet_failure is not None
        else _current_inclusive_same_facet_failures(repository, learning_object_id, target_facets)
        >= config.tau_repeated_facet_failures
    )

    triggered_reasons: list[str] = []
    if surprise_direction == "negative" and bayesian_surprise > config.tau_followup_nats:
        triggered_reasons.append("negative_surprise")
    if max_error_severity >= config.tau_severe_error:
        triggered_reasons.append("severe_error_event")
    if repeated_same_item_failure:
        triggered_reasons.append("repeated_same_item_failure")
    if repeated_same_facet_failure:
        triggered_reasons.append("repeated_same_facet_failure")
    if probe_unfamiliar_probability is not None and probe_unfamiliar_probability >= config.tau_unfamiliar_intervention:
        triggered_reasons.append("high_unfamiliar_posterior")

    if not triggered_reasons:
        return _decision(False, None, "no_trigger", [], [], intent=None)
    if not error_event_written and "high_unfamiliar_posterior" not in triggered_reasons:
        return _decision(False, None, "no_error_event", [], [], intent=None)
    deterministic_dont_know = any(
        attempt.get("practice_item_id") == practice_item_id and attempt.get("attempt_type") == "dont_know"
        for attempt in repository.list_recent_attempts_by_practice_item(practice_item_id, limit=1)
    )
    if grader_confidence is None or (grader_confidence < config.gamma_min and not deterministic_dont_know):
        suppressed = [f"{INTERVENTION_ACTION}:low_grader_confidence"]
        repository.update_attempt_surprise_actions(attempt_id, suppressed_actions=suppressed)
        return _decision(False, None, suppressed[0], [], suppressed, intent=None)
    if available_minutes is not None and available_minutes <= 0:
        suppressed = [f"{INTERVENTION_ACTION}:no_time"]
        repository.update_attempt_surprise_actions(attempt_id, suppressed_actions=suppressed)
        return _decision(False, None, suppressed[0], [], suppressed, intent=None)
    if session_interventions_for_lo >= config.max_interventions_per_lo_per_session:
        suppressed = [f"{INTERVENTION_ACTION}:session_cap_reached:{learning_object_id}"]
        triggered = [f"{INTERVENTION_ACTION}:{reason}:{practice_item_id}" for reason in triggered_reasons]
        repository.update_attempt_surprise_actions(attempt_id, triggered_actions=triggered, suppressed_actions=suppressed)
        return _decision(False, None, suppressed[0], triggered, suppressed, intent=None)

    intent = _choose_intent(
        triggered_reasons,
        probe_phase_active=probe_phase_active,
        lo_independent_evidence_mass=lo_independent_evidence_mass,
        cold_start_min_lo_evidence=config.cold_start_min_lo_evidence,
    )
    candidate = _choose_intervention_item(
        vault,
        repository,
        learning_object_id=learning_object_id,
        exclude_practice_item_id=practice_item_id,
        target_facets=target_facets,
        intent=intent,
    )
    triggered = [f"{INTERVENTION_ACTION}:{reason}:{practice_item_id}" for reason in triggered_reasons]
    if candidate is None:
        now = _now_iso(clock)
        need_id = repository.upsert_intervention_need(
            {
                "attempt_id": attempt_id,
                "learning_object_id": learning_object_id,
                "practice_item_id": practice_item_id,
                "desired_intent": intent,
                "trigger_reason": triggered_reasons[0],
                "target_facets": target_facets,
                "error_types": [],
                "priority": min(1.0, 0.5 + max_error_severity / 2),
                "status": "pending",
                "blocked_reason": "no_suitable_item",
                "candidate_requirements": {
                    "same_learning_object": True,
                    "min_target_facet_overlap": 0.5,
                    "avoid_bad_item_suspicion_above": 0.65,
                },
                "created_at": now,
                "updated_at": now,
            }
        )
        suppressed = [f"{INTERVENTION_ACTION}:no_suitable_item:{need_id}"]
        repository.update_attempt_surprise_actions(attempt_id, triggered_actions=triggered, suppressed_actions=suppressed)
        return _decision(False, None, suppressed[0], triggered, suppressed, intent=intent, need_id=need_id)

    triggered.append(f"{INTERVENTION_ACTION}:queued:{candidate.id}")
    repository.update_attempt_surprise_actions(attempt_id, triggered_actions=triggered)
    return _decision(True, candidate.id, triggered_reasons[0], triggered, [], intent=intent)


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
    clock: Clock | None = None,
) -> FollowupDecision:
    """Run the full post-attempt intervention policy for one attempt result.

    This is the shared UI/CLI entrypoint. It threads the derived attempt debug
    payload into the broader intervention gate so severe/repeated failures,
    target facets, probe state, and cold-start evidence are handled consistently
    outside the CLI.
    """

    debug_payload = result.debug_payload or {}
    target_facets = _target_facets_from_debug(debug_payload)
    aggregate_facet_states = [
        state for state in repository.facet_recall_states(result.learning_object_id) if state.practice_item_id is None
    ]
    lo_independent_evidence_mass = sum(state.independent_evidence_mass for state in aggregate_facet_states)
    probe_state = repository.probe_state(result.learning_object_id)
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
        target_facets=target_facets,
        bad_item_suspicion=float(debug_payload.get("bad_item_suspicion") or 0.0),
        available_minutes=available_minutes,
        session_id=session_id,
        session_interventions_for_lo=_session_interventions_for_lo(
            repository, session_id, result.learning_object_id
        ),
        probe_phase_active=probe_state is not None and probe_state.status == "in_progress",
        lo_independent_evidence_mass=lo_independent_evidence_mass,
        lo_raw_attempt_count=len(
            repository.list_recent_attempts_by_learning_object(result.learning_object_id, limit=1000)
        ),
        clock=clock,
    )


def _probe_unfamiliar_probability(
    vault: LoadedVault,
    repository: Repository,
    result: Any,
    probe_state: Any,
) -> float | None:
    if probe_state is None or probe_state.hypothesis_set_id is None:
        return None
    if float(result.correctness or 0.0) >= 1.0:
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


def _choose_followup_item(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_id: str,
    exclude_practice_item_id: str,
) -> PracticeItem | None:
    candidates = [
        item
        for item in vault.practice_items.values()
        if item.learning_object_id == learning_object_id and item.id != exclude_practice_item_id
    ]
    if not candidates:
        return None

    probe_state = repository.probe_state(learning_object_id)
    if probe_state is not None and probe_state.status == "in_progress" and probe_state.hypothesis_set_id:
        record = repository.fetch_hypothesis_set(probe_state.hypothesis_set_id)
        if record is not None:
            hypothesis_set = HypothesisSet.from_record(record)

            def _eig(item: PracticeItem) -> float:
                item_a, item_b, probe_irt = resolve_item_irt(vault, item)
                rubric = vault.rubric_for_item(item)
                coverage = resolve_coverage(
                    item,
                    rubric,
                    attempt_type="diagnostic_probe",
                    hints_used=0,
                    learner_answer_md="prospective_probe",
                )
                familiarity = familiarity_discount(
                    repository,
                    item,
                    learning_object_id=learning_object_id,
                    covered_facets=coverage.covered_facets,
                    config=vault.config,
                )
                return familiarity.independent_evidence_discount * probe_eig_component(
                    hypothesis_set,
                    item,
                    rubric,
                    item_a=item_a,
                    item_b=item_b,
                    irt=probe_irt,
                )

            candidates.sort(key=lambda item: (-_eig(item), item.id))
            return candidates[0]

    candidates.sort(key=lambda item: item.id)
    return candidates[0]


def _target_facets_from_debug(debug_payload: dict[str, Any]) -> list[str]:
    facet_outcomes = debug_payload.get("facet_outcomes")
    if isinstance(facet_outcomes, dict):
        failed = [
            str(facet)
            for facet, outcome in facet_outcomes.items()
            if isinstance(outcome, (int, float)) and float(outcome) < 0.40
        ]
        if failed:
            return failed
    covered = debug_payload.get("covered_facets")
    if isinstance(covered, dict):
        return list(covered.keys())
    coverage_trace = debug_payload.get("coverage_trace")
    if isinstance(coverage_trace, dict):
        traced = coverage_trace.get("covered_facets")
        if isinstance(traced, dict):
            return list(traced.keys())
    return []


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
) -> FollowupDecision:
    return FollowupDecision(
        triggered=triggered,
        practice_item_id=practice_item_id,
        reason=reason,
        triggered_actions=triggered_actions,
        suppressed_actions=suppressed_actions,
        intent=intent,
        need_id=need_id,
    )


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


def _choose_intervention_item(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_id: str,
    exclude_practice_item_id: str,
    target_facets: list[str],
    intent: str,
) -> PracticeItem | None:
    candidates = [
        item
        for item in vault.practice_items.values()
        if item.learning_object_id == learning_object_id and item.id != exclude_practice_item_id
    ]
    if not candidates:
        return None
    target = set(target_facets)

    def rank(item: PracticeItem) -> tuple[float, float, str]:
        facets = set(item.repair_targets or item.evidence_facets)
        overlap = len(target & facets) / len(target | facets) if target and facets else 0.0
        quality = repository.practice_item_quality_state(item.id)
        suspicion = quality.bad_item_suspicion if quality is not None else 0.0
        scaffold = float(item.scaffold_level or 0.0)
        intent_bonus = scaffold if intent in {"repair", "guided_reconstruction"} else 0.0
        return (-(overlap + intent_bonus), suspicion, item.id)

    candidates.sort(key=rank)
    return candidates[0]


def _attempt_target_facets(repository: Repository, practice_item_id: str) -> list[str]:
    attempts = repository.list_recent_attempts_by_practice_item(practice_item_id, limit=1)
    if not attempts:
        return []
    return list(attempts[0].get("evidence_facets", []))


def _current_inclusive_same_item_failures(repository: Repository, practice_item_id: str) -> int:
    return sum(
        1
        for attempt in repository.list_recent_attempts_by_practice_item(practice_item_id, limit=20)
        if attempt.get("attempt_type") == "dont_know" or float(attempt.get("correctness") or 0.0) <= 0.40 or bool(attempt.get("error_type"))
    )


def _current_inclusive_same_facet_failures(repository: Repository, learning_object_id: str, facets: list[str]) -> int:
    target = set(facets)
    if not target:
        return 0
    return sum(
        1
        for attempt in repository.list_recent_attempts_by_learning_object(learning_object_id, limit=20)
        if set(attempt.get("evidence_facets", [])) & target
        and (
            attempt.get("attempt_type") == "dont_know"
            or float(attempt.get("correctness") or 0.0) <= 0.40
            or bool(attempt.get("error_type"))
        )
    )


def _now_iso(clock: Clock | None) -> str:
    now = clock.now() if clock is not None else datetime.now(UTC)
    return now.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
