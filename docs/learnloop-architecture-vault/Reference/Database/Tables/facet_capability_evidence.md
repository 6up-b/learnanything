---
title: "facet_capability_evidence"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite facet_capability_evidence"
  - "table facet_capability_evidence"
schema_head: 156
table_name: "facet_capability_evidence"
table_role: "derived"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "037_canonical_facet_state.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/037_canonical_facet_state.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/scoreboard.py"
  - "src/learnloop/goals/certification_cold_probe.py"
  - "src/learnloop/goals/goal_certification.py"
  - "src/learnloop/learner/mastery.py"
  - "src/learnloop/substrate/canonical_projection.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
  - "src/learnloop/attempts/trace_evidence.py"
  - "src/learnloop/content/synthesis/coverage_rollup.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `facet_capability_evidence`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Materializes canonical evidence contributions from facets into capabilities. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `facet_id`, `algorithm_version`, `capability`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Replayable cache derived from immutable criterion observations: positive and negative mass split by direct/embedded relationship, bounded certification credit, and the set of independent surface/correlation groups seen so far (JSON list) per (facet, capability). Not a new evidence source (§7.1).

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/037_canonical_facet_state.sql`.
- **Schema touched by:** `037_canonical_facet_state.sql`, `141_conjunctive_instruments.sql`.
- **Rebuild owner:** `canonical_projection`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `facet_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `capability` | `TEXT` | yes | — | — | Stored value |
| `direct_positive_mass` | `REAL` | yes | `0` | — | Stored value |
| `direct_negative_mass` | `REAL` | yes | `0` | — | Stored value |
| `embedded_positive_mass` | `REAL` | yes | `0` | — | Stored value |
| `embedded_negative_mass` | `REAL` | yes | `0` | — | Stored value |
| `certification_credit` | `REAL` | yes | `0` | — | Stored value |
| `independent_surface_groups_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `direct_certification_credit` | `REAL` | yes | `0` | — | Stored value |
| `embedded_certification_credit` | `REAL` | yes | `0` | — | Stored value |
| `unexercised_supporting_mass` | `REAL` | yes | `0` | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_facet_capability_evidence_1` on `facet_id`, `capability` (unique).

## Who calls it

### Repository access surface

- `Repository.facet_capability_evidence()`
- `Repository.facet_capability_evidence_all()`
- `Repository.facet_capability_evidence_for_facet()`
- `Repository.replace_canonical_facet_state()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/trace_evidence.py`
- `src/learnloop/content/synthesis/coverage_rollup.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/scoreboard.py`
- `src/learnloop/goals/certification_cold_probe.py`
- `src/learnloop/goals/exam_readiness.py`
- `src/learnloop/goals/goal_certification.py`
- `src/learnloop/learner/capability_grid.py`
- `src/learnloop/learner/facet_diagnostics.py`
- `src/learnloop/learner/residual_diagnostics.py`
- `src/learnloop/ops/vault_upgrade.py`
- `src/learnloop/substrate/canonical_projection.py`
- `src/learnloop_sidecar/handlers/facet_detail.py`
- `src/learnloop_sidecar/handlers/knowledge_map.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_anti_double_count.py`
- `tests/test_coverage_rollup.py`
- `tests/test_km2_sim_gates.py`
- `tests/test_km2_write_path.py`
- `tests/test_migrations.py`
- `tests/test_rebuild_orchestrator.py`
- `tests/test_scoreboard.py`
- `tests/test_characterization_certification_ledger.py`
- `tests/test_conjunctive_instruments.py`
- `tests/test_contract_frontier_coverage.py`
- `tests/test_curriculum_locks.py`
- `tests/test_error_hunt_items.py`
- `tests/test_exam_session.py`
- `tests/test_grading_cli.py`
- `tests/test_km2_activation.py`
- `tests/test_km2_canonical.py`
- `tests/test_observation_ledger_bulk.py`
- `tests/test_p0_cutover_mvp08.py`
- `tests/test_p0_projection_cutover.py`
- `tests/test_probe_episodes.py`

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
CREATE TABLE facet_capability_evidence (
  facet_id TEXT NOT NULL,
  capability TEXT NOT NULL,
  direct_positive_mass REAL NOT NULL DEFAULT 0,
  direct_negative_mass REAL NOT NULL DEFAULT 0,
  embedded_positive_mass REAL NOT NULL DEFAULT 0,
  embedded_negative_mass REAL NOT NULL DEFAULT 0,
  certification_credit REAL NOT NULL DEFAULT 0,
  independent_surface_groups_json TEXT NOT NULL DEFAULT '[]',
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL, direct_certification_credit REAL NOT NULL DEFAULT 0, embedded_certification_credit REAL NOT NULL DEFAULT 0, unexercised_supporting_mass REAL NOT NULL DEFAULT 0,
  UNIQUE(facet_id, capability)
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
