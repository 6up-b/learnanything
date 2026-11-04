---
title: "generated_probe_items"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "4ce26b4b865d9850ab7f5bd68e1e78d7a590353b"
source_commit_timestamp: "2026-11-04T17:57:24-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite generated_probe_items"
  - "table generated_probe_items"
schema_head: 242
table_name: "generated_probe_items"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "241_followup_generate_serve.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/241_followup_generate_serve.sql"
  - "src/learnloop/db/stores/followup_serve.py"
  - "src/learnloop/followup_serve/identity.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `generated_probe_items`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives generated probe item a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `practice_item_id`, `workflow_id`, `probe_episode_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/241_followup_generate_serve.sql`.
- **Schema touched by:** `241_followup_generate_serve.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `practice_item_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `item_revision` | `TEXT` | yes | — | — | Stored value |
| `source` | `TEXT` | yes | — | — | Stored value |
| `workflow_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/followup_workflows\|followup_workflows.id]] | Stored value |
| `probe_episode_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `workflow_id` → [[Reference/Database/Tables/followup_workflows|`followup_workflows.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `generated_probe_items_workflow` on `workflow_id`.
- `sqlite_autoindex_generated_probe_items_1` on `practice_item_id` (unique).

Database triggers:

- `generated_probe_items_no_delete` — schema-enforced lifecycle or immutability constraint.
- `generated_probe_items_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/followup_serve.py`
- `src/learnloop/followup_serve/identity.py`

### Direct SQL writers

- `src/learnloop/db/stores/followup_serve.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_followup_migration.py`

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
CREATE TABLE generated_probe_items (
  practice_item_id TEXT PRIMARY KEY,
  item_revision TEXT NOT NULL,
  source TEXT NOT NULL CHECK (source IN ('workflow', 'entry', 'mint', 'batch', 'manual')),
  workflow_id TEXT REFERENCES followup_workflows(id),
  probe_episode_id TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
