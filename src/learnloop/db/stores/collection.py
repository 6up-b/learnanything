"""Immutable entry-point provenance for versioned local data collection."""
from __future__ import annotations

import json
import logging
import sqlite3
from collections.abc import Mapping
from typing import Any

from learnloop.clock import utc_now_iso
from learnloop.db.stores.router import append_router_decision, record_learner_pick
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from learnloop.ids import new_ulid
from learnloop.outcome_contract import COLLECTION_VERSION, LABEL_VERSION

_EVIDENCE_ROLES = {TableRole.RAW_LEDGER, TableRole.RECEIPT}


def _single_primary_key(connection: sqlite3.Connection, table: str) -> str | None:
    """The table's one primary-key column, or None for rowid or composite keys."""
    escaped = table.replace('"', '""')
    key_columns = [row[1] for row in connection.execute(f'PRAGMA table_info("{escaped}")') if row[5] > 0]
    return key_columns[0] if len(key_columns) == 1 else None


def _check_evidence_reference(connection: sqlite3.Connection, reference: object) -> None:
    if not isinstance(reference, dict):
        raise ValueError("Each evidence reference must be a {table, id} object.")
    table = reference.get("table")
    key = reference.get("id")
    if not isinstance(table, str) or not isinstance(key, str) or not key:
        raise ValueError("Each evidence reference needs a string table and a string id.")
    if TABLE_ROLES.get(table) not in _EVIDENCE_ROLES:
        raise ValueError(f"Adjudication evidence must reference a retained ledger or receipt table, not {table!r}.")
    key_column = _single_primary_key(connection, table)
    if key_column is None:
        raise ValueError(f"Evidence table {table!r} has no single-column primary key to reference by id.")
    escaped_table = table.replace('"', '""')
    escaped_column = key_column.replace('"', '""')
    found = connection.execute(f'SELECT 1 FROM "{escaped_table}" WHERE "{escaped_column}"=?', (key,)).fetchone()
    if found is None:
        raise ValueError(f"Evidence reference {table}.{key_column}={key!r} does not exist.")



def _offer_open(connection, candidate_id: str, session_id: str, practice_item_id: str) -> bool:
    return connection.execute(
        """SELECT c.id FROM scheduler_slate_candidates c JOIN scheduler_slates s ON s.id=c.slate_id
           WHERE c.id=? AND s.session_id=? AND c.practice_item_id=? AND c.was_returned=1 AND c.chosen_attempt_id IS NULL""",
        (candidate_id, session_id, practice_item_id),
    ).fetchone() is not None

class CollectionStoreMixin:
    def finalize_scheduler_offer(
        self,
        slate_id: str | None,
        candidate_ids: list[str],
        *,
        entry_surface: str = "desktop_queue",
        router_decision: Mapping[str, Any] | None = None,
    ) -> None:
        """Publish the offer; router R1's decision row commits with it.

        ``router_decision`` (built by ``learnloop.router.decisions``) is written in
        the receipt's own transaction, so a published offer and its logged
        decision never disagree. A republished (identical) offer writes nothing.
        A row the ledger refuses (a CHECK or NOT NULL violation) rolls back
        alone with a warning; the offer still publishes.
        """

        if slate_id is None:
            return
        encoded = json.dumps(candidate_ids)
        with self.atomic(), self.connection() as connection:
            existing = connection.execute("SELECT returned_candidate_ids_json FROM scheduler_offer_receipts WHERE slate_id=?", (slate_id,)).fetchone()
            if existing:
                if existing[0] != encoded:
                    raise ValueError("A published offer cannot change.")
                return
            eligible = {row[0] for row in connection.execute("SELECT id FROM scheduler_slate_candidates WHERE slate_id=? AND was_returned=1", (slate_id,))}
            if len(candidate_ids) != len(set(candidate_ids)) or not set(candidate_ids) <= eligible:
                raise ValueError("Final offers must be an ordered subset of the selected candidates.")
            connection.execute("UPDATE scheduler_slate_candidates SET was_returned=0,returned_rank=NULL WHERE slate_id=?", (slate_id,))
            connection.executemany("UPDATE scheduler_slate_candidates SET was_returned=1,returned_rank=? WHERE id=? AND slate_id=?", [(rank, candidate_id, slate_id) for rank, candidate_id in enumerate(candidate_ids, 1)])
            connection.execute("UPDATE scheduler_slates SET returned_count=? WHERE id=?", (len(candidate_ids), slate_id))
            connection.execute("INSERT INTO scheduler_offer_receipts(slate_id,returned_candidate_ids_json,entry_surface,collection_version,created_at) VALUES (?,?,?,?,?)", (slate_id, encoded, entry_surface, COLLECTION_VERSION, utc_now_iso()))
            if router_decision is not None:
                append_router_decision(connection, router_decision)

    def record_false_remediation(self, *, attempt_id: str, value: bool, evidence_refs: list[dict[str, str]], author_kind: str, verifier_version: str) -> str:
        if type(value) is not bool or not evidence_refs or author_kind not in {"human", "machine"} or not verifier_version.strip():
            raise ValueError("An adjudication requires a boolean value, evidence, author kind and verifier version.")
        with self.atomic(), self.connection() as connection:
            # The ledger carries no foreign key (see migration 164), so the
            # attempt's existence is checked here.
            if connection.execute("SELECT 1 FROM practice_attempts WHERE id=?", (attempt_id,)).fetchone() is None:
                raise ValueError(f"Attempt {attempt_id!r} does not exist.")
            for reference in evidence_refs:
                _check_evidence_reference(connection, reference)
            identifier = new_ulid()
            connection.execute(
                "INSERT INTO false_remediation_adjudications(id,attempt_id,label_value,evidence_refs_json,author_kind,verifier_version,label_version,collection_version,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (identifier, attempt_id, int(value), json.dumps(evidence_refs, sort_keys=True), author_kind, verifier_version, LABEL_VERSION, COLLECTION_VERSION, utc_now_iso()),
            )
        return identifier

    def scheduler_offer_open(self, *, scheduler_candidate_id: str, session_id: str, practice_item_id: str) -> bool:
        """Whether an offer is still an unanswered offer of this item in this
        session: the check :meth:`bind_submission_offer` makes, read-only."""

        with self.connection() as connection:
            return _offer_open(connection, scheduler_candidate_id, session_id, practice_item_id)

    def scheduler_offer_answered(self, *, scheduler_candidate_id: str, session_id: str, practice_item_id: str) -> bool:
        """Whether an offer is a real offer of this item in this session that
        an attempt has already answered (stale, not foreign): read-only."""

        with self.connection() as connection:
            return connection.execute(
                """SELECT 1 FROM scheduler_slate_candidates c JOIN scheduler_slates s ON s.id=c.slate_id
                   WHERE c.id=? AND s.session_id=? AND c.practice_item_id=? AND c.was_returned=1
                     AND c.chosen_attempt_id IS NOT NULL""",
                (scheduler_candidate_id, session_id, practice_item_id),
            ).fetchone() is not None

    def submission_offer_answered_elsewhere(self, *, submission_id: str, practice_item_id: str) -> str | None:
        """The attempt that answered this submission's bound offer, when that
        attempt is another submission's (else None): read-only.

        Owner capture 2026-10-25 (B4): the answer box's draft binds its retry
        key to the queue's offer; when the same item is then answered under
        another key (its steps, say), that attempt takes the offer, and the
        key, should it ever be submitted, answers no open offer. A submission
        whose own attempt committed (a retry) is never reported."""

        with self.connection() as connection:
            if connection.execute("SELECT 1 FROM practice_attempts WHERE submission_id=?",
                                  (submission_id,)).fetchone() is not None:
                return None
            row = connection.execute(
                """SELECT c.chosen_attempt_id FROM submission_intents i
                   JOIN scheduler_slate_candidates c ON c.id=i.scheduler_candidate_id
                   JOIN practice_attempts a ON a.id=c.chosen_attempt_id
                   WHERE i.submission_id=? AND i.practice_item_id=?
                     AND (a.submission_id IS NULL OR a.submission_id != i.submission_id)""",
                (submission_id, practice_item_id),
            ).fetchone()
        return str(row[0]) if row is not None else None

    def bind_submission_offer(self, *, submission_id: str | None, session_id: str, practice_item_id: str, scheduler_candidate_id: str | None, entry_surface: str = "desktop_practice", record_pick: bool = True) -> str | None:
        """Return the scheduler offer a submission answers, binding it on first use.

        The first offer bound to a submission id wins: the learner composed the
        answer under it. Reopening the item from a refreshed queue presents that
        queue's offer for the same item with the same submission id; it is
        accepted when it is a real offer of that item in that session, and the
        original offer is returned. A submission id reused for another item or
        session, or an offer that does not belong to them, is rejected.

        ``record_pick=False`` validates an offer without logging a router
        learner pick: a teach-back conversation already bound to its first
        offer only checks a refreshed list's offer of the same item.
        """

        def require_offered(connection, candidate_id: str) -> None:
            if not _offer_open(connection, candidate_id, session_id, practice_item_id):
                raise ValueError("The scheduler offer does not belong to this item/session or was already consumed.")

        def bound_offer(connection) -> tuple[bool, str | None]:
            existing = connection.execute("SELECT * FROM submission_intents WHERE submission_id=?", (submission_id,)).fetchone() if submission_id else None
            if existing is None:
                return False, None
            if existing["session_id"] != session_id or existing["practice_item_id"] != practice_item_id:
                raise ValueError("The submission belongs to a different item or session.")
            if scheduler_candidate_id is not None and scheduler_candidate_id != existing["scheduler_candidate_id"]:
                require_offered(connection, scheduler_candidate_id)
            return True, existing["scheduler_candidate_id"]

        # Draft autosaves repeat the bind for an existing intent; reading it
        # first keeps them from taking the write lock.
        with self.connection() as connection:
            bound, original = bound_offer(connection)
        if bound:
            return original
        with self.atomic(), self.connection() as connection:
            bound, original = bound_offer(connection)
            if bound:
                return original
            if scheduler_candidate_id is not None:
                require_offered(connection, scheduler_candidate_id)
            created_at = utc_now_iso()
            if submission_id:
                connection.execute(
                    "INSERT INTO submission_intents(submission_id,session_id,practice_item_id,scheduler_candidate_id,entry_surface,created_at) VALUES (?,?,?,?,?,?)",
                    (submission_id, session_id, practice_item_id, scheduler_candidate_id, entry_surface, created_at),
                )
            if scheduler_candidate_id is not None and record_pick:
                # Router R1: a first bind to an offered candidate other than the
                # logged offer's head is a learner pick (no propensity). Same
                # transaction as the bind, so the two never disagree; its own
                # savepoint, so a logging failure never fails the bind.
                connection.execute("SAVEPOINT router_learner_pick")
                try:
                    record_learner_pick(
                        connection,
                        scheduler_candidate_id=scheduler_candidate_id,
                        practice_item_id=practice_item_id,
                        session_id=session_id,
                        entry_surface=entry_surface,
                        submission_id=submission_id,
                        created_at=created_at,
                    )
                except Exception:  # logging never fails the bind
                    connection.execute("ROLLBACK TO router_learner_pick")
                    logging.getLogger(__name__).warning(
                        "router R1: learner pick of candidate %s not logged", scheduler_candidate_id,
                        exc_info=True,
                    )
                connection.execute("RELEASE router_learner_pick")
            return scheduler_candidate_id
