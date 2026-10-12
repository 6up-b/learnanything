"""Report 3: the assumption report (learner field §7.3, after F2).

Read-only and aggregate-only: counts and rates per source, never learner text
and never per-LO identities. The first review's outcome is joined from
``practice_attempts`` exactly as serving resolves it (``placement.state``).
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import sqrt
from pathlib import Path
from statistics import median
from typing import Any

from learnloop.algorithm_versions import PLACEMENT_VERSIONS
from learnloop.placement.rules import RULES_VERSION
from learnloop.placement.state import load_placement_state_from_connection, placement_tables_present

REPORT_VERSION = "placement-report-3-v1"
SOURCES = ("self_report", "fast_track", "predictor", "quick_check")
#: The daily-loop spec's flat per-item bound when no duration is known.
DEFAULT_MINUTES_PER_ITEM = 3.0

CONFOUNDS = (
    "Learning and forgetting between the decision and the first review: a miss can mean the "
    "learner forgot, a pass can mean they learned the topic elsewhere in the meantime.",
    "Goal-frontier and requested serving in that window can show the LO's items before its "
    "scheduled check, so some first reviews are early.",
    "A first review is one answer on one item: the miss rate has wide intervals until many "
    "assumptions have resolved.",
    "Grader error: a grader that accepts a wrong answer can fast-track an LO or pass its check "
    "(Slice 1 E1 measures it).",
    "Minutes are estimated from the learner's own answer latencies (or 3 minutes per item), not "
    "measured study time.",
)


def _wilson(failures: int, n: int) -> list[float] | None:
    if not n:
        return None
    p, z = failures / n, 1.959963984540054
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [max(0.0, center - half), min(1.0, center + half)]


def _minutes_per_item(connection: Any) -> tuple[float, str]:
    values = [
        float(row[0]) / 60.0
        for row in connection.execute(
            "SELECT latency_seconds FROM practice_attempts WHERE latency_seconds IS NOT NULL AND latency_seconds > 0"
        ).fetchall()
    ]
    if len(values) >= 5:
        return round(median(values), 3), "median_answer_latency"
    return DEFAULT_MINUTES_PER_ITEM, "flat_3_minutes"


def placement_report(connection: Any, vault: Any) -> dict[str, Any]:
    """Report 3 over one read-only snapshot."""

    version = vault.config.algorithms.algorithm_version
    manifest = {
        "report_version": REPORT_VERSION,
        "rules_version": RULES_VERSION,
        "algorithm_version": version,
        "placement_version": version in PLACEMENT_VERSIONS,
        "placement_config_hash": sha256(json.dumps(
            vault.config.placement.model_dump(mode="json"), sort_keys=True
        ).encode()).hexdigest(),
        "active_predictor": vault.config.field.active_predictor,
    }
    if not placement_tables_present(connection):
        return {"manifest": manifest, "status": "no_placement_tables", "sources": {}, "counts": {}}
    state = load_placement_state_from_connection(connection, active=False)
    returns = connection.execute(
        "SELECT assumption_id FROM assumption_returns ORDER BY created_at, id"
    ).fetchall()
    minutes_per_item, minutes_basis = _minutes_per_item(connection)

    active_items: dict[str, list[str]] = defaultdict(list)
    for item in vault.practice_items.values():
        if item.status == "active" and item.learning_object_id:
            active_items[str(item.learning_object_id)].append(item.id)
    attempted_items = {
        (str(row[0]), str(row[1])): str(row[2])
        for row in connection.execute(
            "SELECT learning_object_id, practice_item_id, MIN(created_at) FROM practice_attempts "
            "WHERE attempt_type NOT IN ('skip','guided_walkthrough') GROUP BY learning_object_id, practice_item_id"
        ).fetchall()
    }

    sources: dict[str, dict[str, Any]] = {}
    for source in SOURCES:
        rows = [a for a in state.assumptions if a.source == source]
        statuses = Counter(a.status for a in rows)
        resolved = statuses["passed"] + statuses["failed"]
        on_schedule = [a for a in rows if a.status in ("passed", "failed") and a.resolved_at >= a.first_review_due]
        early = [a for a in rows if a.status in ("passed", "failed") and a.resolved_at < a.first_review_due]
        skipped = 0
        for assumption in rows:
            until = assumption.resolved_at
            for item_id in active_items.get(assumption.learning_object_id, ()):
                first = attempted_items.get((assumption.learning_object_id, item_id))
                if first is not None and first <= assumption.created_at:
                    continue  # already practised before the assumption
                if first is not None and (until is None or first <= until):
                    continue  # served anyway (the check, or early practice)
                skipped += 1
        sources[source] = {
            "decisions": len(rows),
            "open": statuses["open"],
            "passed": statuses["passed"],
            "failed": statuses["failed"],
            "returned_by_learner": statuses["returned"],
            "first_review_miss_rate": round(statuses["failed"] / resolved, 6) if resolved else None,
            "first_review_miss_rate_wilson_ci95": _wilson(statuses["failed"], resolved),
            "resolved_on_schedule": len(on_schedule),
            "resolved_early": len(early),
            "on_schedule_miss_rate": (
                round(sum(a.status == "failed" for a in on_schedule) / len(on_schedule), 6)
                if on_schedule else None
            ),
            "items_not_served_as_new_material": skipped,
            "learning_minutes_saved_estimate": round(skipped * minutes_per_item, 2),
        }

    # Every LO that started as new material: no answer before placement began.
    placement_started = min((a.created_at for a in state.assumptions), default=None)
    rebuild = connection.execute(
        "SELECT MIN(created_at) FROM derived_state_rebuilds WHERE algorithm_version IN "
        f"({','.join('?' for _ in PLACEMENT_VERSIONS)})",
        tuple(sorted(PLACEMENT_VERSIONS)),
    ).fetchone() if connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='derived_state_rebuilds'"
    ).fetchone() else None
    if rebuild is not None and rebuild[0] is not None:
        placement_started = min(filter(None, (placement_started, str(rebuild[0]))))
    first_answer_by_lo: dict[str, str] = {}
    for (lo, _item), first in attempted_items.items():
        if lo not in first_answer_by_lo or first < first_answer_by_lo[lo]:
            first_answer_by_lo[lo] = first
    new_los = [
        lo for lo, learning_object in vault.learning_objects.items()
        if learning_object.status == "active"
        and (lo not in first_answer_by_lo or (placement_started is not None and first_answer_by_lo[lo] >= placement_started))
    ]
    new_items = sum(len(active_items.get(lo, ())) for lo in new_los)
    saved = sum(values["items_not_served_as_new_material"] for values in sources.values())
    all_resolved = sum(values["passed"] + values["failed"] for values in sources.values())
    all_failed = sum(values["failed"] for values in sources.values())
    return {
        "manifest": manifest,
        "status": "complete",
        "sources": sources,
        "overall": {
            "decisions": len(state.assumptions),
            "open": sum(values["open"] for values in sources.values()),
            "first_review_miss_rate": round(all_failed / all_resolved, 6) if all_resolved else None,
            "first_review_miss_rate_wilson_ci95": _wilson(all_failed, all_resolved),
        },
        "returns_to_learning": {
            "failed_first_reviews": all_failed,
            "i_dont_know_this": len(returns),
            "i_dont_know_this_on_assumed": sum(1 for row in returns if row[0] is not None),
        },
        "learning_minutes": {
            "minutes_per_item": minutes_per_item,
            "minutes_basis": minutes_basis,
            "saved_estimate": round(saved * minutes_per_item, 2),
            "learning_every_new_lo_estimate": round(new_items * minutes_per_item, 2),
            "new_learning_objects": len(new_los),
            "new_material_items": new_items,
            "placement_started_at": placement_started,
        },
        "counts": {
            "assumption_decisions": len(state.assumptions),
            "assumption_returns": len(returns),
        },
        "confounds": list(CONFOUNDS),
        "definitions": {
            "first_review": "The first recorded answer on the LO after the decision.",
            "miss": "That answer is not a clean full-marks answer (the complement of report 2's pass).",
            "returned_by_learner": "\"I don't know this\" before any answer on the LO.",
            "on_schedule": "Resolved at or after the decision's first_review_due.",
        },
    }


def write_placement_report(report: dict[str, Any], output_dir: Path) -> dict[str, str]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, sort_keys=True, indent=2, allow_nan=False)
    digest = sha256(payload.encode()).hexdigest()[:16]
    json_path = directory / f"placement-report-3-{digest}.json"
    markdown_path = directory / f"placement-report-3-{digest}.md"
    json_path.write_text(payload + "\n", encoding="utf-8")
    lines = [
        "# Report 3: assumed known, checked in the first review", "",
        "Aggregates only. No learner text, no per-LO identities.", "",
        "| Source | Decisions | Open | Passed | Failed | Returned | Miss rate | 95% Wilson CI | Minutes saved (est.) |",
        "|---|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for source, values in report.get("sources", {}).items():
        lines.append(
            f"| {source} | {values['decisions']} | {values['open']} | {values['passed']} | "
            f"{values['failed']} | {values['returned_by_learner']} | {values['first_review_miss_rate']} | "
            f"{values['first_review_miss_rate_wilson_ci95']} | {values['learning_minutes_saved_estimate']} |"
        )
    minutes = report.get("learning_minutes", {})
    lines.extend([
        "",
        f"Learning minutes saved (estimate): {minutes.get('saved_estimate')} of "
        f"{minutes.get('learning_every_new_lo_estimate')} for learning every new LO "
        f"({minutes.get('minutes_per_item')} min/item, {minutes.get('minutes_basis')}).",
        "",
        "## Named confounds", "",
        *(f"- {value}" for value in report.get("confounds", ())),
        "", "## Full aggregate report", "", "```json", payload, "```", "",
    ])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(markdown_path)}
