from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.goals.exam_pool import (
    release_exam_pool,
    reserve_exam_pool,
    reserved_item_ids,
)
from learnloop.scheduling.scheduler import read_due_queue
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO
from tests.exam_pool_helpers import _add_item, _vault_with_items

GOAL_ID = "goal_linear_algebra_ml"


def test_reservation_covers_scope_facets_and_strata(tmp_path):
    vault, _paths, repository = _vault_with_items(tmp_path)
    goal = vault.goals[0]

    report = reserve_exam_pool(vault, repository, goal, item_count=3, clock=FrozenClock(NOW))
    assert not report.already_reserved
    assert len(report.reserved_item_ids) == 3
    # Greedy coverage picks the three distinct-facet items before the recall dup.
    assert set(report.covered_facets) == {"recall", "apply", "derive"}
    assert "pi_pool_recall_dup" not in report.reserved_item_ids
    # Difficulty stratification spans low/mid/high.
    assert set(report.strata) == {"low", "mid", "high"}


def test_reservation_is_idempotent_per_goal(tmp_path):
    vault, _paths, repository = _vault_with_items(tmp_path)
    goal = vault.goals[0]

    first = reserve_exam_pool(vault, repository, goal, item_count=3, clock=FrozenClock(NOW))
    second = reserve_exam_pool(vault, repository, goal, item_count=3, clock=FrozenClock(NOW))
    assert second.already_reserved
    assert set(second.reserved_item_ids) == set(first.reserved_item_ids)
    # No duplicate rows were written.
    assert len(repository.reserved_exam_pool_items(GOAL_ID)) == 3


def test_only_never_attempted_items_are_reservable(tmp_path):
    vault, _paths, repository = _vault_with_items(tmp_path)
    goal = vault.goals[0]
    # Attempt one candidate: it must not be reserved.
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_pool_apply_mid", learner_answer_md="x", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 4.0}, confidence=4),
        clock=FrozenClock(NOW),
    )

    report = reserve_exam_pool(vault, repository, goal, item_count=5, clock=FrozenClock(NOW))
    assert "pi_pool_apply_mid" not in report.reserved_item_ids
    # 'apply' can only be tested by the now-attempted item, so it's uncovered.
    assert "apply" in report.uncovered_facets


def test_uncovered_facets_reported_when_no_item_tests_a_facet(tmp_path):
    vault, _paths, repository = _vault_with_items(tmp_path)
    # Scope includes any facet required by SVD LO items; add an item requiring a
    # facet, then attempt it so nothing reservable can test it.
    _add_item(tmp_path / "vault", "pi_pool_prove", facets=["prove"], difficulty=0.5)
    vault = load_vault(tmp_path / "vault")
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_pool_prove", learner_answer_md="x", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 4.0}, confidence=4),
        clock=FrozenClock(NOW),
    )
    report = reserve_exam_pool(vault, repository, vault.goals[0], item_count=5, clock=FrozenClock(NOW))
    assert "prove" in report.uncovered_facets


def test_scheduler_skips_reserved_items(tmp_path):
    vault, _paths, repository = _vault_with_items(tmp_path)
    goal = vault.goals[0]
    # Make the pool items schedulable-eligible by seeding LO evidence (already
    # seeded via seed_due_item) and past-due states.
    for item_id in ("pi_pool_recall_easy", "pi_pool_apply_mid", "pi_pool_derive_hard"):
        repository.upsert_practice_item_state(
            item_id, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
            last_attempt_at="2026-05-16T12:00:00Z", active=True,
        )
    before = {item.practice_item_id for item in read_due_queue(vault, repository, clock=FrozenClock(NOW))}
    assert "pi_pool_recall_easy" in before

    reserve_exam_pool(vault, repository, goal, item_count=3, clock=FrozenClock(NOW))
    reserved = reserved_item_ids(repository)
    assert reserved

    after = {item.practice_item_id for item in read_due_queue(vault, repository, clock=FrozenClock(NOW))}
    assert reserved.isdisjoint(after)


def test_release_frees_items(tmp_path):
    vault, _paths, repository = _vault_with_items(tmp_path)
    goal = vault.goals[0]
    reserve_exam_pool(vault, repository, goal, item_count=3, clock=FrozenClock(NOW))
    assert reserved_item_ids(repository)

    freed = release_exam_pool(repository, GOAL_ID)
    assert len(freed) == 3
    assert reserved_item_ids(repository) == set()
    # A re-reserve is possible after release (items are reservable again).
    again = reserve_exam_pool(vault, repository, goal, item_count=3, clock=FrozenClock(NOW))
    assert not again.already_reserved
    assert len(again.reserved_item_ids) == 3


def test_item_in_at_most_one_unreleased_pool(tmp_path):
    vault, _paths, repository = _vault_with_items(tmp_path)
    # Reserve for the goal; then a second goal cannot re-reserve the same items.
    reserve_exam_pool(vault, repository, vault.goals[0], item_count=3, clock=FrozenClock(NOW))
    reserved_first = repository.reserved_exam_pool_item_ids()

    from learnloop.vault.models import Goal

    other = Goal(
        id="goal_other",
        title="Other",
        target_recall=0.8,
        facet_scope={"concepts": ["singular_value_decomposition"]},
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
    )
    report = reserve_exam_pool(vault, repository, other, item_count=3, clock=FrozenClock(NOW))
    assert set(report.reserved_item_ids).isdisjoint(reserved_first)
