---
title: "rung_variant_requests"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite rung_variant_requests"
  - "table rung_variant_requests"
schema_head: 157
table_name: "rung_variant_requests"
table_role: "workflow"
functionality_status: "active"
domain_family: "tutor-and-remediation"
introduced_in: "108_rung_variant_requests.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/108_rung_variant_requests.sql"
  - "src/learnloop/content/pipeline/jobs.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/db/stores/ingest_queue.py"
  - "src/learnloop/content/authoring/rung_variants.py"
  - "src/learnloop/content/pipeline/runner.py"
  - "src/learnloop/scheduling/scheduler.py"
  - "src/learnloop_sidecar/handlers/item_authoring.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/tutor-and-remediation"
---

# `rung_variant_requests`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Queues a durable, retryable request for rung variant so tutor and repair work can be resumed, reviewed, and connected to subsequent evidence. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `source_practice_item_id`, `learning_object_id`, `attempt_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Learner-initiated re-runging (easier/harder variants). One row per request: the durable lock (caps), the audit trail (target rung snapshot, evidence ids), and the linkage to the minted variant. The evidence writes (self_report attempt + learner claim) happen synchronously at request time and are NEVER rolled back on generation failure — the request itself was real evidence.

It belongs to the **tutor and remediation** navigation family. The family context lives in [[Database Catalog#Tutor And Remediation]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/108_rung_variant_requests.sql`.
- **Schema touched by:** `108_rung_variant_requests.sql`, `115_causal_attribution_p0.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `source_practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `direction` | `TEXT` | yes | — | — | Stored value |
| `source_waypoint_slug` | `TEXT` | yes | — | — | Stored value |
| `target_waypoint_slug` | `TEXT` | yes | — | — | Stored value |
| `target_rung_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | — | — | Stored value |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `learner_claim_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `batch_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `patch_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `failure_reason` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `variant_kind` | `TEXT` | no | — | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_rvr_created_item` on `created_practice_item_id`.
- `idx_rvr_source` on `source_practice_item_id`, `status`.
- `sqlite_autoindex_rung_variant_requests_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.insert_rung_variant_request()`
- `Repository.pending_rung_variant_requests()`
- `Repository.requested_practice_item_ids()`
- `Repository.retry_failed_rung_variant_request()`
- `Repository.rung_variant_request()`
- `Repository.rung_variant_requests()`
- `Repository.update_rung_variant_request()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop/db/stores/ingest_queue.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/authoring/rung_variants.py`
- `src/learnloop/content/pipeline/jobs.py`
- `src/learnloop/content/pipeline/runner.py`
- `src/learnloop/scheduling/scheduler.py`
- `src/learnloop_sidecar/handlers/item_authoring.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_ingest_jobs.py`
- `tests/test_ingest_runner.py`
- `tests/test_question_promotions.py`
- `tests/test_tutor_promotion_service.py`

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
CREATE TABLE rung_variant_requests (
  id TEXT PRIMARY KEY,
  source_practice_item_id TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  direction TEXT NOT NULL CHECK (direction IN ('easier', 'harder')),
  source_waypoint_slug TEXT NOT NULL,
  target_waypoint_slug TEXT NOT NULL,
  -- RungTarget.as_dict() snapshot at request time (audit + job rebuild).
  target_rung_json TEXT NOT NULL,
  status TEXT NOT NULL CHECK (
    status IN ('pending', 'generating', 'applied', 'review_required', 'failed')
  ),
  attempt_id TEXT,
  learner_claim_id TEXT,
  batch_id TEXT,
  patch_id TEXT,
  created_practice_item_id TEXT,
  failure_reason TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
, variant_kind TEXT
  CHECK (variant_kind IS NULL OR variant_kind IN ('easier', 'harder', 'rung_shift')));
```

## Related notes

- [[Database Catalog#Tutor And Remediation|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
