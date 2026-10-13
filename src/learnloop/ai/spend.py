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

Subscription transports (Slice A §5 rule 6, owner 2026-10-12): Codex and the
``chatgpt_plan`` provider are billed to the owner's ChatGPT subscription, so a
``subscription`` budget has no marginal dollar cost. Its token and dollar caps
are not enforced and an unknown price does not refuse the run. Tokens and cost are still estimated, from
reported usage or else the input-plus-output estimate, and receipts record
them as ``estimated_only``. The candidate, pair, call and retry caps still stop
a runaway loop. Metered routes (OpenRouter, OpenAI API keys, embeddings) keep
the full cap set and the physical-request bound.

Shared envelopes (canonical sources, Codex review F2): a ``SpendBudget`` caps
one operation, but a batch command, one import's several operations and a
service's daily cap must bound the SUM of many budgets, across threads.
``spend_envelopes(...)`` activates ``SpendEnvelope`` objects for a context;
every ``SpendBudget.request`` inside it (and in any thread started with a
copy of that context) reserves its metered estimate in each active envelope
BEFORE the physical request is sent, and reconciles upward after, so the
envelope refuses the next request instead of noticing the overrun later. An
envelope may also read an externally observed total (the receipts of other
operations and processes): its in-flight reservations are then held only
until the request's receipt is written. Subscription requests are never
refused by an envelope; their tokens and owner-priced cost are tallied as
``estimated_only``, with no request-count bound.
"""
from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass, replace
from decimal import Decimal
import json
import math
import threading
from typing import Any

from learnloop.ai.errors import AIInterrupted
from learnloop.ai.execution import declared_budgets


_COUNTS = ("candidates", "pairs", "retries", "calls", "total_tokens")

# Codex profile types (``codex_sdk``, the legacy ``http`` adapter), the
# ChatGPT-plan provider (Sign in with ChatGPT, billed to the same plan) and
# the matching client ``provider_type`` values. Everything else is metered.
SUBSCRIPTION_PROFILE_TYPES = frozenset({"codex_sdk", "http", "chatgpt_plan"})
SUBSCRIPTION_CLIENT_TYPES = frozenset({"codex_sdk", "http_adapter", "chatgpt_plan"})
SUBSCRIPTION_UNENFORCED_CAPS = ("max_total_tokens", "max_estimated_usd")
ESTIMATED_ONLY = "estimated_only"
#: ``budget_json`` key: the ledger reservations a request was admitted under.
RESERVATIONS_KEY = "envelope_reservations"


def is_subscription_transport(*, profile=None, client=None) -> bool:
    """True for a route billed to the owner's ChatGPT subscription (Codex or the plan provider)."""
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
    #: None: no money cap on this budget (an owner-unset operation cap; shared
    #: envelopes such as a daily guard still bound it).
    max_estimated_usd: float | None = 1.0

    def __post_init__(self) -> None:
        for name in _COUNTS:
            _count(f"max_{name}", getattr(self, f"max_{name}"))
        if self.max_estimated_usd is not None:
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
        if not self._subscription and self.caps.max_estimated_usd is not None and (
            self._usd + Decimal(str(estimate.estimated_usd)) > Decimal(str(self.caps.max_estimated_usd))
        ):
            raise SpendLimitExceeded("estimated_usd exceeds max_estimated_usd")
        return estimate

    @contextmanager
    def request(self, estimate: SpendEstimate, *, subscription_route: bool = False) -> Iterator[SpendCharge]:
        """Reserve one physical attempt before entering the paid-call body.

        The provider's root ``model_call`` must be inside this context so that
        existing receipt observation writes all caps to ``budget_json``.
        Call ``charge.reconcile`` with usage, including known failed usage.

        ``subscription_route``: the request goes to a subscription route
        (Codex, the ChatGPT plan) although this budget enforces the metered
        caps (``PaidCalls`` keeps one budget per route and prices a
        subscription attempt at $0). Shared envelopes then treat it as the
        subscription it is: no reservation, never refused for money, its
        usage tallied ``estimated_only`` (the sources merge: a $0 reservation
        in the service's daily ledger was refusable once the day's total
        passed its cap).
        """
        if estimate.calls != 1 or estimate.retries not in (0, 1):
            raise ValueError("A request must declare calls=1 and retries=0 or 1")
        self.check(estimate)
        envelopes = _envelopes.get()
        subscription = self._subscription or subscription_route
        reserved = _reserve_in(envelopes, estimate, subscription=subscription)
        self._used = replace(
            self._used,
            **{name: getattr(self._used, name) + getattr(estimate, name) for name in _COUNTS},
        )
        if estimate.estimated_usd is None:
            self._usd_known = False
        else:
            self._usd += Decimal(str(estimate.estimated_usd))
        charge = SpendCharge(self, estimate, envelopes=reserved, subscription=subscription)
        declared = self.declared()
        refs = [ref for envelope, handle in reserved if (ref := envelope.reservation_ref(handle))]
        if refs:
            declared[RESERVATIONS_KEY] = refs
        try:
            with declared_budgets(declared):
                yield charge
        except Exception as exc:
            # A refusal raised below this layer (a released reservation's
            # fence at the receipt's start) is a refusal like any other.
            if getattr(exc, "spend_refused", False) and not isinstance(exc, SpendLimitExceeded):
                raise SpendLimitExceeded(str(exc)) from exc
            raise
        finally:
            for envelope, handle in reserved:
                envelope.settle(handle, actual=charge.actual_usd)


class SpendCharge:
    """An admitted attempt; reconciliation is monotonic and idempotent."""

    def __init__(self, budget: SpendBudget, estimate: SpendEstimate, *,
                 envelopes: tuple[tuple[SpendEnvelope, object], ...] = (),
                 subscription: bool | None = None) -> None:
        self._budget = budget
        #: Whether the attempt is a subscription request for the envelopes
        #: (the budget's flag, or the request's ``subscription_route``).
        self._subscription = budget.subscription if subscription is None else subscription
        self._tokens = estimate.total_tokens
        # None only on a subscription budget whose price is unknown.
        self._usd = Decimal(str(estimate.estimated_usd)) if estimate.estimated_usd is not None else None
        self._envelopes = envelopes
        self._noted_tokens = 0
        self._noted_usd = Decimal(0)
        #: The attempt's actual cost as last reconciled (None: never reported).
        self.actual_usd: Decimal | None = None

    def note_estimated_only(self, *, total_tokens: int, estimated_usd: float | None) -> None:
        """A subscription attempt's estimated usage (cumulative, ``estimated_only``)
        for the active envelopes' reports. Never refuses anything."""
        if not self._subscription:
            return
        tokens = max(0, int(total_tokens) - self._noted_tokens)
        usd = None
        if estimated_usd is not None:
            usd = max(Decimal(0), Decimal(str(estimated_usd)) - self._noted_usd)
            self._noted_usd += usd
        self._noted_tokens += tokens
        for envelope, _amount in self._envelopes:
            envelope.note_estimated_only(tokens, usd)

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
        if self._subscription:
            self.note_estimated_only(total_tokens=tokens, estimated_usd=estimated_usd)
        if estimated_usd is None:
            return
        actual = Decimal(str(estimated_usd))
        self.actual_usd = actual
        usd = actual if self._usd is None else max(self._usd, actual)
        delta = usd - (self._usd or Decimal(0))
        self._budget._usd += delta
        self._usd = usd
        if delta > 0 and not self._subscription:
            for envelope, handle in self._envelopes:
                envelope.charge(delta, handle)


class SpendEnvelope:
    """A money bound shared by every ``SpendBudget`` admitted while it is active.

    Thread-safe. ``max_usd`` bounds metered dollars: each request reserves its
    estimate before it is sent (refused with ``SpendLimitExceeded`` when the
    reservation would pass the bound) and reconciles upward after; nothing is
    refunded. With ``observed`` (a callable returning dollars already recorded
    elsewhere, such as today's receipts), the bound covers that total plus
    this process's requests still in flight; a reservation is released once
    the request's receipt is written, since ``observed`` then includes it.
    Subscription usage is tallied (``estimated_only``), never refused.
    """

    def __init__(self, name: str, max_usd: float, *, observed: Callable[[], float] | None = None) -> None:
        _money("max_usd", max_usd)
        self.name = name
        self.max_usd = Decimal(str(max_usd))
        self._observed = observed
        self._lock = threading.Lock()
        self._charged = Decimal(0)
        self._in_flight = Decimal(0)
        self._refused = 0
        self._estimated_only_tokens = 0
        self._estimated_only_usd: Decimal | None = Decimal(0)

    def _total(self) -> Decimal:
        if self._observed is None:
            return self._charged
        return Decimal(str(self._observed() or 0.0)) + self._in_flight

    def remaining(self) -> float:
        with self._lock:
            return float(max(Decimal(0), self.max_usd - self._total()))

    def reserve(self, usd: Decimal) -> object:
        """Reserve ``usd`` before a request is sent; returns the reservation's
        handle (passed back to ``unreserve``, ``charge`` and ``settle``)."""
        with self._lock:
            if self._total() + usd > self.max_usd:
                self._refused += 1
                raise SpendLimitExceeded(
                    f"{self.name}: ${float(self._total() + usd):.4f} would pass the ${float(self.max_usd):.4f} cap")
            if self._observed is None:
                self._charged += usd
            else:
                self._in_flight += usd
        return usd

    def reservation_ref(self, handle: object) -> str | None:
        """A durable name for the reservation, recorded on the request's root
        receipt (``budget_json.envelope_reservations``) so a ledger that
        counts the reservation never counts the receipt again. None here:
        an in-memory envelope keeps no ledger."""
        return None

    def unreserve(self, handle: object) -> None:
        """Undo a reservation whose request was never sent (another envelope refused it)."""
        usd = Decimal(str(handle))
        with self._lock:
            if self._observed is None:
                self._charged -= usd
            else:
                self._in_flight -= usd

    def charge(self, usd: Decimal, handle: object = None) -> None:
        """Usage above the reservation (reconciliation; never a refund)."""
        if usd <= 0:
            return
        with self._lock:
            if self._observed is None:
                self._charged += usd
            # An observed envelope reads the reconciled cost from the receipt.

    def settle(self, handle: object, actual: Decimal | None = None) -> None:
        """The request finished and its receipt is written (``actual``: its
        reconciled cost, when the provider reported one)."""
        if self._observed is None:
            return
        with self._lock:
            self._in_flight -= Decimal(str(handle))

    def note_estimated_only(self, tokens: int, usd: Decimal | None) -> None:
        with self._lock:
            self._estimated_only_tokens += int(tokens)
            if usd is None:
                self._estimated_only_usd = None
            elif self._estimated_only_usd is not None:
                self._estimated_only_usd += usd

    def report(self) -> dict[str, object]:
        with self._lock:
            total = self._total()
            return {
                "name": self.name, "max_usd": float(self.max_usd), "metered_usd": float(total),
                "remaining_usd": float(max(Decimal(0), self.max_usd - total)),
                "refused_requests": self._refused,
                "basis": "observed receipts plus requests in flight" if self._observed is not None
                else "reserved before each request, reconciled upward",
                "estimated_only": {"tokens": self._estimated_only_tokens,
                                   "usd": None if self._estimated_only_usd is None
                                   else float(self._estimated_only_usd)},
            }


_envelopes: ContextVar[tuple[SpendEnvelope, ...]] = ContextVar("spend_envelopes", default=())


@contextmanager
def spend_envelopes(*envelopes: SpendEnvelope | None) -> Iterator[tuple[SpendEnvelope, ...]]:
    """Activate envelopes for this context (added to any already active).

    A thread started inside this context sees them only when it runs in a
    copy of the context (``contextvars.copy_context().run``).
    """
    active = _envelopes.get()
    added = tuple(envelope for envelope in envelopes if envelope is not None and envelope not in active)
    token = _envelopes.set(active + added)
    try:
        yield active + added
    finally:
        _envelopes.reset(token)


def active_envelopes() -> tuple[SpendEnvelope, ...]:
    return _envelopes.get()


class _NoReservation:
    """A subscription request's place in an envelope: nothing reserved, so
    nothing to settle (its usage is tallied ``estimated_only``)."""

    def __str__(self) -> str:
        return "0"


NO_RESERVATION = _NoReservation()


def _reserve_in(envelopes: tuple[SpendEnvelope, ...], estimate: SpendEstimate, *,
                subscription: bool) -> tuple[tuple[SpendEnvelope, object], ...]:
    """Reserve a metered estimate in every envelope, all or none; returns each
    envelope with its reservation handle."""
    if not envelopes:
        return ()
    if subscription:
        return tuple((envelope, NO_RESERVATION) for envelope in envelopes)
    if estimate.estimated_usd is None:
        raise SpendLimitExceeded("Unknown price: an envelope cannot admit an unpriced metered request")
    amount = Decimal(str(estimate.estimated_usd))
    done: list[tuple[SpendEnvelope, object]] = []
    try:
        for envelope in envelopes:
            done.append((envelope, envelope.reserve(amount)))
    except SpendLimitExceeded:
        for envelope, handle in done:
            envelope.unreserve(handle)
        raise
    return tuple(done)


# Characters per token for a request's input estimate (the house ~4).
_CHARS_PER_TOKEN = 4


@dataclass(frozen=True)
class RequestAdmission:
    """One admitted physical request: what it reserved, priced at its route."""

    key: int
    provider: str | None
    tokens: int
    estimated_usd: float
    price_per_token: float


class MeteredRequestGate:
    """Per-request admission for one unit of paid work (a job attempt).

    Installed with :func:`learnloop.ai.execution.gate_model_requests`, it is
    consulted immediately before EACH physical request, transport retries and
    a provider's JSON repair included, and settled with the usage the request
    reported. A request is admitted only when what this unit has spent, plus
    what requests still in flight reserved, plus this request's estimate (its
    input at ~4 characters a token plus its output ceiling, at the route's
    price) stays within ``limit_usd`` (``None``: no money limit, for work under
    no cap; spend is still settled and ``cancelled`` still consulted). Reported
    usage replaces a reservation
    (the provider's cost, else its tokens at the price); a request that
    reported nothing keeps its whole reservation. A request is therefore
    never sent when it could take the unit past its limit, as long as a
    provider honours its output ceiling; one that overspends stops the next.

    Thread-safe (parallel inventory workers share one gate). Subscription
    routes are never limited here (Slice A §5 rule 6); unknown prices fail
    closed. A refusal raises :class:`SpendLimitExceeded` before the request
    and is kept in :attr:`refusal` for the caller's report.

    ``cancelled``, when given, is consulted before every request made on the
    thread that created the gate, whatever the route: work that was stopped
    (cancelled: Undo, the kill switch) starts no further request, and
    :class:`SpendCancelled` is raised instead. Worker threads skip it: they
    keep SQL off their threads and are stopped by their owner's own poll.
    """

    def __init__(
        self,
        *,
        limit_usd: float | None,
        price_per_token: Callable[[str | None], float | None],
        is_subscription: Callable[[Any], bool],
        default_output_tokens: int = 0,
        spent_before_usd: float = 0.0,
        cancelled: Callable[[], bool] | None = None,
    ) -> None:
        if limit_usd is not None:
            _money("limit_usd", limit_usd)
        _money("spent_before_usd", spent_before_usd)
        _count("default_output_tokens", default_output_tokens)
        self._limit = None if limit_usd is None else Decimal(str(limit_usd))
        self._price = price_per_token
        self._is_subscription = is_subscription
        self._default_output = default_output_tokens
        self._lock = threading.Lock()
        self._spent = Decimal(str(spent_before_usd))
        self._in_flight: dict[int, Decimal] = {}
        self._next_key = 0
        self._cancelled = cancelled
        self._owner_thread = threading.get_ident()
        self.admitted = 0
        self.refusal: dict[str, Any] | None = None

    @property
    def spent_usd(self) -> float:
        with self._lock:
            return float(self._spent)

    @property
    def limit_usd(self) -> float | None:
        return None if self._limit is None else float(self._limit)

    def estimate_tokens(self, client: Any, *, prompt: Any, budget: int | None) -> int:
        """Input (from the request's text) plus the output ceiling."""

        if prompt is None:
            text = ""
        elif isinstance(prompt, str):
            text = prompt
        else:
            text = json.dumps(prompt, ensure_ascii=False, default=str)
        input_tokens = (len(text) + _CHARS_PER_TOKEN - 1) // _CHARS_PER_TOKEN
        output = budget
        if output is None:
            profile = getattr(client, "profile", None) or getattr(client, "config", None)
            output = getattr(profile, "max_tokens", None)
        if output is None:
            output = self._default_output
        return input_tokens + max(int(output), 0)

    def estimate_usd(self, client: Any, *, prompt: Any, budget: int | None) -> float:
        price = self._price(getattr(client, "provider_name", None))
        if price is None:
            raise SpendLimitExceeded("Unknown price: supply an explicit finite owner price estimate")
        return self.estimate_tokens(client, prompt=prompt, budget=budget) * price

    def admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> RequestAdmission | None:
        if (
            self._cancelled is not None
            and threading.get_ident() == self._owner_thread
            and self._cancelled()
        ):
            raise SpendCancelled("Paid work cancelled")
        if self._is_subscription(client):
            return None
        provider = getattr(client, "provider_name", None)
        price = self._price(provider)
        if price is None:
            if self._limit is None:
                return None  # no limit to price against: nothing to admit or settle
            with self._lock:
                self.refusal = {"reason": "unknown_price", "provider": provider, "purpose": purpose}
            raise SpendLimitExceeded("Unknown price: supply an explicit finite owner price estimate")
        _money("price_per_token", price)
        tokens = self.estimate_tokens(client, prompt=prompt, budget=budget)
        usd = Decimal(str(tokens * price))
        with self._lock:
            committed = self._spent + sum(self._in_flight.values(), Decimal(0))
            if self._limit is not None and committed + usd > self._limit:
                self.refusal = {
                    "reason": "limit", "provider": provider, "purpose": purpose,
                    "request_estimate_usd": round(float(usd), 6), "committed_usd": round(float(committed), 6),
                    "limit_usd": round(float(self._limit), 6),
                }
                raise SpendLimitExceeded("estimated_usd exceeds max_estimated_usd")
            key = self._next_key
            self._next_key += 1
            self._in_flight[key] = usd
            self.admitted += 1
        return RequestAdmission(key=key, provider=provider, tokens=tokens, estimated_usd=float(usd),
                                price_per_token=price)

    def settle(self, admission: RequestAdmission | None, usage: Mapping[str, Any]) -> None:
        if admission is None:
            return
        actual = _reported_usd(usage, admission.price_per_token)
        with self._lock:
            reserved = self._in_flight.pop(admission.key, Decimal(0))
            self._spent += reserved if actual is None else actual


def _reported_usd(usage: Mapping[str, Any], price_per_token: float) -> Decimal | None:
    """What a finished request cost: the provider's cost, else its tokens at
    the price; ``None`` when it reported nothing (the reservation stands)."""

    cost = usage.get("cost")
    if isinstance(cost, (int, float)) and not isinstance(cost, bool) and math.isfinite(cost) and cost >= 0:
        return Decimal(str(cost))
    tokens = 0
    reported = False
    for key in ("input_tokens", "output_tokens"):
        value = usage.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            tokens += value
            reported = True
    if not reported:
        return None
    return Decimal(str(tokens * price_per_token))
