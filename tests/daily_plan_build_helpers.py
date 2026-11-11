"""What other test files use from ``tests/test_daily_plan_build.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import timedelta

from learnloop.daily_plan.engine import advance
from learnloop.daily_plan.types import LANES

from tests.daily_plan_fakes import NOW, record_attempt, scheduled, seed_due, seed_open_problem
from tests.helpers import create_daily_plan_vault


PAST = NOW - timedelta(days=1)
LAST = NOW - timedelta(days=5)
FUTURE = NOW + timedelta(days=5)


def _run_to_end(env, *, limit=60):
    clock = env.clock
    steps = []
    record = None
    for _ in range(limit):
        record, step = advance(env, serve=True) if env.session_id else advance(env, serve=False)
        _assert_finite(record)
        steps.append(step)
        if step["kind"] != "item":
            break
        clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], clock.now())
        clock.advance(1)
    return record, steps


def _assert_finite(record):
    assert record.minutes_planned() <= record.budget + 1e-6
    allotment, spent = record.ledger()
    for lane in LANES:
        assert spent[lane] <= allotment[lane] + 1e-3, (lane, spent, allotment)


def _wide_vault(tmp_path, **kwargs):
    los = {
        "lo_m1": [("pi_m1a", 1.0), ("pi_m1b", 1.0)],
        "lo_m2": [("pi_m2a", 2.0)],
        "lo_r1": [("pi_r1a", 2.0), ("pi_r1b", 2.0)],
        "lo_p1": [("pi_p1a", 3.0), ("pi_p1b", 3.0)],
    }
    return create_daily_plan_vault(tmp_path / "vault", learning_objects=los, **kwargs)


def _wide_items():
    return [
        scheduled("pi_r1a", "lo_r1", recent_error=0.5),
        scheduled("pi_r1b", "lo_r1", recent_error=0.5),
        scheduled("pi_m1a", "lo_m1", forgetting_risk=0.6),
        scheduled("pi_m1b", "lo_m1", forgetting_risk=0.6),
        scheduled("pi_m2a", "lo_m2", forgetting_risk=0.6),
        scheduled("pi_eig_easy", "lo_eigen_basics", new_material=1.0),
        scheduled("pi_eig_mid", "lo_eigen_basics", new_material=1.0),
        scheduled("pi_diag_easy", "lo_diag", new_material=1.0),
        scheduled("pi_p1a", "lo_p1", goal_frontier=0.4),
        scheduled("pi_p1b", "lo_p1", goal_frontier=0.4),
    ]


def _seed_wide(repository):
    for item in ("pi_r1a", "pi_r1b", "pi_p1a", "pi_p1b"):
        seed_due(repository, item, due=FUTURE, last=LAST)
    for item in ("pi_m1a", "pi_m1b", "pi_m2a"):
        seed_due(repository, item, due=PAST, last=LAST)
    # lo_r1 is the repair LO: an open diagnosed problem (owner decision
    # 2026-10-12), not just its recent errors.
    seed_open_problem(repository, "lo_r1")
