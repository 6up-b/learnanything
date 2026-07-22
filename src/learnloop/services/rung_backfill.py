"""Depth-rung metadata backfill for legacy practice items.

Bootstrap-era items predate the rung machinery and carry no
``capability``/``task_features``, so waypoint resolution (rung variants,
generation targeting) falls back to the practice-mode heuristic — which cannot
see prompt semantics (a "design the whole workflow" short_answer item reads as
interpretation). This pass LLM-classifies each unstamped active item into the
closed vocabularies, admits each entry through the deterministic validators
(capability vocab, p1_launch task-feature schema, coordination⇒whole_task), and
stamps the vault YAML in place. Classification is annotation of what the item
already is — content, rubric, evidence, and scheduling state are untouched, so
no fork and no reimport.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.activity_patterns import (
    LEGACY_UNMAPPED,
    ensure_builtin_task_feature_schema,
    ensure_capability_alias_registry,
    map_capability,
    validate_task_features,
)
from learnloop.services.depth_rungs import TASK_FEATURE_SCHEMA_SLUG


class RungBackfillError(ValueError):
    pass


def backfill_item_rungs(
    root: Path,
    repository: Repository,
    client: Any,
    *,
    subject: str | None = None,
    dry_run: bool = False,
    batch_size: int = 40,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Classify + stamp rung metadata on active items that lack it.

    Returns ``{stamped: [...], skipped: [{id, reason}], unclassified: [...]}``.
    ``dry_run`` reports what would be stamped without writing.
    """

    import json

    from learnloop.codex.client import RungBackfillContext
    from learnloop.vault.loader import load_vault
    from learnloop.vault.writer import upsert_practice_item

    run = getattr(client, "run_rung_backfill", None)
    if run is None:
        raise RungBackfillError("provider does not implement run_rung_backfill")

    vault = load_vault(root)
    ensure_capability_alias_registry(repository)
    schema_version_id = ensure_builtin_task_feature_schema(repository)
    schema_row = repository.task_feature_schema_version(schema_version_id) or {}
    schema_dims = json.loads(schema_row.get("dimensions_json") or "{}")

    targets = [
        item
        for item in sorted(vault.practice_items.values(), key=lambda i: i.id)
        if item.status == "active"
        and (not item.capability or not item.task_features)
        and (subject is None or subject in vault.subjects_for_item(item))
    ]
    if not targets:
        return {"stamped": [], "skipped": [], "unclassified": []}

    def _excerpt(value: Any, limit: int) -> str:
        text = value if isinstance(value, str) else json.dumps(value, default=str)
        return (text or "")[:limit]

    stamped: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    classified_ids: set[str] = set()

    for start in range(0, len(targets), batch_size):
        batch = targets[start : start + batch_size]
        context = RungBackfillContext(
            items=[
                {
                    "practice_item_id": item.id,
                    "practice_mode": item.practice_mode,
                    "prompt_excerpt": _excerpt(item.prompt, 400),
                    "expected_answer_excerpt": _excerpt(item.expected_answer, 250),
                    "retrieval_demand": item.retrieval_demand,
                    "transfer_distance": item.transfer_distance,
                    "scaffold_level": item.scaffold_level,
                }
                for item in batch
            ],
            task_feature_schema=schema_dims,
        )
        result = run(context)
        by_id = {item.id: item for item in batch}
        for entry in result.items:
            item = by_id.get(entry.practice_item_id)
            if item is None or entry.practice_item_id in classified_ids:
                continue
            classified_ids.add(entry.practice_item_id)
            capability = map_capability(repository, str(entry.capability or ""))
            if capability == LEGACY_UNMAPPED:
                skipped.append({"id": item.id, "reason": f"unknown capability {entry.capability!r}"})
                continue
            features = (
                entry.task_features.model_dump(exclude_none=True)
                if entry.task_features is not None
                else {}
            )
            if not features:
                skipped.append({"id": item.id, "reason": "no task_features returned"})
                continue
            ok, errors = validate_task_features(repository, schema_version_id, features)
            if not ok:
                skipped.append({"id": item.id, "reason": "; ".join(errors)})
                continue
            if capability == "coordination" and features.get("span") != "whole_task":
                skipped.append({"id": item.id, "reason": "coordination requires span=whole_task"})
                continue
            record = {"id": item.id, "capability": capability, "task_features": features}
            stamped.append(record)
            if not dry_run:
                data = item.model_dump(mode="json", exclude_none=False)
                data["capability"] = capability
                data["task_features"] = features
                data["task_feature_schema"] = TASK_FEATURE_SCHEMA_SLUG
                upsert_practice_item(root, data, clock=clock)

    unclassified = [item.id for item in targets if item.id not in classified_ids]
    return {"stamped": stamped, "skipped": skipped, "unclassified": unclassified}
