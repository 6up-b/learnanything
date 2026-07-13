"""Calibration sessions and dialogue microprobes (probe redesign §5.9 / §8.1)."""

from __future__ import annotations

from typing import Any

from learnloop.services.calibration_sessions import (
    CalibrationSessionError,
    calibration_session_progress,
    start_calibration_session,
    stop_calibration_session,
)
from learnloop.services.probe_dialogue import (
    DialogueBlockError,
    DialogueBlockState,
    begin_dialogue_block,
    end_dialogue_block,
    next_dialogue_turn,
    record_turn_submitted,
)
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class StartCalibrationInput(ParamsModel):
    session_id: str
    goal_id: str | None = None
    learning_object_ids: list[str] | None = None
    time_budget_minutes: int | None = None


class CalibrationSessionInput(ParamsModel):
    calibration_session_id: str


@method("start_calibration_session", StartCalibrationInput)
def start_calibration(ctx: SidecarContext, params: StartCalibrationInput) -> dict[str, Any]:
    """Open a §5.9 calibration session over a goal scope or explicit LO list.

    Ensures episodes, resolves pending ones through parameterized generation,
    orders blocks by cross-LO predictive information rate, and returns the
    initial progress payload (including the first target item).
    """

    from learnloop_sidecar.handlers.ai_providers import ready_grading_provider

    vault, repository = ctx.require_vault()
    _provider, runtime, client = ready_grading_provider(vault, override=ctx.grading_provider_override)
    try:
        progress = start_calibration_session(
            vault,
            repository,
            session_id=params.session_id,
            goal_id=params.goal_id,
            learning_object_ids=params.learning_object_ids,
            time_budget_minutes=params.time_budget_minutes,
            ai_client=client if runtime.ready else None,
        )
    except CalibrationSessionError as error:
        raise SidecarError("invalid_request", str(error)) from error
    # Generation may have written new instrument instances into the vault.
    ctx.reload(maintenance=False)
    return versioned(progress)


@method("get_calibration_session", CalibrationSessionInput)
def get_calibration(ctx: SidecarContext, params: CalibrationSessionInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    try:
        progress = calibration_session_progress(vault, repository, params.calibration_session_id)
    except CalibrationSessionError as error:
        raise SidecarError("not_found", str(error)) from error
    return versioned(progress)


@method("stop_calibration_session", CalibrationSessionInput)
def stop_calibration(ctx: SidecarContext, params: CalibrationSessionInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    stop_calibration_session(repository, params.calibration_session_id)
    try:
        progress = calibration_session_progress(vault, repository, params.calibration_session_id)
    except CalibrationSessionError as error:
        raise SidecarError("not_found", str(error)) from error
    return versioned(progress)


# --- Dialogue microprobes (§8.1) -----------------------------------------------------


class BeginDialogueInput(ParamsModel):
    learning_object_id: str


class DialogueStateInput(ParamsModel):
    dialogue_state: str  # DialogueBlockState JSON, round-tripped by the client


class DialogueTurnSubmittedInput(ParamsModel):
    dialogue_state: str
    presentation_id: str


@method("begin_probe_dialogue", BeginDialogueInput)
def begin_probe_dialogue(ctx: SidecarContext, params: BeginDialogueInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    try:
        state = begin_dialogue_block(vault, repository, params.learning_object_id)
    except DialogueBlockError as error:
        raise SidecarError("invalid_request", str(error)) from error
    return versioned({"dialogue_state": state.to_json(), "planned_turns": len(state.planned_kinds)})


@method("next_probe_dialogue_turn", DialogueStateInput)
def next_probe_dialogue_turn(ctx: SidecarContext, params: DialogueStateInput) -> dict[str, Any]:
    """Mint and commit the next dialogue turn (ephemeral instance +
    presentation). The client submits the learner's committed answer through
    the ordinary `submit_attempt` with the returned presentation id.

    §8.1: with a capable AI provider the turn surface is generated adaptively,
    conditioned on the learner's prior committed answers in the block."""

    from learnloop_sidecar.handlers.ai_providers import ready_grading_provider

    vault, repository = ctx.require_vault()
    state = DialogueBlockState.from_json(params.dialogue_state)
    _provider, runtime, client = ready_grading_provider(vault, override=ctx.grading_provider_override)
    try:
        state, turn = next_dialogue_turn(
            vault, repository, state, ai_client=client if runtime.ready else None
        )
    except DialogueBlockError as error:
        raise SidecarError("invalid_request", str(error)) from error
    # Turn instances are written into the vault on demand.
    if turn is not None:
        ctx.reload(maintenance=False)
    return versioned({"dialogue_state": state.to_json(), "turn": turn})


@method("record_probe_dialogue_turn", DialogueTurnSubmittedInput)
def record_probe_dialogue_turn(ctx: SidecarContext, params: DialogueTurnSubmittedInput) -> dict[str, Any]:
    state = record_turn_submitted(
        DialogueBlockState.from_json(params.dialogue_state), params.presentation_id
    )
    done = state.completed_turns >= len(state.planned_kinds)
    return versioned({"dialogue_state": state.to_json(), "block_complete": done})


@method("end_probe_dialogue", DialogueStateInput)
def end_probe_dialogue(ctx: SidecarContext, params: DialogueStateInput) -> dict[str, Any]:
    """§5.7 block boundary: runs the ordered block-end hook and returns the
    released feedback plus the route (typed transition / next block / ordinary
    practice) so the client can reveal and navigate."""

    from learnloop_sidecar.handlers.ai_providers import ready_grading_provider

    vault, repository = ctx.require_vault()
    state = DialogueBlockState.from_json(params.dialogue_state)
    _provider, runtime, client = ready_grading_provider(vault, override=ctx.grading_provider_override)
    block_end = end_dialogue_block(
        vault, repository, state, ai_client=client if runtime.ready else None
    )
    return versioned({"ended": True, "block_end": block_end})
