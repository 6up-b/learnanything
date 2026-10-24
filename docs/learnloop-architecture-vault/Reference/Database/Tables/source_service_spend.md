---
title: "source_service_spend"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "0c0349bdaeae1bba20f10ba6c0bd3c9c898bbbfd"
source_commit_timestamp: "2026-10-24T19:21:28-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite source_service_spend"
  - "table source_service_spend"
schema_head: 219
table_name: "source_service_spend"
table_role: "workflow"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "194_source_service_spend.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/194_source_service_spend.sql"
  - "src/learnloop/db/stores/source_service.py"
  - "src/learnloop/hints/map_builder.py"
  - "src/learnloop/source_retrieval/library_ask.py"
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

Shares the canonical-sources service's daily money cap (source_service.max_daily_cost_usd) across every process that opens the vault: one row per metered request admitted under it, reserved inside one BEGIN IMMEDIATE transaction that recovers orphaned rows and checks the day's total plus the estimate, so a sidecar and a CLI batch cannot both spend the same allowance. One accounting function (service_spend_accounting) gives that total for admission, recovery and reports, counting each request once with the receipts naming its row (`budget_json.envelope_reservations`): while its owner's lease (`lease_expires_at`, renewed while the process lives) holds, a row counts the larger of its charge and its receipts; once reconciled (`settled`), its receipts (its reconciled cost bounding a lost finish); an orphan is reconciled with its receipts or `released` when it has none (`resolved_by` names the owner or recovery), and a receipt naming a released row cannot start, so its request is never sent. A `legacy` row, written before receipts named rows, counts its charge and suppresses no receipt (no durable identity ties one to it; an amount or a second-resolution stamp is no identity), so its charge and every unlinked receipt count and the receipts started in its lifetime are reported as `legacy.uncertain_usd`; a receipt naming no row counts by its own cost. A receipt's dollars are its reported cost, else its tokens at the rate its request recorded, else at the owner's service rate. Subscription requests reserve nothing. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `envelope`, `day`, `reserved_usd`, making the operational relationship explicit. ^table-purpose

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/194_source_service_spend.sql`.
- **Schema touched by:** `194_source_service_spend.sql`, `195_source_service_spend_accounting.sql`.
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
| `legacy` | `INTEGER` | yes | `0` | — | Stored value |
| `process` | `TEXT` | yes | — | — | Stored value |
| `lease_expires_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `resolved_by` | `TEXT` | no | — | — | Stored value |
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

None found by exact static reference scan.

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_approach_maps.py`
- `tests/test_exam_protection.py`
- `tests/test_figures_rpc.py`
- `tests/test_hint_outcome.py`
- `tests/test_reader_rw3b_review_fixes.py`
- `tests/test_source_service_spend_accounting.py`
- `tests/test_source_service_spend_envelopes.py`

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
CREATE TABLE "source_service_spend" (
  id TEXT PRIMARY KEY,
  envelope TEXT NOT NULL,
  day TEXT NOT NULL,
  reserved_usd REAL NOT NULL CHECK (reserved_usd >= 0),
  charged_usd REAL NOT NULL CHECK (charged_usd >= 0),
  state TEXT NOT NULL CHECK (state IN ('in_flight', 'settled', 'released')),
  legacy INTEGER NOT NULL DEFAULT 0 CHECK (legacy IN (0, 1)),
  process TEXT NOT NULL,
  lease_expires_at TEXT,
  resolved_by TEXT CHECK (resolved_by IS NULL OR resolved_by IN ('owner', 'recovery')),
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
