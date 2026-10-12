"""`learnloop eval --probability-arm` and `learnloop eval judges`, offline.

Dry runs and cache loads never read machine secrets or build a client; the
readiness command never touches the network unless asked; the live check is
one spend-capped call to a fake endpoint.
"""
from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from tests.decider_fakes import fake_decisions
from tests.diagnosis_split_helpers import build_diagnosis_vault, seed_history
from tests.helpers import append_config_toml, create_basic_vault


def forbidden(*args, **kwargs):
    raise AssertionError("no credentials or client before a paid call")


@pytest.fixture
def seeded(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    paths = build_diagnosis_vault(tmp_path / "vault")
    seed_history(paths)
    text = (paths.root / "learnloop.toml").read_text(encoding="utf-8")
    text = text.replace("[field]\n", "[field]\nenabled = true\n").replace(
        "llm_probability_enabled = false", "llm_probability_enabled = true")
    (paths.root / "learnloop.toml").write_text(text, encoding="utf-8")
    return paths


def run(*args):
    result = CliRunner().invoke(app, list(args))
    return result.exit_code, json.loads(result.stdout.strip().splitlines()[-1]) if result.stdout.strip() else {}


def test_dry_run_estimates_both_judges_without_secrets_or_clients(seeded, tmp_path, monkeypatch):
    monkeypatch.setattr("learnloop.cli.probability_arms.load_machine_environment", forbidden)
    monkeypatch.setattr("learnloop.cli.probability_arms.ready_client_for_task", forbidden)
    code, report = run(
        "eval", "--vault", str(seeded.root), "--section", "field", "--legacy-fallback", "current_content",
        "--probability-arm", "all", "--llm-cache", str(tmp_path / "cache"), "--dry-run",
        "--max-candidates", "500", "--max-calls", "500", "--max-tokens", "100000000", "--json",
    )
    assert code == 0, report
    assert report["status"] == "dry_run" and report["predictions"] == 7
    decider, llm = report["judges"]["decider"], report["judges"]["llm"]
    assert decider["status"] == llm["status"] == "dry_run"
    assert decider["billing"] == "metered" and decider["price_source"] == "listed_input_price"
    assert decider["model"] == "perplexity/pplx-decider-v1.1-27b"
    assert llm["billing"] == "subscription" and llm["estimate"]["estimated_usd"] is None
    assert report["estimate_total"]["calls"] == decider["pending"] + llm["pending"]
    assert len(report["arms"]) == 12
    assert not (tmp_path / "cache").exists()
    text = json.dumps(report)
    assert "Write the SVD" not in text and "U Sigma" not in text  # aggregates only


def test_probability_arms_need_a_cache_and_the_switches(seeded, tmp_path):
    code, report = run("eval", "--vault", str(seeded.root), "--section", "field",
                       "--probability-arm", "v1", "--json")
    assert code == 1 and "requires --llm-cache" in report["reason"]
    code, report = run("eval", "--vault", str(seeded.root), "--section", "field",
                       "--probability-arm", "v9", "--llm-cache", str(tmp_path / "c"), "--json")
    assert code == 1 and "Unknown probability arm" in report["reason"]
    plain = create_basic_vault(tmp_path / "plain")
    code, report = run("eval", "--vault", str(plain.root), "--section", "field",
                       "--probability-arm", "v1", "--llm-cache", str(tmp_path / "c"), "--json")
    assert code == 1 and report["status"] == "disabled"


def test_missing_cache_fails_closed_with_zero_calls(seeded, tmp_path, monkeypatch):
    monkeypatch.setattr("learnloop.cli.probability_arms.ready_client_for_task", forbidden)
    code, report = run(
        "eval", "--vault", str(seeded.root), "--section", "field", "--legacy-fallback", "current_content",
        "--probability-arm", "v1/decider", "--llm-cache", str(tmp_path / "cache"), "--json",
    )
    assert code == 1 and report["status"] == "incomplete"
    assert report["cache"]["missing"] == {"v1/decider": 7}


def test_prepare_then_replay_writes_reports_with_pairwise_comparisons(seeded, tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    with fake_decisions(p_yes=0.6) as server:
        append_config_toml(seeded.root, (
            "[ai.providers.openrouter_decider]\n"
            'type = "decider"\n'
            f'base_url = "{server.base_url}"\n'
        ))
        code, report = run(
            "eval", "--vault", str(seeded.root), "--section", "field", "--legacy-fallback", "current_content",
            "--probability-arm", "decider", "--llm-cache", str(tmp_path / "cache"), "--prepare-llm",
            "--max-candidates", "100", "--max-calls", "100", "--max-tokens", "1000000",
            "--output", str(tmp_path / "reports"), "--bootstrap-samples", "20", "--json",
        )
    assert code == 0, report
    evaluation = report["evaluation"]
    assert evaluation["offline_preparation"]["judges"]["decider"]["status"] == "complete"
    arms = evaluation["report1"]["arms"]
    assert {f"llm_probability/{v}/decider{suffix}" for v in ("v1", "v2", "v3") for suffix in ("", "+recal")} <= set(arms)
    assert "llm_probability/v3/decider vs llm_probability/v2/decider" in evaluation["report1"]["pairwise"]
    markdown = (tmp_path / "reports" / "evaluation.md").read_text(encoding="utf-8")
    assert "### Paired comparisons" in markdown and "Write the SVD" not in markdown
    # The replay alone makes zero calls: the endpoint is gone and so is the key.
    monkeypatch.delenv("OPENROUTER_API_KEY")
    code, report = run(
        "eval", "--vault", str(seeded.root), "--section", "field", "--legacy-fallback", "current_content",
        "--probability-arm", "decider", "--llm-cache", str(tmp_path / "cache"),
        "--output", str(tmp_path / "reports2"), "--bootstrap-samples", "20", "--json",
    )
    assert code == 0, report


def test_judges_reports_routes_disclosures_and_needs_no_network(seeded, monkeypatch):
    import socket

    monkeypatch.setattr(socket, "socket", lambda *a, **k: pytest.fail("network"))
    code, report = run("eval", "judges", "--vault", str(seeded.root), "--json")
    assert code == 0
    routes = {entry["route"]: entry for entry in report["routes"]}
    assert routes["llm_probability_decider"]["provider"] == "openrouter_decider"
    assert routes["llm_probability_decider"]["ready"] is False
    assert routes["llm_probability_decider"]["falls_back"] is False
    assert routes["llm_probability_llm"]["billing"] == "subscription"
    assert routes["llm_probability_llm"]["consumer_status"] == "on"
    assert routes["router_decider"]["consumer_status"] == "no consumer until router R2"
    assert all(entry["disclosure"] for entry in report["routes"])


def test_judges_live_check_is_one_capped_call_with_no_learner_data(seeded, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    with fake_decisions() as server:
        append_config_toml(seeded.root, (
            "[ai.providers.openrouter_decider]\n"
            'type = "decider"\n'
            f'base_url = "{server.base_url}"\n'
        ))
        code, report = run("eval", "judges", "--vault", str(seeded.root), "--live-decider", "--json")
    assert code == 0, report
    live = report["live_decider"]
    assert live["status"] == "complete" and live["charged"]["calls"] == 1
    assert live["resolved_model"] == "perplexity/pplx-decider-v1.1-27b-20261006"
    assert set(live["answers"]) == {"is_check", "kind", "clarity"}
    assert len(server.requests) == 1
    assert "no learner data" in server.requests[0]["body"]["state"]
