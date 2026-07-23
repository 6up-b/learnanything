"""spec_tutor_promotion.md §3 W3 — promote_tutor_question end-to-end."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.codex.schemas import AuthoringProposal, PromotionAnalysis
from learnloop.db.repositories import Repository
from learnloop.services.promotions import PromotionError, promote_tutor_question
from learnloop.vault.loader import add_note, load_vault

from tests.helpers import NOW, create_basic_vault


# --- fake clients ----------------------------------------------------------


class _AnalysisClient:
    """Provides Step-0 analysis only (no authoring provider available)."""

    provider_name = "codex"
    provider_type = "test"
    model = "test-model"

    def __init__(self, analysis: PromotionAnalysis):
        self._analysis = analysis
        self.analysis_contexts: list = []

    def run_promotion_analysis(self, context) -> PromotionAnalysis:
        self.analysis_contexts.append(context)
        return self._analysis


class _FullClient(_AnalysisClient):
    """Analysis + authoring provider."""

    def __init__(self, analysis: PromotionAnalysis, proposal: AuthoringProposal):
        super().__init__(analysis)
        self._proposal = proposal
        self.authoring_contexts: list = []

    def run_authoring_proposal(self, context) -> AuthoringProposal:
        self.authoring_contexts.append(context)
        return self._proposal


def _insert_event(repository: Repository, event_id: str, **overrides) -> str:
    payload = {
        "id": event_id,
        "context": "practice",
        "practice_item_id": "pi_svd_define_001",
        "question_md": "Why must U have orthonormal columns?",
        "answer_md": "What property of the factors would guarantee that? Consider U^T U.",
        "answer_status": "answered",
    }
    payload.update(overrides)
    return repository.insert_question_event(payload)


def _attach_proposal(*, item_id="pi_svd_promoted_001", tags=None, review_route="auto_apply"):
    """A valid attach-to-existing-LO practice item that can auto-apply with grounding."""

    payload = {
        "learning_object_id": "lo_svd_definition",
        "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"],
        "prompt": "State the property of U's columns that the definition guarantees.",
        "expected_answer": "The columns of U are orthonormal.",
        "evidence_facets": ["recall"],
        "evidence_weights": {"recall": 1.0},
        "criterion_facet_weights": {"correctness": {"recall": 1.0}},
        "retrieval_demand": 0.8,
        "transfer_distance": 0.2,
        "scaffold_level": 0.0,
        "surface_family": "svd-property",
        "repair_targets": ["recall"],
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "correctness", "points": 4, "description": "States orthonormality."}],
            "fatal_errors": [],
        },
    }
    if tags is not None:
        payload["tags"] = tags
    return AuthoringProposal.model_validate(
        {
            "summary": "Promote tutor probe to practice.",
            "source_refs": [{"ref_type": "note", "ref_id": "note_svd_source"}],
            "items": [
                {
                    "client_item_id": "pi_promoted",
                    "item_type": "practice_item",
                    "operation": "create",
                    "proposed_entity_id": item_id,
                    "source_ref_ids": ["note_svd_source"],
                    "rationale": 'Derived from the tutor probe "Consider U^T U."',
                    "review_route": review_route,
                    "audit": {
                        "audit_type": "deterministic_validator",
                        "status": "passed",
                        "summary": "Expected answer normalized.",
                        "validator_name": "short-answer-normalizer",
                        "validator_version": "1",
                    },
                    "payload": payload,
                }
            ],
        }
    )


def _new_lo_proposal():
    """A batch that mints a new LO + first practice item (always review per §3 Step 3)."""

    return AuthoringProposal.model_validate(
        {
            "summary": "Promote tutor probe to a new LO.",
            "source_refs": [{"ref_type": "note", "ref_id": "note_svd_source"}],
            "items": [
                {
                    "client_item_id": "lo_new",
                    "item_type": "learning_object",
                    "operation": "create",
                    "proposed_entity_id": "lo_svd_promoted",
                    "source_ref_ids": ["note_svd_source"],
                    "rationale": 'New LO for the tutor probe "Consider U^T U."',
                    "review_route": "auto_apply",
                    "payload": {
                        "title": "Orthonormality of SVD factors",
                        "subjects": ["linear-algebra"],
                        "concept_id": "singular_value_decomposition",
                        "knowledge_type": "concept",
                        "summary": "U and V have orthonormal columns.",
                    },
                },
                {
                    "client_item_id": "pi_new",
                    "item_type": "practice_item",
                    "operation": "create",
                    "proposed_entity_id": "pi_svd_promoted_new_001",
                    "source_ref_ids": ["note_svd_source"],
                    "rationale": "First item for the new LO.",
                    "review_route": "auto_apply",
                    "audit": {
                        "audit_type": "deterministic_validator",
                        "status": "passed",
                        "summary": "Expected answer normalized.",
                        "validator_name": "short-answer-normalizer",
                        "validator_version": "1",
                    },
                    "payload": {
                        "learning_object_id": "lo_svd_promoted",
                        "subjects": ["linear-algebra"],
                        "practice_mode": "short_answer",
                        "attempt_types_allowed": ["independent_attempt"],
                        "prompt": "Why are U's columns orthonormal?",
                        "expected_answer": "By construction of the SVD.",
                        "evidence_facets": ["recall"],
                        "evidence_weights": {"recall": 1.0},
                        "criterion_facet_weights": {"correctness": {"recall": 1.0}},
                        "retrieval_demand": 0.8,
                        "transfer_distance": 0.2,
                        "scaffold_level": 0.0,
                        "surface_family": "svd-property",
                        "repair_targets": ["recall"],
                        "grading_rubric": {
                            "max_points": 4,
                            "criteria": [{"id": "correctness", "points": 4, "description": "ok"}],
                            "fatal_errors": [],
                        },
                    },
                },
            ],
        }
    )


def _add_origin_source_note(root):
    add_note(
        root,
        "linear-algebra",
        "svd_source",
        "SVD source",
        "The SVD factors U and V have orthonormal columns.",
        related_los=["lo_svd_definition"],
        clock=FrozenClock(NOW),
    )


# --- tests -----------------------------------------------------------------


def test_idempotent_returns_existing_row(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root
    repository = Repository(root / "state.sqlite")
    _insert_event(repository, "ev1")
    repository.insert_question_promotion(
        question_event_id="ev1", intent="practice", route="review_required"
    )
    client = _AnalysisClient(PromotionAnalysis())

    result = promote_tutor_question(root, client, event_id="ev1", intent="practice")

    assert result["route"] == "review_required"
    # No analysis call happened: the idempotency guard returned early.
    assert client.analysis_contexts == []
    # No new proposal batch was created.
    assert repository.proposal_batches() == []


def test_library_gap_rejected(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root
    repository = Repository(root / "state.sqlite")
    _insert_event(
        repository, "ev_lib", context="library", practice_item_id=None, note_id="note_x"
    )
    client = _AnalysisClient(PromotionAnalysis())

    with pytest.raises(PromotionError):
        promote_tutor_question(root, client, event_id="ev_lib", intent="gap")


def test_dedup_short_circuit_practice(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root
    repository = Repository(root / "state.sqlite")
    _insert_event(repository, "ev_dedup")
    client = _AnalysisClient(
        PromotionAnalysis(attributed_facets=["recall"], covered_by_practice_item_id="pi_svd_define_001")
    )

    result = promote_tutor_question(root, client, event_id="ev_dedup", intent="practice")

    assert result["route"] == "existing_item"
    assert result["existing_practice_item_id"] == "pi_svd_define_001"
    assert result["proposed_patch_id"] is None
    assert result["learner_claim_id"] is None
    # No authoring, no grounding note.
    assert repository.proposal_batches() == []
    assert repository.question_event("ev_dedup")["saved_note_id"] is None
    # Decision features still land.
    features = repository.decision_features(decision_id="ev_dedup", decision_type="question_promotion")
    assert features is not None
    assert features["context"]["outcome"] == "existing_item"


def test_reader_promotion_uses_subject_facet_vocabulary_without_origin_item(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root
    repository = Repository(root / "state.sqlite")
    _insert_event(
        repository,
        "ev_reader",
        context="reader",
        practice_item_id=None,
        note_id="span:section-1",
    )
    client = _AnalysisClient(
        PromotionAnalysis(
            attributed_facets=["recall"],
            covered_by_practice_item_id="pi_svd_define_001",
        )
    )

    result = promote_tutor_question(
        root,
        client,
        event_id="ev_reader",
        intent="practice",
        subject_id="linear-algebra",
    )

    assert result["route"] == "existing_item"
    assert client.analysis_contexts[0].facet_vocabulary == ["recall"]
    assert client.analysis_contexts[0].existing_items[0]["id"] == "pi_svd_define_001"


def test_dedup_short_circuit_gap_writes_claim_no_need(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root
    repository = Repository(root / "state.sqlite")
    _insert_event(repository, "ev_dedup_gap")
    client = _AnalysisClient(
        PromotionAnalysis(attributed_facets=["recall"], covered_by_practice_item_id="pi_svd_define_001")
    )

    result = promote_tutor_question(root, client, event_id="ev_dedup_gap", intent="gap")

    assert result["route"] == "existing_item"
    assert result["existing_practice_item_id"] == "pi_svd_define_001"
    # G2 claim written; NO intervention need filed.
    assert result["learner_claim_id"] is not None
    assert result["intervention_need_id"] is None
    claims = repository.learner_claims()
    assert len(claims) == 1
    assert claims[0]["source"] == "tutor_gap_declaration"
    assert claims[0]["scope_id"] == "lo_svd_definition"
    assert not repository.pending_intervention_needs("lo_svd_definition")


def test_grounding_fallback_forces_review(tmp_path):
    # Origin LO has NO source notes of its own -> note-only grounding is
    # semantically empty, so the item is forced to review (§3 Step 1).
    root = create_basic_vault(tmp_path / "vault").root
    repository = Repository(root / "state.sqlite")
    _insert_event(repository, "ev_ground")
    client = _FullClient(PromotionAnalysis(attributed_facets=["recall"]), _attach_proposal())

    result = promote_tutor_question(root, client, event_id="ev_ground", intent="practice")

    assert result["route"] == "review_required"
    assert result["created_practice_item_id"] is None
    items = repository.proposal_items(result["proposed_patch_id"])
    assert all(item["decision"] == "pending" for item in items)


def test_new_lo_batch_forced_review(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root
    repository = Repository(root / "state.sqlite")
    _add_origin_source_note(root)  # grounding present, but a new LO forces review anyway
    _insert_event(repository, "ev_newlo")
    client = _FullClient(PromotionAnalysis(attributed_facets=["recall"]), _new_lo_proposal())

    result = promote_tutor_question(root, client, event_id="ev_newlo", intent="practice")

    assert result["route"] == "review_required"
    assert result["created_practice_item_id"] is None
    assert result["created_learning_object_id"] is None
    items = repository.proposal_items(result["proposed_patch_id"])
    assert len(items) == 2
    assert all(item["decision"] == "pending" for item in items)


def test_attach_to_existing_with_grounding_auto_applies(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root
    repository = Repository(root / "state.sqlite")
    _add_origin_source_note(root)
    _insert_event(repository, "ev_attach")
    client = _FullClient(PromotionAnalysis(attributed_facets=["recall"]), _attach_proposal())

    result = promote_tutor_question(root, client, event_id="ev_attach", intent="practice")

    assert result["route"] == "auto_apply"
    assert result["created_practice_item_id"] == "pi_svd_promoted_001"
    assert result["saved_note_id"]
    # The applied item carries the tutor_promoted tag.
    item = load_vault(root).practice_items["pi_svd_promoted_001"]
    assert "tutor_promoted" in item.tags
    # Rating is never written by promotion.
    assert repository.question_event("ev_attach")["rating"] is None
    # Decision features recorded, rating copied read-only (None here).
    features = repository.decision_features(decision_id="ev_attach", decision_type="question_promotion")
    assert features["context"]["intent"] == "practice"
    assert features["context"]["outcome"] == "attached_to_existing_lo_auto"
    assert features["context"]["rating"] is None


def test_gap_route_writes_claim_need_and_diagnostic_pending(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root
    repository = Repository(root / "state.sqlite")
    _insert_event(repository, "ev_gap")
    # No authoring provider -> inline diagnostic generation is tolerated (skipped).
    client = _AnalysisClient(
        PromotionAnalysis(attributed_facets=["recall"], question_nature="mechanism")
    )

    result = promote_tutor_question(root, client, event_id="ev_gap", intent="gap")

    assert result["route"] == "diagnostic_pending"
    assert result["learner_claim_id"] is not None
    assert result["intervention_need_id"] is not None
    claims = repository.learner_claims()
    assert len(claims) == 1
    assert claims[0]["source"] == "tutor_gap_declaration"
    need = repository.intervention_need(result["intervention_need_id"])
    assert need["trigger_reason"] == "tutor_gap_declaration"
    assert need["blocked_reason"] == "tutor_gap_declaration"
    assert need["learning_object_id"] == "lo_svd_definition"
    assert need["status"] == "pending"  # diagnostic gen unavailable -> need waits
    features = repository.decision_features(decision_id="ev_gap", decision_type="question_promotion")
    assert features["context"]["intent"] == "gap"
    assert features["item_demand_vector"]["question_nature"] == "mechanism"


def test_gap_route_transfer_nature_biases_intent(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root
    repository = Repository(root / "state.sqlite")
    _insert_event(repository, "ev_gap_transfer")
    client = _AnalysisClient(
        PromotionAnalysis(attributed_facets=["recall"], question_nature="edge_case")
    )

    result = promote_tutor_question(root, client, event_id="ev_gap_transfer", intent="gap")
    need = repository.intervention_need(result["intervention_need_id"])
    assert need["desired_intent"] == "transfer"


def test_gap_need_dedup_links_existing_need(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root
    repository = Repository(root / "state.sqlite")
    _insert_event(repository, "ev_gap_a")
    _insert_event(repository, "ev_gap_b")
    client = _AnalysisClient(PromotionAnalysis(attributed_facets=["recall"]))

    first = promote_tutor_question(root, client, event_id="ev_gap_a", intent="gap")
    second = promote_tutor_question(root, client, event_id="ev_gap_b", intent="gap")

    # Second promotion links to the first's still-pending need; no duplicate filed.
    assert second["intervention_need_id"] == first["intervention_need_id"]
    pending = repository.pending_intervention_needs("lo_svd_definition")
    assert len(pending) == 1


def test_gap_inline_diagnostic_generation_when_available(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root
    repository = Repository(root / "state.sqlite")
    _insert_event(repository, "ev_gap_diag")
    empty = AuthoringProposal.model_validate({"summary": "no items", "source_refs": [], "items": []})
    client = _FullClient(PromotionAnalysis(attributed_facets=["recall"]), empty)

    result = promote_tutor_question(root, client, event_id="ev_gap_diag", intent="gap")

    assert result["route"] == "diagnostic_pending"
    # Diagnostic generation ran and fulfilled the need.
    need = repository.intervention_need(result["intervention_need_id"])
    assert need["status"] == "fulfilled"
