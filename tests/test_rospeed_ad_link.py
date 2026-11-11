"""Router speed, item 1: R9's AD predictive link (``value.AdLink``) evaluated once per array, with no value changed.

mvp-0.50's rollouts evaluated the link's 32-point Gauss-Hermite quadrature four times per graded attempt (``F`` and
``logit F`` at the draws' ``η`` and at the belief's, each its own call) and once per topic and draw at every
``P(perform)`` read, though the tail's state changes in a few cells a session. Now one quadrature gives ``F``,
``F'`` and ``logit F`` together (:meth:`AdLink.quadrature`), a model holds the last values it computed per role (the
draws' ``η``, the belief's) and recomputes only the cells whose bits changed, and a graded attempt or a probe reads
the held values for the cells it touches. Every function involved is elementwise, so every number is the one the
code at the follow-up batch's landing (``516db1d862``) computed: these tests put that code back (copied below,
verbatim but for names) and compare **bit for bit** every candidate's ``Q`` per draw, every term and every branch
record, on copy-shaped decisions with every switch of the batch on, on its fallbacks, on the log-space tail of the
link, and for ``baselines`` and ``gain``. Fakes only; nothing is read from a vault.
"""

from __future__ import annotations

import math
import time

import numpy as np
import pytest

from learnloop.router_objective import memory as M
from learnloop.router_objective import value as V
from tests.rospeed_ad_link_helpers import (
    LINK,
    OPTIONS,
    _actions,
    _inputs,
    _landing_code,
    _old_graded,
    _old_logit_and_slope,
    _old_logit_p,
    _old_p,
    _old_performance,
    _old_slope,
    _rows,
)

# -- the decisions -------------------------------------------------------------------------------------------------


CASES = {
    # the copy shapes (topics, a tail block's items), every switch of the batch on
    "arxiv_v2_shaped": dict(n=22),
    "linear_algebra_shaped": dict(n=40),
    "probability_shaped": dict(n=12, items=2),
    # the per-block loop's fallbacks: fewer topics than a session's slots (topics repeat), and a dated use inside
    # the horizon (a block's end can cross it)
    "fewer_topics_than_slots": dict(n=4),
    "a_dated_use_inside_the_horizon": dict(n=22, dated=(V.DatedUse("g", "lo1", 20.3, 1.0),
                                                         V.DatedUse("g", "lo5", 3.01, 2.0))),
    # the link's log-space tail (F underflows below η of about -700) on every topic
    "the_link_in_log_space": dict(n=8, eta_shift=-760.0),
}


def _evaluate(spec: dict, options: dict, draws: int) -> V.Evaluation:
    spec = dict(spec)
    n = spec.pop("n")
    return V.evaluate(_inputs(n, **spec), _actions(n), draws=draws, seed="speed", **options)


#: Every case and option at 8 draws; 64 (the refinement's ceiling) on the two copy-relevant shapes.
GRID = [(case, option, 8) for case in sorted(CASES) for option in sorted(OPTIONS)] + [
    (case, option, 64) for case in ("a_dated_use_inside_the_horizon", "linear_algebra_shaped") for option in sorted(OPTIONS)]


@pytest.mark.parametrize("case,option,draws", GRID)
def test_every_value_is_the_landing_codes_bit_for_bit(case, option, draws, monkeypatch):
    fast = _evaluate(CASES[case], OPTIONS[option], draws)
    with monkeypatch.context() as patch:
        _landing_code(patch)
        landing = _evaluate(CASES[case], OPTIONS[option], draws)
    assert _rows(fast) == _rows(landing)
    assert all(np.isfinite(row.q) for row in fast.valued)


def test_the_baselines_and_the_gain_are_the_landing_codes_bit_for_bit(monkeypatch):
    inputs = _inputs(40, dated=(V.DatedUse("g", "lo1", 12.5, 1.0),))
    options = OPTIONS["every_switch_on"]

    def run():
        return (repr(V.baselines(inputs, 7, draws=16, seed="b", **options)),
                {k: float(v).hex() for k, v in V.gain(inputs, (0.0, 10.0, 30.0, 45.0), draws=16, seed="g",
                                                      **options).items()})

    fast = run()
    with monkeypatch.context() as patch:
        _landing_code(patch)
        landing = run()
    assert fast == landing


def test_the_one_quadrature_gives_each_old_calls_bits():
    grid = np.concatenate([np.linspace(-900, -650, 41), np.linspace(-40, 60, 401), [0.0, -0.0, 1e-300, 745.0]])
    f, df = LINK.quadrature(grid)
    assert f.tobytes() == _old_p(LINK, grid).tobytes()
    assert df.tobytes() == _old_slope(LINK, grid).tobytes()
    assert LINK.p(grid).tobytes() == _old_p(LINK, grid).tobytes()
    assert LINK.slope(grid).tobytes() == _old_slope(LINK, grid).tobytes()
    for new, old in zip(LINK.logit_and_slope(grid), _old_logit_and_slope(LINK, grid), strict=True):
        assert new.tobytes() == old.tobytes()
    assert LINK.logit_p(grid).tobytes() == _old_logit_p(LINK, grid).tobytes()
    # elementwise: a cell's bits do not depend on the array it is evaluated in (stacked, sliced, reshaped)
    stacked = LINK.quadrature(np.stack([grid, grid[::-1]]))[0]
    assert stacked[0].tobytes() == f.tobytes() and stacked[1].tobytes() == f[::-1].tobytes()
    part = grid[3::7]
    assert LINK.logit_p(part).tobytes() == _old_logit_p(LINK, grid)[3::7].tobytes()


def test_the_held_values_follow_the_state_bit_for_bit():
    """The model's held ``logit F`` is recomputed wherever the state's bits changed, in place or by a new array,
    on any state (a copy, another candidate's), and a cell read by a graded attempt is the full call's."""

    model = V._Model(_inputs(12), 32, "held", consistent_review_draw=True, held_ad_link=True)
    state = model.initial()
    first = model.performance(state, 1.0)
    assert first.tobytes() == _old_performance(model, state, 1.0).tobytes()
    state.eta[3, 4] += 0.25  # in place, as the rollouts' updates are
    state.eta[:, 7] = np.nextafter(state.eta[:, 7], np.inf)  # one ulp
    again = model.performance(state, 1.0)
    assert again.tobytes() == _old_performance(model, state, 1.0).tobytes()
    other = model.initial()
    assert model.performance(other, 2.0).tobytes() == _old_performance(model, other, 2.0).tobytes()
    assert model.performance(state, 2.0, belief=True).tobytes() == _old_performance(model, state, 2.0,
                                                                                    belief=True).tobytes()
    # a graded attempt on cells the model holds, and on cells it does not (changed since)
    state.bel[:5, 2] -= 0.5
    rows, cols = np.arange(model.k), np.full(model.k, 2)
    u = np.random.default_rng(3).random(model.k)
    args = (state.eta[rows, cols], state.bel[rows, cols], state.bel_var[rows, cols], state.s[rows, cols],
            state.practiced[rows, cols], np.full(model.k, 1.5), model.theta.coef[rows], u)
    new = model._graded(*args, cells=(rows, cols))
    old = _old_graded(model, *args)
    assert all(a.tobytes() == b.tobytes() for a, b in zip(new, old, strict=True))
    # what a caller is handed cannot be written into the held values
    with pytest.raises(ValueError):
        model._linked_logit(state.eta, "eta")[0, 0] = 1.0


def test_the_linear_algebra_shaped_evaluation_is_faster(monkeypatch):
    """The before/after timing the review file records (median of three, 64 draws, every switch on); asserted only
    loosely (the new code is not slower), since a shared machine's timings vary."""

    spec, options = CASES["linear_algebra_shaped"], OPTIONS["every_switch_on"]

    def timed() -> float:
        spent = []
        for _ in range(3):
            started = time.perf_counter()
            _evaluate(spec, options, 64)
            spent.append(time.perf_counter() - started)
        return sorted(spent)[1]

    fast = timed()
    with monkeypatch.context() as patch:
        _landing_code(patch)
        landing = timed()
    print(f"ROSPEED_AD_LINK linear_algebra_shaped 64 draws: landing {landing * 1000:.0f} ms, now {fast * 1000:.0f} ms")
    assert fast < landing * 1.05 or math.isclose(fast, landing, rel_tol=0.1)


# -- Codex review F1: serving refines until a deadline, so the held link has its switch --------------------------


class _Charged:
    """A deterministic clock charged one unit per sigmoid element, wherever one is evaluated (the rollouts' link
    quadratures, the combiner, the landing code's copies), so a deadline admits exactly the work it admits."""

    def __init__(self) -> None:
        self.spent = 0

    def __call__(self) -> float:
        return float(self.spent)

    def install(self, patch) -> None:
        from tests import rospeed_ad_link_helpers

        real = M.sigmoid

        def charged(x):
            self.spent += int(np.size(x))
            return real(x)

        # The landing code's copy (the ``_old_*`` functions) reads ``sigmoid`` from its helper module.
        for module in (V, M, rospeed_ad_link_helpers):
            patch.setattr(module, "sigmoid", charged)


#: Codex's case: the arxiv_v2-shaped decision (22 topics), seed "speed", merged sessions and the consistent draw.
_DEADLINE_CASE = dict(n=22)
_DEADLINE_OPTIONS = dict(merged_sessions=True, consistent_review_draw=True)


def _deadline_bound(monkeypatch, *, landing: bool, held: bool, deadline: float | None, max_draws: int = 64):
    with monkeypatch.context() as patch:
        clock = _Charged()
        clock.install(patch)
        if landing:
            _landing_code(patch)
        n = _DEADLINE_CASE["n"]
        evaluation = V.evaluate(_inputs(n), _actions(n), draws=8, seed="speed", max_draws=max_draws,
                                keep_going=lambda: True, deadline=deadline, clock=clock,
                                held_ad_link=held, **_DEADLINE_OPTIONS)
        return evaluation, clock.spent


def _choice(evaluation: V.Evaluation) -> str:
    return V.numeric_choice(evaluation, [row.ref for row in evaluation.valued])[0]


def test_the_switch_off_is_the_landing_code_under_a_deadline(monkeypatch):
    """With ``held_ad_link`` off, a deadline-bound evaluation does the landing code's work (every sigmoid element)
    and so completes the same draws, with the same ``Q`` per draw and the same choice; on, it completes more draws
    by the same deadline (which is why it is a serving change with its switch, in the generator payload)."""

    first_batch, cost = _deadline_bound(monkeypatch, landing=True, held=False, deadline=None, max_draws=8)
    assert first_batch.draws == 8 and cost > 0
    deadline = 2.5 * cost  # the landing code's first batch fits; its 16-draw refinement does not
    landing, landing_cost = _deadline_bound(monkeypatch, landing=True, held=False, deadline=deadline)
    off, off_cost = _deadline_bound(monkeypatch, landing=False, held=False, deadline=deadline)
    on, _on_cost = _deadline_bound(monkeypatch, landing=False, held=True, deadline=deadline)
    assert off_cost == landing_cost  # the same work, element for element
    assert (off.draws, off.complete) == (landing.draws, landing.complete) == (8, True)
    assert _rows(off) == _rows(landing)
    assert _choice(off) == _choice(landing)
    # on: the same values per draw, but a deadline admits more of them
    assert on.draws > off.draws
    print("ROSPEED_F1", {"landing": (landing.draws, _choice(landing)), "off": (off.draws, _choice(off)),
                         "on": (on.draws, _choice(on))})


@pytest.mark.slow
def test_the_switch_off_costs_the_landing_codes_work_on_every_shape(monkeypatch):
    """Off, every case and option evaluates exactly the landing code's sigmoid elements (so its time per draw) and
    gives its values bit for bit."""

    for case in ("arxiv_v2_shaped", "linear_algebra_shaped", "a_dated_use_inside_the_horizon", "the_link_in_log_space"):
        for option in OPTIONS.values():
            off_options = {**option, "held_ad_link": False}
            spent = []
            rows = []
            for landing in (False, True):
                with monkeypatch.context() as patch:
                    clock = _Charged()
                    clock.install(patch)
                    if landing:
                        _landing_code(patch)
                    rows.append(_rows(_evaluate(CASES[case], off_options, 8)))
                    spent.append(clock.spent)
            assert spent[0] == spent[1], (case, option)
            assert rows[0] == rows[1], (case, option)


def test_the_switch_reaches_every_rollout_from_the_config(tmp_path):
    """``[router_objective] held_ad_link``: on at the batch's tag by default, off when switched off or below the
    tag; every rollout of a decision takes it from one place (``_rollout_options``)."""

    from learnloop.algorithm_versions import ROUTER_FOLLOWUPS_ALGORITHM_VERSION, ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
    from learnloop.daily_plan import objective_chooser as OC
    from learnloop.router_objective_switches import FOLLOWUP_GENERATOR_SWITCHES, FOLLOWUP_SWITCHES
    from learnloop.vault.loader import load_vault

    from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

    assert "held_ad_link" in FOLLOWUP_GENERATOR_SWITCHES and "held_ad_link" in FOLLOWUP_SWITCHES
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, ROUTER_FOLLOWUPS_ALGORITHM_VERSION)
    assert OC._rollout_options(load_vault(paths.root).config)["held_ad_link"] is True
    set_algorithm_version(paths, ROUTER_LEARNED_TAIL_ALGORITHM_VERSION)
    assert OC._rollout_options(load_vault(paths.root).config)["held_ad_link"] is False
    set_algorithm_version(paths, ROUTER_FOLLOWUPS_ALGORITHM_VERSION)
    append_config_toml(paths.root, "[router_objective]\nheld_ad_link = false\n")
    assert OC._rollout_options(load_vault(paths.root).config)["held_ad_link"] is False
