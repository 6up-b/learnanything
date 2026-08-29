---
title: "calibration_stream_samples"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite calibration_stream_samples"
  - "table calibration_stream_samples"
schema_head: 156
table_name: "calibration_stream_samples"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "066_grader_channel.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/066_grader_channel.sql"
  - "src/learnloop/attempts/calibration_streams.py"
  - "src/learnloop/cli/calibration.py"
  - "src/learnloop/db/repositories.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `calibration_stream_samples`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records sampled observations and their inclusion context for calibration stream so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `observation_id`, `administration_id`, `raw_grade_event_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> ---------------------------------------------------------------------------- Calibration stream sample log (§4.7). Records the inclusion probability under which each attempt entered a stream, so IPW recovers unbiased confusion estimates and the bootstrap composes with the ongoing stream. Error-intake taps land here tagged stream='error_intake' (MNAR; never a denominator). ----------------------------------------------------------------------------

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/066_grader_channel.sql`.
- **Schema touched by:** `066_grader_channel.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `observation_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_observations\|activity_observations.id]] | Stored value |
| `administration_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_administrations\|activity_administrations.id]] | Stored value |
| `raw_grade_event_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/raw_grade_events\|raw_grade_events.id]] | Stored value |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `stream` | `TEXT` | yes | — | — | Stored value |
| `stratum_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `inclusion_probability` | `REAL` | yes | — | — | Stored value |
| `sampling_frame_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `selected` | `INTEGER` | yes | `1` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `raw_grade_event_id` → [[Reference/Database/Tables/raw_grade_events|`raw_grade_events.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `administration_id` → [[Reference/Database/Tables/activity_administrations|`activity_administrations.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `observation_id` → [[Reference/Database/Tables/activity_observations|`activity_observations.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_css_observation` on `observation_id`.
- `idx_css_frame` on `sampling_frame_id`.
- `idx_css_stream` on `stream`.
- `sqlite_autoindex_calibration_stream_samples_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.calibration_stream_samples()`
- `Repository.insert_calibration_stream_sample()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/calibration_streams.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_grade_resolution_pipeline.py`

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
CREATE TABLE calibration_stream_samples (
  id TEXT PRIMARY KEY,
  observation_id TEXT REFERENCES activity_observations(id),
  administration_id TEXT REFERENCES activity_administrations(id),
  raw_grade_event_id TEXT REFERENCES raw_grade_events(id),
  attempt_id TEXT,
  stream TEXT NOT NULL CHECK (stream IN ('error_intake','calibration','adjudicated_anchor')),
  stratum_json TEXT NOT NULL,
  inclusion_probability REAL NOT NULL CHECK (inclusion_probability > 0),
  sampling_frame_id TEXT,
  selected INTEGER NOT NULL DEFAULT 1 CHECK (selected IN (0,1)),
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
