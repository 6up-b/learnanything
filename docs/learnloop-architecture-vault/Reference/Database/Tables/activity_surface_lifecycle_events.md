---
title: "activity_surface_lifecycle_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite activity_surface_lifecycle_events"
  - "table activity_surface_lifecycle_events"
schema_head: 157
table_name: "activity_surface_lifecycle_events"
table_role: "receipt"
functionality_status: "active"
domain_family: "activity-substrate"
introduced_in: "065_activity_lineage_substrate.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/065_activity_lineage_substrate.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/attempts/grade_resolution.py"
  - "src/learnloop/cli/surfaces.py"
  - "src/learnloop/curriculum/golden_path_assessment.py"
  - "src/learnloop/curriculum/golden_path_confirm.py"
  - "src/learnloop/substrate/activities.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `activity_surface_lifecycle_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves the ordered lifecycle transitions for activity surface so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `surface_id`, `reservation_id`, `administration_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> ---------------------------------------------------------------------------- Surface lifecycle events: reserve, release_unseen, expose, consume, quarantine, retire, practice_successor_minted (§3.5). Append-only audit of the surface's held-out life; distinct from the familiarity ledger above. ----------------------------------------------------------------------------

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/065_activity_lineage_substrate.sql`.
- **Schema touched by:** `065_activity_lineage_substrate.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `surface_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_surfaces\|activity_surfaces.id]] | Stored value |
| `reservation_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_surface_reservations\|activity_surface_reservations.id]] | Stored value |
| `administration_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_administrations\|activity_administrations.id]] | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `reason` | `TEXT` | no | — | — | Stored value |
| `detail_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `administration_id` → [[Reference/Database/Tables/activity_administrations|`activity_administrations.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `reservation_id` → [[Reference/Database/Tables/activity_surface_reservations|`activity_surface_reservations.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `surface_id` → [[Reference/Database/Tables/activity_surfaces|`activity_surfaces.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_activity_surface_lifecycle_surface` on `surface_id`, `created_at`.
- `sqlite_autoindex_activity_surface_lifecycle_events_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.append_surface_lifecycle_event()`
- `Repository.confirm_golden_path_atomic()`
- `Repository.open_administration_atomic()`
- `Repository.surface_lifecycle_history()`
- `Repository.write_administration_lineage_atomic()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/grade_resolution.py`
- `src/learnloop/cli/surfaces.py`
- `src/learnloop/curriculum/golden_path_assessment.py`
- `src/learnloop/curriculum/golden_path_confirm.py`
- `src/learnloop/substrate/activities.py`
- `src/learnloop/substrate/compat/substrate_cutover.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_activity_substrate.py`
- `tests/test_administration_adapters.py`
- `tests/test_assessment_enforcement.py`
- `tests/test_golden_path_assessment.py`

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
CREATE TABLE activity_surface_lifecycle_events (
  id TEXT PRIMARY KEY,
  surface_id TEXT NOT NULL REFERENCES activity_surfaces(id),
  reservation_id TEXT REFERENCES activity_surface_reservations(id),
  administration_id TEXT REFERENCES activity_administrations(id),
  kind TEXT NOT NULL
    CHECK (kind IN
      ('reserve', 'release_unseen', 'expose', 'consume', 'quarantine',
       'retire', 'practice_successor_minted')),
  reason TEXT,
  detail_json TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
