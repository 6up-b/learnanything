---
title: "attempt_feedback_metadata"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite attempt_feedback_metadata"
  - "table attempt_feedback_metadata"
schema_head: 156
table_name: "attempt_feedback_metadata"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "005_attempt_feedback_metadata.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/005_attempt_feedback_metadata.sql"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/attempts/coldness_receipt.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/goals/exam_seeding.py"
  - "src/learnloop/ops/debug_time.py"
  - "src/learnloop/attempts/grading.py"
  - "src/learnloop/attempts/post_attempt.py"
  - "src/learnloop/cli/runtime.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `attempt_feedback_metadata`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives attempt feedback metadata a stable database identity so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `attempt_id`, `agent_run_id`, `fallback_reason`, making the operational relationship explicit. ^table-purpose

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/005_attempt_feedback_metadata.sql`.
- **Schema touched by:** `005_attempt_feedback_metadata.sql`, `006_ai_provider_metadata.sql`, `010_scheduler_training_logs.sql`, `111_deterministic_grading_source.sql`, `151_cold_measurement_opportunities.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `attempt_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `grading_source` | `TEXT` | yes | — | — | Stored value |
| `fallback_reason` | `TEXT` | no | — | — | Stored value |
| `agent_run_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/agent_runs\|agent_runs.id]] | Stored value |
| `fatal_errors_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `feedback_md` | `TEXT` | no | — | — | Stored value |
| `repair_suggestions_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `shown_count` | `INTEGER` | yes | `0` | — | Stored value |
| `first_shown_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `last_shown_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `agent_run_id` → [[Reference/Database/Tables/agent_runs|`agent_runs.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_attempt_feedback_metadata_last_shown` on `last_shown_at`, `attempt_id`.
- `sqlite_autoindex_attempt_feedback_metadata_1` on `attempt_id` (unique).

## Who calls it

### Repository access surface

- `Repository.attempts_with_feedback_shown_between()`
- `Repository.fetch_attempt_feedback_metadata()`
- `Repository.record_feedback_shown()`
- `Repository.upsert_attempt_feedback_metadata()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/attempts/coldness_receipt.py`
- `src/learnloop/attempts/grading.py`
- `src/learnloop/attempts/post_attempt.py`
- `src/learnloop/cli/runtime.py`
- `src/learnloop/content/authoring/practice_generation.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/diagnosis_adjudication.py`
- `src/learnloop/diagnosis/followups.py`
- `src/learnloop/diagnosis/misconceptions.py`
- `src/learnloop/diagnosis/missing_vocabulary.py`
- `src/learnloop/diagnosis/probe_blocks.py`
- `src/learnloop/diagnosis/scoreboard.py`
- `src/learnloop/goals/certification_cold_probe.py`
- `src/learnloop/tutor/tutor_qa.py`
- `src/learnloop_sidecar/handlers/adjudication.py`
- `src/learnloop_sidecar/handlers/feedback.py`
- `src/learnloop_sidecar/handlers/practice.py`
- `src/learnloop_sidecar/handlers/serializers.py`
- `src/learnloop_sidecar/handlers/teach_back.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_p2_acceptance.py`
- `tests/test_coldness_receipt.py`
- `tests/test_migrations.py`
- `tests/test_causal_attribution_p1.py`
- `tests/test_common_repair_delivery.py`
- `tests/test_facet_diagnostics_v03.py`
- `tests/test_post_attempt_pipeline.py`
- `tests/test_reveal_ledger.py`
- `tests/test_scoreboard.py`
- `tests/test_sidecar_contract.py`
- `tests/test_tui_feedback.py`
- `tests/test_tui_practice.py`

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
CREATE TABLE "attempt_feedback_metadata" (
  attempt_id TEXT PRIMARY KEY REFERENCES practice_attempts(id) ON DELETE CASCADE,
  grading_source TEXT NOT NULL CHECK (grading_source IN ('ai', 'codex', 'self', 'deterministic')),
  fallback_reason TEXT,
  agent_run_id TEXT REFERENCES agent_runs(id),
  fatal_errors_json TEXT NOT NULL DEFAULT '[]',
  feedback_md TEXT,
  repair_suggestions_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  shown_count INTEGER NOT NULL DEFAULT 0 CHECK (shown_count >= 0),
  first_shown_at TEXT,
  last_shown_at TEXT
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
