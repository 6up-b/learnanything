---
title: "prefilter_payloads"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "eff30f881a7d3ea5b06e0a10156b37049285cf52"
source_commit_timestamp: "2026-11-04T20:48:34-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite prefilter_payloads"
  - "table prefilter_payloads"
schema_head: 244
table_name: "prefilter_payloads"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "240_data_capture.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/240_data_capture.sql"
  - "src/learnloop/data_capture/prefilter.py"
  - "src/learnloop/db/stores/data_capture.py"
  - "src/learnloop/ops/capture_report.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `prefilter_payloads`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives prefilter payload a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `content_hash`, `part`, `content_z`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/240_data_capture.sql`.
- **Schema touched by:** `240_data_capture.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `content_hash` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `part` | `TEXT` | yes | — | — | Stored value |
| `content_z` | `BLOB` | yes | — | — | Stored value |
| `raw_bytes` | `INTEGER` | yes | — | — | Stored value |
| `stored_bytes` | `INTEGER` | yes | — | — | Stored value |
| `first_seen_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_prefilter_payloads_1` on `content_hash` (unique).

Database triggers:

- `prefilter_payloads_no_delete` — schema-enforced lifecycle or immutability constraint.
- `prefilter_payloads_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/data_capture.py`
- `src/learnloop/ops/capture_report.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_data_capture_a1_prefilter.py`
- `tests/test_data_capture_migration.py`

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
CREATE TABLE prefilter_payloads (
  content_hash TEXT PRIMARY KEY,
  part TEXT NOT NULL CHECK (part IN ('gates', 'classification', 'upstream', 'inputs', 'config')),
  content_z BLOB NOT NULL,
  raw_bytes INTEGER NOT NULL,
  stored_bytes INTEGER NOT NULL,
  first_seen_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
