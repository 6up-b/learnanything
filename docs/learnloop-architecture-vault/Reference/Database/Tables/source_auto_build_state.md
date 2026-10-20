---
title: "source_auto_build_state"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "f9acffb687dbd37ff7718342a3d8213d3f562b9a"
source_commit_timestamp: "2026-10-19T21:42:29-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite source_auto_build_state"
  - "table source_auto_build_state"
schema_head: 213
table_name: "source_auto_build_state"
table_role: "workflow"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "198_add_book_state.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/198_add_book_state.sql"
  - "src/learnloop/content/pipeline/add_source.py"
  - "src/learnloop/content/pipeline/jobs.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/sources/source_deletion.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_auto_build_state`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Maintains the decision-facing current projection for source auto build so canonical-source work can be retried without losing provenance or silently changing its input set. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `source_id`, `wanted_extraction_id`, `wanted_section_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> WORKFLOW state for a book's automatic question builds: * generation: advanced by "Undo this book's questions"; a build planned in an older generation never applies (it is cancelled, and a late result stays an unapplied record), so an in-flight build cannot put content back. * wanted_*: the latest reading position a progressive build could not act on yet (work was already running); reconciled when that work finishes, when an AI is connected and when the library opens.

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/198_add_book_state.sql`.
- **Schema touched by:** `198_add_book_state.sql`, `199_reading_request_revision.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `source_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/source_artifacts\|source_artifacts.id]] | Stored value |
| `generation` | `INTEGER` | yes | `0` | — | Stored value |
| `undone_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `wanted_extraction_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `wanted_section_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `wanted_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `wanted_revision` | `INTEGER` | yes | `0` | — | Stored value |
| `wanted_attempts` | `INTEGER` | yes | `0` | — | Stored value |
| `wanted_retry_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `source_id` → [[Reference/Database/Tables/source_artifacts|`source_artifacts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_source_auto_build_state_1` on `source_id` (unique).

## Who calls it

### Repository access surface

- `Repository._reading_request()`
- `Repository._record_reading_request_for_extraction()`
- `Repository.advance_source_auto_build_generation()`
- `Repository.defer_reading_request()`
- `Repository.delete_source_artifact()`
- `Repository.fail_reading_request()`
- `Repository.pending_reading_request()`
- `Repository.pending_reading_requests()`
- `Repository.reading_request_unsettled()`
- `Repository.record_reading_request()`
- `Repository.settle_reading_request()`
- `Repository.source_auto_build_state()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/pipeline/add_source.py`
- `src/learnloop/content/pipeline/jobs.py`
- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/db/repositories.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_reading_request_sweep.py`
- `tests/test_ux_phase1_finish.py`
- `tests/test_ux_phase1_review_fixes.py`
- `tests/test_ux_phase1_round2_rereview.py`
- `tests/test_ad1_reading_opportunities.py`
- `tests/test_reading_hardening_review_fixes.py`
- `tests/test_reading_hardening_verify_fixes.py`

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
CREATE TABLE source_auto_build_state (
  source_id TEXT PRIMARY KEY REFERENCES source_artifacts(id),
  generation INTEGER NOT NULL DEFAULT 0 CHECK (generation >= 0),
  undone_at TEXT,
  wanted_extraction_id TEXT,
  wanted_section_id TEXT,
  wanted_at TEXT,
  updated_at TEXT NOT NULL, wanted_revision INTEGER NOT NULL DEFAULT 0 CHECK (wanted_revision >= 0), wanted_attempts INTEGER NOT NULL DEFAULT 0 CHECK (wanted_attempts >= 0), wanted_retry_at TEXT,
  CHECK ((wanted_section_id IS NULL) = (wanted_extraction_id IS NULL))
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
