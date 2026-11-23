---
title: "companion_exchange_context"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite companion_exchange_context"
  - "table companion_exchange_context"
table_name: "companion_exchange_context"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "262_reader_workbench_foundations.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/262_reader_workbench_foundations.sql"
  - "src/learnloop/companion/history.py"
  - "src/learnloop/db/stores/span_projections.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `companion_exchange_context`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives companion exchange context a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `question_event_id`, `desk_id`, `goal_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Where a tutor exchange happened, recorded when it is asked from a desk (origin 'live'). An exchange with no row was asked before desks existed; the history reads it as such and nothing is written for it.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/262_reader_workbench_foundations.sql`.
- **Schema touched by:** `262_reader_workbench_foundations.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `question_event_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `desk_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `surface` | `TEXT` | yes | — | — | Stored value |
| `window_spec_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `pad_block_ids_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `goal_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `origin` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_companion_exchange_context_desk` on `desk_id`.
- `sqlite_autoindex_companion_exchange_context_1` on `question_event_id` (unique).

Database triggers:

- `companion_exchange_context_no_delete` — schema-enforced lifecycle or immutability constraint.
- `companion_exchange_context_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/companion/history.py`
- `src/learnloop/db/stores/span_projections.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/reader_rd0_migration_helpers.py`
- `tests/test_reader_rd0_migration.py`

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
CREATE TABLE companion_exchange_context (
  question_event_id TEXT PRIMARY KEY,
  desk_id TEXT,
  surface TEXT NOT NULL,
  window_spec_json TEXT,
  pad_block_ids_json TEXT,
  goal_id TEXT,
  origin TEXT NOT NULL CHECK (origin IN ('live', 'backfill')),
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
