---
title: "outcome_schema_versions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite outcome_schema_versions"
  - "table outcome_schema_versions"
schema_head: 157
table_name: "outcome_schema_versions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "066_grader_channel.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/066_grader_channel.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/attempts/grade_resolution.py"
  - "src/learnloop/attempts/grader_calibration.py"
  - "src/learnloop/attempts/outcome_schemas.py"
  - "src/learnloop/substrate/canonical_projection.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `outcome_schema_versions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins immutable versions of outcome schema so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `schema_id`, `content_hash`, `version`, making the operational relationship explicit. ^table-purpose

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/066_grader_channel.sql`.
- **Schema touched by:** `066_grader_channel.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `schema_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/outcome_schemas\|outcome_schemas.id]] | Stored value |
| `version` | `INTEGER` | yes | — | — | Stored value |
| `observed_classes_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `true_classes_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `has_signature_error` | `INTEGER` | yes | `0` | — | Stored value |
| `has_unanswered` | `INTEGER` | yes | `0` | — | Stored value |
| `score_fraction_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `schema_id` → [[Reference/Database/Tables/outcome_schemas|`outcome_schemas.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_outcome_schema_versions_schema` on `schema_id`.
- `sqlite_autoindex_outcome_schema_versions_3` on `schema_id`, `content_hash` (unique).
- `sqlite_autoindex_outcome_schema_versions_2` on `schema_id`, `version` (unique).
- `sqlite_autoindex_outcome_schema_versions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.ensure_outcome_schema_version()`
- `Repository.fetch_outcome_schema_version()`
- `Repository.fetch_outcome_schema_version_by_id()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/grade_resolution.py`
- `src/learnloop/attempts/grader_calibration.py`
- `src/learnloop/attempts/outcome_schemas.py`
- `src/learnloop/substrate/canonical_projection.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_grade_resolution_pipeline.py`
- `tests/test_event_sufficiency.py`
- `tests/test_observation_ledger_bulk.py`

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
CREATE TABLE outcome_schema_versions (
  id TEXT PRIMARY KEY,
  schema_id TEXT NOT NULL REFERENCES outcome_schemas(id) ON DELETE CASCADE,
  version INTEGER NOT NULL CHECK (version >= 1),
  observed_classes_json TEXT NOT NULL,   -- ordered G alphabet
  true_classes_json TEXT NOT NULL,       -- Z alphabet (3 or 4 classes)
  has_signature_error INTEGER NOT NULL DEFAULT 0 CHECK (has_signature_error IN (0,1)),
  has_unanswered INTEGER NOT NULL DEFAULT 0 CHECK (has_unanswered IN (0,1)),
  score_fraction_json TEXT NOT NULL,     -- {class: fraction in [0,1]}
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(schema_id, version),
  UNIQUE(schema_id, content_hash)
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
