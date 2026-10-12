"""PF-c grading support in the blind grader (Slice 2 §5.5, joined at Slice 1 S1.1)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from learnloop.attempts.blind_grading import (
    BLIND_GRADING_PROMPT_VERSION,
    BlindGradingProposal,
    blind_grading_context,
    blind_grading_context_hash,
    blind_grading_prompt,
    blind_prompt_version,
)
from learnloop.attempts.grading import resolved_rubric
from learnloop.attempts.grading_support import (
    REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION,
    REFERENCE_POLICY_PROMPT_VERSION,
    UNVERIFIED_REVIEW_REASON,
    apply_valid_alternative_gate,
    grade_uncertainty_signal,
    modal_sample,
    reference_policy,
    request_blind_grading_run,
    sample_fingerprint,
)
from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import ReviewFakeClient, prompt_payload
from tests.diagnosis_split_helpers import build_diagnosis_vault
from tests.split_live_helpers import split_vault, submit


def _proposal(points: dict[str, float], *, quote: str | None = "U Sigma V", criterion: str = "result", scope: str = "valid_measurement"):
    attributions = []
    if quote is not None:
        attributions.append(
            {
                "error_type": "conceptual_slip",
                "evidence": "x",
                "first_divergence": {"anchor_kind": "span", "criterion_id": criterion, "quote": quote},
                "target_criterion_ids": [criterion],
                "validity_scope": scope,
                "resolution_status": "resolved",
            }
        )
    return BlindGradingProposal.model_validate(
        {
            "local_analysis_md": "reading",
            "attempt_id": "att",
            "practice_item_id": "pi_svd_compute_001",
            "criterion_evidence": [
                {"criterion_id": key, "points_awarded": value, "evidence": "e"} for key, value in points.items()
            ],
            "rubric_score": int(sum(points.values())),
            "error_attributions": attributions,
            "grader_confidence": 0.8,
        }
    )


def _vault(tmp_path):
    paths = build_diagnosis_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    item = vault.practice_items["pi_svd_compute_001"]
    return vault, item, resolved_rubric(vault, item)


def test_reference_policy_is_item_side_and_deterministic(tmp_path):
    vault, item, _rubric = _vault(tmp_path)
    matches = reference_policy(item, "work...\nFinal answer: U Sigma V^T")
    assert matches["reference_status"] == "authored"
    assert matches["final_answer_check"]["status"] == "matches_reference"
    assert reference_policy(item, "the answer is 7")["final_answer_check"]["status"] != "matches_reference"
    context = blind_grading_context(vault, item, attempt_id="a", learner_answer_md="x")
    # No policy: the M1 mvp-2.0 prompt and hash, byte for byte.
    assert blind_prompt_version(context) == BLIND_GRADING_PROMPT_VERSION
    assert "reference_policy" not in blind_grading_prompt(context)
    with_policy = replace(context, reference_policy=reference_policy(item, "x"))
    assert blind_prompt_version(with_policy) == REFERENCE_POLICY_PROMPT_VERSION
    prompt = blind_grading_prompt(with_policy)
    assert "SOLVE FIRST" in prompt and "VALID ALTERNATIVES" in prompt
    assert prompt_payload(prompt)["context"]["reference_policy"]["reference_status"] == "authored"
    assert blind_grading_context_hash(with_policy) != blind_grading_context_hash(context)


def test_gate_records_unlocated_failures_on_a_verifying_answer_as_unverified(tmp_path):
    _vault_obj, item, rubric = _vault(tmp_path)
    answer = "A different route...\nFinal answer: U Sigma V^T"
    policy = reference_policy(item, answer)
    # The grader marked "result" down but its quote is not in the learner's work.
    proposal = _proposal({"setup": 2, "result": 0}, quote="not in the answer")

    gate = apply_valid_alternative_gate(proposal, rubric=rubric, learner_answer_md=answer, policy=policy)

    assert gate.applied and gate.reason == UNVERIFIED_REVIEW_REASON
    assert gate.unverified_criterion_ids == ("result",)
    assert gate.proposal.error_attributions[0].validity_scope == "grader_interpretation"
    assert gate.proposal.manual_review_recommended is True
    # Points are never credited by the gate.
    assert [row.points_awarded for row in gate.proposal.criterion_evidence] == [2, 0]


def test_gate_keeps_a_located_error_and_never_fires_on_a_wrong_final_answer(tmp_path):
    _vault_obj, item, rubric = _vault(tmp_path)
    answer = "I wrote U Sigma V then fixed it\nFinal answer: U Sigma V^T"
    located = apply_valid_alternative_gate(
        _proposal({"setup": 2, "result": 0}, quote="U Sigma V"),
        rubric=rubric, learner_answer_md=answer, policy=reference_policy(item, answer),
    )
    assert located.applied is False
    wrong = "Final answer: U Sigma V"
    untouched = apply_valid_alternative_gate(
        _proposal({"setup": 2, "result": 0}, quote="nowhere"),
        rubric=rubric, learner_answer_md=wrong, policy=reference_policy(item, wrong),
    )
    assert untouched.applied is False
    assert untouched.proposal.error_attributions[0].validity_scope == "valid_measurement"


def test_split_mode_fingerprint_and_asymmetric_shadow_log(tmp_path):
    _vault_obj, _item, rubric = _vault(tmp_path)
    failing = _proposal({"setup": 2, "result": 0})
    passing = _proposal({"setup": 2, "result": 2}, quote=None)
    assert sample_fingerprint(failing, rubric) != sample_fingerprint(passing, rubric)
    # Fingerprint ignores causal content entirely (there is none) and prose.
    assert sample_fingerprint(failing, rubric) == sample_fingerprint(
        failing.model_copy(update={"local_analysis_md": "other words"}), rubric
    )
    winner, log = modal_sample([failing, failing, passing], rubric)
    assert winner == 0 and log["winner_votes"] == 2
    assert log["asymmetric_rule"]["would_differ"] is True
    assert log["asymmetric_rule"]["criteria_modal_fails_not_unanimous"] == ["result"]


def test_uncertainty_signal_is_shadow_and_within_family():
    quiet = grade_uncertainty_signal(score_fraction=1.0, grader_confidence=0.9, prior_fractions=[], family="surface:x")
    assert quiet["shadow"] is True and quiet["would_suggest"] == []
    loud = grade_uncertainty_signal(score_fraction=0.0, grader_confidence=0.4, prior_fractions=[1.0, 1.0], family="surface:x")
    assert loud["disagreement"] == 1.0 and loud["would_suggest"] == ["manual_review", "clarification", "regrade"]


def test_live_blind_grade_records_grading_support_and_its_calibration_identity(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    client = ReviewFakeClient()
    result = submit(vault, repository, client)

    record = repository.latest_blind_grade_record(result.attempt_id)
    assert record["grading_prompt_version"] == REFERENCE_POLICY_PROMPT_VERSION
    support = record["record"]["grading_support"]
    assert support["reference_policy"]["reference_status"] == "authored"
    assert support["uncertainty_signal"]["shadow"] is True
    assert record["record"]["calibration_prompt_version"] == REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION
    with repository.connection() as connection:
        identity = connection.execute(
            "SELECT grading_prompt_version, grader_output_schema_version FROM raw_grade_events WHERE attempt_id = ?",
            (result.attempt_id,),
        ).fetchone()
    assert tuple(identity) == (REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION, "blind_grading_proposal_v1")
    assert "SOLVE FIRST" in client.prompts[0]


def test_grading_support_kill_switch_restores_the_mvp_2_0_blind_prompt(tmp_path):
    _paths, vault, repository = split_vault(tmp_path, config="[diagnosis]\ngrading_support = false")
    client = ReviewFakeClient()
    result = submit(vault, repository, client)

    record = repository.latest_blind_grade_record(result.attempt_id)
    assert record["grading_prompt_version"] == BLIND_GRADING_PROMPT_VERSION
    assert "SOLVE FIRST" not in client.prompts[0]
    with repository.connection() as connection:
        identity = connection.execute(
            "SELECT grading_prompt_version FROM raw_grade_events WHERE attempt_id = ?",
            (result.attempt_id,),
        ).fetchone()
    assert identity[0] == "grading_prompt_v2_blind"


def test_request_blind_grading_run_samples_and_gates(tmp_path):
    vault, item, rubric = _vault(tmp_path)
    answer = "Final answer: U Sigma V^T"
    context = replace(
        blind_grading_context(vault, item, attempt_id="a1", learner_answer_md=answer),
        reference_policy=reference_policy(item, answer),
    )
    run = request_blind_grading_run(ReviewFakeClient(), context, rubric=rubric, sample_count=3)
    assert run.samples == 3 and run.prompt_version == REFERENCE_POLICY_PROMPT_VERSION
    assert run.grading_support["sampling"]["sample_count"] == 3
    assert run.grading_support["reference_policy"]["final_answer_check"]["status"] == "matches_reference"


def test_worked_solution_references_check_against_their_numeric_conclusion():
    from learnloop.attempts.answer_check import final_answer_check, reference_final_answer

    worked = "Choose the first card in 3 ways and the second in 2, giving |E|=6. Therefore P(E)=6/20=3/10."
    assert reference_final_answer(worked) == "3/10"
    assert final_answer_check("Therefore P(E) = 0.3.", worked)["status"] == "matches_reference"
    assert final_answer_check("Final answer: 3/10", worked)["method"].endswith("+reference_conclusion")
    # Conservative: only a consistent, all-numeric chain or a bare number is extracted.
    for text in ("Thus x = 2 when y = 3.", "Hence P = 6/20 = 1/3.", "So it is about 0.63.", "It equals 3/10 because z."):
        assert reference_final_answer(text) is None
    assert final_answer_check("Therefore P(E) = 6/20 = 1/3.", worked)["status"] == "undecidable"
    # A bare reference is compared whole, as before.
    assert reference_final_answer("4") is None
    assert final_answer_check("Final answer: 4", "4") == {"status": "matches_reference", "method": "exact_match"}


class _ZeroWithoutAttribution(ReviewFakeClient):
    """Marks ``result`` down to zero on any answer, naming no error at all."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        evidence = [
            row.model_copy(update={"points_awarded": 0.0}) if row.criterion_id == "result" else row
            for row in result.criterion_evidence
        ]
        return result.model_copy(
            update={
                "criterion_evidence": evidence,
                "rubric_score": int(sum(row.points_awarded for row in evidence)),
                "error_attributions": [],
            }
        )


def _negative_mass(repository, facet: str) -> float:
    return sum(
        cell.direct_negative_mass + cell.embedded_negative_mass
        for cell in repository.facet_capability_evidence_all()
        if cell.facet_id == facet
    )


def test_an_unverified_criterion_writes_no_negative_evidence_even_without_an_attribution(tmp_path):
    """Review F1: the final answer verifies, the grader zeroes a criterion and
    names no error. The criterion is unverified; neither the live grade nor a
    regrade may bank its failure on the criterion's facet through the
    projection's single-target fallback."""

    import json

    from learnloop.attempts.regrade import regrade_attempt
    from learnloop.substrate.canonical_projection import project_canonical_facet_state

    from tests.split_live_helpers import ReadyRuntime

    _paths, vault, repository = split_vault(tmp_path)
    project_canonical_facet_state(vault, repository)
    before = _negative_mass(repository, "recall")  # "result" measures recall
    client = _ZeroWithoutAttribution()
    result = submit(vault, repository, client, answer="A different route.\nFinal answer: U Sigma V^T")

    record = repository.latest_blind_grade_record(result.attempt_id)
    assert record["record"]["grading_support"]["unverified_criterion_ids"] == ["result"]
    assert _negative_mass(repository, "recall") == pytest.approx(before)
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(result.attempt_id)}
    assert rows["result"].points_awarded == 0
    assert json.loads(rows["result"].attribution_json)["negative_evidence_blocked"] == UNVERIFIED_REVIEW_REASON
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    assert attempt["manual_review_reason"] == UNVERIFIED_REVIEW_REASON

    regrade_attempt(vault, repository, attempt, runtime=ReadyRuntime(), client=client, grading_source="ai", clock=None)
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(result.attempt_id)}
    assert json.loads(rows["result"].attribution_json)["negative_evidence_blocked"] == UNVERIFIED_REVIEW_REASON
    assert _negative_mass(repository, "recall") == pytest.approx(before)
    assert repository.fetch_practice_attempt(result.attempt_id)["manual_review_reason"] == UNVERIFIED_REVIEW_REASON
    project_canonical_facet_state(vault, repository)
    assert _negative_mass(repository, "recall") == pytest.approx(before)


def test_an_unverified_multi_target_criterion_opens_no_unresolved_cause_factor(tmp_path):
    """Review F1 (projection side): the block is enforced where evidence is
    projected. An unverified failure on a criterion with two targets is not
    an observed unresolved failure either, so it opens no factor."""

    from learnloop.vault.yaml_io import read_yaml, write_yaml

    paths, _vault, repository = split_vault(tmp_path)
    item_path = paths.practice_item_path("linear-algebra", "pi_svd_compute_001")
    item = read_yaml(item_path)
    for criterion in item["grading_rubric"]["criteria"]:
        if criterion["id"] == "result":
            criterion["targets"] = [
                {"facet": "recall", "capability": "retrieval"},
                {"facet": "compute", "capability": "procedure_execution"},
            ]
    write_yaml(item_path, item)
    vault = load_vault(paths.root)
    result = submit(vault, repository, _ZeroWithoutAttribution(), answer="A different route.\nFinal answer: U Sigma V^T")

    assert repository.unresolved_cause_factors_for_attempt(result.attempt_id) == []
