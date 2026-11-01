"""Curriculum C1 (spec_deliverable_curriculum_v1 §7.6): the memo of the plan's fresh reading choice.

C1's invariant (Codex review fix round 2): *while the plan's reading block has no reading
history, the plan's reading is whatever a fresh build would choose right now* (C1's nearest
fresh deliverable, else RW7b's path, else the order, under the current switches and the
current freshness). The engine re-derives that choice on each reconcile of a plan whose
receipt is C1's (``engine._reading_follows_fresh_choice``). Deriving it reads the library,
the coverage, placement and the learner context, so a plain plan read must not redo it on
every call (Codex review fix round 2, Low 6): this module memoizes it on a cheap
**fingerprint** of its inputs, read without a model call.

* **The whole database (fix round 3).** Any committed write to the vault database
  invalidates the memo: the fingerprint holds ``PRAGMA data_version`` of a watcher
  connection this module keeps open on the database (it changes whenever another
  connection commits, in this process or another) and that connection's
  ``total_changes`` (its own writes; it is read-only, so this stays put). No list of the
  tables the choice reads: an input added later, or one a trace never exercised (fix
  round 3's diagnosis and job rows), cannot be missed.
* **Taken before the inputs.** The engine takes the fingerprint before it gathers any input
  of the choice, so a write that lands while the choice is computed changes the *next*
  fingerprint and the choice is computed again; a stale memo entry can never outlive the
  write that made it stale.
* **Time.** What changes the answer with no write is passed in by the engine (``parts``):
  the local and UTC dates, each goal's days left, and the number of diagnosis waits run out
  by placement's own rule (``placement.state.diagnosis_waits_run_out``, fix round 4: the
  live-job filter, the missing-mode default and the strict boundary are placement's code,
  not a copy), so crossing one recomputes exactly when placement's answer can change.
* **One vault object.** An entry also holds a weak reference to the loaded vault it was
  computed for (config, goals, learning objects and source sets are its files; the desktop
  sidecar replaces the object on every reload), so another object never hits.
* **One database, one file.** The memo and its watcher are for the latest database asked
  about; a different database, or another file at the same path (a restore: checked by
  device and inode on every fingerprint), closes the old watcher and starts over, and a
  file that vanished closes it. The sidecar calls :func:`forget` when a context closes or
  switches vault (fix round 4).

No weight, margin or threshold: the memo changes when a choice is computed, never what it
is (a hit returns exactly what the computation returned for the same inputs).
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sqlite3
import threading
import weakref
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Remembered:
    """A memoized choice: the reading (a ``ReadingTarget`` or None) and its path receipt."""

    reading: Any
    receipt: dict[str, Any] | None


@dataclass
class _Entry:
    fingerprint: str
    vault: weakref.ReferenceType[Any]
    reading: Any
    receipt: str | None


_LOCK = threading.Lock()
#: The database the memo is for, its watcher connection and its one entry.
_DATABASE: str | None = None
_IDENTITY: tuple[int, int] | None = None
_WATCHER: sqlite3.Connection | None = None
_ENTRY: _Entry | None = None


def _key(repository: Any) -> str | None:
    path = getattr(repository, "sqlite_path", None)
    return str(Path(path).resolve()) if path is not None else None


def _close_locked() -> None:
    global _DATABASE, _IDENTITY, _WATCHER, _ENTRY
    if _WATCHER is not None:
        try:
            _WATCHER.close()
        except sqlite3.Error:  # pragma: no cover - closing never fails a read
            pass
    _DATABASE, _IDENTITY, _WATCHER, _ENTRY = None, None, None, None


def _watcher_locked(database: str, identity: tuple[int, int]) -> sqlite3.Connection:
    """The watcher on ``database`` (opened read-only on first use; another database, or
    another file at its path, closes the previous one and drops its entry)."""

    global _DATABASE, _WATCHER, _IDENTITY
    if _DATABASE != database or _WATCHER is None or _IDENTITY != identity:
        _close_locked()
        uri = Path(database).as_uri()
        _WATCHER = sqlite3.connect(f"{uri}?mode=ro", uri=True, check_same_thread=False)
        _DATABASE, _IDENTITY = database, identity
    return _WATCHER


def _identity(database: str) -> tuple[int, int] | None:
    """The database file's identity (device, inode); None when it is gone."""

    try:
        status = os.stat(database)
    except OSError:
        return None
    return (status.st_dev, status.st_ino)


def fingerprint(repository: Any, parts: Mapping[str, Any]) -> str | None:
    """The fingerprint of the choice's inputs: the database's commit version as the watcher
    sees it, the watcher's own changes and the caller's ``parts``. None (never trusted) when
    the database cannot be watched. The watcher is checked against the file's identity on
    every call (fix round 4): a database replaced at the same path (a restore) recreates it
    and drops the entry; a file that vanished closes it."""

    database = _key(repository)
    if database is None:
        return None
    try:
        with _LOCK:
            identity = _identity(database)
            if identity is None:
                _close_locked()
                return None
            if _DATABASE == database and _IDENTITY != identity:
                _close_locked()  # another file at the same path: start over
            watcher = _watcher_locked(database, identity)
            version = int(watcher.execute("PRAGMA data_version").fetchone()[0])
            changes = int(watcher.total_changes)
            if _identity(database) != identity:  # replaced while it was read: never trusted
                _close_locked()
                return None
    except sqlite3.Error:
        with _LOCK:
            _close_locked()
        return None
    payload = {"database": database, "identity": list(identity), "data_version": version,
               "total_changes": changes, "parts": parts}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _vault_ref(vault: Any) -> weakref.ReferenceType[Any] | None:
    try:
        return weakref.ref(vault)
    except TypeError:  # an object that takes no weak reference never hits
        return None


def recall(repository: Any, vault: Any, fingerprint_: str) -> Remembered | None:
    """The choice remembered for this database, vault object and fingerprint, else None.
    Copies: a caller may change what it gets without changing the memo."""

    with _LOCK:
        entry = _ENTRY if _DATABASE == _key(repository) else None
    if entry is None or entry.fingerprint != fingerprint_ or entry.vault() is not vault:
        return None
    return Remembered(reading=entry.reading, receipt=json.loads(entry.receipt) if entry.receipt is not None else None)


def remember(repository: Any, vault: Any, fingerprint_: str, reading: Any, receipt: Mapping[str, Any] | None) -> None:
    """Keep the choice computed for this fingerprint (replacing the previous one)."""

    global _ENTRY
    ref = _vault_ref(vault)
    if ref is None:
        return
    entry = _Entry(fingerprint=fingerprint_, vault=ref, reading=copy.copy(reading),
                   receipt=json.dumps(receipt, sort_keys=False) if receipt is not None else None)
    with _LOCK:
        if _DATABASE == _key(repository):
            _ENTRY = entry


def forget() -> None:
    """Drop the memo and close its watcher."""

    with _LOCK:
        _close_locked()


__all__ = ["Remembered", "fingerprint", "forget", "recall", "remember"]
