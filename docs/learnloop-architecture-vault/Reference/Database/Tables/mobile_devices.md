---
title: "mobile_devices"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "90e8b400ec88a17e7d27bb23aeb54ed456ca9216"
source_commit_timestamp: "2026-10-16T00:42:10-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite mobile_devices"
  - "table mobile_devices"
schema_head: 206
table_name: "mobile_devices"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "171_mobile_capture.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/171_mobile_capture.sql"
  - "src/learnloop/capture/devices.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `mobile_devices`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives mobile device a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `token_hash`, `label`, `scope`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> M1 is an inbox, not learner evidence or an automatic practice workflow.

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
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `label` | `TEXT` | yes | — | — | Stored value |
| `scope` | `TEXT` | yes | — | — | Stored value |
| `token_hash` | `TEXT` | yes | — | — | Stored value |
| `tailscale_login` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `claimed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `last_seen_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `revoked_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_mobile_devices_2` on `token_hash` (unique).
- `sqlite_autoindex_mobile_devices_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/capture/devices.py`

### Direct SQL writers

- `src/learnloop/capture/devices.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_mobile_host_coexistence.py`
- `tests/test_mobile_pairing.py`

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
CREATE TABLE mobile_devices (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    scope TEXT NOT NULL CHECK (scope IN ('capture', 'app')),
    token_hash TEXT NOT NULL UNIQUE,
    tailscale_login TEXT,
    created_at TEXT NOT NULL,
    claimed_at TEXT,
    last_seen_at TEXT,
    revoked_at TEXT
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
