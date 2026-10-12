"""The live T1 step of a diagnose job, and the escalated repair (Slice 2 §3.2, §3.7).

Runs inside the diagnose job, after the diagnosis is persisted and BEFORE its
post-diagnosis normalization, so holding-pen promotion and the K=3 count of
this very attempt already see the merges:

1. materialize the attempt's hypotheses (idempotent; normalization's own
   materialization then does nothing) and refresh the recurrence groups, so
   this diagnosis's validated citations count;
2. with embeddings on: embed this attempt's new hypotheses, shortlist
   candidate pairs against EARLIER hypotheses and let the same-cause judge
   decide each, at most ``recurrence.judge_max_pairs_per_attempt`` calls
   (pairs past the cap wait for the backlog command); refresh the groups
   again.

**Spend.** Inside a budgeted command (``learnloop diagnose drain|retry``)
every embedding request and judge call is admitted on the COMMAND's budget
(its caps, its cancellation, its spend summary), and only while the command's
remaining diagnoses still fit after it (``reserve``); a refusal leaves the
rest for the backlog. Outside one (the sidecar worker, the inline CLI/TUI
path) a per-job budget (:func:`live_judge_caps`) admits them.

After normalization, :func:`record_escalation` writes the escalation receipt
when the attempt's cause has now recurred ``ESCALATION_RECURRENCE_K`` times:
the earlier answers (the evidence the card shows) and a repair whose operator
differs from every repair shown for the group before: one of the diagnosis's
own, else one requested at escalation time (:mod:`.escalation`), else the
honest "same kind of repair" label.

Every failure here is logged and swallowed: a judge or embedding failure
never fails the diagnosis, and an unjudged pair merges nothing.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from typing import Any, Iterator

from learnloop.ai.errors import AIInterrupted
from learnloop.ai.spend import SpendCaps, SpendLimitExceeded
from learnloop.algorithm_versions import RECURRENCE_GROUP_ALGORITHM_VERSION
from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.db.stores.recurrence import insert_escalation
from learnloop.diagnosis.causal_attribution import validate_repair_candidate
from learnloop.diagnosis.causal_factor_deferral import ESCALATION_RECURRENCE_K
from learnloop.diagnosis.misconceptions import materialize_attempt_episode
from learnloop.diagnosis.offline_review.spend import ReviewSpend
from learnloop.diagnosis.recurrence.display import escalation_suggestion_id
from learnloop.diagnosis.recurrence.escalation import per_job_spend, repair_key, request_different_repair
from learnloop.diagnosis.recurrence.judging import (
    Heartbeat,
    LeaseLost,
    Reserve,
    default_judge_client,
    embed_on_spend,
    judge_executor,
    learner_state,
    plan_shortlist,
    receipt_sink,
)
from learnloop.diagnosis.recurrence.kind import SAME_CAUSE, hypothesis_subjects
from learnloop.diagnosis.split.embeddings import hypothesis_records, pending_records
from learnloop.matching.judge import judge_pairs
from learnloop.recurrence import key_for_statement, normalize_statement
from learnloop.substrate.recurrence_groups import active_group_map, recurrence_active, refresh_recurrence_groups
from learnloop.vault.models import LoadedVault

LOG = logging.getLogger(__name__)

#: Receipts of the step's paid calls belong to the attempt, like its diagnosis.
MODEL_CALL_OWNER_KIND = "attempt_diagnosis"
#: Embedding requests one job may make for its own hypotheses (per-job budget).
LIVE_EMBED_CALLS = 4
#: Dry-run allowances (upper bounds) of one job's T1 work: one judge prompt,
#: and the embedding tokens of the attempt's own hypotheses.
PLANNED_JUDGE_PROMPT_TOKENS = 1_500
PLANNED_EMBED_TOKENS_PER_JOB = 1_200

ClientFactory = Callable[[], Any]
Cancelled = Callable[[], bool]


def live_judge_caps(max_pairs: int) -> SpendCaps:
    """One diagnose job's own budget: its judge calls (Codex: calls bound them)
    plus the few metered embedding requests for its own hypotheses."""

    pairs = max(0, int(max_pairs))
    return SpendCaps(
        max_candidates=pairs,
        max_pairs=pairs,
        max_retries=max(2, pairs),
        max_calls=pairs + LIVE_EMBED_CALLS,
        max_total_tokens=max(1, pairs) * 20_000 + 200_000,
        max_estimated_usd=0.30,
    )


@contextmanager
def _receipts_for(spend: ReviewSpend, repository: Repository, attempt_id: str) -> Iterator[None]:
    """Receipt the step's calls under THIS attempt, even on a shared command budget."""

    previous = spend.collector.sink
    spend.collector.sink = receipt_sink(repository, owner_kind=MODEL_CALL_OWNER_KIND, owner_id=attempt_id)
    try:
        yield
    finally:
        spend.collector.sink = previous


def recurrence_step(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    judge_factory: ClientFactory | None = None,
    embedding_factory: ClientFactory | None = None,
    spend: ReviewSpend | None = None,
    reserve: Reserve | None = None,
    cancelled: Cancelled | None = None,
    clock: Clock | None = None,
    heartbeat: Heartbeat | None = None,
) -> dict[str, Any]:
    """``spend``/``reserve``: the enclosing command's budget and what it keeps
    for its remaining diagnoses; None outside a budgeted command.
    ``heartbeat`` renews the diagnose job's lease before every paid request
    and stops the step once another worker holds it."""

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
    job_spend = spend if spend is not None else ReviewSpend(
        live_judge_caps(int(config.judge_max_pairs_per_attempt)), cancelled=cancelled
    )
    try:
        with _receipts_for(job_spend, repository, attempt_id):
            report["judge"] = _judge_attempt(
                vault, repository, attempt_id=attempt_id, judge_factory=judge_factory,
                embedding_factory=embedding_factory, spend=job_spend, reserve=reserve if spend is not None else None,
                heartbeat=heartbeat,
            )
        if report["judge"].get("judged"):
            report["groups"] = refresh_recurrence_groups(vault, repository)
    except Exception:  # noqa: BLE001 - the judge never fails the diagnosis
        LOG.warning("same-cause judging failed for attempt %s", attempt_id, exc_info=True)
        report["judge"] = {"status": "failed"}
    report["budget"] = "command" if spend is not None else "per_job"
    return report


def _judge_attempt(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    judge_factory: ClientFactory,
    embedding_factory: ClientFactory,
    spend: ReviewSpend,
    reserve: Reserve | None,
    heartbeat: Heartbeat | None = None,
) -> dict[str, Any]:
    try:
        embedder = embedding_factory()
    except Exception:  # noqa: BLE001
        embedder = None
    if embedder is None:
        return {"status": "embedding_unavailable"}
    model_id = str(getattr(embedder, "model_id", "") or vault.config.embedding.model)
    missing = pending_records(repository, hypothesis_records(repository, attempt_ids=[attempt_id]), model_id)
    try:
        embedded = embed_on_spend(spend, embedder, repository, missing, reserve=reserve, heartbeat=heartbeat)
    except (SpendLimitExceeded, AIInterrupted) as exc:
        # Refused (caps, the command was cancelled, or the job's lease went
        # to another worker) before sending: this attempt's hypotheses wait
        # for the embed job / backlog; nothing can be shortlisted for them now.
        status = (
            "lease_lost" if isinstance(exc, LeaseLost)
            else "cancelled" if isinstance(exc, AIInterrupted) else "embedding_refused"
        )
        return {"status": status, "reason": str(exc), "spend": spend.summary()}
    population = hypothesis_subjects(vault, repository)
    queries = [subject for subject in learner_state(population) if subject.scope["hypothesis"].attempt_id == attempt_id]
    if not queries:
        return {"status": "no_queries", "embedded": embedded}
    shortlist = plan_shortlist(
        vault, repository, queries=queries, pool=learner_state(population), population=population, model_id=model_id,
    )
    cap = int(vault.config.recurrence.judge_max_pairs_per_attempt)
    pairs = sorted(shortlist.pairs, key=lambda pair: (-pair.score, pair.left.id, pair.right.id))
    chosen, deferred = pairs[:cap], pairs[cap:]
    outcome: dict[str, Any] = {
        "status": "complete",
        "embedded": embedded,
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
    results = judge_pairs(
        repository, SAME_CAUSE, chosen, execute=judge_executor(spend, client, reserve=reserve, heartbeat=heartbeat)
    )
    outcome["judged"] = sum(1 for row in results if row.status == "judged")
    outcome["verdicts"] = {
        verdict: sum(1 for row in results if row.verdict == verdict) for verdict in ("same", "different", "unsure")
    }
    outcome["not_judged"] = [
        row.as_dict() for row in results if row.status in ("failed", "not_run", "claimed_elsewhere", "fenced")
    ]
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


def escalation_card_enabled(vault: LoadedVault) -> bool:
    return bool(getattr(getattr(vault.config, "recurrence", None), "escalation_card_enabled", True))


def _diagnosis_in_force(repository: Repository, attempt_id: str) -> bool:
    """A blind-graded answer counts only while a completed live diagnosis is
    in force for its current grade (a regrade that left nothing to explain,
    or a failed rediagnosis, takes it out); a pre-split answer counts as is."""

    if repository.latest_blind_grade_record(attempt_id) is None:
        return True
    return repository.current_live_diagnosis(attempt_id) is not None


def _shown_repairs(repository: Repository, attempt_ids: list[str]) -> list[dict[str, Any]]:
    """Every repair shown for these answers: their feedback's suggestions and
    any repair an earlier escalation wrote for them."""

    shown: list[dict[str, Any]] = []
    for attempt_id in attempt_ids:
        metadata = repository.fetch_attempt_feedback_metadata(attempt_id) or {}
        shown.extend(dict(repair) for repair in metadata.get("repair_suggestions") or [] if isinstance(repair, Mapping))
        diagnosis = repository.current_live_diagnosis(attempt_id)
        escalation = repository.recurrence_escalation(str(diagnosis["id"])) if diagnosis else None
        if escalation is not None and isinstance(escalation.get("repair"), Mapping):
            shown.append(dict(escalation["repair"]))
    return shown


def record_escalation(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    diagnosis: Mapping[str, Any],
    writer_factory: ClientFactory | None = None,
    spend: ReviewSpend | None = None,
    reserve: Reserve | None = None,
    cancelled: Cancelled | None = None,
    clock: Clock | None = None,
    heartbeat: Heartbeat | None = None,
) -> dict[str, Any] | None:
    """Write the escalation receipt when this attempt's cause recurs K times.

    The recurrence count is the number of distinct attempts, up to and
    including this one, with a hypothesis in the cause's recurrence group
    (exact statement, or a merged group). Idempotent per diagnosis: an
    existing receipt returns before any request. ``writer_factory`` builds
    the diagnosis-route client asked for a different repair when the
    diagnosis offers none (``spend``/``reserve``: the command's budget).
    """

    if not recurrence_active(vault) or diagnosis.get("status") != "completed":
        return None
    if repository.recurrence_escalation(str(diagnosis["id"])) is not None:
        return None
    proposal = diagnosis.get("proposal") or {}
    classes = _attempt_classes(repository, attempt_id)
    statement = _escalated_class(proposal, classes)
    if statement is None:
        return None
    groups = active_group_map(vault, repository)
    key = key_for_statement(statement, groups)
    statements = sorted({value for value, group in groups.items() if group == key} or {statement})
    current = repository.fetch_practice_attempt(attempt_id) or {}
    order = (str(current.get("created_at") or ""), attempt_id)
    earlier: dict[str, tuple[str, str]] = {}
    for member_statement in statements:
        # Only heads that still stand as a learner belief count (candidate or
        # validated, learner_state): a refuted cause ("That's wrong" retires
        # or demotes it) or an item/grader/session-scoped cause in the group
        # is not a recurrence of the learner's belief (second review F8).
        for row in repository.causal_hypotheses_with_statement(member_statement):
            other = str(row.get("attempt_id") or "")
            if other == attempt_id or other in earlier:
                continue
            attempt = repository.fetch_practice_attempt(other)
            if attempt is None or not _diagnosis_in_force(repository, other):
                continue
            other_order = (str(attempt.get("created_at") or ""), other)
            if other_order < order:
                earlier[other] = other_order
    count = len(earlier) + 1
    if count < ESCALATION_RECURRENCE_K:
        return None
    earlier_ids = [attempt for attempt, _order in sorted(earlier.items(), key=lambda item: item[1], reverse=True)]
    earlier_repairs = _shown_repairs(repository, earlier_ids)
    prior = {key_ for key_ in (repair_key(repair) for repair in earlier_repairs) if key_}
    repairs = [
        dict(repair)
        for repair in (repository.fetch_attempt_feedback_metadata(attempt_id) or {}).get("repair_suggestions") or []
        if isinstance(repair, Mapping)
    ]
    chosen = next((repair for repair in repairs if repair_key(repair) and repair_key(repair) not in prior), None)
    source = "diagnosis" if chosen is not None else "none"
    generated: dict[str, Any] | None = None
    generation: dict[str, Any] = {"requested": False}
    if chosen is None and not escalation_card_enabled(vault):
        # Nobody would see it: the card is switched off (second review F9).
        generation = {"requested": False, "status": "card_disabled"}
    elif chosen is None:
        generated, generation = _request_repair(
            vault, statement=statement, classes=classes, count=count, earlier_repairs=earlier_repairs,
            current_repairs=repairs, writer_factory=writer_factory, spend=spend, reserve=reserve,
            cancelled=cancelled, repository=repository, attempt_id=attempt_id, heartbeat=heartbeat,
        )
        if generation.get("status") == "lease_lost":
            # Another worker holds the job now and writes the receipt (with
            # its own request); this one writes nothing (second review F7).
            return None
        if generated is not None:
            # A repair like any other (second review F4): aimed at the
            # recurring cause, validated, shown first with its question.
            generated, validation = _as_repair_suggestion(
                vault, repository, generated, attempt_id=attempt_id, diagnosis_id=str(diagnosis["id"]),
                rows=classes.get(statement) or [], current_repairs=repairs,
            )
            if validation.get("status") == "invalid":
                generation = {**generation, "status": "invalid_repair", "validation": validation}
                generated = None
    different = chosen is not None or generated is not None
    if generated is not None:
        source = "generated"
    elif chosen is None and repairs:
        chosen, source = repairs[0], "diagnosis"
    with repository.atomic():
        escalation_id = insert_escalation(
            repository.connection(),
            attempt_id=attempt_id,
            diagnosis_id=str(diagnosis["id"]),
            group_key=key,
            recurrence_count=count,
            earlier_attempt_ids=earlier_ids,
            repair_suggestion_id=str(chosen.get("id")) if chosen is not None and chosen.get("id") else None,
            repair_operator=(generated or {}).get("operator") or (repair_key(chosen) if chosen is not None else None),
            prior_operators=prior,
            different_approach=different,
            repair_source=source,
            repair=generated,
            generation=generation,
            algorithm_version=RECURRENCE_GROUP_ALGORITHM_VERSION,
            clock=clock,
        )
    return {
        "escalation_id": escalation_id, "group_key": key, "recurrence_count": count,
        "different_approach": different, "repair_source": source, "generation": generation,
    }


_SUGGESTION_FIELDS = (
    "operator", "representation", "practice_mode", "rationale", "eliciting_question",
    "expected_response_contract",
)


def _as_repair_suggestion(
    vault: LoadedVault,
    repository: Repository,
    repair: Mapping[str, Any],
    *,
    attempt_id: str,
    diagnosis_id: str,
    rows: list[dict[str, Any]],
    current_repairs: list[dict[str, Any]] = (),  # type: ignore[assignment]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """The generated repair as a repair suggestion, and its validation.

    It targets the recurring cause's own target (the escalated class's
    learner-state head; else what this answer's own repairs target), names
    its learning object and carries every field the feedback screen renders
    (the eliciting question gets the response box). ``validate_repair_candidate``
    runs on it exactly as on the diagnosis's repairs; an ``invalid`` one is
    never shown.
    """

    attempt = repository.fetch_practice_attempt(attempt_id) or {}
    item = vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
    head = next((row for row in rows if row.get("cause_scope") == "learner_state"), rows[0] if rows else {})
    target = head.get("target_ref")
    targets = [dict(target)] if isinstance(target, Mapping) else next(
        (
            [dict(ref) for ref in repair.get("target_refs") or [] if isinstance(ref, Mapping)]
            for repair in current_repairs
            if any(isinstance(ref, Mapping) for ref in repair.get("target_refs") or [])
        ),
        [],
    )
    suggestion: dict[str, Any] = {
        "id": escalation_suggestion_id(diagnosis_id),
        **{key: repair[key] for key in _SUGGESTION_FIELDS if repair.get(key) not in (None, "")},
        "answer_reveal_budget": float(repair.get("answer_reveal_budget") or 0.0),
        "learning_object_id": str(attempt.get("learning_object_id") or "") or None,
        "target_refs": targets,
        "generated": True,
        "source": "recurrence_escalation",
    }
    suggestion.setdefault("practice_mode", "unspecified")
    validation = validate_repair_candidate(
        dict(suggestion),
        expected_answer=getattr(item, "expected_answer", None),
        trace_contract=getattr(item, "trace_contract", None),
    ).as_dict()
    suggestion["repair_validation"] = validation
    return suggestion, validation


def _request_repair(
    vault: LoadedVault,
    *,
    statement: str,
    classes: Mapping[str, list[dict[str, Any]]],
    count: int,
    earlier_repairs: list[dict[str, Any]],
    current_repairs: list[dict[str, Any]],
    writer_factory: ClientFactory | None,
    spend: ReviewSpend | None,
    reserve: Reserve | None,
    cancelled: Cancelled | None,
    repository: Repository,
    attempt_id: str,
    heartbeat: Heartbeat | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Ask the diagnosis route for a repair with a new operator (§3.7), once."""

    if not bool(getattr(vault.config.recurrence, "escalation_repair_enabled", True)):
        return None, {"requested": False, "status": "disabled"}
    if writer_factory is None:
        return None, {"requested": False, "status": "no_client"}
    if heartbeat is not None and not heartbeat():
        # The paid request is made only while this worker still holds the job.
        return None, {"requested": False, "status": "lease_lost"}
    try:
        client = writer_factory()
    except Exception:  # noqa: BLE001
        client = None
    if client is None:
        return None, {"requested": False, "status": "provider_not_ready"}
    rows = classes.get(statement) or []
    learning_object_id = str(rows[0].get("learning_object_id") or "") if rows else ""
    learning_object = vault.learning_objects.get(learning_object_id)
    job_spend = spend if spend is not None else per_job_spend(cancelled)
    with _receipts_for(job_spend, repository, attempt_id):
        return request_different_repair(
            client=client,
            cause=str(rows[0].get("statement") or statement) if rows else statement,
            learning_object=getattr(learning_object, "title", None) or learning_object_id or None,
            count=count,
            earlier_repairs=earlier_repairs,
            current_repairs=current_repairs,
            spend=job_spend,
            reserve=reserve if spend is not None else None,
        )


__all__ = [
    "PLANNED_EMBED_TOKENS_PER_JOB",
    "escalation_card_enabled",
    "PLANNED_JUDGE_PROMPT_TOKENS",
    "default_live_judge_factory",
    "live_judge_caps",
    "record_escalation",
    "recurrence_step",
]
