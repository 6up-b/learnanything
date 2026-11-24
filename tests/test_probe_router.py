"""G2: the action router is the probe decider on the automatic follow-up lane (``docs/reviews/refactor-g2-design.md``,
the owner's option f of 2026-11-20 and his 2026-11-23 ruling on the share).

At ``PROBE_ROUTER_ALGORITHM_VERSION`` a probe the router cannot yet value is not one of its policies' options: the
automatic lane decides before the probe is written, so its answer pattern is unknown and the probe earns no
information credit (the design's decision 1), and no policy may pick it. The mix decides between no intervention and a
lesson where one is offered; beside it, the probe coin asks the probe on a small randomized share of eligible misses,
at the stop coin's rate (``probe_coin.share``: one config field prices both arms), on its own seed, with an exact
served distribution and its own assignment row. No room to wait, no plan and the router switched off take the same
coin instead of asking the probe deterministically. Below the tag every one of these answers is the predecessor's.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    PROBE_ROUTER_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    probe_router_on,
)
from learnloop.daily_plan import engine as E
from learnloop.daily_plan.router_chooser import CONTINUE_CURRENT, INSERT_NOW, NO_INTERVENTION
from learnloop.followup_run import jobs, router
from learnloop.followup_serve import workflow as wf
from learnloop.plan_refs import LESSON_OFFER_PREFIX
from learnloop.router import mixture as mx
from learnloop.router_objective import assignments as A
from learnloop.router_objective import probe_coin as PC
from learnloop.router_objective import stop_coin as SC

from tests.followup_serve_helpers import AuthorFake, author_clients, miss_with_rivals, rival_causes_vault, run_jobs
from tests.ih2_lessons_compete_helpers import _author_refuses, _miss_env, draw  # noqa: F401 - ``draw`` is a fixture
from tests.probe_router_helpers import BEFORE_PROBE_ROUTER

#: The tag just below the probe router's: the predecessor whose answers stay below it.
BEFORE = BEFORE_PROBE_ROUTER
#: A plan whose stop coin (and so the probe coin) is at 0.2, with no randomized checks in the way.
COINS = '[router_objective]\nstop_coin = 0.2\ncheck_rate = "off"\n'


def _arm(monkeypatch, u: float) -> None:
    """The probe coin's own uniform, fixed: below the share asks the probe, at or above it the mix's draw stands."""

    monkeypatch.setattr(PC, "draw_uniform", lambda seed: u)


def _gate(env):
    from learnloop.daily_plan.objective_chooser import ObjectiveFollowupGate

    restraint = env.policy.restraint
    return ObjectiveFollowupGate(env.vault, env.repository, restraint.runtime, frame=restraint.frame,
                                 card_builder=restraint.card_builder, session_id=env.session_id, clock=env.clock,
                                 may_defer=False)


def _assignments(repository) -> list[dict]:
    with repository.connection() as connection:
        rows = connection.execute("SELECT * FROM policy_experiment_assignments ORDER BY created_at, id").fetchall()
    out = []
    for row in rows:
        item = dict(row)
        item["detail_json"] = json.loads(item["detail_json"] or "{}")
        out.append(item)
    return out


def _router_rows(repository) -> list[dict]:
    with repository.connection() as connection:
        rows = connection.execute("SELECT * FROM router_decisions WHERE decision_kind = 'plan_interrupt' "
                                  "ORDER BY created_at, id").fetchall()
    out = []
    for row in rows:
        item = dict(row)
        item["detail_json"] = json.loads(item["detail_json"] or "{}")
        out.append(item)
    return out


# -- the tag and the one function that prices the share -------------------------------------------------------------


def test_the_tag_and_its_predicate_reads_the_vault_tag_alone():
    assert SUCCESSOR_CHAIN[-2] == PROBE_ROUTER_ALGORITHM_VERSION and LATEST_ALGORITHM_VERSION == SUCCESSOR_CHAIN[-1]
    assert probe_router_on(SimpleNamespace(algorithms=SimpleNamespace(algorithm_version=PROBE_ROUTER_ALGORITHM_VERSION)))
    assert not probe_router_on(SimpleNamespace(algorithms=SimpleNamespace(algorithm_version=BEFORE)))


def test_the_share_is_the_stop_coins_rate_read_through_one_function():
    from learnloop.config.schema import LearnLoopConfig

    config = LearnLoopConfig()
    assert PC.share(config) == config.router_objective.stop_coin == 0.05
    moved = config.model_copy(update={"router_objective": config.router_objective.model_copy(update={"stop_coin": 0.2})})
    assert PC.share(moved) == 0.2


def test_the_served_distribution_is_exact_and_sums_to_one():
    mu = {NO_INTERVENTION: 0.7, "lesson_offer:x": 0.3}
    served = PC.served_distribution(mu, 0.2, probe_ref=INSERT_NOW)
    assert served == pytest.approx({INSERT_NOW: 0.2, NO_INTERVENTION: 0.8 * 0.7, "lesson_offer:x": 0.8 * 0.3})
    assert sum(served.values()) == pytest.approx(1.0)
    # A probe already in the mix's support is refused: the coin is the only way an unlearned probe is served.
    with pytest.raises(ValueError):
        PC.served_distribution({INSERT_NOW: 0.5, NO_INTERVENTION: 0.5}, 0.2, probe_ref=INSERT_NOW)


def test_the_coin_serves_the_probe_below_the_share_and_the_mix_otherwise(monkeypatch):
    mu = {NO_INTERVENTION: 1.0}
    _arm(monkeypatch, 0.1)
    asked = PC.flip("seed", 0.2, probe_ref=INSERT_NOW, mu=mu, drawn=NO_INTERVENTION)
    assert (asked.arm, asked.served, asked.propensity, asked.served_propensity) == (PC.ASK, INSERT_NOW, 0.2, 0.2)
    _arm(monkeypatch, 0.2)
    kept = PC.flip("seed", 0.2, probe_ref=INSERT_NOW, mu=mu, drawn=NO_INTERVENTION)
    assert (kept.arm, kept.served, kept.served_propensity) == (PC.POLICY, NO_INTERVENTION, pytest.approx(0.8))
    row = PC.pending_assignment(asked, seed="seed", support=[INSERT_NOW, NO_INTERVENTION])
    assert (row["experiment_id"], row["variant"], row["propensity"], row["seed"]) == (A.PROBE_COIN, PC.ASK, 0.2, "seed")
    assert row["detail"]["served_propensity"] == 0.2 and row["detail"]["rate_source"] == "router_objective.stop_coin"


def test_the_probe_coin_has_its_own_seed_and_experiment_independent_of_the_stop_coin():
    assert A.PROBE_COIN in A.EXPERIMENTS and A.PROBE_COIN != A.STOP_COIN
    # Its own seed function: never the mix's (whose stream the stop coin reads), whatever the boundary and decision.
    assert PC.seed_for("key", "decision") != mx.seed_for("key", "decision")
    assert PC.seed_for("key", "decision") != PC.seed_for("key", "other")
    assert PC.STAGE != "stop_coin" and SC.VERSION != PC.VERSION


# -- at the tag, on a plan --------------------------------------------------------------------------------------------


def test_at_the_tag_an_unwritten_probe_is_not_an_option_of_either_policy(tmp_path, monkeypatch):
    env, row = _miss_env(tmp_path, version=LATEST_ALGORITHM_VERSION, toml=COINS)
    assert probe_router_on(env.vault.config)
    _arm(monkeypatch, 0.9)
    outcome = _gate(env).decide_followup(E.latest_today(env), None, row, wait_feasible=True)
    assert outcome.chosen_ref == NO_INTERVENTION and outcome.propensity == pytest.approx(0.8)
    coin = outcome.record["probe_coin"]
    assert coin["arm"] == PC.POLICY and coin["rate"] == 0.2
    # The mix had one option (nothing for a model to choose), and the served distribution adds the coin's probe.
    assert outcome.record["mix_support"] == [NO_INTERVENTION]
    assert outcome.record["served_pi"] == pytest.approx({INSERT_NOW: 0.2, NO_INTERVENTION: 0.8})
    assert outcome.record["objective_followup"]["support"] == [INSERT_NOW, NO_INTERVENTION]
    assert outcome.record["decided_by"] == "probe_unlearned" and CONTINUE_CURRENT not in outcome.record["served_pi"]


def test_at_the_tag_the_coin_asks_the_probe_now_with_its_exact_propensity(tmp_path, monkeypatch):
    env, row = _miss_env(tmp_path, version=LATEST_ALGORITHM_VERSION, toml=COINS)
    _arm(monkeypatch, 0.05)
    outcome = _gate(env).decide_followup(E.latest_today(env), None, row, wait_feasible=True)
    assert (outcome.chosen_ref, outcome.propensity) == (INSERT_NOW, pytest.approx(0.2))
    (pending,) = outcome.record["ro5_assignments"]
    assert (pending["experiment_id"], pending["variant"]) == (A.PROBE_COIN, PC.ASK)


def test_at_the_tag_no_room_to_wait_no_longer_forces_the_probe(tmp_path, monkeypatch):
    env, row = _miss_env(tmp_path, version=LATEST_ALGORITHM_VERSION, toml=COINS)
    _arm(monkeypatch, 0.9)
    outcome = _gate(env).decide_followup(E.latest_today(env), None, row, wait_feasible=False)
    assert outcome.chosen_ref == NO_INTERVENTION and outcome.record["decided_by"] != "no_room_to_wait"
    assert outcome.wait_feasible is False


def test_at_the_tag_a_lesson_is_drawn_against_no_intervention_and_the_probe_only_by_the_coin(tmp_path, monkeypatch, draw):
    env, row = _miss_env(tmp_path, version=LATEST_ALGORITHM_VERSION, toml=COINS)
    record = E.latest_today(env)
    offer = E.interrupt_offer(env, record, None)
    assert offer.candidate is not None
    _arm(monkeypatch, 0.9)
    draw.prefer = (LESSON_OFFER_PREFIX,)
    outcome = _gate(env).decide_followup(record, None, row, wait_feasible=True, offer=offer)
    lesson = offer.candidate.candidate_id
    assert outcome.record["mixture"]["support"] == [NO_INTERVENTION, lesson]
    mu = outcome.record["mixture"]["mix_pi"]
    assert set(mu) == {NO_INTERVENTION, lesson}
    served = outcome.record["mixture"]["pi"]
    assert served[INSERT_NOW] == pytest.approx(0.2)
    assert served[lesson] == pytest.approx(0.8 * mu[lesson]) and sum(served.values()) == pytest.approx(1.0)
    assert outcome.chosen_ref == lesson and outcome.propensity == pytest.approx(served[lesson])


def test_at_the_tag_a_zero_share_never_asks_and_writes_no_assignment(tmp_path, monkeypatch):
    env, row = _miss_env(tmp_path, version=LATEST_ALGORITHM_VERSION)  # the helper's plan: stop_coin = 0
    _arm(monkeypatch, 0.0)
    outcome = _gate(env).decide_followup(E.latest_today(env), None, row, wait_feasible=True)
    assert (outcome.chosen_ref, outcome.propensity) == (NO_INTERVENTION, 1.0)
    assert "probe_coin" not in outcome.record and not outcome.record.get("ro5_assignments")


def test_at_the_tag_the_lane_logs_the_coin_with_its_decision(tmp_path, monkeypatch):
    env, row = _miss_env(tmp_path, version=LATEST_ALGORITHM_VERSION, toml=COINS)
    _author_refuses(monkeypatch)
    _arm(monkeypatch, 0.05)
    clients = SimpleNamespace(author=AuthorFake(), authoring=None, runtime=env.policy.restraint.runtime)
    jobs._run_probe_lane(env.vault, env.repository, row, choice=SimpleNamespace(factor_id="f", hypothesis_ids=()),
                         clients=clients, clock=env.clock)
    (decision,) = _router_rows(env.repository)
    assert decision["chosen_ref"] == INSERT_NOW and decision["propensity"] == pytest.approx(0.2)
    candidates = {c["ref"]: c for c in json.loads(decision["candidates_json"])}
    assert candidates[INSERT_NOW]["propensity"] == pytest.approx(0.2)
    # The rest of the served distribution is the mix's μ (here with the lesson the boundary offers), times 1 − r.
    mu = decision["detail_json"]["mixture"]["mix_pi"]
    assert candidates[NO_INTERVENTION]["propensity"] == pytest.approx(0.8 * mu[NO_INTERVENTION])
    assert sum(c["propensity"] for c in candidates.values()) == pytest.approx(1.0)
    assert candidates[CONTINUE_CURRENT]["feasible"] is False
    (assignment,) = [a for a in _assignments(env.repository) if a["experiment_id"] == A.PROBE_COIN]
    assert (assignment["unit_id"], assignment["variant"], assignment["propensity"]) == (decision["id"], PC.ASK, 0.2)
    assert assignment["seed"] == PC.seed_for(decision["detail_json"]["probe_coin"]["boundary_key"], decision["id"])


# -- at the tag, with no plan -----------------------------------------------------------------------------------------


def _no_plan(tmp_path, *, version: str = LATEST_ALGORITHM_VERSION):
    vault, repository, _paths = rival_causes_vault(tmp_path, version=version, config=COINS)
    _result, outcome = miss_with_rivals(vault, repository)
    return vault, repository, wf.get(repository, outcome.workflow_id)


def test_at_the_tag_with_no_plan_the_coin_decides_and_the_decision_is_logged(tmp_path, monkeypatch):
    vault, repository, row = _no_plan(tmp_path)
    _arm(monkeypatch, 0.9)
    run_jobs(vault, repository, clients=author_clients(AuthorFake()))
    after = wf.get(repository, row["id"])
    (decision,) = _router_rows(repository)
    assert (decision["chosen_ref"], decision["propensity"]) == (NO_INTERVENTION, pytest.approx(0.8))
    assert decision["detail_json"]["plan_id"] is None and decision["detail_json"]["probe_coin"]["arm"] == PC.POLICY
    assert (after["chosen_ref"], after["decision_id"]) == (NO_INTERVENTION, decision["id"])
    assert after["release_reason"] == wf.RELEASE_NO_INTERVENTION and not after["practice_item_id"]
    (assignment,) = _assignments(repository)
    assert (assignment["experiment_id"], assignment["variant"], assignment["unit_id"]) == (
        A.PROBE_COIN, PC.POLICY, decision["id"])


def test_at_the_tag_with_no_plan_the_coin_can_ask_and_the_probe_is_written(tmp_path, monkeypatch):
    vault, repository, row = _no_plan(tmp_path)
    _arm(monkeypatch, 0.0)
    run_jobs(vault, repository, clients=author_clients(AuthorFake()))
    after = wf.get(repository, row["id"])
    (decision,) = _router_rows(repository)
    assert (decision["chosen_ref"], decision["propensity"]) == (INSERT_NOW, pytest.approx(0.2))
    assert (after["state"], after["chosen_ref"]) == (wf.READY, router.ASK_NOW)
    assert after["feedback_released_at"] is None


def test_below_the_tag_with_no_plan_the_probe_is_asked_now_with_no_draw(tmp_path):
    vault, repository, row = _no_plan(tmp_path, version=BEFORE)
    run_jobs(vault, repository, clients=author_clients(AuthorFake()))
    after = wf.get(repository, row["id"])
    assert (after["state"], after["chosen_ref"], after["decision_id"]) == (wf.READY, router.ASK_NOW, None)
    assert _router_rows(repository) == [] and _assignments(repository) == []


def test_below_the_tag_the_plan_keeps_the_predecessors_three_arms_and_forced_probe(tmp_path):
    env, row = _miss_env(tmp_path, version=BEFORE, toml=COINS)
    gate = _gate(env)
    alone = gate.decide_followup(E.latest_today(env), None, row, wait_feasible=False)
    assert (alone.chosen_ref, alone.propensity, alone.record["decided_by"]) == (INSERT_NOW, 1.0, "no_room_to_wait")
    assert "probe_coin" not in alone.record


# -- the draws are pinned ---------------------------------------------------------------------------------------------


def test_a_pinned_test_gets_the_same_probe_coin_every_run():
    from tests import pinned_draws

    assert ("probe_coin", "learnloop.router_objective.probe_coin", "seed_for") in pinned_draws.SEED_SOURCES
