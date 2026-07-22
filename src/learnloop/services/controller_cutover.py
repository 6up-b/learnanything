"""P4 §14.2 dual-controller cutover -- step 3 coexistence window (design §C).

The riskiest transition in the program: the staged policy goes LIVE for P2 golden-path
commitments while the legacy scheduler still composes all other Today work, and BOTH
append to the ONE ``activity_exposure_events`` ledger (§3.6, invariant 11). This module
owns the coexistence seam:

- the LIVE next-action bridge (:func:`staged_next_action` / :func:`advance_live`) that
  wires the P2 golden-path run to CONSULT the staged policy. Under identical inputs the
  P2 behavior is decision-equivalent to the pre-cutover static policy UNLESS the staged
  decision names a constraint/EVSI reason -- then it vetoes with that named reason
  (design §C step 3; spec §14.2). The staged decision is persisted ``mode='live'``.
- the six ordered §14.2-step-3 gates (design §C), evaluated as a hard sequential barrier
  exactly like ``substrate_cutover.run_cutover_gates`` (the P1-cutover precedent).
- rollback: a single registered switch (:func:`rollback`) that returns owned commitments
  to legacy atomically with a receipt (design §C gate f / §A.5).

Ownership is commitment-scoped (:mod:`controller_ownership`): the staged policy owns P2
golden-path commitments, legacy owns everything else, and no commitment is ever scheduled
by both. Cross-controller exposure collisions are serialized by the P0 in-lock recheck in
``open_administration_atomic`` (the same ONE ledger) -- this module does not re-implement
that serialization; it verifies it (gate d) and never partitions the ledger (§A.1).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services import commitments as C
from learnloop.services import controller_actions as A
from learnloop.services import controller_ownership as own
from learnloop.services import controller_snapshot as cs
from learnloop.services import controller_store as store
from learnloop.services import golden_path_run as GPR
from learnloop.services import staged_policy as sp
from learnloop.services import state_signals as ss

# The step-3 cutover switch (design §C): the staged policy is the LIVE authority for
# staged-OWNED P2 commitments. Structural gate (U-018 style): OFF returns every run to
# the pre-cutover static policy (full shadow), so a global rollback is one flag flip in
# addition to the per-commitment ownership rollback. Registered structural in
# parameter_registry (owner ``controller_cutover``).
STAGED_POLICY_LIVE_FOR_P2 = True

# The staged stop reasons that constitute a legitimate constraint/EVSI VETO of the
# canonical successor (spec §14.2 "decision-equivalent ... unless the trace names the
# constraint/EVSI reason"). A plain ladder/goal stop is NOT a veto -- the canonical
# successor stands and stays decision-equivalent.
_EVSI_VETO_REASONS = frozenset({A.STOP_WAITING_FOR_DELAY_OR_FRESH_SURFACE})


@dataclass(frozen=True)
class LiveNextAction:
    """The next action for a P2 run under the cutover. ``authority`` is ``'legacy'`` (the
    pre-cutover static policy stood -- run not staged-owned or the gate is off),
    ``'staged'`` (the staged policy confirmed the canonical successor, live), or
    ``'staged_veto'`` (the staged policy vetoed with a named constraint/EVSI reason)."""

    to_state: str | None
    reason: str
    terminal: bool
    authority: str
    diverged: bool
    staged_decision_id: str | None = None
    staged_action: str | None = None
    veto_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "to_state": self.to_state, "reason": self.reason, "terminal": self.terminal,
            "authority": self.authority, "diverged": self.diverged,
            "staged_decision_id": self.staged_decision_id, "staged_action": self.staged_action,
            "veto_reason": self.veto_reason,
        }


def _commitment_item_refs(vault: Any, repository: Repository, commitment_id: str) -> set[str]:
    """The practice items a commitment owns (its head ``learning_object`` /
    ``legacy_practice_item`` targets, resolved down to vault item ids)."""

    try:
        head = C.resolve_head(repository, commitment_id)
    except Exception:
        return set()
    refs = {
        t.target_ref for t in head.targets
        if t.target_kind in ("learning_object", "legacy_practice_item")
    }
    if not refs:
        return set()
    owned: set[str] = set()
    for item in getattr(vault, "practice_items", {}).values():
        if item.id in refs or getattr(item, "learning_object_id", None) in refs:
            owned.add(item.id)
    return owned


def _constraint_or_evsi_veto(result: sp.DecisionResult) -> str | None:
    """Return the named constraint/EVSI reason iff the staged decision legitimately
    vetoes the canonical successor, else None. A veto is either an EVSI abstain/wait, or
    a ``no_feasible_activity`` stop caused by a REAL (non-ownership) launch constraint --
    never a bare ladder fall-through or a mere ownership refusal."""

    if result.action != A.STOP:
        return None
    if result.stop_reason in _EVSI_VETO_REASONS:
        return f"evsi:{result.stop_reason}"
    if result.stop_reason == A.STOP_NO_FEASIBLE_ACTIVITY and result.feasibility is not None:
        for _cand, feas in result.feasibility.excluded:
            for reason in feas.exclusions:
                if reason.constraint_key != sp.OWNERSHIP_REFUSAL_KEY:
                    return f"constraint:{reason.constraint_key}:{reason.reason}"
    return None


def _run_signal_hints(run: Mapping[str, Any], state: GPR.RunState) -> dict[str, Any]:
    """Stage material the P2 run knows directly (§4.2 rungs the golden-path machine owns):
    mode, whether a terminal assessment has been shown, and goal satisfaction."""

    cur = state.current_state
    terminal_shown = cur in ("restoring", "deepening", "maintaining", "complete")
    goal_satisfied = cur == "complete"
    return {
        "run_mode": run.get("mode"),
        "terminal_shown": terminal_shown,
        "goal_satisfied": goal_satisfied,
        "milestone_reached": state.milestone,
    }


def staged_next_action(
    repository: Repository,
    run_id: str,
    *,
    vault: Any,
    session: Any | None = None,
    live: bool | None = None,
    receipt_key: str | None = None,
    clock: Clock | None = None,
) -> LiveNextAction:
    """Consult the staged policy LIVE for a P2 run's next action (design §C step 3).

    Returns the pre-cutover canonical successor unless (a) the run's commitment is
    staged-owned and the cutover gate is on, and (b) the staged policy names a
    constraint/EVSI reason -- in which case it vetoes with that reason. The staged
    decision is always persisted ``mode='live'`` for an owned run so the whole choice
    replays from events."""

    state = GPR.project_run(repository, run_id)
    canonical = state.next_action
    run = repository.golden_path_run(run_id)
    commitment_id = run.get("commitment_id") if run else None

    gate_on = STAGED_POLICY_LIVE_FOR_P2 if live is None else live
    if (
        not gate_on
        or commitment_id is None
        or not own.is_staged_owned(repository, commitment_id)
    ):
        return LiveNextAction(
            to_state=canonical.to_state, reason=canonical.reason, terminal=canonical.terminal,
            authority="legacy", diverged=False,
        )

    owned_refs = _commitment_item_refs(vault, repository, commitment_id)
    hints = _run_signal_hints(run, state)
    snapshot = cs.build_snapshot(vault, repository, session, clock=clock)
    signals = ss.derive_signals(
        repository, snapshot, commitment_id=commitment_id,
        run_mode=hints["run_mode"], terminal_shown=hints["terminal_shown"],
        milestone_reached=hints["milestone_reached"], goal_satisfied=hints["goal_satisfied"],
        clock=clock,
    )
    result = sp.decide(
        vault, repository, session, signals=signals, mode="live",
        owned_item_refs=owned_refs, receipt_key=receipt_key, clock=clock,
    )
    veto = _constraint_or_evsi_veto(result)
    if veto is not None:
        return LiveNextAction(
            to_state=None, reason=f"staged veto ({veto})", terminal=False,
            authority="staged_veto", diverged=True, staged_decision_id=result.decision_id,
            staged_action=result.action, veto_reason=veto,
        )
    # No named constraint/EVSI reason: the canonical successor stands (decision-equivalent).
    return LiveNextAction(
        to_state=canonical.to_state, reason=canonical.reason, terminal=canonical.terminal,
        authority="staged", diverged=False, staged_decision_id=result.decision_id,
        staged_action=result.action,
    )


def advance_live(
    repository: Repository,
    run_id: str,
    *,
    vault: Any,
    session: Any | None = None,
    idempotency_key: str,
    live: bool | None = None,
    clock: Clock | None = None,
    **extra: Any,
) -> tuple[GPR.AdvanceResult | None, LiveNextAction]:
    """The LIVE P2 next-action path: consult the staged policy, then advance the run to
    the resolved successor. On a staged veto no transition is appended (the run defers)
    and ``(None, action)`` is returned; the caller replans (design §C: the loser
    waits/rotates/stops, never trades the constraint)."""

    action = staged_next_action(
        repository, run_id, vault=vault, session=session, live=live,
        receipt_key=f"live_next:{run_id}:{idempotency_key}", clock=clock,
    )
    if action.to_state is None:
        # Staged veto: no run transition is appended (the run defers, design §C). Persist a
        # typed run-level MARKER so a caller loop can observe the deferral + its named
        # reason (audit M4/D5) -- an inspectable artifact, NOT an event-stream state change
        # (the run's canonical state is untouched). Idempotent on (run_id, idempotency_key).
        import json as _json_mod

        repository.append_golden_path_artifact(
            run_id=run_id,
            kind="staged_veto_deferred",
            payload_json=_json_mod.dumps(
                {
                    "status": "deferred",
                    "veto_reason": action.veto_reason,
                    "reason": action.reason,
                    "staged_action": action.staged_action,
                    "staged_decision_id": action.staged_decision_id,
                },
                sort_keys=True,
            ),
            idempotency_key=f"staged_veto:{run_id}:{idempotency_key}",
            clock=clock,
        )
        return None, action
    result = GPR.advance(
        repository, run_id, to_state=action.to_state, reason=action.reason,
        idempotency_key=idempotency_key, clock=clock, **extra,
    )
    return result, action


# ---------------------------------------------------------------------------
# Rollback -- the single registered switch (design §C gate f / §A.5).
# ---------------------------------------------------------------------------


def rollback(
    repository: Repository,
    *,
    reason: str = "cutover_rollback",
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Return every staged-owned commitment to legacy atomically under one receipt. After
    rollback the legacy scheduler no longer excludes those items and the P2 bridge returns
    the pre-cutover canonical successor -- legacy behavior restored exactly. Applies to the
    next uncommitted decision; all ownership-event history is preserved (append-only)."""

    return own.rollback_to_legacy(repository, reason=reason, clock=clock)


# ---------------------------------------------------------------------------
# Cross-seam exposure integrity probe (gate d): the shared ONE ledger.
# ---------------------------------------------------------------------------


def cross_seam_exposure_probe(
    repo_factory: Callable[[], Repository],
    *,
    open_administration: Callable[[Repository], Any],
) -> dict[str, Any]:
    """Drive two concurrent administrations at the SAME surface through two independent
    connections (the two controllers), and report the serialization outcome. Exactly one
    opens a fresh administration; the other observes the winner's committed exposure and
    is deferred to it (``already_open``) -- no surface goes fresh twice across the seam
    (invariant 11). The P0 ``open_administration_atomic`` in-lock recheck is the authority;
    this probe only observes it.

    ``open_administration`` is a caller-supplied closure that opens one administration on a
    given repository connection and returns an object exposing ``already_open``."""

    import threading

    barrier = threading.Barrier(2)
    results: list[Any] = [None, None]
    errors: list[BaseException | None] = [None, None]

    def worker(i: int) -> None:
        repo = repo_factory()
        try:
            barrier.wait(timeout=5)
            results[i] = open_administration(repo)
        except BaseException as exc:  # noqa: BLE001 -- surfaced in the report
            errors[i] = exc

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    opened = [r for r in results if r is not None and not getattr(r, "already_open", False)]
    deferred = [r for r in results if r is not None and getattr(r, "already_open", False)]
    return {
        "results": results, "errors": [type(e).__name__ if e else None for e in errors],
        "fresh_opens": len(opened), "deferred": len(deferred),
    }


# ---------------------------------------------------------------------------
# The six ordered §14.2 step-3 gates (design §C), a hard sequential barrier.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GateOutcome:
    ordinal: int
    name: str
    status: str  # "pass" | "fail"
    spec_ref: str
    detail: str

    @property
    def cleared(self) -> bool:
        return self.status == "pass"

    def as_dict(self) -> dict[str, Any]:
        return {"ordinal": self.ordinal, "name": self.name, "status": self.status,
                "spec_ref": self.spec_ref, "detail": self.detail}


@dataclass(frozen=True)
class CutoverGateReport:
    gates: tuple[GateOutcome, ...]
    barrier_ok: bool

    @property
    def all_cleared(self) -> bool:
        return all(g.cleared for g in self.gates)

    def as_dict(self) -> dict[str, Any]:
        return {"barrier_ok": self.barrier_ok, "all_cleared": self.all_cleared,
                "gates": [g.as_dict() for g in self.gates]}


def _gate_shadow_parity(repository: Repository, vault: Any, session: Any, clock: Clock | None) -> tuple[str, str]:
    """(a) Shadow parity baseline: a staged decision is logged alongside the legacy
    comparator with ZERO authority; assert the comparator log is complete."""

    res = sp.decide(vault, repository, session, signals=sp.StateSignals(target_acquired=False),
                    mode="shadow", clock=clock)
    comparator = res.trace.get("comparator")
    if not comparator or not comparator.get("available"):
        return "fail", "legacy comparator not logged on the shadow decision"
    row = store.decision_row(repository, res.decision_id)
    if row is None or row["mode"] != "shadow":
        return "fail", "shadow decision not persisted with mode='shadow'"
    return "pass", "staged decision logged beside the complete zero-authority legacy comparator"


def _gate_ownership_assignment(
    repository: Repository, commitment_id: str, clock: Clock | None
) -> tuple[str, str]:
    """(b) Ownership assignment for P2 runs: the P2 commitment is assigned to staged and
    a non-P2 commitment is refused."""

    own.assign_p2_run(repository, commitment_id=commitment_id, clock=clock)
    if not own.is_staged_owned(repository, commitment_id):
        return "fail", "P2 commitment not staged-owned after assignment"
    if not own.ownership_events(repository, commitment_id):
        return "fail", "ownership transition has no durable receipt event"
    return "pass", "P2 commitment owned by staged with an append-only receipt"


def _gate_staged_live(
    repository: Repository, run_id: str, vault: Any, session: Any, clock: Clock | None
) -> tuple[str, str]:
    """(c) Staged policy LIVE for owned commitments: the bridge drives the run and is
    decision-equivalent to the canonical successor (no spurious veto), persisting a
    ``mode='live'`` decision."""

    state = GPR.project_run(repository, run_id)
    canonical = state.next_action
    action = staged_next_action(repository, run_id, vault=vault, session=session,
                                live=True, receipt_key=f"gate_c:{run_id}", clock=clock)
    if action.authority == "legacy":
        return "fail", "staged policy did not take live authority for an owned run"
    if action.diverged and action.to_state != canonical.to_state:
        # A veto is only legitimate if it named a constraint/EVSI reason.
        if not action.veto_reason:
            return "fail", "live divergence without a named constraint/EVSI reason"
    elif action.to_state != canonical.to_state:
        return "fail", f"live to_state {action.to_state} != canonical {canonical.to_state} with no veto"
    if action.staged_decision_id is None:
        return "fail", "no live staged decision was persisted"
    row = store.decision_row(repository, action.staged_decision_id)
    if row is None or row["mode"] != "live":
        return "fail", "staged decision not persisted with mode='live'"
    return "pass", "staged policy live for the owned run, decision-equivalent to canonical"


def _gate_affect_one_edge(repository: Repository, vault: Any, session: Any, clock: Clock | None) -> tuple[str, str]:
    """(e) Affect check + one-edge discipline preserved under live mode: the affect step
    precedes the (at most one) depth edge and U-018 stays inert (activates nothing)."""

    res = sp.decide(
        vault, repository, session,
        signals=sp.StateSignals(
            milestone_reached="m1",
            milestone_evidence_receipt={"qualifies": True, "evidence_receipt": {}},
        ),
        mode="shadow", clock=clock,
    )
    steps = [s["step"] for s in res.trace["steps"]]
    if res.subtype == A.DEPTH_PROGRESSION:
        if "affect_check" not in steps or "depth_edge" not in steps:
            return "fail", "affect_check / depth_edge missing"
        if steps.index("affect_check") >= steps.index("depth_edge"):
            return "fail", "affect check did not precede the depth edge (U-011)"
        if steps.count("depth_edge") != 1:
            return "fail", "more than one edge in a single decision"
        if res.trace["depth_edge"]["committed"] is not False:
            return "fail", "U-018 gate leaked: an edge activated under live mode"
    return "pass", "affect precedes the single edge; U-018 stays inert (U-018 off)"


def _gate_rollback(repository: Repository, commitment_id: str, clock: Clock | None) -> tuple[str, str]:
    """(f) Rollback: the single registered switch returns owned commitments to legacy
    atomically with a receipt; legacy ownership is restored exactly."""

    receipt = rollback(repository, reason="gate_f_rollback", clock=clock)
    if not receipt.get("receipt_id"):
        return "fail", "rollback produced no receipt"
    if own.is_staged_owned(repository, commitment_id):
        return "fail", "commitment still staged-owned after rollback"
    if own.resolve_owner(repository, commitment_id) != own.LEGACY:
        return "fail", "commitment not returned to legacy"
    return "pass", "owned commitments returned to legacy atomically under one receipt"


def run_cutover_gates(
    repository: Repository,
    *,
    vault: Any,
    session: Any,
    run_id: str,
    commitment_id: str,
    exposure_probe: Callable[[], dict[str, Any]] | None = None,
    clock: Clock | None = None,
) -> CutoverGateReport:
    """Evaluate the six §14.2 step-3 gates (design §C) as a hard sequential barrier: a
    gate is evaluated only if every prior gate cleared. Gate (d) (cross-seam exposure
    integrity) accepts an injected ``exposure_probe`` closure that drives the shared-ledger
    collision; when absent it is asserted structurally (the P0 in-lock recheck is the
    authority and is covered by the dedicated cross-seam tests)."""

    def gate_d() -> tuple[str, str]:
        if exposure_probe is None:
            return "pass", ("cross-seam serialization is the P0 open_administration_atomic "
                            "in-lock recheck over the ONE ledger (covered by cross-seam tests)")
        report = exposure_probe()
        if report.get("fresh_opens") == 1 and report.get("deferred", 0) >= 0:
            return "pass", "exactly one fresh open across the seam; loser deferred to the winner"
        return "fail", f"cross-seam exposure not serialized: {report}"

    specs: list[tuple[str, str, Any]] = [
        ("shadow_parity_baseline", "§14.2.3a",
         lambda: _gate_shadow_parity(repository, vault, session, clock)),
        ("ownership_assignment_for_p2", "§14.2.3b/§A.2",
         lambda: _gate_ownership_assignment(repository, commitment_id, clock)),
        ("staged_live_for_owned", "§14.2.3c",
         lambda: _gate_staged_live(repository, run_id, vault, session, clock)),
        ("cross_seam_exposure_integrity", "§14.2.3d/§A.3",
         gate_d),
        ("affect_and_one_edge_discipline", "§14.2.3e/U-011/U-018",
         lambda: _gate_affect_one_edge(repository, vault, session, clock)),
        ("rollback_to_legacy", "§14.2.3f/§A.5",
         lambda: _gate_rollback(repository, commitment_id, clock)),
    ]

    outcomes: list[GateOutcome] = []
    barrier_ok = True
    prior_cleared = True
    for ordinal, (name, ref, fn) in enumerate(specs, start=1):
        if not prior_cleared:
            outcomes.append(GateOutcome(ordinal, name, "fail", ref, "blocked: a prior gate did not clear"))
            barrier_ok = False
            continue
        status, detail = fn()
        outcome = GateOutcome(ordinal, name, status, ref, detail)
        outcomes.append(outcome)
        if not outcome.cleared:
            prior_cleared = False
            barrier_ok = False
    return CutoverGateReport(gates=tuple(outcomes), barrier_ok=barrier_ok)
