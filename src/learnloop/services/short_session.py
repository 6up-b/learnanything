"""P4 §12.2 -- the three-minute / short-session block-planner adapter (spec §12.2,
§16.1 "one three-minute activity completes a session", §16.9).

The short session is NOT a new controller: it is the SAME staged block planner
(:mod:`staged_policy`) run with a small ``available_minutes`` (down to ~3). The only
difference is the budget arithmetic -- when the available minutes fall below the 5-minute
attention-block lower bound the block is planned to COMPLETE within them (one activity is
the whole block; :func:`staged_policy.is_short_session` /
``staged_policy._as_short_block``), the constraint engine's fatigue/budget gate keeps only
candidates whose conservative duration fits (real durations, the minutes machinery), and
the within-block selector prefers the admitted short P1 patterns
(``setup_only`` / ``example_completion`` / ``example_comparison``).

Contract (spec §12.2):
- one completed activity completes the session -- never a dangling multi-activity block;
- if no meaningful candidate fits, return ``stop:no_feasible_activity`` -- do NOT fill
  time with low-value leftovers;
- a reviewed edge already authorized by ``auto_within_envelope`` may be activated ONLY
  when the transition fits safely; otherwise the session stops honestly (the depth-edge
  fit guard in :func:`staged_policy.decide`). Neither this adapter nor the re-entry one
  widens the envelope or crosses the goal/task family -- that discipline is inherited from
  the staged policy's feasible-set constraints, not re-implemented here.

The decision runs on the NORMAL decision trace (``staged_policy.decide``): the block, the
feasible set + exclusions, the chosen activity or the typed stop, and the snapshot hash
all replay from events like any other controller decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services import controller_actions as A
from learnloop.services import controller_snapshot as cs
from learnloop.services import staged_policy as sp
from learnloop.vault.models import LoadedVault


@dataclass(frozen=True)
class ShortSessionPlan:
    """The outcome of one short-session decision. ``completed`` is True when exactly one
    structurally meaningful activity was chosen (it IS the whole block); ``stopped`` is
    True when nothing meaningful fit and the session stopped honestly."""

    decision: sp.DecisionResult
    available_minutes: float | None
    is_short_session: bool
    completed: bool
    stopped: bool
    stop_reason: str | None
    chosen_candidate_ref: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "available_minutes": self.available_minutes,
            "is_short_session": self.is_short_session,
            "completed": self.completed,
            "stopped": self.stopped,
            "stop_reason": self.stop_reason,
            "chosen_candidate_ref": self.chosen_candidate_ref,
            "action": self.decision.action,
            "subtype": self.decision.subtype,
            "block": self.decision.trace.get("attention_block"),
        }


def plan_short_session(
    vault: LoadedVault,
    repository: Repository,
    session: Any,
    *,
    signals: sp.StateSignals | None = None,
    candidates: Sequence[cs.Candidate] | None = None,
    continuation: Mapping[str, Any] | None = None,
    diagnostic: sp.DiagnosticSelector | None = None,
    mode: str = "shadow",
    owned_item_refs: set[str] | None = None,
    receipt_key: str | None = None,
    clock: Clock | None = None,
) -> ShortSessionPlan:
    """Plan one short session (§12.2). ``session`` carries the (small) ``available_minutes``
    -- the SAME block planner runs; this adapter only frames the completion contract and
    reports whether the single activity completed the session or it stopped honestly.

    ``continuation`` lets the session continue an in-flight block (the deferred journeys
    home screen is not required, §12.2: existing Today/continue entry points expose this)."""

    result = sp.decide(
        vault, repository, session,
        signals=signals, candidates=candidates, continuation=continuation,
        diagnostic=diagnostic, mode=mode, owned_item_refs=owned_item_refs,
        receipt_key=receipt_key, clock=clock,
    )

    available = getattr(session, "available_minutes", None)
    available_f = float(available) if available is not None else None
    short = available_f is not None and available_f < float(sp.SHORT_SESSION_MAX_MINUTES)

    stopped = result.action == A.STOP
    completed = not stopped and result.chosen_candidate_ref is not None
    # A depth-progression edge activation is a completing structural activity even though
    # it carries no card candidate (the activity IS the edge, §16.9).
    if not stopped and result.subtype == A.DEPTH_PROGRESSION:
        completed = True

    return ShortSessionPlan(
        decision=result,
        available_minutes=available_f,
        is_short_session=short,
        completed=completed,
        stopped=stopped,
        stop_reason=result.stop_reason,
        chosen_candidate_ref=result.chosen_candidate_ref,
    )
