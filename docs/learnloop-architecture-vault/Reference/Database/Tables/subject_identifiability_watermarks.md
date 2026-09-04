---
title: "subject_identifiability_watermarks"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite subject_identifiability_watermarks"
  - "table subject_identifiability_watermarks"
schema_head: 157
table_name: "subject_identifiability_watermarks"
table_role: "derived"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "050_capability_residual_and_identifiability.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/050_capability_residual_and_identifiability.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/ops/doctor.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `subject_identifiability_watermarks`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Materializes whether a subject has enough independent evidence to identify its learner state. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `subject_id`, `registry_hash`, `finding_count`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §11.3 pre-first-practice identifiability doctor watermark. One row per subject records the registry hash last analyzed and how many non-identifiable distinctions were open at that time, so the doctor re-runs graph- identifiability only when a subject's registry changed since the last check (before evidence accrues against unlocked distinctions).

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/050_capability_residual_and_identifiability.sql`.
- **Schema touched by:** `050_capability_residual_and_identifiability.sql`.
- **Rebuild owner:** `identifiability`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `subject_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `registry_hash` | `TEXT` | yes | — | — | Stored value |
| `finding_count` | `INTEGER` | yes | `0` | — | Stored value |
| `checked_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_subject_identifiability_watermarks_1` on `subject_id` (unique).

## Who calls it

### Repository access surface

- `Repository.identifiability_watermark()`
- `Repository.upsert_identifiability_watermark()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/ops/doctor.py`
- `src/learnloop/substrate/rebuild_orchestrator.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_rebuild_orchestrator.py`
- `tests/test_identifiability_doctor.py`

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
CREATE TABLE subject_identifiability_watermarks (
  subject_id TEXT PRIMARY KEY,
  registry_hash TEXT NOT NULL,
  finding_count INTEGER NOT NULL DEFAULT 0,
  checked_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
