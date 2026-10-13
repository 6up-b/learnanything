"""EVSI calibration Part A: the Eedi loaders, the response fit and the simulation.

Synthetic Eedi files stand in for the real releases (never committed): a 2024
bank of one subject whose distractors carry misconception labels, and 2020
answers generated from a planted latent class model, so the fit has a known
answer to recover.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.config.schema import ProbeEpisodeConfig
from learnloop.evsi_calibration import metrics as M
from learnloop.evsi_calibration import policies as P
from learnloop.evsi_calibration.eedi import OPTIONS, load_eedi_2024, load_neurips_2020
from learnloop.evsi_calibration.response_fit import FitSettings, ResponseFit, fit_response_model
from learnloop.evsi_calibration.simulate import SimulationSettings, draw_learners, loss_table_for, run_simulation
from learnloop.evsi_calibration.world import (
    HYP_KNOWS,
    HYP_OTHER,
    build_scenarios,
    eedi_row,
    hand_set_row,
    model_misfit,
    system_rows,
    with_truth,
)
from learnloop.scheduling import evsi as EV

SUBJECT = 33
#: Planted truth of the synthetic 2020 answers.
PLANTED_CONSISTENCY = 0.65


def write_eedi_2024(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "manifest.json").write_text(json.dumps({"sources": [
        {"name": "synthetic Eedi 2024", "version": "test", "licence": "test fixture"}]}))
    with (directory / "misconception_mapping.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["MisconceptionId", "MisconceptionName"])
        for mid, name in ((10, "adds before multiplying"), (11, "works left to right"), (12, "ignores brackets")):
            writer.writerow([mid, name])
    header = ["QuestionId", "ConstructId", "ConstructName", "SubjectId", "SubjectName", "CorrectAnswer",
              "QuestionText", "AnswerAText", "AnswerBText", "AnswerCText", "AnswerDText",
              "MisconceptionAId", "MisconceptionBId", "MisconceptionCId", "MisconceptionDId"]
    labels = [
        ("A", {"B": 10, "C": 11}), ("B", {"A": 10, "D": 12}), ("C", {"A": 11, "B": 12}),
        ("D", {"A": 10}), ("A", {"C": 11, "D": 12}), ("B", {"C": 10}), ("C", {"D": 11}), ("D", {"B": 12}),
    ]
    with (directory / "train.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for index, (correct, mis) in enumerate(labels):
            row = [index, 100 + index, "Order of operations", SUBJECT, "BIDMAS", correct, f"Q{index}",
                   "a", "b", "c", "d"]
            row += [f"{float(mis[o]):.1f}" if o in mis else "" for o in OPTIONS]
            writer.writerow(row)
    return directory


def write_eedi_2020(directory: Path, *, students: int = 6000, seed: int = 7) -> Path:
    """Six questions in one level-3 subject; two planted misconception triples."""

    meta = directory / "data" / "metadata"
    train = directory / "data" / "train_data"
    meta.mkdir(parents=True, exist_ok=True)
    train.mkdir(parents=True, exist_ok=True)
    with (meta / "subject_metadata.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["SubjectId", "Name", "ParentId", "Level"])
        writer.writerows([[3, "Maths", "NULL", 0], [32, "Number", 3, 1], [144, "Operations", 32, 2],
                          [SUBJECT, "BIDMAS", 144, 3]])
    correct = {q: 1 + (q % 4) for q in range(6)}
    designated = {q: 1 + ((q + 1) % 4) for q in range(6)}  # never the correct option
    with (meta / "question_metadata_task_3_4.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["QuestionId", "SubjectId"])
        for q in range(6):
            writer.writerow([q, f"[3, 32, 144, {SUBJECT}]"])
    rng = np.random.default_rng(seed)
    rows, dates = [], []
    answer_id = 0
    for user in range(students):
        cls = rng.choice(["knows", "mx", "my", "unsure"], p=[0.6, 0.15, 0.1, 0.15])
        for q in range(6):
            targeted = (cls == "mx" and q < 3) or (cls == "my" and q >= 3)
            if cls == "knows":
                probs = (0.9, 0.03, 0.07)
            elif targeted:
                probs = (0.2, PLANTED_CONSISTENCY, 0.15)
            else:
                probs = (0.35, 0.15, 0.5)
            category = rng.choice(3, p=probs)
            others = [o for o in range(1, 5) if o not in (correct[q], designated[q])]
            value = correct[q] if category == 0 else (designated[q] if category == 1 else int(rng.choice(others)))
            rows.append((q, user, answer_id, int(value == correct[q]), correct[q], value))
            dates.append((answer_id, f"2020-01-{1 + q:02d} 10:{user % 60:02d}:00.000"))
            answer_id += 1
    with (train / "train_task_3_4.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["QuestionId", "UserId", "AnswerId", "IsCorrect", "CorrectAnswer", "AnswerValue"])
        writer.writerows(rows)
    with (meta / "answer_metadata_task_3_4.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["AnswerId", "DateAnswered", "Confidence", "GroupId", "QuizId", "SchemeOfWorkId"])
        for aid, stamp in dates:
            writer.writerow([f"{aid}.0", stamp, "", 1, 1, ""])
    return directory


@pytest.fixture(scope="module")
def eedi(tmp_path_factory):
    root = tmp_path_factory.mktemp("eedi")
    bank_dir = write_eedi_2024(root / "eedi-2024")
    responses_dir = write_eedi_2020(root / "eedi-2020")
    responses = load_neurips_2020(responses_dir, task="3_4", cache_dir=root / "cache", with_dates=True)
    fit = fit_response_model(responses, settings=FitSettings(bootstrap=50))
    return {"bank_dir": bank_dir, "responses_dir": responses_dir, "bank": load_eedi_2024(bank_dir),
            "responses": responses, "fit": fit, "root": root}


def test_loaders_read_the_bank_and_the_answers(eedi):
    bank = eedi["bank"]
    assert len(bank.questions) == 8
    first = bank.questions[0]
    assert first.correct == "A" and first.misconception_by_option == {"B": "10", "C": "11"}
    assert first.distractors == ("B", "C", "D")
    assert first.options_for("10") == ("B",)
    responses = eedi["responses"]
    assert responses.rows == 6000 * 6
    assert responses.leaf_subject == {q: SUBJECT for q in range(6)}
    assert responses.answered_minute is not None and (responses.answered_minute >= 0).all()
    # The cache round-trips the same arrays.
    again = load_neurips_2020(eedi["responses_dir"], task="3_4", cache_dir=eedi["root"] / "cache", with_dates=True)
    assert np.array_equal(again.answer, responses.answer)


def test_the_fit_recovers_the_planted_consistency(eedi):
    fit: ResponseFit = eedi["fit"]
    assert len(fit.triples) == 2
    assert {tuple(sorted(t.questions)) for t in fit.triples} == {(0, 1, 2), (3, 4, 5)}
    consistency = fit.pooled["consistency"].median
    # Consistent, not exact: about 3,000 fit-half students per triple.
    assert abs(consistency - PLANTED_CONSISTENCY) < 0.08
    assert fit.pooled["knower_slip"].median == pytest.approx(0.10, abs=0.05)
    assert fit.pooled["holder_correct"].median == pytest.approx(0.20, abs=0.07)
    # Persistence: designated errors repeat more often after a designated error.
    assert fit.persistence["excess_repeat_rate"].median > 0.0
    # The fit serializes and reloads.
    again = ResponseFit.from_dict(json.loads(json.dumps(fit.as_dict())))
    assert again.pooled["consistency"].median == pytest.approx(consistency, abs=1e-4)


def test_rows_are_distributions_and_the_hand_set_vocabulary_is_read_not_copied(eedi):
    scenarios = build_scenarios(eedi["bank"], eedi["fit"])
    assert len(scenarios) == 1
    scenario = scenarios[0]
    assert scenario.hypotheses[0] == HYP_KNOWS and scenario.hypotheses[-1] == HYP_OTHER
    assert abs(sum(scenario.prior.values()) - 1.0) < 1e-9
    question = scenario.questions[0]
    for model in ("hand_set", "eedi_fitted"):
        rows = system_rows(model, scenario, question)
        for row in rows.values():
            assert abs(sum(row.values()) - 1.0) < 1e-9
    # A misconception's own labelled distractor dominates under the hand-set card:
    # the ordinal word "dominant" over "rare" (0.60 vs 0.04) after renormalizing.
    row = hand_set_row("mis:10", question)
    assert row["B"] == pytest.approx(0.6 / 0.72, abs=1e-9)
    fitted = eedi_row("mis:10", question, scenario.truth.values)
    assert fitted["B"] == pytest.approx(scenario.truth["consistency"], abs=1e-9)
    stronger = with_truth(scenarios, consistency=0.9)[0]
    assert eedi_row("mis:10", question, stronger.truth.values)["B"] == pytest.approx(0.9)
    misfit = model_misfit(scenarios, "hand_set")
    assert misfit["rows"] > 0 and misfit["p90"] >= misfit["median"]


def test_simulation_runs_every_policy_on_common_random_numbers(eedi, monkeypatch):
    scenarios = build_scenarios(eedi["bank"], eedi["fit"])
    calls = Counter()
    real = EV.rank_feasible

    def counting(*args, **kwargs):
        calls["rank_feasible"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(EV, "rank_feasible", counting)
    settings = SimulationSettings(learners=6, workers=1)
    run = run_simulation(scenarios, settings)
    assert calls["rank_feasible"] > 0  # the real EVSI selector chose (or stopped)
    assert len(run.episodes) == 6 * len(P.ALL_POLICIES)
    truths = {}
    for episode in run.episodes:
        truths.setdefault(episode.learner, set()).add(episode.truth)
    assert all(len(values) == 1 for values in truths.values())
    cap = ProbeEpisodeConfig().maximum_observations
    assert all(e.checks <= cap for e in run.episodes if e.policy in ("incumbent", "caps_only", "random", "max_entropy"))
    for record in run.checks:
        assert abs(sum(record.predicted.values()) - 1.0) < 1e-5  # rounded to 6 places
        assert 0.0 <= record.p_action_change <= 1.0 + 1e-9
    # Same learners, same answers: a rerun is identical.
    again = run_simulation(scenarios, settings, learners=draw_learners(scenarios, settings))
    assert [e.total_minutes for e in again.episodes] == [e.total_minutes for e in run.episodes]


def _episode_state(scenario, belief, *, observations, identical: bool):
    from learnloop.diagnosis import robust_composition as rc

    channel = P.identity_channel(OPTIONS)
    ensembles, objects = {}, {}
    for index, question in enumerate(scenario.questions[:3]):
        # Identical instruments (same rows, same context hash) have no robust
        # winner: the robust selector abstains on them.
        rows_question = scenario.questions[0] if identical else question
        ensemble = rc.build_ensemble(
            joint_alpha=channel, instrument_rows=system_rows("eedi_fitted", scenario, rows_question),
            calibration_model_hash="test", decision_context_hash="same" if identical else f"q{index}",
            draw_count=8, quantile=0.10, perturbation_concentration=40.0,
        )
        objects[question.question_id] = ensemble
        ensembles[question.question_id] = (ensemble.mean_member, tuple(ensemble.members))
    return P.EpisodeState(
        hypotheses=scenario.hypotheses, belief=dict(belief), remaining=sorted(ensembles),
        observations=observations, loss_table=loss_table_for(scenario, P.PolicySettings(), unresolved=0.0),
        ensembles=ensembles, ensemble_objects=objects, rng=np.random.default_rng(0),
        actions_by_hypothesis={h: ("continue" if h == HYP_KNOWS else f"route:{h}") for h in scenario.hypotheses},
    )


def test_the_incumbent_arm_includes_todays_robust_completion_gate(eedi):
    # Review F8: after the minimum independent observations, an unstable
    # posterior whose remaining instruments the robust selector cannot tell
    # apart ends the live episode (probe_episodes._robust_completion_override).
    # The incumbent arm does the same; the cap-only comparator keeps checking.
    scenario = build_scenarios(eedi["bank"], eedi["fit"])[0]
    belief = {h: 1.0 / len(scenario.hypotheses) for h in scenario.hypotheses}  # unstable, not action-equivalent
    minimum = ProbeEpisodeConfig().minimum_independent_observations
    settings = P.PolicySettings(draw_count=8)
    gated = _episode_state(scenario, belief, observations=minimum, identical=True)
    incumbent = P.decide("incumbent", gated, settings)
    assert (incumbent.action, incumbent.reason) == ("stop", "couldnt_reliably_distinguish")
    assert P.decide("caps_only", gated, settings).action == "measure"
    # Before the minimum the gate does not run, exactly as in serving.
    early = _episode_state(scenario, belief, observations=minimum - 1, identical=True)
    assert P.decide("incumbent", early, settings).action == "measure"
    # Distinguishable instruments: no abstention, the incumbent keeps measuring.
    distinct = _episode_state(scenario, belief, observations=minimum, identical=False)
    from learnloop.diagnosis import robust_composition as rc

    verdict = rc.evaluate_selection(
        candidates=[(q, distinct.ensemble_objects[q], 60.0) for q in distinct.remaining], posterior=belief)
    assert P.decide("incumbent", distinct, settings).action == ("stop" if verdict.abstained else "measure")


def test_each_response_world_simulates_histories_generated_in_that_world(eedi, monkeypatch):
    # Review F2: a stronger instrument changes how learners answered BEFORE the
    # episode too; reusing histories drawn under the fitted world misstates the
    # starting belief. Every simulated world runs on its own histories (same
    # seeds, so the learners and their uniforms stay common across worlds).
    from learnloop.evsi_calibration import experiments as X

    calls = []
    real = X.run_simulation

    def recording(world, settings, *, learners=None):
        calls.append((world, list(learners)))
        return real(world, settings, learners=learners)

    monkeypatch.setattr(X, "run_simulation", recording)
    settings = X.ExperimentSettings(
        learners=12, sensitivity_learners=10, workers=1, regime_consistencies=(None, 0.95), regime_repairs=(3.0,),
        unresolved_encounters=(6.0,), bootstrap=20, sweeps=("evsi.PERTURBATION_DELTA",), draw_count=4,
    )
    report = X.run_experiments(eedi["bank"], eedi["fit"], settings)
    base = SimulationSettings(learners=settings.learners, seed=settings.seed)
    fitted = {s.index: s.history for s in draw_learners(build_scenarios(eedi["bank"], eedi["fit"]), base)}
    differs = False
    for world, learners in calls:
        own = {s.index: s.history for s in draw_learners(world, base)}
        assert [s.history for s in learners] == [own[s.index] for s in learners]
        differs = differs or any(own[s.index] != fitted.get(s.index) for s in learners)
    assert differs  # the stronger world really did answer differently
    assert set(report["starting_belief"]) >= {"fitted", "0.95"}


def test_the_measured_loss_charges_unresolved_minutes_off_the_diagonal(eedi):
    scenario = build_scenarios(eedi["bank"], eedi["fit"])[0]
    plain = loss_table_for(scenario, P.PolicySettings(), unresolved=0.0)
    charged = loss_table_for(scenario, P.PolicySettings(), unresolved=2.5)
    mis = scenario.hypotheses[1]
    assert charged.loss(mis, "continue") == pytest.approx(plain.loss(mis, "continue") + 2.5)
    assert charged.loss(HYP_KNOWS, "continue") == 0.0
    assert charged.loss(mis, f"repair:{mis[4:]}") == 0.0


def test_metrics_reliability_tau_and_paired_differences():
    rng = np.random.default_rng(1)
    pairs = [(p, float(rng.random() < p)) for p in rng.random(4000)]
    table = M.reliability(pairs)
    assert table["ece"] < 0.05
    assert M.kendall_tau(["a", "b", "c"], ["a", "b", "c"]) == 1.0
    assert M.kendall_tau(["a", "b", "c"], ["c", "b", "a"]) == -1.0


def test_cli_simulate_quick_writes_a_report(eedi, tmp_path):
    fit_path = tmp_path / "fit.json"
    fit_path.write_text(json.dumps(eedi["fit"].as_dict()))
    result = CliRunner().invoke(app, [
        "evsi", "simulate", "--eedi-2024", str(eedi["bank_dir"]), "--fit", str(fit_path),
        "--output", str(tmp_path / "out"), "--quick", "--learners", "10", "--sensitivity-learners", "10",
        "--workers", "1", "--json",
    ])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output.strip().splitlines()[-1])
    assert payload["status"] == "ok"
    report = json.loads((tmp_path / "out" / "simulation_report.json").read_text())
    assert {"main", "regimes", "sensitivity", "part_c", "recommendations", "hand_set_implied"} <= set(report)
    assert set(report["main"]) == {"hand_set", "eedi_fitted"}


def test_cli_simulate_without_a_fit_needs_the_2020_answers(eedi, tmp_path):
    result = CliRunner().invoke(app, [
        "evsi", "simulate", "--eedi-2024", str(eedi["bank_dir"]), "--output", str(tmp_path / "out"), "--json",
    ])
    assert result.exit_code == 1
    assert json.loads(result.output)["status"] == "invalid"
