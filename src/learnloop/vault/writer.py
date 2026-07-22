from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from learnloop.clock import Clock, utc_now_iso
from learnloop.vault.loader import load_vault
from learnloop.vault.facet_fingerprint import semantic_fingerprint
from learnloop.vault.models import (
    Concept,
    ConceptEdge,
    ErrorType,
    EvidenceFacet,
    LearningObject,
    PracticeItem,
    SourceSet,
)
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml


class VaultWriterError(ValueError):
    pass


CONCEPT_ORDER = [
    "id",
    "title",
    "type",
    "aliases",
    "description",
    "tags",
    "created_at",
    "updated_at",
]
EDGE_ORDER = [
    "id",
    "relation_type",
    "source",
    "target",
    "strength",
    "rationale",
    "created_at",
    "updated_at",
]
LEARNING_OBJECT_ORDER = [
    "schema_version",
    "id",
    "title",
    "subjects",
    "concept",
    "knowledge_type",
    "status",
    "contradicts",
    "summary",
    "prerequisites",
    "confusables",
    "blueprints",
    "difficulty_prior",
    "difficulty_source",
    "tags",
    "provenance",
    "created_at",
    "updated_at",
]
PRACTICE_ITEM_ORDER = [
    "schema_version",
    "id",
    "learning_object_id",
    "subjects",
    "practice_mode",
    "attempt_types_allowed",
    "evidence_facets",
    "evidence_weights",
    "criterion_facet_weights",
    "prompt",
    "expected_answer",
    "difficulty",
    "difficulty_source",
    "retrieval_demand",
    "transfer_distance",
    "scaffold_level",
    "surface_family",
    "repair_targets",
    "tags",
    "hints",
    "hint_policy",
    "grading_rubric",
    "status",
    "status_reason",
    "provenance",
    "created_at",
    "updated_at",
]
ERROR_TYPE_ORDER = [
    "id",
    "title",
    "description",
    "related_concepts",
    "severity_default",
    "is_misconception",
    "tags",
    "created_at",
    "updated_at",
]


def upsert_concept(
    root: Path,
    concept_id: str,
    payload: Concept | dict[str, Any],
    *,
    clock: Clock | None = None,
) -> Path:
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    data = _read_yaml_or(paths.concepts_path, {"schema_version": 1, "concepts": {}})
    concepts = data.setdefault("concepts", {})
    if not isinstance(concepts, dict):
        raise VaultWriterError("concepts/concepts.yaml must contain a concepts mapping")
    existing = _mapping(concepts.get(concept_id))
    raw = _payload(payload)
    if raw.get("id") not in (None, concept_id):
        raise VaultWriterError(f"Concept payload id {raw['id']} does not match {concept_id}")
    raw["id"] = concept_id if raw.get("id") is not None else None
    merged = _merge_entity(existing, raw, CONCEPT_ORDER, clock=clock)
    if merged.get("id") is None:
        merged.pop("id", None)
    concepts[concept_id] = Concept.model_validate(merged).model_dump(mode="json", exclude_none=False)
    if concepts[concept_id].get("id") is None:
        concepts[concept_id].pop("id", None)
    write_yaml(paths.concepts_path, data)
    return paths.concepts_path


def delete_concept(root: Path, concept_id: str) -> Path | None:
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    data = _read_yaml_or(paths.concepts_path, {"schema_version": 1, "concepts": {}})
    concepts = data.setdefault("concepts", {})
    if not isinstance(concepts, dict):
        raise VaultWriterError("concepts/concepts.yaml must contain a concepts mapping")
    if concept_id not in concepts:
        return None
    concepts.pop(concept_id)
    write_yaml(paths.concepts_path, data)
    return paths.concepts_path


def upsert_concept_edge(
    root: Path,
    payload: ConceptEdge | dict[str, Any],
    *,
    clock: Clock | None = None,
) -> Path:
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    data = _read_yaml_or(paths.relations_path, {"schema_version": 1, "edges": []})
    edges = data.setdefault("edges", [])
    if not isinstance(edges, list):
        raise VaultWriterError("concepts/relations.yaml must contain an edges list")
    raw = _payload(payload)
    edge_id = str(raw.get("id") or "")
    if not edge_id:
        raise VaultWriterError("Concept edge id is required")
    index = _list_index_by_id(edges, edge_id)
    existing = _mapping(edges[index]) if index is not None else {}
    merged = _merge_entity(existing, raw, EDGE_ORDER, clock=clock)
    validated = ConceptEdge.model_validate(merged).model_dump(mode="json", exclude_none=False)
    if index is None:
        edges.append(validated)
    else:
        edges[index] = validated
    write_yaml(paths.relations_path, data)
    return paths.relations_path


def delete_concept_edge(root: Path, edge_id: str) -> Path | None:
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    data = _read_yaml_or(paths.relations_path, {"schema_version": 1, "edges": []})
    edges = data.setdefault("edges", [])
    if not isinstance(edges, list):
        raise VaultWriterError("concepts/relations.yaml must contain an edges list")
    index = _list_index_by_id(edges, edge_id)
    if index is None:
        return None
    edges.pop(index)
    write_yaml(paths.relations_path, data)
    return paths.relations_path


def upsert_learning_object(
    root: Path,
    payload: LearningObject | dict[str, Any],
    *,
    clock: Clock | None = None,
) -> Path:
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    raw = _payload(payload)
    learning_object_id = str(raw.get("id") or "")
    if not learning_object_id:
        raise VaultWriterError("Learning Object id is required")
    subjects = raw.get("subjects") or []
    if not subjects:
        raise VaultWriterError("Learning Object subjects must include a primary subject")
    primary_subject = subjects[0]
    if primary_subject not in vault.subjects:
        raise VaultWriterError(f"Unknown primary subject {primary_subject}")
    target_path = paths.learning_object_path(primary_subject, learning_object_id)
    current_path = _locate_entity_path(vault.root, "learning-objects", learning_object_id)
    if current_path is not None and current_path.resolve() != target_path.resolve():
        raise VaultWriterError(f"Refusing to move {learning_object_id} from {current_path} to {target_path}")
    existing = _read_yaml_or(target_path, {})
    merged = _merge_entity(existing, raw, LEARNING_OBJECT_ORDER, clock=clock)
    validated = LearningObject.model_validate(merged).model_dump(mode="json", exclude_none=False)
    _ensure_subject_path(paths, primary_subject, target_path)
    write_yaml(target_path, validated)
    return target_path


def upsert_practice_item(
    root: Path,
    payload: PracticeItem | dict[str, Any],
    *,
    clock: Clock | None = None,
) -> Path:
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    raw = _payload(payload)
    practice_item_id = str(raw.get("id") or "")
    if not practice_item_id:
        raise VaultWriterError("Practice Item id is required")
    learning_object_id = raw.get("learning_object_id")
    learning_object = vault.learning_objects.get(str(learning_object_id))
    if learning_object is None:
        raise VaultWriterError(f"Unknown Learning Object {learning_object_id}")
    subjects = raw.get("subjects")
    subject_list = subjects if subjects is not None else learning_object.subjects
    if not subject_list:
        raise VaultWriterError("Practice Item requires a primary subject through subjects or Learning Object")
    primary_subject = subject_list[0]
    if primary_subject not in vault.subjects:
        raise VaultWriterError(f"Unknown primary subject {primary_subject}")
    target_path = paths.practice_item_path(primary_subject, practice_item_id)
    current_path = _locate_entity_path(vault.root, "practice-items", practice_item_id)
    if current_path is not None and current_path.resolve() != target_path.resolve():
        raise VaultWriterError(f"Refusing to move {practice_item_id} from {current_path} to {target_path}")
    existing = _read_yaml_or(target_path, {})
    merged = _merge_entity(existing, raw, PRACTICE_ITEM_ORDER, clock=clock)
    validated = PracticeItem.model_validate(merged).model_dump(mode="json", exclude_none=False)
    _ensure_subject_path(paths, primary_subject, target_path)
    write_yaml(target_path, validated)
    return target_path


def upsert_error_type(
    root: Path,
    payload: ErrorType | dict[str, Any],
    *,
    clock: Clock | None = None,
) -> Path:
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    data = _read_yaml_or(paths.error_types_path, {"schema_version": 1, "error_types": []})
    error_types = data.setdefault("error_types", [])
    if not isinstance(error_types, list):
        raise VaultWriterError("errors/error_types.yaml must contain an error_types list")
    raw = _payload(payload)
    error_type_id = str(raw.get("id") or "")
    if not error_type_id:
        raise VaultWriterError("Error type id is required")
    index = _list_index_by_id(error_types, error_type_id)
    existing = _mapping(error_types[index]) if index is not None else {}
    merged = _merge_entity(existing, raw, ERROR_TYPE_ORDER, clock=clock)
    validated = ErrorType.model_validate(merged).model_dump(mode="json", exclude_none=False)
    if index is None:
        error_types.append(validated)
    else:
        error_types[index] = validated
    write_yaml(paths.error_types_path, data)
    return paths.error_types_path


FACET_ORDER = [
    "id",
    "concept_id",
    "kind",
    "claim",
    "preconditions",
    "postconditions",
    "applicability",
    "positive_examples",
    "negative_examples",
    "non_goals",
    "error_signatures",
    "instructional_repairs",
    "aliases",
    "status",
    "version",
    "semantic_fingerprint",
    "provenance",
]


def upsert_facet(
    root: Path,
    payload: EvidenceFacet | dict[str, Any],
    *,
    clock: Clock | None = None,
) -> Path:
    """Create or update a canonical facet in facets.yaml (knowledge-model §3.2).

    Facets are the semantic registry entries source-set synthesis mints. The
    write validates through the EvidenceFacet model and (re)computes the
    deterministic ``semantic_fingerprint`` from the normalized contract so cross-
    vault reuse proposals stay stable. The file is written at schema_version 2."""

    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    data = _read_yaml_or(paths.facets_path, {"schema_version": 2, "facets": []})
    if int(data.get("schema_version") or 0) < 2:
        data["schema_version"] = 2
    facets = data.setdefault("facets", [])
    if not isinstance(facets, list):
        raise VaultWriterError("facets.yaml must contain a facets list")
    raw = _payload(payload)
    facet_id = str(raw.get("id") or "")
    if not facet_id:
        raise VaultWriterError("Facet id is required")
    index = _list_index_by_id(facets, facet_id)
    existing = _mapping(facets[index]) if index is not None else {}
    merged_source = {**existing, **raw}
    ordered: dict[str, Any] = {}
    for key in FACET_ORDER:
        if key in merged_source:
            ordered[key] = merged_source[key]
    for key, value in merged_source.items():
        if key not in ordered:
            ordered[key] = value
    validated = EvidenceFacet.model_validate(ordered)
    fingerprint = semantic_fingerprint(validated)
    dumped = validated.model_dump(mode="json", exclude_none=False)
    dumped["semantic_fingerprint"] = fingerprint
    if index is None:
        facets.append(dumped)
    else:
        facets[index] = dumped
    write_yaml(paths.facets_path, data)
    return paths.facets_path


SOURCE_SET_ORDER = [
    "id",
    "subject_id",
    "title",
    "members",
    "priority",
    "created_at",
    "updated_at",
]


def upsert_source_set(
    root: Path,
    payload: SourceSet | dict[str, Any],
    *,
    clock: Clock | None = None,
) -> Path:
    """Create or update a source set in sources/source_sets.yaml (§4.3).

    Membership owns role/scope/priority — this is the one source of truth. The
    write is validated through the SourceSet model and round-trips untouched
    records."""

    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    data = _read_yaml_or(paths.source_sets_path, {"schema_version": 1, "source_sets": []})
    source_sets = data.setdefault("source_sets", [])
    if not isinstance(source_sets, list):
        raise VaultWriterError("sources/source_sets.yaml must contain a source_sets list")
    raw = _payload(payload)
    set_id = str(raw.get("id") or "")
    if not set_id:
        raise VaultWriterError("Source set id is required")
    index = _list_index_by_id(source_sets, set_id)
    existing = _mapping(source_sets[index]) if index is not None else {}
    merged = _merge_entity(existing, raw, SOURCE_SET_ORDER, clock=clock)
    validated = SourceSet.model_validate(merged).model_dump(mode="json", exclude_none=False)
    if index is None:
        source_sets.append(validated)
    else:
        source_sets[index] = validated
    paths.source_sets_path.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(paths.source_sets_path, data)
    return paths.source_sets_path


def _payload(value: BaseModel | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=False)
    return dict(value)


def _mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise VaultWriterError("Expected YAML entity mapping")
    return dict(value)


def _read_yaml_or(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    return read_yaml(path)


def _merge_entity(
    existing: dict[str, Any],
    incoming: dict[str, Any],
    order: list[str],
    *,
    clock: Clock | None,
) -> dict[str, Any]:
    now = utc_now_iso(clock)
    created_at = existing.get("created_at") or incoming.get("created_at") or now
    merged_source = {**existing, **incoming, "created_at": created_at, "updated_at": now}
    ordered: dict[str, Any] = {}
    for key in order:
        if key in merged_source:
            ordered[key] = merged_source[key]
    for source in (existing, incoming):
        for key, value in source.items():
            if key not in ordered:
                ordered[key] = value
    return ordered


def _list_index_by_id(items: list[Any], entity_id: str) -> int | None:
    for index, item in enumerate(items):
        if isinstance(item, dict) and item.get("id") == entity_id:
            return index
    return None


def _locate_entity_path(root: Path, folder: str, entity_id: str) -> Path | None:
    matches = sorted((root / "subjects").glob(f"*/{folder}/{entity_id}.yaml"))
    return matches[0] if matches else None


def _ensure_subject_path(paths: VaultPaths, subject_id: str, target_path: Path) -> None:
    subject_root = paths.subject_dir(subject_id).resolve()
    resolved = target_path.resolve()
    if subject_root not in (resolved, *resolved.parents):
        raise VaultWriterError(f"Refusing to write outside subject {subject_id}: {target_path}")
    target_path.parent.mkdir(parents=True, exist_ok=True)
