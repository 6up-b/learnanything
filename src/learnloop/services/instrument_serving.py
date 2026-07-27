"""Which instrument classes the serving surface can actually carry.

Spec: ``spec_measurement_efficiency_v1.md`` §3.A2/§3.A3; implementation plan item
6.4, and the Stage 6 adversarial review that found the gap.

**The defect this exists to prevent.** An error hunt's whole stimulus is its
worked solution, and a laddered stem's whole stimulus is the shared setup its
parts climb. Both live on the item and neither reaches the practice surface yet.
Serving one anyway does not produce a hard failure — it produces a *silent* one:
the learner sees a prompt saying "correct the worked solution below" with no
solution, cannot answer, and the grader (which DOES receive the solution) marks
every planted error missed. The projection then banks negative facet mass for a
repair the learner was never shown the material to make. That is a harmful write
manufactured by the serving path, and it is worse than not having the instrument
at all, because it looks like evidence.

So the rule is: **an item whose stimulus the serving surface cannot render is not
schedulable.** Authoring, gating, storage and the revert-criterion producers all
work; what is missing is one field on one DTO. Until it lands, this predicate
keeps the item out of the queue and *says why*, rather than letting a
half-shipped instrument write learner state.

Deliberately NOT a config flag. A flag would make "can the app show this?" a
preference; it is a fact about the code, and the correct way to remove this
filter is to make the fact false — render the stimulus, then delete the arm here.
The tests that pin each arm are what make that deletion visible as a decision
rather than a quiet loosening.
"""

from __future__ import annotations

from typing import Any, Literal

UnservableReason = Literal[
    "error_hunt_solution_not_rendered",
    "laddered_stem_stimulus_not_rendered",
]

#: Human-readable remedy per arm, for the doctor/CLI surfaces that report them.
UNSERVABLE_REMEDIES: dict[str, str] = {
    "error_hunt_solution_not_rendered": (
        "the practice surface does not carry `error_hunt.worked_solution_md`, so the "
        "learner would be asked to repair work they cannot see"
    ),
    "laddered_stem_stimulus_not_rendered": (
        "the practice surface does not carry `laddered_stem.stimulus_md`, so a part "
        "would be served without the stimulus it climbs"
    ),
}


def unservable_reason(item) -> UnservableReason | None:
    """Why ``item`` must not be scheduled, or None when it can be served.

    Pure and dependency-free so both the scheduler and the exam pool can call it
    without either importing the other. Returns the FIRST reason; an item
    carrying both contracts is unservable for either, and reporting one is
    enough to keep it out of the queue.
    """

    if getattr(item, "error_hunt", None) is not None:
        return "error_hunt_solution_not_rendered"
    if getattr(item, "laddered_stem", None) is not None:
        return "laddered_stem_stimulus_not_rendered"
    return None


#: Stable wire code for a refused *direct open* (as opposed to a skipped
#: candidate). One code, because the surface's decision is the same for every
#: arm — do not open, say why — and the arm travels in ``details.reason`` where a
#: client can branch on it without parsing prose.
UNSERVABLE_ERROR_CODE = "item_not_servable"


def unservable_refusal(item) -> dict[str, Any] | None:
    """The refusal payload for ``item``, or None when it can be served.

    Selection and presentation boundaries need the SAME two facts — which arm
    fired and what the remedy is — but they act on them differently: a selection
    path skips the item and records the skip beside the one it chose, while a
    direct-open path must refuse the whole call. Both build their answer from
    this dict so a third arm added to :data:`UnservableReason` reaches every
    boundary at once instead of only the ones someone remembered to update.

    ``practice_item_id`` is included because a skip list is read away from the
    item it describes; a reason without an id is not actionable.

    Pure and dependency-free for the reason stated in the module docstring: the
    scheduler, the exam pool, the retry picker and the sidecar handlers all call
    it, and none of them may import the others.
    """

    reason = unservable_reason(item)
    if reason is None:
        return None
    return {
        "practice_item_id": getattr(item, "id", None),
        "reason": reason,
        "remedy": UNSERVABLE_REMEDIES[reason],
    }
