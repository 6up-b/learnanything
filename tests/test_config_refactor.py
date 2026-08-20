from __future__ import annotations

import json
import tomllib
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.config import (
    DEFAULT_CONFIG_TEXT,
    DEFAULTS_SNAPSHOT_BY_ALGORITHM,
    CodexHTTPProviderConfig,
    CodexSDKProviderConfig,
    LEGACY_DEFAULT_CONFIG_TEXT,
    LearnLoopConfig,
    OpenAICompatibleProviderConfig,
    OpenRouterProviderConfig,
    OPENROUTER_TRANSCRIPTION_PROVIDER,
    effective_defaults_fingerprint,
)
from learnloop.vault.loader import init_vault
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import config_dto


def _parsed(text: str) -> LearnLoopConfig:
    return LearnLoopConfig.model_validate(tomllib.loads(text))


def test_config_responsibilities_have_canonical_module_owners() -> None:
    import learnloop.config as public_config
    from learnloop.config import compat, loader, schema, template

    assert public_config.load_config is loader.load_config
    assert public_config.load_dotenv is loader.load_dotenv
    assert public_config.DEFAULT_CONFIG_TEXT is template.DEFAULT_CONFIG_TEXT
    assert public_config.effective_defaults_fingerprint is (
        template.effective_defaults_fingerprint
    )
    assert public_config.CodexConfig is compat.CodexConfig
    assert public_config.ai_provider_from_codex is compat.ai_provider_from_codex

    # Re-export shims would make the package tree look split while leaving the
    # original module responsible for every behavior. Keep that failure mode
    # pinned explicitly.
    for moved_name in (
        "ConfigLoadError",
        "DEFAULT_CONFIG_TEXT",
        "LEGACY_DEFAULT_CONFIG_TEXT",
        "ai_provider_from_codex",
        "effective_defaults_fingerprint",
        "load_config",
        "load_dotenv",
        "write_default_config",
    ):
        assert not hasattr(schema, moved_name)


def test_loader_orchestrates_compatibility_before_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from learnloop.config import loader

    path = tmp_path / "learnloop.toml"
    path.write_text(
        'schema_version = 1\n[codex]\nprovider = "http"\nmodel = "legacy-model"\n',
        encoding="utf-8",
    )
    original = loader.normalize_config_input
    seen: list[dict[str, object]] = []

    def recording_normalizer(raw):
        seen.append(raw)
        return original(raw)

    monkeypatch.setattr(loader, "normalize_config_input", recording_normalizer)
    config = loader.load_config(path)

    assert seen and "codex" in seen[0]
    assert config.ai.providers["codex"].type == "http"
    assert config.ai.providers["codex"].model == "legacy-model"


def test_generated_template_is_decision_only_schema_v2() -> None:
    assert len(DEFAULT_CONFIG_TEXT.splitlines()) <= 80
    assert tomllib.loads(DEFAULT_CONFIG_TEXT)["schema_version"] == 2
    assert "[codex]" not in DEFAULT_CONFIG_TEXT
    assert "default_horizon_days" not in DEFAULT_CONFIG_TEXT
    assert "self_graded_evidence_weight" not in DEFAULT_CONFIG_TEXT
    assert "facet_recall_prior_pseudo_count" not in DEFAULT_CONFIG_TEXT
    assert "max_turns" not in DEFAULT_CONFIG_TEXT
    assert "coverage_epsilon" not in DEFAULT_CONFIG_TEXT
    assert "evidence_span_input_tokens" not in DEFAULT_CONFIG_TEXT
    assert "auth_mode" not in DEFAULT_CONFIG_TEXT


def test_minimal_template_preserves_non_provider_effective_defaults() -> None:
    before = _parsed(LEGACY_DEFAULT_CONFIG_TEXT).model_dump(mode="json")
    after = _parsed(DEFAULT_CONFIG_TEXT).model_dump(mode="json")

    before.pop("schema_version")
    after.pop("schema_version")
    before.pop("ai")
    after.pop("ai")
    assert after == before

    old_ai = _parsed(LEGACY_DEFAULT_CONFIG_TEXT).ai
    new_ai = _parsed(DEFAULT_CONFIG_TEXT).ai
    assert new_ai.active_provider == old_ai.active_provider
    assert new_ai.fallback_provider == old_ai.fallback_provider
    assert new_ai.timeout_seconds == old_ai.timeout_seconds
    for route in (
        "grading",
        "canonical_ingest",
        "canonical_ingest_retry",
        "authoring",
        "tutor_qa",
        "teach_back",
        "rung_variant",
        "animation",
    ):
        assert getattr(new_ai.routing, route) == getattr(old_ai.routing, route)
    for name in ("codex", "codex_low", "codex_medium", "openrouter"):
        assert new_ai.providers[name].type == old_ai.providers[name].type
        assert new_ai.providers[name].model == old_ai.providers[name].model
        assert (
            new_ai.providers[name].reasoning_effort
            == old_ai.providers[name].reasoning_effort
        )


def test_retired_keys_parse_and_are_ignored() -> None:
    config = LearnLoopConfig.model_validate(
        {
            "schema_version": 1,
            "forecasts": {"default_horizon_days": 99},
            "probe": {
                "episode": {"self_graded_evidence_weight": 0.99},
                "dialogue": {"max_turns": 7},
            },
            "recall_coverage": {
                "facet_recall_prior_pseudo_count": 99,
                "coverage_epsilon": 0.25,
            },
            "ingest": {"budgets": {"evidence_span_input_tokens": 1}},
            "cross_lo_propagation": {
                "default": {"hop_decay": 0.9},
                "error_gates": {"recall_failure": {"mean_factor": 0.5}},
            },
        }
    )

    dumped = config.model_dump(mode="json")
    assert "forecasts" not in dumped
    assert "self_graded_evidence_weight" not in dumped["probe"]["episode"]
    assert "max_turns" not in dumped["probe"]["dialogue"]
    assert "facet_recall_prior_pseudo_count" not in dumped["recall_coverage"]
    assert "coverage_epsilon" not in dumped["recall_coverage"]
    assert "evidence_span_input_tokens" not in dumped["ingest"]["budgets"]
    assert "cross_lo_propagation" not in dumped


def test_provider_without_type_keeps_codex_sdk_compatibility() -> None:
    config = LearnLoopConfig.model_validate(
        {"ai": {"providers": {"custom_codex": {"model": "gpt-5.6-sol"}}}}
    )
    assert config.ai.providers["custom_codex"].type == "codex_sdk"
    assert isinstance(config.ai.providers["custom_codex"], CodexSDKProviderConfig)


def test_provider_profiles_use_discriminated_types_and_ignore_retired_auth() -> None:
    config = LearnLoopConfig.model_validate(
        {
            "ai": {
                "providers": {
                    "sdk": {"type": "codex_sdk", "auth_mode": "chatgpt"},
                    "http": {"type": "http_adapter"},
                    "chat": {"type": "openai_compatible"},
                    "router": {"type": "openrouter"},
                }
            }
        }
    )

    assert isinstance(config.ai.providers["sdk"], CodexSDKProviderConfig)
    assert isinstance(config.ai.providers["http"], CodexHTTPProviderConfig)
    assert config.ai.providers["http"].type == "http"
    assert isinstance(config.ai.providers["chat"], OpenAICompatibleProviderConfig)
    assert config.ai.providers["chat"].type == "openai_chat"
    assert isinstance(config.ai.providers["router"], OpenRouterProviderConfig)
    assert "auth_mode" not in config.ai.providers["sdk"].model_dump()
    assert "checkout_path" not in OpenAICompatibleProviderConfig.model_fields
    assert "api_key_env" not in CodexSDKProviderConfig.model_fields
    assert "http_referer" not in OpenAICompatibleProviderConfig.model_fields

    with pytest.raises(ValidationError):
        LearnLoopConfig.model_validate(
            {"ai": {"providers": {"bad": {"type": "unknown_provider"}}}}
        )


def test_legacy_openrouter_audio_becomes_a_dedicated_transcription_route() -> None:
    config = LearnLoopConfig.model_validate(
        {
            "ingest": {
                "audio": {
                    "provider": "openrouter",
                    "transcription_model": "google/gemini-2.5-flash",
                    "timeout_seconds": 417,
                    "language": "fr-CA",
                    "max_file_mb": 19,
                }
            },
            "ai": {
                "providers": {
                    "openrouter": {
                        "type": "openrouter",
                        "model": "base/model",
                        "api_key_env": "CUSTOM_OPENROUTER_KEY",
                        "input_modalities": ["pdf"],
                    }
                }
            },
        }
    )

    assert config.ai.routing.transcription == OPENROUTER_TRANSCRIPTION_PROVIDER
    profile = config.ai.providers[OPENROUTER_TRANSCRIPTION_PROVIDER]
    assert isinstance(profile, OpenRouterProviderConfig)
    assert profile.model == "google/gemini-2.5-flash"
    assert profile.timeout_seconds == 417
    assert profile.api_key_env == "CUSTOM_OPENROUTER_KEY"
    assert profile.input_modalities == ["pdf", "audio"]
    assert config.ingest.audio.language == "fr-CA"
    assert config.ingest.audio.max_file_mb == 19


def test_canonical_transcription_route_wins_over_legacy_audio_input() -> None:
    config = LearnLoopConfig.model_validate(
        {
            "ingest": {
                "audio": {
                    "provider": "openrouter",
                    "transcription_model": "legacy/model",
                }
            },
            "ai": {
                "routing": {"transcription": "custom_audio"},
                "providers": {
                    "custom_audio": {
                        "type": "openrouter",
                        "model": "canonical/model",
                        "input_modalities": ["audio"],
                    }
                },
            },
        }
    )

    assert config.ai.routing.transcription == "custom_audio"
    assert config.ai.providers["custom_audio"].model == "canonical/model"


def test_endpoint_audio_config_does_not_create_a_chat_route() -> None:
    config = LearnLoopConfig.model_validate(
        {
            "ingest": {
                "audio": {
                    "provider": "openai_compatible",
                    "transcription_model": "whisper-large-v3",
                    "timeout_seconds": 222,
                }
            }
        }
    )

    assert not config.ai.routing.transcription
    assert OPENROUTER_TRANSCRIPTION_PROVIDER not in config.ai.providers
    assert config.ingest.audio.transcription_model == "whisper-large-v3"
    assert config.ingest.audio.timeout_seconds == 222


def test_schema_v1_is_accepted_but_v2_is_generated() -> None:
    assert LearnLoopConfig.model_validate({"schema_version": 1}).schema_version == 1
    assert LearnLoopConfig().schema_version == 2
    with pytest.raises(ValidationError):
        LearnLoopConfig.model_validate({"schema_version": 3})


def test_legacy_codex_is_input_only_and_sidecar_does_not_reexport_it(tmp_path) -> None:
    config = LearnLoopConfig.model_validate(
        {
            "schema_version": 1,
            "codex": {
                "provider": "http",
                "model": "legacy-model",
                "base_url": "http://127.0.0.1:9999",
                "auth_mode": "chatgpt",
            },
        }
    )
    assert isinstance(config.ai.providers["codex"], CodexHTTPProviderConfig)
    assert config.ai.providers["codex"].model == "legacy-model"
    assert config.codex.provider == "http"
    assert "codex" not in config.model_dump()

    init_vault(tmp_path)
    assert "codex" not in config_dto(load_vault(tmp_path))


def test_tracked_fixture_config_corpus_is_compatibly_normalized() -> None:
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures"
    config_paths = sorted(fixture_root.glob("*/learnloop.toml"))
    assert len(config_paths) >= 9

    for config_path in config_paths:
        raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
        canonical = deepcopy(raw)
        canonical.pop("codex", None)
        for profile in canonical.get("ai", {}).get("providers", {}).values():
            if isinstance(profile, dict):
                profile.pop("auth_mode", None)

        legacy_config = LearnLoopConfig.model_validate(raw)
        canonical_config = LearnLoopConfig.model_validate(canonical)
        assert legacy_config.model_dump(mode="json") == canonical_config.model_dump(
            mode="json"
        ), config_path


def test_defaults_snapshot_is_keyed_by_algorithm_version() -> None:
    config = _parsed(DEFAULT_CONFIG_TEXT)
    assert effective_defaults_fingerprint(config) == DEFAULTS_SNAPSHOT_BY_ALGORITHM[
        config.algorithms.algorithm_version
    ]


def test_config_effective_reports_full_model_and_explicit_overrides(tmp_path) -> None:
    init_vault(tmp_path)
    runner = CliRunner()

    full = runner.invoke(app, ["config", "effective", "--vault", str(tmp_path), "--json"])
    assert full.exit_code == 0, full.output
    effective = json.loads(full.output)
    assert effective["schema_version"] == 2
    assert effective["mastery"]["cold_start_prior_logit_variance"] == 3.0

    overrides = runner.invoke(
        app,
        [
            "config",
            "effective",
            "--vault",
            str(tmp_path),
            "--only-overrides",
            "--json",
        ],
    )
    assert overrides.exit_code == 0, overrides.output
    explicit = json.loads(overrides.output)
    assert explicit["schema_version"] == 2
    assert "mastery" not in explicit
