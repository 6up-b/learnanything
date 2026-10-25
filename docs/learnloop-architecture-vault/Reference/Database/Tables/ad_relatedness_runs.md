---
title: "ad_relatedness_runs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "a5c36443023a87678721d241d47d6fe4b45fc108"
source_commit_timestamp: "2026-10-25T17:00:22-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite ad_relatedness_runs"
  - "table ad_relatedness_runs"
schema_head: 222
table_name: "ad_relatedness_runs"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "214_adaptive_difficulty_serving.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/214_adaptive_difficulty_serving.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/adaptive_difficulty/relatedness.py"
  - "src/learnloop/db/stores/ad_serving.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `ad_relatedness_runs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Tracks one execution, input identity, and result for ad relatedness so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `subject_id`, `prompt_version`, `input_hash`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §5.10: one relatedness proposal run per subject (the units it covered, the judgment_ledger rows it appended, its input hash and status). The proposal itself is judgment_ledger rows (task `ad_relatedness`); this receipt records which units a run covered, so a unit re-proposed with nothing valid has none.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/214_adaptive_difficulty_serving.sql`.
- **Schema touched by:** `214_adaptive_difficulty_serving.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `run_key` | `TEXT` | yes | — | — | Stored value |
| `subject_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `input_hash` | `TEXT` | yes | — | — | Stored value |
| `units_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `judgment_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | — | — | Stored value |
| `prompt_version` | `TEXT` | yes | — | — | Stored value |
| `judge_model` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_ad_relatedness_runs_subject` on `subject_id`, `created_at`.
- `sqlite_autoindex_ad_relatedness_runs_2` on `run_key` (unique).
- `sqlite_autoindex_ad_relatedness_runs_1` on `id` (unique).

Database triggers:

- `ad_relatedness_runs_no_delete` — schema-enforced lifecycle or immutability constraint.
- `ad_relatedness_runs_no_update` — schema-enforced lifecycle or immutability constraint.

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

- `tests/test_ad23_contract.py`
- `tests/test_ad23_fix_r9.py`
- `tests/test_ad23_migration.py`
- `tests/test_ad3_relatedness.py`
- `tests/test_ad_projection.py`
- `tests/test_architecture.py`

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
CREATE TABLE ad_relatedness_runs (
  id TEXT PRIMARY KEY,
  run_key TEXT NOT NULL UNIQUE,
  subject_id TEXT NOT NULL,
  input_hash TEXT NOT NULL,
  units_json TEXT NOT NULL,
  judgment_ids_json TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('ok', 'failed', 'refused_spend', 'protected', 'stale')),
  prompt_version TEXT NOT NULL,
  judge_model TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
