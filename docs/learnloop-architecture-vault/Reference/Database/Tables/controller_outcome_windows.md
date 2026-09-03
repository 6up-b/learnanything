---
title: "controller_outcome_windows"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite controller_outcome_windows"
  - "table controller_outcome_windows"
schema_head: 157
table_name: "controller_outcome_windows"
table_role: "workflow"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "098_controller_randomization_and_outcomes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/098_controller_randomization_and_outcomes.sql"
  - "src/learnloop/scheduling/controller_store.py"
  - "src/learnloop/scheduling/prequential.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `controller_outcome_windows`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives controller outcome window a stable database identity so queue and controller decisions can resume safely and explain why an activity was selected. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `decision_id`, `assignment_id`, `commitment_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> A delayed outcome window (§3.2, §9.3). Opened when a decision commits an administration whose effect must be read at the NEXT SPACED COLD REVIEW of the affected card -- never at end-of-session. `anchor_kind` names the event the window is anchored to; `due_at` is the expected next cold review; `status` moves pending -> resolved (a qualifying cold observation landed) or censored (never resolved).

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/098_controller_randomization_and_outcomes.sql`.
- **Schema touched by:** `098_controller_randomization_and_outcomes.sql`, `100_kinship_kernel_and_shadow_components.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `decision_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/controller_decisions\|controller_decisions.id]] | Stored value |
| `assignment_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/policy_experiment_assignments\|policy_experiment_assignments.id]] | Stored value |
| `candidate_ref` | `TEXT` | no | — | — | Stored value |
| `commitment_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `card_ref` | `TEXT` | no | — | — | Stored value |
| `horizon_kind` | `TEXT` | yes | `'next_spaced_cold_review'` | — | Stored value |
| `anchor_kind` | `TEXT` | yes | — | — | Stored value |
| `anchor_ref` | `TEXT` | no | — | — | Stored value |
| `opened_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `due_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `resolved_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `outcome_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | `'pending'` | — | Stored value |
| `hypothesis_grade` | `INTEGER` | yes | `0` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `assignment_id` → [[Reference/Database/Tables/policy_experiment_assignments|`policy_experiment_assignments.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `decision_id` → [[Reference/Database/Tables/controller_decisions|`controller_decisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_controller_outcome_windows_card` on `card_ref`, `status`.
- `idx_controller_outcome_windows_status` on `status`, `due_at`.
- `idx_controller_outcome_windows_decision` on `decision_id`.
- `sqlite_autoindex_controller_outcome_windows_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/scheduling/controller_store.py`
- `src/learnloop/scheduling/prequential.py`

### Direct SQL writers

- `src/learnloop/scheduling/controller_store.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_prequential.py`

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
CREATE TABLE controller_outcome_windows (
  id TEXT PRIMARY KEY,
  decision_id TEXT REFERENCES controller_decisions(id),
  assignment_id TEXT REFERENCES policy_experiment_assignments(id),
  candidate_ref TEXT,
  commitment_id TEXT,
  card_ref TEXT,
  -- The horizon is the next spaced cold review (invariant across the layer, §9.3).
  horizon_kind TEXT NOT NULL DEFAULT 'next_spaced_cold_review'
    CHECK (horizon_kind IN ('next_spaced_cold_review')),
  anchor_kind TEXT NOT NULL,
  anchor_ref TEXT,
  opened_at TEXT NOT NULL,
  due_at TEXT,
  resolved_at TEXT,
  -- Burden is co-primary; immediate accuracy is secondary telemetry only (§9.3).
  outcome_json TEXT,
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'resolved', 'censored')),
  -- An unmodeled-carryover intervention's window is hypothesis-grade (label enforced).
  hypothesis_grade INTEGER NOT NULL DEFAULT 0 CHECK (hypothesis_grade IN (0, 1)),
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
