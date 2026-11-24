---
title: "video_chapters"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite video_chapters"
  - "table video_chapters"
table_name: "video_chapters"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "268_reader_workbench_video_chapters.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/268_reader_workbench_video_chapters.sql"
  - "src/learnloop/source_retrieval/follow_along.py"
  - "src/learnloop/source_retrieval/video_chapters.py"
  - "src/learnloop_sidecar/handlers/video.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `video_chapters`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives video chapter a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `chapter_id`, `extraction_id`, `source_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/268_reader_workbench_video_chapters.sql`.
- **Schema touched by:** `268_reader_workbench_video_chapters.sql`, `270_reader_workbench_inline_checks.sql`, `271_reader_workbench_inline_checks_fix.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `chapter_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `extraction_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `source_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `t0` | `REAL` | yes | — | — | Stored value |
| `t1` | `REAL` | yes | — | — | Stored value |
| `title` | `TEXT` | yes | — | — | Stored value |
| `lo_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `state` | `TEXT` | yes | — | — | Stored value |
| `judgment_ref` | `TEXT` | no | — | — | Stored value |
| `suggested_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `decided_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_video_chapters_reading` on `extraction_id`, `t0`.
- `sqlite_autoindex_video_chapters_1` on `chapter_id` (unique).

Database triggers:

- `video_chapters_decide_once` — schema-enforced lifecycle or immutability constraint.
- `video_chapters_keep_decided` — schema-enforced lifecycle or immutability constraint.
- `video_chapters_no_replace_decided` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/source_retrieval/video_chapters.py`

### Direct SQL writers

- `src/learnloop/source_retrieval/video_chapters.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/identity_pins_helpers.py`
- `tests/reader_rd10_migration_helpers.py`
- `tests/test_architecture.py`
- `tests/test_chapters_feed_coverage.py`
- `tests/test_reader_rd10_fix_protection.py`
- `tests/test_reader_rd10_migration.py`
- `tests/test_reader_rd10_video.py`
- `tests/test_reader_rd7_fix_migration.py`
- `tests/test_reader_rd7a_migration.py`
- `tests/test_video_chapters_no_replace.py`

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
CREATE TABLE video_chapters (
  chapter_id TEXT PRIMARY KEY,
  extraction_id TEXT NOT NULL,
  source_id TEXT,
  t0 REAL NOT NULL CHECK (t0 >= 0),
  t1 REAL NOT NULL CHECK (t1 > t0),
  title TEXT NOT NULL CHECK (length(title) >= 1),
  lo_ids_json TEXT NOT NULL DEFAULT '[]',
  state TEXT NOT NULL CHECK (state IN ('suggested', 'accepted', 'dismissed')),
  judgment_ref TEXT,
  suggested_at TEXT NOT NULL,
  decided_at TEXT,
  CHECK ((state = 'suggested') = (decided_at IS NULL))
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
