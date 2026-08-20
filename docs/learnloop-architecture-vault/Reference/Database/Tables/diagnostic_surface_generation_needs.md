---
title: "diagnostic_surface_generation_needs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite diagnostic_surface_generation_needs"
  - "table diagnostic_surface_generation_needs"
schema_head: 156
table_name: "diagnostic_surface_generation_needs"
table_role: "workflow"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "147_diagnostic_surface_generation_needs.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/147_diagnostic_surface_generation_needs.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/diagnostic_surface_supply.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `diagnostic_surface_generation_needs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Queues an identified supply gap for diagnostic surface generation so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `learning_object_id`, `consumed_practice_item_id`, `target_key`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/147_diagnostic_surface_generation_needs.sql`.
- **Schema touched by:** `147_diagnostic_surface_generation_needs.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `consumed_practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `target_key` | `TEXT` | yes | — | — | Stored value |
| `missing_capability` | `TEXT` | yes | — | — | Stored value |
| `facet_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `misconception_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `resolved_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_diagnostic_surface_needs_lo` on `learning_object_id`, `status`.
- `sqlite_autoindex_diagnostic_surface_generation_needs_2` on `consumed_practice_item_id` (unique).
- `sqlite_autoindex_diagnostic_surface_generation_needs_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.diagnostic_surface_generation_needs()`
- `Repository.resolve_diagnostic_surface_generation_need()`
- `Repository.upsert_diagnostic_surface_generation_need()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/diagnostic_surface_supply.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_diagnostic_probe_freshness.py`
- `tests/test_probe_pool_empty.py`
- `tests/test_probe_remint.py`

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
CREATE TABLE diagnostic_surface_generation_needs (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT NOT NULL,
  consumed_practice_item_id TEXT NOT NULL,  -- the administered single-use surface
  target_key TEXT NOT NULL,                 -- facet signature the replacement must cover
  missing_capability TEXT NOT NULL,         -- 'diagnostic_probe_surface'
  facet_ids_json TEXT NOT NULL DEFAULT '[]',
  misconception_ids_json TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL CHECK (status IN ('pending', 'resolved', 'declined')),
  created_at TEXT NOT NULL,
  resolved_at TEXT,
  UNIQUE (consumed_practice_item_id)
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
