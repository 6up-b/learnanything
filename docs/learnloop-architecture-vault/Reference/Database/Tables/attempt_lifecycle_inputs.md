---
title: "attempt_lifecycle_inputs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite attempt_lifecycle_inputs"
  - "table attempt_lifecycle_inputs"
table_name: "attempt_lifecycle_inputs"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "263_attempt_lifecycle_inputs.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/263_attempt_lifecycle_inputs.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/algorithm_versions.py"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/attempts/lifecycle_inputs.py"
  - "src/learnloop/db/attempt_lifecycle_inputs.py"
  - "src/learnloop/db/stores/attempts.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `attempt_lifecycle_inputs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives attempt lifecycle input a stable database identity so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `attempt_id`, `learning_object_id`, `policy_version`, making the operational relationship explicit. ^table-purpose

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/263_attempt_lifecycle_inputs.sql`.
- **Schema touched by:** `263_attempt_lifecycle_inputs.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `attempt_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `required_facets_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `basis` | `TEXT` | yes | — | — | Stored value |
| `policy_version` | `TEXT` | yes | — | — | Stored value |
| `recorded_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_attempt_lifecycle_inputs_1` on `attempt_id` (unique).

## Who calls it

### Repository access surface

- `Repository.attempt_lifecycle_inputs()`

### Direct SQL readers

None found by exact static reference scan.

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/attempts/lifecycle_inputs.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/ad23_contract_helpers.py`
- `tests/attempt_lifecycle_inputs_migration_helpers.py`
- `tests/test_attempt_lifecycle_inputs_migration.py`
- `tests/test_rebuild_closed_row_answer.py`

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
CREATE TABLE attempt_lifecycle_inputs (
  attempt_id TEXT PRIMARY KEY REFERENCES practice_attempts(id),
  learning_object_id TEXT NOT NULL,
  required_facets_json TEXT NOT NULL,
  basis TEXT NOT NULL CHECK (basis IN ('captured_at_application', 'legacy_reconstructed')),
  policy_version TEXT NOT NULL,
  recorded_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
