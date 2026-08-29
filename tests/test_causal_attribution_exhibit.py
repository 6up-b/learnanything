"""Regression replay for the causal-attribution post-mortem exhibit.

The IDs and criterion vector below are the historical attempt named by
spec_causal_attribution_v1.md. The authored contract is the corrected P0b
contract: multiplication is measured directly; branch retention and ± scoping
are item-local steps.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.diagnosis.followups import evaluate_attempt_intervention_followup
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import (
    NOW,
    NOW_ISO,
    create_basic_vault,
    set_algorithm_version,
    write_facets,
)

EXHIBIT_ATTEMPT_ID = "01KY64FZE7ZVJ79YJFWAYZH53Q"
EXHIBIT_ITEM_ID = "pi_exercise_01ky5raxvexp8axggqn8e73vkh"
EXHIBIT_LO_ID = "lo_compute_with_complex_numbers"
MULTIPLICATION = "facet_multiply_complex_numbers_by_distributing_replaci"
ADDITION = "facet_add_complex_numbers_componentwise_a_bi_c_di_a_c_"


def _evidence_rows(points: dict[str, float], suffix: str = "") -> list[dict[str, object]]:
    return [
        {
            "id": f"ge_{criterion_id}{suffix}",
            "criterion_id": criterion_id,
            "points_awarded": awarded,
            "evidence": f"Exhibit evidence for {criterion_id}.",
            "notes": None,
            "local_grader_id": "exhibit_replay",
            "grader_tier": 1,
            "created_at": NOW_ISO,
        }
        for criterion_id, awarded in points.items()
    ]


@pytest.fixture
def exhibit(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_facets(
        paths,
        [
            {
                "id": MULTIPLICATION,
                "kind": "procedure_contract",
                "claim": "Multiply complex numbers by distributing and replacing i² with -1.",
            },
            {
                "id": ADDITION,
                "kind": "procedure_contract",
                "claim": "Add complex numbers componentwise.",
            },
            {"id": "recall", "kind": "definition", "claim": "Recall SVD."},
        ],
    )
    write_yaml(
        paths.learning_object_path("linear-algebra", EXHIBIT_LO_ID),
        {
            "schema_version": 1,
            "id": EXHIBIT_LO_ID,
            "title": "Compute with Complex Numbers",
            "subjects": ["linear-algebra"],
            "concept": "singular_value_decomposition",
            "knowledge_type": "procedure",
            "status": "active",
            "summary": "Compute with complex numbers.",
            "prerequisites": [],
            "confusables": [],
            "blueprints": [],
            "tags": [],
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    write_yaml(
        paths.practice_item_path("linear-algebra", EXHIBIT_ITEM_ID),
        {
            "schema_version": 1,
            "id": EXHIBIT_ITEM_ID,
            "learning_object_id": EXHIBIT_LO_ID,
            "practice_mode": "worked_solution",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": [MULTIPLICATION, ADDITION],
            "evidence_weights": {MULTIPLICATION: 0.8, ADDITION: 0.2},
            "criterion_facet_weights": {"expand_square": {MULTIPLICATION: 1.0}},
            "prompt": "Find two distinct square roots of i.",
            "expected_answer": "The roots are ±(1+i)/sqrt(2), with ± applying to the whole number.",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [
                    {
                        "id": "expand_square",
                        "points": 1,
                        "description": "Expand (a+bi)^2 correctly.",
                        "measurement_status": "direct",
                        "targets": [
                            {
                                "facet": MULTIPLICATION,
                                "capability": "procedure_execution",
                                "role": "primary",
                            }
                        ],
                    },
                    {
                        "id": "form_equations",
                        "points": 1,
                        "description": "Equate real and imaginary components.",
                        "measurement_status": "item_local",
                        "targets": [],
                        "depends_on": ["expand_square"],
                    },
                    {
                        "id": "solve_equations",
                        "points": 1,
                        "description": "Retain both sign branches.",
                        "measurement_status": "item_local",
                        "targets": [],
                        "depends_on": ["form_equations"],
                    },
                    {
                        "id": "state_roots",
                        "points": 1,
                        "description": "Scope ± over the complete root.",
                        "measurement_status": "item_local",
                        "targets": [],
                        "depends_on": ["solve_equations"],
                    },
                ],
                "fatal_errors": [],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    set_algorithm_version(paths, "mvp-0.7")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


def test_exhibit_replay_blocks_false_targets_promotion_and_retry(exhibit):
    vault, repository = exhibit
    points = {
        "expand_square": 1.0,
        "form_equations": 1.0,
        "solve_equations": 0.5,
        "state_roots": 0.5,
    }
    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=EXHIBIT_ITEM_ID,
                learner_answer_md="±sqrt(1/2) + sqrt(1/2)i",
            ),
            attempt_id=EXHIBIT_ATTEMPT_ID,
            grade=ResolvedGrade(
                rubric_score=3,
                criterion_points=points,
                evidence_rows=_evidence_rows(points),
                error_attributions=[
                    GradeAttribution(
                        error_type="local_slip",
                        severity=0.3,
                        evidence="The expansion itself was correct.",
                        target_evidence_families=[MULTIPLICATION],
                        target_criterion_ids=["expand_square"],
                        resolution_status="resolved",
                        cause_scope="transient_execution",
                    ),
                    GradeAttribution(
                        error_type="representation_notation_error",
                        severity=0.8,
                        evidence="The ± symbol scopes only over the real component.",
                        is_misconception=True,
                        misconception_statement="The learner scopes ± over only one component.",
                        misconception_consistent_answer="±a+ai",
                        target_criterion_ids=["state_roots"],
                        resolution_status="resolved",
                        cause_scope="learner_state",
                        target_ref={
                            "kind": "item_step",
                            "checkpoint_id": "state_roots",
                        },
                        operation="scope_plus_minus",
                        first_divergence={
                            "anchor_kind": "whole_answer",
                            "criterion_id": "state_roots",
                        },
                    ),
                ],
                repair_suggestions=[
                    {
                        "practice_mode": "targeted_review",
                        "rationale": "Repair sign enumeration and notation scope.",
                        "target_evidence_families": [MULTIPLICATION],
                        "target_criterion_ids": ["solve_equations", "state_roots"],
                    }
                ],
                grader_confidence=0.99,
                confidence=5,
                manual_review_reason=None,
                diagnosis_md="Expansion passed; the error is branch retention and ± scope.",
            ),
        ),
        clock=FrozenClock(NOW),
    )

    events = {
        event["error_type"]: event
        for event in repository.error_events_for_attempt(EXHIBIT_ATTEMPT_ID)
    }
    notation_plan = events["representation_notation_error"]["repair_plan"] or {}
    assert notation_plan.get("target_evidence_families", []) == []
    assert notation_plan["target_ref"]["kind"] == "item_step"
    assert MULTIPLICATION not in result.repair_suggestions[0]["target_evidence_families"]

    decision = evaluate_attempt_intervention_followup(
        vault,
        repository,
        result=result,
        manual_override=True,
        clock=FrozenClock(NOW),
    )
    assert repository.misconceptions_for_learning_object(EXHIBIT_LO_ID) == []
    assert repository.misconception_candidates_for_learning_object(EXHIBIT_LO_ID)
    need = repository.intervention_need_for_attempt(EXHIBIT_ATTEMPT_ID)
    assert decision.need_id is not None and need is not None
    assert MULTIPLICATION not in need["target_facets"]

    firewall_events = repository.attempt_debug_payload(EXHIBIT_ATTEMPT_ID)[
        "causal_attribution"
    ]["firewall_events"]
    assert any(
        event["kind"] == "passed_facet_write_blocked"
        and event["target"] == MULTIPLICATION
        for event in firewall_events
    )


def test_exhibit_positive_control_preserves_genuine_multiplication_failure(exhibit):
    vault, repository = exhibit
    points = {
        "expand_square": 0.0,
        "form_equations": 0.0,
        "solve_equations": 0.0,
        "state_roots": 0.0,
    }
    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=EXHIBIT_ITEM_ID,
                learner_answer_md="(a+bi)^2 = a^2+b^2i",
            ),
            attempt_id="01KY64FZE7ZVJ79YJFWAYZH53Q_MULTIPLICATION_CONTROL",
            grade=ResolvedGrade(
                rubric_score=0,
                criterion_points=points,
                evidence_rows=_evidence_rows(points, "_multiplication_control"),
                error_attributions=[
                    GradeAttribution(
                        error_type="procedure_misapplication",
                        severity=0.8,
                        evidence="The complex square was expanded incorrectly.",
                        target_evidence_families=[MULTIPLICATION],
                        target_criterion_ids=["expand_square"],
                        resolution_status="resolved",
                        cause_scope="learner_state",
                        target_ref={
                            "kind": "facet_capability",
                            "facet_id": MULTIPLICATION,
                            "capability": "procedure_execution",
                        },
                    )
                ],
                grader_confidence=0.99,
                confidence=5,
                manual_review_reason=None,
            ),
        ),
        clock=FrozenClock(NOW),
    )

    event = repository.error_events_for_attempt(result.attempt_id)[0]
    assert (event["repair_plan"] or {})["target_evidence_families"] == [
        MULTIPLICATION
    ]
    assert not any(
        audit.get("target") == MULTIPLICATION
        for audit in repository.attempt_debug_payload(result.attempt_id)[
            "causal_attribution"
        ]["firewall_events"]
    )
