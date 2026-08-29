"""Structured AI contracts owned by diagnosis and probe features."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Mapping

from pydantic import Field

from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import prompt_safe, render_structured_prompt
from learnloop.attempts.ai_contracts import GRADING_PROMPT_VERSION


@dataclass(frozen=True)
class MisconceptionMatchContext:
    statement: str
    learning_object_id: str
    candidates: list[dict[str, str]]


@dataclass(frozen=True)
class ProbeInstanceContext:
    family_template_id: str
    family_template_version: int
    instrument_kind: str
    measurement_intent: str
    learning_object_id: str
    learning_object_title: str
    learning_object_concept: str
    learning_object_summary: str
    target_facets: list[str] = field(default_factory=list)
    confusable_concept: str | None = None
    observation_alphabet: list[str] = field(default_factory=list)
    count: int = 2
    existing_prompts: list[str] = field(default_factory=list)
    existing_surface_families: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProbeDialogueTurnContext:
    turn_kind: str
    turn_number: int
    planned_turns: int
    learning_object_id: str
    learning_object_title: str
    learning_object_concept: str
    learning_object_summary: str
    target_facets: list[str] = field(default_factory=list)
    confusable_concept: str | None = None
    prior_turns: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class ProbeFamilyTrialsContext:
    family_template_id: str
    family_template_version: int
    instrument_kind: str
    measurement_intent: str
    learning_object_title: str
    learning_object_summary: str
    target_facets: list[str] = field(default_factory=list)
    confusable_concept: str | None = None
    hypothesis_slots: list[str] = field(default_factory=list)
    observation_alphabet: list[str] = field(default_factory=list)
    non_applicable_controls: list[str] = field(default_factory=list)
    surfaces: list[dict] = field(default_factory=list)
    trials_per_hypothesis: int = 3


class MisconceptionMatch(WireModel):
    decision: Literal["same", "new"]
    misconception_id: str | None = None


class DiagnosticTrialResult(WireModel):
    answer: str
    fires: bool


class DiagnosticTrials(WireModel):
    planted: list[DiagnosticTrialResult] = Field(default_factory=list)
    clean: list[DiagnosticTrialResult] = Field(default_factory=list)


class DiagnosticFireJudgment(WireModel):
    fires: bool = False
    rationale: str = ""


class ProbeInstanceSurface(WireModel):
    surface_suffix: str
    prompt_md: str
    expected_answer_md: str


class ProbeInstanceSurfaces(WireModel):
    surfaces: list[ProbeInstanceSurface] = Field(default_factory=list)


class ProbeDialogueTurn(WireModel):
    prompt_md: str
    expected_answer_md: str


class ProbeFamilyTrial(WireModel):
    hypothesis_slot: str
    answer: str
    matched_outcome: str
    non_applicable_control: bool = False


class ProbeFamilyTrials(WireModel):
    trials: list[ProbeFamilyTrial] = Field(default_factory=list)


MISCONCEPTION_MATCH_PROMPT_VERSION = "mvp-0.5-misconception-match"
DIAGNOSTIC_TRIALS_PROMPT_VERSION = "mvp-0.5-diagnostic-trials"
PROBE_INSTANCE_PROMPT_VERSION = "mvp-0.6-probe-instance-surfaces-natural-wording"
PROBE_DIALOGUE_TURN_PROMPT_VERSION = "mvp-0.6-probe-dialogue-turn"
PROBE_FAMILY_TRIALS_PROMPT_VERSION = "mvp-0.6-probe-family-trials"

PROBE_INSTANCE_PROMPT = """\
Generate `count` surface-varied diagnostic Item Instances for ONE probe family \
binding. The family template (`measurement_intent`) defines the measurement \
pattern; you supply only the surfaces: prompt wording, values/entities, and the \
expected answer. Every surface must satisfy ALL of these constraints (spec §9.4):

1. Honor the measurement pattern exactly: a `minimal_recall` surface asks for \
the idea itself; a `prediction_before_computation` surface demands a committed \
prediction plus the decisive reason BEFORE any computation; a `contrast` surface \
forces a choice between the target and `confusable_concept`; a `perturbation` \
surface shifts the familiar framing; a `minimal_counterexample` surface asks \
where the idea fails; long-form kinds ask for the full structured artifact.
2. Ground every prompt in the Learning Object (`learning_object_title`, \
`learning_object_summary`) and make it mention the target concept or a target \
facet by name — an ungrounded prompt fails the structural gate.
3. Never cue the hypothesis: the prompt must not hint at the expected answer, \
name the misconception, or telegraph which response would be "the trap". A \
learner holding each competing state must find the surface equally natural.
4. No answer leakage: `expected_answer_md` must never appear in, or be \
trivially derivable from, `prompt_md`.
5. Vary surfaces genuinely: different values, entities, representations, or \
framings — not the same question re-worded. `surface_suffix` is a short \
snake_case id unique within the batch, and each surface must differ from every \
prompt in `existing_prompts` and every family in `existing_surface_families`.
6. `expected_answer_md` states what a robust learner would actually answer, \
concisely, with the decisive reason — it is the grading anchor, not prose.
7. Write learner-facing prose. Never expose internal snake_case identifiers \
(facet ids, concept slugs) or meta-language like "the Learning Object" or \
"the target facet" in `prompt_md` — describe the idea in natural words. Weave \
the title in naturally (quoted is fine); the structural gate requires the \
title, concept, or a target facet to appear somewhere in the prompt.
"""

PROBE_DIALOGUE_TURN_PROMPT = """\
Generate ONE dialogue microprobe turn of kind `turn_kind` for a short \
diagnostic block (spec §8.1). `prior_turns` holds the block so far as \
{kind, prompt_md, learner_answer_md}; condition on it:

- `commit`: ask the learner to commit to a short, unhedged answer or \
prediction about the target idea. No sub-questions, no scaffolding.
- `reason`: ask for the single decisive reason behind THEIR committed answer \
(quote or paraphrase what they actually committed to — not a generic "explain \
the concept").
- `counterfactual`: minimally change THEIR committed case (one assumption, \
value, or condition) and ask whether their answer still holds and why.
- `counterexample`: ask for one boundary condition or failure case for THEIR \
answer as they stated it.

Hard constraints:
1. MEASUREMENT ONLY: never teach, hint, correct, reframe toward the answer, \
or reveal whether any prior answer was right or wrong. Do not react to \
mistakes — probe them neutrally.
2. Answerable in one or two sentences; one question only.
3. Learner-facing prose: no internal snake_case identifiers or meta-language; \
mention the topic naturally (the structural gate requires the title, concept, \
or a target facet to appear in the prompt).
4. No answer leakage: `expected_answer_md` (what a robust learner would say, \
with the decisive reason — the grading anchor) must not be derivable from \
`prompt_md`.
5. If `prior_turns` is empty (a `commit` turn), ground the question in the \
Learning Object summary alone.
"""

PROBE_FAMILY_TRIALS_PROMPT = """\
Role-play planted learner states for ONE probe family admission gate (spec \
§9.6). For EACH hypothesis slot in `hypothesis_slots` produce \
`trials_per_hypothesis` DISTINCT simulated learner responses to the given \
surfaces (`surfaces` lists {surface_suffix, prompt_md, expected_answer_md}; \
rotate through them so trials cover more than one surface):

- A learner in state `robust_target` (or the family's robust slot) answers \
correctly with a decisive reason, in natural varied phrasing.
- A learner in `confuses_with_neighbor` GENUINELY holds the confusable belief \
and answers consistently with the neighbor concept — never a caricature.
- A learner in `surface_only` reproduces familiar surface wording but breaks \
on shifted framings; `unfamiliar` hedges, answers vaguely, or declines.
- `other_or_unknown` shows a systematic but UNLISTED error pattern.

For each trial set `matched_outcome` to the outcome class from \
`observation_alphabet` that a careful grader would assign to that response — \
judge the response as written, do NOT just echo the planted slot's expected \
signature. If `non_applicable_controls` is non-empty, additionally produce one \
trial per control with `non_applicable_control` = true: a scenario where the \
family's trigger conditions do NOT hold, answered by a learner holding the \
planted state — a sound family must NOT fire a signature outcome there. Keep \
every `answer` under 60 words.
"""


def misconception_match_prompt(context: MisconceptionMatchContext) -> str:
    return render_structured_prompt(
        "learnloop misconception match",
        MISCONCEPTION_MATCH_PROMPT_VERSION,
        {
            "task": (
                "Decide whether the learner belief in `statement` is the SAME "
                "underlying misconception as one of the `candidates` (return "
                "decision 'same' with that candidate's misconception_id) or a "
                "genuinely DISTINCT belief (return decision 'new'). Compare the "
                "beliefs themselves, never their error-type labels. When unsure, "
                "prefer 'new'."
            ),
            "statement": context.statement,
            "learning_object_id": context.learning_object_id,
            "candidates": context.candidates,
        },
    )


def diagnostic_trials_prompt(context: Any) -> str:
    def _get(key: str, default: Any = None) -> Any:
        if isinstance(context, Mapping):
            return context.get(key, default)
        return getattr(context, key, default)

    n_trials = int(_get("n_trials", 0) or 0)
    max_words = int(_get("max_answer_words", 40) or 40)
    return render_structured_prompt(
        "learnloop diagnostic trials",
        DIAGNOSTIC_TRIALS_PROMPT_VERSION,
        {
            "task": (
                f"Role-play {n_trials} DISTINCT `planted` students who GENUINELY "
                "HOLD the belief in `misconception_statement` and answer "
                "`item_prompt` accordingly (natural, varied phrasing — NEVER copy "
                "`misconception_consistent_answer` verbatim), and "
                f"{n_trials} DISTINCT `clean` students who are competent (correct "
                "substance; wording may vary or carry minor slips). For EACH "
                "answer set `fires` = true iff a grader would attribute the "
                "misconception-keyed fatal error described in `keyed_fatal_errors` "
                "— i.e. the answer is substantively consistent with the belief AND "
                f"categorically wrong. Keep every `answer` <= {max_words} words."
            ),
            "n_trials": n_trials,
            "max_answer_words": max_words,
            "item_prompt": _get("item_prompt", ""),
            "expected_answer": _get("expected_answer", ""),
            "misconception_statement": _get("misconception_statement", ""),
            "misconception_consistent_answer": _get("misconception_consistent_answer", ""),
            "keyed_fatal_errors": _get("keyed_fatal_errors", []),
        },
    )


def diagnostic_fire_prompt(context: Mapping[str, Any]) -> str:
    return render_structured_prompt(
        "learnloop diagnostic fire judgment",
        GRADING_PROMPT_VERSION,
        {
            "task": (
                "Decide whether the candidate answer exhibits the diagnostic failure "
                "described by the supplied item/misconception context. Return fires=true "
                "only when the answer semantically triggers that failure; a correct or "
                "meaning-equivalent answer returns false. This is an in-memory simulation "
                "judgment and must not invent an attempt or grading evidence."
            ),
            "context": {key: prompt_safe(value) for key, value in context.items()},
        },
    )


def probe_instance_surfaces_prompt(context: ProbeInstanceContext) -> str:
    return render_structured_prompt(
        "learnloop probe instance surfaces",
        PROBE_INSTANCE_PROMPT_VERSION,
        {"task": PROBE_INSTANCE_PROMPT, "context": asdict(context)},
    )


def probe_dialogue_turn_prompt(context: ProbeDialogueTurnContext) -> str:
    return render_structured_prompt(
        "learnloop probe dialogue turn",
        PROBE_DIALOGUE_TURN_PROMPT_VERSION,
        {"task": PROBE_DIALOGUE_TURN_PROMPT, "context": asdict(context)},
    )


def probe_family_trials_prompt(context: ProbeFamilyTrialsContext) -> str:
    return render_structured_prompt(
        "learnloop probe family trials",
        PROBE_FAMILY_TRIALS_PROMPT_VERSION,
        {"task": PROBE_FAMILY_TRIALS_PROMPT, "context": asdict(context)},
    )
