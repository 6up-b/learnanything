"""Bootstrap synthesis: brief -> sharded synthesis -> dependency-closed proposal
-> applied study map (source-ingestion v2 §8, ING M6).

This service orchestrates the "Create study map" journey:

1. (no lock check: facet identity locks were removed, owner 2026-10-12. A
   rebuild that rewords an existing facet writes a facet version with an
   undo when its proposal applies; ``auto`` routes a subject that already has
   a study map to append);
2. immutable manifest persisted BEFORE the agent run (§8.4): the record of what
   the run read. Nothing reuses a run by it: a rebuild runs again, each paid call
   answering from its checkpoint, and an equal earlier proposal is the result
   (``proposal_match``);
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
import re
from collections.abc import Mapping, Sequence
from contextlib import nullcontext
from dataclasses import dataclass, field
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from learnloop.ai.execution import (
    ModelCheckpoint,
    checkpointed,
    content_key,
    declared_budgets,
    generation_limit,
    model_settings,
    request_key,
)
from learnloop.clock import Clock, utc_now_iso
from learnloop.content.synthesis.ai_contracts import (
    CONCEPT_GRAPH_REGISTRY_PROMPT_VERSION,
    ConceptGraphContext,
    ConceptGraphStructuring,
    ConceptGraphStructuringWithRegistry,
    SourceSetSynthesis,
    SourceSetSynthesisContext,
    concept_graph_has_registry_nominations,
    concept_graph_structuring_prompt,
    source_set_synthesis_prompt,
    source_set_synthesis_prompt_version,
)
from learnloop.ai.transport import StructuredTransport, execute_structured_operation
from learnloop.db.repositories import Repository
from learnloop.vault.repository import vault_repository
from learnloop.ids import new_ulid, snake_case
from learnloop.ai.runs import finish_agent_run
from learnloop.content.synthesis.brief import validate_brief
from learnloop.content.synthesis.normalize import Normalized, normalize
from learnloop.content.facet_identity import authority as facet_meaning
from learnloop.content.facet_identity.plan import FacetIdentityPlan
from learnloop.content.synthesis.exam_profile import ExamUnitEntry, aggregate_exam_profile
from learnloop.content.synthesis.graph_nomination import (
    CONCEPT_RECIPE,
    GraphNominator,
    concept_query,
    plan_ingest_embedding,
)
from learnloop.learner.learner_profile import read_learner_profile
from learnloop.learner.identifiability import analyze_identifiability, build_proposal_view
from learnloop.content.sources import exam_material as EM
from learnloop.content.sources.role_authority import is_scope_only_role, role_authority
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.content.synthesis.source_unit_selection import (
    compute_effective_units,
    effective_scope_groups,
)
from learnloop.content.synthesis.source_unit_inventory import choose_unit_inventory, current_inventory_identity
from learnloop.content.synthesis.synthesis_gates import (
    GateContext,
    GateDiagnostic,
    GateProposal,
    run_synthesis_gates,
)
from learnloop.content.synthesis.proposal_match import ProposalMatch, RejectedProposalMatch, match_proposal
from learnloop.content.synthesis.synthesis_manifests import (
    agent_run_input_context_hash,
    build_manifest,
    content_hash,
    persist_manifest,
)
from learnloop.ai.usage import TokenUsage, UsageMeter, consume_client_usage
from learnloop.content.synthesis.vault_epigraphs import (
    digest_from_proposal_rows,
    generate_vault_epigraphs,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault, SourceSet
from learnloop.vault.paths import VaultPaths

SYNTHESIS_AGENT_PURPOSE = "source_set_synthesis"
BOOTSTRAP_PROPOSAL_PURPOSE = "sourceset_bootstrap"


class StudyMapError(ValueError):
    """A typed bootstrap-synthesis failure (gate hard-fail, budget, missing input)."""

    def __init__(self, code: str, message: str, *, diagnostics: list[dict[str, Any]] | None = None,
                 synthesis_run_id: str | None = None,
                 candidate_preserved: bool = False):
        super().__init__(message)
        self.code = code
        self.diagnostics = diagnostics or []
        self.synthesis_run_id = synthesis_run_id
        self.candidate_preserved = candidate_preserved


def request_source_set_synthesis(
    client: StructuredTransport, context: SourceSetSynthesisContext
) -> SourceSetSynthesis:
    """Synthesize one source-set shard through the shared transport."""

    return execute_structured_operation(
        client,
        purpose="source_set_synthesis",
        prompt=source_set_synthesis_prompt(context),
        result_model=SourceSetSynthesis,
    )


def request_concept_graph_structuring(
    client: StructuredTransport, context: ConceptGraphContext
) -> ConceptGraphStructuring:
    """Structure a merged candidate graph through the shared transport.

    With T5 registry nominations the result model also carries
    ``registry_merges``; without them the request is the pre-T5 one."""

    return execute_structured_operation(
        client,
        purpose=STRUCTURING_PURPOSE,
        prompt=concept_graph_structuring_prompt(context),
        result_model=_structuring_result_model(context),
    )


STRUCTURING_PURPOSE = "concept_graph_structuring"


def _structuring_result_model(context: ConceptGraphContext) -> type[ConceptGraphStructuring]:
    return (
        ConceptGraphStructuringWithRegistry
        if concept_graph_has_registry_nominations(context)
        else ConceptGraphStructuring
    )


def structuring_checkpoint(
    repository: Any, context: ConceptGraphContext, settings: dict[str, Any],
) -> ModelCheckpoint[ConceptGraphStructuring]:
    """The structuring call's checkpoint: the request key of its rendered
    prompt and of the result schema it asks for (with or without registry
    merges), under the run's settings."""

    result_model = _structuring_result_model(context)
    return checkpointed(
        repository, purpose=STRUCTURING_PURPOSE, prompt=concept_graph_structuring_prompt(context),
        schema=result_model.model_json_schema(), settings=settings, result_model=result_model,
    )


@dataclass
class StudyMapResult:
    source_set_id: str
    subject_id: str
    mode: str
    manifest_hash: str
    synthesis_run_id: str | None = None
    proposal_id: str | None = None
    # The proposal is an earlier run's equal one (``proposal_match``); nothing new was written.
    reused: bool = False
    # ... and that proposal had nothing left waiting: the build added nothing.
    nothing_new: bool = False
    applied: bool = False
    goal_id: str | None = None
    item_counts: dict[str, int] = field(default_factory=dict)
    gate_diagnostics: list[dict[str, Any]] = field(default_factory=list)
    generation_needs: list[dict[str, Any]] = field(default_factory=list)
    span_request_count: int = 0
    resolved_span_hashes: list[str] = field(default_factory=list)
    candidate_repairs: list[dict[str, Any]] = field(default_factory=list)
    # Facet identity (handoff §4): the run's judge summary and each merge or
    # absorb it applied, with its undo state. None when the switch is off.
    facet_identity: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_set_id": self.source_set_id,
            "subject_id": self.subject_id,
            "mode": self.mode,
            "manifest_hash": self.manifest_hash,
            "synthesis_run_id": self.synthesis_run_id,
            "proposal_id": self.proposal_id,
            "reused": self.reused,
            "nothing_new": self.nothing_new,
            "applied": self.applied,
            "goal_id": self.goal_id,
            "item_counts": dict(self.item_counts),
            "gate_diagnostics": list(self.gate_diagnostics),
            "generation_needs": list(self.generation_needs),
            "span_request_count": self.span_request_count,
            "resolved_span_hashes": list(self.resolved_span_hashes),
            "candidate_repairs": list(self.candidate_repairs),
            "facet_identity": self.facet_identity,
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
    # Resolves a citation in this source set's selected units with its
    # effective role (Codex verification of F6): the one resolver the
    # facet-meaning chokepoint uses (``facet_identity.authority``).
    resolver: facet_meaning.CitationResolver | None = None
    # "revision:unit" -> the chosen inventory row's id, extraction and content
    # hash. Kept out of the entries (they are rendered into the prompt whole,
    # so a new key there would move every pass checkpoint); the manifest
    # records it (:func:`manifest_inputs`).
    inventory_rows: dict[str, dict[str, str]] = field(default_factory=dict)
    # revision -> its asset's hash; extraction -> "extractor@version".
    asset_hashes: dict[str, str] = field(default_factory=dict)
    extractor_versions: dict[str, str] = field(default_factory=dict)


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
    inventory_rows: dict[str, dict[str, str]] = {}
    span_origin: dict[str, dict[str, str]] = {}
    inventory_route = current_inventory_identity(vault.config)
    # The one exam predicate over every source set of the vault: a unit held
    # out for evaluation (any role) or exam material of any revision never
    # feeds synthesis as teaching, and its spans join the leakage gate.
    exam = EM.exam_material(vault, repo)

    asset_hashes: dict[str, str] = {}
    extractor_versions: dict[str, str] = {}

    for member in source_set.members:
        extraction_id = resolve_extraction_id(repo, member.revision_id)
        membership.append(
            {
                "source_id": member.source_id,
                "revision_id": member.revision_id,
                "role": member.default_role,
                "priority": member.priority,
                # A unit's override changes the role its inventory is read under.
                "role_overrides": {s.unit_id: s.role_override for s in member.scope if s.role_override},
            }
        )
        if member.revision_id not in selected_revision_ids:
            selected_revision_ids.append(member.revision_id)
        revision = repo.get_source_revision(member.revision_id)
        if revision is not None and revision.get("asset_hash"):
            asset_hashes[member.revision_id] = str(revision["asset_hash"])
        if extraction_id is None:
            continue
        if extraction_id not in extraction_ids:
            extraction_ids.append(extraction_id)
        extraction = repo.get_extraction_run(extraction_id)
        if extraction is not None:
            extractor_versions[extraction_id] = f"{extraction.get('extractor')}@{extraction.get('extractor_version')}"
        span_origin[extraction_id] = {
            "source_id": member.source_id,
            "revision_id": member.revision_id,
            "role": member.default_role,
        }
        ir = repo.load_document_ir(extraction_id)
        if ir is not None:
            extraction_units.setdefault(extraction_id, set()).update(u.unit_id for u in ir.units)
            selection = repo.get_unit_selection(extraction_id)
            extraction_units[extraction_id].update(
                str(effective["effective_id"])
                for effective in compute_effective_units(
                    ir, (selection or {}).get("boundary_overrides") or []
                )
            )
            extraction_spans.setdefault(extraction_id, set()).update(b.span_id for b in ir.blocks)
        rows = repo.unit_inventories_for_revision(member.revision_id)
        scope_units = [scope.unit_id for scope in member.scope]
        if not scope_units and ir is not None:
            scope_units = [u.unit_id for u in ir.units]
        role_overrides = {s.unit_id: s.role_override for s in member.scope if s.role_override}
        selection = repo.get_unit_selection(extraction_id)
        exam_use_modes = (selection or {}).get("exam_use_modes", {}) if selection else {}
        paper_metadata = (selection or {}).get("exam_paper_metadata", {}) if selection else {}

        scope_groups = (
            effective_scope_groups(
                ir,
                (selection or {}).get("boundary_overrides") or [],
                scope_units,
                role_by_unit=role_overrides,
                default_role=member.default_role,
            )
            if ir is not None
            else [
                {
                    "unit_id": unit_id,
                    "unit_ids": [unit_id],
                    "role": role_overrides.get(unit_id, member.default_role),
                    "merged": False,
                }
                for unit_id in scope_units
            ]
        )
        raw_spans = {unit.unit_id: tuple(unit.span_ids) for unit in ir.units} if ir is not None else {}
        for group in scope_groups:
            unit_id = str(group["unit_id"])
            source_unit_ids = [str(value) for value in group["unit_ids"]]
            effective_role = str(group["role"])
            authority = role_authority(effective_role)
            if effective_role != "exam":
                group_spans = {span for source_unit_id in source_unit_ids
                               for span in raw_spans.get(source_unit_id, ())}
                withheld = {span for span in group_spans if exam.covers(extraction_id, span)}
                if withheld or exam.covers(extraction_id):
                    # Exam material by the shared predicate in a unit whose
                    # own role teaches (a held-out textbook unit): assessment
                    # only, its spans fed to the leakage gate, its inventory
                    # never in the synthesis context.
                    held_out_span_ids |= {f"{extraction_id}:{span}" for span in (withheld or group_spans)}
                    continue
            if is_scope_only_role(effective_role):
                # Curriculum C3 (spec §9.1): a syllabus only scopes a deliverable. It is never
                # a generation source, so no inventory of it reaches a study map (bootstrap or
                # append), whatever inventory a manual run made.
                continue
            row = choose_unit_inventory(rows, unit_id, source_unit_ids, ir=ir, route=inventory_route)
            if row is None and len(source_unit_ids) > 1:
                # Transition-safe fallback: an existing per-member cache remains
                # usable until the explicit composite inventory has been generated.
                for source_unit_id in source_unit_ids:
                    member_row = choose_unit_inventory(
                        rows, source_unit_id, [source_unit_id], ir=ir, route=inventory_route
                    )
                    if member_row is None:
                        continue
                    inventory = member_row["inventory"]
                    unit_inventory_versions[
                        f"{member.revision_id}:{source_unit_id}"
                    ] = str(member_row.get("inventory_schema_version")) + "|" + str(
                        member_row.get("prompt_version")
                    )
                    inventory_rows[f"{member.revision_id}:{source_unit_id}"] = _chosen_row(member_row)
                    unit_inventories.append(
                        {
                            "extraction_id": extraction_id,
                            "revision_id": member.revision_id,
                            "source_id": member.source_id,
                            "unit_id": source_unit_id,
                            "source_unit_ids": [source_unit_id],
                            "role": effective_role,
                            "semantic_authority": authority.semantic_contract,
                            "inventory": inventory,
                        }
                    )
                continue
            if row is None:
                continue
            inventory = row["inventory"]
            unit_inventory_versions[f"{member.revision_id}:{unit_id}"] = str(
                row.get("inventory_schema_version")
            ) + "|" + str(row.get("prompt_version"))
            inventory_rows[f"{member.revision_id}:{unit_id}"] = _chosen_row(row)
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
                    "source_unit_ids": source_unit_ids,
                    "role": effective_role,
                    "semantic_authority": authority.semantic_contract,
                    "inventory": inventory,
                }
            )

    # Every held-out span of the synthesis's extractions (any role, the shared
    # predicate's partition) is fed to the leakage gate.
    for held_extraction, held_span in exam.held_out.spans:
        if held_extraction in extraction_spans:
            held_out_span_ids.add(f"{held_extraction}:{held_span}")
    for held_extraction in exam.held_out.extractions:
        held_out_span_ids |= {f"{held_extraction}:{span}" for span in extraction_spans.get(held_extraction, ())}
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
        resolver=facet_meaning.CitationResolver.for_source_set(repo, source_set, exam_source_sets=vault),
        inventory_rows=inventory_rows,
        asset_hashes=asset_hashes,
        extractor_versions=extractor_versions,
    )


def _chosen_row(row: Mapping[str, Any]) -> dict[str, str]:
    """Which inventory row was read: its own id and extraction, which can be an
    earlier reading than the one the entry's citations resolve against, and a
    hash of its content (a row updated in place keeps its id)."""

    return {
        "inventory_id": str(row.get("id") or ""),
        "extraction_id": str(row.get("extraction_id") or ""),
        "content_hash": content_hash(row.get("inventory")),
    }


def manifest_inputs(inputs: _SynthesisInputs) -> dict[str, Any]:
    """The source-side fields of a run's manifest: what it read, exactly.

    Each unit's entry names the inventory row it read and that row's content as well as the version labels, so a
    row re-inventoried in place under an unchanged label still shows in the record."""

    return {
        "membership": inputs.membership,
        "revision_ids": inputs.selected_revision_ids,
        "asset_hashes": dict(sorted(inputs.asset_hashes.items())),
        "extraction_ids": inputs.extraction_ids,
        "extractor_versions": dict(sorted(inputs.extractor_versions.items())),
        "unit_inventory_versions": {
            key: {"version": version, **inputs.inventory_rows.get(key, {})}
            for key, version in inputs.unit_inventory_versions.items()
        },
    }


def _registry_index(vault: LoadedVault) -> dict[str, Any]:
    """A compact existing-registry index for the prompt (never full contracts)."""

    return {
        "facets": sorted(vault.evidence_facets.keys()),
        "concepts": sorted(vault.concepts.keys()),
        "learning_objects": sorted(vault.learning_objects.keys()),
    }


# progress(stage, message, current, total) — stage is one of "synthesis" /
# "validation" / "persistence" / "apply"; the durable-job handler maps stages
# onto checkpoint-ladder phases. Exceptions propagate: the runner's report()
# raises JobCancelled here so a cancellation lands at the next stage boundary.
ProgressFn = Callable[[str, str, int | None, int | None], None]


def _notify(
    progress: ProgressFn | None,
    stage: str,
    message: str,
    *,
    current: int | None = None,
    total: int | None = None,
) -> None:
    if progress is not None:
        progress(stage, message, current, total)


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


# --- orchestration ----------------------------------------------------------


def create_study_map(
    root: Path,
    source_set_id: str,
    *,
    client: Any,
    brief: dict[str, Any] | None = None,
    mode: str = "auto",
    apply: bool = False,
    apply_gate: Callable[[], bool] | None = None,
    create_goal: bool = False,
    repository: Repository | None = None,
    clock: Clock | None = None,
    budget_overrides: dict[str, int] | None = None,
    unlimited_token_budget: bool = False,
    progress: ProgressFn | None = None,
    embedding_client_factory: Callable[[], Any] | None = None,
    facet_identity_client: Any = None,
) -> StudyMapResult:
    """``embedding_client_factory`` replaces the ``ai.routing.embedding`` client
    for Slice 2 T5 nominations (tests); used only when nominations are on.
    ``facet_identity_client`` replaces the ``ai.routing.facet_identity_judge``
    client (tests); used only when facet identity is on.

    ``apply_gate`` is consulted immediately before an ``apply`` (UX Phase 1:
    an automatic build re-reads its kill switches and Undo state there); a
    ``False`` keeps the proposal unapplied."""

    vault = load_vault(root)
    if repository is None:
        # Repository opens a fresh sqlite connection per call; nothing to close.
        repository = vault_repository(VaultPaths(vault.root, vault.config))
    return _create_study_map(
        vault, repository, root, source_set_id,
        client=client, brief=brief or {}, mode=mode, apply=apply, apply_gate=apply_gate,
        create_goal=create_goal, clock=clock, budget_overrides=budget_overrides,
        unlimited_token_budget=unlimited_token_budget,
        progress=progress,
        embedding_client_factory=embedding_client_factory,
        facet_identity_client=facet_identity_client,
    )


def _facet_identity_plan(
    candidate: Any, vault: LoadedVault, repository: Repository, run_id: str, *,
    nominator: Any = None, client: Any = None, progress: ProgressFn | None = None,
    attach_enabled: bool = True,
) -> FacetIdentityPlan | None:
    """Facet identity for one run's candidates (``None`` when switched off).

    Never fails the paid synthesis: an unavailable or failing judge leaves the
    candidates as they are and the plan says why.
    """

    if not vault.config.facet_identity.enabled:
        return None
    from learnloop.content.facet_identity.plan import build_plan

    _notify(progress, "synthesis", "Checking facet identity")
    try:
        return build_plan(
            candidate, vault=vault, repository=repository, run_id=run_id,
            nominator=nominator, judge_client=client, attach_enabled=attach_enabled,
        )
    except Exception as exc:  # noqa: BLE001 - facet identity never fails ingest
        return FacetIdentityPlan(status="error", notes=[f"{type(exc).__name__}: {exc}"])


def facet_identity_result(
    root: Path, repository: Repository, plan: FacetIdentityPlan | None, run_id: str | None,
) -> dict[str, Any] | None:
    """The run's facet-identity summary and its actions with their undo state."""

    if plan is None or not run_id:
        return None
    from learnloop.content.facet_identity.actions import describe, list_actions

    vault = load_vault(root)
    return {
        **plan.summary(),
        # The desktop re-reads the run's actions by this id (their live undo state).
        "run_id": run_id,
        "actions": [describe(record, vault) for record in list_actions(repository, run_id=run_id, limit=None)],
    }


def _gate_open(apply_gate: Callable[[], bool] | None) -> bool:
    return apply_gate is None or bool(apply_gate())


def plan_study_map_embedding(root: Path, source_set_id: str) -> dict[str, Any]:
    """Dry run of one bootstrap synthesis's Slice 2 T5 embedding spend.

    Loads the vault and reads stored vectors only: no client, manifest, agent
    run or other data change. The candidates a synthesis embeds are written by
    its paid model call, so the plan bounds them by the per-run cap
    (:func:`plan_ingest_embedding`).
    """

    vault = load_vault(root)
    if not any(s.id == source_set_id for s in vault.source_sets):
        raise StudyMapError("source_set_not_found", f"Source set '{source_set_id}' does not exist.")
    plan = plan_ingest_embedding(
        vault, VaultPaths(vault.root, vault.config).sqlite_path, entry="bootstrap",
    )
    from learnloop.content.facet_identity.plan import ingest_dry_run

    return {"source_set_id": source_set_id, **plan, "facet_identity": ingest_dry_run(vault)}


def bootstrap_scope(
    vault: LoadedVault, brief: Any, *, nominator: GraphNominator | None, facet_identity_client: Any = None,
) -> Any:
    """The ``scope`` a bootstrap synthesis records in its manifest: the brief's scope and, while they are on, what
    the nominator and the facet-identity judge run under. A record: nothing reuses a run by it."""

    scope: Any = brief.get("scope") if isinstance(brief, dict) else None
    if nominator is not None:
        # What the nominator can show the structuring model: the switch, its
        # configuration, the registry prompt and the registry's definitions and
        # index state. Off, the scope is the pre-T5 one.
        scope = {
            "brief_scope": scope,
            "graph_nomination": nominator.identity(prompt_version=CONCEPT_GRAPH_REGISTRY_PROMPT_VERSION),
        }
    # Facet identity (handoff §4): the judge's switch, route and policy. Off,
    # the scope is the pre-change one.
    if vault.config.facet_identity.enabled:
        from learnloop.content.facet_identity.judge import manifest_identity

        scope = {"scope": scope, "facet_identity": manifest_identity(vault.config, client=facet_identity_client)}
    return scope


def resolve_brief(vault: LoadedVault, brief: Mapping[str, Any] | None) -> dict[str, Any]:
    """The brief a bootstrap or an append reads and records, resolved before its manifest is built.

    Normalized tolerantly (a stale persisted brief must never fail a paid build), with the vault's declared learner
    level when the brief carries none, and the item-authoring mode stamped in, so the manifest records the decision
    and a revalidation replays it. Both orchestrators call this: an append that resolved it after hashing recorded a
    brief it did not read, and never inherited the learner's level."""

    resolved = validate_brief(dict(brief or {}), strict=False)
    if not resolved.get("starting_level"):
        profile = read_learner_profile(VaultPaths(vault.root, vault.config))
        if profile is not None:
            resolved["starting_level"] = profile["starting_level"]
            if profile.get("level_note") and not resolved.get("level"):
                resolved["level"] = profile["level_note"]
    if resolved.get("practice_items") not in ("upfront", "as_you_read"):
        resolved["practice_items"] = vault.config.ingest.bootstrap_practice_items
    return resolved


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
    budget_overrides: dict[str, int] | None = None,
    unlimited_token_budget: bool = False,
    progress: ProgressFn | None = None,
    embedding_client_factory: Callable[[], Any] | None = None,
    facet_identity_client: Any = None,
    apply_gate: Callable[[], bool] | None = None,
) -> StudyMapResult:
    """The bootstrap opens its run with the shared head (:func:`open_synthesis_run`), recording the brief's scope:
    it reads every scope unit's inventory. The rest is the shared tail (:func:`finish_synthesis_run`) under the
    ``BOOTSTRAP`` mode: the shard runner over those inventories, then the gates and persistence, with the whole map
    and the exam goal as what it applies when asked."""

    run = open_synthesis_run(
        vault, repository, root, source_set_id, BOOTSTRAP,
        client=client, brief=brief, requested_mode=mode, clock=clock, budget_overrides=budget_overrides,
        unlimited_token_budget=unlimited_token_budget, embedding_client_factory=embedding_client_factory,
        facet_identity_client=facet_identity_client, progress=progress,
        decide_scope=lambda resolved_brief, _inputs, _budgets, nominator: RunScope(bootstrap_scope(
            vault, resolved_brief, nominator=nominator, facet_identity_client=facet_identity_client,
        )),
    )
    manifest_hash = run.manifest["manifest_hash"]

    def apply_map(outcome: SynthesisOutcome) -> dict[str, Any]:
        # Acceptance and goal wiring, when asked (a learnable map requires mvp-0.7;
        # the compilers enforce the bootstrap evidence refusal on a legacy vault).
        if not (apply and not outcome.nothing_new and _gate_open(apply_gate)):
            return {}
        goal_id = _apply_map(
            root, repository, outcome.proposal_id, brief=run.brief, create_goal=create_goal, clock=clock,
            facet_ids=outcome.normalized.facet_ids, progress=progress,
        )
        return {"applied": True, "goal_id": goal_id}

    outcome = finish_synthesis_run(run, BOOTSTRAP, apply=apply_map)
    return StudyMapResult(
        source_set_id=run.source_set.id, subject_id=run.source_set.subject_id, mode=BOOTSTRAP.name,
        manifest_hash=manifest_hash, synthesis_run_id=run.synthesis_run_id, proposal_id=outcome.proposal_id,
        reused=outcome.reused, nothing_new=outcome.nothing_new,
        item_counts=_count_items(outcome.normalized.rows), gate_diagnostics=outcome.gate_diagnostics,
        generation_needs=outcome.generation_needs, span_request_count=outcome.answer.span_request_count,
        resolved_span_hashes=outcome.answer.resolved_span_hashes, facet_identity=outcome.facet_identity,
        **outcome.applied,
    )


@dataclass(frozen=True)
class SynthesisCall:
    """How a mode asks the model, as the values the one shard runner (:func:`_run_synthesis`) reads: what a pass
    sends and is saved under, the units the run's input is split into, and the rule its spend is held to. Bootstrap's
    is beside ``BOOTSTRAP``; the append's beside ``APPEND`` in :mod:`source_append`."""

    #: One pass's request: ``request(client, context)`` sends ``prompt(context)`` for a ``result_model`` answer.
    request: Callable[[Any, Any], Any]
    prompt: Callable[[Any], str]
    result_model: Any
    #: A pass's checkpoint key, from the prompt it sends and the provider settings, and the purpose it is saved under.
    checkpoint_key: Callable[[str, dict[str, Any]], str]
    checkpoint_purpose: str
    #: The run's units of work, lists of inventories: one base pass, and at most one span round, each.
    shards: Callable[[SynthesisRun], list[list[dict[str, Any]]]]
    #: Given the run, ``context(shard, ordinal, shard_count, resolved_spans)``: what one pass renders.
    contexts: Callable[[SynthesisRun], Callable[[list[dict[str, Any]], int, int, list[dict[str, Any]]], Any]]
    #: ``spend(budgets, unlimited)``: the run's spend against its budgets (the methods ``_SynthesisBudget`` has).
    spend: Callable[[Any, bool], Any]
    #: Each shard's answer is filed under its base pass's key (``synthesis_shard_results``, which answers a one-request
    #: shard on a rerun), its client ids are made local to it, and the shards are merged. Unsharded: one unit, whose
    #: answer is the candidate with the ids the model wrote.
    sharded: bool
    #: ``after_passes(run, merged, spend=, answers=, settings=, shard_count=) -> (candidate, usage, diagnostics)``: what
    #: follows the passes; the usage joins the runner's record, the diagnostics are the answer's own review records.
    after_passes: Callable[..., tuple[Any, dict[str, Any], list[dict[str, Any]]]]


@dataclass(frozen=True)
class SynthesisMode:
    """What a bootstrap and an append decide differently, opening the run and once the model has answered. There
    are two rows, ``BOOTSTRAP`` below and ``APPEND`` in :mod:`source_append`, and each field is one difference
    between them.

    The fields marked "kept" are differences between the two former copies that no spec settles: each keeps its
    mode's behaviour exactly until one rule is chosen (``docs/reviews/refactor-bug-ledger.md`` names the field)."""

    #: The mode's name: what the synthesis run records as its mode, what the epigraph service is told, and the one
    #: mode besides ``"auto"`` a caller may ask for.
    name: str
    #: The agent run's purpose, prompt template and output schema.
    agent_purpose: str
    prompt_template: str
    output_schema: str
    #: The prompt's version, given whether the one-facet-per-skill rule is in it (facet identity on).
    prompt_version: Callable[[bool], str]
    #: The ingest budgets the manifest's ``token_budget`` records, and those an unlimited run still records (a
    #: context-window size, not a spend ceiling).
    recorded_budgets: tuple[str, ...]
    unlimited_recorded_budgets: tuple[str, ...]
    #: The proposal's purpose. A rerun is compared only with earlier proposals of the same purpose.
    proposal_purpose: str
    #: The proposal's summary when the answer has none; ``{subject}`` is the rows' subject.
    summary_fallback: str
    #: The typed error of a candidate the synthesis gates block: its code and message.
    gate_failure: tuple[str, str]
    #: How the mode asks the model (:class:`SynthesisCall`): the one shard runner reads it.
    call: SynthesisCall
    #: Maps the answer to proposal rows: the bootstrap normalizer, or the append's, which adds its own item kinds.
    normalize: Callable[..., Normalized]
    #: ``epigraph_digest(rows, context, summary)``: what the Start-screen epigraphs are written about. An append's rows
    #: may hold only links, so its digest is topped up from its new inventories and neighbourhood.
    epigraph_digest: Callable[[list[dict[str, Any]], Any, str], Any]
    #: The gates judge the append vocabulary: only an explicit restructure may update or deactivate.
    append_vocabulary: bool
    #: Where the run's facet-identity actions say they came from.
    facet_action_origin: str
    #: The answer is saved on the run, so a run that fails after it can be finished with no model call
    #: (``revalidate_synthesis_candidate``, which only bootstrap has).
    keeps_candidate_for_repair: bool
    #: Kept: an answer whose client ids collide fails typed, before the gates (append's fails at persist, untyped).
    checks_client_id_collisions: bool
    #: Kept: identifiability findings reach the gates and are persisted as generation needs.
    analyzes_identifiability: bool
    #: Kept: the agent run records the model call's usage alone, drained from the client after each answer;
    #: otherwise whatever the client reports by the run's end (the instrument gates' calls included).
    meters_the_model_call: bool
    #: Kept: the synthesis run records its usage only when it writes a proposal.
    usage_only_with_a_proposal: bool
    #: Kept: the run's usage includes the model call's record (passes, estimates, shards); otherwise only facet
    #: identity's.
    records_call_usage: bool
    #: Kept: the run records the hashes of the spans its span rounds resolved.
    records_resolved_span_hashes: bool
    #: Kept: the model call runs with the run's budgets declared on its root receipts.
    declares_its_budgets: bool
    #: Kept: dropping the answers a run served forgets them, so a later drop in the same run (a fresh answer the gates
    #: reject after a rejected match) names only the answers served since; otherwise it names the earlier ones again.
    forgets_dropped_answers: bool
    #: Kept: the rows of a source set whose ``subject_id`` is empty carry the vault's first subject.
    resolves_an_empty_subject: bool


def _gate_and_persist(
    vault: LoadedVault,
    repository: Repository,
    source_set: SourceSet,
    merged: Any,
    inputs: _SynthesisInputs,
    *,
    mode: SynthesisMode,
    subject_id: str,
    agent_run_id: str | None,
    synthesis_run_id: str,
    now: str,
    usage: dict[str, Any] | None,
    resolved_hashes: list[str] | None,
    clock: Clock | None,
    progress: ProgressFn | None = None,
    items_off: bool = False,
    token_usage: TokenUsage | None = None,
    client: Any = None,
    nominator: Any = None,
    facet_identity_plan: Any = None,
    fresh_answers: bool = False,
    answer_diagnostics: Sequence[dict[str, Any]] = (),
) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]], Normalized, ProposalMatch | None]:
    """Normalize -> §8.7 gates -> instrument gates -> persist proposal, over one answer.

    The proposal is persisted under :mod:`proposal_match`'s rule: rows equal to an earlier proposal of the set are
    that proposal (returned with the match; nothing is written), unless the learner wholly rejected it, which raises
    :class:`RejectedProposalMatch` so the caller drops the answers and pays for fresh ones. ``fresh_answers``: the
    candidate came from those fresh answers, so it is persisted even when it equals the rejected proposal again.
    ``answer_diagnostics`` are the mode's own review records about the answer, reported after the normalizer's.

    Shared by both modes' runs and by candidate revalidation (which re-runs
    exactly this stage over a preserved candidate with zero model calls). On any
    failure the synthesis run and agent run are finalized as failed before the
    typed error propagates.

    ``token_usage`` is the provider-reported cost of the model calls that
    produced ``merged``, already drained by the caller.
    Revalidation has none (its whole point is finishing without paying again),
    so it passes None and no ``client``, leaving the original run's recorded
    cost alone. A mode that does not meter its model call passes None and its
    ``client``, which a completion drains; a failure here does not, because the
    caller's failure arm completes the run again and a second drain would
    record zeros."""

    recorded_usage = None if mode.usage_only_with_a_proposal else usage

    def _fail(error_message: str, coverage: Any = None) -> None:
        repository.complete_synthesis_run(
            synthesis_run_id, status="failed", coverage_decisions=coverage, actual_usage=recorded_usage
        )
        finish_agent_run(
            repository, agent_run_id, usage=token_usage,
            status="failed", error_message=error_message, clock=clock,
        )

    _notify(progress, "validation", "Validating candidate structure")
    normalized = mode.normalize(
        merged, inputs, vault, now, subject_id=subject_id, items_off=items_off, nominator=nominator,
        facet_identity_plan=facet_identity_plan,
    )
    duplicate_diagnostics = _duplicate_client_id_diagnostics(normalized.rows) if mode.checks_client_id_collisions else []
    if duplicate_diagnostics:
        _fail("duplicate synthesis client item ids", {"gate_diagnostics": duplicate_diagnostics})
        raise StudyMapError(
            "duplicate_client_item_ids",
            "Synthesis shards produced colliding client item identifiers.",
            diagnostics=duplicate_diagnostics,
            synthesis_run_id=synthesis_run_id,
            candidate_preserved=True,
        )

    # identifiability analysis (real §11.3 check) — findings drive both the
    # gate hook and the persisted generate-discriminator needs.
    _notify(progress, "validation", "Running quality gates")
    findings = []
    if mode.analyzes_identifiability:
        view = build_proposal_view(
            facets=normalized.facet_payloads,
            criterion_targets=normalized.criterion_targets,
            recipe_components=normalized.recipe_components,
        )
        findings = analyze_identifiability(view)
    gate_ctx = _gate_context(
        vault, repository, inputs, findings, nominator=nominator, append_mode=mode.append_vocabulary,
    )
    gate_proposal = GateProposal(
        items=normalized.gate_items,
        conflict_candidates=normalized.conflict_candidates,
        non_conflict_dispositions=normalized.non_conflict_dispositions,
    )
    report = run_synthesis_gates(gate_proposal, gate_ctx)
    diagnostics = [diag.to_dict() for diag in report.diagnostics]
    diagnostics.extend(normalized.edge_diagnostics)
    diagnostics.extend(answer_diagnostics)

    if report.blocked:
        _fail("synthesis gates hard-failed", {"gate_diagnostics": diagnostics})
        code, message = mode.gate_failure
        raise StudyMapError(
            code, message, diagnostics=diagnostics,
            synthesis_run_id=synthesis_run_id if mode.keeps_candidate_for_repair else None,
            candidate_preserved=mode.keeps_candidate_for_repair,
        )

    # Stage-5.3/6 instrument gates over the practice-item rows, via the one
    # shared composition every authoring lane runs (`authoring_gates`). The §8.7
    # gates above check provenance/scope/structure; these check whether an item
    # measures anything, so an item authored at ingest reaches review with its
    # persona/selected-response/pair judgement. Row-level verdicts, never batch
    # aborts: a refused item
    # persists as `invalid` (acceptance refuses it) rather than discarding the
    # paid-for synthesis. No ``client`` (revalidation) falls back to the
    # deterministic persona rule; missing persona material stays a typed
    # UNTESTED abstention, so first ingests are not blocked.
    from learnloop.content.authoring.authoring_gates import build_instrument_gates

    instrument_gates = build_instrument_gates(
        vault, repository, grading_client=client
    )
    instrument_gates(normalized.rows)
    diagnostics.extend(instrument_gates.diagnostics())

    match = match_proposal(
        repository, source_set_id=source_set.id, purpose=mode.proposal_purpose, rows=normalized.rows,
    )
    if match is not None and match.kind == "rejected":
        if not fresh_answers:
            raise RejectedProposalMatch(match.proposal_id)
        match = None
    # A mode with an auto-apply lane records the ids it may apply, on a match too: they apply the match's
    # waiting items.
    coverage: dict[str, Any] = {"gate_diagnostics": diagnostics}
    if normalized.auto_apply_ids is not None:
        coverage["auto_apply_item_ids"] = normalized.auto_apply_ids
    if match is not None:
        repository.complete_synthesis_run(
            synthesis_run_id, status="completed", proposal_id=match.proposal_id,
            resolved_span_hashes=resolved_hashes,
            coverage_decisions={**coverage, "matched_proposal": {"proposal_id": match.proposal_id, "kind": match.kind}},
            actual_usage=recorded_usage,
        )
        finish_agent_run(repository, agent_run_id, client, usage=token_usage, clock=clock)
        return match.proposal_id, diagnostics, [], normalized, match

    # persist generate-discriminator / coarsen needs (FIRST, per §11.3).
    generation_needs = _persist_generation_needs(repository, subject_id, source_set.id,
                                                  synthesis_run_id, findings, clock=clock)

    # persist the dependency-annotated proposal.
    _notify(progress, "persistence", "Persisting the study-map proposal")
    patch_id = new_ulid()
    repository.persist_proposal_batch(
        {
            "id": patch_id,
            "agent_run_id": agent_run_id,
            "purpose": mode.proposal_purpose,
            "source_refs": [],
            "summary": getattr(merged, "summary", "") or mode.summary_fallback.format(subject=subject_id),
            "created_at": now,
            "updated_at": now,
        },
        normalized.rows,
    )
    if nominator is not None:
        coverage["graph_nomination"] = {
            **(normalized.graph_nomination or {}), "summary": nominator.summary(),
        }
    if facet_identity_plan is not None:
        from learnloop.content.facet_identity.actions import record_proposed_actions

        coverage["facet_identity"] = {
            **facet_identity_plan.summary(),
            "action_ids": record_proposed_actions(
                repository, normalized.facet_identity_actions, origin=mode.facet_action_origin,
                run_id=synthesis_run_id, proposal_id=patch_id, clock=clock,
            ),
        }
    repository.complete_synthesis_run(
        synthesis_run_id, status="completed", proposal_id=patch_id,
        resolved_span_hashes=resolved_hashes,
        coverage_decisions=coverage,
        actual_usage=usage,
    )
    finish_agent_run(repository, agent_run_id, client, usage=token_usage, clock=clock)
    return patch_id, diagnostics, generation_needs, normalized, None


@dataclass(frozen=True)
class SynthesisAnswer:
    """One answer of a mode's model call, as the run's tail reads it."""

    #: What facet identity, the normalizer and the summaries read.
    candidate: Any
    span_request_count: int = 0
    #: The span hashes the call resolved; None: the mode does not record them, and the run records none.
    resolved_span_hashes: list[str] | None = None
    #: The call's own usage record (None: the mode does not record it); facet identity's joins it.
    usage: dict[str, Any] | None = None
    #: The mode's review records about the answer itself, reported after the normalizer's.
    diagnostics: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class SynthesisRun:
    """A synthesis run its head has opened (:func:`open_synthesis_run`: the manifest, agent run and synthesis run
    rows): what the mode's call and the run's tail read."""

    vault: LoadedVault
    repository: Repository
    root: Path
    source_set: SourceSet
    inputs: _SynthesisInputs
    #: Resolved (``resolve_brief``): the request renders it; items off and the epigraphs read it.
    brief: dict[str, Any]
    now: str
    clock: Clock | None
    agent_run_id: str
    synthesis_run_id: str
    client: Any
    nominator: Any
    facet_identity_client: Any
    #: The persisted manifest; its ``manifest_hash`` names it.
    manifest: dict[str, Any]
    #: The ingest budgets with the run's overrides, and the part of them its manifest records.
    budgets: Any
    token_budget: dict[str, Any]
    provider: str
    model: str | None
    #: Facet identity is on, so the prompt carries the one-facet-per-skill rule.
    one_facet_per_skill: bool
    progress: ProgressFn | None = None
    #: What the mode's request reads beyond the source set's inputs (the append's new inventories, the context of the
    #: neighbourhood around them, its change kind and revision diff); the mode's epigraph digest reads it too. None:
    #: the inputs alone (bootstrap).
    context: Any = None
    #: No budget is enforced; spend is still counted.
    unlimited_token_budget: bool = False


@dataclass(frozen=True)
class RunScope:
    """What a mode decides from the source set's inputs before its manifest is built (``decide_scope`` in
    :func:`open_synthesis_run`): the manifest's ``scope`` and, for an append, the revisions it names and the context
    its request reads."""

    scope: Any
    #: The revisions the manifest names. None: the source set's selected revisions.
    revision_ids: list[str] | None = None
    context: Any = None


def open_synthesis_run(
    vault: LoadedVault,
    repository: Repository,
    root: Path,
    source_set_id: str,
    mode: SynthesisMode,
    *,
    client: Any,
    brief: Mapping[str, Any],
    decide_scope: Callable[[dict[str, Any], _SynthesisInputs, Any, GraphNominator | None], RunScope],
    clock: Clock | None,
    budget_overrides: Mapping[str, int] | None = None,
    unlimited_token_budget: bool = False,
    embedding_client_factory: Callable[[], Any] | None = None,
    facet_identity_client: Any = None,
    progress: ProgressFn | None = None,
    requested_mode: str = "auto",
) -> SynthesisRun:
    """Open one synthesis run, for both modes: find the source set, resolve the brief, read the inputs, let the mode
    decide its scope, then persist the manifest that records all of it and open the agent run and the synthesis run.

    ``decide_scope(brief, inputs, budgets, nominator)`` is the mode's own step: bootstrap records the brief's scope;
    an append selects its new inventories and the neighbourhood around them and records both. Every refusal here (an
    unknown source set, a mode the caller may not ask for: ``requested_mode`` is create_study_map's ``mode``) comes
    before anything is read or written. Before the manifest, only the mode's step may write (an append's
    neighbourhood embeds and stores vectors when nominations are on, since the manifest records what they
    compared)."""

    source_set = next((s for s in vault.source_sets if s.id == source_set_id), None)
    if source_set is None:
        raise StudyMapError("source_set_not_found", f"Source set '{source_set_id}' does not exist.")
    resolved_brief = resolve_brief(vault, brief)
    if requested_mode not in ("auto", mode.name):
        raise StudyMapError(
            "unsupported_mode", f"mode '{requested_mode}' is not supported by create_study_map (append is ING M7).",
        )

    inputs = _collect_inputs(repository, vault, source_set)
    # Per-run overrides layer over the vault's budgets and ride into the manifest's token_budget, so an override is
    # on the run's record rather than an invisible tweak.
    budgets = vault.config.ingest.budgets.model_copy(update=dict(budget_overrides or {}))
    # Slice 2 T5: embedding nominations for the structuring pass, the mint shadow and an append's neighbourhood
    # (None when switched off).
    nominator = GraphNominator.for_ingest(vault, repository, client_factory=embedding_client_factory)
    decided = decide_scope(resolved_brief, inputs, budgets, nominator)

    one_facet_per_skill = bool(vault.config.facet_identity.enabled)
    prompt_version = mode.prompt_version(one_facet_per_skill)
    provider = getattr(client, "provider_name", None) or getattr(client, "provider_type", None) or "codex"
    model = getattr(client, "model", None)
    recorded = mode.unlimited_recorded_budgets if unlimited_token_budget else mode.recorded_budgets
    token_budget = {**({"unlimited": True} if unlimited_token_budget else {}),
                    **{name: getattr(budgets, name) for name in recorded}}
    source_inputs = manifest_inputs(inputs)
    if decided.revision_ids is not None:
        source_inputs["revision_ids"] = decided.revision_ids
    manifest = build_manifest(
        vault,
        source_set_id=source_set.id,
        **source_inputs,
        scope=decided.scope,
        brief=resolved_brief,
        prompt_version=prompt_version,
        provider=provider,
        model=model,
        assessment_schema_version=(inputs.exam_profile or {}).get("schema_version") if inputs.exam_profile else None,
        token_budget=token_budget,
        clock=clock,
    )
    # Before the run rows: the synthesis run points at the manifest by id, and the agent run records its hash.
    persist_manifest(repository, manifest)
    manifest_id = repository.synthesis_manifest_by_hash(manifest["manifest_hash"])["id"]

    now = utc_now_iso(clock)
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": mode.agent_purpose,
            "provider": provider,
            "provider_type": getattr(client, "provider_type", "codex"),
            "model": model,
            "prompt_template": mode.prompt_template,
            "prompt_version": prompt_version,
            "input_context_hash": agent_run_input_context_hash(manifest),
            "output_schema": mode.output_schema,
            "started_at": now,
            "status": "running",
        }
    )
    synthesis_run_id = repository.insert_synthesis_run(
        manifest_id=manifest_id, mode=mode.name, agent_run_id=agent_run_id,
    )
    return SynthesisRun(
        vault=vault, repository=repository, root=root, source_set=source_set, inputs=inputs, brief=resolved_brief,
        now=now, clock=clock, agent_run_id=agent_run_id, synthesis_run_id=synthesis_run_id, client=client,
        nominator=nominator, facet_identity_client=facet_identity_client, manifest=manifest, budgets=budgets,
        token_budget=token_budget, provider=provider, model=model, one_facet_per_skill=one_facet_per_skill,
        progress=progress, context=decided.context, unlimited_token_budget=unlimited_token_budget,
    )


@dataclass
class SynthesisOutcome:
    """What a run's tail persisted or matched, and what its apply step added."""

    proposal_id: str
    match: ProposalMatch | None
    normalized: Normalized
    gate_diagnostics: list[dict[str, Any]]
    generation_needs: list[dict[str, Any]]
    answer: SynthesisAnswer
    #: The fields the mode's apply step adds to its result.
    applied: dict[str, Any] = field(default_factory=dict)
    facet_identity: dict[str, Any] | None = None

    @property
    def reused(self) -> bool:
        return self.match is not None

    @property
    def nothing_new(self) -> bool:
        return self.match is not None and self.match.kind == "settled"


def finish_synthesis_run(
    run: SynthesisRun,
    mode: SynthesisMode,
    *,
    apply: Callable[[SynthesisOutcome], dict[str, Any]],
) -> SynthesisOutcome:
    """Everything a synthesis run does once its head has opened it, for both modes: ask the model (the shard runner,
    under the mode's call), plan facet identity, gate and persist the proposal (or match an earlier one), finalize the
    run rows, apply, write epigraphs.

    The model is asked at most twice: the second time only after the rows equalled a proposal the learner wholly
    rejected, whose answers were dropped (``proposal_match``). Any failure up to the persisted proposal fails both
    run rows. Apply and epigraphs run after, outside those arms, so a failed apply leaves the run completed and its
    proposal waiting, which answers the retry. ``apply`` is the mode's own behaviour: what it applies once the
    proposal stands and what follows (bootstrap: the whole map and the exam goal; append: §10.3's routine items, the
    study-map diff and the facet doctor). It returns the fields it adds to the mode's result."""

    repository, client = run.repository, run.client
    answers = _SavedAnswers()

    def ask() -> SynthesisAnswer:
        with declared_budgets(run.token_budget) if mode.declares_its_budgets else nullcontext():
            return _run_synthesis(run, mode, answers)

    def drop_answers() -> None:
        answers.discard(repository, forget=mode.forgets_dropped_answers)

    items_off = run.brief["practice_items"] == "as_you_read"
    # A metered mode drains its client ONCE per answer, into a local threaded to every arm that finalizes the
    # run: the gate stage completes the agent run, and a gate failure completes it again out here, where a second
    # drain would return zeros and erase the cost already recorded.
    token_usage = TokenUsage() if mode.meters_the_model_call else None
    usage: dict[str, Any] | None = None
    candidate_preserved = False
    try:
        for fresh_answers in (False, True):
            answer = ask()
            if token_usage is not None:
                token_usage += consume_client_usage(client)
            facet_identity_plan = _facet_identity_plan(
                answer.candidate, run.vault, repository, run.synthesis_run_id, nominator=run.nominator,
                client=run.facet_identity_client, progress=run.progress,
            )
            usage = answer.usage
            if facet_identity_plan is not None:
                usage = {**(usage or {}), "facet_identity": facet_identity_plan.as_dict()}
            if mode.keeps_candidate_for_repair:
                candidate = answer.candidate
                repository.save_synthesis_candidate(
                    run.synthesis_run_id,
                    candidate.model_dump(mode="json") if hasattr(candidate, "model_dump") else dict(candidate),
                )
                candidate_preserved = True
            try:
                proposal_id, diagnostics, generation_needs, normalized, match = _gate_and_persist(
                    run.vault, repository, run.source_set, answer.candidate, run.inputs, mode=mode,
                    subject_id=(resolve_subject_id(run.source_set, run.vault) if mode.resolves_an_empty_subject
                                else run.source_set.subject_id),
                    agent_run_id=run.agent_run_id, synthesis_run_id=run.synthesis_run_id,
                    now=run.now, usage=usage, resolved_hashes=answer.resolved_span_hashes,
                    clock=run.clock, progress=run.progress, items_off=items_off,
                    token_usage=token_usage, client=client, nominator=run.nominator,
                    facet_identity_plan=facet_identity_plan, fresh_answers=fresh_answers,
                    answer_diagnostics=answer.diagnostics,
                )
            except RejectedProposalMatch:
                drop_answers()
                continue
            break
    except StudyMapError as exc:
        if candidate_preserved:
            exc.candidate_preserved = True
            exc.synthesis_run_id = run.synthesis_run_id
        if exc.code == mode.gate_failure[0]:
            # A rejected answer is the model's: kept, every retry would replay it into the same rejection at zero
            # cost. A repair works on the preserved candidate, not on these.
            drop_answers()
        repository.complete_synthesis_run(
            run.synthesis_run_id,
            status="failed",
            coverage_decisions={"gate_diagnostics": exc.diagnostics} if exc.diagnostics else None,
            actual_usage=None if mode.usage_only_with_a_proposal else usage,
        )
        # A metered run adds what was spent since its last drain (nothing unless the model call itself failed:
        # a sharded run that died mid-flight still spent tokens); an unmetered one drains here.
        if token_usage is not None:
            token_usage += consume_client_usage(client)
        finish_agent_run(
            repository, run.agent_run_id, client, usage=token_usage,
            status="failed", error_message=f"{exc.code}: {exc}", clock=run.clock,
        )
        raise
    except Exception as exc:  # pragma: no cover - defensive
        repository.complete_synthesis_run(run.synthesis_run_id, status="failed")
        if token_usage is not None:
            token_usage += consume_client_usage(client)
        finish_agent_run(
            repository, run.agent_run_id, client, usage=token_usage,
            status="failed", error_message=str(exc), clock=run.clock,
        )
        raise

    outcome = SynthesisOutcome(
        proposal_id=proposal_id, match=match, normalized=normalized, gate_diagnostics=diagnostics,
        generation_needs=generation_needs, answer=answer,
    )
    outcome.applied = apply(outcome)
    if match is not None:
        # Nothing new was persisted, so there is nothing new to write epigraphs
        # about; the earlier proposal's run recorded its facet identity.
        return outcome
    outcome.facet_identity = facet_identity_result(run.root, repository, facet_identity_plan, run.synthesis_run_id)

    # Best-effort Start-screen epigraphs about the freshly synthesized material.
    # Never raises; nothing here can change the outcome. Sits after apply so a
    # failed apply still surfaces first, and outside `_gate_and_persist` because
    # revalidation reuses that with no client.
    summary = str(getattr(answer.candidate, "summary", "") or "")
    digest = mode.epigraph_digest(normalized.rows, run.context, summary)
    generate_vault_epigraphs(
        repository, run.vault, client,
        subject_id=run.source_set.subject_id, source_set_id=run.source_set.id,
        synthesis_run_id=run.synthesis_run_id, mode=mode.name, digest=digest,
        brief=run.brief, clock=run.clock,
    )
    return outcome


_SHARD_PREFIX_RE = re.compile(r"^shard_\d+__")

# Candidate item collections whose entries declare a ``client_item_id``.
_CANDIDATE_ITEM_FIELDS = ("concepts", "facets", "learning_objects", "blueprints", "practice_items")


def derive_candidate_repairs(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    """Mechanically-safe repair ops for a preserved synthesis candidate.

    Only failure classes with a provably-correct fix are derived; anything
    requiring judgment stays a hard gate failure for a human or agent to
    resolve via explicit ``repair_ops``. Current classes:

    - item-level dependencies that reference a rubric criterion id: criteria
      are embedded inside practice-item rubrics and are never proposal items,
      so the reference can never close. Criterion ordering already lives in
      the rubric's own ``depends_on``; dropping the item-level echo loses
      nothing.
    """

    declared: set[str] = set()
    for field_name in _CANDIDATE_ITEM_FIELDS:
        for entry in candidate.get(field_name) or []:
            cid = str((entry or {}).get("client_item_id") or "")
            if cid:
                declared.add(cid)
    criterion_ids = {
        str((criterion or {}).get("id") or "")
        for item in candidate.get("practice_items") or []
        for criterion in (item or {}).get("criteria") or []
    } - {""}

    ops: list[dict[str, Any]] = []
    for item in candidate.get("practice_items") or []:
        item_cid = str((item or {}).get("client_item_id") or "")
        for dep in (item or {}).get("depends_on_client_item_ids") or []:
            dep = str(dep)
            if dep in declared:
                continue
            bare = _SHARD_PREFIX_RE.sub("", dep)
            if bare in criterion_ids:
                ops.append(
                    {
                        "op": "drop_dependency",
                        "item_client_id": item_cid,
                        "dep": dep,
                        "reason": (
                            f"references rubric criterion '{bare}'; criterion ordering "
                            "is already encoded in the rubric's own depends_on"
                        ),
                    }
                )
    return ops


def apply_candidate_repairs(
    candidate: dict[str, Any], ops: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Apply typed repair ops to a candidate dict; returns (repaired, log).

    Ops vocabulary (each targets one practice item's ``depends_on_client_item_ids``):

    - ``drop_dependency``: {"op", "item_client_id", "dep"} — remove ``dep``.
    - ``remap_dependency``: {"op", "item_client_id", "dep", "to"} — replace
      ``dep`` with ``to``, which must be a declared client item id.

    The input candidate is never mutated. Every op is logged with an
    ``applied`` flag; an op that matches nothing is a recorded no-op so a
    repair prepared against a stale diagnostic cannot corrupt anything."""

    repaired = json.loads(json.dumps(candidate))
    declared: set[str] = set()
    for field_name in _CANDIDATE_ITEM_FIELDS:
        for entry in repaired.get(field_name) or []:
            cid = str((entry or {}).get("client_item_id") or "")
            if cid:
                declared.add(cid)
    items_by_client = {
        str((item or {}).get("client_item_id") or ""): item
        for item in repaired.get("practice_items") or []
    }

    log: list[dict[str, Any]] = []
    for op in ops:
        kind = str(op.get("op") or "")
        if kind not in {"drop_dependency", "remap_dependency"}:
            raise StudyMapError("unknown_repair_op", f"Unsupported candidate repair op: '{kind}'.")
        item = items_by_client.get(str(op.get("item_client_id") or ""))
        dep = str(op.get("dep") or "")
        deps = list((item or {}).get("depends_on_client_item_ids") or [])
        applied = item is not None and dep in deps
        if applied and kind == "drop_dependency":
            item["depends_on_client_item_ids"] = [d for d in deps if d != dep]
        elif applied and kind == "remap_dependency":
            to = str(op.get("to") or "")
            if to not in declared:
                raise StudyMapError(
                    "invalid_repair_target",
                    f"remap_dependency target '{to}' is not a declared client item id.",
                )
            item["depends_on_client_item_ids"] = [to if d == dep else d for d in deps]
        log.append({**op, "applied": applied})
    return repaired, log


def revalidate_synthesis_candidate(
    root: Path,
    synthesis_run_id: str,
    *,
    apply: bool = False,
    create_goal: bool = False,
    repair: bool = False,
    repair_ops: list[dict[str, Any]] | None = None,
    repository: Repository | None = None,
    clock: Clock | None = None,
    progress: ProgressFn | None = None,
    apply_gate: Callable[[], bool] | None = None,
) -> StudyMapResult:
    """Re-run normalization, gates, and persistence over a preserved candidate
    with ZERO model calls.

    A post-generation failure (gate hard-fail, id collision, persistence error)
    leaves the expensive merged candidate staged on its synthesis run
    (``candidate_output_json``). After the offending code/config is fixed, this
    finishes the pipeline from that checkpoint instead of paying for another
    model run. Gate failures re-raise typed, with the candidate still preserved.

    ``repair=True`` first derives mechanically-safe repair ops from the
    preserved candidate (see :func:`derive_candidate_repairs`); explicit
    ``repair_ops`` — authored by a user or a repair agent from the gate
    diagnostics — are applied after the derived ones. The stored candidate is
    left untouched; the applied-op log travels on ``actual_usage`` and the
    result for auditability."""

    from learnloop.content.synthesis.ai_contracts import SourceSetSynthesis

    vault = load_vault(root)
    if repository is None:
        repository = vault_repository(VaultPaths(vault.root, vault.config))
    run = repository.synthesis_run(synthesis_run_id)
    if run is None:
        raise StudyMapError(
            "synthesis_run_not_found", f"Synthesis run '{synthesis_run_id}' does not exist."
        )
    if run.get("status") == "completed":
        raise StudyMapError(
            "synthesis_already_completed",
            f"Synthesis run '{synthesis_run_id}' already completed; nothing to revalidate.",
        )
    candidate = run.get("candidate_output")
    if not candidate:
        raise StudyMapError(
            "no_saved_candidate",
            f"Synthesis run '{synthesis_run_id}' preserved no candidate; retry synthesis instead.",
        )
    manifest = repository.synthesis_manifest(run["manifest_id"]) or {}
    source_set_id = str(manifest.get("source_set_id") or "")
    source_set = next((s for s in vault.source_sets if s.id == source_set_id), None)
    if source_set is None:
        raise StudyMapError("source_set_not_found", f"Source set '{source_set_id}' does not exist.")
    subject_id = resolve_subject_id(source_set, vault)

    inputs = _collect_inputs(repository, vault, source_set)
    ops = derive_candidate_repairs(candidate) if repair else []
    ops.extend(repair_ops or [])
    repair_log: list[dict[str, Any]] = []
    if ops:
        candidate, repair_log = apply_candidate_repairs(candidate, ops)
    merged = SourceSetSynthesis.model_validate(candidate)
    now = utc_now_iso(clock)
    usage = dict(run.get("actual_usage") or {})
    usage["revalidations"] = int(usage.get("revalidations") or 0) + 1
    stored_plan = (
        FacetIdentityPlan.from_dict(usage.get("facet_identity")) if vault.config.facet_identity.enabled else None
    )
    if repair_log:
        usage["candidate_repairs"] = list(usage.get("candidate_repairs") or []) + repair_log
    try:
        patch_id, diagnostics, generation_needs, normalized, match = _gate_and_persist(
            vault, repository, source_set, merged, inputs, mode=BOOTSTRAP,
            subject_id=subject_id,
            agent_run_id=run.get("agent_run_id"),
            synthesis_run_id=synthesis_run_id,
            now=now, usage=usage,
            resolved_hashes=[str(h) for h in run.get("resolved_span_hashes") or []],
            clock=clock, progress=progress,
            # Replay the item-authoring decision stamped into the manifest brief.
            items_off=(dict(manifest.get("brief") or {}).get("practice_items") == "as_you_read"),
            # Zero model calls: stored (content-addressed) vectors only.
            nominator=GraphNominator.for_review(vault),
            # The run's own facet-identity decisions, replayed (no judge call),
            # only while the switch is on (off, the run is as it would be without facet identity).
            facet_identity_plan=stored_plan,
        )
    except StudyMapError as exc:
        exc.candidate_preserved = True
        exc.synthesis_run_id = synthesis_run_id
        raise
    except RejectedProposalMatch as rejected:
        # A repair pays nothing, so it cannot ask for fresh answers; persisting
        # would put back what the learner rejected. The candidate is not offered
        # again, so the card's Retry runs a fresh synthesis.
        repository.complete_synthesis_run(synthesis_run_id, status="failed", actual_usage=usage)
        finish_agent_run(repository, run.get("agent_run_id"), status="failed",
                         error_message="matches_rejected_proposal", clock=clock)
        raise StudyMapError(
            "matches_rejected_proposal",
            f"The repaired candidate equals proposal {rejected.proposal_id}, which was rejected; "
            "retry synthesis for a fresh answer.",
            synthesis_run_id=synthesis_run_id,
        ) from rejected

    result = StudyMapResult(
        source_set_id=source_set.id, subject_id=subject_id,
        mode=str(run.get("mode") or "bootstrap"),
        manifest_hash=str(manifest.get("manifest_hash") or ""),
        synthesis_run_id=synthesis_run_id, proposal_id=patch_id,
        reused=match is not None, nothing_new=match is not None and match.kind == "settled",
        item_counts=_count_items(normalized.rows), gate_diagnostics=diagnostics,
        generation_needs=generation_needs, candidate_repairs=repair_log,
    )
    if apply and not result.nothing_new and _gate_open(apply_gate):
        _apply_and_wire_goal(
            root, repository, result, brief=dict(manifest.get("brief") or {}), create_goal=create_goal,
            clock=clock, facet_ids=normalized.facet_ids, progress=progress,
        )
    result.facet_identity = facet_identity_result(root, repository, stored_plan, synthesis_run_id)
    return result


@dataclass
class _SynthesisBudget:
    """One synthesis run's spend against its ingest token budgets.

    Input is a preflight estimate of every full request (instructions, schema
    and context), topped up by provider-reported input when that is larger.
    Output is charged per pass as the larger of the result-size estimate and
    the provider's report. With ``unlimited`` set, spend is still counted for
    the usage record but no limit is enforced.
    """

    budgets: Any
    unlimited: bool
    calls: int = 0
    input_tokens_estimate: int = 0
    output_tokens_spent: int = 0

    def input_ceiling(self) -> int | None:
        return None if self.unlimited else self.budgets.synthesis_total_input_ceiling

    def remaining_output(self) -> int | None:
        return None if self.unlimited else max(0, self.budgets.synthesis_output_tokens - self.output_tokens_spent)

    def check_base_passes(self, unpaid: list[int]) -> None:
        """``unpaid``: the input of each base pass no checkpoint answers; together they must fit the ceiling."""

        ceiling = self.input_ceiling()
        needed = sum(unpaid)
        if ceiling is not None and needed > ceiling:
            raise StudyMapError(
                "budget_exceeded",
                f"Uncached synthesis base passes need about {needed} input tokens, over the "
                f"total-input ceiling of {ceiling}. Each pass counts the full request: "
                "instructions, output schema, brief, registry index and the shard's inventories. "
                "Narrow the source scope or raise synthesis_total_input_ceiling.",
            )

    def check_next_pass_input(self, tokens: int, *, reserve: int) -> None:
        """``reserve`` holds back the input of base passes still to run."""

        ceiling = self.input_ceiling()
        if ceiling is not None and self.input_tokens_estimate + tokens + reserve > ceiling:
            raise StudyMapError("budget_exceeded", "The next synthesis pass would exceed the total-input ceiling; completed passes are saved.")

    def pass_output_limit(self) -> int | None:
        if self.unlimited:
            return None
        limit = min(self.budgets.synthesis_shard_output_tokens, self.budgets.synthesis_output_tokens - self.output_tokens_spent)
        if limit <= 0:
            raise StudyMapError("budget_exceeded", "The synthesis output budget is exhausted; completed passes are saved.")
        return limit

    def charge_pass(self, *, estimated_input: int, reported_input: int, output: int) -> None:
        self.calls += 1
        self.input_tokens_estimate += max(estimated_input, reported_input)
        self.output_tokens_spent += output

    def check_pass_output(self, charge: int, limit: int | None) -> None:
        """A fresh pass's output, charged the larger of its size and the provider's report, against its limit."""

        if limit is not None and charge > limit:
            raise StudyMapError("budget_exceeded", "A synthesis pass exceeded its output budget.")

    def check_shard_output(self, result: Any) -> None:
        if not self.unlimited and _result_tokens(result) > self.budgets.synthesis_shard_output_tokens:
            raise StudyMapError("budget_exceeded", "A synthesis shard exceeded its output budget.")

    def check_merged_output(self, merged: Any, message: str) -> None:
        if not self.unlimited and _result_tokens(merged) > self.budgets.synthesis_output_tokens:
            raise StudyMapError("budget_exceeded", message)


@dataclass
class _SavedAnswers:
    """The saved model answers one synthesis run's candidate came from: each
    shard's result and each pass's checkpoint, fresh or reused.

    Dropped when the gates reject the candidate: kept, they replay it into the
    same rejection at zero cost on every fresh retry, while the card offers
    Retry. A budget failure keeps them (a raised budget reuses what was paid).
    A shard reused from its row made one request, so its base pass is all it
    stands for; a shard with a span round runs both passes and both join."""

    #: Each served answer: its key and the stored form it was served from (a
    #: shard row's output; a pass checkpoint's result). Dropped only while it
    #: is still the saved one: another run may have dropped it already and
    #: saved a fresh answer under the same key.
    shards: list[tuple[str, Any]] = field(default_factory=list)
    passes: list[tuple[str, Any]] = field(default_factory=list)

    def discard(self, repository: Repository, *, forget: bool = True) -> None:
        """Drop every answer served so far. ``forget``: and forget them, so a later drop in the same run (a fresh
        answer the gates reject after a rejected match) names only the answers judged since; kept, it names these
        again, and deletes one only if the store holds that exact answer again (``SynthesisMode.forgets_dropped_answers``)."""

        for key, output in self.shards:
            repository.discard_synthesis_shard_result(key, output=output)
        for key, stored in self.passes:
            repository.discard_model_checkpoint(key, result=stored)
        if forget:
            self.shards.clear()
            self.passes.clear()


def _run_synthesis(run: SynthesisRun, mode: SynthesisMode, answers: _SavedAnswers) -> SynthesisAnswer:
    """The shard runner, for both modes: split the run's input into the mode's units, ask each one (a base pass and at
    most one span round, each answered by its checkpoint when the same request was paid before), then let the mode
    finish the candidate. Every answer served, fresh or reused, joins ``answers``, which the tail drops when the gates
    or the learner reject the candidate.

    The budget rule is the mode's (``call.spend``): an input preflight over every base pass still to pay before
    anything is sent, then each pass checked before it is sent, run under its output limit, saved before its output
    is checked (a paid answer is kept for a retry under a larger budget), and checked again after."""

    call, repository, budgets, client, progress = mode.call, run.repository, run.budgets, run.client, run.progress
    shards = call.shards(run)
    context_for = call.contexts(run)
    merged = None
    span_request_count = 0
    resolved_hashes: list[str] = []
    reused_shards = 0
    spend = call.spend(budgets, run.unlimited_token_budget)
    schema = call.result_model.model_json_schema()
    settings = {**model_settings(client), "provider": run.provider, "model": run.model}

    def pass_request(context):
        prompt = call.prompt(context)
        tokens = max(1, (len(prompt) + len(json.dumps(schema))) // 4)
        key = call.checkpoint_key(prompt, settings)
        return ModelCheckpoint(repository, key, call.checkpoint_purpose, call.result_model.model_validate), tokens

    # Durable per-shard checkpoints: resolve every shard's cache slot up front so
    # the total-input preflight only charges for shards that will actually run.
    # A completed shard is filed under its first pass's request key: a key of
    # its own (labels and inputs, as before) kept answering after a prompt or
    # schema edit that every pass request reflects. Budgets stay out of it, so
    # a retry under revised ceilings still reuses the shard. The key names the
    # first request only, so a shard that also had a span round is never
    # answered here: its second request depends on the span cap and count and
    # on the spans' text, and a changed one must be sent. Its passes run again,
    # each answered by its own checkpoint when unchanged.
    shard_states: list[tuple[int, list[dict[str, Any]], str, dict[str, Any] | None]] = []
    base_reserves = {}
    for ordinal, shard in enumerate(shards):
        checkpoint, tokens = pass_request(context_for(shard, ordinal, len(shards), []))
        cached = repository.synthesis_shard_result(checkpoint.key) if call.sharded else None
        cached = cached if cached and cached.get("output") else None
        if cached is not None and int(cached["output"].get("span_request_count") or 0):
            cached = None
        shard_states.append((ordinal, shard, checkpoint.key, cached))
        base_reserves[ordinal] = 0 if cached or checkpoint.load() is not None else tokens
    spend.check_base_passes([tokens for tokens in base_reserves.values() if tokens])

    def run_pass(context, *, future_input_reserve=0):
        checkpoint, tokens = pass_request(context)
        fetched = checkpoint.fetch()
        if fetched is not None:
            answers.passes.append((checkpoint.key, fetched[1]))
            return fetched[0]
        spend.check_next_pass_input(tokens, reserve=future_input_reserve)
        output_limit = spend.pass_output_limit()
        meter = UsageMeter(client)
        with generation_limit(output_limit):
            result = call.request(client, context)
        output_charge = meter.output_charge(_result_tokens(result))
        spend.charge_pass(estimated_input=tokens, reported_input=meter.reported().input_tokens, output=output_charge)
        # Save before the budget check: the key has no budget in it, so a
        # retry under a larger one reuses this paid answer.
        stored = checkpoint.save(result, {"input_tokens_estimate": tokens, "output_tokens_estimate": _result_tokens(result)})
        answers.passes.append((checkpoint.key, stored))
        spend.check_pass_output(output_charge, output_limit)
        return result

    for ordinal, shard, shard_key, cached in shard_states:
        if cached is not None:
            output = cached["output"]
            # A one-request shard: its row and its base pass hold the same answer.
            answers.shards.append((shard_key, output))
            answers.passes.append((shard_key, output.get("result") or {}))
            result = call.result_model.model_validate(output.get("result") or {})
            span_request_count += int(output.get("span_request_count") or 0)
            resolved_hashes.extend(str(h) for h in output.get("resolved_span_hashes") or [])
            reused_shards += 1
            _notify(progress, "synthesis",
                    f"Reusing completed shard {ordinal + 1} of {len(shards)}",
                    current=ordinal + 1, total=len(shards))
            result = _namespace_synthesis_shard(result, ordinal)
            merged = _merge_synthesis(merged, result) if merged is not None else result
            continue

        _notify(progress, "synthesis",
                f"Synthesizing shard {ordinal + 1} of {len(shards)}",
                current=ordinal + 1, total=len(shards))
        future_reserve = sum(tokens for next_ordinal, tokens in base_reserves.items() if next_ordinal > ordinal)
        result = run_pass(context_for(shard, ordinal, len(shards), []), future_input_reserve=future_reserve)
        spend.check_shard_output(result)
        shard_span_requests = 0
        shard_hashes: list[str] = []
        requests = [r if isinstance(r, dict) else r.model_dump() for r in getattr(result, "span_requests", []) or []]
        if requests:
            shard_span_requests = len(requests)
            _notify(progress, "synthesis",
                    f"Resolving evidence spans for shard {ordinal + 1} of {len(shards)}",
                    current=ordinal + 1, total=len(shards))
            resolved, shard_hashes = _resolve_span_requests(
                repository, requests, run.inputs,
                max_count=budgets.synthesis_span_request_max_count,
                char_cap=budgets.synthesis_span_char_cap,
            )
            # Reserve the remaining base shards before spending on optional
            # evidence expansion. Re-check before every subsequent base call.
            result = run_pass(context_for(shard, ordinal, len(shards), resolved), future_input_reserve=future_reserve)
            spend.check_shard_output(result)
        span_request_count += shard_span_requests
        resolved_hashes.extend(shard_hashes)
        if call.sharded:
            # Checkpoint AFTER the output-budget check so an oversized shard is
            # regenerated on retry rather than reused into the same failure.
            shard_output = {
                "result": result.model_dump(mode="json"),
                "span_request_count": shard_span_requests,
                "resolved_span_hashes": shard_hashes,
            }
            repository.save_synthesis_shard_result(
                shard_key=shard_key, shard_ordinal=ordinal, shard_count=len(shards),
                manifest_hash=run.manifest["manifest_hash"], result=shard_output, clock=run.clock,
            )
            answers.shards.append((shard_key, shard_output))
            result = _namespace_synthesis_shard(result, ordinal)
        merged = _merge_synthesis(merged, result) if merged is not None else result
        spend.check_merged_output(merged, "Merged synthesis exceeded its total output budget; completed shards are saved.")

    if merged is None:
        merged = call.result_model()
    candidate, usage, diagnostics = call.after_passes(
        run, merged, spend=spend, answers=answers, settings=settings, shard_count=len(shards),
    )
    usage = {**usage,
             "calls": spend.calls,
             "input_tokens_estimate": spend.input_tokens_estimate,
             "output_tokens_charged": spend.output_tokens_spent,
             "shard_count": len(shards),
             "reused_shards": reused_shards}
    return SynthesisAnswer(
        candidate, span_request_count,
        resolved_span_hashes=resolved_hashes if mode.records_resolved_span_hashes else None,
        usage=usage if mode.records_call_usage else None,
        diagnostics=diagnostics,
    )


def _bootstrap_pass_key(prompt: str, settings: dict[str, Any]) -> str:
    """Checkpoint identity of one bootstrap pass (:func:`_synthesis_pass_key` over its schema)."""

    return _synthesis_pass_key(prompt, SourceSetSynthesis.model_json_schema(), settings)


def _bootstrap_shards(run: SynthesisRun) -> list[list[dict[str, Any]]]:
    return _shards(run.inputs.unit_inventories, run.budgets.synthesis_shard_input_tokens)


def _bootstrap_contexts(run: SynthesisRun):
    registry = _registry_index(run.vault)

    def context(shard, ordinal, shard_count, resolved_spans):
        return SourceSetSynthesisContext(
            source_set_id=run.source_set.id, subject_id=run.source_set.subject_id, mode="bootstrap",
            brief=run.brief, unit_inventories=shard, exam_profile=run.inputs.exam_profile or {},
            registry_index=registry, resolved_spans=resolved_spans, shard_ordinal=ordinal, shard_count=shard_count,
            one_facet_per_skill=run.one_facet_per_skill,
        )

    return context


def _structure_merged(run: SynthesisRun, merged: Any, *, spend: Any, answers: _SavedAnswers,
                      settings: dict[str, Any], shard_count: int) -> tuple[Any, dict[str, Any], list[dict[str, Any]]]:
    """After a bootstrap's passes: concepts of the same title consolidated across shards, then the graph structured
    (its own checkpointed model call, held to what the passes left of the budgets)."""

    merged = _consolidate_same_title_concepts(merged)
    merged, structuring_usage = _model_graph_structuring(
        merged, run.client, run.source_set, run.inputs, run.repository, run.vault,
        shard_count=shard_count,
        input_tokens_estimate=spend.input_tokens_estimate,
        total_input_ceiling=spend.input_ceiling(),
        output_budget_tokens=spend.remaining_output(),
        progress=run.progress,
        nominator=run.nominator,
        settings=settings,
        answers=answers,
    )
    spend.calls += int(structuring_usage.pop("calls", 0))
    spend.input_tokens_estimate += int(structuring_usage.pop("input_tokens_estimate", 0))
    spend.check_merged_output(merged, "Merged synthesis exceeded its total output budget.")
    return merged, structuring_usage, []


def _rows_digest(rows: list[dict[str, Any]], _context: Any, summary: str) -> Any:
    return digest_from_proposal_rows(rows, summary=summary)


BOOTSTRAP_CALL = SynthesisCall(
    request=request_source_set_synthesis,
    prompt=source_set_synthesis_prompt,
    result_model=SourceSetSynthesis,
    checkpoint_key=_bootstrap_pass_key,
    checkpoint_purpose="synthesis_pass",
    shards=_bootstrap_shards,
    contexts=_bootstrap_contexts,
    spend=_SynthesisBudget,
    sharded=True,
    after_passes=_structure_merged,
)


BOOTSTRAP = SynthesisMode(
    name="bootstrap",
    agent_purpose=SYNTHESIS_AGENT_PURPOSE,
    prompt_template="source-set-synthesis",
    output_schema="SourceSetSynthesis",
    prompt_version=source_set_synthesis_prompt_version,
    recorded_budgets=(
        "synthesis_shard_input_tokens", "synthesis_shard_output_tokens", "synthesis_total_input_ceiling",
        "synthesis_output_tokens",
    ),
    unlimited_recorded_budgets=("synthesis_shard_input_tokens",),
    proposal_purpose=BOOTSTRAP_PROPOSAL_PURPOSE,
    summary_fallback="bootstrap study map for {subject}",
    gate_failure=("synthesis_gate_failed", "Synthesis proposal failed hard quality gates."),
    call=BOOTSTRAP_CALL,
    normalize=normalize,
    epigraph_digest=_rows_digest,
    append_vocabulary=False,
    facet_action_origin="ingest",
    keeps_candidate_for_repair=True,
    checks_client_id_collisions=True,
    analyzes_identifiability=True,
    meters_the_model_call=True,
    usage_only_with_a_proposal=False,
    records_call_usage=True,
    records_resolved_span_hashes=True,
    declares_its_budgets=True,
    forgets_dropped_answers=True,
    resolves_an_empty_subject=True,
)




def _synthesis_pass_key(
    prompt: str, schema: dict[str, Any], settings: dict[str, Any], *, purpose: str = "synthesis_pass",
) -> str:
    """Checkpoint identity of one synthesis pass: the request key of the
    exact prompt and schema sent, under the provider settings that shape the
    answer, with no budget in it. The append call keys the same way under its
    own ``purpose``."""

    return request_key(purpose=purpose, prompt=prompt, schema=schema, settings=settings)


def _result_tokens(result: Any) -> int:
    """Rough output-token estimate: characters of the JSON the model wrote / 4.

    Non-ASCII stays unescaped: a ``\\uXXXX`` escape is six characters for what
    the model emitted as one, which would overcharge CJK or math-symbol output
    several times over and reject passes that fit their budget.
    """

    if hasattr(result, "model_dump"):
        payload = result.model_dump(mode="json")
    elif isinstance(result, dict):
        payload = result
    else:
        payload = str(result)
    return max(1, len(json.dumps(payload, ensure_ascii=False, default=str)) // 4)


def _merge_synthesis(base: Any, extra: Any) -> Any:
    for field_name in ("concepts", "facets", "learning_objects", "blueprints", "practice_items", "conflicts", "non_conflict_dispositions", "concept_relations", "notes"):
        getattr(base, field_name).extend(getattr(extra, field_name))
    return base


def _namespace_synthesis_shard(result: Any, ordinal: int) -> Any:
    """Make model-authored client ids local to one synthesis shard.

    Shards are independent model calls and commonly choose the same descriptive
    client ids. Prefixing both declarations and references before concatenation
    preserves each shard's dependency graph and prevents database collisions.
    Canonical entity ids and source span ids are deliberately untouched.
    """

    prefix = f"shard_{ordinal + 1}__"

    # Relation endpoints ("source"/"target") reference concept client ids OR
    # registered concept ids; only the shard's own declarations are prefixed.
    declared_concepts = {
        getattr(concept, "client_item_id", None) or (concept.get("client_item_id") if isinstance(concept, dict) else None)
        for concept in getattr(result, "concepts", []) or (result.get("concepts") if isinstance(result, dict) else []) or []
    } - {None, ""}

    def rewrite(value: Any, key: str | None = None) -> Any:
        if isinstance(value, list):
            if key and (key.endswith("_client_ids") or key == "depends_on_client_item_ids"):
                return [f"{prefix}{item}" if item else item for item in value]
            return [rewrite(item) for item in value]
        if isinstance(value, dict):
            return {child_key: rewrite(child, child_key) for child_key, child in value.items()}
        if isinstance(value, str) and value and key and (
            key == "client_item_id" or key.endswith("_client_id")
        ):
            return f"{prefix}{value}"
        if isinstance(value, str) and key in ("source", "target") and value in declared_concepts:
            return f"{prefix}{value}"
        return value

    if hasattr(result, "model_dump"):
        return result.__class__.model_validate(rewrite(result.model_dump(mode="python")))
    return rewrite(result)


# --- cross-shard concept consolidation ---------------------------------------


def _consolidate_same_title_concepts(result: Any) -> Any:
    """Deterministic pass: fold concepts whose normalized titles are identical.

    Independent shards routinely re-declare the same concept ("Sample Space" in
    chapters 1 and 2). Same-title duplicates are unambiguous, so they merge
    without a model call; the semantic near-duplicates are left to the
    model-assisted pass."""

    by_title: dict[str, Any] = {}
    mapping: dict[str, str] = {}
    for concept in getattr(result, "concepts", []) or []:
        client_id = getattr(concept, "client_item_id", "") or ""
        key = snake_case(getattr(concept, "title", "") or "")
        if not key or not client_id:
            continue
        first = by_title.get(key)
        if first is None:
            by_title[key] = concept
        elif getattr(first, "client_item_id", ""):
            mapping[client_id] = first.client_item_id
    if not mapping:
        return result
    return _apply_concept_merges(result, mapping)


def _source_skeletons(repository: Repository, inputs: _SynthesisInputs) -> list[dict[str, Any]]:
    """Compact per-source big-picture views from already-paid-for artifacts.

    The deterministic unit/heading tree comes from the persisted Document IR;
    each selected unit is enriched with its CACHED inventory's outline summary,
    prerequisite hints, and concept mentions. No raw source text and no new
    model calls — this is the graph-structuring pass's whole-span context."""

    inventories_by_unit = {
        (entry["extraction_id"], entry["unit_id"]): entry["inventory"]
        for entry in inputs.unit_inventories
    }
    skeletons: list[dict[str, Any]] = []
    for extraction_id in inputs.extraction_ids:
        ir = repository.load_document_ir(extraction_id)
        if ir is None:
            continue
        origin = inputs.span_origin.get(extraction_id, {})
        units_out: list[dict[str, Any]] = []
        for unit in ir.units:
            entry: dict[str, Any] = {
                "unit_id": unit.unit_id,
                "label": (unit.label or "")[:120],
                "parent_unit_id": unit.parent_unit_id,
                "page_start": unit.page_start,
                "page_end": unit.page_end,
            }
            inventory = inventories_by_unit.get((extraction_id, unit.unit_id))
            if inventory:
                summary = str(inventory.get("outline_summary") or "")[:400]
                if summary:
                    entry["summary"] = summary
                hints: list[str] = []
                for claim in inventory.get("claims") or []:
                    for hint in claim.get("prerequisite_hints") or []:
                        if hint and hint not in hints:
                            hints.append(str(hint))
                if hints:
                    entry["prerequisite_hints"] = hints[:12]
                mentions = [
                    str(mention.get("name"))
                    for mention in inventory.get("concept_mentions") or []
                    if mention.get("name")
                ]
                if mentions:
                    entry["concept_mentions"] = list(dict.fromkeys(mentions))[:16]
            units_out.append(entry)
        skeletons.append(
            {
                "source_id": origin.get("source_id"),
                "role": origin.get("role"),
                "units": units_out,
            }
        )
    return skeletons


def _model_graph_structuring(
    merged: Any,
    client: Any,
    source_set: Any,
    inputs: _SynthesisInputs,
    repository: Repository,
    vault: LoadedVault,
    *,
    shard_count: int,
    input_tokens_estimate: int,
    total_input_ceiling: int | None,
    output_budget_tokens: int | None = None,
    progress: ProgressFn | None = None,
    nominator: Any = None,
    settings: dict[str, Any] | None = None,
    answers: _SavedAnswers | None = None,
) -> tuple[Any, dict[str, Any]]:
    """One bounded model pass over the WHOLE merged candidate (§8.5): folds
    semantic duplicate concepts AND authors the big-picture concept relations
    (part_of hierarchy, prerequisites, confusables) across every shard and
    source, using the compact source skeletons as whole-span context.

    Strictly best-effort: the shards are already paid for, so any failure here
    degrades to the deterministic same-title merge (and whatever relations the
    shards authored locally) rather than failing the synthesis. The model only
    NOMINATES merges/relations; validation and application stay deterministic.

    The answer is checkpointed like a pass (``settings`` are the run's), so a
    retry reads it instead of paying again, and joins ``answers``: the gates
    judge the candidate it shaped, and a rejection drops it with the passes.

    Slice 2 T5: with a ``nominator``, the registry concepts nearest each
    candidate by definition embedding are shown with their titles and
    definitions (not ids alone), and the model may decide ``registry_merges``.
    The embedding only nominates; the model decides, guards apply."""

    concepts = list(getattr(merged, "concepts", []) or [])
    nominations: dict[str, list[Any]] = {}
    candidate_queries: dict[str, Any] = {}
    if (
        nominator is not None and client is not None and concepts and vault.concepts
        and output_budget_tokens != 0
    ):
        nominations, candidate_queries = _registry_concept_nominations(nominator, concepts)
    # Single-shard synthesis already saw its whole span and authors relations
    # inline; the global pass earns its call when shards were blind to each
    # other, when a single shard produced no structure at all, or (T5) when
    # existing registry concepts were nominated for a candidate.
    needed = (
        shard_count >= 2
        or not list(getattr(merged, "concept_relations", []) or [])
        or bool(nominations)
    )
    if client is None or len(concepts) < (1 if nominations else 2) or not needed:
        return merged, {}
    if output_budget_tokens == 0:
        return merged, {"graph_structuring_skipped": "output budget exhausted"}

    compact = [
        {
            "client_item_id": concept.client_item_id,
            "title": concept.title,
            "type": concept.type,
            "aliases": list(concept.aliases or []),
            "description": (concept.description or "")[:280],
        }
        for concept in concepts
        if getattr(concept, "client_item_id", "")
    ]
    skeletons = _source_skeletons(repository, inputs)
    registry_concepts = sorted(vault.concepts.keys())
    registry_edges = [
        {"source": edge.source, "target": edge.target, "relation_type": edge.relation_type}
        for edge in vault.edges
    ]
    registry_details, registry_nominations = _registry_nomination_context(nominations, vault)
    context = ConceptGraphContext(
        source_set_id=source_set.id,
        subject_id=source_set.subject_id,
        concepts=compact,
        source_skeletons=skeletons,
        registry_concepts=registry_concepts,
        registry_edges=registry_edges,
        registry_concept_details=registry_details,
        registry_nominations=registry_nominations,
    )
    estimate_parts: list[Any] = [compact, skeletons, registry_concepts, registry_edges]
    if registry_details:
        estimate_parts += [registry_details, registry_nominations]
    estimate = max(1, len(json.dumps(estimate_parts, default=str)) // 4)
    checkpoint = structuring_checkpoint(
        repository, context, settings if settings is not None else model_settings(client),
    )
    calls = 0
    try:
        # A saved answer is free, so the input ceiling below applies only to a call.
        fetched = checkpoint.fetch()
        outcome = None if fetched is None else fetched[0]
        if fetched is not None and answers is not None:
            answers.passes.append((checkpoint.key, fetched[1]))
        if outcome is None:
            if (
                total_input_ceiling is not None
                and input_tokens_estimate + estimate > total_input_ceiling
            ):
                return merged, {"graph_structuring_skipped": "total-input ceiling reached"}
            _notify(progress, "synthesis", "Structuring the concept graph across sources")
            with generation_limit(output_budget_tokens):
                outcome = request_concept_graph_structuring(client, context)
            calls = 1
            # Saved before the output check, as a pass is: a retry under a
            # larger budget reuses this paid answer.
            stored = checkpoint.save(
                outcome, {"input_tokens_estimate": estimate, "output_tokens_estimate": _result_tokens(outcome)})
            if answers is not None:
                answers.passes.append((checkpoint.key, stored))
        if output_budget_tokens is not None and _result_tokens(outcome) > output_budget_tokens:
            return merged, {"graph_structuring_skipped": "output budget exceeded", "calls": calls,
                            "input_tokens_estimate": estimate if calls else 0}
    except Exception as exc:  # noqa: BLE001 — never discard paid-for shards over this
        return merged, {"graph_structuring_skipped": f"{exc.__class__.__name__}: {exc}"}
    mapping = _validated_merge_mapping(outcome, merged)
    if mapping:
        merged = _apply_concept_merges(merged, mapping)
    registry_mapping: dict[str, str] = {}
    ledger_failure: str | None = None
    unrecorded: list[dict[str, Any]] = []
    if registry_details:
        decisions = _validated_registry_merges(outcome, merged, mapping, nominations, vault)
        ledger_failure = _record_registry_merge_verdicts(
            repository, client, decisions, candidate_queries, vault, source_set_id=source_set.id,
        )
        if ledger_failure is not None:
            # An identity decision is used only once its verdict is durable in
            # judgment_ledger: without it, every merge is declined (the
            # candidate stays its own concept) and the decisions are kept on
            # the run's usage record for the owner, never applied.
            unrecorded = [
                {key: decision[key] for key in ("client_item_id", "registry_concept_id", "rationale", "refused")}
                for decision in decisions
            ]
            decisions = []
        registry_mapping = {
            decision["client_item_id"]: decision["registry_concept_id"]
            for decision in decisions if decision["applied"]
        }
        if registry_mapping:
            merged = _fold_into_registry_concepts(merged, registry_mapping)
    known = {
        concept.client_item_id
        for concept in getattr(merged, "concepts", []) or []
        if getattr(concept, "client_item_id", "")
    } | set(registry_concepts)
    authored = 0
    for relation in getattr(outcome, "relations", []) or []:
        source = mapping.get(relation.source, relation.source)
        target = mapping.get(relation.target, relation.target)
        source = registry_mapping.get(source, source)
        target = registry_mapping.get(target, target)
        if not source or not target or source == target:
            continue
        if source not in known or target not in known:
            continue
        merged.concept_relations.append(
            relation.model_copy(update={"source": source, "target": target})
        )
        authored += 1
    usage = {
        "calls": calls,
        "input_tokens_estimate": estimate if calls else 0,
        "consolidated_concepts": len(mapping),
        "authored_relations": authored,
    }
    if registry_details:
        usage["registry_nominated_candidates"] = len(registry_nominations)
        usage["registry_merges"] = len(registry_mapping)
        if ledger_failure is not None:
            usage["registry_merges_declined"] = ledger_failure
            usage["registry_merge_decisions_unrecorded"] = unrecorded
    return merged, usage


# --- Slice 2 T5: registry nominations for the structuring pass -------------


def _registry_concept_nominations(nominator: Any, concepts: list[Any]) -> tuple[dict[str, list[Any]], dict[str, Any]]:
    """Each candidate's top-k registry concepts by definition embedding.

    The candidate text is composed exactly like the ``concept/definition``
    recipe, so the comparison is symmetric and the paid vector is reused if
    the candidate is later applied and backfilled. Degrades to ``{}``.
    """

    queries = {
        concept.client_item_id: concept_query(concept, concept.client_item_id)
        for concept in concepts
        if getattr(concept, "client_item_id", "")
    }
    return nominator.nominate(CONCEPT_RECIPE, list(queries.values())), queries


def _registry_nomination_context(
    nominations: dict[str, list[Any]], vault: LoadedVault,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Titles and definitions for the nominated registry concepts (not ids alone)."""

    if not nominations:
        return [], []
    nominated_ids = sorted({n.record_id for ranked in nominations.values() for n in ranked})
    details = []
    for concept_id in nominated_ids:
        concept = vault.concepts.get(concept_id)
        if concept is None:
            continue
        details.append({
            "id": concept_id,
            "title": concept.title,
            "type": concept.type,
            "aliases": list(concept.aliases or []),
            "description": (concept.description or "")[:400],
        })
    listed = [
        {
            "client_item_id": client_id,
            "registry_concept_ids": [n.record_id for n in ranked],
        }
        for client_id, ranked in sorted(nominations.items())
    ]
    return details, listed


def _validated_registry_merges(
    outcome: Any, merged: Any, mapping: dict[str, str],
    nominations: dict[str, list[Any]], vault: LoadedVault,
) -> list[dict[str, Any]]:
    """Every registry merge the model decided, with whether the guards allow it.

    Applied only for a surviving candidate, a nominated registry concept of the
    same type, and one decision per candidate. A refused decision about a known
    candidate is still the model's verdict and is ledgered with the reason; it
    changes nothing. A decision naming no known candidate is dropped.
    """

    by_client = {
        concept.client_item_id: concept
        for concept in getattr(merged, "concepts", []) or []
        if getattr(concept, "client_item_id", "")
    }
    nominated_ids = {n.record_id for ranked in nominations.values() for n in ranked}
    decisions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in getattr(outcome, "registry_merges", []) or []:
        named = str(getattr(entry, "client_item_id", "") or "")
        client_id = mapping.get(named, named)
        registry_id = str(getattr(entry, "registry_concept_id", "") or "")
        candidate = by_client.get(client_id)
        if candidate is None:
            continue  # no candidate this verdict could be about; nothing to ledger
        registry = vault.concepts.get(registry_id)
        if registry is None:
            refused = "unknown_registry_concept"
        elif registry_id not in nominated_ids:
            refused = "not_nominated"
        elif (candidate.type or "concept") != (registry.type or "concept"):
            refused = "type_mismatch"
        elif client_id in seen:
            refused = "duplicate_decision"
        else:
            refused = None
        if refused is None:
            seen.add(client_id)
        ranks = {n.record_id: n.rank for n in nominations.get(named, []) or nominations.get(client_id, [])}
        decisions.append({
            "client_item_id": client_id,
            "named_client_item_id": named,
            "candidate_title": getattr(candidate, "title", None),
            "registry_concept_id": registry_id,
            "rationale": str(getattr(entry, "rationale", "") or "")[:2000],
            "applied": refused is None,
            "refused": refused,
            "nomination_rank": ranks.get(registry_id),
        })
    return decisions


def _record_registry_merge_verdicts(
    repository: Repository, client: Any, decisions: list[dict[str, Any]],
    candidate_queries: dict[str, Any], vault: LoadedVault, *, source_set_id: str,
) -> str | None:
    """Append each registry-merge decision to ``judgment_ledger`` (task ``same_concept``).

    One transaction: every verdict is recorded or none is. Returns ``None`` on
    success, else the failure (``ledger_write_failed:<type>``), which the
    caller treats as "decline every merge": a ledger failure never fails the
    paid synthesis, and a merge never proceeds without its verdict. Rebuild
    never reads these rows to merge anything.
    """

    import sqlite3

    from learnloop.content.synthesis.ai_contracts import CONCEPT_GRAPH_REGISTRY_PROMPT_VERSION
    from learnloop.db.stores.judgments import append_judgment
    from learnloop.vault.embedding_recipes import concept_definition_text

    if not decisions:
        return None
    model = (
        getattr(client, "model", None) or getattr(client, "provider_name", None)
        or getattr(client, "provider_type", None) or "unknown"
    )
    try:
        with repository.connection() as connection:
            for decision in decisions:
                query = candidate_queries.get(decision["named_client_item_id"]) or candidate_queries.get(
                    decision["client_item_id"]
                )
                candidate_text = query.text if query is not None else str(decision["candidate_title"] or "")
                left_id = query.content_hash if query is not None else content_key(candidate_text)
                registry = vault.concepts.get(decision["registry_concept_id"])
                registry_text = concept_definition_text(registry) if registry is not None else ""
                append_judgment(
                    connection, task="same_concept",
                    left_kind="concept_candidate", left_id=left_id,
                    right_kind="concept", right_id=decision["registry_concept_id"] or "(unknown)",
                    judge="llm", judge_model=str(model),
                    prompt_version=CONCEPT_GRAPH_REGISTRY_PROMPT_VERSION,
                    input_hash=content_key({"candidate": candidate_text, "registry": registry_text}),
                    verdict="same",
                    rationale=json.dumps({**decision, "source_set_id": source_set_id}, sort_keys=True),
                )
    except (sqlite3.Error, ValueError) as exc:
        return f"ledger_write_failed:{type(exc).__name__}"
    return None


def _fold_into_registry_concepts(result: Any, mapping: dict[str, str]) -> Any:
    """Drop candidates decided to BE registry concepts; point references at them.

    ``mapping`` is candidate client id -> registry concept id. Client-id
    references become canonical-id references (``concept_client_id`` ->
    ``concept_id``; prerequisite/confusable client lists -> canonical lists),
    dependency edges on the dropped rows are removed, and relations are
    rewritten, de-duplicated and stripped of self-edges.
    """

    data = result.model_dump(mode="python") if hasattr(result, "model_dump") else dict(result)
    concepts = data.get("concepts") or []
    declared = {
        concept["id"]: mapping[concept["client_item_id"]]
        for concept in concepts
        if concept.get("client_item_id") in mapping and concept.get("id")
    }
    data["concepts"] = [c for c in concepts if c.get("client_item_id") not in mapping]

    def anchor(entity: dict[str, Any]) -> None:
        client_id = entity.get("concept_client_id") or ""
        if client_id in mapping:
            entity["concept_client_id"] = ""
            entity["concept_id"] = mapping[client_id]
        elif entity.get("concept_id") in declared:
            entity["concept_id"] = declared[entity["concept_id"]]

    for facet in data.get("facets") or []:
        anchor(facet)
    for learning_object in data.get("learning_objects") or []:
        anchor(learning_object)
        for client_key, canonical_key in (
            ("prerequisite_concept_client_ids", "prerequisites"),
            ("confusable_concept_client_ids", "confusables"),
        ):
            clients = list(learning_object.get(client_key) or [])
            moved = [mapping[value] for value in clients if value in mapping]
            learning_object[client_key] = [value for value in clients if value not in mapping]
            canonical = [declared.get(value, value) for value in learning_object.get(canonical_key) or []]
            learning_object[canonical_key] = list(dict.fromkeys([*canonical, *moved]))
    for item in data.get("practice_items") or []:
        item["depends_on_client_item_ids"] = [
            value for value in item.get("depends_on_client_item_ids") or [] if value not in mapping
        ]
    seen: set[tuple[str, str, str]] = set()
    relations = []
    for relation in data.get("concept_relations") or []:
        source = str(relation.get("source") or "")
        target = str(relation.get("target") or "")
        source = mapping.get(source, declared.get(source, source))
        target = mapping.get(target, declared.get(target, target))
        signature = (source, target, str(relation.get("relation_type") or ""))
        if not source or not target or source == target or signature in seen:
            continue
        seen.add(signature)
        relations.append({**relation, "source": source, "target": target})
    data["concept_relations"] = relations
    if hasattr(result, "model_validate"):
        return result.__class__.model_validate(data)
    return data


def _validated_merge_mapping(consolidation: Any, result: Any) -> dict[str, str]:
    """duplicate client id -> canonical client id, from validated merge groups.

    Unknown ids, self-merges, re-used duplicates, and chained groups (a canonical
    that is itself merged away) are dropped — an invalid nomination is a no-op,
    never an error."""

    known = {
        concept.client_item_id
        for concept in getattr(result, "concepts", []) or []
        if getattr(concept, "client_item_id", "")
    }
    mapping: dict[str, str] = {}
    for group in getattr(consolidation, "merge_groups", []) or []:
        canonical = str(getattr(group, "canonical_client_id", "") or "")
        if canonical not in known:
            continue
        for duplicate in getattr(group, "duplicate_client_ids", []) or []:
            duplicate = str(duplicate or "")
            if duplicate in known and duplicate != canonical and duplicate not in mapping:
                mapping[duplicate] = canonical
    # Break chains conservatively: a canonical that is itself merged away
    # invalidates the entries pointing at it.
    return {dup: canon for dup, canon in mapping.items() if canon not in mapping}


def _apply_concept_merges(result: Any, mapping: dict[str, str]) -> Any:
    """Fold duplicate concepts into their canonical and rewrite all references.

    The dropped concept's title and aliases become aliases of the canonical (so
    later same-name references still resolve through the concept index), and
    every reference — ``*_client_id`` fields, ``*_client_ids`` lists,
    ``depends_on_client_item_ids``, and canonical-id ``concept_id``/
    ``prerequisites``/``confusables`` entries — is rewritten to the canonical."""

    data = result.model_dump(mode="python") if hasattr(result, "model_dump") else dict(result)
    concepts = data.get("concepts") or []
    by_client = {c.get("client_item_id"): c for c in concepts if c.get("client_item_id")}
    dropped_declared_ids: dict[str, str] = {}
    for duplicate, canonical in mapping.items():
        dup_concept = by_client.get(duplicate)
        canon_concept = by_client.get(canonical)
        if dup_concept is None or canon_concept is None:
            continue
        aliases = list(canon_concept.get("aliases") or [])
        for alias in [dup_concept.get("title"), *(dup_concept.get("aliases") or [])]:
            if alias and alias != canon_concept.get("title") and alias not in aliases:
                aliases.append(alias)
        canon_concept["aliases"] = aliases
        if not canon_concept.get("description") and dup_concept.get("description"):
            canon_concept["description"] = dup_concept["description"]
        if dup_concept.get("id"):
            # Canonical-id references to the dropped concept resolve through the
            # surviving concept's client id (always resolvable in _normalize).
            dropped_declared_ids[dup_concept["id"]] = canonical
    data["concepts"] = [c for c in concepts if c.get("client_item_id") not in mapping]

    def rewrite(value: Any, key: str | None = None) -> Any:
        if isinstance(value, list):
            if key and (key.endswith("_client_ids") or key == "depends_on_client_item_ids"):
                return list(dict.fromkeys(mapping.get(item, item) for item in value))
            if key in ("prerequisites", "confusables"):
                return list(dict.fromkeys(dropped_declared_ids.get(item, item) for item in value))
            return [rewrite(item) for item in value]
        if isinstance(value, dict):
            return {child_key: rewrite(child, child_key) for child_key, child in value.items()}
        if isinstance(value, str) and value and key:
            if key.endswith("_client_id"):
                return mapping.get(value, value)
            if key == "concept_id":
                return dropped_declared_ids.get(value, value)
            if key in ("source", "target"):
                return mapping.get(value, value)
        return value

    data = rewrite(data)
    # Folding duplicates can turn a relation between them into a self-edge, or
    # make two relations identical — drop/dedupe rather than propagate.
    seen_relations: set[tuple[str, str, str]] = set()
    surviving_relations = []
    for relation in data.get("concept_relations") or []:
        signature = (
            str(relation.get("source") or ""),
            str(relation.get("target") or ""),
            str(relation.get("relation_type") or ""),
        )
        if not signature[0] or not signature[1] or signature[0] == signature[1]:
            continue
        if signature in seen_relations:
            continue
        seen_relations.add(signature)
        surviving_relations.append(relation)
    data["concept_relations"] = surviving_relations

    if hasattr(result, "model_dump"):
        return result.__class__.model_validate(data)
    return data


def _duplicate_client_id_diagnostics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(str(row.get("client_item_id") or "") for row in rows)
    duplicates = sorted(client_id for client_id, count in counts.items() if client_id and count > 1)
    return [
        {
            "gate": "client_item_id_uniqueness",
            "severity": "hard_fail",
            "message": f"client item id {client_id!r} occurs {counts[client_id]} times",
            "entity_refs": [client_id],
            "suggested_action": "retry synthesis with shard-local identifiers",
        }
        for client_id in duplicates
    ]


def _gate_context(vault, repository, inputs, findings, nominator=None, *, append_mode: bool = False) -> GateContext:
    registered_facets = set(vault.evidence_facets.keys())
    from learnloop.learner.capability_mapping import CAPABILITY_VOCABULARY

    def hook(_proposal, _ctx):
        return _findings_to_diagnostics(findings)

    return GateContext(
        registered_facet_ids=registered_facets,
        registered_concept_ids=set(vault.concepts.keys()),
        registered_capabilities=set(CAPABILITY_VOCABULARY),
        selected_revision_ids=set(inputs.selected_revision_ids),
        extraction_units=inputs.extraction_units,
        extraction_spans=inputs.extraction_spans,
        held_out_span_ids=inputs.held_out_span_ids,
        vault=vault,
        repository=repository,
        identifiability_hook=hook,
        # T5: the near-duplicate review diagnostic shows cosine beside Jaccard.
        facet_cosine=nominator.facet_cosine if nominator is not None else None,
        append_mode=append_mode,
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


def _apply_and_wire_goal(
    root: Path,
    repository: Repository,
    result: StudyMapResult,
    *,
    brief: dict[str, Any],
    create_goal: bool,
    clock: Clock | None,
    facet_ids: list[str] | None = None,
    progress: ProgressFn | None = None,
) -> None:
    """Accept the proposal, then create the exam-prep Goal when asked (:func:`_apply_map`), into ``result``."""

    goal_id = _apply_map(
        root, repository, str(result.proposal_id), brief=brief, create_goal=create_goal, clock=clock,
        facet_ids=facet_ids, progress=progress,
    )
    result.applied = True
    result.goal_id = goal_id


def _apply_map(
    root: Path,
    repository: Repository,
    proposal_id: str,
    *,
    brief: dict[str, Any],
    create_goal: bool,
    clock: Clock | None,
    facet_ids: list[str] | None,
    progress: ProgressFn | None,
) -> str | None:
    """Accept the whole proposal, then create the exam-prep Goal when asked; the goal's id, if one was made.

    ``facet_ids`` are the freshly normalized facets; a caller without them in
    hand passes None, and they are read back from the persisted proposal items.
    """

    from learnloop.content.proposals.patches import apply_accepted_items

    _notify(progress, "apply", "Applying the study map")
    apply_accepted_items(root, proposal_id, clock=clock)
    if not (create_goal and _is_exam_prep(brief)):
        return None
    if facet_ids is None:
        facet_ids = [
            str((row.get("edited_payload") or row.get("payload") or {}).get("id") or "")
            for row in repository.proposal_items(proposal_id)
            if row["item_type"] == "facet"
        ]
    return _create_goal_from_brief(root, brief, facet_ids, clock=clock, provenance_key=proposal_id)


def _create_goal_from_brief(root: Path, brief: dict[str, Any], facet_ids: list[str], *, clock: Clock | None, provenance_key: str | None = None) -> str | None:
    from learnloop.vault_lock import vault_mutation_lock
    with vault_mutation_lock(root, purpose="study_map_goal"):
        return _create_goal_from_brief_locked(root, brief, facet_ids, clock=clock, provenance_key=provenance_key)


def _create_goal_from_brief_locked(root: Path, brief: dict[str, Any], facet_ids: list[str], *, clock: Clock | None, provenance_key: str | None) -> str | None:
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
    if provenance_key:
        base = f"{base}_{content_key(provenance_key)[:12]}"
        if base in existing:
            return base
    goal_id, n = base, 2
    while goal_id in existing:
        goal_id = f"{base}_{n}"
        n += 1
    now = utc_now_iso(clock)
    entry = {
        "id": goal_id,
        "title": title,
        "intent_sentence": str(brief.get("intent_sentence") or "").strip() or None,
        "creation_source": "study_map",
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
