---
title: "controller_candidates"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite controller_candidates"
  - "table controller_candidates"
schema_head: 157
table_name: "controller_candidates"
table_role: "workflow"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "096_controller_snapshots.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/096_controller_snapshots.sql"
  - "src/learnloop/scheduling/controller_store.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `controller_candidates`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Holds candidates for controller while policy selects or reviews one so queue and controller decisions can resume safely and explain why an activity was selected. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `decision_id`, `learning_object_id`, `comparator_score`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Every considered candidate with its feasibility verdict, typed exclusion reasons, within-mode ranking metrics, and selected flag (§3.2). A score can never resurrect an infeasible candidate: `selected` is only ever set on a `feasible=1` row.

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/096_controller_snapshots.sql`.
- **Schema touched by:** `096_controller_snapshots.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `decision_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/controller_decisions\|controller_decisions.id]] | Stored value |
| `candidate_ref` | `TEXT` | yes | — | — | Stored value |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `feasible` | `INTEGER` | yes | `0` | — | Stored value |
| `exclusion_reasons_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `within_mode_metrics_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `comparator_score` | `REAL` | no | — | — | Stored value |
| `selected` | `INTEGER` | yes | `0` | — | Stored value |
| `rank_ordinal` | `INTEGER` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `decision_id` → [[Reference/Database/Tables/controller_decisions|`controller_decisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_controller_candidates_decision` on `decision_id`.
- `sqlite_autoindex_controller_candidates_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/scheduling/controller_store.py`

### Direct SQL writers

- `src/learnloop/scheduling/controller_store.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`

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
CREATE TABLE controller_candidates (
  id TEXT PRIMARY KEY,
  decision_id TEXT NOT NULL REFERENCES controller_decisions(id),
  candidate_ref TEXT NOT NULL,
  learning_object_id TEXT,
  feasible INTEGER NOT NULL DEFAULT 0 CHECK (feasible IN (0, 1)),
  exclusion_reasons_json TEXT NOT NULL DEFAULT '[]',
  within_mode_metrics_json TEXT NOT NULL DEFAULT '{}',
  comparator_score REAL,
  selected INTEGER NOT NULL DEFAULT 0 CHECK (selected IN (0, 1)),
  rank_ordinal INTEGER,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
