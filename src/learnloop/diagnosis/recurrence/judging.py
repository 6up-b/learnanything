"""Shortlist and judge same-cause pairs (shared by the live step and the backlog).

Candidate pairs come from hypothesis-embedding kNN over vectors already in
``embedding_vectors``: the top ``recurrence.top_k`` earlier, in-scope
hypotheses of each query, and, when B3 has set one for the ranking model AND
it was measured on vectors of the stored width, recipe and prefix, only those
at or above its blocking cutoff. The ranking model is ``embedding.model``
once its backfill covers what any other stored model covers (Slice 1 §9.6);
until then the previous model keeps ranking and the replacement's partial
index is never used. A pair is skipped before ranking when it is already
settled: same exact class, the same recurrence group, or a non-``unsure``
verdict from the owner, a verifier, the judge or a validated diagnoser
citation. Every other shortlisted pair goes to the same-cause judge; nothing
is merged or rejected by score.

Spend: every judge call and embedding request is admitted on a
:class:`ReviewSpend` before it is sent. Inside a budgeted command (``learnloop
diagnose drain|retry``) that is the COMMAND's budget, and a ``reserve``
callback keeps optional recurrence work from eating into what the command's
remaining diagnoses need.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from contextlib import closing
from typing import Any

from learnloop.ai.errors import AIInterrupted
from learnloop.ai.spend import SpendEstimate
from learnloop.ai.transport import execute_structured_operation
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.embedding_vectors import put_vector
from learnloop.diagnosis.offline_review.spend import ReviewSpend
from learnloop.diagnosis.recurrence.kind import SAME_CAUSE, SAME_CAUSE_ROUTE, compatible, scope_of
from learnloop.diagnosis.split.embeddings import TASK_PREFIX
from learnloop.matching.judge import SameOrDifferent
from learnloop.matching.kinds import Subject
from learnloop.matching.shortlist import (
    Shortlist,
    active_model,
    compatible_cutoff,
    shortlist_pairs,
    stored_width,
)
from learnloop.recurrence import key_for_statement
from learnloop.substrate.recurrence_groups import active_group_map, compute_groups
from learnloop.vault.models import LoadedVault

#: The spend route hypothesis embeddings are admitted on (metered).
EMBEDDING_ROUTE = "embedding"
EMBED_BATCH = 32
#: () -> what the enclosing command must keep for its remaining work.
Reserve = Callable[[], SpendEstimate]
#: () -> renew the enclosing diagnose job's lease; False once another worker
#: holds it (second review F7). Called before every paid request.
Heartbeat = Callable[[], bool]


class LeaseLost(AIInterrupted):
    """The enclosing job's lease is held by another worker: no further paid call."""


def beat(heartbeat: Heartbeat | None) -> None:
    """Renew the job lease before a paid request, or stop (``LeaseLost``)."""

    if heartbeat is not None and not heartbeat():
        raise LeaseLost("the diagnose job's lease is held by another worker")

#: Judges whose verdict settles a pair (the learner's card tap does not: the
#: judge may still be asked, and authority decides).
SETTLING_JUDGES = frozenset({"owner", "verifier", "llm", "diagnoser", "decider"})


def estimate_tokens(text: str) -> int:
    return (len(text.encode("utf-8")) + 3) // 4


def settled_class_pairs(repository: Repository) -> set[frozenset[str]]:
    """Class pairs a validated citation or a settling verdict already decided."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        build = compute_groups(connection)
    return {
        frozenset((row["left_class"], row["right_class"]))
        for row in build.labelled
        if row["judge"] in SETTLING_JUDGES and row["verdict"] in ("same", "different")
    }


def blocking_cutoff(vault: LoadedVault, model_id: str, *, dims: int | None) -> tuple[float | None, str, str | None]:
    """(cutoff, basis, refusal): B3's entry for this model when it matches the stored vectors.

    Never a code default. An entry measured at another width, on another
    text recipe or prefix is refused (top-k alone blocks).
    """

    cutoffs = getattr(getattr(vault.config, "recurrence", None), "blocking_cutoffs", None) or {}
    return compatible_cutoff(cutoffs.get(model_id), SAME_CAUSE, model_id=model_id, dims=dims)


def learner_state(subjects: Sequence[Subject]) -> list[Subject]:
    return [subject for subject in subjects if scope_of(subject).cause_scope == "learner_state"]


def plan_shortlist(
    vault: LoadedVault,
    repository: Repository,
    *,
    queries: Sequence[Subject],
    pool: Sequence[Subject],
    population: Sequence[Subject],
    model_id: str,
) -> Shortlist:
    """Shortlist ``queries`` against ``pool``; ``model_id`` is the CONFIGURED model.

    The ranking model may differ while a replacement's backfill is pending.
    """

    groups = active_group_map(vault, repository)
    settled = settled_class_pairs(repository)

    def is_settled(query: Subject, candidate: Subject) -> bool:
        left, right = scope_of(query).statement_normalized, scope_of(candidate).statement_normalized
        if left == right or key_for_statement(left, groups) == key_for_statement(right, groups):
            return True
        return frozenset((left, right)) in settled

    config = vault.config.recurrence
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        activation = active_model(connection, SAME_CAUSE, population, configured=model_id)
        if activation.ranking is None:
            empty = Shortlist(model_id=None, top_k=int(config.top_k), queries=len(queries),
                              queries_without_vector=len(queries))
            empty.activation = activation.summary()
            return empty
        width = stored_width(connection, SAME_CAUSE, model_id=activation.ranking)
        cutoff, basis, refusal = blocking_cutoff(vault, activation.ranking, dims=width)
        shortlist = shortlist_pairs(
            connection,
            SAME_CAUSE,
            queries=queries,
            pool=pool,
            model_id=activation.ranking,
            top_k=int(config.top_k),
            cutoff=cutoff,
            compatible=compatible,
            settled=is_settled,
            centre_over=population,
        )
    shortlist.cutoff_basis, shortlist.cutoff_refusal = basis, refusal
    shortlist.activation = {**activation.summary(), "stored_dims": width}
    return shortlist


def default_judge_client(vault: LoadedVault) -> Any | None:
    """The ``ai.routing.same_cause_judge`` client (unset: the diagnosis route)."""

    from learnloop.ai.routing import ready_client_for_task

    resolved = ready_client_for_task(
        vault.root,
        vault.config,
        SAME_CAUSE_ROUTE,
        timeout_seconds=int(vault.config.recurrence.judge_timeout_seconds),
    )
    return resolved.client if resolved.ready else None


def model_label(client: Any) -> str:
    return str(getattr(client, "model", None) or getattr(client, "model_id", None) or getattr(client, "provider_name", None) or "unknown")


def producer_label(client: Any) -> str:
    """Who produced a verdict: the model AND its reasoning effort.

    Codex's low and medium tiers serve one model (``gpt-5.6-sol``) at
    different efforts: a guard pass or a reused verdict from one must not
    count for the other (second review F10). The label is ``model@effort``
    (just ``model`` without an effort); it is what ``judgment_ledger.judge_model``
    stores for the judge's verdicts. The profile NAME is not part of it: it is
    a config alias (Codex clients do not even carry it), and two profiles with
    the same model and effort are the same producer.
    """

    from learnloop.ai.execution import model_settings

    settings = model_settings(client)
    return producer_label_for(model=settings.get("model") or model_label(client), effort=settings.get("reasoning_effort"))


def producer_label_for(*, model: Any, effort: Any = None) -> str:
    label = str(model or "unknown")
    effort_text = str(effort or "").strip()
    return f"{label}@{effort_text}" if effort_text else label


def sum_estimates(*estimates: SpendEstimate) -> SpendEstimate:
    usd = [estimate.estimated_usd for estimate in estimates]
    return SpendEstimate(
        candidates=sum(estimate.candidates for estimate in estimates),
        pairs=sum(estimate.pairs for estimate in estimates),
        calls=sum(estimate.calls for estimate in estimates),
        total_tokens=sum(estimate.total_tokens for estimate in estimates),
        estimated_usd=None if any(value is None for value in usd) else sum(value or 0.0 for value in usd),
    )


def admit_beside(spend: ReviewSpend, route: str, *, input_tokens: int, reserve: Reserve | None) -> None:
    """Refuse (``SpendLimitExceeded``, nothing sent) unless one request on
    ``route`` still leaves room for what the enclosing command reserves."""

    if reserve is None:
        return
    request = spend.estimate(route, calls=1, input_tokens=input_tokens, output_tokens=spend.output_limit(route))
    spend.check(sum_estimates(request, reserve()))


class JudgeExecutor:
    """One admitted, isolated structured call per pair on the judge route.

    ``producer`` (the model and reasoning effort this route's client answers
    as, :func:`producer_label`) is known before any call: judgment reuse and
    claims are per producer.
    """

    def __init__(self, spend: ReviewSpend, client: Any, *, reserve: Reserve | None = None,
                 heartbeat: Heartbeat | None = None) -> None:
        self.spend = spend
        self.client = client
        self.reserve = reserve
        self.heartbeat = heartbeat
        self.producer = producer_label(client)
        spend.register(SAME_CAUSE_ROUTE, client)

    def __call__(self, prompt: str, result_model: type[SameOrDifferent], purpose: str) -> tuple[SameOrDifferent, str]:
        # Inside a diagnose job: renew its lease first, so the job is never
        # re-leased (and its paid work repeated) while this call runs.
        beat(self.heartbeat)
        tokens = estimate_tokens(prompt)
        admit_beside(self.spend, SAME_CAUSE_ROUTE, input_tokens=tokens, reserve=self.reserve)
        with self.spend.collector.observing():
            with self.spend.request(SAME_CAUSE_ROUTE, purpose, input_tokens=tokens):
                result = execute_structured_operation(
                    self.client, purpose=purpose, prompt=prompt, result_model=result_model, isolated=True
                )
        return result, self.producer


def judge_executor(spend: ReviewSpend, client: Any, *, reserve: Reserve | None = None,
                   heartbeat: Heartbeat | None = None) -> JudgeExecutor:
    return JudgeExecutor(spend, client, reserve=reserve, heartbeat=heartbeat)


def embed_on_spend(
    spend: ReviewSpend,
    client: Any,
    repository: Repository,
    records: Sequence[Any],
    *,
    reserve: Reserve | None = None,
    heartbeat: Heartbeat | None = None,
) -> int:
    """Embed records in admitted batches on ``spend``; returns how many were stored.

    Each batch is admitted (and, with ``reserve``, only while the enclosing
    command's remaining work still fits) before it is sent; a refusal raises
    ``SpendLimitExceeded`` with the earlier batches kept.
    """

    if not records:
        return 0
    if EMBEDDING_ROUTE not in spend.routes or spend.routes[EMBEDDING_ROUTE].model != getattr(client, "model_id", None):
        # Billed as the client actually built; a published price wins.
        from learnloop.diagnosis.split.jobs import register_retrieval_route

        register_retrieval_route(spend, client)
    embedded = 0
    for offset in range(0, len(records), EMBED_BATCH):
        batch = list(records[offset:offset + EMBED_BATCH])
        tokens = sum(estimate_tokens(record.text) + 32 for record in batch)
        beat(heartbeat)
        admit_beside(spend, EMBEDDING_ROUTE, input_tokens=tokens, reserve=reserve)
        with spend.collector.observing():
            with spend.request(EMBEDDING_ROUTE, "embedding", input_tokens=tokens, output_tokens=0):
                vectors = client.embed([record.text for record in batch], TASK_PREFIX)
        if len(vectors) != len(batch):
            raise ValueError("the embedding endpoint returned a different number of vectors")
        with closing(connect(repository.sqlite_path)) as connection, connection:
            for record, vector in zip(batch, vectors, strict=True):
                put_vector(
                    connection, record_kind=record.record_kind, record_id=record.record_id, field=record.field,
                    content_hash=record.content_hash, model_id=client.model_id, task_prefix=TASK_PREFIX, vector=vector,
                )
        embedded += len(batch)
    return embedded


def receipt_sink(repository: Repository, *, owner_kind: str, owner_id: str) -> Callable[[str, dict[str, Any]], None]:
    return lambda action, event: repository.record_model_event(action, event, owner_kind=owner_kind, owner_id=owner_id)


__all__ = [
    "EMBEDDING_ROUTE",
    "Heartbeat",
    "JudgeExecutor",
    "LeaseLost",
    "Reserve",
    "SETTLING_JUDGES",
    "admit_beside",
    "beat",
    "blocking_cutoff",
    "default_judge_client",
    "embed_on_spend",
    "estimate_tokens",
    "judge_executor",
    "learner_state",
    "model_label",
    "plan_shortlist",
    "producer_label",
    "producer_label_for",
    "receipt_sink",
    "settled_class_pairs",
    "sum_estimates",
]
