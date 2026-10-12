"""Explicit capabilities; M1 intentionally exposes no RPC methods."""
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Literal, Mapping


@dataclass(frozen=True)
class MobileMethod:
    name: str
    milestone: str
    kind: Literal["short", "long"]
    retry_safe: bool
    param_constraints: Callable[[dict], None]


ALLOWLIST: Mapping[str, MobileMethod] = MappingProxyType({})


def validate_envelope(value: object) -> dict:
    if (
        not isinstance(value, dict)
        or set(value) - {"method", "params", "request_id"}
        or not isinstance(value.get("method"), str)
        or not value["method"].strip()
        or not isinstance(value.get("params", {}), dict)
        or ("request_id" in value and (
            not isinstance(value["request_id"], str)
            or not value["request_id"].strip()
            or len(value["request_id"]) > 256
        ))
    ):
        raise ValueError("invalid RPC envelope")
    return value
