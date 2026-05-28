from __future__ import annotations

from learnloop.ai.codex_sdk import codex_config_from_ai_profile
from learnloop.config import AIProviderConfig, LearnLoopConfig, load_config
from learnloop.vault.loader import init_vault


def test_default_config_contains_ai_codex_profile(tmp_path):
    init_vault(tmp_path)

    config = load_config(tmp_path / "learnloop.toml")

    assert config.algorithms.algorithm_version == "mvp-0.2"
    assert config.ai.active_provider == "codex"
    assert config.ai.providers["codex"].type == "codex_sdk"
    assert config.ai.providers["codex"].model == "gpt-5.5"
    assert config.ai.providers["codex"].reasoning_effort == "medium"
    assert config.codex.model == "gpt-5.5"
    assert config.codex.reasoning_effort == "medium"
    assert config.ai.providers["deepseek_flash"].model == "deepseek-v4-flash"
    assert config.ai.providers["deepseek_flash"].thinking == "disabled"
    assert config.ai.providers["deepseek_pro"].model == "deepseek-v4-pro"
    assert config.ai.providers["deepseek_pro"].thinking == "enabled"
    assert config.ai.routing.grading == "codex"


def test_in_memory_defaults_match_persisted_algorithm_and_codex_profile(tmp_path):
    init_vault(tmp_path)

    loaded = load_config(tmp_path / "learnloop.toml")
    in_memory = LearnLoopConfig()

    for config in (loaded, in_memory):
        assert config.algorithms.algorithm_version == "mvp-0.2"
        assert config.codex.model == "gpt-5.5"
        assert config.codex.reasoning_effort == "medium"
        assert config.ai.providers["codex"].model == "gpt-5.5"
        assert config.ai.providers["codex"].reasoning_effort == "medium"


def test_sparse_codex_ai_profile_uses_current_codex_defaults():
    sparse = AIProviderConfig(type="codex_sdk")

    codex_config = codex_config_from_ai_profile(sparse)

    assert codex_config.model == "gpt-5.5"
    assert codex_config.reasoning_effort == "medium"


def test_default_config_contains_recall_error_impacts_and_gates(tmp_path):
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

        gates = config.cross_lo_propagation.error_gates
        assert gates["recall_failure"].mean_factor == 0.0
        assert gates["scaffold_failure"].mean_factor == 0.0
        assert gates["arithmetic_slip"].mean_factor == 0.0
        assert gates["arithmetic_slip"].variance_factor < gates["scaffold_failure"].variance_factor


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
