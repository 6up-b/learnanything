"""P2 PRACTICE track -- the bounded, owner-admitted rotating practice pool
(spec_p2_narrow_golden_path §7.3, U-028, §12.4; design B.7; migration 085).

Composition-only over the landed P1 substrate. P2 owns the pool bookkeeping +
admission provenance and the ROTATION ORDERING; every measurement primitive is a
landed service:

- U-028 admission mirrors blueprint / diagnostic-pack review: an LLM drafts a
  candidate within admitted-card / blueprint bounds (a deterministic stub in tests,
  ``golden_path_fixture.stub_pool_surfaces``) and the owner reviews each BEFORE
  admission -- nothing serves as practice until ``admitted``. An assessment-reserved
  surface (a surface_hash / fingerprint collision with the run's reserve) is refused
  at admission -- it never enters a generation candidate set (§7.3).
- ``next_practice_surface`` serves ONE current surface + at most one cached spare
  (``pool_spare_cache``); it applies the P1 ``familiarity_projection_v1`` hard-
  collision + warmth gate and the ``surface_mint.rotation_decision`` lazy-rotation
  rule (rotate after warmth OR cadence, never a new surface every attempt). Card-level
  scheduling only -- never a per-surface FSRS write. It NEVER claims freshness when
  the ledger is missing/uncertain (an ``unknown`` fingerprint is reduced-evidence).
- ``open_practice`` administers through ``activities.open_administration`` at the
  PRACTICE purpose, so a practice exposure lands in the ONE shared exposure ledger --
  the assessment reserve's leakage gate then sees it exactly as any other exposure
  (§12.4 global-exposure-invalidates-reserve). Practice consumes no pristine
  assessment eligibility beyond that ordinary ledger effect.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services import familiarity as F
from learnloop.services import surface_mint as SM
from learnloop.services.activities import (
    Administration,
    ResolvedActivity,
    _canonical_hash,
    _json,
    open_administration,
    reserve_surface,
)

POOL_SPEC_SCHEMA_VERSION = 1  # structural enum; practice-pool spec schema pin.

# decision parameter -- how many spare surfaces are pre-cached beyond the current
# one (§7.3 "one current + one cached spare at most"). Registered heuristic in the
# P0 decision-parameter registry (design §E).
POOL_SPARE_CACHE = 1


class InvalidPool(Exception):
    """A pool surface cannot be admitted (out of blueprint bounds, or it collides
    with an assessment-reserved surface, §7.3)."""


@dataclass(frozen=True)
class PoolSurface:
    surface_slug: str
    angle: str
    admission_status: str
    provenance: str
    surface_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PoolRecord:
    pool_id: str
    pool_slug: str
    blueprint_version_id: str
    status: str
    content_hash: str
    surfaces: tuple[PoolSurface, ...] = ()
    minted: bool = True

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["surfaces"] = [s.as_dict() for s in self.surfaces]
        return data


@dataclass(frozen=True)
class ServedSurface:
    surface_id: str
    surface_slug: str
    angle: str
    fresh: bool
    reduced_evidence: bool
    warmth: float
    exposure_status: str
    needs_rotation: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PoolSelection:
    pool_id: str
    current: ServedSurface | None
    spare: ServedSurface | None
    rotated: bool
    reason: str
    fallback: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "pool_id": self.pool_id,
            "current": self.current.as_dict() if self.current else None,
            "spare": self.spare.as_dict() if self.spare else None,
            "rotated": self.rotated,
            "reason": self.reason,
            "fallback": self.fallback,
        }


# ---------------------------------------------------------------------------
# Deterministic assembly (U-028) -- register -> admit -> review -> activate
# ---------------------------------------------------------------------------

def _canonical_surfaces(surfaces: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for surface in surfaces:
        out.append(
            {
                "surface_slug": surface["surface_slug"],
                "angle": str(surface.get("angle", "")),
                "provenance": str(surface.get("provenance", "llm_within_bounds")),
            }
        )
    out.sort(key=lambda s: s["surface_slug"])
    return out


def pool_content_hash(
    *, pool_slug: str, blueprint_version_id: str, surfaces: Sequence[Mapping[str, Any]]
) -> str:
    """The timestamp/id-independent content identity of a pool (§12.8 determinism)."""

    return _canonical_hash(
        {
            "schema_version": POOL_SPEC_SCHEMA_VERSION,
            "pool_slug": pool_slug,
            "blueprint_version_id": blueprint_version_id,
            "surfaces": _canonical_surfaces(surfaces),
        }
    )


def assemble_pool(
    repository: Repository,
    *,
    pool_slug: str,
    blueprint_version_id: str,
    surfaces: Sequence[Mapping[str, Any]],
    clock: Clock | None = None,
) -> PoolRecord:
    """Assemble a practice pool from candidate surfaces for a reviewed blueprint
    version (§7.3). Deterministic + idempotent: two assemblies with the same surfaces
    produce identical content hashes and the same pool row. Surfaces enter as
    ``candidate`` (nothing serves until the owner admits it)."""

    if not surfaces:
        raise InvalidPool("pool must carry at least one candidate surface (§7.3)")
    content_hash = pool_content_hash(
        pool_slug=pool_slug, blueprint_version_id=blueprint_version_id, surfaces=surfaces
    )
    result = repository.ensure_practice_pool(
        pool_slug=pool_slug,
        blueprint_version_id=blueprint_version_id,
        content_hash=content_hash,
        clock=clock,
    )
    pool_id = result["pool"]["id"]
    for surface in _canonical_surfaces(surfaces):
        repository.register_practice_pool_surface(
            pool_id=pool_id,
            surface_slug=surface["surface_slug"],
            angle=surface["angle"],
            provenance=surface["provenance"],
            content_hash=_canonical_hash(surface),
            clock=clock,
        )
    return _load_pool(repository, pool_id, minted=not result["already_exists"])


def _assert_no_assessment_collision(
    repository: Repository, *, surface_id: str, assessment_surface_id: str | None
) -> None:
    """Refuse a pool surface that collides with the run's assessment reserve (§7.3):
    an exact ``surface_hash`` or ``fingerprint`` match, or a hard-namespace collision.
    An assessment-reserved surface must never enter a practice candidate set."""

    if assessment_surface_id is None:
        return
    candidate = repository.fetch_surface(surface_id)
    reserve = repository.fetch_surface(assessment_surface_id)
    if candidate is None or reserve is None:
        return
    if candidate["surface_hash"] == reserve["surface_hash"]:
        raise InvalidPool(f"pool surface {surface_id!r} hard-collides (surface_hash) with the assessment reserve (§7.3)")
    if candidate.get("fingerprint") and candidate.get("fingerprint") == reserve.get("fingerprint"):
        raise InvalidPool(f"pool surface {surface_id!r} hard-collides (fingerprint) with the assessment reserve (§7.3)")
    reserve_fam = F.familiarity_projection_v1(repository, surface_id=surface_id)
    for collision in reserve_fam.hard_collisions:
        if assessment_surface_id in collision.sibling_surface_ids:
            raise InvalidPool(f"pool surface {surface_id!r} hard-collides ({collision.namespace}) with the assessment reserve (§7.3)")


def _assert_practice_purpose(repository: Repository, surface_id: str) -> None:
    """A purpose-specific family can never transition roles (§12.4): the resolved
    surface's card family must be a practice family, not an assessment/diagnostic one."""

    surface = repository.fetch_surface(surface_id)
    if surface is None:
        return
    card_version_id = surface.get("card_version_id")
    if card_version_id is None:
        return
    purpose = repository.activity_family_purpose_for_card_version(card_version_id)
    if purpose is not None and purpose != "practice":
        raise InvalidPool(
            f"cannot admit a {purpose!r}-purpose surface into a practice pool -- "
            "purpose-specific families cannot transition roles (§12.4)"
        )


def admit_pool_surface(
    repository: Repository,
    *,
    pool_id: str,
    surface_slug: str,
    surface_id: str | None = None,
    assessment_surface_id: str | None = None,
    checks: Mapping[str, Any] | None = None,
    author: str = "owner",
    clock: Clock | None = None,
) -> PoolRecord:
    """Owner admits one reviewed surface into the pool (U-028). Refuses an
    assessment-reserved-surface collision and a non-practice purpose. Append-only."""

    if surface_id is not None:
        _assert_practice_purpose(repository, surface_id)
        _assert_no_assessment_collision(
            repository, surface_id=surface_id, assessment_surface_id=assessment_surface_id
        )
    repository.set_practice_pool_surface_admission(
        pool_id=pool_id,
        surface_slug=surface_slug,
        admission_status="admitted",
        surface_id=surface_id,
        detail_json=_json(dict(checks)) if checks else None,
        author=author,
        clock=clock,
    )
    return _load_pool(repository, pool_id)


def reject_pool_surface(
    repository: Repository,
    *,
    pool_id: str,
    surface_slug: str,
    reason: str,
    author: str = "owner",
    clock: Clock | None = None,
) -> PoolRecord:
    repository.set_practice_pool_surface_admission(
        pool_id=pool_id,
        surface_slug=surface_slug,
        admission_status="rejected",
        surface_id=None,
        detail_json=_json({"reason": reason}),
        author=author,
        clock=clock,
    )
    return _load_pool(repository, pool_id)


def review_pool(
    repository: Repository,
    *,
    pool_id: str,
    checks: Mapping[str, Any] | None = None,
    author: str = "owner",
    clock: Clock | None = None,
) -> PoolRecord:
    """Owner marks the pool reviewed once every surface is admitted (§7.3)."""

    surfaces = repository.practice_pool_surfaces_for(pool_id)
    if not surfaces or any(s["admission_status"] != "admitted" for s in surfaces):
        raise InvalidPool("cannot review a pool with un-admitted surfaces (§7.3)")
    repository.transition_practice_pool(
        pool_id=pool_id, status="reviewed", kind="reviewed",
        detail_json=_json(dict(checks)) if checks else None, author=author, clock=clock,
    )
    return _load_pool(repository, pool_id)


def activate_pool(
    repository: Repository, *, pool_id: str, author: str = "owner", clock: Clock | None = None
) -> PoolRecord:
    pool = repository.practice_pool(pool_id)
    if pool is None or pool["status"] not in ("reviewed", "active"):
        raise InvalidPool(f"cannot activate pool in status {pool['status'] if pool else None!r}")
    if pool["status"] == "reviewed":
        repository.transition_practice_pool(
            pool_id=pool_id, status="active", kind="activated", author=author, clock=clock
        )
    return _load_pool(repository, pool_id)


# ---------------------------------------------------------------------------
# Rotation / selection (§7.3) -- one current + one cached spare
# ---------------------------------------------------------------------------

def _serve(repository: Repository, surface_row: Mapping[str, Any], *, warmth_threshold: float | None, cadence: int | None) -> ServedSurface:
    surface_id = surface_row["surface_id"]
    fam = F.familiarity_projection_v1(repository, surface_id=surface_id, purpose="practice")
    rot = SM.rotation_decision(
        repository, surface_id=surface_id, warmth_threshold=warmth_threshold, cadence=cadence
    )
    # §7.3: never claim freshness when the ledger is missing/uncertain. Only a
    # fingerprinted-but-unexposed surface ('novel') is fresh; 'unknown'/'warm' are not.
    fresh = fam.exposure_status == "novel" and not fam.blocks_unseen_claim
    return ServedSurface(
        surface_id=surface_id,
        surface_slug=surface_row["surface_slug"],
        angle=surface_row["angle"],
        fresh=fresh,
        reduced_evidence=not fresh,
        warmth=fam.warmth,
        exposure_status=fam.exposure_status,
        needs_rotation=rot.needs_rotation,
    )


def _record_pool_selection(
    repository: Repository, pool_id: str, selection: PoolSelection, *, clock: Clock | None
) -> None:
    """Write the served/rotated pool ledger events (§7.3 audit). A ``rotated`` event is
    appended FIRST when rotation fired, then always a ``served`` event carrying the
    served surface's freshness/warmth/exposure flags -- so ``pool_status`` shows exactly
    what was served and why."""

    current = selection.current
    if selection.rotated:
        repository.append_practice_pool_event(
            pool_id=pool_id,
            kind="rotated",
            surface_slug=current.surface_slug if current else None,
            detail_json=_json({"reason": selection.reason, "fallback": selection.fallback}),
            clock=clock,
        )
    repository.append_practice_pool_event(
        pool_id=pool_id,
        kind="served",
        surface_slug=current.surface_slug if current else None,
        detail_json=_json(
            {
                "reason": selection.reason,
                "fallback": selection.fallback,
                "surface": current.as_dict() if current else None,
            }
        ),
        clock=clock,
    )


def next_practice_surface(
    repository: Repository,
    *,
    pool_id: str,
    warmth_threshold: float | None = None,
    cadence: int | None = None,
    clock: Clock | None = None,
) -> PoolSelection:
    """Serve one current admitted surface + at most one cached spare (§7.3).

    Lazy rotation: the front admitted surface is served until it needs rotation
    (warmth crosses the registered threshold OR the exposure cadence is reached), at
    which point the next admitted surface becomes current (``rotated=True``). At most
    ``POOL_SPARE_CACHE`` surfaces are cached beyond the current one. When every surface
    is warm / no fresh surface remains, the run may continue consolidation on the
    least-warm eligible familiar surface with VISIBLY REDUCED evidence (never reported
    fresh) -- the ``fallback`` path.

    Every non-empty selection appends ``served`` (and ``rotated`` when rotation fired)
    to the pool ledger (``practice_pool_events``), so the rotation history is auditable
    through :func:`pool_status`.
    """

    admitted = [
        s for s in repository.practice_pool_surfaces_for(pool_id)
        if s["admission_status"] == "admitted" and s["surface_id"]
    ]
    if not admitted:
        return PoolSelection(pool_id=pool_id, current=None, spare=None, rotated=False,
                             reason="no_admitted_surface", fallback=True)

    served = [_serve(repository, s, warmth_threshold=warmth_threshold, cadence=cadence) for s in admitted]

    # Lazy rotation: walk to the first surface that does not need rotation.
    current_idx = None
    for idx, s in enumerate(served):
        if not s.needs_rotation:
            current_idx = idx
            break
    if current_idx is None:
        # Every surface needs rotation and no fresh surface remains -> fall back to the
        # least-warm eligible familiar surface with reduced evidence (§7.3), never fresh.
        least_warm = min(served, key=lambda s: s.warmth)
        selection = PoolSelection(pool_id=pool_id, current=least_warm, spare=None, rotated=True,
                                  reason="all_warm_reduced_evidence_fallback", fallback=True)
        _record_pool_selection(repository, pool_id, selection, clock=clock)
        return selection

    current = served[current_idx]
    rotated = current_idx > 0
    spares = served[current_idx + 1: current_idx + 1 + POOL_SPARE_CACHE]
    spare = spares[0] if spares else None
    reason = "rotated_after_warmth" if rotated else "serving_current"
    selection = PoolSelection(pool_id=pool_id, current=current, spare=spare, rotated=rotated, reason=reason)
    _record_pool_selection(repository, pool_id, selection, clock=clock)
    return selection


def request_spare_mint(
    repository: Repository,
    *,
    card_version_id: str,
    anchor_surface_id: str | None = None,
    requested_angle: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> str:
    """Enqueue a durable, lease-fenced pre-mint request for a fresh spare surface
    (§7.3, design B.7 batch-and-rank). Off the hot path -- it merely records intent;
    the gate-guarded worker (``surface_mint.process_mint_job`` -> ``admit_candidate``
    with a passing ``GateResult``) admits the survivor. A generator outage leaves the
    request pending and never corrupts an in-flight response (§12.4)."""

    return SM.request_candidates(
        repository,
        card_version_id=card_version_id,
        anchor_surface_id=anchor_surface_id,
        requested_angle=requested_angle,
        clock=clock,
    )


# ---------------------------------------------------------------------------
# Administration (§7.3) -- practice purpose through the shared burn boundary
# ---------------------------------------------------------------------------

def open_practice(
    repository: Repository,
    *,
    resolved: ResolvedActivity,
    goal_id: str | None = None,
    assistance: Mapping[str, Any] | None = None,
    feedback_condition: str | None = None,
    algorithm_version: str | None = None,
    clock: Clock | None = None,
) -> Administration:
    """Administer a pool surface at the PRACTICE purpose through the landed atomic
    render/burn boundary (§7.3). The practice exposure lands in the ONE shared ledger,
    so it warms related surfaces and can invalidate an assessment reserve exactly as
    any other exposure -- practice never consumes pristine assessment eligibility
    beyond that ordinary familiarity-ledger effect (§12.4 leakage)."""

    if resolved.purpose != "practice":
        raise InvalidPool(f"open_practice requires a practice-purpose surface, got {resolved.purpose!r}")
    reservation = reserve_surface(
        repository, surface_id=resolved.surface_id, purpose="practice", goal_id=goal_id, clock=clock
    )
    return open_administration(
        repository,
        resolved=resolved,
        reservation=reservation,
        goal_id=goal_id,
        assistance=assistance,
        feedback_condition=feedback_condition,
        algorithm_version=algorithm_version,
        clock=clock,
    )


def pool_status(repository: Repository, *, pool_id: str) -> dict[str, Any]:
    """The current pool + its admission/rotation ledger (§7.3 audit)."""

    record = _load_pool(repository, pool_id)
    events = repository.practice_pool_events_for(pool_id)
    return {"pool": record.as_dict(), "events": events}


def _load_pool(repository: Repository, pool_id: str, *, minted: bool = True) -> PoolRecord:
    row = repository.practice_pool(pool_id)
    if row is None:
        raise InvalidPool(f"unknown practice pool: {pool_id}")
    surfaces = tuple(
        PoolSurface(
            surface_slug=s["surface_slug"],
            angle=s["angle"],
            admission_status=s["admission_status"],
            provenance=s["provenance"],
            surface_id=s["surface_id"],
        )
        for s in repository.practice_pool_surfaces_for(pool_id)
    )
    return PoolRecord(
        pool_id=row["id"],
        pool_slug=row["pool_slug"],
        blueprint_version_id=row["blueprint_version_id"],
        status=row["status"],
        content_hash=row["content_hash"],
        surfaces=surfaces,
        minted=minted,
    )
