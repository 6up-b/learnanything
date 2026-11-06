"""The follow-up batch, item 3: the objective's numeric policy, faster with the same numbers. Fakes only.

* The tail's sessions are one vectorized step over every block's cells when no topic repeats in a session and no
  dated use can be crossed (``value.MERGED_SESSIONS``): every candidate's ``Q`` per draw equals the per-block loop's
  to 1e-12 (the reference path), on a copy-shaped decision (arxiv_v2's 22 topics) and on the fallback cases (topics
  fewer than a session's slots; a dated use inside the horizon); and the memory model's FSRS update is called far
  fewer times.
* The memory model's FSRS update without ``np.clip`` equals the scheduler's scalar formulas (``scheduling.fsrs``).
"""

from __future__ import annotations

import numpy as np
import pytest

from learnloop.router_objective import memory as M
from learnloop.router_objective import value as V
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS


def _inputs(n: int, *, dated: tuple = (), items: int = 3, seed: int = 0) -> V.Inputs:
    rng = np.random.default_rng(seed)
    topics = tuple(V.Topic(lo=f"lo{i}", eta_mean=float(rng.normal(0, 1)), eta_var=0.5, practiced=bool(i % 3),
                           difficulty=float(rng.uniform(2, 8)), stability=float(rng.uniform(1, 20)) if i % 3 else 0.0,
                           elapsed_days=float(rng.uniform(0, 10)) if i % 3 else 0.0, undated_density=1 / 90,
                           reading_count=float(i % 2)) for i in range(n))
    return V.Inputs(topics=topics, dated=dated, session_minutes=5.0, price=V.Price(kappa0=0.0003, remembered=30.0),
                    tail_block_minutes=10.0, tail_block_items=items, horizon_days=90.0,
                    fsrs_weights=tuple(FSRS6_DEFAULT_WEIGHTS), return_gaps_days=(1.0, 2.0, 1.0))


def _actions(n: int) -> list[V.Action]:
    lo = [f"lo{i}" for i in range(n)]
    return [V.Action(ref="stop_for_today", kind=V.STOP),
            V.Action(ref="a", kind=V.REVIEW, item_los=tuple(lo[1:4]), minutes=10.0, minutes_log_sd=0.3),
            V.Action(ref="b", kind=V.NEW_PRACTICE, item_los=(lo[0],), minutes=8.0),
            V.Action(ref="c", kind=V.PROBE, item_los=(lo[-1],), minutes=4.0,
                     repair=V.Action(ref="c:repair", kind=V.REPAIR, item_los=(lo[-1],), minutes=4.0)),
            V.Action(ref="d", kind=V.READING, item_los=(lo[min(2, n - 1)],), minutes=12.0)]


CASES = {
    "copy_shaped_22_topics": dict(n=22),
    "fewer_topics_than_slots": dict(n=4),
    "a_dated_use_inside_the_horizon": dict(n=22, dated=(V.DatedUse("g", "lo1", 20.3, 1.0),
                                                         V.DatedUse("g", "lo5", 3.01, 2.0))),
}


@pytest.mark.parametrize("case", sorted(CASES))
def test_merged_sessions_equal_the_per_block_loop(case, monkeypatch):
    spec = dict(CASES[case])
    n = spec.pop("n")
    inputs, actions = _inputs(n, **spec), _actions(n)
    merged = V.evaluate(inputs, actions, draws=8, seed="s")
    monkeypatch.setattr(V, "MERGED_SESSIONS", False)
    reference = V.evaluate(inputs, actions, draws=8, seed="s")
    for fast, slow in zip(merged.valued, reference.valued, strict=True):
        assert fast.ref == slow.ref
        assert np.max(np.abs(np.array(fast.q_draws) - np.array(slow.q_draws))) <= 1e-12, fast.ref
        for key, value in slow.terms.items():
            assert abs(fast.terms[key] - value) <= 1e-12, (fast.ref, key)
    assert abs(merged.reference.q - reference.reference.q) <= 1e-12


def test_the_merged_path_calls_the_fsrs_update_far_fewer_times(monkeypatch):
    inputs, actions = _inputs(22), _actions(22)
    calls = {"n": 0}
    real = M.Fsrs.review

    def counted(self, *args, **kwargs):
        calls["n"] += 1
        return real(self, *args, **kwargs)

    monkeypatch.setattr(M.Fsrs, "review", counted)
    V.evaluate(inputs, actions, draws=8, seed="s")
    merged = calls["n"]
    calls["n"] = 0
    monkeypatch.setattr(V, "MERGED_SESSIONS", False)
    V.evaluate(inputs, actions, draws=8, seed="s")
    assert merged * 2 < calls["n"], (merged, calls["n"])


def test_the_fsrs_update_without_clip_equals_the_schedulers_scalar_formulas():
    from learnloop.scheduling import fsrs as F

    fsrs = M.Fsrs(tuple(FSRS6_DEFAULT_WEIGHTS))
    rng = np.random.default_rng(3)
    d = rng.uniform(1, 10, 200)
    s = rng.uniform(0.01, 60, 200)
    elapsed = rng.uniform(0, 40, 200)
    practiced = rng.random(200) < 0.7
    good = rng.random(200) < 0.6
    nd, ns = fsrs.review(d, s, practiced, elapsed, good)
    r = fsrs.retrievability(s, elapsed)
    for i in range(200):
        assert r[i] == pytest.approx(F.forgetting_curve(float(s[i]), float(elapsed[i])), abs=1e-12)
        rating = F.Rating.GOOD if good[i] else F.Rating.AGAIN
        if not practiced[i]:
            assert nd[i] == pytest.approx(F.initial_difficulty(rating), abs=1e-12)
            assert ns[i] == pytest.approx(max(F.initial_stability(rating), M.S_MIN), abs=1e-12)
