"""Adaptive hints H1: the approach-map rows of ``learnloop hints report`` (spec §10, H1's "data it starts").

Maps for served items, validation failures by reason, route counts by origin,
what built each version, and the model calls and today's spend against
``hints.maps.max_daily_cost_usd``, so the owner sees what build-on-serve costs.
Read-only (a read-only connection; the database is never migrated), no model
call, no learner text. The report reads the stored rows whatever
``hints.maps.enabled`` says (it is the owner's view of what exists; no hint or
serving path reads a map while the switch is off) and says which way it is set.
"""

from __future__ import annotations

from collections import Counter
from contextlib import closing
import json
from pathlib import Path
from typing import Any

from learnloop.clock import Clock
from learnloop.db.connection import connect
from learnloop.db.stores import approach_maps as store
from learnloop.hints.map_builder import LEDGER_TASK, OWNER_KIND, maps_spend_today
from learnloop.hints.map_seeds import item_revision
from learnloop.hints.maps import REASONS, route_counts
from learnloop.vault.models import LoadedVault


def _table(connection: Any, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def build_maps_report(vault: LoadedVault, sqlite_path: Path, *, clock: Clock | None = None) -> dict[str, Any]:
    maps_config = vault.config.hints.maps
    report: dict[str, Any] = {
        "enabled": maps_config.enabled, "build_on_serve": maps_config.build_on_serve,
        "max_daily_cost_usd": float(maps_config.max_daily_cost_usd),
        "price_per_million": vault.config.hints.price_per_million,
    }
    with closing(connect(sqlite_path, read_only=True)) as connection:
        rows = store.all_maps(connection)
        active = {item_id: item for item_id, item in vault.practice_items.items() if item.status == "active"}
        current: dict[str, dict[str, Any]] = {}
        latest: dict[str, dict[str, Any]] = {}
        for row in rows:
            latest[row["practice_item_id"]] = row
        for item_id, row in latest.items():
            item = active.get(item_id)
            if item is None:
                continue
            item_hash, structure = item_revision(vault, connection, item)
            match = store.current_map(connection, item_id, practice_item_hash=item_hash, structure_hash=structure)
            if match is not None:
                current[item_id] = match
        served = set()
        if _table(connection, "practice_attempts"):
            served = {str(row[0]) for row in connection.execute("SELECT DISTINCT practice_item_id FROM practice_attempts")}
        served &= set(active)
        verdicts: Counter[str] = Counter()
        reasons: Counter[str] = Counter()
        not_stored: Counter[str] = Counter()
        if _table(connection, "judgment_ledger"):
            for right_kind, verdict, rationale in connection.execute(
                    "SELECT right_kind, verdict, rationale FROM judgment_ledger WHERE task = ?", (LEDGER_TASK,)):
                kind = "merge" if right_kind == "approach_map_merge" else "build"
                verdicts[f"{kind}:{verdict}"] += 1
                if verdict != "valid":
                    try:
                        listed = json.loads(rationale or "{}").get("reasons") or []
                    except ValueError:
                        listed = []
                    reasons.update(str(reason) for reason in listed)
                if verdict == "invalid_not_stored":
                    not_stored[kind] += 1
        receipts = {"calls": 0, "reported_cost_usd": 0.0, "input_tokens": 0, "output_tokens": 0}
        if _table(connection, "model_call_receipts"):
            for cost, input_tokens, output_tokens in connection.execute(
                    "SELECT cost, input_tokens, output_tokens FROM model_call_receipts "
                    "WHERE owner_kind = ? AND parent_call_id IS NULL", (OWNER_KIND,)):
                receipts["calls"] += 1
                receipts["reported_cost_usd"] += float(cost or 0.0)
                receipts["input_tokens"] += int(input_tokens or 0)
                receipts["output_tokens"] += int(output_tokens or 0)
        spend = maps_spend_today(vault, connection, clock=clock)
    origins: Counter[str] = Counter()
    for row in current.values():
        origins.update(route_counts(row["map"]))
    report.update({
        "versions_stored": len(rows),
        "items_with_a_map": len(latest),
        "current_maps": len(current),
        "verified_goal": sum(1 for row in current.values() if row["verified_goal"]),
        "versions_by_trigger": dict(sorted(Counter(row["trigger"] for row in rows).items())),
        "served_items": {
            "basis": "active items with at least one practice attempt",
            "count": len(served), "with_current_map": len(served & set(current)),
            "without_map": len(served - set(current)),
        },
        "validation": {
            "verdicts": dict(sorted(verdicts.items())),
            "failures_by_reason": {reason: reasons.get(reason, 0) for reason in REASONS if reasons.get(reason)},
            "not_stored": dict(sorted(not_stored.items())),
        },
        "routes_by_origin": dict(sorted(origins.items())),
        "routes_per_current_map": (round(sum(origins.values()) / len(current), 3) if current else None),
        "model_calls": receipts,
        "spend_today": spend,
    })
    return report


__all__ = ["build_maps_report"]
