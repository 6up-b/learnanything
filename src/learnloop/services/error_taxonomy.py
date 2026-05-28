from __future__ import annotations

from collections.abc import Iterable

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.grading import ValidatedErrorAttribution
from learnloop.vault.models import LoadedVault


BUILTIN_ERROR_TYPES = {
    "arithmetic_slip",
    "conceptual_slip",
    "incomplete_answer",
    "procedure_misapplication",
    "recall_failure",
    "scaffold_failure",
}


def persist_unknown_error_type_proposals(
    vault: LoadedVault,
    repository: Repository,
    *,
    attributions: Iterable[ValidatedErrorAttribution],
    attempt_id: str,
    agent_run_id: str | None,
    related_concept_id: str | None = None,
    clock: Clock | None = None,
) -> str | None:
    if agent_run_id is None:
        return None
    known = set(vault.error_types) | BUILTIN_ERROR_TYPES
    unknown: list[ValidatedErrorAttribution] = []
    for attribution in attributions:
        if attribution.error_type in known:
            continue
        known.add(attribution.error_type)
        unknown.append(attribution)
    if not unknown:
        return None

    now = utc_now_iso(clock)
    rows = [
        {
            "id": new_ulid(),
            "client_item_id": f"error_type:{attribution.error_type}",
            "item_type": "error_type",
            "operation": "create",
            "target_entity_type": None,
            "target_entity_id": None,
            "payload": _error_type_payload(attribution, related_concept_id),
            "decision": "pending",
            "validation_status": "valid",
            "validation_errors": [],
            "created_at": now,
            "updated_at": now,
        }
        for attribution in unknown
    ]
    return repository.persist_proposal_batch(
        {
            "id": new_ulid(),
            "agent_run_id": agent_run_id,
            "purpose": "grading_error_type",
            "source_refs": [
                {
                    "ref_type": "manual_context",
                    "ref_id": attempt_id,
                    "locator": "grading_error_attribution",
                }
            ],
            "summary": "Proposed error taxonomy entries from grading.",
            "created_at": now,
            "updated_at": now,
        },
        rows,
    )


def _error_type_payload(
    attribution: ValidatedErrorAttribution,
    related_concept_id: str | None,
) -> dict[str, object]:
    return {
        "id": attribution.error_type,
        "title": _title_from_id(attribution.error_type),
        "description": attribution.evidence,
        "related_concepts": [related_concept_id] if related_concept_id else [],
        "severity_default": attribution.severity,
        "is_misconception": attribution.is_misconception,
        "tags": ["grading_proposal"],
    }


def _title_from_id(error_type: str) -> str:
    title = error_type.replace("_", " ").replace("-", " ").strip().title()
    return title or error_type
