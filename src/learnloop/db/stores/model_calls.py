"""Short transactions for call receipts and validated ingestion checkpoints."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any
from contextlib import closing

from learnloop.db.connection import connect
from learnloop.db.scopes import allow_late_model_records
from learnloop.db.stores.source_service import ReservationReleased, released_reservations

#: Optional receipt labels (``learnloop.ai.execution.call_labels``).
LABEL_FIELDS = ("judge", "question_set_version", "state_hash")


_FINISH_FIELDS = ("status", "finished_at", "input_tokens", "output_tokens", "cached_input_tokens", "cache_write_tokens", "reasoning_tokens", "cost", "provider_response_id", "resolved_model", "usage_json", "finish_reason", "error_type", "output_text")


def finish_receipt(connection: Any, event: dict[str, Any], *, owner_kind: str, owner_id: str) -> None:
    """Finalize a started receipt on the caller's connection (the caller owns the transaction)."""

    connection.execute(
        f"UPDATE model_call_receipts SET {','.join(f'{field}=?' for field in _FINISH_FIELDS)} WHERE id=? AND status='started' AND owner_kind=? AND owner_id=?",
        (*(event.get(field) for field in _FINISH_FIELDS), event["id"], owner_kind, owner_id),
    )


def insert_checkpoint(connection: Any, cache_key: str, *, purpose: str, result: dict[str, Any], usage: dict[str, Any] | None = None) -> None:
    """Write a checkpoint once on the caller's connection (the caller owns the transaction)."""

    connection.execute(
        "INSERT INTO model_work_checkpoints(cache_key,purpose,result_json,usage_json,created_at) VALUES (?,?,?,?,?) ON CONFLICT(cache_key) DO NOTHING",
        (cache_key, purpose, json.dumps(result, sort_keys=True), json.dumps(usage or {}, sort_keys=True), datetime.now(timezone.utc).isoformat()),
    )


def delete_checkpoint(connection: Any, cache_key: str) -> None:
    """Delete one checkpoint on the caller's connection (the caller owns the transaction)."""

    connection.execute("DELETE FROM model_work_checkpoints WHERE cache_key=?", (cache_key,))


class ModelCallStoreMixin:
    def record_model_event(self, action: str, event: dict[str, Any], *, owner_kind: str, owner_id: str) -> None:
        if action == "finish":
            # This call already owns a durable start. A late response may
            # finalize only that receipt, never a canonical row. Use a separate
            # short connection so a borrowed job fence cannot drop known usage
            # after takeover.
            with allow_late_model_records(), closing(connect(self.sqlite_path, read_only=self._read_only)) as connection, connection:
                finish_receipt(connection, event, owner_kind=owner_kind, owner_id=owner_id)
            return
        with self.connection() as connection:
            if action == "start":
                fields = ("id", "parent_call_id", "purpose", "provider", "model", "endpoint", "prompt_hash", "schema_hash", "input_text", "schema_json", "budget_json", "output_budget_tokens", "started_at")
                # Judgment-call labels (migration 175) are written only when a
                # caller set them, so unlabelled calls keep working on a
                # database below that migration.
                fields += tuple(label for label in LABEL_FIELDS if event.get(label) is not None)
                connection.execute(
                    f"INSERT INTO model_call_receipts ({','.join(fields)},owner_kind,owner_id,status) VALUES ({','.join('?' for _ in fields)},?,?,'started')",
                    (*(event.get(field) for field in fields), owner_kind, owner_id),
                )
                # Fenced by the daily cap's recovery (sources spend accounting):
                # a root receipt naming a reservation recovery released does
                # not start, so its request is never sent. Checked after the
                # insert, in its transaction, so the release cannot interleave.
                if event.get("parent_call_id") is None and event.get("budget_json"):
                    released = released_reservations(connection, event.get("budget_json"))
                    if released:
                        raise ReservationReleased(
                            f"reservation {', '.join(released)} was released by recovery (its owner was presumed "
                            "terminal): the request is not sent")
            else:
                raise ValueError(f"Unknown model receipt action: {action}")

    def model_call_roots_since(self, *, owner_kind: str, since: str) -> int:
        """Logical model calls (root receipts) of one owner kind started at or
        after ``since`` -- failed and unfinished calls included, since a receipt
        is written before its request is sent."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM model_call_receipts WHERE owner_kind = ? AND parent_call_id IS NULL "
                "AND started_at >= ?",
                (owner_kind, since),
            ).fetchone()
        return int(row[0] or 0)

    def model_call_spend_rows(
        self,
        *,
        started_since: str | None = None,
        owner_kind: str | None = None,
        owner_ids: Any = None,
    ) -> list[dict[str, Any]]:
        """Usage rows for spend accounting: every receipt (usage lands on the
        innermost one), optionally since an ISO time and for some owners."""

        query = (
            "SELECT provider, input_tokens, output_tokens, cost, usage_json, output_budget_tokens, budget_json, "
            "parent_call_id, status, started_at, owner_kind, owner_id FROM model_call_receipts WHERE 1=1"
        )
        params: list[Any] = []
        if started_since is not None:
            query += " AND started_at >= ?"
            params.append(started_since)
        if owner_kind is not None:
            query += " AND owner_kind = ?"
            params.append(owner_kind)
        if owner_ids is not None:
            ids = sorted({str(value) for value in owner_ids})
            if not ids:
                return []
            query += f" AND owner_id IN ({','.join('?' for _ in ids)})"
            params.extend(ids)
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def model_checkpoint(self, cache_key: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT result_json,usage_json FROM model_work_checkpoints WHERE cache_key=?", (cache_key,)).fetchone()
        return {"result": json.loads(row[0]), "usage": json.loads(row[1])} if row else None

    def save_model_checkpoint(self, cache_key: str, *, purpose: str, result: dict[str, Any], usage: dict[str, Any] | None = None) -> None:
        # Saved even after the job lost ownership (see allow_late_model_records).
        # A separate short connection keeps a borrowed, fenced connection from
        # rejecting it.
        with allow_late_model_records(), closing(connect(self.sqlite_path, read_only=self._read_only)) as connection, connection:
            insert_checkpoint(connection, cache_key, purpose=purpose, result=result, usage=usage)

    def discard_model_checkpoint(self, cache_key: str) -> None:
        """Delete a checkpoint whose stored result no longer validates.

        Checkpoints are write-once, so an unreadable one would otherwise fail
        every retry of the work it was meant to save.
        """

        with self.connection() as connection:
            delete_checkpoint(connection, cache_key)
