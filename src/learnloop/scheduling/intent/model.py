"""The intent vocabulary (``spec_daily_loop_v1.md`` §5.2) and its snapshots.

One choice per control press. Four choices are depth presets of an active
``help_me_remember`` commitment, "Check once" is a ``test_me_later``
commitment pending its check, and three are dispositions. No new action, no
table: the commitments API already holds the vocabulary (§3.7).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

#: The control's choices, in the order it shows them.
CHOICES: tuple[str, ...] = (
    "master",
    "learn",
    "keep",
    "light_touch",
    "check_once",
    "reference",
    "pause",
    "let_go",
)

#: The four depth choices and their presets (§5.2's table).
CHOICE_PRESET: dict[str, str] = {
    "master": "master_tasks_like_these",
    "learn": "work_fluently",
    "keep": "remember_key_ideas",
    "light_touch": "keep_in_touch",
}
PRESET_CHOICE: dict[str, str] = {preset: choice for choice, preset in CHOICE_PRESET.items()}

#: The three disposition choices.
CHOICE_DISPOSITION: dict[str, str] = {
    "reference": "reference_only",
    "pause": "paused",
    "let_go": "stopped",
}

#: Plain labels (honest, no jargon).
CHOICE_LABEL: dict[str, str] = {
    "master": "Master",
    "learn": "Learn",
    "keep": "Keep",
    "light_touch": "Light touch",
    "check_once": "Check once",
    "reference": "Reference",
    "pause": "Pause",
    "let_go": "Let go",
    "uncommitted": "No setting",
}

#: Dispositions under which an item is not served and is not a request (§5.3 step 2).
EXCLUDING_DISPOSITIONS: frozenset[str] = frozenset({"paused", "reference_only", "stopped", "satisfied"})

#: The provenance marker of the control's own commitments (§5.1).
INTENT_CONTROL_VIA = "intent_control"

#: A deadline link appends a commitment version with this change reason; it is
#: not a choice, so it never moves the commitment's choice time (§5.4).
DEADLINE_CHANGE_REASON = "intent_deadline"

#: Scope kinds the control acts on (§5.2): a subject or a source fans out to
#: one commitment whose targets are its active LOs (§5.1).
SCOPE_KINDS: frozenset[str] = frozenset({"learning_object", "practice_item", "subject", "source"})

#: Intent tiers for re-entry and admission order (§6.3, §7).
TIER_PUSH = 0  # Master, Learn, and goals with deadlines
TIER_KEEP = 1
TIER_UNCOMMITTED = 2
TIER_LIGHT = 3


def choice_for(action: str, depth_preset: str, disposition: str) -> str:
    """The control's word for a commitment's current state."""

    if disposition in CHOICE_DISPOSITION.values():
        return next(choice for choice, value in CHOICE_DISPOSITION.items() if value == disposition)
    if action == "test_me_later" or disposition in ("one_check_pending", "satisfied"):
        return "check_once"
    return PRESET_CHOICE.get(depth_preset, "keep")


@dataclass(frozen=True)
class ChoiceStamp:
    """When a commitment was last chosen: ``created_at`` then the row's ULID
    (insertion order within a second). Satisfaction and deadline links never
    move it (§5.3 step 2, §5.4)."""

    at: str
    row_id: str


@dataclass(frozen=True)
class CommitmentSnapshot:
    """One commitment as resolution reads it (head targets, folded events)."""

    id: str
    action: str
    created_at: str
    depth_preset: str
    disposition: str
    retired: bool
    choice: ChoiceStamp
    item_targets: frozenset[str] = frozenset()
    learning_object_targets: frozenset[str] = frozenset()
    via: str | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)
    goal_id: str | None = None
    due_hint: str | None = None
    #: The ``disposition_changed`` event that satisfied the check, if any.
    satisfied_at: str | None = None

    @property
    def intent_control(self) -> bool:
        return self.via == INTENT_CONTROL_VIA

    @property
    def scope(self) -> Mapping[str, Any] | None:
        scope = self.provenance.get("scope") if isinstance(self.provenance, Mapping) else None
        return scope if isinstance(scope, Mapping) else None

    @property
    def covers_items(self) -> bool:
        return bool(self.item_targets or self.learning_object_targets)


__all__ = [
    "CHOICES",
    "CHOICE_DISPOSITION",
    "CHOICE_LABEL",
    "CHOICE_PRESET",
    "ChoiceStamp",
    "CommitmentSnapshot",
    "DEADLINE_CHANGE_REASON",
    "EXCLUDING_DISPOSITIONS",
    "INTENT_CONTROL_VIA",
    "PRESET_CHOICE",
    "SCOPE_KINDS",
    "TIER_KEEP",
    "TIER_LIGHT",
    "TIER_PUSH",
    "TIER_UNCOMMITTED",
    "choice_for",
]
