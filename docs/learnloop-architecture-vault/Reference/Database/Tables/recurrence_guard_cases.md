---
title: "recurrence_guard_cases"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "5a6eeb542d922d9dd9b95b45a6400a744fd420d5"
source_commit_timestamp: "2026-10-13T05:32:43-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite recurrence_guard_cases"
  - "table recurrence_guard_cases"
schema_head: 188
table_name: "recurrence_guard_cases"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "176_recurrence_groups.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/176_recurrence_groups.sql"
  - "src/learnloop/db/stores/recurrence.py"
  - "src/learnloop/diagnosis/recurrence/guard.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `recurrence_guard_cases`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives recurrence guard case a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `case_id`, `suite_version`, `expected`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> The same-answer/different-cause guard's planted cases beyond the built-in suite (an M1 run's cases added with `recurrence guard --from-run`). Once registered, a case is required: the switch to mvp-0.12 needs a verdict on every registered negative from the configured judge (§3.6). Append-only.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/176_recurrence_groups.sql`.
- **Schema touched by:** `176_recurrence_groups.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `case_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `suite_version` | `TEXT` | yes | — | — | Stored value |
| `expected` | `TEXT` | yes | — | — | Stored value |
| `topic` | `TEXT` | yes | `''` | — | Stored value |
| `problem` | `TEXT` | yes | `''` | — | Stored value |
| `shared_answer` | `TEXT` | no | — | — | Stored value |
| `statement_a` | `TEXT` | yes | — | — | Stored value |
| `statement_b` | `TEXT` | yes | — | — | Stored value |
| `quote_a` | `TEXT` | no | — | — | Stored value |
| `quote_b` | `TEXT` | no | — | — | Stored value |
| `source` | `TEXT` | yes | — | — | Stored value |
| `registered_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_recurrence_guard_cases_1` on `case_id` (unique).

Database triggers:

- `recurrence_guard_cases_no_delete` — schema-enforced lifecycle or immutability constraint.
- `recurrence_guard_cases_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/recurrence.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

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
CREATE TABLE recurrence_guard_cases (
  case_id TEXT PRIMARY KEY,
  suite_version TEXT NOT NULL,
  expected TEXT NOT NULL CHECK (expected IN ('same', 'different')),
  topic TEXT NOT NULL DEFAULT '',
  problem TEXT NOT NULL DEFAULT '',
  shared_answer TEXT,
  statement_a TEXT NOT NULL,
  statement_b TEXT NOT NULL,
  quote_a TEXT,
  quote_b TEXT,
  source TEXT NOT NULL,
  registered_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
