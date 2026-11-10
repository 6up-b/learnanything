---
title: "decision_records"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite decision_records"
  - "table decision_records"
table_name: "decision_records"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "253_decision_records.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/253_decision_records.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/provenance.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `decision_records`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives decision record a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `trace_id`, `parent_id`, `subject_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/253_decision_records.sql`.
- **Schema touched by:** `253_decision_records.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `trace_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `parent_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `subject_kind` | `TEXT` | no | — | — | Stored value |
| `subject_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `chosen_ref` | `TEXT` | no | — | — | Stored value |
| `decided_by` | `TEXT` | no | — | — | Stored value |
| `rule` | `TEXT` | no | — | — | Stored value |
| `alternatives_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `facts_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `versions_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `detail_table` | `TEXT` | no | — | — | Stored value |
| `detail_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `error_type` | `TEXT` | no | — | — | Stored value |
| `error_where` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `decision_records_kind` on `kind`, `created_at`, `id`.
- `decision_records_parent` on `parent_id`.
- `decision_records_subject` on `subject_kind`, `subject_id`, `created_at`, `id`.
- `decision_records_trace` on `trace_id`, `created_at`, `id`.
- `sqlite_autoindex_decision_records_1` on `id` (unique).

Database triggers:

- `decision_records_no_delete` — schema-enforced lifecycle or immutability constraint.
- `decision_records_no_update` — schema-enforced lifecycle or immutability constraint.

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

- `tests/test_decision_records_migration.py`
- `tests/test_figure_decision_records.py`
- `tests/test_forced_withdrawal_records.py`
- `tests/test_provenance.py`
- `tests/test_slate_record.py`

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
CREATE TABLE decision_records (
  id TEXT PRIMARY KEY,
  trace_id TEXT NOT NULL,
  parent_id TEXT,
  kind TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN (
    'chosen', 'fallback', 'excluded', 'withdrawn', 'timeout', 'discarded', 'failed', 'refused', 'deferred')),
  subject_kind TEXT,
  subject_id TEXT,
  chosen_ref TEXT,
  decided_by TEXT,
  rule TEXT,
  alternatives_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(alternatives_json)),
  facts_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(facts_json)),
  versions_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(versions_json)),
  detail_table TEXT,
  detail_id TEXT,
  error_type TEXT,
  error_where TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
