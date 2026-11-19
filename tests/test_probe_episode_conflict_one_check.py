"""Ledger K9-9: one check for "another probe episode owns this learning object and has measured".

The repair lane's offer and the follow-up router's hard refusal were two copies that disagreed on an empty
learning-object id. Both now ask ``probe_hard_stops.probe_episode_conflict``.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop.diagnosis import machine_checks, probe_episodes, probe_hard_stops as stops
from learnloop.followup_run import router


class _Repository:
    """Only what the check reads: the open episode of a learning object."""

    def __init__(self, episode):
        self.episode = episode
        self.asked: list[str] = []

    def open_probe_episode(self, learning_object_id):
        self.asked.append(learning_object_id)
        return self.episode


def _foreign_episode():
    return SimpleNamespace(id="ep1", origin="placement", status="in_progress")


@pytest.fixture
def measured(monkeypatch):
    monkeypatch.setattr(probe_episodes, "episode_has_observations", lambda _repository, _episode_id: True)


@pytest.mark.parametrize("learning_object_id", ["lo_1", ""], ids=["named", "empty"])
def test_an_open_foreign_episode_that_has_measured_refuses(measured, learning_object_id):
    repository = _Repository(_foreign_episode())
    reason = stops.probe_episode_conflict(repository, factor_id="f1", learning_object_id=learning_object_id)
    assert reason == stops.EPISODE_CONFLICT_REASON
    assert repository.asked == [learning_object_id]


def test_an_unknown_learning_object_asks_nothing(measured):
    repository = _Repository(_foreign_episode())
    assert stops.probe_episode_conflict(repository, factor_id="f1", learning_object_id=None) is None
    assert repository.asked == []


def test_the_factors_own_episode_is_no_conflict(measured):
    own = SimpleNamespace(id="ep1", origin=stops.causal_origin("f1"), status="in_progress")
    assert stops.probe_episode_conflict(_Repository(own), factor_id="f1", learning_object_id="lo_1") is None


@pytest.mark.parametrize("learning_object_id", ["lo_1", ""], ids=["named", "empty"])
def test_the_follow_up_router_asks_the_same_check(measured, monkeypatch, learning_object_id):
    monkeypatch.setattr(stops, "learner_preference", lambda *_a, **_k: "allow")
    monkeypatch.setattr(machine_checks, "pending_machine_checks_for_factor", lambda *_a, **_k: [])
    asked = []

    def check(repository, *, factor_id, learning_object_id):
        asked.append((factor_id, learning_object_id))
        return stops.EPISODE_CONFLICT_REASON

    monkeypatch.setattr(stops, "probe_episode_conflict", check)
    row = {"learning_object_id": learning_object_id, "session_id": None}
    assert router.hard_refusal(None, _Repository(None), row, factor_id="f1") == stops.EPISODE_CONFLICT_REASON
    assert asked == [("f1", learning_object_id)]
