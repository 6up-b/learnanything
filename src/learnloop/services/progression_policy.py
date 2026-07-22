"""P1 step 3 -- the progression-policy object (spec_p1_shared_substrate §3.6;
owner decision A.2).

§3.6 makes ``progression policy`` the third factor of the family construction rule
(``ActivityFamily = commitment target x ActivityPattern version x progression
policy``) but gives no schema. It is distinct from DepthPolicy: DepthPolicy governs
cross-card milestone advancement at the commitment level, while **progression
policy governs within-family card advancement** -- the angle-progression order,
prerequisite evidence per pattern role, orthogonal-next behavior after success,
sibling success-propagation shrinkage, and family-stage prior updates (the objects
§5.4/§5.5 manipulate).

Immutable, content-addressed ``progression_policy_versions``. A family version
references one policy version id; ``resolve_progression_policy`` (in
``services.activities``) reads it.

Decision parameters registered at birth (standing rule 3; see
``services.parameter_registry`` REGISTRY entries) -- their launch defaults seed the
canonical policy body:
  * ``progression_policy:SIBLING_SUCCESS_SHRINKAGE`` (§5.4, family-stage prior only);
  * ``progression_policy:ORTHOGONAL_NEXT_DELAY_DAYS`` (§5.4, delayed-orthogonal cadence).
``PROGRESSION_POLICY_SCHEMA_VERSION`` is a structural version pin, not a knob.
"""

from __future__ import annotations

from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.activities import _canonical_hash, _json

# Structural version pin (enum, not a decision knob -- registered structural).
PROGRESSION_POLICY_SCHEMA_VERSION = 1

# Sibling success-propagation shrinkage (§5.4): success propagates to sibling angles
# strongly shrunk, affecting only the family-stage prior.
SIBLING_SUCCESS_SHRINKAGE = 0.15  # decision parameter

# Delayed-orthogonal cadence (§5.4): after success the next growth activity is a
# delayed orthogonal angle, not a near-clone in working memory.
ORTHOGONAL_NEXT_DELAY_DAYS = 1  # decision parameter

DEFAULT_POLICY_SLUG = "orthogonal_next_v1"


def default_progression_policy_body(policy_slug: str = DEFAULT_POLICY_SLUG) -> dict[str, Any]:
    """The canonical progression-policy body (§5.4/§5.5/§4.3), seeded from the
    registered decision-parameter defaults."""

    return {
        "schema_version": PROGRESSION_POLICY_SCHEMA_VERSION,
        "policy_slug": policy_slug,
        "angle_progression": "delayed_orthogonal",
        "context_fade": ["original", "altered_stripped_cold", "source_restore"],
        "prerequisite_evidence": {},
        "sibling_success_shrinkage": SIBLING_SUCCESS_SHRINKAGE,
        "family_stage_prior_update": "shrunk_blend_v1",
        "post_success_next": "delayed_orthogonal_angle",
        "orthogonal_next_delay_days": ORTHOGONAL_NEXT_DELAY_DAYS,
        "calibration_status": "heuristic",
    }


def register_progression_policy(
    repository: Repository,
    *,
    policy_slug: str,
    body: Mapping[str, Any],
    version: int = PROGRESSION_POLICY_SCHEMA_VERSION,
    clock: Clock | None = None,
) -> str:
    """Register an immutable, content-addressed progression-policy version."""

    canonical = dict(body)
    return repository.ensure_progression_policy_version(
        policy_slug=policy_slug,
        version=version,
        body_json=_json(canonical),
        content_hash=_canonical_hash(canonical),
        clock=clock,
    )


def ensure_default_progression_policy(
    repository: Repository, *, policy_slug: str = DEFAULT_POLICY_SLUG, clock: Clock | None = None
) -> str:
    """Seed / resolve the default progression policy (idempotent)."""

    return register_progression_policy(
        repository, policy_slug=policy_slug, body=default_progression_policy_body(policy_slug),
        clock=clock,
    )


def load_progression_policy(repository: Repository, policy_version_id: str) -> dict[str, Any] | None:
    row = repository.progression_policy_version(policy_version_id)
    if row is None:
        return None
    import json

    return json.loads(row["body_json"])
