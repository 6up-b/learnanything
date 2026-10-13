"""Stage evsi-single-family-unbounded: the single-family EVSI study without its
25-check bound, the bound's stops counted, and the old-vs-new comparison tool.

Synthetic Eedi files stand in for the real releases (never committed): the
single-family test's bank and answers, and the multi-family test's 40-question
bank (more questions than the old bound).
"""

from __future__ import annotations

import copy
import json
from dataclasses import replace

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.evsi_calibration import compare as C
from learnloop.evsi_calibration import experiments as X
from learnloop.evsi_calibration import policies as P
from learnloop.evsi_calibration.eedi import load_eedi_2024, load_neurips_2020
from learnloop.evsi_calibration.response_fit import FitSettings, fit_response_model
from learnloop.evsi_calibration.simulate import SimulationSettings, run_simulation
from learnloop.evsi_calibration.world import build_scenarios
from tests.test_evsi_calibration_sim import write_eedi_2020, write_eedi_2024
from tests.test_evsi_multisim import _write_long_bank


@pytest.fixture(scope="module")
def eedi(tmp_path_factory):
    root = tmp_path_factory.mktemp("eedi-unbounded")
    bank_dir = write_eedi_2024(root / "eedi-2024")
    responses = load_neurips_2020(write_eedi_2020(root / "eedi-2020"), task="3_4", cache_dir=root / "cache",
                                  with_dates=True)
    fit = fit_response_model(responses, settings=FitSettings(bootstrap=50))
    long_bank = load_eedi_2024(_write_long_bank(root / "long-bank", 40))
    return {"root": root, "bank_dir": bank_dir, "bank": load_eedi_2024(bank_dir), "fit": fit,
            "long_scenarios": build_scenarios(long_bank, fit)}


def _tiny(**changes):
    settings = X.ExperimentSettings(
        learners=10, sensitivity_learners=8, workers=1, regime_consistencies=(None, 0.9), regime_repairs=(3.0, 30.0),
        unresolved_encounters=(6.0, 12.0), bootstrap=20,
        sweeps=("evsi.PERTURBATION_DELTA", "robust_composition.ROBUST_QUANTILE"), draw_count=4,
    )
    return replace(settings, **changes)


def _generous(**policy):
    # A check costs nothing, so the EIG rule continues while any information is
    # left: only the bank (or a bound) ends the episode.
    return SimulationSettings(learners=3, policies=("eig_no_gate",),
                              policy=P.PolicySettings(lambda_time=0.0, burden_cost=0.0, draw_count=4, **policy))


def test_the_single_family_path_defaults_to_no_count_bound(eedi, monkeypatch):
    assert P.PolicySettings().safety_bound is None
    assert SimulationSettings().policy.safety_bound is None
    assert X.ExperimentSettings().safety_bound is None
    assert X.ExperimentSettings().reference_bound == X.REFERENCE_BOUND == 25
    # Every run the study makes (main, regimes, sweeps, Part C) is unbounded.
    seen = []
    real = X.run_simulation

    def recording(world, settings, *, learners=None):
        seen.append(settings.policy.safety_bound)
        return real(world, settings, learners=learners)

    monkeypatch.setattr(X, "run_simulation", recording)
    report = X.run_experiments(eedi["bank"], eedi["fit"], _tiny())
    assert seen and all(bound is None for bound in seen)
    assert report["settings"]["safety_bound"] is None and report["policy_defaults"]["safety_bound"] is None
    block = report["count_bound"]
    assert block["applied_bound"] is None and block["reference_bound"] == 25
    assert {cell["section"] for cell in block["cells"]} == {"main", "regimes", "sensitivity", "part_c"}
    assert all(cell["count_bound_stops"] == 0 for cell in block["cells"])
    # An explicit bound reaches every run.
    seen.clear()
    X.run_experiments(eedi["bank"], eedi["fit"], _tiny(safety_bound=25, sweeps=("evsi.PERTURBATION_DELTA",)))
    assert seen and all(bound == 25 for bound in seen)
    # On a bank longer than the old bound, an episode runs past 25 checks and
    # ends by its rule or when the subject's questions run out.
    scenarios = eedi["long_scenarios"]
    assert len(scenarios[0].questions) == 40
    run = run_simulation(scenarios, _generous())
    assert run.episodes and all(e.checks > 25 for e in run.episodes)
    for e, spec in zip(run.episodes, run.learners):
        assert e.checks <= 40 - len(spec.history) and e.stop_reason in ("robust_eig_stop", "no_question_left")


def test_an_explicit_bound_still_stops_and_the_unbounded_run_counts_its_stops(eedi):
    scenarios = eedi["long_scenarios"]
    unbounded = run_simulation(scenarios, _generous())
    bounded = run_simulation(scenarios, _generous(safety_bound=25))
    assert all(e.checks == 25 and e.stop_reason == "safety_bound" for e in bounded.episodes)
    # Common random numbers: the unbounded run's counts are exactly the
    # bounded run's stops, and the bounded run counts its own the same way.
    free, capped = X.bound_counts(unbounded.episodes), X.bound_counts(bounded.episodes)
    stops = sum(1 for e in bounded.episodes if e.stop_reason == "safety_bound")
    assert free["count_bound_stops"] == 0 and free["reference_bound_stops"] == stops == len(bounded.episodes)
    assert free["reference_bound_censored"] == stops and free["max_checks"] > 25
    assert capped["count_bound_stops"] == capped["reference_bound_stops"] == stops
    assert capped["reference_bound_censored"] == 0 and capped["max_checks"] == 25
    # An episode its own rule stops at exactly the bound is the bound's in name
    # only; one the bank ends there is not the bound's at all.
    named = [replace(bounded.episodes[0], checks=25, stop_reason="robust_eig_stop"),
             replace(bounded.episodes[0], checks=25, stop_reason="no_question_left")]
    assert X.bound_counts(named) == {
        "episodes": 2, "max_checks": 25, "ran_out_of_questions": 1, "count_bound_stops": 0,
        "reference_bound_stops": 1, "reference_bound_censored": 0}


def test_cli_simulate_passes_an_explicit_bound_through(eedi, tmp_path):
    fit_path = tmp_path / "fit.json"
    fit_path.write_text(json.dumps(eedi["fit"].as_dict()))
    result = CliRunner().invoke(app, [
        "evsi", "simulate", "--eedi-2024", str(eedi["bank_dir"]), "--fit", str(fit_path),
        "--output", str(tmp_path / "out"), "--quick", "--learners", "10", "--sensitivity-learners", "10",
        "--workers", "1", "--safety-bound", "3", "--json",
    ])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output.strip().splitlines()[-1])
    assert payload["status"] == "ok" and payload["safety_bound"] == 3
    report = json.loads((tmp_path / "out" / "simulation_report.json").read_text())
    assert report["settings"]["safety_bound"] == 3 and report["count_bound"]["applied_bound"] == 3
    assert all(cell["max_checks"] <= 3 for cell in report["count_bound"]["cells"])
    assert C.applied_bound(report) == 3


def _scrambled(value):
    """Every dict's keys reversed and every list of records reversed (pairs
    such as CIs and rankings keep their order): what a different writer, or a
    JSON round trip with sorted keys, may hand the comparison."""

    if isinstance(value, dict):
        return {key: _scrambled(value[key]) for key in reversed(list(value))}
    if isinstance(value, list):
        items = [_scrambled(item) for item in value]
        return list(reversed(items)) if items and all(isinstance(item, dict) for item in items) else items
    return value


def test_the_comparison_tools_ordering_is_stable(eedi):
    new = X.run_experiments(eedi["bank"], eedi["fit"], _tiny())
    # The stored run as it was: bounded at 25 (recorded only in its defaults).
    old = copy.deepcopy(new)
    old["settings"].pop("safety_bound")
    old["policy_defaults"]["safety_bound"] = 25
    old.pop("count_bound")
    assert C.applied_bound(old) == 25 and C.applied_bound(new) is None

    baseline = C.compare_reports(old, new)
    for variant in (_scrambled(new), json.loads(json.dumps(new, sort_keys=True))):
        again = C.compare_reports(_scrambled(old), variant)
        assert json.dumps(again) == json.dumps(baseline)  # order-sensitive equality
    assert C.render_markdown(C.compare_reports(_scrambled(old), _scrambled(new))) == C.render_markdown(baseline)

    # The study's order, not the report's: sections, regimes, arms, claims.
    rows = baseline["cells"]
    sections = [row["key"][0] for row in rows]
    assert sections == sorted(sections, key=C.SECTIONS.index)
    regimes = list(dict.fromkeys(row["cell"] for row in rows if row["key"][0] == "regimes"))
    assert regimes == ["fitted/3", "fitted/30", "0.9/3", "0.9/30"]
    for cell in dict.fromkeys(row["cell"] for row in rows):
        arms = [row["policy"] for row in rows if row["cell"] == cell]
        assert arms == sorted(arms, key=P.ALL_POLICIES.index)
    assert [claim["id"] for claim in baseline["claims"]] == [claim.id for claim in C.CLAIMS]
    assert [row["policy"] for row in baseline["bound"]["cells"] if row["key"] == ["main", "hand_set"]] == \
        list(P.ALL_POLICIES)

    # Identical runs: nothing moved, every arm untouched by the bound, every
    # stored stop reason that could say so agrees.
    assert baseline["summary"]["rows"]["moved_beyond_ci"] == 0 and baseline["summary"]["rank_changes"] == []
    assert baseline["attribution"]["checked"] and baseline["attribution"]["untouched_differing"] == []
    assert baseline["bound"]["checks"]["disagrees"] == 0 and baseline["bound"]["checks"]["agrees"] > 0

    # A number that leaves its CI is flagged where it is, and only there.
    moved = copy.deepcopy(new)
    row = next(r for r in moved["regimes"] if r["consistency"] == 0.9 and r["repair_minutes"] == 30.0)
    arm = row["policies"]["eig_no_gate"]
    arm["mean_total_minutes"] = arm["total_minutes_ci95"][1] + 5.0
    comparison = C.compare_reports(old, moved)
    flagged = [(r["cell"], r["policy"]) for r in comparison["cells"] if r["status"] == "moved_beyond_ci"]
    assert flagged == [("0.9/30", "eig_no_gate")]
    assert comparison["attribution"]["untouched_differing"] == ["0.9/30 eig_no_gate"]
    claim = next(c for c in comparison["claims"] if c["id"] == "S3g")
    assert claim["beyond_ci"] == ["eig_no_gate 0.9/30"]


def test_the_stored_reports_own_stop_reasons_are_read_only_where_complete():
    report = {
        "main": {"eedi_fitted": {"eig_no_gate": {"episodes": {"stop_reasons": {"robust_eig_stop": 398,
                                                                                "safety_bound": 2}}},
                                 "evsi": {"episodes": {"stop_reasons": {"lcb_evsi_below_minutes_cost": 400}}}}},
        "regimes": [{"consistency": "fitted", "repair_minutes": 3.0, "policies": {
            "evsi": {"stop_reasons": {"a": 100, "b": 100, "c": 100, "d": 99}},
            "eig": {"stop_reasons": {"a": 100, "b": 100, "c": 100, "d": 100}}}}],
    }
    assert C.recorded_bound_stops(report, ("main", "eedi_fitted"), "eig_no_gate", 400) == (2, "recorded")
    assert C.recorded_bound_stops(report, ("main", "eedi_fitted"), "evsi", 400) == (0, "recorded")
    # Four reasons kept, one episode unaccounted for: a fifth may be the bound's.
    assert C.recorded_bound_stops(report, ("regimes", "fitted", 3.0), "evsi", 400) == (None, "truncated")
    assert C.recorded_bound_stops(report, ("regimes", "fitted", 3.0), "eig", 400) == (0, "recorded")
    assert C.recorded_bound_stops(report, ("part_c", "fitted", 6.0), "evsi", 400) == (None, "not_recorded")
