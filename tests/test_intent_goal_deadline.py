"""Daily-loop DL2: deadlines are learner goals (§5.4).

"Add a deadline" creates (or moves) a ``Goal`` with ``creation_source:
"learner"``, the due date and the commitment's LOs (their concepts) as its
scope, and links it through a commitment version's ``goal_id``. Linking is not
a choice: it never moves the commitment's choice time. The goal machinery
then treats those LOs as deadline LOs (the plan's deadlines and push).
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.curriculum import commitments as C
from learnloop.daily_plan.engine import _deadlines
from learnloop.intent.control import IntentControlError, Scope, describe
from learnloop.intent.deadline import set_deadline
from learnloop.scheduling.intent.resolution import load_snapshots
from tests.intent_fakes import NOW, make_intent_vault


@pytest.fixture
def iv(tmp_path):
    return make_intent_vault(tmp_path / "vault")


def test_a_deadline_creates_a_learner_goal_linked_by_goal_id(iv):
    applied = iv.choose("learning_object", "lo_a", "learn", NOW)
    result = set_deadline(iv.vault, iv.repository, Scope("learning_object", "lo_a"), "2026-12-01", clock=FrozenClock(NOW))
    iv.reload()
    goal = next(goal for goal in iv.vault.goals if goal.id == result["goal_id"])
    assert goal.creation_source == "learner" and goal.status == "active"
    assert goal.due_at == "2026-12-01T23:59:59Z"
    assert goal.facet_scope.concepts == [iv.vault.learning_objects["lo_a"].concept]
    assert goal.target_recall == pytest.approx(0.90)
    assert C.resolve_head(iv.repository, applied.commitment_id).goal_id == goal.id
    assert "lo_a" in _deadlines(iv.vault, iv.repository)
    view = describe(iv.vault, iv.repository, Scope("learning_object", "lo_a"))
    assert view["current"]["deadline"] == {"goal_id": goal.id, "due_at": "2026-12-01T23:59:59Z"}


def test_moving_the_deadline_updates_the_same_goal(iv):
    iv.choose("learning_object", "lo_a", "master", NOW)
    first = set_deadline(iv.vault, iv.repository, Scope("learning_object", "lo_a"), "2026-12-01", clock=FrozenClock(NOW))
    iv.reload()
    second = set_deadline(iv.vault, iv.repository, Scope("learning_object", "lo_a"), "2026-12-15", clock=FrozenClock(NOW))
    iv.reload()
    assert second["goal_id"] == first["goal_id"] and second["created"] is False
    assert [goal.due_at for goal in iv.vault.goals if goal.id == first["goal_id"]] == ["2026-12-15T23:59:59Z"]


def test_linking_a_deadline_does_not_move_the_choice_time(iv):
    applied = iv.choose("learning_object", "lo_a", "learn", NOW)
    iv.choose("practice_item", "pi_a1", "pause", NOW + timedelta(minutes=1))
    with iv.repository.connection() as connection:
        before = {s.id: s.choice for s in load_snapshots(connection)}[applied.commitment_id]
    set_deadline(iv.vault, iv.repository, Scope("learning_object", "lo_a"), "2026-12-01",
                 clock=FrozenClock(NOW + timedelta(minutes=2)))
    iv.reload()
    with iv.repository.connection() as connection:
        after = {s.id: s.choice for s in load_snapshots(connection)}[applied.commitment_id]
    assert after == before
    assert iv.serving(NOW + timedelta(minutes=3)).intent("pi_a1").disposition == "paused"


def test_a_deadline_needs_an_active_depth_setting(iv):
    with pytest.raises(IntentControlError):
        set_deadline(iv.vault, iv.repository, Scope("learning_object", "lo_a"), "2026-12-01")
    iv.choose("learning_object", "lo_a", "pause", NOW)
    with pytest.raises(IntentControlError):
        set_deadline(iv.vault, iv.repository, Scope("learning_object", "lo_a"), "2026-12-01")
    with pytest.raises(IntentControlError):
        iv.choose("learning_object", "lo_a", "keep", NOW + timedelta(minutes=1))
        set_deadline(iv.vault, iv.repository, Scope("learning_object", "lo_a"), "not a date")
