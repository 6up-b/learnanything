---
title: "canonical_mapping_proposals"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite canonical_mapping_proposals"
  - "table canonical_mapping_proposals"
schema_head: 156
table_name: "canonical_mapping_proposals"
table_role: "workflow"
functionality_status: "active"
domain_family: "reader"
introduced_in: "094_source_objects.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/094_source_objects.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/reader/source_objects.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/reader"
---

# `canonical_mapping_proposals`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives canonical mapping proposal a stable database identity so reader interactions remain anchored to durable source content as extraction and rendering evolve. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `source_object_id`, `annotation_id`, `target_kind`, making the operational relationship explicit. ^table-purpose

It belongs to the **reader** navigation family. The family context lives in [[Database Catalog#Reader]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/094_source_objects.sql`.
- **Schema touched by:** `094_source_objects.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `source_object_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/source_objects\|source_objects.id]] | Stored value |
| `annotation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `target_kind` | `TEXT` | yes | — | — | Stored value |
| `target_ref` | `TEXT` | no | — | — | Stored value |
| `confidence` | `REAL` | no | — | — | Stored value |
| `status` | `TEXT` | yes | `'proposed'` | — | Stored value |
| `rationale` | `TEXT` | no | — | — | Stored value |
| `provenance_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `decided_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `source_object_id` → [[Reference/Database/Tables/source_objects|`source_objects.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_canonical_mapping_proposals_status` on `status`, `created_at`.
- `idx_canonical_mapping_proposals_obj` on `source_object_id`.
- `sqlite_autoindex_canonical_mapping_proposals_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.create_mapping_proposal()`
- `Repository.decide_mapping_proposal()`
- `Repository.mapping_proposals()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/reader/source_objects.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_reader_requests.py`

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
CREATE TABLE canonical_mapping_proposals (
  id TEXT PRIMARY KEY,
  source_object_id TEXT REFERENCES source_objects(id),
  annotation_id TEXT,
  target_kind TEXT NOT NULL
    CHECK (target_kind IN ('facet', 'lo', 'blueprint', 'commitment', 'new_object')),
  target_ref TEXT,
  confidence REAL,
  status TEXT NOT NULL DEFAULT 'proposed'
    CHECK (status IN ('proposed', 'accepted', 'rejected')),
  rationale TEXT,
  provenance_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  decided_at TEXT
);
```

## Related notes

- [[Database Catalog#Reader|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
