---
title: "diagnosis_feedback"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "4108e1ccd58b61e131ea0d5eae57ccce7e08c4ef"
source_commit_timestamp: "2026-10-14T15:56:42-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite diagnosis_feedback"
  - "table diagnosis_feedback"
schema_head: 202
table_name: "diagnosis_feedback"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "170_blind_grading_diagnosis_split.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/170_blind_grading_diagnosis_split.sql"
  - "src/learnloop/db/stores/diagnoses.py"
  - "src/learnloop/db/stores/recurrence.py"
  - "src/learnloop/diagnosis/recurrence/report.py"
  - "src/learnloop/diagnosis/split/card.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `diagnosis_feedback`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives diagnosis feedback a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `diagnosis_id`, `attempt_id`, `cited_attempt_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> M2 diagnosis-card taps (§12.2). Eval only: confers no support authority.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/170_blind_grading_diagnosis_split.sql`.
- **Schema touched by:** `170_blind_grading_diagnosis_split.sql`, `176_recurrence_groups.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `diagnosis_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/attempt_diagnoses\|attempt_diagnoses.id]] | Stored value |
| `attempt_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `response` | `TEXT` | yes | — | — | Stored value |
| `cited_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `forwarded_factor_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `shown_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `responded_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `diagnosis_id` → [[Reference/Database/Tables/attempt_diagnoses|`attempt_diagnoses.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `diagnosis_feedback_diagnosis` on `diagnosis_id`, `responded_at`.
- `sqlite_autoindex_diagnosis_feedback_1` on `id` (unique).

Database triggers:

- `diagnosis_feedback_no_delete` — schema-enforced lifecycle or immutability constraint.
- `diagnosis_feedback_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/diagnoses.py`
- `src/learnloop/db/stores/recurrence.py`
- `src/learnloop/diagnosis/recurrence/report.py`

### Direct SQL writers

- `src/learnloop/db/stores/diagnoses.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_recurrence_live.py`

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
CREATE TABLE "diagnosis_feedback" (
  id TEXT PRIMARY KEY,
  diagnosis_id TEXT NOT NULL REFERENCES attempt_diagnoses(id),
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id),
  response TEXT NOT NULL CHECK (
    response IN (
      'believed_candidate', 'partly', 'slipped', 'diagnosis_wrong', 'unsure', 'not_same_mistake',
      'escalation:helped', 'escalation:didnt_help', 'escalation:not_sure'
    )
  ),
  cited_attempt_id TEXT,
  forwarded_factor_id TEXT,
  shown_at TEXT,
  responded_at TEXT NOT NULL,
  CHECK ((response = 'not_same_mistake') = (cited_attempt_id IS NOT NULL))
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
