"""The AD guard's denial log (``ad_guard_denials.jsonl`` beside the vault database).

Each operation the guard refused something in appends one JSON line per distinct refusal (owner
decision 2026-10-21: logged, counted by ``learnloop ad report``, no UI notice). A line carries the
refusal (``verb``, ``table``, ``why``, ``reader``), the protection ``epoch`` and, since 2026-10-27
(owner decision), ``entry``: the refused operation's entry point (the guard's ``entry``, an
``@entry`` function's qualified name such as ``learnloop.adaptive_difficulty.replay.load_events``,
or the caller chain an unnamed operation was opened from). Lines written before then have no
``entry``; they stay readable and are grouped as :data:`UNRECORDED`.

**Cleared at upgrade (owner decision 2026-10-27).** When ``learnloop upgrade --to <version>``
succeeds (once per command, after its final step, journal included, has completed) the live log is
renamed to a dated archive beside it, ``ad_guard_denials.archived-<from>-to-<to>-<UTC>.jsonl``, so
``ad report`` counts only the denials since the last upgrade. The rename is atomic; an archive is
never overwritten (a name already taken gets a counter) and never deleted. A failed or refused
upgrade leaves the log where it is; no log, nothing to archive. A process that dies after the
upgrade completed but before the rename leaves the log live (its lines are still counted until the
next upgrade archives them).

The log is a diagnostic file, not persisted meaning: no migration and no algorithm successor.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

LOG_NAME = "ad_guard_denials.jsonl"
_ARCHIVE_PREFIX = "ad_guard_denials.archived-"

#: The group of a line written before the entry was recorded (or one with no entry).
UNRECORDED = "unrecorded"
#: The group of a line that is not a JSON object (a torn append).
UNREADABLE = "unreadable"


def denial_log_path(sqlite_path: Any) -> Path:
    """The guard's denial log, beside the vault database."""

    return Path(sqlite_path).with_name(LOG_NAME)


def append_denials(sqlite_path: Any, denials: Iterable[Mapping[str, Any]], *, epoch: Any,
                   entry: str | None) -> None:
    """Append one line per denial, with the operation's epoch and entry point. Raises OSError."""

    with denial_log_path(sqlite_path).open("a", encoding="utf-8") as handle:
        for denial in denials:
            handle.write(json.dumps({**denial, "epoch": epoch, "entry": entry or None}, sort_keys=True) + "\n")


def _lines(path: Path) -> list[str]:
    try:
        return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError:
        return []


def denial_count(sqlite_path: Any) -> int:
    """The live log's lines (denials since the last upgrade); 0 without a log."""

    return len(_lines(denial_log_path(sqlite_path)))


def _entry_of(line: str) -> str:
    try:
        record = json.loads(line)
    except ValueError:
        return UNREADABLE
    if not isinstance(record, dict):
        return UNREADABLE
    entry = record.get("entry")
    return entry if isinstance(entry, str) and entry else UNRECORDED


def archived_logs(sqlite_path: Any) -> list[Path]:
    """The archives earlier upgrades left beside the database, oldest name first."""

    live = denial_log_path(sqlite_path)
    try:
        return sorted(path for path in live.parent.glob(_ARCHIVE_PREFIX + "*.jsonl") if path.is_file())
    except OSError:
        return []


def summary(sqlite_path: Any) -> dict[str, Any]:
    """``ad report``'s guard block: the live log's count and its count by entry point, and the
    archives' counts (file names and line counts only; a line's content is never shown)."""

    lines = _lines(denial_log_path(sqlite_path))
    archives = [{"file": path.name, "denials": len(_lines(path))} for path in archived_logs(sqlite_path)]
    return {"denials": len(lines), "by_entry": dict(sorted(Counter(map(_entry_of, lines)).items())),
            "archived": archives, "archived_denials": sum(a["denials"] for a in archives)}


def _stamp(now: datetime | None) -> str:
    moment = (now or datetime.now(UTC)).astimezone(UTC)
    return moment.strftime("%Y%m%dT%H%M%SZ")


def _safe(version: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ".-_" else "_" for ch in str(version)) or "unknown"


def archive_denial_log(sqlite_path: Any, *, from_version: str, to_version: str,
                       now: datetime | None = None) -> Path | None:
    """Rename the live log to a dated archive beside it; None when there is no log.

    Called once a successful upgrade has completed, under the vault mutation lock (so two upgrades
    never pick the same name). The rename is atomic; a taken name gets a counter, so an archive is
    never overwritten."""

    live = denial_log_path(sqlite_path)
    if not live.is_file():
        return None
    base = f"{_ARCHIVE_PREFIX}{_safe(from_version)}-to-{_safe(to_version)}-{_stamp(now)}"
    target = live.with_name(base + ".jsonl")
    counter = 1
    while target.exists():
        counter += 1
        target = live.with_name(f"{base}-{counter}.jsonl")
    os.rename(live, target)
    return target


__all__ = ["LOG_NAME", "UNREADABLE", "UNRECORDED", "append_denials", "archive_denial_log", "archived_logs",
           "denial_count", "denial_log_path", "summary"]
