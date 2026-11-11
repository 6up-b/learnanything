"""What other test files use from ``tests/test_mobile_phone_contract.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from typing import Any


def _has(value: Any, path: str) -> bool:
    """``a.b``, and ``a[].b`` for every element of the list ``a`` (at least one)."""

    head, _, rest = path.partition(".")
    many = head.endswith("[]")
    key = head[:-2] if many else head
    if not isinstance(value, dict) or key not in value:
        return False
    found = value[key]
    if not rest:
        return not many or isinstance(found, list)
    if many:
        return isinstance(found, list) and bool(found) and all(_has(element, rest) for element in found)
    return _has(found, rest)
