from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.codex.client import AuthoringContext, CodexTurnTimeout
from learnloop.codex.schemas import AuthoringProposal
from learnloop.db.repositories import Repository
from learnloop.services.patches import PatchApplicationError
from learnloop.services.proposals import (
    accept_items,
    edit_proposal_item,
    generate_authoring_proposal,
    persist_authoring_proposal,
)
from learnloop.vault.loader import add_note, load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, create_basic_vault


class _FakeAuthoringClient:
    def __init__(self, proposal: AuthoringProposal):
        self.proposal = proposal

    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        return self.proposal

    def run_grading_proposal(self, context):  # pragma: no cover
        raise NotImplementedError


def test_generate_persists_one_item_per_proposal_item(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(_two_item_payload())
    patch_id = generate_authoring_proposal(vault_root, _FakeAuthoringClient(proposal), clock=FrozenClock(NOW))

    repository = Repository(vault_root / "state.sqlite")
    items = repository.proposal_items(patch_id)
    assert len(items) == 2
    assert {item["item_type"] for item in items} == {"learning_object", "practice_item"}
    assert all(item["decision"] == "pending" for item in items)


def test_ai_proposal_acceptance_records_ai_origin(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(_two_item_payload())
    patch_id = persist_authoring_proposal(
        vault_root,
        proposal,
        provider="deepseek_flash",
        model="deepseek-v4-flash",
        clock=FrozenClock(NOW),
    )

    accept_items(vault_root, patch_id)

    repository = Repository(vault_root / "state.sqlite")
    events = repository.content_events_for_entity("learning_object", "lo_svd_imported")
    assert events[0]["origin"] == "ai"
    with repository.connection() as connection:
        batch = connection.execute(
            "SELECT origin FROM change_batches WHERE id = ?",
            (events[0]["change_batch_id"],),
        ).fetchone()
    assert batch["origin"] == "ai"


def test_reject_route_item_is_persisted_invalid_and_not_applied(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(_reject_payload())
    patch_id = persist_authoring_proposal(vault_root, proposal, provider="import", clock=FrozenClock(NOW))

    repository = Repository(vault_root / "state.sqlite")
    items = repository.proposal_items(patch_id)
    assert len(items) == 1
    assert items[0]["validation_status"] == "invalid"
    assert items[0]["decision"] == "pending"

    with pytest.raises(PatchApplicationError):
        accept_items(vault_root, patch_id)


def test_canonical_source_refs_flow_into_learning_object_provenance(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    add_note(
        vault_root,
        "linear-algebra",
        "canonical_svd",
        "Canonical SVD",
        "SVD is a matrix factorization.",
        source_type="canonical_source",
        clock=FrozenClock(NOW),
    )
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "Canonical extraction",
            "source_refs": [{"ref_type": "canonical_source", "ref_id": "note_canonical_svd"}],
            "items": [
                {
                    "client_item_id": "lo_canonical",
                    "item_type": "learning_object",
                    "operation": "create",
                    "proposed_entity_id": "lo_svd_canonical",
                    "source_ref_ids": ["note_canonical_svd"],
                    "rationale": "Extract the canonical definition.",
                    "review_route": "review_required",
                    "payload": {
                        "title": "Canonical SVD definition",
                        "subjects": ["linear-algebra"],
                        "concept_id": "singular_value_decomposition",
                        "knowledge_type": "definition",
                        "summary": "SVD is a matrix factorization.",
                    },
                }
            ],
        }
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    accept_items(vault_root, patch_id)

    learning_object = load_vault(vault_root).learning_objects["lo_svd_canonical"]
    assert learning_object.provenance.origin == "canonical_extract"
    assert learning_object.provenance.source_refs[0].ref_type == "canonical_source"
    assert learning_object.provenance.source_refs[0].ref_id == "note_canonical_svd"


def test_source_grounded_auto_apply_accepts_low_risk_create(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    add_note(
        vault_root,
        "linear-algebra",
        "svd_extract",
        "SVD extract",
        "SVD supports low-rank approximation.",
        clock=FrozenClock(NOW),
    )
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "Auto apply source extraction",
            "source_refs": [{"ref_type": "note", "ref_id": "note_svd_extract"}],
            "items": [
                {
                    "client_item_id": "lo_auto",
                    "item_type": "learning_object",
                    "operation": "create",
                    "proposed_entity_id": "lo_svd_auto",
                    "source_ref_ids": ["note_svd_extract"],
                    "rationale": "Direct extraction from note.",
                    "review_route": "auto_apply",
                    "payload": {
                        "title": "SVD low-rank use",
                        "subjects": ["linear-algebra"],
                        "concept_id": "singular_value_decomposition",
                        "knowledge_type": "application",
                        "summary": "SVD supports low-rank approximation.",
                    },
                }
            ],
        }
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    repository = Repository(vault_root / "state.sqlite")
    item = repository.proposal_items(patch_id)[0]

    assert item["decision"] == "accepted"
    assert item["applied_change_batch_id"]
    assert "lo_svd_auto" in load_vault(vault_root).learning_objects


def test_source_linked_generated_practice_with_passed_audit_auto_applies(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    add_note(
        vault_root,
        "linear-algebra",
        "svd_extract",
        "SVD extract",
        "SVD supports low-rank approximation.",
        clock=FrozenClock(NOW),
    )
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "Generated source-linked practice",
            "source_refs": [{"ref_type": "note", "ref_id": "note_svd_extract"}],
            "items": [
                {
                    "client_item_id": "pi_generated",
                    "item_type": "practice_item",
                    "operation": "create",
                    "proposed_entity_id": "pi_svd_generated_001",
                    "source_ref_ids": ["note_svd_extract"],
                    "rationale": "Generated because no direct source exercise was available.",
                    "review_route": "auto_apply",
                    "audit": {
                        "audit_type": "deterministic_validator",
                        "status": "passed",
                        "summary": "Expected answer normalized successfully.",
                        "validator_name": "short-answer-normalizer",
                        "validator_version": "1",
                    },
                    "payload": {
                        "learning_object_id": "lo_svd_definition",
                        "subjects": None,
                        "practice_mode": "short_answer",
                        "attempt_types_allowed": ["independent_attempt"],
                        "prompt": "Name one use of SVD.",
                        "expected_answer": "Low-rank approximation.",
                        "evidence_facets": ["application"],
                        "evidence_weights": {"application": 1.0},
                        "criterion_facet_weights": {"correctness": {"application": 1.0}},
                        "retrieval_demand": 0.8,
                        "transfer_distance": 0.2,
                        "scaffold_level": 0.0,
                        "surface_family": "svd-application",
                        "repair_targets": ["application"],
                        "tags": ["generated"],
                        "grading_rubric": {
                            "max_points": 4,
                            "criteria": [{"id": "correctness", "points": 4, "description": "Names a use."}],
                            "fatal_errors": [],
                        },
                    },
                }
            ],
        }
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    repository = Repository(vault_root / "state.sqlite")
    item = repository.proposal_items(patch_id)[0]

    assert item["decision"] == "accepted"
    assert item["audit"]["status"] == "passed"
    assert "pi_svd_generated_001" in load_vault(vault_root).practice_items


def test_auto_apply_batches_dependency_order_for_new_lo_and_practice_item(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    add_note(
        vault_root,
        "linear-algebra",
        "svd_extract",
        "SVD extract",
        "SVD supports low-rank approximation.",
        clock=FrozenClock(NOW),
    )
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "Auto apply dependent LO and practice",
            "source_refs": [{"ref_type": "note", "ref_id": "note_svd_extract"}],
            "items": [
                {
                    "client_item_id": "a_pi_generated",
                    "item_type": "practice_item",
                    "operation": "create",
                    "proposed_entity_id": "pi_svd_new_lo_001",
                    "source_ref_ids": ["note_svd_extract"],
                    "rationale": "Generated because no direct source exercise was available.",
                    "review_route": "auto_apply",
                    "audit": {
                        "audit_type": "deterministic_validator",
                        "status": "passed",
                        "summary": "Expected answer normalized successfully.",
                    },
                    "payload": {
                        "learning_object_id": "lo_svd_new_auto",
                        "subjects": None,
                        "practice_mode": "constructed_response",
                        "attempt_types_allowed": ["open_text"],
                        "prompt": "Explain why SVD supports low-rank approximation.",
                        "expected_answer": "Truncating the singular values gives the best lower-rank approximation.",
                        "evidence_facets": ["application"],
                        "evidence_weights": {"application": 1.0},
                        "criterion_facet_weights": {"correctness": {"application": 1.0}},
                        "retrieval_demand": 0.8,
                        "transfer_distance": 0.2,
                        "scaffold_level": 0.0,
                        "surface_family": "svd-application",
                        "repair_targets": ["application"],
                        "tags": ["generated"],
                        "grading_rubric": {
                            "max_points": 4,
                            "criteria": [{"id": "correctness", "points": 4, "description": "Explains truncation."}],
                            "fatal_errors": [],
                        },
                    },
                },
                {
                    "client_item_id": "z_lo",
                    "item_type": "learning_object",
                    "operation": "create",
                    "proposed_entity_id": "lo_svd_new_auto",
                    "source_ref_ids": ["note_svd_extract"],
                    "rationale": "Direct extraction from note.",
                    "review_route": "auto_apply",
                    "payload": {
                        "title": "SVD low-rank approximation",
                        "subjects": ["linear-algebra"],
                        "concept_id": "singular_value_decomposition",
                        "knowledge_type": "application",
                        "summary": "SVD supports low-rank approximation.",
                    },
                },
            ],
        }
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    repository = Repository(vault_root / "state.sqlite")
    items = repository.proposal_items(patch_id)
    loaded = load_vault(vault_root)

    assert {item["decision"] for item in items} == {"accepted"}
    assert "lo_svd_new_auto" in loaded.learning_objects
    assert "pi_svd_new_lo_001" in loaded.practice_items
    assert loaded.practice_items["pi_svd_new_lo_001"].attempt_types_allowed == ["open_text"]


def test_source_linked_generated_practice_missing_audit_is_invalid(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    add_note(
        vault_root,
        "linear-algebra",
        "svd_extract",
        "SVD extract",
        "SVD supports low-rank approximation.",
        clock=FrozenClock(NOW),
    )
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "Generated source-linked practice without audit",
            "source_refs": [{"ref_type": "note", "ref_id": "note_svd_extract"}],
            "items": [
                {
                    "client_item_id": "pi_generated",
                    "item_type": "practice_item",
                    "operation": "create",
                    "proposed_entity_id": "pi_svd_generated_001",
                    "source_ref_ids": ["note_svd_extract"],
                    "rationale": "Generated because no direct source exercise was available.",
                    "review_route": "auto_apply",
                    "payload": {
                        "learning_object_id": "lo_svd_definition",
                        "subjects": None,
                        "practice_mode": "short_answer",
                        "attempt_types_allowed": ["independent_attempt"],
                        "prompt": "Name one use of SVD.",
                        "expected_answer": "Low-rank approximation.",
                        "evidence_facets": ["application"],
                        "evidence_weights": {"application": 1.0},
                        "criterion_facet_weights": {"correctness": {"application": 1.0}},
                        "retrieval_demand": 0.8,
                        "transfer_distance": 0.2,
                        "scaffold_level": 0.0,
                        "surface_family": "svd-application",
                        "repair_targets": ["application"],
                        "tags": ["generated"],
                        "grading_rubric": {
                            "max_points": 4,
                            "criteria": [{"id": "correctness", "points": 4, "description": "Names a use."}],
                            "fatal_errors": [],
                        },
                    },
                }
            ],
        }
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    repository = Repository(vault_root / "state.sqlite")
    item = repository.proposal_items(patch_id)[0]

    assert item["decision"] == "pending"
    assert item["validation_status"] == "invalid"
    assert item["validation_errors"] == ["missing_generated_audit"]
    with pytest.raises(PatchApplicationError):
        accept_items(vault_root, patch_id)


def test_generated_practice_missing_evidence_facets_is_invalid(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(
        _generated_practice_proposal_payload(
            {
                "evidence_weights": {"application": 1.0},
                "criterion_facet_weights": {"correctness": {"application": 1.0}},
            }
        )
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    item = Repository(vault_root / "state.sqlite").proposal_items(patch_id)[0]

    assert item["decision"] == "pending"
    assert item["validation_status"] == "invalid"
    assert "missing_evidence_facets" in item["validation_errors"]


def test_registry_backed_vault_rejects_unknown_evidence_facet(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(
        paths.facets_path,
        {
            "schema_version": 1,
            "facets": [{"id": "recall", "title": "Recall"}],
        },
    )
    proposal = AuthoringProposal.model_validate(
        _generated_practice_proposal_payload(
            {
                "evidence_facets": ["invented_application_facet"],
                "evidence_weights": {"invented_application_facet": 1.0},
                "criterion_facet_weights": {
                    "correctness": {"invented_application_facet": 1.0}
                },
                "repair_targets": ["invented_application_facet"],
            }
        )
    )

    patch_id = persist_authoring_proposal(
        paths.root, proposal, provider="codex", clock=FrozenClock(NOW)
    )
    item = Repository(paths.sqlite_path).proposal_items(patch_id)[0]

    assert item["validation_status"] == "invalid"
    assert "unknown_evidence_facet:invented_application_facet" in item["validation_errors"]


def test_generated_practice_missing_reward_metadata_is_invalid(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(
        _generated_practice_proposal_payload(
            {
                "evidence_facets": ["application"],
                "evidence_weights": {"application": 1.0},
                "criterion_facet_weights": {"correctness": {"application": 1.0}},
                "retrieval_demand": None,
                "transfer_distance": None,
                "scaffold_level": None,
                "surface_family": None,
                "repair_targets": [],
            }
        )
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    item = Repository(vault_root / "state.sqlite").proposal_items(patch_id)[0]

    assert item["validation_status"] == "invalid"
    assert item["validation_errors"] == [
        "missing_retrieval_demand",
        "missing_transfer_distance",
        "missing_scaffold_level",
        "missing_surface_family",
        "missing_repair_targets",
    ]


def test_generated_practice_rubric_points_cannot_exceed_grading_scale(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(
        _generated_practice_proposal_payload(
            {
                "evidence_facets": ["application"],
                "evidence_weights": {"application": 1.0},
                "criterion_facet_weights": {
                    "setup": {"application": 0.5},
                    "answer": {"application": 0.5},
                },
                "grading_rubric": {
                    "max_points": 4,
                    "criteria": [
                        {"id": "setup", "points": 3, "description": "Sets up the method."},
                        {"id": "answer", "points": 3, "description": "Gives the final answer."},
                    ],
                    "fatal_errors": [],
                },
            }
        )
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    item = Repository(vault_root / "state.sqlite").proposal_items(patch_id)[0]

    assert item["validation_status"] == "invalid"
    assert item["validation_errors"] == ["invalid_grading_rubric:criteria_points_exceed_max_points"]


def test_generated_practice_rejects_unknown_metadata_keys(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(
        _generated_practice_proposal_payload(
            {
                "evidence_facets": ["application"],
                "evidence_weights": {"application": 1.0, "unknown": 0.5},
                "criterion_facet_weights": {
                    "correctness": {"application": 1.0, "unknown": 0.25},
                    "unknown_criterion": {"application": 1.0},
                },
                "repair_targets": ["application", "unknown_repair"],
            }
        )
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    item = Repository(vault_root / "state.sqlite").proposal_items(patch_id)[0]

    assert item["validation_status"] == "invalid"
    assert item["validation_errors"] == [
        "unknown_evidence_weight_facet:unknown",
        "unknown_repair_target:unknown_repair",
        "unknown_criterion_facet_facet:unknown",
        "unknown_criterion_facet_criterion:unknown_criterion",
    ]


def test_manual_practice_missing_evidence_weights_is_warning(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "Manual practice metadata review",
            "source_refs": [{"ref_type": "manual_context", "ref_id": "manual_svd"}],
            "items": [
                {
                    "client_item_id": "pi_manual",
                    "item_type": "practice_item",
                    "operation": "create",
                    "proposed_entity_id": "pi_svd_manual_metadata",
                    "source_ref_ids": ["manual_svd"],
                    "rationale": "Hand-authored practice item.",
                    "review_route": "review_required",
                    "payload": {
                        "learning_object_id": "lo_svd_definition",
                        "subjects": None,
                        "practice_mode": "short_answer",
                        "attempt_types_allowed": ["independent_attempt"],
                        "prompt": "Name one use of SVD.",
                        "expected_answer": "Low-rank approximation.",
                        "evidence_facets": ["application"],
                        "grading_rubric": {
                            "max_points": 4,
                            "criteria": [{"id": "correctness", "points": 4, "description": "Names a use."}],
                            "fatal_errors": [],
                        },
                    },
                }
            ],
        }
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="import", clock=FrozenClock(NOW))
    item = Repository(vault_root / "state.sqlite").proposal_items(patch_id)[0]

    assert item["decision"] == "pending"
    assert item["validation_status"] == "warning"
    assert item["validation_errors"] == ["metadata_review:missing_evidence_weights"]


def test_generated_practice_single_facet_backfills_criterion_facet_weights(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(
        _generated_practice_proposal_payload(
            {
                "evidence_facets": ["application"],
                "evidence_weights": {"application": 1.0},
            }
        )
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    item = Repository(vault_root / "state.sqlite").proposal_items(patch_id)[0]

    assert item["decision"] == "pending"
    # A single evidence facet fully determines the criterion->facet map, so it is
    # backfilled and the review no longer carries the missing_criterion_facet_weights warning.
    assert item["validation_status"] == "valid"
    assert item["payload"]["criterion_facet_weights"] == {"correctness": {"application": 1.0}}
    assert "pi_svd_generated_metadata" not in load_vault(vault_root).practice_items


def test_generated_practice_missing_evidence_weights_is_backfilled_uniform(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(
        _generated_practice_proposal_payload({"evidence_facets": ["application", "recall"]})
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    item = Repository(vault_root / "state.sqlite").proposal_items(patch_id)[0]

    # evidence_weights is uniformly normalized over the facets...
    assert item["payload"]["evidence_weights"] == {"application": 0.5, "recall": 0.5}
    # ...but with >1 facet the criterion->facet assignment is not derivable, so that
    # warning still surfaces for human review.
    assert item["validation_status"] == "warning"
    assert item["validation_errors"] == ["metadata_review:missing_criterion_facet_weights"]


def test_unresolved_source_ref_is_persisted_invalid(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "Bad source",
            "source_refs": [{"ref_type": "canonical_source", "ref_id": "missing_source"}],
            "items": [
                {
                    "client_item_id": "lo_bad_source",
                    "item_type": "learning_object",
                    "operation": "create",
                    "proposed_entity_id": "lo_bad_source",
                    "source_ref_ids": ["missing_source"],
                    "rationale": "Unresolved source should not apply.",
                    "review_route": "review_required",
                    "payload": {
                        "title": "Bad source LO",
                        "subjects": ["linear-algebra"],
                        "concept_id": "singular_value_decomposition",
                        "knowledge_type": "definition",
                        "summary": "Unverified.",
                    },
                }
            ],
        }
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    repository = Repository(vault_root / "state.sqlite")
    item = repository.proposal_items(patch_id)[0]

    assert item["validation_status"] == "invalid"
    assert item["validation_errors"] == ["unresolved_source_ref:missing_source"]
    with pytest.raises(PatchApplicationError):
        accept_items(vault_root, patch_id)


def test_create_payload_missing_required_fields_is_invalid(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "Incomplete create",
            "source_refs": [{"ref_type": "manual_context", "ref_id": "manual_svd"}],
            "items": [
                {
                    "client_item_id": "lo_incomplete",
                    "item_type": "learning_object",
                    "operation": "create",
                    "proposed_entity_id": "lo_incomplete",
                    "source_ref_ids": ["manual_svd"],
                    "rationale": "Missing fields should block acceptance.",
                    "review_route": "review_required",
                    "payload": {
                        "title": "Incomplete LO",
                        "subjects": ["linear-algebra"],
                        "concept_id": "singular_value_decomposition",
                    },
                }
            ],
        }
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    item = Repository(vault_root / "state.sqlite").proposal_items(patch_id)[0]

    assert item["validation_status"] == "invalid"
    assert item["validation_errors"] == ["missing_required:knowledge_type", "missing_required:summary"]
    with pytest.raises(PatchApplicationError):
        accept_items(vault_root, patch_id)


def test_practice_item_without_resolved_rubric_is_invalid_until_edited(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "Missing rubric",
            "source_refs": [{"ref_type": "manual_context", "ref_id": "manual_svd"}],
            "items": [
                {
                    "client_item_id": "pi_missing_rubric",
                    "item_type": "practice_item",
                    "operation": "create",
                    "proposed_entity_id": "pi_svd_missing_rubric",
                    "source_ref_ids": ["manual_svd"],
                    "rationale": "No rubric should block acceptance.",
                    "review_route": "review_required",
                    "payload": {
                        "learning_object_id": "lo_svd_definition",
                        "subjects": None,
                        "practice_mode": "short_answer",
                        "attempt_types_allowed": ["independent_attempt"],
                        "prompt": "Define SVD.",
                        "expected_answer": "A matrix factorization.",
                        "evidence_facets": ["recall"],
                        "evidence_weights": {"recall": 1.0},
                    },
                }
            ],
        }
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    repository = Repository(vault_root / "state.sqlite")
    item = repository.proposal_items(patch_id)[0]

    assert item["validation_status"] == "invalid"
    assert item["validation_errors"] == ["missing_rubric:short_answer"]
    with pytest.raises(PatchApplicationError):
        accept_items(vault_root, patch_id)

    edited = edit_proposal_item(
        vault_root,
        patch_id,
        item["id"],
        {
            **item["payload"],
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [],
            },
        },
        clock=FrozenClock(NOW),
    )

    assert edited["validation_status"] == "valid"
    assert edited["validation_errors"] == []


def test_invalid_concept_edge_proposal_is_persisted_invalid(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "Bad edge",
            "source_refs": [{"ref_type": "manual_context", "ref_id": "manual_svd"}],
            "items": [
                {
                    "client_item_id": "edge_bad",
                    "item_type": "concept_edge",
                    "operation": "create",
                    "source_ref_ids": ["manual_svd"],
                    "rationale": "Endpoint is missing.",
                    "review_route": "review_required",
                    "payload": {
                        "source_concept_id": "missing_concept",
                        "target_concept_id": "singular_value_decomposition",
                        "relation_type": "related",
                    },
                }
            ],
        }
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    item = Repository(vault_root / "state.sqlite").proposal_items(patch_id)[0]

    assert item["validation_status"] == "invalid"
    assert item["validation_errors"] == ["invalid_concept_edge:missing_source:missing_concept"]
    with pytest.raises(PatchApplicationError):
        accept_items(vault_root, patch_id)


def test_update_learning_object_proposal_preserves_existing_required_fields(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "Update LO title",
            "source_refs": [{"ref_type": "existing_entity", "ref_id": "lo_svd_definition"}],
            "items": [
                {
                    "client_item_id": "lo_update",
                    "item_type": "learning_object",
                    "operation": "update",
                    "target": {"entity_type": "learning_object", "entity_id": "lo_svd_definition"},
                    "source_ref_ids": ["lo_svd_definition"],
                    "rationale": "Clarify the title.",
                    "review_route": "review_required",
                    "payload": {"title": "SVD definition clarified"},
                }
            ],
        }
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    accept_items(vault_root, patch_id)

    updated = load_vault(vault_root).learning_objects["lo_svd_definition"]
    assert updated.title == "SVD definition clarified"
    assert updated.concept == "singular_value_decomposition"
    assert updated.subjects == ["linear-algebra"]


def test_update_practice_item_proposal_preserves_existing_learning_object(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "Update PI prompt",
            "source_refs": [{"ref_type": "existing_entity", "ref_id": "pi_svd_define_001"}],
            "items": [
                {
                    "client_item_id": "pi_update",
                    "item_type": "practice_item",
                    "operation": "update",
                    "target": {"entity_type": "practice_item", "entity_id": "pi_svd_define_001"},
                    "source_ref_ids": ["pi_svd_define_001"],
                    "rationale": "Clarify the prompt.",
                    "review_route": "review_required",
                    "payload": {"prompt": "State the compact SVD definition."},
                }
            ],
        }
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    accept_items(vault_root, patch_id)

    updated = load_vault(vault_root).practice_items["pi_svd_define_001"]
    assert updated.prompt == "State the compact SVD definition."
    assert updated.learning_object_id == "lo_svd_definition"


def test_edit_proposal_item_updates_payload_and_refreshes_duplicate_validation(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "Duplicate then edit",
            "source_refs": [{"ref_type": "manual_context", "ref_id": "manual_svd"}],
            "items": [
                {
                    "client_item_id": "lo_edit",
                    "item_type": "learning_object",
                    "operation": "create",
                    "proposed_entity_id": "lo_svd_definition",
                    "source_ref_ids": ["manual_svd"],
                    "rationale": "Needs learner edit.",
                    "review_route": "review_required",
                    "payload": {
                        "title": "Edited SVD use",
                        "subjects": ["linear-algebra"],
                        "concept_id": "singular_value_decomposition",
                        "knowledge_type": "application",
                        "summary": "SVD supports compression.",
                    },
                }
            ],
        }
    )
    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    repository = Repository(vault_root / "state.sqlite")
    item = repository.proposal_items(patch_id)[0]
    assert item["validation_status"] == "invalid"
    assert item["validation_errors"] == ["duplicate_id:lo_svd_definition"]

    edited_payload = {
        **item["payload"],
        "id": "lo_svd_compression",
        "title": "SVD compression",
    }
    edited = edit_proposal_item(vault_root, patch_id, item["id"], edited_payload, clock=FrozenClock(NOW))

    assert edited["validation_status"] == "valid"
    assert edited["validation_errors"] == []
    assert edited["edited_payload"]["id"] == "lo_svd_compression"
    accept_items(vault_root, patch_id, [item["id"]])
    loaded = load_vault(vault_root)
    assert "lo_svd_compression" in loaded.learning_objects
    assert loaded.learning_objects["lo_svd_compression"].title == "SVD compression"


def test_accept_learning_object_create_adds_missing_concept_for_graph(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "New concept through LO",
            "source_refs": [{"ref_type": "manual_context", "ref_id": "manual_svd"}],
            "items": [
                {
                    "client_item_id": "lo_new_concept",
                    "item_type": "learning_object",
                    "operation": "create",
                    "proposed_entity_id": "lo_svd_conditioning",
                    "source_ref_ids": ["manual_svd"],
                    "rationale": "Add a missing concept with the LO.",
                    "review_route": "review_required",
                    "payload": {
                        "title": "Analyze conditioning with singular values",
                        "subjects": ["linear-algebra"],
                        "concept_id": "concept_svd_conditioning",
                        "knowledge_type": "procedure",
                        "summary": "Use the spread of singular values to reason about conditioning.",
                        "tags": ["svd", "conditioning"],
                    },
                },
                {
                    "client_item_id": "edge_existing_to_new",
                    "item_type": "concept_edge",
                    "operation": "create",
                    "source_ref_ids": ["manual_svd"],
                    "rationale": "Conditioning builds on SVD.",
                    "review_route": "review_required",
                    "payload": {
                        "source_concept_id": "singular_value_decomposition",
                        "target_concept_id": "concept_svd_conditioning",
                        "relation_type": "prerequisite",
                    },
                },
            ],
        }
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    repository = Repository(vault_root / "state.sqlite")
    items = repository.proposal_items(patch_id)
    assert [item["validation_status"] for item in items] == ["valid", "valid"]

    accept_items(vault_root, patch_id)

    loaded = load_vault(vault_root)
    assert "concept_svd_conditioning" in loaded.concepts
    assert loaded.concepts["concept_svd_conditioning"].title == "Analyze conditioning with singular values"
    assert loaded.concepts["concept_svd_conditioning"].type == "procedure"
    assert loaded.learning_objects["lo_svd_conditioning"].concept == "concept_svd_conditioning"
    assert any(edge.target == "concept_svd_conditioning" for edge in loaded.edges)


def _two_item_payload() -> dict:
    return {
        "summary": "Two-item proposal",
        "source_refs": [{"ref_type": "manual_context", "ref_id": "manual_svd"}],
        "items": [
            {
                "client_item_id": "lo_1",
                "item_type": "learning_object",
                "operation": "create",
                "proposed_entity_id": "lo_svd_imported",
                "source_ref_ids": ["manual_svd"],
                "rationale": "Add LO.",
                "review_route": "review_required",
                "payload": {
                    "title": "Imported SVD use",
                    "subjects": ["linear-algebra"],
                    "concept_id": "singular_value_decomposition",
                    "knowledge_type": "application",
                    "summary": "SVD compresses matrices.",
                },
            },
            {
                "client_item_id": "pi_1",
                "item_type": "practice_item",
                "operation": "create",
                "proposed_entity_id": "pi_svd_imported_001",
                "source_ref_ids": ["manual_svd"],
                "rationale": "Practice it.",
                "review_route": "review_required",
                "payload": {
                    "learning_object_id": "lo_svd_imported",
                    "subjects": None,
                    "practice_mode": "short_answer",
                    "attempt_types_allowed": ["independent_attempt"],
                    "prompt": "Use of SVD?",
                    "expected_answer": "Low-rank approximation.",
                    "evidence_facets": ["application"],
                    "evidence_weights": {"application": 1.0},
                    "grading_rubric": {
                        "max_points": 4,
                        "criteria": [{"id": "correctness", "points": 4, "description": "Names a use."}],
                        "fatal_errors": [],
                    },
                },
            },
        ],
    }


def _generated_practice_proposal_payload(payload_overrides: dict) -> dict:
    payload = {
        "learning_object_id": "lo_svd_definition",
        "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"],
        "prompt": "Name one use of SVD.",
        "expected_answer": "Low-rank approximation.",
        "retrieval_demand": 0.8,
        "transfer_distance": 0.2,
        "scaffold_level": 0.0,
        "surface_family": "svd-application",
        "repair_targets": ["application"],
        "tags": ["generated"],
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "correctness", "points": 4, "description": "Names a use."}],
            "fatal_errors": [],
        },
    }
    payload.update(payload_overrides)
    return {
        "summary": "Generated source-linked practice metadata",
        "source_refs": [{"ref_type": "manual_context", "ref_id": "manual_svd"}],
        "items": [
            {
                "client_item_id": "pi_generated_metadata",
                "item_type": "practice_item",
                "operation": "create",
                "proposed_entity_id": "pi_svd_generated_metadata",
                "source_ref_ids": ["manual_svd"],
                "rationale": "Generated because no direct source exercise was available.",
                "review_route": "auto_apply",
                "audit": {
                    "audit_type": "deterministic_validator",
                    "status": "passed",
                    "summary": "Expected answer normalized successfully.",
                    "validator_name": "short-answer-normalizer",
                    "validator_version": "1",
                },
                "payload": payload,
            }
        ],
    }


def _reject_payload() -> dict:
    return {
        "summary": "Rejected proposal",
        "source_refs": [{"ref_type": "manual_context", "ref_id": "manual_svd"}],
        "items": [
            {
                "client_item_id": "lo_bad",
                "item_type": "learning_object",
                "operation": "create",
                "proposed_entity_id": "lo_rejected",
                "source_ref_ids": ["manual_svd"],
                "rationale": "Low quality.",
                "review_route": "reject",
                "payload": {
                    "title": "Rejected LO",
                    "subjects": ["linear-algebra"],
                    "concept_id": "singular_value_decomposition",
                    "summary": "x",
                },
            }
        ],
    }


class _QueueAuthoringClient:
    def __init__(self, proposals: list[AuthoringProposal]):
        self.proposals = list(proposals)
        self.contexts: list[AuthoringContext] = []

    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        self.contexts.append(context)
        return self.proposals.pop(0)

    def run_grading_proposal(self, context):  # pragma: no cover
        raise NotImplementedError


def test_invalid_generated_item_gets_one_repair_round_trip(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    broken_payload = _generated_practice_proposal_payload(
        {"evidence_facets": ["application"], "evidence_weights": {"application": 1.0}}
    )
    broken_payload["items"][0]["audit"] = {
        "audit_type": "deterministic_validator",
        "status": "not_applicable_with_trace",
        "summary": "Conceptual item; no numeric validation.",
    }
    repaired_payload = _generated_practice_proposal_payload(
        {"evidence_facets": ["application"], "evidence_weights": {"application": 1.0}}
    )
    repaired_payload["items"][0]["audit"] = {
        "audit_type": "deterministic_validator",
        "status": "not_applicable_with_trace",
        "summary": "Conceptual item; no numeric validation.",
        "trace": "Checked the expected answer against the SVD definition by hand.",
    }
    client = _QueueAuthoringClient(
        [
            AuthoringProposal.model_validate(broken_payload),
            AuthoringProposal.model_validate(repaired_payload),
        ]
    )

    patch_id = generate_authoring_proposal(vault_root, client, clock=FrozenClock(NOW))

    assert len(client.contexts) == 2
    repair_instructions = client.contexts[1].instructions or ""
    assert "REPAIR PASS" in repair_instructions
    assert "missing_generated_audit_trace" in repair_instructions
    repository = Repository(vault_root / "state.sqlite")
    items = repository.proposal_items(patch_id)
    assert len(items) == 1
    assert items[0]["validation_status"] != "invalid"
    assert items[0]["audit"]["trace"].startswith("Checked the expected answer")


def test_valid_proposal_skips_repair_round_trip(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    client = _QueueAuthoringClient([AuthoringProposal.model_validate(_two_item_payload())])

    generate_authoring_proposal(vault_root, client, clock=FrozenClock(NOW))

    assert len(client.contexts) == 1


def test_failed_repair_call_keeps_original_invalid_item(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    broken_payload = _generated_practice_proposal_payload(
        {"evidence_facets": ["application"], "evidence_weights": {"application": 1.0}}
    )
    broken_payload["items"][0]["audit"] = {
        "audit_type": "deterministic_validator",
        "status": "not_applicable_with_trace",
        "summary": "Conceptual item; no numeric validation.",
    }
    client = _QueueAuthoringClient([AuthoringProposal.model_validate(broken_payload)])

    patch_id = generate_authoring_proposal(vault_root, client, clock=FrozenClock(NOW))

    repository = Repository(vault_root / "state.sqlite")
    items = repository.proposal_items(patch_id)
    assert len(items) == 1
    assert items[0]["validation_status"] == "invalid"
    assert items[0]["validation_errors"] == ["missing_generated_audit_trace"]


def test_timed_out_repair_fails_without_persisting_first_pass(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    broken_payload = _generated_practice_proposal_payload(
        {"evidence_facets": ["application"], "evidence_weights": {"application": 1.0}}
    )
    broken_payload["items"][0]["audit"] = {
        "audit_type": "deterministic_validator",
        "status": "not_applicable_with_trace",
        "summary": "Conceptual item; no numeric validation.",
    }

    class TimeoutOnRepairClient:
        def __init__(self):
            self.calls = 0

        def run_authoring_proposal(self, _context):
            self.calls += 1
            if self.calls == 1:
                return AuthoringProposal.model_validate(broken_payload)
            raise CodexTurnTimeout("repair deadline expired")

    client = TimeoutOnRepairClient()

    with pytest.raises(CodexTurnTimeout, match="repair deadline expired"):
        generate_authoring_proposal(vault_root, client, clock=FrozenClock(NOW))

    assert client.calls == 2
    assert Repository(vault_root / "state.sqlite").proposal_batches() == []
