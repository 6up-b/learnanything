"""Router R2b, G3: propensities are exact.

Fail-first (plan §9 R2b, test 2): the logged propensity is reproducible from
the logged components: pi(chosen) recomputed from the row's effective weights,
both models' distributions, the support, the staged pick and epsilon equals
the logged propensity; the seed reproduces the two-stage draw; every option
keeps at least epsilon; a candidate outside the support has propensity 0; a
failed model's weight goes to the staged rule.
"""

from __future__ import annotations

import pytest

from learnloop.router import mixture as mx

from tests.router_mixture_helpers import mixture_env, rows, run
from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime


def _skewed(refs):
    return {ref: (index + 1.0) for index, ref in enumerate(refs)}


def _recompute(row):
    detail = row["detail_json"]["mixture"]
    return mx.recompute({
        "support": detail["support"],
        "staged_ref": detail["staged_ref"],
        "chosen": row["chosen_ref"],
        "epsilon": detail["epsilon"],
        "effective_weights": row["mixture_weights_json"]["effective"],
        "distributions": {name: dist for name, dist in row["model_distributions_json"].items() if dist},
    })


def test_the_logged_propensity_is_reproducible_from_the_logged_components(tmp_path):
    runtime = fake_runtime(decider=FakeDecider(choice=_skewed), llm=FakeLLM())
    env = mixture_env(tmp_path, runtime)
    run(env)
    decisions = [row for row in rows(env) if row["policy"] == "router_mixture_v1"]
    assert decisions, "the mixture made no decision"
    for row in decisions:
        assert row["design"] == "model_mixture" and row["seed"]
        assert row["propensity_kind"] == "exact" and 0 < row["propensity"] < 1
        assert _recompute(row) == pytest.approx(row["propensity"], abs=1e-12)
        detail = row["detail_json"]["mixture"]
        # The seed reproduces the two-stage draw.
        components = mx.component_distributions(
            detail["support"], detail["staged_ref"],
            {name: dist for name, dist in row["model_distributions_json"].items() if dist},
        )
        again = mx.draw(detail["support"], components, row["mixture_weights_json"]["effective"], detail["epsilon"],
                        row["seed"])
        assert again.chosen == row["chosen_ref"] and again.component == detail["drawn_component"]
        # Every option keeps the floor; everything else has propensity 0.
        by_ref = {entry["ref"]: entry for entry in row["candidates_json"]}
        for ref in detail["support"]:
            assert by_ref[ref]["propensity"] >= detail["epsilon"] - 1e-12
        for ref, entry in by_ref.items():
            if ref not in detail["support"]:
                assert entry["propensity"] == 0.0
        assert sum(by_ref[ref]["propensity"] for ref in detail["support"]) == pytest.approx(1.0)


def test_a_failed_models_weight_goes_to_the_staged_rule(tmp_path):
    runtime = fake_runtime(decider=FakeDecider(error=RuntimeError("down")), llm=FakeLLM())
    env = mixture_env(tmp_path, runtime)
    run(env)
    decisions = [row for row in rows(env) if row["policy"] == "router_mixture_v1"]
    assert decisions
    for row in decisions:
        assert row["fallback"] == "decider"
        effective = row["mixture_weights_json"]["effective"]
        assert effective["decider"] == 0.0
        assert effective["staged"] == pytest.approx(2 / 3)
        assert _recompute(row) == pytest.approx(row["propensity"], abs=1e-12)


def test_the_two_stage_marginal_is_the_mixture():
    support = ["a", "b", "c"]
    components = mx.component_distributions(support, "a", {"decider": {"a": 0.1, "b": 0.6, "c": 0.3},
                                                          "llm": {"a": 0.5, "b": 0.5, "c": 0.0}})
    weights = mx.effective_weights({"staged": 1, "decider": 1, "llm": 1}, [])
    pi = mx.mixture(support, components, weights, 0.02)
    counts = {ref: 0 for ref in support}
    n = 20_000
    for index in range(n):
        counts[mx.draw(support, components, weights, 0.02, f"s{index}").chosen] += 1
    for ref in support:
        assert counts[ref] / n == pytest.approx(pi[ref], abs=0.015)
    assert min(pi.values()) >= 0.02
