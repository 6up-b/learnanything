---
title: "check_veil_sets"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite check_veil_sets"
  - "table check_veil_sets"
table_name: "check_veil_sets"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "270_reader_workbench_inline_checks.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/270_reader_workbench_inline_checks.sql"
  - "src/learnloop/db/stores/check_administrations.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `check_veil_sets`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives check veil set a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `veil_set_id`, `commitment_id`, `administration_token`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/270_reader_workbench_inline_checks.sql`.
- **Schema touched by:** `270_reader_workbench_inline_checks.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `veil_set_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `administration_token` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/check_administrations\|check_administrations.administration_token]] | Stored value |
| `commitment_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `seq` | `INTEGER` | yes | — | — | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `method` | `TEXT` | yes | — | — | Stored value |
| `veiled_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `opened_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `administration_token` → [[Reference/Database/Tables/check_administrations|`check_administrations.administration_token`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_check_veil_sets_2` on `administration_token`, `seq` (unique).
- `sqlite_autoindex_check_veil_sets_1` on `veil_set_id` (unique).

Database triggers:

- `check_veil_sets_no_delete` — schema-enforced lifecycle or immutability constraint.
- `check_veil_sets_no_replace` — schema-enforced lifecycle or immutability constraint.
- `check_veil_sets_no_update` — schema-enforced lifecycle or immutability constraint.

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
CREATE TABLE check_veil_sets (
  veil_set_id TEXT PRIMARY KEY,
  administration_token TEXT NOT NULL REFERENCES check_administrations(administration_token),
  commitment_id TEXT NOT NULL,
  seq INTEGER NOT NULL CHECK (seq >= 1),
  kind TEXT NOT NULL CHECK (kind IN ('begin', 'more', 'close')),
  method TEXT NOT NULL,
  veiled_json TEXT NOT NULL DEFAULT '[]',
  opened_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  UNIQUE (administration_token, seq)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
