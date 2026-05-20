from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.scheduler import build_due_queue
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_learning_object

from tests.helpers import NOW, create_basic_vault


def test_state_sync_initializes_and_deactivates_missing_yaml(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)

    result = sync_vault_state(load_vault(vault_root), repository, clock=clock)

    assert result.practice_item_states_created == 1
    assert result.mastery_states_created == 1
    assert repository.practice_item_state("pi_svd_define_001").active is True
    assert repository.mastery_state("lo_svd_definition").evidence_count == 0

    second = sync_vault_state(load_vault(vault_root), repository, clock=clock)

    assert second.as_dict() == {
        "practice_item_states_created": 0,
        "practice_item_states_updated": 0,
        "practice_item_states_deactivated": 0,
        "mastery_states_created": 0,
    }

    paths.practice_item_path("linear-algebra", "pi_svd_define_001").unlink()
    deactivated = sync_vault_state(load_vault(vault_root), repository, clock=clock)

    assert deactivated.practice_item_states_deactivated == 1
    assert repository.practice_item_state("pi_svd_define_001").active is False


def test_state_sync_enters_probe_for_new_active_goal_learning_object(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)

    sync_vault_state(load_vault(vault_root), repository, clock=clock)

    probe_state = repository.probe_state("lo_svd_definition")
    queue = build_due_queue(load_vault(vault_root), repository, clock=clock, persist_explanations=False)

    assert probe_state is not None
    assert probe_state.status == "in_progress"
    assert "pi_svd_define_001" in [item.practice_item_id for item in queue]


def test_state_sync_logs_probe_gap_when_active_goal_lo_has_no_items(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    paths.practice_item_path("linear-algebra", "pi_svd_define_001").unlink()
    upsert_learning_object(
        vault_root,
        {
            "id": "lo_svd_gap",
            "title": "SVD gap",
            "subjects": ["linear-algebra"],
            "concept": "singular_value_decomposition",
            "knowledge_type": "definition",
            "summary": "No Practice Item exists yet.",
        },
        clock=FrozenClock(NOW),
    )
    repository = Repository(paths.sqlite_path)

    sync_vault_state(load_vault(vault_root), repository, clock=FrozenClock(NOW))

    events = repository.elicitation_events()
    assert any(event["trigger"] == "probe_phase_local_pi_inadequate" for event in events)
