"""Application-level coordination for mutating a vault's database schema."""

from __future__ import annotations

import logging
from contextlib import closing
from pathlib import Path

import yaml

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.migrate import Migration, apply_migrations
from learnloop.db.stores.held_out_signals import (
    exam_member_sources,
    pending_unrecorded_sources,
    qualify_unrecorded_signals,
)
from learnloop.vault_lock import DEFAULT_TIMEOUT_S, vault_mutation_lock

_LOG = logging.getLogger(__name__)

#: The vault's source sets, relative to its root (``learnloop.vault.paths.
#: VaultPaths.source_sets_path``; the vault imports this module, so it may not
#: import the vault: pinned equal by a test).
SOURCE_SETS_PATH = Path("sources") / "source_sets.yaml"


def migrate_vault(
    vault_root: Path,
    sqlite_path: Path,
    *,
    migrations_dir: Path | None = None,
    clock: Clock | None = None,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> list[Migration]:
    """Apply migrations while holding the vault's cross-process mutation lock.

    The database path is configurable and may live outside the vault, so callers
    must supply both identities.  Keeping this coordinator above ``db`` avoids a
    persistence-to-domain dependency on the shared vault lock.

    Under the same lock it then records the held-out signals the vault's exam
    membership qualifies (:func:`record_member_exam_signals`).
    """

    with vault_mutation_lock(
        Path(vault_root),
        purpose="database_migrate",
        timeout_s=timeout_s,
    ):
        applied = apply_migrations(
            Path(sqlite_path),
            migrations_dir=migrations_dir,
            clock=clock,
        )
        record_member_exam_signals(Path(vault_root), Path(sqlite_path), clock=clock)
        return applied


def record_member_exam_signals(vault_root: Path, sqlite_path: Path, *, clock: Clock | None = None) -> int:
    """Record as exam material the held-out signals whose role was not
    recorded (migration 225's backfill) on books ``source_sets.yaml`` makes
    exam material now (``db.stores.held_out_signals``; Codex re-review of exam
    protection by extraction identity, F3); the number of rows appended.

    Such a signal protects only while its book is exam material. The vault
    writer records it before a write ends that membership, but a hand edit of
    the file bypasses the writer. So the app records it while the membership
    is known: at the upgrade to 225 and at every later migrate or open. A
    file that cannot be read records nothing here (loading the vault reports
    it)."""

    if not sqlite_path.exists():
        return 0
    with closing(connect(sqlite_path)) as connection:
        pending = pending_unrecorded_sources(connection)
        if not pending:
            return 0
        exam = pending & _exam_member_sources(vault_root / SOURCE_SETS_PATH)
        if not exam:
            return 0
        appended = qualify_unrecorded_signals(connection, exam, created_at=utc_now_iso(clock))
        connection.commit()
        return appended


def _exam_member_sources(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        _LOG.warning("Could not read %s to record its exam material: %s", path, error)
        return set()
    sets = data.get("source_sets") if isinstance(data, dict) else None
    found: set[str] = set()
    for source_set in sets if isinstance(sets, list) else ():
        if isinstance(source_set, dict):
            found |= exam_member_sources(source_set.get("members"))
    return found


__all__ = ["SOURCE_SETS_PATH", "migrate_vault", "record_member_exam_signals"]
