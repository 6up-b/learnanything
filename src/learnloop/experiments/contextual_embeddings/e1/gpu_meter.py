"""The E1 GPU-hours meter: <= 4 GPU-hours for ALL of E1 (spec §8, D2).

Every worker process is charged its wall time from spawn to exit (model
loads, failed loads, smoke, profiling and indexing all count; a GPU held is
a GPU-hour spent). The meter is one file-locked JSON under E1's ledger
directory, cumulative across every E1 plan and process:

* ``open`` refuses a new worker when the allowance left is below the
  minimum slot, or when another worker's entry is still open and its
  heartbeat is fresh (no two E1 workers at once).
* ``supervise`` spawns the worker (the orchestrator's OWN child, the only
  process it ever signals), copies the worker's heartbeat into the entry,
  and at the cap sends SIGTERM, then SIGKILL after the grace. The worker
  also carries the deadline itself and exits at it.
* An entry left open by a crashed orchestrator is charged up to its last
  heartbeat plus ``HEARTBEAT_GRACE_S``, never less than its elapsed time
  while that heartbeat stays fresh.
"""
from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from typing import Any
import uuid

from learnloop.experiments.contextual_embeddings.e1 import pins as e1_pins

METER_NAME = "gpu_meter.json"
#: A worker is not started with less than this left (a model load alone takes minutes).
MIN_SLOT_S = 15 * 60.0


class GpuBudgetExceeded(RuntimeError):
    """The GPU-hours allowance cannot admit another worker (nothing started)."""


class GpuMeter:
    def __init__(self, directory: Path, *, cap_hours: float = e1_pins.GPU_HOURS_CAP,
                 grace_s: float = e1_pins.HEARTBEAT_GRACE_S, clock: Callable[[], float] = time.time) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / METER_NAME
        self.lock_path = self.directory / (METER_NAME + ".lock")
        self.cap_s = float(cap_hours) * 3600.0
        self.grace_s = float(grace_s)
        self.clock = clock

    @contextmanager
    def _locked(self) -> Iterator[dict[str, Any]]:
        with open(self.lock_path, "a+") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                state = (json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists()
                         else {"version": 1, "cap_hours": self.cap_s / 3600.0, "entries": {}})
                if float(state.get("cap_hours", 0)) != self.cap_s / 3600.0:
                    raise ValueError("this GPU meter was opened with a different cap")
                yield state
                temporary = self.path.with_name(f".{self.path.name}.{os.getpid()}.tmp")
                with open(temporary, "w", encoding="utf-8") as out:
                    json.dump(state, out, sort_keys=True, indent=1)
                    out.flush()
                    os.fsync(out.fileno())
                os.replace(temporary, self.path)
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _charged(self, entry: dict[str, Any], now: float) -> float:
        started = float(entry["started_at"])
        if entry.get("ended_at") is not None:
            return max(0.0, float(entry["ended_at"]) - started)
        last = float(entry.get("heartbeat_at") or started)
        # Open: everything up to now while the heartbeat is fresh, else up to the
        # last heartbeat plus the grace (a crashed orchestrator still pays).
        return max(0.0, min(now, last + self.grace_s) - started)

    def _fresh(self, entry: dict[str, Any], now: float) -> bool:
        return entry.get("ended_at") is None and now - float(entry.get("heartbeat_at") or entry["started_at"]) \
            < self.grace_s

    def used_s(self) -> float:
        now = self.clock()
        with self._locked() as state:
            return sum(self._charged(entry, now) for entry in state["entries"].values())

    def remaining_s(self) -> float:
        return max(0.0, self.cap_s - self.used_s())

    def open(self, *, plan_id: str, label: str, min_slot_s: float = MIN_SLOT_S) -> tuple[str, float]:
        """A new entry and its deadline (unix seconds); refused when the
        allowance left is below ``min_slot_s`` or another worker is live."""

        now = self.clock()
        with self._locked() as state:
            live = [key for key, entry in state["entries"].items() if self._fresh(entry, now)]
            if live:
                raise GpuBudgetExceeded("another E1 worker is still running (its heartbeat is fresh)")
            used = sum(self._charged(entry, now) for entry in state["entries"].values())
            left = self.cap_s - used
            if left < min_slot_s:
                raise GpuBudgetExceeded(f"{left / 3600:.2f} GPU-hours left of {self.cap_s / 3600:.2f}: "
                                        f"below the {min_slot_s / 60:.0f}-minute minimum slot")
            entry_id = uuid.uuid4().hex
            state["entries"][entry_id] = {"plan_id": plan_id, "label": label, "started_at": now,
                                          "heartbeat_at": now, "ended_at": None, "status": "running"}
        return entry_id, now + left

    def heartbeat(self, entry_id: str, at: float | None = None) -> None:
        with self._locked() as state:
            entry = state["entries"][entry_id]
            if entry.get("ended_at") is None:
                entry["heartbeat_at"] = float(at if at is not None else self.clock())

    def close(self, entry_id: str, *, status: str, returncode: int | None = None) -> float:
        now = self.clock()
        with self._locked() as state:
            entry = state["entries"][entry_id]
            if entry.get("ended_at") is None:
                entry.update(ended_at=now, status=status, returncode=returncode)
            return float(entry["ended_at"]) - float(entry["started_at"])

    def report(self) -> dict[str, Any]:
        now = self.clock()
        with self._locked() as state:
            entries = list(state["entries"].values())
            used = sum(self._charged(entry, now) for entry in entries)
        return {"cap_hours": self.cap_s / 3600.0, "used_hours": round(used / 3600.0, 4),
                "remaining_hours": round(max(0.0, self.cap_s - used) / 3600.0, 4), "processes": len(entries),
                "by_status": {status: sum(1 for entry in entries if entry.get("status") == status)
                              for status in sorted({str(entry.get("status")) for entry in entries})}}


def supervise(command: Sequence[str], *, meter: GpuMeter, plan_id: str, label: str, heartbeat: Path,
              env: dict[str, str] | None = None, popen: Callable[..., Any] = subprocess.Popen,
              poll_s: float = 5.0, sleep: Callable[[float], None] = time.sleep,
              kill_grace_s: float = e1_pins.KILL_GRACE_S, min_slot_s: float = MIN_SLOT_S,
              on_open: Callable[[float], None] | None = None, log: Path | None = None) -> dict[str, Any]:
    """Run one worker under the meter. ``on_open(deadline_unix)`` runs after
    the entry opens and before the spawn (it writes the deadline into the
    job). Returns the return code, the charged seconds and whether the cap
    stopped it."""

    entry_id, deadline = meter.open(plan_id=plan_id, label=label, min_slot_s=min_slot_s)
    if on_open is not None:
        on_open(deadline)
    process = None
    status, stopped_at_cap = "failed_to_start", False
    try:
        # The worker's stdout and stderr go to ``log`` (its traceback, library
        # warnings), else nowhere.
        sink = open(log, "ab") if log is not None else subprocess.DEVNULL  # noqa: SIM115 - closed below
        try:
            process = popen(list(command), env=env, stdout=sink, stderr=sink)
        finally:
            if log is not None:
                sink.close()
        status = "running"
        signalled_at: float | None = None
        while process.poll() is None:
            sleep(poll_s)
            now = meter.clock()
            beat = _read_heartbeat(heartbeat)
            meter.heartbeat(entry_id, max(now, beat or 0.0) if beat else now)
            if now >= deadline and signalled_at is None:
                stopped_at_cap = True
                process.send_signal(signal.SIGTERM)
                signalled_at = now
            elif signalled_at is not None and now - signalled_at >= kill_grace_s and process.poll() is None:
                process.kill()
        status = "stopped_at_cap" if stopped_at_cap else ("exited" if process.returncode == 0 else "failed")
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        charged = meter.close(entry_id, status=status, returncode=None if process is None else process.returncode)
    return {"returncode": None if process is None else process.returncode, "charged_s": round(charged, 3),
            "stopped_at_cap": stopped_at_cap, "status": status, "meter": meter.report()}


def _read_heartbeat(path: Path) -> float | None:
    try:
        return float(json.loads(Path(path).read_text(encoding="utf-8"))["at"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
