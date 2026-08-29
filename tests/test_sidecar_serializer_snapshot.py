"""Golden wire shapes for the highest-traffic sidecar DTO families."""

from __future__ import annotations

import json
from pathlib import Path

from learnloop.reader.reader_dialogue import reader_enabled, reader_prompt_contract
from learnloop.scheduling.scheduler import ScheduledItem
from learnloop.vault.loader import load_vault
from learnloop_sidecar.dto import versioned
from learnloop_sidecar.handlers.serializers import item_presentation, scheduled_item_dto

from tests.helpers import create_basic_vault

SNAPSHOT = Path(__file__).with_name("sidecar_serializer_snapshot.json")


class _EmptyStateRepository:
    def practice_item_state(self, _practice_item_id):
        return None

    def mastery_state(self, _learning_object_id):
        return None


def test_queue_practice_and_reader_wire_snapshots(tmp_path):
    root = tmp_path / "vault"
    create_basic_vault(root)
    vault = load_vault(root)
    scheduled = ScheduledItem(
        practice_item_id="pi_svd_define_001",
        learning_object_id="lo_svd_definition",
        priority=1.25,
        components={"forgetting_risk": 0.75, "selection_reward": 1.25},
        readiness_factor=0.8,
        selected_mode="short_answer",
        plain_english=["Due for review."],
    )
    reader = reader_prompt_contract()
    reader["reader_enabled"] = reader_enabled(vault)
    actual = {
        "queue": scheduled_item_dto(
            vault,
            _EmptyStateRepository(),
            scheduled,
        ),
        "practice": item_presentation(
            vault.practice_items["pi_svd_define_001"]
        ),
        "reader": versioned(reader),
    }

    assert actual == json.loads(SNAPSHOT.read_text(encoding="utf-8"))
