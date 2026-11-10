"""Curriculum C4: the learner's linked notes in a lesson (spec_deliverable_curriculum_v1 §8.2, §10.2, §10.4).

The teacher reads note text through ``read_note``; the brief lists the notes' headers (``your_notes``).
Since curriculum C2b the notes are the vault's own (the learner's Reader notes and highlights with text,
and their capture-inbox items): both read the stored snapshots of linked notes through
``note_links.effective`` (which withholds a snapshot whose anchor now sits beside protected material),
both only while ``teacher.brief.use_deliverable`` and ``notes.enabled`` are on, and both label the
text as the learner's own voice. Note text is learner text (owner, 2026-11-01), so the teacher may read
it when it helps; it is never a source, a generation input or evidence.

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
        for view in NL.effective(repository, rows, vault=vault):
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
    views = {f"n:{view['link_id']}": view for view in NL.effective(repository, rows, vault=vault)}
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


def notes_still_deliverable(vault: Any, repository: Any, note_refs: Sequence[str]) -> bool:
    """Whether every note a lesson was given (``n:<link id>``: a ``your_notes`` header or a ``read_note``
    text) could still be given now, so an earlier lesson's recap may carry what it took from them
    (followups batch 5, Codex review F2; :func:`learnloop.teacher.brief.recap_admissible` calls it by
    injection). The note is the delivered link row's (append-only, so a later hide or re-link cannot
    drop the dependency), judged by C2b's predicate on every anchor its annotation ever had
    (``vault_notes.snapshot_protected_keys``, the one that withholds the note itself). Fail closed: a
    ref that names no link row, a Reader note with no anchor history (its source cannot be told), or
    notes that cannot be read. A capture holds no book text and stays."""

    refs = {str(ref) for ref in note_refs}
    if not refs:
        return True
    if any(not ref.startswith("n:") or len(ref) <= 2 for ref in refs):
        return False
    try:
        from learnloop.db.stores import learner_notes as notes_store
        from learnloop.source_retrieval import vault_notes as VN

        link_ids = {ref[2:] for ref in refs}
        with repository.connection() as connection:
            rows = notes_store.links_by_id(connection, link_ids)
        if set(rows) != link_ids:
            return False
        keys = {str(row["note_key"]) for row in rows.values()}
        for key in keys:
            ref = VN.split_key(key)
            if ref is not None and ref[0] == VN.KIND_ANNOTATION and not VN.anchor_sources(repository, key):
                return False
        return not VN.snapshot_protected_keys(vault, repository, keys)
    except Exception:  # noqa: BLE001 - notes that can't be judged leave the recap out
        return False


__all__ = ["notes_still_deliverable", "read_note", "your_notes"]
