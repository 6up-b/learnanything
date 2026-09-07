---
title: "policy_experiment_assignments"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite policy_experiment_assignments"
  - "table policy_experiment_assignments"
schema_head: 157
table_name: "policy_experiment_assignments"
table_role: "receipt"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "098_controller_randomization_and_outcomes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/098_controller_randomization_and_outcomes.sql"
  - "src/learnloop/scheduling/controller_store.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `policy_experiment_assignments`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records governed assignments for policy experiment so queue and controller decisions can resume safely and explain why an activity was selected. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `experiment_id`, `decision_id`, `unit_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/098_controller_randomization_and_outcomes.sql`.
- **Schema touched by:** `098_controller_randomization_and_outcomes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `experiment_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `decision_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/controller_decisions\|controller_decisions.id]] | Stored value |
| `unit_kind` | `TEXT` | yes | — | — | Stored value |
| `unit_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `variant` | `TEXT` | yes | — | — | Stored value |
| `propensity` | `REAL` | yes | — | — | Stored value |
| `seed` | `TEXT` | yes | — | — | Stored value |
| `draw` | `REAL` | no | — | — | Stored value |
| `epsilon_margin` | `REAL` | no | — | — | Stored value |
| `near_equivalent` | `INTEGER` | yes | `0` | — | Stored value |
| `design` | `TEXT` | yes | — | — | Stored value |
| `grade` | `TEXT` | yes | `'experimental'` | — | Stored value |
| `candidate_refs_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `detail_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `decision_id` → [[Reference/Database/Tables/controller_decisions|`controller_decisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_policy_experiment_assignments_decision` on `decision_id`.
- `idx_policy_experiment_assignments_unit` on `unit_kind`, `unit_id`.
- `idx_policy_experiment_assignments_experiment` on `experiment_id`, `created_at`.
- `sqlite_autoindex_policy_experiment_assignments_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/scheduling/controller_store.py`

### Direct SQL writers

- `src/learnloop/scheduling/controller_store.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

No table-specific test contains the table name or a detected repository method call. The schema/role invariants are still pinned by `tests/test_migrations.py` and `tests/test_table_roles.py`.

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
CREATE TABLE policy_experiment_assignments (
  id TEXT PRIMARY KEY,
  experiment_id TEXT NOT NULL,
  decision_id TEXT REFERENCES controller_decisions(id),
  -- The experimental unit. At n=1 a durable intervention randomizes the COMMITMENT,
  -- not time; a reversible near-equivalent decision randomizes the decision itself.
  unit_kind TEXT NOT NULL CHECK (unit_kind IN ('decision', 'commitment')),
  unit_id TEXT,
  variant TEXT NOT NULL,
  -- The true assignment probability of `variant` (logged before selection, §9.3).
  propensity REAL NOT NULL CHECK (propensity >= 0.0 AND propensity <= 1.0),
  -- Deterministic draw provenance: seed + drawn value replay the assignment exactly.
  seed TEXT NOT NULL,
  draw REAL,
  -- The declared near-equivalence margin the decision fell within (epsilon tie-break),
  -- NULL for a non-tie MRT/commitment assignment.
  epsilon_margin REAL,
  near_equivalent INTEGER NOT NULL DEFAULT 0 CHECK (near_equivalent IN (0, 1)),
  design TEXT NOT NULL
    CHECK (design IN ('mrt_reversible', 'epsilon_tiebreak', 'commitment_parallel')),
  -- 'experimental' = a valid randomization design; 'hypothesis_grade' = an intervention
  -- with unmodeled carryover that stays hypothesis-grade regardless of accumulated data.
  grade TEXT NOT NULL DEFAULT 'experimental'
    CHECK (grade IN ('experimental', 'hypothesis_grade')),
  candidate_refs_json TEXT NOT NULL DEFAULT '[]',
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
