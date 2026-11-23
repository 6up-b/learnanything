---
title: "desks"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite desks"
  - "table desks"
table_name: "desks"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "262_reader_workbench_foundations.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/262_reader_workbench_foundations.sql"
  - "src/learnloop/companion/asks.py"
  - "src/learnloop/companion/history.py"
  - "src/learnloop/companion/search.py"
  - "src/learnloop/db/stores/desks.py"
  - "src/learnloop/desks/__init__.py"
  - "src/learnloop/desks/workspace.py"
  - "src/learnloop/pads/blocks.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `desks`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives desk a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `desk_id`, `focus_window_id`, `goal_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/262_reader_workbench_foundations.sql`.
- **Schema touched by:** `262_reader_workbench_foundations.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `desk_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `title` | `TEXT` | yes | — | — | Stored value |
| `position` | `TEXT` | yes | — | — | Stored value |
| `focus_window_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `goal_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `companion_dock` | `TEXT` | yes | `'br'` | — | Stored value |
| `companion_shown` | `INTEGER` | yes | `0` | — | Stored value |
| `version` | `INTEGER` | yes | `1` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `archived_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_desks_1` on `desk_id` (unique).

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

- `tests/desk_helpers.py`
- `tests/reader_rd0_migration_helpers.py`
- `tests/test_architecture.py`
- `tests/test_mobile_allowlist.py`
- `tests/test_pad_stale_edits_stacks_and_passage_reads.py`
- `tests/test_reader_rd0_fences.py`
- `tests/test_reader_rd0_protocol.py`
- `tests/test_reader_rd0_reads.py`
- `tests/test_reader_rd0_rpcs.py`
- `tests/test_reader_rd1_model_parity.py`
- `tests/test_reader_rd3a_companion_ask.py`
- `tests/test_reader_rd4_rpcs.py`

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
CREATE TABLE desks (
  desk_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  position TEXT NOT NULL,
  focus_window_id TEXT,
  goal_id TEXT,
  companion_dock TEXT NOT NULL DEFAULT 'br' CHECK (companion_dock IN ('br', 'bl', 'right', 'cb')),
  companion_shown INTEGER NOT NULL DEFAULT 0 CHECK (companion_shown IN (0, 1)),
  version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  archived_at TEXT
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
