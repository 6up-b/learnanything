"""Daily-loop DL2: resolving an item's intent, the most recent choice wins (§5.3, G4).

Every case runs through the real control (``apply_choice``) and the real
scheduler (``build_due_queue``); clocks advance between choices so "most
recent" is a stored-time fact. "Check once" cases are the spec's §13 list.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.curriculum import commitments as C
from learnloop.daily_plan.intent_cost import cost_function
from learnloop.intent.control import Scope, preview
from learnloop.scheduling.intent.model import ChoiceStamp, CommitmentSnapshot
from learnloop.scheduling.intent.resolution import Resolution, load_snapshots
from learnloop.scheduling.intent.serving import check_date

from tests.intent_fakes import NOW, make_intent_vault

T = lambda minutes: NOW + timedelta(minutes=minutes)  # noqa: E731
TARGETS = {
    "keep_in_touch": 0.80,
    "remember_key_ideas": 0.85,
    "work_fluently": 0.90,
    "master_tasks_like_these": 0.92,
    "uncommitted": 0.90,
}


@pytest.fixture
def iv(tmp_path):
    return make_intent_vault(tmp_path / "vault")


def _request(iv, item_id: str, at) -> str:
    """A request commitment another path made (the Reader's written question)."""

    commitment = C.create_commitment(
        iv.repository,
        action="help_me_remember",
        intent_text="my own question",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": item_id, "role": "required"}],
        depth_preset="remember_key_ideas",
        client_idempotency_key=f"reader:{item_id}",
        clock=FrozenClock(at),
    )
    return commitment.id


def test_with_no_commitment_every_item_is_uncommitted_and_intent_builds_nothing(iv):
    assert iv.serving(NOW) is None
    assert sorted(iv.queue(NOW)) == sorted(["pi_a1", "pi_a2", "pi_b1", "pi_c1", "pi_c2"])


def test_an_item_pause_under_an_lo_master_excludes_the_item_and_the_rest_stays_master(iv):
    iv.choose("learning_object", "lo_a", "master", T(0))
    iv.choose("practice_item", "pi_a1", "pause", T(1))
    serving = iv.serving(T(2))
    assert serving.intent("pi_a1").disposition == "paused"
    assert serving.intent("pi_a2").choice == "master"
    assert serving.intent("pi_a2").recall_target == pytest.approx(0.92)
    queue = iv.queue(T(2))
    assert "pi_a1" not in queue and "pi_a2" in queue


def test_a_subject_pause_after_adoption_excludes_the_adopted_items_requests_included(iv):
    _request(iv, "pi_b1", T(0))
    assert "pi_b1" in iv.requested(T(1))
    iv.choose("subject", "linear-algebra", "pause", T(2))
    assert "pi_b1" not in iv.requested(T(3))
    assert iv.queue(T(3)) == []


def test_an_lo_choice_after_an_item_pause_re_includes_the_item(iv):
    iv.choose("practice_item", "pi_a1", "pause", T(0))
    assert "pi_a1" not in iv.queue(T(1))
    iv.choose("learning_object", "lo_a", "learn", T(2))
    assert iv.serving(T(3)).intent("pi_a1").choice == "learn"
    assert "pi_a1" in iv.queue(T(3))


def test_a_request_commitment_never_lowers_a_control_chosen_depth(iv):
    iv.choose("learning_object", "lo_a", "master", T(0))
    _request(iv, "pi_a1", T(1))  # newer, remember_key_ideas (0.85)
    intent = iv.serving(T(2)).intent("pi_a1")
    assert intent.disposition == "active"
    assert intent.depth_preset == "master_tasks_like_these"
    assert intent.recall_target == pytest.approx(0.92)


def test_choosing_master_on_an_item_is_not_a_request(iv):
    iv.choose("practice_item", "pi_b1", "master", T(0))
    assert "pi_b1" not in iv.requested(T(1))


def test_ties_go_to_the_item_level_then_the_higher_target():
    stamp = ChoiceStamp("2026-10-12T09:00:00Z", "01AAAA")
    lo_keep = CommitmentSnapshot(
        id="c_lo", action="help_me_remember", created_at=stamp.at, depth_preset="remember_key_ideas",
        disposition="paused", retired=False, choice=stamp, learning_object_targets=frozenset({"lo"}),
    )
    item_keep = replace(lo_keep, id="c_item", disposition="active", learning_object_targets=frozenset(),
                        item_targets=frozenset({"pi"}), choice=ChoiceStamp(stamp.at, "00AAAA"))
    resolution = Resolution([lo_keep, item_keep], TARGETS)
    assert resolution.for_item("pi", "lo").decided_by == "c_item"
    # Same level, same second: the higher recall target decides.
    low = replace(lo_keep, id="c_low", depth_preset="keep_in_touch", disposition="paused", choice=ChoiceStamp(stamp.at, "ZZ"))
    high = replace(lo_keep, id="c_high", depth_preset="master_tasks_like_these", disposition="active",
                   choice=ChoiceStamp(stamp.at, "00"))
    assert Resolution([low, high], TARGETS).for_item("pi2", "lo").decided_by == "c_high"


@pytest.mark.parametrize(
    "steps,scope,choice",
    [
        ([], ("learning_object", "lo_a"), "pause"),
        ([("learning_object", "lo_a", "master"), ("practice_item", "pi_a1", "pause")], ("learning_object", "lo_a"), "keep"),
        ([("practice_item", "pi_c1", "keep"), ("learning_object", "lo_b", "learn")], ("subject", "linear-algebra"), "pause"),
        ([("learning_object", "lo_a", "learn")], ("practice_item", "pi_a2"), "check_once"),
        ([("practice_item", "pi_a1", "master")], ("learning_object", "lo_a"), "light_touch"),
    ],
)
def test_the_consequence_line_equals_the_resolved_result(iv, steps, scope, choice):
    for minute, (kind, scope_id, step_choice) in enumerate(steps):
        iv.choose(kind, scope_id, step_choice, T(minute))
    at = T(len(steps) + 1)
    shown = preview(iv.vault, iv.repository, Scope(*scope), choice, clock=FrozenClock(at))
    iv.choose(scope[0], scope[1], choice, at)
    serving = iv.serving(at)
    for item_id, expected in shown.after.items():
        actual = serving.intent(item_id)
        assert (actual.disposition, actual.choice, actual.recall_target) == (
            expected.disposition, expected.choice, expected.recall_target,
        ), item_id
    replaced_items = sum(1 for cid in shown.replaced_commitment_ids)
    assert ("replaces your earlier setting" in shown.consequence) == bool(replaced_items)


def test_the_consequence_line_names_what_it_replaces(iv):
    iv.choose("learning_object", "lo_a", "master", T(0))
    iv.choose("practice_item", "pi_c1", "keep", T(1))
    iv.choose("learning_object", "lo_b", "learn", T(2))
    cost = cost_function(iv.vault, iv.repository, clock=FrozenClock(T(3)))
    shown = preview(iv.vault, iv.repository, Scope("subject", "linear-algebra"), "pause", clock=FrozenClock(T(3)), cost=cost)
    assert shown.consequence.startswith("Pause ")
    assert "replaces your earlier setting on 2 topics and 1 item" in shown.consequence
    assert shown.cost_label == "no reviews"


def test_the_projected_cost_follows_the_recall_target(iv):
    at = FrozenClock(T(0))
    cost = cost_function(iv.vault, iv.repository, clock=at)
    minutes = {
        choice: preview(iv.vault, iv.repository, Scope("learning_object", "lo_a"), choice, clock=at, cost=cost)
        for choice in ("master", "learn", "keep", "light_touch", "check_once", "pause")
    }
    assert minutes["master"].cost_minutes_per_day >= minutes["learn"].cost_minutes_per_day
    assert minutes["learn"].cost_minutes_per_day >= minutes["keep"].cost_minutes_per_day
    assert minutes["keep"].cost_minutes_per_day >= minutes["light_touch"].cost_minutes_per_day
    assert minutes["learn"].cost_label.endswith("min/day of reviews")
    assert minutes["check_once"].cost_label.startswith("one check, about ")
    assert (minutes["pause"].cost_minutes_per_day, minutes["pause"].cost_label) == (0.0, "no reviews")


# -- "Check once" (§5.2; §13's DL2 list) ---------------------------------------


def test_check_once_on_an_uncommitted_item_serves_one_check_after_the_delay_then_nothing(iv):
    iv.choose("practice_item", "pi_b1", "check_once", T(0))
    assert "pi_b1" not in iv.queue(T(60 * 24))  # day 1: held back
    due_day = NOW + timedelta(days=7, minutes=1)
    assert "pi_b1" in iv.queue(due_day)
    assert "pi_b1" in iv.requested(due_day)
    iv.answer("pi_b1", due_day + timedelta(minutes=5))
    later = due_day + timedelta(days=3)
    assert "pi_b1" not in iv.queue(later)
    assert iv.serving(later).intent("pi_b1").disposition == "satisfied"


def test_check_once_on_an_item_under_an_older_lo_master_then_nothing_even_under_master(iv):
    iv.choose("learning_object", "lo_a", "master", T(0))
    iv.choose("practice_item", "pi_a1", "check_once", T(1))
    assert "pi_a1" not in iv.queue(T(2))
    assert "pi_a2" in iv.queue(T(2))
    due_day = NOW + timedelta(days=8)
    assert "pi_a1" in iv.queue(due_day)
    iv.answer("pi_a1", due_day)
    assert "pi_a1" not in iv.queue(due_day + timedelta(days=1))
    assert "pi_a2" in iv.queue(due_day + timedelta(days=1))


def test_an_lo_check_serves_exactly_one_item_after_the_delay_then_none(iv):
    iv.choose("learning_object", "lo_a", "check_once", T(0))
    assert not {"pi_a1", "pi_a2"} & set(iv.queue(T(1)))
    due_day = NOW + timedelta(days=8)
    served = {"pi_a1", "pi_a2"} & set(iv.queue(due_day))
    assert len(served) == 1
    (check_item,) = served
    iv.answer(check_item, due_day)
    after = due_day + timedelta(days=1)
    assert not {"pi_a1", "pi_a2"} & set(iv.queue(after))


def test_a_later_lo_choice_re_includes_items_after_their_check(iv):
    iv.choose("learning_object", "lo_a", "check_once", T(0))
    due_day = NOW + timedelta(days=8)
    iv.answer("pi_a1", due_day)
    assert not {"pi_a1", "pi_a2"} & set(iv.queue(due_day + timedelta(hours=1)))
    iv.choose("learning_object", "lo_a", "learn", due_day + timedelta(hours=2))
    assert {"pi_a1", "pi_a2"} <= set(iv.queue(due_day + timedelta(hours=3)))


def test_a_check_replaced_before_its_date_is_never_served_as_a_check(iv):
    iv.choose("practice_item", "pi_a1", "check_once", T(0))
    iv.choose("learning_object", "lo_a", "master", T(10))
    due_day = NOW + timedelta(days=8)
    serving = iv.serving(due_day)
    assert serving.intent("pi_a1").choice == "master"
    assert serving.due_checks() == []
    assert not serving.is_check_candidate("pi_a1")
    # Answering it later never "satisfies" the replaced check into exclusion.
    iv.answer("pi_a1", due_day)
    assert "pi_a1" in iv.queue(due_day + timedelta(days=30))


def test_satisfying_a_check_does_not_move_its_choice_time(iv):
    applied = iv.choose("practice_item", "pi_b1", "check_once", T(0))
    with iv.repository.connection() as connection:
        before = {s.id: s.choice for s in load_snapshots(connection)}
    C.satisfy_single_check(iv.repository, commitment_id=applied.commitment_id, clock=FrozenClock(T(60 * 24 * 9)))
    with iv.repository.connection() as connection:
        after = {s.id: s for s in load_snapshots(connection)}
    assert after[applied.commitment_id].choice == before[applied.commitment_id]
    assert after[applied.commitment_id].disposition == "satisfied"


def test_a_satisfied_check_still_decides_over_an_older_lo_master(iv):
    iv.choose("learning_object", "lo_a", "master", T(0))
    applied = iv.choose("practice_item", "pi_a2", "check_once", T(1))
    C.satisfy_single_check(iv.repository, commitment_id=applied.commitment_id, clock=FrozenClock(NOW + timedelta(days=9)))
    assert iv.serving(NOW + timedelta(days=9)).intent("pi_a2").disposition == "satisfied"
    assert "pi_a2" not in iv.queue(NOW + timedelta(days=9))


def test_retired_commitments_drop_out(iv):
    applied = iv.choose("practice_item", "pi_b1", "pause", T(0))
    C.retire(iv.repository, commitment_id=applied.commitment_id, clock=FrozenClock(T(1)))
    assert iv.serving(T(2)) is None or iv.serving(T(2)).intent("pi_b1").uncommitted
    assert "pi_b1" in iv.queue(T(2))


def test_a_source_locator_only_commitment_covers_no_item(iv):
    C.create_commitment(
        iv.repository, action="test_me_later", intent_text="a passage",
        targets=[{"target_kind": "source_locator", "target_ref": "ex:1:span", "role": "required"}],
        depth_preset="keep_in_touch", clock=FrozenClock(T(0)),
    )
    assert iv.serving(T(1)) is None


def test_check_dates_read_the_due_hint_then_the_default_delay():
    base = CommitmentSnapshot(
        id="c", action="test_me_later", created_at="2026-10-12T09:00:00Z", depth_preset="keep_in_touch",
        disposition="one_check_pending", retired=False, choice=ChoiceStamp("2026-10-12T09:00:00Z", "x"),
    )
    when, source = check_date(base, default_days=7)
    assert (when.isoformat(), source) == ("2026-10-19T09:00:00+00:00", "test_me_later_days")
    when, source = check_date(replace(base, due_hint="2026-10-14T12:00:00Z"), default_days=7)
    assert (when.isoformat(), source) == ("2026-10-14T12:00:00+00:00", "due_hint")
    when, source = check_date(replace(base, due_hint="2026-10-15"), default_days=7)
    assert source == "due_hint"
    assert when.astimezone().date().isoformat() == "2026-10-15"
    assert when.astimezone().hour == 0
