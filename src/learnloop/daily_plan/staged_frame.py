"""Router R2a: the staged frame on Today (``staged_frame_v1``) and its chooser (``staged_v1``).

docs/specs/plan_router_r2_v1.md §3.1-§3.2, owner Q1 (2026-10-13): the staged
component on Today is DL1's ``lane_quota_v1`` over the set the P4 constraint
engine admits. The P2 cutover's own rule, extended to Today: under identical
inputs the staged path is decision-equivalent to the incumbent unless a named
constraint vetoes.

**The source** (:class:`StagedFrameSource`). At each boundary it takes the
pool VOI v2 has already admitted (it never re-decides a probe: owner Q2) and
runs ``constraint_engine.evaluate`` on every item that has a lane, against one
bounded :class:`~learnloop.scheduling.controller_snapshot.ControllerSnapshot`
(its query budget does not grow with the pool). An item a constraint refuses
is dropped before DL1's packing (``legacy_lanes_v1``, unchanged), and the
refusal is recorded with its named reason (the ``plan_block`` row's
``exclusions_json.named.<constraint key>``).

Each item is evaluated in the attention block of its role in the plan:

* a **quick check that must be unseen** (a ``diagnostic_probe`` /
  ``diagnostic_microprobe`` / ``probe`` item, or a due project probe) in a
  ``measure_diagnostic`` block, so the hard-exposure rule applies: a surface
  the learner has already seen (an exact or near-clone exposure in the one
  ledger), or whose freshness cannot be established, is no fresh evidence;
* every other item in its lane's action (``practice`` / ``maintain`` /
  ``instruct``), as ordinary practice. A teach-back is ordinary practice here:
  value-of-information admission (mvp-0.21) decides teach-backs, and the
  dialogue is re-served by design (owner D11).

So on Today the constraints that can refuse are: an inactive or quarantined
item, a stimulus the surface cannot render, a seen or unknown-freshness quick
check, a surface holding a live assessment reservation, and a back-to-back
quick check on the same near-kin surface (dispersion, a deferral). The purpose
constraint is satisfied by construction (an item's purpose is its role), the
fatigue constraint is the container's own minutes rule (the snapshot carries
no session minutes, so the engine does not repeat it), and stage interleaving
needs a staged block (none on Today). Requests (the learner's own, L3) and
mid-plan follow-ups (the follow-up rules; value of information decides them)
are placed by the container, never by the source, so the frame does not veto
them. A due "Check once" (DL2) is placed by the container too, but only once
its candidate passed the one check gate (``scheduling.intent.feasibility``,
fix round 6), which runs this frame's own mandatory evaluation
(``scheduling.frame_constraints``) under every policy: a check is exempt from
value and count composition, never from a mandatory constraint.

**Annotations** on each candidate: the P4 ladder rungs its learning objects
are eligible for (per-LO signals from the lane classification plus the live
adapters; the ladder annotates, it never orders: Q1), whether serving it is
reversible (not when an item holds an open cold check, which serving spends,
or a reserved assessment surface, which the frame refuses anyway), and the
plain reason code of its "why" (:mod:`learnloop.router.why`).

**The chooser** (:class:`StagedChooser`, ``staged_v1``): ``lane_quota_v1``'s
pick over the staged-feasible candidates, deterministic (propensity 1). An
irreversible candidate is chosen only as that deterministic pick (G2): R2b's
mixture draws only among ``draw_support`` (the reversible ones). The chooser
builds the learner-state card (:mod:`learnloop.daily_plan.router_card`) and
returns it on ``BlockChoice.router_record``; the container hands it to the
``plan_block`` logger, which stores it with the decision in the block's
transaction. The chooser writes nothing.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

from learnloop.daily_plan.chooser import LaneQuotaChooser
from learnloop.daily_plan.lanes import (
    ASSUMED_CHECK_REASON,
    GAP_COMMITMENT_CHECK_REASON,
    GAP_SOONER_CHECK_REASON,
    LegacyLanesSource,
    PoolItem,
)
from learnloop.daily_plan.types import (
    BLOCK_MAX_MINUTES,
    LANE_ACTIONS,
    STOP_OFFER_MINUTES,
    BlockCandidate,
    BlockChoice,
    PlanState,
)
from learnloop.router import why as router_why

_LOG = logging.getLogger(__name__)

SOURCE_NAME = "staged_frame_v1"
CHOOSER_NAME = "staged_v1"
MODE = "staged"

# The roles and the fresh-evidence modes are the shared evaluation's
# (``scheduling.frame_constraints``, DL2 fix round 6: the "Check once" gate
# runs the same evaluation under every policy).
from learnloop.scheduling.frame_constraints import (  # noqa: E402, F401 - re-exported
    CONSTRAINTS_UNAVAILABLE_KEY,
    FRESH_EVIDENCE_CHECKS,
    FRESH_EVIDENCE_MODES,
    ROLE_FRESH_EVIDENCE,
    ROLE_PRACTICE,
    item_role,
)

#: The rung the ladder falls through to; every LO is eligible for it, so it
#: is left out of a candidate's annotation.
_FALL_THROUGH_RULES = frozenset({"no_positive_value_stop", "goal_satisfied"})


def reason_code(lane: str, items: Sequence[PoolItem], *, reading: bool = False) -> str:
    """The plain-"why" code of a block (:data:`learnloop.router.why.SENTENCES`)."""

    if reading:
        return "reading"
    if lane == "repair":
        if any(item.followup for item in items):
            return "repair_followup"
        if any(item.reason == "an open diagnosed problem on this topic" for item in items):
            return "repair_open_problem"
        return "repair_recent_errors"
    if lane == "maintain":
        checks = [item for item in items if item.check_kind]
        if checks and len(checks) == len(items):
            kinds = {item.check_kind for item in checks}
            reasons = {item.reason for item in checks}
            if kinds == {"assumed_check"}:
                if reasons == {GAP_COMMITMENT_CHECK_REASON}:
                    return "gap_check_added"
                if reasons == {GAP_SOONER_CHECK_REASON}:
                    return "gap_check_sooner"
                if reasons == {ASSUMED_CHECK_REASON}:
                    return "assumed_check"
            if kinds == {"project_probe"}:
                return "project_check"
            if kinds == {"check_once"}:
                return "check_once"
            return "scheduled_checks"
        return "review"
    if lane == "new":
        return "new_material"
    return "goal_step"


# -- the frame's material (one snapshot per env) ---------------------------------


@dataclass
class FrameMaterial:
    """What the constraint engine and the ladder read, for the items evaluated so far.

    ``refusals`` is mandatory feasibility: an item whose hard constraints could
    not be established is refused (fail closed). ``cold_items`` and
    ``ladder_by_lo`` are annotations, each read on its own: a failed read never
    erases a refusal. ``cold_items`` is None when it could not be read, and
    then no candidate is reversible (G2 never draws an unknown)."""

    snapshot_hash: str | None = None
    manifest_hash: str | None = None
    refusals: dict[str, tuple[dict[str, Any], ...]] = field(default_factory=dict)
    roles: dict[str, str] = field(default_factory=dict)
    reserved_items: frozenset[str] = frozenset()
    cold_items: frozenset[str] | None = frozenset()
    ladder_by_lo: dict[str, dict[str, Any]] = field(default_factory=dict)
    evaluated: frozenset[str] = frozenset()
    error: str | None = None


class StagedFrame:
    """The frame's material for one plan env (one RPC): built at the first
    boundary from one bounded snapshot over the pool, rebuilt over the union
    only when a later pool holds an item it has not evaluated (a follow-up
    that appeared mid-plan). Projection reads share it, so the view's
    projected blocks drop the same items without another snapshot."""

    def __init__(self, vault: Any, repository: Any, *, clock: Any = None) -> None:
        self.vault = vault
        self.repository = repository
        self.clock = clock
        self._material: FrameMaterial | None = None
        self._pool: dict[str, PoolItem] = {}

    def material(self, pool: Iterable[PoolItem]) -> FrameMaterial:
        wanted = {item.practice_item_id: item for item in pool if item.lane is not None}
        if self._material is not None and set(wanted) <= set(self._material.evaluated):
            return self._material
        self._pool.update(wanted)
        self._material = self._build(list(self._pool.values()))
        return self._material

    # -- building --------------------------------------------------------------

    def _cold_items(self) -> frozenset[str]:
        """Items an open cold follow-up holds (``instructional.policy.cold_administration_open``'s rule)."""

        from learnloop.attempts.attempts import COLD_FOLLOWUP_TASK_KINDS

        held: set[str] = set()
        for kind in sorted(COLD_FOLLOWUP_TASK_KINDS):
            for task in self.repository.open_followup_tasks_of_kind(kind):
                if task.get("selected_item_id"):
                    held.add(str(task["selected_item_id"]))
        return frozenset(held)

    def _block(self, item: PoolItem, role: str) -> Any:
        from learnloop.scheduling import controller_actions as A
        from learnloop.scheduling.frame_constraints import attention_block

        if role == ROLE_FRESH_EVIDENCE:
            action, subtype = A.MEASURE_DIAGNOSTIC, None
        else:
            action, subtype = LANE_ACTIONS.get(item.lane or "maintain", ("maintain", None))
        return attention_block(action, subtype, budget_minutes=float(BLOCK_MAX_MINUTES), source=SOURCE_NAME,
                               lane=item.lane)

    def _build(self, pool: Sequence[PoolItem]) -> FrameMaterial:
        """Mandatory feasibility first (``frame_constraints.evaluate_mandatory``,
        the evaluation the "Check once" gate shares: R2a review F2's fail-closed
        rules), then the annotations (open cold checks, the ladder), each read
        on its own. A failed annotation is named in ``error`` and never erases
        a refusal."""

        from learnloop.scheduling.frame_constraints import evaluate_mandatory

        evaluated = frozenset(item.practice_item_id for item in pool)
        evaluation = evaluate_mandatory(self.vault, self.repository, pool, clock=self.clock, block_for=self._block)
        if evaluation.inputs_error is not None:
            return FrameMaterial(
                manifest_hash=evaluation.manifest_hash,
                refusals=evaluation.refusals,
                cold_items=None,
                evaluated=evaluated,
                error=evaluation.inputs_error,
            )
        errors = list(evaluation.errors)
        known = [item for item in pool if item.practice_item_id in self.vault.practice_items]
        # Annotations: each read on its own; the refusals above stand.
        cold_items: frozenset[str] | None
        try:
            cold_items = self._cold_items()
        except Exception as exc:  # noqa: BLE001 - annotation only; reversibility becomes unknown
            _LOG.warning("router R2a: open cold checks could not be read", exc_info=True)
            cold_items = None
            errors.append(f"cold_checks:{type(exc).__name__}")
        try:
            ladder_by_lo = self._ladder(evaluation.snapshot, known, evaluation.reserved_items)
        except Exception as exc:  # noqa: BLE001 - annotation only
            _LOG.warning("router R2a: the ladder annotation could not be built", exc_info=True)
            ladder_by_lo = {}
            errors.append(f"ladder:{type(exc).__name__}")
        return FrameMaterial(
            snapshot_hash=evaluation.snapshot_hash,
            manifest_hash=evaluation.manifest_hash,
            refusals=evaluation.refusals,
            roles=evaluation.roles,
            reserved_items=evaluation.reserved_items,
            cold_items=cold_items,
            ladder_by_lo=ladder_by_lo,
            evaluated=evaluated,
            error="; ".join(dict.fromkeys(errors)) or None,
        )

    def _ladder(self, snapshot: Any, pool: Sequence[PoolItem], reserved_items: frozenset[str]) -> dict[str, dict[str, Any]]:
        """Each LO's eligible P4 rungs from per-LO signals (annotation only, Q1).

        From the lane classification: an LO with no attempted item is not
        acquired (rung 4), one in the repair lane is fragile (rung 5), one with
        a due item is near its retention limit (rung 9). From the live
        adapters' reads: a pending open-set alarm is misspecification (rung 2),
        an in-progress diagnostic episode is measurement value (rung 3; Q2:
        annotated, never composed). A terminal claim is never required on Today
        (no run), so rung 7 never holds; no milestone, so rung 8 never holds.
        """

        from learnloop.scheduling import staged_policy as sp

        by_lo: dict[str, list[PoolItem]] = {}
        for item in pool:
            by_lo.setdefault(item.learning_object_id, []).append(item)
        try:
            alarmed = {
                str(need.learning_object_id) for need in self.repository.probe_generation_needs(status="pending")
                if getattr(need, "learning_object_id", None)
            }
        except Exception:  # noqa: BLE001 - annotation only
            alarmed = set()
        try:
            from learnloop.placement.state import ignored_opening_episode_ids

            ignored = ignored_opening_episode_ids(self.vault, self.repository)
        except Exception:  # noqa: BLE001 - annotation only
            ignored = frozenset()
        measuring = {
            lo for lo, episode in self.repository.open_probe_episodes().items()
            if getattr(episode, "status", None) == "in_progress" and getattr(episode, "id", None) not in ignored
        }
        ladder: dict[str, dict[str, Any]] = {}
        for lo_id, items in sorted(by_lo.items()):
            signals = sp.StateSignals(
                model_misspecified=lo_id in alarmed,
                decision_relevant_robust_value=1.0 if lo_id in measuring else 0.0,
                target_acquired=any(not item.never_attempted for item in items),
                capability_fragile=any(item.lane == "repair" for item in items),
                terminal_required_unshown=False,
                terminal_reserve_valid=any(item.practice_item_id in reserved_items for item in items),
                retention_near_limit=any(item.due for item in items),
            )
            rungs = sp.ladder_eligibility(snapshot, signals)
            fired = next(rung for rung in rungs if rung["fired"])
            ladder[lo_id] = {
                "eligible": [rung["staged_rule"] for rung in rungs
                             if rung["eligible"] and rung["staged_rule"] not in _FALL_THROUGH_RULES],
                "fired": fired["staged_rule"],
                "fired_rung": fired["rung"],
            }
        return ladder


# -- the source ------------------------------------------------------------------


@dataclass
class StagedFrameSource:
    """``staged_frame_v1``: DL1's packing over the staged-feasible pool, annotated."""

    inner: LegacyLanesSource
    material: FrameMaterial
    refused: Mapping[str, tuple[dict[str, Any], ...]]
    titles: Mapping[str, str]
    pool: Mapping[str, PoolItem]
    name: str = SOURCE_NAME

    def candidates(self, state: PlanState) -> list[BlockCandidate]:
        return [replace(candidate, annotations=self._annotate(candidate)) for candidate in self.inner.candidates(state)]

    def _annotate(self, candidate: BlockCandidate) -> dict[str, Any]:
        items = [self.pool[item_id] for item_id in candidate.item_ids if item_id in self.pool]
        cold = self.material.cold_items
        irreversible = sorted(
            # When open cold checks could not be read, whether serving an item
            # spends one is unknown: it is never in a draw's support (G2).
            {f"cold_check_unknown:{item.practice_item_id}" if cold is None else f"cold_check:{item.practice_item_id}"
             for item in items if cold is None or item.practice_item_id in cold}
            | {f"reserved_assessment:{item.practice_item_id}" for item in items
               if item.practice_item_id in self.material.reserved_items}
        )
        rungs = [self.material.ladder_by_lo[lo] for lo in candidate.learning_object_ids if lo in self.material.ladder_by_lo]
        eligible = sorted({rule for rung in rungs for rule in rung["eligible"]})
        fired = min(rungs, key=lambda rung: rung["fired_rung"])["fired"] if rungs else None
        titles = [self.titles.get(lo, lo) for lo in candidate.learning_object_ids]
        annotations: dict[str, Any] = {
            "reason_code": reason_code(candidate.lane, items, reading=candidate.reading is not None),
            "topic": router_why.topic_phrase(titles),
            "reversible": not irreversible,
            "ladder": {"eligible": eligible, "fired": fired},
        }
        if irreversible:
            annotations["irreversible_because"] = irreversible
        if candidate.reading is not None:
            annotations["section"] = candidate.reading.section_title
        return annotations

    def decision_record(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "source": SOURCE_NAME,
            "snapshot_hash": self.material.snapshot_hash,
            "manifest_hash": self.material.manifest_hash,
            "refused": {item_id: [dict(reason) for reason in reasons] for item_id, reasons in sorted(self.refused.items())},
            "evaluated_items": len(self.pool),
        }
        if self.material.error:
            record["error"] = self.material.error
        return record


@dataclass
class StagedFrameFactory:
    """``PlanPolicy.make_source`` for the staged frame: one :class:`StagedFrame` per env."""

    frame: StagedFrame

    def __call__(self, context: Any) -> StagedFrameSource:
        pool = tuple(context.pool)
        material = self.frame.material(pool)
        laned = {item.practice_item_id: item for item in pool if item.lane is not None}
        refused = {item_id: reasons for item_id, reasons in material.refusals.items() if item_id in laned}
        admitted = tuple(item for item in pool if item.practice_item_id not in refused)
        inner = LegacyLanesSource(
            pool=admitted,
            lanes_allowed=context.lanes_allowed,
            admitted_new_ids=context.admitted_new_ids,
            reading=context.reading,
            reading_full_minutes=context.reading_full_minutes,
            titles=context.titles,
        )
        return StagedFrameSource(
            inner=inner, material=material, refused=refused, titles=dict(context.titles), pool=laned,
        )


# -- the chooser -----------------------------------------------------------------

#: ``(state, feasible) -> learner-state card or None``; built per decision.
CardBuilder = Callable[[PlanState, Sequence[BlockCandidate]], Any]


@dataclass
class StagedChooser:
    """``staged_v1``: lane_quota_v1 over the staged-feasible candidates (Q1),
    deterministic, with the plain "why" and the stored learner-state card."""

    card_builder: CardBuilder | None = None
    name: str = CHOOSER_NAME

    def choose(self, state: PlanState, feasible: Sequence[BlockCandidate]) -> BlockChoice:
        base = LaneQuotaChooser().choose(state, feasible)
        chosen = next((candidate for candidate in feasible if candidate.candidate_id == base.candidate_id), None)
        if chosen is None:
            code = router_why.stop_code(state.minutes_left, STOP_OFFER_MINUTES)
            text = router_why.sentence(code)
        else:
            notes = dict(chosen.annotations or {})
            code = str(notes.get("reason_code") or "")
            text = router_why.sentence(code, topic=notes.get("topic"), section=notes.get("section"))
        record: dict[str, Any] = {
            "mode": MODE,
            "policy": CHOOSER_NAME,
            "why_code": code or None,
            "why_version": router_why.WHY_VERSION,
            # G2: what a draw may ever select (R2b's mixture); an irreversible
            # candidate is chosen only as this rule's deterministic pick.
            "draw_support": [c.candidate_id for c in feasible if (c.annotations or {}).get("reversible", True)],
        }
        irreversible = [c.candidate_id for c in feasible if not (c.annotations or {}).get("reversible", True)]
        if irreversible:
            record["irreversible"] = irreversible
        if self.card_builder is not None:
            try:
                card = self.card_builder(state, feasible)
            except Exception as exc:  # noqa: BLE001 - the card never blocks the plan
                _LOG.warning("router R2a: the learner-state card was not built", exc_info=True)
                record["card_error"] = type(exc).__name__
                card = None
            if card is not None:
                record.update(card_version=card.card_version, card_hash=card.card_hash, card=card.payload())
        return BlockChoice(
            candidate_id=base.candidate_id,
            chosen_by="staged",
            propensity=1.0,
            why=text or base.why,
            why_kind="computed",
            router_record=record,
        )


__all__ = [
    "CHOOSER_NAME",
    "FRESH_EVIDENCE_CHECKS",
    "FRESH_EVIDENCE_MODES",
    "FrameMaterial",
    "MODE",
    "SOURCE_NAME",
    "StagedChooser",
    "StagedFrame",
    "StagedFrameFactory",
    "StagedFrameSource",
    "item_role",
    "reason_code",
]
