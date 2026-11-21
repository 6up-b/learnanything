from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from learnloop.ai import model_use


APPLICATION_ERROR_CODE = -32001


@dataclass
class SidecarError(Exception):
    code: str
    message: str
    retryable: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message


def json_rpc_error(
    code: int,
    message: str,
    *,
    stable_code: str | None = None,
    retryable: bool = False,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "code": stable_code or _stable_code_for_json_rpc(code),
        "retryable": retryable,
    }
    if details:
        data["details"] = details
    return {"code": code, "message": message, "data": data}


def sidecar_error(exc: SidecarError) -> dict[str, Any]:
    return json_rpc_error(
        APPLICATION_ERROR_CODE,
        exc.message,
        stable_code=exc.code,
        retryable=exc.retryable,
        details=exc.details,
    )


def _stable_code_for_json_rpc(code: int) -> str:
    return {
        -32700: "parse_error",
        -32600: "invalid_request",
        -32601: "method_not_found",
        -32602: "validation_error",
        -32603: "internal",
    }.get(code, "internal")



def waiting_for_ok_error() -> SidecarError:
    """No OK to use AI yet: nothing was sent. The desktop shows the one sheet and, once the
    learner says OK, sends the same request again (once); the phone says where to say it."""

    return SidecarError(model_use.WAITING_CODE, model_use.WAITING_MESSAGE, details={"waiting_for_ok": True})


def require_ai_ok(vault_root: Path | str | None, client: Any | None = None) -> None:
    """Before an RPC starts model work: refuse it, and store nothing, while the OK is missing."""

    if model_use.waiting(vault_root, client):
        raise waiting_for_ok_error()
