"""``companion.history`` (spec §8.5, owner decision 2): every tutor exchange, by day and then desk, newest
first, each with where it happened and the passage it was about.

The backing data is ``question_events`` (every context), joined with ``companion_exchange_context``
(the desk, the surface and the pad blocks an exchange was asked from) and ``question_event_spans`` (its
passage). An exchange with no context row was asked before desks existed: it is shown with origin
``backfill``, no desk and the surface its own context names ("in the Reader", "while practising"), and
nothing is written for it. The query matches question and answer text by words; the search by meaning
is the companion's job (RD3). An answer withheld as worked help shows as the learner was shown it.
"""
from __future__ import annotations

import json
import re
from collections.abc import Mapping
from datetime import UTC, datetime, time, timedelta
from typing import Any

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.stores import span_projections as spans_store
from learnloop.tutor.tutor_qa import delivered_answer_md

#: A history page's exchanges (a paging size, not a cap: the cursor reaches every exchange).
PAGE_SIZE = 50
LIVE = "live"
BACKFILL = "backfill"
#: Where an exchange asked before desks happened, by its own context.
SURFACE_BY_CONTEXT = {"reader": "reader", "practice": "practice", "feedback": "feedback", "library": "library"}
WHERE = {"reader": "in the Reader", "practice": "while practising", "feedback": "on feedback", "library": "in your library",
         "lesson": "in a lesson", "desk": "on a desk"}
_SENTENCE = re.compile(r"(.+?[.!?])(\s|$)", re.S)


def record_exchange_context(repository: Any, *, question_event_id: str, surface: str, desk_id: str | None = None,
                            window_spec: Mapping[str, Any] | None = None, pad_block_ids: list[str] | None = None,
                            goal_id: str | None = None, clock: Clock | None = None) -> bool:
    """Record where one exchange was asked (origin ``live``); a second record of it is ignored.
    The companion's ask (RD3) calls this as it records the exchange."""

    with repository.connection() as connection:
        return spans_store.insert_exchange_context(connection, {
            "question_event_id": question_event_id, "desk_id": desk_id, "surface": surface,
            "window_spec": dict(window_spec) if window_spec is not None else None, "pad_block_ids": pad_block_ids,
            "goal_id": goal_id, "origin": LIVE, "created_at": utc_now_iso(clock),
        })


def _first_sentence(text: str | None) -> str:
    body = " ".join(str(text or "").split())
    if not body:
        return ""
    match = _SENTENCE.match(body)
    return match.group(1) if match else body


def _local_day(stamp: str) -> str:
    parsed = parse_utc(stamp)
    return parsed.astimezone().date().isoformat() if parsed is not None else str(stamp)[:10]


def _day_start(day: str, *, days_after: int = 0) -> str:
    """A local calendar day's first instant (or that of a day after it), in UTC, as stored stamps are."""

    date = datetime.fromisoformat(day).date() + timedelta(days=days_after)
    return datetime.combine(date, time.min).astimezone().astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _anchors(connection: Any, ids: list[str]) -> dict[str, dict[str, Any]]:
    """Each exchange's passage: its selection if it has one, else its first citation, else its context."""

    rank = {"exact_selection": 0, "citation": 1, "source_context": 2}
    best: dict[str, dict[str, Any]] = {}
    for row in spans_store.rows_for(connection, "question_event_spans", ids):
        if row["span_id"] is None:
            continue
        current = best.get(row["question_event_id"])
        if current is None or rank[row["quality"]] < rank[current["quality"]]:
            best[row["question_event_id"]] = {"extraction_id": row["extraction_id"], "span_id": row["span_id"],
                                              "quality": row["quality"]}
    return best


def companion_history(repository: Any, *, date_from: str | None = None, date_to: str | None = None,
                      desk_id: str | None = None, query: str | None = None, cursor: str | None = None) -> dict[str, Any]:
    clauses, params = [], []
    if date_from:
        clauses.append("q.created_at >= ?")
        params.append(_day_start(date_from))
    if date_to:
        clauses.append("q.created_at < ?")
        params.append(_day_start(date_to, days_after=1))
    if desk_id is not None:
        clauses.append("c.desk_id = ?")
        params.append(desk_id)
    words = (query or "").strip()
    if words:
        like = "%" + words.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        clauses.append("(q.question_md LIKE ? ESCAPE '\\' OR q.answer_md LIKE ? ESCAPE '\\')")
        params.extend([like, like])
    if cursor:
        stamp, _, last = cursor.partition("|")
        clauses.append("(q.created_at < ? OR (q.created_at = ? AND q.id < ?))")
        params.extend([stamp, stamp, last])
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = ("SELECT q.id, q.context, q.question_md, q.answer_md, q.answer_status, q.source_context_json, q.created_at "
           "FROM question_events AS q LEFT JOIN companion_exchange_context AS c ON c.question_event_id = q.id "
           f"{where} ORDER BY q.created_at DESC, q.id DESC LIMIT ?")
    with repository.connection() as connection:
        cursor_rows = connection.execute(sql, [*params, PAGE_SIZE + 1])
        names = [column[0] for column in cursor_rows.description]
        rows = [dict(zip(names, row, strict=True)) for row in cursor_rows.fetchall()]
        page = rows[:PAGE_SIZE]
        ids = [str(row["id"]) for row in page]
        contexts = spans_store.exchange_contexts(connection, ids)
        anchors = _anchors(connection, ids)
    days: list[dict[str, Any]] = []
    for row in page:
        try:
            source_context = json.loads(row.get("source_context_json") or "null") or {}
        except (TypeError, ValueError):
            source_context = {}
        context = contexts.get(str(row["id"]))
        surface = context["surface"] if context else SURFACE_BY_CONTEXT.get(str(row["context"]), str(row["context"]))
        exchange = {
            "question_event_id": row["id"],
            "question_md": row["question_md"],
            "answer_first_sentence": _first_sentence(delivered_answer_md({**row, "source_context": source_context})),
            "answer_status": row["answer_status"],
            "context": row["context"],
            "surface": surface,
            "where": WHERE.get(surface, surface),
            "origin": context["origin"] if context else BACKFILL,
            "goal_id": context["goal_id"] if context else None,
            "pad_block_ids": (context or {}).get("pad_block_ids") or [],
            "anchor": anchors.get(str(row["id"])),
            "created_at": row["created_at"],
        }
        day = _local_day(str(row["created_at"]))
        exchange_desk = context["desk_id"] if context else None
        if not days or days[-1]["date"] != day:
            days.append({"date": day, "desks": []})
        desks = days[-1]["desks"]
        group = next((entry for entry in desks if entry["desk_id"] == exchange_desk), None)
        if group is None:
            group = {"desk_id": exchange_desk, "exchanges": []}
            desks.append(group)
        group["exchanges"].append(exchange)
    next_cursor = f"{page[-1]['created_at']}|{page[-1]['id']}" if len(rows) > PAGE_SIZE else None
    return {"days": days, "cursor": next_cursor}


__all__ = ["BACKFILL", "LIVE", "PAGE_SIZE", "companion_history", "record_exchange_context"]
