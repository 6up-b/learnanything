---
title: "ad_history_forecast_draws"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "b1693676a83a561b40dd2333d6b480e71f6ad59f"
source_commit_timestamp: "2026-11-06T18:53:04-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite ad_history_forecast_draws"
  - "table ad_history_forecast_draws"
schema_head: 249
table_name: "ad_history_forecast_draws"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "245_history_forecaster.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/245_history_forecaster.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/history_forecast.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/db/stores/ad_receipts.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `ad_history_forecast_draws`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives ad history forecast draw a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `plan_presentation_id`, `practice_item_id`, `learning_object_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/245_history_forecaster.sql`.
- **Schema touched by:** `245_history_forecaster.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `draw_key` | `TEXT` | yes | — | — | Stored value |
| `plan_presentation_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `draw_version` | `TEXT` | yes | — | — | Stored value |
| `seed` | `TEXT` | yes | — | — | Stored value |
| `u` | `REAL` | yes | — | — | Stored value |
| `anchor_rung` | `TEXT` | yes | — | — | Stored value |
| `drawn_rung` | `TEXT` | yes | — | — | Stored value |
| `propensity` | `REAL` | yes | — | — | Stored value |
| `propensities_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `card_version` | `TEXT` | yes | — | — | Stored value |
| `frozen_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `protection_epoch` | `TEXT` | no | — | — | Stored value |
| `served_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_ad_history_forecast_draws_presentation` on `plan_presentation_id`.
- `sqlite_autoindex_ad_history_forecast_draws_2` on `draw_key` (unique).
- `sqlite_autoindex_ad_history_forecast_draws_1` on `id` (unique).

Database triggers:

- `ad_history_forecast_draws_no_delete` — schema-enforced lifecycle or immutability constraint.
- `ad_history_forecast_draws_no_update` — schema-enforced lifecycle or immutability constraint.

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

- `tests/test_ro2_ad_document_ir.py`
- `tests/test_ro2_ad_raw_document_reads.py`
- `tests/test_ro2_history_forecaster.py`
- `tests/test_ro2_history_migration.py`
- `tests/test_ro2_history_resolve.py`

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
CREATE TABLE ad_history_forecast_draws (
  id TEXT PRIMARY KEY,
  -- Idempotency: llm_history_v1:plan_presentation:<presentation id>.
  draw_key TEXT NOT NULL UNIQUE,
  plan_presentation_id TEXT NOT NULL,
  practice_item_id TEXT NOT NULL,
  learning_object_id TEXT,
  -- The draw's code version (adaptive_difficulty.history_forecast.DRAW_VERSION).
  draw_version TEXT NOT NULL,
  -- The seed (a digest of the presentation id and the draw version) and the
  -- uniform u in [0, 1) it gives; the drawn rung is the u-th third.
  seed TEXT NOT NULL,
  u REAL NOT NULL CHECK (u >= 0 AND u < 1),
  -- H3 on every eligible presentation.
  anchor_rung TEXT NOT NULL CHECK (anchor_rung = 'H3'),
  drawn_rung TEXT NOT NULL CHECK (drawn_rung IN ('H0', 'H1', 'H2')),
  -- The drawn rung's probability, and every rung's ({"H0": .., "H1": .., "H2": ..}).
  propensity REAL NOT NULL CHECK (propensity > 0 AND propensity <= 1),
  propensities_json TEXT NOT NULL,
  -- ad-forecast-state-v3.
  card_version TEXT NOT NULL,
  -- Per frozen rung: {owner_key, state_hash, bytes, left_out}: ids and counts only.
  frozen_json TEXT NOT NULL,
  -- The protection epoch the cards were read under (sent only at it).
  protection_epoch TEXT,
  served_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
