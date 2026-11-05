"""Router objective RO6 §10 in serving: ``Ṽ = V_tail + ŵ·V_residual`` inside the numeric policy's value. Fakes only.

* **Predecessor byte-identity**: below the tag (mvp-0.48) and at the tag with ``learned_tail = false``, Today's
  blocks, the router's rows, the traces' candidates and ``μ`` are identical, and no trace carries a residual;
* **the trace's terms recompute**: at the tag each candidate's ``V_residual`` is the frozen fit at its frozen
  features, ``Ṽ = V_tail + ŵ·V_residual``, ``V_tail`` is the tail's ``Q̄`` (``terms.q``, unchanged); with no
  randomized contrast ``ŵ = 0`` and the numeric policy's choice is the tail's argmax;
* **a residual moves the argmax only through ŵ**: with a planted fit and ``ŵ = 1`` the numeric policy chooses on
  ``Ṽ``, the tie record names it and the tail's own argmax stays beside it;
* the features frozen at serve time equal the ones rebuilt from the trace and RO0's receipt;
* a residual that fails to compute leaves the numeric policy as mvp-0.48's, and the trace says so.
"""

from __future__ import annotations

import pytest

from learnloop.algorithm_versions import ROUTER_CALIBRATION_ALGORITHM_VERSION, ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
from learnloop.db.stores import router_objective as store
from learnloop.router_objective import learned_tail as LT
from learnloop.router_objective import tail_data as TD
from learnloop.router_objective import tail_serve as TS
from learnloop.router_objective import trace as T

from tests.router_mixture_helpers import mixture_env, run
from tests.router_model_fakes import FakeLLM, fake_runtime
from tests.test_ro4_objective_serving import _blocks, _shape, policy_answer

TAG = ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
OLD = ROUTER_CALIBRATION_ALGORITHM_VERSION
OFF = "[router_objective]\nlearned_tail = false\n"


def _traces(env) -> list[dict]:
    with env.repository.connection() as connection:
        return [store.trace(connection, row["decision_id"]) for row in store.traces(connection)]


def _pin(monkeypatch):
    # The boundary key names the version, and the mix's draw and the numeric policy's rollouts are seeded from it,
    # so both runs drop the version (and the fresh plan and attempt ids) from the key (RO5's method).
    from learnloop.daily_plan import objective_chooser as OC

    real_hash = OC._hash
    monkeypatch.setattr(OC, "_hash", lambda value: real_hash(
        {k: v for k, v in value.items() if k not in ("version", "plan_id")} if isinstance(value, dict) else value))
    monkeypatch.setattr(OC, "_latest_attempt", lambda _repository: "pinned-attempt")
    return lambda _key, _decision: "pinned-seed"


@pytest.mark.parametrize("toml", [OFF], ids=["switch_off"])
def test_below_the_tag_and_switched_off_serve_mvp_048_exactly(tmp_path, monkeypatch, toml):
    pinned = _pin(monkeypatch)
    old = mixture_env(tmp_path / "old", fake_runtime(seed=pinned), version=OLD)
    off = mixture_env(tmp_path / "off", fake_runtime(seed=pinned), version=TAG, toml=toml)
    old_record, off_record = run(old), run(off)
    assert _blocks(old_record) == _blocks(off_record)
    assert _shape(old) == _shape(off)
    old_traces, off_traces = _traces(old), _traces(off)
    assert old_traces and len(old_traces) == len(off_traces)
    assert [t["trace"]["candidates"] for t in old_traces] == [t["trace"]["candidates"] for t in off_traces]
    assert [t["trace"]["mixing"]["mu"] for t in old_traces] == [t["trace"]["mixing"]["mu"] for t in off_traces]
    assert all("residual" not in t["trace"] for t in (*old_traces, *off_traces))


def test_at_the_tag_the_trace_carries_the_residual_and_its_terms_recompute(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(llm=FakeLLM(answer=policy_answer)), version=TAG)
    run(env)
    traces = [t for t in _traces(env) if t["decision_kind"] == "plan_block"]
    assert traces
    for found in traces:
        trace = found["trace"]
        record = trace["residual"]
        assert record["status"] == "applied" and record["version"] == TS.VERSION
        assert record["w_hat"] == 0.0 and record["weight"]["n"] == 0  # no randomized contrast yet
        fit = LT.Fit.from_dict(record["fit"])
        for ref, entry in record["candidates"].items():
            terms = trace["candidates"][ref]["terms"]
            # Exactly, to the trace's six places: the fit's numbers and the features are kept exactly.
            assert entry["v_residual"] == pytest.approx(fit.value(entry["features"]), abs=1e-6)
            assert terms["v_tail"] == terms["q"] == entry["v_tail"]
            assert terms["v_tilde"] == pytest.approx(terms["v_tail"] + terms["w_hat"] * terms["v_residual"], abs=1e-6)
            assert len(entry["features"]) == len(LT.NAMES)
        tie = trace["policies"]["numeric"]["tie"]
        if trace["policies"]["numeric"]["status"] == "answered":
            assert tie["argmax"] == tie["tail_argmax"]  # ŵ = 0: the tail decides
        assert any("correction learned" in line for line in T.explain(found))


def test_the_features_frozen_at_serve_equal_the_rebuild_from_the_trace_and_ro0s_receipt(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    run(env)
    with env.repository.connection() as connection:
        for row in store.traces(connection):
            found = store.trace(connection, row["decision_id"])
            receipt = store.decision_state(connection, row["decision_id"])
            frozen = found["trace"]["residual"]["candidates"]
            rebuilt = TD.rebuilt_features(found["trace"], receipt)
            for ref, entry in frozen.items():
                assert rebuilt[ref] == pytest.approx(tuple(float(v) for v in entry["features"]), abs=1e-4), ref


def _planted_fit(monkeypatch, coef_on: str, value: float):
    """Every decision's fit: a residual on one feature (standardization the identity), and ŵ = 1."""

    names = LT.NAMES
    planted = LT.Fit(generator="g", names=names, mean=(0.0,) * len(names), sd=(1.0,) * len(names),
                     coef=tuple(value if name == coef_on else 0.0 for name in names), n=1, prior_sd=0.01,
                     source="planted")

    class _Fits:
        by_generator = {"g": planted}
        order = ("g",)
        steps = TD.Steps(transitions=(), censored={}, change_points=(), returns_censored={})
        decisions = 0

        def for_serving(self, _generator):
            return planted, "own_version"

    monkeypatch.setattr(TD, "fits", lambda *_a, **_k: _Fits())
    monkeypatch.setattr(LT, "residual_weight", lambda *_a, **_k: LT.WeightFit(
        w_hat=1.0, slope_mean=1.0, slope_sd=0.0, tail_slope=1.0, n=1, forced=1, rank=1.0, p_rank=1.0, sigma2=0.0,
        prior_sd=1.0, source="planted"))


def test_a_planted_residual_moves_the_numeric_choice_through_w_hat(tmp_path, monkeypatch):
    # A large residual for stopping: on V~ the numeric policy picks stop wherever it is in the support.
    _planted_fit(monkeypatch, "stop", 1000.0)
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    run(env, steps=3)
    found = [t for t in _traces(env) if "stop_for_today" in t["trace"]["candidates"]]
    assert found
    trace = found[0]["trace"]
    numeric = trace["policies"]["numeric"]
    assert numeric["choice"] == "stop_for_today" and numeric["tie"]["on"].startswith("v_tilde")
    assert trace["residual"]["w_hat"] == 1.0
    stop = trace["candidates"]["stop_for_today"]["terms"]
    assert stop["v_residual"] == pytest.approx(1000.0) and stop["v_tilde"] == pytest.approx(stop["q"] + 1000.0)


def test_a_failed_residual_leaves_the_numeric_policy_as_the_predecessors(tmp_path, monkeypatch):
    def broken(*_args, **_kwargs):
        raise RuntimeError("no fit")

    monkeypatch.setattr(TD, "fits", broken)
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    run(env, steps=3)
    traces = _traces(env)
    assert traces
    for found in traces:
        record = found["trace"]["residual"]
        assert record["status"] == "failed" and "no fit" in record["error"]
        assert all("v_tilde" not in (entry.get("terms") or {}) for entry in found["trace"]["candidates"].values())
        assert "on" not in (found["trace"]["policies"]["numeric"].get("tie") or {})
