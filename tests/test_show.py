from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.observations import record_observation, register_observation_template
from learnloop.services.probes import enter_probe
from learnloop.services.proposals import accept_items, persist_authoring_proposal
from learnloop.codex.schemas import AuthoringProposal
from learnloop.vault.loader import add_note, load_vault
from learnloop.vault.writer import upsert_concept_edge

from tests.helpers import NOW, NOW_ISO, create_basic_vault, seed_due_item

runner = CliRunner()


def _show_type(vault_root, identifier) -> str:
    result = runner.invoke(app, ["show", identifier, "--json", "--vault", str(vault_root)])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)["type"]


def test_show_inspects_every_deterministic_id(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = seed_due_item(paths)

    # A concept edge and a note to inspect.
    upsert_concept_edge(
        vault_root,
        {
            "id": "edge_show",
            "relation_type": "related",
            "source": "singular_value_decomposition",
            "target": "singular_value_decomposition",
            "strength": 1.0,
        },
        clock=FrozenClock(NOW),
    )
    add_note(vault_root, "linear-algebra", "note_show", "Note", "Body.", clock=FrozenClock(NOW))

    loaded = load_vault(vault_root)
    result = complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="x"),
        SelfGradeInput(criterion_points={"correctness": 2}, confidence=4, error_type="conceptual_slip"),
        clock=FrozenClock(NOW),
    )

    proposal = AuthoringProposal.model_validate(_proposal_payload())
    patch_id = persist_authoring_proposal(vault_root, proposal, provider="import", clock=FrozenClock(NOW))
    item_id = repository.proposal_items(patch_id)[0]["id"]
    apply_result = accept_items(vault_root, patch_id, [item_id])
    change_batch_id = apply_result.change_batch_ids[0]
    evidence_id = repository.fetch_grading_evidence(result.attempt_id)[0].id
    learner_claim_id = repository.insert_learner_claim(
        {
            "id": "claim_show",
            "claim_type": "self_rating",
            "scope_type": "learning_object",
            "scope_id": "lo_svd_definition",
            "evidence_family": "recall",
            "claimed_level": 0.9,
            "prior_pseudo_count": 4.0,
            "source": "manual_cli",
        },
        clock=FrozenClock(NOW),
    )
    intervention_need_id = repository.upsert_intervention_need(
        {
            "id": "need_show",
            "attempt_id": result.attempt_id,
            "practice_item_id": "pi_svd_define_001",
            "learning_object_id": "lo_svd_definition",
            "desired_intent": "diagnostic_probe",
            "trigger_reason": "show_test",
            "target_facets": ["recall"],
            "error_types": ["conceptual_slip"],
            "priority": 0.75,
            "status": "pending",
            "blocked_reason": "queued_for_diagnostic",
            "candidate_requirements": {},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )
    hypothesis_set = enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    observation_template_id = register_observation_template(
        repository,
        domain="linear-algebra",
        version="1",
        title="Reflection",
        template_yaml="schema_version: 1\nfields:\n  - id: reflection\n    type: text\n",
        clock=FrozenClock(NOW),
    )
    observation = record_observation(
        loaded,
        repository,
        template_id=observation_template_id,
        response={"reflection": "ok"},
        related_learning_object_id="lo_svd_definition",
        clock=FrozenClock(NOW),
    )

    assert _show_type(vault_root, "lo_svd_definition") == "learning_object"
    assert _show_type(vault_root, "pi_svd_define_001") == "practice_item"
    assert _show_type(vault_root, "singular_value_decomposition") == "concept"
    assert _show_type(vault_root, "conceptual_slip") == "error_type"
    assert _show_type(vault_root, "edge_show") == "concept_edge"
    assert _show_type(vault_root, "note_show") == "note"
    assert _show_type(vault_root, "note_show:t=1.0-2.0") == "note"
    assert _show_type(vault_root, "linear-algebra") == "subject"
    assert _show_type(vault_root, result.attempt_id) == "practice_attempt"
    assert _show_type(vault_root, result.error_event_ids[0]) == "error_event"
    assert _show_type(vault_root, patch_id) == "proposal"
    assert _show_type(vault_root, item_id) == "proposal_item"
    assert _show_type(vault_root, change_batch_id) == "change_batch"
    assert _show_type(vault_root, evidence_id) == "grading_evidence"
    assert _show_type(vault_root, learner_claim_id) == "learner_claim"
    assert _show_type(vault_root, intervention_need_id) == "intervention_need"
    assert _show_type(vault_root, hypothesis_set.id) == "hypothesis_set"
    assert _show_type(vault_root, observation_template_id) == "observation_template"
    assert _show_type(vault_root, observation.observation_event_id) == "observation_event"


def test_show_attempt_includes_grading_and_surprise(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = seed_due_item(paths)
    loaded = load_vault(vault_root)
    result = complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="x"),
        SelfGradeInput(criterion_points={"correctness": 3}, confidence=4),
        clock=FrozenClock(NOW),
    )

    record = repository.find_record(result.attempt_id)
    assert record is not None
    label, payload = record
    assert label == "practice_attempt"


def test_show_missing_id_returns_not_found(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    result = runner.invoke(app, ["show", "does_not_exist", "--json", "--vault", str(vault_root)])
    assert result.exit_code == 1
    assert json.loads(result.output)["error"] == "not_found"


def _proposal_payload() -> dict:
    return {
        "summary": "Imported SVD proposal",
        "source_refs": [{"ref_type": "manual_context", "ref_id": "manual_svd"}],
        "items": [
            {
                "client_item_id": "lo_1",
                "item_type": "learning_object",
                "operation": "create",
                "proposed_entity_id": "lo_svd_imported",
                "source_ref_ids": ["manual_svd"],
                "rationale": "Add an application LO.",
                "review_route": "review_required",
                "payload": {
                    "title": "Imported SVD use",
                    "subjects": ["linear-algebra"],
                    "concept_id": "singular_value_decomposition",
                    "knowledge_type": "application",
                    "summary": "SVD compresses matrices via low-rank approximation.",
                },
            }
        ],
    }
