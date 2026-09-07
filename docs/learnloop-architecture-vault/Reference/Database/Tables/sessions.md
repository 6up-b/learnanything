---
title: "sessions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite sessions"
  - "table sessions"
schema_head: 157
table_name: "sessions"
table_role: "workflow"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/config/template.py"
  - "src/learnloop/curriculum/ai_contracts.py"
  - "src/learnloop/curriculum/depth_edge_authoring.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/calibration_sessions.py"
  - "src/learnloop/diagnosis/contrast_pairs.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_migration.py"
  - "src/learnloop/diagnosis/followups.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `sessions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Tracks learning-session lifecycle state. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `started_at`, `energy`, `sleep_quality`, making the operational relationship explicit. ^table-purpose

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`, `029_probe_selection_and_calibration.sql`, `143_instrument_classes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `started_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `ended_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `energy` | `TEXT` | no | — | — | Stored value |
| `sleep_quality` | `REAL` | no | — | — | Stored value |
| `available_minutes` | `INTEGER` | no | — | — | Stored value |
| `notes_md_path` | `TEXT` | no | — | — | Stored value |
| `updated_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_sessions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.create_session()`
- `Repository.end_open_sessions_except()`
- `Repository.end_session()`
- `Repository.fetch_session()`
- `Repository.find_record()`
- `Repository.most_recent_ended_at()`
- `Repository.most_recent_open_session()`
- `Repository.review_session_rows()`
- `Repository.session_day_streak()`
- `Repository.session_learner_answers()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/diagnosis/followups.py`
- `src/learnloop/learner/learner_review_feed.py`
- `src/learnloop/learner/session_learning_diff.py`
- `src/learnloop/scheduling/reentry_adapter.py`
- `src/learnloop/scheduling/reentry_summary.py`
- `src/learnloop_sidecar/context.py`
- `src/learnloop_sidecar/handlers/inspector.py`
- `src/learnloop_sidecar/handlers/practice.py`
- `src/learnloop_sidecar/handlers/sessions.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_calibration_sessions.py`
- `tests/test_contrast_pairs.py`
- `tests/test_init.py`
- `tests/test_probe_orchestration_remainder.py`
- `tests/test_session_attempt_attribution.py`
- `tests/test_sidecar_remediation_surfaces.py`
- `tests/test_sidecar_teach_back.py`
- `tests/test_agent_runs.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_item_authoring.py`
- `tests/test_learner_review_system_entries.py`
- `tests/test_repositories.py`
- `tests/test_show.py`
- `tests/test_sidecar_contract.py`
- `tests/test_sidecar_item_authoring.py`
- `tests/test_sidecar_trace_and_clarification.py`
- `tests/test_source_ingestion.py`

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
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  energy TEXT,
  sleep_quality REAL CHECK (sleep_quality IS NULL OR (sleep_quality >= 0.0 AND sleep_quality <= 1.0)),
  available_minutes INTEGER CHECK (available_minutes IS NULL OR available_minutes >= 0),
  notes_md_path TEXT,
  updated_at TEXT
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
