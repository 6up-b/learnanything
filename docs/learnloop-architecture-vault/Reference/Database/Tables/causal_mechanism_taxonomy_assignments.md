---
title: "causal_mechanism_taxonomy_assignments"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite causal_mechanism_taxonomy_assignments"
  - "table causal_mechanism_taxonomy_assignments"
schema_head: 157
table_name: "causal_mechanism_taxonomy_assignments"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "119_causal_mechanism_taxonomy.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/119_causal_mechanism_taxonomy.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `causal_mechanism_taxonomy_assignments`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records governed assignments for causal mechanism taxonomy so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `taxonomy_version_id`, `hypothesis_id`, `mechanism_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/119_causal_mechanism_taxonomy.sql`.
- **Schema touched by:** `119_causal_mechanism_taxonomy.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `taxonomy_version_id` | `TEXT` | yes | — | PRIMARY KEY; FK → [[Reference/Database/Tables/causal_mechanism_taxonomy_versions\|causal_mechanism_taxonomy_versions.id]] | Stored value |
| `hypothesis_id` | `TEXT` | yes | — | PRIMARY KEY; FK → [[Reference/Database/Tables/causal_hypotheses\|causal_hypotheses.id]] | Stored value |
| `mechanism_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `hypothesis_id` → [[Reference/Database/Tables/causal_hypotheses|`causal_hypotheses.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `taxonomy_version_id` → [[Reference/Database/Tables/causal_mechanism_taxonomy_versions|`causal_mechanism_taxonomy_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_causal_mechanism_assignment_hypothesis` on `hypothesis_id`, `taxonomy_version_id`.
- `sqlite_autoindex_causal_mechanism_taxonomy_assignments_1` on `taxonomy_version_id`, `hypothesis_id` (unique).

Database triggers:

- `causal_mechanism_taxonomy_assignments_no_delete` — schema-enforced lifecycle or immutability constraint.
- `causal_mechanism_taxonomy_assignments_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.causal_mechanism_assignment()`
- `Repository.causal_mechanism_taxonomy_version()`
- `Repository.insert_causal_mechanism_taxonomy_version()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_attribution.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_attribution_p1.py`

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
CREATE TABLE causal_mechanism_taxonomy_assignments (
  taxonomy_version_id TEXT NOT NULL
    REFERENCES causal_mechanism_taxonomy_versions(id),
  hypothesis_id TEXT NOT NULL REFERENCES causal_hypotheses(id),
  mechanism_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (taxonomy_version_id, hypothesis_id)
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
