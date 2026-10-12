"""``find_practice`` as an agent tool: a JSON-schema declaration and a dispatcher.

Any tool-calling agent (the tutor, the daily loop's "practice this" box, the
Decider router, or a coding agent through ``learnloop practice-index find
--json``) can declare ``FIND_PRACTICE_TOOL`` and route calls to
``run_find_practice_tool``. The tool proposes; it never serves.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from learnloop.db.repositories import Repository
from learnloop.practice_index.retrieval import PracticeConstraints, find_practice
from learnloop.vault.models import LoadedVault


class FindPracticeArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=2000,
                       description="What the learner wants to practise, in natural language.")
    limit: int | None = Field(default=None, ge=1, le=20, description="At most this many proposals.")
    learning_object_ids: list[str] = Field(default_factory=list,
                                           description="Only items of these learning objects.")
    subjects: list[str] = Field(default_factory=list, description="Only items in these subjects.")
    facet_ids: list[str] = Field(default_factory=list, description="Only items testing these facets.")
    practice_modes: list[str] = Field(default_factory=list, description="Only these practice modes.")
    exclude_item_ids: list[str] = Field(default_factory=list, description="Never propose these items.")
    min_difficulty: float | None = Field(default=None, ge=0, le=1)
    max_difficulty: float | None = Field(default=None, ge=0, le=1)


FIND_PRACTICE_TOOL: dict[str, Any] = {
    "name": "find_practice",
    "description": (
        "Find practice questions in the learner's vault for a natural-language request "
        "(for example 'give me practice on eigenvectors of rotations'). Returns ranked "
        "proposals with a one-line rationale each. Proposals pass the scheduler's "
        "eligibility rules; the tool never serves, grades or records practice."
    ),
    "input_schema": FindPracticeArguments.model_json_schema(),
}


def run_find_practice_tool(vault: LoadedVault, repository: Repository,
                           arguments: Mapping[str, Any], **kwargs: Any) -> dict[str, Any]:
    parsed = FindPracticeArguments.model_validate(dict(arguments))
    constraints = PracticeConstraints.from_mapping(parsed.model_dump(exclude={"query"}))
    return find_practice(vault, repository, parsed.query, constraints, origin="tool", **kwargs)


__all__ = ["FIND_PRACTICE_TOOL", "FindPracticeArguments", "run_find_practice_tool"]
