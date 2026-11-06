---
title: "decision_state_receipts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "6cad8141ecef068e53fce83d54802d5a726e0b95"
source_commit_timestamp: "2026-11-06T08:54:29-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite decision_state_receipts"
  - "table decision_state_receipts"
schema_head: 249
table_name: "decision_state_receipts"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "243_router_objective_receipts.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/243_router_objective_receipts.sql"
  - "src/learnloop/db/stores/router_objective.py"
  - "src/learnloop/router_objective/report.py"
  - "src/learnloop/router_objective/tail_data.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `decision_state_receipts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Freezes the inputs and outcome of each decision state decision so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `decision_id`, `session_id`, `decision_kind`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Rows 9 and 13 (RECEIPT): what the router believed at one decision, ids and numbers only: per candidate item FSRS S, D, R and due; per candidate LO mastery, AD p-bar and P_band, open factors and hypothesis posteriors; goals and contracts in force; versions; session and day active minutes; predicted minutes and their source; pending reports; the stop that was offered and not taken; the VOI verdict in force for a pick. Canonical JSON, zlib-compressed.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/243_router_objective_receipts.sql`.
- **Schema touched by:** `243_router_objective_receipts.sql`, `246_router_objective_traces.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `decision_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/router_decisions\|router_decisions.id]] | Stored value |
| `decision_kind` | `TEXT` | yes | — | — | Stored value |
| `receipt_version` | `TEXT` | yes | — | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `ad_state_hash` | `TEXT` | no | — | — | Stored value |
| `session_active_minutes` | `REAL` | no | — | — | Stored value |
| `day_active_minutes` | `REAL` | no | — | — | Stored value |
| `pending_reports` | `INTEGER` | no | — | — | Stored value |
| `candidate_items` | `INTEGER` | yes | — | — | Stored value |
| `candidate_los` | `INTEGER` | yes | — | — | Stored value |
| `state_z` | `BLOB` | yes | — | — | Stored value |
| `raw_bytes` | `INTEGER` | yes | — | — | Stored value |
| `stored_bytes` | `INTEGER` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `decision_id` → [[Reference/Database/Tables/router_decisions|`router_decisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `decision_state_receipts_created` on `created_at`.
- `sqlite_autoindex_decision_state_receipts_2` on `decision_id` (unique).
- `sqlite_autoindex_decision_state_receipts_1` on `id` (unique).

Database triggers:

- `decision_state_receipts_no_delete` — schema-enforced lifecycle or immutability constraint.
- `decision_state_receipts_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/router_objective.py`
- `src/learnloop/router_objective/report.py`
- `src/learnloop/router_objective/tail_data.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_ro0_gate.py`
- `tests/test_ro0_report.py`
- `tests/test_ro0_rows9_13_decision_state.py`
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
CREATE TABLE decision_state_receipts (
  id TEXT PRIMARY KEY,
  decision_id TEXT NOT NULL UNIQUE REFERENCES router_decisions(id),
  decision_kind TEXT NOT NULL,
  receipt_version TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  session_id TEXT,
  ad_state_hash TEXT,
  session_active_minutes REAL,
  day_active_minutes REAL,
  pending_reports INTEGER,
  candidate_items INTEGER NOT NULL CHECK (candidate_items >= 0),
  candidate_los INTEGER NOT NULL CHECK (candidate_los >= 0),
  state_z BLOB NOT NULL,
  raw_bytes INTEGER NOT NULL,
  stored_bytes INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
