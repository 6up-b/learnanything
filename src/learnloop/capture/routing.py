"""Durable desktop route intents, separate from destination commits.

Intent identity survives a failed receipt write. Destinations must use its ID
and recover that ID before executing again. Transactions here are short; no AI,
vault reload, or destination operation runs inside them.
"""
from __future__ import annotations

import json

from learnloop.ids import new_ulid

from .errors import CaptureError
from .inbox import get_capture


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
                raise CaptureError("capture_conflict", 409, "Retry the original capture route and inputs; a destination may already exist.")
            return intent
        if capture["status"] == "routed":
            raise CaptureError("capture_conflict", 409, "Capture already has a completed route.")
        return None


def begin_route(repo, capture_id: str, *, route: str, request_hash: str) -> dict:
    with repo.atomic(), repo.connection() as conn:
        existing = read_route_intent(repo, capture_id, route=route, request_hash=request_hash)
        if existing is not None:
            return existing
        intent = {"request_hash": request_hash, "destination_id": new_ulid()}
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
