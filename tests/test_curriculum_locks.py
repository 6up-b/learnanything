from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.curriculum_locks import (
    Operation,
    can_apply,
    identity_locks,
)
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, create_basic_vault, write_facets


def _registered(paths):
    write_facets(
        paths,
        [{"id": "recall", "kind": "definition", "claim": "SVD factorization definition."}],
    )


def test_unlocked_facet_merge_is_legal_with_review(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    # Remove the goal so no certified scope locks the facet.
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    _registered(paths)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    result = can_apply(
        vault, repository, Operation(op_type="facet_merge", entity_type="facet", entity_id="recall")
    )
    assert result.legal is True
    assert result.requires_review is True
    assert result.lock_reasons == []


def test_locked_semantic_merge_is_invalid(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    _registered(paths)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    # Accrue attempt evidence against the facet -> history is load-bearing.
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="SVD is U Sigma V^T.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, fatal_errors=[], confidence=4),
        clock=clock,
    )
    result = can_apply(
        vault, repository, Operation(op_type="facet_merge", entity_type="facet", entity_id="recall")
    )
    assert result.legal is False
    assert any(reason.source == "attempts" for reason in result.lock_reasons)


def test_goal_scope_locks_facet(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")  # goal scopes the SVD concept
    _registered(paths)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    result = can_apply(
        vault, repository, Operation(op_type="facet_split", entity_type="facet", entity_id="recall")
    )
    assert result.legal is False
    assert any(reason.source == "goal_certified_scope" for reason in result.lock_reasons)


def test_rename_alias_is_always_sanctioned(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")  # goal + no attempts
    _registered(paths)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    result = can_apply(
        vault, repository, Operation(op_type="rename_alias", entity_type="facet", entity_id="recall")
    )
    assert result.legal is True
    assert result.lock_reasons == []


def test_identity_locks_read_adapter(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")  # goal scopes the facet -> locked
    _registered(paths)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    locks = identity_locks(vault, repository)
    assert "recall" in locks
    assert locks["recall"]


def test_locked_facet_refuses_merge_on_surface_groups(tmp_path):
    """KM2 §3.4: direct evidence spanning >= facet_surface_groups distinct
    surface/correlation groups locks the facet against merge."""

    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    _registered(paths)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    repository.replace_canonical_facet_state(
        recall_rows=[
            {
                "facet_id": "recall",
                "capability_key": "retrieval",
                "practice_item_id": None,
                "recall_alpha": 2.0,
                "recall_beta": 1.0,
                "recall_mean": 0.66,
                "recall_variance": 0.05,
                "independent_evidence_mass": 0.5,
            }
        ],
        capability_rows=[
            {
                "facet_id": "recall",
                "capability": "retrieval",
                "direct_positive_mass": 1.0,
                "certification_credit": 1.0,
                "independent_surface_groups": ["group_a", "group_b"],
            }
        ],
        algorithm_version="mvp-0.7",
    )
    result = can_apply(
        vault, repository, Operation(op_type="facet_merge", entity_type="facet", entity_id="recall")
    )
    assert result.legal is False
    assert any(r.source == "independent_surface_groups" for r in result.lock_reasons)


def test_locked_facet_refuses_merge_on_independent_mass(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    _registered(paths)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    repository.replace_canonical_facet_state(
        recall_rows=[
            {
                "facet_id": "recall",
                "capability_key": "retrieval",
                "practice_item_id": None,
                "recall_alpha": 3.0,
                "recall_beta": 1.0,
                "recall_mean": 0.75,
                "recall_variance": 0.04,
                "independent_evidence_mass": 2.5,  # >= facet_lock_mass (2.0)
            }
        ],
        capability_rows=[
            {
                "facet_id": "recall",
                "capability": "retrieval",
                "direct_positive_mass": 2.5,
                "independent_surface_groups": ["only_one_group"],
            }
        ],
        algorithm_version="mvp-0.7",
    )
    result = can_apply(
        vault, repository, Operation(op_type="facet_merge", entity_type="facet", entity_id="recall")
    )
    assert result.legal is False
    assert any(r.source == "independent_mass" for r in result.lock_reasons)


def test_prelock_facet_with_single_surface_group_still_mergeable(tmp_path):
    """One surface group and sub-threshold mass keeps a facet in the grace
    window: merge is legal-with-review (§3.4)."""

    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    _registered(paths)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    repository.replace_canonical_facet_state(
        recall_rows=[
            {
                "facet_id": "recall",
                "capability_key": "retrieval",
                "practice_item_id": None,
                "recall_alpha": 1.5,
                "recall_beta": 1.0,
                "recall_mean": 0.6,
                "recall_variance": 0.06,
                "independent_evidence_mass": 0.5,
            }
        ],
        capability_rows=[
            {
                "facet_id": "recall",
                "capability": "retrieval",
                "direct_positive_mass": 0.5,
                "independent_surface_groups": ["only_one_group"],
            }
        ],
        algorithm_version="mvp-0.7",
    )
    result = can_apply(
        vault, repository, Operation(op_type="facet_merge", entity_type="facet", entity_id="recall")
    )
    assert result.legal is True
    assert result.requires_review is True


def test_deactivate_locked_learning_object_is_invalid(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    _registered(paths)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="SVD is U Sigma V^T.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, fatal_errors=[], confidence=4),
        clock=clock,
    )
    result = can_apply(
        vault,
        repository,
        Operation(op_type="deactivate", entity_type="learning_object", entity_id="lo_svd_definition"),
    )
    assert result.legal is False
    assert any(reason.source == "attempts" for reason in result.lock_reasons)
