---
title: "session_receipts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "c85c9c438e2298d0425a7a4000cdfdb0b5660d9f"
source_commit_timestamp: "2026-11-06T06:28:25-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite session_receipts"
  - "table session_receipts"
schema_head: 247
table_name: "session_receipts"
table_role: "receipt"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "243_router_objective_receipts.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/243_router_objective_receipts.sql"
  - "src/learnloop/daily_plan/engine.py"
  - "src/learnloop/daily_plan/objective_inputs.py"
  - "src/learnloop/db/stores/router_objective.py"
  - "src/learnloop/router_objective/report.py"
  - "src/learnloop/router_objective/sessions.py"
  - "src/learnloop/router_objective/stop_coin.py"
  - "src/learnloop_sidecar/handlers/sessions.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `session_receipts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Freezes the inputs and outcome of each session decision so queue and controller decisions can resume safely and explain why an activity was selected. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `session_id`, `plan_id`, `block_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Rows 7 and 8 (RECEIPT): one 'availability' row stamped before a session's first block, one 'end' row, and a 'stop_response' row each time an offered stop was overridden (the session goes on, so it is no end). Immutable; missing availability is recorded as missing (minutes_source = 'missing'), and an end nobody reported is marked 'inferred'.

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Receipt]].

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
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `minutes_offered` | `REAL` | no | — | — | Stored value |
| `minutes_source` | `TEXT` | no | — | — | Stored value |
| `local_time` | `TEXT` | no | — | — | Stored value |
| `time_zone` | `TEXT` | no | — | — | Stored value |
| `utc_offset_minutes` | `INTEGER` | no | — | — | Stored value |
| `device` | `TEXT` | no | — | — | Stored value |
| `external_window_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `end_reason` | `TEXT` | no | — | — | Stored value |
| `end_basis` | `TEXT` | no | — | — | Stored value |
| `ended_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `plan_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `block_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `stop_decision_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `detail_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `receipt_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `session_receipts_created` on `created_at`.
- `session_receipts_once` on `session_id`, `kind` (unique).
- `sqlite_autoindex_session_receipts_1` on `id` (unique).

Database triggers:

- `session_receipts_no_delete` — schema-enforced lifecycle or immutability constraint.
- `session_receipts_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/daily_plan/objective_inputs.py`
- `src/learnloop/db/stores/router_objective.py`
- `src/learnloop/router_objective/report.py`
- `src/learnloop/router_objective/sessions.py`
- `src/learnloop/router_objective/stop_coin.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_ro0_gate.py`
- `tests/test_ro0_report.py`
- `tests/test_ro0_rows7_8_sessions.py`
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
CREATE TABLE session_receipts (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  kind TEXT NOT NULL CHECK (kind IN ('availability', 'end', 'stop_response')),
  minutes_offered REAL,
  minutes_source TEXT,
  local_time TEXT,
  time_zone TEXT,
  utc_offset_minutes INTEGER,
  device TEXT,
  -- Filled by a later m1nty bridge; no integration exists in this repository.
  external_window_json TEXT,
  end_reason TEXT CHECK (end_reason IS NULL OR end_reason IN (
    'offered_stop_accepted', 'offered_stop_overridden', 'unprompted_stop', 'app_closed', 'foreground_lost',
    'external_interruption', 'rule', 'unknown'
  )),
  end_basis TEXT CHECK (end_basis IS NULL OR end_basis IN ('explicit', 'inferred')),
  ended_at TEXT,
  plan_id TEXT,
  block_id TEXT,
  stop_decision_id TEXT,
  detail_json TEXT NOT NULL DEFAULT '{}',
  receipt_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK ((kind = 'availability') = (minutes_source IS NOT NULL)),
  CHECK (kind = 'availability' OR (end_reason IS NOT NULL AND end_basis IS NOT NULL)),
  CHECK (session_id IS NOT NULL OR kind = 'stop_response')
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
