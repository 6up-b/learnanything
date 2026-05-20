from __future__ import annotations

from learnloop.services.grading import build_grading_context, grading_context_hash
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
