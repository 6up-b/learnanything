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

# PF-c (owner decision 2026-10-12). The valid-alternative gate's review reason
# (``attempts.grading_support.UNVERIFIED_REVIEW_REASON``; this module stays
# dependency free, a test pins the two equal). On an outcome attempt graded
# under the unassessed rule it is an informational log, not an unresolved
# grade: callers read the attempt's evidence and pass ``outcome_pfc_assessment``
# (``canonical_projection.pfc_assessment``) for every outcome, whatever its
# review reason. The two are read independently (review F7): the attempt step
# records the PF-c reason only when it is the grade's sole review concern, so
# any other reason is a blocking review on a PF-c attempt too, and nothing
# assessed excludes the outcome whatever the reason says. A PF-c attempt
# written before the rule carries no such state and stays ``unresolved_grade``,
# as it always was.
PFC_REVIEW_REASON = "valid_alternative_unverified"
#: Some criteria were assessed: the grade over them is an ordinary outcome.
PFC_PARTIALLY_ASSESSED = "partially_assessed"
#: No criterion was assessed: correct for scheduling, but no measurement.
PFC_NOTHING_ASSESSED = "nothing_assessed"


def retention_exclusions(row: Mapping[str, Any]) -> list[str]:
    metadata = row.get("metadata") or {}
    outcome = metadata.get("outcome") or {}
    source = metadata.get("source") or {}
    pfc_assessment = row.get("outcome_pfc_assessment")
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
    if pfc_assessment == PFC_NOTHING_ASSESSED:
        reasons.append("outcome_unassessed")
    review_reason = row.get("outcome_manual_review_reason", outcome.get("manual_review_reason"))
    pfc_sole_concern = review_reason == PFC_REVIEW_REASON and pfc_assessment in (
        PFC_PARTIALLY_ASSESSED,
        PFC_NOTHING_ASSESSED,
    )
    if row.get("outcome_manual_review", outcome.get("manual_review")) and not pfc_sole_concern:
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
