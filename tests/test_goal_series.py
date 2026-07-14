from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
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
