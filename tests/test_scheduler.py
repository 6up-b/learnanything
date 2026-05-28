from __future__ import annotations

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.scheduler import SchedulerSession, build_due_queue
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
            "schema_version": 1,
            "goals": [
                {
                    "id": "goal_linear_algebra_ml",
                    "title": "Linear algebra for ML",
                    "status": "active",
                    "priority": 0.8,
                    "concept_anchors": ["singular_value_decomposition"],
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
    assert queue[0].components["active_goal"] == 0.8


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
