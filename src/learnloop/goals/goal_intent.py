"""Resolve a Goal's learner-facing quest without conflating every title with intent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from learnloop.vault.models import Goal

QuestBasis = Literal[
    "explicit_intent",
    "exam_goal",
    "practice_goal",
    "legacy_title",
]


@dataclass(frozen=True)
class ResolvedGoalQuest:
    sentence: str
    basis: QuestBasis


def resolve_goal_quest(goal: Goal) -> ResolvedGoalQuest | None:
    """Return the sentence teach-back authoring may use for transfer.

    The learner's explicit larger intent is authoritative. When it is absent,
    learner/study-map goals still express a narrower operational quest through
    their exam configuration or selected practice scope. Automatic
    source-ingestion linkage is deliberately excluded: a chapter title is not
    evidence that the learner authored a quest.

    Legacy goals retain the historical title-as-quest behavior so existing
    vaults do not silently change meaning.
    """

    explicit = (goal.intent_sentence or "").strip()
    if explicit:
        return ResolvedGoalQuest(sentence=explicit, basis="explicit_intent")
    if goal.creation_source == "source_ingestion":
        return None

    title = goal.title.strip()
    if not title:
        return None
    if goal.exam.enabled:
        return ResolvedGoalQuest(
            sentence=f"Do well on the exam goal “{title}”.",
            basis="exam_goal",
        )
    if goal.creation_source in {"learner", "study_map"}:
        return ResolvedGoalQuest(
            sentence=f"Be good at problems covered by the goal “{title}”.",
            basis="practice_goal",
        )
    return ResolvedGoalQuest(sentence=title, basis="legacy_title")
