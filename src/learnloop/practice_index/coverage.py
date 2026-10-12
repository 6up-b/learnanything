"""Coverage: facets with few admissible items become Phase 5a generation targets.

A facet is covered by the items that declare it (canonical ids) and pass the
scheduler's admission rules right now. Facets below
``practice_index.coverage_min_eligible`` are targets, fewest first. The report
is a read: it calls no model and writes nothing.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.practice_index.catalog import facet_items, facet_label, registered_facets
from learnloop.practice_index.admission import PracticeAdmission
from learnloop.vault.models import LoadedVault


@dataclass(frozen=True)
class CoverageTarget:
    facet_id: str
    label: str
    learning_object_ids: tuple[str, ...]
    eligible_items: int
    tagged_items: int
    deficit: int

    def as_dict(self) -> dict[str, Any]:
        values = asdict(self)
        values["learning_object_ids"] = list(self.learning_object_ids)
        return values


def coverage_targets(vault: LoadedVault, repository: Repository, *,
                     min_eligible: int | None = None,
                     clock: Clock | None = None) -> list[CoverageTarget]:
    """Facets with fewer admissible items than the threshold, fewest first."""
    return _coverage(vault, repository, min_eligible=min_eligible, clock=clock)[0]


def coverage_report(vault: LoadedVault, repository: Repository, *,
                    min_eligible: int | None = None,
                    clock: Clock | None = None) -> dict[str, Any]:
    """Aggregate coverage: targets, counts and per-facet eligibility."""
    return _coverage(vault, repository, min_eligible=min_eligible, clock=clock)[1]


def _coverage(vault: LoadedVault, repository: Repository, *, min_eligible: int | None,
              clock: Clock | None) -> tuple[list[CoverageTarget], dict[str, Any]]:
    threshold = vault.config.practice_index.coverage_min_eligible if min_eligible is None else min_eligible
    if threshold < 0:
        raise ValueError("min_eligible must be nonnegative")
    admission = PracticeAdmission.load(vault, repository, clock=clock)
    live = [item for item in vault.practice_items.values() if item.status != "retired"]
    admitted, _excluded = admission.admit(vault, sorted(item.id for item in live))
    admitted_set = set(admitted)
    tagged = facet_items(vault, live)
    facets = registered_facets(vault)
    targets: list[CoverageTarget] = []
    rows: list[dict[str, Any]] = []
    for facet_id, facet in facets.items():
        ids = tagged.get(facet_id, [])
        eligible = [item_id for item_id in ids if item_id in admitted_set]
        learning_objects = tuple(sorted({vault.practice_items[i].learning_object_id for i in ids}))
        rows.append({"facet_id": facet_id, "eligible_items": len(eligible), "tagged_items": len(ids)})
        if len(eligible) < threshold:
            targets.append(CoverageTarget(
                facet_id=facet_id, label=facet_label(facet), learning_object_ids=learning_objects,
                eligible_items=len(eligible), tagged_items=len(ids),
                deficit=threshold - len(eligible),
            ))
    targets.sort(key=lambda target: (target.eligible_items, -target.deficit, target.facet_id))
    unregistered = sorted({
        facet_id for facet_id in tagged if facet_id not in facets
    })
    untagged_items = sum(1 for item_id in admitted_set if not any(
        item_id in tagged.get(facet_id, []) for facet_id in facets
    ))
    return targets, {
        "min_eligible": threshold,
        "facets": len(facets),
        "admissible_items": len(admitted_set),
        "targets": [target.as_dict() for target in targets],
        "covered_facets": len(facets) - len(targets),
        "unregistered_facet_ids": unregistered,
        "admissible_items_without_registered_facet": untagged_items,
        "per_facet": rows,
    }


__all__ = ["CoverageTarget", "coverage_report", "coverage_targets"]
