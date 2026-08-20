---
title: "card_lineages"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite card_lineages"
  - "table card_lineages"
schema_head: 156
table_name: "card_lineages"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "activity-substrate"
introduced_in: "075_card_lineage_state.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/075_card_lineage_state.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/curriculum/depth_transition.py"
  - "src/learnloop/substrate/card_lineage.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `card_lineages`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives card lineage a stable database identity so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It supplies replay-stable input rather than a disposable cache. Rows bind `family_id`, `card_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/075_card_lineage_state.sql`.
- **Schema touched by:** `075_card_lineage_state.sql`, `079_progression_and_lapse.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `family_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_families\|activity_families.id]] | Stored value |
| `card_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_cards\|activity_cards.id]] | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `card_id` → [[Reference/Database/Tables/activity_cards|`activity_cards.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `family_id` → [[Reference/Database/Tables/activity_families|`activity_families.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_card_lineages_card` on `card_id`.
- `idx_card_lineages_family` on `family_id`.
- `sqlite_autoindex_card_lineages_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.card_lineage()`
- `Repository.create_card_lineage()`
- `Repository.record_depth_transition_atomic()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/depth_transition.py`
- `src/learnloop/substrate/card_lineage.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_progression.py`

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
CREATE TABLE card_lineages (
  id TEXT PRIMARY KEY,
  family_id TEXT REFERENCES activity_families(id),
  -- The card whose executable contract this lineage tracks (§3.7). Bare-ish: FKs the
  -- 065 card identity, not a card version (versions live along the lineage edges).
  card_id TEXT REFERENCES activity_cards(id),
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
