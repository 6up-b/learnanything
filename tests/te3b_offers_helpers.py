"""What other test files use from ``tests/test_te3b_offers.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from typing import Any

import pytest

from learnloop.algorithm_versions import LESSON_OFFERS_ALGORITHM_VERSION
from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.daily_plan.engine import advance
from learnloop.router import lesson_suggestions as LS
from learnloop.router_objective import mix

from tests.router_mixture_helpers import rows


TAG = LESSON_OFFERS_ALGORITHM_VERSION
OFFER = "lesson_offer:lo_diag"


def _candidates() -> list[LS.Candidate]:
    return [
        LS.Candidate(ref=LS.lesson_ref("lo_diag"), learning_object_ids=("lo_diag",), reason="new_goal",
                     predicted_success=0.3, title="Diag"),
        LS.Candidate(ref=LS.lesson_ref("lo_m2"), learning_object_ids=("lo_m2",), reason="cold_failing",
                     predicted_success=0.6, title="M2"),
        LS.Candidate(ref=LS.lesson_ref("lo_p1"), learning_object_ids=("lo_p1",), reason="below_band",
                     predicted_success=0.5, title="P1"),
    ]


@pytest.fixture
def offerable(monkeypatch):
    """TE1b's candidates pinned (one new goal LO first by value, two others)."""

    monkeypatch.setattr(SG, "build_candidates", lambda vault, repository, *, now_iso: (_candidates(), {}))


@pytest.fixture
def offer_drawn(monkeypatch):
    """The mix's draw serves the offer whenever it is in the support (its logged probability is the exact ``μ`` of
    the offer, so G3 still holds; the uniforms are not reproduced, which no test here reads)."""

    real = mix.draw

    def draw(support, parts, weights, epsilon, seed):
        drawn = real(support, parts, weights, epsilon, seed)
        if OFFER in support:
            from dataclasses import replace

            return replace(drawn, chosen=OFFER, propensity=drawn.pi[OFFER])
        return drawn

    monkeypatch.setattr(mix, "draw", draw)


def _policy_arm_seed() -> Any:
    """A decision seed whose RO5 stop coin lands on its ``policy`` arm (its uniform past ``offer_stop`` and
    ``present_next``, 0.05 each), so a test that needs the drawn offer served is not stopped by the coin's 5%
    ``offer_stop`` (TE3b landing: with the seed unpinned these tests failed about one run in twenty)."""

    from learnloop.router.mixture import uniform

    seed = next(f"te3b-policy-arm-{index}" for index in range(10_000)
                if uniform(f"te3b-policy-arm-{index}", "stop_coin") >= 0.2)
    return lambda _key, _decision_id: seed


def _objective_rows(env) -> list[dict[str, Any]]:
    return [row for row in rows(env) if row["policy"] == mix.POLICY]


def _first_decision(env) -> tuple[Any, dict[str, Any]]:
    """Advance until the objective has decided a boundary (the day's randomized check block, placed by the rules,
    comes first); answer what is served on the way."""

    from tests.daily_plan_fakes import record_attempt

    for _ in range(8):
        record, step = advance(env, serve=True)
        if _objective_rows(env):
            return record, step
        if step is None or step["kind"] != "item":
            break
        env.clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
    raise AssertionError("the objective never decided a boundary")
