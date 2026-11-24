"""Reader workbench RD9a (spec §11.1, §12.5): what a lesson window's tab and the path view's Teacher lesson row say
about a lesson, read from what the lesson recorded. No model call and no write.

A tab reads "Teacher lesson · <topic>" and "made <date> from your <what>"; ``made_from`` names the <what> from the
lesson's own record: a Reader selection, a diagnostic check (the open turn names its episode), a typed question
(the goal's ``typed`` block), Today's suggestion (origin ``router``), or a topic the learner picked.
"""
from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any, Literal

from learnloop.db.stores import lessons as store

MadeFrom = Literal["selection", "check", "question", "suggestion", "topic"]


def made_from(lesson: dict[str, Any], open_refs: dict[str, Any]) -> MadeFrom:
    """Where a lesson came from, in the order a later fact outranks an earlier one: a suggestion's Start is the
    router's whatever its entry, a check's hand-off names its episode, and a typed goal is stored with entry
    ``learning_object`` (its goal JSON keeps the ``typed`` block)."""

    if lesson.get("origin") == "router":
        return "suggestion"
    if open_refs.get("probe_episode"):
        return "check"
    if (lesson.get("goal") or {}).get("typed"):
        return "question"
    if lesson.get("entry") == "reader_selection":
        return "selection"
    return "topic"


def lesson_summaries(vault: Any, repository: Any, *, lesson_ids: Sequence[str] | None = None,
                     learning_object_ids: Sequence[str] | None = None) -> list[dict[str, Any]]:
    """The lessons named (``lesson_ids``), or those on any of ``learning_object_ids``, or every lesson; newest first.
    A lesson whose LO left the vault keeps its stored goal text as its title."""

    wanted_ids = set(lesson_ids) if lesson_ids is not None else None
    wanted_los = set(learning_object_ids) if learning_object_ids is not None else None
    with repository.connection() as connection:
        rows = connection.execute("SELECT id FROM lessons ORDER BY opened_at DESC, id DESC").fetchall()
        lessons = []
        for (lesson_id,) in rows:
            if wanted_ids is not None and str(lesson_id) not in wanted_ids:
                continue
            lesson = store.lesson(connection, str(lesson_id))
            if lesson is None:
                continue
            if wanted_los is not None and not wanted_los.intersection(lesson.get("learning_object_ids") or []):
                continue
            opened = connection.execute("SELECT refs_json FROM lesson_turns WHERE lesson_id = ? AND action = 'open' "
                                        "ORDER BY seq LIMIT 1", (str(lesson_id),)).fetchone()
            refs = json.loads(opened[0] or "{}") if opened else {}
            lessons.append((lesson, refs if isinstance(refs, dict) else {}))
    out = []
    for lesson, refs in lessons:
        los = list(lesson.get("learning_object_ids") or [])
        titles = [vault.learning_objects[lo].title for lo in los if lo in vault.learning_objects]
        out.append({
            "lesson_id": str(lesson["id"]),
            "title": ", ".join(titles) or str(lesson.get("goal_text") or ""),
            "goal": lesson.get("goal_text"),
            "opened_at": lesson.get("opened_at"),
            "closed": lesson.get("closed_at") is not None,
            "close_reason": lesson.get("close_reason"),
            "learning_object_ids": los,
            "made_from": made_from(lesson, refs),
        })
    return out


__all__ = ["MadeFrom", "lesson_summaries", "made_from"]
