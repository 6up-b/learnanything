from __future__ import annotations

import pytest

from learnloop.config import load_config
from learnloop.services.settings_store import (
    SettingsStoreError,
    apply_config_updates,
    copy_ai_settings,
    openrouter_profile_name,
    openrouter_task_profile_values,
    upsert_env_var,
)
from learnloop.vault.loader import init_vault


def _config_path(root):
    init_vault(root)
    return root / "learnloop.toml"


def _configure_openrouter_ingest(config_path, model="anthropic/claude-sonnet-4.5"):
    base = load_config(config_path).ai.providers["openrouter"]
    name = openrouter_profile_name("ingest")
    updates = {
        ("ai", "providers", name, key): value
        for key, value in openrouter_task_profile_values(base, model).items()
    }
    updates.update(
        {
            ("ai", "routing", task): name
            for task in ("canonical_ingest", "canonical_ingest_retry", "authoring")
        }
    )
    apply_config_updates(config_path, updates)
    return name


def test_apply_config_updates_preserves_comments_and_unrelated_values(tmp_path):
    path = _config_path(tmp_path)
    before = path.read_text(encoding="utf-8")
    assert 'active_provider = "codex"' in before
    assert "# Per-machine" in before

    apply_config_updates(path, {("ai", "active_provider"): "openrouter"})

    after = path.read_text(encoding="utf-8")
    assert 'active_provider = "openrouter"' in after
    assert "# Per-machine" in after
    assert 'fallback_provider = ""' in after
    assert load_config(path).ai.active_provider == "openrouter"


def test_apply_config_updates_creates_task_profile_and_route(tmp_path):
    path = _config_path(tmp_path)

    apply_config_updates(
        path,
        {
            ("ai", "providers", "openrouter_grading", "type"): "openrouter",
            ("ai", "providers", "openrouter_grading", "model"): "openai/gpt-5-mini",
            ("ai", "routing", "grading"): "openrouter_grading",
        },
    )

    config = load_config(path)
    assert config.ai.routing.grading == "openrouter_grading"
    assert config.ai.providers["openrouter_grading"].model == "openai/gpt-5-mini"


def test_openrouter_profile_values_only_emit_configured_fields(tmp_path):
    path = _config_path(tmp_path)
    base = load_config(path).ai.providers["openrouter"]

    values = openrouter_task_profile_values(base, "anthropic/claude-sonnet-4.5")

    assert values["type"] == "openrouter"
    assert values["model"] == "anthropic/claude-sonnet-4.5"
    assert values["api_key_env"] == "OPENROUTER_API_KEY"
    assert "max_tokens" not in values


def test_apply_config_updates_does_not_touch_invalid_toml(tmp_path):
    path = tmp_path / "learnloop.toml"
    path.write_text("[ai\nbroken", encoding="utf-8")

    with pytest.raises(SettingsStoreError) as exc_info:
        apply_config_updates(path, {("ai", "active_provider"): "openrouter"})

    assert exc_info.value.code == "config_unreadable"
    assert path.read_text(encoding="utf-8") == "[ai\nbroken"
    assert not path.with_suffix(".toml.tmp").exists()


def test_copy_ai_settings_copies_routes_and_materialized_profiles(tmp_path):
    source = _config_path(tmp_path / "source")
    target = _config_path(tmp_path / "target")
    profile_name = _configure_openrouter_ingest(source)

    assert copy_ai_settings(source, target) is True

    config = load_config(target)
    assert config.ai.routing.canonical_ingest == profile_name
    assert config.ai.routing.canonical_ingest_retry == profile_name
    assert config.ai.routing.authoring == profile_name
    assert config.ai.providers[profile_name].model == "anthropic/claude-sonnet-4.5"
    assert config.ai.routing.grading == "codex_low"


def test_copy_ai_settings_rejects_missing_or_invalid_source(tmp_path):
    target = _config_path(tmp_path / "target")

    with pytest.raises(SettingsStoreError) as missing:
        copy_ai_settings(tmp_path / "missing.toml", target)
    assert missing.value.code == "config_missing"

    invalid = tmp_path / "invalid.toml"
    invalid.write_text("[ai\nbroken", encoding="utf-8")
    with pytest.raises(SettingsStoreError) as unreadable:
        copy_ai_settings(invalid, target)
    assert unreadable.value.code == "config_unreadable"


def test_upsert_env_var_preserves_other_lines_and_replaces_target(tmp_path):
    path = tmp_path / "settings.env"
    path.write_text(
        "# machine secrets\nexport DEEPSEEK_API_KEY=old\nUNRELATED=keep me\n",
        encoding="utf-8",
    )

    upsert_env_var(path, "OPENROUTER_API_KEY", "or-first")
    upsert_env_var(path, "DEEPSEEK_API_KEY", "new")

    text = path.read_text(encoding="utf-8")
    assert "# machine secrets" in text
    assert "UNRELATED=keep me" in text
    assert "OPENROUTER_API_KEY=or-first" in text
    assert "DEEPSEEK_API_KEY=new" in text
    assert "old" not in text


def test_upsert_env_var_removes_key_and_rejects_unsafe_input(tmp_path):
    path = tmp_path / "global" / "settings.env"
    upsert_env_var(path, "OPENROUTER_API_KEY", "value")
    upsert_env_var(path, "OPENROUTER_API_KEY", None)
    assert "OPENROUTER_API_KEY" not in path.read_text(encoding="utf-8")

    with pytest.raises(SettingsStoreError) as bad_name:
        upsert_env_var(path, "BAD KEY", "x")
    assert bad_name.value.code == "invalid_env_key"

    with pytest.raises(SettingsStoreError) as bad_value:
        upsert_env_var(path, "OPENROUTER_API_KEY", "a\nb")
    assert bad_value.value.code == "invalid_env_value"
