"""Structured AI contracts owned by tutor and teach-back features."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from pydantic import Field

from learnloop.ai.schemas import CandidateCause, WireModel
from learnloop.ai.transport import render_structured_prompt
from learnloop.content.authoring.ai_contracts import (
    BANNED_RESPONSE_MODES,
    LOW_MASTERY_RESPONSE_MODES,
)
from learnloop.content.proposals.ai_contracts import TraceContractPayload


@dataclass(frozen=True)
class TutorQAContext:
    context: str
    question_md: str
    candidate_facets: list[str] = field(default_factory=list)
    thread: list[dict] = field(default_factory=list)
    practice_item_prompt: str | None = None
    expected_answer: str | None = None
    rubric: dict | None = None
    learner_answer_md: str | None = None
    grading_feedback: dict | None = None
    note_title: str | None = None
    note_body: str | None = None
    learning_object_summaries: list[dict] = field(default_factory=list)
    diagnostic_decision: dict | None = None
    source_spans: list[dict] = field(default_factory=list)
    answer_mode: str | None = None


@dataclass(frozen=True)
class TeachBackQuestionContext:
    practice_item_id: str
    practice_item_prompt: str
    criterion_id: str
    criterion_description: str
    criterion_tier: str
    facet_targets: list[str] = field(default_factory=list)
    transcript: list[dict] = field(default_factory=list)
    question_number: int = 1
    max_followups: int = 4
    learning_object_title: str | None = None
    learning_object_summary: str | None = None


@dataclass(frozen=True)
class TeachBackAuthoringContext:
    source_practice_item_id: str
    source_prompt: str
    source_expected_answer: Any
    source_criteria: list[dict] = field(default_factory=list)
    source_trace_contract: dict | None = None
    allowed_facets: list[dict] = field(default_factory=list)
    learning_object_title: str = ""
    learning_object_summary: str = ""
    quest_sentence: str | None = None
    max_core_criteria: int = 3


@dataclass(frozen=True)
class PromotionAnalysisContext:
    intent: str
    thread: list[dict] = field(default_factory=list)
    learning_object_id: str | None = None
    learning_object_title: str | None = None
    facet_vocabulary: list[str] = field(default_factory=list)
    concept_neighbors: list[dict] = field(default_factory=list)
    existing_items: list[dict] = field(default_factory=list)


class TutorCitation(WireModel):
    extraction_id: str
    span_id: str
    label: str | None = None


class TutorAnswer(WireModel):
    answer_md: str
    question_type: Literal[
        "clarification", "prerequisite", "mechanism", "strategy", "verification", "other"
    ] = "other"
    facets: list[str] = Field(default_factory=list)
    question_channel: Literal["epistemic", "interaction_preference"] = "epistemic"
    citations: list[TutorCitation] = Field(default_factory=list)
    embedded_prediction: str | None = None
    new_candidate_cause: CandidateCause | None = None


class TeachBackQuestion(WireModel):
    question_md: str


class TeachBackCriterionDraft(WireModel):
    description: str = ""
    source_criterion_ids: list[str] = Field(default_factory=list)
    measurement_status: Literal[
        "direct", "supporting", "composite", "item_local", "no_canonical_facet"
    ] = "item_local"
    facet_ids: list[str] = Field(default_factory=list)


class TeachBackAuthoring(WireModel):
    prompt_md: str = ""
    expected_answer_md: str = ""
    core_criteria: list[TeachBackCriterionDraft] = Field(default_factory=list)
    transfer_criterion: TeachBackCriterionDraft | None = None
    transfer_scenario: str = ""
    quest_connection: Literal["connected", "not_relevant", "no_quest"] = "no_quest"
    trace_contract: TraceContractPayload | None = None


class PromotionAnalysis(WireModel):
    attributed_facets: list[str] = Field(default_factory=list)
    question_nature: Literal["core_recall", "mechanism", "transfer", "edge_case", "what_if"] = "core_recall"
    attempted_in_thread: bool = False
    covered_by_practice_item_id: str | None = None


TUTOR_QA_PROMPT_VERSION = "mvp-0.8-tutor-qa-learner-embedded-prediction"
TEACH_BACK_PROMPT_VERSION = "mvp-0.4-teach-back"
TEACH_BACK_AUTHORING_PROMPT_VERSION = "mvp-0.1-source-item-quest-transfer"
PROMOTION_ANALYSIS_PROMPT_VERSION = "mvp-0.1-promotion-analysis"
TUTOR_PROMOTION_PROMPT_VERSION = "mvp-0.2-constructed-response-and-keyed-misconceptions"

PROMOTION_ANALYSIS_PROMPT = """\
You are analysing ONE tutor Q&A thread the learner has chosen to promote. The \
tutor answers a learner's question with a SOCRATIC guiding question (never the \
answer itself); the LAST turn in `context.thread` is the one being promoted, and \
the socratic question lives inside its `answer_md`. Return a PromotionAnalysis as \
schema-valid JSON only.

- `attributed_facets`: the evidence facet ids the tutor's socratic question \
exercises. This is a CLOSED vocabulary: return only exact ids from \
`context.facet_vocabulary`. If it is empty or no listed facet covers the probe, \
return an empty list; never mint a facet id during question promotion.
- `question_nature`: classify the socratic question as exactly one of \
`core_recall` (retrieve a fact/definition), `mechanism` (why/how something \
works), `transfer` (apply to a novel situation), `edge_case` (a boundary or \
corner case), or `what_if` (a counterfactual).
- `attempted_in_thread`: true iff the learner visibly TRIED the socratic \
question earlier in the thread and did not answer it comfortably; false if they \
never engaged with it.
- `covered_by_practice_item_id`: if one of `context.existing_items` ALREADY \
exercises the same probe (same facets AND substantially the same cognitive \
demand / surface), return its id so the system schedules it instead of authoring \
a duplicate. Return null when nothing covers it — reuse beats authoring, but do \
NOT force a weak match.
"""

TUTOR_PROMOTION_PROMPT = """\
Promote ONE tutor Q&A exchange into a LearnLoop authoring proposal. The learner \
flagged the tutor's SOCRATIC guiding question as worth keeping as a rep. The \
thread, origin context, and Step-0 attribution are in PROMOTION_CONTEXT below.

1. Derive the practice prompt FROM the tutor's socratic question: extract that \
guiding question from the tutor turn and rephrase it to stand ALONE — \
self-contained, with no reference to "the conversation", "your earlier answer", \
or the item the learner was working on. Each item's `rationale` MUST quote the \
original guiding question VERBATIM (in quotation marks) so a reviewer can see \
what it came from.
2. Attachment decision: if the probed knowledge falls under the origin Learning \
Object (or another existing LO named in context), author ONE `practice_item` \
create against it. Use only existing canonical facet ids from the Step-0 \
`attributed_facets` or the Learning Object's `existing_evidence_facets`; never \
mint a facet id in a practice-item proposal. Only \
if the probe genuinely does not fit any existing LO, author a `learning_object` \
create PLUS its first `practice_item` in the same batch.
3. New Learning Objects MUST use an EXISTING concept id from context \
(`concept_neighbors`). Never invent a concept. If none fits, attach to the \
nearest existing concept and say so in the rationale.
4. Synthesize `expected_answer` from the ATTACHED SOURCE MATERIAL — the tutor \
never stated the answer (guardrail), so this is new content and the main quality \
risk. Do not restate the socratic question as its own answer.
5. Full generated-item metadata contract applies (rubric, evidence_facets / \
weights, criterion_facet_weights, difficulty, surface_family, retrieval_demand, \
transfer_distance, scaffold_level, repair_targets, audit). If you choose a \
`practice_mode` that has no default rubric, ship an explicit `grading_rubric`.
6. Practice mode scales to learner skill. The context carries the origin LO's \
`mastery_mean` and `recommended_difficulty_band`. Pick the mode from this ladder \
keyed to the mastery band: LOW mastery -> cued constructed-response modes \
(__LOW_MASTERY_MODES__) — provide support through `hints` and `scaffold_level`, \
NEVER through answer options; MID mastery -> recall/application \
(`short_answer`, `worked_calculation`); HIGH mastery -> synthesis/transfer \
(`constructed_response`, `proof_explanation`, `teach_back`). Selected-response \
surfaces are BANNED and deterministically rejected: never use \
__BANNED_MODES__, never present lettered answer options (A. / B) / …) or \
true-false choices, and `task_features.response` must agree with the chosen \
mode (never `recognize`). \
Calibrate `difficulty` into the recommended_difficulty_band. For a NEW LO (no \
mastery yet) default to the MID band — the probe will place it.
7. Tag every created item with `tutor_promoted` (add it to the payload `tags`).
8. Leave `misconception_consistent_answer` null for ordinary practice. Populate \
it ONLY when a misconception from `registered_misconceptions` in \
PROMOTION_CONTEXT is this item's diagnostic target, and then the rubric MUST \
carry a fatal error whose `misconception_id` is that canonical id. If \
`registered_misconceptions` is empty or absent, there is no canonical belief to \
key against: leave the field null.
"""

TUTOR_PROMOTION_PROMPT = TUTOR_PROMOTION_PROMPT.replace(
    "__LOW_MASTERY_MODES__", ", ".join(f"`{mode}`" for mode in LOW_MASTERY_RESPONSE_MODES)
).replace(
    "__BANNED_MODES__", ", ".join(f"`{mode}`" for mode in BANNED_RESPONSE_MODES)
)

_TUTOR_QA_LEARNER_EXTRACTION = (
    "Two fields report on the LEARNER'S QUESTION rather than on your answer. "
    "`embedded_prediction`: if the learner's question itself asserts a "
    "falsifiable expectation — something they evidently expect to be true, "
    "e.g. \"learner expects replacing (x+y)e2 with ((x+y)/2)e2 to change the "
    "sum\" — state that expectation in one sentence. Take it from the question "
    "TEXT; do not infer what they probably think, and set it to null when the "
    "question asserts nothing (that is the common case). "
    "`new_candidate_cause`: set it ONLY when this exchange surfaced a possible "
    "cause of the learner's difficulty that their written attempt could not "
    "have shown — something they said or asked that reveals it. Write "
    "`statement` as plain prose in learner-model terms; there is no vocabulary "
    "to fit. Ground it in the learner's words, NEVER in what you just "
    "explained: after you have answered, anything you would say about their "
    "beliefs describes your own explanation, not them. Null is the correct and "
    "usual answer."
)

_TUTOR_QA_SHARED = (
    "You are a LearnLoop tutor answering one learner question. Return a "
    "TutorAnswer as schema-valid JSON only. Classify the question as exactly one "
    "question_type: `clarification` (what the prompt/wording means), "
    "`prerequisite` (background knowledge needed), `mechanism` (why/how "
    "something works), `strategy` (how to approach the task), `verification` "
    "(is my answer/approach right?), or `other`. Also classify question_channel: "
    "`epistemic` when the question signals missing or uncertain knowledge about "
    "the content, `interaction_preference` when the learner is instead asking "
    "for a different explanation style, pace, scaffold level, more or less "
    "detail, or a direct answer (a request about HOW to be tutored, not WHAT is "
    "true). Fill `facets` with the subset "
    "of context.candidate_facets the question is genuinely about (empty when "
    "none apply); never invent facet ids outside that list. Use "
    "context.thread as prior conversation turns and stay consistent with them. "
    "Write answer_md as concise Markdown (LaTeX math allowed). "
    "When context.source_spans is non-empty and a span grounds a claim you make, "
    "add it to `citations` as {extraction_id, span_id, label} using ONLY the "
    "extraction_id/span_id pairs present in context.source_spans — never invent a "
    "span, and cite only spans your answer actually relies on. Leave citations "
    "empty when no provided span is relevant."
    " " + _TUTOR_QA_LEARNER_EXTRACTION
)

_TUTOR_QA_CONTEXT_TASKS = {
    "practice": (
        "Context: the learner is MID-ATTEMPT on the given practice item. Act as "
        "a Socratic tutor. You MUST NOT state the answer, complete the "
        "derivation, reveal the expected answer, or confirm or deny whether the "
        "learner's current approach or partial answer is correct. If the "
        "question asks for verification, deflect with a guiding question that "
        "helps the learner check it themselves. Clarify wording, surface "
        "prerequisites, and nudge strategy without giving away the solution."
    ),
    "feedback": (
        "Context: the learner's attempt has already been graded. Full "
        "explanation is allowed and encouraged: ground your answer in the "
        "practice item, its rubric, the learner's answer, and the grading "
        "feedback provided, explaining what went wrong or right and why."
    ),
    "library": (
        "Context: the learner is reading a note. Answer explanatorily, "
        "grounded in the note body and the related learning objects; connect "
        "the answer back to the note's content."
    ),
    "reader": (
        "Context: the learner is reading a source span in the reader (U-033). "
        "There is NO attempt to protect here, so you are NOT Socratic-by-default: "
        "you MAY state facts, complete a derivation, give a worked example, and "
        "confirm or deny an interpretation. Ground every claim in the provided "
        "source spans and cite them. Support comprehension, inquiry, "
        "self-explanation, and goal connection. You are NOT given the learner's "
        "ability estimate and MUST NOT tune the answer to a supposed deficit."
    ),
}

_TUTOR_QA_READER_MODE_TASKS = {
    "answer_directly": (
        " Answer mode: ANSWER DIRECTLY -- give the complete answer up front, "
        "then a brief why."
    ),
    "help_me_reason": (
        " Answer mode: HELP ME REASON -- do not hand over the final answer first; "
        "walk the learner through the reasoning steps so they reach it."
    ),
    "ask_me_first": (
        " Answer mode: ASK ME FIRST -- open with one focused question that checks "
        "the learner's current understanding before you explain."
    ),
}

_TEACH_BACK_TASK = (
    "You are a curious NAIVE STUDENT being taught by the learner. The learner "
    "just explained the concept to you (see context.transcript, oldest first). "
    "Return a TeachBackQuestion as schema-valid JSON only. Ask exactly ONE "
    "short follow-up question, in character, that probes the rubric criterion "
    "described by context.criterion_description and, when present, its target "
    "facets (context.facet_targets). An item-local criterion can honestly have "
    "no facet target; in that case use the criterion description and practice "
    "item prompt. You do not know the answer: you may feign "
    "confusion, ask for a simpler explanation, an example, an edge case, or a "
    "what-if — but you MUST NOT correct the learner, confirm or deny whether "
    "anything they said is right, reveal any part of the answer, or introduce "
    "facts they have not taught you. Condition on the transcript: do not ask "
    "about something the learner's explanation or earlier answers already "
    "clearly covered; probe the part of the criterion that is still untaught "
    "or fuzzy. If context.criterion_tier is \"transfer\", push toward edge "
    "cases, unusual applications, or transfer scenarios for the criterion. "
    "Write question_md as one concise Markdown question (LaTeX math allowed)."
)

_TEACH_BACK_AUTHORING_TASK = (
    "Transform the ONE completed source Practice Item into a focused teach-back "
    "conversation contract. Return TeachBackAuthoring as schema-valid JSON only. "
    "The opening prompt must name the source problem or task specifically and ask "
    "the learner to explain the reasoning or method; NEVER replace it with the "
    "broad Learning Object title, and do not reveal the expected answer, solution "
    "steps, or hints in that opening prompt. Author 1..context.max_core_criteria core criteria "
    "that together cover EVERY id in context.source_criteria exactly as a teachable "
    "explanation. List the covered ids in source_criterion_ids. You may combine "
    "adjacent source criteria, but may not omit one or invent an id. For every "
    "criterion, link only facet ids from context.allowed_facets that it genuinely "
    "measures. Use item_local or no_canonical_facet with an empty facet_ids list "
    "when the source procedure is more specific than the facet vocabulary; do not "
    "copy a uniform whole-item facet smear. Author exactly one transfer criterion. "
    "If context.quest_sentence is relevant, create a modest, concrete scenario "
    "connected to that sentence which still exercises the SAME reasoning as the "
    "source item, set quest_connection=connected, and place the scenario in "
    "transfer_scenario. The quest may shape ONLY this transfer criterion, never "
    "the core criteria or their facet mappings. If the quest is absent, set "
    "quest_connection=no_quest and use a nearby edge case. If it is unrelated, "
    "set quest_connection=not_relevant and use a nearby edge case rather than "
    "forcing a superficial analogy. The transfer criterion must name what reasoning "
    "the learner should transfer and include the relevant source_criterion_ids. "
    "A transfer criterion that names facets must use measurement_status=supporting; "
    "otherwise use item_local or no_canonical_facet with no facet ids. "
    "Write expected_answer_md as an explanation standard, not merely the final "
    "answer. Preserve context.source_trace_contract when it is reliable; otherwise "
    "compile a small checkpoint trace from the expected reasoning, or return null "
    "when no reliable decomposition exists."
)

_TUTOR_QA_DIAGNOSTIC_DECISION_TASK = (
    "A diagnostic episode on this Learning Object has ENDED and transitioned to "
    "tutoring. context.diagnostic_decision is the persisted typed decision: "
    "ground your tutoring in it. Open with the named `tutor_move` (e.g. "
    "contrast_cases = contrast the target with the confusable; counterexample = "
    "present a case where the diagnosed belief fails; explanation = teach the "
    "mechanism; transfer_question = pose a shifted-surface question; "
    "state_subgoal = name the next subgoal; localize_error = walk to the first "
    "divergent step; elicit_reasoning = ask for their reasoning first). Target "
    "the `target_facets` and the `diagnosed_gap`; match depth to "
    "`scaffold_level` (0 = minimal support, 1 = heavy scaffolding). "
    "`answer_reveal_budget` overrides the mid-attempt guardrail: 0 means never "
    "reveal, 1 means partial worked steps are allowed, 2 means full explanation "
    "including the answer is allowed — measurement is over, so teaching to the "
    "diagnosed gap is the goal."
)

_TUTOR_QA_OPENING_SHARED = (
    "You are a LearnLoop tutor OPENING a tutoring conversation. There is no "
    "learner question yet — do not ask what they would like to know or wait "
    "for one; proactively execute the move below. Return a TutorAnswer as "
    "schema-valid JSON only. Set question_type to `strategy` and "
    "question_channel to `epistemic`. Fill `facets` with the subset of "
    "context.candidate_facets your opening targets (empty when none apply); "
    "never invent facet ids outside that list. Write answer_md as concise "
    "Markdown (LaTeX math allowed). There is no learner question here, so "
    "`embedded_prediction` and `new_candidate_cause` MUST both be null: with "
    "nothing the learner has said, any cause you named would be your own."
)


def tutor_qa_prompt(context: TutorQAContext) -> str:
    opening = not context.question_md.strip() and context.diagnostic_decision is not None
    task = _TUTOR_QA_CONTEXT_TASKS.get(context.context, _TUTOR_QA_CONTEXT_TASKS["library"])
    if context.context == "reader" and context.answer_mode:
        task = task + _TUTOR_QA_READER_MODE_TASKS.get(context.answer_mode, "")
    if context.diagnostic_decision is not None:
        task = task + " " + _TUTOR_QA_DIAGNOSTIC_DECISION_TASK
    shared = _TUTOR_QA_OPENING_SHARED if opening else _TUTOR_QA_SHARED
    return render_structured_prompt(
        "learnloop tutor qa",
        TUTOR_QA_PROMPT_VERSION,
        {"task": shared + " " + task, "context": asdict(context)},
    )


def teach_back_question_prompt(context: TeachBackQuestionContext) -> str:
    return render_structured_prompt(
        "learnloop teach-back question",
        TEACH_BACK_PROMPT_VERSION,
        {"task": _TEACH_BACK_TASK, "context": asdict(context)},
    )


def teach_back_authoring_prompt(context: TeachBackAuthoringContext) -> str:
    return render_structured_prompt(
        "learnloop source-item teach-back authoring",
        TEACH_BACK_AUTHORING_PROMPT_VERSION,
        {"task": _TEACH_BACK_AUTHORING_TASK, "context": asdict(context)},
    )


def promotion_analysis_prompt(context: PromotionAnalysisContext) -> str:
    return render_structured_prompt(
        "learnloop promotion analysis",
        PROMOTION_ANALYSIS_PROMPT_VERSION,
        {"task": PROMOTION_ANALYSIS_PROMPT, "context": asdict(context)},
    )
