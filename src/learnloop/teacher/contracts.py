"""The lesson contracts (spec_teacher_v1 §8): the brief, the teacher's turn, the receipt, and the actions.

* ``LessonBriefV1`` (code -> teacher, §8.1) is built by :mod:`.brief` as a plain
  mapping with :data:`BRIEF_VERSION`; it is the only learner context at open.
* :class:`TeacherTurnV1` (desktop teacher -> code, §8.2) is one strict-schema
  object per model turn: a message, an optional prediction, an optional check,
  and zero or more action requests (§9: one message plus requests).
* ``LessonReceiptV1`` (teacher -> ledger, §8.3) is built by :mod:`.service`
  with :data:`RECEIPT_VERSION`.

The teacher's actions (§9) are one strict request model: ``read_source``,
``find_sources``, ``find_practice``, ``read_history``, ``read_note`` (curriculum
C4), ``write_plan``, ``forecast`` and ``close``; ``pose_prediction`` and
``pose_check`` are the turn's own ``prediction`` and ``check`` fields. No action
grades, writes evidence, picks or dates a delayed check, creates an edge or
reads protected material: no field exists for any of them (§9).
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from learnloop.ai.schemas import WireModel

#: The brief's, the turn's and the receipt's versions (§8).
BRIEF_VERSION = "lesson_brief_v1"
TURN_VERSION = "teacher_turn_v1"
RECEIPT_VERSION = "lesson_receipt_v1"
#: The teacher prompt's identity (with the doctrine version beside it on every receipt).
PROMPT_VERSION = "teacher_turn.v1"

ACTIONS: tuple[str, ...] = (
    "read_source", "find_sources", "find_practice", "read_history", "read_note", "write_plan", "forecast", "close",
)
#: The actions whose results go back to the model (the rest only write or close).
READ_ACTIONS = frozenset({"read_source", "find_sources", "find_practice", "read_history", "read_note"})
CLOSE_REASONS: tuple[str, ...] = (
    "goal_reached", "learner_stop", "budget", "plan_unavailable", "teacher_contract_failure",
    # The vault's protection state changed since the brief was built (ruling R1): code's, never the teacher's.
    "protection_changed",
)
#: Close reasons the teacher itself may give (the others are code's).
TEACHER_CLOSE_REASONS: tuple[str, ...] = ("goal_reached", "learner_stop")
FORECAST_KINDS: tuple[str, ...] = ("lesson_check_correct", "lesson_step_retained")


class CriterionV1(WireModel):
    """One rubric criterion, named by the fact it establishes (owner rule 2026-10-13)."""

    id: str = Field(min_length=1, max_length=40)
    fact: str = Field(min_length=1, max_length=600)
    points: int = Field(ge=1, le=10)


class PredictionV1(WireModel):
    """A nudge before a step (§10 item 7): it arrives open and need not be answerable."""

    node: str = Field(min_length=1, max_length=80)
    prompt: str = Field(min_length=1, max_length=2000)
    choices: list[str] = Field(default_factory=list, max_length=6)


class CheckV1(WireModel):
    """A check after a step (§8.2): answerable from the lesson, applied, its solution committed first."""

    node: str = Field(min_length=1, max_length=80)
    question: str = Field(min_length=1, max_length=4000)
    form: Literal["choices", "free"]
    choices: list[str] = Field(default_factory=list, max_length=6)
    committed_solution: str = Field(min_length=1, max_length=4000)
    rubric: list[CriterionV1] = Field(min_length=1, max_length=8)
    #: The delivered passages (their aliases, ``S3``) the check rests on; empty: "LearnLoop's answer".
    anchors: list[str] = Field(default_factory=list, max_length=12)


class PlanNodeV1(WireModel):
    id: str = Field(min_length=1, max_length=80)
    statement: str = Field(min_length=1, max_length=600)
    lo_id: str | None = None
    anchors: list[str] = Field(default_factory=list, max_length=12)
    premises: list[str] = Field(default_factory=list, max_length=12)


class ActionRequestV1(WireModel):
    """One requested action (§9). Each action reads only the fields it names."""

    action: Literal[
        "read_source", "find_sources", "find_practice", "read_history", "read_note", "write_plan", "forecast", "close",
    ]
    #: find_sources / find_practice: what to look for.
    query: str | None = Field(default=None, max_length=2000)
    #: find_sources: explain | remediate | alternative | worked_example; find_practice: practice |
    #: discriminate | retention | remediate.
    intent: str | None = Field(default=None, max_length=40)
    #: read_source: section refs (``ext/section``) or passage aliases; read_history: history ids
    #: (``h:...``, ``q:...``, ``l:...``); read_note: note ids from the brief.
    refs: list[str] = Field(default_factory=list, max_length=20)
    learning_object_ids: list[str] = Field(default_factory=list, max_length=20)
    unattempted_only: bool = False
    #: write_plan: the outline.
    plan: list[PlanNodeV1] = Field(default_factory=list, max_length=12)
    #: forecast: its kind, the node (or the open check) it is about, and the probability.
    forecast_kind: Literal["lesson_check_correct", "lesson_step_retained"] | None = None
    node: str | None = Field(default=None, max_length=80)
    p: float | None = Field(default=None, ge=0.0, le=1.0)
    #: close: why, and the recap (what to retrieve later, not a summary).
    close_reason: Literal["goal_reached", "learner_stop"] | None = None
    recap: str | None = Field(default=None, max_length=4000)


class TeacherTurnV1(WireModel):
    """One model turn (§8.2)."""

    message: str = Field(default="", max_length=12000)
    choices: list[str] = Field(default_factory=list, max_length=6)
    prediction: PredictionV1 | None = None
    check: CheckV1 | None = None
    requests: list[ActionRequestV1] = Field(default_factory=list, max_length=8)


__all__ = [
    "ACTIONS",
    "BRIEF_VERSION",
    "CLOSE_REASONS",
    "FORECAST_KINDS",
    "PROMPT_VERSION",
    "READ_ACTIONS",
    "RECEIPT_VERSION",
    "TEACHER_CLOSE_REASONS",
    "TURN_VERSION",
    "ActionRequestV1",
    "CheckV1",
    "CriterionV1",
    "PlanNodeV1",
    "PredictionV1",
    "TeacherTurnV1",
]
