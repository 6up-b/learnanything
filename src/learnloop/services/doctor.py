from __future__ import annotations

from dataclasses import dataclass, field
from difflib import get_close_matches
from pathlib import Path
from types import UnionType
from typing import Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel, ValidationError

from learnloop.ai.runtime import AIRuntimeReport, check_ai_runtime
from learnloop.config import LearnLoopConfig, load_config
from learnloop.codex.runtime import CodexRuntimeReport, check_codex_runtime
from learnloop.db.migrate import applied_versions, apply_migrations, discover_migrations
from learnloop.db.repositories import Repository
from learnloop.services.calibration import difficulty_miscalibration_flags
from learnloop.services.state_sync import StateSyncResult, sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import (
    ConceptGraph,
    ConceptsFile,
    DefaultRubric,
    DoctorIssue,
    EvidenceFacetsFile,
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
    details: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "entity_id": self.entity_id,
        }
        if self.details is not None:
            payload["details"] = self.details
        return payload


@dataclass(frozen=True)
class DoctorReport:
    root: Path
    issues: list[HealthIssue] = field(default_factory=list)
    state_sync: StateSyncResult | None = None
    codex_runtime: CodexRuntimeReport | None = None
    ai_runtime: AIRuntimeReport | None = None

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
            "ai_runtime": self.ai_runtime.as_dict() if self.ai_runtime else None,
        }


def run_doctor(root: Path, *, fix_state: bool = False, ai: bool = False, ai_provider: str | None = None) -> DoctorReport:
    vault_root = root.resolve()
    issues: list[HealthIssue] = []
    config = _load_config_for_doctor(vault_root, issues)
    if config is None:
        return DoctorReport(root=vault_root, issues=issues)
    codex_runtime = check_codex_runtime(vault_root, config.codex)
    ai_runtime = check_ai_runtime(vault_root, config, provider_name=ai_provider) if ai else None

    paths = VaultPaths(vault_root, config)
    _check_layout(paths, issues)
    _check_schema_versions(paths, issues)
    _check_unknown_yaml_keys(paths, issues)
    if fix_state:
        apply_migrations(paths.sqlite_path)
    _check_sqlite(paths, issues)

    try:
        vault = load_vault(vault_root)
    except Exception as exc:
        issues.append(_issue("error", "vault:load_failed", f"Vault could not be loaded: {exc}", vault_root))
        return DoctorReport(root=vault_root, issues=issues, codex_runtime=codex_runtime, ai_runtime=ai_runtime)

    issues.extend(_from_loader_issue(issue) for issue in vault.issues)
    _check_references(vault, issues)

    repository = Repository(paths.sqlite_path)
    state_sync_result = sync_vault_state(vault, repository) if fix_state and paths.sqlite_path.exists() else None
    if fix_state and paths.sqlite_path.exists() and vault.facet_aliases:
        repository.merge_facet_recall_aliases(
            vault.facet_aliases,
            algorithm_version=vault.config.algorithms.algorithm_version,
        )
    _check_sql_state(vault, repository, issues)
    _check_derived_state_rebuild_marker(vault, repository, issues)
    _check_invalid_proposals(repository, issues)
    _check_difficulty_calibration(vault, repository, issues)
    _check_bad_item_suspicion(vault, repository, issues)
    _check_criterion_facet_maps(vault, issues)
    _check_registered_facets(vault, issues)
    _check_facet_merge_candidates(vault, issues)
    _check_learning_object_merge_candidates(vault, issues)
    _check_duplicate_diagnostic_proposals(vault, repository, issues)

    return DoctorReport(
        root=vault_root,
        issues=_dedupe(issues),
        state_sync=state_sync_result,
        codex_runtime=codex_runtime,
        ai_runtime=ai_runtime,
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
    for file_path in [paths.concepts_path, paths.relations_path, paths.goals_path, paths.error_types_path, paths.facets_path]:
        if not file_path.exists():
            issues.append(_issue("error", "layout:missing_file", f"Required YAML file is missing: {file_path.relative_to(paths.root)}", file_path))


def _check_schema_versions(paths: VaultPaths, issues: list[HealthIssue]) -> None:
    for file_path in [paths.concepts_path, paths.relations_path, paths.goals_path, paths.error_types_path, paths.facets_path]:
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
        (paths.facets_path, EvidenceFacetsFile),
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
    known_error_types = set(vault.error_types)
    for error in repository.active_error_events():
        if error.error_type not in known_error_types:
            issues.append(
                _issue(
                    "warning",
                    "errors:unaligned_error_type",
                    f"Active error event {error.id} uses unknown error_type {error.error_type}",
                    entity_id=error.id,
                )
            )


def _check_derived_state_rebuild_marker(vault: LoadedVault, repository: Repository, issues: list[HealthIssue]) -> None:
    if not repository.sqlite_path.exists():
        return
    if not repository.learning_object_ids_with_attempts():
        return
    marker = repository.latest_derived_state_rebuild()
    expected_version = vault.config.algorithms.algorithm_version
    if marker is not None and marker.get("algorithm_version") == expected_version:
        return
    if marker is None:
        message = f"Derived state has not been rebuilt for algorithm_version {expected_version}"
    else:
        message = (
            "Derived state was last rebuilt for algorithm_version "
            f"{marker.get('algorithm_version')}; run rebuild-derived-state for {expected_version}"
        )
    issues.append(
        _issue(
            "warning",
            "sql:derived_state_rebuild_stale",
            message,
            repository.sqlite_path,
        )
    )


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


def _check_difficulty_calibration(vault: LoadedVault, repository: Repository, issues: list[HealthIssue]) -> None:
    """Surface items whose IRT difficulty ``b`` looks miscalibrated (spec §7.4)."""

    if not repository.sqlite_path.exists():
        return
    for flag in difficulty_miscalibration_flags(vault, repository):
        issues.append(
            _issue("warning", "difficulty:miscalibrated", flag.message, entity_id=flag.practice_item_id)
        )


def _check_bad_item_suspicion(vault: LoadedVault, repository: Repository, issues: list[HealthIssue]) -> None:
    if not repository.sqlite_path.exists():
        return
    threshold = vault.config.recall_coverage.bad_item_suspicion_review_threshold
    min_evidence = vault.config.recall_coverage.bad_item_min_evidence
    for item_id in vault.practice_items:
        state = repository.practice_item_quality_state(item_id)
        if state is None:
            continue
        if state.evidence_count < min_evidence or state.bad_item_suspicion < threshold:
            continue
        issues.append(
            _issue(
                "warning",
                "practice_item:bad_item_suspicion",
                (
                    f"{item_id} may need author review: bad_item_suspicion="
                    f"{state.bad_item_suspicion:.2f} over {state.evidence_count} attempts"
                ),
                entity_id=item_id,
            )
        )


def _check_criterion_facet_maps(vault: LoadedVault, issues: list[HealthIssue]) -> None:
    for item in vault.practice_items.values():
        rubric = vault.rubric_for_item(item)
        if rubric is None or not rubric.criteria:
            continue
        criteria = {criterion.id for criterion in rubric.criteria}
        facets = set(item.evidence_facets)
        mapped_facets: set[str] = set()
        for criterion_id, raw_map in item.criterion_facet_weights.items():
            if criterion_id not in criteria:
                issues.append(
                    _issue(
                        "error",
                        "practice_item:criterion_facet_map:blocking",
                        f"{item.id} maps unknown rubric criterion {criterion_id!r}",
                        entity_id=item.id,
                    )
                )
                continue
            weights = {facet: float(weight) for facet, weight in raw_map.items()}
            for facet in sorted(set(weights) - facets):
                issues.append(
                    _issue(
                        "error",
                        "practice_item:criterion_facet_map:blocking",
                        f"{item.id} criterion {criterion_id!r} maps unknown evidence facet {facet!r}",
                        entity_id=item.id,
                    )
                )
            valid_weights = [max(0.0, weight) for facet, weight in weights.items() if facet in facets]
            mapped_facets.update(facet for facet, weight in weights.items() if facet in facets and weight > 0)
            total = sum(valid_weights)
            if total <= 0:
                issues.append(
                    _issue(
                        "warning",
                        "practice_item:criterion_facet_map:needs_author_review",
                        f"{item.id} criterion {criterion_id!r} has no positive facet weight",
                        entity_id=item.id,
                    )
                )
            elif abs(total - 1.0) > 1e-6:
                normalized = {
                    facet: max(0.0, weight) / total
                    for facet, weight in sorted(weights.items())
                    if facet in facets and max(0.0, weight) > 0
                }
                issues.append(
                    _issue(
                        "warning",
                        "practice_item:criterion_facet_map:auto_normalizable",
                        f"{item.id} criterion {criterion_id!r} facet weights sum to {total:.3g}; normalize to 1.0",
                        entity_id=item.id,
                        details={
                            "practice_item_id": item.id,
                            "criterion_id": criterion_id,
                            "current_sum": total,
                            "proposed_criterion_facet_weights": {criterion_id: normalized},
                        },
                    )
                )
        if item.criterion_facet_weights or item.provenance.origin in {"codex_proposal", "canonical_extract"}:
            for criterion_id in sorted(criteria - set(item.criterion_facet_weights)):
                issues.append(
                    _issue(
                        "warning",
                        "practice_item:criterion_facet_map:needs_author_review",
                        f"{item.id} rubric criterion {criterion_id!r} has no criterion_facet_weights entry",
                        entity_id=item.id,
                    )
                )
        if item.criterion_facet_weights:
            for facet in sorted(facets - mapped_facets):
                issues.append(
                    _issue(
                        "warning",
                        "practice_item:criterion_facet_map:needs_author_review",
                        f"{item.id} evidence facet {facet!r} has no criterion path and will use whole-item fallback",
                        entity_id=item.id,
                    )
                )


def _check_registered_facets(vault: LoadedVault, issues: list[HealthIssue]) -> None:
    if not vault.evidence_facets:
        return
    known = set(vault.evidence_facets)
    for item in vault.practice_items.values():
        for facet in item.evidence_facets:
            if facet not in known:
                issues.append(
                    _issue(
                        "warning",
                        "evidence_facet:unregistered",
                        f"{item.id} uses evidence facet {facet!r} that is not registered in facets.yaml",
                        entity_id=item.id,
                        details={
                            "practice_item_id": item.id,
                            "facet_id": facet,
                            "suggested_facets_yaml_entry": {
                                "id": facet,
                                "title": facet.replace("_", " ").replace("-", " ").title(),
                                "aliases": [],
                                "description": None,
                                "tags": [],
                            },
                        },
                    )
                )


def _check_facet_merge_candidates(vault: LoadedVault, issues: list[HealthIssue]) -> None:
    by_lo: dict[str, set[str]] = {}
    item_ids_by_lo_facet: dict[tuple[str, str], list[str]] = {}
    for item in vault.practice_items.values():
        by_lo.setdefault(item.learning_object_id, set()).update(item.evidence_facets)
        for facet in item.evidence_facets:
            item_ids_by_lo_facet.setdefault((item.learning_object_id, facet), []).append(item.id)
    for learning_object_id, facets in by_lo.items():
        ordered = sorted(facets)
        for index, left in enumerate(ordered):
            for right in ordered[index + 1 :]:
                score = _facet_similarity(left, right)
                if score < 0.68:
                    continue
                code = "evidence_facet:merge_candidate:auto_propose" if score >= 0.82 else "evidence_facet:merge_candidate:needs_review"
                issues.append(
                    _issue(
                        "warning",
                        code,
                        (
                            f"{learning_object_id} has similar evidence facets {left!r} and {right!r} "
                            f"(similarity={score:.2f})"
                        ),
                        entity_id=learning_object_id,
                        details=_facet_merge_details(
                            learning_object_id,
                            left,
                            right,
                            score,
                            item_ids_by_lo_facet=item_ids_by_lo_facet,
                        ),
                    )
                )


def _facet_merge_details(
    learning_object_id: str,
    left: str,
    right: str,
    score: float,
    *,
    item_ids_by_lo_facet: dict[tuple[str, str], list[str]],
) -> dict[str, Any]:
    canonical, alias = sorted([left, right], key=lambda value: (len(value), value))
    affected = sorted(
        set(item_ids_by_lo_facet.get((learning_object_id, left), []))
        | set(item_ids_by_lo_facet.get((learning_object_id, right), []))
    )
    return {
        "learning_object_id": learning_object_id,
        "canonical_facet_id": canonical,
        "alias_facet_id": alias,
        "similarity": round(score, 3),
        "affected_practice_item_ids": affected,
        "suggested_facets_yaml_alias": {
            "id": canonical,
            "aliases": [alias],
        },
        "suggested_action": "Register the canonical facet in facets.yaml and put the duplicate id in aliases.",
    }


def _check_learning_object_merge_candidates(vault: LoadedVault, issues: list[HealthIssue]) -> None:
    ordered = sorted(vault.learning_objects.values(), key=lambda lo: lo.id)
    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            if left.concept != right.concept:
                continue
            if set(left.subjects) != set(right.subjects):
                continue
            score = max(_text_similarity(left.title, right.title), _text_similarity(left.summary, right.summary))
            if score < 0.82:
                continue
            canonical, duplicate = sorted([left.id, right.id], key=lambda value: (len(value), value))
            issues.append(
                _issue(
                    "warning",
                    "learning_object:merge_candidate:needs_review",
                    f"Learning Objects {left.id!r} and {right.id!r} look duplicative (similarity={score:.2f})",
                    entity_id=canonical,
                    details={
                        "canonical_learning_object_id": canonical,
                        "duplicate_learning_object_id": duplicate,
                        "shared_concept": left.concept,
                        "subjects": sorted(left.subjects),
                        "similarity": round(score, 3),
                        "suggested_action": "Review whether Practice Items should be moved to the canonical Learning Object and the duplicate deactivated.",
                    },
                )
            )


def _check_duplicate_diagnostic_proposals(
    vault: LoadedVault,
    repository: Repository,
    issues: list[HealthIssue],
) -> None:
    if not repository.sqlite_path.exists():
        return
    grouped: dict[tuple[str, tuple[str, ...]], list[dict[str, Any]]] = {}
    for batch in repository.proposal_batches():
        for item in repository.proposal_items(batch["id"]):
            if item.get("decision") != "pending" or item.get("item_type") != "practice_item":
                continue
            payload = item.get("edited_payload") or item.get("payload") or {}
            if not isinstance(payload, dict) or payload.get("practice_mode") != "diagnostic_probe":
                continue
            learning_object_id = str(payload.get("learning_object_id") or "")
            if not learning_object_id:
                continue
            raw_facets = payload.get("evidence_facets") or payload.get("repair_targets") or []
            facets = tuple(sorted({vault.canonical_facet_id(str(facet)) for facet in raw_facets if str(facet)}))
            grouped.setdefault((learning_object_id, facets), []).append(item)
    for (learning_object_id, facets), items in grouped.items():
        if len(items) < 2:
            continue
        proposal_item_ids = [str(item["id"]) for item in items]
        proposed_entity_ids = [
            str(item.get("target_entity_id") or item.get("payload", {}).get("id") or "")
            for item in items
            if str(item.get("target_entity_id") or item.get("payload", {}).get("id") or "")
        ]
        issues.append(
            _issue(
                "warning",
                "proposal:duplicate_diagnostic_practice:needs_review",
                (
                    f"{len(items)} pending diagnostic proposals target {learning_object_id} "
                    f"facets {list(facets)}"
                ),
                entity_id=learning_object_id,
                details={
                    "learning_object_id": learning_object_id,
                    "target_facets": list(facets),
                    "proposal_item_ids": proposal_item_ids,
                    "proposed_practice_item_ids": proposed_entity_ids,
                    "suggested_action": "Keep the best diagnostic item, reject duplicates, and add facet aliases if duplicated only by facet spelling.",
                },
            )
        )


def _facet_similarity(left: str, right: str) -> float:
    left_tokens = _facet_tokens(left)
    right_tokens = _facet_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    jaccard = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
    short = min(left, right, key=len)
    long = max(left, right, key=len)
    containment = 1.0 if short and short in long else 0.0
    return max(jaccard, containment * 0.85)


def _text_similarity(left: str | None, right: str | None) -> float:
    left_tokens = _text_tokens(left or "")
    right_tokens = _text_tokens(right or "")
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _text_tokens(value: str) -> set[str]:
    stop = {"a", "an", "and", "for", "from", "in", "of", "the", "to", "with"}
    normalized = value.replace("_", " ").replace("-", " ").lower()
    return {token for token in normalized.split() if token and token not in stop}


def _facet_tokens(value: str) -> set[str]:
    stop = {"formula", "rule", "concept"}
    normalized = value.replace("_", "-").lower()
    return {token for token in normalized.split("-") if token and token not in stop}


def _issue(
    severity: Severity,
    code: str,
    message: str,
    path: Path | None = None,
    *,
    entity_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> HealthIssue:
    return HealthIssue(
        severity=severity,
        code=code,
        message=message,
        path=str(path) if path else None,
        entity_id=entity_id,
        details=details,
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
