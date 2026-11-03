---
title: "figure_prefetch_decisions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "27497a7340a969f6662bfd46bcc6d5ff9522f505"
source_commit_timestamp: "2026-11-03T04:44:30-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite figure_prefetch_decisions"
  - "table figure_prefetch_decisions"
schema_head: 238
table_name: "figure_prefetch_decisions"
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
  - "src/learnloop/config/schema.py"
  - "src/learnloop/db/stores/figure_prefetch.py"
  - "src/learnloop/figures/prefetch.py"
  - "src/learnloop/figures/prefetch_ledger.py"
  - "src/learnloop/figures/service.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `figure_prefetch_decisions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives figure prefetch decision a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `request_id`, `trigger_kind`, `horizon_kind`, making the operational relationship explicit. ^table-purpose

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
| `trigger_kind` | `TEXT` | yes | — | — | Stored value |
| `trigger_ref` | `TEXT` | yes | — | — | Stored value |
| `request_key` | `TEXT` | yes | — | — | Stored value |
| `input_hash` | `TEXT` | no | — | — | Stored value |
| `anchor_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `goal_text` | `TEXT` | no | — | — | Stored value |
| `goal_author` | `TEXT` | no | — | — | Stored value |
| `source_key` | `TEXT` | no | — | — | Stored value |
| `p_open_content` | `REAL` | no | — | — | Stored value |
| `model_version` | `TEXT` | yes | — | — | Stored value |
| `posterior_digest` | `TEXT` | yes | — | — | Stored value |
| `sampled_eu` | `REAL` | no | — | — | Stored value |
| `propensity` | `REAL` | no | — | — | Stored value |
| `w_minutes` | `REAL` | no | — | — | Stored value |
| `cost_minutes` | `REAL` | no | — | — | Stored value |
| `decision` | `TEXT` | yes | — | — | Stored value |
| `request_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `horizon_kind` | `TEXT` | yes | — | — | Stored value |
| `outcome` | `TEXT` | no | — | — | Stored value |
| `outcome_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_figure_prefetch_decisions_open` on `outcome`.
- `idx_figure_prefetch_decisions_key` on `request_key`, `created_at`.
- `idx_figure_prefetch_decisions_created` on `created_at`.
- `sqlite_autoindex_figure_prefetch_decisions_1` on `id` (unique).

Database triggers:

- `figure_prefetch_decisions_no_delete` — schema-enforced lifecycle or immutability constraint.
- `figure_prefetch_decisions_set_once` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/figures/prefetch.py`
- `src/learnloop/figures/service.py`

### Direct SQL writers

- `src/learnloop/db/stores/figure_prefetch.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_figure_prefetch_migration.py`
- `tests/test_figures_prefetch.py`
- `tests/test_figures_prefetch_boundary.py`
- `tests/test_followups_batch6_prefetch_decided_once.py`
- `tests/test_followups_batch6_prefetch_plan_wait.py`

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
CREATE TABLE figure_prefetch_decisions (
  id TEXT PRIMARY KEY,
  trigger_kind TEXT NOT NULL CHECK (trigger_kind IN ('plan', 'section', 'offer', 'lesson', 'gap')),
  trigger_ref TEXT NOT NULL,
  request_key TEXT NOT NULL,
  input_hash TEXT,
  anchor_json TEXT,
  goal_text TEXT,
  goal_author TEXT CHECK (goal_author IS NULL OR goal_author IN ('prefetch', 'teacher')),
  source_key TEXT,
  p_open_content REAL CHECK (p_open_content IS NULL OR (p_open_content >= 0 AND p_open_content <= 1)),
  model_version TEXT NOT NULL,
  posterior_digest TEXT NOT NULL,
  sampled_eu REAL,
  propensity REAL CHECK (propensity IS NULL OR (propensity >= 0 AND propensity <= 1)),
  w_minutes REAL,
  cost_minutes REAL,
  decision TEXT NOT NULL CHECK (decision IN ('build', 'skip', 'capped', 'deferred_power', 'deferred_plan')),
  request_id TEXT,
  horizon_kind TEXT NOT NULL CHECK (horizon_kind IN ('plan_day_ended', 'section_read', 'lesson_closed',
                                                     'thread_closed', 'gap_closed')),
  outcome TEXT CHECK (outcome IS NULL OR outcome IN ('opened', 'asked', 'neither', 'void')),
  outcome_at TEXT,
  created_at TEXT NOT NULL,
  CHECK (goal_text IS NULL OR goal_author IS NOT NULL),
  CHECK ((outcome IS NULL) = (outcome_at IS NULL))
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
