"""Slip or gap (docs/specs/spec_slip_vs_gap_v1.md §8): the miss-cause sensor (SG1) and the numeric policy weighing the
cause (SG2).

"cold_failing can be from 1 severe bayesian surprise cold retrieval failure or 2 mild surprise cold retrieval failures, or
none since the failures in the cold retrieval were insignificant/trivial arithmetic. This is something for the action
router/diagnosis/teacher ensemble to decide through the learnloop algorithm." (owner, Nov 9). And on §6's default: "While
the numeric prior might not value a lesson after a slip, the LLM can still decide". Fakes only; no model call.
"""

from __future__ import annotations

import ast
import json
import math
import pathlib
from dataclasses import replace
from datetime import timedelta

import numpy as np
import pytest

from learnloop.algorithm_versions import FAILURE_SHARE_ALGORITHM_VERSION, SLIP_GAP_ALGORITHM_VERSION
from learnloop.daily_plan import objective_card as OCARD
from learnloop.daily_plan import objective_chooser as OC
from learnloop.daily_plan.types import LESSON_OFFER_SUBTYPE, BlockCandidate
from learnloop.router_objective import miss_cause as MC
from learnloop.router_objective import miss_cause_report as MCR
from learnloop.router_objective import mix
from learnloop.router_objective import value as V
from learnloop.router_objective_switches import miss_cause_in_value_on, miss_cause_sensor_on
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS
from learnloop.vault.loader import load_vault

from tests.daily_plan_fakes import NOW as CLOCK_NOW
from tests.daily_plan_fakes import iso
from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version
from tests.router_mixture_helpers import join_carried_valuations, mixture_env, rows, run
from tests.router_model_fakes import fake_runtime
from tests.test_ih4_preferences_inform_router import _numbers, _pin, _traces
from tests.test_te3b_offers import OFFER, offerable  # noqa: F401 - the fixture

TAG = SLIP_GAP_ALGORITHM_VERSION
OLD = FAILURE_SHARE_ALGORITHM_VERSION
QUIET = "[router_objective]\nstop_coin = 0.0\n"
SENSOR_ONLY = QUIET + "miss_cause_in_value = false\n"
OFF = QUIET + "miss_cause_sensor = false\n"
NOW = iso(CLOCK_NOW)
SECRET = "THE EXPECTED ANSWER IS argmax over the logits"
#: The diagnoser's verbalized weights (``prior_weight``), one event each.
SLIP_CAUSES = [("transient_execution", 3.0), ("learner_state", 1.0)]
GAP_CAUSES = [("learner_state", 3.0), ("transient_execution", 1.0)]
UNKNOWN_CAUSES = [("unknown", 1.0)]


# -- fixtures on the ledger --------------------------------------------------------------------------------------------


def _exec(repository, sql, params=()):
    with repository.connection() as connection:
        connection.execute(sql, params)
        connection.commit()


def _at(days: float = 0.0, minutes: float = 0.0) -> str:
    return iso(CLOCK_NOW - timedelta(days=days) + timedelta(minutes=minutes))


def _attempt(repository, attempt_id, lo, item, *, at, correctness=0.75, attempt_type="independent_attempt",
             primed=0, hints=0):
    _exec(repository,
          "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
          "correctness, primed, hints_used, created_at) VALUES (?, ?, ?, 'short_answer', ?, ?, ?, ?, ?)",
          (attempt_id, item, lo, attempt_type, correctness, primed, hints, at))
    return attempt_id


def _diagnose(repository, attempt_id, events, *, at, status="completed", error=None):
    proposal = {"analysis_md": SECRET, "event_diagnoses": [
        {"causal_class": causes[0][0], "candidate_causes": [
            {"cause_scope": scope, "prior_weight": weight, "statement": f"{SECRET} ({scope})"} for scope, weight in causes]}
        for causes in events]}
    _exec(repository,
          "INSERT INTO attempt_diagnoses (id, attempt_id, diagnosis_prompt_version, mode, history_mode, status, error, "
          "proposal_json, created_at) VALUES (?, ?, 'v', 'live', 'full', ?, ?, ?, ?)",
          (f"dg_{attempt_id}_{status}", attempt_id, status, error,
           json.dumps(proposal) if status == "completed" else None, at))
    return f"dg_{attempt_id}_{status}"


def _surprise(repository, attempt_id, bayesian, direction="negative", *, at):
    _exec(repository,
          "INSERT INTO attempt_surprise (attempt_id, observed_joint_bucket_json, predictive_surprise, bayesian_surprise, "
          "surprise_direction, algorithm_version, created_at) VALUES (?, '{}', 1.0, ?, ?, 'mvp-0.55', ?)",
          (attempt_id, bayesian, direction, at))


def _pending(repository, attempt_id):
    _exec(repository,
          "INSERT INTO post_attempt_jobs (id, attempt_id, kind, job_key, attempt_completed_at, state, payload_json, "
          "created_at, updated_at) VALUES (?, ?, 'diagnose', ?, ?, 'queued', '{\"mode\": \"live\"}', ?, ?)",
          (f"j_{attempt_id}", attempt_id, f"k_{attempt_id}", NOW, NOW, NOW))


@pytest.fixture
def ledger(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, TAG)
    vault = load_vault(paths.root)
    from learnloop.db.repositories import Repository
    from learnloop.vault.paths import VaultPaths

    return vault, Repository(VaultPaths(vault.root, vault.config).sqlite_path)


def _sensor(vault, repository, los, now=NOW):
    with repository.connection() as connection:
        return MC.sensor(connection, vault.config, los, now)


# -- the sensor ---------------------------------------------------------------------------------------------------------


def test_a_slip_a_gap_and_an_unknown_give_the_diagnosis_weights_by_class(ledger):
    vault, repository = ledger
    for lo, causes in (("lo_a", SLIP_CAUSES), ("lo_b", GAP_CAUSES), ("lo_c", UNKNOWN_CAUSES)):
        attempt = _attempt(repository, f"att_{lo}", lo, f"pi_{lo}", at=_at(1))
        _diagnose(repository, attempt, [causes], at=_at(1, 1))
    found = _sensor(vault, repository, ["lo_a", "lo_b", "lo_c"])
    assert {lo: (r["p_gap"], r["p_slip"], r["p_unknown"]) for lo, r in found.items()} == {
        "lo_a": pytest.approx((0.25, 0.75, 0.0)), "lo_b": pytest.approx((0.75, 0.25, 0.0)),
        "lo_c": pytest.approx((0.0, 0.0, 1.0))}
    assert all(r["status"] == MC.DIAGNOSED and r["basis"] == MC.BASIS_PRIOR for r in found.values())


def test_events_average_and_a_cause_with_no_weight_takes_the_mean_of_the_others():
    p, events = MC.prior_weights({"event_diagnoses": [
        {"candidate_causes": [{"cause_scope": "learner_state", "prior_weight": 1.0},
                              {"cause_scope": "transient_execution", "prior_weight": None}]},
        {"candidate_causes": [{"cause_scope": "transient_execution", "prior_weight": 2.0}]}]})
    assert events == 2
    assert p == pytest.approx({MC.GAP: 0.25, MC.SLIP: 0.75, MC.UNKNOWN: 0.0})
    assert MC.prior_weights({"event_diagnoses": []}) is None


def test_the_latest_miss_is_the_one_read_and_it_is_lesson_suggestions_own_miss(ledger):
    """The same rows ``lesson_suggestion.missed_since`` reads: cold, not fully right, since the last lesson ended; a right
    answer is no miss; an older diagnosed miss is never read past a newer undiagnosed one."""

    from learnloop.daily_plan.lesson_suggestion import missed_since

    vault, repository = ledger
    old = _attempt(repository, "att_old", "lo_a", "pi_1", at=_at(3))
    _diagnose(repository, old, [GAP_CAUSES], at=_at(3, 1))
    new = _attempt(repository, "att_new", "lo_a", "pi_2", at=_at(2), correctness=0.9)
    _attempt(repository, "att_right", "lo_a", "pi_3", at=_at(1), correctness=1.0)
    _attempt(repository, "att_hinted", "lo_a", "pi_4", at=_at(1, 5), correctness=0.0, hints=1)
    record = _sensor(vault, repository, ["lo_a"])["lo_a"]
    assert record["attempt_id"] == new and record["status"] == MC.NONE and record["p_gap"] is None
    cold = [{"created_at": _at(3), "correctness": 0.75}, {"created_at": _at(2), "correctness": 0.9},
            {"created_at": _at(1), "correctness": 1.0}]
    assert missed_since(cold, None) == record["attempt_at"]
    assert MC.FULLY_RIGHT == 1.0
    # A lesson that ended after the miss makes it no miss "since the last lesson".
    _exec(repository, "INSERT INTO lessons (id, driver, origin, entry, goal_text, learning_object_ids_json, doctrine_version, "
          "brief_version, algorithm_version, opened_at, closed_at, goal_json, close_reason) VALUES ('les1', 'desktop', 'learner_pick', "
          "'learning_object', 'g', '[\"lo_a\"]', 'd', 'b', 'mvp-0.57', ?, ?, '{}', 'learner_stop')", (_at(0.5), _at(0.4)))
    assert _sensor(vault, repository, ["lo_a"]) == {}


@pytest.mark.parametrize("setup, status", [
    ("pending", MC.PENDING), ("failed", MC.FAILED), ("none", MC.NONE), ("not_needed", MC.NOT_APPLICABLE),
])
def test_pending_failed_and_absent_diagnoses_are_explicit_never_a_slip(ledger, setup, status):
    vault, repository = ledger
    attempt = _attempt(repository, "att_x", "lo_a", "pi_1", at=_at(1))
    if setup == "pending":
        _pending(repository, attempt)
    elif setup == "failed":
        _diagnose(repository, attempt, [], at=_at(1, 1), status="failed", error="boom")
    elif setup == "not_needed":
        _diagnose(repository, attempt, [], at=_at(1, 1), status="skipped", error="not_needed")
    record = _sensor(vault, repository, ["lo_a"])["lo_a"]
    assert record["status"] == status
    assert record["p_gap"] is record["p_slip"] is record["p_unknown"] is None
    entry = MC.card_entry(record, topic="A", days_before=1.0, reference=[])
    assert "slip" not in json.dumps(entry["cause"]) and isinstance(entry["cause"], str)


def test_a_diagnosis_written_after_the_decision_is_not_read(ledger):
    vault, repository = ledger
    attempt = _attempt(repository, "att_x", "lo_a", "pi_1", at=_at(1))
    _diagnose(repository, attempt, [SLIP_CAUSES], at=_at(0, 30))
    assert _sensor(vault, repository, ["lo_a"])["lo_a"]["status"] == MC.NONE
    assert _sensor(vault, repository, ["lo_a"], now=_at(0, 31))["lo_a"]["status"] == MC.DIAGNOSED


def _factor_with_episode(repository, attempt_id, *, posterior, at, completed=True):
    gap = repository.append_causal_hypothesis(episode_key="ep_gap", attempt_id=attempt_id, learning_object_id="lo_a",
                                              cause_scope="learner_state", statement="gap", statement_normalized="gap",
                                              status="candidate")
    slip = repository.append_causal_hypothesis(episode_key="ep_slip", attempt_id=attempt_id, learning_object_id="lo_a",
                                               cause_scope="transient_execution", statement="slip",
                                               statement_normalized="slip", status="candidate")
    _exec(repository, "INSERT INTO unresolved_cause_factors (id, attempt_id, candidate_causes_json, status, algorithm_version, "
          "created_at, updated_at) VALUES ('fac1', ?, '[]', 'open', 'mvp-0.57', ?, ?)", (attempt_id, at, at))
    body = {gap["id"]: posterior[0], slip["id"]: posterior[1], "other_or_unknown": posterior[2]}
    _exec(repository, "INSERT INTO probe_episodes (id, learning_object_id, status, trigger, minimum_independent_observations, "
          "maximum_observations, algorithm_version, created_at, updated_at, origin, completed_at, completion_posterior_json) "
          "VALUES ('ep1', 'lo_a', ?, 'initial', 2, 4, 'mvp-0.57', ?, ?, 'causal_factor:fac1', ?, ?)",
          ("complete" if completed else "pending_items", at, at, at if completed else None,
           json.dumps(body) if completed else None))


def test_a_probe_posterior_on_the_misss_factor_overrides_the_prior_weights(ledger):
    vault, repository = ledger
    attempt = _attempt(repository, "att_x", "lo_a", "pi_1", at=_at(2))
    _diagnose(repository, attempt, [SLIP_CAUSES], at=_at(2, 1))
    _factor_with_episode(repository, attempt, posterior=(0.6, 0.3, 0.1), at=_at(1))
    record = _sensor(vault, repository, ["lo_a"])["lo_a"]
    assert record["basis"] == MC.BASIS_POSTERIOR and record["episode_id"] == "ep1"
    assert (record["p_gap"], record["p_slip"], record["p_unknown"]) == pytest.approx((0.6, 0.3, 0.1))
    assert record["prior"] == pytest.approx({"gap": 0.25, "slip": 0.75, "unknown": 0.0})


def test_an_episode_with_no_posterior_yet_leaves_the_prior_weights(ledger):
    vault, repository = ledger
    attempt = _attempt(repository, "att_x", "lo_a", "pi_1", at=_at(2))
    _diagnose(repository, attempt, [SLIP_CAUSES], at=_at(2, 1))
    _factor_with_episode(repository, attempt, posterior=(0.6, 0.3, 0.1), at=_at(1), completed=False)
    record = _sensor(vault, repository, ["lo_a"])["lo_a"]
    assert record["basis"] == MC.BASIS_PRIOR and record["p_slip"] == pytest.approx(0.75)


def test_a_my_gap_mark_is_recorded_beside_the_probabilities_never_folded_in(ledger):
    from learnloop.db.stores import hypothesis_marks as marks_store

    vault, repository = ledger
    attempt = _attempt(repository, "att_x", "lo_a", "pi_1", at=_at(2))
    _diagnose(repository, attempt, [SLIP_CAUSES], at=_at(2, 1))
    hypothesis = repository.append_causal_hypothesis(
        episode_key="ep_mine", attempt_id=attempt, learning_object_id="lo_a", cause_scope="learner_state",
        statement=SECRET, statement_normalized=SECRET.lower(), status="candidate")
    with repository.atomic(), repository.connection() as connection:
        marks_store.insert_mark(connection, {
            "id": "mk1", "attempt_id": attempt, "learning_object_id": "lo_a", "hypothesis_version_id": hypothesis["id"],
            "hypothesis_key": "ep_mine", "mark": "my_gap", "display_order_json": "[]", "surface": "feedback",
            "probe_answered": 0, "created_at": _at(1)})
    record = _sensor(vault, repository, ["lo_a"])["lo_a"]
    assert record["learner_marked_my_gap"] == [{"hypothesis_key": "ep_mine", "class": MC.GAP}]
    assert record["p_slip"] == pytest.approx(0.75), "a statement is not evidence"
    entry = MC.card_entry(record, topic="A", days_before=1.0, reference=[0.1])
    assert entry["learner_said_my_gap"] == ["gap"]
    assert SECRET not in json.dumps(entry) and SECRET.lower() not in json.dumps(entry)


def test_nothing_protected_or_answer_restating_reaches_the_card_and_probe_attempts_gain_the_cause(ledger):
    vault, repository = ledger
    probe = _attempt(repository, "att_probe", "lo_a", "pi_probe", at=_at(1), attempt_type="diagnostic_probe",
                     correctness=0.0)
    _diagnose(repository, probe, [GAP_CAUSES], at=_at(1, 1))
    _surprise(repository, probe, 0.3, at=_at(1))
    offer = BlockCandidate(candidate_id="lesson_offer:lo_a", lane="new", action="instruct", subtype=LESSON_OFFER_SUBTYPE,
                           learning_object_ids=("lo_a",), item_ids=(), reading=None, est_minutes=10.0, planner_value=0.0, reason="")
    with repository.connection() as connection:
        entries = OCARD.miss_cause_entries(vault, connection, [offer], served_at=NOW)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["cause"] == {"gap": 0.75, "slip": 0.25, "unknown": 0.0}
    assert entry["diagnosis_status"] == MC.DIAGNOSED and "worse than the mastery model expected" in entry["surprise"]
    text = json.dumps(entries)
    assert SECRET not in text and "statement" not in text and "analysis" not in text
    assert set(entry) <= {"evidence_id", "days_before", "topic", "diagnosis_status", "surprise", "cause", "cause_from",
                          "learner_said_my_gap"}


def test_the_card_shows_offer_and_repair_topics_only_and_names_v4_only_with_an_entry(ledger):
    vault, repository = ledger
    for lo in ("lo_a", "lo_b", "lo_c"):
        _diagnose(repository, _attempt(repository, f"att_{lo}", lo, f"pi_{lo}", at=_at(1)), [SLIP_CAUSES], at=_at(1, 1))

    def block(lo, lane, subtype="completion_or_repair"):
        return BlockCandidate(candidate_id=f"b_{lo}", lane=lane, action="practice", subtype=subtype,
                              learning_object_ids=(lo,), item_ids=(), reading=None, est_minutes=5.0, planner_value=0.0, reason="")

    with repository.connection() as connection:
        entries = OCARD.miss_cause_entries(vault, connection, [block("lo_a", "repair"), block("lo_b", "maintain"),
                                                               block("lo_c", "new")], served_at=NOW)
    assert len(entries) == 1 and entries[0]["evidence_id"] == "attempt:att_lo_a"
    card = OCARD.decision_card(vault, repository, [block("lo_b", "maintain")], served_at=NOW, goals={}, session={},
                               budget=6000)
    assert card["state"]["card"] == OCARD.CARD_VERSION and OCARD.MISS_CAUSES not in card["state"]["history"]
    card = OCARD.decision_card(vault, repository, [block("lo_a", "repair")], served_at=NOW, goals={}, session={},
                               budget=6000)
    assert card["state"]["card"] == OCARD.CARD_VERSION_MISS_CAUSES and card["miss_causes"] == 1


def test_off_and_below_the_tag_the_card_is_the_predecessors(tmp_path, ledger):
    vault, repository = ledger
    _diagnose(repository, _attempt(repository, "att_a", "lo_a", "pi_a", at=_at(1)), [SLIP_CAUSES], at=_at(1, 1))
    repair = BlockCandidate(candidate_id="b", lane="repair", action="practice", subtype="completion_or_repair",
                            learning_object_ids=("lo_a",), item_ids=(), reading=None, est_minutes=5.0, planner_value=0.0, reason="")
    for toml, version in ((OFF, TAG), ("", OLD)):
        paths = create_basic_vault(tmp_path / f"v{version}{len(toml)}")
        set_algorithm_version(paths, version)
        if toml:
            append_config_toml(paths.root, toml)
        other = load_vault(paths.root)
        assert not miss_cause_sensor_on(other.config)
        with repository.connection() as connection:
            assert OCARD.miss_cause_entries(other, connection, [repair], served_at=NOW) == []
        assert OCARD.miss_cause_lines(other, repository, [repair], served_at=NOW, budget=6000) == []


# -- SG2: the value ------------------------------------------------------------------------------------------------------


def _inputs(weights=None, *, gap=None, slip=None, gamma=(0.2, 0.01)) -> V.Inputs:
    causes = None
    if weights is not None:
        causes = V.CauseSplit(gap=gap or gamma, slip=slip or (0.0, gamma[1]), weights=weights)
    return V.Inputs(
        topics=(V.Topic(lo="lo_a", eta_mean=0.0, eta_var=0.3, practiced=True, stability=5.0, elapsed_days=2.0,
                        undated_density=0.2),
                V.Topic(lo="lo_b", eta_mean=0.5, eta_var=0.3, practiced=True, stability=5.0, elapsed_days=2.0,
                        undated_density=0.2)),
        dated=(V.DatedUse(goal_id="g", lo="lo_a", at_days=10.0, weight=1.0),),
        session_minutes=5.0, price=V.Price(kappa0=0.1, remembered=30.0), tail_block_minutes=10.0, tail_block_items=2,
        horizon_days=14.0, fsrs_weights=tuple(FSRS6_DEFAULT_WEIGHTS),
        learning=V.Learning(gamma=gamma, causes=causes))


ACTIONS = [V.Action(ref="lesson", kind=V.LESSON, item_los=("lo_a",), minutes=10.0, mass=0.5),
           V.Action(ref="repair", kind=V.REPAIR, item_los=("lo_a",), minutes=6.0),
           V.Action(ref="review_b", kind=V.REVIEW, item_los=("lo_b",), minutes=6.0)]


def _q(inputs) -> dict[str, float]:
    evaluation = V.evaluate(inputs, ACTIONS, draws=16, seed="sg")
    return {row.ref: row.q for row in evaluation.valued}


def test_the_nov_7_shape_a_slip_is_worth_less_than_a_gap_by_the_priors_difference_only():
    """A 0.75 miss on ``lo_a``: diagnosed slip vs diagnosed gap, at the seeded priors (γ_gap's is γ's; γ_slip's is centred
    at 0 with γ's variance). The lesson and the repair are worth less after the slip; the topic with no diagnosis
    (``lo_b``) is valued as before; and a pure gap at the seeded prior is the predecessor's value draw for draw."""

    before = _q(_inputs())
    gap = _q(_inputs({"lo_a": (1.0, 0.0, 0.0)}))
    slip = _q(_inputs({"lo_a": (0.0, 1.0, 0.0)}))
    assert gap == before, "a pure gap at gamma's prior is the predecessor exactly"
    assert slip["lesson"] < gap["lesson"] and slip["repair"] < gap["repair"]
    model_gap = V._Model(_inputs({"lo_a": (1.0, 0.0, 0.0)}), 16, "sg")
    model_slip = V._Model(_inputs({"lo_a": (0.0, 1.0, 0.0)}), 16, "sg")
    gain_gap, believed_gap = model_gap._cause_gain(0, 0.5)
    gain_slip, believed_slip = model_slip._cause_gain(0, 0.5)
    # By the prior's difference only: the same draws, shifted by (mean_gap - mean_slip) * mass.
    assert np.allclose(gain_gap - gain_slip, 0.2 * 0.5) and believed_gap - believed_slip == pytest.approx(0.1)
    assert model_gap._cause_gain(1, 0.5) is None, "a topic with no diagnosed miss keeps gamma"


def test_a_mixed_diagnosis_values_between_and_unknown_mass_takes_gamma():
    mixed = _q(_inputs({"lo_a": (0.5, 0.5, 0.0)}))
    gap, slip = _q(_inputs({"lo_a": (1.0, 0.0, 0.0)})), _q(_inputs({"lo_a": (0.0, 1.0, 0.0)}))
    assert slip["lesson"] < mixed["lesson"] < gap["lesson"]
    assert _q(_inputs({"lo_a": (0.0, 0.0, 1.0)})) == _q(_inputs()), "unknown mass is gamma's"


def test_the_belief_world_reads_the_slopes_means_only():
    model = V._Model(_inputs({"lo_a": (0.0, 1.0, 0.0)}), 8, "sg")
    belief = model._belief_model()
    assert belief.inputs.learning.causes.slip == (0.0, 0.0) and belief.inputs.learning.causes.gap == (0.2, 0.0)


def test_at_beta_zero_the_sensor_is_the_diagnosiss():
    record = {"p_gap": 0.25, "p_slip": 0.6, "p_unknown": 0.15}
    assert MC.calibrated(record, 0.0, 2.0) == (0.25, 0.6, 0.15)
    assert MC.calibrated(record, 1.3, 0.0) == (0.25, 0.6, 0.15)
    shifted = MC.calibrated(record, 1.0, 1.0)
    assert shifted[0] == pytest.approx(1 / (1 + math.exp(-(math.log(0.25 / 0.75) + 1.0))))
    assert sum(shifted) == pytest.approx(1.0) and shifted[1] / shifted[2] == pytest.approx(0.6 / 0.15)
    assert MC.calibrated({"p_gap": 1.0, "p_slip": 0.0, "p_unknown": 0.0}, 5.0, 3.0) == (1.0, 0.0, 0.0)


def test_with_no_data_beta_and_the_slopes_are_their_seeded_priors(ledger):
    vault, repository = ledger
    attempt = _attempt(repository, "att_x", "lo_a", "pi_1", at=_at(1))
    _diagnose(repository, attempt, [SLIP_CAUSES], at=_at(1, 1))
    records = _sensor(vault, repository, ["lo_a"])
    with repository.connection() as connection:
        weights, record = MC.value_inputs(connection, vault.config, records, (0.2, 0.01), NOW)
    assert record["beta"]["mean"] == 0.0 and record["beta"]["n"] == 0 and record["beta"]["prior"] == [0.0, 1.0]
    assert weights == {"lo_a": (0.25, 0.75, 0.0)}
    assert record["slopes"]["gap"] == [0.2, 0.01] and record["slopes"]["slip"] == [0.0, 0.01]
    assert record["slopes"]["n"] == 0 and SELF_SELECTED_WORD in record["beta"]["label"]


SELF_SELECTED_WORD = "self-selected"


def test_betas_fit_excludes_a_lesson_or_another_attempt_between_the_miss_and_the_check(ledger):
    vault, repository = ledger
    # lo_a: miss, then the next cold check right after, nothing between: a row.
    a = _attempt(repository, "a1", "lo_a", "pi_a1", at=_at(5))
    _diagnose(repository, a, [SLIP_CAUSES], at=_at(5, 1))
    _surprise(repository, a, 0.4, at=_at(5))
    _attempt(repository, "a2", "lo_a", "pi_a2", at=_at(4), correctness=1.0)
    # lo_b: a repair (a primed attempt) between the miss and the check.
    b = _attempt(repository, "b1", "lo_b", "pi_b1", at=_at(5))
    _diagnose(repository, b, [GAP_CAUSES], at=_at(5, 1))
    _surprise(repository, b, 0.1, at=_at(5))
    _attempt(repository, "b_repair", "lo_b", "pi_b1", at=_at(4, 1), primed=1, correctness=1.0)
    _attempt(repository, "b2", "lo_b", "pi_b2", at=_at(4, 2), correctness=0.0)
    # lo_c: a lesson opened between the miss and the check.
    c = _attempt(repository, "c1", "lo_c", "pi_c1", at=_at(5))
    _diagnose(repository, c, [GAP_CAUSES], at=_at(5, 1))
    _surprise(repository, c, 0.2, at=_at(5))
    _exec(repository, "INSERT INTO lessons (id, driver, origin, entry, goal_text, learning_object_ids_json, doctrine_version, "
          "brief_version, algorithm_version, opened_at, closed_at, goal_json, close_reason) VALUES ('les_c', 'desktop', 'learner_pick', "
          "'learning_object', 'g', '[\"lo_c\"]', 'd', 'b', 'mvp-0.57', ?, ?, '{}', 'learner_stop')", (_at(4, 10), _at(4, 20)))
    _attempt(repository, "c2", "lo_c", "pi_c2", at=_at(4, 30), correctness=0.0)
    with repository.connection() as connection:
        rows_, counts = MC.beta_rows(connection, vault.config, NOW)
        fit = MC.beta_fit(connection, vault.config, NOW)
    assert [row["attempt_id"] for row in rows_] == ["a1"]
    assert counts["intervening"] == 2 and counts["rows"] == 1
    assert rows_[0]["missed_again"] == 0.0 and rows_[0]["p_gap"] == pytest.approx(0.25)
    assert fit["n"] == 1 and fit["variance"] < 1.0


def test_beta_moves_with_the_data_in_the_direction_the_outcomes_point(ledger):
    """Misses with high surprise were followed by more misses (relative to the diagnosis): beta goes positive."""

    vault, repository = ledger
    for n in range(12):
        lo = f"lo_{n}"
        miss = _attempt(repository, f"m{n}", lo, f"pi_{n}a", at=_at(20 - n))
        _diagnose(repository, miss, [SLIP_CAUSES], at=_at(20 - n, 1))
        high = n % 2 == 0
        _surprise(repository, miss, 0.5 if high else 0.01, at=_at(20 - n))
        _attempt(repository, f"n{n}", lo, f"pi_{n}b", at=_at(19.5 - n), correctness=0.0 if high else 1.0)
    with repository.connection() as connection:
        fit = MC.beta_fit(connection, vault.config, NOW)
    assert fit["n"] == 12 and fit["mean"] > 0.0


def test_the_cause_slopes_learn_from_a_lesson_that_ran_from_a_diagnosed_offer(ledger):
    vault, repository = ledger
    frozen = {"status": MC.DIAGNOSED, "p_gap": 0.0, "p_slip": 1.0, "p_unknown": 0.0}
    detail = {"lesson_offer": {"learning_object_id": "lo_a", "miss_cause": frozen, "mass": {"mean": 0.5},
                               "card": {"candidates": [{"predicted_success": 0.4}]}}}
    _exec(repository, "INSERT INTO router_decisions (id, receipt_key, decision_kind, surface, mode, policy, algorithm_version, "
          "log_version, snapshot_hash, candidates_json, exclusions_json, candidate_count, chosen_ref, propensity, "
          "propensity_kind, detail_json, created_at) VALUES ('rd1', 'k', 'plan_block', 'desktop', 'live', 'p', 'mvp-0.57', "
          "'v1', 'h', '[]', '[]', 0, 'lesson_offer:lo_a', 0.5, 'exact', ?, ?)", (json.dumps(detail), _at(3)))
    _exec(repository, "INSERT INTO lessons (id, driver, origin, origin_ref, entry, goal_text, learning_object_ids_json, "
          "doctrine_version, brief_version, algorithm_version, opened_at, closed_at, goal_json, close_reason) VALUES ('les1', 'desktop', "
          "'router', 'rd1', 'learning_object', 'g', '[\"lo_a\"]', 'd', 'b', 'mvp-0.57', ?, ?, '{}', 'learner_stop')", (_at(3, 1), _at(3, 20)))
    _attempt(repository, "after", "lo_a", "pi_new", at=_at(2), correctness=1.0)
    with repository.connection() as connection:
        slopes = MC.cause_slopes(connection, (0.2, 0.01), NOW)
    assert slopes["n"] == 1 and slopes["lessons"] == ["les1"]
    assert slopes["slip"][0] > 0.0 and slopes["slip"][1] < 0.01, "a right answer after a slip's lesson moves gamma_slip up"
    assert slopes["gap"] == [0.2, 0.01], "a pure slip says nothing about gamma_gap"


def test_nothing_adds_a_threshold():
    """Static (spec §8): no comparison in the new modules against a fixed number other than a probability's own bounds
    (0 and 1, where a logit is finite) and an empty guard; and the value's split compares nothing at all."""

    root = pathlib.Path(MC.__file__).resolve().parent
    for name in ("miss_cause.py", "miss_cause_report.py"):
        tree = ast.parse((root / name).read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            constants = [part for part in (node.left, *node.comparators) if isinstance(part, ast.Constant)
                         and isinstance(part.value, (int, float)) and not isinstance(part.value, bool)]
            constants += [element for part in (node.left, *node.comparators) if isinstance(part, ast.Tuple)
                          for element in part.elts if isinstance(element, ast.Constant)]
            assert all(constant.value in (0, 1) for constant in constants), (name, ast.unparse(node))
    import inspect
    import textwrap

    tree = ast.parse(textwrap.dedent(inspect.getsource(V._Model._cause_gain)))
    numbers = [node for node in ast.walk(tree) if isinstance(node, ast.Compare)
               for part in (node.left, *node.comparators) if isinstance(part, ast.Constant)
               and isinstance(part.value, (int, float)) and not isinstance(part.value, bool)]
    assert not numbers, "the split compares nothing against a number"


# -- the decisions -------------------------------------------------------------------------------------------------------


def _diagnosed_env(tmp_path, toml, *, seed, version=TAG, causes=SLIP_CAUSES):
    env = mixture_env(tmp_path, fake_runtime(seed=seed), version=version, toml=toml, session_id="s1")
    for lo, item in (("lo_diag", "pi_diag_easy"), ("lo_r1", "pi_r1a")):
        attempt = _attempt(env.repository, f"att_miss_{lo}", lo, item, at=_at(1))
        _diagnose(env.repository, attempt, [causes], at=_at(1, 1))
        _surprise(env.repository, attempt, 0.2, at=_at(1))
    return env


@pytest.fixture
def twins(tmp_path, monkeypatch):
    join_carried_valuations(monkeypatch)
    pinned = _pin(monkeypatch)

    def build(name, toml, version=TAG, causes=SLIP_CAUSES):
        env = _diagnosed_env(tmp_path / name, toml, seed=pinned, version=version, causes=causes)
        run(env)
        return env

    return build


@pytest.mark.usefixtures("offerable")
def test_sg1_freezes_the_sensor_and_every_number_is_the_predecessors(twins):
    on = twins("on", SENSOR_ONLY)
    off = twins("off", OFF)
    below = twins("below", QUIET, version=OLD)
    on_traces, off_traces, below_traces = _traces(on), _traces(off), _traces(below)
    assert on_traces and len(on_traces) == len(off_traces) == len(below_traces)
    assert [_numbers(t) for t in on_traces] == [_numbers(t) for t in off_traces]

    def unversioned(trace):
        # RO6's generator key names the algorithm version (a change point at every tag), never a value.
        numbers = _numbers(trace)
        fit = dict(numbers["residual"].get("fit") or {})
        fit.pop("generator", None)
        return {**numbers, "residual": {**numbers["residual"], "fit": fit}}

    assert [unversioned(t) for t in on_traces] == [unversioned(t) for t in below_traces]
    assert all("miss_cause" not in t for t in off_traces + below_traces)
    frozen = [t for t in on_traces if "miss_cause" in t]
    assert frozen and all(set(t["miss_cause"]["topics"]) <= {"lo_diag", "lo_r1"} for t in frozen)
    assert all("in_value" not in t["miss_cause"] for t in frozen)
    sensors = [entry["sensors"][lo]["miss_cause"] for t in frozen for entry in t["candidates"].values()
               for lo in entry["sensors"] if isinstance(entry["sensors"][lo], dict) and "miss_cause" in entry["sensors"][lo]]
    assert sensors and all(s["status"] == MC.DIAGNOSED and not s["reached_qbar"] for s in sensors)
    offers = [row["detail_json"]["lesson_offers"] for row in rows(on) if (row["detail_json"].get("lesson_offers") or {})
              .get("status") == "offered"]
    assert offers and all(offer["miss_cause"]["p_slip"] == pytest.approx(0.75) for offer in offers)
    assert all("miss_cause" not in (row["detail_json"].get("lesson_offers") or {}) for row in rows(off))


@pytest.mark.usefixtures("offerable")
def test_sg2_moves_only_the_diagnosed_topics_values_and_the_logged_mu_replays(twins):
    on = twins("on", QUIET)
    sensor_only = twins("sensor", SENSOR_ONLY)
    on_traces, base_traces = _traces(on), _traces(sensor_only)
    assert on_traces and len(on_traces) == len(base_traces)
    moved = 0
    for got, base in zip(on_traces, base_traces):
        split = got["miss_cause"]["in_value"]
        assert split["beta"]["mean"] == 0.0 and split["slopes"]["slip"][0] == 0.0
        assert split["topics"] and set(split["topics"]) <= {"lo_diag", "lo_r1"}  # the support's diagnosed topics
        if set(got["candidates"]) != set(base["candidates"]):
            break  # an earlier draw served something else, so the plans have parted: nothing more to pair
        for ref, entry in got["candidates"].items():
            before = base["candidates"][ref]["terms"]
            if before is None or entry["kind"] in (V.PROBE, V.SEQUENCE):
                continue  # a probe's repair branch, or a sequence's repair step, may be on a diagnosed topic
            diagnosed = bool(set(entry.get("sensors") or {}) & set(split["topics"]))
            if entry["kind"] in (V.LESSON, V.REPAIR) and diagnosed:
                moved += entry["terms"]["q"] != before["q"]
            else:
                # Every other candidate is valued on the same draws with the same inputs: bit for bit.
                assert entry["terms"]["q"] == before["q"], ref
    assert moved, "a slip-attributed miss moves the diagnosed topics' lesson and repair values"
    # The logged propensities replay to the logged mu (the mix is unchanged).
    for row in rows(on):
        mixture = row["detail_json"].get("mixture") or {}
        if row["policy"] == mix.POLICY and mixture:
            recomputed = mix.recompute(mixture)
            for entry in row["candidates_json"]:
                if entry["ref"] in recomputed:
                    assert entry["propensity"] == pytest.approx(recomputed[entry["ref"]], abs=1e-12)


def test_the_seed_ignores_the_switches_the_mark_and_the_offers_sensor():
    identity = {"v": 1, "objective": {"enabled": True}, "support": [
        {"candidate_id": "lesson_offer:lo", "annotations": {"lesson_offer": {"reason": "cold_missed"}}}]}
    with_sg = {**identity, "objective": {"enabled": True, "miss_cause_sensor": True, "miss_cause_in_value": False},
               "miss_cause": {"lo": ["diagnosed"]},
               "support": [{"candidate_id": "lesson_offer:lo", "annotations": {
                   "lesson_offer": {"reason": "cold_missed", "miss_cause": {"status": "diagnosed"}}}}]}
    assert OC.numeric_seed(with_sg) == OC.numeric_seed(identity)
    assert OC._hash(with_sg) != OC._hash(identity), "the key still names them, so a flip starts a new job"
    interrupt = {"v": 1, "offer": with_sg["support"][0]}
    assert OC.numeric_seed(interrupt) == OC.numeric_seed({"v": 1, "offer": identity["support"][0]})


def test_the_gates_need_the_tag_the_objective_and_sg2_needs_sg1(tmp_path):
    def config(toml, version=TAG):
        paths = create_basic_vault(tmp_path / f"v{abs(hash((toml, version)))}")
        set_algorithm_version(paths, version)
        if toml:
            append_config_toml(paths.root, toml)
        return load_vault(paths.root).config

    on = config("")
    assert miss_cause_sensor_on(on) and miss_cause_in_value_on(on)
    assert not miss_cause_sensor_on(config("", OLD)) and not miss_cause_in_value_on(config("", OLD))
    off = config("[router_objective]\nmiss_cause_sensor = false\n")
    assert not miss_cause_sensor_on(off) and not miss_cause_in_value_on(off)
    value_off = config("[router_objective]\nmiss_cause_in_value = false\n")
    assert miss_cause_sensor_on(value_off) and not miss_cause_in_value_on(value_off)
    assert not miss_cause_sensor_on(config("[router_objective]\nenabled = false\n"))


# -- the report -----------------------------------------------------------------------------------------------------------


def test_the_report_names_its_labels(ledger):
    vault, repository = ledger
    offer = {"status": "offered", "learning_object_id": "lo_a",
             "miss_cause": {"status": MC.DIAGNOSED, "p_gap": 0.25, "p_slip": 0.75, "p_unknown": 0.0}}
    for n, chosen in enumerate(("lesson_offer:lo_a", "block_x")):
        _exec(repository, "INSERT INTO router_decisions (id, receipt_key, decision_kind, surface, mode, policy, "
              "algorithm_version, log_version, snapshot_hash, candidates_json, exclusions_json, candidate_count, chosen_ref, "
              "propensity, propensity_kind, detail_json, created_at) VALUES (?, ?, 'plan_block', 'desktop', 'live', 'p', "
              "'mvp-0.57', 'v1', 'h', '[]', '[]', 0, ?, 0.5, 'exact', ?, ?)",
              (f"rd{n}", f"k{n}", chosen, json.dumps({"lesson_offers": offer}), _at(3, n)))
    _attempt(repository, "later", "lo_a", "pi_new", at=_at(2), correctness=1.0)
    with repository.connection() as connection:
        report = MCR.section(connection)
    assert report["available"] and report["offers_with_a_sensor"] == 2 and report["statuses"] == {MC.DIAGNOSED: 2}
    assert report["later_cold_results_label"] == MC.OBSERVATIONAL and "observational" in MC.OBSERVATIONAL
    assert report["by_class"]["all_offers"]["slip"]["expected_offers"] == pytest.approx(1.5)
    assert report["by_class"]["lesson_drawn_share"]["slip"] == pytest.approx(0.5)
    assert report["by_class"]["all_offers"]["slip"]["mean_later_cold_grade"] == pytest.approx(1.0)
    text = "\n".join(MCR.lines(report))
    assert "observational" in text and "Slip or gap" in text


