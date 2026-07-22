"""P1 step 6 -- one familiarity namespace + soft-kinship + familiarity_projection_v1
(spec_p1_shared_substrate §4.1, §4.2, §4.3; standing rules 5 & 7; owner decision A.4).

Three concerns, one learner-wide ledger:

  * **Namespaced hard-correlation groups** (§4.1). Every membership is
    ``namespace + value_hash + surface_id``. Namespaces are NEVER interchangeable
    (``svd-1`` in ``source_example`` cannot collide with ``svd-1`` in
    ``solution_recipe``); a surface may belong to MANY groups and ALL are
    considered -- never first-field-wins (fixing the legacy
    ``canonical_projection.surface_group_id`` bug). A missing fingerprint yields
    ``unknown``, never ``novel`` (§4.1).
  * **Soft-kinship feature vector** (§4.2): a per-surface feature vector, never a
    pre-collapsed group id. ``familiarity_projection_v1`` is a deterministic,
    MONOTONE heuristic over these features -- adding exposure never decreases
    warmth. Every coefficient/threshold is a registered P0 decision parameter
    (``services.parameter_registry``).
  * **Tight-kinship clustering for the evidence cap** (§4.3 + A.4): single-linkage
    threshold clustering scoped to a target x capability x angle neighborhood using
    the pairwise warmth score and the registered ``TIGHT_KINSHIP_THRESHOLD``.

Standing rule 5: **salience signals are never learner evidence.** Familiarity
discounts / withholds evidence and explains warmth; it NEVER mints evidence and
never directly decides whether an answer was correct (§4.2 last line). A
:class:`Familiarity` result therefore carries an explicit ``affects`` allowlist and
no correctness/mastery field, and a static test forbids the belief-update modules
from consuming warmth as a knowledge signal.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository

# Feature-schema pin (string: structural, not a numeric decision knob).
FEATURE_SCHEMA_VERSION = "familiarity_v1"

# Launch fingerprint namespaces (§4.1). Never interchangeable.
NAMESPACES: tuple[str, ...] = (
    "surface_hash",
    "shared_stimulus",
    "source_example",
    "solution_recipe",
    "parameter_template",
    "verbatim_target",
    "external_artifact",
)

# Namespaces whose membership is a policy-declared HARD group -- an exact match
# blocks an unseen/independent claim (§4.1). surface_hash is exact-clone; the
# others are declared shared-stimulus / verbatim hard groups.
HARD_NAMESPACES: frozenset[str] = frozenset(
    {"surface_hash", "shared_stimulus", "verbatim_target", "solution_recipe", "external_artifact"}
)

# Exposure kinds that count as "this surface (or a hard sibling) has been seen".
_EXPOSURE_KINDS: frozenset[str] = frozenset(
    {"rendered", "submitted", "feedback_revealed", "shared_stimulus", "externally_reported"}
)

# What familiarity is allowed to affect (§4.2). Correctness is deliberately absent
# (standing rule 5 / §4.2: it does not directly change whether an answer was correct).
AFFECTS: tuple[str, ...] = (
    "evidence_independence_discount",
    "rotation_need",
    "held_out_eligibility",
    "warmth_explanation",
)

# --- registered decision parameters (register at birth; see parameter_registry) --

# A.4: two surfaces co-cluster when pairwise warmth >= this threshold.
TIGHT_KINSHIP_THRESHOLD = 0.6  # decision parameter

# §5.3: a rotating surface needs rotation once warmth crosses this.
WARMTH_ROTATION_THRESHOLD = 0.5  # decision parameter

# §4.2: per-feature non-negative warmth coefficients (monotone). Angle proximity
# (not distance) is used so every coefficient is non-negative and warmth is monotone
# increasing in each supplied feature.
V1_COEFFICIENTS: dict[str, float] = {
    "target_facet_overlap": 1.2,
    "source_proximity": 0.8,
    "recipe_overlap": 1.0,
    "representation_match": 0.6,
    "answer_structure_match": 0.6,
    "parameter_relationship": 0.7,
    "semantic_similarity": 0.9,
    "angle_proximity": 0.5,
    "recency": 0.7,
    "exposure_count": 0.4,
    "feedback_reveal": 0.5,
}


# ---------------------------------------------------------------------------
# Hard-correlation memberships.
# ---------------------------------------------------------------------------

def record_memberships(
    repository: Repository,
    *,
    surface_id: str,
    memberships: Iterable[Mapping[str, Any]],
    clock: Clock | None = None,
) -> list[str]:
    """Record namespaced hard-group memberships for a surface (§4.1). Idempotent per
    ``(surface, namespace, value_hash)``. An invalid namespace fails closed."""

    out: list[str] = []
    for membership in memberships:
        namespace = membership["namespace"]
        if namespace not in NAMESPACES:
            raise ValueError(f"unknown fingerprint namespace: {namespace!r}")
        out.append(
            repository.record_fingerprint_membership(
                surface_id=surface_id,
                namespace=namespace,
                value_hash=str(membership["value_hash"]),
                provenance=membership.get("provenance"),
                status=membership.get("status", "known"),
                confidence=membership.get("confidence"),
                clock=clock,
            )
        )
    return out


def record_soft_features(
    repository: Repository,
    *,
    surface_id: str,
    features: Mapping[str, Any],
    clock: Clock | None = None,
) -> str:
    """Store the §4.2 soft-kinship feature vector for a surface (never a group id)."""

    return repository.upsert_soft_kinship_features(
        surface_id=surface_id,
        feature_schema_version=FEATURE_SCHEMA_VERSION,
        features=dict(features),
        clock=clock,
    )


# ---------------------------------------------------------------------------
# familiarity_projection_v1 -- deterministic, monotone.
# ---------------------------------------------------------------------------

def warmth_score(features: Mapping[str, Any]) -> float:
    """Deterministic monotone warmth in ``[0, 1)`` over the §4.2 feature vector.

    ``warmth = 1 - exp(-sum_i coeff_i * feature_i)`` with non-negative coefficients
    and clamped non-negative features -- strictly increasing in each feature, so
    adding exposure never decreases warmth (§4.2 monotonicity)."""

    total = 0.0
    for name, coeff in V1_COEFFICIENTS.items():
        value = features.get(name)
        if value is None:
            continue
        total += coeff * max(0.0, float(value))
    return 1.0 - math.exp(-total)


@dataclass(frozen=True)
class HardCollision:
    namespace: str
    value_hash: str
    sibling_surface_ids: tuple[str, ...]
    sibling_exposed: bool


@dataclass(frozen=True)
class Familiarity:
    surface_id: str
    purpose: str | None
    exposure_status: str  # 'warm' | 'novel' | 'unknown'
    warmth: float
    hard_collisions: tuple[HardCollision, ...]
    blocks_unseen_claim: bool
    explanation: str
    affects: tuple[str, ...] = AFFECTS

    def as_dict(self) -> dict[str, Any]:
        return {
            "surface_id": self.surface_id,
            "purpose": self.purpose,
            "exposure_status": self.exposure_status,
            "warmth": self.warmth,
            "hard_collisions": [
                {
                    "namespace": c.namespace,
                    "value_hash": c.value_hash,
                    "sibling_surface_ids": list(c.sibling_surface_ids),
                    "sibling_exposed": c.sibling_exposed,
                }
                for c in self.hard_collisions
            ],
            "blocks_unseen_claim": self.blocks_unseen_claim,
            "explanation": self.explanation,
            "affects": list(self.affects),
        }


def _surface_exposed(repository: Repository, surface_id: str) -> bool:
    for event in repository.activity_exposure_events_for_surface(surface_id):
        if event["kind"] in _EXPOSURE_KINDS:
            return True
    return False


def familiarity_projection_v1(
    repository: Repository,
    *,
    surface_id: str,
    purpose: str | None = None,
) -> Familiarity:
    """The P1 named familiarity projection (§4.2).

    - reads exposure UNION namespaced memberships (never first-field-wins);
    - a hard collision (exact ``surface_hash`` or any policy-declared hard group)
      whose sibling has been exposed BLOCKS an unseen/independent claim (§4.1);
    - a surface with NO recorded fingerprint memberships is ``unknown``, never
      ``novel`` (§4.1);
    - warmth is the monotone soft-kinship score (§4.2).
    """

    memberships = repository.fingerprint_memberships_for_surface(surface_id)
    hard_collisions: list[HardCollision] = []
    any_sibling_exposed = False
    for membership in memberships:
        namespace = membership["namespace"]
        if namespace not in HARD_NAMESPACES:
            continue
        siblings = repository.surfaces_sharing_membership(
            namespace=namespace, value_hash=membership["value_hash"], exclude_surface_id=surface_id
        )
        sibling_exposed = any(_surface_exposed(repository, sid) for sid in siblings)
        any_sibling_exposed = any_sibling_exposed or sibling_exposed
        if siblings:
            hard_collisions.append(
                HardCollision(
                    namespace=namespace,
                    value_hash=membership["value_hash"],
                    sibling_surface_ids=tuple(siblings),
                    sibling_exposed=sibling_exposed,
                )
            )

    self_exposed = _surface_exposed(repository, surface_id)

    if not memberships:
        exposure_status = "unknown"  # §4.1: never infer 'novel' from a missing fingerprint
    elif self_exposed or any_sibling_exposed:
        exposure_status = "warm"
    else:
        exposure_status = "novel"

    features_row = repository.soft_kinship_features_for_surface(
        surface_id=surface_id, feature_schema_version=FEATURE_SCHEMA_VERSION
    )
    if features_row is not None:
        import json as _json_mod

        warmth = warmth_score(_json_mod.loads(features_row["features_json"]))
    else:
        warmth = 0.0

    # A hard collision with an EXPOSED sibling (or self already exposed) blocks an
    # unseen/independent claim; an unexposed hard sibling does not by itself.
    blocks_unseen_claim = self_exposed or any_sibling_exposed

    if exposure_status == "unknown":
        explanation = "no fingerprint recorded for this surface; familiarity is unknown, not novel"
    elif exposure_status == "warm":
        parts = []
        if self_exposed:
            parts.append("this exact surface was already shown")
        if any_sibling_exposed:
            parts.append("a hard-correlated sibling surface was already shown")
        explanation = "warm: " + "; ".join(parts)
    else:
        explanation = "novel: fingerprinted but neither this surface nor a hard sibling has been shown"

    return Familiarity(
        surface_id=surface_id,
        purpose=purpose,
        exposure_status=exposure_status,
        warmth=warmth,
        hard_collisions=tuple(hard_collisions),
        blocks_unseen_claim=blocks_unseen_claim,
        explanation=explanation,
    )


# ---------------------------------------------------------------------------
# Tutor / reader-dialogue exposure propagation (U-033, §4.1).
# ---------------------------------------------------------------------------

def propagate_tutor_exposure(
    repository: Repository,
    *,
    explanation_fingerprints: Sequence[Mapping[str, Any]],
    plausibly_touched_surface_ids: Sequence[str] = (),
    clock: Clock | None = None,
) -> dict[str, Any]:
    """When an AI explanation is shown, the claims/proof ideas/representations/
    examples it exposed append memberships against their fingerprint groups so a
    near-term surface reusing those cues reads as warm rather than cold (§4.1).

    An explanation that cannot be fingerprinted degrades to ``unknown`` for the
    surfaces it plausibly touched -- never silently ``novel``."""

    recorded: list[str] = []
    for fp in explanation_fingerprints:
        surface_id = fp.get("surface_id")
        if surface_id is None:
            continue
        recorded.extend(
            record_memberships(
                repository,
                surface_id=surface_id,
                memberships=[
                    {
                        "namespace": fp["namespace"],
                        "value_hash": fp["value_hash"],
                        "provenance": "tutor_explanation",
                        "status": "known",
                    }
                ],
                clock=clock,
            )
        )
    degraded: list[str] = []
    for surface_id in plausibly_touched_surface_ids:
        # Cannot be fingerprinted -> mark unknown, never novel.
        repository.record_fingerprint_membership(
            surface_id=surface_id,
            namespace="external_artifact",
            value_hash="tutor_unfingerprintable",
            provenance="tutor_explanation_degraded",
            status="unknown",
            confidence=0.0,
            clock=clock,
        )
        degraded.append(surface_id)
    return {"recorded": recorded, "degraded_to_unknown": degraded}


# ---------------------------------------------------------------------------
# A.4 tight-kinship single-linkage clustering (the evidence-cap grouping).
# ---------------------------------------------------------------------------

def _pairwise_warmth(
    repository: Repository, surface_a: str, surface_b: str
) -> float:
    """Symmetric pairwise warmth between two surfaces from their stored soft features."""

    import json as _json_mod

    def _features(sid: str) -> dict[str, Any]:
        row = repository.soft_kinship_features_for_surface(
            surface_id=sid, feature_schema_version=FEATURE_SCHEMA_VERSION
        )
        return _json_mod.loads(row["features_json"]) if row is not None else {}

    fa, fb = _features(surface_a), _features(surface_b)
    # Pairwise kinship is the SHARED strength: element-wise min over the union
    # (absent feature = 0). Two surfaces are tight kin only when they BOTH strongly
    # exhibit the same kinship feature -- a strong feature on one side alone does not
    # warm the pair. Symmetric and monotone.
    keys = set(fa) | set(fb)
    combined = {k: min(float(fa.get(k, 0.0) or 0.0), float(fb.get(k, 0.0) or 0.0)) for k in keys}
    return warmth_score(combined)


def tight_kinship_clusters(
    repository: Repository,
    *,
    surface_ids: Sequence[str],
    threshold: float | None = None,
) -> list[list[str]]:
    """Single-linkage threshold clustering (A.4). Two surfaces co-cluster iff
    pairwise warmth >= ``threshold`` (default the registered
    ``TIGHT_KINSHIP_THRESHOLD``). Surfaces are iterated in ULID order for
    determinism; the caller scopes ``surface_ids`` to one target x capability x
    angle neighborhood (§4.3). Returns clusters as sorted id lists.
    """

    cut = TIGHT_KINSHIP_THRESHOLD if threshold is None else threshold
    ordered = sorted(surface_ids)
    # Union-find over the neighborhood.
    parent: dict[str, str] = {s: s for s in ordered}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        # Deterministic: smaller ULID becomes the root.
        if ra < rb:
            parent[rb] = ra
        else:
            parent[ra] = rb

    for i, a in enumerate(ordered):
        for b in ordered[i + 1 :]:
            if _pairwise_warmth(repository, a, b) >= cut:
                union(a, b)

    clusters: dict[str, list[str]] = {}
    for s in ordered:
        clusters.setdefault(find(s), []).append(s)
    return [sorted(members) for _, members in sorted(clusters.items())]


@dataclass(frozen=True)
class EvidenceCapGrouping:
    clusters: tuple[tuple[str, ...], ...]
    independent_group_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "clusters": [list(c) for c in self.clusters],
            "independent_group_count": self.independent_group_count,
        }


def evidence_cap_grouping(
    repository: Repository,
    *,
    surface_ids: Sequence[str],
    threshold: float | None = None,
) -> EvidenceCapGrouping:
    """Independent-group count for the family evidence cap (§4.3): one tight
    soft-kinship cluster contributes exactly ONE independent group, no matter how
    many variant surfaces it holds. Additional administrations in a cluster add
    diminishing mass and ZERO new independent-group count."""

    clusters = tight_kinship_clusters(repository, surface_ids=surface_ids, threshold=threshold)
    return EvidenceCapGrouping(
        clusters=tuple(tuple(c) for c in clusters),
        independent_group_count=len(clusters),
    )
