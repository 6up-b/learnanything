---
title: "diagnosis_wait_receipts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "dcc1b02bb77059ad70b4ed4b98ffdb2935a85735"
source_commit_timestamp: "2026-10-13T18:08:34-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite diagnosis_wait_receipts"
  - "table diagnosis_wait_receipts"
schema_head: 197
table_name: "diagnosis_wait_receipts"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "170_blind_grading_diagnosis_split.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/170_blind_grading_diagnosis_split.sql"
  - "src/learnloop/db/stores/diagnoses.py"
  - "src/learnloop/diagnosis/split/reports.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `diagnosis_wait_receipts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Freezes the inputs and outcome of each diagnosis wait decision so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `session_id`, `waited_seconds`, `served_without_diagnosis`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> E7: one row per item served after a diagnosis-bearing answer in its session; served_without_diagnosis marks a serve while a required diagnosis was not in force (queued, running, failed or budget-skipped), and pending_attempt_ids_json names those attempts.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/170_blind_grading_diagnosis_split.sql`.
- **Schema touched by:** `170_blind_grading_diagnosis_split.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `pending_attempt_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `waited_seconds` | `REAL` | yes | `0` | — | Stored value |
| `served_without_diagnosis` | `INTEGER` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_diagnosis_wait_receipts_1` on `id` (unique).

Database triggers:

- `diagnosis_wait_receipts_no_delete` — schema-enforced lifecycle or immutability constraint.
- `diagnosis_wait_receipts_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/diagnoses.py`

### Direct SQL writers

- `src/learnloop/db/stores/diagnoses.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_diagnosis_async_router.py`

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
CREATE TABLE diagnosis_wait_receipts (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  pending_attempt_ids_json TEXT NOT NULL DEFAULT '[]',
  waited_seconds REAL NOT NULL DEFAULT 0,
  served_without_diagnosis INTEGER NOT NULL CHECK (served_without_diagnosis IN (0, 1)),
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
