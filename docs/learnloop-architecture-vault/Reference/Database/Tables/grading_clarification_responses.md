---
title: "grading_clarification_responses"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite grading_clarification_responses"
  - "table grading_clarification_responses"
schema_head: 156
table_name: "grading_clarification_responses"
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

# `grading_clarification_responses`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives grading clarification response a stable database identity so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `clarification_id`, `answer_md`, `resolved_grading_revision`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> The learner's answer.  Separate table so the request stays immutable, and so "was this ever answered" is a join rather than a mutable flag that a failed regrade could leave lying.  This one is insert-then-stamp-once rather than strictly append-only, and the ordering is deliberate: the answer is written the moment the learner gives it, and the regrade outcome is stamped on afterwards.  Writing the row only after a successful regrade would lose the learner's words to a provider outage -- and the answer is the un-backfillable half of this exchange (standing constraint 6), while the regrade can always be re-run.  DELETE is forbidden; the answer text itself is never rewritten by any code path here.

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
| `clarification_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/grading_clarifications\|grading_clarifications.id]] | Stored value |
| `answer_md` | `TEXT` | yes | — | — | Stored value |
| `resolved_grading_revision` | `INTEGER` | no | — | — | Stored value |
| `outcome` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `clarification_id` → [[Reference/Database/Tables/grading_clarifications|`grading_clarifications.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_grading_clarification_responses_2` on `clarification_id` (unique).
- `sqlite_autoindex_grading_clarification_responses_1` on `id` (unique).

Database triggers:

- `grading_clarification_responses_no_delete` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.clarification_rate_counts()`
- `Repository.grading_clarification_for_attempt()`
- `Repository.grading_clarifications_awaiting_regrade()`
- `Repository.insert_grading_clarification_response()`
- `Repository.stamp_grading_clarification_outcome()`
- `Repository.unanswered_grading_clarifications()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop_sidecar/handlers/app.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

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
CREATE TABLE grading_clarification_responses (
  id TEXT PRIMARY KEY,
  clarification_id TEXT NOT NULL REFERENCES grading_clarifications(id) ON DELETE CASCADE,
  answer_md TEXT NOT NULL,
  -- The grading revision the re-grade produced, once it lands.  Null means the
  -- answer is recorded but the re-grade has not completed -- which is a real,
  -- observable state (provider outage) and must not be indistinguishable from
  -- "never answered".
  resolved_grading_revision INTEGER,
  -- Whether the answer actually resolved the uncertainty.  `abstained` is a
  -- first-class outcome: a learner may answer and STILL leave the grader unable
  -- to name a cause, and recording that as unresolved is what stops A8 from
  -- becoming a machine for manufacturing resolutions.
  outcome TEXT CHECK (outcome IN ('resolved', 'abstained', 'regrade_failed')),
  created_at TEXT NOT NULL,
  UNIQUE(clarification_id)
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
