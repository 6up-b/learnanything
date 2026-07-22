"""P1 step 7 -- mint/gate infrastructure + durable pre-mint jobs
(spec_p1_shared_substrate §5.2, §5.3, §5.6; §9.3, §9.7).

Generalizes the probe_instance_generation mint/gate (instance_gate_errors,
generate_instances_for_episode, approve_probe_instance, run_llm_family_gate) into a
purpose-agnostic surface mint/gate, keeping the diagnostic objective/lifecycle
distinct (probe families keep their identifiability/likelihood gates -- §5.1).

Non-negotiables enforced here:

  * **Rendering and minting are separate transactions** (§5.3). Minting runs off the
    attempt hot path through a durable, leased job queue (migration 078, 033 pattern):
    exactly one worker drains at a time; an expired lease is recovered. A cache race
    may waste a candidate but may never double-administer or manufacture novelty.
  * **Opening an admitted administration calls no generator/LLM** (§9.7). Nothing on
    the administration-open path touches this module; :func:`request_candidates` only
    ENQUEUES a job for a worker to run later.
  * **Attempt submission is usable when mint workers are down** (§9.7): a pending mint
    request never blocks a response; the current admitted surface stays servable while
    its lifecycle permits (§7.5).
  * **The nine §5.2 gates** run on every generated candidate; results are append-only
    with inputs/versions/reviewer/failure reasons. A failed candidate is retained for
    audit but is never servable.
  * **Rotation is warmth/cadence-triggered** (§5.3): keep the admitted surface until
    the warmth projection or exposure cadence requests rotation; retain one admitted
    next + at most one spare; never mint for an inactive/retired card. If no candidate
    passes, serve familiar practice with disclosed reduced evidence -- never "fresh".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.services import familiarity as F
from learnloop.services.activities import _json

# Structural version pins (enums, not decision knobs -- registered structural).
MINT_GATE_POLICY_VERSION = "mint_gate_v1"
MINT_GENERATOR_VERSION = "surface_generator_v1"

# §5.3 rotation cadence (~2-3 administrations) -- a registered heuristic, not an
# invariant. A rotating surface rotates once its warmth OR its exposure cadence asks.
ROTATION_CADENCE_ADMINISTRATIONS = 2  # decision parameter

# §5.3 spare policy: retain one admitted next surface + at most one spare by default.
SPARE_SURFACE_COUNT = 1  # decision parameter

# The nine §5.2 gates, in order. Every generated surface -- regardless of purpose --
# must pass all applicable gates; gate 9 (comparative-vs-anchor) applies only when
# rotating against an anchor.
GATE_NAMES: tuple[str, ...] = (
    "card_contract_equivalence",
    "solvability_answer_key",
    "verbatim_rubric",
    "purpose_leakage",
    "novelty_audit",
    "task_feature_conformance",
    "difficulty_bounds",
    "safety_provenance",
    "comparative_vs_anchor",
)

# Purposes whose credit is unseen/independent -- a hard collision with an exposed
# sibling is disqualifying leakage (§4.1, §4.3, §5.2 gate 4).
_UNSEEN_CREDIT_PURPOSES: frozenset[str] = frozenset({"assessment", "diagnostic"})


class MintWorkerError(RuntimeError):
    """A mint worker failure. Never raised on the attempt/administration path."""


@dataclass(frozen=True)
class GateOutcome:
    name: str
    passed: bool
    reason: str | None = None


@dataclass(frozen=True)
class GateResult:
    gate_policy_version: str
    outcomes: tuple[GateOutcome, ...]
    inputs: Mapping[str, Any] = field(default_factory=dict)

    @property
    def admitted(self) -> bool:
        return all(o.passed for o in self.outcomes)

    @property
    def first_failure(self) -> str | None:
        for o in self.outcomes:
            if not o.passed:
                return o.name
        return None

    def as_dict(self) -> dict[str, Any]:
        return {
            "gate_policy_version": self.gate_policy_version,
            "admitted": self.admitted,
            "first_failure": self.first_failure,
            "outcomes": [
                {"name": o.name, "passed": o.passed, "reason": o.reason} for o in self.outcomes
            ],
            "inputs": dict(self.inputs),
        }


# ---------------------------------------------------------------------------
# Enqueue / claim / resolve -- the durable job surface (§5.6, 033 pattern).
# ---------------------------------------------------------------------------

def request_candidates(
    repository: Repository,
    *,
    card_version_id: str,
    anchor_surface_id: str | None = None,
    requested_angle: Mapping[str, Any] | None = None,
    generator_version: str = MINT_GENERATOR_VERSION,
    gate_policy_version: str = MINT_GATE_POLICY_VERSION,
    token_cost: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> str:
    """Enqueue a durable, idempotent pre-mint job (§5.6). This is the ONLY entry the
    render/administration path may call, and it merely records intent -- it runs no
    generator and never blocks a response. Idempotent on
    ``(card_version, anchor, requested_angle, generator, gate_policy)``.
    """

    angle_json = _json(dict(requested_angle)) if requested_angle is not None else ""
    return repository.enqueue_surface_mint_request(
        card_version_id=card_version_id,
        anchor_surface_id=anchor_surface_id,
        requested_angle_json=angle_json,
        generator_version=generator_version,
        gate_policy_version=gate_policy_version,
        token_cost_json=_json(dict(token_cost)) if token_cost is not None else None,
        clock=clock,
    )


def claim_next_mint_job(
    repository: Repository,
    *,
    worker_id: str,
    lease_seconds: int = 300,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Claim the next pending mint job under a lease (§5.6, 033 pattern). Returns None
    when another worker holds a live lease or nothing is pending. Off the hot path."""

    now = utc_now_iso(clock)
    from datetime import datetime, timedelta

    parsed = datetime.fromisoformat(now.replace("Z", "+00:00"))
    lease_expires_at = (parsed + timedelta(seconds=lease_seconds)).isoformat()
    return repository.claim_next_surface_mint_request(
        worker_id=worker_id,
        now_iso=now,
        lease_expires_at=lease_expires_at,
        lease_cutoff_iso=now,
    )


# ---------------------------------------------------------------------------
# The nine §5.2 gates.
# ---------------------------------------------------------------------------

def _card_bounds(repository: Repository, card_version_id: str) -> dict[str, Any]:
    authoring = repository.activity_card_authoring(card_version_id)
    if authoring is None:
        return {}
    import json as _json_mod

    bounds = _json_mod.loads(authoring.get("surface_variation_bounds_json") or "{}")
    return bounds if isinstance(bounds, Mapping) else {}


def _within_task_feature_bounds(
    features: Mapping[str, Any], bounds: Mapping[str, Any]
) -> bool:
    """Every declared task-feature bound must hold. A bound is either an allowed-value
    list or a ``{min,max}`` interval. An unbounded feature is unconstrained."""

    tf_bounds = bounds.get("task_features") or {}
    for name, allowed in tf_bounds.items():
        if name not in features:
            continue
        value = features[name]
        if isinstance(allowed, Mapping):
            lo, hi = allowed.get("min"), allowed.get("max")
            if lo is not None and value < lo:
                return False
            if hi is not None and value > hi:
                return False
        elif isinstance(allowed, (list, tuple, set)):
            if value not in allowed:
                return False
    return True


def _within_difficulty_bounds(difficulty: Any, bounds: Mapping[str, Any]) -> bool:
    diff_bounds = bounds.get("difficulty") or {}
    lo, hi = diff_bounds.get("min"), diff_bounds.get("max")
    if difficulty is None:
        return True
    if lo is not None and difficulty < lo:
        return False
    if hi is not None and difficulty > hi:
        return False
    return True


def run_all_gates(
    repository: Repository,
    *,
    request: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> GateResult:
    """Run the §5.2 gates on a generated candidate. Structural correctness flags come
    from the generator/candidate payload (default True -- a well-formed generator
    supplies them); the novelty/leakage gates read the authoritative exposure ledger,
    so no caller can bypass them. Rotating candidates additionally face the comparative
    gate against their anchor.
    """

    card_version_id = request["card_version_id"]
    # B2: the persisted anchor is the '' sentinel when there is no anchor (NOT NULL
    # DEFAULT ''); normalize it back to None so "no anchor" is never read as rotating.
    anchor_surface_id = request.get("anchor_surface_id") or None
    rotating = anchor_surface_id is not None
    purpose = candidate.get("purpose", "practice")
    bounds = _card_bounds(repository, card_version_id)
    outcomes: list[GateOutcome] = []

    # 1. card-contract equivalence: the candidate targets the SAME immutable card
    #    version (the contract identity), so it makes the same semantic claim (§3.5).
    same_contract = candidate.get("card_version_id", card_version_id) == card_version_id
    outcomes.append(
        GateOutcome("card_contract_equivalence", same_contract,
                    None if same_contract else "candidate_card_version_mismatch")
    )

    # 2. solvability / answer-key consistency.
    ok = bool(candidate.get("answer_key_consistent", True))
    outcomes.append(GateOutcome("solvability_answer_key", ok,
                                None if ok else "answer_key_inconsistent"))

    # 3. verbatim rubric applicability.
    ok = bool(candidate.get("rubric_verbatim", True))
    outcomes.append(GateOutcome("verbatim_rubric", ok,
                                None if ok else "rubric_not_applicable"))

    # 4. purpose-specific leakage. For an unseen/independent-credit purpose, a hard
    #    collision with an already-exposed sibling is disqualifying leakage (§4.1).
    leakage_ok = True
    leakage_reason: str | None = None
    cand_surface_id = candidate.get("surface_id")
    if cand_surface_id is not None and purpose in _UNSEEN_CREDIT_PURPOSES:
        fam = F.familiarity_projection_v1(repository, surface_id=cand_surface_id, purpose=purpose)
        if fam.blocks_unseen_claim:
            leakage_ok = False
            leakage_reason = "hard_collision_with_exposed_sibling"
    outcomes.append(GateOutcome("purpose_leakage", leakage_ok, leakage_reason))

    # 5. exact + near-clone novelty audit. A candidate identical to (or a hard sibling
    #    of) an exposed surface may not be minted as a fresh isomorph.
    novelty_ok = True
    novelty_reason: str | None = None
    cand_hash = candidate.get("surface_hash")
    if cand_hash is not None:
        prior = repository.exposures_by_surface_hash(cand_hash)
        if prior:
            novelty_ok = False
            novelty_reason = "exact_surface_hash_already_exposed"
    if novelty_ok and cand_surface_id is not None:
        fam = F.familiarity_projection_v1(repository, surface_id=cand_surface_id, purpose=purpose)
        # A near-clone (hard sibling) already exposed cannot be served as fresh.
        if any(c.sibling_exposed for c in fam.hard_collisions):
            novelty_ok = False
            novelty_reason = "near_clone_of_exposed_surface"
    outcomes.append(GateOutcome("novelty_audit", novelty_ok, novelty_reason))

    # 6. task-feature conformance.
    features = candidate.get("task_features") or {}
    ok = _within_task_feature_bounds(features, bounds)
    outcomes.append(GateOutcome("task_feature_conformance", ok,
                                None if ok else "task_features_out_of_bounds"))

    # 7. declared difficulty / complexity bounds.
    ok = _within_difficulty_bounds(candidate.get("difficulty"), bounds)
    outcomes.append(GateOutcome("difficulty_bounds", ok,
                                None if ok else "difficulty_out_of_bounds"))

    # 8. content safety and source/provenance validity.
    ok = bool(candidate.get("safety_ok", True)) and bool(candidate.get("provenance_valid", True))
    outcomes.append(GateOutcome("safety_provenance", ok,
                                None if ok else "safety_or_provenance_invalid"))

    # 9. comparative check against the anchor when rotating (§5.2 gate 9).
    if rotating:
        anchor = repository.fetch_surface(anchor_surface_id)
        comp_ok = True
        comp_reason: str | None = None
        if anchor is not None and cand_hash is not None and cand_hash == anchor.get("surface_hash"):
            comp_ok = False
            comp_reason = "candidate_identical_to_anchor"
        elif candidate.get("comparative_ok") is False:
            comp_ok = False
            comp_reason = "failed_comparative_check"
        outcomes.append(GateOutcome("comparative_vs_anchor", comp_ok, comp_reason))
    else:
        outcomes.append(GateOutcome("comparative_vs_anchor", True, "not_rotating"))

    return GateResult(
        gate_policy_version=request.get("gate_policy_version", MINT_GATE_POLICY_VERSION),
        outcomes=tuple(outcomes),
        inputs={
            "card_version_id": card_version_id,
            "anchor_surface_id": anchor_surface_id,
            "rotating": rotating,
            "purpose": purpose,
        },
    )


def _stale_lease_result(request: Mapping[str, Any], reason: str) -> GateResult:
    """A non-admitting result for a job that is no longer this worker's to process
    (B1 fencing). No state is written; the surface is neither admitted nor rejected."""

    return GateResult(
        gate_policy_version=request.get("gate_policy_version", MINT_GATE_POLICY_VERSION),
        outcomes=(GateOutcome("lease_valid", False, reason),),
        inputs={"request_id": request.get("id"), "stale_lease": True},
    )


def process_mint_job(
    repository: Repository,
    *,
    request: Mapping[str, Any],
    candidate: Mapping[str, Any],
    reviewer: str = "structural_gate",
    clock: Clock | None = None,
) -> GateResult:
    """Run the gates on a claimed job's candidate and transition the request:
    ``candidate_ready`` then ``admitted`` on pass, ``rejected`` on gate failure. The
    candidate surface is recorded either way (retained for audit; never servable when
    rejected). Off the hot path -- an exception here never reaches the attempt writer.

    B1: re-reads the request and refuses to process a job that is no longer ``running``
    under this worker's fencing ``lease_epoch``. A re-run of a terminal request, or a
    slow-but-alive worker whose lease was re-claimed, gets a non-admitting result and
    writes NOTHING -- so one claimed request can never yield two rotation-eligible
    surfaces (no double-admit).
    """

    lease_epoch = request.get("lease_epoch")
    current = repository.surface_mint_request(request["id"])
    if (
        current is None
        or current["status"] != "running"
        or (lease_epoch is not None and current["lease_epoch"] != lease_epoch)
    ):
        return _stale_lease_result(request, "job_not_running_under_this_lease")

    result = run_all_gates(repository, request=request, candidate=candidate)
    cand_surface_id = candidate.get("surface_id")
    gate_json = _json(result.as_dict() | {"reviewer": reviewer})
    applied = repository.set_surface_mint_candidate(
        request_id=request["id"],
        candidate_surface_id=cand_surface_id or "",
        gate_results_json=gate_json,
        expected_lease_epoch=lease_epoch,
        clock=clock,
    )
    if not applied:
        # The lease moved under us between the re-read and the write.
        return _stale_lease_result(request, "lease_lost_before_candidate_write")
    if result.admitted:
        admit_candidate(repository, request_id=request["id"], candidate_surface_id=cand_surface_id,
                        gate_result=result, lease_epoch=lease_epoch, clock=clock)
    else:
        reject_candidate(repository, request_id=request["id"], gate_result=result,
                         failure_reason=result.first_failure, lease_epoch=lease_epoch, clock=clock)
    return result


def _mark_surface_admitted(
    repository: Repository, *, surface_id: str, gate_result: GateResult, admitted: bool,
    clock: Clock | None = None,
) -> None:
    """Raw authoring write -- private (B5). Only :func:`admit_candidate`, which requires
    a passing :class:`GateResult`, may reach it. Flips a surface between admitted +
    rotation-eligible and un-admitted (rotation-ineligible)."""

    existing = repository.activity_surface_authoring(surface_id) or {}
    fields = dict(existing)
    fields["status"] = "admitted" if admitted else "unadmitted"
    fields["rotation_eligible"] = 1 if admitted else 0
    fields["gate_decision_json"] = _json(gate_result.as_dict())
    repository.upsert_activity_surface_authoring(surface_id=surface_id, fields=fields, clock=clock)


def admit_candidate(
    repository: Repository,
    *,
    request_id: str,
    candidate_surface_id: str | None,
    gate_result: GateResult | None = None,
    lease_epoch: int | None = None,
    clock: Clock | None = None,
) -> None:
    """Admit a gate-passing candidate into the pool (§5.2). Marks the surface authoring
    row admitted + rotation-eligible so the rotation policy can serve it next.

    B5: admission REQUIRES a non-None :class:`GateResult` with ``admitted=True``; a
    caller cannot bypass the gates by calling this with no result. The raw authoring
    write is private (:func:`_mark_surface_admitted`)."""

    if gate_result is None or not gate_result.admitted:
        raise MintWorkerError(
            "admit_candidate requires a passing GateResult (admitted=True); "
            f"got {None if gate_result is None else gate_result.first_failure!r}"
        )
    # B1: if this request previously admitted a DIFFERENT surface (a re-claim after
    # lease expiry produced a new candidate), the overwrite un-admits the prior one so
    # exactly one surface stays rotation-eligible per request.
    prior = repository.surface_mint_request(request_id)
    prior_surface = prior.get("candidate_surface_id") if prior else None

    applied = repository.resolve_surface_mint_request(
        request_id=request_id, status="admitted",
        gate_results_json=_json(gate_result.as_dict()),
        candidate_surface_id=candidate_surface_id,
        expected_lease_epoch=lease_epoch, require_active=True, clock=clock,
    )
    if not applied:
        # A stale-lease / already-terminal admit is a no-op (fencing rejected it).
        return
    if prior_surface and prior_surface != candidate_surface_id:
        prior_authoring = repository.activity_surface_authoring(prior_surface)
        if prior_authoring is not None:
            _mark_surface_admitted(
                repository, surface_id=prior_surface, gate_result=gate_result,
                admitted=False, clock=clock,
            )
    if candidate_surface_id:
        _mark_surface_admitted(
            repository, surface_id=candidate_surface_id, gate_result=gate_result,
            admitted=True, clock=clock,
        )


def reject_candidate(
    repository: Repository,
    *,
    request_id: str,
    gate_result: GateResult | None = None,
    failure_reason: str | None = None,
    lease_epoch: int | None = None,
    clock: Clock | None = None,
) -> None:
    """Reject a gate-failing candidate (§5.2). Retained for audit, never servable."""

    repository.resolve_surface_mint_request(
        request_id=request_id, status="rejected",
        gate_results_json=_json(gate_result.as_dict()) if gate_result is not None else None,
        failure_reason=failure_reason, expected_lease_epoch=lease_epoch,
        require_active=True, clock=clock,
    )


def fail_mint_job(
    repository: Repository, *, request_id: str, failure_reason: str, clock: Clock | None = None
) -> None:
    """Mark a job ``failed`` (generator error / interrupted lease). Retained for audit."""

    repository.resolve_surface_mint_request(
        request_id=request_id, status="failed", failure_reason=failure_reason, clock=clock
    )


# ---------------------------------------------------------------------------
# Retirement -> obsolete queued mint work (§5.6, §9.3).
# ---------------------------------------------------------------------------

def obsolete_mint_work_for_card_versions(
    repository: Repository, card_version_ids: Sequence[str], *, clock: Clock | None = None
) -> int:
    """Card/family retirement makes not-yet-terminal mint work ``obsolete`` (§5.6).
    Never spends further minting on an inactive/retired card (§5.3)."""

    return repository.obsolete_surface_mint_requests_for_card_versions(
        list(card_version_ids), clock=clock
    )


# ---------------------------------------------------------------------------
# Fixed / rotating surface policies (§5.3).
# ---------------------------------------------------------------------------

def _administration_count(repository: Repository, surface_id: str) -> int:
    """Administrations of the CARD this surface belongs to (§5.3 cadence). A single
    surface is rendered at most once (expose-at-most-once), so cadence is counted at the
    card-version level: how many of the card's surfaces have been administered."""

    surface = repository.fetch_surface(surface_id)
    if surface is None:
        return 0
    card_version_id = surface.get("card_version_id")
    if card_version_id is None:
        return 0
    count = 0
    for sibling in repository.surfaces_for_card_version(card_version_id):
        events = repository.activity_exposure_events_for_surface(sibling["id"])
        if any(e["kind"] in ("rendered", "submitted") for e in events):
            count += 1
    return count


@dataclass(frozen=True)
class RotationDecision:
    surface_id: str
    needs_rotation: bool
    reason: str
    warmth: float
    administrations: int


def rotation_decision(
    repository: Repository,
    *,
    surface_id: str,
    warmth_threshold: float | None = None,
    cadence: int | None = None,
) -> RotationDecision:
    """Decide whether a rotating surface needs rotation (§5.3): rotate once the warmth
    projection crosses the registered threshold OR the exposure cadence is reached.
    ``fixed`` surfaces never rotate (the caller checks the surface policy first)."""

    warmth_cut = F.WARMTH_ROTATION_THRESHOLD if warmth_threshold is None else warmth_threshold
    cadence_cut = ROTATION_CADENCE_ADMINISTRATIONS if cadence is None else cadence
    fam = F.familiarity_projection_v1(repository, surface_id=surface_id)
    administrations = _administration_count(repository, surface_id)
    if fam.warmth >= warmth_cut:
        return RotationDecision(surface_id, True, "warmth_threshold_crossed", fam.warmth, administrations)
    if administrations >= cadence_cut:
        return RotationDecision(surface_id, True, "exposure_cadence_reached", fam.warmth, administrations)
    return RotationDecision(surface_id, False, "still_fresh_enough", fam.warmth, administrations)


def needs_rotation(repository: Repository, *, surface_id: str) -> bool:
    authoring = repository.activity_surface_authoring(surface_id)
    if authoring is not None and authoring.get("surface_policy") == "fixed":
        # Fixed does not mean fresh, but it never auto-rotates (§5.3).
        return False
    return rotation_decision(repository, surface_id=surface_id).needs_rotation
