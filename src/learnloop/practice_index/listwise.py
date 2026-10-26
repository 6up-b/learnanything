"""One listwise LLM judge for every live rerank (Phase 5b; shared with Slice 2 T6).

A live rerank sends one prompt listing a pool of candidates (``c1``.., ``p1``..),
and the model judges every candidate and picks the best few. The pieces are the
same whatever the candidates are (practice items for ``find_practice``, source
spans for the tutor's grounding), so they live here once:

* **skip check** before any client is built: no route, or a metered route
  without a price, is skipped with a label, never guessed;
* **request identity**: an input hash over the exact prompt, schema, model and
  output budget, and one ``judgment_ledger`` id per candidate derived from it;
* **ledger-served cache**: the same request over the same pool is answered
  from the ledger without a call;
* **one capped call and one retry** through ``PaidCalls`` (checkpointed,
  receipted, under ``SpendBudget`` caps), optionally inside a time box;
* **pick filtering** (unknown refs, duplicates, verdicts that may not be
  picked) and **append-only verdicts**, each with its pick rank.

Callers supply what differs: the route task, ledger task and kinds, the id
prefix, the result model and its verdict field, the score map, the price and
caps, and how candidates are rendered into the prompt. Never raises for a
provider, budget or interruption failure: the outcome carries a status.
"""
from __future__ import annotations

from collections.abc import Callable, Hashable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
import json
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from learnloop.ai.errors import AIInterrupted, AIInvalidOutput, AIProviderUnavailable
from learnloop.ai.execution import content_key
from learnloop.ai.routing import AITask
from learnloop.ai.spend import SpendBudget, SpendCaps, SpendEstimate, SpendLimitExceeded
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.judgments import append_judgment
from learnloop.db.stores.practice_index import judgments_by_ids
from learnloop.practice_index.paid import PaidCalls, PaidRoute, plan_route, resolve_client, transport_problem
from learnloop.vault.models import LoadedVault

Key = TypeVar("Key", bound=Hashable)


@dataclass(frozen=True)
class ListwiseTask:
    """What one kind of listwise rerank writes and how it is routed and priced."""

    route_task: AITask
    ledger_task: str
    left_kind: str
    right_kind: str
    id_prefix: str
    prompt_version: str
    #: None (the default since 2026-10-12): the route's output budget under the
    #: shared policy (``PaidRoute.output_tokens``); an int pins a budget.
    output_tokens: int | None
    result_model: type[BaseModel]
    #: The judgment field holding the verdict (``relevance``, ``verdict``).
    verdict_field: str
    scores: Mapping[str, float]
    #: The config key the skip message names (``practice_index.rerank_price_per_million``).
    price_setting: str
    #: Inserted before "route" in the skip message ("rerank " gives "metered rerank route").
    route_label: str = ""
    #: A pick whose own verdict is one of these is not kept (T6: ``unrelated``).
    drop_pick_verdicts: frozenset[str] = frozenset()
    #: Further judgment fields recorded in each ledger row's rationale (RW5b:
    #: the organizer's ``explorable``), so every verdict the call returns is
    #: in ``judgment_ledger``. Empty: the rationale is ``text`` and ``pick_rank``.
    ledger_fields: tuple[str, ...] = ()


@dataclass
class ListwiseOutcome(Generic[Key]):
    """``status``: ``empty_pool``, a skip label, ``unavailable``, ``cached``,
    ``judged``, ``cancelled``, ``over_budget`` or ``failed`` (``reason`` says why)."""

    status: str
    reason: str | None = None
    picks: list[Key] = field(default_factory=list)
    rows: dict[Key, Mapping[str, Any]] = field(default_factory=dict)
    model: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)

    @property
    def judged(self) -> bool:
        return self.status in {"cached", "judged"}


def route_skip(route: PaidRoute, price: float | None, *, injected: bool,
               price_setting: str, route_label: str = "") -> str | None:
    """Why a live paid step is skipped before any client is built, or None."""

    if not injected and not route.available:
        return f"unavailable: no provider routed for {route.task}"
    if route.billing == "metered" and price is None:
        return f"skipped: metered {route_label}route without {price_setting}"
    return None


def listwise_caps(pool_size: int, *, max_total_tokens: int, max_estimated_usd: float | None) -> SpendCaps:
    """One request and at most one retry, every candidate judged once."""

    return SpendCaps(max_candidates=pool_size, max_pairs=pool_size, max_retries=1, max_calls=2,
                     max_total_tokens=max_total_tokens, max_estimated_usd=max_estimated_usd)


def task_output_tokens(task: ListwiseTask, route: PaidRoute) -> int:
    """The rerank's output budget: the task's pinned one, else the route's policy budget."""

    return task.output_tokens if task.output_tokens is not None else route.output_tokens


def request_input_hash(task: ListwiseTask, route: PaidRoute, prompt: str) -> str:
    identity: dict[str, Any] = {"prompt": prompt, "schema": task.result_model.model_json_schema(),
                                "model": route.model or "unspecified",
                                "output_tokens": task_output_tokens(task, route)}
    if route.reasoning_effort:
        identity["reasoning_effort"] = route.reasoning_effort
    return content_key(identity)


def ledger_ids(task: ListwiseTask, input_hash: str, keys: Sequence[Key],
               id_parts: Callable[[Key], Sequence[str]]) -> dict[Key, str]:
    """One ``judgment_ledger`` id per candidate, derived from the exact request."""

    return {key: task.id_prefix + content_key([input_hash, *id_parts(key)])[:40] for key in keys}


def validate_all_judged(result: Any, refs: Mapping[str, Any]) -> Any:
    # Every candidate must be judged: the verdicts are written once, append-only,
    # under ids derived from this exact request, so a partial answer could never
    # be completed later. A partial answer is retried, then reported unjudged.
    if {judgment.ref for judgment in result.judgments} >= set(refs):
        return result
    raise AIInvalidOutput(f"The {type(result).__name__} did not judge every candidate")


def from_ledger(task: ListwiseTask, keys: Sequence[Key], ids: Mapping[Key, str],
                rows: Mapping[str, Mapping[str, Any]], status: str,
                pick_at_most: int) -> ListwiseOutcome[Key]:
    """The outcome a set of ledger rows describes: verdict rows and picks by rank."""

    found: dict[Key, Mapping[str, Any]] = {}
    ranked: list[tuple[int, int, Key]] = []
    model = None
    for position, key in enumerate(keys):
        row = rows.get(ids[key])
        if row is None:
            continue
        found[key] = row
        model = row["judge_model"]
        details = json.loads(row["rationale"] or "{}")
        if details.get("pick_rank") and row["verdict"] not in task.drop_pick_verdicts:
            ranked.append((int(details["pick_rank"]), position, key))
    picks = [key for _rank, _position, key in sorted(ranked, key=lambda entry: entry[:2])][:pick_at_most]
    return ListwiseOutcome(status, picks=picks, rows=found, model=model)


def _jsonable(value: Any) -> Any:
    """A recorded judgment field as JSON (a nested model, or a list of them, dumped)."""

    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, (list, tuple)):
        return [_jsonable(entry) for entry in value]
    return value


def judge_listwise(
    vault: LoadedVault,
    repository: Repository,
    task: ListwiseTask,
    *,
    prompt: str,
    refs: Mapping[str, Key],
    left_id: str,
    right_id: Callable[[Key], str],
    id_parts: Callable[[Key], Sequence[str]],
    pick_at_most: int,
    caps: SpendCaps,
    price: float | None,
    owner_id: str,
    client: Any | None = None,
    route: PaidRoute | None = None,
    deadline: float | None = None,
    validate: Callable[[Any], Any] | None = None,
    clock: Clock | None = None,
    budget: SpendBudget | None = None,
    admit: Callable[[SpendEstimate], None] | None = None,
    context: Mapping[str, Any] | None = None,
) -> ListwiseOutcome[Key]:
    """Judge the pool ``refs`` (prompt ref -> candidate key) and pick at most ``pick_at_most``.

    ``route`` and ``client`` may be resolved by the caller beforehand (a
    readiness check before paying for retrieval); ``deadline`` is a
    ``time.monotonic()`` bound on the call (see ``PaidCalls.call``);
    ``validate`` defaults to :func:`validate_all_judged`; ``budget`` replaces
    the per-call caps with a caller's (a benchmark's command budget), and
    ``admit`` also admits each attempt under the caller's shared caps (after
    the ledger and checkpoints were found not to answer it). ``context`` is
    recorded with the paid answer (its checkpoint and its receipt's declared
    block), so a caller whose rerun plans its requests differently can find
    the answer again (the role labeller's resume).
    """

    keys = list(refs.values())
    if not keys:
        return ListwiseOutcome("empty_pool")
    injected = client is not None
    route = route or plan_route(vault, task.route_task, client)
    skip = route_skip(route, price, injected=injected, price_setting=task.price_setting,
                      route_label=task.route_label)
    if skip is not None:
        return ListwiseOutcome(skip)
    input_hash = request_input_hash(task, route, prompt)
    ids = ledger_ids(task, input_hash, keys, id_parts)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        cached = judgments_by_ids(connection, ids.values())
    if cached and all(ids[key] in cached for key in keys):
        return from_ledger(task, keys, ids, cached, "cached", pick_at_most)
    if client is None:
        client, reason = resolve_client(vault, route)
    else:
        reason = transport_problem(route, client)
    if client is None or reason is not None:
        return ListwiseOutcome("unavailable", reason=reason)
    calls = PaidCalls(route=route, budget=budget or SpendBudget(caps), price_per_million=price,
                      repository=repository, owner_kind=task.route_task, owner_id=owner_id, admit=admit)
    try:
        result = calls.call(
            client, purpose=task.route_task, prompt=prompt, result_model=task.result_model,
            output_tokens=task_output_tokens(task, route), candidates=len(keys), pairs=len(keys),
            metadata={"prompt_version": task.prompt_version, "input_hash": input_hash},
            validate=validate or (lambda value: validate_all_judged(value, refs)), deadline=deadline,
            context=context,
        )
    except AIInterrupted:
        return ListwiseOutcome("cancelled", usage=calls.report())
    except SpendLimitExceeded as exc:
        return ListwiseOutcome("over_budget", reason=str(exc), usage=calls.report())
    except AIProviderUnavailable as exc:
        return ListwiseOutcome("failed", reason=type(exc).__name__, usage=calls.report())
    model = calls.last_resolved_model or route.model or "unspecified"
    verdicts: dict[str, str] = {}
    for judgment in result.judgments:
        verdicts.setdefault(judgment.ref, str(getattr(judgment, task.verdict_field)))
    picks: list[Key] = []
    for ref in result.picks:
        key = refs.get(ref)
        if key is None or key in picks or verdicts.get(ref) in task.drop_pick_verdicts:
            continue
        picks.append(key)
    picks = picks[:pick_at_most]
    with repository.connection() as connection:
        for judgment in result.judgments:
            key = refs.get(judgment.ref)
            if key is None:
                continue
            judgment_id = ids[key]
            if judgments_by_ids(connection, [judgment_id]):
                continue
            verdict = str(getattr(judgment, task.verdict_field))
            rank = picks.index(key) + 1 if key in picks else None
            details: dict[str, Any] = {"text": judgment.rationale.strip()[:600], "pick_rank": rank}
            for name in task.ledger_fields:
                details[name] = _jsonable(getattr(judgment, name, None))
            append_judgment(
                connection, id=judgment_id, task=task.ledger_task, left_kind=task.left_kind,
                left_id=left_id, right_kind=task.right_kind, right_id=right_id(key), judge="llm",
                judge_model=model, prompt_version=task.prompt_version, input_hash=input_hash,
                verdict=verdict, score=task.scores[verdict],
                rationale=json.dumps(details, ensure_ascii=False, sort_keys=True),
                created_at=utc_now_iso(clock) if clock is not None else None,
            )
        rows = judgments_by_ids(connection, ids.values())
    outcome = from_ledger(task, keys, ids, rows, "judged", pick_at_most)
    outcome.usage = calls.report()
    return outcome


__all__ = [
    "ListwiseOutcome",
    "ListwiseTask",
    "from_ledger",
    "judge_listwise",
    "ledger_ids",
    "listwise_caps",
    "request_input_hash",
    "route_skip",
    "task_output_tokens",
    "validate_all_judged",
]
