from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.goals.exam_pool import (
    release_exam_pool,
    reserve_exam_pool,
    reserved_item_ids,
)
from learnloop.scheduling.scheduler import build_due_queue
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, create_basic_vault, seed_due_item

LO_ID = "lo_svd_definition"
GOAL_ID = "goal_linear_algebra_ml"


def _add_item(root, item_id, *, facets, difficulty=0.5, surface_family=None, mode="short_answer"):
    upsert_practice_item(
        root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": mode,
            "attempt_types_allowed": ["independent_attempt", "dont_know"],
            "evidence_facets": facets,
            "evidence_weights": {facet: 1.0 for facet in facets},
            "prompt": f"Prompt {item_id}.",
            "expected_answer": "Answer.",
            "difficulty": difficulty,
            "surface_family": surface_family,
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


def _vault_with_items(tmp_path):
    """Basic vault + several never-attempted items covering the goal's facets.

    The goal's scope is the SVD concept (all facets required by its LOs). We add
    items testing 'recall', 'apply', and 'derive' so the pool has facets to cover
    and a difficulty/surface spread to stratify over.
    """

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_item(vault_root, "pi_pool_recall_easy", facets=["recall"], difficulty=0.1, surface_family="fam_a")
    _add_item(vault_root, "pi_pool_apply_mid", facets=["apply"], difficulty=0.5, surface_family="fam_b")
    _add_item(vault_root, "pi_pool_derive_hard", facets=["derive"], difficulty=0.9, surface_family="fam_c")
    _add_item(vault_root, "pi_pool_recall_dup", facets=["recall"], difficulty=0.5, surface_family="fam_a")
    repository = seed_due_item(paths)
    return load_vault(vault_root), paths, repository


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
    goal = vault.goals[0]
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
    before = {item.practice_item_id for item in build_due_queue(vault, repository, clock=FrozenClock(NOW), persist_explanations=False)}
    assert "pi_pool_recall_easy" in before

    reserve_exam_pool(vault, repository, goal, item_count=3, clock=FrozenClock(NOW))
    reserved = reserved_item_ids(repository)
    assert reserved

    after = {item.practice_item_id for item in build_due_queue(vault, repository, clock=FrozenClock(NOW), persist_explanations=False)}
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
