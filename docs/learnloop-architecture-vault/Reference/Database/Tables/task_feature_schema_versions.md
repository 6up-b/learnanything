---
title: "task_feature_schema_versions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite task_feature_schema_versions"
  - "table task_feature_schema_versions"
schema_head: 156
table_name: "task_feature_schema_versions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "073_activity_patterns_and_features.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/073_activity_patterns_and_features.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/authoring/exercise_authoring.py"
  - "src/learnloop/curriculum/depth_edge_authoring.py"
  - "src/learnloop/curriculum/rung_backfill.py"
  - "src/learnloop/substrate/activity_patterns.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `task_feature_schema_versions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins immutable versions of task feature schema so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `content_hash`, `schema_slug`, `version`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/073_activity_patterns_and_features.sql`.
- **Schema touched by:** `073_activity_patterns_and_features.sql`, `074_activity_contract_extensions.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `schema_slug` | `TEXT` | yes | — | — | Stored value |
| `version` | `INTEGER` | yes | — | — | Stored value |
| `dimensions_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_task_feature_schema_versions_2` on `schema_slug`, `version` (unique).
- `sqlite_autoindex_task_feature_schema_versions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.ensure_task_feature_schema_version()`
- `Repository.task_feature_schema_version()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/authoring/exercise_authoring.py`
- `src/learnloop/curriculum/depth_edge_authoring.py`
- `src/learnloop/curriculum/rung_backfill.py`
- `src/learnloop/substrate/activity_patterns.py`

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
CREATE TABLE task_feature_schema_versions (
  id TEXT PRIMARY KEY,
  schema_slug TEXT NOT NULL,
  version INTEGER NOT NULL,
  -- complexity / transfer / representation / response / scaffolding / time / tools / span (§3.4).
  dimensions_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(schema_slug, version)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
