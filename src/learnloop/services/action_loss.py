"""P4 step 3 -- the minutes-denominated decision-loss table L(h, a) (U-023, spec §6.2).

The constrained decision-cost hierarchy (U-023): correctness/safety/learner-intent
constraints define FEASIBILITY first (the constraint engine, §5). Among feasible
interventions, the loss of taking action ``a`` when hypothesis ``h`` is true is the
**expected wasted learner-minutes** -- the minutes spent on an ineffective intervention
plus the delay until the effective one. ``lambda_time`` is fixed at 1: minutes are the
cost numeraire, so burden is measured in minutes, never re-weighted.

Entries are **DERIVED, not elicited** (spec §6.2, design §B step 3). The source is:

- the deterministic triage-route structure (``failure_triage_routes``: each reason's
  ``first_intervention`` -- the effective repair when that reason is the true cause);
- activity duration estimates from **logged attempt durations** (P0
  ``interaction_events.attempt_duration_ms``), aggregated by
  :func:`attempt_minutes_by_intervention`.

For a hypothesis (triage reason) ``h`` with effective intervention ``e = route(h)``::

    L(h, a) = 0                              if a == e   (no wasted minutes)
    L(h, a) = minutes(a) + minutes(e)        otherwise   (wasted a + delayed e)

Every cell carries its expected-minutes derivation so the table is inspectable and so
the registration lint (:func:`assert_derived`) can reject a free-constant entry that
lacks a derivation -- "a free-constant entry without a derivation fails registration"
(spec §16.3, U-023). Non-time harms (e.g. a misgrade-risk ceiling) NEVER enter here as
weights; they enter the decision only as constraint thresholds (the constraint engine),
a dominance filter, or a documented tie-break order (:func:`argmin_action`).
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.db.repositories import Repository
from learnloop.services.activities import _canonical_hash

# Structural schema version of the loss-table body (enum, not a decision knob).
LOSS_TABLE_VERSION = 1

# Conservative per-intervention minutes used only when NO logged attempt duration is
# available to derive an estimate from. Heuristic decision parameter (design §E): it is
# the fail-closed fallback so an un-instrumented vault still gets an inspectable table.
DEFAULT_INTERVENTION_MINUTES = 3.0


class LossDerivationError(ValueError):
    """A loss cell was constructed without a minutes derivation (registration lint)."""


@dataclass(frozen=True)
class DurationEstimate:
    """One intervention's minutes estimate + its provenance (inspectable)."""

    intervention: str
    minutes: float
    source: str  # 'logged_attempt_durations' | 'pooled_attempt_durations' | 'heuristic_default'
    sample_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "intervention": self.intervention,
            "minutes": round(float(self.minutes), 6),
            "source": self.source,
            "sample_count": self.sample_count,
        }


@dataclass(frozen=True)
class LossCell:
    """One L(h, a) entry with its expected-minutes derivation attached (§6.2)."""

    hypothesis: str
    action: str
    minutes: float
    derivation: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "hypothesis": self.hypothesis,
            "action": self.action,
            "minutes": round(float(self.minutes), 6),
            "derivation": self.derivation,
        }


@dataclass(frozen=True)
class LossTable:
    """A frozen, content-hashed, minutes-denominated loss table (§6.2)."""

    hypotheses: tuple[str, ...]
    actions: tuple[str, ...]
    cells: Mapping[tuple[str, str], LossCell]
    effective_action: Mapping[str, str]
    version: int = LOSS_TABLE_VERSION
    calibration_label: str = "heuristic"
    scope: str = "global"
    table_hash: str = ""
    # A documented tie-break order over actions (§6.2): NOT a weight -- it only orders
    # actions whose expected loss is already tied, so no non-time harm becomes a weight.
    tie_break_order: tuple[str, ...] = ()

    def loss(self, hypothesis: str, action: str) -> float:
        cell = self.cells.get((hypothesis, action))
        return cell.minutes if cell is not None else 0.0

    def expected_loss(self, action: str, posterior: Mapping[str, float]) -> float:
        return sum(
            max(float(posterior.get(h, 0.0)), 0.0) * self.loss(h, action)
            for h in self.hypotheses
        )

    def argmin_action(self, posterior: Mapping[str, float]) -> str:
        """The minimum-expected-loss action under ``posterior`` (§6.3 ``current_loss``
        argmin). Ties break by the documented ``tie_break_order`` then lexically --
        never by an invented weight (U-023)."""

        order = {a: i for i, a in enumerate(self.tie_break_order)}
        best = min(
            self.actions,
            key=lambda a: (
                round(self.expected_loss(a, posterior), 9),
                order.get(a, len(order)),
                a,
            ),
        )
        return best

    def argmin_action_set(self, posterior: Mapping[str, float], *, tol: float = 1e-9) -> frozenset[str]:
        """All actions whose expected loss is within ``tol`` of the minimum -- the
        decision-space "same optimal action" set (§6.2), never closeness of values."""

        losses = {a: self.expected_loss(a, posterior) for a in self.actions}
        floor = min(losses.values()) if losses else 0.0
        return frozenset(a for a, v in losses.items() if v - floor <= tol)

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "calibration_label": self.calibration_label,
            "scope": self.scope,
            "hypotheses": list(self.hypotheses),
            "actions": list(self.actions),
            "effective_action": dict(sorted(self.effective_action.items())),
            "tie_break_order": list(self.tie_break_order),
            "cells": [self.cells[key].as_dict() for key in sorted(self.cells.keys())],
            "table_hash": self.table_hash,
        }


# ---------------------------------------------------------------------------
# Duration derivation from logged attempts (§6.2: durations from logged attempts).
# ---------------------------------------------------------------------------


def _pooled_attempt_minutes(repository: Repository) -> tuple[float | None, int]:
    """Median logged attempt duration in minutes + the sample count. There is no
    per-intervention tag on ``interaction_events`` yet, so the pooled median is the
    honest cross-intervention estimate; a caller with finer data passes ``overrides``."""

    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT attempt_duration_ms FROM interaction_events "
            "WHERE kind = 'attempt_duration' AND attempt_duration_ms IS NOT NULL"
        ).fetchall()
    values = [int(r["attempt_duration_ms"]) for r in rows if r["attempt_duration_ms"] is not None]
    if not values:
        return None, 0
    return statistics.median(values) / 60000.0, len(values)


def attempt_minutes_by_intervention(
    interventions: Sequence[str],
    *,
    repository: Repository | None = None,
    overrides: Mapping[str, float] | None = None,
) -> dict[str, DurationEstimate]:
    """Per-intervention minutes estimate with provenance. Precedence: an explicit
    ``overrides`` value (finer logged data the caller aggregated) > the pooled logged
    attempt median > :data:`DEFAULT_INTERVENTION_MINUTES` (fail-closed heuristic)."""

    pooled, pooled_n = (None, 0)
    if repository is not None:
        pooled, pooled_n = _pooled_attempt_minutes(repository)
    out: dict[str, DurationEstimate] = {}
    for iv in interventions:
        if overrides is not None and iv in overrides:
            out[iv] = DurationEstimate(iv, float(overrides[iv]), "logged_attempt_durations", 1)
        elif pooled is not None:
            out[iv] = DurationEstimate(iv, float(pooled), "pooled_attempt_durations", pooled_n)
        else:
            out[iv] = DurationEstimate(iv, DEFAULT_INTERVENTION_MINUTES, "heuristic_default", 0)
    return out


# ---------------------------------------------------------------------------
# Table construction from routes + durations.
# ---------------------------------------------------------------------------


def _routes_by_reason(routes: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    by_reason: dict[str, Mapping[str, Any]] = {}
    for route in routes:
        reason = route.get("reason")
        if reason is not None and reason not in by_reason:
            by_reason[reason] = route
    return by_reason


def build_loss_table(
    *,
    routes: Sequence[Mapping[str, Any]],
    hypotheses: Sequence[str] | None = None,
    repository: Repository | None = None,
    duration_overrides: Mapping[str, float] | None = None,
    calibration_label: str = "heuristic",
    scope: str = "global",
) -> LossTable:
    """Derive L(h, a) from triage-route structure + logged attempt durations (§6.2).

    ``routes`` are ``failure_triage_routes`` rows (``reason``, ``first_intervention``,
    ...). ``hypotheses`` restricts the reason set (default: every reason with a route).
    The action space is the distinct ``first_intervention`` values across the reasons.
    Every cell carries a minutes derivation; :func:`assert_derived` then guards it."""

    by_reason = _routes_by_reason(routes)
    reasons = tuple(hypotheses) if hypotheses is not None else tuple(sorted(by_reason.keys()))
    reasons = tuple(r for r in reasons if r in by_reason)

    effective = {r: str(by_reason[r]["first_intervention"]) for r in reasons}
    actions = tuple(sorted(set(effective.values())))
    estimates = attempt_minutes_by_intervention(
        actions, repository=repository, overrides=duration_overrides
    )

    cells: dict[tuple[str, str], LossCell] = {}
    for h in reasons:
        e = effective[h]
        for a in actions:
            if a == e:
                cells[(h, a)] = LossCell(
                    h, a, 0.0,
                    {
                        "kind": "effective_intervention",
                        "wasted_minutes": 0.0,
                        "delay_minutes": 0.0,
                        "effective_intervention": e,
                        "note": "the effective repair for this hypothesis wastes no minutes",
                    },
                )
            else:
                wasted = estimates[a].minutes
                delay = estimates[e].minutes
                cells[(h, a)] = LossCell(
                    h, a, wasted + delay,
                    {
                        "kind": "ineffective_then_effective",
                        "wasted_intervention": a,
                        "wasted_minutes": round(wasted, 6),
                        "effective_intervention": e,
                        "delay_minutes": round(delay, 6),
                        "wasted_source": estimates[a].as_dict(),
                        "delay_source": estimates[e].as_dict(),
                    },
                )

    body = {
        "version": LOSS_TABLE_VERSION,
        "hypotheses": list(reasons),
        "actions": list(actions),
        "effective_action": dict(sorted(effective.items())),
        "cells": [cells[k].as_dict() for k in sorted(cells.keys())],
    }
    table = LossTable(
        hypotheses=reasons,
        actions=actions,
        cells=cells,
        effective_action=effective,
        version=LOSS_TABLE_VERSION,
        calibration_label=calibration_label,
        scope=scope,
        table_hash=_canonical_hash(body),
        tie_break_order=actions,  # documented, stable order; ties break here, not by weight
    )
    assert_derived(table)
    return table


def assert_derived(table: LossTable) -> None:
    """Registration lint (U-023, spec §16.3): every loss cell must carry a minutes
    derivation. A free-constant entry (missing/empty derivation, or a non-zero minutes
    value with no wasted/delay accounting) fails registration."""

    for key, cell in table.cells.items():
        d = cell.derivation
        if not d or "kind" not in d:
            raise LossDerivationError(f"loss cell {key} has no minutes derivation")
        if cell.minutes > 0.0:
            if "wasted_minutes" not in d or "delay_minutes" not in d:
                raise LossDerivationError(
                    f"loss cell {key} is a free constant (no wasted/delay minutes derivation)"
                )
            derived_total = float(d.get("wasted_minutes", 0.0)) + float(d.get("delay_minutes", 0.0))
            if abs(derived_total - cell.minutes) > 1e-6:
                raise LossDerivationError(
                    f"loss cell {key} minutes {cell.minutes} != derived {derived_total}"
                )


def raw_cell(hypothesis: str, action: str, minutes: float) -> LossCell:
    """Construct an UNDERIVED loss cell (a free constant). Used only to prove the
    registration lint rejects it -- production tables always route through
    :func:`build_loss_table`, which attaches a derivation."""

    return LossCell(hypothesis, action, float(minutes), {})
