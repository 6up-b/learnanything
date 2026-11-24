---
title: "desk_windows"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite desk_windows"
  - "table desk_windows"
table_name: "desk_windows"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "262_reader_workbench_foundations.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/262_reader_workbench_foundations.sql"
  - "src/learnloop/companion/search.py"
  - "src/learnloop/db/stores/desks.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `desk_windows`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives desk window a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `window_id`, `desk_id`, `slot`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> A window on a desk. slot orders the strip (0..n-1 among open windows); a pair is two open windows sharing a slot with panes 0 and 1, and active marks the pair's active pane. spec_json holds the window's content reference (or a pad stack's entries); view_json its scroll anchor and view settings. A closed window keeps its row (closed_at) so a close can be undone; its slot is then meaningless.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/262_reader_workbench_foundations.sql`.
- **Schema touched by:** `262_reader_workbench_foundations.sql`, `271_reader_workbench_preparing_windows.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `window_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `desk_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/desks\|desks.desk_id]] | Stored value |
| `slot` | `INTEGER` | yes | — | — | Stored value |
| `pane` | `INTEGER` | yes | `0` | — | Stored value |
| `active` | `INTEGER` | yes | `1` | — | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `spec_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `view_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `opened_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `closed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `desk_id` → [[Reference/Database/Tables/desks|`desks.desk_id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_desk_windows_desk` on `desk_id`, `closed_at`, `slot`, `pane`.
- `sqlite_autoindex_desk_windows_1` on `window_id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/companion/search.py`
- `src/learnloop/db/stores/desks.py`

### Direct SQL writers

- `src/learnloop/db/stores/desks.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/reader_rd0_migration_helpers.py`
- `tests/test_reader_rd0_protocol.py`
- `tests/test_reader_rd_retire_migration.py`

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
CREATE TABLE "desk_windows" (
  window_id TEXT PRIMARY KEY,
  desk_id TEXT NOT NULL REFERENCES desks(desk_id),
  slot INTEGER NOT NULL CHECK (slot >= 0),
  pane INTEGER NOT NULL DEFAULT 0 CHECK (pane IN (0, 1)),
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
  kind TEXT NOT NULL CHECK (kind IN (
    'source', 'video', 'pad', 'pad_stack', 'lesson', 'thread', 'compare', 'panel', 'figure_notebook', 'preparing'
  )),
  spec_json TEXT NOT NULL,
  view_json TEXT NOT NULL DEFAULT '{}',
  opened_at TEXT NOT NULL,
  closed_at TEXT
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
