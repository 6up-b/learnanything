"""Durable desktop route intents, separate from destination commits.

Intent identity survives a failed receipt write. Destinations must use its ID
and recover that ID before executing again. Transactions here are short; no AI,
vault reload, or destination operation runs inside them.

An intent also keeps the request that created it, so a restarted desktop can
finish it without the dialog's lost form values (``pending_route``). An
unfinished intent whose destination provably never committed can be replaced
by a different request or route (``supersede``), never one that may have.
"""
from __future__ import annotations

import json

from learnloop.ids import new_ulid

from .errors import CaptureError
from .inbox import get_capture

_CONFLICT = ("This capture has an unfinished save whose destination may already exist. "
             "Finish the original capture route (Finish saving) or retry it with the same inputs.")


def read_route_intent(repo, capture_id: str, *, route: str, request_hash: str) -> dict | None:
    with repo.connection() as conn:
        capture = get_capture(repo, capture_id)
        if capture["status"] not in ("new", "routed"):
            raise CaptureError("capture_conflict", 409, "Capture was dismissed or purged.")
        row = conn.execute(
            "SELECT intent_route,intent_json FROM capture_routes WHERE capture_id=?",
            (capture_id,),
        ).fetchone()
        if row["intent_json"]:
            intent = json.loads(row["intent_json"])
            if row["intent_route"] != route or intent["request_hash"] != request_hash:
                raise CaptureError("capture_conflict", 409, _CONFLICT)
            return intent
        if capture["status"] == "routed":
            raise CaptureError("capture_conflict", 409, "Capture already has a completed route.")
        return None


def pending_route(repo, capture_id: str) -> dict | None:
    """The unfinished intent of a still-new capture: route, request, destination."""
    with repo.connection() as conn:
        capture = get_capture(repo, capture_id)
        if capture["status"] != "new":
            return None
        row = conn.execute(
            "SELECT intent_route,intent_json FROM capture_routes WHERE capture_id=?",
            (capture_id,),
        ).fetchone()
    if not row["intent_json"]:
        return None
    return {**json.loads(row["intent_json"]), "route": row["intent_route"]}


def begin_route(
    repo, capture_id: str, *, route: str, request_hash: str,
    request: dict | None = None, supersede: str | None = None,
) -> dict:
    """Create (or return the identical) intent.

    ``supersede`` names the destination ID of an unfinished intent the caller has
    established never committed; it is replaced only if it is still that exact,
    response-less intent (compare-and-swap), with a fresh destination ID.
    """
    with repo.atomic(), repo.connection() as conn:
        if supersede is None:
            existing = read_route_intent(repo, capture_id, route=route, request_hash=request_hash)
            if existing is not None:
                return existing
        else:
            current = pending_route(repo, capture_id)
            if (current is None or current.get("destination_id") != supersede
                    or "response" in current):
                raise CaptureError("capture_conflict", 409, _CONFLICT)
        intent = {"request_hash": request_hash, "destination_id": new_ulid()}
        if request is not None:
            intent["request"] = request
        conn.execute(
            "UPDATE capture_routes SET intent_route=?,intent_json=? WHERE capture_id=?",
            (route, json.dumps(intent), capture_id),
        )
        return intent


def update_route_intent(repo, capture_id: str, **values) -> dict:
    with repo.atomic(), repo.connection() as conn:
        capture = get_capture(repo, capture_id)
        if capture["status"] not in ("new", "routed"):
            raise CaptureError("capture_conflict", 409, "Capture was dismissed or purged.")
        row = conn.execute(
            "SELECT intent_json FROM capture_routes WHERE capture_id=?", (capture_id,),
        ).fetchone()
        intent = json.loads(row["intent_json"])
        intent.update(values)
        conn.execute(
            "UPDATE capture_routes SET intent_json=? WHERE capture_id=?",
            (json.dumps(intent), capture_id),
        )
        return intent
