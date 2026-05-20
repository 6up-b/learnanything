from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from learnloop.clock import Clock, utc_now_iso
from learnloop.config import load_config, write_default_config
from learnloop.ids import kebab_case, snake_case
from learnloop.vault.models import (
    ConceptGraph,
    ConceptsFile,
    DefaultRubric,
    DoctorIssue,
    ErrorTypesFile,
    GoalsFile,
    LearningObject,
    LoadedVault,
    Note,
    PracticeItem,
    RelationsFile,
    Subject,
    SubjectMetadata,
)
from learnloop.vault.paths import VaultPaths, find_vault_root
from learnloop.vault.yaml_io import (
    read_markdown_with_frontmatter,
    read_yaml,
    write_markdown_with_frontmatter,
    write_yaml,
)

T = TypeVar("T", bound=BaseModel)


def _load_yaml_model(path: Path, model: type[T], issues: list[DoctorIssue]) -> T | None:
    if not path.exists():
        return None
    try:
        return model.model_validate(read_yaml(path))
    except (OSError, ValueError, ValidationError) as exc:
        issues.append(DoctorIssue("yaml:invalid", f"{path.name} could not be loaded: {exc}", path))
        return None


def _load_markdown_model(
    path: Path,
    model: type[T],
    issues: list[DoctorIssue],
) -> tuple[T | None, str]:
    if not path.exists():
        return None, ""
    try:
        metadata, body = read_markdown_with_frontmatter(path)
        return model.model_validate(metadata), body
    except (OSError, ValueError, ValidationError) as exc:
        issues.append(DoctorIssue("markdown:invalid_frontmatter", f"{path.name} frontmatter is invalid: {exc}", path))
        return None, ""


def load_vault(root: Path | None = None) -> LoadedVault:
    vault_root = root.resolve() if root else find_vault_root(Path.cwd())
    config = load_config(vault_root / "learnloop.toml")
    paths = VaultPaths(vault_root, config)
    issues: list[DoctorIssue] = []
    loaded = LoadedVault(root=vault_root, config=config, issues=issues)

    concepts_file = _load_yaml_model(paths.concepts_path, ConceptsFile, issues)
    if concepts_file:
        loaded.concepts = concepts_file.concepts

    relations_file = _load_yaml_model(paths.relations_path, RelationsFile, issues)
    if relations_file:
        loaded.edges = relations_file.edges

    goals_file = _load_yaml_model(paths.goals_path, GoalsFile, issues)
    if goals_file:
        loaded.goals = goals_file.goals

    error_types_file = _load_yaml_model(paths.error_types_path, ErrorTypesFile, issues)
    if error_types_file:
        loaded.error_types = {error_type.id: error_type for error_type in error_types_file.error_types}

    rubrics_root = vault_root / "rubrics"
    if rubrics_root.exists():
        for rubric_path in sorted(rubrics_root.glob("*.yaml")):
            default_rubric = _load_yaml_model(rubric_path, DefaultRubric, issues)
            if default_rubric is None:
                continue
            practice_mode = default_rubric.applies_to.practice_mode
            if practice_mode in loaded.default_rubrics:
                issues.append(
                    DoctorIssue(
                        "rubric:duplicate_default",
                        f"Duplicate default rubric for practice mode {practice_mode}",
                        rubric_path,
                    )
                )
                continue
            loaded.default_rubrics[practice_mode] = default_rubric.rubric

    subjects_root = vault_root / "subjects"
    if subjects_root.exists():
        for subject_dir in sorted(path for path in subjects_root.iterdir() if path.is_dir()):
            _load_subject_dir(subject_dir, loaded)

    _validate_loaded_vault(loaded)
    return loaded


def _load_subject_dir(subject_dir: Path, loaded: LoadedVault) -> None:
    subject_id = subject_dir.name
    subject_md = subject_dir / "subject.md"
    metadata, body = _load_markdown_model(subject_md, SubjectMetadata, loaded.issues)
    if metadata is None:
        loaded.issues.append(DoctorIssue("subject:missing_metadata", f"Missing valid subject.md for {subject_id}", subject_md))
        return

    graph_path = subject_dir / "concept-graph.yaml"
    graph = _load_yaml_model(graph_path, ConceptGraph, loaded.issues)
    if graph is None:
        graph = ConceptGraph(subject=metadata.id)
        loaded.issues.append(DoctorIssue("subject:missing_graph", f"Missing concept-graph.yaml for {subject_id}", graph_path))

    loaded.subjects[metadata.id] = Subject(metadata=metadata, body=body, graph=graph, path=subject_md)

    for lo_path in sorted((subject_dir / "learning-objects").glob("*.yaml")):
        learning_object = _load_yaml_model(lo_path, LearningObject, loaded.issues)
        if learning_object:
            if learning_object.id in loaded.learning_objects:
                loaded.issues.append(DoctorIssue("learning_object:duplicate_id", f"Duplicate learning object id {learning_object.id}", lo_path))
            loaded.learning_objects[learning_object.id] = learning_object
            if learning_object.subjects and learning_object.subjects[0] != subject_id:
                loaded.issues.append(
                    DoctorIssue(
                        "learning_object:folder_subject_mismatch",
                        f"{learning_object.id} primary subject is {learning_object.subjects[0]}, not folder {subject_id}",
                        lo_path,
                    )
                )

    for pi_path in sorted((subject_dir / "practice-items").glob("*.yaml")):
        practice_item = _load_yaml_model(pi_path, PracticeItem, loaded.issues)
        if practice_item:
            if practice_item.id in loaded.practice_items:
                loaded.issues.append(DoctorIssue("practice_item:duplicate_id", f"Duplicate practice item id {practice_item.id}", pi_path))
            loaded.practice_items[practice_item.id] = practice_item

    for note_path in sorted((subject_dir / "notes").glob("*.md")):
        note = _load_note(note_path, loaded.root, subject_id, loaded.issues)
        if note:
            loaded.notes[note.id] = note


def _load_note(path: Path, root: Path, folder_subject: str, issues: list[DoctorIssue]) -> Note | None:
    try:
        metadata, body = read_markdown_with_frontmatter(path)
        relative = path.relative_to(root).as_posix()
        if not metadata:
            metadata = {
                "id": "note_" + snake_case(path.with_suffix("").name),
                "subjects": [folder_subject],
                "source_type": "learner_note",
            }
        metadata.setdefault("subjects", [folder_subject])
        metadata["path"] = relative
        metadata["body"] = body
        return Note.model_validate(metadata)
    except (OSError, ValueError, ValidationError) as exc:
        issues.append(DoctorIssue("note:invalid", f"{path.name} could not be loaded: {exc}", path))
        return None


def _validate_loaded_vault(loaded: LoadedVault) -> None:
    for item_id, item in loaded.practice_items.items():
        if item.learning_object_id not in loaded.learning_objects:
            loaded.issues.append(
                DoctorIssue(
                    "practice_item:missing_learning_object",
                    f"{item_id} references missing learning object {item.learning_object_id}",
                    None,
                )
            )
    for lo_id, learning_object in loaded.learning_objects.items():
        if learning_object.concept not in loaded.concepts:
            loaded.issues.append(
                DoctorIssue("learning_object:missing_concept", f"{lo_id} references missing concept {learning_object.concept}", None)
            )
        for subject in learning_object.subjects:
            if subject not in loaded.subjects:
                loaded.issues.append(DoctorIssue("learning_object:missing_subject", f"{lo_id} references missing subject {subject}", None))
    known_error_types = set(loaded.error_types)
    for item_id, item in loaded.practice_items.items():
        rubric = loaded.rubric_for_item(item)
        if rubric is None:
            continue
        for fatal_error in rubric.fatal_errors:
            if fatal_error.id not in known_error_types:
                loaded.issues.append(
                    DoctorIssue(
                        "rubric:unaligned_error_type",
                        f"{item_id} fatal error {fatal_error.id} is not in errors/error_types.yaml",
                        None,
                    )
                )


def init_vault(root: Path, clock: Clock | None = None) -> Path:
    vault_root = root.resolve()
    vault_root.mkdir(parents=True, exist_ok=True)
    write_default_config(vault_root / "learnloop.toml")
    config = load_config(vault_root / "learnloop.toml")
    paths = VaultPaths(vault_root, config)
    now = utc_now_iso(clock)

    for directory in [
        vault_root / "concepts",
        vault_root / "profile",
        vault_root / "subjects",
        vault_root / "rubrics",
        vault_root / "errors",
        vault_root / "prompts",
        vault_root / "sessions",
        vault_root / "exports",
        vault_root / ".learnloop" / "backups",
        vault_root / ".learnloop" / "session-checkpoints",
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    agents = vault_root / "AGENTS.md"
    if not agents.exists():
        agents.write_text("# LearnLoop Vault\n\nThis directory is user data. Do not write content directly; use LearnLoop services.\n", encoding="utf-8")

    goals_md = vault_root / "profile" / "goals.md"
    if not goals_md.exists():
        goals_md.write_text("# Learning Goals\n\n", encoding="utf-8")

    if not paths.concepts_path.exists():
        write_yaml(paths.concepts_path, {"schema_version": 1, "concepts": {}})
    if not paths.relations_path.exists():
        write_yaml(paths.relations_path, {"schema_version": 1, "edges": []})
    if not paths.goals_path.exists():
        write_yaml(paths.goals_path, {"schema_version": 1, "goals": []})
    if not paths.error_types_path.exists():
        write_yaml(paths.error_types_path, {"schema_version": 1, "error_types": []})

    from learnloop.db.migrate import apply_migrations

    apply_migrations(paths.sqlite_path)
    return vault_root


def add_subject(root: Path, subject_id: str, title: str, clock: Clock | None = None) -> Path:
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    normalized_id = kebab_case(subject_id)
    now = utc_now_iso(clock)
    subject_dir = paths.subject_dir(normalized_id)
    subject_dir.mkdir(parents=True, exist_ok=True)
    for child in ["notes", "learning-objects", "practice-items"]:
        (subject_dir / child).mkdir(parents=True, exist_ok=True)

    subject_path = paths.subject_markdown_path(normalized_id)
    if not subject_path.exists():
        write_markdown_with_frontmatter(
            subject_path,
            {
                "schema_version": 1,
                "id": normalized_id,
                "title": title,
                "status": "active",
                "created_at": now,
                "updated_at": now,
            },
            f"# {title}\n\nPurpose, scope, preferences, and notes for this subject.\n",
        )

    graph_path = paths.subject_graph_path(normalized_id)
    if not graph_path.exists():
        write_yaml(
            graph_path,
            {
                "schema_version": 1,
                "subject": normalized_id,
                "additional_concepts_in_scope": [],
                "exclude_concepts": [],
                "subject_ordering_hints": [],
            },
        )
    return subject_path


def add_note(
    root: Path,
    subject_id: str,
    note_id: str,
    title: str,
    body: str,
    *,
    source_type: str = "learner_note",
    clock: Clock | None = None,
) -> Path:
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    normalized_subject = kebab_case(subject_id)
    normalized_note = "note_" + snake_case(note_id.removeprefix("note_"))
    now = utc_now_iso(clock)
    if source_type not in {"learner_note", "canonical_source", "imported"}:
        raise ValueError("source_type must be learner_note, canonical_source, or imported")
    note_path = paths.note_path(normalized_subject, normalized_note)
    write_markdown_with_frontmatter(
        note_path,
        {
            "schema_version": 1,
            "id": normalized_note,
            "subjects": [normalized_subject],
            "related_los": [],
            "related_concepts": [],
            "source_type": source_type,
            "created_at": now,
            "updated_at": now,
        },
        f"# {title}\n\n{body.strip()}\n",
    )
    return note_path
