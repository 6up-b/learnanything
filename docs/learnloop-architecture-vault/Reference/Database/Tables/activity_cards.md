---
title: "activity_cards"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite activity_cards"
  - "table activity_cards"
schema_head: 156
table_name: "activity_cards"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "activity-substrate"
introduced_in: "065_activity_lineage_substrate.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/065_activity_lineage_substrate.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/curriculum/golden_path_assessment.py"
  - "src/learnloop/reader/reader_authoring.py"
  - "src/learnloop/substrate/activities.py"
  - "src/learnloop/substrate/compat/activity_backfill.py"
  - "src/learnloop/substrate/compat/substrate_cutover.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `activity_cards`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives activity card a stable database identity so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It supplies replay-stable input rather than a disposable cache. Rows bind `family_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> ---------------------------------------------------------------------------- Card: stable executable identity + generic ActivityContract. card_contract_hash is content-addressed over the semantic contract (design §2). lineage_kind records how this card relates to its predecessor; certification never crosses a 'fork' (invariant §1.1; enforced in the grading/cert package, edge recorded here). ----------------------------------------------------------------------------

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/065_activity_lineage_substrate.sql`.
- **Schema touched by:** `065_activity_lineage_substrate.sql`, `070_p0_measurement_hardening.sql`, `075_card_lineage_state.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `family_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_families\|activity_families.id]] | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `family_id` → [[Reference/Database/Tables/activity_families|`activity_families.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_activity_cards_family_unique` on `family_id` (unique).
- `idx_activity_cards_family` on `family_id`.
- `sqlite_autoindex_activity_cards_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.activity_family_purpose_for_card_version()`
- `Repository.ensure_activity_card()`
- `Repository.resolved_activity_for_surface()`
- `Repository.surfaces_for_family()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/golden_path_assessment.py`
- `src/learnloop/reader/reader_authoring.py`
- `src/learnloop/substrate/activities.py`
- `src/learnloop/substrate/compat/activity_backfill.py`
- `src/learnloop/substrate/compat/substrate_cutover.py`
- `src/learnloop/substrate/surface_pool.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_activity_backfill.py`
- `tests/test_activity_substrate.py`
- `tests/test_goal_contracts.py`
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
CREATE TABLE activity_cards (
  id TEXT PRIMARY KEY,
  family_id TEXT NOT NULL REFERENCES activity_families(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
