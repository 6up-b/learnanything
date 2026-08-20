---
title: "activity_administrations"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite activity_administrations"
  - "table activity_administrations"
schema_head: 156
table_name: "activity_administrations"
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
  - "src/learnloop/substrate/compat/card_outcome_replay.py"
  - "src/learnloop/cli/grading.py"
  - "src/learnloop/goals/goal_contracts.py"
  - "src/learnloop/reader/reader_dialogue.py"
  - "src/learnloop/substrate/activities.py"
  - "src/learnloop/substrate/administration_adapters.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `activity_administrations`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives activity administration a stable database identity so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It supplies replay-stable input rather than a disposable cache. Rows bind `surface_id`, `card_version_id`, `family_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> ---------------------------------------------------------------------------- Administration: fully resolved card+surface+context+policy snapshot with all pins. administration_snapshot_hash covers resolved card + surface + target + context + all decision/model versions (§3.5). One administration per resolved presentation; created atomically at render (§4.5). Decision/model pins are nullable now (later packages fill them); this table stores IDS + effective-value hash, never a config copy (§6 registry rule). reservation_id is bare TEXT to break the reservation<->administration circular DDL dependency (design §6). ----------------------------------------------------------------------------

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/065_activity_lineage_substrate.sql`.
- **Schema touched by:** `065_activity_lineage_substrate.sql`, `066_grader_channel.sql`, `070_p0_measurement_hardening.sql`, `076_administration_context.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `surface_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_surfaces\|activity_surfaces.id]] | Stored value |
| `card_version_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_card_versions\|activity_card_versions.id]] | Stored value |
| `family_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_families\|activity_families.id]] | Stored value |
| `purpose` | `TEXT` | yes | — | — | Stored value |
| `administration_snapshot_hash` | `TEXT` | yes | — | — | Stored value |
| `snapshot_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `target_contract_version_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `target_support_hash` | `TEXT` | no | — | — | Stored value |
| `grader_model_version_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `selection_policy_version_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `decision_params_hash` | `TEXT` | no | — | — | Stored value |
| `assistance_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `feedback_condition` | `TEXT` | no | — | — | Stored value |
| `eligibility_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `reservation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `legacy_backfilled` | `INTEGER` | yes | `0` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `reading_phase` | `TEXT` | no | — | — | Stored value |
| `admin_context_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

Declared SQLite foreign keys:

- `family_id` → [[Reference/Database/Tables/activity_families|`activity_families.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `card_version_id` → [[Reference/Database/Tables/activity_card_versions|`activity_card_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `surface_id` → [[Reference/Database/Tables/activity_surfaces|`activity_surfaces.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_activity_administrations_target` on `target_contract_version_id`.
- `idx_activity_administrations_snapshot_hash` on `administration_snapshot_hash`.
- `idx_activity_administrations_surface` on `surface_id`.
- `sqlite_autoindex_activity_administrations_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.activity_administration()`
- `Repository.administration_by_legacy_presentation()`
- `Repository.all_activity_administrations()`
- `Repository.consumer_pins_for_versions()`
- `Repository.fetch_administration()`
- `Repository.first_cold_observation_for_target()`
- `Repository.insert_legacy_administration()`
- `Repository.open_administration_atomic()`
- `Repository.set_administration_context()`
- `Repository.write_administration_lineage_atomic()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop/db/stores/observation_ledger.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/grading.py`
- `src/learnloop/goals/goal_contracts.py`
- `src/learnloop/reader/reader_dialogue.py`
- `src/learnloop/substrate/activities.py`
- `src/learnloop/substrate/administration_adapters.py`
- `src/learnloop/substrate/compat/activity_backfill.py`
- `src/learnloop/substrate/compat/card_outcome_replay.py`
- `src/learnloop/substrate/compat/substrate_cutover.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_activity_backfill.py`
- `tests/test_activity_substrate.py`
- `tests/test_assessment_enforcement.py`
- `tests/test_goal_contracts.py`
- `tests/test_reader_dialogue.py`
- `tests/test_administration_adapters.py`
- `tests/test_grade_resolution_pipeline.py`
- `tests/test_substrate_cutover.py`

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
CREATE TABLE activity_administrations (
  id TEXT PRIMARY KEY,
  surface_id TEXT NOT NULL REFERENCES activity_surfaces(id),
  card_version_id TEXT NOT NULL REFERENCES activity_card_versions(id),
  family_id TEXT NOT NULL REFERENCES activity_families(id),
  purpose TEXT NOT NULL
    CHECK (purpose IN ('diagnostic', 'instructional', 'practice', 'assessment')),
  administration_snapshot_hash TEXT NOT NULL,
  snapshot_json TEXT NOT NULL,
  target_contract_version_id TEXT,
  target_support_hash TEXT,
  grader_model_version_id TEXT,
  selection_policy_version_id TEXT,
  decision_params_hash TEXT,
  assistance_json TEXT,
  feedback_condition TEXT
    CHECK (feedback_condition IS NULL OR feedback_condition IN
      ('none', 'after_response', 'before_response')),
  eligibility_json TEXT,
  reservation_id TEXT,
  legacy_backfilled INTEGER NOT NULL DEFAULT 0
    CHECK (legacy_backfilled IN (0, 1)),
  created_at TEXT NOT NULL
, reading_phase TEXT, admin_context_json TEXT);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
