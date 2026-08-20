---
title: "composed_selector_telemetry_horizons"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite composed_selector_telemetry_horizons"
  - "table composed_selector_telemetry_horizons"
schema_head: 156
table_name: "composed_selector_telemetry_horizons"
table_role: "workflow"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "100_kinship_kernel_and_shadow_components.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/100_kinship_kernel_and_shadow_components.sql"
  - "src/learnloop/scheduling/shadow_components.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `composed_selector_telemetry_horizons`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives composed selector telemetry horizon a stable database identity so queue and controller decisions can resume safely and explain why an activity was selected. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `horizon_days`, `opened_at`, `retires_at`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> The composed-selector telemetry is TIME-BOXED: a registered horizon after which unpromoted telemetry retires (design §B step 6). One row per registered horizon; a retirement event is appended when now crosses opened_at + horizon_days.

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/100_kinship_kernel_and_shadow_components.sql`.
- **Schema touched by:** `100_kinship_kernel_and_shadow_components.sql`, `101_dual_authority_and_kinship_dedup.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `horizon_days` | `INTEGER` | yes | — | — | Stored value |
| `opened_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `retires_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `retired_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `status` | `TEXT` | yes | `'open'` | — | Stored value |
| `detail_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_composed_selector_horizon_single_open` on `status` (unique).
- `sqlite_autoindex_composed_selector_telemetry_horizons_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/scheduling/shadow_components.py`

### Direct SQL writers

- `src/learnloop/scheduling/shadow_components.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_shadow_components.py`

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
CREATE TABLE composed_selector_telemetry_horizons (
  id TEXT PRIMARY KEY,
  horizon_days INTEGER NOT NULL,
  opened_at TEXT NOT NULL,
  retires_at TEXT NOT NULL,
  retired_at TEXT,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'retired')),
  detail_json TEXT
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
