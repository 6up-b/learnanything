---
title: "diagnostic_eval_cases"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite diagnostic_eval_cases"
  - "table diagnostic_eval_cases"
schema_head: 156
table_name: "diagnostic_eval_cases"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "144_diagnostic_augmentation.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/144_diagnostic_augmentation.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/diagnostic_augmentation.py"
  - "src/learnloop/diagnosis/scoreboard.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `diagnostic_eval_cases`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives diagnostic eval case a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `run_id`, `attempt_id`, `practice_item_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/144_diagnostic_augmentation.sql`.
- **Schema touched by:** `144_diagnostic_augmentation.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `run_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/diagnostic_eval_runs\|diagnostic_eval_runs.id]] | Stored value |
| `case_key` | `TEXT` | yes | — | — | Stored value |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `regression_shape` | `TEXT` | yes | — | — | Stored value |
| `source` | `TEXT` | yes | — | — | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `profile_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `learner_trace_md` | `TEXT` | yes | — | — | Stored value |
| `planted_should_abstain` | `INTEGER` | yes | — | — | Stored value |
| `planted_anchor_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `planted_anchor_key` | `TEXT` | yes | — | — | Stored value |
| `planted_cause_key` | `TEXT` | no | — | — | Stored value |
| `planted_repair_class_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `planted_repair_equivalence_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `system_snapshot_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `system_abstained` | `INTEGER` | yes | — | — | Stored value |
| `system_anchor_key` | `TEXT` | yes | — | — | Stored value |
| `system_cause_key` | `TEXT` | no | — | — | Stored value |
| `system_repair_class_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `system_repair_equivalence_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `anchor_correct` | `INTEGER` | yes | — | — | Stored value |
| `cause_correct` | `INTEGER` | no | — | — | Stored value |
| `repair_correct` | `INTEGER` | no | — | — | Stored value |
| `abstention_correct` | `INTEGER` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `run_id` → [[Reference/Database/Tables/diagnostic_eval_runs|`diagnostic_eval_runs.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_diagnostic_eval_cases_shape` on `regression_shape`, `created_at`, `id`.
- `idx_diagnostic_eval_cases_attempt` on `attempt_id`, `created_at`, `id`.
- `sqlite_autoindex_diagnostic_eval_cases_2` on `run_id`, `case_key` (unique).
- `sqlite_autoindex_diagnostic_eval_cases_1` on `id` (unique).

Database triggers:

- `diagnostic_eval_cases_no_delete` — schema-enforced lifecycle or immutability constraint.
- `diagnostic_eval_cases_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.diagnostic_eval_case_rows()`
- `Repository.insert_diagnostic_eval_case()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/diagnostic_augmentation.py`
- `src/learnloop/diagnosis/scoreboard.py`

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
CREATE TABLE diagnostic_eval_cases (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES diagnostic_eval_runs(id),
  case_key TEXT NOT NULL,
  attempt_id TEXT,
  regression_shape TEXT NOT NULL CHECK (regression_shape IN (
    'exhibit',
    'genuine_facet_failure',
    'multiplication_failure',
    'addition_multiplication_confusion',
    'notation_typo_valid_reasoning',
    'missing_required_step',
    'alternate_valid_path',
    'item_contract_fault',
    'grader_interpretation_fault',
    'composite_supporting_pass',
    'correct_answer_invalid_reasoning',
    'unparseable_notation',
    'open_vocabulary_abstention',
    'cause_change_mid_history'
  )),
  source TEXT NOT NULL CHECK (source IN (
    'discrimination_profile', 'authored_fixture', 'adjudicated_overlap'
  )),
  practice_item_id TEXT NOT NULL,
  profile_id TEXT,
  learner_trace_md TEXT NOT NULL,
  planted_should_abstain INTEGER NOT NULL CHECK (planted_should_abstain IN (0, 1)),
  planted_anchor_json TEXT,
  planted_anchor_key TEXT NOT NULL,
  planted_cause_key TEXT,
  planted_repair_class_id TEXT,
  planted_repair_equivalence_id TEXT,
  system_snapshot_json TEXT NOT NULL,
  system_abstained INTEGER NOT NULL CHECK (system_abstained IN (0, 1)),
  system_anchor_key TEXT NOT NULL,
  system_cause_key TEXT,
  system_repair_class_id TEXT,
  system_repair_equivalence_id TEXT,
  anchor_correct INTEGER NOT NULL CHECK (anchor_correct IN (0, 1)),
  cause_correct INTEGER,
  repair_correct INTEGER,
  abstention_correct INTEGER NOT NULL CHECK (abstention_correct IN (0, 1)),
  created_at TEXT NOT NULL,
  UNIQUE (run_id, case_key),
  CHECK (cause_correct IS NULL OR cause_correct IN (0, 1)),
  CHECK (repair_correct IS NULL OR repair_correct IN (0, 1))
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
