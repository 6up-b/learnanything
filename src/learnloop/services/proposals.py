from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.codex.client import AuthoringContext, CodexClient, CodexUnavailable
from learnloop.codex.prompts import AUTHORING_PROMPT_VERSION
from learnloop.codex.schemas import AuthoringProposal, AuthoringProposalItem, SourceRef
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.patches import PatchApplyResult, apply_accepted_items
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths


def list_proposals(root: Path) -> list[dict]:
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    return repository.proposal_batches()


def _excerpt(text: str, limit: int = 280) -> str:
    collapsed = " ".join(text.split())
    return collapsed[:limit]


def build_authoring_context(
    vault: LoadedVault,
    *,
    subjects: list[str] | None = None,
    note_ids: list[str] | None = None,
    source_refs: list[dict] | None = None,
    instructions: str | None = None,
) -> AuthoringContext:
    """Assemble a deterministic authoring context from selected vault sources.

    Pure and Codex-free: the same vault state and selection produce the same
    context. Notes are filtered by id or by subject membership, and only short
    excerpts/locators are included to avoid overloading the model.
    """

    selected_subjects = sorted(subjects) if subjects else sorted(vault.subjects)
    subject_set = set(selected_subjects)

    notes: list[dict] = []
    for note in vault.notes.values():
        if note_ids is not None:
            if note.id not in note_ids:
                continue
        elif subjects is not None and not (set(note.subjects) & subject_set):
            continue
        notes.append(
            {
                "id": note.id,
                "path": note.path,
                "source_type": note.source_type,
                "excerpt": _excerpt(note.body),
            }
        )
    notes.sort(key=lambda entry: entry["id"])

    def _in_scope(item_subjects: list[str]) -> bool:
        if subjects is None:
            return True
        return bool(set(item_subjects) & subject_set)

    learning_objects = [
        {"id": lo.id, "title": lo.title, "concept": lo.concept, "subjects": lo.subjects}
        for lo in sorted(vault.learning_objects.values(), key=lambda lo: lo.id)
        if _in_scope(lo.subjects)
    ]
    practice_items = [
        {"id": item.id, "learning_object_id": item.learning_object_id, "prompt": _excerpt(item.prompt, 120)}
        for item in sorted(vault.practice_items.values(), key=lambda item: item.id)
        if _in_scope(vault.subjects_for_item(item))
    ]
    concepts = [
        {"id": concept_id, "title": concept.title}
        for concept_id, concept in sorted(vault.concepts.items())
    ]
    goals = [
        {"id": goal.id, "title": goal.title, "concept_anchors": goal.concept_anchors}
        for goal in vault.goals
        if goal.status == "active"
    ]

    resolved_refs = list(source_refs or [])
    source_ids = sorted({note["id"] for note in notes} | {str(ref.get("ref_id")) for ref in resolved_refs})

    return AuthoringContext(
        vault_root=str(vault.root),
        source_ids=source_ids,
        instructions=instructions,
        subjects=selected_subjects,
        source_refs=resolved_refs,
        concepts=concepts,
        notes=notes,
        learning_objects=learning_objects,
        practice_items=practice_items,
        goals=goals,
    )


def authoring_context_hash(context: AuthoringContext) -> str:
    payload = {
        "vault_root": context.vault_root,
        "source_ids": context.source_ids,
        "instructions": context.instructions,
        "subjects": context.subjects,
        "source_refs": context.source_refs,
        "concepts": context.concepts,
        "notes": context.notes,
        "learning_objects": context.learning_objects,
        "practice_items": context.practice_items,
        "goals": context.goals,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def evaluate_review_policy(
    item: AuthoringProposalItem,
    vault: LoadedVault,
    *,
    source_refs: list[SourceRef] | None = None,
) -> str:
    """Resolve an item's effective review route under the auto-apply-low-risk policy.

    Returns one of ``auto_apply``, ``review_required``, or ``reject``. Auto-apply
    is only returned for direct, source-grounded creation of Learning Objects /
    Practice Items with resolvable source refs and no id collision.
    """

    if item.review_route == "reject":
        return "reject"
    if source_refs is not None and _unresolved_source_ref_ids(vault, source_refs, item.source_ref_ids):
        return "reject"
    if item.operation != "create" or item.item_type not in {"learning_object", "practice_item"}:
        return "review_required"
    if not item.source_ref_ids:
        return "review_required"
    if source_refs is not None and not _has_direct_grounding(source_refs, item.source_ref_ids):
        return "review_required"
    if _has_id_collision(item, vault):
        return "review_required"
    if item.review_route == "auto_apply":
        return "auto_apply"
    return "review_required"


def _has_id_collision(item: AuthoringProposalItem, vault: LoadedVault) -> bool:
    candidate_id = item.proposed_entity_id or getattr(item.payload, "id", None)
    if candidate_id is None:
        return False
    if item.item_type == "learning_object":
        return candidate_id in vault.learning_objects
    if item.item_type == "practice_item":
        return candidate_id in vault.practice_items
    return False


def generate_authoring_proposal(
    root: Path,
    codex_client: CodexClient,
    *,
    subjects: list[str] | None = None,
    note_ids: list[str] | None = None,
    instructions: str | None = None,
    model: str | None = None,
    codex_revision: str | None = None,
    clock: Clock | None = None,
) -> str:
    """Run authoring generation through a CodexClient and persist the result.

    The agent run is recorded before the call and completed/failed afterwards so
    every persisted proposal batch has agent-run lineage.
    """

    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    context = build_authoring_context(
        vault, subjects=subjects, note_ids=note_ids, instructions=instructions
    )
    now = utc_now_iso(clock)
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": "authoring",
            "model": model,
            "provider": "codex",
            "prompt_template": "authoring",
            "prompt_version": AUTHORING_PROMPT_VERSION,
            "codex_revision": codex_revision,
            "input_context_hash": authoring_context_hash(context),
            "output_schema": "AuthoringProposal",
            "started_at": now,
            "status": "running",
        }
    )
    try:
        proposal = codex_client.run_authoring_proposal(context)
    except (CodexUnavailable, TimeoutError, ValueError) as exc:
        repository.complete_agent_run(agent_run_id, status="failed", error_message=str(exc), clock=clock)
        raise
    repository.complete_agent_run(agent_run_id, status="completed", clock=clock)
    proposal_payload = proposal.model_dump(mode="json", exclude_none=False)
    rows = [
        _proposal_item_row(item, now, vault=vault, proposal=proposal, provider="codex")
        for item in proposal.items
    ]
    patch_id = repository.persist_proposal_batch(
        {
            "id": new_ulid(),
            "agent_run_id": agent_run_id,
            "purpose": "authoring",
            "source_refs": proposal_payload["source_refs"],
            "summary": proposal.summary,
            "created_at": now,
            "updated_at": now,
        },
        rows,
    )
    _auto_apply_rows(root, patch_id, rows)
    return patch_id


def persist_authoring_proposal(
    root: Path,
    proposal: AuthoringProposal,
    *,
    provider: str = "import",
    model: str | None = None,
    clock: Clock | None = None,
) -> str:
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    now = utc_now_iso(clock)
    proposal_payload = proposal.model_dump(mode="json", exclude_none=False)
    context_hash = hashlib.sha256(
        json.dumps(proposal_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": "authoring",
            "model": model,
            "provider": provider,
            "prompt_template": "authoring",
            "prompt_version": AUTHORING_PROMPT_VERSION,
            "input_context_hash": context_hash,
            "output_schema": "AuthoringProposal",
            "started_at": now,
            "completed_at": now,
            "status": "completed",
        }
    )
    rows = [
        _proposal_item_row(item, now, vault=vault, proposal=proposal, provider=provider)
        for item in proposal.items
    ]
    patch_id = repository.persist_proposal_batch(
        {
            "id": new_ulid(),
            "agent_run_id": agent_run_id,
            "purpose": "authoring",
            "source_refs": proposal_payload["source_refs"],
            "summary": proposal.summary,
            "created_at": now,
            "updated_at": now,
        },
        rows,
    )
    _auto_apply_rows(root, patch_id, rows)
    return patch_id


def reject_items(root: Path, patch_id: str, item_ids: list[str] | None = None) -> int:
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    return repository.set_proposal_item_decision(patch_id, "rejected", item_ids)


def edit_proposal_item(
    root: Path,
    patch_id: str,
    item_id: str,
    edited_payload: dict[str, Any],
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    item = repository.proposal_item(item_id)
    if item is None or item["proposed_patch_id"] != patch_id:
        raise ValueError(f"Proposal item {item_id} was not found in proposal {patch_id}")
    if item["decision"] != "pending":
        raise ValueError(f"Proposal item {item_id} is already {item['decision']}")

    validation_errors = _edited_payload_validation_errors(item, edited_payload, vault)
    validation_status = "invalid" if validation_errors else "valid"
    updated = repository.update_proposal_item_edited_payload(
        item_id,
        edited_payload=edited_payload,
        validation_status=validation_status,
        validation_errors=validation_errors,
        clock=clock,
    )
    if not updated:
        raise ValueError(f"Proposal item {item_id} could not be edited")
    refreshed = repository.proposal_item(item_id)
    if refreshed is None:
        raise ValueError(f"Proposal item {item_id} disappeared after edit")
    return refreshed


def accept_items(root: Path, patch_id: str, item_ids: list[str] | None = None) -> PatchApplyResult:
    return apply_accepted_items(root, patch_id, item_ids)


def _proposal_item_row(
    item: AuthoringProposalItem,
    now: str,
    *,
    vault: LoadedVault,
    proposal: AuthoringProposal,
    provider: str,
) -> dict:
    payload = item.payload.model_dump(mode="json", exclude_none=True)
    if payload.get("id") is None and item.proposed_entity_id is not None:
        payload["id"] = item.proposed_entity_id
    selected_refs = _source_refs_for_item(proposal.source_refs, item.source_ref_ids)
    if item.item_type in {"learning_object", "practice_item"} and selected_refs:
        payload.setdefault("provenance", _provenance_for_refs(selected_refs, provider))

    validation_errors = _validation_errors(item, vault, proposal.source_refs)
    validation_status = "invalid" if validation_errors else "valid"
    review_policy = evaluate_review_policy(item, vault, source_refs=proposal.source_refs)
    return {
        "id": new_ulid(),
        "client_item_id": item.client_item_id,
        "item_type": item.item_type,
        "operation": item.operation,
        "target_entity_type": item.target.entity_type if item.target else None,
        "target_entity_id": item.target.entity_id if item.target else None,
        "payload": payload,
        "decision": "pending",
        "validation_status": validation_status,
        "validation_errors": validation_errors,
        "created_at": now,
        "updated_at": now,
        "_auto_apply": validation_status == "valid" and review_policy == "auto_apply",
    }


def _auto_apply_rows(root: Path, patch_id: str, rows: list[dict[str, Any]]) -> None:
    auto_rows = [row for row in rows if row.get("_auto_apply")]
    auto_rows.sort(key=lambda row: (0 if row["item_type"] == "learning_object" else 1, row["client_item_id"]))
    for row in auto_rows:
        accept_items(root, patch_id, [row["id"]])


def _source_refs_for_item(source_refs: list[SourceRef], source_ref_ids: list[str]) -> list[dict[str, Any]]:
    by_id = {source.ref_id: source for source in source_refs}
    return [
        by_id[ref_id].model_dump(mode="json", exclude_none=True)
        for ref_id in source_ref_ids
        if ref_id in by_id
    ]


def _provenance_for_refs(source_refs: list[dict[str, Any]], provider: str) -> dict[str, Any]:
    origin = "codex_proposal"
    if provider == "import":
        origin = "import"
    if any(source.get("ref_type") == "canonical_source" for source in source_refs):
        origin = "canonical_extract"
    return {"origin": origin, "source_refs": source_refs}


def _has_direct_grounding(source_refs: list[SourceRef], source_ref_ids: list[str]) -> bool:
    by_id = {source.ref_id: source for source in source_refs}
    selected = [by_id[ref_id] for ref_id in source_ref_ids if ref_id in by_id]
    return bool(selected) and all(source.ref_type in {"note", "canonical_source"} for source in selected)


def _validation_errors(
    item: AuthoringProposalItem,
    vault: LoadedVault,
    source_refs: list[SourceRef],
) -> list[str]:
    errors: list[str] = []
    if item.review_route == "reject":
        errors.append("review_route=reject")
    for ref_id in _unresolved_source_ref_ids(vault, source_refs, item.source_ref_ids):
        errors.append(f"unresolved_source_ref:{ref_id}")
    if item.operation == "create" and _has_id_collision(item, vault):
        errors.append(f"duplicate_id:{item.proposed_entity_id or getattr(item.payload, 'id', None)}")
    return errors


def _edited_payload_validation_errors(
    item: dict[str, Any],
    edited_payload: dict[str, Any],
    vault: LoadedVault,
) -> list[str]:
    errors = [
        error for error in item.get("validation_errors", []) if not str(error).startswith("duplicate_id:")
    ]
    if item["operation"] == "create":
        entity_id = edited_payload.get("id") or item.get("target_entity_id")
        if item["item_type"] == "learning_object" and entity_id in vault.learning_objects:
            errors.append(f"duplicate_id:{entity_id}")
        elif item["item_type"] == "practice_item" and entity_id in vault.practice_items:
            errors.append(f"duplicate_id:{entity_id}")
    return errors


def _unresolved_source_ref_ids(
    vault: LoadedVault,
    source_refs: list[SourceRef],
    source_ref_ids: list[str],
) -> list[str]:
    by_id = {source.ref_id: source for source in source_refs}
    unresolved: list[str] = []
    for ref_id in source_ref_ids:
        source = by_id.get(ref_id)
        if source is None or not _source_ref_resolves(vault, source):
            unresolved.append(ref_id)
    return unresolved


def _source_ref_resolves(vault: LoadedVault, source: SourceRef) -> bool:
    if source.ref_type == "manual_context":
        return True
    if source.ref_type == "session":
        return bool(source.ref_id)
    if source.ref_type == "note":
        note = vault.notes.get(source.ref_id)
        return note is not None and _path_matches(source.path, note.path)
    if source.ref_type == "canonical_source":
        note = vault.notes.get(source.ref_id)
        if note is not None:
            return note.source_type == "canonical_source" and _path_matches(source.path, note.path)
        if source.path is None:
            return False
        try:
            candidate = (vault.root / source.path).resolve()
            return vault.root.resolve() in (candidate, *candidate.parents) and candidate.is_file()
        except OSError:
            return False
    if source.ref_type == "existing_entity":
        return (
            source.ref_id in vault.learning_objects
            or source.ref_id in vault.practice_items
            or source.ref_id in vault.concepts
            or source.ref_id in vault.error_types
            or source.ref_id in vault.notes
            or source.ref_id in vault.subjects
            or any(edge.id == source.ref_id for edge in vault.edges)
        )
    return False


def _path_matches(source_path: str | None, note_path: str | None) -> bool:
    return source_path is None or note_path is None or source_path == note_path
