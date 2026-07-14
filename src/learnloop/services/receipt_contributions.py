"""Shared authoritative certification-credit capping for projections and receipts."""

from __future__ import annotations

from collections import defaultdict
from typing import Mapping

from learnloop.services.capability_mapping import cap_certification_by_group

Cell = tuple[str, str]


def cap_observation_contributions(
    staged_by_group: Mapping[str, Mapping[Cell, float]],
    *,
    attempt_type: str,
    evidence_mass: float,
    group_budget_overrides: Mapping[str, float] | None,
    max_groups_per_attempt: int,
) -> dict[Cell, float]:
    """Apply group budgets and the attempt ceiling, preserving cell shares.

    Callers stage already-localized, relationship/assistance-filtered credit.
    This is the one implementation of the coupled caps used by both the banked
    canonical ledger and the learner-facing evidence timeline.
    """

    totals = {group: sum(max(float(value), 0.0) for value in cells.values()) for group, cells in staged_by_group.items()}
    capped = cap_certification_by_group(
        totals,
        attempt_type=attempt_type,
        evidence_mass=evidence_mass,
        overrides=group_budget_overrides,
        max_groups_per_attempt=max_groups_per_attempt,
    )
    result: dict[Cell, float] = defaultdict(float)
    for group, cells in staged_by_group.items():
        raw_total = totals.get(group, 0.0)
        if raw_total <= 0.0:
            continue
        scale = capped.get(group, 0.0) / raw_total
        for cell, value in cells.items():
            result[cell] += max(float(value), 0.0) * scale
    return dict(result)
