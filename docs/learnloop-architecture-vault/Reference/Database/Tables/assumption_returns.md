---
title: "assumption_returns"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "915228c379af9ccecb25f5e3f642d63e97d1b294"
source_commit_timestamp: "2026-10-19T21:54:42-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite assumption_returns"
  - "table assumption_returns"
schema_head: 214
table_name: "assumption_returns"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "172_placement_assumptions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/172_placement_assumptions.sql"
  - "src/learnloop/daily_plan/router_card.py"
  - "src/learnloop/db/stores/placement.py"
  - "src/learnloop/placement/decisions.py"
  - "src/learnloop/placement/report.py"
  - "src/learnloop/placement/state.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `assumption_returns`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives assumption return a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `assumption_id`, `learning_object_id`, `algorithm_version`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> "I don't know this": an immediate return to learning. assumption_id is the open assumption it closed, or NULL when the LO was not assumed (the report still keeps the LO out of fast-track).

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/172_placement_assumptions.sql`.
- **Schema touched by:** `172_placement_assumptions.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `assumption_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/assumption_decisions\|assumption_decisions.id]] | Stored value |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `reason` | `TEXT` | yes | — | — | Stored value |
| `trigger_ref` | `TEXT` | no | — | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `assumption_id` → [[Reference/Database/Tables/assumption_decisions|`assumption_decisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `assumption_returns_lo` on `learning_object_id`, `created_at`, `id`.
- `sqlite_autoindex_assumption_returns_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/daily_plan/router_card.py`
- `src/learnloop/placement/report.py`
- `src/learnloop/placement/state.py`

### Direct SQL writers

- `src/learnloop/db/stores/placement.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_assumed_known.py`

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
CREATE TABLE assumption_returns (
  id TEXT PRIMARY KEY,
  assumption_id TEXT REFERENCES assumption_decisions(id),
  learning_object_id TEXT NOT NULL,
  reason TEXT NOT NULL CHECK (reason IN ('dont_know_this')),
  trigger_ref TEXT,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
