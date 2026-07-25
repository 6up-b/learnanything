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

**P2 causal support is an AND gate, not a replacement** (spec_causal_attribution_v1 §2).
A P2 diagnosis receipt may VETO or downgrade the legacy high-confidence signature route
freely, but it may only PROMOTE an attempt to tier one under an APPROVED support
authority (``causal_attribution.APPROVED_SUPPORT_AUTHORITIES``). A single-attempt
receipt carries ``support_authority="unavailable_single_attempt"`` and all-``None``
support scores by design -- a model-reported number on one attempt never earns
deterministic routing, and equally must never silently disable the legacy route. The
arm that fired is recorded as ``tier_one_basis`` on the result and in the event payload.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services import calibration_streams as CS
from learnloop.services import golden_path_run as GPR
from learnloop.services.activities import _json
from learnloop.services.causal_attribution import (
    APPROVED_SUPPORT_AUTHORITIES,
    OPEN_SET_CAUSE_ID,
    receipt_trace_consistency,
)

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

# The residual reason bucket. Unmapped hypotheses, open-set / ``H_OTHER`` mass, and any
# hypothesis whose signature does not resolve to one of the ten reasons land here. It is
# NEVER renormalized away: the learner-facing decision aid has to see how much of the
# causal mass the diagnosis could not place.
UNKNOWN_REASON = "unknown_or_ambiguous"

# Per-hypothesis trace-consistency states (spec_causal_attribution_v1 §5.6). Only
# ``consistent_with_claims`` is positive evidence; ``no_deterministic_claims`` is absence
# of evidence and ``unknown`` is missing instrumentation -- neither corroborates.
TRACE_CONSISTENCY_STATES: frozenset[str] = frozenset(
    {
        "contradicted",
        "consistent_with_claims",
        "no_deterministic_claims",
        "unknown",
    }
)

# ``tier_one_basis`` vocabulary -- which arm of the §2.1 gate committed the route.
# ``deterministic_trigger`` covers the three spec triggers (quarantine, dont_know on
# never-exposed content, expired trace) which are decisive independently of both the
# grader-confidence bucket and the causal channel.
TIER_ONE_BASIS_DETERMINISTIC = "deterministic_trigger"
TIER_ONE_BASIS_LEGACY = "legacy_dominance"
TIER_ONE_BASIS_CAUSAL = "causal_authority"


class TriageError(Exception):
    """A triage action references an unknown run/event or an unknown reason."""


@dataclass(frozen=True)
class CausalSupportNormalization:
    """One normalization of a P2 diagnosis receipt's causal support, shared by the
    tier-one gate and the tier-two provisional distribution (contract §2).

    ``by_reason`` holds fractions of TOTAL mass -- mapped reasons PLUS the residual
    ``unknown_or_ambiguous`` bucket -- so dominance can never be manufactured by
    dropping rows the diagnosis failed to place. ``dominant_share`` is the largest
    share observed even when ``dominant_reason`` is None (tie, or the residual bucket
    won); the gate only ever reads the two together.
    """

    by_reason: dict[str, float]
    total_mass: float
    incomplete: bool
    authority_approved: bool
    dominant_reason: str | None
    dominant_share: float
    trace_states: dict[str, str]


def _causal_rows(
    causal_support: Mapping[str, Any] | None,
) -> list[Mapping[str, Any]]:
    return [
        value
        for value in (causal_support or {}).get("hypotheses") or []
        if isinstance(value, Mapping)
    ]


def _is_open_set(row: Mapping[str, Any]) -> bool:
    # ``open_set`` is the load-bearing flag; the id check catches a pre-P1 row
    # that carries the placeholder without the flag. It compares against the
    # constant that ``canonical_projection`` actually writes -- NOT
    # ``probe_hypotheses.H_OTHER``, which is a probe-set label in a different
    # namespace and could never match a cause row.
    return (
        bool(row.get("open_set"))
        or str(row.get("hypothesis_id")) == OPEN_SET_CAUSE_ID
    )


def normalize_causal_support(
    causal_support: Mapping[str, Any] | None,
) -> CausalSupportNormalization:
    """Normalize a causal-support snapshot into action-relative reason mass.

    Rules (contract §2):

    - ALL nonnegative support mass is preserved. A negative score is clamped to 0 and
      flags ``incomplete`` -- it is a malformed channel, not evidence.
    - Mapped hypotheses aggregate BY TRIAGE REASON: two hypotheses that imply the same
      repair ADD, because P2 routing is action-relative, not hypothesis-relative.
    - Unmapped / open-set / ``H_OTHER`` mass goes to ``unknown_or_ambiguous`` and stays
      in the denominator.
    - A concrete hypothesis with a missing or non-numeric score sets ``incomplete``,
      which forbids tier-one promotion. Open-set rows legitimately carry no score.
    """

    rows = _causal_rows(causal_support)
    authority = (causal_support or {}).get("support_authority")
    authority_approved = (
        isinstance(authority, str) and authority in APPROVED_SUPPORT_AUTHORITIES
    )

    mass: dict[str, float] = {UNKNOWN_REASON: 0.0}
    trace_states: dict[str, str] = {}
    incomplete = False
    for row in rows:
        hypothesis_id = str(row.get("hypothesis_id") or "")
        state = row.get("trace_consistency")
        if hypothesis_id:
            trace_states[hypothesis_id] = (
                state
                if isinstance(state, str) and state in TRACE_CONSISTENCY_STATES
                else "unknown"
            )
        open_set = _is_open_set(row)
        raw = row.get("support_score")
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            score = 0.0
            if not open_set:
                incomplete = True
        else:
            score = float(raw)
            if score != score or score in (float("inf"), float("-inf")):
                score = 0.0
                incomplete = True
            elif score < 0:
                score = 0.0
                incomplete = True
        reason = row.get("triage_reason")
        bucket = (
            str(reason)
            if not open_set
            and isinstance(reason, str)
            and reason in TRIAGE_REASONS
            else UNKNOWN_REASON
        )
        mass[bucket] = mass.get(bucket, 0.0) + score

    total = sum(mass.values())
    if total <= 0:
        return CausalSupportNormalization(
            by_reason={UNKNOWN_REASON: 0.0},
            total_mass=0.0,
            incomplete=incomplete,
            authority_approved=authority_approved,
            dominant_reason=None,
            dominant_share=0.0,
            trace_states=trace_states,
        )

    by_reason = {key: value / total for key, value in mass.items()}
    ranked = sorted(by_reason.items(), key=lambda kv: (-kv[1], kv[0]))
    top_reason, top_share = ranked[0]
    dominant: str | None = top_reason
    if len(ranked) > 1 and ranked[1][1] == top_share:
        dominant = None  # a tie names no dominant cause
    if dominant == UNKNOWN_REASON:
        dominant = None  # the residual bucket never routes
    return CausalSupportNormalization(
        by_reason=by_reason,
        total_mass=total,
        incomplete=incomplete,
        authority_approved=authority_approved,
        dominant_reason=dominant,
        dominant_share=top_share,
        trace_states=trace_states,
    )


def _reason_trace_state(
    causal_support: Mapping[str, Any] | None, reason: str
) -> str | None:
    """Collapse the per-hypothesis trace-consistency states of every concrete hypothesis
    mapping to ``reason`` (§5.6). ``None`` when no hypothesis maps to the reason at all.

    Any contradiction wins (the veto is cheap and must fire on partial evidence); only a
    unanimous ``consistent_with_claims`` counts as corroboration."""

    states = [
        str(row.get("trace_consistency") or "unknown")
        for row in _causal_rows(causal_support)
        if not _is_open_set(row) and row.get("triage_reason") == reason
    ]
    if not states:
        return None
    if "contradicted" in states:
        return "contradicted"
    if all(state == "consistent_with_claims" for state in states):
        return "consistent_with_claims"
    if "unknown" in states:
        return "unknown"
    return "no_deterministic_claims"


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
    # Which arm of the §2.1 tier-one gate fired; None for tier two.
    tier_one_basis: str | None = None

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


def _decisive_route(
    inputs: Mapping[str, Any],
    signature_map: Mapping[str, str],
    *,
    distribution: Mapping[str, float] | None = None,
    causal_support: Mapping[str, Any] | None = None,
    causal_support_available: bool = False,
) -> tuple[str | None, str | None]:
    """Tier-one decisive route (§6.1). Returns ``(reason, tier_one_basis)`` when evidence
    is decisive, else ``(None, None)`` -- tier two applies.

    The spec's THREE decisive triggers -- a quarantined surface, ``dont_know`` on
    never-exposed content, an expired memory trace -- always auto-commit.

    The error-signature route is the AND gate of contract §2.1::

        legacy_ok      = high grader-confidence bucket AND signature dominance
        causal_veto    = a receipt exists AND (the reason's own hypotheses are
                         trace-CONTRADICTED, OR the causal mass names a different reason)
        causal_promote = approved support authority AND complete scores AND this reason
                         dominant over TOTAL mass AND trace-consistent claims
        tier_one       = (legacy_ok AND NOT causal_veto) OR causal_promote

    The causal channel therefore downgrades freely but promotes only under an approved
    authority -- and, critically, the mere EXISTENCE of a receipt no longer disables the
    legacy route (which, with production single-attempt receipts carrying all-``None``
    support, made tier one unreachable for every diagnosed attempt)."""

    # A bad/quarantined surface is NEVER a learner deficit -- decisive fault route.
    if inputs.get("surface_validity") == "quarantined":
        return "surface_or_grading_fault", TIER_ONE_BASIS_DETERMINISTIC
    # `dont_know` on never-exposed content -> unfamiliar/missing (decisive).
    if inputs.get("coarse_class") == "dont_know" and inputs.get("exposure_history") == "never_exposed":
        return "unfamiliar_or_missing_knowledge", TIER_ONE_BASIS_DETERMINISTIC
    # An expired memory trace -> memory lapse (decisive).
    if inputs.get("memory_trace") == "expired":
        return "memory_lapse", TIER_ONE_BASIS_DETERMINISTIC

    signature = inputs.get("error_signature")
    if not signature:
        return None, None
    merged = {**_SIGNATURE_REASON_MAP, **dict(signature_map)}
    reason = merged.get(str(signature))
    if reason not in TRIAGE_REASONS:
        return None, None

    norm = normalize_causal_support(causal_support)
    trace_state = _reason_trace_state(causal_support, reason)

    try:
        confidence = float(inputs.get("grader_confidence", 0.0) or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0
    legacy_ok = _confidence_bucket(confidence) == "high" and _signature_is_dominant(
        reason, distribution
    )
    causal_veto = causal_support_available and (
        trace_state == "contradicted"
        or (norm.dominant_reason is not None and norm.dominant_reason != reason)
    )
    causal_promote = (
        causal_support_available
        and norm.authority_approved
        and not norm.incomplete
        and norm.dominant_reason == reason
        and norm.dominant_share >= TRIAGE_DOMINANCE_SHARE
        and trace_state == "consistent_with_claims"
    )
    if causal_promote:
        return reason, TIER_ONE_BASIS_CAUSAL
    if legacy_ok and not causal_veto:
        return reason, TIER_ONE_BASIS_LEGACY
    return None, None


def _decisive_reason(
    inputs: Mapping[str, Any],
    signature_map: Mapping[str, str],
    *,
    distribution: Mapping[str, float] | None = None,
    causal_support: Mapping[str, Any] | None = None,
    causal_support_available: bool = False,
) -> str | None:
    """The reason half of :func:`_decisive_route` (kept for callers that do not care
    which arm of the gate fired)."""

    return _decisive_route(
        inputs,
        signature_map,
        distribution=distribution,
        causal_support=causal_support,
        causal_support_available=causal_support_available,
    )[0]


def _latest_discriminating_observation(
    repository: Repository, attempt_id: str
) -> dict[str, Any] | None:
    """The newest ADMITTED §7 observation bearing on this attempt's diagnosis.

    Read straight off the repository rather than through ``causal_orchestrator``:
    the orchestrator imports this module's vocabulary, and a reverse import would
    make the pair circular.
    """

    observations = repository.causal_discriminating_observations(
        attempt_id=attempt_id, admitted_only=True
    )
    return observations[-1] if observations else None


def _causal_support_snapshot(
    repository: Repository,
    inputs: Mapping[str, Any],
    signature_map: Mapping[str, str] | None = None,
) -> tuple[dict[str, Any] | None, bool]:
    """Project a P2 diagnosis receipt into the support snapshot the gate consumes.

    Open-set / ``H_OTHER`` hypotheses are RETAINED (tagged ``open_set``) so their mass
    reaches the denominator rather than inflating a mapped reason's share, and signatures
    resolve through the same merged ``{**_SIGNATURE_REASON_MAP, **signature_map}`` the
    gate uses -- a vault-configured override that only one side honoured used to
    mismatch silently and drop every such attempt to tier two.

    An admitted DISCRIMINATING OBSERVATION (migration 130) is overlaid on top:
    that receipt is the only channel that carries real per-hypothesis support,
    and without the overlay it would be inert data. The overlay is deliberately
    asymmetric, matching §2.1: its scores always land (so a discriminating
    observation may VETO a route), but its ``support_authority`` -- and hence any
    ability to PROMOTE -- lands only when the observation's own sensor earned it
    (``causal_orchestrator.record_probe_classification`` grants ``validator_owned``
    only to a deterministic sensor). A hypothesis the instrument did not measure
    keeps its ``None``, which is what makes ``normalize_causal_support`` report
    ``incomplete`` and refuse promotion on a partial instrument."""

    merged = {**_SIGNATURE_REASON_MAP, **dict(signature_map or {})}
    supplied = inputs.get("causal_support")
    if isinstance(supplied, Mapping):
        return dict(supplied), True
    attempt_id = inputs.get("attempt_id")
    if not attempt_id:
        return None, False
    debug = repository.attempt_debug_payload(str(attempt_id)) or {}
    attribution = debug.get("causal_attribution")
    receipt = (
        attribution.get("diagnosis_receipt")
        if isinstance(attribution, Mapping)
        else None
    )
    if not isinstance(receipt, Mapping):
        return None, False
    scores = receipt.get("support_scores")
    scores = scores if isinstance(scores, Mapping) else {}
    observation = _latest_discriminating_observation(repository, str(attempt_id))
    support_authority = receipt.get("support_authority")
    if observation is not None:
        scores = {**scores, **(observation.get("support_scores") or {})}
        if observation.get("support_authority"):
            support_authority = str(observation["support_authority"])
    # The per-hypothesis states come from causal_attribution's shared reader so every
    # consumer sees one verdict. A legacy (schema <= 2) receipt yields ``unknown`` for
    # every hypothesis: its receipt-level bool cannot say WHICH hypothesis was
    # contradicted, and ``unknown`` is neither a veto nor corroboration (§5.6).
    trace_map = receipt_trace_consistency(dict(receipt))
    legacy_consistent = receipt.get("trace_consistent") is True
    hypotheses: list[dict[str, Any]] = []
    for ref in receipt.get("hypotheses") or []:
        if not isinstance(ref, Mapping):
            continue
        ref_id = ref.get("id") or ref.get("hypothesis_id")
        if not ref_id:
            continue
        ref_id = str(ref_id)
        hypothesis = repository.causal_hypothesis(ref_id)
        open_set = (
            bool(ref.get("open_set"))
            or ref_id == OPEN_SET_CAUSE_ID
            or ref.get("status") == "open_set"
            or (hypothesis or {}).get("status") == "open_set"
        )
        triage_reason = None
        repair_class_id = ref.get("repair_class_id")
        if hypothesis is not None:
            evidence = hypothesis.get("evidence")
            evidence = evidence if isinstance(evidence, Mapping) else {}
            signature = evidence.get("error_type") or hypothesis.get("operation")
            triage_reason = merged.get(str(signature)) if signature else None
            repair_class_id = hypothesis.get("repair_class_id")
        state = trace_map.get(ref_id)
        if not isinstance(state, str) or state not in TRACE_CONSISTENCY_STATES:
            state = "unknown"
        row: dict[str, Any] = {
            "hypothesis_id": ref_id,
            "support_score": scores.get(ref_id),
            "triage_reason": None if open_set else triage_reason,
            "repair_class_id": repair_class_id,
            "trace_consistency": state,
        }
        if open_set:
            row["open_set"] = True
        hypotheses.append(row)
    return (
        {
            # Deprecated receipt-level alias, retained for the P1 claim-check overlay.
            "trace_consistent": legacy_consistent,
            "support_authority": support_authority,
            "discriminating_observation_id": (
                str(observation["id"]) if observation is not None else None
            ),
            "trace_consistency": {
                row["hypothesis_id"]: row["trace_consistency"] for row in hypotheses
            },
            "hypotheses": hypotheses,
        },
        True,
    )


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


def _provisional_distribution(
    inputs: Mapping[str, Any],
    signature_map: Mapping[str, str],
    *,
    causal_support: Mapping[str, Any] | None = None,
) -> dict[str, float]:
    """Tier-two provisional distribution over reasons (§6.1). Uses the P0 grading pass'
    supplied distribution when present; then the causal-support normalization (contract
    §2.2) INCLUDING its ``unknown_or_ambiguous`` residual, which must stay visible to the
    decision aid rather than being renormalized away; otherwise a bounded fallback that
    concentrates on the signature-mapped reason."""

    supplied = inputs.get("provisional_distribution")
    if isinstance(supplied, Mapping) and supplied:
        dist = {str(k): float(v) for k, v in supplied.items() if str(k) in TRIAGE_REASONS}
        total = sum(dist.values())
        if total > 0:
            return {k: v / total for k, v in dist.items()}

    norm = normalize_causal_support(causal_support)
    if norm.total_mass > 0:
        return dict(norm.by_reason)

    signature = inputs.get("error_signature")
    merged = {**_SIGNATURE_REASON_MAP, **dict(signature_map)}
    reason = merged.get(str(signature)) if signature else None
    if reason in TRIAGE_REASONS:
        # Ambiguous but leaning: majority on the leaning reason, remainder unknown.
        return {reason: 0.6, UNKNOWN_REASON: 0.4}
    return {UNKNOWN_REASON: 1.0}


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


def _row_belongs_to(row: Mapping[str, Any], reason: str) -> bool:
    """Which alternative a causal-support row is evidence for -- the same bucketing
    :func:`normalize_causal_support` used to build the distribution."""

    if _is_open_set(row) or row.get("triage_reason") not in TRIAGE_REASONS:
        return reason == UNKNOWN_REASON
    return row.get("triage_reason") == reason


def _alternatives(
    repository: Repository,
    distribution: Mapping[str, float],
    *,
    causal_support: Mapping[str, Any] | None = None,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    ranked = sorted(distribution.items(), key=lambda kv: (-kv[1], kv[0]))[:top_k]
    # The residual bucket is always surfaced when it carries mass, even outside the top
    # k: "how much of this diagnosis could not be placed" is decision-relevant (§2.2).
    if float(distribution.get(UNKNOWN_REASON, 0.0)) > 0 and not any(
        reason == UNKNOWN_REASON for reason, _ in ranked
    ):
        ranked = [*ranked, (UNKNOWN_REASON, float(distribution[UNKNOWN_REASON]))]
    out: list[dict[str, Any]] = []
    for reason, weight in ranked:
        alternative = {
            "reason": reason,
            "weight": round(float(weight), 6),
            "route": _route_summary(
                repository.failure_triage_route_for_reason(reason)
            ),
        }
        causal_hypotheses = [
            dict(row)
            for row in _causal_rows(causal_support)
            if _row_belongs_to(row, reason)
        ]
        if causal_hypotheses:
            alternative["causal_hypotheses"] = causal_hypotheses
        out.append(alternative)
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
    causal_support, causal_support_available = _causal_support_snapshot(
        repository, attempt, signature_map
    )
    # C7: a retried triage() for the same attempt dedupes on this ledger key.
    triage_event_key = f"triage:{attempt_id}" if attempt_id is not None else None
    decisive_reason, tier_one_basis = _decisive_route(
        attempt,
        signature_map,
        distribution=supplied_distribution,
        causal_support=causal_support,
        causal_support_available=causal_support_available,
    )
    normalization = normalize_causal_support(causal_support)
    # The inputs snapshot doubles as the decision payload: ``failure_triage_events`` has
    # no column for the gate trace, and ``tier_one_basis`` has to be auditable per event
    # (contract §2.1, §8 -- a universally-None basis is the anomaly to watch for).
    decision_payload = {
        **dict(attempt),
        "triage_decision": {
            "tier_one_basis": tier_one_basis,
            "causal_support_available": causal_support_available,
            "causal_support_authority_approved": normalization.authority_approved,
            "causal_support_incomplete": normalization.incomplete,
            "causal_dominant_reason": normalization.dominant_reason,
            "causal_dominant_share": round(normalization.dominant_share, 6),
            "causal_total_mass": round(normalization.total_mass, 6),
        },
    }
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
            inputs_snapshot_json=_json(decision_payload),
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
            tier_one_basis=tier_one_basis,
        )

    # Tier two: provisional distribution presented as a decision aid -- NOT committed.
    distribution = _provisional_distribution(
        attempt, signature_map, causal_support=causal_support
    )
    recommended = _recommended_reason(distribution)
    alternatives = _alternatives(
        repository, distribution, causal_support=causal_support
    )
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
        inputs_snapshot_json=_json(decision_payload),
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
