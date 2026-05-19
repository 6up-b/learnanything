from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository

from tests.helpers import NOW, NOW_ISO, create_basic_vault


def test_session_checkpoint_round_trip(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)

    session_id = repository.create_session(energy="medium", available_minutes=25, clock=clock)
    repository.update_session_checkpoint(
        session_id,
        current_practice_item_id="pi_svd_define_001",
        current_answer="draft answer",
        focus_block_state={"step": "practice"},
        readiness={"energy": "medium"},
        clock=clock,
    )

    checkpoint = repository.fetch_session_checkpoint(session_id)

    assert checkpoint["current_practice_item_id"] == "pi_svd_define_001"
    assert checkpoint["focus_block_state"] == {"step": "practice"}
    assert checkpoint["readiness"] == {"energy": "medium"}
    assert repository.clear_session_checkpoint(session_id) is True
    assert repository.fetch_session_checkpoint(session_id) is None


def test_agent_run_and_proposal_status_derivation(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)

    run_id = repository.insert_agent_run(
        {
            "id": "agent_run_1",
            "purpose": "authoring",
            "provider": "fake",
            "output_schema": "AuthoringProposal",
            "started_at": NOW_ISO,
        }
    )
    assert run_id == "agent_run_1"
    assert repository.complete_agent_run(run_id, clock=clock) is True

    patch_id = repository.persist_proposal_batch(
        {
            "id": "patch_1",
            "agent_run_id": run_id,
            "purpose": "authoring",
            "source_refs": [{"ref_id": "note_1"}],
            "summary": "Create one item",
            "created_at": NOW_ISO,
        },
        [
            {
                "id": "proposal_item_1",
                "client_item_id": "client_1",
                "item_type": "practice_item",
                "operation": "create",
                "target_entity_type": "practice_item",
                "payload": {"id": "pi_new"},
                "created_at": NOW_ISO,
            }
        ],
    )

    assert patch_id == "patch_1"
    assert repository.proposal_batches()[0]["source_refs"] == [{"ref_id": "note_1"}]
    assert repository.proposal_items(patch_id)[0]["payload"] == {"id": "pi_new"}
    assert repository.set_proposal_item_decision(patch_id, "accepted", clock=clock) == 1
    assert repository.proposal_batches()[0]["status_cache"] == "accepted"
