from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.codex.client import AuthoringContext
from learnloop.codex.schemas import AuthoringProposal
from learnloop.db.repositories import Repository
from learnloop.services.proposals import generate_authoring_proposal, persist_authoring_proposal

from tests.helpers import NOW, NOW_ISO, create_basic_vault


class _FakeAuthoringClient:
    def __init__(self, proposal: AuthoringProposal):
        self.proposal = proposal
        self.calls = 0

    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        self.calls += 1
        return self.proposal

    def run_grading_proposal(self, context):  # pragma: no cover - unused here
        raise NotImplementedError


def test_insert_and_complete_agent_run(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)

    run_id = repository.insert_agent_run({"purpose": "grading", "started_at": NOW_ISO})
    assert repository.complete_agent_run(run_id, status="completed", clock=FrozenClock(NOW))

    label, record = repository.find_record(run_id)
    assert label == "agent_run"
    assert record["status"] == "completed"
    assert record["completed_at"] is not None


def test_persist_authoring_proposal_records_agent_run(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(_proposal_payload())

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="import", clock=FrozenClock(NOW))

    paths_repo = Repository((vault_root / "state.sqlite"))
    batch = next(batch for batch in paths_repo.proposal_batches() if batch["id"] == patch_id)
    assert batch["agent_run_id"]
    label, run = paths_repo.find_record(batch["agent_run_id"])
    assert label == "agent_run"
    assert run["status"] == "completed"
    assert run["output_schema"] == "AuthoringProposal"


def test_generate_authoring_proposal_with_fake_client_has_lineage(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(_proposal_payload())
    client = _FakeAuthoringClient(proposal)

    patch_id = generate_authoring_proposal(vault_root, client, clock=FrozenClock(NOW))

    assert client.calls == 1
    repository = Repository(vault_root / "state.sqlite")
    batch = next(batch for batch in repository.proposal_batches() if batch["id"] == patch_id)
    assert batch["agent_run_id"]
    label, run = repository.find_record(batch["agent_run_id"])
    assert label == "agent_run"
    assert run["status"] == "completed"
    assert run["input_context_hash"]


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
