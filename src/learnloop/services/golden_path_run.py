"""P2 step 3 -- the golden-path run state machine + resume
(spec_p2_narrow_golden_path §4.1, §4.2, §4.3, §12.6; migration 082).

The run is an event-sourced state machine: ``golden_path_run_events`` is the authority
and ``golden_path_runs.current_state`` is a rebuildable cache. ``project_run`` folds the
event log into a :class:`RunState`; ``advance`` appends exactly one transition, fenced on
the optimistic head and idempotent on a client key, so a crash/retry reopens the same
committed transition and never chooses a second item or repeats a side effect
(invariant 11 / §4.3). Every transition logs the goal-contract HEAD version it evaluated
(P0.4 semantics, §4.1).

This is the narrow, transparent per-run policy of §4.2 -- explicitly NOT the P4 global
controller. Constraints define a feasible set; the machine only moves within it. The
per-stage WORK (baseline episode, triage, ladder, pool, assessment, restoration, depth
edge) is the landed P0/P1 substrate the parallel P2 tracks compose; this module owns the
ordering, the event log, and resume.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.activities import _json

# §4.1 launch states. `current_state` CHECK in migration 082 is the source of truth.
STATES: frozenset[str] = frozenset(
    {
        "draft", "ready", "measuring", "triaging", "instructing", "completing",
        "practicing", "integrating", "awaiting_delayed_check", "ready_to_assess",
        "assessing", "restoring", "deepening", "maintaining", "complete", "paused",
        "practice_only", "needs_review", "abandoned",
    }
)

TERMINAL_STATES: frozenset[str] = frozenset({"complete", "abandoned"})

# §6/§7 instruction & repair states. The FIRST run transition into any of these closes
# the pinned baseline diagnostic segment (P0 invariant 7 / §12.2): once instruction has
# begun the measurement segment is closed and a later re-entry to `measuring` mints a
# FRESH episode. Diagnosis states (`triaging`) and the capable skip (`ready_to_assess`)
# are NOT instruction -- they leave the segment open.
INSTRUCTION_STATES: frozenset[str] = frozenset(
    {"instructing", "completing", "practicing", "integrating"}
)

# Permitted adjacency (§4.1). The run MAY skip states when evidence supports it, MAY
# move back from practice/integration to instruction after a new failure, but NEVER
# reopens a closed diagnostic segment: no state whose segment ran instruction leads
# back to `measuring`. Side states (paused / needs_review / abandoned) are reachable
# from any live state; resume leaves `paused` back to the live states.
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"ready", "abandoned"}),
    "ready": frozenset({"measuring", "ready_to_assess", "practice_only", "paused", "needs_review", "abandoned"}),
    "measuring": frozenset({"triaging", "instructing", "ready_to_assess", "needs_review", "paused", "abandoned"}),
    "triaging": frozenset({"instructing", "completing", "practicing", "integrating", "needs_review", "paused", "abandoned"}),
    "instructing": frozenset({"completing", "practicing", "integrating", "ready_to_assess", "needs_review", "paused", "abandoned"}),
    "completing": frozenset({"practicing", "instructing", "integrating", "ready_to_assess", "needs_review", "paused", "abandoned"}),
    "practicing": frozenset({"integrating", "instructing", "awaiting_delayed_check", "ready_to_assess", "needs_review", "paused", "abandoned"}),
    "integrating": frozenset({"practicing", "instructing", "awaiting_delayed_check", "ready_to_assess", "needs_review", "paused", "abandoned"}),
    "awaiting_delayed_check": frozenset({"practicing", "ready_to_assess", "needs_review", "paused", "abandoned"}),
    "ready_to_assess": frozenset({"assessing", "practicing", "needs_review", "paused", "abandoned"}),
    "assessing": frozenset({"restoring", "needs_review", "paused", "abandoned"}),
    "restoring": frozenset({"deepening", "maintaining", "complete", "needs_review", "paused", "abandoned"}),
    "deepening": frozenset({"maintaining", "complete", "practicing", "needs_review", "paused", "abandoned"}),
    "maintaining": frozenset({"complete", "deepening", "paused", "abandoned"}),
    "paused": frozenset(
        {"ready", "measuring", "triaging", "instructing", "completing", "practicing",
         "integrating", "awaiting_delayed_check", "ready_to_assess", "assessing",
         "restoring", "deepening", "maintaining", "practice_only", "abandoned"}
    ),
    "practice_only": frozenset({"practicing", "instructing", "maintaining", "complete", "paused", "needs_review", "abandoned"}),
    "needs_review": frozenset({"ready", "maintaining", "paused", "abandoned"}),
    "complete": frozenset(),
    "abandoned": frozenset(),
}

# The narrow live policy's canonical happy-path successor per state (§4.2). Used to
# report the "next feasible action" a resume must reproduce (§12.6).
_CANONICAL_NEXT: dict[str, tuple[str, str]] = {
    "ready": ("measuring", "run a bounded baseline to localize the boundary"),
    "measuring": ("triaging", "triage the localized boundary"),
    "triaging": ("instructing", "teach/repair the nearest reason"),
    "instructing": ("practicing", "practice on a fresh surface"),
    "completing": ("practicing", "practice on a fresh surface"),
    "practicing": ("ready_to_assess", "delayed independent practice demonstrated"),
    "integrating": ("ready_to_assess", "whole-task integration demonstrated"),
    "awaiting_delayed_check": ("ready_to_assess", "delayed check due"),
    "ready_to_assess": ("assessing", "administer the fresh held-out assessment"),
    "assessing": ("restoring", "restore source + boundary diff after grade commit"),
    "restoring": ("deepening", "record milestone; render one reviewed next edge"),
    "deepening": ("complete", "one reviewed edge confirmed; replan"),
    "maintaining": ("complete", "hold at target"),
    "practice_only": ("maintaining", "no fresh assessment; hold without terminal claim"),
}


class IllegalTransition(Exception):
    """A requested transition is not in the run's feasible set (§4.1 adjacency)."""

    def __init__(self, run_id: str, *, from_state: str, to_state: str):
        self.run_id = run_id
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"run {run_id}: {from_state} -> {to_state} is not a permitted transition")


class StaleRunHead(Exception):
    """The expected head event no longer matches the run's head (§4.3 optimistic fence)."""

    def __init__(self, run_id: str, *, expected: str | None, actual: str | None):
        self.run_id = run_id
        self.expected = expected
        self.actual = actual
        super().__init__(f"run {run_id}: expected head {expected!r} is not current head {actual!r}")


@dataclass(frozen=True)
class NextAction:
    to_state: str | None
    reason: str
    terminal: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RunState:
    """A projection of the append-only event log (§4.1). Rebuildable from events alone."""

    run_id: str
    current_state: str
    head_event_id: str | None
    head_seq: int
    mode: str
    milestone: str | None
    goal_contract_head_version_id: str | None
    event_count: int
    next_action: NextAction
    history: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AdvanceResult:
    run_id: str
    event_id: str
    seq: int
    from_state: str
    to_state: str
    already_exists: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def next_feasible_action(state: RunState) -> NextAction:
    """The transparent staged policy's next canonical action from a state (§4.2)."""

    return _next_action_for(state.current_state, state.mode)


def _next_action_for(current_state: str, mode: str) -> NextAction:
    if current_state in TERMINAL_STATES:
        return NextAction(to_state=None, reason="run is terminal", terminal=True)
    # A practice_only run never administers a terminal assessment (§1.1).
    if mode == "practice_only" and current_state in ("ready", "ready_to_assess", "instructing", "practicing"):
        return NextAction(to_state="maintaining", reason="practice_only: no terminal claim", terminal=False)
    nxt = _CANONICAL_NEXT.get(current_state)
    if nxt is None:
        return NextAction(to_state=None, reason="await owner/learner decision", terminal=False)
    return NextAction(to_state=nxt[0], reason=nxt[1], terminal=False)


def project_run(repository: Repository, run_id: str) -> RunState:
    """Fold the event log into the current run state (§4.1). Authoritative over the
    cached ``current_state`` column -- a corrupt/mismatched cache is ignored here."""

    run = repository.golden_path_run(run_id)
    if run is None:
        raise ValueError(f"unknown golden-path run: {run_id}")
    events = repository.golden_path_run_events_for(run_id)
    if events:
        head = events[-1]
        current_state = head["to_state"]
        head_event_id = head["id"]
        head_seq = head["seq"]
    else:  # pragma: no cover - confirmation always writes run_started
        current_state = "draft"
        head_event_id = None
        head_seq = 0

    milestone = run["initial_milestone"]
    gc_head = None
    for event in events:
        if event.get("successor_milestone"):
            milestone = event["successor_milestone"]
        if event.get("goal_contract_head_version_id"):
            gc_head = event["goal_contract_head_version_id"]

    history = tuple(
        {
            "seq": e["seq"],
            "from_state": e["from_state"],
            "to_state": e["to_state"],
            "reason": e["reason"],
            "goal_contract_head_version_id": e["goal_contract_head_version_id"],
        }
        for e in events
    )
    return RunState(
        run_id=run_id,
        current_state=current_state,
        head_event_id=head_event_id,
        head_seq=head_seq,
        mode=run["mode"],
        milestone=milestone,
        goal_contract_head_version_id=gc_head,
        event_count=len(events),
        next_action=_next_action_for(current_state, run["mode"]),
        history=history,
    )


def advance(
    repository: Repository,
    run_id: str,
    *,
    to_state: str,
    reason: str,
    idempotency_key: str,
    expected_head_event_id: str | None = None,
    evidence_ids: Sequence[str] | None = None,
    selected_activity: Mapping[str, Any] | None = None,
    feasible_alternatives: Sequence[str] | None = None,
    predecessor_milestone: str | None = None,
    successor_milestone: str | None = None,
    policy_calibration: Mapping[str, Any] | None = None,
    burden: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> AdvanceResult:
    """Append exactly one transition (§4.1). Idempotent on ``idempotency_key``
    (§12.6 exactly-once) and fenced on the optimistic head (§4.3). Validates the
    transition against the feasible-set adjacency and logs the current goal-contract
    head version (P0.4). Raises :class:`IllegalTransition` or :class:`StaleRunHead`."""

    if to_state not in STATES:
        raise IllegalTransition(run_id, from_state="?", to_state=to_state)

    state = project_run(repository, run_id)

    # Idempotent replay: a retried transition with the same key returns the existing
    # event WITHOUT re-validating adjacency (§12.6) -- the side effect already happened.
    existing = _existing_event(repository, run_id, idempotency_key)
    if existing is not None:
        return AdvanceResult(
            run_id=run_id,
            event_id=existing["id"],
            seq=existing["seq"],
            from_state=existing["from_state"],
            to_state=existing["to_state"],
            already_exists=True,
        )

    allowed = ALLOWED_TRANSITIONS.get(state.current_state, frozenset())
    if to_state not in allowed:
        raise IllegalTransition(run_id, from_state=state.current_state, to_state=to_state)

    # P0.4 semantics: read/log the current goal-contract head at decision time.
    run = repository.golden_path_run(run_id)
    head = repository.fetch_goal_contract_head(run["goal_id"]) if run else None
    gc_head_id = head["head_version_id"] if head else None

    fence = expected_head_event_id if expected_head_event_id is not None else state.head_event_id
    result = repository.append_golden_path_run_event(
        run_id=run_id,
        to_state=to_state,
        reason=reason,
        expected_head_event_id=fence,
        idempotency_key=idempotency_key,
        feasible_alternatives_json=_json(list(feasible_alternatives)) if feasible_alternatives else _json(sorted(allowed)),
        evidence_ids_json=_json(list(evidence_ids)) if evidence_ids else None,
        goal_contract_head_version_id=gc_head_id,
        depth_policy_version_id=run["depth_policy_version_id"] if run else None,
        depth_envelope_version_id=run["depth_envelope_version_id"] if run else None,
        predecessor_milestone=predecessor_milestone,
        successor_milestone=successor_milestone,
        selected_activity_json=_json(dict(selected_activity)) if selected_activity else None,
        policy_calibration_json=_json(dict(policy_calibration)) if policy_calibration else None,
        burden_json=_json(dict(burden)) if burden else None,
        clock=clock,
    )
    if result.get("already_exists"):
        event = result["event"]
        return AdvanceResult(
            run_id=run_id, event_id=event["id"], seq=event["seq"],
            from_state=event["from_state"], to_state=event["to_state"], already_exists=True,
        )
    if result.get("stale"):
        raise StaleRunHead(run_id, expected=result["expected"], actual=result["actual"])
    event = result["event"]
    # P0 invariant 7 (§12.2): the first transition into instruction/repair closes the
    # pinned baseline diagnostic segment and snapshots the baseline boundary view (the
    # frozen `before` of the post-assessment boundary diff, §8.4).
    if to_state in INSTRUCTION_STATES:
        _close_diagnostic_segment_on_instruction(repository, run_id, clock=clock)
    return AdvanceResult(
        run_id=run_id, event_id=event["id"], seq=event["seq"],
        from_state=event["from_state"], to_state=event["to_state"], already_exists=False,
    )


def _close_diagnostic_segment_on_instruction(
    repository: Repository, run_id: str, *, clock: Clock | None
) -> None:
    """Close the run's pinned baseline episode + snapshot its boundary view when
    instruction begins (invariant 7 / §5.3 / §8.4). No-op when the run pinned no pack
    or the episode is already closed. The single chokepoint every instruction entry
    passes through is :func:`advance`, so this is the one place the segment closes."""

    pin = repository.diagnostic_pack_pin_for_run(run_id)
    if pin is None:
        return
    from learnloop.services import diagnostic_pack as DP
    from learnloop.services import probe_episodes as PE

    # Snapshot the baseline boundary BEFORE closing the episode -- the projection reads
    # the (about-to-be-frozen) baseline observations, and the snapshot is idempotent.
    DP.snapshot_baseline_boundary(repository, run_id=run_id, clock=clock)
    episode_id = pin.get("probe_episode_id")
    if episode_id:
        closed = PE.close_diagnostic_segment(repository, episode_id, clock=clock)
        if closed is not None:
            repository.append_golden_path_artifact(
                run_id=run_id,
                kind="diagnostic_segment_closed",
                payload_json=_json(
                    {"probe_episode_id": episode_id, "reason": "instruction_started"}
                ),
                idempotency_key=f"diagnostic_segment_closed:{run_id}:{episode_id}",
                clock=clock,
            )


def advance_canonical(
    repository: Repository,
    run_id: str,
    *,
    idempotency_key: str,
    clock: Clock | None = None,
    **extra: Any,
) -> AdvanceResult:
    """Convenience: advance along the canonical happy-path successor (§4.2)."""

    state = project_run(repository, run_id)
    action = state.next_action
    if action.to_state is None:
        raise IllegalTransition(run_id, from_state=state.current_state, to_state="<none>")
    return advance(
        repository, run_id, to_state=action.to_state, reason=action.reason,
        idempotency_key=idempotency_key, clock=clock, **extra,
    )


def _existing_event(repository: Repository, run_id: str, idempotency_key: str) -> dict[str, Any] | None:
    for event in repository.golden_path_run_events_for(run_id):
        if event.get("idempotency_key") == idempotency_key:
            return event
    return None
