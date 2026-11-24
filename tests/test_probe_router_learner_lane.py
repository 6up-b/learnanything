"""G2, the learner's lane: the action router decides whether the feedback screen offers the quick check
(``docs/reviews/refactor-g2-design.md`` §2d, ``docs/reviews/algorithm-probe-router.md``).

At ``PROBE_ROUTER_ALGORITHM_VERSION`` the repair status (``causal_repair_status``) is a read of facts: it forms no worth
verdict, and a reread of the same facts writes no new receipt. Whether the quick check is offered is the router's
decision (``daily_plan.learner_probe``), made once per factor and read back by every later read: the probe priced with
the existing instrument's channel (``diagnostic_value.evaluate_probe``); a learned probe (positive information value
at the learned slopes) an option of the mix, an unlearned one asked only by the probe coin at the stop coin's rate,
with its own seed, its own assignment row and the served distribution logged exactly. The status payload gains
``router_state``, ``router_decision_id`` and ``hard_stop_reasons``. An offer request without the router's selection
is a typed refusal. "Not now" and "Teach me now" keep their meaning. Below the tag, the predecessor exactly.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION, PROBE_ROUTER_ALGORITHM_VERSION, successors_from
from learnloop.daily_plan import learner_probe as LP
from learnloop.diagnosis import causal_orchestrator as causal
from learnloop.diagnosis import probe_offer
from learnloop.diagnosis.remediation import RemediationBlocked, start_remediation_episode
from learnloop.router.plan_log import LEARNER_PROBE_SURFACE, NO_PROBE_REF, PROBE_REF, learner_probe_receipt_key
from learnloop.router_objective import assignments as A
from learnloop.router_objective import probe_coin as PC

from tests.helpers import append_config_toml
from tests.probe_router_authority_helpers import (
    CLOCK,
    PROBE_ITEM,
    TAG,
    call,
    count,
    divergent_factor,
    receipts,
    router_rows,
    sidecar,
    table_rows,
)

HEAD = LATEST_ALGORITHM_VERSION
#: A stop coin (and so the probe coin) at 0.2.
COINS = "\n[router_objective]\nstop_coin = 0.2\n"


def _case(tmp_path, *, coins: str = COINS, **kwargs):
    case = divergent_factor(tmp_path, version=HEAD, **kwargs)
    if coins:
        append_config_toml(case.root, coins)
        from learnloop.vault.loader import load_vault

        case.vault = load_vault(case.root)
    return case


def _arm(monkeypatch, u: float) -> None:
    monkeypatch.setattr(PC, "draw_uniform", lambda seed: u)


def _read(ctx, case) -> dict:
    return call(ctx, "causal_repair_status", {"misconceptionId": case.first})["repairStatus"]


def _learner_rows(repository) -> list[dict]:
    return [row for row in router_rows(repository) if row["surface"] == LEARNER_PROBE_SURFACE]


def _assignments(repository) -> list[dict]:
    rows = table_rows(repository, "policy_experiment_assignments")
    for row in rows:
        row["detail_json"] = json.loads(row["detail_json"] or "{}")
    return rows


# -- the facts read and the one decision ------------------------------------------------------------------------------


def test_the_head_keeps_the_tag():
    assert HEAD in successors_from(PROBE_ROUTER_ALGORITHM_VERSION)


def test_a_status_read_decides_once_and_a_reread_draws_nothing_and_writes_no_receipt(tmp_path, monkeypatch):
    case = _case(tmp_path)
    _arm(monkeypatch, 0.9)
    ctx = sidecar(case.root)
    first = _read(ctx, case)
    (decision,) = _learner_rows(case.repository)
    assert first["routerState"] == "not_selected" and first["routerDecisionId"] == decision["id"]
    assert first["status"] == "started" and first["probeOffered"] is False and first["actions"] == []
    # No worth verdict: the receipt records the facts, and says the router decides.
    (receipt,) = receipts(case.repository, case.factor)
    assert receipt["decision"] == causal.ROUTER_DECIDES and first["probeDecision"] == causal.ROUTER_DECIDES
    inputs = json.loads(receipt["inputs_json"])
    assert inputs["decided_by"] == "probe_router" and "expected_avoided_overteaching_minutes" not in inputs
    # A remounted panel reads the same decision: no new router row, no new receipt.
    again = _read(ctx, case)
    assert again["routerDecisionId"] == decision["id"] and again["routerState"] == "not_selected"
    assert len(_learner_rows(case.repository)) == 1 and len(receipts(case.repository, case.factor)) == 1
    assert decision["receipt_key"] == learner_probe_receipt_key(case.factor)


def test_an_unlearned_probe_is_offered_only_by_the_coin_with_its_exact_propensity(tmp_path, monkeypatch):
    case = _case(tmp_path)
    _arm(monkeypatch, 0.05)
    status = _read(sidecar(case.root), case)
    assert (status["status"], status["routerState"], status["probeOffered"]) == ("needs_disambiguation", "selected",
                                                                                 True)
    assert [action["id"] for action in status["actions"]] == ["take_quick_check", "teach_me_now", "not_now"]
    (decision,) = _learner_rows(case.repository)
    detail = decision["detail_json"]
    # At the seeded slopes no answer changes the repair the router would choose: no information, so unlearned.
    assert detail["learned"] is False and detail["information"] == 0.0
    assert "mixture" not in detail and detail["probe_coin"]["arm"] == PC.ASK
    assert (decision["chosen_ref"], decision["propensity"]) == (PROBE_REF, pytest.approx(0.2))
    # The row names the item only through its candidates: an acceptance's pin binds the administration.
    assert decision["chosen_practice_item_id"] is None
    candidates = {row["ref"]: row for row in json.loads(decision["candidates_json"])}
    assert candidates[NO_PROBE_REF]["propensity"] == pytest.approx(0.8)
    assert detail["served_pi"] == pytest.approx({PROBE_REF: 0.2, NO_PROBE_REF: 0.8})
    (assignment,) = _assignments(case.repository)
    assert (assignment["experiment_id"], assignment["unit_id"], assignment["variant"], assignment["propensity"]) == (
        A.PROBE_COIN, decision["id"], PC.ASK, 0.2)
    # Seeded by the factor, so a retry or a concurrent read draws the same.
    assert assignment["seed"] == PC.seed_for(f"learner_probe:{case.factor}", "learner_probe")


def test_the_valuation_prices_the_existing_instruments_channel(tmp_path, monkeypatch):
    case = _case(tmp_path)
    _arm(monkeypatch, 0.9)
    _read(sidecar(case.root), case)
    (decision,) = _learner_rows(case.repository)
    evaluation = decision["detail_json"]["evaluation"]
    payload = evaluation["decisions"]
    assert payload["1_unauthored_channel"]["status"] == LP.OWNER_DECISIONS.status
    assert evaluation["channel_use"] == "channel" and evaluation["values"]["information"] == 0.0
    assert decision["detail_json"]["valuation"]["status"] == "valued"


def test_a_learned_probe_is_an_option_of_the_mix_and_no_coin_is_flipped(tmp_path, monkeypatch):
    case = _case(tmp_path)
    real = LP.value

    def learned(*args, **kwargs):
        valuation, record = real(*args, **kwargs)
        values = {**valuation.record["values"], "information": 0.5}
        return SimpleNamespace(record={**valuation.record, "values": values}, choice="probe"), record

    monkeypatch.setattr(LP, "value", learned)
    _arm(monkeypatch, 0.0)
    _read(sidecar(case.root), case)
    (decision,) = _learner_rows(case.repository)
    detail = decision["detail_json"]
    assert detail["learned"] is True and "probe_coin" not in detail
    mixture = detail["mixture"]
    assert mixture["numeric_choice"] == PROBE_REF and mixture["support"] == [NO_PROBE_REF, PROBE_REF]
    assert sum(mixture["pi"].values()) == pytest.approx(1.0)
    assert decision["propensity"] == pytest.approx(mixture["pi"][decision["chosen_ref"]])
    assert _assignments(case.repository) == []


def test_a_zero_share_never_offers_an_unlearned_probe_and_writes_no_assignment(tmp_path, monkeypatch):
    case = _case(tmp_path, coins="\n[router_objective]\nstop_coin = 0\n")
    _arm(monkeypatch, 0.0)
    status = _read(sidecar(case.root), case)
    (decision,) = _learner_rows(case.repository)
    assert (status["routerState"], decision["chosen_ref"], decision["propensity"]) == ("not_selected", NO_PROBE_REF,
                                                                                       1.0)
    assert decision["propensity_kind"] == "deterministic" and _assignments(case.repository) == []


# -- the offer, the learner's refusals, the repair entry -------------------------------------------------------------


def test_an_offer_request_without_the_routers_selection_is_a_typed_refusal(tmp_path, monkeypatch):
    case = _case(tmp_path)
    ctx = sidecar(case.root)
    # Before any decision (a stale request from before the tag): refused, and no decision is made by the request.
    early = call(ctx, "causal_probe_offer_action", {"factorId": case.factor})
    assert early["offer"]["accepted"] is False and early["offer"]["reason"] == probe_offer.ROUTER_DECISION_REQUIRED
    assert early["router"]["routerState"] == "pending" and _learner_rows(case.repository) == []
    _arm(monkeypatch, 0.9)
    _read(ctx, case)
    late = call(ctx, "causal_probe_offer_action", {"factorId": case.factor})
    assert late["offer"]["reason"] == probe_offer.ROUTER_DECISION_REQUIRED
    assert late["router"]["routerState"] == "not_selected"
    assert count(case.repository, "probe_presentations") == 0


def test_the_selected_probe_is_accepted_once_and_its_pin_names_the_router_decision(tmp_path, monkeypatch):
    case = _case(tmp_path)
    _arm(monkeypatch, 0.05)
    ctx = sidecar(case.root)
    status = _read(ctx, case)
    offer = call(ctx, "causal_probe_offer_action", {"factorId": case.factor,
                                                    "decisionReceiptId": status["decisionReceiptId"]})["offer"]
    assert offer["accepted"] is True and offer["practiceItemId"] == PROBE_ITEM
    pin = probe_offer.pinned_causal_probe(case.repository, offer["presentationId"])
    assert pin["router_decision_id"] == status["routerDecisionId"]
    again = call(ctx, "causal_probe_offer_action", {"factorId": case.factor})["offer"]
    assert again["accepted"] is True and again["reason"] == "probe_already_pinned"


def test_not_now_after_the_selection_withdraws_the_offer_and_refuses_acceptance(tmp_path, monkeypatch):
    case = _case(tmp_path)
    _arm(monkeypatch, 0.05)
    ctx = sidecar(case.root)
    _read(ctx, case)
    call(ctx, "causal_probe_defer", {"factorId": case.factor})
    status = _read(ctx, case)
    assert (status["status"], status["reason"], status["routerState"]) == (
        "needs_disambiguation", "defer_learner_preference", "unavailable")
    assert status["hardStopReasons"] == ["learner_preference"] and status["probeOffered"] is False
    assert [action["id"] for action in status["actions"]] == ["teach_me_now"]
    refused = call(ctx, "causal_probe_offer_action", {"factorId": case.factor})["offer"]
    assert (refused["accepted"], refused["reason"]) == (False, "learner_preference")


def test_teach_me_now_starts_the_repair_without_the_probe(tmp_path, monkeypatch):
    case = _case(tmp_path)
    _arm(monkeypatch, 0.05)
    status = probe_offer.request_teaching_now(case.vault, case.repository, misconception_id=case.first,
                                              factor_id=case.factor, clock=CLOCK)
    assert (status.status, status.reason, status.router_state) == (
        "started", "learner_requested_teaching_without_probe", "unavailable")
    assert status.episode is not None and _learner_rows(case.repository) == []


def test_the_repair_entry_holds_only_on_the_routers_selection(tmp_path, monkeypatch):
    held_case = _case(tmp_path / "held")
    _arm(monkeypatch, 0.05)
    held = call(sidecar(held_case.root), "start_remediation", {"misconceptionId": held_case.first})
    assert held["episode"] is None and held["repairStatus"]["routerState"] == "selected"
    assert held["repairStatus"]["probeOffered"] is True
    started_case = _case(tmp_path / "started")
    _arm(monkeypatch, 0.9)
    started = call(sidecar(started_case.root), "start_remediation", {"misconceptionId": started_case.first})
    assert started["episode"] is not None and started["repairStatus"] is None
    assert len(_learner_rows(started_case.repository)) == 1


def test_a_repair_entry_with_no_router_behind_it_starts_the_repair(tmp_path):
    case = _case(tmp_path)
    episode = start_remediation_episode(case.repository, case.first, vault=case.vault, clock=CLOCK)
    assert episode is not None and _learner_rows(case.repository) == []


def test_no_executable_instrument_is_unavailable_and_nothing_is_drawn(tmp_path):
    case = _case(tmp_path, instrument=False)
    status = _read(sidecar(case.root), case)
    assert (status["status"], status["reason"], status["routerState"]) == (
        "blocked_pending_review", "no_discriminating_instrument", "unavailable")
    assert status["hardStopReasons"] == ["no_executable_instrument"]
    assert _learner_rows(case.repository) == [] and _assignments(case.repository) == []


def test_one_repair_for_both_causes_settles_the_status_with_no_probe_to_decide(tmp_path):
    case = _case(tmp_path, instrument=False, first="repair:recall", second="repair:recall")
    status = causal.causal_repair_status(case.vault, case.repository, misconception_id=case.first, clock=CLOCK,
                                         start_repair=True)
    assert (status.status, status.probe_decision, status.router_state) == (
        "safe_common_repair_available", "skip_common_repair", "unavailable")
    assert status.hard_stop_reasons == ("common_repair_covers",) and status.episode is not None


# -- below the tag -----------------------------------------------------------------------------------------------------


def test_below_the_tag_the_status_is_the_verdicts_and_carries_no_router_keys(tmp_path):
    case = divergent_factor(tmp_path, version=TAG)
    ctx = sidecar(case.root)
    status = _read(ctx, case)
    assert (status["status"], status["probeDecision"], status["probeOffered"]) == ("needs_disambiguation",
                                                                                   "probe_now", True)
    assert "routerState" not in status and "routerDecisionId" not in status
    _read(ctx, case)
    assert len(receipts(case.repository, case.factor)) == 2 and count(case.repository, "router_decisions") == 0
    offer = call(ctx, "causal_probe_offer_action", {"factorId": case.factor})
    assert offer["offer"]["accepted"] is True and "router" not in offer


def test_below_the_tag_the_repair_entry_is_held_by_the_verdict(tmp_path):
    case = divergent_factor(tmp_path, version=TAG)
    with pytest.raises(RemediationBlocked):
        start_remediation_episode(case.repository, case.first, vault=case.vault, clock=CLOCK)
