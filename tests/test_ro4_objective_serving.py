"""Router objective RO4 (spec §8.2-§8.3, §8.8, §8.10): the objective serving Today, with fakes only.

* **Predecessor**: with ``[router_objective] enabled = false`` at the tag, and below it, Today is mvp-0.46's mixture
  and frame exactly (the same blocks, the same logged decisions), and no trace is written.
* **The frame**: stop is in every reversible support; a block can run past the plan's minutes.
* **Propensities (G3)**: ``μ`` recomputed from the logged values on every path (both policies, the LLM's failure,
  the numeric policy's timeout, no models at all); the logged probability is the one actually used.
* **The trace**: one immutable row per decision, with each candidate's sensors and terms, both policies, the mix.
"""

from __future__ import annotations

from typing import Any

import pytest

from learnloop.algorithm_versions import INTERVAL_FACTOR_ALGORITHM_VERSION, ROUTER_OBJECTIVE_ALGORITHM_VERSION
from learnloop.db.stores import router_objective as store
from learnloop.router_objective import mix

from tests.router_mixture_helpers import mixture_env, rows, run
from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime
from tests.ro4_objective_serving_helpers import _blocks, _shape, policy_answer

TAG = ROUTER_OBJECTIVE_ALGORITHM_VERSION
OLD = INTERVAL_FACTOR_ALGORITHM_VERSION


def _traces(env) -> list[dict[str, Any]]:
    with env.repository.connection() as connection:
        return [store.trace(connection, row["decision_id"]) for row in store.traces(connection)]


def test_off_at_the_tag_is_the_predecessor_exactly(tmp_path):
    # The draw's seed names the version (the boundary key does), so both runs pin one seed.
    pinned = lambda _key, _decision: "pinned-seed"  # noqa: E731
    old = mixture_env(tmp_path / "old", fake_runtime(seed=pinned), version=OLD)
    off = mixture_env(tmp_path / "off", fake_runtime(seed=pinned), version=TAG,
                      toml="[router_objective]\nenabled = false\n")
    assert not getattr(off.policy, "soft_budget", False)
    old_record, off_record = run(old), run(off)
    assert _blocks(old_record) == _blocks(off_record)
    assert _shape(old) == _shape(off)
    assert _traces(off) == [] and _traces(old) == []


def test_with_no_model_the_numeric_policy_serves_with_stop_in_every_support(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    assert env.policy.soft_budget is True
    run(env)
    decided = [row for row in rows(env) if row["policy"] == mix.POLICY]
    assert decided, "the objective decided at least one block"
    traces = {trace["decision_id"]: trace for trace in _traces(env)}
    for row in decided:
        mixture = row["detail_json"]["mixture"]
        assert "stop_for_today" in mixture["support"]
        assert mixture["failed"] == ["llm"]  # no model set up: the LLM policy's share is staged's
        recomputed = mix.recompute(mixture)
        assert recomputed[row["chosen_ref"]] == pytest.approx(row["propensity"] or 1.0)
        assert sum(recomputed.values()) == pytest.approx(1.0)
        trace = traces[row["id"]]
        assert trace["chosen_ref"] == row["chosen_ref"] and trace["numeric_status"] == "answered"
        body = trace["trace"]
        assert set(body["candidates"]) == set(mixture["support"])
        assert body["mixing"]["w"] == pytest.approx(0.8)
        assert "no randomized checks" in body["mixing"]["weight_note"]
        assert body["versions"]["kappa"]["regime"] == "seed"
        for ref, entry in body["candidates"].items():
            assert entry["terms"] is not None and "kappa_integral" in entry["terms"], ref


def test_both_policies_mix_with_exact_propensities_and_the_decider_is_advice(tmp_path):
    decider, llm = FakeDecider(), FakeLLM(answer=policy_answer)
    env = mixture_env(tmp_path, fake_runtime(decider=decider, llm=llm), version=TAG)
    run(env)
    decided = [row for row in rows(env) if row["policy"] == mix.POLICY]
    assert decided
    for row in decided:
        mixture = row["detail_json"]["mixture"]
        assert mixture["failed"] == []
        assert set(mixture["llm_distribution"]) == set(mixture["support"])
        assert all(value > 0 for value in mixture["llm_distribution"].values())
        assert mix.recompute(mixture)[row["chosen_ref"]] == pytest.approx(row["propensity"] or 1.0)
        assert row["model_distributions_json"]["decider"] is not None  # logged as advice
        assert mixture["effective_weights"]["staged"] == 0.0
    schemas = {request.result_model.__name__ for request in llm.requests}
    assert schemas <= {"RouterLLMChoiceV3", "RouterLLMRestraintV3"}  # the older chooser is not served


def test_a_failed_llm_moves_only_its_share_to_staged(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(llm=FakeLLM(error=RuntimeError("down"))), version=TAG)
    run(env)
    decided = [row for row in rows(env) if row["policy"] == mix.POLICY]
    assert decided
    for row in decided:
        mixture = row["detail_json"]["mixture"]
        assert mixture["failed"] == ["llm"]
        assert mixture["effective_weights"] == pytest.approx({"staged": 0.8, "llm": 0.0, "numeric": 0.2})
        assert mix.recompute(mixture)[row["chosen_ref"]] == pytest.approx(row["propensity"] or 1.0)


def test_a_numeric_timeout_is_a_failure_and_both_failed_keeps_the_floor(tmp_path, monkeypatch):
    from learnloop.daily_plan import objective_chooser as OC

    real = OC.run_numeric

    def timed_out(*args, **kwargs):
        real(*args, **kwargs)
        return OC.NumericPolicy(status="timeout", error="no answer within the budget")

    monkeypatch.setattr(OC, "run_numeric", timed_out)
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    run(env)
    decided = [row for row in rows(env) if row["policy"] == mix.POLICY]
    assert decided
    for row in decided:
        mixture = row["detail_json"]["mixture"]
        assert set(mixture["failed"]) == {"llm", "numeric"}
        assert mixture["effective_weights"] == pytest.approx({"staged": 1.0, "llm": 0.0, "numeric": 0.0})
        mu = mix.recompute(mixture)
        k = len(mixture["support"])
        assert all(value >= mixture["epsilon"] - 1e-12 for value in mu.values())
        assert mu[mixture["staged_ref"]] == pytest.approx(1 - k * mixture["epsilon"] + mixture["epsilon"])


def test_the_seed_reproduces_the_draw(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    run(env)
    for row in [row for row in rows(env) if row["policy"] == mix.POLICY]:
        mixture = row["detail_json"]["mixture"]
        parts = mix.components(mixture["support"], mixture["staged_ref"], llm=mixture["llm_distribution"],
                               numeric_ref=mixture["numeric_choice"])
        again = mix.draw(mixture["support"], parts, mixture["effective_weights"], mixture["epsilon"], row["seed"])
        assert again.chosen == row["chosen_ref"]
