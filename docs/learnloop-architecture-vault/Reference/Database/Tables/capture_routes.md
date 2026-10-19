---
title: "capture_routes"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "607bda02bc052e1b6521bd92b457ff3bae39c51b"
source_commit_timestamp: "2026-10-19T10:02:54-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite capture_routes"
  - "table capture_routes"
schema_head: 213
table_name: "capture_routes"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "171_mobile_capture.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/171_mobile_capture.sql"
  - "src/learnloop/capture/inbox.py"
  - "src/learnloop/capture/routing.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `capture_routes`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives capture route a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `capture_id`, `state`, `route`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/171_mobile_capture.sql`.
- **Schema touched by:** `171_mobile_capture.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `capture_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/capture_inbox\|capture_inbox.id]] | Stored value |
| `state` | `TEXT` | yes | — | — | Stored value |
| `route` | `TEXT` | no | — | — | Stored value |
| `routed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `dismissed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `result_refs_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `intent_route` | `TEXT` | no | — | — | Stored value |
| `intent_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `media_delete_pending` | `INTEGER` | yes | `0` | — | Stored value |
| `media_retained_shared` | `INTEGER` | yes | `0` | — | Stored value |
| `lease_owner` | `TEXT` | no | — | — | Stored value |
| `lease_expires_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `capture_id` → [[Reference/Database/Tables/capture_inbox|`capture_inbox.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_capture_routes_1` on `capture_id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/capture/inbox.py`
- `src/learnloop/capture/routing.py`

### Direct SQL writers

- `src/learnloop/capture/inbox.py`
- `src/learnloop/capture/routing.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_capture_domain.py`
- `tests/test_capture_route_recovery.py`
- `tests/test_mobile_host_coexistence.py`

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
CREATE TABLE capture_routes (
    capture_id TEXT PRIMARY KEY REFERENCES capture_inbox(id),
    state TEXT NOT NULL CHECK (state IN ('new', 'routed', 'dismissed', 'processing', 'failed')),
    route TEXT,
    routed_at TEXT,
    dismissed_at TEXT,
    result_refs_json TEXT,
    intent_route TEXT,
    intent_json TEXT,
    media_delete_pending INTEGER NOT NULL DEFAULT 0 CHECK (media_delete_pending IN (0, 1)),
    media_retained_shared INTEGER NOT NULL DEFAULT 0 CHECK (media_retained_shared IN (0, 1)),
    lease_owner TEXT,
    lease_expires_at TEXT
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
