---
title: "activity_surface_reservations"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite activity_surface_reservations"
  - "table activity_surface_reservations"
schema_head: 156
table_name: "activity_surface_reservations"
table_role: "workflow"
functionality_status: "active"
domain_family: "activity-substrate"
introduced_in: "065_activity_lineage_substrate.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/065_activity_lineage_substrate.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/curriculum/golden_path_confirm.py"
  - "src/learnloop/goals/goal_contracts.py"
  - "src/learnloop/reader/reader_dialogue.py"
  - "src/learnloop/scheduling/controller_snapshot.py"
  - "src/learnloop/substrate/activities.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `activity_surface_reservations`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives activity surface reservation a stable database identity so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `surface_id`, `goal_id`, `target_contract_version_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> ---------------------------------------------------------------------------- Reservation: an assessment surface set aside from the pinned target's frozen distribution (§4.5). At most one LIVE (status='reserved') reservation per surface, enforced by a partial unique index (mirrors 023/053). A reservation does not burn; cancellation before render may append release_unseen. ----------------------------------------------------------------------------

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/065_activity_lineage_substrate.sql`.
- **Schema touched by:** `065_activity_lineage_substrate.sql`, `070_p0_measurement_hardening.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `surface_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_surfaces\|activity_surfaces.id]] | Stored value |
| `goal_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `target_contract_version_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `target_support_hash` | `TEXT` | no | — | — | Stored value |
| `purpose` | `TEXT` | yes | — | — | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `eligibility_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `administration_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_administrations\|activity_administrations.id]] | Stored value |
| `reserved_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `closed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `administration_id` → [[Reference/Database/Tables/activity_administrations|`activity_administrations.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `surface_id` → [[Reference/Database/Tables/activity_surfaces|`activity_surfaces.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_asr_target_version` on `target_contract_version_id`.
- `idx_activity_reservation_surface` on `surface_id`, `status`.
- `idx_activity_reservation_live_surface` on `surface_id` (unique).
- `sqlite_autoindex_activity_surface_reservations_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.close_surface_reservation()`
- `Repository.confirm_golden_path_atomic()`
- `Repository.consumer_pins_for_versions()`
- `Repository.fetch_reservation()`
- `Repository.insert_surface_reservation()`
- `Repository.open_administration_atomic()`
- `Repository.reserved_assessment_surfaces()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/golden_path_confirm.py`
- `src/learnloop/goals/goal_contracts.py`
- `src/learnloop/reader/reader_dialogue.py`
- `src/learnloop/scheduling/controller_snapshot.py`
- `src/learnloop/substrate/activities.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_activity_substrate.py`
- `tests/test_golden_path_confirm.py`
- `tests/test_administration_adapters.py`

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
CREATE TABLE activity_surface_reservations (
  id TEXT PRIMARY KEY,
  surface_id TEXT NOT NULL REFERENCES activity_surfaces(id),
  goal_id TEXT,
  target_contract_version_id TEXT,
  target_support_hash TEXT,
  purpose TEXT NOT NULL
    CHECK (purpose IN ('diagnostic', 'instructional', 'practice', 'assessment')),
  status TEXT NOT NULL
    CHECK (status IN ('reserved', 'rendered', 'cancelled', 'released_unseen')),
  eligibility_json TEXT NOT NULL,
  administration_id TEXT REFERENCES activity_administrations(id),
  reserved_at TEXT NOT NULL,
  closed_at TEXT
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
