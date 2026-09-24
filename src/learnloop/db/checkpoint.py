"""Explicit WAL checkpoints after large writes.

SQLite's automatic checkpoint runs a PASSIVE checkpoint when a commit leaves
more than 1000 pages in the ``-wal``.  PASSIVE never waits for readers and
never shrinks the file, so after a burst such as a live rebuild or an ingest
batch the ``-wal`` keeps its peak size.  A TRUNCATE checkpoint after the burst
copies every frame back and truncates the ``-wal`` to zero bytes once no reader
still needs the old frames.

These checkpoints are best effort.  Each runs on its own short-lived
connection, so it never joins a caller's transaction, and waits at most a short
busy timeout for readers and writers.  A busy result is logged rather than
raised: the automatic checkpoint and the next explicit one catch up once the
reader finishes.
"""

from __future__ import annotations

import logging
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from learnloop.db.connection import connect

_LOG = logging.getLogger(__name__)

CHECKPOINT_BUSY_TIMEOUT_MS = 250


@dataclass(frozen=True)
class CheckpointResult:
    """``PRAGMA wal_checkpoint`` output: busy flag, frames in the log, frames copied."""

    busy: bool
    log_frames: int
    checkpointed_frames: int


def checkpoint_wal(
    sqlite_path: Path,
    *,
    reason: str,
    busy_timeout_ms: int = CHECKPOINT_BUSY_TIMEOUT_MS,
) -> CheckpointResult | None:
    """Run ``PRAGMA wal_checkpoint(TRUNCATE)``; ``None`` when it could not run.

    A database that is not in WAL mode reports ``(0, -1, -1)`` and returns
    ``None`` as well, since there is nothing to checkpoint.
    """

    try:
        with closing(connect(Path(sqlite_path))) as connection:
            connection.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")
            busy, log_frames, checkpointed_frames = connection.execute(
                "PRAGMA wal_checkpoint(TRUNCATE)"
            ).fetchone()
    except sqlite3.Error as error:
        _LOG.warning("WAL checkpoint after %s could not run on %s: %s", reason, sqlite_path, error)
        return None
    if log_frames < 0:
        return None
    result = CheckpointResult(
        busy=bool(busy),
        log_frames=int(log_frames),
        checkpointed_frames=int(checkpointed_frames),
    )
    if result.busy:
        _LOG.info(
            "WAL checkpoint after %s on %s was busy: %d of %d frames copied; "
            "a reader or writer still needs the log",
            reason,
            sqlite_path,
            result.checkpointed_frames,
            result.log_frames,
        )
    return result


__all__ = ["CHECKPOINT_BUSY_TIMEOUT_MS", "CheckpointResult", "checkpoint_wal"]
