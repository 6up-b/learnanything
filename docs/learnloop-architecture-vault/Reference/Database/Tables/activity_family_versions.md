---
title: "activity_family_versions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite activity_family_versions"
  - "table activity_family_versions"
schema_head: 157
table_name: "activity_family_versions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "activity-substrate"
introduced_in: "065_activity_lineage_substrate.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/065_activity_lineage_substrate.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/substrate/activities.py"
  - "src/learnloop/substrate/compat/activity_backfill.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `activity_family_versions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins immutable versions of activity family so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It supplies replay-stable input rather than a disposable cache. Rows bind `family_id`, `version`, making the operational relationship explicit. ^table-purpose

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/065_activity_lineage_substrate.sql`.
- **Schema touched by:** `065_activity_lineage_substrate.sql`, `074_activity_contract_extensions.sql`, `079_progression_and_lapse.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `family_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_families\|activity_families.id]] | Stored value |
| `version` | `INTEGER` | yes | — | — | Stored value |
| `family_spec_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `family_id` → [[Reference/Database/Tables/activity_families|`activity_families.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_activity_family_versions_family` on `family_id`.
- `sqlite_autoindex_activity_family_versions_2` on `family_id`, `version` (unique).
- `sqlite_autoindex_activity_family_versions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.activity_family_authoring_purposes()`
- `Repository.activity_family_version_family_id()`
- `Repository.ensure_activity_family_version()`
- `Repository.upsert_activity_family_authoring()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/substrate/activities.py`
- `src/learnloop/substrate/compat/activity_backfill.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_activity_backfill.py`
- `tests/test_activity_substrate.py`

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
CREATE TABLE activity_family_versions (
  id TEXT PRIMARY KEY,
  family_id TEXT NOT NULL REFERENCES activity_families(id) ON DELETE CASCADE,
  version INTEGER NOT NULL CHECK (version >= 1),
  family_spec_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(family_id, version)
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
