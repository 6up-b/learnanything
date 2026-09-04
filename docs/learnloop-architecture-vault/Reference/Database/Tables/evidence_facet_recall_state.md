---
title: "evidence_facet_recall_state"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite evidence_facet_recall_state"
  - "table evidence_facet_recall_state"
schema_head: 157
table_name: "evidence_facet_recall_state"
table_role: "compat"
functionality_status: "legacy-preserved"
domain_family: "learner-state"
introduced_in: "007_recall_coverage_interventions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/007_recall_coverage_interventions.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/learner/facet_state_reader.py"
  - "src/learnloop/ops/doctor.py"
  - "src/learnloop/substrate/shadow_rebuild.py"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/curriculum/curriculum_locks.py"
  - "src/learnloop/learner/recall_coverage.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/compat"
  - "learnloop/status/legacy-preserved"
  - "learnloop/domain/learner-state"
---

# `evidence_facet_recall_state`

> [!warning] Legacy Preserved
> Frozen compatibility state remains readable for older vaults and is not a deletion candidate.

## Why it exists

Preserves the pre-canonical learning-object-scoped facet recall projection for old vaults. It keeps an older vault or replay contract readable while new writes use the refactored path. Rows bind `learning_object_id`, `facet_id`, `practice_item_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Compat]].

## Persistence and lifecycle contract

- **Role:** `compat` — Frozen compatibility state retained for old vaults or an incomplete replacement seam.
- **Functionality status:** `legacy-preserved`.
- **Introduced by:** `migrations/007_recall_coverage_interventions.sql`.
- **Schema touched by:** `007_recall_coverage_interventions.sql`, `037_canonical_facet_state.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `facet_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `recall_alpha` | `REAL` | yes | `1.0` | — | Stored value |
| `recall_beta` | `REAL` | yes | `1.0` | — | Stored value |
| `recall_mean` | `REAL` | yes | — | — | Stored value |
| `recall_variance` | `REAL` | yes | — | — | Stored value |
| `independent_evidence_mass` | `REAL` | yes | `0.0` | — | Stored value |
| `raw_coverage_mass` | `REAL` | yes | `0.0` | — | Stored value |
| `last_attempt_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `last_error_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `consecutive_failures` | `INTEGER` | yes | `0` | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_evidence_facet_recall_item` on `learning_object_id`, `facet_id`, `practice_item_id` (unique).
- `idx_evidence_facet_recall_aggregate` on `learning_object_id`, `facet_id` (unique).
- `sqlite_autoindex_evidence_facet_recall_state_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository._guard_legacy_facet_write()`
- `Repository._upsert_facet_recall_state()`
- `Repository.facet_ids_with_recall_evidence()`
- `Repository.facet_recall_state()`
- `Repository.facet_recall_states()`
- `Repository.merge_facet_recall_aliases()`
- `Repository.reset_learning_object_derived_state()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/curriculum/curriculum_locks.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/learner/facet_state_reader.py`
- `src/learnloop/learner/recall_coverage.py`
- `src/learnloop/ops/doctor.py`
- `src/learnloop/substrate/replay.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_doctor.py`
- `tests/test_km2b_consumer_rekey.py`
- `tests/test_recall_coverage_interventions.py`
- `tests/test_scheduler.py`
- `tests/test_shadow_rebuild.py`
- `tests/test_tutor_promotion_w2.py`
- `tests/test_deferred_regrade.py`
- `tests/test_difficulty_band_guards.py`
- `tests/test_exam_seeding.py`
- `tests/test_goal_projection.py`
- `tests/test_item_parameters.py`
- `tests/test_measurement_state_labels.py`
- `tests/test_replay.py`
- `tests/test_teach_back.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.
5. Compatibility retirement requires production-vault telemetry and an explicit owner decision; code detachment and schema changes are separate gates.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE TABLE evidence_facet_recall_state (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT NOT NULL,
  facet_id TEXT NOT NULL,
  practice_item_id TEXT,
  recall_alpha REAL NOT NULL DEFAULT 1.0,
  recall_beta REAL NOT NULL DEFAULT 1.0,
  recall_mean REAL NOT NULL,
  recall_variance REAL NOT NULL,
  independent_evidence_mass REAL NOT NULL DEFAULT 0.0,
  raw_coverage_mass REAL NOT NULL DEFAULT 0.0,
  last_attempt_at TEXT,
  last_error_at TEXT,
  consecutive_failures INTEGER NOT NULL DEFAULT 0,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Compat|compat policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
