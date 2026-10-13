"""Per-route spend admission and usage accounting for one review run.

Every paid unit of work passes :meth:`ReviewSpend.request` BEFORE it is sent
(Slice A §5.6). One :class:`~learnloop.ai.spend.SpendBudget` holds the
command's caps:

* **metered routes** (OpenRouter, OpenAI keys, embeddings) admit EVERY
  physical request: the unit's first request is admitted up front, and each
  further one (a transport retry, a JSON repair or regeneration) is admitted
  as a retry when its ``model_call`` starts, before it is sent. Each carries
  its full token and dollar estimate; an unknown price fails closed unless the
  owner supplies one. The admitted output limit is handed to the transport
  (``generation_limit``), so the estimate bounds what a request may produce;
* **subscription routes** (Codex on the owner's ChatGPT subscription) have no
  marginal dollar cost (Slice A §5 rule 6): one logical request counts once
  against the call, candidate and retry caps, its physical requests are not
  bounded, and cancellation is still checked before each of them. Their
  tokens and an API-equivalent cost are estimated from reported usage and
  recorded as ``estimated_only``.

This mirrors the subscription rule the Slice A integration adds to
``ai/spend.py`` without touching that module (it is not on this branch's base);
M2 should switch to the shared ``SpendBudget(subscription=...)`` once both land.
"""

from __future__ import annotations

import time
from contextlib import ExitStack, contextmanager, nullcontext
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator

from learnloop.ai.execution import generation_limit, observe_model_calls
from learnloop.ai.spend import SpendBudget, SpendCancelled, SpendCaps, SpendCharge, SpendEstimate

SUBSCRIPTION_CLIENT_TYPES = frozenset({"codex_sdk", "http_adapter", "chatgpt_plan"})
ESTIMATED_ONLY = "estimated_only"
REPORTED = "reported"
#: Published per-million input price of the one Slice 1 embedding model.
KNOWN_PRICES_PER_MILLION = {"qwen/qwen3-embedding-8b": 0.01}
#: Bounded output allowances used in estimates (tokens). On a metered route
#: the admitted limit (this, or the profile's larger ``max_tokens``) is also
#: enforced on the transport, so it must leave room for reasoning tokens.
OUTPUT_ALLOWANCE = {
    "grading": 6_000,
    # mvp-0.15: the proof-like reading and the independent route check (a
    # full re-derivation, so the grader's allowance; review F3).
    "proof_check": 6_000,
    "diagnosis": 8_000,
    "diagnosis_judge": 4_000,
    "diagnosis_generator": 6_000,
    "embedding": 0,
}


def is_subscription_client(client: Any) -> bool:
    return getattr(client, "provider_type", None) in SUBSCRIPTION_CLIENT_TYPES


def admitted_output_limit(route: str, profile_max_tokens: Any) -> int:
    """The route allowance, or the profile's larger declared output limit."""

    allowance = OUTPUT_ALLOWANCE.get(route, 2_000)
    if not allowance:
        return 0
    declared = profile_max_tokens if isinstance(profile_max_tokens, int) and profile_max_tokens > 0 else 0
    return max(allowance, declared)


@dataclass
class RouteInfo:
    route: str
    provider: str | None
    model: str | None
    billing: str  # subscription | metered
    price_per_million: float | None
    price_source: str  # owner_override | known | unknown | subscription
    #: Output tokens one physical request is admitted with (and, metered,
    #: limited to on the transport).
    output_limit: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "route": self.route,
            "provider": self.provider,
            "model": self.model,
            "billing": self.billing,
            "price_per_million": self.price_per_million,
            "price_source": self.price_source,
            "output_limit": self.output_limit,
            "cost_basis": ESTIMATED_ONLY if self.billing == "subscription" else REPORTED,
        }


@dataclass
class CallUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    reasoning_tokens: int = 0
    cost: float | None = None
    calls: int = 0

    def add(self, event: dict[str, Any]) -> None:
        for key in ("input_tokens", "output_tokens", "cached_input_tokens", "reasoning_tokens"):
            value = event.get(key)
            if isinstance(value, (int, float)):
                setattr(self, key, getattr(self, key) + int(value))
        cost = event.get("cost")
        if isinstance(cost, (int, float)):
            self.cost = (self.cost or 0.0) + float(cost)


@dataclass
class _Unit:
    """One admitted unit of work and the physical requests seen inside it."""

    usage: CallUsage
    #: Called before every physical request after the first; may raise to
    #: refuse it (it is then never sent and no receipt is written).
    admit: Callable[[dict[str, Any]], None] | None = None
    physical: list[str] = field(default_factory=list)
    #: physical call id -> its own usage (for per-request reconciliation).
    by_call: dict[str, CallUsage] = field(default_factory=dict)


@dataclass
class UsageCollector:
    """Observes model calls: admits physical requests, forwards receipts, meters.

    A physical request is a ``model_call`` with a parent (the transport's
    per-request receipt under the logical operation); a unit whose transport
    reports none has only its root, which the unit's own admission covered.
    """

    sink: Callable[[str, dict[str, Any]], None] | None = None
    _current: _Unit | None = None
    _roots: set[str] = field(default_factory=set)

    def __call__(self, action: str, event: dict[str, Any]) -> None:
        unit = self._current
        if unit is not None and action == "start" and event.get("parent_call_id") is not None:
            call_id = str(event.get("id"))
            if unit.physical and unit.admit is not None:
                # Before the receipt and before the request: a refusal here
                # propagates out of model_call and nothing is sent.
                unit.admit(event)
            unit.physical.append(call_id)
            unit.by_call[call_id] = CallUsage()
        if self.sink is not None:
            try:
                self.sink(action, event)
            except Exception:  # noqa: BLE001 - receipts are telemetry, never fatal
                pass
        if unit is None:
            return
        if action == "start" and event.get("parent_call_id") is None:
            self._roots.add(str(event.get("id")))
            unit.usage.calls += 1
        if action == "finish":
            unit.usage.add(event)
            own = unit.by_call.get(str(event.get("id")))
            if own is not None:
                own.add(event)

    @contextmanager
    def unit(self, *, admit: Callable[[dict[str, Any]], None] | None = None) -> Iterator[_Unit]:
        previous = self._current
        unit = _Unit(usage=CallUsage(), admit=admit)
        self._current = unit
        try:
            yield unit
        finally:
            self._current = previous

    @contextmanager
    def observing(self) -> Iterator["UsageCollector"]:
        with observe_model_calls(self):
            yield self


@dataclass
class AdmittedCall:
    route: str
    purpose: str
    estimate: SpendEstimate
    usage: CallUsage
    started: float
    latency_seconds: float | None = None
    status: str = "completed"
    physical_requests: int = 1


class ReviewSpend:
    """One budget for the whole run; per-route billing decides what counts."""

    def __init__(
        self,
        caps: SpendCaps,
        *,
        cancelled: Callable[[], bool] | None = None,
        price_per_million: float | None = None,
    ) -> None:
        self.caps = caps
        self.budget = SpendBudget(caps, cancelled=cancelled)
        self._cancelled = cancelled
        self.owner_price = price_per_million
        self.routes: dict[str, RouteInfo] = {}
        self.collector = UsageCollector()
        self.totals: dict[str, CallUsage] = {}
        self.estimated_usd: dict[str, float | None] = {}

    @staticmethod
    def _output_limit(route: str, profile_max_tokens: Any) -> int:
        return admitted_output_limit(route, profile_max_tokens)

    def register(self, route: str, client: Any, *, model_id: str | None = None) -> RouteInfo:
        model = model_id or getattr(client, "model", None) or getattr(client, "model_id", None)
        profile = getattr(client, "profile", None)
        output_limit = self._output_limit(route, getattr(profile, "max_tokens", None))
        if is_subscription_client(client):
            info = RouteInfo(route, getattr(client, "provider_name", None), model, "subscription", self.owner_price, "subscription", output_limit)
        else:
            known = KNOWN_PRICES_PER_MILLION.get(str(model or ""))
            if self.owner_price is not None:
                price, source = self.owner_price, "owner_override"
            elif known is not None:
                price, source = known, "known"
            else:
                price, source = None, "unknown"
            info = RouteInfo(route, getattr(client, "provider_name", None), model, "metered", price, source, output_limit)
        self.routes[route] = info
        return info

    def register_profile(
        self,
        route: str,
        *,
        provider: str | None,
        model: str | None,
        subscription: bool,
        max_tokens: int | None = None,
    ) -> RouteInfo:
        """Classify a route from configuration alone (a dry run builds no client)."""

        output_limit = self._output_limit(route, max_tokens)
        if subscription:
            info = RouteInfo(route, provider, model, "subscription", self.owner_price, "subscription", output_limit)
        else:
            known = KNOWN_PRICES_PER_MILLION.get(str(model or ""))
            price = self.owner_price if self.owner_price is not None else known
            source = "owner_override" if self.owner_price is not None else ("known" if known is not None else "unknown")
            info = RouteInfo(route, provider, model, "metered", price, source, output_limit)
        self.routes[route] = info
        return info

    def output_limit(self, route: str) -> int:
        info = self.routes.get(route)
        return info.output_limit if info is not None else OUTPUT_ALLOWANCE.get(route, 2_000)

    def _usd(self, info: RouteInfo, tokens: int) -> float | None:
        if info.price_per_million is None:
            return None
        return tokens * info.price_per_million / 1_000_000

    def estimate(self, route: str, *, calls: int, input_tokens: int, output_tokens: int, candidates: int = 0, pairs: int = 0) -> SpendEstimate:
        info = self.routes[route]
        tokens = input_tokens + output_tokens
        if info.billing == "subscription":
            return SpendEstimate(candidates=candidates, pairs=pairs, calls=calls, total_tokens=0, estimated_usd=0.0)
        return SpendEstimate(
            candidates=candidates,
            pairs=pairs,
            calls=calls,
            total_tokens=tokens,
            estimated_usd=self._usd(info, tokens),
        )

    def check(self, estimate: SpendEstimate) -> SpendEstimate:
        return self.budget.check(estimate)

    @contextmanager
    def request(
        self,
        route: str,
        purpose: str,
        *,
        input_tokens: int,
        output_tokens: int | None = None,
        retry: bool = False,
    ) -> Iterator[AdmittedCall]:
        """Admit one unit of paid work on ``route``, then meter what it used.

        Metered: the first physical request is admitted here and every later
        one inside the unit (transport retry, JSON repair) is admitted as a
        retry before it is sent; the transport is held to the admitted output
        limit. Subscription: one logical call against the call cap, physical
        requests unbounded but each preceded by a cancellation check.
        """

        if route not in self.routes:
            raise KeyError(f"route {route!r} was not registered")
        info = self.routes[route]
        output = info.output_limit if output_tokens is None else output_tokens
        base = self.estimate(route, calls=1, input_tokens=input_tokens, output_tokens=output)
        estimate = SpendEstimate(
            calls=1,
            retries=1 if retry else 0,
            total_tokens=base.total_tokens,
            estimated_usd=base.estimated_usd,
        )
        with ExitStack() as stack:
            charge = stack.enter_context(self.budget.request(estimate))
            charges: list[SpendCharge] = [charge]
            if info.billing == "metered":
                extra = SpendEstimate(calls=1, retries=1, total_tokens=base.total_tokens, estimated_usd=base.estimated_usd)

                def admit(_event: dict[str, Any]) -> None:
                    charges.append(stack.enter_context(self.budget.request(extra)))
            else:

                def admit(_event: dict[str, Any]) -> None:
                    if self._cancelled is not None and self._cancelled():
                        raise SpendCancelled("Paid work cancelled")

            unit = stack.enter_context(self.collector.unit(admit=admit))
            limit = generation_limit(output) if info.billing == "metered" and output > 0 else nullcontext()
            usage = unit.usage
            call = AdmittedCall(route=route, purpose=purpose, estimate=estimate, usage=usage, started=time.monotonic())
            try:
                with limit:
                    yield call
            except BaseException:
                call.status = "failed"
                raise
            finally:
                call.latency_seconds = round(time.monotonic() - call.started, 3)
                call.physical_requests = max(1, len(unit.physical))
                if info.billing == "metered":
                    # Each admitted physical request reconciles with its OWN
                    # reported usage (the first also absorbs a root-only unit).
                    per_request = [unit.by_call.get(call_id) for call_id in unit.physical] or [usage]
                    for index, admitted in enumerate(charges):
                        own = per_request[index] if index < len(per_request) else None
                        reported = (own.input_tokens + own.output_tokens) if own is not None else 0
                        tokens = reported or base.total_tokens
                        cost = own.cost if own is not None and own.cost is not None else self._usd(info, tokens)
                        admitted.reconcile(total_tokens=tokens, estimated_usd=cost)
                self._accumulate(route, info, usage, input_tokens * call.physical_requests, output * call.physical_requests)

    def _accumulate(self, route: str, info: RouteInfo, usage: CallUsage, input_estimate: int, output_estimate: int) -> None:
        total = self.totals.setdefault(route, CallUsage())
        total.calls += 1
        reported = usage.input_tokens or usage.output_tokens
        total.input_tokens += usage.input_tokens if reported else input_estimate
        total.output_tokens += usage.output_tokens if reported else output_estimate
        total.cached_input_tokens += usage.cached_input_tokens
        total.reasoning_tokens += usage.reasoning_tokens
        tokens = (usage.input_tokens + usage.output_tokens) if reported else input_estimate + output_estimate
        cost = usage.cost if usage.cost is not None else self._usd(info, tokens)
        previous = self.estimated_usd.get(route, 0.0)
        self.estimated_usd[route] = None if cost is None or previous is None else previous + cost

    def call_cost(self, route: str, usage: CallUsage, input_estimate: int, output_estimate: int) -> float | None:
        info = self.routes[route]
        reported = usage.input_tokens or usage.output_tokens
        tokens = (usage.input_tokens + usage.output_tokens) if reported else input_estimate + output_estimate
        return usage.cost if usage.cost is not None else self._usd(info, tokens)

    def summary(self) -> dict[str, Any]:
        return {
            "caps": self.caps.as_dict(),
            "not_enforced_on_subscription": ["max_total_tokens", "max_estimated_usd", "physical requests (retries, JSON repairs)"],
            "charged": {
                "calls": self.budget.used.calls,
                "retries": self.budget.used.retries,
                "metered_total_tokens": self.budget.used.total_tokens,
                "metered_estimated_usd": self.budget.used.estimated_usd,
            },
            "routes": {
                route: {
                    **info.as_dict(),
                    "calls": self.totals.get(route, CallUsage()).calls,
                    "input_tokens": self.totals.get(route, CallUsage()).input_tokens,
                    "output_tokens": self.totals.get(route, CallUsage()).output_tokens,
                    "cached_input_tokens": self.totals.get(route, CallUsage()).cached_input_tokens,
                    "estimated_usd": self.estimated_usd.get(route),
                }
                for route, info in sorted(self.routes.items())
            },
        }


__all__ = [
    "ESTIMATED_ONLY",
    "KNOWN_PRICES_PER_MILLION",
    "OUTPUT_ALLOWANCE",
    "AdmittedCall",
    "CallUsage",
    "ReviewSpend",
    "RouteInfo",
    "UsageCollector",
    "admitted_output_limit",
    "is_subscription_client",
]
