"""PF pilot and scaling-check reports through `learnloop eval` (Slice 2 §5.6)."""
from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from learnloop.ai.spend import SpendCaps
from learnloop.cli import app
from learnloop.content.authoring.pf_sandbox import sandbox_available
from learnloop.ops.pf_generation import GenerationOptions, generate_practice
from learnloop.ops.pf_reports import pilot_report, scaling_report, wilson
from learnloop.vault.loader import load_vault
from tests.helpers import append_config_toml
from tests.pf_fakes import PFFake, clients, seed_pf_vault

needs_bwrap = pytest.mark.skipif(not sandbox_available(), reason="bubblewrap is not installed")
CAPS = SpendCaps(max_candidates=100, max_pairs=4000, max_calls=4000, max_total_tokens=10**9, max_estimated_usd=10**4)


def generate(paths, path, round_id, tier=None):
    report = generate_practice(load_vault(paths.root), caps=CAPS, price_per_million=1.0, clients=clients(),
                               options=GenerationOptions(path=path, round=round_id, tier=tier, select=3))
    assert report["status"] == "complete", report
    return report


def test_wilson_interval():
    assert wilson(0, 0) is None
    low, high = wilson(5, 10)
    assert low < 0.5 < high


@needs_bwrap
def test_pilot_compares_all_three_arms_and_the_blind_judge_is_two_pass(tmp_path):
    _, repository, paths = seed_pf_vault(tmp_path / "vault")
    for path in ("single_shot", "generator", "ensemble"):
        generate(paths, path, "pilot-1")
    pairwise = PFFake("pairwise-judge")
    dry = pilot_report(load_vault(paths.root), round_id="pilot-1", output_dir=tmp_path / "reports",
                       judge=True, dry_run=True, caps=CAPS, price_per_million=1.0, clients={"pairwise": pairwise})
    assert dry["status"] == "dry_run" and dry["judge_estimate"]["calls"] > 0
    assert not pairwise.calls and not (tmp_path / "reports").exists()
    report = pilot_report(load_vault(paths.root), round_id="pilot-1", output_dir=tmp_path / "reports",
                          judge=True, caps=CAPS, price_per_million=1.0, clients={"pairwise": pairwise})
    assert report["status"] == "complete"
    assert set(report["arms"]) == {"single_shot", "generator", "ensemble"}
    for arm in report["arms"].values():
        assert set(arm["survival_by_filter"]) >= {"authoring_gates", "freshness", "structure_check"}
        assert "cost" in arm and "usage_signals" in arm and arm["by_proposer_model"]
    assert report["arms"]["ensemble"]["cost_per_published_item"]["published"] == 3
    assert report["arms"]["single_shot"]["cost_per_published_item"]["published"] == 0
    comparison = report["blind_comparison"]
    assert set(comparison) == {"generator", "ensemble"}
    for arm in comparison.values():
        assert arm["pairs"] > 0 and arm["preferred"]["two_pass_agreement"]["n"] == arm["pairs"]
    with repository.connection() as connection:
        ratings = connection.execute(
            "SELECT judge_model, prompt_version FROM judgment_ledger WHERE task='pilot_rating'").fetchall()
    assert len(ratings) == 2 * sum(arm["pairs"] for arm in comparison.values())
    assert report["recommendation"]["default_path"] in {"ensemble", "generator"}
    for name in report["report_files"]:
        assert (tmp_path / "reports" / name).exists()
    text = (tmp_path / "reports" / report["report_files"][1]).read_text()
    assert "tank" not in text and "Solve" not in text  # aggregates only


@needs_bwrap
def test_scaling_check_reports_each_tier_and_component(tmp_path):
    _, _, paths = seed_pf_vault(tmp_path / "vault")
    append_config_toml(paths.root, '[pf.scaling]\ncheap = ["codex"]\nfrontier = ["codex"]')
    for tier in ("cheap", "frontier"):
        generate(paths, "ensemble", "scale-1", tier=tier)
        generate(paths, "generator", "scale-1", tier=tier)
    pairwise = PFFake("pairwise-judge")
    report = scaling_report(load_vault(paths.root), round_id="scale-1", output_dir=tmp_path / "reports",
                            judge=True, caps=CAPS, price_per_million=1.0, clients={"pairwise": pairwise})
    assert report["status"] == "complete"
    assert set(report["tiers"]) == {"cheap", "frontier"}
    for tier in report["tiers"].values():
        assert tier["candidates"] > 0
        assert tier["judge_agreement"]["structure_judge_vs_program_invariance"]["n"] >= 1
    assert report["blind_comparison"]["pairs"] > 0
    assert report["components"]["generators_verified_pass_rate"] in {
        "insufficient_data", "rises_with_tier", "falls_with_tier", "no_clear_difference"}


def test_scaling_tier_without_routes_is_refused(tmp_path):
    _, _, paths = seed_pf_vault(tmp_path / "vault")
    with pytest.raises(ValueError, match="pf.scaling.cheap"):
        generate_practice(load_vault(paths.root), caps=CAPS, price_per_million=1.0, clients=clients(),
                          options=GenerationOptions(path="ensemble", tier="cheap"), dry_run=True)


def test_eval_cli_reports_without_judge_are_read_only(tmp_path):
    _, _, paths = seed_pf_vault(tmp_path / "vault")
    before = paths.sqlite_path.read_bytes()
    for command in ("pf-pilot", "pf-scaling"):
        result = CliRunner().invoke(app, ["eval", command, "--vault", str(paths.root), "--round", "none",
                                          "--output", str(tmp_path / "reports"), "--json"])
        assert result.exit_code == 0, result.output
        assert json.loads(result.stdout)["status"] == "complete"
    assert paths.sqlite_path.read_bytes() == before
