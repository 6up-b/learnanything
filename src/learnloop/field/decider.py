"""The Decider's answer to ``learnloop field classify-questions`` (Tier 1, mvp-0.20).

The LLM classifier fills a learner question's missing metadata in one
structured call: its question type and the catalog LOs and facets it maps to.
The Decider answers the same with typed choice questions in one request: the
question type (one of ``QUESTION_TYPES``) when it is missing, and a yes/no
"does this question map to it?" per catalog LO and facet when those are
missing. Each answer is the argmax of its distribution; each is a
``judgment_ledger`` row with its probabilities. Logged metadata stays
authoritative: only the missing fields are asked.

No answer (the Decider unavailable, refused for spend or failing, or a catalog
too large for one request of at most ``MAX_QUESTIONS`` questions) hands the
question to the configured LLM classifier, whose verdict is logged against
the Decider's rows (:meth:`Classifier.log_fallback`).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from learnloop.ai.decisions import MAX_QUESTIONS, ChoiceQuestion
from learnloop.ai.review_spend import ReviewSpend
from learnloop.decider_judgments import Decision, decide_many, log_llm
from learnloop.field.signals import QUESTION_TYPES

TASK = "field_question_classification"
_FIELDS = ("lo_ids", "facets")


def questions_for(row: Mapping[str, Any], catalog: list[Mapping[str, Any]]) -> dict[str, ChoiceQuestion]:
    """The typed questions for the metadata ``row`` is missing."""

    questions: dict[str, ChoiceQuestion] = {}
    if not row.get("question_type"):
        questions["question_type"] = ChoiceQuestion(
            "Classify this learner question. Curiosity or extension is other, not confusion.",
            {kind: None for kind in sorted(QUESTION_TYPES)},
        )
    for name, candidates in (
        ("lo_ids", [str(lo["id"]) for lo in catalog]),
        ("facets", sorted({str(facet) for lo in catalog for facet in lo["facets"]})),
    ):
        if row.get(name):
            continue
        for candidate in candidates:
            questions[f"{name}:{candidate}"] = ChoiceQuestion(
                f"Does this question map to catalog {name} {candidate}? A prerequisite question maps to "
                "the prerequisite, not the current item. If uncertain choose no.",
                {"yes": None, "no": None},
            )
    return questions


class Classifier:
    """``classify_missing_questions``' Decider: one request per question, None to fall back."""

    def __init__(self, vault: Any, repository: Any, catalog: list[Mapping[str, Any]],
                 prompt: Callable[[Mapping[str, Any]], str]) -> None:
        self.vault, self.repository, self.catalog, self.prompt = vault, repository, catalog, prompt
        self.decisions: list[Decision] = []

    def __call__(self, row: Mapping[str, Any], budget: Any) -> dict[str, Any] | None:
        self.decisions = []
        questions = questions_for(row, self.catalog)
        if not questions or len(questions) > MAX_QUESTIONS:
            return None  # nothing to ask, or more than one request holds: the LLM classifies it
        # The command's caps (``budget``) admit the Decider's request too.
        spend = ReviewSpend(budget.caps, config=self.vault.config)
        spend.budget = budget
        results = decide_many(
            root=self.vault.root, config=self.vault.config, repository=self.repository, task=TASK,
            state=self.prompt(row), questions=questions, left_kind=row["event_kind"], left_id=row["id"],
            spend=spend, candidates=1,
        )
        self.decisions = list(results.values())
        if any(result.choice is None for result in results.values()):
            return None
        raw: dict[str, Any] = {
            "question_type": row.get("question_type"), "lo_ids": list(row.get("lo_ids") or []),
            "facets": list(row.get("facets") or []), "_decider": True,
            "_model": next(iter(results.values())).model,
        }
        for name, result in results.items():
            if name == "question_type":
                raw[name] = result.choice
            elif result.choice == "yes":
                field_name, candidate = name.split(":", 1)
                raw[field_name].append(candidate)
        return raw

    def log_fallback(self, raw: Mapping[str, Any], model: str) -> None:
        """The fallback LLM's answer to each question the Decider failed, as real pairs."""

        for result in self.decisions:
            if result.judgment_id is None:
                continue
            name = str(result.right_id)
            if name == "question_type":
                choice = raw.get("question_type")
            else:
                field_name, candidate = name.split(":", 1)
                choice = "yes" if candidate in (raw.get(field_name) or []) else "no"
            if choice:
                log_llm(self.repository, result, choice=str(choice), model=model)


__all__ = ["Classifier", "TASK", "questions_for"]
