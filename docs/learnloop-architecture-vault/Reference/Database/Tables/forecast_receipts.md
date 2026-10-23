---
title: "forecast_receipts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "0ecc600eaf8899a2a2ca18e2a38eff4c870c8f1d"
source_commit_timestamp: "2026-10-23T16:27:57-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite forecast_receipts"
  - "table forecast_receipts"
schema_head: 217
table_name: "forecast_receipts"
table_role: "receipt"
functionality_status: "active"
domain_family: "goals-and-exams"
introduced_in: "206_forecast_receipts.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/206_forecast_receipts.sql"
  - "src/learnloop/adaptive_difficulty/__init__.py"
  - "src/learnloop/adaptive_difficulty/backfill.py"
  - "src/learnloop/adaptive_difficulty/data_check.py"
  - "src/learnloop/adaptive_difficulty/forecasters.py"
  - "src/learnloop/adaptive_difficulty/outside.py"
  - "src/learnloop/adaptive_difficulty/reading.py"
  - "src/learnloop/adaptive_difficulty/serve.py"
  - "src/learnloop/adaptive_difficulty/serve_inputs.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/goals-and-exams"
---

# `forecast_receipts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Keeps every saved forecast a decision states before its outcome is known (saved diagnosis forecasts, migration 206): a completed diagnosis's prediction of the next unaided observation of each facet it explains, and a scheduled repair cold check's predicted cold outcome, each written in its decision's transaction with its forecaster, scope, inputs as of when, the forecast payload (the voi_forecasts body) and its exact binding, or the reason it has none (censored at birth). Resolutions are derived at read time by `learnloop diagnosis calibration`; nothing serving, scoring or scheduling reads it and no rebuild writes or clears it. Append-only (an update or delete aborts); kill switch diagnosis.forecast_receipts. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `source_attempt_id`, `learning_object_id`, `facet_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **goals and exams** navigation family. The family context lives in [[Database Catalog#Goals And Exams]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/206_forecast_receipts.sql`.
- **Schema touched by:** `206_forecast_receipts.sql`, `213_adaptive_difficulty_receipts.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `receipt_key` | `TEXT` | yes | — | — | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `forecaster` | `TEXT` | yes | — | — | Stored value |
| `forecaster_version` | `TEXT` | yes | — | — | Stored value |
| `scope` | `TEXT` | yes | — | — | Stored value |
| `decision_kind` | `TEXT` | yes | — | — | Stored value |
| `decision_ref` | `TEXT` | no | — | — | Stored value |
| `source_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `facet_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `hypothesis_ref` | `TEXT` | no | — | — | Stored value |
| `practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `item_content_hash` | `TEXT` | no | — | — | Stored value |
| `binding_kind` | `TEXT` | yes | — | — | Stored value |
| `plan_presentation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `probe_presentation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `followup_task_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `scheduler_candidate_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `censor_reason` | `TEXT` | no | — | — | Stored value |
| `event` | `TEXT` | yes | — | — | Stored value |
| `p` | `REAL` | no | — | — | Stored value |
| `forecast_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `inputs_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `inputs_hash` | `TEXT` | yes | — | — | Stored value |
| `inputs_as_of` | `TEXT` | yes | — | — | Stored value |
| `parameters_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `versions_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | `'ok'` | — | Stored value |
| `algorithm_version` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `received_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_forecast_receipts_probe_presentation` on `probe_presentation_id`.
- `idx_forecast_receipts_plan_presentation` on `plan_presentation_id`.
- `idx_forecast_receipts_task` on `followup_task_id`.
- `idx_forecast_receipts_decision` on `decision_ref`.
- `idx_forecast_receipts_facet` on `learning_object_id`, `facet_id`, `created_at`.
- `idx_forecast_receipts_kind` on `kind`, `created_at`, `id`.
- `sqlite_autoindex_forecast_receipts_2` on `receipt_key` (unique).
- `sqlite_autoindex_forecast_receipts_1` on `id` (unique).

Database triggers:

- `forecast_receipts_no_delete` — schema-enforced lifecycle or immutability constraint.
- `forecast_receipts_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/adaptive_difficulty/backfill.py`
- `src/learnloop/adaptive_difficulty/data_check.py`
- `src/learnloop/adaptive_difficulty/outside.py`
- `src/learnloop/adaptive_difficulty/serve.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/ad_fakes.py`
- `tests/test_ad1_codex_review_fixes.py`
- `tests/test_ad1_migration.py`
- `tests/test_ad1_reading_opportunities.py`
- `tests/test_adaptive_difficulty_ad1.py`
- `tests/test_architecture.py`
- `tests/test_chatgpt_plan_landing.py`
- `tests/test_figure_predictions.py`
- `tests/test_forecast_receipts.py`
- `tests/test_forecast_receipts_landing.py`

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
CREATE TABLE forecast_receipts (
  id TEXT PRIMARY KEY,
  -- Idempotency: <kind>:<decision ref>:<subject>:<forecaster>.
  receipt_key TEXT NOT NULL UNIQUE,
  -- What is forecast: diagnosis_next_observation | repair_cold_outcome
  -- (AD1 adds item_unassisted_success; the vocabulary lives in code,
  -- learnloop.scheduling.forecast_receipts.FORECAST_KINDS).
  kind TEXT NOT NULL,
  -- Who forecast it, and the version of its code, priors and config.
  forecaster TEXT NOT NULL,
  forecaster_version TEXT NOT NULL,
  -- What the forecast is about: next_observation (the next qualifying
  -- observation of a facet, by the frozen rule in forecast_json),
  -- followup_task (the cold attempt one scheduled task binds), presentation
  -- or item (AD1).
  scope TEXT NOT NULL,
  -- The decision that wrote it: diagnosis | cold_retry_schedule (AD1: serve).
  decision_kind TEXT NOT NULL,
  decision_ref TEXT,
  source_attempt_id TEXT,
  learning_object_id TEXT,
  facet_id TEXT,
  hypothesis_ref TEXT,
  practice_item_id TEXT,
  -- AD1, scope item: the item revision an item-only forecast is about.
  item_content_hash TEXT,
  -- The exact binding the resolver may follow, and nothing else:
  -- presented_attempt_on_facet (the first qualifying attempt on the facet
  -- after the receipt, admitted only through its plan or probe presentation
  -- or the scheduler offer it answered), followup_task (the task's consumed
  -- attempt and terminal cold outcome), plan_presentation |
  -- probe_presentation (AD1), or none (censored at birth).
  binding_kind TEXT NOT NULL,
  plan_presentation_id TEXT,
  probe_presentation_id TEXT,
  followup_task_id TEXT,
  scheduler_candidate_id TEXT,
  censor_reason TEXT,
  -- The forecast event (next_observation_shape, cold_success; AD1
  -- unassisted_success) and its binary probability when it has one.
  event TEXT NOT NULL,
  p REAL CHECK (p IS NULL OR (p >= 0 AND p <= 1)),
  -- {emission_alphabet, predicted_outcomes, prior, likelihood, ...}: the
  -- body format of voi_forecasts.forecast_json.
  forecast_json TEXT NOT NULL,
  inputs_json TEXT NOT NULL,
  inputs_hash TEXT NOT NULL,
  -- The newest state the forecaster read; never after the receipt.
  inputs_as_of TEXT NOT NULL,
  parameters_json TEXT NOT NULL,
  versions_json TEXT NOT NULL,
  -- ok | failed | refused_spend (AD1's outside forecasters).
  status TEXT NOT NULL DEFAULT 'ok' CHECK (status IN ('ok', 'failed', 'refused_spend')),
  algorithm_version TEXT,
  -- When the forecast was issued (an in-process forecaster writes it then).
  created_at TEXT NOT NULL,
  -- AD1's outside forecasters: when a late answer arrived (null otherwise).
  received_at TEXT,
  CHECK ((binding_kind = 'none') = (censor_reason IS NOT NULL)),
  CHECK (inputs_as_of <= created_at)
);
```

## Related notes

- [[Database Catalog#Goals And Exams|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
