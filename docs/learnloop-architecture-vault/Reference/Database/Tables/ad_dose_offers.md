---
title: "ad_dose_offers"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "2d93d8ba649c9d08c1fec62fcee731e7f76753e5"
source_commit_timestamp: "2026-10-31T15:33:42-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite ad_dose_offers"
  - "table ad_dose_offers"
schema_head: 226
table_name: "ad_dose_offers"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "214_adaptive_difficulty_serving.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/214_adaptive_difficulty_serving.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/dose.py"
  - "src/learnloop/adaptive_difficulty/material_view.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/db/stores/ad_serving.py"
  - "src/learnloop/scheduling/randomization_layer.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `ad_dose_offers`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives ad dose offer a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `draw_id`, `visit_id`, `extraction_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §5.12 (D21): the Reader's randomized dose offers. One `draw` row per eligible section draw (the feasible variants and why any was infeasible, the base policy's version, the floor, every propensity, the seed and the chosen variant), written before anything is shown; later rows record `delivered`, `not_delivered`, `taken` or `dismissed` and never change the draw's row. No dwell, scroll, active time or answer value is stored.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/214_adaptive_difficulty_serving.sql`.
- **Schema touched by:** `213_adaptive_difficulty_receipts.sql`, `214_adaptive_difficulty_serving.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `row_kind` | `TEXT` | yes | — | — | Stored value |
| `draw_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/ad_dose_offers\|ad_dose_offers.id]] | Stored value |
| `draw_key` | `TEXT` | no | — | — | Stored value |
| `visit_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `extraction_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `section_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `learning_object_ids_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `feasible_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `infeasible_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `base_version` | `TEXT` | no | — | — | Stored value |
| `floor` | `REAL` | no | — | — | Stored value |
| `propensities_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `seed` | `TEXT` | no | — | — | Stored value |
| `u` | `REAL` | no | — | — | Stored value |
| `chosen_variant` | `TEXT` | no | — | — | Stored value |
| `content_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `forecast_p` | `REAL` | no | — | — | Stored value |
| `detail_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `protection_epoch` | `TEXT` | no | — | — | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `draw_id` → [[Reference/Database/Tables/ad_dose_offers|`ad_dose_offers.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_ad_dose_offers_created` on `created_at`.
- `idx_ad_dose_offers_draw` on `draw_id`, `created_at`.
- `sqlite_autoindex_ad_dose_offers_2` on `draw_key` (unique).
- `sqlite_autoindex_ad_dose_offers_1` on `id` (unique).

Database triggers:

- `ad_dose_offers_no_delete` — schema-enforced lifecycle or immutability constraint.
- `ad_dose_offers_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/adaptive_difficulty/material_view.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/ad_ingest_fakes.py`
- `tests/test_ad23_contract.py`
- `tests/test_ad23_migration.py`
- `tests/test_ad3_dose_arm.py`
- `tests/test_ad_guard.py`
- `tests/test_ad_protected_tables.py`
- `tests/test_architecture.py`

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
CREATE TABLE ad_dose_offers (
  id TEXT PRIMARY KEY,
  row_kind TEXT NOT NULL
    CHECK (row_kind IN ('draw', 'delivered', 'not_delivered', 'taken', 'dismissed')),
  draw_id TEXT REFERENCES ad_dose_offers(id),
  draw_key TEXT UNIQUE,
  visit_id TEXT,
  extraction_id TEXT,
  section_id TEXT,
  learning_object_ids_json TEXT,
  feasible_json TEXT,
  infeasible_json TEXT,
  base_version TEXT,
  floor REAL,
  propensities_json TEXT,
  seed TEXT,
  u REAL,
  chosen_variant TEXT CHECK (chosen_variant IS NULL OR chosen_variant IN
    ('none', 'extra_worked_example', 'extra_question')),
  -- What an extra offer carries (a question id, a worked example's span), so a
  -- taken offer's reading opportunity can name it.
  content_json TEXT,
  -- The AD forecast fixed before the draw (precision adjustment, §5.12).
  forecast_p REAL,
  detail_json TEXT,
  created_at TEXT NOT NULL,
  -- The protection epoch the row was computed under (AD23 redesign round 2):
  -- AD reads a row back only at that epoch (adaptive_difficulty.protected_tables.EPOCH).
  protection_epoch TEXT,
  CHECK (
    (row_kind = 'draw' AND draw_id IS NULL AND draw_key IS NOT NULL)
    OR (row_kind != 'draw' AND draw_id IS NOT NULL AND draw_key IS NULL)
  )
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
