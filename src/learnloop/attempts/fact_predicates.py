"""The yes-or-no questions readers ask of an attempt's facts, each under its owner's name.

Every reader that decides whether an attempt was "assisted", "cold", "primed" or "eligible" asks its own question
for its own purpose, and several of those questions differ on purpose (see the discrepancy ledger in
``docs/reviews/ep0-attempt-facts.md``): certification's cold probe and the canonical projection count a hinted
attempt type as assisted, intervention outcomes also count an open-text answer, the coldness receipt also counts any
recorded reveal, the router card and the chat packet call only a primed attempt "assisted". None of them is the
right one; each is right for its reader. So there is no single ``assisted`` here: each function below reproduces
one reader's question over :class:`~learnloop.attempts.facts.AttemptFacts`, with the arguments that reader needs,
and names the module that owns it.

A function either holds its reader's kernel (moved here verbatim, the reader now calling it through a compatibility
adapter that builds the facts from the values it read before) or delegates to the owner's function where the owner
keeps it (the canonical causal-activity policy, intervention outcomes). Reading a submitted count or flag goes
through the same coercion the reader applied (``int(x or 0)``, ``bool(x)``, plain truthiness), never a normalized
copy, so a value the reader treated one way is treated the same way here.

Adaptive difficulty's ``help_timing`` and ``category`` (``adaptive_difficulty.outcomes``) are this module's
siblings but stay with their owner: adaptive difficulty imports nothing of ``learnloop.attempts`` (its evidence
guard), and nothing here imports adaptive difficulty. :class:`AttemptFacts` carries every input they read.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import Any

from learnloop.attempts.facts import AttemptFacts
from learnloop.diagnosis.causal_activity_policy import attempt_counts_as_assisted, resolve_attempt_activity_policy
from learnloop.substrate.intervention_outcomes import is_assisted as _intervention_is_assisted

# -- the canonical causal-activity policy (owner: diagnosis.causal_activity_policy) ------------------------------


def counts_as_assisted(facts: AttemptFacts) -> bool:
    """The canonical assistance test (``attempt_counts_as_assisted``, policy ``causal_activity_v1``): a legacy
    assisted attempt type, any hint, or primed. Readers: certification's cold probe, the scheduler's "on your own",
    the diagnosis scoreboard."""

    return attempt_counts_as_assisted(attempt_type=facts.produced_as, primed=facts.primed,
                                      hints_used=facts.hints_used)


def recorded_counts_as_assisted(facts: AttemptFacts, recorded: Mapping[str, Any] | None,
                                reference_status: str | None = None) -> bool:
    """The canonical test unioned with the attempt's recorded causal classification
    (``resolve_attempt_activity_policy``): what ``facet_outcome_observations.assisted`` stores, and what the
    canonical projection and the facet timeline read."""

    return resolve_attempt_activity_policy(
        attempt_type=facts.produced_as, hints_used=facts.hints_used, primed=facts.primed, recorded=recorded,
        reference_status=reference_status).counts_as_assisted


# -- intervention outcomes (owner: substrate.intervention_outcomes) ----------------------------------------------


def intervention_assisted(facts: AttemptFacts) -> bool:
    """Intervention outcomes' test (``intervention_outcomes.is_assisted``): any attempt type outside the three
    unaided productions (so an open-text answer counts), a hint, or primed. What
    ``retrieval_interventions.next_assisted`` stores; the Reader's report and follow-ups read it too."""

    return _intervention_is_assisted({"attempt_type": facts.produced_as, "hints_used": facts.hints_used,
                                      "primed": facts.primed})


# -- the coldness receipt's unassisted dimension (owner: attempts.coldness_receipt) ------------------------------


def cold_item_reveal_rows(scan: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Ledger rows (migration 154) that exposed the COLD item's own answer."""

    return [
        dict(event)
        for event in scan.get("events") or []
        if event.get("ledger") == "reveal_events"
        and event.get("why") == "reveal_ledger_answer_exposed_on_cold_item"
    ]


def unassisted_for_coldness(facts: AttemptFacts, scan: Mapping[str, Any] | None) -> tuple[str, dict[str, Any]]:
    """The coldness receipt's ``unassisted`` dimension for a cold attempt: ``(status, evidence)``.

    Stricter than the canonical test on purpose: any recorded reveal of the cold item's answer inside the
    measurement window (``scan``) fails it, below the auto-prime threshold too, with the rows as the evidence;
    ``reveal_ledger_scanned`` says whether a scan was made at all."""

    hints = int(facts.hints_used or 0)
    primed = bool(facts.primed)
    ledger_rows = cold_item_reveal_rows(scan) if scan is not None else []
    ok = hints == 0 and not primed and not ledger_rows
    evidence: dict[str, Any] = {
        "hints_used": hints,
        "primed": primed,
        "attempt_type": str(facts.produced_as or "") or None,
        "reveal_ledger_rows": ledger_rows,
        "reveal_ledger_amount": sum(
            float(row.get("amount") or 0.0) for row in ledger_rows
        ),
        "reveal_ledger_scanned": scan is not None,
        "rule": (
            "pass requires hints_used == 0, primed false, AND no recorded "
            "reveal of this item's answer in the measurement window"
        ),
    }
    if ledger_rows:
        evidence["violation"] = "answer_revealed_before_the_cold_attempt"
    return ("pass" if ok else "fail"), evidence


# -- the FSRS rating cap (owner: attempts.attempts, the grade application) ---------------------------------------


def fsrs_cap_value(mapping: dict[int | str, object], hints_used: int) -> object | None:
    """The item's ``fsrs_rating_cap_by_hint`` entry for a hint count: the exact key, its string form, else the
    largest numeric key at or below the count (None when there is none)."""

    if hints_used in mapping:
        return mapping[hints_used]
    string_key = str(hints_used)
    if string_key in mapping:
        return mapping[string_key]
    numeric_keys: list[int] = []
    for key in mapping:
        try:
            numeric_keys.append(int(key))
        except (TypeError, ValueError):
            continue
    eligible = [key for key in numeric_keys if key <= hints_used]
    if not eligible:
        return None
    return mapping.get(max(eligible)) or mapping.get(str(max(eligible)))


def fsrs_rating_cap(facts: AttemptFacts, cap_by_hint: dict[int | str, object]) -> object | None:
    """The cap the item's hint policy puts on an attempt's FSRS rating, from the submitted hint count (the
    grade application reads ``draft.hints_used``; replay and fitting the stored ``hints_used``)."""

    return fsrs_cap_value(cap_by_hint, facts.hints_used)


# -- the diagnoser's history (owner: diagnosis.split.history) ----------------------------------------------------

#: The attempt types the diagnoser's history calls assisted. ``primed`` is a separate field there, and a diagnostic
#: probe is not assisted by its type.
DIAGNOSER_ASSISTED_TYPES = frozenset(
    {"hinted_attempt", "guided_walkthrough", "reconstruction_after_walkthrough"}
)


def diagnoser_assisted(facts: AttemptFacts) -> bool:
    """The diagnoser's ``assisted`` (``HistoryAttempt.assisted``): a hint, or an assisted attempt type; primed is
    its own field, so a primed attempt without a hint is not assisted here."""

    return bool(facts.hints_used) or facts.produced_as in DIAGNOSER_ASSISTED_TYPES


def diagnoser_cold_unassisted(facts: AttemptFacts) -> bool:
    """The diagnoser's "demonstrated" test (``HistoryAttempt.cold_unassisted``): neither assisted nor primed."""

    return not diagnoser_assisted(facts) and not bool(facts.primed)


# -- the teacher's brief and the lesson suggestion (owners: teacher.brief, daily_plan.lesson_suggestion) --------

#: The attempt types a cold check can be: the teacher's ``_COLD_TYPES``; the same members as
#: ``learner.lesson_weight.COLD_ATTEMPT_TYPES``, which the lesson suggestion reads from its owner.
COLD_CHECK_TYPES = frozenset({"independent_attempt", "open_text", "diagnostic_probe", "exam_attempt"})


def unhelped_cold_type(facts: AttemptFacts, cold_types: Collection[str] = COLD_CHECK_TYPES) -> bool:
    """A cold-type answer, unprimed, with no hint (the teacher brief's "cold"). No reveal is read."""

    return facts.produced_as in cold_types and not facts.primed and not facts.hints_used


def graded_cold_check(facts: AttemptFacts, cold_types: Collection[str]) -> bool:
    """The lesson suggestion's cold check: a cold-type answer, unprimed, with no hint, and graded."""

    return (facts.produced_as in cold_types and not facts.primed and not facts.hints_used
            and facts.correctness is not None)


def teacher_attempt_kind(facts: AttemptFacts) -> Any:
    """The teacher brief's word for an attempt in a learner's history: ``cold``, ``assisted`` (an assisted type or
    a hint), ``primed``, else the attempt type itself."""

    return "cold" if unhelped_cold_type(facts) else ("assisted" if facts.produced_as in (
        "hinted_attempt", "guided_walkthrough", "reconstruction_after_walkthrough") or facts.hints_used else (
        "primed" if facts.primed else facts.produced_as))


# -- the router card and the chat packet (owners: daily_plan.router_card, learner_context) -----------------------


def hinted_or_primed(facts: AttemptFacts) -> bool:
    """The router card's per-LO ``assisted`` count: a hint or primed, whatever the attempt type."""

    return int(facts.hints_used or 0) > 0 or bool(facts.primed)


def primed_only(facts: AttemptFacts) -> bool:
    """The ``assisted`` field the router card's recent work and the chat packet's traces show: primed alone (the
    hint count is the field beside it)."""

    return bool(facts.primed)


__all__ = [
    "COLD_CHECK_TYPES", "DIAGNOSER_ASSISTED_TYPES", "cold_item_reveal_rows", "counts_as_assisted",
    "diagnoser_assisted", "diagnoser_cold_unassisted", "fsrs_cap_value", "fsrs_rating_cap", "graded_cold_check",
    "hinted_or_primed", "intervention_assisted", "primed_only", "recorded_counts_as_assisted",
    "teacher_attempt_kind", "unhelped_cold_type", "unassisted_for_coldness",
]
