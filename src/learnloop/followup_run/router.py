"""The router's decision for one workflow (spec §5). Before any item exists."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository

ASK_NOW = "insert_now"
WAIT = "continue_current"
NO_INTERVENTION = "no_intervention"
DECLINE = "decline"


@dataclass(frozen=True)
class FollowupDecision:
    chosen_ref: str
    reason: str
    decided_by: str
    propensity: float = 1.0
    decision_id: str | None = None
    pi: dict[str, float] = field(default_factory=dict)
    floor: float | None = None

    @property
    def refused(self) -> bool:
        return self.chosen_ref == DECLINE

    @property
    def no_intervention(self) -> bool:
        return self.chosen_ref == NO_INTERVENTION

    @property
    def wait(self) -> bool:
        return self.chosen_ref == WAIT

    def for_author(self) -> dict[str, Any]:
        return {"chosen": self.chosen_ref, "timing": "next block" if self.wait else "now"}


def decide(vault: Any, repository: Repository, row: Any, *, choice: Any, clients: Any, clock: Clock | None) -> FollowupDecision:
    return FollowupDecision(ASK_NOW, "no_plan", "no_plan")


def record_decision(repository: Repository, row: Any, decision: FollowupDecision, *, clock: Clock | None) -> None:
    return None


def record_outcome(repository: Repository, row: Any, decision: FollowupDecision, *, outcome: str, clock: Clock | None) -> None:
    return None


def bind_item(repository: Repository, row: Any, decision: FollowupDecision, admitted: Any, *, clock: Clock | None) -> None:
    return None
