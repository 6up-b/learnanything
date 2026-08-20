---
title: "measurement_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite measurement_events"
  - "table measurement_events"
schema_head: 156
table_name: "measurement_events"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "065_activity_lineage_substrate.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/065_activity_lineage_substrate.sql"
  - "src/learnloop/attempts/grader_calibration.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/attempts/grade_resolution.py"
  - "src/learnloop/substrate/activities.py"
  - "src/learnloop/substrate/compat/substrate_cutover.py"
  - "src/learnloop/substrate/p0_projection.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `measurement_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of measurement so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `administration_id`, `observation_id`, `algorithm_version`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> ---------------------------------------------------------------------------- Measurement events: append-only spine tying a response through the grade resolution pipeline (§4.1). P0.1 lands the table so exposure/observation rows have a stable measurement anchor; the grading package (P0.2) writes raw-grade and interpretation kinds. Generic + append-only for replay reproducibility. ----------------------------------------------------------------------------

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/065_activity_lineage_substrate.sql`.
- **Schema touched by:** `065_activity_lineage_substrate.sql`, `066_grader_channel.sql`, `070_p0_measurement_hardening.sql`, `071_probe_robust_cutover.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `administration_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_administrations\|activity_administrations.id]] | Stored value |
| `observation_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_observations\|activity_observations.id]] | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `payload_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `observation_id` → [[Reference/Database/Tables/activity_observations|`activity_observations.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `administration_id` → [[Reference/Database/Tables/activity_administrations|`activity_administrations.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_measurement_events_observation` on `observation_id`.
- `idx_measurement_events_admin` on `administration_id`, `created_at`.
- `sqlite_autoindex_measurement_events_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.append_measurement_event()`
- `Repository.measurement_events_for_administration()`
- `Repository.open_administration_atomic()`
- `Repository.write_administration_lineage_atomic()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/grade_resolution.py`
- `src/learnloop/substrate/activities.py`
- `src/learnloop/substrate/compat/substrate_cutover.py`
- `src/learnloop/substrate/p0_projection.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_activity_substrate.py`
- `tests/test_p0_projection_cutover.py`
- `tests/test_administration_adapters.py`
- `tests/test_assessment_enforcement.py`
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
CREATE TABLE "measurement_events" (
  id TEXT PRIMARY KEY,
  administration_id TEXT NOT NULL
    REFERENCES activity_administrations(id),
  observation_id TEXT REFERENCES activity_observations(id),
  kind TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  payload_json TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
