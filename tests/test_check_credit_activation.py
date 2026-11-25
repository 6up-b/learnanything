"""The committed-check credit at its tag, mvp-0.62 (``docs/reviews/algorithm-mvp-0.62.md``): a new lesson offer carries
its check's delivery sensors, its numeric action is typed, every rollout of the decision prices the check through
``router_objective.check_value``, the offer's identity moves with its delivery evidence, and the decision's trace holds
a lossless replay payload the stored-row report reads exactly. Below the tag (mvp-0.61) every one of these is as it
was: the record, the untyped action, the rollouts, no payload."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
import importlib.util
import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from learnloop.algorithm_versions import (
    COMMITTED_CHECK_DELIVERY_ALGORITHM_VERSION,
    COMMITTED_CHECK_DELIVERY_VERSIONS,
    EVIDENCE_READING_FIX_ALGORITHM_VERSION,
    LATEST_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    committed_check_delivery_on,
)
from learnloop.daily_plan import lesson_offer as LO_OFFER
from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.daily_plan import objective_chooser as OC
from learnloop.daily_plan.objective_seeds import numeric_seed
from learnloop.daily_plan.router_chooser import _hash
from learnloop.daily_plan.types import PlanState
from learnloop.router import lesson_suggestions as LS
from learnloop.router_objective import check_replay as CR
from learnloop.router_objective import check_value as CV
from learnloop.router_objective import rollouts as ROL
from learnloop.router_objective import trace as TR
from learnloop.router_objective import trace_assembly as T
from learnloop.router_objective import types as OT

from tests.check_credit_helpers import DRAWS, SEED, fixture_inputs, typed, typed_offer
from tests.check_credit_report_helpers import NOW, add_trace, seed_report_vault
from tests.daily_plan_fakes import record_attempt
from tests.router_mixture_helpers import mixture_env
from tests.router_model_fakes import fake_runtime

OLD_TAG, NEW_TAG = EVIDENCE_READING_FIX_ALGORITHM_VERSION, COMMITTED_CHECK_DELIVERY_ALGORITHM_VERSION
#: What a check's record carries from the tag on, beside the predecessor's four fields.
SENSOR_FIELDS = {"key", "group", "delivery", "minutes", "rollout_policy", "stream_layout"}


def test_the_tag():
    # A section's end (mvp-0.63), an untaken repair episode's end (mvp-0.64), the application order (mvp-0.65) and
    # the lifecycle inputs (mvp-0.66) landed after it and keep it.
    assert NEW_TAG == "mvp-0.62" == SUCCESSOR_CHAIN[-12] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.73"
    assert SUCCESSOR_CHAIN[-13] == OLD_TAG
    assert COMMITTED_CHECK_DELIVERY_VERSIONS == frozenset({NEW_TAG, "mvp-0.63", "mvp-0.64", "mvp-0.65", "mvp-0.66", "mvp-0.67", "mvp-0.68", "mvp-0.69", "mvp-0.70", "mvp-0.71", "mvp-0.72", "mvp-0.73"})
    for version, on in ((OLD_TAG, False), (NEW_TAG, True)):
        config = SimpleNamespace(algorithms=SimpleNamespace(algorithm_version=version))
        assert committed_check_delivery_on(config) is on
        assert (OC._evaluator(config) is CV.evaluate) is on
        assert (OC._evaluator(config) is ROL.evaluate) is not on


def _env(tmp_path, monkeypatch, version, lo="lo_m1"):
    env = mixture_env(tmp_path, fake_runtime(), version=version)
    candidate = LS.Candidate(ref=LS.lesson_ref(lo), learning_object_ids=(lo,), reason="new_goal",
                             predicted_success=0.3, title=lo)
    monkeypatch.setattr(SG, "build_candidates", lambda vault, repository, *, now_iso: ([candidate], {}))
    return env


def _offer(env, now_iso=None):
    offer = LO_OFFER.build(env.vault, env.repository, today=env.today(), now_iso=now_iso or env.now_iso(),
                           local_hour=9.0, minutes_left=30.0, reentry=False, forced=False)
    assert offer.candidate is not None
    return offer.candidate


@pytest.mark.parametrize("version", [OLD_TAG, NEW_TAG])
def test_both_tags_the_offer_record_and_its_action(tmp_path, monkeypatch, version):
    env = _env(tmp_path, monkeypatch, version)
    candidate = _offer(env)
    (check,) = LO_OFFER.card(candidate)["checks"]
    from learnloop.daily_plan import objective_inputs as OI

    action = OI.action_for(env.vault, env.repository, candidate, practiced=set(), spread=0.0)
    if version == OLD_TAG:
        # mvp-0.61's record, byte for byte in its keys, and its untyped pair.
        assert set(check) == {"lo", "purpose", "days", "basis"}
        assert action.commitments == (("lo_m1", 3.0),) and action.checks == ()
        return
    assert set(check) == {"lo", "purpose", "days", "basis"} | SENSOR_FIELDS
    delivery = check["delivery"]
    # A question exists and no receipt was ever recorded: the one-trial seed alone, a point mass at one.
    assert (delivery["eligible_now"], delivery["successes"], delivery["failures"]) == (True, 0, 0)
    assert (delivery["alpha"], delivery["beta"], delivery["predictive_mean"]) == (1.0, 0.0, 1.0)
    assert delivery["policy_version"] and delivery["priors_version"] and delivery["evidence_digest"]
    # The decision's clock stays out of the record (it is in the boundary's identity; the payload holds the clock).
    assert "as_of" not in delivery and "as_of" not in check["minutes"]
    assert check["minutes"]["basis"] == "item_estimate" and check["minutes"]["minutes"] > 0.0
    assert (check["rollout_policy"], check["stream_layout"]) == (CV.POLICY_VERSION, CV.STREAM_LAYOUT_VERSION)
    assert action.commitments == ()
    (typed_check,) = action.checks
    assert (typed_check.lo, typed_check.days, typed_check.delivery, typed_check.minutes) == (
        "lo_m1", 3.0, (1.0, 0.0), check["minutes"]["minutes"])
    assert (typed_check.key, typed_check.group) == ("lo_m1:retention:0", "legacy_vault_item:retention")


def _identity(candidate):
    """What the boundary hashes of the offer (``BlockCandidate.log_row``) and the numeric seed it feeds."""

    row = candidate.log_row()
    return _hash(row), numeric_seed({"kind": "objective_block", "support": [row]})


def _missing_receipt(env, lesson_id="lesson_missing"):
    at = (env.clock.now() - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with env.repository.connection() as db:
        db.execute(
            "INSERT INTO lessons(id, driver, origin, entry, goal_text, goal_json, learning_object_ids_json, "
            "doctrine_version, brief_version, algorithm_version, opened_at, closed_at, close_reason) "
            "VALUES (?, 'desktop', 'learner_pick', 'learning_object', 'g', '{}', '[\"lo_m1\"]', 'd', 'b', 'v', ?, ?, "
            "'goal_reached')", (lesson_id, at, at))
        db.execute("INSERT INTO lesson_receipts VALUES (?, 'lesson_receipt_v1', 'goal_reached', ?, ?)",
                   (lesson_id, json.dumps({"delayed_checks": [{"purpose": "retention", "missing": True}]}), at))
        db.commit()


def test_the_offers_identity_moves_with_its_delivery_evidence_and_only_with_it(tmp_path, monkeypatch):
    """At the tag the offer's record is in the boundary's identity (its ``log_row``), so a cached or prefetched
    decision cannot keep obsolete delivery evidence: the identity moves when the availability, the receipts or the
    minutes move, and stays when only the clock does."""

    env = _env(tmp_path, monkeypatch, NEW_TAG)
    now = env.now_iso()
    base = _offer(env, now)
    later = _offer(env, (env.clock.now() + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"))
    assert LO_OFFER.card(later)["checks"] == LO_OFFER.card(base)["checks"]
    assert _identity(_offer(env, now)) == _identity(base)

    # The receipts: one planned retention check the picker could not fill is one failure, and a new digest.
    _missing_receipt(env)
    receipts = _offer(env, now)
    moved = LO_OFFER.card(receipts)["checks"][0]["delivery"]
    assert moved["failures"] == 1 and moved["evidence_digest"] != LO_OFFER.card(base)["checks"][0]["delivery"][
        "evidence_digest"]
    assert (moved["alpha"], moved["beta"]) == (1.0, 1.0)
    assert _identity(receipts)[0] != _identity(base)[0] and _identity(receipts)[1] != _identity(base)[1]

    # The minutes: an answer's latency on another topic's item in the same mode moves the plan's estimate.
    record_attempt(env.repository, "pi_p1a", "lo_p1", env.clock.now() - timedelta(hours=1), latency_seconds=600)
    minutes = _offer(env, now)
    assert (LO_OFFER.card(minutes)["checks"][0]["minutes"]["minutes"]
            != LO_OFFER.card(receipts)["checks"][0]["minutes"]["minutes"])
    assert LO_OFFER.card(minutes)["checks"][0]["delivery"] == moved
    assert _identity(minutes) != _identity(receipts)

    # The availability: once every question on the topic has been attempted, no check can be committed today.
    for item in ("pi_m1a", "pi_m1b"):
        record_attempt(env.repository, item, "lo_m1", env.clock.now() - timedelta(hours=1))
    unavailable = _offer(env, now)
    gone = LO_OFFER.card(unavailable)["checks"][0]["delivery"]
    assert gone["eligible_now"] is False and (gone["alpha"], gone["beta"]) == (0.0, 2.0)
    assert _identity(unavailable) != _identity(minutes)


def _numeric(env, candidate):
    from learnloop.daily_plan.types import STOP_FOR_TODAY

    state = PlanState(plan_id="plan_none", kind="normal", minutes_budget=30.0, minutes_left=30.0,
                      lane_minutes_left={"new": 30.0}, days_since_last_activity=0, streak_days=1,
                      current_block_id=None)
    return OC.run_numeric(env.vault, env.repository, state=state, support=[candidate.candidate_id, STOP_FOR_TODAY],
                          candidates={candidate.candidate_id: candidate}, now_iso=env.now_iso(), seed="activation",
                          deadline=None)


@pytest.mark.parametrize("version", [OLD_TAG, NEW_TAG])
def test_both_tags_the_decisions_numeric_answer_and_its_trace(tmp_path, monkeypatch, version):
    """The numeric policy end to end: below the tag the offer is valued with its untyped pair by the rollouts and no
    payload is written; at the tag its typed check is valued by the check-credit path, and the answer carries a
    payload that recomputes its values exactly and survives the trace's rounding."""

    env = _env(tmp_path, monkeypatch, version)
    candidate = _offer(env)
    numeric = _numeric(env, candidate)
    assert numeric.status == "answered", numeric.error
    offer = next(action for action in numeric.actions if action.ref == candidate.candidate_id)
    trace = T.decision_trace(
        support=[candidate.candidate_id], by_id={candidate.candidate_id: candidate}, feasible=[candidate], titles={},
        numeric=numeric, llm=None, decider=None, staged_ref=candidate.candidate_id, weight=(0.5, {}), effective={},
        pi={}, drawn=SimpleNamespace(chosen=candidate.candidate_id, component="numeric", propensity=1.0, u1=0.0,
                                     u2=0.0),
        seed="activation", config=env.vault.config, now_iso=env.now_iso(), guard={}, stop_in_support=True,
        card_version=None)
    if version == OLD_TAG:
        assert offer.commitments and not offer.checks and numeric.replay is None
        assert CR.TRACE_KEY not in trace
        assert "checks" not in trace["candidates"][candidate.candidate_id]["offer"]["action"]
        return
    assert offer.checks and not offer.commitments
    assert trace["candidates"][candidate.candidate_id]["offer"]["action"]["checks"][0]["key"] == "lo_m1:retention:0"
    stored = TR.assemble(trace, decision_id="d", decision_kind="plan_block", decision_state_id=None,
                         algorithm_version=NEW_TAG, local_date=env.today(), session_id=None, created_at=env.now_iso())
    body = CR.read(json.loads(stored["trace_json"])[CR.TRACE_KEY])
    assert body["inputs"] == numeric.inputs and tuple(body["proposed_actions"]) == numeric.actions
    assert tuple(body["old_actions"]) == tuple(CR.untyped(action) for action in numeric.actions)
    assert body["sensors"][f"{candidate.candidate_id}:lo_m1:retention:0"] == LO_OFFER.card(candidate)["checks"][0]
    again = CV.evaluate(body["inputs"], body["proposed_actions"], draws=body["draws"], max_draws=body["draws"],
                        seed=body["seed"], **body["options"]).by_ref()
    for row in numeric.evaluation.valued:
        assert again[row.ref].q_draws == row.q_draws


def test_the_payload_is_lossless_and_refuses_what_it_cannot_hold():
    inputs = fixture_inputs(topics=(OT.Topic(lo="lo_a", eta_mean=1 / 3, eta_var=math.pi / 10),))
    actions = (typed_offer("offer", typed(minutes=7 / 3, delivery=(0.1, 19.0))),
               OT.Action(ref=OT.STOP_FOR_TODAY, kind=OT.STOP))
    stored = CR.record(inputs, actions, seed=SEED, draws=DRAWS, first_draws=DRAWS, max_draws=16, as_of=NOW,
                       options={"consistent_review_draw": True}, versions={"rollout_policy": CV.POLICY_VERSION},
                       sensors={})
    assert stored is not None and stored["version"] == CR.REPLAY_VERSION
    body = CR.read(stored)
    assert body["inputs"] == inputs and tuple(body["proposed_actions"]) == actions
    assert body["inputs"].topics[0].eta_var == math.pi / 10  # every bit, not six decimals
    (old, _stop) = body["old_actions"]
    assert old.checks == () and old.commitments == (("lo_a", 3.0),)
    # The trace's six-decimal rounding leaves the string as it is.
    row = TR.assemble({CR.TRACE_KEY: stored}, decision_id="d", decision_kind="plan_block", decision_state_id=None,
                      algorithm_version=NEW_TAG, local_date=NOW[:10], session_id=None, created_at=NOW)
    assert CR.read(json.loads(row["trace_json"])[CR.TRACE_KEY])["inputs"] == inputs
    with pytest.raises(ValueError, match="digest"):
        CR.read({**stored, "payload": stored["payload"].replace("0.1", "0.2", 1)})
    with pytest.raises(ValueError, match="version"):
        CR.read({**stored, "version": "other"})
    bad = replace(inputs, horizon_days=float("nan"))
    assert CR.record(bad, actions, seed=SEED, draws=DRAWS, first_draws=DRAWS, max_draws=DRAWS, as_of=NOW, options={},
                     versions={}, sensors={}) is None


@pytest.fixture(scope="module")
def report():
    path = Path(__file__).resolve().parents[1] / "scripts" / "check_credit_report.py"
    spec = importlib.util.spec_from_file_location("check_credit_report", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _new_decision_payload(q_recorded=None, *, as_of="2026-10-31T08:59:00Z"):
    """A synthetic mvp-0.62 decision on the design's worked fixture: the offer's check never delivered (no question),
    so the decision valued the lesson alone; its payload, and the value its trace recorded."""

    inputs = fixture_inputs()
    stop = OT.Action(ref=OT.STOP_FOR_TODAY, kind=OT.STOP)
    actions = (typed_offer("lesson_offer:0", typed(delivery=(0.0, 1.0))), stop)
    from learnloop.daily_plan import check_delivery as CD

    sensors = {"lesson_offer:0:c0": {"delivery": {"policy_version": CD.DELIVERY_POLICY_VERSION,
                                                  "priors_version": CD.PRIORS_VERSION}}}
    stored = CR.record(inputs, actions, seed=SEED, draws=DRAWS, first_draws=DRAWS, max_draws=DRAWS, as_of=as_of,
                       options={}, versions={"rollout_policy": CV.POLICY_VERSION,
                                             "streams": CV.STREAM_LAYOUT_VERSION}, sensors=sensors)
    valued = CV.evaluate(inputs, list(actions), draws=DRAWS, seed=SEED).by_ref()["lesson_offer:0"]
    q = valued.q if q_recorded is None else q_recorded
    return {CR.TRACE_KEY: stored, "candidates": {"lesson_offer:0": {"terms": {"q": q}}}}, valued


def test_the_report_reads_a_new_decision_exactly(report, tmp_path):
    paths, repo = seed_report_vault(tmp_path / "vault")
    trace, valued = _new_decision_payload()
    add_trace(repo, "decision-0", trace)
    data = report.build_report(paths.sqlite_path, as_of=NOW)
    exact = data["comparisons"]["exact_historical"]
    assert (exact["computable"], exact["coverage_reasons"]) == (1, {"no_trace": 7})
    old = ROL.evaluate(fixture_inputs(), [CR.untyped(typed_offer("lesson_offer:0", typed(delivery=(0.0, 1.0))))],
                       draws=DRAWS, seed=SEED).by_ref()["lesson_offer:0"]
    # The known difference: the old pricing credits the never-delivered check (0.6 against 0.5 on the accepted
    # branch), at the drawn acceptance p̄ ≈ 0.5.
    assert exact["values"]["proposed_q"]["mean"] == pytest.approx(valued.q, abs=1e-12)
    assert exact["values"]["old_q"]["mean"] == pytest.approx(old.q, abs=1e-12)
    assert exact["values"]["difference"]["mean"] == pytest.approx(valued.q - old.q, abs=1e-12)
    assert valued.q - old.q == pytest.approx(-0.05, abs=1e-4)


@pytest.mark.parametrize("why", ["recorded_value", "clock"])
def test_the_report_refuses_a_payload_that_is_not_this_decisions(report, tmp_path, why):
    paths, repo = seed_report_vault(tmp_path / "vault")
    trace, valued = (_new_decision_payload(q_recorded=0.123) if why == "recorded_value"
                     else _new_decision_payload(as_of="2026-10-31T09:00:01Z"))  # read after the decision
    add_trace(repo, "decision-0", trace)
    exact = report.build_report(paths.sqlite_path, as_of=NOW)["comparisons"]["exact_historical"]
    assert exact["computable"] == 0
    assert exact["coverage_reasons"] == {"no_trace": 7, "invalid_or_unsupported_replay_payload": 1}
