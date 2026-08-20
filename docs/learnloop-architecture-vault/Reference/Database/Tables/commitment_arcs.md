---
title: "commitment_arcs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite commitment_arcs"
  - "table commitment_arcs"
schema_head: 156
table_name: "commitment_arcs"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "095_commitment_arcs.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/095_commitment_arcs.sql"
  - "src/learnloop/curriculum/depth_edge_authoring.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/reader/reader_capture.py"
  - "src/learnloop_sidecar/handlers/reader.py"
  - "src/learnloop/content/sources/source_deletion.py"
  - "src/learnloop/curriculum/commitment_arcs.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `commitment_arcs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives commitment arc a stable database identity so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It supplies replay-stable input rather than a disposable cache. Rows bind `commitment_id`, `source_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/095_commitment_arcs.sql`.
- **Schema touched by:** `095_commitment_arcs.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `commitment_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/commitments\|commitments.id]] | Stored value |
| `source_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `commitment_id` → [[Reference/Database/Tables/commitments|`commitments.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_commitment_arcs_source` on `source_id`.
- `idx_commitment_arcs_commitment` on `commitment_id`.
- `sqlite_autoindex_commitment_arcs_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.arcs_for_commitment()`
- `Repository.arcs_for_source()`
- `Repository.commitment_arc()`
- `Repository.create_commitment_arc()`
- `Repository.delete_source_artifact()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/curriculum/commitment_arcs.py`
- `src/learnloop/reader/reader_capture.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_commitment_arcs.py`
- `tests/test_p3_journeys.py`
- `tests/test_reader_capture.py`
- `tests/test_source_deletion.py`

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
CREATE TABLE commitment_arcs (
  id TEXT PRIMARY KEY,
  commitment_id TEXT NOT NULL REFERENCES commitments(id),
  source_id TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
