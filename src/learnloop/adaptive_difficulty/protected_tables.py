"""The AD guard's table registry (the AD23 redesign, step 2). Step 1: observe only."""

from __future__ import annotations

from typing import Any


def read_verdict(table: str, *, rules: str | None, reader: str) -> str | None:
    return None


def write_verdict(table: str, *, reader: str) -> str | None:
    return None
