---
title: "family_memory_state"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "15789eb84e96d9c3185b408585b3aea5537634f1"
source_commit_timestamp: "2026-10-17T22:04:32-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite family_memory_state"
  - "table family_memory_state"
schema_head: 209
table_name: "family_memory_state"
table_role: "derived"
functionality_status: "active"
domain_family: "operations"
introduced_in: "168_activity_family_membership.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/168_activity_family_membership.sql"
  - "src/learnloop/field/memory.py"
  - "src/learnloop/substrate/family_memory.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `family_memory_state`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Maintains the decision-facing current projection for family memory so maintenance and optional operational work remains inspectable without becoming learner-state authority. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `family_id`, `projection_version`, `weights_hash`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/168_activity_family_membership.sql`.
- **Schema touched by:** `168_activity_family_membership.sql`.
- **Rebuild owner:** `family_memory`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `family_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/activity_families\|activity_families.id]] | Stored value |
| `difficulty` | `REAL` | yes | — | — | Stored value |
| `stability` | `REAL` | yes | — | — | Stored value |
| `retrievability` | `REAL` | yes | — | — | Stored value |
| `last_review_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `review_count` | `INTEGER` | yes | — | — | Stored value |
| `weights_hash` | `TEXT` | yes | — | — | Stored value |
| `projection_version` | `TEXT` | yes | — | — | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `family_id` → [[Reference/Database/Tables/activity_families|`activity_families.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_family_memory_state_1` on `family_id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/substrate/family_memory.py`

### Direct SQL writers

- `src/learnloop/substrate/family_memory.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_family_memory_projection.py`
- `tests/test_rebuild_orchestrator.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.
5. Update the single owner in `DERIVED_STATE_REPLAYERS`, then prove same-version rebuild equivalence and shadow isolation.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE TABLE family_memory_state (
  family_id TEXT PRIMARY KEY REFERENCES activity_families(id),
  difficulty REAL NOT NULL,
  stability REAL NOT NULL,
  retrievability REAL NOT NULL,
  last_review_at TEXT NOT NULL,
  review_count INTEGER NOT NULL CHECK(review_count > 0),
  weights_hash TEXT NOT NULL,
  projection_version TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
