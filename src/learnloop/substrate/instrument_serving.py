"""Which instrument classes the serving surface can actually carry.

Spec: ``spec_measurement_efficiency_v1.md`` §3.A2/§3.A3; implementation plan item
6.4, and the Stage 6 adversarial review that found the gap.

**The defect this exists to prevent.** An instrument whose whole stimulus lives
on a contract the serving surface does not render produces a *silent* failure,
not a hard one: the learner sees a prompt referring to material that is not on
the screen, cannot answer, and the grader (which DOES receive the material)
marks the attempt a miss. The projection then banks negative facet mass for work
the learner was never shown. That is a harmful write manufactured by the serving
path, and it is worse than not having the instrument at all, because it looks
like evidence.

So the rule is: **an item whose stimulus the serving surface cannot render is not
schedulable.** This predicate is the single authority on that question, asked by
every selection and presentation boundary (scheduler, exam pool, probe episodes,
remediation, follow-ups, the staged controller's constraint set, the cold probe,
and the sidecar's direct-open handlers), none of which may import the others.

**RETIRED ARMS — the seam is empty on purpose.** It carried two arms:
``error_hunt_solution_not_rendered`` (§3.A3) and
``laddered_stem_stimulus_not_rendered`` (§3.A2). Both are gone, because the fact
they asserted became false: ``handlers/serializers.item_presentation`` emits
``error_hunt_worked_solution`` and ``laddered_stem_stimulus`` blocks and
``components/ItemPresentation.tsx`` renders them on practice, exam and golden-path
surfaces. Deleting the arms — rather than flipping a flag — is the retirement
protocol this module has always documented, and the inverted tests in
``tests/test_instrument_serving.py`` and
``tests/test_instrument_servability_journeys.py`` are what make the deletion a
visible decision rather than a quiet loosening.

Deliberately NOT a config flag, then or now. A flag would make "can the app show
this?" a preference; it is a fact about the code. The next instrument class that
ships ahead of its renderer adds an arm to :data:`UnservableReason` and a remedy
to :data:`UNSERVABLE_REMEDIES`, and reaches all ~10 boundaries at once because
they already ask. Retiring it deletes the arm again.

What this predicate CANNOT answer, and never could: whether a given item carries
the content its class requires. "Can the app render this class at all" is a fact
about the code; "does this item have a non-blank worked solution" is a fact about
the data, it varies per item, and it is checked where the payload is built —
``learnloop_sidecar.handlers.serializers.item_presentation``, which raises
``item_stimulus_unrenderable``. That check is the remaining guard and stays.
"""

from __future__ import annotations

from typing import Any, Never

#: The closed vocabulary of renderer-blocked instrument classes. ``Never`` means
#: EMPTY, not untyped: no class in the tree is currently blocked, so
#: :func:`unservable_reason` returns ``None`` for every item and a type checker
#: correctly reads each caller's refusal branch as dead. Restore a
#: ``Literal["..."]`` here (and a remedy below) the day an instrument class lands
#: ahead of its renderer again.
UnservableReason = Never

#: Human-readable remedy per arm, for the doctor/CLI surfaces that report them.
#: Empty while :data:`UnservableReason` is: a refusal without a remedy is a dead
#: end, so the two are edited together and the tests pin that they match.
UNSERVABLE_REMEDIES: dict[str, str] = {}


def unservable_reason(item) -> UnservableReason | None:
    """Why ``item`` must not be scheduled, or None when it can be served.

    Returns ``None`` for everything today — see the module docstring: both arms
    retired when their renderer landed. The function and its ~10 call sites stay
    as the seam, because the question ("can this surface carry this instrument
    class?") outlives any particular answer and re-threading it through every
    boundary later is exactly how the Stage 6 gap happened the first time.

    Pure and dependency-free so the scheduler, the exam pool, the probe picker
    and the sidecar handlers can each call it without importing one another.
    Returns the FIRST reason: an item tripping several arms is unservable for
    any of them, and reporting one is enough to keep it out of the queue.
    """

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
    this dict so an arm added to :data:`UnservableReason` reaches every boundary
    at once instead of only the ones someone remembered to update.

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
