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
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths, find_vault_root


CLI_OWNER_KIND = "cli"

_current: ContextVar["CommandReceipts | None"] = ContextVar("cli_command_receipts", default=None)


class CommandReceipts:
    """The receipt store of one command run, bound to its vault on first use."""

    def __init__(self, fallback_label: str) -> None:
        self._fallback_label = fallback_label
        self._run_id = new_ulid()
        self._owner_id: str | None = None
        self._vault_root: Path | None = None
        self._repository: Repository | None = None

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

    def bind_repository(self, repository: Repository) -> None:
        self._repository = repository

    def record(self, action: str, event: dict[str, Any]) -> None:
        self._store().record_model_event(action, event, owner_kind=CLI_OWNER_KIND, owner_id=self.owner_id)

    def _store(self) -> Repository:
        if self._repository is None:
            vault_root = self._vault_root or find_vault_root(Path.cwd())
            loaded = load_vault(vault_root)
            # Attach without migrating: the vault mutation lock that migration
            # takes may already be held by this command, and a command that
            # calls a model has opened (and so migrated) the database already.
            self._repository = Repository.attach(VaultPaths(loaded.root, loaded.config).sqlite_path)
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
