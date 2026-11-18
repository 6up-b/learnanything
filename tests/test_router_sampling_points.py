"""Where a block decision reads what the router's background threads publish.

The objective's job publishes the LLM's card and request from its own thread, and a carried valuation of an earlier
decision lands from another; either can land while a serve is deciding (the card build after the serve's wait ended,
a carry while the trace is assembled). The decision reads each at one fixed point, and its record says what had landed
by then:

* the card (the trace's learner statements): right after the mix's draw;
* the carried valuations (the trace's ``carried_for``): inside the trace's assembly, after its rows;
* the LLM request's question set (the router's record and the decision record): after the trace.

Each test holds the deciding thread at one point with a barrier while a worker thread publishes, and asserts what was
recorded. The expected values are those the decision recorded before its choice was made a pure function: the same
schedules, run against that code, gave these results (an earlier read of any of the three records less).
"""

from __future__ import annotations

import json
import threading
import time
from typing import Any

import pytest

from learnloop import provenance
from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.daily_plan import objective_card
from learnloop.daily_plan import objective_chooser as OC
from learnloop.daily_plan import objective_job as J
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.router_objective import mix, tail_serve
from learnloop.router_objective import trace_assembly as T

from tests.helpers import RANDOMIZED_CHECKS_OFF
from tests.router_mixture_helpers import mixture_env
from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime
from tests.ro4_objective_serving_helpers import policy_answer

TAG = LATEST_ALGORITHM_VERSION
TRACE = "TRACE_SAMPLING"
#: The serve waits a second, so a card build held past it is still out when the serve decides.
TIMED = "[router]\ntimeout_seconds = 1.0\nprefetch_timeout_seconds = 30.0\n\n" + RANDOMIZED_CHECKS_OFF
QUESTION_SET = "router_objective_v1"
EARLIER = "01EARLIERDECISION000000000"


def _hold_at(monkeypatch, point: str, publish) -> None:
    """Run ``publish`` once, on the deciding thread, at ``point``: right after the mix's draw, at the start of the
    trace's common part (its rows), or while the router's record summarizes the models' payloads (after the trace)."""

    fired = threading.Event()

    def once() -> None:
        if not fired.is_set():
            fired.set()
            publish()

    if point == "draw":
        real_draw = mix.draw

        def draw(*args, **kwargs):
            out = real_draw(*args, **kwargs)
            once()
            return out

        monkeypatch.setattr(mix, "draw", draw)
    elif point == "rows":
        real_trace = T.decision_trace

        def decision_trace(*args, **kwargs):
            once()
            return real_trace(*args, **kwargs)

        monkeypatch.setattr(T, "decision_trace", decision_trace)
    else:
        assert point == "payloads"
        real_payloads = OC._payloads

        def payloads(*args, **kwargs):
            once()
            return real_payloads(*args, **kwargs)

        monkeypatch.setattr(OC, "_payloads", payloads)


def _decide(env) -> None:
    with provenance.trace_scope(TRACE):
        build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
        advance(env, serve=True)


def _recorded(env) -> dict[str, Any]:
    with env.repository.connection() as connection:
        row = connection.execute("SELECT question_set_version FROM router_decisions WHERE decision_kind = 'plan_block' "
                                 "ORDER BY created_at, id LIMIT 1").fetchone()
        trace = json.loads(connection.execute("SELECT trace_json FROM router_objective_traces ORDER BY created_at, id "
                                              "LIMIT 1").fetchone()[0])
        [record] = [record for record in provenance.read(connection, TRACE) if record.kind == "plan_block"]
    return {"router": row[0], "record": record.versions.get("question_set_version"),
            "statements": "learner_statements" in trace,
            "carried_for": [entry["decision_id"] for entry in trace.get("carried_for") or ()]}


def _join_jobs() -> None:
    for thread in list(threading.enumerate()):
        if thread.name.startswith(("learnloop-router-", "learnloop-objective-")):
            thread.join(60)


def _card_published_at(tmp_path, monkeypatch, point: str) -> dict[str, Any]:
    """The job's card build is held until the deciding thread reaches ``point``, then finishes there: the card (with a
    learner statement) and the LLM's request are on the job's material before the deciding thread goes on."""

    release, published = threading.Event(), threading.Event()
    real_card = objective_card.decision_card

    def held_card(*args, **kwargs):
        release.wait(30)
        card = dict(real_card(*args, **kwargs))
        card["statements"] = [{"kind": "a statement on record"}]
        return card

    def answer(request):
        published.set()  # the job asks the LLM only once the card and the request are on its material
        return policy_answer(request)

    def publish() -> None:
        release.set()
        assert published.wait(30), "the card build did not publish"

    monkeypatch.setattr(objective_card, "decision_card", held_card)
    _hold_at(monkeypatch, point, publish)
    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM(answer=answer), inline=False),
                      version=TAG, toml=TIMED)
    try:
        _decide(env)
    finally:
        release.set()
        _join_jobs()
    return _recorded(env)


@pytest.mark.parametrize(("point", "statements"), [("draw", True), ("rows", False)])
def test_the_trace_records_the_card_that_had_landed_by_the_draw(tmp_path, monkeypatch, point, statements):
    assert _card_published_at(tmp_path, monkeypatch, point)["statements"] is statements


@pytest.mark.parametrize(("point", "question_set"), [("draw", QUESTION_SET), ("rows", QUESTION_SET),
                                                     ("payloads", None)])
def test_the_records_name_the_question_set_that_had_landed_by_the_end_of_the_trace(tmp_path, monkeypatch, point,
                                                                                   question_set):
    recorded = _card_published_at(tmp_path, monkeypatch, point)
    assert (recorded["router"], recorded["record"]) == (question_set, question_set)


@pytest.mark.parametrize(("point", "carried"), [("rows", [EARLIER]), ("payloads", [])])
def test_the_trace_records_a_carry_that_landed_while_its_rows_were_built(tmp_path, monkeypatch, point, carried):
    """An earlier decision of the same plan had deferred its carried valuation; a worker registers and runs it (valued)
    while the deciding thread is held."""

    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM(answer=policy_answer)), version=TAG,
                      toml=RANDOMIZED_CHECKS_OFF)
    path = env.repository.sqlite_path

    def compute(**_kwargs):
        return {"previous": {"q_status": "valued", "q": {"blk": 0.5}, "draws": 1, "elapsed_ms": 0}}

    def publish() -> None:
        with env.repository.connection() as connection:
            plan_id = connection.execute("SELECT id FROM daily_plans ORDER BY created_at DESC, id DESC LIMIT 1"
                                         ).fetchone()[0]
        numeric = J.NumericPolicy(status="answered", carried=compute,
                                  residual={"previous": {"q_status": tail_serve.NOT_BEFORE_THE_SERVE}})

        def worker() -> None:
            J.defer_carry(numeric, object(), EARLIER, runtime=env.policy.chooser.runtime, sqlite_path=path,
                          config=env.vault.config, session_id=env.session_id, plan_id=plan_id)
            J.drain_carry(path, deadline=time.monotonic() + 60)

        thread = threading.Thread(target=worker, name="carry-worker")
        thread.start()
        thread.join(30)
        assert not thread.is_alive()

    _hold_at(monkeypatch, point, publish)
    try:
        _decide(env)
        assert _recorded(env)["carried_for"] == carried
    finally:
        J.stop_carries(path)
