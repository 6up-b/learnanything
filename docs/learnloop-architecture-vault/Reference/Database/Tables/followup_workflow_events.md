---
title: "followup_workflow_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "bd1bcd9c9518905e38a4c507b834318e9ce6b8f2"
source_commit_timestamp: "2026-11-06T18:38:09-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite followup_workflow_events"
  - "table followup_workflow_events"
schema_head: 249
table_name: "followup_workflow_events"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "241_followup_generate_serve.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/241_followup_generate_serve.sql"
  - "src/learnloop/db/stores/followup_serve.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `followup_workflow_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of followup workflow so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `workflow_id`, `from_state`, `to_state`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/241_followup_generate_serve.sql`.
- **Schema touched by:** `241_followup_generate_serve.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `workflow_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/followup_workflows\|followup_workflows.id]] | Stored value |
| `from_state` | `TEXT` | no | — | — | Stored value |
| `to_state` | `TEXT` | yes | — | — | Stored value |
| `reason` | `TEXT` | yes | — | — | Stored value |
| `detail_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `workflow_id` → [[Reference/Database/Tables/followup_workflows|`followup_workflows.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `followup_workflow_events_workflow` on `workflow_id`, `created_at`.
- `sqlite_autoindex_followup_workflow_events_1` on `id` (unique).

Database triggers:

- `followup_workflow_events_no_delete` — schema-enforced lifecycle or immutability constraint.
- `followup_workflow_events_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/followup_serve.py`

### Direct SQL writers

- `src/learnloop/db/stores/followup_serve.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_followup_codex_review.py`
- `tests/test_followup_migration.py`
- `tests/test_followup_reserved_only.py`

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
CREATE TABLE followup_workflow_events (
  id TEXT PRIMARY KEY,
  workflow_id TEXT NOT NULL REFERENCES followup_workflows(id),
  from_state TEXT,
  to_state TEXT NOT NULL,
  reason TEXT NOT NULL,
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
