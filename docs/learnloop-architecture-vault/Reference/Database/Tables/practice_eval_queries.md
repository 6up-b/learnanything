---
title: "practice_eval_queries"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "ee3115d5879761a347e6e0fa2d57e889fd0d46ac"
source_commit_timestamp: "2026-10-13T10:46:27-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite practice_eval_queries"
  - "table practice_eval_queries"
schema_head: 192
table_name: "practice_eval_queries"
table_role: "workflow"
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
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `practice_eval_queries`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives practice eval querie a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `seed_id`, `model_id`, `run_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> The persisted held-out retrieval query set. LLM-written queries are paid outputs; logged queries copy real find_practice requests. Never regenerated.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/169_practice_index.sql`.
- **Schema touched by:** `169_practice_index.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `query_text` | `TEXT` | yes | — | — | Stored value |
| `seed_kind` | `TEXT` | yes | — | — | Stored value |
| `seed_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `model_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `prompt_version` | `TEXT` | yes | — | — | Stored value |
| `input_hash` | `TEXT` | yes | — | — | Stored value |
| `run_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_practice_eval_queries_2` on `prompt_version`, `seed_kind`, `seed_id` (unique).
- `sqlite_autoindex_practice_eval_queries_1` on `id` (unique).

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
CREATE TABLE practice_eval_queries (
    id TEXT PRIMARY KEY,
    query_text TEXT NOT NULL CHECK(length(trim(query_text)) > 0),
    seed_kind TEXT NOT NULL CHECK(seed_kind IN ('facet', 'item', 'logged')),
    seed_id TEXT NOT NULL,
    model_id TEXT,
    prompt_version TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    run_id TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(prompt_version, seed_kind, seed_id)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
