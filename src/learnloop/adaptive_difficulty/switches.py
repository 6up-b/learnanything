"""AD1's switches, read from config only (``[adaptive_difficulty]``, spec §11.1, §11.4).

A config without the section (a partial config built by hand) reads every
switch as off: logging is something a vault opts into by having the section,
which every current config does by default.
"""

from __future__ import annotations

from typing import Any

#: The in-process forecasters written in the serve transaction (§8.2).
IN_PROCESS_FORECASTERS = ("mastery_ekf", "lo_general+composite")
LLM_V1 = "llm_v1:item"
LLM_V3_LLM = "llm_v3:llm"
LLM_V3_DECIDER = "llm_v3:decider"
OUTSIDE_FORECASTERS = (LLM_V1, LLM_V3_LLM, LLM_V3_DECIDER)


def _section(config: Any) -> Any:
    return getattr(config, "adaptive_difficulty", None)


def ad_enabled(config: Any) -> bool:
    """The master switch (``adaptive_difficulty.enabled``)."""

    section = _section(config)
    return bool(section is not None and getattr(section, "enabled", False))


def receipts_enabled(config: Any) -> bool:
    """``forecast_receipts``: the serve-time sweep, serve inputs, in-process forecasts and the marker."""

    return ad_enabled(config) and bool(getattr(_section(config), "forecast_receipts", False))


def outside_forecasters(config: Any) -> tuple[str, ...]:
    """The outside forecasters that run; () with the switch off.

    Outside forecasts are receipts too: they run only while receipts are on."""

    if not receipts_enabled(config):
        return ()
    chosen = set(getattr(_section(config), "outside_forecasters", None) or ())
    return tuple(name for name in OUTSIDE_FORECASTERS if name in chosen)


def rating_tap_enabled(config: Any) -> bool:
    return ad_enabled(config) and bool(getattr(_section(config), "rating_tap", False))


def feature_audit_enabled(config: Any) -> bool:
    return ad_enabled(config) and bool(getattr(_section(config), "feature_audit", False))


def any_background_work(config: Any) -> bool:
    """Whether a serve or a plan build may start a background AD job."""

    return bool(outside_forecasters(config)) or feature_audit_enabled(config)


__all__ = [
    "IN_PROCESS_FORECASTERS",
    "LLM_V1",
    "LLM_V3_DECIDER",
    "LLM_V3_LLM",
    "OUTSIDE_FORECASTERS",
    "ad_enabled",
    "any_background_work",
    "feature_audit_enabled",
    "outside_forecasters",
    "rating_tap_enabled",
    "receipts_enabled",
]
