from __future__ import annotations

from typing import Any

from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.serializers import attempt_detail, feedback_bundle, practice_item_detail
from learnloop_sidecar.logging import log_event
from learnloop_sidecar.registry import method


class AttemptInput(ParamsModel):
    attempt_id: str


class TriggerRegradeInput(ParamsModel):
    attempt_id: str


class AddErrorEventInput(ParamsModel):
    attempt_id: str
    error_type: str
    severity: float = 0.5


class TriggerFollowupInput(ParamsModel):
    attempt_id: str


class RateFollowupInput(ParamsModel):
    attempt_id: str
    useful: bool


class ReportUnresolvedCauseInput(ParamsModel):
    factor_id: str
    response: str
    candidate_index: int | None = None


class ContestCausalDiagnosisInput(ParamsModel):
    attempt_id: str
    response: str


@method("get_feedback", AttemptInput)
def get_feedback(ctx: SidecarContext, params: AttemptInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    attempt = repository.fetch_practice_attempt(params.attempt_id)
    session_id = attempt.get("session_id") if attempt is not None else None
    repository.record_feedback_shown(params.attempt_id, session_id=session_id)
    bundle = feedback_bundle(vault, repository, params.attempt_id)
    log_event(
        "feedback_shown",
        session_id=session_id,
        attempt_id=params.attempt_id,
        practice_item_id=bundle.get("practiceItemId"),
        feedback_md=bundle.get("feedbackMd"),
        followup_queued=bundle.get("followupQueued"),
        triggered_actions=(bundle.get("surprise") or {}).get("triggeredActions"),
        suppressed_actions=(bundle.get("surprise") or {}).get("suppressedActions"),
    )
    return bundle


@method("get_attempt", AttemptInput)
def get_attempt(ctx: SidecarContext, params: AttemptInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    return attempt_detail(vault, repository, params.attempt_id)


@method("report_unresolved_cause", ReportUnresolvedCauseInput)
def report_unresolved_cause(
    ctx: SidecarContext, params: ReportUnresolvedCauseInput
) -> dict[str, Any]:
    from learnloop.services.causal_attribution import (
        record_unresolved_cause_self_report,
    )

    vault, repository = ctx.require_vault()
    try:
        result = record_unresolved_cause_self_report(
            vault,
            repository,
            factor_id=params.factor_id,
            response=params.response,
            candidate_index=params.candidate_index,
        )
    except ValueError as exc:
        raise SidecarError("invalid_unresolved_cause_report", str(exc)) from exc
    # §5.6 arm (c): "I believed one of these" is the learner-confirmation half of
    # durable promotion. It promotes only in conjunction with a deterministic
    # proof that the response necessarily instantiates that same rule, so this
    # call is a no-op unless the episode's selected repair was verifier-proved.
    # Run here rather than inside the recorder because the confirmation must be
    # persisted first — a promotion is downstream of the evidence, never a
    # precondition for storing it.
    from learnloop.services.durable_promotion import (
        apply_proved_and_confirmed_promotion,
    )

    factor = repository.unresolved_cause_factor(params.factor_id)
    attempt_id = str((factor or {}).get("attempt_id") or "")
    if attempt_id:
        apply_proved_and_confirmed_promotion(
            vault, repository, attempt_id=attempt_id
        )
    return result


@method("contest_causal_diagnosis", ContestCausalDiagnosisInput)
def contest_causal_diagnosis(
    ctx: SidecarContext, params: ContestCausalDiagnosisInput
) -> dict[str, Any]:
    from learnloop.services.causal_attribution import (
        record_causal_diagnosis_contest,
    )

    vault, repository = ctx.require_vault()
    try:
        return record_causal_diagnosis_contest(
            vault,
            repository,
            attempt_id=params.attempt_id,
            response=params.response,
        )
    except ValueError as exc:
        raise SidecarError("invalid_causal_diagnosis_contest", str(exc)) from exc


@method("trigger_regrade", TriggerRegradeInput)
def trigger_regrade(ctx: SidecarContext, params: TriggerRegradeInput) -> dict[str, Any]:
    from learnloop.services.regrade import _regrade_attempt
    from learnloop_sidecar.handlers.ai_providers import (
        client_for_provider,
        grading_source_for_provider,
        provider_label,
        ready_grading_provider,
    )

    vault, repository = ctx.require_vault()
    attempt = repository.fetch_practice_attempt(params.attempt_id)
    if attempt is None:
        raise SidecarError("not_found", f"Attempt {params.attempt_id} not found.")
    provider_name, runtime, client = ready_grading_provider(vault, override=ctx.grading_provider_override)
    if not runtime.ready:
        label = provider_label(provider_name)
        raise SidecarError("ai_unavailable", f"{label} is {runtime.status}; regrade requires an AI provider.")
    client = client or client_for_provider(vault, provider_name)
    if client is None:
        label = provider_label(provider_name)
        raise SidecarError("ai_unavailable", f"{label} client is unavailable; regrade requires an AI provider.")
    _regrade_attempt(
        vault,
        repository,
        attempt,
        runtime=runtime,
        client=client,
        grading_source=grading_source_for_provider(provider_name),
        clock=None,
    )
    return feedback_bundle(vault, repository, params.attempt_id)


@method("trigger_followup", TriggerFollowupInput)
def trigger_followup(ctx: SidecarContext, params: TriggerFollowupInput) -> dict[str, Any]:
    """Manually force a diagnostic follow-up for one attempt.

    The user invokes this from the feedback screen when the automatic
    intervention gate did not fire but they still want a diagnostic item. It
    reuses the standard selection logic with every gate bypassed, and logs the
    surprise/gate context so the thresholds can be retuned against real
    override behaviour.
    """

    from types import SimpleNamespace

    from learnloop.services.followups import evaluate_attempt_intervention_followup

    vault, repository = ctx.require_vault()
    attempt = repository.fetch_practice_attempt(params.attempt_id)
    if attempt is None:
        raise SidecarError("not_found", f"Attempt {params.attempt_id} not found.")

    session_id = attempt.get("session_id")
    surprise = repository.latest_attempt_surprise(params.attempt_id) or {}
    debug_payload = repository.attempt_debug_payload(params.attempt_id) or {}
    error_events = repository.error_events_for_attempt(params.attempt_id)
    result_shim = SimpleNamespace(
        attempt_id=params.attempt_id,
        learning_object_id=attempt["learning_object_id"],
        practice_item_id=attempt["practice_item_id"],
        surprise_direction=surprise.get("surprise_direction"),
        bayesian_surprise=surprise.get("bayesian_surprise") or 0.0,
        grader_confidence=attempt.get("grader_confidence"),
        error_event_ids=[event["id"] for event in error_events],
        correctness=attempt.get("correctness") or 0.0,
        debug_payload=debug_payload,
    )
    decision = evaluate_attempt_intervention_followup(
        vault,
        repository,
        result=result_shim,
        session_id=session_id,
        manual_override=True,
    )
    gate = decision.gate_diagnostics or {}
    log_event(
        "manual_followup_triggered",
        session_id=session_id,
        attempt_id=params.attempt_id,
        practice_item_id=attempt["practice_item_id"],
        learning_object_id=attempt["learning_object_id"],
        outcome="queued" if decision.triggered else ("need_recorded" if decision.need_id else "no_item"),
        queued_practice_item_id=decision.practice_item_id,
        need_id=decision.need_id,
        intent=decision.intent,
        # Surprise vs. threshold gap.
        bayesian_surprise=gate.get("bayesian_surprise"),
        surprise_direction=gate.get("surprise_direction"),
        tau_followup_nats=gate.get("tau_followup_nats"),
        # Grader confidence + gate status.
        grader_confidence=gate.get("grader_confidence"),
        would_auto_fire=gate.get("would_auto_fire"),
        would_suppress=gate.get("would_suppress"),
        natural_trigger_reasons=gate.get("natural_trigger_reasons"),
        # Item / facet context.
        target_facets=gate.get("target_facets"),
        max_error_severity=gate.get("max_error_severity"),
        rubric_score=attempt.get("rubric_score"),
        correctness=attempt.get("correctness"),
        triggered_actions=decision.triggered_actions,
    )
    return feedback_bundle(vault, repository, params.attempt_id)


class StartPrimedRetryInput(ParamsModel):
    attempt_id: str


@method("start_primed_retry", StartPrimedRetryInput)
def start_primed_retry(ctx: SidecarContext, params: StartPrimedRetryInput) -> dict[str, Any]:
    """Serve a sibling item for a primed retry from the source-review panel.

    Picks another item on the missed attempt's learning object (preferring the
    intervention need's target facets, then never/least-recently attempted).
    When the LO has no sibling, generates one on demand through the authoring
    proposal pipeline and auto-accepts it — the retry deliberately stays a real
    vault item so attempt provenance keeps working. The frontend submits the
    resulting attempt with primed=true.
    """

    from learnloop.services.practice_generation import (
        PracticeExpansionError,
        generate_diagnostic_practice_proposal,
        generate_post_probe_practice_proposal,
    )
    from learnloop.codex.client import CodexUnavailable
    from learnloop.services.patches import PatchApplicationError
    from learnloop.services.proposals import accept_items
    from learnloop_sidecar.handlers.ai_providers import provider_label, ready_grading_provider

    vault, repository = ctx.require_vault()
    attempt = repository.fetch_practice_attempt(params.attempt_id)
    if attempt is None:
        raise SidecarError("not_found", f"Attempt {params.attempt_id} not found.")
    learning_object_id = attempt["learning_object_id"]
    need = repository.intervention_need_for_attempt(params.attempt_id)
    generated = False

    sibling = _pick_primed_sibling(vault, repository, attempt, need)
    if sibling is None:
        provider_name, runtime, client = ready_grading_provider(vault, override=ctx.grading_provider_override)
        if not runtime.ready or client is None:
            return _primed_retry_unavailable(
                params, attempt, f"{provider_label(provider_name)} is unavailable; no other item exists for this topic yet."
            )
        try:
            if need is not None and need.get("status") == "pending":
                result = generate_diagnostic_practice_proposal(
                    vault.root, client, learning_object_id=learning_object_id, max_needs=1
                )
                patch_id = result.patch_id
            else:
                patch_id = generate_post_probe_practice_proposal(
                    vault.root, client, learning_object_ids=[learning_object_id], max_new_per_lo=1
                ).patch_id
            accept_items(vault.root, patch_id)
        except (PracticeExpansionError, PatchApplicationError, CodexUnavailable, TimeoutError) as exc:
            return _primed_retry_unavailable(params, attempt, str(exc))
        # Acceptance wrote vault files; refresh the in-memory vault (offline, no
        # Codex probe) and re-run selection over the now-larger item pool.
        ctx.reload(maintenance=False)
        vault, repository = ctx.require_vault()
        generated = True
        sibling = _pick_primed_sibling(vault, repository, attempt, need)
        if sibling is None:
            return _primed_retry_unavailable(params, attempt, "Generation produced no item for this learning object.")

    log_event(
        "primed_retry_started",
        session_id=attempt.get("session_id"),
        attempt_id=params.attempt_id,
        learning_object_id=learning_object_id,
        source_practice_item_id=attempt["practice_item_id"],
        practice_item_id=sibling.id,
        generated=generated,
    )
    return {
        "available": True,
        "generated": generated,
        "practice_item": practice_item_detail(vault, repository, sibling.id),
    }


def _pick_primed_sibling(vault, repository, attempt: dict[str, Any], need: dict[str, Any] | None):
    """Sibling items on the same LO, best-first: target-facet coverage, then freshness."""

    target_facets = {
        vault.canonical_facet_id(facet) for facet in ((need or {}).get("target_facets") or [])
    }
    candidates = []
    for item in vault.practice_items.values():
        if item.learning_object_id != attempt["learning_object_id"] or item.id == attempt["practice_item_id"]:
            continue
        state = repository.practice_item_state(item.id)
        if state is not None and not state.active:
            continue
        covers = bool(target_facets & {vault.canonical_facet_id(facet) for facet in item.evidence_facets})
        last_attempt_at = state.last_attempt_at if state is not None else None
        candidates.append((0 if covers else 1, last_attempt_at or "", item.id, item))
    if not candidates:
        return None
    return min(candidates)[3]


def _primed_retry_unavailable(params: StartPrimedRetryInput, attempt: dict[str, Any], reason: str) -> dict[str, Any]:
    log_event(
        "primed_retry_unavailable",
        session_id=attempt.get("session_id"),
        attempt_id=params.attempt_id,
        learning_object_id=attempt["learning_object_id"],
        reason=reason,
    )
    return {"available": False, "generated": False, "reason": reason, "practice_item": None}


@method("rate_followup", RateFollowupInput)
def rate_followup(ctx: SidecarContext, params: RateFollowupInput) -> dict[str, Any]:
    """One-tap "was this follow-up useful?" label from the feedback screen.

    Every rating is a gate-fitter training example: a useful auto-fired
    follow-up is a true positive, a not-useful one a false positive — the
    complement of the manual-override false-negative stream.
    """

    vault, repository = ctx.require_vault()
    attempt = repository.fetch_practice_attempt(params.attempt_id)
    if attempt is None:
        raise SidecarError("not_found", f"Attempt {params.attempt_id} not found.")
    gate_attempt_id = repository.followup_source_attempt(params.attempt_id)
    repository.upsert_followup_rating(
        attempt_id=params.attempt_id,
        gate_attempt_id=gate_attempt_id,
        useful=params.useful,
    )
    log_event(
        "followup_rated",
        session_id=attempt.get("session_id"),
        attempt_id=params.attempt_id,
        practice_item_id=attempt["practice_item_id"],
        learning_object_id=attempt["learning_object_id"],
        gate_attempt_id=gate_attempt_id,
        useful=params.useful,
    )
    return feedback_bundle(vault, repository, params.attempt_id)


@method("add_error_event", AddErrorEventInput)
def add_error_event(ctx: SidecarContext, params: AddErrorEventInput) -> dict[str, Any]:
    from learnloop.clock import utc_now_iso
    from learnloop.ids import new_ulid

    vault, repository = ctx.require_vault()
    attempt = repository.fetch_practice_attempt(params.attempt_id)
    if attempt is None:
        raise SidecarError("not_found", f"Attempt {params.attempt_id} not found.")
    now = utc_now_iso()
    repository.insert_error_event({
        "id": new_ulid(),
        "attempt_id": params.attempt_id,
        "learning_object_id": attempt["learning_object_id"],
        "error_type": params.error_type,
        "severity": params.severity,
        "is_misconception": False,
        "repair_plan": None,
        "status": "active",
        "created_at": now,
        "updated_at": now,
    })
    return feedback_bundle(vault, repository, params.attempt_id)
