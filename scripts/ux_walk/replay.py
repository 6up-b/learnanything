"""Rerun a recorded walk's steps on a new walk (for example the same persona after the UX overhaul).

    python scripts/ux_walk/replay.py <old-walk-dir> <new-walk-name> [--walks-dir ...] [--stop-on-error]

Reads ``<old-walk>/analyst/steps.jsonl`` and sends each step, in order, through
the new walk's own file protocol (exactly what `walk` does). A step that named
an element by its number is sent by the role and name it resolved to, since
numbers belong to one observation; `say` notes are replayed as notes. The new
walk must already be running (start.py). Its observations sit beside the old
ones for comparison.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import walk_client  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WALKS = ROOT / "fixtures-local" / "ux-walks"
_DESCRIBED = re.compile(r'^(?:\[\d+\] )?(\w+) "(.*)"(?: \(.*\))?$')


def replayable(record: dict) -> dict | None:
    """The action to send again, with numbered targets turned into role and name."""

    action = dict(record.get("action") or {})
    if not action or action.get("verb") in (None, "_malformed"):
        return None
    action.pop("seq", None)
    action.pop("written_at", None)
    described = (record.get("detail") or {}).get("target") or ""
    match = _DESCRIBED.match(described)
    for key in ("target", "into", "within"):
        target = action.get(key)
        if isinstance(target, dict) and "number" in target and match:
            action[key] = {"role": match.group(1), "name": match.group(2)}
    return action


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("old_walk", type=Path)
    parser.add_argument("new_walk")
    parser.add_argument("--walks-dir", default=str(DEFAULT_WALKS))
    parser.add_argument("--stop-on-error", action="store_true")
    args = parser.parse_args(argv)
    steps = [json.loads(line) for line in (args.old_walk / "analyst" / "steps.jsonl").read_text(
        encoding="utf-8").splitlines() if line.strip()]
    channel = Path(args.walks_dir).resolve() / args.new_walk / "persona" / "channel"
    if not walk_client.driver_alive(channel):
        raise SystemExit(f"no walk driver is running for {args.new_walk} (start it with start.py)")
    for record in steps:
        action = replayable(record)
        if action is None:
            continue
        seq = walk_client.submit(channel, action)
        result = walk_client.wait_done(channel, seq, walk_client.limit_for(action))
        print(f"{record.get('step')} -> {seq}: {result.get('ok')} {result.get('error') or ''}".rstrip())
        if args.stop_on_error and not result.get("ok"):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
