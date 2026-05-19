from __future__ import annotations

import pytest

from learnloop.codex.schemas import CriterionEvidence, ErrorAttribution, GradingProposal
from learnloop.services.grading import GradingValidationError, validate_codex_grading_proposal
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault


def test_valid_codex_grade_validates(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]

    validated = validate_codex_grading_proposal(
        _proposal(),
        attempt_id="attempt_1",
        item=item,
        vault=vault,
    )

    assert validated.rubric_score == 2
    assert validated.criterion_evidence[0].points_awarded == 2
    assert validated.error_attributions[0].error_type == "conceptual_slip"
    assert validated.manual_review_reason is None


def test_codex_grade_rejects_mismatched_attempt_and_item(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]

    with pytest.raises(GradingValidationError, match="attempt_id"):
        validate_codex_grading_proposal(_proposal(attempt_id="other"), attempt_id="attempt_1", item=item, vault=vault)
    with pytest.raises(GradingValidationError, match="practice_item_id"):
        validate_codex_grading_proposal(_proposal(practice_item_id="other"), attempt_id="attempt_1", item=item, vault=vault)


def test_codex_grade_rejects_unknown_or_excess_criterion_and_bad_fatal_cap(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]

    with pytest.raises(GradingValidationError, match="Unknown rubric criterion"):
        validate_codex_grading_proposal(
            _proposal(criterion_id="missing"),
            attempt_id="attempt_1",
            item=item,
            vault=vault,
        )
    with pytest.raises(GradingValidationError, match="exceed"):
        validate_codex_grading_proposal(
            _proposal(points_awarded=5),
            attempt_id="attempt_1",
            item=item,
            vault=vault,
        )
    with pytest.raises(GradingValidationError, match="Fatal errors must cap"):
        validate_codex_grading_proposal(
            _proposal(rubric_score=4, fatal_errors=["conceptual_slip"]),
            attempt_id="attempt_1",
            item=item,
            vault=vault,
        )


def test_unknown_codex_error_type_routes_to_manual_review(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]

    validated = validate_codex_grading_proposal(
        _proposal(error_type="new_error"),
        attempt_id="attempt_1",
        item=item,
        vault=vault,
    )

    assert validated.manual_review_reason == "unknown_error_type:new_error"


def _proposal(
    *,
    attempt_id: str = "attempt_1",
    practice_item_id: str = "pi_svd_define_001",
    criterion_id: str = "correctness",
    points_awarded: float = 2,
    rubric_score: int = 2,
    fatal_errors: list[str] | None = None,
    error_type: str = "conceptual_slip",
) -> GradingProposal:
    return GradingProposal(
        attempt_id=attempt_id,
        practice_item_id=practice_item_id,
        rubric_score=rubric_score,
        criterion_evidence=[
            CriterionEvidence(
                criterion_id=criterion_id,
                points_awarded=points_awarded,
                evidence="Answer is partially correct.",
            )
        ],
        fatal_errors=fatal_errors or [],
        error_attributions=[
            ErrorAttribution(
                error_type=error_type,
                severity=0.6,
                evidence="Confuses details.",
                is_misconception=True,
            )
        ],
        grader_confidence=0.9,
    )
