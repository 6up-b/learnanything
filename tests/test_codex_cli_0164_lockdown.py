"""Codex CLI 0.164.0: two retired feature flags, and a refusal that says what to review.

Stage codex-cli-0164-lockdown (2026-10-27, docs/reviews/codex-cli-0164-lockdown.md).
codex-cli 0.164.0 lists ``realtime_conversation`` and ``worktrees`` at stage
``removed`` and on, and ignores ``-c features.<key>=false`` for both
(``features/src/lib.rs`` ``Features::apply_map`` skips the keys), so the launch
check refused every isolated turn. Both were reviewed: neither gives
LearnLoop's turn anything (voice needs a client request LearnLoop never sends,
the worktree tools are dynamic tools only the TUI registers). They may read on
only at stage ``removed``; anything else that stays on refuses, as before, and
the refusal now names the CLI version, each feature's stage and where it is
classified. Everything here runs on a fake ``codex`` (tests/codex_cli_fakes.py);
the installed CLI is exercised by the launch-check tests in
test_codex_isolation_mcp_check.py, test_codex_lockdown_round2.py,
test_codex_lockdown_round3.py and test_diagnosis_isolation.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.ai.providers import codex_lockdown as lockdown
from learnloop.ai.providers.codex import SdkCodexClient
from learnloop.ai.transport import StructuredRequest
from learnloop.config import CodexConfig
from learnloop.diagnosis.offline_review.judge import LinkJudgment
from tests.codex_cli_fakes import FEATURES, fake_codex_calls, write_fake_codex
from tests.project_support import install_fake_codex_sdk

ANSWER = '{"links": []}'
RETIRED = ("realtime_conversation", "worktrees")
CORE_OFF = {"apps": False, "plugins": False, "multi_agent": False}


def _client(tmp_path: Path, program: Path) -> SdkCodexClient:
    vault_root = tmp_path / "vault"
    vault_root.mkdir(exist_ok=True)
    return SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"), sdk_codex_bin=str(program),
                                      model="gpt-5.6-sol"), vault_root)


def _turn(client: SdkCodexClient):
    return client.complete(StructuredRequest(purpose="tutor_qa", prompt="p", result_model=LinkJudgment))


def _launched(log: Path) -> list[list[str]]:
    return [call["overrides"] for call in fake_codex_calls(log) if call["command"][:1] == ["app-server"]]


def _cli_0164(tmp_path: Path, *, stage: str = "removed", extra: tuple[str, ...] = (), **spec):
    """A fake CLI that, like 0.164.0, lists ``RETIRED`` on at ``stage`` and ignores their switch."""

    features = [*FEATURES, *RETIRED, *extra]
    stages = {name: stage for name in RETIRED} | dict(spec.pop("feature_stages", {}))
    ignored = [*RETIRED, *spec.pop("ignored_features", ())]
    return write_fake_codex(tmp_path / "bin", features=features, feature_stages=stages, ignored_features=ignored,
                            version=spec.pop("version", "codex-cli 0.164.0"), **spec)


# -- the reviewed list ------------------------------------------------------------------

def test_the_reviewed_retired_features_are_exactly_the_two_0164_flags():
    """Adding a name here is a security review of what that flag now does, not a refactor."""

    assert set(lockdown.REVIEWED_RETIRED_FEATURES) == set(RETIRED)
    assert all(lockdown.REVIEWED_RETIRED_FEATURES[name].strip() for name in RETIRED)
    # Still switched off on every launch (the switch works on 0.163.0), never permitted outright.
    assert set(RETIRED) <= set(lockdown.LOCKDOWN_DISABLED_FEATURES)
    assert not set(RETIRED) & set(lockdown.PERMITTED_FEATURES)
    assert not set(RETIRED) & set(lockdown.REQUIRED_OFF_FEATURES)


@pytest.mark.parametrize("shell", [False, True])
def test_a_retired_flag_may_read_on_only_at_stage_removed(shell):
    on = {**CORE_OFF, **{name: True for name in RETIRED}}
    assert lockdown.feature_violations(on, shell=shell, stages={name: "removed" for name in RETIRED}) == []
    # Without stages, or at any other stage, both must read off as before.
    assert lockdown.feature_violations(on, shell=shell) == list(RETIRED)
    for stage in ("stable", "under development", "experimental", "deprecated", ""):
        assert lockdown.feature_violations(on, shell=shell, stages={name: stage for name in RETIRED}) == list(RETIRED)


def test_an_unreviewed_feature_at_stage_removed_still_refuses():
    on = {**CORE_OFF, "future_tool": True, "worktrees": True}
    stages = {"future_tool": "removed", "worktrees": "removed"}
    assert lockdown.feature_violations(on, shell=False, stages=stages) == ["future_tool"]


def test_a_core_feature_reported_removed_and_on_still_refuses():
    on = {"apps": True, "plugins": False, "multi_agent": False}
    assert lockdown.feature_violations(on, shell=False, stages={"apps": "removed"}) == ["apps"]


def test_the_refusal_names_the_version_the_stages_and_where_to_classify():
    message = lockdown.feature_refusal(["future_tool", "browser_use"], {"future_tool": "removed",
                                                                       "browser_use": "stable"},
                                       "codex-cli 0.165.0")
    assert "Codex (codex-cli 0.165.0) does not report feature future_tool (removed), browser_use (stable) off" in message
    assert "refusing the isolated turn" in message
    assert "no longer reads the switch of a removed feature (future_tool)" in message
    assert "until future_tool, browser_use are reviewed" in message
    assert "codex_lockdown.py" in message and "REVIEWED_RETIRED_FEATURES" in message
    plain = lockdown.feature_refusal(["apps"], {}, None)
    assert plain.startswith("Codex (version unknown) does not report feature apps off")
    assert "no longer reads" not in plain and "reviewed" not in plain


@pytest.mark.parametrize("stdout, expected", [
    ("codex-cli 0.164.0\n", "codex-cli 0.164.0"),
    ("codex-cli 0.165.0-alpha.1\nextra\n", "codex-cli 0.165.0-alpha.1"),
    ("", None),
    ("Error: secret = \"LEAKED-CONFIG-LINE\"", None),
    ("x" * 200 + " 1", None),
])
def test_only_a_version_shaped_line_reaches_the_message(stdout, expected):
    assert lockdown.cli_version_text(stdout) == expected


# -- the launch check on a fake 0.164.0 -------------------------------------------------

def test_a_0164_cli_with_the_reviewed_retired_flags_on_runs_the_turn(tmp_path, monkeypatch):
    program, log = _cli_0164(tmp_path)
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    _turn(_client(tmp_path, program))
    (launched,) = _launched(log)
    # The switches are still sent: a CLI that reads them turns both off.
    assert {f"features.{name}=false" for name in RETIRED} <= set(launched)
    assert not [call for call in fake_codex_calls(log) if call["command"] == ["--version"]]


def test_a_reviewed_flag_left_on_at_another_stage_refuses_the_turn(tmp_path, monkeypatch):
    program, log = _cli_0164(tmp_path, stage="stable")
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(lockdown.CodexLockdownUnavailable,
                       match=r"codex-cli 0\.164\.0.*realtime_conversation \(stable\), worktrees \(stable\) off"):
        _turn(_client(tmp_path, program))
    assert _launched(log) == []


def test_a_newer_cli_s_retired_unreviewed_feature_refuses_and_names_what_to_review(tmp_path, monkeypatch):
    program, log = _cli_0164(tmp_path, extra=("future_tool",), feature_stages={"future_tool": "removed"},
                             ignored_features=["future_tool"], version="codex-cli 0.165.0")
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(lockdown.CodexLockdownUnavailable) as caught:
        _turn(_client(tmp_path, program))
    message = str(caught.value)
    assert "Codex (codex-cli 0.165.0) does not report feature future_tool (removed) off" in message
    assert "no longer reads the switch of a removed feature (future_tool)" in message
    assert "until future_tool is reviewed" in message
    assert "realtime_conversation" not in message and "worktrees" not in message
    assert _launched(log) == []
    # The unclassified feature was switched off first, then read back on.
    features_lists = [call for call in fake_codex_calls(log) if call["command"] == ["features", "list"]]
    assert "features.future_tool=false" in features_lists[-1]["overrides"]


def test_a_version_probe_that_fails_still_refuses_with_the_features_named(tmp_path, monkeypatch):
    program, log = _cli_0164(tmp_path, extra=("future_tool",), ignored_features=["future_tool"],
                             behaviour={"--version": "fail"})
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(lockdown.CodexLockdownUnavailable) as caught:
        _turn(_client(tmp_path, program))
    message = str(caught.value)
    assert message.startswith("Codex (version unknown) does not report feature future_tool (stable) off")
    assert "LEAKED-CONFIG-LINE" not in message
    assert _launched(log) == []
