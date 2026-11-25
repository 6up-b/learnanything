"""The writer fence: a tag-dependent write commits only under the algorithm tag the vault's database is at.

A vault's tag is published in ``learnloop.toml``, and a process reads it once, when it loads the vault. A process that
loaded the vault before ``learnloop upgrade`` committed an activation still holds the predecessor's tag, and without
this fence it would go on writing under the predecessor's rules after the successor's activation (refactor bug
ledger L42-R2): a grade with no grade-curve row, a lesson check's mass fitted by the old rules, a label-derived
mastery update. The design note is ``docs/reviews/refactor-writer-fence.md``.

**What is authoritative.** The tag a write may commit under is the database's, the one row of ``writer_fence``
(migration 275). An activation (``learnloop.ops.upgrades``) sets it inside its own transaction, before it derives the
successor's state, so it flips at the activation's commit and never before. The config's tag stays the published
value the upgrade writes last; the two differ only while an activation runs (it holds the write lock), after a death
between the config's publication and the commit (the activation journal stands and the next opener completes it;
until then the database, still the predecessor's, is the truth), or after a hand edit of the config. A vault no
fence-aware activation has touched has no row, and then the config is the tag, as before the fence.

**How a write is checked.** Every writable connection this code opens (``db.connection``) registers SQL functions
named after the tags it writes under (:func:`binding`): ``learnloop writes under <tag>``, plus the marker
``learnloop fenced writer``. Triggers on the tables that carry tag-dependent facts (:data:`GUARDED`) look the names
up in ``pragma_function_list`` as the row is written, so the check runs inside the write's own transaction, under its
write lock, against the row as it stands; the triggers never call a function, so a connection without them prepares
the statement and gets the refusal's plain message.

Once the row exists, a write is allowed only on a connection registered for the row's tag, or on a fence-aware
connection bound to no tag (a process that never loaded this vault: a scratch copy, a test seeding rows; it computed
nothing from the vault's config). Everything else is refused: a stale writer of this code (bound to another tag), and
any connection without the marker, which is how code older than the fence (``a17cba6132`` and before) and every other
SQLite client meet the database. Before the first fence-aware activation there is no row and nothing is fenced, so an
older binary keeps working until then; from that activation on it is refused whatever tag it knows (it cannot say
which), its own upgrade included, so the row never falls behind the config.

**Where the binding comes from: the vault the write was computed from.** A connection writes under the tag of the
vault object whose inputs the work used, never under whatever the process loaded last (review fix round, WF-R1): a
scope (:func:`writing_under`, entered for a vault by ``learnloop.vault.repository.vault_writes``) binds every
connection opened in it, and a :class:`~learnloop.db.repositories.Repository` keeps the binding in force when it was
made (``vault_repository`` binds the tag of the paths' own config). The desktop sidecar and the phone host scope each
request to their context's vault, the MCP host each request to the vault it loaded, a background job to the scope it
was started in, the post-attempt worker each pass to the vault it took, and the activation to the predecessor and the
successor together. Only a connection opened outside every scope and every bound repository falls back to the tag of
the newest config this process loaded (:func:`observe`, called by ``load_vault``). A checkout reads its binding once
(:func:`binding`) and uses it for both the pool's key and the registration.

**A refusal is never swallowed** (WF-R2). On a connection this code opened, the trigger's refusal is raised as
:class:`WriterFenceRefusal`, a ``BaseException``: no ``except Exception`` takes it, so a best-effort savepoint or a
broad handler around a fenced write lets it through, and the enclosing transaction (a serve, a grade) rolls back
whole. Only ``except BaseException`` and a bare ``except`` can catch it; each such handler in ``src`` re-raises or is
a registered boundary (:data:`REFUSAL_BOUNDARIES`, checked by ``tests/test_writer_fence_scopes.py``), as is every
keep-alive worker loop. Each refusal is counted per database (:func:`refusals`), so a host whose background work met
one reloads at its next request. The desktop sidecar and the phone host reload the vault and answer a retryable
``vault_upgraded_while_open`` (or, when the config itself disagrees with the database, say to run
``learnloop upgrade``); the MCP host drops its cached vault and says try again; a CLI command stops with the
refusal's words.

**The database's tag never moves backwards** (WF-R4). An activation moves the row only from its predecessor
(:func:`advance`, under its transaction's lock); ``learnloop upgrade`` starts from the row when it exists, and a
config that disagrees with it (restored from an older copy, or edited by hand) is set back to the row's tag first.

This module is a leaf: it imports nothing of LearnLoop, so the connection layer can import it.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager, nullcontext
from contextvars import ContextVar
from pathlib import Path

#: The table holding the database's tag (migration 275).
TABLE = "writer_fence"

#: A fence-aware connection registers one function per tag it writes under, named this prefix plus the tag.
TAG_FUNCTION_PREFIX = "learnloop writes under "

#: Every writable connection this code opens registers this function, bound or not.
MARKER_FUNCTION = "learnloop fenced writer"

#: The text of the triggers' refusal (``RAISE(ABORT, ...)``), the same for every writer, old binaries included.
REFUSAL = (
    "LearnLoop writer fence: this vault was upgraded while this LearnLoop process had it open, so nothing was saved. "
    "Restart LearnLoop from the upgraded version, or reload the vault, and try again."
)

#: The (table, event) pairs whose writes are fenced, one trigger each (migrations 275 and 276 create them; a migration
#: that rebuilds one of these tables recreates its trigger, and ``tests/test_writer_fence.py`` checks every pair at the
#: head). Each is a fact computed under the vault's tag that a rebuild keeps or reads, a learner-visible decision a
#: stale writer could not take back, or the record of a rebuild: the answer itself (``practice_attempts``, the first
#: write of every live grade, so a refused grade writes nothing), a grade's evidence (a regrade's or an adjudication's
#: first write), its surprise and grade curve, a lesson check (its mass is written once), mastery, the grade-time
#: forecast, the application order and a rebuild's receipt (275); a plan's served presentation (the serve-time
#: forecast is recorded only by the serve that inserts it), a probe pinned for the learner, an adjudication (it moves
#: an interpretation's head even when it adds no evidence), and the first completion of a Reader section (the first
#: ``completed_at`` and its cause are kept for good) (276).
GUARDED: tuple[tuple[str, str], ...] = (
    ("practice_attempts", "INSERT"),
    ("grading_evidence", "INSERT"),
    ("attempt_surprise", "INSERT"),
    ("attempt_surprise", "UPDATE"),
    ("attempt_grade_curves", "INSERT"),
    ("lesson_checks", "INSERT"),
    ("learning_object_mastery", "INSERT"),
    ("learning_object_mastery", "UPDATE"),
    ("forecast_receipts", "INSERT"),
    ("attempt_application_order", "INSERT"),
    ("derived_state_rebuilds", "INSERT"),
    ("plan_presentations", "INSERT"),
    ("probe_presentations", "INSERT"),
    ("grade_adjudications", "INSERT"),
    ("reader_section_progress", "INSERT"),
    ("reader_section_progress", "UPDATE"),
)

#: The writes of a fenced pair that the fence looks at, when not all of them: a Reader section's progress is fenced
#: only where it first records a completion (a stale reader's scroll position is no fact a rule decided).
GUARD_CONDITIONS: dict[tuple[str, str], str] = {
    ("reader_section_progress", "INSERT"): "NEW.completed_at IS NOT NULL",
    ("reader_section_progress", "UPDATE"): "OLD.completed_at IS NULL AND NEW.completed_at IS NOT NULL",
}

#: The handlers in ``src`` that catch ``BaseException`` (or everything) without re-raising, as
#: ``path:function``. Each hands what it caught to a waiter or a job's answer (the refusal reaches the requester, and
#: :func:`refusals` makes the host reload), or is the rollback helper that attaches a second failure to the first.
#: ``tests/test_writer_fence_scopes.py`` fails on an unlisted one.
REFUSAL_BOUNDARIES: tuple[str, ...] = (
    "src/learnloop/content/synthesis/jobs.py:answer_pending",
    "src/learnloop/content/synthesis/jobs.py:handle_inventory",
    "src/learnloop/db/repositories.py:_roll_back_after",
    "src/learnloop_mobile/runtime.py:_run",
    "src/learnloop_sidecar/handlers/deliverables.py:run",
    "src/learnloop_sidecar/handlers/hints.py:run",
    "src/learnloop_sidecar/handlers/library_ask.py:run",
    "src/learnloop_sidecar/handlers/notes.py:run",
    "src/learnloop_sidecar/handlers/reader_cue_discovery.py:run",
    "src/learnloop_sidecar/handlers/reading_paths.py:run",
    "src/learnloop_sidecar/polled_jobs.py:run",
)


class WriterFenceRefusal(BaseException):
    """The fence refused a write: the vault was upgraded after the work's vault was loaded, so nothing of the write
    was saved. A ``BaseException`` on purpose, like ``KeyboardInterrupt``: the unit of work must stop and its host
    reload, so no ``except Exception`` (a best-effort savepoint, a fallback) may take it for an ordinary failure."""


class FenceMismatch(RuntimeError):
    """An activation found the database at another tag than its predecessor: it would move the tag sideways or back."""


#: Refusals met so far, by resolved database path (a host compares its own count to reload at its next request).
_REFUSALS: dict[str, int] = {}


class FencedCursor(sqlite3.Cursor):
    """A cursor of a writable connection this code opened: the trigger's refusal comes out as
    :class:`WriterFenceRefusal`; every other error is untouched."""

    def execute(self, sql, parameters=(), /):  # type: ignore[override]
        try:
            return super().execute(sql, parameters)
        except sqlite3.IntegrityError as error:
            raise_refusal(self, error)
            raise

    def executemany(self, sql, parameters, /):  # type: ignore[override]
        try:
            return super().executemany(sql, parameters)
        except sqlite3.IntegrityError as error:
            raise_refusal(self, error)
            raise

    def executescript(self, script, /):  # type: ignore[override]
        try:
            return super().executescript(script)
        except sqlite3.IntegrityError as error:
            raise_refusal(self, error)
            raise


class FencedConnection(sqlite3.Connection):
    """A writable connection this code opened: its statements run on :class:`FencedCursor`s."""

    fence_path: str | None = None

    def cursor(self, factory=None):  # type: ignore[override]
        return super().cursor(FencedCursor if factory is None else factory)

    def execute(self, sql, parameters=(), /):  # type: ignore[override]
        return self.cursor().execute(sql, parameters)

    def executemany(self, sql, parameters, /):  # type: ignore[override]
        return self.cursor().executemany(sql, parameters)

    def executescript(self, script, /):  # type: ignore[override]
        return self.cursor().executescript(script)


def raise_refusal(cursor: sqlite3.Cursor, error: sqlite3.IntegrityError) -> None:
    """Raise ``error`` as :class:`WriterFenceRefusal` when it is the trigger's refusal (and count it for the host);
    return for any other integrity error."""

    if REFUSAL not in str(error):
        return
    path = getattr(cursor.connection, "fence_path", None)
    if path is not None:
        with _OBSERVED_LOCK:
            _REFUSALS[path] = _REFUSALS.get(path, 0) + 1
    raise WriterFenceRefusal(str(error)) from error


def refusals(sqlite_path: Path | str) -> int:
    """How many writes to the database at ``sqlite_path`` the fence refused in this process so far."""

    with _OBSERVED_LOCK:
        return _REFUSALS.get(_key(sqlite_path), 0)


#: The binding of this context, by resolved database path: the tags a connection opened here writes under.
_WRITING_UNDER: ContextVar[tuple[tuple[str, frozenset[str]], ...]] = ContextVar(
    "learnloop_writer_fence_binding", default=()
)

#: The tag of the newest config this process loaded, by resolved database path.
_OBSERVED: dict[str, str] = {}
_OBSERVED_LOCK = threading.Lock()


def _key(sqlite_path: Path | str) -> str:
    return str(Path(sqlite_path).resolve())


def observe(sqlite_path: Path | str, tag: str | None) -> None:
    """This process loaded the vault whose database is ``sqlite_path`` at ``tag``: its connections write under it."""

    if not tag:
        return
    with _OBSERVED_LOCK:
        _OBSERVED[_key(sqlite_path)] = str(tag)


@contextmanager
def writing_under(sqlite_path: Path | str, *tags: str) -> Iterator[None]:
    """Connections to ``sqlite_path`` opened in this context write under ``tags`` (the tag of the vault the work was
    computed from; the activation's predecessor and successor together), whatever this process loaded last. No tags:
    an unbound scope (a scratch copy)."""

    token = _WRITING_UNDER.set(_with_binding(_key(sqlite_path), tags))
    try:
        yield
    finally:
        _WRITING_UNDER.reset(token)


def bound(sqlite_path: Path | str, tags: frozenset[str] | None):
    """:func:`writing_under` ``tags`` when there are any, else nothing: a repository's connection under the binding it
    was made with (:class:`~learnloop.db.repositories.Repository`)."""

    return writing_under(sqlite_path, *tags) if tags else nullcontext()


def bind_scope(sqlite_path: Path | str, *tags: str) -> None:
    """From here to the end of the enclosing :func:`writing_under` (or the context), connections to ``sqlite_path``
    write under ``tags``: what a host does when it publishes a newly loaded vault in the middle of a request."""

    _WRITING_UNDER.set(_with_binding(_key(sqlite_path), tags))


def _with_binding(key: str, tags) -> tuple[tuple[str, frozenset[str]], ...]:
    current = tuple(entry for entry in _WRITING_UNDER.get() if entry[0] != key)
    return current + ((key, frozenset(str(tag) for tag in tags if tag)),)


def current_scope() -> tuple[tuple[str, frozenset[str]], ...]:
    """This context's scopes, to hand to a thread it starts (:func:`restored_scope`)."""

    return _WRITING_UNDER.get()


@contextmanager
def restored_scope(scope: tuple[tuple[str, frozenset[str]], ...]) -> Iterator[None]:
    """Run under the scopes :func:`current_scope` read where the work was started."""

    token = _WRITING_UNDER.set(scope)
    try:
        yield
    finally:
        _WRITING_UNDER.reset(token)


def scoped(sqlite_path: Path | str) -> frozenset[str] | None:
    """The tags a scope of this context binds for ``sqlite_path``, or None outside every scope for it."""

    key = _key(sqlite_path)
    for entry_key, tags in _WRITING_UNDER.get():
        if entry_key == key:
            return tags
    return None


def binding(sqlite_path: Path | str) -> frozenset[str]:
    """The tags a connection to ``sqlite_path`` opened now writes under (empty: unbound). Read once per checkout."""

    tags = scoped(sqlite_path)
    if tags is not None:
        return tags
    with _OBSERVED_LOCK:
        observed = _OBSERVED.get(_key(sqlite_path))
    return frozenset() if observed is None else frozenset({observed})


def _present() -> int:
    return 1


def register(connection: sqlite3.Connection, sqlite_path: Path | str, tags: frozenset[str]) -> frozenset[str]:
    """Register the marker and ``tags`` (the checkout's one read of :func:`binding`) on a writable connection."""

    # Through the base class: the registration is part of the open, not a change a pool's subclass should count as
    # a user's (a pool keys its connections by this binding instead).
    sqlite3.Connection.create_function(connection, MARKER_FUNCTION, 0, _present)
    for tag in sorted(tags):
        sqlite3.Connection.create_function(connection, TAG_FUNCTION_PREFIX + tag, 0, _present)
    if isinstance(connection, FencedConnection):
        connection.fence_path = _key(sqlite_path)
    return tags


def recorded_tag(connection: sqlite3.Connection) -> str | None:
    """The database's tag, or None while no fence-aware activation has set it (or before migration 275)."""

    try:
        row = connection.execute(f"SELECT algorithm_version FROM {TABLE} WHERE id = 1").fetchone()
    except sqlite3.OperationalError:
        return None
    return None if row is None else str(row[0])


def advance(connection: sqlite3.Connection, *, predecessor: str, target: str, recorded_at: str) -> None:
    """Move the database's tag from ``predecessor`` to ``target`` inside the activation's transaction (it commits with
    the activation's state and never before it), or raise :class:`FenceMismatch` when the database is at any other
    tag: a vault no fence-aware activation touched has no row and is taken at the predecessor, so the tag never moves
    sideways or back."""

    row = recorded_tag(connection)
    if row is not None and row != predecessor:
        raise FenceMismatch(
            f"the vault's database is at {row}, not at {predecessor}, so it cannot move to {target}: "
            f"run `learnloop upgrade` again, which starts from the database's tag"
        )
    connection.execute(
        f"INSERT INTO {TABLE}(id, algorithm_version, updated_at) VALUES (1, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET algorithm_version = excluded.algorithm_version, updated_at = excluded.updated_at",
        (target, recorded_at),
    )


def is_refusal(error: BaseException) -> bool:
    """Whether ``error`` is the fence's refusal of a write (nothing of the write was saved; a retry after the
    process reloads the vault runs under the vault's tag)."""

    return isinstance(error, WriterFenceRefusal) or (isinstance(error, sqlite3.DatabaseError) and REFUSAL in str(error))


__all__ = [
    "GUARDED",
    "GUARD_CONDITIONS",
    "MARKER_FUNCTION",
    "REFUSAL",
    "REFUSAL_BOUNDARIES",
    "TABLE",
    "TAG_FUNCTION_PREFIX",
    "FenceMismatch",
    "FencedConnection",
    "FencedCursor",
    "WriterFenceRefusal",
    "advance",
    "bind_scope",
    "binding",
    "bound",
    "current_scope",
    "is_refusal",
    "observe",
    "raise_refusal",
    "recorded_tag",
    "refusals",
    "register",
    "restored_scope",
    "scoped",
    "writing_under",
]
