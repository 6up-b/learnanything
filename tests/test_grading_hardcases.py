"""`learnloop grading hardcases`: the hard-case gold set and its harness (fakes only)."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from learnloop.ai.spend import SpendCaps
from learnloop.attempts.proof_check import CriterionRouteVerdict, ItemKindReading, ProofRouteCheck
from learnloop.cli import app
from learnloop.diagnosis.grading_hardcases import (
    CATEGORIES,
    DEFAULT_CASES,
    judge_outcome,
    load_cases,
    run_hardcases,
    write_report,
)
from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import ReviewFakeClient
from tests.helpers import create_basic_vault

CAPS = SpendCaps(max_candidates=0, max_pairs=0, max_retries=2, max_calls=500,
                 max_total_tokens=5_000_000, max_estimated_usd=3.0)
OPENROUTER = (
    '[ai.providers.haiku]\ntype = "openrouter"\nmodel = "anthropic/claude-haiku-5.5"\n'
    'api_key_env = "OPENROUTER_API_KEY"\nresponse_format = "json_schema"\n'
)


class JudgeFake(ReviewFakeClient):
    """A judge that grades every criterion one way: ``generous`` gives full
    credit and validates every step; ``strict`` marks everything down (without
    locating an error) and refutes the first step."""

    def __init__(self, mode, **kwargs):
        super().__init__(model=f"{mode}-model", **kwargs)
        self.mode = mode

    def _pf_hardcase_grader(self, request, context):
        criteria = context["rubric"]["criteria"]
        full = self.mode == "generous"
        return request.result_model.model_validate({
            "local_analysis_md": "fake", "attempt_id": context["attempt_id"],
            "practice_item_id": context["practice_item_id"],
            "criterion_evidence": [
                {"criterion_id": c["id"], "points_awarded": float(c["points"]) if full else 0.0, "evidence": "fake"}
                for c in criteria
            ],
            "rubric_score": int(sum(c["points"] for c in criteria)) if full else 0,
            "grader_confidence": 0.8,
        })

    def _pf_hardcase_checker(self, request, context):
        answer = context["learner_answer_md"]
        verdict = "established" if self.mode == "generous" else "not_established"
        return ProofRouteCheck(
            route_md="r", step_checks_md="s",
            criteria=[CriterionRouteVerdict(criterion_id=c["id"], verdict=verdict,
                                            invalid_step_quote=None if verdict == "established" else answer[:20])
                      for c in context["rubric_criteria"]],
        )

    def _pf_hardcase_item_kind(self, request, context):
        return ItemKindReading(response_kind="proof", reasoning_is_graded=True, rationale="fake")


def test_the_tracked_gold_set_is_valid_and_covers_every_cell():
    version, cases = load_cases()
    assert version == "grading-hardcases-v1" and DEFAULT_CASES.is_file()
    counts = {category: sum(case.category == category for case in cases) for category in CATEGORIES}
    assert counts == {"valid_alternative": 6, "correct_flawed": 4, "wrong_looks_right": 4}
    assert {case.subject for case in cases} == {"linear_algebra", "probability"}
    for case in cases:
        assert (case.category == "valid_alternative") == (not case.failing)
        assert set(case.failing) <= {criterion.id for criterion in case.rubric.criteria}


def test_outcomes_name_both_errors_and_the_unassessed_middle():
    _version, cases = load_cases()
    valid = next(case for case in cases if case.category == "valid_alternative")
    flawed = next(case for case in cases if case.category == "correct_flawed")
    full = {criterion.id: "full" for criterion in valid.rubric.criteria}
    assert judge_outcome(valid, full) == "correct"
    assert judge_outcome(valid, {**full, valid.rubric.criteria[0].id: "short"}) == "wrong_rejection"
    assert judge_outcome(valid, {**full, valid.rubric.criteria[0].id: "unassessed"}) == "unassessed"
    flawed_full = {criterion.id: "full" for criterion in flawed.rubric.criteria}
    assert judge_outcome(flawed, flawed_full) == "wrong_acceptance"
    assert judge_outcome(flawed, {**flawed_full, flawed.failing[0]: "flagged"}) == "caught"
    assert judge_outcome(flawed, {**flawed_full, flawed.failing[0]: "unassessed"}) == "unassessed"


def _vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    config = paths.root / "learnloop.toml"
    config.write_text(config.read_text(encoding="utf-8") + "\n" + OPENROUTER, encoding="utf-8")
    return load_vault(paths.root, load_environment=False)


def test_a_dry_run_plans_every_role_and_builds_no_client(tmp_path, monkeypatch):
    vault = _vault(tmp_path)
    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task",
                        lambda *a, **k: pytest.fail("a dry run builds no client"))
    unpriced = run_hardcases(vault, routes=["haiku"], caps=CAPS, dry_run=True)
    assert unpriced["status"] == "refused" and "price" in unpriced["reason"]
    report = run_hardcases(vault, routes=["haiku"], caps=CAPS, dry_run=True,
                           input_price_per_million=1.0, output_price_per_million=5.0)
    assert report["status"] == "dry_run"
    assert set(report["plan"]["haiku"]["roles"]) == {"grader", "checker", "item_kind"}
    assert report["estimate"]["metered"]["calls"] == 3 * 14
    assert 0 < report["estimate"]["metered"]["usd_upper_bound"] < 3.0
    capped = run_hardcases(vault, routes=["haiku"], dry_run=True, input_price_per_million=1.0,
                           output_price_per_million=5.0,
                           caps=SpendCaps(max_candidates=0, max_pairs=0, max_calls=500,
                                          max_total_tokens=5_000_000, max_estimated_usd=0.01))
    assert capped["status"] == "refused" and "SpendLimitExceeded" in capped["reason"]


def test_a_run_scores_both_error_rates_per_route_and_the_gate_per_pair(tmp_path):
    vault = _vault(tmp_path)
    report = run_hardcases(
        vault, routes=["generous", "strict"], caps=CAPS,
        clients={"generous": JudgeFake("generous"), "strict": JudgeFake("strict")},
    )
    assert report["status"] == "complete"
    generous, strict = report["by_route"]["generous"], report["by_route"]["strict"]
    # A judge that accepts everything never rejects and always wrongly accepts.
    assert generous["grader"]["wrong_rejection"]["count"] == 0
    assert (generous["grader"]["wrong_acceptance"]["count"], generous["grader"]["wrong_acceptance"]["n"]) == (8, 8)
    # One that rejects everything does the opposite.
    assert (strict["grader"]["wrong_rejection"]["count"], strict["grader"]["wrong_rejection"]["n"]) == (6, 6)
    assert strict["grader"]["wrong_acceptance"]["count"] == 0
    assert strict["checker"]["wrong_rejection"]["count"] == 6
    assert generous["item_kind"] == {"read": 14, "proof_like": 14, "kinds": {"proof": 14}}
    # The gate: a strict grader whose mark-downs locate nothing, checked by a
    # generous checker, is restored everywhere (no rejection, every wrong
    # proof accepted); a generous grader checked by a strict checker that
    # quotes the answer is flagged everywhere.
    restored = report["gate"]["grader=strict checker=generous"]
    assert restored["wrong_rejection"]["count"] == 0 and restored["wrong_acceptance"]["count"] == 8
    assert restored["independent"] is True
    flagged = report["gate"]["grader=generous checker=strict"]
    assert flagged["wrong_acceptance"]["count"] == 0 and flagged["wrong_rejection"]["count"] == 6
    assert report["spend"]["calls_by_role"] == {"hardcase_grader": 28, "hardcase_checker": 28,
                                                "hardcase_item_kind": 28}
    files = write_report(report, tmp_path / "out")
    text = (tmp_path / "out" / "grading-hardcases.md").read_text(encoding="utf-8")
    assert "| grader | strict | strict-model | 6/6 = 1.00" in text and "Eedi MAP" in text
    assert json.loads((tmp_path / "out" / "grading-hardcases.json").read_text())["status"] == "complete"
    assert set(files) == {"json", "markdown"}
    # A rerun pays nothing: every call is checkpointed in the vault copy.
    again = run_hardcases(
        vault, routes=["generous", "strict"], caps=CAPS,
        clients={"generous": JudgeFake("generous"), "strict": JudgeFake("strict")},
    )
    assert again["spend"]["calls_by_role"] == {} and sum(again["spend"]["cached_by_role"].values()) == 84


def test_a_failed_case_is_counted_never_a_crashed_run(tmp_path):
    vault = _vault(tmp_path)
    flaky = JudgeFake("generous", fail_purposes=("pf_hardcase_checker",))
    report = run_hardcases(vault, routes=["generous"], caps=CAPS, clients={"generous": flaky})
    assert report["status"] == "complete"
    assert report["by_route"]["generous"]["checker"]["failed_cases"] == 14
    assert report["errors"]["generous"]


def test_the_cli_dry_run(tmp_path):
    vault = _vault(tmp_path)
    result = CliRunner().invoke(app, [
        "grading", "hardcases", "--vault", str(vault.root), "--route", "haiku", "--dry-run", "--json",
        "--input-price-per-million", "1", "--output-price-per-million", "5",
    ])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "dry_run" and payload["cases"] == 14
    unknown = CliRunner().invoke(app, ["grading", "hardcases", "--vault", str(vault.root), "--route", "nope",
                                       "--dry-run"])
    assert unknown.exit_code == 1 and "not a configured" in unknown.output
