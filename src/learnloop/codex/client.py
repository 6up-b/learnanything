from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from learnloop.codex.schemas import AuthoringProposal, GradingProposal


@dataclass(frozen=True)
class AuthoringContext:
    vault_root: str
    source_ids: list[str]
    instructions: str | None = None
    subjects: list[str] = field(default_factory=list)
    source_refs: list[dict] = field(default_factory=list)
    concepts: list[dict] = field(default_factory=list)
    notes: list[dict] = field(default_factory=list)
    learning_objects: list[dict] = field(default_factory=list)
    practice_items: list[dict] = field(default_factory=list)
    goals: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class GradingContext:
    attempt_id: str
    practice_item_id: str
    prompt: str
    expected_answer: str
    learner_answer_md: str
    rubric: dict


class CodexClient(Protocol):
    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        ...

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        ...


class CodexUnavailable(RuntimeError):
    pass
