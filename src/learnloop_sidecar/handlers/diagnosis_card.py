"""Slice 1 M2 RPCs: the asynchronous diagnosis status and the diagnosis card.

``diagnosis_status(attempt_id)`` returns the status (``pending`` |
``not_needed`` | ``done`` | ``failed``) and, when done, the card: the summary,
the repair suggestions (serialized as the feedback bundle serializes them), the
validated "made this mistake before" citations and the prerequisite-gap
hypothesis. The feedback view polls it every 2-3 s while pending (§11).

``record_diagnosis_feedback`` records the one optional tap (§12.2).
"""

from __future__ import annotations

from typing import Any

from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class DiagnosisStatusInput(ParamsModel):
    attempt_id: str


class DiagnosisFeedbackInput(ParamsModel):
    attempt_id: str
    diagnosis_id: str
    response: str
    cited_attempt_id: str | None = None
    shown_at: str | None = None


@method("diagnosis_status", DiagnosisStatusInput)
def diagnosis_status(ctx: SidecarContext, params: DiagnosisStatusInput) -> dict[str, Any]:
    from learnloop.diagnosis.split.card import debit_displayed_repairs, diagnosis_card
    from learnloop.diagnosis.split.jobs import DONE

    vault, repository = ctx.require_vault()
    attempt = repository.fetch_practice_attempt(params.attempt_id)
    if attempt is None:
        raise SidecarError("not_found", f"Attempt {params.attempt_id} was not found.")
    card = diagnosis_card(vault, repository, params.attempt_id)
    if card["status"] == DONE:
        # The view shows the diagnosis's repairs once this reports done (in
        # the card, and in the feedback bundle it then re-reads), whether or
        # not the card itself is enabled: charge them now, once (§8).
        diagnosis = repository.attempt_diagnosis(str(card["diagnosis_id"])) or {}
        debit_displayed_repairs(
            repository,
            attempt=attempt,
            diagnosis=diagnosis,
            repair_suggestions=list(card.get("repair_suggestions") or []),
            learning_object_id=str(attempt.get("learning_object_id") or "") or None,
        )
    return versioned(card)


@method("record_diagnosis_feedback", DiagnosisFeedbackInput)
def record_diagnosis_feedback(ctx: SidecarContext, params: DiagnosisFeedbackInput) -> dict[str, Any]:
    from learnloop.diagnosis.split.card import CardError, record_card_tap

    vault, repository = ctx.require_vault()
    try:
        result = record_card_tap(
            vault,
            repository,
            attempt_id=params.attempt_id,
            diagnosis_id=params.diagnosis_id,
            response=params.response,
            cited_attempt_id=params.cited_attempt_id,
            shown_at=params.shown_at,
        )
    except CardError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)
