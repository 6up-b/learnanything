"""Compare two ``learnloop evsi simulate`` reports: every recorded value, every headline claim.

Stage ``evsi-single-family-unbounded`` (owner-approved 2026-10-13). The
single-family study ran with a 25-check count bound until its v3 report; the
multi-family review (F4) found such a bound binding. The study was rerun
without it, with the same seeds and the stored fit, so every difference between
the two reports is the bound's. This module lines the two reports up:

* **cells**: every recorded value, old against new, and whether a point
  estimate left the other report's 95% CI. Nothing is hand-picked: each arm's
  block in each cell (the main comparison, the regimes, the sensitivity rows,
  Part C) is flattened leaf by leaf (nested quantiles, calibration bins, stop
  reasons, counts), and so is every report-level section (the fit, the bank, the
  misfit, the starting beliefs, Part C's measured rates, the recommendations).
  Only the run's metadata (:data:`METADATA_KEYS`) is left out, and the header
  shows it. A value present in one report only is ``changed``;
* **bound**: the stored run's bound stops per arm and cell. An unbounded run's
  ``count_bound`` cells say exactly which episodes a bound of ``reference_bound``
  checks stopped (common random numbers: an episode runs identically up to the
  bound), so they count only when that is the bound the other report applied;
  otherwise the attribution is reported unavailable, with the reason. They are
  cross-checked against the stop reasons the stored report kept;
* **attribution**: every arm in every cell where the bound stopped no episode
  must be identical in the two reports, and one where it stopped episodes only
  at a check their own rule would have stopped at anyway may differ in its stop
  reasons alone; so whatever moved, moved because of the bound;
* **claims**: each headline claim of ``docs/reviews/evsi-calibration.md``,
  split into independently evaluated assertions (its conclusions, and the
  figures it states, each at the precision stated), under each report;
* **ranks**: each cell's ranking of the arms by mean minutes per episode.

Ordering is the study's, never a stored dict's: a report read back from JSON has
sorted keys, and iterating it would reorder the arms. Read-only, no simulation.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from learnloop.evsi_calibration import policies as P
from learnloop.evsi_calibration.experiments import SWEEPS

#: v2 (Codex review of the stage): every recorded value, the bound attribution
#: only for a matching reference bound, claims as separate assertions.
COMPARE_VERSION = "evsi_simulate_compare_v2"
SECTIONS = ("main", "regimes", "sensitivity", "part_c", "report")
CELL_SECTIONS = SECTIONS[:4]
SYSTEM_MODELS = ("hand_set", "eedi_fitted")
PART_C_LOSSES = ("minutes_only", "measured_unresolved")
#: Report keys that record how a run was made, not what it measured, so they are
#: never compared as metrics: the header shows the version, the settings, the
#: policy defaults and the applied bound; ``count_bound`` feeds the bound
#: attribution; ``sweeps`` is the grid the sensitivity cells already carry.
METADATA_KEYS = ("count_bound", "elapsed_seconds", "policy_defaults", "settings", "simulation_version", "sweeps",
                 "version")
#: The values of a cell that belong to no arm (a sweep row's ``current`` flag).
CELL_ROW = "(cell)"
#: A report-level section, or a recommendation that names no arm.
REPORT_ROW = "(report)"
#: Stored numbers are rounded to 4 places; closer than this they are the same number.
SAME = 1e-9
#: How many stop reasons each section of a report keeps (``None``: all of them).
RECORDED_STOP_REASONS = {"main": None, "regimes": 4, "sensitivity": 3, "part_c": 0}

STATUS_ORDER = ("identical", "moved_within_ci", "moved_no_ci", "moved_beyond_ci", "changed", "missing")
#: The statuses that are a difference between the two reports.
DIFFERS = ("moved_within_ci", "moved_no_ci", "moved_beyond_ci", "changed")


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


def _absent(value: Any) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def _g(value: Any) -> str:
    number = _number(value)
    return f"{number:g}" if number is not None else str(value)


def _policy_key(policy: str) -> tuple[int, int, str]:
    if policy in (CELL_ROW, REPORT_ROW):
        return (0, 0, policy)
    order = P.ALL_POLICIES
    return (1, order.index(policy), "") if policy in order else (2, 0, policy)


def _policies(*mappings: Any) -> list[str]:
    names: set[str] = set()
    for mapping in mappings:
        if isinstance(mapping, Mapping):
            names |= set(mapping)
    return sorted(names, key=_policy_key)


def strength_label(value: Any) -> str:
    """``fitted`` (Eedi's own consistency) or the overriding consistency."""

    if value in (None, "fitted"):
        return "fitted"
    number = _number(value)
    return f"{number:g}" if number is not None else str(value)


def _strength_key(label: str) -> tuple[int, float, str]:
    if label == "fitted":
        return (0, 0.0, "")
    number = _number(label)
    return (1, number, "") if number is not None else (2, 0.0, label)


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


def _shown(raw: Any, number: float | None) -> Any:
    if number is not None:
        return number
    if _absent(raw):
        return None
    return raw if isinstance(raw, (str, bool)) else str(raw)


def quantity(label: str, old: Any, new: Any, old_ci: Any = None, new_ci: Any = None) -> dict[str, Any]:
    """One recorded value in both reports, and how it moved.

    ``moved_beyond_ci``: a point estimate left the other report's 95% CI (either
    way); ``moved_within_ci``: it moved, inside both CIs; ``moved_no_ci``: it
    moved and has no CI (a mean of checks, a count, a difference of two means);
    ``changed``: a value (or its CI) present in one report only (``None`` and NaN
    count as absent), or a value that is not a number (text, a flag) and differs;
    ``missing``: absent from both."""

    a, b = _number(old), _number(new)
    a_ci, b_ci = _interval(old_ci), _interval(new_ci)
    out: dict[str, Any] = {"label": label, "old": _shown(old, a), "old_ci95": a_ci, "new": _shown(new, b),
                           "new_ci95": b_ci, "delta": None}
    same_ci = (a_ci is None and b_ci is None) or (
        a_ci is not None and b_ci is not None and all(abs(x - y) <= SAME for x, y in zip(a_ci, b_ci)))
    if _absent(old) and _absent(new) and a_ci is None and b_ci is None:
        out["status"] = "missing"
        return out
    if a is None or b is None:
        same = _absent(old) == _absent(new) and out["old"] == out["new"] and same_ci
        out["status"] = "identical" if same else "changed"
        return out

    def outside(x: float, ci: list[float] | None) -> bool:
        return ci is not None and (x < ci[0] - SAME or x > ci[1] + SAME)

    if (a_ci is None) != (b_ci is None):
        status = "changed"
    elif abs(b - a) <= SAME and same_ci:
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
    known = [s for s in statuses if s != "missing"]
    if not known:
        return "missing"
    return max(known, key=STATUS_ORDER.index)


# -- flattening -------------------------------------------------------------------------------------------------


class _Ci(tuple):
    """A recorded 95% CI (two endpoints, or empty for ``None``), kept whole so it
    travels with its point estimate."""


#: Which point estimate a CI belongs to, by the CI's key (``ci95``: whichever
#: sibling exists).
CI_POINTS = {
    "total_minutes_ci95": ("mean_total_minutes",),
    "correct_action_ci95": ("correct_action_rate",),
    "entropy_drop_ci95": ("mean_entropy_drop",),
    "truth_log_gain_ci95": ("mean_truth_log_gain",),
    "realized_value_ci95": ("mean_realized_value",),
    "minutes_per_nat_ci95": ("minutes_per_nat",),
    "ci95": ("mean_difference", "mean"),
}
#: Lists of records named by a range: a reliability table's fixed bins by the
#: range itself (an empty bin is left out), the predicted-EIG quintiles (whose
#: edges are data) by their rank.
RANGE_KEYS = (("bin", "value"), ("eig_range", "rank"))
#: Lists of records named by these fields, when they name each record once.
RECORD_KEYS = ("parameter", "policy", "name")
#: The order a block's groups are listed in (the study's §4.2, §4.1, value).
GROUP_ORDER = ("episodes", "outcome_calibration", "information", "action_change", "value_of_checks")
_STOP_REASON = re.compile(r"^(?:(?P<parent>.*)\.)?stop_reasons\.(?P<reason>[^.\[]+)$")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str)


def _records(items: Sequence[Any]) -> list[tuple[str, Any]]:
    """A list's items, each under a name that does not depend on the list's order."""

    if items and all(isinstance(item, Mapping) for item in items):
        for key, how in RANGE_KEYS:
            ranges = [_interval(item.get(key)) for item in items]
            if all(r is not None for r in ranges):
                ordered = sorted(zip(ranges, items), key=lambda pair: (pair[0], _canonical(pair[1])))
                if how == "value" and len({tuple(r) for r in ranges}) == len(ranges):  # type: ignore[arg-type]
                    return [(f"{_g(r[0])}-{_g(r[1])}", {k: v for k, v in item.items() if k != key})
                            for r, item in ordered]
                return [(f"q{n + 1}", item) for n, (_r, item) in enumerate(ordered)]
        keys = [k for k in RECORD_KEYS if any(k in item for item in items)]
        if keys:
            names = [" ".join(f"{k}={item[k]}" for k in keys if k in item) for item in items]
            if len(set(names)) == len(names):
                return [(name, {k: v for k, v in item.items() if k not in keys}) for name, item in zip(names, items)]
    return [(str(n), item) for n, item in enumerate(items)]


def _flatten(value: Any, prefix: str = "", out: dict[str, Any] | None = None) -> dict[str, Any]:
    """Every recorded leaf under ``value`` by a dotted path (``a.b[name].c``); a
    CI stays whole (:class:`_Ci`)."""

    out = {} if out is None else out
    if isinstance(value, Mapping):
        for key in value:
            label = f"{prefix}.{key}" if prefix else str(key)
            child = value[key]
            if str(key).endswith("ci95") and (child is None or (isinstance(child, (list, tuple)) and len(child) == 2)):
                out[label] = _Ci(child or ())
            else:
                _flatten(child, label, out)
    elif isinstance(value, (list, tuple)):
        for name, item in _records(value):
            _flatten(item, f"{prefix}[{name}]", out)
    else:
        out[prefix or "value"] = value
    return out


def _block(value: Any, prefix: str = "") -> dict[str, Any]:
    return {} if value is None else _flatten(value, prefix)


def _metric_key(label: str) -> tuple[int, str]:
    head = re.split(r"[.\[]", label, maxsplit=1)[0]
    if head == label:
        return (0, label)
    return (1 + GROUP_ORDER.index(head) if head in GROUP_ORDER else 1 + len(GROUP_ORDER), label)


def _reasons_complete(reasons: Mapping[str, Any], section: str, episodes: Any) -> bool:
    """Whether a report kept every stop reason of an arm: a section that keeps
    all of them, fewer kept than the section keeps, or kept counts that add up
    to the arm's episodes."""

    if section not in RECORDED_STOP_REASONS:
        return False
    limit = RECORDED_STOP_REASONS[section]
    if limit is None or len(reasons) < limit:
        return True
    total = _number(episodes)
    counts = [_number(v) for v in reasons.values()]
    return total is not None and None not in counts and sum(counts) == total  # type: ignore[arg-type]


def _with_absent_reasons(flat: Mapping[str, Any], other: Mapping[str, Any], section: str) -> dict[str, Any]:
    """A stop reason the other report records and this one does not is 0 here
    when this report kept every stop reason of the arm."""

    out = dict(flat)
    for label in other:
        match = _STOP_REASON.match(label)
        if not match or label in flat:
            continue
        parent = match.group("parent")
        reasons = {}
        for mine in flat:
            m = _STOP_REASON.match(mine)
            if m and m.group("parent") == parent:
                reasons[m.group("reason")] = flat[mine]
        episodes = flat.get(f"{parent}.episodes" if parent else "episodes")
        if reasons and _reasons_complete(reasons, section, episodes):
            out[label] = 0
    return out


def _metrics(left: Mapping[str, Any], right: Mapping[str, Any], section: str) -> list[dict[str, Any]]:
    """Every value of one arm (or one report-level section) in both reports."""

    left, right = _with_absent_reasons(left, right, section), _with_absent_reasons(right, left, section)
    labels = set(left) | set(right)
    sides = (left, right)
    # A CI is one only where each report that records it records an interval
    # (or nothing); anything else there is compared as a value of its own.
    cis = {label for label in labels if any(isinstance(side.get(label), _Ci) for side in sides)
           and all(label not in side or isinstance(side[label], _Ci) for side in sides)}

    def plain(value: Any) -> Any:
        return (list(value) or None) if isinstance(value, _Ci) else value
    point_of: dict[str, str] = {}
    for label in cis:
        parent, _dot, last = label.rpartition(".")
        for point in CI_POINTS.get(last, ()):
            candidate = f"{parent}.{point}" if parent else point
            if candidate in labels and candidate not in cis:
                point_of[label] = candidate
                break
    ci_for = {point: ci for ci, point in point_of.items()}
    out = []
    for label in sorted(labels - set(point_of), key=_metric_key):
        if label in cis:  # a CI with no point estimate: its two ends
            ends = _interval(left.get(label)), _interval(right.get(label))
            for i in (0, 1):
                out.append(quantity(f"{label}[{i}]", ends[0][i] if ends[0] else None, ends[1][i] if ends[1] else None))
            continue
        ci = ci_for.get(label)
        out.append(quantity(label, plain(left.get(label)), plain(right.get(label)),
                            left.get(ci) if ci else None, right.get(ci) if ci else None))
    return out


# -- cells ------------------------------------------------------------------------------------------------------

CellKey = tuple[Any, ...]


@dataclass(frozen=True)
class _Cell:
    key: CellKey
    order: tuple[Any, ...]
    describe: dict[str, Any]
    #: policy (or :data:`CELL_ROW` / :data:`REPORT_ROW`) -> flattened values
    policies: dict[str, dict[str, Any]]


def _cells(report: Mapping[str, Any]) -> dict[CellKey, _Cell]:
    cells: dict[CellKey, _Cell] = {}
    main = report.get("main") or {}
    models = list(SYSTEM_MODELS) + sorted(m for m in main if m not in SYSTEM_MODELS)
    for index, model in enumerate(models):
        if model not in main:
            continue
        key = ("main", model)
        cells[key] = _Cell(key, (0, index), {"section": "main", "system_model": model},
                           {p: _block(b) for p, b in (main[model] or {}).items()})
    for row in report.get("regimes") or []:
        strength = strength_label(row.get("consistency"))
        repair = _number(row.get("repair_minutes"))
        key = ("regimes", strength, repair)
        policies: dict[str, dict[str, Any]] = {}
        for policy in _policies(row.get("policies"), row.get("value_of_checks")):
            values = _block(_get(row, "policies", policy))
            values.update(_block(_get(row, "value_of_checks", policy), "value_of_checks"))
            policies[policy] = values
        extra = {k: v for k, v in row.items() if k not in ("consistency", "repair_minutes", "policies", "value_of_checks")}
        if extra:
            policies[CELL_ROW] = _flatten(extra)
        cells[key] = _Cell(key, (1, _strength_key(strength), repair),
                           {"section": "regimes", "consistency": strength, "repair_minutes": repair}, policies)
    sensitivity = report.get("sensitivity") or {}
    for name, parameter in (sensitivity.get("parameters") or {}).items():
        current = _number(parameter.get("current"))
        for row in parameter.get("rows") or []:
            value = _number(row.get("value"))
            key = ("sensitivity", name, value)
            policies = {p: _block(b) for p, b in (row.get("policies") or {}).items()}
            extra = {k: v for k, v in row.items() if k not in ("value", "policies")}
            if extra:
                policies[CELL_ROW] = _flatten(extra)
            cells[key] = _Cell(key, (2, _sweep_key(name), value),
                               {"section": "sensitivity", "parameter": name, "value": value, "current": current},
                               policies)
    part_c = report.get("part_c") or {}
    for row in part_c.get("rows") or []:
        strength = strength_label(row.get("consistency"))
        encounters = _number(row.get("encounters"))
        key = ("part_c", strength, encounters)
        if key not in cells:
            cells[key] = _Cell(key, (3, _strength_key(strength), encounters),
                               {"section": "part_c", "consistency": strength, "encounters": encounters}, {})
        cells[key].policies[str(row.get("policy"))] = _flatten(
            {k: v for k, v in row.items() if k not in ("consistency", "encounters", "policy")})

    # Report-level sections: everything that is neither a cell nor metadata.
    def report_cell(part: str, item: str, policy: str, values: dict[str, Any]) -> None:
        key = ("report", part, item)
        if key not in cells:
            cells[key] = _Cell(key, (4, part, item), {"section": "report", "part": part, "item": item}, {})
        cells[key].policies[policy] = values

    for part in sorted(report):
        value = report[part]
        if part in METADATA_KEYS or part in ("main", "regimes"):  # the regimes and main are all cells
            continue
        if part == "sensitivity":
            extra = {k: v for k, v in (value or {}).items() if k != "parameters"}
            if extra:
                report_cell(part, "", REPORT_ROW, _flatten(extra))
            for name, parameter in ((value or {}).get("parameters") or {}).items():
                extra = {k: v for k, v in (parameter or {}).items() if k != "rows"}
                if extra:
                    report_cell(part, name, REPORT_ROW, _flatten(extra))
            continue
        if part == "part_c":
            extra = {k: v for k, v in (value or {}).items() if k != "rows"}
            if extra:
                report_cell(part, "", REPORT_ROW, _flatten(extra))
            continue
        if part == "recommendations" and isinstance(value, list):
            # One row per recommendation, named by its parameter and arm (a
            # repeated name is numbered in the order of the records' content).
            named: dict[tuple[str, str], list[dict[str, Any]]] = {}
            for record in value:
                record = dict(record) if isinstance(record, Mapping) else {"value": record}
                name = (str(record.pop("parameter", "")), str(record.pop("policy", None) or REPORT_ROW))
                named.setdefault(name, []).append(record)
            for (parameter, policy), records in named.items():
                for n, record in enumerate(sorted(records, key=_canonical)):
                    report_cell(part, parameter, policy if n == 0 else f"{policy} #{n + 1}", _flatten(record))
            continue
        report_cell(part, "", REPORT_ROW, _block(value) if isinstance(value, (Mapping, list, tuple))
                    else {"value": value})
    return cells


def _cell_label(describe: Mapping[str, Any]) -> str:
    section = describe["section"]
    if section == "main":
        return f"main {describe['system_model']}"
    if section == "regimes":
        return f"{describe['consistency']}/{_g(describe['repair_minutes'])}"
    if section == "sensitivity":
        return f"{describe['parameter']} = {_g(describe['value'])}"
    if section == "part_c":
        return f"part C {describe['consistency']} x{_g(describe['encounters'])}"
    return f"report {describe['part']}" + (f": {describe['item']}" if describe["item"] else "")


def _minutes(flat: Mapping[str, Any] | None) -> float | None:
    if not flat:
        return None
    return _number(flat.get("episodes.mean_total_minutes", flat.get("mean_total_minutes")))


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
    return (0, "recorded") if _reasons_complete(reasons, key[0], episodes) else (None, "truncated")


def _bound_result(old_bound: Any, new_bound: Any, relation: str, *, reference: Any = None, reason: str | None = None,
                  rows: Sequence[dict[str, Any]] = ()) -> dict[str, Any]:
    return {
        "relation": relation,
        "available": relation in ("bounded_vs_unbounded", "same_bound"),
        "reason": reason,
        "reference_bound": reference,
        "old_applied_bound": old_bound,
        "new_applied_bound": new_bound,
        "cells": list(rows),
        "total_stops": sum(r["stops"] for r in rows),
        "total_censored": sum(r["censored"] for r in rows),
        "checks": {status: sum(1 for r in rows if r["check"] == status)
                   for status in ("agrees", "disagrees", "unverifiable")},
    }


def bound_stops(old: Mapping[str, Any], new: Mapping[str, Any]) -> dict[str, Any]:
    """Per cell and arm, the episodes the bounded report's bound stopped, read
    from the unbounded report's ``count_bound`` cells, and what the bounded
    report itself recorded.

    Those counts are a bound's only when the unbounded run counted the stops of
    the very bound the other report applied (its ``reference_bound``); anything
    else is ``unsupported`` (``available`` false, with the ``reason``): two
    bounded reports, an unbounded report without ``count_bound``, or one that
    counted another bound. Two reports under the same bound (or both without
    one) are ``same_bound``: the bound explains no difference between them."""

    old_bound, new_bound = applied_bound(old), applied_bound(new)
    if old_bound == new_bound:
        return _bound_result(old_bound, new_bound, "same_bound", reference=old_bound,
                             reason="both reports ran under the same bound, which explains no difference between them")
    if old_bound is not None and new_bound is not None:
        return _bound_result(old_bound, new_bound, "unsupported", reason=(
            f"both reports are bounded ({old_bound} and {new_bound} checks): no unbounded run counts either "
            "bound's stops"))
    source, bounded, bound = (new, old, old_bound) if new_bound is None else (old, new, new_bound)
    block = source.get("count_bound")
    if not isinstance(block, Mapping) or not block.get("cells"):
        return _bound_result(old_bound, new_bound, "unsupported", reason=(
            "the unbounded report records no count_bound cells (a report before v3)"))
    reference = block.get("reference_bound")
    if block.get("applied_bound") is not None:
        return _bound_result(old_bound, new_bound, "unsupported", reference=reference, reason=(
            f"the unbounded report's count_bound says it ran under a {block.get('applied_bound')}-check bound"))
    if reference != bound:
        return _bound_result(old_bound, new_bound, "unsupported", reference=reference, reason=(
            f"the unbounded report counted the stops of a {reference}-check bound, but the bounded report ran under "
            f"{bound}: rerun the unbounded study with --reference-bound {bound}"))
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
    return _bound_result(old_bound, new_bound, "bounded_vs_unbounded", reference=reference, rows=rows)


def _bounds_by_cell(bound: Mapping[str, Any]) -> dict[tuple[CellKey, str], tuple[int, int]]:
    out: dict[tuple[CellKey, str], tuple[int, int]] = {}
    for row in bound["cells"]:
        key = (tuple(row["key"]), row["policy"])
        stops, censored = out.get(key, (0, 0))
        out[key] = (stops + row["stops"], censored + row["censored"])
    return out


def _row_bound(bounds: Mapping[tuple[CellKey, str], tuple[int, int]], key: CellKey, policy: str,
               describe: Mapping[str, Any]) -> tuple[int, int]:
    """The episodes behind one row that the bound stopped, and those it changed
    (ran past it unbounded)."""

    def at(cell: CellKey) -> tuple[int, int]:
        return bounds.get((cell, policy), (0, 0))

    if key[0] == "sensitivity":
        stops, censored = at(key)
        current = describe.get("current")
        if current is not None and current != key[2]:
            # A sweep row's difference is paired with the current value's run.
            more = at(("sensitivity", key[1], current))
            stops, censored = stops + more[0], censored + more[1]
        return stops, censored
    if key[0] == "report" and key[1] == "recommendations":
        # A sweep's recommendation is read off its rows (best value, difference).
        hits = [v for (cell, p), v in bounds.items() if p == policy and cell[0] == "sensitivity" and cell[1] == key[2]]
        return sum(h[0] for h in hits), sum(h[1] for h in hits)
    return at(key)


# -- the comparison ---------------------------------------------------------------------------------------------


def compare_cells(old: Mapping[str, Any], new: Mapping[str, Any],
                  bounds: Mapping[tuple[CellKey, str], tuple[int, int]] | None = None) -> list[dict[str, Any]]:
    """Every (cell, arm) of either report, and every report-level section, in
    the study's order, each recorded value old against new. ``bound_stops``:
    episodes of this arm (and, for a sensitivity row, of the current value's
    run it is paired with) that the bound stopped; ``bound_censored``: those of
    them it changed (they run past it unbounded); ``None`` when the bound counts
    are unavailable."""

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
            metrics = _metrics(left, right, key[0])
            stops = censored = None
            if bounds is not None:
                stops, censored = _row_bound(bounds, key, policy, describe)
            rows.append({
                "key": list(key),
                "cell": _cell_label(describe),
                "describe": describe,
                "policy": policy,
                "bound_stops": stops,
                "bound_censored": censored,
                "status": _worst([m["status"] for m in metrics]),
                "metrics": metrics,
            })
    return rows


def attribution(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Every arm where the bound stopped no episode must be identical in both
    reports; one where it stopped episodes only at a check their own rule would
    have stopped at anyway (none ran past it unbounded) may differ only in its
    stop reasons."""

    def name(row: Mapping[str, Any]) -> str:
        return f"{row['cell']} {row['policy']}"

    untouched = [r for r in rows if r["bound_stops"] == 0]
    renamed = [r for r in rows if r["bound_stops"] and not r["bound_censored"]]
    renamed_differing = [
        name(r) for r in renamed
        if any(m["status"] in DIFFERS and not _STOP_REASON.match(m["label"]) for m in r["metrics"])]
    return {
        "checked": bool(rows) and all(r["bound_stops"] is not None for r in rows),
        "untouched_rows": len(untouched),
        "untouched_identical": sum(1 for r in untouched if r["status"] in ("identical", "missing")),
        "untouched_differing": [name(r) for r in untouched if r["status"] in DIFFERS],
        "renamed_only_rows": [name(r) for r in renamed],
        "renamed_only_differing": renamed_differing,
        "touched_rows": [name(r) for r in rows if r["bound_censored"]],
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
            scored = [(p, _minutes(m)) for p, m in cell.policies.items() if p not in (CELL_ROW, REPORT_ROW)]
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
Values = Mapping[str, Value]
NONE: Value = (None, None)


def _regime_row(report: Mapping[str, Any], strength: Any, repair: float) -> Mapping[str, Any] | None:
    for row in report.get("regimes") or []:
        if strength_label(row.get("consistency")) == strength_label(strength) and \
                _number(row.get("repair_minutes")) == float(repair):
            return row
    return None


def _regime_value(report: Mapping[str, Any], strength: Any, repair: float, policy: str,
                  metric: str = "mean_total_minutes", ci: str | None = "total_minutes_ci95") -> Value:
    block = _get(_regime_row(report, strength, repair), "policies", policy)
    return _get(block, metric), (_get(block, ci) if ci else None)


def _regime_stop(report: Mapping[str, Any], strength: Any, repair: float, policy: str, reason: str) -> Value:
    reasons = _get(_regime_row(report, strength, repair), "policies", policy, "stop_reasons")
    if not isinstance(reasons, Mapping):
        return NONE
    if reason in reasons:
        return reasons[reason], None
    # Absent from a complete record: none stopped that way.
    return (0, None) if _reasons_complete(reasons, "regimes", None) else NONE


def _regime_minutes_per_nat(report: Mapping[str, Any], strength: Any, repair: float, policy: str) -> Value:
    block = _get(_regime_row(report, strength, repair), "value_of_checks", policy)
    return _get(block, "minutes_per_nat"), _get(block, "minutes_per_nat_ci95")


def _sweep_row(report: Mapping[str, Any], parameter: str, value: float) -> Mapping[str, Any] | None:
    for row in _get(report, "sensitivity", "parameters", parameter, "rows") or []:
        if _number(row.get("value")) == float(value):
            return row
    return None


def _sweep_value(report: Mapping[str, Any], parameter: str, value: float, policy: str,
                 metric: str = "difference") -> Value:
    block = _get(_sweep_row(report, parameter, value), "policies", policy)
    if metric == "difference":
        return _get(block, "difference_vs_current", "mean_difference"), _get(block, "difference_vs_current", "ci95")
    if metric == "tau":
        return _get(block, "ranking_tau_vs_current"), None
    return _get(block, "mean_total_minutes"), _get(block, "total_minutes_ci95")


def _sweep_values(report: Mapping[str, Any], parameter: str) -> list[float]:
    rows = _get(report, "sensitivity", "parameters", parameter, "rows") or []
    return sorted(v for v in (_number(r.get("value")) for r in rows) if v is not None)


def _sweep_current(report: Mapping[str, Any], parameter: str) -> float | None:
    return _number(_get(report, "sensitivity", "parameters", parameter, "current"))


def _part_c(report: Mapping[str, Any], strength: Any, encounters: float, policy: str,
            metric: str = "difference") -> Value:
    for row in _get(report, "part_c", "rows") or []:
        if strength_label(row.get("consistency")) == strength_label(strength) and \
                _number(row.get("encounters")) == float(encounters) and row.get("policy") == policy:
            if metric == "difference":
                return _get(row, "difference", "mean_difference"), _get(row, "difference", "ci95")
            return row.get(metric), None
    return NONE


def _part_c_encounters(report: Mapping[str, Any]) -> list[float]:
    return sorted({v for v in (_number(r.get("encounters")) for r in _get(report, "part_c", "rows") or [])
                   if v is not None})


def _diff(a: Value, b: Value) -> Value:
    x, y = _number(a[0]), _number(b[0])
    return (None if x is None or y is None else round(x - y, 6)), None


def _point(values: Values, label: str) -> float | None:
    return _number(values.get(label, NONE)[0])


def _ci(values: Values, label: str) -> list[float] | None:
    return _interval(values.get(label, NONE)[1])


def _below(values: Values, label: str) -> bool | None:
    ci = _ci(values, label)
    return None if ci is None else ci[1] < 0


def _above(values: Values, label: str) -> bool | None:
    ci = _ci(values, label)
    return None if ci is None else ci[0] > 0


def _spans_zero(values: Values, label: str) -> bool | None:
    ci = _ci(values, label)
    return None if ci is None else ci[0] <= 0 <= ci[1]


def _lt(values: Values, low: str, high: str) -> bool | None:
    x, y = _point(values, low), _point(values, high)
    return None if x is None or y is None else x < y


def _all(verdicts: Sequence[bool | None]) -> bool | None:
    if not verdicts or any(v is None for v in verdicts):
        return None
    return all(verdicts)  # type: ignore[arg-type]


def _any(verdicts: Sequence[bool | None]) -> bool | None:
    if not verdicts or any(v is None for v in verdicts):
        return None
    return any(verdicts)  # type: ignore[arg-type]


def _extreme(values: Values, policy: str, cell: str, *, highest: bool = False) -> bool | None:
    """Strictly the lowest (or highest) of every arm the cell records."""

    scored = {p: _point(values, f"{p} {cell}") for p in P.ALL_POLICIES if f"{p} {cell}" in values}
    if policy not in scored or any(v is None for v in scored.values()):
        return None
    mine = scored[policy]
    others = [v for p, v in scored.items() if p != policy]
    if not others:
        return None
    return all((mine > v) if highest else (mine < v) for v in others)  # type: ignore[operator]


@dataclass(frozen=True)
class Assertion:
    """One condition of a claim, evaluated on its own. ``conclusion``: what the
    claim concludes; ``figure``: a number it states, at the precision stated
    (the quantity's ``label``, which ``part`` of it, and the ``bounds`` it must
    lie in)."""

    id: str
    kind: str
    text: str
    check: Callable[[Values], bool | None]
    label: str | None = None
    part: str = "point"
    bounds: tuple[float, float] | None = None


def conclusion(id: str, text: str, check: Callable[[Values], bool | None]) -> Assertion:
    return Assertion(id, "conclusion", text, check)


def figure(label: str, stated: float, unit: float, *, part: str = "point", low: float | None = None,
           high: float | None = None, said: str | None = None) -> Assertion:
    """A figure the statement gives, within half a unit of its last digit
    (``unit``), or inside [``low``, ``high``] for a figure stated as a range or
    to one significant digit. ``part``: the point estimate, or the CI's ends."""

    lo = stated - unit / 2 if low is None else low
    hi = stated + unit / 2 if high is None else high

    def check(values: Values) -> bool | None:
        if part == "point":
            x = _point(values, label)
        else:
            ci = _ci(values, label)
            x = None if ci is None else ci[0 if part == "low" else 1]
        return None if x is None else lo - SAME <= x <= hi + SAME

    where = {"point": "", "low": " (CI low end)", "high": " (CI high end)"}[part]
    return Assertion(f"{label}{where}", "figure",
                     f"{label}{where} is {said or _g(stated)} as stated: within [{_g(lo)}, {_g(hi)}]", check,
                     label=label, part=part, bounds=(lo, hi))


@dataclass(frozen=True)
class Claim:
    id: str
    statement: str
    where: str
    #: report -> ordered (label, (point, CI)) pairs
    quantities: Callable[[Mapping[str, Any]], list[tuple[str, Value]]]
    assertions: tuple[Assertion, ...]


VALUE_RULES = ("eig", "evsi", "evsi_lcb_only", "evsi_lookahead")
REPAIRS = (3.0, 10.0, 30.0)
#: The EIG path's ``VALUE_PER_NAT_MINUTES`` the claims are about.
VALUE_PER_NAT = 60.0


def _arms(report: Mapping[str, Any], strength: Any, repair: float) -> list[tuple[str, Value]]:
    cell = f"{strength_label(strength)}/{repair:g}"
    return [(f"{p} {cell}", _regime_value(report, strength, repair, p)) for p in P.ALL_POLICIES]


def _s2(report: Mapping[str, Any]) -> list[tuple[str, Value]]:
    out = []
    for repair in REPAIRS:
        out += [(f"{p} fitted/{repair:g}", _regime_value(report, None, repair, p)) for p in ("incumbent",) + VALUE_RULES]
    for repair in REPAIRS:
        out += [(f"{p} checks fitted/{repair:g}", _regime_value(report, None, repair, p, "mean_checks", None))
                for p in VALUE_RULES]
    return out


def _s3(report: Mapping[str, Any]) -> list[tuple[str, Value]]:
    arms = dict(_arms(report, 0.9, 30.0))
    return list(arms.items()) + [
        ("flip abstention cost (evsi - evsi_lcb_only) 0.9/30", _diff(arms["evsi 0.9/30"], arms["evsi_lcb_only 0.9/30"])),
        ("lookahead saving (evsi_lcb_only - evsi_lookahead) 0.9/30",
         _diff(arms["evsi_lcb_only 0.9/30"], arms["evsi_lookahead 0.9/30"])),
        ("lookahead below the incumbent (incumbent - evsi_lookahead) 0.9/30",
         _diff(arms["incumbent 0.9/30"], arms["evsi_lookahead 0.9/30"])),
        ("left against caps_only (evsi_lookahead - caps_only) 0.9/30",
         _diff(arms["evsi_lookahead 0.9/30"], arms["caps_only 0.9/30"])),
        ("left against eig_no_gate (evsi_lookahead - eig_no_gate) 0.9/30",
         _diff(arms["evsi_lookahead 0.9/30"], arms["eig_no_gate 0.9/30"])),
    ]


def _s3f(report: Mapping[str, Any]) -> list[tuple[str, Value]]:
    incumbent, caps = _regime_value(report, 0.9, 30.0, "incumbent"), _regime_value(report, 0.9, 30.0, "caps_only")
    worlds = report.get("flagged_learners_by_world") or {}
    return [("incumbent 0.9/30", incumbent), ("caps_only 0.9/30", caps),
            ("gate cost (incumbent - caps_only) 0.9/30", _diff(incumbent, caps)),
            ("gate stops 0.9/30", _regime_stop(report, 0.9, 30.0, "incumbent", "couldnt_reliably_distinguish")),
            ("gate stops fitted/3", _regime_stop(report, None, 3.0, "incumbent", "couldnt_reliably_distinguish")),
            ("episodes in the 0.9 world", (worlds.get("0.9"), None)),
            ("episodes in the fitted world", (worlds.get("fitted"), None))]


def _s3g(report: Mapping[str, Any]) -> list[tuple[str, Value]]:
    out = [(f"eig_no_gate {strength_label(s)}/{rep:g}", _regime_value(report, s, rep, "eig_no_gate"))
           for s in ("fitted", 0.7, 0.9) for rep in REPAIRS]
    out.append(("eig_no_gate checks fitted/3", _regime_value(report, None, 3.0, "eig_no_gate", "mean_checks", None)))
    return out + _arms(report, "fitted", 3.0) + _arms(report, 0.7, 30.0) + _arms(report, 0.9, 30.0)


NAT = "robust_composition.VALUE_PER_NAT_MINUTES"


def _s4a(report: Mapping[str, Any]) -> list[tuple[str, Value]]:
    out = []
    for value in _sweep_values(report, NAT):
        out.append((f"eig_no_gate total @{value:g}", _sweep_value(report, NAT, value, "eig_no_gate", "total")))
        out.append((f"eig_no_gate delta @{value:g}", _sweep_value(report, NAT, value, "eig_no_gate")))
    for value in _sweep_values(report, NAT):
        out.append((f"eig delta @{value:g}", _sweep_value(report, NAT, value, "eig")))
    return out


def _s4a_best_at_10(values: Values) -> bool | None:
    totals = {label.split("@")[1]: _point(values, label) for label in values if label.startswith("eig_no_gate total @")}
    if "10" not in totals or any(v is None for v in totals.values()):
        return None
    return all(totals["10"] < v for k, v in totals.items() if k != "10")  # type: ignore[operator]


def _s4a_gate_flat(values: Values) -> bool | None:
    points = [_point(values, label) for label in values if label.startswith("eig delta @")]
    if not points or any(p is None for p in points):
        return None
    return max(abs(p) for p in points) <= 0.195 + SAME  # type: ignore[arg-type]


MINUTES_PER_NAT_CELLS = (("fitted", 3.0), (0.9, 3.0), (0.9, 10.0), (0.9, 30.0))


def _s4b(report: Mapping[str, Any]) -> list[tuple[str, Value]]:
    out = []
    for strength, repair in MINUTES_PER_NAT_CELLS:
        for policy in ("incumbent", "caps_only"):
            out.append((f"minutes per nat: {policy} {strength_label(strength)}/{repair:g}",
                        _regime_minutes_per_nat(report, strength, repair, policy)))
    points = [_number(v[0]) for _label, v in out]
    largest = None if not points or None in points else max(points)  # type: ignore[type-var]
    positive = [p for p in points if p is not None and p > 0]
    out.append(("60 / the largest minutes per nat",
                (round(VALUE_PER_NAT / largest, 4) if largest is not None and largest > 0 else None, None)))
    out.append(("60 / the smallest positive minutes per nat",
                (round(VALUE_PER_NAT / min(positive), 4) if positive and None not in points else None, None)))
    abstain = _get(report, "main", "eedi_fitted", "eig", "episodes", "stop_reasons", "abstain")
    episodes = _get(report, "main", "eedi_fitted", "eig", "episodes", "episodes")
    if abstain is None and isinstance(_get(report, "main", "eedi_fitted", "eig", "episodes", "stop_reasons"), Mapping):
        abstain = 0  # the main comparison keeps every stop reason
    share = None if abstain is None or not episodes else round(float(abstain) / float(episodes), 4)
    out.append(("eig agreement-gate abstentions (share of episodes, main eedi_fitted)", (share, None)))
    return out


def _s4b_above_every_ci(values: Values) -> bool | None:
    highs = [_ci(values, label) for label in values if label.startswith("minutes per nat:")]
    if not highs or any(h is None for h in highs):
        return None
    return max(h[1] for h in highs) < VALUE_PER_NAT  # type: ignore[index]


def _sweep_claim(parameter: str, policies: Sequence[str], prefix: str = "",
                 tau: bool = False) -> Callable[[Mapping[str, Any]], list[tuple[str, Value]]]:
    """Each swept value's paired difference against the current value, per arm
    (and, with ``tau``, the first decision's ranking τ against it, read off
    ``evsi``)."""

    def read(report: Mapping[str, Any]) -> list[tuple[str, Value]]:
        current = _sweep_current(report, parameter)
        out = []
        for value in _sweep_values(report, parameter):
            if current is not None and abs(value - current) <= SAME:
                continue
            for policy in policies:
                out.append((f"{prefix}{policy} delta @{value:g}", _sweep_value(report, parameter, value, policy)))
            if tau:
                out.append((f"{prefix}tau @{value:g}", _sweep_value(report, parameter, value, "evsi", "tau")))
        return out
    return read


def _deltas(values: Values, prefix: str = "") -> list[str]:
    return [label for label in values if label.startswith(prefix) and " delta @" in label]


def _no_minutes_effect(values: Values) -> bool | None:
    """Every paired difference is within noise (its CI spans 0) or negligible
    (under 0.05 minutes per episode: EVSI as built at a concentration of 4 or
    10 moves 0.013 with a CI just clear of 0)."""

    verdicts = []
    for label in _deltas(values):
        spans, point = _spans_zero(values, label), _point(values, label)
        verdicts.append(None if spans is None or point is None else (spans or abs(point) < 0.05))
    return _all(verdicts)


def _rankings_move(prefix: str) -> Callable[[Values], bool | None]:
    def check(values: Values) -> bool | None:
        taus = [_point(values, label) for label in values if label.startswith(f"{prefix}tau @")]
        return _any([None if t is None else t < 1.0 - SAME for t in taus])
    return check


SENSITIVITY_ARMS = ("evsi", "evsi_lcb_only", "evsi_lookahead")
QUANTILE = "robust_composition.ROBUST_QUANTILE"
REPAIR_SWEEP = "action_loss.DEFAULT_INTERVENTION_MINUTES (repair minutes)"
CHECK_SWEEP = "check minutes (probe burden; causal selector default 1.5)"


def _s6(report: Mapping[str, Any]) -> list[tuple[str, Value]]:
    out = []
    for strength in ("fitted", 0.9):
        for encounters in _part_c_encounters(report):
            for policy in ("evsi_lcb_only", "evsi_lookahead"):
                out.append((f"{policy} {strength_label(strength)} x{encounters:g}",
                            _part_c(report, strength, encounters, policy)))
    out.append(("true unresolved minutes x12", _part_c(report, 0.9, 12.0, "evsi_lcb_only", "true_unresolved_minutes")))
    return out


def _part_c_cells(values: Values) -> list[tuple[str, str, float]]:
    out = []
    for label in values:
        parts = label.split(" ")
        if len(parts) == 3 and parts[0] in P.ALL_POLICIES and parts[2].startswith("x"):
            out.append((label, parts[1], float(parts[2][1:])))
    return out


def _s6_check(where: Callable[[str, float], bool], verdict: Callable[[Values, str], bool | None],
              ) -> Callable[[Values], bool | None]:
    def check(values: Values) -> bool | None:
        cells = [(label, s, n) for label, s, n in _part_c_cells(values) if where(s, n)]
        return _all([verdict(values, label) for label, _s, _n in cells])
    return check


def _not(predicate: Callable[[Values, str], bool | None]) -> Callable[[Values, str], bool | None]:
    def negated(values: Values, label: str) -> bool | None:
        verdict = predicate(values, label)
        return None if verdict is None else not verdict
    return negated


CLAIMS: tuple[Claim, ...] = (
    Claim("S2", "At Eedi's strength every value rule stops after the opening error and beats today's incumbent "
          "(3.77 vs 1.81 min at repair 3; 7.98 vs 6.03 at 10; 20.03 vs 18.08 at 30)", "Summary 2, §4.2, §4.3", _s2, (
              conclusion("value_rules_stop", "every value rule (eig, evsi, evsi_lcb_only, evsi_lookahead) averages "
                         "at most 0.1 checks per episode at fitted/3, /10 and /30",
                         lambda v: _all([None if _point(v, f"{p} checks fitted/{r:g}") is None
                                         else _point(v, f"{p} checks fitted/{r:g}") <= 0.1 + SAME  # type: ignore[operator]
                                         for p in VALUE_RULES for r in REPAIRS])),
              conclusion("value_rules_beat_incumbent", "every value rule costs fewer minutes per episode than the "
                         "incumbent at fitted/3, /10 and /30",
                         lambda v: _all([_lt(v, f"{p} fitted/{r:g}", f"incumbent fitted/{r:g}")
                                         for p in VALUE_RULES for r in REPAIRS])),
              figure("incumbent fitted/3", 3.77, 0.01), figure("evsi fitted/3", 1.81, 0.01),
              figure("incumbent fitted/10", 7.98, 0.01), figure("evsi fitted/10", 6.03, 0.01),
              figure("incumbent fitted/30", 20.03, 0.01), figure("evsi fitted/30", 18.08, 0.01),
          )),
    Claim("S3a", "Where checks are strong (0.9/30) EVSI as built costs more than the incumbent (17.9 vs 13.3 min)",
          "Summary 3, §4.3", _s3, (
              conclusion("evsi_above_incumbent", "evsi costs more minutes per episode than the incumbent at 0.9/30",
                         lambda v: _lt(v, "incumbent 0.9/30", "evsi 0.9/30")),
              figure("evsi 0.9/30", 17.9, 0.1), figure("incumbent 0.9/30", 13.3, 0.1),
          )),
    Claim("S3b", "... because of the flip abstention: ignoring it saves 5.4 min (12.5)", "Summary 3, §4.3, §5", _s3, (
        conclusion("lcb_only_below_evsi", "evsi_lcb_only (the flip abstention ignored) costs fewer minutes than evsi "
                   "at 0.9/30", lambda v: _lt(v, "evsi_lcb_only 0.9/30", "evsi 0.9/30")),
        figure("flip abstention cost (evsi - evsi_lcb_only) 0.9/30", 5.4, 0.1),
        figure("evsi_lcb_only 0.9/30", 12.5, 0.1),
    )),
    Claim("S3c", "... and of one-step valuation: the 2-3 check lookahead saves another 1.8 (10.8), 2.6 below the "
          "incumbent", "Summary 3, §4.3, §5", _s3, (
              conclusion("lookahead_below_lcb_only", "evsi_lookahead costs fewer minutes than evsi_lcb_only at 0.9/30",
                         lambda v: _lt(v, "evsi_lookahead 0.9/30", "evsi_lcb_only 0.9/30")),
              conclusion("lookahead_below_incumbent", "evsi_lookahead costs fewer minutes than the incumbent at 0.9/30",
                         lambda v: _lt(v, "evsi_lookahead 0.9/30", "incumbent 0.9/30")),
              figure("lookahead saving (evsi_lcb_only - evsi_lookahead) 0.9/30", 1.8, 0.1),
              figure("evsi_lookahead 0.9/30", 10.8, 0.1),
              figure("lookahead below the incumbent (incumbent - evsi_lookahead) 0.9/30", 2.6, 0.1),
          )),
    Claim("S3d", "1.1-1.2 min remain against caps-only and eig_no_gate at 0.9/30 (eig_no_gate the best rule there)",
          "§4.3", _s3, (
              conclusion("caps_only_below_lookahead", "caps_only costs fewer minutes than evsi_lookahead at 0.9/30",
                         lambda v: _lt(v, "caps_only 0.9/30", "evsi_lookahead 0.9/30")),
              conclusion("eig_no_gate_below_lookahead", "eig_no_gate costs fewer minutes than evsi_lookahead at 0.9/30",
                         lambda v: _lt(v, "eig_no_gate 0.9/30", "evsi_lookahead 0.9/30")),
              conclusion("eig_no_gate_best", "eig_no_gate costs strictly the fewest minutes of every arm at 0.9/30",
                         lambda v: _extreme(v, "eig_no_gate", "0.9/30")),
              figure("left against caps_only (evsi_lookahead - caps_only) 0.9/30", 1.15, 0.1, low=1.05, high=1.25,
                     said="1.1-1.2"),
              figure("left against eig_no_gate (evsi_lookahead - eig_no_gate) 0.9/30", 1.15, 0.1, low=1.05, high=1.25,
                     said="1.1-1.2"),
          )),
    Claim("S3e", "The lookahead is the best rule at 0.9/10 (4.99 vs incumbent 5.82, caps-only 5.13)", "Summary 3, §4.3",
          lambda r: _arms(r, 0.9, 10.0), (
              conclusion("lookahead_best", "evsi_lookahead costs strictly the fewest minutes of every arm at 0.9/10",
                         lambda v: _extreme(v, "evsi_lookahead", "0.9/10")),
              figure("evsi_lookahead 0.9/10", 4.99, 0.01), figure("incumbent 0.9/10", 5.82, 0.01),
              figure("caps_only 0.9/10", 5.13, 0.01),
          )),
    Claim("S3f", "Today's robust completion gate costs 3.7 min per episode at 0.9/30 (incumbent 13.3 vs caps-only 9.6) "
          "and ends 190 of 400 episodes at 0.9, 296 at Eedi's strength", "Summary 3, §4.3, §5, §9.3", _s3f, (
              conclusion("gate_costs_minutes", "the incumbent (with the gate) costs more minutes than caps_only "
                         "(without it) at 0.9/30", lambda v: _lt(v, "caps_only 0.9/30", "incumbent 0.9/30")),
              figure("gate cost (incumbent - caps_only) 0.9/30", 3.7, 0.1),
              figure("incumbent 0.9/30", 13.3, 0.1), figure("caps_only 0.9/30", 9.6, 0.1),
              figure("gate stops 0.9/30", 190, 1), figure("gate stops fitted/3", 296, 1),
              figure("episodes in the 0.9 world", 400, 1), figure("episodes in the fitted world", 400, 1),
          )),
    Claim("S3g", "The eig_no_gate arm in every regime (8.44 min at Eedi/3, the worst rule there; the best rule at "
          "0.7/30, 15.45, and at 0.9/30, 9.58)", "§4.2, §4.3", _s3g, (
              conclusion("worst_at_fitted_3", "eig_no_gate costs strictly the most minutes of every arm at fitted/3",
                         lambda v: _extreme(v, "eig_no_gate", "fitted/3", highest=True)),
              conclusion("best_at_07_30", "eig_no_gate costs strictly the fewest minutes of every arm at 0.7/30",
                         lambda v: _extreme(v, "eig_no_gate", "0.7/30")),
              conclusion("best_at_09_30", "eig_no_gate costs strictly the fewest minutes of every arm at 0.9/30",
                         lambda v: _extreme(v, "eig_no_gate", "0.9/30")),
              figure("eig_no_gate fitted/3", 8.44, 0.01), figure("eig_no_gate 0.7/30", 15.45, 0.01),
              figure("eig_no_gate 0.9/30", 9.58, 0.01),
          )),
    Claim("S4a", "VALUE_PER_NAT_MINUTES on the gate-free EIG rule (0.9/10): best at 10 (4.75 min, -1.89 "
          "[-2.26, -1.52] vs 60); with the gate the scale barely matters", "Summary 4, §4.4, §5", _s4a, (
              conclusion("best_at_10", "eig_no_gate's total minutes are strictly lowest at 10 of every swept value",
                         _s4a_best_at_10),
              conclusion("10_beats_60", "eig_no_gate's paired difference at 10 against 60 has its CI below 0",
                         lambda v: _below(v, "eig_no_gate delta @10")),
              conclusion("gate_flat", "with the gate (eig) every paired difference against 60 is at most 0.19 "
                         "minutes in size (§4.4's bound at its precision: |delta| <= 0.195)", _s4a_gate_flat),
              figure("eig_no_gate total @10", 4.75, 0.01), figure("eig_no_gate delta @10", -1.89, 0.01),
              figure("eig_no_gate delta @10", -2.26, 0.01, part="low"),
              figure("eig_no_gate delta @10", -1.52, 0.01, part="high"),
          )),
    Claim("S4b", "60 is 4-500x the measured minutes per nat; the 90% agreement gate abstains in 89% of the EIG "
          "path's episodes", "Summary 4, §4.4", _s4b, (
              conclusion("above_every_ci", "60 is above every measured minutes per nat's 95% CI (incumbent and "
                         "caps_only at fitted/3, 0.9/3, 0.9/10, 0.9/30)", _s4b_above_every_ci),
              conclusion("at_least_4x", "60 is at least 4x every measured minutes per nat (60 / the largest >= 3.5, "
                         "the stated 4 at its precision)",
                         lambda v: None if _point(v, "60 / the largest minutes per nat") is None
                         else _point(v, "60 / the largest minutes per nat") >= 3.5 - SAME),  # type: ignore[operator]
              conclusion("gate_stops_most", "the agreement gate stops most of the EIG path's episodes (abstentions "
                         "over half of them, main eedi_fitted)",
                         lambda v: None if _point(v, "eig agreement-gate abstentions (share of episodes, main "
                                                     "eedi_fitted)") is None
                         else _point(v, "eig agreement-gate abstentions (share of episodes, main eedi_fitted)") > 0.5),
              figure("60 / the largest minutes per nat", 4, 1),
              figure("60 / the smallest positive minutes per nat", 500, 100, low=450, high=550),
              figure("eig agreement-gate abstentions (share of episodes, main eedi_fitted)", 0.89, 0.01, said="89%"),
          )),
    Claim("S5a", "ROBUST_QUANTILE 0.10 -> 0.25 changes minutes within noise (lcb-only -0.10, lookahead -0.15)",
          "Summary 5, §4.4, §5", _sweep_claim(QUANTILE, SENSITIVITY_ARMS), (
              conclusion("within_noise_at_025", "at 0.25 every arm's paired difference against 0.10 has a CI that "
                         "spans 0", lambda v: _all([_spans_zero(v, f"{p} delta @0.25") for p in SENSITIVITY_ARMS])),
              figure("evsi_lcb_only delta @0.25", -0.10, 0.01), figure("evsi_lookahead delta @0.25", -0.15, 0.01),
          )),
    Claim("S5b", "PERTURBATION_DELTA has no minutes effect (|delta| <= 0.03)", "Summary 5, §4.4, §5",
          _sweep_claim("evsi.PERTURBATION_DELTA", SENSITIVITY_ARMS), (
              conclusion("at_most_003", "every arm's paired difference at every swept value is at most 0.03 minutes "
                         "in size (as stated: |delta| <= 0.035)",
                         lambda v: _all([None if _point(v, label) is None else abs(_point(v, label)) <= 0.035 + SAME
                                         for label in _deltas(v)])),
          )),
    Claim("S5c", "INSTRUMENT_PERTURBATION_CONCENTRATION and the draw count move rankings, not minutes", "§4.4, §5",
          lambda r: _sweep_claim("robust_composition.INSTRUMENT_PERTURBATION_CONCENTRATION", SENSITIVITY_ARMS,
                                 "concentration: ", tau=True)(r)
          + _sweep_claim("robust_composition.ROBUST_DRAW_COUNT (simulation draws)", SENSITIVITY_ARMS, "draws: ",
                         tau=True)(r), (
              conclusion("no_minutes_effect", "every paired difference (both parameters, every arm) has a CI that "
                         "spans 0 or is under 0.05 minutes in size", _no_minutes_effect),
              conclusion("concentration_moves_rankings", "some swept concentration's first-decision ranking "
                         "(evsi) has Kendall tau below 1 against the current value", _rankings_move("concentration: ")),
              conclusion("draws_move_rankings", "some swept draw count's first-decision ranking (evsi) has Kendall "
                         "tau below 1 against the current value", _rankings_move("draws: ")),
          )),
    Claim("S5d", "A positive BURDEN_COST only adds minutes", "§4.4, §5",
          _sweep_claim("robust_composition.BURDEN_COST", ("evsi_lcb_only", "evsi_lookahead")), (
              conclusion("never_lowers", "every positive BURDEN_COST's paired difference (evsi_lcb_only, "
                         "evsi_lookahead) is at least 0",
                         lambda v: _all([None if _point(v, label) is None else _point(v, label) >= -SAME
                                         for label in _deltas(v)])),
          )),
    Claim("S5e", "Knowing the true repair minutes (10, not 3) is worth 0.71-1.06 min per episode", "Summary 5, §4.4",
          lambda r: [(f"{p} delta @10", _sweep_value(r, REPAIR_SWEEP, 10.0, p)) for p in ("evsi_lcb_only", "evsi_lookahead")],
          (
              conclusion("both_below", "both paired differences at 10 (evsi_lcb_only, evsi_lookahead) have CIs below 0",
                         lambda v: _all([_below(v, f"{p} delta @10") for p in ("evsi_lcb_only", "evsi_lookahead")])),
              figure("evsi_lcb_only delta @10", -0.71, 0.01), figure("evsi_lookahead delta @10", -1.06, 0.01),
          )),
    Claim("S5f", "The causal default check burden 1.5 over-states a 1-minute check (+0.30, +0.44)", "§4.4, §5",
          lambda r: [(f"{p} delta @1.5", _sweep_value(r, CHECK_SWEEP, 1.5, p)) for p in ("evsi_lcb_only", "evsi_lookahead")],
          (
              conclusion("both_above", "both paired differences at 1.5 (evsi_lcb_only, evsi_lookahead) have CIs "
                         "above 0", lambda v: _all([_above(v, f"{p} delta @1.5")
                                                    for p in ("evsi_lcb_only", "evsi_lookahead")])),
              figure("evsi_lcb_only delta @1.5", 0.30, 0.01), figure("evsi_lookahead delta @1.5", 0.44, 0.01),
          )),
    Claim("S6", "Charging the measured unresolved cost pays off once it reaches about 3.6 min (consistency 0.9) and "
          "costs nothing measurable below", "Summary 6, §4.5, §9.1", _s6, (
              conclusion("never_costs", "no paired difference (measured - minutes-only) has a CI above 0",
                         _s6_check(lambda s, n: True, _not(_above))),
              conclusion("pays_from_12_at_09", "at consistency 0.9, from 12 encounters on, every paired difference "
                         "has a CI below 0", _s6_check(lambda s, n: s == "0.9" and n >= 12, _below)),
              conclusion("nothing_below_12", "under 12 encounters, at either strength, no paired difference has a CI "
                         "below 0", _s6_check(lambda s, n: n < 12, _not(_below))),
              figure("true unresolved minutes x12", 3.6, 0.1, said="about 3.6"),
          )),
)


def compare_claims(old: Mapping[str, Any], new: Mapping[str, Any]) -> list[dict[str, Any]]:
    out = []
    for claim in CLAIMS:
        a, b = claim.quantities(old), claim.quantities(new)
        labels = list(dict.fromkeys([label for label, _v in a] + [label for label, _v in b]))
        a_map, b_map = dict(a), dict(b)
        quantities = [quantity(label, *_pair(a_map.get(label), b_map.get(label))) for label in labels]
        assertions = []
        for assertion in claim.assertions:
            before, after = assertion.check(a_map), assertion.check(b_map)
            assertions.append({"id": assertion.id, "kind": assertion.kind, "text": assertion.text,
                               "holds_old": before, "holds_new": after, "changed": before != after})
        conclusions = [x for x in assertions if x["kind"] == "conclusion"]
        figures = [x for x in assertions if x["kind"] == "figure"]
        holds_old, holds_new = _all([x["holds_old"] for x in conclusions]), _all([x["holds_new"] for x in conclusions])
        out.append({
            "id": claim.id,
            "statement": claim.statement,
            "where": claim.where,
            "status": _worst([q["status"] for q in quantities]),
            "moved": [q["label"] for q in quantities if q["status"] in DIFFERS],
            "beyond_ci": [q["label"] for q in quantities if q["status"] == "moved_beyond_ci"],
            "holds_old": holds_old,
            "holds_new": holds_new,
            "conclusion_changed": holds_old != holds_new,
            "figures_old": _all([x["holds_old"] for x in figures]) if figures else None,
            "figures_new": _all([x["holds_new"] for x in figures]) if figures else None,
            "figures_changed": [x["text"] for x in figures if x["changed"]],
            "assertions": assertions,
            "quantities": quantities,
        })
    return out


def _pair(left: tuple[Any, Any] | None, right: tuple[Any, Any] | None) -> tuple[Any, Any, Any, Any]:
    lv, lc = left if left else (None, None)
    rv, rc = right if right else (None, None)
    return lv, rv, lc, rc


def compare_reports(old: Mapping[str, Any], new: Mapping[str, Any]) -> dict[str, Any]:
    """The whole comparison, in the study's order (see the module docstring)."""

    bound = bound_stops(old, new)
    bounds = _bounds_by_cell(bound) if bound["available"] else None
    rows = compare_cells(old, new, bounds)
    claims = compare_claims(old, new)
    rank_rows = ranks(old, new)
    statuses = [m["status"] for r in rows for m in r["metrics"]]

    def header(report: Mapping[str, Any]) -> dict[str, Any]:
        return {"version": report.get("version"), "simulation_version": report.get("simulation_version"),
                "applied_bound": applied_bound(report),
                "settings": dict(sorted((report.get("settings") or {}).items())),
                "policy_defaults": dict(sorted((report.get("policy_defaults") or {}).items()))}

    assertions = [a for c in claims for a in c["assertions"]]
    return {
        "version": COMPARE_VERSION,
        "old": header(old),
        "new": header(new),
        "not_compared": list(METADATA_KEYS),
        "bound": bound,
        "attribution": attribution(rows) if bounds is not None else {"checked": False, "reason": bound["reason"]},
        "summary": {
            "metrics": {status: statuses.count(status) for status in STATUS_ORDER},
            "rows": {status: sum(1 for r in rows if r["status"] == status) for status in STATUS_ORDER},
            "claims": {status: sum(1 for c in claims if c["status"] == status) for status in STATUS_ORDER},
            "assertions": {kind: {"count": sum(1 for a in assertions if a["kind"] == kind),
                                  "hold_old": sum(1 for a in assertions if a["kind"] == kind and a["holds_old"]),
                                  "hold_new": sum(1 for a in assertions if a["kind"] == kind and a["holds_new"])}
                           for kind in ("conclusion", "figure")},
            "conclusions_changed": [c["id"] for c in claims if c["conclusion_changed"]],
            "figures_changed": [c["id"] for c in claims if c["figures_changed"]],
            "rank_changes": [r["cell"] for r in rank_rows if r["changed"]],
            "winner_changes": [r["cell"] for r in rank_rows if r["winner_changed"]],
        },
        "claims": claims,
        "ranks": rank_rows,
        "cells": rows,
    }


# -- markdown ---------------------------------------------------------------------------------------------------


def _fmt(value: Any) -> str:
    """A stored number as stored (4 places at most), anything else as text."""

    if value is None:
        return "—"
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return str(value)
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _fmt_q(point: Any, ci: list[float] | None) -> str:
    text = _fmt(point)
    return _md(f"{text} [{_fmt(ci[0])}, {_fmt(ci[1])}]" if ci else text)


def _md(text: Any) -> str:
    """Text for a Markdown table cell (a literal ``|`` would split it)."""

    return str(text).replace("|", "\\|")


def render_markdown(comparison: Mapping[str, Any]) -> str:
    """Tables for a review file: bound stops, claims and their assertions, every
    moved value, rank changes."""

    lines: list[str] = []
    bound = comparison["bound"]
    lines += ["### Bound stops (cells where the bound stopped an episode)", ""]
    if not bound["available"] or bound["relation"] != "bounded_vs_unbounded":
        lines += [f"{bound['relation']}: {bound['reason']}", ""]
    else:
        lines += [f"Bound: {bound['reference_bound']} checks.", "",
                  "| Section | Cell | Arm | Episodes | Stopped at the bound | Changed by it (ran past) "
                  "| Max checks unbounded | Stored report says |",
                  "|---|---|---|---:|---:|---:|---:|---|"]
        for row in bound["cells"]:
            if not row["stops"]:
                continue
            cell = _md(", ".join(f"{k} {v}" for k, v in row["cell"].items()))
            recorded = row["recorded_in_bounded_report"]
            lines.append(f"| {row['section']} | {cell} | `{row['policy']}` | {row['episodes']} | {row['stops']} | "
                         f"{row['censored']} | {row['max_checks_unbounded']} | "
                         f"{recorded if recorded is not None else '—'} ({row['check']}) |")
        lines += ["", f"Total: {bound['total_stops']} stops, {bound['total_censored']} changed; cross-checks "
                  f"{bound['checks']}.", ""]
    attributed = comparison["attribution"]
    if attributed.get("checked"):
        lines += [f"Attribution: {attributed['untouched_identical']} of {attributed['untouched_rows']} rows the bound "
                  f"never reached are identical (differing: {attributed['untouched_differing'] or 'none'}); "
                  f"renamed-only rows differing beyond their stop reasons: "
                  f"{attributed['renamed_only_differing'] or 'none'}; changed rows: "
                  f"{attributed['touched_rows'] or 'none'}.", ""]
    else:
        lines += [f"Attribution: not checked ({attributed.get('reason')}).", ""]
    lines += ["### Claims", "",
              "| Claim | Status | Moved | Conclusions old → new | Stated figures old → new |", "|---|---|---|---|---|"]
    for claim in comparison["claims"]:
        moved = "; ".join(
            f"{_md(q['label'])}: {_fmt_q(q['old'], q['old_ci95'])} → {_fmt_q(q['new'], q['new_ci95'])}"
            for q in claim["quantities"] if q["status"] in DIFFERS) or "nothing"
        figures = "none stated" if not any(a["kind"] == "figure" for a in claim["assertions"]) else \
            f"{claim['figures_old']} → {claim['figures_new']}"
        lines.append(f"| `{claim['id']}` | {claim['status']} | {moved} | {claim['holds_old']} → {claim['holds_new']} | "
                     f"{figures} |")
    lines += ["", "### Claim assertions", "", "| Claim | Kind | Checks | Old | New |", "|---|---|---|---|---|"]
    for claim in comparison["claims"]:
        for assertion in claim["assertions"]:
            lines.append(f"| `{claim['id']}` | {assertion['kind']} | {_md(assertion['text'])} | "
                         f"{assertion['holds_old']} | {assertion['holds_new']} |")
    lines += ["", "### Every moved value", "", "| Cell | Arm | Value | Old [95% CI] | New [95% CI] | Status |",
              "|---|---|---|---|---|---|"]
    for row in comparison["cells"]:
        for metric in row["metrics"]:
            if metric["status"] not in DIFFERS:
                continue
            lines.append(f"| {_md(row['cell'])} | `{row['policy']}` | {_md(metric['label'])} | "
                         f"{_fmt_q(metric['old'], metric['old_ci95'])} | {_fmt_q(metric['new'], metric['new_ci95'])} | "
                         f"{metric['status']} |")
    lines += ["", "### Rank changes", ""]
    changed = [r for r in comparison["ranks"] if r["changed"]]
    if not changed:
        lines.append("None: every cell ranks the arms in the same order.")
    for row in changed:
        lines.append(f"* {row['cell']}: {' < '.join(row['old'])} → {' < '.join(row['new'])}")
    return "\n".join(lines) + "\n"


__all__ = ["CLAIMS", "COMPARE_VERSION", "METADATA_KEYS", "Assertion", "applied_bound", "bound_stops",
           "compare_reports", "quantity", "recorded_bound_stops", "render_markdown", "strength_label"]
