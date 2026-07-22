"""P2 LEARNING + PRACTICE track sidecar RPC
(spec_p2_narrow_golden_path §7.1-§7.3, §9; design B.6-B.7).

The five-layer recipe's Python layer for the pattern ladder + the rotating practice
pool. Handlers compose the landed P2 services (``pattern_ladder``, ``surface_pool``)
and never touch SQL directly. Method names are dotted (``ladder.*`` / ``practice_pool.*``)
so the Tauri client maps them 1:1. This module owns its own handler file per the P2
work partition -- it shares only the one-line registration in ``handlers/__init__``.
"""

from __future__ import annotations

from typing import Any

from learnloop.services import pattern_ladder as PL
from learnloop.services import surface_pool as SP
from learnloop.services.activities import resolve_legacy_item
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


# ---------------------------------------------------------------------------
# ladder.* -- the nine-rung pattern ladder (7 ordinals) (§7.1, §7.2)
# ---------------------------------------------------------------------------

class LadderPolicyInput(ParamsModel):
    policy_slug: str = "ladder_v1"


@method("ladder.policy", LadderPolicyInput)
def ladder_policy(ctx: SidecarContext, params: LadderPolicyInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        policy = PL.active_ladder(repository, policy_slug=params.policy_slug)
    except PL.LadderError as exc:
        raise SidecarError("ladder_error", str(exc)) from exc
    return versioned(policy)


class LadderStatusInput(ParamsModel):
    run_id: str


@method("ladder.status", LadderStatusInput)
def ladder_status(ctx: SidecarContext, params: LadderStatusInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        status = PL.ladder_status(repository, params.run_id)
    except PL.LadderError as exc:
        raise SidecarError("run_not_found", str(exc)) from exc
    return versioned(status)


class LadderEnterInput(ParamsModel):
    run_id: str
    reason: str | None = None
    triage: dict[str, Any] | None = None
    demonstrated_capability: bool = False


@method("ladder.enter", LadderEnterInput)
def ladder_enter(ctx: SidecarContext, params: LadderEnterInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        result = PL.enter_ladder(
            repository,
            params.run_id,
            reason=params.reason,
            triage=params.triage,
            demonstrated_capability=params.demonstrated_capability,
        )
    except PL.LadderError as exc:
        raise SidecarError("ladder_error", str(exc)) from exc
    return versioned(result)


class LadderAdvanceInput(ParamsModel):
    run_id: str
    from_stage: str
    outcome: str
    surface_id: str | None = None
    scaffold_use: float | None = None
    eligible: bool = True
    idempotency_key: str | None = None


@method("ladder.advance", LadderAdvanceInput)
def ladder_advance(ctx: SidecarContext, params: LadderAdvanceInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        result = PL.advance_stage(
            repository,
            params.run_id,
            from_stage=params.from_stage,
            outcome=params.outcome,
            surface_id=params.surface_id,
            scaffold_use=params.scaffold_use,
            eligible=params.eligible,
            idempotency_key=params.idempotency_key,
        )
    except PL.LadderError as exc:
        raise SidecarError("ladder_error", str(exc)) from exc
    return versioned(result.as_dict())


# ---------------------------------------------------------------------------
# practice_pool.* -- the rotating practice pool (§7.3, U-028)
# ---------------------------------------------------------------------------

class PoolAssembleInput(ParamsModel):
    pool_slug: str
    blueprint_version_id: str
    surfaces: list[dict[str, Any]]


@method("practice_pool.assemble", PoolAssembleInput)
def pool_assemble(ctx: SidecarContext, params: PoolAssembleInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        pool = SP.assemble_pool(
            repository,
            pool_slug=params.pool_slug,
            blueprint_version_id=params.blueprint_version_id,
            surfaces=params.surfaces,
        )
    except SP.InvalidPool as exc:
        raise SidecarError("invalid_pool", str(exc)) from exc
    return versioned(pool.as_dict())


class PoolAdmitInput(ParamsModel):
    pool_id: str
    surface_slug: str
    surface_id: str | None = None
    assessment_surface_id: str | None = None
    checks: dict[str, Any] | None = None


@method("practice_pool.admit_surface", PoolAdmitInput)
def pool_admit_surface(ctx: SidecarContext, params: PoolAdmitInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        pool = SP.admit_pool_surface(
            repository,
            pool_id=params.pool_id,
            surface_slug=params.surface_slug,
            surface_id=params.surface_id,
            assessment_surface_id=params.assessment_surface_id,
            checks=params.checks,
        )
    except SP.InvalidPool as exc:
        raise SidecarError("invalid_pool", str(exc)) from exc
    return versioned(pool.as_dict())


class PoolReviewInput(ParamsModel):
    pool_id: str
    checks: dict[str, Any] | None = None


@method("practice_pool.review", PoolReviewInput)
def pool_review(ctx: SidecarContext, params: PoolReviewInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        pool = SP.review_pool(repository, pool_id=params.pool_id, checks=params.checks)
    except SP.InvalidPool as exc:
        raise SidecarError("invalid_pool", str(exc)) from exc
    return versioned(pool.as_dict())


class PoolStatusInput(ParamsModel):
    pool_id: str


@method("practice_pool.status", PoolStatusInput)
def pool_status(ctx: SidecarContext, params: PoolStatusInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        status = SP.pool_status(repository, pool_id=params.pool_id)
    except SP.InvalidPool as exc:
        raise SidecarError("pool_not_found", str(exc)) from exc
    return versioned(status)


class PoolNextInput(ParamsModel):
    pool_id: str
    warmth_threshold: float | None = None
    cadence: int | None = None


@method("practice_pool.next_surface", PoolNextInput)
def pool_next_surface(ctx: SidecarContext, params: PoolNextInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    selection = SP.next_practice_surface(
        repository,
        pool_id=params.pool_id,
        warmth_threshold=params.warmth_threshold,
        cadence=params.cadence,
    )
    return versioned(selection.as_dict())


# ---------------------------------------------------------------------------
# practice_pool.* run composition -- discovery + seeding for the run workspace.
# The desktop only knows a run_id; these compose the run -> blueprint -> pool
# lookup so the run screen can drive the §7.3 assemble -> admit -> review ->
# next_surface choreography without a side channel.
# ---------------------------------------------------------------------------

def _require_run(ctx: SidecarContext, run_id: str) -> tuple[Any, Any, dict[str, Any]]:
    vault, repository = ctx.require_vault()
    run = repository.golden_path_run(run_id)
    if run is None:
        raise SidecarError("run_not_found", f"unknown golden-path run {run_id!r}")
    return vault, repository, dict(run)


def _run_pool_view(vault: Any, repository: Any, run: dict[str, Any]) -> dict[str, Any]:
    blueprint_version_id = run["blueprint_version_id"]
    exemplars = repository.target_exemplars_for(blueprint_version_id)
    anchors = []
    held_out_ref = None
    for exemplar in exemplars:
        ref = exemplar["exemplar_ref"]
        if exemplar["exposure_status"] == "unseen_sibling":
            held_out_ref = ref
            continue
        item = vault.practice_items.get(ref)
        anchors.append(
            {
                "ref": ref,
                "in_vault": item is not None,
                "angle": getattr(item, "practice_mode", None) or "anchor_variation",
            }
        )
    pools = repository.practice_pools_for_blueprint(blueprint_version_id)
    latest = pools[-1] if pools else None
    pool = SP.pool_status(repository, pool_id=latest["id"]) if latest else None
    return {
        "run_id": run["id"],
        "blueprint_version_id": blueprint_version_id,
        "reserved_surface_id": run.get("reserved_surface_id"),
        "pool_id": latest["id"] if latest else None,
        "pool": pool,
        "anchors": anchors,
        "held_out_ref": held_out_ref,
    }


class PoolForRunInput(ParamsModel):
    run_id: str


@method("practice_pool.for_run", PoolForRunInput)
def pool_for_run(ctx: SidecarContext, params: PoolForRunInput) -> dict[str, Any]:
    vault, repository, run = _require_run(ctx, params.run_id)
    return versioned(_run_pool_view(vault, repository, run))


class PoolSeedForRunInput(ParamsModel):
    run_id: str


@method("practice_pool.seed_for_run", PoolSeedForRunInput)
def pool_seed_for_run(ctx: SidecarContext, params: PoolSeedForRunInput) -> dict[str, Any]:
    """Assemble a candidate pool from the run blueprint's familiar-anchor
    exemplars (§7.3). Surfaces enter as ``candidate`` — the owner still admits
    each one and marks the pool reviewed before anything serves (U-028)."""

    vault, repository, run = _require_run(ctx, params.run_id)
    surfaces = []
    for exemplar in repository.target_exemplars_for(run["blueprint_version_id"]):
        if exemplar["exposure_status"] != "familiar_anchor":
            continue
        item = vault.practice_items.get(exemplar["exemplar_ref"])
        if item is None:
            continue
        surfaces.append(
            {
                "surface_slug": exemplar["exemplar_ref"],
                "angle": item.practice_mode or "anchor_variation",
                "provenance": "anchor_exemplar",
            }
        )
    if not surfaces:
        raise SidecarError(
            "invalid_pool", "no anchor exemplar from this run's blueprint is present in the vault"
        )
    try:
        SP.assemble_pool(
            repository,
            pool_slug=f"pool_{params.run_id}",
            blueprint_version_id=run["blueprint_version_id"],
            surfaces=surfaces,
        )
    except SP.InvalidPool as exc:
        raise SidecarError("invalid_pool", str(exc)) from exc
    return versioned(_run_pool_view(vault, repository, run))


class PoolAdmitAnchorInput(ParamsModel):
    run_id: str
    pool_id: str
    surface_slug: str


@method("practice_pool.admit_anchor", PoolAdmitAnchorInput)
def pool_admit_anchor(ctx: SidecarContext, params: PoolAdmitAnchorInput) -> dict[str, Any]:
    """Owner admits one seeded anchor surface: resolves the legacy practice item
    to its P0 surface (idempotent) and admits it with the run's assessment
    reserve as the collision guard (§7.3 hard-collision refusal)."""

    vault, repository, run = _require_run(ctx, params.run_id)
    item = vault.practice_items.get(params.surface_slug)
    if item is None:
        raise SidecarError(
            "invalid_pool", f"practice item {params.surface_slug!r} is not in the vault"
        )
    resolved = resolve_legacy_item(vault, repository, item, purpose="practice")
    try:
        SP.admit_pool_surface(
            repository,
            pool_id=params.pool_id,
            surface_slug=params.surface_slug,
            surface_id=resolved.surface_id,
            assessment_surface_id=run.get("reserved_surface_id"),
        )
    except SP.InvalidPool as exc:
        raise SidecarError("invalid_pool", str(exc)) from exc
    return versioned(_run_pool_view(vault, repository, run))
