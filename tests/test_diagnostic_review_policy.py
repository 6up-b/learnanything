"""§5.3 diagnostic review policy (spec_misconception_diagnostics.md)."""

from __future__ import annotations

from learnloop.content.proposals.ai_contracts import AuthoringProposalItem
from learnloop.content.proposals.proposals import (
    DiagnosticTarget,
    diagnostic_review_errors,
    diagnostic_review_warnings,
    evaluate_review_policy,
)
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault


def _target(**overrides) -> DiagnosticTarget:
    data = dict(
        need_id="need_1",
        misconception_ids=["mc_reverse_q"],
        misconception_statements={"mc_reverse_q": "reverses Q / Q^T"},
        source_practice_item_id="pi_svd_define_001",
        source_surface_family="definition",
        demonstrated_facets=["recall"],
        implicated_facets=["recall"],
    )
    data.update(overrides)
    return DiagnosticTarget(**data)


def _diag_item(**payload_overrides) -> AuthoringProposalItem:
    payload = {
        "learning_object_id": "lo_svd_definition",
        "practice_mode": "short_answer",
        "prompt": "Compute Q^T x and state which of Qx / Q^T x is the coordinate vector.",
        "expected_answer": "Qx is the coordinate vector",
        "misconception_consistent_answer": "Q^T x is the coordinate vector",
        "surface_family": "computation",
        "evidence_facets": ["recall"],
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "c1", "points": 4, "description": "correct"}],
            "fatal_errors": [{"id": "fe_reversed", "description": "reverses Q/Q^T", "misconception_id": "mc_reverse_q", "max_grade": 1}],
        },
    }
    payload.update(payload_overrides)
    return AuthoringProposalItem.model_validate(
        {
            "client_item_id": "c_diag",
            "item_type": "practice_item",
            "operation": "create",
            "proposed_entity_id": "pi_diag_gen",
            "rationale": "Diagnostic applying the belief to a concrete instance.",
            "review_route": "review_required",
            "payload": payload,
        }
    )


def test_valid_diagnostic_reviews(tmp_path):
    loaded = load_vault(create_basic_vault(tmp_path / "vault").root)
    assert evaluate_review_policy(_diag_item(), loaded, context=_target()) == "review_required"
    assert diagnostic_review_errors(_diag_item(), _target()) == []


def test_hard_error_no_keyed_fatal(tmp_path):
    loaded = load_vault(create_basic_vault(tmp_path / "vault").root)
    item = _diag_item(
        grading_rubric={
            "max_points": 4,
            "criteria": [{"id": "c1", "points": 4, "description": "correct"}],
            "fatal_errors": [{"id": "fe_plain", "description": "plain", "max_grade": 1}],
        }
    )
    assert "diagnostic_missing_keyed_fatal_error" in diagnostic_review_errors(item, _target())
    assert evaluate_review_policy(item, loaded, context=_target()) == "reject"


def test_hard_error_missing_consistent_answer(tmp_path):
    item = _diag_item(misconception_consistent_answer=None)
    errors = diagnostic_review_errors(item, _target())
    assert "diagnostic_missing_misconception_consistent_answer" in errors


def test_hard_error_surface_family_matches_source(tmp_path):
    item = _diag_item(surface_family="definition")  # equals source_surface_family
    errors = diagnostic_review_errors(item, _target())
    assert "diagnostic_surface_family_matches_source" in errors


def test_soft_warnings_footprint(tmp_path):
    item = _diag_item(evidence_facets=["recall", "application"])
    target = _target(implicated_facets=["application"], demonstrated_facets=["recall"])
    warnings = diagnostic_review_warnings(item, target)
    assert "diagnostic_footprint_exceeds_implicated_facets" in warnings
    assert "diagnostic_footprint_hits_demonstrated_facet:recall" in warnings


def test_context_none_unchanged(tmp_path):
    loaded = load_vault(create_basic_vault(tmp_path / "vault").root)
    # Without context, a diagnostic-shaped create falls through the ordinary policy
    # (no source refs -> review_required), exactly as before this phase.
    assert evaluate_review_policy(_diag_item(), loaded) == "review_required"


def test_missing_context_is_hard_error(tmp_path):
    assert diagnostic_review_errors(_diag_item(), None) == ["missing_diagnostic_target_context"]
