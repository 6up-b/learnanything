"""P3 slice 3, step 10 -- post-cold reader restoration (spec_p3_reader_integration
§11, design B step 10).

Restoration is an INSTRUCTIONAL EVENT AFTER MEASUREMENT (§11). After a cold
administration is submitted and its measurement segment closes, the reader restores:

  1. the cited source blocks (criterion/facet/card provenance -> source);
  2. the learner's own annotation heads, WITH their anchor statuses;
  3. exact learner wording shown ALONGSIDE the source, never merged into it;
  4. tutor / source-object provenance labels (AI / source / learner distinct);
  5. a recorded source-restoration/exposure event + instructional context;
  6. edit/commit/Ask WITHOUT changing the closed observation.

A ``needs_reanchor``/``orphaned`` annotation is shown as its quote/context in an
"anchor needs review" panel, never falsely attached to uncertain text (§11). When
present it composes the LANDED P2 golden-path restoration seam
(``golden_path_restoration.restore``) for the boundary diff + neighborhoods.

Opening restoration material BEFORE the response (:func:`restore_before_response`)
appends a contamination/feedback exposure event and removes cold eligibility (§11,
§15.6) -- the learner is never trapped in a cold task to protect a metric. All reader
events recorded here are salience-only (firewall §C) and cannot mutate the observation.
"""

from __future__ import annotations

from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services import golden_path_restoration as GPR
from learnloop.services import reader_dialogue as RD
from learnloop.services.activities import log_interaction_event
from learnloop.services.salience_firewall import salience_payload
from learnloop.services.span_view import SpanViewError, build_span_view

RESTORATION_SCHEMA_VERSION = 1

# Anchor statuses safe to attach to source text; the rest go to the review panel.
_ATTACHABLE = ("exact", "reanchored", "manually_anchored")
_REVIEW = ("needs_reanchor", "orphaned")


class ReaderRestorationError(ValueError):
    """Domain error for the reader-restoration service."""


def _annotation_provenance(head: Mapping[str, Any]) -> str:
    version = head.get("version") or {}
    return version.get("authorship") or "learner"


def restore(
    repository: Repository,
    *,
    source_id: str,
    extraction_id: str | None = None,
    run_id: str | None = None,
    idempotency_key: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Restore source + annotations after a closed cold observation (§11).

    Composes the P2 golden-path restoration (boundary diff + source neighborhoods)
    when ``run_id`` is given, then overlays the reader's annotation heads with anchor
    statuses and provenance labels. Records a ``reader_restoration`` exposure but
    appends NOTHING to the measurement substrate (cannot mutate the observation)."""

    boundary_diff: dict[str, Any] | None = None
    source_neighborhoods: dict[str, Any] | None = None
    achieved_milestone: str | None = None
    if run_id is not None:
        receipt = GPR.restore(
            repository, run_id=run_id, idempotency_key=idempotency_key or f"reader_restore:{run_id}",
            clock=clock,
        )
        boundary_diff = receipt.boundary_diff
        source_neighborhoods = receipt.source_neighborhoods
        achieved_milestone = receipt.achieved_milestone

    restored: list[dict[str, Any]] = []
    anchor_needs_review: list[dict[str, Any]] = []
    for head in repository.annotations_for_source(source_id):
        if head is None:
            continue
        anchor = head.get("anchor") or {}
        status = anchor.get("status")
        version = head.get("version") or {}
        segments = head.get("segments") or []
        first = segments[0] if segments else {}
        entry = {
            "annotation_id": head["annotation"]["id"],
            "anchor_status": status,
            "provenance": _annotation_provenance(head),  # learner | ai | source distinct
            "learner_text": version.get("learner_text"),
            "what_i_think_is_going_on": version.get("what_i_think_is_going_on"),
            "quote": first.get("exact_quote"),
            "span_id": first.get("span_id"),
        }
        if status in _REVIEW:
            # §11: show quote/context, never attach to uncertain text.
            entry["reason"] = "anchor_needs_review"
            anchor_needs_review.append(entry)
            continue
        # Resolve the cited source block alongside (never merged into) learner wording.
        source_text: str | None = None
        if extraction_id is not None and first.get("span_id"):
            try:
                view = build_span_view(
                    repository, extraction_id, first["span_id"], context="reader_restoration",
                    record=True, clock=clock,
                )
                source_text = view.get("text")
            except SpanViewError:
                source_text = None
        entry["source_text"] = source_text  # alongside, distinct field
        restored.append(entry)

    # Record the reader restoration as a salience-only event; it cannot mutate the
    # closed observation (§11).
    event_id = log_interaction_event(
        repository,
        kind="reader_source_restored",
        origin="learner",
        subject_type="reader_source",
        subject_id=source_id,
        payload=salience_payload({
            "source_id": source_id, "run_id": run_id,
            "restored": len(restored), "needs_review": len(anchor_needs_review),
            "instructional_context": "post_cold_restoration",
        }),
        clock=clock,
    )

    return {
        "schema_version": RESTORATION_SCHEMA_VERSION,
        "source_id": source_id,
        "run_id": run_id,
        "achieved_milestone": achieved_milestone,
        "boundary_diff": boundary_diff,
        "source_neighborhoods": source_neighborhoods,
        "annotations": restored,
        "anchor_needs_review": anchor_needs_review,
        "observation_mutated": False,
        "allows": ["edit", "commit", "ask"],
        "event_id": event_id,
    }


def restore_before_response(
    repository: Repository,
    *,
    extraction_id: str,
    span_id: str,
    cold_surface_id: str | None = None,
    cold_administration_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Opening restoration material BEFORE the cold response (§11, §15.6): appends a
    contamination/feedback exposure event and removes cold eligibility. Delegates to
    the landed P2 ``reader_dialogue.restore_source`` seam, which burns eligibility
    when a cold administration is open. The learner is never trapped in the task."""

    try:
        result = RD.restore_source(
            repository, extraction_id=extraction_id, span_id=span_id,
            cold_surface_id=cold_surface_id, cold_administration_id=cold_administration_id,
            clock=clock,
        )
    except RD.ReaderDialogueError as exc:
        raise ReaderRestorationError(str(exc)) from exc
    return {
        "contamination": True,
        "cold_eligibility_burned": result.get("cold_eligibility_burned", False),
        "text": result.get("text"),
        "event_id": result.get("event_id"),
    }
