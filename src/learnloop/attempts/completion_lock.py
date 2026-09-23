"""Cross-process serialization of post-attempt completion.

Completing an attempt normalizes its misconceptions, which may call a provider,
so it cannot run inside a database transaction. Two processes resuming the same
attempt (a desktop sidecar and a TUI on one vault, or two sidecars) would then
both normalize it and mint duplicate misconceptions. An OS advisory lock next to
the database serializes the whole completion instead: it is released when its
holder exits or dies, so a crashed completion never blocks recovery.
"""

from __future__ import annotations

import errno
import os
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

try:  # POSIX advisory locks; the app targets local-first POSIX hosts.
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX degradation
    fcntl = None  # type: ignore[assignment]

#: Long enough to wait out another process's provider-backed normalization.
COMPLETION_LOCK_TIMEOUT_S = 120.0
_POLL_INTERVAL_S = 0.05

_held = threading.local()


class AttemptCompletionBusy(RuntimeError):
    """Another process kept the completion lock past the timeout."""


def completion_lock_path(sqlite_path: Path) -> Path:
    """One lock per database file, however its path is spelled.

    Relative and absolute spellings, and a symlink to the database file, all
    resolve to the same lock, which is also the per-thread re-entrancy key.
    """

    return Path(sqlite_path).resolve().parent / "attempt-completion.lock"


@contextmanager
def attempt_completion_lock(
    sqlite_path: Path, *, timeout_s: float | None = None
) -> Iterator[None]:
    """Hold the database's completion lock for the block.

    Re-entrant on one thread: a completion that completes another attempt
    (an exam sitting) must not wait on itself.
    """

    if timeout_s is None:
        timeout_s = COMPLETION_LOCK_TIMEOUT_S
    path = completion_lock_path(sqlite_path)
    held_paths: set[Path] = getattr(_held, "paths", set())
    if fcntl is None or path in held_paths:
        yield
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        _acquire(descriptor, path, timeout_s)
        _held.paths = held_paths | {path}
        try:
            yield
        finally:
            _held.paths = held_paths
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


def _acquire(descriptor: int, path: Path, timeout_s: float) -> None:
    deadline = time.monotonic() + max(0.0, timeout_s)
    while True:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except OSError as exc:
            if exc.errno not in (errno.EACCES, errno.EAGAIN):
                raise
            if time.monotonic() >= deadline:
                raise AttemptCompletionBusy(
                    f"Another process is completing an attempt ({path})."
                ) from exc
            time.sleep(_POLL_INTERVAL_S)
