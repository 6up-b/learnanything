"""Stage evsi-single-family-unbounded: the single-family EVSI study without its
25-check bound, the bound's stops counted, and the old-vs-new comparison tool.

Synthetic Eedi files stand in for the real releases (never committed): the
single-family test's bank and answers, and the multi-family test's 40-question
bank (more questions than the old bound). The headline claims are checked on
``evsi_calibration_claims_v2.json``: the fields they read of the stored v2
report the calibration review quotes (aggregate simulation outputs only).
"""

from __future__ import annotations

import copy
import inspect
import json
from dataclasses import replace
from pathlib import Path

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.cli.evsi import evsi_simulate_command
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
        "--workers", "1", "--safety-bound", "3", "--reference-bound", "2", "--json",
    ])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output.strip().splitlines()[-1])
    assert payload["status"] == "ok" and payload["safety_bound"] == 3 and payload["reference_bound"] == 2
    report = json.loads((tmp_path / "out" / "simulation_report.json").read_text())
    assert report["settings"]["safety_bound"] == 3 and report["count_bound"]["applied_bound"] == 3
    assert report["settings"]["reference_bound"] == report["count_bound"]["reference_bound"] == 2
    assert all(cell["max_checks"] <= 3 for cell in report["count_bound"]["cells"])
    assert C.applied_bound(report) == 3
    # The CLI's default reference bound is the stored runs' bound.
    assert inspect.signature(evsi_simulate_command).parameters["reference_bound"].default == X.REFERENCE_BOUND


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


@pytest.fixture(scope="module")
def unbounded(eedi):
    """A tiny unbounded run (counting the stored runs' 25-check bound)."""

    return X.run_experiments(eedi["bank"], eedi["fit"], _tiny())


def _as_stored(report):
    """The same run as the stored report recorded it: bounded at 25 (in its
    defaults only), no count_bound."""

    old = copy.deepcopy(report)
    old["settings"].pop("safety_bound")
    old["settings"].pop("reference_bound")
    old["policy_defaults"]["safety_bound"] = 25
    old.pop("count_bound")
    return old


def _differing(comparison):
    return [(row["cell"], row["policy"]) for row in comparison["cells"] if row["status"] in C.DIFFERS]


def test_the_comparison_tools_ordering_is_stable(unbounded):
    new = unbounded
    old = _as_stored(new)
    assert C.applied_bound(old) == 25 and C.applied_bound(new) is None

    baseline = C.compare_reports(old, new)
    for variant in (_scrambled(new), json.loads(json.dumps(new, sort_keys=True))):
        again = C.compare_reports(_scrambled(old), variant)
        assert json.dumps(again) == json.dumps(baseline)  # order-sensitive equality
    assert C.render_markdown(C.compare_reports(_scrambled(old), _scrambled(new))) == C.render_markdown(baseline)

    # The study's order, not the report's: sections, regimes, arms, claims.
    rows = baseline["cells"]
    sections = [row["key"][0] for row in rows]
    assert sections == sorted(sections, key=C.SECTIONS.index) and "report" in sections
    regimes = list(dict.fromkeys(row["cell"] for row in rows if row["key"][0] == "regimes"))
    assert regimes == ["fitted/3", "fitted/30", "0.9/3", "0.9/30"]
    for cell in dict.fromkeys(row["cell"] for row in rows if row["key"][0] in C.CELL_SECTIONS):
        arms = [row["policy"] for row in rows if row["cell"] == cell and row["policy"] != C.CELL_ROW]
        assert arms == sorted(arms, key=P.ALL_POLICIES.index)
    assert [claim["id"] for claim in baseline["claims"]] == [claim.id for claim in C.CLAIMS]
    assert [row["policy"] for row in baseline["bound"]["cells"] if row["key"] == ["main", "hand_set"]] == \
        list(P.ALL_POLICIES)

    # Identical runs: nothing moved, every arm untouched by the bound, every
    # stored stop reason that could say so agrees.
    assert _differing(baseline) == [] and baseline["summary"]["rank_changes"] == []
    assert baseline["bound"]["relation"] == "bounded_vs_unbounded" and baseline["bound"]["reference_bound"] == 25
    assert baseline["attribution"]["checked"] and baseline["attribution"]["untouched_differing"] == []
    assert baseline["bound"]["checks"]["disagrees"] == 0 and baseline["bound"]["checks"]["agrees"] > 0

    # A number that leaves its CI is flagged where it is, and only there.
    moved = copy.deepcopy(new)
    row = next(r for r in moved["regimes"] if r["consistency"] == 0.9 and r["repair_minutes"] == 30.0)
    arm = row["policies"]["eig_no_gate"]
    arm["mean_total_minutes"] = arm["total_minutes_ci95"][1] + 5.0
    comparison = C.compare_reports(old, moved)
    flagged = [(r["cell"], r["policy"]) for r in comparison["cells"] if r["status"] == "moved_beyond_ci"]
    assert flagged == [("0.9/30", "eig_no_gate")] and _differing(comparison) == flagged
    assert comparison["attribution"]["untouched_differing"] == ["0.9/30 eig_no_gate"]
    claim = next(c for c in comparison["claims"] if c["id"] == "S3g")
    assert claim["beyond_ci"] == ["eig_no_gate 0.9/30"]


# -- F1 (Codex review): every recorded value is compared -------------------------------------------------------


def _leaves(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _leaves(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _leaves(child, path + (index,))
    else:
        yield path, value


def _kind(report, path):
    """One representative leaf per kind: list positions, arms, system models,
    worlds, swept parameters and stop reasons are instances of a kind."""

    instances = set(P.ALL_POLICIES) | set(C.SYSTEM_MODELS) | {"fitted", "0.7", "0.9"}
    instances |= set((report.get("sensitivity") or {}).get("parameters") or {})
    out = []
    for index, part in enumerate(path):
        generic = isinstance(part, int) or part in instances or (index and path[index - 1] == "stop_reasons")
        out.append("*" if generic else part)
    return tuple(out)


def _mutated(report, path, value):
    out = copy.deepcopy(report)
    target = out
    for part in path[:-1]:
        target = target[part]
    if isinstance(value, bool):
        changed = not value
    elif isinstance(value, (int, float)):
        changed = 1.5 if value != value else value + 1000.5  # NaN -> a number
    elif isinstance(value, str):
        changed = value + "?"
    else:
        changed = 1.5
    target[path[-1]] = changed
    return out


def test_every_recorded_value_is_compared(unbounded):
    new = unbounded
    old = _as_stored(new)

    # The Codex example: an untouched arm's member quantile moves, the arm is
    # flagged and the attribution names it.
    model, policy = next((m, p) for m, arms in new["main"].items() for p, block in arms.items()
                         if isinstance(block["value_of_checks"].get("member_quantile_minus_realized"), dict))
    moved = copy.deepcopy(new)
    moved["main"][model][policy]["value_of_checks"]["member_quantile_minus_realized"]["q10"] = 999.0
    comparison = C.compare_reports(old, moved)
    assert _differing(comparison) == [(f"main {model}", policy)]
    assert comparison["attribution"]["untouched_differing"] == [f"main {model} {policy}"]
    metric = next(m for r in comparison["cells"] if r["policy"] == policy and r["cell"] == f"main {model}"
                  for m in r["metrics"] if m["status"] in C.DIFFERS)
    assert metric["label"] == "value_of_checks.member_quantile_minus_realized.q10" and metric["new"] == 999.0

    # Every kind of recorded value, changed, is caught: the arms' blocks (bins,
    # quantiles, calibration, stop reasons, counts), the cells' own values, and
    # every report-level section. Only the metadata is left out (the header
    # shows it).
    kinds = {}
    for path, value in _leaves(new):
        kinds.setdefault(_kind(new, path), (path, value))
    assert len(kinds) > 150
    caught, metadata = [], []
    for path, value in kinds.values():
        differing = _differing(C.compare_reports(new, _mutated(new, path, value)))
        if path[0] in C.METADATA_KEYS:
            metadata.append(path)
            assert differing == [], path
        else:
            caught.append(path)
            assert differing, f"a change at {path} went unnoticed"
    sections = {path[0] for path in caught}
    assert {"main", "regimes", "sensitivity", "part_c", "fit", "bank", "misfit", "hand_set_implied",
            "starting_belief", "flagged_learners_by_world", "recommendations"} <= sections
    assert {path[0] for path in metadata} == set(C.METADATA_KEYS) & set(new)

    # A value present in one report only is a difference; a stop reason absent
    # from a record that keeps every reason is a count of 0.
    only_new = copy.deepcopy(new)
    only_new["main"]["hand_set"]["incumbent"]["episodes"]["new_measure"] = 0.5
    labels = {m["label"]: m["status"] for r in C.compare_reports(new, only_new)["cells"] for m in r["metrics"]}
    assert labels["episodes.new_measure"] == "changed"
    renamed = copy.deepcopy(new)
    reasons = renamed["main"]["hand_set"]["incumbent"]["episodes"]["stop_reasons"]
    first = next(iter(reasons))
    reasons[first] -= 1
    reasons["safety_bound"] = 1
    metrics = {m["label"]: m for r in C.compare_reports(renamed, new)["cells"] if r["cell"] == "main hand_set"
               and r["policy"] == "incumbent" for m in r["metrics"]}
    gone = metrics["episodes.stop_reasons.safety_bound"]
    assert (gone["old"], gone["new"], gone["status"]) == (1.0, 0.0, "moved_no_ci")


# -- F2 (Codex review): the bound's counts are the bound's only for the bound applied ----------------------------


def test_the_bound_attribution_needs_the_bound_the_other_report_applied(eedi, unbounded, tmp_path):
    bounded = X.run_experiments(eedi["bank"], eedi["fit"], _tiny(safety_bound=3))
    counted = X.run_experiments(eedi["bank"], eedi["fit"], _tiny(reference_bound=3))
    assert C.applied_bound(bounded) == 3 and unbounded["count_bound"]["reference_bound"] == 25

    # The Codex case: a 3-check run against an unbounded run that counted the
    # 25-check bound's stops. Those counts are not this bound's: unsupported,
    # and no arm is called untouched.
    comparison = C.compare_reports(bounded, unbounded)
    bound = comparison["bound"]
    assert (bound["relation"], bound["available"], bound["cells"]) == ("unsupported", False, [])
    assert "25-check bound" in bound["reason"] and "--reference-bound 3" in bound["reason"]
    assert comparison["attribution"] == {"checked": False, "reason": bound["reason"]}
    assert all(row["bound_stops"] is None and row["bound_censored"] is None for row in comparison["cells"])
    assert _differing(comparison)  # the 3-check bound binds in this world

    # The unbounded run that counted the 3-check bound's stops: they agree with
    # the bounded report's own stop reasons, and everything that moved is the
    # bound's (in either direction of the comparison).
    for old, new in ((bounded, counted), (counted, bounded)):
        comparison = C.compare_reports(old, new)
        bound, attributed = comparison["bound"], comparison["attribution"]
        assert bound["relation"] == "bounded_vs_unbounded" and bound["reference_bound"] == 3
        assert bound["total_stops"] > 0 and bound["total_censored"] > 0
        assert bound["checks"]["disagrees"] == 0 and bound["checks"]["agrees"] > 0
        assert attributed["checked"] and attributed["untouched_rows"] > 0
        assert attributed["untouched_differing"] == [] and attributed["renamed_only_differing"] == []
        touched = set(attributed["touched_rows"]) | set(attributed["renamed_only_rows"])
        assert {f"{cell} {policy}" for cell, policy in _differing(comparison)} <= touched
    # Bounded at 25 against the 3-check count: unsupported again.
    assert C.compare_reports(_as_stored(counted), counted)["bound"]["relation"] == "unsupported"

    # Two bounded reports, or a report without count_bound: unsupported. The
    # same bound in both: the bound explains nothing, so everything must match.
    other = copy.deepcopy(bounded)
    other["settings"]["safety_bound"] = 25
    assert C.compare_reports(bounded, other)["bound"]["relation"] == "unsupported"
    bare = copy.deepcopy(unbounded)
    bare.pop("count_bound")
    assert C.compare_reports(bounded, bare)["bound"]["relation"] == "unsupported"
    same = C.compare_reports(unbounded, counted)
    assert same["bound"]["relation"] == "same_bound" and same["attribution"]["checked"]
    assert same["attribution"]["untouched_differing"] == [] and same["attribution"]["untouched_rows"] == len(same["cells"])

    # The CLI says so too.
    paths = {}
    for name, report in (("bounded", bounded), ("unbounded", unbounded)):
        paths[name] = tmp_path / f"{name}.json"
        paths[name].write_text(json.dumps(report, default=str))
    result = CliRunner().invoke(app, ["evsi", "compare", "--old", str(paths["bounded"]), "--new",
                                      str(paths["unbounded"]), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output.strip().splitlines()[-1])
    assert payload["bound"]["relation"] == "unsupported" and payload["attribution"]["checked"] is False


# -- F3 (Codex review): each headline claim is its separate assertions -------------------------------------------

#: What the claims read of the stored v2 report (the run the calibration review
#: quotes), pruned to those fields: every assertion holds on it.
CLAIMS_V2 = Path(__file__).with_name("evsi_calibration_claims_v2.json")


@pytest.fixture(scope="module")
def stored():
    return json.loads(CLAIMS_V2.read_text())


def _regime(report, consistency, repair):
    return next(r for r in report["regimes"] if r["consistency"] == consistency and r["repair_minutes"] == repair)


def _arm(report, consistency, repair, policy):
    return _regime(report, consistency, repair)["policies"][policy]


def _swept(report, parameter, value, policy):
    rows = report["sensitivity"]["parameters"][parameter]["rows"]
    return next(r for r in rows if r["value"] == value)["policies"][policy]


def _part_c_row(report, consistency, encounters, policy):
    return next(r for r in report["part_c"]["rows"]
                if r["consistency"] == consistency and r["encounters"] == encounters and r["policy"] == policy)


def _set(target, key, value):
    target[key] = value


QUANTILE, DELTA, NAT = (C.QUANTILE, "evsi.PERTURBATION_DELTA", C.NAT)
CONCENTRATION = "robust_composition.INSTRUMENT_PERTURBATION_CONCENTRATION"
DRAWS = "robust_composition.ROBUST_DRAW_COUNT (simulation draws)"
BURDEN = "robust_composition.BURDEN_COST"

#: (claim, conclusion, a change to the stored numbers that falsifies it, the
#: other conclusions of the claim it necessarily falsifies too)
FALSIFIERS = (
    ("S2", "value_rules_stop", lambda r: _set(_arm(r, "fitted", 30.0, "evsi_lookahead"), "mean_checks", 0.5), ()),
    ("S2", "value_rules_beat_incumbent", lambda r: _set(_arm(r, "fitted", 10.0, "eig"), "mean_total_minutes", 9.0), ()),
    ("S3a", "evsi_above_incumbent", lambda r: _set(_arm(r, 0.9, 30.0, "evsi"), "mean_total_minutes", 13.0), ()),
    ("S3b", "lcb_only_below_evsi", lambda r: _set(_arm(r, 0.9, 30.0, "evsi_lcb_only"), "mean_total_minutes", 18.0), ()),
    ("S3c", "lookahead_below_lcb_only",
     lambda r: _set(_arm(r, 0.9, 30.0, "evsi_lookahead"), "mean_total_minutes", 12.6), ()),
    ("S3c", "lookahead_below_incumbent", lambda r: _set(_arm(r, 0.9, 30.0, "incumbent"), "mean_total_minutes", 10.5), ()),
    ("S3d", "caps_only_below_lookahead", lambda r: _set(_arm(r, 0.9, 30.0, "caps_only"), "mean_total_minutes", 11.0), ()),
    # Being the best rule there implies being below the lookahead.
    ("S3d", "eig_no_gate_below_lookahead",
     lambda r: _set(_arm(r, 0.9, 30.0, "eig_no_gate"), "mean_total_minutes", 10.9), ("eig_no_gate_best",)),
    ("S3d", "eig_no_gate_best", lambda r: _set(_arm(r, 0.9, 30.0, "caps_only"), "mean_total_minutes", 9.5), ()),
    ("S3e", "lookahead_best", lambda r: _set(_arm(r, 0.9, 10.0, "caps_only"), "mean_total_minutes", 4.9), ()),
    ("S3f", "gate_costs_minutes", lambda r: _set(_arm(r, 0.9, 30.0, "caps_only"), "mean_total_minutes", 14.0), ()),
    ("S3g", "worst_at_fitted_3", lambda r: _set(_arm(r, "fitted", 3.0, "caps_only"), "mean_total_minutes", 9.0), ()),
    ("S3g", "best_at_07_30", lambda r: _set(_arm(r, 0.7, 30.0, "caps_only"), "mean_total_minutes", 15.0), ()),
    ("S3g", "best_at_09_30", lambda r: _set(_arm(r, 0.9, 30.0, "caps_only"), "mean_total_minutes", 9.5), ()),
    ("S4a", "best_at_10", lambda r: _set(_swept(r, NAT, 5.0, "eig_no_gate"), "mean_total_minutes", 4.7), ()),
    ("S4a", "10_beats_60",
     lambda r: _set(_swept(r, NAT, 10.0, "eig_no_gate")["difference_vs_current"], "ci95", [-2.26, 0.1]), ()),
    ("S4a", "gate_flat", lambda r: _set(_swept(r, NAT, 1.0, "eig")["difference_vs_current"], "mean_difference", 0.3), ()),
    ("S4b", "above_every_ci",
     lambda r: _set(_regime(r, 0.9, 30.0)["value_of_checks"]["incumbent"], "minutes_per_nat_ci95", [8.9, 61.0]), ()),
    ("S4b", "at_least_4x",
     lambda r: _set(_regime(r, 0.9, 30.0)["value_of_checks"]["caps_only"], "minutes_per_nat", 20.0), ()),
    ("S4b", "gate_stops_most",
     lambda r: _set(r["main"]["eedi_fitted"]["eig"]["episodes"]["stop_reasons"], "abstain", 100), ()),
    ("S5a", "within_noise_at_025",
     lambda r: _set(_swept(r, QUANTILE, 0.25, "evsi_lookahead")["difference_vs_current"], "ci95", [-0.38, -0.01]), ()),
    ("S5b", "at_most_003",
     lambda r: _set(_swept(r, DELTA, 0.35, "evsi")["difference_vs_current"], "mean_difference", -0.04), ()),
    ("S5c", "no_minutes_effect",
     lambda r: _set(_swept(r, DRAWS, 128, "evsi_lcb_only")["difference_vs_current"], "ci95", [0.05, 0.45]), ()),
    ("S5c", "concentration_moves_rankings",
     lambda r: [_set(row["policies"]["evsi"], "ranking_tau_vs_current", 1.0)
                for row in r["sensitivity"]["parameters"][CONCENTRATION]["rows"]], ()),
    ("S5c", "draws_move_rankings",
     lambda r: [_set(row["policies"]["evsi"], "ranking_tau_vs_current", 1.0)
                for row in r["sensitivity"]["parameters"][DRAWS]["rows"]], ()),
    ("S5d", "never_lowers",
     lambda r: _set(_swept(r, BURDEN, 0.5, "evsi_lookahead")["difference_vs_current"], "mean_difference", -0.1), ()),
    ("S5e", "both_below",
     lambda r: _set(_swept(r, C.REPAIR_SWEEP, 10.0, "evsi_lcb_only")["difference_vs_current"], "ci95",
                    [-1.1, 0.05]), ()),
    ("S5f", "both_above",
     lambda r: _set(_swept(r, C.CHECK_SWEEP, 1.5, "evsi_lookahead")["difference_vs_current"], "ci95",
                    [-0.01, 0.71]), ()),
    ("S6", "never_costs", lambda r: _set(_part_c_row(r, "fitted", 6.0, "evsi_lcb_only")["difference"], "ci95",
                                         [0.01, 0.18]), ()),
    ("S6", "pays_from_12_at_09", lambda r: _set(_part_c_row(r, 0.9, 24.0, "evsi_lookahead")["difference"], "ci95",
                                                [-1.99, 0.1]), ()),
    ("S6", "nothing_below_12", lambda r: _set(_part_c_row(r, 0.9, 6.0, "evsi_lcb_only")["difference"], "ci95",
                                              [-0.25, -0.01]), ()),
)


def _verdicts(stored, report):
    return {(claim["id"], a["id"]): a["holds_new"] for claim in C.compare_claims(stored, report)
            for a in claim["assertions"]}


def test_every_assertion_of_every_claim_holds_on_the_stored_run(stored):
    verdicts = _verdicts(stored, stored)
    assert verdicts and all(verdict is True for verdict in verdicts.values())
    kinds = [a.kind for claim in C.CLAIMS for a in claim.assertions]
    assert kinds.count("conclusion") == len(FALSIFIERS) and kinds.count("figure") > 30


def test_the_codex_case_no_longer_certifies_s4b(stored):
    # Every relevant minutes per nat at 50 [49, 51], and no agreement-gate
    # abstention: 60 is no longer 4-500x them, and the gate stops nothing.
    report = copy.deepcopy(stored)
    for row in report["regimes"]:
        for policy in ("incumbent", "caps_only"):
            row["value_of_checks"][policy].update(minutes_per_nat=50.0, minutes_per_nat_ci95=[49.0, 51.0])
    report["main"]["eedi_fitted"]["eig"]["episodes"]["stop_reasons"].pop("abstain")
    claim = next(c for c in C.compare_claims(stored, report) if c["id"] == "S4b")
    verdicts = {a["id"]: a["holds_new"] for a in claim["assertions"]}
    assert verdicts["above_every_ci"] is True  # it is what it says: 51 < 60
    assert verdicts["at_least_4x"] is False and verdicts["gate_stops_most"] is False
    assert claim["holds_new"] is False and claim["conclusion_changed"] is True
    assert claim["figures_new"] is False and len(claim["figures_changed"]) == 3


@pytest.mark.parametrize("claim_id, target, change, implied", FALSIFIERS,
                         ids=[f"{c}-{a}" for c, a, _f, _i in FALSIFIERS])
def test_each_conclusion_is_falsified_on_its_own(stored, claim_id, target, change, implied):
    report = copy.deepcopy(stored)
    change(report)
    verdicts = _verdicts(stored, report)
    assert verdicts[(claim_id, target)] is False
    claim = next(c for c in C.CLAIMS if c.id == claim_id)
    for assertion in claim.assertions:
        if assertion.kind == "conclusion" and assertion.id not in (target, *implied):
            assert verdicts[(claim_id, assertion.id)] is True, assertion.id
    for implied_id in implied:
        assert verdicts[(claim_id, implied_id)] is False
    compared = next(c for c in C.compare_claims(stored, report) if c["id"] == claim_id)
    assert compared["holds_old"] is True and compared["holds_new"] is False and compared["conclusion_changed"]


def test_each_stated_figure_is_checked_at_its_precision(stored):
    for claim in C.CLAIMS:
        values = dict(claim.quantities(stored))
        for assertion in (a for a in claim.assertions if a.kind == "figure"):
            low, high = assertion.bounds
            assert assertion.check(values) is True
            point, ci = values[assertion.label]
            for outside in (high + max(high - low, 1e-3), low - max(high - low, 1e-3)):
                if assertion.part == "point":
                    changed = (outside, ci)
                else:
                    changed = (point, [outside, ci[1]] if assertion.part == "low" else [ci[0], outside])
                assert assertion.check({**values, assertion.label: changed}) is False, (claim.id, assertion.id)
            # Other assertions do not read this quantity's point.
    # S3g's 8.44 is the one figure the unbounded rerun moved past its precision.
    s3g = next(c for c in C.CLAIMS if c.id == "S3g")
    values = dict(s3g.quantities(stored))
    eight = next(a for a in s3g.assertions if a.id == "eig_no_gate fitted/3")
    assert eight.check({**values, "eig_no_gate fitted/3": (8.46, None)}) is False


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
