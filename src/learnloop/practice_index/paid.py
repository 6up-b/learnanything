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
  cap. An unknown price fails closed unless the owner supplies one. A metered
  chat ``complete`` may send one JSON-repair request after an invalid first
  answer, so each call reserves twice its estimate; reported usage reconciles
  upward and never refunds.

Every call is admitted by ``SpendBudget.request`` before it is sent, and its
receipts carry the caps plus a ``practice_index`` block naming the task,
billing, cost basis, prompt version and input hash.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
import json
from typing import Any, Literal

from pydantic import BaseModel, ValidationError

from learnloop.ai.errors import AIInterrupted, AIInvalidOutput, AIProviderUnavailable
from learnloop.ai.execution import generation_limit, observe_model_calls
from learnloop.ai.routing import MANUAL_PROVIDER, AITask, provider_for_task, ready_client_for_task
from learnloop.ai.spend import SpendBudget, SpendEstimate
from learnloop.ai.transport import STRUCTURED_COMPLETION, execute_structured_operation
from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault


Billing = Literal["subscription", "metered"]
SUBSCRIPTION_PROFILE_TYPES = frozenset({"codex_sdk", "http", "http_adapter"})
#: Framing allowance for system prompts and transport envelopes, in tokens.
FRAMING_TOKENS = 512
#: A metered structured completion may send one JSON-repair request.
METERED_REQUESTS_PER_CALL = 2


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

    @property
    def available(self) -> bool:
        return self.provider not in (None, "", MANUAL_PROVIDER)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def plan_route(vault: LoadedVault, task: AITask, client: Any | None = None) -> PaidRoute:
    """The route a paid role will use: an injected client, or ai.routing.<task>."""
    providers = vault.config.ai.providers
    if client is not None:
        provider = getattr(client, "provider_name", None) or "injected"
        profile = providers.get(provider)
        profile_type = getattr(client, "provider_type", None) or (profile.type if profile else None)
        model = getattr(client, "model", None) or (getattr(profile, "model", None) if profile else None)
        return PaidRoute(task, provider, profile_type, model, billing_for(profile_type))
    selection = provider_for_task(vault.config, task)
    provider = selection.provider_name or None
    if provider in (None, MANUAL_PROVIDER):
        return PaidRoute(task, None, None, None, "metered")
    profile = providers.get(provider)
    profile_type = profile.type if profile is not None else None
    model = getattr(profile, "model", None) if profile is not None else None
    return PaidRoute(task, provider, profile_type, model, billing_for(profile_type))


def resolve_client(vault: LoadedVault, route: PaidRoute) -> tuple[Any | None, str | None]:
    """Build the planned route's client, pinned: no silent fallback to another model."""
    if not route.available:
        return None, f"No provider is routed for {route.task}; set ai.routing.{route.task} or ai.active_provider."
    resolved = ready_client_for_task(vault.root, vault.config, route.task, explicit=route.provider)
    if not resolved.ready or resolved.client is None:
        return None, resolved.runtime.message or f"{route.provider} is not ready"
    if not resolved.client.supports(STRUCTURED_COMPLETION):
        return None, f"{route.provider} cannot run structured completions"
    return resolved.client, None


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
    resolved_models: set[str] = field(default_factory=set)

    def as_dict(self) -> dict[str, Any]:
        values = asdict(self)
        values["resolved_models"] = sorted(self.resolved_models)
        return values


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

    def call(self, client: Any, *, purpose: str, prompt: str,
             result_model: type[BaseModel], output_tokens: int,
             metadata: Mapping[str, Any], candidates: int = 0, pairs: int = 0,
             validate: Callable[[Any], Any] | None = None) -> Any:
        """One logical call, retried on provider failure within the retry cap.

        ``validate`` may raise ``AIInvalidOutput`` for a semantically unusable
        answer; it is then retried like a provider failure.
        """
        tokens = estimated_call_tokens(prompt, result_model, output_tokens)
        attempt = 0
        while True:
            estimate = self.estimate(
                tokens, candidates=0 if attempt else candidates,
                pairs=0 if attempt else pairs, retries=1 if attempt else 0,
            )
            events: list[dict[str, Any]] = []
            try:
                with self.budget.request(estimate) as charge:
                    try:
                        with observe_model_calls(self._observer(metadata, events)), \
                                generation_limit(output_tokens):
                            raw = execute_structured_operation(
                                client, purpose=purpose, prompt=prompt, result_model=result_model,
                            )
                    finally:
                        self._reconcile(charge, tokens, events)
                try:
                    result = result_model.model_validate(
                        raw.model_dump(mode="json") if isinstance(raw, BaseModel) else raw
                    )
                except ValidationError as exc:
                    raise AIInvalidOutput(f"{purpose} returned an invalid {result_model.__name__}") from exc
                return validate(result) if validate is not None else result
            except AIInterrupted:
                raise
            except AIProviderUnavailable:
                if self.budget.used.retries >= self.budget.caps.max_retries:
                    raise
                attempt += 1

    def _observer(self, metadata: Mapping[str, Any], events: list[dict[str, Any]]):
        declared_block = {
            **metadata,
            "task": self.route.task,
            "billing": self.route.billing,
            "cost_basis": "estimated_only" if self.subscription else "metered_estimate",
            "price_per_million": self.price,
            "requests_reserved_per_call": None if self.subscription else METERED_REQUESTS_PER_CALL,
        }

        def observe(action: str, event: dict[str, Any]) -> None:
            if action == "start" and event.get("parent_call_id") is None:
                declared = json.loads(event.get("budget_json") or "{}")
                declared["practice_index"] = declared_block
                event = {**event, "budget_json": json.dumps(declared, sort_keys=True, default=str)}
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
    "FRAMING_TOKENS",
    "METERED_REQUESTS_PER_CALL",
    "SUBSCRIPTION_PROFILE_TYPES",
    "PaidCalls",
    "PaidRoute",
    "billing_for",
    "estimated_call_tokens",
    "plan_route",
    "resolve_client",
]
