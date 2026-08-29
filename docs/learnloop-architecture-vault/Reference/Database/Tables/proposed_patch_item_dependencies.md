---
title: "proposed_patch_item_dependencies"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite proposed_patch_item_dependencies"
  - "table proposed_patch_item_dependencies"
schema_head: 156
table_name: "proposed_patch_item_dependencies"
table_role: "workflow"
functionality_status: "active"
domain_family: "schema-and-change"
introduced_in: "035_proposal_dependencies.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/035_proposal_dependencies.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/pipeline/source_ingestion.py"
  - "src/learnloop/content/proposals/apply_protocol.py"
  - "src/learnloop/content/proposals/proposals.py"
  - "src/learnloop/content/synthesis/source_append.py"
  - "src/learnloop/content/synthesis/source_set_synthesis.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/schema-and-change"
---

# `proposed_patch_item_dependencies`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Declares prerequisite edges for proposed patch item so schema changes and reviewed mutations remain reproducible and auditable. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `proposed_patch_item_id`, `depends_on_patch_item_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **schema and change** navigation family. The family context lives in [[Database Catalog#Schema And Change]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/035_proposal_dependencies.sql`.
- **Schema touched by:** `035_proposal_dependencies.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `proposed_patch_item_id` | `TEXT` | yes | — | PRIMARY KEY; FK → [[Reference/Database/Tables/proposed_patch_items\|proposed_patch_items.id]] | Stored value |
| `depends_on_patch_item_id` | `TEXT` | yes | — | PRIMARY KEY; FK → [[Reference/Database/Tables/proposed_patch_items\|proposed_patch_items.id]] | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `depends_on_patch_item_id` → [[Reference/Database/Tables/proposed_patch_items|`proposed_patch_items.id`]]; on delete `CASCADE`, on update `NO ACTION`.
- `proposed_patch_item_id` → [[Reference/Database/Tables/proposed_patch_items|`proposed_patch_items.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_proposed_patch_item_dependencies_dep` on `depends_on_patch_item_id`.
- `sqlite_autoindex_proposed_patch_item_dependencies_1` on `proposed_patch_item_id`, `depends_on_patch_item_id` (unique).

## Who calls it

### Repository access surface

- `Repository.persist_proposal_batch()`
- `Repository.proposal_item_dependencies()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/content/pipeline/source_ingestion.py`
- `src/learnloop/content/proposals/apply_protocol.py`
- `src/learnloop/content/proposals/proposals.py`
- `src/learnloop/content/synthesis/source_append.py`
- `src/learnloop/content/synthesis/source_set_synthesis.py`
- `src/learnloop/curriculum/graph_edit_proposals.py`
- `src/learnloop/curriculum/subject_registry.py`
- `src/learnloop/diagnosis/error_taxonomy.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_apply_write_ahead.py`
- `tests/test_missing_vocabulary_notes.py`
- `tests/test_patch_applier.py`
- `tests/test_proposal_dependencies.py`
- `tests/test_repositories.py`
- `tests/test_sidecar_contract.py`

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
CREATE TABLE proposed_patch_item_dependencies (
  proposed_patch_item_id TEXT NOT NULL
    REFERENCES proposed_patch_items(id) ON DELETE CASCADE,
  depends_on_patch_item_id TEXT NOT NULL
    REFERENCES proposed_patch_items(id) ON DELETE CASCADE,
  PRIMARY KEY (proposed_patch_item_id, depends_on_patch_item_id)
);
```

## Related notes

- [[Database Catalog#Schema And Change|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
