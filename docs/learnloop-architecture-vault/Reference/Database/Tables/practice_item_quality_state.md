---
title: "practice_item_quality_state"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite practice_item_quality_state"
  - "table practice_item_quality_state"
schema_head: 157
table_name: "practice_item_quality_state"
table_role: "derived"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "007_recall_coverage_interventions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/007_recall_coverage_interventions.sql"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/followups.py"
  - "src/learnloop/goals/exam_session.py"
  - "src/learnloop/learner/recall_coverage.py"
  - "src/learnloop/ops/doctor.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `practice_item_quality_state`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Materializes suspicion and quality state inferred from the attempt history. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `practice_item_id`, `algorithm_version`, `bad_item_suspicion`, making the operational relationship explicit. ^table-purpose

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/007_recall_coverage_interventions.sql`.
- **Schema touched by:** `007_recall_coverage_interventions.sql`.
- **Rebuild owner:** `learning_state`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `practice_item_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `bad_item_suspicion` | `REAL` | yes | `0.0` | — | Stored value |
| `evidence_count` | `INTEGER` | yes | `0` | — | Stored value |
| `suspicion_reasons_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `last_flagged_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_practice_item_quality_state_1` on `practice_item_id` (unique).

## Who calls it

### Repository access surface

- `Repository._upsert_practice_item_quality_state()`
- `Repository.practice_item_quality_state()`
- `Repository.practice_item_quality_states()`
- `Repository.reset_learning_object_derived_state()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/followups.py`
- `src/learnloop/goals/exam_session.py`
- `src/learnloop/learner/recall_coverage.py`
- `src/learnloop/ops/doctor.py`
- `src/learnloop/scheduling/scheduler.py`
- `src/learnloop/substrate/replay.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_doctor.py`
- `tests/test_rebuild_orchestrator.py`
- `tests/test_recall_coverage_interventions.py`
- `tests/test_replay.py`
- `tests/test_scheduler.py`
- `tests/test_item_parameters.py`

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
CREATE TABLE practice_item_quality_state (
  practice_item_id TEXT PRIMARY KEY,
  bad_item_suspicion REAL NOT NULL DEFAULT 0.0,
  evidence_count INTEGER NOT NULL DEFAULT 0,
  suspicion_reasons_json TEXT,
  last_flagged_at TEXT,
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
