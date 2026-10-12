---
title: "practice_index_evaluations"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "5a9a9e3d31c99bb1d5aa65b1d5235509915ed81e"
source_commit_timestamp: "2026-10-12T17:19:24-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite practice_index_evaluations"
  - "table practice_index_evaluations"
schema_head: 176
table_name: "practice_index_evaluations"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "169_practice_index.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/169_practice_index.sql"
  - "src/learnloop/db/stores/practice_index.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `practice_index_evaluations`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives practice index evaluation a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `run_id`, `manifest_hash`, `winner`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Aggregate result of each retrieval evaluation and the path it chose. find_practice in retrieval_path = "auto" reads the latest row whose manifest matches the current index.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/169_practice_index.sql`.
- **Schema touched by:** `169_practice_index.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `winner` | `TEXT` | yes | — | — | Stored value |
| `reason` | `TEXT` | yes | — | — | Stored value |
| `manifest_hash` | `TEXT` | yes | — | — | Stored value |
| `manifest_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `metrics_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `run_id` | `TEXT` | yes | — | — | Application-validated soft reference |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `practice_index_evaluations_manifest` on `manifest_hash`, `created_at`.
- `sqlite_autoindex_practice_index_evaluations_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/practice_index.py`

### Direct SQL writers

- `src/learnloop/db/stores/practice_index.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_practice_index_evaluation.py`

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
CREATE TABLE practice_index_evaluations (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    winner TEXT NOT NULL CHECK(winner IN ('dossier', 'direct')),
    reason TEXT NOT NULL,
    manifest_hash TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    run_id TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
