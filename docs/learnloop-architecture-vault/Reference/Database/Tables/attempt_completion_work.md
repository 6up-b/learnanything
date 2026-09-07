---
title: "attempt_completion_work"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "0395ae32f9e2e40d1cb98b38402631299a94003f"
source_commit_timestamp: "2026-09-07T12:49:13-04:00"
last_verified: "2026-09-07"
aliases:
  - "state.sqlite attempt_completion_work"
  - "table attempt_completion_work"
schema_head: 163
table_name: "attempt_completion_work"
table_role: "workflow"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "159_attempt_completion_work.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/159_attempt_completion_work.sql"
  - "src/learnloop/db/stores/completion.py"
  - "src/learnloop/substrate/data_quality.py"
  - "src/learnloop/substrate/dataset.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `attempt_completion_work`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Coordinates resumable post-attempt work and freezes its completed route so recovery never needs to regrade an acknowledged answer. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `attempt_id`, `submission_id`, `session_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Generation/application and learner-visible completion are separate durable phases.

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/159_attempt_completion_work.sql`.
- **Schema touched by:** `159_attempt_completion_work.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `attempt_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `submission_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `result_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `route_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | `'pending'` | — | Stored value |
| `collection_version` | `TEXT` | yes | `'learnloop-events-v1'` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `completed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_attempt_completion_pending` on `status`, `created_at`.
- `sqlite_autoindex_attempt_completion_work_2` on `submission_id` (unique).
- `sqlite_autoindex_attempt_completion_work_1` on `attempt_id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/completion.py`

### Direct SQL writers

- `src/learnloop/db/stores/completion.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_diagnostic_augmentation.py`
- `tests/test_sidecar_contract.py`

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
CREATE TABLE attempt_completion_work (
    attempt_id TEXT PRIMARY KEY REFERENCES practice_attempts(id),
    submission_id TEXT UNIQUE,
    session_id TEXT,
    practice_item_id TEXT NOT NULL,
    result_json TEXT NOT NULL,
    route_json TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'completed')),
    collection_version TEXT NOT NULL DEFAULT 'learnloop-events-v1',
    created_at TEXT NOT NULL,
    completed_at TEXT
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
