"""The driver's side of the file protocol (the persona's side is walk_client.py, copied in as `walk`).

The persona's directory holds ``channel/``: ``walk`` writes
``action-NNNN.json`` (whole, under the next free number); the driver runs the
actions strictly in number order, writes the observation files, then
``done-NNNN.json`` (written aside and renamed, so a reader never sees half of
it), and refreshes ``driver.json`` every second so ``walk`` can tell a slow
step from a driver that is gone.

``VERBS`` names every verb an action file may carry; ``refusal`` says which
cannot be done on which screen (a desktop window has no Back button).
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

#: Every verb `walk` sends, with what it does (walk_client.py's help says the same to the persona).
VERBS: dict[str, str] = {
    "look": "what is on the screen now",
    "click": "click an element by number, label, or role and name",
    "select": "select text as a mouse drag over it does: a phrase, from one phrase to another (--to), "
              "or the whole text of an element",
    "type": "type into the focused field or into --into N; a date or time field takes the date itself",
    "key": "press a key or chord (Enter, Escape, Tab, Control+k)",
    "scroll": "scroll the page or one region",
    "back": "the phone browser's Back (refused on the desktop: the window has no Back button)",
    "hover": "move the pointer over an element",
    "wait": "wait some seconds, or until a text appears",
    "upload": "answer an open file or folder chooser from files/",
    "resize": "resize the window",
    "say": "a note for the record; the app never sees it",
}
DESKTOP_HAS_NO_BACK = ("A desktop window has no Back button. To leave a dialog or panel press Escape (`walk key "
                       "Escape`); to go elsewhere use the app's own controls (its tabs, Close, ←).")


def refusal(verb: str, viewport: str) -> str | None:
    """Why ``verb`` cannot be done on this kind of screen, or None when it can."""

    if verb == "back" and viewport != "phone":
        return DESKTOP_HAS_NO_BACK
    return None


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
