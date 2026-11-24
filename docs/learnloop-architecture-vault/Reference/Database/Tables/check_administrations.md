---
title: "check_administrations"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite check_administrations"
  - "table check_administrations"
table_name: "check_administrations"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "270_reader_workbench_inline_checks.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/270_reader_workbench_inline_checks.sql"
  - "src/learnloop/db/stores/check_administrations.py"
  - "src/learnloop/intent/inline_administration.py"
  - "src/learnloop/scheduling/intent/serving.py"
  - "src/learnloop_sidecar/check_hold.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `check_administrations`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives check administration a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `request_id`, `commitment_id`, `session_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/270_reader_workbench_inline_checks.sql`.
- **Schema touched by:** `270_reader_workbench_inline_checks.sql`, `271_reader_workbench_inline_checks_fix.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `administration_token` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `request_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `commitment_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `surface` | `TEXT` | yes | — | — | Stored value |
| `session_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `contract_hash` | `TEXT` | no | — | — | Stored value |
| `cold` | `INTEGER` | yes | — | — | Stored value |
| `state` | `TEXT` | yes | — | — | Stored value |
| `protection_method` | `TEXT` | yes | — | — | Stored value |
| `exposure_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `submission_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `opened_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `closed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `candidates_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `presentation_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `pending_before` | `INTEGER` | no | — | — | Stored value |
| `outcome_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `exposure_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_check_administrations_commitment` on `commitment_id`, `opened_at`.
- `idx_check_administrations_one_open` on expression/partial index (unique).
- `sqlite_autoindex_check_administrations_3` on `submission_id` (unique).
- `sqlite_autoindex_check_administrations_2` on `request_id` (unique).
- `sqlite_autoindex_check_administrations_1` on `administration_token` (unique).

Database triggers:

- `check_administrations_closed_final` — schema-enforced lifecycle or immutability constraint.
- `check_administrations_kept` — schema-enforced lifecycle or immutability constraint.
- `check_administrations_no_replace` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/check_administrations.py`

### Direct SQL writers

- `src/learnloop/db/stores/check_administrations.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/reader_rd7a_migration_helpers.py`
- `tests/test_architecture.py`
- `tests/test_reader_rd7_fix_migration.py`
- `tests/test_reader_rd7a_inline_checks.py`
- `tests/test_reader_rd7a_migration.py`

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
CREATE TABLE check_administrations (
  administration_token TEXT PRIMARY KEY,
  request_id TEXT NOT NULL UNIQUE,
  commitment_id TEXT NOT NULL,
  surface TEXT NOT NULL CHECK (surface IN ('reader_inline')),
  session_id TEXT NOT NULL,
  practice_item_id TEXT NOT NULL,
  contract_hash TEXT,
  cold INTEGER NOT NULL CHECK (cold IN (0, 1)),
  state TEXT NOT NULL CHECK (state IN ('open', 'submitted', 'abandoned', 'superseded')),
  protection_method TEXT NOT NULL,
  exposure_json TEXT NOT NULL DEFAULT '[]',
  submission_id TEXT UNIQUE,
  attempt_id TEXT,
  opened_at TEXT NOT NULL,
  closed_at TEXT, candidates_json TEXT NOT NULL DEFAULT '[]', presentation_json TEXT, pending_before INTEGER CHECK (pending_before IS NULL OR pending_before IN (0, 1)), outcome_json TEXT, exposure_ids_json TEXT NOT NULL DEFAULT '[]',
  CHECK ((state = 'open') = (closed_at IS NULL)),
  CHECK (state != 'submitted' OR (submission_id IS NOT NULL AND attempt_id IS NOT NULL))
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
