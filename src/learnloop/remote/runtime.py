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
  vault's content fingerprint (path, size and mtime of every file the loader
  reads, at most every 2 s) and reloaded when it changed; the database is
  never fingerprinted (WAL), it is read fresh on every connection;
* a consistent snapshot: the desktop writes YAML in place (truncate, then
  write), so a load is kept only when the fingerprint is the same before and
  after it and the source-sets file is not caught empty. A load the files
  keep changing under (after a few tries) is kept marked
  ``learner_context.SNAPSHOT_UNSETTLED`` and looked at again on the next
  request: protection is never read from it (it fails closed).

Writes from this process are telemetry (``remote.telemetry``) and whatever an
existing service already writes when called (``find_sources``' receipts and
spend). SQLite (WAL, ``busy_timeout``) serializes them with the desktop's.
"""

from __future__ import annotations

import hashlib
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
from learnloop.learner_context import SNAPSHOT_UNSETTLED
from learnloop.remote.endpoint_token import read_alias_key
from learnloop.vault.loader import load_vault
from learnloop.vault.models import DoctorIssue, LoadedVault
from learnloop.vault.paths import VaultPaths

#: Seconds a content fingerprint is reused before the vault's files are stat'ed again.
FINGERPRINT_TTL_SECONDS = 2.0
#: Loads tried while the vault's files change under them, and the pause between.
SETTLE_ATTEMPTS = 3
SETTLE_PAUSE_SECONDS = 0.05
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


def content_files(root: Path) -> dict[str, tuple[int, int]]:
    """``{relative path: (size, mtime_ns)}`` for the files the vault loader reads."""

    files: dict[str, tuple[int, int]] = {}
    for directory, subdirectories, names in os.walk(root):
        subdirectories[:] = [name for name in subdirectories if not name.startswith(".") and name not in _SKIP_DIRS]
        for name in names:
            if not name.endswith(_CONTENT_SUFFIXES):
                continue
            path = os.path.join(directory, name)
            try:
                stat = os.stat(path)
            except OSError:
                continue
            files[os.path.relpath(path, root)] = (stat.st_size, stat.st_mtime_ns)
    return files


def _digest(files: dict[str, tuple[int, int]]) -> str:
    text = "\n".join(f"{path}\t{size}\t{mtime}" for path, (size, mtime) in sorted(files.items()))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def vault_content_fingerprint(root: Path) -> str:
    """A digest of path, size and mtime over the files the vault loader reads."""

    return _digest(content_files(root))


@dataclass
class RemoteRuntime:
    """One vault, attached as a secondary process."""

    vault_root: Path
    sqlite_path: Path
    repository: Repository
    load_environment: bool = True
    _vault: LoadedVault | None = field(default=None, repr=False)
    _fingerprint: str | None = field(default=None, repr=False)
    _checked_at: float = field(default=float("-inf"), repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _alias_key: bytes | None = field(default=None, repr=False)
    _alias_checked: bool = field(default=False, repr=False)

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
                files = content_files(self.vault_root)
                fingerprint = _digest(files)
                self._checked_at = now
                if self._vault is None or fingerprint != self._fingerprint:
                    self._vault, self._fingerprint = self._settled_load(files, fingerprint)
                    if self._fingerprint is None:
                        self._checked_at = float("-inf")  # unsettled: look again on the next request
            return self._vault

    def _settled_load(self, files: dict[str, tuple[int, int]], fingerprint: str) -> tuple[LoadedVault, str | None]:
        """A load whose files did not change while it ran, with its fingerprint;
        else the last load, marked unsettled, and no fingerprint."""

        vault: LoadedVault | None = None
        for attempt in range(SETTLE_ATTEMPTS):
            if attempt:
                time.sleep(SETTLE_PAUSE_SECONDS)
            vault = load_vault(self.vault_root, load_environment=self.load_environment)
            after = content_files(self.vault_root)
            if _digest(after) == fingerprint and not self._caught_mid_write(vault, after):
                return vault, fingerprint
            files, fingerprint = after, _digest(after)
        assert vault is not None
        vault.issues.append(DoctorIssue(
            SNAPSHOT_UNSETTLED, "the vault's files were changing while they were read; protection is not read from "
            "this snapshot", None))
        return vault, None

    def _caught_mid_write(self, vault: LoadedVault, files: dict[str, tuple[int, int]]) -> bool:
        """The source-sets file read empty: the desktop truncated it to rewrite it."""

        try:
            relative = os.path.relpath(VaultPaths(self.vault_root, vault.config).source_sets_path, self.vault_root)
        except (OSError, ValueError):
            return True
        found = files.get(relative)
        return found is not None and found[0] == 0

    def read_repository(self) -> Repository:
        """A read-only attach: reads through it can never write."""

        return Repository.attach(self.sqlite_path, read_only=True)

    def alias_key(self) -> bytes | None:
        """The key chat's opaque aliases are made with: the vault's
        (``.learnloop/mcp/alias-key``, made by ``learnloop mcp serve``), or
        None, which keys them for this process (``learner_context``). Read
        once; never written here (attaching and viewing write nothing)."""

        if not self._alias_checked:
            self._alias_key = read_alias_key(self.vault_root)
            self._alias_checked = True
        return self._alias_key

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
    "SETTLE_ATTEMPTS",
    "SchemaMismatch",
    "check_schema",
    "content_files",
    "vault_content_fingerprint",
    "vault_sqlite_path",
]
