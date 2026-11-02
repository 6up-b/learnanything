"""Curriculum C4: the learner's linked notes in a lesson (spec_deliverable_curriculum_v1 §8.2, §10.2, §10.4).

The teacher is the one model reader of note text the spec names besides the note link judge
(``read_note``); the brief lists the notes' headers (``your_notes``). Both read C2's stored snapshots
of linked notes (never a tend call during a lesson), both only while ``teacher.brief.use_deliverable``
and ``notes.enabled`` are on and tend is present, and both label the text as the learner's own voice.

This module is the teacher package's only door to the notes' code: the service injects
:func:`your_notes` into the brief and the read action calls :func:`read_note`, so the brief, the
check minting (``teacher.checks``), the guards and the delayed checks never reach it (a note is never
a generation input), and nothing graded ever sees a note (the blind grader reads the answer only).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from learnloop.teacher.brief import STEM_CHARS, c4_active


def your_notes(vault: Any, repository: Any, learning_object_ids: Sequence[str]) -> dict[str, list[dict[str, Any]]]:
    """Per LO, headers of the learner's linked notes (title, heading, date, one line): their own voice (C4)."""

    try:
        from learnloop.db.stores import learner_notes as notes_store
        from learnloop.source_retrieval import note_links as NL

        if not NL.enabled(vault) or not NL.available(vault):
            return {}
        with repository.connection() as connection:
            rows = notes_store.links(connection, learning_object_ids=set(learning_object_ids))
        out: dict[str, list[dict[str, Any]]] = {}
        for view in NL.effective(repository, rows):
            lo = str(view.get("learning_object_id") or "")
            if lo not in set(learning_object_ids):
                continue
            note = view["note"]
            first = next((line.strip() for line in str(note.get("text") or "").splitlines() if line.strip()), "")
            out.setdefault(lo, []).append({
                "id": f"n:{view['link_id']}", "title": note.get("title"), "heading": note.get("heading"),
                "date": note.get("date_label"), "line": first[:STEM_CHARS],
                "voice": "the learner's own note (what they think; not a source)"})
        return out
    except Exception:  # noqa: BLE001 - notes that can't be read are left out
        return {}


def read_note(vault: Any, repository: Any, state: Any, refs: list[str]) -> dict[str, Any]:
    from learnloop.teacher.brief import c4_active

    if not c4_active(vault):
        return {"refused": "notes_off", "message": "the learner's notes are not part of this lesson"}
    try:
        from learnloop.db.stores import learner_notes as notes_store
        from learnloop.source_retrieval import note_links as NL

        if not NL.enabled(vault) or not NL.available(vault):
            return {"refused": "notes_off", "message": "the learner's notes are not available"}
    except Exception:  # noqa: BLE001
        return {"refused": "notes_off", "message": "the learner's notes are not available"}
    allowed: dict[str, str] = {}
    for node in state.brief.get("nodes") or []:
        for note in node.get("your_notes") or []:
            allowed[note["id"]] = node["id"]
    out = []
    with repository.connection() as connection:
        rows = notes_store.links(connection, learning_object_ids=set(allowed.values()))
    views = {f"n:{view['link_id']}": view for view in NL.effective(repository, rows)}
    for ref in refs:
        view = views.get(ref)
        if ref not in allowed or view is None:
            out.append({"id": ref, "refused": "not one of the notes in the brief"})
            continue
        note = view["note"]
        out.append({"id": ref, "voice": "the learner's own note: what they think, not a source of truth",
                    "title": note.get("title"), "heading": note.get("heading"), "date": note.get("date_label"),
                    "text": note.get("text"), "truncated": note.get("truncated")})
    return {"notes": out}


__all__ = ["read_note", "your_notes"]
