"""The judge decides; every verdict goes to ``judgment_ledger`` (Slice 2 R4, §5.8).

One isolated structured call per candidate pair. The executor is injected by
the caller, which owns spend admission (``ai.spend`` caps, a dry run that
sends nothing), the route's client and model-call receipts, so this module
stays free of any domain.

**Judge label.** The ledger's ``judge`` is the executor's (``executor.judge``,
default ``llm``): a later stage can log a second judge beside the LLM on the
same pairs, and reuse, claims and supersession are per label. Router R0's
migration 175 widened ``judgment_ledger``'s CHECK to admit ``decider``; T1's
groups read only the labels in their authority map, so a ``decider`` verdict
is logged beside the others and joins no group until the owner places it in
the authority order.

**Producer identity.** An executor names the producer it will ask
(``executor.producer``: the judge model its route resolves to) before any
call. Reuse is per producer: a pair judged by model A is not "already judged"
for model B, so changing the judge route and rerunning asks B. An explicit
``rerun`` asks the same producer again and its verdict supersedes that
producer's previous one.

**Claims.** Each question (task, producer, prompt version, input) is claimed
in a short write transaction before the call (``judgment_work_claims``); the
network call runs outside any SQLite transaction. A live lease held by another
worker skips the pair (``claimed_elsewhere``), so the sidecar and a backlog
command never pay twice for one pair; the verdict is appended only while this
worker's lease epoch still holds (completion fencing), so a worker whose
lease expired and was re-claimed cannot land a second, conflicting verdict.
Each verdict is appended in its own short transaction as soon as it returns:
a crash loses no paid verdict.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol
from uuid import uuid4

from pydantic import Field

from learnloop.ai.errors import AIInterrupted
from learnloop.ai.execution import content_key
from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendLimitExceeded
from learnloop.ai.transport import render_structured_prompt
from learnloop.clock import utc_now_iso
from learnloop.db.stores.judgment_claims import (
    CLAIMED,
    HELD,
    claim_work,
    complete_claim,
    holds_claim,
    release_claim,
)
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
#: How long a claim protects an in-flight call before another worker may take
#: it over (a crashed worker's claim expires; its late verdict is fenced out).
DEFAULT_LEASE_SECONDS = 900


class SameOrDifferent(WireModel):
    """A pairwise verdict. Three values; no score."""

    verdict: Literal["same", "different", "unsure"]
    rationale: str = Field(description="One or two sentences naming what makes them the same or different.")


#: The ``judgment_ledger.judge`` an executor writes unless it names another.
DEFAULT_JUDGE = "llm"


class Executor(Protocol):
    """One admitted, isolated structured call; ``producer`` is known before it.

    An executor may also carry ``judge`` (the ledger label of its verdicts,
    default ``llm``).
    """

    producer: str

    def __call__(self, prompt: str, result_model: type[SameOrDifferent], purpose: str) -> tuple[SameOrDifferent, str]: ...


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


def claim_key(kind: MatchKind, producer: str, input_hash: str, *, judge: str = DEFAULT_JUDGE) -> str:
    """The work item: one question to one producer under one prompt and input."""

    return content_key({"task": kind.task, "judge": judge, "producer": producer,
                        "prompt_version": kind.prompt_version, "input_hash": input_hash})


def _pair_clause(left: Subject, right: Subject) -> tuple[str, tuple[Any, ...]]:
    return (
        "((left_kind = ? AND left_id = ? AND right_kind = ? AND right_id = ?) "
        "OR (left_kind = ? AND left_id = ? AND right_kind = ? AND right_id = ?))",
        (left.kind, left.id, right.kind, right.id, right.kind, right.id, left.kind, left.id),
    )


def already_judged(
    connection: Any, kind: MatchKind, left: Subject, right: Subject, *, input_hash: str, producer: str | None,
    judge: str = DEFAULT_JUDGE,
) -> bool:
    """A verdict exists for this pair, prompt and input FROM THIS PRODUCER (and judge label).

    ``producer=None`` (a planner that cannot name the producer) matches any
    model; the judge itself always passes its producer.
    """

    clause, params = _pair_clause(left, right)
    query = (
        "SELECT 1 FROM judgment_ledger WHERE task = ? AND judge = ? AND prompt_version = ? "
        f"AND input_hash = ? AND {clause}"
    )
    values: tuple[Any, ...] = (kind.task, judge, kind.prompt_version, input_hash, *params)
    if producer is not None:
        query += " AND judge_model = ?"
        values = (*values, producer)
    return connection.execute(query + " LIMIT 1", values).fetchone() is not None


def _previous_verdict(
    connection: Any, kind: MatchKind, left: Subject, right: Subject, *, producer: str, judge: str = DEFAULT_JUDGE
) -> tuple[str, Subject, Subject] | None:
    """This producer's latest standing verdict on the pair (id, its orientation)."""

    clause, params = _pair_clause(left, right)
    row = connection.execute(
        "SELECT id, left_kind, left_id FROM judgment_ledger j WHERE task = ? AND judge = ? "
        f"AND prompt_version = ? AND judge_model = ? AND {clause} "
        "AND NOT EXISTS (SELECT 1 FROM judgment_ledger later WHERE later.supersedes_id = j.id) "
        "ORDER BY created_at DESC, rowid DESC LIMIT 1",
        (kind.task, judge, kind.prompt_version, producer, *params),
    ).fetchone()
    if row is None:
        return None
    if (str(row[1]), str(row[2])) == (left.kind, left.id):
        return str(row[0]), left, right
    return str(row[0]), right, left


@dataclass
class JudgedPair:
    left: Subject
    right: Subject
    #: judged | already_judged | claimed_elsewhere | fenced | failed | not_run
    status: str
    verdict: str | None = None
    rationale: str | None = None
    judgment_id: str | None = None
    judge_model: str | None = None
    score: float | None = None
    error: str | None = None
    supersedes_id: str | None = None

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
            "supersedes_id": self.supersedes_id,
        }


def judge_pairs(
    repository: Any,
    kind: MatchKind,
    pairs: Sequence[CandidatePair],
    *,
    execute: Callable[..., Any],
    producer: str | None = None,
    judge: str | None = None,
    rerun: bool = False,
    stop_on: tuple[type[BaseException], ...] = (SpendLimitExceeded, AIInterrupted),
    lease_seconds: int = DEFAULT_LEASE_SECONDS,
    now: Callable[[], str] = utc_now_iso,
) -> list[JudgedPair]:
    """Judge each pair once per producer; stop (leaving the rest ``not_run``) on spend or cancel.

    Any other failure marks that pair ``failed`` (its claim released) and
    moves on: an unjudged pair merges nothing and is picked up by the next run.
    """

    producer = str(producer or getattr(execute, "producer", "") or "")
    if not producer:
        raise ValueError("judge_pairs needs the producer (the judge model) before any call")
    label = str(judge or getattr(execute, "judge", None) or DEFAULT_JUDGE)
    owner = f"judge:{uuid4().hex}"
    results: list[JudgedPair] = []
    stopped: str | None = None
    for pair in pairs:
        left, right = pair.left, pair.right
        if stopped is not None:
            results.append(JudgedPair(left, right, "not_run", score=pair.score, error=stopped))
            continue
        input_hash = pair_input_hash(kind, left, right)
        key = claim_key(kind, producer, input_hash, judge=label)
        with repository.atomic():
            connection = repository.connection()
            if not rerun and already_judged(
                connection, kind, left, right, input_hash=input_hash, producer=producer, judge=label
            ):
                status, epoch = "already_judged", None
            else:
                status, epoch = claim_work(
                    connection, claim_key=key, task=kind.task, producer=producer, prompt_version=kind.prompt_version,
                    input_hash=input_hash, owner=owner, now=now(), lease_seconds=lease_seconds, rerun=rerun,
                )
        if status == HELD:
            results.append(JudgedPair(left, right, "claimed_elsewhere", score=pair.score))
            continue
        if status != CLAIMED or epoch is None:
            results.append(JudgedPair(left, right, "already_judged", score=pair.score))
            continue
        try:
            # Outside any transaction: the claim, not a lock, keeps others off it.
            outcome = execute(pair_prompt(kind, left, right), SameOrDifferent, kind.purpose)
        except stop_on as exc:
            stopped = type(exc).__name__
            _release(repository, key, owner, epoch, now)
            results.append(JudgedPair(left, right, "not_run", score=pair.score, error=stopped))
            continue
        except Exception as exc:  # noqa: BLE001 - one failed pair never stops the batch
            _release(repository, key, owner, epoch, now)
            results.append(JudgedPair(left, right, "failed", score=pair.score, error=type(exc).__name__))
            continue
        verdict = outcome[0] if isinstance(outcome, tuple) else outcome
        rationale = str(verdict.rationale or "").strip()[:1000]
        judgment_id: str | None = None
        supersedes: str | None = None
        with repository.atomic():
            connection = repository.connection()
            if holds_claim(connection, claim_key=key, owner=owner, epoch=epoch):
                first, second = left, right
                if rerun:
                    previous = _previous_verdict(connection, kind, left, right, producer=producer, judge=label)
                    if previous is not None:
                        supersedes, first, second = previous
                judgment_id = append_judgment(
                    connection,
                    task=kind.task,
                    left_kind=first.kind,
                    left_id=first.id,
                    right_kind=second.kind,
                    right_id=second.id,
                    judge=label,
                    judge_model=producer,
                    prompt_version=kind.prompt_version,
                    input_hash=input_hash,
                    verdict=verdict.verdict,
                    rationale=rationale,
                    supersedes_id=supersedes,
                )
                complete_claim(connection, claim_key=key, owner=owner, epoch=epoch, judgment_id=judgment_id, now=now())
        if judgment_id is None:
            # Our lease expired and another worker re-claimed the question:
            # its verdict is the one that counts; ours is never appended.
            results.append(JudgedPair(left, right, "fenced", verdict=verdict.verdict, judge_model=producer,
                                      score=pair.score, error="lease_lost"))
            continue
        results.append(
            JudgedPair(
                left, right, "judged", verdict=verdict.verdict, rationale=rationale, judgment_id=judgment_id,
                judge_model=producer, score=pair.score, supersedes_id=supersedes,
            )
        )
    return results


def _release(repository: Any, key: str, owner: str, epoch: int, now: Callable[[], str]) -> None:
    try:
        with repository.atomic():
            release_claim(repository.connection(), claim_key=key, owner=owner, epoch=epoch, now=now())
    except Exception:  # noqa: BLE001 - an unreleased claim simply expires
        pass


__all__ = [
    "DEFAULT_JUDGE",
    "DEFAULT_LEASE_SECONDS",
    "Executor",
    "JudgedPair",
    "SameOrDifferent",
    "already_judged",
    "claim_key",
    "judge_pairs",
    "ordered",
    "pair_input_hash",
    "pair_prompt",
]
