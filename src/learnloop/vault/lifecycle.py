"""Serving lifecycle of a practice item and its owning Learning Object.

``LearningObject.status`` is the learner's lifecycle switch: ``active``,
``dormant`` (parked) or ``resolved`` (done). Only an ``active`` LO's items may be
served; a dormant or resolved LO has been put away by the learner, and bringing
its items back would ignore that choice (daily-loop audit 2026-10-11).

A card the reader's reference-question sweep adopted
(``reader.reader_authoring.adopt_reference_questions``) is served only while
its kill switch ``tutor_qa.adopt_reference_questions`` is on. Off restores the
baseline queue: the card stays in the vault, active and linked to its question,
and turning the switch back on serves it again (re-review F8).

Every serving door asks this one module: the scheduler's candidate loop and its
by-id follow-up lane, the exam pool, the probe pool and the re-probe producer,
and the sidecar's by-id serve doors. It is a pure read of vault YAML and config.
Nothing is persisted or deactivated, so setting the LO back to ``active`` (or
the switch back on) makes its items servable again immediately with their
history, FSRS state and projections untouched.
"""

from __future__ import annotations

from typing import Any

from learnloop.vault.models import LoadedVault, PracticeItem

SERVABLE_LEARNING_OBJECT_STATUS = "active"

#: Versioned provenance of a card the reference-question sweep adopted, as
#: written on the card (``provenance.adoption``) and in its authoring event's
#: ``mechanism``. Write-time adoption (``reader_author_qa``) is not marked: it
#: predates the sweep and is never gated by its switch.
REFERENCE_ADOPTION_MECHANISM = "reader_reference_adoption_v1"
REFERENCE_ADOPTION_DISABLED = "reference_adoption_disabled"
#: Versioned provenance of a prerequisite the learner-text gap pipeline created
#: (``provenance.mechanism`` on the LO). Its items are served only while
#: ``learner_text_gaps.create_prerequisites_enabled`` (and the pipeline) is on:
#: off restores the predecessor's queue; the LO stays in the vault.
LEARNER_TEXT_GAP_MECHANISM = "learner_text_gap_v1"
LEARNER_TEXT_GAP_DISABLED = "learner_text_gap_disabled"


def created_from_learner_text(learning_object: Any) -> bool:
    provenance = getattr(learning_object, "provenance", None)
    extra: dict[str, Any] = getattr(provenance, "model_extra", None) or {}
    return extra.get("mechanism") == LEARNER_TEXT_GAP_MECHANISM


def _learner_text_gap_creations_on(vault: LoadedVault) -> bool:
    section = getattr(vault.config, "learner_text_gaps", None)
    return section is None or bool(section.enabled and section.create_prerequisites_enabled)


def learner_text_gap_edge_in_effect(config: Any, edge: Any) -> bool:
    """Is this relation edge part of the loaded vault (Codex review F10)?

    Every edge is, except a ``prerequisite`` edge the learner-text gap
    pipeline added (``provenance.mechanism == learner_text_gap_v1``) while
    its switch is off: a matched prerequisite's edge needs
    ``learner_text_gaps.add_edges_enabled``, a created prerequisite's edge
    (``provenance.origin == "creation"``) needs ``create_prerequisites_enabled``,
    both need ``enabled``. Off, the edge stays in ``concepts/relations.yaml``
    but nothing reads it (placement order, declared prerequisites, the
    diagnoser's neighbourhood, the map): the predecessor's graph exactly.
    """

    extra: dict[str, Any] = getattr(edge, "model_extra", None) or {}
    provenance = extra.get("provenance")
    if not isinstance(provenance, dict) or provenance.get("mechanism") != LEARNER_TEXT_GAP_MECHANISM:
        return True
    section = getattr(config, "learner_text_gaps", None)
    if section is None:
        return True
    if not section.enabled:
        return False
    if provenance.get("origin") == "creation":
        return bool(section.create_prerequisites_enabled)
    return bool(section.add_edges_enabled)


def adopted_by_reference_sweep(item: PracticeItem) -> bool:
    """True for a card the reader's reference-question sweep adopted."""

    extra: dict[str, Any] = item.provenance.model_extra or {}
    return extra.get("adoption") == REFERENCE_ADOPTION_MECHANISM


def learning_object_serving_block(vault: LoadedVault, learning_object_id: str | None) -> str | None:
    """Why the LO's items may not be served now, or ``None`` when they may.

    Returns ``"learning_object_missing"`` for an unknown id and
    ``"learning_object_<status>"`` (``dormant`` / ``resolved``) for an LO the
    learner has put away."""

    learning_object = vault.learning_objects.get(str(learning_object_id or ""))
    if learning_object is None:
        return "learning_object_missing"
    if learning_object.status != SERVABLE_LEARNING_OBJECT_STATUS:
        return f"learning_object_{learning_object.status}"
    if created_from_learner_text(learning_object) and not _learner_text_gap_creations_on(vault):
        return LEARNER_TEXT_GAP_DISABLED
    return None


def learning_object_servable(vault: LoadedVault, learning_object_id: str | None) -> bool:
    return learning_object_serving_block(vault, learning_object_id) is None


def practice_item_serving_block(vault: LoadedVault, item: PracticeItem) -> str | None:
    """Why this item may not be served now, or ``None`` when it may.

    Its LO's block first (``learning_object_serving_block``), then
    ``"reference_adoption_disabled"`` for a sweep-adopted card while
    ``tutor_qa.adopt_reference_questions`` is off."""

    block = learning_object_serving_block(vault, item.learning_object_id)
    if block is not None:
        return block
    if adopted_by_reference_sweep(item) and not vault.config.tutor_qa.adopt_reference_questions:
        return REFERENCE_ADOPTION_DISABLED
    return None


def practice_item_servable(vault: LoadedVault, item: PracticeItem) -> bool:
    return practice_item_serving_block(vault, item) is None
