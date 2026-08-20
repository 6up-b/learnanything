"""Application-level coordination for mutating a vault's database schema."""

from __future__ import annotations

from pathlib import Path

from learnloop.clock import Clock
from learnloop.db.migrate import Migration, apply_migrations
from learnloop.vault_lock import DEFAULT_TIMEOUT_S, vault_mutation_lock


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
    """

    with vault_mutation_lock(
        Path(vault_root),
        purpose="database_migrate",
        timeout_s=timeout_s,
    ):
        return apply_migrations(
            Path(sqlite_path),
            migrations_dir=migrations_dir,
            clock=clock,
        )
