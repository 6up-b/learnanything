---
title: "followup_ratings"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite followup_ratings"
  - "table followup_ratings"
schema_head: 157
table_name: "followup_ratings"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "017_followup_ratings.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/017_followup_ratings.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/gate_fit.py"
  - "src/learnloop/scheduling/evaluation.py"
  - "src/learnloop_sidecar/handlers/feedback.py"
  - "src/learnloop_sidecar/handlers/serializers.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `followup_ratings`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives followup rating a stable database identity so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `attempt_id`, `gate_attempt_id`, `useful`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> One-tap "was this follow-up useful?" labels for the follow-up gate fitter (Fable's-take item 2). attempt_id is the rated attempt (the follow-up attempt itself); gate_attempt_id is the attempt whose gate decision queued that follow-up, resolved at write time so the fitter can join attempt_surprise.gate_diagnostics_json directly. Sparse, re-ratable (upsert), carries its own provenance/timestamps.

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/017_followup_ratings.sql`.
- **Schema touched by:** `017_followup_ratings.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `attempt_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `gate_attempt_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `useful` | `INTEGER` | yes | — | — | Stored value |
| `source` | `TEXT` | yes | `'user'` | — | Stored value |
| `rated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `gate_attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `SET NULL`, on update `NO ACTION`.
- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_followup_ratings_gate_attempt` on `gate_attempt_id`.
- `sqlite_autoindex_followup_ratings_1` on `attempt_id` (unique).

## Who calls it

### Repository access surface

- `Repository.followup_rating()`
- `Repository.gate_training_rows()`
- `Repository.upsert_followup_rating()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/gate_fit.py`
- `src/learnloop/scheduling/evaluation.py`
- `src/learnloop_sidecar/handlers/feedback.py`
- `src/learnloop_sidecar/handlers/serializers.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_gate_fit.py`
- `tests/test_sidecar_contract.py`

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
CREATE TABLE followup_ratings (
  attempt_id TEXT PRIMARY KEY REFERENCES practice_attempts(id) ON DELETE CASCADE,
  gate_attempt_id TEXT REFERENCES practice_attempts(id) ON DELETE SET NULL,
  useful INTEGER NOT NULL CHECK (useful IN (0, 1)),
  source TEXT NOT NULL DEFAULT 'user',
  rated_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
