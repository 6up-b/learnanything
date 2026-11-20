"""Who answers "should a probe be asked after this miss?" today, at every site, and what each one writes.

The sites, lettered as the G2 design's inventory (``docs/reviews/refactor-g2-design.md`` §1):

- A: which lane a miss takes (the rival count), ``followup_run.lanes``;
- B: the causal repair gate, ``causal_orchestrator.causal_repair_status``;
- C: the repair entry's hold, ``remediation.start_remediation_episode``;
- D: FG1's hard refusals, ``followup_run.router.hard_refusal``;
- E: FG1's class verdict, on the record and never deciding (``followup_run.router.observational``);
- F: the post-miss router, ``followup_run.router.decide`` and the objective gate it draws on;
- G: the general follow-up's value suppression, ``followups.evaluate_intervention_followup``;
- H: the scheduler's admission of a probe by value (``read_due_queue``);
- I: the serve-time admission of a new probe presentation, ``probe_presentations.probe_value_block_reason``;
- J: a diagnostic block's continuation, ``probe_blocks.block_complete``;
- K: an episode's completion by value, ``probe_completion``.

Each test pins the answer the code gives now and the rows it leaves, on the automatic follow-up lane (FG1's
workflow) or on the learner's repair lane (the feedback screen's status, offer and repair calls), for the cases the
design names: no plan, no room to wait, a lesson at the same boundary, a manual request, a retry, and a presentation
already committed. They are characterization tests: where an answer is one the probe router's successor means to
change, the successor's tag changes it and its test says so; below that tag these answers stay.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from learnloop.daily_plan import engine as E
from learnloop.daily_plan.router_chooser import CONTINUE_CURRENT, INSERT_NOW, NO_INTERVENTION
from learnloop.diagnosis import causal_orchestrator as causal
from learnloop.diagnosis import probe_offer
from learnloop.diagnosis import voi_stopping as voi
from learnloop.diagnosis.remediation import RemediationBlocked, start_remediation_episode
from learnloop.followup_run import jobs, lanes, router
from learnloop.followup_serve import workflow as wf
from learnloop.plan_refs import LESSON_OFFER_PREFIX

from tests.followup_journey_helpers import _generate, _journey
from tests.followup_serve_helpers import AuthorFake, author_clients, miss_with_rivals, rival_causes_vault, run_jobs
from tests.ih2_lessons_compete_helpers import _author_refuses, _miss_env, draw  # noqa: F401 - ``draw`` is a fixture
from tests.probe_router_authority_helpers import (
    CLOCK,
    PROBE_ITEM,
    TAG,
    call,
    count,
    decision_records,
    divergent_factor,
    receipts,
    router_rows,
    sidecar,
    table_rows,
)
from tests.voi_stopping_helpers import LO, _build, _followup_setup, _further, _long_probe_vault, _minutes, _probe_vault


def _actions(status) -> list[str]:
    return [action.as_dict()["id"] for action in status.actions]


def _status(case, **kwargs):
    return causal.causal_repair_status(case.vault, case.repository, misconception_id=case.first, clock=CLOCK,
                                       **{"start_repair": False, **kwargs})


def _fg1(tmp_path, *, config: str = ""):
    """A real miss whose diagnosis leaves two rival causes, its workflow pending and no plan (no session)."""

    vault, repository, paths = rival_causes_vault(tmp_path, config=config)
    _result, outcome = miss_with_rivals(vault, repository)
    row = wf.get(repository, outcome.workflow_id)
    factor = repository.unresolved_cause_factors_for_attempt(str(row["source_attempt_id"]))[0]
    return SimpleNamespace(vault=vault, repository=repository, paths=paths, row=row, factor=str(factor["id"]))


# -- A: which lane exists -------------------------------------------------------------------------------------------


class _Factors:
    """``select_lane``'s two reads: the attempt's open factors and whether each hypothesis still exists."""

    def __init__(self, factors, known):
        self._factors, self._known = factors, set(known)

    def unresolved_cause_factors_for_attempt(self, _attempt_id):
        return list(self._factors)

    def causal_hypothesis(self, hypothesis_id):
        return {"id": hypothesis_id} if hypothesis_id in self._known else None


def _factor(factor_id, *ids, open_set=True):
    causes = [{"hypothesis_id": value} for value in ids]
    return {"id": factor_id, "candidate_causes": [*causes, *([{"hypothesis_id": "H_OTHER", "open_set": True}]
                                                            if open_set else [])]}


def test_a_two_concrete_rivals_make_the_probe_lane_and_anything_less_is_practice():
    probe = lanes.select_lane(_Factors([_factor("f1", "h1", "h2")], {"h1", "h2"}), {"source_attempt_id": "a"})
    assert (probe.lane, probe.reason, probe.factor_id, probe.hypothesis_ids) == ("probe", "rival_causes", "f1",
                                                                                  ("h1", "h2"))
    # The open arm is never a rival, a hypothesis that no longer exists is not one, and a repeat counts once.
    one = lanes.select_lane(_Factors([_factor("f1", "h1", "h_gone", "h1")], {"h1"}), {"source_attempt_id": "a"})
    assert (one.lane, one.reason, one.factor_id) == ("practice", "one_hypothesis", "f1")
    none = lanes.select_lane(_Factors([], ()), {"source_attempt_id": "a"})
    assert (none.lane, none.reason, none.factor_id) == ("practice", "no_open_factor", None)
    empty = lanes.select_lane(_Factors([_factor("f1")], ()), {"source_attempt_id": "a"})
    assert (empty.lane, empty.reason) == ("practice", "no_concrete_cause")
    # The first factor with two rivals wins, over an earlier one with a single rival.
    later = lanes.select_lane(_Factors([_factor("f1", "h1"), _factor("f2", "h2", "h3")], {"h1", "h2", "h3"}),
                              {"source_attempt_id": "a"})
    assert (later.lane, later.factor_id) == ("probe", "f2")


def test_a_the_practice_lane_settles_the_workflow_and_hands_the_miss_to_the_general_followup(tmp_path, monkeypatch):
    from learnloop.diagnosis import followups

    case = _fg1(tmp_path)
    seen = []
    real = followups.evaluate_attempt_intervention_followup

    def spy(*args, **kwargs):
        seen.append(kwargs)
        return real(*args, **kwargs)

    monkeypatch.setattr(followups, "evaluate_attempt_intervention_followup", spy)
    assert lanes.settle_practice_lane(case.vault, case.repository, case.row, reason="one_hypothesis", clock=CLOCK)
    # Site G is the practice lane's decider: insertion only, the diagnosis hooks deferred.
    (kwargs,) = seen
    assert kwargs["insertion_only"] is True and kwargs["defer_diagnosis_hooks"] is True
    row = wf.get(case.repository, case.row["id"])
    assert (row["state"], row["lane"], row["release_reason"]) == (wf.SETTLED, wf.LANE_PRACTICE, wf.RELEASE_PRACTICE_LANE)
    assert row["chosen_ref"] is None and row["decision_id"] is None
    # A settled workflow is not settled twice.
    assert not lanes.settle_practice_lane(case.vault, case.repository, row, reason="one_hypothesis", clock=CLOCK)
    assert len(seen) == 1


# -- B and C: the causal gate and the repair entry, on the learner's repair lane -----------------------------------


def test_b_a_status_read_offers_the_quick_check_and_writes_a_new_receipt_every_time(tmp_path):
    case = divergent_factor(tmp_path)
    first = _status(case)
    assert first.status == "needs_disambiguation" and first.probe_offered
    assert first.probe_decision == "probe_now" and first.episode is None
    assert _actions(first) == ["take_quick_check", "teach_me_now", "not_now"]
    # A second read (a remounted panel) is a second verdict with a receipt of its own, not a reread of the first.
    second = _status(case)
    written = receipts(case.repository, case.factor)
    assert [row["decision"] for row in written] == ["probe_now", "probe_now"]
    assert [row["repair_status"] for row in written] == ["needs_disambiguation"] * 2
    assert [row["id"] for row in written] == [first.decision_receipt_id, second.decision_receipt_id]
    assert first.decision_receipt_id != second.decision_receipt_id
    # The learner lane has no router: no draw, no router row, no episode.
    assert count(case.repository, "router_decisions") == 0
    assert count(case.repository, "remediation_episodes") == 0


def test_b_not_now_withdraws_the_offer_and_the_divergence_stays(tmp_path):
    case = divergent_factor(tmp_path)
    probe_offer.defer_probe_offer(case.repository, factor_id=case.factor, clock=CLOCK)
    status = _status(case)
    assert (status.status, status.reason, status.probe_decision) == (
        "needs_disambiguation", "defer_learner_preference", "defer_learner_preference")
    assert not status.probe_offered and status.learner_preference == "decline"
    assert _actions(status) == ["teach_me_now"]
    (receipt,) = receipts(case.repository, case.factor)
    assert receipt["decision"] == "defer_learner_preference"


def test_c_a_manual_teach_me_now_starts_the_repair_without_the_probe(tmp_path):
    case = divergent_factor(tmp_path)
    status = probe_offer.request_teaching_now(case.vault, case.repository, misconception_id=case.first,
                                              factor_id=case.factor, clock=CLOCK)
    assert (status.status, status.reason, status.probe_decision) == (
        "started", "learner_requested_teaching_without_probe", "defer_learner_preference")
    assert status.episode is not None and status.learner_preference == "teach_now"
    assert [row["decision"] for row in receipts(case.repository, case.factor)] == ["defer_learner_preference"]
    # The repair entry then starts the episode the learner asked for, under a fresh verdict and receipt.
    episode = start_remediation_episode(case.repository, case.first, vault=case.vault, clock=CLOCK)
    assert episode["id"] == status.episode["id"]
    assert len(receipts(case.repository, case.factor)) == 2


def test_c_a_repair_request_is_held_by_the_gates_verdict_and_the_hold_is_a_result(tmp_path):
    case = divergent_factor(tmp_path)
    with pytest.raises(RemediationBlocked) as held:
        start_remediation_episode(case.repository, case.first, vault=case.vault, clock=CLOCK)
    assert held.value.repair_status.status == "needs_disambiguation" and held.value.repair_status.probe_offered
    # Over the sidecar the same request is an ordinary result carrying the status, with a receipt per request.
    ctx = sidecar(case.root)
    result = call(ctx, "start_remediation", {"misconceptionId": case.first})
    assert result["episode"] is None
    assert result["repairStatus"]["status"] == "needs_disambiguation" and result["repairStatus"]["probeOffered"]
    assert [row["decision"] for row in receipts(case.repository, case.factor)] == ["probe_now", "probe_now"]
    assert count(case.repository, "remediation_episodes") == 0


def test_b_with_no_instrument_the_verdict_on_a_zero_gain_blocks_the_repair(tmp_path):
    case = divergent_factor(tmp_path, instrument=False)
    status = _status(case)
    # The gain is the pinned 0.0 for a missing instrument, so the value arm (not "probe now") answers.
    assert (status.status, status.reason, status.probe_decision) == (
        "blocked_pending_review", "no_discriminating_instrument", "skip_no_discrimination")
    (receipt,) = receipts(case.repository, case.factor)
    inputs = json.loads(receipt["inputs_json"])
    assert inputs["instrument_available"] is False and inputs["expected_information_gain"] == 0.0
    assert inputs["evsi_provenance"]["expected_information_gain"] == "heuristic_default"
    assert inputs["likelihood_completeness"] == {"complete": False, "reason": "no_instrument"}


def test_b_one_repair_for_both_causes_starts_the_common_repair_with_no_probe(tmp_path):
    case = divergent_factor(tmp_path, instrument=False, first="repair:recall", second="repair:recall")
    status = _status(case, start_repair=True)
    assert (status.status, status.probe_decision) == ("safe_common_repair_available", "skip_common_repair")
    assert status.common_repair_class_id == "repair:recall"
    assert status.episode is not None and not status.probe_offered


def test_b_an_existing_pin_is_reused_and_acceptance_asks_no_gate(tmp_path):
    case = divergent_factor(tmp_path)
    status = _status(case)
    first = probe_offer.accept_probe_offer(case.vault, case.repository, factor_id=case.factor,
                                           decision_receipt_id=status.decision_receipt_id, clock=CLOCK)
    assert first.accepted and first.reason == "probe_pinned" and first.practice_item_id == PROBE_ITEM
    # A second acceptance (a re-tapped button) is the same pin; neither writes a receipt.
    again = probe_offer.accept_probe_offer(case.vault, case.repository, factor_id=case.factor,
                                           decision_receipt_id=status.decision_receipt_id, clock=CLOCK)
    assert again.accepted and again.reason == "probe_already_pinned"
    assert again.presentation_id == first.presentation_id
    assert len(receipts(case.repository, case.factor)) == 1
    # Acceptance reads neither the receipt's verdict nor the learner's "Not now": a stale request still pins.
    probe_offer.defer_probe_offer(case.repository, factor_id=case.factor, clock=CLOCK)
    stale = probe_offer.accept_probe_offer(case.vault, case.repository, factor_id=case.factor, clock=CLOCK)
    assert stale.accepted and stale.presentation_id == first.presentation_id


# -- D and E: FG1's hard refusals and its logged class verdict, on the automatic lane ------------------------------


def test_d_not_now_refuses_before_the_router_and_no_question_is_written(tmp_path):
    case = _fg1(tmp_path)
    probe_offer.defer_probe_offer(case.repository, factor_id=case.factor, clock=CLOCK)
    author = AuthorFake()
    run_jobs(case.vault, case.repository, clients=author_clients(author))
    row = wf.get(case.repository, case.row["id"])
    assert author.calls == 0
    assert (row["state"], row["chosen_ref"], row["release_reason"]) == (wf.REFUSED, router.DECLINE, wf.RELEASE_REFUSED)
    # With no plan, a refusal is still logged as a planless router row (unlike no plan's ask-now), with its outcome.
    (logged,) = router_rows(case.repository)
    assert row["decision_id"] == logged["id"]
    assert logged["detail_json"]["plan_id"] is None and logged["detail_json"]["block_id"] is None
    assert (logged["chosen_ref"], logged["propensity"], logged["policy"]) == (router.DECLINE, 1.0, "staged_v1")
    assert logged["detail_json"]["refused"] == [{"constraint_key": "learner_decline", "reason": "learner_decline"}]
    assert [(b["binding_kind"], b["outcome"]) for b in table_rows(case.repository, "router_decision_bindings")] == [
        ("outcome", "refused")]
    (gate,) = decision_records(case.repository, "followup_gate")
    assert (gate["status"], gate["decided_by"], gate["rule"]) == ("refused", "refused", "learner_decline")
    assert gate["facts"]["refusals"] == ["learner_decline"] and gate["facts"]["logged"] is True


def test_d_a_pending_machine_check_refuses_before_the_router(tmp_path):
    from learnloop.diagnosis.causal_reads import MACHINE_CHECK_REPAIR_MAPPING
    from learnloop.diagnosis.machine_checks import enqueue_backfill_obligation

    case = _fg1(tmp_path)
    enqueue_backfill_obligation(case.repository, {"kind": MACHINE_CHECK_REPAIR_MAPPING, "factor_id": case.factor,
                                                  "attempt_id": case.row["source_attempt_id"], "hypothesis_ids": []},
                                learning_object_id=str(case.row["learning_object_id"]), clock=CLOCK)
    assert router.hard_refusal(case.vault, case.repository, case.row, factor_id=case.factor) == "pending_machine_checks"
    run_jobs(case.vault, case.repository, clients=author_clients(AuthorFake()))
    row = wf.get(case.repository, case.row["id"])
    assert (row["state"], row["chosen_ref"]) == (wf.REFUSED, router.DECLINE)


def test_d_the_refusals_ask_preference_then_machine_checks_then_the_shared_episode_check(tmp_path, monkeypatch):
    from learnloop.diagnosis import probe_hard_stops

    case = _fg1(tmp_path)
    asked = []

    def conflict(repository, *, factor_id, learning_object_id):
        asked.append((factor_id, learning_object_id))
        return "another_probe_episode_is_open"

    monkeypatch.setattr(probe_hard_stops, "probe_episode_conflict", conflict)
    assert router.hard_refusal(case.vault, case.repository, case.row,
                               factor_id=case.factor) == "another_probe_episode_is_open"
    assert asked == [(case.factor, str(case.row["learning_object_id"]))]
    # An earlier refusal answers first, and the episode check is not asked.
    probe_offer.defer_probe_offer(case.repository, factor_id=case.factor, clock=CLOCK)
    assert router.hard_refusal(case.vault, case.repository, case.row, factor_id=case.factor) == "learner_decline"
    assert len(asked) == 1


def test_d_a_not_now_while_the_question_is_written_refuses_after_authoring(tmp_path):
    case = _fg1(tmp_path)

    class _SaysNotNow(AuthorFake):
        def run_followup_probe_authoring(self, context):
            probe_offer.defer_probe_offer(case.repository, factor_id=case.factor, clock=CLOCK)
            return super().run_followup_probe_authoring(context)

    author = _SaysNotNow()
    run_jobs(case.vault, case.repository, clients=author_clients(author))
    row = wf.get(case.repository, case.row["id"])
    # The decision (no plan: ask now) came first and was paid for; the refusal after it settles the workflow.
    assert author.calls == 1
    assert (row["state"], row["chosen_ref"], row["release_reason"]) == (wf.REFUSED, router.ASK_NOW, wf.RELEASE_REFUSED)
    assert row["practice_item_id"] is None and row["presentation_id"] is None


def test_d_a_retry_keeps_the_first_draw_and_asks_only_the_hard_refusals_again(tmp_path):
    case = _fg1(tmp_path)
    choice = SimpleNamespace(factor_id=case.factor, hypothesis_ids=())
    recorded = {**case.row, "chosen_ref": router.ASK_NOW, "decision_id": "decision_1"}
    kept = router.decide_once(case.vault, case.repository, recorded, choice=choice, clients=None, clock=CLOCK)
    assert (kept.chosen_ref, kept.decided_by, kept.decision_id) == (router.ASK_NOW, "recorded", "decision_1")
    assert decision_records(case.repository, "followup_gate") == []
    # A refusal that holds now is the retry's outcome; the row keeps the first draw, and only the gate record says so.
    probe_offer.defer_probe_offer(case.repository, factor_id=case.factor, clock=CLOCK)
    refused = router.decide_once(case.vault, case.repository, recorded, choice=choice, clients=None, clock=CLOCK)
    assert (refused.chosen_ref, refused.reason, refused.decided_by) == (router.DECLINE, "learner_decline", "recorded")
    (gate,) = decision_records(case.repository, "followup_gate")
    assert gate["status"] == "refused" and gate["facts"]["retry"] is True
    # An arm that asks nothing is returned as recorded, refusal or not.
    for arm in (router.NO_INTERVENTION, f"{LESSON_OFFER_PREFIX}lo_x"):
        settled = router.decide_once(case.vault, case.repository, {**recorded, "chosen_ref": arm}, choice=choice,
                                     clients=None, clock=CLOCK)
        assert (settled.chosen_ref, settled.decided_by) == (arm, "recorded")
    assert router_rows(case.repository) == []


def test_e_the_class_verdict_is_logged_where_the_classes_settle_it_and_absent_otherwise(tmp_path):
    case = _fg1(tmp_path)
    seen = router.observational(case.repository, case.factor)
    assert seen["decide_probe_absent"] == router.VERDICT_ABSENT_NO_INSTRUMENT and "decide_probe" not in seen
    common = divergent_factor(tmp_path / "common", instrument=False, first="repair:recall", second="repair:recall")
    settled = router.observational(common.repository, common.factor)
    assert settled["decide_probe"] == "skip_action_equivalent" and settled["repair_class_divergence"] is False
    # Unreadable classes log nothing and decide nothing.
    assert router.observational(case.repository, "no_such_factor") == {}


# -- F: the post-miss router, no plan ------------------------------------------------------------------------------


def test_f_with_no_plan_the_probe_is_asked_now_with_no_draw_and_no_router_row(tmp_path):
    case = _fg1(tmp_path)
    run_jobs(case.vault, case.repository, clients=author_clients(AuthorFake()))
    row = wf.get(case.repository, case.row["id"])
    assert (row["state"], row["lane"], row["chosen_ref"], row["decision_id"]) == (
        wf.READY, wf.LANE_PROBE, router.ASK_NOW, None)
    # Feedback stays held until the question is answered.
    assert row["feedback_released_at"] is None and row["exposed_at"] is None
    assert router_rows(case.repository) == [] and table_rows(case.repository, "router_decision_bindings") == []
    (gate,) = decision_records(case.repository, "followup_gate")
    assert (gate["status"], gate["chosen_ref"], gate["decided_by"], gate["rule"]) == (
        "chosen", router.ASK_NOW, "no_plan", "no_plan")
    assert gate["facts"]["logged"] is False and gate["facts"]["propensity"] == 1.0
    assert gate["facts"]["value_check_absent"] == router.VERDICT_ABSENT_NO_INSTRUMENT
    # No causal receipt: the automatic lane never asks site B.
    assert receipts(case.repository) == []


def test_f_with_no_plan_an_existing_presentation_is_served_with_no_new_value_admission(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import practice as practice_handlers

    ctx, _vault, repository, _result, outcome = _journey(tmp_path, monkeypatch)
    _generate(ctx, repository)
    row = wf.get(repository, outcome.workflow_id)
    assert call(ctx, "followup_next", {"attemptId": row["source_attempt_id"]})["action"] == "open"
    asked = []

    def refuses(*args, **kwargs):
        asked.append(args)
        return "value_below_minutes_cost", {"decision": voi.STOP}

    # Whatever the value rule would answer, the door never asks it for the router's committed presentation.
    monkeypatch.setattr(practice_handlers, "probe_value_block_reason", refuses)
    call(ctx, "open_queue_item", {"practiceItemId": row["practice_item_id"]})
    contract = call(ctx, "get_probe_contract", {"practiceItemId": row["practice_item_id"]})
    assert contract["active"] is True and contract["presentationId"] == row["presentation_id"]
    assert asked == [] and decision_records(repository, "probe_value") == []


# -- F: the post-miss router on a plan -----------------------------------------------------------------------------


def _lane(env, row, *, offer: bool = True):
    """The generation slot's decision on the standing plan, the real gates' (FG1's hard refusals and value checks find
    no factor here and refuse nothing), with the author refusing after it so the arm's own path is what remains."""

    clients = SimpleNamespace(author=AuthorFake(), authoring=None, runtime=env.policy.restraint.runtime)
    jobs._run_probe_lane(env.vault, env.repository, row, choice=SimpleNamespace(factor_id="f", hypothesis_ids=()),
                         clients=clients, clock=env.clock)
    return wf.get(env.repository, row["id"]), router_rows(env.repository)


def test_f_on_a_plan_the_router_draws_once_over_its_arms_and_a_lesson_at_the_same_boundary(tmp_path, draw, monkeypatch):
    env, row = _miss_env(tmp_path)
    _author_refuses(monkeypatch)
    draw.prefer = (CONTINUE_CURRENT,)
    after, logged = _lane(env, row)
    (decision,) = logged
    detail = decision["detail_json"]
    assert detail["mixture"]["support"][:3] == [INSERT_NOW, CONTINUE_CURRENT, NO_INTERVENTION]
    assert len(detail["mixture"]["support"]) == 4 and detail["mixture"]["support"][3].startswith(LESSON_OFFER_PREFIX)
    assert decision["chosen_ref"] == CONTINUE_CURRENT and 0.0 < decision["propensity"] < 1.0
    assert decision["policy"] == "router_objective_v1" and detail["workflow"]["id"] == "fw_miss"
    # Waiting releases what was held at once and marks the later question exposed.
    assert (after["chosen_ref"], after["decision_id"]) == (CONTINUE_CURRENT, decision["id"])
    assert after["release_reason"] == wf.RELEASE_WAIT and after["exposed_at"] is not None
    # What the decision leaves: its trace, its decision-state receipt, the frozen objective, the gate's record.
    assert count(env.repository, "router_objective_traces", "WHERE decision_id = ?", (decision["id"],)) == 1
    assert count(env.repository, "decision_state_receipts", "WHERE decision_id = ?", (decision["id"],)) == 1
    (objective,) = table_rows(env.repository, "decision_objectives", "WHERE decision_id = ?", (decision["id"],))
    assert objective["arm"] == "wait" and objective["decision_kind"] == "plan_interrupt"
    (gate,) = decision_records(env.repository, "followup_gate")
    assert gate["facts"]["logged"] is True and gate["rule"].startswith("drawn_")


def test_f_a_lesson_win_releases_the_hold_and_generates_nothing(tmp_path, draw, monkeypatch):
    env, row = _miss_env(tmp_path)
    draw.prefer = (LESSON_OFFER_PREFIX,)
    after, (decision,) = _lane(env, row)
    assert decision["chosen_ref"].startswith(LESSON_OFFER_PREFIX)
    assert (after["state"], after["chosen_ref"], after["release_reason"]) == (
        wf.WAITING, decision["chosen_ref"], wf.RELEASE_LESSON_OFFER)
    assert not after["practice_item_id"]
    assert [(b["binding_kind"], b["outcome"]) for b in table_rows(env.repository, "router_decision_bindings")] == [
        ("outcome", "lesson_offer")]


def test_f_no_intervention_settles_and_releases_with_nothing_generated(tmp_path, draw, monkeypatch):
    env, row = _miss_env(tmp_path)
    draw.prefer = (NO_INTERVENTION,)
    after, (decision,) = _lane(env, row)
    assert decision["chosen_ref"] == NO_INTERVENTION
    assert (after["state"], after["release_reason"]) == (wf.SETTLED, wf.RELEASE_NO_INTERVENTION)
    assert [(b["binding_kind"], b["outcome"]) for b in table_rows(env.repository, "router_decision_bindings")] == [
        ("outcome", "no_intervention")]


def _objective_gate(env):
    from learnloop.daily_plan.objective_chooser import ObjectiveFollowupGate

    restraint = env.policy.restraint
    return ObjectiveFollowupGate(env.vault, env.repository, restraint.runtime, frame=restraint.frame,
                                 card_builder=restraint.card_builder, session_id=env.session_id, clock=env.clock,
                                 may_defer=False)


def test_f_with_no_room_to_wait_the_probe_is_forced_unless_a_lesson_contests_it(tmp_path, draw):
    env, row = _miss_env(tmp_path)
    record = E.latest_today(env)
    gate = _objective_gate(env)
    alone = gate.decide_followup(record, None, row, wait_feasible=False)
    assert (alone.chosen_ref, alone.propensity, alone.wait_feasible) == (INSERT_NOW, 1.0, False)
    assert (alone.record["policy"], alone.record["decided_by"]) == ("staged_v1", "no_room_to_wait")
    assert alone.record["objective_followup"]["support"] == [INSERT_NOW] and "mixture" not in alone.record
    # With a lesson available, the same boundary is a real draw over the probe and the lesson, and no other arm.
    offer = E.interrupt_offer(env, record, None)
    draw.prefer = (INSERT_NOW,)
    contested = gate.decide_followup(record, None, row, wait_feasible=False, offer=offer)
    assert contested.record["mixture"]["support"] == [INSERT_NOW, offer.candidate.candidate_id]
    assert offer.candidate.candidate_id.startswith(LESSON_OFFER_PREFIX)
    assert contested.chosen_ref == INSERT_NOW and 0.0 < contested.propensity < 1.0


def test_f_the_mid_block_restraint_forces_now_with_no_room_and_draws_two_arms_otherwise(tmp_path, monkeypatch):
    from learnloop.daily_plan.objective_chooser import ObjectiveRestraintGate

    env, _row = _miss_env(tmp_path, questions_left=True)
    record = E.latest_today(env)
    current = record.current_block()
    item = next(entry for entry in current.items if not entry.resolved)
    restraint = env.policy.restraint
    gate = ObjectiveRestraintGate(env.vault, env.repository, restraint.runtime, frame=restraint.frame,
                                  card_builder=restraint.card_builder, session_id=env.session_id, clock=env.clock,
                                  may_defer=False)
    forced = gate.decide(record, current, item, wait_feasible=False)
    assert (forced.chosen_ref, forced.propensity, forced.record["decided_by"]) == (INSERT_NOW, 1.0, "no_room_to_wait")
    drawn = gate.decide(record, current, item, wait_feasible=True)
    assert drawn.record["mixture"]["support"] == [INSERT_NOW, CONTINUE_CURRENT]
    assert drawn.chosen_ref in {INSERT_NOW, CONTINUE_CURRENT} and drawn.propensity < 1.0


def test_f_a_retry_on_a_plan_reuses_the_logged_draw(tmp_path, draw, monkeypatch):
    env, row = _miss_env(tmp_path)
    _author_refuses(monkeypatch)
    draw.prefer = (INSERT_NOW,)
    after, (decision,) = _lane(env, row)
    assert after["chosen_ref"] == INSERT_NOW and after["decision_id"] == decision["id"]
    # The lease recovery's retry: the workflow names its decision, and no second draw or row is made.
    again = router.decide_once(env.vault, env.repository, {**after, "state": wf.PENDING},
                               choice=SimpleNamespace(factor_id="f", hypothesis_ids=()),
                               clients=SimpleNamespace(runtime=env.policy.restraint.runtime), clock=env.clock)
    assert (again.chosen_ref, again.decision_id, again.decided_by) == (INSERT_NOW, decision["id"], "recorded")
    assert len(router_rows(env.repository)) == 1


# -- G: the general follow-up's value suppression ------------------------------------------------------------------


def test_g_value_suppresses_a_followup_and_the_learners_request_overrides_it(tmp_path, monkeypatch):
    loaded, repository, result = _followup_setup(tmp_path, TAG)
    _minutes(monkeypatch, 10_000.0)
    suppressed = _further(loaded, repository, result)
    assert suppressed.triggered is False
    assert suppressed.reason == f"intervention_followup:{voi.VOI_VALUE_SUPPRESSION}:{LO}"
    assert suppressed.gate_diagnostics["voi_stopping"]["decision"] == voi.STOP
    assert [(row["decision_outcome"], row["verdict"]) for row in table_rows(repository, "followup_value_decisions")] == [
        (f"suppressed_{voi.VOI_VALUE_SUPPRESSION}", "stop")]
    forced = _further(loaded, repository, result, manual_override=True)
    assert forced.triggered is True
    assert voi.VOI_VALUE_SUPPRESSION in forced.gate_diagnostics["would_suppress"]
    assert forced.gate_diagnostics["voi_stopping"]["served_by"] == {"mechanism": "manual_override"}
    # Where value pays, it queues the follow-up.
    _minutes(monkeypatch, 0.01)
    queued = _further(loaded, repository, result)
    assert queued.triggered is True and queued.gate_diagnostics["voi_stopping"]["decision"] == voi.CONTINUE


# -- H, I: the scheduler's and the serving door's value admission of a new probe -----------------------------------


def test_h_the_scheduler_withholds_a_probe_whose_value_does_not_pay(tmp_path, monkeypatch):
    from learnloop.scheduling.scheduler import OfferTrace

    _paths, vault, repository = _probe_vault(tmp_path, TAG)
    _minutes(monkeypatch, 10_000.0)
    trace = OfferTrace()
    queue = _build(vault, repository, trace=trace)
    assert all(item.components.get("probe_eig", 0.0) == 0.0 and item.components.get("voi_stop") == 1.0
               for item in queue)
    (stopped,) = [d for d in trace.voi_decisions if d["site"] == voi.SITE_PROBE_EPISODE]
    assert stopped["decision"] == voi.STOP
    _minutes(monkeypatch, 0.01)
    trace = OfferTrace()
    queue = _build(vault, repository, trace=trace)
    assert any(item.components.get("probe_eig", 0.0) > 0.0 for item in queue)
    (kept,) = [d for d in trace.voi_decisions if d["site"] == voi.SITE_PROBE_EPISODE]
    assert kept["decision"] == voi.CONTINUE


def test_i_the_serving_door_refuses_a_new_presentation_by_value_and_records_why(tmp_path, monkeypatch):
    from learnloop.diagnosis.probe_presentations import probe_value_block_reason

    paths, vault, repository = _probe_vault(tmp_path, TAG)
    _minutes(monkeypatch, 10_000.0)
    episode = repository.open_probe_episode(LO)
    reason, body = probe_value_block_reason(vault, repository, episode, "pi_svd_define_001", session_id="sess")
    assert reason == "value_below_minutes_cost" and body["decision"] == voi.STOP
    # The sidecar's door: no presentation, and a ``probe_value`` record of the refusal.
    monkeypatch.setattr("learnloop_sidecar.handlers.practice.ready_grading_provider",
                        lambda *_a, **_k: ("fake", SimpleNamespace(ready=True), object()))
    ctx = sidecar(paths.root)
    contract = call(ctx, "get_probe_contract", {"practiceItemId": "pi_svd_define_001", "sessionId": "sess"})
    assert contract == {**contract, "active": False, "reason": "value_below_minutes_cost"}
    (record,) = decision_records(repository, "probe_value")
    assert record["rule"] == "value_below_minutes_cost"
    assert repository.active_probe_presentation(episode.id, practice_item_id="pi_svd_define_001") is None


# -- J, K: continuing a block, completing an episode ---------------------------------------------------------------


def test_j_a_generated_followups_block_ends_at_its_one_question_and_value_ends_any_other(tmp_path, monkeypatch):
    from learnloop.diagnosis.probe_blocks import block_complete
    from learnloop.diagnosis import probe_episodes as probes
    from learnloop.vault.loader import load_vault
    from tests.helpers import append_config_toml
    from tests.probe_block_end_helpers import _commit, _setup as block_setup, _submit
    from tests.probe_episodes_helpers import ITEM_ID

    ctx, _vault, repository, _result, outcome = _journey(tmp_path / "fg1", monkeypatch)
    _generate(ctx, repository)
    row = wf.get(repository, outcome.workflow_id)
    vault, _ = ctx.require_vault()
    episode = repository.probe_episode(str(row["probe_episode_id"]))
    # FG1's one question closes its block whatever value would say, before any observation.
    _minutes(monkeypatch, 0.01)
    assert block_complete(vault, repository, episode, str(row["presentation_id"])) is True
    # A block of three ordinary probes: its first answer closes it only when the next observation does not pay.
    for minutes, closes in ((0.01, False), (10_000.0, True)):
        root = tmp_path / f"block_{closes}"
        root.mkdir()
        block_vault, block_repository = block_setup(root)
        append_config_toml(block_vault.root, "[probe.block]\ndefault_block_observations = 3")
        block_vault = load_vault(block_vault.root)
        block_episode = probes.enter_episode(block_vault, block_repository, LO, clock=CLOCK)
        presentation = _commit(block_vault, block_repository, block_episode, item_id=ITEM_ID)
        _minutes(monkeypatch, minutes)
        result = _submit(block_vault, block_repository, item_id=ITEM_ID, presentation_id=presentation.id, score=1)
        assert (result.probe_block_end is not None) is closes
        assert block_complete(block_vault, block_repository, block_repository.probe_episode(block_episode.id),
                              presentation.id) is closes


def test_k_value_completes_an_episode_and_off_the_rule_the_count_does(tmp_path, monkeypatch):
    from tests.voi_stopping_helpers import _answer_probe

    vault, repository = _long_probe_vault(tmp_path / "value", TAG)
    _minutes(monkeypatch, 10_000.0)
    episode = _answer_probe(vault, repository)
    assert episode.completion_reason == "value_of_information_stop"
    vault, repository = _long_probe_vault(tmp_path / "count", TAG, "[voi_stopping]\nenabled = false\n")
    _minutes(monkeypatch, 0.0001)
    for _ in range(4):
        episode = _answer_probe(vault, repository)
    assert episode.completion_reason == "observation_budget_exhausted"
