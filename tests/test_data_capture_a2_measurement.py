"""Data capture A2: reading blocks, wait and stop decisions get real outcomes.

The objective is frozen before assignment (the same whichever arm is drawn), the lesson suggestion's
intention-to-treat adapter reads it, a "Check once" measures it (preferring to replace a maintenance slot), and
its due, offered, answered and unavailable states are recorded. Fakes only; no network.
"""

from __future__ import annotations

from datetime import timedelta
import json

import pytest

from learnloop.algorithm_versions import DATA_CAPTURE_ALGORITHM_VERSION, LESSON_SUGGESTIONS_ALGORITHM_VERSION
from learnloop.daily_plan import engine
from learnloop.daily_plan import measurement as M
from learnloop.daily_plan.engine import advance, build_plan, learner_pick
from learnloop.daily_plan.lanes import ReadingTarget
from learnloop.db.stores import data_capture as store
from learnloop.router import outcomes as RO

from tests.daily_plan_fakes import record_attempt, scheduled
from tests.router_mixture_helpers import mixture_env, rows, run
from tests.router_model_fakes import FakeDecider, fake_runtime, first_option, seed_with_first_uniform
from tests.test_router_g4_restraint import DECIDER_ONLY, PAST_THE_FLOOR, _followup_env

TAG = DATA_CAPTURE_ALGORITHM_VERSION
OLD = LESSON_SUGGESTIONS_ALGORITHM_VERSION
OFF = "[data_capture]\nserving = false\n"
READING = ReadingTarget(source_id="s", extraction_id="e", section_id="sec", section_title="A section", words_left=800)


def _objectives(env):
    with env.repository.connection() as connection:
        return store.objectives(connection)


def _events(env):
    with env.repository.connection() as connection:
        return store.measurement_events(connection)


def _outcomes(env, version=RO.OUTCOME_VERSION_V3):
    with env.repository.connection() as connection:
        return {row["decision_id"]: row for row in RO.derive_router_outcomes(connection, outcome_version=version)}


def _answer(env, item, lo, *, correctness=1.0, hints=0):
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type,"
            " hints_used, correctness, manual_review, created_at, session_id, primed, evidence_origin)"
            " VALUES (?,?,?,?,?,?,?,0,?,?,0,'human')",
            (f"att_{item}_{env.now_iso()}", item, lo, "short_answer", "independent_attempt", hints, correctness,
             env.now_iso(), "s_later"),
        )
        connection.commit()


def _picker(*wanted):
    def choice(refs):
        for ref in refs:
            if any(token in ref for token in wanted):
                return {other: (1.0 if other == ref else 0.0) for other in refs}
        return first_option(refs)

    return choice


def _reading_env(tmp_path, monkeypatch, *, choice, toml=DECIDER_ONLY, version=TAG, los=("lo_diag",)):
    monkeypatch.setattr(engine, "_fresh_reading", lambda _env, _intent: (READING, None))
    monkeypatch.setattr(engine, "deliverable_plan_active", lambda _vault: False)
    monkeypatch.setattr(M, "reading_learning_objects", lambda _vault, _repo, _target: list(los))
    runtime = fake_runtime(decider=FakeDecider(choice=choice), seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    return mixture_env(tmp_path, runtime, version=version, toml=toml)


def _reading_decision(env):
    build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    for _ in range(12):
        record, step = advance(env, serve=True)
        if step is None or step["kind"] == "reading":
            return record, step
        env.clock.advance(1)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
    return record, step


def _reading_rows(env):
    return [row for row in rows(env) if any("read" in str(entry.get("ref")) or entry.get("reading")
                                             for entry in row["candidates_json"] if entry.get("ref") == row["chosen_ref"])]


# -- the freeze ------------------------------------------------------------------------------


def test_the_objective_is_frozen_before_the_draw_the_same_for_every_arm(tmp_path, monkeypatch):
    drew_reading = _reading_env(tmp_path / "reading", monkeypatch, choice=_picker("reading", "new:"))
    drew_rule = _reading_env(tmp_path / "rule", monkeypatch, choice=first_option)
    build_plan(drew_reading, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    build_plan(drew_rule, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    first = {row["decision_id"]: row for row in _objectives(drew_reading).values()}
    second = {row["decision_id"]: row for row in _objectives(drew_rule).values()}
    assert first and second
    one, other = next(iter(first.values())), next(iter(second.values()))
    for key in ("learning_object_id", "source", "scope_json", "support_json", "objective_version"):
        assert one[key] == other[key], key
    assert one["learning_object_id"] == "lo_diag" and one["source"] == M.SOURCE_READING


def test_freeze_reads_the_reading_section_then_the_staged_pick_then_the_support():
    class Candidate:
        def __init__(self, candidate_id, los=(), reading=None):
            self.candidate_id, self.learning_object_ids, self.reading = candidate_id, tuple(los), reading

    staged = Candidate("practice", ["lo_a"])
    other = Candidate("other", ["lo_b"])
    stop = "stop_for_today"
    frozen = M.freeze(None, None, staged_ref="practice", candidates=[staged, other], support=["practice", "other"], stop_ref=stop)
    assert (frozen.learning_object_id, frozen.source, frozen.actionless) == ("lo_a", M.SOURCE_STAGED, False)
    assert not M.applies(frozen, M.ARM_PRACTICE), "a practice-only support needs no objective"
    with_stop = M.freeze(None, None, staged_ref="practice", candidates=[staged, other], support=["practice", stop], stop_ref=stop)
    assert with_stop.actionless and with_stop.real_choice and M.applies(with_stop, M.ARM_PRACTICE)
    assert with_stop.scope[0]["learning_object_ids"] == ["lo_a"]
    lone_stop = M.freeze(None, None, staged_ref=None, candidates=[], support=[stop], stop_ref=stop)
    assert (lone_stop.learning_object_id, lone_stop.real_choice) == (None, False)
    assert M.with_last_block(lone_stop, "lo_last").source == M.SOURCE_LAST_BLOCK


def test_the_routers_copy_of_the_actionless_arms_is_the_measurements():
    assert RO.ACTIONLESS_ARMS == M.ACTIONLESS_ARMS and RO.ARM_READING == M.ARM_READING


# -- real outcomes ------------------------------------------------------------------------------


def test_a_reading_arm_gets_a_real_outcome_instead_of_not_applicable(tmp_path, monkeypatch):
    """Reproduced first: under v2 a reading block has no item, so its outcome is ``not_applicable``."""

    env = _reading_env(tmp_path, monkeypatch, choice=_picker("reading", "new:"))
    _record, step = _reading_decision(env)
    assert step["kind"] == "reading"
    decision_id = next(row["decision_id"] for row in _objectives(env).values() if row["arm"] == M.ARM_READING)
    assert _outcomes(env, RO.OUTCOME_VERSION)[decision_id]["r_cold_status"] == "not_applicable"

    pending = _outcomes(env)[decision_id]
    assert pending["r_cold_status"] == "pending" and pending["target_learning_object_id"] == "lo_diag"
    detail = json.loads(pending["detail_json"])
    assert detail["arm"] == M.ARM_READING and detail["r_cold_rule"] == RO.R_COLD_ITT_RULE
    assert detail["objective"]["source"] == M.SOURCE_READING
    assert detail["measurement"]["state"] in {"scheduled", "unavailable"}

    env.clock.advance(60 * 24 * 3)
    _answer(env, "pi_diag_easy", "lo_diag")
    observed = _outcomes(env)[decision_id]
    assert observed["r_cold_status"] == "observed" and observed["s_status"] == "final"
    assert observed["r_next_status"] == "not_applicable"


def test_a_wait_arm_gets_a_real_outcome_and_a_measurement(tmp_path):
    runtime = fake_runtime(decider=FakeDecider(choice=first_option, p_yes=0.0),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = _followup_env(tmp_path, runtime, version=TAG, toml=DECIDER_ONLY)
    advance(env, serve=True)
    (row,) = rows(env, "plan_interrupt")
    assert row["chosen_ref"] == "continue_current"
    objective = _objectives(env)[row["id"]]
    assert objective["arm"] == M.ARM_WAIT and objective["learning_object_id"] == "lo_diag"
    assert objective["measurement"] == M.ARRANGED and objective["commitment_id"]
    assert objective["practice_item_id"] != "pi_diag_mid", "never the follow-up itself"
    assert _outcomes(env, RO.OUTCOME_VERSION)[row["id"]]["r_cold_status"] == "not_applicable"
    outcome = _outcomes(env)[row["id"]]
    assert outcome["r_cold_status"] == "pending" and json.loads(outcome["detail_json"])["arm"] == M.ARM_WAIT


def test_the_insert_arm_of_the_same_decision_has_the_same_objective_on_its_own_outcome(tmp_path):
    runtime = fake_runtime(decider=FakeDecider(choice=first_option, p_yes=1.0),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = _followup_env(tmp_path, runtime, version=TAG, toml=DECIDER_ONLY)
    advance(env, serve=True)
    (row,) = rows(env, "plan_interrupt")
    assert row["chosen_ref"] == "insert_now"
    objective = _objectives(env)[row["id"]]
    assert objective["arm"] == M.ARM_INSERT and objective["learning_object_id"] == "lo_diag"
    detail = json.loads(_outcomes(env)[row["id"]]["detail_json"])
    assert detail["objective_itt"]["arm"] == M.ARM_INSERT
    assert detail["objective_itt"]["objective"]["learning_object_id"] == "lo_diag"


def test_a_stop_drawn_with_work_feasible_is_measured_on_what_it_gave_up(tmp_path):
    choice = _picker("stop_for_today")
    runtime = fake_runtime(decider=FakeDecider(choice=choice), seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = mixture_env(tmp_path, runtime, version=TAG, toml=DECIDER_ONLY)
    build_plan(env, kind="normal", budget=4.0, remembered=4, minutes_source="chip")
    stops = [row for row in rows(env) if row["chosen_ref"] == "stop_for_today"]
    if not stops:
        pytest.skip("the boundary offered no stop at this budget")
    objective = _objectives(env)[stops[0]["id"]]
    assert objective["arm"] == M.ARM_STOP and objective["learning_object_id"]
    outcome = _outcomes(env)[stops[0]["id"]]
    assert outcome["action_status"] == "taken"
    assert json.loads(outcome["detail_json"])["arm"] == M.ARM_STOP


def test_a_stop_with_nothing_else_feasible_keeps_its_objective_and_spends_no_question(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(choice=first_option),
                                             seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR)),
                      version=TAG, toml=DECIDER_ONLY)
    run(env)
    stops = [row for row in rows(env) if row["chosen_ref"] == "stop_for_today"]
    assert stops
    objective = _objectives(env).get(stops[-1]["id"])
    assert objective is not None and objective["source"] == M.SOURCE_LAST_BLOCK
    assert objective["measurement"] == M.NATURAL and objective["commitment_id"] is None


def test_a_learner_pick_is_no_experiment(tmp_path):
    runtime = fake_runtime(decider=FakeDecider(choice=first_option), seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = mixture_env(tmp_path, runtime, version=TAG, toml=DECIDER_ONLY)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    advance(env, serve=True)
    learner_pick(env, "pi_p1b")
    picks = [row for row in rows(env) if row["learner_pick"]]
    assert picks and all(row["id"] not in _objectives(env) for row in picks)


# -- the measurement ------------------------------------------------------------------------------


def _arranged_wait(tmp_path, *, toml=DECIDER_ONLY):
    runtime = fake_runtime(decider=FakeDecider(choice=first_option, p_yes=0.0),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = _followup_env(tmp_path, runtime, version=TAG, toml=toml)
    advance(env, serve=True)
    (row,) = rows(env, "plan_interrupt")
    return env, row["id"], _objectives(env)[row["id"]]


def test_the_measurement_is_an_ordinary_check_once_with_the_teachers_rule_and_dates(tmp_path):
    env, decision_id, objective = _arranged_wait(tmp_path)
    with env.repository.connection() as connection:
        commitment = dict(connection.execute(
            "SELECT provenance_json, due_hint FROM commitment_versions WHERE commitment_id = ?",
            (objective["commitment_id"],)).fetchone())
    provenance = json.loads(commitment["provenance_json"])
    assert provenance["via"] == M.VIA and provenance["decision_id"] == decision_id
    assert provenance["dated_by"] in {"retrievability", "fallback"}
    assert provenance["pick"]["chosen"] == objective["practice_item_id"]
    assert commitment["due_hint"]


def test_one_check_per_lo_while_one_is_pending(tmp_path):
    env, decision_id, objective = _arranged_wait(tmp_path)
    other = M.freeze_followup("lo_diag", support=["insert_now", "continue_current"])
    with env.repository.atomic(), env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO router_decisions SELECT 'd2', 'k2', decision_kind, surface, mode, policy, algorithm_version, log_version,"
            " session_id, parent_decision_id, scheduler_slate_id, controller_decision_id, snapshot_hash, design, seed,"
            " candidates_json, exclusions_json, candidate_count, chosen_ref, chosen_practice_item_id, chosen_learning_object_id,"
            " chosen_scheduler_candidate_id, propensity, propensity_kind, learner_pick, fallback, mixture_weights_json,"
            " model_distributions_json, sensor_answers_json, question_set_version, model_ids_json, card_hash,"
            " similar_decision_ids_json, latency_ms, cost_usd, detail_json, created_at FROM router_decisions WHERE id = ?",
            (decision_id,))
        M.record(env.vault, env.repository, connection, decision_id="d2", decision_kind="plan_interrupt", frozen=other,
                 arm=M.ARM_WAIT, clock=env.clock)
    second = _objectives(env)["d2"]
    assert second["measurement"] == M.SHARED and second["commitment_id"] == objective["commitment_id"]
    with env.repository.connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM commitments WHERE created_action = 'test_me_later'").fetchone()[0] == 1


def test_no_question_to_ask_is_recorded_unavailable_and_visible_on_the_outcome(tmp_path):
    runtime = fake_runtime(decider=FakeDecider(choice=first_option, p_yes=0.0),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = _followup_env(tmp_path, runtime, version=TAG, toml=DECIDER_ONLY)
    from learnloop import delayed_checks as D

    original = D.candidates
    D.candidates = lambda *args, **kwargs: []  # no candidate of any kind
    try:
        advance(env, serve=True)
    finally:
        D.candidates = original
    (row,) = rows(env, "plan_interrupt")
    objective = _objectives(env)[row["id"]]
    assert objective["measurement"] == M.UNAVAILABLE and objective["commitment_id"] is None
    assert [event["reason"] for event in _events(env)[row["id"]]] == [M.NO_QUESTION]
    measurement = json.loads(_outcomes(env)[row["id"]]["detail_json"])["measurement"]
    assert measurement["state"] == "unavailable" and measurement["reasons"] == [M.NO_QUESTION]


def test_an_arrangement_that_fails_never_takes_the_decision_with_it(tmp_path, monkeypatch):
    def fail(*_args, **_kwargs):
        raise RuntimeError("no")

    monkeypatch.setattr(M, "_arrange", fail)
    runtime = fake_runtime(decider=FakeDecider(choice=first_option, p_yes=0.0),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = _followup_env(tmp_path, runtime, version=TAG, toml=DECIDER_ONLY)
    advance(env, serve=True)
    (row,) = rows(env, "plan_interrupt")
    assert _objectives(env)[row["id"]]["measurement"] == M.UNAVAILABLE
    assert [event["reason"] for event in _events(env)[row["id"]]] == [M.ARRANGE_FAILED]


def _due_measurement(tmp_path):
    env, decision_id, objective = _arranged_wait(tmp_path)
    env.clock.instant = env.clock.instant + timedelta(days=30)
    return env, decision_id, objective


def test_the_states_are_recorded_due_then_offered_then_answered(tmp_path):
    env, decision_id, objective = _due_measurement(tmp_path)
    item = objective["practice_item_id"]
    assert M.settle(env.vault, env.repository, clock=env.clock) >= 1
    assert {event["state"] for event in _events(env)[decision_id]} == {"due"}
    with env.repository.atomic(), env.repository.connection() as connection:
        connection.execute("INSERT INTO attention_blocks(id, action, budget_minutes, short_circuit_reason, content_hash, created_at)"
                           " VALUES ('b9', 'practice', 1, '', 'h', ?)", (env.now_iso(),))
        connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at)"
                           " VALUES ('p9', 'b9', ?, 'requested', ?)", (item, env.now_iso()))
    M.settle(env.vault, env.repository, clock=env.clock)
    assert {event["state"] for event in _events(env)[decision_id]} == {"due", "offered"}
    # Idempotent: nothing further to write.
    assert M.settle(env.vault, env.repository, clock=env.clock) == 0
    lo = objective["learning_object_id"]
    env.clock.advance(1)
    record_attempt(env.repository, item, lo, env.clock.now(), session_id="s9")
    env.clock.advance(1)
    M.settle(env.vault, env.repository, clock=env.clock)
    states = {event["state"]: event for event in _events(env)[decision_id]}
    assert set(states) == {"due", "offered", "answered"}
    assert states["answered"]["attempt_id"]
    measurement = json.loads(_outcomes(env)[decision_id]["detail_json"])["measurement"]
    assert measurement["state"] == "answered"


def test_a_due_check_the_plan_could_not_hold_is_unavailable_with_its_reason(tmp_path):
    env, decision_id, objective = _due_measurement(tmp_path)
    today = env.clock.now().astimezone().date().isoformat()
    split = {"checks_unplanned": [{"commitment_id": objective["commitment_id"], "reason": "plan_minutes_exhausted"}]}
    with env.repository.atomic(), env.repository.connection() as connection:
        connection.execute(
            "UPDATE daily_plans SET local_date = ?, split_json = ?", (today, json.dumps(split)))
    M.settle(env.vault, env.repository, clock=env.clock)
    events = _events(env)[decision_id]
    assert {"plan_minutes_exhausted"} == {event["reason"] for event in events if event["state"] == "unavailable"}


def test_settle_is_a_no_op_with_the_switch_off(tmp_path):
    env, decision_id, _objective = _due_measurement(tmp_path)
    env.vault.config.data_capture.serving = False
    assert M.settle(env.vault, env.repository, clock=env.clock) == 0
    assert decision_id not in _events(env)


def test_the_plan_charges_a_measurement_to_the_maintain_lane(tmp_path):
    """A measurement replaces an ordinary maintenance slot: the other lanes keep their minutes."""

    from tests.test_daily_plan_build import _wide_items as _wide

    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    from learnloop.curriculum import commitments as C

    C.create_commitment(env.repository, action="test_me_later", intent_text="x",
                        targets=[{"target_kind": "legacy_practice_item", "target_ref": "pi_diag_mid", "role": "required"}],
                        depth_preset="keep_in_touch", client_idempotency_key="k", due_hint="2020-01-01", reason="r",
                        provenance={"via": M.VIA, "decision_id": "d"})
    live = [scheduled("pi_diag_mid", "lo_diag", new_material=1.0), *_wide()]
    env.eligible = lambda _minutes: live
    prepared = engine._prepare_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    split = prepared.row["split_json"]
    slots = split.get("measurement_slots")
    assert slots and slots["checks"][0]["practice_item_id"] == "pi_diag_mid"
    assert slots["maintain_minutes_replaced"] > 0
    # Against the same plan with a learner's own check: new and repair keep their minutes; maintain gives it up.
    ordinary = mixture_env(tmp_path / "ordinary", fake_runtime(), version=TAG)
    C.create_commitment(ordinary.repository, action="test_me_later", intent_text="x",
                        targets=[{"target_kind": "legacy_practice_item", "target_ref": "pi_diag_mid", "role": "required"}],
                        depth_preset="keep_in_touch", client_idempotency_key="k", due_hint="2020-01-01", reason="r",
                        provenance={"via": "lesson"})
    ordinary.eligible = lambda _minutes: live
    other = engine._prepare_plan(ordinary, kind="normal", budget=40.0, remembered=40, minutes_source="chip").row["split_json"]
    assert "measurement_slots" not in other
    measured_lanes, ordinary_lanes = split["lanes"], other["lanes"]
    assert measured_lanes["maintain"]["load"] < ordinary_lanes["maintain"]["load"]
    assert measured_lanes["repair"]["minutes"] == ordinary_lanes["repair"]["minutes"]
    assert measured_lanes["new"]["minutes"] >= ordinary_lanes["new"]["minutes"]


def test_a_block_of_only_measurement_checks_is_no_learner_pick_and_says_so(tmp_path):
    from learnloop.curriculum import commitments as C
    from tests.daily_plan_fakes import MovableClock, make_env
    from tests.test_daily_plan_build import _seed_wide, _wide_vault

    paths = _wide_vault(tmp_path, version=TAG)
    env = make_env(paths.root, [scheduled("pi_diag_mid", "lo_diag", new_material=1.0)], clock=MovableClock(), session_id="s1")
    _seed_wide(env.repository)
    C.create_commitment(env.repository, action="test_me_later", intent_text="x",
                        targets=[{"target_kind": "legacy_practice_item", "target_ref": "pi_diag_mid", "role": "required"}],
                        depth_preset="keep_in_touch", client_idempotency_key="k", due_hint="2020-01-01", reason="r",
                        provenance={"via": M.VIA, "decision_id": "d"})
    record = build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    block = record.blocks[0]
    assert [item.practice_item_id for item in block.items] == ["pi_diag_mid"]
    assert block.chosen_by != "learner_pick"
    assert "you asked" not in block.chosen.get("why", "") and block.chosen.get("why") == "a short check on something you studied comes first"
    (row,) = rows(env)
    assert row["learner_pick"] == 0


def test_plan_slots_counts_only_measurements_and_never_more_than_the_load():
    class Check:
        def __init__(self, commitment_id, via):
            self.commitment_id, self.provenance = commitment_id, {"via": via, "decision_id": "d"}

    class Intent:
        def check_for(self, item_id):
            return {"m": Check("c1", M.VIA), "l": Check("c2", "lesson")}[item_id]

    class Item:
        def __init__(self, item_id, minutes):
            self.practice_item_id, self.est_minutes = item_id, minutes

    slots, replaced = M.plan_slots(Intent(), [Item("m", 3.0), Item("l", 2.0)], 2.0)
    assert [slot["commitment_id"] for slot in slots] == ["c1"] and replaced == 2.0
    assert M.plan_slots(Intent(), [Item("l", 2.0)], 9.0) == ([], 0.0)


# -- the switch ----------------------------------------------------------------------------------


@pytest.mark.parametrize("version, toml", [(OLD, DECIDER_ONLY), (TAG, DECIDER_ONLY + OFF)])
def test_below_the_tag_or_switched_off_nothing_is_frozen_or_arranged(tmp_path, version, toml):
    runtime = fake_runtime(decider=FakeDecider(choice=first_option, p_yes=0.0),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = _followup_env(tmp_path, runtime, version=version, toml=toml)
    advance(env, serve=True)
    assert _objectives(env) == {}
    with env.repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM commitments").fetchone()[0] == 0
    (row,) = rows(env, "plan_interrupt")
    assert "objective" not in json.dumps(row["detail_json"])


def test_a7s_interface_takes_any_decision_with_an_experiment_id(tmp_path):
    env, _decision_id, _objective = _arranged_wait(tmp_path)
    frozen = M.freeze_followup("lo_p1", support=["probe", "continue"])
    with env.repository.atomic(), env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO router_decisions SELECT 'a7', 'a7k', decision_kind, surface, mode, policy, algorithm_version, log_version,"
            " session_id, parent_decision_id, scheduler_slate_id, controller_decision_id, snapshot_hash, design, seed,"
            " candidates_json, exclusions_json, candidate_count, chosen_ref, chosen_practice_item_id, chosen_learning_object_id,"
            " chosen_scheduler_candidate_id, propensity, propensity_kind, learner_pick, fallback, mixture_weights_json,"
            " model_distributions_json, sensor_answers_json, question_set_version, model_ids_json, card_hash,"
            " similar_decision_ids_json, latency_ms, cost_usd, detail_json, created_at FROM router_decisions LIMIT 1")
        M.record(env.vault, env.repository, connection, decision_id="a7", decision_kind="plan_interrupt", frozen=frozen,
                 arm="stop", experiment_id="probe_vs_continue", clock=env.clock)
    row = _objectives(env)["a7"]
    assert row["experiment_id"] == "probe_vs_continue"
    detail = json.loads(_outcomes(env)["a7"]["detail_json"])
    assert detail["objective"]["experiment_id"] == "probe_vs_continue"


def test_a_decision_before_its_objective_could_be_frozen_stays_not_applicable(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(), version=OLD)
    run(env)
    env.vault.config.algorithms.algorithm_version = TAG
    stops = [row for row in rows(env) if row["chosen_ref"] == "stop_for_today"]
    assert stops
    outcome = _outcomes(env)[stops[-1]["id"]]
    assert outcome["r_cold_status"] == "not_applicable"
    assert json.loads(outcome["detail_json"])["no_outcome"] == "no_frozen_objective"

