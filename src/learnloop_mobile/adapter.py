"""The HTTP side of ``POST /rpc`` (spec §6.2): pure translation, no I/O.

The sidecar speaks JSON-RPC and the phone speaks ``{ok, result}`` or ``{ok, error}``,
the ``CommandError`` shape the desktop client already normalizes. Nothing here runs a
handler; :mod:`learnloop_mobile.runtime` does, on a worker.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

#: §6.2's table. A typed refusal the table does not name is 409: the request was
#: understood and the state says no (``item_retired``, ``session_ended``,
#: ``held_out_material``, ``clarification_unanswerable``, …). The body's stable code
#: is what a client acts on.
_STATUS_BY_CODE: Mapping[str, int] = {
    "validation_error": 422,
    "invalid_request": 422,
    "not_found": 404,
    "method_not_allowed": 403,
    "session_open_elsewhere": 409,
    "session_moved": 409,
    "current_item_desktop_only": 409,
    "submission_conflict": 409,
    "capture_conflict": 409,
    "desktop_only": 409,
    "database_busy": 503,
    "completion_busy": 503,
    "host_busy": 503,
    # A secondary reload that could not settle, or a schema the primary must migrate:
    # the phone waits, and the desktop or the next request repairs it.
    "vault_unsettled": 503,
    "schema_mismatch": 503,
    "grading_fallback_required": 409,
    "internal": 500,
}
_RETRYABLE = frozenset({
    "database_busy", "completion_busy", "host_busy", "vault_unsettled", "schema_mismatch", "grading_fallback_required",
})
_CONFLICT = 409


def status_for(code: str) -> int:
    return _STATUS_BY_CODE.get(code, _CONFLICT)


def error_body(code: str, message: str, *, retryable: bool = False, details: Mapping[str, Any] | None = None) -> dict:
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "retryable": bool(retryable) or code in _RETRYABLE,
            "details": dict(details or {}),
        },
    }


def translate(response: Mapping[str, Any]) -> tuple[int, dict]:
    """A ``_handle`` response as ``(HTTP status, body)``, flattened from ``error.data``."""

    if "error" not in response:
        return 200, {"ok": True, "result": response.get("result")}
    error = response["error"]
    data = error.get("data") or {}
    code = str(data.get("code") or "internal")
    body = error_body(code, str(error.get("message") or code), retryable=bool(data.get("retryable")),
                      details=data.get("details"))
    return status_for(code), body


def flat_error(response: Mapping[str, Any]) -> dict | None:
    """The stored form of a failed job's error: ``CommandError``'s four fields."""

    if "error" not in response:
        return None
    return translate(response)[1]["error"]


def canonical_hash(params: Mapping[str, Any]) -> str:
    """§6.3: sorted-key JSON of the validated params, so a retry's spelling cannot conflict."""

    encoded = json.dumps(params, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
