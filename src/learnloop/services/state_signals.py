"""P4 §14.2 cutover -- live StateSignals adapters (scope item 1).

The staged policy's §4.2 ladder consumes a :class:`~learnloop.services.staged_policy.StateSignals`
object. For all of P4 steps 1-2 those signals were caller-supplied (or planted in tests).
This module supplies the LIVE adapters that derive each decision signal DETERMINISTICALLY
from real vault state -- the wiring the §14.2 cutover names explicitly.

Each adapter is a pure function of (snapshot, bounded repository reads) with an
unambiguous rule, so it is testable against planted states and it fails safe: absent
evidence yields the conservative signal (a target is NOT acquired until a milestone is
reached; no open alarm means NOT misspecified; no open diagnostic means zero decision
value; no reserve means no valid terminal reserve). Reads are per-DECISION and bounded
(not per candidate), so they sit outside the snapshot's §3.1 per-candidate query budget.

The five signals the cutover names:
- ``model_misspecified`` -- an unresolved open-set / ``other_or_unknown`` alarm
  (``probe_generation_needs`` status ``pending``) on any of the commitment's learning
  objects: the model cannot reach an action-safe conclusion (§4.2 rung 2).
- ``decision_relevant_robust_value`` -- an ``in_progress`` open diagnostic episode on a
  commitment learning object carries unresolved, decision-relevant uncertainty worth a
  positive sampling value (§4.2 rung 3).
- ``target_acquired`` -- the commitment has reached at least one depth milestone: its
  current target knowledge is acquired (§4.2 rung 4 negation).
- ``retention_near_limit`` -- a commitment card is at/over its due boundary (§4.2 rung 9).
- ``terminal_reserve_valid`` / ``terminal_required_unshown`` -- a live assessment reserve
  exists AND a terminal claim is required but not yet shown (§4.2 rung 7).
"""

from __future__ import annotations

from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.services import controller_snapshot as cs
from learnloop.services import staged_policy as sp

# A fixed positive robust sampling value assigned when an open diagnostic episode makes
# a decision-relevant uncertainty measurable (§4.2 rung 3). Heuristic decision parameter
# (design §E): its magnitude never orders anything -- the ladder rung is a boolean
# ``> 0`` gate, and within-block ranking is the robust-EVSI-per-minute selector.
OPEN_EPISODE_ROBUST_VALUE = 1.0


def _commitment_learning_object_ids(
    repository: Repository, snapshot: cs.ControllerSnapshot, commitment_id: str | None
) -> set[str]:
    """Learning objects in scope for THIS commitment's decision (audit M3/D4).

    Scoped to the commitment's HEAD TARGETS, not the whole snapshot candidate universe: a
    live run owns one commitment, and an unrelated commitment's learning object -- also
    present in the candidate universe during the cutover -- must NOT be able to fire that
    run's misspecification / decision-value signals. ``learning_object`` head targets
    contribute directly; ``legacy_practice_item`` targets are resolved to their LO through
    the snapshot candidates (which carry ``learning_object_id`` keyed by candidate ref).

    Fails open to the full candidate universe only when there is no commitment in scope or
    the head cannot be resolved -- preserving the pre-cutover behavior for those cases."""

    candidate_los = {c.learning_object_id for c in snapshot.candidates if c.learning_object_id}
    if commitment_id is None:
        return candidate_los
    from learnloop.services import commitments as C

    try:
        head = C.resolve_head(repository, commitment_id)
    except Exception:
        return candidate_los
    item_ref_to_lo = {
        c.candidate_ref: c.learning_object_id
        for c in snapshot.candidates
        if c.learning_object_id
    }
    scope: set[str] = set()
    for target in head.targets:
        if target.target_kind == "learning_object":
            scope.add(target.target_ref)
        elif target.target_kind == "legacy_practice_item":
            lo = item_ref_to_lo.get(target.target_ref)
            if lo:
                scope.add(lo)
    return scope if scope else candidate_los


def misspecification(
    repository: Repository, snapshot: cs.ControllerSnapshot, commitment_id: str | None
) -> bool:
    """True when an unresolved open-set / ``other_or_unknown`` alarm exists on any
    commitment learning object (§4.2 rung 2). A trigger is an alarm, never a diagnosis
    (invariant 9); its presence blocks an action-safe conclusion until expanded."""

    los = _commitment_learning_object_ids(repository, snapshot, commitment_id)
    if not los:
        return False
    for lo in sorted(los):
        needs = repository.probe_generation_needs(learning_object_id=lo, status="pending")
        if needs:
            return True
    return False


def decision_relevant_robust_value(
    repository: Repository, snapshot: cs.ControllerSnapshot, commitment_id: str | None
) -> float:
    """Positive when an ``in_progress`` open diagnostic episode on a commitment learning
    object carries unresolved decision-relevant uncertainty (§4.2 rung 3). ``pending_items``
    episodes leave the LO schedulable and do NOT by themselves imply measurement value;
    only an in-progress episode does."""

    los = _commitment_learning_object_ids(repository, snapshot, commitment_id)
    if not los:
        return 0.0
    open_episodes = repository.open_probe_episodes()
    for episode in open_episodes.values():
        lo = getattr(episode, "learning_object_id", None)
        status = getattr(episode, "status", None)
        if lo in los and status == "in_progress":
            return OPEN_EPISODE_ROBUST_VALUE
    return 0.0


def target_acquired(snapshot: cs.ControllerSnapshot, commitment_id: str | None) -> bool:
    """True when the commitment has reached at least one depth milestone (§4.2 rung 4
    negation). Fails safe to NOT acquired (-> instruct) until real milestone evidence
    exists."""

    if commitment_id is None:
        return True  # no commitment in scope -> nothing to instruct toward.
    commitment = snapshot.commitment(commitment_id)
    if commitment is None:
        return True
    return len(commitment.reached_milestones) > 0


def retention_near_limit(
    snapshot: cs.ControllerSnapshot, *, clock: Clock | None = None
) -> bool:
    """True when a commitment card is at or over its due boundary (§4.2 rung 9). Uses
    the candidate due state carried on the snapshot; deterministic against the decision
    clock."""

    now = utc_now_iso(clock)
    for candidate in snapshot.candidates:
        due = candidate.due_at
        if due is not None and due <= now:
            return True
    return False


def terminal_signals(
    repository: Repository,
    snapshot: cs.ControllerSnapshot,
    commitment_id: str | None,
    *,
    run_mode: str | None = None,
    terminal_shown: bool = False,
) -> tuple[bool, bool]:
    """(``terminal_required_unshown``, ``terminal_reserve_valid``) for §4.2 rung 7.

    A terminal claim is REQUIRED when the run is not ``practice_only`` (a practice-only
    run never administers a terminal assessment, §1.1) and it has not yet been shown. A
    reserve is VALID when a live assessment reservation exists in the snapshot."""

    reserve_valid = len(snapshot.reserved_assessment_surface_ids) > 0
    if run_mode == "practice_only":
        return False, reserve_valid
    required_unshown = not terminal_shown
    return required_unshown, reserve_valid


def derive_signals(
    repository: Repository,
    snapshot: cs.ControllerSnapshot,
    *,
    commitment_id: str | None,
    run_mode: str | None = None,
    terminal_shown: bool = False,
    pending_triage_route: dict[str, Any] | None = None,
    milestone_reached: str | None = None,
    milestone_evidence_receipt: dict[str, Any] | None = None,
    capability_fragile: bool = False,
    integration_failing: bool = False,
    goal_satisfied: bool = False,
    clock: Clock | None = None,
) -> sp.StateSignals:
    """Assemble a live :class:`StateSignals` from real vault state (the five deterministic
    adapters above) plus the run-supplied stage material (triage route / milestone /
    capability-fragility / integration / goal-satisfaction), which the P2 orchestration
    knows directly from its stage. The result feeds ``staged_policy.decide`` live."""

    required_unshown, reserve_valid = terminal_signals(
        repository, snapshot, commitment_id, run_mode=run_mode, terminal_shown=terminal_shown
    )
    return sp.StateSignals(
        pending_triage_route=pending_triage_route,
        model_misspecified=misspecification(repository, snapshot, commitment_id),
        decision_relevant_robust_value=decision_relevant_robust_value(
            repository, snapshot, commitment_id
        ),
        target_acquired=target_acquired(snapshot, commitment_id),
        capability_fragile=capability_fragile,
        integration_failing=integration_failing,
        terminal_required_unshown=required_unshown,
        terminal_reserve_valid=reserve_valid,
        milestone_reached=milestone_reached,
        milestone_evidence_receipt=milestone_evidence_receipt,
        retention_near_limit=retention_near_limit(snapshot, clock=clock),
        goal_satisfied=goal_satisfied,
    )
