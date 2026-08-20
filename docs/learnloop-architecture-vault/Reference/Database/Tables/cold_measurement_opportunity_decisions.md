---
title: "cold_measurement_opportunity_decisions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite cold_measurement_opportunity_decisions"
  - "table cold_measurement_opportunity_decisions"
schema_head: 156
table_name: "cold_measurement_opportunity_decisions"
table_role: "receipt"
functionality_status: "active"
domain_family: "goals-and-exams"
introduced_in: "151_cold_measurement_opportunities.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/151_cold_measurement_opportunities.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/remediation.py"
  - "src/learnloop/goals/certification_cold_probe.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/goals-and-exams"
---

# `cold_measurement_opportunity_decisions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives cold measurement opportunity decision a stable database identity so goal progress and held-out certification remain tied to the contract and evidence that produced them. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `measurement_opportunity_id`, `followup_task_id`, `selected_item_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **goals and exams** navigation family. The family context lives in [[Database Catalog#Goals And Exams]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/151_cold_measurement_opportunities.sql`.
- **Schema touched by:** `151_cold_measurement_opportunities.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `measurement_opportunity_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/cold_measurement_opportunities\|cold_measurement_opportunities.id]] | Stored value |
| `decision` | `TEXT` | yes | — | — | Stored value |
| `reason` | `TEXT` | yes | — | — | Stored value |
| `followup_task_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `selected_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `candidate_summary_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `scheduled_not_before` | `TEXT` | no | — | — | Stored value |
| `scheduled_expires_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `measurement_opportunity_id` → [[Reference/Database/Tables/cold_measurement_opportunities|`cold_measurement_opportunities.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_cold_measurement_opportunity_decisions_outcome` on `decision`, `created_at`, `id`.
- `sqlite_autoindex_cold_measurement_opportunity_decisions_2` on `measurement_opportunity_id` (unique).
- `sqlite_autoindex_cold_measurement_opportunity_decisions_1` on `id` (unique).

Database triggers:

- `cold_measurement_opportunity_decisions_no_delete` — schema-enforced lifecycle or immutability constraint.
- `cold_measurement_opportunity_decisions_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.cold_measurement_opportunity_decision()`
- `Repository.create_followup_task()`
- `Repository.record_cold_measurement_opportunity_decision()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/remediation.py`
- `src/learnloop/goals/certification_cold_probe.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`
- `tests/test_causal_cold_outcomes.py`
- `tests/test_certification_cold_probe.py`
- `tests/test_coldness_receipt.py`
- `tests/test_diagnostic_probe_freshness.py`
- `tests/test_followup_diagnostic_selection.py`
- `tests/test_instrument_servability_journeys.py`
- `tests/test_item_authoring.py`
- `tests/test_scheduler.py`

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
CREATE TABLE cold_measurement_opportunity_decisions (
  id TEXT PRIMARY KEY,
  measurement_opportunity_id TEXT NOT NULL
    REFERENCES cold_measurement_opportunities(id),
  decision TEXT NOT NULL CHECK (
    decision IN (
      'scheduled',
      'structurally_refused',
      'policy_refused',
      'operationally_unavailable',
      'learner_declined'
    )
  ),
  reason TEXT NOT NULL,
  followup_task_id TEXT,
  selected_item_id TEXT,
  candidate_summary_json TEXT NOT NULL DEFAULT '{}',
  scheduled_not_before TEXT,
  scheduled_expires_at TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(measurement_opportunity_id)
);
```

## Related notes

- [[Database Catalog#Goals And Exams|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
