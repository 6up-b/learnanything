"""What other test files use from ``tests/test_rospeed2_connections.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any


def _canon(value: Any) -> Any:
    """A value as exact JSON (floats by their bits)."""

    import numpy as np

    if is_dataclass(value) and not isinstance(value, type):
        return {"__type": type(value).__name__, **{f.name: _canon(getattr(value, f.name)) for f in fields(value)}}
    if isinstance(value, dict):
        return {str(key): _canon(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [_canon(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_canon(item) for item in value.tolist()]
    if isinstance(value, (float, np.floating)):
        return float(value).hex()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (set, frozenset)):
        return sorted(_canon(item) for item in value)
    return value
