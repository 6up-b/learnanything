"""P2 DIAGNOSTIC track -- two-tier failure-reason triage (U-027)
(spec_p2_narrow_golden_path §6.1, §6.2, §12.2; design B.5; migration 083).

After a qualifying miss the run appends a ``failure_triage_event`` over the ten §6.1
reasons via a TWO-TIER mechanism:

- **Tier one** is a DETERMINISTIC route table (registered as DATA in
  ``failure_triage_routes``, not code) applied whenever evidence is decisive --
  ``dont_know`` on never-exposed content, a quarantined grade, an expired memory trace,
  or a high-confidence unambiguous error signature. A decisive route drives the run
  state machine into the ladder entry stage the route names.
- **Tier two** is a provisional distribution over the reasons, emitted from the P0
  grading pass + error-taxonomy firing and presented as a DECISION AID with named
  alternatives. It is NEVER silently applied to a consequential transition -- the run
  waits for a learner/owner ``decide`` (or ``override``).

Learner/owner overrides of either tier are logged as ADJUDICATION ANCHORS into the
U-020 calibration stream (``learner_clarification`` bounded trust). The triage channel
is registered ``heuristic`` in the P0 decision-parameter registry so misroutes are
discoverable rather than ambient. Every triage decision is an append-only row logging
its trace (evaluated goal-contract head, route id or distribution, override if any).

The route is snapshotted here BEFORE any tutor prose is generated -- prose can never
change the action, target, scaffold level, reveal budget, or follow-up contract (§6.2).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services import calibration_streams as CS
from learnloop.services import golden_path_run as GPR
from learnloop.services.activities import _json

# ``version`` parameter: route-table schema. Registered structural in the P0 registry.
TRIAGE_ROUTES_SCHEMA_VERSION = 1

# decision parameter -- grader-confidence bucket edges (low | mid | high). A tier-one
# signature route fires only in the HIGH bucket (>= the top edge); otherwise tier two
# applies. Registered heuristic in the P0 decision-parameter registry (design §E).
TRIAGE_CONFIDENCE_BUCKET_EDGES = (0.5, 0.85)

# decision parameter (owner-flagged default, PENDING OWNER CONFIRMATION -- §14 change
# log) -- the minimum share of the provisional reason distribution that ONE signature
# must carry for the high-confidence error-signature route to stay tier-one. The spec's
# three decisive triggers (quarantine, dont_know-on-never-exposed, expired-trace) always
# auto-commit; the signature route additionally requires a CONCENTRATED distribution --
# a single dominant signature carrying >= this share -- otherwise it downgrades to a
# tier-two decision aid. Registered heuristic in the P0 decision-parameter registry.
TRIAGE_DOMINANCE_SHARE = 0.75

# The ten §6.1 reasons (strings -> not a numeric registry constant).
TRIAGE_REASONS: tuple[str, ...] = (
    "memory_lapse",
    "unfamiliar_or_missing_knowledge",
    "schema_or_conceptual_hole",
    "false_belief_or_confusion",
    "procedure_execution",
    "method_selection",
    "coordination_or_integration",
    "task_interpretation",
    "surface_or_grading_fault",
    "unknown_or_ambiguous",
)

# Built-in error-signature -> reason map. The reviewed blueprint's own
# ``failure_signature_triage`` map is merged on top of this (blueprint has authority).
_SIGNATURE_REASON_MAP: dict[str, str] = {
    "wrong_method": "method_selection",
    "execution_error": "procedure_execution",
    "schema_gap": "schema_or_conceptual_hole",
    "conceptual_hole": "schema_or_conceptual_hole",
    "misconception": "false_belief_or_confusion",
    "false_belief": "false_belief_or_confusion",
    "integration_gap": "coordination_or_integration",
    "coordination_gap": "coordination_or_integration",
    "task_misread": "task_interpretation",
}


class TriageError(Exception):
    """A triage action references an unknown run/event or an unknown reason."""


@dataclass(frozen=True)
class TriageResult:
    run_id: str
    event_id: str
    kind: str
    tier: str
    decisive: bool
    reason: str | None
    route: dict[str, Any] | None
    distribution: dict[str, float] | None
    alternatives: tuple[dict[str, Any], ...]
    routed: bool
    routed_to: str | None
    auto_committed: bool
    anchor_sample_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["alternatives"] = [dict(a) for a in self.alternatives]
        return data


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def _confidence_bucket(confidence: float) -> str:
    lo, hi = TRIAGE_CONFIDENCE_BUCKET_EDGES
    if confidence >= hi:
        return "high"
    if confidence >= lo:
        return "mid"
    return "low"


def _blueprint_signature_map(repository: Repository, run: Mapping[str, Any]) -> dict[str, str]:
    version = repository.task_blueprint_version(run["blueprint_version_id"])
    if version is None:
        return {}
    import json as _json_mod

    spec = _json_mod.loads(version["spec_json"])
    out = {str(k): str(v) for k, v in (spec.get("failure_signature_triage") or {}).items()}
    return out


def _decisive_reason(
    inputs: Mapping[str, Any],
    signature_map: Mapping[str, str],
    *,
    distribution: Mapping[str, float] | None = None,
) -> str | None:
    """Tier-one decisive route (§6.1). Returns a reason when evidence is decisive,
    else None (tier two applies).

    The spec's THREE decisive triggers -- a quarantined surface, ``dont_know`` on
    never-exposed content, an expired memory trace -- always auto-commit. The
    high-confidence error-signature route is narrower (C3 owner-flagged default): it
    stays tier-one only when the reason distribution is CONCENTRATED on a single
    dominant signature (the mapped reason carries >= ``TRIAGE_DOMINANCE_SHARE`` of the
    mass); a diffuse distribution downgrades it to a tier-two decision aid."""

    # A bad/quarantined surface is NEVER a learner deficit -- decisive fault route.
    if inputs.get("surface_validity") == "quarantined":
        return "surface_or_grading_fault"
    # `dont_know` on never-exposed content -> unfamiliar/missing (decisive).
    if inputs.get("coarse_class") == "dont_know" and inputs.get("exposure_history") == "never_exposed":
        return "unfamiliar_or_missing_knowledge"
    # An expired memory trace -> memory lapse (decisive).
    if inputs.get("memory_trace") == "expired":
        return "memory_lapse"
    # A high-confidence, unambiguous error signature routes deterministically ONLY when
    # a single dominant signature owns the distribution mass (C3); otherwise tier two.
    signature = inputs.get("error_signature")
    if signature and _confidence_bucket(float(inputs.get("grader_confidence", 0.0))) == "high":
        merged = {**_SIGNATURE_REASON_MAP, **dict(signature_map)}
        reason = merged.get(str(signature))
        if reason in TRIAGE_REASONS and _signature_is_dominant(reason, distribution):
            return reason
    return None


def _supplied_distribution(inputs: Mapping[str, Any]) -> dict[str, float] | None:
    """The P0-supplied provisional distribution filtered to the ten reasons, or None
    when the grading pass supplied none. Only a supplied distribution can DIFFUSE the
    signature route to tier two (C3)."""

    supplied = inputs.get("provisional_distribution")
    if not isinstance(supplied, Mapping) or not supplied:
        return None
    filtered = {
        str(k): float(v)
        for k, v in supplied.items()
        if str(k) in TRIAGE_REASONS and float(v) > 0
    }
    return filtered or None


def _signature_is_dominant(reason: str, distribution: Mapping[str, float] | None) -> bool:
    """True when ``reason`` owns a dominant share of the provisional distribution mass
    (>= ``TRIAGE_DOMINANCE_SHARE``) and is the argmax (C3). With no distribution the
    route falls back to dominant (a bare high-confidence signature with no competing
    mass is treated as concentrated)."""

    if not distribution:
        return True
    total = sum(float(v) for v in distribution.values())
    if total <= 0:
        return True
    share = float(distribution.get(reason, 0.0)) / total
    if share < TRIAGE_DOMINANCE_SHARE:
        return False
    return reason == _recommended_reason(distribution)


def _provisional_distribution(inputs: Mapping[str, Any], signature_map: Mapping[str, str]) -> dict[str, float]:
    """Tier-two provisional distribution over reasons (§6.1). Uses the P0 grading pass'
    supplied distribution when present; otherwise derives a bounded fallback that
    concentrates on the signature-mapped reason and spreads the remainder to
    ``unknown_or_ambiguous``."""

    supplied = inputs.get("provisional_distribution")
    if isinstance(supplied, Mapping) and supplied:
        dist = {str(k): float(v) for k, v in supplied.items() if str(k) in TRIAGE_REASONS}
        total = sum(dist.values())
        if total > 0:
            return {k: v / total for k, v in dist.items()}

    signature = inputs.get("error_signature")
    merged = {**_SIGNATURE_REASON_MAP, **dict(signature_map)}
    reason = merged.get(str(signature)) if signature else None
    if reason in TRIAGE_REASONS:
        # Ambiguous but leaning: majority on the leaning reason, remainder unknown.
        return {reason: 0.6, "unknown_or_ambiguous": 0.4}
    return {"unknown_or_ambiguous": 1.0}


def _recommended_reason(distribution: Mapping[str, float]) -> str:
    return max(distribution.items(), key=lambda kv: (kv[1], kv[0]))[0]


def _route_summary(route: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if route is None:
        return None
    return {
        "route_id": route["route_id"],
        "reason": route["reason"],
        "first_intervention": route["first_intervention"],
        "cold_follow_up": route["cold_follow_up"],
        "ladder_entry_stage": route["ladder_entry_stage"],
        "reopens_diagnostic": bool(route["reopens_diagnostic"]),
    }


def _alternatives(repository: Repository, distribution: Mapping[str, float], *, top_k: int = 3) -> list[dict[str, Any]]:
    ranked = sorted(distribution.items(), key=lambda kv: (-kv[1], kv[0]))[:top_k]
    out: list[dict[str, Any]] = []
    for reason, weight in ranked:
        out.append(
            {
                "reason": reason,
                "weight": round(float(weight), 6),
                "route": _route_summary(repository.failure_triage_route_for_reason(reason)),
            }
        )
    return out


def _goal_contract_head(repository: Repository, run: Mapping[str, Any]) -> str | None:
    head = repository.fetch_goal_contract_head(run["goal_id"])
    return head["head_version_id"] if head else None


def _route_run(
    repository: Repository,
    run_id: str,
    reason: str,
    route: Mapping[str, Any],
    *,
    idempotency_key: str,
    clock: Clock | None,
) -> tuple[bool, str | None]:
    """Advance the run into the ladder entry stage the route names -- but only from
    the ``triaging`` gate, so triage stays usable diagnostically outside the run's
    happy path without forcing an illegal transition."""

    state = GPR.project_run(repository, run_id)
    if state.current_state != "triaging":
        return False, None
    target = route["ladder_entry_stage"]
    GPR.advance(
        repository,
        run_id,
        to_state=target,
        reason=f"triage_route:{reason}",
        idempotency_key=idempotency_key,
        clock=clock,
    )
    return True, target


def triage(
    repository: Repository,
    run_id: str,
    *,
    attempt: Mapping[str, Any],
    routing_prior: Mapping[str, Any] | None = None,
    idempotency_key: str | None = None,
    clock: Clock | None = None,
) -> TriageResult:
    """Produce a triage record for a qualifying miss (§6.1). Tier one (decisive) routes
    the run; tier two returns a decision aid and does NOT commit any transition.

    ``attempt`` carries the §6.1 inputs snapshot: ``coarse_class``, ``error_signature``,
    ``grader_confidence``, ``exposure_history``, ``surface_validity``, ``memory_trace``,
    ``assistance``, ``misconception_history``, ``committed_response``, and an optional P0
    ``provisional_distribution``. ``routing_prior`` (A.1, reader track) is recorded as a
    labeled ``heuristic`` input in the trace only, superseded by the first cold obs.
    """

    run = repository.golden_path_run(run_id)
    if run is None:
        raise TriageError(f"unknown golden-path run: {run_id}")

    attempt_id = attempt.get("attempt_id")
    signature_map = _blueprint_signature_map(repository, run)
    gc_head = _goal_contract_head(repository, run)

    # C3 dominance gate reads the P0-SUPPLIED provisional distribution only: a bare
    # high-confidence unambiguous signature (no supplied distribution) is itself a
    # concentrated signal and stays tier-one; only an explicitly DIFFUSE supplied
    # distribution downgrades the signature route to a tier-two decision aid.
    supplied_distribution = _supplied_distribution(attempt)
    # C7: a retried triage() for the same attempt dedupes on this ledger key.
    triage_event_key = f"triage:{attempt_id}" if attempt_id is not None else None
    decisive_reason = _decisive_reason(attempt, signature_map, distribution=supplied_distribution)
    if decisive_reason is not None:
        route = repository.failure_triage_route_for_reason(decisive_reason)
        if route is None:  # pragma: no cover - seeded routes always exist
            raise TriageError(f"no route for reason {decisive_reason!r}")
        event = repository.append_failure_triage_event(
            run_id=run_id,
            kind="triaged",
            tier="one",
            decisive=True,
            attempt_id=attempt_id,
            route_id=route["route_id"],
            selected_reason=decisive_reason,
            inputs_snapshot_json=_json(dict(attempt)),
            routing_prior_json=_json(dict(routing_prior)) if routing_prior else None,
            auto_committed=True,
            goal_contract_head_version_id=gc_head,
            idempotency_key=triage_event_key,
            clock=clock,
        )
        routed, routed_to = _route_run(
            repository,
            run_id,
            decisive_reason,
            route,
            idempotency_key=idempotency_key or f"triage-route:{event['id']}",
            clock=clock,
        )
        return TriageResult(
            run_id=run_id,
            event_id=event["id"],
            kind="triaged",
            tier="one",
            decisive=True,
            reason=decisive_reason,
            route=_route_summary(route),
            distribution=None,
            alternatives=(),
            routed=routed,
            routed_to=routed_to,
            auto_committed=True,
        )

    # Tier two: provisional distribution presented as a decision aid -- NOT committed.
    distribution = _provisional_distribution(attempt, signature_map)
    recommended = _recommended_reason(distribution)
    alternatives = _alternatives(repository, distribution)
    event = repository.append_failure_triage_event(
        run_id=run_id,
        kind="triaged",
        tier="two",
        decisive=False,
        attempt_id=attempt_id,
        route_id=None,
        selected_reason=recommended,
        distribution_json=_json(distribution),
        alternatives_json=_json(alternatives),
        inputs_snapshot_json=_json(dict(attempt)),
        routing_prior_json=_json(dict(routing_prior)) if routing_prior else None,
        auto_committed=False,
        goal_contract_head_version_id=gc_head,
        idempotency_key=triage_event_key,
        clock=clock,
    )
    return TriageResult(
        run_id=run_id,
        event_id=event["id"],
        kind="triaged",
        tier="two",
        decisive=False,
        reason=recommended,
        route=_route_summary(repository.failure_triage_route_for_reason(recommended)),
        distribution=distribution,
        alternatives=tuple(alternatives),
        routed=False,
        routed_to=None,
        auto_committed=False,
    )


def _log_adjudication_anchor(
    repository: Repository,
    *,
    run: Mapping[str, Any],
    attempt_id: str | None,
    actor: str,
    chosen_reason: str,
    prior_reason: str | None,
    clock: Clock | None,
) -> str:
    """Log a learner/owner override as an adjudication anchor into the U-020 calibration
    stream (P0.2 machinery). ``learner_clarification`` is bounded-trust: an
    authority-grade single datapoint, never a calibration denominator beyond its weight."""

    # raw_grade_event_id is left NULL: the P2 triage attempt snapshot is not always a
    # persisted grade-event row, and the anchor's identity is the run + chosen reason
    # carried in the stratum. (Linking a non-existent grade event would violate the
    # calibration-sample FK.)
    return CS.record_adjudicated_anchor_sample(
        repository,
        observation_id=None,
        administration_id=None,
        raw_grade_event_id=None,
        stratum={
            "source": "triage_override",
            "actor": actor,
            "trust": "learner_clarification",
            "run_id": run["id"],
            "attempt_id": attempt_id,
            "chosen_reason": chosen_reason,
            "prior_reason": prior_reason,
        },
        clock=clock,
    )


def decide(
    repository: Repository,
    run_id: str,
    *,
    triage_event_id: str,
    chosen_reason: str,
    actor: str = "learner",
    idempotency_key: str | None = None,
    clock: Clock | None = None,
) -> TriageResult:
    """Commit a tier-two decision aid by selecting a named alternative (§6.1). Routes
    the run into the chosen reason's ladder stage. If the pick diverges from the aid's
    recommended reason it is an implicit override -> an adjudication anchor is logged."""

    if chosen_reason not in TRIAGE_REASONS:
        raise TriageError(f"unknown triage reason: {chosen_reason!r}")
    run = repository.golden_path_run(run_id)
    if run is None:
        raise TriageError(f"unknown golden-path run: {run_id}")
    prior = repository.failure_triage_event(triage_event_id)
    if prior is None or prior["run_id"] != run_id:
        raise TriageError(f"unknown triage event: {triage_event_id!r}")

    route = repository.failure_triage_route_for_reason(chosen_reason)
    recommended = prior.get("selected_reason")
    diverged = recommended is not None and chosen_reason != recommended
    anchor_id = None
    if diverged:
        anchor_id = _log_adjudication_anchor(
            repository, run=run, attempt_id=prior.get("attempt_id"), actor=actor,
            chosen_reason=chosen_reason, prior_reason=recommended, clock=clock,
        )

    event = repository.append_failure_triage_event(
        run_id=run_id,
        kind="decided",
        tier="two",
        decisive=False,
        attempt_id=prior.get("attempt_id"),
        route_id=route["route_id"] if route else None,
        selected_reason=chosen_reason,
        override_actor=actor if diverged else None,
        override_reason="diverged_from_recommendation" if diverged else None,
        anchor_sample_id=anchor_id,
        inputs_snapshot_json=prior.get("inputs_snapshot_json"),
        auto_committed=False,
        goal_contract_head_version_id=_goal_contract_head(repository, run),
        clock=clock,
    )
    routed, routed_to = _route_run(
        repository, run_id, chosen_reason, route,
        idempotency_key=idempotency_key or f"triage-decide:{event['id']}", clock=clock,
    ) if route else (False, None)
    return TriageResult(
        run_id=run_id,
        event_id=event["id"],
        kind="decided",
        tier="two",
        decisive=False,
        reason=chosen_reason,
        route=_route_summary(route),
        distribution=None,
        alternatives=(),
        routed=routed,
        routed_to=routed_to,
        auto_committed=False,
        anchor_sample_id=anchor_id,
    )


def override(
    repository: Repository,
    run_id: str,
    *,
    triage_event_id: str,
    chosen_reason: str,
    actor: str = "owner",
    idempotency_key: str | None = None,
    clock: Clock | None = None,
) -> TriageResult:
    """Explicitly override any triage outcome (a decisive tier-one route or a tier-two
    recommendation) with a corrected reason (§6.1). ALWAYS logs an adjudication anchor.
    Routes the run to the corrected reason's stage when still at the ``triaging`` gate;
    a run that already routed keeps the override in the audit trace + calibration stream
    (the correction applies to the next decision), never forcing an illegal transition."""

    if chosen_reason not in TRIAGE_REASONS:
        raise TriageError(f"unknown triage reason: {chosen_reason!r}")
    run = repository.golden_path_run(run_id)
    if run is None:
        raise TriageError(f"unknown golden-path run: {run_id}")
    prior = repository.failure_triage_event(triage_event_id)
    if prior is None or prior["run_id"] != run_id:
        raise TriageError(f"unknown triage event: {triage_event_id!r}")

    route = repository.failure_triage_route_for_reason(chosen_reason)
    anchor_id = _log_adjudication_anchor(
        repository, run=run, attempt_id=prior.get("attempt_id"), actor=actor,
        chosen_reason=chosen_reason, prior_reason=prior.get("selected_reason"), clock=clock,
    )
    event = repository.append_failure_triage_event(
        run_id=run_id,
        kind="overridden",
        tier=prior["tier"],
        decisive=bool(prior["decisive"]),
        attempt_id=prior.get("attempt_id"),
        route_id=route["route_id"] if route else None,
        selected_reason=chosen_reason,
        override_actor=actor,
        override_reason="explicit_override",
        anchor_sample_id=anchor_id,
        inputs_snapshot_json=prior.get("inputs_snapshot_json"),
        auto_committed=False,
        goal_contract_head_version_id=_goal_contract_head(repository, run),
        clock=clock,
    )
    routed, routed_to = _route_run(
        repository, run_id, chosen_reason, route,
        idempotency_key=idempotency_key or f"triage-override:{event['id']}", clock=clock,
    ) if route else (False, None)
    return TriageResult(
        run_id=run_id,
        event_id=event["id"],
        kind="overridden",
        tier=prior["tier"],
        decisive=bool(prior["decisive"]),
        reason=chosen_reason,
        route=_route_summary(route),
        distribution=None,
        alternatives=(),
        routed=routed,
        routed_to=routed_to,
        auto_committed=False,
        anchor_sample_id=anchor_id,
    )


def triage_status(repository: Repository, run_id: str) -> dict[str, Any]:
    """The current triage state + full append-only trace for a run (§6.1 audit)."""

    run = repository.golden_path_run(run_id)
    if run is None:
        raise TriageError(f"unknown golden-path run: {run_id}")
    events = repository.failure_triage_events_for(run_id)
    trace: list[dict[str, Any]] = []
    for e in events:
        import json as _json_mod

        trace.append(
            {
                "event_id": e["id"],
                "seq": e["seq"],
                "kind": e["kind"],
                "tier": e["tier"],
                "decisive": bool(e["decisive"]),
                "route_id": e["route_id"],
                "selected_reason": e["selected_reason"],
                "distribution": _json_mod.loads(e["distribution_json"]) if e["distribution_json"] else None,
                "override_actor": e["override_actor"],
                "anchor_sample_id": e["anchor_sample_id"],
                "goal_contract_head_version_id": e["goal_contract_head_version_id"],
            }
        )
    latest = trace[-1] if trace else None
    return {"run_id": run_id, "latest": latest, "trace": trace}
