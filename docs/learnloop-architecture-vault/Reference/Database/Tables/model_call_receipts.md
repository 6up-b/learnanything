---
title: "model_call_receipts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "0395ae32f9e2e40d1cb98b38402631299a94003f"
source_commit_timestamp: "2026-09-07T12:49:13-04:00"
last_verified: "2026-09-07"
aliases:
  - "state.sqlite model_call_receipts"
  - "table model_call_receipts"
schema_head: 163
table_name: "model_call_receipts"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "160_model_call_receipts.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/160_model_call_receipts.sql"
  - "src/learnloop/db/stores/model_calls.py"
  - "src/learnloop/substrate/data_quality.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `model_call_receipts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Captures each started model operation and physical request, preserving returned text, failures and available provider usage for later cost and quality analysis. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `parent_call_id`, `owner_id`, `provider_response_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> A started receipt survives a process interruption; NULL usage is unknown, never zero cost. Checkpoints contain reusable validated provider work.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/160_model_call_receipts.sql`.
- **Schema touched by:** `160_model_call_receipts.sql`, `163_provider_receipt_details.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `parent_call_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/model_call_receipts\|model_call_receipts.id]] | Stored value |
| `owner_kind` | `TEXT` | yes | — | — | Stored value |
| `owner_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `purpose` | `TEXT` | yes | — | — | Stored value |
| `provider` | `TEXT` | no | — | — | Stored value |
| `model` | `TEXT` | no | — | — | Stored value |
| `prompt_hash` | `TEXT` | no | — | — | Stored value |
| `schema_hash` | `TEXT` | no | — | — | Stored value |
| `input_text` | `TEXT` | no | — | — | Stored value |
| `schema_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `output_text` | `TEXT` | no | — | — | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `started_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `finished_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `input_tokens` | `INTEGER` | no | — | — | Stored value |
| `output_tokens` | `INTEGER` | no | — | — | Stored value |
| `cached_input_tokens` | `INTEGER` | no | — | — | Stored value |
| `reasoning_tokens` | `INTEGER` | no | — | — | Stored value |
| `cost` | `REAL` | no | — | — | Stored value |
| `provider_response_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `finish_reason` | `TEXT` | no | — | — | Stored value |
| `error_type` | `TEXT` | no | — | — | Stored value |
| `output_budget_tokens` | `INTEGER` | no | — | — | Stored value |
| `collection_version` | `TEXT` | yes | `'learnloop-events-v1'` | — | Stored value |
| `endpoint` | `TEXT` | no | — | — | Stored value |
| `resolved_model` | `TEXT` | no | — | — | Stored value |
| `cache_write_tokens` | `INTEGER` | no | — | — | Stored value |
| `usage_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

Declared SQLite foreign keys:

- `parent_call_id` → [[Reference/Database/Tables/model_call_receipts|`model_call_receipts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_model_calls_owner` on `owner_kind`, `owner_id`, `started_at`.
- `sqlite_autoindex_model_call_receipts_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/substrate/data_quality.py`

### Direct SQL writers

- `src/learnloop/db/stores/model_calls.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_ingest_ownership.py`
- `tests/test_ingestion_checkpoints.py`

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
CREATE TABLE model_call_receipts (
  id TEXT PRIMARY KEY,
  parent_call_id TEXT REFERENCES model_call_receipts(id),
  owner_kind TEXT NOT NULL,
  owner_id TEXT NOT NULL,
  purpose TEXT NOT NULL,
  provider TEXT,
  model TEXT,
  prompt_hash TEXT,
  schema_hash TEXT,
  input_text TEXT,
  schema_json TEXT,
  output_text TEXT,
  status TEXT NOT NULL CHECK(status IN ('started','completed','failed','interrupted','truncated')),
  started_at TEXT NOT NULL,
  finished_at TEXT,
  input_tokens INTEGER,
  output_tokens INTEGER,
  cached_input_tokens INTEGER,
  reasoning_tokens INTEGER,
  cost REAL,
  provider_response_id TEXT,
  finish_reason TEXT,
  error_type TEXT,
  output_budget_tokens INTEGER,
  collection_version TEXT NOT NULL DEFAULT 'learnloop-events-v1'
, endpoint TEXT, resolved_model TEXT, cache_write_tokens INTEGER, usage_json TEXT);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
