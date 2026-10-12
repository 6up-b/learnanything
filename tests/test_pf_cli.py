"""`learnloop pf` commands, PF routes and configuration (Slice A §5 rule 6, Slice 2 §5.8)."""
from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.ai.routing import LIST_ROUTE_TASKS, provider_for_task, provider_list_for_task
from learnloop.cli import app
from learnloop.config.schema import LearnLoopConfig
from learnloop.config.template import DEFAULT_CONFIG_TEXT
from learnloop.ops.pf_calls import planned_role_clients, role_providers
from learnloop.vault.loader import load_vault
from tests.helpers import append_config_toml
from tests.pf_fakes import seed_pf_vault


def test_template_keeps_generation_off_and_caps_publication():
    config = LearnLoopConfig.model_validate(__import__("tomllib").loads(DEFAULT_CONFIG_TEXT))
    assert config.pf.generation_enabled is False
    assert config.pf.max_published_per_day == 10
    assert "generation_enabled = false" in DEFAULT_CONFIG_TEXT
    assert config.ai.routing.pf_proposers == [] and config.ai.routing.pf_selection_judge is None


def test_list_routes_resolve_in_order_and_fall_back_to_the_active_provider(tmp_path, monkeypatch):
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    _, _, paths = seed_pf_vault(tmp_path / "vault")
    config = load_vault(paths.root).config
    assert [s.provider_name for s in provider_list_for_task(config, "pf_proposers")] == [config.ai.active_provider]
    append_config_toml(paths.root, """
        [ai.providers.or_a]
        type = "openrouter"
        model = "vendor/model-a"
        [ai.providers.or_b]
        type = "openrouter"
        model = "vendor/model-b"
    """)
    text = (paths.root / "learnloop.toml").read_text()
    text = text.replace('field_question_classifier = ""',
                        'field_question_classifier = ""\npf_proposers = ["or_a", "or_b", "or_a"]\n'
                        'pf_solver_panel = ["codex", "or_b"]\npf_selection_judge = "or_a"')
    (paths.root / "learnloop.toml").write_text(text)
    vault = load_vault(paths.root)
    config = vault.config
    assert [s.provider_name for s in provider_list_for_task(config, "pf_proposers")] == ["or_a", "or_b"]
    assert all(s.explicit for s in provider_list_for_task(config, "pf_proposers"))
    assert provider_for_task(config, "pf_solver_panel").provider_name == "codex"
    assert provider_for_task(config, "pf_selection_judge").provider_name == "or_a"
    assert LIST_ROUTE_TASKS == {"pf_proposers", "pf_solver_panel"}
    planned = planned_role_clients(vault, "proposer")
    assert [client.model for client in planned] == ["vendor/model-a", "vendor/model-b"]
    assert not any(client.subscription for client in planned)
    assert planned_role_clients(vault, "panel")[0].subscription  # Codex panel member
    monkeypatch.setenv("LEARNLOOP_AI_PROVIDER", "or_b")
    assert [s.provider_name for s in provider_list_for_task(config, "pf_proposers")] == ["or_b"]
    assert role_providers(vault, "selection", tier_routes=["codex", "or_a"]) == ["codex"]
    assert role_providers(vault, "proposer", tier_routes=["codex", "or_a"]) == ["codex", "or_a"]
    # The verifiers stay fixed across scaling tiers.
    assert role_providers(vault, "panel", tier_routes=["codex"]) == ["or_b"]


def test_sidecar_settings_show_a_panel_list_as_text():
    from learnloop_sidecar.handlers.settings import _route_display

    assert _route_display(None) is None and _route_display("codex") == "codex"
    assert _route_display(["codex_low", "or_b"]) == "codex_low, or_b"


def test_cli_generate_dry_run_is_json_and_read_only(tmp_path):
    _, _, paths = seed_pf_vault(tmp_path / "vault")
    before = paths.sqlite_path.read_bytes()
    result = CliRunner().invoke(app, ["pf", "generate", "--vault", str(paths.root), "--dry-run", "--json",
                                      "--path", "generator", "--price-per-million", "2"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.stdout)
    assert report["status"] == "dry_run"
    assert report["plan"][0]["path"] == "generator"
    assert report["estimate"]["subscription"]["calls"] > 0  # the template routes Codex
    assert paths.sqlite_path.read_bytes() == before


def test_cli_generate_refuses_when_disabled_and_rejects_bad_input(tmp_path):
    _, _, paths = seed_pf_vault(tmp_path / "vault", enabled=False)
    disabled = CliRunner().invoke(app, ["pf", "generate", "--vault", str(paths.root), "--json"])
    assert disabled.exit_code == 1 and json.loads(disabled.stdout)["status"] == "disabled"
    bad = CliRunner().invoke(app, ["pf", "generate", "--vault", str(paths.root), "--json", "--path", "magic"])
    assert bad.exit_code == 1 and json.loads(bad.stdout)["status"] == "invalid"
    status = CliRunner().invoke(app, ["pf", "status", "--vault", str(paths.root), "--json"])
    assert status.exit_code == 0
    assert json.loads(status.stdout)["generation_enabled"] is False
    publish = CliRunner().invoke(app, ["pf", "publish", "--vault", str(paths.root), "--json"])
    assert publish.exit_code == 1 and json.loads(publish.stdout)["status"] == "disabled"
