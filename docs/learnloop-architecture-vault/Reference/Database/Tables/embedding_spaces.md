---
title: "embedding_spaces"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "0048ada3be44b48136e2f7be0ce1d4eb666912be"
source_commit_timestamp: "2026-10-27T15:49:04-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite embedding_spaces"
  - "table embedding_spaces"
schema_head: 226
table_name: "embedding_spaces"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "220_retrieval_spaces.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/220_retrieval_spaces.sql"
  - "src/learnloop/db/stores/retrieval_spaces.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `embedding_spaces`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives embedding space a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `space_id`, `status_reason`, `name`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/220_retrieval_spaces.sql`.
- **Schema touched by:** `220_retrieval_spaces.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `space_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `name` | `TEXT` | yes | — | — | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `pins_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | — | — | Stored value |
| `status_reason` | `TEXT` | no | — | — | Stored value |
| `canaries_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `retired_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_embedding_spaces_1` on `space_id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/retrieval_spaces.py`

### Direct SQL writers

- `src/learnloop/db/stores/retrieval_spaces.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_retrieval_spaces_migration.py`

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
CREATE TABLE embedding_spaces (
  space_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('local', 'hosted', 'incumbent')),
  pins_json TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active', 'fallback', 'incumbent', 'retired', 'epoch_drift')),
  status_reason TEXT,
  canaries_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  retired_at TEXT
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
