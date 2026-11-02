"""Reader RW5d P5: the power condition of background figure work (spec_reader_show_me_figures_v1 §10b.4).

:func:`power_state` answers one question, whether this machine is on mains
power now, failing closed: anything it cannot establish counts as **on
battery**, and on battery no prebuild starts and a running one stops at its
next admission check (pressed builds are never affected: the learner asked).

* **Linux:** ``/sys/class/power_supply/*``. A battery reporting
  ``Discharging``, or a battery with no ``Mains``/``USB`` supply ``online = 1``,
  is on battery; power-profiles-daemon's active profile (``powerprofilesctl
  get``) ``power-saver`` counts as on battery too (prefer low power when the
  learner asked for it). A machine with no battery is on mains, but only
  when the inventory itself was read whole: no ``power_supply`` directory,
  or a supply whose type or a battery whose status can't be read, is unknown.
* **macOS:** ``pmset -g batt`` ("AC Power" is mains).
* **Windows:** ``GetSystemPowerStatus`` (``ACLineStatus`` 1 is mains).
* Anything else, or any read that fails: on battery.

The two process probes (``powerprofilesctl get``, ``pmset -g batt``) answer for
:data:`PROBE_CACHE_SECONDS` (follow-ups batch 6 (C): a Reader figures read and
every prefetch pass call :func:`power_state`, and each call started the probe,
30 process starts in one smoke run). On Linux the profile's answer is also
dropped the moment the power-supply inventory reads differently (a supply
plugged or unplugged, a battery's status changing): the sysfs files are read on
every call, so the condition they carry is never stale, and the profile is
probed again with it. A failed probe is cached too, still read as not on mains.

:func:`background_hold` is the one check every background build makes before
each physical request (the figure gate's hold): the switch, then the power.
It is here, beside the power reader, so the figure service and the rich job
read it without importing the prefetch service (a composition layer nothing
imports back). Never evidence; reads nothing in the vault but its config.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: Where Linux lists its power supplies.
SYSFS_ROOT = Path("/sys/class/power_supply")
#: ``keep`` (operational): how long a power-profile or pmset read may take
#: before it counts as unknown (fail closed: on battery).
PROBE_TIMEOUT_SECONDS = 2.0
#: ``keep`` (operational): how long one power-profile or pmset probe answers for
#: before it is started again (a bound on process starts, not a model parameter;
#: a Linux supply change drops it at once). Choosing power-saver or unplugging a
#: Mac reaches background builds within this window at the latest.
PROBE_CACHE_SECONDS = 30.0
#: Why a state is what it is (a word for the report's skipped-for-power count).
MAINS, BATTERY, POWER_SAVER, UNKNOWN = "mains", "battery", "power_saver", "unknown"


@dataclass(frozen=True)
class PowerState:
    #: True only when mains power was established.
    on_mains: bool
    #: ``mains`` | ``battery`` | ``power_saver`` | ``unknown``.
    reason: str
    detail: str = ""


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _profile(run: Callable[..., Any] | None = None) -> str | None:
    """power-profiles-daemon's active profile, or None (no daemon, no tool, a failure)."""

    tool = shutil.which("powerprofilesctl")
    if tool is None and run is None:
        return None
    runner = run or subprocess.run
    try:
        done = runner([tool or "powerprofilesctl", "get"], capture_output=True, text=True,
                      timeout=PROBE_TIMEOUT_SECONDS, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if getattr(done, "returncode", 1) != 0:
        return None
    return str(getattr(done, "stdout", "") or "").strip() or None


#: The probes' answers: name -> (key, monotonic time it was probed, answer).
_PROBE_CACHE: dict[str, tuple[object, float, Any]] = {}
#: Held across a probe, so concurrent callers wait for one start instead of each starting one
#: (at most :data:`PROBE_TIMEOUT_SECONDS`).
_PROBE_LOCK = threading.Lock()
#: The cache's clock (tests replace it).
_clock: Callable[[], float] = time.monotonic


def _cached_probe(name: str, key: object, probe: Callable[[], Any]) -> Any:
    """``probe()``'s answer, reused while ``key`` is unchanged and younger than :data:`PROBE_CACHE_SECONDS`."""

    with _PROBE_LOCK:
        now = _clock()
        hit = _PROBE_CACHE.get(name)
        if hit is not None and hit[0] == key and 0.0 <= now - hit[1] < PROBE_CACHE_SECONDS:
            return hit[2]
        try:
            answer = probe()
        except Exception:  # noqa: BLE001 - a probe that raises is not cached; the caller fails closed
            _PROBE_CACHE.pop(name, None)
            raise
        _PROBE_CACHE[name] = (key, now, answer)
        return answer


def reset_probe_cache() -> None:
    """Forget every cached probe answer (tests; :func:`set_power_reader`)."""

    with _PROBE_LOCK:
        _PROBE_CACHE.clear()


def linux_power_state(root: Path = SYSFS_ROOT, *, profile: Callable[[], str | None] | None = None) -> PowerState:
    """The Linux reading (module docstring); ``profile`` reads the power profile (tests inject it).

    Unset, the profile comes from :func:`_profile` through the probe cache, keyed by what this
    call read from sysfs: any supply's type, scope, online flag or status reading differently
    starts the probe again."""

    # Codex review F12: only a complete inventory establishes anything. No
    # sysfs directory, an unreadable one, or a supply whose type can't be read
    # is unknown (fail closed: on battery); an empty, readable directory is a
    # machine with no power supply listed at all (a desktop): mains.
    if not root.is_dir():
        return PowerState(False, UNKNOWN, "no power supply inventory")
    try:
        supplies = sorted(entry for entry in root.iterdir())
    except OSError:
        return PowerState(False, UNKNOWN, "power supplies unreadable")
    batteries: list[Path] = []
    mains_online = False
    inventory: list[tuple[str, str, str | None, str | None, str | None]] = []
    for supply in supplies:
        raw_kind = _read(supply / "type")
        if raw_kind is None:
            return PowerState(False, UNKNOWN, f"power supply {supply.name} unreadable")
        kind = raw_kind.lower()
        scope, online, status = _read(supply / "scope"), _read(supply / "online"), _read(supply / "status")
        inventory.append((supply.name, raw_kind, scope, online, status))
        if kind == "battery":
            if (scope or "").lower() == "device":
                continue  # a mouse's or headset's battery, not the machine's
            batteries.append(supply)
        elif kind in ("mains", "usb", "usb_c", "usb_pd") and (online or "") == "1":
            mains_online = True
    if profile is not None:
        level = profile()
    else:
        level = _cached_probe("powerprofilesctl", (str(root), tuple(inventory)), _profile)
    if level == "power-saver":
        return PowerState(False, POWER_SAVER, "power-saver profile")
    if not batteries:
        return PowerState(True, MAINS, "no battery")
    statuses = [_read(battery / "status") for battery in batteries]
    if any(status is None for status in statuses):
        return PowerState(False, UNKNOWN, "battery status unreadable")
    if any(str(status).lower() == "discharging" for status in statuses):
        return PowerState(False, BATTERY, "battery discharging")
    if not mains_online:
        return PowerState(False, BATTERY, "no mains supply online")
    return PowerState(True, MAINS, "mains online")


def mac_power_state(run: Callable[..., Any] | None = None) -> PowerState:
    """``pmset -g batt``; unset ``run``, its answer comes through the probe cache (no cheap change signal)."""

    if run is None:
        return _cached_probe("pmset", None, lambda: _mac_power_state(subprocess.run))
    return _mac_power_state(run)


def _mac_power_state(runner: Callable[..., Any]) -> PowerState:
    try:
        done = runner(["pmset", "-g", "batt"], capture_output=True, text=True, timeout=PROBE_TIMEOUT_SECONDS,
                      check=False)
    except (OSError, subprocess.SubprocessError):
        return PowerState(False, UNKNOWN, "pmset failed")
    text = str(getattr(done, "stdout", "") or "")
    if "AC Power" in text:
        return PowerState(True, MAINS, "AC Power")
    if "Battery Power" in text:
        return PowerState(False, BATTERY, "Battery Power")
    return PowerState(False, UNKNOWN, "pmset unclear")


def windows_power_state() -> PowerState:  # pragma: no cover - exercised on Windows only
    try:
        import ctypes

        class _Status(ctypes.Structure):
            _fields_ = [("ACLineStatus", ctypes.c_ubyte), ("BatteryFlag", ctypes.c_ubyte),
                        ("BatteryLifePercent", ctypes.c_ubyte), ("SystemStatusFlag", ctypes.c_ubyte),
                        ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]

        status = _Status()
        if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):  # type: ignore[attr-defined]
            return PowerState(False, UNKNOWN, "GetSystemPowerStatus failed")
        if status.SystemStatusFlag == 1:
            return PowerState(False, POWER_SAVER, "battery saver on")
        if status.ACLineStatus == 1:
            return PowerState(True, MAINS, "AC line")
        if status.ACLineStatus == 0:
            return PowerState(False, BATTERY, "on battery")
        return PowerState(False, UNKNOWN, "AC line unknown")
    except Exception:  # noqa: BLE001 - fail closed
        return PowerState(False, UNKNOWN, "power status unreadable")


#: Tests (and the stage's manual runs) replace the reader; unset, the platform's.
_OVERRIDE: Callable[[], PowerState] | None = None
#: ``LEARNLOOP_POWER_STATE=mains|battery``: a fixed reading for a copy run.
POWER_ENV = "LEARNLOOP_POWER_STATE"


def set_power_reader(reader: Callable[[], PowerState] | None) -> None:
    """Install a fixed reader (tests); None restores the platform's."""

    global _OVERRIDE
    _OVERRIDE = reader
    reset_probe_cache()


def power_state() -> PowerState:
    """Whether this machine is on mains now (module docstring). Never raises."""

    if _OVERRIDE is not None:
        try:
            return _OVERRIDE()
        except Exception:  # noqa: BLE001 - fail closed
            return PowerState(False, UNKNOWN, "power reader failed")
    pinned = os.environ.get(POWER_ENV, "").strip().lower()
    if pinned in (MAINS, BATTERY):
        return PowerState(pinned == MAINS, pinned, POWER_ENV)
    try:
        if sys.platform.startswith("linux"):
            return linux_power_state()
        if sys.platform == "darwin":
            return mac_power_state()
        if sys.platform.startswith("win"):
            return windows_power_state()
    except Exception:  # noqa: BLE001 - fail closed
        return PowerState(False, UNKNOWN, "power read failed")
    return PowerState(False, UNKNOWN, f"no power reader for {sys.platform}")


def prefetch_switch(vault: Any) -> bool:
    """``figures.enabled`` and ``figures.prefetch_enabled`` as configured on ``vault``."""

    section = getattr(getattr(vault, "config", None), "figures", None)
    return bool(section is not None and section.enabled and getattr(section, "prefetch_enabled", False))


#: What a background build that stopped for the switch or the power says.
SWITCHED_OFF = "Figures ahead of need are switched off (figures.prefetch_enabled)."
NOT_ON_MAINS = "This computer is not on mains power, so figures are not built ahead of need now."


#: What a background build that yielded to the learner's own work says.
YIELDED = "Waiting for what you are doing now to finish (figures ahead of need yield to it)."


def background_hold(vault: Any, *, wait_foreground: float = 0.0) -> str | None:
    """Why a background (prefetch) build may not make its next request now, or None:
    the switch, the power, then foreground work in flight (Codex review F7: a
    prebuild's every request yields to the learner; ``wait_foreground`` seconds
    it may wait for that work to end first, as the durable rich job does)."""

    from learnloop.figures import foreground as FG

    if not prefetch_switch(vault):
        return SWITCHED_OFF
    if not power_state().on_mains:
        return NOT_ON_MAINS
    if FG.busy() and not FG.wait_idle(wait_foreground):
        return YIELDED
    if not prefetch_switch(vault) or not power_state().on_mains:
        return SWITCHED_OFF if not prefetch_switch(vault) else NOT_ON_MAINS
    return None


__all__ = [
    "BATTERY",
    "MAINS",
    "NOT_ON_MAINS",
    "POWER_ENV",
    "POWER_SAVER",
    "PROBE_CACHE_SECONDS",
    "PROBE_TIMEOUT_SECONDS",
    "SWITCHED_OFF",
    "SYSFS_ROOT",
    "UNKNOWN",
    "YIELDED",
    "PowerState",
    "background_hold",
    "linux_power_state",
    "mac_power_state",
    "power_state",
    "prefetch_switch",
    "reset_probe_cache",
    "set_power_reader",
    "windows_power_state",
]
