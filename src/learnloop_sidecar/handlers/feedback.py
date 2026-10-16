from __future__ import annotations

import logging
from typing import Any

from learnloop.clock import utc_now_iso
from learnloop.substrate.instrument_serving import unservable_refusal
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, to_camel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.serializers import attempt_detail, feedback_bundle, practice_item_detail
from learnloop_sidecar.logging import log_event
from learnloop_sidecar.registry import method


class AttemptInput(ParamsModel):
    attempt_id: str


class FeedbackInput(ParamsModel):
    attempt_id: str
    # Slice 1 M2: the feedback view re-reads the bundle when an asynchronous
    # diagnosis lands; that refresh is not another open of the screen.
    record_open: bool = True


class AnswerClarificationInput(ParamsModel):
    attempt_id: str
    answer_md: str


class TriggerRegradeInput(ParamsModel):
    attempt_id: str
    # UX Phase 4 "I think I was right" (spec §7.5): the learner's one-line
    # reason. Recorded before the regrade (kept even if the grader is
    # unavailable) and never handed to the grader, which stays blind to it.
    # Absent: the plain regrade, exactly as before (records nothing).
    learner_reason: str | None = None
    # The client's key for this one contest (Codex review F7): a retry after a
    # failed or unknown delivery reuses it, so the contest is recorded and
    # queued once. Absent: a fresh key (no retry identity).
    contest_id: str | None = None


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


class SubmitElicitingResponseInput(ParamsModel):
    attempt_id: str
    suggestion_index: int
    response_md: str


def _attach_common_repair(
    repository: Any, attempt_id: str, bundle: dict[str, Any]
) -> None:
    """Journey B: surface the already-decided common-repair recommendation.

    Thin camel-casing shim over the shared read
    (``followups.common_repair_recommendation``), which the §5.7 block-end
    released-feedback payload also uses — it reads the decision receipt the
    post-attempt hook recorded (``followups._consult_common_repair``) and never
    calls the orchestrator, so re-viewing feedback cannot mint another receipt.
    Divergent and incomplete-mapping factors keep the existing
    learner-initiated ``causal_repair_status`` flow untouched.
    """

    from learnloop.diagnosis.followups import common_repair_recommendation

    causal = bundle.get("causalFeedback")
    if not isinstance(causal, dict):
        return
    hypotheses = causal.get("causalHypotheses") or [{}]
    recommendation = common_repair_recommendation(
        repository,
        attempt_id,
        probe_need=causal.get("probeNeed"),
        fallback_misconception_id=str(
            (hypotheses[0] or {}).get("hypothesisId") or ""
        ),
        surface="feedback_common_repair",
    )
    if recommendation is not None:
        causal["commonRepair"] = to_camel(recommendation)


def _debit_repair_display_reveals(
    vault: Any, repository: Any, attempt: dict[str, Any], stored_feedback: dict[str, Any]
) -> None:
    """Charge the reveal ledger for the repair suggestions this screen shows.

    A repair suggestion declares an ``answer_reveal_budget`` — the fraction of
    the solution its lane is licensed to show — and until now that budget
    debited nothing anywhere. Showing the suggestion is when it is spent, so the
    first open of an attempt's feedback appends it to the ledger; the next
    attempt on the item then sees the exposure it was given.

    Best-effort: a bookkeeping failure must never cost the learner their
    feedback screen."""

    from learnloop.attempts.reveal_ledger import record_repair_display_reveals

    try:
        from learnloop.diagnosis.recurrence.display import displayed_repair_suggestions, is_escalation_suggestion
        from learnloop.diagnosis.split.card import debit_escalated_repairs

        practice_item_id = str(attempt.get("practice_item_id") or "") or None
        item = vault.practice_items.get(practice_item_id) if practice_item_id else None
        shown = displayed_repair_suggestions(vault, repository, str(attempt["id"]), stored_feedback.get("repair_suggestions"))
        # Slice 2 T1: an escalated repair is charged once on its own basis.
        debit_escalated_repairs(
            repository, attempt=attempt, repair_suggestions=[row for row in shown if is_escalation_suggestion(row)],
            learning_object_id=item.learning_object_id if item is not None else None,
        )
        suggestions = [row for row in shown if not is_escalation_suggestion(row)]
        diagnosis_ids = {
            str(value.get("id")).split(":")[1]
            for value in suggestions
            if isinstance(value, dict) and str(value.get("id") or "").startswith("diagnosis:")
        }
        if diagnosis_ids:
            # Slice 1 M2: a diagnosis's repairs are charged once, by whichever
            # surface displays them first (the card may already have).
            from learnloop.diagnosis.split.card import diagnosis_repairs_debited

            if any(diagnosis_repairs_debited(repository, str(attempt["id"]), value) for value in diagnosis_ids):
                return
        record_repair_display_reveals(
            repository,
            attempt_id=str(attempt["id"]),
            practice_item_id=practice_item_id,
            learning_object_id=item.learning_object_id if item is not None else None,
            repair_suggestions=suggestions,
        )
    except Exception:  # pragma: no cover - defensive
        logging.getLogger(__name__).warning(
            "failed to debit repair-display reveals for attempt %s",
            attempt.get("id"),
            exc_info=True,
        )


@method("get_feedback", FeedbackInput)
def get_feedback(ctx: SidecarContext, params: FeedbackInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    attempt = repository.fetch_practice_attempt(params.attempt_id)
    session_id = attempt.get("session_id") if attempt is not None else None
    # Read the metadata BEFORE recording the open: `record_feedback_shown` sets
    # `first_shown_at`, so afterwards there is no way left to tell a first open
    # from a reopen.
    stored_feedback = repository.fetch_attempt_feedback_metadata(params.attempt_id) or {}
    first_show = not stored_feedback.get("first_shown_at")
    if params.record_open:
        repository.record_feedback_shown(params.attempt_id, session_id=session_id)
    if params.record_open and first_show and attempt is not None:
        _debit_repair_display_reveals(vault, repository, attempt, stored_feedback)
    bundle = feedback_bundle(vault, repository, params.attempt_id)
    _attach_common_repair(repository, params.attempt_id, bundle)
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


@method("get_attempt_trace_evidence", AttemptInput)
def get_attempt_trace_evidence(ctx: SidecarContext, params: AttemptInput) -> dict[str, Any]:
    """A6 trace observations on one attempt, plus the sentence they earned.

    Spec: ``spec_measurement_efficiency_v1.md`` §3.A6; plan item 6.2.

    A separate read rather than another field on ``feedback_bundle``: that
    bundle is shared by the CLI, the inspector and exam review, none of which
    owe the learner the reward line, and A6's whole cost model rests on the
    reward being a *visible* thing the feedback surface says rather than a
    number every consumer has to know how to ignore.

    ``reward`` is ``None`` — never a zero — when the grader saw nothing beyond
    the item's declared facets. "Your explanation demonstrated 0 additional
    facets" would be a punishment for volunteering, which is precisely the
    incentive rule 3 exists to protect against.
    """

    from learnloop.attempts.trace_evidence import elicitation_reward

    _vault, repository = ctx.require_vault()
    attempt = repository.fetch_practice_attempt(params.attempt_id)
    if attempt is None:
        raise SidecarError("not_found", f"Attempt {params.attempt_id} not found.")
    observations = repository.trace_exercised_facets(params.attempt_id)
    return versioned(
        {
            "attempt_id": params.attempt_id,
            "observations": [
                {
                    "facet_id": row["facet_id"],
                    "observation_scope": row["observation_scope"],
                    "criterion_id": row.get("criterion_id"),
                    "evidence": row.get("evidence") or "",
                    "source": row.get("source"),
                }
                for row in observations
            ],
            # Gated on the learner's own answer text: `observation_scope` says
            # whether the item declared the facet, not whether the learner
            # volunteered an explanation. Ungated, an attempt that was never
            # offered elicitation gets told "your explanation also demonstrated…"
            # about an explanation it does not have.
            "reward": elicitation_reward(
                observations, learner_answer_md=attempt.get("learner_answer_md") or ""
            ),
        }
    )


@method("get_grading_clarification", AttemptInput)
def get_grading_clarification(ctx: SidecarContext, params: AttemptInput) -> dict[str, Any]:
    """The one A8 question this attempt is waiting on, or ``None``.

    Spec: ``spec_measurement_efficiency_v1.md`` §3.A8; plan item 6.3.

    Only a *pending* question is returned. A timed-out one is dropped by
    ``pending_clarification`` because the grade it hedged has already resolved
    to the abstention that triggered it, and re-offering the box would invite an
    answer that can no longer change anything — a worse outcome than never
    asking, since the learner would have spent the effort for nothing.
    """

    from learnloop.attempts.clarification import pending_clarification

    _vault, repository = ctx.require_vault()
    if repository.fetch_practice_attempt(params.attempt_id) is None:
        raise SidecarError("not_found", f"Attempt {params.attempt_id} not found.")
    record = pending_clarification(repository, params.attempt_id)
    return versioned(
        {
            "clarification": (
                record.as_dict(now=utc_now_iso()) if record is not None else None
            )
        }
    )


@method("answer_grading_clarification", AnswerClarificationInput)
def answer_grading_clarification(
    ctx: SidecarContext, params: AnswerClarificationInput
) -> dict[str, Any]:
    """Record the learner's answer and re-grade the attempt with it in hand.

    Spec: ``spec_measurement_efficiency_v1.md`` §3.A8; plan item 6.3.

    An unavailable grading provider is deliberately not an error here. The
    answer is the un-backfillable half of the exchange (standing constraint 6)
    and the re-grade can always be re-run, so the service is called with
    ``client=None`` and the words are persisted anyway; the response reports the
    outage so the surface can say the grade is still provisional rather than
    implying the question resolved it.

    Every other terminal state is passed through untranslated — ``resolved``,
    ``abstained``, ``regrade_failed``. ``abstained`` in particular must not be
    smoothed into success: a learner may answer and the grader may still be
    unable to name a cause, and that is a real result, not a failure of the
    exchange.
    """

    from learnloop.attempts.clarification import answer_clarification
    from learnloop_sidecar.handlers.ai_providers import (
        grading_source_for_provider,
        provider_label,
        ready_grading_provider,
    )

    vault, repository = ctx.require_vault()
    if repository.fetch_practice_attempt(params.attempt_id) is None:
        raise SidecarError("not_found", f"Attempt {params.attempt_id} not found.")
    answer_md = params.answer_md.strip()
    if not answer_md:
        # Skipping is a first-class, cost-free choice made by *not calling this*.
        # An empty submission is a client bug, and accepting it would burn the
        # attempt's single question on nothing.
        raise SidecarError(
            "validation_error",
            "A clarification answer cannot be empty — skipping leaves the grade as it stands.",
        )
    provider_name, runtime, client = ready_grading_provider(
        vault, override=ctx.grading_provider_override
    )
    unavailable = (
        None
        if runtime.ready and client is not None
        else f"{provider_label(provider_name)} is unavailable; your answer is saved and the grade stays provisional until it is re-graded."
    )
    try:
        result = answer_clarification(
            vault,
            repository,
            attempt_id=params.attempt_id,
            answer_md=answer_md,
            runtime=runtime,
            client=client if unavailable is None else None,
            grading_source=grading_source_for_provider(provider_name),
        )
    except ValueError as exc:
        # Already answered, expired, or never asked — all three mean the window
        # this box belongs to has closed, and all three must read differently
        # from "the regrade failed".
        raise SidecarError("clarification_unanswerable", str(exc)) from exc
    log_event(
        "grading_clarification_answered",
        attempt_id=params.attempt_id,
        clarification_id=result.get("clarification_id"),
        outcome=result.get("outcome"),
        regraded=result.get("regraded"),
        grading_provider=provider_name,
    )
    return versioned(
        {
            "clarification_id": result.get("clarification_id"),
            "outcome": result.get("outcome"),
            "regraded": bool(result.get("regraded")),
            "error": result.get("error") or unavailable,
            "feedback": feedback_bundle(vault, repository, params.attempt_id),
        }
    )


@method("report_unresolved_cause", ReportUnresolvedCauseInput)
def report_unresolved_cause(
    ctx: SidecarContext, params: ReportUnresolvedCauseInput
) -> dict[str, Any]:
    from learnloop.diagnosis.causal_attribution import (
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
    from learnloop.tutor.durable_promotion import (
        apply_proved_and_confirmed_promotion,
    )

    factor = repository.unresolved_cause_factor(params.factor_id)
    attempt_id = str((factor or {}).get("attempt_id") or "")
    if attempt_id:
        apply_proved_and_confirmed_promotion(
            vault, repository, attempt_id=attempt_id
        )
    return result


@method("submit_eliciting_response", SubmitElicitingResponseInput)
def submit_eliciting_response(
    ctx: SidecarContext, params: SubmitElicitingResponseInput
) -> dict[str, Any]:
    """The learner's unaided answer to an eliciting repair's question.

    An eliciting suggestion withholds the corrected work and asks one question
    instead; this is where the answer lands. It is recorded as a factor-response
    engagement signal on the same ``causal_attribution_reports`` seam as
    ``report_unresolved_cause`` — the learner's own account, attached to the open
    factor.

    Deliberately NOT a grade. Nothing here scores the response, resolves the
    factor, or confirms a candidate: an unaided response is evidence about the
    factor, and the only machinery licensed to convert evidence into a repair
    verdict is the cold verification lane. The response's independence is
    checked against the reveal ledger and stamped on the record, so a response
    typed after the answer was on screen is stored as what it is.
    """

    from learnloop.diagnosis.causal_attribution import record_eliciting_response

    vault, repository = ctx.require_vault()
    if repository.fetch_practice_attempt(params.attempt_id) is None:
        raise SidecarError("not_found", f"Attempt {params.attempt_id} not found.")
    try:
        result = record_eliciting_response(
            vault,
            repository,
            attempt_id=params.attempt_id,
            suggestion_index=params.suggestion_index,
            response_md=params.response_md,
        )
    except ValueError as exc:
        raise SidecarError("invalid_eliciting_response", str(exc)) from exc
    log_event(
        "eliciting_response_recorded",
        attempt_id=params.attempt_id,
        factor_id=result.get("factor_id"),
        admissible=result.get("admissible_as_independent"),
    )
    return versioned(
        {
            **result,
            "feedback": feedback_bundle(vault, repository, params.attempt_id),
        }
    )


@method("contest_causal_diagnosis", ContestCausalDiagnosisInput)
def contest_causal_diagnosis(
    ctx: SidecarContext, params: ContestCausalDiagnosisInput
) -> dict[str, Any]:
    from learnloop.diagnosis.causal_attribution import (
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
    vault, repository = ctx.require_vault()
    attempt = repository.fetch_practice_attempt(params.attempt_id)
    if attempt is None:
        raise SidecarError("not_found", f"Attempt {params.attempt_id} not found.")
    if params.learner_reason is not None:
        return _contest_grade(ctx, vault, repository, attempt, params)
    _run_regrade(ctx, vault, repository, attempt)
    return feedback_bundle(vault, repository, params.attempt_id)


def _run_regrade(ctx: SidecarContext, vault, repository, attempt: dict[str, Any]) -> None:
    """The existing regrade (learner-blind), or ``ai_unavailable``."""

    from learnloop.attempts.regrade import regrade_attempt
    from learnloop_sidecar.handlers.ai_providers import (
        client_for_provider,
        grading_source_for_provider,
        provider_label,
        ready_grading_provider,
    )

    provider_name, runtime, client = ready_grading_provider(vault, override=ctx.grading_provider_override)
    if not runtime.ready:
        label = provider_label(provider_name)
        raise SidecarError("ai_unavailable", f"{label} is {runtime.status}; regrade requires an AI provider.")
    client = client or client_for_provider(vault, provider_name)
    if client is None:
        label = provider_label(provider_name)
        raise SidecarError("ai_unavailable", f"{label} client is unavailable; regrade requires an AI provider.")
    regrade_attempt(
        vault,
        repository,
        attempt,
        runtime=runtime,
        client=client,
        grading_source=grading_source_for_provider(provider_name),
        clock=None,
    )


def _contest_grade(ctx: SidecarContext, vault, repository, attempt: dict[str, Any],
                   params: TriggerRegradeInput) -> dict[str, Any]:
    """"I think I was right" (spec §7.5): keep the learner's reason, look again
    in place, and send what the look did not settle to the owner's review.

    1. The reason is recorded first (the claim ledger, presentation-only),
       under the client's contest key, so a retry records it once. Nothing
       recorded is ``contest_not_recorded``: the client keeps the reason.
    2. The existing regrade runs, blind to the reason. A grader that cannot
       run (or fails) is not an error any more: the contest is kept.
    3. Unless the answer now reads right, the grade enters the existing
       grade-review queue (``grade_resolution.flag_observation_for_review``:
       ``learnloop grading reviews`` / ``adjudicate``), where the owner's
       adjudication can correct the record (Codex review F3).

    The bundle carries ``contest``: what was recorded, whether the grader
    looked again and whether the grade was sent for review.
    """

    from learnloop.ids import new_ulid

    attempt_id = str(attempt["id"])
    contest_id = (params.contest_id or "").strip() or new_ulid()
    try:
        presentation_id = _record_grade_contest(
            repository, attempt_id, (params.learner_reason or "").strip(),
            contest_id=contest_id, session_id=attempt.get("session_id"),
        )
    except Exception as exc:  # noqa: BLE001 - nothing kept: say so
        logging.getLogger(__name__).warning("grade contest for %s was not recorded", attempt_id, exc_info=True)
        raise SidecarError(
            "contest_not_recorded", "Your note couldn't be saved. Try again.", retryable=True
        ) from exc
    regraded = True
    try:
        _run_regrade(ctx, vault, repository, attempt)
    except SidecarError as exc:
        if exc.code != "ai_unavailable":
            raise
        regraded = False
    except Exception:  # noqa: BLE001 - the contest is kept; the owner reviews it
        logging.getLogger(__name__).warning("contest regrade failed for %s", attempt_id, exc_info=True)
        regraded = False
    bundle = feedback_bundle(vault, repository, attempt_id)
    review_requested = False
    if not _contest_upheld(bundle):
        review_requested = _request_grade_review(repository, attempt_id, contest_id, presentation_id)
    log_event(
        "grade_contest_settled", attempt_id=attempt_id, regraded=regraded, review_requested=review_requested,
    )
    bundle["contest"] = to_camel(
        {"recorded": True, "regraded": regraded, "review_requested": review_requested}
    )
    return bundle


def _contest_upheld(bundle: dict[str, Any]) -> bool:
    """The answer now reads right (the learner's claim holds): full marks and
    not held for review."""

    max_points = float(bundle.get("maxPoints") or 0)
    score = float(bundle.get("rubricScore") or 0)
    correctness = float(bundle.get("correctness") or 0)
    full = score >= max_points if max_points > 0 else correctness >= 1.0
    return bool(full and correctness >= 1.0 and not bundle.get("heldForReview"))


def _request_grade_review(repository, attempt_id: str, contest_id: str, presentation_id: str) -> bool:
    """Queue the contested grade in the existing grade-review intake. False
    when the attempt has no graded observation to queue (a pre-P0.2 grade)."""

    from learnloop.attempts.grade_resolution import flag_observation_for_review

    observation = repository.observation_by_attempt(attempt_id)
    if observation is None:
        return False
    return flag_observation_for_review(
        repository,
        observation_id=str(observation["id"]),
        reason="learner_grade_contest",
        detail={"contest_id": contest_id, "contest_presentation_id": presentation_id},
    ) is not None


#: The claim type a learner's "I think I was right" is kept under.
GRADE_CONTEST_CLAIM_TYPE = "grade_contest"


def _record_grade_contest(repository, attempt_id: str, reason: str, *, contest_id: str,
                          session_id: str | None) -> str:
    """Keep a learner's grade contest in the claim ledger (presented, then
    answered); returns the presentation id.

    The learner started it, so the attention budget that paces system-asked
    claims does not apply: each contest is its own visit, never suppressed, and
    no cooldown hides a second one on the same answer. The contest key makes it
    idempotent: a retry finds the same presentation and its response.
    """

    from learnloop.learner.hypothesis_claims import present_claims, record_response

    [presentation] = present_claims(
        repository,
        [
            {
                "claim_class": "ledger_fact",
                "claim_type": GRADE_CONTEST_CLAIM_TYPE,
                "claim_ref": {"attemptId": attempt_id, "kind": GRADE_CONTEST_CLAIM_TYPE},
                "claim_version": f"{GRADE_CONTEST_CLAIM_TYPE}:{contest_id}",
                "producer_version": "ux-phase4",
                "surface": "feedback_contest",
                "temperature": "hot",
                "visible_at": utc_now_iso(),
                "claim_text": "I think I was right",
            }
        ],
        session_id=None,
        visit_id=f"grade-contest:{attempt_id}:{contest_id}",
        session_card_budget=1,
        claim_cooldown_days=0,
    )
    presentation_id = str(presentation["presentation_id"])
    already = any(
        event.get("event_type") == "responded" and event.get("presentation_id") == presentation_id
        for event in repository.list_hypothesis_events()
    )
    if not already:
        record_response(repository, presentation_id, {"response": "i_think_i_was_right", "reason": reason})
    log_event("grade_contest_recorded", attempt_id=attempt_id, session_id=session_id, has_reason=bool(reason))
    return presentation_id


@method("record_answer_display", AttemptInput)
def record_answer_display(ctx: SidecarContext, params: AttemptInput) -> dict[str, Any]:
    """Feedback's plain surface showed the full answer (UX Phase 4, Codex
    review F1): debit the reveal ledger, once per attempt.

    The expected answer itself (amount 1.0), linked to the attempt whose
    feedback showed it (``reveal_ledger.record_answer_display_reveal``, the
    TUI's worked-answer writer): the next attempt on the item is primed, and a
    later unaided response is stamped as produced after the answer was seen.
    """

    from learnloop.attempts.reveal_ledger import record_answer_display_reveal

    _vault, repository = ctx.require_vault()
    attempt = repository.fetch_practice_attempt(params.attempt_id)
    if attempt is None:
        raise SidecarError("not_found", f"Attempt {params.attempt_id} not found.")
    record_answer_display_reveal(
        repository,
        attempt_id=params.attempt_id,
        practice_item_id=str(attempt["practice_item_id"]),
        learning_object_id=str(attempt.get("learning_object_id") or "") or None,
        basis="feedback_full_answer:desktop",
    )
    return versioned({"recorded": True})


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

    from learnloop.diagnosis.followups import evaluate_attempt_intervention_followup

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

    from learnloop.content.authoring.practice_generation import (
        PracticeExpansionError,
        generate_diagnostic_practice_proposal,
        generate_post_probe_practice_proposal,
    )
    from learnloop.ai.errors import CodexUnavailable
    from learnloop.content.proposals.patches import PatchApplicationError
    from learnloop.content.proposals.proposals import accept_items
    from learnloop_sidecar.handlers.ai_providers import provider_label, ready_grading_provider

    vault, repository = ctx.require_vault()
    attempt = repository.fetch_practice_attempt(params.attempt_id)
    if attempt is None:
        raise SidecarError("not_found", f"Attempt {params.attempt_id} not found.")
    learning_object_id = attempt["learning_object_id"]
    need = repository.intervention_need_for_attempt(params.attempt_id)
    generated = False

    sibling, unservable_skips = _pick_primed_sibling(vault, repository, attempt, need)
    source_first = None
    if sibling is None and need is not None and need.get("status") == "pending":
        # Canonical sources S2b (mvp-0.19): the learner's own textbook
        # exercises first; generation only when none passes every check.
        source_first = _source_first(ctx, vault, repository, need)
        if source_first is not None and source_first.get("outcome") == "fulfilled":
            ctx.reload(maintenance=False)
            vault, repository = ctx.require_vault()
            sibling, unservable_skips = _pick_primed_sibling(vault, repository, attempt, need)
            if sibling is not None and sibling.id == source_first.get("practice_item_id"):
                _record_need_served(vault, repository, need, source_first, attempt)
    if sibling is None:
        provider_name, runtime, client = ready_grading_provider(vault, override=ctx.grading_provider_override)
        if not runtime.ready or client is None:
            return _primed_retry_unavailable(
                params,
                attempt,
                f"{provider_label(provider_name)} is unavailable; no other item exists for this topic yet.",
                unservable_skips=unservable_skips,
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
            return _primed_retry_unavailable(params, attempt, str(exc), unservable_skips=unservable_skips)
        # Acceptance wrote vault files; refresh the in-memory vault (offline, no
        # Codex probe) and re-run selection over the now-larger item pool.
        ctx.reload(maintenance=False)
        vault, repository = ctx.require_vault()
        generated = True
        # Re-selection sees the pre-generation siblings again, so its skip list
        # supersedes the first one rather than adding to it — concatenating would
        # report every refused sibling twice.
        sibling, unservable_skips = _pick_primed_sibling(vault, repository, attempt, need)
        if sibling is None:
            return _primed_retry_unavailable(
                params,
                attempt,
                "Generation produced no item for this learning object.",
                unservable_skips=unservable_skips,
            )

    log_event(
        "primed_retry_started",
        session_id=attempt.get("session_id"),
        attempt_id=params.attempt_id,
        learning_object_id=learning_object_id,
        source_practice_item_id=attempt["practice_item_id"],
        practice_item_id=sibling.id,
        generated=generated,
        unservable_skips=unservable_skips,
    )
    return {
        "available": True,
        "generated": generated,
        **({"source_first": source_first} if source_first is not None else {}),
        "practice_item": practice_item_detail(vault, repository, sibling.id),
        # Present on the SUCCESS response too: the retry the learner got is not
        # the retry the picker would have chosen, and the record of what was
        # refused is what makes that visible instead of silent.
        "unservable_skips": unservable_skips,
    }


def _source_first(ctx: SidecarContext, vault: Any, repository: Any, need: dict[str, Any]) -> dict[str, Any] | None:
    """S2b's step in the primed-retry adapter; None when it is not active."""

    from learnloop.instructional.needs import fulfil_need_from_sources, source_first_active

    if not source_first_active(vault):
        return None
    try:
        return fulfil_need_from_sources(vault, repository, need, path="primed_retry")
    except Exception as exc:  # noqa: BLE001 - generation proceeds exactly as today
        return {"outcome": "generate", "reason": f"source-first failed: {type(exc).__name__}"}


def _record_need_served(vault: Any, repository: Any, need: dict[str, Any], outcome: dict[str, Any],
                        attempt: dict[str, Any]) -> None:
    """S5: a need fulfilled from the sources and served (best effort)."""

    from learnloop.instructional.interventions import record_need_served

    try:
        record_need_served(vault, repository, need, practice_item_id=str(outcome["practice_item_id"]),
                           proposal_id=outcome.get("proposal_id"), session_id=attempt.get("session_id"))
    except Exception:  # noqa: BLE001 - telemetry never fails the serve
        import logging

        logging.getLogger(__name__).warning("intervention record failed", exc_info=True)


def _pick_primed_sibling(
    vault, repository, attempt: dict[str, Any], need: dict[str, Any] | None
) -> tuple[Any | None, list[dict[str, Any]]]:
    """Sibling items on the same LO, best-first.

    Ordering (deterministic, lowest key first): not attempted within the repair
    lane's :data:`~learnloop.diagnosis.remediation.RECENT_ATTEMPT_WINDOW` (an
    item answered minutes ago re-measures short-term memory, not the retry);
    covers a checkpoint the attempt's own repair selection targets (the
    checkpoint-precise signal the facet ranking used to ignore); covers the
    intervention need's target facets; least recently attempted; item id.

    Returns the pick AND the servability skips, because a primed retry is a
    selection path: the right response to an unrenderable sibling is to choose a
    different one, not to fail. Meas §3.A2/§3.A3 — serving an error hunt whose
    worked solution the surface drops asks the learner to repair work they cannot
    see while the grader marks every plant missed, and a primed retry writes that
    straight onto an attempt the learner already got wrong.

    The skip list is returned rather than logged because this path already has a
    learner-visible "why not" channel (``reason`` on the unavailable response),
    and a skip nobody can see is indistinguishable from the picker being broken —
    the LO has items, none is offered, and nothing says which rule ate them.
    """

    from learnloop.clock import SystemClock, parse_utc
    from learnloop.diagnosis.guided_redo import (
        diagnosis_receipt,
        item_step_checkpoint_ids,
        selected_repair,
    )
    from learnloop.diagnosis.remediation import RECENT_ATTEMPT_WINDOW, item_checkpoints

    target_facets = {
        vault.canonical_facet_id(facet) for facet in ((need or {}).get("target_facets") or [])
    }
    selected = selected_repair(diagnosis_receipt(repository, str(attempt["id"])))
    targeted_checkpoints = set(
        item_step_checkpoint_ids(
            (selected or {}).get("repair_class")
            if isinstance((selected or {}).get("repair_class"), dict)
            else None
        )
    )
    now = SystemClock().now()
    candidates = []
    skipped: list[dict[str, Any]] = []
    for item in vault.practice_items.values():
        if item.learning_object_id != attempt["learning_object_id"] or item.id == attempt["practice_item_id"]:
            continue
        state = repository.practice_item_state(item.id)
        if state is not None and not state.active:
            continue
        refusal = unservable_refusal(item)
        if refusal is not None:
            skipped.append(refusal)
            continue
        covers = bool(target_facets & {vault.canonical_facet_id(facet) for facet in item.evidence_facets})
        covers_checkpoint = (
            bool(targeted_checkpoints & item_checkpoints(item))
            if targeted_checkpoints
            else False
        )
        last_attempt_at = state.last_attempt_at if state is not None else None
        attempted_recently = False
        if last_attempt_at:
            parsed = parse_utc(last_attempt_at)
            if parsed is not None:
                attempted_recently = now - parsed < RECENT_ATTEMPT_WINDOW
        candidates.append(
            (
                1 if attempted_recently else 0,
                0 if covers_checkpoint else 1,
                0 if covers else 1,
                last_attempt_at or "",
                item.id,
                item,
            )
        )
    if not candidates:
        return None, skipped
    return min(candidates, key=lambda entry: entry[:-1])[-1], skipped


def _primed_retry_unavailable(
    params: StartPrimedRetryInput,
    attempt: dict[str, Any],
    reason: str,
    *,
    unservable_skips: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    skips = unservable_skips or []
    if skips:
        # The learner-facing reason must name the cause it actually had. "No
        # other item exists for this topic yet" is false when siblings exist and
        # were refused, and that false reason is what would send someone looking
        # for an authoring bug instead of the missing renderer.
        reason = f"{reason} ({len(skips)} item(s) skipped: {skips[0]['remedy']})"
    log_event(
        "primed_retry_unavailable",
        session_id=attempt.get("session_id"),
        attempt_id=params.attempt_id,
        learning_object_id=attempt["learning_object_id"],
        reason=reason,
        unservable_skips=skips,
    )
    return {
        "available": False,
        "generated": False,
        "reason": reason,
        "practice_item": None,
        "unservable_skips": skips,
    }


class StartGuidedRedoInput(ParamsModel):
    attempt_id: str


@method("start_guided_redo", StartGuidedRedoInput)
def start_guided_redo_handler(
    ctx: SidecarContext, params: StartGuidedRedoInput
) -> dict[str, Any]:
    """Guided partial redo (Fix 3): serve the preserved-prefix redo context.

    Returns the learner's preserved work and the redo instruction derived from
    the stored repair selection, and commits a remediation episode for the
    diagnosed case (establishing one through the sanctioned repair entry when
    none is open) to this item as the primed surface, so the subsequent primed
    submit schedules the §6.2 cold retry. A held/blocked repair leaves the
    binding null and the redo serves as a plain primed attempt.
    """

    from learnloop.diagnosis.guided_redo import GuidedRedoUnavailable, start_guided_redo

    vault, repository = ctx.require_vault()
    try:
        result = start_guided_redo(vault, repository, params.attempt_id)
    except GuidedRedoUnavailable as exc:
        raise SidecarError("guided_redo_unavailable", str(exc)) from exc
    log_event(
        "guided_redo_started",
        attempt_id=params.attempt_id,
        practice_item_id=result["practice_item_id"],
        episode_id=result.get("episode_id"),
        cold_item_id=result.get("cold_item_id"),
        cold_unmeasurable_reason=result.get("cold_unmeasurable_reason"),
    )
    return versioned(
        {
            **{key: value for key, value in result.items() if key != "episode"},
            "practice_item": practice_item_detail(
                vault, repository, result["practice_item_id"]
            ),
        }
    )


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
