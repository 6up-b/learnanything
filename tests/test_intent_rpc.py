"""Daily-loop DL2 RPCs: the control, deadlines, and the served check's DTOs.

``get_intent`` shows the current setting and every choice's consequence and
cost; ``set_intent`` applies one; ``set_intent_deadline`` links a learner goal.
A due "Check once" carries ``intentCheck`` on a session serve (absent on any
other item), the answered check carries it on feedback, and with
``intent.enabled = false`` the control answers off and refuses writes.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

import learnloop.clock as clock_module
import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.helpers import append_config_toml
from tests.intent_fakes import NOW, make_intent_vault


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


@pytest.fixture
def setup(tmp_path, monkeypatch):
    iv = make_intent_vault(tmp_path / "vault")
    moment = {"now": NOW}
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: moment["now"])
    ctx = SidecarContext()
    ctx.load(iv.root)
    ctx.grading_provider_override = "manual"
    return iv, ctx, moment


def test_get_intent_shows_every_choice_with_its_consequence_and_cost(setup):
    _iv, ctx, _moment = setup
    view = _call(ctx, "get_intent", {"scopeKind": "learning_object", "scopeId": "lo_a"})
    assert view["enabled"] is True and view["available"] is True
    assert view["current"]["choice"] == "uncommitted"
    choices = {row["choice"]: row for row in view["choices"]}
    assert list(choices) == ["master", "learn", "keep", "light_touch", "check_once", "reference", "pause", "let_go"]
    assert choices["pause"]["consequence"] == "Pause this topic"
    assert choices["pause"]["costLabel"] == "no reviews"
    assert choices["keep"]["costLabel"].endswith("min/day of reviews")


def test_set_intent_applies_and_get_intent_reads_it_back(setup):
    _iv, ctx, moment = setup
    _call(ctx, "set_intent", {"scopeKind": "learning_object", "scopeId": "lo_a", "choice": "master"})
    moment["now"] = NOW + timedelta(minutes=1)
    result = _call(ctx, "set_intent", {"scopeKind": "practice_item", "scopeId": "pi_a1", "choice": "pause"})
    assert result["applied"]["choice"] == "pause"
    view = _call(ctx, "get_intent", {"scopeKind": "learning_object", "scopeId": "lo_a"})
    assert view["current"] == {"choice": "master", "label": "Master", "source": "this control", "deadline": None,
                               "canAddDeadline": True}
    queue = _call(ctx, "get_today_queue", {})
    served = {row["practiceItemId"] for section in queue["sections"] for row in section["items"]}
    assert "pi_a1" not in served and "pi_a2" in served


def test_set_intent_deadline_links_a_goal_and_reloads(setup):
    _iv, ctx, _moment = setup
    _call(ctx, "set_intent", {"scopeKind": "learning_object", "scopeId": "lo_b", "choice": "learn"})
    view = _call(ctx, "set_intent_deadline", {"scopeKind": "learning_object", "scopeId": "lo_b", "dueAt": "2026-12-01"})
    assert view["deadlineSet"]["created"] is True
    assert view["current"]["deadline"]["dueAt"] == "2026-12-01T23:59:59Z"
    vault, _repository = ctx.require_vault()
    assert any(goal.id == view["deadlineSet"]["goalId"] for goal in vault.goals)


def test_a_due_check_carries_its_cold_view_on_a_session_serve_and_on_feedback(setup):
    iv, ctx, moment = setup
    _call(ctx, "set_intent", {"scopeKind": "practice_item", "scopeId": "pi_b1", "choice": "check_once"})
    moment["now"] = NOW + timedelta(days=8)
    session = _call(ctx, "start_session", {})["sessionId"]
    served = _call(ctx, "get_practice_item", {"practiceItemId": "pi_b1", "sessionId": session})
    assert served["intentCheck"]["banner"].startswith("A check on your own.")
    assert served["intentCheck"]["locatorsHidden"] is True
    assert "practice with help" in served["intentCheck"]["helpHeader"]
    other = _call(ctx, "get_practice_item", {"practiceItemId": "pi_a1", "sessionId": session})
    assert "intentCheck" not in other
    read_only = _call(ctx, "get_practice_item", {"practiceItemId": "pi_b1"})
    assert "intentCheck" not in read_only
    attempt = iv.answer("pi_b1", moment["now"] + timedelta(minutes=1))
    moment["now"] = moment["now"] + timedelta(minutes=2)
    feedback = _call(ctx, "get_feedback", {"attemptId": attempt, "recordOpen": False})
    assert feedback["intentCheck"]["kind"] == "check_once"
    assert feedback["intentCheck"]["restoration"] is None


def test_with_intent_off_the_control_answers_off_and_refuses_writes(tmp_path, monkeypatch):
    iv = make_intent_vault(tmp_path / "vault")
    append_config_toml(iv.root, "[intent]\nenabled = false\n")
    ctx = SidecarContext()
    ctx.load(iv.root)
    view = _call(ctx, "get_intent", {"scopeKind": "learning_object", "scopeId": "lo_a"})
    assert view["enabled"] is False and "choices" not in view
    with pytest.raises(SidecarError):
        _call(ctx, "set_intent", {"scopeKind": "learning_object", "scopeId": "lo_a", "choice": "pause"})
    with pytest.raises(SidecarError):
        _call(ctx, "set_intent_deadline", {"scopeKind": "learning_object", "scopeId": "lo_a", "dueAt": "2026-12-01"})


def test_unknown_scopes_and_choices_are_refused(setup):
    _iv, ctx, _moment = setup
    with pytest.raises(SidecarError):
        _call(ctx, "set_intent", {"scopeKind": "galaxy", "scopeId": "x", "choice": "pause"})
    with pytest.raises(SidecarError):
        _call(ctx, "set_intent", {"scopeKind": "learning_object", "scopeId": "lo_a", "choice": "forever"})
    view = _call(ctx, "get_intent", {"scopeKind": "learning_object", "scopeId": "lo_missing"})
    assert view["available"] is False
