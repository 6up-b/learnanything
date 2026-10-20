---
title: "router_decision_payloads"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "ee20a4204c73da58ca7320637f41fbac746d5807"
source_commit_timestamp: "2026-10-20T18:45:49-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite router_decision_payloads"
  - "table router_decision_payloads"
schema_head: 215
table_name: "router_decision_payloads"
table_role: "workflow"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "202_router_staged_frame.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/202_router_staged_frame.sql"
  - "src/learnloop/cli/router.py"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/daily_plan/router_retrieval.py"
  - "src/learnloop/db/stores/router.py"
  - "src/learnloop/router/card.py"
  - "src/learnloop/router/plan_log.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `router_decision_payloads`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives router decision payload a stable database identity so queue and controller decisions can resume safely and explain why an activity was selected. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `decision_id`, `format_version`, `content_hash`, making the operational relationship explicit. ^table-purpose

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/202_router_staged_frame.sql`.
- **Schema touched by:** `202_router_staged_frame.sql`, `213_adaptive_difficulty_receipts.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `decision_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/router_decisions\|router_decisions.id]] | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `format_version` | `TEXT` | yes | — | — | Stored value |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `content_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `content_text` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `decision_id` → [[Reference/Database/Tables/router_decisions|`router_decisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `router_decision_payloads_created` on `created_at`.
- `sqlite_autoindex_router_decision_payloads_2` on `decision_id`, `kind` (unique).
- `sqlite_autoindex_router_decision_payloads_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/cli/router.py`
- `src/learnloop/daily_plan/router_retrieval.py`
- `src/learnloop/db/stores/router.py`

### Direct SQL writers

- `src/learnloop/db/stores/router.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/router_mixture_helpers.py`
- `tests/test_mvp023_upgrade.py`
- `tests/test_router_card.py`
- `tests/test_router_r2a_serving.py`

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
CREATE TABLE router_decision_payloads (
  id TEXT PRIMARY KEY,
  decision_id TEXT NOT NULL REFERENCES router_decisions(id),
  -- card (R2a); R2b adds the model requests and their raw responses.
  kind TEXT NOT NULL CHECK (
    kind IN ('card', 'decider_request', 'decider_response', 'llm_request', 'llm_response')
  ),
  format_version TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  content_json TEXT,
  content_text TEXT,
  created_at TEXT NOT NULL,
  UNIQUE (decision_id, kind)
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
