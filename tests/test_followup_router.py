"""FG1 §5: the router decides before the item exists: three arms, one logged mixture, a binding."""

from __future__ import annotations

import json
from types import SimpleNamespace

from learnloop.daily_plan.engine import advance, build_plan
from learnloop.daily_plan.router_chooser import CONTINUE_CURRENT, INSERT_NOW, NO_INTERVENTION, FollowupGate
from learnloop.db.stores import followup_serve as store
from learnloop.followup_run import router
from learnloop.followup_serve import identity, workflow as wf
from learnloop.router import mixture as mx
from learnloop.router.outcomes import derive_router_outcomes

from tests.daily_plan_fakes import record_attempt
from tests.followup_serve_helpers import TAG
from tests.router_mixture_helpers import mixture_env, rows
from tests.router_model_fakes import fake_runtime
from tests.test_daily_plan_build import _wide_items

ITEM = "pi_diag_mid"


def _env(tmp_path, runtime, *, toml=None):
    env = mixture_env(tmp_path, runtime, version=TAG, toml=toml, items=lambda: list(_wide_items()))
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    record, step = advance(env, serve=True)
    assert step["kind"] == "item"
    env.clock.advance(1)
    record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                   session_id=env.session_id)
    env.clock.advance(1)
    return env, record


def _workflow(env, *, state=wf.PENDING, item=None, decision=None, held=1):
    record_attempt(env.repository, "pi_m1a", "lo_m1", env.clock.now(), session_id=env.session_id)
    with env.repository.connection() as connection:
        attempt_id = connection.execute("SELECT id FROM practice_attempts ORDER BY created_at DESC, id DESC").fetchone()[0]
    with env.repository.atomic(), env.repository.connection() as connection:
        store.insert_workflow(connection, {
            "id": "fw_test", "source_attempt_id": attempt_id, "revision_key": "joint",
            "learning_object_id": "lo_r1", "session_id": env.session_id, "surface": "desktop", "origin": "practice",
            "feedback_held": held, "created_at": env.now_iso(),
        })
    if item or state != wf.PENDING:
        wf.move(env.repository, "fw_test", to_state=state, reason="test", practice_item_id=item, decision_id=decision,
                factor_id="f", clock=env.clock)
    return wf.get(env.repository, "fw_test")


def _gate(env):
    restraint = env.policy.restraint
    return FollowupGate(env.vault, env.repository, restraint.runtime, frame=restraint.frame,
                        card_builder=restraint.card_builder, session_id=env.session_id, clock=env.clock,
                        may_defer=False)


def _row():
    return {"id": "fw_test", "learning_object_id": "lo_r1", "source_attempt_id": "att_x", "session_id": "s1",
            "factor_id": "f"}


def test_no_intervention_sits_in_the_mixture_with_its_floor(tmp_path):
    env, record = _env(tmp_path, fake_runtime())
    outcome = _gate(env).decide_followup(record, record.current_block(), _row(), wait_feasible=True)
    pi = outcome.record["mixture"]["pi"]
    assert set(pi) == {INSERT_NOW, CONTINUE_CURRENT, NO_INTERVENTION}
    assert abs(sum(pi.values()) - 1.0) < 1e-9
    epsilon = outcome.record["mixture"]["epsilon"]
    assert all(value >= epsilon - 1e-12 for value in pi.values())
    assert outcome.chosen_ref in pi and outcome.propensity == pi[outcome.chosen_ref]
    recomputed = mx.draw(
        outcome.record["mixture"]["support"],
        mx.component_distributions(outcome.record["mixture"]["support"], INSERT_NOW, {}),
        outcome.record["mixture"]["effective_weights"], epsilon, outcome.record["seed"],
    )
    assert recomputed.chosen == outcome.chosen_ref


def test_waiting_is_out_of_the_support_when_there_is_no_room(tmp_path):
    env, record = _env(tmp_path, fake_runtime())
    outcome = _gate(env).decide_followup(record, record.current_block(), _row(), wait_feasible=False)
    assert set(outcome.record["mixture"]["pi"]) == {INSERT_NOW, NO_INTERVENTION}
    assert outcome.wait_feasible is False


def _decide(env, record, chosen):
    outcome = _gate(env).decide_followup(record, record.current_block(), _row(), wait_feasible=True)
    return router.FollowupDecision(
        chosen, chosen, "mixture", propensity=outcome.record["mixture"]["pi"][chosen], record=dict(outcome.record),
        block_id=record.current_block().id, plan_id=record.id, plan_kind=record.kind, local_date="2026-11-03",
    )


def test_the_decision_row_is_itemless_and_names_the_workflow(tmp_path):
    env, record = _env(tmp_path, fake_runtime())
    row = _workflow(env)
    decision = router.record_decision(env.vault, env.repository, row, _decide(env, record, NO_INTERVENTION), clock=env.clock)
    logged = rows(env, "plan_interrupt")[-1]
    assert logged["id"] == decision.decision_id
    assert logged["chosen_practice_item_id"] is None and logged["chosen_ref"] == NO_INTERVENTION
    assert logged["receipt_key"].endswith(":fw_test")
    assert logged["detail_json"]["workflow"]["id"] == "fw_test"
    refs = {entry["ref"]: entry for entry in logged["candidates_json"]}
    assert refs[NO_INTERVENTION]["feasible"] and refs[INSERT_NOW]["item_ids"] == []
    assert logged["propensity"] == decision.propensity < 1.0 and logged["design"] == "model_mixture"
    assert wf.get(env.repository, "fw_test")["decision_id"] == logged["id"]


def test_the_binding_is_appended_and_the_row_stays_as_it_was(tmp_path):
    env, record = _env(tmp_path, fake_runtime())
    row = _workflow(env)
    decision = router.record_decision(env.vault, env.repository, row, _decide(env, record, INSERT_NOW), clock=env.clock)
    before = rows(env, "plan_interrupt")[-1]
    admitted = SimpleNamespace(practice_item_id=ITEM, presentation_id="pp_1")
    router.bind_item(env.repository, row, decision, admitted, clock=env.clock)
    router.record_outcome(env.repository, row, decision, outcome="generation_failed", clock=env.clock)
    assert rows(env, "plan_interrupt")[-1] == before
    with env.repository.connection() as connection:
        bound = store.bindings_for_decision(connection, decision.decision_id)
    assert bound["item"]["practice_item_id"] == ITEM and bound["item"]["probe_presentation_id"] == "pp_1"
    assert bound["outcome"]["outcome"] == "generation_failed"


def _outcomes(env):
    with env.repository.connection() as connection:
        return {row["decision_id"]: row for row in derive_router_outcomes(connection, reader_exposures=())}


def test_outcome_joins_follow_the_binding(tmp_path):
    env, record = _env(tmp_path, fake_runtime())
    row = _workflow(env)
    decision = router.record_decision(env.vault, env.repository, row, _decide(env, record, INSERT_NOW), clock=env.clock)
    router.bind_item(env.repository, row, decision, SimpleNamespace(practice_item_id="pi_m2a", presentation_id="pp_1"),
                     clock=env.clock)
    env.clock.advance(1)
    record_attempt(env.repository, "pi_m2a", "lo_m2", env.clock.now(), session_id=env.session_id)
    outcome = _outcomes(env)[decision.decision_id]
    assert outcome["action_attempt_id"] is not None
    assert json.loads(outcome["detail_json"]).get("no_outcome") is None


def test_with_no_binding_a_decision_has_no_action_to_follow(tmp_path):
    env, record = _env(tmp_path, fake_runtime())
    row = _workflow(env)
    decision = router.record_decision(env.vault, env.repository, row, _decide(env, record, INSERT_NOW), clock=env.clock)
    assert _outcomes(env)[decision.decision_id]["action_attempt_id"] is None


def test_data_captures_objective_is_frozen_for_every_arm(tmp_path):
    env, record = _env(tmp_path, fake_runtime())
    row = _workflow(env)
    decision = router.record_decision(env.vault, env.repository, row, _decide(env, record, NO_INTERVENTION), clock=env.clock)
    with env.repository.connection() as connection:
        objective = dict(connection.execute(
            "SELECT * FROM decision_objectives WHERE decision_id = ?", (decision.decision_id,)).fetchone())
    assert objective["arm"] == "no_intervention" and objective["learning_object_id"] == "lo_r1"


# -- the plan's end -----------------------------------------------------------------------------


def _ready(env, *, state=wf.READY, decision=None):
    row = _workflow(env, state=state, item=ITEM, decision=decision)
    identity.register(env.repository, practice_item_id=ITEM, revision="r", source="workflow", workflow_id="fw_test",
                      clock=env.clock)
    return row


def test_ask_now_is_what_next_opens(tmp_path):
    env, _record = _env(tmp_path, fake_runtime())
    assert ITEM in env.vault.practice_items
    _ready(env)
    env.clock.advance(1)
    _record, step = advance(env, serve=False)
    assert step["kind"] == "item" and step["practice_item_id"] == ITEM
    planned = next(item for item in _record.items() if item.practice_item_id == ITEM)
    assert planned.origin == "followup"


def test_a_wait_keeps_its_room_and_next_continues_the_block(tmp_path):
    env, _record = _env(tmp_path, fake_runtime())
    assert ITEM in env.vault.practice_items
    _ready(env, state=wf.WAITING)
    env.clock.advance(1)
    record, step = advance(env, serve=False)
    assert step["practice_item_id"] != ITEM
    assert ITEM in record.current_block().deferred_followups()
    assert ITEM not in {item.practice_item_id for item in record.items()}


def test_a_closed_factor_retires_a_waiting_probe_at_the_boundary(tmp_path):
    env, _record = _env(tmp_path, fake_runtime())
    row = _ready(env, state=wf.WAITING)
    assert not wf.waiting_still_valid(env.repository, row)
    wf.retire_waiting(env.repository, row, reason="hypotheses_changed", clock=env.clock)
    assert wf.get(env.repository, "fw_test")["state"] == wf.SKIPPED
    assert ITEM in identity.retired_probe_ids(env.repository)


def test_a_hard_refusal_needs_no_model_and_spends_nothing(tmp_path, monkeypatch):
    from tests.followup_serve_helpers import AuthorFake, author_clients, miss_with_rivals, rival_causes_vault, run_jobs
    from learnloop.diagnosis.causal_orchestrator import defer_probe_offer

    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    factor = repository.unresolved_cause_factors_for_attempt(wf.get(repository, outcome.workflow_id)["source_attempt_id"])[0]
    defer_probe_offer(repository, factor_id=factor["id"])
    fake = AuthorFake()
    run_jobs(vault, repository, clients=author_clients(fake))
    row = wf.get(repository, outcome.workflow_id)
    assert fake.calls == 0 and row["state"] == wf.REFUSED and row["chosen_ref"] == router.DECLINE
    assert row["feedback_released_at"] is not None


def test_no_plan_asks_now_with_no_draw(tmp_path):
    from tests.followup_serve_helpers import AuthorFake, author_clients, miss_with_rivals, rival_causes_vault, run_jobs

    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    run_jobs(vault, repository, clients=author_clients(AuthorFake()))
    row = wf.get(repository, outcome.workflow_id)
    assert row["state"] == wf.READY and row["chosen_ref"] == router.ASK_NOW and row["decision_id"] is None


def test_the_value_checks_are_on_the_record_and_decide_nothing(tmp_path):
    from tests.followup_serve_helpers import miss_with_rivals, rival_causes_vault

    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    factor = repository.unresolved_cause_factors_for_attempt(wf.get(repository, outcome.workflow_id)["source_attempt_id"])[0]
    seen = router.observational(repository, factor["id"])
    assert seen["repair_class_divergence"] is True and seen["decide_probe"]


def test_decide_runs_the_gate_against_the_standing_plan(tmp_path, monkeypatch):
    env, record = _env(tmp_path, fake_runtime())
    row = _workflow(env)
    monkeypatch.setattr(router, "_plan_context", lambda *_a, **_k: (env, record, _gate(env)))
    monkeypatch.setattr(router, "hard_refusal", lambda *_a, **_k: None)
    choice = SimpleNamespace(factor_id="f", hypothesis_ids=())
    decision = router.decide(env.vault, env.repository, row, choice=choice, clients=None, clock=env.clock)
    assert decision.decided_by in {"mixture", "not_ready"}
    assert decision.chosen_ref in {router.ASK_NOW, router.WAIT, router.NO_INTERVENTION}
    assert decision.block_id == record.current_block().id and decision.decision_id
    logged = router.record_decision(env.vault, env.repository, row, decision, clock=env.clock)
    assert rows(env, "plan_interrupt")[-1]["id"] == logged.decision_id


def test_the_decision_line_says_what_the_screen_should(tmp_path):
    from learnloop.followup_run.decision_view import decision_view

    env, record = _env(tmp_path, fake_runtime())
    row = _workflow(env)
    decision = router.record_decision(env.vault, env.repository, row, _decide(env, record, INSERT_NOW), clock=env.clock)
    view = decision_view(env.repository, decision.decision_id)
    assert view["line"].startswith("Router: ask now")
    assert "floor" in view["line"] and "%" in view["line"]
    assert view["decision_id"] == decision.decision_id
