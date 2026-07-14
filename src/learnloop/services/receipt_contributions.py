"""Shared authoritative certification-credit capping for projections and receipts."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Mapping

from learnloop.services.capability_mapping import (
    cap_certification_by_group,
    group_budget,
)

Cell = tuple[str, str]


@dataclass(frozen=True)
class CellContribution:
    """One (facet, capability) cell's staged→banked credit within one attempt.

    The receipt's per-observation "why this much credit" itemization. ``raw_credit``
    is the staged pre-cap certification credit; ``capped_credit`` is what actually
    banks after the coupled group-budget and attempt-ceiling caps. ``bound_by``
    names which §5.4 cap rule(s) reduced it (empty when ``raw == capped``).
    """

    cell: Cell
    group: str
    raw_credit: float
    capped_credit: float
    group_scale: float
    bound_by: tuple[str, ...]


def itemize_observation_contributions(
    staged_by_group: Mapping[str, Mapping[Cell, float]],
    *,
    attempt_type: str,
    evidence_mass: float,
    group_budget_overrides: Mapping[str, float] | None,
    max_groups_per_attempt: int,
) -> tuple[dict[Cell, float], list[CellContribution]]:
    """Cap the staged credit AND itemize each cell's raw/capped/binding rule.

    The returned capped dict is byte-identical to
    :func:`cap_observation_contributions` (same per-cell expression and order),
    and the itemization's ``capped_credit`` values sum, per cell, to that dict —
    so the receipt itemization is exact against the banked ledger by construction.
    """

    totals = {
        group: sum(max(float(value), 0.0) for value in cells.values())
        for group, cells in staged_by_group.items()
    }
    capped = cap_certification_by_group(
        totals,
        attempt_type=attempt_type,
        evidence_mass=evidence_mass,
        overrides=group_budget_overrides,
        max_groups_per_attempt=max_groups_per_attempt,
    )
    # Reproduce the intermediate group-only cap (pre-ceiling) to attribute which
    # rule bound a cell: the group budget, the attempt ceiling, or both.
    group_only: dict[str, float] = {}
    budgets: dict[str, float] = {}
    for group, raw_total in totals.items():
        budget = group_budget(
            attempt_type, group, evidence_mass=evidence_mass, overrides=group_budget_overrides
        )
        budgets[group] = budget
        group_only[group] = min(raw_total, budget)
    ceiling = evidence_mass * max_groups_per_attempt
    group_only_total = sum(group_only.values())
    ceiling_active = group_only_total > ceiling and group_only_total > 0

    result: dict[Cell, float] = defaultdict(float)
    items: list[CellContribution] = []
    for group, cells in staged_by_group.items():
        raw_total = totals.get(group, 0.0)
        if raw_total <= 0.0:
            continue
        scale = capped.get(group, 0.0) / raw_total
        group_bound = raw_total > budgets.get(group, raw_total)
        bound_by: tuple[str, ...] = tuple(
            reason
            for reason, active in (
                ("group_budget", group_bound),
                ("attempt_ceiling", ceiling_active),
            )
            if active
        )
        for cell, value in cells.items():
            raw = max(float(value), 0.0)
            capped_credit = raw * scale
            result[cell] += capped_credit
            items.append(
                CellContribution(
                    cell=cell,
                    group=group,
                    raw_credit=raw,
                    capped_credit=capped_credit,
                    group_scale=scale,
                    bound_by=bound_by if raw > capped_credit else (),
                )
            )
    return dict(result), items


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

    result, _ = itemize_observation_contributions(
        staged_by_group,
        attempt_type=attempt_type,
        evidence_mass=evidence_mass,
        group_budget_overrides=group_budget_overrides,
        max_groups_per_attempt=max_groups_per_attempt,
    )
    return result
