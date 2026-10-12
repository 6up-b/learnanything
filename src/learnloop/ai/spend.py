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
"""
from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from decimal import Decimal
import math

from learnloop.ai.errors import AIInterrupted
from learnloop.ai.execution import declared_budgets


_COUNTS = ("candidates", "pairs", "retries", "calls", "total_tokens")


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
    ) -> None:
        self._caps = caps
        self._cancelled = cancelled
        self._used = SpendEstimate(estimated_usd=0.0)
        # Decimal summation keeps exact decimal dollar boundaries exact.
        self._usd = Decimal(0)

    @property
    def caps(self) -> SpendCaps:
        return self._caps

    @property
    def used(self) -> SpendEstimate:
        return replace(self._used, estimated_usd=float(self._usd))

    def check(self, estimate: SpendEstimate) -> SpendEstimate:
        """Check additional work without reserving it or making any calls.

        Returns the supplied estimate so commands can render it for dry runs.
        Unknown cost remains None in the plan and is never rendered as zero.
        """
        if self._cancelled is not None and self._cancelled():
            raise SpendCancelled("Paid work cancelled")
        if estimate.estimated_usd is None:
            raise SpendLimitExceeded(
                "Unknown price: supply an explicit finite owner price estimate"
            )
        for name in _COUNTS:
            if getattr(self._used, name) + getattr(estimate, name) > getattr(self.caps, f"max_{name}"):
                raise SpendLimitExceeded(f"{name} exceeds max_{name}")
        if self._usd + Decimal(str(estimate.estimated_usd)) > Decimal(str(self.caps.max_estimated_usd)):
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
        self._usd += Decimal(str(estimate.estimated_usd))
        charge = SpendCharge(self, estimate)
        with declared_budgets(self.caps.as_dict()):
            yield charge


class SpendCharge:
    """An admitted attempt; reconciliation is monotonic and idempotent."""

    def __init__(self, budget: SpendBudget, estimate: SpendEstimate) -> None:
        self._budget = budget
        self._tokens = estimate.total_tokens
        self._usd = Decimal(str(estimate.estimated_usd))

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
        usd = max(self._usd, Decimal(str(estimated_usd)) if estimated_usd is not None else self._usd)
        self._budget._used = replace(
            self._budget._used,
            total_tokens=self._budget._used.total_tokens + tokens - self._tokens,
        )
        self._budget._usd += usd - self._usd
        self._tokens, self._usd = tokens, usd
