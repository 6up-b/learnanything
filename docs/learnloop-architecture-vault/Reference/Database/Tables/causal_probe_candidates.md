---
title: "causal_probe_candidates"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite causal_probe_candidates"
  - "table causal_probe_candidates"
schema_head: 156
table_name: "causal_probe_candidates"
table_role: "workflow"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "121_causal_probe_coherence.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/121_causal_probe_coherence.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_probe_coherence.py"
  - "src/learnloop/diagnosis/causal_probe_commissioning.py"
  - "src/learnloop_sidecar/handlers/app.py"
  - "src/learnloop/diagnosis/causal_health.py"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `causal_probe_candidates`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Holds candidates for causal probe while policy selects or reviews one so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `factor_id`, `practice_item_id`, `hypothesis_set_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/121_causal_probe_coherence.sql`.
- **Schema touched by:** `121_causal_probe_coherence.sql`, `123_causal_prior_basis.sql`, `140_causal_probe_blind_input_contract.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `factor_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/unresolved_cause_factors\|unresolved_cause_factors.id]] | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `hypothesis_set_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/hypothesis_sets\|hypothesis_sets.id]] | Stored value |
| `manipulation_audit_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/probe_manipulation_audits\|probe_manipulation_audits.id]] | Stored value |
| `measurement_contract_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `blind_bundle_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `discrimination_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | — | — | Stored value |
| `reviewer` | `TEXT` | no | — | — | Stored value |
| `review_reason` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `blind_input_contract_version` | `TEXT` | no | — | — | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `manipulation_audit_id` → [[Reference/Database/Tables/probe_manipulation_audits|`probe_manipulation_audits.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `hypothesis_set_id` → [[Reference/Database/Tables/hypothesis_sets|`hypothesis_sets.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `factor_id` → [[Reference/Database/Tables/unresolved_cause_factors|`unresolved_cause_factors.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_causal_probe_candidate_item` on `practice_item_id`, `status`, `created_at`, `id`.
- `idx_causal_probe_candidate_factor` on `factor_id`, `status`, `created_at`, `id`.
- `sqlite_autoindex_causal_probe_candidates_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.causal_probe_candidate()`
- `Repository.causal_probe_candidates_for_factor()`
- `Repository.insert_causal_probe_candidate()`
- `Repository.update_causal_probe_candidate()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop_sidecar/handlers/app.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_health.py`
- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/causal_probe_coherence.py`
- `src/learnloop/diagnosis/causal_probe_commissioning.py`
- `src/learnloop/diagnosis/causal_selection_audit.py`
- `src/learnloop_sidecar/handlers/measurement.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_orchestrator.py`
- `tests/test_causal_probe_commissioning.py`
- `tests/test_causal_shadow_selection.py`

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
CREATE TABLE causal_probe_candidates (
  id TEXT PRIMARY KEY,
  factor_id TEXT NOT NULL REFERENCES unresolved_cause_factors(id),
  practice_item_id TEXT NOT NULL,
  hypothesis_set_id TEXT NOT NULL REFERENCES hypothesis_sets(id),
  manipulation_audit_id TEXT NOT NULL REFERENCES probe_manipulation_audits(id),
  measurement_contract_json TEXT NOT NULL,
  blind_bundle_ids_json TEXT NOT NULL,
  discrimination_json TEXT,
  status TEXT NOT NULL CHECK (
    status IN ('candidate', 'registered', 'reviewed', 'active', 'rejected')
  ),
  reviewer TEXT,
  review_reason TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
, blind_input_contract_version TEXT);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
