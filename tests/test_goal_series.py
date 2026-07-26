from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services import goal_series
from learnloop.services.goal_series import goal_report_series
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault, seed_due_item

ITEM_ID = "pi_svd_define_001"


def _loaded(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = seed_due_item(paths)
    return load_vault(vault_root), repository


def test_series_reflects_evidence_arriving_over_time(tmp_path):
    vault, repository = _loaded(tmp_path)
    goal = vault.goals[0]

    # Evidence lands 8 days after goal creation.
    attempt_at = NOW + timedelta(days=8)
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM_ID,
            learner_answer_md="SVD factorizes into U Sigma V^T.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(attempt_at),
    )

    series = goal_report_series(
        vault, repository, goal, clock=FrozenClock(NOW + timedelta(days=10))
    )

    assert len(series) >= 2
    # All points measure the same scope.
    totals = {point.total for point in series}
    assert len(totals) == 1 and totals.pop() > 0
    # The first checkpoint (goal creation) predates the attempt: replay of the
    # truncated log must show no on-track facets there.
    assert series[0].on_track_count == 0
    # Points are chronological and the last one is the live report.
    ats = [point.at for point in series]
    assert ats == sorted(ats)
    payload = series[0].as_dict()
    assert set(payload) == {
        "at",
        "on_track_count",
        "total",
        "on_track_fraction",
        "certified_count",
        "examined_count",
        "attainment_fraction",
        "predicted_recall_mean",
        "demonstrated_count",
        "ready_mean",
        "projected_ready_mean",
        "projection",
        "decay_estimated",
        "held_flat",
    }


def test_series_replays_past_non_cascading_attempt_references(tmp_path):
    """Rows referencing attempts with NO ACTION must not break checkpoint truncation."""

    vault, repository = _loaded(tmp_path)
    goal = vault.goals[0]

    attempt_at = NOW + timedelta(days=8)
    attempt = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM_ID,
            learner_answer_md="SVD factorizes into U Sigma V^T.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(attempt_at),
    )
    repository.insert_attempt_submission_receipt(
        submission_id="sub_goal_series_001",
        attempt_id=attempt.attempt_id,
        practice_item_id=ITEM_ID,
        result={"ok": True},
        clock=FrozenClock(attempt_at),
    )

    series = goal_report_series(
        vault, repository, goal, clock=FrozenClock(NOW + timedelta(days=10))
    )

    assert series[0].on_track_count == 0
    # The live receipt survives; only the scratch copy is truncated.
    assert repository.attempt_submission_receipt("sub_goal_series_001") is not None


def test_series_shares_one_replay_across_unchanged_checkpoints(tmp_path, monkeypatch):
    vault, repository = _loaded(tmp_path)
    goal = vault.goals[0]

    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM_ID,
            learner_answer_md="SVD factorizes into U Sigma V^T.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW + timedelta(days=8)),
    )

    rebuilds = []
    real_rebuild = goal_series.rebuild_derived_state

    def counted_rebuild(*args, **kwargs):
        rebuilds.append(kwargs.get("clock"))
        return real_rebuild(*args, **kwargs)

    monkeypatch.setattr(goal_series, "rebuild_derived_state", counted_rebuild)

    series = goal_report_series(
        vault, repository, goal, clock=FrozenClock(NOW + timedelta(days=30))
    )

    # Checkpoints at days 0, 7, 14, 21, 28 (+ the live point at day 30). The
    # attempt lands on day 8, so days 0-7 share one replay and days 14-28 another.
    assert len(series) == 6
    assert len(rebuilds) == 2
    # The shared replay still reports per checkpoint: evidence appears on day 14,
    # and decay keeps moving between checkpoints inside a group.
    assert [point.examined_count for point in series[:5]] == [0, 0, 1, 1, 1]
    assert series[2].predicted_recall_mean != series[3].predicted_recall_mean


def test_series_caps_points_and_keeps_recent_window(tmp_path):
    vault, repository = _loaded(tmp_path)
    goal = vault.goals[0]

    series = goal_report_series(
        vault,
        repository,
        goal,
        clock=FrozenClock(NOW + timedelta(days=365)),
        interval_days=7,
        max_points=6,
    )

    assert len(series) == 6
    assert series[-1].at == (NOW + timedelta(days=365)).astimezone(series[-1].at.tzinfo)
