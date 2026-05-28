from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths


@dataclass(frozen=True)
class DebugAdvanceResult:
    days: int
    shifted_cells: int
    shifted_fields: dict[str, int]

    def as_dict(self) -> dict[str, object]:
        return {
            "days": self.days,
            "shifted_cells": self.shifted_cells,
            "shifted_fields": self.shifted_fields,
        }


TIMESTAMP_FIELDS: dict[str, tuple[str, ...]] = {
    "practice_item_state": ("due_at", "last_attempt_at", "updated_at"),
    "learning_object_mastery": ("last_evidence_at", "updated_at"),
    "learner_theta": ("updated_at",),
    "learner_claims": ("created_at",),
    "error_events": ("created_at", "updated_at"),
    "practice_attempts": ("created_at", "updated_at"),
    "grading_evidence": ("created_at", "superseded_at"),
    "attempt_surprise": ("created_at",),
    "lo_probe_state": ("entered_at", "completed_at", "updated_at"),
    "hypothesis_sets": ("created_at",),
    "learner_state_beliefs": ("last_evidence_at", "updated_at"),
    "elicitation_events": ("created_at",),
    "scheduler_explanations": ("created_at",),
    "attempt_feedback_metadata": ("created_at", "updated_at"),
    "observation_events": ("created_at",),
}


class DebugAdvanceError(ValueError):
    pass


def advance_vault_days(root: Path, days: int) -> DebugAdvanceResult:
    if days <= 0:
        raise DebugAdvanceError("days must be a positive integer")

    vault = load_vault(root)
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    modifier = f"-{days} days"
    shifted_fields: dict[str, int] = {}
    shifted_cells = 0

    with sqlite3.connect(sqlite_path) as connection:
        existing = _existing_timestamp_fields(connection)
        for table, fields in TIMESTAMP_FIELDS.items():
            table_fields = existing.get(table, set())
            for field in fields:
                if field not in table_fields:
                    continue
                changed = _shift_field(connection, table, field, modifier)
                if changed:
                    shifted_fields[f"{table}.{field}"] = changed
                    shifted_cells += changed
        connection.commit()

    return DebugAdvanceResult(days=days, shifted_cells=shifted_cells, shifted_fields=shifted_fields)


def _existing_timestamp_fields(connection: sqlite3.Connection) -> dict[str, set[str]]:
    tables = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    existing: dict[str, set[str]] = {}
    for row in tables:
        table = str(row[0])
        columns = connection.execute(f"PRAGMA table_info({_quote_identifier(table)})").fetchall()
        existing[table] = {str(column[1]) for column in columns}
    return existing


def _shift_field(connection: sqlite3.Connection, table: str, field: str, modifier: str) -> int:
    table_sql = _quote_identifier(table)
    field_sql = _quote_identifier(field)
    cursor = connection.execute(
        f"""
        UPDATE {table_sql}
        SET {field_sql} = strftime('%Y-%m-%dT%H:%M:%SZ', datetime({field_sql}, ?))
        WHERE {field_sql} IS NOT NULL
        """,
        (modifier,),
    )
    return int(cursor.rowcount if cursor.rowcount is not None else 0)


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'
