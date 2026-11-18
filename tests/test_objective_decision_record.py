"""Refactor E2 (rule L6): the objective choice returns its own ``plan_block`` record, and the record the container
writes from it is the one the container derived from the chooser's record dict before, field for field.

A plan journey on the wide vault with the objective serving (both models answering and the stop coin at its highest
rate, so offered stops, present-next and the policy arm all occur; then no model at all), every boundary's
``plan_block_records`` call captured and made twice: with the core's record, and with it taken away, which is the
container's own derivation (still the path for staged, the R2 mixture and every fallback).
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from learnloop import provenance
from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.daily_plan import boundary_records
from learnloop.daily_plan.engine import advance, build_plan

from tests.daily_plan_fakes import record_attempt
from tests.router_mixture_helpers import mixture_env
from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime
from tests.ro4_objective_serving_helpers import policy_answer


def _comparable(records):
    out = []
    for record in records:
        values = record.as_dict()
        values.pop("id")
        if values["kind"] != "plan_block":
            values.pop("parent_id")
        out.append(values)
    return out


@pytest.mark.parametrize("models", ["both", "none"])
def test_the_cores_record_is_the_one_the_container_derived(tmp_path, monkeypatch, models):
    captured = []
    real = boundary_records.plan_block_records

    def spy(decision, **kwargs):
        captured.append((decision, kwargs))
        return real(decision, **kwargs)

    monkeypatch.setattr(boundary_records, "plan_block_records", spy)
    runtime = (fake_runtime(decider=FakeDecider(), llm=FakeLLM(answer=policy_answer)) if models == "both"
               else fake_runtime())
    env = mixture_env(tmp_path, runtime, version=LATEST_ALGORITHM_VERSION, toml="[router_objective]\nstop_coin = 0.45\n")
    with provenance.trace_scope("TRACE_E2_RECORD"):
        build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
        for _ in range(10):
            _record, step = advance(env, serve=True)
            if step is None or step["kind"] != "item":
                break
            env.clock.advance(2)
            record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                           session_id=env.session_id)
        own = [(decision, kwargs) for decision, kwargs in captured if decision.choice.decision_record is not None]
        assert own, "the objective decided no boundary"
        for decision, kwargs in own:
            derived = replace(decision, choice=replace(decision.choice, decision_record=None))
            assert _comparable(real(decision, **kwargs)) == _comparable(real(derived, **kwargs))
    decided_by = {decision.choice.decision_record.decided_by for decision, _kwargs in own}
    assert decided_by == ({"objective"} if models == "both" else {"objective_no_models"})
