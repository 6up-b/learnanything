"""The Decider's pattern-link verdicts in the offline review (Tier 1, mvp-0.20).

The LLM link judge answers every labelled link of one target in one call
(``diagnosis_link_judgment``): does the EARLIER answer show the same cause as
the CURRENT one (``same`` / ``different`` / ``not_sure``)? The Decider answers
the same question per link, one typed choice over the same blinded prompt; the
argmax decides. Only when it gives no answer for some link (unavailable,
refused for spend, failing) is the LLM asked, once, for the whole batch, as
before: its verdict decides those links and is logged against the Decider's
row of every link it judged, each a real pair for ``learnloop decider
agreement``. Diagnosis-quality and planted-cause judgments stay with the LLM.

A link the Decider already answered on the same prompt (a pass whose LLM
fallback failed, judged again on the next run) reuses that ledgered answer,
so it is never paid for twice (review F7).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from learnloop.ai.decisions import ChoiceQuestion
from learnloop.decider_judgments import Admit, Decision, decide, log_llm
from learnloop.diagnosis.offline_review.judge import LinkJudgment, LinkVerdict

#: The Tier-1 switch and Decider task of a link judgment.
LINK_TASK = "diagnosis_link_judgment"
LINK_OPTIONS = {
    "same": "The earlier answer shows the same underlying cause as the current answer",
    "different": "The causes differ",
    "not_sure": "The answers cannot establish it",
}
#: ``(judge, judge model, probabilities)`` of each label's deciding verdict.
Producers = dict[str, tuple[str, str, dict[str, float]]]


def link_question(label: str) -> ChoiceQuestion:
    return ChoiceQuestion(
        f"Do the current answer and the earlier answer {label} show the same underlying cause "
        "(the same mistake or the same prerequisite gap)? Compare causes, not correctness or surface errors.",
        dict(LINK_OPTIONS),
    )


def judge_links(
    vault: Any, repository: Any, spend: Any, prompt: str, labels: Mapping[str, str], left_id: str,
    fallback: Callable[[], LinkJudgment], *, llm_model: str, admit: Admit | None = None,
) -> tuple[LinkJudgment, Producers]:
    """The deciding verdict of every label; ``fallback()`` is the LLM's batch call."""

    links: list[LinkVerdict] = []
    producers: Producers = {}
    decisions: dict[str, Decision] = {}
    for label, cited in labels.items():
        decision = decide(
            root=vault.root, config=vault.config, repository=repository, task=LINK_TASK, state=prompt,
            question=link_question(label), left_kind="attempt", left_id=left_id,
            right_kind="attempt", right_id=cited, spend=spend, admit=admit, reuse=True,
        )
        decisions[label] = decision
        if decision.choice is not None:
            links.append(LinkVerdict(label=label, verdict=decision.choice,
                                     reason="the Decider gives no reason; its probabilities are recorded"))
            producers[label] = ("decider", decision.model, decision.probabilities)
    missing = {label for label, decision in decisions.items() if decision.choice is None}
    if missing:
        # The predecessor call, with its shared output budget, for the batch.
        verdict = fallback()
        for row in verdict.links:
            decision = decisions.get(row.label)
            if decision is None:
                continue
            if decision.judgment_id is not None:
                # The batch judged every link: each is a real pair with the Decider's row.
                log_llm(repository, decision, choice=row.verdict, model=llm_model, rationale=row.reason)
            if row.label in missing:
                links.append(row)
                producers[row.label] = ("llm", llm_model, {})
    return LinkJudgment(links=links), producers


__all__ = ["LINK_OPTIONS", "LINK_TASK", "Producers", "judge_links", "link_question"]
