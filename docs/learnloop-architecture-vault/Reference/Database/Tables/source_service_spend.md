---
title: "source_service_spend"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "9380a9135d4cc3b80dd6b3c5c57807d5331cee25"
source_commit_timestamp: "2026-10-13T10:30:13-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite source_service_spend"
  - "table source_service_spend"
schema_head: 191
table_name: "source_service_spend"
table_role: "workflow"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "191_source_service_spend.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/191_source_service_spend.sql"
  - "src/learnloop/db/stores/source_service.py"
  - "src/learnloop/source_retrieval/service_spend.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_service_spend`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Shares the canonical-sources service's daily money cap (source_service.max_daily_cost_usd) across every process that opens the vault: one row per metered request admitted under it, reserved inside one BEGIN IMMEDIATE transaction that checks the day's total (every row, plus the service's receipts no row covers, such as spend from before the table existed) plus the estimate, so a sidecar and a CLI batch cannot both spend the same allowance. In flight a row counts its estimate (reconciled upward); once the request finished it counts the reported cost, else the estimate; the request's root receipt names its row (`budget_json.envelope_reservations`), so it is counted once. Subscription requests reserve nothing. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `envelope`, `day`, `reserved_usd`, making the operational relationship explicit. ^table-purpose

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/191_source_service_spend.sql`.
- **Schema touched by:** `191_source_service_spend.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `envelope` | `TEXT` | yes | — | — | Stored value |
| `day` | `TEXT` | yes | — | — | Stored value |
| `reserved_usd` | `REAL` | yes | — | — | Stored value |
| `charged_usd` | `REAL` | yes | — | — | Stored value |
| `state` | `TEXT` | yes | — | — | Stored value |
| `process` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_source_service_spend_day` on `envelope`, `day`.
- `sqlite_autoindex_source_service_spend_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/source_service.py`

### Direct SQL writers

- `src/learnloop/db/stores/source_service.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

No table-specific test contains the table name or a detected repository method call. The schema/role invariants are still pinned by `tests/test_migrations.py` and `tests/test_table_roles.py`.

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
CREATE TABLE source_service_spend (
  id TEXT PRIMARY KEY,
  envelope TEXT NOT NULL,
  day TEXT NOT NULL,
  reserved_usd REAL NOT NULL CHECK (reserved_usd >= 0),
  charged_usd REAL NOT NULL CHECK (charged_usd >= 0),
  state TEXT NOT NULL CHECK (state IN ('in_flight', 'settled')),
  process TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
