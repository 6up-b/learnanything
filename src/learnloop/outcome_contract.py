"""Versioned observational label eligibility, independent of persistence.

Delayed unassisted retention is distinct from a certified cold measurement.
Only the cold-measurement ledger can establish the latter.
"""
from __future__ import annotations

import json
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

# PF-c's stamp on a grading-evidence row (``attribution_json``) of a criterion
# the valid-alternative gate recorded UNVERIFIED, and the interpretation the
# row was written under (the full rule is documented where the projection
# applies it, ``substrate.canonical_projection``, which re-exports these).
# Defined here, dependency free, so the held-grade predicate
# (``learnloop.held_grades``) reads the same stamp everywhere.
UNVERIFIED_CRITERION_BLOCK = "valid_alternative_unverified"
UNVERIFIED_INTERPRETATION_KEY = "unverified_interpretation"
UNASSESSED_INTERPRETATION = "unassessed"


def _attribution_mapping(attribution: Any) -> Mapping[str, Any] | None:
    if isinstance(attribution, (str, bytes)):
        try:
            attribution = json.loads(attribution)
        except (TypeError, ValueError):
            return None
    return attribution if isinstance(attribution, Mapping) else None


def unverified_evidence_row(attribution: Any) -> bool:
    """Whether a grading-evidence row is a PF-c unverified criterion, under
    either interpretation. ``attribution`` is the row's persisted
    ``attribution_json``: the JSON text or its decoded mapping."""

    mapping = _attribution_mapping(attribution)
    return mapping is not None and mapping.get("negative_evidence_blocked") == UNVERIFIED_CRITERION_BLOCK


def unassessed_evidence_row(attribution: Any) -> bool:
    """Whether a grading-evidence row is a PF-c criterion written under the
    unassessed rule (owner decision 2026-10-12).

    Every reader that turns grading evidence into a grade, a facet outcome, a
    probe feature, a repair verification or a display uses this one test. A
    row written before the rule (no interpretation mark) is False here: it is
    read as it was written.
    """

    mapping = _attribution_mapping(attribution)
    return (
        mapping is not None
        and mapping.get("negative_evidence_blocked") == UNVERIFIED_CRITERION_BLOCK
        and mapping.get(UNVERIFIED_INTERPRETATION_KEY) == UNASSESSED_INTERPRETATION
    )


# The hold (mvp-0.17's proofs route check, re-review F9; since mvp-0.20 the
# grader's own-route rule). A grade with nothing assessed and nothing
# validated is HELD FOR REVIEW: the grader's own grade, provisional, no
# evidence, no FSRS review, no prediction error, until a regrade or an
# adjudication settles it. Unlike PF-c's nothing-assessed answer (verified,
# so correct for scheduling) a held grade is no outcome at all: outcome
# readers exclude it with this reason, and its score is never read as the
# answer's. The hold is one recorded fact, the attempt's latest blind record
# (``grading_support.proof_route_check``, the key both writers use);
# ``attempts.grading_support.apply_route_rule`` writes it for new grades.
GRADE_HELD_FOR_REVIEW = "grade_held_for_review"
#: Route-check gate versions whose records predate the hold: v2 scheduled a
#: held grade as correct, so such a record replays as it was written.
PRE_HOLD_ROUTE_CHECK_VERSIONS = frozenset({"proof-route-check-v1", "proof-route-check-v2"})
#: held-grade-evidence F2: a regrade whose route check failed (``status =
#: unavailable``) on an attempt whose grade was held KEEPS the hold. Its record
#: names the record the hold was carried from under this key; nothing else
#: writes ``held_for_review`` on a check that did not run. mvp-0.17 records
#: only: the own-route rule has no separate call that can fail.
HOLD_KEPT_FROM_KEY = "hold_kept_from"
#: The key a reader's attempt row carries when THE predicate holds its grade
#: (``held_grades.mark_held_attempts``): the row stays (an exposure is
#: an exposure, and its time is the item's last attempt) but its score is no
#: outcome, no failure and no success.
HELD_ROW_KEY = GRADE_HELD_FOR_REVIEW
#: Regrade contracts (``mvp-0.26``): the review reason replay records on an
#: attempt whose current grading epoch cites no assessment contract and is not
#: the attempt's only (first, pre-contract) grade, so nothing recorded says
#: what it was graded out of. Such a grade is held for review exactly as a
#: route-rule hold is (no outcome, no review, no failure, no success) and the
#: ledger's predicate reads the reason (``held_grades``); a regrade or an
#: adjudication that records a contract releases it. Only replay at
#: ``mvp-0.26`` or later writes it, so no earlier vault holds anything by it.
GRADE_CONTRACT_UNRECORDED = "grade_contract_unrecorded"


def grade_held_for_review(grading_support: Mapping[str, Any] | None) -> bool:
    """Did the route rule (or mvp-0.17's route check) hold this grade?

    The RECORD half of the hold: read from a blind run's ``grading_support``
    or the blind record that persists it, never from today's config. A hold
    the rule or the check decided (``status = checked``), or one a failed
    mvp-0.17 regrade check kept (``hold_kept_from``). Whether the attempt is
    held NOW is :func:`grade_is_held` over this and the attempt's current
    evidence.
    """

    proof = (grading_support or {}).get("proof_route_check") or {}
    return (
        isinstance(proof, Mapping)
        and bool(proof.get("held_for_review"))
        and proof.get("version") not in PRE_HOLD_ROUTE_CHECK_VERSIONS
        and (proof.get("status") == "checked" or bool(proof.get(HOLD_KEPT_FROM_KEY)))
    )


def grade_is_held(*, record_held: bool, anything_assessed: bool) -> bool:
    """THE held-grade predicate (held-grade-evidence): is this attempt's grade
    held for review, and so unusable as evidence anywhere?

    Held = the latest blind record holds it (:func:`grade_held_for_review`)
    AND nothing in the attempt's current evidence is assessed: no criterion
    that a live row grades and no live row marks unassessed (the criterion
    vector the attempt step reads). A regrade into a hold supersedes the
    machine-graded rows it replaces (review F1). A regrade
    releases a hold by writing a record without it; an owner adjudication
    (Ruling A's evidence revision) releases it by writing assessed evidence
    over it, so a hold never outlives the revision that settled it.

    Two callers evaluate it, and every reader reads one of them: the attempt
    step in flight (``attempts._compute_resolved_grade_application``, the
    grade being applied, before its blind record is written) and the ledger
    (``learnloop.held_grades.held_for_review_attempts``, re-exported by
    ``substrate.canonical_projection``: any persisted attempt). A held grade
    is the grader's own, provisional score: no outcome, no review, no
    failure, no success, no label.
    """

    return bool(record_held) and not anything_assessed


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
    if row.get("outcome_grade_held_for_review"):
        # mvp-0.17: nothing validated the grade; it is no outcome yet.
        reasons.append(GRADE_HELD_FOR_REVIEW)
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
