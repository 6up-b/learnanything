"""The only SQL for teacher TE1b's lesson suggestions (migration 236; spec_teacher_v1 §15.1, §18.1).

A suggestion is a ``router_decisions`` row (``decision_kind = 'lesson_suggestion'``,
written by :func:`learnloop.db.stores.router.insert_router_decision`, one per
local day by its receipt key ``lesson_suggestion:<date>``); the learner's one
response to a shown one is a ``router_suggestion_responses`` row (RAW_LEDGER,
append-only, unique per decision). Callers own the transaction.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from typing import Any

from learnloop.ids import new_ulid

RECEIPT_PREFIX = "lesson_suggestion:"

#: The learner's one response to a decision (a partial UNIQUE index: one per decision).
RESPONSE_KINDS: tuple[str, ...] = ("accepted", "chose_alternative", "declined", "ignored")
#: A reservation let go (a Start whose lesson never opened; at most one per decision, nothing deleted):
#: ``released`` (the learner's "Not now" on the pending card) or ``expired`` (it can no longer open).
RELEASE_KINDS: tuple[str, ...] = ("released", "expired")
_RESPONSE_SQL = "('accepted', 'chose_alternative', 'declined', 'ignored')"
_RELEASE_SQL = "('released', 'expired')"

RESPONSE_COLUMNS: tuple[str, ...] = (
    "id", "decision_id", "response", "candidate_ref", "learning_object_ids_json", "lesson_id", "session_id",
    "responded_at", "detail_json", "created_at",
)


def tables_present(connection: sqlite3.Connection) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='router_suggestion_responses'"
    ).fetchone() is not None


def receipt_key(day: str) -> str:
    return f"{RECEIPT_PREFIX}{day}"


def _decision(row: sqlite3.Row | Mapping[str, Any]) -> dict[str, Any]:
    out = dict(row)
    out["detail"] = json.loads(out.get("detail_json") or "{}")
    out["candidates"] = json.loads(out.get("candidates_json") or "[]")
    out["day"] = str(out.get("receipt_key") or "")[len(RECEIPT_PREFIX):]
    return out


def decision_for_day(connection: sqlite3.Connection, day: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM router_decisions WHERE receipt_key = ? AND decision_kind = 'lesson_suggestion'",
        (receipt_key(day),),
    ).fetchone()
    return _decision(row) if row is not None else None


def decision(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM router_decisions WHERE id = ? AND decision_kind = 'lesson_suggestion'", (decision_id,)
    ).fetchone()
    return _decision(row) if row is not None else None


def decisions(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Every lesson-suggestion decision, oldest first."""

    return [_decision(row) for row in connection.execute(
        "SELECT * FROM router_decisions WHERE decision_kind = 'lesson_suggestion' ORDER BY created_at, id")]


#: Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): a lesson offer drawn at a plan block boundary is a ``plan_block``
#: decision whose chosen ref names it (``daily_plan.types.LESSON_OFFER_PREFIX``); its card is on the row's detail.
#: Instruct hand-off IH2 (spec_instruct_handoff_v1 §5 item 3): one drawn after a miss is a ``plan_interrupt`` decision
#: read the same way, with its own block (``offer_block_id``: the row's ``block_id`` is the block the miss came from).
OFFER_REF_PREFIX = "lesson_offer:"
OFFER_DECISION_KINDS = "('plan_block', 'plan_interrupt')"


def _offer_decision(row: sqlite3.Row | Mapping[str, Any]) -> dict[str, Any]:
    """A drawn lesson offer in the shape of a shown TE1b decision (its context, its card, its day), so the
    acceptance model, the decline recovery, the ceiling and a pending Start read both alike."""

    out = dict(row)
    detail = json.loads(out.get("detail_json") or "{}")
    offer = detail.get("lesson_offer") or {}
    out["detail"] = {"shown": True, "plan_offer": True, "context": dict(offer.get("context") or {}),
                     "card": {"candidates": list((offer.get("card") or {}).get("candidates") or [])},
                     "block_id": detail.get("offer_block_id") or detail.get("block_id"), "plan_id": detail.get("plan_id"),
                     "version": offer.get("version")}
    out["candidates"] = json.loads(out.get("candidates_json") or "[]")
    out["day"] = str(detail.get("local_date") or "")
    return out


def offer_decisions(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Every drawn lesson offer (a ``plan_block`` or, from IH2, ``plan_interrupt`` decision naming one), oldest first;
    none below TE3b's tag."""

    return [_offer_decision(row) for row in connection.execute(
        f"SELECT * FROM router_decisions WHERE decision_kind IN {OFFER_DECISION_KINDS} AND chosen_ref LIKE ? "
        "ORDER BY created_at, id", (f"{OFFER_REF_PREFIX}%",))]


def offer_decision(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        f"SELECT * FROM router_decisions WHERE id = ? AND decision_kind IN {OFFER_DECISION_KINDS} AND chosen_ref LIKE ?",
        (decision_id, f"{OFFER_REF_PREFIX}%")).fetchone()
    return _offer_decision(row) if row is not None else None


def all_decisions(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """TE1b's daily decisions and TE3b's drawn offers together, oldest first (identical to :func:`decisions`
    while no offer was ever drawn)."""

    offers = offer_decisions(connection)
    daily = decisions(connection)
    if not offers:
        return daily
    return sorted([*daily, *offers], key=lambda d: (str(d["created_at"]), str(d["id"])))


def responses(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Every learner response (never a release), in response order."""

    if not tables_present(connection):
        return []
    return [dict(row) for row in connection.execute(
        f"SELECT * FROM router_suggestion_responses WHERE response IN {_RESPONSE_SQL} ORDER BY responded_at, id")]


def releases(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Every reservation let go (``released`` or ``expired``), in order."""

    if not tables_present(connection):
        return []
    return [dict(row) for row in connection.execute(
        f"SELECT * FROM router_suggestion_responses WHERE response IN {_RELEASE_SQL} ORDER BY responded_at, id")]


def response_for(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None:
    """The decision's one learner response (never its release)."""

    row = connection.execute(
        f"SELECT * FROM router_suggestion_responses WHERE decision_id = ? AND response IN {_RESPONSE_SQL}",
        (decision_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def release_for(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None:
    """The row that let the decision's reservation go, if one did."""

    row = connection.execute(
        f"SELECT * FROM router_suggestion_responses WHERE decision_id = ? AND response IN {_RELEASE_SQL}",
        (decision_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def response_for_lesson(connection: sqlite3.Connection, lesson_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM router_suggestion_responses WHERE lesson_id = ?", (lesson_id,)
    ).fetchone()
    return dict(row) if row is not None else None


def insert_response(
    connection: sqlite3.Connection,
    *,
    decision_id: str,
    response: str,
    candidate_ref: str,
    learning_object_ids: Sequence[str],
    responded_at: str,
    lesson_id: str | None = None,
    session_id: str | None = None,
    detail: Mapping[str, Any] | None = None,
) -> bool:
    """Append the decision's one response (or its one release); a second of either is a no-op (False)."""

    if response not in RESPONSE_KINDS and response not in RELEASE_KINDS:
        raise ValueError(f"unknown suggestion response {response!r}")
    kinds = _RESPONSE_SQL if response in RESPONSE_KINDS else _RELEASE_SQL
    cursor = connection.execute(
        f"INSERT INTO router_suggestion_responses ({','.join(RESPONSE_COLUMNS)}) "
        f"VALUES ({','.join('?' for _ in RESPONSE_COLUMNS)}) "
        f"ON CONFLICT(decision_id) WHERE response IN {kinds} DO NOTHING",
        (f"rsr_{new_ulid().lower()}", decision_id, response, candidate_ref,
         json.dumps(list(learning_object_ids)), lesson_id, session_id, responded_at,
         json.dumps(dict(detail or {}), sort_keys=True), responded_at),
    )
    return cursor.rowcount > 0


def lesson_exists(connection: sqlite3.Connection, lesson_id: str) -> bool:
    return connection.execute("SELECT 1 FROM lessons WHERE id = ?", (lesson_id,)).fetchone() is not None


def open_lesson_learning_objects(connection: sqlite3.Connection) -> set[str]:
    """The LOs of every lesson still open."""

    out: set[str] = set()
    if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='lessons'").fetchone() is None:
        return out
    for (raw,) in connection.execute("SELECT learning_object_ids_json FROM lessons WHERE closed_at IS NULL"):
        out.update(str(lo) for lo in json.loads(raw or "[]"))
    return out


def last_lesson_opened_by_learning_object(connection: sqlite3.Connection) -> dict[str, str]:
    """Per LO, when the latest lesson on it opened."""

    out: dict[str, str] = {}
    if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='lessons'").fetchone() is None:
        return out
    for raw, opened in connection.execute("SELECT learning_object_ids_json, opened_at FROM lessons ORDER BY opened_at, id"):
        for lo in json.loads(raw or "[]"):
            out[str(lo)] = str(opened)
    return out


def attempts_by_learning_object(connection: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    """Each LO's attempts, oldest first (what the candidate reasons read)."""

    out: dict[str, list[dict[str, Any]]] = {}
    for row in connection.execute(
        "SELECT id, learning_object_id, attempt_type, correctness, hints_used, primed, created_at "
        "FROM practice_attempts ORDER BY created_at, id"
    ):
        out.setdefault(str(row["learning_object_id"]), []).append(dict(row))
    return out


__all__ = [
    "OFFER_REF_PREFIX",
    "RECEIPT_PREFIX",
    "RELEASE_KINDS",
    "RESPONSE_KINDS",
    "all_decisions",
    "attempts_by_learning_object",
    "decision",
    "decision_for_day",
    "decisions",
    "offer_decision",
    "offer_decisions",
    "insert_response",
    "last_lesson_opened_by_learning_object",
    "lesson_exists",
    "open_lesson_learning_objects",
    "receipt_key",
    "release_for",
    "releases",
    "response_for",
    "response_for_lesson",
    "responses",
    "tables_present",
]
