---
title: "voi_forecasts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "c3c43fb3089add58dd96a1f5915cf103b7029dd9"
source_commit_timestamp: "2026-10-13T22:50:44-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite voi_forecasts"
  - "table voi_forecasts"
schema_head: 199
table_name: "voi_forecasts"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "184_voi_forecasts.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/184_voi_forecasts.sql"
  - "src/learnloop/cli/evsi.py"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/config/template.py"
  - "src/learnloop/db/stores/voi_forecasts.py"
  - "src/learnloop/diagnosis/causal_diagnostic_selector.py"
  - "src/learnloop/diagnosis/probe_episodes.py"
  - "src/learnloop/diagnosis/voi_forecasting.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `voi_forecasts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives voi forecast a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `learning_object_id`, `probe_episode_id`, `presentation_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/184_voi_forecasts.sql`.
- **Schema touched by:** `184_voi_forecasts.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `receipt_key` | `TEXT` | yes | — | — | Stored value |
| `site` | `TEXT` | yes | — | — | Stored value |
| `decision_ref` | `TEXT` | no | — | — | Stored value |
| `verdict` | `TEXT` | yes | — | — | Stored value |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `probe_episode_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `presentation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `source_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `factor_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `chosen_ref` | `TEXT` | no | — | — | Stored value |
| `chosen_practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `scheduler_candidate_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `candidate_count` | `INTEGER` | yes | — | — | Stored value |
| `eig_nats` | `REAL` | no | — | — | Stored value |
| `evsi_point_minutes` | `REAL` | no | — | — | Stored value |
| `evsi_lcb_minutes` | `REAL` | no | — | — | Stored value |
| `p_action_change` | `REAL` | no | — | — | Stored value |
| `forecast_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `parameters_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `versions_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `forecast_version` | `TEXT` | yes | — | — | Stored value |
| `algorithm_version` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_voi_forecasts_lo` on `learning_object_id`, `created_at`.
- `idx_voi_forecasts_item` on `chosen_practice_item_id`, `created_at`.
- `idx_voi_forecasts_presentation` on `presentation_id`.
- `idx_voi_forecasts_site` on `site`, `created_at`.
- `idx_voi_forecasts_created` on `created_at`, `id`.
- `sqlite_autoindex_voi_forecasts_2` on `receipt_key` (unique).
- `sqlite_autoindex_voi_forecasts_1` on `id` (unique).

Database triggers:

- `voi_forecasts_no_delete` — schema-enforced lifecycle or immutability constraint.
- `voi_forecasts_no_update` — schema-enforced lifecycle or immutability constraint.

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

- `tests/test_architecture.py`
- `tests/test_evsi_router_composition.py`
- `tests/test_facet_rewords_migration.py`
- `tests/test_sources_merge_composition.py`
- `tests/test_voi_forecasts.py`

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
CREATE TABLE voi_forecasts (
  id TEXT PRIMARY KEY,
  -- Idempotency: <site>:<decision ref>, e.g. probe_selection:<presentation>.
  receipt_key TEXT NOT NULL UNIQUE,
  -- probe_selection | probe_robust_selection | followup_selection |
  -- causal_shadow_selection | staged_diagnostic_selection (successors add
  -- sites in code; learnloop.scheduling.voi_forecasts.VOI_SITES).
  site TEXT NOT NULL,
  decision_ref TEXT,
  -- measure | stop | abstain | act | select (the decision's own verdict).
  verdict TEXT NOT NULL,
  learning_object_id TEXT,
  probe_episode_id TEXT,
  presentation_id TEXT,
  source_attempt_id TEXT,
  factor_id TEXT,
  chosen_ref TEXT,
  chosen_practice_item_id TEXT,
  scheduler_candidate_id TEXT,
  candidate_count INTEGER NOT NULL CHECK (candidate_count >= 0),
  eig_nats REAL,
  evsi_point_minutes REAL,
  evsi_lcb_minutes REAL,
  p_action_change REAL CHECK (p_action_change IS NULL OR (p_action_change >= 0 AND p_action_change <= 1)),
  forecast_json TEXT NOT NULL,
  parameters_json TEXT NOT NULL,
  versions_json TEXT NOT NULL,
  forecast_version TEXT NOT NULL,
  algorithm_version TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
