"""The follow-up batch on the copy-shaped synthetic vault: two weeks (RO6's few-weeks journey: six practised topics, the
default arms, one day a week without a session, both policies answering through fakes, a seeded ~70% learner) at
mvp-0.50. Its comparison with mvp-0.49 is recorded in docs/reviews/router-followups-nov5.md. Printed: the
transitions and their censoring (items 4 and 5), the generator versions (item 5), the combiner's fit (item 2) and the
numeric policy's time per decision (item 3). Fakes only; no model request.
"""

from __future__ import annotations

import json
import os
from statistics import median

import pytest

from learnloop.algorithm_versions import ROUTER_FOLLOWUPS_ALGORITHM_VERSION
from learnloop.db.stores import router_objective as store
from learnloop.router_objective import tail_data as TD
from learnloop.vault.loader import load_vault

from tests.router_model_fakes import FakeLLM, fake_runtime
from tests.test_ro4_objective_serving import policy_answer
from tests.test_ro5_calibration import _week_env
from tests.test_ro6_tail_data import _days


def _env(tmp_path, version: str):
    from learnloop.vault.paths import VaultPaths
    from tests.helpers import set_algorithm_version

    runtime = fake_runtime(llm=FakeLLM(answer=policy_answer))
    env = _week_env(tmp_path, runtime)
    set_algorithm_version(VaultPaths(env.vault.root, env.vault.config), version)
    env.vault = load_vault(env.vault.root)
    return env, runtime


@pytest.mark.slow
def test_two_weeks_after_the_batch(tmp_path):
    version = ROUTER_FOLLOWUPS_ALGORITHM_VERSION
    days = int(os.environ.get("LEARNLOOP_ROFU_DAYS", "15"))
    env, runtime = _env(tmp_path, version)
    _days(env, runtime, range(days), skip=frozenset(day for day in range(days) if day % 7 == 3))
    with env.repository.connection() as connection:
        traces = [store.trace(connection, row["decision_id"])["trace"] for row in store.traces(connection)
                  if row["decision_kind"] == "plan_block"]
        fits = TD.fits(connection, env.vault.config, at=env.now_iso())
    latency = [trace["policies"]["numeric"]["latency_ms"] for trace in traces
               if trace["policies"]["numeric"].get("latency_ms") is not None]
    combiner = [trace["versions"]["memory_model"] for trace in traces if trace["versions"].get("memory_model")]
    summary = {
        "version": version, "days": days, "decisions": len(traces),
        "transitions": len(fits.steps.transitions), "censored": dict(sorted(fits.steps.censored.items())),
        "generator_versions": len(fits.order), "fits": {key: fit.n for key, fit in fits.by_generator.items()},
        "carried_for_records": sum(len(trace.get("carried_for") or ()) for trace in traces),
        "numeric_ms": {"median": median(latency) if latency else None, "max": max(latency) if latency else None},
        "combiner_last": {key: combiner[-1].get(key) for key in ("n", "source", "sources")} if combiner else None,
        "learning_last": traces[-1]["versions"].get("learning") if traces else None,
    }
    # Item 2's cost: the combiner's fit as of the end, with and without the traces' join (median of three).
    import time

    from learnloop.daily_plan import objective_inputs as OI

    def timed(vault) -> float:
        spent = []
        for _ in range(3):
            started = time.perf_counter()
            OI._combiner(env.repository, env.now_iso(), vault)
            spent.append((time.perf_counter() - started) * 1000)
        return round(median(spent), 1)

    from tests.helpers import append_config_toml

    summary["combiner_ms"] = {"as_configured": timed(env.vault)}
    append_config_toml(env.vault.root, "[router_objective]\ncombiner_trace_outcomes = false\n")
    summary["combiner_ms"]["join_off"] = timed(load_vault(env.vault.root))
    print("ROFU_WEEKS", json.dumps(summary, sort_keys=True, default=str))
    # Two weeks of the default arms leave transitions to value, one generator per serving config, and a fit for it.
    assert traces and summary["decisions"] == len(traces)
    assert summary["transitions"] > 0
    assert summary["generator_versions"] >= 1 and summary["fits"]
    assert all(trace["versions"]["serving_switches"] for trace in traces)
