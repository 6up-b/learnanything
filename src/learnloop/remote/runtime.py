"""Secondary attach: a second process on a vault the desktop owns (spec_mcp_frontend_c1 §3).

The mobile host's M1 pattern (``learnloop_mobile/host.py``: refuse unless the
schema is exactly this code's, then ``Repository.attach`` with no migration),
extended with the read side of the mobile spec's PR-1 ``load_secondary``:

* the vault's YAML is loaded read-only (``load_vault``); nothing runs that
  ``SidecarContext.load`` runs: no migration, no state sync, no canonical
  projection refresh, no certification scheduling, no startup maintenance, no
  ingest runner and no workers;
* the desktop stays the primary: it migrates, sweeps and grades;
* content freshness: before each request the loaded vault is compared with the
  vault's content fingerprint (file count and newest mtime of the files the
  loader reads, at most every 2 s) and reloaded when it changed; the database
  is never fingerprinted (WAL), it is read fresh on every connection.

Writes from this process are telemetry (``remote.telemetry``) and whatever an
existing service already writes when called (``find_sources``' receipts and
spend). SQLite (WAL, ``busy_timeout``) serializes them with the desktop's.
"""

from __future__ import annotations

import os
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from learnloop.config.loader import load_config
from learnloop.db.migrate import applied_versions, discover_migrations
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths

#: Seconds a content fingerprint is reused before the vault's files are stat'ed again.
FINGERPRINT_TTL_SECONDS = 2.0
#: The files the vault loader reads (YAML, TOML, Markdown); dot-directories
#: (``.learnloop`` machine-local state) and the raw source store are skipped.
_CONTENT_SUFFIXES = (".yaml", ".yml", ".toml", ".md")
_SKIP_DIRS = frozenset({"canonical-sources", "node_modules", "__pycache__"})


class SchemaMismatch(RuntimeError):
    """The vault's schema is not this code's: the desktop (primary) must migrate it.

    The CLI exits 78 (EX_CONFIG) on it, so a supervisor does not restart in a loop."""


def vault_sqlite_path(vault_root: Path) -> Path:
    """The vault's database, from its configuration only (no dotenv, no load)."""

    root = Path(vault_root).resolve()
    config = load_config(root / "learnloop.toml", load_environment=False)
    return VaultPaths(root, config).sqlite_path


def check_schema(sqlite_path: Path, *, vault_root: Path | None = None) -> None:
    """Refuse a database whose applied migrations differ from this code's."""

    path = Path(sqlite_path)
    expected = {migration.version for migration in discover_migrations()}
    try:
        valid = path.is_file() and bool(expected) and applied_versions(path) == expected
    except sqlite3.Error:
        valid = False
    if not valid:
        hint = f" --vault {vault_root}" if vault_root is not None else ""
        raise SchemaMismatch(
            "Schema mismatch: open the desktop app or run `learnloop doctor" + hint + "` once to migrate"
        )


def vault_content_fingerprint(root: Path) -> tuple[int, int]:
    """``(file count, newest mtime_ns)`` over the files the vault loader reads."""

    count = newest = 0
    for directory, subdirectories, files in os.walk(root):
        subdirectories[:] = [name for name in subdirectories if not name.startswith(".") and name not in _SKIP_DIRS]
        for name in files:
            if not name.endswith(_CONTENT_SUFFIXES):
                continue
            try:
                stat = os.stat(os.path.join(directory, name))
            except OSError:
                continue
            count += 1
            newest = max(newest, stat.st_mtime_ns)
    return count, newest


@dataclass
class RemoteRuntime:
    """One vault, attached as a secondary process."""

    vault_root: Path
    sqlite_path: Path
    repository: Repository
    load_environment: bool = True
    _vault: LoadedVault | None = field(default=None, repr=False)
    _fingerprint: tuple[int, int] | None = field(default=None, repr=False)
    _checked_at: float = field(default=float("-inf"), repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @classmethod
    def attach(cls, vault_root: Path | str, *, load_environment: bool = True) -> "RemoteRuntime":
        """Attach without migrating; :class:`SchemaMismatch` unless the schema matches."""

        root = Path(vault_root).expanduser().resolve()
        if not (root / "learnloop.toml").is_file():
            raise SchemaMismatch(f"{root} is not a LearnLoop vault (no learnloop.toml)")
        sqlite_path = vault_sqlite_path(root)
        check_schema(sqlite_path, vault_root=root)
        runtime = cls(vault_root=root, sqlite_path=sqlite_path,
                      repository=Repository.attach(sqlite_path, read_only=False),
                      load_environment=load_environment)
        runtime.vault()
        return runtime

    def vault(self) -> LoadedVault:
        """The loaded vault, reloaded when its files changed (at most every 2 s)."""

        with self._lock:
            now = time.monotonic()
            if self._vault is None or now - self._checked_at >= FINGERPRINT_TTL_SECONDS:
                fingerprint = vault_content_fingerprint(self.vault_root)
                self._checked_at = now
                if self._vault is None or fingerprint != self._fingerprint:
                    self._vault = load_vault(self.vault_root, load_environment=self.load_environment)
                    self._fingerprint = fingerprint
            return self._vault

    def read_repository(self) -> Repository:
        """A read-only attach: reads through it can never write."""

        return Repository.attach(self.sqlite_path, read_only=True)

    def schema_ok(self) -> bool:
        try:
            check_schema(self.sqlite_path)
        except SchemaMismatch:
            return False
        return True

    def describe(self) -> dict[str, Any]:
        return {"vault_root": str(self.vault_root), "attach": "secondary", "migrates": False,
                "startup_work": False}


__all__ = [
    "FINGERPRINT_TTL_SECONDS",
    "RemoteRuntime",
    "SchemaMismatch",
    "check_schema",
    "vault_content_fingerprint",
    "vault_sqlite_path",
]
