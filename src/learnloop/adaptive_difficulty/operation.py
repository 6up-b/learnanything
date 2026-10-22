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
import re
import sqlite3
import sys
from collections.abc import Callable, Iterator, Mapping
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


class OperationPoisoned(GuardDenied):
    """An operation in which the guard refused something: its output may not be used, whatever
    the code inside did with the refusal."""


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
    #: Per AD-writable table, the tables its declared foreign keys read (parents and children).
    constraints: dict[str, frozenset[str]] = field(default_factory=dict)
    #: Set by the first denial (deny mode): the operation is unavailable from then on (every later
    #: AD read of a non-neutral table and every write is refused, and its exit raises), so a
    #: swallowed refusal can never authorize output (the AD23 redesign round 2, class 6).
    poisoned: bool = False
    #: The table the statement being authorized writes (its WHERE may read it).
    _writing: str | None = None
    #: The one bound authorizer every guarded connection carries. Re-installing it (to expire
    #: prepared statements) from inside its own callback then frees no callable that is running.
    _hook: Any = field(default=None, init=False, repr=False)
    #: SQLite's statement trace, on every guarded connection: it marks each statement's start.
    _trace_hook: Any = field(default=None, init=False, repr=False)
    #: The statement being authorized has an UPDATE action (round 6: a later SELECT in it is an
    #: ``UPDATE ... FROM`` or an ``UPDATE ... SET (subquery)``).
    _update_seen: bool = False

    def __post_init__(self) -> None:
        self._hook = self.authorize
        self._trace_hook = self._statement_started

    def _statement_started(self, sql: Any) -> None:
        """SQLite's trace: a statement began running, after its preparation (round 6). The next
        statement is then prepared with no write context, so the reads its own write's SET
        expressions or subqueries make are judged as reads. A statement with a ``RETURNING`` clause
        (which the authorizer cannot tell from a WHERE) poisons the operation: its rows are never
        output, and in the savepoint form its write rolls back."""

        op = _CURRENT.get()
        if op is None or op.guard is not self:
            return
        self._writing, self._update_seen = None, False
        if _RETURNING_RE.search(_bare_sql(str(sql or ""))):
            self._deny("returning", "(statement)", RETURNING, _reader())

    def authorize(self, action: int, arg1: Any, arg2: Any, database: Any, source: Any) -> int:
        op = _CURRENT.get()
        if op is None or op.guard is not self:
            return sqlite3.SQLITE_OK
        if source is not None and str(source) in self.triggers:
            # A trigger's own statements (the schema's integrity checks on a permitted write, such as
            # the judgment ledger's supersession identity): the write that fired it was judged.
            return sqlite3.SQLITE_OK
        if action == _READ:
            table = str(arg1)
            if self._writing is not None and (
                    table == self._writing or table in self.constraints.get(self._writing, ())):
                # A permitted write's own accesses: its WHERE on its own target (a prune, an update
                # by key) and its declared foreign keys (parents and children). Nothing else: a
                # subquery's read of another table is judged as any read, whatever the callback order.
                return sqlite3.SQLITE_OK
            if table == _OWN_WRITE.get():
                return sqlite3.SQLITE_OK
            return self._read(table, database, None if arg2 is None else str(arg2))
        if action in _WRITES and arg1:
            verdict = self._write(str(arg1), _WRITES[action])
            self._writing = str(arg1) if verdict == sqlite3.SQLITE_OK else None
            if verdict == sqlite3.SQLITE_OK and action == sqlite3.SQLITE_UPDATE:
                self._update_seen = True
            return verdict
        if action == sqlite3.SQLITE_SELECT and self._update_seen:
            # SQLite authorizes an UPDATE's FROM clause and its SET subqueries as a SELECT after the
            # UPDATE action (its WHERE subqueries are plain reads): refused (round 6).
            return self._deny("update", str(self._writing or "?"), UPDATE_SELECT, _reader())
        if action != sqlite3.SQLITE_FUNCTION:
            self._writing = None
        return sqlite3.SQLITE_OK

    def _read(self, table: str, database: Any, column: str | None = None) -> int:
        from learnloop.adaptive_difficulty import column_classes as C
        from learnloop.adaptive_difficulty import protected_tables as T

        reader = _reader()
        self.reads.setdefault(table, set()).add(reader)
        rules = _IN_RULES.get()
        kind = T.role(table)
        # Column-aware (round 5): outside the rules' scopes (the material view's rules, the
        # predicate's, the incumbent's constraints) only a table's metadata columns are read raw; a
        # content column (text, JSON or blob that can carry material) is the rules' to resolve.
        # In the incumbent's scope only its named readers read content (round 6).
        raw_content = (rules is None or (rules == T.INCUMBENT and reader not in T.INCUMBENT_READERS)) \
            and C.column_class(table, column) == C.CONTENT
        if kind == T.NEUTRAL and not raw_content:
            return sqlite3.SQLITE_OK
        if self.poisoned:
            return self._deny("read", table, POISONED, reader)
        if kind == T.NEUTRAL:
            return self._deny("read", table, f"{CONTENT_READ} ({table}.{column})", reader)
        if rules not in (None, T.INCUMBENT) and kind != T.PREDICATE:
            return sqlite3.SQLITE_OK
        verdict = T.read_verdict(table, rules=rules, reader=reader, stack=_stack_modules())
        if verdict is None and raw_content:
            verdict = f"{CONTENT_READ} ({table}.{column})"
        if verdict is None:
            return sqlite3.SQLITE_OK
        return self._deny("read", table, verdict, reader)

    def _write(self, table: str, verb: str) -> int:
        from learnloop.adaptive_difficulty import protected_tables as T

        reader = _reader()
        self.writes.setdefault(table, set()).add(reader)
        if self.poisoned:
            return self._deny(verb, table, POISONED, reader)
        read_only = _READ_ONLY.get()
        if read_only is not None:
            return self._deny(verb, table, f"the read-only AD entry point {read_only} writes nothing", reader)
        verdict = T.write_verdict(table)
        if verdict is None:
            return sqlite3.SQLITE_OK
        return self._deny(verb, table, verdict, reader)

    def _deny(self, verb: str, table: str, why: str, reader: str) -> int:
        record = {"verb": verb, "table": table, "why": why, "reader": reader}
        if record not in self.denials:
            self.denials.append(record)
        self._writing, self._update_seen = None, False
        if self.mode == "observe":
            return sqlite3.SQLITE_OK
        if not self.poisoned:
            LOG.warning("AD guard denied %s of %s (%s) by %s: AD is unavailable for the rest of %s", verb, table,
                        why, reader, self.entry or "this operation")
            self.poisoned = True
            # Every statement prepared before the first denial (an AD insert in SQLite's statement
            # cache) is expired now, so its next run is authorized again and refused as poisoned
            # (the AD23 redesign round 3; the same expiry own_write() and rules() use on exit).
            self.refresh()
        return sqlite3.SQLITE_DENY

    def install(self, connection: Any) -> None:
        raw = getattr(connection, "_connection", connection)
        raw = getattr(raw, "_connection", raw)
        if not self.triggers:
            raw.set_authorizer(None)
            try:
                self.triggers, self.constraints = _schema_facts(raw, self.database)
            except sqlite3.DatabaseError:
                self.triggers, self.constraints = frozenset(), {}
        raw.set_authorizer(self._hook)
        raw.set_trace_callback(self._trace_hook)
        if all(known is not raw for known in self.connections):
            self.connections.append(raw)

    def refresh(self) -> None:
        """Expire every guarded connection's statement cache (by re-installing the authorizer)."""

        alive = []
        for raw in self.connections:
            try:
                raw.set_authorizer(self._hook)
            except sqlite3.ProgrammingError:  # closed meanwhile
                continue
            alive.append(raw)
        self.connections = alive

    def remove(self, connection: Any) -> None:
        raw = getattr(connection, "_connection", connection)
        raw = getattr(raw, "_connection", raw)
        try:
            raw.set_authorizer(None)
            raw.set_trace_callback(None)
        except sqlite3.ProgrammingError:  # closed meanwhile
            pass


#: Why a write statement shape is refused (round 6).
UPDATE_SELECT = "an UPDATE with a FROM clause or a SET subquery"
RETURNING = "a write with a RETURNING clause"
_RETURNING_RE = re.compile(r"\bRETURNING\b", re.IGNORECASE)
_SQL_NOISE_RE = re.compile(r"'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"|`[^`]*`|\[[^\]]*\]|--[^\n]*|/\*.*?\*/", re.DOTALL)


def _bare_sql(sql: str) -> str:
    """A statement without its literals, quoted identifiers and comments."""

    return _SQL_NOISE_RE.sub(" ", sql)


#: Why a raw read of a content column is refused (``column_classes``; round 5).
CONTENT_READ = "a content column read outside the rules"
#: Why a statement is refused after the operation's first denial.
POISONED = "the operation was made unavailable by an earlier denial"

_SCHEMA_FACTS: dict[tuple[str, int], tuple[frozenset[str], dict[str, frozenset[str]]]] = {}


def _schema_facts(raw: Any, database: Path) -> tuple[frozenset[str], dict[str, frozenset[str]]]:
    """The schema's trigger names, and per AD-writable table the tables its declared foreign keys
    read: its parents, and the children whose keys reference it (cached per schema version)."""

    from learnloop.adaptive_difficulty import protected_tables as T

    version = int(raw.execute("PRAGMA schema_version").fetchone()[0])
    key = (str(database), version)
    if key not in _SCHEMA_FACTS:
        triggers = frozenset(str(row[0]) for row in raw.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'"))
        tables = [str(row[0]) for row in raw.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
        parents: dict[str, set[str]] = {}
        for table in tables:
            for row in raw.execute(f"PRAGMA foreign_key_list('{table}')"):
                parents.setdefault(table, set()).add(str(row[2]))
        constraints = {}
        for table in T.AD_WRITABLE:
            children = {child for child, refs in parents.items() if table in refs}
            constraints[table] = frozenset(parents.get(table, set()) | children)
        _SCHEMA_FACTS[key] = (triggers, constraints)
    return _SCHEMA_FACTS[key]


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


def epoch_of(view: Any) -> str | None:
    """The protection epoch of a material view (:meth:`MaterialView.epoch`): a digest of everything
    its projection withholds. None while the predicate is unavailable."""

    from learnloop.adaptive_difficulty.material_view import MaterialView

    if not isinstance(view, MaterialView):
        raise TypeError("the protection epoch is a material view's (it digests what the view withholds)")
    return view.epoch


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
        # A statement prepared in the scope is never reused outside it unchecked (round 2, class 1).
        op = _CURRENT.get()
        if op is not None:
            op.guard.refresh()


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
                 mode: str | None = None, name: str | None = None, savepoint: bool = False,
                 read_only: bool = False) -> Iterator[Operation]:
    """Open (or join) the operation for this database (see the module docstring).

    ``protected``: a :class:`~learnloop.adaptive_difficulty.protection.Protection` or material view an
    enclosing step already computed (never recomputed). ``connections``: connections the entry point
    was handed, opened before the operation, which carry the guard for its duration.

    ``savepoint``: the savepoint form (the AD23 redesign rounds 3 and 4). The repository's savepoint
    (its own ``BEGIN IMMEDIATE`` transaction, or a savepoint of the caller's) is opened OUTSIDE the
    operation, and a poisoned operation raises :class:`OperationPoisoned` inside it, joined or not,
    so every write of the operation rolls back before anything of it is released, whatever the code
    inside did with the refusal and however it returned; the caller's fallback runs after.
    ``read_only``: the block writes nothing (the guard refuses any write in it)."""

    if read_only:
        with _operation(vault, repository, protected=protected, connections=connections, mode=mode,
                        name=name) as op:
            token = _READ_ONLY.set(name or op.guard.entry or "a read-only AD operation")
            try:
                yield op
            finally:
                _READ_ONLY.reset(token)
        return
    if not savepoint:
        with _operation(vault, repository, protected=protected, connections=connections, mode=mode,
                        name=name) as op:
            yield op
        return
    raw_repository = getattr(repository, "_ad_raw_repository", repository)
    with raw_repository.atomic(), _operation(vault, repository, protected=protected, connections=connections,
                                             mode=mode, name=name) as op:
        yield op
        if op.guard.poisoned:
            raise OperationPoisoned(f"the AD guard refused a read or write in {op.guard.entry or 'this operation'}")


@contextmanager
def _operation(vault: Any, repository: Any, *, protected: Any = None, connections: tuple[Any, ...] = (),
               mode: str | None = None, name: str | None = None) -> Iterator[Operation]:

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
                   view=view, epoch=view.epoch, raw_vault=raw_vault, raw_repository=raw_repository,
                   guard=guard)

    def hook(connection: Any, path: Path) -> None:
        if path.resolve() == guard.database:
            guard.install(connection)

    from learnloop.vault.loader import vault_loads_forbidden

    pinned = getattr(getattr(raw_repository, "_pin", None), "connection", None)
    guarded = [c for c in (pinned, *connections) if c is not None]
    token = _CURRENT.set(op)
    failed = False
    try:
        for connection in guarded:
            guard.install(connection)
        # Inside an operation AD reads only its projected vault: a fresh load would bypass it.
        with connection_hook(hook), vault_loads_forbidden("inside an adaptive-difficulty operation"):
            try:
                yield op
            except BaseException:
                failed = True
                raise
    finally:
        _CURRENT.reset(token)
        for connection in guarded:
            guard.remove(connection)
        guard.connections = []
        if existing is not None:
            for connection in guarded:
                existing.guard.install(connection)
        _record_denials(op)
    if guard.poisoned and not failed:
        # A refusal was swallowed inside: the operation's output may not stand (round 2, class 6).
        raise OperationPoisoned(f"the AD guard refused a read or write in {guard.entry or 'this operation'}")


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
def optional_operation(vault: Any, repository: Any, *, savepoint: bool = False,
                       read_only: bool = False) -> Iterator[Operation | None]:
    """The operation, or None with adaptive difficulty off (then nothing opens). ``savepoint`` and
    ``read_only``: as :func:`ad_operation`'s."""

    from learnloop.adaptive_difficulty.switches import ad_enabled

    if not ad_enabled(getattr(vault, "config", None)):
        yield None
        return
    with ad_operation(vault, repository, savepoint=savepoint, read_only=read_only) as op:
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


#: An entry point's write form (round 4): every ``@entry`` declares exactly one.
WRITE_FORMS = ("savepoint", "read_only", "durable")
_READ_ONLY: ContextVar[str | None] = ContextVar("ad_read_only", default=None)


def entry(func: Callable[..., Any] | None = None, *,
          poisoned: Callable[[Mapping[str, Any]], Any] | None = None, savepoint: bool = False,
          read_only: bool = False, durable: str | None = None) -> Any:
    """Run an AD entry point inside an operation: its ``vault`` and ``repository`` arguments are
    replaced by the operation's, its ``view`` (when it takes one and none was given) by the
    operation's view, and a ``connection`` it was handed carries the guard. With adaptive
    difficulty off (or no vault and repository) the function runs as it is.

    An operation the guard refused something in raises :class:`OperationPoisoned` at its exit, and
    the function's own result is discarded. ``poisoned``: for an entry point whose caller must never
    see an exception (the serve hook: logging never breaks the serve), what to return instead,
    built from the call's bound arguments.

    Every entry point declares exactly one write form (the AD23 redesign round 4; a sweep test
    checks every ``@entry``):

    * ``savepoint=True``: an entry point that writes AD decisions or receipts. Its operation is in
      the savepoint form (:func:`ad_operation`): a poisoned operation's writes roll back before
      anything is released, then ``poisoned``'s fallback runs;
    * ``read_only=True``: it writes nothing, and the guard refuses (and so poisons on) any write
      while it runs;
    * ``durable="why"``: an entry point that sends to a model. Its units commit on their own (the
      durable work claim other processes must see, the spend ledger that must record money spent,
      each item's receipt), so one transaction around it would hold the database's write lock
      across network calls and hide its claims. What it committed before the first denial read
      nothing withheld (any such read is that denial); every write after it is refused, and its
      exit raises, so its output is discarded."""

    if func is None:
        return lambda inner: entry(inner, poisoned=poisoned, savepoint=savepoint, read_only=read_only,
                                   durable=durable)
    if sum((bool(savepoint), bool(read_only), durable is not None)) != 1:
        raise TypeError(f"AD entry point {func.__qualname__} must declare exactly one write form {WRITE_FORMS}")
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
        arguments = dict(bound.arguments)
        name = f"{func.__module__}.{func.__qualname__}"
        try:
            with ad_operation(vault, repository, protected=given if _is_protection(given) else None,
                              connections=handed, name=name, savepoint=savepoint) as op:
                bound.arguments["vault"] = op.vault
                bound.arguments["repository"] = op.repository
                if "view" in signature.parameters and bound.arguments.get("view") is None:
                    bound.arguments["view"] = op.view
                token = _READ_ONLY.set(name) if read_only else None
                try:
                    return func(*bound.args, **bound.kwargs)
                finally:
                    if token is not None:
                        _READ_ONLY.reset(token)
        except OperationPoisoned:
            if poisoned is None:
                raise
            return poisoned(arguments)

    wrapper.__ad_entry__ = True  # type: ignore[attr-defined]
    wrapper.__ad_write_form__ = "savepoint" if savepoint else "read_only" if read_only else "durable"  # type: ignore[attr-defined]
    return wrapper


def _is_protection(value: Any) -> bool:
    from learnloop.adaptive_difficulty.material_view import MaterialView
    from learnloop.adaptive_difficulty.protection import Protection

    return isinstance(value, (MaterialView, Protection))


__all__ = ["EPOCH_VERSION", "GuardDenied", "OBSERVERS", "Operation", "OperationPoisoned", "RULES_MARKER", "ad_operation", "current",
           "denial_count", "entry", "epoch_of", "incumbent_constraints", "is_denial", "optional_operation",
           "own_write", "rules", "suspended"]
