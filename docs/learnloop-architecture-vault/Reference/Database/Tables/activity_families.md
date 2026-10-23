---
title: "activity_families"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "ea590e192e7d05cf407e35bee338909582716483"
source_commit_timestamp: "2026-10-22T23:06:34-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite activity_families"
  - "table activity_families"
schema_head: 217
table_name: "activity_families"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "activity-substrate"
introduced_in: "065_activity_lineage_substrate.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/065_activity_lineage_substrate.sql"
  - "src/learnloop/adaptive_difficulty/forecasters.py"
  - "src/learnloop/content/authoring/source_exercise_import.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/db/stores/families.py"
  - "src/learnloop/field/outcomes.py"
  - "src/learnloop/ops/pf_generation.py"
  - "src/learnloop/ops/pf_publish.py"
  - "src/learnloop/reader/reader_authoring.py"
  - "src/learnloop/substrate/activities.py"
  - "src/learnloop/substrate/compat/activity_backfill.py"
  - "src/learnloop/substrate/compat/substrate_cutover.py"
  - "src/learnloop/substrate/surface_pool.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `activity_families`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives activity familie a stable database identity so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It supplies replay-stable input rather than a disposable cache. Rows bind `legacy_kind`, `purpose`, `title`, making the operational relationship explicit. ^table-purpose

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/065_activity_lineage_substrate.sql`.
- **Schema touched by:** `065_activity_lineage_substrate.sql`, `070_p0_measurement_hardening.sql`, `075_card_lineage_state.sql`, `168_activity_family_membership.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `purpose` | `TEXT` | yes | — | — | Stored value |
| `legacy_kind` | `TEXT` | no | — | — | Stored value |
| `title` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_activity_families_authoring` on `purpose` (unique).
- `sqlite_autoindex_activity_families_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.activity_family_purpose_for_card_version()`
- `Repository.ensure_activity_family()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop/db/stores/families.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/reader/reader_authoring.py`
- `src/learnloop/substrate/activities.py`
- `src/learnloop/substrate/compat/activity_backfill.py`
- `src/learnloop/substrate/compat/substrate_cutover.py`
- `src/learnloop/substrate/surface_pool.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_activity_backfill.py`
- `tests/test_activity_families.py`
- `tests/test_activity_substrate.py`
- `tests/test_family_memory_projection.py`
- `tests/test_goal_contracts.py`
- `tests/test_judge_routes.py`
- `tests/test_pf_generation.py`
- `tests/test_pf_reports.py`
- `tests/test_activity_contract_extensions.py`
- `tests/test_administration_adapters.py`
- `tests/test_card_lineage.py`
- `tests/test_commitment_arcs.py`
- `tests/test_depth_transition.py`
- `tests/test_event_sufficiency.py`
- `tests/test_familiarity.py`
- `tests/test_journey6.py`
- `tests/test_kinship_feature.py`
- `tests/test_laddered_stems.py`
- `tests/test_progression.py`
- `tests/test_reader_authoring.py`

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
CREATE TABLE activity_families (
  id TEXT PRIMARY KEY,
  purpose TEXT NOT NULL
    CHECK (purpose IN ('diagnostic', 'instructional', 'practice', 'assessment')),
  legacy_kind TEXT
    CHECK (legacy_kind IS NULL OR legacy_kind IN
      ('practice_item', 'probe', 'exam', 'synthetic')),
  title TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
