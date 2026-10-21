---
title: "hypothesis_recurrence_review"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "3092f6161aaa654ac0081fad52bf7ee52020ee2c"
source_commit_timestamp: "2026-10-21T00:06:21-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite hypothesis_recurrence_review"
  - "table hypothesis_recurrence_review"
schema_head: 216
table_name: "hypothesis_recurrence_review"
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
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `hypothesis_recurrence_review`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives hypothesis recurrence review a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `case_kind`, `builder_version`, `left_ref`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Cases for review, rebuilt with the groups: refused unions (the no-chaining rule), different verdicts inside one exact-statement class, attempt-level links that name no single statement class, and diagnoses whose registry match differs from the top-1 registry neighbour by embedding (§3.5).

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
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `case_kind` | `TEXT` | yes | — | — | Stored value |
| `left_ref` | `TEXT` | no | — | — | Stored value |
| `right_ref` | `TEXT` | no | — | — | Stored value |
| `blocking_left_ref` | `TEXT` | no | — | — | Stored value |
| `blocking_right_ref` | `TEXT` | no | — | — | Stored value |
| `source_ref` | `TEXT` | no | — | — | Stored value |
| `occurred_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `detail_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `builder_version` | `TEXT` | yes | — | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `hypothesis_recurrence_review_kind` on `case_kind`, `occurred_at`.
- `sqlite_autoindex_hypothesis_recurrence_review_1` on `id` (unique).

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
CREATE TABLE hypothesis_recurrence_review (
  id TEXT PRIMARY KEY,
  case_kind TEXT NOT NULL CHECK (
    case_kind IN ('refused_union', 'exact_key_conflict', 'unresolved_link', 'registry_disagreement')
  ),
  left_ref TEXT,
  right_ref TEXT,
  blocking_left_ref TEXT,
  blocking_right_ref TEXT,
  source_ref TEXT,
  occurred_at TEXT,
  detail_json TEXT NOT NULL DEFAULT '{}',
  builder_version TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
