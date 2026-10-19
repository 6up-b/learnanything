"""Adaptive difficulty AD2+AD3's desktop RPCs (spec_adaptive_difficulty_v1 §5.12, §9.5, §12).

* ``reader.dose_offer`` -- at an eligible section boundary in the Reader, the
  randomized dose arm's draw (``reading_dose_v1``): its row is written before
  anything is shown; the response names the extra to offer, or none (D21,
  switch ``reading_dose_offers``; outside the successor);
* ``reader.dose_offer_event`` -- the offer's ``delivered``, ``not_delivered``,
  ``taken`` or ``dismissed`` row (never changing the draw);
* ``adaptive_difficulty.readiness`` -- an LO's readiness lines from the
  subject view, labelled as predictions, with the untested rule (a pure read;
  "exam level: not yet predicted" with ``promoted_predictor`` off).

None of them reads a salience magnitude or writes evidence (A2, A12). Desktop
only (pinned in tests/test_mobile_allowlist.py).
"""

from __future__ import annotations

from typing import Any

from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

AD23_RPCS = ("reader.dose_offer", "reader.dose_offer_event", "adaptive_difficulty.readiness")


class ReaderDoseOfferInput(ParamsModel):
    extraction_id: str
    section_id: str
    visit_id: str
    # The Reader's own quick-check conditions at the boundary (anchor mode with
    # section prompts on), and its restraint rules (spec_reader_workbench_v1 §6.1).
    boundary_checks_available: bool = True
    cue_density_off: bool = False
    skim: bool = False
    restored_section: bool = False
    showing_question_id: str | None = None


@method("reader.dose_offer", ReaderDoseOfferInput)
def reader_dose_offer(ctx: SidecarContext, params: ReaderDoseOfferInput) -> dict[str, Any]:
    """The dose arm's draw at a section boundary (§5.12): ``offer`` is the extra to show, or null."""

    from learnloop.adaptive_difficulty.dose import Boundary, decide

    vault, repository = ctx.require_vault()
    decision = decide(vault, repository, Boundary(
        visit_id=params.visit_id, extraction_id=params.extraction_id, section_id=params.section_id,
        boundary_checks_available=params.boundary_checks_available, cue_density_off=params.cue_density_off,
        skim=params.skim, restored_section=params.restored_section,
        showing_question_id=params.showing_question_id,
    ))
    return versioned(decision.as_dict())


class ReaderDoseOfferEventInput(ParamsModel):
    draw_id: str
    event: str


@method("reader.dose_offer_event", ReaderDoseOfferEventInput)
def reader_dose_offer_event(ctx: SidecarContext, params: ReaderDoseOfferEventInput) -> dict[str, Any]:
    """Record that the offer was delivered, not delivered, taken or dismissed."""

    from learnloop.adaptive_difficulty.dose import UPTAKE, record_uptake

    if params.event not in UPTAKE:
        raise SidecarError("validation_error", f"unknown dose offer event {params.event!r}")
    vault, repository = ctx.require_vault()
    try:
        row_id = record_uptake(vault, repository, params.draw_id, params.event)
    except ValueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned({"row_id": row_id, "event": params.event})


class AdaptiveDifficultyReadinessInput(ParamsModel):
    learning_object_id: str


@method("adaptive_difficulty.readiness", AdaptiveDifficultyReadinessInput)
def adaptive_difficulty_readiness(ctx: SidecarContext, params: AdaptiveDifficultyReadinessInput) -> dict[str, Any]:
    """An LO's readiness lines (predictions; "untested" where it has no answer of its own). Writes nothing."""

    from learnloop.adaptive_difficulty.readiness import lo_readiness

    vault, repository = ctx.require_vault()
    if params.learning_object_id not in vault.learning_objects:
        raise SidecarError("not_found", f"No learning object {params.learning_object_id!r}.")
    return versioned(lo_readiness(vault, repository, params.learning_object_id))


__all__ = ["AD23_RPCS"]
