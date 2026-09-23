"""Versioned observational label eligibility, independent of persistence.

Delayed unassisted retention is distinct from a certified cold measurement.
Only the cold-measurement ledger can establish the latter.
"""
from __future__ import annotations

import math
from numbers import Real
from typing import Any, Mapping

COLLECTION_VERSION = "learnloop-events-v1"
LABEL_VERSION = "learnloop-outcomes-v1"
RETENTION_MIN_DELAY_SECONDS = 86400


def retention_exclusions(row: Mapping[str, Any]) -> list[str]:
    metadata = row.get("metadata") or {}
    outcome = metadata.get("outcome") or {}
    source = metadata.get("source") or {}
    reasons = []
    hints = row.get("outcome_hints_used", outcome.get("hints_used"))
    primed = row.get("outcome_primed", outcome.get("primed"))
    if hints is None:
        reasons.append("hints_unknown")
    elif hints:
        reasons.append("hinted")
    if primed is None:
        reasons.append("priming_unknown")
    elif primed:
        reasons.append("primed")
    if row.get("intervening_attempt_count", 0):
        reasons.append("intervening_practice")
    if not _observed_delay_at_least(row.get("elapsed_seconds"), RETENTION_MIN_DELAY_SECONDS):
        reasons.append("insufficient_delay")
    source_session = row.get("source_session_id", source.get("session_id"))
    outcome_session = row.get("outcome_session_id", outcome.get("session_id"))
    if source_session is not None and source_session == outcome_session:
        reasons.append("same_session")
    if row.get("outcome_manual_review", outcome.get("manual_review")):
        reasons.append("unresolved_grade")
    if row.get("label_value") is None:
        reasons.append("outcome_unscorable")
    return reasons


def _observed_delay_at_least(elapsed_seconds: Any, minimum: float) -> bool:
    """A missing or non-finite delay is unobserved, so it never qualifies.

    NaN compares false against every bound, so without the finiteness check
    it would pass as a sufficient delay.
    """

    if isinstance(elapsed_seconds, bool) or not isinstance(elapsed_seconds, Real):
        return False
    return math.isfinite(elapsed_seconds) and elapsed_seconds >= minimum
