---
title: "grade_interpretations"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite grade_interpretations"
  - "table grade_interpretations"
schema_head: 157
table_name: "grade_interpretations"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "066_grader_channel.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/066_grader_channel.sql"
  - "src/learnloop/attempts/effective_observation.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/db/stores/observation_ledger.py"
  - "src/learnloop/substrate/compat/card_outcome_replay.py"
  - "src/learnloop/attempts/grade_resolution.py"
  - "src/learnloop/cli/grading.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `grade_interpretations`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives grade interpretation a stable database identity so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `raw_grade_event_id`, `observation_id`, `administration_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> ---------------------------------------------------------------------------- Grade interpretations (§3.3). Append-only. The current head per observation is a projection selected by activation/supersession measurement_events. ----------------------------------------------------------------------------

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/066_grader_channel.sql`.
- **Schema touched by:** `066_grader_channel.sql`, `070_p0_measurement_hardening.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `raw_grade_event_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/raw_grade_events\|raw_grade_events.id]] | Stored value |
| `observation_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_observations\|activity_observations.id]] | Stored value |
| `administration_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_administrations\|activity_administrations.id]] | Stored value |
| `calibration_model_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/grader_calibration_models\|grader_calibration_models.id]] | Stored value |
| `calibration_model_hash` | `TEXT` | yes | — | — | Stored value |
| `projection_algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `channel_posterior_snapshot_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `response_posterior_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `criterion_posteriors_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `reference_prior_ids_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `certainty_discount` | `REAL` | yes | — | — | Stored value |
| `credible_interval_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `review_flag` | `INTEGER` | yes | `0` | — | Stored value |
| `influence_flag` | `INTEGER` | yes | `0` | — | Stored value |
| `quarantine_state` | `TEXT` | yes | `'active'` | — | Stored value |
| `fallback_reason` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `shared_certainty_lcb` | `REAL` | no | — | — | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `calibration_model_id` → [[Reference/Database/Tables/grader_calibration_models|`grader_calibration_models.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `administration_id` → [[Reference/Database/Tables/activity_administrations|`activity_administrations.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `observation_id` → [[Reference/Database/Tables/activity_observations|`activity_observations.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `raw_grade_event_id` → [[Reference/Database/Tables/raw_grade_events|`raw_grade_events.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_gi_admin` on `administration_id`.
- `idx_gi_raw` on `raw_grade_event_id`.
- `idx_gi_observation` on `observation_id`.
- `sqlite_autoindex_grade_interpretations_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.active_interpretation_for_observation()`
- `Repository.grade_interpretation()`
- `Repository.grade_interpretations_for_observation()`
- `Repository.insert_grade_interpretation()`
- `Repository.pending_grade_reviews()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop/db/stores/observation_ledger.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/grade_resolution.py`
- `src/learnloop/cli/grading.py`
- `src/learnloop/substrate/compat/card_outcome_replay.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_event_sufficiency.py`
- `tests/test_grade_resolution_pipeline.py`
- `tests/test_observation_ledger_bulk.py`
- `tests/test_effective_observation.py`
- `tests/test_p0_projection_cutover.py`
- `tests/test_probe_robust_cutover.py`

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
CREATE TABLE grade_interpretations (
  id TEXT PRIMARY KEY,
  raw_grade_event_id TEXT NOT NULL REFERENCES raw_grade_events(id),
  observation_id TEXT REFERENCES activity_observations(id),
  administration_id TEXT NOT NULL REFERENCES activity_administrations(id),
  calibration_model_id TEXT NOT NULL REFERENCES grader_calibration_models(id),
  calibration_model_hash TEXT NOT NULL,
  projection_algorithm_version TEXT NOT NULL,
  channel_posterior_snapshot_id TEXT,
  response_posterior_json TEXT NOT NULL,   -- {Z: P(Z|E,context)}
  criterion_posteriors_json TEXT,
  reference_prior_ids_json TEXT,
  certainty_discount REAL NOT NULL,
  credible_interval_json TEXT,
  review_flag INTEGER NOT NULL DEFAULT 0 CHECK (review_flag IN (0,1)),
  influence_flag INTEGER NOT NULL DEFAULT 0 CHECK (influence_flag IN (0,1)),
  quarantine_state TEXT NOT NULL DEFAULT 'active'
    CHECK (quarantine_state IN ('active','quarantined')),
  fallback_reason TEXT,
  created_at TEXT NOT NULL
, shared_certainty_lcb REAL);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
