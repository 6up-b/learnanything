"""Connection ownership and nested repository transaction scopes."""

from __future__ import annotations

import sqlite3
import re
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from functools import wraps
from inspect import signature
from typing import Any
from learnloop.db.stores.ingest_queue import JobOwner, owns_ingest_job


class JobOwnershipLost(RuntimeError):
    """An expired or superseded job attempted to publish more state."""


@dataclass(frozen=True)
class _JobGuard:
    path: Path
    job_id: str
    owner: JobOwner

    def check(self, connection):
        if not owns_ingest_job(connection, self.job_id, self.owner):
            raise JobOwnershipLost(
                f'Job {self.job_id} no longer owns attempt {self.owner.attempt_count}'
            )


_job_guard: ContextVar[_JobGuard | None] = ContextVar('ingest_write_guard', default=None)

_LEADING_COMMENTS = re.compile(r'\A(?:\s+|--[^\n]*(?:\n|$)|/\*.*?\*/)*', re.S)
_WRITE_VERBS = frozenset({'INSERT', 'UPDATE', 'DELETE', 'REPLACE', 'CREATE', 'ALTER', 'DROP'})
_STRING_LITERALS = re.compile(r"'(?:[^']|'')*'")
# The DML forms a CTE body can end in. REPLACE must be followed by INTO so the
# replace() string function in a read does not count. A bare UPDATE or DELETE
# used as an identifier still classifies as a write; that only costs a read
# the write guard, whereas missing a write would skip the ownership check.
_CTE_WRITE = re.compile(
    r'\b(?:INSERT|REPLACE)\s+(?:OR\s+\w+\s+)?INTO\b|\bUPDATE\b|\bDELETE\s+FROM\b',
    re.I,
)


def _is_write_statement(sql: str) -> bool:
    """Whether a statement can modify the database.

    A ``WITH`` statement is a write only when it ends in DML; a CTE ``SELECT``
    is a read and must not take the write lock or an ownership check.
    """

    statement = _LEADING_COMMENTS.sub('', sql)
    verb = statement.split(None, 1)[0].upper() if statement else ''
    if verb == 'WITH':
        return _CTE_WRITE.search(_STRING_LITERALS.sub("''", statement)) is not None
    return verb in _WRITE_VERBS


@contextmanager
def allow_late_model_records():
    """Let the model-call store record paid work after its job lost ownership.

    Losing a job's lease removes publication authority, but does not erase
    billable work. Only two writes use this: finishing a receipt the attempt
    itself started (constrained to that receipt's id and owner), and saving a
    validated checkpoint. Checkpoints are write-once, keyed by their inputs
    and never canonical state, so a late one is exactly the work a successor
    would otherwise pay for again.
    """
    token = _job_guard.set(None)
    try:
        yield
    finally:
        _job_guard.reset(token)


@contextmanager
def guard_ingest_writes(path, job_id, worker_id, attempt_count):
    """Fence all repositories for this database on the current worker thread."""
    from learnloop.vault_lock import guard_vault_mutations

    guard = _JobGuard(Path(path).resolve(), job_id, JobOwner(worker_id, attempt_count))
    token = _job_guard.set(guard)

    def check_vault(_root):
        from learnloop.db.connection import connect

        connection = connect(guard.path, read_only=True)
        try:
            guard.check(connection)
        finally:
            connection.close()

    try:
        with guard_vault_mutations(check_vault):
            yield
    finally:
        _job_guard.reset(token)


def current_ingest_job_id(path) -> str | None:
    """The durable job running on this thread for the database at ``path``, if any.

    Work that a job does for itself can name it durably (an adaptive difficulty commission drawn by
    a generation job starts its expiry clock when that job finishes, Codex verify F14)."""

    guard = _job_guard.get()
    if guard is not None and Path(path).resolve() == guard.path:
        return guard.job_id
    return None


#: A hook every connection opened on this thread's context passes through while it is set
#: (``connection_hook``). Adaptive difficulty's operation installs its SQLite authorizer this way
#: (``adaptive_difficulty.operation``); unset, connections are exactly as before.
_connection_hook: ContextVar[Any] = ContextVar('connection_hook', default=None)


@contextmanager
def connection_hook(hook):
    """Pass every connection opened in this context (``connect()``, read-only or writable) to
    ``hook(connection, path)`` before it is returned."""

    token = _connection_hook.set(hook)
    try:
        yield
    finally:
        _connection_hook.reset(token)


def apply_connection_hook(connection, path):
    hook = _connection_hook.get()
    if hook is not None:
        hook(connection, Path(path))
    return connection


def guarded_connection(connection, path):
    apply_connection_hook(connection, path)
    guard = _job_guard.get()
    if guard is not None and Path(path).resolve() == guard.path:
        return _GuardedConnection(connection, guard)
    return connection


class _GuardedConnection:
    def __init__(self, connection, guard):
        self._connection = connection
        self._guard = guard
        self._checked = False

    def __getattr__(self, name):
        return getattr(self._connection, name)

    @property
    def isolation_level(self):
        return self._connection.isolation_level

    @isolation_level.setter
    def isolation_level(self, value):
        self._connection.isolation_level = value
        self._checked = False

    def _before(self, sql):
        if _is_write_statement(sql):
            if not self._connection.in_transaction:
                self._connection.execute('BEGIN IMMEDIATE')
                self._checked = False
            if not self._checked:
                self._guard.check(self._connection)
                self._checked = True
            return
        statement = _LEADING_COMMENTS.sub('', sql)
        verb = statement.split(None, 1)[0].upper() if statement else ''
        if verb in {'COMMIT', 'ROLLBACK', 'END'}:
            self._checked = False

    def execute(self, sql, parameters=()):
        self._before(sql)
        return self._connection.execute(sql, parameters)

    def executemany(self, sql, parameters):
        self._before(sql)
        return self._connection.executemany(sql, parameters)

    def executescript(self, _script):
        raise RuntimeError('schema scripts cannot run inside an owned ingest job')

    def cursor(self, *args, **kwargs):
        return _GuardedCursor(self, self._connection.cursor(*args, **kwargs))

    def commit(self):
        try:
            self._connection.commit()
        finally:
            self._checked = False

    def rollback(self):
        try:
            self._connection.rollback()
        finally:
            self._checked = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        try:
            return self._connection.__exit__(*exc)
        finally:
            self._checked = False


class _GuardedCursor:
    def __init__(self, connection, cursor):
        self._connection, self._cursor = connection, cursor

    def __getattr__(self, name):
        return getattr(self._cursor, name)

    def __iter__(self):
        return iter(self._cursor)

    def execute(self, sql, parameters=()):
        self._connection._before(sql)
        return self._cursor.execute(sql, parameters)

    def executemany(self, sql, parameters):
        self._connection._before(sql)
        return self._cursor.executemany(sql, parameters)


class OwnedConnection:
    """Close a borrowed repository connection at the end of its with block."""

    def __init__(self, connection: sqlite3.Connection):
        object.__setattr__(self, "_connection", connection)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._connection, name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(self._connection, name, value)

    def __enter__(self):
        return self._connection

    def __exit__(self, *exc):
        try:
            return self._connection.__exit__(*exc)
        finally:
            self._connection.close()


class AtomicConnection:
    """Keep store methods' own commits inside an owning transaction.

    Explicit BEGIN/COMMIT pairs become savepoints. Context managers get their
    own savepoint, so a caught inner exception rolls back only that operation.
    No borrowed handle can close or commit the owning transaction. SQL scripts
    are rejected because sqlite3.executescript implicitly commits first.
    """

    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection
        self._serial = 0
        self._contexts: list[tuple[str, int]] = []
        self._explicit: list[tuple[str, int]] = []

    def __getattr__(self, name: str) -> Any:
        return getattr(self._connection, name)

    @property
    def isolation_level(self):
        return self._connection.isolation_level

    @isolation_level.setter
    def isolation_level(self, value):
        # Setting None would commit sqlite3's current transaction immediately.
        pass

    def _savepoint(self) -> str:
        self._serial += 1
        name = f"repository_scope_{self._serial}"
        self._connection.execute(f"SAVEPOINT {name}")
        return name

    def __enter__(self):
        self._contexts.append((self._savepoint(), len(self._explicit)))
        return self

    def __exit__(self, exc_type, exc, traceback):
        name, depth = self._contexts.pop()
        del self._explicit[depth:]
        if exc_type is not None:
            self._connection.execute(f"ROLLBACK TO {name}")
        self._connection.execute(f"RELEASE {name}")
        return False

    def execute(self, sql, parameters=()):
        statement = sql.strip().rstrip(";").upper()
        if statement in {"BEGIN", "BEGIN TRANSACTION", "BEGIN IMMEDIATE", "BEGIN EXCLUSIVE", "BEGIN DEFERRED"}:
            self._explicit.append((self._savepoint(), len(self._contexts)))
            return self._connection.execute("SELECT 1 WHERE 0")
        if statement in {"COMMIT", "END", "END TRANSACTION"}:
            self.commit()
            return self._connection.execute("SELECT 1 WHERE 0")
        if statement in {"ROLLBACK", "ROLLBACK TRANSACTION"}:
            self.rollback()
            return self._connection.execute("SELECT 1 WHERE 0")
        return self._connection.execute(sql, parameters)

    def executescript(self, _script):
        raise RuntimeError("executescript cannot run inside Repository.atomic()")

    def cursor(self, *args, **kwargs):
        return _AtomicCursor(self, self._connection.cursor(*args, **kwargs))

    def commit(self):
        if self._explicit and self._explicit[-1][1] >= len(self._contexts):
            name, _ = self._explicit.pop()
            self._connection.execute(f"RELEASE {name}")

    def rollback(self):
        if self._explicit and self._explicit[-1][1] >= len(self._contexts):
            name, _ = self._explicit.pop()
            self._connection.execute(f"ROLLBACK TO {name}")
            self._connection.execute(f"RELEASE {name}")
        elif self._contexts:
            self._connection.execute(f"ROLLBACK TO {self._contexts[-1][0]}")
        else:
            raise RuntimeError("rollback requires a nested repository scope")

    def close(self):
        pass


class _AtomicCursor:
    """Cursor transaction statements must obey the same borrowing rules."""
    def __init__(self, connection, cursor):
        self._connection = connection
        self._cursor = cursor

    def __getattr__(self, name):
        return getattr(self._cursor, name)

    def __iter__(self):
        return iter(self._cursor)

    def execute(self, sql, parameters=()):
        self._cursor.close()
        self._cursor = self._connection.execute(sql, parameters)
        return self

    def executescript(self, script):
        return self._connection.executescript(script)


def pinned_repository_call(function):
    """Reuse a connection for short local work, preserving each write commit."""
    parameters = signature(function)

    @wraps(function)
    def wrapped(*args, **kwargs):
        repository = parameters.bind(*args, **kwargs).arguments["repository"]
        with repository.pinned():
            return function(*args, **kwargs)

    return wrapped


def atomic_repository_call(function):
    """Wrap a local operation with a named repository argument atomically.

    Only use for local computation/persistence, never an operation that waits
    for a provider. The owning BEGIN IMMEDIATE also serializes read/modify/write
    decisions with other database writers.
    """

    parameters = signature(function)

    @wraps(function)
    def wrapped(*args, **kwargs):
        repository = parameters.bind(*args, **kwargs).arguments["repository"]
        with repository.atomic():
            return function(*args, **kwargs)

    return wrapped
