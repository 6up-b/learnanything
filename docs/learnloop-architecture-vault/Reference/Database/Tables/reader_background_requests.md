---
title: "reader_background_requests"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite reader_background_requests"
  - "table reader_background_requests"
schema_head: 156
table_name: "reader_background_requests"
table_role: "workflow"
functionality_status: "active"
domain_family: "reader"
introduced_in: "093_reader_background_requests.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/093_reader_background_requests.sql"
  - "src/learnloop/content/pipeline/jobs.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop_sidecar/handlers/reader.py"
  - "src/learnloop/content/sources/source_deletion.py"
  - "src/learnloop/reader/reader_requests.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/reader"
---

# `reader_background_requests`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Queues a durable, retryable request for reader background so reader interactions remain anchored to durable source content as extraction and rendering evolve. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `source_id`, `revision_id`, `extraction_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **reader** navigation family. The family context lives in [[Database Catalog#Reader]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/093_reader_background_requests.sql`.
- **Schema touched by:** `093_reader_background_requests.sql`, `131_agent_run_tokens.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `request_key` | `TEXT` | yes | — | — | Stored value |
| `source_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `revision_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `extraction_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `span_id` | `TEXT` | yes | `''` | — | Application-validated soft reference |
| `window_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `preset` | `TEXT` | yes | — | — | Stored value |
| `action` | `TEXT` | yes | `''` | — | Stored value |
| `inventory_profile` | `TEXT` | yes | `'semantic'` | — | Stored value |
| `inventory_schema_version` | `TEXT` | yes | `''` | — | Stored value |
| `synthesis_schema_version` | `TEXT` | yes | `''` | — | Stored value |
| `prompt_version` | `TEXT` | yes | `''` | — | Stored value |
| `provider` | `TEXT` | yes | `''` | — | Stored value |
| `model` | `TEXT` | yes | `''` | — | Stored value |
| `config_hash` | `TEXT` | yes | `''` | — | Stored value |
| `status` | `TEXT` | yes | `'queued'` | — | Stored value |
| `priority_band` | `INTEGER` | yes | `0` | — | Stored value |
| `est_input_tokens` | `INTEGER` | yes | `0` | — | Stored value |
| `est_output_tokens` | `INTEGER` | yes | `0` | — | Stored value |
| `actual_input_tokens` | `INTEGER` | yes | `0` | — | Stored value |
| `actual_output_tokens` | `INTEGER` | yes | `0` | — | Stored value |
| `token_cap` | `INTEGER` | yes | `0` | — | Stored value |
| `cache_hit` | `INTEGER` | yes | `0` | — | Stored value |
| `reason` | `TEXT` | no | — | — | Stored value |
| `result_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `annotation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `commitment_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `client_idempotency_key` | `TEXT` | no | — | — | Stored value |
| `lease_owner` | `TEXT` | no | — | — | Stored value |
| `lease_expires_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `lease_epoch` | `INTEGER` | yes | `0` | — | Stored value |
| `attempt_count` | `INTEGER` | yes | `0` | — | Stored value |
| `cancel_requested` | `INTEGER` | yes | `0` | — | Stored value |
| `error_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `completed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_reader_bg_requests_revision` on `revision_id`.
- `idx_reader_bg_requests_source` on `source_id`.
- `idx_reader_bg_requests_status` on `status`, `priority_band`, `created_at`.
- `sqlite_autoindex_reader_background_requests_2` on `request_key` (unique).
- `sqlite_autoindex_reader_background_requests_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.cancel_reader_request()`
- `Repository.claim_next_reader_request()`
- `Repository.delete_source_artifact()`
- `Repository.enqueue_reader_request()`
- `Repository.get_reader_request()`
- `Repository.has_queued_reader_requests()`
- `Repository.reader_request_by_key()`
- `Repository.reader_requests_for_source()`
- `Repository.resolve_reader_request()`
- `Repository.retry_reader_request()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/pipeline/jobs.py`
- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/reader/reader_requests.py`
- `src/learnloop_sidecar/handlers/reader.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_ingest_jobs.py`
- `tests/test_p3_journeys.py`
- `tests/test_reader_capture.py`
- `tests/test_reader_requests.py`

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
CREATE TABLE reader_background_requests (
  id TEXT PRIMARY KEY,
  request_key TEXT NOT NULL,
  source_id TEXT NOT NULL,
  revision_id TEXT NOT NULL,
  extraction_id TEXT NOT NULL,
  span_id TEXT NOT NULL DEFAULT '',
  window_json TEXT NOT NULL DEFAULT '{}',
  preset TEXT NOT NULL,
  action TEXT NOT NULL DEFAULT '',
  inventory_profile TEXT NOT NULL DEFAULT 'semantic',
  inventory_schema_version TEXT NOT NULL DEFAULT '',
  synthesis_schema_version TEXT NOT NULL DEFAULT '',
  prompt_version TEXT NOT NULL DEFAULT '',
  provider TEXT NOT NULL DEFAULT '',
  model TEXT NOT NULL DEFAULT '',
  config_hash TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued', 'running', 'complete', 'partial', 'failed', 'cancelled', 'obsolete')),
  priority_band INTEGER NOT NULL DEFAULT 0,
  est_input_tokens INTEGER NOT NULL DEFAULT 0,
  est_output_tokens INTEGER NOT NULL DEFAULT 0,
  actual_input_tokens INTEGER NOT NULL DEFAULT 0,
  actual_output_tokens INTEGER NOT NULL DEFAULT 0,
  token_cap INTEGER NOT NULL DEFAULT 0,
  cache_hit INTEGER NOT NULL DEFAULT 0,
  reason TEXT,
  result_json TEXT NOT NULL DEFAULT '{}',
  annotation_id TEXT,
  commitment_id TEXT,
  client_idempotency_key TEXT,
  -- Fenced lease (migration 080 precedent):
  lease_owner TEXT,
  lease_expires_at TEXT,
  lease_epoch INTEGER NOT NULL DEFAULT 0,
  attempt_count INTEGER NOT NULL DEFAULT 0,
  cancel_requested INTEGER NOT NULL DEFAULT 0,
  error_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  completed_at TEXT,
  UNIQUE(request_key)
);
```

## Related notes

- [[Database Catalog#Reader|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
