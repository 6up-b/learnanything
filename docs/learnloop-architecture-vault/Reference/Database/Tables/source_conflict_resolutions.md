---
title: "source_conflict_resolutions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite source_conflict_resolutions"
  - "table source_conflict_resolutions"
schema_head: 157
table_name: "source_conflict_resolutions"
table_role: "receipt"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "051_maintenance_feed.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/051_maintenance_feed.sql"
  - "src/learnloop/content/proposals/conflict_resolution.py"
  - "src/learnloop/db/repositories.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_conflict_resolutions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records explicit resolutions of source conflict without erasing the original evidence so canonical-source work can be retried without losing provenance or silently changing its input set. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `conflict_id`, `resolution_kind`, `actor`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §10.2 Conflict-resolution audit: resolution is a LATER explicit action with its own audit history (prefer-for-context / keep-both-scoped / notation-mapping / dismiss). Resolving preserves both evidence locators and every prior decision.

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/051_maintenance_feed.sql`.
- **Schema touched by:** `051_maintenance_feed.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `conflict_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/source_conflicts\|source_conflicts.id]] | Stored value |
| `resolution_kind` | `TEXT` | yes | — | — | Stored value |
| `resolution_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `actor` | `TEXT` | no | — | — | Stored value |
| `rationale` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `conflict_id` → [[Reference/Database/Tables/source_conflicts|`source_conflicts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_source_conflict_resolutions_conflict` on `conflict_id`.
- `sqlite_autoindex_source_conflict_resolutions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.resolve_source_conflict()`
- `Repository.source_conflict_resolutions()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/proposals/conflict_resolution.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_maintenance_feed.py`

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
CREATE TABLE source_conflict_resolutions (
  id TEXT PRIMARY KEY,
  conflict_id TEXT NOT NULL REFERENCES source_conflicts(id),
  resolution_kind TEXT NOT NULL CHECK (
    resolution_kind IN ('prefer_for_context', 'keep_both_scoped', 'notation_mapping', 'dismiss')
  ),
  resolution_json TEXT NOT NULL,
  actor TEXT,
  rationale TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
