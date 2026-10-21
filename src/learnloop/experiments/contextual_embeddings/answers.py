"""Blind answer evaluation for the E0 finalists (spec §5.2, §5.3).

The same tutor route, version, effort and output policy answers every arm's
delivered context with the same permitted learner information. Two judges of
different models score each answer in two randomized orders, blinded to the
arm: correctness, preserved assumptions, citation entailment (every cited
span must support its claim) and abstention (an answer without sufficient
delivered support must say so). The primary measure is the share passing all
applicable criteria; disagreements go to the named adjudicator.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import time
from typing import Any, Literal

from pydantic import Field

from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import render_structured_prompt

from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.bank import BankQuestion, stable_order
from learnloop.experiments.contextual_embeddings.delivery import Delivered

TUTOR_INSTRUCTIONS = (
    "Answer the learner's question using only the source passages given. Cite the refs you rely on. Keep every "
    "assumption a result needs. If the passages do not support an answer, say so plainly instead of guessing."
)
JUDGE_INSTRUCTIONS = (
    "Score the answer against the passages it was given. correct: the mathematics is right. assumptions: every "
    "condition the result needs is kept. citations: each cited ref supports the claim it is cited for. "
    "abstention: if the passages cannot support an answer, the answer says so (n/a otherwise). Judge only from "
    "the passages; you do not know which system produced the answer."
)
Criterion = Literal["pass", "fail", "n/a"]


class TutorAnswer(WireModel):
    answer: str = Field(min_length=1)
    cited_refs: list[str]
    abstained: bool


class AnswerScore(WireModel):
    correct: Criterion
    assumptions: Criterion
    citations: Criterion
    abstention: Criterion


@dataclass
class ScoredAnswer:
    query_id: str
    arm: str
    scores: list[dict[str, str]]
    final: dict[str, str] | None = None
    adjudicated: bool = False
    #: The tutor answer's wall time (delivery is local; the model call dominates).
    latency_s: float | None = None

    @property
    def passes(self) -> bool | None:
        if self.final is None:
            return None
        return all(value in ("pass", "n/a") for value in self.final.values())


def tutor_prompt(question: BankQuestion, delivered: Delivered) -> tuple[str, dict[str, tuple[str, str]]]:
    refs = {f"r{index}": (str(span.get("extraction_id")), str(span.get("span_id")))
            for index, span in enumerate(delivered.spans, start=1)}
    passages = [{"ref": ref, "relation": span.get("relation"), "text": span.get("text")}
                for ref, span in zip(refs, delivered.spans, strict=True)]
    prompt = render_structured_prompt("E0 tutor answer", pins.ROLE_PINS["tutor"].prompt_version, {
        "instructions": TUTOR_INSTRUCTIONS,
        "context": {"question": question.effective_query, "history": list(question.history), "passages": passages}})
    return prompt, refs


def judge_prompt(question: BankQuestion, delivered: Delivered, answer: TutorAnswer, *, order_salt: int) -> str:
    passages = [{"ref": f"r{index}", "text": span.get("text")} for index, span in enumerate(delivered.spans, start=1)]
    shuffled = stable_order(passages, "judge-order", question.query_id, order_salt, key=lambda value: value["ref"])
    return render_structured_prompt("E0 answer judgement", pins.ROLE_PINS["judge_a"].prompt_version, {
        "instructions": JUDGE_INSTRUCTIONS,
        "context": {"question": question.effective_query, "passages": shuffled,
                    "answer": answer.answer, "cited_refs": answer.cited_refs, "abstained": answer.abstained}})


def answer_and_judge(question: BankQuestion, arm: str, delivered: Delivered, caller: Any) -> ScoredAnswer:
    prompt, _refs = tutor_prompt(question, delivered)
    started = time.monotonic()
    answer = caller.call("tutor", prompt=prompt, result_model=TutorAnswer, arm=arm)
    latency = time.monotonic() - started
    scores = []
    for salt, role in enumerate(("judge_a", "judge_b")):
        result = caller.call(role, prompt=judge_prompt(question, delivered, answer, order_salt=salt),
                             result_model=AnswerScore, arm=arm)
        scores.append(result.model_dump())
    scored = ScoredAnswer(question.query_id, arm, scores, latency_s=latency)
    if scores[0] == scores[1]:
        scored.final = dict(scores[0])
        return scored
    adjudicated = caller.call("judge_adjudicator", prompt=render_structured_prompt(
        "E0 answer adjudication", pins.ROLE_PINS["judge_adjudicator"].prompt_version, {
            "instructions": JUDGE_INSTRUCTIONS + " Two blinded judges disagreed; decide each criterion.",
            "context": {"question": question.effective_query,
                        "passages": [{"ref": f"r{index}", "text": span.get("text")}
                                     for index, span in enumerate(delivered.spans, start=1)],
                        "answer": answer.answer, "cited_refs": answer.cited_refs,
                        "judge_1": scores[0], "judge_2": scores[1]}}), result_model=AnswerScore, arm=arm)
    scored.final = adjudicated.model_dump()
    scored.adjudicated = True
    return scored


def summarize_answers(scored: Sequence[ScoredAnswer]) -> dict[str, dict[str, Any]]:
    by_arm: dict[str, list[ScoredAnswer]] = {}
    for item in scored:
        by_arm.setdefault(item.arm, []).append(item)
    result: dict[str, dict[str, Any]] = {}
    for arm, items in sorted(by_arm.items()):
        finals = [item.final for item in items if item.final is not None]

        def share(criterion: str, finals: Sequence[Mapping[str, str]] = finals) -> float | None:
            applicable = [value[criterion] for value in finals if value[criterion] != "n/a"]
            return sum(1 for value in applicable if value == "pass") / len(applicable) if applicable else None

        passed = [item.passes for item in items if item.passes is not None]
        result[arm] = {"n": len(items), "pass": sum(passed) / len(passed) if passed else None,
                       "correct": share("correct"), "assumptions": share("assumptions"),
                       "citations": share("citations"), "abstention": share("abstention"),
                       "adjudicated": sum(1 for item in items if item.adjudicated)}
    return result
