"""Compare two ``learnloop evsi simulate`` reports: every cell, every headline claim.

Stage ``evsi-single-family-unbounded`` (owner-approved 2026-10-13). The
single-family study ran with a 25-check count bound until its v3 report; the
multi-family review (F4) found such a bound binding. The study was rerun
without it, with the same seeds and the stored fit, so every difference between
the two reports is the bound's. This module lines the two reports up:

* **cells**: every metric of every cell (the main comparison, the regimes, the
  sensitivity rows, Part C), old against new, and whether a point estimate left
  the other report's 95% CI;
* **bound**: the stored run's bound stops per arm and cell. An unbounded run's
  ``count_bound`` cells say exactly which episodes a 25-check bound stopped
  (common random numbers: an episode runs identically up to the bound); they
  are cross-checked against the stop reasons the stored report kept;
* **attribution**: every arm in every cell the bound left untouched must be
  identical in the two reports, so whatever moved, moved because of the bound;
* **claims**: each headline claim of ``docs/reviews/evsi-calibration.md``, its
  quantities and its conclusion under each report;
* **ranks**: each cell's ranking of the arms by mean minutes per episode.

Ordering is the study's, never a stored dict's: a report read back from JSON has
sorted keys, and iterating it would reorder the arms. Read-only, no simulation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from learnloop.evsi_calibration import policies as P
from learnloop.evsi_calibration.experiments import REFERENCE_BOUND, SWEEPS

COMPARE_VERSION = "evsi_simulate_compare_v1"
SECTIONS = ("main", "regimes", "sensitivity", "part_c")
SYSTEM_MODELS = ("hand_set", "eedi_fitted")
PART_C_LOSSES = ("minutes_only", "measured_unresolved")
#: Stored numbers are rounded to 4 places; closer than this they are the same number.
SAME = 1e-9
#: How many stop reasons each section of a report keeps (``None``: all of them).
RECORDED_STOP_REASONS = {"main": None, "regimes": 4, "sensitivity": 3, "part_c": 0}

STATUS_ORDER = ("identical", "moved_within_ci", "moved_no_ci", "moved_beyond_ci", "missing")


# -- small readers ----------------------------------------------------------------------------------------------


def _get(mapping: Any, *path: Any) -> Any:
    for key in path:
        if not isinstance(mapping, Mapping) or key not in mapping:
            return None
        mapping = mapping[key]
    return mapping


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(number) else number


def _interval(value: Any) -> list[float] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    low, high = _number(value[0]), _number(value[1])
    return None if low is None or high is None else [low, high]


def _policy_key(policy: str) -> tuple[int, str]:
    order = P.ALL_POLICIES
    return (order.index(policy), "") if policy in order else (len(order), policy)


def _policies(*mappings: Any) -> list[str]:
    names: set[str] = set()
    for mapping in mappings:
        if isinstance(mapping, Mapping):
            names |= set(mapping)
    return sorted(names, key=_policy_key)


def strength_label(value: Any) -> str:
    """``fitted`` (Eedi's own consistency) or the overriding consistency."""

    return "fitted" if value in (None, "fitted") else f"{float(value):g}"


def _strength_key(label: str) -> tuple[int, float]:
    return (0, 0.0) if label == "fitted" else (1, float(label))


def _sweep_key(name: str) -> tuple[int, str]:
    order = list(SWEEPS)
    return (order.index(name), "") if name in order else (len(order), name)


def applied_bound(report: Mapping[str, Any]) -> int | None:
    """The count bound a report's episodes ran under. Reports before v3 do not
    record it in their settings; they ran under ``PolicySettings``' default,
    which their ``policy_defaults`` record (25)."""

    settings = report.get("settings") or {}
    if "safety_bound" in settings:
        return settings["safety_bound"]
    return (report.get("policy_defaults") or {}).get("safety_bound")


# -- quantities -------------------------------------------------------------------------------------------------


def quantity(label: str, old: Any, new: Any, old_ci: Any = None, new_ci: Any = None) -> dict[str, Any]:
    """One number in both reports, and how it moved.

    ``moved_beyond_ci``: a point estimate left the other report's 95% CI (either
    way); ``moved_within_ci``: it moved, inside both CIs; ``moved_no_ci``: it
    moved and has no CI (a mean of checks, a difference of two means)."""

    a, b = _number(old), _number(new)
    a_ci, b_ci = _interval(old_ci), _interval(new_ci)
    out: dict[str, Any] = {"label": label, "old": a, "old_ci95": a_ci, "new": b, "new_ci95": b_ci}
    if a is None or b is None:
        out.update(delta=None, status="missing")
        return out

    def outside(x: float, ci: list[float] | None) -> bool:
        return ci is not None and (x < ci[0] - SAME or x > ci[1] + SAME)

    same_ci = (a_ci is None and b_ci is None) or (
        a_ci is not None and b_ci is not None and all(abs(x - y) <= SAME for x, y in zip(a_ci, b_ci)))
    if abs(b - a) <= SAME and same_ci:
        status = "identical"
    elif outside(b, a_ci) or outside(a, b_ci):
        status = "moved_beyond_ci"
    elif a_ci is None and b_ci is None:
        status = "moved_no_ci"
    else:
        status = "moved_within_ci"
    out.update(delta=round(b - a, 6), status=status)
    return out


def _worst(statuses: Sequence[str]) -> str:
    if not statuses:
        return "missing"
    known = [s for s in statuses if s != "missing"]
    if not known:
        return "missing"
    return max(known, key=STATUS_ORDER.index)


# -- cells ------------------------------------------------------------------------------------------------------

#: (metric, value path, CI path) inside a main-comparison policy block.
MAIN_METRICS: tuple[tuple[str, tuple[str, ...], tuple[str, ...] | None], ...] = (
    ("mean_total_minutes", ("episodes", "mean_total_minutes"), ("episodes", "total_minutes_ci95")),
    ("mean_checks", ("episodes", "mean_checks"), None),
    ("correct_action_rate", ("episodes", "correct_action_rate"), ("episodes", "correct_action_ci95")),
    ("misconception_identified_rate", ("episodes", "misconception_identified_rate"), None),
    ("mean_wasted_minutes", ("episodes", "mean_wasted_minutes"), None),
    ("log_loss", ("outcome_calibration", "log_loss"), None),
    ("ece", ("outcome_calibration", "ece"), None),
    ("mean_predicted_eig", ("information", "mean_predicted_eig"), None),
    ("mean_entropy_drop", ("information", "mean_entropy_drop"), ("information", "entropy_drop_ci95")),
    ("mean_truth_log_gain", ("information", "mean_truth_log_gain"), ("information", "truth_log_gain_ci95")),
    ("p_action_change_predicted", ("action_change", "mean_predicted"), None),
    ("p_action_change_realized", ("action_change", "realized_rate"), None),
    ("evsi_predicted_per_check", ("value_of_checks", "mean_predicted_evsi_point"), None),
    ("evsi_realized_per_check", ("value_of_checks", "mean_realized_value"), ("value_of_checks", "realized_value_ci95")),
    ("minutes_per_nat", ("value_of_checks", "minutes_per_nat"), ("value_of_checks", "minutes_per_nat_ci95")),
)
REGIME_METRICS = (
    ("mean_total_minutes", ("mean_total_minutes",), ("total_minutes_ci95",)),
    ("mean_checks", ("mean_checks",), None),
    ("correct_action_rate", ("correct_action_rate",), None),
    ("mean_wasted_minutes", ("mean_wasted_minutes",), None),
)
REGIME_VALUE_METRICS = (
    ("evsi_predicted_per_check", ("mean_predicted_evsi_point",), None),
    ("evsi_realized_per_check", ("mean_realized_value",), None),
    ("minutes_per_nat", ("minutes_per_nat",), ("minutes_per_nat_ci95",)),
)
SENSITIVITY_METRICS = (
    ("mean_total_minutes", ("mean_total_minutes",), ("total_minutes_ci95",)),
    ("mean_checks", ("mean_checks",), None),
    ("correct_action_rate", ("correct_action_rate",), None),
    ("difference_vs_current", ("difference_vs_current", "mean_difference"), ("difference_vs_current", "ci95")),
    ("ranking_tau_vs_current", ("ranking_tau_vs_current",), None),
)
PART_C_METRICS = (
    ("difference", ("difference", "mean_difference"), ("difference", "ci95")),
    ("minutes_only_total", ("minutes_only_total",), None),
    ("measured_total", ("measured_total",), None),
    ("minutes_only_checks", ("minutes_only_checks",), None),
    ("measured_checks", ("measured_checks",), None),
)

CellKey = tuple[Any, ...]


@dataclass(frozen=True)
class _Cell:
    key: CellKey
    order: tuple[Any, ...]
    describe: dict[str, Any]
    #: policy -> metric -> (value, ci)
    policies: dict[str, dict[str, tuple[Any, Any]]]


def _read(block: Any, specs: Sequence[tuple[str, tuple[str, ...], tuple[str, ...] | None]]) -> dict[str, tuple[Any, Any]]:
    return {name: (_get(block, *path), _get(block, *ci) if ci else None) for name, path, ci in specs}


def _cells(report: Mapping[str, Any]) -> dict[CellKey, _Cell]:
    cells: dict[CellKey, _Cell] = {}
    main = report.get("main") or {}
    models = list(SYSTEM_MODELS) + sorted(m for m in main if m not in SYSTEM_MODELS)
    for index, model in enumerate(models):
        if model not in main:
            continue
        key = ("main", model)
        cells[key] = _Cell(key, (0, index), {"section": "main", "system_model": model},
                           {p: _read(b, MAIN_METRICS) for p, b in (main[model] or {}).items()})
    for row in report.get("regimes") or []:
        strength = strength_label(row.get("consistency"))
        repair = _number(row.get("repair_minutes"))
        key = ("regimes", strength, repair)
        policies: dict[str, dict[str, tuple[Any, Any]]] = {}
        for policy in _policies(row.get("policies"), row.get("value_of_checks")):
            values = _read(_get(row, "policies", policy), REGIME_METRICS)
            values.update(_read(_get(row, "value_of_checks", policy), REGIME_VALUE_METRICS))
            policies[policy] = values
        cells[key] = _Cell(key, (1, _strength_key(strength), repair),
                           {"section": "regimes", "consistency": strength, "repair_minutes": repair}, policies)
    for name, parameter in (_get(report, "sensitivity", "parameters") or {}).items():
        current = _number(parameter.get("current"))
        for row in parameter.get("rows") or []:
            value = _number(row.get("value"))
            key = ("sensitivity", name, value)
            cells[key] = _Cell(
                key, (2, _sweep_key(name), value),
                {"section": "sensitivity", "parameter": name, "value": value, "current": current},
                {p: _read(b, SENSITIVITY_METRICS) for p, b in (row.get("policies") or {}).items()},
            )
    for row in _get(report, "part_c", "rows") or []:
        strength = strength_label(row.get("consistency"))
        encounters = _number(row.get("encounters"))
        key = ("part_c", strength, encounters)
        if key not in cells:
            cells[key] = _Cell(key, (3, _strength_key(strength), encounters),
                               {"section": "part_c", "consistency": strength, "encounters": encounters,
                                "true_unresolved_minutes": _number(row.get("true_unresolved_minutes"))}, {})
        cells[key].policies[str(row.get("policy"))] = _read(row, PART_C_METRICS)
    return cells


def _cell_label(describe: Mapping[str, Any]) -> str:
    section = describe["section"]
    if section == "main":
        return f"main {describe['system_model']}"
    if section == "regimes":
        return f"{describe['consistency']}/{describe['repair_minutes']:g}"
    if section == "sensitivity":
        return f"{describe['parameter']} = {describe['value']:g}"
    return f"part C {describe['consistency']} x{describe['encounters']:g}"


# -- bound stops ------------------------------------------------------------------------------------------------


def _bound_key(cell: Mapping[str, Any]) -> CellKey:
    section = cell.get("section")
    if section == "main":
        return ("main", cell.get("system_model"))
    if section == "regimes":
        return ("regimes", strength_label(cell.get("consistency")), _number(cell.get("repair_minutes")))
    if section == "sensitivity":
        return ("sensitivity", cell.get("parameter"), _number(cell.get("value")))
    return ("part_c", strength_label(cell.get("consistency")), _number(cell.get("encounters")))


def _recorded_stop_reasons(report: Mapping[str, Any], key: CellKey, policy: str) -> Mapping[str, int] | None:
    section = key[0]
    if section == "main":
        return _get(report, "main", key[1], policy, "episodes", "stop_reasons")
    if section == "regimes":
        for row in report.get("regimes") or []:
            if (strength_label(row.get("consistency")), _number(row.get("repair_minutes"))) == key[1:]:
                return _get(row, "policies", policy, "stop_reasons")
        return None
    if section == "sensitivity":
        for row in _get(report, "sensitivity", "parameters", key[1], "rows") or []:
            if _number(row.get("value")) == key[2]:
                return _get(row, "policies", policy, "stop_reasons")
    return None


def recorded_bound_stops(report: Mapping[str, Any], key: CellKey, policy: str,
                         episodes: int | None) -> tuple[int | None, str]:
    """What a stored report itself says its bound stopped in a cell: the
    ``safety_bound`` stop reason when the report kept it, 0 when it kept every
    stop reason and that one is absent, else unknown (``truncated``: only the
    most frequent reasons were kept; ``not_recorded``: none were)."""

    reasons = _recorded_stop_reasons(report, key, policy)
    if not isinstance(reasons, Mapping):
        return None, "not_recorded"
    if "safety_bound" in reasons:
        return int(reasons["safety_bound"]), "recorded"
    limit = RECORDED_STOP_REASONS.get(key[0])
    complete = limit is None or len(reasons) < limit or (
        episodes is not None and sum(int(v) for v in reasons.values()) == episodes)
    return (0, "recorded") if complete else (None, "truncated")


def bound_stops(old: Mapping[str, Any], new: Mapping[str, Any]) -> dict[str, Any]:
    """Per cell and arm, the episodes the old report's bound stopped, read from
    the unbounded report's ``count_bound`` cells, and what the old report
    itself recorded."""

    old_bound, new_bound = applied_bound(old), applied_bound(new)
    source = new if new_bound is None else (old if old_bound is None else None)
    bounded = old if source is new else new
    block = (source or {}).get("count_bound") or {}
    reference = block.get("reference_bound", REFERENCE_BOUND)
    rows = []
    for cell in block.get("cells") or []:
        key = _bound_key(cell)
        policy = str(cell.get("policy"))
        recorded, how = (None, "not_recorded")
        if cell.get("section") != "part_c":
            recorded, how = recorded_bound_stops(bounded, key, policy, cell.get("episodes"))
        stops = int(cell.get("reference_bound_stops") or 0)
        rows.append({
            "key": list(key),
            "section": cell.get("section"),
            "cell": {k: cell[k] for k in ("system_model", "consistency", "repair_minutes", "parameter", "value",
                                          "encounters", "loss") if k in cell},
            "policy": policy,
            "episodes": cell.get("episodes"),
            "stops": stops,
            "censored": int(cell.get("reference_bound_censored") or 0),
            "max_checks_unbounded": cell.get("max_checks"),
            "ran_out_of_questions": cell.get("ran_out_of_questions"),
            "recorded_in_bounded_report": recorded,
            "record": how,
            "check": ("agrees" if recorded == stops else "disagrees") if recorded is not None else "unverifiable",
        })
    order = {"main": 0, "regimes": 1, "sensitivity": 2, "part_c": 3}

    def sort_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
        key = row["key"]
        if key[0] == "main":
            inner: tuple[Any, ...] = (SYSTEM_MODELS.index(key[1]) if key[1] in SYSTEM_MODELS else 9, str(key[1]))
        elif key[0] == "sensitivity":
            inner = (_sweep_key(key[1]), key[2])
        else:
            inner = (_strength_key(key[1]), key[2])
        loss = row["cell"].get("loss")
        return (order.get(key[0], 9), inner, PART_C_LOSSES.index(loss) if loss in PART_C_LOSSES else 0,
                _policy_key(row["policy"]))

    rows.sort(key=sort_key)
    return {
        "reference_bound": reference,
        "old_applied_bound": old_bound,
        "new_applied_bound": new_bound,
        "available": source is not None and bool(block),
        "cells": rows,
        "total_stops": sum(r["stops"] for r in rows),
        "total_censored": sum(r["censored"] for r in rows),
        "checks": {status: sum(1 for r in rows if r["check"] == status)
                   for status in ("agrees", "disagrees", "unverifiable")},
    }


def _censored_by_cell(bound: Mapping[str, Any]) -> dict[tuple[CellKey, str], int]:
    out: dict[tuple[CellKey, str], int] = {}
    for row in bound["cells"]:
        key = (tuple(row["key"]), row["policy"])
        out[key] = out.get(key, 0) + row["censored"]
    return out


# -- the comparison ---------------------------------------------------------------------------------------------


def compare_cells(old: Mapping[str, Any], new: Mapping[str, Any],
                  censored: Mapping[tuple[CellKey, str], int] | None = None) -> list[dict[str, Any]]:
    """Every (cell, arm) of either report, in the study's order, each metric
    old against new. ``bound_censored``: episodes of this arm (and, for a
    sensitivity row, of the current value's run it is paired with) that the
    old bound changed; ``None`` when the bound counts are unavailable."""

    old_cells, new_cells = _cells(old), _cells(new)
    keys = sorted(set(old_cells) | set(new_cells),
                  key=lambda k: (old_cells.get(k) or new_cells[k]).order)
    rows = []
    for key in keys:
        a, b = old_cells.get(key), new_cells.get(key)
        describe = (b or a).describe  # type: ignore[union-attr]
        for policy in _policies(a.policies if a else None, b.policies if b else None):
            left = (a.policies.get(policy) if a else None) or {}
            right = (b.policies.get(policy) if b else None) or {}
            names = [n for n in dict.fromkeys(list(left) + list(right))]
            metrics = [quantity(n, *_pair(left.get(n), right.get(n))) for n in names]
            hit = None
            if censored is not None:
                hit = censored.get((key, policy), 0)
                current = describe.get("current")
                if key[0] == "sensitivity" and current is not None and current != key[2]:
                    # A sweep row's difference is paired with the current value's run.
                    hit += censored.get((("sensitivity", key[1], current), policy), 0)
            rows.append({
                "key": list(key),
                "cell": _cell_label(describe),
                "describe": describe,
                "policy": policy,
                "bound_censored": hit,
                "status": _worst([m["status"] for m in metrics]),
                "metrics": metrics,
            })
    return rows


def _pair(left: tuple[Any, Any] | None, right: tuple[Any, Any] | None) -> tuple[Any, Any, Any, Any]:
    lv, lc = left if left else (None, None)
    rv, rc = right if right else (None, None)
    return lv, rv, lc, rc


def attribution(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Every arm the bound left untouched must be identical in both reports."""

    untouched = [r for r in rows if r["bound_censored"] == 0]
    differing = [f"{r['cell']} {r['policy']}" for r in untouched if r["status"] not in ("identical", "missing")]
    touched = [r for r in rows if r["bound_censored"]]
    return {
        "checked": bool(rows) and all(r["bound_censored"] is not None for r in rows),
        "untouched_rows": len(untouched),
        "untouched_identical": sum(1 for r in untouched if r["status"] == "identical"),
        "untouched_differing": differing,
        "touched_rows": [f"{r['cell']} {r['policy']}" for r in touched],
    }


def ranks(old: Mapping[str, Any], new: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Each main and regime cell's arms by mean minutes per episode (ties by the
    study's arm order), old against new."""

    old_cells, new_cells = _cells(old), _cells(new)
    keys = sorted((k for k in set(old_cells) | set(new_cells) if k[0] in ("main", "regimes")),
                  key=lambda k: (old_cells.get(k) or new_cells[k]).order)
    out = []
    for key in keys:
        def order(cell: _Cell | None) -> list[str]:
            if cell is None:
                return []
            scored = [(p, _number(m.get("mean_total_minutes", (None, None))[0])) for p, m in cell.policies.items()]
            scored = [(p, v) for p, v in scored if v is not None]
            return [p for p, _v in sorted(scored, key=lambda pv: (pv[1], _policy_key(pv[0])))]

        a, b = order(old_cells.get(key)), order(new_cells.get(key))
        moved = [p for p in _policies(dict.fromkeys(a), dict.fromkeys(b))
                 if p in a and p in b and a.index(p) != b.index(p)]
        describe = (new_cells.get(key) or old_cells[key]).describe
        out.append({"cell": _cell_label(describe), "old": a, "new": b, "changed": moved,
                    "winner_changed": bool(a and b and a[0] != b[0])})
    return out


# -- headline claims --------------------------------------------------------------------------------------------

Value = tuple[Any, Any]  # (point, CI)


def _regime_value(report: Mapping[str, Any], strength: Any, repair: float, policy: str,
                  metric: str = "mean_total_minutes", ci: str | None = "total_minutes_ci95") -> Value:
    for row in report.get("regimes") or []:
        if strength_label(row.get("consistency")) == strength_label(strength) and \
                _number(row.get("repair_minutes")) == float(repair):
            block = _get(row, "policies", policy)
            return _get(block, metric), (_get(block, ci) if ci else None)
    return None, None


def _regime_stop(report: Mapping[str, Any], strength: Any, repair: float, policy: str, reason: str) -> Value:
    for row in report.get("regimes") or []:
        if strength_label(row.get("consistency")) == strength_label(strength) and \
                _number(row.get("repair_minutes")) == float(repair):
            return _get(row, "policies", policy, "stop_reasons", reason), None
    return None, None


def _regime_minutes_per_nat(report: Mapping[str, Any], strength: Any, repair: float, policy: str) -> Value:
    for row in report.get("regimes") or []:
        if strength_label(row.get("consistency")) == strength_label(strength) and \
                _number(row.get("repair_minutes")) == float(repair):
            block = _get(row, "value_of_checks", policy)
            return _get(block, "minutes_per_nat"), _get(block, "minutes_per_nat_ci95")
    return None, None


def _sweep_value(report: Mapping[str, Any], parameter: str, value: float, policy: str,
                 metric: str = "difference") -> Value:
    for row in _get(report, "sensitivity", "parameters", parameter, "rows") or []:
        if _number(row.get("value")) == float(value):
            block = _get(row, "policies", policy)
            if metric == "difference":
                return _get(block, "difference_vs_current", "mean_difference"), _get(block, "difference_vs_current", "ci95")
            return _get(block, "mean_total_minutes"), _get(block, "total_minutes_ci95")
    return None, None


def _sweep_values(report: Mapping[str, Any], parameter: str) -> list[float]:
    rows = _get(report, "sensitivity", "parameters", parameter, "rows") or []
    return sorted(v for v in (_number(r.get("value")) for r in rows) if v is not None)


def _part_c(report: Mapping[str, Any], strength: Any, encounters: float, policy: str) -> Value:
    for row in _get(report, "part_c", "rows") or []:
        if strength_label(row.get("consistency")) == strength_label(strength) and \
                _number(row.get("encounters")) == float(encounters) and row.get("policy") == policy:
            return _get(row, "difference", "mean_difference"), _get(row, "difference", "ci95")
    return None, None


def _part_c_encounters(report: Mapping[str, Any]) -> list[float]:
    return sorted({v for v in (_number(r.get("encounters")) for r in _get(report, "part_c", "rows") or [])
                   if v is not None})


def _diff(a: Value, b: Value) -> Value:
    x, y = _number(a[0]), _number(b[0])
    return (None if x is None or y is None else round(x - y, 6)), None


def _below(value: Value) -> bool | None:
    ci = _interval(value[1])
    return None if ci is None else ci[1] < 0


def _above(value: Value) -> bool | None:
    ci = _interval(value[1])
    return None if ci is None else ci[0] > 0


def _spans_zero(value: Value) -> bool | None:
    ci = _interval(value[1])
    return None if ci is None else ci[0] <= 0 <= ci[1]


def _lt(a: Value, b: Value) -> bool | None:
    x, y = _number(a[0]), _number(b[0])
    return None if x is None or y is None else x < y


def _all(values: Sequence[bool | None]) -> bool | None:
    if any(v is None for v in values) or not values:
        return None
    return all(values)  # type: ignore[arg-type]


@dataclass(frozen=True)
class Claim:
    id: str
    statement: str
    where: str
    #: report -> ordered (label, (point, CI)) pairs
    quantities: Callable[[Mapping[str, Any]], list[tuple[str, Value]]]
    #: the quantities by label -> does the claim's conclusion hold in this report
    holds: Callable[[Mapping[str, Value]], bool | None]


def _claims_s2(report: Mapping[str, Any]) -> list[tuple[str, Value]]:
    out = []
    for repair in (3.0, 10.0, 30.0):
        out.append((f"incumbent fitted/{repair:g}", _regime_value(report, None, repair, "incumbent")))
        out.append((f"evsi fitted/{repair:g}", _regime_value(report, None, repair, "evsi")))
    return out


def _strong(report: Mapping[str, Any], strength: float, repair: float) -> list[tuple[str, Value]]:
    return [(f"{p} {strength:g}/{repair:g}", _regime_value(report, strength, repair, p)) for p in P.POLICIES + P.VARIANTS]


def _arms_lowest(values: Mapping[str, Value], winner: str, cell: str) -> bool | None:
    scored = {label.split(" ")[0]: _number(v[0]) for label, v in values.items() if label.endswith(cell)}
    if not scored or any(v is None for v in scored.values()) or winner not in scored:
        return None
    return min(scored, key=lambda p: (scored[p], _policy_key(p))) == winner


def _value_per_nat(report: Mapping[str, Any]) -> list[tuple[str, Value]]:
    name = "robust_composition.VALUE_PER_NAT_MINUTES"
    out = []
    for value in _sweep_values(report, name):
        out.append((f"eig_no_gate total @{value:g}", _sweep_value(report, name, value, "eig_no_gate", "total")))
        out.append((f"eig_no_gate delta @{value:g}", _sweep_value(report, name, value, "eig_no_gate")))
    for value in _sweep_values(report, name):
        out.append((f"eig delta @{value:g}", _sweep_value(report, name, value, "eig")))
    return out


def _value_per_nat_holds(values: Mapping[str, Value]) -> bool | None:
    totals = {label.split("@")[1]: _number(v[0]) for label, v in values.items()
              if label.startswith("eig_no_gate total")}
    if not totals or any(v is None for v in totals.values()):
        return None
    best = min(totals, key=lambda k: (totals[k], float(k)))
    return best == "10" and bool(_below(values.get("eig_no_gate delta @10", (None, None))))


def _minutes_per_nat(report: Mapping[str, Any]) -> list[tuple[str, Value]]:
    out = []
    for strength, repair in (("fitted", 3.0), (0.9, 3.0), (0.9, 10.0), (0.9, 30.0)):
        for policy in ("incumbent", "caps_only"):
            out.append((f"{policy} {strength_label(strength)}/{repair:g}",
                        _regime_minutes_per_nat(report, strength, repair, policy)))
    abstain = _get(report, "main", "eedi_fitted", "eig", "episodes", "stop_reasons", "abstain")
    episodes = _get(report, "main", "eedi_fitted", "eig", "episodes", "episodes")
    share = None if abstain is None or not episodes else round(float(abstain) / float(episodes), 4)
    out.append(("eig agreement-gate abstentions (share, fitted/3)", (share, None)))
    return out


def _minutes_per_nat_holds(values: Mapping[str, Value]) -> bool | None:
    highs = [_interval(v[1]) for label, v in values.items() if "/" in label and "abstentions" not in label]
    if any(h is None for h in highs) or not highs:
        return None
    return 60.0 > max(h[1] for h in highs)  # type: ignore[index]


def _sweep_claim(parameter: str, policies: Sequence[str], prefix: str = "") -> Callable[[Mapping[str, Any]], list[tuple[str, Value]]]:
    """Each swept value's paired difference against the current value, per arm."""

    def read(report: Mapping[str, Any]) -> list[tuple[str, Value]]:
        current = _number(_get(report, "sensitivity", "parameters", parameter, "current"))
        out = []
        for value in _sweep_values(report, parameter):
            if current is not None and abs(value - current) <= SAME:
                continue
            for policy in policies:
                out.append((f"{prefix}{policy} delta @{value:g}", _sweep_value(report, parameter, value, policy)))
        return out
    return read


def _no_minutes_effect(values: Mapping[str, Value]) -> bool | None:
    """Every paired difference is within noise (its CI spans 0) or negligible
    (under 0.05 minutes per episode: EVSI as built at a concentration of 4 or
    10 moves 0.013 with a CI just clear of 0)."""

    verdicts = []
    for value in values.values():
        spans, point = _spans_zero(value), _number(value[0])
        verdicts.append(None if spans is None or point is None else (spans or abs(point) < 0.05))
    return _all(verdicts)


def _max_abs_at_most(limit: float) -> Callable[[Mapping[str, Value]], bool | None]:
    def holds(values: Mapping[str, Value]) -> bool | None:
        points = [_number(v[0]) for v in values.values()]
        if not points or any(p is None for p in points):
            return None
        return max(abs(p) for p in points) <= limit  # type: ignore[arg-type]
    return holds


def _never_negative(values: Mapping[str, Value]) -> bool | None:
    points = [_number(v[0]) for v in values.values()]
    if not points or any(p is None for p in points):
        return None
    return all(p >= -SAME for p in points)  # type: ignore[operator]


def _part_c_claim(report: Mapping[str, Any]) -> list[tuple[str, Value]]:
    out = []
    for strength in ("fitted", 0.9):
        for encounters in _part_c_encounters(report):
            for policy in ("evsi_lcb_only", "evsi_lookahead"):
                out.append((f"{policy} {strength_label(strength)} x{encounters:g}",
                            _part_c(report, strength, encounters, policy)))
    return out


def _part_c_holds(values: Mapping[str, Value]) -> bool | None:
    """Charging the true cost pays off (CI below 0) at consistency 0.9 from 12
    encounters (U = 3.6 min) on, and nowhere below; never a CI above 0."""

    verdicts = []
    for label, value in values.items():
        policy, strength, encounters = label.split(" ")
        n = float(encounters[1:])
        below, above = _below(value), _above(value)
        if below is None:
            return None
        verdicts.append(not above)
        if strength == "0.9":
            verdicts.append(below if n >= 12 else not below)
        else:
            verdicts.append(not below or n >= 12)
    return _all(verdicts)


CLAIMS: tuple[Claim, ...] = (
    Claim("S2", "At Eedi's strength every value rule stops after the opening error and beats today's incumbent "
          "(3.77 vs 1.81 min at repair 3; 7.98 vs 6.03 at 10; 20.03 vs 18.08 at 30)", "Summary 2, §4.2, §4.3",
          _claims_s2,
          lambda v: _all([_lt(v[f"evsi fitted/{r}"], v[f"incumbent fitted/{r}"]) for r in ("3", "10", "30")])),
    Claim("S3a", "Where checks are strong (0.9/30) EVSI as built costs more than the incumbent (17.9 vs 13.3 min)",
          "Summary 3, §4.3", lambda r: _strong(r, 0.9, 30.0),
          lambda v: _lt(v["incumbent 0.9/30"], v["evsi 0.9/30"])),
    Claim("S3b", "... because of the flip abstention: ignoring it saves 5.4 min (12.5)", "Summary 3, §4.3, §5",
          lambda r: _strong(r, 0.9, 30.0), lambda v: _lt(v["evsi_lcb_only 0.9/30"], v["evsi 0.9/30"])),
    Claim("S3c", "... and of one-step valuation: the 2-3 check lookahead saves another 1.8 (10.8), 2.6 below the "
          "incumbent", "Summary 3, §4.3, §5", lambda r: _strong(r, 0.9, 30.0),
          lambda v: _all([_lt(v["evsi_lookahead 0.9/30"], v["evsi_lcb_only 0.9/30"]),
                          _lt(v["evsi_lookahead 0.9/30"], v["incumbent 0.9/30"])])),
    Claim("S3d", "1.1-1.2 min remain against caps-only and eig_no_gate at 0.9/30 (eig_no_gate the best rule there)",
          "§4.3", lambda r: _strong(r, 0.9, 30.0),
          lambda v: _all([_lt(v["caps_only 0.9/30"], v["evsi_lookahead 0.9/30"]),
                          _lt(v["eig_no_gate 0.9/30"], v["evsi_lookahead 0.9/30"]),
                          _arms_lowest(v, "eig_no_gate", "0.9/30")])),
    Claim("S3e", "The lookahead is the best rule at 0.9/10 (4.99 vs incumbent 5.82, caps-only 5.13)", "Summary 3, §4.3",
          lambda r: _strong(r, 0.9, 10.0), lambda v: _arms_lowest(v, "evsi_lookahead", "0.9/10")),
    Claim("S3f", "Today's robust completion gate costs 3.7 min per episode at 0.9/30 (incumbent 13.3 vs caps-only 9.6) "
          "and ends 190 of 400 episodes at 0.9, 296 at Eedi's strength", "Summary 3, §4.3, §5, §9.3",
          lambda r: [("incumbent 0.9/30", _regime_value(r, 0.9, 30.0, "incumbent")),
                     ("caps_only 0.9/30", _regime_value(r, 0.9, 30.0, "caps_only")),
                     ("gate cost (incumbent - caps_only) 0.9/30",
                      _diff(_regime_value(r, 0.9, 30.0, "incumbent"), _regime_value(r, 0.9, 30.0, "caps_only"))),
                     ("gate stops 0.9/30", _regime_stop(r, 0.9, 30.0, "incumbent", "couldnt_reliably_distinguish")),
                     ("gate stops fitted/3", _regime_stop(r, None, 3.0, "incumbent", "couldnt_reliably_distinguish"))],
          lambda v: _lt(v["caps_only 0.9/30"], v["incumbent 0.9/30"])),
    Claim("S3g", "The eig_no_gate arm in every regime (8.44 min at Eedi/3, the worst rule there; the best rule at "
          "0.7/30, 15.45, and at 0.9/30, 9.58)", "§4.2, §4.3",
          lambda r: [(f"eig_no_gate {strength_label(s)}/{rep:g}", _regime_value(r, s, rep, "eig_no_gate"))
                     for s in ("fitted", 0.7, 0.9) for rep in (3.0, 10.0, 30.0)]
          + [("eig_no_gate checks fitted/3", _regime_value(r, None, 3.0, "eig_no_gate", "mean_checks", None))]
          + _strong(r, 0.7, 30.0) + _strong(r, 0.9, 30.0),
          lambda v: _all([_arms_lowest(v, "eig_no_gate", "0.7/30"), _arms_lowest(v, "eig_no_gate", "0.9/30")])),
    Claim("S4a", "VALUE_PER_NAT_MINUTES on the gate-free EIG rule (0.9/10): best at 10 (4.75 min, -1.89 "
          "[-2.26, -1.52] vs 60); with the gate the scale barely matters", "Summary 4, §4.4, §5",
          _value_per_nat, _value_per_nat_holds),
    Claim("S4b", "60 is 4-500x the measured minutes per nat; the 90% agreement gate abstains in 89% of the EIG "
          "path's episodes", "Summary 4, §4.4", _minutes_per_nat, _minutes_per_nat_holds),
    Claim("S5a", "ROBUST_QUANTILE 0.10 -> 0.25 changes minutes within noise (lcb-only -0.10, lookahead -0.15)",
          "Summary 5, §4.4, §5",
          _sweep_claim("robust_composition.ROBUST_QUANTILE", ("evsi", "evsi_lcb_only", "evsi_lookahead")),
          _no_minutes_effect),
    Claim("S5b", "PERTURBATION_DELTA has no minutes effect (|delta| <= 0.03)", "Summary 5, §4.4, §5",
          _sweep_claim("evsi.PERTURBATION_DELTA", ("evsi", "evsi_lcb_only", "evsi_lookahead")),
          _max_abs_at_most(0.05)),
    Claim("S5c", "INSTRUMENT_PERTURBATION_CONCENTRATION and the draw count move rankings, not minutes", "§4.4, §5",
          lambda r: _sweep_claim("robust_composition.INSTRUMENT_PERTURBATION_CONCENTRATION",
                                 ("evsi", "evsi_lcb_only", "evsi_lookahead"), "concentration: ")(r)
          + _sweep_claim("robust_composition.ROBUST_DRAW_COUNT (simulation draws)",
                         ("evsi", "evsi_lcb_only", "evsi_lookahead"), "draws: ")(r),
          _no_minutes_effect),
    Claim("S5d", "A positive BURDEN_COST only adds minutes", "§4.4, §5",
          _sweep_claim("robust_composition.BURDEN_COST", ("evsi_lcb_only", "evsi_lookahead")), _never_negative),
    Claim("S5e", "Knowing the true repair minutes (10, not 3) is worth 0.71-1.06 min per episode", "Summary 5, §4.4",
          lambda r: [(f"{p} delta @10", _sweep_value(r, "action_loss.DEFAULT_INTERVENTION_MINUTES (repair minutes)",
                                                      10.0, p)) for p in ("evsi_lcb_only", "evsi_lookahead")],
          lambda v: _all([_below(x) for x in v.values()])),
    Claim("S5f", "The causal default check burden 1.5 over-states a 1-minute check (+0.30, +0.44)", "§4.4, §5",
          lambda r: [(f"{p} delta @1.5", _sweep_value(r, "check minutes (probe burden; causal selector default 1.5)",
                                                       1.5, p)) for p in ("evsi_lcb_only", "evsi_lookahead")],
          lambda v: _all([_above(x) for x in v.values()])),
    Claim("S6", "Charging the measured unresolved cost pays off once it reaches about 3.6 min (consistency 0.9) and "
          "costs nothing measurable below", "Summary 6, §4.5, §9.1", _part_c_claim, _part_c_holds),
)


def compare_claims(old: Mapping[str, Any], new: Mapping[str, Any]) -> list[dict[str, Any]]:
    out = []
    for claim in CLAIMS:
        a, b = claim.quantities(old), claim.quantities(new)
        labels = list(dict.fromkeys([label for label, _v in a] + [label for label, _v in b]))
        a_map, b_map = dict(a), dict(b)
        quantities = [quantity(label, *_pair(a_map.get(label), b_map.get(label))) for label in labels]
        holds_old, holds_new = claim.holds(a_map), claim.holds(b_map)
        out.append({
            "id": claim.id,
            "statement": claim.statement,
            "where": claim.where,
            "status": _worst([q["status"] for q in quantities]),
            "moved": [q["label"] for q in quantities if q["status"] not in ("identical", "missing")],
            "beyond_ci": [q["label"] for q in quantities if q["status"] == "moved_beyond_ci"],
            "holds_old": holds_old,
            "holds_new": holds_new,
            "conclusion_changed": holds_old is not None and holds_new is not None and holds_old != holds_new,
            "quantities": quantities,
        })
    return out


def compare_reports(old: Mapping[str, Any], new: Mapping[str, Any]) -> dict[str, Any]:
    """The whole comparison, in the study's order (see the module docstring)."""

    bound = bound_stops(old, new)
    censored = _censored_by_cell(bound) if bound["available"] else None
    rows = compare_cells(old, new, censored)
    claims = compare_claims(old, new)
    rank_rows = ranks(old, new)
    statuses = [m["status"] for r in rows for m in r["metrics"]]
    def header(report: Mapping[str, Any]) -> dict[str, Any]:
        return {"version": report.get("version"), "simulation_version": report.get("simulation_version"),
                "applied_bound": applied_bound(report),
                "settings": dict(sorted((report.get("settings") or {}).items()))}

    return {
        "version": COMPARE_VERSION,
        "old": header(old),
        "new": header(new),
        "bound": bound,
        "attribution": attribution(rows) if censored is not None else {"checked": False},
        "summary": {
            "metrics": {status: statuses.count(status) for status in STATUS_ORDER},
            "rows": {status: sum(1 for r in rows if r["status"] == status) for status in STATUS_ORDER},
            "claims": {status: sum(1 for c in claims if c["status"] == status) for status in STATUS_ORDER},
            "conclusions_changed": [c["id"] for c in claims if c["conclusion_changed"]],
            "rank_changes": [r["cell"] for r in rank_rows if r["changed"]],
            "winner_changes": [r["cell"] for r in rank_rows if r["winner_changed"]],
        },
        "claims": claims,
        "ranks": rank_rows,
        "cells": rows,
    }


# -- markdown ---------------------------------------------------------------------------------------------------


def _fmt(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.2f}" if abs(value) >= 10 else f"{value:.3f}".rstrip("0").rstrip(".") if value else "0"


def _fmt_q(point: float | None, ci: list[float] | None) -> str:
    text = _fmt(point)
    return f"{text} [{_fmt(ci[0])}, {_fmt(ci[1])}]" if ci else text


def render_markdown(comparison: Mapping[str, Any]) -> str:
    """Tables for a review file: bound stops, claims, every moved metric, rank changes."""

    lines: list[str] = []
    bound = comparison["bound"]
    lines += ["### Bound stops (cells where the old bound stopped an episode)", "",
              "| Section | Cell | Arm | Episodes | Stopped at the bound | Changed by it (ran past) | Max checks unbounded "
              "| Stored report says |",
              "|---|---|---|---:|---:|---:|---:|---|"]
    for row in bound["cells"]:
        if not row["stops"]:
            continue
        cell = ", ".join(f"{k} {v}" for k, v in row["cell"].items())
        recorded = row["recorded_in_bounded_report"]
        lines.append(f"| {row['section']} | {cell} | `{row['policy']}` | {row['episodes']} | {row['stops']} | "
                     f"{row['censored']} | {row['max_checks_unbounded']} | "
                     f"{recorded if recorded is not None else '—'} ({row['check']}) |")
    lines += ["", f"Total: {bound['total_stops']} stops, {bound['total_censored']} changed; cross-checks "
              f"{bound['checks']}.", ""]
    lines += ["### Claims", "", "| Claim | Status | Moved | Conclusion old → new |", "|---|---|---|---|"]
    for claim in comparison["claims"]:
        moved = "; ".join(
            f"{q['label']}: {_fmt_q(q['old'], q['old_ci95'])} → {_fmt_q(q['new'], q['new_ci95'])}"
            for q in claim["quantities"] if q["status"] not in ("identical", "missing")) or "nothing"
        lines.append(f"| `{claim['id']}` | {claim['status']} | {moved} | {claim['holds_old']} → {claim['holds_new']} |")
    lines += ["", "### Every moved metric", "", "| Cell | Arm | Metric | Old [95% CI] | New [95% CI] | Status |",
              "|---|---|---|---|---|---|"]
    for row in comparison["cells"]:
        for metric in row["metrics"]:
            if metric["status"] in ("identical", "missing"):
                continue
            lines.append(f"| {row['cell']} | `{row['policy']}` | {metric['label']} | "
                         f"{_fmt_q(metric['old'], metric['old_ci95'])} | {_fmt_q(metric['new'], metric['new_ci95'])} | "
                         f"{metric['status']} |")
    lines += ["", "### Rank changes", ""]
    changed = [r for r in comparison["ranks"] if r["changed"]]
    if not changed:
        lines.append("None: every cell ranks the arms in the same order.")
    for row in changed:
        lines.append(f"* {row['cell']}: {' < '.join(row['old'])} → {' < '.join(row['new'])}")
    return "\n".join(lines) + "\n"


__all__ = ["CLAIMS", "COMPARE_VERSION", "applied_bound", "bound_stops", "compare_reports", "quantity",
           "recorded_bound_stops", "render_markdown", "strength_label"]
