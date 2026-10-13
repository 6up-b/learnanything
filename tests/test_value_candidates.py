"""S2a (G8): valuation verdicts, groups, regimes, greedy conditional checks and no count cap."""
from __future__ import annotations

import pytest

from learnloop.instructional.valuation import (
    CandidateInput, PendingDecision, ValuationProblem, refuse_mixed_decision, value_candidates, value_problem,
)
from learnloop.scheduling import action_loss as AL

SLOTS = ("mastered", "misconception:m1", "misconception:m2", "unfamiliar")


def _problem(**kwargs):
    prior = {slot: 0.25 for slot in SLOTS}
    return ValuationProblem(key="lo:x", space_kind="hypothesis_set", slots=SLOTS, prior=prior,
                            prior_basis="hypothesis_set", state_hash="h", **kwargs)


def _separates(winner: str, *, sharpness: float = 0.98) -> dict[str, dict[str, float]]:
    """A test that tells ``winner`` apart from every other slot."""
    return {slot: ({"hit": sharpness, "miss": 1 - sharpness} if slot == winner
                   else {"hit": 1 - sharpness, "miss": sharpness}) for slot in SLOTS}


def _input(ref, table, *, regime="item_point", members=3, construction=None, minutes=1.0):
    return CandidateInput(ref=ref, kind="item", members=tuple([table] * members), outcome_alphabet=("hit", "miss"),
                          regime=regime, likelihood_basis="estimated_row", expected_minutes=minutes,
                          construction=construction or f"{regime}:{members}")


def test_no_count_cap_three_informative_checks_all_return():
    inputs = [_input("a", _separates("misconception:m1", sharpness=0.99)),
              _input("b", _separates("misconception:m2", sharpness=0.93)),
              _input("c", _separates("unfamiliar", sharpness=0.86))]
    report = value_problem(_problem(), inputs)
    assert report["verdict"] == "act"
    assert [check["ref"] for check in report["checks"]] == ["a", "b", "c"]
    assert report["selector"] == "evaluate_selection"
    assert report["checks"][0]["predicted_outcomes"]


def test_greedy_conditional_valuation_drops_a_redundant_second_check():
    # Two checks that would say exactly the same thing: once one is picked, the
    # other's expected information over its predicted outcomes is nil.
    inputs = [_input("a", _separates("misconception:m1", sharpness=1.0)),
              _input("a_copy", _separates("misconception:m1", sharpness=1.0), minutes=1.5)]
    report = value_problem(_problem(), inputs)
    assert [check["ref"] for check in report["checks"]] == ["a"]
    assert report["stop_at"]["candidate"] == "a_copy"


def test_stop_when_nothing_clears_the_minutes_cost():
    flat = {slot: {"hit": 0.5, "miss": 0.5} for slot in SLOTS}
    report = value_problem(_problem(), [_input("flat", flat, minutes=10.0)])
    assert report["verdict"] in ("stop", "abstain") and report["checks"] == []


def test_learner_initiated_results_have_three_groups():
    structural = CandidateInput(ref="raw", kind="source_exercise", missing=["structural_only"])
    bound = CandidateInput(ref="screened", kind="source_exercise",
                           members=({slot: {f"sig{i}": 1.0} for i, slot in enumerate(SLOTS)},),
                           outcome_alphabet=tuple(f"sig{i}" for i in range(4)), regime="arm_b_noiseless",
                           construction="noiseless", expected_minutes=2.0)
    report = value_problem(_problem(), [_input("a", _separates("misconception:m1")), bound, structural])
    groups = report["groups"]
    assert [e["ref"] for e in groups["valued"]] == ["a"]
    assert [e["ref"] for e in groups["bounded"]] == ["screened"]
    assert groups["bounded"][0]["label"].startswith("LearnLoop's reading of the exercise, not yet checked: at most")
    assert [e["ref"] for e in groups["unvalued"]] == ["raw"]
    assert "can't estimate" in groups["unvalued"][0]["label"]


def test_a_system_initiated_check_needs_a_licensing_regime():
    report = value_problem(_problem(), [_input("a", _separates("misconception:m1"))], system_initiated=True)
    assert (report["verdict"], report["reason"]) == ("abstain", "regime_cannot_license")
    assert report["groups"]["valued"][0]["excluded"] == "regime_cannot_license"
    pinned = _input("p", _separates("misconception:m1"), regime="pinned_channel", members=129,
                    construction="pinned:hash")
    licensed = value_problem(_problem(), [_input("a", _separates("misconception:m2", sharpness=0.99)), pinned],
                             system_initiated=True)
    assert licensed["verdict"] == "act" and [check["ref"] for check in licensed["checks"]][0] == "p"
    assert all(check["licenses_system_check"] for check in licensed["checks"])


def test_mixed_regimes_in_one_learner_problem_use_credible_sets_without_index_errors():
    pinned = _input("p", _separates("misconception:m1", sharpness=0.6), regime="pinned_channel", members=129,
                    construction="pinned:hash")
    item = _input("i", _separates("misconception:m1", sharpness=0.99))
    report = value_problem(_problem(), [pinned, item])
    assert report["selector"] == "evaluate_selection_credible_sets"
    assert report["checks"][0]["ref"] == "i"
    flipped = value_problem(_problem(), [
        _input("p", _separates("misconception:m1", sharpness=0.99), regime="pinned_channel", members=129,
               construction="pinned:hash"),
        _input("i", _separates("misconception:m1", sharpness=0.6))])
    assert flipped["checks"][0]["ref"] == "p"


def test_two_spaces_are_two_problems_with_their_own_verdicts():
    first = _problem()
    second = ValuationProblem(key="causal:f", space_kind="causal_factor", slots=("h1", "h2"),
                              prior={"h1": 0.5, "h2": 0.5}, prior_basis="support_weighted", state_hash="c")
    candidate_second = CandidateInput(ref="a", kind="item", members=({"h1": {"x": 1.0}, "h2": {"y": 1.0}},),
                                      outcome_alphabet=("x", "y"), regime="arm_b_noiseless", construction="noiseless")
    receipt = value_candidates([first, second], {"lo:x": [_input("a", _separates("misconception:m1"))],
                                                 "causal:f": [candidate_second]})
    assert [section["problem"]["key"] for section in receipt["problems"]] == ["lo:x", "causal:f"]
    assert len(receipt["candidates"]["a"]) == 2  # listed once, with each problem's verdict
    assert {entry["problem"] for entry in receipt["candidates"]["a"]} == {"lo:x", "causal:f"}
    assert "summed" not in str(receipt) and "joint" not in str(receipt)


def test_a_decision_spanning_spaces_is_refused():
    first, second = _problem(), ValuationProblem(key="causal:f", space_kind="causal_factor", slots=("h1",),
                                                 prior={"h1": 1.0}, prior_basis="support_weighted", state_hash="c")
    with pytest.raises(ValueError, match="mixed_hypothesis_spaces"):
        refuse_mixed_decision([first, second], {"mastered": "a", "h1": "b"})


def _loss_table():
    routes = [{"reason": "h1", "first_intervention": "repair_a"}, {"reason": "h2", "first_intervention": "repair_b"}]
    return AL.build_loss_table(routes=routes, duration_overrides={"repair_a": 10.0, "repair_b": 10.0})


def test_decision_mode_ranks_by_evsi_and_names_the_action():
    table = _loss_table()
    problem = ValuationProblem(key="causal:f", space_kind="causal_factor", slots=("h1", "h2"),
                               prior={"h1": 0.5, "h2": 0.5}, prior_basis="support_weighted", state_hash="c",
                               decision=PendingDecision("repair_class", {"h1": "repair_a", "h2": "repair_b"}, table))
    sharp = CandidateInput(ref="sharp", kind="item", members=({"h1": {"x": 1.0}, "h2": {"y": 1.0}},),
                           outcome_alphabet=("x", "y"), regime="pinned_channel", construction="p", expected_minutes=1.0)
    report = value_problem(problem, [sharp])
    assert report["mode"] == "decision" and report["selector"] == "rank_feasible"
    assert report["verdict"] in ("measure", "abstain")
    assert report["perfect_information_minutes"] > 0
    unmapped = ValuationProblem(key="causal:g", space_kind="causal_factor", slots=("h1", "h2"),
                                prior={"h1": 0.5, "h2": 0.5}, prior_basis="support_weighted", state_hash="d",
                                decision=PendingDecision("repair_class", {"h1": "repair_a", "h2": None}, None,
                                                         {"reason": "no_action_mapping"}))
    refused = value_problem(unmapped, [sharp])
    assert (refused["verdict"], refused["reason"]) == ("abstain", "no_action_mapping")


def test_identical_inputs_give_identical_receipts():
    inputs = [_input("a", _separates("misconception:m1", sharpness=0.99)), _input("b", _separates("unfamiliar"))]
    assert value_problem(_problem(), inputs) == value_problem(_problem(), inputs)


# -- Codex sources-build review F10: compiled instruments keep their licensing regime ------------


@pytest.mark.parametrize("items", [("pi_svd_define_001",), ("pi_svd_define_001", "pi_svd_define_002")])
def test_an_instrument_only_request_matches_robust_selection(tmp_path, items):
    from learnloop.clock import FrozenClock
    from learnloop.db.repositories import Repository
    from learnloop.diagnosis.probe_episodes import eligible_instruments, enter_episode
    from learnloop.diagnosis.probe_robust import RobustCandidate, load_pinned_channel, robust_selection
    from learnloop.instructional.valuation import episode_problem, item_input, value_problem
    from learnloop.vault.loader import load_vault
    from tests.helpers import NOW, admit_probe_instrument_card, create_basic_vault, set_algorithm_version
    from tests.test_probe_predictive_eig import _add_item

    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    set_algorithm_version(paths, "mvp-0.8")  # the robust probe cutover
    _add_item(root, "pi_svd_define_002", "surface_two")
    vault = load_vault(root)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository, items=items)
    episode = enter_episode(vault, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    problem, missing = episode_problem(vault, repository, episode.id)
    assert missing == [] and problem.excluded_mass  # H_OTHER excluded explicitly, its mass recorded
    entries = eligible_instruments(vault, repository, episode, posterior=problem.context["live_posterior"])
    assert {entry.item.id for entry in entries} == set(items)
    channel = load_pinned_channel(repository, episode.calibration_model_hash)
    live = robust_selection(channel, [RobustCandidate(entry.item.id, entry.instrument, dict(entry.slot_map),
                                                      float(entry.instrument.expected_seconds))
                                      for entry in entries], problem.prior, episode_id=episode.id)
    inputs = [item_input(vault, repository, problem, vault.practice_items[item_id]) for item_id in items]
    assert all(candidate.regime == "pinned_channel" and candidate.likelihood_basis == "compiled_instrument"
               for candidate in inputs)
    for system_initiated in (True, False):
        section = value_problem(problem, inputs, system_initiated=system_initiated)
        assert section["selector"] == "evaluate_selection"
        assert section.get("reason") != "regime_cannot_license"  # pinned_channel licenses a system check
        if live.verdict == "act":
            assert section["verdict"] == "act" and section["checks"][0]["ref"] == live.chosen_slot
        else:
            assert section["stop_at"]["verdict"] == live.verdict
            assert section["stop_at"]["candidate"] == live.chosen_slot
        stop = section.get("stop_at") or {}
        if stop:
            assert abs(stop["robust_eig_per_second"] - round(live.robust_eig_per_second, 8)) < 1e-12


def test_below_the_robust_cutover_instruments_are_ordinary_items(tmp_path):
    from learnloop.clock import FrozenClock
    from learnloop.db.repositories import Repository
    from learnloop.diagnosis.probe_episodes import enter_episode
    from learnloop.instructional.valuation import episode_problem, item_input
    from learnloop.vault.loader import load_vault
    from tests.helpers import NOW, admit_probe_instrument_card, create_basic_vault

    root = tmp_path / "vault"
    paths = create_basic_vault(root)  # mvp-0.6: the legacy point path
    vault = load_vault(root)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository)
    episode = enter_episode(vault, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    problem, _missing = episode_problem(vault, repository, episode.id)
    candidate = item_input(vault, repository, problem, vault.practice_items["pi_svd_define_001"])
    assert candidate.regime == "item_point"
    assert candidate.minutes_provenance["instrument_path"] in ("below_robust_cutover", "no_pinned_channel")
