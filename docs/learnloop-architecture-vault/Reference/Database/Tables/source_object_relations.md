---
title: "source_object_relations"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite source_object_relations"
  - "table source_object_relations"
schema_head: 157
table_name: "source_object_relations"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "094_source_objects.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/094_source_objects.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/sources/source_deletion.py"
  - "src/learnloop/reader/source_objects.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_object_relations`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives source object relation a stable database identity so canonical-source work can be retried without losing provenance or silently changing its input set. It supplies replay-stable input rather than a disposable cache. Rows bind `source_object_id`, `related_object_id`, `relation_type`, making the operational relationship explicit. ^table-purpose

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/094_source_objects.sql`.
- **Schema touched by:** `094_source_objects.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `source_object_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/source_objects\|source_objects.id]] | Stored value |
| `related_object_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/source_objects\|source_objects.id]] | Stored value |
| `version_ordinal` | `INTEGER` | yes | `1` | — | Stored value |
| `relation_type` | `TEXT` | yes | — | — | Stored value |
| `learner_text` | `TEXT` | no | — | — | Stored value |
| `authorship` | `TEXT` | yes | `'learner'` | — | Stored value |
| `review_status` | `TEXT` | yes | `'proposed'` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `related_object_id` → [[Reference/Database/Tables/source_objects|`source_objects.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `source_object_id` → [[Reference/Database/Tables/source_objects|`source_objects.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_source_object_relations_obj` on `source_object_id`.
- `sqlite_autoindex_source_object_relations_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.create_source_object_relation()`
- `Repository.delete_source_artifact()`
- `Repository.relations_for_object()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/reader/source_objects.py`

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
CREATE TABLE source_object_relations (
  id TEXT PRIMARY KEY,
  source_object_id TEXT NOT NULL REFERENCES source_objects(id),
  related_object_id TEXT REFERENCES source_objects(id),
  version_ordinal INTEGER NOT NULL DEFAULT 1,
  relation_type TEXT NOT NULL
    CHECK (relation_type IN ('supports', 'contradicts', 'refines',
                             'alternate_definition', 'unresolved', 'learner_connects')),
  learner_text TEXT,
  authorship TEXT NOT NULL DEFAULT 'learner'
    CHECK (authorship IN ('learner', 'ai', 'expert', 'author')),
  review_status TEXT NOT NULL DEFAULT 'proposed'
    CHECK (review_status IN ('proposed', 'reviewed', 'rejected', 'superseded')),
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
