from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from learnloop.clock import Clock, utc_now_iso
from learnloop.config import load_config
from learnloop.vault.loader import load_practice_item_file, load_vault
from learnloop.vault.facet_fingerprint import semantic_fingerprint
from learnloop.vault.models import (
    ActivityFamily,
    Concept,
    ConceptEdge,
    ErrorType,
    EvidenceFacet,
    LearningObject,
    LoadedVault,
    PracticeItem,
    SourceSet,
)
from learnloop.vault.paths import VaultPaths
from learnloop.vault.scope_seal import scope_seal
from learnloop.vault.yaml_io import read_yaml, write_yaml
from learnloop.vault_lock import vault_mutation_lock


class VaultWriterError(ValueError):
    pass


def upsert_activity_family(root: Path, family: ActivityFamily) -> Path:
    """Write authored family content; identity/history syncing belongs to substrate."""
    vault = load_vault(root)
    lo = vault.learning_objects.get(family.learning_object_id)
    if lo is None or not lo.subjects:
        raise VaultWriterError("Family requires an existing subject-owned learning object")
    if not family.id or Path(family.id).name != family.id or family.id in {".", ".."}:
        raise VaultWriterError("Family id must be a single safe path component")
    paths = VaultPaths(vault.root, vault.config)
    path = paths.activity_family_path(lo.subjects[0], family.id)
    _ensure_subject_path(paths, lo.subjects[0], path)
    write_yaml(path, family.model_dump(mode="json"))
    return path


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
    "trace_contract",
    "variant_contract",
    "teach_back_source",
    # Meas §3.A2-§3.A5 instrument contracts. Placed before `prompt` because they
    # are what the item IS, not decoration on it: an error-hunt's worked solution
    # and a laddered stem's stimulus are read together with the prompt, and a
    # contrast pair is unreadable without its counterpart id in view.
    "laddered_stem",
    "error_hunt",
    "contrast_of",
    "differing_component",
    "discrimination_profiles",
    "prompt",
    "expected_answer",
    "difficulty",
    "difficulty_source",
    "retrieval_demand",
    "transfer_distance",
    "scaffold_level",
    "capability",
    "task_features",
    "task_feature_schema",
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
    paths = _vault_paths(root)
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
    paths = _vault_paths(root)
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
    paths = _vault_paths(root)
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
    paths = _vault_paths(root)
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
    loaded_vault: LoadedVault | None = None,
) -> Path:
    # Interactive mutations already hold the sidecar's validated vault snapshot.
    # Reusing it avoids reparsing every vault file merely to resolve this item's
    # Learning Object and target path. Callers without a snapshot retain the
    # conservative full-load behavior.
    vault = loaded_vault or load_vault(root)
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
    # Read, merge, validate and publish inside the vault mutation lock, the
    # critical section family apply/undo also holds: neither can publish a file
    # read before the other's write (review F1). Re-entrant for callers that
    # already hold it (proposal accept, family operations).
    with vault_mutation_lock(vault.root, purpose="practice_item_write"):
        current_path = _locate_entity_path(vault.root, "practice-items", practice_item_id)
        if current_path is not None and current_path.resolve() != target_path.resolve():
            raise VaultWriterError(f"Refusing to move {practice_item_id} from {current_path} to {target_path}")
        existing = _read_yaml_or(target_path, {})
        merged = _merge_entity(existing, raw, PRACTICE_ITEM_ORDER, clock=clock)
        validated = PracticeItem.model_validate(merged).model_dump(mode="json", exclude_none=False)
        _ensure_subject_path(paths, primary_subject, target_path)
        write_yaml(target_path, validated)
    return target_path


def current_practice_item(root: Path, practice_item_id: str, *, loaded_vault: LoadedVault) -> PracticeItem | None:
    """The item as written on disk now, parsed like the full loader.

    For callers holding a possibly stale vault snapshot; call it inside the
    vault mutation lock so the read and the following write form one section.
    """

    path = _locate_entity_path(Path(root), "practice-items", practice_item_id)
    if path is None:
        return None
    return load_practice_item_file(path, loaded_vault, issues=[])


def upsert_error_type(
    root: Path,
    payload: ErrorType | dict[str, Any],
    *,
    clock: Clock | None = None,
) -> Path:
    paths = _vault_paths(root)
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

    paths = _vault_paths(root)
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

    paths = _vault_paths(root)
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
    if isinstance(raw.get("members"), list):
        raw = {**raw, "members": _keep_scope_readings(existing.get("members"), raw["members"])}
    merged = _merge_entity(existing, raw, SOURCE_SET_ORDER, clock=clock)
    validated = SourceSet.model_validate(merged).model_dump(mode="json", exclude_none=False)
    if index is None:
        source_sets.append(validated)
    else:
        source_sets[index] = validated
    paths.source_sets_path.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(paths.source_sets_path, data)
    return paths.source_sets_path


#: The member fields naming the reading a scope's unit ids were chosen on
#: (``SourceSetMember.scope_extraction_id``; exam protection by extraction identity).
_SCOPE_READING_FIELDS = ("scope_extraction_id", "scope_revision_id", "scope_seal")


def _scope_key(member: Any) -> tuple[Any, ...] | None:
    if not isinstance(member, dict):
        return None
    scope = []
    for entry in member.get("scope") or []:
        if not isinstance(entry, dict):
            return None
        scope.append((str(entry.get("unit_id") or ""), entry.get("role_override") or None))
    return (str(member.get("source_id") or ""), str(member.get("revision_id") or ""), tuple(scope))


def _without_reading(member: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in member.items() if key not in _SCOPE_READING_FIELDS}


def _keep_scope_readings(existing: Any, incoming: list[Any]) -> list[Any]:
    """Seal and keep the reading each member's scope names (exam protection
    by extraction identity).

    A member that names its reading is sealed (``scope_seal``): the book, the
    reading and the scope's entries, so an edit made outside the writer is
    seen. A member that arrives with a seal its content no longer matches
    (its units or reading changed under it) names no reading: the change
    named none. A member that re-sends an unchanged scope (same source,
    pinned revision, unit ids and role overrides) without naming its reading
    keeps the stored member's sealed reading: a writer that does not know the
    fields (an older desktop, a hand-built payload) never erases them. A
    changed scope keeps nothing."""

    recorded: dict[tuple[Any, ...], dict[str, Any]] = {}
    for member in existing if isinstance(existing, list) else []:
        key = _scope_key(member)
        if key is not None and key[2] and member.get("scope_extraction_id") \
                and member.get("scope_seal") == scope_seal(member):
            recorded.setdefault(key, {field: member.get(field) for field in _SCOPE_READING_FIELDS})
    kept: list[Any] = []
    for member in incoming:
        key = _scope_key(member)
        if key is None:
            kept.append(member)
            continue
        if not key[2]:
            member = _without_reading(member)
        elif member.get("scope_extraction_id"):
            seal = scope_seal(member)
            member = _without_reading(member) if member.get("scope_seal") not in (None, seal) \
                else {**member, "scope_seal": seal}
        elif key in recorded:
            member = {**member, **recorded[key]}
        else:
            member = _without_reading(member)
        kept.append(member)
    return kept


def _vault_paths(root: Path) -> VaultPaths:
    """Paths for a registry edit; the rest of the vault does not need to be parsed."""

    vault_root = root.resolve()
    return VaultPaths(vault_root, load_config(vault_root / "learnloop.toml"))


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
