"""Explicit, bounded paid classification; never imported by signal replay.

The caller supplies a lazy classifier using the explicit
``field_question_classifier`` route and ``field_question_classification``
operation. On a metered route (openai_chat/openrouter) it must be a
single-physical-call classifier with hidden SDK retries disabled. There are no
implicit retries here: a rerun resumes successful WORKFLOW rows and re-admits
unfinished work.

A Codex route is billed to the owner's subscription (Slice A §5 rule 6): it runs
without the physical-request bound, its token and dollar caps are not enforced
and an unknown price does not refuse it, while the candidate and call caps
still stop a runaway loop. Its cost is estimated from reported token usage
(else the planned input-plus-output estimate) and receipts record it as
``estimated_only``.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import json
from typing import Any
from uuid import uuid4

from learnloop.ai.errors import AIInterrupted
from learnloop.ai.execution import observe_model_calls
from learnloop.ai.spend import (
    ESTIMATED_ONLY, SpendBudget, SpendCaps, SpendEstimate, SpendLimitExceeded,
    subscription_usage_estimate,
)
from learnloop.db.stores.field import insert_question_classification
from learnloop.db.stores.judgments import append_judgment
from learnloop.field.signals import QUESTION_TYPES, classification_input, input_hash

PROMPT_VERSION = "field-question-classification-v1"
TASK = "field_question_classification"


def _validated(raw: Mapping[str, Any]) -> dict[str, Any]:
    if raw.get("_invalid_mapping"):
        raise ValueError("invalid mapping")
    if raw.get("question_type") not in QUESTION_TYPES:
        raise ValueError("invalid question type")
    result = {"question_type": raw["question_type"]}
    for name in ("lo_ids", "facets"):
        value = raw.get(name, [])
        if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
            raise ValueError(f"invalid {name}")
        result[name] = list(dict.fromkeys(value))
    return result


def _price_per_token(estimate: SpendEstimate) -> float | None:
    if estimate.estimated_usd is None or not estimate.total_tokens:
        return None
    return estimate.estimated_usd / estimate.total_tokens


def load_cached_classifications(connection: Any) -> tuple[dict[str, Any], ...]:
    # Dry-run against a pre-F1 copy must not migrate just to estimate work.
    if connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='question_classifications'"
    ).fetchone() is None:
        return ()
    cursor = connection.execute("SELECT * FROM question_classifications ORDER BY created_at,id")
    names = [column[0] for column in cursor.description]
    return tuple(dict(zip(names, row, strict=True)) for row in cursor)


def classify_missing_questions(
    repository: Any,
    events: Iterable[Mapping[str, Any]],
    *,
    model: str,
    classify: Callable[[dict[str, Any]], Mapping[str, Any]],
    estimate_per_question: SpendEstimate,
    caps: SpendCaps,
    enabled: bool = False,
    dry_run: bool = False,
    cancelled: Callable[[], bool] | None = None,
    subscription: bool = False,
) -> dict[str, Any]:
    """Classify missing information, recording every returned verdict.

    ``classify`` receives only question-time input. It may lazily construct the
    configured provider on its first call, so disabled/dry runs never touch
    credentials. Returned JSON requires question_type, lo_ids and facets.
    Successful rows and ledger receipts commit after each question. A malformed
    verdict is ledgered but never cached; call failures are model-call receipts,
    not invented classification verdicts. No evidence table is touched.
    """
    if not model.strip():
        raise ValueError("explicit classification model is required")
    if estimate_per_question.calls != 1 or estimate_per_question.retries:
        raise ValueError("estimate must describe one physical call without retries")
    budget = SpendBudget(caps, cancelled=cancelled, subscription=subscription)
    with repository.connection() as connection:
        cached = {
            (c["question_event_id"] or c["interaction_event_id"], c["input_hash"], c["model"], c["prompt_version"],
             "question_event" if c["question_event_id"] else "interaction_event")
            for c in load_cached_classifications(connection)
        }
    pending = {}
    for event in events:
        row = classification_input(event)
        if row["question_type"] and (row["facets"] or row["lo_ids"]):
            continue
        digest = input_hash(event)
        key = row["id"], digest, model, PROMPT_VERSION, row["event_kind"]
        if key not in cached:
            pending[key] = row
    count = len(pending)
    estimate = SpendEstimate(
        candidates=count, calls=count, total_tokens=count * estimate_per_question.total_tokens,
        estimated_usd=(count * estimate_per_question.estimated_usd
                       if estimate_per_question.estimated_usd is not None else (0.0 if not count else None)),
    )
    report = {
        "status": "dry_run" if dry_run else "complete", "pending": count,
        "classified": 0, "invalid": 0, "model": model, "prompt_version": PROMPT_VERSION,
        "estimate": asdict(estimate), "charged": asdict(budget.used), "caps": caps.as_dict(),
        "billing": "subscription" if subscription else "metered",
        "cost_basis": ESTIMATED_ONLY if subscription else "metered_caps",
        "physical_request_bound": not subscription,
        "caps_in_force": budget.declared(),
    }
    if not enabled and not dry_run:
        return {**report, "status": "disabled"}
    try:
        budget.check(estimate)
        if dry_run:
            return report
        for key, row in pending.items():
            event_id, digest, _, _, kind = key
            checkpoint_key = hashlib.sha256(json.dumps(key).encode()).hexdigest()
            checkpoint = repository.model_checkpoint(checkpoint_key)
            raw = checkpoint["result"] if checkpoint else None
            if raw is None:
                usage: dict[str, Any] = {}
                physical_calls = 0

                def observe(action: str, event: dict[str, Any]) -> None:
                    nonlocal physical_calls
                    if action == "start" and not subscription and (
                        event.get("purpose") == "chat_request"
                        or str(event.get("purpose", "")).endswith(":sdk_turn")
                    ):
                        # Structured transports may attempt JSON repair or retry
                        # internally. Their durable start occurs BEFORE I/O.
                        # One callback reservation admits one physical call only
                        # on a metered route; Codex turns are not bounded.
                        if physical_calls:
                            raise SpendLimitExceeded("Implicit classification retry requires a new command")
                        physical_calls += 1
                    if action != "start" and subscription:
                        event = {**event, "usage_json": json.dumps({
                            **json.loads(event.get("usage_json") or "{}"),
                            **subscription_usage_estimate(
                                event, planned_tokens=estimate_per_question.total_tokens,
                                price_per_token=_price_per_token(estimate_per_question),
                            ),
                        }, sort_keys=True)}
                    repository.record_model_event(action, event, owner_kind=TASK, owner_id=event_id)
                    if action == "finish":
                        for name in ("input_tokens", "output_tokens", "cost"):
                            if event.get(name) is not None:
                                usage[name] = max(usage.get(name, 0), event[name])

                with budget.request(replace(estimate_per_question, candidates=1)) as charge:
                    with observe_model_calls(observe):
                        try:
                            raw = dict(classify(row))
                        finally:
                            tokens = None
                            if usage.get("input_tokens") is not None or usage.get("output_tokens") is not None:
                                tokens = (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0)
                            cost = usage.get("cost")
                            if tokens and estimate_per_question.total_tokens and estimate_per_question.estimated_usd is not None:
                                cost = max(cost or 0, tokens * estimate_per_question.estimated_usd / estimate_per_question.total_tokens)
                            if subscription and estimate_per_question.estimated_usd is None:
                                cost = None  # estimated tokens only; never refused
                            charge.reconcile(total_tokens=tokens, estimated_usd=cost)
            try:
                result = _validated(raw)
            except (ValueError, TypeError):
                result = None
            now = datetime.now(timezone.utc).isoformat()
            with repository.connection() as connection:
                append_judgment(
                    connection, task=TASK, left_kind=kind, left_id=event_id,
                    judge="llm", judge_model=model, prompt_version=PROMPT_VERSION,
                    input_hash=digest, verdict=json.dumps(raw, sort_keys=True),
                    created_at=now,
                )
                if result is not None:
                    insert_question_classification(
                        connection,
                        (str(uuid4()), event_id if kind == "question_event" else None,
                         event_id if kind == "interaction_event" else None, digest,
                         result["question_type"], json.dumps(result["lo_ids"]), json.dumps(result["facets"]),
                         model, PROMPT_VERSION, now),
                    )
            if result is not None:
                repository.save_model_checkpoint(checkpoint_key, purpose=TASK, result=dict(raw))
                report["classified"] += 1
            else:
                report["invalid"] += 1
    except AIInterrupted:
        report["status"] = "cancelled"
    except SpendLimitExceeded:
        report["status"] = "over_budget"
    finally:
        report["charged"] = asdict(budget.used)
    return report
