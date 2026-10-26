"""Tutor Q&A RPCs: ask, rate, save-as-note, transcript."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from learnloop.ai.errors import CodexUnavailable
from pydantic import Field

from learnloop.source_retrieval.tutor import PinnedSpanProvider, TutorSpanProvider, linked_reference_filter
from learnloop.tutor import question_queue as QQ
from learnloop.tutor.question_queue import QuestionQueueError
from learnloop.tutor.teach_back import TEACH_BACK_PRACTICE_MODE
from learnloop.tutor.tutor_qa import (
    READER_ANSWER_MODES,
    QuestionLimitReached,
    TutorQAError,
    ask_panel_enabled,
    ask_question,
    WITHHELD_NOT_SAVED,
    answer_withheld,
    delivered_answer_md,
    earlier_threads,
    help_style_answer_mode,
    build_tutor_opening,
    build_tutor_qa_note,
    practice_thread_events,
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
    # Canonical sources S4 (§10.3), "Explain this with my work": the passages
    # the learner chose (span keys "<extraction>:<span>") and their current draft.
    pinned_span_keys: list[str] = Field(default_factory=list, max_length=20)
    learner_draft_md: str | None = Field(default=None, max_length=8000)
    # Reader CA2 (ux_reader_compare_ask_v1 §7, K5/K7; ``ask.panel_enabled``):
    # the attempt's key (the practice thread is the attempt's), the workbench
    # session a Work-in-Steps question is asked from (validated against the
    # item on the server), the step it is about, and a one-question answer
    # mode (absent: the help style's). Policy and counts stay the server's.
    submission_id: str | None = Field(default=None, max_length=200)
    workbench_session_id: str | None = Field(default=None, max_length=200)
    about_step: int | None = Field(default=None, ge=1)
    answer_mode: str | None = None


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
    # Reader CA2 (K5): the attempt's key; its thread only.
    submission_id: str | None = Field(default=None, max_length=200)
    # Codex review F6: the unfinished workbench the thread is asked from (the
    # server derives its key and practice session, the same in every host).
    workbench_session_id: str | None = Field(default=None, max_length=200)


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
            # The remaining count of the attempt the question was asked in
            # (its stored key; owner 2026-10-26: per attempt).
            key = (event.get("source_context") or {}).get("attempt_key") or {}
            used, limit = question_usage(
                vault, repository, context=event["context"],
                practice_item_id=event.get("practice_item_id"), attempt_id=event.get("attempt_id"),
                note_id=event.get("note_id"), session_id=event.get("session_id"),
                submission_id=key.get("submission_id") if isinstance(key, dict) else None,
                workbench_session_id=key.get("workbench_session_id") if isinstance(key, dict) else None,
            )
            response = {key: event.get(key) for key in (
                "note_id", "answer_md", "question_type", "facets", "hint_equivalent", "leak_suspected",
                # Reader CA2: the mode it was written in, as the first answer said.
                "answer_mode",
            )}
            response.update(event_id=event_id, remaining=None if limit is None else max(0, limit - used),
                            answer_md=delivered_answer_md(event),
                            citations=(event.get("source_context") or {}).get("citations", []))
            # The same gap status the first answer carried (the enqueue is
            # idempotent per question, so a recovered answer never queues twice).
            response["learner_gap"] = queue_tutor_question_gap(
                ctx, vault, repository, event_id, (event.get("source_context") or {}).get("learner_gap")
            )
            _with_offers(vault, repository, response, event_id, _stored_tool_requests(repository, event_id))
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
    panel_ask = _ask_panel_inputs(ctx, vault, repository, params)
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
            # Codex review F10: a workbench question's practice session is
            # the server's (the workbench submit's own rule).
            session_id=panel_ask.session_id if panel_ask.bound else params.session_id,
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
            # Slice 2 T6: question-dependent, verified source spans (kill switch
            # source_retrieval.enabled; any failure keeps the linked spans).
            # S4's "Explain this with my work" pins the learner's chosen spans.
            source_span_provider=_span_provider(vault, repository, params, cold=panel_ask.cold),
            learner_draft_md=params.learner_draft_md,
            # Tutor delivery fixes (Codex review F1): the numbered blocks a
            # linked span cites pass the teaching scope's item exclusions.
            linked_reference_filter=linked_reference_filter,
            # Canonical sources S4: the answer's typed tool requests (None when
            # source_service.tutor_tools is off: S0's tutor byte for byte).
            tool_request_handler=_tool_request_handler(vault),
            **({"answer_mode": panel_ask.answer_mode} if panel_ask.answer_mode is not None else {}),
            **({"submission_id": panel_ask.submission_id, "workbench_session_id": panel_ask.workbench_session_id,
                "about_step": params.about_step,
                # Codex review F3: a workbench question during a cold
                # administration counts as the workbench's cold rule says.
                "count_every_question": panel_ask.count_every_question,
                # Codex review F2 (K9): worked help is never served on the spot.
                "worked_help_check": _worked_help_check}
               if params.context == "practice" and ask_panel_enabled(vault) else {}),
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
    _record_citations(vault, repository, result["event_id"])
    response = {
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
        # Reader CA2 (§7.4): the mode the answer was written in (None: today's).
        "answer_mode": result.get("answer_mode"),
        # Codex review F2 (K9): a withheld worked answer's take step.
        **({"take_offer": result["take_offer"]} if result.get("take_offer") else {}),
        # Learner-text gaps: the question is read for a named gap off the
        # request path; the overlay polls get_learner_text_gap.
        "learner_gap": queue_tutor_question_gap(
            ctx, vault, repository, result["event_id"], result.get("learner_gap")
        ),
    }
    _with_offers(vault, repository, response, result["event_id"], result.get("tool_requests") or [])
    return finish_route(
        ctx, repository, params.capture_id, "ask_tutor",
        {"question_event_id": result["event_id"], "note_id": note_id}, response,
    )


@dataclass(frozen=True)
class PanelAsk:
    """What the server derives for one practice or feedback question while
    ``ask.panel_enabled`` (Reader CA2 §7.4, K5, K7; Codex review F3, F6,
    F10), never from the client's word: the answer mode, the validated
    workbench, the attempt's key and practice session, whether the item is
    under a cold administration, and the cold rule's count."""

    answer_mode: str | None = None
    workbench_session_id: str | None = None
    submission_id: str | None = None
    session_id: str | None = None
    cold: bool = False
    count_every_question: bool = False

    @property
    def bound(self) -> bool:
        return self.workbench_session_id is not None


def _ask_panel_inputs(ctx: SidecarContext, vault: Any, repository: Any, params: Any, *,
                      transcript: bool = False) -> PanelAsk:
    """Reader CA2 (§7.4, K7): the :class:`PanelAsk` of a practice or feedback
    question (or transcript) while ``ask.panel_enabled``.

    The mode is the help style's (``hints.help_style``; a workbench session's
    per-problem style wins, spec D31) unless the learner changed it for this
    one question. The workbench session must be bound to the question's item;
    a client cannot name another problem's. Codex review F6: an unfinished
    workbench is one attempt in every host, so its key is the server's
    (``workbench:<id>``, the workbench submit's) unless the practice screen's
    answer box handed its own key to the steps; its practice session is the
    workbench submit's rule (the named open one, the session's, the most
    recent open one, else a new one), so a question asked from the Reader
    with no practice session open still counts at the submit (F10). Codex
    review F3: the cold status is the server's; a cold item grounds in
    nothing (``cold_attempt``), and a workbench question on it counts as the
    workbench's cold rule says (every question while the one help rule is
    off, ``reader.ask``'s predecessor rule; only substantive ones under it).
    Off, or another context: an empty :class:`PanelAsk` and the question goes
    out exactly as before."""

    answer_mode_param = getattr(params, "answer_mode", None)
    if params.context not in ("practice", "feedback") or not ask_panel_enabled(vault):
        if answer_mode_param is not None and params.context in ("practice", "feedback"):
            raise SidecarError("validation_error", "Answer modes need the Ask panel (ask.panel_enabled).")
        return PanelAsk()
    if answer_mode_param is not None and answer_mode_param not in READER_ANSWER_MODES:
        raise SidecarError("validation_error", f"Unknown answer mode {answer_mode_param!r}.")
    style = vault.config.hints.help_style
    item_id = params.practice_item_id
    cold = params.context == "practice" and bool(item_id) and _item_cold(vault, repository, str(item_id))
    if params.workbench_session_id is None:
        return PanelAsk(answer_mode=answer_mode_param or help_style_answer_mode(style),
                        submission_id=params.submission_id, session_id=params.session_id, cold=cold)
    if params.context != "practice":
        raise SidecarError("validation_error", "Only a practice question is asked from a workbench.")
    from learnloop.reader import workbench as WB
    from learnloop.serve_eligibility import help_converts_active
    from learnloop_sidecar.handlers.workbench import _practice_session

    try:
        session = WB.session_row(repository, params.workbench_session_id)
    except Exception as exc:  # noqa: BLE001 - an unknown session is the caller's error
        raise SidecarError("validation_error", "That workbench session was not found.") from exc
    if session is None or not item_id or session.get("practice_item_id") != item_id:
        raise SidecarError("validation_error", "That workbench session is not this item's problem.")
    style = session.get("help_style") or style
    if transcript:
        # A read never opens a practice session: the thread is the
        # workbench's whatever its session.
        practice_session = params.session_id or session.get("practice_session_id")
    else:
        practice_session = _practice_session(ctx, repository, params.session_id or session.get("practice_session_id"))
    return PanelAsk(
        answer_mode=answer_mode_param or help_style_answer_mode(style),
        workbench_session_id=params.workbench_session_id,
        submission_id=params.submission_id or WB.submission_id_for(params.workbench_session_id),
        session_id=practice_session,
        cold=cold,
        count_every_question=cold and not help_converts_active(vault),
    )


def _worked_help_check(answer_md: str, item: Any) -> list[str]:
    """Codex review F2 (K9): the hint service's leak control at levels 1-3
    (``hints.contracts.leak_flags``) for an Ask answer before it is shown."""

    from learnloop.hints.contracts import leak_flags

    return leak_flags([answer_md], item=item, current=None, level=3)


def _item_cold(vault: Any, repository: Any, practice_item_id: str) -> bool:
    """Is the item under a cold administration now (an open cold follow-up or
    a held-out exam, ``instructional.policy.cold_administration_open``, or a
    "Check once" served cold)? Server-derived; fails closed."""

    from learnloop.instructional.policy import cold_administration_open

    try:
        if cold_administration_open(repository, practice_item_id):
            return True
    except Exception:  # noqa: BLE001 - fail closed
        return True
    return _served_cold(vault, repository, practice_item_id)


def _with_offers(vault: Any, repository: Any, response: dict[str, Any], event_id: str,
                 tool_requests: list[dict[str, Any]]) -> None:
    """Canonical sources S0 (§6.2): a deterministic "Practice this" request the
    frontend runs once the answer is on screen. S4 (§10.3): the tutor's typed
    requests (present only when it wrote some); its own find_practice request
    replaces S0's. A recovered response is built the same way, from the rows."""

    response["practice_request"] = (None if any(entry.get("tool") == "find_practice" for entry in tool_requests)
                                    else tutor_practice_request(vault, repository, event_id))
    if tool_requests:
        response["tool_requests"] = tool_requests


def _stored_tool_requests(repository: Any, event_id: str | None) -> list[dict[str, Any]]:
    if not event_id:
        return []
    from learnloop.instructional.tools import offered_tool_requests

    try:
        return offered_tool_requests(repository, event_id)
    except Exception:  # noqa: BLE001 - a vault before migration 192 has no rows
        return []


def _record_citations(vault: Any, repository: Any, event_id: str) -> None:
    """S5: a tutor answer citing retrieved spans is an intervention (best effort)."""

    from learnloop.instructional.interventions import record_tutor_citations

    try:
        record_tutor_citations(vault, repository, event_id)
    except Exception:  # noqa: BLE001 - telemetry never fails the answer
        import logging

        logging.getLogger(__name__).warning("intervention record failed for %s", event_id, exc_info=True)


def _span_provider(vault: Any, repository: Any, params: AskTutorQuestionInput, *, cold: bool = False) -> Any:
    if cold:
        # Codex review F3 (K7): during a cold administration the server's
        # policy is ``cold_attempt``: nothing is retrieved or grounded, on
        # every host (``reader.ask``'s rule).
        return PinnedSpanProvider([], cold=True)
    if not params.pinned_span_keys:
        return TutorSpanProvider(intent_for=_tutor_intent_for)
    from learnloop.instructional.policy import cold_administration_open

    item_id = params.practice_item_id if params.context in ("practice", "feedback") else None
    return PinnedSpanProvider(params.pinned_span_keys, cold=cold_administration_open(repository, item_id))


def _tool_request_handler(vault: Any) -> Any:
    from learnloop.instructional.tools import tutor_request_handler

    return tutor_request_handler(vault)




def _tutor_intent_for(vault: Any, repository: Any, *, context: str, item: Any) -> dict[str, Any] | None:
    """Canonical sources S3: remediate when the item's LO has an active misconception."""

    from learnloop.instructional.sources import tutor_intent_for

    return tutor_intent_for(vault, repository, context=context, item=item)


def tutor_practice_request(vault: Any, repository: Any, event_id: str) -> dict[str, Any] | None:
    """The answer's practice request, or None when the offer is switched off."""

    from learnloop.instructional.offers import practice_request_for_answer

    service = vault.config.source_service
    if not (service.enabled and service.tutor_offers and vault.config.practice_index.enabled):
        return None
    event = repository.question_event(event_id)
    if event is None:
        return None
    return practice_request_for_answer(vault, event, exercise_arm=bool(service.exercise_arm))


class PreviewTutorOpeningInput(ParamsModel):
    practice_item_id: str
    session_id: str | None = None


@method("preview_tutor_opening", PreviewTutorOpeningInput)
def preview_tutor_opening(ctx: SidecarContext, params: PreviewTutorOpeningInput) -> dict[str, Any]:
    """A proactive tutor opening for a just-closed diagnostic block (§12.1).

    Best-effort and ephemeral: unlike ``ask_tutor_question`` this never raises
    on an unready provider or a missing decision — it degrades to
    ``opening_md: None`` so the overlay falls back to the ordinary
    learner-speaks-first flow.
    """

    vault, repository = ctx.require_vault()
    _provider_name, runtime, client = ready_tutor_qa_provider(vault)
    if not runtime.ready or client is None:
        return versioned({"opening_md": None})
    try:
        opening_md = build_tutor_opening(
            vault, repository, client, practice_item_id=params.practice_item_id,
            linked_reference_filter=linked_reference_filter,
        )
    except (CodexUnavailable, TimeoutError):
        return versioned({"opening_md": None})
    return versioned({"opening_md": opening_md})


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
    """Persist and enqueue an answered tutor turn for durable promotion."""

    vault, repository = ctx.require_vault()
    if ctx.vault_root is None:
        raise SidecarError("vault_not_loaded", "No vault has been initialized.")
    event = repository.question_event(params.event_id)
    if event is None:
        raise SidecarError(
            "validation_error", f"Question event {params.event_id} was not found."
        )
    if event.get("answer_status") != "answered":
        raise SidecarError(
            "validation_error", "Only answered tutor turns can be promoted."
        )
    if answer_withheld(event):
        # Codex re-review F12: a withheld worked answer is taken from the
        # ladder, never promoted (nor saved) from Ask.
        raise SidecarError("validation_error", WITHHELD_NOT_SAVED)
    if params.intent not in {"practice", "gap"}:
        raise SidecarError(
            "validation_error", f"Unknown promotion intent {params.intent!r}"
        )
    if params.intent == "gap" and event.get("context") not in {
        "practice",
        "feedback",
    }:
        raise SidecarError(
            "validation_error",
            "The gap route requires an origin learning object and is only "
            "available in the practice/feedback contexts.",
        )

    promotion = repository.question_promotion(params.event_id)
    request = repository.question_promotion_request(params.event_id)
    if promotion is not None:
        if request is None:
            repository.insert_question_promotion_request(
                question_event_id=params.event_id,
                intent=params.intent,
                subject_id=params.subject_id,
                learning_object_id=params.learning_object_id,
                status="completed",
                stage="review" if promotion["route"] == "review_required" else "ready",
            )
            repository.update_question_promotion_request(
                params.event_id,
                promotion_route=promotion["route"],
            )
            request = repository.question_promotion_request(params.event_id)
        return versioned({"request": request, "promotion": promotion})

    if request is None:
        repository.insert_question_promotion_request(
            question_event_id=params.event_id,
            intent=params.intent,
            subject_id=params.subject_id,
            learning_object_id=params.learning_object_id,
        )
        repository.bump_queue_revision()
        request = repository.question_promotion_request(params.event_id)
    elif request["status"] == "failed":
        if request.get("batch_id"):
            repository.update_question_promotion_request(
                params.event_id,
                subject_id=params.subject_id,
                learning_object_id=params.learning_object_id,
            )
            ctx.ingest_jobs.resume_batch(str(request["batch_id"]))
            repository.bump_queue_revision()
            request = repository.question_promotion_request(params.event_id)
            return versioned({"request": request, "promotion": None})
        repository.retry_question_promotion_request(params.event_id)

    if request is not None and request.get("batch_id"):
        return versioned({"request": request, "promotion": None})

    try:
        batch_id = ctx.ingest_jobs.enqueue_question_promotion(
            event_id=params.event_id,
            subject_id=params.subject_id,
        )
    except Exception as exc:  # noqa: BLE001 - preserve the durable request failure
        repository.update_question_promotion_request(
            params.event_id,
            status="failed",
            stage="failed",
            error_code="enqueue_failed",
            error_message=str(exc) or exc.__class__.__name__,
            retryable=True,
        )
        repository.bump_queue_revision()
        raise SidecarError(
            "enqueue_failed",
            f"Could not queue practice authoring: {exc}",
            retryable=True,
        ) from exc
    repository.update_question_promotion_request(
        params.event_id, batch_id=batch_id
    )
    request = repository.question_promotion_request(params.event_id)
    return versioned({"request": request, "promotion": None})


@method("get_tutor_transcript", GetTutorTranscriptInput)
def get_tutor_transcript(ctx: SidecarContext, params: GetTutorTranscriptInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    panel = ask_panel_enabled(vault)
    panel_ask = (_ask_panel_inputs(ctx, vault, repository, params, transcript=True)
                 if panel and params.context == "practice" else PanelAsk())
    try:
        # The practice budget is the attempt's (owner, 2026-10-26: B3's rule
        # on every route), read with the keys of the thread shown below.
        used, limit = question_usage(
            vault,
            repository,
            context=params.context,
            practice_item_id=params.practice_item_id,
            attempt_id=params.attempt_id,
            note_id=params.note_id,
            session_id=panel_ask.session_id if panel_ask.bound else params.session_id,
            submission_id=panel_ask.submission_id if panel else None,
            workbench_session_id=panel_ask.workbench_session_id,
        )
    except TutorQAError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    if params.context == "practice":
        # Owner capture 2026-10-25 (B3): the current attempt's thread; a
        # reattempt starts a fresh one (earlier turns stay on record). Reader
        # CA2 (K5): with the panel, keyed by the attempt's submission id, or
        # (Codex review F6) the unfinished workbench the server names.
        events = practice_thread_events(
            repository, practice_item_id=params.practice_item_id,
            session_id=panel_ask.session_id if panel_ask.bound else params.session_id,
            submission_id=panel_ask.submission_id if panel else None,
            workbench_session_id=panel_ask.workbench_session_id,
        )
    elif params.context == "feedback":
        events = repository.question_events(
            context="feedback", attempt_id=params.attempt_id, answer_status="answered"
        )
    elif params.context == "reader":
        events = repository.question_events(
            context="reader", note_id=params.note_id, answer_status="answered"
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
    promotion_requests = repository.question_promotion_requests_for_events(
        [event["id"] for event in events]
    )
    for event in events:
        event["promotion"] = promotions.get(event["id"])
        event["promotion_request"] = promotion_requests.get(event["id"])
        # Codex review F2: a withheld worked answer is restored as its take step.
        event["answer_md"] = delivered_answer_md(event)
    payload: dict[str, Any] = {"events": events, "remaining": None if limit is None else max(0, limit - used)}
    if panel and params.context in ("practice", "feedback"):
        payload.update(_earlier(vault, repository, params))
    if panel and params.context == "practice" and params.practice_item_id:
        payload["help_record"] = _help_record(repository, params, panel_ask, events)
    return versioned(payload)


def _help_record(repository: Any, params: GetTutorTranscriptInput, panel_ask: PanelAsk,
                 thread: list[dict[str, Any]]) -> dict[str, Any]:
    """Reader CA2 (§7.5, K8; Codex review F7): the attempt's help record as
    Submit will fold it, in order, read from what is stored (never the
    panel's memory): every question Submit counts (the item's window, which
    may hold a question asked on an earlier serving of the item), this
    attempt's free clarifications, the hints the hint service showed under
    the attempt's key (worked help, levels 4-5, primes rather than counts),
    and an earlier attempt's help opened before Submit (its one hint, from the
    draft's checkpoint or the open problem it moved onto). ``counted`` is their hint-equivalents; the screen
    adds only what the client alone counts (its authored hints, the book)."""

    from learnloop.hint_window import counts_in_session, workbench_bound
    from learnloop.tutor.tutor_qa import hint_equivalents_for_submission
    from learnloop_sidecar.handlers.practice import _earlier_opened_hint

    item_id = str(params.practice_item_id)
    session_id = panel_ask.session_id if panel_ask.bound else params.session_id
    attempts = repository.list_recent_attempts_by_practice_item(item_id, limit=1)
    since = str(attempts[0]["created_at"]) if attempts else None
    in_thread = {str(event["id"]) for event in thread}
    items: list[dict[str, Any]] = []
    for event in repository.question_events(practice_item_id=item_id, answer_status="answered"):
        if since is not None and str(event["created_at"]) <= since:
            continue
        counted = bool(event.get("hint_equivalent"))
        if not counted and str(event["id"]) not in in_thread:
            continue
        if counted and not counts_in_session(context=event.get("context"), question_session_id=event.get("session_id"),
                                             attempt_session_id=session_id,
                                             bound=workbench_bound(event.get("source_context"))):
            continue
        items.append({"kind": "question", "at": event["created_at"], "counts": counted,
                      "event_id": event["id"], "this_attempt": str(event["id"]) in in_thread})
    items.extend(_shown_assists(repository, item_id, session_id, panel_ask.submission_id))
    # Orchestrator fix F1/F15: once the draft moved into steps an open
    # problem of the item carries the opening as its own component (never in
    # the authored count the screen gets back), so it is still the server's
    # to add, whatever session or draft the record is read for.
    earlier = _earlier_opened_hint(repository, session_id, item_id)
    if earlier:
        items.append({"kind": "earlier", "at": None, "counts": True})
    opened = bool(earlier) or _draft_opened(repository, session_id, item_id)
    items.sort(key=lambda entry: (entry["at"] is None, str(entry["at"] or "")))
    question_hints = hint_equivalents_for_submission(repository, item_id, session_id) if session_id else 0
    return {
        "items": items,
        # What Submit's server side adds: the questions it folds, the hint
        # service's shown hints (levels 1-3) and the earlier attempt's help.
        "counted": question_hints + earlier + sum(
            1 for entry in items if entry["kind"] == "hint" and entry.get("counted_by") == "server"
            and entry["counts"]),
        "earlier_opened": opened,
    }


def _draft_opened(repository: Any, session_id: str | None, item_id: str) -> bool:
    from learnloop_sidecar.handlers.sessions import draft_earlier_opened

    if not session_id:
        return False
    try:
        return draft_earlier_opened(repository.fetch_session_checkpoint(session_id), practice_item_id=item_id)
    except Exception:  # noqa: BLE001 - a session with no checkpoint opened nothing
        return False


def _shown_assists(repository: Any, item_id: str, session_id: str | None,
                   submission_id: str | None) -> list[dict[str, Any]]:
    """The attempt's shown hints still unattached, under its key (``help_assists``)."""

    if not submission_id:
        return []
    try:
        with repository.connection() as connection:
            rows = connection.execute(
                "SELECT id, assist_kind, level, hint_kind, counted_by, requested_at, shown_at FROM help_assists "
                "WHERE practice_item_id = ? AND submission_id = ? AND attempt_id IS NULL AND shown = 1 "
                "AND assist_kind IN ('hint', 'check') ORDER BY requested_at, id",
                (item_id, submission_id),
            ).fetchall()
    except Exception:  # noqa: BLE001 - a vault before help_assists shows none
        return []
    out: list[dict[str, Any]] = []
    for row in rows:
        level = row["level"]
        worked = level is not None and int(level) >= 4
        out.append({
            # Codex re-review F14: the row's id, so the screen reconciles its
            # own hint entries with the record by identity.
            "assist_id": row["id"],
            "kind": "worked" if worked else row["assist_kind"],
            "at": row["shown_at"] or row["requested_at"],
            "level": level,
            "counts": not worked and row["counted_by"] in ("server", "client"),
            "counted_by": row["counted_by"],
        })
    return out


def _earlier(vault: Any, repository: Any, params: GetTutorTranscriptInput) -> dict[str, Any]:
    """Reader CA2 (§7.3, K6, Q2): *earlier on this question*. Before Submit
    (the practice context) opening one counts as one hint (said first; the
    screen records the opening on its draft and the submit counts it from
    there, Codex review F1); after Submit (the feedback context) it is free.
    During a check on your own it is absent, and ``cold`` says so (the same
    server derivation as the question's policy, F3). The help style rides
    along for the panel (§7.4)."""

    item_id = params.practice_item_id
    if params.context == "feedback" and params.attempt_id:
        attempt = repository.fetch_practice_attempt(params.attempt_id)
        item_id = item_id or (attempt or {}).get("practice_item_id")
    if not item_id:
        return {"earlier": [], "earlier_counts_as_hint": False, "cold": False}
    cold = params.context == "practice" and _item_cold(vault, repository, item_id)
    earlier = [] if cold else earlier_threads(vault, repository, practice_item_id=item_id)
    if params.context == "feedback" and params.attempt_id:
        # The attempt just graded is the feedback screen itself, not "earlier".
        earlier = [entry for entry in earlier if entry["attempt_id"] != params.attempt_id]
    return {
        "earlier": earlier,
        "earlier_counts_as_hint": params.context == "practice",
        "cold": cold,
        "help_style": vault.config.hints.help_style,
    }


def _served_cold(vault: Any, repository: Any, practice_item_id: str) -> bool:
    """Is the item served as a check on your own now (a due "Check once"
    served cold, or a due cold follow-up)? Server-derived (U11: nothing from
    before shows on a cold check)."""

    from learnloop.clock import SystemClock
    from learnloop.intent.checks import cold_followup_duty, served_check

    now = SystemClock().now()
    try:
        check = served_check(vault, repository, practice_item_id, now=now)
    except Exception:  # noqa: BLE001 - fail closed: hide the earlier help
        return True
    if check is not None:
        return bool(check.get("cold"))
    return cold_followup_duty(repository, practice_item_id, now=now) is not None
