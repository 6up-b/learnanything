"""Replay-safe migration of legacy error labels onto causal hypotheses.

Historical ``error_events.error_type`` values remain untouched: they are raw
grading evidence and replay provenance. Causal hypotheses, however, should name
the stable nine-class mechanism basis. This service appends a new immutable
hypothesis version when a legacy label has an unambiguous canonical mapping.
Unknown item-local detector signatures remain unresolved rather than being
laundered into a guessed cause.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.error_taxonomy_map import (
    MECHANISM_TAXONOMY_SET,
    map_legacy_error_type,
)


@dataclass(frozen=True)
class LegacyCausalMigrationReport:
    inspected: int
    migrated: int
    already_canonical: int
    unresolved_hypothesis_ids: tuple[str, ...]
    conflicted_hypothesis_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "inspected": self.inspected,
            "migrated": self.migrated,
            "already_canonical": self.already_canonical,
            "unresolved_hypothesis_ids": list(self.unresolved_hypothesis_ids),
            "conflicted_hypothesis_ids": list(self.conflicted_hypothesis_ids),
        }


def migrate_legacy_causal_basis(
    repository: Repository,
    *,
    clock: Clock | None = None,
) -> LegacyCausalMigrationReport:
    """Append canonical-mechanism versions for legacy causal hypotheses.

    The raw label is read first from the hypothesis evidence receipt and then
    from its linked error event. A pre-existing, different canonical mechanism
    is treated as a conflict and never overwritten.
    """

    rows = repository.all_causal_hypotheses()
    migrated = 0
    already = 0
    unresolved: list[str] = []
    conflicted: list[str] = []

    for row in rows:
        evidence = (
            dict(row.get("evidence") or {})
            if isinstance(row.get("evidence"), dict)
            else {}
        )
        raw_error_type = evidence.get("error_type")
        if not raw_error_type and row.get("error_event_id"):
            record = repository.find_record(str(row["error_event_id"]))
            if record is not None and record[0] == "error_event":
                raw_error_type = record[1].get("error_type")
        canonical = map_legacy_error_type(
            str(raw_error_type) if raw_error_type else None
        )
        if canonical not in MECHANISM_TAXONOMY_SET:
            unresolved.append(str(row["id"]))
            continue
        existing = row.get("mechanism")
        if existing == canonical:
            already += 1
            continue
        if existing is not None:
            conflicted.append(str(row["id"]))
            continue

        repository.append_causal_hypothesis(
            episode_key=str(row["episode_key"]),
            attempt_id=str(row["attempt_id"]),
            error_event_id=(
                str(row["error_event_id"]) if row.get("error_event_id") else None
            ),
            learning_object_id=str(row["learning_object_id"]),
            cause_scope=str(row["cause_scope"]),
            statement=str(row["statement"]),
            statement_normalized=str(row["statement_normalized"]),
            mechanism=canonical,
            operation=(
                str(row["operation"]) if row.get("operation") is not None else None
            ),
            target_ref=row.get("target_ref"),
            applicability=row.get("applicability"),
            postdictive_claims=row.get("postdictive_claims") or (),
            evidence=evidence,
            repair_class_id=row.get("repair_class_id"),
            repair_class_basis=row.get("repair_class_basis"),
            repair_class_unresolved_reason=row.get(
                "repair_class_unresolved_reason"
            ),
            status=str(row["status"]),
            generation_agent_run_id=row.get("generation_agent_run_id"),
            model=row.get("model"),
            clock=clock,
        )
        migrated += 1

    return LegacyCausalMigrationReport(
        inspected=len(rows),
        migrated=migrated,
        already_canonical=already,
        unresolved_hypothesis_ids=tuple(unresolved),
        conflicted_hypothesis_ids=tuple(conflicted),
    )
