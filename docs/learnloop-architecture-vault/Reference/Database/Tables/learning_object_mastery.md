---
title: "learning_object_mastery"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite learning_object_mastery"
  - "table learning_object_mastery"
schema_head: 157
table_name: "learning_object_mastery"
table_role: "derived"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/ops/debug_time.py"
  - "src/learnloop/ops/doctor.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
  - "src/learnloop/substrate/shadow_rebuild.py"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/content/authoring/practice_generation.py"
  - "src/learnloop/content/authoring/rung_variants.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `learning_object_mastery`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Materializes the current per-learning-object mastery posterior for learner-facing decisions. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `learning_object_id`, `algorithm_version`, `logit_mean`, making the operational relationship explicit. ^table-purpose

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`.
- **Rebuild owner:** `learning_state`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `learning_object_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `logit_mean` | `REAL` | yes | `0.0` | — | Stored value |
| `logit_variance` | `REAL` | yes | `1.0` | — | Stored value |
| `evidence_count` | `INTEGER` | yes | `0` | — | Stored value |
| `last_evidence_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_learning_object_mastery_1` on `learning_object_id` (unique).

## Who calls it

### Repository access surface

- `Repository._upsert_mastery_state_record()`
- `Repository.find_record()`
- `Repository.mastery_state()`
- `Repository.mastery_states()`
- `Repository.reset_learning_object_derived_state()`
- `Repository.upsert_mastery_state()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/cli/app.py`
- `src/learnloop/content/authoring/practice_generation.py`
- `src/learnloop/content/authoring/rung_variants.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/calibration_sessions.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/diagnosis/probe_episodes.py`
- `src/learnloop/diagnosis/probe_hypotheses.py`
- `src/learnloop/diagnosis/probes.py`
- `src/learnloop/goals/exam_session.py`
- `src/learnloop/goals/goal_projection.py`
- `src/learnloop/learner/capability_grid.py`
- `src/learnloop/learner/facet_diagnostics.py`
- `src/learnloop/learner/mastery.py`
- `src/learnloop/learner/recall_calibration.py`
- `src/learnloop/ops/doctor.py`
- `src/learnloop/reader/reader_guidance.py`
- `src/learnloop/scheduling/scheduler.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`
- `tests/test_p0_cutover_mvp08.py`
- `tests/test_rebuild_orchestrator.py`
- `tests/test_shadow_rebuild.py`
- `tests/test_table_roles.py`
- `tests/helpers.py`
- `tests/test_agent_runs.py`
- `tests/test_apply_write_ahead.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_attempts.py`
- `tests/test_calibration.py`
- `tests/test_cli_attempt.py`
- `tests/test_cli_generate_practice.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_contract_commissioning.py`
- `tests/test_deferred_regrade.py`
- `tests/test_diagnostic_probe_freshness.py`
- `tests/test_diagnostic_probe_single_use.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_e2e_local.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.
5. Update the single owner in `DERIVED_STATE_REPLAYERS`, then prove same-version rebuild equivalence and shadow isolation.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE TABLE learning_object_mastery (
  learning_object_id TEXT PRIMARY KEY,
  logit_mean REAL NOT NULL DEFAULT 0.0,
  logit_variance REAL NOT NULL DEFAULT 1.0 CHECK (logit_variance >= 0.0),
  evidence_count INTEGER NOT NULL DEFAULT 0 CHECK (evidence_count >= 0),
  last_evidence_at TEXT,
  algorithm_version TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
