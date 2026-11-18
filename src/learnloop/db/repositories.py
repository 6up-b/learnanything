from __future__ import annotations

import json
import logging
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

from learnloop import hint_window
from learnloop.activation_journal import refuse_if_interrupted
from learnloop.recurrence import key_for_statement, recurrence_key
from learnloop.outcome_contract import COLLECTION_VERSION
from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.migrate import create_or_attach_current
from learnloop.db.row_serialization import _json, _loads
from learnloop.db.records import (
    ItemParameterState,
    MasteryState,
    PracticeItemState,
    ProbePresentationRecord,
    _UNSET,
    _decode_attempt,
    _decode_causal_hypothesis,
    _decode_error_event,
    _decode_followup_task,
    _decode_hypothesis_set,
    _decode_intervention_need,
    _decode_learning_outcome_label,
    _decode_misconception_candidate,
    _decode_observation_event,
    _decode_observation_template,
    _decode_scheduler_slate,
    _decode_surprise,
    _insert_probe_presentation_row,
    _probe_observation_record,
    _probe_presentation_record,
    _probe_state_record,
    _projection_id,
)
from learnloop.db.stores.attempts import AttemptStoreMixin
from learnloop.db.stores.causal import CausalStoreMixin
from learnloop.db.stores.grading import GradingStoreMixin
from learnloop.db.stores.learner_model import LearnerModelStoreMixin
from learnloop.db.stores.probes import ProbeStoreMixin
from learnloop.db.stores.remediation import RemediationStoreMixin
from learnloop.db.stores.activity import ActivityStoreMixin
from learnloop.db.stores.goals import GoalStoreMixin
from learnloop.db.stores.reader import ReaderStoreMixin
from learnloop.db.stores.source_documents import SourceDocumentStoreMixin
from learnloop.db.stores.task_blueprints import TaskBlueprintStoreMixin
from learnloop.db.stores.completion import AttemptCompletionStoreMixin
from learnloop.db.stores.diagnoses import (
    DiagnosisStoreMixin,
)
from learnloop.db.stores.model_calls import ModelCallStoreMixin
from learnloop.db.stores.recurrence import RecurrenceStoreMixin
from learnloop.db.stores.reading_requests import ReadingRequestStoreMixin
from learnloop.db.stores.session_ownership import SessionOwnershipStoreMixin
from learnloop.db.stores.collection import CollectionStoreMixin
from learnloop.db.stores.ingest_queue import IngestQueueStoreMixin
from learnloop.db.stores.facet_identity import settled_merge_rows
from learnloop.db.stores.observation_ledger import (
    load_authoritative_observation_ledger,
    load_canonical_observation_ledger,
)
from learnloop.ids import new_ulid
from learnloop.ai.usage import TokenUsage
#: A falsifiable expectation extracted from the learner's own tutor question.
OBSERVATION_CHANNEL_LEARNER_QUESTION = "learner_question_embedded"

#: Question contexts whose hint-equivalent rows count in the item's window
#: whatever their practice session (``count_hint_equivalent_question_events``):
#: defined once in ``learnloop.hint_window``, which the learner field's
#: question-to-attempt link reads too (RW1c fix round 5, R3).
ITEM_WINDOW_QUESTION_CONTEXTS = hint_window.ITEM_WINDOW_QUESTION_CONTEXTS


class BlueprintNotReviewed(Exception):
    """A golden-path confirmation named a blueprint version that is not
    reviewed/active (spec_p2 §3.1 step 1). Nothing is activated."""

    def __init__(self, blueprint_version_id: str, *, status: str | None):
        self.blueprint_version_id = blueprint_version_id
        self.status = status
        super().__init__(
            f"blueprint version {blueprint_version_id} is {status!r}, not reviewed/active"
        )


class GoalAlreadyConfirmed(Exception):
    """The goal already has a confirmed contract head whose content differs from the
    v1 this confirmation would mint (spec_p2 §1.2 invariant 2). A fresh golden-path
    run must use a fresh goal id; an edit mints an append-only successor instead."""

    def __init__(self, goal_id: str, *, head_version_id: str | None):
        self.goal_id = goal_id
        self.head_version_id = head_version_id
        super().__init__(
            f"goal {goal_id} is already confirmed (head {head_version_id!r}); "
            "confirmation cannot re-mint v1"
        )


def _proposal_item_identity(client_item_id: Any, payload: Any, edited_payload: Any) -> str:
    """What a proposal item would create: the edited payload's ``id`` when it
    was edited, else the payload's, else its client id (no ``id`` in either)."""

    effective = edited_payload if isinstance(edited_payload, Mapping) else payload
    if isinstance(effective, Mapping) and isinstance(effective.get("id"), str) and effective["id"]:
        return f"id:{effective['id']}"
    return f"client:{client_item_id or ''}"


# -- write-on-change for whole-projection derived tables (followups-oct31, fix 1)


@dataclass(frozen=True)
class _ProjectionTable:
    """A derived table a projection persists whole.

    ``key`` names a cell (the table's unique key); ``values`` are every column
    the projection decides. ``created_at`` and ``updated_at`` are bookkeeping,
    never compared: ``updated_at`` records when a cell's values last changed.
    """

    name: str
    key: tuple[str, ...]
    values: tuple[str, ...]


_FACET_RECALL_PROJECTION = _ProjectionTable(
    "facet_recall_state",
    ("facet_id", "capability_key", "practice_item_id"),
    (
        "id", "recall_alpha", "recall_beta", "recall_mean", "recall_variance",
        "independent_evidence_mass", "raw_coverage_mass", "last_observed_at",
        "last_error_at", "consecutive_failures", "algorithm_version",
    ),
)
_FACET_CAPABILITY_PROJECTION = _ProjectionTable(
    "facet_capability_evidence",
    ("facet_id", "capability"),
    (
        "direct_positive_mass", "direct_negative_mass", "embedded_positive_mass",
        "embedded_negative_mass", "certification_credit", "direct_certification_credit",
        "embedded_certification_credit", "unexercised_supporting_mass",
        "independent_surface_groups_json", "algorithm_version",
    ),
)
_CAPABILITY_RESIDUAL_PROJECTION = _ProjectionTable(
    "capability_residual_state",
    ("facet_id", "capability"),
    (
        "id", "active", "activation_reason", "residual_alpha", "residual_beta",
        "residual_mean", "parent_alpha", "parent_beta", "parent_mean", "divergence",
        "independent_groups", "independent_mass", "algorithm_version",
    ),
)


@dataclass(frozen=True)
class _RebuildStamps:
    """A derived table whose stamps a rebuild keeps on the cells it leaves as
    they were: ``compared`` says what a cell is (a projected stamp included),
    ``stamps`` say when it last changed."""

    key: tuple[str, ...]
    compared: tuple[str, ...]
    stamps: tuple[str, ...]


#: A recall row's ``created_at`` is projected (its first observation), so it is
#: compared; a capability or residual row's is when the cell first appeared.
_REBUILD_STAMPED_TABLES: dict[str, _RebuildStamps] = {
    "facet_recall_state": _RebuildStamps(
        _FACET_RECALL_PROJECTION.key, (*_FACET_RECALL_PROJECTION.values, "created_at"), ("updated_at",)
    ),
    "facet_capability_evidence": _RebuildStamps(
        _FACET_CAPABILITY_PROJECTION.key, _FACET_CAPABILITY_PROJECTION.values, ("created_at", "updated_at")
    ),
    "capability_residual_state": _RebuildStamps(
        _CAPABILITY_RESIDUAL_PROJECTION.key, _CAPABILITY_RESIDUAL_PROJECTION.values, ("created_at", "updated_at")
    ),
    "subject_identifiability_watermarks": _RebuildStamps(
        ("subject_id",), ("registry_hash", "finding_count"), ("checked_at",)
    ),
}
#: The canonical belief cache: what a learning object's replay walks through
#: earlier states (its bounded folds) before its closing projection.
CANONICAL_STAMPED_TABLES: tuple[str, ...] = (
    "facet_recall_state", "facet_capability_evidence", "capability_residual_state",
)
#: Everything the umbrella rebuild re-derives that carries such stamps.
REBUILD_STAMPED_TABLES: tuple[str, ...] = (*CANONICAL_STAMPED_TABLES, "subject_identifiability_watermarks")


@dataclass
class _ProjectionChanges:
    vanished: list[int] = field(default_factory=list)
    changed: list[tuple[int, Mapping[str, Any], str]] = field(default_factory=list)
    new: list[Mapping[str, Any]] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.vanished or self.changed or self.new)


def _projection_changes(
    connection: sqlite3.Connection,
    table: _ProjectionTable,
    cells: Sequence[Mapping[str, Any]],
) -> _ProjectionChanges:
    """Compare a projection with the stored rows, cell by cell.

    A cell's ``created_at`` of ``None`` means "keep the stored one"; a non-null
    one is projected and differs only when the projection moved it.
    """

    projected: dict[tuple[Any, ...], Mapping[str, Any]] = {}
    for cell in cells:
        key = tuple(cell[column] for column in table.key)
        if key in projected:
            # The full DELETE+INSERT this replaces failed on the unique index.
            raise sqlite3.IntegrityError(
                f"UNIQUE constraint failed: {table.name} {dict(zip(table.key, key, strict=True))}"
            )
        projected[key] = cell
    columns = ", ".join((*table.key, *table.values))
    stored = {
        tuple(row[column] for column in table.key): row
        for row in connection.execute(
            f"SELECT rowid AS stored_rowid, {columns}, created_at FROM {table.name}"
        )
    }
    changes = _ProjectionChanges()
    for key, row in stored.items():
        if key not in projected:
            changes.vanished.append(int(row["stored_rowid"]))
    for key, cell in projected.items():
        row = stored.get(key)
        if row is None:
            changes.new.append(cell)
            continue
        created_at = cell["created_at"] if cell.get("created_at") is not None else row["created_at"]
        if created_at != row["created_at"] or any(
            cell[column] != row[column] for column in table.values
        ):
            changes.changed.append((int(row["stored_rowid"]), cell, created_at))
    return changes


def _apply_projection_changes(
    connection: sqlite3.Connection,
    table: _ProjectionTable,
    changes: _ProjectionChanges,
    *,
    now: str,
) -> None:
    # Deletes first, so a new cell can never collide with a vanished one.
    connection.executemany(
        f"DELETE FROM {table.name} WHERE rowid = ?",
        [(rowid,) for rowid in changes.vanished],
    )
    assignments = ", ".join(f"{column} = ?" for column in table.values)
    connection.executemany(
        f"UPDATE {table.name} SET {assignments}, created_at = ?, updated_at = ? WHERE rowid = ?",
        [
            (*(cell[column] for column in table.values), created_at, now, rowid)
            for rowid, cell, created_at in changes.changed
        ],
    )
    columns = (*table.key, *table.values)
    placeholders = ", ".join("?" for _ in range(len(columns) + 2))
    connection.executemany(
        f"INSERT INTO {table.name}({', '.join(columns)}, created_at, updated_at) "
        f"VALUES ({placeholders})",
        [
            (
                *(cell[column] for column in columns),
                cell["created_at"] if cell.get("created_at") is not None else now,
                now,
            )
            for cell in changes.new
        ],
    )


def _write_projection_on_change(
    connection: sqlite3.Connection,
    projections: Sequence[tuple[_ProjectionTable, Sequence[Mapping[str, Any]]]],
    *,
    now: str,
) -> bool:
    """Persist whole projections, writing only the cells that changed.

    Returns whether anything was written. Outside an owning transaction the
    comparison first runs on a read snapshot, so the common no-op takes no
    write lock and commits nothing; when something differs it is compared
    again under ``BEGIN IMMEDIATE`` and applied from that comparison, so a
    writer that committed in between is never applied against stale rowids.
    Inside an owning transaction (``Repository.atomic``) the one comparison
    already runs under its lock.
    """

    def compare() -> list[tuple[_ProjectionTable, _ProjectionChanges]]:
        return [
            (table, _projection_changes(connection, table, cells))
            for table, cells in projections
        ]

    if not connection.in_transaction:
        connection.execute("BEGIN")
        try:
            pending = any(changes for _, changes in compare())
        finally:
            connection.rollback()  # a read snapshot only: nothing to commit
        if not pending:
            return False
        connection.execute("BEGIN IMMEDIATE")
    planned = compare()
    written = False
    for table, changes in planned:
        if changes:
            _apply_projection_changes(connection, table, changes, now=now)
            written = True
    connection.commit()
    return written


def _non_negative_tokens(value: Any) -> int:
    """Coerce a token count for a NOT NULL DEFAULT 0 column (migration 131).

    Token columns are counters that get SUMmed into cost ratios, so a None from
    an unset mapping key, or a float from a provider that reports one, must land
    as a plain non-negative int rather than as NULL or a type error.
    """

    if value is None:
        return 0
    try:
        count = int(value)
    except (TypeError, ValueError):
        return 0
    return count if count > 0 else 0


@dataclass(frozen=True)
class FacetRecallState:
    id: str
    learning_object_id: str
    facet_id: str
    practice_item_id: str | None
    recall_alpha: float
    recall_beta: float
    recall_mean: float
    recall_variance: float
    independent_evidence_mass: float
    raw_coverage_mass: float
    last_attempt_at: str | None
    last_error_at: str | None
    consecutive_failures: int
    algorithm_version: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class CanonicalFacetRecallState:
    """Canonical shared facet belief (KM2 §7.1), keyed on the post-merge facet id
    and observed capability. ``practice_item_id=None`` is the shared aggregate."""

    id: str
    facet_id: str
    capability_key: str
    practice_item_id: str | None
    recall_alpha: float
    recall_beta: float
    recall_mean: float
    recall_variance: float
    independent_evidence_mass: float
    raw_coverage_mass: float
    last_observed_at: str | None
    last_error_at: str | None
    consecutive_failures: int
    algorithm_version: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class FacetCapabilityEvidence:
    """Capability-sliced certification ledger (KM2 §7.1). A replayable cache
    derived from immutable observations, not a new evidence source."""

    facet_id: str
    capability: str
    direct_positive_mass: float
    direct_negative_mass: float
    embedded_positive_mass: float
    embedded_negative_mass: float
    certification_credit: float
    # A1 guard 2 (migration 141): the split ``certification_credit`` is capped
    # from. ``certification_credit`` stays the ONE number Demonstrated reads;
    # these say how it was earned, so the cap is auditable without re-running
    # the projection.
    direct_certification_credit: float = 0.0
    embedded_certification_credit: float = 0.0
    # A1 guard 1: mass a ``supporting`` target would have earned had the trace
    # shown its facet exercised. Recorded, never silent.
    unexercised_supporting_mass: float = 0.0
    independent_surface_groups: list[str] = field(default_factory=list)
    algorithm_version: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass(frozen=True)
class FacetUncertaintyState:
    id: str
    learning_object_id: str
    facet_id: str
    hypothesis_marginal: dict[str, float]
    uncertainty: float
    status: str
    opened_by_attempt_id: str
    opened_reason: str
    last_evidence_at: str | None
    algorithm_version: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class PracticeItemQualityState:
    practice_item_id: str
    bad_item_suspicion: float
    evidence_count: int
    suspicion_reasons: list[str]
    last_flagged_at: str | None
    algorithm_version: str
    updated_at: str


def _roll_back_after(connection: sqlite3.Connection, failure: BaseException) -> bool:
    """Roll back after ``failure`` without replacing it; report success.

    A failed COMMIT (``database is locked`` while a reader holds its SHARED
    lock past the busy timeout) leaves SQLite's transaction open, so the
    failure path must roll back. If the rollback fails as well, the caller
    still sees the original failure, with the rollback error attached as a
    note, and must stop using the connection: its transaction is still open.
    """

    try:
        connection.rollback()
    except BaseException as rollback_error:
        # The note is diagnostic only; a failure while attaching it must not
        # stop the caller from invalidating the connection.
        try:
            failure.add_note(f"Rolling back after this failure also failed: {rollback_error!r}")
        except Exception:
            pass
        return False
    return True


class _PinnedConnection:
    """Proxy that hands the same SQLite connection to every repository call.

    Opening a connection is cheap; the *first* prepared statement on it is not,
    because SQLite parses the whole schema then (~900 objects here, ~10ms). Paths
    that make hundreds of small repository calls — replay, the goal series — pay
    that once per call, which dominates their runtime. ``Repository.pinned()``
    keeps one connection alive for the block and hands out this proxy, which
    mimics a raw connection's context-manager semantics (commit on clean exit,
    rollback on error) without closing the underlying handle. The other
    connection proxies (owned, atomic, ingest-guarded) live in ``db/scopes.py``.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._invalidated = False

    @property
    def invalidated(self) -> bool:
        return self._invalidated

    def invalidate(self) -> None:
        """Close the handle whose failed transaction could not be rolled back.

        Closing discards the open transaction, and every later use through the
        pin raises instead of committing work whose scope reported failure.
        """

        self._invalidated = True
        self._connection.close()

    def _require_valid(self) -> None:
        if self._invalidated:
            raise sqlite3.ProgrammingError(
                "pinned connection was closed after a failed rollback"
            )

    def __getattr__(self, name: str) -> Any:
        if name in {"_connection", "_invalidated"}:
            # Only reached before __init__ has run (copying, unpickling).
            raise AttributeError(name)
        self._require_valid()
        return getattr(self._connection, name)

    def __setattr__(self, name: str, value: Any) -> None:
        # Callers that drive their own transactions assign isolation_level; that
        # has to reach the real connection, not shadow it on the proxy.
        if name in {"_connection", "_invalidated"}:
            super().__setattr__(name, value)
        else:
            self._require_valid()
            setattr(self._connection, name, value)

    def __enter__(self) -> sqlite3.Connection:
        self._require_valid()
        return self._connection

    def __exit__(self, exc_type, exc, traceback) -> bool:
        if exc is not None:
            if not _roll_back_after(self._connection, exc):
                self.invalidate()
            return False
        try:
            self._connection.commit()
        except BaseException as failure:
            if not _roll_back_after(self._connection, failure):
                self.invalidate()
            raise
        return False

    def close(self) -> None:
        # Call sites that drive their own transactions (isolation_level = None,
        # explicit BEGIN) close the connection when done. Under a pin it outlives
        # them, so closing only restores the default transaction handling.
        if not self._invalidated:
            self._connection.isolation_level = ""



def _bindable_plan_presentation(connection: sqlite3.Connection, attempt: Mapping[str, Any]) -> str | None:
    """Router R2a: the ``plan_presentation_id`` an attempt may record, or None.

    The presentation must exist, be of the attempt's item, and not be answered
    by another attempt (the partial unique index would otherwise refuse the
    whole row). A refused id is logged and dropped: the attempt records
    unbound, and its outcome falls back to the labelled session rule."""

    presentation_id = attempt.get("plan_presentation_id")
    if not presentation_id:
        return None
    from learnloop.db.stores.plan_presentations import bindable_presentation

    try:
        bound, why = bindable_presentation(
            connection, str(presentation_id), practice_item_id=str(attempt["practice_item_id"]),
            attempt_id=str(attempt["id"]),
        )
    except sqlite3.Error:
        bound, why = None, "presentation_unreadable"
    if bound is None:
        logging.getLogger(__name__).warning(
            "router R2a: attempt %s recorded without plan presentation %s (%s)", attempt.get("id"), presentation_id, why,
        )
    return bound

class Repository(
    IngestQueueStoreMixin,
    AttemptCompletionStoreMixin,
    ModelCallStoreMixin,
    CollectionStoreMixin,
    DiagnosisStoreMixin,
    RecurrenceStoreMixin,
    SessionOwnershipStoreMixin,
    ReadingRequestStoreMixin,
    ActivityStoreMixin,
    SourceDocumentStoreMixin,
    ReaderStoreMixin,
    GoalStoreMixin,
    TaskBlueprintStoreMixin,
    AttemptStoreMixin,
    GradingStoreMixin,
    CausalStoreMixin,
    ProbeStoreMixin,
    LearnerModelStoreMixin,
    RemediationStoreMixin,
):
    def __init__(self, sqlite_path: Path):
        """Create the database, or attach to one at this code's migrations.

        An existing database with migrations pending is refused, unchanged
        (``UncoordinatedMigrationError``): only the vault's migration
        coordinator upgrades it, because the upgrade's vault-level step (the
        held-out signals the vault's exam membership qualifies) needs the
        vault, which this path-only constructor does not know (exam
        protection identity, F3 final). Code that has the vault opens it
        through ``learnloop.vault.repository``.
        """
        self._initialize(sqlite_path, read_only=False)
        create_or_attach_current(sqlite_path)

    @classmethod
    def attach(
        cls,
        sqlite_path: Path,
        *,
        read_only: bool = False,
    ) -> Repository:
        """Attach to an existing database without applying migrations.

        ``read_only`` is independent from migration policy.  Doctor attaches
        read-only to make accidental writes physically impossible, while replay
        code attaches writable scratch copies whose historical schema must not
        be upgraded as a side effect of opening them.
        """

        repository = cls.__new__(cls)
        repository._initialize(sqlite_path, read_only=read_only)
        return repository

    def _initialize(self, sqlite_path: Path, *, read_only: bool) -> None:
        # LP-min (a), re-review F2: no attach serves a vault whose activation
        # did not commit (the successor's label over the predecessor's state).
        # ``learnloop.vault.repository`` completes it before it attaches.
        refuse_if_interrupted(Path(sqlite_path))
        self.sqlite_path = Path(sqlite_path)
        self._read_only = bool(read_only)
        self._pin = threading.local()

    def connection(self) -> sqlite3.Connection:
        pinned = getattr(self._pin, "connection", None)
        if pinned is not None:
            return pinned
        from learnloop.db.scopes import OwnedConnection

        return OwnedConnection(connect(self.sqlite_path, read_only=self._read_only))

    def in_atomic(self) -> bool:
        """This thread is inside an ``atomic()`` block (a new one would be a savepoint of it)."""

        from learnloop.db.scopes import AtomicConnection

        return isinstance(getattr(self._pin, "connection", None), AtomicConnection)

    @contextmanager
    def atomic(self) -> Iterator[None]:
        """Commit a local operation once, including its nested store writes.

        Inside another ``atomic()`` the block becomes a savepoint of the owning
        transaction. Otherwise it runs one ``BEGIN IMMEDIATE`` transaction on
        the pinned connection when a pin is active, or on a connection of its
        own. A block exception or a failed commit rolls the transaction back
        before propagating, because a pinned connection outlives this scope and
        the next write on it would otherwise publish the work. If that rollback
        also fails, the original exception still propagates and a borrowed
        pinned connection is closed, so nothing can commit the failed work.
        """
        from learnloop.db.scopes import AtomicConnection

        current = getattr(self._pin, "connection", None)
        if isinstance(current, AtomicConnection):
            with current:
                yield
            return
        owns_connection = current is None
        raw = (
            connect(self.sqlite_path, read_only=self._read_only)
            if owns_connection
            else current._connection
        )
        if raw.in_transaction:
            raise RuntimeError("Repository.atomic() requires no unrelated pending transaction")
        try:
            raw.execute("BEGIN IMMEDIATE")
            self._pin.connection = AtomicConnection(raw)
            try:
                yield
                raw.commit()
            except BaseException as failure:
                rolled_back = _roll_back_after(raw, failure)
                if not rolled_back and not owns_connection:
                    current.invalidate()
                raise
        finally:
            self._pin.connection = current
            if owns_connection:
                raw.close()

    @contextmanager
    def pinned(self) -> Iterator[None]:
        """Reuse one connection for the block, on this thread only.

        Purely a performance measure: repository calls behave as they do
        unpinned, they just skip the per-call schema parse. Nested pins reuse the
        outermost connection; other threads keep opening their own. Work left
        uncommitted on the connection commits when the block succeeds and is
        rolled back when it raises; closing the connection discards it even if
        that rollback fails.
        """

        if getattr(self._pin, "connection", None) is not None:
            yield
            return
        raw = connect(self.sqlite_path, read_only=self._read_only)
        pin = _PinnedConnection(raw)
        self._pin.connection = pin
        try:
            yield
            # An invalidated pin was closed with its failed work discarded, and
            # that failure already reached the caller.
            if not pin.invalidated:
                raw.commit()
        except BaseException as failure:
            if not pin.invalidated:
                _roll_back_after(raw, failure)
            raise
        finally:
            self._pin.connection = None
            raw.close()

    def practice_item_state(self, practice_item_id: str) -> PracticeItemState | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM practice_item_state WHERE practice_item_id = ?",
                (practice_item_id,),
            ).fetchone()
        return _practice_item_state(row) if row is not None else None

    def practice_item_states(self) -> dict[str, PracticeItemState]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM practice_item_state").fetchall()
        return {row["practice_item_id"]: _practice_item_state(row) for row in rows}

    def initialize_practice_item_state(
        self,
        practice_item_id: str,
        *,
        content_hash: str | None = None,
        active: bool = True,
        clock: Clock | None = None,
    ) -> bool:
        """Insert a fresh scheduling row only when none exists.

        Never touches an existing row (practice already recorded for the item),
        so a retried publication cannot erase scheduling state. Returns whether
        a row was inserted.
        """
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO practice_item_state(
                  practice_item_id, difficulty, stability, retrievability, due_at,
                  active, content_hash, last_attempt_at, updated_at
                )
                VALUES (?, NULL, NULL, NULL, NULL, ?, ?, NULL, ?)
                ON CONFLICT(practice_item_id) DO NOTHING
                """,
                (practice_item_id, 1 if active else 0, content_hash, now),
            )
            connection.commit()
        return cursor.rowcount > 0

    def update_practice_item_content_state(
        self,
        practice_item_id: str,
        *,
        active: bool,
        content_hash: str | None,
        clock: Clock | None = None,
    ) -> bool:
        """Set only ``active`` and ``content_hash`` on an existing row.

        Mobile PR-2: content sync owns these two columns and nothing else, so it
        can never write back a difficulty, stability, retrievability, due date or
        last-attempt time it read before an attempt committed in another process.
        The caller decides ``active`` and calls this inside the same
        ``atomic()`` transaction (``reconcile_practice_item_state``). Returns
        whether a row was updated.
        """

        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE practice_item_state SET active = ?, content_hash = ?, updated_at = ? "
                "WHERE practice_item_id = ?",
                (1 if active else 0, content_hash, now, practice_item_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    def upsert_practice_item_state(
        self,
        practice_item_id: str,
        *,
        difficulty: float | None = None,
        stability: float | None = None,
        retrievability: float | None = None,
        due_at: str | None = None,
        active: bool = True,
        content_hash: str | None = None,
        last_attempt_at: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO practice_item_state(
                  practice_item_id, difficulty, stability, retrievability, due_at,
                  active, content_hash, last_attempt_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(practice_item_id) DO UPDATE SET
                  difficulty = excluded.difficulty,
                  stability = excluded.stability,
                  retrievability = excluded.retrievability,
                  due_at = excluded.due_at,
                  active = excluded.active,
                  content_hash = excluded.content_hash,
                  last_attempt_at = excluded.last_attempt_at,
                  updated_at = excluded.updated_at
                """,
                (
                    practice_item_id,
                    difficulty,
                    stability,
                    retrievability,
                    due_at,
                    1 if active else 0,
                    content_hash,
                    last_attempt_at,
                    now,
                ),
            )
            connection.commit()

    def inactive_practice_item_ids(self, practice_item_ids: Iterable[str]) -> frozenset[str]:
        """The given items whose scheduling row exists and is inactive."""

        ids = sorted({str(value) for value in practice_item_ids})
        if not ids:
            return frozenset()
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT practice_item_id FROM practice_item_state "
                f"WHERE active = 0 AND practice_item_id IN ({placeholders})",
                ids,
            ).fetchall()
        return frozenset(str(row["practice_item_id"]) for row in rows)

    def keep_practice_items_inactive(self, practice_item_ids: Iterable[str]) -> int:
        """Close the given items' rows again after replay rewrote them active.

        Only the flag moves: the replayed scheduling columns and the row's
        stamp stay as replay wrote them. Returns the rows changed.
        """

        ids = sorted({str(value) for value in practice_item_ids})
        if not ids:
            return 0
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as connection:
            cursor = connection.execute(
                f"UPDATE practice_item_state SET active = 0 "
                f"WHERE active = 1 AND practice_item_id IN ({placeholders})",
                ids,
            )
            connection.commit()
        return int(cursor.rowcount)

    def set_practice_item_active(
        self, practice_item_id: str, *, active: bool, clock: Clock | None = None
    ) -> None:
        """Flip only the active flag, preserving scheduling state on the row."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE practice_item_state SET active = ?, updated_at = ? WHERE practice_item_id = ?",
                (1 if active else 0, now, practice_item_id),
            )
            if cursor.rowcount == 0:
                connection.execute(
                    """
                    INSERT INTO practice_item_state(practice_item_id, active, updated_at)
                    VALUES (?, ?, ?)
                    """,
                    (practice_item_id, 1 if active else 0, now),
                )
            connection.commit()

    def deactivate_practice_item_serving(
        self, practice_item_id: str, *, clock: Clock | None = None
    ) -> dict[str, int]:
        """Atomically close every serving door for one terminal item."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            state = connection.execute(
                """
                UPDATE practice_item_state
                   SET active = 0, updated_at = ?
                 WHERE practice_item_id = ?
                """,
                (now, practice_item_id),
            )
            if state.rowcount == 0:
                connection.execute(
                    """
                    INSERT INTO practice_item_state(
                      practice_item_id, active, updated_at
                    ) VALUES (?, 0, ?)
                    """,
                    (practice_item_id, now),
                )
            followups = connection.execute(
                """
                UPDATE followup_tasks
                   SET status = 'expired', updated_at = ?
                 WHERE selected_item_id = ?
                   AND status IN ('pending', 'served')
                """,
                (now, practice_item_id),
            )
            checkpoints = connection.execute(
                """
                DELETE FROM session_checkpoints
                 WHERE current_practice_item_id = ?
                """,
                (practice_item_id,),
            )
            connection.commit()
        return {
            "expired_followups": int(followups.rowcount),
            "cleared_checkpoints": int(checkpoints.rowcount),
        }

    def mastery_state(self, learning_object_id: str) -> MasteryState | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM learning_object_mastery WHERE learning_object_id = ?",
                (learning_object_id,),
            ).fetchone()
        return _mastery_state(row) if row is not None else None

    def mastery_states(self) -> dict[str, MasteryState]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM learning_object_mastery").fetchall()
        return {row["learning_object_id"]: _mastery_state(row) for row in rows}

    def upsert_mastery_state(
        self,
        mastery: MasteryState,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO learning_object_mastery(
                  learning_object_id, logit_mean, logit_variance, evidence_count,
                  last_evidence_at, algorithm_version, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(learning_object_id) DO UPDATE SET
                  logit_mean = excluded.logit_mean,
                  logit_variance = excluded.logit_variance,
                  evidence_count = excluded.evidence_count,
                  last_evidence_at = excluded.last_evidence_at,
                  algorithm_version = excluded.algorithm_version,
                  updated_at = excluded.updated_at
                """,
                (
                    mastery.learning_object_id,
                    mastery.logit_mean,
                    mastery.logit_variance,
                    mastery.evidence_count,
                    mastery.last_evidence_at,
                    mastery.algorithm_version,
                    mastery.updated_at,
                ),
            )
            connection.commit()

    def record_deferred_regrade(
        self,
        *,
        attempt_id: str,
        new_evidence_rows: Iterable[Mapping[str, Any]],
        superseded_by_evidence_id: str,
        mastery_state: MasteryState,
        attempt_update: Mapping[str, Any],
        content_events: Iterable[Mapping[str, Any]] = (),
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            for row in new_evidence_rows:
                self._insert_grading_evidence(connection, attempt_id, row)
            connection.execute(
                """
                UPDATE grading_evidence
                SET superseded_at = ?, superseded_by_evidence_id = ?
                WHERE attempt_id = ? AND grader_tier = 1 AND superseded_at IS NULL
                """,
                (now, superseded_by_evidence_id, attempt_id),
            )
            connection.execute(
                """
                UPDATE practice_attempts
                SET rubric_score = ?,
                    correctness = ?,
                    grader_confidence = ?,
                    manual_review = ?,
                    manual_review_reason = ?,
                    error_type = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    attempt_update["rubric_score"],
                    attempt_update["correctness"],
                    attempt_update["grader_confidence"],
                    1 if attempt_update.get("manual_review") else 0,
                    attempt_update.get("manual_review_reason"),
                    attempt_update.get("error_type"),
                    now,
                    attempt_id,
                ),
            )
            self._upsert_mastery_state_record(connection, mastery_state)
            for event in content_events:
                connection.execute(
                    """
                    INSERT INTO content_events(
                      id, change_batch_id, event_type, subject, entity_type,
                      entity_id, origin, review_status, summary, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event["id"],
                        event.get("change_batch_id"),
                        event["event_type"],
                        event.get("subject"),
                        event["entity_type"],
                        event["entity_id"],
                        event.get("origin", "codex"),
                        event.get("review_status", "accepted"),
                        event.get("summary"),
                        event["created_at"],
                    ),
                )
            connection.commit()

    @staticmethod
    def _record_text_provenance(connection: Any, kind: str, record_id: str, text: Any, record: Any,
                                writer: str, clock: Clock | None) -> None:
        """One write-time provenance row for a text this transaction writes
        (diagnosis input provenance), when its writer passed a record."""

        if record is None or text is None:
            return
        from learnloop.db.stores.write_provenance import record_text_write

        record_text_write(connection, kind=kind, record_id=record_id, text=text, writer=writer, record=record,
                          clock=clock)

    def facet_ids_with_recall_evidence(self) -> set[str]:
        """Facet ids with legacy per-LO recall evidence (mvp-0.6 first-touch lock).

        Reads only the legacy table on purpose: canonical mvp-0.7 facets are NOT
        first-touch-locked (§3.4 — that would defeat the grace window). They lock
        through the independence gate in ``_facet_independence_locked`` (distinct
        surface groups / independent mass / active-goal scope) instead.
        """

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT DISTINCT facet_id FROM evidence_facet_recall_state"
            ).fetchall()
        return {str(row["facet_id"]) for row in rows}

    # -- Misconception candidates (KM4 §10.3 promotion discipline) -----------

    def _projected_causal_candidates(
        self,
        learning_object_id: str,
        *,
        statement_normalized: str | None = None,
    ) -> list[dict[str, Any]]:
        """Compatibility projection over P1's single hypothesis owner."""

        # Slice 2 T1: the recurrence-group map (empty unless the successor is
        # active) makes merged statement classes one group; singleton classes
        # keep their exact key.
        groups = self.recurrence_group_map()
        heads = self.causal_hypotheses_for_learning_object(
            learning_object_id,
            statuses=("candidate", "validated"),
            statement_normalized=statement_normalized,
            groups=groups,
        )
        # Slice 1 §7.6: every grouping goes through the recurrence-key seam.
        validated_statements = {
            recurrence_key(row, groups)
            for row in heads
            if row["status"] == "validated"
        }
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in heads:
            if row["status"] != "candidate":
                continue
            if row.get("cause_scope") != "learner_state":
                # Content/instrument-scoped (and legacy "unknown") causes are
                # not candidate learner beliefs and never reach the repair
                # offer. Deliberate — but never silent again (G11): the
                # learner-derived defaults now land as learner_state at mint
                # time, so anything dropped here was explicitly scoped away.
                logging.getLogger(__name__).debug(
                    "projected-candidate filter dropped hypothesis %s "
                    "(cause_scope=%r, learning_object=%s)",
                    row.get("id"),
                    row.get("cause_scope"),
                    learning_object_id,
                )
                continue
            normalized = recurrence_key(row, groups)
            if normalized in validated_statements:
                continue
            grouped.setdefault(normalized, []).append(row)
        attempt_ids = sorted(
            {
                str(member["attempt_id"])
                for members in grouped.values()
                for member in members
            }
        )
        concepts_by_attempt: dict[str, Any] = {}
        if attempt_ids:
            placeholders = ",".join("?" for _ in attempt_ids)
            with self.connection() as connection:
                attempt_rows = connection.execute(
                    f"""
                    SELECT id, concept FROM practice_attempts
                     WHERE id IN ({placeholders})
                    """,
                    attempt_ids,
                ).fetchall()
            concepts_by_attempt = {
                str(row["id"]): row["concept"] for row in attempt_rows
            }
        projections: list[dict[str, Any]] = []
        for normalized, members in grouped.items():
            members.sort(
                key=lambda row: (
                    str(row.get("created_at") or ""),
                    str(row["id"]),
                )
            )
            representative = members[0]
            source_error_event_ids: list[str] = []
            surface_families: set[str] = set()
            item_ids: set[str] = set()
            facet_ids: set[str] = set()
            signatures: list[str] = []
            severities: list[float] = []
            target_facet: str | None = None
            confused_with_facet: str | None = None
            for member in members:
                evidence = member.get("evidence")
                evidence = evidence if isinstance(evidence, Mapping) else {}
                applicability = member.get("applicability")
                applicability = (
                    applicability if isinstance(applicability, Mapping) else {}
                )
                event_id = member.get("error_event_id")
                if event_id and str(event_id) not in source_error_event_ids:
                    source_error_event_ids.append(str(event_id))
                surface = applicability.get("surface_family")
                if surface:
                    surface_families.add(str(surface))
                item_id = applicability.get("practice_item_id")
                if item_id:
                    item_ids.add(str(item_id))
                target_ref = member.get("target_ref")
                if (
                    isinstance(target_ref, Mapping)
                    and target_ref.get("kind") == "facet_capability"
                ):
                    target_facet = target_facet or str(
                        target_ref.get("facet_id") or ""
                    )
                    if target_ref.get("facet_id"):
                        facet_ids.add(str(target_ref["facet_id"]))
                contrast = evidence.get("facet_contrast")
                if isinstance(contrast, Mapping):
                    target_facet = target_facet or contrast.get("target_facet")
                    confused_with_facet = (
                        confused_with_facet
                        or contrast.get("confused_with_facet")
                    )
                signature = evidence.get("preregistered_signature")
                if signature and str(signature) not in signatures:
                    signatures.append(str(signature))
                severity = evidence.get("severity")
                if isinstance(severity, (int, float)):
                    severities.append(float(severity))
            latest = members[-1]
            latest_evidence = latest.get("evidence")
            latest_evidence = (
                latest_evidence
                if isinstance(latest_evidence, Mapping)
                else {}
            )
            projections.append(
                {
                    "id": representative["id"],
                    "learning_object_id": learning_object_id,
                    "concept_id": concepts_by_attempt.get(
                        str(representative["attempt_id"])
                    ),
                    "statement": representative["statement"],
                    "statement_normalized": normalized,
                    "signature": signatures[0] if signatures else None,
                    # Compatibility-only projection for pre-P1 consumers. The
                    # causal hypothesis itself keeps mechanism NULL until an
                    # operation cluster earns a taxonomy id.
                    "mechanism": latest.get("mechanism")
                    or latest_evidence.get("error_type"),
                    "operation": latest.get("operation"),
                    "target_facet": target_facet,
                    "confused_with_facet": confused_with_facet,
                    "facet_ids": sorted(facet_ids),
                    "source_error_event_ids": source_error_event_ids,
                    "surface_families": sorted(surface_families),
                    "item_ids": sorted(item_ids),
                    "occurrence_count": len(members),
                    "severity": max(severities, default=0.0),
                    "status": "candidate",
                    "promoted_misconception_id": None,
                    "promotion_reason": None,
                    "created_at": representative["created_at"],
                    "updated_at": latest["created_at"],
                    "causal_hypothesis_ids": [
                        member["id"] for member in members
                    ],
                    "projection": "causal_hypotheses",
                }
            )
        return sorted(
            projections,
            key=lambda row: (str(row["created_at"]), str(row["id"])),
        )

    def misconception_candidate_by_normalized(
        self, learning_object_id: str, statement_normalized: str
    ) -> dict[str, Any] | None:
        """The open candidate for one normalized statement on an LO, if any.

        ``statement_normalized`` may be a raw normalized statement or a
        recurrence key; a statement whose class was merged (Slice 2 T1)
        resolves to its group's candidate.
        """

        groups = self.recurrence_group_map()
        key = key_for_statement(statement_normalized, groups)
        projected = next(
            (
                row
                for row in self._projected_causal_candidates(
                    learning_object_id,
                    statement_normalized=key,
                )
                if recurrence_key(row, groups) == key
            ),
            None,
        )
        if projected is not None:
            return projected

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM misconception_candidates
                WHERE learning_object_id = ? AND statement_normalized = ?
                  AND status = 'candidate'
                ORDER BY created_at, id
                LIMIT 1
                """,
                (learning_object_id, statement_normalized),
            ).fetchone()
        return _decode_misconception_candidate(row) if row is not None else None

    def misconception_candidates_for_learning_object(
        self, learning_object_id: str, statuses: Iterable[str] = ("candidate",)
    ) -> list[dict[str, Any]]:
        status_list = list(statuses)
        placeholders = ",".join("?" for _ in status_list) or "''"
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM misconception_candidates
                WHERE learning_object_id = ? AND status IN ({placeholders})
                ORDER BY created_at, id
                """,
                (learning_object_id, *status_list),
            ).fetchall()
        legacy = [_decode_misconception_candidate(row) for row in rows]
        projected = (
            self._projected_causal_candidates(learning_object_id)
            if "candidate" in status_list
            else []
        )
        groups = self.recurrence_group_map()
        projected_normalized = {recurrence_key(row, groups) for row in projected}
        return [
            *projected,
            *[
                row
                for row in legacy
                if recurrence_key(row, groups) not in projected_normalized
            ],
        ]

    def update_misconception_candidate(
        self,
        candidate_id: str,
        *,
        severity: float | None = None,
        occurrence_count: int | None = None,
        append_source_error_event_ids: Iterable[str] | None = None,
        add_surface_families: Iterable[str] | None = None,
        add_item_ids: Iterable[str] | None = None,
        signature: str | None = None,
        mechanism: str | None = None,
        target_facet: str | None = None,
        confused_with_facet: str | None = None,
        status: str | None = None,
        promoted_misconception_id: str | None = None,
        promotion_reason: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any] | None:
        causal = self.causal_hypothesis(candidate_id)
        if causal is not None:
            if status not in (None, "candidate", "promoted"):
                raise ValueError("unsupported causal candidate status transition")
            unsupported_values = {
                "severity": severity,
                "occurrence_count": occurrence_count,
                "append_source_error_event_ids": (
                    list(append_source_error_event_ids)
                    if append_source_error_event_ids is not None
                    else None
                ),
                "add_surface_families": (
                    list(add_surface_families)
                    if add_surface_families is not None
                    else None
                ),
                "add_item_ids": (
                    list(add_item_ids)
                    if add_item_ids is not None
                    else None
                ),
                "signature": signature,
                "mechanism": mechanism,
                "target_facet": target_facet,
                "confused_with_facet": confused_with_facet,
            }
            supplied_unsupported = sorted(
                name
                for name, value in unsupported_values.items()
                if value is not None
            )
            if supplied_unsupported:
                raise ValueError(
                    "projected causal candidates are read-only for fields: "
                    + ", ".join(supplied_unsupported)
                )
            if status != "promoted" and (
                promoted_misconception_id is not None
                or promotion_reason is not None
            ):
                raise ValueError(
                    "promotion metadata requires status='promoted'"
                )
            if status == "promoted":
                groups = self.recurrence_group_map()
                group = recurrence_key(causal, groups)
                for member in self.causal_hypotheses_for_learning_object(
                    str(causal["learning_object_id"]),
                    statuses=("candidate",),
                ):
                    if recurrence_key(member, groups) != group:
                        continue
                    evidence = dict(member.get("evidence") or {})
                    evidence["promoted_misconception_id"] = promoted_misconception_id
                    evidence["promotion_reason"] = promotion_reason
                    self.append_causal_hypothesis(
                        episode_key=str(member["episode_key"]),
                        attempt_id=str(member["attempt_id"]),
                        error_event_id=member.get("error_event_id"),
                        learning_object_id=str(member["learning_object_id"]),
                        cause_scope=str(member["cause_scope"]),
                        statement=str(member["statement"]),
                        # The member's own class: an episode's statement is
                        # stable across its versions (a merged group spans
                        # several statement classes; Slice 2 T1).
                        statement_normalized=str(member["statement_normalized"]),
                        mechanism=member.get("mechanism"),
                        operation=member.get("operation"),
                        target_ref=member.get("target_ref"),
                        applicability=member.get("applicability"),
                        postdictive_claims=member.get("postdictive_claims")
                        or [],
                        evidence=evidence,
                        repair_class_id=member.get("repair_class_id"),
                        status="validated",
                        generation_agent_run_id=member.get(
                            "generation_agent_run_id"
                        ),
                        model=member.get("model"),
                        clock=clock,
                    )
            return self.misconception_candidate_by_id(candidate_id)
        now = utc_now_iso(clock)
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM misconception_candidates WHERE id = ?",
                (candidate_id,),
            ).fetchone()
            if row is None:
                return None
            current = _decode_misconception_candidate(row)
            source_ids = list(current["source_error_event_ids"])
            for event_id in append_source_error_event_ids or []:
                if str(event_id) not in source_ids:
                    source_ids.append(str(event_id))
            surfaces = set(current["surface_families"]) | {
                str(s) for s in (add_surface_families or [])
            }
            item_ids = set(current["item_ids"]) | {str(i) for i in (add_item_ids or [])}
            connection.execute(
                """
                UPDATE misconception_candidates
                SET severity = ?, occurrence_count = ?, source_error_event_ids_json = ?,
                    surface_families_json = ?, item_ids_json = ?, signature = ?,
                    mechanism = ?, target_facet = ?, confused_with_facet = ?,
                    status = ?, promoted_misconception_id = ?, promotion_reason = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    float(severity) if severity is not None else current["severity"],
                    int(occurrence_count) if occurrence_count is not None else current["occurrence_count"],
                    _json(source_ids),
                    _json(sorted(surfaces)),
                    _json(sorted(item_ids)),
                    signature if signature is not None else current["signature"],
                    mechanism if mechanism is not None else current["mechanism"],
                    target_facet if target_facet is not None else current["target_facet"],
                    confused_with_facet if confused_with_facet is not None else current["confused_with_facet"],
                    status if status is not None else current["status"],
                    promoted_misconception_id
                    if promoted_misconception_id is not None
                    else current["promoted_misconception_id"],
                    promotion_reason if promotion_reason is not None else current["promotion_reason"],
                    now,
                    candidate_id,
                ),
            )
            connection.commit()
        return self.misconception_candidate_by_id(candidate_id)

    def calibration_duel_pairs(self) -> list[dict[str, Any]]:
        """Matched pre-outcome learner/model predictions on ordinary cold attempts."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT a.id AS attempt_id,
                       a.answer_confidence AS answer_confidence,
                       a.correctness AS correctness,
                       c.predicted_correctness AS model_predicted_correctness
                FROM practice_attempts a
                JOIN scheduler_slate_candidates c
                  ON c.id = a.scheduler_candidate_id OR c.chosen_attempt_id = a.id
                WHERE a.answer_confidence IS NOT NULL
                  AND a.correctness IS NOT NULL
                  AND c.predicted_correctness IS NOT NULL
                  AND COALESCE(a.primed, 0) = 0
                  AND COALESCE(a.hints_used, 0) = 0
                  AND a.attempt_type NOT IN (
                    'hinted_attempt', 'guided_walkthrough', 'self_report',
                    'dont_know', 'skip'
                  )
                ORDER BY a.created_at, a.id
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def answer_confidence_presence(self, *, exclude_attempt_ids: Iterable[str] = ()) -> dict[str, int]:
        """How often an ordinary graded attempt carries a pre-answer confidence tap.

        The duel's denominator: graded, unprimed, unhinted ordinary attempts
        (the duel's own exclusions, without its scheduler-candidate match).
        ``exclude_attempt_ids`` are not graded attempts here (the caller's
        held grades).
        """

        excluded = sorted({str(value) for value in exclude_attempt_ids if value})
        exclusion = f" AND a.id NOT IN ({','.join('?' for _ in excluded)})" if excluded else ""
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS graded,
                       COALESCE(SUM(a.answer_confidence IS NOT NULL), 0) AS with_confidence
                FROM practice_attempts a
                WHERE a.correctness IS NOT NULL
                  AND COALESCE(a.primed, 0) = 0
                  AND COALESCE(a.hints_used, 0) = 0
                  AND a.attempt_type NOT IN (
                    'hinted_attempt', 'guided_walkthrough', 'self_report',
                    'dont_know', 'skip'
                  )
                """
                + exclusion,
                excluded,
            ).fetchone()
        return {"graded_attempts": int(row["graded"]), "with_confidence": int(row["with_confidence"])}

    def gate_training_rows(self) -> list[dict[str, Any]]:
        """Every persisted gate evaluation LEFT JOINed to its usefulness rating
        (via gate_attempt_id) — the gate fitter's raw input, oldest first."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT s.attempt_id, s.gate_diagnostics_json, s.created_at,
                       r.useful AS rating_useful, r.source AS rating_source
                FROM attempt_surprise s
                LEFT JOIN followup_ratings r ON r.gate_attempt_id = s.attempt_id
                WHERE s.gate_diagnostics_json IS NOT NULL
                ORDER BY s.created_at ASC, s.attempt_id ASC
                """
            ).fetchall()
        return [
            {
                "attempt_id": row["attempt_id"],
                "created_at": row["created_at"],
                "gate_diagnostics": _loads(row["gate_diagnostics_json"], None),
                "rating_useful": None if row["rating_useful"] is None else bool(row["rating_useful"]),
                "rating_source": row["rating_source"],
            }
            for row in rows
        ]

    # ── Tutor Q&A question events ─────────────────────────────────────────

    def insert_question_event(self, event: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        """Append a learner question. Q10 (diagnosis input provenance): it
        records the item contract (revision) it was asked about: the one the
        caller names (the item as presented), else, for a question asked
        about a graded attempt, the attempt's pinned contract; None on no
        item.

        RO0's fields (rows 1 to 3: ``reveal_state_json`` and the generating
        process it fills) are never in the row's insert (landing ruling R1):
        they follow in their own savepoint, so a refused receipt leaves the
        question, and the answer it waits for, standing."""

        from learnloop.db.stores import router_objective as receipts

        event, receipt = receipts.split_receipt("question_events", event)
        event_id = str(event.get("id") or new_ulid())
        now = event.get("created_at") or utc_now_iso(clock)
        with self.connection() as connection:
            contract = event.get("assessment_contract_version_id")
            if contract is None and event.get("attempt_id") and event.get("practice_item_id"):
                from learnloop.db.stores.write_provenance import pinned_contract_ids

                contract = pinned_contract_ids(
                    connection, {str(event["attempt_id"]): str(event["practice_item_id"])}
                ).get(str(event["attempt_id"]))
            if not event.get("practice_item_id"):
                contract = None
            connection.execute(
                """
                INSERT INTO question_events(
                  id, context, note_id, practice_item_id, attempt_id, session_id,
                  question_md, answer_md, question_type, facets_json,
                  hint_equivalent, leak_suspected, rating, seconds_into_attempt,
                  provider, answer_status,
                  preceding_tutor_move, scaffold_level, warning_state, learner_mode,
                  question_opportunity, hints_used_before, direct_explanation_request,
                  attempt_progress, signal_channel, source_context_json, created_at,
                  assessment_contract_version_id, answer_mode
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    event["context"],
                    event.get("note_id"),
                    event.get("practice_item_id"),
                    event.get("attempt_id"),
                    event.get("session_id"),
                    event["question_md"],
                    event.get("answer_md"),
                    event.get("question_type"),
                    _json(sorted({str(facet) for facet in event.get("facets", [])})),
                    1 if event.get("hint_equivalent") else 0,
                    1 if event.get("leak_suspected") else 0,
                    event.get("rating"),
                    event.get("seconds_into_attempt"),
                    event.get("provider"),
                    event.get("answer_status") or "answered",
                    event.get("preceding_tutor_move"),
                    event.get("scaffold_level"),
                    event.get("warning_state"),
                    event.get("learner_mode"),
                    event.get("question_opportunity"),
                    event.get("hints_used_before"),
                    1 if event.get("direct_explanation_request") else 0,
                    event.get("attempt_progress"),
                    event.get("signal_channel"),
                    (
                        _json(dict(event["source_context"]))
                        if isinstance(event.get("source_context"), Mapping)
                        else None
                    ),
                    now,
                    None if contract is None else str(contract),
                    # Adaptive difficulty AD1 (§5.11, fix round 4, V5): the
                    # reader tutor's answer mode, set once at the ask.
                    event.get("answer_mode"),
                ),
            )
            # RO0 rows 1 to 3, after the row: only a question RO0 read has them. Refused, the question stands without them.
            receipts.fill_receipt(connection, "question_events", event_id, receipt)
            connection.commit()
        return event_id

    def update_question_event_answer(
        self,
        event_id: str,
        *,
        answer_md: str | None,
        question_type: str | None,
        facets: list[str] | None,
        hint_equivalent: bool,
        leak_suspected: bool,
        answer_status: str,
        signal_channel: str | None = None,
        source_context: Mapping[str, Any] | None = None,
        leak_overlap: float | None = None,
        remediation_episode_id: str | None = None,
        answered_at: str | None = None,
    ) -> bool:
        """Complete (or fail) a pending question event after the provider call.

        Second half of the two-phase write: the question row already exists
        with answer_status='pending'; this fills in the answer and the tutor's
        classification (including the §13.4 epistemic vs interaction-preference
        channel), or marks the turn 'failed' while keeping the question text as
        evidence. An answer stamps ``answered_at`` (default: now) once: the
        first completion's time is kept (adaptive difficulty AD1, migration
        213; Codex review F4)."""

        completed = answered_at or utc_now_iso()
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE question_events
                SET answer_md = ?, question_type = ?, facets_json = ?,
                    hint_equivalent = ?, leak_suspected = ?, answer_status = ?,
                    signal_channel = COALESCE(?, signal_channel),
                    source_context_json = COALESCE(?, source_context_json),
                    leak_overlap = COALESCE(?, leak_overlap),
                    remediation_episode_id = COALESCE(?, remediation_episode_id),
                    answered_at = CASE WHEN ? = 'answered' THEN COALESCE(answered_at, ?) ELSE answered_at END
                WHERE id = ?
                """,
                (
                    answer_md,
                    question_type,
                    _json(sorted({str(facet) for facet in facets})) if facets is not None else _json([]),
                    1 if hint_equivalent else 0,
                    1 if leak_suspected else 0,
                    answer_status,
                    signal_channel,
                    _json(dict(source_context)) if source_context is not None else None,
                    leak_overlap,
                    remediation_episode_id,
                    answer_status,
                    completed,
                    event_id,
                ),
            )
            connection.commit()
            return cursor.rowcount > 0

    def question_events(
        self,
        *,
        context: str | None = None,
        note_id: str | None = None,
        practice_item_id: str | None = None,
        attempt_id: str | None = None,
        session_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
        answer_status: str | None = None,
        resolution: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM question_events"
        clauses: list[str] = []
        parameters: list[Any] = []
        for column, value in (
            ("context", context),
            ("note_id", note_id),
            ("practice_item_id", practice_item_id),
            ("attempt_id", attempt_id),
            ("session_id", session_id),
            ("answer_status", answer_status),
            ("resolution", resolution),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                parameters.append(value)
        if since is not None:
            clauses.append("created_at >= ?")
            parameters.append(since)
        if until is not None:
            clauses.append("created_at < ?")
            parameters.append(until)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [_decode_question_event(row) for row in rows]

    def count_question_events(
        self,
        *,
        context: str | None = None,
        note_id: str | None = None,
        practice_item_id: str | None = None,
        attempt_id: str | None = None,
        session_id: str | None = None,
        since: str | None = None,
        answer_status: str | None = None,
        resolution: str | None = None,
    ) -> int:
        return len(
            self.question_events(
                context=context,
                note_id=note_id,
                practice_item_id=practice_item_id,
                attempt_id=attempt_id,
                session_id=session_id,
                since=since,
                answer_status=answer_status,
                resolution=resolution,
            )
        )

    def question_event(self, event_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM question_events WHERE id = ?", (event_id,)
            ).fetchone()
        return _decode_question_event(row) if row is not None else None

    def set_question_event_rating(self, event_id: str, *, useful: bool) -> bool:
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE question_events SET rating = ? WHERE id = ?",
                (1 if useful else 0, event_id),
            )
            connection.commit()
            return cursor.rowcount > 0

    def set_question_event_resolution(self, event_id: str, *, resolution: str) -> bool:
        """Learner-facing queue state (migration 102): open | resolved | dismissed."""

        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE question_events SET resolution = ? WHERE id = ?",
                (resolution, event_id),
            )
            connection.commit()
            return cursor.rowcount > 0

    def count_hint_equivalent_question_events(
        self,
        practice_item_id: str,
        session_id: str | None,
        *,
        since: str | None = None,
        until: str | None = None,
        item_window_only: bool = False,
    ) -> int:
        """Substantive questions on this item in the hint-equivalence window.

        Questions on this (item, session) newer than ``since`` (typically the
        previous attempt on the item) and, when ``until`` is given, at or before
        it (for reconstructing the count post hoc).

        A Reader question bound to the item by a workbench session
        (``context = 'reader'`` with an item: only RW1c's server-derived
        binding writes one, ``ITEM_WINDOW_QUESTION_CONTEXTS``) counts in the
        ITEM window whatever its practice session, or none: the learner can
        ask before any practice session is open, or in one that ends before
        they submit in the next, and the help is still on the item (RW1c fix
        round 4, F1, the rule RW2b's held help already follows). The window
        start is the item's last attempt, so whichever attempt of the item
        commits next counts it once and the window then moves past it.
        ``item_window_only`` counts only those (a submit that will open its
        own practice session sees no other session's practice rows).

        Deliberately NOT filtered by context. A mechanism question asked from
        the *feedback* screen — where the graded solution is already on screen —
        helps the next attempt on the same item at least as much as the same
        question asked mid-attempt; gating on ``context = 'practice'`` let that
        help land as clean unassisted evidence. ``hint_equivalent`` is set by
        ``tutor_qa.ask_question`` for every context where a practice item is
        bound, so the flag alone carries the policy now."""

        query = (
            "SELECT COUNT(*) AS n FROM question_events "
            "WHERE hint_equivalent = 1 AND practice_item_id = ?"
        )
        parameters: list[Any] = [practice_item_id]
        # The window's session rule, shared with the learner field's link
        # from a question to the attempt it preceded (fix round 5, R3).
        clause, clause_parameters = hint_window.session_clause(session_id, item_window_only=item_window_only)
        query += clause
        parameters.extend(clause_parameters)
        if since is not None:
            query += " AND created_at > ?"
            parameters.append(since)
        if until is not None:
            query += " AND created_at <= ?"
            parameters.append(until)
        with self.connection() as connection:
            row = connection.execute(query, parameters).fetchone()
        return int(row["n"]) if row is not None else 0

    # ── Reveal ledger (migration 154) ─────────────────────────────────────

    def insert_reveal_event(
        self, event: Mapping[str, Any], *, clock: Clock | None = None
    ) -> str:
        """Append one answer-exposure entry to the cross-channel reveal ledger.

        Every surface that can hand a learner part of a graded solution writes
        here — tutor answers, repair-suggestion displays, guided redos, source
        review — so the submit path can ask one question ("how much of this
        item's answer has been exposed since the last attempt?") instead of
        re-deriving it per channel."""

        event_id = str(event.get("id") or new_ulid())
        amount = max(0.0, min(1.0, float(event.get("amount") or 0.0)))
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO reveal_events(
                  id, practice_item_id, learning_object_id, remediation_episode_id,
                  source_kind, amount, basis, question_event_id, attempt_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    str(event["practice_item_id"]),
                    event.get("learning_object_id"),
                    event.get("remediation_episode_id"),
                    str(event["source_kind"]),
                    amount,
                    event.get("basis"),
                    event.get("question_event_id"),
                    event.get("attempt_id"),
                    event.get("created_at") or utc_now_iso(clock),
                ),
            )
            connection.commit()
        return event_id

    def reveal_events(
        self,
        *,
        practice_item_id: str | None = None,
        remediation_episode_id: str | None = None,
        source_kind: str | None = None,
        attempt_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        parameters: list[Any] = []
        for column, value in (
            ("practice_item_id", practice_item_id),
            ("remediation_episode_id", remediation_episode_id),
            ("source_kind", source_kind),
            ("attempt_id", attempt_id),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                parameters.append(value)
        if since is not None:
            clauses.append("created_at > ?")
            parameters.append(since)
        if until is not None:
            clauses.append("created_at <= ?")
            parameters.append(until)
        query = "SELECT * FROM reveal_events"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [dict(row) for row in rows]

    def reveal_events_for_target(
        self,
        *,
        practice_item_id: str | None = None,
        learning_object_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[dict[str, Any]]:
        """Reveals on this item OR anywhere in this learning object (OR, not AND).

        The cold lane's question is wider than one item: a reveal on the cold
        item is an answer leak, and a reveal elsewhere in the same learning
        object is material exposure the receipt has to see before it can claim
        isolation. Both arrive in one time-bounded, index-backed read so a
        caller cannot accidentally scan only half of it. Window convention
        matches ``total_reveal_amount``: ``since`` exclusive, ``until``
        inclusive. Ordered oldest first."""

        clauses: list[str] = []
        parameters: list[Any] = []
        targets: list[str] = []
        if practice_item_id is not None:
            targets.append("practice_item_id = ?")
            parameters.append(practice_item_id)
        if learning_object_id is not None:
            targets.append("learning_object_id = ?")
            parameters.append(learning_object_id)
        if not targets:
            return []
        clauses.append("(" + " OR ".join(targets) + ")")
        if since is not None:
            clauses.append("created_at > ?")
            parameters.append(since)
        if until is not None:
            clauses.append("created_at <= ?")
            parameters.append(until)
        query = (
            "SELECT * FROM reveal_events WHERE "
            + " AND ".join(clauses)
            + " ORDER BY created_at, id"
        )
        with self.connection() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [dict(row) for row in rows]

    def total_reveal_amount(
        self,
        practice_item_id: str,
        *,
        since: str | None = None,
        until: str | None = None,
        linked_attempt_id: str | None = None,
        linked_kinds: Sequence[str] = (),
        routine_basis_prefixes: Sequence[str] = (),
        routine_covered_from: str | None = None,
    ) -> float:
        """Summed reveal amount for one item in a window.

        Same window convention as
        ``count_hint_equivalent_question_events``: ``since`` is exclusive (the
        previous attempt's timestamp, whose evidence already absorbed anything
        before it) and ``until`` is inclusive.

        ``linked_attempt_id``/``linked_kinds``: rows of those kinds linked to
        that attempt (the one at ``since``) were written after it by
        construction, so they count even when stamped in its own second.

        ``routine_basis_prefixes``/``routine_covered_from`` (UX Phase 4): an
        ``answer_display`` row whose basis starts with one of the prefixes (the
        plain surface's routine displays) counts by its coverage instead of the
        window: when stamped at or after ``routine_covered_from``, whatever
        attempts came between (a full answer still on screen after the last
        attempt is an exposure for the next). Every other row keeps the window.
        A submission's own disclosure is subtracted by the caller, which parses
        each row's identity (``reveal_ledger.is_own_disclosure``)."""

        def prefix_match(prefixes: Sequence[str]) -> tuple[str, list[Any]]:
            # A prefix match without LIKE (its "_" is a wildcard).
            clause = " OR ".join("substr(COALESCE(basis, ''), 1, ?) = ?" for _ in prefixes)
            values: list[Any] = []
            for prefix in prefixes:
                values.extend([len(prefix), prefix])
            return clause, values

        window = ""
        window_parameters: list[Any] = []
        if since is not None and linked_attempt_id is not None and linked_kinds:
            marks = ", ".join("?" for _ in linked_kinds)
            window = "(created_at > ? OR (attempt_id = ? AND source_kind IN (" + marks + ") AND created_at >= ?))"
            window_parameters = [since, linked_attempt_id, *linked_kinds, since]
        elif since is not None:
            window = "created_at > ?"
            window_parameters = [since]

        query = "SELECT COALESCE(SUM(amount), 0.0) AS total FROM reveal_events WHERE practice_item_id = ?"
        parameters: list[Any] = [practice_item_id]
        if until is not None:
            query += " AND created_at <= ?"
            parameters.append(until)
        if routine_basis_prefixes and routine_covered_from is not None:
            routine_clause, routine_values = prefix_match(routine_basis_prefixes)
            routine = f"(source_kind = 'answer_display' AND ({routine_clause}))"
            query += (
                f" AND (({routine} AND created_at >= ?)"
                f" OR (NOT {routine}" + (f" AND {window}" if window else "") + "))"
            )
            parameters.extend([*routine_values, routine_covered_from, *routine_values, *window_parameters])
        elif window:
            query += f" AND {window}"
            parameters.extend(window_parameters)
        with self.connection() as connection:
            row = connection.execute(query, parameters).fetchone()
        return float(row["total"]) if row is not None else 0.0

    def question_counts_by_facet(self) -> dict[str, int]:
        """Total question_events touching each classified facet."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT facets_json FROM question_events WHERE facets_json IS NOT NULL"
            ).fetchall()
        counts: dict[str, int] = {}
        for row in rows:
            for facet in _loads(row["facets_json"], []):
                counts[str(facet)] = counts.get(str(facet), 0) + 1
        return counts

    def set_question_event_saved_note(self, event_id: str, note_id: str | None) -> bool:
        """Persist the tutor-turn -> saved-note link (migration 027, spec §5).

        Written by ``save_tutor_answer_note`` so the "saved" UI state survives a
        remount and ``get_tutor_transcript`` can surface it."""

        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE question_events SET saved_note_id = ? WHERE id = ?",
                (note_id, event_id),
            )
            connection.commit()
            return cursor.rowcount > 0

    # --- question_promotions (spec_tutor_promotion.md §5) ----------------------

    def insert_question_promotion(
        self,
        *,
        question_event_id: str,
        intent: str,
        route: str,
        attributed_facets: list[str] | None = None,
        question_nature: str | None = None,
        attempted_in_thread: bool | None = None,
        learner_claim_id: str | None = None,
        intervention_need_id: str | None = None,
        proposed_patch_id: str | None = None,
        saved_note_id: str | None = None,
        existing_practice_item_id: str | None = None,
        created_practice_item_id: str | None = None,
        created_learning_object_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Insert the promotion ledger row for a tutor turn (§4 step 4).

        Idempotency is the caller's contract: the PK is ``question_event_id``,
        so re-promoting an already-promoted turn raises IntegrityError — the
        promotion service checks ``question_promotion(event_id)`` first."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO question_promotions(
                  question_event_id, intent, attributed_facets_json, question_nature,
                  attempted_in_thread, learner_claim_id, intervention_need_id,
                  proposed_patch_id, saved_note_id, existing_practice_item_id,
                  created_practice_item_id, created_learning_object_id, route,
                  created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    question_event_id,
                    intent,
                    _json(list(attributed_facets)) if attributed_facets is not None else None,
                    question_nature,
                    None if attempted_in_thread is None else (1 if attempted_in_thread else 0),
                    learner_claim_id,
                    intervention_need_id,
                    proposed_patch_id,
                    saved_note_id,
                    existing_practice_item_id,
                    created_practice_item_id,
                    created_learning_object_id,
                    route,
                    now,
                    now,
                ),
            )
            connection.commit()
        return question_event_id

    def update_question_promotion(
        self,
        question_event_id: str,
        *,
        route: Any = _UNSET,
        attributed_facets: Any = _UNSET,
        question_nature: Any = _UNSET,
        attempted_in_thread: Any = _UNSET,
        learner_claim_id: Any = _UNSET,
        intervention_need_id: Any = _UNSET,
        proposed_patch_id: Any = _UNSET,
        saved_note_id: Any = _UNSET,
        existing_practice_item_id: Any = _UNSET,
        created_practice_item_id: Any = _UNSET,
        created_learning_object_id: Any = _UNSET,
        clock: Clock | None = None,
    ) -> bool:
        """Fill created ids / transition the route on an existing promotion row.

        Only the supplied fields are written (``_UNSET`` sentinel distinguishes
        "leave unchanged" from an explicit ``None``); ``updated_at`` always
        advances."""

        assignments: list[str] = []
        parameters: list[Any] = []

        def _set(column: str, value: Any) -> None:
            assignments.append(f"{column} = ?")
            parameters.append(value)

        if route is not _UNSET:
            _set("route", route)
        if attributed_facets is not _UNSET:
            _set(
                "attributed_facets_json",
                _json(list(attributed_facets)) if attributed_facets is not None else None,
            )
        if question_nature is not _UNSET:
            _set("question_nature", question_nature)
        if attempted_in_thread is not _UNSET:
            _set(
                "attempted_in_thread",
                None if attempted_in_thread is None else (1 if attempted_in_thread else 0),
            )
        if learner_claim_id is not _UNSET:
            _set("learner_claim_id", learner_claim_id)
        if intervention_need_id is not _UNSET:
            _set("intervention_need_id", intervention_need_id)
        if proposed_patch_id is not _UNSET:
            _set("proposed_patch_id", proposed_patch_id)
        if saved_note_id is not _UNSET:
            _set("saved_note_id", saved_note_id)
        if existing_practice_item_id is not _UNSET:
            _set("existing_practice_item_id", existing_practice_item_id)
        if created_practice_item_id is not _UNSET:
            _set("created_practice_item_id", created_practice_item_id)
        if created_learning_object_id is not _UNSET:
            _set("created_learning_object_id", created_learning_object_id)

        _set("updated_at", utc_now_iso(clock))
        parameters.append(question_event_id)
        with self.connection() as connection:
            cursor = connection.execute(
                f"UPDATE question_promotions SET {', '.join(assignments)} WHERE question_event_id = ?",
                parameters,
            )
            connection.commit()
            return cursor.rowcount > 0

    def question_promotion(self, event_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM question_promotions WHERE question_event_id = ?",
                (event_id,),
            ).fetchone()
        return _decode_question_promotion(row) if row is not None else None

    def question_promotions(self) -> list[dict[str, Any]]:
        """All promotion rows, oldest first (requested-floor + signal joins)."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM question_promotions ORDER BY created_at, question_event_id"
            ).fetchall()
        return [_decode_question_promotion(row) for row in rows]

    def question_promotions_for_events(self, event_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
        """Promotion rows keyed by question_event_id, for the tutor transcript.

        Returns a dict so the transcript can attach promotion state per turn in
        one query (empty when no ids are given)."""

        ids = [str(event_id) for event_id in event_ids]
        if not ids:
            return {}
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM question_promotions WHERE question_event_id IN ({placeholders})",
                ids,
            ).fetchall()
        return {row["question_event_id"]: _decode_question_promotion(row) for row in rows}

    def question_promotions_for_patch(self, patch_id: str) -> list[dict[str, Any]]:
        """Promotion rows awaiting or completed through one proposal patch."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM question_promotions
                WHERE proposed_patch_id = ?
                ORDER BY created_at, question_event_id
                """,
                (patch_id,),
            ).fetchall()
        return [_decode_question_promotion(row) for row in rows]

    # --- durable question-promotion requests (migration 117) ------------------

    def insert_question_promotion_request(
        self,
        *,
        question_event_id: str,
        intent: str,
        subject_id: str | None = None,
        learning_object_id: str | None = None,
        status: str = "queued",
        stage: str = "queued",
        batch_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO question_promotion_requests(
                  question_event_id, intent, subject_id, learning_object_id,
                  status, stage, batch_id, promotion_route, error_code,
                  error_message, retryable, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, 0, ?, ?)
                """,
                (
                    question_event_id,
                    intent,
                    subject_id,
                    learning_object_id,
                    status,
                    stage,
                    batch_id,
                    now,
                    now,
                ),
            )
            connection.commit()
        return question_event_id

    def update_question_promotion_request(
        self,
        question_event_id: str,
        *,
        status: Any = _UNSET,
        stage: Any = _UNSET,
        batch_id: Any = _UNSET,
        promotion_route: Any = _UNSET,
        error_code: Any = _UNSET,
        error_message: Any = _UNSET,
        retryable: Any = _UNSET,
        subject_id: Any = _UNSET,
        learning_object_id: Any = _UNSET,
        clock: Clock | None = None,
    ) -> bool:
        assignments: list[str] = []
        parameters: list[Any] = []

        def _set(column: str, value: Any) -> None:
            assignments.append(f"{column} = ?")
            parameters.append(value)

        for column, value in (
            ("status", status),
            ("stage", stage),
            ("batch_id", batch_id),
            ("promotion_route", promotion_route),
            ("error_code", error_code),
            ("error_message", error_message),
            ("subject_id", subject_id),
            ("learning_object_id", learning_object_id),
        ):
            if value is not _UNSET:
                _set(column, value)
        if retryable is not _UNSET:
            _set("retryable", 1 if retryable else 0)
        _set("updated_at", utc_now_iso(clock))
        parameters.append(question_event_id)
        with self.connection() as connection:
            cursor = connection.execute(
                f"""
                UPDATE question_promotion_requests
                SET {', '.join(assignments)}
                WHERE question_event_id = ?
                """,
                parameters,
            )
            connection.commit()
        return cursor.rowcount > 0

    def question_promotion_request(self, event_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM question_promotion_requests
                WHERE question_event_id = ?
                """,
                (event_id,),
            ).fetchone()
        return _decode_question_promotion_request(row) if row is not None else None

    def question_promotion_requests_for_events(
        self, event_ids: Iterable[str]
    ) -> dict[str, dict[str, Any]]:
        ids = [str(event_id) for event_id in event_ids]
        if not ids:
            return {}
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM question_promotion_requests
                WHERE question_event_id IN ({placeholders})
                """,
                ids,
            ).fetchall()
        return {
            row["question_event_id"]: _decode_question_promotion_request(row)
            for row in rows
        }

    def retry_question_promotion_request(
        self, event_id: str, *, clock: Clock | None = None
    ) -> bool:
        """Re-open a failed durable request without losing its selected target."""

        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE question_promotion_requests
                SET status = 'queued',
                    stage = 'queued',
                    promotion_route = NULL,
                    error_code = NULL,
                    error_message = NULL,
                    retryable = 0,
                    updated_at = ?
                WHERE question_event_id = ? AND status = 'failed'
                """,
                (utc_now_iso(clock), event_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    def requested_practice_item_ids(self, *, skip_commitment_ids: Sequence[str] = ()) -> list[str]:
        """Practice items with a learner request not yet consumed by a later attempt.

        *Requested items* (spec §4a) = practice items referenced by a
        ``question_promotions`` row (``created_practice_item_id`` or
        ``existing_practice_item_id``) whose request has no attempt at or after
        that request time, oldest unconsumed request first. This deliberately
        permits "practice this again" after an earlier attempt.

        A card the learner adopted through a ``help_me_remember`` commitment (the
        reader's "write my own question") is requested too, from the moment the
        commitment first named it as a ``legacy_practice_item`` target, unless
        the commitment was retired.

        Daily-loop DL2 (intent): ``skip_commitment_ids`` leaves those
        commitments out of the ``help_me_remember`` branch (the intent
        control's own commitments: choosing Master or Keep on an item is not a
        request, spec §5.3). Empty, the query is exactly the one before DL2."""

        skip = [str(value) for value in skip_commitment_ids]
        skip_clause = (
            f"\n                    AND commitment.id NOT IN ({','.join('?' for _ in skip)})" if skip else ""
        )
        with self.connection() as connection:
            rows = connection.execute(
                """
                WITH requests AS (
                  SELECT
                    COALESCE(created_practice_item_id, existing_practice_item_id) AS item_id,
                    created_at AS requested_at
                  FROM question_promotions
                  WHERE created_practice_item_id IS NOT NULL
                     OR existing_practice_item_id IS NOT NULL
                  UNION
                  -- Learner-requested rung variants (migration 108): an applied
                  -- easier/harder variant remains requested until an attempt
                  -- consumes that particular request.
                  SELECT created_practice_item_id AS item_id, created_at AS requested_at
                  FROM rung_variant_requests
                  WHERE status = 'applied' AND created_practice_item_id IS NOT NULL
                  UNION
                  -- Learner-adopted cards (reader "write my own question"): the
                  -- commitment's first version naming the card is the request.
                  SELECT target.target_ref AS item_id, MIN(target.created_at) AS requested_at
                  FROM commitment_target_versions target
                  JOIN commitment_versions version ON version.id = target.commitment_version_id
                  JOIN commitments commitment ON commitment.id = version.commitment_id
                  WHERE target.target_kind = 'legacy_practice_item'
                    AND commitment.created_action = 'help_me_remember'
                    AND NOT EXISTS (
                      SELECT 1 FROM commitment_events event
                      WHERE event.commitment_id = commitment.id AND event.kind = 'retired'
                    )""" + skip_clause + """
                  GROUP BY commitment.id, target.target_ref
                ),
                unconsumed AS (
                  SELECT request.item_id, request.requested_at
                  FROM requests request
                  WHERE NOT EXISTS (
                    SELECT 1
                    FROM practice_attempts attempt
                    WHERE attempt.practice_item_id = request.item_id
                      AND attempt.created_at >= request.requested_at
                  )
                )
                SELECT item_id
                FROM unconsumed
                GROUP BY item_id
                ORDER BY MIN(requested_at), item_id
                """,
                skip,
            ).fetchall()
        return [row["item_id"] for row in rows]

    # --- Today queue invalidation (migration 117) ------------------------------

    def queue_revision(self) -> dict[str, Any]:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT revision, updated_at FROM queue_state WHERE singleton = 1"
            ).fetchone()
        return {
            "revision": int(row["revision"]) if row is not None else 0,
            "updated_at": row["updated_at"] if row is not None else None,
        }

    def bump_queue_revision(self, *, clock: Clock | None = None) -> int:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO queue_state(singleton, revision, updated_at)
                VALUES (1, 1, ?)
                ON CONFLICT(singleton) DO UPDATE SET
                  revision = queue_state.revision + 1,
                  updated_at = excluded.updated_at
                """,
                (now,),
            )
            row = connection.execute(
                "SELECT revision FROM queue_state WHERE singleton = 1"
            ).fetchone()
            connection.commit()
        return int(row["revision"])

    # --- rung variant requests (migration 108) --------------------------------

    def insert_rung_variant_request(self, request: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        request_id = str(request.get("id") or new_ulid())
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO rung_variant_requests(
                  id, source_practice_item_id, learning_object_id, direction,
                  source_waypoint_slug, target_waypoint_slug, target_rung_json,
                  status, attempt_id, learner_claim_id, batch_id, patch_id,
                  created_practice_item_id, failure_reason, variant_kind,
                  created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    request["source_practice_item_id"],
                    request["learning_object_id"],
                    request["direction"],
                    request["source_waypoint_slug"],
                    request["target_waypoint_slug"],
                    request["target_rung_json"],
                    request.get("status") or "pending",
                    request.get("attempt_id"),
                    request.get("learner_claim_id"),
                    request.get("batch_id"),
                    request.get("patch_id"),
                    request.get("created_practice_item_id"),
                    request.get("failure_reason"),
                    request.get("variant_kind") or request["direction"],
                    now,
                    now,
                ),
            )
            connection.commit()
        return request_id

    def rung_variant_request(self, request_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM rung_variant_requests WHERE id = ?", (request_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def rung_variant_requests(
        self, request_ids: Iterable[str]
    ) -> dict[str, dict[str, Any]]:
        """Bulk-load rung requests used by ingest progress views."""

        ids = sorted({str(request_id) for request_id in request_ids if request_id})
        if not ids:
            return {}
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM rung_variant_requests WHERE id IN ({placeholders})",
                ids,
            ).fetchall()
        return {str(row["id"]): dict(row) for row in rows}

    def update_rung_variant_request(
        self, request_id: str, *, clock: Clock | None = None, **fields: Any
    ) -> bool:
        allowed = {
            "status", "attempt_id", "learner_claim_id", "batch_id", "patch_id",
            "created_practice_item_id", "failure_reason", "variant_kind",
        }
        updates = {key: value for key, value in fields.items() if key in allowed}
        if not updates:
            return False
        assignments = ", ".join(f"{key} = ?" for key in updates)
        with self.connection() as connection:
            cursor = connection.execute(
                f"UPDATE rung_variant_requests SET {assignments}, updated_at = ? WHERE id = ?",
                (*updates.values(), utc_now_iso(clock), request_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    def retry_failed_rung_variant_request(
        self, request_id: str, *, clock: Clock | None = None
    ) -> bool:
        """Return one failed generation request to its pre-generation state.

        The learner attempt and claim are evidence from the original request and
        deliberately survive retries. Generation-owned output pointers and the
        prior failure are cleared so the same durable request can author again.
        """

        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE rung_variant_requests
                   SET status = 'pending',
                       patch_id = NULL,
                       created_practice_item_id = NULL,
                       failure_reason = NULL,
                       updated_at = ?
                 WHERE id = ? AND status = 'failed'
                """,
                (utc_now_iso(clock), request_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    def pending_rung_variant_requests(self, source_practice_item_id: str) -> list[dict[str, Any]]:
        """Non-terminal requests for one item — the per-item request lock."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM rung_variant_requests
                WHERE source_practice_item_id = ? AND status IN ('pending', 'generating')
                ORDER BY created_at, id
                """,
                (source_practice_item_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Concept animations (spec_fork_features §2)
    # ------------------------------------------------------------------

    _CONCEPT_ANIMATION_FIELDS = {
        "status", "scene_code", "scene_class", "title", "narration_md",
        "video_hash", "video_file_name", "duration_seconds", "provider",
        "model", "prompt_version", "quality", "repair_attempted",
        "failure_stage", "failure_reason", "render_stderr", "batch_id",
        "completed_at", "renderer", "storyboard_json", "video_job_ids",
    }

    def insert_concept_animation(self, row: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        animation_id = str(row.get("id") or new_ulid())
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO concept_animations(
                  id, concept_id, learning_object_id, status, scene_code,
                  scene_class, title, narration_md, video_hash, video_file_name,
                  duration_seconds, provider, model, prompt_version, quality,
                  repair_attempted, failure_stage, failure_reason, render_stderr,
                  batch_id, created_at, updated_at, completed_at, renderer
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    animation_id,
                    row["concept_id"],
                    row.get("learning_object_id"),
                    row.get("status") or "queued",
                    row.get("scene_code"),
                    row.get("scene_class"),
                    row.get("title"),
                    row.get("narration_md"),
                    row.get("video_hash"),
                    row.get("video_file_name"),
                    row.get("duration_seconds"),
                    row.get("provider"),
                    row.get("model"),
                    row.get("prompt_version"),
                    row.get("quality"),
                    int(row.get("repair_attempted") or 0),
                    row.get("failure_stage"),
                    row.get("failure_reason"),
                    row.get("render_stderr"),
                    row.get("batch_id"),
                    now,
                    now,
                    row.get("completed_at"),
                    row.get("renderer") or "manim",
                ),
            )
            connection.commit()
        return animation_id

    def concept_animation(self, animation_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM concept_animations WHERE id = ?", (animation_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def update_concept_animation(
        self, animation_id: str, *, clock: Clock | None = None, **fields: Any
    ) -> bool:
        updates = {key: value for key, value in fields.items() if key in self._CONCEPT_ANIMATION_FIELDS}
        if not updates:
            return False
        assignments = ", ".join(f"{key} = ?" for key in updates)
        with self.connection() as connection:
            cursor = connection.execute(
                f"UPDATE concept_animations SET {assignments}, updated_at = ? WHERE id = ?",
                (*updates.values(), utc_now_iso(clock), animation_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    def concept_animations_for_concept(self, concept_id: str, limit: int = 10) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM concept_animations
                WHERE concept_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (concept_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def pending_concept_animations(self, concept_id: str) -> list[dict[str, Any]]:
        """Non-terminal animations for one concept — the per-concept lock."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM concept_animations
                WHERE concept_id = ? AND status IN ('queued', 'generating', 'validating', 'rendering')
                ORDER BY created_at, id
                """,
                (concept_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_learner_claim(self, claim: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        claim_id = str(claim.get("id") or new_ulid())
        created_at = str(claim.get("created_at") or utc_now_iso(clock))
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO learner_claims(
                  id, claim_type, scope_type, scope_id, evidence_family,
                  claimed_level, prior_pseudo_count, source, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    claim_id,
                    claim["claim_type"],
                    claim["scope_type"],
                    claim.get("scope_id"),
                    claim.get("evidence_family"),
                    claim["claimed_level"],
                    claim["prior_pseudo_count"],
                    claim["source"],
                    created_at,
                ),
            )
            connection.commit()
        return claim_id

    def record_learner_claim_application(self, claim_id: str, learning_object_id: str) -> int:
        """Record how many of the LO's attempts were applied when the claim was; that count.

        LP-min (a), re-review F7 (``learner_claims.applied_after_attempts``):
        called inside the claim's re-anchor transaction, so the count and the
        mastery write read one snapshot. Replay applies the claim after that
        many of the LO's attempts."""

        with self.connection() as connection:
            (count,) = connection.execute(
                "SELECT COUNT(*) FROM practice_attempts WHERE learning_object_id = ?", (learning_object_id,)
            ).fetchone()
            connection.execute(
                "UPDATE learner_claims SET applied_after_attempts = ? WHERE id = ?", (int(count), claim_id)
            )
            connection.commit()
        return int(count)

    def learner_claims(self, *, include_superseded: bool = False) -> list[dict[str, Any]]:
        """The claims in force (newest first); ``include_superseded`` adds the replaced ones.

        A claim another claim replaced (``superseded_by``, successor mvp-0.36,
        migration 225) is kept for replay only: every live reader reads the
        claims in force, which are exactly the rows the predecessor's replace
        seam left (it deleted the replaced ones). Replay passes
        ``include_superseded`` and applies each claim at its own point."""

        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM learner_claims ORDER BY created_at DESC, id").fetchall()
        claims = [dict(row) for row in rows]
        if include_superseded:
            return claims
        # Filtered here, not in SQL: a database attached below migration 225 has no such column.
        return [claim for claim in claims if claim.get("superseded_by") is None]

    def replace_learner_claim(
        self,
        claim: Mapping[str, Any],
        *,
        clock: Clock | None = None,
    ) -> str:
        """The replace seam: ``claim`` replaces the in-force claims of its source on its scope; its id.

        One source keeps one claim in force per scope (init-wizard global
        claims, rung-variant requests and too-easy/too-hard reports per LO).
        The replaced rows stay (the successor mvp-0.36), marked
        ``superseded_by`` the new claim's id in the transaction that inserts
        it, so replay can apply each at its own time."""

        with self.atomic():
            claim_id = self.insert_learner_claim(claim, clock=clock)
            query = (
                "UPDATE learner_claims SET superseded_by = ? WHERE source = ? AND scope_type = ? "
                "AND superseded_by IS NULL AND id <> ?"
            )
            params: list[Any] = [claim_id, claim["source"], claim["scope_type"], claim_id]
            if claim.get("scope_id") is not None:
                query += " AND scope_id = ?"
                params.append(claim["scope_id"])
            with self.connection() as connection:
                connection.execute(query, params)
                connection.commit()
        return claim_id

    def delete_learner_claims(
        self, *, source: str, scope_type: str, scope_id: str | None = None
    ) -> int:
        """Delete claims by (source, scope_type[, scope_id]) — the replace seam
        for init-wizard (global) and rung-variant (per-LO) re-claims.

        Below the claim-fixes successor ``covering_learner_claim`` breaks
        specificity ties by pseudo-count, then highest claimed_level, so
        re-seeding a LOWER level must remove the old row rather than append
        beside it. (From the successor on the newest claim wins the tie; the
        replace seam stays, so one source keeps one row per scope.)
        """

        query = "DELETE FROM learner_claims WHERE source = ? AND scope_type = ?"
        params: list[Any] = [source, scope_type]
        if scope_id is not None:
            query += " AND scope_id = ?"
            params.append(scope_id)
        with self.connection() as connection:
            cursor = connection.execute(query, params)
            connection.commit()
        return cursor.rowcount

    def reset_learning_object_derived_state(self, learning_object_id: str) -> None:
        with self.connection() as connection:
            attempt_ids = [
                row["id"]
                for row in connection.execute(
                    "SELECT id FROM practice_attempts WHERE learning_object_id = ?",
                    (learning_object_id,),
                ).fetchall()
            ]
            item_ids = [
                row["practice_item_id"]
                for row in connection.execute(
                    "SELECT DISTINCT practice_item_id FROM practice_attempts WHERE learning_object_id = ?",
                    (learning_object_id,),
                ).fetchall()
            ]
            connection.execute(
                "DELETE FROM learning_object_mastery WHERE learning_object_id = ?",
                (learning_object_id,),
            )
            connection.execute(
                "DELETE FROM evidence_facet_recall_state WHERE learning_object_id = ?",
                (learning_object_id,),
            )
            connection.execute(
                "DELETE FROM facet_uncertainty WHERE learning_object_id = ?",
                (learning_object_id,),
            )
            if attempt_ids:
                placeholders = ",".join("?" for _ in attempt_ids)
                connection.execute(f"DELETE FROM error_events WHERE attempt_id IN ({placeholders})", attempt_ids)
                connection.execute(f"DELETE FROM attempt_surprise WHERE attempt_id IN ({placeholders})", attempt_ids)
                # P1 diagnosis receipts live inside attempt_debug_payloads and
                # are immutable decision records, not disposable derived state.
                # replace_attempt_derived_outcome preserves them while replacing
                # the surrounding replay trace below.
                connection.execute(f"DELETE FROM ability_transition_events WHERE attempt_id IN ({placeholders})", attempt_ids)
            if item_ids:
                placeholders = ",".join("?" for _ in item_ids)
                connection.execute(f"DELETE FROM practice_item_state WHERE practice_item_id IN ({placeholders})", item_ids)
                connection.execute(
                    f"DELETE FROM practice_item_quality_state WHERE practice_item_id IN ({placeholders})",
                    item_ids,
                )
                # Derived EB difficulty posteriors are rebuilt by replay.
                # fitted_parameters is intentionally NOT cleared here: fitted
                # sets are inputs to replay, not derived state.
                connection.execute(
                    f"DELETE FROM item_parameter_state WHERE practice_item_id IN ({placeholders})",
                    item_ids,
                )
            connection.commit()

    def clear_derived_projection_tables(
        self, table_names: Iterable[str]
    ) -> dict[str, int]:
        """Atomically clear explicitly registered DERIVED projection tables.

        Dynamic table names are accepted only after exact membership validation
        against the table-role registry.  This keeps SQL ownership in the
        persistence layer while letting the rebuild registry declare families.
        """

        from learnloop.db.table_roles import TableRole, tables_for_role

        requested = tuple(sorted(set(str(table) for table in table_names)))
        unexpected = sorted(set(requested) - set(tables_for_role(TableRole.DERIVED)))
        if unexpected:
            raise ValueError(
                "cannot clear non-DERIVED tables: " + ", ".join(unexpected)
            )
        counts: dict[str, int] = {}
        with self.connection() as connection:
            for table in requested:
                counts[table] = int(
                    connection.execute(
                        f'SELECT COUNT(*) FROM "{table}"'
                    ).fetchone()[0]
                )
                connection.execute(f'DELETE FROM "{table}"')
            connection.commit()
        return counts

    def replace_attempt_derived_outcome(
        self,
        *,
        attempt: Mapping[str, Any],
        error_events: Iterable[Mapping[str, Any]],
        surprise: Mapping[str, Any],
        practice_item_state: PracticeItemState,
        mastery_state: MasteryState,
        facet_uncertainty_states: Iterable[Mapping[str, Any]] = (),
        quality_state: Mapping[str, Any] | None = None,
        ability_transition: Mapping[str, Any] | None = None,
        attempt_debug_payload: Mapping[str, Any] | None = None,
        item_parameter_state: ItemParameterState | None = None,
    ) -> None:
        with self.connection() as connection:
            prior_debug_row = connection.execute(
                """
                SELECT payload_json FROM attempt_debug_payloads
                WHERE attempt_id = ?
                """,
                (attempt["id"],),
            ).fetchone()
            prior_debug = (
                _loads(prior_debug_row["payload_json"], {})
                if prior_debug_row is not None
                else {}
            )
            next_debug = (
                dict(attempt_debug_payload)
                if attempt_debug_payload is not None
                else None
            )
            if next_debug is not None:
                prior_attribution = prior_debug.get("causal_attribution")
                prior_receipts = (
                    prior_attribution.get("diagnosis_receipts")
                    if isinstance(prior_attribution, Mapping)
                    else None
                )
                if isinstance(prior_receipts, list) and prior_receipts:
                    next_attribution = next_debug.get("causal_attribution")
                    if not isinstance(next_attribution, dict):
                        next_attribution = {}
                        next_debug["causal_attribution"] = next_attribution
                    next_attribution["diagnosis_receipts"] = [
                        dict(value)
                        for value in prior_receipts
                        if isinstance(value, Mapping)
                    ]
                    current = (
                        prior_attribution.get("diagnosis_receipt")
                        if isinstance(prior_attribution, Mapping)
                        else None
                    )
                    if isinstance(current, Mapping):
                        next_attribution["diagnosis_receipt"] = dict(current)
            connection.execute(
                """
                UPDATE practice_attempts
                SET rubric_score = ?,
                    correctness = ?,
                    confidence = ?,
                    latency_seconds = ?,
                    hints_used = ?,
                    error_type = ?,
                    grader_confidence = ?,
                    manual_review = ?,
                    manual_review_reason = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    attempt["rubric_score"],
                    attempt["correctness"],
                    attempt.get("confidence"),
                    attempt.get("latency_seconds"),
                    attempt.get("hints_used"),
                    attempt.get("error_type"),
                    attempt["grader_confidence"],
                    1 if attempt.get("manual_review") else 0,
                    attempt.get("manual_review_reason"),
                    attempt["updated_at"],
                    attempt["id"],
                ),
            )
            connection.execute("DELETE FROM error_events WHERE attempt_id = ?", (attempt["id"],))
            connection.execute("DELETE FROM attempt_surprise WHERE attempt_id = ?", (attempt["id"],))
            connection.execute("DELETE FROM attempt_debug_payloads WHERE attempt_id = ?", (attempt["id"],))
            connection.execute("DELETE FROM ability_transition_events WHERE attempt_id = ?", (attempt["id"],))
            for event in error_events:
                self._insert_error_event(connection, event)
            self._insert_attempt_surprise(connection, surprise)
            self._upsert_practice_item_state_record(connection, practice_item_state)
            self._upsert_mastery_state_record(connection, mastery_state)
            for state in facet_uncertainty_states:
                self._upsert_facet_uncertainty_state(connection, state)
            if quality_state is not None:
                self._upsert_practice_item_quality_state(connection, quality_state)
            if ability_transition is not None:
                self._upsert_ability_transition_event(connection, ability_transition)
            if item_parameter_state is not None:
                self._upsert_item_parameter_state_record(connection, item_parameter_state)
            if next_debug is not None:
                connection.execute(
                    """
                    INSERT INTO attempt_debug_payloads(
                      attempt_id, payload_json, algorithm_version, created_at
                    )
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(attempt_id) DO UPDATE SET
                      payload_json = excluded.payload_json,
                      algorithm_version = excluded.algorithm_version,
                      created_at = excluded.created_at
                    """,
                    (
                        attempt["id"],
                        _json(next_debug),
                        next_debug.get("algorithm_version", ""),
                        next_debug.get("created_at", attempt.get("created_at")),
                    ),
                )
            connection.execute("DELETE FROM learning_outcome_labels WHERE outcome_attempt_id = ?", (attempt["id"],))
            self._insert_learning_outcome_labels(
                connection,
                attempt,
                algorithm_version=surprise["algorithm_version"],
            )
            connection.commit()

    def facet_recall_state(
        self,
        learning_object_id: str,
        facet_id: str,
        practice_item_id: str | None = None,
    ) -> FacetRecallState | None:
        with self.connection() as connection:
            if practice_item_id is None:
                row = connection.execute(
                    """
                    SELECT * FROM evidence_facet_recall_state
                    WHERE learning_object_id = ? AND facet_id = ? AND practice_item_id IS NULL
                    """,
                    (learning_object_id, facet_id),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT * FROM evidence_facet_recall_state
                    WHERE learning_object_id = ? AND facet_id = ? AND practice_item_id = ?
                    """,
                    (learning_object_id, facet_id, practice_item_id),
                ).fetchone()
        return _facet_recall_state(row) if row is not None else None

    # -- KM2 canonical shared facet state (§7.1) --------------------------------
    # These read/write the canonical `facet_recall_state`, `facet_capability_evidence`,
    # and `facet_merges` tables. They are consumed only under mvp-0.7; the legacy
    # per-LO `evidence_facet_recall_state` methods above stay untouched so mvp-0.6
    # replay reproduces byte-identical state.

    def canonical_facet_recall_states(self) -> list[CanonicalFacetRecallState]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM facet_recall_state ORDER BY facet_id, capability_key, practice_item_id"
            ).fetchall()
        return [_canonical_facet_recall_state(row) for row in rows]

    def canonical_facet_recall_state(
        self,
        facet_id: str,
        capability_key: str = "shared",
        practice_item_id: str | None = None,
    ) -> CanonicalFacetRecallState | None:
        with self.connection() as connection:
            if practice_item_id is None:
                row = connection.execute(
                    """
                    SELECT * FROM facet_recall_state
                    WHERE facet_id = ? AND capability_key = ? AND practice_item_id IS NULL
                    """,
                    (facet_id, capability_key),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT * FROM facet_recall_state
                    WHERE facet_id = ? AND capability_key = ? AND practice_item_id = ?
                    """,
                    (facet_id, capability_key, practice_item_id),
                ).fetchone()
        return _canonical_facet_recall_state(row) if row is not None else None

    def facet_capability_evidence(
        self, facet_id: str, capability: str
    ) -> FacetCapabilityEvidence | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM facet_capability_evidence WHERE facet_id = ? AND capability = ?",
                (facet_id, capability),
            ).fetchone()
        return _facet_capability_evidence(row) if row is not None else None

    def facet_capability_evidence_all(self) -> list[FacetCapabilityEvidence]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM facet_capability_evidence ORDER BY facet_id, capability"
            ).fetchall()
        return [_facet_capability_evidence(row) for row in rows]

    def facet_capability_evidence_for_facet(
        self, facet_id: str
    ) -> list[FacetCapabilityEvidence]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM facet_capability_evidence WHERE facet_id = ? ORDER BY capability",
                (facet_id,),
            ).fetchall()
        return [_facet_capability_evidence(row) for row in rows]

    def facet_independence_evidence(self, facet_id: str) -> tuple[int, float]:
        """(#distinct direct surface/correlation groups, independent mass) for the
        independence-gated lock trigger (§3.4). Direct evidence only."""

        groups: set[str] = set()
        for cell in self.facet_capability_evidence_for_facet(facet_id):
            groups.update(cell.independent_surface_groups)
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT COALESCE(SUM(independent_evidence_mass), 0.0) AS mass
                FROM facet_recall_state
                WHERE facet_id = ? AND practice_item_id IS NULL
                """,
                (facet_id,),
            ).fetchone()
        return len(groups), float(row["mass"] if row is not None else 0.0)

    def canonical_observation_ledger(self) -> list[dict[str, Any]]:
        """Every graded attempt in global chronological order with its
        non-superseded grading evidence (KM2 projection input).

        Chronological across LOs so the derived canonical belief state is
        deterministic regardless of per-LO replay order; beta masses accumulate
        additively so only timestamps/consecutive-failures depend on order.  The
        read model is assembled in two bulk queries by ``db.observation_ledger``;
        no query is issued from inside the attempt loop.
        """

        with self.connection() as connection:
            # Hold one read transaction across both scans.  A concurrent grade
            # supersession must be observed wholly before or wholly after the
            # replay snapshot, never as an attempt row from one epoch and
            # evidence rows from another.
            if not connection.in_transaction:
                connection.execute("BEGIN")
            return load_canonical_observation_ledger(connection)

    def canonical_observation_ledger_v2(self) -> list[dict[str, Any]]:
        """P0.3 (§4.3) authoritative-events ledger. Extends the mvp-0.7 row with the
        administration, the ACTIVE calibrated grade interpretation/adjudication, the
        grader/calibration lineage, the target-contract pin, and quarantine state.

        The mvp-0.8 projection reads only these authoritative events; the legacy
        summary columns are never replay inputs. The base attempt/evidence shape is
        the byte-identical v1 shape so the projection loop stays shared; the P0.3
        lineage fields are ADDED (never removed) -- projector tests fail if a variant
        omits them (§9.2 bullet 3)."""

        with self.connection() as connection:
            if not connection.in_transaction:
                connection.execute("BEGIN")
            return load_authoritative_observation_ledger(connection)

    def replace_canonical_facet_state(
        self,
        *,
        recall_rows: Iterable[Mapping[str, Any]],
        capability_rows: Iterable[Mapping[str, Any]],
        algorithm_version: str,
        clock: Clock | None = None,
    ) -> None:
        """Make the canonical belief cache equal a derived projection.

        The canonical state is a pure, order-independent (beta masses accumulate
        additively) projection over the immutable observation ledger, so the
        whole projection is handed in: no per-LO reset can shear a facet shared
        across LOs. Idempotent.

        Write only on change (followups-oct31, fix 1): every load and reload
        re-projects, and almost always to the same values. Each cell is compared
        with the stored row on its value columns; a vanished cell is deleted, a
        new one inserted, a changed one updated with ``updated_at = now``, and an
        unchanged one is not touched. When nothing differs nothing is written at
        all, so a no-op reload leaves the database file (``PRAGMA data_version``)
        unchanged. ``updated_at`` therefore means "this estimate last changed
        then". A recall row's ``created_at`` is projected (its first
        observation's time) and written as projected; a capability row carries
        none, so it keeps the stored one (``now`` when the cell first appears).
        """

        now = utc_now_iso(clock)
        recall_cells = [
            {
                "id": str(
                    state.get("id")
                    or _projection_id(
                        "frs",
                        state["facet_id"],
                        state.get("capability_key", "shared"),
                        state.get("practice_item_id"),
                    )
                ),
                "facet_id": state["facet_id"],
                "capability_key": state.get("capability_key", "shared"),
                "practice_item_id": state.get("practice_item_id"),
                "recall_alpha": state["recall_alpha"],
                "recall_beta": state["recall_beta"],
                "recall_mean": state["recall_mean"],
                "recall_variance": state["recall_variance"],
                "independent_evidence_mass": state.get("independent_evidence_mass", 0.0),
                "raw_coverage_mass": state.get("raw_coverage_mass", 0.0),
                "last_observed_at": state.get("last_observed_at"),
                "last_error_at": state.get("last_error_at"),
                "consecutive_failures": int(state.get("consecutive_failures", 0)),
                "algorithm_version": algorithm_version,
                "created_at": state.get("created_at"),
            }
            for state in recall_rows
        ]
        capability_cells = [
            {
                "facet_id": row["facet_id"],
                "capability": row["capability"],
                "direct_positive_mass": row.get("direct_positive_mass", 0.0),
                "direct_negative_mass": row.get("direct_negative_mass", 0.0),
                "embedded_positive_mass": row.get("embedded_positive_mass", 0.0),
                "embedded_negative_mass": row.get("embedded_negative_mass", 0.0),
                "certification_credit": row.get("certification_credit", 0.0),
                "direct_certification_credit": row.get("direct_certification_credit", 0.0),
                "embedded_certification_credit": row.get("embedded_certification_credit", 0.0),
                "unexercised_supporting_mass": row.get("unexercised_supporting_mass", 0.0),
                "independent_surface_groups_json": _json(
                    sorted(row.get("independent_surface_groups", []))
                ),
                "algorithm_version": algorithm_version,
                "created_at": row.get("created_at"),
            }
            for row in capability_rows
        ]
        with self.connection() as connection:
            _write_projection_on_change(
                connection,
                (
                    (_FACET_RECALL_PROJECTION, recall_cells),
                    (_FACET_CAPABILITY_PROJECTION, capability_cells),
                ),
                now=now,
            )

    def rebuild_stamp_snapshot(self, tables: Iterable[str]) -> dict[str, dict[tuple[Any, ...], dict[str, Any]]]:
        """The cells of these derived tables as a rebuild found them (see
        :meth:`keep_unchanged_rebuild_stamps`)."""

        snapshot: dict[str, dict[tuple[Any, ...], dict[str, Any]]] = {}
        with self.connection() as connection:
            for table in tables:
                spec = _REBUILD_STAMPED_TABLES[table]
                columns = ", ".join(dict.fromkeys((*spec.key, *spec.compared, *spec.stamps)))
                snapshot[table] = {
                    tuple(row[column] for column in spec.key): dict(row)
                    for row in connection.execute(f"SELECT {columns} FROM {table}")
                }
        return snapshot

    def keep_unchanged_rebuild_stamps(
        self, snapshot: Mapping[str, Mapping[tuple[Any, ...], Mapping[str, Any]]]
    ) -> int:
        """Give each cell a rebuild left as it found it the stamps it had then.

        A stamp says when its cell last changed, so a rebuild that changes no
        value must change no stamp (and a second rebuild then changes nothing).
        A rebuild cannot get there by writing on change alone: a learning
        object's replay folds the cache through each attempt's position (the
        state its live write read) before its closing projection, and the
        umbrella clears a table before re-deriving it, so an unchanged cell is
        rewritten, or deleted and re-inserted, on the way. Cells that changed,
        appeared or vanished keep what the rebuild wrote. Returns the number of
        cells whose stamps were put back."""

        restored = 0
        with self.connection() as connection:
            for table, before in snapshot.items():
                spec = _REBUILD_STAMPED_TABLES[table]
                columns = ", ".join(dict.fromkeys((*spec.key, *spec.compared, *spec.stamps)))
                updates = []
                for row in connection.execute(f"SELECT rowid AS stored_rowid, {columns} FROM {table}"):
                    found = before.get(tuple(row[column] for column in spec.key))
                    if found is None or any(row[column] != found[column] for column in spec.compared):
                        continue
                    if all(row[column] == found[column] for column in spec.stamps):
                        continue
                    updates.append((*(found[column] for column in spec.stamps), int(row["stored_rowid"])))
                if updates:
                    assignments = ", ".join(f"{column} = ?" for column in spec.stamps)
                    connection.executemany(f"UPDATE {table} SET {assignments} WHERE rowid = ?", updates)
                    restored += len(updates)
            connection.commit()
        return restored

    # -- capability residual activation (§4.2, KM5; DEFAULT OFF) -----------------

    def replace_capability_residual_state(
        self,
        *,
        rows: Iterable[Mapping[str, Any]],
        algorithm_version: str,
        clock: Clock | None = None,
    ) -> None:
        """Make the derived capability-residual activation state equal a projection (§4.2).

        Like :meth:`replace_canonical_facet_state`, this persists a pure
        projection over the observation ledger + closed episodes, so a rebuild
        reproduces its values, and it writes only the cells that changed
        (nothing when none did). When residual activation is disabled in config
        the projection passes ``rows=[]`` and the table stays empty —
        determinism holds with the feature on and off.
        """

        now = utc_now_iso(clock)
        cells = [
            {
                "id": str(
                    row.get("id")
                    or _projection_id("crs", row["facet_id"], row["capability"])
                ),
                "facet_id": row["facet_id"],
                "capability": row["capability"],
                "active": 1 if row.get("active") else 0,
                "activation_reason": row.get("activation_reason"),
                "residual_alpha": float(row["residual_alpha"]),
                "residual_beta": float(row["residual_beta"]),
                "residual_mean": float(row["residual_mean"]),
                "parent_alpha": float(row["parent_alpha"]),
                "parent_beta": float(row["parent_beta"]),
                "parent_mean": float(row["parent_mean"]),
                "divergence": float(row.get("divergence", 0.0)),
                "independent_groups": int(row.get("independent_groups", 0)),
                "independent_mass": float(row.get("independent_mass", 0.0)),
                "algorithm_version": algorithm_version,
                "created_at": row.get("created_at"),
            }
            for row in rows
        ]
        with self.connection() as connection:
            _write_projection_on_change(
                connection, ((_CAPABILITY_RESIDUAL_PROJECTION, cells),), now=now
            )

    def capability_residual_states(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM capability_residual_state ORDER BY facet_id, capability"
            ).fetchall()
        return [_capability_residual_row(row) for row in rows]

    def capability_residual_state(
        self, facet_id: str, capability: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM capability_residual_state WHERE facet_id = ? AND capability = ?",
                (facet_id, capability),
            ).fetchone()
        return _capability_residual_row(row) if row is not None else None

    # -- pre-first-practice identifiability watermark (§11.3, KM5) ---------------

    def identifiability_watermark(self, subject_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM subject_identifiability_watermarks WHERE subject_id = ?",
                (subject_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "subject_id": row["subject_id"],
            "registry_hash": row["registry_hash"],
            "finding_count": int(row["finding_count"]),
            "checked_at": row["checked_at"],
        }

    def upsert_identifiability_watermark(
        self,
        *,
        subject_id: str,
        registry_hash: str,
        finding_count: int,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO subject_identifiability_watermarks(
                  subject_id, registry_hash, finding_count, checked_at
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(subject_id) DO UPDATE SET
                  registry_hash = excluded.registry_hash,
                  finding_count = excluded.finding_count,
                  checked_at = excluded.checked_at
                """,
                (subject_id, registry_hash, int(finding_count), now),
            )
            connection.commit()

    # -- facet_merges: transitive resolution, cycle-rejected at write (§3.4) ------

    def facet_merge_map(self, *, include_in_flight: bool = False) -> dict[str, str]:
        """The settled merge map, retired facet -> survivor.

        Rows of a facet-identity merge or undo still in flight (``applying`` or
        ``undoing``) are left out until it settles: facets.yaml is the authority
        meanwhile (``stores.facet_identity.settled_merge_rows``, review F12).
        ``include_in_flight`` returns every row, for the write-time checks.
        """

        with self.connection() as connection:
            if not include_in_flight:
                return dict(settled_merge_rows(connection))
            rows = connection.execute(
                "SELECT retired_facet_id, surviving_facet_id FROM facet_merges"
            ).fetchall()
        return {str(r["retired_facet_id"]): str(r["surviving_facet_id"]) for r in rows}

    def resolve_facet_merge(self, facet_id: str, merge_map: Mapping[str, str] | None = None) -> str:
        """Resolve a facet id transitively to its terminal survivor (§7.1)."""

        table = dict(merge_map) if merge_map is not None else self.facet_merge_map()
        return _resolve_merge(facet_id, table)

    def insert_facet_merge(
        self,
        *,
        retired_facet_id: str,
        surviving_facet_id: str,
        proposal_item_id: str | None = None,
        rationale: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        """Record a pre-lock reviewed merge; reject a row that creates a cycle.

        A cycle would make transitive resolution non-terminating; it is rejected
        at write time so the map can always be resolved to a fixed point (§7.1).
        """

        if retired_facet_id == surviving_facet_id:
            raise ValueError("merge would create a cycle: a facet cannot be merged into itself")
        table = self.facet_merge_map(include_in_flight=True)
        if retired_facet_id in table:
            raise ValueError(f"facet {retired_facet_id!r} is already retired by a merge")
        # Would (retired -> surviving) create a cycle? It does iff `retired` is
        # already reachable from `surviving` under the existing map.
        if _resolve_merge(surviving_facet_id, table) == retired_facet_id or _reaches(
            surviving_facet_id, retired_facet_id, table
        ):
            raise ValueError(
                f"merge {retired_facet_id!r} -> {surviving_facet_id!r} would create a cycle"
            )
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO facet_merges(
                  retired_facet_id, surviving_facet_id, merged_at, proposal_item_id, rationale
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (retired_facet_id, surviving_facet_id, now, proposal_item_id, rationale),
            )
            connection.commit()

    def facet_recall_states(self, learning_object_id: str | None = None) -> list[FacetRecallState]:
        with self.connection() as connection:
            if learning_object_id is None:
                rows = connection.execute(
                    "SELECT * FROM evidence_facet_recall_state ORDER BY learning_object_id, facet_id, practice_item_id"
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT * FROM evidence_facet_recall_state
                    WHERE learning_object_id = ?
                    ORDER BY facet_id, practice_item_id
                    """,
                    (learning_object_id,),
                ).fetchall()
        return [_facet_recall_state(row) for row in rows]

    def facet_uncertainty_state(
        self,
        learning_object_id: str,
        facet_id: str,
    ) -> FacetUncertaintyState | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM facet_uncertainty
                WHERE learning_object_id = ? AND facet_id = ?
                """,
                (learning_object_id, facet_id),
            ).fetchone()
        return _facet_uncertainty_state(row) if row is not None else None

    def facet_uncertainty_states(
        self,
        learning_object_id: str | None = None,
        *,
        statuses: Iterable[str] | None = None,
    ) -> list[FacetUncertaintyState]:
        clauses: list[str] = []
        parameters: list[Any] = []
        if learning_object_id is not None:
            clauses.append("learning_object_id = ?")
            parameters.append(learning_object_id)
        status_values = list(statuses or [])
        if status_values:
            clauses.append(f"status IN ({','.join('?' for _ in status_values)})")
            parameters.extend(status_values)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM facet_uncertainty{where}
                ORDER BY learning_object_id, status, uncertainty DESC, facet_id
                """,
                parameters,
            ).fetchall()
        return [_facet_uncertainty_state(row) for row in rows]

    def upsert_facet_uncertainty_state(self, state: Mapping[str, Any]) -> None:
        with self.connection() as connection:
            self._upsert_facet_uncertainty_state(connection, state)
            connection.commit()

    def practice_item_quality_state(self, practice_item_id: str) -> PracticeItemQualityState | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM practice_item_quality_state WHERE practice_item_id = ?",
                (practice_item_id,),
            ).fetchone()
        return _practice_item_quality_state(row) if row is not None else None

    def practice_item_quality_states(self) -> dict[str, PracticeItemQualityState]:
        """All item-quality projections keyed for a scheduler vault sweep."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM practice_item_quality_state ORDER BY practice_item_id"
            ).fetchall()
        return {
            str(row["practice_item_id"]): _practice_item_quality_state(row)
            for row in rows
        }

    def upsert_practice_item_quality_state(self, state: Mapping[str, Any]) -> None:
        with self.connection() as connection:
            self._upsert_practice_item_quality_state(connection, state)
            connection.commit()

    def ability_transition_event(self, attempt_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM ability_transition_events WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
        return _decode_ability_transition_event(row) if row is not None else None

    def latest_whole_vault_rebuild(self) -> dict[str, Any] | None:
        """The latest rebuild that replayed every learning object (scope ``all``), or None."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM derived_state_rebuilds WHERE scope = 'all' ORDER BY created_at DESC, id DESC LIMIT 1"
            ).fetchone()
        return _decode_derived_state_rebuild(row) if row is not None else None

    def record_derived_state_rebuild(
        self,
        *,
        scope: str,
        learning_object_ids: list[str],
        algorithm_version: str,
        rebuilt_learning_objects: int,
        replayed_attempts: int,
        canonical_projection_version: str | None = None,
        coverage_denominator_version: str | None = None,
        projection_switches: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> str:
        rebuild_id = new_ulid()
        created_at = utc_now_iso(clock)
        columns = [
            "id", "scope", "learning_object_ids_json", "algorithm_version",
            "rebuilt_learning_objects", "replayed_attempts",
            "canonical_projection_version", "coverage_denominator_version", "created_at",
        ]
        values: list[Any] = [
            rebuild_id,
            scope,
            _json(learning_object_ids),
            algorithm_version,
            rebuilt_learning_objects,
            replayed_attempts,
            canonical_projection_version,
            coverage_denominator_version,
            created_at,
        ]
        if projection_switches is not None:
            # Router objective RO1 (migration 244): the switches a replay derived
            # persisted state under, the projection's defaults snapshot. Written
            # only by a rebuild that replays attempts, and only when given.
            columns.append("projection_switches_json")
            values.append(_json(dict(sorted(projection_switches.items()))))
        with self.connection() as connection:
            connection.execute(
                f"INSERT INTO derived_state_rebuilds({', '.join(columns)}) "
                f"VALUES ({', '.join('?' for _ in columns)})",
                values,
            )
            connection.commit()
        return rebuild_id

    # ------------------------------------------------------------------
    # P0.5 parameter registry (migration 069). SQL-only; the definition and
    # projection logic live in ``learnloop.params.parameter_registry``.
    # ------------------------------------------------------------------

    def upsert_parameter_registry_entry(self, *, entry: dict[str, Any], clock: Clock | None = None) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO parameter_registry(
                  path, kind, param_class, effective_value_json, effective_value_hash,
                  source, status, lifecycle, rationale, scope, owner,
                  sensitivity_certificate_id, evidence_manifest_id, redundancy_proof_id,
                  promotion_evidence_id, last_review_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                  kind = excluded.kind,
                  param_class = excluded.param_class,
                  effective_value_json = excluded.effective_value_json,
                  effective_value_hash = excluded.effective_value_hash,
                  source = excluded.source,
                  status = excluded.status,
                  lifecycle = excluded.lifecycle,
                  rationale = excluded.rationale,
                  scope = excluded.scope,
                  owner = excluded.owner,
                  sensitivity_certificate_id = excluded.sensitivity_certificate_id,
                  evidence_manifest_id = excluded.evidence_manifest_id,
                  redundancy_proof_id = excluded.redundancy_proof_id,
                  promotion_evidence_id = excluded.promotion_evidence_id,
                  last_review_at = excluded.last_review_at,
                  updated_at = excluded.updated_at
                """,
                (
                    entry["path"],
                    entry["kind"],
                    entry["param_class"],
                    _json(entry["effective_value"]),
                    entry["effective_value_hash"],
                    entry["source"],
                    entry["status"],
                    entry["lifecycle"],
                    entry["rationale"],
                    entry["scope"],
                    entry["owner"],
                    entry.get("sensitivity_certificate_id"),
                    entry.get("evidence_manifest_id"),
                    entry.get("redundancy_proof_id"),
                    entry.get("promotion_evidence_id"),
                    entry.get("last_review_at"),
                    now,
                ),
            )
            connection.commit()

    def parameter_registry_entry(self, path: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM parameter_registry WHERE path = ?", (path,)
            ).fetchone()
        return dict(row) if row is not None else None

    def parameter_registry_entries(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM parameter_registry ORDER BY path"
            ).fetchall()
        return [dict(r) for r in rows]

    def insert_parameter_registry_manifest(
        self,
        *,
        algorithm_version: str,
        manifest_hash: str,
        entries: dict[str, Any],
        clock: Clock | None = None,
    ) -> str | None:
        """Freeze one immutable manifest per algorithm version. Idempotent: a
        second freeze of the same version is a no-op (returns None)."""

        manifest_id = new_ulid()
        frozen_at = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM parameter_registry_manifests WHERE algorithm_version = ?",
                (algorithm_version,),
            ).fetchone()
            if existing is not None:
                return None
            connection.execute(
                """
                INSERT INTO parameter_registry_manifests(
                  id, algorithm_version, manifest_hash, entries_json, frozen_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (manifest_id, algorithm_version, manifest_hash, _json(entries), frozen_at),
            )
            connection.commit()
        return manifest_id

    def parameter_registry_manifest(self, algorithm_version: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM parameter_registry_manifests WHERE algorithm_version = ?",
                (algorithm_version,),
            ).fetchone()
        return dict(row) if row is not None else None

    def insert_sensitivity_certificate(self, *, certificate: dict[str, Any], clock: Clock | None = None) -> str:
        cert_id = certificate.get("id") or new_ulid()
        produced_at = certificate.get("produced_at") or utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO parameter_sensitivity_certificates(
                  id, path, covered_value_hash, plausible_range_json, flip_points_json,
                  decision_stable, scenario_json, sim_report_hash, produced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cert_id,
                    certificate["path"],
                    certificate["covered_value_hash"],
                    _json(certificate["plausible_range"]),
                    _json(certificate["flip_points"]),
                    1 if certificate["decision_stable"] else 0,
                    _json(certificate["scenario"]),
                    certificate["sim_report_hash"],
                    produced_at,
                ),
            )
            connection.commit()
        return cert_id

    def sensitivity_certificates_for_path(self, path: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM parameter_sensitivity_certificates WHERE path = ? ORDER BY produced_at DESC",
                (path,),
            ).fetchall()
        return [dict(r) for r in rows]

    def record_parameter_bind_event(
        self,
        *,
        path: str,
        bound_context: dict[str, Any],
        observation_ref: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        event_id = new_ulid()
        created_at = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO parameter_bind_events(
                  id, path, bound_context_json, observation_ref, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (event_id, path, _json(bound_context), observation_ref, created_at),
            )
            connection.commit()
        return event_id

    def parameter_bind_events_for_path(self, path: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM parameter_bind_events WHERE path = ? ORDER BY created_at",
                (path,),
            ).fetchall()
        return [dict(r) for r in rows]

    def chosen_candidate_outcomes(self) -> list[dict[str, Any]]:
        """Slate candidates joined to their realized attempts (`learnloop eval`
        prediction-calibration input), oldest first."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT c.id AS candidate_id, c.slate_id, c.practice_item_id, c.learning_object_id,
                       c.predicted_correctness, c.selection_propensity, c.exploration_flag,
                       c.selected_mode,
                       a.id AS attempt_id, a.correctness, a.rubric_score, a.attempt_type, a.created_at
                FROM scheduler_slate_candidates c
                JOIN practice_attempts a ON a.id = c.chosen_attempt_id
                WHERE c.predicted_correctness IS NOT NULL AND a.correctness IS NOT NULL
                ORDER BY a.created_at ASC, a.id ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def prediction_interval_rows(self) -> list[dict[str, Any]]:
        """Per-attempt predicted score distribution joined to the realized
        outcome (`learnloop eval` coverage input), oldest first per LO."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT s.attempt_id, s.predicted_score_dist_json,
                       a.learning_object_id, a.correctness, a.rubric_score,
                       a.attempt_type, a.created_at
                FROM attempt_surprise s
                JOIN practice_attempts a ON a.id = s.attempt_id
                WHERE s.predicted_score_dist_json IS NOT NULL
                  AND a.correctness IS NOT NULL
                ORDER BY a.learning_object_id ASC, a.created_at ASC, a.id ASC
                """
            ).fetchall()
        return [
            {
                "attempt_id": row["attempt_id"],
                "learning_object_id": row["learning_object_id"],
                "predicted_score_dist": _loads(row["predicted_score_dist_json"], None),
                "correctness": row["correctness"],
                "attempt_type": row["attempt_type"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def retention_label_rows(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT l.*, a.primed AS outcome_primed,
                       a.manual_review AS outcome_manual_review,
                       a.manual_review_reason AS outcome_manual_review_reason,
                       a.session_id AS outcome_session_id,
                       source.session_id AS source_session_id
                FROM learning_outcome_labels l
                JOIN practice_attempts a ON a.id=l.outcome_attempt_id
                JOIN practice_attempts source ON source.id=l.source_attempt_id
                WHERE l.label_type = 'same_item_retention'
                ORDER BY l.created_at ASC, l.id ASC
                """
            ).fetchall()
        return [_decode_learning_outcome_label(row) for row in rows]

    def item_attempt_history(self) -> list[dict[str, Any]]:
        """Graded attempts ordered for per-item FSRS replay (`learnloop eval`)."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, practice_item_id, rubric_score, hints_used, attempt_type, created_at
                FROM practice_attempts
                WHERE rubric_score IS NOT NULL
                ORDER BY practice_item_id ASC, created_at ASC, id ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def candidate_propensity_rows(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT slate_id, id, selection_propensity, selection_temperature,
                       exploration_flag, chosen_attempt_id, was_returned, propensity_kind
                FROM scheduler_slate_candidates
                ORDER BY created_at ASC, id ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_fitted_parameters(
        self,
        *,
        scope: str,
        params: Mapping[str, Any],
        algorithm_version: str,
        training_rows_count: int,
        training_data_through: str | None = None,
        metrics: Mapping[str, Any] | None = None,
        activate: bool = True,
        clock: Clock | None = None,
    ) -> str:
        """Insert a fitted parameter set; when ``activate``, atomically replace
        the currently active set for the scope (history rows are kept)."""

        fitted_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            if activate:
                connection.execute(
                    "UPDATE fitted_parameters SET active = 0, deactivated_at = ? WHERE scope = ? AND active = 1",
                    (now, scope),
                )
            connection.execute(
                """
                INSERT INTO fitted_parameters(
                  id, scope, params_json, fitted_at, algorithm_version,
                  training_rows_count, training_data_through, metrics_json,
                  active, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fitted_id,
                    scope,
                    _json(dict(params)),
                    now,
                    algorithm_version,
                    training_rows_count,
                    training_data_through,
                    _json(dict(metrics)) if metrics is not None else None,
                    1 if activate else 0,
                    now,
                ),
            )
            connection.commit()
        return fitted_id

    def active_fitted_parameters(self, scope: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM fitted_parameters
                WHERE scope = ? AND active = 1
                ORDER BY fitted_at DESC, id DESC
                LIMIT 1
                """,
                (scope,),
            ).fetchone()
        return _decode_fitted_parameters(row) if row is not None else None

    def list_fitted_parameters(self, scope: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        query = "SELECT * FROM fitted_parameters"
        params: tuple[Any, ...] = ()
        if scope is not None:
            query += " WHERE scope = ?"
            params = (scope,)
        query += " ORDER BY fitted_at DESC, rowid DESC LIMIT ?"
        params = (*params, limit)
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [_decode_fitted_parameters(row) for row in rows]

    def deactivate_fitted_parameters(
        self, scope: str, *, fitted_id: str | None = None, clock: Clock | None = None
    ) -> int:
        now = utc_now_iso(clock)
        query = "UPDATE fitted_parameters SET active = 0, deactivated_at = ? WHERE scope = ? AND active = 1"
        params: tuple[Any, ...] = (now, scope)
        if fitted_id is not None:
            query += " AND id = ?"
            params = (*params, fitted_id)
        with self.connection() as connection:
            cursor = connection.execute(query, params)
            connection.commit()
            return cursor.rowcount

    def item_parameter_state(self, practice_item_id: str) -> ItemParameterState | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM item_parameter_state WHERE practice_item_id = ?",
                (practice_item_id,),
            ).fetchone()
        return _decode_item_parameter_state(row) if row is not None else None

    def item_parameter_states(self) -> dict[str, ItemParameterState]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM item_parameter_state").fetchall()
        return {row["practice_item_id"]: _decode_item_parameter_state(row) for row in rows}

    def _upsert_item_parameter_state_record(
        self, connection: sqlite3.Connection, state: ItemParameterState
    ) -> None:
        connection.execute(
            """
            INSERT INTO item_parameter_state(
              practice_item_id, b_mean, b_var, evidence_count, algorithm_version, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(practice_item_id) DO UPDATE SET
              b_mean = excluded.b_mean,
              b_var = excluded.b_var,
              evidence_count = excluded.evidence_count,
              algorithm_version = excluded.algorithm_version,
              updated_at = excluded.updated_at
            """,
            (
                state.practice_item_id,
                state.b_mean,
                state.b_var,
                state.evidence_count,
                state.algorithm_version,
                state.updated_at,
            ),
        )

    def latest_derived_state_rebuild(self) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM derived_state_rebuilds
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """
            ).fetchone()
        return _decode_derived_state_rebuild(row) if row is not None else None

    def has_whole_vault_rebuild(self, *, algorithm_version: str) -> bool:
        """Whether a whole-vault rebuild (scope ``all``) ran under ``algorithm_version``.

        An activation that rebuilds the whole vault commits this receipt in
        its own transaction, so it marks the activation complete whatever
        startup, per-LO or recovery receipts are written after it."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT 1 FROM derived_state_rebuilds WHERE scope = 'all' AND algorithm_version = ? LIMIT 1",
                (algorithm_version,),
            ).fetchone()
        return row is not None

    def latest_canonical_projection_rebuild(self) -> dict[str, Any] | None:
        """Latest rebuild that explicitly names its projection semantics.

        ``derived_state_rebuilds`` also carries narrow scheduler/substrate
        recovery markers written by services that do not rebuild canonical
        facet state.  Their NULL projection field means "not reported", not a
        rollback.  Startup rollout checks must therefore read the latest
        explicit projection baseline rather than whichever unrelated marker
        happened to be written last.
        """

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM derived_state_rebuilds
                WHERE canonical_projection_version IS NOT NULL
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """
            ).fetchone()
        return _decode_derived_state_rebuild(row) if row is not None else None

    def active_probe_presentation_for_session(
        self, session_id: str
    ) -> ProbePresentationRecord | None:
        """The scheduler-backed assignment currently owned by one session."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT p.*
                FROM probe_presentations p
                JOIN scheduler_slate_candidates c ON c.id = p.scheduler_candidate_id
                JOIN scheduler_slates s ON s.id = c.slate_id
                WHERE s.session_id = ? AND p.status IN ('selected', 'served')
                ORDER BY p.created_at DESC, p.id DESC
                LIMIT 1
                """,
                (session_id,),
            ).fetchone()
        return _probe_presentation_record(row) if row is not None else None

    def qualifying_probe_observation_count_for_session(self, session_id: str) -> int:
        """Qualifying diagnostic observations recorded in one session (§5.9 cap).

        held-grade-evidence (review F3): an observation whose grade a later
        regrade holds for review qualifies nothing while it is held."""

        from learnloop.held_grades import held_for_review_attempts

        with self.connection() as connection:
            attempt_ids = [
                str(row["attempt_id"])
                for row in connection.execute(
                    """
                    SELECT o.attempt_id
                    FROM probe_observations o
                    JOIN practice_attempts a ON a.id = o.attempt_id
                    WHERE a.session_id = ? AND o.eligible_for_completion = 1
                    """,
                    (session_id,),
                ).fetchall()
            ]
            held = held_for_review_attempts(connection, attempt_ids) if attempt_ids else frozenset()
        return sum(1 for attempt_id in attempt_ids if attempt_id not in held)

    def probe_observations_for_episode(
        self, probe_episode_id: str, *, as_recorded: bool = False
    ) -> list[dict[str, Any]]:
        """Observations joined through attempt → presentation → episode (§5.1).

        Episode progress is always derived from this join, never cached. Each row
        is the observation record dict plus its attempt and presentation context.

        held-grade-evidence (review F3): the rows are the EFFECTIVE view
        (``held_grades.effective_probe_observation_rows``). An observation whose
        grade a later regrade holds for review reads, while it is held, as one
        held on submission is written: no belief update, not qualifying, no
        joined score. ``as_recorded=True`` returns the stored flags (the receipt).
        """

        from learnloop.held_grades import effective_probe_observation_rows

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT o.*, a.practice_item_id, a.attempt_type, a.rubric_score,
                       a.error_type, a.hints_used, a.created_at AS attempt_created_at,
                       p.id AS presentation_id, p.state_segment_id, p.target_facets_json,
                       p.instrument_card_id, p.instrument_card_version,
                       p.probe_family_template_id, p.probe_family_template_version,
                       p.expected_information_gain, p.selection_components_json,
                       p.served_at, p.submitted_at, p.instrument_card_snapshot_json
                FROM probe_observations o
                JOIN practice_attempts a ON a.id = o.attempt_id
                JOIN probe_presentations p ON p.id = a.probe_presentation_id
                WHERE p.probe_episode_id = ?
                ORDER BY o.created_at, o.id
                """,
                (probe_episode_id,),
            ).fetchall()
        results: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(row)
            payload["observation"] = _probe_observation_record(row)
            payload["target_facets"] = _loads(row["target_facets_json"], [])
            payload["selection_components"] = _loads(row["selection_components_json"], {})
            payload["instrument_card_snapshot"] = _loads(row["instrument_card_snapshot_json"], None)
            results.append(payload)
        if as_recorded or not results:
            return results
        with self.connection() as connection:
            return effective_probe_observation_rows(connection, results)

    # --- synthesis-time generate-discriminator needs (ING M6, §8.7) ----------

    def upsert_synthesis_generation_need(
        self,
        *,
        subject_id: str,
        need_kind: str,
        target_key: str,
        missing_capability: str,
        facet_ids: list[str] | None = None,
        source_set_id: str | None = None,
        synthesis_run_id: str | None = None,
        detail: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Record one deduplicated synthesis-time generation/coarsen need.

        Mirrors ``upsert_probe_generation_need`` but synthesis-scoped: deduped on
        (subject_id, need_kind, target_key) since there is no probe episode yet.
        """

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM synthesis_generation_needs "
                "WHERE subject_id = ? AND need_kind = ? AND target_key = ?",
                (subject_id, need_kind, target_key),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            need_id = new_ulid()
            connection.execute(
                """
                INSERT INTO synthesis_generation_needs(
                  id, subject_id, source_set_id, synthesis_run_id, need_kind,
                  target_key, missing_capability, facet_ids_json, detail, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                """,
                (
                    need_id,
                    subject_id,
                    source_set_id,
                    synthesis_run_id,
                    need_kind,
                    target_key,
                    missing_capability,
                    _json(list(facet_ids or [])),
                    detail,
                    now,
                ),
            )
            connection.commit()
        return need_id

    def synthesis_generation_needs(
        self,
        *,
        subject_id: str | None = None,
        status: str | None = None,
        need_kind: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        parameters: list[Any] = []
        for column, value in (
            ("subject_id", subject_id),
            ("status", status),
            ("need_kind", need_kind),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                parameters.append(value)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM synthesis_generation_needs{where} ORDER BY created_at, id",
                parameters,
            ).fetchall()
        return [
            {
                "id": row["id"],
                "subject_id": row["subject_id"],
                "source_set_id": row["source_set_id"],
                "synthesis_run_id": row["synthesis_run_id"],
                "need_kind": row["need_kind"],
                "target_key": row["target_key"],
                "missing_capability": row["missing_capability"],
                "facet_ids": _loads(row["facet_ids_json"], []),
                "detail": row["detail"],
                "status": row["status"],
                "created_at": row["created_at"],
                "resolved_at": row["resolved_at"],
            }
            for row in rows
        ]

    def resolve_synthesis_generation_need(
        self, need_id: str, *, status: str = "resolved", clock: Clock | None = None
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                "UPDATE synthesis_generation_needs SET status = ?, resolved_at = ? WHERE id = ?",
                (status, now, need_id),
            )
            connection.commit()

    def insert_elicitation_event(self, event: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        event_id = str(event.get("id") or new_ulid())
        now = event.get("created_at") or utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO elicitation_events(
                  id, session_id, selected_practice_item_id, target_scope_json,
                  policy, candidate_scores_json, entropy_before,
                  expected_information_gain, selected_reason, hypothesis_set_id,
                  hypothesis_set_json, trigger, fallback_outcome, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    event.get("session_id"),
                    event.get("selected_practice_item_id"),
                    _json(event.get("target_scope")) if event.get("target_scope") is not None else None,
                    event.get("policy", "probe_eig"),
                    _json(event.get("candidate_scores")) if event.get("candidate_scores") is not None else None,
                    event.get("entropy_before"),
                    event.get("expected_information_gain"),
                    event.get("selected_reason"),
                    event.get("hypothesis_set_id"),
                    _json(event.get("hypothesis_set")) if event.get("hypothesis_set") is not None else None,
                    event.get("trigger"),
                    event.get("fallback_outcome"),
                    now,
                ),
            )
            connection.commit()
        return event_id

    def record_decision_features(
        self,
        *,
        decision_id: str,
        decision_type: str,
        ability_vector: Mapping[str, Any],
        item_demand_vector: Mapping[str, Any] | None = None,
        context: Mapping[str, Any] | None = None,
        algorithm_version: str,
        clock: Clock | None = None,
    ) -> str:
        feature_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM decision_features
                WHERE decision_id = ? AND decision_type = ?
                """,
                (decision_id, decision_type),
            ).fetchone()
            if existing is not None:
                feature_id = existing["id"]
            connection.execute(
                """
                INSERT INTO decision_features(
                  id, decision_id, decision_type, ability_vector_json,
                  item_demand_vector_json, context_json, algorithm_version, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(decision_id, decision_type) DO NOTHING
                """,
                (
                    feature_id,
                    decision_id,
                    decision_type,
                    _json(dict(ability_vector)),
                    _json(dict(item_demand_vector)) if item_demand_vector is not None else None,
                    _json(dict(context or {})),
                    algorithm_version,
                    now,
                ),
            )
            connection.commit()
        return feature_id

    def decision_features(self, *, decision_id: str, decision_type: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM decision_features
                WHERE decision_id = ? AND decision_type = ?
                """,
                (decision_id, decision_type),
            ).fetchone()
        return _decode_decision_features(row) if row is not None else None

    def elicitation_events(self, session_id: str | None = None) -> list[dict[str, Any]]:
        with self.connection() as connection:
            if session_id is None:
                rows = connection.execute(
                    "SELECT * FROM elicitation_events ORDER BY created_at DESC"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM elicitation_events WHERE session_id = ? ORDER BY created_at DESC",
                    (session_id,),
                ).fetchall()
        return [_decode_elicitation_event(row) for row in rows]

    def insert_scheduler_explanations(
        self,
        explanations: Iterable[dict[str, Any]],
        *,
        session_id: str | None,
        algorithm_version: str,
        retention_limit: int | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            for explanation in explanations:
                connection.execute(
                    """
                    INSERT INTO scheduler_explanations(
                      id, session_id, practice_item_id, selected_mode, priority,
                      components_json, readiness_factor, expected_information_gain,
                      target_scope_json, plain_english_json, algorithm_version, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_ulid(),
                        session_id,
                        explanation["practice_item_id"],
                        explanation.get("selected_mode", "review"),
                        explanation["priority"],
                        _json(explanation["components"]),
                        explanation.get("readiness_factor"),
                        explanation.get("expected_information_gain"),
                        _json(explanation.get("target_scope")) if explanation.get("target_scope") is not None else None,
                        _json(explanation.get("plain_english")) if explanation.get("plain_english") is not None else None,
                        algorithm_version,
                        now,
                    ),
                )
            if session_id is not None and retention_limit is not None and retention_limit > 0:
                connection.execute(
                    """
                    DELETE FROM scheduler_explanations
                    WHERE session_id = ?
                      AND id NOT IN (
                        SELECT id FROM scheduler_explanations
                        WHERE session_id = ?
                        ORDER BY created_at DESC, priority DESC, practice_item_id ASC, id DESC
                        LIMIT ?
                      )
                    """,
                    (session_id, session_id, retention_limit),
                )
            connection.commit()

    def record_scheduler_slate(
        self,
        explanations: Iterable[dict[str, Any]],
        *,
        session_id: str | None,
        algorithm_version: str,
        requested_limit: int | None = None,
        session_context: Mapping[str, Any] | None = None,
        config_snapshot: Mapping[str, Any] | None = None,
        selection_policy: str = "selection_reward_v1",
        probe_presentation: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> str:
        rows = list(explanations)
        now = utc_now_iso(clock)
        slate_id = new_ulid()
        returned = [
            row for row in rows if float((row.get("components") or {}).get("selected") or 0.0) > 0.0
        ]
        returned_rank_by_id = {
            row["practice_item_id"]: rank
            for rank, row in enumerate(returned, start=1)
        }
        candidate_ids: dict[str, str] = {}
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO scheduler_slates(
                  id, session_id, generated_at, requested_limit, returned_count,
                  candidate_count, chosen_practice_item_id, chosen_attempt_id,
                  selection_policy, session_context_json, config_snapshot_json,
                  algorithm_version, created_at, updated_at, collection_version
                )
                VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    slate_id,
                    session_id,
                    now,
                    requested_limit,
                    len(returned),
                    len(rows),
                    selection_policy,
                    _json(dict(session_context or {})),
                    _json(dict(config_snapshot or {})),
                    algorithm_version,
                    now,
                    now,
                    COLLECTION_VERSION,
                ),
            )
            for rank, explanation in enumerate(rows, start=1):
                components = dict(explanation.get("components") or {})
                target_scope = explanation.get("target_scope") or {}
                reward_debug = target_scope.get("selection_reward") if isinstance(target_scope, Mapping) else None
                practice_item_id = explanation["practice_item_id"]
                candidate_id = new_ulid()
                candidate_ids[practice_item_id] = candidate_id
                returned_rank = returned_rank_by_id.get(practice_item_id)
                connection.execute(
                    """
                    INSERT INTO scheduler_slate_candidates(
                      id, slate_id, practice_item_id, learning_object_id, rank,
                      returned_rank, was_returned, chosen_attempt_id, selected_mode,
                      priority, selection_reward, predicted_correctness,
                      legacy_priority, expected_information_gain, readiness_factor,
                      components_json, reward_debug_json, target_scope_json,
                      plain_english_json, selection_propensity, exploration_flag,
                      selection_temperature, algorithm_version, created_at, chosen_at, propensity_kind
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, NULL, ?)
                    """,
                    (
                        candidate_id,
                        slate_id,
                        practice_item_id,
                        _learning_object_id_from_target_scope(target_scope),
                        rank,
                        returned_rank,
                        1 if returned_rank is not None else 0,
                        explanation.get("selected_mode", "review"),
                        explanation["priority"],
                        components.get("selection_reward"),
                        components.get("predicted_correctness"),
                        components.get("legacy_priority"),
                        explanation.get("expected_information_gain"),
                        explanation.get("readiness_factor"),
                        _json(components),
                        _json(reward_debug) if reward_debug is not None else None,
                        _json(target_scope) if target_scope else None,
                        _json(explanation.get("plain_english")) if explanation.get("plain_english") is not None else None,
                        explanation.get("selection_propensity"),
                        int(explanation.get("exploration_flag") or 0),
                        algorithm_version,
                        now,
                        explanation.get("propensity_kind", "legacy-unverified"),
                    ),
                )
                features = explanation.get("decision_features")
                if features is not None:
                    snapshot = features.get("item_snapshot")
                    if snapshot is not None:
                        # Content-addressed: every later build that scores the
                        # same revision references this row instead of copying it.
                        connection.execute(
                            """
                            INSERT OR IGNORE INTO practice_item_snapshots(
                              content_hash, practice_item_id, item_json, created_at
                            )
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                snapshot["content_hash"],
                                snapshot["practice_item_id"],
                                snapshot["item_json"],
                                now,
                            ),
                        )
                    connection.execute(
                        """
                        INSERT INTO decision_features(
                          id, decision_id, decision_type, ability_vector_json,
                          item_demand_vector_json, context_json, algorithm_version, created_at
                        )
                        VALUES (?, ?, 'selection', ?, ?, ?, ?, ?)
                        """,
                        (
                            new_ulid(),
                            candidate_id,
                            _json(features["ability_vector"]),
                            _json(features.get("item_demand_vector")),
                            _json(features.get("context", {})),
                            algorithm_version,
                            now,
                        ),
                    )
            if probe_presentation is not None:
                presentation_values = dict(probe_presentation)
                practice_item_id = str(presentation_values["practice_item_id"])
                candidate_id = candidate_ids.get(practice_item_id)
                if candidate_id is None or returned_rank_by_id.get(practice_item_id) != 1:
                    raise ValueError(
                        "probe presentation must bind the top returned scheduler candidate"
                    )
                episode = connection.execute(
                    """
                    SELECT status, active_state_segment_id
                    FROM probe_episodes WHERE id = ?
                    """,
                    (presentation_values["probe_episode_id"],),
                ).fetchone()
                if (
                    episode is None
                    or episode["status"] != "in_progress"
                    or episode["active_state_segment_id"]
                    != presentation_values["state_segment_id"]
                ):
                    raise ValueError(
                        "probe presentation episode changed before scheduler commitment"
                    )
                # Do not replace an assignment that may already be displayed.
                # A later explicit abandonment/consumption boundary owns that
                # transition; queue refreshes are observational only.
                active = connection.execute(
                    """
                    SELECT id FROM probe_presentations
                    WHERE probe_episode_id = ? AND status IN ('selected', 'served')
                    LIMIT 1
                    """,
                    (presentation_values["probe_episode_id"],),
                ).fetchone()
                if active is None:
                    presentation_values["scheduler_candidate_id"] = candidate_id
                    _insert_probe_presentation_row(
                        connection,
                        presentation_id=new_ulid(),
                        now=now,
                        values=presentation_values,
                    )
            connection.commit()
        return slate_id

    def latest_scheduler_slate_by_session(self, session_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM scheduler_slates
                WHERE session_id = ?
                ORDER BY generated_at DESC, id DESC
                LIMIT 1
                """,
                (session_id,),
            ).fetchone()
        return _decode_scheduler_slate(row) if row is not None else None

    def scheduler_slate_candidates(self, slate_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM scheduler_slate_candidates
                WHERE slate_id = ?
                ORDER BY rank ASC, id ASC
                """,
                (slate_id,),
            ).fetchall()
        return [_decode_scheduler_slate_candidate(row) for row in rows]

    def latest_scheduler_explanation(self, practice_item_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM scheduler_explanations
                WHERE practice_item_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (practice_item_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "practice_item_id": row["practice_item_id"],
            "selected_mode": row["selected_mode"],
            "priority": row["priority"],
            "components": _loads(row["components_json"], {}),
            "readiness_factor": row["readiness_factor"],
            "expected_information_gain": row["expected_information_gain"],
            "target_scope": _loads(row["target_scope_json"], None),
            "plain_english": _loads(row["plain_english_json"], {}),
            "created_at": row["created_at"],
        }

    def latest_scheduler_explanations_by_session(self, session_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM scheduler_explanations
                WHERE session_id = ?
                ORDER BY created_at DESC, priority DESC, practice_item_id
                """,
                (session_id,),
            ).fetchall()
        return [_decode_scheduler_explanation(row) for row in rows]

    def create_session(
        self,
        *,
        energy: str | None = None,
        sleep_quality: float | None = None,
        available_minutes: int | None = None,
        notes_md_path: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        now = utc_now_iso(clock)
        session_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO sessions(
                  id, started_at, ended_at, energy, sleep_quality,
                  available_minutes, notes_md_path, updated_at
                )
                VALUES (?, ?, NULL, ?, ?, ?, ?, ?)
                """,
                (session_id, now, energy, sleep_quality, available_minutes, notes_md_path, now),
            )
            connection.commit()
        return session_id

    def fetch_session(self, session_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def most_recent_open_session(self) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM sessions
                WHERE ended_at IS NULL
                ORDER BY started_at DESC, id DESC
                LIMIT 1
                """
            ).fetchone()
        return dict(row) if row is not None else None

    def most_recent_ended_at(self, *, stale_open_before: str | None = None) -> str | None:
        """When the learner was last really active outside an open session, or None.

        Powers the F7 welcome-back diff (§4.4): the break the re-entry panel is
        gated on. That is the latest completed-session end or the latest attempt
        that belongs to no still-open session (an attempt outside any session is
        real activity too). The open session's own attempts are excluded so
        practising inside the re-entry session never ends it. Stale sessions
        are ended at their last activity (``end_open_sessions_except``), so the
        app noticing them late does not reset the break. Read-only, outside replay.

        ``stale_open_before`` (daily-loop DL1, review F2): a session still open
        that started before this instant is stale, not the current one, so its
        last activity counts too -- what ``end_open_sessions_except`` would end
        it at (its last attempt or checkpoint write, else its start). The daily
        plan measures its gap before Begin ends stale sessions, and "Done" or
        closing the app leaves yesterday's session open.
        """

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT MAX(at) AS latest FROM (
                  SELECT ended_at AS at FROM sessions WHERE ended_at IS NOT NULL
                  UNION ALL
                  SELECT attempt.created_at AS at
                  FROM practice_attempts attempt
                  LEFT JOIN sessions session ON session.id = attempt.session_id
                  WHERE session.id IS NULL OR session.ended_at IS NOT NULL
                     OR (:stale_before IS NOT NULL AND session.started_at < :stale_before)
                  UNION ALL
                  SELECT MAX(session.started_at, COALESCE(checkpoint.updated_at, session.started_at)) AS at
                  FROM sessions session
                  LEFT JOIN session_checkpoints checkpoint ON checkpoint.session_id = session.id
                  WHERE :stale_before IS NOT NULL
                    AND session.ended_at IS NULL
                    AND session.started_at < :stale_before
                )
                """,
                {"stale_before": stale_open_before},
            ).fetchone()
        return row["latest"] if row is not None else None

    def latest_session_minutes(self) -> tuple[int, str] | None:
        """``(minutes, started_at)`` of the latest session begun with minutes, or None.

        Daily-loop DL0 (spec_daily_loop_v1.md §6.6): Start remembers the last
        session's budget. Sessions that recorded no minutes (old clients, the
        CLI) are skipped rather than read as "no budget". The start time lets
        a newer choice that recorded no session (the TUI's) win over it.
        """

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT available_minutes, started_at FROM sessions
                WHERE available_minutes IS NOT NULL AND available_minutes > 0
                ORDER BY started_at DESC, id DESC
                LIMIT 1
                """
            ).fetchone()
        if row is None:
            return None
        return int(row["available_minutes"]), str(row["started_at"])

    def session_day_streak(self, *, clock: Clock | None = None) -> dict[str, Any]:
        """Consecutive-day study streak derived from session start timestamps.

        Days are counted in the machine's local timezone. ``current`` is the run
        of consecutive days ending today (or yesterday, if today has no session
        yet but the streak is still alive). ``active_today`` reports whether a
        session was already started today, and ``longest`` is the best run ever.
        """
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT started_at FROM sessions WHERE started_at IS NOT NULL"
            ).fetchall()

        days: set[date] = set()
        for row in rows:
            started = parse_utc(row["started_at"])
            if started is not None:
                days.add(started.astimezone().date())

        if not days:
            return {"current": 0, "active_today": False, "longest": 0}

        today = (clock or SystemClock()).now().astimezone().date()
        active_today = today in days

        anchor = today if active_today else today - timedelta(days=1)
        current = 0
        cursor = anchor
        while cursor in days:
            current += 1
            cursor -= timedelta(days=1)

        ordered = sorted(days)
        longest = 1
        run = 1
        for previous, day in zip(ordered, ordered[1:], strict=False):
            run = run + 1 if (day - previous).days == 1 else 1
            longest = max(longest, run)

        return {"current": current, "active_today": active_today, "longest": longest}

    def end_open_sessions_except(self, session_id: str, *, clock: Clock | None = None) -> int:
        """End every other open (stale) session at its own last activity.

        A session left open because the app closed mid-session ends where the
        learner stopped: its last attempt or checkpoint write, else its start.
        Stamping "now" would stretch it over the whole break and reset the
        welcome-back gap (daily-loop follow-up, 2026-10-11)."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE sessions
                SET ended_at = MAX(
                      started_at,
                      COALESCE((SELECT MAX(attempt.created_at) FROM practice_attempts attempt
                                WHERE attempt.session_id = sessions.id), started_at),
                      COALESCE((SELECT checkpoint.updated_at FROM session_checkpoints checkpoint
                                WHERE checkpoint.session_id = sessions.id), started_at)
                    ),
                    updated_at = ?
                WHERE ended_at IS NULL AND id != ?
                """,
                (now, session_id),
            )
            connection.commit()
            return cursor.rowcount

    def end_session(self, session_id: str, *, clock: Clock | None = None) -> dict[str, Any] | None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE sessions
                SET ended_at = COALESCE(ended_at, ?), updated_at = ?
                WHERE id = ?
                """,
                (now, now, session_id),
            )
            if cursor.rowcount == 0:
                connection.rollback()
                return None
            row = connection.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
            connection.commit()
        return dict(row) if row is not None else None

    def session_learner_answers(self, session_id: str) -> list[str]:
        """Every answer body recorded against this session, in submission order.

        Exists for Meas §3.A6's per-session elicitation budget, which has no
        ledger of its own to count: an offer the learner declines is
        deliberately never written down, so the submitted answers are the only
        record of how many extra lines were actually volunteered. Scoped
        strictly to ``session_id`` rather than the started/ended window
        ``session_attempt_counts`` falls back to — a budget that leaked across
        sessions through orphaned attempts would silently tighten itself.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT learner_answer_md FROM practice_attempts
                WHERE session_id = ?
                ORDER BY created_at, id
                """,
                (session_id,),
            ).fetchall()
        return [str(row["learner_answer_md"] or "") for row in rows]

    def session_attempt_counts(self, session_id: str) -> dict[str, int] | None:
        session = self.fetch_session(session_id)
        if session is None:
            return None
        started_at = session["started_at"]
        ended_at = session["ended_at"] or utc_now_iso()
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS attempts_recorded,
                       COUNT(DISTINCT practice_item_id) AS items_reviewed
                FROM practice_attempts
                WHERE session_id = ?
                   OR (
                     session_id IS NULL
                     AND created_at >= ? AND created_at <= ?
                   )
                """,
                (session_id, started_at, ended_at),
            ).fetchone()
        return {
            "attempts_recorded": int(row["attempts_recorded"] if row is not None else 0),
            "items_reviewed": int(row["items_reviewed"] if row is not None else 0),
        }

    def session_attempt_rows(self, session_id: str) -> list[dict[str, Any]]:
        """The session's attempts, oldest first, with what the session finish
        reads (the same session window as :meth:`session_attempt_counts`)."""

        session = self.fetch_session(session_id)
        if session is None:
            return []
        started_at = session["started_at"]
        ended_at = session["ended_at"] or utc_now_iso()
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, practice_item_id, learning_object_id, attempt_type,
                       hints_used, primed, correctness, evidence_facets_json, created_at
                FROM practice_attempts
                WHERE session_id = ?
                   OR (
                     session_id IS NULL
                     AND created_at >= ? AND created_at <= ?
                   )
                ORDER BY created_at, id
                """,
                (session_id, started_at, ended_at),
            ).fetchall()
        return [dict(row) for row in rows]

    def review_session_rows(self) -> list[dict[str, Any]]:
        """Reverse-chronological session spine for the Review surface."""

        with self.connection() as connection:
            sessions = connection.execute(
                "SELECT * FROM sessions WHERE ended_at IS NOT NULL ORDER BY ended_at DESC, id DESC"
            ).fetchall()
            result: list[dict[str, Any]] = []
            for session in sessions:
                attempts = connection.execute(
                    """
                    SELECT a.id, a.practice_item_id, a.learning_object_id,
                           a.created_at, s.surprise_direction
                    FROM practice_attempts a
                    LEFT JOIN attempt_surprise s ON s.attempt_id = a.id
                    WHERE a.session_id = ? OR (
                      a.session_id IS NULL AND a.created_at >= ? AND a.created_at <= ?
                    )
                    ORDER BY a.created_at, a.id
                    """,
                    (session["id"], session["started_at"], session["ended_at"]),
                ).fetchall()
                result.append(
                    dict(session)
                    | {
                        "attempts": [dict(row) for row in attempts],
                        "predictions_up": sum(row["surprise_direction"] == "positive" for row in attempts),
                        "predictions_down": sum(row["surprise_direction"] == "negative" for row in attempts),
                    }
                )
        return result

    def update_session_checkpoint(
        self,
        session_id: str,
        *,
        current_practice_item_id: str | None = None,
        current_answer: str | None = None,
        focus_block_state: Mapping[str, Any] | None = None,
        pending_grading_proposal: Mapping[str, Any] | None = None,
        readiness: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO session_checkpoints(
                  session_id, current_practice_item_id, current_answer,
                  focus_block_state_json, pending_grading_proposal_json,
                  readiness_json, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                  current_practice_item_id = excluded.current_practice_item_id,
                  current_answer = excluded.current_answer,
                  focus_block_state_json = excluded.focus_block_state_json,
                  pending_grading_proposal_json = excluded.pending_grading_proposal_json,
                  readiness_json = excluded.readiness_json,
                  updated_at = excluded.updated_at
                """,
                (
                    session_id,
                    current_practice_item_id,
                    current_answer,
                    _json(focus_block_state) if focus_block_state is not None else None,
                    _json(pending_grading_proposal) if pending_grading_proposal is not None else None,
                    _json(readiness) if readiness is not None else None,
                    now,
                ),
            )
            connection.commit()

    def fetch_session_checkpoint(self, session_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM session_checkpoints WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["focus_block_state"] = _loads(payload.pop("focus_block_state_json"), None)
        payload["pending_grading_proposal"] = _loads(payload.pop("pending_grading_proposal_json"), None)
        payload["readiness"] = _loads(payload.pop("readiness_json"), None)
        return payload

    def open_session_checkpoints_except(self, session_id: str) -> list[dict[str, Any]]:
        """The checkpoints of every OTHER open session (the ones
        :meth:`end_open_sessions_except` is about to end), decoded like
        :meth:`fetch_session_checkpoint`."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT checkpoint.session_id
                FROM session_checkpoints checkpoint
                JOIN sessions ON sessions.id = checkpoint.session_id
                WHERE sessions.ended_at IS NULL AND sessions.id != ?
                ORDER BY checkpoint.session_id
                """,
                (session_id,),
            ).fetchall()
        checkpoints = [self.fetch_session_checkpoint(str(row["session_id"])) for row in rows]
        return [checkpoint for checkpoint in checkpoints if checkpoint is not None]

    def clear_session_checkpoint(self, session_id: str) -> bool:
        with self.connection() as connection:
            cursor = connection.execute(
                "DELETE FROM session_checkpoints WHERE session_id = ?",
                (session_id,),
            )
            connection.commit()
            return cursor.rowcount > 0

    def clear_practice_checkpoint_for_item(self, session_id: str, practice_item_id: str) -> bool:
        """Clear this session's draft only while it still points at this card.

        A card the learner skipped (learner field F2's "I know this") must not
        reopen on restart; a draft the session has since moved to another card
        is left alone. Runs inside the caller's ``atomic()`` when there is one.
        """

        with self.connection() as connection:
            cursor = connection.execute(
                "DELETE FROM session_checkpoints WHERE session_id = ? AND current_practice_item_id = ?",
                (session_id, practice_item_id),
            )
            connection.commit()
            return cursor.rowcount > 0

    def acknowledge_practice_checkpoint(
        self,
        session_id: str,
        *,
        practice_item_id: str,
        submission_id: str,
    ) -> str:
        """Atomically clear only the practice checkpoint the client received.

        A post-submit route can unmount its Practice screen while a new item is
        already saving a draft in the same session.  A session-id-only DELETE
        lets the stale completion erase that newer checkpoint.  Holding an
        immediate SQLite write lock across compare + delete makes the expected
        item/retry key an acknowledgement token rather than a best-effort read.
        """

        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT current_practice_item_id, focus_block_state_json
                FROM session_checkpoints
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
            if row is None:
                return "already_absent"
            focus = _loads(row["focus_block_state_json"], None)
            practice = focus.get("practice") if isinstance(focus, dict) else None
            saved_submission_id = None
            if isinstance(practice, dict):
                saved_submission_id = practice.get("submissionId") or practice.get("submission_id")
            if (
                row["current_practice_item_id"] != practice_item_id
                or saved_submission_id != submission_id
            ):
                return "checkpoint_mismatch"
            cursor = connection.execute(
                "DELETE FROM session_checkpoints WHERE session_id = ?",
                (session_id,),
            )
            return "cleared" if cursor.rowcount > 0 else "checkpoint_mismatch"

    def insert_agent_run(self, run: Mapping[str, Any]) -> str:
        run_id = str(run.get("id") or new_ulid())
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO agent_runs(
                  id, purpose, model, provider, prompt_template, prompt_version,
                  sdk_version, codex_revision, provider_type, provider_revision,
                  input_context_hash, output_schema, started_at, completed_at,
                  status, error_message, est_input_tokens, est_output_tokens
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    run["purpose"],
                    run.get("model"),
                    run.get("provider", "codex"),
                    run.get("prompt_template"),
                    run.get("prompt_version"),
                    run.get("sdk_version"),
                    run.get("codex_revision"),
                    run.get("provider_type"),
                    run.get("provider_revision"),
                    run.get("input_context_hash"),
                    run.get("output_schema"),
                    run["started_at"],
                    run.get("completed_at"),
                    run.get("status", "running"),
                    run.get("error_message"),
                    # A7 (spec_diagnostic_augmentation_v1.md §2): the pre-flight
                    # budget, 0 when the caller does not estimate. Actuals are
                    # written at completion, where the provider has reported them.
                    _non_negative_tokens(run.get("est_input_tokens")),
                    _non_negative_tokens(run.get("est_output_tokens")),
                ),
            )
            connection.commit()
        return run_id

    def complete_agent_run(
        self,
        run_id: str,
        *,
        status: str = "completed",
        error_message: str | None = None,
        usage: TokenUsage | None = None,
        clock: Clock | None = None,
    ) -> bool:
        """Finalize a run, optionally recording what the provider charged for it.

        `usage` is what the client accumulated over every model call this run
        made (A7 / migration 131) — extended here rather than split into a
        second `record_agent_run_usage` method because usage is known exactly
        when the run ends, on both the success and the failure arm, and a
        separate call would double the writes and let the two drift apart.
        `usage=None` leaves the actual_* columns untouched, so a caller with no
        client in scope (or a second, redundant completion of the same run)
        cannot zero out a cost already recorded.
        """

        now = utc_now_iso(clock)
        with self.connection() as connection:
            if usage is None:
                cursor = connection.execute(
                    """
                    UPDATE agent_runs
                    SET completed_at = ?, status = ?, error_message = ?
                    WHERE id = ?
                    """,
                    (now, status, error_message, run_id),
                )
            else:
                cursor = connection.execute(
                    """
                    UPDATE agent_runs
                    SET completed_at = ?, status = ?, error_message = ?,
                        actual_input_tokens = ?, actual_output_tokens = ?
                    WHERE id = ?
                    """,
                    (
                        now,
                        status,
                        error_message,
                        _non_negative_tokens(usage.input_tokens),
                        _non_negative_tokens(usage.output_tokens),
                        run_id,
                    ),
                )
            connection.commit()
            return cursor.rowcount > 0

    def add_agent_run_usage(self, run_id: str, usage: TokenUsage) -> bool:
        """Add tokens to a run that was already finalized (A7).

        For the one shape `complete_agent_run` cannot express: a billed call that
        happens *after* the run is closed. `generate_authoring_proposal` closes
        its run before the best-effort item-repair pass, deliberately — a repair
        interrupt must not reopen a completed authoring run — but the repair
        still costs tokens that belong to that run's cost, not to whatever the
        client does next. Additive, so it is safe to call after any drain.
        """

        if usage.input_tokens <= 0 and usage.output_tokens <= 0:
            return False
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE agent_runs
                SET actual_input_tokens = actual_input_tokens + ?,
                    actual_output_tokens = actual_output_tokens + ?
                WHERE id = ?
                """,
                (
                    _non_negative_tokens(usage.input_tokens),
                    _non_negative_tokens(usage.output_tokens),
                    run_id,
                ),
            )
            connection.commit()
            return cursor.rowcount > 0

    def completed_agent_run_by_context(self, purpose: str, input_context_hash: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM agent_runs
                WHERE purpose = ? AND input_context_hash = ? AND status = 'completed'
                ORDER BY completed_at DESC, started_at DESC
                LIMIT 1
                """,
                (purpose, input_context_hash),
            ).fetchone()
        return dict(row) if row is not None else None

    def agent_run(self, run_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM agent_runs WHERE id = ?",
                (run_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def proposal_batch_for_agent_run(self, agent_run_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM proposed_patches
                WHERE agent_run_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (agent_run_id,),
            ).fetchone()
        return _decode_proposal_batch(row) if row is not None else None

    def proposal_batch(self, patch_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM proposed_patches WHERE id = ?",
                (patch_id,),
            ).fetchone()
        return _decode_proposal_batch(row) if row is not None else None

    def persist_proposal_batch(
        self,
        batch: Mapping[str, Any],
        items: Iterable[Mapping[str, Any]],
        *,
        join_pending: Mapping[str, Any] | None = None,
    ) -> str:
        """Write one proposal batch and its items.

        ``join_pending`` (a source ref) proposes each item once, however many
        callers name it (UX Phase 2, Codex review of ux-phase2-shell F6; Phase
        1 usability round 1: "Proposals grows on every practice, with
        duplicate error-type proposals"). An item whose ``item_type``,
        ``operation`` and effective identity already wait (a ``pending`` item;
        the identity is the edited payload's ``id`` when the item was edited,
        else the payload's, else the ``client_item_id``) is not written
        again: the ref joins the waiting item's batch's source refs instead,
        so that proposal keeps every caller that named it. The check and the
        write run under one write lock, so two callers at once cannot both
        write. Returns the new batch's id, or, when every item already waits,
        the first waiting batch the ref joined. Proposal tables are WORKFLOW:
        nothing replays or grades from them, so no persisted meaning changes.
        """

        batch_id = str(batch.get("id") or new_ulid())
        item_rows = list(items)
        client_ids = [str(item.get("client_item_id") or "") for item in item_rows]
        client_id_counts: dict[str, int] = {}
        for client_id in client_ids:
            client_id_counts[client_id] = client_id_counts.get(client_id, 0) + 1
        duplicate_client_ids = sorted(
            client_id
            for client_id, count in client_id_counts.items()
            if client_id and count > 1
        )
        if duplicate_client_ids:
            raise ValueError(
                "proposal contains duplicate client_item_id values: "
                + ", ".join(duplicate_client_ids)
            )
        with self.connection() as connection:
            if join_pending is not None:
                if not connection.in_transaction:
                    # Take the write lock BEFORE reading so the check-and-insert
                    # is one atomic step even across connections.
                    connection.execute("BEGIN IMMEDIATE")
                fresh: list[Mapping[str, Any]] = []
                joined: list[str] = []
                for item in item_rows:
                    # Match by what each waiting item would now create (fix
                    # round 2, verify 20261021-114726-Jrt7sA item 5): the
                    # payload editor can change a waiting item's ``id`` while
                    # its ``client_item_id`` keeps the old one, so the stale
                    # client id would join the wrong proposal (or miss the
                    # renamed one). Read under the same write lock as the insert.
                    identity = _proposal_item_identity(
                        item.get("client_item_id"), item.get("payload"), item.get("edited_payload")
                    )
                    waiting = next(
                        (
                            row
                            for row in connection.execute(
                                """
                                SELECT proposed_patch_id, client_item_id, payload_json, edited_payload_json
                                  FROM proposed_patch_items
                                 WHERE item_type = ? AND operation = ? AND decision = 'pending'
                                 ORDER BY created_at, id
                                """,
                                (item["item_type"], item["operation"]),
                            ).fetchall()
                            if _proposal_item_identity(
                                row["client_item_id"],
                                _loads(row["payload_json"], None),
                                _loads(row["edited_payload_json"], None),
                            )
                            == identity
                        ),
                        None,
                    )
                    if waiting is None:
                        fresh.append(item)
                    elif str(waiting["proposed_patch_id"]) not in joined:
                        joined.append(str(waiting["proposed_patch_id"]))
                ref = dict(join_pending)
                for patch_id in joined:
                    current = connection.execute(
                        "SELECT source_refs_json FROM proposed_patches WHERE id = ?", (patch_id,)
                    ).fetchone()
                    refs = _loads(current["source_refs_json"], []) if current is not None else []
                    if ref not in refs:
                        connection.execute(
                            "UPDATE proposed_patches SET source_refs_json = ?, updated_at = ? WHERE id = ?",
                            (_json([*refs, ref]), batch.get("updated_at", batch["created_at"]), patch_id),
                        )
                if joined and not fresh:
                    connection.commit()
                    return joined[0]
                item_rows = fresh
            connection.execute(
                """
                INSERT INTO proposed_patches(
                  id, agent_run_id, purpose, source_refs_json, summary,
                  status_cache, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id,
                    batch["agent_run_id"],
                    batch["purpose"],
                    _json(batch.get("source_refs", [])),
                    batch.get("summary"),
                    batch.get("status_cache", "pending"),
                    batch["created_at"],
                    batch.get("updated_at", batch["created_at"]),
                ),
            )
            # client_item_id -> DB id, so LLM-declared depends_on_client_item_ids
            # normalize into the dependency table (source-ingestion §10.2).
            client_to_db_id: dict[str, str] = {}
            dependency_edges: list[tuple[str, list[str]]] = []
            for item in item_rows:
                item_db_id = item.get("id") or new_ulid()
                client_to_db_id[str(item["client_item_id"])] = item_db_id
                depends_on = list(item.get("depends_on_client_item_ids") or [])
                if depends_on:
                    dependency_edges.append((item_db_id, [str(dep) for dep in depends_on]))
                connection.execute(
                    """
                    INSERT INTO proposed_patch_items(
                      id, proposed_patch_id, client_item_id, item_type, operation,
                      target_entity_type, target_entity_id, payload_json,
                      source_ref_ids_json, audit_json, edited_payload_json,
                      decision, validation_status, validation_errors_json,
                      applied_change_batch_id, decided_at, decided_by,
                      created_at, updated_at, dependency_status,
                      dependency_block_reason_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item_db_id,
                        batch_id,
                        item["client_item_id"],
                        item["item_type"],
                        item["operation"],
                        item.get("target_entity_type"),
                        item.get("target_entity_id"),
                        _json(item["payload"]),
                        _json(item.get("source_ref_ids", [])),
                        _json(item.get("audit")) if item.get("audit") is not None else None,
                        _json(item.get("edited_payload")) if item.get("edited_payload") is not None else None,
                        item.get("decision", "pending"),
                        item.get("validation_status", "valid"),
                        _json(item.get("validation_errors", [])),
                        item.get("applied_change_batch_id"),
                        item.get("decided_at"),
                        item.get("decided_by"),
                        item["created_at"],
                        item.get("updated_at", item["created_at"]),
                        item.get("dependency_status", "pending"),
                        _json(item.get("dependency_block_reason"))
                        if item.get("dependency_block_reason") is not None
                        else None,
                    ),
                )
            for item_db_id, depends_on in dependency_edges:
                for client_dep in depends_on:
                    dep_db_id = client_to_db_id.get(client_dep)
                    if dep_db_id is None or dep_db_id == item_db_id:
                        # An unknown or self-referential dependency is dropped
                        # rather than persisted as a dangling edge; the item's
                        # dependency_status carries any blocking reason.
                        continue
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO proposed_patch_item_dependencies(
                          proposed_patch_item_id, depends_on_patch_item_id
                        )
                        VALUES (?, ?)
                        """,
                        (item_db_id, dep_db_id),
                    )
            self._refresh_proposal_status(connection, batch_id, updated_at=batch.get("updated_at", batch["created_at"]))
            connection.commit()
        return batch_id

    def proposal_item_dependencies(self, item_id: str) -> list[str]:
        """DB ids this proposal item depends on (source-ingestion §10.2)."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT depends_on_patch_item_id
                FROM proposed_patch_item_dependencies
                WHERE proposed_patch_item_id = ?
                ORDER BY depends_on_patch_item_id
                """,
                (item_id,),
            ).fetchall()
        return [row["depends_on_patch_item_id"] for row in rows]

    def set_proposal_item_dependency_status(
        self,
        item_id: str,
        *,
        dependency_status: str,
        block_reason: Mapping[str, Any] | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE proposed_patch_items
                SET dependency_status = ?, dependency_block_reason_json = ?
                WHERE id = ?
                """,
                (
                    dependency_status,
                    _json(block_reason) if block_reason is not None else None,
                    item_id,
                ),
            )
            connection.commit()

    def consumer_pins_for_versions(
        self, version_ids: Sequence[str]
    ) -> list[dict[str, Any]]:
        """UNION projection (§1.5) of every consumer pin whose
        ``target_contract_version_id`` is in ``version_ids``: probe episodes,
        assessment reservations, and administrations. Read-only."""

        if not version_ids:
            return []
        placeholders = ",".join("?" for _ in version_ids)
        pins: list[dict[str, Any]] = []
        with self.connection() as connection:
            for kind, table, id_col in (
                ("probe_episode", "probe_episodes", "id"),
                ("assessment_reserve", "activity_surface_reservations", "id"),
                ("administration", "activity_administrations", "id"),
            ):
                rows = connection.execute(
                    f"""
                    SELECT {id_col} AS consumer_id, target_contract_version_id,
                           target_support_hash
                      FROM {table}
                     WHERE target_contract_version_id IN ({placeholders})
                    """,
                    tuple(version_ids),
                ).fetchall()
                for row in rows:
                    pins.append(
                        {
                            "consumer_kind": kind,
                            "consumer_id": row["consumer_id"],
                            "target_contract_version_id": row["target_contract_version_id"],
                            "target_support_hash": row["target_support_hash"],
                        }
                    )
        return pins

    def capture_local_transaction(
        self,
        *,
        source_id: str,
        client_idempotency_key: str,
        annotation: Mapping[str, Any] | None,
        anchor: Mapping[str, Any] | None,
        interaction_event: Mapping[str, Any],
        outbox: Mapping[str, Any],
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """The one local-first capture transaction (§5.3): create annotation +
        version + anchor + segments, append the typed interaction event, and write
        ONE durable outbox row -- all in a SINGLE SQLite transaction. On any error
        the whole thing rolls back (no acknowledgement, no orphan). Idempotent on
        client_idempotency_key: a retry returns the existing receipt untouched."""

        existing = self.capture_by_client_key(client_idempotency_key)
        if existing is not None:
            return {
                "annotation_id": existing["annotation_id"],
                "outbox_id": existing["id"],
                "interaction_event_id": existing["interaction_event_id"],
                "deduplicated": True,
            }

        now = utc_now_iso(clock)
        annotation_id: str | None = None
        event_id = new_ulid()
        outbox_id = new_ulid()
        connection = self.connection()
        try:
            connection.execute("BEGIN")
            if annotation is not None and anchor is not None:
                annotation_id = new_ulid()
                connection.execute(
                    "INSERT INTO source_annotations(id, source_id, created_at) VALUES (?, ?, ?)",
                    (annotation_id, source_id, now),
                )
                self._write_annotation_version(
                    connection, annotation_id=annotation_id, version_ordinal=1,
                    version=annotation, now=now,
                )
                self._write_anchor_version(
                    connection, annotation_id=annotation_id, version_ordinal=1, anchor=anchor, now=now
                )
                connection.execute(
                    "INSERT INTO source_annotation_events(id, annotation_id, event_type, payload_json, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (new_ulid(), annotation_id, "create", _json({"capture": True}), now),
                )
            ev = dict(interaction_event)
            connection.execute(
                """
                INSERT INTO interaction_events(
                  id, kind, subject_type, subject_id, administration_id, surface_id,
                  attempt_id, affect_tap_kind, attempt_duration_ms, payload_json,
                  origin, created_at, occurred_at, received_at, actor, client_id,
                  session_id, visit_id, payload_schema_version, source_id, revision_id,
                  render_view_id, locator_json, annotation_id, commitment_id, activity_id,
                  payload_hash, client_idempotency_key, privacy_locality, consent_context,
                  producer_version, app_version, policy_version, supersedes_event_id
                ) VALUES (?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, ?, ?, ?, ?, ?, NULL,
                          NULL, ?, NULL, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, NULL,
                          NULL, NULL, NULL, NULL)
                """,
                (
                    event_id,
                    ev["kind"],
                    ev.get("subject_type"),
                    ev.get("subject_id"),
                    _json(ev.get("payload", {})),
                    ev.get("origin", "learner"),
                    now,
                    now,
                    now,
                    ev.get("session_id"),
                    ev.get("payload_schema_version", "reader-capture-v1"),
                    source_id,
                    ev.get("revision_id"),
                    ev.get("render_view_id"),
                    _json(ev["locator"]) if ev.get("locator") is not None else None,
                    annotation_id,
                    ev.get("payload_hash"),
                    client_idempotency_key,
                    ev.get("privacy_locality", "local_private"),
                ),
            )
            connection.execute(
                """
                INSERT INTO reader_capture_outbox(
                  id, client_idempotency_key, capture_kind, state, payload_json,
                  annotation_id, commitment_id, source_id, revision_id, render_view_id,
                  interaction_event_id, target_ref, attempts, last_error,
                  created_at, updated_at, drained_at
                ) VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, NULL, 0, NULL, ?, ?, NULL)
                """,
                (
                    outbox_id,
                    client_idempotency_key,
                    outbox["capture_kind"],
                    _json(outbox.get("payload", {})),
                    annotation_id,
                    outbox.get("commitment_id"),
                    source_id,
                    outbox.get("revision_id"),
                    outbox.get("render_view_id"),
                    event_id,
                    now,
                    now,
                ),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return {
            "annotation_id": annotation_id,
            "outbox_id": outbox_id,
            "interaction_event_id": event_id,
            "deduplicated": False,
        }

    # ------------------------------------------------------------------
    # Vault epigraphs (migration 158): model-authored quotes/haiku about the
    # material, one batch per completed synthesis. Append-only history; the
    # Start screen reads the newest N.
    # ------------------------------------------------------------------

    def insert_vault_epigraphs(
        self,
        *,
        subject_id: str,
        source_set_id: str | None,
        synthesis_run_id: str | None,
        mode: str,
        epigraphs: Sequence[Mapping[str, Any]],
        prompt_version: str,
        provider: str | None,
        model: str | None,
        clock: Clock | None = None,
    ) -> list[str]:
        """Persist one synthesis's batch. ``epigraphs`` entries carry ``kind``
        and ``text`` (haiku lines already "\n"-joined). The batch shares one
        ``created_at``; ``ordinal`` records model order because ULIDs minted
        in one millisecond do not sort by insertion."""

        now = utc_now_iso(clock)
        ids: list[str] = []
        with self.connection() as connection:
            for ordinal, entry in enumerate(epigraphs):
                epigraph_id = f"vep_{new_ulid()}"
                connection.execute(
                    "INSERT INTO vault_epigraphs("
                    "  id, subject_id, source_set_id, synthesis_run_id, mode, kind,"
                    "  text, prompt_version, provider, model, ordinal, created_at"
                    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        epigraph_id,
                        subject_id,
                        source_set_id,
                        synthesis_run_id,
                        mode,
                        str(entry["kind"]),
                        str(entry["text"]),
                        prompt_version,
                        provider,
                        model,
                        ordinal,
                        now,
                    ),
                )
                ids.append(epigraph_id)
            connection.commit()
        return ids

    def recent_vault_epigraphs(
        self, *, subject_id: str | None = None, limit: int = 12
    ) -> list[dict[str, Any]]:
        """Newest first; ``subject_id=None`` spans the whole vault."""

        sql = "SELECT * FROM vault_epigraphs"
        params: list[Any] = []
        if subject_id:
            sql += " WHERE subject_id = ?"
            params.append(subject_id)
        sql += " ORDER BY created_at DESC, ordinal DESC, id DESC LIMIT ?"
        params.append(int(limit))
        with self.connection() as connection:
            rows = connection.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # P0.2 grader channel (spec_p0_measurement_correctness §3.1-§3.3, §4.7).
    # All INSERT-only; model/schema/event rows never receive an UPDATE. The two
    # exceptions are pure projection-head pointers on activity_observations
    # (active_interpretation_id) which are not append-only event tables.
    # ------------------------------------------------------------------

    def ensure_outcome_schema(
        self, *, slug: str, kind: str, clock: Clock | None = None
    ) -> str:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT id FROM outcome_schemas WHERE slug = ?", (slug,)
            ).fetchone()
            if row is not None:
                return row["id"]
            schema_id = new_ulid()
            connection.execute(
                "INSERT INTO outcome_schemas(id, slug, kind, created_at) VALUES (?, ?, ?, ?)",
                (schema_id, slug, kind, utc_now_iso(clock)),
            )
            connection.commit()
            return schema_id

    def insert_calibration_model(
        self, *, model: Mapping[str, Any], alphas: Mapping[str, Mapping[str, float]],
        clock: Clock | None = None,
    ) -> str:
        """Insert one immutable model version + its per-Z Dirichlet alpha rows.

        Content-addressed: short-circuits on an existing ``content_hash`` (M1) so a
        check-then-act race can never mint a duplicate immutable model. The
        UNIQUE(content_hash) backstop (migration 070) is the hard guarantee."""

        existing = self.find_calibration_model_by_hash(model["content_hash"])
        if existing is not None:
            return existing["id"]

        model_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO grader_calibration_models(
                  id, grader_provider, grader_model_revision, grading_prompt_version,
                  grader_output_schema_version, grader_identity_hash, semver,
                  parent_model_id, content_hash, scope_level, outcome_schema_id,
                  outcome_schema_version, domain, length_bucket, backoff_chain_json,
                  status, count_heuristic_prior, count_planted_sim, count_exploratory_em,
                  count_adjudicated_anchor, count_held_out_evaluation,
                  prequential_log_loss, multiclass_brier, reliability_bins_json,
                  sample_count, eval_time_range_json, prior_concentration,
                  provenance_json, evidence_manifest_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model_id,
                    model.get("grader_provider"),
                    model.get("grader_model_revision"),
                    model.get("grading_prompt_version"),
                    model.get("grader_output_schema_version"),
                    model.get("grader_identity_hash"),
                    model["semver"],
                    model.get("parent_model_id"),
                    model["content_hash"],
                    model["scope_level"],
                    model.get("outcome_schema_id"),
                    model.get("outcome_schema_version"),
                    model.get("domain"),
                    model.get("length_bucket"),
                    model["backoff_chain_json"],
                    model["status"],
                    int(model.get("count_heuristic_prior", 0)),
                    int(model.get("count_planted_sim", 0)),
                    int(model.get("count_exploratory_em", 0)),
                    int(model.get("count_adjudicated_anchor", 0)),
                    int(model.get("count_held_out_evaluation", 0)),
                    model.get("prequential_log_loss"),
                    model.get("multiclass_brier"),
                    model.get("reliability_bins_json"),
                    model.get("sample_count"),
                    model.get("eval_time_range_json"),
                    model.get("prior_concentration"),
                    model.get("provenance_json"),
                    model.get("evidence_manifest_json"),
                    now,
                ),
            )
            for true_class, alpha in alphas.items():
                connection.execute(
                    """
                    INSERT INTO grader_calibration_alphas(
                      id, model_id, true_class, alpha_json, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (new_ulid(), model_id, true_class, _json(dict(alpha)), now),
                )
            connection.commit()
        return model_id

    def active_interpretation_for_observation(self, observation_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT gi.* FROM grade_interpretations gi
                  JOIN activity_observations o ON o.active_interpretation_id = gi.id
                 WHERE o.id = ?
                """,
                (observation_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def grade_head_review(self, observation_id: str, interpretation_id: str) -> dict[str, Any] | None:
        """How a review made this interpretation the observation's head, or None
        when the grade pipeline wrote it: ``{"kind": "adjudication",
        "adjudication_id": ...}`` for an adjudication's result, ``{"kind":
        "quarantine"}`` for a quarantined head, ``{"kind": "review_flag"}`` for a
        head a review request activated (``interpretation_activated``)."""

        with self.connection() as connection:
            adjudication = connection.execute(
                "SELECT id FROM grade_adjudications WHERE resulting_interpretation_id = ? "
                "ORDER BY created_at DESC, id DESC LIMIT 1",
                (interpretation_id,),
            ).fetchone()
            if adjudication is not None:
                return {"kind": "adjudication", "adjudication_id": str(adjudication[0])}
            state = connection.execute(
                "SELECT quarantine_state FROM grade_interpretations WHERE id = ?", (interpretation_id,)
            ).fetchone()
            if state is not None and state[0] == "quarantined":
                return {"kind": "quarantine"}
            activated = connection.execute(
                "SELECT 1 FROM measurement_events WHERE observation_id = ? "
                "AND kind IN ('interpretation_activated', 'grade_quarantined') "
                "AND json_extract(payload_json, '$.interpretation_id') = ? LIMIT 1",
                (observation_id, interpretation_id),
            ).fetchone()
        return {"kind": "review_flag"} if activated is not None else None

    def pending_grade_reviews(self) -> list[dict[str, Any]]:
        """Active-head grade interpretations flagged for review or quarantined
        (§4.4, §5). Joined to the observation + administration so the CLI can order
        by influence. Quarantined first, then influence-flagged, then oldest.

        An attempt's grade is its newest observation's head, the one the
        authoritative ledger reads (``observation_ledger``): a vault rebuilt
        before replay reused observations holds one copy per rebuild, and an
        older copy's flag is no pending review (an adjudication of it would
        never reach the projection). An observation with no attempt is listed
        as before."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT gi.*, o.id AS observation_id_join,
                       o.attempt_id AS attempt_id,
                       o.surface_id AS surface_id,
                       o.evidence_eligibility AS evidence_eligibility
                  FROM grade_interpretations gi
                  JOIN activity_observations o ON o.active_interpretation_id = gi.id
                 WHERE (gi.review_flag = 1 OR gi.quarantine_state = 'quarantined')
                   AND (o.attempt_id IS NULL OR o.id = (
                        SELECT newest.id FROM activity_observations AS newest
                         WHERE newest.attempt_id = o.attempt_id
                         ORDER BY newest.created_at DESC, newest.id DESC
                         LIMIT 1))
                 ORDER BY
                   CASE WHEN gi.quarantine_state = 'quarantined' THEN 0 ELSE 1 END,
                   CASE WHEN gi.influence_flag = 1 THEN 0 ELSE 1 END,
                   CASE WHEN o.evidence_eligibility = 'terminal' THEN 0
                        WHEN o.evidence_eligibility = 'diagnostic' THEN 1 ELSE 2 END,
                   gi.created_at ASC
                """
            ).fetchall()
        return [dict(r) for r in rows]

    def causal_hypotheses_for_learning_object(
        self,
        learning_object_id: str,
        *,
        statuses: Iterable[str] = ("candidate",),
        latest_only: bool = True,
        statement_normalized: str | None = None,
        groups: Mapping[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Hypothesis heads on an LO; ``statement_normalized`` is a recurrence key.

        The key filter runs through :func:`learnloop.recurrence.recurrence_key`
        (Slice 1 §7.6) rather than SQL equality, so Slice 2 T1's recurrence
        groups apply without touching this query. A raw normalized statement
        is accepted too and resolves to its group. ``groups`` is the caller's
        already-loaded group map (loaded here when omitted).
        """

        status_list = [str(value) for value in statuses]
        if not status_list:
            return []
        placeholders = ",".join("?" for _ in status_list)
        latest_clause = (
            """
            AND h.version = (
              SELECT MAX(head.version)
                FROM causal_hypotheses head
               WHERE head.episode_key = h.episode_key
            )
            """
            if latest_only
            else ""
        )
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT h.* FROM causal_hypotheses h
                 WHERE h.learning_object_id = ?
                   AND h.status IN ({placeholders})
                   {latest_clause}
                 ORDER BY h.created_at, h.id
                """,
                (learning_object_id, *status_list),
            ).fetchall()
        decoded = [_decode_causal_hypothesis(row) for row in rows]
        if statement_normalized is None:
            return decoded
        if groups is None:
            groups = self.recurrence_group_map()
        key = key_for_statement(statement_normalized, groups)
        return [row for row in decoded if recurrence_key(row, groups) == key]

    def expired_cold_retry_tasks_without_outcome(self) -> list[dict[str, Any]]:
        """Expired repair-lane retries whose terminal disposition is unrecorded.

        The expiry UPDATE inside ``due_followup_tasks`` is silent by design (it
        is a queue transition, not a label); this is the reconciliation read the
        per-attempt sweep uses to turn each expiry into a typed §4.3 row.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT ft.* FROM followup_tasks ft
                LEFT JOIN causal_cold_outcomes cco ON cco.followup_task_id = ft.id
                WHERE ft.kind = 'cold_retry' AND ft.status = 'expired'
                  AND cco.id IS NULL
                ORDER BY ft.updated_at, ft.id
                """
            ).fetchall()
        return [_decode_followup_task(row) for row in rows]

    def proposal_batches(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM proposed_patches ORDER BY created_at DESC"
            ).fetchall()
        return [_decode_proposal_batch(row) for row in rows]

    def proposal_items(self, patch_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM proposed_patch_items
                WHERE proposed_patch_id = ?
                ORDER BY created_at, client_item_id
                """,
                (patch_id,),
            ).fetchall()
        return [_decode_proposal_item(row) for row in rows]

    def persona_gate_audit_rows(self, *, since: str | None = None) -> list[dict[str, Any]]:
        """Every proposal item carrying a §3.0 persona-gate audit (plan item 5.3).

        The projection is deliberately narrow — the gate's typed verdict fields
        plus the reviewer's later ``decision`` — because its one consumer
        (``persona_gate.gate_precision``) is a rate over gate predictions and must
        not accidentally acquire a second definition of the verdict by re-deriving
        it from the payload. ``decision`` is returned as ``reviewer_decision`` to
        keep it from colliding with the gate's own ``decision`` arm.
        """

        clauses = ["json_extract(audit_json, '$.persona_gate') IS NOT NULL"]
        parameters: list[Any] = []
        if since is not None:
            clauses.append("created_at >= ?")
            parameters.append(since)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id AS proposal_item_id,
                       proposed_patch_id AS patch_id,
                       client_item_id,
                       created_at,
                       decision AS reviewer_decision,
                       json_extract(audit_json, '$.persona_gate.instrument_class') AS instrument_class,
                       json_extract(audit_json, '$.persona_gate.tier') AS tier,
                       json_extract(audit_json, '$.persona_gate.decision') AS decision,
                       json_extract(audit_json, '$.persona_gate.reason') AS reason
                  FROM proposed_patch_items
                 WHERE {' AND '.join(clauses)}
                 ORDER BY created_at, id
                """,
                tuple(parameters),
            ).fetchall()
        return [dict(row) for row in rows]

    def proposal_item(self, item_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM proposed_patch_items WHERE id = ?",
                (item_id,),
            ).fetchone()
        return _decode_proposal_item(row) if row is not None else None

    def proposal_items_by_client_id(self, client_item_id: str) -> list[dict[str, Any]]:
        """All proposal items sharing a ``client_item_id`` (used to dedupe re-proposals)."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM proposed_patch_items WHERE client_item_id = ?",
                (client_item_id,),
            ).fetchall()
        return [_decode_proposal_item(row) for row in rows]

    def pending_invalid_proposal_items(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM proposed_patch_items
                WHERE decision = 'pending' AND validation_status = 'invalid'
                ORDER BY created_at, id
                """
            ).fetchall()
        return [_decode_proposal_item(row) for row in rows]

    def update_proposal_item_edited_payload(
        self,
        item_id: str,
        *,
        edited_payload: Mapping[str, Any],
        validation_status: str,
        validation_errors: list[str],
        clock: Clock | None = None,
    ) -> bool:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE proposed_patch_items
                SET edited_payload_json = ?,
                    validation_status = ?,
                    validation_errors_json = ?,
                    updated_at = ?
                WHERE id = ? AND decision = 'pending'
                """,
                (_json(edited_payload), validation_status, _json(validation_errors), now, item_id),
            )
            patch_row = connection.execute(
                "SELECT proposed_patch_id FROM proposed_patch_items WHERE id = ?",
                (item_id,),
            ).fetchone()
            if patch_row is not None:
                self._refresh_proposal_status(connection, patch_row["proposed_patch_id"], updated_at=now)
            connection.commit()
            return cursor.rowcount > 0

    def update_proposal_item_validation(
        self,
        item_id: str,
        *,
        validation_status: str,
        validation_errors: list[str],
        clock: Clock | None = None,
    ) -> bool:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE proposed_patch_items
                SET validation_status = ?,
                    validation_errors_json = ?,
                    updated_at = ?
                WHERE id = ? AND decision = 'pending'
                """,
                (validation_status, _json(validation_errors), now, item_id),
            )
            patch_row = connection.execute(
                "SELECT proposed_patch_id FROM proposed_patch_items WHERE id = ?",
                (item_id,),
            ).fetchone()
            if patch_row is not None:
                self._refresh_proposal_status(connection, patch_row["proposed_patch_id"], updated_at=now)
            connection.commit()
            return cursor.rowcount > 0

    def pending_proposal_items(self, patch_id: str, item_ids: list[str] | None = None) -> list[dict[str, Any]]:
        parameters: list[Any] = [patch_id]
        item_filter = ""
        if item_ids:
            placeholders = ",".join("?" for _ in item_ids)
            item_filter = f" AND id IN ({placeholders})"
            parameters.extend(item_ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM proposed_patch_items
                WHERE proposed_patch_id = ? AND decision = 'pending'{item_filter}
                ORDER BY created_at, client_item_id
                """,
                parameters,
            ).fetchall()
        return [_decode_proposal_item(row) for row in rows]

    def record_applied_proposal_item(
        self,
        *,
        proposal_item_id: str,
        change_batch: Mapping[str, Any],
        content_events: Iterable[Mapping[str, Any]],
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO change_batches(
                  id, proposed_patch_item_id, reason, origin, summary, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    change_batch["id"],
                    proposal_item_id,
                    change_batch.get("reason", "proposal_accept"),
                    change_batch.get("origin", "codex"),
                    change_batch.get("summary"),
                    change_batch["created_at"],
                ),
            )
            for event in content_events:
                connection.execute(
                    """
                    INSERT INTO content_events(
                      id, change_batch_id, event_type, subject, entity_type,
                      entity_id, origin, review_status, summary, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event["id"],
                        change_batch["id"],
                        event["event_type"],
                        event.get("subject"),
                        event["entity_type"],
                        event["entity_id"],
                        event.get("origin", "codex"),
                        event.get("review_status", "accepted"),
                        event.get("summary"),
                        event["created_at"],
                    ),
                )
            connection.execute(
                """
                UPDATE proposed_patch_items
                SET decision = 'accepted',
                    applied_change_batch_id = ?,
                    decided_at = ?,
                    decided_by = 'learner',
                    updated_at = ?
                WHERE id = ?
                """,
                (change_batch["id"], now, now, proposal_item_id),
            )
            patch_row = connection.execute(
                "SELECT proposed_patch_id FROM proposed_patch_items WHERE id = ?",
                (proposal_item_id,),
            ).fetchone()
            if patch_row is not None:
                self._refresh_proposal_status(connection, patch_row["proposed_patch_id"], updated_at=now)
            connection.commit()

    def record_content_events(self, events: Iterable[Mapping[str, Any]]) -> int:
        count = 0
        with self.connection() as connection:
            for event in events:
                connection.execute(
                    """
                    INSERT INTO content_events(
                      id, change_batch_id, event_type, subject, entity_type,
                      entity_id, origin, review_status, summary, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.get("id") or new_ulid(),
                        event.get("change_batch_id"),
                        event["event_type"],
                        event.get("subject"),
                        event["entity_type"],
                        event["entity_id"],
                        event.get("origin", "codex"),
                        event.get("review_status"),
                        event.get("summary"),
                        event["created_at"],
                    ),
                )
                count += 1
            connection.commit()
        return count

    def content_events_for_entity(self, entity_type: str, entity_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM content_events
                WHERE entity_type = ? AND entity_id = ?
                ORDER BY created_at DESC, id
                """,
                (entity_type, entity_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def active_source_events_for_entity(self, entity_type: str, entity_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT
                  content_events.rowid AS _rowid,
                  content_events.*,
                  proposed_patch_items.payload_json AS _proposal_payload_json,
                  proposed_patch_items.edited_payload_json AS _proposal_edited_payload_json
                FROM content_events
                LEFT JOIN change_batches ON change_batches.id = content_events.change_batch_id
                LEFT JOIN proposed_patch_items ON proposed_patch_items.id = change_batches.proposed_patch_item_id
                WHERE content_events.entity_type = ? AND content_events.entity_id = ?
                ORDER BY content_events.rowid
                """,
                (entity_type, entity_id),
            ).fetchall()
        last_grounding_rowid = 0
        for row in rows:
            if (
                row["event_type"] in {"created", "updated"}
                and row["review_status"] == "accepted"
                and _content_event_has_source_grounding(row)
            ):
                last_grounding_rowid = max(last_grounding_rowid, int(row["_rowid"]))
        active = []
        for row in rows:
            if row["event_type"] not in {"source_span_changed", "source_span_removed"}:
                continue
            if int(row["_rowid"]) <= last_grounding_rowid:
                continue
            payload = dict(row)
            payload.pop("_rowid", None)
            payload.pop("_proposal_payload_json", None)
            payload.pop("_proposal_edited_payload_json", None)
            active.append(payload)
        return active

    def reject_applied_proposal_item(
        self,
        proposal_item_id: str,
        *,
        content_event: Mapping[str, Any],
        decided_by: str = "learner",
        clock: Clock | None = None,
    ) -> bool:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            item_row = connection.execute(
                """
                SELECT proposed_patch_id FROM proposed_patch_items
                WHERE id = ? AND decision = 'accepted'
                """,
                (proposal_item_id,),
            ).fetchone()
            if item_row is None:
                return False
            connection.execute(
                """
                INSERT INTO content_events(
                  id, change_batch_id, event_type, subject, entity_type,
                  entity_id, origin, review_status, summary, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    content_event.get("id") or new_ulid(),
                    content_event.get("change_batch_id"),
                    content_event["event_type"],
                    content_event.get("subject"),
                    content_event["entity_type"],
                    content_event["entity_id"],
                    content_event.get("origin", "codex"),
                    content_event.get("review_status", "rejected"),
                    content_event.get("summary"),
                    content_event["created_at"],
                ),
            )
            connection.execute(
                """
                UPDATE proposed_patch_items
                SET decision = 'rejected',
                    decided_at = ?,
                    decided_by = ?,
                    updated_at = ?
                WHERE id = ? AND decision = 'accepted'
                """,
                (now, decided_by, now, proposal_item_id),
            )
            self._refresh_proposal_status(connection, item_row["proposed_patch_id"], updated_at=now)
            connection.commit()
        return True

    def set_proposal_item_decision(
        self,
        patch_id: str,
        decision: str,
        item_ids: list[str] | None = None,
        *,
        decided_by: str = "learner",
        clock: Clock | None = None,
    ) -> int:
        now = utc_now_iso(clock)
        parameters: list[Any] = [decision, now, decided_by, now, patch_id]
        item_filter = ""
        if item_ids:
            placeholders = ",".join("?" for _ in item_ids)
            item_filter = f" AND id IN ({placeholders})"
            parameters.extend(item_ids)
        with self.connection() as connection:
            cursor = connection.execute(
                f"""
                UPDATE proposed_patch_items
                SET decision = ?, decided_at = ?, decided_by = ?, updated_at = ?
                WHERE proposed_patch_id = ? AND decision = 'pending'{item_filter}
                """,
                parameters,
            )
            self._refresh_proposal_status(connection, patch_id, updated_at=now)
            connection.commit()
            return cursor.rowcount

    def delete_proposal_item(self, item_id: str, *, clock: Clock | None = None) -> bool:
        """Permanently remove a proposal item row, refreshing its batch status."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            row = connection.execute(
                "SELECT proposed_patch_id FROM proposed_patch_items WHERE id = ?",
                (item_id,),
            ).fetchone()
            if row is None:
                return False
            cursor = connection.execute(
                "DELETE FROM proposed_patch_items WHERE id = ?",
                (item_id,),
            )
            self._refresh_proposal_status(connection, row["proposed_patch_id"], updated_at=now)
            connection.commit()
            return cursor.rowcount > 0

    def reset_proposal_item_decision(
        self,
        patch_id: str,
        item_ids: list[str] | None = None,
        *,
        clock: Clock | None = None,
    ) -> int:
        """Reset a decided item back to ``pending`` — the inbox "undo" action.

        Scoped to the only reversible-without-side-effects case: a ``rejected`` item
        that was never applied to disk (``applied_change_batch_id IS NULL``). Accepted
        items (and rejected-after-revert items) carry a change batch and are excluded,
        so undo can never resurrect a proposal whose entity has already been written
        and would collide on re-accept.
        """

        now = utc_now_iso(clock)
        parameters: list[Any] = [now, patch_id]
        item_filter = ""
        if item_ids:
            placeholders = ",".join("?" for _ in item_ids)
            item_filter = f" AND id IN ({placeholders})"
            parameters.extend(item_ids)
        with self.connection() as connection:
            cursor = connection.execute(
                f"""
                UPDATE proposed_patch_items
                SET decision = 'pending', decided_at = NULL, decided_by = NULL, updated_at = ?
                WHERE proposed_patch_id = ?
                  AND decision = 'rejected'
                  AND applied_change_batch_id IS NULL{item_filter}
                """,
                parameters,
            )
            self._refresh_proposal_status(connection, patch_id, updated_at=now)
            connection.commit()
            return cursor.rowcount

    def find_record(self, identifier: str) -> tuple[str, dict[str, Any]] | None:
        tables: list[tuple[str, str, str, Any]] = [
            ("practice_attempt", "practice_attempts", "id", _decode_attempt),
            ("grading_evidence", "grading_evidence", "id", dict),
            ("error_event", "error_events", "id", _decode_error_event),
            ("attempt_surprise", "attempt_surprise", "attempt_id", _decode_surprise),
            ("practice_item_state", "practice_item_state", "practice_item_id", dict),
            ("learning_object_mastery", "learning_object_mastery", "learning_object_id", dict),
            ("facet_uncertainty", "facet_uncertainty", "id", _facet_uncertainty_state),
            ("learner_claim", "learner_claims", "id", dict),
            ("lo_probe_state", "lo_probe_state", "learning_object_id", _probe_state_record),
            ("hypothesis_set", "hypothesis_sets", "id", _decode_hypothesis_set),
            ("learner_state_belief", "learner_state_beliefs", "id", dict),
            ("intervention_need", "intervention_needs", "id", _decode_intervention_need),
            ("elicitation_event", "elicitation_events", "id", _decode_elicitation_event),
            ("decision_feature", "decision_features", "id", _decode_decision_features),
            ("proposal", "proposed_patches", "id", _decode_proposal_batch),
            ("proposal_item", "proposed_patch_items", "id", _decode_proposal_item),
            ("change_batch", "change_batches", "id", dict),
            ("content_event", "content_events", "id", dict),
            ("scheduler_explanation", "scheduler_explanations", "id", _decode_scheduler_explanation),
            ("scheduler_slate", "scheduler_slates", "id", _decode_scheduler_slate),
            ("scheduler_slate_candidate", "scheduler_slate_candidates", "id", _decode_scheduler_slate_candidate),
            ("learning_outcome_label", "learning_outcome_labels", "id", _decode_learning_outcome_label),
            ("session", "sessions", "id", dict),
            ("session_checkpoint", "session_checkpoints", "session_id", dict),
            ("observation_template", "observation_templates", "id", _decode_observation_template),
            ("observation_event", "observation_events", "id", _decode_observation_event),
            ("agent_run", "agent_runs", "id", dict),
            ("causal_hypothesis", "causal_hypotheses", "id", _decode_causal_hypothesis),
        ]
        with self.connection() as connection:
            for label, table, column, decoder in tables:
                row = connection.execute(f"SELECT * FROM {table} WHERE {column} = ? LIMIT 1", (identifier,)).fetchone()
                if row is not None:
                    return label, decoder(row)
        return None

    def _refresh_proposal_status(self, connection: sqlite3.Connection, patch_id: str, *, updated_at: str) -> None:
        rows = connection.execute(
            """
            SELECT decision, validation_status, COUNT(*) AS count
            FROM proposed_patch_items
            WHERE proposed_patch_id = ?
            GROUP BY decision, validation_status
            """,
            (patch_id,),
        ).fetchall()
        if not rows:
            return
        total = sum(row["count"] for row in rows)
        accepted = sum(row["count"] for row in rows if row["decision"] == "accepted")
        rejected = sum(row["count"] for row in rows if row["decision"] == "rejected")
        pending = sum(row["count"] for row in rows if row["decision"] == "pending")
        invalid = sum(row["count"] for row in rows if row["validation_status"] == "invalid")
        if invalid == total:
            status = "invalid"
        elif accepted == total:
            status = "accepted"
        elif rejected == total:
            status = "rejected"
        elif accepted > 0 or rejected > 0:
            status = "partially_accepted"
        elif pending == total:
            status = "pending"
        else:
            status = "pending"
        connection.execute(
            "UPDATE proposed_patches SET status_cache = ?, updated_at = ? WHERE id = ?",
            (status, updated_at, patch_id),
        )

    def _insert_practice_attempt(self, connection: sqlite3.Connection, attempt: Mapping[str, Any]) -> None:
        columns = [
            "id", "practice_item_id", "learning_object_id", "subject", "concept", "practice_mode",
            "attempt_type", "learner_answer_md", "evidence_facets_json", "evidence_weights_json",
            "rubric_score", "correctness", "confidence", "latency_seconds", "hints_used",
            "error_type", "grader_confidence", "manual_review", "manual_review_reason",
            "created_at", "updated_at", "session_id", "scheduler_slate_id", "scheduler_candidate_id",
            "primed", "probe_presentation_id", "answer_confidence", "submission_id",
            "declared_dont_know", "collection_version", "entry_surface", "evidence_origin",
        ]
        values: list[Any] = [
            attempt["id"],
            attempt["practice_item_id"],
            attempt["learning_object_id"],
            attempt.get("subject"),
            attempt.get("concept"),
            attempt["practice_mode"],
            attempt["attempt_type"],
            attempt.get("learner_answer_md"),
            _json(attempt.get("evidence_facets", [])),
            _json(attempt.get("evidence_weights", {})),
            attempt.get("rubric_score"),
            attempt.get("correctness"),
            attempt.get("confidence"),
            attempt.get("latency_seconds"),
            attempt.get("hints_used", 0),
            attempt.get("error_type"),
            attempt.get("grader_confidence"),
            1 if attempt.get("manual_review") else 0,
            attempt.get("manual_review_reason"),
            attempt["created_at"],
            attempt.get("updated_at"),
            attempt.get("session_id"),
            attempt.get("scheduler_slate_id"),
            attempt.get("scheduler_candidate_id"),
            1 if attempt.get("primed") else 0,
            attempt.get("probe_presentation_id"),
            attempt.get("answer_confidence"),
            attempt.get("submission_id"),
            1 if attempt.get("declared_dont_know") else 0,
            attempt.get("collection_version", COLLECTION_VERSION),
            attempt.get("entry_surface", "unspecified"),
            attempt.get("evidence_origin", "unknown"),
        ]
        if attempt.get("declared_stuck"):
            # mvp-0.13 (migration 178). Written only when set, so a database
            # attached below 178 still records every ordinary attempt (the
            # column defaults to 0); a stuck answer there fails loudly.
            columns.append("declared_stuck")
            values.append(1)
        if attempt.get("reference_status") not in (None, "not_applicable"):
            # Canonical sources S1 (migration 188): the served item's answer-key
            # status, recorded once at attempt time (C3). Written only when it
            # says something, like declared_stuck.
            columns.append("reference_status")
            values.append(attempt["reference_status"])
        if attempt.get("received_at") is not None:
            # Router objective RO1 (migration 244): when the attempt became
            # known, written only where created_at is not the write time (exam
            # seeding). Written only when set, like the AD1 columns below.
            columns.extend(("received_at", "received_at_source"))
            values.extend((attempt["received_at"], attempt.get("received_at_source") or "recorded"))
        for column in ("difficulty_rating", "first_hint_progress"):
            if attempt.get(column) is not None:
                # Adaptive difficulty AD1 (migration 213): written only when
                # set, so a database attached below 213 still records every
                # attempt without them.
                columns.append(column)
                values.append(attempt[column])
        presentation_id = _bindable_plan_presentation(connection, attempt)
        if presentation_id is not None:
            # Router R2a (migration 202): the plan presentation this attempt
            # answers. Checked in this transaction; a wrong or consumed id
            # leaves the attempt unbound (binding never fails a submit).
            columns.append("plan_presentation_id")
            values.append(presentation_id)
        connection.execute(
            f"INSERT INTO practice_attempts({', '.join(columns)}) "
            f"VALUES ({', '.join('?' for _ in columns)})",
            values,
        )
        if attempt.get("active_seconds") is not None:
            # Recognition and effort RE0 (migration 252): the active seconds follow the row in their own savepoint, as
            # RO0's columns do, so a refused write leaves the attempt standing with them null (and a vault below 252 has
            # no such column). Null is never written: a surface that sends no clock reads as missing.
            from learnloop.db.stores import router_objective as receipts

            receipts.fill_receipt(connection, "practice_attempts", attempt["id"],
                                  {"active_seconds": attempt["active_seconds"]})

    def _record_attempt_practice_item_state(
        self,
        connection: sqlite3.Connection,
        state: PracticeItemState,
    ) -> None:
        """A live attempt's write to its item's scheduling row.

        Mobile PR-4 (the reverse of PR-2's race, ``spec_mobile_tailnet_v1``
        §9.3): content sync owns ``active`` and ``content_hash``, and an
        attempt owns the memory state. The attempt computed both content
        columns from the vault it loaded, which a content sync in another
        process (the desktop's watcher, the phone host's reload) may have
        moved past while the answer was being graded; writing them back would
        reopen an item the sync just closed, or restore an old hash. So an
        existing row takes only the scheduling columns and the last-attempt
        time, and ``active`` can only close: a diagnostic probe's single use
        (``active = 0``) still lands, a non-probe attempt never reopens a row.
        A missing row is inserted whole, as before. Replay keeps the full
        upsert (``replace_attempt_derived_outcome``): it deletes the rows it
        rebuilds first, and re-closes what was closed outside the ledger.
        Without a concurrent writer it also keeps a closed row closed, which
        changes serving (``ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION``).
        """

        connection.execute(
            """
            INSERT INTO practice_item_state(
              practice_item_id, difficulty, stability, retrievability, due_at,
              active, content_hash, last_attempt_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(practice_item_id) DO UPDATE SET
              difficulty = excluded.difficulty,
              stability = excluded.stability,
              retrievability = excluded.retrievability,
              due_at = excluded.due_at,
              active = MIN(practice_item_state.active, excluded.active),
              last_attempt_at = excluded.last_attempt_at,
              updated_at = excluded.updated_at
            """,
            (
                state.practice_item_id,
                state.difficulty,
                state.stability,
                state.retrievability,
                state.due_at,
                1 if state.active else 0,
                state.content_hash,
                state.last_attempt_at,
                state.updated_at,
            ),
        )

    def _upsert_practice_item_state_record(
        self,
        connection: sqlite3.Connection,
        state: PracticeItemState,
    ) -> None:
        connection.execute(
            """
            INSERT INTO practice_item_state(
              practice_item_id, difficulty, stability, retrievability, due_at,
              active, content_hash, last_attempt_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(practice_item_id) DO UPDATE SET
              difficulty = excluded.difficulty,
              stability = excluded.stability,
              retrievability = excluded.retrievability,
              due_at = excluded.due_at,
              active = excluded.active,
              content_hash = excluded.content_hash,
              last_attempt_at = excluded.last_attempt_at,
              updated_at = excluded.updated_at
            """,
            (
                state.practice_item_id,
                state.difficulty,
                state.stability,
                state.retrievability,
                state.due_at,
                1 if state.active else 0,
                state.content_hash,
                state.last_attempt_at,
                state.updated_at,
            ),
        )

    def _upsert_mastery_state_record(
        self,
        connection: sqlite3.Connection,
        mastery: MasteryState,
    ) -> None:
        connection.execute(
            """
            INSERT INTO learning_object_mastery(
              learning_object_id, logit_mean, logit_variance, evidence_count,
              last_evidence_at, algorithm_version, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(learning_object_id) DO UPDATE SET
              logit_mean = excluded.logit_mean,
              logit_variance = excluded.logit_variance,
              evidence_count = excluded.evidence_count,
              last_evidence_at = excluded.last_evidence_at,
              algorithm_version = excluded.algorithm_version,
              updated_at = excluded.updated_at
            """,
            (
                mastery.learning_object_id,
                mastery.logit_mean,
                mastery.logit_variance,
                mastery.evidence_count,
                mastery.last_evidence_at,
                mastery.algorithm_version,
                mastery.updated_at,
            ),
        )

    def _upsert_facet_uncertainty_state(self, connection: sqlite3.Connection, state: Mapping[str, Any]) -> None:
        marginal = {
            str(label): float(probability)
            for label, probability in dict(state.get("hypothesis_marginal") or {}).items()
        }
        existing = connection.execute(
            """
            SELECT id, created_at, opened_by_attempt_id, opened_reason
            FROM facet_uncertainty
            WHERE learning_object_id = ? AND facet_id = ?
            """,
            (state["learning_object_id"], state["facet_id"]),
        ).fetchone()
        state_id = str(state.get("id") or (existing["id"] if existing is not None else new_ulid()))
        opened_by_attempt_id = str(
            state.get("opened_by_attempt_id")
            or (existing["opened_by_attempt_id"] if existing is not None else "")
        )
        opened_reason = str(
            state.get("opened_reason")
            or (existing["opened_reason"] if existing is not None else "low_facet_outcome")
        )
        if existing is not None:
            connection.execute(
                """
                UPDATE facet_uncertainty
                SET hypothesis_marginal = ?, uncertainty = ?, status = ?,
                    opened_by_attempt_id = ?, opened_reason = ?,
                    last_evidence_at = ?, algorithm_version = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    _json(marginal),
                    state["uncertainty"],
                    state["status"],
                    opened_by_attempt_id,
                    opened_reason,
                    state.get("last_evidence_at"),
                    state["algorithm_version"],
                    state["updated_at"],
                    state_id,
                ),
            )
            return
        connection.execute(
            """
            INSERT INTO facet_uncertainty(
              id, learning_object_id, facet_id, hypothesis_marginal, uncertainty,
              status, opened_by_attempt_id, opened_reason, last_evidence_at,
              algorithm_version, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                state_id,
                state["learning_object_id"],
                state["facet_id"],
                _json(marginal),
                state["uncertainty"],
                state["status"],
                opened_by_attempt_id,
                opened_reason,
                state.get("last_evidence_at"),
                state["algorithm_version"],
                state.get("created_at", state["updated_at"]),
                state["updated_at"],
            ),
        )

    def _upsert_practice_item_quality_state(self, connection: sqlite3.Connection, state: Mapping[str, Any]) -> None:
        connection.execute(
            """
            INSERT INTO practice_item_quality_state(
              practice_item_id, bad_item_suspicion, evidence_count,
              suspicion_reasons_json, last_flagged_at, algorithm_version, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(practice_item_id) DO UPDATE SET
              bad_item_suspicion = excluded.bad_item_suspicion,
              evidence_count = excluded.evidence_count,
              suspicion_reasons_json = excluded.suspicion_reasons_json,
              last_flagged_at = excluded.last_flagged_at,
              algorithm_version = excluded.algorithm_version,
              updated_at = excluded.updated_at
            """,
            (
                state["practice_item_id"],
                state["bad_item_suspicion"],
                state["evidence_count"],
                _json(state.get("suspicion_reasons", [])),
                state.get("last_flagged_at"),
                state["algorithm_version"],
                state["updated_at"],
            ),
        )

    def _upsert_ability_transition_event(self, connection: sqlite3.Connection, event: Mapping[str, Any]) -> None:
        connection.execute(
            """
            INSERT INTO ability_transition_events(
              attempt_id, learning_object_id, practice_item_id, transition_type,
              expected_skill_gain, target_facets_json, reason,
              applied_to_belief_counts, applied_to_mastery, applied_to_facet_recall,
              process_noise, algorithm_version, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(attempt_id) DO UPDATE SET
              learning_object_id = excluded.learning_object_id,
              practice_item_id = excluded.practice_item_id,
              transition_type = excluded.transition_type,
              expected_skill_gain = excluded.expected_skill_gain,
              target_facets_json = excluded.target_facets_json,
              reason = excluded.reason,
              applied_to_belief_counts = excluded.applied_to_belief_counts,
              applied_to_mastery = excluded.applied_to_mastery,
              applied_to_facet_recall = excluded.applied_to_facet_recall,
              process_noise = excluded.process_noise,
              algorithm_version = excluded.algorithm_version,
              created_at = excluded.created_at
            """,
            (
                event["attempt_id"],
                event["learning_object_id"],
                event["practice_item_id"],
                event["transition_type"],
                event["expected_skill_gain"],
                _json(event.get("target_facets", [])),
                event["reason"],
                1 if event.get("applied_to_belief_counts") else 0,
                1 if event.get("applied_to_mastery") else 0,
                1 if event.get("applied_to_facet_recall") else 0,
                event.get("process_noise"),
                event["algorithm_version"],
                event["created_at"],
            ),
        )

    def _link_attempt_to_scheduler_candidate(
        self, connection: sqlite3.Connection, attempt: Mapping[str, Any],
    ) -> None:
        session_id = attempt.get("session_id")
        candidate_id = attempt.get("scheduler_candidate_id")
        if not candidate_id and attempt.get("probe_presentation_id"):
            presentation = connection.execute("SELECT scheduler_candidate_id FROM probe_presentations WHERE id=?", (attempt["probe_presentation_id"],)).fetchone()
            candidate_id = presentation[0] if presentation else None
        if not candidate_id:
            return  # Direct/legacy selection is unavailable, never inferred.
        row = connection.execute(
            """SELECT c.id AS candidate_id, c.slate_id FROM scheduler_slate_candidates c
               JOIN scheduler_slates s ON s.id=c.slate_id
               WHERE c.id=? AND s.session_id=? AND c.practice_item_id=?
                 AND c.was_returned=1 AND s.generated_at<=?
                 AND (c.chosen_attempt_id IS NULL OR c.chosen_attempt_id=?)""",
            (candidate_id, session_id, attempt["practice_item_id"], attempt["created_at"], attempt["id"]),
        ).fetchone()
        if row is None:
            raise ValueError("The scheduler offer does not belong to this item/session or was already consumed.")
        connection.execute(
            """
            UPDATE practice_attempts
            SET scheduler_slate_id = ?, scheduler_candidate_id = ?
            WHERE id = ?
            """,
            (row["slate_id"], row["candidate_id"], attempt["id"]),
        )
        connection.execute(
            """
            UPDATE scheduler_slate_candidates
            SET chosen_attempt_id = COALESCE(chosen_attempt_id, ?),
                chosen_at = COALESCE(chosen_at, ?)
            WHERE id = ?
            """,
            (attempt["id"], attempt["created_at"], row["candidate_id"]),
        )
        connection.execute(
            """
            UPDATE scheduler_slates
            SET chosen_practice_item_id = COALESCE(chosen_practice_item_id, ?),
                chosen_attempt_id = COALESCE(chosen_attempt_id, ?),
                updated_at = ?
            WHERE id = ?
            """,
            (attempt["practice_item_id"], attempt["id"], attempt["created_at"], row["slate_id"]),
        )

    # -- UX Phase 1: a book's automatic-build state (migration 198) ----------

    def source_auto_build_state(self, source_id: str) -> dict[str, Any]:
        """The book's automatic-build generation and pending reading position
        (generation 0 and nothing pending when the book has no row yet)."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_auto_build_state WHERE source_id = ?", (source_id,)
            ).fetchone()
        if row is None:
            return {
                "source_id": source_id, "generation": 0, "undone_at": None,
                "wanted_extraction_id": None, "wanted_section_id": None, "wanted_at": None,
                "wanted_revision": 0, "wanted_attempts": 0, "wanted_retry_at": None,
            }
        return dict(row)

    def advance_source_auto_build_generation(self, source_id: str, *, clock: Clock | None = None) -> int:
        """Undo: start a new generation (older builds never apply) and drop
        any pending reading position. Returns the new generation."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_auto_build_state(source_id, generation, undone_at, updated_at)
                VALUES (?, 1, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                  generation = source_auto_build_state.generation + 1,
                  undone_at = excluded.undone_at,
                  wanted_extraction_id = NULL,
                  wanted_section_id = NULL,
                  wanted_at = NULL,
                  wanted_revision = source_auto_build_state.wanted_revision + 1,
                  wanted_attempts = 0,
                  wanted_retry_at = NULL,
                  updated_at = excluded.updated_at
                """,
                (source_id, now, now),
            )
            row = connection.execute(
                "SELECT generation FROM source_auto_build_state WHERE source_id = ?", (source_id,)
            ).fetchone()
            connection.commit()
        return int(row["generation"])

    def delete_source_artifact(self, source_id: str) -> dict[str, int]:
        """Remove a source artifact and everything derived from it, atomically.

        Three policies, applied per table:

        * DELETE — rows that exist only because this source was imported: the
          Document IR, render views and their crosswalk, unit selections and
          inventories, reader progress/requests/questions, annotations, source
          objects, exposure events, and the provenance links citing it. Children
          go before parents; the source layer uses restrictive foreign keys.
        * DETACH — nullable pointers on records the learner keeps regardless
          (a commitment arc, a notation mapping). Deleting those would destroy
          learner work over a source that merely motivated it.
        * LEAVE — append-only history (``interaction_events``,
          ``synthesis_manifests``, the ingest queue). Those record what happened
          at the time; rewriting them to hide a deleted source would falsify the
          audit trail, and a stale id there is expected.

        Returns per-table row counts. Callers are responsible for the vault-side
        cleanup (collection membership, stored original bytes) — see
        ``learnloop.content.sources.source_deletion``.
        """

        counts: dict[str, int] = {}
        with self.connection() as connection:
            revision_ids = [
                row["id"]
                for row in connection.execute(
                    "SELECT id FROM source_revisions WHERE source_id = ?", (source_id,)
                ).fetchall()
            ]
            extraction_ids: list[str] = []
            if revision_ids:
                revision_marks = ",".join("?" for _ in revision_ids)
                extraction_ids = [
                    row["id"]
                    for row in connection.execute(
                        f"SELECT id FROM source_extraction_runs WHERE revision_id IN ({revision_marks})",
                        revision_ids,
                    ).fetchall()
                ]

            def run(table: str, sql: str, params: Sequence[Any]) -> None:
                cursor = connection.execute(sql, list(params))
                counts[table] = counts.get(table, 0) + cursor.rowcount

            def by_ids(table: str, column: str, ids: Sequence[str]) -> None:
                if not ids:
                    counts.setdefault(table, 0)
                    return
                marks = ",".join("?" for _ in ids)
                run(table, f"DELETE FROM {table} WHERE {column} IN ({marks})", ids)

            # --- rows keyed by extraction -----------------------------------
            for table in (
                "source_document_assets",
                "source_document_blocks",
                "source_document_units",
                "source_block_health",
                "reader_section_progress",
            ):
                by_ids(table, "extraction_id", extraction_ids)
            if extraction_ids:
                marks = ",".join("?" for _ in extraction_ids)
                run(
                    "source_span_reanchors",
                    f"DELETE FROM source_span_reanchors WHERE from_extraction_id IN ({marks}) "
                    f"OR to_extraction_id IN ({marks})",
                    [*extraction_ids, *extraction_ids],
                )
            else:
                counts.setdefault("source_span_reanchors", 0)
            by_ids("source_unit_inventories", "extraction_id", extraction_ids)
            # The held-out signal ledger is keyed by revision (a row whose
            # reading is unknown names none).
            by_ids("source_held_out_signal_marks", "revision_id", revision_ids)

            # --- render views (crosswalk rows hang off the view) ------------
            view_ids = [
                row["id"]
                for row in connection.execute(
                    "SELECT id FROM source_render_views WHERE source_id = ?", (source_id,)
                ).fetchall()
            ]
            by_ids("source_render_block_crosswalk", "render_view_id", view_ids)

            # --- annotations and source objects (versions before parents) ---
            annotation_ids = [
                row["id"]
                for row in connection.execute(
                    "SELECT id FROM source_annotations WHERE source_id = ?", (source_id,)
                ).fetchall()
            ]
            by_ids("source_annotation_versions", "annotation_id", annotation_ids)
            by_ids("source_annotation_anchor_versions", "annotation_id", annotation_ids)

            object_ids = [
                row["id"]
                for row in connection.execute(
                    "SELECT id FROM source_objects WHERE source_id = ?", (source_id,)
                ).fetchall()
            ]
            version_ids: list[str] = []
            if object_ids:
                object_marks = ",".join("?" for _ in object_ids)
                version_ids = [
                    row["id"]
                    for row in connection.execute(
                        f"SELECT id FROM source_object_versions WHERE source_object_id IN ({object_marks})",
                        object_ids,
                    ).fetchall()
                ]
            by_ids("source_object_citations", "source_object_version_id", version_ids)
            by_ids("source_object_relations", "source_object_id", object_ids)
            by_ids("source_object_versions", "source_object_id", object_ids)

            # --- rows keyed directly by the source --------------------------
            for table in (
                "source_objects",
                "source_annotations",
                "source_render_views",
                "source_exposure_events",
                "source_unit_selections",
                "reader_authored_questions",
                "reader_background_requests",
                "reader_capture_outbox",
                "entity_source_links",
                "source_auto_build_state",
            ):
                run(table, f"DELETE FROM {table} WHERE source_id = ?", (source_id,))

            # --- detach learner-owned records that outlive the source -------
            run(
                "commitment_arcs",
                "UPDATE commitment_arcs SET source_id = NULL WHERE source_id = ?",
                (source_id,),
            )
            run(
                "notation_mappings",
                "UPDATE notation_mappings SET source_id = NULL, revision_id = NULL "
                "WHERE source_id = ?",
                (source_id,),
            )

            # --- identity chain, children first -----------------------------
            by_ids("source_extraction_runs", "id", extraction_ids)
            by_ids("source_revisions", "id", revision_ids)
            run("source_artifacts", "DELETE FROM source_artifacts WHERE id = ?", (source_id,))
            connection.commit()
        return counts

    # --- maintenance feed (§11) --------------------------------------------

    def upsert_maintenance_notice(
        self,
        *,
        notice_type: str,
        dedup_key: str,
        title: str,
        action: Mapping[str, Any],
        aging_policy: str,
        severity: str = "info",
        subject_id: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        detail: Any = None,
        clock: Clock | None = None,
    ) -> str:
        """Insert or refresh a notice (idempotent on ``(notice_type, dedup_key)``).

        A live notice keeps its id, snooze_count, and snoozed_until across
        regeneration; only ``last_seen_at`` (and severity/detail) refresh, so
        deterministic re-generation never duplicates or resets a notice."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT * FROM maintenance_notices WHERE notice_type = ? AND dedup_key = ?",
                (notice_type, dedup_key),
            ).fetchone()
            if existing is not None:
                connection.execute(
                    """
                    UPDATE maintenance_notices
                       SET title = ?, action_json = ?, severity = ?, detail_json = ?,
                           last_seen_at = ?,
                           status = CASE WHEN status IN ('dismissed','resolved','expired','snoozed')
                                         THEN status ELSE 'active' END
                     WHERE id = ?
                    """,
                    (title, _json(action), severity, _json(detail), now, existing["id"]),
                )
                connection.commit()
                return existing["id"]
            row_id = new_ulid()
            connection.execute(
                """
                INSERT INTO maintenance_notices(
                  id, subject_id, notice_type, dedup_key, severity, aging_policy,
                  entity_type, entity_id, title, detail_json, action_json, status,
                  snooze_count, snoozed_until, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', 0, NULL, ?, ?)
                """,
                (
                    row_id, subject_id, notice_type, dedup_key, severity, aging_policy,
                    entity_type, entity_id, title, _json(detail), _json(action), now, now,
                ),
            )
            connection.commit()
            return row_id

    def maintenance_notices(
        self, *, subject_id: str | None = None, include_hidden: bool = False
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM maintenance_notices"
        clauses: list[str] = []
        params: list[Any] = []
        if not include_hidden:
            clauses.append("status IN ('active', 'snoozed')")
        if subject_id is not None:
            clauses.append("(subject_id = ? OR subject_id IS NULL)")
            params.append(subject_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY severity DESC, first_seen_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [_decode_maintenance_notice(row) for row in rows]

    def maintenance_notice(self, notice_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM maintenance_notices WHERE id = ?", (notice_id,)
            ).fetchone()
        return _decode_maintenance_notice(row) if row else None

    def set_maintenance_notice_status(
        self,
        notice_id: str,
        *,
        status: str,
        snoozed_until: str | None = None,
        bump_snooze: bool = False,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                f"""
                UPDATE maintenance_notices
                   SET status = ?, snoozed_until = ?,
                       snooze_count = snooze_count + {1 if bump_snooze else 0},
                       resolved_at = CASE WHEN ? IN ('resolved','expired','dismissed') THEN ? ELSE resolved_at END
                 WHERE id = ?
                """,
                (status, snoozed_until, status, now, notice_id),
            )
            connection.commit()

    def resolve_maintenance_notice_if_detail(
        self, notice_id: str, *, detail_key: str, expected: Any, clock: Clock | None = None
    ) -> bool:
        """Resolve a live notice only while its stored ``detail[detail_key]``
        is still ``expected`` (one guarded statement: a write that changed the
        detail since the caller read it keeps the notice). Reader CA1's
        transcription reports resolve this way (Codex review F8). Returns
        whether it was resolved."""

        if not detail_key.isidentifier():
            raise ValueError(f"not a detail key: {detail_key!r}")
        now = utc_now_iso(clock)
        with self.connection() as connection:
            changed = connection.execute(
                f"""
                UPDATE maintenance_notices
                   SET status = 'resolved', resolved_at = ?
                 WHERE id = ? AND status IN ('active', 'snoozed')
                   AND json_extract(detail_json, '$.{detail_key}') IS ?
                """,
                (now, notice_id, expected),
            ).rowcount
            connection.commit()
        return bool(changed)

    def insert_synthesis_manifest(self, manifest: Mapping[str, Any]) -> str:
        """Persist an immutable synthesis manifest (§8.4). Idempotent on
        ``manifest_hash`` — an identical manifest returns the existing id and is
        never re-inserted."""

        manifest_hash = str(manifest["manifest_hash"])
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM synthesis_manifests WHERE manifest_hash = ?",
                (manifest_hash,),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            row_id = str(manifest.get("id") or new_ulid())
            connection.execute(
                """
                INSERT INTO synthesis_manifests(
                  id, manifest_hash, source_set_id, membership_json,
                  revision_ids_json, asset_hashes_json, extraction_ids_json,
                  unit_inventory_versions_json, scope_json, brief_json,
                  prompt_version, schema_version, provider, model,
                  extractor_versions_json, curriculum_snapshot_hash,
                  facet_registry_hash, task_graph_hash, assessment_schema_version,
                  learner_model_contract_version, lock_fingerprint,
                  token_budget_json, estimated_usage_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    manifest_hash,
                    manifest.get("source_set_id"),
                    _json(manifest.get("membership")),
                    _json(manifest.get("revision_ids")),
                    _json(manifest.get("asset_hashes")),
                    _json(manifest.get("extraction_ids")),
                    _json(manifest.get("unit_inventory_versions")),
                    _json(manifest.get("scope")),
                    _json(manifest.get("brief")),
                    manifest.get("prompt_version"),
                    manifest.get("schema_version"),
                    manifest.get("provider"),
                    manifest.get("model"),
                    _json(manifest.get("extractor_versions")),
                    manifest.get("curriculum_snapshot_hash"),
                    manifest.get("facet_registry_hash"),
                    manifest.get("task_graph_hash"),
                    manifest.get("assessment_schema_version"),
                    manifest.get("learner_model_contract_version"),
                    manifest.get("lock_fingerprint"),
                    _json(manifest.get("token_budget")),
                    _json(manifest.get("estimated_usage")),
                    manifest.get("created_at") or utc_now_iso(),
                ),
            )
            connection.commit()
        return row_id

    def synthesis_manifest(self, manifest_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM synthesis_manifests WHERE id = ?",
                (manifest_id,),
            ).fetchone()
        return _decode_synthesis_manifest(row) if row is not None else None

    def synthesis_manifest_by_hash(self, manifest_hash: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM synthesis_manifests WHERE manifest_hash = ?",
                (manifest_hash,),
            ).fetchone()
        return _decode_synthesis_manifest(row) if row is not None else None

    def completed_synthesis_manifests(self, source_set_id: str) -> list[dict[str, Any]]:
        """The manifest of each completed synthesis run of a source set, oldest
        first, with the run's ``proposal_id`` beside it."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT m.*, r.proposal_id AS proposal_id
                FROM synthesis_runs r JOIN synthesis_manifests m ON m.id = r.manifest_id
                WHERE m.source_set_id = ? AND r.status = 'completed'
                ORDER BY r.created_at, r.id
                """,
                (source_set_id,),
            ).fetchall()
        return [_decode_synthesis_manifest(row) for row in rows]

    def insert_synthesis_run(
        self,
        *,
        manifest_id: str,
        mode: str,
        agent_run_id: str | None = None,
        proposal_id: str | None = None,
        span_request: Any = None,
        status: str = "created",
        run_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        row_id = run_id or new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO synthesis_runs(
                  id, manifest_id, mode, agent_run_id, proposal_id,
                  span_request_json, resolved_span_hashes_json,
                  coverage_decisions_json, actual_usage_json, status,
                  created_at, completed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    manifest_id,
                    mode,
                    agent_run_id,
                    proposal_id,
                    _json(span_request) if span_request is not None else None,
                    None,
                    None,
                    None,
                    status,
                    utc_now_iso(clock),
                    None,
                ),
            )
            connection.commit()
        return row_id

    def complete_synthesis_run(
        self,
        run_id: str,
        *,
        status: str,
        proposal_id: str | None = None,
        resolved_span_hashes: Any = None,
        coverage_decisions: Any = None,
        actual_usage: Any = None,
        clock: Clock | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE synthesis_runs
                   SET status = ?,
                       proposal_id = COALESCE(?, proposal_id),
                       resolved_span_hashes_json = COALESCE(?, resolved_span_hashes_json),
                       coverage_decisions_json = COALESCE(?, coverage_decisions_json),
                       actual_usage_json = COALESCE(?, actual_usage_json),
                       completed_at = ?
                 WHERE id = ?
                """,
                (
                    status,
                    proposal_id,
                    _json(resolved_span_hashes) if resolved_span_hashes is not None else None,
                    _json(coverage_decisions) if coverage_decisions is not None else None,
                    _json(actual_usage) if actual_usage is not None else None,
                    utc_now_iso(clock),
                    run_id,
                ),
            )
            connection.commit()

    def synthesis_run(self, run_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM synthesis_runs WHERE id = ?", (run_id,)
            ).fetchone()
        return _decode_synthesis_run(row) if row is not None else None

    def synthesis_run_for_agent_run(self, agent_run_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM synthesis_runs WHERE agent_run_id = ? ORDER BY created_at DESC, id DESC LIMIT 1",
                (agent_run_id,),
            ).fetchone()
        return _decode_synthesis_run(row) if row is not None else None

    def save_synthesis_candidate(self, run_id: str, candidate: Mapping[str, Any]) -> None:
        """Stage model output before gates and proposal persistence."""

        with self.connection() as connection:
            connection.execute(
                "UPDATE synthesis_runs SET candidate_output_json = ? WHERE id = ?",
                (_json(dict(candidate)), run_id),
            )
            connection.commit()

    def save_synthesis_shard_result(
        self,
        *,
        shard_key: str,
        shard_ordinal: int,
        shard_count: int,
        result: Mapping[str, Any],
        manifest_hash: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        """Persist one completed synthesis shard's model output (durable checkpoint).

        Keyed by the request key of the shard's first pass (what it sends), so a
        retried synthesis reuses finished shards at zero model cost, including
        retries whose revised token ceilings mint a different manifest."""

        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO synthesis_shard_results(
                  shard_key, manifest_hash, shard_ordinal, shard_count, output_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(shard_key) DO UPDATE SET
                  manifest_hash = excluded.manifest_hash,
                  shard_ordinal = excluded.shard_ordinal,
                  shard_count = excluded.shard_count,
                  output_json = excluded.output_json
                """,
                (
                    shard_key,
                    manifest_hash,
                    shard_ordinal,
                    shard_count,
                    _json(dict(result)),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()

    def synthesis_shard_result(self, shard_key: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM synthesis_shard_results WHERE shard_key = ?", (shard_key,)
            ).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["output"] = _loads(data.pop("output_json", None), None)
        return data

    def discard_synthesis_shard_result(self, shard_key: str, *, output: Mapping[str, Any] | None = None) -> None:
        """Delete one shard's saved output, so the next synthesis pays for a
        fresh answer instead of replaying one the quality gates rejected.

        With ``output`` (the output that was judged), only while the row still
        holds it: another run may have saved a fresh one under the key since.
        Compared on the stored text, which :meth:`save_synthesis_shard_result`
        writes with the same serialization."""

        with self.connection() as connection:
            if output is None:
                connection.execute("DELETE FROM synthesis_shard_results WHERE shard_key = ?", (shard_key,))
            else:
                connection.execute(
                    "DELETE FROM synthesis_shard_results WHERE shard_key = ? AND output_json = ?",
                    (shard_key, _json(dict(output))),
                )
            connection.commit()

    def finalize_stale_synthesis_runs(
        self, *, before_iso: str, clock: Clock | None = None
    ) -> list[str]:
        """Mark abandoned non-terminal synthesis runs failed (startup hygiene).

        Historical error paths did not always finalize the run row, leaving
        'created'/'running' rows behind forever. Only rows created before
        ``before_iso`` are touched, so a currently-executing synthesis (whose
        worker holds a live job lease) is never finalized under it. Preserved
        candidates stay in place — only the status/completed_at are stamped."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT id FROM synthesis_runs
                 WHERE status IN ('created', 'running') AND created_at < ?
                 ORDER BY created_at, id
                """,
                (before_iso,),
            ).fetchall()
            run_ids = [row["id"] for row in rows]
            if run_ids:
                now = utc_now_iso(clock)
                connection.executemany(
                    "UPDATE synthesis_runs SET status = 'failed', completed_at = ? WHERE id = ?",
                    [(now, run_id) for run_id in run_ids],
                )
            connection.commit()
        return run_ids

    def synthesis_run_introducing_entity(
        self, entity_type: str, entity_id: str
    ) -> dict[str, Any] | None:
        """The synthesis run whose proposal introduced an entity (patch -> run ->
        manifest lineage, §9.2). Resolved via the entity's applied content event's
        change batch -> proposal item -> proposed_patch -> synthesis_runs.proposal_id.
        """

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT synthesis_runs.*
                  FROM content_events
                  JOIN change_batches
                    ON change_batches.id = content_events.change_batch_id
                  JOIN proposed_patch_items
                    ON proposed_patch_items.id = change_batches.proposed_patch_item_id
                  JOIN synthesis_runs
                    ON synthesis_runs.proposal_id = proposed_patch_items.proposed_patch_id
                 WHERE content_events.entity_type = ?
                   AND content_events.entity_id = ?
                   AND content_events.event_type = 'created'
                 ORDER BY content_events.created_at
                 LIMIT 1
                """,
                (entity_type, entity_id),
            ).fetchone()
        return _decode_synthesis_run(row) if row is not None else None

    def insert_apply_intent(
        self,
        *,
        proposed_patch_id: str,
        item_ids: list[str],
        targets: list[Mapping[str, Any]],
        db_plan: list[Mapping[str, Any]],
        intent_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Durably commit the write-ahead apply intent BEFORE any YAML is staged
        (§10.2). Returns the intent id."""

        row_id = intent_id or new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO apply_intents(
                  id, proposed_patch_id, item_ids_json, targets_json,
                  db_plan_json, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, 'pending', ?)
                """,
                (
                    row_id,
                    proposed_patch_id,
                    _json(list(item_ids)),
                    _json([dict(t) for t in targets]),
                    _json([dict(p) for p in db_plan]),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return row_id

    def mark_apply_intent_applied(self, intent_id: str, *, clock: Clock | None = None) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE apply_intents SET status = 'applied', applied_at = ? WHERE id = ?",
                (utc_now_iso(clock), intent_id),
            )
            connection.commit()

    def pending_apply_intents(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM apply_intents WHERE status = 'pending' ORDER BY created_at, id"
            ).fetchall()
        return [_decode_apply_intent(row) for row in rows]

    def outstanding_apply_intents(self) -> list[dict[str, Any]]:
        """Intents that refuse the next accept: ``pending`` (mid-flight) and ``conflicted`` (K3.5).

        Below migration 255 the table has no ``conflicted`` rows, so this is the pending list there.
        """

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM apply_intents WHERE status IN ('pending', 'conflicted') ORDER BY created_at, id"
            ).fetchall()
        return [_decode_apply_intent(row) for row in rows]

    def apply_intent(self, intent_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM apply_intents WHERE id = ?", (intent_id,)).fetchone()
        return _decode_apply_intent(row) if row is not None else None

    def mark_apply_intent_conflicted(
        self, intent_id: str, conflicts: list[Mapping[str, Any]], *, clock: Clock | None = None
    ) -> None:
        """Recovery found target files changed since the intent (K3.5): nothing was written."""

        with self.connection() as connection:
            connection.execute(
                "UPDATE apply_intents SET status = 'conflicted', conflict_json = ?, conflicted_at = ? "
                "WHERE id = ? AND status IN ('pending', 'conflicted')",
                (_json([dict(c) for c in conflicts]), utc_now_iso(clock), intent_id),
            )
            connection.commit()

    def mark_apply_intent_rolled_back(self, intent_id: str, *, clock: Clock | None = None) -> None:
        """The accept stopped before writing any file (K3.5: a target changed under it)."""

        with self.connection() as connection:
            connection.execute(
                "UPDATE apply_intents SET status = 'rolled_back', rolled_back_at = ? WHERE id = ? AND status = 'pending'",
                (utc_now_iso(clock), intent_id),
            )
            connection.commit()

    def mark_apply_intent_set_aside(self, intent_id: str, *, clock: Clock | None = None) -> bool:
        """The owner kept the files as they are (K3.5); True when a conflicted intent was settled."""

        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE apply_intents SET status = 'set_aside', set_aside_at = ? WHERE id = ? AND status = 'conflicted'",
                (utc_now_iso(clock), intent_id),
            )
            connection.commit()
        return cursor.rowcount == 1

    def derived_state_rebuild_version_changes(self) -> list[dict[str, Any]]:
        """Recalibration boundaries: each derived-state rebuild whose
        ``algorithm_version`` OR ``canonical_projection_version`` differs from
        the immediately preceding rebuild. Collapses consecutive same-version
        rebuilds so a version bump surfaces as exactly one entry, regardless of
        how many learning objects/facets it recomputed. Ordered oldest-first.

        The projection version is a second, finer boundary: a canonical
        projection semantics change (P2 §4.4 — probe/primed attempts become
        assisted) retro-changes derived facet state without touching the vault
        algorithm version, and must still surface as one honest "estimates
        recomputed, your evidence unchanged" entry rather than silently.

        THE FIRST ROW IS NOT ALWAYS HOUSEKEEPING.  Skipping it unconditionally
        (there is no predecessor to differ from) is right for a fresh vault, but
        wrong for the case that actually matters: a vault whose learner has been
        practising for months and whose ``derived_state_rebuilds`` table is
        empty, because rebuilds only started being recorded later.  Its first
        rebuild recomputes estimates the learner has already SEEN, under a
        projection version that was never in force when they saw them — and
        under the old rule it emitted nothing at all.  A silent state change is
        the failure mode `spec_diagnostic_augmentation_v1.md` A6 exists to
        prevent: the system must be able to say it was wrong.

        So the first row emits a boundary exactly when it recomputed prior
        learner evidence (``replayed_attempts > 0``) under a recorded projection
        version.  A first rebuild on a vault with nothing to replay narrates
        housekeeping the learner never saw, and stays silent. The dedicated
        startup projection scope stays silent on later zero-replay baselines as
        well, while still advancing the version used for future comparisons.
        ``previous_*`` is ``None`` on that entry, which is the truthful statement
        that no earlier version was on record.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, scope, algorithm_version, canonical_projection_version,
                       coverage_denominator_version, replayed_attempts, created_at
                FROM derived_state_rebuilds
                ORDER BY created_at, id
                """
            ).fetchall()
        changes: list[dict[str, Any]] = []
        previous_version: str | None = None
        previous_projection: str | None = None
        previous_coverage: str | None = None
        first = True
        for row in rows:
            version = str(row["algorithm_version"])
            raw_projection = row["canonical_projection_version"]
            projection = (
                str(raw_projection)
                if raw_projection is not None
                else previous_projection
            )
            # Measurement §5.2 (migration 138): a third, independent boundary.
            # The contract-frontier denominator moves DISPLAYED mastery with no
            # change to the evidence or the projection, so it needs its own
            # version — attributing the entry to either existing one would name a
            # cause that was not the cause.
            #
            # A NULL projection or coverage value means "this writer did not
            # report that dimension", not "the version was rolled back to
            # nothing". Historical rows predate the columns, and narrow rebuild
            # writers need not stamp either. Comparing NULL as a real value
            # would mint a phantom boundary on the next stamped rebuild and then
            # another on the one after — narrating recalibrations that never
            # happened. Unreported versions therefore carry forward and can
            # never themselves be a boundary.
            raw_coverage = row["coverage_denominator_version"]
            coverage = (
                str(raw_coverage) if raw_coverage is not None else previous_coverage
            )
            first_recalibrates_seen_evidence = (
                first
                and (projection is not None or coverage is not None)
                and int(row["replayed_attempts"] or 0) > 0
            )
            # Startup also stamps the current projection on an empty fresh
            # vault.  That is a baseline for future comparisons, not a change
            # to anything the learner demonstrated, so even a later software
            # upgrade while the vault is still empty remains silent.  The row
            # still advances ``previous_projection`` below, preventing a false
            # cutover after the learner's first attempt.
            silent_empty_projection_baseline = (
                str(row["scope"]) == "canonical_projection_startup"
                and int(row["replayed_attempts"] or 0) == 0
            )
            if not silent_empty_projection_baseline and (
                first_recalibrates_seen_evidence
                or (
                    not first
                    and (
                        version != previous_version
                        or projection != previous_projection
                        or coverage != previous_coverage
                    )
                )
            ):
                changes.append(
                    {
                        "id": str(row["id"]),
                        "algorithm_version": version,
                        "previous_algorithm_version": previous_version,
                        "canonical_projection_version": projection,
                        "previous_canonical_projection_version": (
                            previous_projection
                        ),
                        "coverage_denominator_version": coverage,
                        "previous_coverage_denominator_version": previous_coverage,
                        "at": str(row["created_at"]),
                    }
                )
            first = False
            previous_version = version
            previous_projection = projection
            previous_coverage = coverage
        return changes

    def record_depth_transition_atomic(
        self,
        *,
        commitment_id: str,
        milestone_slug: str,
        milestone_detail_json: str | None,
        transition_detail_json: str | None,
        receipt_key: str,
        fork_spec: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """B4: append the step-7 ``depth_milestone_reached`` + ``depth_transition_committed``
        events AND (when supplied) the step-6 fork lineage/edge/state in ONE transaction.

        Idempotent on ``receipt_key`` (the decision/evidence receipt id): a retry that
        replays the same decision finds the prior ``depth_transition_committed`` event
        and returns it WITHOUT appending a second milestone/transition or a second fork
        (no double-commit). Returns a dict with the event ids, any forked lineage/state
        ids, and ``already`` (True on the idempotent short-circuit)."""

        now = utc_now_iso(clock)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("BEGIN IMMEDIATE")
            prior = connection.execute(
                """
                SELECT id, detail_json FROM commitment_events
                 WHERE commitment_id = ? AND kind = 'depth_transition_committed'
                   AND json_extract(detail_json, '$.receipt_key') = ?
                 ORDER BY created_at, id LIMIT 1
                """,
                (commitment_id, receipt_key),
            ).fetchone()
            if prior is not None:
                connection.execute("ROLLBACK")
                detail = json.loads(prior["detail_json"] or "{}")
                return {
                    "already": True,
                    "transition_event_id": prior["id"],
                    "forked_lineage_id": detail.get("forked_lineage_id"),
                    "forked_state_id": detail.get("forked_state_id"),
                }

            forked_lineage_id: str | None = None
            forked_state_id: str | None = None
            if fork_spec is not None:
                forked_lineage_id = fork_spec.get("lineage_id") or new_ulid()
                connection.execute(
                    "INSERT INTO card_lineages(id, family_id, card_id, created_at) VALUES (?, ?, ?, ?)",
                    (forked_lineage_id, fork_spec.get("family_id"), fork_spec.get("card_id"), now),
                )
                connection.execute(
                    """
                    INSERT INTO card_lineage_edges(
                      id, lineage_id, from_card_version_id, to_card_version_id,
                      edge_kind, classifier_version, rationale_json, created_at
                    )
                    VALUES (?, ?, ?, ?, 'semantic_fork', ?, ?, ?)
                    """,
                    (
                        new_ulid(), forked_lineage_id,
                        fork_spec.get("predecessor_card_version_id"),
                        fork_spec["forked_card_version_id"],
                        fork_spec["classifier_version"],
                        json.dumps(dict(fork_spec.get("rationale") or {"reason": "semantic_fork"}),
                                   sort_keys=True),
                        now,
                    ),
                )
                forked_state_id = fork_spec.get("state_id") or new_ulid()
                projection_head = {
                    "reviews": [],
                    "forked_from_version": fork_spec.get("predecessor_card_version_id"),
                }
                connection.execute(
                    """
                    INSERT INTO activity_card_state(
                      id, learner_id, card_lineage_id, scheduler_algorithm_version,
                      model_label, difficulty, stability, retrievability, due_at,
                      last_eligible_review_at, lapse_episode_id, active,
                      projection_head_json, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, 1, ?, ?)
                    """,
                    (
                        forked_state_id, fork_spec.get("learner_id", "local"),
                        forked_lineage_id, fork_spec["scheduler_algorithm_version"],
                        fork_spec.get("model_label", "fsrs"),
                        fork_spec.get("informed_difficulty_prior"),
                        json.dumps(projection_head, sort_keys=True), now,
                    ),
                )

            milestone_event_id = new_ulid()
            connection.execute(
                """
                INSERT INTO commitment_events(
                  id, commitment_id, commitment_version_id, kind, detail_json, created_at
                )
                VALUES (?, ?, NULL, 'depth_milestone_reached', ?, ?)
                """,
                (milestone_event_id, commitment_id, milestone_detail_json, now),
            )
            transition_event_id = new_ulid()
            connection.execute(
                """
                INSERT INTO commitment_events(
                  id, commitment_id, commitment_version_id, kind, detail_json, created_at
                )
                VALUES (?, ?, NULL, 'depth_transition_committed', ?, ?)
                """,
                (transition_event_id, commitment_id, transition_detail_json, now),
            )
            connection.execute("COMMIT")
            return {
                "already": False,
                "milestone_event_id": milestone_event_id,
                "transition_event_id": transition_event_id,
                "forked_lineage_id": forked_lineage_id,
                "forked_state_id": forked_state_id,
            }
        except Exception:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise
        finally:
            connection.close()

    # ------------------------------------------------------------------
    # P2 golden path -- atomic confirmation + run events (spec_p2 §3.1, §4, 082)
    # ------------------------------------------------------------------

    def confirm_golden_path_atomic(
        self,
        *,
        receipt_key: str,
        blueprint_version_id: str,
        goal_id: str,
        goal_contract: Mapping[str, Any],
        commitment: Mapping[str, Any],
        run: Mapping[str, Any],
        reservation: Mapping[str, Any] | None = None,
        fault_hook: Any = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """The ONE atomic confirmation (spec_p2 §3.1). In a single transaction:
        activate the reviewed blueprint, append goal-contract v1 + head, insert the
        commitment (+v1 version/targets/created event), reserve the fresh assessment
        surface, and mint the run + ``run_started`` event. If ANY part fails the whole
        transaction rolls back and nothing becomes active.

        Idempotent on ``golden_path_runs.receipt_key`` -- a byte-identical re-confirm
        returns the existing run with ``already_exists=True``.

        ``fault_hook`` is a test-only seam: a callable invoked with a stage label
        after each internal write. Raising inside it proves the whole boundary rolls
        back (the §12.6 fault-injection acceptance) -- no partial confirmation.
        """

        def _fault(label: str) -> None:
            if fault_hook is not None:
                fault_hook(label)

        now = utc_now_iso(clock)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("BEGIN IMMEDIATE")

            existing_run = connection.execute(
                "SELECT * FROM golden_path_runs WHERE receipt_key = ?", (receipt_key,)
            ).fetchone()
            if existing_run is not None:
                connection.execute("ROLLBACK")
                return {"run": dict(existing_run), "already_exists": True}

            # Step 1: activate the reviewed blueprint (assert reviewed/active).
            bp = connection.execute(
                "SELECT status FROM task_blueprint_versions WHERE id = ?",
                (blueprint_version_id,),
            ).fetchone()
            if bp is None or bp["status"] not in ("reviewed", "active"):
                connection.execute("ROLLBACK")
                raise BlueprintNotReviewed(
                    blueprint_version_id, status=bp["status"] if bp else None
                )
            if bp["status"] == "reviewed":
                connection.execute(
                    "UPDATE task_blueprint_versions SET status = 'active', activated_at = ? WHERE id = ?",
                    (now, blueprint_version_id),
                )
                connection.execute(
                    """
                    INSERT INTO task_blueprint_review_events(
                      id, blueprint_version_id, kind, detail_json, author, created_at
                    )
                    VALUES (?, ?, 'activated', ?, 'owner', ?)
                    """,
                    (new_ulid(), blueprint_version_id, _json({"receipt_key": receipt_key}), now),
                )
            _fault("blueprint_activated")

            # Step 2: goal-contract v1 (idempotent on content_hash; fresh head only).
            head_row = connection.execute(
                "SELECT head_version_id FROM goal_contract_heads WHERE goal_id = ?",
                (goal_id,),
            ).fetchone()
            existing_gcv = connection.execute(
                "SELECT id FROM goal_contract_versions WHERE goal_id = ? AND content_hash = ?",
                (goal_id, goal_contract["content_hash"]),
            ).fetchone()
            if existing_gcv is not None:
                goal_contract_version_id = existing_gcv["id"]
            else:
                if head_row is not None:
                    connection.execute("ROLLBACK")
                    raise GoalAlreadyConfirmed(
                        goal_id, head_version_id=head_row["head_version_id"]
                    )
                goal_contract_version_id = new_ulid()
                connection.execute(
                    """
                    INSERT INTO goal_contract_versions(
                      id, goal_id, version, predecessor_version_id, contract_json,
                      content_hash, support_hash, contract_schema_version, change_class,
                      envelope_version, predecessor_milestone, activated_edge_id,
                      evidence_receipt_json, burden_delta_json, author, reason, created_at
                    )
                    VALUES (?, ?, 1, NULL, ?, ?, ?, ?, 'confirm', ?, NULL, NULL, NULL, NULL, ?, NULL, ?)
                    """,
                    (
                        goal_contract_version_id, goal_id, goal_contract["contract_json"],
                        goal_contract["content_hash"], goal_contract["support_hash"],
                        int(goal_contract["contract_schema_version"]),
                        goal_contract.get("head_envelope_version"),
                        goal_contract.get("author", "learner"), now,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO goal_contract_heads(
                      goal_id, head_version_id, head_version, head_content_hash,
                      head_support_hash, head_envelope_version, updated_at
                    )
                    VALUES (?, ?, 1, ?, ?, ?, ?)
                    """,
                    (
                        goal_id, goal_contract_version_id, goal_contract["content_hash"],
                        goal_contract["support_hash"], goal_contract.get("head_envelope_version"), now,
                    ),
                )
            _fault("goal_contract_appended")

            # Step 3: commitment + v1 version/targets/created event (reuses the shared
            # row-builder so the commitment shape stays identical to create_commitment).
            commitment_id = new_ulid()
            connection.execute(
                """
                INSERT INTO commitments(
                  id, learner_id, created_action, idempotency_key, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    commitment_id, commitment.get("learner_id", "local"),
                    commitment["created_action"], commitment.get("idempotency_key"), now,
                ),
            )
            commitment_version_id = self._insert_commitment_version_rows(
                connection,
                commitment_id=commitment_id,
                predecessor_version_id=None,
                version=1,
                version_fields=commitment["version_fields"],
                targets=commitment["targets"],
                author=commitment.get("author", "learner"),
                change_reason=None,
                events=[{"kind": "created", "detail": {"action": commitment["created_action"]}}],
                now=now,
            )
            _fault("commitment_created")

            # Step 4: reserve the fresh held-out assessment surface (§8.1).
            reservation_id: str | None = None
            if reservation is not None:
                reservation_id = new_ulid()
                connection.execute(
                    """
                    INSERT INTO activity_surface_reservations(
                      id, surface_id, goal_id, target_contract_version_id,
                      target_support_hash, purpose, status, eligibility_json,
                      administration_id, reserved_at, closed_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'reserved', ?, NULL, ?, NULL)
                    """,
                    (
                        reservation_id, reservation["surface_id"], goal_id,
                        goal_contract_version_id, reservation.get("target_support_hash"),
                        reservation.get("purpose", "assessment"),
                        reservation.get("eligibility_json", "{}"), now,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO activity_surface_lifecycle_events(
                      id, surface_id, reservation_id, administration_id, kind,
                      reason, detail_json, created_at
                    )
                    VALUES (?, ?, ?, NULL, 'reserve', ?, NULL, ?)
                    """,
                    (
                        new_ulid(), reservation["surface_id"], reservation_id,
                        "golden_path_confirm", now,
                    ),
                )
            _fault("reserve_created")

            # Step 5: mint the run + run_started event (written LAST -- the run row is
            # what makes the confirmation "active"; a partial failure never reaches it).
            run_id = new_ulid()
            mode = run.get("mode", "certifying")
            connection.execute(
                """
                INSERT INTO golden_path_runs(
                  id, receipt_key, learner_id, goal_id, commitment_id,
                  commitment_version_id, source_rev, unit_id, blueprint_version_id,
                  goal_contract_version_id, depth_policy_version_id,
                  depth_envelope_version_id, initial_milestone, reserved_reservation_id,
                  reserved_surface_id, reserved_support_hash, mode,
                  orchestration_policy_json, decision_param_manifest_json,
                  visible_caps_json, current_state, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ready', ?, ?)
                """,
                (
                    run_id, receipt_key, run.get("learner_id", "local"), goal_id,
                    commitment_id, commitment_version_id, run["source_rev"], run["unit_id"],
                    blueprint_version_id, goal_contract_version_id,
                    commitment["version_fields"].get("depth_policy_version_id"),
                    commitment["version_fields"].get("depth_envelope_version_id"),
                    run["initial_milestone"], reservation_id,
                    reservation["surface_id"] if reservation is not None else None,
                    reservation.get("target_support_hash") if reservation is not None else None,
                    mode, run.get("orchestration_policy_json"),
                    run.get("decision_param_manifest_json"), run.get("visible_caps_json"),
                    now, now,
                ),
            )
            connection.execute(
                """
                INSERT INTO golden_path_run_events(
                  id, run_id, seq, from_state, to_state, reason,
                  feasible_alternatives_json, evidence_ids_json,
                  goal_contract_head_version_id, depth_policy_version_id,
                  depth_envelope_version_id, predecessor_milestone, successor_milestone,
                  selected_activity_json, policy_calibration_json, burden_json,
                  expected_head_event_id, idempotency_key, created_at
                )
                VALUES (?, ?, 1, 'draft', 'ready', 'run_started', NULL, NULL, ?, ?, ?, NULL, ?, NULL, NULL, NULL, NULL, ?, ?)
                """,
                (
                    new_ulid(), run_id, goal_contract_version_id,
                    commitment["version_fields"].get("depth_policy_version_id"),
                    commitment["version_fields"].get("depth_envelope_version_id"),
                    run["initial_milestone"], receipt_key + ":start", now,
                ),
            )
            _fault("run_started")

            connection.execute("COMMIT")
            run_row = self.golden_path_run(run_id)
            return {
                "run": run_row,
                "already_exists": False,
                "goal_contract_version_id": goal_contract_version_id,
                "commitment_id": commitment_id,
                "commitment_version_id": commitment_version_id,
                "reservation_id": reservation_id,
            }
        except Exception:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise
        finally:
            connection.close()

    # --- failure triage -------------------------------------------------

    def failure_triage_routes(self, *, active_only: bool = True) -> list[dict[str, Any]]:
        with self.connection() as connection:
            if active_only:
                rows = connection.execute(
                    "SELECT * FROM failure_triage_routes WHERE active = 1 ORDER BY reason, route_version"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM failure_triage_routes ORDER BY reason, route_version"
                ).fetchall()
        return [dict(row) for row in rows]

    def failure_triage_route_for_reason(self, reason: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM failure_triage_routes WHERE reason = ? AND active = 1 "
                "ORDER BY route_version DESC LIMIT 1",
                (reason,),
            ).fetchone()
        return dict(row) if row is not None else None

    def failure_triage_events_for(self, run_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM failure_triage_events WHERE run_id = ? ORDER BY seq",
                (run_id,),
            ).fetchall()
        return [dict(row) for row in rows]


def _decode_maintenance_notice(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["detail"] = _loads(data.pop("detail_json", None), None)
    data["action"] = _loads(data.pop("action_json", None), {})
    return data


def _decode_synthesis_manifest(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    for key in (
        "membership",
        "revision_ids",
        "asset_hashes",
        "extraction_ids",
        "unit_inventory_versions",
        "scope",
        "brief",
        "extractor_versions",
        "token_budget",
        "estimated_usage",
    ):
        data[key] = _loads(data.pop(f"{key}_json", None), None)
    return data


def _decode_synthesis_run(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    for key in (
        "span_request",
        "resolved_span_hashes",
        "coverage_decisions",
        "actual_usage",
        "candidate_output",
    ):
        data[key] = _loads(data.pop(f"{key}_json", None), None)
    return data


def _decode_apply_intent(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["item_ids"] = _loads(data.pop("item_ids_json"), [])
    data["targets"] = _loads(data.pop("targets_json"), [])
    data["db_plan"] = _loads(data.pop("db_plan_json"), [])
    if "conflict_json" in data:
        data["conflicts"] = _loads(data.pop("conflict_json"), [])
    return data


def _practice_item_state(row: sqlite3.Row) -> PracticeItemState:
    return PracticeItemState(
        practice_item_id=row["practice_item_id"],
        difficulty=row["difficulty"],
        stability=row["stability"],
        retrievability=row["retrievability"],
        due_at=row["due_at"],
        active=bool(row["active"]),
        content_hash=row["content_hash"],
        last_attempt_at=row["last_attempt_at"],
        updated_at=row["updated_at"],
    )


def _mastery_state(row: sqlite3.Row) -> MasteryState:
    return MasteryState(
        learning_object_id=row["learning_object_id"],
        logit_mean=row["logit_mean"],
        logit_variance=row["logit_variance"],
        evidence_count=row["evidence_count"],
        last_evidence_at=row["last_evidence_at"],
        algorithm_version=row["algorithm_version"],
        updated_at=row["updated_at"],
    )


def _facet_recall_state(row: sqlite3.Row) -> FacetRecallState:
    return FacetRecallState(
        id=row["id"],
        learning_object_id=row["learning_object_id"],
        facet_id=row["facet_id"],
        practice_item_id=row["practice_item_id"],
        recall_alpha=row["recall_alpha"],
        recall_beta=row["recall_beta"],
        recall_mean=row["recall_mean"],
        recall_variance=row["recall_variance"],
        independent_evidence_mass=row["independent_evidence_mass"],
        raw_coverage_mass=row["raw_coverage_mass"],
        last_attempt_at=row["last_attempt_at"],
        last_error_at=row["last_error_at"],
        consecutive_failures=row["consecutive_failures"],
        algorithm_version=row["algorithm_version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _canonical_facet_recall_state(row: sqlite3.Row) -> CanonicalFacetRecallState:
    return CanonicalFacetRecallState(
        id=row["id"],
        facet_id=row["facet_id"],
        capability_key=row["capability_key"],
        practice_item_id=row["practice_item_id"],
        recall_alpha=row["recall_alpha"],
        recall_beta=row["recall_beta"],
        recall_mean=row["recall_mean"],
        recall_variance=row["recall_variance"],
        independent_evidence_mass=row["independent_evidence_mass"],
        raw_coverage_mass=row["raw_coverage_mass"],
        last_observed_at=row["last_observed_at"],
        last_error_at=row["last_error_at"],
        consecutive_failures=row["consecutive_failures"],
        algorithm_version=row["algorithm_version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _facet_capability_evidence(row: sqlite3.Row) -> FacetCapabilityEvidence:
    return FacetCapabilityEvidence(
        facet_id=row["facet_id"],
        capability=row["capability"],
        direct_positive_mass=row["direct_positive_mass"],
        direct_negative_mass=row["direct_negative_mass"],
        embedded_positive_mass=row["embedded_positive_mass"],
        embedded_negative_mass=row["embedded_negative_mass"],
        certification_credit=row["certification_credit"],
        direct_certification_credit=row["direct_certification_credit"],
        embedded_certification_credit=row["embedded_certification_credit"],
        unexercised_supporting_mass=row["unexercised_supporting_mass"],
        independent_surface_groups=[str(g) for g in _loads(row["independent_surface_groups_json"], [])],
        algorithm_version=row["algorithm_version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _capability_residual_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "facet_id": row["facet_id"],
        "capability": row["capability"],
        "active": bool(row["active"]),
        "activation_reason": row["activation_reason"],
        "residual_alpha": row["residual_alpha"],
        "residual_beta": row["residual_beta"],
        "residual_mean": row["residual_mean"],
        "parent_alpha": row["parent_alpha"],
        "parent_beta": row["parent_beta"],
        "parent_mean": row["parent_mean"],
        "divergence": row["divergence"],
        "independent_groups": int(row["independent_groups"]),
        "independent_mass": row["independent_mass"],
        "algorithm_version": row["algorithm_version"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _resolve_merge(facet_id: str, merge_map: Mapping[str, str]) -> str:
    """Follow retired->surviving edges to the terminal survivor.

    Assumes the map is acyclic (enforced at write time by ``insert_facet_merge``);
    a defensive visited-set still guards against a malformed table."""

    seen: set[str] = set()
    current = facet_id
    while current in merge_map and current not in seen:
        seen.add(current)
        current = merge_map[current]
    return current


def _reaches(start: str, target: str, merge_map: Mapping[str, str]) -> bool:
    seen: set[str] = set()
    current = start
    while current in merge_map and current not in seen:
        if current == target:
            return True
        seen.add(current)
        current = merge_map[current]
    return current == target


def _facet_uncertainty_state(row: sqlite3.Row) -> FacetUncertaintyState:
    return FacetUncertaintyState(
        id=row["id"],
        learning_object_id=row["learning_object_id"],
        facet_id=row["facet_id"],
        hypothesis_marginal={
            str(label): float(probability)
            for label, probability in _loads(row["hypothesis_marginal"], {}).items()
        },
        uncertainty=float(row["uncertainty"]),
        status=row["status"],
        opened_by_attempt_id=row["opened_by_attempt_id"],
        opened_reason=row["opened_reason"],
        last_evidence_at=row["last_evidence_at"],
        algorithm_version=row["algorithm_version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _practice_item_quality_state(row: sqlite3.Row) -> PracticeItemQualityState:
    return PracticeItemQualityState(
        practice_item_id=row["practice_item_id"],
        bad_item_suspicion=row["bad_item_suspicion"],
        evidence_count=row["evidence_count"],
        suspicion_reasons=_loads(row["suspicion_reasons_json"], []),
        last_flagged_at=row["last_flagged_at"],
        algorithm_version=row["algorithm_version"],
        updated_at=row["updated_at"],
    )


def _decode_ability_transition_event(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["target_facets"] = _loads(payload.pop("target_facets_json"), [])
    payload["applied_to_belief_counts"] = bool(payload["applied_to_belief_counts"])
    payload["applied_to_mastery"] = bool(payload["applied_to_mastery"])
    payload["applied_to_facet_recall"] = bool(payload["applied_to_facet_recall"])
    return payload


def _decode_fitted_parameters(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["params"] = _loads(payload.pop("params_json"), {})
    payload["metrics"] = _loads(payload.pop("metrics_json"), None)
    payload["active"] = bool(payload["active"])
    return payload


def _decode_item_parameter_state(row: sqlite3.Row) -> ItemParameterState:
    return ItemParameterState(
        practice_item_id=row["practice_item_id"],
        b_mean=row["b_mean"],
        b_var=row["b_var"],
        evidence_count=row["evidence_count"],
        algorithm_version=row["algorithm_version"],
        updated_at=row["updated_at"],
    )


def _decode_derived_state_rebuild(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["learning_object_ids"] = _loads(payload.pop("learning_object_ids_json"), [])
    if "projection_switches_json" in payload:
        payload["projection_switches"] = _loads(payload.pop("projection_switches_json"), None)
    return payload


def _decode_question_event(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["facets"] = _loads(payload.pop("facets_json"), [])
    payload["source_context"] = _loads(payload.pop("source_context_json", None), {})
    payload["hint_equivalent"] = bool(payload["hint_equivalent"])
    payload["leak_suspected"] = bool(payload["leak_suspected"])
    # saved_note_id (migration 027) is a plain column and rides along in
    # dict(row); older DBs predating the transcript join surface it as None.
    payload.setdefault("saved_note_id", None)
    # §13.4 context columns (migration 030) ride along in dict(row); default
    # them for rows read before the migration applied.
    payload.setdefault("signal_channel", None)
    # Reveal quantification (migration 154); absent on rows read from a DB that
    # predates the ledger.
    payload.setdefault("leak_overlap", None)
    payload.setdefault("remediation_episode_id", None)
    if payload.get("direct_explanation_request") is not None:
        payload["direct_explanation_request"] = bool(payload["direct_explanation_request"])
    return payload


def _decode_question_promotion(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["attributed_facets"] = _loads(payload.pop("attributed_facets_json"), [])
    attempted = payload.get("attempted_in_thread")
    payload["attempted_in_thread"] = None if attempted is None else bool(attempted)
    return payload


def _decode_question_promotion_request(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["retryable"] = bool(payload.get("retryable"))
    return payload


def _decode_elicitation_event(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["target_scope"] = _loads(payload.pop("target_scope_json"), None)
    payload["candidate_scores"] = _loads(payload.pop("candidate_scores_json"), None)
    payload["hypothesis_set"] = _loads(payload.pop("hypothesis_set_json"), None)
    return payload


def _decode_decision_features(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["ability_vector"] = _loads(payload.pop("ability_vector_json"), {})
    payload["item_demand_vector"] = _loads(payload.pop("item_demand_vector_json"), None)
    payload["context"] = _loads(payload.pop("context_json"), {})
    return payload


def _decode_scheduler_explanation(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["components"] = _loads(payload.pop("components_json"), {})
    payload["target_scope"] = _loads(payload.pop("target_scope_json"), None)
    payload["plain_english"] = _loads(payload.pop("plain_english_json"), None)
    return payload


def _decode_scheduler_slate_candidate(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["was_returned"] = bool(payload["was_returned"])
    payload["components"] = _loads(payload.pop("components_json"), {})
    payload["reward_debug"] = _loads(payload.pop("reward_debug_json"), None)
    payload["target_scope"] = _loads(payload.pop("target_scope_json"), None)
    payload["plain_english"] = _loads(payload.pop("plain_english_json"), None)
    return payload


def _learning_object_id_from_target_scope(target_scope: Any) -> str | None:
    if not isinstance(target_scope, Mapping):
        return None
    value = target_scope.get("learning_object_id")
    return str(value) if value is not None else None


def _decode_proposal_batch(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["source_refs"] = _loads(payload.pop("source_refs_json"), [])
    return payload


def _decode_proposal_item(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["payload"] = _loads(payload.pop("payload_json"), {})
    payload["source_ref_ids"] = _loads(payload.pop("source_ref_ids_json", None), [])
    payload["audit"] = _loads(payload.pop("audit_json", None), None)
    payload["edited_payload"] = _loads(payload.pop("edited_payload_json"), None)
    payload["validation_errors"] = _loads(payload.pop("validation_errors_json"), [])
    if "dependency_block_reason_json" in payload:
        payload["dependency_block_reason"] = _loads(payload.pop("dependency_block_reason_json"), None)
    return payload


def _content_event_has_source_grounding(row: sqlite3.Row) -> bool:
    payload = _loads(row["_proposal_edited_payload_json"], None)
    if payload is None:
        payload = _loads(row["_proposal_payload_json"], {})
    provenance = payload.get("provenance") if isinstance(payload, dict) else None
    if not isinstance(provenance, dict):
        return False
    source_refs = provenance.get("source_refs")
    return isinstance(source_refs, list) and bool(source_refs)
