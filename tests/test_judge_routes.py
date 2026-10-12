"""Judgment routes (router spec §6.2): profiles, routing, readiness, receipts.

* Decider routes take only a decider profile, resolve an unset route to the
  code-default ``openrouter_decider``, never fall back to a chat provider and
  ignore ``LEARNLOOP_AI_PROVIDER``.
* LLM routes are ordinary chat routes: unset follows the active provider.
* Profiles come from code defaults for configs that predate them (B6), while
  an explicit vault profile stays authoritative.
* Receipts carry judge labels; judgment_ledger accepts the Decider.
"""
from __future__ import annotations

from contextlib import closing
from types import SimpleNamespace

import pytest

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.execution import call_labels, model_call, observe_model_calls
from learnloop.ai.routing import (
    DECIDER_TASKS, is_generation_profile, provider_for_task, ready_client_for_task,
    route_profile_mismatch, runtime_for_provider,
)
from learnloop.config import load_config
from learnloop.config.schema import DeciderProviderConfig, LearnLoopConfig
from learnloop.db.connection import connect
from learnloop.db.migrate import apply_migrations, discover_migrations
from learnloop.db.repositories import Repository
from learnloop.db.stores.judgments import append_judgment
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import _settings_ready, available_grading_providers
from tests.helpers import create_basic_vault
from tests.test_settings_sidecar import _settings_rpc


@pytest.fixture
def codex_ready(monkeypatch):
    monkeypatch.setattr(
        "learnloop.ai.runtime.check_codex_runtime",
        lambda *args, **kwargs: SimpleNamespace(status="ready", actual_revision=None, message="ok"),
    )
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)


@pytest.fixture
def vault(tmp_path, monkeypatch, codex_ready):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    paths = create_basic_vault(tmp_path / "vault")
    return load_vault(paths.root)


def test_profiles_come_from_code_defaults_for_configs_that_predate_them(tmp_path):
    path = tmp_path / "learnloop.toml"
    # An owner vault from before Phase 1: no embedding or decider profile.
    path.write_text('schema_version = 2\n[ai]\nactive_provider = "codex"\n', encoding="utf-8")
    config = load_config(path, load_environment=False)
    assert config.ai.providers["openrouter_decider"].type == "decider"
    assert config.ai.providers["openrouter_decider"].model == "perplexity/pplx-decider-v1.1-27b"
    assert config.ai.providers["openrouter_decider"].base_url == "https://openrouter.ai/api"
    assert config.ai.providers["openrouter_decider"].api_key_env == "OPENROUTER_API_KEY"
    assert config.ai.providers["openrouter_embedding"].type == "openai_embedding"
    assert config.ai.providers["openrouter_embedding"].base_url == "https://openrouter.ai/api/v1"
    assert provider_for_task(config, "llm_probability_decider").provider_name == "openrouter_decider"
    # Routes that name the code-default profiles resolve without a vault profile.
    config.ai.routing.embedding = "openrouter_embedding"
    assert route_profile_mismatch(config, "openrouter_embedding", "embedding") is None
    assert route_profile_mismatch(config, "openrouter_decider", "router_decider") is None


def test_an_explicit_vault_profile_stays_authoritative(tmp_path):
    path = tmp_path / "learnloop.toml"
    path.write_text(
        'schema_version = 2\n[ai.providers.openrouter_decider]\ntype = "decider"\napi = "perplexity"\n'
        'model = "pplx-decider-v1.1-27b"\n[ai.providers.openrouter_embedding]\ntype = "openai_embedding"\n'
        'base_url = "https://example.invalid/v1"\n', encoding="utf-8",
    )
    config = load_config(path, load_environment=False)
    assert config.ai.providers["openrouter_decider"].api == "perplexity"
    assert config.ai.providers["openrouter_decider"].model == "pplx-decider-v1.1-27b"
    assert config.ai.providers["openrouter_embedding"].base_url == "https://example.invalid/v1"


@pytest.mark.parametrize("task", sorted(DECIDER_TASKS))
def test_decider_routes_are_explicit_ignore_the_env_and_never_fall_back(vault, monkeypatch, task):
    config = vault.config
    monkeypatch.setenv("LEARNLOOP_AI_PROVIDER", "codex")
    config.ai.fallback_provider = "codex"
    selection = provider_for_task(config, task)
    assert (selection.provider_name, selection.explicit, selection.from_env) == ("openrouter_decider", True, False)
    # No key: the decider route is not ready, and it does NOT fall back.
    resolved = ready_client_for_task(vault.root, config, task)
    assert resolved.provider_name == "openrouter_decider" and resolved.fallback_from is None
    assert not resolved.ready and resolved.runtime.status == "provider_auth_required"
    # A chat profile on a decider route is refused, never used.
    setattr(config.ai.routing, task, "codex")
    resolved = ready_client_for_task(vault.root, config, task)
    assert not resolved.ready and "never falls back to a chat provider" in resolved.runtime.message
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    setattr(config.ai.routing, task, None)
    resolved = ready_client_for_task(vault.root, config, task)
    assert resolved.ready and resolved.client.provider_type == "decider"
    assert resolved.client.model == "perplexity/pplx-decider-v1.1-27b"


@pytest.mark.parametrize("task", ["llm_probability_llm", "router_llm"])
def test_llm_routes_are_ordinary_chat_routes(vault, monkeypatch, task):
    config = vault.config
    assert provider_for_task(config, task).provider_name == config.ai.active_provider
    setattr(config.ai.routing, task, "codex_medium")
    assert provider_for_task(config, task).provider_name == "codex_medium"
    monkeypatch.setenv("LEARNLOOP_AI_PROVIDER", "deepseek_pro")
    assert provider_for_task(config, task).provider_name == "deepseek_pro"
    assert provider_for_task(config, task, allow_env=False).provider_name == "codex_medium"
    # A decision-model profile cannot serve a chat route.
    assert "decision-model profile" in route_profile_mismatch(config, "openrouter_decider", task)


@pytest.mark.parametrize("task", [None, "grading", "tutor_qa", "embedding"])
def test_decider_profiles_never_serve_other_work(vault, monkeypatch, task):
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    assert not runtime_for_provider(vault.root, vault.config, "openrouter_decider", task=task).ready
    assert not is_generation_profile(vault.config, "openrouter_decider")
    assert not is_generation_profile(vault.config, "openrouter_embedding")
    assert is_generation_profile(vault.config, "codex")


def test_decider_readiness_is_key_presence_without_network(vault, monkeypatch):
    import socket

    monkeypatch.setattr(socket, "socket", lambda *a, **k: pytest.fail("readiness must not touch the network"))
    report = runtime_for_provider(vault.root, vault.config, "openrouter_decider", task="router_decider")
    assert report.status == "provider_auth_required" and "OPENROUTER_API_KEY" in report.message
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    report = runtime_for_provider(vault.root, vault.config, "openrouter_decider", task="router_decider")
    assert report.ready and report.model == "perplexity/pplx-decider-v1.1-27b"
    vault.config.ai.providers["direct"] = DeciderProviderConfig(api="perplexity")
    vault.config.ai.routing.router_decider = "direct"
    report = runtime_for_provider(vault.root, vault.config, "direct", task="router_decider")
    assert report.status == "provider_auth_required" and "PERPLEXITY_API_KEY" in report.message


def test_grading_providers_and_settings_health_ignore_judgment_routes(vault, monkeypatch):
    assert "openrouter_decider" not in available_grading_providers(vault)
    assert "openrouter_embedding" not in available_grading_providers(vault)
    # A fresh Codex vault without an OpenRouter key is healthy: the router
    # routes have no consumer and the llm_probability harness is off.
    vault.config.ai.routing.router_decider = "openrouter_decider"
    vault.config.ai.routing.llm_probability_decider = "openrouter_decider"
    assert _settings_ready(vault)
    vault.config.field.enabled = True
    vault.config.field.llm_probability_enabled = True
    assert not _settings_ready(vault)
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    assert _settings_ready(vault)


def test_settings_payload_discloses_each_judgment_route(tmp_path, monkeypatch, codex_ready):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    paths = create_basic_vault(tmp_path / "vault")
    response = _settings_rpc(paths.root, ("get_settings", {}))[0]
    judges = {entry["route"]: entry for entry in response["result"]["judges"]}
    assert set(judges) == {"llm_probability_decider", "llm_probability_llm", "router_decider", "router_llm"}
    decider = judges["llm_probability_decider"]
    assert decider["provider"] == "openrouter_decider" and decider["providerType"] == "decider"
    assert decider["ready"] is False
    assert "Perplexity" in decider["disclosure"] and "OpenRouter" in decider["disclosure"]
    assert "Nothing is sent yet" in judges["router_llm"]["disclosure"]
    assert "ChatGPT subscription" in judges["router_llm"]["disclosure"]
    names = {provider["name"]: provider["type"] for provider in response["result"]["ai"]["providers"]}
    assert names["openrouter_decider"] == "decider"


def test_settings_refuse_a_decider_profile_for_a_generation_use_case(tmp_path, monkeypatch, codex_ready):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    paths = create_basic_vault(tmp_path / "vault")
    responses = _settings_rpc(
        paths.root,
        ("update_ai_settings", {"activeProvider": "openrouter_decider"}),
        ("update_ai_settings", {"useCases": {"grading": {"provider": "openrouter_decider"}}}),
    )
    for response in responses:
        assert "decision-model" in response["error"]["message"]


def test_call_labels_reach_the_start_event_and_refuse_unknown_labels():
    events = []
    client = SimpleNamespace(model="m", provider_name="p")
    with observe_model_calls(lambda action, event: events.append(event)):
        with call_labels(judge="llm", question_set_version="v1"), call_labels(state_hash="h"):
            with model_call(client, purpose="llm_probability"):
                pass
        with model_call(client, purpose="other"):
            pass
    assert (events[0]["judge"], events[0]["question_set_version"], events[0]["state_hash"]) == ("llm", "v1", "h")
    assert "judge" not in events[2]
    with pytest.raises(ValueError, match="Unknown receipt labels"):
        with call_labels(temperature="0"):
            pass
    with pytest.raises(ValueError, match="judge must be"):
        with call_labels(judge="owner"):
            pass


def test_receipts_store_labels_and_unlabelled_calls_work_below_169(tmp_path):
    repository = Repository(tmp_path / "head.sqlite")
    client = SimpleNamespace(model="m", provider_name="p")
    with observe_model_calls(lambda action, event: repository.record_model_event(
            action, event, owner_kind="test", owner_id="1")):
        with call_labels(judge="decider", question_set_version="qs", state_hash="abc"):
            with model_call(client, purpose="llm_probability"):
                pass
    with closing(connect(tmp_path / "head.sqlite", read_only=True)) as connection:
        row = connection.execute(
            "SELECT judge, question_set_version, state_hash, status FROM model_call_receipts").fetchone()
    assert tuple(row) == ("decider", "qs", "abc", "completed")
    # A database before migration 169 still records unlabelled calls.
    old = tmp_path / "old"
    old.mkdir()
    import shutil

    for migration in discover_migrations():
        if migration.version < 169:
            shutil.copy2(migration.path, old / migration.path.name)
    apply_migrations(tmp_path / "old.sqlite", migrations_dir=old)
    old_repository = Repository.attach(tmp_path / "old.sqlite")
    with observe_model_calls(lambda action, event: old_repository.record_model_event(
            action, event, owner_kind="test", owner_id="1")):
        with model_call(client, purpose="other"):
            pass


def test_judgment_ledger_accepts_the_decider_with_provenance(tmp_path):
    path = tmp_path / "state.sqlite"
    apply_migrations(path)
    with closing(connect(path)) as connection:
        append_judgment(connection, task="llm_probability", left_kind="probability_request", left_id="d",
                        judge="decider", judge_model="perplexity/pplx-decider-v1.1-27b-20261006",
                        prompt_version="llm_probability_qs_v1", input_hash="h", verdict="{}", score=0.4)
        with pytest.raises(ValueError, match="decider"):
            append_judgment(connection, task="t", left_kind="k", left_id="l", judge="decider",
                            input_hash="h", verdict="v")
        import sqlite3

        with pytest.raises(sqlite3.IntegrityError, match="nonempty judge_model and prompt_version"):
            connection.execute(
                "INSERT INTO judgment_ledger (id,created_at,task,left_kind,left_id,judge,input_hash,verdict,rationale) "
                "VALUES ('x','2026','t','k','l','decider','h','v','')"
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO judgment_ledger (id,created_at,task,left_kind,left_id,judge,input_hash,verdict,rationale) "
                "VALUES ('y','2026','t','k','l','oracle','h','v','')"
            )
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE judgment_ledger SET verdict='changed'")


def test_migration_169_preserves_every_judgment_and_its_references(tmp_path):
    """Rebuilding the append-only ledger keeps rows, ids, triggers and the FK graph."""

    import shutil
    import sqlite3

    before = tmp_path / "before"
    before.mkdir()
    for migration in discover_migrations():
        if migration.version < 169:
            shutil.copy2(migration.path, before / migration.path.name)
    path = tmp_path / "state.sqlite"
    apply_migrations(path, migrations_dir=before)
    with closing(connect(path)) as connection:
        first = append_judgment(connection, task="same_target", left_kind="item", left_id="a",
                                right_kind="item", right_id="b", judge="llm", judge_model="m",
                                prompt_version="v", input_hash="h", verdict="same")
        append_judgment(connection, task="same_target", left_kind="item", left_id="a",
                        right_kind="item", right_id="b", judge="owner", input_hash="h2",
                        verdict="different", supersedes_id=first)
        connection.commit()
        rows_before = connection.execute("SELECT * FROM judgment_ledger ORDER BY id").fetchall()
    assert [m.version for m in apply_migrations(path)] == [169]
    with closing(connect(path)) as connection:
        assert [tuple(r) for r in connection.execute("SELECT * FROM judgment_ledger ORDER BY id")] == [
            tuple(r) for r in rows_before]
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        triggers = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='judgment_ledger'")}
        assert triggers == {"judgment_ledger_no_update", "judgment_ledger_no_delete",
                            "judgment_ledger_validate_insert"}
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM judgment_ledger")
        references = connection.execute(
            "SELECT \"table\" FROM pragma_foreign_key_list('activity_family_membership_events')").fetchall()
        assert ("judgment_ledger",) in {tuple(r) for r in references}
        columns = {row[1] for row in connection.execute("PRAGMA table_info(model_call_receipts)")}
        assert {"judge", "question_set_version", "state_hash"} <= columns
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO model_call_receipts (id, owner_kind, owner_id, purpose, status, started_at, judge) "
                "VALUES ('c', 'o', 'i', 'p', 'started', '2026', 'oracle')"
            )


def test_codex_judge_runs_on_the_subscription_route_by_default(monkeypatch, tmp_path):
    from learnloop.ai.client import make_ai_provider_client

    config = LearnLoopConfig()
    assert provider_for_task(config, "llm_probability_llm").provider_name == "codex"
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(AIProviderUnavailable, match="OPENROUTER_API_KEY"):
        # The decider client requires its key; nothing is built silently.
        make_ai_provider_client(config, tmp_path, provider_name="openrouter_decider")
