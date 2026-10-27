---
title: "session_handoffs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "0843991f2b18f27dbcfa32509c74e214a072eab8"
source_commit_timestamp: "2026-10-27T17:51:02-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite session_handoffs"
  - "table session_handoffs"
schema_head: 226
table_name: "session_handoffs"
table_role: "receipt"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "226_session_ownership.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/226_session_ownership.sql"
  - "src/learnloop/db/stores/session_ownership.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `session_handoffs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives session handoff a stable database identity so queue and controller decisions can resume safely and explain why an activity was selected. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `session_id`, `from_device_id`, `to_device_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/226_session_ownership.sql`.
- **Schema touched by:** `226_session_ownership.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `session_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/sessions\|sessions.id]] | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `from_device_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `to_device_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `generation` | `INTEGER` | yes | — | — | Stored value |
| `checkpoint_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `at` | `TEXT` | yes | — | — | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `session_id` → [[Reference/Database/Tables/sessions|`sessions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_session_handoffs_session` on `session_id`, `at`, `id`.
- `sqlite_autoindex_session_handoffs_1` on `id` (unique).

Database triggers:

- `session_handoffs_no_delete` — schema-enforced lifecycle or immutability constraint.
- `session_handoffs_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/session_ownership.py`

### Direct SQL writers

- `src/learnloop/db/stores/session_ownership.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_architecture.py`
- `tests/test_session_ownership.py`
- `tests/test_session_ownership_migration.py`

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
CREATE TABLE session_handoffs (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id),
  kind TEXT NOT NULL CHECK (kind IN ('adopt', 'replace')),
  from_device_id TEXT,
  to_device_id TEXT,
  generation INTEGER NOT NULL CHECK (generation >= 0),
  checkpoint_json TEXT,
  at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
