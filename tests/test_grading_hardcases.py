"""`learnloop grading hardcases`: the hard-case gold set and its harness (fakes only)."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from learnloop.ai.spend import SpendCaps
from learnloop.attempts.proof_check import CriterionRouteVerdict, ItemKindReading, ProofRouteCheck
from learnloop.cli import app
from learnloop.diagnosis.grading_hardcases import (
    ALL_ARMS,
    CATEGORIES,
    CELLS,
    DEFAULT_CASES,
    PRODUCTION_ARM,
    case_context,
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
    """Review F8: P2's four cells, the checkable valid alternative included;
    every case says where it came from, and none is a real trace yet."""

    version, cases = load_cases()
    assert version == "grading-hardcases-v2" and DEFAULT_CASES.name == "cases_v2.json"
    counts = {category: sum(case.category == category for case in cases) for category in CATEGORIES}
    assert counts == {"valid_alternative": 8, "correct_flawed": 4, "wrong_looks_right": 4}
    cells = {cell: sum(case.cell == cell for case in cases) for cell in CELLS}
    assert cells == {"valid_alternative_checkable": 2, "valid_alternative_proof": 6,
                     "correct_flawed": 4, "wrong_looks_right": 4}
    # The cell follows from the deterministic check, not a label.
    assert {case.final_answer_status for case in cases if case.cell == "valid_alternative_checkable"} == {
        "matches_reference"}
    assert {case.subject for case in cases} == {"linear_algebra", "probability"}
    assert {case.provenance for case in cases} == {"synthetic_hand_checked"}
    for case in cases:
        assert (case.category == "valid_alternative") == (not case.failing)
        assert set(case.failing) <= {criterion.id for criterion in case.rubric.criteria}
    # v1 (the recorded live run's set) still loads; it has no cell-1 case.
    v1_version, v1 = load_cases(DEFAULT_CASES.with_name("cases_v1.json"))
    assert v1_version == "grading-hardcases-v1" and len(v1) == 14
    assert not any(case.cell == "valid_alternative_checkable" for case in v1)


def test_a_set_without_real_traces_is_labelled_smoke_coverage(tmp_path):
    from learnloop.diagnosis.grading_hardcases import gold_set_coverage

    _version, cases = load_cases()
    coverage = gold_set_coverage(cases)
    assert coverage["kind"] == "synthetic smoke coverage"
    assert any("real traces" in limitation for limitation in coverage["limitations"])
    # A real trace must name its source.
    payload = json.loads(DEFAULT_CASES.read_text(encoding="utf-8"))
    payload["cases"][-1]["provenance"] = "real_trace"
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="source"):
        load_cases(path)
    payload["cases"][-1]["source"] = "owner vault attempt (adjudicated)"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert gold_set_coverage(load_cases(path)[1])["real_traces_by_cell"]["wrong_looks_right"] == 1


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
    # Each request reserves its route's policy budget (16,384 output tokens
    # by default; the hand-set 6,000 / 3,000 / 2,000 are retired at the merge).
    report = run_hardcases(vault, routes=["haiku"], caps=CAPS, dry_run=True,
                           input_price_per_million=1.0, output_price_per_million=2.0)
    assert report["status"] == "dry_run"
    assert set(report["plan"]["haiku"]["roles"]) == {f"grader:{PRODUCTION_ARM}", "checker", "item_kind"}
    assert report["estimate"]["metered"]["calls"] == 3 * 16
    assert 0 < report["estimate"]["metered"]["usd_upper_bound"] < 3.0
    assert report["gold_set"]["kind"] == "synthetic smoke coverage"
    assert any("--ablations" in limitation for limitation in report["limitations"])
    assert any("noise floor" in limitation for limitation in report["limitations"])
    # R2's crossed arms and fresh repetitions are planned and priced too.
    crossed = run_hardcases(vault, routes=["haiku"], caps=CAPS, dry_run=True, arms=ALL_ARMS, repeats=2,
                            input_price_per_million=1.0, output_price_per_million=5.0)
    assert crossed["estimate"]["metered"]["calls"] == (4 + 2) * 16 * 2
    assert not any("--ablations" in limitation for limitation in crossed["limitations"])
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
    assert (strict["grader"]["wrong_rejection"]["count"], strict["grader"]["wrong_rejection"]["n"]) == (8, 8)
    assert strict["grader"]["wrong_acceptance"]["count"] == 0
    assert strict["checker"]["wrong_rejection"]["count"] == 8
    assert strict["grader"]["by_cell"]["valid_alternative_checkable"] == {"wrong_rejection": 2}
    assert generous["item_kind"] == {"read": 16, "proof_like": 16, "kinds": {"proof": 16}}
    # The gate: a strict grader whose mark-downs locate nothing, checked by a
    # generous checker, is restored everywhere (no rejection, every wrong
    # proof accepted); a generous grader checked by a strict checker that
    # quotes the answer is flagged everywhere.
    restored = report["gate"]["grader=strict checker=generous"]
    assert restored["wrong_rejection"]["count"] == 0 and restored["wrong_acceptance"]["count"] == 8
    assert restored["independent"] is True and restored["check"] == {"checked": 16}
    flagged = report["gate"]["grader=generous checker=strict"]
    assert flagged["wrong_acceptance"]["count"] == 0 and flagged["wrong_rejection"]["count"] == 8
    assert report["spend"]["calls_by_role"] == {"hardcase_grader": 32, "hardcase_checker": 32,
                                                "hardcase_item_kind": 32}
    files = write_report(report, tmp_path / "out")
    text = (tmp_path / "out" / "grading-hardcases.md").read_text(encoding="utf-8")
    assert "| grader | strict | strict-model | 8/8 = 1.00" in text and "Eedi MAP" in text
    assert "synthetic smoke coverage" in text and "Limitation: no real traces" in text
    assert json.loads((tmp_path / "out" / "grading-hardcases.json").read_text())["status"] == "complete"
    assert set(files) == {"json", "markdown"}
    # Review F7: every judge's verdict is in judgment_ledger, keyed by the case's content.
    rows = _hardcase_judgments(vault)
    assert len(rows) == report["judgments"]["ensured"] == 2 * 3 * 16
    assert {row["task"] for row in rows} == {
        "grading_hardcase_grader", "grading_hardcase_checker", "grading_hardcase_item_kind"}
    assert {row["judge_model"] for row in rows} == {"generous-model", "strict-model"}
    _version, cases = load_cases()
    assert {row["left_id"] for row in rows} == {case.content_key for case in cases}
    grader_rows = [row for row in rows if row["task"] == "grading_hardcase_grader"
                   and row["judge_model"] == "strict-model"]
    assert {json.loads(row["verdict"])["outcome"] for row in grader_rows} == {"wrong_rejection", "caught"}
    # A rerun pays nothing (every call is checkpointed in the vault copy) and
    # ensures each judgment exists without duplicating it.
    again = run_hardcases(
        vault, routes=["generous", "strict"], caps=CAPS,
        clients={"generous": JudgeFake("generous"), "strict": JudgeFake("strict")},
    )
    assert again["spend"]["calls_by_role"] == {} and sum(again["spend"]["cached_by_role"].values()) == 96
    assert again["judgments"]["ensured"] == 96 and len(_hardcase_judgments(vault)) == 96


def _hardcase_judgments(vault):
    from learnloop.db.connection import connect
    from learnloop.vault.paths import VaultPaths

    with connect(VaultPaths(vault.root, vault.config).sqlite_path, read_only=True) as connection:
        connection.row_factory = __import__("sqlite3").Row
        return [dict(row) for row in connection.execute(
            "SELECT * FROM judgment_ledger WHERE task LIKE 'grading_hardcase_%'")]


class NotProofReader(JudgeFake):
    """A generous checker whose own item reading says the items are not proof-like."""

    def _pf_hardcase_item_kind(self, request, context):
        return ItemKindReading(response_kind="computation", reasoning_is_graded=False, rationale="fake")


class DivergentStrict(JudgeFake):
    """A strict grader that reads every route as divergent from the reference."""

    def __init__(self, **kwargs):
        super().__init__("strict", **kwargs)

    def _pf_hardcase_grader(self, request, context):
        from learnloop.attempts.grading_support import RouteCheck

        result = super()._pf_hardcase_grader(request, context)
        return result.model_copy(update={"route_check": RouteCheck(divergent_route=True, rederivation_md="r")})


class AbstainingChecker(JudgeFake):
    def __init__(self, **kwargs):
        super().__init__("abstaining", **kwargs)

    def _pf_hardcase_checker(self, request, context):
        return ProofRouteCheck(route_md="r", step_checks_md="s", criteria=[
            CriterionRouteVerdict(criterion_id=c["id"], verdict="cannot_tell") for c in context["rubric_criteria"]])


def test_the_gate_follows_the_production_path(tmp_path):
    """Review F6: the check runs only where the checker route's own reading is
    proof-like and the check returned; otherwise PF-c's grade stands, as live
    grading does. A strict grader checked by a generous checker is restored
    only when the checker's reading lets the check run."""

    vault = _vault(tmp_path)
    report = run_hardcases(vault, routes=["strict", "notproof", "unread", "nocheck"], caps=CAPS, clients={
        "strict": JudgeFake("strict"),
        "notproof": NotProofReader("generous"),
        "unread": JudgeFake("generous", fail_purposes=("pf_hardcase_item_kind",)),
        "nocheck": JudgeFake("generous", fail_purposes=("pf_hardcase_checker",)),
    })
    for checker_route, status in (("notproof", "not_proof_like"), ("unread", "unclassified"),
                                  ("nocheck", "unavailable")):
        gate = report["gate"][f"grader=strict checker={checker_route}"]
        assert gate["check"] == {status: 16}, checker_route
        # PF-c alone: proofs stay rejected; checkable alternatives are unassessed.
        assert gate["wrong_rejection"]["count"] == 6 and gate["failed_cases"] == 0
        assert gate["by_cell"]["valid_alternative_checkable"] == {"unassessed": 2}
    assert report["by_route"]["unread"]["item_kind"]["read"] == 0


def test_the_gate_applies_p1_to_a_divergent_route(tmp_path):
    vault = _vault(tmp_path)
    report = run_hardcases(vault, routes=["divergent", "abstaining"], caps=CAPS, clients={
        "divergent": DivergentStrict(), "abstaining": AbstainingChecker()})
    gate = report["gate"]["grader=divergent checker=abstaining"]
    # Nothing located by either judge on a divergent route: unassessed, never rejected.
    assert gate["wrong_rejection"]["count"] == 0 and gate["unassessed"] == 16


class FlipGrader(JudgeFake):
    """Generous on the first repetition's grader calls, strict on the next."""

    def __init__(self, **kwargs):
        super().__init__("flip", **kwargs)
        self.turn = 0
        self.per_repetition = len(load_cases()[1])

    def _pf_hardcase_grader(self, request, context):
        self.mode = "generous" if (self.turn // self.per_repetition) % 2 == 0 else "strict"
        self.turn += 1
        return super()._pf_hardcase_grader(request, context)


def test_repetitions_are_fresh_and_give_a_noise_floor(tmp_path):
    vault = _vault(tmp_path)
    steady = run_hardcases(vault, routes=["generous"], caps=CAPS, repeats=2,
                           clients={"generous": JudgeFake("generous")})
    assert steady["spend"]["calls_by_role"]["hardcase_grader"] == 32  # nothing reused across repetitions
    noise = steady["by_route"]["generous"]["grader"]["noise_floor"]
    assert noise["repetitions"] == 2 and noise["changed"]["count"] == 0 and noise["changed"]["n"] == 16
    assert any(key.endswith("#1") for key in steady["per_case"]["la-rank-ata-nullspace"])
    flip = run_hardcases(vault, routes=["flip"], caps=CAPS, repeats=2, clients={"flip": FlipGrader()})
    changed = flip["by_route"]["flip"]["grader"]["noise_floor"]["changed"]
    assert changed["count"] == changed["n"] == 16  # every outcome changed between repetitions
    # Each repetition's verdicts are separately identified in the ledger.
    assert len([row for row in _hardcase_judgments(vault) if row["judge_model"] == "flip-model"]) == 3 * 16 * 2


def test_the_grader_arms_cross_the_reference_and_the_check(tmp_path):
    vault = _vault(tmp_path)
    _version, cases = load_cases()
    case = next(c for c in cases if c.cell == "valid_alternative_checkable")
    production = case_context(vault, case)
    assert production.reference_policy["final_answer_check"]["status"] == "matches_reference"
    assert production.reference_policy["reference_status"] == "authored" and production.expected_answer
    solve_first = case_context(vault, case, "solve_first+check_shown")
    assert solve_first.expected_answer == "" and solve_first.reference_policy["reference_status"] == "absent"
    assert solve_first.reference_policy["final_answer_check"]["status"] == "matches_reference"
    withheld = case_context(vault, case, "reference_shown+check_withheld")
    assert withheld.reference_policy["final_answer_check"]["status"] == "withheld_from_grader"
    assert withheld.verifier_observations == [] and withheld.expected_answer
    with pytest.raises(ValueError, match="unknown grader arm"):
        case_context(vault, case, "reference_shown+check_late")
    seen: list[str] = []

    class Recording(JudgeFake):
        def _pf_hardcase_grader(self, request, context):
            seen.append(json.dumps(context, sort_keys=True))
            return super()._pf_hardcase_grader(request, context)

    report = run_hardcases(vault, routes=["rec"], caps=CAPS, arms=ALL_ARMS, clients={"rec": Recording("strict")})
    assert len(seen) == 4 * 16
    reference_text = "Expand along the first row"
    assert sum(reference_text in context for context in seen) == 2  # the two reference_shown arms
    assert sum("withheld_from_grader" in context for context in seen) == 2 * 16
    by_route = report["by_route"]["rec"]
    assert set(by_route) >= {"grader", "grader[solve_first+check_withheld]", "checker"}
    # The gate applies the real check whatever the grader was shown.
    gate = report["gate"]["grader=rec checker=rec arm=reference_shown+check_withheld"]
    assert gate["arm"] == "reference_shown+check_withheld" and gate["check"] == {"checked": 16}


def test_a_failed_case_is_counted_never_a_crashed_run(tmp_path):
    vault = _vault(tmp_path)
    flaky = JudgeFake("generous", fail_purposes=("pf_hardcase_checker",))
    report = run_hardcases(vault, routes=["generous"], caps=CAPS, clients={"generous": flaky})
    assert report["status"] == "complete"
    assert report["by_route"]["generous"]["checker"]["failed_cases"] == 16
    assert report["errors"]["generous"]
    # The gate is not failed: without a check, PF-c's grade stands (review F6).
    assert report["gate"]["grader=generous checker=generous"]["failed_cases"] == 0


def test_the_cli_dry_run(tmp_path):
    vault = _vault(tmp_path)
    result = CliRunner().invoke(app, [
        "grading", "hardcases", "--vault", str(vault.root), "--route", "haiku", "--dry-run", "--json",
        "--input-price-per-million", "1", "--output-price-per-million", "2",
    ])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "dry_run" and payload["cases"] == 16
    ablations = CliRunner().invoke(app, [
        "grading", "hardcases", "--vault", str(vault.root), "--route", "haiku", "--dry-run",
        "--input-price-per-million", "1", "--output-price-per-million", "5", "--ablations", "--repeats", "2",
        "--max-tokens", "10000000", "--max-cost-usd", "20", "--max-calls", "500",
    ])
    assert ablations.exit_code == 0, ablations.output
    summary = json.loads(ablations.output)
    assert summary["arms"] == list(ALL_ARMS) and summary["repeats"] == 2
    assert summary["estimate"]["metered"]["calls"] == 6 * 16 * 2
    unknown = CliRunner().invoke(app, ["grading", "hardcases", "--vault", str(vault.root), "--route", "nope",
                                       "--dry-run"])
    assert unknown.exit_code == 1 and "not a configured" in unknown.output
