"""RO0 row 4: who initiated a source exposure.

``learner``, ``plan``, ``tutor_citation``, ``dose_offer`` or ``lesson``, with the block, session and visit ids where
they are known. A new field and not a new row: existing coldness readers count rows, and ``context`` keeps its meaning.
It separates what the learner chose from what the plan sent. Off, the writer's statement is the predecessor's.
"""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from learnloop.data_capture.gates import objective_receipts_on
from learnloop.db.stores import router_objective as store

logger = logging.getLogger(__name__)

LEARNER = "learner"
PLAN = "plan"
TUTOR_CITATION = "tutor_citation"
DOSE_OFFER = "dose_offer"
LESSON = "lesson"
INITIATORS: frozenset[str] = frozenset({LEARNER, PLAN, TUTOR_CITATION, DOSE_OFFER, LESSON})
#: Contexts that say by themselves who sent the learner there; every other is the learner's own opening.
_BY_CONTEXT: Mapping[str, str] = {
    "tutor_citation": TUTOR_CITATION,
    "remediation": PLAN,
    "remediation_delivery": PLAN,
}
#: The extra columns of ``source_exposure_events`` (a vault below migration 242 has none).
COLUMNS: tuple[str, ...] = ("initiator", "initiator_block_id", "initiator_session_id", "initiator_visit_id")


def initiator_for(context: str | None, stated: str | None = None) -> str:
    """A client's word when it is one of ours, else what the context says, else the learner."""

    if stated in INITIATORS:
        return str(stated)
    return _BY_CONTEXT.get(str(context or ""), LEARNER)


def open_session_id(repository: Any) -> str | None:
    """The open session, the one an exposure now belongs to; None when it cannot be said."""

    try:
        found = repository.most_recent_open_session()
    except Exception:  # noqa: BLE001 - a receipt never blocks an opening
        logger.warning("router objective: the open session was not read", exc_info=True)
        return None
    return str(found["id"]) if found else None


def fields(config: Any, repository: Any, *, context: str | None, initiator: str | None = None, block_id: str | None = None,
           session_id: str | None = None, visit_id: str | None = None) -> dict[str, Any]:
    """The event's RO0 fields, ``{}`` off or below the migration (the writer then writes what it always did)."""

    if not objective_receipts_on(config):
        return {}
    try:
        with repository.connection() as connection:
            if not store.column_present(connection, "source_exposure_events", "initiator"):
                return {}
    except Exception:  # noqa: BLE001 - a receipt never blocks an opening
        logger.warning("router objective: the exposure's columns were not read", exc_info=True)
        return {}
    return {
        "initiator": initiator_for(context, initiator),
        "initiator_block_id": block_id,
        "initiator_session_id": session_id or open_session_id(repository),
        "initiator_visit_id": visit_id,
    }


def plan_block_for_reading(repository: Any, extraction_id: str | None) -> str | None:
    """The plan's newest reading block on this reading: the block a plan-sent visit belongs to."""

    if not extraction_id:
        return None
    try:
        with repository.connection() as connection:
            row = connection.execute(
                "SELECT id FROM attention_blocks WHERE daily_plan_id IS NOT NULL AND reading_json IS NOT NULL "
                "AND json_extract(reading_json, '$.extraction_id') = ? ORDER BY created_at DESC, id DESC LIMIT 1",
                (extraction_id,)).fetchone()
    except Exception:  # noqa: BLE001 - a receipt never blocks a visit
        logger.warning("router objective: the plan's reading block was not read", exc_info=True)
        return None
    return str(row[0]) if row is not None else None


def visit_fields(config: Any, repository: Any, payload: Mapping[str, Any]) -> dict[str, Any]:
    """What a Reader visit's event adds: its initiator, and the server's session and the plan's block."""

    initiator = initiator_for(None, str(payload.get("initiator") or "") or None)
    block = payload.get("block_id") or (plan_block_for_reading(repository, payload.get("extraction_id"))
                                        if initiator == PLAN else None)
    return {
        "initiator": initiator,
        **({"block_id": block} if block else {}),
        **({"session_id": session} if (session := payload.get("session_id") or open_session_id(repository)) else {}),
    }


__all__ = ["COLUMNS", "DOSE_OFFER", "INITIATORS", "LEARNER", "LESSON", "PLAN", "TUTOR_CITATION", "fields", "initiator_for",
           "open_session_id", "plan_block_for_reading", "visit_fields"]
