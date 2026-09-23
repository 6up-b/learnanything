"""Model-call receipts for one CLI command run.

The root command callback installs one observer per command run. Every model
call below it is recorded, including calls made by domain code that resolves
its own provider client. The receipts are owned by ``owner_kind="cli"``, and
the owner id names the command and the run. The observer writes to the vault
the command works on: the repository the command opened, or else the database
of the vault root it resolved. That target is only needed when a model call
starts, so commands that never call a model never open a database for it.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Iterator

import click

from learnloop.ai.execution import observe_model_calls
from learnloop.db.migrate import applied_versions
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths, find_vault_root


CLI_OWNER_KIND = "cli"
# The migration that gives model_call_receipts every column the start write sets.
RECEIPT_SCHEMA_VERSION = 165

_current: ContextVar["CommandReceipts | None"] = ContextVar("cli_command_receipts", default=None)


class CommandReceipts:
    """The receipt store of one command run, bound to its vault on first use."""

    def __init__(self, fallback_label: str) -> None:
        self._fallback_label = fallback_label
        self._run_id = new_ulid()
        self._owner_id: str | None = None
        self._vault_root: Path | None = None
        self._repository: Repository | None = None
        self._recording_unavailable = False

    @property
    def owner_id(self) -> str:
        """``<command path>:<run ulid>``, fixed the first time it is read.

        The root callback runs before the subcommand is parsed, so the full
        command path is read from the subcommand's own context: the first
        vault binding or model call happens inside it.
        """

        if self._owner_id is None:
            self._owner_id = f"{_command_path() or self._fallback_label}:{self._run_id}"
        return self._owner_id

    def bind_vault(self, vault_root: Path) -> None:
        # Binding happens inside the subcommand, so its path is readable now.
        _ = self.owner_id
        if self._vault_root != vault_root:
            self._vault_root = vault_root
            self._repository = None
            self._recording_unavailable = False

    def bind_repository(self, repository: Repository) -> None:
        self._repository = repository

    def record(self, action: str, event: dict[str, Any]) -> None:
        store = self._store()
        if store is None:
            return
        store.record_model_event(action, event, owner_kind=CLI_OWNER_KIND, owner_id=self.owner_id)

    def _store(self) -> Repository | None:
        """The repository to record into, or None when receipts cannot be kept.

        A paid model call must never fail because bookkeeping is unavailable,
        so a database below the receipt schema turns recording off for this
        run, with one notice, instead of failing the call's start write.
        """

        if self._repository is None and not self._recording_unavailable:
            vault_root = self._vault_root or find_vault_root(Path.cwd())
            loaded = load_vault(vault_root)
            sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
            applied = applied_versions(sqlite_path)
            if RECEIPT_SCHEMA_VERSION not in applied:
                self._recording_unavailable = True
                current = max(applied, default=0)
                click.echo(
                    f"learnloop: model calls in this command are not recorded: the vault database is at "
                    f"migration {current} and receipts need {RECEIPT_SCHEMA_VERSION}. "
                    f"Run `learnloop upgrade --vault {loaded.root}`.",
                    err=True,
                )
                return None
            # Attach without migrating: the vault mutation lock that migration
            # takes may already be held by this command.
            self._repository = Repository.attach(sqlite_path)
        return self._repository


@contextmanager
def command_receipts(fallback_label: str) -> Iterator[CommandReceipts]:
    receipts = CommandReceipts(fallback_label)
    token = _current.set(receipts)
    try:
        with observe_model_calls(receipts.record):
            yield receipts
    finally:
        _current.reset(token)


def bind_command_vault(vault_root: Path) -> None:
    receipts = _current.get()
    if receipts is not None:
        receipts.bind_vault(vault_root)


def bind_command_repository(repository: Repository) -> None:
    receipts = _current.get()
    if receipts is not None:
        receipts.bind_repository(repository)


def _command_path() -> str | None:
    """The running subcommand's path below the program name, e.g. ``exam answer``."""

    ctx = click.get_current_context(silent=True)
    if ctx is None or ctx.parent is None:
        return None
    return ctx.command_path.partition(" ")[2] or None
