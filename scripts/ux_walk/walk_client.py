#!/usr/bin/env python3
"""walk: act on the LearnLoop screen and read what you see. (Files only; no network.)

    walk look                          what is on the screen now
    walk click 7                       click element [7] from the last look
    walk click "Start session"         click what is labelled so (or shows that text)
    walk click --role button "Next"    click a button with that name
    walk type "my answer"              type into the focused field
    walk type "my answer" --into 4 --enter      click field [4], type, press Enter
    walk type "x" --clear              empty the field first
    walk key Enter | Escape | Tab | Shift+Tab | Control+k | ArrowDown
    walk scroll down | up [--page | --lines N] [--in 3]
    walk back                          the browser's back (the desktop window has no back button)
    walk hover 5
    walk wait 3                        wait three seconds, then look
    walk wait --for "Saved" --limit 20 wait until that text appears (at most 20 s)
    walk upload notes.pdf              choose a file from your files/ folder in an open file chooser
    walk upload --folder my-library    choose (or create) a folder in files/ in an open folder chooser
    walk upload --cancel               close the open chooser without choosing
    walk resize 1024 768 | desktop | phone
    walk say "I expected a Save button here"   a note in your words (not sent to the app)

Each step prints what you can now see and saves it under observations/ with a
screenshot (NNNN.png). Numbers like [7] refer to the latest observation only.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHANNEL = HERE / "channel"
HEARTBEAT_STALE_SECONDS = 15.0
DEFAULT_LIMIT = 60.0
MARGIN_SECONDS = 30.0


class WalkError(Exception):
    pass


def _seq_of(name: str) -> int | None:
    stem = name.split(".", 1)[0]
    if not stem.startswith("action-"):
        return None
    try:
        return int(stem[len("action-"):])
    except ValueError:
        return None


def submit(channel: Path, action: dict) -> int:
    """Write one action file under the next free number; returns the number.

    The file appears whole or not at all (written aside, then hard-linked into
    place), and the link fails if another `walk` took the number first, so two
    concurrent steps get two numbers and the driver runs them in order."""

    channel.mkdir(parents=True, exist_ok=True)
    while True:
        taken = [seq for seq in (_seq_of(name) for name in os.listdir(channel)) if seq is not None]
        seq = max(taken, default=0) + 1
        handle, name = tempfile.mkstemp(prefix=".pending-", dir=channel)
        temporary = Path(name)
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(json.dumps({**action, "seq": seq, "written_at": time.time()}))
        try:
            os.link(temporary, channel / f"action-{seq:04d}.json")
            return seq
        except FileExistsError:
            continue
        finally:
            temporary.unlink(missing_ok=True)


def driver_alive(channel: Path, now: float | None = None) -> bool:
    beat = channel / "driver.json"
    try:
        stamp = json.loads(beat.read_text(encoding="utf-8")).get("beat", 0)
    except (OSError, ValueError):
        return False
    return (now if now is not None else time.time()) - float(stamp) < HEARTBEAT_STALE_SECONDS


def wait_done(channel: Path, seq: int, limit: float, poll: float = 0.1) -> dict:
    """The driver's result for action ``seq``; raises WalkError on timeout or a dead driver."""

    done = channel / f"done-{seq:04d}.json"
    deadline = time.monotonic() + limit
    while time.monotonic() < deadline:
        if done.exists():
            try:
                return json.loads(done.read_text(encoding="utf-8"))
            except ValueError:
                pass  # written aside and renamed, so this is a reader racing the rename on another platform
        if not driver_alive(channel):
            raise WalkError("The walk driver is not running (ask whoever started the walk).")
        time.sleep(poll)
    raise WalkError(f"No answer from the screen after {int(limit)} s (step {seq}). Try `walk look`.")


def _take(args: list[str], flag: str) -> str | None:
    if flag in args:
        position = args.index(flag)
        if position + 1 >= len(args):
            raise WalkError(f"{flag} needs a value")
        value = args[position + 1]
        del args[position:position + 2]
        return value
    return None


def _flag(args: list[str], flag: str) -> bool:
    if flag in args:
        args.remove(flag)
        return True
    return False


def _target(args: list[str]) -> dict:
    role = _take(args, "--role")
    if not args:
        raise WalkError("say what to act on: a number from the last look, or its label")
    label = " ".join(args)
    if role:
        return {"role": role, "name": label}
    if label.isdigit():
        return {"number": int(label)}
    return {"text": label}


def parse(argv: list[str]) -> dict:
    if not argv or argv[0] in ("-h", "--help", "help"):
        raise WalkError(__doc__ or "")
    verb, args = argv[0], list(argv[1:])
    if verb == "look":
        return {"verb": "look"}
    if verb in ("click", "hover"):
        return {"verb": verb, "target": _target(args)}
    if verb == "type":
        into = _take(args, "--into")
        enter = _flag(args, "--enter")
        clear = _flag(args, "--clear")
        if not args:
            raise WalkError("type needs the text to type")
        action: dict = {"verb": "type", "text": " ".join(args), "enter": enter, "clear": clear}
        if into is not None:
            action["into"] = _target([into])
        return action
    if verb == "key":
        if len(args) != 1:
            raise WalkError("key needs one key, e.g. Enter, Escape, Tab, Control+k")
        return {"verb": "key", "keys": args[0]}
    if verb == "scroll":
        within = _take(args, "--in")
        lines = _take(args, "--lines")
        page = _flag(args, "--page")
        direction = args[0] if args else "down"
        if direction not in ("up", "down", "left", "right"):
            raise WalkError("scroll up, down, left or right")
        action = {"verb": "scroll", "direction": direction, "amount": "page" if page or not lines else int(lines)}
        if within is not None:
            action["within"] = _target([within])
        return action
    if verb == "back":
        return {"verb": "back"}
    if verb == "wait":
        text = _take(args, "--for")
        limit = _take(args, "--limit")
        if text is not None:
            return {"verb": "wait", "text": text, "limit": float(limit or 15)}
        return {"verb": "wait", "seconds": float(args[0]) if args else 2.0}
    if verb == "upload":
        if _flag(args, "--cancel"):
            return {"verb": "upload", "cancel": True}
        folder = _take(args, "--folder")
        if folder is not None:
            return {"verb": "upload", "folder": folder}
        if not args:
            raise WalkError("upload needs a file name from your files/ folder (or --folder NAME, or --cancel)")
        return {"verb": "upload", "files": args}
    if verb == "resize":
        if len(args) == 1 and args[0] in ("desktop", "phone"):
            return {"verb": "resize", "preset": args[0]}
        if len(args) == 2 and all(arg.isdigit() for arg in args):
            return {"verb": "resize", "width": int(args[0]), "height": int(args[1])}
        raise WalkError("resize WIDTH HEIGHT, or resize desktop|phone")
    if verb == "say":
        if not args:
            raise WalkError("say needs your note")
        return {"verb": "say", "text": " ".join(args)}
    raise WalkError(f"unknown verb {verb!r}; run `walk help`")


def limit_for(action: dict) -> float:
    if action["verb"] == "wait":
        return float(action.get("limit") or action.get("seconds") or 0) + MARGIN_SECONDS
    return DEFAULT_LIMIT + MARGIN_SECONDS


def main(argv: list[str]) -> int:
    try:
        action = parse(argv)
        seq = submit(CHANNEL, action)
        result = wait_done(CHANNEL, seq, limit_for(action))
    except WalkError as exc:
        print(str(exc).strip(), file=sys.stderr)
        return 2
    observation = result.get("observation")
    if observation:
        print((HERE / observation).read_text(encoding="utf-8"), end="")
    if result.get("screenshot"):
        print(f"(screenshot: {result['screenshot']})")
    if not result.get("ok", False):
        print(result.get("error") or "That did not work.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
