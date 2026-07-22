"""P1 step 8 -- within-family angle progression, family evidence caps, and post-lapse
linked retries (spec_p1_shared_substrate §4.3, §5.4, §5.5; owner decision A.4).

Three concerns:

  * **Orthogonal-next angle progression** (§5.4). After success the next growth
    activity is a *delayed orthogonal angle*, never a near-clone while the answer is
    in working memory. Context fades ``original -> altered/stripped cold -> source
    restore``. Sibling success-propagation is strongly shrunk and touches ONLY the
    family-stage prior -- it never marks a sibling reviewed or grants its independent
    surface group.
  * **Family evidence cap** (§4.3 + A.4). One family / card lineage / hard group /
    tight soft-kinship cluster cannot mint unbounded independent evidence. The cap
    limits total effective mass per target x capability x angle neighborhood; a
    tight-kinship cluster contributes exactly ONE independent group (via
    ``familiarity.evidence_cap_grouping``) and additional administrations add
    diminishing mass and zero new independent-group count.
  * **Lapse and retry episodes** (§5.5). A failed eligible practice administration
    opens a durable lapse. Same-session retries are linked observations that never
    overwrite the original failure; before ``give_up`` they update a derived
    retrievability but stack no independent evidence or repeated penalty. The launch
    post-lapse follow-up is next day (a registered decision parameter).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.services import familiarity as F
from learnloop.services.activities import _canonical_hash, _json
from learnloop.services.progression_policy import SIBLING_SUCCESS_SHRINKAGE

# §4.3 cap: max total effective independent mass per target x capability x angle
# neighborhood. A registered heuristic decision parameter (calibration deferred).
MAX_EFFECTIVE_MASS_PER_CLUSTER = 3.0  # decision parameter

# §4.3 diminishing returns: each additional administration inside one tight cluster
# contributes decay^k of a unit of mass and zero new independent-group count.
DIMINISHING_MASS_DECAY = 0.5  # decision parameter

# §5.5 / §10 launch post-lapse follow-up cadence (next day), provisional.
POST_LAPSE_FOLLOWUP_DAYS = 1  # decision parameter

DEFAULT_CAP_POLICY_SLUG = "family_evidence_cap_v1"


# ---------------------------------------------------------------------------
# §5.4 orthogonal-next angle progression.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GrowthActivity:
    angle_progression: str
    next_angle: dict[str, Any]
    changed_axis: str | None
    delay_days: int
    context_fade_next: str | None
    is_near_clone: bool
    sibling_propagation: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "angle_progression": self.angle_progression,
            "next_angle": self.next_angle,
            "changed_axis": self.changed_axis,
            "delay_days": self.delay_days,
            "context_fade_next": self.context_fade_next,
            "is_near_clone": self.is_near_clone,
            "sibling_propagation": self.sibling_propagation,
        }


def _next_context(fade: Sequence[str], current: str | None) -> str | None:
    if not fade:
        return None
    if current is None:
        return fade[0]
    if current in fade:
        idx = fade.index(current)
        return fade[idx + 1] if idx + 1 < len(fade) else fade[-1]
    return fade[0]


def _orthogonal_angle(
    coordinates: Mapping[str, Any], current_angle: Mapping[str, Any]
) -> tuple[dict[str, Any], str | None]:
    """Advance ONE orthogonal coordinate deterministically (sorted axis order): pick
    the first axis whose declared values offer something other than the current value,
    and step to the next distinct value. Cosmetic paraphrase stays the same angle."""

    next_angle = dict(current_angle)
    for axis in sorted(coordinates.keys()):
        values = coordinates[axis]
        if not isinstance(values, (list, tuple)) or len(values) < 2:
            continue
        current = current_angle.get(axis)
        if current in values:
            idx = values.index(current)
            candidate = values[(idx + 1) % len(values)]
        else:
            candidate = values[0]
        if candidate != current:
            next_angle[axis] = candidate
            return next_angle, axis
    return next_angle, None


def next_growth_activity(
    repository: Repository,
    *,
    family_version_id: str,
    current_angle: Mapping[str, Any] | None = None,
    current_context: str | None = None,
) -> GrowthActivity:
    """The §5.4 next growth activity after a success: a delayed orthogonal angle (never
    a near-clone), stepping the context fade, with strongly-shrunk sibling propagation
    that only touches the family-stage prior."""

    from learnloop.services.activities import resolve_progression_policy

    policy = resolve_progression_policy(repository, family_version_id) or {}
    delay_days = int(policy.get("orthogonal_next_delay_days", 1))
    fade = policy.get("context_fade") or ["original", "altered_stripped_cold", "source_restore"]
    shrinkage = float(policy.get("sibling_success_shrinkage", SIBLING_SUCCESS_SHRINKAGE))

    inventories = repository.angle_inventories_for_family(family_version_id)
    coordinates: dict[str, Any] = {}
    if inventories:
        import json as _json_mod

        coordinates = _json_mod.loads(inventories[0]["coordinates_json"] or "{}")

    current = dict(current_angle or {})
    next_angle, changed_axis = _orthogonal_angle(coordinates, current)
    is_near_clone = changed_axis is None and next_angle == current

    return GrowthActivity(
        angle_progression=policy.get("angle_progression", "delayed_orthogonal"),
        next_angle=next_angle,
        changed_axis=changed_axis,
        delay_days=delay_days,
        context_fade_next=_next_context(fade, current_context),
        is_near_clone=is_near_clone,
        sibling_propagation={
            "shrinkage": shrinkage,
            "family_stage_prior_only": True,
            "marks_sibling_reviewed": False,
            "grants_independent_group": False,
        },
    )


# ---------------------------------------------------------------------------
# §4.3 family evidence cap (+ A.4 tight-kinship clustering).
# ---------------------------------------------------------------------------

def default_cap_body() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "policy_slug": DEFAULT_CAP_POLICY_SLUG,
        "max_effective_mass_per_cluster": MAX_EFFECTIVE_MASS_PER_CLUSTER,
        "diminishing_mass_decay": DIMINISHING_MASS_DECAY,
        "tight_kinship_threshold": F.TIGHT_KINSHIP_THRESHOLD,
    }


def ensure_default_evidence_cap_policy(
    repository: Repository, *, clock: Clock | None = None
) -> str:
    body = default_cap_body()
    return repository.ensure_family_evidence_cap_policy(
        policy_slug=DEFAULT_CAP_POLICY_SLUG, version=1, caps_json=_json(body),
        content_hash=_canonical_hash(body), clock=clock,
    )


@dataclass(frozen=True)
class EvidenceCap:
    independent_group_count: int
    effective_mass: float
    clusters: tuple[tuple[str, ...], ...]
    capped: bool
    max_effective_mass: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "independent_group_count": self.independent_group_count,
            "effective_mass": self.effective_mass,
            "clusters": [list(c) for c in self.clusters],
            "capped": self.capped,
            "max_effective_mass": self.max_effective_mass,
        }


def apply_evidence_cap(
    repository: Repository,
    *,
    surface_ids: Sequence[str],
    cap_policy_id: str | None = None,
    threshold: float | None = None,
) -> EvidenceCap:
    """Cap independent evidence over a target x capability x angle neighborhood (§4.3).

    Each tight soft-kinship cluster is ONE independent group. Within a cluster the
    first administration contributes a full unit of mass and each subsequent one
    ``decay^k`` (diminishing returns), summed and capped at ``max_effective_mass`` per
    cluster. Total effective mass never exceeds ``clusters x max_effective_mass``.
    """

    decay = DIMINISHING_MASS_DECAY
    max_mass = MAX_EFFECTIVE_MASS_PER_CLUSTER
    if cap_policy_id is not None:
        policy = repository.family_evidence_cap_policy(cap_policy_id)
        if policy is not None:
            import json as _json_mod

            caps = _json_mod.loads(policy["caps_json"] or "{}")
            decay = float(caps.get("diminishing_mass_decay", decay))
            max_mass = float(caps.get("max_effective_mass_per_cluster", max_mass))
            if threshold is None:
                threshold = caps.get("tight_kinship_threshold")

    grouping = F.evidence_cap_grouping(repository, surface_ids=surface_ids, threshold=threshold)
    total_mass = 0.0
    capped = False
    for cluster in grouping.clusters:
        cluster_mass = sum(decay**k for k in range(len(cluster)))
        if cluster_mass >= max_mass:
            cluster_mass = max_mass
            capped = True
        total_mass += cluster_mass
    return EvidenceCap(
        independent_group_count=grouping.independent_group_count,
        effective_mass=total_mass,
        clusters=grouping.clusters,
        capped=capped,
        max_effective_mass=max_mass,
    )


# ---------------------------------------------------------------------------
# §5.5 lapse + linked retry episodes.
# ---------------------------------------------------------------------------

def _plus_days(iso: str, days: int) -> str:
    parsed = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (parsed + timedelta(days=days)).isoformat()


def open_lapse_episode(
    repository: Repository,
    *,
    card_lineage_id: str,
    opened_administration_id: str | None = None,
    learner_id: str = "local",
    followup_days: int | None = None,
    clock: Clock | None = None,
) -> str:
    """Open a durable lapse on a failed eligible practice administration (§5.5). The
    follow-up is next day by default (registered decision parameter), on a
    fresh/orthogonal surface when available."""

    days = POST_LAPSE_FOLLOWUP_DAYS if followup_days is None else followup_days
    now = utc_now_iso(clock)
    return repository.open_lapse_episode(
        card_lineage_id=card_lineage_id,
        opened_administration_id=opened_administration_id,
        learner_id=learner_id,
        followup_due_at=_plus_days(now, days),
        clock=clock,
    )


def link_retry(
    repository: Repository,
    *,
    episode_id: str,
    observation: Mapping[str, Any],
    derived_retrievability: float | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Link a same-session retry to an OPEN lapse (§5.5). Retries are appended, never
    overwriting the original failure; they update a derived retrievability but stack no
    independent evidence or repeated penalty. A no-op on a closed episode."""

    import json as _json_mod

    episode = repository.lapse_episode(episode_id)
    if episode is None:
        raise ValueError(f"unknown lapse episode: {episode_id}")
    if episode["status"] != "open":
        return episode
    retries = _json_mod.loads(episode.get("retry_observations_json") or "[]")
    retries.append(dict(observation))
    repository.update_lapse_episode(
        episode_id=episode_id,
        retry_observations_json=_json(retries),
        derived_retrievability=derived_retrievability,
    )
    return repository.lapse_episode(episode_id)


def give_up(
    repository: Repository, *, episode_id: str, clock: Clock | None = None
) -> dict[str, Any]:
    """Close a lapse as ``given_up`` (§5.5). The original failure and every linked
    retry are preserved."""

    repository.update_lapse_episode(
        episode_id=episode_id, status="given_up", closed_at=utc_now_iso(clock)
    )
    return repository.lapse_episode(episode_id)


def recover(
    repository: Repository, *, episode_id: str, clock: Clock | None = None
) -> dict[str, Any]:
    """Close a lapse as ``recovered`` (the next-day follow-up demonstrated recall)."""

    repository.update_lapse_episode(
        episode_id=episode_id, status="recovered", closed_at=utc_now_iso(clock)
    )
    return repository.lapse_episode(episode_id)
