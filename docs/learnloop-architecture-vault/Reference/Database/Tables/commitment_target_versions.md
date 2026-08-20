---
title: "commitment_target_versions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite commitment_target_versions"
  - "table commitment_target_versions"
schema_head: 156
table_name: "commitment_target_versions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "072_commitments.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/072_commitments.sql"
  - "src/learnloop/curriculum/commitments.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/authoring/rung_variants.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `commitment_target_versions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins immutable versions of commitment target so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It supplies replay-stable input rather than a disposable cache. Rows bind `commitment_version_id`, `target_kind`, `target_ref`, making the operational relationship explicit. ^table-purpose

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/072_commitments.sql`.
- **Schema touched by:** `072_commitments.sql`, `074_activity_contract_extensions.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `commitment_version_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/commitment_versions\|commitment_versions.id]] | Stored value |
| `target_kind` | `TEXT` | yes | — | — | Stored value |
| `target_ref` | `TEXT` | yes | — | — | Stored value |
| `salience` | `REAL` | no | — | — | Stored value |
| `role` | `TEXT` | yes | — | — | Stored value |
| `provenance_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `commitment_version_id` → [[Reference/Database/Tables/commitment_versions|`commitment_versions.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_ctv_version` on `commitment_version_id`.
- `sqlite_autoindex_commitment_target_versions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository._insert_commitment_version_rows()`
- `Repository.commitment_targets_for_version()`
- `Repository.commitments_targeting()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/authoring/rung_variants.py`
- `src/learnloop/curriculum/commitments.py`
- `src/learnloop/db/repositories.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_commitments.py`

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
CREATE TABLE commitment_target_versions (
  id TEXT PRIMARY KEY,
  commitment_version_id TEXT NOT NULL
    REFERENCES commitment_versions(id) ON DELETE CASCADE,
  target_kind TEXT NOT NULL CHECK (target_kind IN (
    'p0_target_exemplar', 'canonical_facet', 'learning_object',
    'source_locator', 'legacy_practice_item')),
  target_ref TEXT NOT NULL,                       -- kind-specific id, bare TEXT
  salience REAL,
  role TEXT NOT NULL CHECK (role IN ('required', 'optional')),
  provenance_json TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
