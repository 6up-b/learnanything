"""Deliverable curriculum C5: notes as learner text (spec_deliverable_curriculum_v1 §10.2,
§10.4, §12 C5).

With the learner's opt-in (``notes.gaps_enabled``, default off: owner Q9), a note the
learner LINKED is also a learner-text-gaps input (``source_kind = 'learner_note'``),
tier 2 only: it steers hypotheses and suggestions, never mastery, evidence or grading.

**Which notes.** Exactly the links C2 shows (:func:`note_links.effective_rows`, the one
rule): a model's proposal of a topic's current candidate state the learner did not hide,
and a link the learner made by hand. A hidden link, an unlinked note, a proposal of a
superseded state and a note's older snapshot never feed gaps. The gap's source is the
linked SNAPSHOT (``learner_notes.id``), so the note is read with the text it is linked
with now, and a changed note (a new snapshot) is a new reading.

**Keyed to what it is linked to.** Its topics: the LOs its proposals were judged for and
the LOs the passages it was linked to by hand are provenance-linked to. Its context: the
topics' titles and statements and the linked sections' first blocks, read through C0a's
protection (:func:`section_coverage.peek`). A note linked to a passage that is protected
material, or a Reader note written beside protected material (C2b), is not read at all
(:class:`NoteWithheld`): no exam-material text, and no note
written beside it, reaches the gap model.

**Learner text like any other** (C2b, owner 2026-11-01): a note's reading takes the
learner-text-gaps pipeline's ordinary transport (its reader and judge routes, the Decider,
the embedding shortlist); never written to, never a source, never a generation input. This
module is the gap pipeline's one way to the notes (the declared exception in the
``notes-are-never-a-source-or-evidence`` import contract); it only reads.

Off (``notes.gaps_enabled``, ``notes.enabled``, or ``learner_text_gaps.enabled`` off):
:func:`enabled` is false and nothing here reads a note row.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.db.stores import learner_notes as store
from learnloop.source_retrieval import note_links as NL
from learnloop.source_retrieval import section_coverage as SC
from learnloop.source_retrieval import vault_notes as VN

SOURCE_KIND = "learner_note"
#: Structural bounds (what fits a prompt; none is a weight, margin or threshold).
#: A topic's statement as the gap reader is shown it.
STATEMENT_CHARS = NL.STATEMENT_CHARS
#: A linked section's first blocks as the gap reader is shown them.
LEAD_CHARS = NL.LEAD_CHARS


class NoteWithheld(Exception):
    """The note is linked to protected material (an exam unit, a held-back reading): it
    is not read for gaps."""


def enabled(vault: Any) -> bool:
    """The opt-in, the notes and the gap pipeline all on. False: the gaps code reads no
    note row."""

    notes = getattr(vault.config, "notes", None)
    gaps = getattr(vault.config, "learner_text_gaps", None)
    if not (notes is not None and bool(getattr(notes, "gaps_enabled", False))
            and gaps is not None and bool(getattr(gaps, "enabled", False))):
        return False
    return NL.available(vault)


@dataclass(frozen=True)
class LinkedNote:
    """One linked note's current snapshot and everything it is linked to now."""

    note_id: str
    note_key: str
    learning_object_ids: tuple[str, ...]
    #: (extraction, section, span) of each linked passage (a proposal's anchor, or the
    #: passage the learner linked it to by hand).
    passages: tuple[tuple[str, str | None, str | None], ...]
    note: Mapping[str, Any]


def linked_notes(vault: Any, repository: Repository) -> list[LinkedNote]:
    """Every note linked now, by the snapshot its links show, oldest link first. Only with
    :func:`enabled`; empty otherwise (no note row is read)."""

    if not enabled(vault):
        return []
    with repository.connection() as connection:
        if not store.tables_present(connection):
            return []
        rows = store.links(connection)
    by_snapshot: dict[str, dict[str, Any]] = {}
    for row, note in NL.effective_rows(repository, rows):
        entry = by_snapshot.setdefault(str(note["id"]), {"note": note, "los": [], "passages": []})
        lo = row.get("learning_object_id")
        if lo and str(lo) not in entry["los"]:
            entry["los"].append(str(lo))
        if row.get("extraction_id"):
            passage = (str(row["extraction_id"]), row.get("section_id"), row.get("span_id"))
            if passage not in entry["passages"]:
                entry["passages"].append(passage)
    return [LinkedNote(note_id=note_id, note_key=str(entry["note"]["note_key"]),
                       learning_object_ids=tuple(entry["los"]), passages=tuple(entry["passages"]),
                       note=entry["note"]) for note_id, entry in by_snapshot.items()]


def linked_note_ids(vault: Any, repository: Repository) -> list[str]:
    """The snapshots the gap queue may read now (:func:`linked_notes`)."""

    return [linked.note_id for linked in linked_notes(vault, repository)]


def _one_line(text: Any, limit: int) -> str:
    return " ".join(str(text or "").split())[:limit]


def _section_lead(vault: Any, repository: Repository, library: SC.Library, passage: tuple[str, str | None, str | None],
                  ) -> dict[str, Any] | None:
    """A linked passage's section, its title and first blocks, protection read now.
    Raises :class:`NoteWithheld` for protected material; None when it is not readable."""

    extraction_id, section_id, span_id = passage
    if span_id and library.protection.span_out(extraction_id, span_id):
        raise NoteWithheld("linked to protected material")
    if not section_id:
        try:
            reading = library.reading(extraction_id)
        except SC.CoverageError:
            return None
        section_id = (reading.span_section.get(span_id) or reading.all_spans.get(span_id)) if reading and span_id else None
    if not section_id:
        return None
    try:
        peeked = SC.peek(vault, repository, extraction_id, str(section_id))
    except SC.CoverageError as exc:
        if getattr(exc, "code", "") == "withheld":
            raise NoteWithheld("linked to protected material") from exc
        return None
    text = " ".join(" ".join(str(block.get("text") or "").split()) for block in peeked.get("blocks") or ())
    return {"book": str(peeked.get("source_title") or ""), "section": str(peeked.get("title") or ""),
            "lead": _one_line(text, LEAD_CHARS)}


def note_text(vault: Any, repository: Repository, note_id: str) -> dict[str, Any] | None:
    """What the gap pipeline reads for one linked snapshot, or None: switched off, the
    note is no longer linked (hidden, unlinked, or a newer snapshot shows), or it is gone.

    Returns the note's text, its topics (linked LOs, then the LOs provenance-linked to its
    hand-linked passages), the subject they share (if one) and the reader's context.
    Raises :class:`NoteWithheld` when it is linked to protected material."""

    from learnloop.reader.reader_progression import learning_objects_for_span

    linked = next((entry for entry in linked_notes(vault, repository) if entry.note_id == str(note_id)), None)
    if linked is None:
        return None
    if linked.note.get("origin") == VN.ORIGIN and VN.beside_protected(vault, repository, linked.note_key):
        # C2b: a Reader note written beside material protected since it was linked is not read.
        raise NoteWithheld("written beside protected material")
    los = [lo for lo in linked.learning_object_ids if lo in vault.learning_objects]
    library = SC.Library(vault, repository)
    passages: list[dict[str, Any]] = []
    for passage in linked.passages:
        extraction_id, _section_id, span_id = passage
        lead = _section_lead(vault, repository, library, passage)
        if lead is not None and lead not in passages:
            passages.append(lead)
        if span_id:
            for lo in learning_objects_for_span(vault, repository, extraction_id=extraction_id, span_id=str(span_id)):
                if lo in vault.learning_objects and lo not in los:
                    los.append(lo)
    subjects = {subject for lo in los for subject in vault.learning_objects[lo].subjects[:1]}
    note = linked.note
    context: dict[str, Any] = {
        "surface": "learner_note",
        "note": {"title": str(note.get("title") or ""), "heading": str(note.get("heading") or ""),
                 "written": str(note.get("captured_on") or "")},
        "learning_objects": [
            {"title": vault.learning_objects[lo].title,
             "statement": _one_line(getattr(vault.learning_objects[lo], "summary", "") or "", STATEMENT_CHARS)}
            for lo in los],
    }
    if note.get("origin") == "pocket_notes":
        context["note"]["handwritten"] = "a handwritten page, transcribed (it may carry transcription slips)"
    if passages:
        context["passages"] = passages
    return {
        "source_id": linked.note_id,
        "text": str(note.get("text_md") or ""),
        "created_at": str(note.get("created_at") or ""),
        "learning_object_ids": tuple(los),
        "subject_id": next(iter(subjects)) if len(subjects) == 1 else None,
        "context": context,
        # What the text and context were built from (never sent): the request gate
        # revalidates exactly these (Codex re-review F3).
        "passage_refs": tuple(linked.passages),
    }


def payload(*, text: str, learning_object_ids: Sequence[str], subject_id: str | None,
            context: Mapping[str, Any]) -> str:
    """What a note's reading sends (its text, topics, subject and context), in one
    canonical form: the request gate compares the prepared request's with what the
    note's links build now (Codex re-review F3)."""

    return json.dumps({"text": str(text), "learning_object_ids": [str(lo) for lo in learning_object_ids],
                       "subject_id": subject_id, "context": context}, sort_keys=True, default=str)


#: The gate's reasons (shown on the skipped job; no note text in them).
OFF = "your notes, or reading them for gaps, are switched off"
PROTECTED = "the note is linked to protected material"
UNLINKED = "the note is no longer linked (hidden, unlinked or changed)"
CHANGED = ("what the note is linked to changed after its reading was prepared (the next sweep prepares it "
           "again from its links as they are then)")


def refusal(vault: Any, repository: Repository, note_id: str, *, prepared: str | None = None,
            passages: Sequence[tuple[str, str | None, str | None]] = ()) -> str | None:
    """Why the snapshot ``note_id`` may not be read for gaps now, or None when it may
    (Codex review F3: the note reading's request gate asks before every request and
    before the gap row is written). Read from ``vault`` as configured now: switched
    off, no longer linked (hidden, unlinked, superseded), or linked to protected material.

    Bound to the prepared request (Codex re-review F3): ``passages`` are the passages
    it was built from (``LearnerText.bound_passages``), each revalidated against the
    protection read now even when its link is gone; ``prepared`` is its
    :func:`payload`, which must still be what the note's links build now (a link
    removed, a topic added, an opening changed: the prepared request is stale and is
    not sent)."""

    if not enabled(vault):
        return OFF
    try:
        found = note_text(vault, repository, note_id)
        library = SC.Library(vault, repository)
        for passage in passages:
            _section_lead(vault, repository, library, tuple(passage))
    except NoteWithheld:
        return PROTECTED
    if found is None:
        return UNLINKED
    if prepared is not None and payload(text=found["text"], learning_object_ids=found["learning_object_ids"],
                                        subject_id=found["subject_id"], context=found["context"]) != prepared:
        return CHANGED
    return None


__all__ = [
    "LinkedNote",
    "NoteWithheld",
    "SOURCE_KIND",
    "enabled",
    "linked_note_ids",
    "linked_notes",
    "note_text",
    "payload",
    "refusal",
]
