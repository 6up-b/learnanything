"""Tutor Q&A RPCs: ask, rate, save-as-note, transcript."""

from __future__ import annotations

from typing import Any

from learnloop.ai.errors import CodexUnavailable
from learnloop.tutor import question_queue as QQ
from learnloop.tutor.question_queue import QuestionQueueError
from learnloop.tutor.teach_back import TEACH_BACK_PRACTICE_MODE
from learnloop.tutor.tutor_qa import (
    QuestionLimitReached,
    TutorQAError,
    ask_question,
    build_tutor_opening,
    build_tutor_qa_note,
    question_usage,
)
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.capture import finish_route, route_intent
from learnloop_sidecar.handlers.ai_providers import ready_tutor_qa_provider, provider_label
from learnloop_sidecar.handlers.learner_gaps import queue_tutor_question_gap
from learnloop_sidecar.registry import method


class AskTutorQuestionInput(ParamsModel):
    capture_id: str | None = None
    subject_id: str | None = None
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
    learning_object_id: str | None = None


class ListQuestionQueueInput(ParamsModel):
    # None lists every question regardless of state; default is the open queue.
    resolution: str | None = "open"
    limit: int | None = None


class ResolveQuestionEventInput(ParamsModel):
    event_id: str
    resolution: str


@method("list_question_queue", ListQuestionQueueInput)
def list_question_queue(ctx: SidecarContext, params: ListQuestionQueueInput) -> dict[str, Any]:
    """The outstanding-question queue (newest first) + the open count."""

    vault, repository = ctx.require_vault()
    try:
        questions = QQ.list_question_queue(
            repository,
            vault=vault,
            resolution=params.resolution,
            limit=params.limit,
        )
    except QuestionQueueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(
        {"questions": questions, "openCount": QQ.count_open_questions(repository)}
    )


@method("resolve_question_event", ResolveQuestionEventInput)
def resolve_question_event(ctx: SidecarContext, params: ResolveQuestionEventInput) -> dict[str, Any]:
    """Flip one question to open/resolved/dismissed (learner-owned queue state)."""

    _vault, repository = ctx.require_vault()
    try:
        event = QQ.set_question_resolution(
            repository, question_event_id=params.event_id, resolution=params.resolution
        )
    except QuestionQueueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(
        {
            "eventId": event["id"],
            "resolution": event["resolution"],
            "openCount": QQ.count_open_questions(repository),
        }
    )


@method("ask_tutor_question", AskTutorQuestionInput)
def ask_tutor_question(ctx: SidecarContext, params: AskTutorQuestionInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    if params.capture_id is not None and params.context != "library":
        raise SidecarError("validation_error", "Captured questions must use the library context.")
    intent = route_intent(repository, params, "ask_tutor", create=False, ctx=ctx)
    event_id = intent["destination_id"] if intent else None
    if intent:
        response = intent.get("response")
        event = repository.question_event(event_id)
        if response is None and event is not None:
            if event["answer_status"] != "answered":
                raise SidecarError(
                    "capture_question_incomplete",
                    "This capture's question was already started but has no committed answer. "
                    "No second question was created. Keep the capture for recovery or dismiss it.",
                    details={"event_id": event_id}, retryable=False,
                )
            used, limit = question_usage(
                vault, repository, context=event["context"],
                practice_item_id=event.get("practice_item_id"), attempt_id=event.get("attempt_id"),
                note_id=event.get("note_id"), session_id=event.get("session_id"),
            )
            response = {key: event.get(key) for key in (
                "note_id", "answer_md", "question_type", "facets", "hint_equivalent", "leak_suspected",
            )}
            response.update(event_id=event_id, remaining=max(0, limit - used),
                            citations=(event.get("source_context") or {}).get("citations", []))
        if response is not None:
            return finish_route(ctx, repository, params.capture_id, "ask_tutor",
                                {"question_event_id": event_id, "note_id": response["note_id"]}, response)
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
    note_id = params.note_id
    if params.capture_id is not None and params.context == "library":
        import hashlib

        from learnloop.capture import get_capture
        from learnloop.vault.loader import add_note, move_note
        from learnloop_sidecar.handlers.capture import capture_call

        capture = capture_call(get_capture, repository, params.capture_id)
        if capture["kind"] != "text":
            raise SidecarError("validation_error", "Only text captures can be sent to the tutor.")
        if not params.question.strip():
            raise SidecarError("validation_error", "Question must not be empty.")
        if params.subject_id not in vault.subjects:
            raise SidecarError("unknown_subject", "Choose an existing subject for this tutor reference.")
        if intent is None:
            intent = route_intent(repository, params, "ask_tutor", ctx=ctx)
            event_id = intent["destination_id"]
        # Library requires a note. Only actual send creates this reference,
        # never opening/cancelling the dialog; no practice is started.
        note_id = "note_capture_" + hashlib.sha256(params.capture_id.encode()).hexdigest()[:24]
        if note_id not in vault.notes:
            add_note(
                vault.root, params.subject_id, note_id, "Captured question",
                f"{capture['text']}\n\nCapture provenance: {params.capture_id}",
            )
            ctx.reload(maintenance=False)
            vault, repository = ctx.require_vault()
        elif vault.notes[note_id].subjects != [params.subject_id]:
            # A send that crashed after writing the note was replaced by this
            # request (its question was never created): file the note under
            # the subject this request and its persisted intent name.
            move_note(vault.root, note_id, params.subject_id)
            ctx.reload(maintenance=False)
            vault, repository = ctx.require_vault()
    try:
        result = ask_question(
            vault,
            repository,
            client,
            context=params.context,
            question_md=params.question,
            practice_item_id=params.practice_item_id,
            attempt_id=params.attempt_id,
            note_id=note_id,
            session_id=params.session_id,
            seconds_into_attempt=params.seconds_into_attempt,
            **({"question_event_id": event_id} if intent else {}),
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
    return finish_route(
        ctx, repository, params.capture_id, "ask_tutor",
        {"question_event_id": result["event_id"], "note_id": note_id},
        {
            "note_id": note_id,
            "event_id": result["event_id"],
            "answer_md": result["answer_md"],
            "question_type": result["question_type"],
            "facets": result["facets"],
            "hint_equivalent": result["hint_equivalent"],
            "leak_suspected": result["leak_suspected"],
            # ING M8 (§9.2): source-span citations; chips open Open-in-source.
            "citations": result.get("citations", []),
            "remaining": result["remaining"],
            # Learner-text gaps: the question is read for a named gap off the
            # request path; the overlay polls get_learner_text_gap.
            "learner_gap": queue_tutor_question_gap(
                ctx, vault, repository, result["event_id"], result.get("learner_gap")
            ),
        }
    )
