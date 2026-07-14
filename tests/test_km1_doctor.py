from __future__ import annotations

from learnloop.services.doctor import run_doctor
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import create_basic_vault, set_algorithm_version, write_facets


def _codes(paths):
    report = run_doctor(paths.root)
    return {issue.code: issue.severity for issue in report.issues}


def test_empty_registry_with_facet_items_is_doctor_error_on_mvp07(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    codes = _codes(paths)
    assert codes.get("evidence_facet:empty_registry") == "error"


def test_empty_registry_is_skipped_on_legacy(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    codes = _codes(paths)
    # Legacy vaults keep today's behavior: no empty-registry issue at all.
    assert "evidence_facet:empty_registry" not in codes


def test_unregistered_facet_is_doctor_error_on_mvp07(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    write_facets(
        paths,
        [{"id": "facet_other", "kind": "definition", "claim": "Some other atom."}],
    )
    codes = _codes(paths)
    # The item still declares "recall", which is not registered.
    assert codes.get("evidence_facet:unregistered") == "error"


def test_unregistered_facet_is_warning_on_legacy(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_facets(paths, [{"id": "facet_other", "title": "Other"}], schema_version=1)
    codes = _codes(paths)
    assert codes.get("evidence_facet:unregistered") == "warning"


def test_facet_missing_claim_is_incomplete_contract_error_on_mvp07(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    write_facets(paths, [{"id": "recall", "kind": "definition"}])  # claim omitted
    codes = _codes(paths)
    assert codes.get("evidence_facet:incomplete_contract") == "error"


def test_criterion_dependency_cycle_rejected(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    data = read_yaml(item_path)
    data["grading_rubric"]["criteria"] = [
        {"id": "a", "points": 2, "description": "A", "depends_on": ["b"]},
        {"id": "b", "points": 2, "description": "B", "depends_on": ["a"]},
    ]
    write_yaml(item_path, data)
    codes = _codes(paths)
    assert codes.get("criterion:dependency_cycle") == "error"


def test_blueprint_invalid_capability_rejected(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    lo_path = paths.learning_object_path("linear-algebra", "lo_svd_definition")
    data = read_yaml(lo_path)
    data["blueprints"] = [
        {
            "id": "bp1",
            "weight": 1.0,
            "recipes": [
                {
                    "id": "r1",
                    "composition": "conjunctive",
                    "all_of": [{"facet": "recall", "capability": "not_a_capability"}],
                }
            ],
        }
    ]
    write_yaml(lo_path, data)
    codes = _codes(paths)
    assert codes.get("blueprint:invalid_capability") == "error"


def test_valid_blueprint_and_criterion_targets_pass(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_facets(
        paths,
        [{"id": "recall", "kind": "definition", "claim": "SVD factorization definition."}],
    )
    lo_path = paths.learning_object_path("linear-algebra", "lo_svd_definition")
    data = read_yaml(lo_path)
    data["blueprints"] = [
        {
            "id": "bp1",
            "weight": 1.0,
            "recipes": [
                {
                    "id": "r1",
                    "composition": "conjunctive",
                    "all_of": [{"facet": "recall", "capability": "retrieval"}],
                }
            ],
        }
    ]
    write_yaml(lo_path, data)
    report = run_doctor(paths.root)
    facet_codes = {
        issue.code
        for issue in report.issues
        if issue.severity == "error"
        and issue.code.split(":")[0] in ("blueprint", "criterion", "evidence_facet")
    }
    assert facet_codes == set()
