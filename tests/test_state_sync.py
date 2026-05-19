from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

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
