#!/usr/bin/env python3
"""Generate the schema and effective-configuration reference notes.

This script intentionally reads the checked-in migration-head fixture rather
than attempting to reconstruct a schema from prose.  It combines four live
authorities:

* ``fixtures/migration_head_158/state.sqlite`` for columns, keys, indexes,
  triggers, and foreign keys;
* ``learnloop.db.table_roles`` for rebuild policy;
* ``learnloop.substrate.rebuild_orchestrator`` for DERIVED-table ownership;
* the parsed ``DEFAULT_CONFIG_TEXT`` plus ``LearnLoopConfig`` for the complete
  effective configuration of a newly initialized vault.

The output is deliberately mechanical.  Hand-authored architectural context
lives beside it in the parent reference directories.
"""

from __future__ import annotations

import ast
import functools
import json
import re
import sqlite3
import subprocess
import sys
import tomllib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


SCRIPT_PATH = Path(__file__).resolve()
VAULT_ROOT = SCRIPT_PATH.parents[1]
REPOSITORY_ROOT = SCRIPT_PATH.parents[3]
SRC_ROOT = REPOSITORY_ROOT / "src"
TABLES_ROOT = VAULT_ROOT / "Reference" / "Database" / "Tables"
CONFIG_FIELDS_ROOT = VAULT_ROOT / "Reference" / "Configuration" / "Fields"
SCHEMA_PATH = REPOSITORY_ROOT / "fixtures" / "migration_head_158" / "state.sqlite"
MIGRATIONS_ROOT = REPOSITORY_ROOT / "migrations"

sys.path.insert(0, str(SRC_ROOT))

from learnloop.config.schema import LearnLoopConfig  # noqa: E402
from learnloop.config.template import DEFAULT_CONFIG_TEXT  # noqa: E402
from learnloop.db.table_roles import TABLE_ROLES, TableRole  # noqa: E402
from learnloop.substrate.rebuild_orchestrator import (  # noqa: E402
    derived_table_owners,
    validate_replayer_registry,
)


COMMIT = subprocess.check_output(
    ["git", "log", "-1", "--format=%H"], cwd=REPOSITORY_ROOT, text=True
).strip()
COMMIT_TIMESTAMP = subprocess.check_output(
    ["git", "log", "-1", "--format=%cI"], cwd=REPOSITORY_ROOT, text=True
).strip()
VERIFIED_DATE = "2026-08-18"
SCHEMA_HEAD = 158


DOMAIN_DESCRIPTIONS: dict[str, str] = {
    "schema-and-change": "schema evolution, reviewed content changes, recovery intents, and governed parameters",
    "attempts-and-measurement": "attempt capture, grading, measurement, and evidence authority",
    "learner-state": "learner beliefs, mastery, recall, and capability projections",
    "diagnosis": "diagnostic probes, causal attribution, misconceptions, and repair evidence",
    "scheduling": "queue selection, sessions, controller decisions, and policy evaluation",
    "activity-substrate": "stable activity identity, versions, exposures, lineage, and lifecycle",
    "sources-and-ingest": "source acquisition, normalized source IR, synthesis, and durable ingest work",
    "reader": "reader rendering, annotations, capture, progress, and source-object interaction",
    "tutor-and-remediation": "questions, tutoring, remediation, and practice-supply workflows",
    "goals-and-exams": "goals, forecasts, exams, and cold certification",
    "curriculum": "curricular commitments, depth progression, blueprints, and golden-path runs",
    "operations": "maintenance, generic observations, and optional generated media",
}


# The final clause is deliberately about an operational outcome, not a topic.
# It gives the family heuristic somewhere concrete to land when a migration did
# not provide a table-specific prose comment.
DOMAIN_OUTCOMES: dict[str, str] = {
    "schema-and-change": "schema changes and reviewed mutations remain reproducible and auditable",
    "attempts-and-measurement": "an attempt can be graded, replayed, and traced back to the evidence that changed learner state",
    "learner-state": "learner-facing mastery and capability decisions use a reproducible evidence projection",
    "diagnosis": "diagnostic selection and repair can distinguish competing explanations instead of guessing from a score",
    "scheduling": "queue and controller decisions can resume safely and explain why an activity was selected",
    "activity-substrate": "activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes",
    "sources-and-ingest": "canonical-source work can be retried without losing provenance or silently changing its input set",
    "reader": "reader interactions remain anchored to durable source content as extraction and rendering evolve",
    "tutor-and-remediation": "tutor and repair work can be resumed, reviewed, and connected to subsequent evidence",
    "goals-and-exams": "goal progress and held-out certification remain tied to the contract and evidence that produced them",
    "curriculum": "curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity",
    "operations": "maintenance and optional operational work remains inspectable without becoming learner-state authority",
}


ROLE_OUTCOMES: dict[TableRole, str] = {
    TableRole.RAW_LEDGER: "It supplies replay-stable input rather than a disposable cache.",
    TableRole.DERIVED: "Its current rows may be cleared and reconstructed by the registered projection owner.",
    TableRole.RECEIPT: "It preserves the decision trail and is never cleared by derived-state rebuilds.",
    TableRole.WORKFLOW: "It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence.",
    TableRole.COMPAT: "It keeps an older vault or replay contract readable while new writes use the refactored path.",
}


PURPOSE_OVERRIDES: dict[str, str] = {
    "schema_migrations": "Records exactly which numbered SQL migrations have been applied to this database.",
    "practice_attempts": "Stores the authoritative learner-attempt ledger used by grading, replay, diagnosis, and scheduling.",
    "learning_object_mastery": "Materializes the current per-learning-object mastery posterior for learner-facing decisions.",
    "facet_recall_state": "Materializes canonical per-facet recall evidence and uncertainty for the current knowledge model.",
    "evidence_facet_recall_state": "Preserves the pre-canonical learning-object-scoped facet recall projection for old vaults.",
    "activity_card_state": "Stores authoritative scheduling state for the newer card-lineage substrate, including its co-located review stream.",
    "practice_item_state": "Preserves the still-used historical practice-item scheduling seam while card state remains a partial successor.",
    "attempt_surprise": "Materializes per-attempt Bayesian surprise and follow-up gate diagnostics.",
    "ability_transition_events": "Materializes the replayed ability-state transition attributed to each attempt.",
    "item_parameter_state": "Materializes learned item-parameter state reconstructed from attempt evidence.",
    "learning_outcome_labels": "Materializes replayed outcome labels consumed by learner and scheduling views.",
    "practice_item_quality_state": "Materializes suspicion and quality state inferred from the attempt history.",
    "facet_capability_evidence": "Materializes canonical evidence contributions from facets into capabilities.",
    "capability_residual_state": "Materializes capability residuals after canonical facet evidence has been projected.",
    "subject_identifiability_watermarks": "Materializes whether a subject has enough independent evidence to identify its learner state.",
    "derived_state_rebuilds": "Records each explicit derived-state rebuild and the algorithm/projection boundaries used.",
    "ingest_batches": "Tracks a user-visible durable batch of source-pipeline work.",
    "ingest_jobs": "Tracks individual leased, retryable jobs within an ingest batch.",
    "ingest_job_dependencies": "Records prerequisite edges between durable ingest jobs.",
    "apply_intents": "Provides write-ahead recovery state for multi-file proposal application.",
    "agent_runs": "Records AI/provider run provenance, status, and usage identity without making provider output authoritative by itself.",
    "capability_aliases": "Maps legacy capability names to their canonical registry identity so old evidence remains interpretable after vocabulary changes.",
    "source_artifacts": "Identifies an acquired canonical source independently from any one revision or extraction.",
    "source_revisions": "Records immutable revisions of canonical sources and their content identity.",
    "source_document_blocks": "Stores normalized block-level source IR produced by an extraction run.",
    "source_document_units": "Stores normalized semantic units assembled from source blocks.",
    "source_exam_profiles": "Retains a dormant proposed cache of aggregated exam profiles; retirement remains owner-gated.",
    "source_locator_schemes": "Retains dormant locator-to-scheme detection state; retirement remains owner-gated.",
    "learner_theta": "Retains the legacy IRT theta table for compatibility and telemetry; it is not the canonical learner projection.",
    "controller_shadow_predictions": "Stores non-authoritative controller predictions; a schema CHECK fixes authority to 'none'.",
    "controller_prequential_reports": "Stores delayed evaluation reports over controller shadow predictions.",
    "shadow_component_events": "Records the lifecycle of deliberately firewalled shadow scoring components.",
    "queue_state": "Stores the mutable practice queue head and its workflow position.",
    "sessions": "Tracks learning-session lifecycle state.",
    "session_checkpoints": "Tracks recoverable checkpoints within a learning session.",
    "learner_claims": "Stores learner-supplied prior claims, including the optional initialization-wizard claim.",
    "goal_contract_versions": "Stores immutable goal-contract versions.",
    "goal_contract_heads": "Points workflow consumers at the current goal-contract version.",
    "exam_sessions": "Tracks a held-out exam session from reservation through completion.",
    "exam_answers": "Stores answers submitted within an exam session.",
    "content_events": "Records accepted content lifecycle changes independently from the mutable YAML files.",
    "proposed_patches": "Tracks an AI- or user-originated reviewed content proposal.",
    "proposed_patch_items": "Tracks individually reviewable operations within a proposed patch.",
    "change_batches": "Groups accepted content mutations into an auditable application unit.",
    "maintenance_notices": "Stores actionable maintenance items surfaced by operational checks.",
    "observation_templates": "Stores reusable schemas for manually recorded observations.",
    "observation_events": "Stores observations captured through registered observation templates.",
    "concept_animations": "Tracks requested and rendered concept-animation artifacts.",
}


STATUS_OVERRIDES: dict[str, tuple[str, str]] = {
    "practice_item_state": ("active-historical-seam", "Still read and written while activity_card_state is only a partial successor."),
    "controller_shadow_predictions": ("dormant-shadow", "Executable telemetry only; schema-enforced authority is always none."),
    "controller_prequential_reports": ("dormant-shadow", "Evaluation over shadow telemetry; it has no live selection authority."),
    "shadow_component_events": ("dormant-shadow", "Deliberately firewalled component lifecycle telemetry."),
    "source_exam_profiles": ("dormant-owner-gated", "No live caller was established; telemetry and owner review gate any retirement."),
    "source_locator_schemes": ("dormant-owner-gated", "No live caller was established; telemetry and owner review gate any retirement."),
    "learner_theta": ("dormant-owner-gated", "Legacy state is retained pending decisive production-vault telemetry."),
}


def yaml_scalar(value: Any) -> str:
    """JSON scalars are valid YAML scalars and avoid hand-rolled escaping."""

    return json.dumps(value, ensure_ascii=False)


def frontmatter(
    *,
    title: str,
    status: str,
    tags: Iterable[str],
    source_paths: Iterable[str],
    extra: dict[str, Any] | None = None,
    aliases: Iterable[str] = (),
) -> str:
    lines = [
        "---",
        f"title: {yaml_scalar(title)}",
        f"status: {yaml_scalar(status)}",
        'doc_version: "1.0"',
        'architecture_version: "post-refactor"',
        f"source_commit: {yaml_scalar(COMMIT)}",
        f"source_commit_timestamp: {yaml_scalar(COMMIT_TIMESTAMP)}",
        f"last_verified: {yaml_scalar(VERIFIED_DATE)}",
    ]
    alias_values = list(dict.fromkeys(aliases))
    if alias_values:
        lines.append("aliases:")
        lines.extend(f"  - {yaml_scalar(value)}" for value in alias_values)
    if extra:
        for key, value in extra.items():
            lines.append(f"{key}: {yaml_scalar(value)}")
    lines.append("source_paths:")
    lines.extend(f"  - {yaml_scalar(value)}" for value in dict.fromkeys(source_paths))
    lines.append("tags:")
    lines.extend(f"  - {yaml_scalar(value)}" for value in dict.fromkeys(tags))
    lines.append("---")
    return "\n".join(lines)


def table_domain(table: str) -> str:
    """Assign each table to one navigational family, not an ownership claim."""

    if table.startswith(("activity_", "card_lineage", "surface_fingerprint", "soft_kinship", "retirement_records")):
        return "activity-substrate"
    if table.startswith(("source_", "synthesis_", "ingest_", "entity_source", "notation_mapping", "apply_intents")):
        return "sources-and-ingest"
    if table.startswith(("reader_", "canonical_mapping")):
        return "reader"
    if table.startswith(("probe_", "causal_", "diagnostic_", "misconception", "coldness_", "discrimination_", "contrast_pair", "error_hunt", "unresolved_cause", "persona_realism")):
        return "diagnosis"
    if table.startswith(("scheduler_", "controller_", "attention_", "session", "queue_state", "decision_features", "policy_experiment", "familiarity_kernel", "shadow_component", "composed_selector")):
        return "scheduling"
    if table.startswith(("commitment", "depth_", "task_blueprint", "golden_path", "progression_", "angle_inventor", "p2_ladder", "lapse_episode", "family_evidence", "target_exemplar")):
        return "curriculum"
    if table.startswith(("goal_", "exam_", "forecast", "certification_", "cold_measurement")):
        return "goals-and-exams"
    if table.startswith(("question_", "remediation_", "failure_triage", "rung_variant", "followup_task", "missing_vocabulary")):
        return "tutor-and-remediation"
    if table.startswith(("learner_", "learning_object_mastery", "learning_outcome", "facet_", "evidence_facet", "capability_", "subject_identifiability", "practice_item_quality", "lo_probe_state", "hypothesis_sets", "intervention_needs")):
        return "learner-state"
    if table.startswith(("practice_attempt", "grading_", "grader_", "grade_", "raw_grade", "attempt_", "error_events", "measurement_", "outcome_schema", "calibration_stream", "reveal_events", "trace_exercised", "followup_ratings")):
        return "attempts-and-measurement"
    if table.startswith(("proposed_", "change_batches", "content_events", "parameter_", "fitted_parameters", "item_parameter", "derived_state", "schema_migrations", "agent_runs", "assessment_contract")):
        return "schema-and-change"
    return "operations"


def functionality_status(table: str, role: TableRole) -> tuple[str, str]:
    if table in STATUS_OVERRIDES:
        return STATUS_OVERRIDES[table]
    if role is TableRole.COMPAT:
        return (
            "legacy-preserved",
            "Frozen compatibility state remains readable for older vaults and is not a deletion candidate.",
        )
    return (
        "active",
        "The table participates in a current persistence, audit, projection, or workflow contract.",
    )


TABLE_ACTIONS: tuple[tuple[str, str], ...] = (
    ("_lifecycle_events", "Preserves the ordered lifecycle transitions for {subject}"),
    ("_decision_receipts", "Freezes each decision, its inputs, and its reason for {subject}"),
    ("_submission_receipts", "Makes client submission of {subject} idempotent and auditable"),
    ("_review_events", "Preserves the review and approval history for {subject}"),
    ("_events", "Preserves an append-only chronology of {subject}"),
    ("_versions", "Pins immutable versions of {subject}"),
    ("_state", "Maintains the decision-facing current projection for {subject}"),
    ("_receipts", "Freezes the inputs and outcome of each {subject} decision"),
    ("_jobs", "Coordinates leased, retryable work for {subject}"),
    ("_requests", "Queues a durable, retryable request for {subject}"),
    ("_dependencies", "Declares prerequisite edges for {subject}"),
    ("_outcomes", "Records the measured outcome and lineage for {subject}"),
    ("_reports", "Captures an inspectable analysis result for {subject}"),
    ("_predictions", "Records predictions for {subject} before their outcomes are known"),
    ("_samples", "Records sampled observations and their inclusion context for {subject}"),
    ("_runs", "Tracks one execution, input identity, and result for {subject}"),
    ("_sessions", "Tracks the resumable lifecycle of {subject}"),
    ("_candidates", "Holds candidates for {subject} while policy selects or reviews one"),
    ("_observations", "Records observations used to evaluate {subject}"),
    ("_templates", "Versions reusable definitions that generate or validate {subject}"),
    ("_artifacts", "Identifies durable output artifacts produced for {subject}"),
    ("_manifests", "Pins the complete input identity for {subject}"),
    ("_mappings", "Maps external or historical identities into {subject}"),
    ("_links", "Preserves explicit relationship edges for {subject}"),
    ("_assignments", "Records governed assignments for {subject}"),
    ("_resolutions", "Records explicit resolutions of {subject} without erasing the original evidence"),
    ("_corrections", "Appends governed corrections to {subject} without rewriting history"),
    ("_needs", "Queues an identified supply gap for {subject}"),
    ("_opportunities", "Records the denominator of available opportunities for {subject}"),
    ("_policies", "Pins the policy definition used for {subject}"),
)


def _purpose_subject(table: str) -> str:
    for suffix, _action in TABLE_ACTIONS:
        if table.endswith(suffix):
            stem = table[: -len(suffix)]
            return stem.replace("_", " ") or table.replace("_", " ")
    # A final plural ``s`` usually denotes the stable identity/home table.
    stem = table[:-1] if table.endswith("s") and not table.endswith("ss") else table
    return stem.replace("_", " ")


@functools.cache
def table_column_names(table: str) -> tuple[str, ...]:
    connection = sqlite3.connect(f"file:{SCHEMA_PATH}?mode=ro", uri=True)
    try:
        return tuple(str(row[1]) for row in connection.execute(f'PRAGMA table_info("{table}")'))
    finally:
        connection.close()


def purpose_columns(columns: Iterable[str]) -> list[str]:
    """Choose the columns that best explain what one row connects or decides."""

    values = list(columns)
    priority_suffixes = (
        "_id",
        "_kind",
        "_type",
        "_status",
        "_version",
        "_outcome",
        "_decision",
        "_reason",
        "_score",
        "_hash",
    )
    ignored = {
        "id",
        "created_at",
        "updated_at",
        "applied_at",
        "completed_at",
        "ended_at",
    }
    ranked = [
        value
        for suffix in priority_suffixes
        for value in values
        if value not in ignored and value.endswith(suffix)
    ]
    if len(ranked) < 3:
        ranked.extend(
            value
            for value in values
            if value not in ignored
            and value not in ranked
            and not value.endswith("_json")
        )
    return list(dict.fromkeys(ranked))[:3]


def table_purpose(
    table: str,
    domain: str,
    *,
    columns: Iterable[str] | None = None,
    role: TableRole | None = None,
) -> str:
    if table in PURPOSE_OVERRIDES:
        selected = purpose_columns(columns or table_column_names(table))
        bindings = ""
        if selected:
            rendered = ", ".join(f"`{column}`" for column in selected)
            bindings = f" Rows bind {rendered}, making the operational relationship explicit."
        return (
            f"{PURPOSE_OVERRIDES[table]} {ROLE_OUTCOMES[role or TABLE_ROLES[table]]}"
            f"{bindings}"
        )
    subject = _purpose_subject(table)
    action = f"Gives {subject} a stable database identity"
    for suffix, candidate in TABLE_ACTIONS:
        if table.endswith(suffix):
            action = candidate.format(subject=subject)
            break
    selected = purpose_columns(columns or table_column_names(table))
    bindings = ""
    if selected:
        rendered = ", ".join(f"`{column}`" for column in selected)
        bindings = f" Rows bind {rendered}, making the operational relationship explicit."
    role_clause = ROLE_OUTCOMES[role or TABLE_ROLES[table]]
    return (
        f"{action} so {DOMAIN_OUTCOMES[domain]}. {role_clause}{bindings}"
    )


def migration_files() -> list[Path]:
    return sorted(MIGRATIONS_ROOT.glob("*.sql"), key=lambda path: int(path.name.split("_", 1)[0]))


MIGRATION_TEXT = {path: path.read_text(encoding="utf-8") for path in migration_files()}


def migrations_mentioning(table: str) -> list[Path]:
    pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(table)}(?![A-Za-z0-9_])", re.IGNORECASE)
    return [path for path, text in MIGRATION_TEXT.items() if pattern.search(text)]


def introducing_migration(table: str, candidates: list[Path]) -> Path:
    create = re.compile(
        rf"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"`\[]?{re.escape(table)}[\"`\]]?\b",
        re.IGNORECASE,
    )
    for path in candidates:
        if create.search(MIGRATION_TEXT[path]):
            return path
    return candidates[0]


def migration_comment(path: Path, table: str) -> str | None:
    text = MIGRATION_TEXT[path]
    match = re.search(
        rf"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"`\[]?{re.escape(table)}[\"`\]]?\b",
        text,
        re.IGNORECASE,
    )
    if match is None:
        return None
    prior = text[: match.start()].splitlines()
    comments: list[str] = []
    blank_seen = False
    for line in reversed(prior):
        stripped = line.strip()
        if stripped.startswith("--"):
            comments.append(stripped.removeprefix("--").strip())
            blank_seen = False
            continue
        if not stripped and not blank_seen:
            blank_seen = True
            continue
        break
    result = " ".join(reversed(comments)).strip()
    return result if 12 <= len(result) <= 800 else None


def python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


SOURCE_FILES = python_files(SRC_ROOT)
TEST_FILES = python_files(REPOSITORY_ROOT / "tests")
SOURCE_TEXT = {path: path.read_text(encoding="utf-8", errors="replace") for path in SOURCE_FILES}
TEST_TEXT = {path: path.read_text(encoding="utf-8", errors="replace") for path in TEST_FILES}


def repo_relative(path: Path) -> str:
    return path.relative_to(REPOSITORY_ROOT).as_posix()


def repository_methods_by_table() -> dict[str, list[str]]:
    path = REPOSITORY_ROOT / "src" / "learnloop" / "db" / "repositories.py"
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    tree = ast.parse(text)
    result: dict[str, list[str]] = defaultdict(list)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        segment = "\n".join(lines[node.lineno - 1 : node.end_lineno])
        for table in TABLE_ROLES:
            if re.search(rf"(?<![A-Za-z0-9_]){re.escape(table)}(?![A-Za-z0-9_])", segment):
                result[table].append(node.name)
    return {table: sorted(set(names)) for table, names in result.items()}


REPOSITORY_METHODS = repository_methods_by_table()


def files_calling_methods(texts: dict[Path, str], methods: Iterable[str]) -> list[Path]:
    method_list = list(methods)
    if not method_list:
        return []
    pattern = re.compile(r"\.\s*(?:" + "|".join(re.escape(name) for name in method_list) + r")\s*\(")
    return sorted(path for path, text in texts.items() if pattern.search(text))


def files_mentioning(texts: dict[Path, str], table: str) -> list[Path]:
    pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(table)}(?![A-Za-z0-9_])")
    return sorted(path for path, text in texts.items() if pattern.search(text))


def sql_access_modes(table: str, paths: Iterable[Path]) -> tuple[list[Path], list[Path]]:
    quoted = rf"[\"'`]?{re.escape(table)}[\"'`]?"
    read_pattern = re.compile(rf"\b(?:FROM|JOIN)\s+{quoted}\b", re.IGNORECASE)
    write_pattern = re.compile(rf"\b(?:INSERT\s+INTO|REPLACE\s+INTO|UPDATE|DELETE\s+FROM)\s+{quoted}\b", re.IGNORECASE)
    readers: list[Path] = []
    writers: list[Path] = []
    for path in paths:
        text = SOURCE_TEXT[path]
        if read_pattern.search(text):
            readers.append(path)
        if write_pattern.search(text):
            writers.append(path)
    return readers, writers


def sqlite_metadata(connection: sqlite3.Connection, table: str) -> dict[str, Any]:
    columns = [dict(row) for row in connection.execute(f'PRAGMA table_info("{table}")')]
    foreign_keys = [dict(row) for row in connection.execute(f'PRAGMA foreign_key_list("{table}")')]
    indexes: list[dict[str, Any]] = []
    for row in connection.execute(f'PRAGMA index_list("{table}")'):
        item = dict(row)
        name = str(item["name"])
        item["columns"] = [
            str(part["name"])
            for part in connection.execute(f'PRAGMA index_info("{name}")')
            if part["name"] is not None
        ]
        indexes.append(item)
    triggers = [
        dict(row)
        for row in connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='trigger' AND tbl_name=? ORDER BY name",
            (table,),
        )
    ]
    ddl_row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return {
        "columns": columns,
        "foreign_keys": foreign_keys,
        "indexes": indexes,
        "triggers": triggers,
        "ddl": str(ddl_row[0]),
    }


def markdown_list(values: Iterable[str], *, empty: str = "None found by exact static reference scan.") -> str:
    items = list(dict.fromkeys(values))
    if not items:
        return empty
    return "\n".join(f"- `{item}`" for item in items)


def table_wikilink(table: str, label: str | None = None, *, in_table: bool = False) -> str:
    """Return an unambiguous table-note link.

    Module notes can legitimately share a stem with a SQL table.  Path-qualified
    links keep Obsidian from choosing whichever duplicate it indexed first.
    Markdown table cells also require an escaped alias separator.
    """

    target = f"Reference/Database/Tables/{table}"
    if label is None:
        label = table
    separator = "\\|" if in_table else "|"
    return f"[[{target}{separator}{label}]]"


def table_note(connection: sqlite3.Connection, table: str) -> str:
    role = TABLE_ROLES[table]
    domain = table_domain(table)
    status, status_reason = functionality_status(table, role)
    metadata = sqlite_metadata(connection, table)
    migration_hits = migrations_mentioning(table)
    introduced = introducing_migration(table, migration_hits)
    comment = migration_comment(introduced, table)
    direct_sources = files_mentioning(SOURCE_TEXT, table)
    repo_methods = REPOSITORY_METHODS.get(table, [])
    method_callers = files_calling_methods(SOURCE_TEXT, repo_methods)
    direct_tests = files_mentioning(TEST_TEXT, table)
    method_tests = files_calling_methods(TEST_TEXT, repo_methods)
    readers, writers = sql_access_modes(table, direct_sources)
    source_paths = [
        "src/learnloop/db/table_roles.py",
        repo_relative(introduced),
        *[repo_relative(path) for path in direct_sources[:8]],
        *[repo_relative(path) for path in method_callers[:5]],
    ]
    if role is TableRole.DERIVED:
        source_paths.append("src/learnloop/substrate/rebuild_orchestrator.py")
    owners = derived_table_owners().get(table, ())
    role_text = {
        TableRole.RAW_LEDGER: "Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.",
        TableRole.DERIVED: "Clearable projection reconstructed by exactly one registered replayer.",
        TableRole.RECEIPT: "Historical audit/decision receipt. It is preserved and never rebuilt.",
        TableRole.WORKFLOW: "Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.",
        TableRole.COMPAT: "Frozen compatibility state retained for old vaults or an incomplete replacement seam.",
    }[role]
    callout_kind = "warning" if status != "active" else "info"
    lines = [
        frontmatter(
            title=table,
            status="current",
            aliases=[f"state.sqlite {table}", f"table {table}"],
            tags=[
                "learnloop/database/table",
                f"learnloop/database/role/{role.value.replace('_', '-')}",
                f"learnloop/status/{status}",
                f"learnloop/domain/{domain}",
            ],
            source_paths=source_paths,
            extra={
                "schema_head": SCHEMA_HEAD,
                "table_name": table,
                "table_role": role.value,
                "functionality_status": status,
                "domain_family": domain,
                "introduced_in": introduced.name,
                "generated": True,
            },
        ),
        "",
        f"# `{table}`",
        "",
        f"> [!{callout_kind}] {status.replace('-', ' ').title()}",
        f"> {status_reason}",
        "",
        "## Why it exists",
        "",
        table_purpose(
            table,
            domain,
            columns=[str(column["name"]) for column in metadata["columns"]],
            role=role,
        ) + " ^table-purpose",
        "",
    ]
    if comment:
        lines.extend(
            [
                "> [!quote] Migration design note",
                f"> {comment}",
                "",
            ]
        )
    lines.extend(
        [
        f"It belongs to the **{domain.replace('-', ' ')}** navigation family. The family context lives in [[Database Catalog#{domain.replace('-', ' ').title()}]]. Its persistence behavior follows [[Table Roles#{role.value.replace('_', ' ').title()}]].",
            "",
            "## Persistence and lifecycle contract",
            "",
            f"- **Role:** `{role.value}` — {role_text}",
            f"- **Functionality status:** `{status}`.",
            f"- **Introduced by:** `{repo_relative(introduced)}`.",
            f"- **Schema touched by:** {', '.join(f'`{path.name}`' for path in migration_hits)}.",
            f"- **Rebuild owner:** {', '.join(f'`{owner}`' for owner in owners) if owners else 'none; this table is preserved by the rebuild umbrella.'}",
            "",
            "For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle",
            "",
            "## Columns",
            "",
            "| Column | SQLite type | Required | Default | Key | Operational reading |",
            "|---|---|---:|---|---|---|",
        ]
    )
    fk_by_column = {str(item["from"]): item for item in metadata["foreign_keys"]}
    for column in metadata["columns"]:
        name = str(column["name"])
        key = "PRIMARY KEY" if int(column["pk"]) else ""
        if name in fk_by_column:
            fk = fk_by_column[name]
            target = f"{fk['table']}.{fk['to']}"
            key = f"{key}; FK → {table_wikilink(str(fk['table']), target, in_table=True)}".strip("; ")
        operational = "JSON-encoded structured payload" if name.endswith("_json") else "Application-validated soft reference" if name.endswith("_id") and name not in fk_by_column and not int(column["pk"]) else "Timestamp (ISO-8601 UTC text)" if name.endswith("_at") else "Stored value"
        default = "—" if column["dflt_value"] is None else f"`{column['dflt_value']}`"
        lines.append(
            f"| `{name}` | `{column['type'] or 'ANY'}` | {'yes' if int(column['notnull']) else 'no'} | {default} | {key or '—'} | {operational} |"
        )
    lines.extend(["", "## Relationships and access paths", ""])
    if metadata["foreign_keys"]:
        lines.append("Declared SQLite foreign keys:")
        lines.append("")
        for fk in metadata["foreign_keys"]:
            target_label = f"`{fk['table']}.{fk['to']}`"
            target_link = table_wikilink(str(fk["table"]), target_label)
            lines.append(
                f"- `{fk['from']}` → {target_link}; on delete `{fk['on_delete']}`, on update `{fk['on_update']}`."
            )
    else:
        lines.append(
            "No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams."
        )
    lines.extend(["", "Indexes and uniqueness:", ""])
    if metadata["indexes"]:
        for index in metadata["indexes"]:
            columns = ", ".join(f"`{value}`" for value in index["columns"]) or "expression/partial index"
            lines.append(
                f"- `{index['name']}` on {columns}{' (unique)' if int(index['unique']) else ''}."
            )
    else:
        lines.append("- No secondary index is declared beyond any rowid/primary-key storage.")
    if metadata["triggers"]:
        lines.extend(["", "Database triggers:", ""])
        for trigger in metadata["triggers"]:
            lines.append(f"- `{trigger['name']}` — schema-enforced lifecycle or immutability constraint.")
    lines.extend(
        [
            "",
            "## Who calls it",
            "",
            "### Repository access surface",
            "",
            markdown_list([f"Repository.{name}()" for name in repo_methods]),
            "",
            "### Direct SQL readers",
            "",
            markdown_list([repo_relative(path) for path in readers]),
            "",
            "### Direct SQL writers",
            "",
            markdown_list([repo_relative(path) for path in writers]),
            "",
            "### Upstream callers of the repository access surface",
            "",
            markdown_list([repo_relative(path) for path in method_callers[:20]]),
            "",
            "> [!note] Static-reference boundary",
            "> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.",
            "",
            "## Tests that define behavior",
            "",
            markdown_list(
                [repo_relative(path) for path in dict.fromkeys([*direct_tests, *method_tests])][:20],
                empty="No table-specific test contains the table name or a detected repository method call. The schema/role invariants are still pinned by `tests/test_migrations.py` and `tests/test_table_roles.py`.",
            ),
            "",
            "Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.",
            "",
            "## Extension and modification guidance",
            "",
            "1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.",
            "2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.",
            "3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.",
            "4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.",
        ]
    )
    if role is TableRole.DERIVED:
        lines.append(
            "5. Update the single owner in `DERIVED_STATE_REPLAYERS`, then prove same-version rebuild equivalence and shadow isolation."
        )
    elif role is TableRole.COMPAT:
        lines.append(
            "5. Compatibility retirement requires production-vault telemetry and an explicit owner decision; code detachment and schema changes are separate gates."
        )
    lines.extend(
        [
            "",
            "## Live schema DDL",
            "",
            "> [!tip] Why keep the DDL here?",
            "> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.",
            "",
            "```sql",
            metadata["ddl"].strip() + ";",
            "```",
            "",
            "## Related notes",
            "",
            f"- [[Database Catalog#{domain.replace('-', ' ').title()}|Sibling tables in this family]]",
            f"- [[Table Roles#{role.value.replace('_', ' ').title()}|{role.value} policy]]",
            "- [[Rebuild Ownership]]",
            "- [[State and Persistence]]",
            "- [[Vault Lifecycle]]",
            "",
        ]
    )
    return "\n".join(lines)


def generate_table_notes() -> dict[str, list[str]]:
    validate_replayer_registry()
    connection = sqlite3.connect(SCHEMA_PATH)
    connection.row_factory = sqlite3.Row
    try:
        actual = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        if actual != set(TABLE_ROLES):
            raise SystemExit(
                f"schema/role mismatch: missing={sorted(set(TABLE_ROLES)-actual)}, extra={sorted(actual-set(TABLE_ROLES))}"
            )
        grouped: dict[str, list[str]] = defaultdict(list)
        for table in sorted(actual):
            grouped[table_domain(table)].append(table)
            (TABLES_ROOT / f"{table}.md").write_text(
                table_note(connection, table), encoding="utf-8"
            )
        return dict(grouped)
    finally:
        connection.close()


def flatten(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    if isinstance(value, dict):
        rows: list[tuple[str, Any]] = []
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(flatten(child, path))
        return rows
    return [(prefix, value)]


def value_type(value: Any) -> str:
    if value is None:
        return "nullable"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return type(value).__name__


def explicit_leaf_paths(raw: dict[str, Any]) -> set[str]:
    return {path for path, _value in flatten(raw)}


CONFIG_SECTION_FUNCTIONS: dict[str, str] = {
    "schema_version": "configuration parsing and one-way compatibility normalization",
    "storage": "vault persistence location resolution",
    "algorithms": "replay and defaults-version selection",
    "evidence": "evidence mass, coverage, correlation, and certification accounting",
    "scheduler": "queue scoring, exploration, surprise, and follow-up selection",
    "goals": "goal-frontier projection",
    "hypothesis": "learner-facing hypothesis cards and re-entry signals",
    "mastery": "difficulty-aware mastery filtering and display",
    "probe": "diagnostic episodes, instruments, calibration, and lifecycle",
    "recall_coverage": "evidence independence, facet coverage, and error-severity computation",
    "facet_diagnostic": "facet failure and uncertainty classification",
    "misconceptions": "misconception resolution and discriminator gates",
    "practice_generation": "target-success bands for generated practice and probes",
    "exam_seeding": "reliability assigned to imported exam evidence",
    "tutor_qa": "tutor question budgets and question-derived diagnostic signals",
    "tutor_promotion": "promotion of learner questions into claims, needs, and practice",
    "teach_back": "teach-back dialogue and evidence limits",
    "rung_variants": "learner-requested easier and harder activity variants",
    "animation": "consented concept-animation generation and sandboxed rendering",
    "ingest": "source acquisition, extraction, media handling, token budgets, and durable workers",
    "ai": "typed provider profiles and task-to-provider routing",
    "capabilities": "optional capability-residual activation and shrinkage",
    "locks": "evidence gates that lock facets and curriculum progress",
    "error_impacts": "error-family severity shaping",
    "fitting": "offline fitting of learner-specific scheduler parameters",
    "trace_evidence": "opportunistic trace evidence and learner-burden limits",
    "diagnostic_augmentation": "multi-sample diagnostic augmentation",
}


LEGACY_CONFIG_PATHS = {
    "probe.attempts_target_default",
    "probe.attempts_target_with_strong_claim",
    "probe.claim_skip_threshold",
    "probe.variance_convergence_threshold",
}


DORMANT_CONFIG_PREFIXES = (
    "probe.shadow.",
    "capabilities.",
)
DORMANT_CONFIG_PATHS = {
    "scheduler.followup.predictive_eig_weight",
    "scheduler.followup.predictive_eig_target_cap",
    "mastery.irt.eb_difficulty_enabled",
    "mastery.irt.b_prior_variance",
    "mastery.irt.b_learning_rate_scale",
    "mastery.irt.b_max_step",
    "mastery.irt.b_var_min",
}


COMPAT_ALIASES_BY_SECTION: dict[str, list[tuple[str, str, str]]] = {
    "ai": [
        ("[codex]", "[ai.providers.codex]", "One-way translation of the retired top-level Codex profile."),
        ("provider type codex_http or http_adapter", "type = http", "Accepted discriminator spellings for older provider profiles."),
        ("provider type openai_compatible", "type = openai_chat", "Accepted older name for the canonical OpenAI chat transport."),
        ("ai.providers.*.auth_mode", "discarded", "Historically parsed but never consumed; it does not survive serialization."),
    ],
    "ingest": [
        ("ingest.audio.provider = openrouter", "ai.providers.openrouter_transcription + ai.routing.transcription", "Moves the legacy audio-provider selector into typed AI routing."),
        ("ingest.budgets.evidence_span_input_tokens", "discarded", "Retired ingestion budget accepted only so old vaults still open."),
    ],
    "probe": [
        ("probe.episode.self_graded_evidence_weight", "discarded", "Retired pre-redesign input; it has no live-policy effect."),
        ("probe.dialogue.max_turns", "discarded", "Retired dialogue spelling; live policy uses planned_turns."),
    ],
    "recall_coverage": [
        ("recall_coverage.facet_recall_prior_pseudo_count", "discarded", "Retired prior knob accepted only during one-way normalization."),
        ("recall_coverage.coverage_epsilon", "discarded", "Retired numeric knob accepted only during one-way normalization."),
    ],
    "error_impacts": [
        ("error_impacts.*.max_sharpening", "recall_coverage.max_error_sharpening", "Legacy location translated only when the canonical key is absent."),
    ],
    "schema_version": [
        ("forecasts", "discarded", "Retired top-level section; forecast behavior no longer reads it."),
        ("cross_lo_propagation", "discarded", "Retired LO-to-LO propagation section; canonical shared-facet state replaces it."),
    ],
}


def config_field_status(path: str) -> tuple[str, str]:
    if path == "probe.hypothesis_set_max_size":
        return (
            "ACTIVE",
            "Kept by the refactor and consumed by current hypothesis construction to cap each live diagnostic hypothesis set.",
        )
    if path in LEGACY_CONFIG_PATHS:
        return (
            "LEGACY",
            "Consumed only by the frozen pre-redesign replay path; live diagnostic policy uses probe.episode.",
        )
    if path.endswith(".lo_mastery_delta"):
        return (
            "COMPAT",
            "Retained for legacy mastery-impact compatibility; current coverage uses local_severity_gain.",
        )
    if path == "ingest.audio.provider":
        return (
            "COMPAT",
            "Raw legacy selector retained for normalization; chat transcription routes through ai.routing.transcription.",
        )
    if path in DORMANT_CONFIG_PATHS or path.startswith(DORMANT_CONFIG_PREFIXES):
        if path.startswith("probe.shadow."):
            reason = "Shadow-only telemetry has no live selection authority."
        elif path.startswith("capabilities."):
            reason = "Capability residuals ship behind residual_activation_enabled=false."
        elif path.startswith("mastery.irt.b_") or path.endswith("eb_difficulty_enabled"):
            reason = "Empirical-Bayes item difficulty ships dark behind eb_difficulty_enabled=false."
        else:
            reason = "Predictive EIG is logged but contributes zero weight in the shipped configuration."
        return "DORMANT", reason
    return (
        "ACTIVE",
        "Declared by the canonical typed configuration; exact runtime consumers are cited when a statically resolvable path exists.",
    )


def humanize_config_words(value: str) -> str:
    replacements = {
        "lo": "learning-object",
        "eig": "expected-information-gain",
        "irt": "item-response",
        "ttl": "time-to-live",
        "llm": "language-model",
        "fsrs": "FSRS",
        "pdf": "PDF",
        "api": "API",
        "mb": "megabytes",
    }
    return " ".join(replacements.get(part, part) for part in value.split("_"))


def config_field_function(path: str, value: Any) -> str:
    parts = path.split(".")
    section = parts[0]
    leaf = parts[-1]
    parent = humanize_config_words(parts[-2]) if len(parts) > 1 else section
    concern = CONFIG_SECTION_FUNCTIONS[section]

    if path == "schema_version":
        return "Selects the accepted learnloop.toml schema and activates one-way normalization for older schema-1 input."
    if path == "storage.sqlite_path":
        return "Locates the vault's SQLite machine-state file relative to the vault root unless an absolute path is supplied."
    if path == "algorithms.algorithm_version":
        return "Pins the replay/defaults namespace so historical evidence is interpreted by the algorithm that produced it."
    if ".attempt_types." in path and leaf == "evidence_mass":
        attempt_type = humanize_config_words(parts[-2])
        return f"Weights how much a {attempt_type} observation contributes to ability, reliability, and certification evidence."
    if ".attempt_types." in path and leaf == "surface_exposure":
        attempt_type = humanize_config_words(parts[-2])
        return f"Overrides the fraction of the item's facet surface counted as examined by a {attempt_type} observation; null inherits evidence_mass."
    if path.startswith("evidence.item_coverage_by_practice_mode."):
        mode = humanize_config_words(leaf)
        return f"Sets fallback facet-surface coverage for a {mode} item when no rubric or explicit evidence weights define coverage."
    if path.startswith("evidence.blueprints.guess_by_format."):
        return f"Sets the chance-success floor for {humanize_config_words(leaf)} responses in blueprint likelihood calculations."
    if path.startswith("ai.routing."):
        return f"Selects the named provider profile that executes the {humanize_config_words(leaf)} AI operation; an empty optional route follows the documented fallback chain."
    if path.startswith("ai.providers."):
        provider = parts[2]
        if leaf == "type":
            return f"Chooses the validated transport adapter used by the {provider} provider profile."
        if leaf == "model":
            return f"Pins the model identifier sent by the {provider} provider profile."
        if leaf == "api_key_env":
            return f"Names the environment variable from which the {provider} adapter reads its secret; the secret is never stored in the vault."
        if leaf.endswith("_path"):
            return f"Sets the {humanize_config_words(leaf[:-5])} endpoint or executable path used by the {provider} adapter when its transport supports it."
        return f"Configures {humanize_config_words(leaf)} for the typed {provider} provider profile."
    if path.startswith("recall_coverage.severity_examples."):
        example = humanize_config_words(parts[2])
        if leaf.startswith("expected_"):
            return f"Declares the expected {humanize_config_words(leaf.removeprefix('expected_'))} for the executable {example} severity example."
        return f"Supplies the {humanize_config_words(leaf)} input used to verify the executable {example} severity example."
    if path.startswith("error_impacts."):
        error = humanize_config_words(parts[1])
        if ".families." in path:
            return f"Sets the legacy {humanize_config_words(leaf)}-family impact recorded for a {error} classification."
        return f"Sets {humanize_config_words(leaf)} applied when an attempt is classified as {error}."
    if path.startswith("evidence.certification.group_budgets."):
        return f"Overrides the certification budget for correlation group {leaf}; absent groups inherit attempt evidence mass."
    if leaf == "enabled" or leaf.endswith("_enabled") or leaf.startswith("apply_") or isinstance(value, bool):
        feature = leaf.removesuffix("_enabled").removeprefix("apply_")
        if feature == "enabled":
            feature = parent
        return f"Turns {humanize_config_words(feature)} behavior on or off within {concern}."
    if leaf.endswith("_weight") or leaf.endswith("_multiplier") or leaf.endswith("_discount"):
        base = re.sub(r"_(?:weight|multiplier|discount)$", "", leaf)
        return f"Scales the contribution of {humanize_config_words(base)} in {concern}."
    if "threshold" in leaf or leaf.startswith(("tau_", "theta_", "cut_")):
        base = re.sub(r"^(?:tau|theta|cut)_", "", leaf).replace("_threshold", "")
        return f"Sets the decision cutoff for {humanize_config_words(base)} in {concern}."
    if leaf.endswith(("_cap", "_limit", "_max", "_maximum")) or leaf.startswith("max_"):
        base = re.sub(r"(^max_|_(?:cap|limit|max|maximum)$)", "", leaf)
        return f"Caps {humanize_config_words(base)} allowed by {concern}."
    if leaf.endswith("_min") or leaf.startswith("min_") or "minimum" in leaf:
        base = re.sub(r"(^min_|_(?:min|minimum)$)", "", leaf).replace("minimum_", "")
        return f"Sets the minimum {humanize_config_words(base)} required by {concern}."
    if leaf.endswith(("_seconds", "_minutes", "_days")):
        unit = leaf.rsplit("_", 1)[-1]
        base = leaf[: -(len(unit) + 1)]
        return f"Sets the {humanize_config_words(base)} duration in {unit} for {concern}."
    if leaf.endswith("_window") or "window" in leaf:
        return f"Sets the rolling {humanize_config_words(leaf)} used by {concern}."
    if leaf.endswith("_rate"):
        return f"Sets the rate of {humanize_config_words(leaf.removesuffix('_rate'))} used by {concern}."
    if leaf.endswith(("_variance", "_probability", "_ratio", "_fraction", "_share")):
        return f"Sets the {humanize_config_words(leaf)} used by {concern}."
    if leaf.endswith("_model") or leaf == "model":
        return f"Selects the model implementation or model identifier used for {concern}."
    if leaf.endswith("_path"):
        return f"Locates the {humanize_config_words(leaf.removesuffix('_path'))} resource used by {concern}."
    if leaf.endswith("_version"):
        return f"Pins the {humanize_config_words(leaf.removesuffix('_version'))} contract used by {concern}."
    return f"Controls {humanize_config_words(leaf)} in {concern}, using the typed value shown here as the fresh-vault default."


CONFIG_SCHEMA_SOURCE = REPOSITORY_ROOT / "src" / "learnloop" / "config" / "schema.py"


@functools.cache
def effective_config_model() -> LearnLoopConfig:
    return LearnLoopConfig.model_validate(tomllib.loads(DEFAULT_CONFIG_TEXT))


@functools.cache
def effective_config_paths() -> tuple[str, ...]:
    payload = effective_config_model().model_dump(mode="json", exclude_none=False)
    return tuple(path for path, _value in flatten(payload))


@functools.cache
def schema_field_lines() -> dict[tuple[str, str], int]:
    """Index exact Pydantic field declarations by declaring class and field."""

    tree = ast.parse(CONFIG_SCHEMA_SOURCE.read_text(encoding="utf-8"))
    result: dict[tuple[str, str], int] = {}
    for class_node in (node for node in tree.body if isinstance(node, ast.ClassDef)):
        for statement in class_node.body:
            if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                result[(class_node.name, statement.target.id)] = statement.lineno
    return result


def _declaring_field_line(model_type: type[Any], field_name: str) -> int | None:
    lines = schema_field_lines()
    for candidate in model_type.__mro__:
        line = lines.get((candidate.__name__, field_name))
        if line is not None:
            return line
    return None


@functools.cache
def schema_declaration_reference(path: str) -> str:
    """Return the declaration that defines this exact field or dynamic container.

    Effective configuration contains dynamic dictionary members such as provider
    names and error families.  For those members the authoritative declaration
    is the closest typed dictionary field, never an unrelated declaration that
    happens to share the leaf token.
    """

    current: Any = effective_config_model()
    best_line: int | None = None
    for segment in path.split("."):
        model_fields = getattr(type(current), "model_fields", None)
        if isinstance(model_fields, dict):
            if segment in model_fields:
                line = _declaring_field_line(type(current), segment)
                if line is None:
                    raise RuntimeError(
                        f"no schema declaration for {type(current).__name__}.{segment}"
                    )
                best_line = line
            try:
                current = getattr(current, segment)
            except AttributeError as exc:
                raise RuntimeError(f"cannot traverse effective config path {path}") from exc
            continue
        if isinstance(current, dict):
            if segment not in current:
                raise RuntimeError(f"dynamic config key {segment!r} is absent in {path}")
            current = current[segment]
            continue
        raise RuntimeError(f"cannot traverse effective config path {path} at {segment}")
    if best_line is None:
        raise RuntimeError(f"no typed schema container found for {path}")
    return f"{repo_relative(CONFIG_SCHEMA_SOURCE)}:{best_line}"


@functools.cache
def _model_annotation_prefixes() -> dict[str, tuple[str, ...]]:
    """Map instantiated config model classes to an unambiguous dotted prefix."""

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
                # A dictionary's concrete keys are data, not part of its model
                # annotation.  ``*`` lets a typed submodel consumer support each
                # effective key without pretending it named one particular key.
                visit(child, (*prefix, "*"))

    visit(effective_config_model(), ())
    result: dict[str, tuple[str, ...]] = {}
    for class_name, prefixes in found.items():
        if len(prefixes) == 1:
            result[class_name] = next(iter(prefixes))
    return result


def _annotation_prefix(annotation: ast.expr | None) -> tuple[str, ...] | None:
    if annotation is None:
        return None
    prefixes = _model_annotation_prefixes()
    candidates: set[tuple[str, ...]] = set()
    if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
        for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", annotation.value):
            if token in prefixes:
                candidates.add(prefixes[token])
    else:
        for node in ast.walk(annotation):
            name = node.id if isinstance(node, ast.Name) else None
            if name in prefixes:
                candidates.add(prefixes[name])
    return next(iter(candidates)) if len(candidates) == 1 else None


def _expression_config_path(
    node: ast.AST,
    aliases: dict[str, tuple[str, ...]],
) -> tuple[str, ...] | None:
    if isinstance(node, ast.Name):
        return aliases.get(node.id)
    if isinstance(node, ast.Attribute):
        base = _expression_config_path(node.value, aliases)
        if base is not None:
            return (*base, node.attr)
        # LoadedVault and sidecar context objects expose the one canonical
        # ``.config`` root.  No leaf match is accepted until the complete path
        # beneath this marker equals a real effective field.
        if node.attr == "config":
            return ()
        return None
    if isinstance(node, ast.Subscript):
        base = _expression_config_path(node.value, aliases)
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
        base = _expression_config_path(node.args[0], aliases)
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
        base = _expression_config_path(node.func.value, aliases)
        if base is None:
            return None
        key = node.args[0]
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            return (*base, key.value)
        return (*base, "*")
    return None


def _nodes_in_scope(scope: ast.AST) -> list[ast.AST]:
    """Return nodes in one lexical scope, excluding nested definitions."""

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


def _scope_config_patterns(scope: ast.AST) -> set[tuple[tuple[str, ...], int]]:
    nodes = _nodes_in_scope(scope)
    aliases: dict[str, tuple[str, ...]] = {}
    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
        arguments = [*scope.args.posonlyargs, *scope.args.args, *scope.args.kwonlyargs]
        if scope.args.vararg is not None:
            arguments.append(scope.args.vararg)
        if scope.args.kwarg is not None:
            arguments.append(scope.args.kwarg)
        for argument in arguments:
            prefix = _annotation_prefix(argument.annotation)
            if prefix is not None:
                aliases[argument.arg] = prefix

    # Resolve local aliases such as ``followup_config = vault.config.scheduler.followup``.
    # A small fixed point handles aliases of aliases without making leaf-token guesses.
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
                resolved = _expression_config_path(value, aliases)
                if resolved is not None:
                    for target in targets:
                        if isinstance(target, ast.Name) and aliases.get(target.id) != resolved:
                            aliases[target.id] = resolved
                            changed = True
            if isinstance(node, (ast.For, ast.AsyncFor)) and isinstance(node.iter, ast.Call):
                call = node.iter
                if isinstance(call.func, ast.Attribute) and call.func.attr in {"items", "values"}:
                    container = _expression_config_path(call.func.value, aliases)
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
            resolved = _expression_config_path(node, aliases)
            if resolved:
                patterns.add((resolved, node.lineno))
    return patterns


def _config_pattern_matches(pattern: tuple[str, ...], dotted_path: str) -> bool:
    parts = tuple(dotted_path.split("."))
    return len(pattern) == len(parts) and all(
        expected == "*" or expected == actual
        for expected, actual in zip(pattern, parts, strict=True)
    )


@functools.cache
def runtime_config_references() -> dict[str, tuple[str, ...]]:
    """Index only complete, path-aware config reads outside the config package."""

    known_paths = effective_config_paths()
    found: dict[str, list[str]] = defaultdict(list)
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
        patterns = set().union(*(_scope_config_patterns(scope) for scope in scopes))
        for dotted_path in known_paths:
            matching_lines = sorted(
                line for pattern, line in patterns if _config_pattern_matches(pattern, dotted_path)
            )
            if matching_lines:
                found[dotted_path].append(
                    f"{repo_relative(source)}:{matching_lines[0]}"
                )
    return {path: tuple(references) for path, references in found.items()}


def source_line_references(path: str, *, limit: int = 3) -> list[str]:
    """Return one exact declaration and up to two exact runtime consumers."""

    references = [schema_declaration_reference(path)]
    references.extend(runtime_config_references().get(path, ()))
    return list(dict.fromkeys(references))[:limit]


def markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def config_section_note(
    section: str,
    effective_payload: dict[str, Any],
    explicit_paths: set[str],
) -> str:
    rows = flatten(effective_payload[section], section)
    row_details = [
        (
            path,
            value,
            config_field_function(path, value),
            config_field_status(path),
            source_line_references(path),
        )
        for path, value in rows
    ]
    status_counts = Counter(status for _path, _value, _function, (status, _reason), _refs in row_details)
    consumer_source_paths = [
        reference.rsplit(":", 1)[0]
        for _path, _value, _function, _status, references in row_details
        for reference in references
        if "/config/" not in reference
    ]
    key_tokens = {path.rsplit(".", 1)[-1] for path, _value in rows}
    related_tests = sorted(
        path
        for path, text in TEST_TEXT.items()
        if any(re.search(rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])", text) for token in key_tokens)
    )[:12]
    title = f"Config - {section}"
    lines = [
        frontmatter(
            title=title,
            status="current",
            aliases=[f"learnloop.toml {section}", f"[{section}] configuration"],
            tags=[
                "learnloop/configuration/fields",
                f"learnloop/configuration/section/{section.replace('_', '-')}",
                "learnloop/status/active",
            ],
            source_paths=[
                "src/learnloop/config/schema.py",
                "src/learnloop/config/template.py",
                "tests/test_config_refactor.py",
                *list(dict.fromkeys(consumer_source_paths))[:12],
                *[repo_relative(path) for path in related_tests],
            ],
            extra={
                "config_schema_version": 2,
                "algorithm_version": "mvp-0.9",
                "generated": True,
                "field_count": len(rows),
                "field_status_counts": dict(sorted(status_counts.items())),
            },
        ),
        "",
        f"# `{section}` configuration",
        "",
        f"> [!info] Effective new-vault values",
        f"> This catalog was generated by parsing the current decision-only template and validating it through `LearnLoopConfig`. It contains {len(rows)} leaf values under `{section}`.",
        "",
        "The main configuration contract, precedence rules, and safe-edit workflow live in [[Configuration]]. Provider semantics live in [[AI Architecture]], and learning-policy meaning belongs in [[Learning System]]. ^config-section-scope",
        "",
        "> [!abstract] Status vocabulary",
        "> **ACTIVE** is canonical live policy; **DORMANT** is implemented but firewalled/default-inert; **COMPAT** is accepted only at a compatibility seam; **LEGACY** is consumed only by a frozen historical path. Status describes runtime authority, not whether the effective value happens to be false or null.",
        "",
        "## Field catalog",
        "",
        "| Dotted path | Effective value | Shape | Origin | Function | Runtime/refactor status | Consumer/source anchors |",
        "|---|---|---|---|---|---|---|",
    ]
    for path, value, function, (field_status, status_reason), references in row_details:
        serialized = json.dumps(value, ensure_ascii=False, sort_keys=True)
        origin = "explicit template decision" if path in explicit_paths else "modeled default or validator seed"
        anchors = "; ".join(f"`{reference}`" for reference in references) or "`src/learnloop/config/schema.py`"
        status_text = f"**{field_status}** — {status_reason}"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{path}`",
                    f"`{markdown_cell(serialized)}`",
                    value_type(value),
                    origin,
                    markdown_cell(function),
                    markdown_cell(status_text),
                    anchors,
                ]
            )
            + " |"
        )
    aliases = COMPAT_ALIASES_BY_SECTION.get(section, [])
    if aliases:
        lines.extend(
            [
                "",
                "## Compatibility-only inputs",
                "",
                "> [!warning] Accepted is not canonical",
                "> These spellings exist only so older vaults open. Normalization is one-way; effective configuration and runtime modules use the canonical target or discard the retired input.",
                "",
                "| Accepted legacy input | Canonical result | Status | Function |",
                "|---|---|---|---|",
            ]
        )
        for alias, target, function in aliases:
            lines.append(
                f"| `{markdown_cell(alias)}` | `{markdown_cell(target)}` | **COMPAT** | {markdown_cell(function)} |"
            )
    lines.extend(
        [
            "",
            "> [!warning] Omitted does not mean frozen in the file",
            "> Most values are intentionally absent from `learnloop.toml`. Their reproducibility is protected by the defaults fingerprint keyed to `algorithms.algorithm_version`, not by dumping every default into each vault.",
            "",
            "## Who consumes it",
            "",
            "Every row cites the exact Pydantic field declaration (or typed dynamic-key container). Additional anchors appear only when static analysis resolves the complete dotted path, a typed submodel parameter, or an alias derived from one of those paths; a declaration-only row means no direct runtime read was resolved, not that a same-named token was accepted as evidence. The broad tests most directly mentioning this section include:",
            "",
            markdown_list([repo_relative(path) for path in related_tests]),
            "",
            "## Extension and modification guidance",
            "",
            "1. Add or change the typed field in `src/learnloop/config/schema.py`.",
            "2. Add it to the minimal template only if it represents a real user decision; derived policy stays omitted.",
            "3. If behavior changes for omitted values, make the algorithm-version/defaults-fingerprint decision explicit and update `tests/test_config_refactor.py`.",
            "4. Put one-way legacy spelling translation in `src/learnloop/config/compat.py`; runtime modules should read only the canonical typed shape.",
            "5. Verify the effective result with `learnloop config effective --json`.",
            "",
            "## Related notes",
            "",
            "- [[Configuration#Effective configuration and explicit overrides]]",
            "- [[learnloop.toml]]",
            "- [[Legacy Configuration Compatibility]]",
            "- [[Environment and Machine Settings]]",
            "",
        ]
    )
    return "\n".join(lines)


def generate_config_field_notes() -> list[str]:
    raw = tomllib.loads(DEFAULT_CONFIG_TEXT)
    effective = LearnLoopConfig.model_validate(raw).model_dump(mode="json", exclude_none=False)
    explicit = explicit_leaf_paths(raw)
    sections = list(effective)
    for section in sections:
        (CONFIG_FIELDS_ROOT / f"Config - {section}.md").write_text(
            config_section_note(section, effective, explicit), encoding="utf-8"
        )
    return sections


def generate_table_catalog(grouped: dict[str, list[str]]) -> None:
    role_counts = Counter(role.value for role in TABLE_ROLES.values())
    status_counts = Counter(
        functionality_status(table, TABLE_ROLES[table])[0] for table in TABLE_ROLES
    )
    lines = [
        frontmatter(
            title="Database Catalog",
            status="current",
            aliases=["state.sqlite table index", "Database table MOC", "Table Catalog"],
            tags=[
                "learnloop/database/moc",
                "learnloop/database/schema-head-156",
                "learnloop/navigation",
            ],
            source_paths=[
                "src/learnloop/db/table_roles.py",
                "fixtures/migration_head_158/state.sqlite",
                "migrations/",
                "tests/test_table_roles.py",
                "tests/test_migrations.py",
            ],
            extra={
                "schema_head": SCHEMA_HEAD,
                "table_count": len(TABLE_ROLES),
                "generated": True,
            },
        ),
        "",
        "# Database Catalog",
        "",
        "This is the exhaustive map of the 251 user tables at migration head 156. Use [[Table Roles]] to interpret rebuild policy and [[Rebuild Ownership]] to see which projections are actually cleared and replayed. The larger persistence boundary lives in [[State and Persistence]]. ^catalog-scope",
        "",
        "> [!important] Role is not runtime status",
        "> `raw_ledger`, `derived`, `receipt`, `workflow`, and `compat` say what rebuild may do. `active`, `legacy-preserved`, `dormant-shadow`, and `dormant-owner-gated` say how the refactored runtime treats the table. See [[Table Roles#Role versus functionality status]].",
        "",
        "## Role indexes",
        "",
        "### By rebuild role",
        "",
        "| Role | Tables |",
        "|---|---:|",
    ]
    for role in TableRole:
        lines.append(f"| [[Table Roles#{role.value.replace('_', ' ').title()}|`{role.value}`]] | {role_counts[role.value]} |")
    lines.extend(
        [
            "",
            "### By functionality status",
            "",
            "| Status | Tables |",
            "|---|---:|",
        ]
    )
    for status, count in sorted(status_counts.items()):
        lines.append(f"| `{status}` | {count} |")
    lines.extend(
        [
            "",
            "## DERIVED tables",
            "",
            "The exact clearable set is: " + ", ".join(
                table_wikilink(table)
                for table in sorted(
                    name for name, role in TABLE_ROLES.items() if role is TableRole.DERIVED
                )
            ) + ". Ownership and dependency order live in [[Rebuild Ownership]]. ^derived-table-index",
            "",
            "## How to use this catalog",
            "",
            "Choose a domain-family section for conceptual neighborhood, a role tag for rebuild policy, or a functionality-status tag for current refactor state. Each table note then supplies DDL, relationships, exact static callers, tests, and modification guidance.",
            "",
            "### Finding a table in Obsidian",
            "",
            "Use Obsidian's core Search syntax:",
            "",
            "- `path:\"Reference/Database/Tables\" tag:#learnloop/database/role/derived` — every rebuildable projection.",
            "- `path:\"Reference/Database/Tables\" tag:#learnloop/status/dormant-owner-gated` — telemetry-gated dormant state.",
            "- `path:\"Reference/Database/Tables\" \"attempt_id\"` — tables whose note mentions an attempt relationship.",
            "- `path:\"Reference/Database/Tables\" section:(\"Who calls it\") \"probe_episodes\"` — access references within a specific section.",
            "- `tag:#learnloop/domain/sources-and-ingest` — the source/ingest family across indexes and table notes.",
            "",
            "> [!tip] Optional Dataview query",
            "> If Dataview is installed, the following query turns frontmatter into a live sortable inventory. The vault does not require Dataview.",
            "",
            "```dataview",
            "TABLE table_role AS Role, functionality_status AS Status, introduced_in AS Introduced",
            "FROM \"Reference/Database/Tables\"",
            "SORT domain_family ASC, file.name ASC",
            "```",
            "",
        ]
    )
    for domain in DOMAIN_DESCRIPTIONS:
        tables = grouped.get(domain, [])
        lines.extend(
            [
                f"## {domain.replace('-', ' ').title()}",
                "",
                f"{DOMAIN_DESCRIPTIONS[domain].capitalize()}. This is a navigational grouping, not permission for cross-domain imports. ^family-{domain}",
                "",
            ]
        )
        for table in tables:
            role = TABLE_ROLES[table]
            status, _reason = functionality_status(table, role)
            lines.append(
                f"- {table_wikilink(table)} — `{role.value}` · `{status}` · {table_purpose(table, domain, role=role)}"
            )
        lines.append("")
    lines.extend(
        [
            "## Maintenance contract",
            "",
            "Regenerate after any schema, role, or configuration-model change:",
            "",
            "```bash",
            ".venv/bin/python docs/learnloop-architecture-vault/_scripts/db_generate_reference.py",
            "```",
            "",
            "Validate live schema/config coverage and this vault's complete note graph:",
            "",
            "```bash",
            ".venv/bin/python docs/learnloop-architecture-vault/_scripts/db_validate_reference.py",
            ".venv/bin/python docs/learnloop-architecture-vault/_scripts/validate_vault.py",
            "```",
            "",
            "Then run `tests/test_migrations.py` and `tests/test_table_roles.py` when schema or role code changed. The first validator enforces the 251 table functions and exact 487-leaf config catalog; the second resolves the whole vault's frontmatter, source paths, Wikilinks, headings, and blocks.",
            "",
        ]
    )
    (VAULT_ROOT / "Reference" / "Database" / "Database Catalog.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def generate_config_catalog(sections: list[str]) -> None:
    raw = tomllib.loads(DEFAULT_CONFIG_TEXT)
    effective = LearnLoopConfig.model_validate(raw).model_dump(mode="json", exclude_none=False)
    all_rows = [
        (path, value)
        for section in sections
        for path, value in flatten(effective[section], section)
    ]
    status_counts = Counter(config_field_status(path)[0] for path, _value in all_rows)
    lines = [
        frontmatter(
            title="Configuration Field Catalog",
            status="current",
            aliases=["Effective config index", "learnloop.toml field MOC"],
            tags=[
                "learnloop/configuration/moc",
                "learnloop/configuration/schema-v2",
                "learnloop/navigation",
            ],
            source_paths=[
                "src/learnloop/config/schema.py",
                "src/learnloop/config/template.py",
                "tests/test_config_refactor.py",
            ],
            extra={
                "config_schema_version": 2,
                "algorithm_version": "mvp-0.9",
                "section_count": len(sections),
                "field_count": sum(
                    len(flatten(effective[section], section)) for section in sections
                ),
                "field_status_counts": dict(sorted(status_counts.items())),
                "generated": True,
            },
        ),
        "",
        "# Configuration Field Catalog",
        "",
        "The section notes below enumerate every leaf in the effective configuration of a newly initialized mvp-0.9 vault. Start with [[Configuration]] for precedence and policy, then use this catalog for exact paths/defaults. ^config-catalog-scope",
        "",
        "> [!note] Explicit versus effective",
        "> The generated `learnloop.toml` is intentionally small. Each field row says whether the value is an explicit template decision or a modeled default/validator seed.",
        "",
        "## Runtime and refactor status",
        "",
        "Every one of the 487 effective leaves has a semantic Function, a runtime/refactor Status, and concrete schema or consumer anchors. Status is about authority, not truthiness:",
        "",
        "| Status | Effective leaves | Meaning |",
        "|---|---:|---|",
        f"| `ACTIVE` | {status_counts['ACTIVE']} | Canonical typed input to current behavior. |",
        f"| `DORMANT` | {status_counts['DORMANT']} | Implemented but shadow-only, default-inert, or behind a shipped-off activation gate. |",
        f"| `COMPAT` | {status_counts['COMPAT']} | Effective compatibility seam retained while canonical behavior uses another field or route. |",
        f"| `LEGACY` | {status_counts['LEGACY']} | Read only by a frozen historical replay path. |",
        "",
        "> [!warning] Compatibility aliases are not effective leaves",
        "> One-way aliases and discarded retired keys are listed under **Compatibility-only inputs** in the affected section notes. They are accepted inputs, but do not survive as additional leaves in the 487-path effective model. See [[Legacy Configuration Compatibility]].",
        "",
        "## Sections",
        "",
        "| Section | Effective leaf values | Primary concern |",
        "|---|---:|---|",
    ]
    for section in sections:
        count = len(flatten(effective[section], section))
        concern = (
            "AI provider profile and task routing; see [[AI Architecture]]"
            if section == "ai"
            else "Learning policy; see [[Learning System]]"
            if section in {"evidence", "scheduler", "goals", "mastery", "probe", "recall_coverage"}
            else "Runtime configuration"
        )
        lines.append(f"| [[Config - {section}|`{section}`]] | {count} | {concern} |")
    lines.extend(
        [
            "",
            "## Search recipes",
            "",
            "- `path:\"Reference/Configuration/Fields\" \"gate_score_threshold\"` — locate an exact field.",
            "- `path:\"Reference/Configuration/Fields\" \"explicit template decision\"` — see fields written by init.",
            "- `path:\"Reference/Configuration/Fields\" \"modeled default or validator seed\"` — see hidden effective policy.",
            "- `path:\"Reference/Configuration/Fields\" \"**LEGACY**\"` — frozen replay-only fields.",
            "- `path:\"Reference/Configuration/Fields\" \"Compatibility-only inputs\"` — sections accepting old spellings.",
            "- `tag:#learnloop/configuration/section/ingest` — filter to one top-level section.",
            "",
            "## Related notes",
            "",
            "- [[learnloop.toml]]",
            "- [[Legacy Configuration Compatibility]]",
            "- [[Environment and Machine Settings]]",
            "- [[Runtime and Vault Data Files]]",
            "",
        ]
    )
    (VAULT_ROOT / "Reference" / "Configuration" / "Configuration Field Catalog.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def validate_generated(grouped: dict[str, list[str]], sections: list[str]) -> None:
    table_files = sorted(TABLES_ROOT.glob("*.md"))
    config_files = sorted(CONFIG_FIELDS_ROOT.glob("*.md"))
    if len(table_files) != len(TABLE_ROLES) or len(TABLE_ROLES) != 251:
        raise SystemExit(
            f"expected 251 table notes, got {len(table_files)} for {len(TABLE_ROLES)} roles"
        )
    if len(config_files) != len(sections):
        raise SystemExit(
            f"expected {len(sections)} config section notes, got {len(config_files)}"
        )
    if sum(len(values) for values in grouped.values()) != 251:
        raise SystemExit("table grouping does not cover every table exactly once")
    for path in [*table_files, *config_files]:
        text = path.read_text(encoding="utf-8")
        required = (
            "source_commit_timestamp:",
            "source_paths:",
            "tags:",
            "status:",
            "doc_version:",
        )
        missing = [token for token in required if token not in text[:3000]]
        if missing:
            raise SystemExit(f"{path} is missing frontmatter fields: {missing}")


def main() -> None:
    TABLES_ROOT.mkdir(parents=True, exist_ok=True)
    CONFIG_FIELDS_ROOT.mkdir(parents=True, exist_ok=True)
    grouped = generate_table_notes()
    sections = generate_config_field_notes()
    generate_table_catalog(grouped)
    generate_config_catalog(sections)
    validate_generated(grouped, sections)
    effective = LearnLoopConfig.model_validate(tomllib.loads(DEFAULT_CONFIG_TEXT)).model_dump(
        mode="json", exclude_none=False
    )
    config_status_counts = Counter(
        config_field_status(path)[0]
        for section in sections
        for path, _value in flatten(effective[section], section)
    )
    print(
        json.dumps(
            {
                "table_notes": len(list(TABLES_ROOT.glob("*.md"))),
                "table_groups": {name: len(values) for name, values in sorted(grouped.items())},
                "config_section_notes": len(sections),
                "config_status_counts": dict(sorted(config_status_counts.items())),
                "schema_head": SCHEMA_HEAD,
                "source_commit": COMMIT,
                "source_commit_timestamp": COMMIT_TIMESTAMP,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
