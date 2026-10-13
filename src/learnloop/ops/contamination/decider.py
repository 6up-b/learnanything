"""The Decider's leak / reveal verdict (Tier 1, mvp-0.22).

The same two-text question the LLM judge is asked (the request's rendered
prompt), as one typed choice: the task's positive verdict (``leak`` or
``reveal``), ``clean`` or ``unsure``. The argmax decides. A verdict is
ledgered under the request's own checkpoint id, so the report reads it as it
reads the LLM's and a rerun never pays for it again; a Decider with no answer
(unavailable, refused for spend, failing) leaves the request to the LLM judge,
and its failure row (another id) pairs with the LLM's verdict in ``learnloop
decider agreement``.
"""

from __future__ import annotations

from typing import Any

from learnloop.ai.decisions import ChoiceQuestion
from learnloop.ai.execution import content_key
from learnloop.ai.review_spend import ReviewSpend
from learnloop.decider_judgments import decide
from learnloop.ops.contamination.judge import OPERATIONS, JudgeRequest, ledger_verdict


def question(task: str) -> ChoiceQuestion:
    return ChoiceQuestion(
        "Apply the contamination instructions to these two texts. Sharing a topic or a general technique "
        "is clean; use unsure when the texts cannot settle it.",
        {ledger_verdict(task, "contaminated"): "Contaminated: it exposes the protected question or answer",
         "clean": None, "unsure": None},
    )


def judge(vault: Any, repository: Any, request: JudgeRequest, budget: Any, *, run_id: str,
          candidates: int = 0, pairs: int = 0) -> bool:
    """Ledger the Decider's verdict for ``request``; False hands it to the LLM judge."""

    spend = ReviewSpend(budget.caps, config=vault.config)
    spend.budget = budget  # the report's caps admit the Decider's request too
    # Its receipt belongs to the report's run, as the LLM judge's do.
    spend.collector.sink = lambda action, event: repository.record_model_event(
        action, event, owner_kind="contamination_report", owner_id=run_id)
    candidate = request.candidate
    decision = decide(
        root=vault.root, config=vault.config, repository=repository, task=OPERATIONS[candidate.task],
        ledger_task=candidate.task, state=request.prompt, question=question(candidate.task),
        left_kind=candidate.left_kind, left_id=candidate.left_id,
        right_kind=candidate.right_kind, right_id=candidate.right_id,
        input_hash=content_key({"prompt": request.prompt}), spend=spend, candidates=candidates, pairs=pairs,
        judgment_id=request.judgment_id,
        rationale={"detector": candidate.detector, "pass": request.pass_index, "run_id": run_id,
                   "result": {"rationale": "the Decider gives no rationale; its probabilities are recorded",
                              "revealed": ""}},
    )
    return decision.choice is not None


__all__ = ["judge", "question"]
