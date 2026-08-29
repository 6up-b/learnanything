---
title: "learning_outcome_labels"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite learning_outcome_labels"
  - "table learning_outcome_labels"
schema_head: 156
table_name: "learning_outcome_labels"
table_role: "derived"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "010_scheduler_training_logs.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/010_scheduler_training_logs.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_migration.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `learning_outcome_labels`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Materializes replayed outcome labels consumed by learner and scheduling views. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `source_attempt_id`, `outcome_attempt_id`, `practice_item_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/010_scheduler_training_logs.sql`.
- **Schema touched by:** `010_scheduler_training_logs.sql`, `153_variable_rubric_scales.sql`.
- **Rebuild owner:** `learning_state`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `source_attempt_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `outcome_attempt_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `label_type` | `TEXT` | yes | — | — | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `label_value` | `REAL` | no | — | — | Stored value |
| `outcome_correctness` | `REAL` | no | — | — | Stored value |
| `outcome_rubric_score` | `INTEGER` | no | — | — | Stored value |
| `outcome_attempt_type` | `TEXT` | no | — | — | Stored value |
| `outcome_hints_used` | `INTEGER` | no | — | — | Stored value |
| `outcome_latency_seconds` | `INTEGER` | no | — | — | Stored value |
| `elapsed_seconds` | `INTEGER` | no | — | — | Stored value |
| `intervening_attempt_count` | `INTEGER` | yes | `0` | — | Stored value |
| `metadata_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `outcome_attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `CASCADE`, on update `NO ACTION`.
- `source_attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_learning_outcome_labels_outcome` on `outcome_attempt_id`.
- `idx_learning_outcome_labels_source` on `source_attempt_id`, `label_type`, `created_at`.
- `sqlite_autoindex_learning_outcome_labels_2` on `source_attempt_id`, `outcome_attempt_id`, `label_type` (unique).
- `sqlite_autoindex_learning_outcome_labels_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository._insert_learning_outcome_labels()`
- `Repository.find_record()`
- `Repository.learning_outcome_labels_for_source()`
- `Repository.replace_attempt_derived_outcome()`
- `Repository.retention_label_rows()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/cli/app.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/scheduling/evaluation.py`
- `src/learnloop_sidecar/handlers/inspector.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`
- `tests/test_observation_ledger_bulk.py`
- `tests/test_rebuild_orchestrator.py`
- `tests/test_agent_runs.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_attempts.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_show.py`
- `tests/test_source_ingestion.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.
5. Update the single owner in `DERIVED_STATE_REPLAYERS`, then prove same-version rebuild equivalence and shadow isolation.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE TABLE "learning_outcome_labels" (
  id TEXT PRIMARY KEY,
  source_attempt_id TEXT NOT NULL REFERENCES practice_attempts(id) ON DELETE CASCADE,
  outcome_attempt_id TEXT NOT NULL REFERENCES practice_attempts(id) ON DELETE CASCADE,
  label_type TEXT NOT NULL CHECK (
    label_type IN ('same_item_retention', 'same_learning_object_transfer')
  ),
  practice_item_id TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  label_value REAL CHECK (label_value IS NULL OR (label_value >= 0.0 AND label_value <= 1.0)),
  outcome_correctness REAL CHECK (
    outcome_correctness IS NULL OR (outcome_correctness >= 0.0 AND outcome_correctness <= 1.0)
  ),
  outcome_rubric_score INTEGER CHECK (
    outcome_rubric_score IS NULL OR outcome_rubric_score >= 0
  ),
  outcome_attempt_type TEXT,
  outcome_hints_used INTEGER,
  outcome_latency_seconds INTEGER,
  elapsed_seconds INTEGER CHECK (elapsed_seconds IS NULL OR elapsed_seconds >= 0),
  intervening_attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (intervening_attempt_count >= 0),
  metadata_json TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (source_attempt_id, outcome_attempt_id, label_type)
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
