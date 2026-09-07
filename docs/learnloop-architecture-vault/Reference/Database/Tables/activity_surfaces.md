---
title: "activity_surfaces"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite activity_surfaces"
  - "table activity_surfaces"
schema_head: 157
table_name: "activity_surfaces"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "activity-substrate"
introduced_in: "065_activity_lineage_substrate.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/065_activity_lineage_substrate.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/cli/surfaces.py"
  - "src/learnloop/content/authoring/item_authoring.py"
  - "src/learnloop/curriculum/golden_path_assessment.py"
  - "src/learnloop/reader/reader_dialogue.py"
  - "src/learnloop/scheduling/controller_snapshot.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `activity_surfaces`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives activity surface a stable database identity so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It supplies replay-stable input rather than a disposable cache. Rows bind `card_version_id`, `legacy_practice_item_id`, `surface_hash`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> ---------------------------------------------------------------------------- Surface: exact prompt/parameters/media/answer-key artifact bound to ONE card version. surface_hash is the exact-collision key (§3.6 rule 1); fingerprint is the shared-stimulus/near-clone key (§3.6 rule 2). legacy_surface_unverifiable marks a historical surface whose exact content is unrecoverable (§7.1 step 4): it grants no new pristine terminal credit. ----------------------------------------------------------------------------

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/065_activity_lineage_substrate.sql`.
- **Schema touched by:** `065_activity_lineage_substrate.sql`, `070_p0_measurement_hardening.sql`, `077_familiarity_namespace.sql`, `078_surface_mint_jobs.sql`, `080_mint_fencing_and_commitment_idempotency.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `card_version_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_card_versions\|activity_card_versions.id]] | Stored value |
| `surface_hash` | `TEXT` | yes | — | — | Stored value |
| `fingerprint` | `TEXT` | no | — | — | Stored value |
| `surface_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `legacy_practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `legacy_surface_unverifiable` | `INTEGER` | yes | `0` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `card_version_id` → [[Reference/Database/Tables/activity_card_versions|`activity_card_versions.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_activity_surfaces_legacy_item` on `legacy_practice_item_id`.
- `idx_activity_surfaces_fingerprint` on `fingerprint`.
- `idx_activity_surfaces_hash` on `surface_hash`.
- `sqlite_autoindex_activity_surfaces_2` on `card_version_id`, `surface_hash` (unique).
- `sqlite_autoindex_activity_surfaces_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.ensure_activity_surface()`
- `Repository.fetch_surface()`
- `Repository.fetch_surface_by_hash()`
- `Repository.mark_surface_unverifiable()`
- `Repository.reserved_assessment_surfaces()`
- `Repository.resolved_activity_for_surface()`
- `Repository.surfaces_for_card_version()`
- `Repository.surfaces_for_family()`
- `Repository.surfaces_for_legacy_practice_item()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/surfaces.py`
- `src/learnloop/content/authoring/item_authoring.py`
- `src/learnloop/curriculum/golden_path_assessment.py`
- `src/learnloop/reader/reader_dialogue.py`
- `src/learnloop/scheduling/controller_snapshot.py`
- `src/learnloop/substrate/activities.py`
- `src/learnloop/substrate/compat/activity_backfill.py`
- `src/learnloop/substrate/surface_mint.py`
- `src/learnloop/substrate/surface_pool.py`
- `src/learnloop_sidecar/handlers/golden_path_assessment.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_activity_backfill.py`
- `tests/test_activity_substrate.py`
- `tests/test_goal_contracts.py`
- `tests/test_administration_adapters.py`
- `tests/test_event_sufficiency.py`
- `tests/test_familiarity.py`
- `tests/test_item_authoring.py`
- `tests/test_journey6.py`
- `tests/test_kinship_feature.py`
- `tests/test_laddered_stems.py`
- `tests/test_p2_leakage_suite.py`
- `tests/test_progression.py`
- `tests/test_reader_dialogue.py`
- `tests/test_substrate_cutover.py`
- `tests/test_surface_mint.py`
- `tests/test_surface_pool.py`

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
CREATE TABLE activity_surfaces (
  id TEXT PRIMARY KEY,
  card_version_id TEXT NOT NULL
    REFERENCES activity_card_versions(id) ON DELETE CASCADE,
  surface_hash TEXT NOT NULL,
  fingerprint TEXT,
  surface_json TEXT NOT NULL,
  legacy_practice_item_id TEXT,
  legacy_surface_unverifiable INTEGER NOT NULL DEFAULT 0
    CHECK (legacy_surface_unverifiable IN (0, 1)),
  created_at TEXT NOT NULL,
  UNIQUE(card_version_id, surface_hash)
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
