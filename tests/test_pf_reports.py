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
    # The fake judge always prefers position A, so its two passes never agree.
    assert report["recommendation"]["default_path"] is None
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
        assert tier["judge_agreement"]["descriptive"]["structure_isomorph_rate_on_program_draws"]["n"] >= 1
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


@needs_bwrap
def test_each_scaling_tier_runs_its_own_program_writer_on_identical_inputs(tmp_path):
    """Codex review F11: the frontier arm never measures the cheap writer's stored program."""
    from learnloop.content.authoring import pf_contracts as C
    from tests.pf_fakes import prompt_context

    _, repository, paths = seed_pf_vault(tmp_path / "vault")
    append_config_toml(paths.root, '[pf.scaling]\ncheap = ["codex"]\nfrontier = ["codex"]')
    writers = {"cheap": PFFake("cheap-writer"), "frontier": PFFake("frontier-writer")}
    for tier, writer in writers.items():
        report = generate_practice(load_vault(paths.root), caps=CAPS, price_per_million=1.0,
                                   clients=clients(program=writer),
                                   options=GenerationOptions(path="generator", round="scale-1", tier=tier,
                                                             publish=False))
        assert report["status"] == "complete", report
    requests = {tier: [r for r in writer.calls if r.result_model is C.GeneratorProgramResult]
                for tier, writer in writers.items()}
    assert requests["cheap"] and requests["frontier"]
    contexts = {tier: prompt_context(calls[0].prompt) for tier, calls in requests.items()}
    for key in ("parent", "family", "parent_skeleton"):
        assert contexts["cheap"][key] == contexts["frontier"][key]  # identical frozen inputs
    with repository.connection() as connection:
        models = dict(connection.execute(
            "SELECT tier, GROUP_CONCAT(DISTINCT proposer_model) FROM pf_candidates GROUP BY tier").fetchall())
    assert models == {"cheap": "cheap-writer-resolved", "frontier": "frontier-writer-resolved"}
    family = load_vault(paths.root).activity_families["af_linear"]
    assert family.generator is None and family.source_kind == "authored"  # tier trials never author the family


def test_pilot_never_recommends_a_path_without_usable_comparisons():
    """Codex review F13: empty or inconclusive comparisons are insufficient evidence."""
    from learnloop.ops.pf_reports import _recommend

    arms = {arm: {"survived_all_filters": {"rate": 0.5}} for arm in ("generator", "ensemble", "single_shot")}
    for comparison in ({}, {"generator": {"pairs": 0}, "ensemble": {"pairs": 0}},
                       {"generator": {"pairs": 4, "decisions": []}, "ensemble": {"pairs": 4, "decisions": []}}):
        verdict = _recommend({"arms": arms, "blind_comparison": comparison})
        assert verdict["default_path"] is None, comparison


def test_pairs_never_cross_families_or_frozen_inputs():
    from learnloop.ops.pf_reports import _pair_rows

    def row(identifier, family, parent_hash="p"):
        return {"id": identifier, "family_id": family,
                "judged_inputs_json": json.dumps({"parent_input_hash": parent_hash, "family_revision": "f"})}

    left = [row("l1", "fa"), row("l2", "fb"), row("l3", "fa", parent_hash="edited")]
    right = [row("r1", "fa"), row("r2", "fc"), row("r3", "fa")]
    pairs = _pair_rows(left, right, 15)
    assert [(a["id"], b["family_id"]) for a, b in pairs] == [("l1", "fa")]
    assert all(a["family_id"] == b["family_id"] for a, b in pairs)


class PrefersSolve(PFFake):
    """A consistent blind judge: prefers the 'Solve ...' item, else a tie."""

    def complete(self, request):
        from learnloop.content.authoring import pf_contracts as C
        from tests.pf_fakes import prompt_context

        if request.result_model is not C.PairwiseVerdict:
            return super().complete(request)
        self.calls.append(request)
        context = prompt_context(request.prompt)
        a, b = (context[side]["problem"].startswith("Solve") for side in ("A", "B"))
        choice = "A" if a and not b else "B" if b and not a else "tie"
        return C.PairwiseVerdict(preferred=choice, depth=choice, accuracy="tie", rationale="consistent")


@needs_bwrap
def test_pilot_recommends_only_from_agreed_comparisons_on_the_same_families(tmp_path):
    _, _, paths = seed_pf_vault(tmp_path / "vault")
    for path in ("single_shot", "generator", "ensemble"):
        generate(paths, path, "pilot-1")
    biased = pilot_report(load_vault(paths.root), round_id="pilot-1", output_dir=tmp_path / "a", judge=True,
                          caps=CAPS, price_per_million=1.0, clients={"pairwise": PFFake("position-biased")})
    # The fake always prefers position A: the two passes never agree.
    assert biased["recommendation"]["default_path"] is None
    assert "insufficient" in biased["recommendation"]["reason"]
    consistent = pilot_report(load_vault(paths.root), round_id="pilot-1", output_dir=tmp_path / "b", judge=True,
                              caps=CAPS, price_per_million=1.0, clients={"pairwise": PrefersSolve("consistent")})
    assert consistent["recommendation"]["default_path"] == "generator", consistent["recommendation"]
    for arm in ("generator", "ensemble"):
        assert consistent["blind_comparison"][arm]["families"] == ["af_linear"]


@needs_bwrap
def test_suspect_acceptance_is_descriptive_and_never_ranks_a_tier(tmp_path):
    """Codex review F12: a frontier judge that calls every suspect isomorphic is not 'better'."""
    _, _, paths = seed_pf_vault(tmp_path / "vault")
    append_config_toml(paths.root, '[pf.scaling]\ncheap = ["codex"]\nfrontier = ["codex"]')
    judges = {"cheap": PFFake("cheap-judge"), "frontier": PFFake("frontier-judge", freshness_parent="isomorph")}
    for tier, judge in judges.items():
        report = generate_practice(load_vault(paths.root), caps=CAPS, price_per_million=1.0,
                                   clients=clients(freshness=judge),
                                   options=GenerationOptions(path="ensemble", round="scale-2", tier=tier,
                                                             count=10, publish=False))
        assert report["status"] == "complete", report
    report = scaling_report(load_vault(paths.root), round_id="scale-2", output_dir=tmp_path / "reports")
    rates = {tier: report["tiers"][tier]["judge_agreement"]["descriptive"]["freshness_suspect_acceptance"]
             for tier in ("cheap", "frontier")}
    assert rates["frontier"]["rate"] > rates["cheap"]["rate"] and rates["frontier"]["n"] >= 10
    assert report["components"]["freshness_judge"] == "insufficient_data"
    assert report["components"]["structure_judge"] == "insufficient_data"


def test_judge_accuracy_comes_from_labelled_pairs_judged_at_both_tiers(tmp_path):
    from learnloop.content.authoring import pf_contracts as C
    from learnloop.ops.embedding_compare import CompareRequest, run_compare
    from tests.pf_fakes import prompt_context
    from tests.test_embedding_compare import benchmark

    class Reads(PFFake):
        """Calls a pair isomorphic only when both stems are about apples (the benchmark's positives)."""

        def __init__(self, model, always=False):
            super().__init__(model)
            self.always = always

        def complete(self, request):
            if request.result_model is not C.FreshnessVerdict:
                return super().complete(request)
            self.calls.append(request)
            context = prompt_context(request.prompt)
            same = self.always or ("apples" in context["candidate"]["stem"]
                                   and "apples" in context["comparisons"][0]["prompt"])
            return C.FreshnessVerdict(comparisons=[C.FreshnessComparison(
                ref="item_0", verdict="isomorph" if same else "different", rationale="r")])

    vault, _, paths = seed_pf_vault(tmp_path / "vault")
    append_config_toml(paths.root, '[pf.scaling]\ncheap = ["codex"]\nfrontier = ["codex"]')
    bench = benchmark(tmp_path)
    for tier, judge in (("cheap", Reads("careful")), ("frontier", Reads("eager", always=True))):
        result = run_compare(load_vault(paths.root), request=CompareRequest(
            suite="b2", output_dir=tmp_path / f"b2-{tier}", benchmark_dir=bench, views=("judge",), tier=tier),
            caps=CAPS, price_per_million=1.0, clients={"freshness": judge})
        assert result["status"] == "complete" and result["tier"] == tier
    report = scaling_report(load_vault(paths.root), round_id="none", output_dir=tmp_path / "reports")
    labelled = report["judge_accuracy_on_labelled_pairs"]["freshness"]
    assert labelled["pairs_judged_at_both_tiers"] == 12
    assert labelled["cheap"]["accuracy"]["rate"] == 1.0 and labelled["frontier"]["accuracy"]["rate"] == 0.5
    assert report["components"]["freshness_judge"] == "falls_with_tier"


@needs_bwrap
def test_report_dry_runs_price_and_admit_the_blind_judge(tmp_path):
    """Codex review F9: a supplied price yields dollars, and the dry run applies the caps."""
    from learnloop.ai.spend import SpendCaps as Caps

    _, _, paths = seed_pf_vault(tmp_path / "vault")
    append_config_toml(paths.root, '[pf.scaling]\ncheap = ["codex"]\nfrontier = ["codex"]')
    for path in ("single_shot", "generator"):
        generate(paths, path, "pilot-1")
    for tier in ("cheap", "frontier"):
        generate(paths, "generator", "scale-1", tier=tier)
    vault = load_vault(paths.root)
    tight = Caps(max_candidates=100, max_pairs=100, max_calls=100, max_total_tokens=10**9,
                 max_estimated_usd=0.000001)
    judge = PFFake("judge")
    priced = pilot_report(vault, round_id="pilot-1", output_dir=tmp_path / "r", judge=True, dry_run=True,
                          caps=CAPS, price_per_million=2.0, clients={"pairwise": judge})
    assert priced["status"] == "dry_run" and priced["judge_estimate"]["calls"] > 0
    assert priced["judge_estimate"]["estimated_usd"] > 0 and priced["judge_estimate"]["billing"] == "metered"
    over = pilot_report(vault, round_id="pilot-1", output_dir=tmp_path / "r", judge=True, dry_run=True,
                        caps=tight, price_per_million=2.0, clients={"pairwise": judge})
    assert over["status"] == "over_budget" and "estimated_usd" in over["reason"]
    unknown = scaling_report(vault, round_id="scale-1", output_dir=tmp_path / "r", judge=True, dry_run=True,
                             caps=CAPS, clients={"pairwise": judge})
    assert unknown["judge_estimate"]["calls"] > 0
    assert unknown["status"] == "over_budget" and "Unknown price" in unknown["reason"]
    codex = scaling_report(vault, round_id="scale-1", output_dir=tmp_path / "r", judge=True, dry_run=True,
                           caps=tight, clients={"pairwise": PFFake("judge", provider_type="codex_sdk")})
    assert codex["status"] == "dry_run" and codex["judge_estimate"]["billing"] == "subscription"
    assert codex["judge_estimate"]["cost_basis"] == "estimated_only"
    # A refused real run sends nothing and writes no report.
    refused = pilot_report(vault, round_id="pilot-1", output_dir=tmp_path / "r", judge=True,
                           caps=tight, price_per_million=2.0, clients={"pairwise": judge})
    assert refused["status"] == "over_budget" and "blind_comparison" not in refused
    assert not judge.calls and not (tmp_path / "r").exists()
