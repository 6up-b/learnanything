"""Cross-process vault mutation lock (source-ingestion §8.2).

A single OS-level advisory file lock at ``.learnloop/vault.lock`` serializes the
accept-time critical section — the final lock/target recheck, YAML mutation,
derived-state sync, proposal decision, and any evidence write that could create a
competing lock — across CLI and sidecar. A pre-write fingerprint check WITHOUT
this shared critical section does not close the race; this is the shared section.

Mechanism: ``fcntl.flock`` (advisory, whole-file, released on close/exit and on
process death — so a crashed holder never wedges the vault). The holder's pid and
purpose are written into the file for diagnostics. Acquire is bounded by a
timeout; on contention it raises ``VaultLockTimeout`` rather than blocking
forever.

Nothing of this kind existed before ING M5.
"""

from __future__ import annotations

import errno
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

try:  # POSIX advisory locks. The app targets local-first POSIX hosts.
    import fcntl

    _HAVE_FCNTL = True
except ImportError:  # pragma: no cover - Windows fallback path
    fcntl = None  # type: ignore[assignment]
    _HAVE_FCNTL = False


DEFAULT_TIMEOUT_S = 10.0
_POLL_INTERVAL_S = 0.05


class VaultLockError(RuntimeError):
    """Base class for vault mutation lock failures."""


class VaultLockTimeout(VaultLockError):
    """Raised when the lock could not be acquired within the timeout."""


@dataclass(frozen=True)
class LockHolder:
    pid: int
    purpose: str


def vault_lock_path(root: Path) -> Path:
    return Path(root) / ".learnloop" / "vault.lock"


def read_lock_holder(root: Path) -> LockHolder | None:
    """Best-effort diagnostic read of the current holder metadata.

    The file content is advisory only — it reflects who last acquired the lock and
    may be stale if that holder has since exited. Authoritative mutual exclusion is
    the ``flock`` itself, not this content.
    """

    path = vault_lock_path(root)
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not text:
        return None
    pid_part, _, purpose = text.partition(" ")
    try:
        pid = int(pid_part)
    except ValueError:
        return None
    return LockHolder(pid=pid, purpose=purpose or "unknown")


@contextmanager
def vault_mutation_lock(
    root: Path,
    *,
    purpose: str,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> Iterator[LockHolder]:
    """Acquire the exclusive vault mutation lock for the critical section.

    Usage::

        with vault_mutation_lock(root, purpose="proposal_accept"):
            ...  # lock/target recheck -> YAML mutation -> sync -> decision

    Raises ``VaultLockTimeout`` if another process holds the lock past
    ``timeout_s``. On POSIX the lock is released automatically if this process
    dies, so a crash mid-section never wedges the vault (crash *consistency* is
    the write-ahead protocol's job; this only closes the race).
    """

    path = vault_lock_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    holder = LockHolder(pid=os.getpid(), purpose=purpose)

    if not _HAVE_FCNTL:  # pragma: no cover - non-POSIX degradation
        # Without OS advisory locks the shared critical section cannot be
        # guaranteed; single-process use still works, and the holder file records
        # intent for diagnostics.
        _write_holder(path, holder)
        try:
            yield holder
        finally:
            _clear_holder(path)
        return

    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        _acquire_with_timeout(fd, path, timeout_s)
        _write_holder_fd(fd, holder)
        try:
            yield holder
        finally:
            # Blank the holder metadata before releasing so a later diagnostic
            # read does not attribute the lock to a process no longer holding it.
            try:
                os.ftruncate(fd, 0)
            except OSError:
                pass
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
    finally:
        os.close(fd)


def _acquire_with_timeout(fd: int, path: Path, timeout_s: float) -> None:
    deadline = time.monotonic() + max(0.0, timeout_s)
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except OSError as exc:
            if exc.errno not in (errno.EACCES, errno.EAGAIN):
                raise
            if time.monotonic() >= deadline:
                current = read_lock_holder(path)
                held_by = (
                    f" held by pid {current.pid} ({current.purpose})"
                    if current is not None
                    else ""
                )
                raise VaultLockTimeout(
                    f"Could not acquire vault mutation lock at {path} within "
                    f"{timeout_s:.1f}s{held_by}"
                ) from exc
            time.sleep(_POLL_INTERVAL_S)


def _write_holder_fd(fd: int, holder: LockHolder) -> None:
    os.ftruncate(fd, 0)
    os.lseek(fd, 0, os.SEEK_SET)
    os.write(fd, f"{holder.pid} {holder.purpose}".encode("utf-8"))
    os.fsync(fd)


def _write_holder(path: Path, holder: LockHolder) -> None:
    path.write_text(f"{holder.pid} {holder.purpose}", encoding="utf-8")


def _clear_holder(path: Path) -> None:
    try:
        path.write_text("", encoding="utf-8")
    except OSError:
        pass
