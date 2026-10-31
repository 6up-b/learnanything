"""Codex CLI 0.165.0: two new default-on features switched off; bundled skills stay off.

Stage codex-cli-0165-lockdown (2026-10-31, docs/reviews/codex-cli-0165-lockdown.md).
codex-cli 0.165.0 turns on ``prediction_preserve_parent_tools`` (new: a
prediction fork or ``thread/sample`` with MCP disabled keeps the parent's tool
declarations) and ``reasoning_effort_override`` (under development and off in
0.164.0: an effort change becomes a ``configuration_update`` input item). Both
honour ``-c features.<key>=false``, so both are now switched off on every
launch; the launch check still refuses if either reads on. ``skills.bundled``
is not a feature but a config table: its switch is ``skills.bundled.enabled``,
sent on every launch since hardening round 3, and its effect is read back from
``debug prompt-input``. Everything here runs on a fake ``codex``
(tests/codex_cli_fakes.py); the installed CLI is exercised by the launch-check
tests in test_codex_isolation_mcp_check.py, test_codex_lockdown_round2.py,
test_codex_lockdown_round3.py and test_diagnosis_isolation.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.ai.providers import codex_lockdown as lockdown
from learnloop.ai.providers.codex import SdkCodexClient, isolated_turn_overrides
from learnloop.ai.transport import StructuredRequest
from learnloop.config import CodexConfig
from learnloop.diagnosis.offline_review.judge import LinkJudgment
from tests.codex_cli_fakes import FEATURES, fake_codex_calls, write_fake_codex
from tests.project_support import install_fake_codex_sdk

ANSWER = '{"links": []}'
NEW_0165 = ("prediction_preserve_parent_tools", "reasoning_effort_override")
RETIRED = ("realtime_conversation", "worktrees")
BUNDLED = ("imagegen", "openai-docs", "skill-creator", "skill-installer")


@pytest.fixture(autouse=True)
def _fresh_check_cache():
    lockdown.clear_check_cache()
    yield
    lockdown.clear_check_cache()


def _client(tmp_path: Path, program: Path) -> SdkCodexClient:
    vault_root = tmp_path / "vault"
    vault_root.mkdir(exist_ok=True)
    return SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"), sdk_codex_bin=str(program),
                                      model="gpt-5.6-sol"), vault_root)


def _turn(client: SdkCodexClient):
    return client.complete(StructuredRequest(purpose="tutor_qa", prompt="p", result_model=LinkJudgment))


def _launched(log: Path) -> list[list[str]]:
    return [call["overrides"] for call in fake_codex_calls(log) if call["command"][:1] == ["app-server"]]


def _feature_lists(log: Path) -> list[dict]:
    return [call for call in fake_codex_calls(log) if call["command"] == ["features", "list"]]


def _cli_0165(tmp_path: Path, *, extra: tuple[str, ...] = (), **spec):
    """A fake CLI that, like 0.165.0, lists the two new features on by default (their switch works)
    and the two 0.164.0 retired flags on at stage ``removed`` (their switch ignored)."""

    features = [*FEATURES, *NEW_0165, *RETIRED, *extra]
    stages = {name: "removed" for name in RETIRED} | dict(spec.pop("feature_stages", {}))
    ignored = [*RETIRED, *spec.pop("ignored_features", ())]
    return write_fake_codex(tmp_path / "bin", features=features, feature_stages=stages, ignored_features=ignored,
                            version=spec.pop("version", "codex-cli 0.165.0"), **spec)


def _bundled(codex_home: Path) -> list[list[str]]:
    return [[name, str(codex_home / "skills" / ".system" / name / "SKILL.md")] for name in BUNDLED]


# -- the classification -----------------------------------------------------------------

def test_the_0165_defaults_are_switched_off_and_never_tolerated():
    """Each is reviewed and switched off; none may read on (not permitted, not a retired flag)."""

    assert set(NEW_0165) <= set(lockdown.LOCKDOWN_DISABLED_FEATURES)
    assert not set(NEW_0165) & lockdown.PERMITTED_FEATURES
    assert not set(NEW_0165) & set(lockdown.REVIEWED_RETIRED_FEATURES)
    for shell in (False, True):
        on = {"apps": False, "plugins": False, "multi_agent": False, **{name: True for name in NEW_0165}}
        assert lockdown.feature_violations(on, shell=shell, stages={name: "stable" for name in NEW_0165}) == \
            sorted(NEW_0165)
        # Even a CLI that retires one later does not make it tolerated without a review.
        assert lockdown.feature_violations(on, shell=shell, stages={name: "removed" for name in NEW_0165}) == \
            sorted(NEW_0165)
        assert not lockdown.unclassified_features_on(on, shell=shell)


@pytest.mark.parametrize("shell", [False, True])
def test_every_launch_sends_both_switches_and_the_bundled_skills_switch(tmp_path, shell):
    overrides = isolated_turn_overrides(tmp_path, shell=shell)
    assert {f"features.{name}=false" for name in NEW_0165} <= set(overrides)
    # skills.bundled is a config table, not a feature: its own key, never a features.* one
    # and never a bare boolean (which codex-cli 0.165.0 refuses to load).
    assert "skills.bundled.enabled=false" in overrides
    assert not [o for o in overrides if o.split("=", 1)[0] in {"skills.bundled", "features.skills",
                                                              "features.skills.bundled", "features.bundled_skills"}]
    assert lockdown.skill_disable_overrides(()) == ["skills.bundled.enabled=false"]


# -- the launch check on a fake 0.165.0 -------------------------------------------------

def test_a_0165_cli_runs_the_turn_with_both_new_features_off(tmp_path, monkeypatch):
    program, log = _cli_0165(tmp_path)
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    _turn(_client(tmp_path, program))
    (launched,) = _launched(log)
    assert {f"features.{name}=false" for name in NEW_0165} <= set(launched)
    # Classified: the first listing already reads both off, so no unclassified round.
    (listing,) = _feature_lists(log)
    assert {f"features.{name}=false" for name in NEW_0165} <= set(listing["overrides"])


@pytest.mark.parametrize("feature", NEW_0165)
def test_a_0165_feature_whose_switch_is_ignored_refuses_the_turn(tmp_path, monkeypatch, feature):
    program, log = _cli_0165(tmp_path, ignored_features=[feature])
    captured = install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(lockdown.CodexLockdownUnavailable) as caught:
        _turn(_client(tmp_path, program))
    message = str(caught.value)
    assert f"Codex (codex-cli 0.165.0) does not report feature {feature} (stable) off" in message
    assert "refusing the isolated turn" in message
    assert _launched(log) == [] and "app_config" not in captured


def test_a_0165_cli_with_an_unknown_new_feature_left_on_still_refuses(tmp_path, monkeypatch):
    program, log = _cli_0165(tmp_path, extra=("future_tool",), ignored_features=["future_tool"],
                             version="codex-cli 0.166.0")
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(lockdown.CodexLockdownUnavailable) as caught:
        _turn(_client(tmp_path, program))
    message = str(caught.value)
    assert "Codex (codex-cli 0.166.0) does not report feature future_tool (stable) off" in message
    assert "until future_tool is reviewed" in message
    assert not any(name in message for name in NEW_0165)
    assert _launched(log) == []
    assert "features.future_tool=false" in _feature_lists(log)[-1]["overrides"]


def test_a_0165_cli_with_an_unknown_new_feature_whose_switch_works_switches_it_off(tmp_path, monkeypatch):
    program, log = _cli_0165(tmp_path, extra=("future_tool",))
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    _turn(_client(tmp_path, program))
    (launched,) = _launched(log)
    assert {"features.future_tool=false", *(f"features.{name}=false" for name in NEW_0165)} <= set(launched)


# -- bundled skills: the skills.bundled.enabled switch ----------------------------------

def test_bundled_skills_are_switched_off_by_their_own_key(tmp_path, monkeypatch):
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    program, log = _cli_0165(tmp_path, bundled_skills=_bundled(codex_home))
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    _turn(_client(tmp_path, program))
    (launched,) = _launched(log)
    assert "skills.bundled.enabled=false" in launched
    # The switch alone left the context with no skill: nothing to disable by name.
    assert not [override for override in launched if override.startswith("skills.config=")]


def test_bundled_skills_a_cli_keeps_listing_are_disabled_by_name_and_path(tmp_path, monkeypatch):
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    bundled = _bundled(codex_home)
    program, log = _cli_0165(tmp_path, bundled_skills=bundled, ignored_skill_overrides=["skills.bundled.enabled"])
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    _turn(_client(tmp_path, program))
    (launched,) = _launched(log)
    assert "skills.bundled.enabled=false" in launched
    (rules,) = [override for override in launched if override.startswith("skills.config=")]
    for name, path in bundled:
        assert f'name="{name}"' in rules and f'path="{path}"' in rules


def test_bundled_skills_no_switch_removes_refuse_the_turn(tmp_path, monkeypatch):
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    program, log = _cli_0165(tmp_path, bundled_skills=_bundled(codex_home),
                             ignored_skill_overrides=["skills.bundled.enabled", "skills.config"])
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(lockdown.CodexLockdownUnavailable, match="still lists skills .*imagegen"):
        _turn(_client(tmp_path, program))
    assert _launched(log) == []
