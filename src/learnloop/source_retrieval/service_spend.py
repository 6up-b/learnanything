"""The canonical-sources service's shared money bounds (spec_source_practice_and_probes_v1 SC10, §7.5).

Every paid step of the service runs under ``SpendBudget`` caps per operation;
these envelopes bound the SUM (Codex review F2, re-review F2):

* **the daily cap** (``source_service.max_daily_cost_usd``, metered): shared
  by every thread AND every process that opens the vault. Each metered request
  reserves its estimate in ``source_service_spend`` inside one BEGIN
  IMMEDIATE transaction that checks the day's total (every process's
  reservations PLUS the service's receipts no reservation covers, such as
  spend from before the ledger existed) plus the estimate against the cap, so
  a request that would pass it is refused before it is sent, and a sidecar
  and a CLI batch cannot both spend the same allowance. A request's root
  receipt names its reservation, so a finished request counts once.
  Every complete service operation runs under it: retrieval (embeddings,
  rewrites, reranks, verification), valuation and imports;
* **one operation's cap** (an import: ``import_max_cost_usd``);
* **a batch's cap** (``--max-cost-usd`` of an owner-run harvest or verify).

Subscription requests (Codex, the ChatGPT plan) are never refused by money:
their tokens and owner-priced dollars are reported as ``estimated_only``, with
no request-count bound (Slice A §5 rule 6).
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import closing, contextmanager
from decimal import Decimal
import sqlite3
import threading
from typing import Any

from learnloop.ai.spend import SpendEnvelope, SpendLimitExceeded, spend_envelopes
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_service import (
    SERVICE_OWNER_KINDS,
    charge_service_spend,
    release_service_spend,
    reserve_service_spend,
    service_spend_ids,
    service_spend_total,
    settle_service_spend,
    spend_since,
)
from learnloop.ids import new_ulid
from learnloop.practice_index.paid import SUBSCRIPTION_PROFILE_TYPES
from learnloop.vault.models import LoadedVault

DAILY_ENVELOPE = "source_service.max_daily_cost_usd"
#: This process, on its reservations (a crashed process's stay counted).
PROCESS = "proc_" + new_ulid()

_DAILY: dict[tuple[str, str, float], SpendEnvelope] = {}
_DAILY_LOCK = threading.Lock()


class SharedDailyEnvelope(SpendEnvelope):
    """The daily cap, reserved transactionally in the vault database (re-review F2).

    ``reserve`` admits a request only when the day's total plus its estimate
    fits the cap. The total is every process's reservations PLUS the
    service's receipts that no reservation covers (spend from before the
    ledger existed, or by a path outside the envelope): never the larger of
    the two (Codex third pass F2), and never a finished request twice, since
    its root receipt names its reservation (``reservation_ref``). The
    reservation is a row: in flight it counts its estimate (reconciled
    upward); once the request finished it counts the cost the provider
    reported, as the receipt does, else its estimate. Subscription requests
    reserve nothing (``estimated_only``).
    """

    def __init__(self, vault: LoadedVault, repository: Repository, *, day: str, cap: float) -> None:
        super().__init__(DAILY_ENVELOPE, cap)
        self._vault = vault
        self._repository = repository
        self._since = day  # UTC midnight
        self._day = day[:10]

    def _unledgered(self, connection: sqlite3.Connection) -> float:
        """The service's receipts today that no reservation of this envelope covers."""
        return unledgered_receipts_usd(connection, self._vault, self._since, self.name)

    def _total(self) -> Decimal:
        with closing(connect(self._repository.sqlite_path, read_only=True)) as connection:
            ledger = service_spend_total(connection, self.name, self._day)
            unledgered = self._unledgered(connection)
        return Decimal(str(ledger + unledgered))

    def reservation_ref(self, handle: object) -> str | None:
        return handle if isinstance(handle, str) else None

    def reserve(self, usd: Decimal) -> object:
        handle = "ssp_" + new_ulid()
        with self._repository.atomic():
            connection = self._repository.connection()
            admitted, total = reserve_service_spend(
                connection, id=handle, envelope=self.name, day=self._day, usd=float(usd),
                cap=float(self.max_usd), process=PROCESS, now=utc_now_iso(),
                unledgered_usd=self._unledgered(connection))
        if not admitted:
            with self._lock:
                self._refused += 1
            raise SpendLimitExceeded(
                f"{self.name}: ${total + float(usd):.4f} would pass the ${float(self.max_usd):.4f} cap "
                "(shared by every process using this vault)")
        return handle

    def unreserve(self, handle: object) -> None:
        if isinstance(handle, str):
            with self._repository.atomic():
                release_service_spend(self._repository.connection(), handle)

    def charge(self, usd: Decimal, handle: object = None) -> None:
        if usd > 0 and isinstance(handle, str):
            with self._repository.atomic():
                charge_service_spend(self._repository.connection(), handle, float(usd), utc_now_iso())

    def settle(self, handle: object, actual: Decimal | None = None) -> None:
        if isinstance(handle, str):
            with self._repository.atomic():
                settle_service_spend(self._repository.connection(), handle, utc_now_iso(),
                                     None if actual is None else float(actual))

    def report(self) -> dict[str, object]:
        report = super().report()
        report["basis"] = ("reservations shared by every process (source_service_spend), plus the service's "
                           "receipts no reservation covers")
        return report


def unledgered_receipts_usd(connection: sqlite3.Connection, vault: LoadedVault, since: str,
                            envelope: str = DAILY_ENVELOPE) -> float:
    """Metered dollars of the service's receipts since ``since`` whose request
    no reservation of ``envelope`` that day covers."""

    return float(_receipt_spend(connection, vault, since, envelope)["usd"])


def _receipt_spend(connection: sqlite3.Connection, vault: LoadedVault, since: str, envelope: str) -> dict[str, Any]:
    return spend_since(connection, since, owner_kinds=SERVICE_OWNER_KINDS,
                       price_per_million=vault.config.source_service.llm_price_per_million,
                       subscription_providers=subscription_providers(vault),
                       ledgered=service_spend_ids(connection, envelope, since[:10]))


def subscription_providers(vault: LoadedVault) -> frozenset[str]:
    """Provider names whose profile bills the owner's subscription."""

    return frozenset(name for name, profile in vault.config.ai.providers.items()
                     if str(getattr(profile, "type", "") or "").lower() in SUBSCRIPTION_PROFILE_TYPES)


def midnight(clock: Clock | None = None) -> str:
    return utc_now_iso(clock)[:10] + "T00:00:00"


def service_spend_today(vault: LoadedVault, repository: Repository, clock: Clock | None = None) -> dict[str, Any]:
    """The service's spend since UTC midnight: metered dollars (the daily
    cap's basis: every process's reservations plus the receipts no
    reservation covers) and the subscription's ``estimated_only`` tokens and
    dollars."""

    since = midnight(clock)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        spent = _receipt_spend(connection, vault, since, DAILY_ENVELOPE)
        ledger = service_spend_total(connection, DAILY_ENVELOPE, since[:10])
    spent["unledgered_receipts_usd"] = spent["usd"]
    spent["reserved_usd"] = ledger
    spent["usd"] = float(spent["usd"]) + ledger
    return spent


def daily_envelope(vault: LoadedVault, repository: Repository, clock: Clock | None = None) -> SpendEnvelope:
    """The daily envelope for this database and UTC day, shared through the
    database by every process (one object per process for its threads)."""

    cap = float(vault.config.source_service.max_daily_cost_usd)
    day = midnight(clock)
    key = (str(repository.sqlite_path), day, cap)
    with _DAILY_LOCK:
        envelope = _DAILY.get(key)
        if envelope is None:
            envelope = SharedDailyEnvelope(vault, repository, day=day, cap=cap)
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
    "SharedDailyEnvelope",
    "batch_envelope",
    "daily_envelope",
    "midnight",
    "service_spend",
    "service_spend_today",
    "subscription_providers",
    "unledgered_receipts_usd",
]
