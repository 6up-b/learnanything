---
title: "decision_features"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite decision_features"
  - "table decision_features"
schema_head: 156
table_name: "decision_features"
table_role: "receipt"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "011_training_dataset_logging.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/011_training_dataset_logging.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/tutor/promotions.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_migration.py"
  - "src/learnloop/diagnosis/followups.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `decision_features`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives decision feature a stable database identity so queue and controller decisions can resume safely and explain why an activity was selected. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `decision_id`, `decision_type`, `algorithm_version`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Training-dataset logging (spec_training_dataset_architecture.md §3.2, §3.3). Makes the scheduler decision log trainable by (1) freezing the decision-time feature inputs that are otherwise recomputed live, and (2) recording the selection propensity needed for off-policy estimation. No live algorithm behavior changes; these are append-only logging additions. (§3.2) Frozen decision-time feature snapshots. decision_id is a soft reference whose target table depends on decision_type: 'selection' -> scheduler_slate_candidates.id, 'probe' -> elicitation_events.id, 'grading' -> practice_attempts.id. No FK: the application validates the reference, matching the soft-reference convention.

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/011_training_dataset_logging.sql`.
- **Schema touched by:** `011_training_dataset_logging.sql`, `012_facet_diagnostic_state.sql`, `027_question_promotions.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `decision_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `decision_type` | `TEXT` | yes | — | — | Stored value |
| `ability_vector_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `item_demand_vector_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `context_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_decision_features_type_time` on `decision_type`, `created_at`.
- `sqlite_autoindex_decision_features_2` on `decision_id`, `decision_type` (unique).
- `sqlite_autoindex_decision_features_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.decision_features()`
- `Repository.find_record()`
- `Repository.record_decision_features()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/diagnosis/followups.py`
- `src/learnloop/tutor/promotions.py`
- `src/learnloop_sidecar/handlers/inspector.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_facet_diagnostics_v03.py`
- `tests/test_instrument_servability_journeys.py`
- `tests/test_migrations.py`
- `tests/test_misconception_routing.py`
- `tests/test_predictive_eig.py`
- `tests/test_question_promotions.py`
- `tests/test_tutor_promotion_service.py`
- `tests/test_agent_runs.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_show.py`
- `tests/test_source_ingestion.py`

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
CREATE TABLE "decision_features" (
  id TEXT PRIMARY KEY,
  decision_id TEXT NOT NULL,
  decision_type TEXT NOT NULL CHECK (
    decision_type IN ('selection', 'probe', 'grading', 'followup', 'question_promotion')
  ),
  ability_vector_json TEXT NOT NULL,
  item_demand_vector_json TEXT,
  context_json TEXT,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (decision_id, decision_type)
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
