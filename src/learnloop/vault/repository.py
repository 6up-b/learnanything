"""Application-level repository opening for a configured vault.

Only the vault's migration coordinator upgrades a vault's database
(``learnloop.migration_coordinator.migrate_vault``): under the vault mutation
lock it applies the migrations, then records the held-out signals the vault's
exam membership qualifies. ``Repository(path)`` knows no vault, so it creates
a database or attaches to a current one and refuses to upgrade one
(``UncoordinatedMigrationError``; exam protection identity, F3 final).

* An entry point (a CLI command, the sidecar, the TUI, a script) opens the
  vault with :func:`open_vault_repository`: every open upgrades and records.
* Code below an entry point that has the vault opens it with
  :func:`vault_repository`: a current database is attached as before, without
  the lock; one that is missing or behind is opened through the coordinator.
* Both first complete an activation a dead process left journalled
  (:func:`complete_interrupted_activation`; LP-min (a), re-review F2), or
  raise, so no entry point serves a half-activated vault. Every other attach
  refuses one (``learnloop.activation_journal``).

``tests/test_coordinated_migrations.py`` pins that nothing else in ``src/``
or ``scripts/`` constructs ``Repository(path)`` or upgrades a database.
"""

from __future__ import annotations

from pathlib import Path

from learnloop import activation_journal
from learnloop.clock import Clock
from learnloop.db.migrate import UncoordinatedMigrationError
from learnloop.db.repositories import Repository
from learnloop.migration_coordinator import migrate_vault
from learnloop.vault.paths import VaultPaths
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
    the vault. Every entry point opens its vault here.
    """

    migrate_vault(
        Path(vault_root),
        Path(sqlite_path),
        migrations_dir=migrations_dir,
        clock=clock,
        timeout_s=timeout_s,
    )
    complete_interrupted_activation(Path(vault_root), Path(sqlite_path))
    return Repository.attach(Path(sqlite_path), read_only=False)


def complete_interrupted_activation(vault_root: Path, sqlite_path: Path) -> None:
    """Complete an activation a dead process left journalled, or raise (LP-min (a), re-review F2).

    A process that died between publishing the claim-fixes successor's config
    and committing its database left the successor's label over the
    predecessor's state, with a journal beside the database. Every opener
    here completes that activation before it attaches, under the vault
    mutation lock, through the completion the process's entry point installed
    (``learnloop.activation_journal``), so no entry point serves the
    half-activated vault. If it cannot complete (or the process installed
    none), :class:`learnloop.activation_journal.InterruptedActivation` is
    raised and nothing is served; the journal stays for the next open or
    ``learnloop upgrade``. Without a journal this is one ``stat``.
    """

    activation_journal.complete(Path(vault_root), Path(sqlite_path))


def vault_repository(paths: VaultPaths) -> Repository:
    """The vault's repository for code below an entry point.

    A database at this code's migrations is attached exactly as
    ``Repository(path)`` attaches it, without taking the vault lock. A missing
    one, or one with migrations pending (a CLI command run first after an
    upgrade of LearnLoop), is opened through the coordinator
    (:func:`open_vault_repository`), so it is upgraded under the lock and what
    the vault's exam membership qualifies is recorded before anything reads it.
    """

    if paths.sqlite_path.exists() and (
        activation_journal.completing() or not activation_journal.pending(paths.sqlite_path)
    ):
        try:
            return Repository(paths.sqlite_path)
        except UncoordinatedMigrationError:
            pass
    # Missing, behind, or an interrupted activation to complete (re-review F2).
    return open_vault_repository(paths.root, paths.sqlite_path)


__all__ = ["complete_interrupted_activation", "open_vault_repository", "vault_repository"]
