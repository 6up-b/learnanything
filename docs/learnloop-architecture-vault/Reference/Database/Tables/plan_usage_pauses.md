---
title: "plan_usage_pauses"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "0394abccde203a1e4bd7d479ffe28c7035d61f2f"
source_commit_timestamp: "2026-11-06T14:55:42-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite plan_usage_pauses"
  - "table plan_usage_pauses"
schema_head: 249
table_name: "plan_usage_pauses"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "237_figure_prefetch.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/237_figure_prefetch.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/db/stores/figure_prefetch.py"
  - "src/learnloop/figures/prefetch.py"
  - "src/learnloop/figures/prefetch_ledger.py"
  - "src/learnloop/figures/prefetch_model.py"
  - "src/learnloop/params/parameter_registry.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `plan_usage_pauses`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives plan usage pause a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `hit_at`, `reset_at`, `plan_requests_today`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/237_figure_prefetch.sql`.
- **Schema touched by:** `237_figure_prefetch.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `hit_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `reset_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `plan_requests_today` | `INTEGER` | yes | `0` | — | Stored value |
| `plan_tokens_today_known` | `INTEGER` | yes | `0` | — | Stored value |
| `observed_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_plan_usage_pauses_2` on `hit_at` (unique).
- `sqlite_autoindex_plan_usage_pauses_1` on `id` (unique).

Database triggers:

- `plan_usage_pauses_no_delete` — schema-enforced lifecycle or immutability constraint.
- `plan_usage_pauses_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/figures/prefetch.py`
- `src/learnloop/params/parameter_registry.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_figure_prefetch_migration.py`
- `tests/test_figures_prefetch.py`
- `tests/test_figures_prefetch_boundary.py`
- `tests/test_followups_batch7_prefetch_capped_resume.py`

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
CREATE TABLE plan_usage_pauses (
  id TEXT PRIMARY KEY,
  hit_at TEXT NOT NULL UNIQUE,
  reset_at TEXT,
  plan_requests_today INTEGER NOT NULL DEFAULT 0 CHECK (plan_requests_today >= 0),
  plan_tokens_today_known INTEGER NOT NULL DEFAULT 0 CHECK (plan_tokens_today_known >= 0),
  observed_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
