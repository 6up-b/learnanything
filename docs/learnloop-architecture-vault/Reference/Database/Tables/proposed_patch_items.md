---
title: "proposed_patch_items"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite proposed_patch_items"
  - "table proposed_patch_items"
schema_head: 157
table_name: "proposed_patch_items"
table_role: "workflow"
functionality_status: "active"
domain_family: "schema-and-change"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/content/authoring/persona_gate.py"
  - "src/learnloop/content/synthesis/source_set_synthesis.py"
  - "src/learnloop/curriculum/concepts.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/ops/doctor.py"
  - "src/learnloop_sidecar/handlers/app.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/content/authoring/practice_generation.py"
  - "src/learnloop/content/authoring/rung_variants.py"
  - "src/learnloop/content/pipeline/source_ingestion.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/schema-and-change"
---

# `proposed_patch_items`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Tracks individually reviewable operations within a proposed patch. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `proposed_patch_id`, `client_item_id`, `target_entity_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **schema and change** navigation family. The family context lives in [[Database Catalog#Schema And Change]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`, `003_proposal_item_audit.sql`, `013_proposal_item_source_refs.sql`, `035_proposal_dependencies.sql`, `117_question_promotion_jobs_and_queue_revision.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `proposed_patch_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/proposed_patches\|proposed_patches.id]] | Stored value |
| `client_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `item_type` | `TEXT` | yes | — | — | Stored value |
| `operation` | `TEXT` | yes | — | — | Stored value |
| `target_entity_type` | `TEXT` | no | — | — | Stored value |
| `target_entity_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `payload_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `edited_payload_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `decision` | `TEXT` | yes | — | — | Stored value |
| `validation_status` | `TEXT` | yes | — | — | Stored value |
| `validation_errors_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `applied_change_batch_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `decided_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `decided_by` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `audit_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `source_ref_ids_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `dependency_status` | `TEXT` | yes | `'pending'` | — | Stored value |
| `dependency_block_reason_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

Declared SQLite foreign keys:

- `proposed_patch_id` → [[Reference/Database/Tables/proposed_patches|`proposed_patches.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_proposed_patch_items_decision` on `proposed_patch_id`, `decision`.
- `sqlite_autoindex_proposed_patch_items_2` on `proposed_patch_id`, `client_item_id` (unique).
- `sqlite_autoindex_proposed_patch_items_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository._refresh_proposal_status()`
- `Repository.active_source_events_for_entity()`
- `Repository.delete_proposal_item()`
- `Repository.find_record()`
- `Repository.pending_invalid_proposal_items()`
- `Repository.pending_proposal_items()`
- `Repository.persist_proposal_batch()`
- `Repository.persona_gate_audit_rows()`
- `Repository.proposal_item()`
- `Repository.proposal_items()`
- `Repository.proposal_items_by_client_id()`
- `Repository.record_applied_proposal_item()`
- `Repository.reject_applied_proposal_item()`
- `Repository.reset_proposal_item_decision()`
- `Repository.set_proposal_item_decision()`
- `Repository.set_proposal_item_dependency_status()`
- `Repository.synthesis_run_introducing_entity()`
- `Repository.update_proposal_item_audit()`
- `Repository.update_proposal_item_edited_payload()`
- `Repository.update_proposal_item_validation()`

### Direct SQL readers

- `src/learnloop/curriculum/concepts.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop_sidecar/handlers/app.py`

### Direct SQL writers

- `src/learnloop/curriculum/concepts.py`
- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/content/authoring/persona_gate.py`
- `src/learnloop/content/authoring/practice_generation.py`
- `src/learnloop/content/authoring/rung_variants.py`
- `src/learnloop/content/pipeline/source_ingestion.py`
- `src/learnloop/content/proposals/apply_protocol.py`
- `src/learnloop/content/proposals/patches.py`
- `src/learnloop/content/proposals/proposals.py`
- `src/learnloop/content/sources/provenance.py`
- `src/learnloop/content/synthesis/source_append.py`
- `src/learnloop/content/synthesis/source_set_synthesis.py`
- `src/learnloop/content/synthesis/study_map_diff.py`
- `src/learnloop/curriculum/graph_edit_proposals.py`
- `src/learnloop/curriculum/subject_registry.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/diagnosis/error_taxonomy.py`
- `src/learnloop/ops/doctor.py`
- `src/learnloop/tutor/promotions.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_patch_applier.py`
- `tests/test_agent_runs.py`
- `tests/test_apply_write_ahead.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_cli_generate_practice.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_diagnostic_generation.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_graph_edit_proposals.py`
- `tests/test_ingest_instrument_gates.py`
- `tests/test_missing_vocabulary_notes.py`
- `tests/test_persona_gate.py`
- `tests/test_practice_leakage.py`
- `tests/test_proposal_dependencies.py`
- `tests/test_proposal_persistence.py`
- `tests/test_repositories.py`
- `tests/test_self_attributed_misconceptions.py`
- `tests/test_show.py`
- `tests/test_sidecar_contract.py`
- `tests/test_source_append.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE TABLE "proposed_patch_items" (
  id TEXT PRIMARY KEY,
  proposed_patch_id TEXT NOT NULL REFERENCES proposed_patches(id) ON DELETE CASCADE,
  client_item_id TEXT NOT NULL,
  item_type TEXT NOT NULL CHECK (
    item_type IN (
      'learning_object', 'practice_item', 'concept', 'concept_edge', 'rubric', 'error_type',
      'facet', 'task_blueprint', 'provenance_link', 'notation_mapping', 'source_conflict'
    )
  ),
  operation TEXT NOT NULL CHECK (operation IN ('create', 'update', 'deactivate')),
  target_entity_type TEXT CHECK (
    target_entity_type IS NULL OR
    target_entity_type IN (
      'learning_object', 'practice_item', 'concept', 'concept_edge', 'rubric', 'error_type',
      'facet', 'task_blueprint', 'provenance_link', 'notation_mapping', 'source_conflict'
    )
  ),
  target_entity_id TEXT,
  payload_json TEXT NOT NULL,
  edited_payload_json TEXT,
  decision TEXT NOT NULL CHECK (decision IN ('pending', 'accepted', 'rejected')),
  validation_status TEXT NOT NULL CHECK (validation_status IN ('valid', 'warning', 'invalid')),
  validation_errors_json TEXT,
  applied_change_batch_id TEXT,
  decided_at TEXT,
  decided_by TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  audit_json TEXT,
  source_ref_ids_json TEXT,
  dependency_status TEXT NOT NULL DEFAULT 'pending'
    CHECK (dependency_status IN ('pending', 'ready', 'blocked')),
  dependency_block_reason_json TEXT,
  UNIQUE (proposed_patch_id, client_item_id)
);
```

## Related notes

- [[Database Catalog#Schema And Change|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
