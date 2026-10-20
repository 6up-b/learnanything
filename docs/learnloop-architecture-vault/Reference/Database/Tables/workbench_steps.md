---
title: "workbench_steps"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "e0cda60da02a8215e4bc08dbde19ea57c47c283a"
source_commit_timestamp: "2026-10-20T00:32:50-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite workbench_steps"
  - "table workbench_steps"
schema_head: 213
table_name: "workbench_steps"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "207_workbench.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/207_workbench.sql"
  - "src/learnloop/db/stores/workbench.py"
  - "src/learnloop/diagnosis/text_gaps/sources.py"
  - "src/learnloop/reader/recap.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `workbench_steps`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Appends one row per change to a workbench problem's steps (reader workbench RW2a, migration 207): a new step at its fractional ordinal, an edit superseding the newest version of its chain, a tombstone for a delete and an undo superseding it, each under the client's idempotency key, so nothing the learner wrote is lost and a retried write is answered from its row. Append-only (an update or delete aborts); stuck steps stay learner work and never enter the submitted answer. Replay never reads it. It supplies replay-stable input rather than a disposable cache. Rows bind `session_id`, `supersedes_id`, `ordinal`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/207_workbench.sql`.
- **Schema touched by:** `207_workbench.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `session_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/workbench_sessions\|workbench_sessions.id]] | Stored value |
| `ordinal` | `REAL` | yes | — | — | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `body_md` | `TEXT` | yes | — | — | Stored value |
| `supersedes_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/workbench_steps\|workbench_steps.id]] | Stored value |
| `deleted` | `INTEGER` | yes | `0` | — | Stored value |
| `client_idempotency_key` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `supersedes_id` → [[Reference/Database/Tables/workbench_steps|`workbench_steps.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `session_id` → [[Reference/Database/Tables/workbench_sessions|`workbench_sessions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_workbench_steps_supersedes` on `supersedes_id` (unique).
- `idx_workbench_steps_session` on `session_id`, `created_at`, `id`.
- `sqlite_autoindex_workbench_steps_2` on `session_id`, `client_idempotency_key` (unique).
- `sqlite_autoindex_workbench_steps_1` on `id` (unique).

Database triggers:

- `workbench_steps_no_delete` — schema-enforced lifecycle or immutability constraint.
- `workbench_steps_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/diagnosis/text_gaps/sources.py`
- `src/learnloop/reader/recap.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_architecture.py`
- `tests/test_reader_workbench_rw2a.py`

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
CREATE TABLE workbench_steps (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES workbench_sessions(id),
  -- The step's place in the list (fractional, so a step can go between two).
  ordinal REAL NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('step', 'stuck')),
  body_md TEXT NOT NULL,
  -- The version this row replaces (an edit, a tombstone or an undo).
  supersedes_id TEXT REFERENCES workbench_steps(id),
  -- A tombstone: the step is deleted (its text kept on the row).
  deleted INTEGER NOT NULL DEFAULT 0 CHECK (deleted IN (0, 1)),
  client_idempotency_key TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (session_id, client_idempotency_key)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
