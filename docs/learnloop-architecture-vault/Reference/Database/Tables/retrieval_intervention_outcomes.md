---
title: "retrieval_intervention_outcomes"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "ceb81f7f731f136a2e4800fe5aef7a747c3739b2"
source_commit_timestamp: "2026-10-21T09:51:57-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite retrieval_intervention_outcomes"
  - "table retrieval_intervention_outcomes"
schema_head: 216
table_name: "retrieval_intervention_outcomes"
table_role: "derived"
functionality_status: "active"
domain_family: "operations"
introduced_in: "193_retrieval_interventions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/193_retrieval_interventions.sql"
  - "src/learnloop/db/stores/source_service.py"
  - "src/learnloop/substrate/intervention_outcomes.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `retrieval_intervention_outcomes`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Materializes the outcome join for retrieval_interventions (canonical sources S5): R_next within the session or day, R_cold as the decision-value outcome states (pending stays right-censored), the observed bucket beside the predicted one, actual beside predicted minutes and the learner's taps. Rebuilt by its one replayer from persisted rows with no model call; associations, not causes. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `intervention_id`, `next_attempt_id`, `cold_attempt_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> The outcome join (DERIVED; exactly one replayer, zero model calls, persisted rows only). Pending outcomes stay right-censored, never failures.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/193_retrieval_interventions.sql`.
- **Schema touched by:** `193_retrieval_interventions.sql`.
- **Rebuild owner:** `retrieval_intervention_outcomes`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `intervention_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `as_of` | `TEXT` | no | — | — | Stored value |
| `next_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `next_correctness` | `REAL` | no | — | — | Stored value |
| `next_assisted` | `INTEGER` | no | — | — | Stored value |
| `next_window` | `TEXT` | no | — | — | Stored value |
| `cold_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `cold_outcome_state` | `TEXT` | yes | — | — | Stored value |
| `cold_correctness` | `REAL` | no | — | — | Stored value |
| `observed_bucket` | `TEXT` | no | — | — | Stored value |
| `predicted_outcomes_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `predicted_minutes` | `REAL` | no | — | — | Stored value |
| `actual_minutes` | `REAL` | no | — | — | Stored value |
| `hypothesis_movement_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `learner_signals_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `action_before` | `TEXT` | no | — | — | Stored value |
| `action_after` | `TEXT` | no | — | — | Stored value |
| `action_flipped` | `INTEGER` | no | — | — | Stored value |
| `outcome_version` | `TEXT` | yes | — | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_retrieval_intervention_outcomes_1` on `intervention_id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/source_service.py`

### Direct SQL writers

- `src/learnloop/db/stores/source_service.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_intervention_outcomes_replayer.py`
- `tests/test_rebuild_orchestrator.py`

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
CREATE TABLE retrieval_intervention_outcomes (
  intervention_id TEXT PRIMARY KEY,
  as_of TEXT,
  next_attempt_id TEXT,
  next_correctness REAL,
  next_assisted INTEGER,
  next_window TEXT,
  cold_attempt_id TEXT,
  cold_outcome_state TEXT NOT NULL,
  cold_correctness REAL,
  observed_bucket TEXT,
  predicted_outcomes_json TEXT,
  predicted_minutes REAL,
  actual_minutes REAL,
  hypothesis_movement_json TEXT NOT NULL DEFAULT '{}',
  learner_signals_json TEXT NOT NULL DEFAULT '[]',
  action_before TEXT,
  action_after TEXT,
  action_flipped INTEGER,
  outcome_version TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
