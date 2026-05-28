from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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

