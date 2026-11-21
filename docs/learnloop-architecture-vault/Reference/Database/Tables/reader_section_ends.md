---
title: "reader_section_ends"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite reader_section_ends"
  - "table reader_section_ends"
table_name: "reader_section_ends"
table_role: "workflow"
functionality_status: "active"
domain_family: "reader"
introduced_in: "256_reader_seen_spans.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/256_reader_seen_spans.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/db/stores/reader.py"
  - "src/learnloop/reader/seen_passages.py"
  - "src/learnloop_sidecar/handlers/reader.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/reader"
---

# `reader_section_ends`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives reader section end a stable database identity so reader interactions remain anchored to durable source content as extraction and rendering evolve. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `extraction_id`, `section_id`, `span_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **reader** navigation family. The family context lives in [[Database Catalog#Reader]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/256_reader_seen_spans.sql`.
- **Schema touched by:** `256_reader_seen_spans.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `extraction_id` | `TEXT` | yes | — | PRIMARY KEY | Stored value |
| `section_id` | `TEXT` | yes | — | PRIMARY KEY | Stored value |
| `span_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `first_seen_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `origin` | `TEXT` | yes | — | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_reader_section_ends_1` on `extraction_id`, `section_id` (unique).

Database triggers:

- `reader_section_ends_no_delete` — schema-enforced lifecycle or immutability constraint.
- `reader_section_ends_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.reader_section_ends_for()`
- `Repository.upsert_reader_section_progress()`

### Direct SQL readers

- `src/learnloop/db/stores/reader.py`

### Direct SQL writers

- `src/learnloop/db/stores/reader.py`

### Upstream callers of the repository access surface

- `src/learnloop/reader/seen_passages.py`
- `src/learnloop_sidecar/handlers/reader.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/reader_seen_spans_migration_helpers.py`
- `tests/test_reader_seen_passages.py`
- `tests/test_reader_seen_spans_migration.py`
- `tests/ad23_contract_helpers.py`
- `tests/ad_ingest_fakes.py`
- `tests/curriculum_c1_plan_follows_path_helpers.py`
- `tests/reread_safety_helpers.py`
- `tests/test_ad1_reading_opportunities.py`
- `tests/test_curriculum_c1_fix_round2.py`
- `tests/test_curriculum_c1_fix_round3.py`
- `tests/test_daily_plan_reading.py`
- `tests/test_deliverable_path.py`
- `tests/test_figures_prefetch.py`
- `tests/test_first_questions_today.py`
- `tests/test_followups_batch6_prefetch_decided_once.py`
- `tests/test_followups_batch7_prefetch_capped_resume.py`
- `tests/test_plan_follows_path.py`
- `tests/test_reading_paths.py`
- `tests/test_reread_safety.py`
- `tests/test_section_done_before_build.py`

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
CREATE TABLE reader_section_ends (
  extraction_id TEXT NOT NULL,
  section_id TEXT NOT NULL,
  span_id TEXT NOT NULL,
  first_seen_at TEXT NOT NULL,
  origin TEXT NOT NULL CHECK (origin IN ('desktop', 'phone')),
  PRIMARY KEY (extraction_id, section_id)
);
```

## Related notes

- [[Database Catalog#Reader|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
