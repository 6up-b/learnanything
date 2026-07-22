"""P1 step 9 -- dual-write cutover, narrowed by the 2026-07-19 owner decision.

The owner has decided that pre-mvp-0.8 vaults are **not** migrated: mvp-0.8+ vaults
reinitialize fresh. So the step-9 cutover no longer has to protect *legacy-vault
history* across a dual-write window. What remains, and what this module owns, is the
integrity of the **new-substrate write path** on a fresh mvp-0.8 vault:

- flipping the purpose-adapter path to be the LIVE default for mvp-0.8 vaults, while
  legacy (mvp-0.7 / mvp-0.6) vaults keep the byte-identical purpose-blind path and
  their characterization pins (:func:`purpose_adapters_live`);
- writing the complete new-substrate lineage for one administration
  (administration + exposure + observation + adapter-specific scheduling/evidence)
  as one fail-safe unit, so a fault after any write boundary never leaves a
  half-updated scheduling/evidence projection -- the spec's silent-corruption
  concern (§7.4/§7.5). A projection that cannot complete is DEFERRED to a
  deterministic rebuild over the durable raw events, never half-applied
  (:func:`submit_administration_response`, :func:`rebuild_deferred_projection`);
- the six ordered §7.4 cutover gates, evaluated as a hard sequential barrier in
  their narrowed form -- legacy-row *equivalence* gates are N/A by owner decision;
  new-substrate write-completeness / atomicity / failure / rollback gates stay
  fully live (:func:`run_cutover_gates`).

This module never raises into the attempt writer (except invariant 8's
:class:`OpportunisticDiagnosisRejected`, which must always propagate).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services import administration_adapters as _adapters
from learnloop.services.administration_adapters import OpportunisticDiagnosisRejected
from learnloop.services.assessment_contracts import (
    CANONICAL_STATE_VERSIONS,
    KM_ALGORITHM_VERSION,
    P0_ALGORITHM_VERSION,
)

# The scheduler-algorithm version stamped on P1 card-lineage state. Distinct from the
# vault projection version so legacy replay under the old version stays byte-identical.
P1_SCHEDULER_ALGORITHM_VERSION = "fsrs6"

# The vault projection version from which the purpose-adapter scheduling path is the
# LIVE default (registry: ``substrate_cutover:PURPOSE_ADAPTERS_LIVE_FROM``). This is the
# code binding for that registered structural param: :func:`purpose_adapters_live`
# consumes it, so the registry entry names a constant the cutover decision actually
# reads. Legacy vaults (any earlier version) keep the purpose-blind path.
PURPOSE_ADAPTERS_LIVE_FROM = P0_ALGORITHM_VERSION


# ---------------------------------------------------------------------------
# The gate flip: purpose adapters are LIVE for mvp-0.8, legacy for older vaults.
# ---------------------------------------------------------------------------

def purpose_adapters_live(algorithm_version: str | None) -> bool:
    """Whether the purpose-adapter path is the LIVE scheduling authority for a vault.

    Live for mvp-0.8 (:data:`P0_ALGORITHM_VERSION`) -- the fresh-vault default after
    the owner decision. Legacy vaults (mvp-0.7 / mvp-0.6, or an unknown/None version)
    keep the purpose-blind hot-path FSRS write and their characterization pins. The
    module-level :data:`administration_adapters.P1_PURPOSE_ADAPTERS_ENABLED` remains
    a global test override that forces the adapter path ON regardless of version.
    """

    if _adapters.P1_PURPOSE_ADAPTERS_ENABLED:
        return True
    return algorithm_version == PURPOSE_ADAPTERS_LIVE_FROM


def scheduling_write_authority(algorithm_version: str | None) -> str:
    """``'purpose_adapter'`` for a live mvp-0.8 vault, else ``'legacy_fsrs'`` (§7.4
    gate 6: new-administration scheduling can only be written through the adapter on
    a live vault; a direct legacy write for a new administration is rejected)."""

    return "purpose_adapter" if purpose_adapters_live(algorithm_version) else "legacy_fsrs"


class LegacyWriteRejected(Exception):
    """§7.4 gate 6: a direct legacy scheduling write was attempted for a new
    administration on a live mvp-0.8 vault. New-administration scheduling can only be
    written through the purpose adapter."""


def reject_legacy_scheduling_write(algorithm_version: str | None, *, administration_id: str) -> None:
    """Guard the new-substrate write path (§7.4 gate 6). On a live vault, refuse any
    attempt to write scheduling for a new administration outside the purpose adapter."""

    if purpose_adapters_live(algorithm_version):
        raise LegacyWriteRejected(
            f"new administration {administration_id!r} must write scheduling through the "
            "purpose adapter, not the legacy path"
        )


def guarded_legacy_scheduling_write(
    repository: Repository,
    *,
    algorithm_version: str | None,
    administration_id: str,
    card_lineage_id: str,
    scheduler_algorithm_version: str = P1_SCHEDULER_ALGORITHM_VERSION,
    difficulty: float | None = None,
    stability: float | None = None,
    retrievability: float | None = None,
    due_at: str | None = None,
    model_label: str = "fsrs",
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """The service-layer CHOKEPOINT that gate 6 enforces (§7.4 gate 6).

    Every legacy-path (non-adapter) scheduling write for a card lineage must pass
    through here. On a LIVE mvp-0.8 vault the guard fires BEFORE any row is written, so
    a direct legacy ``activity_card_state`` write for a new-substrate administration is
    actually prevented -- not merely flagged. On a legacy vault the write proceeds
    (that path keeps its byte-identical legacy scheduler). The adapter path
    (:meth:`PracticeAdapter.apply_scheduling`) is the ONLY sanctioned scheduling write
    on a live vault and never routes through this function."""

    reject_legacy_scheduling_write(algorithm_version, administration_id=administration_id)
    repository.upsert_activity_card_state(
        card_lineage_id=card_lineage_id,
        scheduler_algorithm_version=scheduler_algorithm_version,
        model_label=model_label,
        difficulty=difficulty,
        stability=stability,
        retrievability=retrievability,
        due_at=due_at,
        clock=clock,
    )
    return repository.activity_card_state(
        card_lineage_id=card_lineage_id,
        scheduler_algorithm_version=scheduler_algorithm_version,
    )


# ---------------------------------------------------------------------------
# The complete new-substrate lineage write (fail-safe, one unit).
# ---------------------------------------------------------------------------

class InjectedFault(Exception):
    """A fault injected by the fault-injection test after a named write boundary."""


# Ordered write boundaries of one administration transaction (§7.4). ``administration``
# (which atomically also writes the once-only ``rendered`` exposure) is the burn
# boundary; the response-side boundaries follow; ``projection`` is the only derived
# write and the only one that must never half-update (§7.5).
WRITE_BOUNDARIES: tuple[str, ...] = ("administration", "exposure", "observation", "projection")


@dataclass(frozen=True)
class SubstrateWriteReceipt:
    administration_id: str | None
    exposure_event_id: str | None
    observation_id: str | None
    card_state: dict[str, Any] | None
    boundaries_completed: tuple[str, ...]
    deferred: bool
    rebuild_id: str | None
    error: str | None = None

    @property
    def complete(self) -> bool:
        return not self.deferred and self.error is None

    def as_dict(self) -> dict[str, Any]:
        return {
            "administration_id": self.administration_id,
            "exposure_event_id": self.exposure_event_id,
            "observation_id": self.observation_id,
            "card_state": self.card_state,
            "boundaries_completed": list(self.boundaries_completed),
            "deferred": self.deferred,
            "rebuild_id": self.rebuild_id,
            "error": self.error,
        }


def _existing_observation(repository: Repository, administration_id: str) -> dict[str, Any] | None:
    rows = repository.observations_for_administration(administration_id)
    return rows[0] if rows else None


def submit_administration_response(
    repository: Repository,
    *,
    surface: Mapping[str, Any],
    card_version_id: str,
    family_id: str,
    purpose: str,
    card_lineage_id: str,
    algorithm_version: str,
    scheduler_algorithm_version: str = P1_SCHEDULER_ALGORITHM_VERSION,
    review_event: Mapping[str, Any] | None,
    eligible: bool,
    failed: bool,
    attempt_id: str | None = None,
    response_ref: str | None = None,
    feedback_condition: str | None = None,
    admin_context: Mapping[str, Any] | None = None,
    reading_phase: str | None = None,
    snapshot_hash: str | None = None,
    snapshot_json: str = "{}",
    prior_reviews: Sequence[Mapping[str, Any]] = (),
    fault_after: Sequence[str] = (),
    clock: Clock | None = None,
) -> SubstrateWriteReceipt:
    """Write the complete new-substrate lineage for one administration as ONE
    fail-safe unit (§7.4): administration (+ once-only rendered exposure) -> submitted
    exposure -> observation -> adapter-specific scheduling/evidence projection.

    Fail-safe posture (§7.5, silent-corruption concern): each raw event write is
    individually durable and idempotent (render-once for the administration; a
    guard skips a duplicate submitted exposure / observation on retry). The scheduling
    PROJECTION is the only derived write and the only one that must never half-update:
    on any fault before or during it, the durable raw events are preserved, a
    deterministic rebuild is enqueued in ``derived_state_rebuilds``, and the receipt
    reports ``deferred=True``. This function never raises into the attempt writer
    (except :class:`OpportunisticDiagnosisRejected`).

    ``fault_after`` is the fault-injection hook: a fault is raised immediately after
    each named boundary in :data:`WRITE_BOUNDARIES`, proving no boundary leaves a
    half-updated projection.
    """

    from learnloop.services import activities as _activities

    import json as _json_mod

    faults = frozenset(fault_after)
    consumes_unseen = purpose in ("assessment", "diagnostic")
    evidence_eligibility, eligibility_reason = _activities.evidence_eligibility_for(
        purpose=purpose, feedback_condition=feedback_condition
    )
    # The response's FSRS review (rating + elapsed) and failed flag are persisted into
    # the raw-event ledger (the response_appended measurement) so a deferred projection
    # can be re-derived from durable events alone, never from caller-supplied evidence.
    response_ledger = {
        "review_event": (
            {"rating": int(review_event["rating"]), "elapsed_days": float(review_event.get("elapsed_days", 0.0))}
            if review_event is not None
            else None
        ),
        "failed": bool(failed),
        "scheduler_algorithm_version": scheduler_algorithm_version,
    }

    # (1) the RAW-EVENT lineage as ONE transaction: administration (+ its context, so no
    # NULL-context window) + rendered/submitted exposures + observation + measurement
    # events. A fault before commit rolls back the WHOLE unit -- nothing is left
    # half-written -- so the ONLY write that can ever defer is the projection below.
    try:
        lineage = repository.write_administration_lineage_atomic(
            surface_id=surface["id"],
            card_version_id=card_version_id,
            family_id=family_id,
            purpose=purpose,
            surface_hash=surface["surface_hash"],
            fingerprint=surface.get("fingerprint"),
            snapshot_hash=snapshot_hash or f"snap-{surface['surface_hash']}",
            snapshot_json=snapshot_json,
            consumes_unseen=consumes_unseen,
            algorithm_version=algorithm_version,
            evidence_eligibility=evidence_eligibility,
            eligibility_reason=eligibility_reason,
            reading_phase=reading_phase,
            admin_context=admin_context,
            attempt_id=attempt_id,
            response_ref=response_ref,
            response_ledger_json=_json_mod.dumps(response_ledger, sort_keys=True),
            fault_after=faults & {"administration", "exposure"},
            clock=clock,
        )
    except Exception as exc:  # noqa: BLE001 -- fail-safe: never raise into the attempt writer
        # The raw-event transaction rolled back: NOTHING was written, so there is nothing
        # to rebuild. A retry (recovery) re-runs cleanly and completes.
        return SubstrateWriteReceipt(
            administration_id=None,
            exposure_event_id=None,
            observation_id=None,
            card_state=None,
            boundaries_completed=(),
            deferred=True,
            rebuild_id=None,
            error=str(exc),
        )

    administration_id = lineage["administration_id"]
    exposure_event_id = lineage["submitted_exposure_id"]
    observation_id = lineage["observation_id"]
    completed = ["administration", "exposure", "observation"]

    # A post-commit fault before the projection: the raw events are durable; the
    # projection is DEFERRED to a deterministic rebuild over the ledger (§7.5).
    if "observation" in faults:
        rebuild_id = _enqueue_rebuild(repository, administration_id, scheduler_algorithm_version, clock)
        return SubstrateWriteReceipt(
            administration_id=administration_id,
            exposure_event_id=exposure_event_id,
            observation_id=observation_id,
            card_state=None,
            boundaries_completed=tuple(completed),
            deferred=True,
            rebuild_id=rebuild_id,
            error="injected fault after boundary: observation",
        )

    # (2) scheduling/evidence projection -- adapter selected by IMMUTABLE purpose, never
    # attempt_type/route. This is the ONLY derived write and the only one that may defer.
    try:
        projection = _adapters.project_administration(
            repository,
            administration_id=administration_id,
            eligible=eligible,
            failed=failed,
            card_lineage_id=card_lineage_id,
            scheduler_algorithm_version=scheduler_algorithm_version,
            review_event=review_event,
            prior_reviews=prior_reviews,
            clock=clock,
        )
    except OpportunisticDiagnosisRejected:
        raise
    except Exception as exc:  # noqa: BLE001 -- fail-safe: raw events durable, defer projection
        rebuild_id = _enqueue_rebuild(repository, administration_id, scheduler_algorithm_version, clock)
        return SubstrateWriteReceipt(
            administration_id=administration_id, exposure_event_id=exposure_event_id,
            observation_id=observation_id, card_state=None, boundaries_completed=tuple(completed),
            deferred=True, rebuild_id=rebuild_id, error=str(exc),
        )

    if projection.deferred:
        # The adapter's own fail-safe caught a projection error; enqueue the rebuild
        # rather than persisting a half-updated card state.
        rebuild_id = _enqueue_rebuild(repository, administration_id, scheduler_algorithm_version, clock)
        return SubstrateWriteReceipt(
            administration_id=administration_id, exposure_event_id=exposure_event_id,
            observation_id=observation_id, card_state=None, boundaries_completed=tuple(completed),
            deferred=True, rebuild_id=rebuild_id, error=projection.error,
        )

    card_state = projection.card_state
    if "projection" in faults:
        # A fault AFTER the projection committed: the card state IS durable, but we still
        # enqueue a rebuild (deferred) so recovery is idempotent -- never a half-update.
        rebuild_id = _enqueue_rebuild(repository, administration_id, scheduler_algorithm_version, clock)
        return SubstrateWriteReceipt(
            administration_id=administration_id, exposure_event_id=exposure_event_id,
            observation_id=observation_id, card_state=card_state, boundaries_completed=tuple(completed),
            deferred=True, rebuild_id=rebuild_id, error="injected fault after boundary: projection",
        )

    completed.append("projection")
    return SubstrateWriteReceipt(
        administration_id=administration_id,
        exposure_event_id=exposure_event_id,
        observation_id=observation_id,
        card_state=card_state,
        boundaries_completed=tuple(completed),
        deferred=False,
        rebuild_id=None,
    )


def _enqueue_rebuild(
    repository: Repository, administration_id: str, scheduler_algorithm_version: str, clock: Clock | None
) -> str:
    return repository.record_derived_state_rebuild(
        scope="activity_card_state",
        learning_object_ids=[administration_id],
        algorithm_version=scheduler_algorithm_version,
        rebuilt_learning_objects=0,
        replayed_attempts=0,
        clock=clock,
    )


class NoObservationToRebuild(Exception):
    """A deferred-projection rebuild was requested for an administration that has no
    durable observation in the ledger. There is nothing to project (§7.5): a projection
    may never be written without an observation to derive it from."""


def rebuild_deferred_projection(
    repository: Repository,
    *,
    administration_id: str,
    card_lineage_id: str,
    scheduler_algorithm_version: str = P1_SCHEDULER_ALGORITHM_VERSION,
    prior_reviews: Sequence[Mapping[str, Any]] = (),
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Deterministically reapply the scheduling/evidence projection for a deferred
    administration by RE-DERIVING its inputs from the durable ledger (§7.5) -- never
    from caller-supplied evidence:

    - eligibility comes from the observation's recorded ``evidence_eligibility``;
    - the FSRS review (rating/elapsed) and failed flag come from the persisted
      ``response_appended`` measurement event.

    Refuses (raises :class:`NoObservationToRebuild`) when no observation exists: a
    projection may never be written without an observation to derive it from. Idempotent:
    the card-state upsert is keyed by learner x lineage x scheduler version."""

    import json as _json_mod

    observation = _existing_observation(repository, administration_id)
    if observation is None:
        raise NoObservationToRebuild(
            f"administration {administration_id!r} has no observation; nothing to project"
        )

    eligible = observation.get("evidence_eligibility") == "practice"

    review_event: Mapping[str, Any] | None = None
    failed = False
    for event in repository.measurement_events_for_administration(administration_id):
        if event.get("kind") != "response_appended" or not event.get("payload_json"):
            continue
        payload = _json_mod.loads(event["payload_json"])
        review_event = payload.get("review_event")
        failed = bool(payload.get("failed", False))
        break

    projection = _adapters.project_administration(
        repository,
        administration_id=administration_id,
        eligible=eligible,
        failed=failed,
        card_lineage_id=card_lineage_id,
        scheduler_algorithm_version=scheduler_algorithm_version,
        review_event=review_event,
        prior_reviews=prior_reviews,
        clock=clock,
    )
    return projection.card_state


# ---------------------------------------------------------------------------
# The six ordered cutover gates (§7.4), narrowed by the owner decision.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GateOutcome:
    ordinal: int
    name: str
    status: str  # "pass" | "na_owner_decision" | "fail"
    spec_ref: str
    detail: str

    @property
    def cleared(self) -> bool:
        return self.status in ("pass", "na_owner_decision")

    def as_dict(self) -> dict[str, Any]:
        return {
            "ordinal": self.ordinal,
            "name": self.name,
            "status": self.status,
            "spec_ref": self.spec_ref,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class CutoverGateReport:
    algorithm_version: str
    gates: tuple[GateOutcome, ...]
    barrier_ok: bool

    @property
    def all_cleared(self) -> bool:
        return all(g.cleared for g in self.gates)

    def as_dict(self) -> dict[str, Any]:
        return {
            "algorithm_version": self.algorithm_version,
            "barrier_ok": self.barrier_ok,
            "all_cleared": self.all_cleared,
            "gates": [g.as_dict() for g in self.gates],
        }


# Expected §3.10 purpose-matrix deltas (gate 4). The one place the adapter contract is
# asserted end-to-end for the cutover report.
_PURPOSE_MATRIX = {
    "diagnostic": dict(updates_practice_schedule=False, applies_fsrs_review=False),
    "instructional": dict(updates_practice_schedule=False, applies_fsrs_review=False),
    "practice": dict(updates_practice_schedule=True, applies_fsrs_review=True),
    "assessment": dict(updates_practice_schedule=False, applies_fsrs_review=False),
}


def _gate_purpose_side_effects() -> tuple[str, str]:
    """Gate 4 (LIVE): the §9.4 purpose matrix -- the same synthetic response under each
    purpose produces the exact §3.10 scheduling delta."""

    for purpose, expected in _PURPOSE_MATRIX.items():
        eff = _adapters.resolve_adapter(purpose).effects(eligible=True, failed=False)
        if not eff.records_full_exposure:
            return "fail", f"{purpose}: full exposure not recorded"
        for key, value in expected.items():
            if getattr(eff, key) != value:
                return "fail", f"{purpose}.{key} != {value}"
    return "pass", "four purpose adapters produce the exact §3.10 deltas (live)"


def _gate3_probe_lineage(repository: Repository, clock: Clock | None) -> str:
    """A throwaway practice card + lineage the gate 3 drive can project onto."""

    from learnloop.services import activities as _activities
    from learnloop.services import card_lineage as _lineage

    contract = {"target": "__gate3_probe__", "capability": "retrieval"}
    family_id = repository.ensure_activity_family(
        purpose="practice", legacy_kind=None, title="__gate3_probe__", clock=clock
    )
    card_id = repository.ensure_activity_card(family_id=family_id, clock=clock)
    cv = repository.ensure_activity_card_version(
        card_id=card_id, version=1,
        card_contract_hash=_activities._canonical_hash(contract),
        contract_json=_activities._json(contract), schema_version=1, clock=clock,
    )
    existing = repository.lineage_for_card_version(cv)
    if existing is not None:
        return existing
    return _lineage.start_lineage(
        repository, genesis_card_version_id=cv, family_id=family_id, card_id=card_id, clock=clock
    )


def _gate_new_scheduling_projection(
    repository: Repository, algorithm_version: str, clock: Clock | None
) -> tuple[str, str]:
    """Gate 3 (LIVE, reframed): the NARROWED scope drops legacy-row equivalence. What
    stays live is new-substrate write completeness -- the practice adapter's card-state
    projection, DRIVEN and persisted, reproduces an INDEPENDENT FSRS transition computed
    over the same review stream by a separate code path (a hand fold over
    :func:`fsrs.apply_review`, never the adapter's own :func:`replay_review_events`)."""

    from learnloop.services.fsrs import FSRS6_DEFAULT_WEIGHTS, Rating, apply_review

    reviews = [{"rating": Rating.GOOD, "elapsed_days": 0.0}, {"rating": Rating.GOOD, "elapsed_days": 1.0}]
    lineage_id = _gate3_probe_lineage(repository, clock)
    # Drive the REAL practice adapter -> it persists activity_card_state via rebuild.
    card_state = _adapters.PracticeAdapter().apply_scheduling(
        repository,
        card_lineage_id=lineage_id,
        scheduler_algorithm_version=P1_SCHEDULER_ALGORITHM_VERSION,
        review_event=reviews[-1],
        eligible=True,
        prior_reviews=reviews[:-1],
        weights=FSRS6_DEFAULT_WEIGHTS,
        clock=clock,
    )
    # Independent transition (separate code path): fold apply_review by hand.
    memory = None
    for review in reviews:
        memory = apply_review(memory, review["rating"], review["elapsed_days"], FSRS6_DEFAULT_WEIGHTS)
    if card_state is None or card_state.get("stability") is None:
        return "fail", "adapter scheduling projection produced no persisted stability"
    if memory is None or memory.stability is None:
        return "fail", "independent FSRS transition produced no stability"
    if abs(float(card_state["stability"]) - float(memory.stability)) > 1e-9:
        return "fail", (
            f"adapter stability {card_state['stability']} != independent {memory.stability}"
        )
    return "pass", "driven adapter card-state projection matches an independent FSRS transition (live)"


def _gate_legacy_writes_rejected(
    repository: Repository, algorithm_version: str, clock: Clock | None
) -> tuple[str, str]:
    """Gate 6 (LIVE): enforced at the service-layer CHOKEPOINT
    (:func:`guarded_legacy_scheduling_write`). On a live vault a direct legacy
    card-state write for a NEW administration is prevented BEFORE any row is written; the
    gate drives that chokepoint against a real lineage and asserts both that it raises
    AND that no card state was persisted (a genuinely blocked write, not a bare flag)."""

    if not purpose_adapters_live(algorithm_version):
        return "na_owner_decision", "legacy vault keeps the legacy write path (not a live mvp-0.8 vault)"
    lineage_id = _gate3_probe_lineage(repository, clock)
    before = repository.activity_card_state(
        card_lineage_id=lineage_id, scheduler_algorithm_version=P1_SCHEDULER_ALGORITHM_VERSION
    )
    try:
        guarded_legacy_scheduling_write(
            repository,
            algorithm_version=algorithm_version,
            administration_id="probe",
            card_lineage_id=lineage_id,
            stability=999.0,
            clock=clock,
        )
    except LegacyWriteRejected:
        after = repository.activity_card_state(
            card_lineage_id=lineage_id, scheduler_algorithm_version=P1_SCHEDULER_ALGORITHM_VERSION
        )
        after_stability = after.get("stability") if after is not None else None
        before_stability = before.get("stability") if before is not None else None
        if after_stability != before_stability:
            return "fail", "legacy write mutated card state before the guard fired"
        return "pass", "direct legacy scheduling write is blocked at the chokepoint (no row written, live)"
    return "fail", "legacy write was not rejected on a live vault"


def run_cutover_gates(
    repository: Repository,
    *,
    algorithm_version: str,
    clock: Clock | None = None,
) -> CutoverGateReport:
    """Evaluate the six §7.4 cutover gates as a hard sequential barrier, narrowed by the
    2026-07-19 owner decision (no old-vault migration): legacy-row *equivalence* gates
    are N/A; new-substrate write-completeness / atomicity / failure / rollback gates
    stay fully live. A gate is evaluated only if every prior gate cleared."""

    live = purpose_adapters_live(algorithm_version)
    # Each entry lazily produces (status, detail) so a later gate is only evaluated once
    # its predecessors cleared (the sequential barrier, §7.4 tail).
    specs: list[tuple[str, str, Any]] = [
        (
            "identity_mapping_coverage_100pct",
            "§7.4.1/§7.2/§9.5",
            lambda: (
                "na_owner_decision",
                "fresh mvp-0.8 vaults reinitialize; no legacy PracticeItem backfill to cover "
                "(owner decision 2026-07-19). Frozen backfill machinery kept green, not extended.",
            ),
        ),
        (
            "historical_replay_equivalence",
            "§7.4.2/§9.5",
            lambda: (
                "na_owner_decision",
                "byte-identical probe/exam replay is a frozen legacy characterization "
                "(test_characterization_probe_replay); not a new-vault write-path concern.",
            ),
        ),
        (
            "new_scheduling_projection_correct",
            "§7.4.3",
            lambda: _gate_new_scheduling_projection(repository, algorithm_version, clock),
        ),
        (
            "purpose_side_effects",
            "§7.4.4/§9.4",
            _gate_purpose_side_effects,
        ),
        (
            "legacy_scheduler_reads_compat_state",
            "§7.4.5",
            lambda: (
                "na_owner_decision",
                "legacy practice_item_state compatibility read path is frozen legacy machinery "
                "(owner decision 2026-07-19); a fresh mvp-0.8 vault has no legacy scheduler reader.",
            ),
        ),
        (
            "legacy_writes_rejected_for_new_admin",
            "§7.4.6",
            lambda: _gate_legacy_writes_rejected(repository, algorithm_version, clock),
        ),
    ]

    outcomes: list[GateOutcome] = []
    barrier_ok = True
    prior_cleared = True
    for ordinal, (name, ref, fn) in enumerate(specs, start=1):
        if not prior_cleared:
            # The barrier stops: an un-cleared gate blocks every later gate.
            outcomes.append(GateOutcome(ordinal, name, "fail", ref, "blocked: a prior gate did not clear"))
            barrier_ok = False
            continue
        status, detail = fn()
        outcome = GateOutcome(ordinal, name, status, ref, detail)
        outcomes.append(outcome)
        if not outcome.cleared:
            prior_cleared = False
            barrier_ok = False

    return CutoverGateReport(algorithm_version=algorithm_version, gates=tuple(outcomes), barrier_ok=barrier_ok)


# Convenience re-exports for callers/tests.
__all__ = [
    "P1_SCHEDULER_ALGORITHM_VERSION",
    "PURPOSE_ADAPTERS_LIVE_FROM",
    "P0_ALGORITHM_VERSION",
    "KM_ALGORITHM_VERSION",
    "CANONICAL_STATE_VERSIONS",
    "purpose_adapters_live",
    "scheduling_write_authority",
    "reject_legacy_scheduling_write",
    "guarded_legacy_scheduling_write",
    "LegacyWriteRejected",
    "InjectedFault",
    "WRITE_BOUNDARIES",
    "SubstrateWriteReceipt",
    "submit_administration_response",
    "rebuild_deferred_projection",
    "NoObservationToRebuild",
    "GateOutcome",
    "CutoverGateReport",
    "run_cutover_gates",
]
