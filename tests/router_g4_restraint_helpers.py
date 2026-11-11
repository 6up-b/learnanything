"""What other test files use from ``tests/test_router_g4_restraint.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.daily_plan.engine import advance, build_plan

from tests.daily_plan_fakes import record_attempt, scheduled
from tests.router_mixture_helpers import mixture_env
from tests.daily_plan_build_helpers import _wide_items


DECIDER_ONLY = "[router.weights]\nstaged = 0.0\ndecider = 1.0\nllm = 0.0\n"
#: A first stage outside every floor (k * eps <= 7 * 0.02): the draw follows
#: the Decider, whose block choice is the rule's pick (``first_option``).
PAST_THE_FLOOR = 0.2


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
