"""The blind LLM judge for the M1 arms (Slice 1 §12.1 "Who judges").

Per diagnosed attempt, one call sees the item, the answer and up to six
explanations under shuffled neutral labels (D1, D2, ...): no arm, mode, model
or id ever reaches it. It rates each explanation with the spot-check
vocabulary (right / partly / wrong / not sure), picks the best (or none) and
states a preference for each requested pair. Two passes run with the order
reversed; their agreement is reported. Cross-attempt claims are judged
separately (:class:`LinkJudgment`), with both answers side by side, so a
diagnosis is neither rewarded nor punished here for history the judge cannot
see. Planted cases get one more call that matches each arm's primary cause
against the known truth.
"""

from __future__ import annotations

import hashlib
import json
import random
from typing import Any, Literal, Mapping, Sequence

from pydantic import Field

from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import OperationClient, execute_structured_operation, render_structured_prompt
from learnloop.diagnosis.split.validation import primary_cause

JUDGE_PROMPT_VERSION = "diagnosis-review-judge-v1"
LINK_JUDGE_PROMPT_VERSION = "diagnosis-link-judge-v1"
PLANTED_JUDGE_PROMPT_VERSION = "diagnosis-planted-cause-judge-v1"
RATINGS = ("right", "partly", "wrong", "not_sure")
#: Pairs the M1 decision rule reads (§12.1): every new arm against today's
#: joint grader (a), the other modes against the default (d), and the repeat
#: of (b) against (b) for the noise floor.
PAIRS_OF_INTEREST: tuple[tuple[str, str], ...] = (
    ("a", "b"),
    ("a", "c"),
    ("a", "d"),
    ("a", "e"),
    ("b", "d"),
    ("c", "d"),
    ("e", "d"),
    ("b", "b_prime"),
)


class CandidateVerdict(WireModel):
    label: str
    rating: Literal["right", "partly", "wrong", "not_sure"]
    reason: str


class PairPreference(WireModel):
    left: str
    right: str
    preferred: Literal["left", "right", "tie"]
    reason: str


class DiagnosisJudgment(WireModel):
    analysis_md: str = Field(description="Your own reading of what went wrong in this answer, written first.")
    ratings: list[CandidateVerdict] = Field(default_factory=list)
    best: str = Field(description="The label of the best explanation, or 'none'.")
    pairs: list[PairPreference] = Field(default_factory=list)


class LinkVerdict(WireModel):
    label: str
    verdict: Literal["same", "different", "not_sure"]
    reason: str


class LinkJudgment(WireModel):
    links: list[LinkVerdict] = Field(default_factory=list)


class CauseMatch(WireModel):
    label: str
    matches: Literal["target_cause", "other_planted_cause", "neither"]
    reason: str


class PlantedCauseJudgment(WireModel):
    matches: list[CauseMatch] = Field(default_factory=list)


def judge_view(proposal: Mapping[str, Any]) -> dict[str, Any]:
    """What the judge may see of one diagnosis: content only, no ids or labels."""

    causes = []
    for event in proposal.get("event_diagnoses") or []:
        causes.append(
            {
                "causal_class": event.get("causal_class"),
                "misconception_statement": event.get("misconception_statement"),
                "candidate_causes": [
                    {"statement": cause.get("statement"), "prior_weight": cause.get("prior_weight")}
                    for cause in event.get("candidate_causes") or []
                ],
                "history_changed_cause": (event.get("history_changed_cause") or {}).get("changed"),
            }
        )
    return {
        "explanation": proposal.get("analysis_md") or "",
        "causes": causes,
        "repairs": [
            {
                "operator": repair.get("operator"),
                "rationale": repair.get("rationale"),
                "eliciting_question": repair.get("eliciting_question"),
            }
            for repair in proposal.get("repair_suggestions") or []
        ],
        "abstentions": [abstention.get("reason") for abstention in proposal.get("abstentions") or []],
    }


def assign_labels(arms: Sequence[str], *, seed: int, pass_index: int) -> dict[str, str]:
    """label -> arm. Pass 0 is a seeded shuffle; pass 1 is its reverse."""

    order = list(arms)
    random.Random(seed).shuffle(order)
    if pass_index % 2 == 1:
        order.reverse()
    return {f"D{position + 1}": arm for position, arm in enumerate(order)}


def input_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def diagnosis_judgment_prompt(
    *,
    item: Mapping[str, Any],
    learner_answer_md: str,
    labelled: Mapping[str, Mapping[str, Any]],
    pairs: Sequence[tuple[str, str]],
) -> str:
    return render_structured_prompt(
        "learnloop diagnosis review judge",
        JUDGE_PROMPT_VERSION,
        {
            "task": (
                "You are an expert tutor judging explanations of ONE learner answer. "
                "First write your own reading of what went wrong in `analysis_md`. Then "
                "rate each labelled explanation: right (it names the real cause of THIS "
                "answer's failure), partly (part right, or right but missing the main "
                "point), wrong (the cause it names is not what happened), or not_sure "
                "(the answer does not let you tell). Judge explanations of this answer "
                "only: some explanations mention the learner's earlier work, which you "
                "cannot see; neither reward nor penalize those claims. Prefer specific, "
                "checkable explanations over vague ones, but never prefer length. A "
                "repair suggestion counts only insofar as it follows from a right "
                "explanation. Pick the best label, or 'none' when none is right. For "
                "each requested pair, say which is the better explanation or 'tie'. "
                "Labels are arbitrary and their order means nothing."
            ),
            "context": {
                "item": dict(item),
                "learner_answer_md": learner_answer_md,
                "explanations": {label: dict(view) for label, view in labelled.items()},
                "requested_pairs": [{"left": left, "right": right} for left, right in pairs],
            },
        },
    )


def link_judgment_prompt(
    *,
    current: Mapping[str, Any],
    links: Mapping[str, Mapping[str, Any]],
) -> str:
    return render_structured_prompt(
        "learnloop pattern link judge",
        LINK_JUDGE_PROMPT_VERSION,
        {
            "task": (
                "Each labelled entry claims that an EARLIER answer by the same learner "
                "shows the same mistake (or the same prerequisite gap) as the CURRENT "
                "answer. Read both answers side by side. Say `same` only when the same "
                "underlying mistake visibly produced both; `different` when the earlier "
                "failure has another cause or is not a failure of this kind; `not_sure` "
                "when the text cannot settle it. Judge the answers, not the claim's "
                "wording."
            ),
            "context": {"current": dict(current), "links": {label: dict(value) for label, value in links.items()}},
        },
    )


def planted_cause_prompt(
    *,
    item: Mapping[str, Any],
    learner_answer_md: str,
    target_cause: str,
    other_causes: Sequence[str],
    labelled_causes: Mapping[str, str],
) -> str:
    return render_structured_prompt(
        "learnloop planted cause matcher",
        PLANTED_JUDGE_PROMPT_VERSION,
        {
            "task": (
                "The answer below was written to exhibit a KNOWN cause (`target_cause`). "
                "Other planted causes are listed too. For each labelled statement, say "
                "whether it names the target cause (allowing different wording), one of "
                "the other planted causes, or neither."
            ),
            "context": {
                "item": dict(item),
                "learner_answer_md": learner_answer_md,
                "target_cause": target_cause,
                "other_planted_causes": list(other_causes),
                "statements": dict(labelled_causes),
            },
        },
    )


def request_diagnosis_judgment(client: OperationClient, prompt: str) -> DiagnosisJudgment:
    return execute_structured_operation(client, purpose="diagnosis_review_judgment", prompt=prompt, result_model=DiagnosisJudgment)


def request_link_judgment(client: OperationClient, prompt: str) -> LinkJudgment:
    return execute_structured_operation(client, purpose="diagnosis_link_judgment", prompt=prompt, result_model=LinkJudgment)


def request_planted_cause_judgment(client: OperationClient, prompt: str) -> PlantedCauseJudgment:
    return execute_structured_operation(client, purpose="diagnosis_planted_cause_judgment", prompt=prompt, result_model=PlantedCauseJudgment)


def primary_statement(proposal: Mapping[str, Any]) -> str | None:
    event, cause = primary_cause(proposal)
    if cause is not None and str(cause.get("statement") or "").strip():
        return str(cause["statement"])
    if event is not None and str(event.get("misconception_statement") or "").strip():
        return str(event["misconception_statement"])
    for event in proposal.get("event_diagnoses") or []:
        if str(event.get("misconception_statement") or "").strip():
            return str(event["misconception_statement"])
    return None


def canonical_pair(left_arm: str, right_arm: str, preferred: str) -> tuple[str, str, str]:
    """Normalize a preference to the PAIRS_OF_INTEREST orientation."""

    for first, second in PAIRS_OF_INTEREST:
        if (left_arm, right_arm) == (first, second):
            return first, second, preferred
        if (left_arm, right_arm) == (second, first):
            flipped = {"left": "right", "right": "left"}.get(preferred, preferred)
            return first, second, flipped
    return left_arm, right_arm, preferred


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


__all__ = [
    "JUDGE_PROMPT_VERSION",
    "LINK_JUDGE_PROMPT_VERSION",
    "PAIRS_OF_INTEREST",
    "PLANTED_JUDGE_PROMPT_VERSION",
    "RATINGS",
    "CandidateVerdict",
    "CauseMatch",
    "DiagnosisJudgment",
    "LinkJudgment",
    "LinkVerdict",
    "PairPreference",
    "PlantedCauseJudgment",
    "assign_labels",
    "canonical_pair",
    "diagnosis_judgment_prompt",
    "input_hash",
    "judge_view",
    "link_judgment_prompt",
    "planted_cause_prompt",
    "primary_statement",
    "request_diagnosis_judgment",
    "request_link_judgment",
    "request_planted_cause_judgment",
]
