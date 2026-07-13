from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.services.goal_pace import PACE_WINDOW_DAYS, compute_goal_pace
from learnloop.services.goal_projection import FacetProjection, GoalReport, goal_report
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault, seed_due_item

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"


def _loaded(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = seed_due_item(paths)
    return load_vault(vault_root), repository


def _insert_attempt(repository, attempt_id: str, created_at: str) -> None:
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO practice_attempts
              (id, practice_item_id, learning_object_id, practice_mode, attempt_type, hints_used, created_at)
            VALUES (?, ?, ?, ?, 'independent_attempt', 0, ?)
            """,
            (attempt_id, ITEM_ID, LO_ID, "short_answer", created_at),
        )
        connection.commit()


def _iso(days_ago: float) -> str:
    return (NOW - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_daily_attempt_counts_is_zero_filled_and_buckets_by_day(tmp_path):
    _vault, repository = _loaded(tmp_path)
    _insert_attempt(repository, "attempt_a", _iso(1))
    _insert_attempt(repository, "attempt_b", _iso(1.1))
    _insert_attempt(repository, "attempt_c", _iso(3))
    _insert_attempt(repository, "attempt_old", _iso(PACE_WINDOW_DAYS + 5))  # outside window

    counts = repository.daily_attempt_counts(days=PACE_WINDOW_DAYS, clock=FrozenClock(NOW))
    assert len(counts) == PACE_WINDOW_DAYS
    assert sum(counts.values()) == 3
    assert max(counts.values()) == 2
    assert min(counts.values()) == 0  # idle days present


def test_compute_goal_pace_with_due_date(tmp_path):
    vault, repository = _loaded(tmp_path)
    goal = vault.goals[0]
    goal.due_at = (NOW + timedelta(days=5)).isoformat()
    _insert_attempt(repository, "attempt_a", _iso(1))
    _insert_attempt(repository, "attempt_b", _iso(2))

    report = goal_report(vault, repository, goal, clock=FrozenClock(NOW))
    pace = compute_goal_pace(vault, repository, goal, report, clock=FrozenClock(NOW))

    assert pace.attempts_last_14d == 2
    assert pace.attempts_per_day == pytest.approx(2 / PACE_WINDOW_DAYS)
    assert pace.days_left == pytest.approx(5.0, abs=0.01)
    assert pace.attempts_remaining == report.attempts_remaining
    assert pace.needed_per_day == pytest.approx(report.attempts_remaining / 5.0, rel=0.01)
    assert pace.on_pace is (pace.attempts_per_day >= pace.needed_per_day)
    assert pace.attempts_logged == 2  # both raw attempts are on the scope LO


def test_compute_goal_pace_open_ended(tmp_path):
    vault, repository = _loaded(tmp_path)
    goal = vault.goals[0]
    assert goal.due_at is None

    report = goal_report(vault, repository, goal, clock=FrozenClock(NOW))
    pace = compute_goal_pace(vault, repository, goal, report, clock=FrozenClock(NOW))

    assert pace.days_left is None
    assert pace.needed_per_day is None
    assert pace.on_pace is None
    assert pace.attempts_remaining == report.attempts_remaining


def test_unknowable_remaining_surfaces_as_none(tmp_path):
    vault, repository = _loaded(tmp_path)
    goal = vault.goals[0]
    facet = FacetProjection(
        learning_object_id=LO_ID,
        facet_id="recall",
        label="unexamined",
        current_recall=None,
        projected_recall=None,
        on_track=False,
        predicted_current=0.5,
        predicted_at_horizon=0.5,
        evidence_mass=0.0,
        certified=False,
        attempts_to_certify=None,  # no supporting items anywhere
    )
    report = GoalReport(
        goal_id=goal.id,
        target_recall=goal.target_recall,
        due_at=None,
        horizon=NOW,
        facets=[facet],
    )

    pace = compute_goal_pace(vault, repository, goal, report, clock=FrozenClock(NOW))
    assert pace.attempts_remaining is None  # unknowable, not zero


def test_pace_as_dict_shape(tmp_path):
    vault, repository = _loaded(tmp_path)
    goal = vault.goals[0]
    report = goal_report(vault, repository, goal, clock=FrozenClock(NOW))
    payload = compute_goal_pace(vault, repository, goal, report, clock=FrozenClock(NOW)).as_dict()
    assert set(payload) == {
        "attempts_per_day",
        "attempts_last_14d",
        "days_left",
        "attempts_remaining",
        "needed_per_day",
        "on_pace",
        "attempts_logged",
    }
