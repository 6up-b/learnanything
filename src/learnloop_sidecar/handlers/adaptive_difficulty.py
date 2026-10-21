"""Adaptive difficulty AD2+AD3's desktop RPCs (spec_adaptive_difficulty_v1 §5.12, §9.5, §12).

* ``reader.dose_offer`` -- at an eligible section boundary in the Reader, the
  randomized dose arm's draw (``reading_dose_v1``): its row is written before
  anything is shown; the response names the extra to offer, or none (D21,
  switch ``reading_dose_offers``; outside the successor);
* ``reader.dose_offer_event`` -- the offer's ``delivered``, ``not_delivered``,
  ``taken`` or ``dismissed`` row (never changing the draw);
* ``adaptive_difficulty.readiness`` -- an LO's readiness lines from the
  subject view, labelled as predictions, with the untested rule (a pure read;
  "exam level: not yet predicted" with ``promoted_predictor`` off);
* ``adaptive_difficulty.why_item`` -- "why this item" for a served plan item:
  the one line of the draw that chose it (§12), or none (a pure read).

None of them reads a salience magnitude or writes evidence (A2, A12). Desktop
only (pinned in tests/test_mobile_allowlist.py).
"""

from __future__ import annotations

from typing import Any

from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

AD23_RPCS = ("reader.dose_offer", "reader.dose_offer_event", "adaptive_difficulty.readiness",
             "adaptive_difficulty.why_item")


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
    from learnloop.adaptive_difficulty.operation import optional_operation

    from learnloop.adaptive_difficulty.operation import is_denial

    vault, repository = ctx.require_vault()
    try:
        return versioned(_dose_offer(vault, repository, params))
    except Exception as exc:
        if not is_denial(exc):
            raise
        # The AD guard refused something in the decision: AD is unavailable for it and nothing of it
        # is shown (the incumbent: no offer; owner decision 2026-10-21).
        return versioned({"eligible": False, "reason": "unavailable", "draw_id": None, "offer": None})


def _dose_offer(vault: Any, repository: Any, params: ReaderDoseOfferInput) -> dict[str, Any]:
    from learnloop.adaptive_difficulty.dose import Boundary, decide
    from learnloop.adaptive_difficulty.operation import optional_operation

    # One AD operation for the draw and the response (A8; Codex verify F23; the AD23 redesign).
    with optional_operation(vault, repository) as op:
        view = op.view if op is not None else None
        decision = decide(vault, repository, Boundary(
            visit_id=params.visit_id, extraction_id=params.extraction_id, section_id=params.section_id,
            boundary_checks_available=params.boundary_checks_available, cue_density_off=params.cue_density_off,
            skim=params.skim, restored_section=params.restored_section,
            showing_question_id=params.showing_question_id,
        ), view=view)
        result = decision.as_dict()
        offer = result.get("offer")
        if offer and offer.get("variant") == "extra_question" and view is not None:
            # The exact question the draw chose, so the Reader shows it (Codex review F6), never the
            # section's ordinary check; read at response time, nothing more persisted.
            offer["question"] = _offered_question(repository, view, (offer.get("content") or {}).get("question_id"))
            if offer["question"] is None:
                # Withheld between the draw and the response: nothing of it is shown.
                result["offer"] = None
    return result


def _offered_question(repository: Any, view: Any, question_id: Any) -> dict[str, Any] | None:
    import json
    from contextlib import closing

    from learnloop.db.connection import connect

    if not question_id:
        return None
    # Revalidated through the material view at response time: a question whose section, anchors
    # or cited spans are held out now is never returned (Codex verify F23).
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = view.question(connection, question_id)
    if row is None:
        return None
    try:
        spans = [str(span) for span in json.loads(row.get("span_ids_json") or "[]")]
    except (TypeError, ValueError):
        spans = []
    return {"question_id": str(row["id"]), "section_id": row.get("section_id"), "prompt": row.get("question_md") or "",
            "expected_answer": row.get("expected_answer_md") or "", "span_ids": spans}


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
        # Gated at the write (fix round 10, F36): AD or the dose arm off, protection unavailable,
        # or the offer withheld now records nothing and answers a harmless no-op.
        row_id = record_uptake(vault, repository, params.draw_id, params.event)
    except ValueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned({"row_id": row_id, "event": params.event, "recorded": row_id is not None})


class AdaptiveDifficultyReadinessInput(ParamsModel):
    learning_object_id: str


@method("adaptive_difficulty.readiness", AdaptiveDifficultyReadinessInput)
def adaptive_difficulty_readiness(ctx: SidecarContext, params: AdaptiveDifficultyReadinessInput) -> dict[str, Any]:
    """An LO's readiness lines (predictions; "untested" where it has no answer of its own). Writes nothing."""

    from learnloop.adaptive_difficulty.readiness import lo_readiness

    from learnloop.adaptive_difficulty.operation import is_denial

    vault, repository = ctx.require_vault()
    if params.learning_object_id not in vault.learning_objects:
        raise SidecarError("not_found", f"No learning object {params.learning_object_id!r}.")
    try:
        return versioned(lo_readiness(vault, repository, params.learning_object_id))
    except Exception as exc:
        if not is_denial(exc):
            raise
        from learnloop.adaptive_difficulty.readiness import NOT_PREDICTED, READINESS_VERSION

        return versioned({"version": READINESS_VERSION, "predicted": False, "line": NOT_PREDICTED, "cells": []})


class AdaptiveDifficultyWhyItemInput(ParamsModel):
    plan_presentation_id: str


@method("adaptive_difficulty.why_item", AdaptiveDifficultyWhyItemInput)
def adaptive_difficulty_why_item(ctx: SidecarContext, params: AdaptiveDifficultyWhyItemInput) -> dict[str, Any]:
    """"Why this item" (§12): ``{"why": null}`` when no AD draw chose the served item. Writes nothing."""

    from contextlib import closing

    from learnloop.adaptive_difficulty.serving import why_for_presentation
    from learnloop.db.connection import connect

    from learnloop.adaptive_difficulty.operation import optional_operation

    from learnloop.adaptive_difficulty.operation import is_denial

    vault, repository = ctx.require_vault()
    try:
        with optional_operation(vault, repository) as op, \
                closing(connect(repository.sqlite_path, read_only=True)) as connection:
            found = why_for_presentation(connection, params.plan_presentation_id, view=op.view) \
                if op is not None else None
    except Exception as exc:
        if not is_denial(exc):
            raise
        found = None  # the AD guard refused something: no "why" is shown
    return versioned({"why": found["why"] if found else None, "mode": found["mode"] if found else None})


__all__ = ["AD23_RPCS"]
