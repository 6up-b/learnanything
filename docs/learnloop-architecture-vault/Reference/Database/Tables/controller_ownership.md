---
title: "controller_ownership"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite controller_ownership"
  - "table controller_ownership"
schema_head: 156
table_name: "controller_ownership"
table_role: "workflow"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "099_controller_ownership.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/099_controller_ownership.sql"
  - "src/learnloop/diagnosis/probe_episodes.py"
  - "src/learnloop/goals/exam_pool.py"
  - "src/learnloop/params/parameter_registry.py"
  - "src/learnloop/scheduling/controller_cutover.py"
  - "src/learnloop/scheduling/controller_ownership.py"
  - "src/learnloop/scheduling/scheduler.py"
  - "src/learnloop/scheduling/staged_policy.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `controller_ownership`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives controller ownership a stable database identity so queue and controller decisions can resume safely and explain why an activity was selected. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `commitment_id`, `receipt_id`, `ownership_version`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> The rebuildable current-owner head projection (design §A.2: commitment_id -> owner). Deterministically re-derivable by folding controller_ownership_events; kept as a head for the scheduler's per-build ownership-exclusion read.

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/099_controller_ownership.sql`.
- **Schema touched by:** `099_controller_ownership.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `commitment_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `owner` | `TEXT` | yes | — | — | Stored value |
| `ownership_version` | `INTEGER` | yes | — | — | Stored value |
| `policy_version` | `INTEGER` | yes | — | — | Stored value |
| `receipt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `assigned_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_controller_ownership_owner` on `owner`.
- `sqlite_autoindex_controller_ownership_1` on `commitment_id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/scheduling/controller_ownership.py`

### Direct SQL writers

- `src/learnloop/scheduling/controller_ownership.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_architecture.py`
- `tests/test_controller_cutover.py`
- `tests/test_controller_ownership.py`
- `tests/test_cross_seam_exposure.py`
- `tests/test_dual_authority_administration.py`

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
CREATE TABLE controller_ownership (
  commitment_id TEXT PRIMARY KEY,
  owner TEXT NOT NULL CHECK (owner IN ('staged', 'legacy')),
  ownership_version INTEGER NOT NULL,
  policy_version INTEGER NOT NULL,
  receipt_id TEXT NOT NULL,
  assigned_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
