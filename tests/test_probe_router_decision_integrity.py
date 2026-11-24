"""The probe router's decisions hold together (``docs/reviews/algorithm-probe-router.md``): each test failed on main
before its fix.

Authority comes from the decision itself. A probe pinned by a router decision made below the probe router's
tag keeps its predecessor treatment after the vault is upgraded, mid-episode and in replay; only a decision the row
says was made at the tag, and that asked the probe, owns its presentation.
A pin that no longer stands (ended unanswered) owns nothing.
"""

from __future__ import annotations

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.diagnosis import probe_completion
from learnloop.diagnosis.probe_episodes import router_selected_episode
from learnloop.diagnosis.probe_offer import accept_probe_offer
from learnloop.router.plan_log import PROBE_REF, log_learner_probe_decision
from learnloop.vault.loader import load_vault

from tests.helpers import _set_algorithm_version_at
from tests.ih2_lessons_compete_helpers import draw  # noqa: F401 - a fixture
from tests.probe_router_authority_helpers import CLOCK, TAG, divergent_factor

HEAD = LATEST_ALGORITHM_VERSION


def _pinned(tmp_path, *, decided_at: str):
    """A probe pinned on the learner lane by a router decision row stamped ``decided_at`` (the vault at that tag when
    it was drawn, as the automatic lane's decisions below the tag are), then the vault upgraded to the head."""

    case = divergent_factor(tmp_path, version=decided_at)
    with case.repository.atomic(), case.repository.connection() as connection:
        decision_id = log_learner_probe_decision(connection, {
            "factor_id": case.factor, "chosen_ref": PROBE_REF, "propensity": 0.2,
            "served_pi": {PROBE_REF: 0.2, "no_probe": 0.8}, "detail": {}, "config": case.vault.config})
    offer = accept_probe_offer(case.vault, case.repository, factor_id=case.factor, router_decision_id=decision_id,
                               clock=CLOCK)
    assert offer.accepted
    _set_algorithm_version_at(case.root, HEAD)
    case.vault = load_vault(case.root)
    presentation = case.repository.probe_presentation(offer.presentation_id)
    episode = case.repository.probe_episode(offer.episode_id)
    rows = [{"selection_components": presentation.selection_components}]
    return case, presentation, episode, rows


def test_r1_a_pin_drawn_below_the_tag_keeps_its_predecessor_gates_after_the_upgrade(tmp_path):
    case, _presentation, episode, rows = _pinned(tmp_path, decided_at=TAG)
    assert not router_selected_episode(case.vault, case.repository, episode)
    # Value still decides the episode, as it did when the probe was asked.
    assert probe_completion.value_decides_episode(case.vault, case.repository, rows)


def test_r1_a_pin_drawn_at_the_tag_is_the_routers(tmp_path):
    case, _presentation, episode, rows = _pinned(tmp_path, decided_at=HEAD)
    assert router_selected_episode(case.vault, case.repository, episode)
    assert not probe_completion.value_decides_episode(case.vault, case.repository, rows)


def test_r7_a_pin_ended_unanswered_owns_nothing(tmp_path):
    case, presentation, episode, _rows = _pinned(tmp_path, decided_at=HEAD)
    case.repository.end_probe_presentation(presentation.id, end_reason="invalidated", clock=CLOCK)
    assert not router_selected_episode(case.vault, case.repository, episode)


# -- one decision, one served arm, everywhere it is logged ------------------------------------------------------


def _lane(tmp_path, monkeypatch, draw, u: float):
    import json
    from types import SimpleNamespace

    from learnloop.followup_run import jobs
    from learnloop.plan_refs import LESSON_OFFER_PREFIX
    from learnloop.router_objective import probe_coin as PC

    from tests.followup_serve_helpers import AuthorFake
    from tests.ih2_lessons_compete_helpers import _author_refuses, _miss_env

    env, row = _miss_env(tmp_path, version=HEAD, toml='[router_objective]\nstop_coin = 0.2\ncheck_rate = "off"\n')
    _author_refuses(monkeypatch)
    monkeypatch.setattr(PC, "draw_uniform", lambda _seed: u)
    draw.prefer = (LESSON_OFFER_PREFIX,)
    clients = SimpleNamespace(author=AuthorFake(), authoring=None, runtime=env.policy.restraint.runtime)
    jobs._run_probe_lane(env.vault, env.repository, row, choice=SimpleNamespace(factor_id="f", hypothesis_ids=()),
                         clients=clients, clock=env.clock)
    with env.repository.connection() as connection:
        (decision,) = [dict(r) for r in connection.execute(
            "SELECT id, chosen_ref, propensity FROM router_decisions WHERE decision_kind = 'plan_interrupt'")]
        (trace,) = [dict(r) for r in connection.execute(
            "SELECT decision_id, chosen_ref, propensity, trace_json FROM router_objective_traces "
            "WHERE decision_kind = 'plan_interrupt'")]
    trace["trace"] = json.loads(trace.pop("trace_json"))
    return decision, trace


def test_r2_the_trace_names_the_probe_the_coin_asked_at_its_served_probability(tmp_path, monkeypatch, draw):
    import pytest

    from learnloop.daily_plan.router_chooser import INSERT_NOW

    decision, trace = _lane(tmp_path, monkeypatch, draw, 0.05)
    assert decision["chosen_ref"] == trace["chosen_ref"] == INSERT_NOW
    assert decision["propensity"] == pytest.approx(0.2) and trace["propensity"] == pytest.approx(0.2)
    assert trace["trace"]["mixing"]["drawn_chosen"].startswith("lesson_offer:")


def test_r2_on_the_policy_arm_the_trace_logs_the_served_probability_not_mu(tmp_path, monkeypatch, draw):
    import pytest

    decision, trace = _lane(tmp_path, monkeypatch, draw, 0.9)
    mu = trace["trace"]["mixing"]["mu"][decision["chosen_ref"]]
    assert decision["chosen_ref"] == trace["chosen_ref"] and decision["chosen_ref"].startswith("lesson_offer:")
    assert trace["propensity"] == pytest.approx(decision["propensity"]) == pytest.approx(0.8 * mu, abs=1e-6)


# -- the selection is its own candidate's, read again at acceptance ------------------------------


def _learner(tmp_path, monkeypatch, *, u: float = 0.05):
    from learnloop.router_objective import probe_coin as PC

    from tests.helpers import append_config_toml
    from tests.probe_router_authority_helpers import sidecar

    case = divergent_factor(tmp_path, version=HEAD)
    append_config_toml(case.root, "\n[router_objective]\nstop_coin = 0.2\n")
    case.vault = load_vault(case.root)
    monkeypatch.setattr(PC, "draw_uniform", lambda _seed: u)
    case.ctx = sidecar(case.root)
    return case


def _answered_elsewhere(monkeypatch) -> None:
    """The probe's item already answered in another administration (the never-seen rule's exclusion)."""

    from learnloop.diagnosis import probe_episodes

    from tests.probe_router_authority_helpers import PROBE_ITEM

    monkeypatch.setattr(probe_episodes, "administered_surface_exclusions", lambda *_a, **_k: ({PROBE_ITEM}, set()))


def _read(case) -> dict:
    from tests.probe_router_authority_helpers import call

    return call(case.ctx, "causal_repair_status", {"misconceptionId": case.first})["repairStatus"]


def _offer(case) -> dict:
    from tests.probe_router_authority_helpers import call

    return call(case.ctx, "causal_probe_offer_action", {"factorId": case.factor})["offer"]


def test_r3_a_selection_whose_candidate_was_rejected_is_refused_and_never_substituted(tmp_path, monkeypatch):
    from learnloop.diagnosis.causal_probe_coherence import transition_probe_candidate

    case = _learner(tmp_path, monkeypatch)
    selected = _read(case)
    assert selected["routerState"] == "selected"
    transition_probe_candidate(case.repository, selected["candidateId"], to_status="rejected", reviewer="owner",
                               clock=CLOCK)
    # No reviewed instrument is left: the facts say so before the decision is read, and the click is refused.
    gone = _read(case)
    assert (gone["routerState"], gone["hardStopReasons"]) == ("unavailable", ["no_executable_instrument"])
    refused = _offer(case)
    assert (refused["accepted"], refused["reason"]) == (False, "no_executable_instrument")


def test_r3_a_selection_that_can_no_longer_be_administered_is_void_and_the_repair_goes_on(tmp_path, monkeypatch):
    case = _learner(tmp_path, monkeypatch)
    assert _read(case)["routerState"] == "selected"
    _answered_elsewhere(monkeypatch)
    void = _read(case)
    assert (void["routerState"], void["status"], void["probeOffered"]) == ("void", "started", False)
    assert void["hardStopReasons"] == ["probe_item_already_answered"]
    refused = _offer(case)
    assert (refused["accepted"], refused["reason"]) == (False, "probe_item_already_answered")


def test_r6_a_machine_check_queued_after_the_selection_refuses_the_stale_click(tmp_path, monkeypatch):
    from learnloop.diagnosis import causal_orchestrator

    case = _learner(tmp_path, monkeypatch)
    assert _read(case)["routerState"] == "selected"
    monkeypatch.setattr(causal_orchestrator, "pending_machine_checks_for_factor",
                        lambda *_a, **_k: [{"id": "check_after_selection"}])
    refused = _offer(case)
    assert (refused["accepted"], refused["reason"]) == (False, "machine_checks_pending")


def test_r13_a_probe_already_answered_is_no_option_and_nothing_is_drawn(tmp_path, monkeypatch):
    case = _learner(tmp_path, monkeypatch)
    _answered_elsewhere(monkeypatch)
    status = _read(case)
    assert (status["status"], status["routerState"], status["reason"]) == ("started", "unavailable",
                                                                           "probe_item_already_answered")
    with case.repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM router_decisions").fetchone()[0] == 0


# -- no arm is served without its committed decision and assignment --------------------------------------------


def _automatic(tmp_path, monkeypatch, draw, *, u: float, toml: str = "", prefer=None):
    from types import SimpleNamespace

    from learnloop.followup_run import jobs
    from learnloop.followup_serve import workflow as wf
    from learnloop.router_objective import probe_coin as PC

    from tests.followup_serve_helpers import AuthorFake
    from tests.ih2_lessons_compete_helpers import _author_refuses, _miss_env

    env, row = _miss_env(tmp_path, version=HEAD,
                         toml='[router_objective]\nstop_coin = 0.2\ncheck_rate = "off"\n' + toml)
    _author_refuses(monkeypatch)
    monkeypatch.setattr(PC, "draw_uniform", lambda _seed: u)
    if prefer:
        draw.prefer = prefer
    clients = SimpleNamespace(author=AuthorFake(), authoring=None, runtime=env.policy.restraint.runtime)
    jobs._run_probe_lane(env.vault, env.repository, row, choice=SimpleNamespace(factor_id="f", hypothesis_ids=()),
                         clients=clients, clock=env.clock)
    with env.repository.connection() as connection:
        decisions = connection.execute("SELECT COUNT(*) FROM router_decisions WHERE decision_kind = 'plan_interrupt'"
                                       ).fetchone()[0]
    return wf.get(env.repository, row["id"]), decisions


def test_r4_with_logging_off_the_coins_probe_is_not_asked(tmp_path, monkeypatch, draw):
    from learnloop.daily_plan.router_chooser import NO_INTERVENTION

    after, decisions = _automatic(tmp_path, monkeypatch, draw, u=0.0, toml="\n[router]\nlog_decisions = false\n")
    assert decisions == 0 and after["chosen_ref"] == NO_INTERVENTION and not after["practice_item_id"]


def test_r4_a_refused_assignment_rolls_the_decision_back_and_no_probe_is_asked(tmp_path, monkeypatch, draw):
    from learnloop.daily_plan.router_chooser import NO_INTERVENTION
    from learnloop.router_objective import assignments

    monkeypatch.setattr(assignments, "insert", lambda *_a, **_k: None)
    after, decisions = _automatic(tmp_path, monkeypatch, draw, u=0.0)
    assert decisions == 0 and after["chosen_ref"] == NO_INTERVENTION


def test_r4_a_failed_write_never_turns_a_drawn_lesson_into_the_probe(tmp_path, monkeypatch, draw):
    from learnloop.daily_plan.router_chooser import NO_INTERVENTION
    from learnloop.plan_refs import LESSON_OFFER_PREFIX
    from learnloop.router import plan_log

    def broken(*_a, **_k):
        raise RuntimeError("the ledger refused the row")

    monkeypatch.setattr(plan_log, "log_followup_decision", broken)
    after, _decisions = _automatic(tmp_path, monkeypatch, draw, u=0.9, prefer=(LESSON_OFFER_PREFIX,))
    assert after["chosen_ref"] == NO_INTERVENTION


def test_r4_the_learner_lanes_decision_and_assignment_commit_together(tmp_path, monkeypatch):
    from learnloop.router_objective import assignments

    case = _learner(tmp_path, monkeypatch)
    monkeypatch.setattr(assignments, "insert", lambda *_a, **_k: None)
    status = _read(case)
    assert status["routerState"] == "pending" and status["probeOffered"] is False
    with case.repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM router_decisions").fetchone()[0] == 0


def test_r5_with_the_objective_off_the_old_gate_never_draws_the_unwritten_probe(tmp_path, monkeypatch, draw):
    from learnloop.daily_plan.router_chooser import INSERT_NOW, NO_INTERVENTION

    after, decisions = _automatic(tmp_path, monkeypatch, draw, u=0.9, toml="enabled = false\n", prefer=(INSERT_NOW,))
    assert after["chosen_ref"] == NO_INTERVENTION and decisions == 1


# -- the learner lane's record --------------------------------------------------


def _decision(case) -> dict:
    import json

    with case.repository.connection() as connection:
        row = dict(connection.execute(
            "SELECT * FROM router_decisions WHERE surface = 'causal_repair'").fetchone())
    row["detail"] = json.loads(row["detail_json"])
    return row


def test_r15_the_valuation_runs_under_the_choosers_options_and_freezes_what_it_valued(tmp_path, monkeypatch):
    from learnloop.daily_plan import objective_chooser as OC

    case = _learner(tmp_path, monkeypatch)
    _read(case)
    frozen = _decision(case)["detail"]["valuation"]["frozen"]
    assert frozen["rollout_options"] == OC.rollout_options(case.vault.config)
    assert frozen["inputs"]["topics"] and frozen["seed"] and frozen["draws"] >= 1
    assert frozen["payload"]["channel"]["status"] == "complete"


def test_r16_each_repair_is_priced_at_its_own_minutes(tmp_path, monkeypatch):
    from learnloop.diagnosis import causal_diagnostic_selector as CDS

    monkeypatch.setattr(CDS, "duration_estimates_for_repair_classes", lambda _repository, classes: {
        cls: {"minutes": 2.0 if cls == "repair:recall" else 20.0, "source": "authored_prior"} for cls in classes})
    case = _learner(tmp_path, monkeypatch)
    _read(case)
    repairs = {r["ref"]: r for r in _decision(case)["detail"]["valuation"]["frozen"]["payload"]["repairs"]}
    assert repairs["repair:recall"]["minutes"] == 2.0 and repairs["repair:method"]["minutes"] == 20.0
    assert "authored_prior" in repairs["repair:recall"]["source"]


def test_r17_a_selected_row_binds_no_item_before_an_acceptance(tmp_path, monkeypatch):
    case = _learner(tmp_path, monkeypatch)
    _read(case)
    assert _decision(case)["chosen_practice_item_id"] is None


def test_r18_a_retry_draws_the_same_coin_and_a_receipt_never_stands_for_another_status(tmp_path, monkeypatch):
    from learnloop.router_objective import probe_coin as PC

    case = _learner(tmp_path, monkeypatch)
    seeds = []
    real = PC.seed_for
    monkeypatch.setattr(PC, "seed_for", lambda key, unit: seeds.append(real(key, unit)) or seeds[-1])
    status = _read(case)
    assert len(set(seeds)) == 1 and seeds[0] == real(f"learner_probe:{case.factor}", "learner_probe")
    from tests.probe_router_authority_helpers import receipts

    (receipt,) = [r for r in receipts(case.repository, case.factor) if r["id"] == status["decisionReceiptId"]]
    assert receipt["repair_status"] == status["status"]


def test_r20_a_tiny_share_is_still_an_exact_propensity():
    from learnloop.router.plan_log import NO_PROBE_REF, build_learner_probe_decision

    row = build_learner_probe_decision({"factor_id": "f", "chosen_ref": NO_PROBE_REF, "propensity": 1 - 5e-13,
                                        "served_pi": {PROBE_REF: 5e-13, NO_PROBE_REF: 1 - 5e-13}, "detail": {}})
    assert row["propensity_kind"] == "exact" and row["propensity"] < 1.0


# -- one decision per factor, across lanes, for the factor the screen shows -----------------------------------------


def _automatic_decision_on(case, chosen_ref: str) -> str:
    """The automatic lane (FG1) decided this factor's probe after its miss: a probe-lane workflow on the factor that
    names its committed decision."""

    from learnloop.db.stores import followup_serve as store
    from learnloop.router.plan_log import log_followup_decision

    from tests.causal_orchestrator_helpers import LO_ID, NOW_ISO

    with case.repository.atomic(), case.repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "hints_used, correctness, latency_seconds, manual_review, created_at, session_id, primed, evidence_origin)"
            " VALUES ('att_orchestrator', 'pi_svd_define_001', ?, 'short_answer', 'independent_attempt', 0, 0.0, 60, "
            "0, ?, NULL, 0, 'human')", (LO_ID, NOW_ISO))
        store.insert_workflow(connection, {"id": "wf_automatic", "source_attempt_id": "att_orchestrator",
                                           "revision_key": "r1", "learning_object_id": LO_ID, "session_id": None,
                                           "surface": "desktop", "origin": "practice", "lane": "probe",
                                           "feedback_held": 0, "created_at": NOW_ISO})
        decision_id = log_followup_decision(connection, {
            "workflow": {"id": "wf_automatic", "learning_object_id": LO_ID, "source_attempt_id": "att_orchestrator",
                         "factor_id": case.factor},
            "chosen_ref": chosen_ref, "propensity": 0.8, "router_record": {}, "config": case.vault.config,
            "decided_at": NOW_ISO})
        store.update_workflow(connection, "wf_automatic", at=NOW_ISO, factor_id=case.factor, decision_id=decision_id,
                              chosen_ref=chosen_ref)
    return str(decision_id)


def _learner_decisions(case) -> int:
    with case.repository.connection() as connection:
        return connection.execute("SELECT COUNT(*) FROM router_decisions WHERE surface = 'causal_repair'").fetchone()[0]


def test_r11_the_learner_lane_reads_the_automatic_lanes_decision_and_flips_no_coin(tmp_path, monkeypatch):
    from learnloop.router.plan_log import NO_INTERVENTION_REF
    from learnloop.router_objective import probe_coin as PC

    case = _learner(tmp_path, monkeypatch)  # a fresh coin here would offer the probe
    flipped: list[str] = []
    real = PC.flip
    monkeypatch.setattr(PC, "flip", lambda *a, **k: flipped.append("flip") or real(*a, **k))
    decided = _automatic_decision_on(case, NO_INTERVENTION_REF)
    status = _read(case)
    assert (status["routerState"], status["routerDecisionId"], status["probeOffered"]) == ("not_selected", decided,
                                                                                            False)
    assert status["reason"] == "router_did_not_select_probe_on_automatic_lane"
    assert not flipped and _learner_decisions(case) == 0
    refused = _offer(case)
    assert (refused["accepted"], refused["reason"]) == (False, "router_decision_required")


def test_r11_a_probe_the_automatic_lane_asked_is_the_factors_one_probe(tmp_path, monkeypatch):
    from learnloop.router.plan_log import INSERT_REF

    case = _learner(tmp_path, monkeypatch)
    decided = _automatic_decision_on(case, INSERT_REF)
    status = _read(case)
    assert (status["routerState"], status["routerDecisionId"], status["reason"]) == (
        "not_selected", decided, "router_asked_on_automatic_lane")
    assert _learner_decisions(case) == 0


def _second_factor(case) -> str:
    """A newer open factor on the same cause: another miss (with causes of its own on the learning object) whose factor
    names the same rival causes."""

    from tests.causal_orchestrator_helpers import _seed_factor

    _seed_factor(case.repository, attempt_id="att_second")
    causes = case.repository.unresolved_cause_factor(case.factor)["candidate_causes"]
    return case.repository.insert_unresolved_cause_factor(attempt_id="att_second", candidate_causes=causes,
                                                          algorithm_version="causal_attribution_p2", clock=CLOCK)


def test_r12_the_status_and_its_decision_are_the_shown_factors_never_the_oldest(tmp_path, monkeypatch):
    from learnloop.router.plan_log import learner_probe_decision

    from tests.probe_router_authority_helpers import call

    case = _learner(tmp_path, monkeypatch)
    second = _second_factor(case)
    named = call(case.ctx, "causal_repair_status", {"misconceptionId": case.first, "factorId": second})["repairStatus"]
    by_attempt = call(case.ctx, "causal_repair_status",
                      {"misconceptionId": case.first, "attemptId": "att_second"})["repairStatus"]
    assert named["factorId"] == by_attempt["factorId"] == second
    with case.repository.connection() as connection:
        # The oldest factor's probe was never decided by the second factor's feedback.
        assert learner_probe_decision(connection, case.factor) is None


def test_r12_teach_me_now_reads_the_factor_it_recorded_consent_on(tmp_path, monkeypatch):
    from tests.probe_router_authority_helpers import call

    case = _learner(tmp_path, monkeypatch)
    second = _second_factor(case)
    taught = call(case.ctx, "causal_teach_me_now", {"factorId": second, "misconceptionId": case.first})["repairStatus"]
    assert (taught["factorId"], taught["reason"]) == (second, "learner_requested_teaching_without_probe")


def test_r12_a_factor_that_is_not_the_causes_is_refused(tmp_path, monkeypatch):
    import pytest

    from learnloop_sidecar.errors import SidecarError

    from tests.probe_router_authority_helpers import call

    case = _learner(tmp_path, monkeypatch)
    with pytest.raises(SidecarError):
        call(case.ctx, "causal_repair_status", {"misconceptionId": case.first, "factorId": "not_a_factor_of_it"})


# -- the probe priced as its answer will be admitted ------------------------------------------------------------------


def test_r14_a_reveal_on_the_learning_object_prices_the_probe_exposed(tmp_path, monkeypatch):
    from learnloop.attempts.reveal_ledger import record_reveal

    from tests.causal_orchestrator_helpers import LO_ID

    case = _learner(tmp_path, monkeypatch)
    # A solution shown on a sibling item of the learning object: the answer admission refuses any later answer on
    # the object as not independent, so the probe can separate no cause.
    assert record_reveal(case.repository, practice_item_id="pi_svd_define_001", learning_object_id=LO_ID,
                         source_kind="repair_display", amount=1.0)
    _read(case)
    detail = _decision(case)["detail"]
    assert detail["valuation"]["frozen"]["payload"]["exposed"] is True
    assert detail["valuation"]["exposure"]["reason"] == "post_reveal_not_independent"
    assert detail["evaluation"]["channel_use"] == "exposed" and detail["information"] == 0.0


def test_r14_with_nothing_revealed_the_probe_is_priced_unexposed_and_says_so(tmp_path, monkeypatch):
    case = _learner(tmp_path, monkeypatch)
    _read(case)
    valuation = _decision(case)["detail"]["valuation"]
    assert valuation["frozen"]["payload"]["exposed"] is False
    assert valuation["exposure"] == {"exposed": False, "reason": None, "scope": "item_and_learning_object",
                                     "at": valuation["exposure"]["at"]}
