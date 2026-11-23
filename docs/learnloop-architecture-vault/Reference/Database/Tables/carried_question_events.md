---
title: "carried_question_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite carried_question_events"
  - "table carried_question_events"
table_name: "carried_question_events"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "266_reader_workbench_pads.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/266_reader_workbench_pads.sql"
  - "src/learnloop/db/stores/pad_ledgers.py"
  - "src/learnloop/db/stores/pad_reads.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `carried_question_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of carried question so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `event_id`, `carried_id`, `event`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/266_reader_workbench_pads.sql`.
- **Schema touched by:** `266_reader_workbench_pads.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `event_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `carried_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/carried_questions\|carried_questions.carried_id]] | Stored value |
| `event` | `TEXT` | yes | — | — | Stored value |
| `ref` | `TEXT` | no | — | — | Stored value |
| `at` | `TEXT` | yes | — | — | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `carried_id` → [[Reference/Database/Tables/carried_questions|`carried_questions.carried_id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_carried_question_events_carried` on `carried_id`, `at`.
- `sqlite_autoindex_carried_question_events_1` on `event_id` (unique).

Database triggers:

- `carried_question_events_no_delete` — schema-enforced lifecycle or immutability constraint.
- `carried_question_events_no_replace` — schema-enforced lifecycle or immutability constraint.
- `carried_question_events_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/pad_reads.py`

### Direct SQL writers

- `src/learnloop/db/stores/pad_ledgers.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/reader_rd4_migration_helpers.py`
- `tests/test_reader_rd4_carried_and_proposals.py`
- `tests/test_reader_rd4_migration.py`

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
CREATE TABLE carried_question_events (
  event_id TEXT PRIMARY KEY,
  carried_id TEXT NOT NULL REFERENCES carried_questions(carried_id),
  event TEXT NOT NULL CHECK (event IN ('carried', 'surfaced', 'fruitful', 'not_now', 'let_go', 'ignored')),
  ref TEXT,
  at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
