from __future__ import annotations

from dataclasses import dataclass, field
from difflib import get_close_matches
from pathlib import Path
from types import UnionType
from typing import Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel, ValidationError

from learnloop.config import LearnLoopConfig, load_config
from learnloop.codex.runtime import CodexRuntimeReport, check_codex_runtime
from learnloop.db.migrate import applied_versions, discover_migrations
from learnloop.db.repositories import Repository
from learnloop.services.state_sync import StateSyncResult, sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import (
    ConceptGraph,
    ConceptsFile,
    DefaultRubric,
    DoctorIssue,
    ErrorTypesFile,
    GoalsFile,
    LearningObject,
    LoadedVault,
    PracticeItem,
    RelationsFile,
)
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml

Severity = Literal["error", "warning"]


@dataclass(frozen=True)
class HealthIssue:
    severity: Severity
    code: str
    message: str
    path: str | None = None
    entity_id: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "entity_id": self.entity_id,
        }


@dataclass(frozen=True)
class DoctorReport:
    root: Path
    issues: list[HealthIssue] = field(default_factory=list)
    state_sync: StateSyncResult | None = None
    codex_runtime: CodexRuntimeReport | None = None

    @property
    def clean(self) -> bool:
        return not self.issues

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")

    def as_dict(self) -> dict[str, object]:
        return {
            "version": 1,
            "root": str(self.root),
            "clean": self.clean,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [issue.as_dict() for issue in self.issues],
            "state_sync": self.state_sync.as_dict() if self.state_sync else None,
            "codex_runtime": self.codex_runtime.as_dict() if self.codex_runtime else None,
        }


def run_doctor(root: Path, *, fix_state: bool = False) -> DoctorReport:
    vault_root = root.resolve()
    issues: list[HealthIssue] = []
    config = _load_config_for_doctor(vault_root, issues)
    if config is None:
        return DoctorReport(root=vault_root, issues=issues)
    codex_runtime = check_codex_runtime(vault_root, config.codex)

    paths = VaultPaths(vault_root, config)
    _check_layout(paths, issues)
    _check_schema_versions(paths, issues)
    _check_unknown_yaml_keys(paths, issues)
    _check_sqlite(paths, issues)

    try:
        vault = load_vault(vault_root)
    except Exception as exc:
        issues.append(_issue("error", "vault:load_failed", f"Vault could not be loaded: {exc}", vault_root))
        return DoctorReport(root=vault_root, issues=issues, codex_runtime=codex_runtime)

    issues.extend(_from_loader_issue(issue) for issue in vault.issues)
    _check_references(vault, issues)

    repository = Repository(paths.sqlite_path)
    state_sync_result = sync_vault_state(vault, repository) if fix_state and paths.sqlite_path.exists() else None
    _check_sql_state(vault, repository, issues)
    _check_invalid_proposals(repository, issues)

    return DoctorReport(
        root=vault_root,
        issues=_dedupe(issues),
        state_sync=state_sync_result,
        codex_runtime=codex_runtime,
    )


def _load_config_for_doctor(root: Path, issues: list[HealthIssue]) -> LearnLoopConfig | None:
    path = root / "learnloop.toml"
    if not path.exists():
        issues.append(_issue("error", "config:missing", "learnloop.toml is missing", path))
        return None
    try:
        return load_config(path)
    except (OSError, ValueError, ValidationError) as exc:
        issues.append(_issue("error", "config:invalid", f"learnloop.toml is invalid: {exc}", path))
        return None


def _check_layout(paths: VaultPaths, issues: list[HealthIssue]) -> None:
    for directory in [
        paths.root / "concepts",
        paths.root / "profile",
        paths.root / "subjects",
        paths.root / "rubrics",
        paths.root / "errors",
        paths.root / "prompts",
        paths.root / "sessions",
        paths.root / "exports",
        paths.root / ".learnloop" / "backups",
        paths.root / ".learnloop" / "session-checkpoints",
    ]:
        if not directory.is_dir():
            issues.append(_issue("error", "layout:missing_directory", f"Required directory is missing: {directory.relative_to(paths.root)}", directory))
    for file_path in [paths.concepts_path, paths.relations_path, paths.goals_path, paths.error_types_path]:
        if not file_path.exists():
            issues.append(_issue("error", "layout:missing_file", f"Required YAML file is missing: {file_path.relative_to(paths.root)}", file_path))


def _check_schema_versions(paths: VaultPaths, issues: list[HealthIssue]) -> None:
    for file_path in [paths.concepts_path, paths.relations_path, paths.goals_path, paths.error_types_path]:
        _check_yaml_schema(file_path, issues)
    for file_path in sorted((paths.root / "subjects").glob("*/concept-graph.yaml")):
        _check_yaml_schema(file_path, issues)
    for folder in ["learning-objects", "practice-items"]:
        for file_path in sorted((paths.root / "subjects").glob(f"*/{folder}/*.yaml")):
            _check_yaml_schema(file_path, issues)


def _check_yaml_schema(path: Path, issues: list[HealthIssue]) -> None:
    if not path.exists():
        return
    try:
        data = read_yaml(path)
    except Exception as exc:
        issues.append(_issue("error", "yaml:invalid", f"{path.name} could not be parsed: {exc}", path))
        return
    schema_version = data.get("schema_version")
    if schema_version != 1:
        issues.append(
            _issue(
                "error",
                "yaml:unsupported_schema_version",
                f"{path.name} has unsupported schema_version {schema_version!r}",
                path,
            )
        )


def _check_unknown_yaml_keys(paths: VaultPaths, issues: list[HealthIssue]) -> None:
    yaml_models: list[tuple[Path, type[BaseModel]]] = [
        (paths.concepts_path, ConceptsFile),
        (paths.relations_path, RelationsFile),
        (paths.goals_path, GoalsFile),
        (paths.error_types_path, ErrorTypesFile),
    ]
    yaml_models.extend(
        (file_path, ConceptGraph)
        for file_path in sorted((paths.root / "subjects").glob("*/concept-graph.yaml"))
    )
    yaml_models.extend(
        (file_path, LearningObject)
        for file_path in sorted((paths.root / "subjects").glob("*/learning-objects/*.yaml"))
    )
    yaml_models.extend(
        (file_path, PracticeItem)
        for file_path in sorted((paths.root / "subjects").glob("*/practice-items/*.yaml"))
    )
    yaml_models.extend(
        (file_path, DefaultRubric)
        for file_path in sorted((paths.root / "rubrics").glob("*.yaml"))
    )
    for file_path, model in yaml_models:
        _check_unknown_yaml_keys_for_file(file_path, model, issues)


def _check_unknown_yaml_keys_for_file(
    path: Path,
    model: type[BaseModel],
    issues: list[HealthIssue],
) -> None:
    if not path.exists():
        return
    try:
        data = read_yaml(path)
    except Exception:
        return
    if isinstance(data, dict):
        _check_unknown_mapping_keys(data, model, issues, path=path, location=path.name)


def _check_unknown_mapping_keys(
    data: dict[str, Any],
    model: type[BaseModel],
    issues: list[HealthIssue],
    *,
    path: Path,
    location: str,
) -> None:
    known = set(model.model_fields)
    for key, value in data.items():
        if key not in known:
            match = get_close_matches(str(key), known, n=1, cutoff=0.82)
            if match:
                issues.append(
                    _issue(
                        "warning",
                        "yaml:unknown_key_typo",
                        f"{location} has unknown key {key!r}; did you mean {match[0]!r}?",
                        path,
                    )
                )
            continue
        annotation = model.model_fields[key].annotation
        for child_location, child_model, child_data in _iter_model_children(value, annotation, f"{location}.{key}"):
            _check_unknown_mapping_keys(child_data, child_model, issues, path=path, location=child_location)


def _iter_model_children(
    value: Any,
    annotation: Any,
    location: str,
) -> list[tuple[str, type[BaseModel], dict[str, Any]]]:
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in {UnionType, Union}:
        children: list[tuple[str, type[BaseModel], dict[str, Any]]] = []
        for arg in args:
            children.extend(_iter_model_children(value, arg, location))
        return children
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return [(location, annotation, value)] if isinstance(value, dict) else []
    if origin in {list, tuple} and args:
        child_model = _model_from_annotation(args[0])
        if child_model is None or not isinstance(value, list):
            return []
        return [
            (f"{location}[{index}]", child_model, item)
            for index, item in enumerate(value)
            if isinstance(item, dict)
        ]
    if origin is dict and len(args) == 2:
        child_model = _model_from_annotation(args[1])
        if child_model is None or not isinstance(value, dict):
            return []
        return [
            (f"{location}.{key}", child_model, item)
            for key, item in value.items()
            if isinstance(item, dict)
        ]
    return []


def _model_from_annotation(annotation: Any) -> type[BaseModel] | None:
    origin = get_origin(annotation)
    if origin in {UnionType, Union}:
        for arg in get_args(annotation):
            model = _model_from_annotation(arg)
            if model is not None:
                return model
        return None
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    return None


def _check_sqlite(paths: VaultPaths, issues: list[HealthIssue]) -> None:
    if not paths.sqlite_path.exists():
        issues.append(_issue("error", "sqlite:missing", "SQLite state database is missing", paths.sqlite_path))
        return
    expected = {migration.version for migration in discover_migrations()}
    applied = applied_versions(paths.sqlite_path)
    missing = sorted(expected - applied)
    if missing:
        issues.append(
            _issue(
                "error",
                "sqlite:migrations_missing",
                f"SQLite is missing migration versions: {', '.join(str(version) for version in missing)}",
                paths.sqlite_path,
            )
        )


def _from_loader_issue(issue: DoctorIssue) -> HealthIssue:
    warning_codes = {
        "learning_object:folder_subject_mismatch",
        "rubric:unaligned_error_type",
    }
    severity: Severity = "warning" if issue.code in warning_codes else "error"
    return _issue(severity, issue.code, issue.message, issue.path)


def _check_references(vault: LoadedVault, issues: list[HealthIssue]) -> None:
    concept_ids = set(vault.concepts)
    subject_ids = set(vault.subjects)
    learning_object_ids = set(vault.learning_objects)
    error_type_ids = set(vault.error_types)

    for goal in vault.goals:
        for concept_id in goal.concept_anchors:
            if concept_id not in concept_ids:
                issues.append(_issue("error", "goal:missing_concept", f"{goal.id} references missing concept {concept_id}", entity_id=goal.id))
    for edge in vault.edges:
        if edge.source not in concept_ids:
            issues.append(_issue("error", "concept_edge:missing_source", f"{edge.id} references missing source concept {edge.source}", entity_id=edge.id))
        if edge.target not in concept_ids:
            issues.append(_issue("error", "concept_edge:missing_target", f"{edge.id} references missing target concept {edge.target}", entity_id=edge.id))
    for error_type in vault.error_types.values():
        for concept_id in error_type.related_concepts:
            if concept_id not in concept_ids:
                issues.append(_issue("warning", "error_type:missing_related_concept", f"{error_type.id} references missing related concept {concept_id}", entity_id=error_type.id))
    for item in vault.practice_items.values():
        for subject_id in vault.subjects_for_item(item):
            if subject_id not in subject_ids:
                issues.append(_issue("error", "practice_item:missing_subject", f"{item.id} references missing subject {subject_id}", entity_id=item.id))
        rubric = vault.rubric_for_item(item)
        if rubric is None:
            issues.append(_issue("warning", "practice_item:missing_rubric", f"{item.id} has no resolved grading rubric", entity_id=item.id))
        else:
            for fatal_error in rubric.fatal_errors:
                if fatal_error.id not in error_type_ids:
                    issues.append(_issue("warning", "rubric:unaligned_error_type", f"{item.id} fatal error {fatal_error.id} is not in errors/error_types.yaml", entity_id=item.id))
    for note in vault.notes.values():
        for subject_id in note.subjects:
            if subject_id not in subject_ids:
                issues.append(_issue("error", "note:missing_subject", f"{note.id} references missing subject {subject_id}", entity_id=note.id))
        for learning_object_id in note.related_los:
            if learning_object_id not in learning_object_ids:
                issues.append(_issue("warning", "note:missing_learning_object", f"{note.id} references missing Learning Object {learning_object_id}", entity_id=note.id))
        for concept_id in note.related_concepts:
            if concept_id not in concept_ids:
                issues.append(_issue("warning", "note:missing_concept", f"{note.id} references missing concept {concept_id}", entity_id=note.id))


def _check_sql_state(vault: LoadedVault, repository: Repository, issues: list[HealthIssue]) -> None:
    if not repository.sqlite_path.exists():
        return
    practice_item_states = repository.practice_item_states()
    mastery_states = repository.mastery_states()
    for item_id in vault.practice_items:
        if item_id not in practice_item_states:
            issues.append(_issue("error", "sql:missing_practice_item_state", f"Missing practice_item_state for {item_id}", entity_id=item_id))
    for item_id, state in practice_item_states.items():
        if item_id not in vault.practice_items and state.active:
            issues.append(_issue("warning", "sql:state_for_missing_practice_item", f"Active SQL state exists for missing Practice Item {item_id}", entity_id=item_id))
    for learning_object_id in vault.learning_objects:
        if learning_object_id not in mastery_states:
            issues.append(_issue("error", "sql:missing_learning_object_mastery", f"Missing learning_object_mastery for {learning_object_id}", entity_id=learning_object_id))
    for learning_object_id in mastery_states:
        if learning_object_id not in vault.learning_objects:
            issues.append(_issue("warning", "sql:mastery_for_missing_learning_object", f"SQL mastery exists for missing Learning Object {learning_object_id}", entity_id=learning_object_id))


def _check_invalid_proposals(repository: Repository, issues: list[HealthIssue]) -> None:
    if not repository.sqlite_path.exists():
        return
    for item in repository.pending_invalid_proposal_items():
        issues.append(
            _issue(
                "warning",
                "proposal:invalid_pending_item",
                f"Pending proposal item {item['id']} is invalid",
                entity_id=item["id"],
            )
        )


def _issue(
    severity: Severity,
    code: str,
    message: str,
    path: Path | None = None,
    *,
    entity_id: str | None = None,
) -> HealthIssue:
    return HealthIssue(
        severity=severity,
        code=code,
        message=message,
        path=str(path) if path else None,
        entity_id=entity_id,
    )


def _dedupe(issues: list[HealthIssue]) -> list[HealthIssue]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[HealthIssue] = []
    for issue in issues:
        key = (issue.severity, issue.code, issue.message)
        if key in seen:
            continue
        seen.add(key)
        unique.append(issue)
    return sorted(unique, key=lambda issue: (issue.severity != "error", issue.code, issue.entity_id or "", issue.path or ""))
