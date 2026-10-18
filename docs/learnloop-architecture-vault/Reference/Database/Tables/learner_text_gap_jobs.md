---
title: "learner_text_gap_jobs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "d49d18ffc5b7ac0d4c5d476b70a323629bad9e0d"
source_commit_timestamp: "2026-10-18T04:55:03-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite learner_text_gap_jobs"
  - "table learner_text_gap_jobs"
schema_head: 211
table_name: "learner_text_gap_jobs"
table_role: "workflow"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "182_learner_text_gaps.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/182_learner_text_gaps.sql"
  - "src/learnloop/db/stores/learner_gaps.py"
  - "src/learnloop/reader/reader_report.py"
  - "src/learnloop_sidecar/post_attempt_worker.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `learner_text_gap_jobs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Coordinates leased, retryable work for learner text gap so learner-facing mastery and capability decisions use a reproducible evidence projection. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `source_id`, `source_kind`, `state`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> The durable queue (lease fencing as post_attempt_jobs, 170). A tutor question has no attempt, so this is its own table. payload_json keeps a creation's progress (concept, LO, edge written) so a retry never creates twice.

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/182_learner_text_gaps.sql`.
- **Schema touched by:** `182_learner_text_gaps.sql`, `208_learner_text_source_kinds.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `source_kind` | `TEXT` | yes | — | — | Stored value |
| `source_id` | `TEXT` | yes | — | — | Application-validated soft reference |
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

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `learner_text_gap_jobs_order` on `state`, `created_at`, `id`.
- `sqlite_autoindex_learner_text_gap_jobs_2` on `source_kind`, `source_id` (unique).
- `sqlite_autoindex_learner_text_gap_jobs_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/learner_gaps.py`
- `src/learnloop/reader/reader_report.py`

### Direct SQL writers

- `src/learnloop/db/stores/learner_gaps.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_held_grade_composition.py`
- `tests/test_learner_text_gaps_composition.py`
- `tests/test_learner_text_gaps_rereview.py`
- `tests/test_learner_text_source_widening.py`
- `tests/test_mvp016_upgrade.py`
- `tests/test_reader_active_reading.py`
- `tests/test_reader_formative_texts.py`
- `tests/test_reader_rw1b_review.py`

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
CREATE TABLE "learner_text_gap_jobs" (
  id TEXT PRIMARY KEY,
  source_kind TEXT NOT NULL CHECK (source_kind IN (
    'tutor_question', 'stuck_answer', 'diagnosis', 'workbench_text', 'reader_formative'
  )),
  source_id TEXT NOT NULL,
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
  UNIQUE (source_kind, source_id)
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
