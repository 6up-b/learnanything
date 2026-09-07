---
title: "depth_edge_templates"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite depth_edge_templates"
  - "table depth_edge_templates"
schema_head: 157
table_name: "depth_edge_templates"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "107_depth_edge_templates.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/107_depth_edge_templates.sql"
  - "src/learnloop/cli/depth.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/curriculum/depth_edge_authoring.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `depth_edge_templates`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Versions reusable definitions that generate or validate depth edge so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It supplies replay-stable input rather than a disposable cache. Rows bind `template_slug`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Depth-edge authoring (the P1 curated-edge half, spec v2 §depth / spec_p1 §3.1.1). Owner-curated reusable edge TEMPLATES; LLM-authored concrete edge INSTANCES admitted by deterministic gates and pinned into an immutable envelope version. The instances table is a proposal lifecycle ONLY — authorized edges live exclusively in depth_envelope_versions.reviewed_edges_json; nothing reads authorization from here.

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
| `template_slug` | `TEXT` | yes | — | — | Stored value |
| `domain_scope_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_depth_edge_templates_2` on `template_slug` (unique).
- `sqlite_autoindex_depth_edge_templates_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.depth_edge_template_by_slug()`
- `Repository.depth_edge_templates()`
- `Repository.insert_depth_edge_template()`

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
CREATE TABLE depth_edge_templates (
  id TEXT PRIMARY KEY,
  template_slug TEXT NOT NULL UNIQUE,
  domain_scope_json TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
