"""F1 config cannot activate a challenger or read evaluation-machine secrets."""
import pytest
from pydantic import ValidationError

from learnloop.ai.routing import provider_for_task
from learnloop.config.loader import load_config
from learnloop.config.schema import LearnLoopConfig
from learnloop.config.template import write_default_config
from learnloop.vault.loader import load_vault
from tests.helpers import create_basic_vault


def test_field_defaults_are_offline_and_incumbent_only():
    config = LearnLoopConfig()
    assert config.field.active_predictor == "mastery_ekf"
    assert config.field.legacy_fallback == "exclude"
    assert not config.field.question_classification_enabled
    assert not config.field.llm_probability_enabled
    for challenger in ("lo_general", "llm_probability", "base_rate_lo"):
        with pytest.raises(ValidationError):
            LearnLoopConfig.model_validate({"field": {"active_predictor": challenger}})


@pytest.mark.parametrize("task", ["field_question_classifier"])
def test_field_paid_routes_are_explicit_not_global(task, monkeypatch):
    config = LearnLoopConfig()
    monkeypatch.setenv("LEARNLOOP_AI_PROVIDER", "unrelated-provider")
    selection = provider_for_task(config, task)
    assert selection.provider_name == ""
    assert selection.explicit
    setattr(config.ai.routing, task, "offline-experiment")
    assert provider_for_task(config, task).provider_name == "offline-experiment"


def test_offline_config_never_opens_dotenv_or_global_settings(tmp_path, monkeypatch):
    path = tmp_path / "learnloop.toml"
    write_default_config(path)

    def forbidden(*args, **kwargs):
        raise AssertionError("Offline evaluation must not load machine secrets")

    monkeypatch.setattr("learnloop.config.loader.load_dotenv", forbidden)
    monkeypatch.setattr("learnloop.config.loader.global_settings_path", forbidden)
    monkeypatch.setattr("learnloop.config.loader._apply_global_overrides", forbidden)
    assert load_config(path, load_environment=False).field.active_predictor == "mastery_ekf"


def test_offline_vault_load_uses_only_explicit_vault_config(tmp_path, monkeypatch):
    paths = create_basic_vault(tmp_path)

    def forbidden(*args, **kwargs):
        raise AssertionError("Offline evaluation must not load machine secrets")

    monkeypatch.setattr("learnloop.config.loader.load_dotenv", forbidden)
    assert load_vault(paths.root, load_environment=False).config.field.legacy_fallback == "exclude"


def test_retired_numeric_probability_route_loads_with_a_deprecation_note(tmp_path):
    """Owner decision 2026-10-12: ai.routing.field_llm_probability is retired.

    An old vault that still sets it loads (the value is ignored) and doctor
    reports a warning, never an error.
    """
    from learnloop.ai.routing import ROUTE_FOR_OPERATION
    from learnloop.config.schema import AIRoutingConfig
    from learnloop.ops.doctor import run_doctor

    paths = create_basic_vault(tmp_path)
    toml = paths.root / "learnloop.toml"
    assert "field_llm_probability" not in toml.read_text(encoding="utf-8")
    text = toml.read_text(encoding="utf-8").replace(
        'field_question_classifier = ""',
        'field_question_classifier = ""\nfield_llm_probability = "openrouter"', 1,
    )
    toml.write_text(text, encoding="utf-8")
    config = load_vault(paths.root, load_environment=False).config
    assert "field_llm_probability" not in AIRoutingConfig.model_fields
    assert "field_llm_probability" not in config.ai.routing.model_dump()
    assert "field_llm_probability" not in ROUTE_FOR_OPERATION
    report = run_doctor(paths.root)
    retired = [issue for issue in report.issues if issue.code == "config:retired_route"]
    assert len(retired) == 1 and retired[0].severity == "warning"
    assert "field_llm_probability" in retired[0].message
    assert "llm_probability_llm" in retired[0].message
