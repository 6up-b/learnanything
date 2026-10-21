"""Guarded AD operations: A8 by construction at the data sources (the AD23 redesign, Option B).

Every AD entry point runs inside ONE operation (:func:`ad_operation`, or the :func:`entry`
decorator). The operation computes the held-out predicate once, and its **epoch**, and yields:

* ``op.vault``: the vault as AD may see it (projected: no withheld item, note, protected-only
  facet, or provenance reference into withheld material);
* ``op.repository``: the same repository, whose document-IR loader drops withheld blocks;
* ``op.view``: the material view, the one place AD's protected tables are read
  (:mod:`~learnloop.adaptive_difficulty.material_view`, its rules in
  :mod:`~learnloop.adaptive_difficulty.protected_tables`);
* ``op.epoch``: a digest of the protected material, which keys every cache and stamps every
  artefact an operation persists (relatedness runs, frozen outside-forecast inputs, preparation).

While an operation is open, every SQLite connection to its database (each one opened in its
context, the repository's pinned connection and any connection the entry point was handed) carries
the AD **guard**, an authorizer:

* a read of a *protected* table is allowed only while the rules execute (``rules()``: the
  material view's readers, whose SQL carries the fixed marker :data:`RULES_MARKER`; when the rules'
  scope closes every guarded connection's statement cache is expired, so nothing prepared inside it
  is reused outside it unchecked);
* a read of a *predicate* table (the predicate's own inputs) is allowed only while the predicate is
  computed; a read of a *denied* table (the incumbent's derived state) is refused, except by the
  named ``mastery_ekf`` carve-out;
* the incumbent's serve-time constraints asked of a visible candidate run in
  :func:`incumbent_constraints`, readable only by the registry's named incumbent readers;
* a write is allowed only to an AD-owned table (with the write's own checks: its foreign keys, its
  WHERE on its own target, the schema's triggers, and a store writer's idempotency read in
  :func:`own_write`);
* the egress (a model request and its send guard's fresh re-reads) leaves the operation
  (:func:`suspended`), and a vault load inside one is refused.

A refused statement raises (``sqlite3.DatabaseError``: "not authorized", or "access to T.C is
prohibited"). AD's fail-closed paths turn that into "AD unavailable for this operation": the
incumbent serves (owner decision 2026-10-21). Each denial is logged beside the database
(``ad_guard_denials.jsonl``) and counted (``learnloop ad report``'s ``guard`` block); no UI notice.

With adaptive difficulty off, no operation opens and nothing here runs.
"""

from __future__ import annotations

import copy
import functools
import hashlib
import inspect
import json
import logging
import sqlite3
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

LOG = logging.getLogger(__name__)

#: The epoch's version: bump it when what the epoch covers changes.
EPOCH_VERSION = "ad_protection_epoch_v1"
#: The marker the rules' SQL carries (and only theirs: linted by ``tests/test_ad_guard.py``).
RULES_MARKER = "/* ad-rules */"

_CURRENT: ContextVar["Operation | None"] = ContextVar("ad_operation", default=None)
_IN_RULES: ContextVar[str | None] = ContextVar("ad_rules", default=None)
_OWN_WRITE: ContextVar[str | None] = ContextVar("ad_own_write", default=None)

_READ = sqlite3.SQLITE_READ
_WRITES = {sqlite3.SQLITE_INSERT: "insert", sqlite3.SQLITE_UPDATE: "update", sqlite3.SQLITE_DELETE: "delete"}


class GuardDenied(RuntimeError):
    """A read or write the AD guard refused inside an operation (A8): AD is unavailable for it."""


@dataclass
class Guard:
    """The operation's SQLite authorizer (see the module docstring)."""

    database: Path
    mode: str = "deny"
    entry: str = ""
    #: table -> the AD-side modules that read it (always recorded; the tests' trace).
    reads: dict[str, set[str]] = field(default_factory=dict)
    writes: dict[str, set[str]] = field(default_factory=dict)
    denials: list[dict[str, Any]] = field(default_factory=list)
    connections: list[Any] = field(default_factory=list)
    #: The schema's trigger names (read at install, before the guard is on).
    triggers: frozenset[str] = frozenset()
    #: The table the statement being authorized writes (its WHERE may read it).
    _writing: str | None = None

    def authorize(self, action: int, arg1: Any, arg2: Any, database: Any, source: Any) -> int:
        op = _CURRENT.get()
        if op is None or op.guard is not self:
            return sqlite3.SQLITE_OK
        if source is not None and str(source) in self.triggers:
            # A trigger's own statements (the schema's integrity checks on a permitted write, such as
            # the judgment ledger's supersession identity): the write that fired it was judged.
            return sqlite3.SQLITE_OK
        if action == _READ:
            if self._writing is not None or str(arg1) == _OWN_WRITE.get():
                # A permitted write's own checks, prepared with it: its foreign keys' parents and its
                # WHERE on its own target (a prune, an update by key). A subquery is a SELECT, which
                # ends the write's region, so what it reads is judged as any read.
                return sqlite3.SQLITE_OK
            return self._read(str(arg1), database)
        if action in _WRITES and arg1:
            verdict = self._write(str(arg1), _WRITES[action])
            self._writing = str(arg1) if verdict == sqlite3.SQLITE_OK else None
            return verdict
        if action != sqlite3.SQLITE_FUNCTION:
            self._writing = None
        return sqlite3.SQLITE_OK

    def _read(self, table: str, database: Any) -> int:
        from learnloop.adaptive_difficulty import protected_tables as T

        reader = _reader()
        self.reads.setdefault(table, set()).add(reader)
        rules = _IN_RULES.get()
        kind = T.role(table)
        if kind == T.NEUTRAL or (rules not in (None, T.INCUMBENT) and kind != T.PREDICATE):
            return sqlite3.SQLITE_OK
        verdict = T.read_verdict(table, rules=rules, reader=reader, stack=_stack_modules())
        if verdict is None:
            return sqlite3.SQLITE_OK
        return self._deny("read", table, verdict, reader)

    def _write(self, table: str, verb: str) -> int:
        from learnloop.adaptive_difficulty import protected_tables as T

        reader = _reader()
        self.writes.setdefault(table, set()).add(reader)
        verdict = T.write_verdict(table)
        if verdict is None:
            return sqlite3.SQLITE_OK
        return self._deny(verb, table, verdict, reader)

    def _deny(self, verb: str, table: str, why: str, reader: str) -> int:
        record = {"verb": verb, "table": table, "why": why, "reader": reader}
        if record not in self.denials:
            self.denials.append(record)
        if self.mode == "observe":
            return sqlite3.SQLITE_OK
        LOG.warning("AD guard denied %s of %s (%s) by %s", verb, table, why, reader)
        return sqlite3.SQLITE_DENY

    def install(self, connection: Any) -> None:
        raw = getattr(connection, "_connection", connection)
        raw = getattr(raw, "_connection", raw)
        if not self.triggers:
            raw.set_authorizer(None)
            try:
                self.triggers = frozenset(str(row[0]) for row in raw.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'trigger'"))
            except sqlite3.DatabaseError:
                self.triggers = frozenset()
        raw.set_authorizer(self.authorize)
        if all(known is not raw for known in self.connections):
            self.connections.append(raw)

    def refresh(self) -> None:
        """Expire every guarded connection's statement cache (by re-installing the authorizer)."""

        alive = []
        for raw in self.connections:
            try:
                raw.set_authorizer(self.authorize)
            except sqlite3.ProgrammingError:  # closed meanwhile
                continue
            alive.append(raw)
        self.connections = alive

    def remove(self, connection: Any) -> None:
        raw = getattr(connection, "_connection", connection)
        raw = getattr(raw, "_connection", raw)
        try:
            raw.set_authorizer(None)
        except sqlite3.ProgrammingError:  # closed meanwhile
            pass


def _entry_name() -> str:
    frame = sys._getframe(2)
    names = []
    while frame is not None and len(names) < 4:
        name = frame.f_globals.get("__name__", "")
        if name.startswith("learnloop") and name != __name__ and "contextlib" not in name:
            names.append(f"{name}.{frame.f_code.co_name}")
        frame = frame.f_back
    return " < ".join(names)


def _stack_modules() -> tuple[str, ...]:
    out = []
    frame = sys._getframe(2)
    while frame is not None:
        name = frame.f_globals.get("__name__", "")
        if name.startswith("learnloop"):
            out.append(name)
        frame = frame.f_back
    return tuple(out)


def _reader() -> str:
    """The innermost LearnLoop module (outside the database layer and this module) on the stack."""

    frame = sys._getframe(3)
    while frame is not None:
        name = frame.f_globals.get("__name__", "")
        if name.startswith("learnloop") and not name.startswith(("learnloop.db", __name__)):
            return name
        frame = frame.f_back
    return "<outside learnloop>"


@dataclass
class Operation:
    """One AD operation (see the module docstring)."""

    vault: Any
    repository: Any
    view: Any
    epoch: str | None
    raw_vault: Any
    raw_repository: Any
    guard: Guard

    @property
    def available(self) -> bool:
        return bool(getattr(self.view, "available", False))


def current() -> Operation | None:
    """The operation open in this context, if any."""

    return _CURRENT.get()


def epoch_of(protection: Any) -> str | None:
    """The protection epoch: a digest of the predicate's version, the held-out extractions and span
    keys, and the reserved exam items. None while the predicate is unavailable."""

    material = getattr(protection, "material", None)
    if material is None:
        return None
    extractions = sorted(str(value) for value in (getattr(material, "extractions", ()) or ()))
    spans = sorted([str(key[0]), str(key[1])] for key in (getattr(material, "spans", ()) or ()))
    reserved = sorted(str(value) for value in (getattr(protection, "reserved", ()) or ()))
    body = json.dumps([EPOCH_VERSION, extractions, spans, reserved], separators=(",", ":"))
    return hashlib.sha256(body.encode()).hexdigest()


@contextmanager
def rules(name: str) -> Iterator[None]:
    """The rules' read scope: protected tables may be read (the rules' own SQL carries
    :data:`RULES_MARKER`). When the outermost scope closes, every guarded connection's statement
    cache is expired (re-installing the authorizer does it, SQLite's fact 1 of the redesign §3.6),
    so no statement a helper prepared inside the rules is reused outside them unchecked."""

    outer = _IN_RULES.get()
    token = _IN_RULES.set(name)
    try:
        yield
    finally:
        _IN_RULES.reset(token)
        if outer is None:
            op = _CURRENT.get()
            if op is not None:
                op.guard.refresh()


@contextmanager
def own_write(table: str) -> Iterator[None]:
    """A store writer's own idempotency read of the AD table it writes (its existence check before
    the insert): allowed for that table only, and only around the writer's call."""

    from learnloop.adaptive_difficulty import protected_tables as T

    if table not in T.AD_WRITABLE:
        raise ValueError(f"{table} is not a table AD writes")
    token = _OWN_WRITE.set(table)
    try:
        yield
    finally:
        _OWN_WRITE.reset(token)


@contextmanager
def incumbent_constraints() -> Iterator[None]:
    """The incumbent's serve-time constraints, asked of a visible candidate inside an operation (the
    slot's routine exclusions and staged-frame admission): read only by the registry's named
    incumbent readers (``protected_tables.INCUMBENT_READERS``), never written. Named, not closed:
    see the registry."""

    with rules("incumbent"):
        yield


@contextmanager
def suspended() -> Iterator[None]:
    """Leave the operation for a deliberate egress (the AD23 redesign): the send guard re-reads the
    predicate afresh at each request by design, and a model call may run the incumbent's own work
    (a reload's maintenance), which never runs inside an operation. While suspended the guard
    allows everything (no operation is current) and no new connection is hooked; at the end its
    authorizer is re-installed on every connection of the operation, which expires their statement
    caches. Outside an operation it does nothing."""

    op = _CURRENT.get()
    if op is None:
        yield
        return
    token = _CURRENT.set(None)
    rules_token = _IN_RULES.set(None)
    from learnloop.vault.loader import vault_loads_forbidden

    try:
        with _no_hook(), vault_loads_forbidden(None):
            yield
    finally:
        _IN_RULES.reset(rules_token)
        _CURRENT.reset(token)
        op.guard.refresh()


@contextmanager
def _no_hook() -> Iterator[None]:
    from learnloop.db.scopes import connection_hook

    with connection_hook(None):
        yield


def _same_database(op: Operation, repository: Any) -> bool:
    try:
        return Path(op.raw_repository.sqlite_path).resolve() == Path(repository.sqlite_path).resolve()
    except (AttributeError, OSError):
        return False


@contextmanager
def ad_operation(vault: Any, repository: Any, *, protected: Any = None, connections: tuple[Any, ...] = (),
                 mode: str | None = None, name: str | None = None) -> Iterator[Operation]:
    """Open (or join) the operation for this database (see the module docstring).

    ``protected``: a :class:`~learnloop.adaptive_difficulty.protection.Protection` or material view an
    enclosing step already computed (never recomputed). ``connections``: connections the entry point
    was handed, opened before the operation, which carry the guard for its duration."""

    from learnloop.db.scopes import connection_hook

    from learnloop.adaptive_difficulty.material_view import MaterialView, detached_view

    existing = _CURRENT.get()
    if existing is not None and _same_database(existing, repository) and (
            protected is None or protected is existing.view or protected is existing.view.protection):
        installed = [connection for connection in connections if connection is not None]
        for connection in installed:
            existing.guard.install(connection)
        yield existing
        return
    raw_vault = getattr(vault, "_ad_raw_vault", vault)
    raw_repository = getattr(repository, "_ad_raw_repository", repository)
    view = protected if isinstance(protected, MaterialView) else detached_view(raw_vault, raw_repository, protected)
    guard = Guard(Path(raw_repository.sqlite_path).resolve(), mode=mode or _default_mode(), entry=name or _entry_name())
    from learnloop.adaptive_difficulty.projection import project_repository, project_vault

    op = Operation(vault=project_vault(view), repository=project_repository(raw_repository, view),
                   view=view, epoch=epoch_of(view.protection), raw_vault=raw_vault, raw_repository=raw_repository,
                   guard=guard)

    def hook(connection: Any, path: Path) -> None:
        if path.resolve() == guard.database:
            guard.install(connection)

    from learnloop.vault.loader import vault_loads_forbidden

    pinned = getattr(getattr(raw_repository, "_pin", None), "connection", None)
    guarded = [c for c in (pinned, *connections) if c is not None]
    token = _CURRENT.set(op)
    try:
        for connection in guarded:
            guard.install(connection)
        # Inside an operation AD reads only its projected vault: a fresh load would bypass it.
        with connection_hook(hook), vault_loads_forbidden("inside an adaptive-difficulty operation"):
            yield op
    finally:
        _CURRENT.reset(token)
        for connection in guarded:
            guard.remove(connection)
        guard.connections = []
        if existing is not None:
            for connection in guarded:
                existing.guard.install(connection)
        _record_denials(op)


#: The guard's mode for new operations: "deny" in production; the tests may observe.
_MODE: dict[str, str] = {"mode": "deny"}


def _default_mode() -> str:
    return _MODE["mode"]


#: Denials of this process, by (verb, table, reader): ``learnloop ad report`` shows them, and they
#: are appended to the vault's guard log (``ad_guard_denials.jsonl``) for a later report.
DENIALS: list[dict[str, Any]] = []


#: The guard's trace hook (the redesign §3.6: SQLite allows one authorizer per connection, so the
#: tests observe the guard's own record instead of installing theirs): each is called with every
#: operation as it closes.
OBSERVERS: list[Callable[[Operation], None]] = []


def _record_denials(op: Operation) -> None:
    for observer in list(OBSERVERS):
        observer(op)
    if not op.guard.denials or op.guard.mode == "observe":
        return
    DENIALS.extend(op.guard.denials)
    try:
        path = denial_log_path(op.raw_repository.sqlite_path)
        with path.open("a", encoding="utf-8") as handle:
            for denial in op.guard.denials:
                handle.write(json.dumps({**denial, "epoch": op.epoch}, sort_keys=True) + "\n")
    except OSError:
        LOG.warning("AD guard denials not logged", exc_info=True)


def denial_log_path(sqlite_path: Any) -> Path:
    """The guard's denial log, beside the vault database."""

    return Path(sqlite_path).with_name("ad_guard_denials.jsonl")


def denial_count(sqlite_path: Any) -> int:
    path = denial_log_path(sqlite_path)
    if not path.exists():
        return 0
    try:
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    except OSError:
        return 0


@contextmanager
def optional_operation(vault: Any, repository: Any) -> Iterator[Operation | None]:
    """The operation, or None with adaptive difficulty off (then nothing opens)."""

    from learnloop.adaptive_difficulty.switches import ad_enabled

    if not ad_enabled(getattr(vault, "config", None)):
        yield None
        return
    with ad_operation(vault, repository) as op:
        yield op


def is_denial(exc: BaseException) -> bool:
    """Whether an exception is the guard's refusal (SQLite's "not authorized" for a statement,
    "access to <table>.<column> is prohibited" for a column read), or an AD reader's refusal to read
    a withheld record it would otherwise reuse (:class:`GuardDenied`)."""

    if isinstance(exc, GuardDenied):
        return True
    text = str(exc)
    return isinstance(exc, sqlite3.DatabaseError) and (
        "not authorized" in text or (text.startswith("access to ") and text.endswith(" is prohibited")))


def entry(func: Callable[..., Any]) -> Callable[..., Any]:
    """Run an AD entry point inside an operation: its ``vault`` and ``repository`` arguments are
    replaced by the operation's, its ``view`` (when it takes one and none was given) by the
    operation's view, and a ``connection`` it was handed carries the guard. With adaptive
    difficulty off (or no vault and repository) the function runs as it is."""

    signature = inspect.signature(func)

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        from learnloop.adaptive_difficulty.switches import ad_enabled

        bound = signature.bind_partial(*args, **kwargs)
        vault, repository = bound.arguments.get("vault"), bound.arguments.get("repository")
        if vault is None or repository is None or not ad_enabled(getattr(vault, "config", None)):
            return func(*args, **kwargs)
        given = bound.arguments.get("view")
        if given is None:
            given = bound.arguments.get("protected")
        handed = tuple(value for name, value in bound.arguments.items()
                       if name == "connection" and value is not None)
        with ad_operation(vault, repository, protected=given if _is_protection(given) else None,
                          connections=handed, name=f"{func.__module__}.{func.__qualname__}") as op:
            bound.arguments["vault"] = op.vault
            bound.arguments["repository"] = op.repository
            if "view" in signature.parameters and bound.arguments.get("view") is None:
                bound.arguments["view"] = op.view
            return func(*bound.args, **bound.kwargs)

    wrapper.__ad_entry__ = True  # type: ignore[attr-defined]
    return wrapper


def _is_protection(value: Any) -> bool:
    from learnloop.adaptive_difficulty.material_view import MaterialView
    from learnloop.adaptive_difficulty.protection import Protection

    return isinstance(value, (MaterialView, Protection))


__all__ = ["EPOCH_VERSION", "GuardDenied", "OBSERVERS", "Operation", "RULES_MARKER", "ad_operation", "current",
           "denial_count", "entry", "epoch_of", "incumbent_constraints", "is_denial", "optional_operation",
           "own_write", "rules", "suspended"]
