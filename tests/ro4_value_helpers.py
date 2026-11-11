"""What other test files use from ``tests/test_ro4_value.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import math

from learnloop.router_objective import memory as M
from learnloop.router_objective import value as V
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS


W = tuple(FSRS6_DEFAULT_WEIGHTS)
EXACT = M.Combiner(mean=(0.0, 1.0, 0.0), variance=(0.0, 0.0, 0.0), source="test")
FIXED = V.Learning(gamma=(0.0, 0.0), gbar=((0.0, 0.0), (0.0, 0.0)))


def _logit(p: float) -> float:
    return math.log(p / (1 - p))


def _inputs(**overrides):
    base = dict(
        topics=(V.Topic(lo="lo_a", eta_mean=_logit(0.78), eta_var=0.0, undated_density=0.0),),
        dated=(), session_minutes=10.0,
        price=V.Price(kappa0=0.02 * 2 * 10 / ((10 + 10) ** 2 - 10 ** 2), remembered=10.0, remembered_source="test"),
        tail_block_minutes=10.0, tail_block_items=1, horizon_days=1.0, fsrs_weights=W,
        return_gaps_days=(2.0,), stop_accept=(1e6, 1e-6), combiner=EXACT, learning=FIXED,
    )
    base.update(overrides)
    return V.Inputs(**base)
