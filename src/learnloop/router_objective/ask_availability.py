"""RO0 row 3: whether Ask was available, per plan presentation and Reader visit.

``plan_presentations`` is append-only with one row per block and item, so ``ask_available`` holds the state at the
serve (:func:`at_serve`, the server's own rule). A later change, which only the screen sees (a diagnostic check's
contract loads, for one), is an impression event on the block's ledger (:func:`record_change`), never an update of the
row. Without this, "no question" can't be read as anything.
"""

from __future__ import annotations

import logging
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.data_capture.gates import objective_receipts_on
from learnloop.db.stores import daily_plans as plans
from learnloop.ids import new_ulid

logger = logging.getLogger(__name__)

EVENT_KIND = "ask_availability_changed"
#: The tutor refuses a teach-back's item (the AI plays the student): the server's own rule at a serve.
_REFUSED_MODES = frozenset({"teach_back"})


def at_serve(vault: Any, practice_item_id: str) -> int | None:
    """1 or 0 by the server's rule at the serve; None for an item this vault cannot read."""

    item = getattr(vault, "practice_items", {}).get(practice_item_id)
    if item is None:
        return None
    return 0 if getattr(item, "practice_mode", None) in _REFUSED_MODES else 1


def serve_fields(vault: Any, connection: Any, practice_item_id: str) -> dict[str, Any]:
    """The presentation row's new column, on or off, at or below migration 243. Never raises: a keyed pick's serve
    propagates its own failures, and a receipt's must not be one (landing ruling R1)."""

    try:
        if not objective_receipts_on(vault.config):
            return {}
        return {"ask_available": at_serve(vault, practice_item_id)}
    except Exception:  # noqa: BLE001 - a receipt never blocks a serve
        logger.warning("router objective: Ask's availability at this serve was not read", exc_info=True)
        return {}


def _standing(connection: Any, presentation: dict[str, Any]) -> int | None:
    state = presentation.get("ask_available")
    for row in connection.execute(
            "SELECT json_extract(detail_json, '$.presentation_id'), json_extract(detail_json, '$.ask_available') "
            "FROM attention_block_events WHERE block_id = ? AND kind = ? ORDER BY event_ordinal",
            (presentation["block_id"], EVENT_KIND)):
        if row[0] == presentation["id"]:
            state = row[1]
    return None if state is None else int(state)


def record_change(vault: Any, repository: Any, *, session_id: str | None, practice_item_id: str, available: bool,
                  reason: str | None = None, clock: Clock | None = None) -> bool:
    """The screen reports Ask's availability on an item it is showing. A presentation whose standing state already
    says so writes nothing, and an item the plan did not serve has no presentation to speak of. Never raises."""

    if not objective_receipts_on(vault.config) or not session_id:
        return False
    try:
        with repository.atomic(), repository.connection() as connection:
            row = connection.execute(
                "SELECT * FROM plan_presentations WHERE session_id = ? AND practice_item_id = ? "
                "ORDER BY served_at DESC, id DESC LIMIT 1", (session_id, practice_item_id)).fetchone()
            if row is None:
                return False
            presentation = dict(row)
            value = 1 if available else 0
            if _standing(connection, presentation) == value:
                return False
            plans.append_block_event(
                connection, event_id=new_ulid(), block_id=str(presentation["block_id"]), kind=EVENT_KIND,
                detail={"presentation_id": presentation["id"], "practice_item_id": practice_item_id,
                        "ask_available": value, **({"reason": str(reason)[:80]} if reason else {})},
                created_at=utc_now_iso(clock))
            return True
    except Exception:  # noqa: BLE001 - a receipt never blocks the screen
        logger.warning("router objective: an Ask availability change was not recorded", exc_info=True)
        return False


__all__ = ["EVENT_KIND", "at_serve", "record_change", "serve_fields"]
