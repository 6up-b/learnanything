"""Startup ownership for the canonical projection-version boundary.

The canonical facet tables are a deterministic cache, so desktop startup
refreshes them from the immutable observation ledger.  A projection semantics
change can alter that cache without adding learner evidence; that refresh must
therefore leave one ``derived_state_rebuilds`` marker.  Keeping the marker next
to the startup refresh prevents the cache write and its learner-visible
recalibration contract from drifting apart.

**The fold is skipped when nothing it reads changed** (followups-nov1c B; fix 2 of
the facet-table rewrite investigation, ``docs/reviews/followups-oct31.md``). Every
load and reload used to fold the whole observation ledger even when the facet
writers then wrote nothing (substrate facet write-on-change). The startup refresh
now takes a fingerprint of every input the fold reads *before* reading any of
them, and skips the fold when it equals the fingerprint a previous fold in this
process left behind (:func:`fold_inputs_fingerprint`):

* **The whole database.** ``PRAGMA data_version`` of a read-only watcher
  connection kept open on the vault database (it changes whenever any other
  connection commits, in this process or another) and the watcher's own
  ``total_changes``, with the file's device and inode (a database restored at the
  same path starts over). No list of the tables the fold reads: any committed
  write anywhere forces the next fold, so a table added to the fold later cannot be
  missed. (This is ``daily_plan.reading_choice``'s watcher rule.)
* **The loaded vault.** A digest of exactly the fields of the ``LoadedVault`` the
  fold reads (:data:`FOLD_VAULT_FIELDS`: its root, its whole config, its practice
  items, its default rubrics and its facet aliases); a test runs the fold over a
  vault whose every other field raises on access.
* **The code.** The algorithm version and ``CANONICAL_PROJECTION_VERSION``.

A fingerprint is remembered only when the fold it was taken before committed
nothing at all (the same fingerprint taken again after it): the cache then holds
exactly what that fold computed from exactly those inputs, so a later start with
the same fingerprint would recompute the same rows and write nothing. A fold that
wrote (a new attempt, a projection change, a stamp) is not remembered, and the next
start folds again. Nothing is persisted (an in-process memo): the first start of a
process always folds. A projection-version boundary (no current baseline) always
folds, and stamps as before.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.learner.assessment_contracts import CANONICAL_STATE_VERSIONS
from learnloop.substrate.canonical_projection import (
    CANONICAL_PROJECTION_VERSION,
    project_canonical_facet_state,
)
from learnloop.vault.models import LoadedVault


def refresh_canonical_projection_on_startup(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None = None,
) -> str | None:
    """Refresh the cache and stamp a changed projection baseline exactly once.

    Fresh vaults receive a zero-replay baseline marker.  It is deliberately not
    a learner-visible recalibration, but it prevents the first later restart
    (after the learner has practised under the current projection) from being
    misreported as a version cutover.  Older vaults with observations and no
    current baseline get one marker with the number of observations actually
    folded; subsequent starts still verify the cache but add no marker.

    The marker is written *after* projection succeeds.  If the process stops in
    between, the next startup repeats the idempotent projection and then stamps
    it; it can never claim a rebuild that did not complete.
    """

    algorithm_version = vault.config.algorithms.algorithm_version
    if algorithm_version not in CANONICAL_STATE_VERSIONS:
        return None

    # Startup is allowed to have multiple native callers (initialization,
    # watcher-driven reload, reconnect).  Serialize the check/project/stamp
    # sequence across processes so two simultaneous initializations cannot
    # narrate the same rollout twice.
    from learnloop.vault_lock import vault_mutation_lock

    with vault_mutation_lock(vault.root, purpose="canonical_projection_startup"):
        baseline = repository.latest_canonical_projection_rebuild()
        current = bool(
            baseline is not None
            and baseline.get("algorithm_version") == algorithm_version
            and baseline.get("canonical_projection_version")
            == CANONICAL_PROJECTION_VERSION
        )

        # Taken before the fold reads anything (followups-nov1c B): a write that
        # lands while the fold runs changes the next fingerprint.
        before = fold_inputs_fingerprint(vault, repository) if current else None
        if before is not None and _remembered(repository) == before:
            return None  # nothing the fold reads changed since a fold that wrote nothing
        project_canonical_facet_state(vault, repository, clock=clock)
        if current:
            if before is not None and fold_inputs_fingerprint(vault, repository) == before:
                _remember(repository, before)
            return None

        learning_object_ids = repository.learning_object_ids_with_attempts()
        replayed_attempts = repository.attempt_count()

        # Coverage is an independent displayed-estimate boundary.  Stamp its
        # current content-addressed value on this full projection marker so the
        # review feed never attributes a later coverage change to this rollout.
        from learnloop.learner.facet_diagnostics import (
            coverage_denominator_version,
        )

        return repository.record_derived_state_rebuild(
            scope="canonical_projection_startup",
            learning_object_ids=learning_object_ids,
            algorithm_version=algorithm_version,
            rebuilt_learning_objects=len(learning_object_ids),
            replayed_attempts=replayed_attempts,
            canonical_projection_version=CANONICAL_PROJECTION_VERSION,
            coverage_denominator_version=coverage_denominator_version(
                vault, repository
            ),
            clock=clock,
        )


# -- the fold skip (followups-nov1c B) ----------------------------------------------------------

#: The fields of ``LoadedVault`` the fold reads (``project_canonical_facet_state``
#: and ``project_capability_residuals``, through this refresh). The fingerprint
#: digests each of them whole; ``tests/test_canonical_projection_fold_skip.py``
#: runs the refresh over a vault whose every other field raises on access.
FOLD_VAULT_FIELDS: frozenset[str] = frozenset(
    {"root", "config", "practice_items", "default_rubrics", "facet_aliases"}
)


@dataclass
class _Memo:
    """The database the memo is for, its watcher connection and the fingerprint
    the last fold that wrote nothing was taken with."""

    database: str | None = None
    identity: tuple[int, int] | None = None
    watcher: sqlite3.Connection | None = None
    folded: str | None = None


_MEMO = _Memo()
_MEMO_LOCK = threading.Lock()


def _database(repository: Repository) -> str | None:
    path = getattr(repository, "sqlite_path", None)
    return str(Path(path).resolve()) if path is not None else None


def _identity(database: str) -> tuple[int, int] | None:
    try:
        status = os.stat(database)
    except OSError:
        return None
    return (status.st_dev, status.st_ino)


def _close_locked() -> None:
    if _MEMO.watcher is not None:
        try:
            _MEMO.watcher.close()
        except sqlite3.Error:  # pragma: no cover - closing never fails a refresh
            pass
    _MEMO.database, _MEMO.identity, _MEMO.watcher, _MEMO.folded = None, None, None, None


def _commit_version(database: str) -> tuple[tuple[int, int], int, int] | None:
    """The database's commit version as the watcher sees it: (identity,
    ``data_version``, the watcher's own ``total_changes``), or None when it cannot
    be watched. Another database, or another file at the same path, closes the
    previous watcher and drops its fingerprint."""

    try:
        with _MEMO_LOCK:
            identity = _identity(database)
            if identity is None:
                _close_locked()
                return None
            if _MEMO.database != database or _MEMO.identity != identity or _MEMO.watcher is None:
                _close_locked()
                uri = Path(database).as_uri()
                _MEMO.watcher = sqlite3.connect(f"{uri}?mode=ro", uri=True, check_same_thread=False)
                _MEMO.database, _MEMO.identity = database, identity
            watcher = _MEMO.watcher
            version = int(watcher.execute("PRAGMA data_version").fetchone()[0])
            changes = int(watcher.total_changes)
            if _identity(database) != identity:  # replaced while it was read: never trusted
                _close_locked()
                return None
    except sqlite3.Error:
        with _MEMO_LOCK:
            _close_locked()
        return None
    return identity, version, changes


def _vault_digest(vault: LoadedVault) -> str:
    """One digest over every field of the loaded vault the fold reads
    (:data:`FOLD_VAULT_FIELDS`), each whole."""

    def dump(models: dict[str, Any]) -> dict[str, Any]:
        return {str(key): model.model_dump(mode="json") for key, model in sorted(models.items())}

    payload = {
        "root": str(Path(vault.root).resolve()),
        "config": vault.config.model_dump(mode="json"),
        "practice_items": dump(vault.practice_items),
        "default_rubrics": dump(vault.default_rubrics),
        "facet_aliases": {str(key): str(value) for key, value in sorted(vault.facet_aliases.items())},
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def fold_inputs_fingerprint(vault: LoadedVault, repository: Repository) -> str | None:
    """The fingerprint of every input the canonical fold reads (see the module doc):
    the database's commit version, the vault fields it reads and the code's
    versions. None (never trusted: the fold runs) when the database cannot be
    watched."""

    database = _database(repository)
    if database is None:
        return None
    version = _commit_version(database)
    if version is None:
        return None
    identity, data_version, changes = version
    payload = {
        "database": database, "identity": list(identity), "data_version": data_version,
        "total_changes": changes, "algorithm_version": vault.config.algorithms.algorithm_version,
        "canonical_projection_version": CANONICAL_PROJECTION_VERSION, "vault": _vault_digest(vault),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _remembered(repository: Repository) -> str | None:
    with _MEMO_LOCK:
        return _MEMO.folded if _MEMO.database == _database(repository) else None


def _remember(repository: Repository, fingerprint: str) -> None:
    with _MEMO_LOCK:
        if _MEMO.database == _database(repository):
            _MEMO.folded = fingerprint


def forget_fold_memo() -> None:
    """Drop the remembered fingerprint and close the watcher (a context closing or
    switching vault): the next refresh folds."""

    with _MEMO_LOCK:
        _close_locked()
