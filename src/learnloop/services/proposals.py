from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from math import ceil
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from learnloop.attempt_types import unsupported_attempt_types
from learnloop.ai.client import AIProviderClient
from learnloop.clock import Clock, utc_now_iso
from learnloop.codex.client import AuthoringContext, CodexClient, CodexUnavailable
from learnloop.codex.client import _authoring_prompt, _codex_output_schema
from learnloop.codex.prompts import AUTHORING_PROMPT_VERSION
from learnloop.codex.schemas import AuthoringProposal, AuthoringProposalItem, SourceRef
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.patches import PatchApplyResult, apply_accepted_items, reject_applied_items
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault, PracticeItem
from learnloop.vault.paths import VaultPaths


def list_proposals(root: Path) -> list[dict]:
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    batches = repository.proposal_batches()
    for batch in batches:
        batch["items"] = repository.proposal_items(batch["id"])
    return batches


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


def authoring_context_stats(context: AuthoringContext) -> dict[str, Any]:
    context_payload = asdict(context)
    context_json = json.dumps(context_payload, sort_keys=True, ensure_ascii=False)
    prompt = _authoring_prompt(context)
    schema_json = json.dumps(_codex_output_schema(AuthoringProposal), sort_keys=True, ensure_ascii=False)
    total_chars = len(prompt) + len(schema_json)
    sections = {
        "source_refs": context.source_refs,
        "concepts": context.concepts,
        "notes": context.notes,
        "learning_objects": context.learning_objects,
        "practice_items": context.practice_items,
        "goals": context.goals,
    }
    return {
        "counts": {
            "subjects": len(context.subjects),
            "source_refs": len(context.source_refs),
            "concepts": len(context.concepts),
            "notes": len(context.notes),
            "learning_objects": len(context.learning_objects),
            "practice_items": len(context.practice_items),
            "goals": len(context.goals),
        },
        "chars": {
            "context": len(context_json),
            "prompt": len(prompt),
            "output_schema": len(schema_json),
            "prompt_plus_schema": total_chars,
            "sections": {
                name: len(json.dumps(value, sort_keys=True, ensure_ascii=False))
                for name, value in sections.items()
            },
        },
        "approx_tokens": {
            "prompt_plus_schema": ceil(total_chars / 4),
        },
    }


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
    if item.operation != "create" or item.item_type not in {"learning_object", "practice_item", "concept_edge"}:
        return "review_required"
    if not item.source_ref_ids:
        return "review_required"
    if source_refs is not None and not _has_direct_grounding(source_refs, item.source_ref_ids):
        return "review_required"
    if _has_id_collision(item, vault):
        return "review_required"
    if _generated_practice_audit_error(item) is not None:
        return "review_required"
    if item.review_route == "auto_apply":
        return "auto_apply"
    return "review_required"


def _has_id_collision(item: AuthoringProposalItem, vault: LoadedVault) -> bool:
    candidate_id = item.proposed_entity_id or getattr(item.payload, "id", None)
    if candidate_id is None and item.item_type == "concept_edge":
        payload = item.payload.model_dump(mode="json", exclude_none=True)
        candidate_id = _default_edge_id(payload)
    if candidate_id is None:
        return False
    if item.item_type == "learning_object":
        return candidate_id in vault.learning_objects
    if item.item_type == "practice_item":
        return candidate_id in vault.practice_items
    if item.item_type == "concept_edge":
        return any(edge.id == candidate_id for edge in vault.edges)
    return False


def generate_authoring_proposal(
    root: Path,
    codex_client: CodexClient | AIProviderClient,
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
    provider_fields = _agent_provider_fields(codex_client, model=model, provider_revision=codex_revision)
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": "authoring",
            **provider_fields,
            "prompt_template": "authoring",
            "prompt_version": AUTHORING_PROMPT_VERSION,
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
        _proposal_item_row(item, now, vault=vault, proposal=proposal, provider=provider_fields["provider"] or "codex")
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


def _agent_provider_fields(
    client: CodexClient | AIProviderClient,
    *,
    model: str | None,
    provider_revision: str | None,
) -> dict[str, str | None]:
    provider = getattr(client, "provider_name", None) or "codex"
    provider_type = getattr(client, "provider_type", None)
    resolved_model = model or getattr(client, "model", None)
    fields = {
        "model": resolved_model,
        "provider": provider,
        "provider_type": provider_type,
        "provider_revision": provider_revision,
    }
    if provider == "codex" or provider_type == "codex_sdk":
        fields["codex_revision"] = provider_revision
    return fields


def maybe_promote_self_tagged_fatal_error(
    vault: LoadedVault,
    repository: Repository,
    *,
    item: PracticeItem,
    error_type: str | None,
    clock: Clock | None = None,
) -> str | None:
    """Queue a reviewed proposal to add a repeatedly self-tagged misconception ``E`` to
    an item's rubric ``fatal_errors`` (spec §12.4 — durable-probe promotion).

    Promotion is **independent of the per-attempt trust weight ``w``**: cross-attempt
    repetition is the only N=1-safe signal that the item *reliably* reveals ``E`` (same
    philosophy as §3 / §7.4). It fires exactly once, when the per-``(item, E)`` self-tag
    count reaches ``probe.self_tag.promotion_threshold``; the proposal is always
    ``review_required`` (never auto-applied) — the review gate guards against a learner
    talking themselves into a misconception. Returns the patch id when queued, else None.
    """

    if not error_type:
        return None
    error = vault.error_types.get(error_type)
    if error is None or not error.is_misconception:
        return None
    rubric = vault.rubric_for_item(item)
    if rubric is None:
        return None
    if any(fatal_error.id == error_type for fatal_error in rubric.fatal_errors):
        return None  # already a rubric-asserted probe of E

    threshold = vault.config.probe.self_tag.promotion_threshold
    if repository.count_attempts_with_error_type(item.id, error_type) < threshold:
        return None

    client_item_id = f"self_tag_promotion:{item.id}:{error_type}"
    if repository.proposal_items_by_client_id(client_item_id):
        return None  # already proposed (pending/accepted/rejected) — fire once

    now = utc_now_iso(clock)
    fatal_errors = [fatal_error.model_dump(mode="json", exclude_none=True) for fatal_error in rubric.fatal_errors]
    fatal_errors.append(
        {
            "id": error_type,
            "description": f"Learner repeatedly self-attributed {error.title} on this item.",
            "max_grade": 1,
        }
    )
    rubric_payload = {
        "target_practice_item_id": item.id,
        "max_points": rubric.max_points,
        "criteria": [criterion.model_dump(mode="json", exclude_none=True) for criterion in rubric.criteria],
        "fatal_errors": fatal_errors,
    }
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": "self_tag_promotion",
            "provider": "self",
            "prompt_template": "self_tag_promotion",
            "started_at": now,
            "completed_at": now,
            "status": "completed",
        }
    )
    return repository.persist_proposal_batch(
        {
            "id": new_ulid(),
            "agent_run_id": agent_run_id,
            "purpose": "self_tag_promotion",
            "source_refs": [],
            "summary": f"Promote self-attributed {error_type} to a fatal error on {item.id}.",
            "created_at": now,
            "updated_at": now,
        },
        [
            {
                "id": new_ulid(),
                "client_item_id": client_item_id,
                "item_type": "rubric",
                "operation": "update",
                "target_entity_type": "rubric",
                "target_entity_id": item.id,
                "payload": rubric_payload,
                "decision": "pending",
                "validation_status": "valid",
                "validation_errors": [],
                "created_at": now,
                "updated_at": now,
            }
        ],
    )


def reject_items(root: Path, patch_id: str, item_ids: list[str] | None = None) -> int:
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    applied_count = reject_applied_items(root, patch_id, item_ids)
    pending_count = repository.set_proposal_item_decision(patch_id, "rejected", item_ids)
    return applied_count + pending_count


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

    batch = repository.proposal_batch(patch_id)
    validation_errors = _edited_payload_validation_errors(
        item,
        edited_payload,
        vault,
        batch_source_refs=batch.get("source_refs") if batch is not None else None,
    )
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


def refresh_proposal_item_validation(
    root: Path,
    patch_id: str,
    item_id: str,
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

    payload = item.get("edited_payload") if item.get("edited_payload") is not None else item.get("payload")
    payload = payload if isinstance(payload, dict) else {}
    batch = repository.proposal_batch(patch_id)
    validation_errors = _edited_payload_validation_errors(
        item,
        payload,
        vault,
        batch_source_refs=batch.get("source_refs") if batch is not None else None,
    )
    validation_status = "invalid" if validation_errors else "valid"
    updated = repository.update_proposal_item_validation(
        item_id,
        validation_status=validation_status,
        validation_errors=validation_errors,
        clock=clock,
    )
    if not updated:
        raise ValueError(f"Proposal item {item_id} could not be refreshed")
    refreshed = repository.proposal_item(item_id)
    if refreshed is None:
        raise ValueError(f"Proposal item {item_id} disappeared after refresh")
    return refreshed


def delete_proposal_item(root: Path, patch_id: str, item_id: str) -> bool:
    """Permanently remove a single proposal item from the inbox.

    Hard delete (distinct from :func:`reject_items`, which keeps the row and is
    reversible). If the item was already applied to the vault, its change is
    reverted first via :func:`reject_applied_items` so the on-disk state never
    desyncs from a row that no longer exists.
    """

    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    item = repository.proposal_item(item_id)
    if item is None or item["proposed_patch_id"] != patch_id:
        raise ValueError(f"Proposal item {item_id} was not found in proposal {patch_id}")
    if item.get("applied_change_batch_id") is not None:
        reject_applied_items(root, patch_id, [item_id])
    return repository.delete_proposal_item(item_id)


def accept_items(root: Path, patch_id: str, item_ids: list[str] | None = None) -> PatchApplyResult:
    return apply_accepted_items(root, patch_id, item_ids)


def reset_items(
    root: Path,
    patch_id: str,
    item_ids: list[str] | None = None,
    *,
    clock: Clock | None = None,
) -> int:
    """Undo a decision: send rejected-but-never-applied items back to ``pending``.

    The repository enforces the safety scope (see
    :meth:`Repository.reset_proposal_item_decision`) — applied items are left alone,
    so undo can never desync the inbox from what was written to the vault.
    """

    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    return repository.reset_proposal_item_decision(patch_id, item_ids, clock=clock)


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

    validation_errors = _validation_errors(item, vault, proposal.source_refs, proposal=proposal)
    validation_warnings = _validation_warnings(item, vault, proposal=proposal)
    validation_status = "invalid" if validation_errors else ("warning" if validation_warnings else "valid")
    review_policy = evaluate_review_policy(item, vault, source_refs=proposal.source_refs)
    return {
        "id": new_ulid(),
        "client_item_id": item.client_item_id,
        "item_type": item.item_type,
        "operation": item.operation,
        "target_entity_type": item.target.entity_type if item.target else None,
        "target_entity_id": item.target.entity_id if item.target else None,
        "payload": payload,
        "audit": item.audit.model_dump(mode="json", exclude_none=True) if item.audit is not None else None,
        "decision": "pending",
        "validation_status": validation_status,
        "validation_errors": validation_errors if validation_errors else validation_warnings,
        "created_at": now,
        "updated_at": now,
        "_auto_apply": validation_status == "valid" and review_policy == "auto_apply",
    }


def _auto_apply_rows(root: Path, patch_id: str, rows: list[dict[str, Any]]) -> None:
    auto_rows = [row for row in rows if row.get("_auto_apply")]
    if not auto_rows:
        return
    accept_items(root, patch_id, [row["id"] for row in auto_rows])


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
    *,
    proposal: AuthoringProposal | None = None,
) -> list[str]:
    errors: list[str] = []
    if item.review_route == "reject":
        errors.append("review_route=reject")
    for ref_id in _unresolved_source_ref_ids(vault, source_refs, item.source_ref_ids):
        errors.append(f"unresolved_source_ref:{ref_id}")
    if item.operation == "create" and _has_id_collision(item, vault):
        errors.append(f"duplicate_id:{item.proposed_entity_id or getattr(item.payload, 'id', None)}")
    if item.operation == "create":
        errors.extend(
            _required_create_payload_errors(
                item.item_type,
                item.payload.model_dump(mode="json", exclude_none=True),
                vault,
                proposal,
            )
        )
    if item.operation == "create" and item.item_type == "practice_item":
        practice_mode = getattr(item.payload, "practice_mode", None)
        if getattr(item.payload, "grading_rubric", None) is None and practice_mode not in vault.default_rubrics:
            errors.append(f"missing_rubric:{practice_mode or 'unknown_practice_mode'}")
        payload = item.payload.model_dump(mode="json", exclude_none=True)
        errors.extend(_attempt_type_validation_errors(payload))
        errors.extend(_practice_item_metadata_errors(payload, vault, proposal, generated=_looks_source_linked_generated(item)))
        audit_error = _generated_practice_audit_error(item)
        if audit_error is not None:
            errors.append(audit_error)
    if item.operation == "update" and item.item_type == "practice_item":
        payload = item.payload.model_dump(mode="json", exclude_none=True)
        errors.extend(_attempt_type_validation_errors(payload))
        errors.extend(_practice_item_metadata_errors(payload, vault, proposal, generated=False))
    if item.item_type == "concept_edge":
        errors.extend(_concept_edge_validation_errors(item.payload.model_dump(mode="json", exclude_none=True), vault, proposal))
    return errors


def _validation_warnings(
    item: AuthoringProposalItem,
    vault: LoadedVault,
    *,
    proposal: AuthoringProposal | None = None,
) -> list[str]:
    if item.item_type != "practice_item":
        return []
    payload = item.payload.model_dump(mode="json", exclude_none=True)
    return _practice_item_metadata_warnings(
        payload,
        vault,
        proposal,
        generated=_looks_source_linked_generated(item),
    )


def _edited_payload_validation_errors(
    item: dict[str, Any],
    edited_payload: dict[str, Any],
    vault: LoadedVault,
    *,
    batch_source_refs: list[dict[str, Any]] | None = None,
) -> list[str]:
    errors = [
        error
        for error in item.get("validation_errors", [])
        if str(error) == "review_route=reject"
    ]
    errors.extend(_payload_source_ref_validation_errors(edited_payload, vault, batch_source_refs))
    if item["operation"] == "create":
        entity_id = edited_payload.get("id") or item.get("target_entity_id")
        if item["item_type"] == "learning_object" and entity_id in vault.learning_objects:
            errors.append(f"duplicate_id:{entity_id}")
        elif item["item_type"] == "practice_item" and entity_id in vault.practice_items:
            errors.append(f"duplicate_id:{entity_id}")
        errors.extend(_required_create_payload_errors(item["item_type"], edited_payload, vault, None))
    if item["operation"] == "create" and item["item_type"] == "practice_item":
        practice_mode = edited_payload.get("practice_mode")
        if edited_payload.get("grading_rubric") is None and practice_mode not in vault.default_rubrics:
            errors.append(f"missing_rubric:{practice_mode or 'unknown_practice_mode'}")
    if item["item_type"] == "practice_item":
        errors.extend(_attempt_type_validation_errors(edited_payload))
        errors.extend(_practice_item_metadata_errors(edited_payload, vault, None, generated=False))
    if item["item_type"] == "concept_edge":
        errors.extend(_concept_edge_validation_errors(edited_payload, vault, None))
    return _dedupe_preserve_order(errors)


def _payload_source_ref_validation_errors(
    payload: dict[str, Any],
    vault: LoadedVault,
    batch_source_refs: list[dict[str, Any]] | None,
) -> list[str]:
    refs = _payload_source_ref_dicts(payload)
    if not refs:
        refs = batch_source_refs or []
    errors: list[str] = []
    for raw_ref in refs:
        if not isinstance(raw_ref, dict):
            errors.append("invalid_source_ref")
            continue
        try:
            source = SourceRef.model_validate(raw_ref)
        except ValidationError:
            errors.append(f"invalid_source_ref:{raw_ref.get('ref_id') or 'unknown'}")
            continue
        if not _source_ref_resolves(vault, source):
            errors.append(f"unresolved_source_ref:{source.ref_id}")
    return errors


def _payload_source_ref_dicts(payload: dict[str, Any]) -> list[dict[str, Any]]:
    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        return []
    source_refs = provenance.get("source_refs")
    if not isinstance(source_refs, list):
        return []
    return [source for source in source_refs if isinstance(source, dict)]


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _required_create_payload_errors(
    item_type: str,
    payload: dict[str, Any],
    vault: LoadedVault,
    proposal: AuthoringProposal | None,
) -> list[str]:
    required_by_type = {
        "learning_object": ["title", "subjects", "concept_id", "knowledge_type", "summary"],
        "practice_item": ["learning_object_id", "practice_mode", "prompt", "expected_answer"],
        "concept": ["title"],
        "error_type": ["title"],
    }
    errors: list[str] = []
    for field in required_by_type.get(item_type, []):
        if _missing(payload.get(field)):
            errors.append(f"missing_required:{field}")
    if item_type == "learning_object":
        concept_id = payload.get("concept_id") or payload.get("concept")
        if not _missing(concept_id) and concept_id not in _available_concept_ids(vault, proposal):
            errors.append(f"missing_required:concept_id:{concept_id}")
        subjects = payload.get("subjects") or []
        if subjects and subjects[0] not in vault.subjects:
            errors.append(f"missing_required:subject:{subjects[0]}")
    if item_type == "practice_item":
        learning_object_id = payload.get("learning_object_id")
        if not _missing(learning_object_id) and learning_object_id not in _available_learning_object_ids(vault, proposal):
            errors.append(f"missing_required:learning_object_id:{learning_object_id}")
    return errors


def _missing(value: Any) -> bool:
    return value is None or value == "" or value == []


def _attempt_type_validation_errors(payload: dict[str, Any]) -> list[str]:
    return [
        f"unsupported_attempt_type:{attempt_type}"
        for attempt_type in unsupported_attempt_types(payload.get("attempt_types_allowed"))
    ]


def _practice_item_metadata_errors(
    payload: dict[str, Any],
    vault: LoadedVault,
    proposal: AuthoringProposal | None,
    *,
    generated: bool,
) -> list[str]:
    errors: list[str] = []
    evidence_facets = _string_list(payload.get("evidence_facets"))
    evidence_weights = _float_map(payload.get("evidence_weights"))
    criterion_facet_weights = _nested_float_map(payload.get("criterion_facet_weights"))
    if generated and not evidence_facets:
        errors.append("missing_evidence_facets")
    unknown_weight_facets = sorted(set(evidence_weights) - set(evidence_facets))
    errors.extend(f"unknown_evidence_weight_facet:{facet}" for facet in unknown_weight_facets)
    if generated:
        errors.extend(_generated_practice_reward_metadata_errors(payload, evidence_facets, vault, proposal))
    weight_sum = sum(max(0.0, weight) for facet, weight in evidence_weights.items() if facet in evidence_facets)
    if generated and evidence_weights and weight_sum <= 0:
        errors.append("empty_evidence_weight_sum")
    criterion_ids = _rubric_criterion_ids(payload, vault, proposal)
    for criterion_id, facet_weights in criterion_facet_weights.items():
        if criterion_id not in criterion_ids:
            errors.append(f"unknown_criterion_facet_criterion:{criterion_id}")
        for facet in sorted(set(facet_weights) - set(evidence_facets)):
            errors.append(f"unknown_criterion_facet_facet:{facet}")
    return errors


def _practice_item_metadata_warnings(
    payload: dict[str, Any],
    vault: LoadedVault,
    proposal: AuthoringProposal | None,
    *,
    generated: bool,
) -> list[str]:
    warnings: list[str] = []
    evidence_facets = _string_list(payload.get("evidence_facets"))
    evidence_weights = _float_map(payload.get("evidence_weights"))
    criterion_facet_weights = _nested_float_map(payload.get("criterion_facet_weights"))
    if not generated and not evidence_facets:
        warnings.append("metadata_review:missing_evidence_facets")
    if evidence_facets and not evidence_weights:
        warnings.append("metadata_review:missing_evidence_weights")
    if generated and _rubric_criterion_ids(payload, vault, proposal) and not criterion_facet_weights:
        warnings.append("metadata_review:missing_criterion_facet_weights")
    return warnings


def _generated_practice_reward_metadata_errors(
    payload: dict[str, Any],
    evidence_facets: list[str],
    vault: LoadedVault,
    proposal: AuthoringProposal | None,
) -> list[str]:
    errors: list[str] = []
    for field in ("retrieval_demand", "transfer_distance", "scaffold_level"):
        if _missing(payload.get(field)):
            errors.append(f"missing_{field}")
            continue
        try:
            value = float(payload[field])
        except (TypeError, ValueError):
            errors.append(f"invalid_{field}")
            continue
        if value < 0.0 or value > 1.0:
            errors.append(f"invalid_{field}")
    if _missing(payload.get("surface_family")):
        errors.append("missing_surface_family")
    repair_targets = _string_list(payload.get("repair_targets"))
    if not repair_targets:
        errors.append("missing_repair_targets")
    else:
        allowed = set(evidence_facets) | _rubric_fatal_error_ids(payload, vault, proposal)
        for target in sorted(set(repair_targets) - allowed):
            errors.append(f"unknown_repair_target:{target}")
    return errors


def _rubric_criterion_ids(
    payload: dict[str, Any],
    vault: LoadedVault,
    proposal: AuthoringProposal | None,
) -> set[str]:
    rubric = payload.get("grading_rubric")
    if isinstance(rubric, dict):
        return {
            str(criterion.get("id"))
            for criterion in rubric.get("criteria", [])
            if isinstance(criterion, dict) and criterion.get("id")
        }
    practice_mode = payload.get("practice_mode")
    default = vault.default_rubrics.get(str(practice_mode)) if practice_mode is not None else None
    if default is None:
        return set()
    return {criterion.id for criterion in default.criteria}


def _rubric_fatal_error_ids(
    payload: dict[str, Any],
    vault: LoadedVault,
    proposal: AuthoringProposal | None,
) -> set[str]:
    rubric = payload.get("grading_rubric")
    if isinstance(rubric, dict):
        return {
            str(error.get("id"))
            for error in rubric.get("fatal_errors", [])
            if isinstance(error, dict) and error.get("id")
        }
    practice_mode = payload.get("practice_mode")
    default = vault.default_rubrics.get(str(practice_mode)) if practice_mode is not None else None
    if default is None:
        return set()
    return {fatal.id for fatal in default.fatal_errors}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _float_map(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, float] = {}
    for key, raw in value.items():
        try:
            result[str(key)] = float(raw)
        except (TypeError, ValueError):
            result[str(key)] = 0.0
    return result


def _nested_float_map(value: Any) -> dict[str, dict[str, float]]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, dict[str, float]] = {}
    for key, raw in value.items():
        result[str(key)] = _float_map(raw)
    return result


def _generated_practice_audit_error(item: AuthoringProposalItem) -> str | None:
    if item.item_type != "practice_item" or item.operation != "create":
        return None
    if not _looks_source_linked_generated(item):
        return None
    audit = item.audit
    if audit is None:
        return "missing_generated_audit"
    if audit.status == "failed":
        return "generated_audit_failed"
    if audit.status == "not_applicable_with_trace" and _missing(audit.trace):
        return "missing_generated_audit_trace"
    return None


def _looks_source_linked_generated(item: AuthoringProposalItem) -> bool:
    if item.audit is not None:
        return True
    payload = item.payload.model_dump(mode="json", exclude_none=True)
    tags = {str(tag).lower() for tag in payload.get("tags", [])}
    if tags & {"generated", "source_linked_generated", "source-linked-generated"}:
        return True
    rationale = item.rationale.lower()
    cues = (
        "generated",
        "no direct source",
        "no direct exercise",
        "no source exercise",
        "no direct example",
        "no source example",
        "transfer prompt",
        "misconception check",
    )
    return any(cue in rationale for cue in cues)


def _available_concept_ids(vault: LoadedVault, proposal: AuthoringProposal | None) -> set[str]:
    concept_ids = set(vault.concepts)
    if proposal is None:
        return concept_ids
    for item in proposal.items:
        if item.item_type == "concept" and item.operation == "create":
            concept_id = item.proposed_entity_id or getattr(item.payload, "id", None)
            if concept_id:
                concept_ids.add(concept_id)
        if item.item_type == "learning_object" and item.operation == "create":
            concept_id = getattr(item.payload, "concept_id", None)
            if concept_id:
                concept_ids.add(concept_id)
    return concept_ids


def _available_learning_object_ids(vault: LoadedVault, proposal: AuthoringProposal | None) -> set[str]:
    learning_object_ids = set(vault.learning_objects)
    if proposal is None:
        return learning_object_ids
    for item in proposal.items:
        if item.item_type == "learning_object" and item.operation == "create":
            learning_object_id = item.proposed_entity_id or getattr(item.payload, "id", None)
            if learning_object_id:
                learning_object_ids.add(learning_object_id)
    return learning_object_ids


def _concept_edge_validation_errors(
    payload: dict[str, Any],
    vault: LoadedVault,
    proposal: AuthoringProposal | None,
) -> list[str]:
    source = payload.get("source") or payload.get("source_concept_id")
    target = payload.get("target") or payload.get("target_concept_id")
    available_concepts = set(vault.concepts)
    if proposal is not None:
        available_concepts |= {
            item.proposed_entity_id or getattr(item.payload, "id", None)
            for item in proposal.items
            if item.item_type == "concept" and item.operation == "create"
        }
        available_concepts |= {
            getattr(item.payload, "concept_id", None)
            for item in proposal.items
            if item.item_type == "learning_object" and item.operation == "create"
        }
        available_concepts.discard(None)
    errors: list[str] = []
    if source not in available_concepts:
        errors.append(f"invalid_concept_edge:missing_source:{source or 'unknown'}")
    if target not in available_concepts:
        errors.append(f"invalid_concept_edge:missing_target:{target or 'unknown'}")
    return errors


def _default_edge_id(payload: dict[str, Any]) -> str | None:
    source = payload.get("source") or payload.get("source_concept_id")
    target = payload.get("target") or payload.get("target_concept_id")
    relation_type = payload.get("relation_type")
    if source is None or target is None or relation_type is None:
        return None
    from learnloop.ids import snake_case

    return f"edge_{snake_case(str(source))}_{relation_type}_{snake_case(str(target))}"


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
