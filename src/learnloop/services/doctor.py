from __future__ import annotations

import tomllib
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
from learnloop.services.assessment_contracts import KM_ALGORITHM_VERSION
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
    _check_retired_config(vault_root, issues)
    codex_runtime = check_codex_runtime(vault_root, config.codex)
    ai_runtime = check_ai_runtime(vault_root, config, provider_name=ai_provider) if ai else None

    paths = VaultPaths(vault_root, config)
    _check_layout(paths, issues)
    _check_schema_versions(paths, issues)
    _check_unknown_yaml_keys(paths, issues)
    if fix_state:
        apply_migrations(paths.sqlite_path)
    _check_sqlite(paths, issues)
    _recover_apply_intents(paths, issues, fix_state=fix_state)

    try:
        vault = load_vault(vault_root)
    except Exception as exc:
        issues.append(_issue("error", "vault:load_failed", f"Vault could not be loaded: {exc}", vault_root))
        return DoctorReport(root=vault_root, issues=issues, codex_runtime=codex_runtime, ai_runtime=ai_runtime)

    issues.extend(_from_loader_issue(issue) for issue in vault.issues)
    _check_references(vault, issues)

    repository = Repository(paths.sqlite_path)
    _check_source_sets(vault, repository, issues)
    state_sync_result = sync_vault_state(vault, repository) if fix_state and paths.sqlite_path.exists() else None
    if (
        fix_state
        and paths.sqlite_path.exists()
        and vault.facet_aliases
        and vault.config.algorithms.algorithm_version != KM_ALGORITHM_VERSION
    ):
        # KM2b: the legacy per-LO alias merge folds `evidence_facet_recall_state`
        # rows in place — an mvp-0.6-only table. Under mvp-0.7 aliases + merges are
        # resolved at read/projection time, so this legacy fold must not run.
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
    _check_facet_contract_completeness(vault, issues)
    _check_blueprints_and_criteria(vault, issues)
    _check_concept_merge_candidates(vault, issues)
    _check_facet_merge_candidates(vault, issues)
    _check_learning_object_merge_candidates(vault, issues)
    _check_duplicate_diagnostic_proposals(vault, repository, issues)
    _check_mvp07_canonical_state(vault, repository, issues)

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


def _check_retired_config(root: Path, issues: list[HealthIssue]) -> None:
    """Migration warning for retired config blocks (knowledge-model §8.3/§15).

    ``[cross_lo_propagation]`` (and ``propagation_mean_floor_mass``) are retired:
    the LO-to-LO graph prior is now prerequisite-only, direction-respecting, and
    shadow-only, and the error gates were dormant. A vault TOML that still
    declares them parses (for back-compat) but the values are ignored, so warn.

    Parses the TOML (comments are ignored) so a documentation comment mentioning
    the retired block never false-positives.
    """

    path = root / "learnloop.toml"
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return
    retired = [
        name
        for name in ("cross_lo_propagation", "propagation_mean_floor_mass")
        if name in data
    ]
    for name in retired:
        issues.append(
            _issue(
                "warning",
                "config:retired_cross_lo_propagation",
                f"learnloop.toml sets retired '{name}' (knowledge-model §8.3): "
                "the value is ignored — remove the block. The graph prior is now "
                "prerequisite-only and shadow-only.",
                path,
            )
        )


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
    for file_path in [paths.concepts_path, paths.relations_path, paths.error_types_path, paths.facets_path]:
        _check_yaml_schema(file_path, issues)
    # goals.yaml v1 (concept_anchors) still loads via the legacy converter.
    _check_yaml_schema(paths.goals_path, issues, supported={1, 2})
    for file_path in sorted((paths.root / "subjects").glob("*/concept-graph.yaml")):
        _check_yaml_schema(file_path, issues)
    for folder in ["learning-objects", "practice-items"]:
        for file_path in sorted((paths.root / "subjects").glob(f"*/{folder}/*.yaml")):
            _check_yaml_schema(file_path, issues)


def _check_yaml_schema(path: Path, issues: list[HealthIssue], supported: set[int] = frozenset({1})) -> None:
    if not path.exists():
        return
    try:
        data = read_yaml(path)
    except Exception as exc:
        issues.append(_issue("error", "yaml:invalid", f"{path.name} could not be parsed: {exc}", path))
        return
    schema_version = data.get("schema_version")
    if schema_version not in supported:
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


def _recover_apply_intents(paths: VaultPaths, issues: list[HealthIssue], *, fix_state: bool) -> None:
    """Complete any write-ahead apply intent left mid-flight (§10.2 recovery).

    A pending intent means a proposal acceptance crashed between the durable DB
    commit and the applied mark. Under ``--fix`` it is completed idempotently
    while holding the vault mutation lock; otherwise it is reported so a plain
    ``doctor`` run never silently mutates the vault.
    """

    if not paths.sqlite_path.exists():
        return
    from learnloop.services.apply_protocol import recover_apply_intents
    from learnloop.services.vault_lock import vault_mutation_lock

    repository = Repository(paths.sqlite_path)
    pending = repository.pending_apply_intents()
    if not pending:
        return
    if not fix_state:
        issues.append(
            _issue(
                "warning",
                "apply_intents:pending",
                f"{len(pending)} proposal apply intent(s) left mid-flight; run doctor --fix to recover",
                paths.sqlite_path,
            )
        )
        return
    try:
        with vault_mutation_lock(paths.root, purpose="doctor_recover_apply"):
            recovered = recover_apply_intents(paths.root, repository)
    except Exception as exc:  # pragma: no cover - defensive
        issues.append(
            _issue("error", "apply_intents:recovery_failed", f"Apply-intent recovery failed: {exc}", paths.sqlite_path)
        )
        return
    if recovered:
        issues.append(
            _issue(
                "warning",
                "apply_intents:recovered",
                f"Recovered {len(recovered)} mid-flight proposal apply intent(s)",
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
        for concept_id in goal.facet_scope.concepts:
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


def _check_source_sets(vault: LoadedVault, repository: Repository, issues: list[HealthIssue]) -> None:
    """Validate source-set membership (spec_source_ingestion_v2 §4.3).

    Unknown roles are open strings → warnings; missing pins are errors;
    subject/source/revision/unit references must resolve. Membership owns
    role/scope/priority — the source note carries only hints."""

    from learnloop.services.role_authority import KNOWN_ROLES

    subject_ids = set(vault.subjects)
    db_available = repository.sqlite_path.exists()
    for source_set in vault.source_sets:
        if source_set.subject_id not in subject_ids:
            issues.append(
                _issue("error", "source_set:missing_subject", f"{source_set.id} references missing subject {source_set.subject_id}", entity_id=source_set.id)
            )
        for member in source_set.members:
            if not (member.revision_id or "").strip():
                issues.append(
                    _issue("error", "source_set:missing_pin", f"{source_set.id} member {member.source_id} has no pinned revision_id", entity_id=source_set.id)
                )
            if member.default_role not in KNOWN_ROLES:
                issues.append(
                    _issue("warning", "source_set:unknown_role", f"{source_set.id} member {member.source_id} has unknown role '{member.default_role}' (fails closed for authority until confirmed)", entity_id=source_set.id)
                )
            if db_available:
                if member.source_id and repository.get_source_artifact(member.source_id) is None:
                    issues.append(
                        _issue("error", "source_set:missing_source", f"{source_set.id} references source {member.source_id} not in the library", entity_id=source_set.id)
                    )
                elif member.revision_id and repository.get_source_revision(member.revision_id) is None:
                    issues.append(
                        _issue("warning", "source_set:missing_revision", f"{source_set.id} pins revision {member.revision_id} not in the library", entity_id=source_set.id)
                    )
            for scope in member.scope:
                if scope.role_override is not None and scope.role_override not in KNOWN_ROLES:
                    issues.append(
                        _issue("warning", "source_set:unknown_role_override", f"{source_set.id} unit {scope.unit_id} has unknown role_override '{scope.role_override}'", entity_id=source_set.id)
                    )


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


def _check_mvp07_canonical_state(vault: LoadedVault, repository: Repository, issues: list[HealthIssue]) -> None:
    """Guard against mixed/inconsistent keying on an mvp-0.7 vault (KM §15).

    Canonical belief rows keyed on a facet that (after alias + merge resolution)
    is not registered signal a mixed or corrupted state; on an mvp-0.7 vault this
    is an error. Legacy vaults never write these rows, so the check is a no-op.
    """

    if vault.config.algorithms.algorithm_version != "mvp-0.7":
        return
    known = set(vault.evidence_facets)
    if not known:
        return
    try:
        merge_map = repository.facet_merge_map()
        states = repository.canonical_facet_recall_states()
    except Exception:
        return
    for state in states:
        resolved = repository.resolve_facet_merge(vault.canonical_facet_id(state.facet_id), merge_map)
        if resolved not in known:
            issues.append(
                _issue(
                    "error",
                    "facet_recall_state:unregistered_canonical_facet",
                    (
                        f"canonical belief row keys facet {state.facet_id!r} "
                        f"(resolves to {resolved!r}) which is not registered"
                    ),
                    entity_id=state.facet_id,
                    details={"facet_id": state.facet_id, "resolved_facet_id": resolved},
                )
            )


def _mvp07_facet_severity(vault: LoadedVault) -> Severity:
    """Facet-registry issues are errors on mvp-0.7 vaults, warnings on legacy.

    The upgraded doctor must not break frozen legacy vaults (§3.2), so severity
    is gated by the vault-global algorithm version.
    """

    if vault.config.algorithms.algorithm_version == "mvp-0.7":
        return "error"
    return "warning"


def _check_registered_facets(vault: LoadedVault, issues: list[HealthIssue]) -> None:
    known = set(vault.evidence_facets)
    severity = _mvp07_facet_severity(vault)

    # Once any item declares evidence_facets, an empty registry is a real gap.
    # On mvp-0.7 vaults this is a doctor error (fixes the doctor.py:588 skip,
    # knowledge-model §3.2). Legacy vaults keep today's warning-only behavior:
    # an empty registry is skipped so the upgraded doctor does not add new noise
    # to (or break) frozen vaults.
    if not known:
        if severity == "error":
            facet_bearing = [item for item in vault.practice_items.values() if item.evidence_facets]
            if facet_bearing:
                issues.append(
                    _issue(
                        "error",
                        "evidence_facet:empty_registry",
                        (
                            f"{len(facet_bearing)} practice item(s) declare evidence facets but "
                            "facets.yaml has no registry entries"
                        ),
                        entity_id=facet_bearing[0].id,
                        details={"facet_bearing_item_ids": sorted(item.id for item in facet_bearing)},
                    )
                )
        return

    for item in vault.practice_items.values():
        for facet in item.evidence_facets:
            if facet not in known:
                issues.append(
                    _issue(
                        severity,
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


def _check_facet_contract_completeness(vault: LoadedVault, issues: list[HealthIssue]) -> None:
    """Facet semantic-contract completeness (knowledge-model §3.2).

    A registry entry that declares any part of its v2 semantic contract but omits
    ``claim`` or ``kind`` is incomplete. On mvp-0.7 vaults every registered facet
    must carry both; on legacy vaults this stays a warning.
    """

    if not vault.evidence_facets:
        return
    is_mvp07 = vault.config.algorithms.algorithm_version == "mvp-0.7"
    for facet in vault.evidence_facets.values():
        declares_contract = any(
            [
                facet.kind,
                facet.claim,
                facet.preconditions,
                facet.postconditions,
                facet.applicability,
                facet.positive_examples,
                facet.negative_examples,
                facet.non_goals,
                facet.error_signatures,
                facet.instructional_repairs,
            ]
        )
        if not (is_mvp07 or declares_contract):
            continue
        missing = [field for field in ("claim", "kind") if not getattr(facet, field)]
        if missing:
            issues.append(
                _issue(
                    "error" if is_mvp07 else "warning",
                    "evidence_facet:incomplete_contract",
                    f"facet {facet.id!r} is missing required contract field(s): {', '.join(missing)}",
                    entity_id=facet.id,
                    details={"facet_id": facet.id, "missing": missing},
                )
            )


def _check_blueprints_and_criteria(vault: LoadedVault, issues: list[HealthIssue]) -> None:
    """Validate LO blueprints and rubric criterion targets (§5.1/§7.2).

    - blueprint recipe ids are unique within an LO;
    - blueprint/recipe facets are registered (severity gated by version);
    - recipe/criterion capabilities are in the closed vocabulary;
    - criterion depends_on forms a DAG (a cycle is rejected).
    """

    from learnloop.services.capability_mapping import is_valid_capability
    from learnloop.vault.models import learning_object_facet_union, recipe_components

    known = set(vault.evidence_facets)
    severity = _mvp07_facet_severity(vault)

    for lo in vault.learning_objects.values():
        if not lo.blueprints:
            continue
        recipe_ids: set[str] = set()
        for blueprint in lo.blueprints:
            for recipe in blueprint.recipes:
                if recipe.id in recipe_ids:
                    issues.append(
                        _issue(
                            "error",
                            "blueprint:duplicate_recipe_id",
                            f"{lo.id} declares recipe id {recipe.id!r} more than once",
                            entity_id=lo.id,
                        )
                    )
                recipe_ids.add(recipe.id)
                for component in recipe_components(recipe):
                    if not is_valid_capability(component.capability):
                        issues.append(
                            _issue(
                                "error",
                                "blueprint:invalid_capability",
                                (
                                    f"{lo.id} recipe {recipe.id!r} uses capability "
                                    f"{component.capability!r} outside the closed vocabulary"
                                ),
                                entity_id=lo.id,
                            )
                        )
        if known:
            for facet in learning_object_facet_union(lo):
                if facet not in known:
                    issues.append(
                        _issue(
                            severity,
                            "blueprint:unregistered_facet",
                            f"{lo.id} blueprint references unregistered facet {facet!r}",
                            entity_id=lo.id,
                            details={"learning_object_id": lo.id, "facet_id": facet},
                        )
                    )

    _check_criterion_target_dags(vault, issues)


def _check_criterion_target_dags(vault: LoadedVault, issues: list[HealthIssue]) -> None:
    from learnloop.services.capability_mapping import is_valid_capability

    known = set(vault.evidence_facets)
    severity = _mvp07_facet_severity(vault)
    rubrics: list[tuple[str, Any]] = [
        (f"rubric:{mode}", rubric) for mode, rubric in vault.default_rubrics.items()
    ]
    for item in vault.practice_items.values():
        if item.grading_rubric is not None:
            rubrics.append((item.id, item.grading_rubric))

    for owner_id, rubric in rubrics:
        criterion_ids = {criterion.id for criterion in rubric.criteria}
        graph: dict[str, list[str]] = {}
        for criterion in rubric.criteria:
            graph[criterion.id] = [dep for dep in criterion.depends_on if dep in criterion_ids]
            for dep in criterion.depends_on:
                if dep not in criterion_ids:
                    issues.append(
                        _issue(
                            "error",
                            "criterion:unknown_dependency",
                            f"{owner_id} criterion {criterion.id!r} depends_on unknown criterion {dep!r}",
                            entity_id=owner_id,
                        )
                    )
            for target in criterion.targets:
                if not is_valid_capability(target.capability):
                    issues.append(
                        _issue(
                            "error",
                            "criterion:invalid_capability",
                            (
                                f"{owner_id} criterion {criterion.id!r} target uses capability "
                                f"{target.capability!r} outside the closed vocabulary"
                            ),
                            entity_id=owner_id,
                        )
                    )
                if known and target.facet not in known:
                    issues.append(
                        _issue(
                            severity,
                            "criterion:unregistered_target_facet",
                            f"{owner_id} criterion {criterion.id!r} targets unregistered facet {target.facet!r}",
                            entity_id=owner_id,
                        )
                    )
        cycle = _first_dependency_cycle(graph)
        if cycle is not None:
            issues.append(
                _issue(
                    "error",
                    "criterion:dependency_cycle",
                    f"{owner_id} criterion depends_on graph has a cycle: {' -> '.join(cycle)}",
                    entity_id=owner_id,
                    details={"cycle": cycle},
                )
            )


def _first_dependency_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    """Return one cycle as an id path, or None if the graph is a DAG."""

    WHITE, GREY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}

    def visit(node: str, stack: list[str]) -> list[str] | None:
        color[node] = GREY
        stack.append(node)
        for neighbor in graph.get(node, []):
            if color.get(neighbor) == GREY:
                index = stack.index(neighbor)
                return stack[index:] + [neighbor]
            if color.get(neighbor) == WHITE:
                found = visit(neighbor, stack)
                if found is not None:
                    return found
        stack.pop()
        color[node] = BLACK
        return None

    for node in graph:
        if color[node] == WHITE:
            found = visit(node, [])
            if found is not None:
                return found
    return None


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


def _check_concept_merge_candidates(vault: LoadedVault, issues: list[HealthIssue]) -> None:
    ordered = sorted(vault.concepts.items())
    for index, (left_id, left) in enumerate(ordered):
        for right_id, right in ordered[index + 1 :]:
            strong_alias = bool(_concept_surfaces(left_id, left) & _concept_surfaces(right_id, right))
            score = _concept_similarity(left_id, left, right_id, right)
            if not strong_alias and score < 0.72:
                continue
            canonical, duplicate = sorted([left_id, right_id], key=lambda value: (len(value), value))
            code = "concept:merge_candidate:strong_alias" if strong_alias else "concept:merge_candidate:needs_review"
            issues.append(
                _issue(
                    "warning",
                    code,
                    f"Concepts {left_id!r} and {right_id!r} look duplicative (similarity={score:.2f})",
                    entity_id=canonical,
                    details={
                        "canonical_concept_id": canonical,
                        "duplicate_concept_id": duplicate,
                        "similarity": round(score, 3),
                        "strong_alias": strong_alias,
                        "affected": _concept_merge_affected_refs(vault, canonical, duplicate),
                        "suggested_action": (
                            f"Review and run `learnloop merge-concepts {canonical} {duplicate}` "
                            "if these are the same concept."
                        ),
                    },
                )
            )


def _concept_similarity(left_id: str, left: Any, right_id: str, right: Any) -> float:
    left_text = " ".join([left_id, left.title, *(left.aliases or []), left.description or ""])
    right_text = " ".join([right_id, right.title, *(right.aliases or []), right.description or ""])
    return max(
        _text_similarity(left.title, right.title),
        _text_similarity(left_id, right_id),
        _text_similarity(left_text, right_text),
    )


def _concept_surfaces(concept_id: str, concept: Any) -> set[str]:
    values = [concept_id, concept.title, *(concept.aliases or [])]
    return {_normalized_surface(value) for value in values if _normalized_surface(value)}


def _normalized_surface(value: str) -> str:
    return " ".join(sorted(_text_tokens(value)))


def _concept_merge_affected_refs(vault: LoadedVault, canonical_id: str, duplicate_id: str) -> dict[str, list[str]]:
    concept_ids = {canonical_id, duplicate_id}
    return {
        "learning_objects": sorted(
            learning_object.id
            for learning_object in vault.learning_objects.values()
            if learning_object.concept in concept_ids
            or bool(set(learning_object.prerequisites) & concept_ids)
            or bool(set(learning_object.confusables) & concept_ids)
        ),
        "concept_edges": sorted(
            edge.id for edge in vault.edges if edge.source in concept_ids or edge.target in concept_ids
        ),
        "goals": sorted(
            goal.id for goal in vault.goals if bool(set(goal.facet_scope.concepts) & concept_ids)
        ),
        "error_types": sorted(
            error_type.id
            for error_type in vault.error_types.values()
            if bool(set(error_type.related_concepts) & concept_ids)
        ),
        "notes": sorted(
            note.id for note in vault.notes.values() if bool(set(note.related_concepts) & concept_ids)
        ),
    }


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
