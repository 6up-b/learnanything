---
title: "attempt_submission_receipts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite attempt_submission_receipts"
  - "table attempt_submission_receipts"
schema_head: 157
table_name: "attempt_submission_receipts"
table_role: "receipt"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "053_attempt_submission_idempotency.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/053_attempt_submission_idempotency.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop_sidecar/handlers/practice.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `attempt_submission_receipts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Makes client submission of attempt idempotent and auditable so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `submission_id`, `attempt_id`, `practice_item_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/053_attempt_submission_idempotency.sql`.
- **Schema touched by:** `053_attempt_submission_idempotency.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `submission_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `result_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_attempt_submission_receipts_2` on `attempt_id` (unique).
- `sqlite_autoindex_attempt_submission_receipts_1` on `submission_id` (unique).

## Who calls it

### Repository access surface

- `Repository.attempt_submission_receipt()`
- `Repository.insert_attempt_submission_receipt()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop_sidecar/handlers/practice.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_sidecar_contract.py`
- `tests/test_goal_series.py`

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
CREATE TABLE attempt_submission_receipts (
  submission_id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL UNIQUE REFERENCES practice_attempts(id),
  practice_item_id TEXT NOT NULL,
  result_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
