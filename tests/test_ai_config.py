from __future__ import annotations

import os

from learnloop.ai.client import make_ai_provider_client
from learnloop.ai.codex_sdk import codex_config_from_ai_profile
from learnloop.config import (
    CODEX_CHECKOUT_ENV,
    AIProviderConfig,
    LearnLoopConfig,
    load_config,
)
from learnloop.vault.loader import init_vault


def test_default_config_contains_ai_codex_profile(tmp_path):
    init_vault(tmp_path)

    config = load_config(tmp_path / "learnloop.toml")

    # P0.5 cutover: new vaults default to mvp-0.8 (spec §7.2).
    assert config.algorithms.algorithm_version == "mvp-0.8"
    assert config.ai.active_provider == "codex"
    assert config.ai.providers["codex"].type == "codex_sdk"
    assert config.ai.providers["codex"].model == "gpt-5.6-sol"
    assert config.ai.providers["codex"].reasoning_effort == "low"
    assert config.ai.providers["codex_low"].model == "gpt-5.6-sol"
    assert config.ai.providers["codex_low"].reasoning_effort == "low"
    assert config.ai.providers["codex_medium"].model == "gpt-5.6-sol"
    assert config.ai.providers["codex_medium"].reasoning_effort == "medium"
    assert config.codex.model == "gpt-5.6-sol"
    assert config.codex.reasoning_effort == "low"
    assert config.ai.providers["deepseek_flash"].model == "deepseek-v4-flash"
    assert config.ai.providers["deepseek_flash"].thinking == "disabled"
    assert config.ai.providers["deepseek_pro"].model == "deepseek-v4-pro"
    assert config.ai.providers["deepseek_pro"].thinking == "enabled"
    assert config.ai.providers["openrouter"].type == "openrouter"
    assert config.ai.routing.grading == "codex_low"
    assert config.ai.routing.tutor_qa == "codex_low"
    assert config.ai.routing.teach_back == "codex_low"
    assert config.ai.routing.authoring == "codex_medium"
    assert config.ai.routing.canonical_ingest == "codex_medium"
    assert config.ai.routing.canonical_ingest_retry == "codex_medium"


def test_default_config_seeds_openrouter_profile(tmp_path):
    init_vault(tmp_path)

    for config in (load_config(tmp_path / "learnloop.toml"), LearnLoopConfig()):
        profile = config.ai.providers["openrouter"]
        assert profile.type == "openrouter"
        assert profile.model == "deepseek/deepseek-chat"
        assert profile.api_key_env == "OPENROUTER_API_KEY"
        assert profile.response_format == "json_object"
        assert profile.timeout_seconds == 180
        assert profile.base_url is None


def test_global_ai_timeout_is_applied_to_codex_sdk_profiles(tmp_path):
    config = LearnLoopConfig()
    config.ai.timeout_seconds = 17
    config.ai.providers["codex_medium"].timeout_seconds = None

    client = make_ai_provider_client(
        config,
        tmp_path,
        provider_name="codex_medium",
    )

    assert client.config.timeout_seconds == 17


def test_in_memory_defaults_match_persisted_algorithm_and_codex_profile(tmp_path):
    init_vault(tmp_path)

    loaded = load_config(tmp_path / "learnloop.toml")
    in_memory = LearnLoopConfig()

    # P0.5 cutover: new vaults are written as mvp-0.8; the in-memory default stays
    # mvp-0.6 because it is the fallback for configs that predate the field and must
    # never silently activate the new knowledge model over legacy content.
    assert loaded.algorithms.algorithm_version == "mvp-0.8"
    assert in_memory.algorithms.algorithm_version == "mvp-0.6"

    for config in (loaded, in_memory):
        assert config.codex.model == "gpt-5.6-sol"
        assert config.codex.reasoning_effort == "low"
        assert config.ai.providers["codex"].model == "gpt-5.6-sol"
        assert config.ai.providers["codex"].reasoning_effort == "low"
        assert config.ai.providers["codex_low"].reasoning_effort == "low"
        assert config.ai.providers["codex_medium"].reasoning_effort == "medium"
        assert config.ai.routing.authoring == "codex_medium"
        assert config.ai.routing.grading == "codex_low"


def test_default_config_ships_blank_codex_checkout_path(tmp_path):
    # The Codex checkout is a per-machine concern, sourced from global settings
    # rather than the committed vault config, so the template must not hardcode it.
    init_vault(tmp_path)

    config = load_config(tmp_path / "learnloop.toml")

    assert config.codex.checkout_path == ""
    assert config.ai.providers["codex"].checkout_path in (None, "")


def test_codex_checkout_path_env_override_applies_to_codex_and_ai_provider(tmp_path, monkeypatch):
    init_vault(tmp_path)
    checkout = tmp_path / "codex-checkout"
    checkout.mkdir()
    monkeypatch.setenv(CODEX_CHECKOUT_ENV, str(checkout))

    config = load_config(tmp_path / "learnloop.toml")

    assert config.codex.checkout_path == str(checkout)
    assert config.ai.providers["codex"].checkout_path == str(checkout)
    assert config.ai.providers["codex_low"].checkout_path == str(checkout)
    assert config.ai.providers["codex_medium"].checkout_path == str(checkout)


def test_legacy_codex_routes_upgrade_to_workload_specific_effort_profiles():
    config = LearnLoopConfig.model_validate(
        {
            "ai": {
                "active_provider": "codex",
                "routing": {
                    "grading": "codex",
                    "canonical_ingest": "codex",
                    "canonical_ingest_retry": "codex",
                    "authoring": "codex",
                    "tutor_qa": "codex",
                    "teach_back": "codex",
                },
                "providers": {
                    "codex": {
                        "type": "codex_sdk",
                        "model": "gpt-5.5",
                        "reasoning_effort": "medium",
                    }
                },
            }
        }
    )

    assert config.ai.routing.authoring == "codex_medium"
    assert config.ai.routing.canonical_ingest == "codex_medium"
    assert config.ai.routing.canonical_ingest_retry == "codex_medium"
    assert config.ai.routing.grading == "codex_low"
    assert config.ai.routing.tutor_qa == "codex_low"
    assert config.ai.routing.teach_back == "codex_low"
    assert config.ai.providers["codex"].model == "gpt-5.6-sol"
    assert config.ai.providers["codex"].reasoning_effort == "low"
    assert config.ai.providers["codex_low"].reasoning_effort == "low"
    assert config.ai.providers["codex_medium"].reasoning_effort == "medium"
    assert config.codex.model == "gpt-5.6-sol"
    assert config.codex.reasoning_effort == "low"


def test_codex_checkout_path_loaded_from_global_settings_file(tmp_path, monkeypatch):
    init_vault(tmp_path)
    checkout = tmp_path / "codex-checkout"
    checkout.mkdir()
    settings_dir = tmp_path / "global-config"
    settings_dir.mkdir()
    (settings_dir / "settings.env").write_text(
        f"{CODEX_CHECKOUT_ENV}={checkout}\n", encoding="utf-8"
    )
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(settings_dir))
    # load_dotenv writes straight into os.environ; ensure a clean slate and undo it.
    monkeypatch.delenv(CODEX_CHECKOUT_ENV, raising=False)
    try:
        config = load_config(tmp_path / "learnloop.toml")
        assert config.codex.checkout_path == str(checkout)
    finally:
        os.environ.pop(CODEX_CHECKOUT_ENV, None)


def test_shell_env_wins_over_global_settings_file(tmp_path, monkeypatch):
    init_vault(tmp_path)
    settings_dir = tmp_path / "global-config"
    settings_dir.mkdir()
    (settings_dir / "settings.env").write_text(
        f"{CODEX_CHECKOUT_ENV}={tmp_path / 'from-file'}\n", encoding="utf-8"
    )
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(settings_dir))
    monkeypatch.setenv(CODEX_CHECKOUT_ENV, str(tmp_path / "from-shell"))

    config = load_config(tmp_path / "learnloop.toml")

    assert config.codex.checkout_path == str(tmp_path / "from-shell")


def test_sparse_codex_ai_profile_uses_current_codex_defaults():
    sparse = AIProviderConfig(type="codex_sdk")

    codex_config = codex_config_from_ai_profile(sparse)

    assert codex_config.model == "gpt-5.6-sol"
    assert codex_config.reasoning_effort == "low"


def test_default_config_contains_recall_error_impacts(tmp_path):
    init_vault(tmp_path)

    loaded = load_config(tmp_path / "learnloop.toml")
    in_memory = LearnLoopConfig()

    for config in (loaded, in_memory):
        recall = config.error_impacts["recall_failure"]
        scaffold = config.error_impacts["scaffold_failure"]
        slip = config.error_impacts["arithmetic_slip"]
        assert scaffold.local_severity_gain > recall.local_severity_gain
        assert slip.local_severity_gain < recall.local_severity_gain
        assert scaffold.families["recall"] < recall.families["recall"]
        assert slip.families["numeric"] < 0.0

        # cross_lo_propagation.error_gates is retired (knowledge-model §8.3): the
        # default config no longer seeds it.
        assert config.cross_lo_propagation.error_gates == {}


def test_error_impacts_max_sharpening_maps_to_recall_coverage_runtime_field():
    config = LearnLoopConfig.model_validate(
        {
            "error_impacts": {
                "max_sharpening": 2.25,
                "recall_failure": {"local_severity_gain": 0.9},
            }
        }
    )

    assert config.recall_coverage.max_error_sharpening == 2.25
    assert config.error_impacts["recall_failure"].local_severity_gain == 0.9


def test_legacy_codex_config_maps_to_ai_profile():
    config = LearnLoopConfig.model_validate(
        {
            "codex": {
                "provider": "http",
                "model": "gpt-5.4-mini",
                "checkout_path": "codex-checkout",
                "base_url": "http://127.0.0.1:9999",
            }
        }
    )

    profile = config.ai.providers["codex"]

    assert profile.type == "http_adapter"
    assert profile.model == "gpt-5.4-mini"
    assert profile.checkout_path == "codex-checkout"
    assert profile.base_url == "http://127.0.0.1:9999"


def test_ai_provider_profiles_load_openai_chat():
    config = LearnLoopConfig.model_validate(
        {
            "ai": {
                "active_provider": "deepseek_flash",
                "providers": {
                    "deepseek_flash": {
                        "type": "openai_chat",
                        "base_url": "https://api.deepseek.com",
                        "api_key_env": "DEEPSEEK_API_KEY",
                        "model": "deepseek-v4-flash",
                        "response_format": "json_object",
                        "thinking": "disabled",
                        "max_tokens": 8192,
                    }
                },
            }
        }
    )

    assert config.ai.providers["deepseek_flash"] == AIProviderConfig(
        type="openai_chat",
        base_url="https://api.deepseek.com",
        api_key_env="DEEPSEEK_API_KEY",
        model="deepseek-v4-flash",
        response_format="json_object",
        thinking="disabled",
        max_tokens=8192,
    )
