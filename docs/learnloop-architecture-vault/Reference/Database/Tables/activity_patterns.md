---
title: "activity_patterns"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite activity_patterns"
  - "table activity_patterns"
schema_head: 157
table_name: "activity_patterns"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "activity-substrate"
introduced_in: "073_activity_patterns_and_features.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/073_activity_patterns_and_features.sql"
  - "src/learnloop/content/authoring/exercise_authoring.py"
  - "src/learnloop/content/authoring/practice_generation.py"
  - "src/learnloop/curriculum/depth_edge_authoring.py"
  - "src/learnloop/curriculum/depth_rungs.py"
  - "src/learnloop/curriculum/pattern_ladder.py"
  - "src/learnloop/curriculum/rung_backfill.py"
  - "src/learnloop/curriculum/task_blueprints.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/substrate/activity_patterns.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `activity_patterns`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives activity pattern a stable database identity so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It supplies replay-stable input rather than a disposable cache. Rows bind `pattern_slug`, making the operational relationship explicit. ^table-purpose

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/073_activity_patterns_and_features.sql`.
- **Schema touched by:** `073_activity_patterns_and_features.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `pattern_slug` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_activity_patterns_2` on `pattern_slug` (unique).
- `sqlite_autoindex_activity_patterns_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.activity_pattern_version_by_slug()`
- `Repository.ensure_activity_pattern()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop/substrate/activity_patterns.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/depth_edge_authoring.py`
- `src/learnloop/substrate/activity_patterns.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_activity_contract_extensions.py`
- `tests/test_activity_patterns.py`

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
CREATE TABLE activity_patterns (
  id TEXT PRIMARY KEY,
  pattern_slug TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
