---
title: "assessment_contract_versions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "5298b57ea745a210c54a1d3a8f79637558edd1a1"
source_commit_timestamp: "2026-10-25T16:12:33-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite assessment_contract_versions"
  - "table assessment_contract_versions"
schema_head: 222
table_name: "assessment_contract_versions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "schema-and-change"
introduced_in: "034_assessment_contract_snapshots.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/034_assessment_contract_snapshots.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/material_view.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/db/stores/answered_contracts.py"
  - "src/learnloop/db/stores/observation_ledger.py"
  - "src/learnloop/db/stores/source_service.py"
  - "src/learnloop/db/stores/write_provenance.py"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/attempts/measurement_corrections.py"
  - "src/learnloop/learner/assessment_contracts.py"
  - "src/learnloop/learner/facet_evidence_timeline.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/schema-and-change"
---

# `assessment_contract_versions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins immutable versions of assessment contract so schema changes and reviewed mutations remain reproducible and auditable. It supplies replay-stable input rather than a disposable cache. Rows bind `practice_item_id`, `schema_version`, `contract_hash`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> KM1 (knowledge-model §5.2): immutable assessment-contract snapshots and the observation lineage stamped onto grading evidence. Purely additive: every new grading_evidence column is nullable and unread under legacy algorithm_version, so mvp-0.6 replay reproduces byte-identical derived state.

It belongs to the **schema and change** navigation family. The family context lives in [[Database Catalog#Schema And Change]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/034_assessment_contract_snapshots.sql`.
- **Schema touched by:** `034_assessment_contract_snapshots.sql`, `065_activity_lineage_substrate.sql`, `116_measurement_contract_corrections.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `contract_hash` | `TEXT` | yes | — | — | Stored value |
| `contract_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `schema_version` | `INTEGER` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_assessment_contract_versions_item` on `practice_item_id`.
- `sqlite_autoindex_assessment_contract_versions_2` on `practice_item_id`, `contract_hash` (unique).
- `sqlite_autoindex_assessment_contract_versions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.assessment_contract_versions_for_practice_item()`
- `Repository.ensure_assessment_contract_version()`
- `Repository.fetch_assessment_contract_version()`
- `Repository.fetch_assessment_contract_versions()`
- `Repository.list_all_assessment_contract_versions()`

### Direct SQL readers

- `src/learnloop/adaptive_difficulty/material_view.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/db/stores/answered_contracts.py`
- `src/learnloop/db/stores/observation_ledger.py`
- `src/learnloop/db/stores/source_service.py`
- `src/learnloop/db/stores/write_provenance.py`
- `src/learnloop/evsi_calibration/forecast_report.py`
- `src/learnloop/evsi_calibration/live_report.py`
- `src/learnloop/field/outcomes.py`
- `src/learnloop/field/probability_states.py`
- `src/learnloop/field/workbench_signals.py`
- `src/learnloop/learner_context.py`
- `src/learnloop/learner_protection.py`
- `src/learnloop/placement/state.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/attempts/measurement_corrections.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/learner/assessment_contracts.py`
- `src/learnloop/learner/facet_evidence_timeline.py`
- `src/learnloop/substrate/compat/activity_backfill.py`
- `src/learnloop_sidecar/handlers/serializers.py`
- `src/learnloop_sidecar/handlers/workbench.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/mcp_world.py`
- `tests/test_ad_guard.py`
- `tests/test_ad_protected_readings.py`
- `tests/test_ad_protected_tables.py`
- `tests/test_collection_dataset.py`
- `tests/test_diagnosis_input_provenance_landing.py`
- `tests/test_field_workbench_signals.py`
- `tests/test_mcp_c1a_narrow.py`
- `tests/test_mcp_c1a_review.py`
- `tests/test_mcp_runtime.py`
- `tests/test_reader_workbench_rw2a.py`
- `tests/test_regrade_contract_successor.py`
- `tests/test_required_method_rereview.py`
- `tests/test_required_method_round3_final_verify.py`
- `tests/test_required_method_round3_rereview.py`
- `tests/test_reread_safety_landing.py`
- `tests/test_voi_forecasts.py`
- `tests/test_assessment_contracts.py`
- `tests/test_measurement_corrections.py`
- `tests/test_sidecar_contract.py`

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
CREATE TABLE assessment_contract_versions (
  id TEXT PRIMARY KEY,
  practice_item_id TEXT NOT NULL,
  contract_hash TEXT NOT NULL,
  contract_json TEXT NOT NULL,
  schema_version INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(practice_item_id, contract_hash)
);
```

## Related notes

- [[Database Catalog#Schema And Change|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
