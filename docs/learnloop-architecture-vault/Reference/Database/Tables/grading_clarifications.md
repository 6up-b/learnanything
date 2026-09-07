---
title: "grading_clarifications"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite grading_clarifications"
  - "table grading_clarifications"
schema_head: 157
table_name: "grading_clarifications"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "142_grading_clarifications.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/142_grading_clarifications.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop_sidecar/handlers/app.py"
  - "src/learnloop/attempts/clarification.py"
  - "src/learnloop/cli/clarification.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `grading_clarifications`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives grading clarification a stable database identity so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `attempt_id`, `criterion_id`, `agent_run_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/142_grading_clarifications.sql`.
- **Schema touched by:** `142_grading_clarifications.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `criterion_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `reason` | `TEXT` | yes | — | — | Stored value |
| `trigger` | `TEXT` | yes | — | — | Stored value |
| `question_md` | `TEXT` | yes | — | — | Stored value |
| `expires_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `grading_prompt_version` | `TEXT` | no | — | — | Stored value |
| `agent_run_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_grading_clarifications_pending` on `expires_at`, `attempt_id`.
- `sqlite_autoindex_grading_clarifications_2` on `attempt_id` (unique).
- `sqlite_autoindex_grading_clarifications_1` on `id` (unique).

Database triggers:

- `grading_clarifications_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.clarification_rate_counts()`
- `Repository.grading_clarification_for_attempt()`
- `Repository.grading_clarifications_awaiting_regrade()`
- `Repository.insert_grading_clarification()`
- `Repository.unanswered_grading_clarifications()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop_sidecar/handlers/app.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/attempts/clarification.py`
- `src/learnloop/cli/clarification.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_sidecar_trace_and_clarification.py`

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
CREATE TABLE grading_clarifications (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id) ON DELETE CASCADE,
  -- The hedged or abstained criterion the question is about.  Nullable: an
  -- attribution-level abstention ("I cannot name what went wrong") is not scoped
  -- to one criterion, and forcing one would be fabricated structure.
  criterion_id TEXT,
  -- Which of the three §3.A8 uncertainty shapes this is.  Closed vocabulary
  -- with an explicit `other` arm, per the standing "no new enum without an
  -- abstention arm" constraint.
  reason TEXT NOT NULL CHECK (reason IN (
    'ambiguous_notation',
    'skipped_step',
    'correct_answer_possibly_invalid_reasoning',
    'method_ambiguity',
    'other'
  )),
  -- What actually licensed the question: which signal on the provisional grade
  -- was hedged or abstained.  A confident grade can never produce a row here
  -- (that would make it an interrogation), and this column is the record of
  -- which non-confident signal it was.
  trigger TEXT NOT NULL CHECK (trigger IN (
    'hedged_criterion',
    'abstained_attribution',
    'low_grader_confidence'
  )),
  question_md TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  grading_prompt_version TEXT,
  agent_run_id TEXT,
  created_at TEXT NOT NULL,
  -- ONE question per attempt (§3.A8's bound, enforced by the schema rather than
  -- by a check in a service that a second caller could forget).
  UNIQUE(attempt_id)
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
