---
title: "error_event_lineage"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "b35681815a840bde6a724331ee47d84a215209e3"
source_commit_timestamp: "2026-10-20T23:01:52-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite error_event_lineage"
  - "table error_event_lineage"
schema_head: 215
table_name: "error_event_lineage"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "205_write_provenance.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/205_write_provenance.sql"
  - "src/learnloop/db/stores/write_provenance.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `error_event_lineage`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives error event lineage a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `attempt_id`, `error_event_id`, `replaces_error_event_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/205_write_provenance.sql`.
- **Schema touched by:** `205_write_provenance.sql`, `206_forecast_receipts.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `error_event_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `replaces_error_event_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `reason` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_error_event_lineage_attempt` on `attempt_id`, `created_at`.
- `idx_error_event_lineage_retired` on `replaces_error_event_id` (unique).
- `idx_error_event_lineage_replaced` on `replaces_error_event_id`.
- `sqlite_autoindex_error_event_lineage_2` on `error_event_id`, `replaces_error_event_id` (unique).
- `sqlite_autoindex_error_event_lineage_1` on `id` (unique).

Database triggers:

- `error_event_lineage_no_delete` — schema-enforced lifecycle or immutability constraint.
- `error_event_lineage_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/write_provenance.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_diagnosis_input_provenance.py`
- `tests/test_diagnosis_input_provenance_landing.py`
- `tests/test_forecast_receipts_landing.py`
- `tests/test_ux_phase4_landing.py`

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
CREATE TABLE error_event_lineage (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL,
  error_event_id TEXT,
  replaces_error_event_id TEXT NOT NULL,
  reason TEXT NOT NULL CHECK (reason IN ('regrade')),
  created_at TEXT NOT NULL,
  UNIQUE (error_event_id, replaces_error_event_id)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
