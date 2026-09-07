---
title: "activity_observations"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite activity_observations"
  - "table activity_observations"
schema_head: 157
table_name: "activity_observations"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "activity-substrate"
introduced_in: "065_activity_lineage_substrate.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/065_activity_lineage_substrate.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/db/stores/observation_ledger.py"
  - "src/learnloop/substrate/compat/activity_backfill.py"
  - "src/learnloop/substrate/compat/card_outcome_replay.py"
  - "src/learnloop/attempts/calibration_streams.py"
  - "src/learnloop/attempts/grade_resolution.py"
  - "src/learnloop/cli/grading.py"
  - "src/learnloop/goals/goal_contracts.py"
  - "src/learnloop/substrate/activities.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `activity_observations`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records observations used to evaluate activity so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It supplies replay-stable input rather than a disposable cache. Rows bind `administration_id`, `surface_id`, `attempt_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> ---------------------------------------------------------------------------- Observation: joins one response/attempt to its raw grade events, active interpretation, and purpose-specific evidence eligibility (§3.5). P0.1 creates the row + linkage columns; the grading package fills interpretation. ----------------------------------------------------------------------------

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/065_activity_lineage_substrate.sql`.
- **Schema touched by:** `065_activity_lineage_substrate.sql`, `066_grader_channel.sql`, `070_p0_measurement_hardening.sql`, `071_probe_robust_cutover.sql`, `156_projection_ledger_indexes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `administration_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_administrations\|activity_administrations.id]] | Stored value |
| `surface_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_surfaces\|activity_surfaces.id]] | Stored value |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `response_ref` | `TEXT` | no | — | — | Stored value |
| `active_interpretation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `evidence_eligibility` | `TEXT` | no | — | — | Stored value |
| `eligibility_reason` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `surface_id` → [[Reference/Database/Tables/activity_surfaces|`activity_surfaces.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `administration_id` → [[Reference/Database/Tables/activity_administrations|`activity_administrations.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_activity_observations_attempt` on `attempt_id`, `created_at`, `id`.
- `idx_activity_observations_active_interp` on `active_interpretation_id`.
- `idx_activity_observations_admin` on `administration_id`.
- `sqlite_autoindex_activity_observations_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.active_interpretation_for_observation()`
- `Repository.insert_activity_observation()`
- `Repository.observation_attempt_id()`
- `Repository.observation_by_attempt()`
- `Repository.observations_for_administration()`
- `Repository.pending_grade_reviews()`
- `Repository.set_active_interpretation()`
- `Repository.write_administration_lineage_atomic()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop/db/stores/observation_ledger.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/calibration_streams.py`
- `src/learnloop/attempts/grade_resolution.py`
- `src/learnloop/cli/grading.py`
- `src/learnloop/goals/goal_contracts.py`
- `src/learnloop/substrate/activities.py`
- `src/learnloop/substrate/compat/activity_backfill.py`
- `src/learnloop/substrate/compat/card_outcome_replay.py`
- `src/learnloop/substrate/compat/substrate_cutover.py`
- `src/learnloop/substrate/rebuild_orchestrator.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_activity_backfill.py`
- `tests/test_activity_substrate.py`
- `tests/test_reader_dialogue.py`
- `tests/test_rebuild_orchestrator.py`
- `tests/test_effective_observation.py`
- `tests/test_event_sufficiency.py`
- `tests/test_exam_session.py`
- `tests/test_goal_contracts.py`
- `tests/test_golden_path_assessment.py`
- `tests/test_grade_resolution_pipeline.py`
- `tests/test_grading_cli.py`
- `tests/test_journey6.py`
- `tests/test_p0_projection_cutover.py`
- `tests/test_probe_robust_cutover.py`
- `tests/test_substrate_cutover.py`
- `tests/test_unresolved_cause_gate.py`

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
CREATE TABLE "activity_observations" (
  id TEXT PRIMARY KEY,
  administration_id TEXT NOT NULL
    REFERENCES activity_administrations(id),
  surface_id TEXT NOT NULL REFERENCES activity_surfaces(id),
  attempt_id TEXT,
  response_ref TEXT,
  active_interpretation_id TEXT,
  evidence_eligibility TEXT
    CHECK (evidence_eligibility IS NULL OR evidence_eligibility IN
      ('terminal', 'diagnostic', 'practice', 'ineligible')),
  eligibility_reason TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
