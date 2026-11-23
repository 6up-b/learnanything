"""The learner's choices on a section for one goal (Reader workbench v2 §12.5): *read it anyway* on a
section the goal lens dims (skippable, or needed only deeper), or ``none``, clearing it.

A path line's own choices (*use this one instead*, *read it anyway*, *skip it*, *check me later*) are
``deliverable_path.override``'s, per LO, unchanged. A section that is not about any LO on the path has
no line to carry one, so its choice is a ``learner_card`` verdict in the judgment ledger (the goal
lens writes only receipts: Reader workbench v2 fence 4), as Reader CA5a keeps *not about this*: no new
table, one row per choice, the newest per (goal, section) standing, idempotent by the client's
operation id. It changes only what the lens shows (the section stays lit); nothing else reads it.
"""
from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

from learnloop.ai.execution import content_key
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores.judgments import append_judgment
from learnloop.section_map import extraction_sections

TASK = "goal_lens_section"
LEFT_KIND = "deliverable_goal"
RIGHT_KIND = "reader_section"
VERSION = "goal_lens_section_choice.v1"
CHOICES: tuple[str, ...] = ("read_anyway", "none")
_OPERATION_ID = re.compile(r"^[A-Za-z0-9_-]{8,80}$")


class ChoiceError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _ledger_id(operation_id: str) -> str:
    return f"glc_{operation_id}"


def _view(row: Mapping[str, Any], *, replayed: bool) -> dict[str, Any]:
    try:
        record = json.loads(row["rationale"] or "{}")
    except (TypeError, ValueError):
        record = {}
    extraction_id, _sep, section_id = str(row["right_id"]).partition("/")
    return {"operation_id": record.get("operation_id"), "goal_id": row["left_id"], "extraction_id": extraction_id,
            "section_id": section_id, "choice": row["verdict"], "replayed": replayed, "created_at": row["created_at"]}


def choose(repository: Repository, goal_id: str, extraction_id: str, section_id: str, choice: str, *,
           operation_id: str, clock: Clock | None = None) -> dict[str, Any]:
    """One choice on a section of a reading, for one goal. The caller checks the goal is a deliverable."""

    if choice not in CHOICES:
        raise ChoiceError("validation_error", f"unknown choice {choice!r}")
    if not _OPERATION_ID.match(operation_id or ""):
        raise ChoiceError("validation_error", "operation_id must be 8-80 letters, digits, '-' or '_'.")
    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        raise ChoiceError("extraction_not_found", f"No reading {extraction_id!r}.")
    rows, _blocks, _spans = extraction_sections(ir)
    if not any(str(row["id"]) == section_id for row in rows):
        raise ChoiceError("validation_error", "That section is not in this reading.")
    right_id = f"{extraction_id}/{section_id}"
    now = utc_now_iso(clock)
    with repository.atomic():
        connection = repository.connection()
        existing = connection.execute("SELECT * FROM judgment_ledger WHERE id = ?",
                                      (_ledger_id(operation_id),)).fetchone()
        if existing is not None:
            # The id binds the whole choice: a retry after another choice must not acknowledge this one.
            if (existing["task"], existing["left_id"], existing["right_id"], existing["verdict"]) != (
                    TASK, goal_id, right_id, choice):
                raise ChoiceError("validation_error", "That operation id was used for another choice.")
            return _view(existing, replayed=True)
        append_judgment(
            connection, id=_ledger_id(operation_id), task=TASK, left_kind=LEFT_KIND, left_id=goal_id,
            right_kind=RIGHT_KIND, right_id=right_id, judge="learner_card", verdict=choice, prompt_version=VERSION,
            input_hash=content_key({"choice": choice, "goal": goal_id, "section": right_id}),
            rationale=json.dumps({"operation_id": operation_id}, sort_keys=True), created_at=now)
        row = connection.execute("SELECT * FROM judgment_ledger WHERE id = ?", (_ledger_id(operation_id),)).fetchone()
    return _view(row, replayed=False)


def section_choices(repository: Repository, goal_id: str) -> dict[str, str]:
    """Section ref -> the learner's standing choice for this goal (a cleared one is absent)."""

    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT right_id, verdict FROM judgment_ledger WHERE task = ? AND left_kind = ? AND left_id = ? "
            "AND judge = 'learner_card' ORDER BY created_at, rowid", (TASK, LEFT_KIND, goal_id)).fetchall()
    newest = {str(right): str(verdict) for right, verdict in rows}
    return {ref: verdict for ref, verdict in newest.items() if verdict != "none"}


__all__ = ["CHOICES", "ChoiceError", "choose", "section_choices"]
