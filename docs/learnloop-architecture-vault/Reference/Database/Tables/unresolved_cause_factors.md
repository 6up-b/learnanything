---
title: "unresolved_cause_factors"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite unresolved_cause_factors"
  - "table unresolved_cause_factors"
schema_head: 157
table_name: "unresolved_cause_factors"
table_role: "workflow"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "034_assessment_contract_snapshots.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/034_assessment_contract_snapshots.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_factor_deferral.py"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
  - "src/learnloop/diagnosis/causal_selection_audit.py"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_health.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `unresolved_cause_factors`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives unresolved cause factor a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `attempt_id`, `observation_id`, `resolution_kind`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/034_assessment_contract_snapshots.sql`.
- **Schema touched by:** `034_assessment_contract_snapshots.sql`, `115_causal_attribution_p0.sql`, `121_causal_probe_coherence.sql`, `148_factor_deferral_labels.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `observation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `candidate_causes_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | — | — | Stored value |
| `resolution_observation_ids_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `resolution_kind` | `TEXT` | no | — | — | Stored value |
| `resolution_detail_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_unresolved_cause_factors_status` on `status`.
- `idx_unresolved_cause_factors_attempt` on `attempt_id`.
- `sqlite_autoindex_unresolved_cause_factors_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.close_unresolved_cause_factor()`
- `Repository.insert_unresolved_cause_factor()`
- `Repository.open_unresolved_cause_factors()`
- `Repository.open_unresolved_cause_observation_ids()`
- `Repository.resolve_unresolved_cause_factor()`
- `Repository.retire_unresolved_cause_factor()`
- `Repository.set_unresolved_cause_hypothesis_refs()`
- `Repository.unresolved_cause_factor()`
- `Repository.unresolved_cause_factors()`
- `Repository.unresolved_cause_factors_for_attempt()`
- `Repository.unresolved_cause_observation_ids()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_factor_deferral.py`
- `src/learnloop/diagnosis/causal_health.py`
- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/causal_probe_coherence.py`
- `src/learnloop/diagnosis/causal_probe_commissioning.py`
- `src/learnloop/diagnosis/causal_selection_audit.py`
- `src/learnloop/diagnosis/diagnosis_adjudication.py`
- `src/learnloop/diagnosis/followups.py`
- `src/learnloop/diagnosis/misconceptions.py`
- `src/learnloop/diagnosis/probe_targeting.py`
- `src/learnloop/substrate/canonical_projection.py`
- `src/learnloop/tutor/tutor_qa.py`
- `src/learnloop_sidecar/handlers/feedback.py`
- `src/learnloop_sidecar/handlers/knowledge_map.py`
- `src/learnloop_sidecar/handlers/measurement.py`
- `src/learnloop_sidecar/handlers/serializers.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_factor_deferral.py`
- `tests/test_anti_double_count.py`
- `tests/test_causal_attribution_p0.py`
- `tests/test_causal_attribution_p1.py`
- `tests/test_causal_attribution_p2.py`
- `tests/test_causal_orchestrator.py`
- `tests/test_causal_p2_acceptance.py`
- `tests/test_causal_probe_commissioning.py`
- `tests/test_causal_repair_mapping_p2.py`
- `tests/test_causal_shadow_selection.py`
- `tests/test_common_repair_delivery.py`
- `tests/test_conjunctive_instruments.py`
- `tests/test_dialogue_causal_join.py`
- `tests/test_durable_promotion_arms.py`
- `tests/test_km2_write_path.py`
- `tests/test_km4_taxonomy.py`
- `tests/test_probe_block_end.py`
- `tests/test_projection_evidence_polarity.py`
- `tests/test_unresolved_cause_gate.py`

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
CREATE TABLE unresolved_cause_factors (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL,
  observation_id TEXT,
  candidate_causes_json TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('open', 'resolved', 'retired')),
  resolution_observation_ids_json TEXT,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
, resolution_kind TEXT, resolution_detail_json TEXT);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
