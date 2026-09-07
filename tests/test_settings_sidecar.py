from __future__ import annotations

import io
import json

from learnloop.config import load_config
from learnloop_sidecar.server import serve

from tests.helpers import create_basic_vault


def _rpc(messages: list[dict]) -> list[dict]:
    stdin = io.StringIO("".join(json.dumps(message) + "\n" for message in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def _settings_rpc(vault_root, *messages):
    payload = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"vaultPath": str(vault_root)},
        }
    ]
    payload.extend(
        {
            "jsonrpc": "2.0",
            "id": index + 2,
            "method": name,
            "params": params,
        }
        for index, (name, params) in enumerate(messages)
    )
    return _rpc(payload)[1:]


def test_config_and_settings_report_ai_routes(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    responses = _settings_rpc(
        vault_root,
        ("get_config", {}),
        ("get_settings", {}),
    )

    config = responses[0]["result"]
    settings = responses[1]["result"]
    assert config["ai"]["routing"]["authoring"] == "codex_medium"
    assert settings["ai"]["routing"]["grading"] == "codex_low"
    assert settings["ai"]["envProviderOverride"] is None
    assert sorted(settings["ai"]["useCases"]) == ["animation", "grading", "ingest", "tutor", "video"]
    assert "openrouter" in {
        provider["name"] for provider in settings["ai"]["providers"]
    }
    assert settings["openrouter"]["keyPresent"] is False


def test_update_ai_settings_materializes_openrouter_grading_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    result = _settings_rpc(
        vault_root,
        (
            "update_ai_settings",
            {
                "useCases": {
                    "grading": {
                        "provider": "openrouter",
                        "openrouterModel": "anthropic/claude-sonnet-4.5",
                    }
                }
            },
        ),
    )[0]["result"]

    assert result["ai"]["routing"]["grading"] == "openrouter_grading"
    config = load_config(vault_root / "learnloop.toml")
    assert config.ai.routing.grading == "openrouter_grading"
    assert (
        config.ai.providers["openrouter_grading"].model
        == "anthropic/claude-sonnet-4.5"
    )


def test_update_ai_settings_expands_ingest_and_clears_manual_override(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    responses = _settings_rpc(
        vault_root,
        ("set_grading_provider", {"provider": "manual"}),
        (
            "update_ai_settings",
            {"useCases": {"grading": {"provider": "deepseek_flash"}}},
        ),
        (
            "update_ai_settings",
            {
                "useCases": {
                    "ingest": {
                        "provider": "openrouter",
                        "openrouterModel": "deepseek/deepseek-chat",
                    }
                }
            },
        ),
    )

    assert responses[0]["result"]["manualGrading"] is True
    assert responses[1]["result"]["health"]["ai"]["gradingProviderOverride"] is None
    routing = responses[2]["result"]["ai"]["routing"]
    assert routing["canonicalIngest"] == "openrouter_ingest"
    assert routing["canonicalIngestRetry"] == "openrouter_ingest"
    assert routing["authoring"] == "openrouter_ingest"


def test_update_ai_settings_rejects_unknown_values_without_persisting(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    responses = _settings_rpc(
        vault_root,
        (
            "update_ai_settings",
            {"useCases": {"grading": {"provider": "unknown"}}},
        ),
        (
            "update_ai_settings",
            {"useCases": {"dreaming": {"provider": "codex"}}},
        ),
        (
            "update_ai_settings",
            {
                "useCases": {
                    "grading": {
                        "provider": "openrouter",
                        "openrouterModel": "has spaces",
                    }
                }
            },
        ),
    )

    assert [response["error"]["data"]["code"] for response in responses] == [
        "invalid_provider",
        "invalid_use_case",
        "invalid_model",
    ]
    assert load_config(vault_root / "learnloop.toml").ai.routing.grading == "codex_low"


def test_set_openrouter_key_writes_global_env_without_echoing_secret(
    tmp_path,
    monkeypatch,
):
    global_root = tmp_path / "global"
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(global_root))
    monkeypatch.setenv("OPENROUTER_API_KEY", "stale-key")
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    result = _settings_rpc(
        vault_root,
        ("set_openrouter_api_key", {"apiKey": "or-fresh-key-1234"}),
    )[0]["result"]

    assert result["keyPresent"] is True
    assert result["keyHint"] == "1234"
    assert result["ready"] is True
    assert "or-fresh-key-1234" not in json.dumps(result)
    assert (
        global_root.joinpath("settings.env").read_text(encoding="utf-8")
        == "OPENROUTER_API_KEY=or-fresh-key-1234\n"
    )


def test_set_openrouter_key_can_remove_and_reject_control_characters(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "remove-me")
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    responses = _settings_rpc(
        vault_root,
        ("set_openrouter_api_key", {"apiKey": ""}),
        ("set_openrouter_api_key", {"apiKey": "bad\u0000key"}),
    )

    assert responses[0]["result"]["keyPresent"] is False
    assert responses[1]["error"]["data"]["code"] == "invalid_api_key"


def test_new_vault_inherits_ai_routes_but_existing_vault_is_untouched(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    source_root = tmp_path / "source"
    create_basic_vault(source_root)
    new_root = tmp_path / "new"
    existing_root = tmp_path / "existing"
    create_basic_vault(existing_root)

    responses = _settings_rpc(
        source_root,
        (
            "update_ai_settings",
            {
                "useCases": {
                    "ingest": {
                        "provider": "openrouter",
                        "openrouterModel": "anthropic/claude-sonnet-4.5",
                    }
                }
            },
        ),
        ("create_vault", {"path": str(new_root)}),
        ("create_vault", {"path": str(existing_root)}),
    )
    assert all("result" in response for response in responses)

    new_config = load_config(new_root / "learnloop.toml")
    existing_config = load_config(existing_root / "learnloop.toml")
    assert new_config.ai.routing.authoring == "openrouter_ingest"
    assert (
        new_config.ai.providers["openrouter_ingest"].model
        == "anthropic/claude-sonnet-4.5"
    )
    assert existing_config.ai.routing.authoring == "codex_medium"


def test_get_settings_reports_ingest_budgets_and_provider_limits(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    settings = _settings_rpc(vault_root, ("get_settings", {}))[0]["result"]

    budgets = settings["ingest"]["budgets"]
    assert budgets["inventoryInputTokens"] == 20000
    assert budgets["synthesisTotalInputCeiling"] == 48000
    # The UI validates against the same ranges the handler enforces.
    assert settings["ingest"]["budgetBounds"]["inventoryOutputTokens"] == {
        "min": 1000,
        "max": 100000,
    }
    # `[ingest.providers.*]` is commented out by default, which is exactly the
    # state that silently disables the build plan's context checks.
    limits = settings["ingest"]["providerLimits"]
    assert limits["provider"] == "codex_medium"
    assert limits["contextTokens"] is None


def test_update_ingest_settings_persists_budgets_and_provider_limits(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    responses = _settings_rpc(
        vault_root,
        (
            "update_ingest_settings",
            {
                "budgets": {
                    "inventoryOutputTokens": 4500,
                    "synthesisTotalInputCeiling": 120000,
                },
                "providerContextTokens": 128000,
                "providerMaxOutputTokens": 32768,
            },
        ),
    )
    result = responses[0]["result"]
    assert result["ingest"]["budgets"]["inventoryOutputTokens"] == 4500
    assert result["ingest"]["budgets"]["synthesisTotalInputCeiling"] == 120000
    assert result["ingest"]["providerLimits"]["contextTokens"] == 128000

    config = load_config(vault_root / "learnloop.toml")
    assert config.ingest.budgets.inventory_output_tokens == 4500
    assert config.ingest.budgets.synthesis_total_input_ceiling == 120000
    # Untouched ceilings keep their defaults, so one row can be applied alone.
    assert config.ingest.budgets.inventory_input_tokens == 20000
    assert config.ingest.providers["codex_medium"].context_tokens == 128000
    assert config.ingest.providers["codex_medium"].max_output_tokens == 32768


def test_update_ingest_settings_rejects_bad_budgets_without_persisting(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    responses = _settings_rpc(
        vault_root,
        ("update_ingest_settings", {"budgets": {"inventoryOutputTokens": 10}}),
        ("update_ingest_settings", {"budgets": {"notACeiling": 4000}}),
        ("update_ingest_settings", {"providerContextTokens": 0}),
    )

    assert [response["error"]["data"]["code"] for response in responses] == [
        "invalid_inventory_budget",
        "invalid_budget_override",
        "invalid_provider_limit",
    ]
    config = load_config(vault_root / "learnloop.toml")
    assert config.ingest.budgets.inventory_output_tokens == 3000
    assert "codex_medium" not in config.ingest.providers


def test_get_settings_reports_animation_block(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    animation = _settings_rpc(vault_root, ("get_settings", {}))[0]["result"]["animation"]

    assert animation["enabled"] is True
    assert animation["renderer"] == "manim"
    assert animation["rendererOptions"] == ["manim", "video_model"]
    assert animation["video"]["ready"] is False
    assert "no video model chosen" in animation["video"]["reason"]
    assert animation["video"]["maxShots"] == 4
    assert animation["video"]["timeoutSeconds"] == 1800
    assert animation["quality"] == "qm"
    assert animation["qualityOptions"] == ["ql", "qm", "qh"]
    assert animation["minDurationSeconds"] == 30
    assert animation["maxDurationSeconds"] == 60
    assert animation["timeoutSeconds"] == 600
    assert animation["durationBounds"] == {"min": 15, "max": 180}


def test_update_animation_settings_persists_and_rejects_bad_values(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    responses = _settings_rpc(
        vault_root,
        ("update_animation_settings", {"quality": "qh", "maxDurationSeconds": 90, "timeoutSeconds": 900}),
        ("update_animation_settings", {"quality": "4k"}),
        ("update_animation_settings", {"maxDurationSeconds": 10}),
        ("update_animation_settings", {"timeoutSeconds": 5}),
    )
    result = responses[0]["result"]["animation"]
    assert result["quality"] == "qh"
    assert result["maxDurationSeconds"] == 90
    assert result["timeoutSeconds"] == 900
    assert [response["error"]["data"]["code"] for response in responses[1:]] == [
        "invalid_quality",
        "invalid_duration",
        "invalid_timeout",
    ]

    config = load_config(vault_root / "learnloop.toml")
    assert config.animation.quality == "qh"
    assert config.animation.max_duration_seconds == 90
    assert config.animation.timeout_seconds == 900
    # The edit lands in the existing [animation] table (comment-preserving writer).
    assert (vault_root / "learnloop.toml").read_text().count("[animation]") == 1


def test_update_ai_settings_materializes_openrouter_video_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    responses = _settings_rpc(
        vault_root,
        ("update_ai_settings", {"useCases": {"video": {"provider": "codex"}}}),
        ("update_ai_settings", {"useCases": {"video": {"provider": "openrouter", "openrouterModel": "veo"}}}),
        (
            "update_ai_settings",
            {"useCases": {"video": {"provider": "openrouter", "openrouterModel": "google/veo-3.1"}}},
        ),
        ("update_animation_settings", {"renderer": "video_model", "videoMaxShots": 3}),
        ("update_animation_settings", {"renderer": "hologram"}),
        ("update_animation_settings", {"videoMaxShots": 9}),
    )
    assert responses[0]["error"]["data"]["code"] == "invalid_provider"
    assert responses[1]["error"]["data"]["code"] == "invalid_model"
    routed = responses[2]["result"]
    assert routed["ai"]["routing"]["videoGeneration"] == "openrouter_video"
    animation = responses[3]["result"]["animation"]
    assert animation["renderer"] == "video_model"
    assert animation["video"]["ready"] is True
    assert animation["video"]["provider"] == "openrouter_video"
    assert animation["video"]["model"] == "google/veo-3.1"
    assert animation["video"]["maxShots"] == 3
    assert responses[4]["error"]["data"]["code"] == "invalid_renderer"
    assert responses[5]["error"]["data"]["code"] == "invalid_shot_count"

    config = load_config(vault_root / "learnloop.toml")
    assert config.ai.providers["openrouter_video"].model == "google/veo-3.1"
    assert config.ai.providers["openrouter_video"].type == "openrouter"
    assert config.animation.renderer == "video_model"
    assert config.animation.video_max_shots == 3


# ---------------------------------------------------------------------------
# Native media ingestion: per-modality readiness, capability detection
# ---------------------------------------------------------------------------

_CATALOG_PAYLOAD = {
    "data": [
        {
            "id": "google/gemini-2.5-pro",
            "architecture": {"input_modalities": ["text", "image", "file", "audio"]},
        },
        {"id": "text-only/model", "architecture": {"input_modalities": ["text"]}},
    ]
}


def _seed_catalog(monkeypatch, payload=_CATALOG_PAYLOAD, *, fail=False):
    from learnloop.ai.providers import openrouter_catalog as catalog

    def fake_fetch(timeout):
        if fail:
            raise OSError("offline")
        return payload

    monkeypatch.setattr(catalog, "_fetch_models_payload", fake_fetch)
    return catalog


def _route_ingest_to_openrouter(vault_root, model="google/gemini-2.5-pro", modalities=None):
    from learnloop.ops.settings_store import apply_config_updates

    updates = {
        ("ai", "routing", "canonical_ingest"): "openrouter",
        ("ai", "providers", "openrouter", "model"): model,
    }
    if modalities is not None:
        updates[("ai", "providers", "openrouter", "input_modalities")] = list(modalities)
    apply_config_updates(vault_root / "learnloop.toml", updates)


def test_get_settings_reports_native_modality_readiness(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    settings = _settings_rpc(vault_root, ("get_settings", {}))[0]["result"]

    ingest = settings["ingest"]
    assert ingest["pdfEngine"] == "auto"
    assert ingest["audioMode"] == "transcription"
    native = ingest["native"]
    assert [entry["modality"] for entry in native["modalities"]] == ["pdf", "audio"]
    # A Codex-routed ingest route cannot take media natively; the UI gets the reason.
    for entry in native["modalities"]:
        assert entry["requested"] is False
        assert entry["ready"] is False
        assert entry["reason"] == "provider_not_chat"
        assert entry["providerName"] == "codex_medium"
    assert native["fallbackWhenUnavailable"] is False
    assert native["maxPdfMb"] == 32 and native["maxAudioMb"] == 20
    assert native["knownModalities"] == ["audio", "pdf", "image", "video"]
    assert native["catalog"]["cached"] is False
    by_name = {provider["name"]: provider for provider in settings["ai"]["providers"]}
    assert by_name["openrouter"]["inputModalities"] == []


def test_update_ingest_settings_sets_per_modality_authorities(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    responses = _settings_rpc(
        vault_root,
        (
            "update_ingest_settings",
            {
                "pdfEngine": "native",
                "audioMode": "native",
                "nativeFallbackWhenUnavailable": True,
                "nativeMaxPdfMb": 10,
            },
        ),
        ("update_ingest_settings", {"nativeMaxAudioMb": 0}),
    )
    result = responses[0]["result"]
    assert result["ingest"]["pdfEngine"] == "native"
    assert result["ingest"]["audioMode"] == "native"
    assert result["ingest"]["native"]["fallbackWhenUnavailable"] is True
    assert result["ingest"]["native"]["maxPdfMb"] == 10
    pdf_state = next(e for e in result["ingest"]["native"]["modalities"] if e["modality"] == "pdf")
    assert pdf_state["requested"] is True and pdf_state["ready"] is False
    assert responses[1]["error"]["data"]["code"] == "invalid_native_limit"

    config = load_config(vault_root / "learnloop.toml")
    assert config.ingest.pdf.engine == "native"
    assert config.ingest.audio.mode == "native"
    assert config.ingest.native.fallback_when_unavailable is True
    assert config.ingest.native.max_pdf_mb == 10
    assert config.ingest.native.max_audio_mb == 20


def test_update_ingest_settings_native_adopts_cached_catalog_modalities(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    _route_ingest_to_openrouter(vault_root)
    catalog = _seed_catalog(monkeypatch)
    catalog.load_catalog()  # populate the on-disk cache
    _seed_catalog(monkeypatch, fail=True)  # the save path must stay cache-only

    result = _settings_rpc(vault_root, ("update_ingest_settings", {"pdfEngine": "native"}))[0]["result"]

    pdf_state = next(e for e in result["ingest"]["native"]["modalities"] if e["modality"] == "pdf")
    assert pdf_state["ready"] is True
    assert pdf_state["providerName"] == "openrouter"
    assert pdf_state["model"] == "google/gemini-2.5-pro"
    config = load_config(vault_root / "learnloop.toml")
    assert config.ai.providers["openrouter"].input_modalities == ["audio", "pdf", "image"]


def test_detect_provider_capabilities_network_cache_and_unavailable(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    _route_ingest_to_openrouter(vault_root)
    _seed_catalog(monkeypatch)

    first = _settings_rpc(vault_root, ("detect_provider_capabilities", {"provider": "openrouter"}))[0]["result"]
    assert first["source"] == "network"
    assert first["modelKnown"] is True
    assert first["detected"] == ["audio", "pdf", "image"]
    assert first["declared"] == []
    assert "accepts audio, pdf, image" in first["message"]
    # Detection proposes; nothing is written until the learner applies it.
    assert load_config(vault_root / "learnloop.toml").ai.providers["openrouter"].input_modalities == []

    _seed_catalog(monkeypatch, fail=True)
    responses = _settings_rpc(
        vault_root,
        ("detect_provider_capabilities", {"provider": "openrouter", "refresh": True}),
        ("detect_provider_capabilities", {"provider": "codex"}),
        ("detect_provider_capabilities", {"provider": "ghost"}),
    )
    cached = responses[0]["result"]
    assert cached["source"] == "cache" and cached["stale"] is True
    assert cached["detected"] == ["audio", "pdf", "image"]
    assert responses[1]["error"]["data"]["code"] == "unsupported_provider_type"
    assert responses[2]["error"]["data"]["code"] == "invalid_provider"


def test_detect_provider_capabilities_without_any_catalog_is_a_result(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    _seed_catalog(monkeypatch, fail=True)

    result = _settings_rpc(vault_root, ("detect_provider_capabilities", {"provider": "openrouter"}))[0]["result"]
    assert result["source"] == "unavailable"
    assert result["detected"] is None and result["modelKnown"] is False
    assert "catalog" in result["message"]


def test_update_provider_modalities_validates_and_persists(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    _route_ingest_to_openrouter(vault_root)

    responses = _settings_rpc(
        vault_root,
        ("update_provider_modalities", {"provider": "openrouter", "inputModalities": ["pdf", "bogus"]}),
        ("update_provider_modalities", {"provider": "codex", "inputModalities": ["pdf"]}),
        ("update_provider_modalities", {"provider": "openrouter", "inputModalities": ["Pdf", "audio", "pdf"]}),
        ("update_ingest_settings", {"pdfEngine": "native"}),
    )
    assert responses[0]["error"]["data"]["code"] == "invalid_modality"
    assert responses[1]["error"]["data"]["code"] == "unsupported_provider_type"
    applied = responses[2]["result"]
    by_name = {provider["name"]: provider for provider in applied["ai"]["providers"]}
    assert by_name["openrouter"]["inputModalities"] == ["audio", "pdf"]
    assert load_config(vault_root / "learnloop.toml").ai.providers["openrouter"].input_modalities == ["audio", "pdf"]
    pdf_state = next(e for e in responses[3]["result"]["ingest"]["native"]["modalities"] if e["modality"] == "pdf")
    assert pdf_state["ready"] is True


def test_update_ai_settings_openrouter_ingest_profile_uses_cached_catalog(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    catalog = _seed_catalog(monkeypatch)
    catalog.load_catalog()

    _settings_rpc(
        vault_root,
        (
            "update_ai_settings",
            {"useCases": {"ingest": {"provider": "openrouter", "openrouterModel": "text-only/model"}}},
        ),
    )

    profile = load_config(vault_root / "learnloop.toml").ai.providers["openrouter_ingest"]
    assert profile.model == "text-only/model"
    # The base profile's declaration is not copied onto a model the catalog knows takes text only.
    assert profile.input_modalities == []


def test_start_import_batch_fails_fast_for_native_pdf_conflicts(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    pdf_path = tmp_path / "chapter.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    responses = _settings_rpc(
        vault_root,
        ("start_import_batch", {"sources": [str(pdf_path)], "pdfEngine": "native"}),
        (
            "start_import_batch",
            {"sources": [str(pdf_path)], "pdfEngine": "native", "pageStart": 1, "pageEnd": 3},
        ),
        ("start_ingest", {"source": str(pdf_path), "subjectId": "linear-algebra", "pdfEngine": "native"}),
    )
    unready = responses[0]["error"]["data"]
    assert unready["code"] == "native_pdf_unavailable"
    assert unready["details"]["reason"] == "provider_not_chat"
    assert responses[1]["error"]["data"]["code"] == "invalid_page_range"
    assert responses[2]["error"]["data"]["code"] == "native_pdf_unavailable"

    # With the fallback opted in, an unready route takes the local road, which
    # honours page ranges: the preflight must not refuse what the job accepts.
    from learnloop.ops.settings_store import apply_config_updates

    apply_config_updates(vault_root / "learnloop.toml", {("ingest", "native", "fallback_when_unavailable"): True})
    accepted = _settings_rpc(
        vault_root,
        (
            "start_import_batch",
            {"sources": [str(pdf_path)], "pdfEngine": "native", "pageStart": 1, "pageEnd": 3},
        ),
    )[0]
    assert "error" not in accepted, accepted


def test_update_provider_modalities_materializes_a_compat_derived_profile(tmp_path, monkeypatch):
    """The legacy [ingest.audio] provider shape synthesises openrouter_transcription in
    memory only; declaring a modality on it must write the whole profile, not a bare
    table that reloads as the pydantic default."""

    from learnloop.ops.settings_store import apply_config_updates

    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    apply_config_updates(
        vault_root / "learnloop.toml",
        {
            ("ingest", "audio", "provider"): "openrouter",
            ("ingest", "audio", "transcription_model"): "google/gemini-2.5-flash",
        },
    )
    before = load_config(vault_root / "learnloop.toml").ai.providers["openrouter_transcription"]
    assert before.type == "openrouter" and before.model == "google/gemini-2.5-flash"

    result = _settings_rpc(
        vault_root,
        ("update_provider_modalities", {"provider": "openrouter_transcription", "inputModalities": ["audio"]}),
    )[0]["result"]

    after = load_config(vault_root / "learnloop.toml").ai.providers["openrouter_transcription"]
    assert after.type == "openrouter"
    assert after.model == "google/gemini-2.5-flash"
    assert after.input_modalities == ["audio"]
    row = next(p for p in result["ai"]["providers"] if p["name"] == "openrouter_transcription")
    assert row["inputModalities"] == ["audio"]


def test_detect_provider_capabilities_without_a_model_skips_the_network(tmp_path, monkeypatch):
    from learnloop.ops.settings_store import apply_config_updates

    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    apply_config_updates(
        vault_root / "learnloop.toml",
        {("ai", "providers", "openrouter", "type"): "openrouter", ("ai", "providers", "openrouter", "model"): ""},
    )
    catalog = _seed_catalog(monkeypatch, fail=True)  # any fetch would raise

    result = _settings_rpc(vault_root, ("detect_provider_capabilities", {"provider": "openrouter"}))[0]["result"]

    assert result["source"] == "unavailable"
    assert "no model slug" in result["message"]
    assert not catalog.catalog_cache_path().exists()
