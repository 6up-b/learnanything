---
title: "attention_blocks"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite attention_blocks"
  - "table attention_blocks"
schema_head: 156
table_name: "attention_blocks"
table_role: "workflow"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "096_controller_snapshots.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/096_controller_snapshots.sql"
  - "src/learnloop/scheduling/controller_store.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `attention_blocks`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives attention block a stable database identity so queue and controller decisions can resume safely and explain why an activity was selected. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `session_id`, `commitment_id`, `short_circuit_reason`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> One coherent 5-15 minute attention block (§4.1): commitment neighborhood + canonical action + subtype + budget + exit rules. A short-circuit (continuation / explicit learner choice / served administration) is logged as such.

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/096_controller_snapshots.sql`.
- **Schema touched by:** `096_controller_snapshots.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `commitment_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `action` | `TEXT` | yes | — | — | Stored value |
| `subtype` | `TEXT` | no | — | — | Stored value |
| `budget_minutes` | `REAL` | yes | — | — | Stored value |
| `neighborhood_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `exit_rules_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `short_circuit_reason` | `TEXT` | no | — | — | Stored value |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_attention_blocks_session` on `session_id`, `created_at`.
- `sqlite_autoindex_attention_blocks_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

None found by exact static reference scan.

### Direct SQL writers

- `src/learnloop/scheduling/controller_store.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`

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
CREATE TABLE attention_blocks (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  commitment_id TEXT,
  action TEXT NOT NULL,
  subtype TEXT,
  budget_minutes REAL NOT NULL,
  neighborhood_json TEXT NOT NULL DEFAULT '{}',
  exit_rules_json TEXT NOT NULL DEFAULT '[]',
  short_circuit_reason TEXT,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
