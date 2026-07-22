"""P4 step 6 (DESCOPED, U-025) -- prequential held-out scoring of shadow predictive
components (spec_p4_controller_and_scale §7.1/§7.3; design §B step 6, §F).

Prequential scoring evaluates a predictive component on the LIVE predictions it made
*before* their outcomes were known -- log-loss / Brier on the realized delayed outcome
at a predeclared horizon (the **next spaced cold review**, never immediate answer
success, §9.3). These **component** reports are the PRIMARY product (§7.3); the
composed-selector comparison is secondary.

The score joins ``controller_shadow_predictions`` (096, ``scorer_kind =
'predictive_component:<name>'``, authority CHECK IN ('none')) to the resolved
``controller_outcome_windows`` (098) sharing a ``decision_id``. The report splits along
two dimensions -- target FAMILY (``card_ref``) and TIME (the calendar-date bucket of the
horizon resolution) -- to catch near-clone / temporal-drift leakage the aggregate hides
(§7.2, audit L3/L11). A surface-group split is NOT reported: the outcome window carries no
surface-group key, so that dimension is deferred rather than faked. The report never
scores on a text/outcome available before its own decision.

This module computes and persists reports only; it grants NO authority. Promotion of a
component (feeding the staged policy's INPUTS, never actions) is gated in
``shadow_components.py`` and emits a U-022 promotion-evidence artifact.
"""

from __future__ import annotations

import json as _json
import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.activities import _canonical_hash

REPORT_SCHEMA_VERSION = "prequential_v1"
# The horizon every prequential outcome resolves at (§9.3). A structural pin, not a knob.
HORIZON_KIND = "next_spaced_cold_review"

_eps = 1e-9


def _clip(p: float) -> float:
    return min(1.0 - _eps, max(_eps, float(p)))


def brier(pairs: Sequence[tuple[float, float]]) -> float | None:
    """Mean squared error of probabilistic predictions vs {0,1} outcomes."""

    if not pairs:
        return None
    return sum((p - y) ** 2 for p, y in pairs) / len(pairs)


def log_loss(pairs: Sequence[tuple[float, float]]) -> float | None:
    """Mean negative log-likelihood of {0,1} outcomes under the predicted probability."""

    if not pairs:
        return None
    total = 0.0
    for p, y in pairs:
        p = _clip(p)
        total += -(y * math.log(p) + (1.0 - y) * math.log(1.0 - p))
    return total / len(pairs)


@dataclass(frozen=True)
class PrequentialReport:
    target_kind: str  # 'predictive_component:<name>' | 'composed_selector'
    component: str | None
    horizon_kind: str
    metrics: dict[str, Any]
    splits: dict[str, Any]
    sample_count: int
    report_hash: str
    id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "target_kind": self.target_kind,
            "component": self.component,
            "horizon_kind": self.horizon_kind,
            "metrics": self.metrics,
            "splits": self.splits,
            "sample_count": self.sample_count,
            "report_hash": self.report_hash,
        }


def _effective_sample(pairs: Sequence[tuple[float, float]]) -> int:
    """Effective sample size = number of resolved, non-censored pairs. At n=1 with a
    deterministic incumbent this is small and is reported honestly, never inflated."""

    return len(pairs)


def _metrics_body(pairs: Sequence[tuple[float, float]]) -> dict[str, Any]:
    return {
        "schema": REPORT_SCHEMA_VERSION,
        "n": len(pairs),
        "effective_sample": _effective_sample(pairs),
        "brier": None if brier(pairs) is None else round(brier(pairs), 6),
        "log_loss": None if log_loss(pairs) is None else round(log_loss(pairs), 6),
        "base_rate": None if not pairs else round(sum(y for _p, y in pairs) / len(pairs), 6),
    }


# ---------------------------------------------------------------------------
# Read: join component predictions to resolved outcomes (bounded bulk reads).
# ---------------------------------------------------------------------------


def _resolved_outcomes_by_decision(repository: Repository) -> dict[str, dict[str, Any]]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT * FROM controller_outcome_windows WHERE status = 'resolved' "
            "AND decision_id IS NOT NULL"
        ).fetchall()
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        out[row["decision_id"]] = dict(row)
    return out


def _component_predictions(repository: Repository, scorer_kind: str) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT * FROM controller_shadow_predictions WHERE scorer_kind = ? "
            "AND decision_id IS NOT NULL ORDER BY created_at, id",
            (scorer_kind,),
        ).fetchall()
    return [dict(r) for r in rows]


def _time_bucket(window: dict[str, Any]) -> str:
    """The calendar-date time bucket a resolved outcome falls in (audit L3/D7). Derived
    from the horizon resolution timestamp, so error is split across time as well as
    family -- catching drift that a family-only split hides."""

    ts = window.get("resolved_at") or window.get("due_at") or window.get("opened_at") or ""
    return str(ts)[:10] or "unbucketed"


def _pairs_for(
    repository: Repository, scorer_kind: str, *, outcome_key: str
) -> tuple[list[tuple[float, float]], dict[str, dict[str, list[tuple[float, float]]]]]:
    """Return (all_pairs, split_groups). ``split_groups`` maps a split DIMENSION
    ('by_family' / 'by_time') to its per-group pairs (audit L3/D7: the report splits along
    BOTH the claimed dimensions, not family alone). ``outcome_key`` names the {0,1} field
    in the resolved window's ``outcome_json`` (e.g. 'cold_success')."""

    outcomes = _resolved_outcomes_by_decision(repository)
    pairs: list[tuple[float, float]] = []
    by_family: dict[str, list[tuple[float, float]]] = {}
    by_time: dict[str, list[tuple[float, float]]] = {}
    for pred in _component_predictions(repository, scorer_kind):
        window = outcomes.get(pred["decision_id"])
        if window is None or not window.get("outcome_json"):
            continue  # unresolved / censored -> excluded, reported as missingness
        outcome = _json.loads(window["outcome_json"])
        if outcome_key not in outcome:
            continue
        predicted = _json.loads(pred["prediction_json"]).get("value")
        if predicted is None:
            continue
        y = 1.0 if outcome[outcome_key] else 0.0
        pair = (float(predicted), y)
        pairs.append(pair)
        by_family.setdefault(str(window.get("card_ref") or "unsplit"), []).append(pair)
        by_time.setdefault(_time_bucket(window), []).append(pair)
    return pairs, {"by_family": by_family, "by_time": by_time}


def _splits_body(
    split_groups: dict[str, dict[str, list[tuple[float, float]]]]
) -> dict[str, dict[str, Any]]:
    """Metrics per group within each split dimension, deterministically ordered."""

    return {
        dimension: {group: _metrics_body(gp) for group, gp in sorted(groups.items())}
        for dimension, groups in sorted(split_groups.items())
    }


def component_report(
    repository: Repository,
    *,
    component: str,
    outcome_key: str = "cold_success",
    persist: bool = True,
    clock: Clock | None = None,
) -> PrequentialReport:
    """The PRIMARY product (§7.3): a prequential calibration/error report for one
    predictive component at the next-spaced-cold-review horizon, split by target family/
    surface group. Never scores on immediate answer success."""

    scorer_kind = f"predictive_component:{component}"
    pairs, split_groups = _pairs_for(repository, scorer_kind, outcome_key=outcome_key)
    metrics = _metrics_body(pairs)
    splits = _splits_body(split_groups)
    body = {"metrics": metrics, "splits": splits}
    report = PrequentialReport(
        target_kind=scorer_kind, component=component, horizon_kind=HORIZON_KIND,
        metrics=metrics, splits=splits, sample_count=len(pairs),
        report_hash=_canonical_hash(body),
    )
    if persist:
        report = _persist_report(repository, report, clock=clock)
    return report


def composed_selector_report(
    repository: Repository,
    *,
    outcome_key: str = "cold_success",
    persist: bool = True,
    clock: Clock | None = None,
) -> PrequentialReport:
    """The SECONDARY product (§7.3): the composed-selector comparison. Reported for
    completeness only; the monolithic action chooser is never promotable (U-025 §7.4)."""

    pairs, split_groups = _pairs_for(repository, "composed_selector", outcome_key=outcome_key)
    metrics = _metrics_body(pairs)
    metrics["note"] = "secondary telemetry; no promotion path for the composed chooser (U-025)"
    splits = _splits_body(split_groups)
    body = {"metrics": metrics, "splits": splits}
    report = PrequentialReport(
        target_kind="composed_selector", component=None, horizon_kind=HORIZON_KIND,
        metrics=metrics, splits=splits, sample_count=len(pairs),
        report_hash=_canonical_hash(body),
    )
    if persist:
        report = _persist_report(repository, report, clock=clock)
    return report


def _persist_report(
    repository: Repository, report: PrequentialReport, *, clock: Clock | None
) -> PrequentialReport:
    report_id = new_ulid()
    with repository.connection() as connection:
        # A report is a rebuildable snapshot keyed by content (report_hash). Re-persisting
        # the same content is idempotent (audit L5/D9): UNIQUE(report_hash) + ON CONFLICT
        # DO NOTHING collapses a replay to the standing row rather than duplicating it.
        connection.execute(
            "INSERT INTO controller_prequential_reports(id, target_kind, component, "
            "horizon_kind, metrics_json, splits_json, sample_count, report_hash, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(report_hash) DO NOTHING",
            (
                report_id, report.target_kind, report.component, report.horizon_kind,
                _json.dumps(report.metrics), _json.dumps(report.splits),
                report.sample_count, report.report_hash, utc_now_iso(clock),
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT id FROM controller_prequential_reports WHERE report_hash = ?",
            (report.report_hash,),
        ).fetchone()
        if row is not None:
            report_id = row["id"]
    return PrequentialReport(
        target_kind=report.target_kind, component=report.component,
        horizon_kind=report.horizon_kind, metrics=report.metrics, splits=report.splits,
        sample_count=report.sample_count, report_hash=report.report_hash, id=report_id,
    )


def reports_for(repository: Repository, *, target_kind: str) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT * FROM controller_prequential_reports WHERE target_kind = ? "
            "ORDER BY created_at, id",
            (target_kind,),
        ).fetchall()
    return [dict(r) for r in rows]
