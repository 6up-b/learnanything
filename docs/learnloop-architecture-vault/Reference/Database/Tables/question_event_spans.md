---
title: "question_event_spans"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite question_event_spans"
  - "table question_event_spans"
table_name: "question_event_spans"
table_role: "derived"
functionality_status: "active"
domain_family: "tutor-and-remediation"
introduced_in: "262_reader_workbench_foundations.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/262_reader_workbench_foundations.sql"
  - "src/learnloop/companion/history.py"
  - "src/learnloop/db/stores/span_projection_reads.py"
  - "src/learnloop/db/stores/span_projections.py"
  - "src/learnloop/passage_union/union.py"
  - "src/learnloop/substrate/passage_spans.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/tutor-and-remediation"
---

# `question_event_spans`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives question event span a stable database identity so tutor and repair work can be resumed, reviewed, and connected to subsequent evidence. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `question_event_id`, `extraction_id`, `span_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> DERIVED: the passages a tutor exchange is tied to, on the reading it was asked on (aliases are applied when read). role: the learner's selection, a passage the answer cited, or the context it was asked in (an item's source passage). quality: exact_selection | citation | source_context | unanchored; an unanchored row has no passage and keeps only the learning object it is about.

It belongs to the **tutor and remediation** navigation family. The family context lives in [[Database Catalog#Tutor And Remediation]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/262_reader_workbench_foundations.sql`.
- **Schema touched by:** `262_reader_workbench_foundations.sql`, `264_reader_workbench_guards.sql`.
- **Rebuild owner:** `question_event_spans`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `question_event_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `extraction_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `span_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `role` | `TEXT` | yes | — | — | Stored value |
| `quality` | `TEXT` | yes | — | — | Stored value |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_question_event_spans_span` on `extraction_id`, `span_id`.
- `idx_question_event_spans_row` on `question_event_id`, `role` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

None found by exact static reference scan.

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/reader_rd0_migration_helpers.py`
- `tests/test_reader_rd0_guards_migration.py`
- `tests/test_reader_rd0_migration.py`
- `tests/test_reader_rd0_spans.py`
- `tests/test_reader_rd3a_companion_ask.py`
- `tests/test_rebuild_orchestrator.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.
5. Update the single owner in `DERIVED_STATE_REPLAYERS`, then prove same-version rebuild equivalence and shadow isolation.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE TABLE question_event_spans (
  question_event_id TEXT NOT NULL,
  extraction_id TEXT,
  span_id TEXT,
  role TEXT NOT NULL CHECK (role IN ('selection', 'cited', 'context')),
  quality TEXT NOT NULL CHECK (quality IN ('exact_selection', 'citation', 'source_context', 'unanchored')),
  learning_object_id TEXT,
  CHECK ((quality = 'unanchored') = (span_id IS NULL)),
  CHECK ((extraction_id IS NULL) = (span_id IS NULL))
);
```

## Related notes

- [[Database Catalog#Tutor And Remediation|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
