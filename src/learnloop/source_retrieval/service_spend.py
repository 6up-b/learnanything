"""The canonical-sources service's shared money bounds (spec_source_practice_and_probes_v1 SC10, §7.5).

Every paid step of the service runs under ``SpendBudget`` caps per operation;
these envelopes bound the SUM (Codex review F2, re-review F2):

* **the daily cap** (``source_service.max_daily_cost_usd``, metered): shared
  by every thread AND every process that opens the vault. Each metered request
  reserves its estimate in ``source_service_spend`` inside one BEGIN
  IMMEDIATE transaction that computes the day's total and checks it plus the
  estimate against the cap, so a request that would pass it is refused before
  it is sent, and a sidecar and a CLI batch cannot both spend the same
  allowance. Every complete service operation runs under it: retrieval
  (embeddings, rewrites, reranks, verification), valuation and imports;
* **one operation's cap** (an import: ``import_max_cost_usd``; a comparison:
  ``compare_max_cost_usd``), only when the owner sets one: both default to
  None, no cap (owner, 2026-10-13: spend is observed in real use through
  ``learnloop sources report`` and caps set later from it; the provider key's
  own limit is the hard backstop);
* **a batch's cap** (``--max-cost-usd`` of an owner-run harvest or verify).

The day's total is ONE accounting function
(``db.stores.source_service.service_spend_accounting``), read by admission,
recovery and every report, which counts each linked request exactly once
(sources-spend-accounting: Codex F2 reopened, F14) and a legacy one at least
once, never less than was spent (a legacy row suppresses no receipt; the
overlap is reported as ``legacy.uncertain_usd``). A request's root receipt
names its reservation; while the reservation's owner lives it counts the
larger of its charge and what that receipt shows (a worker that died after
its receipt but before reconciling it leaves both), once reconciled what the
receipt shows, and a receipt naming no reservation counts by its own cost.
Each process renews the leases of its reservations in flight
(``LEASE_SECONDS``, every ``HEARTBEAT_SECONDS``); once a dead owner's lease
has run out, the next admission recovers its reservation: reconciled with its
receipt, or released when it has none (it was never sent).

Subscription requests (Codex, the ChatGPT plan) are never refused by money:
their tokens and owner-priced dollars are reported as ``estimated_only``, with
no request-count bound (Slice A §5 rule 6).
"""
from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import closing, contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import sqlite3
import threading
from typing import Any

from learnloop.ai.spend import SpendEnvelope, SpendLimitExceeded, spend_envelopes
from learnloop.clock import Clock, SystemClock, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_service import (
    SERVICE_OWNER_KINDS,
    charge_service_spend,
    release_service_spend,
    renew_service_spend_leases,
    reserve_service_spend,
    service_spend_accounting,
    service_spend_report,
    settle_service_spend,
)
from learnloop.ids import new_ulid
from learnloop.practice_index.paid import SUBSCRIPTION_PROFILE_TYPES
from learnloop.vault.models import LoadedVault

DAILY_ENVELOPE = "source_service.max_daily_cost_usd"
#: This process, on its reservations: the owner token their writes are fenced by.
PROCESS = "proc_" + new_ulid()
#: How long a reservation in flight stays its owner's without a renewal. A
#: process renews its leases every ``HEARTBEAT_SECONDS`` while it lives; a
#: reservation whose lease has run out has a terminal owner, and the next
#: admission recovers it. Process-liveness bounds, not money decisions.
LEASE_SECONDS = 300
HEARTBEAT_SECONDS = 60

#: "The service's own rate" (``source_service.llm_price_per_million``), as
#: distinct from an explicit None (no rate).
_SERVICE_PRICE = object()

_DAILY: dict[tuple[str, str, float, str], SpendEnvelope] = {}
_DAILY_LOCK = threading.Lock()


class _Leases:
    """This process's reservations in flight, whose leases it renews while it lives."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._held: dict[str, tuple[Repository, set[str]]] = {}
        self._thread: threading.Thread | None = None
        # Set when the last lease is dropped: the heartbeat ends then, not a
        # whole beat later (a thread with nothing to renew is not kept).
        self._idle = threading.Event()

    def hold(self, repository: Repository, handle: str) -> None:
        with self._lock:
            _repository, handles = self._held.setdefault(str(repository.sqlite_path), (repository, set()))
            handles.add(handle)
            self._idle.clear()
            if self._thread is None:
                self._thread = threading.Thread(target=self._run, name="source-service-spend-leases", daemon=True)
                self._thread.start()

    def drop(self, repository: Repository, handle: str) -> None:
        with self._lock:
            key = str(repository.sqlite_path)
            entry = self._held.get(key)
            if entry is None:
                return
            entry[1].discard(handle)
            if not entry[1]:
                del self._held[key]
            if not self._held:
                self._idle.set()

    def renew_now(self) -> int:
        """Renew every held lease now (the heartbeat's one beat)."""

        with self._lock:
            work = [(repository, sorted(handles)) for repository, handles in self._held.values()]
        renewed = 0
        until = datetime.now(timezone.utc) + timedelta(seconds=LEASE_SECONDS)
        for repository, handles in work:
            if not Path(repository.sqlite_path).exists():
                continue
            try:
                with repository.atomic():
                    renewed += renew_service_spend_leases(repository.connection(), handles, process=PROCESS,
                                                          until=until)
            except Exception:  # noqa: BLE001 - the next beat retries; a lease outlives several misses
                continue
        return renewed

    def _run(self) -> None:
        while True:
            self._idle.wait(HEARTBEAT_SECONDS)
            with self._lock:
                if not self._held:
                    self._thread = None
                    return
            try:
                self.renew_now()
            except Exception:  # noqa: BLE001 - the heartbeat outlives any one failed beat
                continue


_LEASES = _Leases()


class SharedDailyEnvelope(SpendEnvelope):
    """The daily cap, reserved transactionally in the vault database.

    ``reserve`` recovers orphaned reservations and admits a request only when
    the day's total (``service_spend_accounting``) plus its estimate fits the
    cap, in one BEGIN IMMEDIATE transaction. The reservation is a row its
    process's heartbeat keeps leased; its writes (charge, settle) are fenced
    by this process's token. Subscription requests reserve nothing
    (``estimated_only``).
    """

    def __init__(self, vault: LoadedVault, repository: Repository, *, day: str, cap: float,
                 clock: Clock | None = None, name: str = DAILY_ENVELOPE,
                 owner_kinds: Sequence[str] | None = SERVICE_OWNER_KINDS,
                 price_per_million: float | None | object = _SERVICE_PRICE) -> None:
        super().__init__(name, cap)
        self._vault = vault
        self._repository = repository
        self._since = day  # UTC midnight
        self._day = day[:10]
        #: The clock the envelope was opened with: every reservation, charge,
        #: settlement and total is stamped by it (the day it guards is its day).
        self._clock = clock
        #: Another daily cap kept in the same ledger (reader workbench RW4a:
        #: ``library_ask.max_daily_cost_usd``) names its own envelope, the
        #: receipt kinds it counts and its owner's rate; the defaults are the
        #: service's own cap, unchanged.
        self._owner_kinds = owner_kinds
        self._price = (vault.config.source_service.llm_price_per_million
                       if price_per_million is _SERVICE_PRICE else price_per_million)

    def _now(self) -> str:
        return utc_now_iso(self._clock)

    def accounting(self, connection: sqlite3.Connection, now: str | None = None) -> dict[str, Any]:
        return daily_accounting(connection, self._vault, self._since, envelope=self.name, now=now or self._now(),
                                owner_kinds=self._owner_kinds, price_per_million=self._price)

    def _total(self) -> Decimal:
        with closing(connect(self._repository.sqlite_path, read_only=True)) as connection:
            return Decimal(str(self.accounting(connection)["usd"]))

    def reservation_ref(self, handle: object) -> str | None:
        return handle if isinstance(handle, str) else None

    def reserve(self, usd: Decimal) -> object:
        handle = "ssp_" + new_ulid()
        with self._repository.atomic():
            admitted, total = reserve_service_spend(
                self._repository.connection(), id=handle, envelope=self.name, day=self._day, since=self._since,
                usd=float(usd), cap=float(self.max_usd), process=PROCESS, now=self._now(),
                lease_seconds=LEASE_SECONDS, price_per_million=self._price,
                subscription_providers=subscription_providers(self._vault), owner_kinds=self._owner_kinds)
        if not admitted:
            with self._lock:
                self._refused += 1
            raise SpendLimitExceeded(
                f"{self.name}: ${total + float(usd):.4f} would pass the ${float(self.max_usd):.4f} cap "
                "(shared by every process using this vault)")
        _LEASES.hold(self._repository, handle)
        return handle

    def unreserve(self, handle: object) -> None:
        if isinstance(handle, str):
            try:
                with self._repository.atomic():
                    release_service_spend(self._repository.connection(), handle, process=PROCESS)
            finally:
                _LEASES.drop(self._repository, handle)

    def charge(self, usd: Decimal, handle: object = None) -> None:
        if usd > 0 and isinstance(handle, str):
            with self._repository.atomic():
                charge_service_spend(self._repository.connection(), handle, float(usd), self._now(),
                                     process=PROCESS)

    def settle(self, handle: object, actual: Decimal | None = None) -> None:
        if isinstance(handle, str):
            try:
                with self._repository.atomic():
                    settle_service_spend(self._repository.connection(), handle, self._now(),
                                         None if actual is None else float(actual), process=PROCESS)
            finally:
                _LEASES.drop(self._repository, handle)

    def report(self) -> dict[str, object]:
        """The inherited report (this process's refusals and ``estimated_only``
        tally), with the day's total and its full breakdown (``accounting``:
        reservations by state, pending recovery, legacy coverage, pricing)
        from one read of ``service_spend_accounting``."""

        with closing(connect(self._repository.sqlite_path, read_only=True)) as connection:
            accounting = self.accounting(connection)
        report = super().report()
        total = float(accounting["usd"])
        report["metered_usd"] = total
        report["remaining_usd"] = max(0.0, float(self.max_usd) - total)
        report["basis"] = ("every process's reservations, each counted once with the receipts naming it, plus "
                           "the service's receipts that name none (source_service_spend)")
        report["accounting"] = accounting
        return report


def daily_accounting(connection: sqlite3.Connection, vault: LoadedVault, since: str, *,
                     envelope: str = DAILY_ENVELOPE, now: str | None = None,
                     owner_kinds: Sequence[str] | None = SERVICE_OWNER_KINDS,
                     price_per_million: float | None | object = _SERVICE_PRICE) -> dict[str, Any]:
    """The daily cap's total since ``since`` (UTC midnight): the one function
    admission, recovery and every report read."""

    price = vault.config.source_service.llm_price_per_million if price_per_million is _SERVICE_PRICE \
        else price_per_million
    return service_spend_accounting(
        connection, envelope=envelope, day=since[:10], since=since, now=now or utc_now_iso(),
        price_per_million=price,  # type: ignore[arg-type]
        subscription_providers=subscription_providers(vault), owner_kinds=owner_kinds)


def subscription_providers(vault: LoadedVault) -> frozenset[str]:
    """Provider names whose profile bills the owner's subscription."""

    return frozenset(name for name, profile in vault.config.ai.providers.items()
                     if str(getattr(profile, "type", "") or "").lower() in SUBSCRIPTION_PROFILE_TYPES)


def midnight(clock: Clock | None = None) -> str:
    return utc_now_iso(clock)[:10] + "T00:00:00"


def service_spend_today(vault: LoadedVault, repository: Repository, clock: Clock | None = None) -> dict[str, Any]:
    """The service's spend since UTC midnight, as the daily cap counts it:
    metered dollars (``usd``: ``reservations_usd``, every reservation counted
    once with its receipts, plus ``unlinked_receipts_usd``) and the
    subscription's ``estimated_only`` tokens and dollars."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return daily_accounting(connection, vault, midnight(clock), now=utc_now_iso(clock))


def spend_report(vault: LoadedVault, repository: Repository, *, days: int = 7, top: int = 5,
                 clock: Clock | None = None) -> dict[str, Any]:
    """The service's actual spend over the last ``days`` UTC days (today
    included), for setting caps from real use (owner, 2026-10-13): per day the
    metered receipt cost and the reservations, reserved vs settled; the
    largest operations; and today's daily guard (what admission counts, the
    cap and what remains). Reads only."""

    today = utc_now_iso(clock)[:10]
    first = datetime.fromisoformat(today) - timedelta(days=max(1, int(days)) - 1)
    span = [(first + timedelta(days=offset)).strftime("%Y-%m-%d") for offset in range(max(1, int(days)))]
    service = vault.config.source_service
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        report = service_spend_report(
            connection, envelope=DAILY_ENVELOPE, days=span, price_per_million=service.llm_price_per_million,
            subscription_providers=subscription_providers(vault), owner_kinds=SERVICE_OWNER_KINDS, top=top)
        guard = daily_accounting(connection, vault, midnight(clock), now=utc_now_iso(clock))
    cap = float(service.max_daily_cost_usd)
    report["daily_guard"] = {
        "day": today, "cap_usd": cap, "counted_usd": float(guard["usd"]),
        "remaining_usd": max(0.0, cap - float(guard["usd"])),
        "uncertain_legacy_usd": float(guard["legacy"]["uncertain_usd"]),
    }
    report["operation_caps"] = {"import_max_cost_usd": service.import_max_cost_usd,
                                "compare_max_cost_usd": service.compare_max_cost_usd}
    report["basis"] = ("metered dollars from the receipts (reported cost, else tokens at the request's recorded "
                       "rate, else at source_service.llm_price_per_million); subscription requests are "
                       "estimated_only and never counted against a cap")
    return report


def _clock_key(clock: Clock | None) -> str:
    """One shared envelope per database and day for the system clock; an
    injected clock (a test's, a replay's) gets its own, stamped by it."""

    return "system" if clock is None or isinstance(clock, SystemClock) else f"clock:{id(clock)}"


def daily_envelope(vault: LoadedVault, repository: Repository, clock: Clock | None = None) -> SpendEnvelope:
    """The daily envelope for this database and UTC day, shared through the
    database by every process (one object per process for its threads). Its
    reservations, charges and settlements are stamped by ``clock``."""

    cap = float(vault.config.source_service.max_daily_cost_usd)
    day = midnight(clock)
    key = (str(repository.sqlite_path), day, cap, _clock_key(clock))
    with _DAILY_LOCK:
        envelope = _DAILY.get(key)
        if envelope is None:
            envelope = SharedDailyEnvelope(vault, repository, day=day, cap=cap, clock=clock)
            _DAILY[key] = envelope
        return envelope


@contextmanager
def service_spend(vault: LoadedVault, repository: Repository, *, max_usd: float | None = None,
                  name: str = "operation", clock: Clock | None = None) -> Iterator[dict[str, SpendEnvelope]]:
    """The daily envelope, plus one for this operation when ``max_usd`` is given."""

    envelopes = {"daily": daily_envelope(vault, repository, clock)}
    if max_usd is not None:
        envelopes[name] = SpendEnvelope(name, float(max_usd))
    with spend_envelopes(*envelopes.values()):
        yield envelopes


def batch_envelope(name: str, max_usd: float) -> SpendEnvelope:
    return SpendEnvelope(name, float(max_usd))


__all__ = [
    "DAILY_ENVELOPE",
    "HEARTBEAT_SECONDS",
    "LEASE_SECONDS",
    "SharedDailyEnvelope",
    "batch_envelope",
    "daily_accounting",
    "daily_envelope",
    "midnight",
    "service_spend",
    "service_spend_today",
    "spend_report",
    "subscription_providers",
]
