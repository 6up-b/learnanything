"""Slice 1 §5.3–5.5 / C4: every validator rule has a rejecting case."""

from __future__ import annotations

import pytest

from learnloop.ai.strict_schema import strict_output_schema
from learnloop.attempts.grading import resolved_rubric
from learnloop.diagnosis.split.context import assemble_diagnosis_context, current_attempt_from
from learnloop.diagnosis.split.contract import (
    DiagnosisProposal,
    RecitingDiagnosisProposal,
    as_diagnosis_proposal,
    diagnosis_prompt,
    proposal_model_for,
)
from learnloop.diagnosis.split.history import (
    HypothesisRecord,
    RegistryRecord,
    StaticHistoryStore,
    VaultHistoryStore,
)
from learnloop.diagnosis.split.settings import DiagnosisSettings
from learnloop.diagnosis.split.validation import local_support, validate_diagnosis_proposal

from tests.diagnosis_split_helpers import blind_record, build_diagnosis_vault, seed_history

VALID = {"error_type": "conceptual_slip", "first_divergence": {"anchor_kind": "span", "criterion_id": "result", "quote": "U Sigma V"},
         "target_evidence_families": ["recall"], "target_criterion_ids": ["result"], "resolution_status": "unresolved",
         "validity_scope": "valid_measurement", "evidence": "Blind evidence."}


@pytest.fixture()
def world(tmp_path):
    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, repository = seed_history(paths)
    real = VaultHistoryStore(vault, repository)
    store = StaticHistoryStore(
        attempts=real.all_attempts(),
        hypotheses=[
            HypothesisRecord(
                id="hyp_prior", kind="causal_hypothesis", statement="Thinks transposing changes nothing.",
                scope="learner_state", status="candidate", lifecycle="candidate", learning_object_id="lo_svd_compute",
                source_attempt_id="att_02_svd_fail", validated_evidence_count=1, last_updated="2026-05-01T10:00:00Z",
                target_facets=("recall",),
            )
        ],
        registry=[
            RegistryRecord(id="mc_durable", kind="durable", statement="Thinks V needs no transpose.", learning_object_id="lo_svd_compute",
                           status="active", facet_ids=("recall",), occurrence_count=2, source_attempt_id="att_02_svd_fail"),
        ],
    )
    return vault, store


def _assembled(vault, store, *, criteria=None, attributions=None, mode="exact", traces=None):
    attempt = store.attempt("att_06_svd_fail")
    item = vault.practice_items[attempt.practice_item_id]
    record = blind_record(
        score=sum((criteria or {"setup": 2, "result": 0}).values()), max_points=4,
        criteria=criteria or {"setup": 2, "result": 0},
        attributions=attributions if attributions is not None else [VALID],
        local_analysis="The final factor V is not transposed.",
        traces=traces if traces is not None else [{"id": "rt1", "minimal_edit": "transpose V", "repaired_answer_md": "U Sigma V^T", "learner_work_prefix": "", "changed_latent_claims": [], "changed_checkpoint_ids": []}],
    )
    current = current_attempt_from(vault, item, attempt_id=attempt.attempt_id, completed_at=attempt.completed_at,
                                   learner_answer_md=attempt.learner_answer_md, blind_grade=record)
    assembled = assemble_diagnosis_context(vault, store, current, DiagnosisSettings(), mode=mode)
    return current, item, assembled


def _event(index=0, **overrides):
    event = {
        "event_index": index,
        "causal_class": "learner_state",
        "candidate_causes": [{"statement": "Believes V needs no transpose in the final factor.", "cause_scope": "learner_state", "prior_weight": 2}],
        "registry_match": {"kind": "abstain"},
        "history_changed_cause": {"changed": False, "note": ""},
    }
    event.update(overrides)
    return event


def _validate(vault, store, proposal, **kwargs):
    current, item, assembled = _assembled(vault, store, **kwargs)
    return validate_diagnosis_proposal(
        DiagnosisProposal.model_validate(proposal), assembled=assembled, current=current, vault=vault,
        item=item, rubric=resolved_rubric(vault, item), store=store,
    )


def _rules(result):
    return [issue["rule"] for issue in result.report["issues"]]


def test_closed_world_ids_are_counted_and_removed(world):
    vault, store = world
    result = _validate(vault, store, {
        "analysis_md": "a",
        "evidence_attempt_ids": ["att_02_svd_fail", "att_invented", "att_04_unrelated_fail"],
        "event_diagnoses": [_event(prior_hypothesis_id="hyp_invented", registry_match={"kind": "durable", "id": "mc_invented"})],
        "repair_suggestions": [{"practice_mode": "redo", "rationale": "r", "repaired_trace_id": "rt9", "learning_object_id": "lo_invented",
                                "target_evidence_families": ["facet_invented"]}],
        "prerequisite_gap_hypotheses": [{"prerequisite_ref": "lo_nowhere", "suggested_discriminator_md": "probe"}],
    })
    unknown = result.report["unknown_ids"]
    # att_04 is a real attempt but outside this context: invented history too.
    assert set(unknown["attempts"]) == {"att_invented", "att_04_unrelated_fail"}
    assert unknown["hypotheses"] == ["hyp_invented"]
    assert unknown["registry"] == ["mc_invented"]
    assert unknown["repaired_traces"] == ["rt9"]
    assert "lo_invented" in unknown["learning_objects"]
    assert "facet_invented" in unknown["facets"]
    assert result.unknown_id_count == 8
    assert result.proposal["evidence_attempt_ids"] == ["att_02_svd_fail"]
    assert result.proposal["event_diagnoses"][0]["prior_hypothesis_id"] is None
    assert result.proposal["prerequisite_gap_hypotheses"] == []


def test_unknown_event_index_is_rejected_and_empty_result_is_validation_rejected(world):
    vault, store = world
    result = _validate(vault, store, {"analysis_md": "a", "event_diagnoses": [_event(index=5)]})
    assert result.report["unknown_ids"]["event_indexes"] == ["5"]
    assert result.status == "validation_rejected"
    assert result.report["rejection_reason"] == "no_event_diagnosis_survived"
    assert _validate(vault, store, {"analysis_md": "  ", "event_diagnoses": [_event()]}).status == "validation_rejected"


def test_verbatim_quote_anchoring_drops_invented_quotes(world):
    vault, store = world
    result = _validate(vault, store, {
        "analysis_md": "a",
        "evidence_attempt_ids": ["att_02_svd_fail"],
        "event_diagnoses": [_event()],
        "pattern_claims": [
            {"hypothesis_ref": "cause:0:0", "relation": "same_mechanism", "cited": [
                {"attempt_id": "att_02_svd_fail", "quote": "A =  U Sigma V"},  # whitespace-normalized match
                {"attempt_id": "att_02_svd_fail", "quote": "a sentence the learner never wrote"},
            ]},
        ],
    })
    cited = result.proposal["pattern_claims"][0]["cited"]
    assert [citation["quote"] for citation in cited] == ["A =  U Sigma V"]
    assert "citation_quote_unanchored" in _rules(result)
    assert [citation.attempt_id for citation in result.validated_citations] == ["att_02_svd_fail"]


def test_citation_validity_requires_a_blind_non_pass_on_an_overlapping_target(world):
    vault, store = world
    result = _validate(vault, store, {
        "analysis_md": "a",
        "evidence_attempt_ids": ["att_02_svd_fail", "att_03_svd_pass", "att_05_eigen_fail"],
        "event_diagnoses": [_event()],
        "pattern_claims": [
            {"hypothesis_ref": "cause:0:0", "relation": "same_mechanism", "cited": [
                {"attempt_id": "att_02_svd_fail", "quote": "U Sigma V"},
                {"attempt_id": "att_03_svd_pass", "quote": "U Sigma V^T"},
                {"attempt_id": "att_05_eigen_fail", "quote": "P D P"},
            ]},
        ],
    })
    # The cited PASS is kept as a citation but never counts toward recurrence.
    assert {citation["attempt_id"] for citation in result.proposal["pattern_claims"][0]["cited"]} == {
        "att_02_svd_fail", "att_03_svd_pass", "att_05_eigen_fail"}
    reasons = {issue["attempt_id"]: issue["reason"] for issue in result.report["issues"] if issue["rule"] == "citation_not_valid_for_recurrence"}
    assert reasons == {"att_03_svd_pass": "cited_attempt_passed"}
    validated = {citation.attempt_id: citation.surface_group for citation in result.validated_citations}
    assert set(validated) == {"att_02_svd_fail", "att_05_eigen_fail"}
    # Independence is by surface group.
    assert result.report["validated_recurrence"] == [{"claim_index": 0, "independent_surface_groups": 2}]


def test_citation_without_target_overlap_or_valid_measurement_is_not_counted(world):
    vault, store = world
    # Re-key the hypothesis to a facet no cited attempt touches.
    result = _validate(vault, store, {
        "analysis_md": "a",
        "evidence_attempt_ids": ["att_02_svd_fail"],
        "event_diagnoses": [_event(candidate_causes=[{"statement": "s", "cause_scope": "learner_state",
                                                      "target_ref": {"kind": "facet_capability", "facet_id": "transpose", "capability": "retrieval"}}])],
        "pattern_claims": [{"hypothesis_ref": "cause:0:0", "relation": "same_mechanism",
                            "cited": [{"attempt_id": "att_02_svd_fail", "quote": "U Sigma V"}]}],
    })
    reasons = [issue.get("reason") for issue in result.report["issues"] if issue["rule"] == "citation_not_valid_for_recurrence"]
    assert reasons == []  # recall overlaps via the current blind attribution's targets
    assert result.validated_citations


def test_scope_firewall_rejects_a_causal_class_on_an_invalid_measurement(world):
    vault, store = world
    item_contract = {**VALID, "validity_scope": "item_contract"}
    result = _validate(vault, store, {"analysis_md": "a", "event_diagnoses": [_event(0), _event(1)]},
                       attributions=[VALID, item_contract])
    events = {event["event_index"]: event for event in result.proposal["event_diagnoses"]}
    assert events[0]["causal_class"] == "learner_state"
    assert events[1]["causal_class"] == "unknown"
    assert "scope_firewall" in _rules(result)


def test_passed_facet_firewall_strips_protected_diagnoser_targets(world):
    vault, store = world
    result = _validate(
        vault, store,
        {"analysis_md": "a",
         "event_diagnoses": [_event(candidate_causes=[{"statement": "s", "cause_scope": "learner_state",
                                                       "target_ref": {"kind": "facet_capability", "facet_id": "recall", "capability": "retrieval"}}])],
         "repair_suggestions": [{"practice_mode": "redo", "rationale": "r", "target_evidence_families": ["recall"],
                                 "target_criterion_ids": ["result"]}]},
        criteria={"setup": 2, "result": 2},
    )
    assert result.proposal["event_diagnoses"][0]["candidate_causes"][0]["target_ref"] == {"kind": "none"}
    assert result.proposal["repair_suggestions"][0]["target_evidence_families"] == []
    assert result.proposal["repair_suggestions"][0]["target_criterion_ids"] == []
    rules = _rules(result)
    assert "passed_facet_firewall" in rules and "passed_criterion_firewall" in rules


def test_registry_match_rules(world):
    vault, store = world
    result = _validate(vault, store, {"analysis_md": "a", "event_diagnoses": [
        _event(0, registry_match={"kind": "durable", "id": "mc_durable"}),
    ]})
    assert result.proposal["event_diagnoses"][0]["registry_match"]["id"] == "mc_durable"
    result = _validate(vault, store, {"analysis_md": "a", "event_diagnoses": [_event(0, registry_match={"kind": "new"})]})
    assert result.proposal["event_diagnoses"][0]["registry_match"]["kind"] == "abstain"
    assert "registry_new_without_statement" in _rules(result)
    result = _validate(vault, store, {"analysis_md": "a", "event_diagnoses": [_event(0, registry_match={"kind": "abstain"})]})
    assert result.report["issues"] == []


def test_repair_validation_runs_and_checks_the_trace_reference(world):
    vault, store = world
    result = _validate(vault, store, {"analysis_md": "a", "event_diagnoses": [_event()], "repair_suggestions": [
        {"practice_mode": "redo", "rationale": "r", "repaired_trace_id": "rt1", "operator": "insert_transpose"},
    ]})
    repair = result.proposal["repair_suggestions"][0]
    assert repair["repaired_trace_id"] == "rt1"
    assert "repair_validation" in repair


def test_anchoring_suspect_when_a_reused_hypothesis_lacks_local_support(world):
    vault, store = world
    unsupported = {"statement": "Has never memorized the spectral theorem.", "cause_scope": "learner_state", "prior_weight": 3}
    suspect = _validate(vault, store, {"analysis_md": "a", "event_diagnoses": [_event(candidate_causes=[unsupported], prior_hypothesis_id="hyp_prior")]})
    assert suspect.anchoring_suspect is True
    changed = _validate(vault, store, {"analysis_md": "a", "event_diagnoses": [_event(candidate_causes=[unsupported], prior_hypothesis_id="hyp_prior",
                                                                                       history_changed_cause={"changed": True, "note": "new cause"})]})
    assert changed.anchoring_suspect is False
    supported = _validate(vault, store, {"analysis_md": "a", "event_diagnoses": [_event(
        candidate_causes=[{"statement": "The final factor V is left not transposed.", "cause_scope": "learner_state"}], prior_hypothesis_id="hyp_prior")]})
    assert supported.anchoring_suspect is False
    assert local_support("final factor transposed", ["The final factor V is not transposed."]) == 1.0


def test_generation_order_differs_by_mode_and_normalizes():
    assert list(strict_output_schema(DiagnosisProposal)["properties"])[:2] == ["analysis_md", "evidence_attempt_ids"]
    assert list(strict_output_schema(RecitingDiagnosisProposal)["properties"])[:2] == ["evidence_attempt_ids", "analysis_md"]
    assert proposal_model_for("exact") is DiagnosisProposal
    for mode in ("full", "snapshot", "hybrid"):
        assert proposal_model_for(mode) is RecitingDiagnosisProposal
    reciting = RecitingDiagnosisProposal.model_validate({"evidence_attempt_ids": ["x"], "analysis_md": "a"})
    assert as_diagnosis_proposal(reciting) == DiagnosisProposal.model_validate({"analysis_md": "a", "evidence_attempt_ids": ["x"]})


def test_prompt_rules_by_mode(world):
    vault, store = world
    for mode in ("exact", "full"):
        _current, _item, assembled = _assembled(vault, store, mode=mode)
        prompt = diagnosis_prompt(assembled)
        assert "never replace evidence in this trace" in prompt
        assert ("RECITE FIRST" in prompt) is (mode != "exact")
        assert "READ-ONLY WORKSPACE" not in prompt
