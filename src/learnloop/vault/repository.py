"""Application-level repository opening for a configured vault."""

from __future__ import annotations

from pathlib import Path

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.migration_coordinator import migrate_vault
from learnloop.vault_lock import DEFAULT_TIMEOUT_S


def open_vault_repository(
    vault_root: Path,
    sqlite_path: Path,
    *,
    migrations_dir: Path | None = None,
    clock: Clock | None = None,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> Repository:
    """Migrate and attach a repository under the vault mutation lock.

    Keeping this factory above :mod:`learnloop.db` lets callers provide the
    configured vault identity even when ``state.sqlite`` is relocated outside
    the vault.  ``Repository(Path)`` remains the compatibility constructor for
    path-only callers; application entry points use this factory.
    """

    migrate_vault(
        Path(vault_root),
        Path(sqlite_path),
        migrations_dir=migrations_dir,
        clock=clock,
        timeout_s=timeout_s,
    )
    return Repository.attach(Path(sqlite_path), read_only=False)


__all__ = ["open_vault_repository"]
