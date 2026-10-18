"""The feature audit (spec_adaptive_difficulty_v1 §7.2, §10.3; AD1, switch ``feature_audit``).

After an item revision is prepared for the pool (and in the owner-run
backfill), one Tier-1-style Decider judgment per audited dimension of the
launch task-feature schema (``p1_launch@1``: ``complexity``, ``transfer``,
``scaffolding``, ``span``, ``response``) reads the item stem and reference
answer only: never learner data, never held-out text (a protected item is
not audited, A8, and the predicate is read again before each request and
each record: :mod:`learnloop.adaptive_difficulty.sending`, Codex re-review
F11). Each dimension is a typed choice over its vocabulary; the
argmax decides and a tie is no answer; the distribution is logged in
``judgment_ledger`` (task ``ad_feature_audit``, version
``ad-feature-audit-v1``), one row per dimension, left the revision's
``content_hash`` (the ``practice_item_snapshots`` serialization, migration
164). A dimension the Decider leaves unanswered (unavailable, refused, failed
or tied) goes to the LLM judge on ``ai.routing.ad_feature_audit``, recorded as
such (judge ``llm``, the Decider's status and row in the rationale). With
``[decider_routes] ad_feature_audit`` off the LLM judges every dimension.

**The canonical audit** of a revision, per dimension and audit version, is
the earliest judgment that answered (:func:`canonical_audits`). A later run of
the same version never replaces it (:func:`audit_revision` asks only the
dimensions still unanswered); a new audit version is a change of persisted
meaning (§7.5). An edited item is a new revision with its own audit.

Audits are judgments, never evidence: nothing serving, scoring, scheduling or
certification reads them in AD1 (serve inputs freeze the ones answered before
a serve, §7.5).
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from learnloop.ai.decisions import ChoiceQuestion, choice_probabilities
from learnloop.ai.errors import AIInterrupted, AIInvalidOutput, AIProviderUnavailable
from learnloop.ai.execution import content_key
from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendLimitExceeded
from learnloop.ai.transport import render_structured_prompt
from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.stores import ad_receipts as store
from learnloop.db.stores.judgments import append_judgment

from learnloop.adaptive_difficulty import sending
from learnloop.adaptive_difficulty import spend as ad_spend
from learnloop.adaptive_difficulty.protection import guard
from learnloop.adaptive_difficulty.sending import ProtectedContent, SendGuard, StaleSnapshot, refusal_status
from learnloop.adaptive_difficulty.switches import feature_audit_enabled

LOG = logging.getLogger(__name__)

TASK = "ad_feature_audit"
VERSION = "ad-feature-audit-v1"
LEFT_KIND = "practice_item_revision"
RIGHT_KIND = "dimension"
#: The LLM judge's route (``ai.routing.ad_feature_audit``) and the Decider's.
LLM_ROUTE = "ad_feature_audit"
DECIDER_ROUTE = "tier1_decider"
SCHEMA = "p1_launch@1"
DIMENSIONS = ("complexity", "transfer", "scaffolding", "span", "response")
#: Each audited dimension's vocabulary (``substrate.activity_patterns``'s
#: launch schema; ``complexity`` is the ordinal 0-4 as text options).
VOCABULARY: dict[str, tuple[str, ...]] = {
    "complexity": ("0", "1", "2", "3", "4"),
    "transfer": ("same_context", "near", "far", "novel_combination"),
    "scaffolding": ("none", "cue", "partial", "worked"),
    "span": ("atomic", "single_step", "multi_step", "whole_task"),
    "response": ("recognize", "short_constructed", "long_constructed", "structured_steps", "performance"),
}
_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "complexity": {
        "0": "One fact or definition, nothing to combine.",
        "1": "Two ideas or one short manipulation.",
        "2": "A few steps or ideas that must be combined.",
        "3": "Many interacting steps or ideas.",
        "4": "A long chain with several interacting parts, exam-level.",
    },
    "transfer": {
        "same_context": "The same setting and wording the topic is taught in.",
        "near": "A slightly changed setting or representation.",
        "far": "A different setting where the idea must be recognized.",
        "novel_combination": "The idea combined with others in a new way.",
    },
    "scaffolding": {
        "none": "No help in the question: the learner starts from nothing.",
        "cue": "A cue or reminder that points at the idea.",
        "partial": "Part of the solution or a structure is given.",
        "worked": "A worked solution is given to follow or complete.",
    },
    "span": {
        "atomic": "One atomic recall or recognition.",
        "single_step": "One step of reasoning or computation.",
        "multi_step": "Several connected steps.",
        "whole_task": "A whole task from setup to answer.",
    },
    "response": {
        "recognize": "Choose or recognize an answer (selected response).",
        "short_constructed": "Write a short answer.",
        "long_constructed": "Write a long answer or explanation.",
        "structured_steps": "Write a structured sequence of steps or a derivation.",
        "performance": "Perform or produce a complete artifact.",
    },
}
_INSTRUCTIONS = {
    "complexity": "How complex is this practice question: how many ideas or steps must be combined to answer it?",
    "transfer": "How far is this question's setting from the one its topic is taught in?",
    "scaffolding": "How much help does the question itself give the learner?",
    "span": "How much of a task does the question ask for?",
    "response": "What kind of response does the question ask for?",
}
_PREAMBLE = ("Judge only from the question and its reference answer below, as written. Say how the question is "
             "built, not how hard it is for anyone.")
#: One audit's paid-call bounds (the ask, a retry): runaway-loop bounds, not money.
_CAPS = dict(max_candidates=0, max_pairs=0, max_retries=1, max_calls=2, max_total_tokens=60_000)


def item_revision(item: Any) -> tuple[str, str]:
    """``(content_hash, item_json)``: the revision's ``practice_item_snapshots`` serialization.

    The same full-item serialization the scheduler's decision features write
    (``scheduling.scheduler``'s snapshot of a scored revision; a test pins the
    two equal), so one revision has one hash whichever path stored it."""

    item_json = json.dumps(item.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(item_json.encode("utf-8")).hexdigest(), item_json


def _answer_text(item: Any) -> str:
    expected = getattr(item, "expected_answer", "")
    return expected if isinstance(expected, str) else json.dumps(expected, sort_keys=True, ensure_ascii=False)


def audit_state(item: Any) -> dict[str, Any]:
    """What the audit reads: the stem and the reference answer, nothing else."""

    return {"question": str(item.prompt), "reference_answer": _answer_text(item), "schema": SCHEMA}


def question_for(dimension: str) -> ChoiceQuestion:
    return ChoiceQuestion(
        instructions=f"{_INSTRUCTIONS[dimension]} {_PREAMBLE}",
        options={value: _DESCRIPTIONS[dimension][value] for value in VOCABULARY[dimension]},
    )


class FeatureAuditV1(WireModel):
    """The LLM judge's answer: one value per asked dimension (null: cannot tell)."""

    complexity: Literal["0", "1", "2", "3", "4"] | None = None
    transfer: Literal["same_context", "near", "far", "novel_combination"] | None = None
    scaffolding: Literal["none", "cue", "partial", "worked"] | None = None
    span: Literal["atomic", "single_step", "multi_step", "whole_task"] | None = None
    response: Literal["recognize", "short_constructed", "long_constructed", "structured_steps",
                      "performance"] | None = None


def llm_prompt(item: Any, dimensions: Sequence[str]) -> str:
    return render_structured_prompt("Read how a practice question is built", VERSION, {
        "instructions": (
            f"{_PREAMBLE} For each dimension asked, return exactly one of its options, or null if the question "
            "does not let you tell. Leave the dimensions not asked null."
        ),
        "dimensions": {name: {"question": _INSTRUCTIONS[name], "options": _DESCRIPTIONS[name]}
                       for name in dimensions},
        "state": audit_state(item),
    })


@dataclass
class AuditOutcome:
    """One revision's audit run. ``status``: audited | current | disabled |
    protected | not_found | failed | planned."""

    status: str
    practice_item_id: str
    content_hash: str | None = None
    answered: dict[str, str] = field(default_factory=dict)
    judges: dict[str, str] = field(default_factory=dict)
    unanswered: list[str] = field(default_factory=list)
    decider_status: str | None = None
    llm_status: str | None = None
    judgment_ids: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value not in (None, [], {})}


def canonical_audits(connection: Any, content_hash: str, *, as_of: str | None = None,
                     version: str = VERSION) -> dict[str, dict[str, Any]]:
    """Per dimension, the revision's canonical audit: the earliest answered judgment.

    ``as_of`` limits it to judgments written no later than that instant (a
    historical resolution, §7.5)."""

    if not store.has_table(connection, "judgment_ledger"):
        return {}
    rows = connection.execute(
        "SELECT id, right_id, verdict, judge, created_at FROM judgment_ledger WHERE task = ? AND prompt_version = ? "
        "AND left_kind = ? AND left_id = ? AND right_kind = ? ORDER BY created_at, rowid",
        (TASK, version, LEFT_KIND, content_hash, RIGHT_KIND),
    ).fetchall()
    limit = parse_utc(as_of) if as_of else None
    found: dict[str, dict[str, Any]] = {}
    for row in rows:
        dimension, verdict = str(row[1]), str(row[2])
        if dimension in found or verdict not in VOCABULARY.get(dimension, ()):
            continue
        if limit is not None:
            written = parse_utc(str(row[4])) if row[4] else None
            if written is None or written > limit:
                continue
        found[dimension] = {"judgment_id": str(row[0]), "value": verdict, "judge": str(row[3]),
                            "created_at": str(row[4])}
    return found


def _append(repository: Any, *, content_hash: str, item_id: str, dimension: str, judge: str, verdict: str,
            model: str, input_hash: str, score: float | None, rationale: Mapping[str, Any], now: str,
            admit: Callable[[], None] | None = None) -> str:
    with repository.atomic():
        if admit is not None:
            # The record admission, inside the write (fix round 5, V1).
            admit()
        return append_judgment(
            repository.connection(), task=TASK, left_kind=LEFT_KIND, left_id=content_hash, right_kind=RIGHT_KIND,
            right_id=dimension, judge=judge, judge_model=model or "unknown", prompt_version=VERSION,
            input_hash=input_hash, verdict=verdict, score=score, created_at=now,
            rationale=json.dumps({"practice_item_id": item_id, **dict(rationale)}, sort_keys=True, default=str),
        )


def _decider_client(vault: Any, factory: Callable[[], Any] | None) -> Any:
    if factory is not None:
        return factory()
    if ad_spend.models_off():
        return None
    from learnloop.decider_judgments import client_for

    return client_for(vault.root, vault.config)


def _llm_client(vault: Any, client: Any | None) -> tuple[Any | None, str | None]:
    from learnloop.practice_index.paid import plan_route, resolve_client

    if client is not None:
        return client, None
    if ad_spend.models_off():
        return None, "models_off"
    return resolve_client(vault, plan_route(vault, LLM_ROUTE))  # type: ignore[arg-type]


def _remaining(repository: Any, content_hash: str) -> list[str]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        done = canonical_audits(connection, content_hash)
    return [dimension for dimension in DIMENSIONS if dimension not in done]


def audit_revision(vault: Any, repository: Any, item: Any, *, decider_factory: Callable[[], Any] | None = None,
                   llm_client: Any | None = None, clock: Clock | None = None,
                   protected: Any = None, fence: Any = None,
                   live_vault: Callable[[], Any] | None = None) -> AuditOutcome:
    """Audit one item revision: the dimensions it has no canonical audit for.

    ``item`` is the revision itself (a current item, or a snapshot the
    backfill reads); a protected revision is never audited (A8; Codex review
    F1: the revision's own source references are checked, not only the
    current item's id). The work runs under the revision's durable claim
    (:mod:`learnloop.adaptive_difficulty.claims`; Codex review F5, F6): a
    revision another worker is auditing is ``busy``; the claim's holder
    re-reads the canonical audits before asking, so a revision is paid for
    once; and with a background job's ``fence`` nothing more is asked or
    written once its vault is switched or closed (``stale``).

    Never raises for a model failure: what the Decider leaves unanswered goes
    to the LLM judge, and what neither answers stays unanswered (retried by a
    later preparation or the backfill). A cancellation propagates.
    ``live_vault``: the provider of the vault loaded now, whose held-out
    predicate each request and record is checked against (fix round 4, V1)."""

    from learnloop.adaptive_difficulty.claims import LeaseLost, audit_key, claimed

    item_id = str(getattr(item, "id", ""))
    outcome = AuditOutcome(status="disabled", practice_item_id=item_id)
    if not feature_audit_enabled(vault.config):
        return outcome
    if guard(vault, repository, protected).covers(item):
        outcome.status = "protected"
        return outcome
    content_hash, item_json = item_revision(item)
    outcome.content_hash = content_hash
    if not _remaining(repository, content_hash):
        outcome.status = "current"
        return outcome
    try:
        with claimed(repository, audit_key(content_hash), fence=fence) as worker:
            if worker is None:
                outcome.status = "busy"
                return outcome
            # Re-read under the claim: another worker may have finished it.
            remaining = _remaining(repository, content_hash)
            if not remaining:
                outcome.status = "current"
                return outcome
            # Today's predicate before each request and each record, never the
            # caller's earlier one (Codex re-review F11: the backfill and a
            # preparation compute theirs once for many revisions).
            send = SendGuard(vault, repository, items=[item], protected=protected, live_vault=live_vault)
            _audit(vault, worker, item, item_json, content_hash, remaining, outcome,
                   decider_factory=decider_factory, llm_client=llm_client, clock=clock, send=send)
    except ProtectedContent as exc:
        # Refused before a request or a record: what was already recorded
        # stays (it was recorded while the revision was not protected).
        # ``stale`` (a reload under the check) is retryable, never settled
        # work; ``protected`` is held-out content (fix round 6, V3).
        outcome.status = refusal_status(exc)
        outcome.unanswered = [dimension for dimension in DIMENSIONS if dimension not in outcome.answered]
    except LeaseLost:
        outcome.status = "stale"
    return outcome


def _audit(vault: Any, worker: Any, item: Any, item_json: str, content_hash: str, remaining: list[str],
           outcome: AuditOutcome, *, decider_factory: Callable[[], Any] | None, llm_client: Any | None,
           clock: Clock | None, send: SendGuard) -> None:
    from learnloop.adaptive_difficulty.claims import LeaseLost

    item_id = outcome.practice_item_id
    repository = worker.repository
    # The audited revision is kept, so a later reader (level credit, AD4)
    # finds the content its audit read.
    with repository.atomic():
        store.insert_item_snapshot(repository.connection(), content_hash_value=content_hash,
                                   practice_item_id=item_id, item_json=item_json, created_at=utc_now_iso(clock))
    state = audit_state(item)
    envelope = ad_spend.ad_envelope(vault, worker.base, clock=clock)
    pending = list(remaining)
    decider_rows: dict[str, tuple[str, str]] = {}
    from learnloop import decider_judgments

    if decider_judgments.enabled(vault.config, TASK):
        questions = {dimension: question_for(dimension) for dimension in remaining}
        model = "unavailable"
        status = "ok"
        distributions: dict[str, dict[str, float]] = {}
        try:
            worker.require_live()
            client = _decider_client(vault, decider_factory)
            if client is None:
                raise AIProviderUnavailable("Decider unavailable")
            model = str(getattr(client, "model", None) or "unknown")
            result = sending.ask_decider(
                send, client, config=vault.config, repository=repository, task=TASK, state=state,
                questions=questions, owner_id=content_hash, route=DECIDER_ROUTE, question_set_version=VERSION,
                envelope=envelope,
            )
            model = str(result.model or model)
            distributions = {name: choice_probabilities(result.answers[name], question)
                             for name, question in questions.items()}
        except ProtectedContent as exc:
            outcome.decider_status = refusal_status(exc)
            raise
        except (AIInterrupted, LeaseLost):
            raise
        except SpendLimitExceeded:
            status = "refused"
        except AIProviderUnavailable:
            status = "unavailable"
        except Exception:  # noqa: BLE001 - a failed Decider hands the dimensions to the LLM
            LOG.warning("feature audit: the Decider failed for %s", item_id, exc_info=True)
            status = "failed"
        outcome.decider_status = status
        try:
            # Nothing is recorded once the revision is protected (F11).
            generation = send.check("recording the Decider's audit")
        except ProtectedContent as exc:
            outcome.decider_status = refusal_status(exc)
            raise

        def admit_decider() -> None:
            try:
                send.confirm(generation, "recording the Decider's audit")
            except ProtectedContent as exc:
                outcome.decider_status = refusal_status(exc)
                raise

        for dimension in remaining:
            question = questions[dimension]
            probabilities = distributions.get(dimension, {})
            choice = decider_judgments.argmax(probabilities) if status == "ok" else None
            verdict = choice or ("tied" if status == "ok" else status)
            input_hash = content_key({"state": state, "question": question.wire(), "task": TASK})
            judgment_id = _append(
                repository, content_hash=content_hash, item_id=item_id, dimension=dimension, judge="decider",
                verdict=verdict, model=model, input_hash=input_hash,
                score=probabilities.get(choice) if choice else None,
                rationale={"status": "ok" if choice else verdict, "probabilities": probabilities,
                           "dimension": dimension, "schema": SCHEMA},
                now=utc_now_iso(clock), admit=admit_decider,
            )
            outcome.judgment_ids.append(judgment_id)
            if choice is not None:
                outcome.answered[dimension] = choice
                outcome.judges[dimension] = "decider"
                pending.remove(dimension)
            else:
                decider_rows[dimension] = (judgment_id, verdict)
    if pending:
        worker.require_live()
        _llm_fallback(vault, repository, item, pending, decider_rows, outcome, envelope=envelope,
                      client=llm_client, content_hash=content_hash, clock=clock, send=send)
    outcome.unanswered = [dimension for dimension in remaining if dimension not in outcome.answered]
    outcome.status = "audited" if outcome.answered else "failed"


def _llm_fallback(vault: Any, repository: Any, item: Any, dimensions: list[str],
                  decider_rows: Mapping[str, tuple[str, str]],
                  outcome: AuditOutcome, *, envelope: Any, client: Any | None, content_hash: str,
                  clock: Clock | None, send: SendGuard) -> None:
    from learnloop.practice_index.paid import plan_route

    route = plan_route(vault, LLM_ROUTE, client)  # type: ignore[arg-type]
    subscription = route.billing == "subscription"
    price = vault.config.adaptive_difficulty.price_per_million
    resolved, problem = _llm_client(vault, client)
    if resolved is None:
        outcome.llm_status = "unavailable"
        LOG.info("feature audit: no LLM judge for %s (%s)", outcome.practice_item_id, problem)
        return
    if not subscription and price is None:
        outcome.llm_status = "unpriced"
        return
    prompt = llm_prompt(item, dimensions)
    try:
        answer, calls = sending.ask_llm(
            send, route, resolved, price=price, repository=repository, caps=_CAPS,
            owner_kind=ad_spend.AUDIT_OWNER_KIND, owner_id=content_hash, purpose=TASK, prompt=prompt,
            result_model=FeatureAuditV1, envelope=envelope,
            metadata={"practice_item_id": outcome.practice_item_id, "content_hash": content_hash,
                      "prompt_version": VERSION})
    except ProtectedContent as exc:
        outcome.llm_status = refusal_status(exc)
        raise
    except AIInterrupted:
        raise
    except SpendLimitExceeded:
        outcome.llm_status = "refused"
        return
    except (AIProviderUnavailable, AIInvalidOutput, TimeoutError):
        if send.refused is not None:
            # A transport that reported the guard's refusal as its own failure.
            outcome.llm_status = "stale" if send.stale else "protected"
            raise (StaleSnapshot if send.stale else ProtectedContent)(send.refused) from None
        outcome.llm_status = "failed"
        return
    model = str(calls.last_resolved_model or getattr(resolved, "model", None) or route.model or "unknown")
    try:
        # Nothing is recorded once the revision is protected (F11).
        generation = send.check("recording the LLM's audit")
    except ProtectedContent as exc:
        outcome.llm_status = refusal_status(exc)
        raise

    def admit_llm() -> None:
        try:
            send.confirm(generation, "recording the LLM's audit")
        except ProtectedContent as exc:
            outcome.llm_status = refusal_status(exc)
            raise

    outcome.llm_status = "ok"
    values = answer.model_dump(mode="json")
    now = utc_now_iso(clock)
    with repository.atomic():
        admit_llm()
        owner_key = f"{TASK}:{content_hash}:{','.join(dimensions)}"
        store.insert_payload(repository.connection(), owner_key=owner_key, forecaster=TASK, kind="request",
                             content={"prompt": prompt}, created_at=now)
        store.insert_payload(repository.connection(), owner_key=owner_key, forecaster=TASK, kind="response",
                             content=values, created_at=now)
    for dimension in dimensions:
        value = values.get(dimension)
        if value not in VOCABULARY[dimension]:
            continue
        judgment_id = _append(
            repository, content_hash=content_hash, item_id=outcome.practice_item_id, dimension=dimension,
            judge="llm", verdict=str(value), model=model,
            input_hash=content_key({"prompt": prompt, "task": TASK, "dimension": dimension}), score=None,
            rationale={"fallback": decider_rows[dimension][1] if dimension in decider_rows else "decider_off",
                       "decider_judgment_id": decider_rows[dimension][0] if dimension in decider_rows else None,
                       "dimension": dimension, "schema": SCHEMA},
            now=utc_now_iso(clock), admit=admit_llm,
        )
        outcome.judgment_ids.append(judgment_id)
        outcome.answered[dimension] = str(value)
        outcome.judges[dimension] = "llm"


__all__ = [
    "AuditOutcome",
    "DIMENSIONS",
    "FeatureAuditV1",
    "LEFT_KIND",
    "RIGHT_KIND",
    "TASK",
    "VERSION",
    "VOCABULARY",
    "audit_revision",
    "audit_state",
    "canonical_audits",
    "item_revision",
    "llm_prompt",
    "question_for",
]
