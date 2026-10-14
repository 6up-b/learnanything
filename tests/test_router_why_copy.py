"""Router R2a: the learner-facing "why" is plain words (plan §7, UX §9).

Every sentence :mod:`learnloop.router.why` can produce passes the server-side
copy deny-list (the desktop list plus the router plan's own terms: lanes,
probe, EVSI, facet, LO, mvp, propensity, Decider, staged, queue, due, ...),
and so does every "why" the staged chooser writes on a real plan. The
deny-list itself catches what it should.
"""

from __future__ import annotations

import pytest

from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.daily_plan.lanes import (
    ASSUMED_CHECK_REASON,
    GAP_COMMITMENT_CHECK_REASON,
    GAP_SOONER_CHECK_REASON,
    PoolItem,
)
from learnloop.daily_plan.policy import policy_for
from learnloop.daily_plan.staged_frame import reason_code
from learnloop.router import why

from tests.daily_plan_fakes import MovableClock, make_env, record_attempt
from tests.test_daily_plan_build import _seed_wide, _wide_items, _wide_vault

TOPICS = ("Eigenvalues", "Eigenvalues and Bases", "Eigenvalues and 2 more topics")


@pytest.mark.parametrize("code", sorted(why.SENTENCES))
@pytest.mark.parametrize("topic", TOPICS)
def test_every_sentence_is_plain(code, topic):
    text = why.sentence(code, topic=topic, section="3.2 Bases")
    assert text and text[0].isupper() and text.endswith((".", "?"))
    assert why.jargon_in(text) == [], (code, text)


def test_the_deferral_and_details_lines_are_plain():
    for reason in ("constraint:hard_exposure_collision:exact_surface_collision",
                   "constraint:assessment_reservation:reserved_assessment_surface",
                   "constraint:same_facet_dispersion:same_facet_back_to_back", "evsi:waiting", None):
        assert why.jargon_in(why.deferral_sentence(reason)) == [], reason
    assert why.jargon_in(why.DETAILS_STAGED) == []


def test_the_deny_list_catches_the_internal_terms():
    for text in ("maintain: 2 reviews past their 90% recall target", "a probe on this LO", "EVSI says so",
                 "the staged rule", "propensity 0.4", "the Decider picked it", "items due today", "the lane",
                 "mvp-0.23", "a facet check", "the queue"):
        assert why.jargon_in(text), text
    assert why.jargon_in("Eigenvalues again, before it slips.") == []


def test_topic_phrases_name_one_two_or_many_topics():
    assert why.topic_phrase(["A"]) == "A"
    assert why.topic_phrase(["A", "B"]) == "A and B"
    assert why.topic_phrase(["A", "B", "C"]) == "A and 2 more topics"
    assert why.topic_phrase([]) == "this topic"


def _item(**overrides) -> PoolItem:
    base = dict(practice_item_id="pi", learning_object_id="lo", rank=0, priority=0.5, lane="maintain",
                reason="past its review date", est_minutes=2.0, never_attempted=False)
    base.update(overrides)
    return PoolItem(**base)


def test_reason_codes_follow_the_lane_and_its_items():
    assert reason_code("repair", [_item(lane="repair", followup=True)]) == "repair_followup"
    assert reason_code("repair", [_item(lane="repair", reason="an open diagnosed problem on this topic")]) == (
        "repair_open_problem"
    )
    assert reason_code("repair", [_item(lane="repair", reason="a recent error on this topic")]) == "repair_recent_errors"
    assert reason_code("maintain", [_item()]) == "review"
    assert reason_code("maintain", [_item(check_kind="assumed_check", reason=ASSUMED_CHECK_REASON)]) == "assumed_check"
    assert reason_code("maintain", [_item(check_kind="assumed_check", reason=GAP_COMMITMENT_CHECK_REASON)]) == (
        "gap_check_added"
    )
    assert reason_code("maintain", [_item(check_kind="assumed_check", reason=GAP_SOONER_CHECK_REASON)]) == (
        "gap_check_sooner"
    )
    assert reason_code("maintain", [_item(check_kind="project_probe")]) == "project_check"
    assert reason_code("maintain", [_item(check_kind="project_probe"), _item(check_kind="check_once")]) == (
        "scheduled_checks"
    )
    assert reason_code("new", [_item(lane="new", never_attempted=True)]) == "new_material"
    assert reason_code("new", [], reading=True) == "reading"
    assert reason_code("push", [_item(lane="push")]) == "goal_step"
    assert all(code in why.SENTENCES for code in (
        "repair_followup", "repair_open_problem", "repair_recent_errors", "review", "assumed_check", "gap_check_added",
        "gap_check_sooner", "project_check", "scheduled_checks", "new_material", "reading", "goal_step",
    ))


def test_every_why_the_staged_chooser_writes_on_a_plan_is_plain(tmp_path):
    paths = _wide_vault(tmp_path, version=ROUTER_STAGED_FRAME_ALGORITHM_VERSION)
    clock = MovableClock()
    env = make_env(paths.root, _wide_items(), clock=clock, session_id="s1")
    _seed_wide(env.repository)
    env.policy = policy_for(env.vault, env.repository, session_id="s1", clock=clock)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    for _ in range(30):
        record, step = advance(env, serve=True)
        if step["kind"] != "item":
            break
        clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], clock.now())
    whys = [block.chosen["why"] for block in record.blocks] + [receipt.chosen.get("why", "") for receipt in record.receipts]
    assert whys
    for text in whys:
        assert text and why.jargon_in(text) == [], text
