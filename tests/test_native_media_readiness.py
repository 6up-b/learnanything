from __future__ import annotations

import pytest

from learnloop.ai.native_media import (
    REASON_MANUAL_PROVIDER,
    REASON_MODALITY_NOT_DECLARED,
    REASON_PROVIDER_MISSING,
    REASON_PROVIDER_NOT_CHAT,
    native_modality_readiness,
    native_requested,
)
from learnloop.config.schema import LearnLoopConfig


def _config(**overrides):
    payload = {
        "ai": {
            "active_provider": "codex",
            "routing": {"canonical_ingest": "openrouter"},
            "providers": {
                "openrouter": {
                    "type": "openrouter",
                    "model": "google/gemini-2.5-pro",
                    "input_modalities": ["pdf", "audio"],
                }
            },
        },
        "ingest": {"pdf": {"engine": "native"}, "audio": {"mode": "native"}},
    }
    for path, value in overrides.items():
        cursor = payload
        parts = path.split(".")
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[parts[-1]] = value
    return LearnLoopConfig.model_validate(payload)


def test_ready_when_route_is_a_chat_provider_declaring_the_modality(monkeypatch):
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    for modality in ("pdf", "audio"):
        readiness = native_modality_readiness(_config(), modality)
        assert readiness.ready is True
        assert readiness.requested is True
        assert readiness.reason is None
        assert readiness.provider_name == "openrouter"
        assert readiness.provider_type == "openrouter"
        assert readiness.model == "google/gemini-2.5-pro"
        assert readiness.task == "canonical_ingest"
        assert "accepts" in readiness.message
    assert native_modality_readiness(_config(), "pdf").max_mb == 32
    assert native_modality_readiness(_config(), "audio").max_mb == 20


def test_requested_follows_each_modality_authority(monkeypatch):
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    config = _config(**{"ingest.pdf.engine": "auto", "ingest.audio.mode": "transcription"})
    assert native_requested(config, "pdf") is False
    assert native_requested(config, "audio") is False
    # A per-run override (the pipeline's effective PDF engine) wins over the vault.
    readiness = native_modality_readiness(config, "pdf", requested=True)
    assert readiness.requested is True and readiness.ready is True
    assert native_modality_readiness(config, "pdf").requested is False


def test_reasons_are_typed(monkeypatch):
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    not_declared = native_modality_readiness(
        _config(**{"ai.providers.openrouter.input_modalities": ["audio"]}), "pdf"
    )
    assert not_declared.ready is False
    assert not_declared.declared is False
    assert not_declared.reason == REASON_MODALITY_NOT_DECLARED

    not_chat = native_modality_readiness(_config(**{"ai.routing.canonical_ingest": "codex"}), "pdf")
    assert not_chat.ready is False
    assert not_chat.reason == REASON_PROVIDER_NOT_CHAT
    assert not_chat.provider_type == "codex_sdk"

    missing = native_modality_readiness(_config(**{"ai.routing.canonical_ingest": "ghost"}), "pdf")
    assert missing.ready is False
    assert missing.reason == REASON_PROVIDER_MISSING

    manual = native_modality_readiness(_config(**{"ai.routing.canonical_ingest": "manual"}), "audio")
    assert manual.ready is False
    assert manual.reason == REASON_MANUAL_PROVIDER


def test_environment_override_selects_the_provider_like_runtime(monkeypatch):
    monkeypatch.setenv("LEARNLOOP_AI_PROVIDER", "codex")
    readiness = native_modality_readiness(_config(), "pdf")
    assert readiness.provider_name == "codex"
    assert readiness.reason == REASON_PROVIDER_NOT_CHAT


def test_unknown_modality_is_rejected():
    with pytest.raises(ValueError):
        native_modality_readiness(_config(), "hologram")


def test_as_dict_is_camel_safe_payload(monkeypatch):
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    payload = native_modality_readiness(_config(), "pdf").as_dict()
    assert set(payload) == {
        "modality", "requested", "task", "provider_name", "provider_type", "model",
        "declared", "ready", "reason", "message", "max_mb",
    }
