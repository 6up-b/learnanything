---
title: "mastery_seed_inputs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite mastery_seed_inputs"
  - "table mastery_seed_inputs"
table_name: "mastery_seed_inputs"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "265_mastery_seed_inputs.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/265_mastery_seed_inputs.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/algorithm_versions.py"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/db/mastery_seed_inputs.py"
  - "src/learnloop/db/stores/attempts.py"
  - "src/learnloop/db/stores/practice_state.py"
  - "src/learnloop/learner/mastery_seed.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `mastery_seed_inputs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives mastery seed input a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `learning_object_id`, `selected_claim_id`, `policy_version`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/265_mastery_seed_inputs.sql`.
- **Schema touched by:** `265_mastery_seed_inputs.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `learning_object_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `claims_made_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `selected_claim_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `materialized_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `basis` | `TEXT` | yes | — | — | Stored value |
| `policy_version` | `TEXT` | yes | — | — | Stored value |
| `recorded_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_mastery_seed_inputs_1` on `learning_object_id` (unique).

## Who calls it

### Repository access surface

- `Repository.mastery_seed_inputs()`
- `Repository.record_attempt_outcome()`

### Direct SQL readers

None found by exact static reference scan.

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/learner/mastery_seed.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/mastery_seed_inputs_migration_helpers.py`
- `tests/test_mastery_seed_inputs_migration.py`
- `tests/test_mastery_seed_replay.py`

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
CREATE TABLE mastery_seed_inputs (
  learning_object_id TEXT PRIMARY KEY,
  claims_made_json TEXT NOT NULL,
  selected_claim_id TEXT,
  materialized_at TEXT,
  basis TEXT NOT NULL CHECK (basis IN ('captured_at_materialization', 'legacy_reconstructed')),
  policy_version TEXT NOT NULL,
  recorded_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
