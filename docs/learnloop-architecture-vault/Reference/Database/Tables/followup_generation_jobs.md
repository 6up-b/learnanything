---
title: "followup_generation_jobs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "0cc1e5ab5436f13e72c0cd2bf84543dccd7ff3f2"
source_commit_timestamp: "2026-11-07T01:07:25-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite followup_generation_jobs"
  - "table followup_generation_jobs"
schema_head: 250
table_name: "followup_generation_jobs"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "241_followup_generate_serve.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/241_followup_generate_serve.sql"
  - "src/learnloop/db/stores/followup_serve.py"
  - "src/learnloop/followup_run/lesson_probe.py"
  - "src/learnloop/followup_serve/queue.py"
  - "src/learnloop_sidecar/post_attempt_worker.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `followup_generation_jobs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Coordinates leased, retryable work for followup generation so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `workflow_id`, `probe_episode_id`, `need_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/241_followup_generate_serve.sql`.
- **Schema touched by:** `241_followup_generate_serve.sql`, `248_teacher_te2_sources.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `dedupe_key` | `TEXT` | yes | — | — | Stored value |
| `workflow_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/followup_workflows\|followup_workflows.id]] | Stored value |
| `probe_episode_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `need_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `state` | `TEXT` | yes | `'queued'` | — | Stored value |
| `attempt_count` | `INTEGER` | yes | `0` | — | Stored value |
| `lease_owner` | `TEXT` | no | — | — | Stored value |
| `lease_expires_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `lease_epoch` | `INTEGER` | yes | `0` | — | Stored value |
| `not_before` | `TEXT` | no | — | — | Stored value |
| `last_error` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `workflow_id` → [[Reference/Database/Tables/followup_workflows|`followup_workflows.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `followup_generation_jobs_order` on `state`, `created_at`, `id`.
- `sqlite_autoindex_followup_generation_jobs_2` on `dedupe_key` (unique).
- `sqlite_autoindex_followup_generation_jobs_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/followup_serve.py`

### Direct SQL writers

- `src/learnloop/db/stores/followup_serve.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_followup_codex_review.py`
- `tests/test_followup_generate_e2e.py`
- `tests/test_followup_migration.py`
- `tests/test_followup_reserved_only.py`
- `tests/test_teacher_exam_question_guard.py`
- `tests/test_teacher_te2_migration.py`
- `tests/test_teacher_te2_probes.py`

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
CREATE TABLE "followup_generation_jobs" (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('workflow', 'entry_episode', 'need', 'lesson')),
  dedupe_key TEXT NOT NULL UNIQUE,
  workflow_id TEXT REFERENCES followup_workflows(id),
  probe_episode_id TEXT,
  need_id TEXT,
  state TEXT NOT NULL DEFAULT 'queued'
    CHECK (state IN ('queued', 'leased', 'done', 'failed', 'skipped')),
  attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  lease_owner TEXT,
  lease_expires_at TEXT,
  lease_epoch INTEGER NOT NULL DEFAULT 0,
  not_before TEXT,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
