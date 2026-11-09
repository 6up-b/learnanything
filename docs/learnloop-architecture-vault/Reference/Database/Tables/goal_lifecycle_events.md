---
title: "goal_lifecycle_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "53222a3c7f94a77acea81ca9d7a02c0621e4badc"
source_commit_timestamp: "2026-11-08T23:13:15-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite goal_lifecycle_events"
  - "table goal_lifecycle_events"
schema_head: 251
table_name: "goal_lifecycle_events"
table_role: "receipt"
functionality_status: "active"
domain_family: "goals-and-exams"
introduced_in: "243_router_objective_receipts.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/243_router_objective_receipts.sql"
  - "src/learnloop/db/stores/router_objective.py"
  - "src/learnloop/router_objective/report.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/goals-and-exams"
---

# `goal_lifecycle_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves the ordered lifecycle transitions for goal so goal progress and held-out certification remain tied to the contract and evidence that produced them. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `goal_id`, `contract_version_id`, `previous_status`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Row 11 (RECEIPT): a goal's lifecycle as it was seen at load, for what versioned contracts do not cover: status lives in the vault's YAML. 'abandoned' has no writer yet: the vault's status has no such value, so a removal while active says so in its reason.

It belongs to the **goals and exams** navigation family. The family context lives in [[Database Catalog#Goals And Exams]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/243_router_objective_receipts.sql`.
- **Schema touched by:** `243_router_objective_receipts.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `goal_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `event` | `TEXT` | yes | — | — | Stored value |
| `reason` | `TEXT` | yes | — | — | Stored value |
| `status` | `TEXT` | no | — | — | Stored value |
| `previous_status` | `TEXT` | no | — | — | Stored value |
| `due_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `previous_due_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `contract_version_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `occurred_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `receipt_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `goal_lifecycle_events_goal` on `goal_id`, `created_at`.
- `sqlite_autoindex_goal_lifecycle_events_1` on `id` (unique).

Database triggers:

- `goal_lifecycle_events_no_delete` — schema-enforced lifecycle or immutability constraint.
- `goal_lifecycle_events_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/router_objective.py`
- `src/learnloop/router_objective/report.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_ro0_codex_review.py`
- `tests/test_ro0_gate.py`
- `tests/test_ro0_report.py`
- `tests/test_ro0_row11_goal_lifecycle.py`
- `tests/test_router_objective_migration.py`

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
CREATE TABLE goal_lifecycle_events (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  event TEXT NOT NULL CHECK (event IN (
    'created', 'date_changed', 'paused', 'resumed', 'expired', 'abandoned', 'completed', 'removed'
  )),
  reason TEXT NOT NULL,
  status TEXT,
  previous_status TEXT,
  due_at TEXT,
  previous_due_at TEXT,
  contract_version_id TEXT,
  occurred_at TEXT,
  receipt_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Goals And Exams|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
