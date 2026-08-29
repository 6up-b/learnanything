---
title: "task_blueprints"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite task_blueprints"
  - "table task_blueprints"
schema_head: 156
table_name: "task_blueprints"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "081_task_blueprints.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/081_task_blueprints.sql"
  - "src/learnloop/curriculum/golden_path_fixture.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop_sidecar/handlers/golden_path.py"
  - "src/learnloop/curriculum/task_blueprints.py"
  - "src/learnloop/reader/reader_guidance.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `task_blueprints`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives task blueprint a stable database identity so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It supplies replay-stable input rather than a disposable cache. Rows bind `unit_id`, `blueprint_slug`, `source_rev`, making the operational relationship explicit. ^table-purpose

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/081_task_blueprints.sql`.
- **Schema touched by:** `081_task_blueprints.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `blueprint_slug` | `TEXT` | yes | — | — | Stored value |
| `source_rev` | `TEXT` | yes | — | — | Stored value |
| `unit_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `family_key` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_task_blueprints_unit` on `source_rev`, `unit_id`.
- `sqlite_autoindex_task_blueprints_2` on `blueprint_slug` (unique).
- `sqlite_autoindex_task_blueprints_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.ensure_task_blueprint()`
- `Repository.reviewed_reading_question_placements()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/task_blueprints.py`
- `src/learnloop/reader/reader_guidance.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_p2_acceptance.py`
- `tests/test_controller_cutover.py`
- `tests/test_golden_path_assessment.py`
- `tests/test_golden_path_confirm.py`
- `tests/test_golden_path_run.py`
- `tests/test_reader_guidance.py`
- `tests/test_sidecar_golden_path_assessment.py`
- `tests/test_task_blueprints.py`

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
CREATE TABLE task_blueprints (
  id TEXT PRIMARY KEY,
  blueprint_slug TEXT NOT NULL,
  source_rev TEXT NOT NULL,
  unit_id TEXT NOT NULL,
  family_key TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(blueprint_slug)
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
