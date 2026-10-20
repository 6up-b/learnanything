"""Daily-loop DL2: disposition exclusion (§5.2, §5.3 step 2).

Pause, Reference and Let go keep an item out of the open queue, the plan and
the request floor, at every scope; resuming (a later choice) brings it back;
the review-load projection leaves excluded items out; with ``intent.enabled =
false`` none of it applies. Held-out material keeps its own exclusions, and a
"Check once" never selects a held-out item.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.curriculum import commitments as C
from learnloop.clock import FrozenClock
from learnloop.daily_plan.engine import PlanEnv, _review_items, _estimator
from learnloop.scheduling import scheduler as scheduler_module
from learnloop.scheduling.serving_exclusions import ServingExclusions
from tests.daily_plan_fakes import MovableClock
from tests.helpers import append_config_toml
from tests.intent_fakes import NOW, make_intent_vault

T = lambda minutes: NOW + timedelta(minutes=minutes)  # noqa: E731


@pytest.fixture
def iv(tmp_path):
    return make_intent_vault(tmp_path / "vault")


@pytest.mark.parametrize("choice", ["pause", "reference", "let_go"])
@pytest.mark.parametrize("scope", [("practice_item", "pi_a1"), ("learning_object", "lo_a"), ("subject", "linear-algebra")])
def test_each_excluding_choice_keeps_its_items_out_at_every_scope(iv, choice, scope):
    iv.choose(scope[0], scope[1], choice, T(0))
    assert "pi_a1" not in iv.queue(T(1))
    assert iv.serving(T(1)).withhold_reason("pi_a1").startswith("intent_")


def test_resuming_with_a_later_choice_brings_items_back(iv):
    iv.choose("learning_object", "lo_a", "pause", T(0))
    assert not {"pi_a1", "pi_a2"} & set(iv.queue(T(1)))
    iv.choose("learning_object", "lo_a", "keep", T(2))
    assert {"pi_a1", "pi_a2"} <= set(iv.queue(T(3)))


def test_an_excluded_request_is_not_a_request(iv):
    C.create_commitment(
        iv.repository, action="help_me_remember", intent_text="written while reading",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": "pi_c1", "role": "required"}],
        depth_preset="remember_key_ideas", clock=FrozenClock(T(0)),
    )
    assert "pi_c1" in iv.requested(T(1))
    iv.choose("practice_item", "pi_c1", "reference", T(2))
    assert "pi_c1" not in iv.requested(T(3))
    assert "pi_c1" not in iv.queue(T(3))


def test_excluded_items_are_left_out_of_the_review_load(iv):
    iv.choose("learning_object", "lo_c", "let_go", T(0))
    env = PlanEnv(vault=iv.vault, repository=iv.repository, clock=MovableClock(T(1)))
    estimator = _estimator(env)
    ids = {item.practice_item_id for item in _review_items(env, estimator, iv.serving(T(1)))}
    assert not {"pi_c1", "pi_c2"} & ids
    assert {"pi_a1", "pi_b1"} <= ids
    assert {"pi_c1", "pi_c2"} <= {item.practice_item_id for item in _review_items(env, estimator)}


def test_with_intent_off_commitments_change_nothing_served(iv):
    iv.choose("subject", "linear-algebra", "pause", T(0))
    assert iv.queue(T(1)) == []
    append_config_toml(iv.root, "[intent]\nenabled = false\n")
    iv.reload()
    assert sorted(iv.queue(T(1))) == ["pi_a1", "pi_a2", "pi_b1", "pi_c1", "pi_c2"]


def _hold_out(monkeypatch, item_ids):
    original = scheduler_module.routine_serving_exclusions

    def patched(vault, repository):
        base = original(vault, repository)
        return ServingExclusions(
            reserved_exam_item_ids=base.reserved_exam_item_ids,
            rung_variant_hold_ids=base.rung_variant_hold_ids,
            staged_owned_item_ids=base.staged_owned_item_ids,
            held_out_item_ids=frozenset(base.held_out_item_ids) | frozenset(item_ids),
        )

    monkeypatch.setattr(scheduler_module, "routine_serving_exclusions", patched)


def test_a_check_once_never_selects_a_held_out_item(iv, monkeypatch):
    iv.choose("learning_object", "lo_a", "check_once", T(0))
    due_day = NOW + timedelta(days=8)
    _hold_out(monkeypatch, {"pi_a1"})
    served = {"pi_a1", "pi_a2"} & set(iv.queue(due_day))
    assert served == {"pi_a2"}
    _hold_out(monkeypatch, {"pi_a1", "pi_a2"})
    assert not {"pi_a1", "pi_a2"} & set(iv.queue(due_day))


def test_an_item_check_on_a_held_out_item_is_never_served(iv, monkeypatch):
    iv.choose("practice_item", "pi_b1", "check_once", T(0))
    _hold_out(monkeypatch, {"pi_b1"})
    assert "pi_b1" not in iv.queue(NOW + timedelta(days=8))
