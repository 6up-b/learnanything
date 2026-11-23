from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict


def camel_name(name: str) -> str:
    head, *tail = name.split("_")
    return head + "".join(part[:1].upper() + part[1:] for part in tail)


class ParamsModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=camel_name,
        populate_by_name=True,
        extra="forbid",
    )


class EmptyParams(ParamsModel):
    pass


class Verbatim(dict):
    """Opaque JSON a reply carries as stored (a pad block's payload, a window's view, an anchor): its keys
    are the client's own, so camelCasing them would rewrite and could merge them ("a_b" and "aB")."""


def to_camel(value: Any) -> Any:
    if isinstance(value, Verbatim):
        return dict(value)
    if isinstance(value, BaseModel):
        return to_camel(value.model_dump(by_alias=True))
    if isinstance(value, Mapping):
        return {camel_name(str(key)): to_camel(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_camel(item) for item in value]
    if isinstance(value, tuple):
        return [to_camel(item) for item in value]
    return value


def versioned(payload: Mapping[str, Any] | None = None, *, version: int = 1) -> dict[str, Any]:
    result = {"version": version}
    if payload:
        result.update(to_camel(dict(payload)))
    return result

