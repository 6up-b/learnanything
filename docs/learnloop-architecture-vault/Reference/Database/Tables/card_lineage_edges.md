---
title: "card_lineage_edges"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite card_lineage_edges"
  - "table card_lineage_edges"
schema_head: 157
table_name: "card_lineage_edges"
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
  - "src/learnloop/substrate/compat/substrate_cutover.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `card_lineage_edges`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives card lineage edge a stable database identity so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It supplies replay-stable input rather than a disposable cache. Rows bind `lineage_id`, `from_card_version_id`, `to_card_version_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/075_card_lineage_state.sql`.
- **Schema touched by:** `075_card_lineage_state.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `lineage_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/card_lineages\|card_lineages.id]] | Stored value |
| `from_card_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_card_versions\|activity_card_versions.id]] | Stored value |
| `to_card_version_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_card_versions\|activity_card_versions.id]] | Stored value |
| `edge_kind` | `TEXT` | yes | — | — | Stored value |
| `classifier_version` | `TEXT` | yes | — | — | Stored value |
| `rationale_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `to_card_version_id` → [[Reference/Database/Tables/activity_card_versions|`activity_card_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `from_card_version_id` → [[Reference/Database/Tables/activity_card_versions|`activity_card_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `lineage_id` → [[Reference/Database/Tables/card_lineages|`card_lineages.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_cle_to_version` on `to_card_version_id`.
- `idx_cle_lineage` on `lineage_id`, `created_at`.
- `sqlite_autoindex_card_lineage_edges_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.append_card_lineage_edge()`
- `Repository.card_lineage_edges()`
- `Repository.lineage_for_card_version()`
- `Repository.record_depth_transition_atomic()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/depth_transition.py`
- `src/learnloop/substrate/card_lineage.py`
- `src/learnloop/substrate/compat/substrate_cutover.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_card_lineage.py`

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
CREATE TABLE card_lineage_edges (
  id TEXT PRIMARY KEY,
  lineage_id TEXT NOT NULL REFERENCES card_lineages(id) ON DELETE CASCADE,
  -- NULL from_ for the lineage's genesis version.
  from_card_version_id TEXT REFERENCES activity_card_versions(id),
  to_card_version_id TEXT NOT NULL REFERENCES activity_card_versions(id),
  edge_kind TEXT NOT NULL CHECK (edge_kind IN (
    'minor_successor', 'semantic_fork', 'split_from', 'merged_from')),
  classifier_version TEXT NOT NULL,
  rationale_json TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
