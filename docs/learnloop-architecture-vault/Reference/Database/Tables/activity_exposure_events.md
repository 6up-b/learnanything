---
title: "activity_exposure_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite activity_exposure_events"
  - "table activity_exposure_events"
schema_head: 157
table_name: "activity_exposure_events"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "activity-substrate"
introduced_in: "065_activity_lineage_substrate.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/065_activity_lineage_substrate.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/scheduling/constraint_engine.py"
  - "src/learnloop/scheduling/controller_cutover.py"
  - "src/learnloop/scheduling/controller_store.py"
  - "src/learnloop/scheduling/open_world_gate.py"
  - "src/learnloop/substrate/activities.py"
  - "src/learnloop/cli/surfaces.py"
  - "src/learnloop/learner/familiarity.py"
  - "src/learnloop/substrate/compat/activity_backfill.py"
  - "src/learnloop/substrate/compat/substrate_cutover.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `activity_exposure_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of activity exposure so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It supplies replay-stable input rather than a disposable cache. Rows bind `surface_id`, `administration_id`, `surface_hash`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> ---------------------------------------------------------------------------- Exposure ledger: THE ONE shared familiarity ledger (§3.6). Every purpose writes here. Held-out eligibility only ever queries this table. A partial unique index guarantees a surface is RENDERED at most once (the atomic burn boundary, §4.5; test 9.5 "two concurrent renders expose once"). ----------------------------------------------------------------------------

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/065_activity_lineage_substrate.sql`.
- **Schema touched by:** `065_activity_lineage_substrate.sql`, `077_familiarity_namespace.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `surface_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_surfaces\|activity_surfaces.id]] | Stored value |
| `administration_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_administrations\|activity_administrations.id]] | Stored value |
| `surface_hash` | `TEXT` | yes | — | — | Stored value |
| `fingerprint` | `TEXT` | no | — | — | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `purpose` | `TEXT` | yes | — | — | Stored value |
| `consumes_unseen` | `INTEGER` | yes | `0` | — | Stored value |
| `detail_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `administration_id` → [[Reference/Database/Tables/activity_administrations|`activity_administrations.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `surface_id` → [[Reference/Database/Tables/activity_surfaces|`activity_surfaces.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_activity_exposure_fingerprint` on `fingerprint`.
- `idx_activity_exposure_surface_hash` on `surface_hash`.
- `idx_activity_exposure_surface` on `surface_id`, `kind`.
- `idx_activity_exposure_render_once` on `surface_id` (unique).
- `sqlite_autoindex_activity_exposure_events_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.activity_exposure_events_for_surface()`
- `Repository.append_exposure_event()`
- `Repository.append_exposure_event_at()`
- `Repository.exposures_by_fingerprint()`
- `Repository.exposures_by_surface_hash()`
- `Repository.exposures_for_surface()`
- `Repository.open_administration_atomic()`
- `Repository.write_administration_lineage_atomic()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop/scheduling/controller_store.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/surfaces.py`
- `src/learnloop/learner/familiarity.py`
- `src/learnloop/substrate/activities.py`
- `src/learnloop/substrate/compat/activity_backfill.py`
- `src/learnloop/substrate/compat/substrate_cutover.py`
- `src/learnloop/substrate/surface_mint.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_activity_backfill.py`
- `tests/test_activity_substrate.py`
- `tests/test_cross_seam_exposure.py`
- `tests/test_progression.py`
- `tests/test_administration_adapters.py`
- `tests/test_assessment_enforcement.py`
- `tests/test_familiarity.py`
- `tests/test_journey6.py`
- `tests/test_substrate_cutover.py`
- `tests/test_surface_mint.py`

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
CREATE TABLE activity_exposure_events (
  id TEXT PRIMARY KEY,
  surface_id TEXT NOT NULL REFERENCES activity_surfaces(id),
  administration_id TEXT REFERENCES activity_administrations(id),
  surface_hash TEXT NOT NULL,
  fingerprint TEXT,
  kind TEXT NOT NULL
    CHECK (kind IN
      ('rendered', 'submitted', 'feedback_revealed',
       'externally_reported', 'shared_stimulus')),
  purpose TEXT NOT NULL
    CHECK (purpose IN ('diagnostic', 'instructional', 'practice', 'assessment')),
  consumes_unseen INTEGER NOT NULL DEFAULT 0
    CHECK (consumes_unseen IN (0, 1)),
  detail_json TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
