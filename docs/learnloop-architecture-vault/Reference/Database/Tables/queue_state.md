---
title: "queue_state"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite queue_state"
  - "table queue_state"
schema_head: 157
table_name: "queue_state"
table_role: "workflow"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "117_question_promotion_jobs_and_queue_revision.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/117_question_promotion_jobs_and_queue_revision.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/authoring/item_authoring.py"
  - "src/learnloop/content/pipeline/jobs.py"
  - "src/learnloop/content/pipeline/runner.py"
  - "src/learnloop/diagnosis/probe_remint.py"
  - "src/learnloop/tutor/promotions.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `queue_state`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Stores the mutable practice queue head and its workflow position. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `singleton`, `revision`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> A single durable high-water mark lets Today poll cheaply.  Queue-affecting mutations bump it; the expensive scheduler RPC is called only after change.

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/117_question_promotion_jobs_and_queue_revision.sql`.
- **Schema touched by:** `117_question_promotion_jobs_and_queue_revision.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `singleton` | `INTEGER` | no | — | PRIMARY KEY | Stored value |
| `revision` | `INTEGER` | yes | `0` | — | Stored value |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- No secondary index is declared beyond any rowid/primary-key storage.

## Who calls it

### Repository access surface

- `Repository.bump_queue_revision()`
- `Repository.queue_revision()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/authoring/item_authoring.py`
- `src/learnloop/content/pipeline/jobs.py`
- `src/learnloop/content/pipeline/runner.py`
- `src/learnloop/diagnosis/probe_remint.py`
- `src/learnloop/tutor/promotions.py`
- `src/learnloop_sidecar/context.py`
- `src/learnloop_sidecar/handlers/item_authoring.py`
- `src/learnloop_sidecar/handlers/queue.py`
- `src/learnloop_sidecar/handlers/tutor_qa.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`
- `tests/test_question_promotions.py`
- `tests/test_question_promotion_jobs.py`
- `tests/test_vault_watcher_refresh.py`

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
CREATE TABLE queue_state (
  singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
  revision INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
