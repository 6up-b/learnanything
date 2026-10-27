---
title: "ad_selections"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "72208d5a50777166e4f6d036a3f61805212debf1"
source_commit_timestamp: "2026-10-27T13:01:42-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite ad_selections"
  - "table ad_selections"
schema_head: 225
table_name: "ad_selections"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "214_adaptive_difficulty_serving.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/214_adaptive_difficulty_serving.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/material_view.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/adaptive_difficulty/serving.py"
  - "src/learnloop/daily_plan/ad_slot.py"
  - "src/learnloop/daily_plan/engine.py"
  - "src/learnloop/db/stores/ad_serving.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `ad_selections`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives ad selection a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `learning_object_id`, `daily_plan_id`, `block_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/214_adaptive_difficulty_serving.sql`.
- **Schema touched by:** `214_adaptive_difficulty_serving.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `decision_key` | `TEXT` | yes | — | — | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `view` | `TEXT` | yes | — | — | Stored value |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `cell_facet` | `TEXT` | no | — | — | Stored value |
| `cell_capability` | `TEXT` | no | — | — | Stored value |
| `daily_plan_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `block_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `slot_position` | `INTEGER` | no | — | — | Stored value |
| `slot_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `mode` | `TEXT` | yes | — | — | Stored value |
| `support_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `excluded_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `constants_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `seed` | `TEXT` | yes | — | — | Stored value |
| `u` | `REAL` | no | — | — | Stored value |
| `chosen_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `chosen_point_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `propensity` | `REAL` | no | — | — | Stored value |
| `router_decision_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `router_propensity` | `REAL` | no | — | — | Stored value |
| `pair_propensity` | `REAL` | no | — | — | Stored value |
| `empty_support` | `INTEGER` | yes | — | — | Stored value |
| `state_hash` | `TEXT` | yes | — | — | Stored value |
| `versions_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `generating_job_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `protection_epoch` | `TEXT` | no | — | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_ad_selections_block` on `block_id`, `slot_position`.
- `idx_ad_selections_cell` on `kind`, `cell_facet`, `cell_capability`, `created_at`.
- `sqlite_autoindex_ad_selections_2` on `decision_key` (unique).
- `sqlite_autoindex_ad_selections_1` on `id` (unique).

Database triggers:

- `ad_selections_no_delete` — schema-enforced lifecycle or immutability constraint.
- `ad_selections_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

None found by exact static reference scan.

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_ad23_contract.py`
- `tests/test_ad23_migration.py`
- `tests/test_ad2_model.py`
- `tests/test_ad2_serving.py`
- `tests/test_ad_guard.py`
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
CREATE TABLE ad_selections (
  id TEXT PRIMARY KEY,
  decision_key TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL CHECK (kind IN ('serve', 'commission')),
  -- The view the draw read: `subject` (promoted_predictor on) or `lo:<id>`.
  view TEXT NOT NULL,
  learning_object_id TEXT,
  cell_facet TEXT,
  cell_capability TEXT,
  daily_plan_id TEXT,
  block_id TEXT,
  slot_position INTEGER,
  slot_item_id TEXT,
  mode TEXT NOT NULL CHECK (mode IN ('band', 'calibrate', 'predecessor', 'empty_support')),
  -- [{ref, p_band, p_bar, info, propensity}] over the support S (serve) or X_c (commission).
  support_json TEXT NOT NULL,
  -- [{ref, failed: [check, ...]}]: candidates that were not in S, and why.
  excluded_json TEXT NOT NULL,
  constants_json TEXT NOT NULL,
  seed TEXT NOT NULL,
  u REAL,
  chosen_item_id TEXT,
  chosen_point_json TEXT,
  propensity REAL,
  -- §10.1: the router's propensity for the block, and the pair's.
  router_decision_id TEXT,
  router_propensity REAL,
  pair_propensity REAL,
  empty_support INTEGER NOT NULL CHECK (empty_support IN (0, 1)),
  state_hash TEXT NOT NULL,
  versions_json TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  -- A commission the generation path drew inside a durable job: that job
  -- (`ingest_jobs.id`, no foreign key: jobs may be pruned). Its expiry clock
  -- starts when the job finishes (Codex verify F14). NULL for a serve draw,
  -- a serve-time commission (its batch is named by it) and a draw outside a job.
  generating_job_id TEXT,
  created_at TEXT NOT NULL,
  -- The protection epoch the row was computed under (AD23 redesign round 2):
  -- AD reads a row back only at that epoch (adaptive_difficulty.protected_tables.EPOCH).
  protection_epoch TEXT
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
