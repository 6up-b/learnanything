"""RO0 rows 9 and 13 (spec_router_objective_v1 §4): what the router believed at each decision."""

from __future__ import annotations

import re
import sqlite3

import pytest

from learnloop.daily_plan.engine import advance, build_plan, learner_pick
from learnloop.db.stores import router_objective as store
from learnloop.router_objective import decision_state as DS
from learnloop.scheduling.fsrs import retrievability
from tests.router_mixture_helpers import mixture_env, rows, run
from tests.router_model_fakes import fake_runtime

OFF = "[router_objective]\nreceipts = false\n"


def _plan(tmp_path, *, toml=None, budget=25.0):
    env = mixture_env(tmp_path, fake_runtime(), toml=toml)
    build_plan(env, kind="normal", budget=budget, remembered=int(budget), minutes_source="chip")
    return env


def _states(env):
    with env.repository.connection() as connection:
        ids = [str(row[0]) for row in connection.execute("SELECT decision_id FROM decision_state_receipts ORDER BY created_at, id")]
        return [store.decision_state(connection, decision_id) for decision_id in ids]


def test_every_plan_decision_has_its_state_with_the_decisions_transaction(tmp_path):
    env = _plan(tmp_path)
    run(env)
    decisions = rows(env)
    assert decisions
    states = {row["decision_id"]: row for row in _states(env)}
    assert {row["id"] for row in decisions} == set(states)
    for decision in decisions:
        state = states[decision["id"]]
        assert state["decision_kind"] == "plan_block" and state["session_id"] == env.session_id


def test_the_state_has_each_candidate_items_belief_and_minutes(tmp_path):
    env = _plan(tmp_path)
    advance(env, serve=True)
    decision = rows(env)[0]
    state = _states(env)[0]["state"]
    named = {item for entry in decision["candidates_json"] for item in entry.get("item_ids") or ()}
    assert named and named <= set(state["items"])
    some = next(row for row in state["items"].values() if row.get("s") is not None)
    assert {"s", "d", "r", "due"} <= set(some)
    assert 0.0 <= some["r"] <= 1.0
    for row in state["items"].values():
        assert row["minutes_source"].startswith("estimator:") and row["minutes"] > 0 and "n_item" in row


def test_the_state_has_each_candidate_los_belief(tmp_path):
    env = _plan(tmp_path)
    advance(env, serve=True)
    state = _states(env)[0]["state"]
    assert state["los"]
    for row in state["los"].values():
        assert set(row) <= {"logit_mean", "logit_variance", "evidence", "ad", "open_factors", "hypotheses", "misconceptions", "episodes"}


def test_goals_versions_minutes_pending_and_stop_are_recorded(tmp_path):
    env = _plan(tmp_path)
    run(env, steps=3)
    receipt = _states(env)[-1]
    state = receipt["state"]
    assert state["versions"]["algorithm"] == env.vault.config.algorithms.algorithm_version
    assert state["versions"]["config"] and state["versions"]["code"] and state["versions"]["fsrs_weights"]
    assert state["versions"]["estimator"]
    assert isinstance(state["goals"], list)
    assert state["active_minutes"]["basis"]
    assert receipt["day_active_minutes"] is not None
    assert set(state["pending_reports"]) == {"diagnosis_jobs", "followup_workflows", "clarifications"}
    assert receipt["pending_reports"] == sum(value or 0 for value in state["pending_reports"].values())
    assert state["stop"]["value"] is None and state["stop"]["value_source"] == "none_at_this_version"
    assert {"offered", "taken", "minutes_left"} <= set(state["stop"])


def test_a_stop_says_it_was_taken_and_offered(tmp_path):
    env = _plan(tmp_path, budget=6.0)
    run(env)
    stop = next(row for row in rows(env) if row["chosen_ref"] == "stop_for_today")
    receipt = next(row for row in _states(env) if row["decision_id"] == stop["id"])
    assert receipt["state"]["stop"]["taken"] is True


def test_a_pick_holds_the_verdict_in_force(tmp_path):
    env = _plan(tmp_path)
    advance(env, serve=True)
    other = next(item for item in ("pi_wide_01", "pi_wide_02", *env.vault.practice_items)
                 if item in env.vault.practice_items and not any(
                     item == (row["detail_json"].get("items") or [{}])[0].get("practice_item_id") for row in rows(env)))
    learner_pick(env, other)
    receipt = _states(env)[-1]
    assert receipt["state"]["pick_voi"] == {"verdict": "none_in_force"}
    assert other in receipt["state"]["items"]


def test_receipts_hold_ids_and_numbers(tmp_path):
    env = _plan(tmp_path)
    run(env, steps=3)
    for receipt in _states(env):
        for lo in env.vault.learning_objects.values():
            # A whole word: this vault's titles are two characters ("M2"), which random ULIDs in the state contain.
            assert not re.search(rf"(?<![0-9A-Za-z_]){re.escape(lo.title)}(?![0-9A-Za-z_])", str(receipt["state"]))
        for item in env.vault.practice_items.values():
            assert item.prompt not in str(receipt["state"])


def test_off_nothing_is_written_and_the_plan_stands(tmp_path):
    env = _plan(tmp_path, toml=OFF)
    run(env, steps=3)
    assert rows(env)
    assert _states(env) == []


def test_a_refused_state_rolls_back_alone_and_the_decision_stands(tmp_path, monkeypatch):
    def refused(*_args, **_kwargs):
        raise sqlite3.OperationalError("refused")

    monkeypatch.setattr(store, "_append", refused)
    env = _plan(tmp_path)
    advance(env, serve=True)
    monkeypatch.undo()
    assert rows(env) and _states(env) == []


def test_a_state_that_cannot_be_read_never_touches_the_decision(tmp_path, monkeypatch):
    def broken(*_args, **_kwargs):
        raise RuntimeError("no")

    monkeypatch.setattr(DS, "_lo_rows", broken)
    env = _plan(tmp_path)
    advance(env, serve=True)
    monkeypatch.undo()
    assert rows(env) and _states(env) == []


def test_ad_failing_is_said_and_everything_else_is_kept(tmp_path):
    env = _plan(tmp_path)

    def broken(_los):
        raise RuntimeError("no")

    material = DS.prepare(env.vault, env.repository, candidates=[{"learning_object_ids": ["lo"]}], session_id=None,
                          retrievability=retrievability, ad_fields=broken, clock=env.clock)
    assert '"status":"unavailable"' in material.content and material.candidate_los == 1


def test_a_path_that_reads_no_ad_says_so(tmp_path):
    env = _plan(tmp_path)
    material = DS.prepare(env.vault, env.repository, candidates=[], session_id=None, retrievability=retrievability,
                          clock=env.clock)
    assert f'"status":"{DS.AD_NOT_READ}"' in material.content


def test_the_candidate_shapes_of_the_ledger():
    class Item:
        learning_object_id = "lo_item"

    class Vault:
        practice_items = {"a": Item()}

    assert DS.candidate_ids(Vault, [
        {"ref": "x", "kind": "block", "item_ids": ["a"], "learning_object_ids": ["lo_block"]},
        {"ref": "b", "kind": "item", "learning_object_id": "lo_offer"},
        {"ref": "stop_for_today", "kind": "stop"},
    ]) == (["a", "b"], ["lo_block", "lo_offer", "lo_item"])


@pytest.mark.parametrize("column", ["decision_kind"])
def test_the_receipt_is_immutable(tmp_path, column):
    env = _plan(tmp_path)
    advance(env, serve=True)
    with env.repository.connection() as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(f"UPDATE decision_state_receipts SET {column} = 'x'")
        connection.rollback()
