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
  :func:`incumbent_constraints`, whose readers are every LearnLoop module reached inside it but
  AD's own (``protected_tables.incumbent_reader``), and from which only verdicts leave;
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
import os
import re
import sqlite3
import sys
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from types import MappingProxyType
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
    constraints: dict[str, frozenset[tuple[str, str]]] = field(default_factory=dict)
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
    #: The incumbent scope's last stack verdict: (statement site frame, its instruction, the scope's
    #: entry frame, the verdict); cleared when the scope closes.
    _scope_cache: Any = field(default=None, init=False, repr=False)

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
            if self._writing is not None and self._write_access(table, None if arg2 is None else str(arg2)):
                # A permitted write's own accesses: its WHERE on its own target's metadata (a prune,
                # an update by key) and its declared foreign keys' key columns (round 7). Nothing
                # else: a subquery's read of another table, or of any other column, is judged as a
                # read, whatever the callback order.
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

    def _write_access(self, table: str, column: str | None) -> bool:
        from learnloop.adaptive_difficulty import column_classes as C

        if (table, str(column or "")) in self.constraints.get(str(self._writing), ()):
            return True
        return table == self._writing and C.column_class(table, column) == C.METADATA

    def _read(self, table: str, database: Any, column: str | None = None) -> int:
        from learnloop.adaptive_difficulty import column_classes as C
        from learnloop.adaptive_difficulty import protected_tables as T

        reader = _reader()
        self.reads.setdefault(table, set()).add(reader)
        rules = _IN_RULES.get()
        kind = T.role(table)
        if rules == T.INCUMBENT:
            # The incumbent's scope (the compose fix rounds 2 and 3): entered only by
            # :func:`incumbent_answer`, it runs one registered incumbent question over plain data.
            # Its readers are derived (every LearnLoop module but AD's own), and a read is allowed
            # only while no AD frame and no callback from outside LearnLoop lies between the read
            # and the scope's entry (:meth:`_scope_violation`): AD code run inside the scope (a
            # callback, lambda, method or generator) is refused and poisons the operation.
            if self.poisoned:
                return self._deny("read", table, POISONED, reader)
            violation = self._scope_violation()
            if violation is not None:
                return self._deny("read", table, violation, reader)
            return sqlite3.SQLITE_OK
        # Column-aware (round 5): outside the rules' scopes (the material view's rules, the
        # predicate's, the incumbent's constraints) only a table's metadata columns are read raw; a
        # content column (text, JSON or blob that can carry material) is the rules' to resolve.
        # In the incumbent's scope only its named readers read content (round 6).
        raw_content = rules is None and C.column_class(table, column) == C.CONTENT
        # A column derived from other rows (``protected_tables.DERIVED``; round 7) is read only where
        # it is derived again from visible rows (the projection's ``rules("derive")``), by the
        # predicate, or by the incumbent's named readers; the rules never hand it out.
        derived = T.COLUMNS.get(table, {}).get(str(column or "")) == T.DERIVED and rules not in (
            DERIVE, "predicate")
        if kind == T.NEUTRAL and not raw_content:
            return sqlite3.SQLITE_OK
        if self.poisoned:
            return self._deny("read", table, POISONED, reader)
        if kind is None:
            # An unclassified table is refused in every scope, the rules' included (round 8, F4):
            # nothing reads what the registry has not judged.
            return self._deny("read", table, "an unclassified table", reader)
        if derived:
            return self._deny("read", table, f"{DERIVED_READ} ({table}.{column})", reader)
        if kind == T.NEUTRAL:
            return self._deny("read", table, f"{CONTENT_READ} ({table}.{column})", reader)
        if rules is not None and kind != T.PREDICATE:
            return sqlite3.SQLITE_OK
        verdict = T.read_verdict(table, rules=rules, reader=reader, stack=_stack_modules())
        if verdict is None and raw_content:
            verdict = f"{CONTENT_READ} ({table}.{column})"
        if verdict is None:
            return sqlite3.SQLITE_OK
        return self._deny("read", table, verdict, reader)

    def _scope_violation(self) -> str | None:
        """Why a read in the incumbent's scope may not run, or None: the frames between it and the
        scope's entry (:func:`incumbent_answer`'s own frame) must all be incumbent code, LearnLoop
        modules outside AD or the Python installation's own (the standard library, installed
        packages); an AD frame or a frame from anywhere else (a test's or a planted callback) is
        refused. Cached per statement site (the frame that prepared it and its instruction)."""

        entry = _SCOPE_ENTRY.get()
        if entry is None:
            return "a read in the incumbent's scope with no entry"
        frame = sys._getframe(2)
        while frame is not None and frame.f_globals.get("__name__") == __name__:
            frame = frame.f_back
        if frame is None:
            return "a read in the incumbent's scope outside its entry"
        cached = self._scope_cache
        if cached is not None and cached[0] is frame and cached[1] == frame.f_lasti and cached[2] is entry:
            return cached[3]
        site, lasti = frame, frame.f_lasti
        verdict: str | None = "a read in the incumbent's scope outside its entry"
        while frame is not None:
            if frame is entry:
                verdict = None
                break
            name = str(frame.f_globals.get("__name__", ""))
            where = f"{name}.{frame.f_code.co_name}"
            if _ad_owned(name):
                verdict = f"AD code inside the incumbent's scope ({where})"
                break
            if not _trusted_frame(name, frame.f_code.co_filename):
                verdict = f"a callback from outside LearnLoop inside the incumbent's scope ({where})"
                break
            frame = frame.f_back
        self._scope_cache = (site, lasti, entry, verdict)
        return verdict

    def _write(self, table: str, verb: str) -> int:
        from learnloop.adaptive_difficulty import protected_tables as T

        reader = _reader()
        self.writes.setdefault(table, set()).add(reader)
        if self.poisoned:
            return self._deny(verb, table, POISONED, reader)
        if _IN_RULES.get() == T.INCUMBENT:
            # The incumbent's scope writes nothing, AD's own tables included (the compose fix round 3).
            return self._deny(verb, table, "a write inside the incumbent's scope", reader)
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


#: The derivation scope (round 7): the projection reads a derived column only to derive it again.
DERIVE = "derive"
DERIVED_READ = "a column derived from other rows read outside its derivation"
#: Why a raw read of a content column is refused (``column_classes``; round 5).
CONTENT_READ = "a content column read outside the rules"
#: Why a statement is refused after the operation's first denial.
POISONED = "the operation was made unavailable by an earlier denial"

_SCHEMA_FACTS: dict[tuple[str, int], tuple[frozenset[str], dict[str, frozenset[tuple[str, str]]]]] = {}


def _schema_facts(raw: Any, database: Path) -> tuple[frozenset[str], dict[str, frozenset[tuple[str, str]]]]:
    """The schema's trigger names, and per AD-writable table the KEY COLUMNS its declared foreign
    keys read, as ``(table, column)``: its parents' referenced keys, and the children's referencing
    columns (cached per schema version). Round 7: only these, never a child's other columns, so a
    DELETE's WHERE subquery reading a referencing table by anything but its key is judged as a read."""

    from learnloop.adaptive_difficulty import protected_tables as T

    version = int(raw.execute("PRAGMA schema_version").fetchone()[0])
    key = (str(database), version)
    if key not in _SCHEMA_FACTS:
        triggers = frozenset(str(row[0]) for row in raw.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'"))
        tables = [str(row[0]) for row in raw.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
        def primary_key(table: str) -> list[str]:
            return [str(row[1]) for row in raw.execute(f"PRAGMA table_info('{table}')") if row[5]]

        # table -> [(parent, the table's referencing column, the parent's referenced column)]
        references: dict[str, list[tuple[str, str, str]]] = {}
        for table in tables:
            for row in raw.execute(f"PRAGMA foreign_key_list('{table}')"):
                parent = str(row[2])
                to = [str(row[4])] if row[4] is not None else primary_key(parent)
                references.setdefault(table, []).extend((parent, str(row[3]), column) for column in to)
        constraints = {}
        for table in T.AD_WRITABLE:
            keys = {(parent, to) for parent, _from, to in references.get(table, ())}
            keys |= {(child, from_) for child, refs in references.items() for parent, from_, _to in refs
                     if parent == table}
            constraints[table] = frozenset(keys)
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

    from learnloop.adaptive_difficulty import protected_tables as T

    if name == T.INCUMBENT and not _ENTERING_SCOPE.get():
        # The incumbent's scope opens only through :func:`incumbent_answer` (the compose fix round 3).
        _refuse_entry("rules('incumbent') called directly")
    outer = _IN_RULES.get()
    token = _IN_RULES.set(name)
    try:
        yield
    finally:
        _IN_RULES.reset(token)
        if outer != name:
            # Leaving any scope for a narrower one (the rules, or the derivation scope back into
            # the rules: round 7) expires what was prepared inside it.
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


_SCOPE_ENTRY: ContextVar[Any] = ContextVar("ad_incumbent_scope_entry", default=None)
_ENTERING_SCOPE: ContextVar[bool] = ContextVar("ad_incumbent_scope_entering", default=False)


@dataclass(frozen=True)
class IncumbentHandles:
    """The operation's own handles on the vault and the database, the only objects that reach an
    incumbent question besides its plain request (never anything AD passed)."""

    vault: Any
    repository: Any


def incumbent_answer(question: Callable[[IncumbentHandles, Any], Any], request: Any) -> Any:
    """Ask the incumbent one question inside the incumbent's scope, and return its plain answer
    (the compose fix round 3, by construction):

    * the caller is one of the two pinned entry functions (``protected_tables.INCUMBENT_ENTRIES``),
      checked on the live frame: any other entry (by ``getattr``, an alias, another module, a
      function forged with the entry's name) is refused and poisons the operation;
    * ``question`` is one of the registered incumbent questions (``INCUMBENT_QUESTIONS``: functions of
      an incumbent module, checked on their code), so only incumbent code runs in the scope;
    * ``request`` is plain, immutable data (:func:`require_plain`): no callable and no AD-owned
      object crosses into the scope, so nothing AD defined can run there through its arguments; and
      a read whose stack holds AD code or a callback from outside LearnLoop is refused anyway
      (``Guard._scope_violation``);
    * the question receives the operation's own handles (:class:`IncumbentHandles`), runs with every
      write refused, and its answer is checked plain on the way out."""

    from learnloop.adaptive_difficulty import protected_tables as T

    caller = sys._getframe(1)
    if not _pinned_entry(caller):
        _refuse_entry(f"an entry from {caller.f_globals.get('__name__', '?')}.{caller.f_code.co_name}")
    if not _registered_question(question):
        _refuse_entry(f"an unregistered question {getattr(question, '__qualname__', question)!r}")
    op = _CURRENT.get()
    if op is None:
        raise GuardDenied("the incumbent's scope opens only inside an AD operation")
    problem = plain_problem(request)
    if problem is not None:
        _refuse_entry(f"a request that is not plain data ({problem})")
    handles = IncumbentHandles(vault=op.raw_vault, repository=op.raw_repository)
    entering = _ENTERING_SCOPE.set(True)
    try:
        scope = rules(T.INCUMBENT)
        scope.__enter__()
    finally:
        _ENTERING_SCOPE.reset(entering)
    entry_token = _SCOPE_ENTRY.set(sys._getframe(0))
    try:
        answer = question(handles, request)
    except BaseException:
        _SCOPE_ENTRY.reset(entry_token)
        op.guard._scope_cache = None
        scope.__exit__(*sys.exc_info())
        raise
    _SCOPE_ENTRY.reset(entry_token)
    op.guard._scope_cache = None
    scope.__exit__(None, None, None)
    if op.guard.poisoned:
        raise OperationPoisoned("the AD guard refused a read or write in the incumbent's scope")
    problem = plain_problem(answer)
    if problem is not None:
        _refuse_entry(f"an answer that is not plain data ({problem})")
    return answer


@contextmanager
def incumbent_constraints() -> Iterator[None]:
    """Refused (the compose fix round 3): the incumbent's scope opens only through
    :func:`incumbent_answer`, from a pinned entry function. Kept so a stale caller fails loudly."""

    _refuse_entry("incumbent_constraints() called directly")
    yield  # pragma: no cover - never reached


def _refuse_entry(why: str) -> None:
    op = _CURRENT.get()
    if op is not None:
        op.guard._deny("enter", "(incumbent scope)", f"the incumbent's scope refused: {why}", _reader())
    raise GuardDenied(f"the incumbent's scope refused: {why}")


def _pinned_entry(frame: Any) -> bool:
    from learnloop.adaptive_difficulty import protected_tables as T

    name = frame.f_globals.get("__name__", "")
    module = sys.modules.get(str(name))
    return bool(
        (name, frame.f_code.co_name) in T.INCUMBENT_ENTRIES
        and module is not None
        and frame.f_globals is module.__dict__
        and frame.f_code.co_filename == getattr(module, "__file__", None)
        and frame.f_code.co_qualname == frame.f_code.co_name
    )


def _registered_question(question: Any) -> bool:
    from learnloop.adaptive_difficulty import protected_tables as T

    code = getattr(question, "__code__", None)
    module_name = getattr(question, "__module__", None)
    module = sys.modules.get(str(module_name))
    return bool(
        code is not None
        and (module_name, getattr(question, "__qualname__", None)) in T.INCUMBENT_QUESTIONS
        and module is not None
        and code.co_filename == getattr(module, "__file__", None)
        and getattr(question, "__globals__", None) is module.__dict__
    )


def _ad_owned(module: str) -> bool:
    from learnloop.adaptive_difficulty import protected_tables as T

    return any(module == prefix or module.startswith(prefix + ".") for prefix in T.AD_MODULES)


def _trusted_frame(module: str, filename: str) -> bool:
    """A frame of incumbent code (a LearnLoop module outside AD) or of the Python installation."""

    if filename.startswith("<"):
        # Generated code (a dataclass's methods, frozen importlib): judged by the module it runs in.
        return module.startswith("learnloop.") or not module or module in sys.stdlib_module_names or \
            module.split(".")[0] in sys.stdlib_module_names
    path = os.path.abspath(filename)
    return any(path.startswith(root) for root in _trusted_roots())


_ROOTS: list[tuple[str, ...]] = []


def _trusted_roots() -> tuple[str, ...]:
    if not _ROOTS:
        import sysconfig

        import learnloop

        roots = {os.path.join(os.path.abspath(os.path.dirname(learnloop.__file__)), "")}
        for key in ("stdlib", "platstdlib", "purelib", "platlib"):
            path = sysconfig.get_paths().get(key)
            if path:
                roots.add(os.path.join(os.path.abspath(path), ""))
        _ROOTS.append(tuple(sorted(roots)))
    return _ROOTS[0]


_PLAIN_SCALARS = (type(None), bool, int, float, str, datetime, date, timedelta)


def plain_problem(value: Any, *, _path: str = "request", _depth: int = 0, _seen: set[int] | None = None) -> str | None:
    """Why ``value`` is not plain, immutable data, or None (the incumbent scope's boundary): a
    scalar (None, bool, int, float, str, date, datetime, timedelta), a tuple or frozenset of plain
    data, a read-only mapping (``types.MappingProxyType``) of plain keys to plain values, or an
    instance of a FROZEN dataclass of an incumbent module (LearnLoop, outside AD) whose every field
    is plain. Nothing else: no callable, no generator, no mutable container, no AD-owned object."""

    if _depth > 24:
        return f"{_path}: nested too deeply"
    if isinstance(value, _PLAIN_SCALARS) and type(value) in _PLAIN_SCALARS:
        return None
    seen = _seen if _seen is not None else set()
    if id(value) in seen:
        return None
    seen.add(id(value))
    kind = type(value)
    if kind in (tuple, frozenset):
        for index, element in enumerate(value):
            problem = plain_problem(element, _path=f"{_path}[{index}]", _depth=_depth + 1, _seen=seen)
            if problem is not None:
                return problem
        return None
    if kind is MappingProxyType:
        for key, element in value.items():
            problem = plain_problem(key, _path=f"{_path} key", _depth=_depth + 1, _seen=seen) or plain_problem(
                element, _path=f"{_path}[{key!r}]", _depth=_depth + 1, _seen=seen)
            if problem is not None:
                return problem
        return None
    import dataclasses

    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        module = str(getattr(kind, "__module__", ""))
        if _ad_owned(module) or not module.startswith("learnloop."):
            return f"{_path}: a {kind.__qualname__} from {module} (only incumbent dataclasses cross)"
        if not kind.__dataclass_params__.frozen:  # type: ignore[attr-defined]
            return f"{_path}: a mutable {kind.__qualname__}"
        for item in dataclasses.fields(value):
            problem = plain_problem(getattr(value, item.name), _path=f"{_path}.{item.name}", _depth=_depth + 1,
                                    _seen=seen)
            if problem is not None:
                return problem
        extra = set(getattr(value, "__dict__", {})) - {item.name for item in dataclasses.fields(value)}
        if extra:
            return f"{_path}: a {kind.__qualname__} with attributes beyond its fields ({sorted(extra)})"
        return None
    if callable(value):
        return f"{_path}: a callable ({kind.__qualname__})"
    return f"{_path}: a {kind.__module__}.{kind.__qualname__}"


def require_plain(value: Any, *, what: str = "request") -> None:
    problem = plain_problem(value, _path=what)
    if problem is not None:
        raise GuardDenied(f"not plain data: {problem}")


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
           "IncumbentHandles", "denial_count", "entry", "epoch_of", "incumbent_answer", "incumbent_constraints", "is_denial", "optional_operation",
           "own_write", "rules", "suspended"]
