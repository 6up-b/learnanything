---
title: "maintenance_notices"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite maintenance_notices"
  - "table maintenance_notices"
schema_head: 157
table_name: "maintenance_notices"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "051_maintenance_feed.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/051_maintenance_feed.sql"
  - "src/learnloop/curriculum/graph_edit_proposals.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/diagnostic_surface_supply.py"
  - "src/learnloop/ops/maintenance_feed.py"
  - "src/learnloop_sidecar/handlers/app.py"
  - "src/learnloop_sidecar/handlers/ingest.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `maintenance_notices`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Stores actionable maintenance items surfaced by operational checks. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `subject_id`, `entity_id`, `notice_type`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/051_maintenance_feed.sql`.
- **Schema touched by:** `051_maintenance_feed.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `subject_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `notice_type` | `TEXT` | yes | — | — | Stored value |
| `dedup_key` | `TEXT` | yes | — | — | Stored value |
| `severity` | `TEXT` | yes | `'info'` | — | Stored value |
| `aging_policy` | `TEXT` | yes | — | — | Stored value |
| `entity_type` | `TEXT` | no | — | — | Stored value |
| `entity_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `title` | `TEXT` | yes | — | — | Stored value |
| `detail_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `action_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | `'active'` | — | Stored value |
| `snooze_count` | `INTEGER` | yes | `0` | — | Stored value |
| `snoozed_until` | `TEXT` | no | — | — | Stored value |
| `first_seen_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `last_seen_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `resolved_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_maintenance_notices_subject` on `subject_id`.
- `idx_maintenance_notices_status` on `status`, `notice_type`.
- `sqlite_autoindex_maintenance_notices_2` on `notice_type`, `dedup_key` (unique).
- `sqlite_autoindex_maintenance_notices_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.live_maintenance_notice_keys()`
- `Repository.maintenance_notice()`
- `Repository.maintenance_notices()`
- `Repository.set_maintenance_notice_status()`
- `Repository.upsert_maintenance_notice()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop_sidecar/handlers/app.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/graph_edit_proposals.py`
- `src/learnloop/diagnosis/diagnostic_surface_supply.py`
- `src/learnloop/ops/maintenance_feed.py`
- `src/learnloop_sidecar/handlers/ingest.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_maintenance_feed.py`
- `tests/test_probe_pool_empty.py`
- `tests/test_graph_edit_proposals.py`
- `tests/test_sidecar_measurement.py`

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
CREATE TABLE maintenance_notices (
  id TEXT PRIMARY KEY,
  subject_id TEXT,
  notice_type TEXT NOT NULL,
  dedup_key TEXT NOT NULL,
  severity TEXT NOT NULL DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'action_needed')),
  aging_policy TEXT NOT NULL CHECK (
    aging_policy IN ('auto_expiry', 'auto_resolution', 'escalation')
  ),
  entity_type TEXT,
  entity_id TEXT,
  title TEXT NOT NULL,
  detail_json TEXT,
  action_json TEXT NOT NULL,        -- {action, label, ...} — one concrete action link
  status TEXT NOT NULL DEFAULT 'active' CHECK (
    status IN ('active', 'snoozed', 'dismissed', 'resolved', 'expired')
  ),
  snooze_count INTEGER NOT NULL DEFAULT 0,
  snoozed_until TEXT,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  resolved_at TEXT,
  UNIQUE (notice_type, dedup_key)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
