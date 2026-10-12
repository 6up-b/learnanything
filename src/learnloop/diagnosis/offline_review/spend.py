"""Per-route spend admission and usage accounting for one review run.

Every paid request passes :meth:`ReviewSpend.request` BEFORE it is sent (Slice A
§5.6). One :class:`~learnloop.ai.spend.SpendBudget` holds the command's caps:

* **metered routes** (OpenRouter, OpenAI keys, embeddings) are admitted with
  their full token and dollar estimate; an unknown price fails closed unless
  the owner supplies one;
* **subscription routes** (Codex on the owner's ChatGPT subscription) have no
  marginal dollar cost (Slice A §5 rule 6): they count against the call,
  candidate and retry caps only. Their tokens and an API-equivalent cost are
  still estimated from reported usage and recorded as ``estimated_only``.

This mirrors the subscription rule the Slice A integration adds to
``ai/spend.py`` without touching that module (it is not on this branch's base);
M2 should switch to the shared ``SpendBudget(subscription=...)`` once both land.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator

from learnloop.ai.execution import observe_model_calls
from learnloop.ai.spend import SpendBudget, SpendCaps, SpendEstimate

SUBSCRIPTION_CLIENT_TYPES = frozenset({"codex_sdk", "http_adapter"})
ESTIMATED_ONLY = "estimated_only"
REPORTED = "reported"
#: Published per-million input price of the one Slice 1 embedding model.
KNOWN_PRICES_PER_MILLION = {"qwen/qwen3-embedding-8b": 0.01}
#: Bounded output allowances used in estimates (tokens).
OUTPUT_ALLOWANCE = {
    "grading": 3_000,
    "diagnosis": 4_000,
    "diagnosis_judge": 2_500,
    "diagnosis_generator": 3_000,
    "embedding": 0,
}


def is_subscription_client(client: Any) -> bool:
    return getattr(client, "provider_type", None) in SUBSCRIPTION_CLIENT_TYPES


@dataclass
class RouteInfo:
    route: str
    provider: str | None
    model: str | None
    billing: str  # subscription | metered
    price_per_million: float | None
    price_source: str  # owner_override | known | unknown | subscription

    def as_dict(self) -> dict[str, Any]:
        return {
            "route": self.route,
            "provider": self.provider,
            "model": self.model,
            "billing": self.billing,
            "price_per_million": self.price_per_million,
            "price_source": self.price_source,
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
class UsageCollector:
    """Observes model calls: forwards receipts and meters the current unit."""

    sink: Callable[[str, dict[str, Any]], None] | None = None
    _current: CallUsage | None = None
    _roots: set[str] = field(default_factory=set)

    def __call__(self, action: str, event: dict[str, Any]) -> None:
        if self.sink is not None:
            try:
                self.sink(action, event)
            except Exception:  # noqa: BLE001 - receipts are telemetry, never fatal
                pass
        if self._current is None:
            return
        if action == "start" and event.get("parent_call_id") is None:
            self._roots.add(str(event.get("id")))
            self._current.calls += 1
        if action == "finish":
            self._current.add(event)

    @contextmanager
    def unit(self) -> Iterator[CallUsage]:
        previous = self._current
        usage = CallUsage()
        self._current = usage
        try:
            yield usage
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
        self.owner_price = price_per_million
        self.routes: dict[str, RouteInfo] = {}
        self.collector = UsageCollector()
        self.totals: dict[str, CallUsage] = {}
        self.estimated_usd: dict[str, float | None] = {}

    def register(self, route: str, client: Any, *, model_id: str | None = None) -> RouteInfo:
        model = model_id or getattr(client, "model", None) or getattr(client, "model_id", None)
        if is_subscription_client(client):
            info = RouteInfo(route, getattr(client, "provider_name", None), model, "subscription", self.owner_price, "subscription")
        else:
            known = KNOWN_PRICES_PER_MILLION.get(str(model or ""))
            if self.owner_price is not None:
                price, source = self.owner_price, "owner_override"
            elif known is not None:
                price, source = known, "known"
            else:
                price, source = None, "unknown"
            info = RouteInfo(route, getattr(client, "provider_name", None), model, "metered", price, source)
        self.routes[route] = info
        return info

    def register_profile(self, route: str, *, provider: str | None, model: str | None, subscription: bool) -> RouteInfo:
        """Classify a route from configuration alone (a dry run builds no client)."""

        if subscription:
            info = RouteInfo(route, provider, model, "subscription", self.owner_price, "subscription")
        else:
            known = KNOWN_PRICES_PER_MILLION.get(str(model or ""))
            price = self.owner_price if self.owner_price is not None else known
            source = "owner_override" if self.owner_price is not None else ("known" if known is not None else "unknown")
            info = RouteInfo(route, provider, model, "metered", price, source)
        self.routes[route] = info
        return info

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
        """Admit ONE physical request on ``route``, then meter what it used."""

        if route not in self.routes:
            raise KeyError(f"route {route!r} was not registered")
        info = self.routes[route]
        output = OUTPUT_ALLOWANCE.get(route, 2_000) if output_tokens is None else output_tokens
        base = self.estimate(route, calls=1, input_tokens=input_tokens, output_tokens=output)
        estimate = SpendEstimate(
            calls=1,
            retries=1 if retry else 0,
            total_tokens=base.total_tokens,
            estimated_usd=base.estimated_usd,
        )
        with self.budget.request(estimate) as charge, self.collector.unit() as usage:
            call = AdmittedCall(route=route, purpose=purpose, estimate=estimate, usage=usage, started=time.monotonic())
            try:
                yield call
            except BaseException:
                call.status = "failed"
                raise
            finally:
                call.latency_seconds = round(time.monotonic() - call.started, 3)
                actual = usage.input_tokens + usage.output_tokens
                if info.billing == "metered":
                    tokens = actual or base.total_tokens
                    cost = usage.cost if usage.cost is not None else self._usd(info, tokens)
                    charge.reconcile(total_tokens=tokens, estimated_usd=cost)
                self._accumulate(route, info, usage, input_tokens, output)

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
            "not_enforced_on_subscription": ["max_total_tokens", "max_estimated_usd"],
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
    "is_subscription_client",
]
