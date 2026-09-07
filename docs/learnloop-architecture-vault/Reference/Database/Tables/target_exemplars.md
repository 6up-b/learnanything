---
title: "target_exemplars"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite target_exemplars"
  - "table target_exemplars"
schema_head: 157
table_name: "target_exemplars"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "081_task_blueprints.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/081_task_blueprints.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/curriculum/task_blueprints.py"
  - "src/learnloop_sidecar/handlers/ladder.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `target_exemplars`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives target exemplar a stable database identity so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It supplies replay-stable input rather than a disposable cache. Rows bind `blueprint_version_id`, `exposure_status`, `exemplar_ref`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Exemplar link rows (§3.3): the selected exercises carry exposure status `familiar_anchor` and ZERO held-out weight -- an anchor grounds generation and explanation but can never count as unseen assessment (invariant 4 / §12.1).

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/081_task_blueprints.sql`.
- **Schema touched by:** `081_task_blueprints.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `blueprint_version_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/task_blueprint_versions\|task_blueprint_versions.id]] | Stored value |
| `exemplar_ref` | `TEXT` | yes | — | — | Stored value |
| `weight` | `REAL` | yes | `1.0` | — | Stored value |
| `exposure_status` | `TEXT` | yes | `'familiar_anchor'` | — | Stored value |
| `held_out_weight` | `REAL` | yes | `0.0` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `blueprint_version_id` → [[Reference/Database/Tables/task_blueprint_versions|`task_blueprint_versions.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_target_exemplars_version` on `blueprint_version_id`.
- `sqlite_autoindex_target_exemplars_2` on `blueprint_version_id`, `exemplar_ref` (unique).
- `sqlite_autoindex_target_exemplars_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.register_task_blueprint_version()`
- `Repository.target_exemplars_for()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/task_blueprints.py`
- `src/learnloop_sidecar/handlers/ladder.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_task_blueprints.py`

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
CREATE TABLE target_exemplars (
  id TEXT PRIMARY KEY,
  blueprint_version_id TEXT NOT NULL
    REFERENCES task_blueprint_versions(id) ON DELETE CASCADE,
  exemplar_ref TEXT NOT NULL,
  weight REAL NOT NULL DEFAULT 1.0,
  exposure_status TEXT NOT NULL DEFAULT 'familiar_anchor'
    CHECK (exposure_status IN ('familiar_anchor', 'unseen_sibling')),
  held_out_weight REAL NOT NULL DEFAULT 0.0
    CHECK (held_out_weight = 0.0 OR exposure_status = 'unseen_sibling'),
  created_at TEXT NOT NULL,
  UNIQUE(blueprint_version_id, exemplar_ref)
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
