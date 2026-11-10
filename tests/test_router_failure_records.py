"""Refactor B2 (ADR-017, strategy §3.6 case 1): a router failure leaves a decision record, read back through ``why``.

Before B2 each of these was silent:

* **a chooser crash** became ``<error: Type>`` with the chooser's record, its mix and both models' answers dropped
  and no log line (the map's S1). Now: ``plan_block``, ``fallback``, ``chooser_error``, the exception's type and
  ``module:function:line`` (never its message), and a ``model_answer`` per component, ``discarded``;
* **a component timeout** became a synthetic timeout inside the router's ledger only (S2). Now: a ``model_answer``
  with ``timeout`` and the configured waits;
* **a late answer** (the Nov 7 case) left a receipt nothing pointed at. Now ``why`` lists it under ``discarded``;
* **a prefetched decision** named only one trace. Now its record names the serving trace and the prefetch's, and
  ``why`` reads the calls of both.

Every model is a fake (``tests/router_model_fakes.py``); every assertion reads the records back through
``learnloop why --json`` or ``provenance.read``.
"""

from __future__ import annotations

import json
import re
import threading
import time
from typing import Any

import pytest
from typer.testing import CliRunner

from learnloop import provenance
from learnloop.algorithm_versions import ROUTER_OBJECTIVE_ALGORITHM_VERSION
from learnloop.daily_plan import boundary_records
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.daily_plan.policy import policy_for

from tests.router_mixture_helpers import B, mixture_env, rows
from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime
from tests.test_ro4_objective_serving import policy_answer

TAG = ROUTER_OBJECTIVE_ALGORITHM_VERSION
SECRET = "the learner wrote about eigenvalues here"


def _why(env, target: str) -> dict[str, Any]:
    from learnloop.cli import app

    result = CliRunner().invoke(app, ["why", target, "--json", "--vault", str(env.vault.root)])
    assert result.exit_code == 0, result.output
    assert SECRET not in result.output
    return json.loads(result.output)


def _by_kind(payload: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return [record for record in payload["records"] if record["kind"] == kind]


def _answers(payload: dict[str, Any], block: dict[str, Any]) -> dict[str, dict[str, Any]]:
    answers = {record["facts"]["component"]: record for record in _by_kind(payload, "model_answer")
               if record["parent_id"] == block["id"]}
    for record in answers.values():
        assert record["trace_id"] == block["trace_id"] and record["subject_id"] == block["subject_id"]
    return answers


def _wait_for(predicate, seconds: float = 10.0) -> None:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError("timed out waiting")


# -- a chooser crash (S1) ---------------------------------------------------------------------------


@pytest.mark.parametrize(("version", "draw"), [(B, "learnloop.router.mixture.draw"),
                                               (TAG, "learnloop.router_objective.mix.draw")])
def test_a_chooser_crash_writes_a_fallback_record_with_the_error_and_each_models_answer(tmp_path, monkeypatch,
                                                                                        version, draw):
    """Fail-first: before B2 the crash left no record at all, and its models' answers were dropped."""

    decider, llm = FakeDecider(), FakeLLM(answer=policy_answer if version == TAG else None)
    env = mixture_env(tmp_path, fake_runtime(decider=decider, llm=llm), version=version)

    def exploding(*_args, **_kwargs):
        raise RuntimeError(SECRET)

    monkeypatch.setattr(draw, exploding)
    with provenance.trace_scope("TRACE_CRASH"):
        build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
        record, step = advance(env, serve=True)
    assert step is not None and step["kind"] == "item"  # the rule served: the crash changed nothing learner-visible
    payload = _why(env, "TRACE_CRASH")
    blocks = _by_kind(payload, "plan_block")
    assert blocks, "a crashed decision leaves a plan_block record"
    block = blocks[0]
    assert (block["status"], block["rule"], block["decided_by"]) == ("fallback", "chooser_error", "lane_quota")
    assert block["error_type"] == "RuntimeError"
    assert re.fullmatch(r"tests\.test_router_failure_records:exploding:\d+", block["error_where"])
    assert block["subject_kind"] == "block" and block["detail_table"] == "router_decisions"
    assert block["chosen_ref"] == record.blocks[0].chosen["candidate_id"]
    assert block["facts"]["timeout_s"] == 40 and block["facts"]["boundary_key"]
    assert block["facts"]["prefetch_trace"] == "TRACE_CRASH"
    answers = _answers(payload, block)
    expected = {"decider", "llm"} | ({"numeric"} if version == TAG else set())
    assert set(answers) == expected
    for name, answer in answers.items():
        assert answer["status"] == "discarded" and answer["rule"] == "answered", name
        assert answer["facts"]["discarded_by"] == "chooser_error"
    assert answers["llm"]["decided_by"] == "router_llm" and answers["llm"]["versions"]["model"] == "fake-router-llm"
    assert answers["decider"]["decided_by"] == "router_decider"
    # The router's own ledger row says the same fallback (unchanged by B2).
    assert rows(env)[0]["detail_json"]["fallback_reason"] == "chooser_error"


def test_the_crash_is_logged_with_its_trace_and_never_its_message(tmp_path, monkeypatch, caplog):
    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM(answer=policy_answer)), version=TAG)

    def exploding(*_args, **_kwargs):
        raise RuntimeError(SECRET)

    monkeypatch.setattr("learnloop.router_objective.mix.draw", exploding)
    with caplog.at_level("WARNING", logger="learnloop.daily_plan.engine"), provenance.trace_scope("TRACE_LOG"):
        build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
        advance(env, serve=True)
    warnings = [r.getMessage() for r in caplog.records if r.levelname == "WARNING" and "chooser failed" in r.getMessage()]
    assert warnings and all("TRACE_LOG" in line and "RuntimeError" in line and SECRET not in line for line in warnings)


# -- a component timeout (S2) and its late answer --------------------------------------------------


def _timed_out_env(tmp_path, gate: threading.Event):
    llm = FakeLLM(answer=policy_answer, gate=gate)
    runtime = fake_runtime(decider=FakeDecider(), llm=llm, inline=False)
    env = mixture_env(tmp_path, runtime, version=TAG,
                      toml="[router]\ntimeout_seconds = 0.3\nprefetch_timeout_seconds = 0.6\n")
    return env, llm


def test_a_component_timeout_writes_a_model_answer_with_the_configured_wait(tmp_path):
    """Fail-first: before B2 a timed-out component had no record; only the router's ledger said ``timeout``."""

    gate = threading.Event()
    try:
        env, _llm = _timed_out_env(tmp_path, gate)
        with provenance.trace_scope("TRACE_TIMEOUT"):
            build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
            advance(env, serve=True)
        payload = _why(env, "TRACE_TIMEOUT")
        block = _by_kind(payload, "plan_block")[0]
        # The numeric policy waits on the LLM's forecasts, so it may be out at the serve's wait too.
        assert block["status"] == "chosen" and block["facts"]["mix_fallback"] in {"llm", "both"}
        assert block["facts"]["timeout_s"] == 0.3 and block["facts"]["prefetch_timeout_s"] == 0.6
        assert block["facts"]["may_defer"] is False and block["facts"]["waited_ms"] >= 0
        answers = _answers(payload, block)
        llm = answers["llm"]
        assert (llm["status"], llm["rule"], llm["decided_by"]) == ("timeout", "timeout", "router_llm")
        assert llm["facts"]["timeout_s"] == 0.3 and llm["facts"]["prefetch_timeout_s"] == 0.6
        assert answers["decider"]["status"] == "chosen" and answers["decider"]["rule"] == "answered"
        assert answers["staged"]["status"] == "chosen" and answers["staged"]["chosen_ref"]
        assert set(answers) == {"decider", "llm", "numeric", "staged"}
        # The support, each option's probability and why it lost.
        assert block["alternatives"] and all(alt["lost_by"] for alt in block["alternatives"])
        assert all("p" in alt for alt in block["alternatives"] if alt["lost_by"] == "not_drawn")
    finally:
        gate.set()


def test_a_late_answer_is_listed_as_discarded(tmp_path):
    """Fail-first: before B2 nothing compared a receipt's finish with its decision; ``why`` had no ``discarded``."""

    gate = threading.Event()
    try:
        env, llm = _timed_out_env(tmp_path, gate)
        with provenance.trace_scope("TRACE_LATE"):
            build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
            advance(env, serve=True)
        before = _why(env, "TRACE_LATE")
        block = _by_kind(before, "plan_block")[0]
        out = [late for late in before["discarded"] if late["record_id"] == block["id"]]
        assert out and all(late["late_ms"] is None for late in out)  # still out when asked
    finally:
        gate.set()

    def finished() -> bool:
        with env.repository.connection() as connection:
            return connection.execute(
                "SELECT COUNT(*) FROM model_call_receipts WHERE trace_id = 'TRACE_LATE' AND purpose LIKE 'router%' "
                "AND owner_id = ? AND finished_at IS NULL", (block["facts"]["boundary_key"],)).fetchone()[0] == 0

    _wait_for(finished)
    payload = _why(env, "TRACE_LATE")
    late = [entry for entry in payload["discarded"] if entry["record_id"] == block["id"]]
    assert late and all(entry["late_ms"] > 0 and entry["trace_id"] == "TRACE_LATE" for entry in late)
    assert {entry["model"] for entry in late} == {"fake-router-llm"}
    called = {call["id"] for call in payload["model_calls"]}
    assert {entry["call_id"] for entry in late} <= called
    from learnloop.cli import app

    text = CliRunner().invoke(app, ["why", "TRACE_LATE", "--vault", str(env.vault.root)]).output
    assert "Discarded:" in text and "s late" in text


# -- a prefetched decision names both traces ---------------------------------------------------------


def test_a_prefetched_decision_names_the_prefetching_and_the_serving_trace(tmp_path):
    gate = threading.Event()
    runtime = fake_runtime(decider=FakeDecider(gate=gate), llm=FakeLLM(answer=policy_answer, gate=gate), inline=False)
    env = mixture_env(tmp_path, runtime, version=TAG, serve=False)
    try:
        with provenance.trace_scope("TRACE_PREFETCH"):
            build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
            _record, step = advance(env, serve=False)  # Today's open: the models are asked, nothing is decided
        assert step is None or step.get("kind") != "item"
        with env.repository.connection() as connection:
            assert provenance.read(connection, "TRACE_PREFETCH") == []
    finally:
        gate.set()
    env.policy = policy_for(env.vault, env.repository, session_id=env.session_id, clock=env.clock, runtime=runtime,
                            serve=True)
    with provenance.trace_scope("TRACE_SERVE"):
        advance(env, serve=True)
    payload = _why(env, "TRACE_SERVE")
    block = _by_kind(payload, "plan_block")[0]
    assert block["trace_id"] == "TRACE_SERVE" and block["facts"]["prefetch_trace"] == "TRACE_PREFETCH"
    assert payload["traces"] == ["TRACE_SERVE"] and payload["prefetch_traces"] == ["TRACE_PREFETCH"]
    prefetched = [call for call in payload["model_calls"] if call["trace_id"] == "TRACE_PREFETCH"]
    assert {call["model"] for call in prefetched} >= {"fake-router-llm"}


# -- calls no decision names (S4, S5) ----------------------------------------------------------------------


def test_a_prefetch_whose_key_changed_before_the_serve_leaves_unclaimed_calls(tmp_path):
    """The map's S4 (a key that changes before serving) and S5 (an evicted prefetch) both leave router calls that no
    decision names. ``why`` on the prefetch's trace lists them, derived at read time."""

    from tests.daily_plan_fakes import record_attempt

    runtime = fake_runtime(decider=FakeDecider(), llm=FakeLLM(answer=policy_answer), inline=False)
    env = mixture_env(tmp_path, runtime, version=TAG, serve=False)
    gate = threading.Event()
    runtime.models.llm.gate = gate
    try:
        with provenance.trace_scope("TRACE_ORPHAN"):
            build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
            advance(env, serve=False)
    finally:
        gate.set()
    _wait_for(lambda: not _open_calls(env, "TRACE_ORPHAN"))
    item = next(iter(env.vault.practice_items.values()))
    env.clock.advance(1)
    record_attempt(env.repository, item.id, item.learning_object_id, env.clock.now())  # the key's ``as_of`` moves
    env.policy = policy_for(env.vault, env.repository, session_id=env.session_id, clock=env.clock, runtime=runtime,
                            serve=True)
    with provenance.trace_scope("TRACE_SERVED"):
        advance(env, serve=True)
    served = _by_kind(_why(env, "TRACE_SERVED"), "plan_block")[0]
    orphan = _why(env, "TRACE_ORPHAN")
    assert orphan["records"] == [] and orphan["traces"] == ["TRACE_ORPHAN"] and orphan["model_calls"]
    assert orphan["unclaimed"], "the first key's calls are named by no decision"
    assert {call["boundary_key"] for call in orphan["unclaimed"]} != {served["facts"]["boundary_key"]}
    assert all(call["trace_id"] == "TRACE_ORPHAN" for call in orphan["unclaimed"])
    assert _why(env, "TRACE_SERVED")["unclaimed"] == []


def _open_calls(env, trace: str) -> int:
    with env.repository.connection() as connection:
        return connection.execute("SELECT COUNT(*) FROM model_call_receipts WHERE trace_id = ? AND finished_at IS NULL",
                                  (trace,)).fetchone()[0]


def test_the_store_names_the_routers_receipt_owner():
    from learnloop.daily_plan.router_runtime import RECEIPT_OWNER
    from learnloop.db.stores.provenance import ROUTER_OWNER

    assert ROUTER_OWNER == RECEIPT_OWNER


# -- what a record may hold ------------------------------------------------------------------------------


def test_records_hold_codes_only_and_an_id_that_is_not_a_code_is_hashed():
    assert boundary_records.ref("review:abc123") == "review:abc123"
    hashed = boundary_records.ref("an item id with spaces")
    assert hashed.startswith("sha256:") and provenance.is_code(hashed)
    assert boundary_records._error_type("TimeoutError: the model said " + SECRET) == "TimeoutError"
    assert boundary_records._error_type("card: KeyError") == "KeyError"
    assert boundary_records._error_type("no answer within the budget") is None
    assert boundary_records._where("pkg.mod:<lambda>:12") == "pkg.mod:_lambda_:12"


def test_a_record_that_cannot_be_built_never_blocks_the_block(tmp_path, monkeypatch, caplog):
    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM(answer=policy_answer)), version=TAG)

    def broken(*_args, **_kwargs):
        raise ValueError(SECRET)

    monkeypatch.setattr(boundary_records, "plan_block_records", broken)
    with provenance.trace_scope("TRACE_BROKEN"):
        build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
        _record, step = advance(env, serve=True)
    assert step is not None and step["kind"] == "item" and rows(env)
    with env.repository.connection() as connection:
        assert provenance.read(connection, "TRACE_BROKEN") == []
    assert not any(SECRET in r.getMessage() for r in caplog.records)
