---
title: "practice_pool_surfaces"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite practice_pool_surfaces"
  - "table practice_pool_surfaces"
schema_head: 157
table_name: "practice_pool_surfaces"
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
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `practice_pool_surfaces`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives practice pool surface a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `pool_id`, `surface_id`, `admission_status`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Pool surfaces: reviewed practice surfaces, each with a rotation `angle` and named provenance. `admission_status` is the U-028 owner gate -- a surface is never servable until 'admitted'. `surface_id` links the resolved P0 activity surface once the deterministic stub / minter has produced it.

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
| `pool_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/practice_pools\|practice_pools.id]] | Stored value |
| `surface_slug` | `TEXT` | yes | — | — | Stored value |
| `angle` | `TEXT` | yes | — | — | Stored value |
| `provenance` | `TEXT` | yes | `'llm_within_bounds'` | — | Stored value |
| `surface_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `admission_status` | `TEXT` | yes | `'candidate'` | — | Stored value |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `pool_id` → [[Reference/Database/Tables/practice_pools|`practice_pools.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_practice_pool_surfaces_pool` on `pool_id`.
- `sqlite_autoindex_practice_pool_surfaces_2` on `pool_id`, `surface_slug` (unique).
- `sqlite_autoindex_practice_pool_surfaces_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.practice_pool_surfaces_for()`
- `Repository.register_practice_pool_surface()`
- `Repository.set_practice_pool_surface_admission()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/substrate/surface_pool.py`

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
CREATE TABLE practice_pool_surfaces (
  id TEXT PRIMARY KEY,
  pool_id TEXT NOT NULL REFERENCES practice_pools(id) ON DELETE CASCADE,
  surface_slug TEXT NOT NULL,
  angle TEXT NOT NULL,
  provenance TEXT NOT NULL DEFAULT 'llm_within_bounds',
  surface_id TEXT,
  admission_status TEXT NOT NULL DEFAULT 'candidate'
    CHECK (admission_status IN ('candidate', 'admitted', 'rejected')),
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(pool_id, surface_slug)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
