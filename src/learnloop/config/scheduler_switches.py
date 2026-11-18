"""The scheduler's surprise interval switch.

When remove_interval_factor is enabled, the FSRS interval omits the surprise factor.
"""

from __future__ import annotations

from typing import Any


def interval_factor_removed(config: Any) -> bool:
    """§5.1: True when the FSRS interval carries no surprise factor (the switch)."""

    scheduler = getattr(config, "scheduler", None)
    surprise = getattr(scheduler, "surprise", None)
    return bool(getattr(surprise, "remove_interval_factor", False))
