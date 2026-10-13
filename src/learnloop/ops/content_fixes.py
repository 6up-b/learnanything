"""``learnloop doctor --fix-content``: repair vault content doctor can fix safely.

One repair today: practice-item criteria whose ``depends_on`` names something
other than a sibling criterion of the same item (doctor
``criterion:unknown_dependency``). Study-map synthesis copied the model's
``depends_on`` verbatim until 2026-10-13, and models often wrote facet or
blueprint ids there. Grading treats a dependency that names no criterion as
passed, so those entries never gated anything; removing them changes no grade
and no evidence. Each edited item's ``rubric_content_hash`` changes, so its
next presentation snapshots a new assessment-contract version; attempts
already graded keep the contract they were graded against.

The edit is a YAML round trip of one ``grading_rubric.criteria[*].depends_on``
list per item, under the vault mutation lock, written through a staged,
fsynced temp file and an atomic rename. A file that does not parse is
reported and left alone, and so is one whose rewritten text would not read
back as the same item with only those lists changed.
"""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
from typing import Any

from learnloop.content.proposals.apply_protocol import materialize_targets
from learnloop.vault.yaml_io import read_yaml, yaml_to_string
from learnloop.vault_lock import vault_mutation_lock

FIX = "criterion_dependencies"


def _sibling_filter(criteria: list[Any]) -> list[dict[str, Any]]:
    """Per-criterion ``{criterion_id, removed, kept}`` for criteria that change."""

    siblings = {str(criterion.get("id") or "") for criterion in criteria if isinstance(criterion, dict)} - {""}
    changes: list[dict[str, Any]] = []
    for criterion in criteria:
        if not isinstance(criterion, dict):
            continue
        own = str(criterion.get("id") or "")
        current = [str(dep) for dep in criterion.get("depends_on") or []]
        kept: list[str] = []
        removed: list[str] = []
        for dep in current:
            if dep in siblings and dep != own:
                if dep not in kept:
                    kept.append(dep)
            elif dep not in removed:
                removed.append(dep)
        if removed:
            changes.append({"criterion_id": own, "removed": removed, "kept": kept})
    return changes


def _plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _plain(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_plain(child) for child in value]
    return value


def fix_criterion_dependencies(root: Path, *, dry_run: bool = True) -> dict[str, Any]:
    """Remove criterion ``depends_on`` entries that name no sibling criterion.

    ``dry_run`` (the default) lists every edit and writes nothing. Returns a
    JSON-safe report: the items and criteria changed, the entries removed,
    and the files it could not read or would not rewrite.
    """

    root = Path(root).resolve()
    report: dict[str, Any] = {
        "fix": FIX,
        "dry_run": dry_run,
        "items_changed": 0,
        "criteria_changed": 0,
        "entries_removed": 0,
        "changes": [],
        "unreadable": [],
        "not_rewritten": [],
        "note": (
            "Grading already treated these entries as passed, so no grade or evidence changes. "
            "Each edited item's rubric_content_hash changes: its next presentation snapshots a new "
            "assessment-contract version, and graded attempts keep the contract they were graded against."
        ),
    }

    def plan() -> list[tuple[Path, Any, dict[str, Any]]]:
        planned: list[tuple[Path, Any, dict[str, Any]]] = []
        for path in sorted((root / "subjects").glob("*/practice-items/*.yaml")):
            try:
                data = read_yaml(path)
            except Exception as exc:  # noqa: BLE001 - reported, never fixed here
                report["unreadable"].append({"path": str(path), "error": str(exc).splitlines()[0]})
                continue
            rubric = data.get("grading_rubric") if isinstance(data, dict) else None
            criteria = rubric.get("criteria") if isinstance(rubric, dict) else None
            if not isinstance(criteria, list):
                continue
            changes = _sibling_filter(criteria)
            if not changes:
                continue
            planned.append((path, data, {
                "practice_item_id": str(data.get("id") or path.stem),
                "path": str(path),
                "criteria": changes,
            }))
        return planned

    def rewrite(path: Path, data: Any, change: dict[str, Any]) -> str | None:
        """The new file text, or None when it would not read back as intended."""

        expected = _plain(data)
        by_id = {entry["criterion_id"]: entry["kept"] for entry in change["criteria"]}
        for criterion in data["grading_rubric"]["criteria"]:
            if isinstance(criterion, dict) and str(criterion.get("id") or "") in by_id:
                criterion["depends_on"] = list(by_id[str(criterion.get("id") or "")])
        for criterion in expected["grading_rubric"]["criteria"]:
            if isinstance(criterion, dict) and str(criterion.get("id") or "") in by_id:
                criterion["depends_on"] = list(by_id[str(criterion.get("id") or "")])
        text = yaml_to_string(data)
        # Read the new text back outside the vault (a reader must never see it).
        with tempfile.TemporaryDirectory(prefix="learnloop-fix-content-") as scratch:
            probe = Path(scratch) / path.name
            try:
                probe.write_text(text, encoding="utf-8")
                reread = _plain(read_yaml(probe))
            except Exception:  # noqa: BLE001 - an unsafe rewrite is skipped and reported
                return None
        return text if reread == expected else None

    def record(change: dict[str, Any]) -> None:
        report["changes"].append(change)
        report["items_changed"] += 1
        report["criteria_changed"] += len(change["criteria"])
        report["entries_removed"] += sum(len(entry["removed"]) for entry in change["criteria"])

    if dry_run:
        for _path, _data, change in plan():
            record(change)
        return report

    with vault_mutation_lock(root, purpose="doctor_fix_content"):
        for path, data, change in plan():
            text = rewrite(path, data, change)
            if text is None:
                report["not_rewritten"].append({
                    "path": str(path),
                    "reason": "the rewritten YAML would not read back as the same item; edit it by hand",
                })
                continue
            materialize_targets(root, [{
                "rel_path": str(path.relative_to(root)),
                "post_content": text,
                "post_hash": "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest(),
            }])
            record(change)
    return report


__all__ = ["FIX", "fix_criterion_dependencies"]
