from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.scheduling.scheduler import ScheduledItem
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop_sidecar.handlers.serializers import scheduled_item_dtos

from tests.helpers import create_basic_vault


def test_queue_serialization_bulk_loads_state_once(tmp_path, monkeypatch):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository)
    item = next(iter(vault.practice_items.values()))
    scheduled = ScheduledItem(
        practice_item_id=item.id,
        learning_object_id=item.learning_object_id,
        priority=1.0,
        components={},
        readiness_factor=1.0,
        selected_mode=item.practice_mode,
        plain_english=[],
    )

    calls = {"items": 0, "mastery": 0}
    original_items = repository.practice_item_states
    original_mastery = repository.mastery_states

    def item_states_once():
        calls["items"] += 1
        return original_items()

    def mastery_states_once():
        calls["mastery"] += 1
        return original_mastery()

    monkeypatch.setattr(repository, "practice_item_states", item_states_once)
    monkeypatch.setattr(repository, "mastery_states", mastery_states_once)
    monkeypatch.setattr(
        repository,
        "practice_item_state",
        lambda *_args: (_ for _ in ()).throw(
            AssertionError("queue serialization must not load item state per row")
        ),
    )
    monkeypatch.setattr(
        repository,
        "mastery_state",
        lambda *_args: (_ for _ in ()).throw(
            AssertionError("queue serialization must not load mastery per row")
        ),
    )

    rows = scheduled_item_dtos(vault, repository, [scheduled] * 12)

    assert len(rows) == 12
    assert calls == {"items": 1, "mastery": 1}
