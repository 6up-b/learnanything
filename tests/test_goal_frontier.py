from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.scheduler import build_due_queue
from learnloop.services.selection_rewards import SchedulerIntent, score_selection_reward
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_concept, upsert_learning_object, upsert_practice_item
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import ALGORITHM_VERSION, NOW, NOW_ISO, create_basic_vault, seed_due_item

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"


def _loaded(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = seed_due_item(paths)
    return load_vault(vault_root), paths, repository


def _upsert_uncertainty(repository, *, status: str, top_label: str, opened_by_attempt_id: str) -> None:
    solid = 0.3 if top_label != "facet_solid:recall" else 0.7
    repository.upsert_facet_uncertainty_state(
        {
            "learning_object_id": LO_ID,
            "facet_id": "recall",
            "hypothesis_marginal": {"facet_solid:recall": solid, "facet_absent:recall": 1.0 - solid},
            "uncertainty": 0.5,
            "status": status,
            "opened_by_attempt_id": opened_by_attempt_id,
            "opened_reason": "low_facet_outcome",
            "last_evidence_at": NOW_ISO,
            "algorithm_version": ALGORITHM_VERSION,
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )


def test_unexamined_facet_on_goal_frontier_scales_by_goal_priority(tmp_path):
    vault, _paths, repository = _loaded(tmp_path)

    queue = build_due_queue(vault, repository, clock=FrozenClock(NOW), persist_explanations=False)

    item = queue[0]
    # Facet "recall" has no evidence -> unexamined -> on the frontier; the
    # basic vault goal's scope contains the LO with priority 0.8.
    assert item.components["goal_frontier"] == pytest.approx(0.8)
    assert "active_goal" not in item.components
    config = vault.config.scheduler
    expected_priority = (
        config.forgetting_risk_weight * item.components["forgetting_risk"]
        + config.goal_frontier_weight * 0.8
    )
    assert item.priority == pytest.approx(expected_priority)
    assert "goal frontier weight 0.80" in item.plain_english


def test_known_gap_and_uncertain_facets_are_both_on_frontier(tmp_path):
    # Frontier semantics widened: a facet is "not on track" when unexamined,
    # uncertain, or a known gap (or solid-but-projected-below-target). Both a
    # resolved known-gap and an open/uncertain facet are therefore on the frontier.
    vault, _paths, repository = _loaded(tmp_path)
    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM_ID,
            learner_answer_md="SVD factorizes into U Sigma V^T.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW),
    )

    _upsert_uncertainty(
        repository, status="resolved", top_label="facet_absent:recall", opened_by_attempt_id=result.attempt_id
    )
    queue = build_due_queue(vault, repository, clock=FrozenClock(NOW), persist_explanations=False)
    # The raw frontier weight (goal priority 0.8) is multiplied by the same-item
    # exposure discount because the item was just attempted above.
    exposure = queue[0].components["goal_frontier_exposure_discount"]
    assert 0.0 < exposure < 1.0
    assert queue[0].components["goal_frontier"] == pytest.approx(0.8 * exposure)

    _upsert_uncertainty(
        repository, status="open", top_label="facet_absent:recall", opened_by_attempt_id=result.attempt_id
    )
    queue = build_due_queue(vault, repository, clock=FrozenClock(NOW), persist_explanations=False)
    # Uncertain now counts as not-on-track (previously excluded).
    assert queue[0].components["goal_frontier"] == pytest.approx(0.8 * exposure)


def test_no_active_goals_means_no_goal_frontier(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    write_yaml(paths.goals_path, {"schema_version": 1, "goals": []})
    repository = seed_due_item(paths)
    vault = load_vault(vault_root)

    queue = build_due_queue(vault, repository, clock=FrozenClock(NOW), persist_explanations=False)

    assert queue[0].components["goal_frontier"] == 0.0
    assert "active_goal" not in queue[0].components


def test_repair_reward_includes_goal_frontier_term(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items[ITEM_ID]
    learning_object = vault.learning_objects[LO_ID]
    mastery = MasteryState(
        learning_object_id=LO_ID,
        logit_mean=0.0,
        logit_variance=1.0,
        evidence_count=1,
        last_evidence_at=NOW_ISO,
        algorithm_version=ALGORITHM_VERSION,
        updated_at=NOW_ISO,
    )

    def reward(goal_frontier: float) -> float:
        return score_selection_reward(
            vault,
            item,
            learning_object,
            mastery=mastery,
            facet_states=[],
            quality_state=None,
            active_errors=[],
            base_components={"recent_error": 0.0, "goal_frontier": goal_frontier},
            probe_eig=0.0,
            intent=SchedulerIntent.REPAIR,
        ).selection_reward

    on_goal = reward(0.8)
    off_goal = reward(0.0)
    assert on_goal - off_goal == pytest.approx(0.15 * 0.8)


def _add_offgoal_lo_and_items(vault_root, repository, *, count: int) -> list[str]:
    """A second concept outside the goal scope with ``count`` due, non-goal items."""

    upsert_concept(vault_root, "matrix_rank", {"title": "Matrix rank", "type": "concept"}, clock=FrozenClock(NOW))
    upsert_learning_object(
        vault_root,
        {
            "id": "lo_rank",
            "title": "Matrix rank",
            "subjects": ["linear-algebra"],
            "concept": "matrix_rank",
            "knowledge_type": "fact",
            "summary": "The rank of a matrix.",
        },
        clock=FrozenClock(NOW),
    )
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id="lo_rank",
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=1,
            last_evidence_at="2026-05-18T12:00:00Z",
            algorithm_version=ALGORITHM_VERSION,
            updated_at=NOW_ISO,
        )
    )
    item_ids: list[str] = []
    for index in range(count):
        item_id = f"pi_rank_{index:03d}"
        upsert_practice_item(
            vault_root,
            {
                "id": item_id,
                "learning_object_id": "lo_rank",
                "subjects": None,
                "practice_mode": "short_answer",
                "attempt_types_allowed": ["independent_attempt"],
                "evidence_facets": ["recall"],
                "evidence_weights": {"recall": 1.0},
                "prompt": f"State the rank fact {index}.",
                "expected_answer": "Rank equals number of independent rows.",
                "grading_rubric": {
                    "max_points": 4,
                    "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
                    "fatal_errors": [],
                },
            },
            clock=FrozenClock(NOW),
        )
        repository.upsert_practice_item_state(
            item_id,
            difficulty=5.0,
            stability=1.0,
            due_at="2026-05-17T12:00:00Z",
            last_attempt_at="2026-05-15T12:00:00Z",
            active=True,
        )
        item_ids.append(item_id)
    return item_ids


def test_goal_quota_guarantees_floor_share_at_top_of_queue(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = seed_due_item(paths)  # pi_svd_define_001 is the goal-frontier item
    _add_offgoal_lo_and_items(vault_root, repository, count=4)
    vault = load_vault(vault_root)

    queue = build_due_queue(vault, repository, clock=FrozenClock(NOW), persist_explanations=False)

    def is_goal(item) -> bool:
        return item.components.get("goal_frontier", 0.0) > 0

    goal_items = [item for item in queue if is_goal(item)]
    non_goal_items = [item for item in queue if not is_goal(item)]
    assert goal_items and non_goal_items  # a genuine mix

    # Goal has no due date -> quota floor is goal_quota_floor_min (0.30).
    floor = vault.config.scheduler.goal_quota_floor_min
    assert floor == pytest.approx(0.30)

    # Floor holds at every prefix while goal items remain in the tail.
    for k in range(1, len(queue) + 1):
        prefix_goal = sum(1 for item in queue[:k] if is_goal(item))
        tail_has_goal = any(is_goal(item) for item in queue[k:])
        assert prefix_goal >= floor * k or not tail_has_goal

    # With floor > 0 and a goal item available, position 1 is a goal item.
    assert is_goal(queue[0])


def test_cold_start_lo_on_frontier_is_schedulable(tmp_path):
    # A never-attempted LO inside an active goal's scope has all its facets
    # unexamined -> at risk -> on the frontier. The scheduler's cold-start
    # gate must not drop its items, or "practice at-risk facets" can never
    # serve the goal's untouched material. No seed_due_item here: no mastery
    # row, no item state — the LO is genuinely cold.
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    vault = load_vault(vault_root)

    queue = build_due_queue(vault, repository, clock=FrozenClock(NOW), persist_explanations=False)

    frontier_ids = [
        item.practice_item_id
        for item in queue
        if item.components.get("goal_frontier", 0.0) > 0
    ]
    assert ITEM_ID in frontier_ids
