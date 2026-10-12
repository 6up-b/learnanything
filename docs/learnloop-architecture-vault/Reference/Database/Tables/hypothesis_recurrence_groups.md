---
title: "hypothesis_recurrence_groups"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "22023ab4b1ea026ef099fb3cc842034689397276"
source_commit_timestamp: "2026-10-12T12:14:39-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite hypothesis_recurrence_groups"
  - "table hypothesis_recurrence_groups"
schema_head: 171
table_name: "hypothesis_recurrence_groups"
table_role: "derived"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "171_recurrence_groups.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/171_recurrence_groups.sql"
  - "src/learnloop/db/stores/recurrence.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `hypothesis_recurrence_groups`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives hypothesis recurrence group a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `builder_version`, `episode_key`, `statement_normalized`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Slice 2 T1 (M3, spec_embedding_consumers_v1 §3): recurrence with authority.  The three hypothesis_recurrence_* tables are DERIVED: one replayer (substrate.recurrence_groups) clears and rebuilds them from raw ledgers (causal_hypotheses, attempt_diagnoses + their receipts, judgment_ledger, diagnosis_feedback) with no model or embedding call. They are empty unless the mvp-0.11 successor is active and recurrence.enabled is on. Members of MERGED groups only. A statement class that was never merged with another keeps its exact statement_normalized key and has no row here.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/171_recurrence_groups.sql`.
- **Schema touched by:** `171_recurrence_groups.sql`.
- **Rebuild owner:** `recurrence_groups`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `episode_key` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `statement_normalized` | `TEXT` | yes | — | — | Stored value |
| `group_key` | `TEXT` | yes | — | — | Stored value |
| `root_episode_key` | `TEXT` | yes | — | — | Stored value |
| `class_count` | `INTEGER` | yes | — | — | Stored value |
| `joined_by` | `TEXT` | yes | — | — | Stored value |
| `joined_by_ref` | `TEXT` | no | — | — | Stored value |
| `judge` | `TEXT` | no | — | — | Stored value |
| `builder_version` | `TEXT` | yes | — | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `hypothesis_recurrence_groups_statement` on `statement_normalized`.
- `hypothesis_recurrence_groups_key` on `group_key`.
- `sqlite_autoindex_hypothesis_recurrence_groups_1` on `episode_key` (unique).

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
CREATE TABLE hypothesis_recurrence_groups (
  episode_key TEXT PRIMARY KEY,
  statement_normalized TEXT NOT NULL,
  group_key TEXT NOT NULL,
  root_episode_key TEXT NOT NULL,
  class_count INTEGER NOT NULL CHECK (class_count >= 2),
  joined_by TEXT NOT NULL CHECK (joined_by IN ('root', 'exact_key', 'citation', 'judgment')),
  joined_by_ref TEXT,
  judge TEXT,
  builder_version TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
