---
title: "pads"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite pads"
  - "table pads"
table_name: "pads"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "262_reader_workbench_foundations.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/262_reader_workbench_foundations.sql"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/algorithm_versions.py"
  - "src/learnloop/companion/search.py"
  - "src/learnloop/db/stores/learner_gaps.py"
  - "src/learnloop/db/stores/pad_reads.py"
  - "src/learnloop/db/stores/pads.py"
  - "src/learnloop/desks/content_ref.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `pads`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives pad a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `pad_id`, `home_desk_id`, `workbench_session_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> A scratchpad. Pads belong to the library: archiving a desk leaves its pads here. version counts the applied pad-level ops (title, keep); block edits are versioned per block instead.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/262_reader_workbench_foundations.sql`.
- **Schema touched by:** `262_reader_workbench_foundations.sql`, `266_reader_workbench_pads.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `pad_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `title` | `TEXT` | yes | `''` | — | Stored value |
| `kept` | `INTEGER` | yes | `0` | — | Stored value |
| `home_desk_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `workbench_session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `lesson_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `version` | `INTEGER` | yes | `1` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `archived_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_pads_home_desk` on `home_desk_id`, `kind`.
- `sqlite_autoindex_pads_1` on `pad_id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/companion/search.py`
- `src/learnloop/db/stores/pad_reads.py`
- `src/learnloop/db/stores/pads.py`

### Direct SQL writers

- `src/learnloop/db/stores/pads.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/desk_helpers.py`
- `tests/identity_pins_helpers.py`
- `tests/ink_helpers.py`
- `tests/reader_rd0_migration_helpers.py`
- `tests/reader_rd4_helpers.py`
- `tests/test_architecture.py`
- `tests/test_menu_elsewhere_and_proposals.py`
- `tests/test_mobile_allowlist.py`
- `tests/test_notebook_pad_cells.py`
- `tests/test_pad_stale_edits_stacks_and_passage_reads.py`
- `tests/test_reader_rd0_fences.py`
- `tests/test_reader_rd0_guards_migration.py`
- `tests/test_reader_rd0_migration.py`
- `tests/test_reader_rd0_protocol.py`
- `tests/test_reader_rd0_rpcs.py`
- `tests/test_reader_rd3_fix_backend.py`
- `tests/test_reader_rd3a_search.py`
- `tests/test_reader_rd4_carried_and_proposals.py`
- `tests/test_reader_rd4_emission.py`
- `tests/test_reader_rd4_migration.py`

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
CREATE TABLE pads (
  pad_id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('running', 'named', 'problem', 'ink', 'lesson_additions')),
  title TEXT NOT NULL DEFAULT '',
  kept INTEGER NOT NULL DEFAULT 0 CHECK (kept IN (0, 1)),
  home_desk_id TEXT,
  workbench_session_id TEXT,
  lesson_id TEXT,
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
