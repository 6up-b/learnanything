"""Shortlist and judge same-cause pairs (shared by the live step and the backlog).

Candidate pairs come from hypothesis-embedding kNN over vectors already in
``embedding_vectors`` for the configured model (``embedding.model``): the top
``recurrence.top_k`` earlier, in-scope hypotheses of each query, and, when B3
has set one for this model, only those at or above its blocking cutoff. A pair
is skipped before ranking when it is already settled: same exact class, the
same recurrence group, or a non-``unsure`` verdict from the owner, a verifier,
the judge or a validated diagnoser citation. Every other shortlisted pair goes
to the same-cause judge; nothing is merged or rejected by score.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from contextlib import closing
from typing import Any

from learnloop.ai.transport import execute_structured_operation
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.diagnosis.offline_review.spend import ReviewSpend
from learnloop.diagnosis.recurrence.kind import SAME_CAUSE, SAME_CAUSE_ROUTE, compatible, scope_of
from learnloop.matching.judge import Executor, SameOrDifferent
from learnloop.matching.kinds import Subject
from learnloop.matching.shortlist import Shortlist, shortlist_pairs
from learnloop.recurrence import key_for_statement
from learnloop.substrate.recurrence_groups import compute_groups
from learnloop.vault.models import LoadedVault

#: Judges whose verdict settles a pair (the learner's card tap does not: the
#: judge may still be asked, and authority decides).
SETTLING_JUDGES = frozenset({"owner", "verifier", "llm", "diagnoser"})


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


def blocking_cutoff(vault: LoadedVault, model_id: str) -> float | None:
    """B3's cutoff for this model, or None (top-k only). Never a code default."""

    cutoffs = getattr(getattr(vault.config, "recurrence", None), "blocking_cutoffs", None) or {}
    value = cutoffs.get(model_id)
    return float(value) if value is not None else None


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
    groups = repository.recurrence_group_map()
    settled = settled_class_pairs(repository)

    def is_settled(query: Subject, candidate: Subject) -> bool:
        left, right = scope_of(query).statement_normalized, scope_of(candidate).statement_normalized
        if left == right or key_for_statement(left, groups) == key_for_statement(right, groups):
            return True
        return frozenset((left, right)) in settled

    config = vault.config.recurrence
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return shortlist_pairs(
            connection,
            SAME_CAUSE,
            queries=queries,
            pool=pool,
            model_id=model_id,
            top_k=int(config.top_k),
            cutoff=blocking_cutoff(vault, model_id),
            compatible=compatible,
            settled=is_settled,
            centre_over=population,
        )


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


def judge_executor(spend: ReviewSpend, client: Any) -> Executor:
    """One admitted, isolated structured call per pair on the judge route."""

    spend.register(SAME_CAUSE_ROUTE, client)
    label = model_label(client)

    def execute(prompt: str, result_model: type[SameOrDifferent], purpose: str) -> tuple[SameOrDifferent, str]:
        with spend.collector.observing():
            with spend.request(SAME_CAUSE_ROUTE, purpose, input_tokens=estimate_tokens(prompt)):
                result = execute_structured_operation(
                    client, purpose=purpose, prompt=prompt, result_model=result_model, isolated=True
                )
        return result, label

    return execute


def receipt_sink(repository: Repository, *, owner_kind: str, owner_id: str) -> Callable[[str, dict[str, Any]], None]:
    return lambda action, event: repository.record_model_event(action, event, owner_kind=owner_kind, owner_id=owner_id)


__all__ = [
    "SETTLING_JUDGES",
    "blocking_cutoff",
    "default_judge_client",
    "estimate_tokens",
    "judge_executor",
    "learner_state",
    "model_label",
    "plan_shortlist",
    "receipt_sink",
    "settled_class_pairs",
]
