"""Every objective kind needs a rollout effect, a feature group, a plan candidate that production turns into it and a
trace case."""

from dataclasses import fields, replace
from types import SimpleNamespace

import numpy as np
import pytest

from learnloop.daily_plan import objective_inputs
from learnloop.daily_plan.router_chooser import support_order
from learnloop.daily_plan.types import BlockCandidate, PlanState, ReadingTarget
from learnloop.router_objective import diagnostic_payload, diagnostic_value, learned_tail, rollouts, trace_assembly, types
from learnloop.router_objective.objective import _Ledger
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS


def _changed(before, after):
    return any(not np.array_equal(getattr(before, field.name), getattr(after, field.name)) for field in fields(before))


def _model(*, undated_density: float = 0.0) -> rollouts._Model:
    inputs = types.Inputs(
        topics=(types.Topic("lo", 0.0, 0.25, undated_density=undated_density),), dated=(), session_minutes=0.0,
        price=types.Price(0.0, 10.0), tail_block_minutes=5.0, tail_block_items=1,
        horizon_days=1.0, fsrs_weights=tuple(FSRS6_DEFAULT_WEIGHTS),
    )
    return rollouts._Model(inputs, draws=2, seed="kind coverage")


@pytest.mark.parametrize("kind", sorted(types.KINDS - {types.STOP, types.SEQUENCE}))
def test_action_kind_has_a_rollout_effect(kind):
    action = types.Action(ref=kind, kind=kind, item_los=("lo",), minutes=5.0)
    model = _model()
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


def test_a_probe_with_a_diagnostic_payload_has_its_effect_through_the_successor_evaluator():
    """The same kind with a payload (G2): the rollouts refuse it, and the successor evaluator values it with a state
    or ledger effect (its policy's path differs from acting now with no repair)."""

    model = _model(undated_density=1.0)
    payload = diagnostic_payload.DiagnosticProbe(
        topic="lo", hypotheses=(diagnostic_payload.Hypothesis("h", 1.0),), prior_basis="test",
        channel=diagnostic_payload.MissingChannel("unauthored"),
        repairs=(diagnostic_payload.RepairOption("r", types.Action("r", types.REPAIR, ("lo",), 5.0),
                                                 frozenset({"h"})),))
    probe = types.Action(ref="probe", kind=types.PROBE, item_los=("lo",), minutes=5.0, diagnostic=payload)
    with pytest.raises(ValueError, match="diagnostic payload"):
        model.value(probe)
    out = diagnostic_value.evaluate_probe(model.inputs, probe, decisions=diagnostic_payload.DESIGN_RECOMMENDATIONS,
                                          draws=2, seed="kind coverage").by_ref()
    assert out["probe"].q_draws != out[f"{diagnostic_value.ACT_NOW}none"].q_draws


def test_stop_ends_the_session_in_its_accepted_branch():
    """Stop has no topical effect: its value is the learner's acceptance mix of ending today's session now (the tail
    from tomorrow) and overriding it (the tail's next block today)."""

    model = _model(undated_density=1.0)
    stop = types.Action(ref=types.STOP_FOR_TODAY, kind=types.STOP)
    valued, extra = model.value(stop)
    ended = model._stop_accepted()
    overridden, _state, _minutes = model._do(model.tail_action(), stream=1)
    assert not np.array_equal(ended.q, overridden.q), "ending the session must differ from another block today"
    p = model.theta.stop_accept
    np.testing.assert_allclose(valued.q, p * ended.q + (1 - p) * overridden.q)
    assert extra["branches"]["accepted"] == pytest.approx(float(ended.q.mean()))
    assert extra["branches"]["overridden"] == pytest.approx(float(overridden.q.mean()))


def test_a_sequence_is_valued_by_its_steps():
    """A sequence has no effect of its own: one step is valued as that step, and each further step adds its own."""

    model = _model(undated_density=1.0)
    review = types.Action("review", types.REVIEW, ("lo",), minutes=5.0)
    new = types.Action("new", types.NEW_PRACTICE, ("lo",), minutes=5.0)
    one = types.Action("one", types.SEQUENCE, ("lo",), minutes=5.0, steps=(review,))
    two = types.Action("two", types.SEQUENCE, ("lo", "lo"), minutes=10.0, steps=(review, new))
    as_review, review_state, review_minutes = model._do(review)
    as_one, one_state, one_minutes = model._do(one)
    assert not _changed(as_review, as_one) and not _changed(review_state, one_state)
    np.testing.assert_array_equal(review_minutes, one_minutes)
    _as_two, two_state, two_minutes = model._do(two)
    assert _changed(one_state, two_state), "the second step changed nothing"
    assert np.all(two_minutes > one_minutes)


@pytest.mark.parametrize("kind", sorted(types.KINDS))
def test_action_kind_has_its_existing_learned_tail_group(kind):
    expected = kind if kind in {"stop", "reading", "probe"} else "practice"
    assert learned_tail.kind_group(kind) == expected


# Each kind's plan candidate as the plan builds it: its lane, its item (by practice mode, ``_ITEMS``), and its trace
# option and label. Stop has no candidate and a sequence is mid-block steps; both are valued directly above.
_ITEMS = {"pi_recall": "free_recall", "pi_probe": "diagnostic_probe", "pi_teach": "teach_back"}
PLAN_CASES = {
    "review": ("maintain", "pi_recall", "block", "maintain: Vectors (5 min)"),
    "new_practice": ("new", "pi_recall", "block", "new: Vectors (5 min)"),
    "reading": ("new", None, "block", "new: Spans (5 min)"),
    "probe": ("repair", "pi_probe", "block", "repair: Vectors (5 min)"),
    "repair": ("repair", "pi_recall", "block", "repair: Vectors (5 min)"),
    "teach_back": ("push", "pi_teach", "block", "push: Vectors (5 min)"),
    "lesson": ("new", None, "lesson_offer", "offer a lesson on Vectors (about 5 min)"),
}
NO_CANDIDATE = {"stop", "sequence"}


def _candidate(kind: str) -> BlockCandidate:
    lane, item, _option, _label = PLAN_CASES[kind]
    lesson = kind == "lesson"
    return BlockCandidate(
        candidate_id=f"{types.LESSON_OFFER_PREFIX}lo" if lesson else kind, lane=lane, action="practice",
        subtype=types.LESSON_OFFER_SUBTYPE if lesson else None, learning_object_ids=("lo",),
        item_ids=(item,) if item else (),
        reading=ReadingTarget("source", "extraction", "section", "Spans", 300) if kind == "reading" else None,
        est_minutes=5.0, planner_value=1.0, reason="test",
        annotations={"reversible": True, **({"lesson_offer": {"learning_object_id": "lo"}} if lesson else {})},
    )


def test_every_kind_has_a_plan_case_or_is_valued_without_a_candidate():
    assert set(PLAN_CASES) | NO_CANDIDATE == types.KINDS
    assert not set(PLAN_CASES) & NO_CANDIDATE


@pytest.mark.parametrize("kind", sorted(PLAN_CASES))
def test_a_plan_candidate_reaches_its_kind_through_production_dispatch(kind):
    vault = SimpleNamespace(config=None, practice_items={
        item: SimpleNamespace(practice_mode=mode, learning_object_id="lo") for item, mode in _ITEMS.items()})
    action = objective_inputs.action_for(vault, None, _candidate(kind), practiced=set(), spread=0.0)
    assert action.kind == kind


@pytest.mark.parametrize("kind", sorted(PLAN_CASES))
def test_a_plan_candidates_trace_label_and_reversibility(kind):
    candidate = _candidate(kind)
    _lane, _item, option, label = PLAN_CASES[kind]
    assert trace_assembly.option_kind(candidate.candidate_id, candidate) == option
    assert trace_assembly.option_label(option, candidate, {"lo": "Vectors"}) == label
    state = PlanState("plan", "normal", 10.0, 5.0, {}, 0, 0, None)
    ref = candidate.candidate_id
    assert support_order(state, [candidate], ref, k=2, stop_offered=False, ties_only=False) == [ref]
    blocked = replace(candidate, annotations={"reversible": False})
    assert support_order(state, [blocked], ref, k=2, stop_offered=False, ties_only=False) == []


def test_stops_trace_label_and_support():
    ref = types.STOP_FOR_TODAY
    assert trace_assembly.option_kind(ref, None) == "stop"
    assert trace_assembly.option_label("stop", None, {}) == "stop for today"
    state = PlanState("plan", "normal", 10.0, 5.0, {}, 0, 0, None)
    assert support_order(state, [], ref, k=2, stop_offered=True, ties_only=False) == [ref]
    assert support_order(state, [], ref, k=2, stop_offered=False, ties_only=False) == []
