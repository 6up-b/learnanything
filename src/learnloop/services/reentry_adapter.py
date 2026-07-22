"""P4 §12.1 -- the hiatus re-entry block-planner adapter (spec §12.1, §16.9).

Returning after a configured hiatus is NOT a diagnosis. The re-entry path (spec §12.1):

1. opens the NON-DIAGNOSTIC welcome-back surface first -- the existing
   :func:`reentry_summary.reentry_summary` FSRS diff. It may seed candidates but makes
   NO diagnostic claim on its own (§12.1 last paragraph, §16.9 bullet 2);
2. pins the current confirmed goal-contract target distribution for the episode -- the
   frozen :class:`predictive_targets.TargetSet` (never an ID-ordered slice, §6.6/§16.3);
3. classifies decayed state into ``retained`` / ``recoverable`` / ``needs_attention`` with
   intervals and context, NEVER deficit labels and NEVER backlog/streak language (§12.1,
   §16.9 bullet 1). Cells that are still solid or carry no decay information are TRUSTED
   (not re-checked); the fragile / target-frontier cells are the re-check candidates
   ("what gets re-checked vs trusted");
4. samples the high-value previously-demonstrated / historically-fragile / target-frontier
   cells and runs an OPTIONAL measure-mode attention block through the normal decision
   trace (:func:`staged_policy.decide`) with a small visible cap and the robust stop rule
   the staged measure block already owns (goal-conditioned predictive value over the
   pinned frozen target, §12.1 bullet 3, §16.3);
5. neither widens the envelope nor crosses the goal/task family -- that discipline is the
   staged policy's feasible-set constraints, inherited, not re-implemented here (§16.9
   bullet 4). A reviewed edge already authorized by ``auto_within_envelope`` may be
   activated when it fits.

The deferred journeys home screen is not required (§12.2): existing Today/continue entry
points expose this adapter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC
from typing import Any

from learnloop.clock import Clock, SystemClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.services import controller_snapshot as cs
from learnloop.services import goal_contracts
from learnloop.services import predictive_targets as pt
from learnloop.services import staged_policy as sp
from learnloop.services import state_signals as ss
from learnloop.services.goal_projection import facet_projections_at, goal_report
from learnloop.services.overconfidence import blueprint_weight_by_facet
from learnloop.services.reentry_summary import ReentrySummary, reentry_summary
from learnloop.vault.models import Goal, LoadedVault

# The small visible cap on re-entry re-check questions (§12.1 "keep a small visible cap
# and robust stop rule"). Heuristic decision parameter -- it never orders anything (the
# within-block robust-EVSI-per-minute selector does); it only bounds the candidate pool.
REENTRY_QUESTION_CAP = 5

# Recoverable band (§12.1): a previously-demonstrated cell whose Ready has slipped below
# target but by no more than this margin is RECOVERABLE (a light refresher), distinct from
# NEEDS_ATTENTION (slipped further). Reported as context, never a deficit label. Heuristic.
REENTRY_RECOVERABLE_BAND = 0.15

_RETAINED = "retained"
_RECOVERABLE = "recoverable"
_NEEDS_ATTENTION = "needs_attention"


@dataclass(frozen=True)
class CellStatus:
    """One facet cell's re-entry status with intervals + context (never a deficit label)."""

    learning_object_id: str
    learning_object_title: str
    facet_id: str
    status: str  # retained | recoverable | needs_attention
    ready_now: float
    ready_last: float
    predicted_current: float
    blueprint_weight: float
    re_checked: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "learning_object_id": self.learning_object_id,
            "learning_object_title": self.learning_object_title,
            "facet_id": self.facet_id,
            "status": self.status,
            "ready_now": round(self.ready_now, 6),
            "ready_last": round(self.ready_last, 6),
            "predicted_current": round(self.predicted_current, 6),
            "blueprint_weight": self.blueprint_weight,
            "re_checked": self.re_checked,
        }


@dataclass(frozen=True)
class ReentryPlan:
    show: bool
    welcome_back: dict[str, Any]              # the non-diagnostic FSRS summary
    welcome_back_is_diagnostic: bool          # always False -- the summary makes no claim
    pinned_target_hash: str | None            # frozen predictive-target distribution pin
    pinned_contract_version_id: str | None
    question_cap: int
    retained: list[CellStatus] = field(default_factory=list)
    recoverable: list[CellStatus] = field(default_factory=list)
    needs_attention: list[CellStatus] = field(default_factory=list)
    sampled_cells: list[CellStatus] = field(default_factory=list)
    decision: dict[str, Any] | None = None    # the staged measure decision trace
    decision_id: str | None = None
    stopped: bool = False
    uses_backlog_language: bool = False       # structurally False (§16.9 bullet 1)

    def as_dict(self) -> dict[str, Any]:
        return {
            "show": self.show,
            "welcome_back": self.welcome_back,
            "welcome_back_is_diagnostic": self.welcome_back_is_diagnostic,
            "pinned_target_hash": self.pinned_target_hash,
            "pinned_contract_version_id": self.pinned_contract_version_id,
            "question_cap": self.question_cap,
            "retained": [c.as_dict() for c in self.retained],
            "recoverable": [c.as_dict() for c in self.recoverable],
            "needs_attention": [c.as_dict() for c in self.needs_attention],
            "sampled_cells": [c.as_dict() for c in self.sampled_cells],
            "decision_id": self.decision_id,
            "stopped": self.stopped,
            "uses_backlog_language": self.uses_backlog_language,
        }


def classify_cells(
    vault: LoadedVault,
    repository: Repository,
    goal: Goal,
    *,
    clock: Clock | None = None,
) -> list[CellStatus]:
    """Classify each decay-estimated facet cell into retained / recoverable /
    needs_attention by comparing FSRS Ready at the last session end vs now (§12.1). Cells
    with no decay information (held flat) are TRUSTED and excluded from the confident copy,
    exactly like the welcome-back diff. Reports intervals + context, not deficit labels."""

    now = (clock or SystemClock()).now().astimezone(UTC)
    last_ended_iso = repository.most_recent_ended_at()
    last_ended = parse_utc(last_ended_iso) if last_ended_iso else now
    target = goal.target_recall

    proj_now = {
        (f.learning_object_id, f.facet_id): f
        for f in facet_projections_at(vault, repository, goal, now, clock=clock)
    }
    proj_last = {
        (f.learning_object_id, f.facet_id): f
        for f in facet_projections_at(vault, repository, goal, last_ended, clock=clock)
    }
    report = goal_report(vault, repository, goal, clock=clock)
    weights = blueprint_weight_by_facet(vault, report)

    cells: list[CellStatus] = []
    for key, now_facet in proj_now.items():
        if not now_facet.decay_estimated:
            continue  # held flat -> trusted, no decay information (not re-checked)
        last_facet = proj_last.get(key)
        ready_now = now_facet.ready
        ready_last = last_facet.ready if last_facet is not None else ready_now
        if ready_now >= target:
            status, re_checked = _RETAINED, False
        elif ready_last >= target and ready_now >= target - REENTRY_RECOVERABLE_BAND:
            status, re_checked = _RECOVERABLE, True
        else:
            status, re_checked = _NEEDS_ATTENTION, True
        lo = vault.learning_objects.get(now_facet.learning_object_id)
        cells.append(
            CellStatus(
                learning_object_id=now_facet.learning_object_id,
                learning_object_title=(lo.title if lo is not None else now_facet.learning_object_id),
                facet_id=now_facet.facet_id,
                status=status,
                ready_now=ready_now,
                ready_last=ready_last,
                predicted_current=now_facet.predicted_current,
                blueprint_weight=weights.get(
                    (now_facet.learning_object_id, vault.canonical_facet_id(now_facet.facet_id)), 1.0
                ),
                re_checked=re_checked,
            )
        )
    return cells


def _pinned_target(repository: Repository, goal: Goal, cells: list[CellStatus]) -> pt.TargetSet:
    """Pin the frozen predictive target distribution for the episode (§12.1 bullet 2).
    Uses the confirmed goal-contract head when present; otherwise pins a frozen target set
    derived from the classified cells (still order-invariant, still a stable hash)."""

    head = goal_contracts.resolve_head(repository, goal.id)
    if head is not None:
        return pt.build_from_contract_version(head)
    body = {
        "exemplars": [
            {"id": f"{c.learning_object_id}:{c.facet_id}", "weight": c.blueprint_weight}
            for c in cells
        ],
        "eligibility": {"held_out": True},
    }
    return pt.build_target_set(body, contract_version_id=None)


def _goal_conditioned_priority(cell: CellStatus) -> tuple[float, float, str]:
    """Re-entry sampling priority over the pinned frozen target (§12.1 bullet 3): the
    historically fragile / target-frontier cells first, high blueprint weight first. This
    is the goal-conditioned ordering; the per-question robust stop rule is the staged
    measure block's robust-EVSI selector. Returns a sort key (descending)."""

    # needs_attention (2) before recoverable (1) before retained (0); then blueprint weight.
    rank = {_NEEDS_ATTENTION: 2.0, _RECOVERABLE: 1.0, _RETAINED: 0.0}[cell.status]
    return (rank, cell.blueprint_weight, cell.facet_id)


def plan_reentry(
    vault: LoadedVault,
    repository: Repository,
    goal: Goal,
    session: Any | None = None,
    *,
    question_cap: int = REENTRY_QUESTION_CAP,
    gap_days: int | None = None,
    mode: str = "shadow",
    run_measure_block: bool = True,
    receipt_key: str | None = None,
    clock: Clock | None = None,
) -> ReentryPlan:
    """Plan the hiatus re-entry (§12.1). Composes the non-diagnostic welcome-back summary,
    pins the frozen target distribution, classifies decayed state without deficit/backlog
    language, and (optionally) runs a capped measure-mode attention block on the normal
    decision trace with the staged policy's robust stop rule."""

    summary: ReentrySummary = reentry_summary(vault, repository, goal, clock=clock, gap_days=gap_days)
    cells = classify_cells(vault, repository, goal, clock=clock)
    target_set = _pinned_target(repository, goal, cells)

    retained = [c for c in cells if c.status == _RETAINED]
    recoverable = [c for c in cells if c.status == _RECOVERABLE]
    needs_attention = [c for c in cells if c.status == _NEEDS_ATTENTION]

    # Sample the fragile / target-frontier cells first, capped to the small visible cap.
    frontier = sorted(
        (c for c in cells if c.re_checked),
        key=_goal_conditioned_priority,
        reverse=True,
    )
    sampled = frontier[:question_cap]

    decision_trace: dict[str, Any] | None = None
    decision_id: str | None = None
    stopped = False
    if run_measure_block and session is not None:
        # A non-empty frontier carries decision-relevant, measurable uncertainty -> the
        # ladder yields a measure_diagnostic block. An empty frontier means everything is
        # retained/trusted -> the ladder honestly stops (no measure block invented).
        signal = ss.OPEN_EPISODE_ROBUST_VALUE if sampled else 0.0
        signals = sp.StateSignals(decision_relevant_robust_value=signal)
        # Cap the candidate universe to the sampled cells' learning objects (the small
        # visible cap is structural, not just advisory copy).
        sampled_los = {c.learning_object_id for c in sampled}
        candidates = [
            cand for cand in cs.build_snapshot(vault, repository, session, clock=clock).candidates
            if cand.learning_object_id in sampled_los
        ] or None
        result = sp.decide(
            vault, repository, session, signals=signals, candidates=candidates,
            mode=mode, receipt_key=receipt_key, clock=clock,
        )
        decision_trace = result.trace
        decision_id = result.decision_id
        stopped = result.action == "stop"

    return ReentryPlan(
        show=summary.show,
        welcome_back=summary.as_dict(),
        welcome_back_is_diagnostic=False,
        pinned_target_hash=target_set.target_set_hash,
        pinned_contract_version_id=target_set.contract_version_id,
        question_cap=question_cap,
        retained=retained,
        recoverable=recoverable,
        needs_attention=needs_attention,
        sampled_cells=sampled,
        decision=decision_trace,
        decision_id=decision_id,
        stopped=stopped,
        uses_backlog_language=False,
    )
