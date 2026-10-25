"""Claim feedback on the review that resolves it (LP-min (a); LPQ9).

spec_learned_parameters_v1 §3.0b item 7 and LPQ9 (decided 2026-10-24, the
recommended default): when a review resolves a scope the learner marked as
known ("I know this", or "too easy" on an item: a ``self_report``
assumption), that review's feedback says so in one quiet line: "You marked
this as known; this check: missed". Accuracy feedback on a claim is what
raised self-assessment validity (D1). Nothing else is shown: no score, no
calibration figure, no trait label (ITS sweep P4).

Display only, read after grading from the placement ledger: the line is
never an input to grading, to mastery or to the resolution itself, and the
grader never sees the claim. It appears on the one attempt the placement
state names as the assumption's resolving attempt, so it never repeats on a
later or unrelated review; a miss whose diagnosis has not landed has no
resolving attempt yet, so its line appears once the diagnosis decides it (on
the next open of that review's feedback).

Ships with the claim-fixes successor and under its kill switch
(``learnloop.learner.mastery.claim_fixes_live``); placement off, nothing.
"""

from __future__ import annotations

from typing import Any

from learnloop.db.repositories import Repository
from learnloop.learner.mastery import claim_fixes_live
from learnloop.placement.state import load_placement_state, placement_active
from learnloop.vault.models import LoadedVault

#: The assumption source a learner's own "I know this" / "too easy" writes.
_LEARNER_CLAIM_SOURCE = "self_report"

#: The resolved statuses, worded as the review reads them.
_CHECK_WORDS = {"passed": "passed", "failed": "missed"}


def claim_check(vault: LoadedVault, repository: Repository, attempt_id: str) -> dict[str, Any] | None:
    """The claim line for the review ``attempt_id``, or None when it resolves no claim."""

    if not claim_fixes_live(vault) or not placement_active(vault):
        return None
    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        return None
    state = load_placement_state(vault, repository, now_iso=str(attempt.get("created_at") or "") or None)
    for assumption in state.assumptions:
        if (
            assumption.source == _LEARNER_CLAIM_SOURCE
            and assumption.resolving_attempt_id == attempt_id
            and assumption.status in _CHECK_WORDS
        ):
            check = _CHECK_WORDS[assumption.status]
            return {
                "claim": "marked_known",
                "check": check,
                "line": f"You marked this as known; this check: {check}.",
            }
    return None


__all__ = ["claim_check"]
