---
title: "angle_inventories"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite angle_inventories"
  - "table angle_inventories"
schema_head: 157
table_name: "angle_inventories"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "079_progression_and_lapse.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/079_progression_and_lapse.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/scheduling/progression.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `angle_inventories`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives angle inventorie a stable database identity so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It supplies replay-stable input rather than a disposable cache. Rows bind `family_version_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> P1 step 8 (spec_p1_shared_substrate §4.3, §5.4, §5.5, §5.7): angle inventories, family evidence-cap policies, and durable lapse/retry episodes. These back the within-family angle progression (§5.4 orthogonal-next), the family evidence cap (§4.3 + owner decision A.4 tight-kinship clustering), and post-lapse linked retries (§5.5). The one-edge depth-transition service (§5.7) reuses P0.4's goal_contracts.append_authorized_depth_successor + P1 commitments/card lineage and adds no schema of its own.  Migration numbering: highest applied on disk = 078 (surface mint jobs); P1 step 8 starts at 079. Never edit applied migrations.

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/079_progression_and_lapse.sql`.
- **Schema touched by:** `079_progression_and_lapse.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `family_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_family_versions\|activity_family_versions.id]] | Stored value |
| `coordinates_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `coverage_targets_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `family_version_id` → [[Reference/Database/Tables/activity_family_versions|`activity_family_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_angle_inv_family` on `family_version_id`.
- `sqlite_autoindex_angle_inventories_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.angle_inventories_for_family()`
- `Repository.insert_angle_inventory()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/scheduling/progression.py`

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
CREATE TABLE angle_inventories (
  id TEXT PRIMARY KEY,
  family_version_id TEXT REFERENCES activity_family_versions(id),
  -- §5.4 coordinates: cue direction / response form / representation / operation /
  -- context / task span / transfer distance / scaffolding. A cosmetic paraphrase is
  -- the same angle; a new cognitive angle is a sibling card/branch.
  coordinates_json TEXT NOT NULL,
  coverage_targets_json TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
