---
title: "depth_milestone_versions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite depth_milestone_versions"
  - "table depth_milestone_versions"
schema_head: 156
table_name: "depth_milestone_versions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "072_commitments.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/072_commitments.sql"
  - "src/learnloop/curriculum/depth_edge_authoring.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/curriculum/depth_rungs.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `depth_milestone_versions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins immutable versions of depth milestone so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It supplies replay-stable input rather than a disposable cache. Rows bind `envelope_version_id`, `content_hash`, `milestone_slug`, making the operational relationship explicit. ^table-purpose

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/072_commitments.sql`.
- **Schema touched by:** `072_commitments.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `envelope_version_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/depth_envelope_versions\|depth_envelope_versions.id]] | Stored value |
| `milestone_slug` | `TEXT` | yes | — | — | Stored value |
| `task_contract_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `entry_evidence_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `exit_evidence_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `fresh_proof_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `expected_burden_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `envelope_version_id` → [[Reference/Database/Tables/depth_envelope_versions|`depth_envelope_versions.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_depth_milestone_envelope` on `envelope_version_id`.
- `sqlite_autoindex_depth_milestone_versions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.depth_milestone_version_for()`
- `Repository.insert_depth_milestone_version()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/depth_edge_authoring.py`
- `src/learnloop/curriculum/depth_rungs.py`

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
CREATE TABLE depth_milestone_versions (
  id TEXT PRIMARY KEY,
  envelope_version_id TEXT NOT NULL
    REFERENCES depth_envelope_versions(id) ON DELETE CASCADE,
  milestone_slug TEXT NOT NULL,
  task_contract_json TEXT NOT NULL,
  entry_evidence_json TEXT,
  exit_evidence_json TEXT,
  fresh_proof_json TEXT,
  expected_burden_json TEXT,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
