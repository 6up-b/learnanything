"""The objective's prefetch job refines the numeric policy while the LLM policy is out (refactor fix round, T3).

Production's job hands ``run_numeric`` a ``keep_going`` that holds while the LLM policy is outstanding and the job's
deadline has not passed (``objective_chooser._run_job``). The default pin (``tests/pinned_draws.py``) replaces it with one
batch of draws, so these tests are ``real_draws``: they run the real job on a threaded runtime, an LLM fake that blocks
until released and a clock the test moves, and read each completed batch from ``V.evaluate``'s ``on_complete``.
"""

from __future__ import annotations

import threading
import time
from types import SimpleNamespace

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.daily_plan import objective_chooser as OC
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.daily_plan.router_runtime import RouterRuntime
from learnloop.router_objective import value as V

from tests.router_mixture_helpers import mixture_env
from tests.router_model_fakes import FakeDecider, FakeLLM, FakeModels, block_drawing_seed
from tests.ro4_objective_serving_helpers import policy_answer

pytestmark = pytest.mark.real_draws

WAIT = 60.0


class _MovableClock:
    """The runtime's clock: real monotonic time plus an offset the test moves, so a deadline can pass on command while
    nothing waits on a frozen clock."""

    def __init__(self) -> None:
        self.offset = 0.0

    def __call__(self) -> float:
        return time.monotonic() + self.offset


def _job(tmp_path, monkeypatch, *, stop_after: int):
    """Start the objective job of a plan's first boundary; hold it at its ``stop_after``-th completed batch.

    Returns control: ``batches`` (the draws of each completed batch, in order), ``reached`` (set once the job holds at
    batch ``stop_after``), ``proceed`` (the job continues once set), ``gate`` (the LLM answers once set), ``clock``,
    ``runtime`` and ``entry`` (the prefetch the job runs under, found once it has started)."""

    control = SimpleNamespace(batches=[], reached=threading.Event(), proceed=threading.Event(), gate=threading.Event(),
                              clock=_MovableClock(), refined=[], runtime=None)
    real = V.evaluate

    def spy(*args, **kwargs):
        if kwargs.get("keep_going") is None:  # the correction pass and carried valuations do not refine
            return real(*args, **kwargs)
        control.refined.append(True)
        inner = kwargs.get("on_complete")

        def on_complete(evaluation):
            if inner is not None:
                inner(evaluation)
            control.batches.append(evaluation.draws)
            if len(control.batches) == stop_after:
                control.reached.set()
                control.proceed.wait(WAIT)

        return real(*args, **{**kwargs, "on_complete": on_complete})

    monkeypatch.setattr(V, "evaluate", spy)
    runtime = RouterRuntime(models=FakeModels(decider=FakeDecider(), llm=FakeLLM(gate=control.gate, answer=policy_answer)),
                            inline=False, seed=block_drawing_seed(), clock=control.clock)
    control.runtime = runtime
    env = mixture_env(tmp_path, runtime, version=LATEST_ALGORITHM_VERSION, serve=False,
                      toml='[router_objective]\nstop_coin = 0.0\ncheck_rate = "off"\n[router]\ntimeout_seconds = 3.0\nprefetch_timeout_seconds = 40.0\n')
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    advance(env, serve=False)  # a read of the first boundary starts its job and leaves the decision open
    return control, env


def _finish(control) -> None:
    control.gate.set()
    control.proceed.set()
    for thread in list(threading.enumerate()):
        if thread.name.startswith(("learnloop-router-", "learnloop-objective-")):
            thread.join(WAIT)


def test_refinement_runs_another_batch_while_the_llm_is_out_and_stops_when_it_answers(tmp_path, monkeypatch):
    control, env = _job(tmp_path, monkeypatch, stop_after=2)
    try:
        assert control.reached.wait(WAIT), "the numeric policy never finished a second batch with the LLM out"
        # The LLM has not answered, and the job completed a second batch of draws: refinement went on (it doubles).
        assert not control.gate.is_set() and len(control.batches) == 2 and control.batches[1] == 2 * control.batches[0]
        entries = list(control.runtime._entries.values())
        assert len(entries) == 1 and not entries[0].events[OC.LLM].is_set()
        # The model answers; the job, held at its second batch, then asks keep_going and stops there.
        control.gate.set()
        assert entries[0].events[OC.LLM].wait(WAIT), "the LLM fake never answered"
        control.proceed.set()
        assert entries[0].events[OC.NUMERIC].wait(WAIT), "the numeric policy never answered"
        time.sleep(0.2)  # a refinement that kept going would finish its third batch in this time
        assert len(control.batches) == 2
        assert entries[0].components[OC.NUMERIC].parsed.evaluation.draws == control.batches[1]
    finally:
        _finish(control)


def test_refinement_stops_at_the_deadline_with_the_llm_still_out(tmp_path, monkeypatch):
    control, env = _job(tmp_path, monkeypatch, stop_after=2)
    try:
        assert control.reached.wait(WAIT), "the numeric policy never finished a second batch with the LLM out"
        entries = list(control.runtime._entries.values())
        assert len(entries) == 1 and not entries[0].events[OC.LLM].is_set()
        control.clock.offset += entries[0].deadline - control.clock() + 1.0  # past the job's deadline
        control.proceed.set()
        assert entries[0].events[OC.NUMERIC].wait(WAIT), "the numeric policy never answered"
        time.sleep(0.2)
        assert len(control.batches) == 2 and not control.gate.is_set()
        assert not entries[0].events[OC.LLM].is_set()  # it stopped at the deadline, not for the model
    finally:
        _finish(control)
