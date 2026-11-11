"""Refactor C4: the Codex transport is gone; old configs and stored rows stay readable.

* An old ``learnloop.toml`` that names Codex (the active provider, a fallback,
  pinned routes, a legacy ``codex_http`` profile, the retired opt-in, a retired
  route's effort) still loads, and every entry that could serve it answers with
  the clear refusal: readiness, routing, the client factory and `doctor`. No
  process starts.
* An old top-level ``[codex]`` table still loads to the same profile it did
  when a runtime view read it (the expected values were taken at the base
  commit, ``88607cb3fe``).
* Replay reads a stored attempt's ``grading_source``, never the provider: an
  attempt graded as ``codex`` replays to the same learner state, and replay
  builds no model client.
"""

from __future__ import annotations

from contextlib import closing
import subprocess
from typing import Any

import pytest
import tomlkit

from learnloop.ai.agent_harness import AgentHarnessRefused, refusal_message
from learnloop.ai.client import make_ai_provider_client
from learnloop.ai.routing import ready_client_for_task, runtime_for_provider
from learnloop.attempts.ai_contracts import CriterionEvidence, GradingProposal
from learnloop.attempts.attempts import AttemptDraft, complete_codex_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.config import LearnLoopConfig
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.ops.doctor import run_doctor
from learnloop.substrate.shadow_rebuild import shadow_rebuild
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault

CODEX_NAMES = ("codex", "codex_low", "codex_medium", "codex_luna", "legacy_http")


@pytest.fixture
def no_process(monkeypatch):
    def refuse(*_args: Any, **_kwargs: Any):
        raise AssertionError("a process was started")

    monkeypatch.setattr(subprocess, "Popen", refuse)
    monkeypatch.setattr(subprocess, "run", refuse)


def _old_codex_vault(tmp_path):
    root = tmp_path / "vault"
    create_basic_vault(root)
    path = root / "learnloop.toml"
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    ai = document["ai"]
    ai["active_provider"] = "codex"
    ai["fallback_provider"] = "codex"
    ai["agent_harness_opt_in"] = True  # the retired opt-in
    providers = ai.setdefault("providers", tomlkit.table())
    providers["codex"] = {"type": "codex_sdk", "checkout_path": "/opt/codex", "revision": "abc123",
                          "sdk_codex_bin": "/usr/bin/codex"}
    providers["legacy_http"] = {"type": "codex_http", "base_url": "http://127.0.0.1:8765", "model": "m"}
    routing = ai.setdefault("routing", tomlkit.table())
    routing["grading"] = "codex_low"
    routing["tutor_qa"] = "codex"  # the legacy spelling of a task's Codex tier
    routing["authoring"] = "legacy_http"
    ai["route_reasoning_effort"] = {"proof_check": "high"}  # a retired route's effort
    path.write_text(tomlkit.dumps(document), encoding="utf-8")
    return root


def test_an_old_config_naming_codex_loads_and_every_entry_refuses_it_clearly(tmp_path, no_process):
    root = _old_codex_vault(tmp_path)
    vault = load_vault(root)
    config = vault.config
    assert config.ai.active_provider == "codex"
    assert config.ai.routing.tutor_qa == "codex_low"
    assert config.ai.providers["legacy_http"].type == "http"
    assert not hasattr(config.ai, "agent_harness_opt_in")

    for name in CODEX_NAMES:
        # The message an old config meets (the opt-in clause it used to end with named a removed setting).
        expected = refusal_message(name)
        assert expected == (
            f"AI provider {name!r} is the Codex agent harness, which LearnLoop no longer uses for serving "
            "(plan-first transport, owner decision 2026-10-21). Use the ChatGPT plan "
            "(`learnloop ai signin chatgpt`; `learnloop doctor --fix` moves pinned Codex routes to it)."
        )
        report = runtime_for_provider(root, config, name)
        assert (report.status, report.ready, report.message) == ("provider_unavailable", False, expected)
        with pytest.raises(AgentHarnessRefused) as refused:
            make_ai_provider_client(config, root, provider_name=name)
        assert str(refused.value) == expected

    for task, name in (("grading", "codex_low"), ("tutor_qa", "codex_low"), ("authoring", "legacy_http")):
        resolved = ready_client_for_task(root, config, task)
        assert resolved.client is None and not resolved.ready, task
        assert resolved.provider_name == name and resolved.fallback_from is None, task
        assert "is the Codex agent harness" in resolved.runtime.message, task

    pinned = {issue.details["setting"] for issue in run_doctor(root).issues if issue.code == "ai:codex_route_pinned"}
    assert {"ai.active_provider", "ai.fallback_provider", "ai.routing.grading", "ai.routing.tutor_qa",
            "ai.routing.authoring"} <= pinned


_LEGACY_TABLE_DEFAULTS = {
    "authoring_path": "/authoring-proposal", "base_url": "http://127.0.0.1:8765",
    "canonical_ingest_path": "/canonical-ingest", "checkout_path": "", "grading_path": "/grading-proposal",
    "healthcheck_path": "/health", "healthcheck_timeout_seconds": 5, "input_modalities": [],
    "misconception_match_path": "/misconception-match", "model": "gpt-5.6-sol", "reasoning_effort": "low",
    "reasoning_summary": "none", "revision": "<pinned-commit>", "sdk_codex_bin": "", "sdk_launch_command": "",
    "sdk_python_path": "sdk/python/src", "startup_command": "", "startup_timeout_seconds": 20,
    "teach_back_authoring_path": "/teach-back-authoring", "teach_back_path": "/teach-back", "timeout_seconds": 180,
    "tutor_qa_path": "/tutor-qa", "type": "codex_sdk",
}


@pytest.mark.parametrize(("table", "changed"), [
    ({}, {}),
    ({"provider": "http", "base_url": "http://x:1", "checkout_path": "/c", "revision": "r1", "timeout_seconds": 30},
     {"type": "http", "base_url": "http://x:1", "checkout_path": "/c", "revision": "r1", "timeout_seconds": 30}),
    # The legacy model alias still moves to the current model and effort; an unknown key is dropped.
    ({"provider": "sdk", "model": "gpt-5.5", "reasoning_effort": "high", "startup_timeout_seconds": "7",
      "extra_key": 1}, {"startup_timeout_seconds": 7}),
    ({"provider": "http_adapter", "sdk_codex_bin": "/b", "teach_back_path": "/tb"},
     {"type": "http", "sdk_codex_bin": "/b", "teach_back_path": "/tb"}),
])
def test_a_legacy_codex_table_loads_to_the_profile_it_did_at_the_base(table, changed):
    config = LearnLoopConfig.model_validate({"codex": table})
    assert config.ai.providers["codex"].model_dump(mode="json") == _LEGACY_TABLE_DEFAULTS | changed
    for tier, effort in (("codex_low", "low"), ("codex_medium", "medium"), ("codex_luna", "low")):
        profile = config.ai.providers[tier]
        assert (profile.type, profile.reasoning_effort) == ((_LEGACY_TABLE_DEFAULTS | changed)["type"], effort)


def _stored_grading_source(database, attempt_id: str) -> str:
    with closing(connect(database, read_only=True)) as connection:
        row = connection.execute(
            "SELECT grading_source FROM attempt_feedback_metadata WHERE attempt_id = ?", (attempt_id,)
        ).fetchone()
    return row[0]


def test_an_attempt_graded_by_codex_replays_identically(tmp_path, monkeypatch):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    repository.insert_agent_run(
        {"id": "agent_run_codex", "purpose": "grading", "started_at": NOW.isoformat(), "status": "completed",
         "provider": "codex_low", "provider_type": "codex_sdk", "model": "gpt-5.6-sol"}
    )
    complete_codex_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="SVD is U Sigma V^T.",
                     attempt_type="independent_attempt"),
        GradingProposal(
            attempt_id="attempt_codex_replay",
            practice_item_id="pi_svd_define_001",
            rubric_score=3,
            criterion_evidence=[CriterionEvidence(criterion_id="correctness", points_awarded=3,
                                                  evidence="Correct but incomplete.")],
            grader_confidence=0.9,
        ),
        agent_run_id="agent_run_codex",
        clock=clock,
    )
    assert _stored_grading_source(paths.sqlite_path, "attempt_codex_replay") == "codex"

    def no_client(*_args: Any, **_kwargs: Any):
        raise AssertionError("replay built a model client")

    monkeypatch.setattr("learnloop.ai.client.make_ai_provider_client_from_profile", no_client)
    result = shadow_rebuild(load_vault(paths.root))

    assert result.live_database_unchanged
    assert result.learner_state_diff["summary"] == {"mastery": 0, "facet": 0, "schedule": 0}
    assert result.learner_state_diff["mastery"]["summary"]["unchanged"] > 0
    assert result.schedule_before == result.schedule_after
    assert _stored_grading_source(paths.sqlite_path, "attempt_codex_replay") == "codex"
