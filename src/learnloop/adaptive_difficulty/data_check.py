"""``learnloop ad data-check`` (spec_adaptive_difficulty_v1 §14 AD1, §3.3, §17 Q1, Q3).

Read-only, on a backup copy: the database is opened read-only, never
migrated, and no model is called. Aggregates only (counts, shares,
correlations), never learner text:

* the §3.3 tables: items by ``difficulty_source``, items with
  ``task_features``, graded attempts (excluding ``self_report``), items
  attempted once / at least twice, the full-credit share, and the first
  unassisted, unprimed attempt per item against its ``difficulty`` label
  (Spearman's rho with a Fisher-z interval, overall, within capability and
  per capability);
* first-surface attempts per (facet, capability) cell;
* coverage of latency, answer confidence, hints, priming, the AD1 rating tap
  and first-hint progress;
* exam-material assessment items with and without a facet mapping (their
  spans cite a learning object), held-out ones counted apart (Q3);
* historical attempts by revision status (``exact``,
  ``reconstructed_current``, ``excluded``: §7.5).
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from contextlib import closing
from typing import Any

from learnloop.db.connection import connect


def _ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    position = 0
    while position < len(order):
        end = position
        while end + 1 < len(order) and values[order[end + 1]] == values[order[position]]:
            end += 1
        average = (position + end) / 2.0 + 1.0
        for index in order[position:end + 1]:
            ranks[index] = average
        position = end + 1
    return ranks


def spearman(xs: list[float], ys: list[float]) -> dict[str, Any]:
    """Spearman's rho with an approximate 95% Fisher-z interval; n < 4 reports no interval."""

    n = len(xs)
    if n < 3:
        return {"n": n, "rho": None, "interval": None}
    rx, ry = _ranks(xs), _ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sxx = sum((a - mx) ** 2 for a in rx)
    syy = sum((b - my) ** 2 for b in ry)
    if sxx <= 0 or syy <= 0:
        return {"n": n, "rho": None, "interval": None}
    rho = sxy / math.sqrt(sxx * syy)
    interval = None
    if n > 3 and abs(rho) < 1:
        z, se = math.atanh(rho), 1.0 / math.sqrt(n - 3)
        interval = [round(math.tanh(z - 1.96 * se), 3), round(math.tanh(z + 1.96 * se), 3)]
    return {"n": n, "rho": round(rho, 3), "interval": interval}


def _has(connection: Any, table: str, column: str | None = None) -> bool:
    row = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
    if row is None:
        return False
    if column is None:
        return True
    return any(info[1] == column for info in connection.execute(f"PRAGMA table_info({table})"))


def data_check(vault: Any, sqlite_path: Any, *, repository: Any = None) -> dict[str, Any]:
    from learnloop.field.outcomes import load_attempt_rows

    items = [item for item in vault.practice_items.values()]
    report: dict[str, Any] = {"items": len(items)}
    report["difficulty_source"] = dict(sorted(Counter(str(item.difficulty_source or "none") for item in items).items()))
    report["items_with_task_features"] = sum(1 for item in items if item.task_features)
    with closing(connect(sqlite_path, read_only=True)) as connection:
        columns = {info[1] for info in connection.execute("PRAGMA table_info(practice_attempts)")}
        select = ["id", "practice_item_id", "attempt_type", "correctness", "hints_used", "primed", "latency_seconds",
                  "answer_confidence", "created_at"]
        select += [name for name in ("difficulty_rating", "first_hint_progress") if name in columns]
        rows = [dict(zip(select, values)) for values in connection.execute(
            f"SELECT {', '.join(select)} FROM practice_attempts WHERE attempt_type NOT IN ('self_report', 'skip') "
            "AND correctness IS NOT NULL ORDER BY created_at, id")]
        per_item = Counter(row["practice_item_id"] for row in rows)
        report["graded_attempts"] = len(rows)
        report["items_attempted_once"] = sum(1 for count in per_item.values() if count == 1)
        report["items_attempted_twice_or_more"] = sum(1 for count in per_item.values() if count >= 2)
        report["full_credit_share"] = (round(sum(1 for row in rows if float(row["correctness"]) >= 0.999) / len(rows), 3)
                                       if rows else None)
        total = len(rows) or 1
        report["coverage"] = {
            "latency": round(sum(1 for row in rows if row["latency_seconds"] is not None) / total, 3),
            "answer_confidence": round(sum(1 for row in rows if row["answer_confidence"] is not None) / total, 3),
            "hints": round(sum(1 for row in rows if int(row["hints_used"] or 0) > 0) / total, 3),
            "primed": round(sum(1 for row in rows if row["primed"]) / total, 3),
            "difficulty_rating": (round(sum(1 for row in rows if row.get("difficulty_rating")) / total, 3)
                                  if "difficulty_rating" in columns else None),
            "first_hint_progress_among_hinted": _share(
                [row for row in rows if int(row["hints_used"] or 0) > 0], "first_hint_progress")
            if "first_hint_progress" in columns else None,
        }
        # §3.3: first unassisted, unprimed attempt per item vs its label.
        first: dict[str, dict[str, Any]] = {}
        for row in rows:
            if row["practice_item_id"] in first or int(row["hints_used"] or 0) > 0 or row["primed"]:
                continue
            first[row["practice_item_id"]] = row
        pairs: dict[str, list[tuple[float, float]]] = defaultdict(list)
        for item_id, row in first.items():
            item = vault.practice_items.get(item_id)
            if item is None or item.difficulty is None:
                continue
            pairs[str(item.capability or "unknown")].append((float(item.difficulty), float(row["correctness"])))
        everything = [pair for values in pairs.values() for pair in values]
        within_x: list[float] = []
        within_y: list[float] = []
        for values in pairs.values():
            if len(values) < 2:
                continue
            mx = sum(x for x, _ in values) / len(values)
            my = sum(y for _, y in values) / len(values)
            within_x += [x - mx for x, _ in values]
            within_y += [y - my for _, y in values]
        report["first_attempt_vs_label"] = {
            "overall": spearman([x for x, _ in everything], [y for _, y in everything]),
            "within_capability_residual": spearman(within_x, within_y),
            "per_capability": {cap: spearman([x for x, _ in values], [y for _, y in values])
                               for cap, values in sorted(pairs.items())},
        }
        attempt_rows = load_attempt_rows(connection, vault)
        report["historical_revision_status"] = dict(sorted(Counter(row.revision_status for row in attempt_rows).items()))
        seen_surfaces: set[str] = set()
        cells: Counter[str] = Counter()
        for row in attempt_rows:
            group = row.surface_group_id or row.features.item_id
            if group in seen_surfaces or row.effective_mass <= 0:
                continue
            seen_surfaces.add(group)
            item = vault.practice_items.get(row.features.item_id)
            capability = row.features.capability or "unknown"
            for facet in (item.evidence_facets if item is not None else []):
                cells[f"{vault.canonical_facet_id(str(facet))}|{capability}"] += 1
        report["first_surface_attempts_per_cell"] = {
            "cells": len(cells), "attempts": sum(cells.values()),
            "distribution": dict(sorted(Counter(min(count, 15) for count in cells.values()).items())),
        }
        report["exam_assessment_items"] = _exam_units(vault, connection, repository)
        if _has(connection, "item_serve_inputs"):
            report["ad1_receipts"] = {
                "item_serve_inputs": connection.execute("SELECT COUNT(*) FROM item_serve_inputs").fetchone()[0],
                "ad_reading_opportunities": connection.execute(
                    "SELECT COUNT(*) FROM ad_reading_opportunities").fetchone()[0],
                "item_forecasts": dict(connection.execute(
                    "SELECT forecaster, COUNT(*) FROM forecast_receipts WHERE kind = 'item_unassisted_success' "
                    "GROUP BY forecaster").fetchall()),
                "feature_audits": connection.execute(
                    "SELECT COUNT(*) FROM judgment_ledger WHERE task = 'ad_feature_audit'").fetchone()[0],
            }
    return report


def _share(rows: list[dict[str, Any]], key: str) -> float | None:
    if not rows:
        return None
    return round(sum(1 for row in rows if row.get(key)) / len(rows), 3)


def _exam_units(vault: Any, connection: Any, repository: Any) -> dict[str, Any]:
    if repository is None or not _has(connection, "source_unit_inventories"):
        return {"available": False}
    from learnloop.content.sources.exam_material import exam_material
    from learnloop.reader.reader_progression import learning_objects_for_span

    try:
        material = exam_material(vault, repository)
    except Exception:  # noqa: BLE001 - a report never fails on its optional section
        return {"available": False}
    counts = Counter()
    for extraction_id, inventory_json in connection.execute(
        "SELECT extraction_id, inventory_json FROM source_unit_inventories"
    ):
        try:
            inventory = json.loads(inventory_json or "{}")
        except (TypeError, ValueError):
            continue
        for signal in inventory.get("assessment_signals") or []:
            spans = [str(span) for span in signal.get("span_ids") or []]
            if not spans or not any(material.covers(str(extraction_id), span) for span in spans):
                continue
            held = bool(signal.get("held_out"))
            mapped = any(learning_objects_for_span(vault, repository, extraction_id=str(extraction_id), span_id=span)
                         for span in spans)
            counts[("held_out" if held else "practice_available", "mapped" if mapped else "unmapped")] += 1
    return {"available": True, **{f"{scope}_{mapping}": count for (scope, mapping), count in sorted(counts.items())}}


__all__ = ["data_check", "spearman"]
