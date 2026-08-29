---
title: "parameter_registry_manifests"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite parameter_registry_manifests"
  - "table parameter_registry_manifests"
schema_head: 156
table_name: "parameter_registry_manifests"
table_role: "receipt"
functionality_status: "active"
domain_family: "schema-and-change"
introduced_in: "069_parameter_registry.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/069_parameter_registry.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/params/parameter_registry.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/schema-and-change"
---

# `parameter_registry_manifests`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins the complete input identity for parameter registry so schema changes and reviewed mutations remain reproducible and auditable. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `algorithm_version`, `manifest_hash`, `frozen_at`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> (c) Immutable frozen manifest per algorithm version (replay reproducibility).

It belongs to the **schema and change** navigation family. The family context lives in [[Database Catalog#Schema And Change]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/069_parameter_registry.sql`.
- **Schema touched by:** `069_parameter_registry.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `manifest_hash` | `TEXT` | yes | — | — | Stored value |
| `entries_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `frozen_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_parameter_registry_manifests_2` on `algorithm_version` (unique).
- `sqlite_autoindex_parameter_registry_manifests_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.insert_parameter_registry_manifest()`
- `Repository.parameter_registry_manifest()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/params/parameter_registry.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_p0_cutover_mvp08.py`

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
CREATE TABLE parameter_registry_manifests (
  id TEXT PRIMARY KEY,
  algorithm_version TEXT NOT NULL,     -- 'mvp-0.6','mvp-0.7','mvp-0.8'
  manifest_hash TEXT NOT NULL,         -- _canonical_hash over entries_json
  entries_json TEXT NOT NULL,          -- {path:{value_hash,status,lifecycle,source}}
  frozen_at TEXT NOT NULL,
  UNIQUE(algorithm_version)            -- one frozen manifest per version
);
```

## Related notes

- [[Database Catalog#Schema And Change|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
