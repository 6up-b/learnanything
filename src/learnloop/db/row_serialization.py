"""Canonical JSON encoding and nullable JSON row decoding for database stores."""

from __future__ import annotations

import json
from typing import Any


def _json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _loads(value: str | None, default: Any) -> Any:
    if value is None:
        return default
    return json.loads(value)
