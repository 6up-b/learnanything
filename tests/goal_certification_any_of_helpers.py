"""What other test files use from ``tests/test_goal_certification_any_of.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from pathlib import Path

from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW_ISO, create_basic_vault, set_algorithm_version, write_facets


LO_ID = "lo_composite"
CONCEPT = "singular_value_decomposition"
COMP_A = "facet_component_a"
ALT_X = "facet_alternative_x"
ALT_Y = "facet_alternative_y"
INTEG = "facet_integration"
# (facet, capability, item id) for every cell these recipes can name.
CELLS = {
    COMP_A: ("procedure_execution", "pi_comp_a"),
    ALT_X: ("method_selection", "pi_alt_x"),
    ALT_Y: ("method_selection", "pi_alt_y"),
    INTEG: ("coordination", "pi_integrated"),
}


def _item(item_id, *, facet, capability, correlation_group):
    return {
        "schema_version": 1,
        "id": item_id,
        "learning_object_id": LO_ID,
        "subjects": None,
        "practice_mode": "constructed_response",
        "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
        "evidence_facets": [facet],
        "evidence_weights": {facet: 1.0},
        "prompt": f"Prompt for {item_id}.",
        "expected_answer": "An answer.",
        "difficulty": 0.5,
        "grading_rubric": {
            "max_points": 4,
            "criteria": [
                {
                    "id": "c1",
                    "points": 4,
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


def _component(facet, *, modality="hard"):
    capability, _item_id = CELLS[facet]
    return {"facet": facet, "capability": capability, "modality": modality}


def build_vault(root: Path, recipe: dict):
    """An mvp-0.7 vault whose single LO carries exactly ``recipe``.

    Every cell the recipes can name has an instrument, so a certification result
    is always a statement about evidence rather than about missing items.
    """

    paths = create_basic_vault(root)
    write_facets(
        paths,
        [
            {"id": COMP_A, "kind": "procedure", "claim": "Component A procedure."},
            {"id": ALT_X, "kind": "procedure", "claim": "Alternative method X."},
            {"id": ALT_Y, "kind": "procedure", "claim": "Alternative method Y."},
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
            "summary": "A composite skill with alternative methods.",
            "prerequisites": [],
            "confusables": [],
            "blueprints": [{"id": "bp_solve", "weight": 1.0, "recipes": [recipe]}],
            "difficulty_prior": 0.55,
            "tags": [],
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    for facet, (capability, item_id) in CELLS.items():
        write_yaml(
            paths.practice_item_path("linear-algebra", item_id),
            _item(item_id, facet=facet, capability=capability, correlation_group=f"cg_{facet}"),
        )
    default_item = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    if default_item.exists():
        default_item.unlink()
    set_algorithm_version(paths, "mvp-0.7")
    return paths
