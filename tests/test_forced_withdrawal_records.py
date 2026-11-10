"""Refactor B3 (ADR-017, strategy §3.6 case 2): forced items, withdrawals and boundary failures leave decision records,
read back through ``learnloop why``.

Before B3 each of these was silent or answerable only by time-ordering:

* **an offer taken back for forced items** (the Nov 8 case, IH2's switch off): the ``expired`` row said
  ``forced_items``, but not which probe forced it, its workflow, or the decision that came next. Now an
  ``offer_withdrawn`` record names the forced items with their workflows and source attempts, its parent is the
  offer's ``plan_block``, and the next boundary's ``plan_block`` names it as its parent;
* **IH2's contest** (switch on): the contest's ``plan_block`` names the offer it replaces and the forced items, with
  both options' chances, and the replaced offer gets an ``offer_withdrawn`` record naming the decision;
* **plan decisions name their triggering attempt** (break 1): ``facts.trigger_attempt``;
* **the restraint gate** (``plan_interrupt``, B2's open item): what it let in, made wait or refused, by which rule;
* **a boundary step that failed** (the day's check draw or placement, the lesson offer's builder): a log line only.
  Now a ``failed`` child of the boundary's record, with the type and where, never the message;
* **AD unavailable** (the incumbent served): a log line and a JSONL denial line only. Now an ``ad_slot`` record,
  naming the phase, AD's code and what the guard refused (verb, table, reader), beside the JSONL log, which
  ``learnloop ad report`` and the upgrade's archival still read;
* **a cold check the serve could not take cold**: served as practice, with a log line only. Now a
  ``serve_eligibility`` record;
* **a Today offer published unlogged** (the map's S12, a head mismatch): a warning only. Now a ``today_offer``
  record, ``failed``, naming both heads, its parent the build's ``slate`` record.

Every model is a fake; every assertion reads the records back through ``learnloop why --json``.
"""

from __future__ import annotations

from dataclasses import replace
import json
from typing import Any

import pytest
from typer.testing import CliRunner

from learnloop import provenance
from learnloop.daily_plan import engine as E
from learnloop.daily_plan.engine import advance

from tests.router_mixture_helpers import mixture_env, rows
from tests.router_model_fakes import FakeDecider, fake_runtime, first_option, seed_with_first_uniform
from tests.test_ih2_lessons_compete import OFF, OLD, QUIET, _env as _ih2_env, _open_offer, _ready_probe
from tests.test_ih2_lessons_compete import TAG as IH2_TAG
from tests.test_ih2_lessons_compete import draw  # noqa: F401 - the fixture
from tests.test_router_g4_restraint import DECIDER_ONLY, PAST_THE_FLOOR, _followup_env
from tests.test_te3b_offers import OFFER, offerable  # noqa: F401 - the fixture

SECRET = "the learner wrote about eigenvalues here"


def _why(root: Any, target: str, *more: str) -> dict[str, Any]:
    from learnloop.cli import app

    result = CliRunner().invoke(app, ["why", target, *more, "--json", "--vault", str(root)])
    assert result.exit_code == 0, result.output
    assert SECRET not in result.output
    return json.loads(result.output)


def _by_kind(payload: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return [record for record in payload["records"] if record["kind"] == kind]


def _latest_attempt(env) -> str:
    with env.repository.connection() as connection:
        return str(connection.execute(
            "SELECT id FROM practice_attempts ORDER BY created_at DESC, id DESC LIMIT 1").fetchone()[0])


def _all_records(env, kind: str) -> list[dict[str, Any]]:
    with env.repository.connection() as connection:
        found = [dict(row) for row in connection.execute(
            "SELECT * FROM decision_records WHERE kind = ? ORDER BY created_at, id", (kind,))]
    for row in found:
        for key in ("alternatives_json", "facts_json", "versions_json"):
            row[key] = json.loads(row[key])
    return found


# -- case 2: the offer taken back for forced items (IH2's switch off, and below its tag) ----------------------------


@pytest.mark.usefixtures("offerable")
@pytest.mark.parametrize("version,toml", [(IH2_TAG, OFF), (OLD, QUIET)], ids=["switch_off", "below_tag"])
def test_a_withdrawal_names_the_forced_probe_its_workflow_and_the_next_decision_points_to_it(tmp_path, draw, version,
                                                                                            toml):
    """Fail-first: before B3 nothing named the probe that forced the withdrawal, nor the decision that followed."""

    env = _ih2_env(tmp_path, version=version, toml=toml)
    step = _open_offer(env, draw)
    workflow = _ready_probe(env)
    probe = workflow["practice_item_id"]
    env.clock.advance(1)
    draw.prefer = (OFFER,)
    with provenance.trace_scope("TRACE_NEXT"):
        _record, served = advance(env, serve=True)
    assert served["kind"] == "item" and served["practice_item_id"] == probe  # what's served is unchanged
    offer_decision, offer_block = step["offer"]["decision_id"], step["block_id"]

    [withdrawn] = _by_kind(_why(env.vault.root, f"offer:{offer_decision}"), "offer_withdrawn")
    assert (withdrawn["status"], withdrawn["rule"], withdrawn["decided_by"]) == ("withdrawn", "forced_items", "plan")
    assert withdrawn["detail_table"] == "router_decisions" and withdrawn["detail_id"] == offer_decision
    [forced] = withdrawn["alternatives"]
    assert forced["ref"] == probe and forced["origin"] == E.ORIGIN_FOLLOWUP
    assert forced["workflow"] == "fw_test" and forced["source_attempt"] == workflow["source_attempt_id"]
    facts = withdrawn["facts"]
    assert facts["offer_block"] == offer_block and facts["forced"] == [probe] and facts["workflows"] == ["fw_test"]
    assert facts["source_attempts"] == [workflow["source_attempt_id"]] and facts["expired_row"] is True
    # Its parent is the offer's own plan_block record.
    [drawn] = _by_kind(_why(env.vault.root, f"block:{offer_block}"), "plan_block")
    assert withdrawn["parent_id"] == drawn["id"] and drawn["chosen_ref"] == OFFER

    # The next decision, in the same trace, names the withdrawal as its parent.
    trace = _why(env.vault.root, withdrawn["id"])
    [nxt] = [record for record in trace["records"] if record["kind"] == "plan_block"
             and record["parent_id"] == withdrawn["id"]]
    assert nxt["trace_id"] == withdrawn["trace_id"] == "TRACE_NEXT"
    assert nxt["subject_id"] == E.latest_today(env).current_block().id
    assert nxt["facts"]["forced"] == [probe] and nxt["facts"]["workflows"] == ["fw_test"]
    assert nxt["facts"]["trigger_attempt"] == _latest_attempt(env) == workflow["source_attempt_id"]
    assert [record["rule"] for record in _all_records(env, "offer_withdrawn")] == ["forced_items"]


# -- IH2's switch on: one contest decision replaces the withdrawal --------------------------------------------------


@pytest.mark.usefixtures("offerable")
def test_with_the_switch_on_the_contest_names_the_offer_it_replaces_and_both_chances(tmp_path, draw):
    env = _ih2_env(tmp_path)
    step = _open_offer(env, draw)
    workflow = _ready_probe(env)
    probe = workflow["practice_item_id"]
    offer_decision, offer_block = step["offer"]["decision_id"], step["block_id"]
    env.clock.advance(1)
    draw.prefer = ("followup_contest:",)
    _record, served = advance(env, serve=True)
    assert served["practice_item_id"] == probe
    contest_row = rows(env)[-1]

    [contest] = _by_kind(_why(env.vault.root, f"block:{E.latest_today(env).current_block().id}"), "plan_block")
    assert contest["detail_id"] == contest_row["id"] and contest["chosen_ref"] == f"followup_contest:{probe}"
    lost = {item["ref"]: item for item in contest["alternatives"]}
    assert lost[OFFER]["lost_by"] == "not_drawn" and 0.0 < lost[OFFER]["p"] < 1.0
    assert 0.0 < contest["facts"]["propensity"] < 1.0
    assert contest["facts"]["superseding_offer_block"] == offer_block
    assert contest["facts"]["superseding_offer_decision"] == offer_decision
    assert contest["facts"]["forced"] == [probe] and contest["facts"]["workflows"] == ["fw_test"]

    [replaced] = _by_kind(_why(env.vault.root, f"offer:{offer_decision}"), "offer_withdrawn")
    assert (replaced["status"], replaced["rule"]) == ("withdrawn", "superseded_by_decision")
    assert replaced["chosen_ref"] == contest_row["id"] == replaced["facts"]["superseded_by"]
    assert [item["ref"] for item in replaced["alternatives"]] == [probe]
    [drawn] = _by_kind(_why(env.vault.root, f"block:{offer_block}"), "plan_block")
    assert replaced["parent_id"] == drawn["id"]
    # Never the switch-off path's withdrawal.
    assert [record["rule"] for record in _all_records(env, "offer_withdrawn")] == ["superseded_by_decision"]


# -- the restraint gate: plan_interrupt (B2's open item) -------------------------------------------------------------


@pytest.mark.parametrize("p_yes,status,chosen", [(0.0, "deferred", "continue_current"), (1.0, "chosen", "insert_now")])
def test_the_restraint_records_what_it_let_in_or_made_wait_with_its_components(tmp_path, p_yes, status, chosen):
    runtime = fake_runtime(decider=FakeDecider(choice=first_option, p_yes=p_yes),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = _followup_env(tmp_path, runtime, toml=DECIDER_ONLY)
    advance(env, serve=True)
    (row,) = rows(env, "plan_interrupt")
    assert row["chosen_ref"] == chosen
    payload = _why(env.vault.root, "item:pi_diag_mid")
    [interrupt] = _by_kind(payload, "plan_interrupt")
    assert (interrupt["status"], interrupt["chosen_ref"]) == (status, chosen)
    assert interrupt["detail_id"] == row["id"] and interrupt["subject_id"] == "pi_diag_mid"
    assert interrupt["decided_by"] == "mixture" and interrupt["rule"]
    assert interrupt["facts"]["block"] == row["detail_json"]["block_id"]
    assert interrupt["facts"]["trigger_attempt"] == _latest_attempt(env)
    assert {item["lost_by"] for item in interrupt["alternatives"]} == {"not_drawn"}
    answers = {record["facts"]["component"]: record for record in _by_kind(payload, "model_answer")
               if record["parent_id"] == interrupt["id"]}
    assert answers["decider"]["status"] == "chosen" and answers["decider"]["decided_by"] == "router_decider"


def test_a_refused_follow_up_is_recorded_with_the_constraint_that_refused_it(tmp_path):
    from learnloop.substrate.activities import reserve_surface, resolve_legacy_item
    from learnloop.vault.loader import load_vault

    runtime = fake_runtime(decider=FakeDecider(choice=first_option, p_yes=1.0),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = _followup_env(tmp_path, runtime, toml=DECIDER_ONLY)
    vault = load_vault(env.vault.root)
    resolved = resolve_legacy_item(vault, env.repository, vault.practice_items["pi_diag_mid"], purpose="assessment")
    reserve_surface(env.repository, surface_id=resolved.surface_id, purpose="assessment")
    advance(env, serve=True)
    [interrupt] = _by_kind(_why(env.vault.root, "item:pi_diag_mid"), "plan_interrupt")
    assert (interrupt["status"], interrupt["chosen_ref"], interrupt["decided_by"]) == ("refused", "decline", "refused")
    assert interrupt["rule"] == interrupt["facts"]["refusals"][0]


# -- a boundary step that failed ---------------------------------------------------------------------------------------


@pytest.mark.usefixtures("offerable")
def test_a_failed_check_draw_placement_and_lesson_builder_are_the_boundarys_children(tmp_path, monkeypatch, caplog):
    """Fail-first: before B3 each was a WARNING line and nothing else."""

    from learnloop.router_objective import checks

    def boom(*_args, **_kwargs):
        raise RuntimeError(SECRET)

    monkeypatch.setattr(checks, "draw_day", boom)
    monkeypatch.setattr(E, "_checks_to_place", boom)
    env = _ih2_env(tmp_path)
    env.policy = replace(env.policy, lesson_offer=boom)
    for _ in range(6):
        _record, step = advance(env, serve=True)
        if _all_records(env, "lesson_offer_build"):
            break
        env.clock.advance(2)
        from tests.daily_plan_fakes import record_attempt

        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
    assert step["kind"] == "item"  # the plan served regardless
    [builder] = _all_records(env, "lesson_offer_build")
    payload = _why(env.vault.root, builder["id"])
    [block] = [record for record in _by_kind(payload, "plan_block") if record["id"] == builder["parent_id"]]
    failures = {(record["kind"], record["rule"]): record for record in payload["records"]
                if record["parent_id"] == block["id"] and record["status"] == "failed"}
    assert set(failures) == {("lesson_offer_build", "builder_error"), ("randomized_check", "draw_error"),
                             ("randomized_check", "place_error")}
    for record in failures.values():
        assert record["error_type"] == "RuntimeError" and record["subject_id"] == block["subject_id"]
        assert record["error_where"].startswith("tests.test_forced_withdrawal_records:boom:")
    assert SECRET not in json.dumps(payload)


def test_the_days_check_block_writes_its_own_plan_block_record(tmp_path, offerable):
    from tests.test_te3b_offers import TAG as TE3B_TAG
    from tests.test_te3b_offers import _first_decision

    env = mixture_env(tmp_path, fake_runtime(), version=TE3B_TAG)
    _first_decision(env)
    checks = [row for row in rows(env) if row["detail_json"].get("source") == "ro5_randomized_check"]
    assert checks, "the day's check block was placed"
    payload = _why(env.vault.root, f"block:{_block_of(env, checks[0])}")
    [record] = _by_kind(payload, "plan_block")
    assert (record["decided_by"], record["rule"], record["status"]) == ("rules", "ro5_randomized_check", "chosen")
    assert record["detail_id"] == checks[0]["id"] and record["facts"]["checks"]


def _block_of(env, row: dict[str, Any]) -> str:
    with env.repository.connection() as connection:
        return str(connection.execute("SELECT id FROM attention_blocks WHERE decision_ref = ?",
                                      (row["id"],)).fetchone()[0])


# -- AD unavailable: the incumbent decided -------------------------------------------------------------------------


def _ad_env(tmp_path):
    from tests.ad23_fakes import ad23_vault, env_for, intent_gated
    from tests.test_ad23_inversion import HARD, ITEMS, ROUTERS

    paths = ad23_vault(tmp_path, items=ITEMS, features={"pi_h": HARD}, config=ROUTERS["staged"])
    env, clock = env_for(paths, items=ITEMS)
    return paths, intent_gated(env), clock


def test_a_slot_whose_plan_facts_fail_records_the_incumbents_fallback_with_no_text(tmp_path):
    from learnloop.daily_plan.engine import build_plan
    from tests.ad23_fakes import cold_followup

    paths, env, clock = _ad_env(tmp_path)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    cold_followup(paths, "pi_e1", clock=clock, context_json='{"note": "' + SECRET + ' unterminated')
    _record, step = advance(env, serve=True)
    assert step.get("practice_item_id") == "pi_h"
    # ``why item:`` would also run today's scheduler explanation, which reads the malformed context; the record's own
    # id reads only the records.
    [row] = _all_records(env, "ad_slot")
    [record] = _by_kind(_why(paths.root, row["id"]), "ad_slot")
    assert record["subject_kind"] == "item" and record["subject_id"] == "pi_h"
    assert (record["status"], record["decided_by"], record["rule"]) == ("fallback", "incumbent", "incumbent_facts_failed")
    assert record["facts"]["phase"] == "facts" and record["facts"]["where"] == "slot" and record["error_type"]


def test_a_guard_denial_is_recorded_beside_the_jsonl_log_the_report_still_reads(tmp_path, monkeypatch):
    from learnloop.adaptive_difficulty import denial_log
    from learnloop.adaptive_difficulty import operation as O
    from learnloop.daily_plan import ad_slot
    from learnloop.daily_plan.engine import build_plan

    paths, env, _clock = _ad_env(tmp_path)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")

    def open_slot(vault, repository, *, slot_item_id):
        try:
            with O.ad_operation(vault, repository) as _op, repository.connection() as connection:
                connection.execute("SELECT learner_answer_md FROM practice_attempts").fetchall()
        except Exception:  # noqa: BLE001 - the guard refused, as ad_slot's phase would see it
            pass
        raise ad_slot.AdUnavailable("guard_denied")

    monkeypatch.setattr(ad_slot, "open_slot", open_slot)
    _record, step = advance(env, serve=True)
    assert step.get("practice_item_id") == "pi_h"  # the incumbent served
    [record] = _by_kind(_why(paths.root, "item:pi_h"), "ad_slot")
    assert (record["rule"], record["facts"]["phase"]) == ("guard_denied", "view")
    assert {"verb": "read", "table": "practice_attempts"}.items() <= record["facts"]["denials"][0].items()
    assert record["facts"]["denials_n"] >= 1
    # The JSONL log stays: ``ad report`` counts it and the upgrade archives it.
    assert denial_log.denial_count(paths.sqlite_path) >= 1


# -- a cold check the serve could not take cold ------------------------------------------------------------------------


@pytest.mark.parametrize("verdict,status", [("serve_as_ordinary", "fallback"), ("defer_until", "excluded")])
def test_a_cold_check_served_as_practice_or_displaced_leaves_a_record(tmp_path, monkeypatch, verdict, status):
    from learnloop import serve_eligibility as se
    from learnloop.scheduling import scheduler

    env = mixture_env(tmp_path, fake_runtime())
    record, _step = advance(env, serve=False)
    target = record.current_block().items[0].practice_item_id
    decision = se.EligibilityDecision(request="serve", verdict=verdict, reason=se.COLD_CHECK_ROUTINE_DISPLAY,
                                      practice_item_id=target, at=env.now_iso(), task_ids=("task_1",),
                                      message="A plain sentence for the learner.")
    monkeypatch.setattr(E, "_open_cold_check_items", lambda env_: {target})
    monkeypatch.setattr(scheduler, "cold_check_serve_decision",
                        lambda vault, repository, item_id, clock=None: decision if item_id == target else None)
    advance(env, serve=True)
    [entry] = _by_kind(_why(env.vault.root, f"item:{target}"), "serve_eligibility")
    assert (entry["status"], entry["rule"], entry["facts"]["verdict"]) == (status, se.COLD_CHECK_ROUTINE_DISPLAY, verdict)
    assert entry["facts"]["tasks"] == ["task_1"]
    assert "plain sentence" not in json.dumps(entry)


# -- S12: a Today offer published unlogged -----------------------------------------------------------------------------


def test_a_head_mismatch_publishes_the_offer_and_records_both_heads(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import queue as queue_handler

    from tests.test_router_offer_log import _call, _decisions, _served, _two_due_items

    paths, repository, ctx, session_id = _two_due_items(tmp_path)
    monkeypatch.setattr(queue_handler, "_served_head", lambda dtos: "pi_not_the_head")
    queue = _call(ctx, "get_today_queue", {"sessionId": session_id})
    assert _served(queue), "the offer is published"
    assert _decisions(repository) == []  # unlogged, as before
    payload = _why(paths.root, "latest", "--kind", "today_offer")
    [record] = _by_kind(payload, "today_offer")
    assert (record["status"], record["rule"]) == ("failed", "head_mismatch")
    assert record["facts"]["served_head"] == "pi_not_the_head" and record["facts"]["realized_head"]
    assert record["facts"]["realized_head"] != "pi_not_the_head"
    slates = _by_kind(_why(paths.root, f"slate:{record['subject_id']}"), "slate")
    assert slates and record["parent_id"] == slates[-1]["id"]


# -- no prose -------------------------------------------------------------------------------------------------------------


def test_the_builders_keep_ids_numbers_and_codes_only():
    """Planted text in an id, a refusal's ``why``, an eligibility message or an exception's message never reaches a
    record: ids that aren't codes are hashed, prose is dropped."""

    from types import SimpleNamespace

    from learnloop import serve_eligibility as se
    from learnloop.daily_plan import plan_records as PR
    from learnloop.daily_plan.boundary_records import forced_entry
    from learnloop.router.decisions import OfferHeadMismatch, offer_failure_record

    records = [
        PR.offer_withdrawn(why=SECRET, block_id=SECRET, offer_decision_id="dec_1",
                           forced=[forced_entry(SECRET, origin=SECRET, workflow={"id": SECRET,
                                                                                 "source_attempt_id": "att_1"})]),
        PR.ad_unavailable(phase="view", code=SECRET, subject_kind="item", subject_id=SECRET,
                          denials=[{"verb": "read", "table": "practice_attempts", "why": SECRET, "reader": SECRET}]),
        PR.serve_eligibility(se.EligibilityDecision(request="serve", verdict="defer_until", reason=SECRET,
                                                    practice_item_id=SECRET, at="2026-11-10T00:00:00Z",
                                                    message=SECRET), block_id="b1", displaced=True),
        PR.step_failure(PR.RANDOMIZED_CHECK, PR.CHECK_DRAW_ERROR, RuntimeError(SECRET)),
        *PR.plan_interrupt(outcome=SimpleNamespace(chosen_ref="decline", propensity=1.0, wait_feasible=True,
                                                   record={"decided_by": "refused", "why": SECRET},
                                                   refused={"reasons": [{"constraint_key": "hard_x",
                                                                         "reason": SECRET}]}),
                           item_id=SECRET, block_id="b1", plan_id="p1", detail_id="d1"),
        offer_failure_record(OfferHeadMismatch(SECRET, realized_head=SECRET, served_head="pi_a", slate_id="s1"),
                             slate_id="s1", surface="desktop_queue"),
        offer_failure_record(ValueError(SECRET), slate_id=SECRET, surface=SECRET),
    ]
    for record in records:
        assert provenance.check_no_prose(record) == [], record.kind
        assert SECRET not in json.dumps(record.as_dict()), record.kind
