"""Router R2c, G4: the restraint on mid-block follow-ups (``plan_interrupt``).

Fail-first (plan §9 R2c): today a follow-up always joins the current block;
with a fake Decider whose P(intervene now) is near 0, it waits for the
boundary, with an exact propensity on its ``plan_interrupt`` row, and opens
the next block.
"""

from __future__ import annotations

import pytest

from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
from learnloop.daily_plan.engine import advance, build_plan

from tests.daily_plan_fakes import record_attempt, scheduled
from tests.router_mixture_helpers import mixture_env, rows
from tests.router_model_fakes import FakeDecider, fake_runtime, seed_with_first_uniform
from tests.test_daily_plan_build import _wide_items

DECIDER_ONLY = "[router.weights]\nstaged = 0.0\ndecider = 1.0\nllm = 0.0\n"


def _followup_env(tmp_path, runtime, *, version=None, toml=None):
    live = list(_wide_items())
    kwargs = {"version": version} if version else {}
    env = mixture_env(tmp_path, runtime, toml=toml, items=lambda: live, **kwargs)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    record, step = advance(env, serve=True)
    assert step["kind"] == "item"
    assert len(record.current_block().items) >= 2
    # The learner answers it, and the answer produced a follow-up that was
    # not in the plan at build.
    env.clock.advance(1)
    record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                   session_id=env.session_id)
    live.insert(0, scheduled("pi_diag_mid", "lo_diag", followup_kind="negative_surprise_followup"))
    env.clock.advance(1)
    return env


def test_a_follow_up_joins_the_current_block_today_and_waits_with_a_decider_near_zero(tmp_path):
    # Today (R2a, mvp-0.23): the follow-up joins the current block.
    today = _followup_env(tmp_path / "today", fake_runtime(), version=ROUTER_STAGED_FRAME_ALGORITHM_VERSION)
    record, step = advance(today, serve=False)
    current = record.current_block()
    assert "pi_diag_mid" in [item.practice_item_id for item in current.items]
    assert step["practice_item_id"] == "pi_diag_mid"

    # R2c: the Decider says "don't interrupt" (P(yes) = 0); the draw lands
    # outside the floor, so the follow-up waits for the next block.
    floor = 2 * 0.02
    runtime = fake_runtime(decider=FakeDecider(p_yes=0.0), seed=seed_with_first_uniform(at_least=floor))
    env = _followup_env(tmp_path / "r2c", runtime, toml=DECIDER_ONLY)
    record, step = advance(env, serve=True)
    current = record.current_block()
    assert "pi_diag_mid" not in [item.practice_item_id for item in current.items]
    assert current.deferred_followups() == {"pi_diag_mid"}
    (row,) = rows(env, "plan_interrupt")
    assert row["chosen_ref"] == "continue_current"
    assert row["propensity_kind"] == "exact"
    # pi(insert) = (1 - 2 eps) * (w_d * 0) + eps; pi(continue) = 1 - pi(insert).
    assert row["propensity"] == pytest.approx(1 - 0.02)
    assert row["design"] == "model_mixture" and row["seed"]
    assert row["chosen_practice_item_id"] is None
    by_ref = {entry["ref"]: entry for entry in row["candidates_json"]}
    assert by_ref["insert_now"]["propensity"] == pytest.approx(0.02)
    assert by_ref["insert_now"]["feasible"] and by_ref["continue_current"]["feasible"]

    # It opens the next block, at the boundary.
    for _ in range(20):
        env.clock.advance(2)
        if step is None or step["kind"] != "item":
            break
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
        record, step = advance(env, serve=True)
        if step and step.get("practice_item_id") == "pi_diag_mid":
            break
    assert step["practice_item_id"] == "pi_diag_mid"
    block = next(block for block in record.blocks if block.id == step["block_id"])
    assert block.ordinal > current.ordinal
    assert next(item for item in block.items if item.practice_item_id == "pi_diag_mid").origin == "followup"
