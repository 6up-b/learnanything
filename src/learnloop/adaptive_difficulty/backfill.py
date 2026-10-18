"""AD1's owner-run backfills (spec_adaptive_difficulty_v1 §14 AD1, §7.2, §8.2, §5.11).

``learnloop ad backfill`` (``--dry-run`` first, on a backup copy):

* ``--audit``: the feature audit of every active item's current revision and
  of every other revision held in ``practice_item_snapshots`` (an answered or
  served revision), under ``adaptive_difficulty.daily_spend_cap_usd``;
* ``--llm-v1``: the one-time ``llm_v1:item`` forecast of the never-attempted
  active items that exist now;
* ``--reading``: the reading-opportunity sweep over the whole history (no
  model call).

A dry run opens the database read-only, calls nothing, writes nothing and
prints the plan with its estimate. Protected items (held-out material, exam
reservations) are never audited or forecast (A8).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from contextlib import closing
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.connection import connect

from learnloop.adaptive_difficulty.feature_audit import (
    DIMENSIONS,
    audit_revision,
    audit_state,
    canonical_audits,
    item_revision,
    question_for,
)
from learnloop.adaptive_difficulty.outside import Clients, forecast_item, item_view
from learnloop.adaptive_difficulty.protection import protected_items
from learnloop.adaptive_difficulty.reading import sweep
from learnloop.adaptive_difficulty.switches import (
    LLM_V1,
    feature_audit_enabled,
    outside_forecasters,
    receipts_enabled,
)


def _revisions(vault: Any, connection: Any, protected: frozenset[str]) -> list[tuple[Any, str]]:
    """``(item, content_hash)`` for every active item's current revision and every held snapshot."""

    from learnloop.vault.models import PracticeItem

    seen: set[str] = set()
    revisions: list[tuple[Any, str]] = []
    for item in sorted(vault.practice_items.values(), key=lambda value: value.id):
        if getattr(item, "status", "active") != "active" or item.id in protected:
            continue
        content_hash, _json = item_revision(item)
        if content_hash not in seen:
            seen.add(content_hash)
            revisions.append((item, content_hash))
    for content_hash, item_id, item_json in connection.execute(
        "SELECT content_hash, practice_item_id, item_json FROM practice_item_snapshots ORDER BY created_at, content_hash"
    ):
        if content_hash in seen or str(item_id) in protected:
            continue
        try:
            item = PracticeItem.model_validate_json(item_json)
        except ValueError:
            continue
        # A snapshot audits as the revision it holds, under its stored hash.
        if item_revision(item)[0] != content_hash:
            continue
        seen.add(content_hash)
        revisions.append((item, content_hash))
    return revisions


def _never_attempted(vault: Any, connection: Any, protected: frozenset[str]) -> list[Any]:
    attempted = {str(row[0]) for row in connection.execute("SELECT DISTINCT practice_item_id FROM practice_attempts")}
    return [item for item in sorted(vault.practice_items.values(), key=lambda value: value.id)
            if getattr(item, "status", "active") == "active" and item.id not in attempted and item.id not in protected]


def backfill(vault: Any, repository: Any, *, audit: bool, llm_v1: bool, reading: bool, dry_run: bool,
             limit: int | None = None, clients: Clients | None = None,
             decider_factory: Callable[[], Any] | None = None, clock: Clock | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"dry_run": dry_run}
    protected = protected_items(vault, repository)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        revisions = _revisions(vault, connection, protected) if audit else []
        pending_audits = [(item, content_hash, [d for d in DIMENSIONS if d not in canonical_audits(connection, content_hash)])
                          for item, content_hash in revisions]
        pending_audits = [entry for entry in pending_audits if entry[2]]
        candidates = _never_attempted(vault, connection, protected) if llm_v1 else []
        existing = {str(row[0]) for row in connection.execute(
            "SELECT item_content_hash FROM forecast_receipts WHERE kind = 'item_unassisted_success' AND scope = 'item' "
            "AND forecaster = ? AND status = 'ok'", (LLM_V1,))} if candidates else set()
        pending_v1 = [item for item in candidates if item_revision(item)[0] not in existing]
    if limit is not None:
        pending_audits, pending_v1 = pending_audits[:limit], pending_v1[:limit]
    if audit:
        if not feature_audit_enabled(vault.config):
            result["audit"] = {"status": "disabled", "reason": "adaptive_difficulty.feature_audit is off"}
        else:
            tokens = sum(len(json.dumps({"state": audit_state(item),
                                         "questions": {d: question_for(d).wire() for d in dims}})) // 3 + 512
                         for item, _hash, dims in pending_audits)
            plan = {"revisions": len(pending_audits), "dimensions": sum(len(d) for _i, _h, d in pending_audits),
                    "decider_requests": len(pending_audits), "estimated_decider_input_tokens": tokens,
                    "protected_skipped": len(protected)}
            if dry_run:
                result["audit"] = {"status": "planned", **plan}
            else:
                outcomes = [audit_revision(vault, repository, item, decider_factory=decider_factory,
                                           llm_client=clients.llm if clients else None, clock=clock).as_dict()
                            for item, _hash, _dims in pending_audits]
                result["audit"] = {"status": "done", **plan,
                                   "by_status": _count(outcome.get("status") for outcome in outcomes)}
    if llm_v1:
        if LLM_V1 not in outside_forecasters(vault.config):
            result["llm_v1"] = {"status": "disabled", "reason": "llm_v1:item is not in adaptive_difficulty.outside_forecasters"}
        else:
            tokens = sum(len(json.dumps(item_view(vault, item))) // 3 + 600 for item in pending_v1)
            plan = {"items": len(pending_v1), "calls": len(pending_v1), "estimated_input_tokens": tokens}
            if dry_run:
                result["llm_v1"] = {"status": "planned", **plan}
            else:
                outcomes = [forecast_item(vault, repository, item, clients=clients, clock=clock).as_dict()
                            for item in pending_v1]
                result["llm_v1"] = {"status": "done", **plan,
                                    "by_status": _count(outcome.get("status") for outcome in outcomes)}
    if reading:
        if not receipts_enabled(vault.config):
            result["reading"] = {"status": "disabled", "reason": "adaptive_difficulty.forecast_receipts is off"}
        elif dry_run:
            result["reading"] = {"status": "planned", "model_calls": 0}
        else:
            swept = sweep(vault, repository, as_of=utc_now_iso(clock), sweep_kind="backfill", clock=clock)
            result["reading"] = {"status": "done", **swept.as_dict()}
    return result


def _count(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return dict(sorted(counts.items()))


__all__ = ["backfill"]
