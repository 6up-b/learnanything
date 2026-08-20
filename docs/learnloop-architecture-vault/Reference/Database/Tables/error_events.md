---
title: "error_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite error_events"
  - "table error_events"
schema_head: 156
table_name: "error_events"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/cli/runtime.py"
  - "src/learnloop/cli/sim.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_migration.py"
  - "src/learnloop/diagnosis/diagnostic_gate.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/content/proposals/proposals.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `error_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of error so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `attempt_id`, `learning_object_id`, `misconception_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`, `025_misconception_registry.sql`, `144_diagnostic_augmentation.sql`, `156_projection_ledger_indexes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `error_type` | `TEXT` | yes | — | — | Stored value |
| `severity` | `REAL` | yes | — | — | Stored value |
| `is_misconception` | `INTEGER` | yes | `0` | — | Stored value |
| `repair_plan_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `misconception_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `misconception_statement` | `TEXT` | no | — | — | Stored value |
| `misconception_consistent_answer` | `TEXT` | no | — | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_error_events_attempt_replay` on `attempt_id`, `created_at`, `id`.
- `idx_error_events_status` on `status`, `learning_object_id`.
- `sqlite_autoindex_error_events_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository._insert_error_event()`
- `Repository.active_error_events()`
- `Repository.active_errors_by_learning_object()`
- `Repository.all_error_events_by_attempt()`
- `Repository.attempt_ids_for_misconception()`
- `Repository.error_events_for_attempt()`
- `Repository.find_record()`
- `Repository.record_attempt_outcome()`
- `Repository.replace_attempt_derived_outcome()`
- `Repository.reset_learning_object_derived_state()`
- `Repository.resolve_error_event()`
- `Repository.set_error_event_misconception()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop/sim/metrics.py`
- `src/learnloop/sim/runner.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/cli/app.py`
- `src/learnloop/cli/runtime.py`
- `src/learnloop/content/proposals/proposals.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/followups.py`
- `src/learnloop/diagnosis/guided_redo.py`
- `src/learnloop/diagnosis/misconceptions.py`
- `src/learnloop/diagnosis/missing_vocabulary.py`
- `src/learnloop/diagnosis/probe_episodes.py`
- `src/learnloop/diagnosis/probes.py`
- `src/learnloop/diagnosis/remediation.py`
- `src/learnloop/diagnosis/taxonomy_regrade.py`
- `src/learnloop/goals/exam_session.py`
- `src/learnloop/learner/recall_calibration.py`
- `src/learnloop/ops/doctor.py`
- `src/learnloop/reader/reader_guidance.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_attribution_p1.py`
- `tests/test_migrations.py`
- `tests/test_replay.py`
- `tests/test_simulation.py`
- `tests/test_table_roles.py`
- `tests/test_agent_runs.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_attempts.py`
- `tests/test_causal_attribution_exhibit.py`
- `tests/test_causal_attribution_p0.py`
- `tests/test_cli_attempt.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_deferred_regrade.py`
- `tests/test_diagnostic_augmentation.py`
- `tests/test_diagnostic_gate.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_e2e_local.py`
- `tests/test_guided_redo.py`
- `tests/test_item_parameters.py`
- `tests/test_misconception_registry.py`

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
CREATE TABLE error_events (
  id TEXT PRIMARY KEY,
  attempt_id TEXT,
  learning_object_id TEXT NOT NULL,
  error_type TEXT NOT NULL,
  severity REAL NOT NULL CHECK (severity >= 0.0 AND severity <= 1.0),
  is_misconception INTEGER NOT NULL DEFAULT 0 CHECK (is_misconception IN (0, 1)),
  repair_plan_json TEXT,
  status TEXT NOT NULL CHECK (status IN ('active', 'resolved')),
  created_at TEXT NOT NULL,
  updated_at TEXT
, misconception_id TEXT, misconception_statement TEXT, misconception_consistent_answer TEXT);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
