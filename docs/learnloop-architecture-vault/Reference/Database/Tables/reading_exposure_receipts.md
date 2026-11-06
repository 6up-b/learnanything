---
title: "reading_exposure_receipts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "04d1b40e19aa935b9233c007868ca3c58d217e99"
source_commit_timestamp: "2026-11-06T04:58:47-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite reading_exposure_receipts"
  - "table reading_exposure_receipts"
schema_head: 248
table_name: "reading_exposure_receipts"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "240_data_capture.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/240_data_capture.sql"
  - "src/learnloop/data_capture/reading_exposures.py"
  - "src/learnloop/db/stores/data_capture.py"
  - "src/learnloop/ops/capture_report.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `reading_exposure_receipts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Freezes the inputs and outcome of each reading exposure decision so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `source_id`, `learning_object_id`, `mapping_version`, making the operational relationship explicit. ^table-purpose

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
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `subkind` | `TEXT` | yes | — | — | Stored value |
| `source_table` | `TEXT` | yes | — | — | Stored value |
| `source_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `source_written_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `mapping_version` | `TEXT` | yes | — | — | Stored value |
| `swept_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `reading_exposure_receipts_source_time` on `source_written_at`.
- `sqlite_autoindex_reading_exposure_receipts_2` on `kind`, `subkind`, `source_table`, `source_id`, `learning_object_id` (unique).
- `sqlite_autoindex_reading_exposure_receipts_1` on `id` (unique).

Database triggers:

- `reading_exposure_receipts_no_delete` — schema-enforced lifecycle or immutability constraint.
- `reading_exposure_receipts_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

None found by exact static reference scan.

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_data_capture_codex_rereview.py`
- `tests/test_data_capture_landing_review.py`
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
CREATE TABLE reading_exposure_receipts (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  subkind TEXT NOT NULL,
  source_table TEXT NOT NULL,
  source_id TEXT NOT NULL,
  source_written_at TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  mapping_version TEXT NOT NULL,
  swept_at TEXT NOT NULL,
  UNIQUE (kind, subkind, source_table, source_id, learning_object_id)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
