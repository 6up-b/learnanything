"""``lane_quota_v1``: DL1's deterministic block chooser (``spec_daily_loop_v1.md`` §6.8).

It picks the feasible candidate from the lane with the largest unspent share
of its split; ties go in the order repair, maintain, new, push, then to the
higher planner value (then the source's order). With nothing feasible it
stops for today. Its "why" is computed from the source's reason.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from learnloop.daily_plan.types import (
    LANES,
    STOP_FOR_TODAY,
    STOP_OFFER_MINUTES,
    BlockCandidate,
    BlockChoice,
    PlanState,
)

CHOOSER_NAME = "lane_quota_v1"


def unspent_share(lane: str, state: PlanState) -> float:
    total = float(state.lane_minutes_allotted.get(lane, 0.0))
    left = float(state.lane_minutes_left.get(lane, 0.0))
    if total <= 1e-9:
        return 1.0 if left > 1e-9 else 0.0
    return left / total


@dataclass(frozen=True)
class LaneQuotaChooser:
    name: str = CHOOSER_NAME

    def choose(self, state: PlanState, feasible: Sequence[BlockCandidate]) -> BlockChoice:
        if not feasible:
            why = (
                "today's minutes are used"
                if state.minutes_left < STOP_OFFER_MINUTES
                else "nothing more worth doing today fits"
            )
            return BlockChoice(
                candidate_id=STOP_FOR_TODAY,
                chosen_by="lane_quota",
                propensity=1.0,
                why=why,
                why_kind="computed",
            )
        order = {candidate.candidate_id: index for index, candidate in enumerate(feasible)}
        best = min(
            feasible,
            key=lambda candidate: (
                -round(unspent_share(candidate.lane, state), 9),
                LANES.index(candidate.lane),
                -candidate.planner_value,
                order[candidate.candidate_id],
            ),
        )
        return BlockChoice(
            candidate_id=best.candidate_id,
            chosen_by="lane_quota",
            propensity=1.0,
            why=best.reason,
            why_kind="computed",
        )


__all__ = ["CHOOSER_NAME", "LaneQuotaChooser", "unspent_share"]
