---
title: "diagnostic_eval_runs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite diagnostic_eval_runs"
  - "table diagnostic_eval_runs"
schema_head: 156
table_name: "diagnostic_eval_runs"
table_role: "receipt"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "144_diagnostic_augmentation.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/144_diagnostic_augmentation.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/diagnostic_augmentation.py"
  - "src/learnloop/diagnosis/scoreboard.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `diagnostic_eval_runs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Tracks one execution, input identity, and result for diagnostic eval so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `persona_realism_run_id`, `harness_version`, `grading_prompt_version`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/144_diagnostic_augmentation.sql`.
- **Schema touched by:** `144_diagnostic_augmentation.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `harness_version` | `TEXT` | yes | — | — | Stored value |
| `grading_prompt_version` | `TEXT` | yes | — | — | Stored value |
| `generator_provider` | `TEXT` | no | — | — | Stored value |
| `generator_model` | `TEXT` | no | — | — | Stored value |
| `generator_family` | `TEXT` | yes | — | — | Stored value |
| `diagnostician_provider` | `TEXT` | no | — | — | Stored value |
| `diagnostician_model` | `TEXT` | no | — | — | Stored value |
| `diagnostician_family` | `TEXT` | yes | — | — | Stored value |
| `cross_model_separated` | `INTEGER` | yes | — | — | Stored value |
| `persona_realism_run_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/persona_realism_runs\|persona_realism_runs.id]] | Stored value |
| `realism_licensed` | `INTEGER` | yes | — | — | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `case_count` | `INTEGER` | yes | — | — | Stored value |
| `metrics_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `persona_realism_run_id` → [[Reference/Database/Tables/persona_realism_runs|`persona_realism_runs.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_diagnostic_eval_runs_created` on `created_at`, `id`.
- `sqlite_autoindex_diagnostic_eval_runs_1` on `id` (unique).

Database triggers:

- `diagnostic_eval_runs_no_delete` — schema-enforced lifecycle or immutability constraint.
- `diagnostic_eval_runs_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.diagnostic_eval_case_rows()`
- `Repository.diagnostic_eval_run_rows()`
- `Repository.insert_diagnostic_eval_run()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/diagnostic_augmentation.py`
- `src/learnloop/diagnosis/scoreboard.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

No table-specific test contains the table name or a detected repository method call. The schema/role invariants are still pinned by `tests/test_migrations.py` and `tests/test_table_roles.py`.

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
CREATE TABLE diagnostic_eval_runs (
  id TEXT PRIMARY KEY,
  harness_version TEXT NOT NULL,
  grading_prompt_version TEXT NOT NULL,
  generator_provider TEXT,
  generator_model TEXT,
  generator_family TEXT NOT NULL,
  diagnostician_provider TEXT,
  diagnostician_model TEXT,
  diagnostician_family TEXT NOT NULL,
  cross_model_separated INTEGER NOT NULL
    CHECK (cross_model_separated IN (0, 1)),
  persona_realism_run_id TEXT REFERENCES persona_realism_runs(id),
  realism_licensed INTEGER NOT NULL CHECK (realism_licensed IN (0, 1)),
  status TEXT NOT NULL CHECK (status IN (
    'licensed', 'unlicensed_realism', 'invalid_same_model_family',
    'incomplete_regression_matrix', 'failed'
  )),
  case_count INTEGER NOT NULL CHECK (case_count >= 0),
  metrics_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK (
    (status = 'licensed' AND cross_model_separated = 1 AND realism_licensed = 1)
    OR status != 'licensed'
  )
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
