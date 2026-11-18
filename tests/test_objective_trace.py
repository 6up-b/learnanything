"""The decision trace's assembly (``router_objective/trace_assembly.py``): each option's row by its kind, the names it
repeats from the plan, and the trace's serialized key order, without a vault. The bytes of real traces are held by the
router's journeys (``test_ro4_objective_serving``, ``test_ro6_serving``, ``test_router_failure_records``) and P-draw."""

from __future__ import annotations

from types import SimpleNamespace

from learnloop.config.schema import LearnLoopConfig
from learnloop.daily_plan import objective_inputs as OI
from learnloop.daily_plan import types as plan_types
from learnloop.daily_plan.types import BlockCandidate
from learnloop.router_objective import mix
from learnloop.router_objective import trace_assembly as TA


def _candidate(candidate_id: str, *, subtype: str | None = None, lane: str = "maintain",
               reading: object = None) -> BlockCandidate:
    return BlockCandidate(
        candidate_id=candidate_id, lane=lane, action="maintain", subtype=subtype, learning_object_ids=("lo_a", "lo_b"),
        item_ids=(f"pi_{candidate_id}",), reading=reading, est_minutes=4.4, planner_value=0.5, reason="r",
        annotations={"reason_code": "maintain", "reversible": True})


def test_the_names_it_repeats_are_the_plans():
    assert TA.STOP_FOR_TODAY == plan_types.STOP_FOR_TODAY
    assert TA.LESSON_OFFER_SUBTYPE == plan_types.LESSON_OFFER_SUBTYPE
    assert TA.MISS_CAUSE_SOURCE == OI.MISS_CAUSE_SOURCE


def test_each_option_is_told_apart_by_its_own_fields_and_labelled():
    titles = {"lo_a": "Vectors", "lo_b": "Bases"}
    block = _candidate("blk")
    offer = _candidate("lesson_offer:lo_a", subtype=TA.LESSON_OFFER_SUBTYPE)
    reading = _candidate("rd", lane="read", reading=SimpleNamespace(section_title="2.1 Spans"))
    assert TA.option_kind(TA.STOP_FOR_TODAY, None) == TA.STOP
    assert TA.option_kind("blk", block) == TA.BLOCK
    assert TA.option_kind("lesson_offer:lo_a", offer) == TA.LESSON_OFFER
    assert TA.option_kind("gone", None) is None
    assert TA.option_label(TA.STOP, None, titles) == "stop for today"
    assert TA.option_label(TA.BLOCK, block, titles) == "maintain: Vectors, Bases (4 min)"
    assert TA.option_label(TA.BLOCK, reading, titles) == "read: 2.1 Spans (4 min)"
    assert TA.option_label(TA.LESSON_OFFER, offer, titles) == "offer a lesson on Vectors, Bases (about 4 min)"
    assert TA.option_label(None, None, titles) is None


def _trace(support, by_id):
    config = LearnLoopConfig()
    parts = mix.components(list(support), support[0], llm=None, numeric_ref=None)
    effective = mix.effective_weights(0.5, [mix.LLM, mix.NUMERIC], to_other_policy=False)
    drawn = mix.draw(list(support), parts, effective, 0.05, "seed")
    return TA.decision_trace(support=support, by_id=by_id, feasible=list(by_id.values()), titles={}, numeric=None,
                             llm=None, decider=None, staged_ref=support[0], weight=(0.5, {"note": "prior"}),
                             effective=effective, pi=drawn.pi, drawn=drawn, seed="seed", config=config,
                             now_iso="2026-10-12T10:00:00Z", guard={}, stop_in_support=TA.STOP_FOR_TODAY in support,
                             card_version=None)


def test_with_no_numeric_answer_the_trace_keeps_its_keys_in_order_and_each_row_its_own():
    by_id = {"blk": _candidate("blk"), "lesson_offer:lo_a": _candidate("lesson_offer:lo_a",
                                                                       subtype=TA.LESSON_OFFER_SUBTYPE)}
    trace = _trace(("blk", "lesson_offer:lo_a", TA.STOP_FOR_TODAY), by_id)
    assert list(trace) == ["candidates", "reference", "v", "cutoff_days", "precision", "filtered", "stop_in_support",
                           "session", "policies", "mixing", "evaluation", "frontier", "inputs_sources", "versions"]
    rows = trace["candidates"]
    assert list(rows) == ["blk", "lesson_offer:lo_a", TA.STOP_FOR_TODAY]
    assert list(rows["blk"]) == ["label", "kind", "main_lo", "minutes", "sensors", "terms", "split", "branches"]
    assert list(rows["lesson_offer:lo_a"]) == [*rows["blk"], "offer"]
    assert rows[TA.STOP_FOR_TODAY]["label"] == "stop for today" and "offer" not in rows[TA.STOP_FOR_TODAY]
    assert trace["policies"]["llm"]["status"] == trace["policies"]["numeric"]["status"] == "not_ready"
    assert trace["filtered"] == {}


def test_a_ref_with_no_candidate_is_labelled_by_its_ref():
    trace = _trace(("insert_now", "gone"), {"insert_now": _candidate("insert_now")})
    assert trace["candidates"]["gone"]["label"] == "gone"
    assert trace["candidates"]["insert_now"]["label"] == "maintain: lo_a, lo_b (4 min)"


def test_the_failure_rule_is_logged_only_where_it_is_not_stageds():
    assert TA.failure_rule_field(False) == {}
    assert TA.failure_rule_field(True) == {"failure_rule": mix.OTHER_POLICY_RULE}
