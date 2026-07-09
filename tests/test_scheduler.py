from __future__ import annotations

from datetime import UTC, datetime

import pytest

from learnloop.clock import FrozenClock
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import MasteryState, PracticeItemState, Repository
from learnloop.services.scheduler import (
    ScheduledItem,
    SchedulerSession,
    _rotate_same_day_frontier_repeats,
    _selection_propensities,
    build_due_queue,
)
from learnloop.services.selection_rewards import SchedulerIntent
from learnloop.vault.loader import add_subject, init_vault, load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import write_yaml
from tests.helpers import create_basic_vault


NOW = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)
NOW_ISO = "2026-05-19T12:00:00Z"


def test_scheduler_scores_due_goal_item(tmp_path):
    vault_root = tmp_path / "vault"
    clock = FrozenClock(NOW)
    init_vault(vault_root, clock=clock)
    add_subject(vault_root, "linear-algebra", "Linear Algebra", clock=clock)
    vault = load_vault(vault_root)
    paths = VaultPaths(vault.root, vault.config)

    write_yaml(
        paths.concepts_path,
        {
            "schema_version": 1,
            "concepts": {
                "singular_value_decomposition": {
                    "title": "Singular Value Decomposition",
                    "type": "procedure",
                    "aliases": ["SVD"],
                    "description": "Matrix factorization.",
                    "tags": [],
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                }
            },
        },
    )
    write_yaml(
        paths.goals_path,
        {
            "schema_version": 2,
            "goals": [
                {
                    "id": "goal_linear_algebra_ml",
                    "title": "Linear algebra for ML",
                    "status": "active",
                    "priority": 0.8,
                    "target_recall": 0.8,
                    "facet_scope": {"concepts": ["singular_value_decomposition"]},
                    "due_at": None,
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                }
            ],
        },
    )
    write_yaml(
        paths.learning_object_path("linear-algebra", "lo_svd_definition"),
        {
            "schema_version": 1,
            "id": "lo_svd_definition",
            "title": "SVD definition",
            "subjects": ["linear-algebra"],
            "concept": "singular_value_decomposition",
            "knowledge_type": "definition",
            "status": "active",
            "contradicts": None,
            "summary": "SVD factorizes a matrix into orthogonal factors and singular values.",
            "prerequisites": [],
            "confusables": [],
            "difficulty_prior": 0.55,
            "tags": [],
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_define_001"),
        {
            "schema_version": 1,
            "id": "pi_svd_define_001",
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "Define SVD.",
            "expected_answer": "A matrix factorization.",
            "difficulty": 0.55,
            "tags": [],
            "hints": [],
            "hint_policy": {"max_useful_hints": 0, "fsrs_rating_cap_by_hint": {}, "mastery_alpha_dampening_by_hint": {}},
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )

    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    repository.upsert_practice_item_state(
        "pi_svd_define_001",
        difficulty=5.0,
        stability=2.0,
        due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z",
        active=True,
        clock=clock,
    )
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id="lo_svd_definition",
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=1,
            last_evidence_at="2026-05-16T12:00:00Z",
            algorithm_version="mvp-0.1",
            updated_at=NOW_ISO,
        )
    )

    queue = build_due_queue(loaded, repository, clock=clock, persist_explanations=False)

    assert [item.practice_item_id for item in queue] == ["pi_svd_define_001"]
    assert queue[0].components["forgetting_risk"] > 0
    # Facet "recall" is unexamined -> on the goal frontier; the goal scope names
    # the LO's concept with priority 0.8 (no active_goal component anymore).
    assert queue[0].components["goal_frontier"] == pytest.approx(0.8)
    assert "active_goal" not in queue[0].components


def test_scheduler_persists_bounded_reward_debug_and_rejected_candidates(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_define_002"),
        {
            "schema_version": 1,
            "id": "pi_svd_define_002",
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "State the SVD factors.",
            "expected_answer": "U, Sigma, V transpose.",
            "difficulty": 0.55,
            "retrieval_demand": 0.8,
            "transfer_distance": 0.2,
            "scaffold_level": 0.0,
            "surface_family": "svd-definition",
            "repair_targets": ["recall"],
            "tags": [],
            "hints": [],
            "hint_policy": {"max_useful_hints": 0, "fsrs_rating_cap_by_hint": {}, "mastery_alpha_dampening_by_hint": {}},
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    loaded = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id="lo_svd_definition",
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=1,
            last_evidence_at="2026-05-16T12:00:00Z",
            algorithm_version="mvp-0.1",
            updated_at=NOW_ISO,
        )
    )
    for item_id in ("pi_svd_define_001", "pi_svd_define_002"):
        repository.upsert_practice_item_state(
            item_id,
            difficulty=5.0,
            stability=2.0,
            due_at="2026-05-18T12:00:00Z",
            last_attempt_at="2026-05-16T12:00:00Z",
            active=True,
            clock=clock,
        )

    queue = build_due_queue(loaded, repository, clock=clock, limit=1, session=SchedulerSession(session_id="s_rewards"))

    explanations = repository.latest_scheduler_explanations_by_session("s_rewards")
    slate = repository.latest_scheduler_slate_by_session("s_rewards")
    assert len(queue) == 1
    assert len(explanations) == 2
    assert slate is not None
    assert slate["candidate_count"] == 2
    assert slate["returned_count"] == 1
    candidates = repository.scheduler_slate_candidates(slate["id"])
    assert [candidate["rank"] for candidate in candidates] == [1, 2]
    assert sum(1 for candidate in candidates if candidate["was_returned"]) == 1
    assert candidates[0]["components"]["selection_reward"] == explanations[0]["components"]["selection_reward"]
    selected = [row for row in explanations if row["components"]["selected"] == 1.0]
    rejected = [row for row in explanations if row["components"]["selected"] == 0.0]
    assert len(selected) == 1
    assert len(rejected) == 1
    reward_debug = selected[0]["target_scope"]["selection_reward"]
    assert -1.0 <= selected[0]["components"]["selection_reward"] <= 1.0
    assert 0.0 <= selected[0]["components"]["predicted_correctness"] <= 1.0
    assert reward_debug["intent"] in {"practice", "repair", "transfer", "probe"}
    assert "ability_vector" in reward_debug
    assert "item_demand_vector" in reward_debug


def test_scheduler_orders_eligible_items_by_selection_reward_before_id(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_define_999"),
        {
            "schema_version": 1,
            "id": "pi_svd_define_999",
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "State the SVD factors in order.",
            "expected_answer": "U, Sigma, V transpose.",
            "difficulty": 0.55,
            "transfer_distance": 1.0,
            "tags": [],
            "hints": [],
            "hint_policy": {"max_useful_hints": 0, "fsrs_rating_cap_by_hint": {}, "mastery_alpha_dampening_by_hint": {}},
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    loaded = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id="lo_svd_definition",
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=1,
            last_evidence_at="2026-05-16T12:00:00Z",
            algorithm_version="mvp-0.1",
            updated_at=NOW_ISO,
        )
    )
    repository.upsert_practice_item_quality_state(
        {
            "practice_item_id": "pi_svd_define_001",
            "bad_item_suspicion": 0.80,
            "evidence_count": 3,
            "suspicion_reasons": ["test_quality_penalty"],
            "last_flagged_at": NOW_ISO,
            "algorithm_version": "mvp-0.1",
            "updated_at": NOW_ISO,
        }
    )
    for item_id in ("pi_svd_define_001", "pi_svd_define_999"):
        repository.upsert_practice_item_state(
            item_id,
            difficulty=5.0,
            stability=2.0,
            due_at="2026-05-18T12:00:00Z",
            last_attempt_at="2026-05-16T12:00:00Z",
            active=True,
            clock=clock,
        )

    queue = build_due_queue(loaded, repository, clock=clock, persist_explanations=False)

    rewards = {item.practice_item_id: item.components["selection_reward"] for item in queue}
    assert queue[0].practice_item_id == "pi_svd_define_999"
    assert rewards["pi_svd_define_999"] > rewards["pi_svd_define_001"]
    assert "legacy_priority" in queue[0].components

    loaded.config.scheduler.selection_exploration_rate = 1.0
    loaded.config.scheduler.selection_exploration_reward_window = 1.0
    explored = build_due_queue(
        loaded,
        repository,
        clock=clock,
        session=SchedulerSession(session_id="explore_reward_order"),
        persist_explanations=False,
    )
    explored_again = build_due_queue(
        loaded,
        repository,
        clock=clock,
        session=SchedulerSession(session_id="explore_reward_order"),
        persist_explanations=False,
    )
    assert explored[0].practice_item_id == "pi_svd_define_001"
    assert explored_again[0].practice_item_id == explored[0].practice_item_id
    assert explored[0].components["exploration_selected"] == 1.0


def test_scheduler_selects_item_on_weak_canonical_facet_boundary(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(
        paths.facets_path,
        {
            "schema_version": 1,
            "facets": [
                {
                    "id": "compute_spectral_error_from_sigma",
                    "title": "Compute spectral error from singular values",
                    "aliases": ["spectral-norm"],
                    "description": None,
                    "tags": [],
                },
                {
                    "id": "recall",
                    "title": "Recall",
                    "aliases": [],
                    "description": None,
                    "tags": [],
                },
            ],
        },
    )
    spectral_item = {
        "schema_version": 1,
        "id": "pi_spectral_boundary",
        "learning_object_id": "lo_svd_definition",
        "subjects": None,
        "practice_mode": "diagnostic_probe",
        "attempt_types_allowed": ["diagnostic_probe", "open_text", "dont_know"],
        "evidence_facets": ["spectral-norm"],
        "evidence_weights": {"spectral-norm": 1.0},
        "criterion_facet_weights": {"c_spectral": {"spectral-norm": 1.0}},
        "prompt": "For singular values 10, 6, 2, 1, what is the spectral-norm rank-2 error?",
        "expected_answer": "2",
        "difficulty": 0.55,
        "difficulty_source": "author",
        "retrieval_demand": 0.85,
        "transfer_distance": 0.1,
        "scaffold_level": 0.0,
        "surface_family": "spectral_boundary",
        "repair_targets": ["spectral-norm"],
        "tags": [],
        "hints": [],
        "hint_policy": {"max_useful_hints": 0, "fsrs_rating_cap_by_hint": {}, "mastery_alpha_dampening_by_hint": {}},
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "c_spectral", "points": 4, "description": "States the spectral error."}],
            "fatal_errors": [],
        },
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }
    write_yaml(paths.practice_item_path("linear-algebra", "pi_spectral_boundary"), spectral_item)
    loaded = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id="lo_svd_definition",
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=3,
            last_evidence_at="2026-05-16T12:00:00Z",
            algorithm_version="mvp-0.1",
            updated_at=NOW_ISO,
        )
    )
    for item_id in ("pi_svd_define_001", "pi_spectral_boundary"):
        repository.upsert_practice_item_state(
            item_id,
            difficulty=5.0,
            stability=2.0,
            due_at=None,
            last_attempt_at="2026-05-16T12:00:00Z",
            active=True,
            clock=clock,
        )
    _insert_facet_state(repository, "recall", alpha=9.0, beta=1.0)
    _insert_facet_state(repository, "spectral-norm", alpha=2.0, beta=3.0)

    queue = build_due_queue(loaded, repository, clock=clock, persist_explanations=False)

    assert queue[0].practice_item_id == "pi_spectral_boundary"
    assert queue[0].components["targeted_boundary_fit"] > 0
    assert queue[0].components["boundary_target"] > 0
    assert queue[0].reward_debug is not None
    demand = queue[0].reward_debug["item_demand_vector"]
    ability = queue[0].reward_debug["ability_vector"]
    assert demand["evidence_weights"] == {"compute_spectral_error_from_sigma": 1.0}
    assert "compute_spectral_error_from_sigma" in ability["facet_recall_mean_by_facet"]


def _insert_facet_state(repository: Repository, facet_id: str, *, alpha: float, beta: float) -> None:
    total = alpha + beta
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO evidence_facet_recall_state(
              id, learning_object_id, facet_id, practice_item_id,
              recall_alpha, recall_beta, recall_mean, recall_variance,
              independent_evidence_mass, raw_coverage_mass, last_attempt_at,
              last_error_at, consecutive_failures, algorithm_version,
              created_at, updated_at
            )
            VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"facet_{facet_id}",
                "lo_svd_definition",
                facet_id,
                alpha,
                beta,
                alpha / total,
                alpha * beta / ((total**2) * (total + 1.0)),
                total - 2.0,
                total - 2.0,
                NOW_ISO,
                NOW_ISO,
                0,
                "mvp-0.1",
                NOW_ISO,
                NOW_ISO,
            ),
        )
        connection.commit()


def test_scheduler_candidate_logs_are_retained_per_configured_limit(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    loaded = load_vault(paths.root)
    loaded.config.scheduler.candidate_log_retention_limit = 1
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id="lo_svd_definition",
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=1,
            last_evidence_at="2026-05-16T12:00:00Z",
            algorithm_version="mvp-0.1",
            updated_at=NOW_ISO,
        )
    )
    repository.upsert_practice_item_state(
        "pi_svd_define_001",
        difficulty=5.0,
        stability=2.0,
        due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z",
        active=True,
        clock=clock,
    )

    build_due_queue(loaded, repository, clock=clock, session=SchedulerSession(session_id="s_retention"))
    build_due_queue(loaded, repository, clock=clock, session=SchedulerSession(session_id="s_retention"))

    explanations = repository.latest_scheduler_explanations_by_session("s_retention")
    assert len(explanations) == 1
    assert explanations[0]["practice_item_id"] == "pi_svd_define_001"


def _scheduled(item_id: str, reward: float, *, intent: str = "practice") -> ScheduledItem:
    return ScheduledItem(
        practice_item_id=item_id,
        learning_object_id="lo",
        priority=reward,
        components={"selection_reward": reward},
        readiness_factor=None,
        selected_mode="short_answer",
        plain_english=[],
        reward_debug={"intent": intent},
    )


def _config(rate: float, window: float) -> LearnLoopConfig:
    config = LearnLoopConfig()
    config.scheduler.selection_exploration_rate = rate
    config.scheduler.selection_exploration_reward_window = window
    return config


def test_selection_propensities_epsilon_split_over_near_ties():
    # rate of probability mass goes to the best; (1 - rate) -- no, the *design* is
    # 1 - rate stays on the greedy best, rate is split uniformly over the eligible
    # near-tie alternatives. Window is wide here so both followers are eligible.
    queue = [_scheduled("a", 1.0), _scheduled("b", 0.95), _scheduled("c", 0.90)]
    propensity = _selection_propensities(queue, SchedulerSession(session_id="s"), _config(0.1, 1.0))
    assert propensity["a"] == 0.9
    assert propensity["b"] == 0.05
    assert propensity["c"] == 0.05
    assert abs(sum(propensity.values()) - 1.0) < 1e-9


def test_selection_propensities_window_excludes_far_candidates():
    # Only "b" is within the 0.10 window of the best; "c" is too far to be explored,
    # so it carries zero served-probability and "a" keeps 1 - rate.
    queue = [_scheduled("a", 1.0), _scheduled("b", 0.95), _scheduled("c", 0.50)]
    propensity = _selection_propensities(queue, SchedulerSession(session_id="s"), _config(0.2, 0.10))
    assert propensity["a"] == 0.8
    assert propensity["b"] == 0.2
    assert propensity["c"] == 0.0


def test_selection_propensities_greedy_when_disabled_or_singleton_or_probe():
    rate_off = _config(0.0, 1.0)
    queue = [_scheduled("a", 1.0), _scheduled("b", 0.95)]
    assert _selection_propensities(queue, SchedulerSession(session_id="s"), rate_off) == {"a": 1.0, "b": 0.0}

    # No session id -> no exploration (matches _apply_seeded_exploration gating).
    assert _selection_propensities(queue, SchedulerSession(session_id=None), _config(0.2, 1.0)) == {
        "a": 1.0,
        "b": 0.0,
    }

    # Single candidate -> always served.
    assert _selection_propensities([_scheduled("a", 1.0)], SchedulerSession(session_id="s"), _config(0.2, 1.0)) == {
        "a": 1.0
    }

    # A probe at the top is never displaced by exploration, so it keeps propensity 1.
    probe_queue = [_scheduled("a", 1.0, intent=SchedulerIntent.PROBE.value), _scheduled("b", 0.95)]
    assert _selection_propensities(probe_queue, SchedulerSession(session_id="s"), _config(0.2, 1.0)) == {
        "a": 1.0,
        "b": 0.0,
    }


def test_scheduler_persists_selection_propensity_and_exploration_flag(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_define_999"),
        {
            "schema_version": 1,
            "id": "pi_svd_define_999",
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "State the SVD factors in order.",
            "expected_answer": "U, Sigma, V transpose.",
            "difficulty": 0.55,
            "transfer_distance": 1.0,
            "tags": [],
            "hints": [],
            "hint_policy": {"max_useful_hints": 0, "fsrs_rating_cap_by_hint": {}, "mastery_alpha_dampening_by_hint": {}},
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    loaded = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id="lo_svd_definition",
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=1,
            last_evidence_at="2026-05-16T12:00:00Z",
            algorithm_version="mvp-0.1",
            updated_at=NOW_ISO,
        )
    )
    for item_id in ("pi_svd_define_001", "pi_svd_define_999"):
        repository.upsert_practice_item_state(
            item_id,
            difficulty=5.0,
            stability=2.0,
            due_at="2026-05-18T12:00:00Z",
            last_attempt_at="2026-05-16T12:00:00Z",
            active=True,
            clock=clock,
        )

    # Wide window so both due items are eligible near-ties -> non-degenerate propensity.
    loaded.config.scheduler.selection_exploration_rate = 0.1
    loaded.config.scheduler.selection_exploration_reward_window = 1.0
    build_due_queue(loaded, repository, clock=clock, session=SchedulerSession(session_id="s_prop"))

    slate = repository.latest_scheduler_slate_by_session("s_prop")
    candidates = repository.scheduler_slate_candidates(slate["id"])
    propensity_by_id = {row["practice_item_id"]: row["selection_propensity"] for row in candidates}
    assert all(value is not None for value in propensity_by_id.values())
    assert abs(sum(propensity_by_id.values()) - 1.0) < 1e-9
    # Exactly the candidate promoted by seeded exploration carries the realized flag.
    explored = [row["practice_item_id"] for row in candidates if row["exploration_flag"] == 1]
    assert len(explored) <= 1


# ── goal-frontier rotation (at-risk repeat fix) ──────────────────────────────


def _frontier_item(item_id: str, reward: float, frontier: float = 0.5) -> ScheduledItem:
    return ScheduledItem(
        practice_item_id=item_id,
        learning_object_id="lo_svd_definition",
        priority=reward,
        components={"goal_frontier": frontier, "selection_reward": reward},
        readiness_factor=None,
        selected_mode="short_answer",
        plain_english=[],
    )


def _item_state(item_id: str, last_attempt_at: str | None) -> PracticeItemState:
    return PracticeItemState(
        practice_item_id=item_id,
        difficulty=None,
        stability=None,
        retrievability=None,
        due_at=None,
        active=True,
        content_hash=None,
        last_attempt_at=last_attempt_at,
        updated_at=NOW_ISO,
    )


def test_frontier_items_attempted_today_rotate_behind_fresh_ones():
    queue = [
        _frontier_item("pi_repeat", 0.9),
        _frontier_item("pi_fresh", 0.7),
    ]
    item_states = {
        "pi_repeat": _item_state("pi_repeat", NOW_ISO),
        "pi_fresh": _item_state("pi_fresh", "2026-05-12T09:00:00Z"),
    }
    rotated = _rotate_same_day_frontier_repeats(queue, item_states, NOW)
    assert [item.practice_item_id for item in rotated] == ["pi_fresh", "pi_repeat"]


def test_rotation_no_op_when_all_frontier_items_attempted_today():
    queue = [
        _frontier_item("pi_a", 0.9),
        _frontier_item("pi_b", 0.7),
    ]
    item_states = {
        "pi_a": _item_state("pi_a", NOW_ISO),
        "pi_b": _item_state("pi_b", NOW_ISO),
    }
    rotated = _rotate_same_day_frontier_repeats(queue, item_states, NOW)
    assert [item.practice_item_id for item in rotated] == ["pi_a", "pi_b"]


def test_rotation_leaves_non_frontier_slots_untouched():
    non_frontier = ScheduledItem(
        practice_item_id="pi_other",
        learning_object_id="lo_svd_definition",
        priority=1.0,
        components={"goal_frontier": 0.0},
        readiness_factor=None,
        selected_mode="short_answer",
        plain_english=[],
    )
    queue = [
        _frontier_item("pi_repeat", 0.9),
        non_frontier,
        _frontier_item("pi_fresh", 0.7),
    ]
    item_states = {
        "pi_repeat": _item_state("pi_repeat", NOW_ISO),
        "pi_fresh": _item_state("pi_fresh", None),
    }
    rotated = _rotate_same_day_frontier_repeats(queue, item_states, NOW)
    assert [item.practice_item_id for item in rotated] == ["pi_fresh", "pi_other", "pi_repeat"]
