"""Short transactions for call receipts and validated ingestion checkpoints."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any
from contextlib import closing

from learnloop.db.connection import connect
from learnloop.db.scopes import allow_late_model_observation


class ModelCallStoreMixin:
    def record_model_event(self, action: str, event: dict[str, Any], *, owner_kind: str, owner_id: str) -> None:
        if action == "finish":
            fields = ("status", "finished_at", "input_tokens", "output_tokens", "cached_input_tokens", "cache_write_tokens", "reasoning_tokens", "cost", "provider_response_id", "resolved_model", "usage_json", "finish_reason", "error_type", "output_text")
            # This call already owns a durable start. A late response may
            # finalize only that receipt, never a checkpoint or canonical row.
            # Use a separate short connection so a borrowed job fence cannot
            # drop known usage after takeover.
            with allow_late_model_observation(), closing(connect(self.sqlite_path, read_only=self._read_only)) as connection, connection:
                connection.execute(
                    f"UPDATE model_call_receipts SET {','.join(f'{field}=?' for field in fields)} WHERE id=? AND status='started' AND owner_kind=? AND owner_id=?",
                    (*(event.get(field) for field in fields), event["id"], owner_kind, owner_id),
                )
            return
        with self.connection() as connection:
            if action == "start":
                fields = ("id", "parent_call_id", "purpose", "provider", "model", "endpoint", "prompt_hash", "schema_hash", "input_text", "schema_json", "output_budget_tokens", "started_at")
                connection.execute(
                    f"INSERT INTO model_call_receipts ({','.join(fields)},owner_kind,owner_id,status) VALUES ({','.join('?' for _ in fields)},?,?,'started')",
                    (*(event.get(field) for field in fields), owner_kind, owner_id),
                )
            else:
                raise ValueError(f"Unknown model receipt action: {action}")

    def model_checkpoint(self, cache_key: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT result_json,usage_json FROM model_work_checkpoints WHERE cache_key=?", (cache_key,)).fetchone()
        return {"result": json.loads(row[0]), "usage": json.loads(row[1])} if row else None

    def save_model_checkpoint(self, cache_key: str, *, purpose: str, result: dict[str, Any], usage: dict[str, Any] | None = None) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO model_work_checkpoints(cache_key,purpose,result_json,usage_json,created_at) VALUES (?,?,?,?,?) ON CONFLICT(cache_key) DO NOTHING",
                (cache_key, purpose, json.dumps(result, sort_keys=True), json.dumps(usage or {}, sort_keys=True), datetime.now(timezone.utc).isoformat()),
            )
