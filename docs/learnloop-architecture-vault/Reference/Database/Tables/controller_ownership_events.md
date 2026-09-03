---
title: "controller_ownership_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite controller_ownership_events"
  - "table controller_ownership_events"
schema_head: 157
table_name: "controller_ownership_events"
table_role: "receipt"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "099_controller_ownership.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/099_controller_ownership.sql"
  - "src/learnloop/scheduling/controller_ownership.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `controller_ownership_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of controller ownership so queue and controller decisions can resume safely and explain why an activity was selected. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `commitment_id`, `receipt_id`, `policy_version`, making the operational relationship explicit. ^table-purpose

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/099_controller_ownership.sql`.
- **Schema touched by:** `099_controller_ownership.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `commitment_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `event_ordinal` | `INTEGER` | yes | — | — | Stored value |
| `from_owner` | `TEXT` | no | — | — | Stored value |
| `to_owner` | `TEXT` | yes | — | — | Stored value |
| `reason` | `TEXT` | yes | — | — | Stored value |
| `receipt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `policy_version` | `INTEGER` | yes | — | — | Stored value |
| `detail_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_controller_ownership_events_receipt` on `receipt_id`.
- `idx_controller_ownership_events_commitment` on `commitment_id`, `event_ordinal`.
- `sqlite_autoindex_controller_ownership_events_2` on `commitment_id`, `event_ordinal` (unique).
- `sqlite_autoindex_controller_ownership_events_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/scheduling/controller_ownership.py`

### Direct SQL writers

- `src/learnloop/scheduling/controller_ownership.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

No table-specific test contains the table name or a detected repository method call. The schema/role invariants are still pinned by `tests/test_migrations.py` and `tests/test_table_roles.py`.

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
CREATE TABLE controller_ownership_events (
  id TEXT PRIMARY KEY,
  commitment_id TEXT NOT NULL,
  event_ordinal INTEGER NOT NULL,
  from_owner TEXT CHECK (from_owner IN ('staged', 'legacy')),
  to_owner TEXT NOT NULL CHECK (to_owner IN ('staged', 'legacy')),
  reason TEXT NOT NULL,
  receipt_id TEXT NOT NULL,
  policy_version INTEGER NOT NULL,
  detail_json TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(commitment_id, event_ordinal)
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
