"""Activity lineage substrate services (spec_p0_measurement_correctness §3.5-§3.8).

This is the service boundary for the FINAL generic activity substrate (migration
065): resolve a legacy item to family/card/surface, reserve a surface, open an
administration atomically at render (the burn boundary, §4.5), append
exposure/feedback/lifecycle events, evaluate held-out eligibility against the ONE
shared familiarity ledger (§3.6), retire an activity with a reason record (§3.7),
and log interaction events (§3.8). SQL lives in ``db/repositories.py``; this
module holds the decisions.

The three presentation-identity hashes (§3.5) are split here from the monolithic
``assessment_contract_versions.contract_hash``:

- ``card_contract_hash`` -- the semantic claim (target, response contract, rubric
  semantics, task regime incl. purpose, feedback policy, evidence eligibility);
- ``surface_hash`` -- the exact presentation (prompt, expected answer,
  parameters, media);
- ``administration_snapshot_hash`` -- the fully resolved pin set at render.

All three reuse the 32-char unprefixed convention of
``assessment_contracts._content_hash`` so a legacy contract hash and a freshly
split card hash live in one hash family (required by the §7.1 backfill mapping).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import Repository
from learnloop.services.assessment_contracts import compile_assessment_contract
from learnloop.vault.models import LoadedVault, PracticeItem

# Purposes are immutable per family (§3.5, invariant §1.1). Diagnostic and
# assessment renders consume unseen status; instructional/practice enter the
# shared ledger but do not consume the object.
_CONSUMING_PURPOSES = frozenset({"diagnostic", "assessment"})

_PURPOSE_TO_LEGACY_KIND = {
    "practice": "practice_item",
    "diagnostic": "probe",
    "assessment": "exam",
    "instructional": "synthetic",
}

# provenance (§3.7) -> interaction-event origin (§3.8) mapping.
_PROVENANCE_TO_ORIGIN = {
    "learner_action": "learner",
    "affect_signal_escalation": "system",
    "owner_tooling": "owner_tooling",
}


class SurfaceAlreadyReserved(Exception):
    """Raised when a surface already has a live (uncancelled) reservation."""

    def __init__(self, surface_id: str):
        super().__init__(f"surface already has a live reservation: {surface_id}")
        self.surface_id = surface_id


class ExposureCollisionAtRender(Exception):
    """Raised when an assessment render collides with a prior exposure inside the
    burn lock (§4.5, §7.3 "exposure collision at render -> refuse ... and replace
    with a fresh eligible surface")."""

    def __init__(self, surface_id: str, reason: str):
        super().__init__(f"exposure collision at render for {surface_id}: {reason}")
        self.surface_id = surface_id
        self.reason = reason


def _json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _loads(value: str | None, default: Any = None) -> Any:
    if value is None:
        return default
    return json.loads(value)


def _canonical_hash(payload: Any) -> str:
    """32-char unprefixed sha256 over canonical JSON (matches
    ``assessment_contracts._content_hash`` for legacy->split hash continuity)."""

    return hashlib.sha256(_json(payload).encode("utf-8")).hexdigest()[:32]


def _algorithm_version(explicit: str | None) -> str:
    if explicit is not None:
        return explicit
    return LearnLoopConfig().algorithms.algorithm_version


# ---------------------------------------------------------------------------
# Hash boundaries (§3.5). Inputs are the compiled assessment contract (reused
# from assessment_contracts.compile_assessment_contract) partitioned into the
# semantic card payload and the exact surface payload.
# ---------------------------------------------------------------------------

def card_semantic_payload(contract: Mapping[str, Any], *, purpose: str) -> dict[str, Any]:
    """The semantic-claim partition of a compiled contract (§3.5 card_contract_hash).

    Everything that, if changed, is a new claim about what a response
    demonstrates -- but NOT the exact wording/parameters/media (those go to the
    surface). Purpose is part of the task regime, so a practice card and an
    assessment adapter of the same item are distinct card versions.
    """

    criteria = contract.get("criteria") or []
    return {
        "semantic_target": sorted(
            (
                _json(
                    sorted(
                        (target for target in (criterion.get("targets") or [])),
                        key=_json,
                    )
                )
                for criterion in criteria
            )
        ),
        "response_contract": {
            "practice_mode": contract.get("practice_mode"),
            "criteria": sorted(
                (
                    {
                        "id": criterion.get("id"),
                        "max_points": criterion.get("max_points"),
                        "tier": criterion.get("tier"),
                        "depends_on": sorted(criterion.get("depends_on") or []),
                        "correlation_group": criterion.get("correlation_group"),
                        "recipe_ids": sorted(criterion.get("recipe_ids") or []),
                    }
                    for criterion in criteria
                ),
                key=lambda item: str(item.get("id")),
            ),
        },
        "rubric_semantics": {
            "rubric_content_hash": contract.get("rubric_content_hash"),
            "rubric_max_points": contract.get("rubric_max_points"),
            "fatal_errors": sorted(
                (
                    {
                        "id": fatal.get("id"),
                        "description": fatal.get("description"),
                        "max_grade": fatal.get("max_grade"),
                        "misconception_id": fatal.get("misconception_id"),
                    }
                    for fatal in (contract.get("fatal_errors") or [])
                ),
                key=lambda item: str(item.get("id")),
            ),
        },
        "task_regime": {
            "purpose": purpose,
            "surface_family": contract.get("surface_family"),
            "assistance": contract.get("assistance"),
        },
        "feedback_policy": {"condition_class": (contract.get("feedback_policy") or "default")},
        "evidence_eligibility": contract.get("evidence_fingerprint"),
    }


def surface_payload(contract: Mapping[str, Any]) -> dict[str, Any]:
    """The exact-presentation partition of a compiled contract (§3.5 surface_hash)."""

    return {
        "prompt": contract.get("prompt"),
        "expected_answer": contract.get("expected_answer"),
        "parameters": contract.get("parameters"),
        "media": contract.get("media"),
    }


def fingerprint_of(contract: Mapping[str, Any]) -> str | None:
    """Shared-stimulus/near-clone key (§3.6 rule 2) from the evidence fingerprint.

    None when the item declares no fingerprint (a bare item has no shared-stimulus
    key and cannot collide by near-clone).
    """

    fingerprint = contract.get("evidence_fingerprint")
    if not fingerprint:
        return None
    return _canonical_hash(fingerprint)


def card_contract_hash(contract: Mapping[str, Any], *, purpose: str) -> str:
    return _canonical_hash(card_semantic_payload(contract, purpose=purpose))


def surface_hash(contract: Mapping[str, Any]) -> str:
    return _canonical_hash(surface_payload(contract))


def administration_snapshot_hash(payload: Mapping[str, Any]) -> str:
    return _canonical_hash(payload)


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ResolvedActivity:
    family_id: str
    family_version_id: str
    card_id: str
    card_version_id: str
    surface_id: str
    purpose: str
    card_contract_hash: str
    surface_hash: str
    fingerprint: str | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Eligibility:
    is_unseen: bool
    reason: str
    collisions: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Reservation:
    reservation_id: str
    surface_id: str
    purpose: str
    eligibility: Eligibility

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


@dataclass(frozen=True)
class Administration:
    administration_id: str
    surface_id: str
    card_version_id: str
    purpose: str
    snapshot_hash: str
    already_open: bool
    consumes_unseen: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RenderRefused:
    """No fresh eligible surface remained after an exposure collision (§4.5)."""

    surface_id: str
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Resolution (§3.5, §7.1 step 1)
# ---------------------------------------------------------------------------

def resolve_legacy_item(
    vault: LoadedVault,
    repository: Repository,
    item: PracticeItem,
    *,
    purpose: str,
    rubric: Any | None = None,
    clock: Clock | None = None,
) -> ResolvedActivity:
    """Deterministic, idempotent legacy item -> family/card/surface resolution.

    The default legacy family is ``practice`` and never changes purpose. A
    probe/exam reuse mints a purpose-specific adapter card+surface referencing the
    same legacy item with the EXACT identical ``surface_hash`` (only the card's
    task-regime purpose differs), so the shared ledger blocks manufactured
    novelty (§7.1 step 1).
    """

    contract = compile_assessment_contract(vault, item, rubric=rubric)
    cch = card_contract_hash(contract, purpose=purpose)
    sh = surface_hash(contract)
    fp = fingerprint_of(contract)
    legacy_kind = _PURPOSE_TO_LEGACY_KIND[purpose]
    schema_version = int(getattr(item, "schema_version", 1) or 1)

    family_id = repository.ensure_activity_family(
        purpose=purpose, legacy_kind=legacy_kind, title=item.id, clock=clock
    )
    family_version_id = repository.ensure_activity_family_version(
        family_id=family_id,
        version=1,
        family_spec_json=_json(
            {
                "purpose": purpose,
                "legacy_kind": legacy_kind,
                "legacy_item_id": item.id,
                "learning_object_id": item.learning_object_id,
            }
        ),
        clock=clock,
    )
    card_id = repository.ensure_activity_card(family_id=family_id, clock=clock)
    card_version_id = repository.ensure_activity_card_version(
        card_id=card_id,
        version=1,
        card_contract_hash=cch,
        contract_json=_json(card_semantic_payload(contract, purpose=purpose)),
        schema_version=schema_version,
        legacy_contract_version_id=None,
        clock=clock,
    )
    surface_id = repository.ensure_activity_surface(
        card_version_id=card_version_id,
        surface_hash=sh,
        fingerprint=fp,
        surface_json=_json(surface_payload(contract)),
        legacy_practice_item_id=item.id,
        clock=clock,
    )
    return ResolvedActivity(
        family_id=family_id,
        family_version_id=family_version_id,
        card_id=card_id,
        card_version_id=card_version_id,
        surface_id=surface_id,
        purpose=purpose,
        card_contract_hash=cch,
        surface_hash=sh,
        fingerprint=fp,
    )


# ---------------------------------------------------------------------------
# Held-out eligibility (§3.6) -- the four rules against the ONE shared ledger.
# ---------------------------------------------------------------------------

def evaluate_held_out_eligibility(
    repository: Repository, *, surface: Mapping[str, Any], purpose: str
) -> Eligibility:
    """The four §3.6 rules against ``activity_exposure_events`` (the ONE ledger)."""

    surface_id = surface["id"]
    sh = surface["surface_hash"]
    fp = surface.get("fingerprint")

    # Rule 1: exact surface_hash exposure is a hard collision.
    exact = repository.exposures_by_surface_hash(sh)
    if exact:
        return Eligibility(
            is_unseen=False,
            reason="exact_surface_collision",
            collisions={"exact": [event["id"] for event in exact]},
        )

    # Rule 2: shared-stimulus / fingerprint collision is a near-clone collision.
    if fp:
        near = [event for event in repository.exposures_by_fingerprint(fp)]
        if near:
            return Eligibility(
                is_unseen=False,
                reason="near_clone_collision",
                collisions={"fingerprint": [event["id"] for event in near]},
            )

    # Rule 3: an unresolved quarantine lifecycle event disqualifies assessment.
    lifecycle = repository.surface_lifecycle_history(surface_id)
    if any(event["kind"] == "quarantine" for event in lifecycle):
        return Eligibility(is_unseen=False, reason="assessment_disqualified")

    # Rule 4: absence of a recorded exposure means "unseen in LearnLoop" only.
    return Eligibility(is_unseen=True, reason="unseen_in_learnloop")


# ---------------------------------------------------------------------------
# Reservation (§4.5)
# ---------------------------------------------------------------------------

def reserve_surface(
    repository: Repository,
    *,
    surface_id: str,
    purpose: str,
    goal_id: str | None = None,
    target_contract_version_id: str | None = None,
    target_support_hash: str | None = None,
    clock: Clock | None = None,
) -> Reservation:
    """Reserve a surface from the pinned target's frozen distribution (§4.5).

    Snapshots the eligibility decision (§3.6) and appends a ``reserve`` lifecycle
    event. Raises :class:`SurfaceAlreadyReserved` on the live-uniqueness conflict.
    """

    surface = repository.fetch_surface(surface_id)
    if surface is None:
        raise ValueError(f"unknown surface: {surface_id}")
    eligibility = evaluate_held_out_eligibility(repository, surface=surface, purpose=purpose)
    try:
        reservation_id = repository.insert_surface_reservation(
            surface_id=surface_id,
            goal_id=goal_id,
            target_contract_version_id=target_contract_version_id,
            target_support_hash=target_support_hash,
            purpose=purpose,
            eligibility_json=_json(eligibility.as_dict()),
            clock=clock,
        )
    except sqlite3.IntegrityError as exc:
        raise SurfaceAlreadyReserved(surface_id) from exc
    repository.append_surface_lifecycle_event(
        surface_id=surface_id,
        kind="reserve",
        reservation_id=reservation_id,
        detail_json=_json({"purpose": purpose, "eligibility": eligibility.as_dict()}),
        clock=clock,
    )
    return Reservation(
        reservation_id=reservation_id,
        surface_id=surface_id,
        purpose=purpose,
        eligibility=eligibility,
    )


def cancel_reservation(
    repository: Repository, reservation_id: str, *, clock: Clock | None = None
) -> str:
    """Cancel a reservation. Returns ``released_unseen`` when the surface is still
    pristine (no exposure event) -- restoring it to availability -- else
    ``cancelled`` (the surface stays burned). Implements §4.5 / §9.5 line 1."""

    reservation = repository.fetch_reservation(reservation_id)
    if reservation is None:
        raise ValueError(f"unknown reservation: {reservation_id}")
    surface_id = reservation["surface_id"]

    # Already exposed -> the surface is burned; cancel without releasing (the
    # status guard leaves a concurrently-rendered reservation's 'rendered' intact).
    if repository.exposures_for_surface(surface_id):
        repository.close_surface_reservation(
            reservation_id=reservation_id, status="cancelled",
            expected_status="reserved", clock=clock,
        )
        return "cancelled"

    # Atomically claim the release: only a still-'reserved' reservation transitions
    # (L8). If we lost the race to a concurrent render or cancel, do NOT release.
    claimed = repository.close_surface_reservation(
        reservation_id=reservation_id, status="released_unseen",
        expected_status="reserved", clock=clock,
    )
    if not claimed:
        return "cancelled"

    # Re-check exposure INSIDE the won transition: a render that burned the surface
    # between our first read and the compare-and-set means the surface is no longer
    # pristine, so we must NOT emit a release_unseen lifecycle event (§4.5/§9.5).
    if repository.exposures_for_surface(surface_id):
        return "cancelled"

    repository.append_surface_lifecycle_event(
        surface_id=surface_id,
        kind="release_unseen",
        reservation_id=reservation_id,
        clock=clock,
    )
    return "released_unseen"


# ---------------------------------------------------------------------------
# Render / burn (§4.5) -- the atomic boundary.
# ---------------------------------------------------------------------------

def open_administration(
    repository: Repository,
    *,
    resolved: ResolvedActivity,
    reservation: Reservation | None = None,
    goal_id: str | None = None,
    target_contract_version_id: str | None = None,
    target_support_hash: str | None = None,
    grader_model_version_id: str | None = None,
    selection_policy_version_id: str | None = None,
    decision_params_hash: str | None = None,
    assistance: Mapping[str, Any] | None = None,
    feedback_condition: str | None = None,
    algorithm_version: str | None = None,
    head_support_hash: str | None = None,
    enforce_eligibility: bool | None = None,
    clock: Clock | None = None,
) -> Administration:
    """The atomic render/burn boundary (§4.5). Rechecks eligibility, computes the
    ``administration_snapshot_hash``, and opens the administration once. Under a
    concurrent second render the loser returns the winner's administration
    (expose-at-most-once, §9.5).

    For ``purpose == 'assessment'`` (unless ``enforce_eligibility`` is overridden)
    the §3.6 collision check is re-run INSIDE the burn lock and a collision
    REFUSES the render (raises :class:`ExposureCollisionAtRender`) instead of
    burning a colliding surface. When ``head_support_hash`` is supplied and differs
    from the pinned ``target_support_hash``, the administration is stamped
    ``eligibility_json.support_representative = false`` (the older version may still
    certify but is labeled unrepresentative of the new head; §4.5) -- the reserve is
    neither retargeted nor destroyed."""

    surface = repository.fetch_surface(resolved.surface_id)
    if surface is None:
        raise ValueError(f"unknown surface: {resolved.surface_id}")

    if enforce_eligibility is None:
        enforce_eligibility = resolved.purpose == "assessment"

    # Recheck eligibility immediately before render (§4.5). The verdict is pinned
    # into the snapshot for audit; for assessment it is ALSO enforced in-lock.
    eligibility = evaluate_held_out_eligibility(
        repository, surface=surface, purpose=resolved.purpose
    )
    reservation_id = reservation.reservation_id if reservation is not None else None
    resolved_goal_id = goal_id
    if resolved_goal_id is None and reservation is not None:
        row = repository.fetch_reservation(reservation.reservation_id)
        resolved_goal_id = row["goal_id"] if row is not None else None

    # Target-head support compatibility (§4.5): mark unrepresentative when the head
    # support hash has moved since the reservation pinned its support hash.
    support_representative = True
    if head_support_hash is not None and target_support_hash is not None:
        support_representative = head_support_hash == target_support_hash
    eligibility_dict = eligibility.as_dict()
    eligibility_dict["support_representative"] = support_representative

    snapshot_payload = {
        "card_version_id": resolved.card_version_id,
        "card_contract_hash": resolved.card_contract_hash,
        "surface_id": resolved.surface_id,
        "surface_hash": resolved.surface_hash,
        "target_contract_version_id": target_contract_version_id,
        "target_support_hash": target_support_hash,
        "context": {"goal_id": resolved_goal_id, "purpose": resolved.purpose},
        "grader_model_version_id": grader_model_version_id,
        "selection_policy_version_id": selection_policy_version_id,
        "decision_params_hash": decision_params_hash,
        "assistance": dict(assistance) if assistance is not None else None,
        "feedback_condition": feedback_condition,
    }
    snapshot_hash = administration_snapshot_hash(snapshot_payload)
    consumes_unseen = resolved.purpose in _CONSUMING_PURPOSES

    pins = {
        "target_contract_version_id": target_contract_version_id,
        "target_support_hash": target_support_hash,
        "grader_model_version_id": grader_model_version_id,
        "selection_policy_version_id": selection_policy_version_id,
        "decision_params_hash": decision_params_hash,
        "assistance_json": _json(dict(assistance)) if assistance is not None else None,
        "feedback_condition": feedback_condition,
        "eligibility_json": _json(eligibility_dict),
    }
    result = repository.open_administration_atomic(
        reservation_id=reservation_id,
        surface_id=resolved.surface_id,
        card_version_id=resolved.card_version_id,
        family_id=resolved.family_id,
        purpose=resolved.purpose,
        surface_hash=resolved.surface_hash,
        fingerprint=resolved.fingerprint,
        snapshot_hash=snapshot_hash,
        snapshot_json=_json(snapshot_payload),
        consumes_unseen=consumes_unseen,
        pins=pins,
        algorithm_version=_algorithm_version(algorithm_version),
        enforce_eligibility=enforce_eligibility,
        clock=clock,
    )
    if result.get("refused"):
        raise ExposureCollisionAtRender(resolved.surface_id, result["refusal_reason"])
    admin = result["administration"]
    return Administration(
        administration_id=admin["id"],
        surface_id=admin["surface_id"],
        card_version_id=admin["card_version_id"],
        purpose=admin["purpose"],
        snapshot_hash=admin["administration_snapshot_hash"],
        already_open=result["already_open"],
        consumes_unseen=consumes_unseen,
    )


def render_assessment_with_replacement(
    repository: Repository,
    *,
    candidates: list[ResolvedActivity],
    goal_id: str | None = None,
    target_contract_version_id: str | None = None,
    target_support_hash: str | None = None,
    head_support_hash: str | None = None,
    feedback_condition: str | None = None,
    algorithm_version: str | None = None,
    clock: Clock | None = None,
) -> Administration | RenderRefused:
    """Draw the next eligible surface from the pinned target's frozen distribution
    on an exposure collision (§4.5, §7.3 row 7). Reserves + renders each candidate
    in order; on :class:`ExposureCollisionAtRender` moves to the next; returns
    :class:`RenderRefused` when none remain."""

    last_reason = "no_candidates"
    for resolved in candidates:
        last_reason = "exhausted"
        try:
            reservation = reserve_surface(
                repository,
                surface_id=resolved.surface_id,
                purpose="assessment",
                goal_id=goal_id,
                target_contract_version_id=target_contract_version_id,
                target_support_hash=target_support_hash,
                clock=clock,
            )
        except SurfaceAlreadyReserved:
            continue
        try:
            return open_administration(
                repository,
                resolved=resolved,
                reservation=reservation,
                goal_id=goal_id,
                target_contract_version_id=target_contract_version_id,
                target_support_hash=target_support_hash,
                head_support_hash=head_support_hash,
                feedback_condition=feedback_condition,
                algorithm_version=algorithm_version,
                clock=clock,
            )
        except ExposureCollisionAtRender as exc:
            last_reason = exc.reason
            cancel_reservation(repository, reservation.reservation_id, clock=clock)
            continue
    return RenderRefused(
        surface_id=candidates[-1].surface_id if candidates else "",
        reason=last_reason,
    )


def append_practice_successor_proposal(
    repository: Repository,
    *,
    surface_id: str,
    administration_id: str | None = None,
    not_before: str | None = None,
    reason: str | None = None,
    clock: Clock | None = None,
) -> str:
    """Record a practice-successor PROPOSAL after a failed assessment with feedback
    (§4.5, §9.5 line 4). Appends a ``practice_successor_minted`` lifecycle event
    marked ``detail.stage='proposal'``. The assessment purpose and burn state are
    never changed (invariant 7); P1 may later mint the linked practice surface."""

    return repository.append_surface_lifecycle_event(
        surface_id=surface_id,
        kind="practice_successor_minted",
        administration_id=administration_id,
        reason=reason,
        detail_json=_json({"stage": "proposal", "not_before": not_before}),
        clock=clock,
    )


# ---------------------------------------------------------------------------
# Exposure / feedback / observation / lifecycle wrappers (§3.5, §3.6)
# ---------------------------------------------------------------------------

def append_exposure(
    repository: Repository,
    *,
    surface: Mapping[str, Any],
    administration_id: str | None,
    kind: str,
    purpose: str,
    consumes_unseen: bool | None = None,
    detail: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> str:
    if consumes_unseen is None:
        consumes_unseen = kind == "rendered" and purpose in _CONSUMING_PURPOSES
    return repository.append_exposure_event(
        surface_id=surface["id"],
        administration_id=administration_id,
        surface_hash=surface["surface_hash"],
        fingerprint=surface.get("fingerprint"),
        kind=kind,
        purpose=purpose,
        consumes_unseen=consumes_unseen,
        detail_json=_json(dict(detail)) if detail is not None else None,
        clock=clock,
    )


def append_feedback(
    repository: Repository,
    *,
    surface: Mapping[str, Any],
    administration_id: str | None,
    purpose: str,
    timing: str,
    clock: Clock | None = None,
) -> str:
    """Append a ``feedback_revealed`` exposure. ``timing='before_response'`` makes
    the administration ineligible for terminal credit (§4.5, §9.5 line 3) -- that
    verdict is recorded on the observation via :func:`append_observation`."""

    return repository.append_exposure_event(
        surface_id=surface["id"],
        administration_id=administration_id,
        surface_hash=surface["surface_hash"],
        fingerprint=surface.get("fingerprint"),
        kind="feedback_revealed",
        purpose=purpose,
        consumes_unseen=False,
        detail_json=_json({"timing": timing}),
        clock=clock,
    )


def append_lifecycle(
    repository: Repository,
    *,
    surface_id: str,
    kind: str,
    reservation_id: str | None = None,
    administration_id: str | None = None,
    reason: str | None = None,
    detail: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> str:
    return repository.append_surface_lifecycle_event(
        surface_id=surface_id,
        kind=kind,
        reservation_id=reservation_id,
        administration_id=administration_id,
        reason=reason,
        detail_json=_json(dict(detail)) if detail is not None else None,
        clock=clock,
    )


def evidence_eligibility_for(
    *, purpose: str, feedback_condition: str | None
) -> tuple[str, str]:
    """Purpose+feedback -> (evidence_eligibility, reason) for an observation (§3.6/§4.5).

    Feedback revealed before response yields no terminal credit; instructional
    administrations are categorically ineligible for unassisted certification.
    """

    if feedback_condition == "before_response":
        return "ineligible", "feedback_before_response"
    if purpose == "instructional":
        return "ineligible", "instructional_not_certifiable"
    if purpose == "assessment":
        return "terminal", "assessment_terminal"
    if purpose == "diagnostic":
        return "diagnostic", "diagnostic_evidence"
    return "practice", "practice_evidence"


def append_observation(
    repository: Repository,
    *,
    administration_id: str,
    surface_id: str,
    purpose: str,
    feedback_condition: str | None = None,
    attempt_id: str | None = None,
    response_ref: str | None = None,
    algorithm_version: str | None = None,
    clock: Clock | None = None,
) -> str:
    """Record one response/attempt observation with its purpose-specific evidence
    eligibility, and anchor a ``response_appended`` measurement event (§3.5, §4.1)."""

    eligibility, reason = evidence_eligibility_for(
        purpose=purpose, feedback_condition=feedback_condition
    )
    observation_id = repository.insert_activity_observation(
        administration_id=administration_id,
        surface_id=surface_id,
        attempt_id=attempt_id,
        response_ref=response_ref,
        evidence_eligibility=eligibility,
        eligibility_reason=reason,
        clock=clock,
    )
    repository.append_measurement_event(
        administration_id=administration_id,
        kind="response_appended",
        algorithm_version=_algorithm_version(algorithm_version),
        observation_id=observation_id,
        clock=clock,
    )
    return observation_id


# ---------------------------------------------------------------------------
# Retirement (§3.7)
# ---------------------------------------------------------------------------

def retire_with_reason(
    repository: Repository,
    *,
    scope: str,
    reason: str,
    provenance: str,
    family_id: str | None = None,
    card_version_id: str | None = None,
    surface_id: str | None = None,
    replacement_proposal: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> str:
    """Retire a family/card/surface (§3.7). Appends a ``retire`` lifecycle event for
    each affected surface, a ``retirement_reason`` interaction event (§3.8), and a
    ``retirement_records`` row. Deletes NOTHING -- learner state, facet evidence,
    source relationships, and goals are untouched (§3.7 invariant)."""

    if scope == "surface":
        if surface_id is None:
            raise ValueError("surface scope requires surface_id")
        surface_ids = [surface_id]
    elif scope == "card":
        if card_version_id is None:
            raise ValueError("card scope requires card_version_id")
        surface_ids = [row["id"] for row in repository.surfaces_for_card_version(card_version_id)]
    elif scope == "family":
        if family_id is None:
            raise ValueError("family scope requires family_id")
        surface_ids = [row["id"] for row in repository.surfaces_for_family(family_id)]
    else:
        raise ValueError(f"unknown retirement scope: {scope}")

    detail = {
        "scope": scope,
        "reason": reason,
        "provenance": provenance,
        "family_id": family_id,
        "card_version_id": card_version_id,
        "surface_id": surface_id,
    }
    lifecycle_event_id: str | None = None
    for affected in surface_ids:
        event_id = repository.append_surface_lifecycle_event(
            surface_id=affected,
            kind="retire",
            reason=reason,
            detail_json=_json(detail),
            clock=clock,
        )
        if lifecycle_event_id is None:
            lifecycle_event_id = event_id

    interaction_event_id = repository.append_interaction_event(
        kind="retirement_reason",
        origin=_PROVENANCE_TO_ORIGIN.get(provenance, "system"),
        subject_type=scope,
        subject_id=surface_id or card_version_id or family_id,
        surface_id=surface_id,
        payload_json=_json(detail),
        clock=clock,
    )
    return repository.insert_retirement_record(
        scope=scope,
        family_id=family_id,
        card_version_id=card_version_id,
        surface_id=surface_id,
        reason=reason,
        provenance=provenance,
        replacement_proposal_json=_json(dict(replacement_proposal))
        if replacement_proposal is not None
        else None,
        lifecycle_event_id=lifecycle_event_id,
        interaction_event_id=interaction_event_id,
        clock=clock,
    )


# ---------------------------------------------------------------------------
# Interaction-event envelope (§3.8) -- the single writer + convenience shims.
# ---------------------------------------------------------------------------

def log_interaction_event(
    repository: Repository,
    *,
    kind: str,
    origin: str = "learner",
    subject_type: str | None = None,
    subject_id: str | None = None,
    administration_id: str | None = None,
    surface_id: str | None = None,
    attempt_id: str | None = None,
    affect_tap_kind: str | None = None,
    attempt_duration_ms: int | None = None,
    payload: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> str:
    """The single writer for the Layer-5 interaction envelope (§3.8).

    F1: reader/reading kinds are auto-stamped ``authority_class='salience_only'``
    by construction here -- membership in ``READING_EVENT_KINDS`` is the single
    source of truth, so no reader write can forget the firewall stamp. Non-reader
    kinds (``attempt_duration`` etc.) keep their own semantics and are untouched."""

    from learnloop.services.salience_firewall import READING_EVENT_KINDS, SALIENCE_ONLY

    if kind in READING_EVENT_KINDS:
        payload = {**(dict(payload) if payload is not None else {}),
                   "authority_class": SALIENCE_ONLY}

    return repository.append_interaction_event(
        kind=kind,
        origin=origin,
        subject_type=subject_type,
        subject_id=subject_id,
        administration_id=administration_id,
        surface_id=surface_id,
        attempt_id=attempt_id,
        affect_tap_kind=affect_tap_kind,
        attempt_duration_ms=attempt_duration_ms,
        payload_json=_json(dict(payload)) if payload is not None else None,
        clock=clock,
    )


def log_attempt_duration(
    repository: Repository,
    *,
    administration_id: str | None,
    attempt_id: str | None,
    duration_ms: int,
    surface_id: str | None = None,
    origin: str = "learner",
    clock: Clock | None = None,
) -> str:
    """Log an attempt duration (§3.8, review-burden accounting / stop-mode cost)."""

    return log_interaction_event(
        repository,
        kind="attempt_duration",
        origin=origin,
        administration_id=administration_id,
        surface_id=surface_id,
        attempt_id=attempt_id,
        attempt_duration_ms=duration_ms,
        clock=clock,
    )


def log_affect_tap(
    repository: Repository,
    *,
    affect_tap_kind: str,
    subject_type: str | None = None,
    subject_id: str | None = None,
    administration_id: str | None = None,
    surface_id: str | None = None,
    attempt_id: str | None = None,
    origin: str = "learner",
    payload: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> str:
    """Capture an affect tap (§4.6). The signal is logged unconditionally; the
    discount/quarantine/retirement effects are applied by later packages."""

    return log_interaction_event(
        repository,
        kind="affect_tap",
        origin=origin,
        subject_type=subject_type,
        subject_id=subject_id,
        administration_id=administration_id,
        surface_id=surface_id,
        attempt_id=attempt_id,
        affect_tap_kind=affect_tap_kind,
        payload=payload,
        clock=clock,
    )


# ===========================================================================
# P1 step 3 -- family/card contract extensions (spec_p1_shared_substrate §3.6, §3.7)
#
# Owner decision A.1: extend the P0 (migration 065) immutable family/card version
# rows via side tables keyed by the P0 version id -- NEVER rename or ALTER the
# immutable P0 rows (they stay byte-frozen for replay). These functions ADD to this
# module; no P0 symbol above is renamed (P0 §3.5 guarantee).
# ===========================================================================

# The four immutable authoring purposes (§3.5, invariant 2). A family is authored
# as exactly one; it never transitions to another purpose in place.
_AUTHORING_PURPOSES = frozenset({"diagnostic", "instructional", "practice", "assessment"})

# Typed cross-purpose link kinds (§3.6). A link connects families; it never re-labels
# a card/surface, and never points a family at its own identity (invariant 2).
_CROSS_PURPOSE_LINK_KINDS = frozenset(
    {"diagnoses_for", "teaches_for", "practices_for", "assesses_for"}
)

_P1_CAPABILITIES = frozenset(
    {"retrieval", "schema_interpretation", "procedure_execution", "method_selection", "coordination"}
)


class FamilyPurposeImmutable(Exception):
    """A family's authoring purpose cannot change in place; cross-purpose reuse must
    create a separately gated family (§1.1 invariant 2, §9.1)."""

    def __init__(self, family_id: str, existing: str, requested: str):
        super().__init__(
            f"family {family_id} is authored {existing!r}; cannot re-author as "
            f"{requested!r} in place (cross-purpose reuse needs a separate family)"
        )
        self.family_id = family_id
        self.existing = existing
        self.requested = requested


class CrossPurposeIdentityReuse(Exception):
    """A cross-purpose link tried to reuse the same activity identity (§9.1)."""


class InvalidAuthoring(Exception):
    """Authoring input violated a closed vocabulary or contract."""


def author_family_version(
    repository: Repository,
    *,
    family_id: str,
    version: int,
    authoring_purpose: str,
    family_spec: Mapping[str, Any],
    pattern_version_id: str | None = None,
    progression_policy_version_id: str | None = None,
    commitment_id: str | None = None,
    commitment_target_version_id: str | None = None,
    goal_contract_version_id: str | None = None,
    depth_policy_version_id: str | None = None,
    depth_envelope_version_id: str | None = None,
    served_milestone_edges: Any | None = None,
    angle_inventory: Any | None = None,
    coverage_targets: Any | None = None,
    cross_purpose_links: Sequence[Mapping[str, Any]] | None = None,
    clock: Clock | None = None,
) -> str:
    """Stage 1-3 of the §5.1 authoring transaction: resolve target + policy/pattern
    and create a DRAFT family version (idempotent on ``(family_id, version)``) plus
    its authoring side row. Failure before activation leaves an inspectable draft and
    no schedulable partial object (§5.1, §7.5); call :func:`activate_family_version`
    to activate. Re-running with identical inputs yields the SAME family_version_id.

    Enforces family-purpose immutability (§9.1): a family already authored under one
    purpose cannot be re-authored under another in place."""

    if authoring_purpose not in _AUTHORING_PURPOSES:
        raise InvalidAuthoring(f"invalid authoring purpose: {authoring_purpose!r}")

    existing_purposes = repository.activity_family_authoring_purposes(family_id)
    for other_purpose in existing_purposes.values():
        if other_purpose != authoring_purpose:
            raise FamilyPurposeImmutable(family_id, other_purpose, authoring_purpose)

    family_version_id = repository.ensure_activity_family_version(
        family_id=family_id, version=version, family_spec_json=_json(dict(family_spec)), clock=clock
    )

    links = _validate_cross_purpose_links(repository, family_version_id, cross_purpose_links)

    repository.upsert_activity_family_authoring(
        family_version_id=family_version_id,
        fields={
            "commitment_id": commitment_id,
            "commitment_target_version_id": commitment_target_version_id,
            "authoring_purpose": authoring_purpose,
            "pattern_version_id": pattern_version_id,
            "progression_policy_version_id": progression_policy_version_id,
            "goal_contract_version_id": goal_contract_version_id,
            "depth_policy_version_id": depth_policy_version_id,
            "depth_envelope_version_id": depth_envelope_version_id,
            "served_milestone_edges_json": _json(served_milestone_edges) if served_milestone_edges is not None else None,
            "cross_purpose_links_json": _json(links) if links else None,
            "angle_inventory_json": _json(angle_inventory) if angle_inventory is not None else None,
            "coverage_targets_json": _json(coverage_targets) if coverage_targets is not None else None,
            "status": "draft",
        },
        clock=clock,
    )
    return family_version_id


def activate_family_version(repository: Repository, *, family_version_id: str) -> None:
    """Activate a drafted family version (§5.1 stage 6). Idempotent."""

    if repository.activity_family_authoring(family_version_id) is None:
        raise InvalidAuthoring(f"no authoring draft for family version: {family_version_id}")
    repository.set_activity_family_authoring_status(
        family_version_id=family_version_id, status="active"
    )


def _validate_cross_purpose_links(
    repository: Repository,
    family_version_id: str,
    cross_purpose_links: Sequence[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    if not cross_purpose_links:
        return []
    own_family_id = repository.activity_family_version_family_id(family_version_id)
    out: list[dict[str, Any]] = []
    for link in cross_purpose_links:
        kind = link.get("link_kind")
        target_family_id = link.get("target_family_id")
        if kind not in _CROSS_PURPOSE_LINK_KINDS:
            raise InvalidAuthoring(f"invalid cross-purpose link kind: {kind!r}")
        if not target_family_id:
            raise InvalidAuthoring("cross-purpose link requires target_family_id")
        if own_family_id is not None and target_family_id == own_family_id:
            # A cross-purpose link never reuses the same activity identity (§9.1).
            raise CrossPurposeIdentityReuse(
                f"cross-purpose link {kind!r} cannot point at the family's own identity"
            )
        out.append({"link_kind": kind, "target_family_id": target_family_id})
    return out


def link_cross_purpose_families(
    repository: Repository,
    *,
    family_version_id: str,
    links: Sequence[Mapping[str, Any]],
    clock: Clock | None = None,
) -> list[dict[str, Any]]:
    """Attach typed cross-purpose family links (§3.6). Links families; never reuses a
    card/surface identity. Merges onto any existing links on the authoring row."""

    authoring = repository.activity_family_authoring(family_version_id)
    if authoring is None:
        raise InvalidAuthoring(f"no authoring row for family version: {family_version_id}")
    validated = _validate_cross_purpose_links(repository, family_version_id, links)
    existing = _loads(authoring.get("cross_purpose_links_json") or "[]", [])
    merged = existing + validated
    fields = dict(authoring)
    fields["cross_purpose_links_json"] = _json(merged)
    repository.upsert_activity_family_authoring(
        family_version_id=family_version_id, fields=fields, clock=clock
    )
    return merged


def pin_card_authoring(
    repository: Repository,
    *,
    card_version_id: str,
    family_version_id: str | None = None,
    pattern_version_id: str | None = None,
    task_feature_schema_version_id: str | None = None,
    task_features: Mapping[str, Any] | None = None,
    capability: str | None = None,
    outcome_schema_id: str | None = None,
    outcome_schema_version: int | None = None,
    surface_policy: str | None = None,
    surface_variation_bounds: Mapping[str, Any] | None = None,
    angle_identity: Mapping[str, Any] | None = None,
    generator_version: str | None = None,
    gate_policy_version: str | None = None,
    expected_burden: Mapping[str, Any] | None = None,
    calibration_metadata: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> None:
    """Pin the P1 card-version authoring contract (§3.7) as a side row keyed by the
    P0 immutable card version id. The 065 ``activity_card_versions`` row is untouched."""

    if capability is not None and capability not in _P1_CAPABILITIES:
        raise InvalidAuthoring(f"invalid capability: {capability!r}")
    if surface_policy is not None and surface_policy not in ("fixed", "rotating"):
        raise InvalidAuthoring(f"invalid surface policy: {surface_policy!r}")
    repository.upsert_activity_card_authoring(
        card_version_id=card_version_id,
        fields={
            "family_version_id": family_version_id,
            "pattern_version_id": pattern_version_id,
            "task_feature_schema_version_id": task_feature_schema_version_id,
            "task_features_json": _json(dict(task_features)) if task_features is not None else None,
            "capability": capability,
            "outcome_schema_id": outcome_schema_id,
            "outcome_schema_version": outcome_schema_version,
            "surface_policy": surface_policy,
            "surface_variation_bounds_json": _json(dict(surface_variation_bounds)) if surface_variation_bounds is not None else None,
            "angle_identity_json": _json(dict(angle_identity)) if angle_identity is not None else None,
            "generator_version": generator_version,
            "gate_policy_version": gate_policy_version,
            "expected_burden_json": _json(dict(expected_burden)) if expected_burden is not None else None,
            "calibration_metadata_json": _json(dict(calibration_metadata)) if calibration_metadata is not None else None,
        },
        clock=clock,
    )


def resolve_progression_policy(
    repository: Repository, family_version_id: str
) -> dict[str, Any] | None:
    """Resolve the progression policy pinned on a family version (§3.6, §6). Returns
    the immutable policy body, or ``None`` when no policy is pinned."""

    authoring = repository.activity_family_authoring(family_version_id)
    if authoring is None:
        return None
    policy_version_id = authoring.get("progression_policy_version_id")
    if not policy_version_id:
        return None
    row = repository.progression_policy_version(policy_version_id)
    if row is None:
        return None
    return _loads(row["body_json"], {})


def inspect_angle_coverage(
    repository: Repository, family_version_id: str
) -> dict[str, Any]:
    """Inspect a family version's declared angle inventory and coverage targets
    (§5.4, §6 CLI parity). Returns empty structures when nothing is pinned."""

    authoring = repository.activity_family_authoring(family_version_id)
    if authoring is None:
        return {"angle_inventory": None, "coverage_targets": None}
    return {
        "angle_inventory": _loads(authoring.get("angle_inventory_json") or "null", None),
        "coverage_targets": _loads(authoring.get("coverage_targets_json") or "null", None),
    }
