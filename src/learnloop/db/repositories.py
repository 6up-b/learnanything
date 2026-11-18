"""SQLite repository facade and transaction boundaries.

Repository opens the database and supplies connection, atomic and pinned scopes.
It dispatches record lookups and keeps operations that span feature tables together.
Feature mixins in learnloop.db.stores supply inherited repository methods.
Shared row types and decoders live in learnloop.db.records.
The facade also holds outcome schema and calibration model minting methods."""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

from learnloop import hint_window
from learnloop.activation_journal import refuse_if_interrupted
from learnloop.recurrence import key_for_statement, recurrence_key
from learnloop.outcome_contract import COLLECTION_VERSION
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.migrate import create_or_attach_current
from learnloop.db.row_serialization import _json, _loads
from learnloop.db.records import (
    ItemParameterState,
    MasteryState,
    PracticeItemState,
    ProbePresentationRecord,
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
)
from learnloop.db.records import (
    _CAPABILITY_RESIDUAL_PROJECTION,
    _FACET_CAPABILITY_PROJECTION,
    _FACET_RECALL_PROJECTION,
    _decode_decision_features,
    _decode_elicitation_event,
    _decode_proposal_batch,
    _decode_proposal_item,
    _decode_scheduler_explanation,
    _decode_scheduler_slate_candidate,
    _facet_uncertainty_state,
)
from learnloop.db.stores.content import ContentStoreMixin
from learnloop.db.stores.facet_projection import FacetProjectionStoreMixin
from learnloop.db.stores.maintenance import MaintenanceStoreMixin
from learnloop.db.stores.practice_state import PracticeStateStoreMixin
from learnloop.db.stores.questions import QuestionStoreMixin
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
from learnloop.ids import new_ulid
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
    ContentStoreMixin,
    QuestionStoreMixin,
    PracticeStateStoreMixin,
    FacetProjectionStoreMixin,
    MaintenanceStoreMixin,
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


def _learning_object_id_from_target_scope(target_scope: Any) -> str | None:
    if not isinstance(target_scope, Mapping):
        return None
    value = target_scope.get("learning_object_id")
    return str(value) if value is not None else None
