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

**Where the binding comes from.** :func:`writing_under` (a context variable: the activation binds the predecessor and
the successor together), else the tag of the newest config this process loaded for the database (:func:`observe`,
called by ``load_vault``; the upgrade observes its target once it commits). A refused write raises
``sqlite3.IntegrityError`` carrying :data:`REFUSAL` (:func:`is_refusal`); the desktop sidecar and the phone host
reload the vault and answer with a retryable error, the MCP host answers "try again" (each of its requests loads the
vault), and the CLI's command stops with the refusal's own words.

This module is a leaf: it imports nothing of LearnLoop, so the connection layer can import it.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
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

#: The (table, event) pairs whose writes are fenced, one trigger each (migration 275 creates them; a migration that
#: rebuilds one of these tables recreates its trigger, and ``tests/test_writer_fence.py`` checks every pair at the
#: head). Each is a fact computed under the vault's tag that a rebuild keeps or reads, or the record of a rebuild:
#: the answer itself (``practice_attempts``, the first write of every live grade, so a refused grade writes nothing),
#: a grade's evidence (a regrade's or an adjudication's first write), its surprise and grade curve, a lesson check
#: (its mass is written once), mastery, the grade-time forecast, the application order, and a rebuild's receipt.
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
)


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
    """Connections to ``sqlite_path`` opened in this context write under ``tags`` (the activation's predecessor and
    successor together), whatever this process observed."""

    key = _key(sqlite_path)
    current = tuple(entry for entry in _WRITING_UNDER.get() if entry[0] != key)
    token = _WRITING_UNDER.set(current + ((key, frozenset(str(tag) for tag in tags if tag)),))
    try:
        yield
    finally:
        _WRITING_UNDER.reset(token)


def binding(sqlite_path: Path | str) -> frozenset[str]:
    """The tags a connection to ``sqlite_path`` opened now writes under (empty: unbound)."""

    key = _key(sqlite_path)
    for entry_key, tags in _WRITING_UNDER.get():
        if entry_key == key:
            return tags
    with _OBSERVED_LOCK:
        observed = _OBSERVED.get(key)
    return frozenset() if observed is None else frozenset({observed})


def _present() -> int:
    return 1


def register(connection: sqlite3.Connection, sqlite_path: Path | str) -> frozenset[str]:
    """Register the marker and this context's binding on a writable connection; the binding registered."""

    tags = binding(sqlite_path)
    connection.create_function(MARKER_FUNCTION, 0, _present)
    for tag in sorted(tags):
        connection.create_function(TAG_FUNCTION_PREFIX + tag, 0, _present)
    return tags


def recorded_tag(connection: sqlite3.Connection) -> str | None:
    """The database's tag, or None while no fence-aware activation has set it (or before migration 275)."""

    try:
        row = connection.execute(f"SELECT algorithm_version FROM {TABLE} WHERE id = 1").fetchone()
    except sqlite3.OperationalError:
        return None
    return None if row is None else str(row[0])


def activate(connection: sqlite3.Connection, *, target: str, recorded_at: str) -> None:
    """Set the database's tag to ``target`` inside the activation's transaction: it commits with the activation's
    state and never before it, so a writer still at the predecessor is refused from that commit on."""

    connection.execute(
        f"INSERT INTO {TABLE}(id, algorithm_version, updated_at) VALUES (1, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET algorithm_version = excluded.algorithm_version, updated_at = excluded.updated_at",
        (target, recorded_at),
    )


def is_refusal(error: BaseException) -> bool:
    """Whether ``error`` is the fence's refusal of a write (nothing of the write was saved; a retry after the
    process reloads the vault runs under the vault's tag)."""

    return isinstance(error, sqlite3.DatabaseError) and REFUSAL in str(error)


__all__ = [
    "GUARDED",
    "MARKER_FUNCTION",
    "REFUSAL",
    "TABLE",
    "TAG_FUNCTION_PREFIX",
    "activate",
    "binding",
    "is_refusal",
    "observe",
    "recorded_tag",
    "register",
    "writing_under",
]
