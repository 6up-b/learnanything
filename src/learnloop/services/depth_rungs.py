"""Depth rungs: waypoint targeting for practice-item generation (spec v2 §4).

Depth is a policy trajectory through capability × task-feature space, not an
enum (spec_new_improvements_v2 §4; spec_p1_shared_substrate §3.1.1/§3.4). The
generation-time unit of that trajectory is a :class:`RungTarget` — one closed-
vocab capability plus one point TaskFeature vector against the ``p1_launch``
schema — sourced from a commitment's next milestone ``task_contract_json`` when
one exists, else from the built-in :data:`DEFAULT_TRAJECTORY`.

Numeric difficulty stays orthogonal: the success-band inversion in
``practice_generation`` calibrates ``difficulty`` WITHIN whichever rung this
module selects. Never encode a rung as a difficulty value.

Everything here is deterministic and fail-closed: a malformed milestone
contract, unknown capability, or schema-invalid vector never guesses — it falls
back to the default trajectory with ``fallback_reason`` set.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from learnloop.db.repositories import Repository
from learnloop.services.activity_patterns import (
    LEGACY_UNMAPPED,
    ensure_builtin_task_feature_schema,
    ensure_capability_alias_registry,
    map_capability,
    validate_task_features,
)
from learnloop.services.synthesis_gates import GateDiagnostic

# Structural pin for the built-in trajectory (audit trail on generated items);
# not a tunable knob.
RUNG_TRAJECTORY_VERSION = "default_trajectory_v1"

TASK_FEATURE_SCHEMA_SLUG = "p1_launch@1"

_SCAFFOLDING_ORDER = ("none", "cue", "partial", "worked")  # index 0 = hardest
_TRANSFER_ORDER = ("same_context", "near", "far", "novel_combination")
_SPAN_ORDER = ("atomic", "single_step", "multi_step", "whole_task")


@dataclass(frozen=True)
class RungTarget:
    waypoint_slug: str
    capability: str
    task_features: dict[str, Any]
    # Per-dimension {"target": value, "max": hardest allowed value}. "max" uses
    # each dimension's hardness direction (complexity/transfer/span: higher is
    # harder; scaffolding: LESS scaffolding is harder).
    task_feature_bounds: dict[str, dict[str, Any]]
    task_feature_schema_version_id: str
    source: str  # "default_trajectory" | "milestone_edge"
    milestone_slug: str | None = None
    edge_id: str | None = None
    envelope_version_id: str | None = None
    fallback_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "waypoint_slug": self.waypoint_slug,
            "capability": self.capability,
            "task_features": dict(self.task_features),
            "task_feature_bounds": {k: dict(v) for k, v in self.task_feature_bounds.items()},
            "task_feature_schema_version_id": self.task_feature_schema_version_id,
            "source": self.source,
            "milestone_slug": self.milestone_slug,
            "edge_id": self.edge_id,
            "envelope_version_id": self.envelope_version_id,
            "fallback_reason": self.fallback_reason,
            "trajectory_version": RUNG_TRAJECTORY_VERSION,
        }


@dataclass(frozen=True)
class Waypoint:
    slug: str
    capability: str
    features: dict[str, Any] = field(default_factory=dict)


# The built-in entry trajectory (Phase-1 waypoint source; a commitment envelope
# supersedes it). Deliberately stops before novel_combination / whole_task /
# coordination: deeper regions require a learner-reviewed depth envelope
# (spec v2 "depth is a learner-authorized program, not a scalar").
DEFAULT_TRAJECTORY: tuple[Waypoint, ...] = (
    Waypoint(
        "recognize",
        "retrieval",
        {"complexity": 0, "transfer": "same_context", "response": "recognize", "scaffolding": "cue", "span": "atomic"},
    ),
    Waypoint(
        "recall",
        "retrieval",
        {"complexity": 1, "transfer": "same_context", "response": "short_constructed", "scaffolding": "none", "span": "atomic"},
    ),
    Waypoint(
        "interpret",
        "schema_interpretation",
        {"complexity": 2, "transfer": "near", "response": "long_constructed", "scaffolding": "none", "span": "single_step"},
    ),
    Waypoint(
        "execute",
        "procedure_execution",
        {"complexity": 2, "transfer": "near", "response": "structured_steps", "scaffolding": "none", "span": "multi_step"},
    ),
    Waypoint(
        "select_method",
        "method_selection",
        {"complexity": 3, "transfer": "far", "response": "short_constructed", "scaffolding": "none", "span": "single_step"},
    ),
)

_WAYPOINT_BY_SLUG = {w.slug: w for w in DEFAULT_TRAJECTORY}


def trajectory_slugs() -> tuple[str, ...]:
    """Ordered waypoint slugs of the built-in trajectory (easiest first)."""

    return tuple(w.slug for w in DEFAULT_TRAJECTORY)


def adjacent_slug(slug: str, direction: str) -> str | None:
    """The waypoint one step easier/harder on the default trajectory, or None
    at the trajectory bounds (deeper than select_method needs an envelope)."""

    slugs = trajectory_slugs()
    if slug not in slugs:
        return None
    index = slugs.index(slug) + (1 if direction == "harder" else -1)
    if index < 0 or index >= len(slugs):
        return None
    return slugs[index]


def waypoint_rung(repository: Repository, slug: str) -> RungTarget:
    """A RungTarget for one default-trajectory waypoint (public seam for
    rung_variants and other callers; keeps them off module-private names)."""

    waypoint = _WAYPOINT_BY_SLUG.get(slug)
    if waypoint is None:
        raise ValueError(f"unknown waypoint slug: {slug!r}")
    return _waypoint_target(waypoint, ensure_builtin_task_feature_schema(repository))


def _default_bounds(features: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Point-target bounds: max equals the target on every declared dimension —
    the generated item may not exceed the waypoint's hardness anywhere."""

    return {dim: {"target": value, "max": value} for dim, value in features.items()}


def _waypoint_target(
    waypoint: Waypoint,
    schema_version_id: str,
    *,
    fallback_reason: str | None = None,
) -> RungTarget:
    return RungTarget(
        waypoint_slug=waypoint.slug,
        capability=waypoint.capability,
        task_features=dict(waypoint.features),
        task_feature_bounds=_default_bounds(waypoint.features),
        task_feature_schema_version_id=schema_version_id,
        source="default_trajectory",
        fallback_reason=fallback_reason,
    )


def select_rung(
    vault,
    repository: Repository,
    *,
    learning_object_id: str,
    mastery_mean: float | None,
    evidence_count: int = 0,
    claimed_level: float | None = None,
    commitment_id: str | None = None,
) -> RungTarget:
    """Pick the generation waypoint for one learning object.

    Commitment path: project the commitment's next reviewed milestone contract.
    Default path: mastery-band keyed entry on :data:`DEFAULT_TRAJECTORY` —
    with zero evidence the learner's claim (already folded into a claim-seeded
    ``mastery_mean``, or passed explicitly) moves the entry point; no signal at
    all starts at ``recognize``.
    """

    schema_version_id = ensure_builtin_task_feature_schema(repository)
    ensure_capability_alias_registry(repository)

    if commitment_id is not None:
        target = _milestone_rung(repository, commitment_id, schema_version_id)
        if target is not None:
            return target
        # _milestone_rung returning None means "malformed/missing" — the default
        # path below is the fail-closed landing zone; reason recorded there.

    # Diagnosed path: a completed probe episode's top hypothesis names the
    # learner's actual gap, which locates the entry rung far better than the
    # scalar mastery band (a "procedure_without_selection" learner belongs at
    # select_method practice even while scalar mastery is still climbing).
    hypothesis_slug = _rung_from_episode_hypothesis(repository, learning_object_id)
    if hypothesis_slug is not None:
        return _waypoint_target(_WAYPOINT_BY_SLUG[hypothesis_slug], schema_version_id)

    ability = mastery_mean if (mastery_mean is not None and evidence_count > 0) else (
        mastery_mean if mastery_mean is not None else claimed_level
    )
    developing = float(vault.config.mastery.display_developing_threshold)
    strong = float(vault.config.mastery.display_strong_threshold)

    # Band-keyed entry with NO evidence-count gates: counts measured exposure,
    # not capability, and pinned claim-seeded learners at the bottom rungs
    # regardless of how their evidence looked (the verified too-easy trap).
    if ability is None or ability < developing:
        slug = "recognize"
    elif ability < strong:
        slug = "recall"
    elif ability >= 0.75:
        slug = "select_method"
    else:
        slug = "interpret"

    reason = "commitment_projection_failed" if commitment_id is not None else None
    return _waypoint_target(_WAYPOINT_BY_SLUG[slug], schema_version_id, fallback_reason=reason)


# Hypothesis label -> the rung whose practice repairs that gap. Labels missing
# here (open-set, dynamic confuses_with:/misconception: labels) fall back to
# the mastery band — a belief fault needs contrast work, not a rung change.
_RUNG_BY_HYPOTHESIS = {
    "unfamiliar": "recognize",
    "surface_only": "recall",
    "recall_without_mechanism": "interpret",
    "procedure_without_selection": "select_method",
    "schema_without_transfer": "execute",
    "robust_initial_grasp": "select_method",
}

_HYPOTHESIS_COMPLETION_REASONS = ("decision_stable", "action_equivalent", "fast_path_strong_claim")


def _rung_from_episode_hypothesis(repository: Repository, learning_object_id: str) -> str | None:
    """Entry slug from the LO's latest trusted completed probe episode, or None."""

    try:
        episode = repository.latest_completed_probe_episode(learning_object_id)
    except AttributeError:
        return None
    if episode is None or episode.get("completion_reason") not in _HYPOTHESIS_COMPLETION_REASONS:
        return None
    top_label = episode.get("top_hypothesis")
    if not top_label:
        return None
    return _RUNG_BY_HYPOTHESIS.get(str(top_label))


def _milestone_rung(
    repository: Repository, commitment_id: str, schema_version_id: str
) -> RungTarget | None:
    """Project the commitment's NEXT milestone into a RungTarget, or None."""

    from learnloop.services import commitments as C

    try:
        head = C.resolve_head(repository, commitment_id)
    except Exception:
        return None
    envelope_version_id = head.depth_envelope_version_id
    if not envelope_version_id:
        return None
    row = repository.depth_envelope_version(envelope_version_id)
    if row is None:
        return None
    try:
        edges = json.loads(row["reviewed_edges_json"] or "[]")
    except (json.JSONDecodeError, TypeError):
        return None
    reviewed = [e for e in edges if isinstance(e, dict) and e.get("reviewed") and e.get("edge_id")]
    if not reviewed:
        return None

    reached = _reached_milestones(repository, commitment_id)
    # Next edge: first reviewed edge whose predecessor is the last reached
    # milestone; with nothing reached, the DAG's first edge.
    if reached:
        edge = next((e for e in reviewed if e.get("predecessor_milestone") == reached[-1]), None)
    else:
        edge = reviewed[0]
    if edge is None:
        return None
    successor = edge.get("successor_milestone")
    if not successor:
        return None
    milestone = repository.depth_milestone_version_for(envelope_version_id, str(successor))
    if milestone is None:
        return None
    try:
        contract = json.loads(milestone["task_contract_json"] or "{}")
    except (json.JSONDecodeError, TypeError):
        return None
    projected = project_task_contract(repository, contract, schema_version_id)
    if projected is None:
        return None
    capability, features, bounds = projected
    return RungTarget(
        waypoint_slug=str(successor),
        capability=capability,
        task_features=features,
        task_feature_bounds=bounds,
        task_feature_schema_version_id=schema_version_id,
        source="milestone_edge",
        milestone_slug=str(successor),
        edge_id=str(edge.get("edge_id")),
        envelope_version_id=envelope_version_id,
    )


def _reached_milestones(repository: Repository, commitment_id: str) -> list[str]:
    reached: list[str] = []
    try:
        events = repository.commitment_events_for(commitment_id)
    except Exception:
        return reached
    for event in events:
        if event.get("kind") != "depth_milestone_reached":
            continue
        payload = event.get("detail_json") or event.get("payload")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                continue
        if isinstance(payload, dict):
            slug = payload.get("milestone_slug") or payload.get("milestone")
            if slug:
                reached.append(str(slug))
    return reached


def project_task_contract(
    repository: Repository, contract: Mapping[str, Any], schema_version_id: str
) -> tuple[str, dict[str, Any], dict[str, dict[str, Any]]] | None:
    """Project a milestone ``task_contract_json`` into (capability, point
    vector, bounds), or None when any piece is malformed (no partial rungs).

    Per-dimension preference: explicit point value in ``task_features`` →
    ``{"target": v}`` in ``task_feature_bounds`` → bare ``{"max": v}`` on an
    ordered dimension takes the deepest allowed value (the milestone's intent is
    its far edge) → anything else refuses the whole projection.
    """

    raw_capability = contract.get("capability")
    if not isinstance(raw_capability, str):
        return None
    capability = map_capability(repository, raw_capability)
    if capability == LEGACY_UNMAPPED:
        return None

    point = contract.get("task_features") if isinstance(contract.get("task_features"), Mapping) else {}
    raw_bounds = (
        contract.get("task_feature_bounds")
        if isinstance(contract.get("task_feature_bounds"), Mapping)
        else {}
    )

    features: dict[str, Any] = {}
    bounds: dict[str, dict[str, Any]] = {}
    for dim in set(point) | set(raw_bounds):
        if dim in point:
            value = point[dim]
            bound_max = raw_bounds.get(dim, {}).get("max") if isinstance(raw_bounds.get(dim), Mapping) else None
            features[dim] = value
            bounds[dim] = {"target": value, "max": bound_max if bound_max is not None else value}
            continue
        spec = raw_bounds.get(dim)
        if not isinstance(spec, Mapping):
            return None
        if "target" in spec:
            features[dim] = spec["target"]
            bounds[dim] = {"target": spec["target"], "max": spec.get("max", spec["target"])}
        elif "max" in spec:
            # Deepest-allowed reading for ordered dimensions only.
            if dim == "complexity":
                features[dim] = spec["max"]
            elif dim == "scaffolding":
                features[dim] = spec["max"]
            elif dim in ("transfer", "span"):
                features[dim] = spec["max"]
            else:
                return None
            bounds[dim] = {"target": features[dim], "max": spec["max"]}
        else:
            return None

    ok, _errors = validate_task_features(repository, schema_version_id, features)
    if not ok:
        return None
    return capability, features, bounds


def rung_float_proxies(rung: RungTarget) -> dict[str, tuple[float, float]]:
    """Legacy float bands consistent with the rung, so the two vocabularies
    (task features vs retrieval_demand/transfer_distance/scaffold_level) cannot
    silently drift. Consumed as prompt guidance and a review-severity tripwire."""

    features = rung.task_features
    proxies: dict[str, tuple[float, float]] = {}

    response = features.get("response")
    scaffolding = features.get("scaffolding")
    if response == "recognize":
        proxies["retrieval_demand"] = (0.0, 0.3)
    elif scaffolding in ("partial", "worked"):
        proxies["retrieval_demand"] = (0.1, 0.5)
    elif scaffolding == "cue":
        proxies["retrieval_demand"] = (0.3, 0.7)
    elif response is not None:
        proxies["retrieval_demand"] = (0.6, 0.95)

    transfer = features.get("transfer")
    transfer_bands = {
        "same_context": (0.0, 0.2),
        "near": (0.2, 0.5),
        "far": (0.5, 0.8),
        "novel_combination": (0.8, 1.0),
    }
    if transfer in transfer_bands:
        proxies["transfer_distance"] = transfer_bands[transfer]

    scaffold_bands = {
        "none": (0.0, 0.15),
        "cue": (0.15, 0.4),
        "partial": (0.4, 0.7),
        "worked": (0.7, 1.0),
    }
    if scaffolding in scaffold_bands:
        proxies["scaffold_level"] = scaffold_bands[scaffolding]

    return proxies


def validate_item_against_rung(
    repository: Repository, *, payload: Mapping[str, Any], rung: RungTarget
) -> list[GateDiagnostic]:
    """Deterministic admission check of one generated-item payload against its
    rung. ``hard_fail`` = the item overshoots or contradicts the authorized
    waypoint; ``review`` = suspicious but salvageable (missing metadata, float
    drift, sideways transfer)."""

    diagnostics: list[GateDiagnostic] = []
    item_ref = str(payload.get("client_item_id") or payload.get("id") or payload.get("title") or "item")

    def diag(severity: str, message: str, action: str) -> None:
        diagnostics.append(
            GateDiagnostic(
                gate="rung_target",
                severity=severity,  # type: ignore[arg-type]
                entity_refs=(item_ref,),
                message=message,
                suggested_action=action,
            )
        )

    capability = payload.get("capability")
    features = payload.get("task_features")
    if not capability or not isinstance(features, Mapping) or not features:
        diag(
            "review",
            "generated item is missing capability/task_features metadata",
            "review the item; regenerate with waypoint metadata",
        )
        return diagnostics

    mapped = map_capability(repository, str(capability))
    if mapped == LEGACY_UNMAPPED:
        diag("hard_fail", f"unknown capability {capability!r}", "use the closed capability vocabulary")
        return diagnostics
    if mapped != rung.capability:
        diag(
            "hard_fail",
            f"capability {mapped!r} does not match the target waypoint capability {rung.capability!r}",
            f"author at the {rung.waypoint_slug} waypoint",
        )

    ok, errors = validate_task_features(repository, rung.task_feature_schema_version_id, features)
    if not ok:
        diag("hard_fail", f"task_features invalid: {'; '.join(errors)}", "emit schema-valid task features")
        return diagnostics

    if mapped == "coordination" and features.get("span") != "whole_task":
        diag(
            "hard_fail",
            "coordination requires span=whole_task",
            "use a whole-task span or a different capability",
        )

    for dim, bound in rung.task_feature_bounds.items():
        if dim not in features:
            continue
        value = features[dim]
        target = bound.get("target")
        limit = bound.get("max", target)
        if dim == "complexity":
            if isinstance(value, int) and isinstance(limit, int) and value > limit:
                diag("hard_fail", f"complexity {value} exceeds the waypoint max {limit}", "reduce complexity")
        elif dim == "scaffolding":
            # Less scaffolding than the target is HARDER than authorized.
            try:
                if _SCAFFOLDING_ORDER.index(str(value)) < _SCAFFOLDING_ORDER.index(str(limit)):
                    diag(
                        "hard_fail",
                        f"scaffolding {value!r} is below the waypoint minimum {limit!r}",
                        "keep the waypoint's scaffolding level",
                    )
                elif value != target:
                    diag("review", f"scaffolding {value!r} differs from target {target!r}", "verify the support level")
            except ValueError:
                pass  # schema validation already flagged unknown values
        elif dim == "transfer":
            try:
                if _TRANSFER_ORDER.index(str(value)) > _TRANSFER_ORDER.index(str(limit)):
                    diag(
                        "hard_fail",
                        f"transfer {value!r} exceeds the waypoint max {limit!r}",
                        "stay within the authorized transfer distance",
                    )
                elif value != target:
                    diag("review", f"transfer {value!r} differs from target {target!r}", "verify transfer distance")
            except ValueError:
                pass
        elif dim in ("response", "span"):
            if value != target:
                diag(
                    "hard_fail",
                    f"{dim} {value!r} does not match the waypoint target {target!r}",
                    f"author a {target} {dim} item",
                )
        elif dim == "representation":
            allowed = set(target or [])
            if allowed and not set(value or []) <= allowed:
                diag(
                    "hard_fail",
                    f"representation {value!r} outside the allowed set {sorted(allowed)}",
                    "use the waypoint's representations",
                )

    for proxy, (low, high) in rung_float_proxies(rung).items():
        declared = payload.get(proxy)
        if declared is None:
            continue
        try:
            declared_value = float(declared)
        except (TypeError, ValueError):
            continue
        if not (low - 1e-9 <= declared_value <= high + 1e-9):
            diag(
                "review",
                f"{proxy}={declared_value} outside the rung band [{low}, {high}]",
                "check the float proxies against the waypoint",
            )

    return diagnostics
