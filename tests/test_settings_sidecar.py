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
    assert sorted(settings["ai"]["useCases"]) == ["animation", "grading", "ingest", "tutor"]
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
