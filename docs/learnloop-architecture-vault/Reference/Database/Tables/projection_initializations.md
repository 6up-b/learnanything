---
title: "projection_initializations"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite projection_initializations"
  - "table projection_initializations"
table_name: "projection_initializations"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "264_reader_workbench_guards.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/264_reader_workbench_guards.sql"
  - "src/learnloop/db/stores/span_projections.py"
  - "src/learnloop/substrate/passage_spans.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `projection_initializations`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives projection initialization a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `projection`, `sources`, `rows`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/264_reader_workbench_guards.sql`.
- **Schema touched by:** `264_reader_workbench_guards.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `projection` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `sources` | `INTEGER` | yes | — | — | Stored value |
| `rows` | `INTEGER` | yes | — | — | Stored value |
| `initialized_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_projection_initializations_1` on `projection` (unique).

Database triggers:

- `projection_initializations_no_delete` — schema-enforced lifecycle or immutability constraint.
- `projection_initializations_no_replace` — schema-enforced lifecycle or immutability constraint.
- `projection_initializations_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/span_projections.py`

### Direct SQL writers

- `src/learnloop/db/stores/span_projections.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/reader_rd0_guards_migration_helpers.py`
- `tests/test_reader_rd0_guards_migration.py`
- `tests/test_reader_rd0_spans.py`

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
CREATE TABLE projection_initializations (
  projection TEXT PRIMARY KEY CHECK (projection IN ('question_event_spans', 'learner_text_gap_spans')),
  sources INTEGER NOT NULL CHECK (sources >= 0),
  rows INTEGER NOT NULL CHECK (rows >= 0),
  initialized_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
