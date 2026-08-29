"""Intent-first session composition — SHADOW MODE ONLY (knowledge-model §11.2).

Session composition, per §11.2, should select an **intent** first —

    diagnose_uncertainty | repair_misconception | restore_retrievability |
    build_missing_knowledge | develop_transfer | practice_integration

— and then rank candidates within it. This module computes that intent choice and
the within-intent rankings and LOGS them alongside live behavior. It is strictly
shadow: it never reorders the live queue, exactly like the KM3a
``routine_planner_shadow`` disagreement signal.

Promotion of an intent-first policy to LIVE selection requires held-out predictive
gains and is **NOT this milestone** (the sim-sweep finding is that
membership/gating decides outcomes while ranking weights are decision-inert, so an
intent policy earns live authority only by beating the current composition on
held-out data). Until then the intent + rankings are recorded for offline
comparison via ``shadow_intent_report`` and nothing else.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from learnloop.vault.models import LoadedVault


class SessionIntent(str, Enum):
    DIAGNOSE_UNCERTAINTY = "diagnose_uncertainty"
    REPAIR_MISCONCEPTION = "repair_misconception"
    RESTORE_RETRIEVABILITY = "restore_retrievability"
    BUILD_MISSING_KNOWLEDGE = "build_missing_knowledge"
    DEVELOP_TRANSFER = "develop_transfer"
    PRACTICE_INTEGRATION = "practice_integration"


# SHADOW intent-selection priority. NOTE: this order is decision-inert — it never
# steers the live queue (which stays exactly as composed). It only picks which
# intent's ranking to compare against live behavior in the shadow log.
_INTENT_PRIORITY: tuple[SessionIntent, ...] = (
    SessionIntent.DIAGNOSE_UNCERTAINTY,
    SessionIntent.REPAIR_MISCONCEPTION,
    SessionIntent.PRACTICE_INTEGRATION,
    SessionIntent.DEVELOP_TRANSFER,
    SessionIntent.RESTORE_RETRIEVABILITY,
    SessionIntent.BUILD_MISSING_KNOWLEDGE,
)

_INTEGRATION_MODES: frozenset[str] = frozenset(
    {"constructed_response", "proof", "derivation"}
)
_RESTORE_FORGETTING_THRESHOLD = 0.5


def classify_intent(vault: LoadedVault, item: Any) -> SessionIntent:
    """Classify one scheduled candidate into a §11.2 session intent (shadow)."""

    components = getattr(item, "components", {}) or {}
    pi = vault.practice_items.get(getattr(item, "practice_item_id", None))
    if components.get("probe_eig", 0.0) > 0.0:
        return SessionIntent.DIAGNOSE_UNCERTAINTY
    if components.get("recent_error", 0.0) > 0.0 and pi is not None and getattr(pi, "repair_targets", None):
        return SessionIntent.REPAIR_MISCONCEPTION
    if pi is not None and (getattr(pi, "transfer_distance", None) or 0.0) > 0.0:
        return SessionIntent.DEVELOP_TRANSFER
    if pi is not None and getattr(pi, "practice_mode", None) in _INTEGRATION_MODES:
        return SessionIntent.PRACTICE_INTEGRATION
    if components.get("forgetting_risk", 0.0) >= _RESTORE_FORGETTING_THRESHOLD:
        return SessionIntent.RESTORE_RETRIEVABILITY
    return SessionIntent.BUILD_MISSING_KNOWLEDGE


def shadow_intent_plan(
    vault: LoadedVault, queue: list[Any], *, top_k: int = 3
) -> dict[str, Any] | None:
    """Compute the shadow intent + within-intent rankings for a live queue.

    Returns ``None`` for an empty queue. The plan reads the already-composed live
    queue (ranked by selection reward) and never mutates it; ``shadow_first_item``
    is what an intent-first policy WOULD serve, compared to the live queue's head.
    """

    if not queue:
        return None
    intents: dict[str, list[str]] = {}
    counts: dict[str, int] = {}
    for item in queue:
        intent = classify_intent(vault, item).value
        counts[intent] = counts.get(intent, 0) + 1
        intents.setdefault(intent, []).append(item.practice_item_id)

    selected_intent: str | None = None
    for candidate in _INTENT_PRIORITY:
        if candidate.value in intents:
            selected_intent = candidate.value
            break

    live_first = queue[0].practice_item_id
    shadow_first = intents[selected_intent][0] if selected_intent else live_first
    return {
        "selected_intent": selected_intent,
        "intent_counts": counts,
        "rankings_by_intent": {k: v[:top_k] for k, v in intents.items()},
        "live_first_item": live_first,
        "shadow_first_item": shadow_first,
        "agrees_with_live": shadow_first == live_first,
    }
