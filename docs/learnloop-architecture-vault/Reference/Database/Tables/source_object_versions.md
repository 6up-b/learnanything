---
title: "source_object_versions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite source_object_versions"
  - "table source_object_versions"
schema_head: 157
table_name: "source_object_versions"
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

# `source_object_versions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins immutable versions of source object so canonical-source work can be retried without losing provenance or silently changing its input set. It supplies replay-stable input rather than a disposable cache. Rows bind `source_object_id`, `revision_id`, `object_type`, making the operational relationship explicit. ^table-purpose

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
| `version_ordinal` | `INTEGER` | yes | — | — | Stored value |
| `revision_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `object_type` | `TEXT` | yes | — | — | Stored value |
| `authorial_role` | `TEXT` | no | — | — | Stored value |
| `salience_proposal` | `REAL` | no | — | — | Stored value |
| `exact_text` | `TEXT` | yes | `''` | — | Stored value |
| `content_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `authorship` | `TEXT` | yes | `'ai'` | — | Stored value |
| `model_provenance_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | `'proposed'` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `source_object_id` → [[Reference/Database/Tables/source_objects|`source_objects.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_source_object_versions_revision` on `revision_id`.
- `idx_source_object_versions_obj` on `source_object_id`, `version_ordinal`.
- `sqlite_autoindex_source_object_versions_2` on `source_object_id`, `version_ordinal` (unique).
- `sqlite_autoindex_source_object_versions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.append_source_object_version()`
- `Repository.delete_source_artifact()`
- `Repository.source_object_head()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/reader/source_objects.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_source_objects.py`

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
CREATE TABLE source_object_versions (
  id TEXT PRIMARY KEY,
  source_object_id TEXT NOT NULL REFERENCES source_objects(id),
  version_ordinal INTEGER NOT NULL,
  revision_id TEXT NOT NULL,
  object_type TEXT NOT NULL
    CHECK (object_type IN ('claim', 'definition', 'procedure', 'worked_example',
                           'problem', 'proof_move', 'motif_or_passage', 'artifact')),
  authorial_role TEXT,
  salience_proposal REAL,
  exact_text TEXT NOT NULL DEFAULT '',
  content_json TEXT NOT NULL DEFAULT '{}',
  authorship TEXT NOT NULL DEFAULT 'ai'
    CHECK (authorship IN ('learner', 'ai', 'expert', 'author')),
  model_provenance_json TEXT,
  status TEXT NOT NULL DEFAULT 'proposed'
    CHECK (status IN ('proposed', 'reviewed', 'rejected', 'superseded')),
  created_at TEXT NOT NULL,
  UNIQUE(source_object_id, version_ordinal)
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
