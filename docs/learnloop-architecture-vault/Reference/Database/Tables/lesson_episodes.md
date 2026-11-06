---
title: "lesson_episodes"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "0394abccde203a1e4bd7d479ffe28c7035d61f2f"
source_commit_timestamp: "2026-11-06T14:55:42-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite lesson_episodes"
  - "table lesson_episodes"
schema_head: 249
table_name: "lesson_episodes"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "247_lesson_episodes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/247_lesson_episodes.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/db/stores/lessons.py"
  - "src/learnloop/evsi_calibration/forecast_report.py"
  - "src/learnloop/params/parameter_registry.py"
  - "src/learnloop/teacher/episodes.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `lesson_episodes`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives lesson episode a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `lesson_id`, `node_id`, `learning_object_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/247_lesson_episodes.sql`.
- **Schema touched by:** `247_lesson_episodes.sql`, `248_teacher_te2_sources.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `lesson_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/lessons\|lessons.id]] | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `opened_by` | `TEXT` | yes | — | — | Stored value |
| `node_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `opened_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `hypothesis_count` | `INTEGER` | no | — | — | Stored value |
| `hypothesis_hash` | `TEXT` | no | — | — | Stored value |
| `hypothesis_payload_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `repair_class` | `TEXT` | no | — | — | Stored value |
| `teacher_p` | `REAL` | no | — | — | Stored value |
| `teacher_forecast_receipt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `predicted_success` | `REAL` | no | — | — | Stored value |
| `predicted_low` | `REAL` | no | — | — | Stored value |
| `predicted_high` | `REAL` | no | — | — | Stored value |
| `predicted_source` | `TEXT` | no | — | — | Stored value |
| `mastery_mean` | `REAL` | no | — | — | Stored value |
| `mastery_variance` | `REAL` | no | — | — | Stored value |
| `open_misconceptions` | `INTEGER` | no | — | — | Stored value |
| `open_hypotheses` | `INTEGER` | no | — | — | Stored value |
| `open_ids_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `origin` | `TEXT` | yes | — | — | Stored value |
| `origin_decision_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `objective_trace_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `generation_job_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `generated_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `gap_job_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_lo_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `experiment_assignment_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `closed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `close_reason` | `TEXT` | no | — | — | Stored value |
| `active_seconds` | `REAL` | no | — | — | Stored value |
| `elapsed_seconds` | `REAL` | no | — | — | Stored value |
| `unreported_seconds` | `REAL` | no | — | — | Stored value |
| `missing_intervals` | `INTEGER` | no | — | — | Stored value |
| `minutes_source` | `TEXT` | no | — | — | Stored value |
| `outcome_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `outcome_correctness` | `REAL` | no | — | — | Stored value |
| `recheck_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `gap_result` | `TEXT` | no | — | — | Stored value |
| `lo_undo_state` | `TEXT` | no | — | — | Stored value |
| `episode_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `refusal_reason` | `TEXT` | no | — | — | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `lesson_id` → [[Reference/Database/Tables/lessons|`lessons.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_lesson_episodes_lo` on `learning_object_id`, `opened_at`.
- `idx_lesson_episodes_lesson` on `lesson_id`, `opened_at`.
- `sqlite_autoindex_lesson_episodes_2` on `opened_by` (unique).
- `sqlite_autoindex_lesson_episodes_1` on `id` (unique).

Database triggers:

- `lesson_episodes_close_once` — schema-enforced lifecycle or immutability constraint.
- `lesson_episodes_no_delete` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/lessons.py`
- `src/learnloop/evsi_calibration/forecast_report.py`
- `src/learnloop/teacher/service.py`

### Direct SQL writers

- `src/learnloop/db/stores/lessons.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_teacher_te2_lessons.py`
- `tests/test_teacher_te2_migration.py`
- `tests/test_teacher_te2_probes.py`
- `tests/test_teacher_te2log_activity.py`
- `tests/test_teacher_te2log_episodes.py`
- `tests/test_teacher_te2log_migration.py`
- `tests/test_teacher_te2log_receipt.py`

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
CREATE TABLE lesson_episodes (
  id TEXT PRIMARY KEY,
  lesson_id TEXT NOT NULL REFERENCES lessons(id),
  kind TEXT NOT NULL CHECK (kind IN ('probe', 'detour', 'gap', 'goal_lo')),
  -- The lesson_turns row of the action that opened the episode (one episode per
  -- action: a recovered action writes nothing twice).
  opened_by TEXT NOT NULL UNIQUE,
  node_id TEXT,
  learning_object_id TEXT,
  opened_at TEXT NOT NULL,
  -- Hypothesis: for a probe the readings, for a detour the hypothesis, for a gap
  -- the gap in words; the words are in lesson_turn_payloads under
  -- hypothesis_payload_id, the row keeps their count and sha256.
  hypothesis_count INTEGER CHECK (hypothesis_count IS NULL OR hypothesis_count >= 0),
  hypothesis_hash TEXT,
  hypothesis_payload_id TEXT,
  -- Repair class: a detour's repair, or 'unlogged' (a plan that inserted a node
  -- with no note_detour); a gap's kind; null for a probe and a goal LO.
  repair_class TEXT CHECK (repair_class IS NULL OR repair_class IN (
    'repair_in_place', 'insert_foundation', 'reteach', 'unlogged', 'prerequisite', 'misconception')),
  -- Prior belief at the opening: the teacher's p (and its forecast receipt, for
  -- a probe), the brief's predicted success for the node with its interval and
  -- its source, the LO's mastery mean and variance, the open misconceptions and
  -- hypotheses on the LO (counts here, ids in open_ids_json).
  teacher_p REAL CHECK (teacher_p IS NULL OR (teacher_p >= 0.0 AND teacher_p <= 1.0)),
  teacher_forecast_receipt_id TEXT,
  predicted_success REAL CHECK (predicted_success IS NULL OR (predicted_success >= 0.0 AND predicted_success <= 1.0)),
  predicted_low REAL CHECK (predicted_low IS NULL OR (predicted_low >= 0.0 AND predicted_low <= 1.0)),
  predicted_high REAL CHECK (predicted_high IS NULL OR (predicted_high >= 0.0 AND predicted_high <= 1.0)),
  predicted_source TEXT,
  mastery_mean REAL,
  mastery_variance REAL CHECK (mastery_variance IS NULL OR mastery_variance >= 0.0),
  open_misconceptions INTEGER CHECK (open_misconceptions IS NULL OR open_misconceptions >= 0),
  open_hypotheses INTEGER CHECK (open_hypotheses IS NULL OR open_hypotheses >= 0),
  open_ids_json TEXT NOT NULL DEFAULT '{}',
  -- Origin ids: the lesson's origin (learner_pick, or router with the accepted
  -- offer's decision id), that decision's router_objective_traces id, the FG1
  -- generation job and item (a probe), the gap job, the created LO, and every
  -- policy_experiment_assignments id in force for the lesson's day.
  origin TEXT NOT NULL CHECK (origin IN ('learner_pick', 'router')),
  origin_decision_id TEXT,
  objective_trace_id TEXT,
  generation_job_id TEXT,
  generated_item_id TEXT,
  gap_job_id TEXT,
  created_lo_id TEXT,
  experiment_assignment_ids_json TEXT NOT NULL DEFAULT '[]',
  -- Closing (set once): when and why it closed; active and elapsed seconds from
  -- opening to closing, never blended (elapsed is closed_at - opened_at; active
  -- the foreground intervals inside it; unreported the elapsed time no interval
  -- covers; missing the seqs that never arrived); the outcome refs.
  closed_at TEXT,
  close_reason TEXT CHECK (close_reason IS NULL OR close_reason IN (
    'rechecked', 'answered', 'refused', 'retired', 'resolved', 'lesson_closed')),
  active_seconds REAL CHECK (active_seconds IS NULL OR active_seconds >= 0.0),
  elapsed_seconds REAL CHECK (elapsed_seconds IS NULL OR elapsed_seconds >= 0.0),
  unreported_seconds REAL CHECK (unreported_seconds IS NULL OR unreported_seconds >= 0.0),
  missing_intervals INTEGER CHECK (missing_intervals IS NULL OR missing_intervals >= 0),
  minutes_source TEXT CHECK (minutes_source IS NULL OR minutes_source IN ('lesson_activity', 'no_intervals')),
  outcome_attempt_id TEXT,
  outcome_correctness REAL CHECK (outcome_correctness IS NULL OR (outcome_correctness >= 0.0 AND outcome_correctness <= 1.0)),
  recheck_attempt_id TEXT,
  gap_result TEXT,
  lo_undo_state TEXT,
  episode_version TEXT NOT NULL,
  created_at TEXT NOT NULL, refusal_reason TEXT CHECK (refusal_reason IS NULL OR refusal_reason IN (
  'reserved_match', 'protection_unavailable', 'not_admitted', 'generation_failed', 'route_unavailable',
  'lesson_closed', 'switch_off')),
  -- A detour always has its repair; a gap may have its kind; a probe and a goal LO have none.
  CHECK (CASE kind
    WHEN 'detour' THEN repair_class IS NOT NULL
      AND repair_class IN ('repair_in_place', 'insert_foundation', 'reteach', 'unlogged')
    WHEN 'gap' THEN repair_class IS NULL OR repair_class IN ('prerequisite', 'misconception')
    ELSE repair_class IS NULL END),
  CHECK ((closed_at IS NULL) = (close_reason IS NULL))
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
