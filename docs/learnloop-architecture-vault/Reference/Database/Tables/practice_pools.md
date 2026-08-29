---
title: "practice_pools"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite practice_pools"
  - "table practice_pools"
schema_head: 156
table_name: "practice_pools"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "085_surface_pool.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/085_surface_pool.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/substrate/surface_pool.py"
  - "src/learnloop_sidecar/handlers/ladder.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `practice_pools`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives practice pool a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `blueprint_version_id`, `content_hash`, `pool_slug`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/085_surface_pool.sql`.
- **Schema touched by:** `085_surface_pool.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `pool_slug` | `TEXT` | yes | — | — | Stored value |
| `blueprint_version_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/task_blueprint_versions\|task_blueprint_versions.id]] | Stored value |
| `status` | `TEXT` | yes | `'draft'` | — | Stored value |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `blueprint_version_id` → [[Reference/Database/Tables/task_blueprint_versions|`task_blueprint_versions.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_practice_pools_blueprint` on `blueprint_version_id`.
- `sqlite_autoindex_practice_pools_2` on `pool_slug` (unique).
- `sqlite_autoindex_practice_pools_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.ensure_practice_pool()`
- `Repository.practice_pool()`
- `Repository.practice_pool_by_slug()`
- `Repository.practice_pools_for_blueprint()`
- `Repository.transition_practice_pool()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/substrate/surface_pool.py`
- `src/learnloop_sidecar/handlers/ladder.py`

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
CREATE TABLE practice_pools (
  id TEXT PRIMARY KEY,
  pool_slug TEXT NOT NULL,
  blueprint_version_id TEXT NOT NULL
    REFERENCES task_blueprint_versions(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft', 'reviewed', 'active', 'retired')),
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(pool_slug)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
