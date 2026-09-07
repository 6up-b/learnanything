---
title: "scheduler_offer_receipts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "0395ae32f9e2e40d1cb98b38402631299a94003f"
source_commit_timestamp: "2026-09-07T12:49:13-04:00"
last_verified: "2026-09-07"
aliases:
  - "state.sqlite scheduler_offer_receipts"
  - "table scheduler_offer_receipts"
schema_head: 163
table_name: "scheduler_offer_receipts"
table_role: "receipt"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "161_collection_contract.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/161_collection_contract.sql"
  - "src/learnloop/db/stores/collection.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `scheduler_offer_receipts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Freezes the ordered candidates returned after adapter filtering so later queue refreshes cannot rewrite an earlier offer. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `slate_id`, `collection_version`, `entry_surface`, making the operational relationship explicit. ^table-purpose

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/161_collection_contract.sql`.
- **Schema touched by:** `161_collection_contract.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `slate_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/scheduler_slates\|scheduler_slates.id]] | Stored value |
| `returned_candidate_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `entry_surface` | `TEXT` | yes | — | — | Stored value |
| `collection_version` | `TEXT` | yes | `'learnloop-events-v1'` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `slate_id` → [[Reference/Database/Tables/scheduler_slates|`scheduler_slates.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_scheduler_offer_receipts_1` on `slate_id` (unique).

Database triggers:

- `scheduler_offer_receipts_immutable_delete` — schema-enforced lifecycle or immutability constraint.
- `scheduler_offer_receipts_immutable_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/collection.py`

### Direct SQL writers

- `src/learnloop/db/stores/collection.py`

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
CREATE TABLE scheduler_offer_receipts (
  slate_id TEXT PRIMARY KEY REFERENCES scheduler_slates(id),
  returned_candidate_ids_json TEXT NOT NULL,
  entry_surface TEXT NOT NULL,
  collection_version TEXT NOT NULL DEFAULT 'learnloop-events-v1',
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
