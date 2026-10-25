---
title: "field_signal_receipts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "c54ecedfa5118e990dee937eeb7741f8ccb4eb45"
source_commit_timestamp: "2026-10-25T12:09:24-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite field_signal_receipts"
  - "table field_signal_receipts"
schema_head: 220
table_name: "field_signal_receipts"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "219_field_signal_receipts.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/219_field_signal_receipts.sql"
  - "src/learnloop/algorithm_versions.py"
  - "src/learnloop/db/stores/field_signal_receipts.py"
  - "src/learnloop/placement/decisions.py"
  - "src/learnloop/placement/field_receipts.py"
  - "src/learnloop/workbench_field_signals_upgrade.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `field_signal_receipts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Freezes the inputs and outcome of each field signal decision so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `learning_object_id`, `decision_kind`, `signal_version`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/219_field_signal_receipts.sql`.
- **Schema touched by:** `219_field_signal_receipts.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `receipt_key` | `TEXT` | yes | — | — | Stored value |
| `decision_kind` | `TEXT` | yes | — | — | Stored value |
| `decision_ref` | `TEXT` | no | — | — | Stored value |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `signal_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `predecessor_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `successor_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `signal_version` | `TEXT` | yes | — | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `field_signal_receipts_lo` on `learning_object_id`, `created_at`, `id`.
- `sqlite_autoindex_field_signal_receipts_2` on `receipt_key` (unique).
- `sqlite_autoindex_field_signal_receipts_1` on `id` (unique).

Database triggers:

- `field_signal_receipts_no_delete` — schema-enforced lifecycle or immutability constraint.
- `field_signal_receipts_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/field_signal_receipts.py`

### Direct SQL writers

- `src/learnloop/db/stores/field_signal_receipts.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_architecture.py`
- `tests/test_field_workbench_signals.py`
- `tests/test_rw2d_receipts_migration.py`

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
CREATE TABLE field_signal_receipts (
  id TEXT PRIMARY KEY,
  -- Idempotency: <decision_kind>:<decision_ref>:<lo>:<sha256 of the
  -- workbench ids and the predecessor verdict>.
  receipt_key TEXT NOT NULL UNIQUE,
  decision_kind TEXT NOT NULL CHECK (decision_kind IN ('fast_track', 'quick_check')),
  decision_ref TEXT,
  learning_object_id TEXT NOT NULL,
  signal_ids_json TEXT NOT NULL,
  predecessor_json TEXT NOT NULL,
  successor_json TEXT NOT NULL,
  signal_version TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
