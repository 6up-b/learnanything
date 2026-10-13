"""The canonical-sources service's shared money bounds (spec_source_practice_and_probes_v1 SC10, §7.5).

Every paid step of the service runs under ``SpendBudget`` caps per operation;
these envelopes bound the SUM (Codex review F2):

* **the daily cap** (``source_service.max_daily_cost_usd``, metered): one
  envelope per database and UTC day, shared by every thread of the process. It
  reads the service's metered receipts since midnight (every process's) at
  each reservation and adds this process's requests still in flight, so a
  request that would pass the cap is refused before it is sent;
* **one operation's cap** (an import: ``import_max_cost_usd``);
* **a batch's cap** (``--max-cost-usd`` of an owner-run harvest or verify).

Subscription requests (Codex, the ChatGPT plan) are never refused by money:
their tokens and owner-priced dollars are reported as ``estimated_only``, with
no request-count bound (Slice A §5 rule 6).
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import closing, contextmanager
import threading
from typing import Any

from learnloop.ai.spend import SpendEnvelope, spend_envelopes
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_service import SERVICE_OWNER_KINDS, spend_since
from learnloop.practice_index.paid import SUBSCRIPTION_PROFILE_TYPES
from learnloop.vault.models import LoadedVault

_DAILY: dict[tuple[str, str, float], SpendEnvelope] = {}
_DAILY_LOCK = threading.Lock()


def subscription_providers(vault: LoadedVault) -> frozenset[str]:
    """Provider names whose profile bills the owner's subscription."""

    return frozenset(name for name, profile in vault.config.ai.providers.items()
                     if str(getattr(profile, "type", "") or "").lower() in SUBSCRIPTION_PROFILE_TYPES)


def midnight(clock: Clock | None = None) -> str:
    return utc_now_iso(clock)[:10] + "T00:00:00"


def service_spend_today(vault: LoadedVault, repository: Repository, clock: Clock | None = None) -> dict[str, Any]:
    """The service's spend since UTC midnight: metered dollars (the daily
    cap's basis) and the subscription's ``estimated_only`` tokens and dollars."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return spend_since(connection, midnight(clock), owner_kinds=SERVICE_OWNER_KINDS,
                           price_per_million=vault.config.source_service.llm_price_per_million,
                           subscription_providers=subscription_providers(vault))


def daily_envelope(vault: LoadedVault, repository: Repository, clock: Clock | None = None) -> SpendEnvelope:
    """The process-wide daily envelope for this database and UTC day."""

    cap = float(vault.config.source_service.max_daily_cost_usd)
    day = midnight(clock)
    key = (str(repository.sqlite_path), day, cap)
    with _DAILY_LOCK:
        envelope = _DAILY.get(key)
        if envelope is None:
            def observed() -> float:
                return float(service_spend_today(vault, repository, clock)["usd"])

            envelope = SpendEnvelope("source_service.max_daily_cost_usd", cap, observed=observed)
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
    "batch_envelope",
    "daily_envelope",
    "midnight",
    "service_spend",
    "service_spend_today",
    "subscription_providers",
]
