---
title: "router_decision_bindings"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "283405f0a5d78fa722adca27f66f4c6c05bff975"
source_commit_timestamp: "2026-11-07T02:53:30-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite router_decision_bindings"
  - "table router_decision_bindings"
schema_head: 249
table_name: "router_decision_bindings"
table_role: "receipt"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "241_followup_generate_serve.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/241_followup_generate_serve.sql"
  - "src/learnloop/db/stores/followup_serve.py"
  - "src/learnloop/router/plan_log.py"
  - "src/learnloop/router_objective/trajectory.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `router_decision_bindings`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives router decision binding a stable database identity so queue and controller decisions can resume safely and explain why an activity was selected. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `decision_id`, `workflow_id`, `practice_item_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Receipt]].

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
| `decision_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/router_decisions\|router_decisions.id]] | Stored value |
| `workflow_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/followup_workflows\|followup_workflows.id]] | Stored value |
| `binding_kind` | `TEXT` | yes | — | — | Stored value |
| `practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `probe_presentation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `plan_presentation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `outcome` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `workflow_id` → [[Reference/Database/Tables/followup_workflows|`followup_workflows.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `decision_id` → [[Reference/Database/Tables/router_decisions|`router_decisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `router_decision_bindings_item` on `practice_item_id`.
- `sqlite_autoindex_router_decision_bindings_2` on `decision_id`, `binding_kind` (unique).
- `sqlite_autoindex_router_decision_bindings_1` on `id` (unique).

Database triggers:

- `router_decision_bindings_no_delete` — schema-enforced lifecycle or immutability constraint.
- `router_decision_bindings_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/followup_serve.py`
- `src/learnloop/router_objective/trajectory.py`

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
CREATE TABLE router_decision_bindings (
  id TEXT PRIMARY KEY,
  decision_id TEXT NOT NULL REFERENCES router_decisions(id),
  workflow_id TEXT NOT NULL REFERENCES followup_workflows(id),
  binding_kind TEXT NOT NULL
    CHECK (binding_kind IN ('item', 'presentation', 'plan_presentation', 'outcome')),
  practice_item_id TEXT,
  probe_presentation_id TEXT,
  plan_presentation_id TEXT,
  outcome TEXT,
  created_at TEXT NOT NULL,
  UNIQUE (decision_id, binding_kind)
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
