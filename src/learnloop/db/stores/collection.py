"""Immutable entry-point provenance for versioned local data collection."""
from __future__ import annotations

import json
import sqlite3

from learnloop.clock import utc_now_iso
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


class CollectionStoreMixin:
    def finalize_scheduler_offer(self, slate_id: str | None, candidate_ids: list[str], *, entry_surface: str = "desktop_queue") -> None:
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

    def bind_submission_offer(self, *, submission_id: str | None, session_id: str, practice_item_id: str, scheduler_candidate_id: str | None, entry_surface: str = "desktop_practice") -> str | None:
        with self.atomic(), self.connection() as connection:
            existing = connection.execute("SELECT * FROM submission_intents WHERE submission_id=?", (submission_id,)).fetchone() if submission_id else None
            if existing is not None:
                if existing["session_id"] != session_id or existing["practice_item_id"] != practice_item_id:
                    raise ValueError("The submission belongs to a different item or session.")
                if scheduler_candidate_id is not None and scheduler_candidate_id != existing["scheduler_candidate_id"]:
                    raise ValueError("The submission's original scheduler offer cannot change.")
                return existing["scheduler_candidate_id"]
            if scheduler_candidate_id is not None:
                candidate = connection.execute(
                    """SELECT c.id FROM scheduler_slate_candidates c JOIN scheduler_slates s ON s.id=c.slate_id
                       WHERE c.id=? AND s.session_id=? AND c.practice_item_id=? AND c.was_returned=1 AND c.chosen_attempt_id IS NULL""",
                    (scheduler_candidate_id, session_id, practice_item_id),
                ).fetchone()
                if candidate is None:
                    raise ValueError("The scheduler offer does not belong to this item/session or was already consumed.")
            if submission_id:
                connection.execute(
                    "INSERT INTO submission_intents(submission_id,session_id,practice_item_id,scheduler_candidate_id,entry_surface,created_at) VALUES (?,?,?,?,?,?)",
                    (submission_id, session_id, practice_item_id, scheduler_candidate_id, entry_surface, utc_now_iso()),
                )
            return scheduler_candidate_id
