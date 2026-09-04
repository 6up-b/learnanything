---
title: "derived_state_rebuilds"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite derived_state_rebuilds"
  - "table derived_state_rebuilds"
schema_head: 157
table_name: "derived_state_rebuilds"
table_role: "receipt"
functionality_status: "active"
domain_family: "schema-and-change"
introduced_in: "009_derived_state_rebuilds.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/009_derived_state_rebuilds.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/ops/doctor.py"
  - "src/learnloop/ops/vault_upgrade.py"
  - "src/learnloop/substrate/canonical_projection_rollout.py"
  - "src/learnloop/substrate/compat/substrate_cutover.py"
  - "src/learnloop/substrate/p0_projection.py"
  - "src/learnloop/attempts/measurement_corrections.py"
  - "src/learnloop/curriculum/integration_backfill.py"
  - "src/learnloop/learner/learner_review_feed.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/schema-and-change"
---

# `derived_state_rebuilds`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records each explicit derived-state rebuild and the algorithm/projection boundaries used. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `algorithm_version`, `canonical_projection_version`, `coverage_denominator_version`, making the operational relationship explicit. ^table-purpose

It belongs to the **schema and change** navigation family. The family context lives in [[Database Catalog#Schema And Change]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/009_derived_state_rebuilds.sql`.
- **Schema touched by:** `009_derived_state_rebuilds.sql`, `122_causal_activity_events.sql`, `138_coverage_denominator_version.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `scope` | `TEXT` | yes | — | — | Stored value |
| `learning_object_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `rebuilt_learning_objects` | `INTEGER` | yes | — | — | Stored value |
| `replayed_attempts` | `INTEGER` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `canonical_projection_version` | `TEXT` | no | — | — | Stored value |
| `coverage_denominator_version` | `TEXT` | no | — | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_derived_state_rebuilds_latest` on `created_at`, `id`.
- `sqlite_autoindex_derived_state_rebuilds_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.derived_state_rebuild_version_changes()`
- `Repository.latest_canonical_projection_rebuild()`
- `Repository.latest_derived_state_rebuild()`
- `Repository.record_derived_state_rebuild()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/measurement_corrections.py`
- `src/learnloop/curriculum/integration_backfill.py`
- `src/learnloop/learner/learner_review_feed.py`
- `src/learnloop/ops/doctor.py`
- `src/learnloop/substrate/canonical_projection_rollout.py`
- `src/learnloop/substrate/compat/substrate_cutover.py`
- `src/learnloop/substrate/p0_projection.py`
- `src/learnloop/substrate/rebuild_orchestrator.py`
- `src/learnloop/substrate/replay.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_canonical_projection_rollout.py`
- `tests/test_causal_activity_policy.py`
- `tests/test_causal_p2_acceptance.py`
- `tests/test_ingest_instrument_gates.py`
- `tests/test_migrations.py`
- `tests/test_p0_cutover_mvp08.py`
- `tests/test_p0_projection_cutover.py`
- `tests/test_rebuild_orchestrator.py`
- `tests/test_shadow_rebuild.py`
- `tests/test_table_roles.py`
- `tests/test_contract_frontier_coverage.py`
- `tests/test_coverage_denominator_boundary.py`
- `tests/test_learner_review_system_entries.py`
- `tests/test_measurement_corrections.py`
- `tests/test_mvp09_upgrade.py`
- `tests/test_replay.py`
- `tests/test_surfaced_belief_corrections.py`

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
CREATE TABLE derived_state_rebuilds (
  id TEXT PRIMARY KEY,
  scope TEXT NOT NULL,
  learning_object_ids_json TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  rebuilt_learning_objects INTEGER NOT NULL,
  replayed_attempts INTEGER NOT NULL,
  created_at TEXT NOT NULL
, canonical_projection_version TEXT, coverage_denominator_version TEXT);
```

## Related notes

- [[Database Catalog#Schema And Change|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
