"""What other test files use from ``tests/test_contract_commissioning.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.vault.yaml_io import read_yaml, write_yaml


LO_ID = "lo_svd_definition"


def _write_blueprint(paths, components, *, integration=None, recipe_id="r1"):
    lo_path = paths.learning_object_path("linear-algebra", LO_ID)
    data = read_yaml(lo_path)
    recipe = {
        "id": recipe_id,
        "composition": "conjunctive",
        "all_of": [
            {"facet": facet, "capability": capability, "modality": modality}
            for facet, capability, modality in components
        ],
    }
    if integration is not None:
        recipe["integration"] = {
            "facet": integration[0],
            "capability": integration[1],
            "modality": "hard",
        }
    data["blueprints"] = [{"id": "bp1", "weight": 1.0, "recipes": [recipe]}]
    write_yaml(lo_path, data)
    return paths
