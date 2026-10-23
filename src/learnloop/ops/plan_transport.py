"""Plan-first transport T1: the vault settings that still pin the Codex harness.

Owner decision 2026-10-21: every serving route uses the tool-free ChatGPT
plan, and a Codex (``codex_sdk`` / legacy ``http``) profile serves nothing
without ``ai.agent_harness_opt_in``. A vault's ``learnloop.toml`` that names a
Codex profile is not aliased silently at load (receipts and checkpoints key
on provider and model): `learnloop doctor` reports each such setting
(``ai:codex_route_pinned``) and `learnloop doctor --fix` rewrites it to the
plan profile of the same tier.

Only settings written in the file are read (``tomllib``, not the effective
config), so a code default is never reported and the rewrite touches only
what the owner wrote.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib
from typing import Any

from learnloop.ai.agent_harness import is_agent_harness_profile
from learnloop.config import LearnLoopConfig
from learnloop.config.schema import (
    CHATGPT_LOW_PROVIDER,
    CHATGPT_MEDIUM_PROVIDER,
    CODEX_PROVIDER_NAMES,
    CODEX_TO_PLAN_PROFILE,
)

FINDING_CODE = "ai:codex_route_pinned"


@dataclass(frozen=True)
class CodexPin:
    """One setting of ``learnloop.toml`` that names a Codex profile, and its rewrite."""

    setting: str
    key_path: tuple[str, ...]
    value: Any
    replacement: Any

    def as_dict(self) -> dict[str, Any]:
        return {"setting": self.setting, "value": self.value, "replacement": self.replacement}


def _is_codex(config: LearnLoopConfig, name: str) -> bool:
    return name in CODEX_PROVIDER_NAMES or is_agent_harness_profile(config.ai.providers.get(name))


def _plan_profile_for(config: LearnLoopConfig, name: str) -> str:
    """The plan profile of the same tier as Codex profile ``name``."""

    if name in CODEX_TO_PLAN_PROFILE:
        return CODEX_TO_PLAN_PROFILE[name]
    profile = config.ai.providers.get(name)
    effort = (getattr(profile, "reasoning_effort", None) or "").strip().lower()
    return CHATGPT_MEDIUM_PROVIDER if effort in {"medium", "high", "xhigh"} else CHATGPT_LOW_PROVIDER


def codex_pins(root: Path, config: LearnLoopConfig) -> list[CodexPin]:
    """Every setting written in ``root/learnloop.toml`` that names a Codex profile.

    Empty when the owner opted in to the agent harness (those settings are
    then served as written).
    """

    if config.ai.agent_harness_opt_in:
        return []
    try:
        with (root / "learnloop.toml").open("rb") as handle:
            raw = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return []
    ai = raw.get("ai")
    if not isinstance(ai, dict):
        return []
    pins: list[CodexPin] = []
    active = ai.get("active_provider")
    if isinstance(active, str) and active.strip() and _is_codex(config, active.strip()):
        pins.append(CodexPin("ai.active_provider", ("ai", "active_provider"), active,
                             _plan_profile_for(config, active.strip())))
    fallback = ai.get("fallback_provider")
    if isinstance(fallback, str) and fallback.strip() and _is_codex(config, fallback.strip()):
        # Codex is never a fallback; the plan's OpenRouter offer is asked instead.
        pins.append(CodexPin("ai.fallback_provider", ("ai", "fallback_provider"), fallback, ""))
    routing = ai.get("routing")
    if isinstance(routing, dict):
        for task, value in routing.items():
            if isinstance(value, str):
                if value.strip() and _is_codex(config, value.strip()):
                    pins.append(CodexPin(f"ai.routing.{task}", ("ai", "routing", task), value,
                                         _plan_profile_for(config, value.strip())))
            elif isinstance(value, list) and any(isinstance(entry, str) and _is_codex(config, entry.strip())
                                                 for entry in value):
                rewritten = list(dict.fromkeys(
                    _plan_profile_for(config, entry.strip())
                    if isinstance(entry, str) and _is_codex(config, entry.strip()) else entry
                    for entry in value
                ))
                pins.append(CodexPin(f"ai.routing.{task}", ("ai", "routing", task), value, rewritten))
    return pins


def finding_message(pin: CodexPin) -> str:
    target = f'"{pin.replacement}"' if pin.replacement != "" else "unset"
    return (
        f"{pin.setting} = {pin.value!r} names the Codex agent harness, which LearnLoop no longer uses for "
        f"serving (plan-first transport, owner decision 2026-10-21), so this route reads unavailable. "
        f"`learnloop doctor --fix` sets it to {target} (the ChatGPT plan); or set "
        "ai.agent_harness_opt_in = true to keep Codex."
    )


def fix_codex_pins(root: Path, config: LearnLoopConfig, *, dry_run: bool = False) -> dict[str, Any]:
    """Rewrite every :func:`codex_pins` setting in place (comments and layout kept)."""

    from learnloop.ops.settings_store import apply_config_updates

    pins = codex_pins(root, config)
    if pins and not dry_run:
        apply_config_updates(root / "learnloop.toml", {pin.key_path: pin.replacement for pin in pins})
    return {"dry_run": dry_run, "rewritten": [pin.as_dict() for pin in pins]}


__all__ = ["CodexPin", "FINDING_CODE", "codex_pins", "finding_message", "fix_codex_pins"]
