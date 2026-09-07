---
title: "agent_runs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite agent_runs"
  - "table agent_runs"
schema_head: 157
table_name: "agent_runs"
table_role: "receipt"
functionality_status: "active"
domain_family: "schema-and-change"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/ai/runs.py"
  - "src/learnloop/ai/usage.py"
  - "src/learnloop/content/synthesis/source_set_synthesis.py"
  - "src/learnloop/content/synthesis/synthesis_manifests.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/scoreboard.py"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/attempts/coldness_receipt.py"
  - "src/learnloop/attempts/grading.py"
  - "src/learnloop/attempts/regrade.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/schema-and-change"
---

# `agent_runs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records AI/provider run provenance, status, and usage identity without making provider output authoritative by itself. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `provider_type`, `prompt_version`, `sdk_version`, making the operational relationship explicit. ^table-purpose

It belongs to the **schema and change** navigation family. The family context lives in [[Database Catalog#Schema And Change]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`, `005_attempt_feedback_metadata.sql`, `006_ai_provider_metadata.sql`, `044_provenance_manifests_apply_intents.sql`, `111_deterministic_grading_source.sql`, `131_agent_run_tokens.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `purpose` | `TEXT` | yes | — | — | Stored value |
| `model` | `TEXT` | no | — | — | Stored value |
| `provider` | `TEXT` | yes | — | — | Stored value |
| `prompt_template` | `TEXT` | no | — | — | Stored value |
| `prompt_version` | `TEXT` | no | — | — | Stored value |
| `sdk_version` | `TEXT` | no | — | — | Stored value |
| `codex_revision` | `TEXT` | no | — | — | Stored value |
| `input_context_hash` | `TEXT` | no | — | — | Stored value |
| `output_schema` | `TEXT` | no | — | — | Stored value |
| `started_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `completed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `status` | `TEXT` | yes | — | — | Stored value |
| `error_message` | `TEXT` | no | — | — | Stored value |
| `provider_type` | `TEXT` | no | — | — | Stored value |
| `provider_revision` | `TEXT` | no | — | — | Stored value |
| `est_input_tokens` | `INTEGER` | yes | `0` | — | Stored value |
| `est_output_tokens` | `INTEGER` | yes | `0` | — | Stored value |
| `actual_input_tokens` | `INTEGER` | yes | `0` | — | Stored value |
| `actual_output_tokens` | `INTEGER` | yes | `0` | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_agent_runs_purpose_completed` on `purpose`, `completed_at`.
- `sqlite_autoindex_agent_runs_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.add_agent_run_usage()`
- `Repository.agent_run()`
- `Repository.complete_agent_run()`
- `Repository.completed_agent_run_by_context()`
- `Repository.find_record()`
- `Repository.insert_agent_run()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/ai/runs.py`
- `src/learnloop/attempts/attempts.py`
- `src/learnloop/attempts/coldness_receipt.py`
- `src/learnloop/attempts/grading.py`
- `src/learnloop/attempts/regrade.py`
- `src/learnloop/cli/app.py`
- `src/learnloop/content/pipeline/source_ingestion.py`
- `src/learnloop/content/proposals/patches.py`
- `src/learnloop/content/proposals/proposals.py`
- `src/learnloop/content/synthesis/source_append.py`
- `src/learnloop/content/synthesis/source_set_synthesis.py`
- `src/learnloop/curriculum/graph_edit_proposals.py`
- `src/learnloop/curriculum/subject_registry.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/diagnosis/diagnosis_adjudication.py`
- `src/learnloop/diagnosis/missing_vocabulary.py`
- `src/learnloop/diagnosis/scoreboard.py`
- `src/learnloop/goals/certification_cold_probe.py`
- `src/learnloop/tutor/tutor_qa.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_agent_run_tokens.py`
- `tests/test_deferred_regrade.py`
- `tests/test_ingest_m3.py`
- `tests/test_migrations.py`
- `tests/test_proposal_dependencies.py`
- `tests/test_question_signal.py`
- `tests/test_source_ingestion.py`
- `tests/test_synthesis_manifests.py`
- `tests/test_agent_runs.py`
- `tests/test_apply_write_ahead.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_coldness_receipt.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_graph_edit_proposals.py`
- `tests/test_missing_vocabulary_notes.py`
- `tests/test_patch_applier.py`
- `tests/test_practice_leakage.py`
- `tests/test_repositories.py`
- `tests/test_scoreboard.py`

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
CREATE TABLE agent_runs (
  id TEXT PRIMARY KEY,
  purpose TEXT NOT NULL,
  model TEXT,
  provider TEXT NOT NULL,
  prompt_template TEXT,
  prompt_version TEXT,
  sdk_version TEXT,
  codex_revision TEXT,
  input_context_hash TEXT,
  output_schema TEXT,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
  error_message TEXT
, provider_type TEXT, provider_revision TEXT, est_input_tokens INTEGER NOT NULL DEFAULT 0, est_output_tokens INTEGER NOT NULL DEFAULT 0, actual_input_tokens INTEGER NOT NULL DEFAULT 0, actual_output_tokens INTEGER NOT NULL DEFAULT 0);
```

## Related notes

- [[Database Catalog#Schema And Change|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
