"""The driver's side of the file protocol (the persona's side is walk_client.py, copied in as `walk`).

The persona's directory holds ``channel/``: ``walk`` writes
``action-NNNN.json`` (whole, under the next free number); the driver runs the
actions strictly in number order, writes the observation files, then
``done-NNNN.json`` (written aside and renamed, so a reader never sees half of
it), and refreshes ``driver.json`` every second so ``walk`` can tell a slow
step from a driver that is gone.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path


def pending(channel: Path, after: int) -> list[int]:
    """Action numbers above ``after`` that are waiting, lowest first."""

    numbers = []
    for name in os.listdir(channel):
        if name.startswith("action-") and name.endswith(".json"):
            try:
                seq = int(name[len("action-"):-len(".json")])
            except ValueError:
                continue
            if seq > after:
                numbers.append(seq)
    return sorted(numbers)


def next_action(channel: Path, after: int) -> tuple[int, dict] | None:
    """The next action to run: number ``after + 1`` only, so steps never run out of order.

    A later number waiting while ``after + 1`` is missing cannot happen with
    ``walk`` (a number is taken only by the link that writes the whole file);
    it is reported as malformed rather than skipped over."""

    waiting = pending(channel, after)
    if not waiting:
        return None
    seq = after + 1
    path = channel / f"action-{seq:04d}.json"
    if waiting[0] != seq:
        return waiting[0], {"verb": "_malformed", "error": f"step {seq} is missing; step {waiting[0]} is waiting"}
    try:
        return seq, json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return seq, {"verb": "_malformed", "error": f"could not read step {seq}: {exc}"}


def write_done(channel: Path, seq: int, result: dict) -> None:
    temporary = channel / f".done-{seq:04d}.tmp"
    temporary.write_text(json.dumps({"seq": seq, **result}), encoding="utf-8")
    os.replace(temporary, channel / f"done-{seq:04d}.json")


def heartbeat(channel: Path, **fields: object) -> None:
    temporary = channel / ".driver.tmp"
    temporary.write_text(json.dumps({"beat": time.time(), "pid": os.getpid(), **fields}), encoding="utf-8")
    os.replace(temporary, channel / "driver.json")


def last_done(channel: Path) -> int:
    """The highest finished step, so a restarted driver continues after it."""

    numbers = []
    for name in os.listdir(channel):
        if name.startswith("done-") and name.endswith(".json"):
            try:
                numbers.append(int(name[len("done-"):-len(".json")]))
            except ValueError:
                continue
    return max(numbers, default=0)
