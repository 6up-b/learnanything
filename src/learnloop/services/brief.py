"""Typed synthesis brief (spec §8 / mvp-0.8 reader-first seeding).

The brief has always been an untyped dict threaded from the UI/CLI into
``create_study_map``; this module gives it a schema without changing the wire
format — dicts in, dicts out. ``validate_brief`` is the single normalization
point: it folds camelCase wire keys (the Tauri UI historically sent
``includeTopics``/``targetRecall``/… which the snake_case readers silently
ignored) into snake_case, validates known fields, and preserves unknown ones
(``extra="allow"``) so free-form briefs keep working.

``starting_level`` is the machine-readable learner level: a closed ordinal that
maps to a global learner claim (see :mod:`learnloop.services.learner_profile`)
and thereby seeds initial mastery/ability for difficulty calibration. The
free-text ``level`` field remains for qualitative prompt use.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError

# Ordinal learner levels (precedent: reader_authoring.COACH_LEVELS). Maps to a
# claimed mastery probability for the init-wizard global learner claim; the
# pseudo-count keeps the prior weak (variance 1.0) — a self-report should nudge
# the starting point, never dominate observed evidence.
STARTING_LEVELS: tuple[str, ...] = (
    "new_to_this",
    "some_exposure",
    "comfortable",
    "strong_background",
)

STARTING_LEVEL_CLAIMS: dict[str, float] = {
    "new_to_this": 0.15,
    "some_exposure": 0.35,
    "comfortable": 0.55,
    "strong_background": 0.75,
}

INIT_CLAIM_PSEUDO_COUNT = 1.0

StartingLevel = Literal["new_to_this", "some_exposure", "comfortable", "strong_background"]

PracticeItemsMode = Literal["upfront", "as_you_read"]


class Brief(BaseModel):
    """Known brief fields. Unknown keys are preserved verbatim."""

    model_config = ConfigDict(extra="allow")

    outcome: str | None = None
    level: str | None = None
    starting_level: StartingLevel | None = None
    depth: str | None = None
    scope: str | None = None
    subject: str | None = None
    source_title: str | None = None
    notation: str | None = None
    include_topics: list[str] | None = None
    exclude_topics: list[str] | None = None
    # Exam-prep goal fields (consumed by _create_goal_from_brief).
    goal_title: str | None = None
    target_recall: float | None = None
    due_at: str | None = None
    exam_item_count: int | None = None
    # Bootstrap item-authoring mode: "upfront" (default, config-resolved) authors
    # practice items at synthesis time; "as_you_read" authors none — items accrue
    # progressively from reading (reader quick-check escalation + per-section
    # expansion).
    practice_items: PracticeItemsMode | None = None


_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def _snake_name(name: str) -> str:
    return _CAMEL_BOUNDARY.sub("_", name).lower()


def _snake_keys(raw: dict[str, Any]) -> dict[str, Any]:
    return {_snake_name(str(key)): value for key, value in raw.items()}


class BriefValidationError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def validate_brief(raw: dict[str, Any] | None, *, strict: bool = True) -> dict[str, Any]:
    """Normalize + validate a brief dict, returning a snake_case dict.

    ``strict=True`` (entry boundaries: sidecar RPCs, CLI) raises
    :class:`BriefValidationError` on invalid known fields. ``strict=False``
    (service-side belt-and-braces over persisted briefs) drops invalid known
    fields instead — a stale stored brief must never fail a paid build.
    """

    data = _snake_keys(raw or {})
    try:
        model = Brief.model_validate(data)
    except ValidationError as exc:
        messages = [
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        ]
        if strict:
            raise BriefValidationError(messages) from exc
        for error in exc.errors():
            if error["loc"]:
                data.pop(str(error["loc"][0]), None)
        model = Brief.model_validate(data)
    return model.model_dump(exclude_none=True)
