"""Deterministic synthesis quality gates (source-ingestion §8.7).

Before a synthesis proposal is persisted or presented, it runs the §8.7 table of
deterministic checks. Every gate returns a TYPED diagnostic — ``{gate, severity,
entity_refs, message, suggested_action}`` — never a generic "synthesis failed".
Severity is ``hard_fail`` (the proposal cannot be persisted) or ``review`` (it is
downgraded from any auto-apply lane to human review).

These are pure functions over a :class:`GateProposal` and a :class:`GateContext`;
M6 calls :func:`run_synthesis_gates` from the synthesis pipeline. The authority
rules follow the single normative §4.2 authority matrix.

The identifiability gate is a SEAM: KM5's full identifiability doctor
(knowledge-model §11.3) fills :attr:`GateContext.identifiability_hook`. Until then
it runs the degenerate duplicate-target-signature check.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

# §4.2 authority matrix: roles that may independently support a semantic claim.
SEMANTIC_AUTHORITY_ROLES: frozenset[str] = frozenset(
    {"primary_textbook", "lecture", "paper", "reference", "alternate_explanation"}
)
# Roles that contribute only assessment/task alignment, never semantic authority.
ASSESSMENT_ONLY_ROLES: frozenset[str] = frozenset({"exam"})

_SEMANTIC_ITEM_TYPES: frozenset[str] = frozenset({"facet", "learning_object", "concept"})
_TOKEN_RE = re.compile(r"[a-z0-9]+")

Severity = str  # "hard_fail" | "review"


@dataclass(frozen=True)
class GateDiagnostic:
    gate: str
    severity: Severity
    entity_refs: tuple[str, ...]
    message: str
    suggested_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate": self.gate,
            "severity": self.severity,
            "entity_refs": list(self.entity_refs),
            "message": self.message,
            "suggested_action": self.suggested_action,
        }


@dataclass
class ProvenanceRef:
    """A source span backing a proposed entity (§4.2/§8.5)."""

    extraction_id: str | None = None
    revision_id: str | None = None
    unit_id: str | None = None
    span_id: str | None = None
    relation: str = "support"
    role: str = "reference"
    manual_authority: bool = False
    held_out: bool = False


@dataclass
class GateItem:
    client_item_id: str
    item_type: str
    operation: str = "create"
    entity_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    provenance: list[ProvenanceRef] = field(default_factory=list)
    # Overrides; when None the value is inferred from item_type/operation.
    establishes_semantic: bool | None = None
    destructive: bool | None = None
    # Held-out leakage: a teaching/generated-practice payload that embeds spans.
    is_teaching_or_practice: bool = False
    embedded_span_ids: list[str] = field(default_factory=list)
    # Explicit human/manual authority override for an otherwise-exam-only claim.
    manual_authority: bool = False
    # Test/enforcement seam for the lock guard when no vault/repository is wired.
    lock_reason: str | None = None

    def is_semantic(self) -> bool:
        if self.establishes_semantic is not None:
            return self.establishes_semantic
        return self.item_type in _SEMANTIC_ITEM_TYPES and self.operation in {"create", "update"}

    def is_destructive(self) -> bool:
        if self.destructive is not None:
            return self.destructive
        return self.operation in {"update", "deactivate"}

    def refs(self) -> tuple[str, ...]:
        return (self.entity_id or self.client_item_id,)


@dataclass
class GateProposal:
    items: list[GateItem] = field(default_factory=list)
    # Conflict candidates the model flagged; each needs a source_conflict item or
    # an explicit non-conflict disposition (§8.7 conflict-disposition gate).
    conflict_candidates: list[str] = field(default_factory=list)
    non_conflict_dispositions: set[str] = field(default_factory=set)


@dataclass
class GateContext:
    registered_facet_ids: set[str] = field(default_factory=set)
    registered_capabilities: set[str] | None = None  # None = accept any capability
    selected_revision_ids: set[str] = field(default_factory=set)
    # extraction_id -> valid unit ids / span ids for that extraction run.
    extraction_units: dict[str, set[str]] = field(default_factory=dict)
    extraction_spans: dict[str, set[str]] = field(default_factory=dict)
    held_out_span_ids: set[str] = field(default_factory=set)
    token_budget: int | None = None
    token_estimate: int | None = None
    truncated: bool = False
    # Lexical near-duplicate threshold (Jaccard over claim/title tokens).
    near_duplicate_threshold: float = 0.85
    registered_facet_texts: dict[str, str] = field(default_factory=dict)
    # Lock guard: when both are present, gates delegate to can_apply; otherwise
    # they fall back to each item's `lock_reason` field (pure unit tests).
    vault: Any = None
    repository: Any = None
    # Identifiability SEAM (KM5 doctor fills this; default = degenerate check).
    identifiability_hook: Callable[["GateProposal", "GateContext"], list[GateDiagnostic]] | None = None


@dataclass
class GateReport:
    diagnostics: list[GateDiagnostic] = field(default_factory=list)

    @property
    def hard_fails(self) -> list[GateDiagnostic]:
        return [d for d in self.diagnostics if d.severity == "hard_fail"]

    @property
    def reviews(self) -> list[GateDiagnostic]:
        return [d for d in self.diagnostics if d.severity == "review"]

    @property
    def blocked(self) -> bool:
        """True when any hard_fail is present — the proposal cannot be persisted."""

        return bool(self.hard_fails)

    @property
    def requires_review(self) -> bool:
        return bool(self.reviews)

    def gates_fired(self) -> set[str]:
        return {d.gate for d in self.diagnostics}


def run_synthesis_gates(proposal: GateProposal, ctx: GateContext) -> GateReport:
    """Run every §8.7 gate and collect typed diagnostics."""

    diagnostics: list[GateDiagnostic] = []
    for gate in _GATES:
        diagnostics.extend(gate(proposal, ctx))
    hook = ctx.identifiability_hook or _default_identifiability
    diagnostics.extend(hook(proposal, ctx))
    return GateReport(diagnostics=diagnostics)


# --- individual gates -------------------------------------------------------


def _gate_span_resolution(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]:
    out: list[GateDiagnostic] = []
    for item in proposal.items:
        for ref in item.provenance:
            if ref.span_id is None or ref.extraction_id is None:
                continue
            valid = ctx.extraction_spans.get(ref.extraction_id, set())
            if ref.span_id not in valid:
                out.append(
                    GateDiagnostic(
                        gate="span_resolution",
                        severity="hard_fail",
                        entity_refs=item.refs(),
                        message=(
                            f"span {ref.span_id} does not resolve in extraction "
                            f"run {ref.extraction_id}"
                        ),
                        suggested_action="re-extract or drop the unresolved citation",
                    )
                )
    return out


def _gate_scope(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]:
    if not ctx.selected_revision_ids:
        return []
    out: list[GateDiagnostic] = []
    for item in proposal.items:
        for ref in item.provenance:
            if ref.revision_id is not None and ref.revision_id not in ctx.selected_revision_ids:
                out.append(
                    GateDiagnostic(
                        gate="scope",
                        severity="hard_fail",
                        entity_refs=item.refs(),
                        message=f"entity cites revision {ref.revision_id} outside selected scope",
                        suggested_action="restrict citations to the selected revisions",
                    )
                )
    return out


def _gate_unit_id_validity(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]:
    if not ctx.extraction_units:
        return []
    out: list[GateDiagnostic] = []
    for item in proposal.items:
        for ref in item.provenance:
            if ref.unit_id is None or ref.extraction_id is None:
                continue
            valid = ctx.extraction_units.get(ref.extraction_id, set())
            if ref.unit_id not in valid:
                out.append(
                    GateDiagnostic(
                        gate="unit_id_validity",
                        severity="hard_fail",
                        entity_refs=item.refs(),
                        message=(
                            f"unit {ref.unit_id} is not valid for extraction run "
                            f"{ref.extraction_id}"
                        ),
                        suggested_action="cite a unit id present in the extraction run",
                    )
                )
    return out


def _gate_conflict_disposition(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]:
    covered: set[str] = set(proposal.non_conflict_dispositions)
    for item in proposal.items:
        if item.item_type == "source_conflict":
            candidate = item.payload.get("candidate_id") or item.payload.get("conflict_candidate_id")
            if candidate is not None:
                covered.add(str(candidate))
    out: list[GateDiagnostic] = []
    for candidate in proposal.conflict_candidates:
        if candidate not in covered:
            out.append(
                GateDiagnostic(
                    gate="conflict_disposition",
                    severity="hard_fail",
                    entity_refs=(candidate,),
                    message=f"declared conflict candidate {candidate} has no disposition",
                    suggested_action="emit a source_conflict item or an explicit non-conflict disposition",
                )
            )
    return out


def _gate_lock_guard(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]:
    out: list[GateDiagnostic] = []
    for item in proposal.items:
        if not item.is_destructive():
            continue
        reason = _lock_reason_for(item, ctx)
        if reason is not None:
            out.append(
                GateDiagnostic(
                    gate="lock_guard",
                    severity="hard_fail",
                    entity_refs=item.refs(),
                    message=f"destructive op on locked identity bypassed the lock guard: {reason}",
                    suggested_action="route through restructure-with-history or drop the destructive op",
                )
            )
    return out


def _lock_reason_for(item: GateItem, ctx: GateContext) -> str | None:
    """Delegate to can_apply when a vault/repository is wired, else use the
    item's injected lock_reason. Never a second enumerated lock list."""

    if ctx.vault is not None and ctx.repository is not None and item.entity_id is not None:
        from learnloop.services.curriculum_locks import Operation, can_apply

        entity_type = item.item_type if item.item_type in {"facet", "learning_object", "practice_item", "concept"} else "learning_object"
        op_type = "deactivate" if item.operation == "deactivate" else "blueprint_identity_change"
        result = can_apply(
            ctx.vault,
            ctx.repository,
            Operation(op_type=op_type, entity_type=entity_type, entity_id=item.entity_id),
        )
        if not result.legal:
            return "; ".join(r.detail for r in result.lock_reasons) or "identity is locked"
        return None
    return item.lock_reason


def _gate_adequate_provenance(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]:
    out: list[GateDiagnostic] = []
    for item in proposal.items:
        if not item.is_semantic():
            continue
        if _has_semantic_authority(item):
            continue
        out.append(
            GateDiagnostic(
                gate="adequate_provenance",
                severity="review",
                entity_refs=item.refs(),
                message=(
                    "created/updated semantic contract lacks an in-scope span from a "
                    "role allowed semantic authority"
                ),
                suggested_action="attach an authoritative in-scope span or mark human/manual context",
            )
        )
    return out


def _has_semantic_authority(item: GateItem) -> bool:
    if item.manual_authority:
        return True
    for ref in item.provenance:
        if ref.manual_authority:
            return True
        if ref.role in SEMANTIC_AUTHORITY_ROLES and ref.relation in {"primary", "support", "alternate"}:
            return True
    return False


def _gate_criterion_targets_dag(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]:
    known_facets = set(ctx.registered_facet_ids) | {
        item.entity_id or item.client_item_id for item in proposal.items if item.item_type == "facet"
    }
    out: list[GateDiagnostic] = []
    for item in proposal.items:
        criteria = _criteria_of(item)
        if not criteria:
            continue
        for criterion in criteria:
            for target in criterion.get("targets", []) or []:
                facet = target.get("facet")
                if facet is not None and str(facet) not in known_facets:
                    out.append(
                        GateDiagnostic(
                            gate="criterion_target",
                            severity="hard_fail",
                            entity_refs=item.refs(),
                            message=f"criterion target facet {facet} is not registered or proposed",
                            suggested_action="target a registered/proposed facet",
                        )
                    )
                capability = target.get("capability")
                if (
                    capability is not None
                    and ctx.registered_capabilities is not None
                    and str(capability) not in ctx.registered_capabilities
                ):
                    out.append(
                        GateDiagnostic(
                            gate="criterion_target",
                            severity="hard_fail",
                            entity_refs=item.refs(),
                            message=f"criterion target capability {capability} is unknown",
                            suggested_action="target a known capability",
                        )
                    )
        cycle = _first_cycle({str(c.get("id")): [str(d) for d in (c.get("depends_on") or [])] for c in criteria if c.get("id") is not None})
        if cycle is not None:
            out.append(
                GateDiagnostic(
                    gate="criterion_dag",
                    severity="hard_fail",
                    entity_refs=item.refs(),
                    message=f"criterion dependency DAG has a cycle: {' -> '.join(cycle)}",
                    suggested_action="break the criterion dependency cycle",
                )
            )
    return out


def _gate_recipe_validity(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]:
    known_facets = set(ctx.registered_facet_ids) | {
        item.entity_id or item.client_item_id for item in proposal.items if item.item_type == "facet"
    }
    out: list[GateDiagnostic] = []
    for item in proposal.items:
        blueprints = _blueprints_of(item)
        if not blueprints:
            continue
        for blueprint in blueprints:
            recipes = blueprint.get("recipes") or []
            if not recipes:
                out.append(
                    GateDiagnostic(
                        gate="recipe_validity",
                        severity="hard_fail",
                        entity_refs=item.refs(),
                        message=f"blueprint {blueprint.get('id')} has no valid recipe",
                        suggested_action="add at least one AND/OR recipe to the blueprint",
                    )
                )
                continue
            for recipe in recipes:
                for facet in recipe.get("facets") or []:
                    if str(facet) not in known_facets:
                        out.append(
                            GateDiagnostic(
                                gate="recipe_validity",
                                severity="hard_fail",
                                entity_refs=item.refs(),
                                message=f"recipe references unresolved facet {facet}",
                                suggested_action="reference a registered/proposed facet in the recipe",
                            )
                        )
    return out


def _gate_dependency_closure(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]:
    ids = {item.client_item_id for item in proposal.items}
    graph: dict[str, list[str]] = {}
    out: list[GateDiagnostic] = []
    for item in proposal.items:
        graph[item.client_item_id] = list(item.depends_on)
        for dep in item.depends_on:
            if dep not in ids:
                out.append(
                    GateDiagnostic(
                        gate="dependency_closure",
                        severity="hard_fail",
                        entity_refs=item.refs(),
                        message=f"item depends on {dep} which is not in the proposal (dangling requirement)",
                        suggested_action="include the required item or remove the dependency",
                    )
                )
    cycle = _first_cycle(graph)
    if cycle is not None:
        out.append(
            GateDiagnostic(
                gate="dependency_closure",
                severity="hard_fail",
                entity_refs=tuple(cycle),
                message=f"proposal dependency graph has a cycle: {' -> '.join(cycle)}",
                suggested_action="break the dependency cycle so a closure exists",
            )
        )
    return out


def _gate_exam_authority(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]:
    out: list[GateDiagnostic] = []
    for item in proposal.items:
        if not item.is_semantic():
            continue
        if item.manual_authority:
            continue
        if not item.provenance:
            continue
        roles = {ref.role for ref in item.provenance if not ref.manual_authority}
        if roles and roles <= ASSESSMENT_ONLY_ROLES:
            out.append(
                GateDiagnostic(
                    gate="exam_authority",
                    severity="hard_fail",
                    entity_refs=item.refs(),
                    message="exam-only evidence attempts to establish a canonical claim/equivalence/prerequisite",
                    suggested_action="corroborate with an explanatory source span or grant explicit manual authority",
                )
            )
    return out


def _gate_held_out_leakage(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]:
    if not ctx.held_out_span_ids:
        return []
    out: list[GateDiagnostic] = []
    for item in proposal.items:
        if not item.is_teaching_or_practice:
            continue
        leaked = sorted(set(item.embedded_span_ids) & ctx.held_out_span_ids)
        if leaked:
            out.append(
                GateDiagnostic(
                    gate="held_out_leakage",
                    severity="hard_fail",
                    entity_refs=item.refs(),
                    message=f"held-out exam span(s) {leaked} appear in a teaching/generated-practice payload",
                    suggested_action="regenerate a fresh surface that does not reproduce held-out content",
                )
            )
    return out


def _gate_token_truncation(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]:
    out: list[GateDiagnostic] = []
    over_budget = (
        ctx.token_budget is not None
        and ctx.token_estimate is not None
        and ctx.token_estimate > ctx.token_budget
    )
    if over_budget or ctx.truncated:
        out.append(
            GateDiagnostic(
                gate="token_truncation",
                severity="hard_fail",
                entity_refs=(),
                message=(
                    f"token/context budget exceeded or content truncated "
                    f"(estimate={ctx.token_estimate}, budget={ctx.token_budget}, truncated={ctx.truncated})"
                ),
                suggested_action="shard the synthesis into dependency-closed bundles or narrow scope",
            )
        )
    return out


def _gate_practice_exam_only(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]:
    out: list[GateDiagnostic] = []
    for item in proposal.items:
        if item.item_type != "practice_item":
            continue
        if not item.provenance:
            continue
        roles = {ref.role for ref in item.provenance}
        if roles and roles <= ASSESSMENT_ONLY_ROLES:
            out.append(
                GateDiagnostic(
                    gate="practice_exam_only",
                    severity="review",
                    entity_refs=item.refs(),
                    message="practice item relies solely on an exam-role source",
                    suggested_action="ground the practice item in an explanatory/practice source or review",
                )
            )
    return out


def _gate_duplicate_ids_dangling(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]:
    out: list[GateDiagnostic] = []
    seen: dict[str, str] = {}
    for item in proposal.items:
        key = item.entity_id
        if key is None:
            continue
        if key in seen and seen[key] != item.client_item_id:
            out.append(
                GateDiagnostic(
                    gate="duplicate_ids",
                    severity="hard_fail",
                    entity_refs=(key,),
                    message=f"duplicate entity id {key} across proposal items",
                    suggested_action="assign a unique id or merge the duplicate items",
                )
            )
        seen.setdefault(key, item.client_item_id)
    # Dangling concept_edge endpoints.
    concept_ids = {
        item.entity_id or item.client_item_id
        for item in proposal.items
        if item.item_type == "concept"
    } | ctx.registered_facet_ids  # tolerate pre-existing endpoints via registry
    for item in proposal.items:
        if item.item_type != "concept_edge":
            continue
        for endpoint_key in ("source", "target"):
            endpoint = item.payload.get(endpoint_key)
            if endpoint is not None and str(endpoint) not in concept_ids and not _endpoint_known(str(endpoint), proposal):
                out.append(
                    GateDiagnostic(
                        gate="dangling_edge",
                        severity="hard_fail",
                        entity_refs=item.refs(),
                        message=f"concept edge {endpoint_key} {endpoint} does not resolve",
                        suggested_action="create the endpoint or drop the edge",
                    )
                )
    return out


def _endpoint_known(endpoint: str, proposal: GateProposal) -> bool:
    for item in proposal.items:
        if item.item_type == "concept" and (item.entity_id == endpoint or item.client_item_id == endpoint):
            return True
    return False


def _gate_near_duplicate_facets(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]:
    facets = [item for item in proposal.items if item.item_type == "facet"]
    out: list[GateDiagnostic] = []
    texts: list[tuple[str, set[str]]] = []
    for item in facets:
        texts.append((item.entity_id or item.client_item_id, _facet_tokens(item.payload)))
    # Proposed-vs-proposed.
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            sim = _jaccard(texts[i][1], texts[j][1])
            if sim >= ctx.near_duplicate_threshold:
                out.append(
                    GateDiagnostic(
                        gate="near_duplicate_facet",
                        severity="review",
                        entity_refs=(texts[i][0], texts[j][0]),
                        message=f"proposed facets {texts[i][0]} and {texts[j][0]} are near-duplicates (jaccard {sim:.2f})",
                        suggested_action="review as a merge proposal; never auto-merge",
                    )
                )
    # Proposed-vs-registered.
    registered = {fid: _text_tokens(text) for fid, text in ctx.registered_facet_texts.items()}
    for fid, tokens in texts:
        for rid, rtokens in registered.items():
            sim = _jaccard(tokens, rtokens)
            if sim >= ctx.near_duplicate_threshold:
                out.append(
                    GateDiagnostic(
                        gate="near_duplicate_facet",
                        severity="review",
                        entity_refs=(fid, rid),
                        message=f"proposed facet {fid} is a near-duplicate of registered {rid} (jaccard {sim:.2f})",
                        suggested_action="review as a merge proposal; never auto-merge",
                    )
                )
    return out


def _default_identifiability(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]:
    """Degenerate identifiability check (SEAM for KM5's §11.3 doctor).

    Two proposed facets with an identical discriminating signature and identical
    instructional repairs cannot be told apart by any assessment: emit a
    generate-discriminator need, coarsening only when repairs are identical.
    """

    facets = [item for item in proposal.items if item.item_type == "facet"]
    by_signature: dict[tuple[str, ...], list[GateItem]] = {}
    for item in facets:
        by_signature.setdefault(_facet_signature(item.payload), []).append(item)
    out: list[GateDiagnostic] = []
    for signature, group in by_signature.items():
        if len(group) < 2 or signature == ():
            continue
        refs = tuple(item.entity_id or item.client_item_id for item in group)
        repairs = {tuple(sorted(str(r) for r in (item.payload.get("instructional_repairs") or []))) for item in group}
        if len(repairs) == 1:
            out.append(
                GateDiagnostic(
                    gate="identifiability",
                    severity="review",
                    entity_refs=refs,
                    message="facets share a discriminating signature and identical repairs; no assessment can distinguish them",
                    suggested_action="coarsen to one facet (identical repairs) or author a distinguishing discriminator",
                )
            )
        else:
            out.append(
                GateDiagnostic(
                    gate="identifiability",
                    severity="review",
                    entity_refs=refs,
                    message="facets share a discriminating signature; no distinguishing assessment exists",
                    suggested_action="generate a discriminator (anchor/contrast probe or item)",
                )
            )
    return out


_GATES: tuple[Callable[[GateProposal, GateContext], list[GateDiagnostic]], ...] = (
    _gate_span_resolution,
    _gate_scope,
    _gate_unit_id_validity,
    _gate_conflict_disposition,
    _gate_lock_guard,
    _gate_adequate_provenance,
    _gate_criterion_targets_dag,
    _gate_recipe_validity,
    _gate_dependency_closure,
    _gate_exam_authority,
    _gate_held_out_leakage,
    _gate_token_truncation,
    _gate_practice_exam_only,
    _gate_duplicate_ids_dangling,
    _gate_near_duplicate_facets,
)


# --- helpers ----------------------------------------------------------------


def _criteria_of(item: GateItem) -> list[dict[str, Any]]:
    criteria = item.payload.get("criteria")
    if isinstance(criteria, list):
        return [c for c in criteria if isinstance(c, dict)]
    rubric = item.payload.get("grading_rubric")
    if isinstance(rubric, dict) and isinstance(rubric.get("criteria"), list):
        return [c for c in rubric["criteria"] if isinstance(c, dict)]
    return []


def _blueprints_of(item: GateItem) -> list[dict[str, Any]]:
    blueprints = item.payload.get("blueprints")
    if isinstance(blueprints, list):
        return [b for b in blueprints if isinstance(b, dict)]
    return []


def _facet_tokens(payload: dict[str, Any]) -> set[str]:
    parts = [payload.get("title") or "", payload.get("claim") or "", payload.get("description") or ""]
    return _text_tokens(" ".join(str(p) for p in parts))


def _facet_signature(payload: dict[str, Any]) -> tuple[str, ...]:
    claim = str(payload.get("claim") or payload.get("title") or "").strip().lower()
    error_sigs = tuple(sorted(str(s).strip().lower() for s in (payload.get("error_signatures") or [])))
    if not claim and not error_sigs:
        return ()
    return (claim, *error_sigs)


def _text_tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 0.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def _first_cycle(graph: dict[str, Iterable[str]]) -> list[str] | None:
    color: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        color[node] = 1
        stack.append(node)
        for neighbor in graph.get(node, []):
            neighbor = str(neighbor)
            if neighbor not in graph:
                continue
            state = color.get(neighbor, 0)
            if state == 1:
                idx = stack.index(neighbor)
                return [*stack[idx:], neighbor]
            if state == 0:
                found = visit(neighbor)
                if found is not None:
                    return found
        stack.pop()
        color[node] = 2
        return None

    for node in graph:
        if color.get(node, 0) == 0:
            found = visit(node)
            if found is not None:
                return found
    return None
