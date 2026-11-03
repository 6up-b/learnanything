---
title: "decision_measurement_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "55154e0388c3526da2d1a55ac4d850cea630f066"
source_commit_timestamp: "2026-11-03T13:30:51-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite decision_measurement_events"
  - "table decision_measurement_events"
schema_head: 239
table_name: "decision_measurement_events"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "239_data_capture.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/239_data_capture.sql"
  - "src/learnloop/daily_plan/measurement.py"
  - "src/learnloop/db/stores/data_capture.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `decision_measurement_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of decision measurement so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `decision_id`, `practice_item_id`, `attempt_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/239_data_capture.sql`.
- **Schema touched by:** `239_data_capture.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `decision_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/decision_objectives\|decision_objectives.decision_id]] | Stored value |
| `state` | `TEXT` | yes | — | — | Stored value |
| `reason` | `TEXT` | yes | `''` | — | Stored value |
| `practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `detail_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `decision_id` → [[Reference/Database/Tables/decision_objectives|`decision_objectives.decision_id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `decision_measurement_events_decision` on `decision_id`, `created_at`.
- `sqlite_autoindex_decision_measurement_events_2` on `decision_id`, `state`, `reason` (unique).
- `sqlite_autoindex_decision_measurement_events_1` on `id` (unique).

Database triggers:

- `decision_measurement_events_no_delete` — schema-enforced lifecycle or immutability constraint.
- `decision_measurement_events_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/daily_plan/measurement.py`
- `src/learnloop/db/stores/data_capture.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_data_capture_migration.py`

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
CREATE TABLE decision_measurement_events (
  id TEXT PRIMARY KEY,
  decision_id TEXT NOT NULL REFERENCES decision_objectives(decision_id),
  state TEXT NOT NULL CHECK (state IN ('due', 'offered', 'answered', 'unavailable')),
  reason TEXT NOT NULL DEFAULT '',
  practice_item_id TEXT,
  attempt_id TEXT,
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  UNIQUE (decision_id, state, reason)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
