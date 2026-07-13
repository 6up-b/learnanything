"""Tutor Q&A RPCs: ask, rate, save-as-note, transcript."""

from __future__ import annotations

from typing import Any

from learnloop.codex.client import CodexUnavailable
from learnloop.services.promotions import PromotionError
from learnloop.services.promotions import (
    promote_tutor_question as promote_tutor_question_service,
)
from learnloop.services.teach_back import TEACH_BACK_PRACTICE_MODE
from learnloop.services.tutor_qa import (
    QuestionLimitReached,
    TutorQAError,
    ask_question,
    build_tutor_qa_note,
    question_usage,
)
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.ai_providers import ready_tutor_qa_provider, provider_label
from learnloop_sidecar.registry import method


class AskTutorQuestionInput(ParamsModel):
    context: str
    question: str
    practice_item_id: str | None = None
    attempt_id: str | None = None
    note_id: str | None = None
    session_id: str | None = None
    seconds_into_attempt: float | None = None
    # §13.4 generating-process context (probe redesign Checkpoint 4.6): all
    # optional; persisted verbatim on the question event for later contextual
    # likelihood calibration.
    preceding_tutor_move: str | None = None
    scaffold_level: str | None = None
    warning_state: str | None = None
    learner_mode: str | None = None
    question_opportunity: str | None = None
    hints_used_before: int | None = None
    direct_explanation_request: bool = False
    attempt_progress: str | None = None


class RateTutorAnswerInput(ParamsModel):
    event_id: str
    useful: bool


class SaveTutorAnswerNoteInput(ParamsModel):
    event_id: str
    subject_id: str | None = None


class GetTutorTranscriptInput(ParamsModel):
    context: str
    practice_item_id: str | None = None
    attempt_id: str | None = None
    note_id: str | None = None
    session_id: str | None = None


class PromoteTutorQuestionInput(ParamsModel):
    event_id: str
    intent: str
    subject_id: str | None = None


@method("ask_tutor_question", AskTutorQuestionInput)
def ask_tutor_question(ctx: SidecarContext, params: AskTutorQuestionInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    # Server-side backstop for the frontend guard: during a teach-back
    # conversation the AI plays the naive student, so the learner must not be
    # able to ask the tutor about the very item they are teaching.
    if params.context == "practice" and params.practice_item_id is not None:
        item = vault.practice_items.get(params.practice_item_id)
        if item is not None and item.practice_mode == TEACH_BACK_PRACTICE_MODE:
            raise SidecarError(
                "tutor_disabled_teach_back",
                "The tutor is disabled during teach-back — the AI plays the student.",
                retryable=False,
            )
    provider_name, runtime, client = ready_tutor_qa_provider(vault)
    if not runtime.ready or client is None:
        raise SidecarError(
            "provider_unavailable",
            f"{provider_label(provider_name)} is unavailable for tutor Q&A.",
            retryable=True,
        )
    try:
        result = ask_question(
            vault,
            repository,
            client,
            context=params.context,
            question_md=params.question,
            practice_item_id=params.practice_item_id,
            attempt_id=params.attempt_id,
            note_id=params.note_id,
            session_id=params.session_id,
            seconds_into_attempt=params.seconds_into_attempt,
            question_context={
                "preceding_tutor_move": params.preceding_tutor_move,
                "scaffold_level": params.scaffold_level,
                "warning_state": params.warning_state,
                "learner_mode": params.learner_mode,
                "question_opportunity": params.question_opportunity,
                "hints_used_before": params.hints_used_before,
                "direct_explanation_request": params.direct_explanation_request,
                "attempt_progress": params.attempt_progress,
            },
        )
    except QuestionLimitReached as exc:
        raise SidecarError(
            "question_limit_reached",
            str(exc),
            details={"limit": exc.limit, "used": exc.used, "context": exc.context},
        ) from exc
    except TutorQAError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    except (CodexUnavailable, TimeoutError) as exc:
        raise SidecarError(
            "provider_unavailable",
            f"{provider_label(provider_name)} is unavailable for tutor Q&A.",
            retryable=True,
        ) from exc
    return versioned(
        {
            "event_id": result["event_id"],
            "answer_md": result["answer_md"],
            "question_type": result["question_type"],
            "facets": result["facets"],
            "hint_equivalent": result["hint_equivalent"],
            "leak_suspected": result["leak_suspected"],
            "remaining": result["remaining"],
        }
    )


@method("rate_tutor_answer", RateTutorAnswerInput)
def rate_tutor_answer(ctx: SidecarContext, params: RateTutorAnswerInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    if not repository.set_question_event_rating(params.event_id, useful=params.useful):
        raise SidecarError("not_found", f"Question event {params.event_id} was not found.")
    return versioned({"ok": True})


@method("save_tutor_answer_note", SaveTutorAnswerNoteInput)
def save_tutor_answer_note(ctx: SidecarContext, params: SaveTutorAnswerNoteInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    event = repository.question_event(params.event_id)
    if event is None:
        raise SidecarError("not_found", f"Question event {params.event_id} was not found.")

    # A turn already saved as a note returns the existing note (idempotent);
    # the saved_note_id back-link is persisted server-side (migration 027) so the
    # "saved" UI state survives a remount.
    try:
        result = build_tutor_qa_note(vault, repository, event, subject_id=params.subject_id)
    except TutorQAError as exc:
        raise SidecarError("invalid_request", str(exc)) from exc
    except ValueError as exc:
        raise SidecarError("invalid_request", str(exc)) from exc
    if not result["reused"]:
        ctx.reload(maintenance=False)
    return versioned({"note_id": result["note_id"], "path": result["path"], "reused": result["reused"]})


@method("promote_tutor_question", PromoteTutorQuestionInput)
def promote_tutor_question(ctx: SidecarContext, params: PromoteTutorQuestionInput) -> dict[str, Any]:
    """Promote an answered tutor turn to practice/gap (spec_tutor_promotion.md §2/§8 W4).

    Reuses ``ask_tutor_question``'s provider-resolution path: the Step-0
    analysis and (practice route) authoring generation both need a live
    provider, so an unready provider fails fast here with the same
    ``provider_unavailable`` shape the ask flow uses, instead of surfacing a
    confusing error from deep inside the service.
    """
    vault, repository = ctx.require_vault()
    if ctx.vault_root is None:
        raise SidecarError("vault_not_loaded", "No vault has been initialized.")
    provider_name, runtime, client = ready_tutor_qa_provider(vault)
    if not runtime.ready or client is None:
        raise SidecarError(
            "provider_unavailable",
            f"{provider_label(provider_name)} is unavailable for tutor Q&A.",
            retryable=True,
        )
    # Detect idempotent replay before calling the service so we don't reload the
    # vault for a turn that was already promoted (mirrors save_tutor_answer_note's
    # `reused` check) — nothing changed on disk on a replay.
    already_promoted = repository.question_promotion(params.event_id) is not None
    try:
        result = promote_tutor_question_service(
            ctx.vault_root,
            client,
            event_id=params.event_id,
            intent=params.intent,
            subject_id=params.subject_id,
        )
    except PromotionError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    except (CodexUnavailable, TimeoutError) as exc:
        raise SidecarError(
            "provider_unavailable",
            f"{provider_label(provider_name)} is unavailable for tutor Q&A.",
            retryable=True,
        ) from exc
    # Reload when this call actually applied entities (auto_apply route) or
    # materialized a grounding note (both write vault files), mirroring how
    # save_tutor_answer_note reloads only on a fresh (non-reused) note.
    if not already_promoted and (result.get("route") == "auto_apply" or result.get("saved_note_id")):
        ctx.reload(maintenance=False)
    return versioned(result)


@method("get_tutor_transcript", GetTutorTranscriptInput)
def get_tutor_transcript(ctx: SidecarContext, params: GetTutorTranscriptInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    try:
        used, limit = question_usage(
            vault,
            repository,
            context=params.context,
            practice_item_id=params.practice_item_id,
            attempt_id=params.attempt_id,
            note_id=params.note_id,
            session_id=params.session_id,
        )
    except TutorQAError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    if params.context == "practice":
        events = repository.question_events(
            context="practice",
            practice_item_id=params.practice_item_id,
            session_id=params.session_id,
            answer_status="answered",
        )
    elif params.context == "feedback":
        events = repository.question_events(
            context="feedback", attempt_id=params.attempt_id, answer_status="answered"
        )
    else:
        events = repository.question_events(
            context="library", note_id=params.note_id, answer_status="answered"
        )
    # Attach persisted promotion state per turn so the overlay renders result
    # chips instead of the promote button on remount (spec §2 idempotency).
    # saved_note_id already rides along on each event row (migration 027).
    promotions = repository.question_promotions_for_events(
        [event["id"] for event in events]
    )
    for event in events:
        event["promotion"] = promotions.get(event["id"])
    return versioned({"events": events, "remaining": max(0, limit - used)})
