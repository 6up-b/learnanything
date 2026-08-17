from __future__ import annotations

import json
import logging
import time
from typing import Any, TextIO

from pydantic import ValidationError

import learnloop_sidecar.handlers  # noqa: F401
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError, json_rpc_error, sidecar_error
from learnloop_sidecar.logging import log_event
from learnloop_sidecar.registry import METHOD_REGISTRY

LOG = logging.getLogger(__name__)

_INTERNAL_ERROR_MESSAGE = (
    "LearnLoop could not confirm whether this action completed. Check the current "
    "state before trying it again."
)


def serve(stdin: TextIO, stdout: TextIO) -> None:
    ctx = SidecarContext()
    for raw_line in stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            _write(stdout, {"jsonrpc": "2.0", "id": None, "error": json_rpc_error(-32700, str(exc))})
            continue
        response = _handle(ctx, request)
        if response is not None:
            _write(stdout, response)
        if ctx.shutdown_requested:
            break


def _handle(ctx: SidecarContext, request: Any) -> dict[str, Any] | None:
    if (
        not isinstance(request, dict)
        or request.get("jsonrpc") != "2.0"
        or not isinstance(request.get("method"), str)
        or not request["method"]
    ):
        return {"jsonrpc": "2.0", "id": _request_id(request), "error": json_rpc_error(-32600, "Invalid request.")}
    request_id = request.get("id")
    method_name = request["method"]
    if request_id is None and str(method_name).startswith("$/"):
        return None
    spec = METHOD_REGISTRY.get(method_name)
    if spec is None:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": json_rpc_error(-32601, f"Unknown method {method_name}."),
        }
    started = time.perf_counter()
    log_event("rpc.request", method=method_name, id=request_id)
    try:
        raw_params = request.get("params")
        params = spec.params_model.model_validate({} if raw_params is None else raw_params)
        result = spec.handler(ctx, params)
    except ValidationError as exc:
        log_event("rpc.error", method=method_name, id=request_id, code="validation_error",
                  duration_ms=_elapsed_ms(started))
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": json_rpc_error(
                -32602,
                "Invalid params.",
                stable_code="validation_error",
                details={"errors": _safe_validation_errors(exc)},
            ),
        }
    except SidecarError as exc:
        log_event("rpc.error", method=method_name, id=request_id, code=exc.code,
                  message=exc.message, duration_ms=_elapsed_ms(started))
        return {"jsonrpc": "2.0", "id": request_id, "error": sidecar_error(exc)}
    except Exception:
        LOG.exception("handler failed")
        log_event("rpc.error", level=logging.ERROR, method=method_name, id=request_id,
                  code="internal", duration_ms=_elapsed_ms(started))
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": json_rpc_error(
                -32603,
                _INTERNAL_ERROR_MESSAGE,
                stable_code="internal",
                retryable=False,
                details={"method": method_name, "outcome": "unknown"},
            ),
        }
    log_event("rpc.response", method=method_name, id=request_id, duration_ms=_elapsed_ms(started))
    if request_id is None:
        return None
    return {"jsonrpc": "2.0", "id": request_id, "result": result if result is not None else {"ok": True}}


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)


def _write(stdout: TextIO, response: dict[str, Any]) -> None:
    try:
        encoded = json.dumps(response, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError):
        LOG.exception("sidecar response was not JSON serializable")
        encoded = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": response.get("id"),
                "error": json_rpc_error(
                    -32603,
                    _INTERNAL_ERROR_MESSAGE,
                    stable_code="internal",
                    retryable=False,
                    details={"phase": "serialize_response", "outcome": "unknown"},
                ),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    stdout.write(encoded + "\n")
    stdout.flush()


def _request_id(request: Any) -> Any:
    return request.get("id") if isinstance(request, dict) else None


def _safe_validation_errors(exc: ValidationError) -> list[dict[str, Any]]:
    """Return actionable Pydantic diagnostics without echoing request values.

    ``ValidationError.errors()`` includes the rejected ``input`` by default.
    Some sidecar inputs contain learner answers or API keys, and this data is
    forwarded through Tauri to the UI.  Location, type, and message are enough
    for schema-drift handling and field-level diagnostics.
    """

    return [
        {
            "location": list(error.get("loc") or ()),
            "type": error.get("type", "value_error"),
            "message": error.get("msg", "Invalid value."),
        }
        for error in exc.errors(include_url=False)
    ]
