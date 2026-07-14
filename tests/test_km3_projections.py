"""KM3 projections + goal certification (knowledge-model §9.2/§9.5/§16).

Builds an mvp-0.7 vault whose composite LO carries an authored AND-recipe
blueprint (two capability-matched components plus an integration factor) and
drives real attempts through the write path, so the blueprint readiness
projection and the Ready/Demonstrated dual-axis run end to end.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.blueprint_projection import project_lo_readiness
from learnloop.services.goal_certification import facet_demonstration, lo_certification
from learnloop.services.goal_projection import goal_report
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import (
    NOW,
    NOW_ISO,
    create_basic_vault,
    set_algorithm_version,
    write_facets,
)

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


def build_blueprint_vault(root: Path):
    """An mvp-0.7 composite LO with an AND-recipe blueprint + integration facet."""

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
    set_algorithm_version(paths, "mvp-0.7")
    return paths


@pytest.fixture
def blueprint_vault(tmp_path):
    paths = build_blueprint_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


def _attempt(vault, repository, item_id, criterion, *, hints_used=0):
    complete_self_graded_attempt(
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


# -- Blueprint readiness (§9.2) ------------------------------------------------


def test_blueprint_readiness_wired_into_goal_report(blueprint_vault):
    vault, repository = blueprint_vault
    _attempt(vault, repository, "pi_comp_a", 4)
    _attempt(vault, repository, "pi_comp_b", 4)

    report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    assert LO_ID in report.blueprint_readiness_by_lo
    readiness = report.blueprint_readiness_by_lo[LO_ID]
    assert readiness.has_blueprints is True
    # Components are strong, but the untested integration facet (predicted at the
    # 0.5 prior) is the bottleneck that keeps readiness below the component level.
    assert readiness.bottleneck is not None
    assert readiness.bottleneck.facet == INTEG
    assert readiness.readiness is not None and readiness.readiness < 0.55


def test_readiness_rises_when_components_improve():
    # Pure check: strengthening a component recall raises blueprint readiness.
    lo = _load_lo()
    weak = project_lo_readiness(lo, lambda f, c: 0.3, slip=0.05).readiness
    strong = project_lo_readiness(lo, lambda f, c: 0.9, slip=0.05).readiness
    assert strong > weak


def _load_lo():
    import tempfile

    paths = build_blueprint_vault(Path(tempfile.mkdtemp()) / "vault")
    vault = load_vault(paths.root)
    return vault.learning_objects[LO_ID]


# -- Goal certification / Demonstrated axis (§9.5, §16) ------------------------


def test_retrieval_style_component_demonstrates_only_its_capability(blueprint_vault):
    vault, repository = blueprint_vault
    _attempt(vault, repository, "pi_comp_a", 4)

    lo = vault.learning_objects[LO_ID]
    comp_a = facet_demonstration(vault, repository, lo, COMP_A)
    assert comp_a.required_capabilities == ("procedure_execution",)
    assert comp_a.demonstrated is True
    # Component B was never attempted -> not demonstrated at its capability.
    comp_b = facet_demonstration(vault, repository, lo, COMP_B)
    assert comp_b.demonstrated is False


def test_planted_integration_gap_not_shown_demonstrated(blueprint_vault):
    """§16 projection row: strong components + missing integration -> not demonstrated."""

    vault, repository = blueprint_vault
    # Demonstrate BOTH components unassisted, repeatedly, but never the integrated
    # whole-task item.
    for _ in range(3):
        _attempt(vault, repository, "pi_comp_a", 4)
        _attempt(vault, repository, "pi_comp_b", 4)

    lo = vault.learning_objects[LO_ID]
    assert facet_demonstration(vault, repository, lo, COMP_A).demonstrated is True
    assert facet_demonstration(vault, repository, lo, COMP_B).demonstrated is True

    cert = lo_certification(vault, repository, lo)
    assert cert.demonstrated is False
    assert INTEG in cert.integration_gaps

    # Once the integrated task is also demonstrated directly, the LO certifies.
    _attempt(vault, repository, "pi_integrated", 4)
    cert_after = lo_certification(vault, repository, lo)
    assert cert_after.demonstrated is True
    assert cert_after.integration_gaps == ()


def test_goal_report_exposes_dual_axis_fields(blueprint_vault):
    vault, repository = blueprint_vault
    _attempt(vault, repository, "pi_comp_a", 4)

    report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    comp_a = next(f for f in report.facets if f.facet_id == COMP_A)
    # Ready (prediction) and Demonstrated (capability-matched credit) are both
    # exposed and are distinct axes.
    assert comp_a.required_capabilities == ("procedure_execution",)
    assert comp_a.demonstrated is True
    assert comp_a.ready == comp_a.predicted_at_horizon
    integ = next(f for f in report.facets if f.facet_id == INTEG)
    assert integ.demonstrated is False


def test_hinted_component_not_demonstrated(blueprint_vault):
    vault, repository = blueprint_vault
    _attempt(vault, repository, "pi_comp_a", 4, hints_used=1)
    lo = vault.learning_objects[LO_ID]
    # Assisted evidence earns no certification credit -> not demonstrated (§5.4).
    assert facet_demonstration(vault, repository, lo, COMP_A).demonstrated is False
