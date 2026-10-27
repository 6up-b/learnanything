---
title: "ad_commission_results"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "0843991f2b18f27dbcfa32509c74e214a072eab8"
source_commit_timestamp: "2026-10-27T17:51:02-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite ad_commission_results"
  - "table ad_commission_results"
schema_head: 226
table_name: "ad_commission_results"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "214_adaptive_difficulty_serving.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/214_adaptive_difficulty_serving.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/generation.py"
  - "src/learnloop/adaptive_difficulty/material_view.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/db/stores/ad_serving.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `ad_commission_results`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives ad commission result a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `selection_id`, `practice_item_id`, `content_hash`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §7.4: a landed commission's re-forecast, linked to its selection; the combined status is derived, the selection row is never mutated.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/214_adaptive_difficulty_serving.sql`.
- **Schema touched by:** `214_adaptive_difficulty_serving.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `selection_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/ad_selections\|ad_selections.id]] | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `content_hash` | `TEXT` | no | — | — | Stored value |
| `features_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `p_bar` | `REAL` | yes | — | — | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `state_hash` | `TEXT` | yes | — | — | Stored value |
| `landed_after_expiry` | `INTEGER` | yes | `0` | — | Stored value |
| `features_match` | `INTEGER` | yes | `1` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `protection_epoch` | `TEXT` | no | — | — | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `selection_id` → [[Reference/Database/Tables/ad_selections|`ad_selections.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_ad_commission_results_2` on `practice_item_id` (unique).
- `sqlite_autoindex_ad_commission_results_1` on `id` (unique).

Database triggers:

- `ad_commission_results_no_delete` — schema-enforced lifecycle or immutability constraint.
- `ad_commission_results_no_update` — schema-enforced lifecycle or immutability constraint.

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
CREATE TABLE ad_commission_results (
  id TEXT PRIMARY KEY,
  selection_id TEXT NOT NULL REFERENCES ad_selections(id),
  practice_item_id TEXT NOT NULL,
  content_hash TEXT,
  features_json TEXT,
  p_bar REAL NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('in_band', 'realized_out_of_band')),
  state_hash TEXT NOT NULL,
  -- 1 when the item landed after its commission had expired (Codex verify
  -- F15): the landing is recorded whatever the commission's expiry.
  landed_after_expiry INTEGER NOT NULL DEFAULT 0 CHECK (landed_after_expiry IN (0, 1)),
  -- Ownership is by cell and landing order, not by feature match (verify F15,
  -- round 6): `features_json` holds the item's realized features, and this is 1
  -- when they are the commission's requested point.
  features_match INTEGER NOT NULL DEFAULT 1 CHECK (features_match IN (0, 1)),
  created_at TEXT NOT NULL,
  -- The protection epoch the row was computed under (AD23 redesign round 2):
  -- AD reads a row back only at that epoch (adaptive_difficulty.protected_tables.EPOCH).
  protection_epoch TEXT,
  -- One owner per landed item (verify F16): the first attribution is final.
  UNIQUE (practice_item_id)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
