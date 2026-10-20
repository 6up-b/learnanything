"""Builders for daily-loop DL2 (intent) tests: a vault, choices, queue reads.

A daily-plan vault with two extra LOs whose items were reviewed ten days ago
and are due now, so the real scheduler serves them; choices go through the
real control (``learnloop.intent.control.apply_choice``) at a given instant.
No model is ever called.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.intent.control import Scope, apply_choice
from learnloop.scheduling.intent.serving import intent_serving

from learnloop.scheduling.scheduler import build_due_queue
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.daily_plan_fakes import iso, record_attempt, seed_due
from tests.helpers import create_daily_plan_vault

NOW = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)

#: lo_a: two items; lo_b: one item; lo_c: two items (a second LO for subject tests).
LEARNING_OBJECTS = {
    "lo_a": [("pi_a1", 2.0), ("pi_a2", 2.0)],
    "lo_b": [("pi_b1", 2.0)],
    "lo_c": [("pi_c1", 2.0), ("pi_c2", 2.0)],
}
OURS = {item_id for items in LEARNING_OBJECTS.values() for item_id, _ in items}
ITEM_LO = {item_id: lo for lo, items in LEARNING_OBJECTS.items() for item_id, _ in items}


@dataclass
class IntentVault:
    root: Path
    vault: Any
    repository: Repository

    def reload(self) -> None:
        self.vault = load_vault(self.root)

    def choose(self, kind: str, scope_id: str, choice: str, at: datetime) -> Any:
        return apply_choice(self.vault, self.repository, Scope(kind, scope_id), choice, clock=FrozenClock(at))

    def queue(self, at: datetime, **kwargs: Any) -> list[str]:
        return [
            entry.practice_item_id
            for entry in build_due_queue(self.vault, self.repository, clock=FrozenClock(at), persist_explanations=False, **kwargs)
            if entry.practice_item_id in OURS
        ]

    def serving(self, at: datetime) -> Any:
        return intent_serving(self.vault, self.repository, now=at)

    def requested(self, at: datetime) -> list[str]:
        serving = self.serving(at)
        if serving is None:
            return self.repository.requested_practice_item_ids()
        return serving.filter_requests(
            self.repository.requested_practice_item_ids(
                skip_commitment_ids=serving.intent_control_request_commitments()
            )
        )

    def answer(self, item_id: str, at: datetime) -> str:
        return record_attempt(self.repository, item_id, ITEM_LO[item_id], at)


def make_intent_vault(root: Path, *, plan_toml: str | None = None, reviewed_days_ago: int = 10) -> IntentVault:
    paths = create_daily_plan_vault(root, learning_objects=LEARNING_OBJECTS, plan_toml=plan_toml)
    vault = load_vault(paths.root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    reviewed = NOW - timedelta(days=reviewed_days_ago)
    for item_id, lo_id in sorted(ITEM_LO.items()):
        record_attempt(repository, item_id, lo_id, reviewed)
        seed_due(repository, item_id, due=NOW - timedelta(days=1), last=reviewed)
    for lo_id in LEARNING_OBJECTS:
        # Practised LOs carry evidence (else the cold-start gate withholds them).
        repository.upsert_mastery_state(
            MasteryState(
                learning_object_id=lo_id, logit_mean=0.0, logit_variance=1.0, evidence_count=1,
                last_evidence_at=iso(reviewed), algorithm_version=vault.config.algorithms.algorithm_version,
                updated_at=iso(reviewed),
            )
        )
    return IntentVault(root=paths.root, vault=vault, repository=repository)


__all__ = ["IntentVault", "ITEM_LO", "LEARNING_OBJECTS", "NOW", "OURS", "iso", "make_intent_vault"]
