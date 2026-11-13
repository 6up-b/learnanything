"""What other test files use from ``tests/test_km3_projections.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.certain_grade_helpers import make_grade_certain
from tests.helpers import NOW, NOW_ISO, create_basic_vault, set_algorithm_version, write_facets


COMP_A = "facet_component_a"
COMP_B = "facet_component_b"
INTEG = "facet_integration"
LO_ID = "lo_composite"
CONCEPT = "singular_value_decomposition"


def _item(item_id, *, facet, capability, mode, correlation_group, points=4):
    return {
        "schema_version": 1,
        "id": item_id,
        "learning_object_id": LO_ID,
        "subjects": None,
        "practice_mode": mode,
        "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
        "evidence_facets": [facet],
        "evidence_weights": {facet: 1.0},
        "prompt": f"Prompt for {item_id}.",
        "expected_answer": "An answer.",
        "difficulty": 0.5,
        "grading_rubric": {
            "max_points": points,
            "criteria": [
                {
                    "id": "c1",
                    "points": points,
                    "description": "criterion",
                    "targets": [{"facet": facet, "capability": capability, "role": "primary"}],
                    "correlation_group": correlation_group,
                    "recipe_ids": ["recipe_main"],
                }
            ],
            "fatal_errors": [],
        },
        "evidence_fingerprint": {"source_family": correlation_group},
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


# The tag whose capability projection the dual-axis tests still read: the head's projection reports these
# facets' capabilities differently.
BLUEPRINT_OLD_TAG = "mvp-0.7"


def build_blueprint_vault(root: Path, *, version: str = LATEST_ALGORITHM_VERSION):
    """A composite LO with an AND-recipe blueprint + integration facet, at ``version`` (the head by default)."""

    paths = create_basic_vault(root)
    write_yaml(
        paths.goals_path,
        {
            "schema_version": 2,
            "goals": [
                {
                    "id": "goal_master",
                    "title": "Master the composite skill",
                    "status": "active",
                    "priority": 1.0,
                    "target_recall": 0.8,
                    "due_at": None,
                    "facet_scope": {"concepts": [CONCEPT], "facets": []},
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                }
            ],
        },
    )
    write_facets(
        paths,
        [
            {"id": COMP_A, "kind": "procedure", "claim": "Component A procedure."},
            {"id": COMP_B, "kind": "definition", "claim": "Component B schema."},
            {"id": INTEG, "kind": "procedure", "claim": "Coordinate the components."},
        ],
    )
    write_yaml(
        paths.learning_object_path("linear-algebra", LO_ID),
        {
            "schema_version": 1,
            "id": LO_ID,
            "title": "Composite skill",
            "subjects": ["linear-algebra"],
            "concept": CONCEPT,
            "knowledge_type": "procedure",
            "status": "active",
            "contradicts": None,
            "summary": "A composite skill requiring two components and their coordination.",
            "prerequisites": [],
            "confusables": [],
            "blueprints": [
                {
                    "id": "bp_solve",
                    "weight": 1.0,
                    "recipes": [
                        {
                            "id": "recipe_main",
                            "composition": "conjunctive",
                            "all_of": [
                                {"facet": COMP_A, "capability": "procedure_execution"},
                                {"facet": COMP_B, "capability": "schema_interpretation"},
                            ],
                            "integration": {"facet": INTEG, "capability": "coordination"},
                        }
                    ],
                }
            ],
            "difficulty_prior": 0.55,
            "tags": [],
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_comp_a"),
        _item("pi_comp_a", facet=COMP_A, capability="procedure_execution", mode="constructed_response", correlation_group="cg_a"),
    )
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_comp_b"),
        _item("pi_comp_b", facet=COMP_B, capability="schema_interpretation", mode="short_answer", correlation_group="cg_b"),
    )
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_integrated"),
        _item("pi_integrated", facet=INTEG, capability="coordination", mode="constructed_response", correlation_group="cg_integ"),
    )
    # Remove the default basic-vault item so its facet does not clutter the scope.
    default_item = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    if default_item.exists():
        default_item.unlink()
    if version != LATEST_ALGORITHM_VERSION:
        set_algorithm_version(paths, version)
    return paths


def _synced(paths):
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


@pytest.fixture
def blueprint_vault(tmp_path):
    return _synced(build_blueprint_vault(tmp_path / "vault"))


@pytest.fixture
def blueprint_vault_old_tag(tmp_path):
    return _synced(build_blueprint_vault(tmp_path / "vault", version=BLUEPRINT_OLD_TAG))


def _attempt(vault, repository, item_id, criterion, *, hints_used=0):
    """A self-graded attempt whose grade is then certain (``tests/certain_grade_helpers.py``): the KM3 readers
    are tested over banked credit, and one uncertain self-grade banks too little to certify a cell."""

    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=item_id,
            learner_answer_md="An answer.",
            attempt_type="independent_attempt",
            hints_used=hints_used,
        ),
        SelfGradeInput(criterion_points={"c1": criterion}, fatal_errors=[], confidence=4),
        clock=FrozenClock(NOW),
    )
    make_grade_certain(vault, repository, result.attempt_id, clock=FrozenClock(NOW))
    return result
