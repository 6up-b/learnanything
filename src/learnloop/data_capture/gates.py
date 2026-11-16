"""The switches of data capture (``[data_capture]``) and of RO0's receipts. A leaf: no store, no domain.

``receipts_on`` acts at every algorithm version: a receipt changes nothing served.
Data capture's serving changes (mvp-0.44) have no switch: its kill switch went once
every vault was past the tag.
"""

from __future__ import annotations

from typing import Any


#: Data capture (mvp-0.44): R_cold under the shared delayed-completion definition (A4); ``router.outcomes`` derives it.
OUTCOME_VERSION_V3 = "router_outcomes_v3"


def receipts_on(config: Any) -> bool:
    section = getattr(config, "data_capture", None)
    return bool(getattr(section, "receipts", False))


def objective_receipts_on(config: Any) -> bool:
    """RO0's additive receipts and columns (``[router_objective] receipts``): at every algorithm version."""

    section = getattr(config, "router_objective", None)
    return bool(getattr(section, "receipts", False))


__all__ = ["OUTCOME_VERSION_V3", "objective_receipts_on", "receipts_on"]
