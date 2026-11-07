---
title: "decision_objectives"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "bc9eadcc88232d3af229b26b721d88b037e39f7d"
source_commit_timestamp: "2026-11-07T01:13:16-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite decision_objectives"
  - "table decision_objectives"
schema_head: 250
table_name: "decision_objectives"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "240_data_capture.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/240_data_capture.sql"
  - "src/learnloop/daily_plan/measurement.py"
  - "src/learnloop/db/stores/data_capture.py"
  - "src/learnloop/db/stores/router_objective.py"
  - "src/learnloop/router/first_delayed_success.py"
  - "src/learnloop/router/outcomes.py"
  - "src/learnloop/router_objective/report.py"
  - "src/learnloop/router_objective/trajectory.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `decision_objectives`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives decision objective a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `decision_id`, `learning_object_id`, `commitment_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/240_data_capture.sql`.
- **Schema touched by:** `240_data_capture.sql`, `243_router_objective_receipts.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `decision_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/router_decisions\|router_decisions.id]] | Stored value |
| `decision_kind` | `TEXT` | yes | — | — | Stored value |
| `objective_version` | `TEXT` | yes | — | — | Stored value |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `source` | `TEXT` | yes | — | — | Stored value |
| `scope_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `arm` | `TEXT` | yes | — | — | Stored value |
| `support_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `measurement` | `TEXT` | yes | — | — | Stored value |
| `commitment_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `pick_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `experiment_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `delay_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

Declared SQLite foreign keys:

- `decision_id` → [[Reference/Database/Tables/router_decisions|`router_decisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `decision_objectives_commitment` on `commitment_id`.
- `decision_objectives_lo` on `learning_object_id`, `created_at`.
- `sqlite_autoindex_decision_objectives_1` on `decision_id` (unique).

Database triggers:

- `decision_objectives_no_delete` — schema-enforced lifecycle or immutability constraint.
- `decision_objectives_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/daily_plan/measurement.py`
- `src/learnloop/db/stores/data_capture.py`
- `src/learnloop/router/first_delayed_success.py`
- `src/learnloop/router_objective/report.py`
- `src/learnloop/router_objective/trajectory.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_data_capture_landing_review.py`
- `tests/test_data_capture_migration.py`
- `tests/test_data_capture_successor.py`
- `tests/test_followup_router.py`
- `tests/test_ro0_codex_verify.py`
- `tests/test_ro0_row10_cold_timing.py`
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
CREATE TABLE decision_objectives (
  decision_id TEXT PRIMARY KEY REFERENCES router_decisions(id),
  decision_kind TEXT NOT NULL,
  objective_version TEXT NOT NULL,
  learning_object_id TEXT,
  source TEXT NOT NULL,
  scope_json TEXT NOT NULL,
  arm TEXT NOT NULL,
  support_json TEXT NOT NULL,
  -- arranged: a check commitment measures it; shared: another pending check on
  -- the LO does; natural: left to ordinary retrievals (no real choice was made);
  -- unavailable: nothing to measure with (reason on its decision_measurement_events row).
  measurement TEXT NOT NULL CHECK (measurement IN ('arranged', 'shared', 'natural', 'unavailable')),
  commitment_id TEXT,
  practice_item_id TEXT,
  pick_json TEXT NOT NULL DEFAULT '{}',
  experiment_id TEXT,
  created_at TEXT NOT NULL
, delay_json TEXT);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
