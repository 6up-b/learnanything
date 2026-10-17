---
title: "hypothesis_recurrence_state"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "bc073330b00047576686a6150238801d1119d365"
source_commit_timestamp: "2026-10-16T22:36:24-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite hypothesis_recurrence_state"
  - "table hypothesis_recurrence_state"
schema_head: 206
table_name: "hypothesis_recurrence_state"
table_role: "derived"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "176_recurrence_groups.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/176_recurrence_groups.sql"
  - "src/learnloop/db/stores/recurrence.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
  - "src/learnloop/substrate/recurrence_groups.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `hypothesis_recurrence_state`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Maintains the decision-facing current projection for hypothesis recurrence so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `builder_version`, `scope`, `input_fingerprint`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> One row (scope 'vault'): the inputs the current groups were built from (a cheap fingerprint lets normalization skip an unchanged rebuild) and counts. active = 1: the groups are in force (the successor is active and recurrence.enabled is on). active = 0: PREPARED by `upgrade --to mvp-0.12` before its config switch; consumers read no group until activation flips it. No row while the successor is off.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/176_recurrence_groups.sql`.
- **Schema touched by:** `176_recurrence_groups.sql`.
- **Rebuild owner:** `recurrence_groups`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `scope` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `input_fingerprint` | `TEXT` | yes | — | — | Stored value |
| `builder_version` | `TEXT` | yes | — | — | Stored value |
| `active` | `INTEGER` | yes | — | — | Stored value |
| `group_count` | `INTEGER` | yes | `0` | — | Stored value |
| `member_count` | `INTEGER` | yes | `0` | — | Stored value |
| `review_count` | `INTEGER` | yes | `0` | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_hypothesis_recurrence_state_1` on `scope` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/recurrence.py`

### Direct SQL writers

- `src/learnloop/db/stores/recurrence.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_rebuild_orchestrator.py`
- `tests/test_recurrence_live.py`

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
CREATE TABLE hypothesis_recurrence_state (
  scope TEXT PRIMARY KEY,
  input_fingerprint TEXT NOT NULL,
  builder_version TEXT NOT NULL,
  active INTEGER NOT NULL CHECK (active IN (0, 1)),
  group_count INTEGER NOT NULL DEFAULT 0,
  member_count INTEGER NOT NULL DEFAULT 0,
  review_count INTEGER NOT NULL DEFAULT 0
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
