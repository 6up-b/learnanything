"""EVSI multi-family study (stage evsi-multisim): families, fits, simulation, analysis.

Synthetic Eedi files stand in for the real releases (never committed): the
single-family test's 2024 bank and 2020 answers (two planted misconception
triples in one subject), plus a planted hidden Markov data set for the
learning family.
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import replace

import numpy as np
import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.evsi_calibration import families as F
from learnloop.evsi_calibration import multifamily as MF
from learnloop.evsi_calibration import multisim as MS
from learnloop.evsi_calibration import policies as P
from learnloop.evsi_calibration.eedi import load_eedi_2024, load_neurips_2020
from learnloop.evsi_calibration.family_data import (
    GAP_LATER,
    GAP_SAME_SESSION,
    TripleData,
    build_subject_data,
    build_triple_data,
    is_fit,
    is_held_out,
)
from learnloop.evsi_calibration.family_fit import (
    FamilyFits,
    FamilyFitSettings,
    fit_families,
    fit_lca,
    fit_lta,
)
from learnloop.evsi_calibration.response_fit import FitSettings, fit_response_model
from learnloop.evsi_calibration.simulate import SimulationSettings, loss_table_for, run_simulation
from learnloop.evsi_calibration.world import HYP_KNOWS, HYP_OTHER, build_scenarios, hand_set_row
from tests.test_evsi_calibration_sim import SUBJECT, write_eedi_2020, write_eedi_2024

FAST = FamilyFitSettings(lca_iterations=300, cdm_iterations=150, nrm_iterations=40, lta_iterations=80,
                         bootstrap=30, workers=1)


@pytest.fixture(scope="module")
def eedi(tmp_path_factory):
    root = tmp_path_factory.mktemp("eedi-multi")
    bank_dir = write_eedi_2024(root / "eedi-2024")
    responses_dir = write_eedi_2020(root / "eedi-2020")
    responses = load_neurips_2020(responses_dir, task="3_4", cache_dir=root / "cache", with_dates=True)
    single = fit_response_model(responses, settings=FitSettings(bootstrap=50))
    triples = build_triple_data(responses, single.triples)
    subjects = build_subject_data(responses, [t.split(held_out=False) for t in triples])
    fits = fit_families(triples, subjects, FAST, source={"test": True})
    bank = load_eedi_2024(bank_dir)
    return {"root": root, "bank_dir": bank_dir, "responses_dir": responses_dir, "bank": bank,
            "single": single, "triples": triples, "subjects": subjects, "fits": fits}


def test_the_splits_are_disjoint_and_the_roles_and_order_are_read_from_the_answers(eedi):
    triple = eedi["triples"][0]
    fit, held = triple.split(held_out=False), triple.split(held_out=True)
    assert fit.n > 0 and held.n > 0
    assert not set(fit.users.tolist()) & set(held.users.tolist())
    assert is_fit(fit.users).all() and is_held_out(held.users).all()
    assert (triple.users % 2 == 1).all()  # even users selected the triples
    roles = triple.role_options()
    assert ((roles == 0) == (triple.options == np.asarray(triple.correct)[None, :])).all()
    assert ((roles == 1) == (triple.options == np.asarray(triple.designated)[None, :])).all()
    order, gaps = triple.time_order()
    assert sorted(order[0].tolist()) == [0, 1, 2]
    # The synthetic dates put the questions a day apart: every gap is "later".
    assert (gaps == GAP_LATER).all()
    subject = eedi["subjects"][0]
    assert subject.attributes == 2 and subject.items == 6
    assert ((subject.options > 0).sum(axis=1) >= 2).all()


def test_every_family_beats_the_marginal_on_held_out_students(eedi):
    validation = eedi["fits"].validation
    assert validation["triples"] == 2
    families = validation["families"]
    for name in ("lca", "cdm", "nrm", "lta"):
        block = families[name]
        assert block["nll_gain_vs_marginal"] > 0.0, name
        assert block["adequate"], name
        assert block["log_loss_three"] < families["marginal"]["log_loss_three"]
        distractor = block["distractor"]
        assert 0.0 <= distractor["mean_predicted_designated_share"] <= 1.0
    # The fits serialize and reload.
    again = FamilyFits.from_dict(json.loads(json.dumps(eedi["fits"].as_dict())))
    assert set(again.cdm) == set(eedi["fits"].cdm) and set(again.nrm) == set(eedi["fits"].nrm)
    assert np.allclose(again.lta.transitions, eedi["fits"].lta.transitions, atol=1e-5)


def test_the_cdm_and_nrm_find_the_planted_misconception_signal(eedi):
    fits = eedi["fits"]
    cdm = next(iter(fits.cdm.values()))
    summary = cdm.summary()
    # Planted: holders pick the designated distractor 65% of the time, others 3-15%.
    assert summary["consistency"] > summary["unsure_designated"] + 0.2
    assert summary["knower_slip"] < 0.3
    for nrm in fits.nrm.values():
        assert nrm.params[:, 4].mean() > 0.3  # the designated choice rises with the trait


def _planted_learning(n: int, seed: int, learn: float) -> TripleData:
    """Three items answered in one session; holders resolve with probability
    ``learn`` after each encounter."""

    rng = np.random.default_rng(seed)
    emission = {0: (0.9, 0.03, 0.07), 1: (0.15, 0.7, 0.15), 2: (0.35, 0.15, 0.5)}
    options = np.zeros((n, 3), dtype=np.int8)
    minutes = np.zeros((n, 3), dtype=np.int64)
    correct, designated = (1, 2, 3), (2, 3, 4)
    for i in range(n):
        state = int(rng.choice(3, p=[0.5, 0.3, 0.2]))
        order = rng.permutation(3)
        for position, item in enumerate(order):
            category = int(rng.choice(3, p=emission[state]))
            others = [o for o in (1, 2, 3, 4) if o not in (correct[item], designated[item])]
            options[i, item] = (correct[item] if category == 0 else designated[item] if category == 1
                                else int(rng.choice(others)))
            minutes[i, item] = 1000 + 5 * position
            if state == 1 and rng.random() < learn:
                state = 0
    users = np.arange(n) * 8 + 1  # fit split
    return TripleData(0, 33, (1, 2, 3), correct, designated, users, options, minutes)


def test_the_learning_family_recovers_a_planted_within_session_transition():
    triple = _planted_learning(6000, 3, learn=0.3)
    order, gaps = triple.time_order()
    assert (gaps == GAP_SAME_SESSION).all()
    lca = {fit_index: fit for fit_index, fit in enumerate(fit_lca([triple], FAST))}
    fit = fit_lta([triple], {0: lca[0]}, replace(FAST, lta_iterations=300))
    holds_to_knows = fit.transitions[GAP_SAME_SESSION][1, 0]
    assert holds_to_knows == pytest.approx(0.3, abs=0.1)
    static = fit_lta([_planted_learning(6000, 4, learn=0.0)], {0: lca[0]}, replace(FAST, lta_iterations=300))
    assert static.transitions[GAP_SAME_SESSION][1, 0] < 0.1


def test_strength_moves_only_holders_in_every_family(eedi):
    families = F.build_families(eedi["bank"], eedi["fits"])
    scenarios = build_scenarios(eedi["bank"], eedi["fits"].lca)
    for name in ("lca", "cdm", "nrm", "lta"):
        base = F.implied_quantities(families[name], scenarios)
        strong = F.implied_quantities(families[name].with_strength(0.9), scenarios)
        assert strong["consistency"] > base["consistency"] + 0.1, name
        assert strong["consistency"] == pytest.approx(0.9, abs=0.08), name
        assert strong["false_alarm"] == pytest.approx(base["false_alarm"], abs=1e-6), name
        assert strong["knower_slip"] == pytest.approx(base["knower_slip"], abs=1e-6), name
        assert strong["prevalence"]["knows"] == pytest.approx(base["prevalence"]["knows"], abs=1e-6), name


def test_family_rows_and_priors_are_distributions_and_needs_name_hypotheses(eedi):
    families = F.build_families(eedi["bank"], eedi["fits"])
    scenario = build_scenarios(eedi["bank"], eedi["fits"].lca)[0]
    rng = np.random.default_rng(5)
    for name, family in families.items():
        model = family.scenario_model(scenario)
        prior = model.system_prior()
        assert set(prior) == set(scenario.hypotheses)
        assert sum(prior.values()) == pytest.approx(1.0)
        for question in scenario.questions:
            for row in model.system_rows(question).values():
                assert sum(row.values()) == pytest.approx(1.0)
        for _ in range(20):
            state = model.draw_state(rng)
            needs = model.needs(state)
            assert needs and set(needs) <= set(scenario.hypotheses), name
            assert sum(model.row(state, scenario.questions[0]).values()) == pytest.approx(1.0)


def test_the_learning_scenario_moves_holders_and_keeps_a_distribution(eedi):
    families = F.build_families(eedi["bank"], eedi["fits"])
    scenario = build_scenarios(eedi["bank"], eedi["fits"].lca)[0]
    transitions = np.array([[0.9, 0.05, 0.05], [0.3, 0.6, 0.1], [0.2, 0.1, 0.7]])
    model = F.LearningScenario(families["lca"].scenarios_by_subject[scenario.subject_id], transitions)
    holder = next(h for h in scenario.hypotheses if h.startswith("mis:"))
    distribution = model.next_distribution(holder)
    assert sum(distribution.values()) == pytest.approx(1.0)
    assert distribution[HYP_KNOWS] == pytest.approx(0.3)
    assert distribution[holder] == pytest.approx(0.6)
    misconceptions = [h for h in scenario.hypotheses if h.startswith("mis:")]
    from_other = model.next_distribution(HYP_OTHER)
    assert sum(from_other[m] for m in misconceptions) == pytest.approx(0.1)
    assert model.transition(holder, 0.0) in distribution


def test_true_loss_is_the_loss_table_for_one_need_and_charges_each_unaddressed_need(eedi):
    scenario = build_scenarios(eedi["bank"], eedi["fits"].lca)[0]
    table = loss_table_for(scenario, P.PolicySettings(repair_minutes=7.0), unresolved=2.0)
    for h in scenario.hypotheses:
        for a in table.actions:
            assert MS.true_loss((h,), a, repair_minutes=7.0, unresolved=2.0) == pytest.approx(table.loss(h, a))
    m1, m2 = [h for h in scenario.hypotheses if h.startswith("mis:")][:2]
    repair_1 = f"repair:{m1[4:]}"
    # Repairing one of two held misconceptions leaves the other's repair and its unresolved cost.
    assert MS.true_loss((m1, m2), repair_1, repair_minutes=7.0, unresolved=2.0) == pytest.approx(9.0)
    assert MS.true_loss((m1, m2), "continue", repair_minutes=7.0, unresolved=2.0) == pytest.approx(18.0)


def test_the_family_loop_reproduces_the_single_family_loop_for_the_latent_class_family(eedi):
    scenarios = tuple(build_scenarios(eedi["bank"], eedi["fits"].lca))
    families = F.build_families(eedi["bank"], eedi["fits"])
    policy = P.PolicySettings(draw_count=6)
    for system, model in (("family", "eedi_fitted"), ("hand_set", "hand_set")):
        multi = MS.run_family_simulation(MS.World(families["lca"], scenarios),
                                         MS.MultiSimSettings(learners=8, system=system, policy=policy,
                                                             policies=P.ALL_POLICIES))
        single = run_simulation(list(scenarios), SimulationSettings(learners=8, system_model=model, policy=policy))
        assert [(e.policy, e.learner, e.total_minutes, e.checks, e.final_action) for e in multi.episodes] == \
            [(e.policy, e.learner, e.total_minutes, e.checks, e.final_action) for e in single.episodes]
        assert [(c.question_id, c.realized, c.truth_log_gain) for c in multi.checks] == \
            [(c.question_id, c.realized, c.truth_log_gain) for c in single.checks]


def test_every_family_and_a_cross_system_run_all_policies(eedi):
    scenarios = tuple(build_scenarios(eedi["bank"], eedi["fits"].lca))
    families = F.build_families(eedi["bank"], eedi["fits"])
    systems = {name: families[name] for name in F.FAMILY_NAMES}
    for name in ("cdm", "nrm", "lta_reveal"):
        world = MS.World(families[name], scenarios, systems=systems)
        run = MS.run_family_simulation(world, MS.MultiSimSettings(learners=6, system="lca",
                                                                  policy=P.PolicySettings(draw_count=4)))
        assert len(run.episodes) == 6 * len(P.ALL_POLICIES + P.SUCCESSOR_POLICIES)
        for episode in run.episodes:
            assert episode.total_minutes >= episode.check_minutes - 1e-9
        again = MS.run_family_simulation(world, MS.MultiSimSettings(learners=6, system="lca",
                                                                    policy=P.PolicySettings(draw_count=4)))
        assert [e.total_minutes for e in again.episodes] == [e.total_minutes for e in run.episodes]


def _state(scenario, belief, settings):
    from learnloop.diagnosis import robust_composition as rc

    ensembles, objects = {}, {}
    for index, question in enumerate(scenario.questions[:4]):
        ensemble = rc.build_ensemble(
            joint_alpha=P.identity_channel(("A", "B", "C", "D")),
            instrument_rows={h: hand_set_row(h, question) for h in scenario.hypotheses},
            calibration_model_hash="test", decision_context_hash=f"q{index}", draw_count=8,
            quantile=0.10, perturbation_concentration=40.0,
        )
        objects[question.question_id] = ensemble
        ensembles[question.question_id] = (ensemble.mean_member, tuple(ensemble.members))
    from learnloop.evsi_calibration.world import route_for

    return P.EpisodeState(
        hypotheses=scenario.hypotheses, belief=dict(belief), remaining=sorted(ensembles), observations=0,
        loss_table=loss_table_for(scenario, settings, unresolved=0.0), ensembles=ensembles,
        ensemble_objects=objects, rng=np.random.default_rng(0),
        actions_by_hypothesis={h: route_for(h) for h in scenario.hypotheses},
    )


def test_the_successor_arm_values_with_the_nat_scale_when_no_decision_is_at_stake(eedi):
    # voi_stopping.value_candidates: when every hypothesis with posterior mass
    # routes to one repair nothing is at stake, so the robust EIG times
    # VALUE_PER_NAT_MINUTES decides; the incumbent's highest-EIG instrument is
    # served when it pays.
    from learnloop.diagnosis import robust_composition as rc

    scenario = build_scenarios(eedi["bank"], eedi["fits"].lca)[0]
    rest = (1.0 - 0.95) / (len(scenario.hypotheses) - 1)
    belief = {h: (0.95 if h == HYP_KNOWS else rest) for h in scenario.hypotheses}
    one_repair = {h: "continue" for h in scenario.hypotheses}

    def single_route(settings):
        state = _state(scenario, belief, settings)
        state.actions_by_hypothesis = dict(one_repair)
        return state

    generous = P.PolicySettings(value_per_nat_minutes=1.0e6)
    state = single_route(generous)
    decision = P.decide("voi_successor", state, generous)
    best = max(sorted(state.remaining),
               key=lambda q: rc.expected_information_gain(state.ensembles[q][0], state.belief))
    assert (decision.action, decision.question_id) == ("measure", best)
    assert decision.reason == "value_pays:eig_value"
    stingy = P.PolicySettings(value_per_nat_minutes=0.0)
    decision = P.decide("voi_successor", single_route(stingy), stingy)
    assert (decision.action, decision.reason) == ("stop", "value_of_information_stop:eig_value")
    # Review F6 on the successor: with the real routes the same near-sure
    # belief is at stake (its support routes to several repairs), so robust
    # EVSI values it, not the nat scale, unless rank_feasible abstains.
    at_stake = P.decide("voi_successor", _state(scenario, belief, generous), generous)
    method = at_stake.reason.split(":", 1)[1]
    assert method == "robust_evsi" or method.startswith("eig_value:evsi_")
    if method == "robust_evsi":
        assert P.decide("voi_successor", _state(scenario, belief, stingy), stingy).reason == at_stake.reason
    # The proposed package never reads the nat scale.
    assert P.decide("voi_proposed", _state(scenario, belief, generous), generous).reason == \
        P.decide("voi_proposed", _state(scenario, belief, stingy), stingy).reason


def test_the_successor_arms_lift_the_episode_maximum_onto_value(eedi):
    # serving/voi-stopping's episode_maximum_binds: while the site is on, the
    # episode's maximum_observations no longer ends it; the incumbent's does.
    from learnloop.config.schema import ProbeEpisodeConfig

    scenario = build_scenarios(eedi["bank"], eedi["fits"].lca)[0]
    belief = {h: 1.0 / len(scenario.hypotheses) for h in scenario.hypotheses}
    settings = P.PolicySettings()
    maximum = ProbeEpisodeConfig().maximum_observations

    def at_maximum():
        state = _state(scenario, belief, settings)
        state.observations = maximum
        return state

    assert P.decide("incumbent", at_maximum(), settings).reason == "observation_budget_exhausted"
    assert P.decide("caps_only", at_maximum(), settings).reason == "observation_budget_exhausted"
    for policy in P.SUCCESSOR_POLICIES:
        assert P.decide(policy, at_maximum(), settings).reason != "observation_budget_exhausted"
    lifted = at_maximum()
    bounded = replace(settings, safety_bound=25)  # an explicit bound still stops
    lifted.observations = bounded.safety_bound
    assert P.decide("voi_successor", lifted, bounded).reason == "safety_bound"
    unbounded = settings  # no bound by default
    assert unbounded.safety_bound is None
    lifted.observations = 10_000
    assert P.decide("eig_no_gate", lifted, replace(unbounded, value_per_nat_minutes=1.0e6)).action == "measure"


def test_each_ablation_puts_back_exactly_one_piece_of_the_successor(eedi):
    from learnloop.config.schema import ProbeEpisodeConfig

    scenario = build_scenarios(eedi["bank"], eedi["fits"].lca)[0]
    hypotheses = scenario.hypotheses
    mis = [h for h in hypotheses if h.startswith("mis:")]
    beliefs = [
        {h: 1.0 / len(hypotheses) for h in hypotheses},
        {h: (0.5 if h in (HYP_KNOWS, mis[0]) else 0.0) + 1e-3 for h in hypotheses},
        {h: (0.95 if h == HYP_KNOWS else 0.05 / (len(hypotheses) - 1)) for h in hypotheses},
    ]
    config = ProbeEpisodeConfig()
    settings = P.PolicySettings(repair_minutes=30.0)
    for raw in beliefs:
        total = sum(raw.values())
        belief = {h: v / total for h, v in raw.items()}
        for observations in (0, 2):
            def state():
                st = _state(scenario, belief, settings)
                st.observations = observations
                return st

            proposed = P.decide("voi_proposed", state(), settings)
            if P._cap_stop(state(), config, budget=False) is None:
                # The top-value variant is the lookahead rule inside the stops;
                # the package measures exactly when it does (serving aside).
                top = P.decide("voi_p_top_value", state(), settings)
                look = P.decide_lookahead(state(), settings)
                assert (top.action, top.question_id) == (look.action, look.question_id)
                assert proposed.action == top.action
                one_step = P.decide("voi_p_one_step", state(), settings)
                assert one_step.action == P.decide_evsi(state(), settings, obey_abstention=False).action
                single = P.decide_evsi(state(), settings)
                fallback = P.decide("voi_p_with_fallback", state(), settings)
                if single.verdict == "abstain":
                    assert "eig_value:evsi_" in fallback.reason
                else:
                    assert (fallback.action, fallback.question_id) == (proposed.action, proposed.question_id)
            gated = P.decide("voi_p_with_gate", state(), settings)
            if P._incumbent_stop(state(), settings, config, budget=False) is None:
                assert gated == proposed
            else:
                assert gated.action == "stop"


def _random_beliefs(hypotheses, n, seed):
    rng = np.random.default_rng(seed)
    return [{h: float(v) for h, v in zip(hypotheses, rng.dirichlet(np.full(len(hypotheses), 0.7)))}
            for _ in range(n)]


def test_the_package_with_every_piece_put_back_is_the_successor(eedi):
    # Codex review F1: the package once served rank_feasible's top-ranked check
    # while the successor serves the incumbent's highest-EIG one when it pays,
    # an undocumented fourth change. Now the package shares the successor's
    # gate and serving rule: with the gate, the fallback and no lookahead put
    # back it IS the successor, decision for decision, and the top-value
    # serving is its own arm.
    scenario = build_scenarios(eedi["bank"], eedi["fits"].lca)[0]
    hypotheses = scenario.hypotheses
    beliefs = _random_beliefs(hypotheses, 25, 0) + [
        {h: 1.0 / len(hypotheses) for h in hypotheses},
        {h: (0.95 if h == HYP_KNOWS else 0.05 / (len(hypotheses) - 1)) for h in hypotheses},
    ]
    served_apart = 0
    for belief in beliefs:
        for repair in (3.0, 10.0, 30.0):
            settings = P.PolicySettings(repair_minutes=repair)
            for observations in (0, 1, 2, 5):
                def state():
                    st = _state(scenario, belief, settings)
                    st.observations = observations
                    return st

                assert P.decide_package(state(), settings, gate=True, fallback=True, lookahead=False) == \
                    P.decide_successor(state(), settings)
                proposed = P.decide("voi_proposed", state(), settings)
                top = P.decide("voi_p_top_value", state(), settings)
                assert proposed.action == top.action
                served_apart += proposed.question_id != top.question_id
    assert served_apart > 0

    # The review's counterexample shape, without abstention: two checks pay,
    # the highest-EIG one is not rank_feasible's top-ranked one.
    found = None
    for belief in _random_beliefs(hypotheses, 200, 1):
        settings = P.PolicySettings(repair_minutes=10.0)
        st = _state(scenario, belief, settings)
        gate = P._lcb_value_gate(st, settings)
        highest = P._highest_eig(st)
        verdict = P._rank(st, settings, P._prefilter(st, settings)).verdict
        if len(gate.paying) >= 2 and highest in gate.paying and gate.top != highest and verdict == "measure":
            found = (belief, settings, highest, gate.top)
            break
    assert found is not None
    belief, settings, highest, top_ref = found
    assert P.decide("voi_successor", _state(scenario, belief, settings), settings).question_id == highest
    assert P.decide("voi_proposed", _state(scenario, belief, settings), settings).question_id == highest
    assert P.decide("voi_p_top_value", _state(scenario, belief, settings), settings).question_id == top_ref
    assert P.decide("evsi_lookahead", _state(scenario, belief, settings), settings).question_id == top_ref


def _write_long_bank(directory, questions: int):
    """The synthetic 2024 bank's label patterns repeated: one subject with
    ``questions`` questions (more than the old 25-check bound)."""

    write_eedi_2024(directory)
    labels = [
        ("A", {"B": 10, "C": 11}), ("B", {"A": 10, "D": 12}), ("C", {"A": 11, "B": 12}),
        ("D", {"A": 10}), ("A", {"C": 11, "D": 12}), ("B", {"C": 10}), ("C", {"D": 11}), ("D", {"B": 12}),
    ]
    with (directory / "train.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["QuestionId", "ConstructId", "ConstructName", "SubjectId", "SubjectName", "CorrectAnswer",
                         "QuestionText", "AnswerAText", "AnswerBText", "AnswerCText", "AnswerDText",
                         "MisconceptionAId", "MisconceptionBId", "MisconceptionCId", "MisconceptionDId"])
        for index in range(questions):
            correct, mis = labels[index % len(labels)]
            writer.writerow([index, 100 + index, "Order of operations", SUBJECT, "BIDMAS", correct, f"Q{index}",
                             "a", "b", "c", "d"] + [f"{float(mis[o]):.1f}" if o in mis else "" for o in "ABCD"])
    return directory


def test_the_multi_family_study_runs_every_episode_without_a_count_bound(eedi, tmp_path):
    # Codex review F4: the study inherited PolicySettings.safety_bound = 25, and
    # it bound (an NRM learner's eig_no_gate episode: 25 checks with it, 37
    # without). The bank is finite, so the study runs with no bound: an episode
    # ends by its own rule or when the subject's questions run out.
    base = MF.study_base(MF.MultiFamilySettings())
    assert base.policy.safety_bound is None
    assert MS.MultiSimSettings().policy.safety_bound is None
    assert P.PolicySettings().safety_bound is None  # the single-family study too (evsi-single-family-unbounded)
    bank = load_eedi_2024(_write_long_bank(tmp_path / "long-bank", 40))
    scenarios = tuple(build_scenarios(bank, eedi["fits"].lca))
    assert len(scenarios[0].questions) == 40
    families = F.build_families(bank, eedi["fits"])
    world = MS.World(families["lca"], scenarios)
    # A check costs nothing, so the EIG rule continues while any information is
    # left: the episode is bounded by the bank alone.
    generous = replace(base, learners=3, policies=("eig_no_gate",),
                       policy=replace(base.policy, lambda_time=0.0, burden_cost=0.0, draw_count=4))
    run = MS.run_family_simulation(world, generous)
    assert run.episodes and all(e.checks > 25 for e in run.episodes)
    for e, spec in zip(run.episodes, run.learners):
        assert e.checks == 40 - len(spec.history) and e.stop_reason == "no_question_left"
    # The old bound censored exactly these episodes.
    bounded = MS.run_family_simulation(world, replace(generous, policy=replace(generous.policy, safety_bound=25)))
    assert all(e.checks == 25 and e.stop_reason == "safety_bound" for e in bounded.episodes)
    # The cell's table counts the episodes the bank, not the rule, ended.
    table = MF._policy_table(run, seed=1, draws=20)["eig_no_gate"]
    assert table["ran_out_of_questions"] == len(run.episodes) and table["count_bound_stops"] == 0
    assert table["max_checks"] == max(e.checks for e in run.episodes)


def _population_oracle(model, question, single_item_model):
    """``P(option | hypothesis)`` marginalized over the item pool and the
    learner population, from the TRUTH's answer rows: each item answers as a
    one-item pool, each population state's needs split its weight."""

    sums = {h: np.zeros(4) for h in model.hypotheses}
    singles = [single_item_model(i) for i in range(model.pool.shape[0])]
    for state in model.population:
        needs = model.needs(tuple(state))
        mean = np.mean([[single.row(tuple(state), question)[o] for o in "ABCD"] for single in singles], axis=0)
        for h in needs:
            sums[h] += mean / len(needs)
    return {h: (v / v.sum() if v.sum() > 0 else np.full(4, 0.25)) for h, v in sums.items()}


def test_the_calibrated_systems_average_responses_over_the_item_pool(eedi):
    # Codex review F3: the nrm system applied the softmax to the MEAN item
    # parameters, which is not the mean response the truth draws from. The
    # system rows must equal an explicit item-mixture oracle built from the
    # truth's own answer rows over the identical learner population.
    families = F.build_families(eedi["bank"], eedi["fits"])
    scenario = build_scenarios(eedi["bank"], eedi["fits"].lca)[0]
    for family in (families["nrm"], families["nrm"].with_strength(0.9)):
        model = family.scenario_model(scenario)
        assert model.pool.shape[0] >= 2
        mean_params = F.NrmScenario(scenario, model.pool.mean(axis=0, keepdims=True), model.typical,
                                    holder_shift=model.holder_shift)
        largest_gap = 0.0
        for question in scenario.questions[:3]:
            rows = model.system_rows(question)
            oracle = _population_oracle(
                model, question,
                lambda i: F.NrmScenario(scenario, model.pool[i:i + 1], model.typical, holder_shift=model.holder_shift))
            for h in scenario.hypotheses:
                assert [rows[h][o] for o in "ABCD"] == pytest.approx(list(oracle[h]), abs=1e-9), h
                old = mean_params.system_rows(question)[h]
                largest_gap = max(largest_gap, max(abs(old[o] - rows[h][o]) for o in "ABCD"))
        # The parameter average is measurably not the response average.
        assert largest_gap > 1e-3
        # The bisection's holder-only path reads the same rows.
        fresh = family.scenario_model(scenario)
        assert fresh.targeted_consistencies() == pytest.approx(F.ScenarioModel.targeted_consistencies(model), abs=1e-12)

    cdm = families["cdm"].scenario_model(scenario)
    assert cdm.pool.shape[0] >= 2
    for question in scenario.questions[:3]:
        rows = cdm.system_rows(question)
        singles = [F.CdmScenario(scenario, cdm.pool[i:i + 1], families["cdm"].priors.get(
            scenario.subject_id, families["cdm"].pooled_prior)) for i in range(cdm.pool.shape[0])]
        sums = {h: np.zeros(4) for h in scenario.hypotheses}
        for profile, weight in cdm.profiles:
            mean = np.mean([[single.row(profile, question)[o] for o in "ABCD"] for single in singles], axis=0)
            for h, share in cdm._primary_weights(profile).items():
                sums[h] += weight * share * mean
        for h in scenario.hypotheses:
            assert [rows[h][o] for o in "ABCD"] == pytest.approx(list(sums[h] / sums[h].sum()), abs=1e-9), h


def test_the_implied_consistency_carries_a_subject_clustered_ci(eedi):
    families = F.build_families(eedi["bank"], eedi["fits"])
    scenarios = build_scenarios(eedi["bank"], eedi["fits"].lca)
    for name in ("lca", "cdm", "nrm", "lta"):
        implied = F.implied_quantities(families[name], scenarios)
        low, high = implied["consistency_ci95"]
        assert low <= implied["consistency"] <= high, name


def test_the_counted_card_row_starts_at_the_vocabulary_and_follows_the_counts(eedi):
    scenario = build_scenarios(eedi["bank"], eedi["fits"].lca)[0]
    question = scenario.questions[0]
    for h in scenario.hypotheses:
        assert MF.counted_row(h, question, {}, 8.0) == pytest.approx(hand_set_row(h, question))
    slot = "confuses_with_neighbor"
    counts = {slot: {"correct": 6.0, "signature": 4.0, "other_error": 0.0}}
    mis = next(h for h in scenario.hypotheses if h.startswith("mis:") and question.options_for(h[4:]))
    vocabulary = MF._vocabulary_role_row(slot)
    for pseudo in (2.0, 8.0):
        row = MF.counted_row(mis, question, counts, pseudo)
        # (pseudo * prior + counts) / (pseudo + n), as validate_and_compile_card compiles it.
        assert row[question.correct] == pytest.approx((pseudo * vocabulary["correct"] + 6.0) / (pseudo + 10.0))
    assert MF.counted_row(mis, question, counts, 2.0)[question.correct] > \
        MF.counted_row(mis, question, counts, 8.0)[question.correct]


def test_cli_multisim_quick_fits_every_family_and_reports_claims(eedi, tmp_path):
    result = CliRunner().invoke(app, [
        "evsi", "multisim", "--eedi-2024", str(eedi["bank_dir"]), "--eedi-2020", str(eedi["responses_dir"]),
        "--task", "3_4", "--output", str(tmp_path / "out"), "--quick", "--learners", "10",
        "--sensitivity-learners", "10", "--workers", "1", "--json",
    ])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output.strip().splitlines()[-1])
    assert payload["status"] == "ok"
    assert payload["families"] == ["lca", "cdm", "nrm", "lta"]
    report = json.loads((tmp_path / "out" / "multisim_report.json").read_text())
    analysis = report["analysis"]
    verdicts = {"supported", "directional", "family-dependent", "contradicted", "no difference", "not tested",
                "insufficient evidence"}
    assert {claim["verdict"] for claim in analysis["claims"]} <= verdicts
    assert analysis["winners"] and all(w["per_family"] for w in analysis["winners"])
    for name in ("lca", "cdm", "nrm", "lta"):
        block = report["families"][name]
        assert {"main", "regimes", "rotation", "sensitivity", "part_c"} <= set(block)
        assert set(block["main"]) == {"family", "hand_set"} | ({"lca", "cdm", "nrm", "lta"} - {name})
    assert not report["families"]["lta_reveal"]["fitted"]
    assert set(report["pseudo_count"]["streams"]) == {"lca", "cdm", "nrm", "lta"}
    fits = json.loads((tmp_path / "out" / "family_fits.json").read_text())
    assert set(fits["validation"]["families"]) == {"marginal", "lca", "cdm", "nrm", "lta"}
    # Reusing the saved fits skips the fit and gives the same study.
    again = CliRunner().invoke(app, [
        "evsi", "multisim", "--eedi-2024", str(eedi["bank_dir"]), "--fits", str(tmp_path / "out" / "family_fits.json"),
        "--output", str(tmp_path / "again"), "--quick", "--learners", "10", "--sensitivity-learners", "10",
        "--workers", "1", "--json",
    ])
    assert again.exit_code == 0, again.output
    second = json.loads((tmp_path / "again" / "multisim_report.json").read_text())
    assert second["fits"]["validation"] == report["fits"]["validation"]
    assert [c["id"] for c in second["analysis"]["claims"]] == [c["id"] for c in analysis["claims"]]
    assert not (tmp_path / "again" / "family_fits.json").exists()
    assert analysis["policy_regret"] and {r["policy"] for r in analysis["policy_regret"]} == \
        set(report["families"]["lca"]["regimes"][0]["episodes"]["policies"])
    # Rotation claims are one per regime, never pooled across regimes.
    rotation = [c for c in analysis["claims"] if c["id"].startswith("R:")]
    assert rotation and all("@" in c["id"] for c in rotation)
    for claim in rotation:
        assert {v["regime"] for v in claim["values"]} == {claim["id"].split("@", 1)[1]}
        assert all(v["system"] in analysis["families"] and v["system"] != v["family"] for v in claim["values"])
    # Re-scoring a stored report recomputes the analysis from its episodes alone.
    stored = tmp_path / "out" / "multisim_report.json"
    report["analysis"] = {}
    stored.write_text(json.dumps(report))
    rescored = CliRunner().invoke(app, ["evsi", "multisim", "--reanalyze", str(stored), "--json"])
    assert rescored.exit_code == 0, rescored.output
    assert json.loads(rescored.output.strip().splitlines()[-1])["most_robust_policy"] == \
        analysis["policy_regret"][0]["policy"]
    assert json.loads(stored.read_text())["analysis"] == json.loads(json.dumps(analysis))


def test_winners_list_tied_modes_in_name_order_and_score_rank_agreement():
    assert MF._kendall_tau({"a": 1.0, "b": 2.0, "c": 3.0}, {"a": 1.5, "b": 2.5, "c": 9.0}) == pytest.approx(1.0)
    assert MF._kendall_tau({"a": 1.0, "b": 2.0, "c": 3.0}, {"a": 3.0, "b": 2.0, "c": 1.0}) == pytest.approx(-1.0)
    assert MF._kendall_tau({"a": 1.0, "b": 1.0}, {"a": 2.0, "b": 2.0}) is None

    def cell(totals):
        return {"consistency": "fitted", "repair_minutes": 3.0,
                "episodes": {"learners": [0, 1, 2], "policies": {p: {"total": t} for p, t in totals.items()}}}

    report = {"families": {
        "x": {"regimes": [cell({"zeta": [1.0, 1.0, 1.0], "alpha": [2.0, 2.0, 2.0], "mid": [3.0, 3.0, 3.0]})]},
        "y": {"regimes": [cell({"zeta": [2.0, 2.0, 2.0], "alpha": [1.0, 1.0, 1.0], "mid": [3.0, 3.0, 3.0]})]},
    }}
    for _ in range(3):
        row = MF._winners(report, ["x", "y"], seed=1, draws=20)[0]
        assert row["modal_tied"] == ["alpha", "zeta"] and row["modal_winner"] == "alpha"
        assert row["top1_agreement"] == "1/2"
        # zeta < alpha < mid against alpha < zeta < mid: one discordant pair of three.
        assert row["ranking_kendall_tau"] == {"mean": pytest.approx(1 / 3, abs=1e-4),
                                              "min": pytest.approx(1 / 3, abs=1e-4), "pairs": 1}
        assert row["regret_of_other_family_winner"]["x"]["y"] == pytest.approx(1.0)

    # The robust choice: "mid" is never best but never far; "zeta" and "alpha"
    # each lose a full minute in the other family. A stress family is reported
    # apart and never ranks.
    report["families"]["x"]["regimes"][0]["episodes"]["policies"]["mid"]["total"] = [1.5, 1.5, 1.5]
    report["families"]["y"]["regimes"][0]["episodes"]["policies"]["mid"]["total"] = [1.5, 1.5, 1.5]
    report["families"]["s"] = {"regimes": [cell({"zeta": [1.0] * 3, "alpha": [9.0] * 3, "mid": [1.0] * 3})]}
    rows = MF._policy_regret(report, ["x", "y"], ["s"])
    assert [r["policy"] for r in rows] == ["mid", "alpha", "zeta"]
    assert rows[0]["max_regret"] == pytest.approx(0.5) and rows[0]["cells_near_best"] == "0/2"
    assert rows[1]["max_regret"] == pytest.approx(1.0) and rows[1]["max_regret_cell"] == "x fitted/3"
    assert rows[1]["cells_near_best"] == "1/2" and rows[1]["stress_max_regret"] == pytest.approx(8.0)


def test_a_zero_effect_everywhere_is_no_difference_not_a_contradiction():
    zero = {"value": 0.0, "ci95": [0.0, 0.0], "holds": False, "certified": False}
    assert MF._verdict([zero, dict(zero)]) == "no difference"
    against = {"value": 0.1, "ci95": [-0.2, 0.4], "holds": False, "certified": False}
    assert MF._verdict([zero, against]) == "contradicted"
    assert MF._verdict([zero, {"value": -0.3, "ci95": [-0.5, -0.1], "holds": True, "certified": True}]) == \
        "family-dependent"
    # A value certifies only through a CI (Codex review: C1a was certified by a
    # fixed margin with no CI): without one it holds at most directionally.
    assert MF._verdict([{"value": "8/8", "ci95": None, "holds": True, "certified": True}]) == "directional"
    assert MF._verdict([{"value": 0.3, "ci95": [0.2, 0.4], "holds": True, "certified": True}]) == "supported"


def test_the_pseudo_count_log_loss_is_per_check_of_each_arm():
    # Arm "few" stops after one check (1 nat each), arm "many" after four
    # (3 nats over four checks): per check, few is WORSE (1.0 against 0.75),
    # whatever the resample.
    few = {"per_episode_log_loss": [1.0, 1.0, 1.0], "per_episode_checks": [1, 1, 1]}
    many = {"per_episode_log_loss": [3.0, 3.0, 3.0], "per_episode_checks": [4, 4, 4]}
    picks = np.random.default_rng(0).integers(0, 3, size=(50, 3))
    difference = MF._per_check_log_loss(few, picks) - MF._per_check_log_loss(many, picks)
    assert difference == pytest.approx(np.full(50, 0.25))
    assert MF._per_check_log_loss({"per_episode_log_loss": [0.0], "per_episode_checks": [0]},
                                  np.zeros((2, 1), dtype=int)) == pytest.approx([0.0, 0.0])


def test_cli_multisim_without_fits_needs_the_2020_answers(eedi, tmp_path):
    result = CliRunner().invoke(app, [
        "evsi", "multisim", "--eedi-2024", str(eedi["bank_dir"]), "--output", str(tmp_path / "out"), "--json",
    ])
    assert result.exit_code == 1
    assert json.loads(result.output)["status"] == "invalid"
    no_bank = CliRunner().invoke(app, ["evsi", "multisim", "--output", str(tmp_path / "out"), "--json"])
    assert no_bank.exit_code == 1 and "--eedi-2024" in json.loads(no_bank.output)["reason"]


def _synthetic_report(families=("a", "b", "c"), *, learners: int = 30) -> dict:
    """A stored multisim report reduced to what the analyzer reads: per family,
    the fitted consistency and one regime (fitted strength, 30-minute repairs)
    in which ``evsi`` beats ``incumbent`` by a minute per learner."""

    rng = np.random.default_rng(3)

    def cell():
        base = rng.uniform(10.0, 20.0, size=learners)
        totals = {"incumbent": base, "evsi": base - 1.0 + rng.normal(0, 0.1, size=learners),
                  "evsi_lcb_only": base - 1.2}
        return {"consistency": "fitted", "repair_minutes": 30.0, "policies": {},
                "episodes": {"learners": list(range(learners)),
                             "policies": {p: {"total": [round(float(x), 4) for x in v]} for p, v in totals.items()}}}

    return {
        "settings": {"seed": 1, "bootstrap": 100, "families": list(families), "stress_families": [],
                     "strengths": [None], "repairs": [30.0], "pseudo_count_regimes": []},
        "hand_set_implied": {"consistency": {"contrast_card_dominant_normalized": 0.8333}},
        "fits": {"validation": {"families": {name: {"adequate": True} for name in families}}},
        "families": {name: {"fitted": True,
                            "implied": {"fitted": {"consistency": 0.4, "consistency_ci95": [0.38, 0.42]}},
                            "regimes": [cell()]} for name in families},
    }


def test_certification_needs_adequate_families_and_every_cell():
    # Codex review F2: the analyzer counted every family whatever its adequacy,
    # and a family missing a cell simply did not vote ("every family" became
    # "every available result").
    def claim(analysis, claim_id):
        return next(c for c in analysis["claims"] if c["id"] == claim_id)

    report = _synthetic_report()
    complete = MF.analyze(report)
    assert complete["families"] == ["a", "b", "c"] and complete["excluded_families"] == []
    assert claim(complete, "C7:30")["verdict"] == "supported"
    assert claim(complete, "C1a")["verdict"] == "supported"
    assert all(row["complete"] for row in complete["winners"])

    # Every fit fails the adequacy gate: nothing votes, nothing is certified.
    failed = json.loads(json.dumps(report))
    for block in failed["fits"]["validation"]["families"].values():
        block["adequate"] = False
    analysis = MF.analyze(failed)
    assert analysis["families"] == [] and not analysis["enough_families"]
    assert {e["family"] for e in analysis["excluded_families"]} == {"a", "b", "c"}
    assert {c["verdict"] for c in analysis["claims"]} == {"insufficient evidence"}
    assert analysis["policy_regret"] == [] and analysis["winners"] == []

    # One inadequate family is excluded (and reported), not silently counted.
    one = json.loads(json.dumps(report))
    one["fits"]["validation"]["families"]["c"]["adequate"] = False
    analysis = MF.analyze(one)
    assert analysis["families"] == ["a", "b"]
    assert analysis["excluded_families"] == [{"family": "c", "reason": "failed the adequacy gate on held-out students"}]
    assert {v["family"] for v in claim(analysis, "C7:30")["values"]} == {"a", "b"}
    # A fit with no held-out validation is not adequate either.
    del one["fits"]["validation"]["families"]["b"]
    assert MF.analyze(one)["families"] == ["a"]
    assert claim(MF.analyze(one), "C7:30")["verdict"] == "insufficient evidence"  # one family is not RankCert

    # A voting family missing the claim's cell: insufficient evidence, named.
    gap = json.loads(json.dumps(report))
    gap["families"]["c"]["regimes"] = []
    analysis = MF.analyze(gap)
    assert claim(analysis, "C7:30")["verdict"] == "insufficient evidence"
    assert claim(analysis, "C7:30")["missing"] == ["c"]
    assert [row["complete"] for row in analysis["winners"]] == [False]
    assert all(not row["complete"] for row in analysis["policy_regret"])
    # A required family absent from the report is an exclusion, never a quiet 2/2.
    absent = json.loads(json.dumps(report))
    del absent["families"]["c"]
    analysis = MF.analyze(absent)
    assert {"family": "c", "reason": "required by the study and adequate on held-out students, but absent from the "
                                     "report: every claim needs its cells"} in analysis["excluded_families"]
    assert claim(analysis, "C7:30")["verdict"] == "insufficient evidence"
    assert claim(analysis, "C7:30")["missing"] == ["c"]


def test_a_required_adequate_family_absent_from_the_report_blocks_certification(tmp_path):
    # Codex re-review F2: deleting a required family's results (its passing
    # validation and its place in the study's settings kept) left the other
    # families to certify alone (3/3 supported) and every regret row complete.
    report = _synthetic_report(("a", "b", "c", "d"))
    absent = json.loads(json.dumps(report))
    del absent["families"]["d"]
    analysis = MF.analyze(absent)
    assert analysis["families"] == ["a", "b", "c"] and analysis["enough_families"]
    assert analysis["coverage_families"] == ["a", "b", "c", "d"]
    assert analysis["excluded_families"] == [{
        "family": "d", "reason": "required by the study and adequate on held-out students, but absent from the "
                                 "report: every claim needs its cells"}]
    for claim_id in ("C7:30", "C1a"):
        claim = next(c for c in analysis["claims"] if c["id"] == claim_id)
        assert claim["verdict"] == "insufficient evidence", claim_id
        assert claim["missing"] == ["d"], claim_id
    assert {c["verdict"] for c in analysis["claims"]} <= {"insufficient evidence", "not tested"}
    assert [(row["complete"], row["missing"]) for row in analysis["winners"]] == [(False, ["d"])]
    assert analysis["policy_regret"] and all(
        not row["complete"] and row["missing_cells"] == ["d fitted/30"] for row in analysis["policy_regret"])
    # The CLI's headline names no robust policy from an incomplete ranking.
    stored = tmp_path / "multisim_report.json"
    stored.write_text(json.dumps({**absent, "elapsed_seconds": 1.0, "analysis": {}}))
    result = CliRunner().invoke(app, ["evsi", "multisim", "--reanalyze", str(stored), "--json"])
    assert result.exit_code == 0, result.output
    headline = json.loads(result.output.strip().splitlines()[-1])
    assert headline["coverage_families"] == ["a", "b", "c", "d"] and headline["most_robust_policy"] is None
    stored.write_text(json.dumps({**report, "elapsed_seconds": 1.0, "analysis": {}}))
    result = CliRunner().invoke(app, ["evsi", "multisim", "--reanalyze", str(stored), "--json"])
    assert json.loads(result.output.strip().splitlines()[-1])["most_robust_policy"] == "evsi_lcb_only"

    # Its validation failed or is unknown: it could never vote, so its absence
    # blocks nothing (it is still reported).
    for validation in ({"adequate": False}, None):
        variant = json.loads(json.dumps(absent))
        if validation is None:
            del variant["fits"]["validation"]["families"]["d"]
        else:
            variant["fits"]["validation"]["families"]["d"] = validation
        analysis = MF.analyze(variant)
        assert analysis["coverage_families"] == ["a", "b", "c"]
        assert [e["family"] for e in analysis["excluded_families"]] == ["d"]
        assert next(c for c in analysis["claims"] if c["id"] == "C7:30")["verdict"] == "supported"
        assert all(row["complete"] for row in analysis["winners"] + analysis["policy_regret"])

    # A required family's results flagged as not fitted are still required.
    unflagged = json.loads(json.dumps(report))
    unflagged["families"]["d"]["fitted"] = False
    analysis = MF.analyze(unflagged)
    assert analysis["families"] == ["a", "b", "c", "d"] and analysis["stress_families"] == []


def test_the_nrm_row_cache_never_serves_a_revised_bank(eedi, monkeypatch):
    # Codex re-review F6: the process-wide nrm row cache was keyed by the model
    # fingerprint and the question id alone, so a revised bank (same ids,
    # subjects, hypotheses and fits; different option labels or key) read the
    # earlier bank's rows in the same process.
    monkeypatch.setattr(F, "_NRM_ROW_CACHE", {})
    nrm = F.build_families(eedi["bank"], eedi["fits"])["nrm"]
    scenario = build_scenarios(eedi["bank"], eedi["fits"].lca)[0]
    question = next(q for q in scenario.questions
                    if len(set(q.misconception_by_option.values())) == 2
                    and all(f"mis:{m}" in scenario.hypotheses for m in q.misconception_by_option.values()))
    first, second = sorted(question.misconception_by_option)
    unlabelled = next(o for o in "ABCD" if o != question.correct and o not in question.misconception_by_option)
    revisions = {
        "labels swapped": replace(question, misconception_by_option={
            first: question.misconception_by_option[second], second: question.misconception_by_option[first]}),
        "key moved": replace(question, correct=unlabelled, misconception_by_option={
            question.correct: question.misconception_by_option[first],
            second: question.misconception_by_option[second]}),
    }
    original = nrm.scenario_model(scenario).system_rows(question)
    for label, revised in revisions.items():
        bank = replace(scenario, questions=tuple(revised if q.question_id == question.question_id else q
                                                 for q in scenario.questions))
        served = nrm.scenario_model(bank).system_rows(revised)
        with monkeypatch.context() as fresh_cache:
            fresh_cache.setattr(F, "_NRM_ROW_CACHE", {})
            fresh = nrm.scenario_model(bank).system_rows(revised)
        for h in scenario.hypotheses:
            assert [served[h][o] for o in "ABCD"] == pytest.approx([fresh[h][o] for o in "ABCD"], abs=1e-12), (label, h)
        assert any(abs(fresh[h][o] - original[h][o]) > 1e-3 for h in scenario.hypotheses for o in "ABCD"), label
    # The original bank still reads its own rows from the shared cache.
    again = nrm.scenario_model(scenario).system_rows(question)
    assert again == original


def test_c1a_certifies_through_the_consistency_ci_not_a_fixed_margin():
    report = _synthetic_report()
    straddles = json.loads(json.dumps(report))
    straddles["families"]["b"]["implied"]["fitted"]["consistency_ci95"] = [0.38, 0.85]
    claim = next(c for c in MF.analyze(straddles)["claims"] if c["id"] == "C1a")
    assert claim["verdict"] == "directional" and claim["families_certified"] == "2/3"
    # A stored report from before the CI: it holds, never certified.
    old = json.loads(json.dumps(report))
    for block in old["families"].values():
        del block["implied"]["fitted"]["consistency_ci95"]
    claim = next(c for c in MF.analyze(old)["claims"] if c["id"] == "C1a")
    assert claim["verdict"] == "directional" and claim["families_certified"] == "0/3"


def test_reanalysis_never_destroys_the_stored_report(tmp_path, monkeypatch):
    # Codex review F5: --reanalyze rewrote the report with Path.write_text,
    # which truncates first; an interruption (here: the disk fills while the
    # new report is flushed) lost the stored episodes.
    stored = tmp_path / "multisim_report.json"
    report = _synthetic_report()
    report.update({"elapsed_seconds": 1.0, "analysis": {}})
    original = json.dumps(report)
    stored.write_text(original)

    def truncate_then_fail(path, data, *args, **kwargs):
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(data[: len(data) // 3])
        raise OSError(28, "No space left on device")

    def no_space(fd):
        raise OSError(28, "No space left on device")

    with monkeypatch.context() as patched:
        patched.setattr(type(stored), "write_text", truncate_then_fail)
        patched.setattr(os, "fsync", no_space)
        result = CliRunner().invoke(app, ["evsi", "multisim", "--reanalyze", str(stored), "--json"])
    assert result.exit_code == 1
    assert stored.read_text() == original
    assert sorted(p.name for p in tmp_path.iterdir()) == ["multisim_report.json"]  # no temporary left
    # The same rewrite succeeds once the disk has room, atomically.
    result = CliRunner().invoke(app, ["evsi", "multisim", "--reanalyze", str(stored), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(stored.read_text())["analysis"]["families"] == ["a", "b", "c"]


def test_the_atomic_writer_keeps_the_old_file_on_any_failure(tmp_path, monkeypatch):
    from learnloop.evsi_calibration import artifacts

    target = tmp_path / "family_fits.json"
    target.write_text("old")
    with monkeypatch.context() as patched:
        patched.setattr(artifacts.os, "replace", lambda source, destination: (_ for _ in ()).throw(OSError("busy")))
        with pytest.raises(OSError):
            artifacts.write_text_atomic(target, "new")
    assert target.read_text() == "old" and sorted(p.name for p in tmp_path.iterdir()) == ["family_fits.json"]
    artifacts.write_text_atomic(target, "new")
    artifacts.write_text_atomic(tmp_path / "fresh" / "report.json", "{}")
    assert target.read_text() == "new" and (tmp_path / "fresh" / "report.json").read_text() == "{}"
