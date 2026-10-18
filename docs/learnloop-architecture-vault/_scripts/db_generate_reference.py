#!/usr/bin/env python3
"""Generate the schema and effective-configuration reference notes.

This script intentionally reads the checked-in migration-head fixture rather
than attempting to reconstruct a schema from prose.  It combines four live
authorities:

* ``fixtures/migration_head_210/state.sqlite`` for columns, keys, indexes,
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
SCHEMA_PATH = REPOSITORY_ROOT / "fixtures" / "migration_head_210" / "state.sqlite"
MIGRATIONS_ROOT = REPOSITORY_ROOT / "migrations"

sys.path.insert(0, str(SRC_ROOT))

from learnloop.config.schema import LearnLoopConfig  # noqa: E402
from learnloop.config.template import DEFAULT_CONFIG_TEXT  # noqa: E402
from learnloop.db.table_roles import TABLE_ROLES, TableRole, user_table_names  # noqa: E402
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
VERIFIED_DATE = "2026-09-23"
SCHEMA_HEAD = 210


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
    "source_block_fts": "Indexes source block text for FTS5 BM25 keyword search (Slice 2 T6: library search, tutor spans, Quick Add scope); triggers keep it in step with `source_document_blocks` and its one replayer rebuilds it, so it never holds anything the block ledger does not. Hazard: rows are keyed by the blocks' implicit rowid (the block table has a composite key), so a migration that rebuilds `source_document_blocks` must recreate the triggers and rerun the replayer (`learnloop rebuild-derived-state`); deletes also match the block's identity as well as its rowid (migration 177), and `learnloop doctor` reports stale or missing rows.",
    "attempt_completion_work": "Coordinates resumable post-attempt work and freezes its completed route so recovery never needs to regrade an acknowledged answer.",
    "model_call_receipts": "Captures each started model operation and physical request, preserving returned text, failures and available provider usage for later cost and quality analysis.",
    "model_work_checkpoints": "Preserves validated inventory windows and synthesis passes under content hashes so interrupted jobs reuse completed model work.",
    "instructional_impressions": "Records which find_practice proposal candidates a surface actually rendered (canonical sources S0): retrieved, displayed and served stay three records. Read only by the exposure rule (an earlier impression of a prompt excludes it from the independent intents within the cold retrieval delay) and by S5's intervention records; deliberately not activity_exposure_events, whose rendered rows burn a surface. Append-only.",
    "source_exercise_imports": "Tracks each textbook exercise imported as practice (canonical sources S1): the caller and proposal, the exercise's extraction, spans and revision, the authored item, the answer-key ladder's status and label, any family attachment and the intervention need it fulfilled. Workflow state for the interactive import's time box and background check; certification reads the key through reference_key_checks.",
    "reference_key_checks": "Appends one row per answer-key check of an imported exercise (canonical sources S1): the rung (book solution, panel and symbolic check), the label it earned, its evidence refs and the reference_content_hash of the stem, key and rubric it verified, so an edit leaves the current content unverified. Read by the certification gate (practice_attempts.reference_status) and the key label shown to the learner.",
    "source_comparisons": "Holds compare_sources results (canonical sources S3): each source's quote-verified contributions and pairwise relations under the caller's policy, the dropped lines and pins, the uncompared and unverified sources, and the manifest. No consensus field; reused for an identical query, policy and source set.",
    "source_tool_calls": "Receipts for the typed source tools (canonical sources S4): a request row per validated request from the tutor, the router or an external agent (its stored caller context, derived policy, validated arguments and dropped ids, refused when it leaked the answer or arrived during a cold administration) and a run row per execution naming the request (result refs, keys, source versions, model, latency). Append-only.",
    "retrieval_interventions": "Appends one row when a retrieved asset is shown or served (canonical sources S5): a cited or opened passage, a comparison shown, ranked remediation passages delivered, a proposal picked, a need fulfilled from the sources and served. References only (assets with revisions, targets, the valuation's state hashes, the valued candidate's predicted outcome distribution and minutes, impressions, the independence verdict at valuation and serving time); reports read it, nothing serves from it.",
    "retrieval_intervention_outcomes": "Materializes the outcome join for retrieval_interventions (canonical sources S5): R_next within the session or day, R_cold as the decision-value outcome states (pending stays right-censored), the observed bucket beside the predicted one, actual beside predicted minutes and the learner's taps. Rebuilt by its one replayer from persisted rows with no model call; associations, not causes.",
    "source_held_out_signal_marks": "Keeps each held-out assessment signal on the reading its model run read (exam protection by extraction identity, migration 204): one row per fresh inventory that held anything out, with the extraction and revision it read, the unit, the role it ran under and the sorted span ids. `content.sources.exam_material` reads protection from it, never from `source_unit_inventories`, whose cache rows a reuse rebinds to another reading. A reuse writes no row. Backfilled rows from rebound cache rows name no reading (`extraction_id` NULL): their book stays protected and they mark no reading. Append-only (an update aborts); deleted only with its book.",
    "source_service_spend": "Shares the canonical-sources service's daily money cap (source_service.max_daily_cost_usd) across every process that opens the vault: one row per metered request admitted under it, reserved inside one BEGIN IMMEDIATE transaction that recovers orphaned rows and checks the day's total plus the estimate, so a sidecar and a CLI batch cannot both spend the same allowance. One accounting function (service_spend_accounting) gives that total for admission, recovery and reports, counting each request once with the receipts naming its row (`budget_json.envelope_reservations`): while its owner's lease (`lease_expires_at`, renewed while the process lives) holds, a row counts the larger of its charge and its receipts; once reconciled (`settled`), its receipts (its reconciled cost bounding a lost finish); an orphan is reconciled with its receipts or `released` when it has none (`resolved_by` names the owner or recovery), and a receipt naming a released row cannot start, so its request is never sent. A `legacy` row, written before receipts named rows, counts its charge and suppresses no receipt (no durable identity ties one to it; an amount or a second-resolution stamp is no identity), so its charge and every unlinked receipt count and the receipts started in its lifetime are reported as `legacy.uncertain_usd`; a receipt naming no row counts by its own cost. A receipt's dollars are its reported cost, else its tokens at the rate its request recorded, else at the owner's service rate. Subscription requests reserve nothing.",
    "daily_plans": "Holds each local day's finite daily plan (daily-loop DL1, mvp-0.14): its kind (normal, re-entry or a keep-going extension), budget and remembered minutes, the split_v1 lane minutes and the new-material admission it was built with, and its status. Its blocks are attention_blocks rows (daily_plan_id, plan_ordinal, lane, chosen_by) whose every decision is an attention_block_events receipt; nothing here is evidence and replay never reads it.",
    "submission_intents": "Binds a durable retry identity to the exact session, practice item and offered scheduler candidate before the attempt is committed.",
    "scheduler_offer_receipts": "Freezes the ordered candidates returned after adapter filtering so later queue refreshes cannot rewrite an earlier offer.",
    "workbench_sessions": "Holds each problem worked in steps (reader workbench RW2a, migration 207): beside the source in the Reader or full width on the practice screen, opened at once with its verbatim stem before the exercise import binds it to an item (import_status, the batch and its request for try again), how it was opened (origin, entry), the book's visibility and when it first counted as one hint-equivalent (source_shown_at), and its lifecycle (open, submitted with its attempt, abandoned and reopened). Lifecycle state, updated in place; replay never reads it, because the submitted attempt carries the evidence (hints_used, entry_surface). Kill switch workbench.enabled.",
    "workbench_steps": "Appends one row per change to a workbench problem's steps (reader workbench RW2a, migration 207): a new step at its fractional ordinal, an edit superseding the newest version of its chain, a tombstone for a delete and an undo superseding it, each under the client's idempotency key, so nothing the learner wrote is lost and a retried write is answered from its row. Append-only (an update or delete aborts); stuck steps stay learner work and never enter the submitted answer. Replay never reads it.",
    "forecast_receipts": "Keeps every saved forecast a decision states before its outcome is known (saved diagnosis forecasts, migration 206): a completed diagnosis's prediction of the next unaided observation of each facet it explains, and a scheduled repair cold check's predicted cold outcome, each written in its decision's transaction with its forecaster, scope, inputs as of when, the forecast payload (the voi_forecasts body) and its exact binding, or the reason it has none (censored at birth). Resolutions are derived at read time by `learnloop diagnosis calibration`; nothing serving, scoring or scheduling reads it and no rebuild writes or clears it. Append-only (an update or delete aborts); kill switch diagnosis.forecast_receipts.",
    "followup_value_decisions": "Keeps one immutable receipt per follow-up decision the value-of-information rule takes part in (mvp-0.21): each decision on a source attempt gets its own id and ordinal (an automatic decision and a later manual follow-up, or a recorded generation need and a later queue), with the value decision's forecasts in `decision_json` (NULL when no candidate was valued), so no later decision overwrites an earlier one and no rebuild clears them.",
    "decision_features": "Freezes the decision-time inputs of scheduler, probe and grading decisions. Selection rows (`feature_schema` `selection_features_v1`) hold the learner's ability vector for the item's learning object and the item's scored demand vector; `item_demand_vector.content_hash` joins to `practice_item_snapshots.content_hash`, and components, propensity and policy stay on the scheduler candidate and slate rows that `decision_id` names.",
    "practice_item_snapshots": "Keeps one content-addressed copy of every practice-item revision the scheduler scored, keyed by the SHA-256 of its canonical JSON, so selection decision features can be joined to the exact item text after the vault item changes.",
    "false_remediation_adjudications": "Records append-only human or machine false-remediation labels with retained evidence references and verifier versions; corrections append another adjudication.",
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
    if table.startswith(("probe_", "causal_", "diagnostic_", "misconception", "coldness_", "discrimination_", "contrast_pair", "error_hunt", "unresolved_cause", "persona_realism", "hypothesis_recurrence", "recurrence_")):
        return "diagnosis"
    if table.startswith(("scheduler_", "controller_", "attention_", "daily_plans", "session", "queue_state", "decision_features", "practice_item_snapshots", "policy_experiment", "familiarity_kernel", "shadow_component", "composed_selector", "router_")):
        return "scheduling"
    if table.startswith(("commitment", "depth_", "task_blueprint", "golden_path", "progression_", "angle_inventor", "p2_ladder", "lapse_episode", "family_evidence", "target_exemplar")):
        return "curriculum"
    if table.startswith(("goal_", "exam_", "forecast", "certification_", "cold_measurement")):
        return "goals-and-exams"
    if table.startswith(("question_", "remediation_", "failure_triage", "rung_variant", "followup_task", "followup_value", "missing_vocabulary")):
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
    connection = sqlite3.connect(f"file:{SCHEMA_PATH}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        # FTS5 shadow tables belong to their registered virtual table.
        actual = set(user_table_names(connection))
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
    "embedding": "opt-in embedding substrate, model identity, backfill consent, and privacy disclosure",
    "graph_nomination": "Slice 2 T5 embedding nominations for ingest and graph review (never identity), with ingest-time embedding caps",
    "facet_identity": "facet identity at mint time and the dedupe command: the cheap judge's neighbourhood size, shortlist rank and spend caps (merges apply live with an undo; merge_locked_facets is a retired key nothing reads)",
    "project": "project-understanding M1: automatic capture of agent-written diffs and delayed probes in the standalone project store",
    "field": "offline learner-field analysis, revision exclusions, and opt-in paid experiments",
    "practice_index": "find_practice retrieval, rerank, coverage, and the paid dossier and evaluation switches",
    "capabilities": "optional capability-residual activation and shrinkage",
    "locks": "the retired facet identity-lock thresholds (nothing reads them since facet locks were removed on 2026-10-12)",
    "error_impacts": "error-family severity shaping",
    "fitting": "offline fitting of learner-specific scheduler parameters",
    "trace_evidence": "opportunistic trace evidence and learner-burden limits",
    "diagnostic_augmentation": "multi-sample diagnostic augmentation",
    "families": "explicit-command offline family authoring, not live scheduling",
    "diagnosis": "Slice 1 learner-blind grading and the asynchronous history-aware diagnoser (mvp-0.10): kill switch, history mode, queue limits, diagnosis card, PF-c grading support, mvp-0.21's probe hypothesis lane reading the diagnoser's verdict (with its pending rule), and the saved diagnosis forecasts' kill switch (forecast_receipts, logging only)",
    "placement": "learner field F2 (mvp-0.11): starting new material without ceremony, assumed-known receipts, and the optional quick check",
    "router": "action router R1: decision logging on today's serving paths and the mvp-0.15 probe-tie admission kill switch",
    "pf": "PF-b generation, verification and capped publication of verified practice items (kill switch off by default)",
    "recurrence": "Slice 2 T1 recurrence groups with authority (mvp-0.12): kill switch, the live same-cause judge's shortlist (top-k and benchmark-set blocking cutoffs bound to the vectors they were measured on) and caps, the escalation card and its escalated-repair request",
    "source_retrieval": "Slice 2 T6 source retrieval (keyword + dense, fused by rank) for the library search, tutor spans, the Quick Add scope and labelled LO suggestions, with the live rewrite and verification spend",
    "stuck_prompt": "the \"I'm stuck\" answer control that replaces \"I don't know\" (mvp-0.13)",
    "hints": "adaptive hints H0: hint telemetry (each authored hint the practice screen reveals recorded as a help_assists row, with its time and a hash and length of the draft, and attached to the attempt at submit): the kill switch; telemetry only, hints_used stays the client's count (no successor)",
    "source_service": "canonical sources as a shared instructional service (mvp-0.18/0.19): the master switch, one kill switch per phase (tutor offers, the exercise arm and its key checks, discriminating search, source-first needs, intent-aware grounding, comparisons, tutor tools, intervention records), the interactive verifier's time box, a comparison's prompt-size bound and the money caps",
    "plan": "daily-loop DL1 (mvp-0.14): the finite daily plan's kill switches, remembered minutes, split caps, new-material admission, duration estimates, reading pace and re-entry caps",
    "learner_text_gaps": "learner-text gaps: tutor questions, stuck answers and diagnoses read for named prerequisites and misconceptions (kill switches, the authoritative chooser, the shortlist, edges, created prerequisites and their daily cap, holding-pen sightings, per-text spend caps) and mvp-0.16's sooner check",
    "evsi": "EVSI calibration: the value-of-information forecast log (voi_forecasts, logging only) and the measured-loss regime's switch and shrinkage strength (Part C, default off)",
    "reader_inquiry": "reader workbench RW1a: branching Ask, inquiry status with reopen, the return stack and detour strip, the reconnect line with its passage-scoped quick check, and the Reader's funnel activity (content and display only)",
    "workbench": "reader workbench RW2a: the resumable scratchpad (a problem worked in steps beside the source, submitted through the ordinary attempt path with a visible book as one hint-equivalent): the kill switch, and how long an untouched open problem waits before the recap calls it unfinished (a display limit; nothing is closed automatically)",
    "recap": "reader workbench RW6a: \"Last time here\" (the returning card at the head of the Guide) and Wrap up (offered in the rail after activity and once where the learner lands after leaving a source): two kill switches over pure reads of existing ledgers (salience-only events only; no model call, nothing stored)",
    "cues": "reader workbench RW3a: margin cues from the Guide's own citations (display only): the kill switch, the learner's density per section, at most one mark per screenful, and the books cues are switched off for",
    "reader_intent": "reader workbench RW1b: the intent box (a small, unfocused box under a selection whose words one typed Decider choice routes to a palette action, run exactly as the palette's own; the palette grouped by the five learner intentions): the kill switch, speculative routing once typing pauses (its switch and pause), the routing's timeout and the route's daily call cap (speculation stops at 80% of it); routing writes ledger rows and salience-only events only",
    "reader_active_reading": "reader workbench RW1b: active reading on a selected derivation or worked example (try the next step with the book's next lines folded, why does this step work, what does this assume, reconstruct this later, another way to see this): the kill switch; the questions are the quick-check producer's formative rows and never an attempt",
    "reader_formative": "reader workbench RW1b: a next-step, why-step or assumption answer the learner marks partly or no becomes reader_formative learner text for learner-text gaps (tier 2: never evidence, mastery or FSRS): the kill switch",
    "library_ask": "reader workbench RW4a: ask your library (Shift+Enter in the library search, Ctrl+Shift+F or a selection's where else / where is this used / what do I need first): verbatim passages from the sources service's find_sources under the Reader caller's derived policy, grouped by source and role, each with one organizer line (one listwise call, route library_organizer) that must cite its own passage: the kill switch, the concept-graph expansion's switch, the personalized chip's default and the organizer's daily metered cap; retrieval is context and the lines are display (no successor)",
    "reader_compare": "reader workbench RW4a: the Reader's compare table over the sources service's compare_sources (one row per source, each line quoting its own source, no consensus; display only until RW4d's keep): the kill switch",
    "proof_check": "the valid-alternative gate for proofs and explanations, in the grader (mvp-0.20): the kill switch of the own-route rules and the server-side unlocated rule (mvp-0.17's separate route check was removed on 2026-10-13)",
    "voi_stopping": "value-of-information stopping (mvp-0.21): the kill switch and per-site sub-switches that lift four count caps (probe observations per session, further follow-ups per LO, further teach-backs, project probes per day) onto value of information, and the multi-family EVSI study's three switches (the robust completion gate while value decides, the 2-3 check lookahead, the value gate's robust quantile)",
    "decider_routes": "Tier 1, the Decider migration (mvp-0.22, owner 2026-10-13): one kill switch per small judgment the Decider decides with its LLM as fallback, the facet span-support check and the method-explicit required-method statement judgment",
    "required_method": "method-explicit items (mvp-0.25): the kill switch of the own-route rules' required method (own-route-v2: a criterion tied to an item's required method is graded on use of that method)",
    "ui": "how the desktop presents learner surfaces (docs/specs/ux_learnloop_v1.md §10, display only): UX Phase 4's kill switch of the plain practice card, feedback, short-check results, repair step and session finish (\"classic\" restores the screens exactly)",
    "eligibility": "one serve/administration eligibility decision (mvp-0.27): the kill switch of every serve path asking the decision submit asks (cold checks, probes, quick-check offers) and of historical writers' bounded auto-prime window",
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
    if path.startswith("locks.") or path == "facet_identity.merge_locked_facets":
        return (
            "COMPAT",
            "Retired with facet identity locks (owner, 2026-10-12): accepted so older vaults still open and the "
            "recorded defaults snapshots stay put; nothing reads it, and doctor warns when a vault sets it.",
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


# Leaves whose meaning the name-based templates below cannot express. Each text
# restates the declaring comment in src/learnloop/config/schema.py.
CONFIG_FUNCTION_OVERRIDES: dict[str, str] = {
    "ai.routing.field_question_classifier": (
        "Names an explicit offline question-classification profile. Empty disables the route; "
        "global chat overrides, active-provider and fallback-provider settings never apply."
    ),
    "facet_identity.reword_confirm": (
        "Kill switch of the owner's one-tap reword confirm (2026-10-13): on, a model-proposed change to a "
        "registered facet's meaning without an explanatory span (not exam-only) waits for the owner's confirm and "
        "a title or worked-example change needs no explanatory citation; off restores the predecessor rule "
        "(refused at accept, dropped by the producers). Exam-only support is refused either way."
    ),
    "diagnosis.forecast_receipts": (
        "Kill switch of saved diagnosis forecasts: on, a completed diagnosis and a scheduled repair cold check "
        "write their forecasts as forecast_receipts rows in the deciding transaction; off writes none. Logging "
        "only: no grading, scoring, scheduling or serving change, and replay never reads the receipts."
    ),
    "field.enabled": "Allows explicitly requested paid field experiments; never changes serving or evidence.",
    "field.active_predictor": "Pins the serving interface to mastery_ekf in F1; challengers require a later algorithm successor.",
    "field.legacy_fallback": "Excludes missing historical attribution revisions by default; current_content is explicit and labeled reconstructed.",
    "field.question_classification_enabled": "Additional opt-in for bounded classification of missing question metadata; replay only reads cached output.",
    "field.llm_probability_enabled": "Additional opt-in for offline probability preparation; ordinary replay uses a store-free cached arm and never calls a model.",
    "placement.enabled": "Kill switch for F2 placement at mvp-0.11 and later; off restores the predecessor's opening probes, serving and ordering and ignores recorded assumptions.",
    "placement.initial_probes": "Opens the predecessor's opening diagnostic episode per new LO while placement stays on (D11 default off).",
    "placement.assumed_first_interval_days": "Days from an assumed-known decision to its first review, which is the check (D6).",
    "placement.fast_track_min_correct": "Clean full-marks first answers fast-track needs before the probability test (D6, at least 2).",
    "placement.fast_track_q": "Probability the active predictor must give that the LO's ability exceeds the known threshold (D6).",
    "placement.known_probability": "Success probability whose logit is the known threshold theta_known (D6: logit(0.75)).",
    "placement.quick_check_k": "Most answers one optional quick check serves (D4).",
    "placement.quick_check_budget_minutes": "Time budget of one optional quick check (D4).",
    "plan.enabled": "Kill switch for the finite daily plan at mvp-0.14 and later; off restores mvp-0.13's Today (the open queue with its re-entry cap) and every plan RPC answers enabled false.",
    "plan.new_admission_enabled": "Sub-switch: off admits no system-chosen new material (learner requests and scheduled checks still serve).",
    "plan.reading_blocks": "Sub-switch: on puts at most one reading block a day from an as_you_read source in the new lane.",
    "plan.reading_from_furthest": "Kill switch for UX Phase 1's reading step (U4), a live change wherever the plan acts (no successor tag; replay never reads the selection): the reading block continues from the furthest section read and skips front matter while a chapter is left; off it is DL1's first unfinished section in book order.",
    "plan.deterministic_staged_plans": "Kill switch for plan determinism (owner rule 2026-10-13: staged plans are deterministic), a live change wherever the router composes Today (no successor tag; replay never reads a plan): the staged plan's pool is the scheduler's greedy order and a contrast pair's member order is the pair's own draw, so the same vault state plans the same blocks in every session; at mvp-0.24 that pool also gives the model mixture its candidates (the staged pick and the support), while the mixture keeps its own seeded draw, floor and logged propensities; off restores the staged pool as mvp-0.23 and mvp-0.24 landed (the scheduler's seeded exploration and the per-session pair order).",
    "plan.default_minutes": "Daily budget on a vault with no plan and no session minutes (D1); afterwards the remembered minutes carry forward.",
    "plan.minutes_presets": "The one-tap minute chips on Start and Today.",
    "plan.repair_max_share": "Largest share of the budget the repair lane takes before new and push (D2).",
    "plan.maintain_max_share": "Largest share of the budget due maintenance takes, so overdue reviews never take the whole day (D2, Q10).",
    "plan.keep_going_minutes": "Minutes one keep-going extension adds after today's plan is done (D3).",
    "plan.load_horizon_days": "Horizon of the projected daily review load new-material admission compares with the budget (Q11).",
    "plan.load_ceiling": "Share of the budget the projected review load plus admitted new material may reach (Q11).",
    "plan.new_item_reviews_14d": "Reviews assumed for a new item in its first two weeks when costing its admission (Q11).",
    "plan.max_new_items_per_day": "Most new items planned a day across the day's plans; learner requests are exempt (Q11).",
    "plan.min_new_items_per_day": "Fewest new items a day when new material exists and the plan is not re-entry (Q11).",
    "plan.latency_cap_minutes": "Winsorizing cap on an answer latency in the duration estimate (Q12).",
    "plan.read_words_per_minute": "Reading pace that turns a section's words left into a reading block's estimate.",
    "plan.pre_questions": "Pre-questions a reading block may open with (DL4; DL1 serves none).",
    "plan.reentry_minutes": "Most minutes a re-entry plan takes after a break, whatever the remembered budget (D11).",
    "plan.reentry_max_items": "Most items a re-entry plan serves after a break, whatever its minutes allow (D11).",
    "plan.project_probes_max_per_day": "Most due project probes a day in the maintain lane (project M2); the rest stay in the full list.",
    "plan.headline": "Shows the optional one-line Today headline (display only, D7).",
    "router.log_decisions": "Writes one router_decisions row per Today offer, staged P2 decision, learner pick and daily-plan block decision; not a serving change, acts at every version.",
    "router.probe_tie_admission": "Kill switch for router R1's mvp-0.15 successor: probe near-ties, teach-back items included, join the Today queue's seeded exploration; off serves exactly as mvp-0.14.",
    "ingest.audio.mode": (
        "Selects the audio path: `transcription` (the `ai.routing.transcription` chat route when set, "
        "else the transcription endpoint) or `native` (mp3/wav sent as input_audio parts to the "
        "canonical_ingest chat provider, which must declare `audio` in its input modalities; other "
        "containers still take the transcription path)."
    ),
    "ingest.native.max_audio_mb": (
        "Caps audio megabytes sent to the chat provider by native audio ingestion; base64 inflates "
        "the file by about 33% inside a chat body, and the cap is checked before any upload."
    ),
    "ingest.native.max_pdf_mb": (
        "Caps PDF megabytes sent to the chat provider by native PDF ingestion (OpenAI-compatible "
        "file inputs accept at most 32 MB per file); checked before any upload."
    ),
    "ingest.native.fallback_when_unavailable": (
        "When a native modality is selected but the routed provider cannot take it for a "
        "configuration reason, runs the non-native path (PDF: marker/pypdf; audio: the transcription "
        "route or endpoint) with a health flag instead of failing closed."
    ),
    "ingest.pdf.engine": (
        "Selects the PDF/image reader: `auto` (GLM-OCR when it can run, then local Marker, then pypdf, "
        "the reason kept in extraction health), `glm_ocr`, `marker`, `pypdf`, or `native` (the whole PDF "
        "to the canonical_ingest chat provider). Explicit engines fail rather than switch; only GLM-OCR "
        "reads PNG/JPG."
    ),
    "ingest.pdf.glm_ocr.backend": (
        "GLM-OCR backend: `auto`/`api` use z.ai's hosted layout_parsing when a key is set (whole file "
        "sent after the one-time whole-file OK naming z.ai; never for a repair OK'd as local); `local` uses the "
        "self-hosted glmocr server at local_url when it accepts a connection."
    ),
    "ingest.pdf.glm_ocr.api_url": "z.ai's (or Zhipu's open.bigmodel.cn) GLM-OCR layout_parsing endpoint; https only, redirects refused.",
    "ingest.pdf.glm_ocr.api_key_env": (
        "Name of the environment variable holding the z.ai key (never the key); ZHIPU_API_KEY and "
        "ZHIPUAI_API_KEY are read when it is unset. Settings saves the key to the machine's settings.env."
    ),
    "ingest.pdf.glm_ocr.local_url": (
        "The self-hosted `python -m glmocr.server` parse endpoint; selected PDF pages are sent as PNG "
        "images. A repair OK'd as local uses it only when it is a loopback address."
    ),
    "ingest.pdf.glm_ocr.request_timeout_seconds": "Per-request timeout for GLM-OCR calls (each page window is one request).",
    "ingest.pdf.glm_ocr.max_pages_per_request": "Largest page window per GLM-OCR request (1-30; the hosted service reads at most 30 pages).",
    "ingest.pdf.glm_ocr.price_per_million_tokens": (
        "USD per million GLM-OCR tokens, input and output alike, for receipts, the automatic-build "
        "daily guard and import previews (3,500 tokens a page estimated); no per-file money cap."
    ),
    "ingest.pdf.glm_ocr.base64_style": "How the file is sent to the hosted API: a data URI (documented) or bare base64.",
    "ai.routing.embedding": (
        "Names the openai_embedding profile that embeds text; empty means the code-default "
        "openrouter_embedding profile. It has no fallback: LEARNLOOP_AI_PROVIDER, the active provider "
        "and the fallback provider never apply, nothing is sent unless embedding.enabled is also on, "
        "and a chat profile here is refused (as is this profile on any generation route)."
    ),
    "embedding.enabled": (
        "Master switch for remote embeddings. While false, the embedding route resolves to no client, "
        "so no consumer can send text, and the disabled route does not affect settings health."
    ),
    "embedding.backfill_enabled": (
        "Separate consent for `learnloop embeddings backfill` paid runs; dry-run estimates work "
        "without it. Both switches must be true before any request is sent."
    ),
    "embedding.model": (
        "The embedding model id to request and to key stored vectors by; authoritative over the "
        "embedding profile's own model field. Changing it backfills a new model beside the old vectors."
    ),
    "embedding.dimensions": (
        "Stored vector width for embedding.model (MRL truncation, then L2-normalization). Fixed per "
        "model once vectors exist; consumers may request a narrower renormalized view at query time."
    ),
    "embedding.map_neighbors_enabled": (
        "Display-only kill switch for the knowledge map: while true, an item whose current stem has a "
        "stored vector for the ranking model takes its four shown neighbours from item-text similarity; "
        "false keeps the facet/concept-graph neighbours. The ranking model is embedding.model once its "
        "stored vectors cover every current stem another stored model covers; until a replacement's "
        "backfill catches up, the previous model keeps ranking (Slice 2 §4). Reads stored vectors only "
        "(no calls) and never moves map coordinates or learner state."
    ),
    "embedding.privacy_disclosure": (
        "Read-only disclosure computed by the schema and shown in Settings and `config effective`; "
        "setting it in learnloop.toml has no effect."
    ),
    "ai.routing.rubric_phrasing_judge": (
        "Names the judge of `learnloop grading method-phrasing` (method-explicit items, owner rule "
        "2026-10-13): a decider profile (one typed fact/method choice per criterion) or a chat profile "
        "(one structured reading per item, with fact rewrites). Empty uses the Tier-1 Decider "
        "(ai.routing.tier1_decider's profile, else the code-default openrouter_decider) when it is "
        "ready, else ai.active_provider; with neither ready the report falls back to the conservative "
        "heuristic and says so. The same route makes the one-time required-method statement judgments "
        "(redesign 2026-10-14): whether a textbook exercise's statement requires its proposed method (at "
        "import) and whether a PF variant's stem prohibits its parent's (at selection), the Decider first "
        "(argmax of its probabilities; decider_routes.required_method_statement), else the LLM judge, "
        "ledgered (task required_method_statement); with neither ready nothing is decided. Grading never "
        "uses it."
    ),
    "ai.routing.project": (
        "Names the provider profile for project-understanding probe authoring and the closed-book "
        "check. Empty follows ai.routing.grading, then the active provider; probe grading itself "
        "always uses the grading route."
    ),
    "project.auto_sweep": (
        "Kill switch for the automatic, git-only capture sweep at app start and Today-queue build; "
        "`learnloop project sweep` still runs when false. Nothing happens until a repo is enrolled."
    ),
    "project.probe_delay_days": (
        "Days after capture that a diff's probes stay sealed (never rendered by any command); "
        "stored on each probe when it is generated."
    ),
    "project.probes_per_diff": (
        "Probes selected at random (stored seed) from the survivors of the validity and "
        "closed-book filters; fewer survivors leave the diff under-probed."
    ),
    "project.candidates_per_diff": (
        "Answer-first candidates requested from the authoring model per diff before filtering."
    ),
    "project.min_diff_lines": (
        "M1b gate randomization threshold (spec section 5.1): smaller diffs are left out of "
        "randomization. M1 probes every capture with probe-able content."
    ),
    "project.context_lines": (
        "Head-side lines of context stored and sent around each hunk; extended to the enclosing "
        "function or class while the bundle fits project.context_token_budget."
    ),
    "project.context_token_budget": (
        "Upper bound on one diff bundle's estimated tokens; larger diffs keep hunk-only excerpts, "
        "then drop trailing files, and are marked truncated."
    ),
    "project.enroll_backfill_days": (
        "On enrollment, agent-trailer commits from this many days back are captured too."
    ),
    "project.plan_sweep_min_interval_minutes": (
        "Minimum minutes between automatic plan-build sweeps; app start always sweeps."
    ),
    "project.generate_before_serving": (
        "When true, `learnloop project probes` generates questions for due diffs that have none "
        "before serving, under the command's spend caps."
    ),
    "project.grading_reasoning_effort": (
        "Reasoning effort for probe grading (closed-book judgments and answer grades), applied to the "
        "grading route's profile when it takes an effort; empty keeps the route's own effort (spec "
        "section 5.2: one high-effort pass)."
    ),
    "project.require_tool_isolation": (
        "Kill switch for tool isolation: when true, an agentic transport (Codex) runs project calls in "
        "a bubblewrap sandbox with no home, vault or repo visible, and a transport that can be neither "
        "sandboxed nor is tool-free is refused; false runs unconfined and receipts record none."
    ),
    "reader_inquiry.enabled": (
        "Kill switch for reader workbench RW1a (content and display, no successor): branching Ask "
        "(a follow-up names its parent and sees only its ancestors), inquiry status on the root "
        "question with reopen, the detour strip and Alt+arrow return stack, the reconnect line and "
        "its passage-scoped quick check, and the Reader activity the reader report reads. Off: "
        "today's flat Ask rail, and every RPC RW1a extends answers byte-identically."
    ),
    "cues.enabled": (
        "Kill switch for reader workbench RW3a (display only, no successor): the Guide's own passages on "
        "a Learning Object with a recent misunderstanding shown as quiet margin marks with a fixed note "
        "and a \"because\" line, their taps (salience-only events and learner_card verdicts on "
        "passage_cue) and the density control. Off: the guide plan carries no cues and the Reader shows "
        "no marks and no density control."
    ),
    "cues.density": (
        "The learner's display limit of margin marks per section: off, fewer, normal or more (0, 1, 2 "
        "or 4); \"fewer marks like this\" steps it down one notch. Remembered in vault config so it "
        "holds across devices. A display limit only, never a count that decides learning."
    ),
    "cues.one_per_viewport": (
        "At most one margin mark per screenful at every density (spacing computed when the text is "
        "laid out, never while scrolling); off leaves the per-section density budget alone."
    ),
    "cues.off_sources": (
        "Source ids the learner switched margin cues off for (from a mark's popover; undoable until "
        "they leave the source)."
    ),
    "workbench.enabled": (
        "Kill switch for reader workbench RW2a (no successor): the step workbench beside the source in "
        "the Reader and the practice screen's \"Work in steps\", saved as typed, resumable, abandonable "
        "and reopened, submitted through the ordinary attempt path (a visible book is one "
        "hints_used). Off: no workbench entry anywhere, every workbench RPC refuses, the config DTO "
        "carries no workbench key, and the practice screen is byte-identical."
    ),
    "workbench.open_session_days": (
        "Days an open workbench problem may go untouched before the recap shows it as \"unfinished\", "
        "without alarm. A display limit only: nothing is closed automatically."
    ),
    "stuck_prompt.enabled": (
        "Kill switch for mvp-0.13's \"I'm stuck\" control (write what you can, or what's confusing "
        "you). On, a stuck answer is an ordinary attempt at the standard mass: graded and diagnosed "
        "when it has text, scored 0 with no model call and no error tag when empty. Off, an mvp-0.13 "
        "vault shows \"I don't know\" and records dont_know exactly as mvp-0.12. Dormant below "
        "mvp-0.13; replay reads practice_attempts.declared_stuck, never this switch."
    ),
    "proof_check.enabled": (
        "Kill switch for mvp-0.20's own-route rules. On, the blind grader's prompt grades every "
        "criterion on the learner's own route and marks down only by quoting the failing step, and "
        "a server-side rule leaves a mark-down on a divergent route that quotes nothing from the "
        "learner's words, an omitted criterion, or one the grader declares it cannot verify "
        "unassessed (holding the grade for review when nothing is then assessed and nothing "
        "validated) and appends the verdict to judgment_ledger: one grading call. Off, new answers grade as mvp-0.19 now does (whose grading is "
        "mvp-0.16's: mvp-0.17's separate route check was removed on 2026-10-13). Dormant below mvp-0.20; "
        "replay reads the blind record and evidence rows, never this switch."
    ),
    "ai.routing.tier1_decider": (
        "Selects the decision-model profile (type `decider`) that answers the Tier-1 judgments "
        "`[decider_routes]` moves to the Decider (mvp-0.22) and the facet span-support check; empty uses "
        "the code-default `openrouter_decider` profile. A Decider-only route: never a chat provider, "
        "never `LEARNLOOP_AI_PROVIDER`, never a generic LLM fallback. Learner-text gaps keep "
        "`ai.routing.learner_gap_decider`."
    ),
    "decider_routes.learner_gap_judge": (
        "Kill switch for the Decider's learner-text gap pair verdicts (same prerequisite, same belief) and "
        "its \"needed?\" verdict at mvp-0.22: the argmax of one typed choice decides, the learner_gap_judge "
        "LLM only where it gave no answer (unavailable, refused for spend, failing). Off: both judges as at "
        "mvp-0.21 (learner_text_gaps.chooser decides whose verdict counts; beliefs the LLM's)."
    ),
    "decider_routes.learner_gap_kind": (
        "Kill switch for the Decider's kind of a learner text at mvp-0.22 (the gap chooser's authority): its "
        "argmax decides and the context model still names the gap; the context model's kind only where the "
        "Decider gave no answer. Off: learner_text_gaps.chooser decides, as at mvp-0.21."
    ),
    "decider_routes.misconception_match": (
        "Kill switch for the Decider's misconception match at mvp-0.22: one typed choice over the "
        "candidate registry beliefs and `new`; the grading route's misconception_match call only where it "
        "gave no answer. Off: the LLM alone, as at mvp-0.21. No model client (replay, the worker): no call."
    ),
    "decider_routes.diagnosis_link_judgment": (
        "Kill switch for the Decider's pattern-link verdicts in `learnloop diagnose review` at mvp-0.22 "
        "(same / different / not_sure per blinded earlier answer); the diagnosis_judge LLM batch only for a "
        "link it gave no answer. A Decider link imported from a review joins T1's recurrence groups. Off: "
        "the LLM judge, as at mvp-0.21."
    ),
    "decider_routes.field_question_classification": (
        "Kill switch for the Decider's answer to `learnloop field classify-questions` at mvp-0.22 (the "
        "missing question type and a yes/no per catalog LO and facet, in one request); the configured "
        "field_question_classifier route only where it gave no answer or the catalog needs more than one "
        "request. Off: the classifier route, as at mvp-0.21."
    ),
    "decider_routes.contamination_leak_judgment": (
        "Kill switch for the Decider's exam and tutor-answer leak verdicts in the contamination report at "
        "mvp-0.22; the contamination_judge LLM only for a pair it gave no answer. Off: the LLM judge, as at "
        "mvp-0.21."
    ),
    "decider_routes.contamination_reveal_judgment": (
        "Kill switch for the Decider's reader-reserve reveal verdicts in the contamination report at "
        "mvp-0.22; the contamination_judge LLM only for a pair it gave no answer. Off: the LLM judge, as at "
        "mvp-0.21."
    ),
    "decider_routes.facet_span_support": (
        "Kill switch for the facet span-support check (a content path, every version): before a "
        "model-proposed reword of a registered facet's meaning that cites explanatory spans applies, the "
        "Decider answers one typed question over those spans and the new wording; only `supports` as its "
        "top option applies it, anything else (or no answer) holds it for the owner's one-tap confirm. Off: "
        "a cited reword applies as before."
    ),
    "decider_routes.required_method_statement": (
        "Kill switch for the Decider's one-time required-method statement judgment (method-explicit "
        "items, a Tier-1 content task registered at their merge; every version): whether a textbook "
        "exercise's statement requires the method its import proposes (requires / allows / prohibits; "
        "only requires keeps the item's required_method) and whether a PF variant's stem contradicts "
        "its parent's (a contradicting stem is refused). The Decider is ai.routing.rubric_phrasing_judge's "
        "decider profile, else the Tier-1 Decider's; every verdict is ledgered (task "
        "required_method_statement) and reused, so a statement is judged once. Off: the LLM judge on "
        "ai.routing.rubric_phrasing_judge (or ai.active_provider) decides it. Grading never reads it."
    ),
    "required_method.enabled": (
        "Kill switch for the method-explicit successor's required-method grading (owner rule "
        "2026-10-13; mvp-0.25). On, the own-route rules are "
        "own-route-v2: an item's required_method, frozen with the assessment contract (the one "
        "authority: no prompt is parsed to decide it), reaches the grader's policy, and a criterion "
        "tied to it is graded on use of that method, so a divergent "
        "route fails it with no quoted wrong step (neither PF-c's gate nor the unlocated rule "
        "unassesses it); every other criterion keeps the own-route rules. Off, new answers grade "
        "exactly as mvp-0.24. Dormant below the successor and when proof_check.enabled is off; "
        "replay reads the blind record, never this switch. Generation phrasing criteria by fact and "
        "doctor's criterion:method_phrased are content paths, not gated here."
    ),
    "eligibility.enabled": (
        "Kill switch for the one eligibility decision's successor (mvp-0.27; "
        "learnloop.serve_eligibility). On, every serve path asks the decision submit asks: an item "
        "submit would prime is never served as a cold check, a probe or a quick-check offer; a cold "
        "check its item can no longer take cold (the answer shown with no lapse, or the item "
        "practised since the check was set) is withdrawn with its typed disposition "
        "(unmeasurable_no_held_out_surface for a repair cold retry; an expired certification probe) "
        "and the item served as ordinary practice; exam seeding, an exam's finish and a kept-state "
        "sim count only reveals up to their own instant when auto-priming. Off, every path serves "
        "and admits exactly as mvp-0.26. Dormant below the successor; replay reads each attempt's "
        "recorded primed flag, never this switch."
    ),
    "practice_index.enabled": (
        "Kill switch for find_practice (sidecar RPC, CLI and agent tool). It only proposes items; "
        "turning it off changes nothing the scheduler serves."
    ),
    "practice_index.retrieval_path": (
        "auto uses the two-level dossier path only when the latest retrieval evaluation on the "
        "current index found that it beats direct item search; direct and dossier force a path "
        "(dossier falls back to direct while the dossier index is incomplete)."
    ),
    "practice_index.rerank_enabled": (
        "Lets find_practice ask the practice_rerank route to judge and pick from its candidate pool; "
        "every verdict is appended to judgment_ledger (task practice_relevance)."
    ),
    "practice_index.rerank_price_per_million": (
        "USD per million tokens for a metered rerank route; without it a metered rerank is skipped. "
        "Codex routes run on the subscription and need no price."
    ),
    "practice_index.rerank_max_cost_usd": (
        "Per-request dollar cap for a metered rerank, checked before the request is sent."
    ),
    "practice_index.query_embedding_price_per_million": (
        "USD per million input tokens for find_practice's query embedding when embedding.model "
        "has no published estimate; without it the query embedding is skipped (keyword search)."
    ),
    "practice_index.facet_top_k": (
        "The fewest facets the two-level path keeps; it adds more in rank order until their "
        "admissible items fill candidate_pool."
    ),
    "practice_index.candidate_pool": (
        "How many fused candidates find_practice sends to the rerank, and how many admissible "
        "items the two-level path's facets must cover."
    ),
    "practice_index.proposals": (
        "Default number of proposals find_practice returns when the request gives no limit."
    ),
    "practice_index.rrf_k": (
        "Reciprocal-rank-fusion constant for combining keyword and embedding rankings; ranks are "
        "fused, so no score threshold is set by hand."
    ),
    "practice_index.coverage_min_eligible": (
        "Facets with fewer admissible items than this are listed as targets for generating more practice."
    ),
    "practice_index.usage_window_hours": (
        "A proposed item attempted within this many hours of the proposal is logged as practised "
        "(judgment_ledger task practice_usage, judge exact_key)."
    ),
    "practice_index.dossiers_enabled": (
        "Consent for paid `learnloop practice-index dossiers` runs; dry-run estimates work without it."
    ),
    "practice_index.evaluation_enabled": (
        "Consent for paid `learnloop eval practice-index` runs (query writing and relevance labels); "
        "dry-run estimates work without it."
    ),
    "recurrence.enabled": (
        "Kill switch for recurrence groups at mvp-0.12: off, grouping sites use exact statements again "
        "from the next normalization, vault open or rebuild; recorded verdicts are kept."
    ),
    "recurrence.judge_enabled": (
        "Runs the live same-cause judge inside each diagnose job (the backlog command and the guard are "
        "explicit owner commands and run regardless)."
    ),
    "recurrence.top_k": (
        "Earlier in-scope hypotheses per new hypothesis whose pair reaches the same-cause judge."
    ),
    "recurrence.blocking_cutoffs": (
        "Embedding model id to B3's entry: the recall-oriented cosine cutoff and the width, text recipe and "
        "task prefix it was measured on. It applies only to stored vectors of exactly that identity (others "
        "are refused); a model without one is blocked by top-k alone. Never merges or rejects anything by score."
    ),
    "recurrence.judge_max_pairs_per_attempt": (
        "Live judge calls per diagnose job; shortlisted pairs past it wait for the backlog command."
    ),
    "recurrence.judge_timeout_seconds": (
        "Per-turn deadline for one Codex same-cause judge turn."
    ),
    "recurrence.escalation_card_enabled": (
        "Shows the escalated repair, its earlier answers and its usefulness tap on the diagnosis card."
    ),
    "recurrence.escalation_repair_enabled": (
        "At a recurrence group's K-th answer, when none of the diagnosis's repairs differs from those shown "
        "before, asks the diagnosis route once for a repair with a different operator and representation; "
        "off, the card says the repair is the same kind as before."
    ),
    "source_retrieval.enabled": (
        "Kill switch for Slice 2 T6: false restores the substring library search, the learning "
        "object's linked tutor spans, the label-keyword Quick Add scope and no LO suggestion. "
        "Retrieval is context only, so it changes no evidence or serving."
    ),
    "source_retrieval.dense": (
        "Use the stored source_block/text vectors (deep library searches and tutor spans) when every "
        "block in the searched scope has a current vector for embedding.model; otherwise keyword only, "
        "labelled as such."
    ),
    "source_retrieval.query_rewrite": (
        "Rewrite a conceptual question (a question word or mark, or five content terms) with the "
        "source_query_rewrite route before retrieval; keyword searches are never rewritten."
    ),
    "source_retrieval.tutor_rerank": (
        "Verify the tutor's retrieved spans with an LLM listwise rerank (route source_rerank, ledger task "
        "source_relevance); only verified spans reach the tutor. Off or unavailable, the tutor keeps the "
        "learning object's linked spans."
    ),
    "source_retrieval.suggest_learning_objects": (
        "Offer a nearest-LO suggestion, labelled as one, for a reader span with no provenance-linked "
        "learning object; it is never written as a candidate or promotion target."
    ),
    "source_retrieval.llm_price_per_million": (
        "USD per million tokens for metered rewrite and rerank routes; without it those steps are skipped. "
        "Codex routes run on the subscription and need no price."
    ),
    "source_retrieval.rewrite_max_cost_usd": (
        "Dollar cap for one live query rewrite (one call and one retry), checked before the request is sent."
    ),
    "source_retrieval.rerank_max_cost_usd": (
        "Dollar cap for one live tutor-span verification (one call and one retry), checked before sending."
    ),
    "source_retrieval.query_embedding_price_per_million": (
        "USD per million input tokens for query embeddings when embedding.model has no published "
        "estimate; without it dense retrieval is skipped."
    ),
    "source_retrieval.rrf_k": (
        "Reciprocal-rank-fusion constant for combining the keyword, meaning and rewrite rankings; ranks "
        "are fused, so no score threshold is set by hand."
    ),
    "source_retrieval.tutor_candidate_pool": (
        "How many fused candidate spans the tutor's verification rerank judges."
    ),
    "source_retrieval.tutor_spans": (
        "At most this many verified spans reach the tutor as citable context."
    ),
}


def config_field_function(path: str, value: Any) -> str:
    if path in CONFIG_FUNCTION_OVERRIDES:
        return CONFIG_FUNCTION_OVERRIDES[path]
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
                f"learnloop/database/schema-head-{SCHEMA_HEAD}",
                "learnloop/navigation",
            ],
            source_paths=[
                "src/learnloop/db/table_roles.py",
                "fixtures/migration_head_210/state.sqlite",
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
        f"This is the exhaustive map of the {len(TABLE_ROLES)} user tables at migration head {SCHEMA_HEAD}. Use [[Table Roles]] to interpret rebuild policy and [[Rebuild Ownership]] to see which projections are actually cleared and replayed. The larger persistence boundary lives in [[State and Persistence]]. ^catalog-scope",
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
            "Then run `tests/test_migrations.py` and `tests/test_table_roles.py` when schema or role code changed. The first validator checks table coverage and the configuration catalog against their live authorities; the second resolves the whole vault's frontmatter, source paths, Wikilinks, headings, and blocks.",
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
    leaf_count = len(all_rows)
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
        f"Every one of the {leaf_count} effective leaves has a semantic Function, a runtime/refactor Status, and concrete schema or consumer anchors. Status is about authority, not truthiness:",
        "",
        "| Status | Effective leaves | Meaning |",
        "|---|---:|---|",
        f"| `ACTIVE` | {status_counts['ACTIVE']} | Canonical typed input to current behavior. |",
        f"| `DORMANT` | {status_counts['DORMANT']} | Implemented but shadow-only, default-inert, or behind a shipped-off activation gate. |",
        f"| `COMPAT` | {status_counts['COMPAT']} | Effective compatibility seam retained while canonical behavior uses another field or route. |",
        f"| `LEGACY` | {status_counts['LEGACY']} | Read only by a frozen historical replay path. |",
        "",
        "> [!warning] Compatibility aliases are not effective leaves",
        f"> One-way aliases and discarded retired keys are listed under **Compatibility-only inputs** in the affected section notes. They are accepted inputs, but do not survive as additional leaves in the {leaf_count}-path effective model. See [[Legacy Configuration Compatibility]].",
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
    if len(table_files) != len(TABLE_ROLES):
        raise SystemExit(
            f"expected {len(TABLE_ROLES)} table notes, got {len(table_files)}"
        )
    if len(config_files) != len(sections):
        raise SystemExit(
            f"expected {len(sections)} config section notes, got {len(config_files)}"
        )
    if sum(len(values) for values in grouped.values()) != len(TABLE_ROLES):
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
