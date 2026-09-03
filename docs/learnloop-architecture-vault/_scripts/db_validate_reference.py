#!/usr/bin/env python3
"""Validate the generated database and configuration reference graph.

Run from any working directory with the repository virtual environment::

    .venv/bin/python \
      docs/learnloop-architecture-vault/_scripts/db_validate_reference.py

The validator deliberately compares documentation against live authorities. It
does not trust catalog prose as a source of truth.
"""

from __future__ import annotations

import ast
import functools
import json
import re
import sqlite3
import sys
import tomllib
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import yaml


SCRIPT_PATH = Path(__file__).resolve()
VAULT_ROOT = SCRIPT_PATH.parents[1]
REPOSITORY_ROOT = SCRIPT_PATH.parents[3]
SRC_ROOT = REPOSITORY_ROOT / "src"
DATABASE_ROOT = VAULT_ROOT / "Reference" / "Database"
TABLES_ROOT = DATABASE_ROOT / "Tables"
CONFIG_ROOT = VAULT_ROOT / "Reference" / "Configuration"
CONFIG_FIELDS_ROOT = CONFIG_ROOT / "Fields"
INITIALIZATION_NOTE = VAULT_ROOT / "Reference" / "CLI" / "Initialization.md"
SCHEMA_PATH = REPOSITORY_ROOT / "fixtures" / "migration_head_157" / "state.sqlite"
CONFIG_SCHEMA_SOURCE = REPOSITORY_ROOT / "src" / "learnloop" / "config" / "schema.py"
SCHEMA_HEAD = 157

sys.path.insert(0, str(SRC_ROOT))

from learnloop.config.schema import LearnLoopConfig  # noqa: E402
from learnloop.config.template import DEFAULT_CONFIG_TEXT  # noqa: E402
from learnloop.db.table_roles import TABLE_ROLES, TableRole  # noqa: E402
from learnloop.substrate.rebuild_orchestrator import (  # noqa: E402
    derived_table_owners,
    validate_replayer_registry,
)


REQUIRED_FRONTMATTER = {
    "title",
    "status",
    "doc_version",
    "architecture_version",
    "source_commit",
    "source_commit_timestamp",
    "last_verified",
    "source_paths",
    "tags",
}
EXPECTED_STATUS_OVERRIDES = {
    "practice_item_state": "active-historical-seam",
    "controller_shadow_predictions": "dormant-shadow",
    "controller_prequential_reports": "dormant-shadow",
    "shadow_component_events": "dormant-shadow",
    "source_exam_profiles": "dormant-owner-gated",
    "source_locator_schemes": "dormant-owner-gated",
    "learner_theta": "dormant-owner-gated",
}
EXPECTED_LEGACY_TABLES = {
    "evidence_facet_recall_state",
    "facet_uncertainty",
    "elicitation_events",
    "hypothesis_sets",
    "learner_state_beliefs",
    "lo_probe_state",
}
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
BLOCK_RE = re.compile(r"(?:^|\s)\^([A-Za-z0-9-]+)\s*$", re.MULTILINE)
TABLE_PURPOSE_RE = re.compile(
    r"^## Why it exists\s*\n+(.+?)\s+\^table-purpose\s*$", re.MULTILINE
)

LEGACY_CONFIG_PATHS = {
    "probe.attempts_target_default",
    "probe.attempts_target_with_strong_claim",
    "probe.claim_skip_threshold",
    "probe.variance_convergence_threshold",
}
DORMANT_CONFIG_PREFIXES = ("probe.shadow.", "capabilities.")
DORMANT_CONFIG_PATHS = {
    "scheduler.followup.predictive_eig_weight",
    "scheduler.followup.predictive_eig_target_cap",
    "mastery.irt.eb_difficulty_enabled",
    "mastery.irt.b_prior_variance",
    "mastery.irt.b_learning_rate_scale",
    "mastery.irt.b_max_step",
    "mastery.irt.b_var_min",
}
PINNED_CONFIG_STATUSES = {
    "probe.hypothesis_set_max_size": "ACTIVE",
    "probe.attempts_target_default": "LEGACY",
    "probe.shadow.enabled": "DORMANT",
    "scheduler.followup.predictive_eig_weight": "DORMANT",
    "ingest.audio.provider": "COMPAT",
}
CONFIG_ANCHOR_RE = re.compile(r"`([^`]+\.py):([1-9][0-9]*)`")
REQUIRED_COMPAT_INPUTS = {
    "schema_version": ("forecasts", "cross_lo_propagation"),
    "ai": ("[codex]", "codex_http", "openai_compatible", "auth_mode"),
    "ingest": ("ingest.audio.provider = openrouter", "evidence_span_input_tokens"),
    "probe": ("self_graded_evidence_weight", "probe.dialogue.max_turns"),
    "recall_coverage": ("facet_recall_prior_pseudo_count", "coverage_epsilon"),
    "error_impacts": ("max_sharpening", "recall_coverage.max_error_sharpening"),
}


class ValidationErrors:
    """Accumulate independent failures so one run reports every repair."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def add(self, message: str) -> None:
        self.messages.append(message)

    def expect(self, condition: bool, message: str) -> None:
        if not condition:
            self.add(message)


def owned_notes() -> list[Path]:
    paths = [
        *DATABASE_ROOT.rglob("*.md"),
        *CONFIG_ROOT.rglob("*.md"),
        INITIALIZATION_NOTE,
    ]
    return sorted(set(path.resolve() for path in paths))


def parse_frontmatter(path: Path, errors: ValidationErrors) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.add(f"{path.relative_to(VAULT_ROOT)}: missing YAML frontmatter")
        return {}
    try:
        raw, _body = text[4:].split("\n---\n", 1)
    except ValueError:
        errors.add(f"{path.relative_to(VAULT_ROOT)}: unterminated YAML frontmatter")
        return {}
    try:
        parsed = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        errors.add(f"{path.relative_to(VAULT_ROOT)}: invalid YAML: {exc}")
        return {}
    if not isinstance(parsed, dict):
        errors.add(f"{path.relative_to(VAULT_ROOT)}: frontmatter is not a mapping")
        return {}
    return parsed


def flatten(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    if isinstance(value, dict):
        rows: list[tuple[str, Any]] = []
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(flatten(child, path))
        return rows
    return [(prefix, value)]


def expected_functionality_status(table: str, role: TableRole) -> str:
    if table in EXPECTED_STATUS_OVERRIDES:
        return EXPECTED_STATUS_OVERRIDES[table]
    if table in EXPECTED_LEGACY_TABLES:
        return "legacy-preserved"
    if role is TableRole.COMPAT:
        raise AssertionError(f"unclassified COMPAT status: {table}")
    return "active"


def expected_config_status(path: str) -> str:
    if path in LEGACY_CONFIG_PATHS:
        return "LEGACY"
    if path.endswith(".lo_mastery_delta") or path == "ingest.audio.provider":
        return "COMPAT"
    if path in DORMANT_CONFIG_PATHS or path.startswith(DORMANT_CONFIG_PREFIXES):
        return "DORMANT"
    return "ACTIVE"


def python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


SOURCE_FILES = python_files(SRC_ROOT)
SOURCE_TEXT = {
    path: path.read_text(encoding="utf-8", errors="replace") for path in SOURCE_FILES
}


def repo_relative(path: Path) -> str:
    return path.relative_to(REPOSITORY_ROOT).as_posix()


@functools.cache
def effective_config_model() -> LearnLoopConfig:
    return LearnLoopConfig.model_validate(tomllib.loads(DEFAULT_CONFIG_TEXT))


@functools.cache
def effective_config_paths() -> tuple[str, ...]:
    payload = effective_config_model().model_dump(mode="json", exclude_none=False)
    return tuple(path for path, _value in flatten(payload))


@functools.cache
def schema_field_lines() -> dict[tuple[str, str], int]:
    tree = ast.parse(CONFIG_SCHEMA_SOURCE.read_text(encoding="utf-8"))
    result: dict[tuple[str, str], int] = {}
    for class_node in (node for node in tree.body if isinstance(node, ast.ClassDef)):
        for statement in class_node.body:
            if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                result[(class_node.name, statement.target.id)] = statement.lineno
    return result


def declaring_field_line(model_type: type[Any], field_name: str) -> int | None:
    lines = schema_field_lines()
    for candidate in model_type.__mro__:
        line = lines.get((candidate.__name__, field_name))
        if line is not None:
            return line
    return None


@functools.cache
def expected_schema_reference(path: str) -> str:
    """Independently derive the exact field or typed-container declaration."""

    current: Any = effective_config_model()
    best_line: int | None = None
    for segment in path.split("."):
        model_fields = getattr(type(current), "model_fields", None)
        if isinstance(model_fields, dict):
            if segment in model_fields:
                line = declaring_field_line(type(current), segment)
                if line is None:
                    raise RuntimeError(
                        f"no schema declaration for {type(current).__name__}.{segment}"
                    )
                best_line = line
            current = getattr(current, segment)
            continue
        if isinstance(current, dict):
            current = current[segment]
            continue
        raise RuntimeError(f"cannot derive a schema declaration for {path}")
    if best_line is None:
        raise RuntimeError(f"no typed schema container for {path}")
    return f"{repo_relative(CONFIG_SCHEMA_SOURCE)}:{best_line}"


@functools.cache
def model_annotation_prefixes() -> dict[str, tuple[str, ...]]:
    found: dict[str, set[tuple[str, ...]]] = defaultdict(set)

    def visit(value: Any, prefix: tuple[str, ...]) -> None:
        model_fields = getattr(type(value), "model_fields", None)
        if isinstance(model_fields, dict):
            for candidate in type(value).__mro__:
                if candidate.__module__ == "learnloop.config.schema":
                    found[candidate.__name__].add(prefix)
            for field_name in model_fields:
                visit(getattr(value, field_name), (*prefix, field_name))
            return
        if isinstance(value, dict):
            for child in value.values():
                visit(child, (*prefix, "*"))

    visit(effective_config_model(), ())
    return {
        class_name: next(iter(prefixes))
        for class_name, prefixes in found.items()
        if len(prefixes) == 1
    }


def annotation_prefix(annotation: ast.expr | None) -> tuple[str, ...] | None:
    if annotation is None:
        return None
    prefixes = model_annotation_prefixes()
    candidates: set[tuple[str, ...]] = set()
    if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
        tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", annotation.value)
        candidates.update(prefixes[token] for token in tokens if token in prefixes)
    else:
        for node in ast.walk(annotation):
            if isinstance(node, ast.Name) and node.id in prefixes:
                candidates.add(prefixes[node.id])
    return next(iter(candidates)) if len(candidates) == 1 else None


def expression_config_path(
    node: ast.AST,
    aliases: dict[str, tuple[str, ...]],
) -> tuple[str, ...] | None:
    if isinstance(node, ast.Name):
        return aliases.get(node.id)
    if isinstance(node, ast.Attribute):
        base = expression_config_path(node.value, aliases)
        if base is not None:
            return (*base, node.attr)
        if node.attr == "config":
            return ()
        return None
    if isinstance(node, ast.Subscript):
        base = expression_config_path(node.value, aliases)
        if base is None:
            return None
        index = node.slice
        if isinstance(index, ast.Constant) and isinstance(index.value, str):
            return (*base, index.value)
        return (*base, "*")
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) >= 2
    ):
        base = expression_config_path(node.args[0], aliases)
        if base is None:
            return None
        attribute = node.args[1]
        if isinstance(attribute, ast.Constant) and isinstance(attribute.value, str):
            return (*base, attribute.value)
        return (*base, "*")
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and node.args
    ):
        base = expression_config_path(node.func.value, aliases)
        if base is None:
            return None
        key = node.args[0]
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            return (*base, key.value)
        return (*base, "*")
    return None


def nodes_in_scope(scope: ast.AST) -> list[ast.AST]:
    result: list[ast.AST] = []

    def walk(node: ast.AST, *, root: bool = False) -> None:
        if not root and isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ):
            return
        result.append(node)
        for child in ast.iter_child_nodes(node):
            walk(child)

    walk(scope, root=True)
    return result


def scope_config_patterns(scope: ast.AST) -> set[tuple[tuple[str, ...], int]]:
    nodes = nodes_in_scope(scope)
    aliases: dict[str, tuple[str, ...]] = {}
    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
        arguments = [*scope.args.posonlyargs, *scope.args.args, *scope.args.kwonlyargs]
        if scope.args.vararg is not None:
            arguments.append(scope.args.vararg)
        if scope.args.kwarg is not None:
            arguments.append(scope.args.kwarg)
        for argument in arguments:
            prefix = annotation_prefix(argument.annotation)
            if prefix is not None:
                aliases[argument.arg] = prefix

    for _iteration in range(6):
        changed = False
        for node in nodes:
            value: ast.AST | None = None
            targets: list[ast.AST] = []
            if isinstance(node, ast.Assign):
                value = node.value
                targets = list(node.targets)
            elif isinstance(node, ast.AnnAssign):
                value = node.value
                targets = [node.target]
            if value is not None:
                resolved = expression_config_path(value, aliases)
                if resolved is not None:
                    for target in targets:
                        if isinstance(target, ast.Name) and aliases.get(target.id) != resolved:
                            aliases[target.id] = resolved
                            changed = True
            if isinstance(node, (ast.For, ast.AsyncFor)) and isinstance(node.iter, ast.Call):
                call = node.iter
                if isinstance(call.func, ast.Attribute) and call.func.attr in {"items", "values"}:
                    container = expression_config_path(call.func.value, aliases)
                    if container is not None:
                        target: ast.AST = node.target
                        if call.func.attr == "items" and isinstance(target, (ast.Tuple, ast.List)):
                            target = target.elts[-1]
                        if isinstance(target, ast.Name):
                            resolved = (*container, "*")
                            if aliases.get(target.id) != resolved:
                                aliases[target.id] = resolved
                                changed = True
        if not changed:
            break

    patterns: set[tuple[tuple[str, ...], int]] = set()
    for node in nodes:
        if isinstance(node, (ast.Attribute, ast.Subscript, ast.Call)):
            resolved = expression_config_path(node, aliases)
            if resolved:
                patterns.add((resolved, node.lineno))
    return patterns


def config_pattern_matches(pattern: tuple[str, ...], dotted_path: str) -> bool:
    parts = tuple(dotted_path.split("."))
    return len(pattern) == len(parts) and all(
        expected == "*" or expected == actual
        for expected, actual in zip(pattern, parts, strict=True)
    )


@functools.cache
def expected_runtime_references() -> dict[str, set[str]]:
    known_paths = effective_config_paths()
    found: dict[str, set[str]] = defaultdict(set)
    for source in SOURCE_FILES:
        if "/config/" in source.as_posix():
            continue
        tree = ast.parse(SOURCE_TEXT[source])
        scopes: list[ast.AST] = [tree]
        scopes.extend(
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        )
        patterns = set().union(*(scope_config_patterns(scope) for scope in scopes))
        for dotted_path in known_paths:
            for pattern, line in patterns:
                if config_pattern_matches(pattern, dotted_path):
                    found[dotted_path].add(f"{repo_relative(source)}:{line}")
    return found


def validate_config_anchors(
    note_name: str,
    dotted_path: str,
    rendered: str,
    errors: ValidationErrors,
) -> None:
    parsed = [f"{path}:{line}" for path, line in CONFIG_ANCHOR_RE.findall(rendered)]
    errors.expect(bool(parsed), f"{note_name}: {dotted_path} has no parseable code anchor")
    errors.expect(
        rendered.count("`") == len(parsed) * 2,
        f"{note_name}: {dotted_path} contains an unvalidated anchor form",
    )
    errors.expect(
        len(parsed) == len(set(parsed)),
        f"{note_name}: {dotted_path} repeats a source anchor",
    )
    schema_reference = expected_schema_reference(dotted_path)
    errors.expect(
        schema_reference in parsed,
        f"{note_name}: {dotted_path} does not cite its exact schema declaration {schema_reference}",
    )
    allowed_runtime = expected_runtime_references().get(dotted_path, set())
    for reference in parsed:
        errors.expect(
            reference == schema_reference or reference in allowed_runtime,
            f"{note_name}: {dotted_path} cites unrelated source line {reference}",
        )


def parse_config_field_rows(path: Path, errors: ValidationErrors) -> dict[str, dict[str, str]]:
    """Read the generated seven-column field table without treating prose tables as fields."""

    text = path.read_text(encoding="utf-8")
    required_header = (
        "| Dotted path | Effective value | Shape | Origin | Function | "
        "Runtime/refactor status | Consumer/source anchors |"
    )
    errors.expect(required_header in text, f"{path.name}: field table lacks Function/Status/source columns")
    rows: dict[str, dict[str, str]] = {}
    in_catalog = False
    for line in text.splitlines():
        if line == "## Field catalog":
            in_catalog = True
            continue
        if in_catalog and line.startswith("## "):
            break
        if not in_catalog or not line.startswith("| `"):
            continue
        cells = line[2:-2].split(" | ") if line.endswith(" |") else []
        if len(cells) != 7:
            errors.add(f"{path.name}: malformed field row: {line[:160]}")
            continue
        path_cell, _value, _shape, _origin, function, status_cell, anchors = cells
        match = re.fullmatch(r"`([^`]+)`", path_cell)
        if match is None:
            errors.add(f"{path.name}: malformed dotted path cell {path_cell}")
            continue
        dotted = match.group(1)
        status_match = re.match(r"\*\*(ACTIVE|COMPAT|LEGACY|DORMANT)\*\*\s+—\s+(.+)", status_cell)
        if status_match is None:
            errors.add(f"{path.name}: {dotted} has malformed status cell")
            continue
        if dotted in rows:
            errors.add(f"{path.name}: duplicate field row {dotted}")
        rows[dotted] = {
            "function": function.strip(),
            "status": status_match.group(1),
            "status_reason": status_match.group(2).strip(),
            "anchors": anchors.strip(),
        }
    return rows


def validate_frontmatter(
    paths: Iterable[Path], errors: ValidationErrors
) -> dict[Path, dict[str, Any]]:
    parsed: dict[Path, dict[str, Any]] = {}
    for path in paths:
        data = parse_frontmatter(path, errors)
        parsed[path] = data
        rel = path.relative_to(VAULT_ROOT)
        missing = REQUIRED_FRONTMATTER - set(data)
        if missing:
            errors.add(f"{rel}: missing frontmatter fields {sorted(missing)}")
        errors.expect(bool(data.get("title")), f"{rel}: empty title")
        errors.expect(bool(data.get("status")), f"{rel}: empty documentation status")
        errors.expect(bool(data.get("doc_version")), f"{rel}: empty doc_version")
        errors.expect(
            bool(data.get("architecture_version")),
            f"{rel}: empty architecture_version",
        )
        errors.expect(
            isinstance(data.get("source_commit"), str)
            and bool(re.fullmatch(r"[0-9a-f]{40}", data["source_commit"])),
            f"{rel}: source_commit must be a full Git hash",
        )
        timestamp = data.get("source_commit_timestamp")
        try:
            datetime.fromisoformat(str(timestamp))
        except ValueError:
            errors.add(f"{rel}: source_commit_timestamp is not ISO-8601")
        tags = data.get("tags")
        errors.expect(
            isinstance(tags, list) and bool(tags) and all(isinstance(tag, str) for tag in tags),
            f"{rel}: tags must be a non-empty string list",
        )
        source_paths = data.get("source_paths")
        errors.expect(
            isinstance(source_paths, list)
            and bool(source_paths)
            and all(isinstance(source, str) for source in source_paths),
            f"{rel}: source_paths must be a non-empty string list",
        )
        if isinstance(source_paths, list):
            for source in source_paths:
                if not isinstance(source, str):
                    continue
                candidate = REPOSITORY_ROOT / source.rstrip("/")
                if not candidate.exists():
                    errors.add(f"{rel}: cited source path does not exist: {source}")
    return parsed


def migration_head_tables() -> tuple[set[str], int]:
    connection = sqlite3.connect(f"file:{SCHEMA_PATH}?mode=ro", uri=True)
    try:
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        head = int(connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0])
    finally:
        connection.close()
    return tables, head


def validate_database_coverage(
    metadata: dict[Path, dict[str, Any]], errors: ValidationErrors
) -> tuple[Counter[str], Counter[str]]:
    validate_replayer_registry()
    schema_tables, schema_head = migration_head_tables()
    registry_tables = set(TABLE_ROLES)
    documented_tables = {path.stem for path in TABLES_ROOT.glob("*.md")}
    errors.expect(schema_head == SCHEMA_HEAD, f"fixture head is {schema_head}, expected {SCHEMA_HEAD}")
    errors.expect(
        schema_tables == registry_tables,
        "migration-head tables differ from TABLE_ROLES: "
        f"missing={sorted(schema_tables - registry_tables)}, "
        f"extra={sorted(registry_tables - schema_tables)}",
    )
    errors.expect(
        documented_tables == registry_tables,
        "table-note coverage differs from TABLE_ROLES: "
        f"missing={sorted(registry_tables - documented_tables)}, "
        f"extra={sorted(documented_tables - registry_tables)}",
    )

    role_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    for table, role in TABLE_ROLES.items():
        note = (TABLES_ROOT / f"{table}.md").resolve()
        data = metadata.get(note, {})
        note_text = note.read_text(encoding="utf-8") if note.exists() else ""
        expected_status = expected_functionality_status(table, role)
        role_counts[role.value] += 1
        status_counts[expected_status] += 1
        errors.expect(data.get("table_name") == table, f"{note.name}: table_name mismatch")
        errors.expect(data.get("table_role") == role.value, f"{note.name}: table_role mismatch")
        errors.expect(
            data.get("functionality_status") == expected_status,
            f"{note.name}: functionality_status mismatch",
        )
        errors.expect(data.get("schema_head") == SCHEMA_HEAD, f"{note.name}: schema_head mismatch")
        errors.expect(data.get("generated") is True, f"{note.name}: generated flag is not true")
        purpose_match = TABLE_PURPOSE_RE.search(note_text)
        errors.expect(purpose_match is not None, f"{note.name}: missing table-purpose block")
        if purpose_match is not None:
            purpose = purpose_match.group(1).strip()
            normalized_table = table.replace("_", " ")
            errors.expect(
                len(purpose) >= 70,
                f"{note.name}: table purpose is too short to explain an operational function",
            )
            errors.expect(
                not re.search(r"\bstores\s+(?:\w+\s+)?records\s+for\b", purpose, re.IGNORECASE),
                f"{note.name}: tautological 'stores records for' purpose",
            )
            errors.expect(
                f"stores records for **{normalized_table}**" not in purpose.casefold(),
                f"{note.name}: purpose merely restates the table name",
            )
            errors.expect(
                any(
                    verb in purpose.casefold()
                    for verb in (
                        "records",
                        "tracks",
                        "preserves",
                        "maintains",
                        "materializes",
                        "coordinates",
                        "pins",
                        "maps",
                        "queues",
                        "identifies",
                        "provides",
                        "holds",
                        "gives",
                        "captures",
                        "freezes",
                        "stores",
                        "supplies",
                        "lets",
                        "keeps",
                        "retains",
                        "points",
                        "groups",
                        "binds",
                    )
                ),
                f"{note.name}: purpose lacks an operational verb",
            )

    owners = derived_table_owners()
    derived = {table for table, role in TABLE_ROLES.items() if role is TableRole.DERIVED}
    errors.expect(set(owners) == derived, "documented DERIVED set differs from replayer ownership")
    for table in derived:
        errors.expect(len(owners.get(table, ())) == 1, f"{table}: expected exactly one rebuild owner")

    catalog = (DATABASE_ROOT / "Database Catalog.md").resolve()
    catalog_data = metadata.get(catalog, {})
    catalog_text = catalog.read_text(encoding="utf-8") if catalog.exists() else ""
    errors.expect(catalog.exists(), "canonical Reference/Database/Database Catalog.md is missing")
    errors.expect(catalog_data.get("title") == "Database Catalog", "catalog title is not canonical")
    errors.expect(catalog_data.get("table_count") == len(TABLE_ROLES), "catalog table_count mismatch")
    errors.expect(not (DATABASE_ROOT / "Table Catalog.md").exists(), "obsolete Table Catalog.md remains")
    for heading in ("## Role indexes", "## DERIVED tables", "## How to use this catalog"):
        errors.expect(heading in catalog_text, f"Database Catalog is missing {heading}")
    return role_counts, status_counts


def validate_config_coverage(
    metadata: dict[Path, dict[str, Any]], errors: ValidationErrors
) -> tuple[int, int, Counter[str]]:
    explicit = tomllib.loads(DEFAULT_CONFIG_TEXT)
    effective = LearnLoopConfig.model_validate(explicit).model_dump(
        mode="json", exclude_none=False
    )
    expected_sections = set(effective)
    documented_sections = {
        path.stem.removeprefix("Config - ") for path in CONFIG_FIELDS_ROOT.glob("Config - *.md")
    }
    errors.expect(
        documented_sections == expected_sections,
        "config-section coverage mismatch: "
        f"missing={sorted(expected_sections - documented_sections)}, "
        f"extra={sorted(documented_sections - expected_sections)}",
    )
    total_fields = 0
    all_documented_paths: set[str] = set()
    status_counts: Counter[str] = Counter()
    for section, payload in effective.items():
        expected_rows = dict(flatten(payload, section))
        count = len(expected_rows)
        total_fields += count
        note = (CONFIG_FIELDS_ROOT / f"Config - {section}.md").resolve()
        data = metadata.get(note, {})
        documented_rows = parse_config_field_rows(note, errors)
        documented_paths = set(documented_rows)
        expected_paths = set(expected_rows)
        errors.expect(
            documented_paths == expected_paths,
            f"Config - {section}: exact leaf coverage mismatch: "
            f"missing={sorted(expected_paths - documented_paths)}, "
            f"extra={sorted(documented_paths - expected_paths)}",
        )
        all_documented_paths.update(documented_paths)
        expected_section_statuses: Counter[str] = Counter()
        for dotted in expected_paths:
            expected_status = expected_config_status(dotted)
            expected_section_statuses[expected_status] += 1
            status_counts[expected_status] += 1
            row = documented_rows.get(dotted, {})
            function = row.get("function", "")
            errors.expect(
                len(function) >= 40 and "runtime configuration" != function.casefold(),
                f"Config - {section}: {dotted} lacks a semantic Function",
            )
            errors.expect(
                row.get("status") == expected_status,
                f"Config - {section}: {dotted} status {row.get('status')} != {expected_status}",
            )
            errors.expect(
                len(row.get("status_reason", "")) >= 20,
                f"Config - {section}: {dotted} lacks status evidence",
            )
            anchors = row.get("anchors", "")
            validate_config_anchors(
                f"Config - {section}", dotted, anchors, errors
            )
            if dotted in PINNED_CONFIG_STATUSES:
                errors.expect(
                    row.get("status") == PINNED_CONFIG_STATUSES[dotted],
                    f"Config - {section}: pinned status drift for {dotted}",
                )
        if section == "probe":
            hypothesis_row = documented_rows.get("probe.hypothesis_set_max_size", {})
            hypothesis_runtime = expected_runtime_references().get(
                "probe.hypothesis_set_max_size", set()
            )
            cited = {
                f"{path}:{line}"
                for path, line in CONFIG_ANCHOR_RE.findall(
                    hypothesis_row.get("anchors", "")
                )
            }
            errors.expect(
                bool(cited & hypothesis_runtime),
                "Config - probe: hypothesis_set_max_size must cite a current runtime consumer",
            )
            errors.expect(
                "current hypothesis construction"
                in hypothesis_row.get("status_reason", "").casefold(),
                "Config - probe: hypothesis_set_max_size status reason does not explain its live role",
            )
        errors.expect(data.get("field_count") == count, f"Config - {section}: field_count mismatch")
        errors.expect(data.get("generated") is True, f"Config - {section}: generated flag is not true")
        errors.expect(
            data.get("config_schema_version") == 2,
            f"Config - {section}: config_schema_version mismatch",
        )
        errors.expect(
            data.get("field_status_counts") == dict(sorted(expected_section_statuses.items())),
            f"Config - {section}: field_status_counts mismatch",
        )
        if section in REQUIRED_COMPAT_INPUTS:
            note_text = note.read_text(encoding="utf-8")
            errors.expect(
                "## Compatibility-only inputs" in note_text,
                f"Config - {section}: compatibility-only input section is missing",
            )
            for token in REQUIRED_COMPAT_INPUTS[section]:
                errors.expect(
                    token in note_text,
                    f"Config - {section}: compatibility input {token!r} is not documented",
                )

    expected_all_paths = {path for path, _value in flatten(effective)}
    errors.expect(
        all_documented_paths == expected_all_paths,
        "configuration reference does not cover each effective leaf exactly once",
    )

    overview = (CONFIG_ROOT / "Configuration.md").resolve()
    errors.expect(overview.exists(), "canonical Reference/Configuration/Configuration.md is missing")
    errors.expect(metadata.get(overview, {}).get("title") == "Configuration", "Configuration title mismatch")
    catalog = (CONFIG_ROOT / "Configuration Field Catalog.md").resolve()
    catalog_data = metadata.get(catalog, {})
    errors.expect(
        catalog_data.get("section_count") == len(expected_sections),
        "Configuration Field Catalog section_count mismatch",
    )
    errors.expect(
        catalog_data.get("field_count") == total_fields,
        "Configuration Field Catalog field_count mismatch",
    )
    errors.expect(
        catalog_data.get("field_status_counts") == dict(sorted(status_counts.items())),
        "Configuration Field Catalog field_status_counts mismatch",
    )
    return len(expected_sections), total_fields, status_counts


def normalize_heading(value: str) -> str:
    value = re.sub(r"[`*_~]", "", value)
    return re.sub(r"\s+", " ", value.strip()).casefold()


def split_wikilink(body: str) -> tuple[str, str | None]:
    # Obsidian aliases use ``|``; inside a Markdown table the same character is
    # escaped as ``\|``. Both forms still belong to the Wikilink grammar.
    normalized = body.replace("\\|", "|")
    target, separator, _alias = normalized.partition("|")
    target = target.strip()
    if "#" not in target:
        return target, None
    note, fragment = target.split("#", 1)
    return note.strip(), fragment.strip()


def build_note_index(
    metadata: dict[Path, dict[str, Any]], errors: ValidationErrors
) -> tuple[dict[str, set[Path]], dict[Path, set[str]], dict[Path, set[str]]]:
    names: dict[str, set[Path]] = defaultdict(set)
    headings: dict[Path, set[str]] = {}
    blocks: dict[Path, set[str]] = {}
    for path in VAULT_ROOT.rglob("*.md"):
        resolved = path.resolve()
        data = metadata.get(resolved)
        if data is None:
            # Only owned notes have strict frontmatter validation, but all vault
            # notes participate in link resolution.
            data = parse_frontmatter(resolved, errors)
        candidates = {path.stem, str(data.get("title", ""))}
        aliases = data.get("aliases", [])
        if isinstance(aliases, list):
            candidates.update(str(alias) for alias in aliases)
        for candidate in candidates:
            if candidate:
                names[candidate.casefold()].add(resolved)
        text = path.read_text(encoding="utf-8")
        headings[resolved] = {normalize_heading(match) for match in HEADING_RE.findall(text)}
        blocks[resolved] = set(BLOCK_RE.findall(text))
    return names, headings, blocks


def validate_links(metadata: dict[Path, dict[str, Any]], errors: ValidationErrors) -> tuple[int, int]:
    names, headings, blocks = build_note_index(metadata, errors)
    checked = 0
    path_qualified_table_links = 0
    for source in owned_notes():
        text = source.read_text(encoding="utf-8")
        for match in WIKILINK_RE.finditer(text):
            checked += 1
            raw_target, fragment = split_wikilink(match.group(1))
            if not raw_target:
                candidates = {source}
            elif "/" in raw_target:
                relative = raw_target.removesuffix(".md") + ".md"
                candidate = (VAULT_ROOT / relative).resolve()
                candidates = {candidate} if candidate.exists() else set()
            else:
                candidates = names.get(raw_target.casefold(), set())

            rel = source.relative_to(VAULT_ROOT)
            if not candidates:
                errors.add(f"{rel}: unresolved Wikilink [[{match.group(1)}]]")
                continue
            if len(candidates) > 1:
                rendered = sorted(str(path.relative_to(VAULT_ROOT)) for path in candidates)
                errors.add(f"{rel}: ambiguous Wikilink [[{match.group(1)}]] -> {rendered}")
                continue
            target = next(iter(candidates))
            if raw_target.startswith("Reference/Database/Tables/"):
                path_qualified_table_links += 1
            elif raw_target in TABLE_ROLES:
                errors.add(
                    f"{rel}: table Wikilink must be path-qualified: [[{match.group(1)}]]"
                )
            if fragment:
                if fragment.startswith("^"):
                    errors.expect(
                        fragment[1:] in blocks.get(target, set()),
                        f"{rel}: missing block target [[{match.group(1)}]]",
                    )
                else:
                    errors.expect(
                        normalize_heading(fragment) in headings.get(target, set()),
                        f"{rel}: missing heading target [[{match.group(1)}]]",
                    )
    return checked, path_qualified_table_links


def main() -> int:
    errors = ValidationErrors()
    paths = owned_notes()
    metadata = validate_frontmatter(paths, errors)
    role_counts, status_counts = validate_database_coverage(metadata, errors)
    config_sections, config_fields, config_status_counts = validate_config_coverage(metadata, errors)
    links_checked, qualified_table_links = validate_links(metadata, errors)
    report = {
        "database": {
            "schema_head": SCHEMA_HEAD,
            "table_notes": len(list(TABLES_ROOT.glob("*.md"))),
            "role_counts": dict(sorted(role_counts.items())),
            "functionality_status_counts": dict(sorted(status_counts.items())),
        },
        "configuration": {
            "section_notes": config_sections,
            "effective_leaf_values": config_fields,
            "field_status_counts": dict(sorted(config_status_counts.items())),
        },
        "documentation": {
            "owned_notes": len(paths),
            "wikilinks_checked": links_checked,
            "path_qualified_table_links": qualified_table_links,
        },
        "errors": errors.messages,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if errors.messages else 0


if __name__ == "__main__":
    raise SystemExit(main())
