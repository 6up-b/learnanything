from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid, snake_case
from learnloop.services.state_sync import sync_vault_state
from learnloop.services.vault_lock import vault_mutation_lock
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import (
    VaultWriterError,
    delete_concept,
    delete_concept_edge,
    upsert_concept,
    upsert_concept_edge,
    upsert_error_type,
    upsert_facet,
    upsert_learning_object,
    upsert_practice_item,
)

# Learnable-map item types whose acceptance requires an mvp-0.7 vault
# (source-ingestion §8.2 / knowledge-model §12.7 feature gate). Applying any of
# these in a legacy vault is refused so no attempts can accrue against a
# partially-upgraded map.
LEARNABLE_MAP_ITEM_TYPES = frozenset({"facet", "task_blueprint"})


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
    """Accept a dependency-closed set of proposal items as one logical transaction.

    Runs under the cross-process vault mutation lock (§8.2), which serializes the
    accept-time lock/target recheck, YAML mutation, derived-state sync, and
    proposal decision. Application itself uses the write-ahead protocol
    (``services.apply_protocol``, §10.2): a durable intent commits to SQLite first,
    YAML is staged/fsynced/atomically renamed, then the intent is marked applied —
    so a crash mid-flight is completed by startup/doctor recovery.
    """

    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    with vault_mutation_lock(vault.root, purpose="proposal_accept"):
        return _apply_accepted_locked(vault, repository, patch_id, item_ids, clock)


def _apply_accepted_locked(
    vault: LoadedVault,
    repository: Repository,
    patch_id: str,
    item_ids: list[str] | None,
    clock: Clock | None,
) -> PatchApplyResult:
    from learnloop.services.apply_protocol import (
        compute_dependency_closure,
        materialize_targets,
        perform_db_effects,
        stage_target_contents,
    )

    requested = repository.pending_proposal_items(patch_id, item_ids)
    for item in requested:
        if item["validation_status"] == "invalid":
            raise PatchApplicationError(f"Proposal item {item['id']} is invalid and cannot be accepted")

    origin = _proposal_origin(repository, patch_id)
    ordered_ids, blocked = compute_dependency_closure(repository, requested)

    # A dependent with a rejected/unaccepted prerequisite is blocked, never
    # partially applied (§10.2). Applyable items are marked ready.
    for item_id, reason in blocked.items():
        repository.set_proposal_item_dependency_status(
            item_id, dependency_status="blocked", block_reason=reason
        )
    for item_id in ordered_ids:
        repository.set_proposal_item_dependency_status(item_id, dependency_status="ready")

    requested_by_id = {item["id"]: item for item in requested}
    ordered_items = [requested_by_id[item_id] for item_id in ordered_ids]

    # Accept-time refusal: an update/deactivate whose target changed after
    # synthesis, or whose identity became locked (e.g. an attempt inserted after
    # synthesis), is refused while holding the mutation lock (§8.2 enforcement 3).
    _accept_time_rechecks(vault, repository, ordered_items)

    if not ordered_items:
        return PatchApplyResult(applied_count=0, change_batch_ids=[])

    targets, db_plan = stage_target_contents(
        vault.root, vault, ordered_items, origin, patch_id, clock=clock
    )
    # 1. Durable intent commits FIRST (closure + target contents/hashes + DB plan).
    intent_id = repository.insert_apply_intent(
        proposed_patch_id=patch_id,
        item_ids=ordered_ids,
        targets=targets,
        db_plan=db_plan,
        clock=clock,
    )
    # 2. Stage/fsync/atomic-rename the YAML into place.
    materialize_targets(vault.root, targets)
    # 3. Derived-state sync + DB side effects, then mark the intent applied.
    sync_vault_state(load_vault(vault.root), repository, clock=clock)
    change_batch_ids = perform_db_effects(repository, db_plan, clock=clock)
    repository.mark_apply_intent_applied(intent_id, clock=clock)
    return PatchApplyResult(applied_count=len(ordered_items), change_batch_ids=change_batch_ids)


def compute_target_hash(vault: LoadedVault, item_type: str, entity_id: str) -> str | None:
    """Content hash of the current on-vault target entity (§8.2 expected_target_hash).

    Synthesis stamps this on every update/deactivate item; acceptance refuses if
    the live target no longer matches — the target changed after synthesis even if
    lock state did not. Returns ``None`` when the entity does not exist (create) or
    the type is not hash-checked.
    """

    entity: Any = None
    if item_type == "learning_object":
        entity = vault.learning_objects.get(entity_id)
    elif item_type == "practice_item":
        entity = vault.practice_items.get(entity_id)
    elif item_type == "concept":
        entity = vault.concepts.get(entity_id)
    elif item_type == "error_type":
        entity = vault.error_types.get(entity_id)
    elif item_type == "rubric":
        item = vault.practice_items.get(entity_id)
        entity = item.grading_rubric if item is not None else None
    if entity is None:
        return None
    payload = entity.model_dump(mode="json", exclude_none=False)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _accept_time_rechecks(
    vault: LoadedVault, repository: Repository, ordered_items: list[dict[str, Any]]
) -> None:
    from learnloop.services.curriculum_locks import Operation, can_apply

    lock_entity_types = {"learning_object", "practice_item", "concept", "rubric"}
    for item in ordered_items:
        payload = item["edited_payload"] if item.get("edited_payload") is not None else item["payload"]
        expected = payload.get("expected_target_hash") if isinstance(payload, dict) else None
        if expected is None:
            continue  # legacy item: no v2 accept-time recheck
        if item["operation"] not in {"update", "deactivate"}:
            continue
        item_type = item["item_type"]
        entity_id = _entity_id(item, payload)
        current = compute_target_hash(vault, item_type, entity_id)
        if current is not None and current != expected:
            raise PatchApplicationError(
                f"Refusing to apply {item_type} {entity_id}: target changed after "
                f"synthesis (expected {expected}, found {current})"
            )
        if item_type in lock_entity_types:
            entity_type = "practice_item" if item_type == "rubric" else item_type
            op_type = "deactivate" if item["operation"] == "deactivate" else "blueprint_identity_change"
            result = can_apply(
                vault,
                repository,
                Operation(op_type=op_type, entity_type=entity_type, entity_id=entity_id),
            )
            if not result.legal:
                detail = "; ".join(reason.detail for reason in result.lock_reasons)
                raise PatchApplicationError(
                    f"Refusing to apply {item_type} {entity_id}: identity is locked "
                    f"({detail})"
                )


def reject_applied_items(
    root: Path,
    patch_id: str,
    item_ids: list[str] | None = None,
    *,
    clock: Clock | None = None,
) -> int:
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    origin = _proposal_origin(repository, patch_id)
    requested = set(item_ids or [])
    items = [
        item
        for item in repository.proposal_items(patch_id)
        if item["decision"] == "accepted"
        and item.get("applied_change_batch_id")
        and (not requested or item["id"] in requested)
    ]
    rejected = 0
    # Reverting an applied item mutates the vault, so it takes the same
    # accept-time critical-section lock as acceptance (§8.2).
    with vault_mutation_lock(vault.root, purpose="proposal_reject"):
        for item in items:
            event = _apply_reject_side_effect(vault, repository, item, origin=origin, clock=clock)
            if event is None:
                raise PatchApplicationError(
                    f"Cannot revert proposal item {item['id']} ({item['item_type']} {item['operation']})"
                )
            if repository.reject_applied_proposal_item(item["id"], content_event=event, clock=clock):
                rejected += 1
                vault = load_vault(root)
    return rejected


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
    if item_type == "facet":
        return _compile_facet(vault, item, payload)
    if item_type == "task_blueprint":
        return _compile_task_blueprint(vault, item, payload)
    raise PatchApplicationError(f"Unsupported proposal item type {item_type}")


def _refuse_learnable_on_legacy(vault: LoadedVault, item_type: str, entity_id: str) -> None:
    """Bootstrap evidence refusal (§8.2 enforcement 2, knowledge-model §12.7).

    A learnable study map (facets/blueprints) may only be applied once the vault
    is at algorithm_version mvp-0.7. In a legacy vault synthesis/preview may run
    but ACCEPTANCE refuses with a typed reason, so no attempts can accrue against
    a partially-upgraded map."""

    if vault.config.algorithms.algorithm_version != "mvp-0.7":
        raise PatchApplicationError(
            f"bootstrap_evidence_refused: cannot apply learnable {item_type} {entity_id} "
            f"in a legacy vault (requires algorithm_version mvp-0.7)"
        )


def _compile_facet(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch:
    entity_id = _entity_id(item, payload)
    _refuse_learnable_on_legacy(vault, "facet", entity_id)
    data = {**payload, "id": entity_id}
    concept_id = data.get("concept_id")
    if concept_id is not None and concept_id not in vault.concepts:
        raise PatchApplicationError(f"Facet {entity_id} references missing concept {concept_id}")
    return CompiledPatch(
        proposal_item_id=item["id"],
        entity_type="facet",
        entity_id=entity_id,
        subject=None,
        event_type=_event_type(item["operation"]),
        summary=f"{item['operation']} facet {entity_id}",
        apply=lambda root, clock: upsert_facet(root, data, clock=clock),
    )


def _compile_task_blueprint(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch:
    blueprint_id = str(payload.get("id") or "")
    if not blueprint_id:
        raise PatchApplicationError(f"Proposal item {item['id']} task_blueprint requires an id")
    _refuse_learnable_on_legacy(vault, "task_blueprint", blueprint_id)
    learning_object_id = payload.get("learning_object_id") or item.get("target_entity_id")
    existing = vault.learning_objects.get(str(learning_object_id))
    if existing is None:
        raise PatchApplicationError(
            f"task_blueprint {blueprint_id} references missing Learning Object {learning_object_id}"
        )
    data = existing.model_dump(mode="json", exclude_none=False)
    blueprint = {
        "id": blueprint_id,
        "weight": payload.get("weight", 1.0),
        "recipes": payload.get("recipes") or [],
    }
    blueprints = [dict(bp) for bp in (data.get("blueprints") or []) if bp.get("id") != blueprint_id]
    blueprints.append(blueprint)
    data["blueprints"] = blueprints
    subject = existing.subjects[0]
    return CompiledPatch(
        proposal_item_id=item["id"],
        entity_type="task_blueprint",
        entity_id=blueprint_id,
        subject=subject,
        event_type=_event_type(item["operation"]),
        summary=f"{item['operation']} task blueprint {blueprint_id} on {learning_object_id}",
        apply=lambda root, clock: upsert_learning_object(root, data, clock=clock),
    )


def _proposal_apply_order(item: dict[str, Any]) -> tuple[int, int, str]:
    operation_order = {"create": 0, "update": 1, "deactivate": 2}
    type_order = {
        "concept": 0,
        "error_type": 1,
        "facet": 2,
        "learning_object": 3,
        "task_blueprint": 4,
        "practice_item": 5,
        "rubric": 6,
        "concept_edge": 7,
    }
    return (
        operation_order.get(str(item.get("operation")), 9),
        type_order.get(str(item.get("item_type")), 9),
        str(item.get("client_item_id") or item.get("id") or ""),
    )


def _proposal_origin(repository: Repository, patch_id: str) -> str:
    batch = repository.proposal_batch(patch_id)
    if batch is None:
        return "codex"
    run = repository.agent_run(batch["agent_run_id"])
    provider = (run or {}).get("provider")
    if provider == "codex":
        return "codex"
    if provider == "import":
        return "system"
    return "ai"


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
    edge_id = _entity_id(
        item,
        payload,
        default=_default_edge_id(payload),
    )
    existing = _edge_by_id(vault, edge_id)
    if item["operation"] == "update" and existing is None:
        raise PatchApplicationError(f"Cannot update missing concept edge {edge_id}")
    source = payload.get("source") or payload.get("source_concept_id") or (existing.source if existing else None)
    target = payload.get("target") or payload.get("target_concept_id") or (existing.target if existing else None)
    if source not in vault.concepts:
        raise PatchApplicationError(f"Concept edge source does not exist: {source}")
    if target not in vault.concepts:
        raise PatchApplicationError(f"Concept edge target does not exist: {target}")
    relation_type = payload.get("relation_type") or (existing.relation_type if existing else None)
    data = {
        "id": edge_id,
        "source": source,
        "target": target,
        "relation_type": relation_type,
        "strength": payload.get("strength", existing.strength if existing else 1.0),
        "rationale": payload.get("rationale", existing.rationale if existing else None),
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
    data = existing.model_dump(mode="json", exclude_none=False) if existing is not None else {}
    data.update(payload)
    data["id"] = entity_id
    if "concept_id" in data:
        data["concept"] = data.pop("concept_id")
    subjects = data.get("subjects") or (existing.subjects if existing else None)
    concept = data.get("concept") or (existing.concept if existing else None)
    if not subjects:
        raise PatchApplicationError(f"Learning Object {entity_id} requires subjects")
    if subjects[0] not in vault.subjects:
        raise PatchApplicationError(f"Learning Object {entity_id} references missing subject {subjects[0]}")
    auto_concept = concept not in vault.concepts
    return CompiledPatch(
        proposal_item_id=item["id"],
        entity_type="learning_object",
        entity_id=entity_id,
        subject=subjects[0],
        event_type=_event_type(item["operation"]),
        summary=f"{item['operation']} Learning Object {entity_id}",
        apply=lambda root, clock: _upsert_learning_object_with_concept(
            root,
            data,
            auto_create_concept=auto_concept,
            clock=clock,
        ),
    )


def _upsert_learning_object_with_concept(
    root: Path,
    data: dict[str, Any],
    *,
    auto_create_concept: bool,
    clock: Clock | None,
) -> Path:
    if auto_create_concept:
        concept_id = str(data["concept"])
        upsert_concept(root, concept_id, _concept_from_learning_object(data), clock=clock)
    return upsert_learning_object(root, data, clock=clock)


def _concept_from_learning_object(data: dict[str, Any]) -> dict[str, Any]:
    knowledge_type = str(data.get("knowledge_type") or "").lower()
    if "skill" in knowledge_type:
        concept_type = "skill"
    elif "procedure" in knowledge_type:
        concept_type = "procedure"
    else:
        concept_type = "concept"
    tags: list[str] = []
    for value in [*(data.get("subjects") or []), *(data.get("tags") or [])]:
        if value not in tags:
            tags.append(value)
    return {
        "title": data.get("title") or str(data["concept"]),
        "type": concept_type,
        "aliases": [],
        "description": data.get("summary"),
        "tags": tags,
    }


def _compile_practice_item(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch:
    entity_id = _entity_id(item, payload)
    existing = vault.practice_items.get(entity_id)
    if item["operation"] == "update" and existing is None:
        raise PatchApplicationError(f"Cannot update missing Practice Item {entity_id}")
    data = existing.model_dump(mode="json", exclude_none=False) if existing is not None else {}
    data.update(payload)
    data["id"] = entity_id
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
    _reject_unregistered_facets(vault, entity_id, data)
    return CompiledPatch(
        proposal_item_id=item["id"],
        entity_type="practice_item",
        entity_id=entity_id,
        subject=primary_subject,
        event_type=_event_type(item["operation"]),
        summary=f"{item['operation']} Practice Item {entity_id}",
        apply=lambda root, clock: upsert_practice_item(root, data, clock=clock),
    )


def _reject_unregistered_facets(vault: LoadedVault, entity_id: str, data: dict[str, Any]) -> None:
    """Generated-item facet gate (knowledge-model §3.2, mirrors the probe gate).

    On mvp-0.7 vaults a newly generated item MUST reference registered canonical
    facets; an unregistered facet id is rejected. Legacy vaults keep today's
    lenient behavior (doctor warns instead), so frozen content is untouched.
    """

    if vault.config.algorithms.algorithm_version != "mvp-0.7":
        return
    if not vault.evidence_facets:
        return
    from learnloop.services.capability_mapping import unregistered_facet_errors

    facet_ids = [vault.canonical_facet_id(str(facet)) for facet in data.get("evidence_facets") or []]
    errors = unregistered_facet_errors(set(vault.evidence_facets), facet_ids)
    if errors:
        raise PatchApplicationError(
            f"Practice Item {entity_id} references {'; '.join(errors)}"
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


def _apply_reject_side_effect(
    vault: LoadedVault,
    repository: Repository,
    item: dict[str, Any],
    *,
    origin: str,
    clock: Clock | None,
) -> dict[str, Any] | None:
    if item["operation"] != "create":
        return None
    payload = item["edited_payload"] if item.get("edited_payload") is not None else item["payload"]
    entity_id = _entity_id(item, payload, default=_default_edge_id(payload) if item["item_type"] == "concept_edge" else None)
    now = utc_now_iso(clock)
    if item["item_type"] == "learning_object":
        existing = vault.learning_objects.get(entity_id)
        if existing is None:
            return None
        data = existing.model_dump(mode="json", exclude_none=False)
        data["status"] = "dormant"
        upsert_learning_object(vault.root, data, clock=clock)
        sync_vault_state(load_vault(vault.root), repository, clock=clock)
        subject = existing.subjects[0] if existing.subjects else None
        summary = f"reject auto-applied Learning Object {entity_id}"
        entity_type = "learning_object"
    elif item["item_type"] == "practice_item":
        existing = vault.practice_items.get(entity_id)
        if existing is None:
            return None
        state = repository.practice_item_state(entity_id)
        repository.upsert_practice_item_state(
            entity_id,
            difficulty=state.difficulty if state else None,
            stability=state.stability if state else None,
            retrievability=state.retrievability if state else None,
            due_at=state.due_at if state else None,
            active=False,
            content_hash=state.content_hash if state else None,
            last_attempt_at=state.last_attempt_at if state else None,
            clock=clock,
        )
        subject = vault.subjects_for_item(existing)[0] if vault.subjects_for_item(existing) else None
        summary = f"reject auto-applied Practice Item {entity_id}"
        entity_type = "practice_item"
    elif item["item_type"] == "concept":
        existing = vault.concepts.get(entity_id)
        if existing is None:
            return None
        blockers = _concept_revert_blockers(vault, entity_id)
        if blockers:
            joined = ", ".join(blockers[:8])
            suffix = "" if len(blockers) <= 8 else f", and {len(blockers) - 8} more"
            raise PatchApplicationError(
                f"Cannot revert created concept {entity_id}; it is still referenced by {joined}{suffix}."
            )
        delete_concept(vault.root, entity_id)
        sync_vault_state(load_vault(vault.root), repository, clock=clock)
        subject = None
        summary = f"reject created concept {entity_id}"
        entity_type = "concept"
    elif item["item_type"] == "concept_edge":
        existing = _edge_by_id(vault, entity_id)
        if existing is None:
            return None
        delete_concept_edge(vault.root, entity_id)
        sync_vault_state(load_vault(vault.root), repository, clock=clock)
        subject = None
        summary = f"reject created concept edge {entity_id}"
        entity_type = "concept_edge"
    else:
        return None
    return {
        "id": new_ulid(),
        "event_type": "deactivated",
        "subject": subject,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "origin": origin,
        "review_status": "rejected",
        "summary": summary,
        "created_at": now,
    }


def _concept_revert_blockers(vault: LoadedVault, concept_id: str) -> list[str]:
    blockers: list[str] = []
    for learning_object in vault.learning_objects.values():
        if learning_object.concept == concept_id:
            blockers.append(f"learning_object:{learning_object.id}.concept")
        if concept_id in learning_object.prerequisites:
            blockers.append(f"learning_object:{learning_object.id}.prerequisites")
        if concept_id in learning_object.confusables:
            blockers.append(f"learning_object:{learning_object.id}.confusables")
    for edge in vault.edges:
        if edge.source == concept_id or edge.target == concept_id:
            blockers.append(f"concept_edge:{edge.id}")
    for goal in vault.goals:
        if concept_id in goal.facet_scope.concepts:
            blockers.append(f"goal:{goal.id}.facet_scope.concepts")
    for error_type in vault.error_types.values():
        if concept_id in error_type.related_concepts:
            blockers.append(f"error_type:{error_type.id}.related_concepts")
    for note in vault.notes.values():
        if concept_id in note.related_concepts:
            blockers.append(f"note:{note.id}.related_concepts")
    for subject in vault.subjects.values():
        graph = subject.graph
        if concept_id in graph.additional_concepts_in_scope:
            blockers.append(f"subject:{subject.metadata.id}.additional_concepts_in_scope")
        if concept_id in graph.exclude_concepts:
            blockers.append(f"subject:{subject.metadata.id}.exclude_concepts")
        if concept_id in graph.subject_ordering_hints:
            blockers.append(f"subject:{subject.metadata.id}.subject_ordering_hints")
    return sorted(blockers)


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


def _default_edge_id(payload: dict[str, Any]) -> str | None:
    source = payload.get("source") or payload.get("source_concept_id")
    target = payload.get("target") or payload.get("target_concept_id")
    relation_type = payload.get("relation_type")
    if source is None or target is None or relation_type is None:
        return None
    return f"edge_{snake_case(str(source))}_{relation_type}_{snake_case(str(target))}"


def _edge_by_id(vault: LoadedVault, edge_id: str) -> Any | None:
    for edge in vault.edges:
        if edge.id == edge_id:
            return edge
    return None


def _event_type(operation: str) -> str:
    return {"create": "created", "update": "updated", "deactivate": "deactivated"}[operation]
