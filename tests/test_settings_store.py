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


def _config_path(tmp_path):
    init_vault(tmp_path)
    return tmp_path / "learnloop.toml"


def test_apply_config_updates_preserves_comments_and_unrelated_lines(tmp_path):
    path = _config_path(tmp_path)
    before = path.read_text(encoding="utf-8")
    assert 'active_provider = "codex"' in before

    apply_config_updates(path, {("ai", "active_provider"): "openrouter"})

    after = path.read_text(encoding="utf-8")
    assert 'active_provider = "openrouter"' in after
    # A known template comment survives, and the untouched neighbouring keys do too.
    assert "# Any OpenRouter model slug works" in after
    assert 'fallback_provider = ""' in after
    config = load_config(path)
    assert config.ai.active_provider == "openrouter"


def test_apply_config_updates_creates_missing_tables(tmp_path):
    path = _config_path(tmp_path)

    apply_config_updates(
        path,
        {
            ("ai", "providers", "openrouter_grading", "type"): "openrouter",
            ("ai", "providers", "openrouter_grading", "model"): "anthropic/claude-sonnet-4.5",
            ("ai", "routing", "grading"): "openrouter_grading",
        },
    )

    config = load_config(path)
    profile = config.ai.providers["openrouter_grading"]
    assert profile.type == "openrouter"
    assert profile.model == "anthropic/claude-sonnet-4.5"
    assert config.ai.routing.grading == "openrouter_grading"


def test_openrouter_task_profile_values_round_trip(tmp_path):
    path = _config_path(tmp_path)
    base = load_config(path).ai.providers["openrouter"]
    name = openrouter_profile_name("grading")
    values = openrouter_task_profile_values(base, "openai/gpt-5-mini")

    apply_config_updates(
        path, {("ai", "providers", name, key): value for key, value in values.items()}
    )

    profile = load_config(path).ai.providers[name]
    assert profile.type == "openrouter"
    assert profile.model == "openai/gpt-5-mini"
    assert profile.api_key_env == "OPENROUTER_API_KEY"
    assert profile.response_format == "json_object"
    # Unset base keys are never dumped into the TOML.
    assert "max_tokens" not in path.read_text(encoding="utf-8").split(f"[ai.providers.{name}]", 1)[1].split("[", 1)[0]


def test_apply_config_updates_is_atomic_on_parse_failure(tmp_path):
    path = tmp_path / "learnloop.toml"
    path.write_text("[ai\nbroken", encoding="utf-8")

    with pytest.raises(SettingsStoreError) as excinfo:
        apply_config_updates(path, {("ai", "active_provider"): "openrouter"})

    assert excinfo.value.code == "config_unreadable"
    assert path.read_text(encoding="utf-8") == "[ai\nbroken"
    assert not (tmp_path / "learnloop.toml.tmp").exists()


def test_apply_config_updates_missing_file(tmp_path):
    with pytest.raises(SettingsStoreError) as excinfo:
        apply_config_updates(tmp_path / "absent.toml", {("ai", "active_provider"): "x"})
    assert excinfo.value.code == "config_missing"


def _configure_openrouter_ingest(config_path, model="anthropic/claude-sonnet-4.5"):
    """Persist what update_ai_settings writes for the ingest use-case."""

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


def test_copy_ai_settings_copies_routing_and_materialized_profiles(tmp_path):
    source_path = _config_path(tmp_path / "source")
    target_path = _config_path(tmp_path / "target")
    name = _configure_openrouter_ingest(source_path)

    assert copy_ai_settings(source_path, target_path) is True

    config = load_config(target_path)
    assert config.ai.routing.canonical_ingest == name
    assert config.ai.routing.canonical_ingest_retry == name
    assert config.ai.routing.authoring == name
    assert config.ai.providers[name].model == "anthropic/claude-sonnet-4.5"
    assert config.ai.providers[name].api_key_env == "OPENROUTER_API_KEY"
    # Unconfigured use-cases keep the template defaults, template comments
    # survive, and the codex tables are untouched.
    text = target_path.read_text(encoding="utf-8")
    assert config.ai.routing.grading == "codex_low"
    assert "# Any OpenRouter model slug works" in text
    assert 'checkout_path = ""' in text


def test_copy_ai_settings_default_source_is_semantic_noop(tmp_path):
    source_path = _config_path(tmp_path / "source")
    target_path = _config_path(tmp_path / "target")

    copy_ai_settings(source_path, target_path)

    config = load_config(target_path)
    assert config.ai.active_provider == "codex"
    assert config.ai.routing.canonical_ingest == "codex_medium"
    assert config.ai.routing.grading == "codex_low"


def test_copy_ai_settings_errors_on_missing_or_invalid_source(tmp_path):
    target_path = _config_path(tmp_path / "target")

    with pytest.raises(SettingsStoreError) as excinfo:
        copy_ai_settings(tmp_path / "absent.toml", target_path)
    assert excinfo.value.code == "config_missing"

    bad = tmp_path / "bad.toml"
    bad.write_text("[ai\nbroken", encoding="utf-8")
    with pytest.raises(SettingsStoreError) as excinfo:
        copy_ai_settings(bad, target_path)
    assert excinfo.value.code == "config_unreadable"
    # The failed copies never touched the target.
    assert load_config(target_path).ai.routing.canonical_ingest == "codex_medium"


def test_upsert_env_var_appends_and_replaces_preserving_other_lines(tmp_path):
    path = tmp_path / "settings.env"
    path.write_text(
        "# machine secrets\nexport DEEPSEEK_API_KEY=old-deepseek\nUNRELATED=keep me\n",
        encoding="utf-8",
    )

    upsert_env_var(path, "OPENROUTER_API_KEY", "or-first")
    text = path.read_text(encoding="utf-8")
    assert "# machine secrets" in text
    assert "export DEEPSEEK_API_KEY=old-deepseek" in text
    assert "UNRELATED=keep me" in text
    assert "OPENROUTER_API_KEY=or-first" in text

    # Replacing an export-prefixed key rewrites just that line.
    upsert_env_var(path, "DEEPSEEK_API_KEY", "new-deepseek")
    text = path.read_text(encoding="utf-8")
    assert "DEEPSEEK_API_KEY=new-deepseek" in text
    assert "old-deepseek" not in text
    assert "OPENROUTER_API_KEY=or-first" in text


def test_upsert_env_var_removes_key_on_none_and_creates_parents(tmp_path):
    path = tmp_path / "config" / "learnloop" / "settings.env"

    upsert_env_var(path, "OPENROUTER_API_KEY", "value")
    assert path.read_text(encoding="utf-8") == "OPENROUTER_API_KEY=value\n"

    upsert_env_var(path, "OPENROUTER_API_KEY", None)
    assert "OPENROUTER_API_KEY" not in path.read_text(encoding="utf-8")

    # Removing from a file that never had the key is a no-op, not an error.
    upsert_env_var(path, "NEVER_SET", None)


def test_upsert_env_var_rejects_bad_names_and_newlines(tmp_path):
    path = tmp_path / "settings.env"
    with pytest.raises(SettingsStoreError) as excinfo:
        upsert_env_var(path, "BAD KEY", "x")
    assert excinfo.value.code == "invalid_env_key"

    with pytest.raises(SettingsStoreError) as excinfo:
        upsert_env_var(path, "OPENROUTER_API_KEY", "a\nb")
    assert excinfo.value.code == "invalid_env_value"
    assert not path.exists()
