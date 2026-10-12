"""Finite, per-command admission for paid work (Slice A §5.6).

Use ``check`` on the whole planned estimate for a no-call dry run, and put
``request`` immediately around EACH physical attempt, including retries.
Disable hidden SDK retries. Count new candidates/pairs once, not again when
retrying them. Calls, tokens and dollars are charged on every attempt.

Unknown prices fail closed. The command may accept an explicit owner-supplied
finite price estimate and use it to compute ``estimated_usd``; increasing the
dollar cap alone never admits an unknown price. Record that override in the
command's report. Estimates must include bounded output as well as input.

Reservations are never refunded, even on failure or absent usage. Reconciliation
only increases charges; a provider exceeding its estimate stops the NEXT request
but does not discard an already-paid response. This is a serial, in-memory
command budget, not a concurrent or cross-process quota. Resume skips finished
work through existing model_work_checkpoints; a resumed command gets fresh caps.

Subscription transports (Slice A §5 rule 6, owner 2026-10-12): Codex is billed
to the owner's ChatGPT subscription, so a ``subscription`` budget has no
marginal dollar cost. Its token and dollar caps are not enforced and an unknown
price does not refuse the run. Tokens and cost are still estimated, from
reported usage or else the input-plus-output estimate, and receipts record
them as ``estimated_only``. The candidate, pair, call and retry caps still stop
a runaway loop. Metered routes (OpenRouter, OpenAI API keys, embeddings) keep
the full cap set and the physical-request bound.
"""
from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from decimal import Decimal
import math

from learnloop.ai.errors import AIInterrupted
from learnloop.ai.execution import declared_budgets


_COUNTS = ("candidates", "pairs", "retries", "calls", "total_tokens")

# Codex profile types (``codex_sdk``, the legacy ``http`` adapter) and the
# matching client ``provider_type`` values. Everything else is metered.
SUBSCRIPTION_PROFILE_TYPES = frozenset({"codex_sdk", "http"})
SUBSCRIPTION_CLIENT_TYPES = frozenset({"codex_sdk", "http_adapter"})
SUBSCRIPTION_UNENFORCED_CAPS = ("max_total_tokens", "max_estimated_usd")
ESTIMATED_ONLY = "estimated_only"


def is_subscription_transport(*, profile=None, client=None) -> bool:
    """True for a Codex route billed to the owner's subscription."""
    if client is not None:
        return getattr(client, "provider_type", None) in SUBSCRIPTION_CLIENT_TYPES
    return getattr(profile, "type", None) in SUBSCRIPTION_PROFILE_TYPES


def subscription_usage_estimate(
    event: Mapping[str, object], *, planned_tokens: int, price_per_token: float | None,
) -> dict[str, object]:
    """A subscription receipt's ``usage_json`` estimate (``estimated_only``).

    Tokens come from the usage the transport reported, else the planned
    input-plus-output estimate. Dollars are priced only with an owner price.
    """
    reported = int(event.get("input_tokens") or 0) + int(event.get("output_tokens") or 0)
    tokens = reported or planned_tokens
    return {
        "cost_basis": ESTIMATED_ONLY,
        "estimated_total_tokens": tokens,
        "estimated_token_source": "reported_usage" if reported else "input_plus_output_estimate",
        "estimated_usd": tokens * price_per_token if price_per_token is not None else None,
    }


def _count(name: str, value: int) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")


def _money(name: str, value: float) -> None:
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")


@dataclass(frozen=True)
class SpendCaps:
    max_candidates: int = 100
    max_pairs: int = 100
    max_retries: int = 2
    max_calls: int = 100
    max_total_tokens: int = 100_000
    max_estimated_usd: float = 1.0

    def __post_init__(self) -> None:
        for name in _COUNTS:
            _count(f"max_{name}", getattr(self, f"max_{name}"))
        _money("max_estimated_usd", self.max_estimated_usd)

    def as_dict(self) -> dict[str, int | float]:
        return asdict(self)


@dataclass(frozen=True)
class SpendEstimate:
    candidates: int = 0
    pairs: int = 0
    retries: int = 0
    calls: int = 0
    total_tokens: int = 0
    estimated_usd: float | None = None

    def __post_init__(self) -> None:
        for name in _COUNTS:
            _count(name, getattr(self, name))
        if self.estimated_usd is not None:
            _money("estimated_usd", self.estimated_usd)


class SpendLimitExceeded(ValueError):
    """The next request cannot be admitted under the declared caps."""


class SpendCancelled(AIInterrupted):
    """Cancellation was observed before admitting another request."""


class SpendBudget:
    def __init__(
        self, caps: SpendCaps, *, cancelled: Callable[[], bool] | None = None,
        subscription: bool = False,
    ) -> None:
        self._caps = caps
        self._cancelled = cancelled
        self._subscription = subscription
        self._used = SpendEstimate(estimated_usd=0.0)
        # Decimal summation keeps exact decimal dollar boundaries exact.
        self._usd = Decimal(0)
        # A subscription run may proceed without a price; its total is unknown.
        self._usd_known = True

    @property
    def caps(self) -> SpendCaps:
        return self._caps

    @property
    def subscription(self) -> bool:
        return self._subscription

    @property
    def used(self) -> SpendEstimate:
        return replace(self._used, estimated_usd=float(self._usd) if self._usd_known else None)

    def declared(self) -> dict[str, object]:
        """The caps in force, as recorded on receipts' ``budget_json``."""
        declared: dict[str, object] = dict(self.caps.as_dict())
        if self._subscription:
            declared.update(
                billing="subscription", cost_basis=ESTIMATED_ONLY,
                physical_request_bound=False,
                not_enforced=list(SUBSCRIPTION_UNENFORCED_CAPS),
            )
        return declared

    def check(self, estimate: SpendEstimate) -> SpendEstimate:
        """Check additional work without reserving it or making any calls.

        Returns the supplied estimate so commands can render it for dry runs.
        Unknown cost remains None in the plan and is never rendered as zero.
        """
        if self._cancelled is not None and self._cancelled():
            raise SpendCancelled("Paid work cancelled")
        if estimate.estimated_usd is None and not self._subscription:
            raise SpendLimitExceeded(
                "Unknown price: supply an explicit finite owner price estimate"
            )
        for name in _COUNTS:
            if self._subscription and f"max_{name}" in SUBSCRIPTION_UNENFORCED_CAPS:
                continue
            if getattr(self._used, name) + getattr(estimate, name) > getattr(self.caps, f"max_{name}"):
                raise SpendLimitExceeded(f"{name} exceeds max_{name}")
        if not self._subscription and (
            self._usd + Decimal(str(estimate.estimated_usd)) > Decimal(str(self.caps.max_estimated_usd))
        ):
            raise SpendLimitExceeded("estimated_usd exceeds max_estimated_usd")
        return estimate

    @contextmanager
    def request(self, estimate: SpendEstimate) -> Iterator[SpendCharge]:
        """Reserve one physical attempt before entering the paid-call body.

        The provider's root ``model_call`` must be inside this context so that
        existing receipt observation writes all caps to ``budget_json``.
        Call ``charge.reconcile`` with usage, including known failed usage.
        """
        if estimate.calls != 1 or estimate.retries not in (0, 1):
            raise ValueError("A request must declare calls=1 and retries=0 or 1")
        self.check(estimate)
        self._used = replace(
            self._used,
            **{name: getattr(self._used, name) + getattr(estimate, name) for name in _COUNTS},
        )
        if estimate.estimated_usd is None:
            self._usd_known = False
        else:
            self._usd += Decimal(str(estimate.estimated_usd))
        charge = SpendCharge(self, estimate)
        with declared_budgets(self.declared()):
            yield charge


class SpendCharge:
    """An admitted attempt; reconciliation is monotonic and idempotent."""

    def __init__(self, budget: SpendBudget, estimate: SpendEstimate) -> None:
        self._budget = budget
        self._tokens = estimate.total_tokens
        # None only on a subscription budget whose price is unknown.
        self._usd = Decimal(str(estimate.estimated_usd)) if estimate.estimated_usd is not None else None

    def reconcile(
        self, *, total_tokens: int | None = None, estimated_usd: float | None = None,
    ) -> None:
        """Supply cumulative actual usage for this attempt, not usage deltas.

        None means unknown, retaining the reservation. Lower actual values do
        not refund headroom. Over-cap actual usage is recorded without raising
        here: admission blocks the next call instead of losing paid output.
        If actual tokens exceed the estimate and the provider omits cost, the
        caller must recompute estimated_usd using its known/owner-supplied rate;
        this layer cannot infer mixed input/output pricing from total tokens.
        """
        if total_tokens is not None:
            _count("total_tokens", total_tokens)
        if estimated_usd is not None:
            _money("estimated_usd", estimated_usd)
        tokens = max(self._tokens, total_tokens if total_tokens is not None else self._tokens)
        self._budget._used = replace(
            self._budget._used,
            total_tokens=self._budget._used.total_tokens + tokens - self._tokens,
        )
        self._tokens = tokens
        if estimated_usd is None:
            return
        actual = Decimal(str(estimated_usd))
        usd = actual if self._usd is None else max(self._usd, actual)
        self._budget._usd += usd - (self._usd or Decimal(0))
        self._usd = usd
