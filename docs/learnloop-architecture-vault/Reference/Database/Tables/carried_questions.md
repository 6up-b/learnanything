---
title: "carried_questions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite carried_questions"
  - "table carried_questions"
table_name: "carried_questions"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "266_reader_workbench_pads.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/266_reader_workbench_pads.sql"
  - "src/learnloop/db/stores/pad_ledgers.py"
  - "src/learnloop/db/stores/pad_reads.py"
  - "src/learnloop/teacher/brief.py"
  - "src/learnloop/teacher/carried.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `carried_questions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives carried question a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `carried_id`, `desk_id`, `origin_kind`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> A question the learner carries. carried_id is client-minted. origin_kind/origin_ref say where it was carried from (a pad block, a selection or margin note on a passage, the desk drain, or typed); anchor_json is the passage it was carried beside (extraction_id, span_id, anchor-v1), when there is one. state is the latest label: 'carried' and 'not_now' are still carried, 'fruitful' and 'let_go' are not. version counts the labels, so a label names the state it expects.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/266_reader_workbench_pads.sql`.
- **Schema touched by:** `266_reader_workbench_pads.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `carried_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `text` | `TEXT` | yes | — | — | Stored value |
| `origin_kind` | `TEXT` | yes | — | — | Stored value |
| `origin_ref` | `TEXT` | no | — | — | Stored value |
| `anchor_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `desk_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `since` | `TEXT` | yes | — | — | Stored value |
| `state` | `TEXT` | yes | `'carried'` | — | Stored value |
| `version` | `INTEGER` | yes | `1` | — | Stored value |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_carried_questions_state` on `state`, `since`.
- `sqlite_autoindex_carried_questions_1` on `carried_id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/pad_ledgers.py`
- `src/learnloop/db/stores/pad_reads.py`

### Direct SQL writers

- `src/learnloop/db/stores/pad_ledgers.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/identity_pins_helpers.py`
- `tests/reader_rd4_migration_helpers.py`
- `tests/test_reader_rd4_migration.py`
- `tests/test_teacher_carried_questions.py`

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
CREATE TABLE carried_questions (
  carried_id TEXT PRIMARY KEY,
  text TEXT NOT NULL CHECK (length(trim(text)) > 0),
  origin_kind TEXT NOT NULL CHECK (origin_kind IN ('block', 'selection', 'note', 'drain', 'typed')),
  origin_ref TEXT,
  anchor_json TEXT,
  desk_id TEXT,
  since TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'carried' CHECK (state IN ('carried', 'fruitful', 'not_now', 'let_go')),
  version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
