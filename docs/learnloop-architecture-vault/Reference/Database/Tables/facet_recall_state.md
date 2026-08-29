---
title: "facet_recall_state"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite facet_recall_state"
  - "table facet_recall_state"
schema_head: 156
table_name: "facet_recall_state"
table_role: "derived"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "037_canonical_facet_state.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/037_canonical_facet_state.sql"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/learner/facet_evidence_timeline.py"
  - "src/learnloop/learner/facet_state_reader.py"
  - "src/learnloop/learner/recall_coverage.py"
  - "src/learnloop/ops/doctor.py"
  - "src/learnloop/sim/metrics.py"
  - "src/learnloop/curriculum/curriculum_locks.py"
  - "src/learnloop/goals/certification_cold_probe.py"
  - "src/learnloop/goals/exam_readiness.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `facet_recall_state`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Materializes canonical per-facet recall evidence and uncertainty for the current knowledge model. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `facet_id`, `practice_item_id`, `algorithm_version`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> KM2 (knowledge-model §7.1): canonical shared facet belief state, the capability-sliced certification ledger, and the pre-lock facet-merge map.  Purely additive. The legacy per-LO `evidence_facet_recall_state` (migration 007) and `facet_uncertainty` (migration 012) are retained read-only for frozen mvp-0.6 replay; these tables receive writes only under the mvp-0.7 algorithm_version. mvp-0.6 replay never touches them, so it reproduces byte-identical derived state. Canonical facet belief state, keyed on the post-alias/post-merge canonical facet id and the observed capability (§7.1). `practice_item_id IS NULL` is the shared aggregate row; a non-null id is a per-item marginal. SQLite UNIQUE permits multiple NULLs, so the two scopes need separate partial unique indexes.

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/037_canonical_facet_state.sql`.
- **Schema touched by:** `037_canonical_facet_state.sql`.
- **Rebuild owner:** `canonical_projection`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `facet_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `capability_key` | `TEXT` | yes | `'shared'` | — | Stored value |
| `practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `recall_alpha` | `REAL` | yes | — | — | Stored value |
| `recall_beta` | `REAL` | yes | — | — | Stored value |
| `recall_mean` | `REAL` | yes | — | — | Stored value |
| `recall_variance` | `REAL` | yes | — | — | Stored value |
| `independent_evidence_mass` | `REAL` | yes | `0` | — | Stored value |
| `raw_coverage_mass` | `REAL` | yes | `0` | — | Stored value |
| `last_observed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `last_error_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `consecutive_failures` | `INTEGER` | yes | `0` | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `facet_recall_item` on `facet_id`, `capability_key`, `practice_item_id` (unique).
- `facet_recall_aggregate` on `facet_id`, `capability_key` (unique).
- `sqlite_autoindex_facet_recall_state_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.canonical_facet_recall_state()`
- `Repository.canonical_facet_recall_states()`
- `Repository.facet_independence_evidence()`
- `Repository.facet_recall_state()`
- `Repository.replace_canonical_facet_state()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/curriculum/curriculum_locks.py`
- `src/learnloop/goals/certification_cold_probe.py`
- `src/learnloop/goals/exam_readiness.py`
- `src/learnloop/learner/facet_evidence_timeline.py`
- `src/learnloop/learner/facet_state_reader.py`
- `src/learnloop/learner/recall_coverage.py`
- `src/learnloop/ops/doctor.py`
- `src/learnloop/sim/metrics.py`
- `src/learnloop/substrate/canonical_projection.py`
- `src/learnloop_sidecar/handlers/facet_detail.py`
- `src/learnloop_sidecar/handlers/knowledge_map.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_deferred_regrade.py`
- `tests/test_doctor.py`
- `tests/test_km2_canonical.py`
- `tests/test_migrations.py`
- `tests/test_rebuild_orchestrator.py`
- `tests/test_recall_coverage_interventions.py`
- `tests/test_replay.py`
- `tests/test_shadow_rebuild.py`
- `tests/test_anti_double_count.py`
- `tests/test_contract_frontier_coverage.py`
- `tests/test_curriculum_locks.py`
- `tests/test_km2_activation.py`
- `tests/test_km2_sim_gates.py`
- `tests/test_km2_write_path.py`
- `tests/test_km2b_consumer_rekey.py`
- `tests/test_measurement_corrections.py`
- `tests/test_projection_evidence_polarity.py`
- `tests/test_receipt_derivation.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.
5. Update the single owner in `DERIVED_STATE_REPLAYERS`, then prove same-version rebuild equivalence and shadow isolation.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE TABLE facet_recall_state (
  id TEXT PRIMARY KEY,
  facet_id TEXT NOT NULL,
  capability_key TEXT NOT NULL DEFAULT 'shared',
  practice_item_id TEXT,
  recall_alpha REAL NOT NULL,
  recall_beta REAL NOT NULL,
  recall_mean REAL NOT NULL,
  recall_variance REAL NOT NULL,
  independent_evidence_mass REAL NOT NULL DEFAULT 0,
  raw_coverage_mass REAL NOT NULL DEFAULT 0,
  last_observed_at TEXT,
  last_error_at TEXT,
  consecutive_failures INTEGER NOT NULL DEFAULT 0,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
