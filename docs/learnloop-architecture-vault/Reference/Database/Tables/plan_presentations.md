---
title: "plan_presentations"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "b5ae9988697a3537bfa21426f0070f42e5354f2f"
source_commit_timestamp: "2026-10-31T17:40:16-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite plan_presentations"
  - "table plan_presentations"
schema_head: 228
table_name: "plan_presentations"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "202_router_staged_frame.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/202_router_staged_frame.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/forecasters.py"
  - "src/learnloop/adaptive_difficulty/material_view.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/adaptive_difficulty/scoring.py"
  - "src/learnloop/adaptive_difficulty/serve.py"
  - "src/learnloop/daily_plan/engine.py"
  - "src/learnloop/db/repositories.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `plan_presentations`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives plan presentation a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `block_id`, `router_decision_id`, `controller_decision_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> One row per plan item served (DL1's item_served receipt), in the same transaction. The block's router decision (attention_blocks.decision_ref) and, when that decision named one, the staged controller decision are copied so a forecast or an outcome joins without re-reading the block.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/202_router_staged_frame.sql`.
- **Schema touched by:** `202_router_staged_frame.sql`, `214_adaptive_difficulty_serving.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `block_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/attention_blocks\|attention_blocks.id]] | Stored value |
| `router_decision_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/router_decisions\|router_decisions.id]] | Stored value |
| `controller_decision_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `position` | `INTEGER` | no | — | — | Stored value |
| `origin` | `TEXT` | yes | — | — | Stored value |
| `scheduler_candidate_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `probe_presentation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `served_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `router_decision_id` → [[Reference/Database/Tables/router_decisions|`router_decisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `block_id` → [[Reference/Database/Tables/attention_blocks|`attention_blocks.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `plan_presentations_session_item` on `session_id`, `practice_item_id`.
- `plan_presentations_controller` on `controller_decision_id`.
- `plan_presentations_decision` on `router_decision_id`.
- `sqlite_autoindex_plan_presentations_2` on `block_id`, `practice_item_id` (unique).
- `sqlite_autoindex_plan_presentations_1` on `id` (unique).

Database triggers:

- `plan_presentations_no_delete` — schema-enforced lifecycle or immutability constraint.
- `plan_presentations_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository._bindable_plan_presentation()`

### Direct SQL readers

- `src/learnloop/adaptive_difficulty/material_view.py`
- `src/learnloop/db/stores/plan_presentations.py`
- `src/learnloop/evsi_calibration/live_report.py`

### Direct SQL writers

- `src/learnloop/db/stores/plan_presentations.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_ad1_codex_review_fixes.py`
- `tests/test_ad23_contract.py`
- `tests/test_ad23_fix_review.py`
- `tests/test_ad_guard.py`
- `tests/test_adaptive_difficulty_ad1.py`
- `tests/test_architecture.py`
- `tests/test_evsi_staged_binding.py`
- `tests/test_forecast_receipts.py`
- `tests/test_mvp023_upgrade.py`
- `tests/test_reader_rw3a_landing.py`
- `tests/test_reader_rw4b_admission_idempotency.py`
- `tests/test_reader_rw4b_fix6.py`
- `tests/test_router_g4_restraint.py`
- `tests/test_router_presentations.py`
- `tests/test_router_r2a_serving.py`
- `tests/test_router_r2bc_landing.py`
- `tests/test_ux_phase4_landing.py`

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
CREATE TABLE plan_presentations (
  id TEXT PRIMARY KEY,
  block_id TEXT NOT NULL REFERENCES attention_blocks(id),
  router_decision_id TEXT REFERENCES router_decisions(id),
  controller_decision_id TEXT,
  practice_item_id TEXT NOT NULL,
  position INTEGER CHECK (position IS NULL OR position >= 1),
  -- chooser | requested | followup | learner_pick | open_list
  origin TEXT NOT NULL,
  scheduler_candidate_id TEXT,
  -- A committed probe presentation the item was served under (none yet: the
  -- plan does not open probe presentations; kept for that join).
  probe_presentation_id TEXT,
  session_id TEXT,
  served_at TEXT NOT NULL,
  UNIQUE (block_id, practice_item_id)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
