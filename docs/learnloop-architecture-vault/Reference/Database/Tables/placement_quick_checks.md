---
title: "placement_quick_checks"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "c89c84851bd6efb2023a8365288d63d797f70a63"
source_commit_timestamp: "2026-10-17T15:04:44-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite placement_quick_checks"
  - "table placement_quick_checks"
schema_head: 208
table_name: "placement_quick_checks"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "172_placement_assumptions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/172_placement_assumptions.sql"
  - "src/learnloop/db/stores/placement.py"
  - "src/learnloop/diagnosis/quick_check.py"
  - "src/learnloop/placement/decisions.py"
  - "src/learnloop/placement/state.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `placement_quick_checks`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives placement quick check a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `calibration_session_id`, `session_id`, `request_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Queue state of the optional "Check what I already know". The calibration session row keeps the budget and stop/expiry; this keeps the scope, k and the moment its results fed the split.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/172_placement_assumptions.sql`.
- **Schema touched by:** `172_placement_assumptions.sql`, `173_placement_quick_check_presentations.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `calibration_session_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/probe_calibration_sessions\|probe_calibration_sessions.id]] | Stored value |
| `session_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `learning_object_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `k` | `INTEGER` | yes | — | — | Stored value |
| `budget_minutes` | `INTEGER` | yes | — | — | Stored value |
| `predictor` | `TEXT` | yes | — | — | Stored value |
| `predictor_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `finished_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `outcome_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `request_id` | `TEXT` | no | — | — | Application-validated soft reference |

## Relationships and access paths

Declared SQLite foreign keys:

- `calibration_session_id` → [[Reference/Database/Tables/probe_calibration_sessions|`probe_calibration_sessions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `placement_quick_checks_request` on `request_id` (unique).
- `sqlite_autoindex_placement_quick_checks_1` on `calibration_session_id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/diagnosis/quick_check.py`
- `src/learnloop/placement/decisions.py`

### Direct SQL writers

- `src/learnloop/db/stores/placement.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_assumed_known.py`
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
CREATE TABLE placement_quick_checks (
  calibration_session_id TEXT PRIMARY KEY REFERENCES probe_calibration_sessions(id),
  session_id TEXT NOT NULL,
  learning_object_ids_json TEXT NOT NULL,
  k INTEGER NOT NULL CHECK (k >= 1),
  budget_minutes INTEGER NOT NULL CHECK (budget_minutes >= 1),
  predictor TEXT NOT NULL,
  predictor_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  finished_at TEXT,
  outcome_json TEXT
, request_id TEXT);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
