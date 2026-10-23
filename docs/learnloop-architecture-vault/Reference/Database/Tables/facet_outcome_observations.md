---
title: "facet_outcome_observations"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "26923e913a375e196f5d1fcef869d143401bf453"
source_commit_timestamp: "2026-10-22T17:12:57-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite facet_outcome_observations"
  - "table facet_outcome_observations"
schema_head: 214
table_name: "facet_outcome_observations"
table_role: "derived"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "167_learner_field_outcomes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/167_learner_field_outcomes.sql"
  - "src/learnloop/db/stores/field.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `facet_outcome_observations`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records observations used to evaluate facet outcome so learner-facing mastery and capability decisions use a reproducible evidence projection. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `attempt_id`, `facet_id`, `practice_item_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> F1 derived read model. No live policy or evidence changes.

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/167_learner_field_outcomes.sql`.
- **Schema touched by:** `167_learner_field_outcomes.sql`, `180_daily_plans.sql`.
- **Rebuild owner:** `field_outcomes`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `attempt_id` | `TEXT` | yes | — | PRIMARY KEY | Stored value |
| `facet_id` | `TEXT` | yes | — | PRIMARY KEY | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `item_snapshot_hash` | `TEXT` | no | — | — | Stored value |
| `revision_status` | `TEXT` | yes | — | — | Stored value |
| `observed_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `outcome` | `REAL` | yes | — | — | Stored value |
| `facet_share` | `REAL` | yes | — | — | Stored value |
| `effective_mass` | `REAL` | yes | — | — | Stored value |
| `cold` | `INTEGER` | yes | — | — | Stored value |
| `assisted` | `INTEGER` | yes | — | — | Stored value |
| `primed` | `INTEGER` | yes | — | — | Stored value |
| `surface_group_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `serving_origin` | `TEXT` | yes | — | — | Stored value |
| `serving_propensity` | `REAL` | no | — | — | Stored value |
| `scheduler_candidate_id` | `TEXT` | no | — | — | Application-validated soft reference |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `facet_outcome_observations_time` on `observed_at`, `attempt_id`.
- `sqlite_autoindex_facet_outcome_observations_1` on `attempt_id`, `facet_id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/field.py`

### Direct SQL writers

- `src/learnloop/db/stores/field.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_daily_plan_composition.py`
- `tests/test_daily_plan_owner_decisions.py`
- `tests/test_facet_outcome_view.py`
- `tests/test_held_grade_composition.py`
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
CREATE TABLE "facet_outcome_observations" (
  attempt_id TEXT NOT NULL,
  facet_id TEXT NOT NULL,
  practice_item_id TEXT NOT NULL,
  item_snapshot_hash TEXT,
  revision_status TEXT NOT NULL CHECK (revision_status IN ('exact','reconstructed_current','excluded')),
  observed_at TEXT NOT NULL,
  outcome REAL NOT NULL CHECK (outcome BETWEEN 0 AND 1),
  facet_share REAL NOT NULL CHECK (facet_share > 0 AND facet_share <= 1),
  effective_mass REAL NOT NULL CHECK (effective_mass >= 0),
  cold INTEGER NOT NULL CHECK (cold IN (0,1)),
  assisted INTEGER NOT NULL CHECK (assisted IN (0,1)),
  primed INTEGER NOT NULL CHECK (primed IN (0,1)),
  surface_group_id TEXT,
  serving_origin TEXT NOT NULL CHECK (serving_origin IN ('learner_pick','system_probe','forced_followup','requested','daily_plan','unknown')),
  serving_propensity REAL CHECK (serving_propensity IS NULL OR serving_propensity BETWEEN 0 AND 1),
  scheduler_candidate_id TEXT,
  PRIMARY KEY (attempt_id, facet_id)
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
