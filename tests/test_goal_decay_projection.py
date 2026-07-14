"""B4 decay-projection series: monotone do-nothing decay, held-flat exclusion
with honest coverage counts, a fixture golden, and the zero-coverage case that
lets the UI suppress the projection (spec §4.1)."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.goal_projection import goal_report, projected_ready_mean_at
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, create_basic_vault, seed_due_item

FIXTURE_VAULT = Path(__file__).resolve().parents[1] / "fixtures" / "linear_algebra"


def _add_application_item(root) -> None:
    """A second active item on the same LO whose facet has no FSRS state."""

    upsert_practice_item(
        root,
        {
            "id": "pi_svd_apply_001",
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["application"],
            "evidence_weights": {"application": 1.0},
            "prompt": "Apply SVD to compress a matrix.",
            "expected_answer": "Truncate to the top singular values.",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
                "fatal_errors": [],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=FrozenClock(NOW),
    )


def test_do_nothing_projection_is_monotone_non_increasing_for_decay_facets(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)  # gives the recall facet FSRS stability
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    goal = vault.goals[0]

    means = []
    for days in (1, 3, 7, 14, 30, 60):
        mean, estimated, held = projected_ready_mean_at(
            vault, repository, goal, NOW + timedelta(days=days), clock=FrozenClock(NOW)
        )
        assert mean is not None
        assert estimated == 1
        assert held == 0
        means.append(mean)
    assert means == sorted(means, reverse=True)
    assert means[-1] < means[0]


def test_held_flat_facets_are_excluded_from_the_curve_but_counted(tmp_path):
    # Vault A: decay-estimated recall facet only.
    root_a = tmp_path / "vault_a"
    paths_a = create_basic_vault(root_a)
    seed_due_item(paths_a)
    vault_a = load_vault(root_a)
    repo_a = Repository(paths_a.sqlite_path)

    # Vault B: same, plus an application facet with no FSRS information.
    root_b = tmp_path / "vault_b"
    paths_b = create_basic_vault(root_b)
    seed_due_item(paths_b)
    _add_application_item(root_b)
    vault_b = load_vault(root_b)
    repo_b = Repository(paths_b.sqlite_path)

    at = NOW + timedelta(days=14)
    mean_a, estimated_a, held_a = projected_ready_mean_at(
        vault_a, repo_a, vault_a.goals[0], at, clock=FrozenClock(NOW)
    )
    mean_b, estimated_b, held_b = projected_ready_mean_at(
        vault_b, repo_b, vault_b.goals[0], at, clock=FrozenClock(NOW)
    )
    # Coverage is disclosed...
    assert (estimated_a, held_a) == (1, 0)
    assert (estimated_b, held_b) == (1, 1)
    # ...and the held-flat facet never enters the curve: the projected mean is
    # identical with or without it.
    assert mean_b == pytest.approx(mean_a)

    report = goal_report(vault_b, repo_b, vault_b.goals[0], clock=FrozenClock(NOW))
    assert report.decay_estimated_count == 1
    assert report.held_flat_count == 1
    by_facet = {facet.facet_id: facet for facet in report.facets}
    assert by_facet["recall"].decay_estimated is True
    assert by_facet["application"].decay_estimated is False


def test_goal_with_zero_decay_estimated_facets_reports_suppressible_coverage(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)  # no FSRS state anywhere
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    goal = vault.goals[0]

    report = goal_report(vault, repository, goal, clock=FrozenClock(NOW))
    assert report.total > 0
    assert report.decay_estimated_count == 0
    assert report.held_flat_count == report.total

    mean, estimated, held = projected_ready_mean_at(
        vault, repository, goal, NOW + timedelta(days=14), clock=FrozenClock(NOW)
    )
    # No decay information is not evidence of no decay: the projection is None
    # and coverage says why, so the UI can suppress the dotted line entirely.
    assert mean is None
    assert estimated == 0
    assert held == report.total


def test_linear_algebra_fixture_golden_projection(tmp_path):
    """Pinned golden over the real fixture vault (state.sqlite as committed)."""

    root = tmp_path / "linear_algebra"
    shutil.copytree(FIXTURE_VAULT, root)
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    now = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    goal = vault.goals[0]
    assert goal.id == "goal_symmetric_matrices_and_variance"

    report = goal_report(vault, repository, goal, clock=FrozenClock(now))
    assert report.total == 21
    assert report.decay_estimated_count == 18
    assert report.held_flat_count == 3
    assert report.predicted_recall_mean == pytest.approx(0.5070636822913404)
    assert report.ready_current_mean == pytest.approx(0.5374934018174398)

    golden = {
        1: 0.5349885290787593,
        7: 0.5255922504720373,
        14: 0.5168249031187426,
        30: 0.5013334479727833,
    }
    for days, expected in golden.items():
        mean, estimated, held = projected_ready_mean_at(
            vault, repository, goal, now + timedelta(days=days), clock=FrozenClock(now)
        )
        assert (estimated, held) == (18, 3)
        assert mean == pytest.approx(expected)
    # The golden series itself is monotone non-increasing.
    values = list(golden.values())
    assert values == sorted(values, reverse=True)
