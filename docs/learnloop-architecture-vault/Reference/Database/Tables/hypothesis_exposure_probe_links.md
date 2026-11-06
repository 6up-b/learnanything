---
title: "hypothesis_exposure_probe_links"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "0394abccde203a1e4bd7d479ffe28c7035d61f2f"
source_commit_timestamp: "2026-11-06T14:55:42-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite hypothesis_exposure_probe_links"
  - "table hypothesis_exposure_probe_links"
schema_head: 249
table_name: "hypothesis_exposure_probe_links"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "242_hypothesis_marks.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/242_hypothesis_marks.sql"
  - "src/learnloop/db/stores/hypothesis_marks.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `hypothesis_exposure_probe_links`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves explicit relationship edges for hypothesis exposure probe so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `exposure_id`, `attempt_id`, `probe_attempt_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/242_hypothesis_marks.sql`.
- **Schema touched by:** `242_hypothesis_marks.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `exposure_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/hypothesis_list_exposures\|hypothesis_list_exposures.id]] | Stored value |
| `attempt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `probe_attempt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `exposure_id` → [[Reference/Database/Tables/hypothesis_list_exposures|`hypothesis_list_exposures.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `hypothesis_exposure_probe_links_attempt` on `attempt_id`, `created_at`, `id`.
- `sqlite_autoindex_hypothesis_exposure_probe_links_2` on `exposure_id`, `probe_attempt_id` (unique).
- `sqlite_autoindex_hypothesis_exposure_probe_links_1` on `id` (unique).

Database triggers:

- `hypothesis_exposure_probe_links_no_delete` — schema-enforced lifecycle or immutability constraint.
- `hypothesis_exposure_probe_links_no_update` — schema-enforced lifecycle or immutability constraint.

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

- `tests/test_hypothesis_marks.py`
- `tests/test_hypothesis_marks_migration.py`

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
CREATE TABLE hypothesis_exposure_probe_links (
  id TEXT PRIMARY KEY,
  exposure_id TEXT NOT NULL REFERENCES hypothesis_list_exposures(id),
  attempt_id TEXT NOT NULL,
  probe_attempt_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (exposure_id, probe_attempt_id)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
