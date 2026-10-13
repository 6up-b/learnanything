"""Slice 1 §4 / C2: the learner-blind grading contract.

Blindness is structural: ``BlindGradingContext`` has no field that can hold
learner history, and the rendered prompt carries no prior attempt id, trace,
grade or hypothesis even when the vault has a rich history.
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from learnloop.ai.strict_schema import strict_output_schema
from learnloop.attempts.ai_contracts import GradingContext
from learnloop.attempts.blind_grading import (
    BLIND_CALIBRATION_PROMPT_VERSION,
    BLIND_GRADER_OUTPUT_SCHEMA_VERSION,
    BLIND_GRADING_PROMPT_VERSION,
    BlindGradingContext,
    BlindGradingProposal,
    blind_grading_context,
    blind_grading_context_hash,
    blind_grading_prompt,
    request_blind_grading_proposal,
    to_grading_proposal,
    validate_blind_grading_proposal,
)
from learnloop.attempts.grading import GradingValidationError

from tests.diagnosis_fakes import ReviewFakeClient
from tests.diagnosis_split_helpers import build_diagnosis_vault, seed_history


@pytest.fixture()
def seeded(tmp_path):
    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, repository = seed_history(paths)
    return vault, repository


def _proposal(**overrides) -> BlindGradingProposal:
    payload = {
        "local_analysis_md": "The final factor V is not transposed in 'U Sigma V'.",
        "repaired_traces": [
            {
                "id": "rt1",
                "learner_work_prefix": "",
                "repair_insertion_point": {"anchor_kind": "span", "criterion_id": "result", "quote": "U Sigma V"},
                "minimal_edit": "transpose V",
                "regenerated_work": "U Sigma V^T",
                "repaired_answer_md": "U Sigma V^T",
            }
        ],
        "attempt_id": "att_new",
        "practice_item_id": "pi_svd_compute_001",
        "criterion_evidence": [
            {"criterion_id": "setup", "points_awarded": 2, "evidence": "set up"},
            {"criterion_id": "result", "points_awarded": 0, "evidence": "wrong factor"},
        ],
        "rubric_score": 2,
        "error_attributions": [
            {
                "error_type": "conceptual_slip",
                "evidence": "V is not transposed.",
                "first_divergence": {"anchor_kind": "span", "criterion_id": "result", "quote": "U Sigma V"},
                "target_evidence_families": ["recall"],
                "resolution_status": "unresolved",
                "validity_scope": "valid_measurement",
                "repaired_trace_id": "rt1",
            }
        ],
        "grader_confidence": 0.8,
    }
    payload.update(overrides)
    return BlindGradingProposal.model_validate(payload)


def test_blind_context_has_no_history_capable_field():
    blind = {field.name for field in dataclasses.fields(BlindGradingContext)}
    joint = {field.name for field in dataclasses.fields(GradingContext)}
    # Exactly today's context minus the C4 history (§4.1), plus PF-c's
    # reference policy, which is item-side and this-answer-only (Slice 2 §5.5),
    # and mvp-0.13's answer prompt: how THIS answer was asked for ("I'm stuck"),
    # a fixed constant, never history.
    assert blind == (joint - {"diagnostic_history"}) | {"reference_policy", "answer_prompt"}
    forbidden = ("history", "prior", "hypothes", "diagnos", "retriev", "misconception")
    assert not [name for name in blind if any(token in name for token in forbidden)]
    # The facet registry is item-side vocabulary (S1 keeps it); the
    # misconception registry is learner-derived and has no field here.
    assert "facet_registry" in blind


def test_rendered_blind_prompt_contains_no_prior_attempt_or_hypothesis(seeded):
    vault, repository = seeded
    item = vault.practice_items["pi_svd_compute_001"]
    context = blind_grading_context(vault, item, attempt_id="att_new", learner_answer_md="A = U Sigma V once more")
    prompt = blind_grading_prompt(context)
    with repository.connection() as connection:
        prior_ids = [row[0] for row in connection.execute("SELECT id FROM practice_attempts")]
        prior_answers = [row[0] for row in connection.execute("SELECT learner_answer_md FROM practice_attempts")]
        statements = [row[0] for row in connection.execute("SELECT statement FROM causal_hypotheses")]
    assert prior_ids and statements
    for value in [*prior_ids, *statements]:
        assert value not in prompt
    for answer in prior_answers:
        assert f'"learner_answer_md": {json.dumps(answer)}' not in prompt
    assert "diagnostic_history" not in prompt
    assert f"prompt_version: {BLIND_GRADING_PROMPT_VERSION}" in prompt


def test_blind_prompt_drops_every_causal_instruction(seeded):
    vault, _repository = seeded
    item = vault.practice_items["pi_svd_compute_001"]
    prompt = blind_grading_prompt(blind_grading_context(vault, item, attempt_id="x", learner_answer_md="y"))
    task = json.loads(prompt.split("\n\n")[-1])["task"]
    for phrase in (
        "candidate_causes",
        "misconception_statement",
        "eliciting_question",
        "prior_weight",
        "postdictive",
        "test recurrence",
        "diagnostic_history",
        "operator",
    ):
        assert phrase not in task
    assert "LEARNER-BLIND" in task
    assert BLIND_GRADING_PROMPT_VERSION == "mvp-2.0-blind-local-grader"
    assert BLIND_CALIBRATION_PROMPT_VERSION == "grading_prompt_v2_blind"
    assert BLIND_GRADER_OUTPUT_SCHEMA_VERSION == "blind_grading_proposal_v1"


def test_generation_order_is_local_analysis_then_traces_then_facets_last():
    properties = list(strict_output_schema(BlindGradingProposal)["properties"])
    assert properties[:2] == ["local_analysis_md", "repaired_traces"]
    assert properties[-1] == "exercised_facets"
    attribution = strict_output_schema(BlindGradingProposal)["$defs"]["BlindErrorAttribution"]["properties"]
    for causal in ("candidate_causes", "misconception_statement", "operation", "causal_confidence", "cause_scope", "is_misconception"):
        assert causal not in attribution
    assert "validity_scope" in attribution


def test_field_mapping_onto_the_joint_shape(seeded):
    vault, _repository = seeded
    proposal = _proposal(
        error_attributions=[
            {
                "error_type": "conceptual_slip",
                "evidence": "x",
                "resolution_status": "unresolved",
                "validity_scope": "item_contract",
            },
            {
                "error_type": "arithmetic_slip",
                "evidence": "y",
                "resolution_status": "unresolved",
                "validity_scope": "valid_measurement",
            },
        ]
    )
    joint = to_grading_proposal(proposal, vault=vault)
    assert joint.diagnosis_md == proposal.local_analysis_md
    assert [suggestion.repaired_trace.minimal_edit for suggestion in joint.repair_suggestions] == ["transpose V"]
    assert all(not suggestion.operator for suggestion in joint.repair_suggestions)
    first, second = joint.error_attributions
    assert first.cause_scope == "item_contract"
    assert second.cause_scope == "unknown"
    # O2: the misconception flag is the taxonomy prior, never the model's.
    assert first.is_misconception is True
    assert second.is_misconception is False
    assert all(not row.candidate_causes and row.misconception_statement is None for row in joint.error_attributions)


def test_validator_accepts_reanchors_and_keeps_blind_fields(seeded):
    vault, _repository = seeded
    item = vault.practice_items["pi_svd_compute_001"]
    answer = "So A = U Sigma V and done."
    validated = validate_blind_grading_proposal(_proposal(), attempt_id="att_new", item=item, vault=vault, learner_answer_md=answer)
    assert validated.grade.rubric_score == 2
    divergence = validated.grade.error_attributions[0].first_divergence
    assert divergence["char_start"] == answer.index("U Sigma V")
    assert validated.validity_scopes == ("valid_measurement",)
    assert validated.attribution_trace_ids == ("rt1",)
    record = validated.as_record()
    assert record["grader_mode"] == "blind"
    assert record["repaired_traces"][0]["id"] == "rt1"
    assert record["error_attributions"][0]["validity_scope"] == "valid_measurement"
    assert "candidate_causes" not in json.dumps(record)


def test_validator_rejects_unknown_criterion_and_duplicate_trace_ids(seeded):
    vault, _repository = seeded
    item = vault.practice_items["pi_svd_compute_001"]
    with pytest.raises(GradingValidationError):
        validate_blind_grading_proposal(
            _proposal(criterion_evidence=[{"criterion_id": "nope", "points_awarded": 1, "evidence": "e"}]),
            attempt_id="att_new", item=item, vault=vault, learner_answer_md="U Sigma V",
        )
    duplicate = _proposal()
    duplicate.repaired_traces.append(duplicate.repaired_traces[0])
    with pytest.raises(GradingValidationError):
        validate_blind_grading_proposal(duplicate, attempt_id="att_new", item=item, vault=vault, learner_answer_md="U Sigma V")
    with pytest.raises(GradingValidationError):
        validate_blind_grading_proposal(_proposal(), attempt_id="other", item=item, vault=vault, learner_answer_md="U Sigma V")


def test_dangling_repaired_trace_reference_is_dropped(seeded):
    vault, _repository = seeded
    item = vault.practice_items["pi_svd_compute_001"]
    proposal = _proposal()
    proposal.error_attributions[0].repaired_trace_id = "rt9"
    validated = validate_blind_grading_proposal(proposal, attempt_id="att_new", item=item, vault=vault, learner_answer_md="U Sigma V")
    assert validated.attribution_trace_ids == (None,)


def test_request_uses_the_blind_operation_and_hash_is_stable(seeded):
    vault, _repository = seeded
    item = vault.practice_items["pi_svd_compute_001"]
    context = blind_grading_context(vault, item, attempt_id="att_new", learner_answer_md="U Sigma V")
    client = ReviewFakeClient()
    proposal = request_blind_grading_proposal(client, context)
    assert client.calls == ["blind_grading"]
    assert proposal.attempt_id == "att_new"
    assert blind_grading_context_hash(context) == blind_grading_context_hash(
        blind_grading_context(vault, item, attempt_id="att_new", learner_answer_md="U Sigma V")
    )


def test_shared_fakes_answer_the_blind_and_diagnosis_purposes(seeded):
    from tests import structured_ai
    from tests.openai_fakes import blind_grading_json

    vault, _repository = seeded
    item = vault.practice_items["pi_svd_compute_001"]
    context = blind_grading_context(vault, item, attempt_id="att_new", learner_answer_md="U Sigma V")

    class Fake(structured_ai.StructuredClientFake):
        def run_blind_grading_proposal(self, received):
            assert isinstance(received, BlindGradingContext)
            payload = json.loads(blind_grading_json())
            payload.update(
                attempt_id=received.attempt_id,
                practice_item_id=received.practice_item_id,
                criterion_evidence=[
                    {"criterion_id": "setup", "points_awarded": 2, "evidence": "ok"},
                    {"criterion_id": "result", "points_awarded": 2, "evidence": "ok"},
                ],
            )
            return BlindGradingProposal.model_validate(payload)

    proposal = request_blind_grading_proposal(Fake(), context)
    assert proposal.rubric_score == 4 and proposal.local_analysis_md == "Correct."
    assert structured_ai._HANDLER_FOR_PURPOSE["diagnosis"] == "run_diagnosis_proposal"
