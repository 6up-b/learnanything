"""Teach-back conversation RPCs: start, submit turn, finish (grade transcript).

The learner teaches the practice item's concept to an AI naive student. The
conversation state (core ``TeachBackState``) is persisted verbatim inside the
session checkpoint's ``current_answer`` slot as ``{"mode": "teach_back",
"state": <state dict>}``, so a crash mid-conversation is resumable and no new
tables are needed. The finishing turn grades the whole transcript as ONE
``teach_back`` attempt and clears the checkpoint in the same call (mirroring
``submit_attempt``'s lost-response guarantee).
"""

from __future__ import annotations

import json
from typing import Any

from learnloop.codex.client import CodexUnavailable
from learnloop.services.attempts import AttemptValidationError
from learnloop.services.teach_back import (
    TEACH_BACK_PRACTICE_MODE,
    TeachBackError,
    TeachBackState,
    asked_criterion_ids,
    begin_teach_back,
    finish_teach_back,
    next_question,
    plan_followups,
    record_answer,
    render_transcript_md,
)
from learnloop_sidecar.context import SidecarContext, teach_back_envelope
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.ai_providers import (
    MANUAL_PROVIDER,
    provider_label,
    ready_grading_provider,
    ready_teach_back_provider,
)
from learnloop_sidecar.logging import log_event
from learnloop_sidecar.handlers.sessions import (
    SessionCheckpointInput,
    _require_open_session,
    patch_checkpoint,
)
from learnloop_sidecar.registry import method


class RequestTeachBackInput(ParamsModel):
    # Either directly, or via a sibling practice item on the same LO.
    learning_object_id: str | None = None
    practice_item_id: str | None = None


@method("request_teach_back", RequestTeachBackInput)
def request_teach_back(ctx: SidecarContext, params: RequestTeachBackInput) -> dict[str, Any]:
    """Learner opt-in to a teach-back on an LO: find or mint the card.

    Returns the teach_back practice item id (existing active card, else a
    deterministically minted one — see ``ensure_teach_back_item``). The client
    then drives the normal ``start_teach_back`` flow with it.
    """

    from learnloop.services.teach_back import ensure_teach_back_item

    vault, repository = ctx.require_vault()
    learning_object_id = params.learning_object_id
    if learning_object_id is None:
        if params.practice_item_id is None:
            raise SidecarError(
                "validation_error", "learning_object_id or practice_item_id is required."
            )
        item = vault.practice_items.get(params.practice_item_id)
        if item is None:
            raise SidecarError(
                "not_found", f"Practice Item {params.practice_item_id} was not found."
            )
        learning_object_id = item.learning_object_id
    try:
        item_id, created = ensure_teach_back_item(
            vault.root, vault, repository, learning_object_id
        )
    except TeachBackError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    if created:
        ctx.reload(maintenance=False)
    return versioned({"practice_item_id": item_id, "created": created})


class StartTeachBackInput(ParamsModel):
    session_id: str
    practice_item_id: str


class SubmitTeachBackTurnInput(ParamsModel):
    session_id: str
    practice_item_id: str
    answer_md: str = ""
    # Client-requested early finish: grade whatever has been asked so far.
    finish: bool = False
    latency_seconds: int | None = None


@method("start_teach_back", StartTeachBackInput)
def start_teach_back(ctx: SidecarContext, params: StartTeachBackInput) -> dict[str, Any]:
    """Plan the conversation and persist an empty state into the checkpoint.

    Returns the teaching brief (item prompt), the planned question budget and
    the conversation state. Raises ``provider_unavailable`` when the routed
    teach-back provider is not ready — the conversation cannot start without
    the naive student.
    """

    vault, repository = ctx.require_vault()
    _require_open_session(repository, params.session_id)
    item = _require_teach_back_item(vault, params.practice_item_id)
    provider_name, runtime, client = ready_teach_back_provider(vault)
    if not runtime.ready or client is None:
        raise SidecarError(
            "provider_unavailable",
            f"{provider_label(provider_name)} is unavailable for teach-back.",
            retryable=True,
        )
    # Idempotent: an in-progress conversation for this item (the client lost
    # its local copy, e.g. left the screen and came back) is returned as-is
    # instead of being wiped by a fresh plan.
    state = _load_state(repository, params.session_id, item.id)
    if state is None:
        state = TeachBackState(practice_item_id=item.id, planned=plan_followups(vault, repository, item))
        _persist_state(repository, params.session_id, state)
    learning_object = vault.learning_object_for_item(item)
    return versioned(
        {
            "practice_item_id": item.id,
            "prompt": item.prompt,
            "learning_object_title": (
                learning_object.title if learning_object is not None else item.learning_object_id
            ),
            "budget": min(len(state.planned), vault.config.teach_back.max_followups),
            "state": state.to_dict(),
        }
    )


@method("submit_teach_back_turn", SubmitTeachBackTurnInput)
def submit_teach_back_turn(ctx: SidecarContext, params: SubmitTeachBackTurnInput) -> dict[str, Any]:
    """Record a learner turn, then either ask the next question or finish.

    The first submitted turn is the opening explanation; later turns answer
    the pending AI question. When the plan/budget is exhausted, the client
    requests ``finish``, or the question provider fails mid-conversation, the
    transcript is graded (asked criteria only) as one attempt and the
    checkpoint is cleared in the same call.
    """

    vault, repository = ctx.require_vault()
    _require_open_session(repository, params.session_id)
    item = _require_teach_back_item(vault, params.practice_item_id)
    state = _load_state(repository, params.session_id, item.id)
    try:
        if state is None or not state.turns:
            # Fresh conversation (or the checkpoint envelope was lost): the
            # submitted text is the opening explanation. Planning is
            # deterministic given DB state, so re-planning here is safe.
            planned = state.planned if state is not None and state.planned else None
            state = begin_teach_back(vault, repository, item, opening_md=params.answer_md)
            if planned is not None:
                state.planned = planned
        elif state.turns[-1].role == "ai":
            if params.answer_md.strip():
                record_answer(state, params.answer_md)
            elif not params.finish:
                # Finishing with a dangling question is fine (the unanswered
                # criterion is simply not graded); continuing requires an answer.
                raise TeachBackError("Answer must not be empty.")
        elif params.answer_md.strip():
            # The last turn is already a learner turn (resume after a crash
            # between answer persist and question generation). Any text the
            # learner typed on this resumed submit must not vanish: fold it
            # into the pending learner turn before generating the question.
            pending = state.turns[-1]
            pending.content_md = (
                f"{pending.content_md.rstrip()}\n\n{params.answer_md}"
                if pending.content_md.strip()
                else params.answer_md
            )
    except TeachBackError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    # Persist before calling the provider so the answered turn survives a crash.
    _persist_state(repository, params.session_id, state)

    budget = min(len(state.planned), vault.config.teach_back.max_followups)
    if not params.finish and state.asked_count < budget:
        provider_name, runtime, client = ready_teach_back_provider(vault)
        question = None
        if runtime.ready and client is not None:
            try:
                state, question = next_question(vault, state, client)
            except (CodexUnavailable, TimeoutError):
                # Provider failure mid-conversation: grade the partial
                # transcript (asked criteria only) below.
                question = None
        if question is not None:
            _persist_state(repository, params.session_id, state)
            return versioned(
                {
                    "done": False,
                    "question_md": question["question_md"],
                    "criterion_id": question["criterion_id"],
                    "tier": question["tier"],
                    "facet_targets": question["facet_targets"],
                    "question_number": question["question_number"],
                    "remaining": question["remaining"],
                    "asked": state.asked_count,
                    "budget": budget,
                    "state": state.to_dict(),
                }
            )
    return _finish(ctx, vault, repository, params, state)


def filter_unready_teach_back_items(vault, queue: list, *, grading_provider_override: str | None = None) -> list:
    """Drop teach_back items from a built queue when AI is unavailable for them.

    Handler-level only (never persisted): a teach-back conversation dead-ends
    without the naive-student provider AND without an AI grader (manual
    grading cannot grade a transcript), so the item is only offered when both
    halves are available. The readiness probes only run when the queue
    actually contains a teach_back item.
    """

    def is_teach_back(entry) -> bool:
        item = vault.practice_items.get(entry.practice_item_id)
        return item is not None and item.practice_mode == TEACH_BACK_PRACTICE_MODE

    if not any(is_teach_back(entry) for entry in queue):
        return list(queue)
    _provider, runtime, client = ready_teach_back_provider(vault)
    if runtime.ready and client is not None:
        _grader, grading_runtime, grading_client = ready_grading_provider(
            vault, override=grading_provider_override
        )
        if grading_runtime.ready and grading_client is not None:
            return list(queue)
    return [entry for entry in queue if not is_teach_back(entry)]


def _finish(
    ctx: SidecarContext,
    vault,
    repository,
    params: SubmitTeachBackTurnInput,
    state: TeachBackState,
) -> dict[str, Any]:
    # Imported lazily: practice.py imports queue.py which imports this module
    # (for the queue readiness filter), so a top-level import would be circular.
    from learnloop_sidecar.handlers.practice import (
        _evaluate_followup,
        _log_attempt_recorded,
        _persist_feedback_metadata,
    )

    if ctx.grading_provider_override == MANUAL_PROVIDER:
        # Manual grading cannot grade a teach-back transcript (the AI plays
        # both the student and the grader). Non-retryable by design: retrying
        # cannot succeed until the learner switches grading off manual. The
        # conversation state stays checkpointed.
        raise SidecarError(
            "manual_grading_unsupported",
            "Manual grading cannot grade a teach-back transcript. Switch grading off "
            "manual, then finish the conversation — it is saved and will resume.",
            retryable=False,
        )
    provider_name, runtime, client = ready_grading_provider(vault, override=ctx.grading_provider_override)
    if not runtime.ready or client is None:
        # The conversation state stays checkpointed — retrying the finish once
        # the grader is back grades the same transcript.
        raise SidecarError(
            "provider_unavailable",
            f"{provider_label(provider_name)} is unavailable to grade the teach-back transcript. Retry to grade.",
            retryable=True,
        )
    # Idempotency backstop: if this conversation was already graded (the client
    # lost the response and retried), return the recorded attempt instead of
    # grading the same transcript twice.
    if state.conversation_id is not None:
        existing_attempt_id = repository.find_attempt_id_by_evidence_agent_run(
            practice_item_id=state.practice_item_id,
            agent_run_id=state.conversation_id,
            attempt_type="teach_back",
        )
        if existing_attempt_id is not None:
            repository.clear_session_checkpoint(params.session_id)
            return _existing_attempt_payload(vault, repository, state, existing_attempt_id)
    try:
        result = finish_teach_back(
            vault,
            repository,
            state,
            client,
            session_id=params.session_id,
            latency_seconds=params.latency_seconds,
            agent_run_id=state.conversation_id,
        )
    except (CodexUnavailable, TimeoutError) as exc:
        raise SidecarError(
            "provider_unavailable",
            f"{provider_label(provider_name)} is unavailable to grade the teach-back transcript. Retry to grade.",
            retryable=True,
        ) from exc
    except (AttemptValidationError, TeachBackError, ValueError) as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    # Clear the checkpoint IMMEDIATELY after the attempt is recorded, so a
    # failure in any post-step can never leave a graded conversation to replay
    # (which would double-count the transcript's evidence on retry).
    repository.clear_session_checkpoint(params.session_id)
    # Post-steps are secondary: the attempt is recorded and the response must
    # report it, so failures here are logged, never raised.
    for post_step in (
        lambda: _persist_feedback_metadata(repository, result.attempt, None),
        lambda: _evaluate_followup(vault, repository, params.session_id, result.attempt),
        lambda: _log_attempt_recorded(repository, params.session_id, result.transcript_md, result.attempt),
    ):
        try:
            post_step()
        except Exception as exc:  # noqa: BLE001 - deliberately non-fatal
            log_event(
                "teach_back_post_finish_error",
                session_id=params.session_id,
                attempt_id=result.attempt.attempt_id,
                practice_item_id=state.practice_item_id,
                error=f"{type(exc).__name__}: {exc}",
            )
    return versioned(
        {
            **result.attempt.as_dict(),
            "done": True,
            "transcript_md": result.transcript_md,
            "asked_criterion_ids": result.asked_criterion_ids,
            "graded_criterion_ids": result.graded_criterion_ids,
        }
    )


def _existing_attempt_payload(vault, repository, state: TeachBackState, attempt_id: str) -> dict[str, Any]:
    """Response for a finish retry whose attempt was already recorded.

    Rebuilt from persisted rows (the in-memory ``AttemptResult`` is gone with
    the original call); mirrors the live finish payload's key fields.
    """

    item = vault.practice_items.get(state.practice_item_id)
    attempt = repository.fetch_practice_attempt(attempt_id) or {}
    surprise = repository.latest_attempt_surprise(attempt_id) or {}
    feedback = repository.fetch_attempt_feedback_metadata(attempt_id) or {}
    mastery = repository.mastery_state(attempt.get("learning_object_id") or "")
    item_state = repository.practice_item_state(state.practice_item_id)
    evidence = repository.fetch_grading_evidence(attempt_id)
    graded_criterion_ids = sorted({row.criterion_id for row in evidence})
    return versioned(
        {
            "attempt_id": attempt_id,
            "practice_item_id": state.practice_item_id,
            "learning_object_id": attempt.get("learning_object_id"),
            "rubric_score": attempt.get("rubric_score"),
            "correctness": attempt.get("correctness"),
            "grader_confidence": attempt.get("grader_confidence"),
            "manual_review_reason": attempt.get("manual_review_reason"),
            "fsrs_rating": None,
            "due_at": item_state.due_at if item_state is not None else None,
            "mastery_mean": mastery.logit_mean if mastery is not None else None,
            "mastery_variance": mastery.logit_variance if mastery is not None else None,
            "surprise_direction": surprise.get("surprise_direction"),
            "predictive_surprise": surprise.get("predictive_surprise"),
            "bayesian_surprise": surprise.get("bayesian_surprise"),
            "error_event_ids": [event["id"] for event in repository.error_events_for_attempt(attempt_id)],
            "grading_source": feedback.get("grading_source") or "ai",
            "fallback_reason": feedback.get("fallback_reason"),
            "agent_run_id": feedback.get("agent_run_id"),
            "feedback_md": feedback.get("feedback_md"),
            "repair_suggestions": feedback.get("repair_suggestions") or [],
            "fatal_errors": feedback.get("fatal_errors") or [],
            "debug": {},
            "done": True,
            "duplicate_finish": True,
            "transcript_md": attempt.get("learner_answer_md")
            or (render_transcript_md(state, item) if item is not None else ""),
            "asked_criterion_ids": asked_criterion_ids(state),
            "graded_criterion_ids": graded_criterion_ids,
        }
    )


def _require_teach_back_item(vault, practice_item_id: str):
    item = vault.practice_items.get(practice_item_id)
    if item is None:
        raise SidecarError("not_found", f"Practice Item {practice_item_id} was not found.")
    if item.practice_mode != TEACH_BACK_PRACTICE_MODE:
        raise SidecarError(
            "validation_error",
            f"Practice Item {practice_item_id} is not a teach_back item.",
        )
    return item


def _load_state(repository, session_id: str, practice_item_id: str) -> TeachBackState | None:
    checkpoint = repository.fetch_session_checkpoint(session_id) or {}
    envelope = teach_back_envelope(checkpoint.get("current_answer"))
    if envelope is None:
        return None
    state = TeachBackState.from_dict(envelope["state"])
    if state.practice_item_id != practice_item_id:
        return None
    return state


def _persist_state(repository, session_id: str, state: TeachBackState) -> None:
    patch_checkpoint(
        repository,
        SessionCheckpointInput(
            session_id=session_id,
            current_practice_item_id=state.practice_item_id,
            current_answer=json.dumps(
                {"mode": "teach_back", "state": state.to_dict()}, sort_keys=True
            ),
        ),
    )
