---
title: "placement_quick_check_items"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "8fc4dea3cf9af37970a1a03f0c6064a4e1b37a62"
source_commit_timestamp: "2026-10-12T18:37:04-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite placement_quick_check_items"
  - "table placement_quick_check_items"
schema_head: 176
table_name: "placement_quick_check_items"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "173_placement_quick_check_presentations.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/173_placement_quick_check_presentations.sql"
  - "src/learnloop/db/stores/placement.py"
  - "src/learnloop/placement/decisions.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `placement_quick_check_items`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives placement quick check item a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `calibration_session_id`, `practice_item_id`, `learning_object_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> One row per item the quick check presented, at most k per check. Only the first attempt on a presented item, in the check's practice session, after the presentation and before the check's stop/expiry boundary, is bound to it; only bound attempts are the check's results.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/173_placement_quick_check_presentations.sql`.
- **Schema touched by:** `173_placement_quick_check_presentations.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `calibration_session_id` | `TEXT` | yes | — | PRIMARY KEY; FK → [[Reference/Database/Tables/placement_quick_checks\|placement_quick_checks.calibration_session_id]] | Stored value |
| `ordinal` | `INTEGER` | yes | — | PRIMARY KEY | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `presented_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `answered_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `calibration_session_id` → [[Reference/Database/Tables/placement_quick_checks|`placement_quick_checks.calibration_session_id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `placement_quick_check_items_attempt` on `attempt_id` (unique).
- `sqlite_autoindex_placement_quick_check_items_2` on `calibration_session_id`, `practice_item_id` (unique).
- `sqlite_autoindex_placement_quick_check_items_1` on `calibration_session_id`, `ordinal` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/placement/decisions.py`

### Direct SQL writers

- `src/learnloop/db/stores/placement.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_quick_check.py`

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
CREATE TABLE placement_quick_check_items (
  calibration_session_id TEXT NOT NULL
    REFERENCES placement_quick_checks(calibration_session_id),
  ordinal INTEGER NOT NULL CHECK (ordinal >= 1),
  practice_item_id TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  presented_at TEXT NOT NULL,
  attempt_id TEXT,
  answered_at TEXT,
  PRIMARY KEY (calibration_session_id, ordinal),
  UNIQUE (calibration_session_id, practice_item_id),
  CHECK ((attempt_id IS NULL) = (answered_at IS NULL))
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
