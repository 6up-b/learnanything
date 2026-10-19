"""What a learner text is, how it is read, and the typed questions about it.

Learner-text gaps (implementation_handoffs §4, owner-directed 2026-10-12): a
tutor question, a non-empty stuck answer or a diagnosis of a wrong answer is
read for the gap it names: a missing prerequisite, a misconception (a wrong
belief), a slip, a wording or notation problem, or none.

The model with the whole exchange in context names the gap FIRST, in its own
words (``tutor.ai_contracts.LearnerGap``), then picks the kind; it is never
asked to pick from a list. The Decider answers the same typed question as a
logged second opinion. Every reading and verdict is appended to
``judgment_ledger``; nothing here is evidence (learner field G13).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import Field

from learnloop.ai.decisions import ChoiceQuestion
from learnloop.ai.schemas import WireModel
from learnloop.tutor.ai_contracts import LEARNER_GAP_KINDS, LEARNER_GAP_RULES, LearnerGap
from learnloop.vault.lifecycle import LEARNER_TEXT_GAP_MECHANISM

#: The pipeline's own version (what a ledger row was produced by).
PIPELINE_VERSION = "learner-text-gaps-v1"
#: Versioned provenance of what the pipeline writes into the vault: a created
#: concept / LO, an added prerequisite edge (the serving gate reads it).
PROVENANCE_MECHANISM = LEARNER_TEXT_GAP_MECHANISM
SOURCE_KINDS = ("tutor_question", "stuck_answer", "diagnosis", "reader_formative", "workbench_text", "hint_feedback")
#: The kinds this pipeline reads today: ``workbench_text`` is admitted by the
#: schema (migration 208) for RW2b, which builds its adapter; until then a
#: queued one is skipped as having nothing to read.
#: Adaptive hints H2b (migration 212) adds ``hint_feedback``: the practice
#: screen's "doesn't connect" text and discriminating answers, read from
#: ``help_assists`` (:func:`~.sources.hint_feedback_text`).
#: Reader workbench RW2b reads ``workbench_text`` (its adapter,
#: :func:`~.sources.workbench_text`): stuck steps, replies and discriminating
#: answers written while working in steps.
READABLE_SOURCE_KINDS = ("tutor_question", "stuck_answer", "diagnosis", "reader_formative", "hint_feedback",
                         "workbench_text")
#: The kinds whose named gaps stay content and display (spec W1 tier 2, RW1b
#: §4.5 "no successor"): a gap read from them names a prerequisite or a belief
#: (and may create one), but never brings a check forward and is never a weak
#: prerequisite observation for placement's fast track (``field.signals``).
#: Those are serving changes; feeding them from a missed active-reading answer
#: (or RW2b's workbench text, RW2d) needs its own algorithm successor with a
#: kill switch (Codex review of RW1b, F1). Before RW1b no row of either kind
#: existed, so excluding them changes nothing that was served.
#: ``hint_feedback`` (adaptive hints H2b) joins them for the same reason: a
#: gap named in a reply to a hint is content and the next hint's rivals,
#: never a serving change (spec_adaptive_hints_v1 §9; no successor).
NON_SERVING_SOURCE_KINDS = ("reader_formative", "workbench_text", "hint_feedback")
#: The kinds, plus ``unread`` (the context model's reading failed and the
#: Decider gave none either).
KINDS = LEARNER_GAP_KINDS
UNREAD = "unread"
CHOOSERS = ("context_model", "decider")

#: ``judgment_ledger`` tasks.
KIND_TASK = "learner_gap_kind"
SAME_PREREQUISITE_TASK = "same_prerequisite"
SAME_BELIEF_TASK = "same_belief"
NEEDED_TASK = "prerequisite_needed"

#: Prompt / question-set versions.
DECIDER_KIND_QUESTION_SET = "learner-gap-kind-qs-v1"
DECIDER_PAIR_QUESTION_SET = "learner-gap-pair-qs-v1"
DECIDER_NEEDED_QUESTION_SET = "prerequisite-needed-qs-v1"
READER_PROMPT_VERSION = "learner-gap-reader-v1"
#: RW1b: the same reader, told it reads a missed active-reading answer.
READER_FORMATIVE_PROMPT_VERSION = "learner-gap-reader-formative-v1"
NEEDED_PROMPT_VERSION = "prerequisite-needed-v1"
DRAFT_PROMPT_VERSION = "learner-gap-prerequisite-draft-v1"

#: Operations (``ai.routing.ROUTE_FOR_OPERATION``) and their routes.
READER_PURPOSE = "learner_gap_reading"
NEEDED_PURPOSE = "learner_gap_prerequisite_needed"
DRAFT_PURPOSE = "learner_gap_prerequisite_draft"
JUDGE_ROUTE = "learner_gap_judge"
READER_ROUTE = "learner_gap_reader"
DECIDER_ROUTE = "learner_gap_decider"
DRAFT_ROUTE = "authoring"
EMBEDDING_ROUTE = "embedding"


@dataclass(frozen=True)
class GapReading:
    """One reading of a learner text: the kind and the gap as named.

    ``status`` is ``ok`` or ``failed`` (the call failed or was refused; the
    reading then names nothing).
    """

    kind: str
    prerequisite_name: str | None = None
    prerequisite_line: str | None = None
    belief_statement: str | None = None
    judge: str = "llm"  # llm | diagnoser
    judge_model: str = "unknown"
    prompt_version: str = ""
    status: str = "ok"
    #: Diagnosis readings: the diagnoser's own picks (validated refs).
    prerequisite_refs: tuple[str, ...] = ()
    registry_match: Mapping[str, Any] | None = None

    @classmethod
    def from_gap(cls, gap: LearnerGap | Mapping[str, Any], **extra: Any) -> "GapReading":
        data = gap.model_dump(mode="json") if hasattr(gap, "model_dump") else dict(gap)
        kind = str(data.get("kind") or "none")
        return cls(
            kind=kind if kind in KINDS else "none",
            prerequisite_name=_clean(data.get("prerequisite_name")),
            prerequisite_line=_clean(data.get("prerequisite_line")),
            belief_statement=_clean(data.get("belief_statement")),
            **extra,
        )

    def named(self) -> dict[str, Any]:
        return {
            "prerequisite_name": self.prerequisite_name,
            "prerequisite_line": self.prerequisite_line,
            "belief_statement": self.belief_statement,
        }

    def as_progress(self) -> dict[str, Any]:
        """JSON for the job's progress: a retry acts on this reading, never a
        second one (re-review F1)."""

        return {
            "kind": self.kind, **self.named(), "judge": self.judge, "judge_model": self.judge_model,
            "prompt_version": self.prompt_version, "status": self.status,
            "prerequisite_refs": list(self.prerequisite_refs),
            "registry_match": dict(self.registry_match) if self.registry_match is not None else None,
        }

    @classmethod
    def from_progress(cls, data: Mapping[str, Any]) -> "GapReading":
        return cls(
            kind=str(data["kind"]), prerequisite_name=data.get("prerequisite_name"),
            prerequisite_line=data.get("prerequisite_line"), belief_statement=data.get("belief_statement"),
            judge=str(data.get("judge") or "llm"), judge_model=str(data.get("judge_model") or "unknown"),
            prompt_version=str(data.get("prompt_version") or ""), status=str(data.get("status") or "ok"),
            prerequisite_refs=tuple(str(ref) for ref in data.get("prerequisite_refs") or ()),
            registry_match=dict(data["registry_match"]) if data.get("registry_match") is not None else None,
        )

    def names(self, kind: str) -> bool:
        """Does this reading name a gap of ``kind`` (so it can be matched)?"""

        if kind == "prerequisite":
            return bool(self.prerequisite_name) or bool(self.prerequisite_refs)
        if kind == "misconception":
            return bool(self.belief_statement) or bool(self.registry_match)
        return True


def _clean(value: Any) -> str | None:
    text = " ".join(str(value or "").split())[:500]
    return text or None


@dataclass(frozen=True)
class LearnerText:
    """One learner text the pipeline reads.

    ``anchor_learning_object_ids`` are the LOs the text is about (the item's
    LO; a note's related LOs); ``subject_id`` is the asking item's subject,
    which grounds every target. ``reading`` is the context model's reading
    when it was produced elsewhere (the tutor's answer, the diagnosis); the
    stuck-text reader produces its own.
    """

    source_kind: str
    source_id: str
    text: str
    context_judge: str  # tutor | diagnoser | gap_reader
    created_at: str
    subject_id: str | None = None
    anchor_learning_object_ids: tuple[str, ...] = ()
    practice_item_id: str | None = None
    attempt_id: str | None = None
    question_event_id: str | None = None
    reading: GapReading | None = None
    #: What the Decider and the stuck-text reader see besides the text (the
    #: item's prompt, the LO title, a note title). Never an answer key.
    context: Mapping[str, Any] = field(default_factory=dict)

    @property
    def anchor(self) -> str | None:
        return self.anchor_learning_object_ids[0] if len(self.anchor_learning_object_ids) == 1 else None

    @property
    def subject_key(self) -> str:
        return f"{self.source_kind}:{self.source_id}"


# -- the Decider's typed questions -------------------------------------------------------

KIND_OPTIONS: dict[str, str] = {
    "prerequisite": "Missing knowledge that this material builds on: a prerequisite the learner does not know.",
    "misconception": "A wrong belief: the text states or presupposes something false.",
    "slip": "A procedural error or a lapse, not missing knowledge.",
    "wording": "A wording or notation problem: what the prompt or a symbol means.",
    "none": "Nothing missing: curiosity, a check of the learner's own work, or no gap at all.",
}

KIND_QUESTION = ChoiceQuestion(
    instructions=(
        "The state holds one text a learner wrote (a question to a tutor, an answer written "
        "when stuck, or a wrong answer) and what it was about. What does the LEARNER'S text "
        "show about the learner? Judge the learner's words only."
    ),
    options=KIND_OPTIONS,
)

PAIR_QUESTION_INSTRUCTIONS = (
    "The state is a judging task about two items, `first` and `second`. Answer its question "
    "with exactly one option."
)
PAIR_OPTIONS: dict[str, str] = {
    "same": "The two items are the same in the sense the task's question asks.",
    "different": "They are different in that sense.",
    "unsure": "The text cannot settle it.",
}

NEEDED_OPTIONS: dict[str, str] = {
    "yes": "Knowing the prerequisite is needed to do this practice item.",
    "no": "The item can be done without it.",
    "unsure": "The text cannot settle it.",
}
NEEDED_QUESTION = ChoiceQuestion(
    instructions=(
        "The state holds one practice item and one piece of knowledge. Is that knowledge "
        "needed to do the item (it builds on it), as opposed to merely related?"
    ),
    options=NEEDED_OPTIONS,
)


# -- LLM contracts ----------------------------------------------------------------------


class NeededVerdict(WireModel):
    """"Is this prerequisite needed to do this item?" (one isolated call)."""

    verdict: Literal["yes", "no", "unsure"]
    rationale: str = Field(description="One sentence naming why the item does or does not build on it.")


class PrerequisiteDraft(WireModel):
    """The missing prerequisite as a concept, one learning objective and its edge."""

    concept_title: str = Field(description="The concept's name, as a textbook section would title it.")
    concept_description: str = Field(description="Two or three sentences defining the concept.")
    concept_type: Literal["concept", "procedure", "skill"] = "concept"
    learning_object_title: str = Field(description="A short learning-objective title.")
    learning_object_statement: str = Field(
        description="One or two sentences: what the learner will be able to do or explain."
    )
    knowledge_type: Literal["definition", "procedure", "concept", "skill", "fact"] = "concept"
    edge_rationale: str = Field(description="One sentence: why the asking item builds on this prerequisite.")


READER_TASK = (
    "You read ONE answer a learner wrote after pressing \"I'm stuck\" and being asked to "
    "write what they can, or what is confusing them. Return a LearnerGap as schema-valid "
    "JSON only. " + LEARNER_GAP_RULES + " The item they were answering is in `context`; "
    "it is background only: report on the learner's own words."
)

# RW1b (spec_reader_workbench_v1 §4.2): a next-step, why-step or assumption
# answer the learner wrote while reading and then marked, after seeing the
# expected answer, as only partly matching or not matching it.
READER_FORMATIVE_TASK = (
    "You read ONE answer a learner wrote while reading a book: they were asked a short question "
    "about a passage (`context.question`: predict the next step, justify a step, or name what it "
    "assumes), answered it, were shown the expected answer (`context.expected_answer`, the book's "
    "own lines or, when `context.expected_answer_from` says so, LearnLoop's model's) and judged their "
    "own answer as `context.self_check` (partly, or no). Name what their answer shows they were "
    "missing. Return a LearnerGap as schema-valid JSON only. " + LEARNER_GAP_RULES + " The passage "
    "and the expected answer are background only: report on the learner's own words."
)

NEEDED_TASK_TEXT = (
    "Decide whether the learning objective in `context.prerequisite` is NEEDED to do the "
    "practice item in `context.item`: the item builds on it, so a learner without it could "
    "not do the item. Related or nearby topics are not enough. Return a NeededVerdict as "
    "schema-valid JSON only."
)

DRAFT_TASK = (
    "A learner's own text named knowledge they are missing, and no learning objective in "
    "their course covers it. Draft it as ONE concept and ONE learning objective under it, "
    "plus why the item the learner was working on builds on it. Stay at the scope the "
    "learner named (`context.named`): do not broaden it into a course. Write plain, "
    "correct definitions; never invent facts about the learner. Return a PrerequisiteDraft "
    "as schema-valid JSON only."
)


__all__ = [
    "CHOOSERS",
    "DECIDER_KIND_QUESTION_SET",
    "DECIDER_NEEDED_QUESTION_SET",
    "DECIDER_PAIR_QUESTION_SET",
    "DECIDER_ROUTE",
    "DRAFT_PROMPT_VERSION",
    "DRAFT_PURPOSE",
    "DRAFT_ROUTE",
    "DRAFT_TASK",
    "EMBEDDING_ROUTE",
    "GapReading",
    "JUDGE_ROUTE",
    "KINDS",
    "KIND_OPTIONS",
    "KIND_QUESTION",
    "KIND_TASK",
    "LearnerText",
    "NEEDED_OPTIONS",
    "NEEDED_PROMPT_VERSION",
    "NEEDED_PURPOSE",
    "NEEDED_QUESTION",
    "NEEDED_TASK",
    "NEEDED_TASK_TEXT",
    "NeededVerdict",
    "PAIR_OPTIONS",
    "PAIR_QUESTION_INSTRUCTIONS",
    "PIPELINE_VERSION",
    "PROVENANCE_MECHANISM",
    "PrerequisiteDraft",
    "READER_PROMPT_VERSION",
    "READER_PURPOSE",
    "READER_ROUTE",
    "READER_FORMATIVE_PROMPT_VERSION",
    "READER_FORMATIVE_TASK",
    "NON_SERVING_SOURCE_KINDS",
    "READABLE_SOURCE_KINDS",
    "READER_TASK",
    "SAME_BELIEF_TASK",
    "SAME_PREREQUISITE_TASK",
    "SOURCE_KINDS",
    "UNREAD",
]
