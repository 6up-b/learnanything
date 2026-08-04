from __future__ import annotations

import pytest

from learnloop.codex.schemas import CriterionEvidence, ErrorAttribution, GradingProposal, RepairSuggestion
from learnloop.services.grading import GradingValidationError, validate_codex_grading_proposal
from learnloop.vault.loader import load_vault
from learnloop.vault.models import Rubric, RubricCriterion

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


def test_codex_error_attribution_preserves_target_evidence_families(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"].model_copy(
        update={"evidence_facets": ["recall", "numeric"], "evidence_weights": {"recall": 0.5, "numeric": 0.5}}
    )

    validated = validate_codex_grading_proposal(
        _proposal(target_evidence_families=["numeric"]),
        attempt_id="attempt_1",
        item=item,
        vault=vault,
    )

    assert validated.error_attributions[0].target_evidence_families == ["numeric"]


def test_codex_error_attribution_passes_through_misconception_fields(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]

    validated = validate_codex_grading_proposal(
        _proposal(
            misconception_statement="believes Q maps standard vectors to eigenbasis coefficients",
            misconception_consistent_answer="Qx is the coordinate vector",
        ),
        attempt_id="attempt_1",
        item=item,
        vault=vault,
    )

    attribution = validated.error_attributions[0]
    assert attribution.misconception_statement == "believes Q maps standard vectors to eigenbasis coefficients"
    assert attribution.misconception_consistent_answer == "Qx is the coordinate vector"


def test_codex_misconception_without_statement_does_not_hard_fail(tmp_path):
    # Legacy providers omit the structured statement; validation must pass it as
    # None rather than raising (spec §2.1).
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]

    validated = validate_codex_grading_proposal(
        _proposal(is_misconception=True),
        attempt_id="attempt_1",
        item=item,
        vault=vault,
    )

    attribution = validated.error_attributions[0]
    assert attribution.is_misconception is True
    assert attribution.misconception_statement is None
    assert attribution.misconception_consistent_answer is None


def test_codex_error_attribution_does_not_expand_target_criterion_to_facet(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"].model_copy(
        update={
            "evidence_facets": ["recall", "numeric"],
            "evidence_weights": {"recall": 0.5, "numeric": 0.5},
            "criterion_facet_weights": {"correctness": {"numeric": 1.0}},
        }
    )

    validated = validate_codex_grading_proposal(
        _proposal(target_criterion_ids=["correctness"]),
        attempt_id="attempt_1",
        item=item,
        vault=vault,
    )

    attribution = validated.error_attributions[0]
    assert attribution.target_criterion_ids == ["correctness"]
    assert attribution.target_evidence_families == []


def test_explicit_recall_wording_normalizes_to_recall_failure(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]

    validated = validate_codex_grading_proposal(
        _proposal(
            error_type="missing_spectral_norm_error",
            is_misconception=False,
            evidence="The learner wrote they do not remember this part.",
        ),
        attempt_id="attempt_1",
        item=item,
        vault=vault,
        learner_answer_md="I don't know the spectral norm.",
    )

    assert validated.error_attributions[0].error_type == "recall_failure"
    assert validated.manual_review_reason is None


def test_unknown_target_criterion_routes_to_manual_review(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]

    validated = validate_codex_grading_proposal(
        _proposal(target_criterion_ids=["missing_criterion"]),
        attempt_id="attempt_1",
        item=item,
        vault=vault,
    )

    assert validated.manual_review_reason == "unknown_target_criterion:missing_criterion"
    assert validated.error_attributions[0].target_criterion_ids == []


def test_codex_error_attribution_unknown_target_family_routes_to_manual_review(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]

    validated = validate_codex_grading_proposal(
        _proposal(target_evidence_families=["unknown-facet"]),
        attempt_id="attempt_1",
        item=item,
        vault=vault,
    )

    assert validated.manual_review_reason == "unknown_target_evidence_family:unknown-facet"
    assert validated.error_attributions[0].target_evidence_families == []


def test_repair_suggestion_target_families_are_canonicalized(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"].model_copy(
        update={"evidence_facets": ["recall", "numeric"], "evidence_weights": {"recall": 0.5, "numeric": 0.5}}
    )
    proposal = _proposal(
        repair_suggestions=[
            RepairSuggestion(
                practice_mode="targeted_review",
                rationale="Fix numeric setup.",
                target_evidence_families=["numeric"],
            )
        ]
    )

    validated = validate_codex_grading_proposal(
        proposal,
        attempt_id="attempt_1",
        item=item,
        vault=vault,
    )

    assert validated.manual_review_reason is None
    assert validated.repair_suggestions is not None
    suggestion = validated.repair_suggestions[0]
    assert suggestion["practice_mode"] == "targeted_review"
    assert suggestion["learning_object_id"] is None
    assert suggestion["rationale"] == "Fix numeric setup."
    assert suggestion["target_evidence_families"] == ["numeric"]
    assert suggestion["repair_validation"]["authority"] == (
        "learnloop_validator"
    )
    assert suggestion["repair_validation"]["status"] == "incomplete"


def test_unknown_repair_suggestion_target_family_routes_to_manual_review(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]
    proposal = _proposal(
        repair_suggestions=[
            RepairSuggestion(
                practice_mode="targeted_review",
                rationale="Fix the missing facet.",
                target_evidence_families=["missing_facet"],
            )
        ]
    )

    validated = validate_codex_grading_proposal(
        proposal,
        attempt_id="attempt_1",
        item=item,
        vault=vault,
    )

    assert validated.manual_review_reason == "unknown_target_evidence_family:missing_facet"
    assert validated.repair_suggestions[0]["target_evidence_families"] == []


def test_codex_grade_rejects_mismatched_attempt_and_item(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]

    with pytest.raises(GradingValidationError, match="attempt_id"):
        validate_codex_grading_proposal(_proposal(attempt_id="other"), attempt_id="attempt_1", item=item, vault=vault)
    with pytest.raises(GradingValidationError, match="practice_item_id"):
        validate_codex_grading_proposal(_proposal(practice_item_id="other"), attempt_id="attempt_1", item=item, vault=vault)


def test_codex_grade_rejects_unknown_or_excess_criterion_and_derives_fatal_cap(tmp_path):
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
    validated = validate_codex_grading_proposal(
        _proposal(rubric_score=4, fatal_errors=["conceptual_slip"]),
        attempt_id="attempt_1",
        item=item,
        vault=vault,
    )
    assert validated.rubric_score == 1


def test_codex_score_and_max_are_derived_from_criterion_points(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]
    rubric = Rubric(
        max_points=4,
        criteria=[
            RubricCriterion(id="formula", points=2, description="Formula."),
            RubricCriterion(id="smoothing", points=3, description="Smoothing."),
        ],
    )
    proposal = GradingProposal(
        attempt_id="attempt_1",
        practice_item_id=item.id,
        rubric_score=4,
        criterion_evidence=[
            CriterionEvidence(criterion_id="formula", points_awarded=2, evidence="Correct."),
            CriterionEvidence(criterion_id="smoothing", points_awarded=3, evidence="Correct."),
        ],
        grader_confidence=0.9,
    )

    validated = validate_codex_grading_proposal(
        proposal,
        attempt_id="attempt_1",
        item=item,
        vault=vault,
        rubric=rubric,
    )

    assert rubric.max_points == 5
    assert validated.rubric_score == 5


def test_recall_normalization_does_not_scan_unrelated_answer_text(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]

    validated = validate_codex_grading_proposal(
        _proposal(
            error_type="incomplete_answer",
            is_misconception=False,
            evidence="The final requested conclusion is omitted.",
        ),
        attempt_id="attempt_1",
        item=item,
        vault=vault,
        learner_answer_md="I am not sure how to count one earlier case. The later calculation is correct.",
    )

    assert validated.error_attributions[0].error_type == "incomplete_answer"


def test_unanchored_known_facet_requests_review_instead_of_failing_grade(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]

    validated = validate_codex_grading_proposal(
        _proposal(target_evidence_families=["recall"]).model_copy(
            update={"diagnosis_md": "The final explanation is incomplete."}
        ),
        attempt_id="attempt_1",
        item=item,
        vault=vault,
    )

    assert validated.error_attributions[0].target_evidence_families == ["recall"]
    assert validated.manual_review_reason == "unanchored_diagnosis_facet:recall"


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


def test_codex_error_severity_defaults_from_taxonomy(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]
    proposal = _proposal()
    proposal.error_attributions[0].severity = None

    validated = validate_codex_grading_proposal(
        proposal,
        attempt_id="attempt_1",
        item=item,
        vault=vault,
    )

    assert validated.error_attributions[0].severity == 0.7


def test_low_codex_grader_confidence_routes_to_manual_review(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]

    proposal = _proposal()
    proposal.grader_confidence = 0.2
    validated = validate_codex_grading_proposal(
        proposal,
        attempt_id="attempt_1",
        item=item,
        vault=vault,
    )

    assert validated.manual_review_reason == "low_grader_confidence"


def _proposal(
    *,
    attempt_id: str = "attempt_1",
    practice_item_id: str = "pi_svd_define_001",
    criterion_id: str = "correctness",
    points_awarded: float = 2,
    rubric_score: int = 2,
    fatal_errors: list[str] | None = None,
    error_type: str = "conceptual_slip",
    is_misconception: bool = True,
    evidence: str = "Confuses details.",
    misconception_statement: str | None = None,
    misconception_consistent_answer: str | None = None,
    target_evidence_families: list[str] | None = None,
    target_criterion_ids: list[str] | None = None,
    repair_suggestions: list[RepairSuggestion] | None = None,
) -> GradingProposal:
    diagnosis_facets = [
        *(target_evidence_families or []),
        *(
            facet
            for suggestion in repair_suggestions or []
            for facet in suggestion.target_evidence_families
        ),
    ]
    return GradingProposal(
        diagnosis_md=(
            "The diagnosis implicates " + ", ".join(diagnosis_facets) + "."
            if diagnosis_facets
            else None
        ),
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
                evidence=evidence,
                is_misconception=is_misconception,
                misconception_statement=misconception_statement,
                misconception_consistent_answer=misconception_consistent_answer,
                target_evidence_families=target_evidence_families or [],
                target_criterion_ids=target_criterion_ids or [],
            )
        ],
        grader_confidence=0.9,
        repair_suggestions=repair_suggestions or [],
    )
