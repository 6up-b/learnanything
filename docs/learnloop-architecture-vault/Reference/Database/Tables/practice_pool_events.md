---
title: "practice_pool_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite practice_pool_events"
  - "table practice_pool_events"
schema_head: 156
table_name: "practice_pool_events"
table_role: "receipt"
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
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `practice_pool_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of practice pool so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `pool_id`, `surface_slug`, `kind`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Append-only admission / rotation ledger (U-028 artifacts-not-API-calls): every register / review / admit / reject / activate / serve / rotate decision is a durable, reviewable record.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
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
| `surface_slug` | `TEXT` | no | — | — | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `detail_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `author` | `TEXT` | yes | `'owner'` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `pool_id` → [[Reference/Database/Tables/practice_pools|`practice_pools.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_practice_pool_events_pool` on `pool_id`, `created_at`.
- `sqlite_autoindex_practice_pool_events_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.append_practice_pool_event()`
- `Repository.ensure_practice_pool()`
- `Repository.practice_pool_events_for()`
- `Repository.set_practice_pool_surface_admission()`
- `Repository.transition_practice_pool()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/substrate/surface_pool.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_surface_pool.py`

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
CREATE TABLE practice_pool_events (
  id TEXT PRIMARY KEY,
  pool_id TEXT NOT NULL REFERENCES practice_pools(id) ON DELETE CASCADE,
  surface_slug TEXT,
  kind TEXT NOT NULL CHECK (kind IN (
    'registered', 'reviewed', 'admitted', 'rejected', 'activated', 'retired',
    'served', 'rotated')),
  detail_json TEXT,
  author TEXT NOT NULL DEFAULT 'owner',
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
