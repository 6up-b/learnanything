---
title: "learner_text_gap_reversals"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "924e0756f341f88c29d8ae1ff5083921c59e7c23"
source_commit_timestamp: "2026-10-20T19:18:15-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite learner_text_gap_reversals"
  - "table learner_text_gap_reversals"
schema_head: 216
table_name: "learner_text_gap_reversals"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "182_learner_text_gaps.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/182_learner_text_gaps.sql"
  - "src/learnloop/daily_plan/router_card.py"
  - "src/learnloop/db/stores/learner_gaps.py"
  - "src/learnloop/field/signals.py"
  - "src/learnloop/learner_context.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `learner_text_gap_reversals`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives learner text gap reversal a stable database identity so learner-facing mastery and capability decisions use a reproducible evidence projection. It supplies replay-stable input rather than a disposable cache. Rows bind `gap_id`, `reversal`, `actor`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> The learner's one-tap reversals: undo an added edge, undo a created prerequisite, or "not what I meant" on a belief sighting. One of each kind per gap (a repeated tap is a no-op). Append-only.

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/182_learner_text_gaps.sql`.
- **Schema touched by:** `182_learner_text_gaps.sql`, `208_learner_text_source_kinds.sql`, `212_hint_feedback_source_kind.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `gap_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/learner_text_gaps\|learner_text_gaps.id]] | Stored value |
| `reversal` | `TEXT` | yes | — | — | Stored value |
| `actor` | `TEXT` | yes | — | — | Stored value |
| `detail_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `gap_id` → [[Reference/Database/Tables/learner_text_gaps|`learner_text_gaps.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_learner_text_gap_reversals_2` on `gap_id`, `reversal` (unique).
- `sqlite_autoindex_learner_text_gap_reversals_1` on `id` (unique).

Database triggers:

- `learner_text_gap_reversals_no_delete` — schema-enforced lifecycle or immutability constraint.
- `learner_text_gap_reversals_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/daily_plan/router_card.py`
- `src/learnloop/db/stores/learner_gaps.py`
- `src/learnloop/field/signals.py`
- `src/learnloop/learner_context.py`

### Direct SQL writers

- `src/learnloop/db/stores/learner_gaps.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/mcp_world.py`
- `tests/test_hint_feedback_widening.py`
- `tests/test_learner_text_source_widening.py`
- `tests/test_mvp016_upgrade.py`

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
CREATE TABLE learner_text_gap_reversals (
  id TEXT PRIMARY KEY,
  gap_id TEXT NOT NULL REFERENCES learner_text_gaps(id),
  reversal TEXT NOT NULL CHECK (reversal IN ('undo_edge', 'undo_creation', 'not_this_belief')),
  actor TEXT NOT NULL CHECK (actor IN ('learner', 'owner')),
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  UNIQUE (gap_id, reversal)
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
