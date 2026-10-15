"""Marking exam material on a reading (protection redesign, 2026-10-15).

Exam and held-out protection never carries to another reading by content,
alias or label matching (``content.sources.exam_material``, rule 4): a reading
of a book with exam material marked on another reading (a re-read, a reading
of a new revision) is withheld whole until the owner marks it. This module is
the owner's side of that rule:

* :func:`held_back_reading`: the reading the Reader opens for a book, when it
  is withheld whole; the book's card then says so in plain words and offers
  "Mark exam material on this reading" (:data:`MARK_ACTION`), and doctor names
  it (``source:reading_held_back``);
* :func:`suggest_marks`: what to mark, pre-filled. It is a suggestion and
  never an authority: every unit of the reading that may hold material
  protected on a marked reading of the book (the unit its unit maps to, the
  units its aliases land in, the units on the same pages), over-inclusive by
  design, shown to the owner by name before anything is written;
* :func:`mark_plan` / :func:`mark_exam_material`: the confirmation the card
  shows, and the owner's confirmed marking: the suggested units held out
  (``held_out_evaluation``) in the reading's own unit selection, and the
  owner's mark (``exam_material.PROTECTION_MARK_KEY``) that makes the reading
  marked even when nothing on it is held out. The earlier reading keeps its
  own marks exactly as they are.

Nothing here changes persisted meaning: the unit selection is WORKFLOW state
that replay never reads.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.content.pipeline import reread
from learnloop.content.sources import span_aliases
from learnloop.content.sources.exam_material import (
    HELD_OUT_EVALUATION,
    PROTECTION_MARK_KEY,
    exam_material,
    source_marks,
)

#: The card's action (``source_action``) and its label.
MARK_ACTION = "mark_exam_material"
MARK_LABEL = "Mark exam material on this reading"
#: The card's line while the reading the Reader opens is held back, and its details.
HELD_BACK_LINE = "This reading is held back until you mark its exam material"
HELD_BACK_DETAILS = (
    "You marked exam material in another reading of this book. LearnLoop doesn't guess where that material is "
    "in this reading, so it keeps the whole reading out of explanations, questions and search until you mark "
    "its exam material here. The other reading stays protected as you marked it."
)
#: How many unit names the confirmation lists before "and N more".
_LISTED = 8


def held_back_reading(vault: Any, repository: Any, source_id: str) -> str | None:
    """The reading the Reader opens for the book, when it is withheld whole
    until exam material is marked on it (``exam_material`` rule 4); else None."""

    reading = reread.reread_reading(repository, source_id)
    if reading is None:
        return None
    marks = source_marks(vault, repository).get(str(source_id))
    return reading if marks is not None and reading in marks.unmarked else None


def held_back_readings(vault: Any, repository: Any) -> list[dict[str, Any]]:
    """Every book whose current reading is held back: ``{"source_id",
    "extraction_id", "older"}`` (``older``: the book's other extractions also
    held back, which no Reader opens)."""

    found: list[dict[str, Any]] = []
    for source_id, marks in sorted(source_marks(vault, repository).items()):
        reading = reread.reread_reading(repository, source_id)
        if reading is None or reading not in marks.unmarked:
            continue
        found.append({"source_id": source_id, "extraction_id": reading,
                      "older": [extraction_id for extraction_id in marks.unmarked if extraction_id != reading]})
    return found


@dataclass(frozen=True)
class MarkSuggestion:
    """What :func:`mark_exam_material` would hold out on a reading."""

    extraction_id: str
    #: The reading's raw unit ids suggested held out, in outline order.
    held_out: tuple[str, ...]
    #: Their labels, in the same order.
    labels: tuple[str, ...]
    #: The marked readings the suggestion was made from.
    from_readings: tuple[str, ...]


def _protected_spans(material: Any, extraction_id: str, block_spans: list[str]) -> set[str]:
    """The spans of a marked reading under positional protection: its held-out
    part, and its exam units (rule 2), never the whole-source exam role (rule
    1, which reaches every reading anyway)."""

    held = material.held_out
    if extraction_id in held.extractions:
        return set(block_spans)
    spans = {span for extraction, span in held.spans if extraction == extraction_id}
    if extraction_id not in material.material.extractions:
        spans |= {span for extraction, span in material.material.spans if extraction == extraction_id}
    return spans


def suggest_marks(vault: Any, repository: Any, extraction_id: str) -> MarkSuggestion:
    """Every unit of ``extraction_id`` that may hold material protected on a
    marked reading of its book: over-inclusive, a suggestion the owner checks
    before anything is written, never a carry of protection.

    From each marked reading: the unit its protected units map to
    (``reread.unit_map``), the unit each protected span's alias lands in
    (the same text or the same place), and every unit with a block on a page
    a protected block is on."""

    extraction_id = str(extraction_id)
    source_id = span_aliases.reading_source(repository, extraction_id)
    marks = source_marks(vault, repository).get(str(source_id)) if source_id else None
    target = repository.load_document_ir(extraction_id)
    if marks is None or target is None:
        return MarkSuggestion(extraction_id, (), (), ())
    material = exam_material(vault, repository)
    unit_of_span = {span: unit.unit_id for unit in target.units for span in unit.span_ids}
    units_on_page: dict[int, set[str]] = {}
    for block in target.blocks:
        if block.page is not None and block.span_id in unit_of_span:
            units_on_page.setdefault(int(block.page), set()).add(unit_of_span[block.span_id])
    chosen: set[str] = set()
    origins: list[str] = []
    for origin in marks.marked:
        if origin == extraction_id:
            continue
        old = repository.load_document_ir(origin)
        if old is None:
            continue
        protected = _protected_spans(material, origin, [block.span_id for block in old.blocks])
        if not protected:
            continue
        origins.append(origin)
        aliases = span_aliases.alias_map(repository, origin, extraction_id)
        for span in protected:
            hit = aliases.get(span)
            if hit is not None and hit[0] in unit_of_span:
                chosen.add(unit_of_span[hit[0]])
        mapped = reread.unit_map(old, target, aliases)
        for unit in old.units:
            if protected.intersection(unit.span_ids) and mapped.get(unit.unit_id):
                chosen.add(str(mapped[unit.unit_id]))
        for block in old.blocks:
            if block.span_id in protected and block.page is not None:
                chosen |= units_on_page.get(int(block.page), set())
    ordered = [unit for unit in target.units if unit.unit_id in chosen]
    return MarkSuggestion(extraction_id, tuple(unit.unit_id for unit in ordered),
                          tuple(" ".join(str(unit.label or unit.unit_id).split()) for unit in ordered),
                          tuple(sorted(origins)))


def _listed(labels: tuple[str, ...]) -> str:
    shown = list(labels[:_LISTED])
    more = len(labels) - len(shown)
    return "; ".join(shown) + (f"; and {more} more" if more > 0 else "")


def mark_plan(vault: Any, repository: Any, source_id: str, *, title: str | None = None) -> dict[str, Any] | None:
    """The card's confirmation before marking, in plain words; None when the
    book's reading is not held back."""

    reading = held_back_reading(vault, repository, source_id)
    if reading is None:
        return None
    suggestion = suggest_marks(vault, repository, reading)
    if suggestion.labels:
        lines = [f"Held out as exam material: {_listed(suggestion.labels)}.",
                 "These are suggested from what you marked in the other reading: check them. The rest of this "
                 "reading becomes available for explanations, questions and search."]
    else:
        lines = ["Nothing in this reading matches the exam material you marked in the other reading.",
                 "Marking it makes the whole reading available for explanations, questions and search."]
    name = title or "this book"
    return {
        "source_id": str(source_id),
        "extraction_id": reading,
        "held_out_unit_ids": list(suggestion.held_out),
        "needs_confirmation": True,
        "title": f"Mark exam material on this reading of {name}?",
        "lines": lines,
        "confirm_label": "Mark it" if not suggestion.labels else "Mark them",
        "cancel_label": "Not now",
    }


def mark_exam_material(vault: Any, repository: Any, source_id: str, *,
                       clock: Clock | None = None) -> dict[str, Any] | None:
    """The owner's confirmed marking of the reading the Reader opens: the
    suggested units held out in its own unit selection, and the owner's mark
    (``PROTECTION_MARK_KEY``), so ``exam_material`` reads it as marked (rule
    4). A carry-over the re-read still owes is finished first, so the study
    map's chapters reach the selection the marks are written into. None when
    the book's reading is not held back."""

    if reread.carry_owed(repository, source_id) is not None:
        reread.finish_carry_over(repository, source_id, clock=clock)
    reading = held_back_reading(vault, repository, source_id)
    if reading is None:
        return None
    suggestion = suggest_marks(vault, repository, reading)
    stored: Mapping[str, Any] = repository.get_unit_selection(reading) or {}
    modes = dict(stored.get("exam_use_modes") or {})
    for unit_id in suggestion.held_out:
        modes[unit_id] = HELD_OUT_EVALUATION
    metadata = dict(stored.get("exam_paper_metadata") or {})
    metadata[PROTECTION_MARK_KEY] = {"at": utc_now_iso(clock), "from": list(suggestion.from_readings),
                                     "held_out": list(suggestion.held_out)}
    run = repository.get_extraction_run(reading) or {}
    revision = repository.get_source_revision(str(run.get("revision_id") or "")) or {}
    repository.upsert_unit_selection(
        extraction_id=reading, source_id=revision.get("source_id") or str(source_id),
        revision_id=run.get("revision_id"), selected_unit_ids=list(stored.get("selected_unit_ids") or []),
        boundary_overrides=list(stored.get("boundary_overrides") or []),
        needs_review=list(stored.get("needs_review") or []), exam_use_modes=modes, exam_paper_metadata=metadata,
        role_override=stored.get("role_override"), clock=clock,
    )
    return {"extraction_id": reading, "held_out_unit_ids": list(suggestion.held_out),
            "from_extraction_ids": list(suggestion.from_readings)}


__all__ = [
    "HELD_BACK_DETAILS",
    "HELD_BACK_LINE",
    "MARK_ACTION",
    "MARK_LABEL",
    "MarkSuggestion",
    "held_back_reading",
    "held_back_readings",
    "mark_exam_material",
    "mark_plan",
    "suggest_marks",
]
