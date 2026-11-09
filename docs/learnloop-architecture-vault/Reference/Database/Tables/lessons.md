---
title: "lessons"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "53be1788a536ed0c52c215db58e75dc8c80f34d3"
source_commit_timestamp: "2026-11-09T09:10:53-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite lessons"
  - "table lessons"
schema_head: 251
table_name: "lessons"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "234_teacher_lessons.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/234_teacher_lessons.sql"
  - "src/learnloop/adaptive_difficulty/arms.py"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/dose_report.py"
  - "src/learnloop/adaptive_difficulty/history_card.py"
  - "src/learnloop/adaptive_difficulty/lessons.py"
  - "src/learnloop/adaptive_difficulty/material_view.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/adaptive_difficulty/readiness.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `lessons`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives lesson a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `doctrine_version`, `brief_version`, `algorithm_version`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/234_teacher_lessons.sql`.
- **Schema touched by:** `234_teacher_lessons.sql`, `236_router_lesson_suggestions.sql`, `247_lesson_episodes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `driver` | `TEXT` | yes | — | — | Stored value |
| `origin` | `TEXT` | yes | — | — | Stored value |
| `origin_ref` | `TEXT` | no | — | — | Stored value |
| `entry` | `TEXT` | yes | — | — | Stored value |
| `goal_text` | `TEXT` | yes | — | — | Stored value |
| `goal_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `learning_object_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `doctrine_version` | `TEXT` | yes | — | — | Stored value |
| `brief_version` | `TEXT` | yes | — | — | Stored value |
| `route` | `TEXT` | no | — | — | Stored value |
| `model` | `TEXT` | no | — | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `opened_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `closed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `close_reason` | `TEXT` | no | — | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_lessons_opened` on `opened_at`.
- `sqlite_autoindex_lessons_1` on `id` (unique).

Database triggers:

- `lessons_close_once` — schema-enforced lifecycle or immutability constraint.
- `lessons_no_delete` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/cli/router.py`
- `src/learnloop/daily_plan/lesson_offer.py`
- `src/learnloop/db/stores/lessons.py`
- `src/learnloop/db/stores/router_suggestions.py`
- `src/learnloop/evsi_calibration/forecast_report.py`
- `src/learnloop/figures/prefetch.py`
- `src/learnloop/router_objective/forecast_resolve.py`
- `src/learnloop/router_objective/offer_report.py`
- `src/learnloop/router_objective/preference_report.py`
- `src/learnloop/teacher/report.py`
- `src/learnloop/teacher/service.py`

### Direct SQL writers

- `src/learnloop/db/stores/lessons.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/conftest.py`
- `tests/test_architecture.py`
- `tests/test_figures_prefetch_review_fixes.py`
- `tests/test_followups_batch5_lesson.py`
- `tests/test_followups_batch5_recap_dependencies.py`
- `tests/test_followups_batch6_review_fixes.py`
- `tests/test_followups_batch6_router_report.py`
- `tests/test_ih2_lessons_compete.py`
- `tests/test_ih3_learner_preferences.py`
- `tests/test_ih7_lesson_sources_follow_diagnosis.py`
- `tests/test_mobile_allowlist.py`
- `tests/test_reader_rw5d_p4b_teacher_visuals.py`
- `tests/test_ro2_ad_raw_document_reads.py`
- `tests/test_te3a_lesson_opportunity.py`
- `tests/test_te3b_binding.py`
- `tests/test_te3b_clock.py`
- `tests/test_te3b_population.py`
- `tests/test_te3b_value.py`
- `tests/test_teacher_te1_lesson.py`
- `tests/test_teacher_te1_migration.py`

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
CREATE TABLE lessons (
  id TEXT PRIMARY KEY,
  driver TEXT NOT NULL CHECK (driver = 'desktop' OR driver LIKE 'chat:%'),
  origin TEXT NOT NULL CHECK (origin IN ('learner_pick', 'router')),
  origin_ref TEXT,
  entry TEXT NOT NULL CHECK (entry IN ('learning_object', 'reader_selection', 'new_topic')),
  goal_text TEXT NOT NULL,
  goal_json TEXT NOT NULL,
  learning_object_ids_json TEXT NOT NULL,
  doctrine_version TEXT NOT NULL,
  brief_version TEXT NOT NULL,
  route TEXT,
  model TEXT,
  algorithm_version TEXT NOT NULL,
  opened_at TEXT NOT NULL,
  closed_at TEXT,
  close_reason TEXT CHECK (close_reason IS NULL OR close_reason IN (
    'goal_reached', 'learner_stop', 'budget', 'plan_unavailable', 'teacher_contract_failure',
    'protection_changed')),
  CHECK ((closed_at IS NULL) = (close_reason IS NULL))
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
