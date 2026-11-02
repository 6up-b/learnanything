"""Follow-ups batch 6 (C): the power probe's process starts are bounded.

``figures/power.py`` ``power_state()`` started ``powerprofilesctl get`` on every call (30 process
starts in the RW5d P5 landing smoke: every Reader figures read with prefetch on, and every pass).
The probe's answer now holds for ``PROBE_CACHE_SECONDS`` (``keep``, operational), is dropped at
once when the sysfs power-supply inventory reads differently, and the reading still fails closed.
Each test counts process starts through a fake ``subprocess.run``; no process is started.
"""

from __future__ import annotations

import functools
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from learnloop.figures import power as P
from learnloop.params import parameter_registry as R


class Starts:
    """A fake ``subprocess.run`` that counts the processes it would have started."""

    def __init__(self, stdout: str = "balanced", *, returncode: int = 0, raises: BaseException | None = None,
                 delay_s: float = 0.0) -> None:
        self.argv: list[list[str]] = []
        self.stdout, self.returncode, self.raises, self.delay_s = stdout, returncode, raises, delay_s
        self._lock = threading.Lock()

    def __call__(self, argv, **kwargs):
        with self._lock:
            self.argv.append(list(argv))
        if self.delay_s:
            time.sleep(self.delay_s)
        if self.raises is not None:
            raise self.raises
        return SimpleNamespace(returncode=self.returncode, stdout=self.stdout)

    @property
    def count(self) -> int:
        return len(self.argv)


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def probe(monkeypatch):
    """A counting ``subprocess.run`` behind the real probes, a hand-moved clock, an empty cache."""

    starts = Starts()
    clock = Clock()
    monkeypatch.setattr(P.subprocess, "run", starts)
    monkeypatch.setattr(P.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(P, "_clock", clock, raising=False)  # raising=False: the fail-first run on the old module
    monkeypatch.delenv(P.POWER_ENV, raising=False)
    P.set_power_reader(None)
    yield starts, clock
    getattr(P, "reset_probe_cache", lambda: None)()


def _supply(root: Path, name: str, **files: str) -> None:
    folder = root / name
    folder.mkdir(parents=True, exist_ok=True)
    for key, value in files.items():
        (folder / key).write_text(value + "\n", encoding="utf-8")


def _laptop_on_mains(root: Path) -> Path:
    _supply(root, "BAT0", type="Battery", status="Charging", capacity="80")
    _supply(root, "AC", type="Mains", online="1")
    return root


def test_thirty_reads_start_the_profile_probe_once(tmp_path, probe, monkeypatch):
    starts, _clock = probe
    root = _laptop_on_mains(tmp_path / "ps")
    if sys.platform.startswith("linux"):
        # power_state() itself, as the Reader's figure reads and the prefetch pass call it.
        monkeypatch.setattr(P, "linux_power_state", functools.partial(P.linux_power_state, root))
        readings = [P.power_state() for _ in range(30)]
    else:
        readings = [P.linux_power_state(root) for _ in range(30)]
    assert all(reading.on_mains for reading in readings)
    assert starts.argv == [["/usr/bin/powerprofilesctl", "get"]]


def test_a_power_supply_change_in_sysfs_probes_again_at_once(tmp_path, probe):
    starts, _clock = probe
    root = _laptop_on_mains(tmp_path / "ps")
    assert P.linux_power_state(root).on_mains is True
    # Unplugged: the mains supply goes offline and the battery discharges.
    _supply(root, "AC", online="0")
    _supply(root, "BAT0", status="Discharging")
    reading = P.linux_power_state(root)
    assert (reading.on_mains, reading.reason) == (False, P.BATTERY)
    assert starts.count == 2
    assert P.linux_power_state(root).reason == P.BATTERY and starts.count == 2
    # A battery's capacity is not the condition: it changes all the time and is not read.
    _supply(root, "BAT0", capacity="79")
    P.linux_power_state(root)
    assert starts.count == 2


def test_the_probe_answers_only_for_its_window(tmp_path, probe):
    starts, clock = probe
    root = _laptop_on_mains(tmp_path / "ps")
    P.linux_power_state(root)
    clock.now += P.PROBE_CACHE_SECONDS - 0.5
    P.linux_power_state(root)
    assert starts.count == 1
    clock.now += 1.0
    P.linux_power_state(root)
    assert starts.count == 2
    clock.now -= 10_000.0  # a clock that went back never stretches the window
    P.linux_power_state(root)
    assert starts.count == 3


def test_a_cached_power_saver_profile_keeps_background_work_off(tmp_path, probe):
    starts, clock = probe
    starts.stdout = "power-saver"
    root = _laptop_on_mains(tmp_path / "ps")
    assert [P.linux_power_state(root).reason for _ in range(5)] == [P.POWER_SAVER] * 5
    assert starts.count == 1
    starts.stdout = "balanced"  # the learner leaves power-saver: seen once the window has passed
    clock.now += P.PROBE_CACHE_SECONDS
    assert P.linux_power_state(root).on_mains is True and starts.count == 2


def test_a_failed_probe_is_cached_and_the_reading_still_fails_closed(tmp_path, probe):
    starts, _clock = probe
    # The profile probe timing out: the sysfs reading decides, as before, and the timeout is not
    # waited for again on every call.
    starts.raises = subprocess.TimeoutExpired(["powerprofilesctl", "get"], P.PROBE_TIMEOUT_SECONDS)
    root = tmp_path / "ps"
    _supply(root, "BAT0", type="Battery", status="Discharging")
    assert [P.linux_power_state(root).reason for _ in range(3)] == [P.BATTERY] * 3
    assert starts.count == 1


def test_a_probe_that_raises_is_not_cached_and_reads_as_not_on_mains(tmp_path, probe, monkeypatch):
    starts, _clock = probe
    starts.raises = ValueError("unexpected")
    root = _laptop_on_mains(tmp_path / "ps")
    monkeypatch.setattr(P, "linux_power_state", functools.partial(P.linux_power_state, root))
    monkeypatch.setattr(P.sys, "platform", "linux")
    assert P.power_state().reason == P.UNKNOWN and P.power_state().on_mains is False
    assert starts.count == 2  # nothing kept from a probe that raised
    starts.raises = None
    assert P.power_state().on_mains is True and starts.count == 3


def test_concurrent_reads_share_one_probe(tmp_path, probe):
    starts, _clock = probe
    starts.delay_s = 0.05
    root = _laptop_on_mains(tmp_path / "ps")
    results: list[bool] = []
    threads = [threading.Thread(target=lambda: results.append(P.linux_power_state(root).on_mains)) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)
    assert results == [True] * 8 and starts.count == 1


def test_no_tool_starts_nothing_and_an_injected_profile_is_never_cached(tmp_path, probe, monkeypatch):
    starts, _clock = probe
    root = _laptop_on_mains(tmp_path / "ps")
    calls = []
    for _ in range(3):
        P.linux_power_state(root, profile=lambda: calls.append(1) or "power-saver")
    assert len(calls) == 3 and starts.count == 0
    monkeypatch.setattr(P.shutil, "which", lambda name: None)
    assert P.linux_power_state(root).on_mains is True and starts.count == 0


def test_pmset_is_cached_for_the_window_too(probe):
    starts, clock = probe
    starts.stdout = "Now drawing from 'AC Power'"
    assert [P.mac_power_state().on_mains for _ in range(4)] == [True] * 4
    assert starts.argv == [["pmset", "-g", "batt"]]
    starts.stdout = "Now drawing from 'Battery Power'"
    clock.now += P.PROBE_CACHE_SECONDS
    assert P.mac_power_state().reason == P.BATTERY and starts.count == 2
    # An injected runner is read directly (the existing parsing tests), never cached.
    fake = Starts("Now drawing from 'AC Power'")
    assert P.mac_power_state(fake).on_mains and P.mac_power_state(fake).on_mains and fake.count == 2


def test_installing_a_reader_forgets_the_cached_probes(tmp_path, probe):
    starts, _clock = probe
    root = _laptop_on_mains(tmp_path / "ps")
    P.linux_power_state(root)
    P.set_power_reader(lambda: P.PowerState(True, P.MAINS, "test"))
    P.set_power_reader(None)
    P.linux_power_state(root)
    assert starts.count == 2


def test_the_window_is_a_registered_keep_bound():
    entry = R.REGISTRY["figure_power:PROBE_CACHE_SECONDS"]
    assert entry.param_class == "operational" and entry.kind == "structural" and "keep" in entry.rationale
