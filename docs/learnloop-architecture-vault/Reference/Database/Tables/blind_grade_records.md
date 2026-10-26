---
title: "blind_grade_records"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "73d7d146740284eca0a5ff26ab53593429e7cc20"
source_commit_timestamp: "2026-10-26T10:42:06-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite blind_grade_records"
  - "table blind_grade_records"
schema_head: 224
table_name: "blind_grade_records"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "170_blind_grading_diagnosis_split.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/170_blind_grading_diagnosis_split.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/attempts/stuck.py"
  - "src/learnloop/daily_plan/router_teach_back.py"
  - "src/learnloop/db/stores/diagnoses.py"
  - "src/learnloop/db/stores/recurrence.py"
  - "src/learnloop/db/stores/write_provenance.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `blind_grade_records`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives blind grade record a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `attempt_id`, `agent_run_id`, `supersedes_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Slice 1 M2 (spec_blind_grading_diagnosis_split_v1 §6.1): the live split between the learner-blind grader and the history-aware diagnoser.  Every model output here is a persisted input: replay reads these ledgers and never calls the grader, the diagnoser or the embedding endpoint (S7). The validated blind grade of one attempt (BlindGradingProposal after the shared validators), as the diagnoser and later diagnoses read it. A regrade appends a successor with supersedes_id; nothing is edited.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/170_blind_grading_diagnosis_split.sql`.
- **Schema touched by:** `170_blind_grading_diagnosis_split.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `agent_run_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `grading_prompt_version` | `TEXT` | yes | — | — | Stored value |
| `output_schema_version` | `TEXT` | yes | — | — | Stored value |
| `context_hash` | `TEXT` | yes | — | — | Stored value |
| `record_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `supersedes_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/blind_grade_records\|blind_grade_records.id]] | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `supersedes_id` → [[Reference/Database/Tables/blind_grade_records|`blind_grade_records.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `blind_grade_records_attempt` on `attempt_id`, `created_at`, `id`.
- `sqlite_autoindex_blind_grade_records_1` on `id` (unique).

Database triggers:

- `blind_grade_records_no_delete` — schema-enforced lifecycle or immutability constraint.
- `blind_grade_records_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/attempts/stuck.py`
- `src/learnloop/daily_plan/router_teach_back.py`
- `src/learnloop/db/stores/diagnoses.py`
- `src/learnloop/db/stores/recurrence.py`
- `src/learnloop/db/stores/write_provenance.py`
- `src/learnloop/diagnosis/split/reports.py`
- `src/learnloop/held_grades.py`
- `src/learnloop/learner_context.py`
- `src/learnloop/placement/state.py`
- `src/learnloop/workbench/help_outcomes.py`
- `src/learnloop_sidecar/handlers/serializers.py`

### Direct SQL writers

- `src/learnloop/db/stores/diagnoses.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_diagnosis_input_provenance.py`
- `tests/test_help_outcomes.py`
- `tests/test_mvp017_route_check_replay.py`
- `tests/test_required_method_grading.py`
- `tests/test_router_r2c_teach_back.py`

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
CREATE TABLE blind_grade_records (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id),
  agent_run_id TEXT,
  grading_prompt_version TEXT NOT NULL,
  output_schema_version TEXT NOT NULL,
  context_hash TEXT NOT NULL,
  record_json TEXT NOT NULL,
  supersedes_id TEXT REFERENCES blind_grade_records(id),
  created_at TEXT NOT NULL,
  CHECK (supersedes_id IS NULL OR supersedes_id != id)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
