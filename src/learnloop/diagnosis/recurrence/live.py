"""The live T1 step of a diagnose job, and the escalated repair (Slice 2 §3.2, §3.7).

Runs inside the diagnose job, after the diagnosis is persisted and BEFORE its
post-diagnosis normalization, so holding-pen promotion and the K=3 count of
this very attempt already see the merges:

1. materialize the attempt's hypotheses (idempotent; normalization's own
   materialization then does nothing) and refresh the recurrence groups, so
   this diagnosis's validated citations count;
2. with embeddings on: embed this attempt's new hypotheses (one capped,
   metered batch), shortlist candidate pairs against EARLIER hypotheses and
   let the same-cause judge decide each, at most
   ``recurrence.judge_max_pairs_per_attempt`` calls (pairs past the cap wait
   for the backlog command); refresh the groups again.

After normalization, :func:`record_escalation` writes the escalation receipt
when the attempt's cause has now recurred ``ESCALATION_RECURRENCE_K`` times:
the earlier answers (the evidence the card shows) and the repair, preferring
one whose operator differs from every repair shown for the group before.

Every failure here is logged and swallowed: a judge or embedding failure
never fails the diagnosis, and an unjudged pair merges nothing.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from typing import Any

from learnloop.ai.execution import record_model_calls
from learnloop.ai.spend import SpendCaps
from learnloop.algorithm_versions import RECURRENCE_GROUP_ALGORITHM_VERSION
from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.db.stores.recurrence import insert_escalation
from learnloop.diagnosis.causal_factor_deferral import ESCALATION_RECURRENCE_K
from learnloop.diagnosis.misconceptions import materialize_attempt_episode
from learnloop.diagnosis.offline_review.spend import ReviewSpend
from learnloop.diagnosis.recurrence.judging import (
    default_judge_client,
    judge_executor,
    learner_state,
    plan_shortlist,
    receipt_sink,
)
from learnloop.diagnosis.recurrence.kind import SAME_CAUSE, hypothesis_subjects
from learnloop.diagnosis.split.embeddings import embed_records, hypothesis_records
from learnloop.matching.judge import judge_pairs
from learnloop.recurrence import key_for_statement, normalize_statement
from learnloop.substrate.recurrence_groups import recurrence_active, refresh_recurrence_groups
from learnloop.vault.models import LoadedVault

LOG = logging.getLogger(__name__)

#: Receipts of the step's paid calls belong to the attempt, like its diagnosis.
MODEL_CALL_OWNER_KIND = "attempt_diagnosis"

ClientFactory = Callable[[], Any]


def live_judge_caps(max_pairs: int) -> SpendCaps:
    """One diagnose job's judge budget (Codex: calls/candidates bound it)."""

    pairs = max(0, int(max_pairs))
    return SpendCaps(
        max_candidates=pairs,
        max_pairs=pairs,
        max_retries=max(2, pairs),
        max_calls=pairs,
        max_total_tokens=max(1, pairs) * 20_000,
        max_estimated_usd=0.25,
    )


def recurrence_step(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    judge_factory: ClientFactory | None = None,
    embedding_factory: ClientFactory | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    if not recurrence_active(vault):
        return {"status": "inactive"}
    report: dict[str, Any] = {"status": "groups_refreshed"}
    try:
        materialize_attempt_episode(vault, repository, attempt_id=attempt_id, clock=clock)
        report["groups"] = refresh_recurrence_groups(vault, repository)
    except Exception:  # noqa: BLE001 - normalization refreshes again; never fail the job
        LOG.warning("recurrence refresh failed for attempt %s", attempt_id, exc_info=True)
        return {"status": "refresh_failed"}
    config = vault.config.recurrence
    if not config.judge_enabled or int(config.judge_max_pairs_per_attempt) <= 0:
        report["judge"] = "disabled"
        return report
    if not vault.config.embedding.enabled or embedding_factory is None or judge_factory is None:
        report["judge"] = "no_embeddings" if not vault.config.embedding.enabled else "no_client"
        return report
    try:
        report["judge"] = _judge_attempt(
            vault, repository, attempt_id=attempt_id, judge_factory=judge_factory,
            embedding_factory=embedding_factory,
        )
        if report["judge"].get("judged"):
            report["groups"] = refresh_recurrence_groups(vault, repository)
    except Exception:  # noqa: BLE001 - the judge never fails the diagnosis
        LOG.warning("same-cause judging failed for attempt %s", attempt_id, exc_info=True)
        report["judge"] = {"status": "failed"}
    return report


def _judge_attempt(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    judge_factory: ClientFactory,
    embedding_factory: ClientFactory,
) -> dict[str, Any]:
    try:
        embedder = embedding_factory()
    except Exception:  # noqa: BLE001
        embedder = None
    if embedder is None:
        return {"status": "embedding_unavailable"}
    model_id = str(getattr(embedder, "model_id", "") or vault.config.embedding.model)
    with record_model_calls(repository, owner_kind=MODEL_CALL_OWNER_KIND, owner_id=attempt_id):
        embedded = embed_records(embedder, repository, hypothesis_records(repository, attempt_ids=[attempt_id]))
    population = hypothesis_subjects(vault, repository)
    queries = [subject for subject in learner_state(population) if subject.scope["hypothesis"].attempt_id == attempt_id]
    if not queries:
        return {"status": "no_queries", "embedded": embedded.embedded}
    shortlist = plan_shortlist(
        vault, repository, queries=queries, pool=learner_state(population), population=population, model_id=model_id,
    )
    cap = int(vault.config.recurrence.judge_max_pairs_per_attempt)
    pairs = sorted(shortlist.pairs, key=lambda pair: (-pair.score, pair.left.id, pair.right.id))
    chosen, deferred = pairs[:cap], pairs[cap:]
    outcome: dict[str, Any] = {
        "status": "complete",
        "embedded": embedded.embedded,
        "shortlist": shortlist.summary(),
        "deferred_to_backlog": len(deferred),
        "judged": 0,
    }
    if not chosen:
        return outcome
    client = judge_factory()
    if client is None:
        outcome["status"] = "judge_not_ready"
        return outcome
    spend = ReviewSpend(live_judge_caps(cap))
    spend.collector.sink = receipt_sink(repository, owner_kind=MODEL_CALL_OWNER_KIND, owner_id=attempt_id)
    results = judge_pairs(repository, SAME_CAUSE, chosen, execute=judge_executor(spend, client))
    outcome["judged"] = sum(1 for row in results if row.status == "judged")
    outcome["verdicts"] = {
        verdict: sum(1 for row in results if row.verdict == verdict) for verdict in ("same", "different", "unsure")
    }
    outcome["not_judged"] = [row.as_dict() for row in results if row.status in ("failed", "not_run")]
    outcome["spend"] = spend.summary()
    return outcome


def default_live_judge_factory(vault: LoadedVault) -> ClientFactory:
    return lambda: default_judge_client(vault)


# -- the escalated repair (§3.7) -------------------------------------------------------


def _attempt_classes(repository: Repository, attempt_id: str) -> dict[str, list[dict[str, Any]]]:
    classes: dict[str, list[dict[str, Any]]] = {}
    for row in repository.causal_hypotheses_for_attempt(attempt_id):
        if row.get("status") == "open_set":
            continue
        classes.setdefault(str(row.get("statement_normalized") or ""), []).append(row)
    return classes


def _escalated_class(proposal: Mapping[str, Any], classes: Mapping[str, list[dict[str, Any]]]) -> str | None:
    """The diagnosis's highest-weight cause that is a learner-state hypothesis here."""

    ranked: list[tuple[float, int, int, str]] = []
    for event_position, event in enumerate(proposal.get("event_diagnoses") or []):
        if not isinstance(event, Mapping):
            continue
        for cause_position, cause in enumerate(event.get("candidate_causes") or []):
            if not isinstance(cause, Mapping):
                continue
            statement = normalize_statement(str(cause.get("statement") or ""))
            if statement:
                ranked.append((-float(cause.get("prior_weight") or 0.0), event_position, cause_position, statement))
    for _weight, _event, _cause, statement in sorted(ranked):
        if any(row.get("cause_scope") == "learner_state" for row in classes.get(statement) or []):
            return statement
    return None


def _repair_key(repair: Mapping[str, Any]) -> str | None:
    operator = str(repair.get("operator") or "").strip()
    if operator:
        return operator
    mode = str(repair.get("practice_mode") or "").strip()
    return f"mode:{mode}" if mode else None


def _shown_repair_keys(repository: Repository, attempt_ids: list[str]) -> set[str]:
    keys: set[str] = set()
    for attempt_id in attempt_ids:
        metadata = repository.fetch_attempt_feedback_metadata(attempt_id) or {}
        for repair in metadata.get("repair_suggestions") or []:
            if isinstance(repair, Mapping) and (key := _repair_key(repair)) is not None:
                keys.add(key)
    return keys


def record_escalation(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    diagnosis: Mapping[str, Any],
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Write the escalation receipt when this attempt's cause recurs K times.

    The recurrence count is the number of distinct attempts, up to and
    including this one, with a hypothesis in the cause's recurrence group
    (exact statement, or a merged group). Idempotent per diagnosis.
    """

    if not recurrence_active(vault) or diagnosis.get("status") != "completed":
        return None
    proposal = diagnosis.get("proposal") or {}
    classes = _attempt_classes(repository, attempt_id)
    statement = _escalated_class(proposal, classes)
    if statement is None:
        return None
    groups = repository.recurrence_group_map()
    key = key_for_statement(statement, groups)
    statements = sorted({value for value, group in groups.items() if group == key} or {statement})
    current = repository.fetch_practice_attempt(attempt_id) or {}
    order = (str(current.get("created_at") or ""), attempt_id)
    earlier: dict[str, tuple[str, str]] = {}
    for member_statement in statements:
        for row in repository.causal_hypotheses_with_statement(member_statement):
            other = str(row.get("attempt_id") or "")
            if other == attempt_id or other in earlier:
                continue
            attempt = repository.fetch_practice_attempt(other)
            if attempt is None:
                continue
            other_order = (str(attempt.get("created_at") or ""), other)
            if other_order < order:
                earlier[other] = other_order
    count = len(earlier) + 1
    if count < ESCALATION_RECURRENCE_K:
        return None
    earlier_ids = [attempt for attempt, _order in sorted(earlier.items(), key=lambda item: item[1], reverse=True)]
    prior = _shown_repair_keys(repository, earlier_ids)
    repairs = [
        repair
        for repair in (repository.fetch_attempt_feedback_metadata(attempt_id) or {}).get("repair_suggestions") or []
        if isinstance(repair, Mapping)
    ]
    chosen = next((repair for repair in repairs if (_repair_key(repair) or "") not in prior and _repair_key(repair)), None)
    different = chosen is not None
    if chosen is None and repairs:
        chosen = repairs[0]
    with repository.atomic():
        escalation_id = insert_escalation(
            repository.connection(),
            attempt_id=attempt_id,
            diagnosis_id=str(diagnosis["id"]),
            group_key=key,
            recurrence_count=count,
            earlier_attempt_ids=earlier_ids,
            repair_suggestion_id=str(chosen.get("id")) if chosen is not None and chosen.get("id") else None,
            repair_operator=_repair_key(chosen) if chosen is not None else None,
            prior_operators=prior,
            different_approach=different,
            algorithm_version=RECURRENCE_GROUP_ALGORITHM_VERSION,
            clock=clock,
        )
    return {"escalation_id": escalation_id, "group_key": key, "recurrence_count": count, "different_approach": different}


__all__ = [
    "default_live_judge_factory",
    "live_judge_caps",
    "record_escalation",
    "recurrence_step",
]
