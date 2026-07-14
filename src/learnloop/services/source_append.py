"""Append reconciliation: safe increments to an existing study map (ING M7, §10).

After the first study map exists, every added source, newly selected unit, or
adopted source revision routes here. This service REUSES all of M6's synthesis
machinery (manifests, span protocol, §8.7 gates, proposal pipeline) with a
different context builder + prompt:

    context = new/changed inventories + brief + a BOUNDED affected neighborhood
              (append_neighborhood.select_neighborhood) — NEVER the full map.

Output is an ``AppendReconciliation`` mapped to the §10.2 intent/storage vocabulary:

    new_coverage                         -> create existing curriculum types
    span_attach / alternate_explanation  -> provenance_link create
    assessment_alignment                 -> provenance_link create (relation=...)
    notation_mapping                     -> notation_mapping create (review)
    conflict                             -> source_conflict create (review)
    restructure_unlocked                 -> update/deactivate (review, lock-checked)

Purity is VERIFIED from item type + payload (the append-vocabulary gate + the
specialized apply handlers), never trusted from the LLM's intent label. Routine
span/assessment attachments that pass §10.3 auto-apply under the vault lock; every
other item stays a pending review proposal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.codex.client import AppendReconciliationContext
from learnloop.codex.prompts import APPEND_RECONCILIATION_PROMPT_VERSION
from learnloop.codex.schemas import (
    SourceSetSynthesis,
    SynthSpanRef,
)
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.append_neighborhood import Neighborhood, select_neighborhood
from learnloop.services.patches import compute_target_hash
from learnloop.services.source_set_synthesis import (
    StudyMapError,
    _collect_inputs,
    _gate_context,
    _normalize,
    _resolve_span_requests,
    _row,
    _span_refs,
)
from learnloop.services.synthesis_gates import GateItem, GateProposal, ProvenanceRef, run_synthesis_gates
from learnloop.services.synthesis_manifests import (
    agent_run_input_context_hash,
    build_manifest,
    persist_manifest,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault, SourceSet
from learnloop.vault.paths import VaultPaths

APPEND_AGENT_PURPOSE = "append_reconciliation"
APPEND_PROPOSAL_PURPOSE = "sourceset_append"

_AUTO_APPLY_RELATIONS = frozenset({"support", "alternate", "assessment_alignment"})


@dataclass
class AppendResult:
    source_set_id: str
    subject_id: str
    change_kind: str
    manifest_hash: str
    synthesis_run_id: str | None = None
    proposal_id: str | None = None
    reused: bool = False
    auto_applied_item_ids: list[str] = field(default_factory=list)
    review_item_ids: list[str] = field(default_factory=list)
    item_counts: dict[str, int] = field(default_factory=dict)
    gate_diagnostics: list[dict[str, Any]] = field(default_factory=list)
    neighborhood: dict[str, Any] = field(default_factory=dict)
    span_request_count: int = 0
    study_map_diff: dict[str, Any] = field(default_factory=dict)
    merge_review_proposals: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_set_id": self.source_set_id,
            "subject_id": self.subject_id,
            "change_kind": self.change_kind,
            "manifest_hash": self.manifest_hash,
            "synthesis_run_id": self.synthesis_run_id,
            "proposal_id": self.proposal_id,
            "reused": self.reused,
            "auto_applied_item_ids": list(self.auto_applied_item_ids),
            "review_item_ids": list(self.review_item_ids),
            "item_counts": dict(self.item_counts),
            "gate_diagnostics": list(self.gate_diagnostics),
            "neighborhood": dict(self.neighborhood),
            "span_request_count": self.span_request_count,
            "study_map_diff": dict(self.study_map_diff),
            "merge_review_proposals": list(self.merge_review_proposals),
        }


# --- orchestration ----------------------------------------------------------


def append_source(
    root: Path,
    source_set_id: str,
    *,
    client: Any,
    new_revision_ids: list[str] | None = None,
    change_kind: str = "source_added",
    revision_diff: dict[str, Any] | None = None,
    brief: dict[str, Any] | None = None,
    auto_apply: bool = True,
    repository: Repository | None = None,
    clock: Clock | None = None,
) -> AppendResult:
    """Run bounded append reconciliation and (by policy) auto-apply routine items."""

    vault = load_vault(root)
    if repository is None:
        # Repository opens a fresh sqlite connection per call; nothing to close.
        repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    return _append(
        vault, repository, root, source_set_id,
        client=client, new_revision_ids=new_revision_ids, change_kind=change_kind,
        revision_diff=revision_diff or {}, brief=brief or {}, auto_apply=auto_apply, clock=clock,
    )


def _append(
    vault: LoadedVault,
    repository: Repository,
    root: Path,
    source_set_id: str,
    *,
    client: Any,
    new_revision_ids: list[str] | None,
    change_kind: str,
    revision_diff: dict[str, Any],
    brief: dict[str, Any],
    auto_apply: bool,
    clock: Clock | None,
) -> AppendResult:
    source_set = next((s for s in vault.source_sets if s.id == source_set_id), None)
    if source_set is None:
        raise StudyMapError("source_set_not_found", f"Source set '{source_set_id}' does not exist.")
    subject_id = source_set.subject_id

    run_method = getattr(client, "run_append_reconciliation", None)
    if run_method is None:
        raise StudyMapError("provider_unavailable", "provider does not implement run_append_reconciliation")

    inputs = _collect_inputs(repository, vault, source_set)
    revs = set(new_revision_ids or inputs.selected_revision_ids)
    new_inventories = [entry for entry in inputs.unit_inventories if entry["revision_id"] in revs]
    new_source_ids = {entry["source_id"] for entry in new_inventories}
    budgets = vault.config.ingest.budgets

    # Deterministic bounded affected-neighborhood selection (§10.1/§3.2).
    neighborhood = select_neighborhood(
        vault, repository, new_inventories,
        budget_tokens=budgets.append_neighborhood_input_tokens,
        source_ids=new_source_ids, revision_ids=revs,
    )

    provider = getattr(client, "provider_name", None) or getattr(client, "provider_type", None) or "codex"
    model = getattr(client, "model", None)
    manifest = build_manifest(
        vault,
        source_set_id=source_set.id,
        membership=inputs.membership,
        revision_ids=sorted(revs),
        extraction_ids=inputs.extraction_ids,
        unit_inventory_versions=inputs.unit_inventory_versions,
        scope={
            "mode": "append",
            "change_kind": change_kind,
            "new_revision_ids": sorted(revs),
            "neighborhood": neighborhood.as_manifest_record(),
        },
        brief=brief,
        prompt_version=APPEND_RECONCILIATION_PROMPT_VERSION,
        provider=provider,
        model=model,
        assessment_schema_version=(inputs.exam_profile or {}).get("schema_version") if inputs.exam_profile else None,
        token_budget={
            "append_neighborhood_input_tokens": budgets.append_neighborhood_input_tokens,
            "append_output_tokens": budgets.append_output_tokens,
        },
        clock=clock,
    )
    manifest_hash = manifest["manifest_hash"]
    persist_manifest(repository, manifest)
    manifest_id = repository.synthesis_manifest_by_hash(manifest_hash)["id"]
    context_hash = agent_run_input_context_hash(manifest)

    cached = repository.completed_agent_run_by_context(APPEND_AGENT_PURPOSE, context_hash)
    if cached is not None:
        batch = repository.proposal_batch_for_agent_run(cached["id"])
        return AppendResult(
            source_set_id=source_set.id, subject_id=subject_id, change_kind=change_kind,
            manifest_hash=manifest_hash, proposal_id=(batch or {}).get("id"), reused=True,
            neighborhood=neighborhood.as_manifest_record(),
        )

    now = utc_now_iso(clock)
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": APPEND_AGENT_PURPOSE,
            "provider": provider,
            "provider_type": getattr(client, "provider_type", "codex"),
            "model": model,
            "prompt_template": "append-reconciliation",
            "prompt_version": APPEND_RECONCILIATION_PROMPT_VERSION,
            "input_context_hash": context_hash,
            "output_schema": "AppendReconciliation",
            "started_at": now,
            "status": "running",
        }
    )
    synthesis_run_id = repository.insert_synthesis_run(
        manifest_id=manifest_id, mode="append", agent_run_id=agent_run_id
    )

    try:
        reconciliation, span_request_count = _run_reconciliation(
            run_method, repository, inputs, new_inventories, neighborhood, source_set,
            subject_id, change_kind, revision_diff, brief, budgets, clock=clock,
        )
        rows, gate_items, conflict_candidates, dispositions, auto_apply_ids = _normalize_append(
            reconciliation, inputs, vault, neighborhood, now, subject_id=subject_id,
        )

        gate_ctx = _gate_context(vault, repository, inputs, [])
        gate_ctx.append_mode = True
        gate_proposal = GateProposal(
            items=gate_items,
            conflict_candidates=conflict_candidates,
            non_conflict_dispositions=dispositions,
        )
        report = run_synthesis_gates(gate_proposal, gate_ctx)
        diagnostics = [d.to_dict() for d in report.diagnostics]
        if report.blocked:
            repository.complete_synthesis_run(synthesis_run_id, status="failed",
                                              coverage_decisions={"gate_diagnostics": diagnostics})
            repository.complete_agent_run(agent_run_id, status="failed",
                                          error_message="append gates hard-failed", clock=clock)
            raise StudyMapError("append_gate_failed", "Append proposal failed hard quality gates.",
                                diagnostics=diagnostics)

        patch_id = new_ulid()
        repository.persist_proposal_batch(
            {
                "id": patch_id,
                "agent_run_id": agent_run_id,
                "purpose": APPEND_PROPOSAL_PURPOSE,
                "source_refs": [],
                "summary": getattr(reconciliation, "summary", "") or f"append reconciliation for {subject_id}",
                "created_at": now,
                "updated_at": now,
            },
            rows,
        )
        repository.complete_synthesis_run(
            synthesis_run_id, status="completed", proposal_id=patch_id,
            coverage_decisions={"gate_diagnostics": diagnostics, "auto_apply_item_ids": auto_apply_ids},
        )
        repository.complete_agent_run(agent_run_id, status="completed", clock=clock)
    except StudyMapError:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        repository.complete_synthesis_run(synthesis_run_id, status="failed")
        repository.complete_agent_run(agent_run_id, status="failed", error_message=str(exc), clock=clock)
        raise

    row_by_client = {r["client_item_id"]: r["id"] for r in rows}
    auto_ids = [row_by_client[c] for c in auto_apply_ids if c in row_by_client]
    review_ids = [r["id"] for r in rows if r["id"] not in set(auto_ids)]

    result = AppendResult(
        source_set_id=source_set.id, subject_id=subject_id, change_kind=change_kind,
        manifest_hash=manifest_hash, synthesis_run_id=synthesis_run_id, proposal_id=patch_id,
        item_counts=_count(rows), gate_diagnostics=diagnostics,
        neighborhood=neighborhood.as_manifest_record(), span_request_count=span_request_count,
        review_item_ids=review_ids,
    )

    # §10.3 auto-apply lane: routine span/assessment attachments apply under the
    # vault lock; everything else stays a pending review proposal.
    if auto_apply and auto_ids:
        from learnloop.services.patches import apply_accepted_items

        snapshot = _snapshot(repository, vault)
        apply_accepted_items(root, patch_id, item_ids=auto_ids, clock=clock)
        result.auto_applied_item_ids = auto_ids
        vault_after = load_vault(root)
        result.study_map_diff = _diff_from_snapshot(repository, vault_after, snapshot, patch_id)
        # Post-append near-duplicate facet doctor pass: merge-review only, never
        # auto-merge (§14). Runs after any new_coverage facets have been applied.
        from learnloop.services.facet_doctor import near_duplicate_facet_review

        result.merge_review_proposals = [
            p.as_dict() for p in near_duplicate_facet_review(vault_after)
        ]
    return result


def _run_reconciliation(
    run_method, repository, inputs, new_inventories, neighborhood, source_set,
    subject_id, change_kind, revision_diff, brief, budgets, *, clock,
):
    context = AppendReconciliationContext(
        source_set_id=source_set.id, subject_id=subject_id, change_kind=change_kind,
        brief=brief, new_inventories=new_inventories, neighborhood=neighborhood.as_context(),
        exam_profile=inputs.exam_profile or {}, revision_diff=revision_diff, resolved_spans=[],
    )
    result = run_method(context)
    if _output_tokens(result) > budgets.append_output_tokens:
        raise StudyMapError("budget_exceeded", "Append reconciliation exceeded its output budget.")
    span_request_count = 0
    requests = [r if isinstance(r, dict) else r.model_dump() for r in getattr(result, "span_requests", []) or []]
    if requests:
        span_request_count = len(requests)
        resolved, _hashes = _resolve_span_requests(
            repository, requests, inputs,
            max_count=budgets.synthesis_span_request_max_count,
            char_cap=budgets.synthesis_span_char_cap,
        )
        context = AppendReconciliationContext(
            source_set_id=source_set.id, subject_id=subject_id, change_kind=change_kind,
            brief=brief, new_inventories=new_inventories, neighborhood=neighborhood.as_context(),
            exam_profile=inputs.exam_profile or {}, revision_diff=revision_diff, resolved_spans=resolved,
        )
        result = run_method(context)
        if _output_tokens(result) > budgets.append_output_tokens:
            raise StudyMapError("budget_exceeded", "Append reconciliation exceeded its output budget.")
    return result, span_request_count


def _output_tokens(result: Any) -> int:
    import json

    payload = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
    return max(1, len(json.dumps(payload, default=str)) // 4)


# --- normalization ----------------------------------------------------------


def _normalize_append(reconciliation, inputs, vault, neighborhood, now, *, subject_id):
    """Map an AppendReconciliation to proposal rows + gate items + auto-apply ids."""

    def d(obj):
        return obj if isinstance(obj, dict) else obj.model_dump()

    # new_coverage reuses the bootstrap normalizer.
    coverage = SourceSetSynthesis(
        concepts=getattr(reconciliation, "concepts", []) or [],
        facets=getattr(reconciliation, "facets", []) or [],
        learning_objects=getattr(reconciliation, "learning_objects", []) or [],
        blueprints=getattr(reconciliation, "blueprints", []) or [],
        practice_items=getattr(reconciliation, "practice_items", []) or [],
    )
    normalized = _normalize(coverage, inputs, vault, now, subject_id=subject_id)
    rows = list(normalized.rows)
    gate_items = list(normalized.gate_items)
    auto_apply_ids: list[str] = []

    # provenance_link items.
    for link in getattr(reconciliation, "provenance_links", []) or []:
        obj = d(link)
        client = obj.get("client_item_id") or f"plink_{new_ulid()[:8]}"
        target_type = obj.get("target_entity_type") or "facet"
        target_id = obj.get("target_entity_id") or ""
        relation = obj.get("relation") or _relation_for_intent(obj.get("reconciliation_intent"))
        gate_refs, yaml_refs, span_ids = _span_refs([obj.get("span") or {}], inputs, default_relation=relation)
        ref = yaml_refs[0] if yaml_refs else {}
        current_hash = compute_target_hash(vault, _hash_type(target_type), target_id)
        payload = {
            "target_entity_type": target_type,
            "target_entity_id": target_id,
            "relation": relation,
            "reconciliation_intent": obj.get("reconciliation_intent") or "span_attach",
            "expected_target_hash": obj.get("expected_target_hash") or current_hash,
            "source_id": ref.get("source_id"),
            "revision_id": ref.get("revision_id"),
            "extraction_id": ref.get("extraction_id"),
            "locator": ref.get("locator"),
            "locator_scheme": ref.get("locator_scheme"),
            "span_hash": ref.get("span_hash"),
            "subject_id": subject_id,
        }
        rows.append(_row("provenance_link", new_ulid(), payload, [], client_id=client, now=now,
                         target_entity_id=target_id, target_entity_type=_target_type(target_type)))
        gate_items.append(
            GateItem(
                client_item_id=client, item_type="provenance_link", operation="create",
                entity_id=None, payload=payload, provenance=gate_refs,
                reconciliation_intent=obj.get("reconciliation_intent"),
            )
        )
        if _auto_applies(payload, gate_refs, vault, current_hash, target_type):
            auto_apply_ids.append(client)

    # notation_mapping items (review-required).
    for mapping in getattr(reconciliation, "notation_mappings", []) or []:
        obj = d(mapping)
        client = obj.get("client_item_id") or f"notation_{new_ulid()[:8]}"
        _gate_refs, yaml_refs, _ = _span_refs([obj.get("span") or {}], inputs, default_relation="support")
        ref = yaml_refs[0] if yaml_refs else {}
        payload = {
            "target_entity_type": obj.get("target_entity_type") or "facet",
            "target_entity_id": obj.get("target_entity_id") or "",
            "canonical_notation": obj.get("canonical_notation") or "",
            "alternate_notation": obj.get("alternate_notation") or "",
            "context": obj.get("context"),
            "source_id": ref.get("source_id"),
            "revision_id": ref.get("revision_id"),
            "locator": ref.get("locator"),
            "subject_id": subject_id,
        }
        rows.append(_row("notation_mapping", new_ulid(), payload, [], client_id=client, now=now))
        gate_items.append(
            GateItem(client_item_id=client, item_type="notation_mapping", operation="create",
                     entity_id=None, payload=payload)
        )

    # source_conflict items (always reviewed).
    conflict_candidates = list(getattr(reconciliation, "conflict_candidates", []) or [])
    for conflict in getattr(reconciliation, "conflicts", []) or []:
        obj = d(conflict)
        client = obj.get("client_item_id") or f"conflict_{new_ulid()[:8]}"
        left = _span_yaml(obj.get("left"), inputs)
        right = _span_yaml(obj.get("right"), inputs)
        payload = {
            "entity_type": obj.get("entity_type") or "facet",
            "entity_id": obj.get("entity_id") or "",
            "statement": obj.get("statement") or "",
            "left": left,
            "right": right,
            "candidate_id": client,
            "subject_id": subject_id,
        }
        rows.append(_row("source_conflict", new_ulid(), payload, [], client_id=client, now=now))
        gate_items.append(
            GateItem(client_item_id=client, item_type="source_conflict", operation="create",
                     entity_id=None, payload=payload)
        )

    # restructure_unlocked items (update/deactivate, review + lock-checked).
    for restructure in getattr(reconciliation, "restructures", []) or []:
        obj = d(restructure)
        client = obj.get("client_item_id") or f"restructure_{new_ulid()[:8]}"
        target_type = obj.get("target_entity_type") or "learning_object"
        target_id = obj.get("target_entity_id") or ""
        operation = obj.get("operation") or "update"
        payload = dict(obj.get("payload") or {})
        payload["id"] = target_id
        payload["expected_target_hash"] = obj.get("expected_target_hash")
        row = _row(target_type, target_id, payload, [], client_id=client, now=now)
        row["operation"] = operation
        rows.append(row)
        gate_items.append(
            GateItem(client_item_id=client, item_type=target_type, operation=operation,
                     entity_id=target_id, payload=payload, reconciliation_intent="restructure_unlocked")
        )

    return rows, gate_items, conflict_candidates, set(getattr(reconciliation, "non_conflict_dispositions", []) or []), auto_apply_ids


def _relation_for_intent(intent: str | None) -> str:
    return {
        "span_attach": "support",
        "alternate_explanation": "alternate",
        "assessment_alignment": "assessment_alignment",
    }.get(str(intent or ""), "support")


def _hash_type(target_type: str) -> str:
    return "learning_object" if target_type == "task_blueprint" else target_type


def _target_type(target_type: str) -> str:
    valid = {"learning_object", "practice_item", "concept", "concept_edge", "rubric",
             "error_type", "facet", "task_blueprint", "provenance_link", "notation_mapping", "source_conflict"}
    return target_type if target_type in valid else None


def _auto_applies(payload, gate_refs, vault, current_hash, target_type) -> bool:
    """§10.3 auto-apply predicate for a provenance_link.

    span_attach/alternate: target hash still matches, every cited span resolves in
    scope, relation not already present, nothing removed/replaced.
    assessment_alignment: only to task/blueprint metadata or provenance, never to a
    facet semantic contract."""

    relation = payload["relation"]
    if relation not in _AUTO_APPLY_RELATIONS:
        return False
    if not payload.get("locator") or not payload.get("target_entity_id"):
        return False
    if relation == "assessment_alignment":
        return target_type in {"task_blueprint", "learning_object", "practice_item"}
    # expected target hash must still match the live entity (nothing changed).
    expected = payload.get("expected_target_hash")
    if expected is not None and current_hash is not None and expected != current_hash:
        return False
    if current_hash is None:  # target does not exist -> cannot auto-attach
        return False
    # every cited span must have resolved (gate_refs carry validated ids).
    if not gate_refs or any(not r.span_id for r in gate_refs):
        return False
    # Relation-not-already-present + nothing-removed are guaranteed structurally:
    # the entity_source_links insert is INSERT OR IGNORE on the UNIQUE relation key,
    # and the handler only ever inserts a row (never rewrites the target YAML).
    return True


def _span_yaml(span, inputs) -> dict[str, Any]:
    if span is None:
        return {}
    _refs, yaml_refs, _ = _span_refs([span if isinstance(span, dict) else span.model_dump()], inputs, default_relation="support")
    return yaml_refs[0] if yaml_refs else {}


def _count(rows) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["item_type"]] = counts.get(row["item_type"], 0) + 1
    return counts


# --- study-map diff snapshot ------------------------------------------------


def _snapshot(repository: Repository, vault: LoadedVault) -> dict[str, Any]:
    return {
        "facets": set(vault.evidence_facets.keys()),
        "links": _link_count(repository),
        "open_conflicts": len(repository.source_conflicts_by_status("open")),
        "stale_links": len(repository.stale_entity_source_links()),
        "notations": len(repository.all_notation_mappings()),
    }


def _link_count(repository: Repository) -> int:
    with repository.connection() as connection:
        return int(connection.execute("SELECT COUNT(*) AS n FROM entity_source_links").fetchone()["n"])


def _diff_from_snapshot(repository, vault_after, before, patch_id) -> dict[str, Any]:
    from learnloop.services.study_map_diff import compute_study_map_diff

    return compute_study_map_diff(repository, vault_after, before, patch_id)
