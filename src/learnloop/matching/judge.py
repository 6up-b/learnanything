"""The judge decides; every verdict goes to ``judgment_ledger`` (Slice 2 R4, §5.8).

One isolated structured call per candidate pair. The executor is injected by
the caller, which owns spend admission (``ai.spend`` caps, a dry run that
sends nothing), the route's client and model-call receipts, so this module
stays free of any domain. Each verdict is appended in its own short
transaction as soon as it returns: a crash loses no paid verdict, and a rerun
skips every pair already judged under the same prompt version and input.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import Field

from learnloop.ai.errors import AIInterrupted
from learnloop.ai.execution import content_key
from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendLimitExceeded
from learnloop.ai.transport import render_structured_prompt
from learnloop.db.stores.judgments import append_judgment
from learnloop.matching.kinds import MatchKind, Subject
from learnloop.matching.shortlist import CandidatePair

_COMMON_RULES = (
    "You are an independent judge. You see two items, `first` and `second`, in "
    "no meaningful order. Decide only the question asked. Answer `same`, "
    "`different` or `unsure`, then give a one- or two-sentence rationale that "
    "names what makes them the same or different. Use `unsure` when the text "
    "cannot settle it; never guess."
)


class SameOrDifferent(WireModel):
    """A pairwise verdict. Three values; no score."""

    verdict: Literal["same", "different", "unsure"]
    rationale: str = Field(description="One or two sentences naming what makes them the same or different.")


#: (prompt, result model, purpose) -> (validated result, the model that answered).
Executor = Callable[[str, type[SameOrDifferent], str], tuple[SameOrDifferent, str]]


def ordered(left: Subject, right: Subject) -> tuple[Subject, Subject]:
    """A presentation order that depends on ids only, never on rank."""

    return (left, right) if content_key([left.kind, left.id]) <= content_key([right.kind, right.id]) else (right, left)


def pair_prompt(kind: MatchKind, left: Subject, right: Subject) -> str:
    first, second = ordered(left, right)
    return render_structured_prompt(
        f"learnloop {kind.name} judge",
        kind.prompt_version,
        {
            "task": f"{_COMMON_RULES} Question: {kind.question} {kind.guidance}",
            "context": {"first": dict(kind.render(first)), "second": dict(kind.render(second))},
        },
    )


def pair_input_hash(kind: MatchKind, left: Subject, right: Subject) -> str:
    """The exact input a verdict was given: both subjects' content, unordered."""

    first, second = ordered(left, right)
    return content_key(
        {
            "task": kind.task,
            "prompt_version": kind.prompt_version,
            "subjects": [
                [first.kind, first.id, first.content_hash, dict(kind.render(first))],
                [second.kind, second.id, second.content_hash, dict(kind.render(second))],
            ],
        }
    )


def already_judged(connection: Any, kind: MatchKind, left: Subject, right: Subject, *, input_hash: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM judgment_ledger WHERE task = ? AND judge = 'llm' AND prompt_version = ? "
        "AND input_hash = ? AND ((left_kind = ? AND left_id = ? AND right_kind = ? AND right_id = ?) "
        "OR (left_kind = ? AND left_id = ? AND right_kind = ? AND right_id = ?)) LIMIT 1",
        (
            kind.task, kind.prompt_version, input_hash,
            left.kind, left.id, right.kind, right.id,
            right.kind, right.id, left.kind, left.id,
        ),
    ).fetchone()
    return row is not None


@dataclass
class JudgedPair:
    left: Subject
    right: Subject
    status: str  # judged | already_judged | failed | not_run
    verdict: str | None = None
    rationale: str | None = None
    judgment_id: str | None = None
    judge_model: str | None = None
    score: float | None = None
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "left": [self.left.kind, self.left.id],
            "right": [self.right.kind, self.right.id],
            "status": self.status,
            "verdict": self.verdict,
            "judgment_id": self.judgment_id,
            "judge_model": self.judge_model,
            "shortlist_score": self.score,
            "error": self.error,
        }


def judge_pairs(
    repository: Any,
    kind: MatchKind,
    pairs: Sequence[CandidatePair],
    *,
    execute: Executor,
    stop_on: tuple[type[BaseException], ...] = (SpendLimitExceeded, AIInterrupted),
) -> list[JudgedPair]:
    """Judge each pair once; stop (leaving the rest ``not_run``) on spend or cancel.

    Any other failure marks that pair ``failed`` and moves on: an unjudged
    pair merges nothing and is picked up by the next run.
    """

    results: list[JudgedPair] = []
    stopped: str | None = None
    for pair in pairs:
        left, right = pair.left, pair.right
        if stopped is not None:
            results.append(JudgedPair(left, right, "not_run", score=pair.score, error=stopped))
            continue
        input_hash = pair_input_hash(kind, left, right)
        with repository.connection() as connection:
            if already_judged(connection, kind, left, right, input_hash=input_hash):
                results.append(JudgedPair(left, right, "already_judged", score=pair.score))
                continue
        try:
            verdict, model = execute(pair_prompt(kind, left, right), SameOrDifferent, kind.purpose)
        except stop_on as exc:
            stopped = type(exc).__name__
            results.append(JudgedPair(left, right, "not_run", score=pair.score, error=stopped))
            continue
        except Exception as exc:  # noqa: BLE001 - one failed pair never stops the batch
            results.append(JudgedPair(left, right, "failed", score=pair.score, error=type(exc).__name__))
            continue
        rationale = str(verdict.rationale or "").strip()[:1000]
        with repository.atomic():
            judgment_id = append_judgment(
                repository.connection(),
                task=kind.task,
                left_kind=left.kind,
                left_id=left.id,
                right_kind=right.kind,
                right_id=right.id,
                judge="llm",
                judge_model=str(model or "unknown"),
                prompt_version=kind.prompt_version,
                input_hash=input_hash,
                verdict=verdict.verdict,
                rationale=rationale,
            )
        results.append(
            JudgedPair(
                left, right, "judged", verdict=verdict.verdict, rationale=rationale,
                judgment_id=judgment_id, judge_model=str(model or "unknown"), score=pair.score,
            )
        )
    return results


__all__ = [
    "Executor",
    "JudgedPair",
    "SameOrDifferent",
    "already_judged",
    "judge_pairs",
    "ordered",
    "pair_input_hash",
    "pair_prompt",
]
