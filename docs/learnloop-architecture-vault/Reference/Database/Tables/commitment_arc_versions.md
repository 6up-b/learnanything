---
title: "commitment_arc_versions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite commitment_arc_versions"
  - "table commitment_arc_versions"
schema_head: 157
table_name: "commitment_arc_versions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "095_commitment_arcs.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/095_commitment_arcs.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/curriculum/commitment_arcs.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `commitment_arc_versions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins immutable versions of commitment arc so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It supplies replay-stable input rather than a disposable cache. Rows bind `arc_id`, `predecessor_version_id`, `depth_policy_version_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/095_commitment_arcs.sql`.
- **Schema touched by:** `095_commitment_arcs.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `arc_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/commitment_arcs\|commitment_arcs.id]] | Stored value |
| `version_ordinal` | `INTEGER` | yes | — | — | Stored value |
| `predecessor_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/commitment_arc_versions\|commitment_arc_versions.id]] | Stored value |
| `pattern_refs_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `stages_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `depth_policy_version_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `depth_envelope_version_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `stage_milestone_map_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `predecessor_version_id` → [[Reference/Database/Tables/commitment_arc_versions|`commitment_arc_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `arc_id` → [[Reference/Database/Tables/commitment_arcs|`commitment_arcs.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_commitment_arc_versions_arc` on `arc_id`, `version_ordinal`.
- `sqlite_autoindex_commitment_arc_versions_2` on `arc_id`, `version_ordinal` (unique).
- `sqlite_autoindex_commitment_arc_versions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.append_commitment_arc_version()`
- `Repository.commitment_arc_head_version()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/commitment_arcs.py`

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
CREATE TABLE commitment_arc_versions (
  id TEXT PRIMARY KEY,
  arc_id TEXT NOT NULL REFERENCES commitment_arcs(id),
  version_ordinal INTEGER NOT NULL,
  predecessor_version_id TEXT REFERENCES commitment_arc_versions(id),
  -- P1 pattern refs the arc unfolds through.
  pattern_refs_json TEXT NOT NULL DEFAULT '[]',
  -- The ordered conditional stage program (comprehend..transfer..revisit).
  stages_json TEXT NOT NULL DEFAULT '[]',
  -- The pinned P1 depth objects at authoring time (§10.1). An arc never widens
  -- these; a widen requires a confirmed commitment/envelope successor.
  depth_policy_version_id TEXT,
  depth_envelope_version_id TEXT,
  -- stage_slug -> reviewed depth-milestone edge id (§10.1).
  stage_milestone_map_json TEXT NOT NULL DEFAULT '{}',
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(arc_id, version_ordinal)
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
