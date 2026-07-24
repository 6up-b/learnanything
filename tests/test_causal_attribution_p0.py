from __future__ import annotations

import json

import pytest

from learnloop.clock import FrozenClock
from learnloop.codex.client import _codex_output_schema
from learnloop.codex.schemas import (
    CriterionEvidence,
    ErrorAttribution,
    GradingProposal,
    RepairSuggestion,
)
from learnloop.db.repositories import Repository
from learnloop.services.grading import (
    GradingValidationError,
    validate_codex_grading_proposal,
)
from learnloop.services.causal_attribution import record_unresolved_cause_self_report
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    SelfGradeInput,
    apply_attempt,
    complete_self_graded_attempt,
)
from learnloop.services.misconceptions import _event_facet_ids
from learnloop.services.remediation import start_remediation_episode
from learnloop.services.rung_variants import audit_variant_direction
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import (
    Rubric,
    RubricCriterion,
    TraceContract,
    TraceRecipe,
)
from learnloop_sidecar.handlers.serializers import feedback_bundle

from tests.helpers import NOW, NOW_ISO, create_basic_vault
from tests.test_km2_write_path import build_mvp07_vault


def test_grading_schema_is_prose_first():
    schema = _codex_output_schema(GradingProposal)
    assert next(iter(schema["properties"])) == "diagnosis_md"


def test_passed_facet_and_repair_targets_are_blocked(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    item = vault.practice_items["pi_svd_define_001"].model_copy(
        update={
            "evidence_facets": ["recall", "numeric"],
            "criterion_facet_weights": {
                "known": {"recall": 1.0},
                "failed": {"numeric": 1.0},
            },
        }
    )
    rubric = Rubric(
        max_points=2,
        criteria=[
            RubricCriterion(id="known", points=1, description="Known"),
            RubricCriterion(id="failed", points=1, description="Failed"),
        ],
    )
    proposal = GradingProposal(
        diagnosis_md="The recall facet is demonstrated; the numeric facet failed.",
        attempt_id="att",
        practice_item_id=item.id,
        rubric_score=1,
        criterion_evidence=[
            CriterionEvidence(
                criterion_id="known", points_awarded=1, evidence="Full credit."
            ),
            CriterionEvidence(
                criterion_id="failed", points_awarded=0, evidence="No credit."
            ),
        ],
        error_attributions=[
            ErrorAttribution(
                error_type="conceptual_slip",
                evidence="Numeric failure.",
                resolution_status="resolved",
                cause_scope="learner_state",
                target_evidence_families=["recall", "numeric"],
                target_criterion_ids=["known", "failed"],
            )
        ],
        grader_confidence=0.9,
        repair_suggestions=[
            RepairSuggestion(
                practice_mode="targeted_review",
                rationale="Repair only what failed.",
                target_evidence_families=["recall", "numeric"],
                target_criterion_ids=["known", "failed"],
            )
        ],
    )

    validated = validate_codex_grading_proposal(
        proposal,
        attempt_id="att",
        item=item,
        vault=vault,
        rubric=rubric,
    )

    attribution = validated.error_attributions[0]
    assert attribution.target_evidence_families == ["numeric"]
    assert attribution.target_criterion_ids == ["failed"]
    assert validated.repair_suggestions[0]["target_evidence_families"] == ["numeric"]
    assert validated.repair_suggestions[0]["target_criterion_ids"] == ["failed"]
    kinds = {event["kind"] for event in validated.attribution_audit_events}
    assert "passed_facet_write_blocked" in kinds
    assert "passed_criterion_write_blocked" in kinds


def test_partial_credit_is_positive_projection_evidence_but_not_firewall_protection(
    tmp_path,
):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    item = vault.practice_items["pi_svd_define_001"].model_copy(
        update={
            "evidence_facets": ["recall"],
            "criterion_facet_weights": {"mostly_correct": {"recall": 1.0}},
        }
    )
    rubric = Rubric(
        max_points=1,
        criteria=[
            RubricCriterion(
                id="mostly_correct", points=1, description="Mostly correct"
            )
        ],
    )
    proposal = GradingProposal(
        diagnosis_md="The recall step was nearly right but contains a specific error.",
        attempt_id="att_partial",
        practice_item_id=item.id,
        rubric_score=1,
        criterion_evidence=[
            CriterionEvidence(
                criterion_id="mostly_correct",
                points_awarded=0.9,
                evidence="Minor but real error.",
            )
        ],
        error_attributions=[
            ErrorAttribution(
                error_type="conceptual_slip",
                evidence="Specific recall error.",
                resolution_status="resolved",
                cause_scope="learner_state",
                target_evidence_families=["recall"],
                target_criterion_ids=["mostly_correct"],
            )
        ],
        grader_confidence=0.9,
    )

    validated = validate_codex_grading_proposal(
        proposal,
        attempt_id="att_partial",
        item=item,
        vault=vault,
        rubric=rubric,
    )
    attribution = validated.error_attributions[0]
    assert attribution.target_evidence_families == ["recall"]
    assert attribution.target_criterion_ids == ["mostly_correct"]
    assert validated.attribution_audit_events == []


def test_passed_typed_target_is_blocked_and_resolution_reopens(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    item = vault.practice_items["pi_svd_define_001"]
    proposal = GradingProposal(
        diagnosis_md="The recall facet is demonstrated.",
        attempt_id="att",
        practice_item_id=item.id,
        rubric_score=4,
        criterion_evidence=[
            CriterionEvidence(
                criterion_id="correctness",
                points_awarded=4,
                evidence="Full credit.",
            )
        ],
        error_attributions=[
            ErrorAttribution(
                error_type="conceptual_slip",
                evidence="Contradictory model output.",
                resolution_status="resolved",
                cause_scope="learner_state",
                target_ref={
                    "kind": "facet_capability",
                    "facet_id": "recall",
                    "capability": "retrieval",
                },
            )
        ],
        grader_confidence=0.9,
    )

    validated = validate_codex_grading_proposal(
        proposal,
        attempt_id="att",
        item=item,
        vault=vault,
    )

    attribution = validated.error_attributions[0]
    assert attribution.target_ref == {"kind": "none"}
    assert attribution.resolution_status == "unresolved"
    assert any(
        event["kind"] == "passed_typed_target_write_blocked"
        for event in validated.attribution_audit_events
    )


def test_event_facet_ids_never_fall_back_to_attempt_facets(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    assert _event_facet_ids(
        vault,
        {"repair_plan": None},
        {"evidence_facets": ["recall"]},
    ) == []


def test_missing_step_divergence_must_reference_authored_checkpoint(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    item = vault.practice_items["pi_svd_define_001"].model_copy(
        update={
            "trace_contract": TraceContract(
                recipes=[
                    TraceRecipe(
                        id="definition",
                        checkpoints=["state_factorization"],
                    )
                ]
            )
        }
    )

    def proposal(checkpoint_id: str) -> GradingProposal:
        return GradingProposal(
            diagnosis_md="The required factorization step is missing.",
            attempt_id="att",
            practice_item_id=item.id,
            rubric_score=0,
            criterion_evidence=[
                CriterionEvidence(
                    criterion_id="correctness",
                    points_awarded=0,
                    evidence="No definition supplied.",
                )
            ],
            error_attributions=[
                ErrorAttribution(
                    error_type="incomplete_answer",
                    evidence="The required step is absent.",
                    resolution_status="unresolved",
                    cause_scope="unknown",
                    first_divergence={
                        "anchor_kind": "missing_required_step",
                        "criterion_id": "correctness",
                        "checkpoint_id": checkpoint_id,
                    },
                )
            ],
            grader_confidence=0.8,
        )

    validated = validate_codex_grading_proposal(
        proposal("state_factorization"),
        attempt_id="att",
        item=item,
        vault=vault,
    )
    assert (
        validated.error_attributions[0].first_divergence["checkpoint_id"]
        == "state_factorization"
    )
    with pytest.raises(GradingValidationError, match="Unknown first-divergence checkpoint"):
        validate_codex_grading_proposal(
            proposal("invented_step"),
            attempt_id="att",
            item=item,
            vault=vault,
        )


def test_write_boundary_persists_firewall_telemetry(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id="pi_svd_define_001",
                learner_answer_md="A fully correct answer.",
            ),
            attempt_id="att_firewall",
            grade=ResolvedGrade(
                rubric_score=4,
                criterion_points={"correctness": 4},
                evidence_rows=[],
                error_attributions=[
                    GradeAttribution(
                        error_type="conceptual_slip",
                        severity=0.6,
                        target_evidence_families=["recall"],
                        target_criterion_ids=["correctness"],
                        resolution_status="resolved",
                    )
                ],
                grader_confidence=1.0,
                confidence=5,
                manual_review_reason=None,
            ),
        ),
        clock=FrozenClock(NOW),
    )

    event = repository.error_events_for_attempt(result.attempt_id)[0]
    assert not (event["repair_plan"] or {}).get("target_evidence_families")
    debug = repository.attempt_debug_payload(result.attempt_id)
    kinds = {
        entry["kind"]
        for entry in debug["causal_attribution"]["firewall_events"]
    }
    assert "passed_facet_write_blocked" in kinds
    assert "passed_criterion_write_blocked" in kinds


def test_machine_review_scope_blocks_negative_observation_attribution(tmp_path):
    paths = build_mvp07_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))

    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id="pi_svd_define_001",
                learner_answer_md="The item wording is defective.",
            ),
            attempt_id="att_item_fault",
            grade=ResolvedGrade(
                rubric_score=0,
                criterion_points={"correctness": 0},
                evidence_rows=[
                    {
                        "id": "ge_item_fault",
                        "criterion_id": "correctness",
                        "points_awarded": 0.0,
                        "evidence": "The item contract is suspect.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": NOW_ISO,
                    }
                ],
                error_attributions=[
                    GradeAttribution(
                        error_type="conceptual_slip",
                        severity=0.6,
                        target_criterion_ids=["correctness"],
                        cause_scope="item_contract",
                        resolution_status="resolved",
                    )
                ],
                grader_confidence=0.9,
                confidence=4,
                manual_review_reason="attribution_scope:item_contract",
            ),
        ),
        clock=FrozenClock(NOW),
    )

    evidence = repository.fetch_grading_evidence(result.attempt_id)
    assert len(evidence) == 1
    assert json.loads(evidence[0].attribution_json or "{}") == {
        "negative_evidence_blocked": "machine_review_scope",
        "targets": [],
    }


def test_provisional_belief_can_open_remediation(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    candidate_id = repository.insert_misconception_candidate(
        learning_object_id="lo_svd_definition",
        statement="believes Q and Q transpose are interchangeable",
        statement_normalized="believes q and q transpose are interchangeable",
        concept_id="singular_value_decomposition",
        target_facet="recall",
        facet_ids=["recall"],
        source_error_event_ids=[],
        surface_families=[],
        item_ids=[],
        occurrence_count=1,
        severity=0.7,
        clock=FrozenClock(NOW),
    )

    episode = start_remediation_episode(
        repository, candidate_id, clock=FrozenClock(NOW)
    )

    assert episode["case_kind"] == "diagnosis"
    assert episode["case_ref"] == candidate_id


def test_variant_direction_audit_is_symmetric(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    source = vault.practice_items["pi_svd_define_001"].model_copy(
        update={
            "difficulty": 0.5,
            "task_features": {
                "complexity": 2,
                "span": "multi_step",
                "response": "structured_steps",
                "transfer": "near",
                "scaffolding": "cue",
            },
        }
    )
    harder = {
        "difficulty": 0.4,
        "task_features": {
            "complexity": 1,
            "span": "single_step",
            "response": "short_constructed",
            "transfer": "same_context",
            "scaffolding": "partial",
        },
        "variant_contract": {
            "intended_manipulations": [],
            "incidental_changes": [],
        },
    }
    easier = {
        "difficulty": 0.6,
        "task_features": {
            "complexity": 3,
            "span": "whole_task",
            "response": "long_constructed",
            "transfer": "far",
            "scaffolding": "none",
        },
        "variant_contract": {
            "intended_manipulations": [],
            "incidental_changes": [],
        },
    }

    harder_violations = audit_variant_direction(source, harder, "harder")
    easier_violations = audit_variant_direction(source, easier, "easier")
    assert any("difficulty" in value for value in harder_violations)
    assert any("span" in value for value in harder_violations)
    assert any("difficulty" in value for value in easier_violations)
    assert any("span" in value for value in easier_violations)


def test_learner_confirmation_resolves_factor_to_provisional_belief(tmp_path):
    paths = build_mvp07_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_ambiguous_001",
            learner_answer_md="An answer.",
        ),
        SelfGradeInput(
            criterion_points={"whole_item": 0},
            fatal_errors=[],
            confidence=4,
        ),
        clock=clock,
    )
    factor = repository.unresolved_cause_factors_for_attempt(result.attempt_id)[0]
    before = feedback_bundle(vault, repository, result.attempt_id)
    assert before["unresolvedCauses"][0]["selfReportQuestion"] is not None

    report = record_unresolved_cause_self_report(
        vault,
        repository,
        factor_id=factor["id"],
        response="believed_candidate",
        candidate_index=0,
        clock=clock,
    )

    assert report["resolved"] is True
    assert report["provisional_belief_id"] is not None
    assert repository.unresolved_cause_factor(factor["id"])["status"] == "resolved"


def test_nonconfirming_self_report_is_recorded_once_without_reprompt(tmp_path):
    paths = build_mvp07_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_ambiguous_001",
            learner_answer_md="An answer.",
        ),
        SelfGradeInput(
            criterion_points={"whole_item": 0},
            fatal_errors=[],
            confidence=4,
        ),
        clock=clock,
    )
    factor = repository.unresolved_cause_factors_for_attempt(result.attempt_id)[0]

    report = record_unresolved_cause_self_report(
        vault,
        repository,
        factor_id=factor["id"],
        response="slipped",
        clock=clock,
    )
    assert report["resolved"] is False
    presented = repository.unresolved_cause_factors_for_attempt(result.attempt_id)[0]
    assert presented["self_report"]["response"] == "slipped"
    after = feedback_bundle(vault, repository, result.attempt_id)
    assert after["unresolvedCauses"][0]["selfReport"]["response"] == "slipped"
    assert after["unresolvedCauses"][0]["selfReportQuestion"] is None

    with pytest.raises(ValueError, match="already has a learner report"):
        record_unresolved_cause_self_report(
            vault,
            repository,
            factor_id=factor["id"],
            response="diagnosis_wrong",
            clock=clock,
        )
