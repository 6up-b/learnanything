"""``can_apply`` after facet identity locks were removed (owner, 2026-10-12).

No facet arm refuses anything any more: accrued attempt evidence, an active
goal's certified scope, independent surface groups and independent mass used
to lock a facet against merge and split; each now leaves the operation legal
and review-required. The learning-object arm (an LO with recorded attempts)
still refuses a destructive LO or practice-item operation.
"""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.curriculum.curriculum_locks import Operation, can_apply
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, create_basic_vault, write_facets


def _registered(paths):
    write_facets(
        paths,
        [{"id": "recall", "kind": "definition", "claim": "SVD factorization definition."}],
    )


def _attempt(vault, repository):
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


def _facet_state(repository, *, surface_groups, mass):
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
                "independent_evidence_mass": mass,
            }
        ],
        capability_rows=[
            {
                "facet_id": "recall",
                "capability": "retrieval",
                "direct_positive_mass": mass,
                "certification_credit": 1.0,
                "independent_surface_groups": surface_groups,
            }
        ],
        algorithm_version="mvp-0.7",
    )


def _facet_op(vault, repository, op_type="facet_merge"):
    return can_apply(vault, repository, Operation(op_type=op_type, entity_type="facet", entity_id="recall"))


def test_a_facet_merge_is_legal_with_review(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    _registered(paths)
    result = _facet_op(load_vault(paths.root), Repository(paths.sqlite_path))
    assert result.legal is True
    assert result.requires_review is True
    assert result.lock_reasons == []


def test_attempt_evidence_no_longer_locks_a_facet(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    _registered(paths)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    _attempt(vault, repository)
    for op_type in ("facet_merge", "facet_split"):
        result = _facet_op(vault, repository, op_type)
        assert result.legal is True and result.requires_review is True and result.lock_reasons == []


def test_an_active_goal_scope_no_longer_locks_a_facet(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")  # the goal scopes the SVD concept
    _registered(paths)
    result = _facet_op(load_vault(paths.root), Repository(paths.sqlite_path), "facet_split")
    assert result.legal is True and result.lock_reasons == []


def test_independent_surface_groups_and_mass_no_longer_lock_a_facet(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    _registered(paths)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    _facet_state(repository, surface_groups=["group_a", "group_b"], mass=2.5)
    assert repository.facet_independence_evidence("recall") == (2, 2.5)
    result = _facet_op(vault, repository)
    assert result.legal is True and result.lock_reasons == []


def test_rename_alias_is_always_sanctioned(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _registered(paths)
    result = can_apply(
        load_vault(paths.root), Repository(paths.sqlite_path),
        Operation(op_type="rename_alias", entity_type="facet", entity_id="recall"),
    )
    assert result.legal is True
    assert result.requires_review is False
    assert result.lock_reasons == []


def test_deactivating_a_practised_learning_object_is_still_invalid(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    _registered(paths)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    _attempt(vault, repository)
    result = can_apply(
        vault,
        repository,
        Operation(op_type="deactivate", entity_type="learning_object", entity_id="lo_svd_definition"),
    )
    assert result.legal is False
    assert [(reason.source, reason.entity_id) for reason in result.lock_reasons] == [
        ("attempts", "lo_svd_definition")
    ]
    item = can_apply(
        vault,
        repository,
        Operation(op_type="blueprint_identity_change", entity_type="practice_item", entity_id="pi_svd_define_001"),
    )
    assert item.legal is False


def test_an_unpractised_learning_object_is_legal_with_review_whatever_its_facets_carry(tmp_path):
    """The LO's facets are in an active goal's certified scope, which used to
    lock the LO through its facet closure; only the LO's own attempts count now."""

    paths = create_basic_vault(tmp_path / "vault")
    _registered(paths)
    result = can_apply(
        load_vault(paths.root), Repository(paths.sqlite_path),
        Operation(op_type="blueprint_identity_change", entity_type="learning_object",
                  entity_id="lo_svd_definition"),
    )
    assert result.legal is True and result.requires_review is True
