"""RO0 row 4: who initiated a source exposure.

``learner``, ``plan``, ``tutor_citation``, ``dose_offer`` or ``lesson``, with the block, session and visit ids where
they are known. A new field and not a new row: existing coldness readers count rows, and ``context`` keeps its meaning.
It separates what the learner chose from what the plan sent. Off, the writer's statement is the predecessor's.

A link is never guessed (landing ruling R2). A visit's block and session are the ones the client captured at the
opening, else the ones in force at the visit's own time (``occurred_at``, not when its batch arrived); when none fits or
more than one does, the visit says the link is unknown. An opening the server records as it happens names the one open
session, and none when two are open.
"""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from learnloop.data_capture.gates import objective_receipts_on

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
#: The extra columns of ``source_exposure_events`` (a vault below migration 243 has none).
COLUMNS: tuple[str, ...] = ("initiator", "initiator_block_id", "initiator_session_id", "initiator_visit_id")
#: How a visit's ``session_id`` and ``block_id`` were linked (``session_link``, ``block_link`` in its payload).
LINK_CLIENT = "client"
LINK_AS_OF_EVENT = "as_of_event"
LINK_UNKNOWN = "unknown"


def initiator_for(context: str | None, stated: str | None = None) -> str:
    """A client's word when it is one of ours, else what the context says, else the learner."""

    if stated in INITIATORS:
        return str(stated)
    return _BY_CONTEXT.get(str(context or ""), LEARNER)


def _only(rows: list[Any]) -> str | None:
    return str(rows[0][0]) if len(rows) == 1 else None


def session_at(repository: Any, at: str | None = None) -> str | None:
    """The one session in force at ``at``: started by then and not ended before it. ``at`` None (an opening recorded
    as it happens): the one session still open. None when none fits or more than one does, never the newest."""

    try:
        with repository.connection() as connection:
            if at is None:
                rows = connection.execute("SELECT id FROM sessions WHERE ended_at IS NULL LIMIT 2").fetchall()
            else:
                rows = connection.execute(
                    "SELECT id FROM sessions WHERE julianday(started_at) <= julianday(?) "
                    "AND (ended_at IS NULL OR julianday(ended_at) >= julianday(?)) LIMIT 2", (at, at)).fetchall()
    except Exception:  # noqa: BLE001 - a receipt never blocks an opening
        logger.warning("router objective: the session of an exposure was not read", exc_info=True)
        return None
    return _only(rows)


def plan_block_at(repository: Any, extraction_id: str | None, at: str) -> str | None:
    """The one plan reading block on this reading in force at ``at``: created by then and not ended before it. None
    when none fits or more than one does."""

    if not extraction_id:
        return None
    try:
        with repository.connection() as connection:
            rows = connection.execute(
                "SELECT b.id FROM attention_blocks b WHERE b.daily_plan_id IS NOT NULL AND b.reading_json IS NOT NULL "
                "AND json_extract(b.reading_json, '$.extraction_id') = ? AND julianday(b.created_at) <= julianday(?) "
                "AND NOT EXISTS (SELECT 1 FROM attention_block_events e WHERE e.block_id = b.id AND e.kind = 'block_ended' "
                "AND julianday(e.created_at) < julianday(?)) LIMIT 2", (extraction_id, at, at)).fetchall()
    except Exception:  # noqa: BLE001 - a receipt never blocks a visit
        logger.warning("router objective: the plan's reading block was not read", exc_info=True)
        return None
    return _only(rows)


def fields(config: Any, repository: Any, *, context: str | None, initiator: str | None = None, block_id: str | None = None,
           session_id: str | None = None, visit_id: str | None = None) -> dict[str, Any]:
    """The event's RO0 fields, ``{}`` when the receipts are off (the writer then writes what it always did)."""

    if not objective_receipts_on(config):
        return {}
    return {
        "initiator": initiator_for(context, initiator),
        "initiator_block_id": block_id,
        "initiator_session_id": session_id or session_at(repository),
        "initiator_visit_id": visit_id,
    }


def visit_fields(config: Any, repository: Any, payload: Mapping[str, Any], *, at: str) -> dict[str, Any]:
    """What a Reader visit's event adds: its initiator, and its session and (a plan-sent visit's) block, each as the
    client captured it at the opening, else as of ``at``, the visit's own time; else the link is unknown."""

    initiator = initiator_for(None, str(payload.get("initiator") or "") or None)
    out: dict[str, Any] = {"initiator": initiator}
    if payload.get("session_id"):
        out.update(session_id=payload["session_id"], session_link=LINK_CLIENT)
    elif (session := session_at(repository, at)) is not None:
        out.update(session_id=session, session_link=LINK_AS_OF_EVENT)
    else:
        out["session_link"] = LINK_UNKNOWN
    if payload.get("block_id"):
        out.update(block_id=payload["block_id"], block_link=LINK_CLIENT)
    elif initiator == PLAN:
        if (block := plan_block_at(repository, payload.get("extraction_id"), at)) is not None:
            out.update(block_id=block, block_link=LINK_AS_OF_EVENT)
        else:
            out["block_link"] = LINK_UNKNOWN
    return out


__all__ = ["COLUMNS", "DOSE_OFFER", "INITIATORS", "LEARNER", "LESSON", "LINK_AS_OF_EVENT", "LINK_CLIENT", "LINK_UNKNOWN",
           "PLAN", "TUTOR_CITATION", "fields", "initiator_for", "plan_block_at", "session_at", "visit_fields"]
