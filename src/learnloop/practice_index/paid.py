"""Paid LLM calls for the practice index, admitted one by one under spend caps.

Two billing modes (Slice A §5 rule 6):

* **subscription** (Codex: ``codex_sdk`` and the Codex HTTP adapter) runs on
  the owner's ChatGPT subscription. It has no marginal dollar cost and its
  app-server turns expose no physical-request bound, so no token or dollar cap
  applies. Tokens and cost are still estimated, from reported usage when the
  turn reports it and from the input + output estimate otherwise, and are
  labelled ``estimated_only``. Call, candidate, pair and retry caps still apply,
  so a runaway loop stops.
* **metered** (OpenRouter, OpenAI-compatible keys, anything else) keeps every
  cap. An unknown price fails closed unless the owner supplies one. Each
  admitted attempt runs under ``single_request()``: exactly one physical
  request, with no hidden transport retry and no hidden JSON repair. A retry or
  repair is a new attempt, admitted and charged on its own under the retry
  cap. A metered transport that cannot bound its physical requests is refused
  before any request, and a second physical request inside one admitted
  attempt is stopped before it is sent. Reported usage reconciles upward and
  never refunds.

Every attempt is admitted by ``SpendBudget.request`` before it is sent, and its
receipts carry the caps plus a ``practice_index`` block naming the task,
billing, cost basis, prompt version and input hash.

A validated answer is checkpointed (``model_work_checkpoints``) under its full
request identity before the caller writes it anywhere, so a crash or a failed
write after a paid response never pays for it again: the rerun recovers the
answer and materializes it idempotently.

The completed receipt commits before that checkpoint, so a crash or a failed
checkpoint write between the two leaves the paid answer only on its receipt.
Each root receipt therefore names its request key (and the caller's context)
in its ``practice_index`` block, written before the request is sent. Before
paying, a call with no checkpoint looks for a completed receipt with the same
request identity (request key, prompt hash, schema hash and output budget)
whose answer still validates; it recovers that answer and checkpoints it.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import closing, nullcontext
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import sqlite3
import time
from typing import Any, Literal

from pydantic import BaseModel, ValidationError

from learnloop.ai.errors import AIInterrupted, AIInvalidOutput, AIOutputTruncated, AIProviderUnavailable, AITurnTimeout
from learnloop.ai.execution import (
    content_key,
    generation_limit,
    observe_model_calls,
    requested_reasoning_effort,
    single_request,
)
from learnloop.ai.output_budget import (
    TRUNCATION_RETRY_FACTOR,
    TruncationRetry,
    output_budget,
    output_ceiling,
    reasoning_effort,
)
from learnloop.ai.routing import MANUAL_PROVIDER, AITask, provider_for_task, ready_client_for_task
from learnloop.ai.spend import SpendBudget, SpendEstimate, SpendLimitExceeded
from learnloop.ai.transport import (
    BOUNDED_STRUCTURED_COMPLETION,
    STRUCTURED_COMPLETION,
    execute_structured_operation,
)
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.practice_index import completed_root_receipts
from learnloop.vault.models import LoadedVault


Billing = Literal["subscription", "metered"]
SUBSCRIPTION_PROFILE_TYPES = frozenset({"codex_sdk", "http", "http_adapter"})
#: Framing allowance for system prompts and transport envelopes, in tokens.
FRAMING_TOKENS = 512
#: Physical requests per admitted metered attempt (``single_request()``).
METERED_REQUESTS_PER_CALL = 1


class UnboundedTransport(AIProviderUnavailable):
    """A metered transport that cannot bound its physical requests."""


def transport_problem(route: PaidRoute, client: Any) -> str | None:
    """Why ``client`` cannot run this route's paid calls, or None.

    A metered route needs ``BOUNDED_STRUCTURED_COMPLETION``: one physical
    request per admitted attempt. Codex (subscription) is exempt by the owner's
    decision (Slice A §5 rule 6).
    """
    name = getattr(client, "provider_name", None) or route.provider or "the provider"
    if not client.supports(STRUCTURED_COMPLETION):
        return f"{name} cannot run structured completions"
    if route.billing == "metered" and not client.supports(BOUNDED_STRUCTURED_COMPLETION):
        return (f"{name} cannot bound physical requests; a metered route needs one request per "
                "admitted call (openai_chat or openrouter), or route the role to Codex.")
    return None


def billing_for(profile_type: str | None) -> Billing:
    return "subscription" if (profile_type or "").strip().lower() in SUBSCRIPTION_PROFILE_TYPES else "metered"


@dataclass(frozen=True)
class PaidRoute:
    """The planned route of one paid role; resolved without any network call."""

    task: AITask
    provider: str | None
    profile_type: str | None
    model: str | None
    billing: Billing
    #: The route's output budget (``learnloop.ai.output_budget``): every call
    #: on it asks for and reserves this many output tokens.
    output_tokens: int = output_budget(None)
    #: The route's requested reasoning effort (``ai.route_reasoning_effort``).
    reasoning_effort: str | None = None

    @property
    def available(self) -> bool:
        return self.provider not in (None, "", MANUAL_PROVIDER)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def plan_route(vault: LoadedVault, task: AITask, client: Any | None = None) -> PaidRoute:
    """The route a paid role will use: an injected client, or ai.routing.<task>."""
    providers = vault.config.ai.providers
    effort = reasoning_effort(vault.config, task)
    if client is not None:
        provider = getattr(client, "provider_name", None) or "injected"
        profile = providers.get(provider)
        profile_type = getattr(client, "provider_type", None) or (profile.type if profile else None)
        model = getattr(client, "model", None) or (getattr(profile, "model", None) if profile else None)
        return PaidRoute(task, provider, profile_type, model, billing_for(profile_type),
                         output_budget(vault.config, task, provider=provider), effort)
    selection = provider_for_task(vault.config, task)
    provider = selection.provider_name or None
    if provider in (None, MANUAL_PROVIDER):
        return PaidRoute(task, None, None, None, "metered", output_budget(vault.config, task), effort)
    profile = providers.get(provider)
    profile_type = profile.type if profile is not None else None
    model = getattr(profile, "model", None) if profile is not None else None
    return PaidRoute(task, provider, profile_type, model, billing_for(profile_type),
                     output_budget(vault.config, task, provider=provider), effort)


def resolve_client(vault: LoadedVault, route: PaidRoute) -> tuple[Any | None, str | None]:
    """Build the planned route's client, pinned: no silent fallback to another model."""
    if not route.available:
        return None, f"No provider is routed for {route.task}; set ai.routing.{route.task} or ai.active_provider."
    resolved = ready_client_for_task(vault.root, vault.config, route.task, explicit=route.provider)
    if not resolved.ready or resolved.client is None:
        return None, resolved.runtime.message or f"{route.provider} is not ready"
    problem = transport_problem(route, resolved.client)
    if problem is not None:
        return None, problem
    return resolved.client, None


def planning_repository(sqlite_path: Path, *, dry_run: bool) -> Repository:
    """The repository a paid batch command plans with.

    A dry run attaches read-only and never migrates, so planning an older
    database changes neither its schema nor its journal mode; tables it does
    not have yet read as empty. A real run opens (and migrates) as usual.
    """
    if not dry_run:
        return Repository(sqlite_path)
    if not Path(sqlite_path).exists():
        raise ValueError(f"No database at {sqlite_path}; open the vault once before planning.")
    return Repository.attach(sqlite_path, read_only=True)


def estimated_call_tokens(prompt: str, result_model: type[BaseModel], output_tokens: int) -> int:
    """UTF-8 bytes upper-bound ordinary tokenizer input; output is bounded."""
    schema = json.dumps(result_model.model_json_schema(), sort_keys=True)
    return len(prompt.encode("utf-8")) + len(schema.encode("utf-8")) + FRAMING_TOKENS + output_tokens


@dataclass
class UsageTotals:
    calls: int = 0
    receipts: int = 0
    reported_input_tokens: int = 0
    reported_output_tokens: int = 0
    reported_cost_usd: float = 0.0
    estimated_only_tokens: int = 0
    estimated_only_usd: float | None = 0.0
    #: Answers recovered (from a checkpoint or a receipt) instead of being paid for again.
    recovered: int = 0
    #: Of those, answers whose checkpoint never committed: recovered from the receipt.
    recovered_from_receipts: int = 0
    resolved_models: set[str] = field(default_factory=set)
    #: Truncated attempts (``finish_reason = length``), each logged as an event
    #: and retried once at double the budget (``learnloop.ai.output_budget``).
    truncations: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        values = asdict(self)
        values["resolved_models"] = sorted(self.resolved_models)
        return values


_MISSING = object()
CHECKPOINT_PREFIX = "practice_index:"


def checkpoint_key(route: PaidRoute, *, purpose: str, prompt: str,
                   result_model: type[BaseModel], output_tokens: int) -> str:
    """A paid answer's request identity: purpose, prompt, schema, output budget,
    provider and model (the identity its destination rows are keyed by)."""
    identity: dict[str, Any] = {
        "purpose": purpose, "prompt": prompt, "schema": result_model.model_json_schema(),
        "output_tokens": output_tokens, "provider": route.provider, "model": route.model,
    }
    if route.reasoning_effort:
        # A requested effort changes what the model produces; unset keeps the
        # keys of every answer checkpointed before efforts existed.
        identity["reasoning_effort"] = route.reasoning_effort
    return CHECKPOINT_PREFIX + content_key(identity)


_UNUSABLE = (KeyError, TypeError, ValueError, ValidationError, AIInvalidOutput)


def receipt_answer(
    connection: sqlite3.Connection, route: PaidRoute, *, purpose: str, prompt: str,
    result_model: type[BaseModel], output_tokens: int,
    validate: Callable[[Any], Any] | None = None,
) -> tuple[Any, BaseModel, dict[str, Any]] | None:
    """A paid answer left only on its completed receipt, or None.

    The receipt must carry the same request identity: the request key it
    declared before the request was sent, the prompt hash, the schema hash and
    the output budget. Its answer must parse and pass ``validate``; a receipt
    whose answer fails (an attempt that was retried) is skipped. Newest first.
    Returns ``(value, answer, receipt)``.
    """
    key = checkpoint_key(route, purpose=purpose, prompt=prompt, result_model=result_model,
                         output_tokens=output_tokens)
    schema_hash = content_key(result_model.model_json_schema())
    receipts = completed_root_receipts(connection, purpose=purpose, prompt_hash=content_key(prompt))
    # A truncation retry ran the same request with a larger budget: double,
    # or less when the transport's ceiling held it.
    for receipt in receipts:
        budget = receipt["output_budget_tokens"]
        if (receipt["declared"].get("request_key") != key or receipt["schema_hash"] != schema_hash
                or not isinstance(budget, int)
                or not output_tokens <= budget <= output_tokens * TRUNCATION_RETRY_FACTOR):
            continue
        try:
            answer = result_model.model_validate_json(receipt["output_text"])
            value = validate(answer) if validate is not None else answer
        except _UNUSABLE:
            continue
        return value, answer, receipt
    return None


def receipt_answers(connection: sqlite3.Connection, *, purpose: str) -> list[dict[str, Any]]:
    """Every completed root receipt of one paid role that declared a request key
    (newest first): for roles whose rerun cannot rebuild the request, such as
    query-writer batches, which a rerun plans differently."""
    return [receipt for receipt in completed_root_receipts(connection, purpose=purpose)
            if str(receipt["declared"].get("request_key") or "").startswith(CHECKPOINT_PREFIX)]


class PaidCalls:
    """Serial paid calls for one command, under one ``SpendBudget``."""

    def __init__(self, *, route: PaidRoute, budget: SpendBudget,
                 price_per_million: float | None, repository: Repository | None,
                 owner_kind: str, owner_id: str):
        self.route = route
        self.budget = budget
        self.price = price_per_million
        self.repository = repository
        self.owner_kind = owner_kind
        self.owner_id = owner_id
        self.totals = UsageTotals(estimated_only_usd=0.0 if price_per_million is not None else None)
        self.last_resolved_model: str | None = None

    @property
    def subscription(self) -> bool:
        return self.route.billing == "subscription"

    def estimate(self, tokens: int, *, candidates: int = 0, pairs: int = 0,
                 calls: int = 1, retries: int = 0) -> SpendEstimate:
        """What the budget is charged before sending ``calls`` calls of ``tokens`` total."""
        if self.subscription:
            return SpendEstimate(candidates=candidates, pairs=pairs, retries=retries,
                                 calls=calls, total_tokens=0, estimated_usd=0.0)
        worst = tokens * METERED_REQUESTS_PER_CALL
        usd = worst * self.price / 1_000_000 if self.price is not None else (None if calls else 0.0)
        return SpendEstimate(candidates=candidates, pairs=pairs, retries=retries,
                             calls=calls, total_tokens=worst, estimated_usd=usd)

    def plan(self, token_counts: list[int], *, candidates: int = 0,
             pairs: int = 0) -> dict[str, Any]:
        """The dry-run view of a whole plan: the budget charge and the estimate."""
        tokens = sum(token_counts)
        estimate = self.estimate(tokens, candidates=candidates, pairs=pairs,
                                 calls=len(token_counts))
        return {
            "billing": self.route.billing,
            "cost_basis": "estimated_only" if self.subscription else "metered_estimate",
            "calls": len(token_counts),
            "estimated_tokens": tokens if self.subscription else estimate.total_tokens,
            "estimated_usd": (
                (tokens * self.price / 1_000_000 if self.price is not None else None)
                if self.subscription else estimate.estimated_usd
            ),
            "marginal_usd": 0.0 if self.subscription else estimate.estimated_usd,
            "budget_charge": asdict(estimate),
        }

    def report(self) -> dict[str, Any]:
        return {
            "route": self.route.as_dict(),
            "billing": self.route.billing,
            "cost_basis": "estimated_only" if self.subscription else "metered_estimate",
            "price_per_million": self.price,
            "charged": asdict(self.budget.used),
            "usage": self.totals.as_dict(),
        }

    def checkpoint_key(self, *, purpose: str, prompt: str, result_model: type[BaseModel],
                       output_tokens: int) -> str:
        """The full request identity a paid answer is checkpointed under."""
        return checkpoint_key(self.route, purpose=purpose, prompt=prompt,
                              result_model=result_model, output_tokens=output_tokens)

    def call(self, client: Any, *, purpose: str, prompt: str,
             result_model: type[BaseModel], output_tokens: int,
             metadata: Mapping[str, Any], candidates: int = 0, pairs: int = 0,
             validate: Callable[[Any], Any] | None = None,
             context: Mapping[str, Any] | None = None,
             deadline: float | None = None) -> Any:
        """One logical call, retried on provider failure within the retry cap.

        ``validate`` may raise ``AIInvalidOutput`` for a semantically unusable
        answer; it is then retried like a provider failure. A validated answer
        is checkpointed (with ``context``) before it is returned, and an
        existing checkpoint for the same request is returned without a request.

        ``deadline`` (a ``time.monotonic()`` value) time-boxes a live caller:
        each attempt's request carries the remaining time as its timeout (every
        transport enforces ``StructuredRequest.timeout_seconds``), and no attempt
        starts once it has passed (``AITurnTimeout``, never a retry).
        """
        key = self.checkpoint_key(purpose=purpose, prompt=prompt, result_model=result_model,
                                  output_tokens=output_tokens)
        recovered = self._recover(key, result_model, validate)
        if recovered is _MISSING:
            recovered = self._recover_receipt(key, purpose=purpose, prompt=prompt,
                                              result_model=result_model,
                                              output_tokens=output_tokens, validate=validate,
                                              context=context)
        if recovered is not _MISSING:
            return recovered
        problem = transport_problem(self.route, client)
        if problem is not None:
            raise UnboundedTransport(problem)
        truncation = TruncationRetry(output_tokens, role=purpose, provider=self.route.provider,
                                     model=self.route.model, owner_kind=self.owner_kind,
                                     owner_id=self.owner_id, ceiling=output_ceiling(client))
        attempt = 0
        while True:
            tokens = estimated_call_tokens(prompt, result_model, truncation.budget)
            timeout_seconds = None
            if deadline is not None:
                timeout_seconds = deadline - time.monotonic()
                if timeout_seconds <= 0:
                    raise AITurnTimeout(f"{purpose}: the time box ran out before the request")
            estimate = self.estimate(
                tokens, candidates=0 if attempt else candidates,
                pairs=0 if attempt else pairs, retries=1 if attempt else 0,
            )
            events: list[dict[str, Any]] = []
            try:
                with self.budget.request(estimate) as charge:
                    # Metered: exactly one physical request per admitted attempt.
                    bound = nullcontext() if self.subscription else single_request()
                    try:
                        with observe_model_calls(self._observer(metadata, events, key, context)), \
                                generation_limit(truncation.budget), truncation.receipts(), \
                                requested_reasoning_effort(self.route.reasoning_effort), bound:
                            raw = execute_structured_operation(
                                client, purpose=purpose, prompt=prompt, result_model=result_model,
                                timeout_seconds=timeout_seconds,
                            )
                    finally:
                        self._reconcile(charge, tokens, events)
                try:
                    result = result_model.model_validate(
                        raw.model_dump(mode="json") if isinstance(raw, BaseModel) else raw
                    )
                except ValidationError as exc:
                    raise AIInvalidOutput(f"{purpose} returned an invalid {result_model.__name__}") from exc
                value = validate(result) if validate is not None else result
                self._checkpoint(key, purpose, result, context)
                return value
            except AIInterrupted:
                raise
            except AIOutputTruncated:
                # Never accepted: logged, then retried once at double the budget
                # (admitted and charged like any retry), else the call fails.
                allowed = self.budget.used.retries < self.budget.caps.max_retries
                retry = truncation.after_truncation(allowed=allowed)
                self.totals.truncations.append(truncation.events[-1])
                if not retry:
                    raise
                attempt += 1
            except AIProviderUnavailable:
                if self.budget.used.retries >= self.budget.caps.max_retries:
                    raise
                attempt += 1

    def _recover(self, key: str, result_model: type[BaseModel],
                 validate: Callable[[Any], Any] | None) -> Any:
        if self.repository is None:
            return _MISSING
        saved = self.repository.model_checkpoint(key)
        if saved is None:
            return _MISSING
        try:
            result = result_model.model_validate(saved["result"]["answer"])
            value = validate(result) if validate is not None else result
        except (KeyError, TypeError, ValidationError, AIInvalidOutput):
            # Write-once checkpoints: an unusable one would block every rerun.
            self.repository.discard_model_checkpoint(key)
            return _MISSING
        self.totals.recovered += 1
        model = saved["result"].get("resolved_model")
        self.last_resolved_model = str(model) if model else None
        if self.last_resolved_model:
            self.totals.resolved_models.add(self.last_resolved_model)
        return value

    def _recover_receipt(self, key: str, *, purpose: str, prompt: str,
                         result_model: type[BaseModel], output_tokens: int,
                         validate: Callable[[Any], Any] | None,
                         context: Mapping[str, Any] | None) -> Any:
        """A paid answer whose receipt committed but whose checkpoint did not.

        It is checkpointed now, so the caller materializes it like any other
        recovered answer (its destination writes are idempotent)."""
        if self.repository is None:
            return _MISSING
        with closing(connect(self.repository.sqlite_path, read_only=True)) as connection:
            found = receipt_answer(connection, self.route, purpose=purpose, prompt=prompt,
                                   result_model=result_model, output_tokens=output_tokens,
                                   validate=validate)
        if found is None:
            return _MISSING
        value, answer, receipt = found
        self.last_resolved_model = str(receipt["resolved_model"]) if receipt["resolved_model"] else None
        if self.last_resolved_model:
            self.totals.resolved_models.add(self.last_resolved_model)
        self._checkpoint(key, purpose, answer, context)
        self.totals.recovered += 1
        self.totals.recovered_from_receipts += 1
        return value

    def _checkpoint(self, key: str, purpose: str, result: BaseModel,
                    context: Mapping[str, Any] | None) -> None:
        if self.repository is None:
            return
        self.repository.save_model_checkpoint(key, purpose=purpose, result={
            "answer": result.model_dump(mode="json"),
            "resolved_model": self.last_resolved_model,
            "route": {"provider": self.route.provider, "model": self.route.model},
            "context": dict(context or {}),
        })

    def _observer(self, metadata: Mapping[str, Any], events: list[dict[str, Any]],
                  request_key: str, context: Mapping[str, Any] | None = None):
        declared_block = {
            **metadata,
            # Written before the request is sent: a completed receipt whose
            # checkpoint never committed is recoverable by this identity.
            "request_key": request_key,
            **({"context": dict(context)} if context else {}),
            "task": self.route.task,
            "billing": self.route.billing,
            "cost_basis": "estimated_only" if self.subscription else "metered_estimate",
            "price_per_million": self.price,
            "requests_reserved_per_call": None if self.subscription else METERED_REQUESTS_PER_CALL,
        }

        physical = [0]

        def observe(action: str, event: dict[str, Any]) -> None:
            if action == "start" and event.get("parent_call_id") is None:
                declared = json.loads(event.get("budget_json") or "{}")
                declared["practice_index"] = declared_block
                event = {**event, "budget_json": json.dumps(declared, sort_keys=True, default=str)}
            elif action == "start" and not self.subscription:
                # Raised before the request is sent: an admitted metered attempt
                # never carries a second physical request.
                physical[0] += 1
                if physical[0] > METERED_REQUESTS_PER_CALL:
                    raise SpendLimitExceeded(
                        "A metered transport tried a second physical request inside one "
                        "admitted call"
                    )
            if action == "finish":
                events.append(event)
            if self.repository is not None:
                self.repository.record_model_event(
                    action, event, owner_kind=self.owner_kind, owner_id=self.owner_id,
                )

        return observe

    def _reconcile(self, charge, tokens_estimate: int, events: list[dict[str, Any]]) -> None:
        self.totals.calls += 1
        self.totals.receipts += len(events)
        reported_in = [e.get("input_tokens") for e in events if e.get("input_tokens") is not None]
        reported_out = [e.get("output_tokens") for e in events if e.get("output_tokens") is not None]
        reported_cost = [float(e["cost"]) for e in events if e.get("cost") is not None]
        for event in events:
            if event.get("resolved_model"):
                self.last_resolved_model = str(event["resolved_model"])
                self.totals.resolved_models.add(self.last_resolved_model)
        reported = (sum(reported_in) + sum(reported_out)) if (reported_in or reported_out) else None
        self.totals.reported_input_tokens += sum(reported_in)
        self.totals.reported_output_tokens += sum(reported_out)
        self.totals.reported_cost_usd += sum(reported_cost)
        if self.subscription:
            used = reported if reported is not None else tokens_estimate
            self.totals.estimated_only_tokens += used
            if self.totals.estimated_only_usd is not None and self.price is not None:
                self.totals.estimated_only_usd += used * self.price / 1_000_000
            return
        cost = sum(reported_cost) if reported_cost else None
        if reported is not None and self.price is not None:
            cost = max(cost or 0.0, reported * self.price / 1_000_000)
        charge.reconcile(total_tokens=reported, estimated_usd=cost)


__all__ = [
    "CHECKPOINT_PREFIX",
    "FRAMING_TOKENS",
    "METERED_REQUESTS_PER_CALL",
    "SUBSCRIPTION_PROFILE_TYPES",
    "PaidCalls",
    "PaidRoute",
    "UnboundedTransport",
    "billing_for",
    "checkpoint_key",
    "estimated_call_tokens",
    "plan_route",
    "planning_repository",
    "receipt_answer",
    "receipt_answers",
    "resolve_client",
    "transport_problem",
]
