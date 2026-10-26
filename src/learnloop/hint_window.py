"""Which attempt a question counts toward: one definition of the hint window's
session rule for every reader (RW1c fix rounds 4 and 5).

A question on a practice item counts toward the NEXT attempt on that item:
after the item's previous attempt, at or before this one. Whether it counts
for that attempt's practice session depends on the question's context:

* an ordinary question (practice, feedback) counts in its own practice
  session, or for an attempt in no session;
* a question whose context is in :data:`ITEM_WINDOW_QUESTION_CONTEXTS` (a
  Reader question a workbench session binds to the item, RW1c) counts in the
  ITEM's window whatever its practice session, or none: the learner can ask
  before any session is open, or in one that ends before the next submit,
  and the help is still on the item (fix round 4, F1).

* a practice question a workbench session binds (Reader CA2: its
  ``source_context.attempt_key`` names the unfinished workbench it was asked
  from, :func:`workbench_bound`) counts in the item's window whatever its
  practice session, as a bound Reader question does: the Reader opens a
  practice session for a question asked with none open, and the workbench may
  be resumed and submitted in another one after that session ends (Codex
  re-review F13). The thread restored for the workbench matches it by the
  same key in every session, so the count and the thread agree.

Two readers apply the rule and must agree: the hint count
(``Repository.count_hint_equivalent_question_events``, through
:func:`session_clause`) and the learner field's link from a question to the
attempt it preceded (``field.signals``, through :func:`following_attempt`).
Fix round 5 (R3) made the field read the same rule rather than a copy, so a
bound Reader question is attributed to the attempt that counts it.

This module imports nothing from LearnLoop: the database layer and the
field's pure leaf modules both read it.
"""
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

#: Question contexts whose rows count in the item's window whatever their
#: practice session. A Reader question carries an item only when a workbench
#: session binds it (RW1c), and that help is on the item, not on a practice
#: session (fix round 4, F1).
ITEM_WINDOW_QUESTION_CONTEXTS: tuple[str, ...] = ("reader",)


#: :func:`workbench_bound` as SQL over ``question_events`` (Codex re-review F13).
WORKBENCH_BOUND_SQL = "json_extract(source_context_json, '$.attempt_key.workbench_session_id') IS NOT NULL"


def workbench_bound(source_context: Mapping[str, Any] | str | None) -> bool:
    """Whether a question's ``source_context`` (parsed, or its stored JSON)
    names the unfinished workbench it was asked from (Reader CA2's
    ``attempt_key.workbench_session_id``, written only by the server)."""

    if isinstance(source_context, str):
        try:
            source_context = json.loads(source_context)
        except (TypeError, ValueError):
            return False
    if not isinstance(source_context, Mapping):
        return False
    key = source_context.get("attempt_key")
    return isinstance(key, Mapping) and key.get("workbench_session_id") is not None


def counts_in_session(*, context: str | None, question_session_id: str | None,
                      attempt_session_id: str | None, bound: bool = False) -> bool:
    """Whether a question in the item's window counts for an attempt (or a
    submit) in ``attempt_session_id``: the attempt is in no session, the
    question was asked in the same one, its context counts in the item's
    window whatever the session, or a workbench binds it (``bound``,
    :func:`workbench_bound`)."""

    return (attempt_session_id is None or question_session_id == attempt_session_id
            or context in ITEM_WINDOW_QUESTION_CONTEXTS or bound)


def session_clause(session_id: str | None, *, item_window_only: bool = False) -> tuple[str, list[Any]]:
    """:func:`counts_in_session` as SQL over ``question_events``: ``(clause, parameters)``.

    ``item_window_only`` keeps only the item-window questions (a submit that
    will open its own practice session sees no other session's unbound
    practice rows)."""

    marks = ", ".join("?" for _ in ITEM_WINDOW_QUESTION_CONTEXTS)
    if item_window_only:
        return f" AND (context IN ({marks}) OR {WORKBENCH_BOUND_SQL})", list(ITEM_WINDOW_QUESTION_CONTEXTS)
    if session_id is not None:
        return (f" AND (session_id = ? OR context IN ({marks}) OR {WORKBENCH_BOUND_SQL})",
                [session_id, *ITEM_WINDOW_QUESTION_CONTEXTS])
    return "", []


def following_attempt(asked: datetime, *, context: str | None, question_session_id: str | None,
                      attempts: Sequence[tuple[datetime, str, str | None]], bound: bool = False) -> str | None:
    """The attempt a question asked at ``asked`` counts toward, or None.

    ``attempts`` are the item's ``(created, attempt_id, session_id)`` in
    time order. The next attempt at or after the question closes its window;
    it takes the question only when :func:`counts_in_session` says so (the
    window then moves past it, so a later attempt never does)."""

    following = next((attempt for attempt in attempts if attempt[0] >= asked), None)
    if following is None or not counts_in_session(context=context, question_session_id=question_session_id,
                                                  attempt_session_id=following[2], bound=bound):
        return None
    return following[1]


__all__ = [
    "ITEM_WINDOW_QUESTION_CONTEXTS",
    "WORKBENCH_BOUND_SQL",
    "counts_in_session",
    "following_attempt",
    "session_clause",
    "workbench_bound",
]
