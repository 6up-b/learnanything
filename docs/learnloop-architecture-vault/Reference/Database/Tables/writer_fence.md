---
title: "writer_fence"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite writer_fence"
  - "table writer_fence"
table_name: "writer_fence"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "275_writer_fence.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/275_writer_fence.sql"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/content/pipeline/jobs.py"
  - "src/learnloop/daily_plan/probe_continuation.py"
  - "src/learnloop/db/connection.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/db/writer_fence.py"
  - "src/learnloop/diagnosis/probe_offer.py"
  - "src/learnloop/projects/experiment_store.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `writer_fence`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives writer fence a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `algorithm_version`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/275_writer_fence.sql`.
- **Schema touched by:** `275_writer_fence.sql`, `276_writer_fence_more_writes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `INTEGER` | no | — | PRIMARY KEY | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- No secondary index is declared beyond any rowid/primary-key storage.

Database triggers:

- `writer_fence_no_delete` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository._connect()`
- `Repository._initialize()`

### Direct SQL readers

None found by exact static reference scan.

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/db/repositories.py`
- `src/learnloop/projects/experiment_store.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/connection_reuse.py`
- `tests/helpers.py`
- `tests/test_architecture.py`
- `tests/test_connection_reuse.py`
- `tests/test_mcp_tools.py`
- `tests/test_probe_router_episode_owner.py`
- `tests/test_sidecar_contract.py`
- `tests/test_writer_fence.py`
- `tests/test_writer_fence_recovery.py`
- `tests/test_writer_fence_scopes.py`
- `tests/writer_fence_helpers.py`
- `tests/writer_fence_migration_helpers.py`

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
CREATE TABLE writer_fence (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    algorithm_version TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
