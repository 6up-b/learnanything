"""Embedding-only profiles and generation routes never serve each other.

Regression tests for the Phase 1 audit (M1-M3): an opt-in, disabled embedding
route must not change what generation routing, health or settings report.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.routing import client_for_provider, ready_client_for_task, runtime_for_provider
from learnloop.config import load_config
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import _settings_ready, available_grading_providers
from tests.helpers import create_basic_vault
from tests.openai_fakes import install_fake_openai
from tests.test_settings_sidecar import _settings_rpc

EMBEDDING_PROFILE = "openrouter_embedding"


@pytest.fixture
def codex_ready(monkeypatch):
    monkeypatch.setattr(
        "learnloop.ai.runtime.check_codex_runtime",
        lambda *args, **kwargs: SimpleNamespace(status="ready", actual_revision=None, message="ok"),
    )
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)


@pytest.fixture
def vault(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    paths = create_basic_vault(tmp_path / "vault")
    loaded = load_vault(paths.root)
    assert loaded.config.ai.routing.embedding == EMBEDDING_PROFILE
    assert loaded.config.ai.providers[EMBEDDING_PROFILE].type == "openai_embedding"
    return loaded


def test_disabled_embedding_route_does_not_fail_settings_health(vault, codex_ready, monkeypatch):
    # A Codex-only learner without an OpenRouter key: a fresh template vault is healthy.
    assert not vault.config.embedding.enabled
    assert _settings_ready(vault)
    # Opting in makes the embedding route count, and its key is then required.
    vault.config.embedding.enabled = True
    assert not _settings_ready(vault)
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    assert _settings_ready(vault)


def test_settings_health_checks_each_route_under_its_own_task(vault, codex_ready, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    vault.config.ai.routing.tutor_qa = EMBEDDING_PROFILE
    assert not _settings_ready(vault)
    vault.config.ai.routing.tutor_qa = "codex_low"
    vault.config.embedding.enabled = True
    vault.config.ai.routing.embedding = "openrouter"
    assert not _settings_ready(vault)


def test_settings_health_checks_each_profile_of_a_pf_list_route(vault, codex_ready, monkeypatch):
    # Phase 5a's list routes (ensemble proposers, solver panel) are checked
    # profile by profile; a list must not break the health payload.
    vault.config.ai.routing.pf_proposers = ["codex", "openrouter"]
    vault.config.ai.routing.pf_solver_panel = ["codex_low"]
    assert not _settings_ready(vault)  # the OpenRouter proposer has no key
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    assert _settings_ready(vault)


@pytest.mark.parametrize("source", ["env", "explicit", "active", "route"])
def test_generation_never_resolves_an_embedding_profile(vault, codex_ready, monkeypatch, source):
    install_fake_openai(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    config = vault.config
    explicit = None
    if source == "env":
        monkeypatch.setenv("LEARNLOOP_AI_PROVIDER", EMBEDDING_PROFILE)
    elif source == "explicit":
        explicit = EMBEDDING_PROFILE
    elif source == "active":
        config.ai.routing.grading = None
        config.ai.active_provider = EMBEDDING_PROFILE
    else:
        config.ai.routing.grading = EMBEDDING_PROFILE
    resolved = ready_client_for_task(vault.root, config, "grading", explicit=explicit)
    assert not resolved.ready
    assert resolved.client is None
    assert "embedding-only" in resolved.runtime.message


def test_embedding_profile_primary_falls_back_to_a_generation_provider(vault, codex_ready, monkeypatch):
    install_fake_openai(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    config = vault.config
    config.ai.routing.grading = EMBEDDING_PROFILE
    config.ai.fallback_provider = "openrouter"
    resolved = ready_client_for_task(vault.root, config, "grading")
    assert resolved.ready
    assert resolved.provider_name == "openrouter"
    assert resolved.fallback_from == EMBEDDING_PROFILE
    # The reverse: a generation primary never falls back onto the embedding profile.
    config.ai.routing.grading = "missing"
    config.ai.fallback_provider = EMBEDDING_PROFILE
    assert not ready_client_for_task(vault.root, config, "grading").ready


def test_direct_provider_resolution_defaults_to_generation(vault, monkeypatch):
    install_fake_openai(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    config = vault.config
    assert not runtime_for_provider(vault.root, config, EMBEDDING_PROFILE).ready
    with pytest.raises(AIProviderUnavailable, match="embedding-only"):
        client_for_provider(vault.root, config, EMBEDDING_PROFILE)
    assert runtime_for_provider(vault.root, config, EMBEDDING_PROFILE, task="embedding").ready
    assert not runtime_for_provider(vault.root, config, "openrouter", task="embedding").ready
    with pytest.raises(AIProviderUnavailable, match="openai_embedding"):
        client_for_provider(vault.root, config, "openrouter", task="embedding")


def test_master_switch_is_enforced_where_the_client_is_obtained(vault, monkeypatch):
    module = install_fake_openai(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    config = vault.config
    disabled = ready_client_for_task(vault.root, config, "embedding")
    assert not disabled.ready
    assert disabled.client is None
    assert "embedding.enabled" in disabled.runtime.message
    assert module.instances == []
    config.embedding.enabled = True
    assert ready_client_for_task(vault.root, config, "embedding").ready
    assert len(module.instances) == 1


def test_sidecar_never_offers_or_persists_an_embedding_profile_for_generation(vault):
    assert EMBEDDING_PROFILE not in available_grading_providers(vault)
    responses = _settings_rpc(
        vault.root,
        ("set_grading_provider", {"provider": EMBEDDING_PROFILE}),
        ("update_ai_settings", {"activeProvider": EMBEDDING_PROFILE}),
        ("update_ai_settings", {"useCases": {"grading": {"provider": EMBEDDING_PROFILE}}}),
        ("get_runtime_health", {}),
    )
    assert [response["error"]["data"]["code"] for response in responses[:3]] == [
        "invalid_provider",
        "invalid_provider",
        "invalid_provider",
    ]
    persisted = load_config(vault.root / "learnloop.toml")
    assert persisted.ai.active_provider == "codex"
    assert persisted.ai.routing.grading == "codex_low"
    assert EMBEDDING_PROFILE not in responses[3]["result"]["ai"]["availableGradingProviders"]


def test_config_payloads_report_the_authoritative_embedding_model(vault):
    toml = vault.root / "learnloop.toml"
    text = toml.read_text(encoding="utf-8")
    assert 'model = "qwen/qwen3-embedding-8b"' in text
    toml.write_text(
        text.replace('model = "qwen/qwen3-embedding-8b"', 'model = "qwen/qwen3-embedding-4b"', 1),
        encoding="utf-8",
    )
    config, settings = (
        response["result"] for response in _settings_rpc(vault.root, ("get_config", {}), ("get_settings", {}))
    )
    providers = {provider["name"]: provider for provider in settings["ai"]["providers"]}
    assert providers[EMBEDDING_PROFILE]["model"] == "qwen/qwen3-embedding-4b"
    # get_config keys providers by (camelized) name.
    assert config["ai"]["providers"]["openrouterEmbedding"]["model"] == "qwen/qwen3-embedding-4b"
