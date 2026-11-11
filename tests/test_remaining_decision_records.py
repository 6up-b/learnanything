"""Refactor B8 (ADR-017, "B8: boundaries with no record, and why not"): the remaining boundaries that had no stored
answer now leave a decision record, read back through ``learnloop why --json`` or ``provenance.read``.

Each was silent before B8:

* **a plan decision logger that raised** (S13's other half, ``engine._log_plan_decision`` and ``_log_interrupt``):
  a warning line, and a block with no ``router_decisions`` row. Now ``router_decision_row``/``failed``/
  ``logger_error`` on the block, with the exception's class and frame;
* **a shared daily cap's refusal** (``SharedDailyEnvelope.reserve``: the source service, hints, figures, the Reader's
  follow-ups, reading paths, deliverables, ...): each caller turned it into its own status, and the exception named
  no rule or numbers. Now ``spend_admission``/``envelope_cap`` with the cap, the day's total and the estimate;
* **a lesson closed with ``budget``**: the gate's refusal (which request, its estimate, the limit) was kept nowhere.
  Now ``spend_admission``/``lesson_envelope``;
* **the curriculum path's daily re-judgment** that judged nothing (unavailable, switched off, coalesced): only the
  sidecar's memory and a log line. Now ``curriculum_path_refresh``;
* **an AD commission's job that generated nothing**: "commission no longer open" whether it closed, AD's view was
  unavailable, or AD's guard refused a read. Now ``ad_commission_skip`` names which;
* **a figure prediction's gap reading stopped by the figure gate**: the job row kept prose only. Now the gate's
  ``figure_admission`` record, in the job's trace;
* **the FSRS review**: the grade's record named the rating only; the elapsed days, the state before and after, the
  interval and the due time were overwritten by the next review. Now ``grade.facts.fsrs``.

Every model is a fake; nothing here leaves the machine.
"""

from __future__ import annotations

import json
import re
from contextlib import contextmanager
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from typer.testing import CliRunner

from learnloop import provenance, refusal_records
from learnloop.ai.spend import SpendLimitExceeded
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from tests.helpers import create_basic_vault

SECRET = "the learner wrote xylophone-planted-secret"


def _why(root: Path, target: str, *, kind: str | None = None) -> dict[str, Any]:
    from learnloop.cli import app

    args = ["why", target, "--json", "--vault", str(root), *(["--kind", kind] if kind else [])]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "xylophone" not in result.output
    return json.loads(result.output)


def _by_kind(payload: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return [record for record in payload["records"] if record["kind"] == kind]


def _all(path: Path, kind: str) -> list[provenance.DecisionRecord]:
    with connect(path, read_only=True) as connection:
        rows = connection.execute("SELECT trace_id FROM decision_records WHERE kind = ?", (kind,)).fetchall()
        return [record for trace in sorted({row[0] for row in rows})
                for record in provenance.read(connection, trace, kind=kind)]


# -- a plan decision logger that raised (S13's other half) ----------------------------------------------------------


def test_a_plan_logger_that_raises_leaves_a_record_on_the_block_and_serves_the_same(tmp_path, monkeypatch):
    """Fail-first: before B8 the failure was a warning line and the block simply had no ledger row."""

    from learnloop.daily_plan import engine
    from learnloop.daily_plan.engine import advance, build_plan
    from tests.router_mixture_helpers import mixture_env
    from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime

    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM()))

    def exploding(_connection, _decision):
        raise RuntimeError(SECRET)

    monkeypatch.setattr(engine, "_PLAN_DECISION_LOGGERS", [exploding])
    with provenance.trace_scope("TRACE_LOGGER"):
        record = build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
        _record, step = advance(env, serve=True)
    # The plan serves on, as it did before B8 (the draw's seed follows the decision's id, so which item is drawn
    # varies run to run; the P-draw shows the record changes no draw).
    assert step is not None and step["kind"] == "item"
    block_id = record.blocks[0].id
    failures = _by_kind(_why(env.vault.root, "TRACE_LOGGER"), refusal_records.ROUTER_DECISION_ROW)
    assert failures, "a logger that raised leaves a record"
    first = failures[0]
    assert (first["status"], first["rule"], first["decided_by"]) == ("failed", "logger_error", "plan_decision_logger")
    assert first["subject_kind"] == "block"
    assert block_id in {record["subject_id"] for record in failures}
    assert first["error_type"] == "RuntimeError"
    assert re.fullmatch(r"tests\.test_remaining_decision_records:exploding:\d+", first["error_where"])
    assert first["facts"]["decision_kind"] == "plan_block" and first["facts"]["applied"] is True
    assert first["facts"]["logger"] == "exploding"
    assert _by_kind(_why(env.vault.root, f"block:{first['subject_id']}"), refusal_records.ROUTER_DECISION_ROW)


def test_a_follow_up_interrupts_logger_that_raises_leaves_a_record(tmp_path, monkeypatch):
    from learnloop.daily_plan.engine import advance
    from tests.router_mixture_helpers import rows
    from tests.router_model_fakes import FakeDecider, fake_runtime, first_option, seed_with_first_uniform
    from tests.router_g4_restraint_helpers import DECIDER_ONLY, PAST_THE_FLOOR, _followup_env

    def exploding(*_args, **_kwargs):
        raise RuntimeError(SECRET)

    monkeypatch.setattr("learnloop.router.plan_log.log_plan_interrupt_decision", exploding)
    runtime = fake_runtime(decider=FakeDecider(choice=first_option, p_yes=1.0),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = _followup_env(tmp_path, runtime, toml=DECIDER_ONLY)
    with provenance.trace_scope("TRACE_INTERRUPT"):
        advance(env, serve=True)
    assert rows(env, "plan_interrupt") == []
    failures = [record for record in _by_kind(_why(env.vault.root, "TRACE_INTERRUPT"),
                                              refusal_records.ROUTER_DECISION_ROW)
                if record["facts"]["decision_kind"] == "plan_interrupt"]
    assert len(failures) == 1
    assert (failures[0]["status"], failures[0]["rule"]) == ("failed", "logger_error")
    assert failures[0]["subject_kind"] == "block" and "logged_ref" not in failures[0]["facts"]


# -- a shared daily cap's refusal -----------------------------------------------------------------------------------


def _envelope(tmp_path, **kwargs):
    from learnloop.source_retrieval.service_spend import SharedDailyEnvelope

    paths = create_basic_vault(tmp_path / "vault")
    vault, repository = load_vault(paths.root), Repository.attach(paths.sqlite_path)
    envelope = SharedDailyEnvelope(vault, repository, day="2026-11-10T00:00:00Z", cap=0.01,
                                   name="hints.max_daily_cost_usd", price_per_million=1.0, **kwargs)
    return paths, repository, envelope


def test_a_shared_daily_caps_refusal_names_its_cap_and_leaves_a_record(tmp_path):
    """Fail-first: before B8 the refusal named no rule or numbers, and no row said the cap refused."""

    paths, _repository, envelope = _envelope(tmp_path)
    with provenance.trace_scope("TRACE_CAP"), pytest.raises(SpendLimitExceeded) as caught:
        envelope.reserve(Decimal("0.5"))
    assert "would pass the $0.0100 cap" in str(caught.value)  # the message is unchanged
    assert (caught.value.rule, caught.value.limit, caught.value.used, caught.value.requested, caught.value.scope) == (
        "envelope_cap", 0.01, 0.0, 0.5, "hints.max_daily_cost_usd")
    [record] = _by_kind(_why(paths.root, "TRACE_CAP"), refusal_records.SPEND_ADMISSION)
    assert (record["status"], record["rule"], record["decided_by"]) == (
        "refused", "envelope_cap", "hints.max_daily_cost_usd")
    assert record["facts"]["limit_usd"] == 0.01 and record["facts"]["request_usd"] == 0.5
    assert record["facts"]["spent_usd"] == 0.0 and record["facts"]["scope"] == "hints.max_daily_cost_usd"
    # An admitted request leaves none.
    envelope.unreserve(envelope.reserve(Decimal("0.001")))
    assert len(_all(paths.sqlite_path, refusal_records.SPEND_ADMISSION)) == 1


def test_ads_envelope_records_no_refusal_since_its_guard_denies_the_table(tmp_path):
    from learnloop.adaptive_difficulty.spend import ad_envelope

    paths = create_basic_vault(tmp_path / "vault")
    vault, repository = load_vault(paths.root), Repository.attach(paths.sqlite_path)
    envelope = ad_envelope(vault, repository)
    assert envelope._record_refusals is False
    _paths, _repository, recording = _envelope(tmp_path / "other")
    assert recording._record_refusals is True


def test_a_cap_record_that_cannot_be_built_still_refuses(tmp_path, monkeypatch, caplog):
    paths, _repository, envelope = _envelope(tmp_path)

    def broken(**_kwargs):
        raise RuntimeError(SECRET)

    monkeypatch.setattr(refusal_records, "envelope_record", broken)
    with caplog.at_level("WARNING"), pytest.raises(SpendLimitExceeded):
        envelope.reserve(Decimal("0.5"))
    assert _all(paths.sqlite_path, refusal_records.SPEND_ADMISSION) == []
    assert all(SECRET not in record.getMessage() for record in caplog.records)


# -- a lesson closed with ``budget`` --------------------------------------------------------------------------------


def test_a_lesson_closed_with_budget_names_the_request_and_the_limit(tmp_path):
    """Fail-first: before B8 the close receipt said ``budget`` and the gate's refusal was kept nowhere."""

    from tests.teacher_te1_review_fixes_helpers import _metered, _turn

    reads = {"message": "Let me read.", "requests": [{"action": "read_source", "refs": ["ext_book/ch_det"]}]}
    paths, repository, fake, lesson_id, cap = _metered(tmp_path, [reads, {"message": "Read it."}], cap_factor=1.5)
    with provenance.trace_scope("TRACE_LESSON"):
        view = _turn(paths, repository, lesson_id, fake)
    assert view["closed"] and view["close_reason"] == "budget"
    [record] = _by_kind(_why(paths.root, "TRACE_LESSON"), refusal_records.SPEND_ADMISSION)
    assert (record["status"], record["decided_by"], record["rule"]) == ("refused", "lesson_envelope",
                                                                        "max_estimated_usd")
    facts = record["facts"]
    assert facts["lesson_id"] == lesson_id and facts["purpose"] == "teacher_turn"
    assert facts["limit_usd"] == pytest.approx(cap, abs=1e-6) and facts["request_usd"] > 0
    assert facts["committed_usd"] + facts["request_usd"] > facts["limit_usd"]


# -- the curriculum path's daily re-judgment ------------------------------------------------------------------------


def test_the_daily_re_judgment_records_what_it_decided_and_nothing_for_none_or_fresh(tmp_path, monkeypatch):
    """Fail-first: before B8 an unavailable or coalesced re-judgment lived only in the sidecar's memory."""

    from learnloop.source_retrieval import deliverable_path as DP

    paths = create_basic_vault(tmp_path / "vault")
    vault, repository = load_vault(paths.root), Repository.attach(paths.sqlite_path)
    outcomes = iter([
        {"status": "unavailable", "reason": "plan_only"},
        {"status": "none"},
        {"status": "fresh", "goal_id": "goal_a", "depth": "working"},
        {"status": "coalesced", "goal_id": "goal_a", "depth": "working", "state_key": "abc123"},
        {"status": "switched_off", "reason": "curriculum.enabled is false"},
    ])
    monkeypatch.setattr(DP, "_refresh_for_plan", lambda *_a, **_k: next(outcomes))
    with provenance.trace_scope("TRACE_REFRESH"):
        returned = [DP.refresh_for_plan(vault, repository) for _ in range(5)]
    assert [item["status"] for item in returned] == ["unavailable", "none", "fresh", "coalesced", "switched_off"]
    records = _by_kind(_why(paths.root, "TRACE_REFRESH"), DP.REFRESH_RECORD)
    assert [(r["status"], r["rule"]) for r in records] == [("refused", "plan_only"), ("deferred", "coalesced"),
                                                           ("excluded", "switched_off")]
    assert records[1]["subject_kind"] == "goal" and records[1]["subject_id"] == "goal_a"
    assert records[1]["facts"] == {"outcome": "coalesced", "goal_id": "goal_a", "depth": "working",
                                   "state_key": "abc123"}
    assert "reason" not in records[2]["facts"]  # a sentence is never kept; the status says it

    def failing(*_a, **_k):
        raise RuntimeError(SECRET)

    monkeypatch.setattr(DP, "_refresh_for_plan", failing)
    with provenance.trace_scope("TRACE_REFRESH_FAIL"), pytest.raises(RuntimeError):
        DP.refresh_for_plan(vault, repository)
    [failed] = _by_kind(_why(paths.root, "TRACE_REFRESH_FAIL"), DP.REFRESH_RECORD)
    assert (failed["status"], failed["error_type"]) == ("failed", "RuntimeError")


# -- an AD commission's job that generated nothing ------------------------------------------------------------------


@pytest.mark.parametrize("staged,rule", [("closed", "commission_closed"), ("unavailable", "view_unavailable"),
                                         ("denied", "guard_denied")])
def test_a_commission_job_that_generated_nothing_says_why(tmp_path, monkeypatch, staged, rule):
    """Fail-first: before B8 all three were "commission no longer open" in the job's result, and nothing else."""

    from learnloop.adaptive_difficulty.operation import GuardDenied
    from learnloop.content.pipeline import jobs

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository.attach(paths.sqlite_path)

    @contextmanager
    def operation(*_args, **_kwargs):
        if staged == "denied":
            raise GuardDenied("planted denial")
        view = SimpleNamespace(available=staged != "unavailable", open_commissions=lambda *_a, **_k: [])
        yield SimpleNamespace(view=view)

    monkeypatch.setattr("learnloop.adaptive_difficulty.generation.contract_on", lambda _config: True)
    monkeypatch.setattr("learnloop.adaptive_difficulty.operation.ad_operation", operation)
    ctx = SimpleNamespace(vault_root=paths.root, repo=repository, clock=None, job={"id": "job_commission_1"},
                          job_id="job_commission_1")
    with provenance.trace_scope("TRACE_COMMISSION"):
        result = jobs._handle_ad_commission(ctx, [], "sel_commission_1")
    assert result == {"generated": 0, "skipped_reason": "commission no longer open"}  # unchanged
    [record] = _by_kind(_why(paths.root, "job:job_commission_1"), jobs.AD_COMMISSION_SKIP)
    assert (record["status"], record["rule"], record["decided_by"]) == ("excluded", rule, "ad_commission_job")
    assert record["facts"]["commission_id"] == "sel_commission_1"
    assert (record["detail_table"], record["detail_id"]) == ("ad_selections", "sel_commission_1")


# -- a figure prediction's gap reading stopped by the figure gate ---------------------------------------------------


def test_the_gap_readings_figure_gate_records_its_refusal_in_the_jobs_trace(tmp_path):
    """Fail-first (B5's open item): the job's gate got no repository, so its refusal wrote no record."""

    from learnloop.diagnosis.text_gaps.jobs import process_next_gap_job
    from tests.figures_scope_redesign_helpers import _Counter, _gap_clients, _gap_job
    from tests.figures_switch_off_helpers import _switch

    paths, repository, _ctx, _found = _gap_job(tmp_path)
    counter = _Counter(lambda: _switch(paths.root, "figures", False), 1)
    outcome = process_next_gap_job(paths.root, repository, owner="t", clients=_gap_clients(counter))
    assert (outcome.state, outcome.error) == ("retry_later", "figures_changed")  # unchanged
    [record] = _all(paths.sqlite_path, refusal_records.FIGURE_ADMISSION)
    assert (record.status, record.rule, record.decided_by) == ("refused", "figures_off", "figures_gate")
    assert record.facts == {"purpose": record.facts["purpose"]} and record.facts["purpose"]


# -- the FSRS review on the grade's record --------------------------------------------------------------------------


def test_the_grade_record_carries_the_fsrs_review_it_applied(tmp_path):
    """Fail-first: before B8 the record named the rating only; elapsed days, the state before and after, the interval
    and the due time were overwritten by the next review and the elapsed time was never stored."""

    from learnloop.attempts import grade_records
    from tests.followup_serve_helpers import CLOCK, BlindRivalClient, live_shape_vault
    from tests.split_live_helpers import submit

    paths, vault, repository = live_shape_vault(tmp_path, task_features=False)
    client = BlindRivalClient()
    first = submit(vault, repository, client, pipeline=False, when=CLOCK.now())
    second = submit(vault, repository, client, pipeline=False, when=CLOCK.now() + timedelta(days=3))
    reviews = []
    for result in (first, second):
        [grade] = _by_kind(_why(paths.root, f"attempt:{result.attempt_id}"), grade_records.GRADE)
        reviews.append(grade["facts"]["fsrs"])
    one, two = reviews
    for review in reviews:
        assert set(review) >= {"applied", "rating", "rating_uncapped", "elapsed_days", "weights", "stability",
                               "difficulty", "interval_days", "interval_factor", "due_at"}
    # The vault's item has history already, so the first review here reads a prior state too.
    if one["applied"]:
        assert one["interval_days"] > 0 and one["due_at"] and one["elapsed_days"] >= 0
    if two["applied"] and one["applied"]:
        assert two["elapsed_days"] == pytest.approx(3.0, abs=1e-3)
        assert two["prior_stability"] == pytest.approx(one["stability"], abs=1e-6)
        assert two["prior_due_at"] == one["due_at"]
    else:
        assert two["skipped"] in {"held", "causal_activity", "ineligible_observation"}
    assert one["rating"] <= one["rating_uncapped"]


def test_an_fsrs_summary_with_a_non_finite_number_keeps_the_grade_record():
    from learnloop.attempts import grade_records

    record = grade_records.grade_record(
        attempt_id="att_1", practice_item_id="pi_1", learning_object_id=None, rubric_score=1, max_points=2,
        correctness=0.5, grader_confidence=None, grading_source="self", grader_mode=None, manual_review_reason=None,
        fsrs={"applied": True, "stability": float("nan"), "elapsed_days": 1.5, "due_at": "2026-11-12T00:00:00Z",
              "note": SECRET},
    )
    assert record.facts["fsrs"] == {"applied": True, "elapsed_days": 1.5, "due_at": "2026-11-12T00:00:00Z"}
    assert provenance.check_no_prose(record) == []


# -- no prose -------------------------------------------------------------------------------------------------------


def test_every_b8_builder_passes_the_prose_check_with_learner_text_planted():
    from learnloop.content.pipeline.jobs import ad_commission_skip_record
    from learnloop.source_retrieval.deliverable_path import refresh_record

    error = RuntimeError(SECRET)
    try:
        raise error
    except RuntimeError as caught:
        error = caught
    records = [
        refusal_records.plan_logger_record(decision_kind="plan_block", block_id=SECRET, plan_id=SECRET,
                                           logger=SECRET, exc=error, logged_ref=SECRET),
        refusal_records.envelope_record(envelope=SECRET, cap_usd=1.0, spent_usd=0.5, request_usd=0.6,
                                        owner_kinds=[SECRET, "hint_writer"]),
        refusal_records.lesson_budget_record(lesson_id=SECRET, exc=SpendLimitExceeded(SECRET, rule="max_calls"),
                                             refusal={"purpose": SECRET, "provider": SECRET, "limit_usd": 1.0}),
        refresh_record({"status": "unavailable", "goal_id": SECRET, "reason": SECRET, "state_key": SECRET}),
        refresh_record(None, error=error),
        ad_commission_skip_record(commission_id=SECRET, job_id=SECRET, rule="guard_denied"),
    ]
    for record in records:
        assert provenance.check_no_prose(record) == [], record
        assert "xylophone" not in json.dumps(record.as_dict())
