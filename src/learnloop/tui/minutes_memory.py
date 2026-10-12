"""The TUI's remembered session minutes (daily-loop DL0, ``spec_daily_loop_v1.md`` §6.6).

The TUI begins practice without recording a session row (unchanged by DL0: an
open row would be adopted by the desktop as its active session, and a row moves
the streak and the re-entry gap), so "the last session's minutes" never sees a
TUI Begin. The
minutes a TUI Begin used are kept here instead, in the machine-global LearnLoop
config directory beside ``settings.env``: one small JSON file per vault, keyed by
the vault's resolved path. Start offers the newer of this choice and the last
session's minutes (``remembered_session_minutes``).

Best effort, like any preference: a missing, unreadable or unwritable file means
nothing is remembered, never a failed Begin. DL1's
``daily_plans.remembered_minutes`` replaces this store.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.config.loader import global_settings_path
from learnloop.scheduling.session_minutes import ChosenMinutes

_SCHEMA_VERSION = 1


def chosen_minutes_path(vault_root: Path) -> Path:
    """Where the TUI keeps the minutes it last began with for ``vault_root``."""

    resolved = str(Path(vault_root).resolve())
    digest = hashlib.sha256(resolved.encode("utf-8")).hexdigest()[:16]
    return global_settings_path().parent / "tui" / f"session-minutes-{digest}.json"


def load_chosen_minutes(vault_root: Path) -> ChosenMinutes | None:
    """The minutes the TUI last began with on this vault, or None."""

    try:
        data = json.loads(chosen_minutes_path(vault_root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("vault_root") != str(Path(vault_root).resolve()):
        return None
    minutes = data.get("minutes")
    chosen_at = data.get("chosen_at")
    if isinstance(minutes, bool) or not isinstance(minutes, int) or minutes <= 0:
        return None
    if not isinstance(chosen_at, str):
        return None
    try:
        if parse_utc(chosen_at) is None:
            return None
    except ValueError:
        return None
    return ChosenMinutes(minutes=minutes, chosen_at=chosen_at)


def save_chosen_minutes(vault_root: Path, minutes: int, *, clock: Clock | None = None) -> bool:
    """Remember a TUI Begin's minutes. False (never an error) when it can't be written."""

    path = chosen_minutes_path(vault_root)
    payload = {
        "schema_version": _SCHEMA_VERSION,
        "vault_root": str(Path(vault_root).resolve()),
        "minutes": int(minutes),
        "chosen_at": utc_now_iso(clock),
    }
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        os.replace(temporary, path)
    except OSError:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        return False
    return True


__all__ = ["chosen_minutes_path", "load_chosen_minutes", "save_chosen_minutes"]
