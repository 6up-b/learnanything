from __future__ import annotations

import os

from learnloop.ai.runtime import check_ai_runtime
from learnloop.config import LearnLoopConfig, load_config


def test_openai_chat_runtime_requires_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    config = _deepseek_config()

    report = check_ai_runtime(tmp_path, config)

    assert report.status == "provider_auth_required"
    assert report.ready is False
    assert report.active_provider == "deepseek_flash"
    assert report.provider_type == "openai_chat"


def test_openai_chat_runtime_ready_with_api_key(tmp_path, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    config = _deepseek_config()

    report = check_ai_runtime(tmp_path, config)

    assert report.status == "ready"
    assert report.ready is True
    assert report.model == "deepseek-v4-flash"


def test_openai_chat_runtime_uses_vault_dotenv(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    _write_deepseek_vault_config(tmp_path)
    (tmp_path / ".env").write_text("DEEPSEEK_API_KEY=dotenv-key\n", encoding="utf-8")

    config = load_config(tmp_path / "learnloop.toml")
    report = check_ai_runtime(tmp_path, config)

    assert report.status == "ready"
    assert report.ready is True


def test_vault_dotenv_does_not_override_shell_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "shell-key")
    _write_deepseek_vault_config(tmp_path)
    (tmp_path / ".env").write_text("DEEPSEEK_API_KEY=dotenv-key\n", encoding="utf-8")

    load_config(tmp_path / "learnloop.toml")

    assert os.environ["DEEPSEEK_API_KEY"] == "shell-key"


def test_ai_runtime_reports_missing_provider(tmp_path):
    report = check_ai_runtime(tmp_path, LearnLoopConfig(), provider_name="missing")

    assert report.status == "provider_missing_config"
    assert report.ready is False


def test_openrouter_runtime_requires_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    report = check_ai_runtime(tmp_path, LearnLoopConfig(), provider_name="openrouter")

    assert report.status == "provider_auth_required"
    assert report.ready is False
    assert report.provider_type == "openrouter"
    assert "OPENROUTER_API_KEY" in (report.message or "")


def test_openrouter_runtime_ready_with_api_key(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    report = check_ai_runtime(tmp_path, LearnLoopConfig(), provider_name="openrouter")

    assert report.status == "ready"
    assert report.ready is True
    assert report.model == "deepseek/deepseek-chat"


def test_openrouter_runtime_defaults_to_openrouter_key_env(tmp_path, monkeypatch):
    # A profile that omits api_key_env must resolve OPENROUTER_API_KEY, not the
    # generic OPENAI_API_KEY fallback used by the openai_chat type.
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "other-key")
    config = LearnLoopConfig.model_validate(
        {
            "ai": {
                "active_provider": "openrouter",
                "providers": {"openrouter": {"type": "openrouter", "model": "deepseek/deepseek-chat"}},
            }
        }
    )

    report = check_ai_runtime(tmp_path, config)

    assert report.status == "provider_auth_required"
    assert "OPENROUTER_API_KEY" in (report.message or "")


def _deepseek_config() -> LearnLoopConfig:
    return LearnLoopConfig.model_validate(
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
                    }
                },
            }
        }
    )


def _write_deepseek_vault_config(tmp_path) -> None:
    (tmp_path / "learnloop.toml").write_text(
        """
schema_version = 1

[ai]
active_provider = "deepseek_flash"

[ai.providers.deepseek_flash]
type = "openai_chat"
base_url = "https://api.deepseek.com"
api_key_env = "DEEPSEEK_API_KEY"
model = "deepseek-v4-flash"
response_format = "json_object"
thinking = "disabled"
""",
        encoding="utf-8",
    )
