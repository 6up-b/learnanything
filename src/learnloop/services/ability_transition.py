from __future__ import annotations

from learnloop.services.recall_coverage import clamp
from learnloop.vault.models import PracticeItem


def estimate_ability_transition(
    item: PracticeItem,
    *,
    correctness: float,
    attempt_type: str,
    target_facets: list[str],
    error_event_written: bool,
) -> dict[str, object]:
    """Audit the modeled learning gain from doing/reviewing an item.

    This is intentionally not belief evidence. The attempt pipeline records it
    for scheduler/reward inspection while leaving mastery and facet beta counts
    to the observed answer only.
    """

    if item.practice_mode == "diagnostic_probe":
        expected_gain = 0.0
        reason = "diagnostic_probe_no_learning_transition"
    elif attempt_type in {"dont_know", "hinted_attempt"} or error_event_written:
        expected_gain = 0.04 + 0.04 * (1.0 - clamp(correctness))
        reason = "feedback_after_gap"
    else:
        expected_gain = 0.02 * clamp(correctness)
        reason = "successful_practice_reinforcement"
    return {
        "transition_type": "expected_skill_gain",
        "expected_skill_gain": clamp(expected_gain, 0.0, 0.08),
        "target_facets": sorted(set(target_facets)),
        "reason": reason,
        "applied_to_belief_counts": False,
        "applied_to_mastery": False,
        "applied_to_facet_recall": False,
    }
