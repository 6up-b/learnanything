---
title: "item_forecast_payloads"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "99e32cd003f2677d0c129a75140bd1a0df72b3cf"
source_commit_timestamp: "2026-10-20T16:16:52-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite item_forecast_payloads"
  - "table item_forecast_payloads"
schema_head: 215
table_name: "item_forecast_payloads"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "213_adaptive_difficulty_receipts.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/213_adaptive_difficulty_receipts.sql"
  - "src/learnloop/adaptive_difficulty/outside.py"
  - "src/learnloop/db/stores/ad_receipts.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `item_forecast_payloads`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives item forecast payload a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `content_hash`, `owner_key`, `forecaster`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §8.1: the raw request and response of a paid outside forecaster (and of the feature audit's LLM fallback); the receipt keeps the hash. WORKFLOW: pruned after router.payload_retention_days, like router_decision_payloads.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/213_adaptive_difficulty_receipts.sql`.
- **Schema touched by:** `213_adaptive_difficulty_receipts.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `owner_key` | `TEXT` | yes | — | — | Stored value |
| `forecaster` | `TEXT` | yes | — | — | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `content_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_item_forecast_payloads_created` on `created_at`.
- `sqlite_autoindex_item_forecast_payloads_2` on `owner_key`, `kind` (unique).
- `sqlite_autoindex_item_forecast_payloads_1` on `id` (unique).

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

- `tests/ad_fakes.py`
- `tests/test_ad1_codex_rereview_fixes.py`
- `tests/test_ad1_codex_review_fixes.py`
- `tests/test_ad1_migration.py`
- `tests/test_adaptive_difficulty_ad1.py`
- `tests/test_architecture.py`

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
CREATE TABLE item_forecast_payloads (
  id TEXT PRIMARY KEY,
  -- The forecast receipt (forecast_receipts.receipt_key) or audit the payload
  -- belongs to.
  owner_key TEXT NOT NULL,
  forecaster TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('request', 'response')),
  content_hash TEXT NOT NULL,
  content_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (owner_key, kind)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
