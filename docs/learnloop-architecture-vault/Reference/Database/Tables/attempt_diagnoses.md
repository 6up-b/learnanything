---
title: "attempt_diagnoses"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "e6fd14844aad42f2dab12ad7edd02e250c033734"
source_commit_timestamp: "2026-10-17T05:11:36-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite attempt_diagnoses"
  - "table attempt_diagnoses"
schema_head: 207
table_name: "attempt_diagnoses"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "170_blind_grading_diagnosis_split.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/170_blind_grading_diagnosis_split.sql"
  - "src/learnloop/db/stores/diagnoses.py"
  - "src/learnloop/db/stores/recurrence.py"
  - "src/learnloop/db/stores/write_provenance.py"
  - "src/learnloop/diagnosis/recurrence/report.py"
  - "src/learnloop/diagnosis/split/diagnoser.py"
  - "src/learnloop/diagnosis/text_gaps/jobs.py"
  - "src/learnloop/diagnosis/text_gaps/sources.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `attempt_diagnoses`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives attempt diagnose a stable database identity so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `attempt_id`, `blind_grade_record_id`, `agent_run_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> One diagnosis run. proposal_json is the VALIDATED DiagnosisProposal; causal_view_json is the §4.2 reverse mapping onto the error-event and repair-suggestion shapes the causal consumers read, computed once here so replay never re-derives it. Re-diagnosis appends with supersedes_id.

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/170_blind_grading_diagnosis_split.sql`.
- **Schema touched by:** `170_blind_grading_diagnosis_split.sql`, `176_recurrence_groups.sql`, `182_learner_text_gaps.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `blind_grade_record_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/blind_grade_records\|blind_grade_records.id]] | Stored value |
| `agent_run_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `diagnosis_prompt_version` | `TEXT` | yes | — | — | Stored value |
| `provider` | `TEXT` | no | — | — | Stored value |
| `model` | `TEXT` | no | — | — | Stored value |
| `mode` | `TEXT` | yes | — | — | Stored value |
| `history_mode` | `TEXT` | yes | — | — | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `proposal_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `causal_view_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `validation_report_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `error` | `TEXT` | no | — | — | Stored value |
| `latency_seconds` | `REAL` | no | — | — | Stored value |
| `supersedes_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/attempt_diagnoses\|attempt_diagnoses.id]] | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `supersedes_id` → [[Reference/Database/Tables/attempt_diagnoses|`attempt_diagnoses.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `blind_grade_record_id` → [[Reference/Database/Tables/blind_grade_records|`blind_grade_records.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `attempt_diagnoses_attempt` on `attempt_id`, `created_at`, `id`.
- `sqlite_autoindex_attempt_diagnoses_1` on `id` (unique).

Database triggers:

- `attempt_diagnoses_no_delete` — schema-enforced lifecycle or immutability constraint.
- `attempt_diagnoses_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/diagnoses.py`
- `src/learnloop/db/stores/recurrence.py`
- `src/learnloop/db/stores/write_provenance.py`
- `src/learnloop/diagnosis/recurrence/report.py`
- `src/learnloop/diagnosis/text_gaps/jobs.py`
- `src/learnloop/diagnosis/text_gaps/sources.py`
- `src/learnloop/placement/state.py`

### Direct SQL writers

- `src/learnloop/db/stores/diagnoses.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_chatgpt_plan_landing.py`
- `tests/test_diagnosis_input_provenance.py`
- `tests/test_forecast_receipts.py`
- `tests/test_forecast_receipts_landing.py`
- `tests/test_learner_text_gaps_flow.py`

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
CREATE TABLE attempt_diagnoses (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id),
  blind_grade_record_id TEXT REFERENCES blind_grade_records(id),
  agent_run_id TEXT,
  diagnosis_prompt_version TEXT NOT NULL,
  provider TEXT,
  model TEXT,
  mode TEXT NOT NULL CHECK (mode IN ('shadow', 'live')),
  history_mode TEXT NOT NULL CHECK (history_mode IN ('exact', 'full', 'snapshot', 'hybrid')),
  status TEXT NOT NULL CHECK (status IN ('completed', 'failed', 'skipped', 'validation_rejected')),
  proposal_json TEXT,
  causal_view_json TEXT,
  validation_report_json TEXT NOT NULL DEFAULT '{}',
  error TEXT,
  latency_seconds REAL,
  supersedes_id TEXT REFERENCES attempt_diagnoses(id),
  created_at TEXT NOT NULL,
  CHECK (supersedes_id IS NULL OR supersedes_id != id),
  CHECK (status != 'completed' OR proposal_json IS NOT NULL)
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
