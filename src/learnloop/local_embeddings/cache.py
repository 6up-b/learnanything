"""The local space's vector cache (spec_local_contextual_retrieval_v1 §4.4, Q11).

``<vault>/.learnloop/vector-cache/<space_id>.sqlite``: derived local state,
outside ``state.sqlite`` (out of snapshots, the table-role registry and the
tracked fixture databases; ``.learnloop/`` is gitignored). A rebuild costs
GPU minutes and no money, so it is a cache, not a paid input.

* Rows are keyed by the window key (``source_retrieval.windows.window_key``):
  reuse by content never applies (the same text in another window is another
  vector), and a stale window is never found.
* Vectors are the worker's int8-valued rows stored as FP16 (exact for values
  in [-127, 127]), ``2 * dims`` bytes like ``embedding_vectors``.
* The resolver opens the file read-only; only the index job writes it. A
  missing or unreadable cache is uncovered (never repaired in place): the
  index job moves a corrupt file aside and rebuilds.
* ``meta`` holds the space's pins and its stored canary vectors.

Copy a cache only through ``learnloop.db.copies`` (the backup API).
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any

import numpy as np

from learnloop.db.connection import connect

CACHE_DIR = (".learnloop", "vector-cache")
_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS vectors ("
    " vector_key TEXT PRIMARY KEY, extraction_id TEXT NOT NULL, span_id TEXT NOT NULL,"
    " dims INTEGER NOT NULL CHECK(dims > 0),"
    " vector BLOB NOT NULL CHECK(typeof(vector) = 'blob' AND length(vector) = 2 * dims),"
    " split_mean INTEGER NOT NULL DEFAULT 0, job_id TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE INDEX IF NOT EXISTS vectors_extraction ON vectors(extraction_id)",
    "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
)


class CacheUnreadable(RuntimeError):
    """The cache file exists but cannot be read as a vector cache."""


def cache_path(vault_root: Path, space_id: str) -> Path:
    if not space_id or "/" in space_id or space_id.startswith("."):
        raise ValueError("a space id names one cache file")
    return Path(vault_root).joinpath(*CACHE_DIR, f"{space_id}.sqlite")


def _blob(vector: Sequence[float] | np.ndarray) -> tuple[int, bytes]:
    array = np.asarray(vector, dtype=np.float64)
    if array.ndim != 1 or not array.size or not np.isfinite(array).all():
        raise ValueError("a cached vector must be a nonempty finite one-dimensional array")
    if np.any(np.abs(array) > np.finfo(np.float16).max):
        raise ValueError("vector exceeds float16 range")
    return int(array.size), array.astype("<f2").tobytes()


class VectorCache:
    """One space's cache file."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    @property
    def exists(self) -> bool:
        return self.path.is_file()

    def _read(self):
        if not self.exists:
            return None
        try:
            connection = connect(self.path, read_only=True)
            connection.execute("SELECT 1 FROM vectors LIMIT 1").fetchall()
        except sqlite3.DatabaseError as exc:
            raise CacheUnreadable(f"the vector cache cannot be read ({type(exc).__name__})") from None
        return connection

    def present(self, keys: Iterable[str]) -> set[str]:
        """Which of ``keys`` have a vector (no vector bytes read)."""

        wanted = sorted(set(keys))
        connection = self._read()
        if connection is None or not wanted:
            return set()
        found: set[str] = set()
        with closing(connection):
            for start in range(0, len(wanted), 500):
                chunk = wanted[start:start + 500]
                found.update(str(row[0]) for row in connection.execute(
                    f"SELECT vector_key FROM vectors WHERE vector_key IN ({', '.join('?' for _ in chunk)})",
                    chunk))
        return found

    def vectors(self, keys: Iterable[str]) -> dict[str, np.ndarray]:
        wanted = sorted(set(keys))
        connection = self._read()
        if connection is None or not wanted:
            return {}
        found: dict[str, np.ndarray] = {}
        with closing(connection):
            for start in range(0, len(wanted), 500):
                chunk = wanted[start:start + 500]
                for key, blob in connection.execute(
                    f"SELECT vector_key, vector FROM vectors WHERE vector_key IN ({', '.join('?' for _ in chunk)})",
                    chunk):
                    found[str(key)] = np.frombuffer(blob, dtype="<f2").astype(np.float64)
        return found

    def meta(self) -> dict[str, Any]:
        connection = self._read()
        if connection is None:
            return {}
        with closing(connection):
            return {str(key): json.loads(value) for key, value in connection.execute("SELECT key, value FROM meta")}

    def report(self) -> dict[str, Any]:
        try:
            connection = self._read()
        except CacheUnreadable as exc:
            return {"status": "unreadable", "reason": str(exc)}
        if connection is None:
            return {"status": "missing", "rows": 0, "extractions": 0}
        with closing(connection):
            rows, extractions = connection.execute(
                "SELECT COUNT(*), COUNT(DISTINCT extraction_id) FROM vectors").fetchone()
        return {"status": "ok", "rows": int(rows), "extractions": int(extractions)}

    # -- writes (the index job only) --------------------------------------------------
    def _writable(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            connection = connect(self.path)
            for statement in _SCHEMA:
                connection.execute(statement)
        except sqlite3.DatabaseError:
            # Never repaired in place: set aside, rebuilt from the model.
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            self.path.replace(self.path.with_name(f"{self.path.name}.corrupt-{stamp}"))
            connection = connect(self.path)
            for statement in _SCHEMA:
                connection.execute(statement)
        return connection

    def write(self, rows: Sequence[Mapping[str, Any]], *, job_id: str,
              meta: Mapping[str, Any] | None = None) -> int:
        """Insert ``{key, extraction_id, span_id, vector, split_mean}`` rows (first write wins)."""

        now = datetime.now(timezone.utc).isoformat()
        with closing(self._writable()) as connection, connection:
            for key, value in (meta or {}).items():
                connection.execute("INSERT INTO meta (key, value) VALUES (?, ?) "
                                   "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                                   (str(key), json.dumps(value, sort_keys=True)))
            written = 0
            for row in rows:
                dims, blob = _blob(row["vector"])
                cursor = connection.execute(
                    "INSERT INTO vectors (vector_key, extraction_id, span_id, dims, vector, split_mean, job_id, "
                    "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(vector_key) DO NOTHING",
                    (str(row["key"]), str(row["extraction_id"]), str(row["span_id"]), dims, blob,
                     1 if row.get("split_mean") else 0, job_id, now))
                written += cursor.rowcount
        return written


__all__ = ["CACHE_DIR", "CacheUnreadable", "VectorCache", "cache_path"]
