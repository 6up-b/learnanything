"""What a copy of a practice item keeps of its source's location, so the exam classifier sees it.

A "Keep as practice" copy of an administered probe (``diagnosis.probe_remint``) is a mechanical copy of its content.
Whether an item was made from exam or held-out material is read from two of its fields
(``content.sources.exam_material.item_source_keys``): its canonical exercise and its provenance source refs. A copy that
kept the content but not those would read as unprotected, so protecting the passage later would not protect the copy.
:func:`source_locators` is what a copy keeps; :func:`copies_missing_locators` and :func:`repair_copy_locators` find and
repair copies made before they kept it (``learnloop doctor``, ``doctor --fix-state``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from learnloop.clock import Clock
from learnloop.vault.models import LoadedVault, PracticeItem
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_practice_item
from learnloop.vault.yaml_io import read_yaml

#: The provenance origin of a "Keep as practice" copy (``diagnosis.probe_remint``).
REMINT_ORIGIN = "probe_remint"


def source_locators(source: PracticeItem) -> dict[str, Any]:
    """The source item's own locators a copy keeps: its canonical exercise (``canonical_exercise``) and its provenance
    source refs (``source_refs``), the two fields ``exam_material.item_source_keys`` reads to tell whether an item was
    made from exam or held-out material. A copy that kept the content but not these would read as unprotected."""

    canonical = getattr(source, "canonical_exercise", None)
    refs = getattr(getattr(source, "provenance", None), "source_refs", None) or ()
    return {
        **({"canonical_exercise": canonical.model_dump(mode="json", exclude_none=True)} if canonical is not None else {}),
        "source_refs": [ref.model_dump(mode="json", exclude_none=True) for ref in refs],
    }


def copies_missing_locators(vault: LoadedVault) -> list[tuple[PracticeItem, PracticeItem]]:
    """``(remint, its source)`` for each remint made before copies kept their source's locators
    (:func:`source_locators`): the source names a canonical exercise or source refs the remint lacks, so the exam
    classifier cannot see that the copy was made from the same passage. ``learnloop doctor`` names them, and
    ``doctor --fix-state`` copies the locators in (:func:`repair_copy_locators`)."""

    found = []
    for item in vault.practice_items.values():
        if item.provenance.origin != REMINT_ORIGIN:
            continue
        source_id = next((ref.ref_id for ref in item.provenance.source_refs if ref.ref_type == "existing_entity"),
                         None)
        source = vault.practice_items.get(str(source_id)) if source_id else None
        if source is None:
            continue
        wanted = source_locators(source)
        held = [ref.model_dump(mode="json", exclude_none=True) for ref in item.provenance.source_refs]
        lacks_exercise = "canonical_exercise" in wanted and item.canonical_exercise is None
        if lacks_exercise or any(ref not in held for ref in wanted["source_refs"]):
            found.append((item, source))
    return found


def repair_copy_locators(root: Path, vault: LoadedVault, *, clock: Clock | None = None) -> list[str]:
    """Copy each older remint's missing source locators in (:func:`remint_missing_locators`); returns the repaired
    remint ids. Nothing else of the remint changes."""

    repaired = []
    for item, source in copies_missing_locators(vault):
        path = next(VaultPaths(vault.root, vault.config).root.rglob(f"{item.id}.yaml"), None)
        if path is None:
            continue
        payload = read_yaml(path)
        wanted = source_locators(source)
        if item.canonical_exercise is None and "canonical_exercise" in wanted:
            payload["canonical_exercise"] = wanted["canonical_exercise"]
        provenance = dict(payload.get("provenance") or {})
        held = [ref.model_dump(mode="json", exclude_none=True) for ref in item.provenance.source_refs]
        refs = list(provenance.get("source_refs") or [])
        refs.extend(ref for ref in wanted["source_refs"] if ref not in held)
        provenance["source_refs"] = refs
        payload["provenance"] = provenance
        upsert_practice_item(root, payload, clock=clock, loaded_vault=vault)
        repaired.append(item.id)
    return repaired


__all__ = ["REMINT_ORIGIN", "copies_missing_locators", "repair_copy_locators", "source_locators"]
