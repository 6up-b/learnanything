---
title: "post_attempt_jobs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "fcf7dc95d383cc97b89741893bc312737dbde569"
source_commit_timestamp: "2026-10-14T10:48:23-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite post_attempt_jobs"
  - "table post_attempt_jobs"
schema_head: 202
table_name: "post_attempt_jobs"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "170_blind_grading_diagnosis_split.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/170_blind_grading_diagnosis_split.sql"
  - "src/learnloop/cli/diagnose.py"
  - "src/learnloop/db/stores/diagnoses.py"
  - "src/learnloop/diagnosis/split/jobs.py"
  - "src/learnloop/ops/doctor.py"
  - "src/learnloop/placement/state.py"
  - "src/learnloop_sidecar/context.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `post_attempt_jobs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Coordinates leased, retryable work for post attempt so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `attempt_id`, `kind`, `job_key`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> The durable post-attempt queue (§11). Lease fencing follows reader_background_requests (migration 093): lease_epoch moves on every claim, and a guarded write from a worker whose lease was re-claimed applies to zero rows.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/170_blind_grading_diagnosis_split.sql`.
- **Schema touched by:** `170_blind_grading_diagnosis_split.sql`, `182_learner_text_gaps.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `job_key` | `TEXT` | yes | — | — | Stored value |
| `attempt_completed_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `state` | `TEXT` | yes | `'queued'` | — | Stored value |
| `attempt_count` | `INTEGER` | yes | `0` | — | Stored value |
| `lease_owner` | `TEXT` | no | — | — | Stored value |
| `lease_expires_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `lease_epoch` | `INTEGER` | yes | `0` | — | Stored value |
| `not_before` | `TEXT` | no | — | — | Stored value |
| `last_error` | `TEXT` | no | — | — | Stored value |
| `payload_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `post_attempt_jobs_order` on `kind`, `state`, `attempt_completed_at`, `attempt_id`.
- `sqlite_autoindex_post_attempt_jobs_2` on `kind`, `job_key` (unique).
- `sqlite_autoindex_post_attempt_jobs_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/diagnoses.py`
- `src/learnloop/placement/state.py`

### Direct SQL writers

- `src/learnloop/db/stores/diagnoses.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_diagnosis_embeddings.py`
- `tests/test_diagnosis_pipeline.py`
- `tests/test_diagnosis_reports.py`
- `tests/test_field_split_outcomes.py`
- `tests/test_held_grade_composition.py`
- `tests/test_placement_diagnosis_decides.py`
- `tests/test_placement_split_grades.py`
- `tests/test_post_attempt_worker.py`
- `tests/test_reader_guidance.py`

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
CREATE TABLE post_attempt_jobs (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id),
  kind TEXT NOT NULL CHECK (kind IN ('diagnose', 'embed')),
  job_key TEXT NOT NULL,
  attempt_completed_at TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'queued'
    CHECK (state IN ('queued', 'leased', 'done', 'failed', 'skipped')),
  attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  lease_owner TEXT,
  lease_expires_at TEXT,
  lease_epoch INTEGER NOT NULL DEFAULT 0,
  not_before TEXT,
  last_error TEXT,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (kind, job_key)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
