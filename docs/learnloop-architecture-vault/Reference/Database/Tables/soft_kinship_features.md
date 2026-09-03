---
title: "soft_kinship_features"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite soft_kinship_features"
  - "table soft_kinship_features"
schema_head: 157
table_name: "soft_kinship_features"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "activity-substrate"
introduced_in: "077_familiarity_namespace.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/077_familiarity_namespace.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/learner/familiarity.py"
  - "src/learnloop/scheduling/kinship_feature.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `soft_kinship_features`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives soft kinship feature a stable database identity so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It supplies replay-stable input rather than a disposable cache. Rows bind `surface_id`, `feature_schema_version`, making the operational relationship explicit. ^table-purpose

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/077_familiarity_namespace.sql`.
- **Schema touched by:** `077_familiarity_namespace.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `surface_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_surfaces\|activity_surfaces.id]] | Stored value |
| `feature_schema_version` | `TEXT` | yes | — | — | Stored value |
| `features_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `surface_id` → [[Reference/Database/Tables/activity_surfaces|`activity_surfaces.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_soft_kinship_features_2` on `surface_id`, `feature_schema_version` (unique).
- `sqlite_autoindex_soft_kinship_features_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.soft_kinship_features_for_surface()`
- `Repository.upsert_soft_kinship_features()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/learner/familiarity.py`
- `src/learnloop/scheduling/kinship_feature.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_table_roles.py`
- `tests/test_laddered_stems.py`

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
CREATE TABLE soft_kinship_features (
  id TEXT PRIMARY KEY,
  surface_id TEXT NOT NULL REFERENCES activity_surfaces(id) ON DELETE CASCADE,
  feature_schema_version TEXT NOT NULL,
  -- §4.2 feature vector: NEVER a pre-collapsed group id. Target/facet overlap,
  -- source/shared-stimulus proximity, recipe overlap, representation/answer match,
  -- parameter/template relationship, semantic similarity, angle distance, recency,
  -- exposure count, feedback reveal.
  features_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(surface_id, feature_schema_version)
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
