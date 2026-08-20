---
title: "cold_measurement_opportunities"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite cold_measurement_opportunities"
  - "table cold_measurement_opportunities"
schema_head: 156
table_name: "cold_measurement_opportunities"
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

# `cold_measurement_opportunities`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records the denominator of available opportunities for cold measurement so goal progress and held-out certification remain tied to the contract and evidence that produced them. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `learning_object_id`, `remediation_episode_id`, `source_attempt_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Durable cold-measurement opportunities and receipt lineage.  A cold measurement starts before an item is selected.  Recording only the scheduled task loses every refused opportunity and makes selection availability look like learner performance.  The base row therefore records that an opportunity existed; exactly one append-only decision records how it terminated:  scheduled | structurally_refused | policy_refused | operationally_unavailable | learner_declined  Administration/final receipts and scheduled tasks are children of that opportunity.  A crash between creation and decision leaves an honest undecided opportunity rather than silently erasing the denominator.

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
| `lane` | `TEXT` | yes | — | — | Stored value |
| `trigger_kind` | `TEXT` | yes | — | — | Stored value |
| `trigger_ref` | `TEXT` | yes | — | — | Stored value |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `case_kind` | `TEXT` | no | — | — | Stored value |
| `case_ref` | `TEXT` | no | — | — | Stored value |
| `remediation_episode_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `source_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `certificate_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `policy_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_cold_measurement_opportunities_lane_lo` on `lane`, `learning_object_id`, `created_at`, `id`.
- `sqlite_autoindex_cold_measurement_opportunities_2` on `lane`, `trigger_kind`, `trigger_ref` (unique).
- `sqlite_autoindex_cold_measurement_opportunities_1` on `id` (unique).

Database triggers:

- `cold_measurement_opportunities_no_delete` — schema-enforced lifecycle or immutability constraint.
- `cold_measurement_opportunities_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.cold_measurement_opportunity()`
- `Repository.get_or_create_cold_measurement_opportunity()`

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

- `tests/test_causal_cold_outcomes.py`
- `tests/test_migrations.py`
- `tests/test_certification_cold_probe.py`

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
CREATE TABLE cold_measurement_opportunities (
  id TEXT PRIMARY KEY,
  lane TEXT NOT NULL,
  trigger_kind TEXT NOT NULL,
  trigger_ref TEXT NOT NULL,
  learning_object_id TEXT,
  case_kind TEXT,
  case_ref TEXT,
  remediation_episode_id TEXT,
  source_attempt_id TEXT,
  certificate_id TEXT,
  policy_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(lane, trigger_kind, trigger_ref)
);
```

## Related notes

- [[Database Catalog#Goals And Exams|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
