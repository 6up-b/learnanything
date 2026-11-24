"""Carried questions (spec §10.12): a question the learner carries, beside a passage or not, until it bears fruit or
they let it go.

* **Carry** (the verb, a "? carry" chip on a block ending in "?", or the desk drain's carry): one row, idempotent by
  the client-minted ``carried_id`` (the same request again finds it; another request under the same id is refused).
* **Labels**: "fruitful", "not now" and "let it go", three different labels, each an event; the row's ``state`` is
  the latest and ``version`` counts them, so a label names the version it expects and a stale one is a conflict.
  ``carried`` and ``not_now`` are still carried (the shelf and the margin show them); ``fruitful`` and ``let_go``
  are not.
* **Surfaced** and **ignored**: logged when a client shows a carried question beside a passage and when the learner
  passes it by, never a nudge and never a state change.

Workflow data and labels: nothing here is evidence, and no router or Teacher reads a carried question yet (its
use as a learner pick is an open design question, recorded in the stage's review).
"""
from __future__ import annotations

from typing import Any

from learnloop.clock import utc_now_iso
from learnloop.db.stores import pad_ledgers as store
from learnloop.db.stores import pad_reads as reads
from learnloop.ids import new_ulid

ORIGINS = ("block", "selection", "note", "drain", "typed")
LABELS = ("fruitful", "not_now", "let_go")
OPEN_STATES = ("carried", "not_now")
CLOSED_STATES = ("fruitful", "let_go")
#: Events that change nothing but are logged (a carried question shown beside a passage; passed by).
NOTICES = ("surfaced", "ignored")
PAGE_SIZE = 50
#: Display, not a cap (spec §10.12): the shelf shows at most this many carried questions, labelled; the rest are in
#: the library. An attention limit from the spec, returned so every client applies the same one.
SHELF_LIMIT = 3


class CarriedRefused(Exception):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code, self.message, self.details = code, message, details or {}


def _out(row: dict[str, Any]) -> dict[str, Any]:
    return {"carried_id": row["carried_id"], "text": row["text"], "origin_kind": row["origin_kind"],
            "origin_ref": row["origin_ref"], "anchor": row["anchor"], "desk_id": row["desk_id"], "since": row["since"],
            "state": row["state"], "carried": row["state"] in OPEN_STATES, "version": int(row["version"]),
            "updated_at": row["updated_at"]}


def check_question(text: str, anchor: dict[str, Any] | None) -> str:
    """The question's words, or its own refusal (``empty_question``, ``bad_anchor``): checked before anything else
    about it (a caller's protection check comes after these, so they keep their codes)."""

    words = " ".join(str(text or "").split())
    if not words:
        raise CarriedRefused("empty_question", "Write a question before saving it for later.")
    if anchor is not None and not (anchor.get("extraction_id") and anchor.get("span_id")):
        raise CarriedRefused("bad_anchor", "Select the passage again before saving this question for later.")
    return words


def carry(repository: Any, *, carried_id: str, text: str, origin_kind: str, origin_ref: str | None,
          anchor: dict[str, Any] | None, desk_id: str | None, clock: Any = None) -> dict[str, Any]:
    """Carry one question; returns it (``created`` false on a retry)."""

    words = check_question(text, anchor)
    with repository.atomic():
        connection = repository.connection()
        existing = reads.carried(connection, carried_id)
        if existing is not None:
            same = (existing["text"], existing["origin_kind"], existing["origin_ref"], existing["anchor"],
                    existing["desk_id"]) == (words, origin_kind, origin_ref, anchor, desk_id)
            if not same:
                raise CarriedRefused("carried_id_reused", "Couldn’t save this question for later. Reopen the pad or passage and try again.")
            return {**_out(existing), "created": False}
        now = utc_now_iso(clock)
        store.insert_carried(connection, {"carried_id": carried_id, "text": words, "origin_kind": origin_kind,
                                          "origin_ref": origin_ref, "anchor": anchor, "desk_id": desk_id,
                                          "since": now})
        store.insert_carried_event(connection, event_id=new_ulid(), carried_id=carried_id, event="carried",
                                   ref=origin_ref, at=now)
        return {**_out(reads.carried(connection, carried_id) or {}), "created": True}


def mark(repository: Any, *, event_id: str, carried_id: str, event: str, expected_version: int | None,
         ref: str | None, clock: Any = None) -> dict[str, Any]:
    """A label (``fruitful``, ``not_now``, ``let_go``: needs ``expected_version``) or a notice (``surfaced``,
    ``ignored``: changes nothing). Idempotent by ``event_id``. Returns the question as it stands, with ``conflict``
    when a label's expected version was stale (nothing is written then)."""

    with repository.atomic():
        connection = repository.connection()
        row = reads.carried(connection, carried_id)
        if row is None:
            raise CarriedRefused("carried_not_found", "Couldn’t find this saved question. Reopen the list.")
        logged = reads.carried_event_exists(connection, event_id)
        if logged is not None:
            if (logged["carried_id"], logged["event"], logged["ref"]) != (carried_id, event, ref):
                raise CarriedRefused("event_id_reused", "Reopen saved questions and try that choice again.")
            return {**_out(row), "conflict": False, "applied": False}
        if event in LABELS:
            if expected_version is None:
                raise CarriedRefused("expected_version_required", "This saved question changed. Reopen the list and try again.")
            if int(expected_version) != int(row["version"]):
                return {**_out(row), "conflict": True, "applied": False}
        elif event not in NOTICES:
            raise CarriedRefused("unknown_event", "Couldn’t update this saved question. Reopen the list and choose an action.")
        now = utc_now_iso(clock)
        store.insert_carried_event(connection, event_id=event_id, carried_id=carried_id, event=event, ref=ref, at=now)
        if event in LABELS:
            store.set_carried_state(connection, carried_id, event, now)
        return {**_out(reads.carried(connection, carried_id) or {}), "conflict": False, "applied": True}


def listing(repository: Any, *, which: str, desk_id: str | None, cursor: str | None) -> dict[str, Any]:
    """Carried questions, longest carried first, a page at a time: ``open`` (still carried), ``closed`` or ``all``."""

    states = {"open": OPEN_STATES, "closed": CLOSED_STATES, "all": OPEN_STATES + CLOSED_STATES}[which]
    after: tuple[str, str] | None = None
    if cursor:
        since, _, last = cursor.partition("|")
        after = (since, last)
    with repository.connection() as connection:
        rows = reads.list_carried(connection, states=states, desk_id=desk_id, after=after, page_size=PAGE_SIZE + 1)
    page = rows[:PAGE_SIZE]
    return {"carried": [_out(row) for row in page], "shelf_limit": SHELF_LIMIT,
            "cursor": f"{page[-1]['since']}|{page[-1]['carried_id']}" if len(rows) > PAGE_SIZE else None}


def history(repository: Any, carried_id: str) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        return [{"event_id": row["event_id"], "event": row["event"], "ref": row["ref"], "at": row["at"]}
                for row in reads.carried_events(connection, carried_id)]


__all__ = [
    "CLOSED_STATES", "CarriedRefused", "LABELS", "NOTICES", "OPEN_STATES", "ORIGINS", "PAGE_SIZE", "SHELF_LIMIT",
    "carry", "check_question", "history", "listing", "mark",
]
