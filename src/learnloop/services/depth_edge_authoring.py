"""Depth-edge authoring: the P1 curated-edge half (spec v2 §depth, spec_p1 §3.1.1).

Two-level authoring: the owner curates reusable EDGE TEMPLATES (structural
patterns — allowed capability transitions, per-dimension step deltas, exit-gate
kinds); an LLM instantiates concrete EDGE INSTANCES for one commitment. Every
instance is admitted or rejected by SIX deterministic gates — model judgment
never authorizes an edge — and only learner/owner-confirmed admitted instances
are PINNED into a new immutable envelope version (plus matching milestone
rows), which is the sole authority ``depth_transition`` and ``commitment_arcs``
read. Auto-activation stays behind U-018 (`depth_transition.LIVE_ACTIVATION_ENABLED`);
nothing here activates anything.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services import commitments as C
from learnloop.services.activities import _canonical_hash
from learnloop.services.activity_patterns import (
    LEGACY_UNMAPPED,
    ensure_builtin_task_feature_schema,
    ensure_capability_alias_registry,
    map_capability,
    validate_task_features,
)
from learnloop.services.depth_rungs import project_task_contract
from learnloop.services.synthesis_gates import GateDiagnostic

EXIT_GATE_KINDS: frozenset[str] = frozenset({"n_of_m_success", "fresh_surface_pass", "certified_attempt"})
FRESH_PROOF_KINDS: frozenset[str] = frozenset({"fresh_surface", "reserved_family_mint"})

# Ordered dimensions whose template step deltas are measured in vocabulary
# positions (complexity is measured in integer steps directly).
_ORDERED_VOCAB = {
    "transfer": ("same_context", "near", "far", "novel_combination"),
    "scaffolding": ("worked", "partial", "cue", "none"),  # depth direction: less support
    "span": ("atomic", "single_step", "multi_step", "whole_task"),
}


class DepthEdgeAuthoringError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Templates (owner curation)
# ---------------------------------------------------------------------------


def create_edge_template(
    repository: Repository,
    *,
    template_slug: str,
    body: Mapping[str, Any],
    domain_scope: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> tuple[str, str]:
    """Create a template with its version 1 (status ``draft``)."""

    _validate_template_body(body)
    if repository.depth_edge_template_by_slug(template_slug) is not None:
        raise DepthEdgeAuthoringError(f"template slug already exists: {template_slug}")
    template_id = repository.insert_depth_edge_template(
        template_slug=template_slug, domain_scope=domain_scope, clock=clock
    )
    version_id = repository.insert_depth_edge_template_version(
        template_id=template_id,
        version=1,
        body_json=json.dumps(dict(body), sort_keys=True),
        content_hash=_canonical_hash(dict(body)),
        clock=clock,
    )
    return template_id, version_id


def append_template_version(
    repository: Repository,
    *,
    template_slug: str,
    body: Mapping[str, Any],
    clock: Clock | None = None,
) -> str:
    _validate_template_body(body)
    template = repository.depth_edge_template_by_slug(template_slug)
    if template is None:
        raise DepthEdgeAuthoringError(f"unknown template slug: {template_slug}")
    versions = repository.depth_edge_template_versions_for(template["id"])
    next_version = max((v["version"] for v in versions), default=0) + 1
    return repository.insert_depth_edge_template_version(
        template_id=template["id"],
        version=next_version,
        body_json=json.dumps(dict(body), sort_keys=True),
        content_hash=_canonical_hash(dict(body)),
        clock=clock,
    )


def review_edge_template(
    repository: Repository,
    *,
    version_id: str,
    status: str,
    reviewed_by: str = "owner",
    clock: Clock | None = None,
) -> None:
    if status not in ("reviewed", "retired"):
        raise DepthEdgeAuthoringError("review status must be 'reviewed' or 'retired'")
    if not repository.review_depth_edge_template_version(
        version_id, status=status, reviewed_by=reviewed_by, clock=clock
    ):
        raise DepthEdgeAuthoringError(f"unknown template version: {version_id}")


def _validate_template_body(body: Mapping[str, Any]) -> None:
    if not isinstance(body.get("step_deltas"), Mapping) or not body["step_deltas"]:
        raise DepthEdgeAuthoringError("template body needs non-empty step_deltas ({dim: max step})")
    exit_kind = body.get("exit_gate_kind")
    if exit_kind not in EXIT_GATE_KINDS:
        raise DepthEdgeAuthoringError(f"exit_gate_kind must be one of {sorted(EXIT_GATE_KINDS)}")
    if body.get("fresh_proof_kind") not in FRESH_PROOF_KINDS:
        raise DepthEdgeAuthoringError(f"fresh_proof_kind must be one of {sorted(FRESH_PROOF_KINDS)}")
    if not body.get("eligible_pattern_slugs"):
        raise DepthEdgeAuthoringError("template body needs eligible_pattern_slugs")


# ---------------------------------------------------------------------------
# Instance authoring (owner-invoked; candidates only)
# ---------------------------------------------------------------------------


def author_edge_instances(
    repository: Repository,
    client: Any,
    *,
    commitment_id: str,
    template_version_ids: list[str],
    count: int = 1,
    author: str = "codex",
    clock: Clock | None = None,
) -> list[dict[str, Any]]:
    """LLM-author edge instances from reviewed templates; each is immediately
    gated and stored ``admitted`` or ``rejected`` with its full admission
    report. Returns the stored instance rows. Never activates anything."""

    from learnloop.codex.client import DepthEdgeInstanceContext

    run = getattr(client, "run_depth_edge_instances", None)
    if run is None:
        raise DepthEdgeAuthoringError("provider does not implement run_depth_edge_instances")

    head = C.resolve_head(repository, commitment_id)
    envelope_row = _envelope_row(repository, head.depth_envelope_version_id)
    template_versions = []
    for version_id in template_version_ids:
        row = repository.depth_edge_template_version(version_id)
        if row is None:
            raise DepthEdgeAuthoringError(f"unknown template version: {version_id}")
        if row["status"] != "reviewed":
            # Fail closed: only owner-reviewed templates may parent instances.
            raise DepthEdgeAuthoringError(
                f"template version {version_id} is {row['status']!r}, not 'reviewed'"
            )
        template_versions.append(row)

    ensure_capability_alias_registry(repository)
    schema_version_id = ensure_builtin_task_feature_schema(repository)
    schema_row = repository.task_feature_schema_version(schema_version_id) or {}
    pattern_slugs = sorted(
        {
            slug
            for row in template_versions
            for slug in json.loads(row["body_json"]).get("eligible_pattern_slugs", [])
        }
    )
    context = DepthEdgeInstanceContext(
        commitment_id=commitment_id,
        templates=[
            {"template_version_id": row["id"], **json.loads(row["body_json"])}
            for row in template_versions
        ],
        envelope_bounds=json.loads(envelope_row.get("bounds_json") or "{}"),
        current_milestones=json.loads(envelope_row.get("reviewed_edges_json") or "[]"),
        pattern_slugs=pattern_slugs,
        task_feature_schema=json.loads(schema_row.get("dimensions_json") or "{}"),
        count=count,
    )
    batch = run(context)

    stored: list[dict[str, Any]] = []
    template_by_id = {row["id"]: row for row in template_versions}
    for payload in batch.instances[: max(count, len(batch.instances))]:
        # Attribute each instance to the first template whose gates it passes,
        # falling back to the first template's report when none admit.
        reports: list[tuple[str, list[GateDiagnostic]]] = []
        for row in template_versions:
            diagnostics = admit_edge_instance(
                repository,
                instance=payload.model_dump(mode="json"),
                template_version=row,
                envelope_row=envelope_row,
            )
            reports.append((row["id"], diagnostics))
            if not any(d.severity == "hard_fail" for d in diagnostics):
                break
        template_version_id, diagnostics = reports[-1]
        admitted = not any(d.severity == "hard_fail" for d in diagnostics)
        instance_id = repository.insert_depth_edge_instance(
            {
                "template_version_id": template_version_id,
                "commitment_id": commitment_id,
                "edge_id": payload.edge_id or f"edge_{new_ulid()[:8]}",
                "predecessor_milestone": payload.predecessor_milestone,
                "successor_milestone_slug": payload.successor_milestone_slug,
                "successor_task_contract_json": json.dumps(payload.successor_task_contract, sort_keys=True),
                "entry_evidence_json": json.dumps(payload.entry_evidence) if payload.entry_evidence else None,
                "exit_evidence_json": json.dumps(payload.exit_evidence, sort_keys=True),
                "fresh_proof_json": json.dumps(payload.fresh_proof, sort_keys=True),
                "expected_burden_json": json.dumps(payload.expected_burden, sort_keys=True),
                "activity_path_json": json.dumps(payload.activity_path, sort_keys=True),
                "status": "admitted" if admitted else "rejected",
                "admission_report_json": json.dumps([d.to_dict() for d in diagnostics]),
                "author": author,
            },
            clock=clock,
        )
        stored.append(repository.depth_edge_instance(instance_id) or {})
    return stored


# ---------------------------------------------------------------------------
# Deterministic admission gates (all hard_fail on violation; fail closed)
# ---------------------------------------------------------------------------


def admit_edge_instance(
    repository: Repository,
    *,
    instance: Mapping[str, Any],
    template_version: Mapping[str, Any],
    envelope_row: Mapping[str, Any],
) -> list[GateDiagnostic]:
    """The six §5.7-adjacent admission gates over one candidate edge instance."""

    diagnostics: list[GateDiagnostic] = []
    edge_ref = str(instance.get("edge_id") or "edge")

    def fail(gate: str, message: str, action: str) -> None:
        diagnostics.append(
            GateDiagnostic(
                gate=gate,
                severity="hard_fail",
                entity_refs=(edge_ref,),
                message=message,
                suggested_action=action,
            )
        )

    body = json.loads(template_version["body_json"]) if isinstance(template_version.get("body_json"), str) else dict(template_version.get("body_json") or {})
    contract = instance.get("successor_task_contract")
    if isinstance(contract, str):
        try:
            contract = json.loads(contract)
        except json.JSONDecodeError:
            contract = None
    contract = contract if isinstance(contract, Mapping) else {}

    schema_version_id = ensure_builtin_task_feature_schema(repository)

    # Gate 1 — well-formed successor contract.
    capability = contract.get("capability")
    if not isinstance(capability, str) or map_capability(repository, capability) == LEGACY_UNMAPPED:
        fail("edge_contract", f"unknown or missing capability {capability!r}", "use the closed capability vocabulary")
    projected = project_task_contract(repository, contract, schema_version_id)
    if projected is None:
        fail("edge_contract", "successor task contract does not project to a valid task-feature point", "fix task_features/task_feature_bounds")
    else:
        mapped_capability, features, _bounds = projected
        if mapped_capability == "coordination" and features.get("span") != "whole_task":
            fail("edge_contract", "coordination requires span=whole_task", "use whole_task span")
    exit_evidence = _as_dict(instance.get("exit_evidence_json") or instance.get("exit_evidence"))
    if exit_evidence.get("kind") not in EXIT_GATE_KINDS:
        fail("edge_contract", f"exit_evidence.kind must be one of {sorted(EXIT_GATE_KINDS)}", "declare an observable exit gate")
    elif not isinstance(exit_evidence.get("threshold"), (int, float, Mapping)):
        fail("edge_contract", "exit_evidence needs a numeric threshold", "add a threshold")
    burden = _as_dict(instance.get("expected_burden_json") or instance.get("expected_burden"))
    if not burden:
        fail("edge_contract", "expected_burden is missing", "estimate sessions/attempts to cross the edge")

    # Gate 2 — delta strictly inside the envelope bounds.
    bounds = json.loads(envelope_row.get("bounds_json") or "{}")
    if projected is not None:
        _mapped, features, _b = projected
        for dim, value in features.items():
            allowed = bounds.get(dim)
            if allowed is None:
                # Unbounded dimension = unauthorized region: refuse, never assume.
                fail("envelope_bounds", f"envelope does not bound dimension {dim!r}", "shrink the contract or widen the envelope via the confirmed-successor path")
                continue
            if not _value_within_bound(dim, value, allowed):
                fail("envelope_bounds", f"{dim}={value!r} outside the envelope bound {allowed!r}", "stay inside the authorized region")

    # Gate 3 — monotone, template-conformant step.
    predecessor_features = _predecessor_features(repository, envelope_row, str(instance.get("predecessor_milestone") or ""))
    if projected is not None and predecessor_features is not None:
        _mapped, features, _b = projected
        deltas = body.get("step_deltas") or {}
        changed = False
        for dim, value in features.items():
            prev = predecessor_features.get(dim)
            if prev is None or prev == value:
                continue
            changed = True
            step = _dimension_step(dim, prev, value)
            if step is None:
                fail("template_step", f"{dim}: cannot compare {prev!r} -> {value!r}", "use vocabulary values")
                continue
            if step < 0:
                fail("template_step", f"{dim} regresses ({prev!r} -> {value!r})", "successor must be deeper, not shallower")
                continue
            max_step = deltas.get(dim)
            if max_step is not None and step > int(max_step):
                fail("template_step", f"{dim} step {step} exceeds template delta {max_step}", "take a smaller step")
        if not changed:
            fail("template_step", "successor does not differ from predecessor on any dimension", "deepen at least one dimension")
    allowed_transitions = body.get("capability_transitions")
    if projected is not None and allowed_transitions:
        mapped_capability = projected[0]
        pairs = {(str(t.get("from")), str(t.get("to"))) for t in allowed_transitions if isinstance(t, Mapping)}
        predecessor_capability = (predecessor_features or {}).get("capability")
        if predecessor_capability is not None and (str(predecessor_capability), mapped_capability) not in pairs:
            fail("template_step", f"capability transition {predecessor_capability!r} -> {mapped_capability!r} not allowed by template", "use an allowed transition")

    # Gate 4 — satisfiable fresh-proof route.
    fresh = _as_dict(instance.get("fresh_proof_json") or instance.get("fresh_proof"))
    if fresh.get("kind") not in FRESH_PROOF_KINDS:
        fail("fresh_proof", f"fresh_proof.kind must be one of {sorted(FRESH_PROOF_KINDS)}", "name a fresh-proof route")

    # Gate 5 — admitted activity path.
    path = _as_dict(instance.get("activity_path_json") or instance.get("activity_path"))
    slug = str(path.get("pattern_slug") or "")
    eligible = set(body.get("eligible_pattern_slugs") or [])
    if not slug:
        fail("activity_path", "activity_path.pattern_slug is missing", "name an eligible pattern")
    elif eligible and slug not in eligible:
        fail("activity_path", f"pattern {slug!r} not eligible for this template", f"use one of {sorted(eligible)}")
    else:
        pattern = repository.activity_pattern_version_by_slug(pattern_slug=slug, status="active")
        if pattern is None:
            pattern = repository.activity_pattern_version_by_slug(pattern_slug=slug)
        if pattern is None:
            fail("activity_path", f"no admitted activity pattern {slug!r}", "register the pattern first")
        else:
            purpose = str(path.get("purpose") or "practice")
            allowed_purposes = json.loads(pattern.get("allowed_purposes_json") or "[]")
            if allowed_purposes and purpose not in allowed_purposes:
                fail("activity_path", f"pattern {slug!r} does not allow purpose {purpose!r}", f"use one of {allowed_purposes}")

    # Gate 6 — leakage + DAG integrity.
    blob = json.dumps({k: v for k, v in instance.items() if k != "admission_report_json"}, default=str)
    if "reserved_surface" in blob:
        fail("leakage_dag", "instance references a reserved assessment surface", "never cite reserved surfaces")
    edges = json.loads(envelope_row.get("reviewed_edges_json") or "[]")
    existing_ids = {str(e.get("edge_id")) for e in edges if isinstance(e, Mapping)}
    if str(instance.get("edge_id") or "") in existing_ids:
        fail("leakage_dag", f"edge_id {instance.get('edge_id')!r} already exists in the envelope DAG", "pick a unique edge id")
    predecessor = str(instance.get("predecessor_milestone") or "")
    known_milestones = {str(e.get("predecessor_milestone")) for e in edges if isinstance(e, Mapping)} | {
        str(e.get("successor_milestone")) for e in edges if isinstance(e, Mapping)
    }
    if edges and predecessor and predecessor not in known_milestones:
        fail("leakage_dag", f"predecessor milestone {predecessor!r} is not in the current DAG", "anchor the edge to an existing milestone")
    successor = str(instance.get("successor_milestone_slug") or "")
    if successor and successor == predecessor:
        fail("leakage_dag", "successor equals predecessor (cycle)", "name a new successor milestone")

    return diagnostics


# ---------------------------------------------------------------------------
# Pinning (learner/owner confirmation -> immutable envelope authority)
# ---------------------------------------------------------------------------


def pin_admitted_edges(
    repository: Repository,
    *,
    commitment_id: str,
    instance_ids: list[str],
    confirmed_by: str = "learner",
    receipt_key: str | None = None,
    clock: Clock | None = None,
) -> str:
    """Append confirmed admitted instances into a NEW envelope version (bounds
    unchanged — no widening) plus matching ``depth_milestone_versions`` rows.
    Idempotent on ``receipt_key``. Returns the new envelope version id."""

    key = receipt_key or f"pin:{commitment_id}:{','.join(sorted(instance_ids))}"
    for existing in repository.depth_edge_instances_for(commitment_id, status="pinned"):
        if existing.get("receipt_key") == key:
            return str(existing["pinned_envelope_version_id"])

    instances: list[dict[str, Any]] = []
    for instance_id in instance_ids:
        row = repository.depth_edge_instance(instance_id)
        if row is None:
            raise DepthEdgeAuthoringError(f"unknown edge instance: {instance_id}")
        if row["commitment_id"] != commitment_id:
            raise DepthEdgeAuthoringError(f"instance {instance_id} belongs to another commitment")
        if row["status"] != "admitted":
            raise DepthEdgeAuthoringError(f"instance {instance_id} is {row['status']!r}, not 'admitted'")
        instances.append(row)
    if not instances:
        raise DepthEdgeAuthoringError("no instances to pin")

    head = C.resolve_head(repository, commitment_id)
    envelope_row = _envelope_row(repository, head.depth_envelope_version_id)
    bounds = json.loads(envelope_row.get("bounds_json") or "{}")
    reviewed_edges = json.loads(envelope_row.get("reviewed_edges_json") or "[]")
    for row in instances:
        reviewed_edges.append(
            {
                "edge_id": row["edge_id"],
                "reviewed": True,
                "predecessor_milestone": row["predecessor_milestone"],
                "successor_milestone": row["successor_milestone_slug"],
                "template_version_id": row["template_version_id"],
                "instance_id": row["id"],
                "confirmed_by": confirmed_by,
            }
        )

    version = C.change_depth_envelope(
        repository,
        commitment_id=commitment_id,
        bounds=bounds,
        reviewed_edges=reviewed_edges,
        change_reason="depth_edges_pinned",
        author=confirmed_by,
        clock=clock,
    )
    envelope_version_id = version.depth_envelope_version_id

    for row in instances:
        contract_json = row["successor_task_contract_json"]
        repository.insert_depth_milestone_version(
            envelope_version_id=envelope_version_id,
            milestone_slug=row["successor_milestone_slug"],
            task_contract_json=contract_json,
            entry_evidence_json=row.get("entry_evidence_json"),
            exit_evidence_json=row.get("exit_evidence_json"),
            fresh_proof_json=row.get("fresh_proof_json"),
            expected_burden_json=row.get("expected_burden_json"),
            content_hash=_canonical_hash(
                {"milestone": row["successor_milestone_slug"], "contract": contract_json}
            ),
            clock=clock,
        )
        repository.update_depth_edge_instance_status(
            row["id"], status="pinned", pinned_envelope_version_id=envelope_version_id, clock=clock
        )
        with repository.connection() as connection:
            connection.execute(
                "UPDATE depth_edge_instances SET receipt_key = ? WHERE id = ? AND receipt_key IS NULL",
                (key, row["id"]),
            )
            connection.commit()
    return envelope_version_id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _envelope_row(repository: Repository, envelope_version_id: str | None) -> dict[str, Any]:
    if not envelope_version_id:
        raise DepthEdgeAuthoringError("commitment has no depth envelope version")
    row = repository.depth_envelope_version(envelope_version_id)
    if row is None:
        raise DepthEdgeAuthoringError(f"unknown envelope version: {envelope_version_id}")
    return row


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return dict(value) if isinstance(value, Mapping) else {}


def _value_within_bound(dim: str, value: Any, allowed: Any) -> bool:
    """Is one task-feature value inside one envelope bound?

    Bounds may be a max scalar (ordinal), an allowed-values list, or a
    ``{"max": ...}`` mapping. Unknown shapes refuse (fail closed).
    """

    if isinstance(allowed, Mapping):
        allowed = allowed.get("max", allowed.get("values"))
    if dim == "complexity" and isinstance(allowed, (int, float)) and isinstance(value, (int, float)):
        return value <= allowed
    if isinstance(allowed, (list, tuple, set)):
        return value in allowed
    if dim in _ORDERED_VOCAB and isinstance(allowed, str):
        order = _ORDERED_VOCAB[dim]
        try:
            return order.index(str(value)) <= order.index(allowed)
        except ValueError:
            return False
    return value == allowed


def _predecessor_features(
    repository: Repository, envelope_row: Mapping[str, Any], predecessor_milestone: str
) -> dict[str, Any] | None:
    """The predecessor milestone's task-feature point (+capability), or None
    when the milestone has no stored contract (root milestones)."""

    if not predecessor_milestone:
        return None
    milestone = repository.depth_milestone_version_for(
        str(envelope_row["id"]), predecessor_milestone
    )
    if milestone is None:
        return None
    try:
        contract = json.loads(milestone["task_contract_json"] or "{}")
    except (json.JSONDecodeError, TypeError):
        return None
    schema_version_id = ensure_builtin_task_feature_schema(repository)
    projected = project_task_contract(repository, contract, schema_version_id)
    if projected is None:
        return None
    capability, features, _bounds = projected
    return {"capability": capability, **features}


def _dimension_step(dim: str, prev: Any, new: Any) -> int | None:
    """Signed depth step for one dimension (positive = deeper), or None when
    the values cannot be compared."""

    if dim == "complexity":
        if isinstance(prev, (int, float)) and isinstance(new, (int, float)):
            return int(new) - int(prev)
        return None
    order = _ORDERED_VOCAB.get(dim)
    if order is not None:
        try:
            return order.index(str(new)) - order.index(str(prev))
        except ValueError:
            return None
    if dim == "response":
        # Response forms are categorical; any change counts as one step.
        return 1 if prev != new else 0
    if dim == "representation":
        prev_set, new_set = set(prev or []), set(new or [])
        return 1 if new_set != prev_set else 0
    return 1 if prev != new else 0
