"""The follow-up batch, item 3: the objective's numeric policy, faster with the same numbers. Fakes only.

* The tail's sessions are one vectorized step over every block's cells when no topic repeats in a session and no
  dated use can be crossed (``merged_sessions``): every candidate's ``Q`` per draw equals the per-block loop's
  to 1e-12 (the reference path), on a copy-shaped decision (arxiv_v2's 22 topics) and on the fallback cases (topics
  fewer than a session's slots; a dated use inside the horizon); and the memory model's FSRS update is called far
  fewer times.
* Codex review F2: a deadline-bound evaluation completes more draws merged, which can change ``Q̄`` and the tie
  rule, so the merged path is a serving change: the rollouts default to the per-block loop, and the numeric policy
  merges only at the batch's tag with ``[router_objective] merged_sessions`` (every rollout of the decision or none).
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
    merged = V.evaluate(inputs, actions, draws=8, seed="s", merged_sessions=True)
    reference = V.evaluate(inputs, actions, draws=8, seed="s", merged_sessions=False)
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
    V.evaluate(inputs, actions, draws=8, seed="s", merged_sessions=True)
    merged = calls["n"]
    calls["n"] = 0
    V.evaluate(inputs, actions, draws=8, seed="s", merged_sessions=False)
    assert merged * 2 < calls["n"], (merged, calls["n"])


def _charged_clock(monkeypatch) -> dict[str, float]:
    """A clock that charges one unit per FSRS update (each vectorized call the same, as Codex's F2 instrument)."""

    clock = {"now": 0.0}
    real = M.Fsrs.review

    def charged(self, *args, **kwargs):
        clock["now"] += 1.0
        return real(self, *args, **kwargs)

    monkeypatch.setattr(M.Fsrs, "review", charged)
    return clock


def test_a_deadline_admits_more_draws_merged_so_the_default_is_the_per_block_loop(monkeypatch):
    """Codex review F2: the same budget completes more refinement batches merged (a serving change below a fixed
    draw count's equality), so the rollouts' default, the predecessor's path, is the per-block loop: the default
    evaluation completes exactly the per-block loop's draws with its values, at the same deadline."""

    inputs, actions = _inputs(22), _actions(22)
    clock = _charged_clock(monkeypatch)
    V.evaluate(inputs, actions, draws=8, seed="s", merged_sessions=False, clock=lambda: clock["now"])
    budget = 2.5 * clock["now"]  # the first batch, the second (twice the draws, the same calls), and a part

    def run(**kwargs):
        clock["now"] = 0.0
        return V.evaluate(inputs, actions, draws=8, seed="s", max_draws=64, keep_going=lambda: True,
                          deadline=budget, clock=lambda: clock["now"], **kwargs)

    per_block, merged, default = run(merged_sessions=False), run(merged_sessions=True), run()
    assert merged.draws > per_block.draws, (merged.draws, per_block.draws)
    assert default.draws == per_block.draws
    assert [row.q_draws for row in default.valued] == [row.q_draws for row in per_block.valued]
    for name in ("baselines", "gain"):
        clock["now"] = 0.0
        args = (inputs, 14) if name == "baselines" else (inputs, [0.0, 30.0])
        getattr(V, name)(*args, draws=8, seed="s")
        default_calls = clock["now"]
        clock["now"] = 0.0
        getattr(V, name)(*args, draws=8, seed="s", merged_sessions=False)
        assert default_calls == clock["now"], name


@pytest.mark.parametrize("version,switch,expected", [
    ("tag", True, True), ("tag", False, False), ("below", True, False)])
def test_the_numeric_policy_merges_only_at_the_tag_with_its_switch(tmp_path, monkeypatch, version, switch, expected):
    """Codex review F2: every rollout a decision runs (the evaluation and its refinement, the correction, the carried
    valuation, the baselines and the day's gain curve) is merged at the batch's tag with ``merged_sessions``, and
    none below it or with the switch off (mvp-0.49's per-block loop, so its deadline admits mvp-0.49's draws)."""

    from learnloop.algorithm_versions import ROUTER_FOLLOWUPS_ALGORITHM_VERSION, ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
    from learnloop.daily_plan import objective_chooser as OC

    from tests.router_mixture_helpers import mixture_env, run
    from tests.router_model_fakes import block_drawing_seed, fake_runtime

    seen: dict[str, list[bool]] = {"evaluate": [], "baselines": [], "gain": []}
    for name in seen:
        real = getattr(V, name)

        def spy(*args, _real=real, _name=name, **kwargs):
            seen[_name].append(bool(kwargs.get("merged_sessions", False)))
            return _real(*args, **kwargs)

        monkeypatch.setattr(OC.V, name, spy)
    tag = ROUTER_FOLLOWUPS_ALGORITHM_VERSION if version == "tag" else ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
    env = mixture_env(tmp_path, fake_runtime(seed=block_drawing_seed()), version=tag,
                      toml=f"[router_objective]\nmerged_sessions = {'true' if switch else 'false'}\n")
    run(env, steps=4)
    assert seen["evaluate"] and seen["baselines"] and seen["gain"], {k: len(v) for k, v in seen.items()}
    assert all(flag is expected for calls in seen.values() for flag in calls), seen


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
