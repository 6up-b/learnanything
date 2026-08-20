from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from learnloop.ops.debug_time_store import (
    existing_timestamp_fields,
    shift_timestamp_field,
)
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
        existing = existing_timestamp_fields(connection)
        for table, fields in TIMESTAMP_FIELDS.items():
            table_fields = existing.get(table, set())
            for field in fields:
                if field not in table_fields:
                    continue
                changed = shift_timestamp_field(connection, table, field, modifier)
                if changed:
                    shifted_fields[f"{table}.{field}"] = changed
                    shifted_cells += changed
        connection.commit()

    return DebugAdvanceResult(days=days, shifted_cells=shifted_cells, shifted_fields=shifted_fields)
