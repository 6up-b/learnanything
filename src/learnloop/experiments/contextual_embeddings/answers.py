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
import json
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
    #: The arm as DELIVERED: a bounded fallback keeps its own name
    #: (``D3_fallback_d2``), never the arm it stood in for (Codex review F8).
    arm: str
    scores: list[dict[str, str]]
    final: dict[str, str] | None = None
    adjudicated: bool = False
    #: Online Reader latency: query embedding and search (retrieval arms),
    #: delivery and the tutor call, as first measured (Codex review F9).
    latency_s: float | None = None
    tutor_latency_s: float | None = None
    retrieval_latency_s: float | None = None
    #: True when the tutor answer came from a checkpoint (its latency is the
    #: original measurement; the cache condition is reported apart).
    cached: bool = False
    #: The planned arm when a fallback was delivered instead (else None).
    planned_arm: str | None = None
    delivery_receipt: dict[str, Any] | None = None

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
        "instructions": TUTOR_INSTRUCTIONS, "context": {**question.context(), "passages": passages}})
    return prompt, refs


def judge_prompt(question: BankQuestion, delivered: Delivered, answer: TutorAnswer, *, order_salt: int) -> str:
    passages = [{"ref": f"r{index}", "text": span.get("text")} for index, span in enumerate(delivered.spans, start=1)]
    shuffled = stable_order(passages, "judge-order", question.query_id, order_salt, key=lambda value: value["ref"])
    return render_structured_prompt("E0 answer judgement", pins.ROLE_PINS["judge_a"].prompt_version, {
        "instructions": JUDGE_INSTRUCTIONS,
        "context": {**question.context(), "passages": shuffled,
                    "answer": answer.answer, "cited_refs": answer.cited_refs, "abstained": answer.abstained}})


def _measured(caller: Any, fallback: float) -> tuple[float, bool]:
    last = getattr(caller, "last", None)
    if last is not None and last.latency_s is not None:
        return float(last.latency_s), bool(last.cached)
    return fallback, False


def _record(caller: Any, question: BankQuestion, arm: str, verdict: Mapping[str, str], role: str) -> None:
    record = getattr(caller, "record_judgment", None)
    if record is not None:
        passes = all(value in ("pass", "n/a") for value in verdict.values())
        record(task="e0_answer_judgement", left_id=question.query_id, right_kind="e0_arm", right_id=arm,
               verdict=json.dumps(dict(sorted(verdict.items()))), score=1.0 if passes else 0.0,
               details={"judge_role": role})


def answer_and_judge(question: BankQuestion, arm: str, delivered: Delivered, caller: Any, *,
                     retrieval_latency_s: float | None = None) -> ScoredAnswer:
    """Answer and judge one delivery. ``arm`` is what was planned; the
    record carries ``delivered.arm`` (a fallback keeps its own name) and the
    planned arm beside it. ``retrieval_latency_s``: the online query
    embedding, search and delivery time measured for this question."""

    prompt, _refs = tutor_prompt(question, delivered)
    started = time.monotonic()
    delivered_arm = delivered.arm if not arm.endswith(":D1") else arm
    answer = caller.call("tutor", prompt=prompt, result_model=TutorAnswer, arm=delivered_arm)
    tutor_latency, cached = _measured(caller, time.monotonic() - started)
    scores = []
    for salt, role in enumerate(("judge_a", "judge_b")):
        result = caller.call(role, prompt=judge_prompt(question, delivered, answer, order_salt=salt),
                             result_model=AnswerScore, arm=delivered_arm)
        scores.append(result.model_dump())
        _record(caller, question, delivered_arm, scores[-1], role)
    online = tutor_latency + (retrieval_latency_s or 0.0)
    scored = ScoredAnswer(question.query_id, delivered_arm, scores, latency_s=round(online, 4),
                          tutor_latency_s=round(tutor_latency, 4), retrieval_latency_s=retrieval_latency_s,
                          cached=cached, planned_arm=arm if delivered_arm != arm else None,
                          delivery_receipt={key: value for key, value in delivered.receipt.items()
                                            if key in ("does_not_fit", "basis", "omitted", "blocks")})
    if scores[0] == scores[1]:
        scored.final = dict(scores[0])
        return scored
    adjudicated = caller.call("judge_adjudicator", prompt=render_structured_prompt(
        "E0 answer adjudication", pins.ROLE_PINS["judge_adjudicator"].prompt_version, {
            "instructions": JUDGE_INSTRUCTIONS + " Two blinded judges disagreed; decide each criterion.",
            "context": {**question.context(),
                        "passages": [{"ref": f"r{index}", "text": span.get("text")}
                                     for index, span in enumerate(delivered.spans, start=1)],
                        "answer": answer.answer, "cited_refs": answer.cited_refs,
                        "judge_1": scores[0], "judge_2": scores[1]}}), result_model=AnswerScore, arm=delivered_arm)
    scored.final = adjudicated.model_dump()
    scored.adjudicated = True
    _record(caller, question, delivered_arm, scored.final, "judge_adjudicator")
    return scored


def summarize_answers(scored: Sequence[ScoredAnswer],
                      planned: Mapping[str, int] | None = None) -> dict[str, dict[str, Any]]:
    """Per delivered arm: the pass share and components over the answers
    made, with the PLANNED denominator beside them (``planned``: answers the
    frozen plan owes each planned arm; a fallback counts under its own name
    and as missing for the arm it stood in for: Codex review F17)."""

    by_arm: dict[str, list[ScoredAnswer]] = {}
    for item in scored:
        by_arm.setdefault(item.arm, []).append(item)
    result: dict[str, dict[str, Any]] = {}
    for arm in sorted(set(by_arm) | set(planned or {})):
        items = by_arm.get(arm, [])
        if not items:
            result[arm] = {"n": 0, "planned": int((planned or {}).get(arm, 0)),
                           "missing": int((planned or {}).get(arm, 0)), "pass": None}
            continue
        finals = [item.final for item in items if item.final is not None]

        def share(criterion: str, finals: Sequence[Mapping[str, str]] = finals) -> float | None:
            applicable = [value[criterion] for value in finals if value[criterion] != "n/a"]
            return sum(1 for value in applicable if value == "pass") / len(applicable) if applicable else None

        passed = [item.passes for item in items if item.passes is not None]
        result[arm] = {"n": len(items), "pass": sum(passed) / len(passed) if passed else None,
                       "correct": share("correct"), "assumptions": share("assumptions"),
                       "citations": share("citations"), "abstention": share("abstention"),
                       "adjudicated": sum(1 for item in items if item.adjudicated),
                       "cached_tutor_answers": sum(1 for item in items if item.cached)}
        if planned is not None and arm in planned:
            result[arm]["planned"] = int(planned[arm])
            result[arm]["missing"] = max(0, int(planned[arm]) - len(items))
    return result
