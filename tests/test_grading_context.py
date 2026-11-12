from __future__ import annotations

from learnloop.attempts.grading import build_grading_context, evidence_coverage, grading_context_hash
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import create_basic_vault


def test_grading_context_is_deterministic_and_hashable(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]

    first = build_grading_context(
        vault,
        item,
        attempt_id="attempt_1",
        learner_answer_md="SVD is U Sigma V^T.",
    )
    second = build_grading_context(
        vault,
        item,
        attempt_id="attempt_1",
        learner_answer_md="SVD is U Sigma V^T.",
    )

    assert first == second
    assert first.rubric["criteria"][0]["id"] == "correctness"
    assert first.evidence_facets == ["recall"]
    assert first.evidence_weights == {"recall": 1.0}
    assert first.criterion_facet_weights == {"correctness": {"recall": 1.0}}
    # The head offers KM4's nine mechanism types (mvp-0.7, error_taxonomy_map §10.1),
    # not the mvp-0.6 grader vocabulary.
    assert [entry["id"] for entry in first.error_taxonomy["canonical_error_types"]] == [
        "retrieval_failure",
        "conceptual_schema_error",
        "procedure_execution_error",
        "selection_planning_error",
        "condition_assumption_error",
        "representation_notation_error",
        "transfer_context_error",
        "local_slip",
        "assessment_ambiguity",
    ]
    assert "failed criterion" in first.error_taxonomy["targeting_policy"]
    assert "Passing criteria" in first.error_taxonomy["targeting_policy"]
    assert grading_context_hash(first) == grading_context_hash(second)


def test_grading_context_uses_default_rubric_when_inline_rubric_is_omitted(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    practice_item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    practice_item = read_yaml(practice_item_path)
    practice_item.pop("grading_rubric")
    write_yaml(practice_item_path, practice_item)
    write_yaml(
        paths.root / "rubrics" / "short_answer.yaml",
        {
            "schema_version": 1,
            "id": "rubric_short_answer_default",
            "applies_to": {"practice_mode": "short_answer"},
            "rubric": {
                "max_points": 4,
                "criteria": [
                    {"id": "correctness", "points": 3, "description": "States the core idea."},
                    {"id": "clarity", "points": 1, "description": "Is understandable."},
                ],
                "fatal_errors": [],
            },
        },
    )
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]

    context = build_grading_context(
        vault,
        item,
        attempt_id="attempt_1",
        learner_answer_md="SVD is U Sigma V^T.",
    )

    assert item.grading_rubric is None
    assert [criterion["id"] for criterion in context.rubric["criteria"]] == ["correctness", "clarity"]


def test_legacy_evidence_coverage_wrapper_is_score_independent(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]

    assert evidence_coverage(item, {"correctness": 0.0}) == 1.0

    practice_item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    practice_item = read_yaml(practice_item_path)
    practice_item["evidence_weights"] = {}
    write_yaml(practice_item_path, practice_item)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]

    assert evidence_coverage(item, {"correctness": 0.0}) == 0.75
