from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import (
    read_markdown_with_frontmatter,
    read_yaml,
    write_markdown_with_frontmatter,
    write_yaml,
)


class ConceptMergeError(ValueError):
    pass


@dataclass(frozen=True)
class ConceptMergeResult:
    canonical_id: str
    duplicate_id: str
    dry_run: bool
    changed_files: list[str] = field(default_factory=list)
    change_batch_id: str | None = None
    content_event_count: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "canonical_id": self.canonical_id,
            "duplicate_id": self.duplicate_id,
            "dry_run": self.dry_run,
            "changed_files": self.changed_files,
            "change_batch_id": self.change_batch_id,
            "content_event_count": self.content_event_count,
        }


def merge_concepts(
    root: Path,
    canonical_id: str,
    duplicate_id: str,
    *,
    add_alias: bool = True,
    dry_run: bool = False,
    force: bool = False,
    clock: Clock | None = None,
) -> ConceptMergeResult:
    vault = load_vault(root)
    if canonical_id == duplicate_id:
        raise ConceptMergeError("canonical and duplicate concept ids must differ")
    canonical = vault.concepts.get(canonical_id)
    duplicate = vault.concepts.get(duplicate_id)
    if canonical is None:
        raise ConceptMergeError(f"unknown canonical concept {canonical_id!r}")
    if duplicate is None:
        raise ConceptMergeError(f"unknown duplicate concept {duplicate_id!r}")
    if canonical.type != duplicate.type and not force:
        raise ConceptMergeError(
            f"concept type mismatch: {canonical_id}={canonical.type}, {duplicate_id}={duplicate.type}; pass --force"
        )
    canonical_description = (canonical.description or "").strip()
    duplicate_description = (duplicate.description or "").strip()
    if (
        canonical_description
        and duplicate_description
        and canonical_description != duplicate_description
        and not force
    ):
        raise ConceptMergeError("concept descriptions differ; pass --force to keep the canonical description")

    paths = VaultPaths(vault.root, vault.config)
    changed_files: set[str] = set()
    now = utc_now_iso(clock)

    _merge_concepts_file(
        paths.concepts_path,
        canonical_id,
        duplicate_id,
        add_alias=add_alias,
        clock_iso=now,
        changed_files=changed_files,
        dry_run=dry_run,
    )
    _rewrite_relations_file(paths.relations_path, canonical_id, duplicate_id, changed_files, dry_run=dry_run)
    _rewrite_goals_file(paths.goals_path, canonical_id, duplicate_id, changed_files, dry_run=dry_run, clock_iso=now)
    _rewrite_error_types_file(paths.error_types_path, canonical_id, duplicate_id, changed_files, dry_run=dry_run, clock_iso=now)
    for graph_path in sorted((vault.root / "subjects").glob("*/concept-graph.yaml")):
        _rewrite_subject_graph_file(graph_path, canonical_id, duplicate_id, changed_files, dry_run=dry_run)
    for lo_path in sorted((vault.root / "subjects").glob("*/learning-objects/*.yaml")):
        _rewrite_learning_object_file(lo_path, canonical_id, duplicate_id, changed_files, dry_run=dry_run, clock_iso=now)
    for note_path in sorted((vault.root / "subjects").glob("*/notes/*.md")):
        _rewrite_note_file(note_path, canonical_id, duplicate_id, changed_files, dry_run=dry_run, clock_iso=now)

    change_batch_id = None
    content_event_count = 0
    if not dry_run:
        repository = Repository(paths.sqlite_path)
        _rewrite_pending_proposal_refs(repository, canonical_id, duplicate_id, clock_iso=now)
        refreshed = load_vault(vault.root)
        sync_vault_state(refreshed, repository, clock=clock)
        change_batch_id = _record_concept_merge_events(
            repository,
            canonical_id,
            duplicate_id,
            clock_iso=now,
        )
        content_event_count = 2

    return ConceptMergeResult(
        canonical_id=canonical_id,
        duplicate_id=duplicate_id,
        dry_run=dry_run,
        changed_files=sorted(_relative(vault.root, path) for path in changed_files),
        change_batch_id=change_batch_id,
        content_event_count=content_event_count,
    )


def _merge_concepts_file(
    path: Path,
    canonical_id: str,
    duplicate_id: str,
    *,
    add_alias: bool,
    clock_iso: str,
    changed_files: set[str],
    dry_run: bool,
) -> None:
    data = read_yaml(path)
    concepts = data.get("concepts")
    if not isinstance(concepts, dict):
        raise ConceptMergeError("concepts/concepts.yaml must contain a concepts mapping")
    canonical = dict(concepts[canonical_id])
    duplicate = dict(concepts[duplicate_id])
    aliases = _unique_strings(canonical.get("aliases") or [])
    if add_alias:
        aliases = _unique_strings(
            [
                *aliases,
                duplicate_id,
                duplicate.get("title"),
                *(duplicate.get("aliases") or []),
            ],
            exclude={canonical_id, canonical.get("title")},
        )
    canonical["aliases"] = aliases
    canonical["tags"] = _unique_strings([*(canonical.get("tags") or []), *(duplicate.get("tags") or [])])
    if not canonical.get("description") and duplicate.get("description"):
        canonical["description"] = duplicate["description"]
    canonical["updated_at"] = clock_iso
    concepts[canonical_id] = canonical
    del concepts[duplicate_id]
    _write_yaml_if_changed(path, data, changed_files, dry_run=dry_run)


def _rewrite_relations_file(
    path: Path,
    canonical_id: str,
    duplicate_id: str,
    changed_files: set[str],
    *,
    dry_run: bool,
) -> None:
    data = read_yaml(path)
    edges = data.get("edges", [])
    if not isinstance(edges, list):
        raise ConceptMergeError("concepts/relations.yaml must contain an edges list")
    changed = False
    rewritten: list[dict[str, Any]] = []
    by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for raw in edges:
        if not isinstance(raw, dict):
            rewritten.append(raw)
            continue
        edge = dict(raw)
        source = _rewrite_value(edge.get("source"), canonical_id, duplicate_id)
        target = _rewrite_value(edge.get("target"), canonical_id, duplicate_id)
        if source != edge.get("source") or target != edge.get("target"):
            changed = True
        edge["source"] = source
        edge["target"] = target
        if edge.get("source") == edge.get("target"):
            changed = True
            continue
        key = (str(edge.get("source")), str(edge.get("target")), str(edge.get("relation_type")))
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = edge
            rewritten.append(edge)
            continue
        changed = True
        if float(edge.get("strength") or 0) > float(existing.get("strength") or 0):
            existing["strength"] = edge.get("strength")
        if not existing.get("rationale") and edge.get("rationale"):
            existing["rationale"] = edge.get("rationale")
    data["edges"] = rewritten
    _write_yaml_if_changed(path, data, changed_files, dry_run=dry_run, force_changed=changed)


def _rewrite_goals_file(
    path: Path,
    canonical_id: str,
    duplicate_id: str,
    changed_files: set[str],
    *,
    dry_run: bool,
    clock_iso: str,
) -> None:
    data = read_yaml(path)
    changed = False
    for goal in data.get("goals", []):
        if not isinstance(goal, dict):
            continue
        # Legacy v1 goals key concepts under concept_anchors; v2 under
        # facet_scope.concepts. Rewrite whichever form the file uses.
        anchors = goal.get("concept_anchors")
        if isinstance(anchors, list):
            rewritten = _rewrite_list(anchors, canonical_id, duplicate_id)
            if rewritten != anchors:
                goal["concept_anchors"] = rewritten
                goal["updated_at"] = clock_iso
                changed = True
        scope = goal.get("facet_scope")
        if isinstance(scope, dict) and isinstance(scope.get("concepts"), list):
            rewritten = _rewrite_list(scope["concepts"], canonical_id, duplicate_id)
            if rewritten != scope["concepts"]:
                scope["concepts"] = rewritten
                goal["updated_at"] = clock_iso
                changed = True
    _write_yaml_if_changed(path, data, changed_files, dry_run=dry_run, force_changed=changed)


def _rewrite_error_types_file(
    path: Path,
    canonical_id: str,
    duplicate_id: str,
    changed_files: set[str],
    *,
    dry_run: bool,
    clock_iso: str,
) -> None:
    data = read_yaml(path)
    changed = False
    for error_type in data.get("error_types", []):
        if not isinstance(error_type, dict):
            continue
        related = error_type.get("related_concepts")
        if isinstance(related, list):
            rewritten = _rewrite_list(related, canonical_id, duplicate_id)
            if rewritten != related:
                error_type["related_concepts"] = rewritten
                error_type["updated_at"] = clock_iso
                changed = True
    _write_yaml_if_changed(path, data, changed_files, dry_run=dry_run, force_changed=changed)


def _rewrite_subject_graph_file(
    path: Path,
    canonical_id: str,
    duplicate_id: str,
    changed_files: set[str],
    *,
    dry_run: bool,
) -> None:
    data = read_yaml(path)
    changed = False
    for key in ["additional_concepts_in_scope", "exclude_concepts", "subject_ordering_hints"]:
        values = data.get(key)
        if not isinstance(values, list):
            continue
        rewritten = _rewrite_list(values, canonical_id, duplicate_id)
        if rewritten != values:
            data[key] = rewritten
            changed = True
    _write_yaml_if_changed(path, data, changed_files, dry_run=dry_run, force_changed=changed)


def _rewrite_learning_object_file(
    path: Path,
    canonical_id: str,
    duplicate_id: str,
    changed_files: set[str],
    *,
    dry_run: bool,
    clock_iso: str,
) -> None:
    data = read_yaml(path)
    changed = False
    if data.get("concept") == duplicate_id:
        data["concept"] = canonical_id
        changed = True
    for key in ["prerequisites", "confusables"]:
        values = data.get(key)
        if not isinstance(values, list):
            continue
        rewritten = _rewrite_list(values, canonical_id, duplicate_id)
        if rewritten != values:
            data[key] = rewritten
            changed = True
    if changed:
        data["updated_at"] = clock_iso
    _write_yaml_if_changed(path, data, changed_files, dry_run=dry_run, force_changed=changed)


def _rewrite_note_file(
    path: Path,
    canonical_id: str,
    duplicate_id: str,
    changed_files: set[str],
    *,
    dry_run: bool,
    clock_iso: str,
) -> None:
    metadata, body = read_markdown_with_frontmatter(path)
    related = metadata.get("related_concepts")
    if not isinstance(related, list):
        return
    rewritten = _rewrite_list(related, canonical_id, duplicate_id)
    if rewritten == related:
        return
    metadata["related_concepts"] = rewritten
    metadata["updated_at"] = clock_iso
    changed_files.add(str(path))
    if not dry_run:
        write_markdown_with_frontmatter(path, metadata, body)


def _rewrite_pending_proposal_refs(
    repository: Repository,
    canonical_id: str,
    duplicate_id: str,
    *,
    clock_iso: str,
) -> None:
    with repository.connection() as connection:
        rows = connection.execute(
            """
            SELECT id, target_entity_type, target_entity_id, payload_json, edited_payload_json
            FROM proposed_patch_items
            WHERE decision = 'pending'
            """
        ).fetchall()
        for row in rows:
            original_payload = json.loads(row["payload_json"])
            payload = _rewrite_proposal_payload(original_payload, canonical_id, duplicate_id)
            original_edited = json.loads(row["edited_payload_json"]) if row["edited_payload_json"] is not None else None
            edited = (
                _rewrite_proposal_payload(original_edited, canonical_id, duplicate_id)
                if original_edited is not None
                else None
            )
            target_entity_id = _rewrite_value(row["target_entity_id"], canonical_id, duplicate_id)
            if payload == original_payload and edited == original_edited and target_entity_id == row["target_entity_id"]:
                continue
            connection.execute(
                """
                UPDATE proposed_patch_items
                SET target_entity_id = ?, payload_json = ?, edited_payload_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    target_entity_id,
                    json.dumps(payload, sort_keys=True),
                    json.dumps(edited, sort_keys=True) if edited is not None else None,
                    clock_iso,
                    row["id"],
                ),
            )
        connection.commit()


def _rewrite_proposal_payload(payload: Any, canonical_id: str, duplicate_id: str) -> Any:
    if not isinstance(payload, dict):
        return payload
    rewritten = dict(payload)
    for key in ["concept", "concept_id", "source_concept_id", "target_concept_id"]:
        if key in rewritten:
            rewritten[key] = _rewrite_value(rewritten[key], canonical_id, duplicate_id)
    for key in ["related_concepts", "prerequisites", "confusables"]:
        if isinstance(rewritten.get(key), list):
            rewritten[key] = _rewrite_list(rewritten[key], canonical_id, duplicate_id)
    return rewritten


def _record_concept_merge_events(
    repository: Repository,
    canonical_id: str,
    duplicate_id: str,
    *,
    clock_iso: str,
) -> str:
    change_batch_id = new_ulid()
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO change_batches(id, proposed_patch_item_id, reason, origin, summary, created_at)
            VALUES (?, NULL, 'manual_edit', 'learner', ?, ?)
            """,
            (change_batch_id, f"merge concept {duplicate_id} into {canonical_id}", clock_iso),
        )
        for event_type, entity_id, summary in [
            ("updated", canonical_id, f"merge alias concept {duplicate_id} into {canonical_id}"),
            ("deactivated", duplicate_id, f"concept {duplicate_id} merged into {canonical_id}"),
        ]:
            connection.execute(
                """
                INSERT INTO content_events(
                  id, change_batch_id, event_type, subject, entity_type,
                  entity_id, origin, review_status, summary, created_at
                )
                VALUES (?, ?, ?, NULL, 'concept', ?, 'learner', 'accepted', ?, ?)
                """,
                (new_ulid(), change_batch_id, event_type, entity_id, summary, clock_iso),
            )
        connection.commit()
    return change_batch_id


def _write_yaml_if_changed(
    path: Path,
    data: dict[str, Any],
    changed_files: set[str],
    *,
    dry_run: bool,
    force_changed: bool = True,
) -> None:
    if not force_changed:
        return
    changed_files.add(str(path))
    if not dry_run:
        write_yaml(path, data)


def _rewrite_value(value: Any, canonical_id: str, duplicate_id: str) -> Any:
    return canonical_id if value == duplicate_id else value


def _rewrite_list(values: list[Any], canonical_id: str, duplicate_id: str) -> list[Any]:
    return _unique_strings(_rewrite_value(value, canonical_id, duplicate_id) for value in values)


def _unique_strings(values: Any, *, exclude: set[Any] | None = None) -> list[str]:
    excluded = {str(value) for value in (exclude or set()) if value is not None}
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value)
        if not text or text in excluded or text in seen:
            continue
        seen.add(text)
        output.append(text)
    return output


def _relative(root: Path, path: str) -> str:
    try:
        return Path(path).resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path
