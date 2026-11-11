"""What other test files use from ``tests/test_identifiability_doctor.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from pathlib import Path

from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW_ISO, create_basic_vault, set_algorithm_version, write_facets
from tests.km2_write_path_helpers import _item, _rubric


def _build_registry_vault(root: Path) -> Path:
    """mvp-0.7 vault whose LO blueprint requires a facet-capability no criterion
    observes (§11.3 check 2 missing anchor)."""

    paths = create_basic_vault(root)
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    write_facets(
        paths,
        [
            {"id": "facet_def", "kind": "definition", "claim": "A definition."},
            {"id": "facet_pick", "kind": "applicability_condition", "claim": "When to pick."},
        ],
    )
    # LO with a blueprint requiring facet_pick@method_selection, but the only
    # rubric criterion observes facet_def@retrieval -> facet_pick has no anchor.
    lo = {
        "schema_version": 1,
        "id": "lo_svd_definition",
        "title": "SVD definition",
        "subjects": ["linear-algebra"],
        "concept": "singular_value_decomposition",
        "knowledge_type": "definition",
        "status": "active",
        "contradicts": None,
        "summary": "Define SVD.",
        "prerequisites": [],
        "confusables": [],
        "blueprints": [
            {
                "id": "bp_main",
                "weight": 1.0,
                "recipes": [
                    {
                        "id": "recipe_main",
                        "composition": "conjunctive",
                        "all_of": [
                            {"facet": "facet_def", "capability": "retrieval", "modality": "hard"},
                            {"facet": "facet_pick", "capability": "method_selection", "modality": "hard"},
                        ],
                    }
                ],
            }
        ],
        "difficulty_prior": 0.5,
        "tags": [],
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }
    write_yaml(paths.learning_object_path("linear-algebra", "lo_svd_definition"), lo)
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_define_001"),
        _item(
            "pi_svd_define_001",
            "lo_svd_definition",
            evidence_facets=["facet_def"],
            rubric=_rubric(
                "correctness",
                [{"facet": "facet_def", "capability": "retrieval", "role": "primary"}],
                correlation_group="def_group",
            ),
            fingerprint={"source_family": "chapter3"},
        ),
    )
    set_algorithm_version(paths, "mvp-0.7")
    return paths
