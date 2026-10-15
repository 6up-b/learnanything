"""Marking exam material on a reading (protection redesign, 2026-10-15;
extraction identity, the same day's fourth round).

Exam and held-out protection never carries to another reading by content,
alias or label matching, and every mark names the reading it was made on
(``content.sources.exam_material``, rule 4): a reading of a book with exam
material marked on another reading (a re-read, a reading of a new revision),
or of a book whose legacy mark names no reading at all, is withheld whole
until the owner marks it. This module is the owner's side of that rule:

* :func:`held_back_reading`: the reading the Reader opens for a book, when it
  is withheld whole; the book's card then says so in plain words
  (:func:`held_back_details`: why, a legacy mark included) and offers "Mark
  exam material on this reading" (:data:`MARK_ACTION`), and doctor names it
  (``source:reading_held_back``);
* :func:`suggest_marks`: what to mark, pre-filled. It is a suggestion and
  never an authority: every unit of the reading that may hold material any
  mark of the book protects (``exam_material.protected_spans_by_reading``:
  the unit its unit maps to, the units its aliases land in, the units on the
  same pages; a legacy mark's own unit ids), over-inclusive by design, shown
  to the owner by name before anything is written;
* :func:`mark_plan` / :func:`mark_exam_material`: the confirmation the card
  shows, bound to the reading and the proposal it shows (``proposal_hash``),
  and the owner's confirmed marking: exactly the confirmed units held out
  (``held_out_evaluation``) in the reading's own unit selection, with the
  owner's mark (``exam_material.PROTECTION_MARK_KEY``) and the reading the
  marks were made on (``exam_material.MARKS_MADE_ON_KEY``), with the
  book's unplaced marks the owner reviewed (``exam_material.
  REVIEWED_UNPLACED``: a later or changed one holds the reading back again)
  and the owner's verdict in ``judgment_ledger`` (:data:`MARK_JUDGMENT_TASK`),
  in one transaction. If the reading the Reader opens, or the proposal for
  it, changed since it was shown, nothing is written and a fresh
  confirmation is returned (:class:`StaleMarkConfirmation`; final verify
  F13). The earlier readings keep their own marks exactly as they are.

Nothing here changes persisted meaning: the unit selection is WORKFLOW state
that replay never reads, and the verdict is an append-only owner judgment
that no replayer reads.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.content.pipeline import reread
from learnloop.content.sources import span_aliases
from learnloop.content.sources.exam_material import (
    AMBIGUOUS_SCOPE,
    AMBIGUOUS_SELECTION,
    HELD_OUT_EVALUATION,
    MARKS_MADE_ON_KEY,
    PROTECTION_MARK_KEY,
    REVIEWED_UNPLACED,
    SourceMarks,
    marks_made_on,
    protected_spans_by_reading,
    source_marks,
)
from learnloop.db.stores.judgments import append_judgment

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
#: The details when the book's marks were made before LearnLoop recorded the
#: reading each was made on (a legacy mark: ``SourceMarks.ambiguous``).
AMBIGUOUS_DETAILS = (
    "You marked exam material in this book before LearnLoop recorded which reading you marked it on, so it can't "
    "tell where that material is now. It keeps every reading of the book out of explanations, questions and "
    "search until you mark its exam material here. Marking it records exactly what is held out on this reading."
)
#: The details when what makes it unclear is exam questions LearnLoop found
#: before it recorded which reading it found them on (``SourceMarks.ambiguous``
#: is ``signal`` only: an inventory's held-out signal of unknown reading).
FOUND_DETAILS = (
    "LearnLoop found exam questions in this book before it recorded which reading it found them on, so it can't "
    "tell where they are now. It keeps every reading of the book out of explanations, questions and search until "
    "you mark its exam material here. Marking it records exactly what is held out on this reading."
)
#: The ``judgment_ledger`` task of the owner's marking verdict (``judge = owner``).
MARK_JUDGMENT_TASK = "exam_material_marking"
#: The confirmation's first line when what it showed changed before the owner confirmed.
CHANGED_LINE = "This reading changed since you looked, so nothing was marked yet. Check it again:"
#: How many unit names the confirmation lists before "and N more".
_LISTED = 8


class StaleMarkConfirmation(Exception):
    """The confirmation the owner gave no longer matches the reading the
    Reader opens or the proposal for it; ``plan`` is the fresh confirmation
    (None when nothing is held back any more)."""

    def __init__(self, plan: dict[str, Any] | None) -> None:
        super().__init__("the marking confirmation is out of date")
        self.plan = plan


def held_back_reading(vault: Any, repository: Any, source_id: str) -> str | None:
    """The reading the Reader opens for the book, when it is withheld whole
    until exam material is marked on it (``exam_material`` rule 4); else None."""

    reading = reread.reread_reading(repository, source_id)
    if reading is None:
        return None
    marks = source_marks(vault, repository).get(str(source_id))
    return reading if marks is not None and reading in marks.unmarked else None


def held_back_details(vault: Any, repository: Any, source_id: str) -> str:
    """The card's details for a held-back reading: why, in plain words."""

    marks = source_marks(vault, repository).get(str(source_id))
    if marks is None or not marks.ambiguous:
        return HELD_BACK_DETAILS
    owners = {AMBIGUOUS_SCOPE, AMBIGUOUS_SELECTION}
    return AMBIGUOUS_DETAILS if owners & set(marks.ambiguous) else FOUND_DETAILS


def held_back_readings(vault: Any, repository: Any) -> list[dict[str, Any]]:
    """Every book whose current reading is held back: ``{"source_id",
    "extraction_id", "older", "ambiguous"}`` (``older``: the book's other
    extractions also held back, which no Reader opens; ``ambiguous``: the
    kinds of legacy mark that name no reading)."""

    found: list[dict[str, Any]] = []
    for source_id, marks in sorted(source_marks(vault, repository).items()):
        reading = reread.reread_reading(repository, source_id)
        if reading is None or reading not in marks.unmarked:
            continue
        found.append({"source_id": source_id, "extraction_id": reading,
                      "older": [extraction_id for extraction_id in marks.unmarked if extraction_id != reading],
                      "ambiguous": list(marks.ambiguous)})
    return found


@dataclass(frozen=True)
class MarkSuggestion:
    """What :func:`mark_exam_material` would hold out on a reading."""

    extraction_id: str
    #: The reading's raw unit ids suggested held out, in outline order.
    held_out: tuple[str, ...]
    #: Their labels, in the same order.
    labels: tuple[str, ...]
    #: The readings the suggestion was made from (the reading itself, for a legacy mark on it).
    from_readings: tuple[str, ...]


def suggest_marks(vault: Any, repository: Any, extraction_id: str) -> MarkSuggestion:
    """Every unit of ``extraction_id`` that may hold material any mark of its
    book protects: over-inclusive, a suggestion the owner checks before
    anything is written, never a carry of protection.

    From each other reading with protected spans: the unit its protected
    units map to (``reread.unit_map``), the unit each protected span's alias
    lands in (the same text or the same place), and every unit with a block
    on a page a protected block is on. On the reading itself: the units a
    legacy mark or a reused inventory names there."""

    extraction_id = str(extraction_id)
    source_id = span_aliases.reading_source(repository, extraction_id)
    target = repository.load_document_ir(extraction_id)
    if not source_id or target is None or str(source_id) not in source_marks(vault, repository):
        return MarkSuggestion(extraction_id, (), (), ())
    protected_by = protected_spans_by_reading(vault, repository, str(source_id))
    unit_of_span = {span: unit.unit_id for unit in target.units for span in unit.span_ids}
    units_on_page: dict[int, set[str]] = {}
    for block in target.blocks:
        if block.page is not None and block.span_id in unit_of_span:
            units_on_page.setdefault(int(block.page), set()).add(unit_of_span[block.span_id])
    chosen: set[str] = set()
    origins: list[str] = []
    own = protected_by.get(extraction_id, set())
    if own:
        chosen |= {unit_of_span[span] for span in own if span in unit_of_span}
        origins.append(extraction_id)
    for origin, protected in sorted(protected_by.items()):
        if origin == extraction_id or not protected:
            continue
        old = repository.load_document_ir(origin)
        if old is None:
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
                          tuple(sorted(dict.fromkeys(origins))))


def _listed(labels: tuple[str, ...]) -> str:
    shown = list(labels[:_LISTED])
    more = len(labels) - len(shown)
    return "; ".join(shown) + (f"; and {more} more" if more > 0 else "")


def _marks_state(selection: Mapping[str, Any] | None) -> dict[str, Any]:
    """What a reading's own selection says about protection (part of the
    proposal: a mark written meanwhile makes the confirmation stale)."""

    stored = selection or {}
    metadata = dict(stored.get("exam_paper_metadata") or {})
    return {"modes": dict(sorted(dict(stored.get("exam_use_modes") or {}).items())),
            "marked": metadata.get(PROTECTION_MARK_KEY), "made_on": metadata.get(MARKS_MADE_ON_KEY)}


def proposal_hash(source_id: str, extraction_id: str, revision_id: str | None, suggestion: MarkSuggestion,
                  selection: Mapping[str, Any] | None, unplaced: tuple[str, ...] = ()) -> str:
    """The identity of one shown proposal: the book, the reading and its
    revision, the units it holds out and where they were suggested from, the
    reading's own marks as they stood, and the book's unplaced marks it was
    made over (the ones the marking records it reviewed)."""

    payload = {"source_id": str(source_id), "extraction_id": str(extraction_id), "revision_id": revision_id,
               "held_out": list(suggestion.held_out), "from": list(suggestion.from_readings),
               "selection": _marks_state(selection), "unplaced": sorted(unplaced)}
    return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                                 default=str).encode()).hexdigest()


def _plan(vault: Any, repository: Any, source_id: str, title: str | None) -> tuple[
        dict[str, Any], MarkSuggestion, dict[str, Any] | None, SourceMarks] | None:
    reading = reread.reread_reading(repository, source_id)
    marks = source_marks(vault, repository).get(str(source_id)) if reading is not None else None
    if marks is None or reading not in marks.unmarked:
        return None
    suggestion = suggest_marks(vault, repository, reading)
    run = repository.get_extraction_run(reading) or {}
    revision_id = None if run.get("revision_id") is None else str(run["revision_id"])
    selection = repository.get_unit_selection(reading)
    if suggestion.labels:
        lines = [f"Held out as exam material: {_listed(suggestion.labels)}.",
                 "These are suggested from what you marked before: check them. The rest of this "
                 "reading becomes available for explanations, questions and search."]
    else:
        lines = ["Nothing in this reading matches the exam material you marked before.",
                 "Marking it makes the whole reading available for explanations, questions and search."]
    name = title or "this book"
    plan = {
        "source_id": str(source_id),
        "extraction_id": reading,
        "revision_id": revision_id,
        "held_out_unit_ids": list(suggestion.held_out),
        "proposal_hash": proposal_hash(source_id, reading, revision_id, suggestion, selection, marks.unplaced),
        "needs_confirmation": True,
        "title": f"Mark exam material on this reading of {name}?",
        "lines": lines,
        "confirm_label": "Mark it" if not suggestion.labels else "Mark them",
        "cancel_label": "Not now",
    }
    return plan, suggestion, selection, marks


def mark_plan(vault: Any, repository: Any, source_id: str, *, title: str | None = None) -> dict[str, Any] | None:
    """The card's confirmation before marking, in plain words, bound to the
    reading it names and the proposal it shows (``proposal_hash``); None when
    the book's reading is not held back."""

    planned = _plan(vault, repository, source_id, title)
    return None if planned is None else planned[0]


def mark_exam_material(vault: Any, repository: Any, source_id: str, *, extraction_id: str | None,
                       proposal_hash: str | None, title: str | None = None,
                       clock: Clock | None = None) -> dict[str, Any]:
    """The owner's confirmed marking of the reading the Reader opens, exactly
    as the confirmation they confirmed showed it (``extraction_id`` and
    ``proposal_hash`` from :func:`mark_plan`): the units held out in its own
    unit selection, the owner's mark (``PROTECTION_MARK_KEY``) and the
    reading the marks were made on (``MARKS_MADE_ON_KEY``), so
    ``exam_material`` reads it as marked exactly (rule 4).

    The marking records the book's unplaced marks the owner reviewed
    (``exam_material.REVIEWED_UNPLACED``): it covers those only, so a mark
    made or changed later holds the reading back again (Codex review of
    extraction identity, F1). The owner's verdict is appended to
    ``judgment_ledger`` (:data:`MARK_JUDGMENT_TASK`, ``judge = owner``: the
    reading, its revision, the proposal, the units held out, when) in the
    same transaction, once per proposal (F5).

    A carry-over the re-read still owes is finished first, so the study map's
    chapters reach the selection the marks are written into. Then, in one
    transaction (no other write between the check and the marking), the
    confirmation is checked against a fresh one: a different reading, a
    different proposal, nothing held back any more, or a call that names no
    confirmation raises :class:`StaleMarkConfirmation` with the fresh
    confirmation, and nothing is written."""

    if reread.carry_owed(repository, source_id) is not None:
        reread.finish_carry_over(repository, source_id, clock=clock)
    with repository.atomic():
        planned = _plan(vault, repository, source_id, title)
        if planned is None:
            raise StaleMarkConfirmation(None)
        plan, suggestion, selection, marks = planned
        if not extraction_id or not proposal_hash or plan["extraction_id"] != str(extraction_id) \
                or plan["proposal_hash"] != str(proposal_hash):
            raise StaleMarkConfirmation(plan)
        reading = plan["extraction_id"]
        stored: Mapping[str, Any] = selection or {}
        # Exactly the confirmed units are held out: a held-out mode the
        # reading carried that was not confirmed (a legacy one, shown in the
        # suggestion) gives way to the confirmation; other modes stay.
        modes = {unit_id: mode for unit_id, mode in dict(stored.get("exam_use_modes") or {}).items()
                 if mode != HELD_OUT_EVALUATION}
        for unit_id in suggestion.held_out:
            modes[unit_id] = HELD_OUT_EVALUATION
        made_on = marks_made_on(reading, plan["revision_id"])
        now = utc_now_iso(clock)
        metadata = dict(stored.get("exam_paper_metadata") or {})
        metadata[PROTECTION_MARK_KEY] = {"at": now, "from": list(suggestion.from_readings),
                                         "held_out": list(suggestion.held_out), **made_on,
                                         "proposal_hash": plan["proposal_hash"],
                                         REVIEWED_UNPLACED: list(marks.unplaced)}
        metadata[MARKS_MADE_ON_KEY] = made_on
        revision = repository.get_source_revision(str(plan["revision_id"] or "")) or {}
        repository.upsert_unit_selection(
            extraction_id=reading, source_id=revision.get("source_id") or str(source_id),
            revision_id=plan["revision_id"], selected_unit_ids=list(stored.get("selected_unit_ids") or []),
            boundary_overrides=list(stored.get("boundary_overrides") or []),
            needs_review=list(stored.get("needs_review") or []), exam_use_modes=modes,
            exam_paper_metadata=metadata, role_override=stored.get("role_override"), clock=clock,
        )
        _record_verdict(repository, str(source_id), plan, suggestion, list(marks.unplaced), now)
    return {"extraction_id": reading, "held_out_unit_ids": list(suggestion.held_out),
            "from_extraction_ids": list(suggestion.from_readings)}


def _record_verdict(repository: Any, source_id: str, plan: Mapping[str, Any], suggestion: MarkSuggestion,
                    reviewed: list[str], now: str) -> None:
    """The owner's marking as an owner verdict in ``judgment_ledger``, in the
    caller's transaction, once per confirmed proposal (Codex review of
    extraction identity, F5: every owner verdict appends to the ledger)."""

    judgment_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"learnloop:{MARK_JUDGMENT_TASK}:{plan['proposal_hash']}"))
    with repository.connection() as connection:
        if connection.execute("SELECT 1 FROM judgment_ledger WHERE id = ?", (judgment_id,)).fetchone():
            return
        append_judgment(
            connection, id=judgment_id, task=MARK_JUDGMENT_TASK, left_kind="extraction",
            left_id=str(plan["extraction_id"]), right_kind="source", right_id=source_id, judge="owner",
            input_hash=str(plan["proposal_hash"]), verdict="marked",
            rationale=json.dumps({
                "action": MARK_ACTION, "source_id": source_id, "extraction_id": plan["extraction_id"],
                "revision_id": plan["revision_id"], "proposal_hash": plan["proposal_hash"],
                "held_out_unit_ids": list(suggestion.held_out), "from_extraction_ids": list(suggestion.from_readings),
                "reviewed_unplaced": reviewed, "at": now,
            }, sort_keys=True),
            created_at=now,
        )


__all__ = [
    "AMBIGUOUS_DETAILS",
    "CHANGED_LINE",
    "FOUND_DETAILS",
    "HELD_BACK_DETAILS",
    "HELD_BACK_LINE",
    "MARK_ACTION",
    "MARK_JUDGMENT_TASK",
    "MARK_LABEL",
    "MarkSuggestion",
    "StaleMarkConfirmation",
    "held_back_details",
    "held_back_reading",
    "held_back_readings",
    "mark_exam_material",
    "mark_plan",
    "proposal_hash",
    "suggest_marks",
]
