"""Router R2b, G7: fallback to the staged rule, flagged on the receipt.

Fail-first (plan §9 R2b, test 3): a model that does not answer in time (a
slow fake LLM; a serving step waits ``router.timeout_seconds``) reaches the
staged rule with ``fallback = llm``: its weight goes to the rule and the
draw keeps its exact propensity.
"""

from __future__ import annotations

import threading

import pytest

from learnloop.ai.decisions import DecisionResponseInvalid
from learnloop.daily_plan.engine import advance, build_plan

from tests.router_mixture_helpers import mixture_env, rows
from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime

FAST = "[router]\ntimeout_seconds = 0.3\nprefetch_timeout_seconds = 0.6\n"


def test_a_timeout_reaches_the_staged_rule_with_fallback_llm(tmp_path):
    gate = threading.Event()
    try:
        runtime = fake_runtime(decider=FakeDecider(), llm=FakeLLM(gate=gate), inline=False)
        env = mixture_env(tmp_path, runtime, toml=FAST, serve=True)
        build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
        record, step = advance(env, serve=True)
        assert step is not None and step["kind"] == "item"
        (row,) = [row for row in rows(env) if row["policy"] == "router_mixture_v1"][:1]
        assert row["fallback"] == "llm"
        detail = row["detail_json"]["mixture"]
        assert detail["models"]["llm"]["status"] == "timeout"
        assert detail["models"]["decider"]["status"] == "answered"
        assert row["mixture_weights_json"]["effective"]["llm"] == 0.0
        assert row["mixture_weights_json"]["effective"]["staged"] == pytest.approx(2 / 3)
        assert row["propensity_kind"] == "exact"
        from learnloop.daily_plan.view import _why_details

        details = _why_details(record.blocks[0])
        assert "The second model didn't answer in time, so its share went to the usual rule." in details
    finally:
        gate.set()


@pytest.mark.parametrize("error, status", [
    (RuntimeError("HTTP 502"), "failed"),
    (DecisionResponseInvalid("shape changed"), "invalid"),
])
def test_an_error_or_an_invalid_answer_falls_back(tmp_path, error, status):
    runtime = fake_runtime(decider=FakeDecider(error=error), llm=FakeLLM(error=RuntimeError("boom")))
    env = mixture_env(tmp_path, runtime)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    advance(env, serve=True)
    row = rows(env)[0]
    assert row["fallback"] == "both"
    assert row["detail_json"]["mixture"]["models"]["decider"]["status"] == status
    # The floor is kept on a full fallback (owner Q7): still an exact draw.
    assert row["propensity_kind"] == "exact"
    assert row["mixture_weights_json"]["effective"] == {"staged": 1.0, "decider": 0.0, "llm": 0.0}
