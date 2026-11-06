---
title: "followup_workflows"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "b1c67e1f52ee99dcfab1eeca5de019d636162201"
source_commit_timestamp: "2026-11-06T11:48:24-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite followup_workflows"
  - "table followup_workflows"
schema_head: 249
table_name: "followup_workflows"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "241_followup_generate_serve.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/241_followup_generate_serve.sql"
  - "src/learnloop/db/stores/followup_serve.py"
  - "src/learnloop/router_objective/decision_state.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `followup_workflows`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives followup workflow a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `source_attempt_id`, `learning_object_id`, `session_id`, making the operational relationship explicit. ^table-purpose

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
| `source_attempt_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `revision_key` | `TEXT` | yes | — | — | Stored value |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `surface` | `TEXT` | yes | — | — | Stored value |
| `origin` | `TEXT` | yes | — | — | Stored value |
| `state` | `TEXT` | yes | — | — | Stored value |
| `settled_reason` | `TEXT` | no | — | — | Stored value |
| `lane` | `TEXT` | no | — | — | Stored value |
| `factor_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `decision_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `chosen_ref` | `TEXT` | no | — | — | Stored value |
| `practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `probe_candidate_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `hypothesis_set_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `probe_episode_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `presentation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `feedback_held` | `INTEGER` | yes | `0` | — | Stored value |
| `feedback_released_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `release_reason` | `TEXT` | no | — | — | Stored value |
| `shown_anyway_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `exposed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `next_requested_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `feedback_debited_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `source_attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `followup_workflows_item` on `practice_item_id`.
- `followup_workflows_session` on `session_id`, `state`.
- `followup_workflows_state` on `state`, `updated_at`.
- `sqlite_autoindex_followup_workflows_2` on `source_attempt_id`, `revision_key` (unique).
- `sqlite_autoindex_followup_workflows_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/followup_serve.py`
- `src/learnloop/router_objective/decision_state.py`

### Direct SQL writers

- `src/learnloop/db/stores/followup_serve.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_followup_codex_review.py`
- `tests/test_followup_fg1c_r1_exposure_independence.py`
- `tests/test_followup_fg1d_probe_shadow.py`
- `tests/test_followup_migration.py`
- `tests/test_followup_workflow.py`
- `tests/test_hypothesis_marks.py`
- `tests/test_ro0_rows9_13_decision_state.py`

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
CREATE TABLE followup_workflows (
  id TEXT PRIMARY KEY,
  source_attempt_id TEXT NOT NULL REFERENCES practice_attempts(id),
  revision_key TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  session_id TEXT,
  surface TEXT NOT NULL,
  origin TEXT NOT NULL CHECK (origin IN ('practice', 'exam', 'block')),
  state TEXT NOT NULL
    CHECK (state IN ('pending', 'ready', 'waiting', 'refused', 'failed', 'skipped', 'settled')),
  settled_reason TEXT,
  lane TEXT CHECK (lane IN ('probe', 'practice') OR lane IS NULL),
  factor_id TEXT,
  decision_id TEXT,
  chosen_ref TEXT,
  practice_item_id TEXT,
  probe_candidate_id TEXT,
  hypothesis_set_id TEXT,
  probe_episode_id TEXT,
  presentation_id TEXT,
  feedback_held INTEGER NOT NULL DEFAULT 0 CHECK (feedback_held IN (0, 1)),
  feedback_released_at TEXT,
  release_reason TEXT,
  shown_anyway_at TEXT,
  exposed_at TEXT,
  next_requested_at TEXT,
  feedback_debited_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (source_attempt_id, revision_key)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
