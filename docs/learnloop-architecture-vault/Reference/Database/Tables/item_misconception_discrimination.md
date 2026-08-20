---
title: "item_misconception_discrimination"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite item_misconception_discrimination"
  - "table item_misconception_discrimination"
schema_head: 156
table_name: "item_misconception_discrimination"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "025_misconception_registry.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/025_misconception_registry.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/diagnostic_gate.py"
  - "src/learnloop/diagnosis/followups.py"
  - "src/learnloop/diagnosis/misconceptions.py"
  - "src/learnloop/diagnosis/probes.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `item_misconception_discrimination`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives item misconception discrimination a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `practice_item_id`, `misconception_id`, `sensitivity_alpha`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Estimated (not binary) discrimination of an item's keyed fatal error against a misconception (spec §1.3). Beta posteriors over sensitivity (fire | belief) and specificity (no-fire | clean); consumers read lower bounds, never bare means.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/025_misconception_registry.sql`.
- **Schema touched by:** `025_misconception_registry.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `practice_item_id` | `TEXT` | yes | — | PRIMARY KEY | Stored value |
| `misconception_id` | `TEXT` | yes | — | PRIMARY KEY | Stored value |
| `sensitivity_alpha` | `REAL` | yes | `1` | — | Stored value |
| `sensitivity_beta` | `REAL` | yes | `1` | — | Stored value |
| `specificity_alpha` | `REAL` | yes | `1` | — | Stored value |
| `specificity_beta` | `REAL` | yes | `1` | — | Stored value |
| `n_planted_trials` | `INTEGER` | yes | `0` | — | Stored value |
| `n_clean_trials` | `INTEGER` | yes | `0` | — | Stored value |
| `source` | `TEXT` | no | — | — | Stored value |
| `updated_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_item_mc_discrimination_misconception` on `misconception_id`.
- `sqlite_autoindex_item_misconception_discrimination_1` on `practice_item_id`, `misconception_id` (unique).

## Who calls it

### Repository access surface

- `Repository.discrimination_row()`
- `Repository.discrimination_rows_for_item()`
- `Repository.discrimination_rows_for_misconceptions()`
- `Repository.upsert_item_misconception_discrimination()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/diagnostic_gate.py`
- `src/learnloop/diagnosis/followups.py`
- `src/learnloop/diagnosis/misconceptions.py`
- `src/learnloop/diagnosis/probes.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`
- `tests/test_table_roles.py`
- `tests/test_diagnostic_gate.py`
- `tests/test_diagnostic_generation.py`
- `tests/test_misconception_registry.py`
- `tests/test_misconception_routing.py`
- `tests/test_repositories.py`

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
CREATE TABLE item_misconception_discrimination (
  practice_item_id TEXT NOT NULL,
  misconception_id TEXT NOT NULL,
  sensitivity_alpha REAL NOT NULL DEFAULT 1,
  sensitivity_beta REAL NOT NULL DEFAULT 1,
  specificity_alpha REAL NOT NULL DEFAULT 1,
  specificity_beta REAL NOT NULL DEFAULT 1,
  n_planted_trials INTEGER NOT NULL DEFAULT 0,
  n_clean_trials INTEGER NOT NULL DEFAULT 0,
  source TEXT,
  updated_at TEXT,
  PRIMARY KEY (practice_item_id, misconception_id)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
