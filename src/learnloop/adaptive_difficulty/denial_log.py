"""The AD guard's denial log (``ad_guard_denials.jsonl`` beside the vault database).

Each operation the guard refused something in appends one JSON line per distinct refusal (owner
decision 2026-10-21: logged, counted by ``learnloop ad report``, no UI notice). A line carries the
refusal (``verb``, ``table``, ``why``, ``reader``), the protection ``epoch`` and, since 2026-10-27
(owner decision), ``entry``: the refused operation's entry point (the guard's ``entry``, an
``@entry`` function's qualified name such as ``learnloop.adaptive_difficulty.replay.load_events``,
or the caller chain an unnamed operation was opened from). Lines written before then have no
``entry``; they stay readable and are grouped as :data:`UNRECORDED`.

**Cleared at upgrade (owner decision 2026-10-27).** ``learnloop upgrade --to <version>`` marks the
live log when the command starts (:func:`cutover_mark`: the file's identity and length). When the
upgrade succeeds (once per command, after its final step) the lines the log held at that mark move
to a dated archive beside it, ``ad_guard_denials.archived-<from>-to-<to>-<UTC>.jsonl``; a line
appended after the mark (a sidecar's denial during or after the upgrade) stays live. So ``ad report``
counts the denials recorded since the last upgrade began, and an AD failure under the successor is
never moved out of the count (Codex review F1, 2026-10-27). When nothing was appended since the mark
the archive is the live file renamed (atomic, byte-identical). An archive is never overwritten (a
name already taken gets a counter) and never deleted. A failed or refused upgrade leaves the log
where it is; no log at the mark, nothing to archive; no mark (the command could not take one), no
archive either: without it a successor's denial cannot be told from the marked lines (Codex verify 2
F1), so the log stays live until the next upgrade.

**A failed archival changes nothing (Codex verify 2).** Every write is looped until all its bytes
are down (a short write under ``RLIMIT_FSIZE`` or a full disk is not success). If any step of a
split fails, the live log is left untouched and the partial archive and staging file this archival
created are removed; an archive that already existed is never touched.

**One lock (Codex review F1/F2).** Appends, the mark, the archival and :func:`summary` each run
under an exclusive ``flock`` on ``ad_guard_denials.lock`` beside the log, and an append opens, writes
and closes the live file inside it: no append handle spans an archival, and a report never sees a
line both live and archived. It is a leaf lock: nothing else is acquired while it is held, so it
sits after the vault mutation lock and SQLite's locks in every order. Without ``fcntl`` (non-POSIX)
it degrades to no lock. A report that cannot take the lock gives the live count only and marks the
archive count unavailable (Codex verify 2 F2).

Crash windows (best effort, never a hidden line): a process that dies after the upgrade completed
but before the archival leaves the marked lines live (counted until the next upgrade archives
them); one that dies while splitting a log appended to after the mark (archive written, live file
not yet replaced) leaves the marked lines both archived and live (counted twice until the next
upgrade).

The log is a diagnostic file, not persisted meaning: no migration and no algorithm successor.
"""

from __future__ import annotations

import errno
import json
import os
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:  # POSIX advisory locks, as learnloop.vault_lock.
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX degradation
    fcntl = None  # type: ignore[assignment]

LOG_NAME = "ad_guard_denials.jsonl"
LOCK_NAME = "ad_guard_denials.lock"
_ARCHIVE_PREFIX = "ad_guard_denials.archived-"

#: The group of a line written before the entry was recorded (or one with no entry).
UNRECORDED = "unrecorded"
#: The group of a line that is not a JSON object (a torn append).
UNREADABLE = "unreadable"


def denial_log_path(sqlite_path: Any) -> Path:
    """The guard's denial log, beside the vault database."""

    return Path(sqlite_path).with_name(LOG_NAME)


@contextmanager
def _log_lock(sqlite_path: Any) -> Iterator[None]:
    """The log's leaf lock (see the module docstring). Raises OSError when it cannot be opened."""

    if fcntl is None:  # pragma: no cover - non-POSIX degradation
        yield
        return
    fd = os.open(Path(sqlite_path).with_name(LOCK_NAME), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def append_denials(sqlite_path: Any, denials: Iterable[Mapping[str, Any]], *, epoch: Any,
                   entry: str | None) -> None:
    """Append one line per denial, with the operation's epoch and entry point. Raises OSError.

    Under the log lock, opened and closed inside it. A torn tail (a writer that died mid-line) is
    ended first, so the new lines never join it."""

    text = "".join(json.dumps({**denial, "epoch": epoch, "entry": entry or None}, sort_keys=True) + "\n"
                   for denial in denials)
    if not text:
        return
    path = denial_log_path(sqlite_path)
    with _log_lock(sqlite_path), path.open("ab") as handle:
        if handle.tell() and not _ends_with_newline(path):
            text = "\n" + text
        handle.write(text.encode("utf-8"))


def _ends_with_newline(path: Path) -> bool:
    with path.open("rb") as handle:
        handle.seek(-1, os.SEEK_END)
        return handle.read(1) == b"\n"


def _lines(path: Path) -> list[str]:
    try:
        return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError:
        return []


def denial_count(sqlite_path: Any) -> int:
    """The live log's lines (denials since the last upgrade began); 0 without a log."""

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


def _snapshot(sqlite_path: Any) -> dict[str, Any]:
    lines = _lines(denial_log_path(sqlite_path))
    archives = [{"file": path.name, "denials": len(_lines(path))} for path in archived_logs(sqlite_path)]
    return {"denials": len(lines), "by_entry": dict(sorted(Counter(map(_entry_of, lines)).items())),
            "archived": archives, "archived_denials": sum(a["denials"] for a in archives)}


def summary(sqlite_path: Any) -> dict[str, Any]:
    """``ad report``'s guard block: the live log's count and its count by entry point, and the
    archives' counts (file names and line counts only; a line's content is never shown).

    Read under the log lock, so an archival never lands between the live read and the archive
    listing (Codex review F2). When the lock cannot be taken, the live count alone is given and the
    archives are marked unavailable (``archived``/``archived_denials`` None, ``archived_unavailable``
    the reason): an unlocked pair of reads could count a line both live and archived (Codex verify 2
    F2). The live count is never withheld."""

    try:
        with _log_lock(sqlite_path):
            return _snapshot(sqlite_path)
    except OSError as exc:
        reason = f"the denial log's lock could not be taken ({type(exc).__name__})"
    lines = _lines(denial_log_path(sqlite_path))
    return {"denials": len(lines), "by_entry": dict(sorted(Counter(map(_entry_of, lines)).items())),
            "archived": None, "archived_denials": None, "archived_unavailable": reason}


@dataclass(frozen=True)
class Cutover:
    """The live log as an upgrade command found it: its identity and length (``None``/0: no log)."""

    identity: tuple[int, int] | None
    length: int


def cutover_mark(sqlite_path: Any) -> Cutover:
    """Mark the live log at an upgrade command's start (under the log lock, so the length ends at a
    whole append). Raises OSError."""

    with _log_lock(sqlite_path):
        try:
            stat = os.stat(denial_log_path(sqlite_path))
        except FileNotFoundError:
            return Cutover(identity=None, length=0)
        return Cutover(identity=(stat.st_dev, stat.st_ino), length=stat.st_size)


def _stamp(now: datetime | None) -> str:
    moment = (now or datetime.now(UTC)).astimezone(UTC)
    return moment.strftime("%Y%m%dT%H%M%SZ")


def _safe(version: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ".-_" else "_" for ch in str(version)) or "unknown"


def _remove(path: Path) -> None:
    try:
        os.unlink(path)
    except OSError:  # gone already; or it stays, and its lines are counted twice, never hidden
        pass


def _fsync_write(path: Path, data: bytes, *, exclusive: bool) -> None:
    """Write every byte of ``data`` to ``path`` and fsync it, or raise (Codex verify 2: ``os.write``
    may write a prefix and return its length). A file this call opened is removed on failure: it is
    one it created (``exclusive``) or the archival's own staging file. A failed exclusive open (a
    name already taken) leaves that file alone."""

    flags = os.O_WRONLY | os.O_CREAT | (os.O_EXCL if exclusive else os.O_TRUNC)
    fd = os.open(path, flags, 0o644)
    try:
        try:
            view = memoryview(data)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise OSError(errno.EIO, f"wrote nothing of {len(view)} byte(s)", str(path))
                view = view[written:]
            os.fsync(fd)
        finally:
            os.close(fd)
    except BaseException:
        _remove(path)
        raise


def archive_denial_log(sqlite_path: Any, *, from_version: str, to_version: str, mark: Cutover | None,
                       now: datetime | None = None) -> Path | None:
    """Move the lines the live log held at ``mark`` to a dated archive beside it; None when the mark
    found no log, or the log there now is a later one (another archival moved the marked lines).

    ``mark`` None (the command could not mark the log at its start) archives nothing (Codex verify 2
    F1): the log stays live. Under the log lock: appends wait, and two archivals never pick the same
    name. A taken name gets a counter, so an archive is never overwritten. Raises OSError when the
    archival fails; the live log is then untouched and nothing this call wrote is left behind."""

    if mark is None:
        return None

    live = denial_log_path(sqlite_path)
    with _log_lock(sqlite_path):
        try:
            stat = os.stat(live)
        except FileNotFoundError:
            return None
        if mark.identity != (stat.st_dev, stat.st_ino) or not mark.length:
            return None  # every line here was appended after the command started
        cut = min(mark.length, stat.st_size)
        base = f"{_ARCHIVE_PREFIX}{_safe(from_version)}-to-{_safe(to_version)}-{_stamp(now)}"
        target = live.with_name(base + ".jsonl")
        counter = 1
        while target.exists():
            counter += 1
            target = live.with_name(f"{base}-{counter}.jsonl")
        if cut == stat.st_size:
            os.rename(live, target)
            return target
        data = live.read_bytes()
        head, tail = data[:cut], data[cut:]
        # The marked lines into the archive first, then the later ones as the live log: a crash in
        # between counts the marked lines twice, never hides one. A failure before the replace
        # removes both files written here and leaves the live log as it was.
        _fsync_write(target, head, exclusive=True)
        staged = live.with_name(LOG_NAME + ".tmp")
        try:
            _fsync_write(staged, tail, exclusive=False)
        except BaseException:
            _remove(staged)
            _remove(target)
            raise
        try:
            os.replace(staged, live)
        except BaseException:
            # An interrupt can arrive after the replace committed. The archive is removed only when
            # the live log is provably still the original file; otherwise it holds the only copy of
            # the marked lines.
            try:
                current = os.stat(live)
                untouched = (current.st_dev, current.st_ino) == mark.identity
            except OSError:
                untouched = False
            if untouched:
                _remove(staged)
                _remove(target)
            raise
        return target


__all__ = ["LOCK_NAME", "LOG_NAME", "UNREADABLE", "UNRECORDED", "Cutover", "append_denials", "archive_denial_log",
           "archived_logs", "cutover_mark", "denial_count", "denial_log_path", "summary"]
