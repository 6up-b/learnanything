---
title: "ink_strokes"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite ink_strokes"
  - "table ink_strokes"
table_name: "ink_strokes"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "267_reader_workbench_ink.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/267_reader_workbench_ink.sql"
  - "src/learnloop/db/stores/ink_strokes.py"
  - "src/learnloop/pads/ink.py"
  - "src/learnloop/pads/ink_transcribe.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `ink_strokes`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives ink stroke a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `ink_id`, `owner_id`, `client_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/267_reader_workbench_ink.sql`.
- **Schema touched by:** `267_reader_workbench_ink.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `ink_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `owner_kind` | `TEXT` | yes | — | — | Stored value |
| `owner_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `encoding` | `TEXT` | yes | — | — | Stored value |
| `strokes_blob` | `BLOB` | yes | — | — | Stored value |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `stroke_count` | `INTEGER` | yes | — | — | Stored value |
| `pointer_meta` | `TEXT` | yes | `'{}'` | — | Stored value |
| `client_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_ink_strokes_owner` on `owner_kind`, `owner_id`.
- `sqlite_autoindex_ink_strokes_1` on `ink_id` (unique).

Database triggers:

- `ink_strokes_no_delete` — schema-enforced lifecycle or immutability constraint.
- `ink_strokes_no_replace` — schema-enforced lifecycle or immutability constraint.
- `ink_strokes_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/ink_strokes.py`

### Direct SQL writers

- `src/learnloop/db/stores/ink_strokes.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/reader_rd8a_migration_helpers.py`
- `tests/test_architecture.py`
- `tests/test_reader_rd8a_ink.py`
- `tests/test_reader_rd8a_migration.py`

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
CREATE TABLE ink_strokes (
  ink_id TEXT PRIMARY KEY,
  owner_kind TEXT NOT NULL CHECK (owner_kind IN ('block', 'annotation', 'source')),
  owner_id TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('strokes', 'erase')),
  encoding TEXT NOT NULL CHECK (encoding IN ('zlib-json-v1')),
  strokes_blob BLOB NOT NULL,
  content_hash TEXT NOT NULL,
  stroke_count INTEGER NOT NULL CHECK (stroke_count >= 1),
  pointer_meta TEXT NOT NULL DEFAULT '{}',
  client_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
