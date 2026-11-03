"""Codex CLI 0.166.0: eight new features switched off; plugin discovery reaches nothing.

Stage codex-cli-0166-lockdown (2026-11-02, docs/reviews/codex-cli-0166-lockdown.md).
codex-cli 0.166.0 adds ``plugin_discovery_prefetch``, on by default: the switch
for the plugin directory, featured-plugin and recommendation fetches the app
server already made at startup in 0.165.0. It adds seven more keys, off by
default. All eight honour ``-c features.<key>=false``, so all are now switched
off on every launch, and the launch check refuses if any reads on. The lock that
stops plugin startup traffic is ``features.plugins`` (required off): the prefetch
switch alone leaves the other startup tasks running, so both are pinned here.
Everything here runs on a fake ``codex`` (tests/codex_cli_fakes.py); the installed
CLI is exercised by the launch-check tests in test_codex_isolation_mcp_check.py,
test_codex_lockdown_round2.py, test_codex_lockdown_round3.py and
test_diagnosis_isolation.py.
"""

from __future__ import annotations

import json
import subprocess
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
PREFETCH = "plugin_discovery_prefetch"
NEW_0166 = (
    "critical_path_timing",
    "guardian_native_multi_agent_history",
    "mcp_connection_sharing",
    "omit_skill_descriptions",
    PREFETCH,
    "simplified_selection_hints",
    "skill_catalog_deltas",
    "untrusted_as_tool_output",
)
#: Under development in 0.165.0, stage ``removed`` in 0.166.0 with no reader left.
NOW_REMOVED = "code_mode_tool_description_first"
EARLIER = ("prediction_preserve_parent_tools", "reasoning_effort_override")
RETIRED = ("realtime_conversation", "worktrees")


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


def _cli_0166(tmp_path: Path, *, extra: tuple[str, ...] = (), **spec):
    """A fake CLI that lists the eight new features on (the real one defaults only the prefetch on; a layer
    could turn the others on) with working switches, 0.165.0's two, and the retired flags on at ``removed``."""

    features = [*FEATURES, *NEW_0166, *EARLIER, *RETIRED, *extra]
    stages = {name: "removed" for name in RETIRED} | dict(spec.pop("feature_stages", {}))
    ignored = [*RETIRED, *spec.pop("ignored_features", ())]
    return write_fake_codex(tmp_path / "bin", features=features, feature_stages=stages, ignored_features=ignored,
                            version=spec.pop("version", "codex-cli 0.166.0"), **spec)


# -- the classification -----------------------------------------------------------------

def test_the_0166_features_are_switched_off_and_never_tolerated():
    """Each is reviewed and switched off; none may read on (not permitted, not a retired flag)."""

    assert set(NEW_0166) <= set(lockdown.LOCKDOWN_DISABLED_FEATURES)
    assert not set(NEW_0166) & lockdown.PERMITTED_FEATURES
    assert not set(NEW_0166) & set(lockdown.REVIEWED_RETIRED_FEATURES)
    for shell in (False, True):
        on = {"apps": False, "plugins": False, "multi_agent": False, **{name: True for name in NEW_0166}}
        assert lockdown.feature_violations(on, shell=shell, stages={name: "stable" for name in NEW_0166}) == \
            sorted(NEW_0166)
        # Even a CLI that retires one later does not make it tolerated without a review.
        assert lockdown.feature_violations(on, shell=shell, stages={name: "removed" for name in NEW_0166}) == \
            sorted(NEW_0166)
        assert not lockdown.unclassified_features_on(on, shell=shell)


def test_the_real_lock_on_plugin_startup_stays_required():
    """``features.plugins`` gates every plugin startup task: it must be listed and read off, whatever the CLI."""

    assert "plugins" in lockdown.REQUIRED_OFF_FEATURES
    assert {"plugins", "remote_plugin", PREFETCH} <= set(lockdown.LOCKDOWN_DISABLED_FEATURES)
    assert lockdown.feature_violations({"apps": False, "multi_agent": False, PREFETCH: False}, shell=False) == \
        ["plugins"]


@pytest.mark.parametrize("shell", [False, True])
def test_every_launch_sends_all_eight_switches(tmp_path, shell):
    overrides = isolated_turn_overrides(tmp_path, shell=shell)
    assert {f"features.{name}=false" for name in NEW_0166} <= set(overrides)
    assert "features.plugins=false" in overrides


# -- the launch check on a fake 0.166.0 -------------------------------------------------

def test_a_0166_cli_runs_the_turn_with_every_new_feature_off(tmp_path, monkeypatch):
    program, log = _cli_0166(tmp_path)
    captured = install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    _turn(_client(tmp_path, program))
    (launched,) = _launched(log)
    assert {f"features.{name}=false" for name in NEW_0166} <= set(launched)
    # Classified: the first listing already reads all eight off, so no unclassified round.
    (listing,) = _feature_lists(log)
    assert {f"features.{name}=false" for name in NEW_0166} <= set(listing["overrides"])
    loaded = json.loads(captured["spawned"]["stdout"])
    assert not set(NEW_0166) & set(loaded["features_on"])


def test_the_app_server_of_an_isolated_turn_starts_no_plugin_task(tmp_path, monkeypatch):
    """No directory fetch, no marketplace update, no curated sync, no bundle download."""

    program, _log = _cli_0166(tmp_path, plugin_servers={"sampleplug": True})
    captured = install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    _turn(_client(tmp_path, program))
    loaded = json.loads(captured["spawned"]["stdout"])
    assert loaded["plugin_startup_tasks"] == []
    assert loaded["servers_on"] == []


def test_the_prefetch_switch_alone_would_not_stop_plugin_startup_traffic(tmp_path):
    """Why ``features.plugins`` is the check that matters (0.166.0's own test keeps the bundle sync running
    under ``features.plugin_discovery_prefetch=false``): the fake's model of it, on no lockdown overrides."""

    program, _log = _cli_0166(tmp_path)
    def tasks(*flags: str) -> list[str]:
        completed = subprocess.run([str(program), *flags, "app-server"], capture_output=True, text=True, timeout=60)
        return json.loads(completed.stdout)["plugin_startup_tasks"]

    only_prefetch_off = tasks("-c", f"features.{PREFETCH}=false")
    assert "installed_bundle_sync" in only_prefetch_off and "featured_plugin_ids" not in only_prefetch_off
    assert "featured_plugin_ids" in tasks()
    assert tasks("-c", "features.plugins=false") == []


@pytest.mark.parametrize("feature", NEW_0166)
def test_a_0166_feature_whose_switch_is_ignored_refuses_the_turn(tmp_path, monkeypatch, feature):
    program, log = _cli_0166(tmp_path, ignored_features=[feature])
    captured = install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(lockdown.CodexLockdownUnavailable) as caught:
        _turn(_client(tmp_path, program))
    message = str(caught.value)
    assert f"Codex (codex-cli 0.166.0) does not report feature {feature} (stable) off" in message
    assert "refusing the isolated turn" in message
    assert _launched(log) == [] and "app_config" not in captured


def test_a_cli_that_keeps_plugins_on_refuses_the_turn_whatever_the_prefetch_says(tmp_path, monkeypatch):
    program, log = _cli_0166(tmp_path, ignored_features=["plugins"])
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(lockdown.CodexLockdownUnavailable, match=r"does not report feature plugins \(stable\) off"):
        _turn(_client(tmp_path, program))
    assert _launched(log) == []


def test_the_prefetch_retired_later_with_its_switch_ignored_still_refuses(tmp_path, monkeypatch):
    """Stage ``removed`` is no review: a later CLI that stops reading the switch is reviewed first."""

    program, log = _cli_0166(tmp_path, ignored_features=[PREFETCH], feature_stages={PREFETCH: "removed"},
                             version="codex-cli 0.167.0")
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(lockdown.CodexLockdownUnavailable) as caught:
        _turn(_client(tmp_path, program))
    message = str(caught.value)
    assert f"does not report feature {PREFETCH} (removed) off" in message
    assert "no longer reads the switch" in message
    assert _launched(log) == []


def test_a_0165_cli_without_the_new_rows_still_runs(tmp_path, monkeypatch):
    """Codex ignores an unknown ``features.*`` key, so the switches cost an older CLI nothing."""

    features = [*FEATURES, *EARLIER, *RETIRED]
    program, log = write_fake_codex(tmp_path / "bin", features=features, ignored_features=list(RETIRED),
                                    feature_stages={name: "removed" for name in RETIRED}, version="codex-cli 0.165.0")
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    _turn(_client(tmp_path, program))
    (launched,) = _launched(log)
    assert f"features.{PREFETCH}=false" in launched


# -- the flag 0.166.0 retired, and what comes next --------------------------------------

def test_the_flag_0166_retired_is_not_classified_and_a_layer_cannot_leave_it_on(tmp_path, monkeypatch):
    """No code reads ``code_mode_tool_description_first`` any more, and it defaults off, so it needs no
    entry. If a config layer turns it on, it is treated like any unknown feature: switched off, read back."""

    assert NOW_REMOVED not in lockdown.LOCKDOWN_DISABLED_FEATURES
    assert NOW_REMOVED not in lockdown.PERMITTED_FEATURES
    assert NOW_REMOVED not in lockdown.REVIEWED_RETIRED_FEATURES
    program, log = _cli_0166(tmp_path, extra=(NOW_REMOVED,), feature_stages={NOW_REMOVED: "removed"})
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    _turn(_client(tmp_path, program))
    (launched,) = _launched(log)
    assert f"features.{NOW_REMOVED}=false" in launched


def test_the_flag_0166_retired_left_on_with_its_switch_ignored_refuses(tmp_path, monkeypatch):
    program, log = _cli_0166(tmp_path, extra=(NOW_REMOVED,), feature_stages={NOW_REMOVED: "removed"},
                             ignored_features=[NOW_REMOVED])
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(lockdown.CodexLockdownUnavailable, match=f"{NOW_REMOVED} \\(removed\\) off"):
        _turn(_client(tmp_path, program))
    assert _launched(log) == []


def test_a_0166_cli_with_an_unknown_new_feature_left_on_still_refuses(tmp_path, monkeypatch):
    program, log = _cli_0166(tmp_path, extra=("future_tool",), ignored_features=["future_tool"],
                             version="codex-cli 0.167.0")
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(lockdown.CodexLockdownUnavailable) as caught:
        _turn(_client(tmp_path, program))
    message = str(caught.value)
    assert "Codex (codex-cli 0.167.0) does not report feature future_tool (stable) off" in message
    assert "until future_tool is reviewed" in message
    assert not any(name in message for name in NEW_0166)
    assert _launched(log) == []
    assert "features.future_tool=false" in _feature_lists(log)[-1]["overrides"]


def test_a_0166_cli_with_an_unknown_new_feature_whose_switch_works_switches_it_off(tmp_path, monkeypatch):
    program, log = _cli_0166(tmp_path, extra=("future_tool",))
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    _turn(_client(tmp_path, program))
    (launched,) = _launched(log)
    assert {"features.future_tool=false", *(f"features.{name}=false" for name in NEW_0166)} <= set(launched)
