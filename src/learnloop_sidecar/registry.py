from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from learnloop_sidecar.dto import EmptyParams, ParamsModel


Handler = Callable[[Any, ParamsModel], dict[str, Any] | None]


@dataclass(frozen=True)
class MethodSpec:
    name: str
    params_model: type[ParamsModel]
    handler: Handler


METHOD_REGISTRY: dict[str, MethodSpec] = {}


def method(name: str, params_model: type[ParamsModel] = EmptyParams) -> Callable[[Handler], Handler]:
    def register(handler: Handler) -> Handler:
        METHOD_REGISTRY[name] = MethodSpec(name=name, params_model=params_model, handler=handler)
        return handler

    return register

