"""The full Part A study behind ``learnloop evsi simulate``.

1. **Fit** the response model to Eedi 2020 (:mod:`.response_fit`) and compare
   it with what today's hand-set constants imply.
2. **Main comparison**: every policy on the fitted world, with the system
   running today's ``hand_set`` vocabulary and with the ``eedi_fitted`` model.
3. **Regimes**: instrument strength (Eedi's fitted consistency, 0.7, 0.9) by
   stakes (repair minutes 3 = ``DEFAULT_INTERVENTION_MINUTES``, 10, 30). Eedi's
   multiple choice is a weak instrument; the owner's free-text checks are
   plausibly stronger, so the study shows where the rules change behaviour.
4. **Sensitivity** of rankings and stopping to each hand-set number, at a
   regime where measuring matters (in the fitted regime every value-based
   rule stops at once, so a sweep there would show nothing).
5. **Part C**: what an unresolved misconception truly costs (Eedi's excess
   repeat-error rate x encounters x minutes per error) against a system that
   ignores it and one that charges it.
6. **Recommendations** with their evidence and confidence.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from learnloop.config.schema import ProbeConfig
from learnloop.diagnosis import robust_composition as rc
from learnloop.diagnosis.probes import BRIDGE_SENSITIVITY, BRIDGE_SPECIFICITY
from learnloop.evsi_calibration import metrics as M
from learnloop.evsi_calibration import policies as P
from learnloop.evsi_calibration.eedi import EediBank
from learnloop.evsi_calibration.response_fit import ResponseFit
from learnloop.evsi_calibration.simulate import (
    SIMULATION_VERSION,
    SimulationSettings,
    draw_learners,
    run_simulation,
    with_policy,
)
from learnloop.evsi_calibration.world import (
    HYP_KNOWS,
    HYP_OTHER,
    build_scenarios,
    hand_set_row,
    misconception_hypothesis,
    model_misfit,
    with_truth,
)
from learnloop.scheduling import action_loss as AL
from learnloop.scheduling import evsi as EV

EXPERIMENTS_VERSION = "evsi_calibration_experiments_v1"


@dataclass(frozen=True)
class ExperimentSettings:
    learners: int = 400
    sensitivity_learners: int = 300
    seed: int = 20261012
    workers: int = 8
    regime_consistencies: tuple[float | None, ...] = (None, 0.7, 0.9)
    regime_repairs: tuple[float, ...] = (3.0, 10.0, 30.0)
    #: Where measuring matters (see module docstring).
    sensitivity_consistency: float = 0.9
    sensitivity_repair: float = 10.0
    #: Part C: encounters an unresolved misconception meets before it is caught
    #: some other way, and minutes per repeated error. Neither is in Eedi.
    unresolved_encounters: tuple[float, ...] = (3.0, 6.0, 12.0, 24.0)
    minutes_per_repeat_error: float = 2.0
    bootstrap: int = 400
    #: Restrict the sensitivity sweep to these SWEEPS names (None: all).
    sweeps: tuple[str, ...] | None = None
    #: Ensemble draws per check (simulation default 32; --quick uses fewer).
    draw_count: int = 32

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


#: Swept hand-set parameters: name -> (PolicySettings field, current value, grid).
SWEEPS: dict[str, tuple[str, float, tuple[float, ...]]] = {
    "evsi.PERTURBATION_DELTA": ("perturbation_delta", EV.PERTURBATION_DELTA, (0.05, 0.10, 0.15, 0.25, 0.35)),
    "robust_composition.ROBUST_QUANTILE": ("robust_quantile", rc.ROBUST_QUANTILE, (0.05, 0.10, 0.25, 0.50)),
    "robust_composition.INSTRUMENT_PERTURBATION_CONCENTRATION": (
        "instrument_concentration", rc.INSTRUMENT_PERTURBATION_CONCENTRATION, (4.0, 10.0, 40.0, 160.0)
    ),
    "robust_composition.ROBUST_DRAW_COUNT (simulation draws)": ("draw_count", 32, (16, 32, 64, 128)),
    "robust_composition.BURDEN_COST": ("burden_cost", rc.BURDEN_COST, (0.0, 0.5, 1.0, 2.0)),
    "action_loss.DEFAULT_INTERVENTION_MINUTES (repair minutes)": (
        "repair_minutes", AL.DEFAULT_INTERVENTION_MINUTES, (1.5, 3.0, 6.0, 10.0, 20.0)
    ),
    "check minutes (probe burden; causal selector default 1.5)": ("check_minutes", 1.0, (0.5, 1.0, 1.5, 3.0)),
    "robust_composition.VALUE_PER_NAT_MINUTES": (
        "value_per_nat_minutes", rc.VALUE_PER_NAT_MINUTES, (1.0, 2.5, 5.0, 10.0, 20.0, 40.0, 60.0, 120.0)
    ),
}
#: Which policies each sweep exercises (the EIG path alone reads the nat scale).
SWEEP_POLICIES: dict[str, tuple[str, ...]] = {
    "robust_composition.VALUE_PER_NAT_MINUTES": ("eig", "eig_no_gate"),
}
DEFAULT_SWEEP_POLICIES = ("evsi", "evsi_lcb_only", "evsi_lookahead")


def hand_set_implied(bank: EediBank, scenarios: Sequence[Any]) -> dict[str, Any]:
    """What today's constants imply for the quantities Eedi measures."""

    targeted, knows_correct, other_designated, other_correct = [], [], [], []
    for scenario in scenarios:
        for question in scenario.questions:
            for misconception in scenario.misconceptions:
                options = question.options_for(misconception)
                if options:
                    row = hand_set_row(misconception_hypothesis(misconception), question)
                    targeted.append(sum(row[o] for o in options))
            row = hand_set_row(HYP_KNOWS, question)
            knows_correct.append(row[question.correct])
            row = hand_set_row(HYP_OTHER, question)
            other_correct.append(row[question.correct])
            labelled = list(question.misconception_by_option)
            if labelled:
                other_designated.append(float(np.mean([row[o] for o in labelled])))
    irt = ProbeConfig().irt

    def sigmoid(x: float) -> float:
        return 1.0 / (1.0 + np.exp(-x))

    return {
        "consistency": {
            "contrast_card_dominant_normalized": round(float(np.median(targeted)), 4) if targeted else None,
            "probe.irt.err_low_frac": irt.err_low_frac,
            "probes._BRIDGE_SENSITIVITY": BRIDGE_SENSITIVITY,
        },
        "false_alarm": {
            "contrast_card_other_or_unknown_signature": round(float(np.median(other_designated)), 4)
            if other_designated else None,
            "probe.irt.unfamiliar_error_leak": irt.unfamiliar_error_leak,
            "1 - probes._BRIDGE_SPECIFICITY": round(1.0 - BRIDGE_SPECIFICITY, 4),
        },
        "knower_slip": {
            "contrast_card_robust_initial_grasp": round(1.0 - float(np.median(knows_correct)), 4),
            "probe.irt.theta_mastered P(low) at b=0": round(1.0 - float(sigmoid(irt.theta_mastered - irt.cut_mid)), 4),
        },
        "unsure_correct": {
            "contrast_card_other_or_unknown": round(float(np.median(other_correct)), 4),
            "probe.irt.theta_unfamiliar P(high) at b=0": round(float(sigmoid(irt.theta_unfamiliar - irt.cut_high)), 4),
        },
        "instrument_perturbation_concentration": rc.INSTRUMENT_PERTURBATION_CONCENTRATION,
    }


def _policy_rows(run: Any, *, seed: int, draws: int) -> dict[str, Any]:
    summary = M.summarize(run.checks, run.episodes, seed=seed, draws=draws)
    return summary


def _compact(summary: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for policy, blocks in summary.items():
        e = blocks["episodes"]
        out[policy] = {
            "mean_checks": e.get("mean_checks"),
            "mean_total_minutes": e.get("mean_total_minutes"),
            "total_minutes_ci95": e.get("total_minutes_ci95"),
            "correct_action_rate": e.get("correct_action_rate"),
            "mean_wasted_minutes": e.get("mean_wasted_minutes"),
            "stop_reasons": dict(list((e.get("stop_reasons") or {}).items())[:4]),
        }
    return out


def _first_rankings(run: Any, policy: str) -> dict[int, tuple[str, ...]]:
    return {e.learner: e.first_ranking for e in run.episodes if e.policy == policy and e.first_ranking}


def run_experiments(
    bank: EediBank,
    fit: ResponseFit,
    settings: ExperimentSettings,
    *,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    say = progress or (lambda message: None)
    started = time.time()
    scenarios = build_scenarios(bank, fit)
    if not scenarios:
        raise ValueError("no simulation scenario: the 2024 bank and the fit share no usable subject")
    base = SimulationSettings(
        learners=settings.learners, seed=settings.seed, workers=settings.workers,
        policy=P.PolicySettings(draw_count=settings.draw_count),
    )
    learners = draw_learners(scenarios, base)
    report: dict[str, Any] = {
        "version": EXPERIMENTS_VERSION,
        "simulation_version": SIMULATION_VERSION,
        "settings": settings.as_dict(),
        "policy_defaults": P.PolicySettings().as_dict(),
        "fit": {
            "pooled": {k: v.as_dict() for k, v in fit.pooled.items()},
            "persistence": {k: v.as_dict() for k, v in fit.persistence.items()},
            "consistency_concentration": fit.consistency_concentration,
            "source": dict(fit.source),
            "triples": len(fit.triples),
            "subjects_with_own_fit": len(fit.by_subject),
        },
        "bank": {
            "questions": len(bank.questions),
            "misconceptions": len(bank.misconception_names),
            "source_hash": bank.source_hash,
            "manifest_sources": list((bank.manifest or {}).get("sources") or []),
            "scenarios": len(scenarios),
            "scenarios_with_subject_fit": sum(1 for s in scenarios if s.truth.source == "subject_fit"),
            "mean_hypotheses": round(float(np.mean([len(s.hypotheses) for s in scenarios])), 2),
            "mean_questions": round(float(np.mean([len(s.questions) for s in scenarios])), 2),
            "flagged_learners": len(learners),
        },
        "hand_set_implied": hand_set_implied(bank, scenarios),
        "misfit": {model: model_misfit(scenarios, model) for model in ("hand_set", "eedi_fitted")},
    }

    # 2. main comparison
    say("main comparison")
    main: dict[str, Any] = {}
    for model in ("hand_set", "eedi_fitted"):
        run = run_simulation(scenarios, replace(base, system_model=model), learners=learners)
        main[model] = _policy_rows(run, seed=settings.seed, draws=settings.bootstrap)
    report["main"] = main

    # 3. regimes
    say("regimes")
    regimes: list[dict[str, Any]] = []
    for consistency in settings.regime_consistencies:
        world = scenarios if consistency is None else with_truth(scenarios, consistency=consistency)
        for repair in settings.regime_repairs:
            run = run_simulation(
                world,
                with_policy(replace(base, system_model="eedi_fitted"), repair_minutes=repair),
                learners=learners,
            )
            summary = M.summarize(run.checks, run.episodes, seed=settings.seed, draws=settings.bootstrap)
            regimes.append({
                "consistency": "fitted" if consistency is None else consistency,
                "repair_minutes": repair,
                "policies": _compact(summary),
                "value_of_checks": {
                    p: {k: summary[p]["value_of_checks"].get(k) for k in (
                        "mean_predicted_evsi_point", "mean_realized_value", "model_minutes_per_nat",
                        "minutes_per_nat", "minutes_per_nat_ci95", "member_quantile_minus_realized")}
                    for p in summary
                },
            })
    report["regimes"] = regimes

    # 4. sensitivity
    say("sensitivity")
    world = with_truth(scenarios, consistency=settings.sensitivity_consistency)
    sens_base = with_policy(
        replace(base, system_model="eedi_fitted", learners=settings.sensitivity_learners),
        repair_minutes=settings.sensitivity_repair,
    )
    sens_learners = learners[: settings.sensitivity_learners]
    sensitivity: dict[str, Any] = {
        "regime": {"consistency": settings.sensitivity_consistency, "repair_minutes": settings.sensitivity_repair},
        "parameters": {},
    }
    for name, (field_name, current, grid) in SWEEPS.items():
        if settings.sweeps is not None and name not in settings.sweeps:
            continue
        policies = SWEEP_POLICIES.get(name, DEFAULT_SWEEP_POLICIES)
        runs: dict[float, Any] = {}
        for value in sorted(set(grid) | {current}):
            # The world stays fixed: a sweep moves what the system assumes, and
            # the true repair and check minutes stay the regime's.
            arm = replace(
                with_policy(sens_base, **{field_name: value}),
                policies=policies,
                truth_repair_minutes=settings.sensitivity_repair,
                truth_check_minutes=sens_base.policy.check_minutes,
            )
            if field_name == "draw_count":
                arm = replace(arm, policy=replace(arm.policy, draw_count=int(value)))
            runs[value] = run_simulation(world, arm, learners=sens_learners)
        rows = []
        for value, run in sorted(runs.items()):
            row: dict[str, Any] = {"value": value, "current": value == current, "policies": {}}
            for policy in policies:
                episodes = [e for e in run.episodes if e.policy == policy]
                base_episodes = [e for e in runs[current].episodes if e.policy == policy]
                taus = []
                base_rank = _first_rankings(runs[current], policy)
                for learner, ranking in _first_rankings(run, policy).items():
                    if learner in base_rank:
                        tau = M.kendall_tau(base_rank[learner], ranking)
                        if tau is not None:
                            taus.append(tau)
                summary = M.episode_summary(episodes, np.random.default_rng(settings.seed), settings.bootstrap)
                row["policies"][policy] = {
                    "mean_total_minutes": summary["mean_total_minutes"],
                    "total_minutes_ci95": summary["total_minutes_ci95"],
                    "mean_checks": summary["mean_checks"],
                    "correct_action_rate": summary["correct_action_rate"],
                    "first_decision_measures": round(
                        float(np.mean([e.checks > 0 for e in episodes])), 4) if episodes else None,
                    "ranking_tau_vs_current": round(float(np.mean(taus)), 4) if taus else None,
                    "difference_vs_current": M.paired_difference(
                        base_episodes, episodes, seed=settings.seed, draws=settings.bootstrap),
                    "stop_reasons": dict(list(summary["stop_reasons"].items())[:3]),
                }
            rows.append(row)
        sensitivity["parameters"][name] = {"field": field_name, "current": current, "rows": rows}
    report["sensitivity"] = sensitivity

    # 5. Part C
    say("part C")
    excess = fit.persistence.get("excess_repeat_rate")
    part_c: dict[str, Any] = {
        "excess_repeat_rate": excess.as_dict() if excess is not None else None,
        "minutes_per_repeat_error": settings.minutes_per_repeat_error,
        "rows": [],
    }
    if excess is not None:
        for consistency in (None, settings.sensitivity_consistency):
            world_c = scenarios if consistency is None else with_truth(scenarios, consistency=consistency)
            for encounters in settings.unresolved_encounters:
                true_u = float(excess.median) * encounters * settings.minutes_per_repeat_error
                arms = {}
                for label, system_u in (("minutes_only", 0.0), ("measured_unresolved", true_u)):
                    arm = with_policy(
                        replace(base, system_model="eedi_fitted", truth_unresolved_minutes=true_u,
                                policies=("evsi_lcb_only", "evsi_lookahead", "caps")),
                        unresolved_minutes=system_u,
                    )
                    arms[label] = run_simulation(world_c, arm, learners=learners)
                for policy in ("evsi_lcb_only", "evsi_lookahead"):
                    left = [e for e in arms["minutes_only"].episodes if e.policy == policy]
                    right = [e for e in arms["measured_unresolved"].episodes if e.policy == policy]
                    part_c["rows"].append({
                        "consistency": "fitted" if consistency is None else consistency,
                        "encounters": encounters,
                        "true_unresolved_minutes": round(true_u, 4),
                        "policy": policy,
                        "minutes_only_total": round(float(np.mean([e.total_minutes for e in left])), 4),
                        "measured_total": round(float(np.mean([e.total_minutes for e in right])), 4),
                        "minutes_only_checks": round(float(np.mean([e.checks for e in left])), 4),
                        "measured_checks": round(float(np.mean([e.checks for e in right])), 4),
                        "difference": M.paired_difference(left, right, seed=settings.seed, draws=settings.bootstrap),
                    })
    report["part_c"] = part_c
    report["recommendations"] = recommendations(report)
    report["elapsed_seconds"] = round(time.time() - started, 1)
    return report


def _best_value(parameter: Mapping[str, Any], policy: str) -> dict[str, Any] | None:
    rows = [r for r in parameter["rows"] if policy in r["policies"] and r["policies"][policy]["mean_total_minutes"] is not None]
    if not rows:
        return None
    best = min(rows, key=lambda r: (r["policies"][policy]["mean_total_minutes"], abs(r["value"] - parameter["current"])))
    diff = best["policies"][policy]["difference_vs_current"]
    ci = diff.get("ci95") or [0.0, 0.0]
    return {
        "value": best["value"],
        "mean_total_minutes": best["policies"][policy]["mean_total_minutes"],
        "difference_vs_current": diff.get("mean_difference"),
        "ci95": ci,
        "distinguishable": bool(ci and (ci[1] < 0 or ci[0] > 0)),
    }


def recommendations(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Structured recommendations; the review file renders and argues them."""

    out: list[dict[str, Any]] = []
    fit = report["fit"]["pooled"]
    implied = report["hand_set_implied"]
    out.append({
        "parameter": "response model: consistency P(signature | holds misconception)",
        "current": implied["consistency"],
        "eedi": fit["consistency"],
        "recommendation": "treat the vocabulary as a prior only; replace with per-family fitted values from the "
                          "owner's own probe outcomes (the Dirichlet counts already kept per family)",
        "confidence": "high for Eedi multiple choice; low for transfer to free text",
    })
    out.append({
        "parameter": "response model: false alarm P(signature | does not hold it)",
        "current": implied["false_alarm"],
        "eedi": fit["unsure_designated"],
        "confidence": "high for Eedi multiple choice; low for transfer",
    })
    out.append({
        "parameter": "response model: knower slip",
        "current": implied["knower_slip"],
        "eedi": fit["knower_slip"],
        "confidence": "medium (the knows class includes partial knowers)",
    })
    misfit = report["misfit"]["eedi_fitted"]
    out.append({
        "parameter": "evsi.PERTURBATION_DELTA",
        "current": EV.PERTURBATION_DELTA,
        "evidence": {"eedi_fitted_row_misfit": misfit, "hand_set_row_misfit": report["misfit"]["hand_set"]},
        "recommended": misfit.get("p90"),
        "confidence": "medium: sized to the measured per-question error of a calibrated model",
    })
    out.append({
        "parameter": "robust_composition.INSTRUMENT_PERTURBATION_CONCENTRATION",
        "current": rc.INSTRUMENT_PERTURBATION_CONCENTRATION,
        "eedi_between_item_concentration": report["fit"]["consistency_concentration"],
        "confidence": "medium",
    })
    for name, parameter in report["sensitivity"]["parameters"].items():
        for policy in (SWEEP_POLICIES.get(name) or DEFAULT_SWEEP_POLICIES):
            best = _best_value(parameter, policy)
            if best is not None:
                out.append({"parameter": name, "policy": policy, "current": parameter["current"], "best_in_sweep": best})
    return out


__all__ = ["ExperimentSettings", "run_experiments", "recommendations", "SWEEPS"]
