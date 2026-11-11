"""What other test files use from ``tests/test_ro5_calibration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.algorithm_versions import ROUTER_CALIBRATION_ALGORITHM_VERSION
from learnloop.daily_plan.policy import policy_for

from tests.daily_plan_fakes import iso


TAG = ROUTER_CALIBRATION_ALGORITHM_VERSION


def _new_session(env, runtime, day: int) -> str:
    session_id = f"s{day}"
    with env.repository.connection() as connection:
        connection.execute("INSERT INTO sessions(id, started_at) VALUES (?, ?)", (session_id, iso(env.clock.now())))
        connection.commit()
    env.session_id = session_id
    env.policy = policy_for(env.vault, env.repository, session_id=session_id, clock=env.clock, runtime=runtime,
                            serve=True)
    return session_id


def _end_session(env, session_id: str) -> None:
    with env.repository.connection() as connection:
        connection.execute("UPDATE sessions SET ended_at = ? WHERE id = ?", (iso(env.clock.now()), session_id))
        connection.commit()


def _week_env(tmp_path, runtime):
    """A copy-shaped vault: six practised topics (each with one item in memory, due or not) and four unseen items
    each, the shape of a real vault where new items wait in the pool."""

    from datetime import timedelta

    from tests.daily_plan_fakes import MovableClock, NOW, make_env, scheduled, seed_due
    from tests.helpers import create_daily_plan_vault

    los = {f"lo_{name}": [(f"pi_{name}{i}", 2.0) for i in range(5)] for name in "abcdef"}
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=los, version=TAG)
    items = []
    for index, (lo, entries) in enumerate(los.items()):
        items.append(scheduled(entries[0][0], lo, forgetting_risk=0.6 - 0.05 * index))
        items += [scheduled(item_id, lo, new_material=1.0) for item_id, _minutes in entries[1:]]
    env = make_env(paths.root, items, clock=MovableClock(), session_id=None)
    for index, (lo, entries) in enumerate(los.items()):
        due = NOW - timedelta(days=1) if index % 2 == 0 else NOW + timedelta(days=3)
        seed_due(env.repository, entries[0][0], due=due, last=NOW - timedelta(days=5))
    env.policy = policy_for(env.vault, env.repository, session_id=None, clock=env.clock, runtime=runtime, serve=True)
    return env


def _grade_answers(env, day: int) -> None:
    """The fake run records ungraded answers; a real day's are graded. Each answer of the day graded correct or not
    from a seeded draw (a synthetic learner at about 70%), so the checks resolve to labels (Codex review F1: an
    ungraded answer is no label)."""

    import random

    rng = random.Random(f"ro5-week-{day}")
    with env.repository.connection() as connection:
        ids = [row[0] for row in connection.execute(
            "SELECT id FROM practice_attempts WHERE correctness IS NULL ORDER BY created_at, id")]
        for attempt_id in ids:
            connection.execute("UPDATE practice_attempts SET correctness = ? WHERE id = ?",
                               (1.0 if rng.random() < 0.7 else 0.0, attempt_id))
        connection.commit()
