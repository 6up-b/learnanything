from __future__ import annotations

from learnloop.services.grading import build_grading_context, grading_context_hash
from learnloop.vault.loader import load_vault

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
