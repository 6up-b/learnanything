---
title: "depth_edge_template_versions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite depth_edge_template_versions"
  - "table depth_edge_template_versions"
schema_head: 156
table_name: "depth_edge_template_versions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "107_depth_edge_templates.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/107_depth_edge_templates.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/cli/depth.py"
  - "src/learnloop/curriculum/depth_edge_authoring.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `depth_edge_template_versions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins immutable versions of depth edge template so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It supplies replay-stable input rather than a disposable cache. Rows bind `template_id`, `content_hash`, `version`, making the operational relationship explicit. ^table-purpose

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/107_depth_edge_templates.sql`.
- **Schema touched by:** `107_depth_edge_templates.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `template_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/depth_edge_templates\|depth_edge_templates.id]] | Stored value |
| `version` | `INTEGER` | yes | — | — | Stored value |
| `body_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `status` | `TEXT` | yes | `'draft'` | — | Stored value |
| `reviewed_by` | `TEXT` | no | — | — | Stored value |
| `reviewed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `template_id` → [[Reference/Database/Tables/depth_edge_templates|`depth_edge_templates.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_depth_edge_template_versions_3` on `template_id`, `content_hash` (unique).
- `sqlite_autoindex_depth_edge_template_versions_2` on `template_id`, `version` (unique).
- `sqlite_autoindex_depth_edge_template_versions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.depth_edge_template_version()`
- `Repository.depth_edge_template_versions_for()`
- `Repository.insert_depth_edge_template_version()`
- `Repository.review_depth_edge_template_version()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/depth.py`
- `src/learnloop/curriculum/depth_edge_authoring.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

No table-specific test contains the table name or a detected repository method call. The schema/role invariants are still pinned by `tests/test_migrations.py` and `tests/test_table_roles.py`.

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
CREATE TABLE depth_edge_template_versions (
  id TEXT PRIMARY KEY,
  template_id TEXT NOT NULL REFERENCES depth_edge_templates(id),
  version INTEGER NOT NULL,
  -- Structural pattern: allowed capability transitions, per-dimension max step
  -- deltas, exit-gate kind (closed set), fresh-proof kind, burden params,
  -- eligible activity pattern slugs.
  body_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'reviewed', 'retired')),
  reviewed_by TEXT,
  reviewed_at TEXT,
  created_at TEXT NOT NULL,
  UNIQUE (template_id, version),
  UNIQUE (template_id, content_hash)
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
