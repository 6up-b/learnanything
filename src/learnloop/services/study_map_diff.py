"""Study-map diff after an applied append (source-ingestion §10.5).

Deterministic, LLM-free: computed from the accepted patch + entity_source_links
deltas against a pre-append snapshot. Reports what the append actually changed —
new facets/links/conflicts, blueprint/task-distribution shift, stale links repaired
— so the Update-study-map review surface can show the concrete effect.
"""

from __future__ import annotations

from typing import Any

from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault


def compute_study_map_diff(
    repository: Repository,
    vault_after: LoadedVault,
    before: dict[str, Any],
    patch_id: str | None = None,
) -> dict[str, Any]:
    """Diff the study map after an applied append against a pre-append snapshot.

    ``before`` is the snapshot captured before acceptance:
    ``{facets: set[str], links: int, open_conflicts: int, stale_links: int,
    notations: int}``.
    """

    after_facets = set(vault_after.evidence_facets.keys())
    before_facets = set(before.get("facets") or set())
    with repository.connection() as connection:
        after_links = int(connection.execute("SELECT COUNT(*) AS n FROM entity_source_links").fetchone()["n"])
    after_open_conflicts = len(repository.source_conflicts_by_status("open"))
    after_stale = len(repository.stale_entity_source_links())
    after_notations = len(repository.all_notation_mappings())

    diff: dict[str, Any] = {
        "new_facets": sorted(after_facets - before_facets),
        "removed_facets": sorted(before_facets - after_facets),
        "new_links": max(0, after_links - int(before.get("links", 0))),
        "new_conflicts": max(0, after_open_conflicts - int(before.get("open_conflicts", 0))),
        "new_notations": max(0, after_notations - int(before.get("notations", 0))),
        "stale_links_repaired": max(0, int(before.get("stale_links", 0)) - after_stale),
        "blueprint_distribution_shift": _blueprint_shift(repository, patch_id),
    }
    diff["has_changes"] = bool(
        diff["new_facets"]
        or diff["removed_facets"]
        or diff["new_links"]
        or diff["new_conflicts"]
        or diff["new_notations"]
        or diff["stale_links_repaired"]
        or diff["blueprint_distribution_shift"]
    )
    return diff


def _blueprint_shift(repository: Repository, patch_id: str | None) -> list[dict[str, Any]]:
    """Blueprint/task-distribution changes introduced by this append's patch items."""

    if patch_id is None:
        return []
    shifts: list[dict[str, Any]] = []
    for item in repository.proposal_items(patch_id):
        if item["item_type"] != "task_blueprint":
            continue
        payload = item.get("edited_payload") or item["payload"]
        if not isinstance(payload, dict):
            continue
        shifts.append(
            {
                "blueprint_id": payload.get("id"),
                "learning_object_id": payload.get("learning_object_id"),
                "weight": payload.get("weight"),
                "operation": item["operation"],
            }
        )
    return shifts
