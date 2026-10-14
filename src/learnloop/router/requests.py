"""Router R2b/R2c: the two models' requests and the strict parsing of their answers.

docs/specs/plan_router_r2_v1.md §2 ("Both model requests"), spec_action_router_v1
§6.3. Each model gets the same state: the learner-state card the decision
stores (its text), the options (the top-k reversible candidates, ``stop for
today`` when the plan offers it), the similar past decisions when the
decision's inclusion coin says so (R2c), and the evidence ids the LLM may cite.

* **The Decider** (``router_qs_v1``) gets ``choose_block``, a typed
  :class:`~learnloop.ai.decisions.ChoiceQuestion` over the options.
  ``router_qs_v2`` (R2c) adds the logged-only sensors, one
  :class:`~learnloop.ai.decisions.NoulQuestion` each: ``teach_first_<lo>``
  ("does the evidence show a misunderstanding to teach before more
  practice?") and ``will_pass_next_<lo>``, for at most three learning objects
  of the options. A follow-up's restraint decision (R2c, ``plan_interrupt``) is
  its own request (``router_restraint_v1``): one ``intervene_now`` noul.
* **The LLM** (``router_llm_v1`` / ``router_llm_v2`` / ``router_llm_restraint_v1``)
  gets the same questions as one structured answer: a probability for each
  option id (renormalized by the client), at most three plain sentences of
  rationale, and the evidence ids the rationale relies on; v2 adds the sensors.

**Parsing fails closed** (:class:`RouterResponseInvalid`): an option id that
was not asked, a repeated id, a probability that is not a finite number in
[0, 1], no mass at all, a sensor for a topic that was not asked. The caller
then gives that model's weight to the staged rule (G7). The rationale is not
validated here: whether it is shown is the "why" guard's decision
(:func:`learnloop.router.why.rationale_guard`), which checks its evidence ids
against the card and the copy rules; a failed guard hides the text and keeps
the distribution.

A leaf module: the typed decision questions (pure dataclasses,
``learnloop.ai.decisions``; the only import from ``learnloop.ai``, an
import-linter exception scoped to this module), pydantic for the LLM's answer
shape, and nothing that calls a model.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import math
from typing import Any

from pydantic import BaseModel, ConfigDict

from learnloop.ai.decisions import (
    ChoiceAnswer,
    ChoiceQuestion,
    DecisionResult,
    NoulAnswer,
    NoulQuestion,
    Question,
)

PURPOSE = "router_decision"
QUESTION_SET_V1 = "router_qs_v1"
QUESTION_SET_V2 = "router_qs_v2"
RESTRAINT_QUESTION_SET = "router_restraint_v1"
LLM_SCHEMA_V1 = "router_llm_v1"
LLM_SCHEMA_V2 = "router_llm_v2"
LLM_RESTRAINT_SCHEMA = "router_llm_restraint_v1"
#: Sensors are asked for at most this many learning objects (spec §6.3).
MAX_SENSOR_LOS = 3
MAX_RATIONALE_SENTENCES = 3
CHOOSE_BLOCK = "choose_block"
INTERVENE_NOW = "intervene_now"
TEACH_FIRST = "teach_first"
WILL_PASS_NEXT = "will_pass_next"
SENSORS = (TEACH_FIRST, WILL_PASS_NEXT)
#: An option description's length (the Decider's option text stays short).
OPTION_LIMIT = 240


class RouterResponseInvalid(ValueError):
    """A model's answer broke the request's contract; that model's answer is not used."""


# -- the options and the state -------------------------------------------------------


@dataclass(frozen=True)
class BlockOption:
    """One option the models choose among: a reversible candidate, or stop for today."""

    ref: str
    description: str


@dataclass(frozen=True)
class SensorTopic:
    learning_object_id: str
    title: str


def option_description(
    *, why: str, kind: str, item_count: int, est_minutes: float, topics: Sequence[str], section: str | None = None
) -> str:
    """"Eigenvalues again, before it slips. Review: 2 questions, about 4 min (Eigenvalues)." """

    what = {"maintain": "review", "practice": "practice", "instruct": "new material"}.get(kind.split("/")[0], kind)
    if section:
        body = f"{why} Reading {section}, about {max(1, round(est_minutes))} min."
    else:
        noun = "question" if item_count == 1 else "questions"
        about = f" ({', '.join(topics)})" if topics else ""
        body = f"{why} {what.capitalize()}: {item_count} {noun}, about {max(1, round(est_minutes))} min{about}."
    text = " ".join(body.split())
    return text if len(text) <= OPTION_LIMIT else text[: OPTION_LIMIT - 1].rstrip() + "…"


STOP_DESCRIPTION = "Stop for today: today's useful time is nearly used."


@dataclass(frozen=True)
class EvidenceRef:
    """An attempt on the card the LLM may cite (``evidence_ids``)."""

    attempt_id: str
    label: str


def evidence_from_card(card_json: Mapping[str, Any] | None) -> tuple[EvidenceRef, ...]:
    """The card's citable evidence: each shown recent attempt, labelled plainly."""

    refs = []
    for entry in (card_json or {}).get("recent_work") or ():
        attempt_id = entry.get("attempt_id")
        if not attempt_id:
            continue
        result = str(entry.get("result") or "not graded").replace("_", " ")
        label = f"your answer on {entry.get('topic') or 'this topic'} on {str(entry.get('at') or '')[:10]} ({result})"
        refs.append(EvidenceRef(attempt_id=str(attempt_id), label=label))
    seen = {ref.attempt_id for ref in refs}
    for entry in ((card_json or {}).get("evidence_sections") or {}).get("teach_back_summaries") or ():
        attempt_id = entry.get("attempt_id")
        if attempt_id and str(attempt_id) not in seen:
            seen.add(str(attempt_id))
            label = f"your teach-back on {entry.get('topic') or 'this topic'} on {str(entry.get('at') or '')[:10]}"
            refs.append(EvidenceRef(attempt_id=str(attempt_id), label=label))
    return tuple(refs)


def state_text(
    card_text: str,
    options: Sequence[BlockOption],
    *,
    similar: Sequence[str] = (),
    evidence: Sequence[EvidenceRef] = (),
    extra: Sequence[str] = (),
) -> str:
    """The state both models read (the Decider's ``state``, the LLM prompt's body)."""

    lines = [card_text.rstrip(), "", "# The options"]
    lines.extend(f"- [{option.ref}] {option.description}" for option in options)
    if extra:
        lines.append("")
        lines.extend(extra)
    if similar:
        lines.append("")
        lines.append("# Similar past decisions and what followed")
        lines.extend(similar)
    if evidence:
        lines.append("")
        lines.append("# Answers you may cite (evidence ids)")
        lines.extend(f"- {ref.attempt_id}: {ref.label}" for ref in evidence)
    return "\n".join(lines) + "\n"


# -- the Decider's questions -----------------------------------------------------------

CHOOSE_INSTRUCTIONS = (
    "You are choosing the next block of study for one learner, from the options listed in the state. "
    "Pick the block that will help this learner most right now: weigh what their recent answers show, what "
    "is fragile or about to be forgotten, what is new, and the time they have left today."
)
TEACH_FIRST_INSTRUCTIONS = (
    "Does the evidence show a misunderstanding of {title} that should be taught or explained before the "
    "learner practises it more?"
)
WILL_PASS_INSTRUCTIONS = (
    "Will the learner answer their next question on {title} correctly, on their own and without hints?"
)
INTERVENE_INSTRUCTIONS = (
    "A follow-up question about {topic} came out of the learner's last answer. Would interrupting the current "
    "block to ask it now do more good than letting the learner finish the block first? (If not, the follow-up "
    "opens the next block.)"
)


def sensor_question_name(kind: str, learning_object_id: str) -> str:
    return f"{kind}_{learning_object_id}"


@dataclass(frozen=True)
class BoundaryRequest:
    """One block decision's request to both models (built once, at prefetch)."""

    options: tuple[BlockOption, ...]
    state: str
    sensors: tuple[SensorTopic, ...] = ()
    evidence: tuple[EvidenceRef, ...] = ()

    @property
    def question_set_version(self) -> str:
        return QUESTION_SET_V2 if self.sensors else QUESTION_SET_V1

    @property
    def llm_schema_version(self) -> str:
        return LLM_SCHEMA_V2 if self.sensors else LLM_SCHEMA_V1

    @property
    def refs(self) -> tuple[str, ...]:
        return tuple(option.ref for option in self.options)

    def decider_questions(self) -> dict[str, Question]:
        questions: dict[str, Question] = {
            CHOOSE_BLOCK: ChoiceQuestion(
                instructions=CHOOSE_INSTRUCTIONS,
                options={option.ref: option.description for option in self.options},
            )
        }
        for topic in self.sensors:
            questions[sensor_question_name(TEACH_FIRST, topic.learning_object_id)] = NoulQuestion(
                instructions=TEACH_FIRST_INSTRUCTIONS.format(title=topic.title)
            )
            questions[sensor_question_name(WILL_PASS_NEXT, topic.learning_object_id)] = NoulQuestion(
                instructions=WILL_PASS_INSTRUCTIONS.format(title=topic.title)
            )
        return questions

    def llm_prompt(self) -> str:
        lines = [
            "You help a study app choose what one learner does next. Read the learner's state below, then answer.",
            "",
            "1. choose_block: give a probability for each option id listed under \"The options\" (use only those "
            "ids; the probabilities need not add up exactly to 1). Put more on the block that will help this "
            "learner most right now.",
            f"2. rationale: at most {MAX_RATIONALE_SENTENCES} short sentences, addressed to the learner as \"you\", "
            "saying in plain words why the block you favour is a good next step. No numbers or probabilities, no "
            "ids, and none of the app's internal words (lane, probe, queue, facet, mastery, scheduler, candidate, "
            "decider, staged, propensity, calibration, rubric).",
            "3. evidence_ids: the ids of the answers (listed under \"Answers you may cite\") your rationale relies "
            "on; an empty list if none.",
        ]
        if self.sensors:
            lines.append(
                "4. teach_first and will_pass_next: for each topic id listed below, the probability that the "
                "evidence shows a misunderstanding to teach before more practice (teach_first), and the "
                "probability that the learner answers their next question on it correctly without hints "
                "(will_pass_next)."
            )
            lines.extend(f"   - {topic.learning_object_id}: {topic.title}" for topic in self.sensors)
        lines.extend(["", "--- the learner's state ---", self.state])
        return "\n".join(lines)


@dataclass(frozen=True)
class RestraintRequest:
    """A follow-up's restraint decision (``plan_interrupt``): one ``intervene_now`` noul."""

    topic: str
    state: str

    question_set_version: str = RESTRAINT_QUESTION_SET
    llm_schema_version: str = LLM_RESTRAINT_SCHEMA

    def decider_questions(self) -> dict[str, Question]:
        return {INTERVENE_NOW: NoulQuestion(instructions=INTERVENE_INSTRUCTIONS.format(topic=self.topic))}

    def llm_prompt(self) -> str:
        return "\n".join([
            "You help a study app decide whether to interrupt one learner. Read the learner's state below, then "
            "answer.",
            "",
            "1. intervene_now: the probability that interrupting the current block now, to ask the follow-up "
            f"question about {self.topic}, does more good than letting the learner finish the block first (the "
            "follow-up then opens the next block).",
            f"2. rationale: at most {MAX_RATIONALE_SENTENCES} short plain sentences.",
            "",
            "--- the learner's state ---",
            self.state,
        ])


# -- the LLM's answers -------------------------------------------------------------------


class _Wire(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OptionProbability(_Wire):
    id: str
    probability: float


class TopicProbability(_Wire):
    topic_id: str
    probability: float


class RouterLLMAnswerV1(_Wire):
    """``router_llm_v1``: the block distribution, a rationale and its evidence ids."""

    choose_block: list[OptionProbability]
    rationale: str
    evidence_ids: list[str]


class RouterLLMAnswerV2(RouterLLMAnswerV1):
    """``router_llm_v2`` (R2c): v1 plus the logged-only sensors."""

    teach_first: list[TopicProbability]
    will_pass_next: list[TopicProbability]


class RouterLLMRestraintAnswer(_Wire):
    """``router_llm_restraint_v1``: P(interrupt now does more good) and a rationale."""

    intervene_now: float
    rationale: str


def llm_result_model(schema_version: str) -> type[_Wire]:
    return {
        LLM_SCHEMA_V1: RouterLLMAnswerV1,
        LLM_SCHEMA_V2: RouterLLMAnswerV2,
        LLM_RESTRAINT_SCHEMA: RouterLLMRestraintAnswer,
    }[schema_version]


def _probability(value: Any, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise RouterResponseInvalid(f"{what} is not a finite number")
    if not 0.0 <= float(value) <= 1.0:
        raise RouterResponseInvalid(f"{what} is outside [0, 1]")
    return float(value)


def _as_mapping(answer: Any) -> Mapping[str, Any]:
    if isinstance(answer, BaseModel):
        return answer.model_dump()
    if isinstance(answer, Mapping):
        return answer
    raise RouterResponseInvalid("the answer is not an object")


@dataclass(frozen=True)
class ParsedChoice:
    """A model's answer to a block decision, validated."""

    #: renormalized over the asked option ids (missing ids are 0)
    distribution: Mapping[str, float]
    sensors: Mapping[str, Mapping[str, float]] = field(default_factory=dict)
    rationale: str | None = None
    evidence_ids: tuple[str, ...] = ()


def _distribution(entries: Any, refs: Sequence[str], what: str) -> dict[str, float]:
    if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)):
        raise RouterResponseInvalid(f"{what} is not a list")
    asked = set(refs)
    seen: dict[str, float] = {}
    for entry in entries:
        entry = _as_mapping(entry)
        ref = entry.get("id")
        if not isinstance(ref, str) or ref not in asked:
            raise RouterResponseInvalid(f"{what} names an option that was not asked: {ref!r}")
        if ref in seen:
            raise RouterResponseInvalid(f"{what} names {ref!r} twice")
        seen[ref] = _probability(entry.get("probability"), f"{what} probability of {ref!r}")
    total = sum(seen.values())
    if total <= 0:
        raise RouterResponseInvalid(f"{what} puts no probability on any option")
    return {ref: seen.get(ref, 0.0) / total for ref in refs}


def _sensor_answers(entries: Any, topics: Sequence[str], what: str) -> dict[str, float]:
    if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)):
        raise RouterResponseInvalid(f"{what} is not a list")
    asked = set(topics)
    out: dict[str, float] = {}
    for entry in entries:
        entry = _as_mapping(entry)
        topic = entry.get("topic_id")
        if not isinstance(topic, str) or topic not in asked:
            raise RouterResponseInvalid(f"{what} names a topic that was not asked: {topic!r}")
        if topic in out:
            raise RouterResponseInvalid(f"{what} names {topic!r} twice")
        out[topic] = _probability(entry.get("probability"), f"{what} of {topic!r}")
    return out


def parse_llm_choice(answer: Any, request: BoundaryRequest) -> ParsedChoice:
    """Validate the LLM's block answer against the request (fails closed)."""

    data = _as_mapping(answer)
    distribution = _distribution(data.get("choose_block"), request.refs, CHOOSE_BLOCK)
    sensors: dict[str, dict[str, float]] = {}
    if request.sensors:
        topics = [topic.learning_object_id for topic in request.sensors]
        for kind in SENSORS:
            sensors[kind] = _sensor_answers(data.get(kind), topics, kind)
    rationale = data.get("rationale")
    evidence = data.get("evidence_ids") or []
    if not isinstance(evidence, Sequence) or isinstance(evidence, (str, bytes)) or not all(
        isinstance(value, str) for value in evidence
    ):
        raise RouterResponseInvalid("evidence_ids is not a list of strings")
    return ParsedChoice(
        distribution=distribution,
        sensors=sensors,
        rationale=str(rationale).strip() if isinstance(rationale, str) else None,
        evidence_ids=tuple(dict.fromkeys(evidence)),
    )


def parse_decider_choice(result: DecisionResult, request: BoundaryRequest) -> ParsedChoice:
    """The Decider's typed answers (already parsed strictly by the client) for one block decision."""

    answer = result.answers.get(CHOOSE_BLOCK)
    if not isinstance(answer, ChoiceAnswer):
        raise RouterResponseInvalid("the Decider gave no choose_block answer")
    entries = [{"id": ref, "probability": probability} for ref, probability in answer.probabilities.items()]
    distribution = _distribution(entries, request.refs, CHOOSE_BLOCK)
    sensors: dict[str, dict[str, float]] = {}
    for kind in SENSORS if request.sensors else ():
        sensors[kind] = {}
        for topic in request.sensors:
            noul = result.answers.get(sensor_question_name(kind, topic.learning_object_id))
            if not isinstance(noul, NoulAnswer):
                raise RouterResponseInvalid(f"the Decider gave no {kind} answer for {topic.learning_object_id!r}")
            sensors[kind][topic.learning_object_id] = _probability(noul.p_yes, kind)
    return ParsedChoice(distribution=distribution, sensors=sensors)


def parse_llm_restraint(answer: Any) -> tuple[float, str | None]:
    data = _as_mapping(answer)
    rationale = data.get("rationale")
    return _probability(data.get(INTERVENE_NOW), INTERVENE_NOW), (str(rationale).strip() if isinstance(rationale, str) else None)


def parse_decider_restraint(result: DecisionResult) -> float:
    answer = result.answers.get(INTERVENE_NOW)
    if not isinstance(answer, NoulAnswer):
        raise RouterResponseInvalid("the Decider gave no intervene_now answer")
    return _probability(answer.p_yes, INTERVENE_NOW)


__all__ = [
    "BlockOption",
    "BoundaryRequest",
    "CHOOSE_BLOCK",
    "EvidenceRef",
    "INTERVENE_NOW",
    "LLM_RESTRAINT_SCHEMA",
    "LLM_SCHEMA_V1",
    "LLM_SCHEMA_V2",
    "MAX_RATIONALE_SENTENCES",
    "MAX_SENSOR_LOS",
    "OptionProbability",
    "PURPOSE",
    "ParsedChoice",
    "QUESTION_SET_V1",
    "QUESTION_SET_V2",
    "RESTRAINT_QUESTION_SET",
    "RestraintRequest",
    "RouterLLMAnswerV1",
    "RouterLLMAnswerV2",
    "RouterLLMRestraintAnswer",
    "RouterResponseInvalid",
    "SENSORS",
    "STOP_DESCRIPTION",
    "SensorTopic",
    "TEACH_FIRST",
    "TopicProbability",
    "WILL_PASS_NEXT",
    "evidence_from_card",
    "llm_result_model",
    "option_description",
    "parse_decider_choice",
    "parse_decider_restraint",
    "parse_llm_choice",
    "parse_llm_restraint",
    "sensor_question_name",
    "state_text",
]
