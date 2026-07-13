from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
import hashlib
import json
from math import ceil
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

from learnloop.attempt_types import unsupported_attempt_types
from learnloop.ai.client import AIProviderClient
from learnloop.clock import Clock, utc_now_iso
from learnloop.codex.client import AuthoringContext, CodexClient, CodexUnavailable
from learnloop.codex.client import _authoring_prompt, _codex_output_schema
from learnloop.codex.prompts import (
    AUTHORING_PROMPT_VERSION,
    DIAGNOSTIC_AUTHORING_PROMPT,
    DIAGNOSTIC_AUTHORING_PROMPT_VERSION,
)
from learnloop.codex.schemas import AuthoringProposal, AuthoringProposalItem, ProposalItemAudit, SourceRef
from learnloop.db.repositories import MisconceptionRecord, Repository
from learnloop.services.diagnostic_gate import GateResult, run_discrimination_gate
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
    focus_concepts: list[str] | None = None,
    focus_facets: list[str] | None = None,
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

    facet_vocabulary = _vault_evidence_facet_unions(vault)
    surface_families = _vault_surface_family_unions(vault)
    learning_objects = [
        {
            "id": lo.id,
            "title": lo.title,
            "concept": lo.concept,
            "subjects": lo.subjects,
            "existing_evidence_facets": facet_vocabulary.get(lo.id, []),
            "existing_surface_families": surface_families.get(lo.id, []),
        }
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
        {"id": goal.id, "title": goal.title, "concept_anchors": goal.facet_scope.concepts}
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
        focus_concepts=list(focus_concepts or []),
        focus_facets=list(focus_facets or []),
    )


def _vault_evidence_facet_unions(vault: LoadedVault) -> dict[str, list[str]]:
    """Per-LO union of canonical evidence facet ids across the vault's items.

    Unlike ``_active_evidence_facet_unions`` in practice_generation this is
    Repository-free (``build_authoring_context`` is pure over the vault), so
    deactivated items' facets are included — for vocabulary reuse that is the
    right call: a facet id stays canonical even when its item is retired.
    """

    unions: dict[str, set[str]] = {}
    for item in vault.practice_items.values():
        unions.setdefault(item.learning_object_id, set()).update(
            vault.canonical_facet_id(facet) for facet in item.evidence_facets
        )
    return {lo_id: sorted(facets) for lo_id, facets in unions.items() if facets}


def _vault_surface_family_unions(vault: LoadedVault) -> dict[str, list[str]]:
    unions: dict[str, set[str]] = {}
    for item in vault.practice_items.values():
        if item.surface_family:
            unions.setdefault(item.learning_object_id, set()).add(str(item.surface_family))
    return {lo_id: sorted(families) for lo_id, families in unions.items() if families}


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
        "focus_concepts": context.focus_concepts,
        "focus_facets": context.focus_facets,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DiagnosticTarget:
    """Relational review context for a diagnostic-authoring proposal (spec §5.3).

    Resolved from the intervention need at review time. ``demonstrated_facets`` and
    ``source_surface_family`` are read from the need's ``diagnostic_focus`` snapshot
    (taken at need-creation), never from live learner state, so a proposal validates
    identically regardless of when it is reviewed. ``implicated_facets`` (the union
    of the targeted beliefs' facets) backs the soft footprint warning.
    """

    need_id: str
    misconception_ids: list[str]
    misconception_statements: dict[str, str]
    source_practice_item_id: str | None
    source_surface_family: str | None
    demonstrated_facets: list[str]
    implicated_facets: list[str] = field(default_factory=list)


def diagnostic_target_from_need(need: dict[str, Any]) -> DiagnosticTarget:
    """Build a :class:`DiagnosticTarget` from an intervention need row (spec §5.3)."""

    focus = need.get("diagnostic_focus") if isinstance(need.get("diagnostic_focus"), dict) else {}
    focus = focus or {}
    return DiagnosticTarget(
        need_id=str(need["id"]),
        misconception_ids=[str(mc) for mc in (focus.get("misconception_ids") or [])],
        misconception_statements={
            str(k): str(v) for k, v in (focus.get("misconception_statements") or {}).items()
        },
        source_practice_item_id=focus.get("source_practice_item_id") or need.get("practice_item_id"),
        source_surface_family=focus.get("source_surface_family"),
        demonstrated_facets=[str(f) for f in (focus.get("demonstrated_facets") or [])],
        implicated_facets=[str(f) for f in (focus.get("implicated_facets") or [])],
    )


def _diagnostic_payload_fatal_misconception_ids(payload: dict[str, Any]) -> set[str]:
    rubric = payload.get("grading_rubric")
    if not isinstance(rubric, dict):
        return set()
    ids: set[str] = set()
    for fatal_error in rubric.get("fatal_errors", []) or []:
        if isinstance(fatal_error, dict) and fatal_error.get("misconception_id"):
            ids.add(str(fatal_error["misconception_id"]))
    return ids


def diagnostic_review_errors(item: AuthoringProposalItem, context: DiagnosticTarget | None) -> list[str]:
    """Hard §5.3 validation errors for a diagnostic-authoring item.

    A missing context on a diagnostic item is itself a hard error (the relational
    checks must not silently soften). With context: no fatal error keyed to one of
    the target misconception ids; missing ``misconception_consistent_answer``;
    ``surface_family`` equal to the source item's.
    """

    if context is None:
        return ["missing_diagnostic_target_context"]
    if item.item_type != "practice_item":
        return []
    payload = item.payload.model_dump(mode="json", exclude_none=True)
    errors: list[str] = []
    fatal_mc_ids = _diagnostic_payload_fatal_misconception_ids(payload)
    if not (fatal_mc_ids & set(context.misconception_ids)):
        errors.append("diagnostic_missing_keyed_fatal_error")
    if _missing(payload.get("misconception_consistent_answer")):
        errors.append("diagnostic_missing_misconception_consistent_answer")
    surface_family = payload.get("surface_family")
    if (
        surface_family is not None
        and context.source_surface_family is not None
        and surface_family == context.source_surface_family
    ):
        errors.append("diagnostic_surface_family_matches_source")
    return errors


def diagnostic_review_warnings(item: AuthoringProposalItem, context: DiagnosticTarget | None) -> list[str]:
    """Soft §5.3 warnings: footprint exceeds implicated set / hits demonstrated facets."""

    if context is None or item.item_type != "practice_item":
        return []
    payload = item.payload.model_dump(mode="json", exclude_none=True)
    evidence_facets = set(_string_list(payload.get("evidence_facets")))
    warnings: list[str] = []
    implicated = set(context.implicated_facets)
    if implicated and not evidence_facets <= implicated:
        warnings.append("diagnostic_footprint_exceeds_implicated_facets")
    intersecting = sorted(evidence_facets & set(context.demonstrated_facets))
    for facet in intersecting:
        warnings.append(f"diagnostic_footprint_hits_demonstrated_facet:{facet}")
    return warnings


def evaluate_review_policy(
    item: AuthoringProposalItem,
    vault: LoadedVault,
    *,
    source_refs: list[SourceRef] | None = None,
    context: DiagnosticTarget | None = None,
) -> str:
    """Resolve an item's effective review route under the auto-apply-low-risk policy.

    Returns one of ``auto_apply``, ``review_required``, or ``reject``. Auto-apply
    is only returned for direct, source-grounded creation of Learning Objects /
    Practice Items with resolvable source refs and no id collision.

    When ``context`` is supplied (a diagnostic-authoring item, spec §5.3) the
    relational checks run: any hard :func:`diagnostic_review_errors` route to
    ``reject``; otherwise a diagnostic item is never auto-applied — the sim gate
    (§6) is the only thing that can later promote it — so it is ``review_required``.
    ``context=None`` keeps today's behavior for ordinary authoring proposals.
    """

    if context is not None:
        if diagnostic_review_errors(item, context):
            return "reject"
        return "review_required"

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
    source_refs: list[dict[str, Any]] | None = None,
    instructions: str | None = None,
    focus_concepts: list[str] | None = None,
    focus_facets: list[str] | None = None,
    model: str | None = None,
    codex_revision: str | None = None,
    merge_context_source_refs: bool = False,
    row_transform: Callable[[list[dict[str, Any]]], None] | None = None,
    clock: Clock | None = None,
) -> str:
    """Run authoring generation through a CodexClient and persist the result.

    The agent run is recorded before the call and completed/failed afterwards so
    every persisted proposal batch has agent-run lineage.

    ``row_transform`` is an optional, default-off seam (spec_tutor_promotion.md §3
    Step 3): it is invoked once on the final persisted rows AFTER validation/repair
    and BEFORE persist + ``_auto_apply_rows``, so a caller can downgrade a row's
    ``_auto_apply`` flag or patch its payload (e.g. force review, add a tag)
    without the route ever leaking to auto-apply. It mutates the rows in place.
    """

    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    context = build_authoring_context(
        vault,
        subjects=subjects,
        note_ids=note_ids,
        source_refs=source_refs,
        instructions=instructions,
        focus_concepts=focus_concepts,
        focus_facets=focus_facets,
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
    if merge_context_source_refs:
        proposal = _proposal_with_context_source_refs(proposal, context.source_refs)
    repository.complete_agent_run(agent_run_id, status="completed", clock=clock)
    provider = provider_fields["provider"] or "codex"
    rows = [
        _proposal_item_row(item, now, vault=vault, proposal=proposal, provider=provider)
        for item in proposal.items
    ]
    proposal, rows = _repair_invalid_proposal_items(
        codex_client,
        context,
        proposal,
        rows,
        vault=vault,
        provider=provider,
        now=now,
    )
    if row_transform is not None:
        row_transform(rows)
    proposal_payload = proposal.model_dump(mode="json", exclude_none=False)
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


def build_diagnostic_authoring_context(
    vault: LoadedVault,
    repository: Repository,
    need: dict[str, Any],
) -> AuthoringContext:
    """Package ⟨belief, learner answer, grader evidence, source item⟩ for authoring (spec §5.1).

    Reuses :class:`AuthoringContext` (least invasive): the §5.2 constraints plus a
    ``DIAGNOSTIC_TARGET`` JSON block ride in the ``instructions`` field, so the
    existing ``run_authoring_proposal`` path and fake clients work unchanged. The
    demonstrated facets come from the need's ``diagnostic_focus`` snapshot, not live
    state (§5.3).
    """

    target = diagnostic_target_from_need(need)
    learning_object_id = need.get("learning_object_id")
    records = [repository.misconception(mc_id) for mc_id in target.misconception_ids]
    misconception_blocks = [
        {"id": r.id, "statement": r.statement, "signature": r.signature, "facet_ids": r.facet_ids}
        for r in records
        if r is not None
    ]
    attempt = repository.fetch_practice_attempt(str(need.get("attempt_id") or "")) or {}
    learner_answer_md = attempt.get("learner_answer_md")
    grader_evidence: list[dict[str, Any]] = []
    for event in repository.error_events_for_attempt(str(need.get("attempt_id") or "")):
        event_mc = event.get("misconception_id")
        if event_mc is not None and event_mc not in target.misconception_ids:
            continue
        grader_evidence.append(
            {
                "misconception_id": event_mc,
                "statement": event.get("misconception_statement"),
                "misconception_consistent_answer": event.get("misconception_consistent_answer"),
                "repair_plan": event.get("repair_plan"),
            }
        )
    source_item = vault.practice_items.get(str(target.source_practice_item_id or ""))
    source_block = None
    if source_item is not None:
        expected = source_item.expected_answer
        source_block = {
            "id": source_item.id,
            "prompt": _excerpt(source_item.prompt, 400),
            "expected_answer": expected if isinstance(expected, str) else "(structured answer)",
            "surface_family": source_item.surface_family,
            "evidence_facets": list(source_item.evidence_facets),
        }
    target_payload = {
        "learning_object_id": learning_object_id,
        "misconceptions": misconception_blocks,
        "learner_answer_md": learner_answer_md,
        "grader_evidence": grader_evidence,
        "source_item": source_block,
        "demonstrated_facets": target.demonstrated_facets,
        "implicated_facets": target.implicated_facets,
    }
    instructions = (
        DIAGNOSTIC_AUTHORING_PROMPT
        + "\n\nDIAGNOSTIC_TARGET:\n"
        + json.dumps(target_payload, sort_keys=True, ensure_ascii=False)
    )
    learning_object = vault.learning_objects.get(str(learning_object_id or ""))
    subjects = list(learning_object.subjects) if learning_object is not None else None
    return build_authoring_context(vault, subjects=subjects, instructions=instructions)


def _diagnostic_proposal_item_row(
    item: AuthoringProposalItem,
    now: str,
    *,
    vault: LoadedVault,
    proposal: AuthoringProposal,
    provider: str,
    context: DiagnosticTarget,
) -> dict[str, Any]:
    """Persisted row for a diagnostic-authoring item: base validation + §5.3 checks.

    Diagnostic items are never auto-applied (the sim gate is the only promoter);
    the relational §5.3 errors/warnings are surfaced exactly like the ordinary
    ``_validation_errors``/``_validation_warnings`` on the row.
    """

    row = _proposal_item_row(item, now, vault=vault, proposal=proposal, provider=provider)
    row["_auto_apply"] = False
    if item.item_type != "practice_item":
        return row
    errors = _dedupe_preserve_order(
        _validation_errors(item, vault, proposal.source_refs, proposal=proposal)
        + diagnostic_review_errors(item, context)
    )
    warnings = _dedupe_preserve_order(
        _validation_warnings(item, vault, proposal=proposal) + diagnostic_review_warnings(item, context)
    )
    if errors:
        row["validation_status"] = "invalid"
        row["validation_errors"] = errors
    elif warnings:
        row["validation_status"] = "warning"
        row["validation_errors"] = warnings
    else:
        row["validation_status"] = "valid"
        row["validation_errors"] = []
    return row


def _gate_target_record(
    payload: dict[str, Any],
    target: DiagnosticTarget,
    records_by_id: dict[str, MisconceptionRecord],
) -> MisconceptionRecord | None:
    """The registry belief a generated item is gated against (its keyed fatal, else first)."""

    fatal_mc_ids = _diagnostic_payload_fatal_misconception_ids(payload)
    for mc_id in target.misconception_ids:
        if mc_id in fatal_mc_ids and mc_id in records_by_id:
            return records_by_id[mc_id]
    for mc_id in target.misconception_ids:
        if mc_id in records_by_id:
            return records_by_id[mc_id]
    return None


def _reopen_need_after_gate_failure(
    repository: Repository,
    *,
    need_id: str,
    patch_id: str,
    item_id: str | None,
    results: list[GateResult],
    need: dict[str, Any],
) -> None:
    """Reopen the need with the sim estimates attached (spec §6 reopen).

    Mirrors ``_reopen_diagnostic_needs_for_rejected_items``' blocked_reason
    convention (``diagnostic_proposal_rejected:<patch>:<item>``) and appends
    ``last_gate_result`` into ``diagnostic_focus`` so the next generation round
    sees the (sens, spec) estimates + failure reason.
    """

    blocked_reason = f"diagnostic_proposal_rejected:{patch_id}"
    if item_id:
        blocked_reason = f"{blocked_reason}:{item_id}"
    focus = dict(need.get("diagnostic_focus") or {})
    focus["last_gate_result"] = [result.as_dict() for result in results]
    repository.update_intervention_need_diagnostic_focus(need_id, focus)
    repository.update_intervention_need_status(need_id, status="pending", blocked_reason=blocked_reason)


def generate_diagnostic_proposal(
    root: Path,
    client: CodexClient | AIProviderClient,
    *,
    need_id: str,
    model: str | None = None,
    clock: Clock | None = None,
) -> str:
    """Author a discriminating diagnostic from a pending misconception need (spec §5/§6).

    Builds the §5.1 context, runs generation, validates each item against the
    §5.3 ``DiagnosticTarget``, persists (never auto-applying — review_required at
    most), links the need (``diagnostic_proposal_queued:<patch>[:<item>]``), then
    runs the §6 sim discrimination gate per generated item. Gate pass seeds the
    discrimination row and leaves the item for review; gate failure rejects the
    item and reopens the need with the estimates attached.
    """

    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    need = repository.intervention_need(need_id)
    if need is None:
        raise ValueError(f"Intervention need {need_id} not found")
    target = diagnostic_target_from_need(need)
    if not target.misconception_ids:
        raise ValueError(f"Intervention need {need_id} carries no misconception_ids for diagnostic authoring")
    records_by_id: dict[str, MisconceptionRecord] = {}
    for mc_id in target.misconception_ids:
        record = repository.misconception(mc_id)
        if record is not None:
            records_by_id[mc_id] = record

    context = build_diagnostic_authoring_context(vault, repository, need)
    now = utc_now_iso(clock)
    provider_fields = _agent_provider_fields(client, model=model, provider_revision=None)
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": "diagnostic_authoring",
            **provider_fields,
            "prompt_template": "diagnostic_authoring",
            "prompt_version": DIAGNOSTIC_AUTHORING_PROMPT_VERSION,
            "input_context_hash": authoring_context_hash(context),
            "output_schema": "AuthoringProposal",
            "started_at": now,
            "status": "running",
        }
    )
    try:
        proposal = client.run_authoring_proposal(context)
    except (CodexUnavailable, TimeoutError, ValueError) as exc:
        repository.complete_agent_run(agent_run_id, status="failed", error_message=str(exc), clock=clock)
        raise
    repository.complete_agent_run(agent_run_id, status="completed", clock=clock)

    provider = provider_fields["provider"] or "codex"
    proposal_payload = proposal.model_dump(mode="json", exclude_none=False)
    rows = [
        _diagnostic_proposal_item_row(
            item, now, vault=vault, proposal=proposal, provider=provider, context=target
        )
        for item in proposal.items
    ]
    practice_rows = [
        (row, item) for row, item in zip(rows, proposal.items) if item.item_type == "practice_item"
    ]
    primary_item_id = practice_rows[0][0]["payload"].get("id") if practice_rows else None
    patch_id = repository.persist_proposal_batch(
        {
            "id": new_ulid(),
            "agent_run_id": agent_run_id,
            "purpose": "diagnostic_authoring",
            "source_refs": proposal_payload["source_refs"],
            "summary": proposal.summary,
            "created_at": now,
            "updated_at": now,
        },
        rows,
    )

    blocked_reason = f"diagnostic_proposal_queued:{patch_id}"
    if primary_item_id:
        blocked_reason = f"{blocked_reason}:{primary_item_id}"
    repository.update_intervention_need_status(need_id, status="fulfilled", blocked_reason=blocked_reason)

    # spec §6: sim discrimination gate, post-generation / pre-queue. Rejects any
    # item whose planted/clean simulation does not clear the lower-bound thresholds.
    failed_row_ids: list[str] = []
    failure_results: list[GateResult] = []
    failed_item_ids: list[str] = []
    for row, _item in practice_rows:
        payload = row["payload"]
        record = _gate_target_record(payload, target, records_by_id)
        if record is None:
            continue
        result = run_discrimination_gate(
            vault,
            repository,
            item=payload,
            misconception=record,
            grading_client=client,
            clock=clock,
        )
        if not result.accepted:
            failed_row_ids.append(row["id"])
            failure_results.append(result)
            failed_item_ids.append(str(payload.get("id") or ""))
    if failed_row_ids:
        repository.set_proposal_item_decision(patch_id, "rejected", failed_row_ids)
        _reopen_need_after_gate_failure(
            repository,
            need_id=need_id,
            patch_id=patch_id,
            item_id=failed_item_ids[0] if failed_item_ids else None,
            results=failure_results,
            need=need,
        )
    return patch_id


def _proposal_with_context_source_refs(
    proposal: AuthoringProposal,
    context_source_refs: list[dict[str, Any]],
) -> AuthoringProposal:
    if not context_source_refs:
        return proposal
    merged_by_id = {
        ref.ref_id: ref.model_dump(mode="json", exclude_none=True)
        for ref in proposal.source_refs
    }
    for raw_ref in context_source_refs:
        ref = SourceRef.model_validate(raw_ref)
        merged_by_id[ref.ref_id] = ref.model_dump(mode="json", exclude_none=True)
    return AuthoringProposal.model_validate(
        {
            "summary": proposal.summary,
            "source_refs": list(merged_by_id.values()),
            "items": [item.model_dump(mode="json", exclude_none=True) for item in proposal.items],
        }
    )


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
    diagnostic_reopen_candidates = _diagnostic_reopen_candidates(repository, patch_id, item_ids)
    applied_count = reject_applied_items(root, patch_id, item_ids)
    pending_count = repository.set_proposal_item_decision(patch_id, "rejected", item_ids)
    if applied_count + pending_count:
        _reopen_diagnostic_needs_for_rejected_items(repository, patch_id, diagnostic_reopen_candidates)
    return applied_count + pending_count


def _diagnostic_reopen_candidates(
    repository: Repository,
    patch_id: str,
    item_ids: list[str] | None,
) -> list[dict[str, Any]]:
    selected = set(item_ids) if item_ids else None
    return [
        item
        for item in repository.proposal_items(patch_id)
        if item["decision"] in {"pending", "accepted"}
        and (selected is None or item["id"] in selected)
        and _is_diagnostic_probe_item(item)
    ]


def _is_diagnostic_probe_item(item: dict[str, Any]) -> bool:
    if item.get("item_type") != "practice_item" or item.get("operation") != "create":
        return False
    payloads = [item.get("payload")]
    if item.get("edited_payload") is not None:
        payloads.append(item.get("edited_payload"))
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        if payload.get("practice_mode") == "diagnostic_probe":
            return True
        attempt_types = payload.get("attempt_types_allowed")
        if isinstance(attempt_types, list) and "diagnostic_probe" in attempt_types:
            return True
    return False


def _reopen_diagnostic_needs_for_rejected_items(
    repository: Repository,
    patch_id: str,
    candidate_items: list[dict[str, Any]],
) -> None:
    if not candidate_items:
        return
    queued_needs = repository.intervention_needs_for_diagnostic_proposal(patch_id)
    if not queued_needs:
        return
    queued_by_id = {need["id"]: need for need in queued_needs}
    matched: dict[str, str | None] = {}
    unmatched_items: list[dict[str, Any]] = []
    for item in candidate_items:
        need_ids = _need_ids_for_diagnostic_item(item, queued_by_id, patch_id)
        if need_ids:
            for need_id in need_ids:
                matched.setdefault(need_id, item["id"])
        else:
            unmatched_items.append(item)

    remaining_patch_level_needs = [
        need
        for need in queued_needs
        if need["id"] not in matched
        and need.get("blocked_reason") == f"diagnostic_proposal_queued:{patch_id}"
    ]
    if len(unmatched_items) == 1 and len(remaining_patch_level_needs) == 1:
        matched[remaining_patch_level_needs[0]["id"]] = unmatched_items[0]["id"]

    for need_id, item_id in matched.items():
        blocked_reason = f"diagnostic_proposal_rejected:{patch_id}"
        if item_id:
            blocked_reason = f"{blocked_reason}:{item_id}"
        repository.update_intervention_need_status(
            need_id,
            status="pending",
            blocked_reason=blocked_reason,
        )


def _need_ids_for_diagnostic_item(
    item: dict[str, Any],
    queued_by_id: dict[str, dict[str, Any]],
    patch_id: str,
) -> list[str]:
    item_id = str(item["id"])
    item_specific_reason = f"diagnostic_proposal_queued:{patch_id}:{item_id}"
    item_specific = [
        need_id
        for need_id, need in queued_by_id.items()
        if need.get("blocked_reason") == item_specific_reason
    ]
    if item_specific:
        return item_specific

    source_ref_ids = {str(ref_id) for ref_id in item.get("source_ref_ids") or []}
    source_ref_matches = sorted(need_id for need_id in source_ref_ids if need_id in queued_by_id)
    if source_ref_matches:
        return source_ref_matches

    client_item_id = str(item.get("client_item_id") or "")
    return sorted(need_id for need_id in queued_by_id if need_id in client_item_id)


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


def repair_proposal_item_audit(
    root: Path,
    patch_id: str,
    item_id: str,
    audit: dict[str, Any],
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Replace a pending item's audit and revalidate the complete proposal item."""
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    item = repository.proposal_item(item_id)
    if item is None or item["proposed_patch_id"] != patch_id:
        raise ValueError(f"Proposal item {item_id} was not found in proposal {patch_id}")
    if item["decision"] != "pending":
        raise ValueError(f"Proposal item {item_id} is already {item['decision']}")

    validated_audit = ProposalItemAudit.model_validate(audit)
    payload = item.get("edited_payload") or item.get("payload") or {}
    batch = repository.proposal_batch(patch_id)
    errors = _edited_payload_validation_errors(
        item,
        payload,
        vault,
        batch_source_refs=batch.get("source_refs") if batch is not None else None,
    )
    if validated_audit.status == "failed":
        errors.append("generated_audit_failed")
    elif validated_audit.status == "not_applicable_with_trace" and _missing(validated_audit.trace):
        errors.append("missing_generated_audit_trace")
    errors = _dedupe_preserve_order(errors)
    updated = repository.update_proposal_item_audit(
        item_id,
        audit=validated_audit.model_dump(mode="json", exclude_none=True),
        validation_status="invalid" if errors else "valid",
        validation_errors=errors,
        clock=clock,
    )
    if not updated:
        raise ValueError(f"Proposal item {item_id} could not be repaired")
    refreshed = repository.proposal_item(item_id)
    if refreshed is None:
        raise ValueError(f"Proposal item {item_id} disappeared after repair")
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


def accept_items(
    root: Path,
    patch_id: str,
    item_ids: list[str] | None = None,
    *,
    clock: Clock | None = None,
) -> PatchApplyResult:
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    selected_items = repository.pending_proposal_items(patch_id, item_ids)
    diagnostic_items = [item for item in selected_items if _is_diagnostic_probe_item(item)]
    result = apply_accepted_items(root, patch_id, item_ids, clock=clock)
    if result.applied_count and diagnostic_items:
        _queue_accepted_diagnostic_followups_for_patch(repository, patch_id, diagnostic_items)
    return result


def queue_accepted_diagnostic_followups(
    repository: Repository,
    *,
    patch_id: str | None = None,
) -> int:
    """Backfill queued follow-up actions for accepted diagnostic proposals.

    New acceptances are queued by ``accept_items``. This reconciler handles
    already-accepted diagnostic probes from before that handoff existed, so the
    Today queue can still surface them as intervention follow-ups.
    """

    batches = [repository.proposal_batch(patch_id)] if patch_id else repository.proposal_batches()
    queued = 0
    for batch in batches:
        if batch is None:
            continue
        accepted_diagnostics = [
            item
            for item in repository.proposal_items(batch["id"])
            if item.get("decision") == "accepted" and _is_diagnostic_probe_item(item)
        ]
        queued += _queue_accepted_diagnostic_followups_for_patch(
            repository,
            batch["id"],
            accepted_diagnostics,
        )
    return queued


def _queue_accepted_diagnostic_followups_for_patch(
    repository: Repository,
    patch_id: str,
    diagnostic_items: list[dict[str, Any]],
) -> int:
    queued_needs = repository.intervention_needs_for_diagnostic_proposal(patch_id)
    if not queued_needs:
        return 0
    queued_by_id = {need["id"]: need for need in queued_needs}
    queued_count = 0
    for item in diagnostic_items:
        practice_item_id = _accepted_practice_item_id(item)
        if practice_item_id is None:
            continue
        for need_id in _need_ids_for_diagnostic_item(item, queued_by_id, patch_id):
            attempt_id = queued_by_id[need_id].get("attempt_id")
            if attempt_id and _append_intervention_queued_action(repository, str(attempt_id), practice_item_id):
                queued_count += 1
    return queued_count


def _accepted_practice_item_id(item: dict[str, Any]) -> str | None:
    payload = item.get("edited_payload") if item.get("edited_payload") is not None else item.get("payload")
    if not isinstance(payload, dict):
        return None
    entity_id = payload.get("id") or item.get("target_entity_id")
    return str(entity_id) if entity_id else None


def _append_intervention_queued_action(
    repository: Repository,
    attempt_id: str,
    practice_item_id: str,
) -> bool:
    surprise = repository.latest_attempt_surprise(attempt_id)
    if surprise is None:
        return False
    action = f"intervention_followup:queued:{practice_item_id}"
    triggered_actions = list(surprise.get("triggered_actions") or [])
    if action in triggered_actions:
        return False
    return repository.update_attempt_surprise_actions(
        attempt_id,
        triggered_actions=[*triggered_actions, action],
    )


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
    if item.item_type == "practice_item" and _looks_source_linked_generated(item):
        # Mutate the model before dumping so the persisted payload and the validators
        # (which re-dump item.payload) agree on the backfilled maps.
        _backfill_practice_item_facet_weights(item, vault)
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
        "source_ref_ids": list(item.source_ref_ids),
        "audit": item.audit.model_dump(mode="json", exclude_none=True) if item.audit is not None else None,
        "decision": "pending",
        "validation_status": validation_status,
        "validation_errors": validation_errors if validation_errors else validation_warnings,
        "created_at": now,
        "updated_at": now,
        "_auto_apply": validation_status == "valid" and review_policy == "auto_apply",
    }


def _repair_invalid_proposal_items(
    codex_client: CodexClient | AIProviderClient,
    context: AuthoringContext,
    proposal: AuthoringProposal,
    rows: list[dict[str, Any]],
    *,
    vault: LoadedVault,
    provider: str,
    now: str,
) -> tuple[AuthoringProposal, list[dict[str, Any]]]:
    """One-shot self-repair for items that failed deterministic validation.

    Feeds the failing items and their error codes back to the provider once and
    merges corrected items by ``client_item_id``. Best-effort: any provider
    failure (or a fake client that can't take a second call) leaves the original
    proposal untouched, so callers never lose the first-pass result.
    """

    invalid_rows = [row for row in rows if row["validation_status"] == "invalid"]
    if not invalid_rows:
        return proposal, rows
    items_by_client_id = {item.client_item_id: item for item in proposal.items}
    failing = [
        {
            "client_item_id": row["client_item_id"],
            "validation_errors": row["validation_errors"],
            "item": items_by_client_id[row["client_item_id"]].model_dump(mode="json", exclude_none=True),
        }
        for row in invalid_rows
        if row["client_item_id"] in items_by_client_id
    ]
    if not failing:
        return proposal, rows
    instructions = (
        "REPAIR PASS: your previous authoring proposal contains items that failed "
        "LearnLoop's deterministic validation. Return a proposal whose items are "
        "ONLY corrected versions of the FAILING_ITEMS below. Keep each item's "
        "client_item_id, entity ids, source_ref_ids, and intent unchanged; change "
        "only what the validation error codes name. Reuse the original proposal's "
        "source_refs verbatim. FAILING_ITEMS: "
        + json.dumps(failing, sort_keys=True, ensure_ascii=False)
    )
    try:
        repaired = codex_client.run_authoring_proposal(replace(context, instructions=instructions))
    except Exception:
        return proposal, rows
    failing_ids = {entry["client_item_id"] for entry in failing}
    repaired_by_id = {
        item.client_item_id: item for item in repaired.items if item.client_item_id in failing_ids
    }
    if not repaired_by_id:
        return proposal, rows
    merged = proposal.model_copy(
        update={
            "items": [
                repaired_by_id.get(item.client_item_id, item) for item in proposal.items
            ]
        }
    )
    merged_rows = [
        _proposal_item_row(item, now, vault=vault, proposal=merged, provider=provider)
        for item in merged.items
    ]
    return merged, merged_rows


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


def _backfill_practice_item_facet_weights(item: AuthoringProposalItem, vault: LoadedVault) -> None:
    """Derive the facet-weight maps the authoring model commonly omits.

    ``evidence_weights`` / ``criterion_facet_weights`` are optional in the authoring
    schema, so generated diagnostic probes routinely arrive without them and trip the
    ``metadata_review:missing_*`` review warnings on every diagnostic review. Both are
    recoverable from data already on the payload, so we fill the unambiguous cases here
    (mirroring the ``provenance`` backfill above) rather than relying on LLM compliance:

    - ``evidence_weights``: a uniform normalized distribution over ``evidence_facets``.
    - ``criterion_facet_weights``: when the item has a *single* evidence facet, every
      rubric criterion maps to it with weight ``1.0``. With multiple facets the
      criterion->facet assignment is not derivable, so it is left for human review.

    Mutates ``item.payload`` in place (only missing/empty maps are filled, so
    author-supplied weights are never overwritten) so the persisted payload and the
    re-dumping validators stay in agreement.
    """

    payload = item.payload
    evidence_facets = [str(facet) for facet in (getattr(payload, "evidence_facets", None) or []) if str(facet)]
    if not evidence_facets:
        return
    if not (getattr(payload, "evidence_weights", None) or {}):
        share = 1.0 / len(evidence_facets)
        payload.evidence_weights = {facet: share for facet in evidence_facets}
    if not (getattr(payload, "criterion_facet_weights", None) or {}) and len(evidence_facets) == 1:
        facet = evidence_facets[0]
        criterion_ids = _rubric_criterion_ids(payload.model_dump(mode="json", exclude_none=True), vault, None)
        if criterion_ids:
            payload.criterion_facet_weights = {
                criterion_id: {facet: 1.0} for criterion_id in sorted(criterion_ids)
            }


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
        # teach_back items always carry their own two-tier rubric: the default-rubric
        # fallback is not allowed for them.
        if getattr(item.payload, "grading_rubric", None) is None and (
            practice_mode == _TEACH_BACK_PRACTICE_MODE or practice_mode not in vault.default_rubrics
        ):
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
        if edited_payload.get("grading_rubric") is None and (
            practice_mode == _TEACH_BACK_PRACTICE_MODE or practice_mode not in vault.default_rubrics
        ):
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


# Kept as a local literal (matches services.teach_back.TEACH_BACK_PRACTICE_MODE)
# so proposal validation stays import-light.
_TEACH_BACK_PRACTICE_MODE = "teach_back"
_RUBRIC_CRITERION_TIERS = {"core", "transfer"}


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
    errors.extend(_practice_item_rubric_errors(payload))
    criterion_ids = _rubric_criterion_ids(payload, vault, proposal)
    for criterion_id, facet_weights in criterion_facet_weights.items():
        if criterion_id not in criterion_ids:
            errors.append(f"unknown_criterion_facet_criterion:{criterion_id}")
        for facet in sorted(set(facet_weights) - set(evidence_facets)):
            errors.append(f"unknown_criterion_facet_facet:{facet}")
    if payload.get("practice_mode") == _TEACH_BACK_PRACTICE_MODE:
        errors.extend(_teach_back_rubric_errors(payload, evidence_facets, criterion_facet_weights))
    return errors


def _teach_back_rubric_errors(
    payload: dict[str, Any],
    evidence_facets: list[str],
    criterion_facet_weights: dict[str, dict[str, float]],
) -> list[str]:
    """Structural checks for teach_back rubrics beyond the generic rubric rules.

    Only asked criteria produce evidence at grade time, and follow-up planning
    walks criterion_facet_weights per tier, so every criterion must be facet
    mapped and every evidence facet must be reachable through a core-tier
    criterion. The missing-rubric case itself is reported by the create-path
    ``missing_rubric:teach_back`` error, not here.
    """

    rubric = payload.get("grading_rubric")
    if not isinstance(rubric, dict):
        return []
    criteria = rubric.get("criteria")
    if not isinstance(criteria, list):
        return []
    tier_by_criterion: dict[str, str] = {}
    for criterion in criteria:
        if not isinstance(criterion, dict) or not criterion.get("id"):
            continue
        tier_by_criterion[str(criterion["id"])] = str(criterion.get("tier") or "core")
    errors: list[str] = []
    for criterion_id in sorted(tier_by_criterion):
        if not criterion_facet_weights.get(criterion_id):
            errors.append(f"teach_back_unmapped_criterion:{criterion_id}")
    core_facets: set[str] = set()
    for criterion_id, facet_weights in criterion_facet_weights.items():
        if tier_by_criterion.get(criterion_id) == "core":
            core_facets.update(facet for facet, weight in facet_weights.items() if weight > 0)
    for facet in sorted(set(evidence_facets) - core_facets):
        errors.append(f"teach_back_missing_core_criterion:{facet}")
    return errors


def _practice_item_rubric_errors(payload: dict[str, Any]) -> list[str]:
    rubric = payload.get("grading_rubric")
    if not isinstance(rubric, dict):
        return []

    errors: list[str] = []
    try:
        max_points = float(rubric.get("max_points", 4))
    except (TypeError, ValueError):
        return ["invalid_grading_rubric:max_points"]
    if max_points <= 0:
        errors.append("invalid_grading_rubric:max_points")
    if max_points > 4:
        errors.append("invalid_grading_rubric:max_points_exceeds_grading_scale")

    total_points = 0.0
    criteria = rubric.get("criteria")
    if isinstance(criteria, list):
        for criterion in criteria:
            if not isinstance(criterion, dict):
                continue
            try:
                points = float(criterion.get("points", 0))
            except (TypeError, ValueError):
                errors.append(f"invalid_grading_rubric:criterion_points:{criterion.get('id') or 'unknown'}")
                continue
            if points <= 0 or points > 4:
                errors.append(f"invalid_grading_rubric:criterion_points:{criterion.get('id') or 'unknown'}")
            tier = criterion.get("tier")
            if tier is not None and tier not in _RUBRIC_CRITERION_TIERS:
                errors.append(f"invalid_grading_rubric:criterion_tier:{criterion.get('id') or 'unknown'}")
            total_points += max(points, 0.0)
    if criteria and total_points > max_points + 1e-6:
        errors.append("invalid_grading_rubric:criteria_points_exceed_max_points")

    fatal_errors = rubric.get("fatal_errors")
    if isinstance(fatal_errors, list):
        for fatal_error in fatal_errors:
            if not isinstance(fatal_error, dict):
                continue
            try:
                max_grade = float(fatal_error.get("max_grade", 0))
            except (TypeError, ValueError):
                errors.append(f"invalid_grading_rubric:fatal_max_grade:{fatal_error.get('id') or 'unknown'}")
                continue
            if max_grade < 0 or max_grade > min(max_points, 4):
                errors.append(f"invalid_grading_rubric:fatal_max_grade:{fatal_error.get('id') or 'unknown'}")
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
