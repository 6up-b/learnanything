"""Bootstrap synthesis: brief -> sharded synthesis -> dependency-closed proposal
-> applied study map (source-ingestion v2 §8, ING M6).

This service orchestrates the "Create study map" journey:

1. lock check — bootstrap is legal only where nothing touched is identity-locked
   (§8.2 enforcement 1; typed refusal ``subject_identity_locked``);
2. immutable manifest persisted BEFORE the agent run (§8.4; the manifest hash is
   the ``agent_runs.input_context_hash`` cache seam — an identical manifest reuses
   the completed run);
3. sharded N-way synthesis over role-specific unit inventories (NOT raw
   documents) + brief + exam assessment-alignment lane (aggregates + cited task
   metadata only; held-out wording NEVER); one bounded span-request round;
4. deterministic §8.7 quality gates including the real synthesis-time
   identifiability analysis (§11.3); hard fails abort before persisting;
5. a dependency-annotated proposal persisted through the existing pipeline
   (purpose ``sourceset_bootstrap``); acceptance is atomic under the vault lock;
6. optional Goal creation for exam-preparation briefs, wired after acceptance.

The LLM never writes files: everything flows AuthoringProposal-shaped rows ->
proposed_patch_items -> apply_accepted_items.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.codex.client import SourceSetSynthesisContext
from learnloop.codex.prompts import SOURCE_SET_SYNTHESIS_PROMPT_VERSION
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid, snake_case
from learnloop.services.exam_profile import ExamUnitEntry, aggregate_exam_profile
from learnloop.services.identifiability import analyze_identifiability, build_proposal_view
from learnloop.services.role_authority import role_authority
from learnloop.services.source_outline import resolve_extraction_id
from learnloop.services.source_unit_inventory import profile_satisfies
from learnloop.services.synthesis_gates import (
    GateContext,
    GateDiagnostic,
    GateItem,
    GateProposal,
    ProvenanceRef,
    run_synthesis_gates,
)
from learnloop.services.synthesis_manifests import (
    agent_run_input_context_hash,
    build_manifest,
    persist_manifest,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault, SourceSet
from learnloop.vault.paths import VaultPaths

SYNTHESIS_AGENT_PURPOSE = "source_set_synthesis"
BOOTSTRAP_PROPOSAL_PURPOSE = "sourceset_bootstrap"

# Roles allowed to support a canonical semantic claim (mirror of the gate set).
_SEMANTIC_ROLES = frozenset(
    {"primary_textbook", "lecture", "paper", "reference", "alternate_explanation"}
)


class StudyMapError(ValueError):
    """A typed bootstrap-synthesis failure (lock refusal / gate hard-fail)."""

    def __init__(self, code: str, message: str, *, diagnostics: list[dict[str, Any]] | None = None,
                 lock_reasons: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.code = code
        self.diagnostics = diagnostics or []
        self.lock_reasons = lock_reasons or []


@dataclass
class StudyMapResult:
    source_set_id: str
    subject_id: str
    mode: str
    manifest_hash: str
    synthesis_run_id: str | None = None
    proposal_id: str | None = None
    reused: bool = False
    applied: bool = False
    goal_id: str | None = None
    item_counts: dict[str, int] = field(default_factory=dict)
    gate_diagnostics: list[dict[str, Any]] = field(default_factory=list)
    generation_needs: list[dict[str, Any]] = field(default_factory=list)
    span_request_count: int = 0
    resolved_span_hashes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_set_id": self.source_set_id,
            "subject_id": self.subject_id,
            "mode": self.mode,
            "manifest_hash": self.manifest_hash,
            "synthesis_run_id": self.synthesis_run_id,
            "proposal_id": self.proposal_id,
            "reused": self.reused,
            "applied": self.applied,
            "goal_id": self.goal_id,
            "item_counts": dict(self.item_counts),
            "gate_diagnostics": list(self.gate_diagnostics),
            "generation_needs": list(self.generation_needs),
            "span_request_count": self.span_request_count,
            "resolved_span_hashes": list(self.resolved_span_hashes),
        }


# --- input assembly ---------------------------------------------------------


@dataclass
class _SynthesisInputs:
    unit_inventories: list[dict[str, Any]]
    exam_profile: dict[str, Any] | None
    held_out_span_ids: set[str]
    selected_revision_ids: list[str]
    extraction_ids: list[str]
    extraction_units: dict[str, set[str]]
    extraction_spans: dict[str, set[str]]
    membership: list[dict[str, Any]]
    unit_inventory_versions: dict[str, str]
    span_origin: dict[str, dict[str, str]]  # extraction_id -> {source_id, revision_id, role}


def _best_inventory(rows: list[dict[str, Any]], unit_id: str, requested_profile: str) -> dict[str, Any] | None:
    candidates = [row for row in rows if row["unit_id"] == unit_id]
    if not candidates:
        return None
    satisfying = [
        row
        for row in candidates
        if profile_satisfies(row["inventory_profile"], row["inventory_schema_version"], requested_profile)
    ]
    pool = satisfying or candidates
    pool.sort(key=lambda row: (row["inventory_profile"] != "combined", row["inventory_profile"]))
    return pool[0]


def _assessment_signal_spans(inventory: dict[str, Any], *, held_out_only: bool) -> set[str]:
    spans: set[str] = set()
    for signal in inventory.get("assessment_signals", []) or []:
        if held_out_only and not signal.get("held_out"):
            continue
        for span_id in signal.get("span_ids", []) or []:
            spans.add(str(span_id))
    return spans


def _collect_inputs(repo: Repository, vault: LoadedVault, source_set: SourceSet) -> _SynthesisInputs:
    unit_inventories: list[dict[str, Any]] = []
    exam_entries: list[ExamUnitEntry] = []
    held_out_span_ids: set[str] = set()
    selected_revision_ids: list[str] = []
    extraction_ids: list[str] = []
    extraction_units: dict[str, set[str]] = {}
    extraction_spans: dict[str, set[str]] = {}
    membership: list[dict[str, Any]] = []
    unit_inventory_versions: dict[str, str] = {}
    span_origin: dict[str, dict[str, str]] = {}

    for member in source_set.members:
        extraction_id = resolve_extraction_id(repo, member.revision_id)
        membership.append(
            {
                "source_id": member.source_id,
                "revision_id": member.revision_id,
                "role": member.default_role,
                "priority": member.priority,
            }
        )
        if member.revision_id not in selected_revision_ids:
            selected_revision_ids.append(member.revision_id)
        if extraction_id is None:
            continue
        if extraction_id not in extraction_ids:
            extraction_ids.append(extraction_id)
        span_origin[extraction_id] = {
            "source_id": member.source_id,
            "revision_id": member.revision_id,
            "role": member.default_role,
        }
        ir = repo.load_document_ir(extraction_id)
        if ir is not None:
            extraction_units.setdefault(extraction_id, set()).update(u.unit_id for u in ir.units)
            extraction_spans.setdefault(extraction_id, set()).update(b.span_id for b in ir.blocks)
        rows = repo.unit_inventories_for_revision(member.revision_id)
        scope_units = [scope.unit_id for scope in member.scope]
        if not scope_units and ir is not None:
            scope_units = [u.unit_id for u in ir.units]
        role_overrides = {s.unit_id: s.role_override for s in member.scope if s.role_override}
        selection = repo.get_unit_selection(extraction_id)
        exam_use_modes = (selection or {}).get("exam_use_modes", {}) if selection else {}
        paper_metadata = (selection or {}).get("exam_paper_metadata", {}) if selection else {}

        for unit_id in scope_units:
            effective_role = role_overrides.get(unit_id, member.default_role)
            authority = role_authority(effective_role)
            row = _best_inventory(rows, unit_id, "combined")
            if row is None:
                continue
            inventory = row["inventory"]
            unit_inventory_versions[f"{member.revision_id}:{unit_id}"] = str(
                row.get("inventory_schema_version")
            ) + "|" + str(row.get("prompt_version"))
            # Assessment-alignment lane: exam-role units contribute ONLY through
            # the aggregate exam profile + cited task metadata. Their raw
            # inventory is never placed in the synthesis context, and every
            # held-out span id is fed to the leakage gate.
            if effective_role == "exam" and authority.assessment_alignment and not authority.semantic_contract:
                exam_entries.append(
                    ExamUnitEntry(unit_id=unit_id, inventory=inventory, paper_metadata=paper_metadata)
                )
                whole_unit = exam_use_modes.get(unit_id) == "held_out_evaluation"
                spans = _assessment_signal_spans(inventory, held_out_only=not whole_unit)
                # Namespace by extraction: span ids are unique only within a run.
                held_out_span_ids |= {f"{extraction_id}:{span}" for span in spans}
                continue
            unit_inventories.append(
                {
                    "extraction_id": extraction_id,
                    "revision_id": member.revision_id,
                    "source_id": member.source_id,
                    "unit_id": unit_id,
                    "role": effective_role,
                    "semantic_authority": authority.semantic_contract,
                    "inventory": inventory,
                }
            )

    exam_profile = aggregate_exam_profile(exam_entries).as_dict() if exam_entries else None
    return _SynthesisInputs(
        unit_inventories=unit_inventories,
        exam_profile=exam_profile,
        held_out_span_ids=held_out_span_ids,
        selected_revision_ids=selected_revision_ids,
        extraction_ids=extraction_ids,
        extraction_units=extraction_units,
        extraction_spans=extraction_spans,
        membership=membership,
        unit_inventory_versions=unit_inventory_versions,
        span_origin=span_origin,
    )


def _registry_index(vault: LoadedVault) -> dict[str, Any]:
    """A compact existing-registry index for the prompt (never full contracts)."""

    return {
        "facets": sorted(vault.evidence_facets.keys()),
        "concepts": sorted(vault.concepts.keys()),
        "learning_objects": sorted(vault.learning_objects.keys()),
    }


def _shards(unit_inventories: list[dict[str, Any]], shard_input_tokens: int) -> list[list[dict[str, Any]]]:
    if not unit_inventories:
        return [[]]
    shards: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    budget = 0
    for entry in unit_inventories:
        estimate = max(1, len(json.dumps(entry, default=str)) // 4)
        if current and budget + estimate > shard_input_tokens:
            shards.append(current)
            current = []
            budget = 0
        current.append(entry)
        budget += estimate
    if current:
        shards.append(current)
    return shards or [[]]


# --- span-request round -----------------------------------------------------


def _resolve_span_requests(
    repo: Repository,
    requests: list[dict[str, Any]],
    inputs: _SynthesisInputs,
    *,
    max_count: int,
    char_cap: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    """One bounded span-request round (§8.5). Resolves ONLY spans in selected
    revisions/units, enforcing the request-count / per-span char caps."""

    resolved: list[dict[str, Any]] = []
    hashes: list[str] = []
    import hashlib

    valid_units = inputs.extraction_units
    for request in requests[:max_count]:
        extraction_id = str(request.get("extraction_id") or "")
        unit_id = str(request.get("unit_id") or "")
        span_id = str(request.get("span_id") or "")
        if extraction_id not in inputs.extraction_ids:
            continue
        if unit_id and unit_id not in valid_units.get(extraction_id, set()):
            continue
        if span_id not in inputs.extraction_spans.get(extraction_id, set()):
            continue
        ir = repo.load_document_ir(extraction_id)
        if ir is None:
            continue
        block = ir.block_by_span(span_id)
        if block is None:
            continue
        text = (block.text or "")[:char_cap]
        digest = "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        resolved.append(
            {
                "extraction_id": extraction_id,
                "unit_id": unit_id,
                "span_id": span_id,
                "purpose": request.get("purpose", ""),
                "text": text,
                "span_hash": digest,
            }
        )
        hashes.append(digest)
    return resolved, hashes


# --- normalization into proposal rows + gate items --------------------------


def _slug(prefix: str, text: str, fallback: str) -> str:
    core = snake_case(text)[:48] if text else ""
    return f"{prefix}_{core}" if core else f"{prefix}_{fallback}"


@dataclass
class _Normalized:
    rows: list[dict[str, Any]]
    gate_items: list[GateItem]
    conflict_candidates: list[str]
    non_conflict_dispositions: set[str]
    facet_payloads: list[dict[str, Any]]
    criterion_targets: list[dict[str, Any]]
    recipe_components: list[dict[str, Any]]
    facet_ids: list[str]


def _span_refs(
    refs: list[Any], inputs: _SynthesisInputs, *, default_relation: str
) -> tuple[list[ProvenanceRef], list[dict[str, Any]], list[str]]:
    """Build gate ProvenanceRefs + YAML source_refs from synth span refs.

    Role/source/revision are resolved from the citation's extraction (untrusted-
    text discipline: never trust the model's claimed role)."""

    from learnloop.ingest.locators import BLOCK_SPAN_V1, format_block_span

    gate_refs: list[ProvenanceRef] = []
    yaml_refs: list[dict[str, Any]] = []
    span_ids: list[str] = []
    for ref in refs or []:
        ref = ref if isinstance(ref, dict) else ref.model_dump()
        extraction_id = str(ref.get("extraction_id") or "")
        span_id = str(ref.get("span_id") or "")
        unit_id = str(ref.get("unit_id") or "")
        origin = inputs.span_origin.get(extraction_id, {})
        role = origin.get("role", ref.get("role") or "reference")
        source_id = origin.get("source_id", ref.get("source_id") or "")
        revision_id = origin.get("revision_id", ref.get("revision_id") or "")
        relation = ref.get("relation") or default_relation
        namespaced = f"{extraction_id}:{span_id}"
        held_out = namespaced in inputs.held_out_span_ids
        gate_refs.append(
            ProvenanceRef(
                extraction_id=extraction_id,
                revision_id=revision_id,
                unit_id=unit_id,
                span_id=span_id,
                relation=relation,
                role=role,
                held_out=held_out,
            )
        )
        yaml_refs.append(
            {
                "ref_type": "canonical_source",
                "ref_id": source_id,
                "source_id": source_id,
                "revision_id": revision_id,
                "extraction_id": extraction_id,
                "locator": ref.get("locator") or format_block_span(extraction_id, span_id),
                "locator_scheme": BLOCK_SPAN_V1,
                "relation": relation if relation in {"primary", "support", "alternate", "exercise", "assessment_alignment"} else "support",
                "role": role,
                "span_hash": ref.get("span_hash"),
            }
        )
        if span_id:
            span_ids.append(namespaced)
    return gate_refs, yaml_refs, span_ids


def _normalize(synth: Any, inputs: _SynthesisInputs, vault: LoadedVault, now: str, *, subject_id: str) -> _Normalized:
    rows: list[dict[str, Any]] = []
    gate_items: list[GateItem] = []
    facet_payloads: list[dict[str, Any]] = []
    criterion_targets: list[dict[str, Any]] = []
    recipe_components: list[dict[str, Any]] = []

    def d(obj: Any) -> dict[str, Any]:
        return obj if isinstance(obj, dict) else obj.model_dump()

    # id assignment maps: client_item_id -> entity id
    concept_ids: dict[str, str] = {}
    facet_client_to_id: dict[str, str] = {}
    lo_client_to_id: dict[str, str] = {}

    used_ids: set[str] = set()

    def unique(candidate: str) -> str:
        base = candidate
        n = 2
        while candidate in used_ids:
            candidate = f"{base}_{n}"
            n += 1
        used_ids.add(candidate)
        return candidate

    # concepts
    for concept in getattr(synth, "concepts", []) or []:
        c = d(concept)
        cid = c.get("id") or _slug("concept", c.get("title", ""), new_ulid()[:8])
        cid = unique(str(cid))
        ckey = c.get("client_item_id") or cid
        concept_ids[ckey] = cid
        payload = {"id": cid, "title": c.get("title") or cid, "type": c.get("type") or "concept",
                   "description": c.get("description") or ""}
        rows.append(_row("concept", cid, payload, [], client_id=ckey, now=now))
        gate_items.append(GateItem(client_item_id=ckey, item_type="concept",
                                   entity_id=cid, payload=payload, establishes_semantic=False))

    # facets
    for facet in getattr(synth, "facets", []) or []:
        f = d(facet)
        client = f.get("client_item_id") or ""
        fid = f.get("id") or _slug("facet", f.get("claim", ""), new_ulid()[:8])
        fid = unique(str(fid))
        fkey = client or fid
        facet_client_to_id[fkey] = fid
        concept_client = f.get("concept_client_id") or ""
        concept_id = concept_ids.get(concept_client) or f.get("concept_id") or ""
        gate_refs, yaml_refs, _spans = _span_refs(f.get("provenance", []), inputs, default_relation="primary")
        payload = {
            "id": fid,
            "concept_id": concept_id or None,
            "kind": f.get("kind") or "definition",
            "claim": f.get("claim") or "",
            "preconditions": f.get("preconditions") or [],
            "postconditions": f.get("postconditions") or [],
            "applicability": f.get("applicability") or [],
            "positive_examples": f.get("positive_examples") or [],
            "negative_examples": f.get("negative_examples") or [],
            "non_goals": f.get("non_goals") or [],
            "error_signatures": f.get("error_signatures") or [],
            "instructional_repairs": f.get("instructional_repairs") or [],
            "aliases": f.get("aliases") or [],
            "status": "reviewed",
            "provenance": {"origin": "sourceset_synthesis", "source_refs": yaml_refs},
        }
        facet_payloads.append(payload)
        deps = [concept_client] if concept_client and concept_client in concept_ids else []
        rows.append(_row("facet", fid, payload, deps, client_id=fkey, now=now))
        gate_items.append(
            GateItem(
                client_item_id=fkey,
                item_type="facet",
                entity_id=fid,
                payload=payload,
                depends_on=deps,
                provenance=gate_refs,
                establishes_semantic=True,
            )
        )

    # learning objects
    for lo in getattr(synth, "learning_objects", []) or []:
        obj = d(lo)
        client = obj.get("client_item_id") or ""
        oid = obj.get("id") or _slug("lo", obj.get("title", ""), new_ulid()[:8])
        oid = unique(str(oid))
        lokey = client or oid
        lo_client_to_id[lokey] = oid
        concept_client = obj.get("concept_client_id") or ""
        concept_id = (
            concept_ids.get(concept_client)
            or obj.get("concept_id")
            or _slug("concept", obj.get("title", ""), oid)
        )
        gate_refs, yaml_refs, _spans = _span_refs(obj.get("provenance", []), inputs, default_relation="primary")
        payload = {
            "id": oid,
            "concept_id": concept_id or None,
            "title": obj.get("title") or oid,
            "summary": obj.get("summary") or "",
            "subjects": [subject_id],
            "knowledge_type": obj.get("knowledge_type") or "concept",
            "prerequisites": obj.get("prerequisites") or [],
            "provenance": {"origin": "codex_proposal", "source_refs": yaml_refs},
        }
        deps = [concept_client] if concept_client and concept_client in concept_ids else []
        rows.append(_row("learning_object", oid, payload, deps, client_id=lokey, now=now))
        gate_items.append(
            GateItem(
                client_item_id=lokey,
                item_type="learning_object",
                entity_id=oid,
                payload=payload,
                depends_on=deps,
                provenance=gate_refs,
                establishes_semantic=True,
            )
        )

    # blueprints (task_blueprint items merged onto their LO)
    for blueprint in getattr(synth, "blueprints", []) or []:
        bp = d(blueprint)
        client = bp.get("client_item_id") or ""
        bid = bp.get("id") or _slug("bp", "", new_ulid()[:8])
        bid = unique(str(bid))
        lo_client = bp.get("learning_object_client_id") or ""
        lo_id = lo_client_to_id.get(lo_client) or bp.get("learning_object_id") or ""
        recipes_payload: list[dict[str, Any]] = []
        gate_recipes: list[dict[str, Any]] = []
        facet_deps: list[str] = []
        for recipe in bp.get("recipes", []) or []:
            r = recipe if isinstance(recipe, dict) else recipe.model_dump()
            comps_out: list[dict[str, Any]] = []
            flat_facets: list[str] = []
            for slot in ("all_of", "any_of"):
                for comp in r.get(slot) or []:
                    cm = comp if isinstance(comp, dict) else comp.model_dump()
                    fclient = cm.get("facet_client_id") or ""
                    facet_id = facet_client_to_id.get(fclient) or cm.get("facet") or ""
                    capability = cm.get("capability") or "retrieval"
                    comps_out.append({"facet": facet_id, "capability": capability, "modality": cm.get("modality") or "hard", "_slot": slot})
                    flat_facets.append(facet_id)
                    recipe_components.append({"facet": facet_id, "capability": capability})
                    if fclient in facet_client_to_id and fclient not in facet_deps:
                        facet_deps.append(fclient)
            integration = r.get("integration")
            integ_out = None
            if integration:
                im = integration if isinstance(integration, dict) else integration.model_dump()
                fclient = im.get("facet_client_id") or ""
                facet_id = facet_client_to_id.get(fclient) or im.get("facet") or ""
                integ_out = {"facet": facet_id, "capability": im.get("capability") or "coordination", "modality": "hard"}
                flat_facets.append(facet_id)
                recipe_components.append({"facet": facet_id, "capability": im.get("capability") or "coordination"})
                if fclient in facet_client_to_id and fclient not in facet_deps:
                    facet_deps.append(fclient)
            recipe_row = {
                "id": r.get("id") or f"recipe_{new_ulid()[:8]}",
                "composition": r.get("composition") or "conjunctive",
                "all_of": [{"facet": c["facet"], "capability": c["capability"], "modality": c["modality"]} for c in comps_out if c["_slot"] == "all_of"],
                "any_of": [{"facet": c["facet"], "capability": c["capability"], "modality": c["modality"]} for c in comps_out if c["_slot"] == "any_of"],
            }
            if integ_out:
                recipe_row["integration"] = integ_out
            recipes_payload.append(recipe_row)
            gate_recipes.append({**recipe_row, "facets": flat_facets})
        payload = {"id": bid, "learning_object_id": lo_id, "weight": bp.get("weight", 1.0), "recipes": recipes_payload}
        deps = ([lo_client] if lo_client in lo_client_to_id else []) + facet_deps
        rows.append(_row("task_blueprint", bid, payload, deps, client_id=client or bid, now=now,
                         target_entity_id=lo_id, target_entity_type="learning_object"))
        gate_items.append(
            GateItem(
                client_item_id=client or bid,
                item_type="task_blueprint",
                entity_id=bid,
                payload={"blueprints": [{"id": bid, "weight": bp.get("weight", 1.0), "recipes": gate_recipes}]},
                depends_on=deps,
                establishes_semantic=False,
            )
        )

    # practice items (+ rubric criteria)
    for item in getattr(synth, "practice_items", []) or []:
        pi = d(item)
        client = pi.get("client_item_id") or ""
        pid = pi.get("id") or _slug("pi", pi.get("prompt", "")[:24], new_ulid()[:8])
        pid = unique(str(pid))
        lo_client = pi.get("learning_object_client_id") or ""
        lo_id = lo_client_to_id.get(lo_client) or pi.get("learning_object_id") or ""
        evidence_facets: list[str] = []
        for fc in pi.get("evidence_facet_client_ids") or []:
            evidence_facets.append(facet_client_to_id.get(fc, fc))
        for f in pi.get("evidence_facets") or []:
            if f not in evidence_facets:
                evidence_facets.append(f)
        criteria_payload: list[dict[str, Any]] = []
        for criterion in pi.get("criteria", []) or []:
            c = criterion if isinstance(criterion, dict) else criterion.model_dump()
            targets_out: list[dict[str, Any]] = []
            for target in c.get("targets", []) or []:
                t = target if isinstance(target, dict) else target.model_dump()
                fclient = t.get("facet_client_id") or ""
                facet_id = facet_client_to_id.get(fclient) or t.get("facet") or ""
                capability = t.get("capability") or "retrieval"
                role = t.get("role") or "primary"
                targets_out.append({"facet": facet_id, "capability": capability, "role": role})
                criterion_targets.append(
                    {
                        "criterion_id": c.get("id") or "",
                        "correlation_group": c.get("correlation_group") or "",
                        "facet": facet_id,
                        "capability": capability,
                        "role": role,
                    }
                )
            criteria_payload.append(
                {
                    "id": c.get("id") or f"crit_{new_ulid()[:6]}",
                    "points": c.get("points", 1.0),
                    "description": c.get("description") or "",
                    "tier": c.get("tier") or "core",
                    "targets": targets_out,
                    "depends_on": c.get("depends_on") or [],
                    "recipe_ids": c.get("recipe_ids") or [],
                    "correlation_group": c.get("correlation_group") or None,
                }
            )
        gate_refs, yaml_refs, span_ids = _span_refs(pi.get("provenance", []), inputs, default_relation="exercise")
        fp = pi.get("evidence_fingerprint") or {}
        fp = fp if isinstance(fp, dict) else fp.model_dump()
        rubric = {"max_points": 4, "criteria": criteria_payload, "fatal_errors": []}
        payload = {
            "id": pid,
            "learning_object_id": lo_id,
            "practice_mode": pi.get("practice_mode") or "retrieval",
            "prompt": pi.get("prompt") or "",
            "expected_answer": pi.get("expected_answer") or "",
            "evidence_facets": evidence_facets,
            "grading_rubric": rubric if criteria_payload else None,
            "retrieval_demand": pi.get("retrieval_demand", 0.5),
            "transfer_distance": pi.get("transfer_distance", 0.0),
            "scaffold_level": pi.get("scaffold_level", 0.0),
            "surface_family": pi.get("surface_family") or "source_form",
            "repair_targets": evidence_facets or None,
            "evidence_fingerprint": {k: v for k, v in fp.items() if v},
            "provenance": {"origin": "codex_proposal", "source_refs": yaml_refs},
        }
        deps = ([lo_client] if lo_client in lo_client_to_id else [])
        for fc in pi.get("evidence_facet_client_ids") or []:
            if fc in facet_client_to_id and fc not in deps:
                deps.append(fc)
        extra = list(pi.get("depends_on_client_item_ids") or [])
        for dep in extra:
            if dep not in deps:
                deps.append(dep)
        rows.append(_row("practice_item", pid, payload, deps, client_id=client or pid, now=now))
        gate_items.append(
            GateItem(
                client_item_id=client or pid,
                item_type="practice_item",
                entity_id=pid,
                payload={"criteria": criteria_payload, "grading_rubric": rubric},
                depends_on=deps,
                provenance=gate_refs,
                is_teaching_or_practice=True,
                embedded_span_ids=span_ids,
            )
        )

    conflict_candidates = [str(c.get("entity_client_id") or c.get("statement") or "")
                           for c in (d(x) for x in getattr(synth, "conflicts", []) or [])]
    dispositions = set(getattr(synth, "non_conflict_dispositions", []) or [])

    return _Normalized(
        rows=rows,
        gate_items=gate_items,
        conflict_candidates=[c for c in conflict_candidates if c],
        non_conflict_dispositions=dispositions,
        facet_payloads=facet_payloads,
        criterion_targets=criterion_targets,
        recipe_components=recipe_components,
        facet_ids=list(facet_client_to_id.values()),
    )


def resolve_subject_id(source_set: Any, vault: LoadedVault) -> str:
    """The subject a synthesized study map belongs to: the source set's own
    subject_id (§4.3 — sets are subject-scoped), never "first subject in the
    vault", which misfires on multi-subject vaults and crashes on fresh ones."""

    sid = getattr(source_set, "subject_id", None) or (
        source_set.get("subject_id") if isinstance(source_set, dict) else None
    )
    if sid:
        return str(sid)
    if vault.subjects:
        return next(iter(vault.subjects.keys()))
    raise StudyMapError(
        "missing_subject", "source set has no subject_id and the vault has no subjects"
    )


def _row(item_type: str, entity_id: str, payload: dict[str, Any], depends_on: list[str],
         *, client_id: str, now: str, target_entity_id: str | None = None,
         target_entity_type: str | None = None) -> dict[str, Any]:
    return {
        "id": new_ulid(),
        "client_item_id": client_id,
        "item_type": item_type,
        "operation": "create",
        "target_entity_type": target_entity_type if target_entity_id else None,
        "target_entity_id": target_entity_id,
        "payload": payload,
        "source_ref_ids": [],
        "audit": None,
        "decision": "pending",
        "validation_status": "valid",
        "validation_errors": [],
        "depends_on_client_item_ids": list(depends_on),
        "dependency_status": "pending",
        "created_at": now,
        "updated_at": now,
    }


# --- lock refusal -----------------------------------------------------------


def _bootstrap_lock_refusal(vault: LoadedVault, repository: Repository) -> list[dict[str, Any]]:
    """§8.2 enforcement 1: bootstrap is legal only where nothing is identity-locked."""

    from learnloop.services.curriculum_locks import identity_locks

    locked = identity_locks(vault, repository)
    reasons: list[dict[str, Any]] = []
    for facet_id, lock_reasons in locked.items():
        for reason in lock_reasons:
            reasons.append(
                {
                    "facet_id": facet_id,
                    "source": reason.source,
                    "entity_type": reason.entity_type,
                    "entity_id": reason.entity_id,
                    "detail": reason.detail,
                }
            )
    return reasons


# --- orchestration ----------------------------------------------------------


def create_study_map(
    root: Path,
    source_set_id: str,
    *,
    client: Any,
    brief: dict[str, Any] | None = None,
    mode: str = "auto",
    apply: bool = False,
    create_goal: bool = False,
    repository: Repository | None = None,
    clock: Clock | None = None,
) -> StudyMapResult:
    vault = load_vault(root)
    if repository is None:
        # Repository opens a fresh sqlite connection per call; nothing to close.
        repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    return _create_study_map(
        vault, repository, root, source_set_id,
        client=client, brief=brief or {}, mode=mode, apply=apply,
        create_goal=create_goal, clock=clock,
    )


def _create_study_map(
    vault: LoadedVault,
    repository: Repository,
    root: Path,
    source_set_id: str,
    *,
    client: Any,
    brief: dict[str, Any],
    mode: str,
    apply: bool,
    create_goal: bool,
    clock: Clock | None,
) -> StudyMapResult:
    source_set = next((s for s in vault.source_sets if s.id == source_set_id), None)
    if source_set is None:
        raise StudyMapError("source_set_not_found", f"Source set '{source_set_id}' does not exist.")
    subject_id = source_set.subject_id

    resolved_mode = "bootstrap" if mode in {"auto", "bootstrap"} else mode
    if resolved_mode != "bootstrap":
        raise StudyMapError("unsupported_mode", f"mode '{mode}' is not supported by create_study_map (append is ING M7).")

    run_method = getattr(client, "run_source_set_synthesis", None)
    if run_method is None:
        raise StudyMapError("provider_unavailable", "synthesis provider does not implement run_source_set_synthesis")

    # 1. lock check — typed refusal for a locked subject.
    lock_reasons = _bootstrap_lock_refusal(vault, repository)
    if lock_reasons:
        raise StudyMapError(
            "subject_identity_locked",
            f"Bootstrap synthesis refused: subject '{subject_id}' has locked identities.",
            lock_reasons=lock_reasons,
        )

    inputs = _collect_inputs(repository, vault, source_set)
    budgets = vault.config.ingest.budgets

    # 2. immutable manifest BEFORE the agent run.
    provider = getattr(client, "provider_name", None) or getattr(client, "provider_type", None) or "codex"
    model = getattr(client, "model", None)
    manifest = build_manifest(
        vault,
        source_set_id=source_set.id,
        membership=inputs.membership,
        revision_ids=inputs.selected_revision_ids,
        extraction_ids=inputs.extraction_ids,
        unit_inventory_versions=inputs.unit_inventory_versions,
        scope=brief.get("scope") if isinstance(brief, dict) else None,
        brief=brief,
        prompt_version=SOURCE_SET_SYNTHESIS_PROMPT_VERSION,
        provider=provider,
        model=model,
        assessment_schema_version=(inputs.exam_profile or {}).get("schema_version") if inputs.exam_profile else None,
        token_budget={
            "synthesis_shard_input_tokens": budgets.synthesis_shard_input_tokens,
            "synthesis_total_input_ceiling": budgets.synthesis_total_input_ceiling,
            "synthesis_output_tokens": budgets.synthesis_output_tokens,
        },
        clock=clock,
    )
    manifest_hash = manifest["manifest_hash"]
    persist_manifest(repository, manifest)
    manifest_id = repository.synthesis_manifest_by_hash(manifest_hash)["id"]
    context_hash = agent_run_input_context_hash(manifest)

    # cache: identical manifest reuses the completed agent run.
    cached = repository.completed_agent_run_by_context(SYNTHESIS_AGENT_PURPOSE, context_hash)
    if cached is not None:
        batch = repository.proposal_batch_for_agent_run(cached["id"])
        return StudyMapResult(
            source_set_id=source_set.id, subject_id=subject_id, mode=resolved_mode,
            manifest_hash=manifest_hash, proposal_id=(batch or {}).get("id"), reused=True,
        )

    now = utc_now_iso(clock)
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": SYNTHESIS_AGENT_PURPOSE,
            "provider": provider,
            "provider_type": getattr(client, "provider_type", "codex"),
            "model": model,
            "prompt_template": "source-set-synthesis",
            "prompt_version": SOURCE_SET_SYNTHESIS_PROMPT_VERSION,
            "input_context_hash": context_hash,
            "output_schema": "SourceSetSynthesis",
            "started_at": now,
            "status": "running",
        }
    )
    synthesis_run_id = repository.insert_synthesis_run(
        manifest_id=manifest_id, mode=resolved_mode, agent_run_id=agent_run_id
    )

    try:
        merged, span_request_count, resolved_hashes, usage = _run_synthesis(
            run_method, repository, inputs, vault, source_set, brief, budgets, clock=clock,
        )
        normalized = _normalize(merged, inputs, vault, now, subject_id=resolve_subject_id(source_set, vault))

        # 3. identifiability analysis (real §11.3 check) — findings drive both the
        #    gate hook and the persisted generate-discriminator needs.
        view = build_proposal_view(
            facets=normalized.facet_payloads,
            criterion_targets=normalized.criterion_targets,
            recipe_components=normalized.recipe_components,
        )
        findings = analyze_identifiability(view)
        gate_ctx = _gate_context(vault, repository, inputs, findings)
        gate_proposal = GateProposal(
            items=normalized.gate_items,
            conflict_candidates=normalized.conflict_candidates,
            non_conflict_dispositions=normalized.non_conflict_dispositions,
        )
        report = run_synthesis_gates(gate_proposal, gate_ctx)
        diagnostics = [diag.to_dict() for diag in report.diagnostics]

        if report.blocked:
            repository.complete_synthesis_run(synthesis_run_id, status="failed",
                                              coverage_decisions={"gate_diagnostics": diagnostics})
            repository.complete_agent_run(agent_run_id, status="failed",
                                          error_message="synthesis gates hard-failed", clock=clock)
            raise StudyMapError("synthesis_gate_failed",
                                "Synthesis proposal failed hard quality gates.",
                                diagnostics=diagnostics)

        # 4. persist generate-discriminator / coarsen needs (FIRST, per §11.3).
        generation_needs = _persist_generation_needs(repository, subject_id, source_set.id,
                                                      synthesis_run_id, findings, clock=clock)

        # 5. persist the dependency-annotated proposal.
        patch_id = new_ulid()
        repository.persist_proposal_batch(
            {
                "id": patch_id,
                "agent_run_id": agent_run_id,
                "purpose": BOOTSTRAP_PROPOSAL_PURPOSE,
                "source_refs": [],
                "summary": getattr(merged, "summary", "") or f"bootstrap study map for {subject_id}",
                "created_at": now,
                "updated_at": now,
            },
            normalized.rows,
        )
        repository.complete_synthesis_run(
            synthesis_run_id, status="completed", proposal_id=patch_id,
            resolved_span_hashes=resolved_hashes,
            coverage_decisions={"gate_diagnostics": diagnostics},
            actual_usage=usage,
        )
        repository.complete_agent_run(agent_run_id, status="completed", clock=clock)
    except StudyMapError:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        repository.complete_synthesis_run(synthesis_run_id, status="failed")
        repository.complete_agent_run(agent_run_id, status="failed", error_message=str(exc), clock=clock)
        raise

    result = StudyMapResult(
        source_set_id=source_set.id, subject_id=subject_id, mode=resolved_mode,
        manifest_hash=manifest_hash, synthesis_run_id=synthesis_run_id, proposal_id=patch_id,
        item_counts=_count_items(normalized.rows), gate_diagnostics=diagnostics,
        generation_needs=generation_needs, span_request_count=span_request_count,
        resolved_span_hashes=resolved_hashes,
    )

    # 6. optional acceptance + goal wiring (learnable map requires mvp-0.7; the
    #    compilers enforce the bootstrap evidence refusal on a legacy vault).
    if apply:
        from learnloop.services.patches import apply_accepted_items

        apply_accepted_items(root, patch_id, clock=clock)
        result.applied = True
        if create_goal and _is_exam_prep(brief):
            result.goal_id = _create_goal_from_brief(root, brief, normalized.facet_ids, clock=clock)
    return result


def _run_synthesis(run_method, repository, inputs, vault, source_set, brief, budgets, *, clock):
    registry = _registry_index(vault)
    shards = _shards(inputs.unit_inventories, budgets.synthesis_shard_input_tokens)
    merged = None
    span_request_count = 0
    resolved_hashes: list[str] = []
    calls = 0
    input_tokens_estimate = 0
    from learnloop.codex.schemas import SourceSetSynthesis

    base_input_tokens = sum(
        max(1, len(json.dumps(entry, default=str)) // 4)
        for entry in inputs.unit_inventories
    )
    if base_input_tokens > budgets.synthesis_total_input_ceiling:
        raise StudyMapError(
            "budget_exceeded",
            "Selected inventories exceed the synthesis total-input ceiling; narrow the source scope.",
        )

    for ordinal, shard in enumerate(shards):
        shard_tokens = sum(max(1, len(json.dumps(entry, default=str)) // 4) for entry in shard)
        input_tokens_estimate += shard_tokens
        context = SourceSetSynthesisContext(
            source_set_id=source_set.id, subject_id=source_set.subject_id, mode="bootstrap",
            brief=brief, unit_inventories=shard, exam_profile=inputs.exam_profile or {},
            registry_index=registry, resolved_spans=[], shard_ordinal=ordinal, shard_count=len(shards),
        )
        result = run_method(context)
        calls += 1
        if _result_tokens(result) > budgets.synthesis_shard_output_tokens:
            raise StudyMapError("budget_exceeded", "A synthesis shard exceeded its output budget.")
        requests = [r if isinstance(r, dict) else r.model_dump() for r in getattr(result, "span_requests", []) or []]
        if requests:
            span_request_count += len(requests)
            resolved, hashes = _resolve_span_requests(
                repository, requests, inputs,
                max_count=budgets.synthesis_span_request_max_count,
                char_cap=budgets.synthesis_span_char_cap,
            )
            resolved_hashes.extend(hashes)
            context = SourceSetSynthesisContext(
                source_set_id=source_set.id, subject_id=source_set.subject_id, mode="bootstrap",
                brief=brief, unit_inventories=shard, exam_profile=inputs.exam_profile or {},
                registry_index=registry, resolved_spans=resolved, shard_ordinal=ordinal, shard_count=len(shards),
            )
            second_round_tokens = shard_tokens + sum(
                max(1, len(json.dumps(span, default=str)) // 4) for span in resolved
            )
            if input_tokens_estimate + second_round_tokens > budgets.synthesis_total_input_ceiling:
                raise StudyMapError(
                    "budget_exceeded",
                    "The requested evidence spans would exceed the synthesis total-input ceiling.",
                )
            input_tokens_estimate += second_round_tokens
            result = run_method(context)
            calls += 1
            if _result_tokens(result) > budgets.synthesis_shard_output_tokens:
                raise StudyMapError("budget_exceeded", "A synthesis shard exceeded its output budget.")
        merged = _merge_synthesis(merged, result) if merged is not None else result

    if merged is None:
        merged = SourceSetSynthesis()
    if _result_tokens(merged) > budgets.synthesis_output_tokens:
        raise StudyMapError("budget_exceeded", "Merged synthesis exceeded its total output budget.")
    usage = {"calls": calls, "input_tokens_estimate": input_tokens_estimate}
    return merged, span_request_count, resolved_hashes, usage


def _result_tokens(result: Any) -> int:
    if hasattr(result, "model_dump"):
        payload = result.model_dump(mode="json")
    elif isinstance(result, dict):
        payload = result
    else:
        payload = str(result)
    return max(1, len(json.dumps(payload, default=str)) // 4)


def _merge_synthesis(base: Any, extra: Any) -> Any:
    for field_name in ("concepts", "facets", "learning_objects", "blueprints", "practice_items", "conflicts", "non_conflict_dispositions", "notes"):
        getattr(base, field_name).extend(getattr(extra, field_name))
    return base


def _gate_context(vault, repository, inputs, findings) -> GateContext:
    registered_facets = set(vault.evidence_facets.keys())
    from learnloop.services.capability_mapping import CAPABILITY_VOCABULARY

    def hook(_proposal, _ctx):
        return _findings_to_diagnostics(findings)

    return GateContext(
        registered_facet_ids=registered_facets,
        registered_capabilities=set(CAPABILITY_VOCABULARY),
        selected_revision_ids=set(inputs.selected_revision_ids),
        extraction_units=inputs.extraction_units,
        extraction_spans=inputs.extraction_spans,
        held_out_span_ids=inputs.held_out_span_ids,
        vault=vault,
        repository=repository,
        identifiability_hook=hook,
    )


def _findings_to_diagnostics(findings) -> list[GateDiagnostic]:
    out: list[GateDiagnostic] = []
    for finding in findings:
        out.append(
            GateDiagnostic(
                gate="identifiability",
                severity="review",
                entity_refs=finding.facet_ids,
                message=finding.message,
                suggested_action=finding.suggested_action,
            )
        )
    return out


def _persist_generation_needs(repository, subject_id, source_set_id, synthesis_run_id, findings, *, clock):
    persisted: list[dict[str, Any]] = []
    for finding in findings:
        repository.upsert_synthesis_generation_need(
            subject_id=subject_id,
            need_kind=finding.kind,
            target_key=finding.target_key,
            missing_capability=finding.capability or "unresolved",
            facet_ids=list(finding.facet_ids),
            source_set_id=source_set_id,
            synthesis_run_id=synthesis_run_id,
            detail=finding.detail,
            clock=clock,
        )
        persisted.append(
            {
                "kind": finding.kind,
                "target_key": finding.target_key,
                "capability": finding.capability,
                "facet_ids": list(finding.facet_ids),
                "message": finding.message,
            }
        )
    return persisted


def _count_items(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["item_type"]] = counts.get(row["item_type"], 0) + 1
    return counts


def _is_exam_prep(brief: dict[str, Any]) -> bool:
    outcome = str(brief.get("outcome") or brief.get("assessment_alignment_intent") or "").lower()
    return "exam" in outcome or bool(brief.get("exam_preparation"))


def _create_goal_from_brief(root: Path, brief: dict[str, Any], facet_ids: list[str], *, clock: Clock | None) -> str | None:
    """Create a Goal wired to the freshly minted facets (§5.1), after acceptance."""

    from learnloop.vault.models import Goal
    from learnloop.vault.paths import VaultPaths as _VP
    from learnloop.vault.yaml_io import read_yaml, write_yaml

    vault = load_vault(root)
    paths = _VP(vault.root, vault.config)
    applied_facets = [f for f in facet_ids if f in vault.evidence_facets]
    if not applied_facets:
        return None
    goals_data = read_yaml(paths.goals_path) if paths.goals_path.exists() else {"schema_version": 2, "goals": []}
    goals = goals_data.setdefault("goals", [])
    title = str(brief.get("goal_title") or brief.get("outcome") or "Exam preparation")
    base = f"goal_{snake_case(title)[:40] or 'exam_prep'}"
    existing = {str(g.get("id")) for g in goals if isinstance(g, dict)}
    goal_id, n = base, 2
    while goal_id in existing:
        goal_id = f"{base}_{n}"
        n += 1
    now = utc_now_iso(clock)
    entry = {
        "id": goal_id,
        "title": title,
        "status": "active",
        "priority": 0.5,
        "target_recall": float(brief.get("target_recall", 0.8)),
        "facet_scope": {"concepts": [], "facets": applied_facets},
        "due_at": brief.get("due_at"),
        "exam": {"enabled": True, "item_count": int(brief.get("exam_item_count", 20))},
        "created_at": now,
        "updated_at": now,
    }
    Goal.model_validate(entry)
    goals.append(entry)
    goals_data["schema_version"] = 2
    write_yaml(paths.goals_path, goals_data)
    return goal_id
