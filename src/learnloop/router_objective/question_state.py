"""RO0 rows 1, 2 and 3 at an ask: the state a question was asked in, computed before the model call.

Row 1 (``question_events.reveal_state_json``): the reveal sum on the item, whether an answer or a worked solution
has ever been disclosed, the hint level reached, the attempt state. **Ever disclosed** is what the server knows;
**visible now** is what only the screen knows, so it is client-sent or ``unknown`` and never inferred from the first.

Row 2: ``hints_used_before``, ``scaffold_level``, ``preceding_tutor_move`` and ``learner_mode``, computed from
``help_assists`` where the server can, and sent by clients where only they know. A client's value stands. One offline
reader: the probability arms' card reads ``hints_used_before`` (``field.probability_states.STATE_VERSION``).

Row 3 (``question_events.question_opportunity``): what the question was asked from.

Ids, kinds and numbers only. Never fails the question: what cannot be read stays unwritten, with a warning.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
import logging
from typing import Any

from learnloop.db.stores import router_objective as store

logger = logging.getLogger(__name__)

STATE_VERSION = "reveal_state_v1"
#: The client's and the server's fields of row 2 and row 3: off, none is written (nothing sent them before RO0).
PROCESS_FIELDS: tuple[str, ...] = (
    "hints_used_before", "scaffold_level", "preceding_tutor_move", "learner_mode", "question_opportunity",
)
VISIBLE = "visible"
NOT_VISIBLE = "not_visible"
UNKNOWN = "unknown"
#: A help row at this level or above is worked help (level 4 or 5: ``hints.writer``, the fold's ``primed``).
_WORKED_LEVEL = 4
_ANSWER_KINDS = frozenset({"answer_display"})
_WORKED_KINDS = frozenset({"guided_redo", "repair_display"})


def _dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _visible_now(client: Any) -> str:
    if client is True:
        return VISIBLE
    if client is False:
        return NOT_VISIBLE
    return UNKNOWN


def _attempt_state(context: str, attempt_id: str | None, attempt_progress: Any, *, has_item: bool) -> str:
    if not has_item:
        return "no_item"
    if attempt_id is not None or context == "feedback":
        return "submitted"
    if context == "practice":
        return {"draft_started": "draft_started", "no_draft": "no_draft"}.get(str(attempt_progress), "open")
    return "not_in_an_attempt"


def _assists(connection: Any, practice_item_id: str) -> list[dict[str, Any]]:
    if not store.table_present(connection, "help_assists"):
        return []
    return [dict(row) for row in connection.execute(
        "SELECT assist_kind, hint_kind, level, authored_index, attempt_id, practice_session_id, shown_at, requested_at "
        "FROM help_assists WHERE practice_item_id = ? AND shown = 1 ORDER BY COALESCE(shown_at, requested_at)",
        (practice_item_id,))]


def _reveals(connection: Any, practice_item_id: str) -> dict[str, tuple[int, float]]:
    if not store.table_present(connection, "reveal_events"):
        return {}
    return {str(row[0]): (int(row[1]), float(row[2] or 0.0)) for row in connection.execute(
        "SELECT source_kind, COUNT(*), SUM(amount) FROM reveal_events WHERE practice_item_id = ? GROUP BY source_kind",
        (practice_item_id,))}


def _hints_before(assists: list[dict[str, Any]], session_id: str | None) -> int:
    """Hints shown on this item not yet attached to an attempt, in this session (the attempt's own window)."""

    authored: set[Any] = set()
    served = 0
    for row in assists:
        if row["assist_kind"] != "hint" or row["attempt_id"] is not None:
            continue
        if session_id is not None and row["practice_session_id"] not in (session_id, None):
            continue
        if row["hint_kind"] == "authored":
            authored.add(row["authored_index"])
        else:
            served += 1
    return served + len(authored)


def _preceding_move(connection: Any, assists: list[dict[str, Any]], *, context: str, practice_item_id: str | None,
                    session_id: str | None) -> str:
    """The tutor's last move before this question: a hint's kind, an answer, or ``none``."""

    last_help = max((str(row["shown_at"] or row["requested_at"] or "") for row in assists), default="")
    question = connection.execute(
        "SELECT MAX(created_at) FROM question_events WHERE practice_item_id = ? AND COALESCE(session_id, '') = COALESCE(?, '') "
        "AND answer_status = 'answered'", (practice_item_id, session_id)).fetchone()
    last_answer = str(question[0] or "") if question is not None else ""
    if not last_help and not last_answer:
        return "none"
    if last_answer >= last_help:
        return "tutor_answer"
    row = assists[-1]
    return f"{row['assist_kind']}:{row['hint_kind']}" if row.get("hint_kind") else str(row["assist_kind"])


def _opportunity(connection: Any, context: str, practice_item_id: str | None, session_id: str | None) -> tuple[str, str | None]:
    """What the question was asked from, and the presentation that opened it where one did."""

    if context == "reader":
        return "reader_visit", None
    if context == "practice" and practice_item_id and session_id and store.table_present(connection, "plan_presentations"):
        row = connection.execute(
            "SELECT id FROM plan_presentations WHERE session_id = ? AND practice_item_id = ? ORDER BY served_at DESC, id DESC LIMIT 1",
            (session_id, practice_item_id)).fetchone()
        if row is not None:
            return "plan_presentation", str(row[0])
    return str(context), None


def fields_at_ask(repository: Any, *, context: str, practice_item_id: str | None, attempt_id: str | None,
                  session_id: str | None, question_context: Mapping[str, Any],
                  workbench_session_id: str | None = None) -> dict[str, Any]:
    """The columns RO0 adds or fills on one question row, on a fresh read; ``{}`` when it cannot be read."""

    try:
        with repository.connection() as connection:
            assists = _assists(connection, practice_item_id) if practice_item_id else []
            reveals = _reveals(connection, practice_item_id) if practice_item_id else {}
            hints_before = _hints_before(assists, session_id)
            levels = [int(row["level"]) for row in assists if row["level"] is not None]
            level = max(levels, default=None)
            opportunity, presentation_id = _opportunity(connection, context, practice_item_id, session_id)
            move = _preceding_move(connection, assists, context=context, practice_item_id=practice_item_id,
                                   session_id=session_id) if practice_item_id else None
    except Exception:  # noqa: BLE001 - a receipt never blocks an answer
        logger.warning("router objective: the state at this ask was not read", exc_info=True)
        return {}
    has_item = practice_item_id is not None
    state = {
        "version": STATE_VERSION,
        "reveal_sum": round(sum(amount for _count, amount in reveals.values()), 6) if has_item else None,
        "reveal_kinds": {kind: count for kind, (count, _amount) in sorted(reveals.items())},
        "answer_disclosed_ever": bool(_ANSWER_KINDS & set(reveals)) if has_item else None,
        "worked_solution_disclosed_ever": (bool(_WORKED_KINDS & set(reveals)) or (level or 0) >= _WORKED_LEVEL)
        if has_item else None,
        "hint_level_reached": level,
        "attempt_state": _attempt_state(context, attempt_id, question_context.get("attempt_progress"), has_item=has_item),
        "visible_now": _visible_now(question_context.get("answer_visible_now")),
        **({"presentation_id": presentation_id} if presentation_id else {}),
    }
    filled: dict[str, Any] = {"reveal_state_json": _dumps(state)}
    computed = {
        "hints_used_before": hints_before if has_item else None,
        "scaffold_level": (str(level) if level is not None else "none") if has_item else None,
        "preceding_tutor_move": move,
        "learner_mode": "work_in_steps" if workbench_session_id else None,
        "question_opportunity": opportunity,
    }
    for name, value in computed.items():
        client = question_context.get(name)
        filled[name] = client if client is not None else value
    return filled


__all__ = ["NOT_VISIBLE", "PROCESS_FIELDS", "STATE_VERSION", "UNKNOWN", "VISIBLE", "fields_at_ask"]
