"""Tutor Q&A RPCs: ask, rate, save-as-note, transcript."""

from __future__ import annotations

from typing import Any

from learnloop.codex.client import CodexUnavailable
from learnloop.ids import new_ulid
from learnloop.services.teach_back import TEACH_BACK_PRACTICE_MODE
from learnloop.services.tutor_qa import (
    QuestionLimitReached,
    TutorQAError,
    ask_question,
    question_usage,
)
from learnloop.vault.loader import add_note
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

    related_los: list[str] = []
    subjects: list[str] = []
    item_id = event.get("practice_item_id")
    if item_id is not None:
        item = vault.practice_items.get(item_id)
        if item is not None:
            related_los.append(item.learning_object_id)
            subjects = vault.subjects_for_item(item)
    source_note_id = event.get("note_id")
    if source_note_id is not None:
        source_note = vault.notes.get(source_note_id)
        if source_note is not None:
            related_los.extend(source_note.related_los)
            subjects = subjects or list(source_note.subjects)

    subject_id = params.subject_id or (subjects[0] if subjects else None)
    if subject_id is None and vault.subjects:
        subject_id = sorted(vault.subjects)[0]
    if subject_id is None:
        raise SidecarError("invalid_request", "No subject available to file the note under.")

    title = _note_title(event["question_md"])
    body = (
        f"**Q ({event['context']}):** {event['question_md'].strip()}\n\n"
        f"**A:** {(event.get('answer_md') or '').strip()}\n"
    )
    try:
        path = add_note(
            vault.root,
            subject_id,
            f"tutor_qa_{new_ulid().lower()}",
            title,
            body,
            related_los=sorted(set(related_los)),
        )
    except ValueError as exc:
        raise SidecarError("invalid_request", str(exc)) from exc
    ctx.reload(maintenance=False)
    return versioned({"note_id": path.stem, "path": str(path)})


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
    return versioned({"events": events, "remaining": max(0, limit - used)})


def _note_title(question_md: str) -> str:
    text = " ".join(question_md.split())
    if len(text) <= 60:
        return text
    return text[:59].rstrip() + "…"
