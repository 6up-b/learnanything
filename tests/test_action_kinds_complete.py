"""Every objective kind needs a rollout effect, a feature group and a trace case."""

from dataclasses import fields, replace

import numpy as np
import pytest

from learnloop.daily_plan.router_chooser import support_order
from learnloop.daily_plan.types import BlockCandidate, PlanState, ReadingTarget
from learnloop.db.stores import router_suggestions
from learnloop.followup_serve import workflow
from learnloop.router import decisions, plan_log
from learnloop.router_objective import learned_tail, rollouts, trace_assembly, types
from learnloop.router_objective.objective import _Ledger
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS


def _changed(before, after):
    return any(not np.array_equal(getattr(before, field.name), getattr(after, field.name)) for field in fields(before))


@pytest.mark.parametrize("kind", sorted(types.KINDS))
def test_action_kind_has_a_rollout_effect(kind):
    review = types.Action("review", "review", ("lo",), minutes=5.0)
    action = types.Action(
        ref=kind, kind=kind, item_los=() if kind == "stop" else ("lo",),
        minutes=0.0 if kind == "stop" else 5.0, steps=(review,) if kind == "sequence" else (),
    )
    if kind in {"stop", "sequence"}:
        # Stop ends the session, and a sequence gets its effects from its steps. Neither has a topical effect
        # of its own for a segment to apply.
        return

    inputs = types.Inputs(
        topics=(types.Topic("lo", 0.0, 0.25),), dated=(), session_minutes=0.0,
        price=types.Price(0.0, 10.0), tail_block_minutes=5.0, tail_block_items=1,
        horizon_days=1.0, fsrs_weights=tuple(FSRS6_DEFAULT_WEIGHTS),
    )
    model = rollouts._Model(inputs, draws=2, seed="kind coverage")
    state = model.initial()
    ledger = _Ledger.zeros(2)
    # With no dated uses, undated density or price, the generic segment adds no value just for taking time.
    model._segment(state, ledger, action, start=np.zeros(2), spent=np.zeros(2), minutes=np.full(2, action.minutes),
                   dated_done=np.zeros((2, 0), dtype=bool), stream=0)
    if _changed(model.initial(), state) or _changed(_Ledger.zeros(2), ledger):
        return

    ordinary, _, _ = model._do(action)
    valued, _ = model.value(action)
    assert _changed(ordinary, valued), f"{kind!r} has no state or ledger effect in the rollout"


@pytest.mark.parametrize("kind", sorted(types.KINDS))
def test_action_kind_has_its_existing_learned_tail_group(kind):
    expected = kind if kind in {"stop", "reading", "probe"} else "practice"
    assert learned_tail.kind_group(kind) == expected


# The same plan block can have different objective kinds. Stop has no block and a sequence represents mid-block steps.
TRACE_CASES = {
    "review": ("block", "maintain", "maintain: Vectors (5 min)"),
    "new_practice": ("block", "new", "new: Vectors (5 min)"),
    "reading": ("block", "new", "new: Spans (5 min)"),
    "probe": ("block", "repair", "repair: Vectors (5 min)"),
    "repair": ("block", "repair", "repair: Vectors (5 min)"),
    "teach_back": ("block", "push", "push: Vectors (5 min)"),
    "lesson": ("lesson_offer", "new", "offer a lesson on Vectors (about 5 min)"),
    "stop": ("stop", None, "stop for today"),
    "sequence": ("block", "maintain", "maintain: Vectors (5 min)"),
}


@pytest.mark.parametrize("kind", sorted(types.KINDS))
def test_action_kind_trace_label_and_reversibility(kind):
    assert kind in TRACE_CASES, f"pin {kind!r}'s plan option, label and reversibility"
    option, lane, label = TRACE_CASES[kind]
    ref = {"lesson": "lesson_offer:lo", "stop": "stop_for_today", "sequence": "continue_current"}.get(kind, kind)
    candidate = None if lane is None else BlockCandidate(
        candidate_id=ref, lane=lane, action="practice", subtype="lesson_offer" if kind == "lesson" else None,
        learning_object_ids=("lo",), item_ids=(),
        reading=ReadingTarget("source", "extraction", "section", "Spans", 300) if kind == "reading" else None,
        est_minutes=5.0, planner_value=1.0, reason="test",
        annotations={"reversible": True} if kind in {"lesson", "sequence"} else {},
    )
    assert trace_assembly.option_kind(ref, candidate) == option
    assert trace_assembly.option_label(option, candidate, {"lo": "Vectors"}) == label

    state = PlanState("plan", "normal", 10.0, 5.0, {}, 0, 0, None)
    if candidate is None:
        assert support_order(state, [], ref, k=2, stop_offered=True, ties_only=False) == [ref]
        assert support_order(state, [], ref, k=2, stop_offered=False, ties_only=False) == []
    else:
        assert support_order(state, [candidate], ref, k=2, stop_offered=False, ties_only=False) == [ref]
        blocked = replace(candidate, annotations={"reversible": False})
        assert support_order(state, [blocked], ref, k=2, stop_offered=False, ties_only=False) == []


def test_ref_copies_across_import_boundaries_stay_equal():
    assert plan_log.OFFER_PREFIX == router_suggestions.OFFER_REF_PREFIX == workflow.LESSON_REF_PREFIX
    assert workflow.LESSON_REF_PREFIX == types.LESSON_OFFER_PREFIX == "lesson_offer:"
    assert plan_log.STOP_REF == decisions.STOP_REF == types.STOP_FOR_TODAY == "stop_for_today"
