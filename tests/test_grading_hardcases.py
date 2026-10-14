"""`learnloop grading hardcases`: the hard-case gold set and its harness (fakes only).

Since route-check-in-grader the harness measures the grader alone, with the
own-route rules in its prompt, on its raw output and along the production
path (PF-c's gate, then the own-route rule). Since method-explicit items
(harness v4, gold set v3) the production rules are ``own-route-v2`` with the
item's required method, and cell 5 holds required-method items answered by
another valid method, each paired with the same mathematics without one.
"""

from __future__ import annotations

import itertools
import json

import pytest
from typer.testing import CliRunner

from learnloop.ai.spend import SpendCaps
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
    """A grader that grades every criterion one way: ``generous`` gives full
    credit; ``strict`` marks everything down without locating an error."""

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


def test_the_tracked_gold_set_is_valid_and_covers_every_cell():
    """Review F8: P2's four cells, the checkable valid alternative included,
    and the method-explicit fifth; every case says where it came from, and
    none is a real trace yet."""

    version, cases = load_cases()
    assert version == "grading-hardcases-v3" and DEFAULT_CASES.name == "cases_v3.json"
    counts = {category: sum(case.category == category for case in cases) for category in CATEGORIES}
    assert counts == {"valid_alternative": 10, "correct_flawed": 4, "wrong_looks_right": 4,
                      "required_method_bypassed": 2}
    cells = {cell: sum(case.cell == cell for case in cases) for cell in CELLS}
    assert cells == {"valid_alternative_checkable": 3, "valid_alternative_proof": 7,
                     "correct_flawed": 4, "wrong_looks_right": 4, "required_method_bypassed": 2}
    # The cell follows from the deterministic check, not a label.
    assert {case.final_answer_status for case in cases if case.cell == "valid_alternative_checkable"} == {
        "matches_reference"}
    assert {case.subject for case in cases} == {"linear_algebra", "probability"}
    assert {case.provenance for case in cases} == {"synthetic_hand_checked"}
    for case in cases:
        assert (case.category == "valid_alternative") == (not case.failing)
        assert set(case.failing) <= {criterion.id for criterion in case.rubric.criteria}
    # v2 (the route-rules live run's set) still loads: cells 1-4 only.
    v2_version, v2 = load_cases(DEFAULT_CASES.with_name("cases_v2.json"))
    assert v2_version == "grading-hardcases-v2" and len(v2) == 16
    assert not any(case.item.required_method for case in v2)
    assert [case.id for case in cases[:16]] == [case.id for case in v2]
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
    last = max(index for index, case in enumerate(payload["cases"]) if case["category"] == "wrong_looks_right")
    payload["cases"][last]["provenance"] = "real_trace"
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="source"):
        load_cases(path)
    payload["cases"][last]["source"] = "owner vault attempt (adjudicated)"
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
    assert judge_outcome(flawed, {**flawed_full, flawed.failing[0]: "short"}) == "caught"
    assert judge_outcome(flawed, {**flawed_full, flawed.failing[0]: "unassessed"}) == "unassessed"


def _vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    config = paths.root / "learnloop.toml"
    config.write_text(config.read_text(encoding="utf-8") + "\n" + OPENROUTER, encoding="utf-8")
    return load_vault(paths.root, load_environment=False)


def test_a_dry_run_plans_the_grader_and_builds_no_client(tmp_path, monkeypatch):
    vault = _vault(tmp_path)
    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task",
                        lambda *a, **k: pytest.fail("a dry run builds no client"))
    unpriced = run_hardcases(vault, routes=["haiku"], caps=CAPS, dry_run=True)
    assert unpriced["status"] == "refused" and "price" in unpriced["reason"]
    # Each request reserves the grading route's policy budget (16,384 output
    # tokens by default). One call per case: no checker, no item reading.
    report = run_hardcases(vault, routes=["haiku"], caps=CAPS, dry_run=True,
                           input_price_per_million=1.0, output_price_per_million=2.0)
    assert report["status"] == "dry_run"
    assert set(report["plan"]["haiku"]["roles"]) == {f"grader:{PRODUCTION_ARM}"}
    assert report["estimate"]["metered"]["calls"] == 20
    assert report["prompt_versions"]["grader"].endswith("+own-route-v2")
    assert 0 < report["estimate"]["metered"]["usd_upper_bound"] < 3.0
    assert report["gold_set"]["kind"] == "synthetic smoke coverage"
    assert any("--ablations" in limitation for limitation in report["limitations"])
    assert any("noise floor" in limitation for limitation in report["limitations"])
    # R2's crossed arms and fresh repetitions are planned and priced too.
    crossed = run_hardcases(vault, routes=["haiku"], caps=CAPS, dry_run=True, arms=ALL_ARMS, repeats=2,
                            input_price_per_million=1.0, output_price_per_million=5.0)
    assert crossed["estimate"]["metered"]["calls"] == 4 * 20 * 2
    assert not any("--ablations" in limitation for limitation in crossed["limitations"])
    capped = run_hardcases(vault, routes=["haiku"], dry_run=True, input_price_per_million=1.0,
                           output_price_per_million=5.0,
                           caps=SpendCaps(max_candidates=0, max_pairs=0, max_calls=500,
                                          max_total_tokens=5_000_000, max_estimated_usd=0.01))
    assert capped["status"] == "refused" and "SpendLimitExceeded" in capped["reason"]


def test_a_run_scores_both_error_rates_per_route_and_the_production_path(tmp_path):
    vault = _vault(tmp_path)
    report = run_hardcases(
        vault, routes=["generous", "strict"], caps=CAPS,
        clients={"generous": JudgeFake("generous"), "strict": JudgeFake("strict")},
    )
    assert report["status"] == "complete"
    generous, strict = report["by_route"]["generous"], report["by_route"]["strict"]
    assert set(generous) == {"model", "grader"}
    # A grader that accepts everything never rejects and always wrongly accepts.
    assert generous["grader"]["wrong_rejection"]["count"] == 0
    assert (generous["grader"]["wrong_acceptance"]["count"], generous["grader"]["wrong_acceptance"]["n"]) == (8, 8)
    # ... and never enforces a required method (cell 5, reported apart).
    assert generous["grader"]["required_method"]["not_enforced"]["count"] == 2
    # One that rejects everything does the opposite.
    assert (strict["grader"]["wrong_rejection"]["count"], strict["grader"]["wrong_rejection"]["n"]) == (10, 10)
    assert strict["grader"]["wrong_acceptance"]["count"] == 0
    assert strict["grader"]["by_cell"]["valid_alternative_checkable"] == {"wrong_rejection": 3}
    # It fails the method criteria but also rejects the facts the other route established.
    assert strict["grader"]["required_method"]["fact_rejected"]["count"] == 2
    # The production path: PF-c leaves a checkable alternative's unlocated
    # mark-downs unassessed; a route the grader does not read as divergent
    # keeps the rest of its mark-downs.
    path = report["gate"]["grader=strict"]
    assert path["wrong_rejection"]["count"] == 7 and path["by_cell"]["valid_alternative_checkable"] == {"unassessed": 3}
    assert path["rule"] == {"unchanged": 20}
    assert report["gate"]["grader=generous"]["wrong_acceptance"]["count"] == 8
    assert report["spend"]["calls_by_role"] == {"hardcase_grader": 40}
    files = write_report(report, tmp_path / "out")
    text = (tmp_path / "out" / "grading-hardcases.md").read_text(encoding="utf-8")
    assert "| grader | strict | strict-model | 10/10 = 1.00" in text and "Eedi MAP" in text
    assert "Required method enforced (cell 5)" in text
    assert "| gate | grader=strict | rule=" in text
    assert "synthetic smoke coverage" in text and "Limitation: no real traces" in text
    assert json.loads((tmp_path / "out" / "grading-hardcases.json").read_text())["status"] == "complete"
    assert set(files) == {"json", "markdown"}
    # Review F7: every grader verdict is in judgment_ledger, keyed by the case's content.
    rows = _hardcase_judgments(vault)
    assert len(rows) == report["judgments"]["ensured"] == 2 * 20
    assert {row["task"] for row in rows} == {"grading_hardcase_grader"}
    assert {row["judge_model"] for row in rows} == {"generous-model", "strict-model"}
    _version, cases = load_cases()
    assert {row["left_id"] for row in rows} == {case.content_key for case in cases}
    strict_rows = [row for row in rows if row["judge_model"] == "strict-model"]
    assert {json.loads(row["verdict"])["outcome"] for row in strict_rows} == {"wrong_rejection", "caught"}
    # A rerun pays nothing (every call is checkpointed in the vault copy) and
    # ensures each judgment exists without duplicating it.
    again = run_hardcases(
        vault, routes=["generous", "strict"], caps=CAPS,
        clients={"generous": JudgeFake("generous"), "strict": JudgeFake("strict")},
    )
    assert again["spend"]["calls_by_role"] == {} and sum(again["spend"]["cached_by_role"].values()) == 40
    assert again["judgments"]["ensured"] == 40 and len(_hardcase_judgments(vault)) == 40


def _hardcase_judgments(vault):
    from learnloop.db.connection import connect
    from learnloop.vault.paths import VaultPaths

    with connect(VaultPaths(vault.root, vault.config).sqlite_path, read_only=True) as connection:
        connection.row_factory = __import__("sqlite3").Row
        return [dict(row) for row in connection.execute(
            "SELECT * FROM judgment_ledger WHERE task LIKE 'grading_hardcase_%'")]


class DivergentStrict(JudgeFake):
    """A strict grader that reads every route as divergent from the reference,
    optionally citing ``quote`` (a quote from the answer, or a fabricated one)
    as the located error on every criterion."""

    def __init__(self, quote=None, *, declare=False, **kwargs):
        super().__init__("strict", **kwargs)
        self.quote = quote
        #: Also declare every criterion unverifiable (``unverified_criterion_ids``).
        self.declare = declare

    def _pf_hardcase_grader(self, request, context):
        payload = super()._pf_hardcase_grader(request, context).model_dump(mode="json")
        payload["route_check"] = {"divergent_route": True, "rederivation_md": "r"}
        if self.declare:
            payload["unverified_criterion_ids"] = [c["id"] for c in context["rubric"]["criteria"]]
        if self.quote is not None:
            answer = context["learner_answer_md"]
            quote = answer.split(".")[0] if self.quote == "answer" else self.quote
            payload["error_attributions"] = [
                {"error_type": "conceptual_slip", "evidence": "e", "target_criterion_ids": [c["id"]],
                 "first_divergence": {"anchor_kind": "span", "criterion_id": c["id"], "quote": quote},
                 "validity_scope": "valid_measurement"}
                for c in context["rubric"]["criteria"]
            ]
        return request.result_model.model_validate(payload)


@pytest.mark.parametrize("quote", [None, "a step the learner never wrote"], ids=["unlocated", "fabricated"])
def test_the_production_path_applies_p1_to_a_divergent_route(tmp_path, quote):
    """Nothing located verbatim on a divergent route: unassessed, never a
    rejection (and held where nothing validated the answer); PF-c already
    unassesses a checkable alternative's mark-downs. A required method's
    criterion is the exception: the route is its evidence, so cell 5's method
    criteria stay failed while its facts (marked down by this strict grader)
    are unassessed. Review F8: facts that were not credited make the case
    ``unassessed``, never a success."""

    vault = _vault(tmp_path)
    report = run_hardcases(vault, routes=["divergent"], caps=CAPS, clients={"divergent": DivergentStrict(quote)})
    path = report["gate"]["grader=divergent"]
    assert path["wrong_rejection"]["count"] == 0 and path["unassessed"] == 20
    # Held: 7 proofs and the 8 failing cases. Unchanged: PF-c's 3 checkable
    # alternatives and the checkable cell-5 case (PF-c unassessed its facts;
    # its method criterion stays failed). Unlocated: the other cell-5 case.
    assert path["rule"] == {"held": 15, "unchanged": 4, "unlocated": 1}
    assert path["by_cell"]["required_method_bypassed"] == {"unassessed": 2}
    assert path["required_method"]["enforced"]["count"] == 0
    assert path["required_method"]["not_enforced"]["count"] == 0
    # The raw grade is still a rejection: the rule, not the grader, saved it.
    assert report["by_route"]["divergent"]["grader"]["wrong_rejection"]["count"] == 10


def test_a_verbatim_quote_keeps_the_mark_down_on_a_divergent_route(tmp_path):
    vault = _vault(tmp_path)
    report = run_hardcases(vault, routes=["quoting"], caps=CAPS,
                           clients={"quoting": DivergentStrict("answer")})
    path = report["gate"]["grader=quoting"]
    assert path["wrong_rejection"]["count"] == 10 and path["rule"] == {"unchanged": 20}


def test_the_production_path_reads_the_graders_declared_uncertainty(tmp_path):
    """Review F2: a quoted mark-down the grader itself declares unverifiable
    is unassessed on a divergent route, as in serving; a conclusion that
    differs from the reference still outranks it."""

    vault = _vault(tmp_path)
    report = run_hardcases(vault, routes=["declaring"], caps=CAPS,
                           clients={"declaring": DivergentStrict("answer", declare=True)})
    path = report["gate"]["grader=declaring"]
    assert path["wrong_rejection"]["count"] == 0
    # The quote no longer keeps them; a required method's criterion the
    # grader itself declares unverifiable is unassessed too (cell 5's
    # undecidable case is then held, its checkable one left to PF-c).
    assert path["rule"] == {"held": 16, "unchanged": 4}
    assert path["by_cell"]["required_method_bypassed"] == {"unassessed": 2}


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
    assert steady["spend"]["calls_by_role"] == {"hardcase_grader": 40}  # nothing reused across repetitions
    noise = steady["by_route"]["generous"]["grader"]["noise_floor"]
    assert noise["repetitions"] == 2 and noise["changed"]["count"] == 0 and noise["changed"]["n"] == 20
    assert any(key.endswith("#1") for key in steady["per_case"]["la-rank-ata-nullspace"])
    flip = run_hardcases(vault, routes=["flip"], caps=CAPS, repeats=2, clients={"flip": FlipGrader()})
    changed = flip["by_route"]["flip"]["grader"]["noise_floor"]["changed"]
    assert changed["count"] == changed["n"] == 20  # every outcome changed between repetitions
    # Each repetition's verdicts are separately identified in the ledger.
    assert len([row for row in _hardcase_judgments(vault) if row["judge_model"] == "flip-model"]) == 20 * 2


def test_the_grader_arms_cross_the_reference_and_the_check(tmp_path):
    vault = _vault(tmp_path)
    _version, cases = load_cases()
    case = next(c for c in cases if c.cell == "valid_alternative_checkable")
    production = case_context(vault, case)
    assert production.reference_policy["final_answer_check"]["status"] == "matches_reference"
    assert production.reference_policy["route_rules"] == "own-route-v2"
    assert "required_method" not in production.reference_policy
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
    assert len(seen) == 4 * 20
    reference_text = "Expand along the first row"
    # Three determinant cases, each under the two reference_shown arms.
    assert sum(reference_text in context for context in seen) == 3 * 2
    assert sum("withheld_from_grader" in context for context in seen) == 2 * 20
    by_route = report["by_route"]["rec"]
    assert set(by_route) == {"model", "grader", "grader[solve_first+check_shown]",
                             "grader[reference_shown+check_withheld]", "grader[solve_first+check_withheld]"}
    # The production path applies the real check whatever the grader was shown.
    gate = report["gate"]["grader=rec arm=reference_shown+check_withheld"]
    assert gate["arm"] == "reference_shown+check_withheld" and sum(gate["rule"].values()) == 20
    assert gate["by_cell"]["valid_alternative_checkable"] == {"unassessed": 3}


def test_a_failed_case_is_counted_never_a_crashed_run(tmp_path):
    vault = _vault(tmp_path)
    flaky = JudgeFake("generous", fail_purposes=("pf_hardcase_grader",))
    report = run_hardcases(vault, routes=["generous"], caps=CAPS, clients={"generous": flaky})
    assert report["status"] == "complete"
    assert report["by_route"]["generous"]["grader"]["failed_cases"] == 20
    assert report["errors"]["generous"]
    assert report["gate"]["grader=generous"]["failed_cases"] == 20


def test_the_cli_dry_run(tmp_path):
    vault = _vault(tmp_path)
    result = CliRunner().invoke(app, [
        "grading", "hardcases", "--vault", str(vault.root), "--route", "haiku", "--dry-run", "--json",
        "--input-price-per-million", "1", "--output-price-per-million", "2",
    ])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "dry_run" and payload["cases"] == 20
    ablations = CliRunner().invoke(app, [
        "grading", "hardcases", "--vault", str(vault.root), "--route", "haiku", "--dry-run",
        "--input-price-per-million", "1", "--output-price-per-million", "5", "--ablations", "--repeats", "2",
        "--max-tokens", "10000000", "--max-cost-usd", "20", "--max-calls", "500",
    ])
    assert ablations.exit_code == 0, ablations.output
    summary = json.loads(ablations.output)
    assert summary["arms"] == list(ALL_ARMS) and summary["repeats"] == 2
    assert summary["estimate"]["metered"]["calls"] == 4 * 20 * 2
    unknown = CliRunner().invoke(app, ["grading", "hardcases", "--vault", str(vault.root), "--route", "nope",
                                       "--dry-run"])
    assert unknown.exit_code == 1 and "not a configured" in unknown.output


# -- method-explicit items (harness v4, gold set v3 cell 5) ---------------------------------


def _method_cases():
    _version, cases = load_cases()
    by_id = {case.id: case for case in cases}
    return by_id, [case for case in cases if case.cell == "required_method_bypassed"]


def test_cell_5_pairs_each_required_method_with_the_same_mathematics_without_one(tmp_path):
    """(a) a required-method item answered by another valid method, (b) the
    same mathematics without a required method: the same answer, a valid
    alternative."""

    vault = _vault(tmp_path)
    by_id, method_cases = _method_cases()
    pairs = {
        "la-det-required-cofactor-by-row-reduction": "la-det-no-required-method-row-reduction",
        "pr-at-least-one-six-required-inclusion-exclusion-by-complement":
            "pr-at-least-one-six-no-required-method-complement",
    }
    assert {case.id for case in method_cases} == set(pairs)
    for required_id, free_id in pairs.items():
        required, free = by_id[required_id], by_id[free_id]
        method = required.item.required_method
        assert method is not None and method.criterion_ids == list(required.failing) == ["method"]
        assert method.name.lower() in required.item.prompt.lower()
        assert free.item.required_method is None and free.category == "valid_alternative" and not free.failing
        assert free.answer == required.answer and free.item.expected_answer == required.item.expected_answer
        # The free item's criteria name facts (the heuristic reads none by method).
        from learnloop.vault.required_method import method_phrase

        assert all(method_phrase(criterion.description) is None for criterion in free.rubric.criteria)
        # Its production context carries the own-route-v2 rules and the item's method.
        assert case_context(vault, required).reference_policy["required_method"] == {
            "name": method.name, "criterion_ids": ["method"]}
        assert "required_method" not in case_context(vault, free).reference_policy
        # Round 3: the grader is shown the statement, then the instruction
        # rendered from the field; the free item's statement exactly.
        assert case_context(vault, required).prompt == (
            f"{required.item.prompt}\n\nUse {method.name} in your answer.")
        assert case_context(vault, free).prompt == free.item.prompt


def test_outcomes_on_a_required_method_bypassed():
    _by_id, method_cases = _method_cases()
    case = method_cases[0]
    others = [criterion.id for criterion in case.rubric.criteria if criterion.id not in case.failing]
    caught = {"method": "short", **{cid: "full" for cid in others}}
    assert judge_outcome(case, caught) == "caught"
    # Full credit on the method criterion: the requirement was not enforced.
    assert judge_outcome(case, {**caught, "method": "full"}) == "wrong_acceptance"
    # A fact criterion marked down: a valid route's fact rejected.
    assert judge_outcome(case, {**caught, others[0]: "short"}) == "wrong_rejection"
    assert judge_outcome(case, {**caught, "method": "unassessed"}) == "unassessed"
    # Review F8: facts left unassessed were not credited, so the case is not a
    # success ("method failed, facts credited"); it stays unassessed.
    assert judge_outcome(case, {"method": "short", **{cid: "unassessed" for cid in others}}) == "unassessed"


@pytest.mark.parametrize("method, steps, result", list(itertools.product(("full", "short", "unassessed"), repeat=3)))
def test_every_fact_and_method_state_on_a_required_method_bypassed(method, steps, result):
    """Review F8: ``caught`` only when the method criterion failed AND every
    fact criterion has full credit; a method at full credit is an unenforced
    requirement, a fact marked down a valid route's fact rejected, and
    anything else left unassessed is ``unassessed``."""

    by_id, _method_cases_ = _method_cases()
    case = by_id["la-det-required-cofactor-by-row-reduction"]
    assert set(case.failing) == {"method"} and {c.id for c in case.rubric.criteria} == {"method", "steps", "result"}
    states = {"method": method, "steps": steps, "result": result}
    if method == "full":
        expected = "wrong_acceptance"
    elif "short" in (steps, result):
        expected = "wrong_rejection"
    elif "unassessed" in (method, steps, result):
        expected = "unassessed"
    else:
        expected = "caught"
    assert judge_outcome(case, states) == expected
    assert (expected == "caught") == (states == {"method": "short", "steps": "full", "result": "full"})


@pytest.mark.parametrize("mutation, message", [
    # Redesign 2026-10-14: doctor's validation of the field, no phrasing read
    # (round 3: a generated statement is never checked for the sentence).
    (lambda case: case["item"]["required_method"].pop("decided_by"), "required_method:undecided"),
    (lambda case: case["label"].update(failing_criteria=["result"]), "fails exactly its method criteria"),
    (lambda case: case["item"].pop("required_method"), "names its required method's criteria"),
    (lambda case: case.update(answer=case["answer"].replace("\n\ndet(A) = 13", "\n\n12")), "differs"),
], ids=["undecided", "wrong_label", "no_method", "wrong_answer"])
def test_the_loader_refuses_a_malformed_required_method_case(tmp_path, mutation, message):
    payload = json.loads(DEFAULT_CASES.read_text(encoding="utf-8"))
    case = next(entry for entry in payload["cases"] if entry["id"] == "la-det-required-cofactor-by-row-reduction")
    mutation(case)
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_cases(path)


class MethodAwareGrader(JudgeFake):
    """What a correct grader does: on a required-method item answered by
    another route, it fails the method criteria with NO quoted step (the route
    is the evidence) and reads the route as divergent; every other criterion
    gets full credit on the facts."""

    def __init__(self, **kwargs):
        super().__init__("generous", **kwargs)

    def _pf_hardcase_grader(self, request, context):
        payload = super()._pf_hardcase_grader(request, context).model_dump(mode="json")
        method = (context.get("reference_policy") or {}).get("required_method")
        if method:
            payload["route_check"] = {"divergent_route": True, "rederivation_md": "another method"}
            for row in payload["criterion_evidence"]:
                if row["criterion_id"] in method["criterion_ids"]:
                    row["points_awarded"] = 0.0
                    row["evidence"] = f"the answer does not use {method['name']}"
            payload["rubric_score"] = int(sum(row["points_awarded"] for row in payload["criterion_evidence"]))
        return request.result_model.model_validate(payload)


def test_the_production_path_enforces_a_required_method_without_a_quote(tmp_path):
    """Cell 5 along the production path: the method criterion stays failed on
    a divergent route although no step is quoted (neither PF-c's gate, on the
    checkable case, nor the unlocated rule unassesses it); the paired items
    without a required method pass on the same answer."""

    vault = _vault(tmp_path)
    report = run_hardcases(vault, routes=["aware"], caps=CAPS, clients={"aware": MethodAwareGrader()})
    raw = report["by_route"]["aware"]["grader"]
    gate = report["gate"]["grader=aware"]
    for summary in (raw, gate):
        assert summary["required_method"]["enforced"]["count"] == summary["required_method"]["enforced"]["n"] == 2
        assert summary["required_method"]["fact_rejected"]["count"] == 0
        assert summary["wrong_rejection"]["count"] == 0
    per_case = report["per_case"]
    assert per_case["la-det-no-required-method-row-reduction"]["gate:aware"] == "correct"
    assert per_case["pr-at-least-one-six-no-required-method-complement"]["gate:aware"] == "correct"
    assert per_case["la-det-required-cofactor-by-row-reduction"]["gate:aware"] == "caught"
    assert per_case["pr-at-least-one-six-required-inclusion-exclusion-by-complement"]["gate:aware"] == "caught"
