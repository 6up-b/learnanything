"""AD1's paid work under one daily cap (spec §11.4 ``daily_spend_cap_usd``; handoffs §0 rule 6).

``adaptive_difficulty.daily_spend_cap_usd`` is a durable, atomic daily cap in
the vault's spend ledger (RW4a/H1's :class:`SharedDailyEnvelope`, every
process): the outside forecasters' and the feature audit's metered receipts
(owner kinds :data:`OWNER_KINDS`) priced at
``adaptive_difficulty.price_per_million`` plus the reservations in flight. The
Decider is priced at its profile's listed input price; Codex and the ChatGPT
plan are ``estimated_only`` and count nothing.

``LEARNLOOP_AD_MODELS=off`` (set by the test suite, and on a vault-copy run):
no AD job resolves a client unless one was injected.
"""

from __future__ import annotations

import os
from typing import Any

from learnloop.clock import Clock
from learnloop.source_retrieval.service_spend import SharedDailyEnvelope, midnight

ENVELOPE = "adaptive_difficulty.daily_spend_cap_usd"
#: The model-call receipts' owner kinds the cap counts.
FORECAST_OWNER_KIND = "ad_item_forecast"
AUDIT_OWNER_KIND = "ad_feature_audit"
#: AD2+AD3: the relatedness proposal (spec §5.10), inside the same daily cap.
RELATEDNESS_OWNER_KIND = "ad_relatedness"
OWNER_KINDS = (FORECAST_OWNER_KIND, AUDIT_OWNER_KIND, RELATEDNESS_OWNER_KIND)
MODELS_ENV = "LEARNLOOP_AD_MODELS"


def models_off() -> bool:
    return os.environ.get(MODELS_ENV, "").strip().lower() == "off"


def ad_envelope(vault: Any, repository: Any, *, clock: Clock | None = None) -> SharedDailyEnvelope:
    settings = vault.config.adaptive_difficulty
    return SharedDailyEnvelope(
        vault, repository, day=midnight(clock), cap=float(settings.daily_spend_cap_usd), clock=clock,
        name=ENVELOPE, owner_kinds=OWNER_KINDS, price_per_million=settings.price_per_million,
    )


__all__ = ["AUDIT_OWNER_KIND", "ENVELOPE", "FORECAST_OWNER_KIND", "MODELS_ENV", "OWNER_KINDS", "RELATEDNESS_OWNER_KIND",
           "ad_envelope", "models_off"]
