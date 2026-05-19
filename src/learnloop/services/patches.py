from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid, snake_case
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import (
    VaultWriterError,
    upsert_concept,
    upsert_concept_edge,
    upsert_error_type,
    upsert_learning_object,
    upsert_practice_item,
)


class PatchApplicationError(ValueError):
    pass


@dataclass(frozen=True)
class CompiledPatch:
    proposal_item_id: str
    entity_type: str
    entity_id: str
    subject: str | None
    event_type: str
    summary: str
    apply: Callable[[Path, Clock | None], Path | None]


@dataclass(frozen=True)
class PatchApplyResult:
    applied_count: int
    change_batch_ids: list[str]


def apply_accepted_items(
    root: Path,
    patch_id: str,
    item_ids: list[str] | None = None,
    *,
    clock: Clock | None = None,
) -> PatchApplyResult:
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    items = repository.pending_proposal_items(patch_id, item_ids)
    change_batch_ids: list[str] = []
    for item in items:
        if item["validation_status"] == "invalid":
            raise PatchApplicationError(f"Proposal item {item['id']} is invalid and cannot be accepted")
        compiled = compile_proposal_item(vault, item)
        compiled.apply(vault.root, clock)
        refreshed = load_vault(vault.root)
        sync_vault_state(refreshed, repository, clock=clock)
        now = utc_now_iso(clock)
        change_batch_id = new_ulid()
        repository.record_applied_proposal_item(
            proposal_item_id=item["id"],
            change_batch={
                "id": change_batch_id,
                "reason": "proposal_accept",
                "origin": "codex",
                "summary": compiled.summary,
                "created_at": now,
            },
            content_events=[
                {
                    "id": new_ulid(),
                    "event_type": compiled.event_type,
                    "subject": compiled.subject,
                    "entity_type": compiled.entity_type,
                    "entity_id": compiled.entity_id,
                    "origin": "codex",
                    "review_status": "accepted",
                    "summary": compiled.summary,
                    "created_at": now,
                }
            ],
            clock=clock,
        )
        change_batch_ids.append(change_batch_id)
        vault = refreshed
    return PatchApplyResult(applied_count=len(change_batch_ids), change_batch_ids=change_batch_ids)


def compile_proposal_item(vault: LoadedVault, item: dict[str, Any]) -> CompiledPatch:
    payload = item["edited_payload"] if item.get("edited_payload") is not None else item["payload"]
    operation = item["operation"]
    item_type = item["item_type"]
    if operation == "deactivate":
        return _compile_deactivate(vault, item, payload)
    if operation not in {"create", "update"}:
        raise PatchApplicationError(f"Unsupported proposal operation {operation}")
    if item_type == "concept":
        return _compile_concept(vault, item, payload)
    if item_type == "concept_edge":
        return _compile_concept_edge(vault, item, payload)
    if item_type == "learning_object":
        return _compile_learning_object(vault, item, payload)
    if item_type == "practice_item":
        return _compile_practice_item(vault, item, payload)
    if item_type == "rubric":
        return _compile_rubric(vault, item, payload)
    if item_type == "error_type":
        return _compile_error_type(vault, item, payload)
    raise PatchApplicationError(f"Unsupported proposal item type {item_type}")


def _compile_concept(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch:
    entity_id = _entity_id(item, payload)
    if item["operation"] == "update" and entity_id not in vault.concepts:
        raise PatchApplicationError(f"Cannot update missing concept {entity_id}")
    data = {**payload, "id": entity_id}
    return CompiledPatch(
        proposal_item_id=item["id"],
        entity_type="concept",
        entity_id=entity_id,
        subject=None,
        event_type=_event_type(item["operation"]),
        summary=f"{item['operation']} concept {entity_id}",
        apply=lambda root, clock: upsert_concept(root, entity_id, data, clock=clock),
    )


def _compile_concept_edge(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch:
    source = payload.get("source") or payload.get("source_concept_id")
    target = payload.get("target") or payload.get("target_concept_id")
    if source not in vault.concepts:
        raise PatchApplicationError(f"Concept edge source does not exist: {source}")
    if target not in vault.concepts:
        raise PatchApplicationError(f"Concept edge target does not exist: {target}")
    relation_type = payload.get("relation_type")
    edge_id = _entity_id(item, payload, default=f"edge_{snake_case(str(source))}_{relation_type}_{snake_case(str(target))}")
    if item["operation"] == "update" and all(edge.id != edge_id for edge in vault.edges):
        raise PatchApplicationError(f"Cannot update missing concept edge {edge_id}")
    data = {
        "id": edge_id,
        "source": source,
        "target": target,
        "relation_type": relation_type,
        "strength": payload.get("strength", 1.0),
        "rationale": payload.get("rationale"),
    }
    return CompiledPatch(
        proposal_item_id=item["id"],
        entity_type="concept_edge",
        entity_id=edge_id,
        subject=None,
        event_type=_event_type(item["operation"]),
        summary=f"{item['operation']} concept edge {edge_id}",
        apply=lambda root, clock: upsert_concept_edge(root, data, clock=clock),
    )


def _compile_learning_object(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch:
    entity_id = _entity_id(item, payload)
    existing = vault.learning_objects.get(entity_id)
    if item["operation"] == "update" and existing is None:
        raise PatchApplicationError(f"Cannot update missing Learning Object {entity_id}")
    data = {**payload, "id": entity_id}
    if "concept_id" in data and "concept" not in data:
        data["concept"] = data.pop("concept_id")
    subjects = data.get("subjects") or (existing.subjects if existing else None)
    concept = data.get("concept") or (existing.concept if existing else None)
    if not subjects:
        raise PatchApplicationError(f"Learning Object {entity_id} requires subjects")
    if subjects[0] not in vault.subjects:
        raise PatchApplicationError(f"Learning Object {entity_id} references missing subject {subjects[0]}")
    if concept not in vault.concepts:
        raise PatchApplicationError(f"Learning Object {entity_id} references missing concept {concept}")
    return CompiledPatch(
        proposal_item_id=item["id"],
        entity_type="learning_object",
        entity_id=entity_id,
        subject=subjects[0],
        event_type=_event_type(item["operation"]),
        summary=f"{item['operation']} Learning Object {entity_id}",
        apply=lambda root, clock: upsert_learning_object(root, data, clock=clock),
    )


def _compile_practice_item(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch:
    entity_id = _entity_id(item, payload)
    existing = vault.practice_items.get(entity_id)
    if item["operation"] == "update" and existing is None:
        raise PatchApplicationError(f"Cannot update missing Practice Item {entity_id}")
    data = {**payload, "id": entity_id}
    learning_object_id = data.get("learning_object_id") or (existing.learning_object_id if existing else None)
    if learning_object_id not in vault.learning_objects:
        raise PatchApplicationError(f"Practice Item {entity_id} references missing Learning Object {learning_object_id}")
    learning_object = vault.learning_objects[learning_object_id]
    subjects = data.get("subjects")
    primary_subject = (subjects or learning_object.subjects)[0]
    if primary_subject not in vault.subjects:
        raise PatchApplicationError(f"Practice Item {entity_id} references missing subject {primary_subject}")
    if data.get("grading_rubric") is not None:
        data["grading_rubric"] = _normalize_rubric_payload(data["grading_rubric"])
    return CompiledPatch(
        proposal_item_id=item["id"],
        entity_type="practice_item",
        entity_id=entity_id,
        subject=primary_subject,
        event_type=_event_type(item["operation"]),
        summary=f"{item['operation']} Practice Item {entity_id}",
        apply=lambda root, clock: upsert_practice_item(root, data, clock=clock),
    )


def _compile_rubric(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch:
    practice_item_id = payload.get("target_practice_item_id") or item.get("target_entity_id")
    if practice_item_id not in vault.practice_items:
        raise PatchApplicationError(f"Rubric target Practice Item does not exist: {practice_item_id}")
    practice_item = vault.practice_items[practice_item_id]
    data = practice_item.model_dump(mode="json", exclude_none=False)
    data["grading_rubric"] = _normalize_rubric_payload(payload)
    subject = vault.subjects_for_item(practice_item)[0]
    return CompiledPatch(
        proposal_item_id=item["id"],
        entity_type="rubric",
        entity_id=practice_item_id,
        subject=subject,
        event_type="updated",
        summary=f"update rubric for Practice Item {practice_item_id}",
        apply=lambda root, clock: upsert_practice_item(root, data, clock=clock),
    )


def _compile_error_type(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch:
    entity_id = _entity_id(item, payload)
    if item["operation"] == "update" and entity_id not in vault.error_types:
        raise PatchApplicationError(f"Cannot update missing error type {entity_id}")
    for concept_id in payload.get("related_concepts") or []:
        if concept_id not in vault.concepts:
            raise PatchApplicationError(f"Error type {entity_id} references missing concept {concept_id}")
    data = {**payload, "id": entity_id}
    return CompiledPatch(
        proposal_item_id=item["id"],
        entity_type="error_type",
        entity_id=entity_id,
        subject=None,
        event_type=_event_type(item["operation"]),
        summary=f"{item['operation']} error type {entity_id}",
        apply=lambda root, clock: upsert_error_type(root, data, clock=clock),
    )


def _compile_deactivate(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch:
    entity_id = _entity_id(item, payload)
    if item["item_type"] != "learning_object":
        raise PatchApplicationError(f"Deactivate is only supported for Learning Objects in this slice, not {item['item_type']}")
    existing = vault.learning_objects.get(entity_id)
    if existing is None:
        raise PatchApplicationError(f"Cannot deactivate missing Learning Object {entity_id}")
    data = existing.model_dump(mode="json", exclude_none=False)
    data["status"] = "dormant"
    subject = existing.subjects[0]
    return CompiledPatch(
        proposal_item_id=item["id"],
        entity_type="learning_object",
        entity_id=entity_id,
        subject=subject,
        event_type="deactivated",
        summary=f"deactivate Learning Object {entity_id}",
        apply=lambda root, clock: upsert_learning_object(root, data, clock=clock),
    )


def _normalize_rubric_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "max_points": payload.get("max_points", 4),
        "criteria": payload.get("criteria", []),
        "fatal_errors": payload.get("fatal_errors", []),
    }


def _entity_id(item: dict[str, Any], payload: dict[str, Any], default: str | None = None) -> str:
    entity_id = payload.get("id") or item.get("target_entity_id") or default
    if not entity_id:
        raise PatchApplicationError(f"Proposal item {item['id']} does not identify a target entity")
    return str(entity_id)


def _event_type(operation: str) -> str:
    return {"create": "created", "update": "updated", "deactivate": "deactivated"}[operation]
