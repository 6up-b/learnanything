---
title: "error_hunt_outcomes"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite error_hunt_outcomes"
  - "table error_hunt_outcomes"
schema_head: 156
table_name: "error_hunt_outcomes"
table_role: "receipt"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "143_instrument_classes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/143_instrument_classes.sql"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop_sidecar/handlers/measurement.py"
  - "src/learnloop/diagnosis/error_hunt.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `error_hunt_outcomes`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records the measured outcome and lineage for error hunt so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `attempt_id`, `practice_item_id`, `misconception_candidate_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/143_instrument_classes.sql`.
- **Schema touched by:** `143_instrument_classes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `clean_solution` | `INTEGER` | yes | — | — | Stored value |
| `planted_total` | `INTEGER` | yes | — | — | Stored value |
| `planted_repaired` | `INTEGER` | yes | — | — | Stored value |
| `planted_flagged_not_repaired` | `INTEGER` | yes | — | — | Stored value |
| `planted_missed` | `INTEGER` | yes | — | — | Stored value |
| `false_positive_reports` | `INTEGER` | yes | — | — | Stored value |
| `misconception_candidate_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `facet_failure_suppressed` | `INTEGER` | yes | `0` | — | Stored value |
| `grading_prompt_version` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_error_hunt_outcomes_clean` on `clean_solution`, `created_at`.
- `idx_error_hunt_outcomes_item` on `practice_item_id`, `created_at`.
- `sqlite_autoindex_error_hunt_outcomes_2` on `attempt_id` (unique).
- `sqlite_autoindex_error_hunt_outcomes_1` on `id` (unique).

Database triggers:

- `error_hunt_outcomes_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.error_hunt_outcome()`
- `Repository.error_hunt_outcome_rows()`
- `Repository.insert_error_hunt_outcome()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/error_hunt.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_error_hunt_items.py`

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
CREATE TABLE error_hunt_outcomes (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id) ON DELETE CASCADE,
  practice_item_id TEXT NOT NULL,
  -- 1 when the administered solution carried NO planted errors (the rotation).
  -- Stored rather than derived from `planted_total = 0`, because "this rotation
  -- served the clean variant" and "this item's plants failed to load" are
  -- different events and must not read alike.
  clean_solution INTEGER NOT NULL CHECK (clean_solution IN (0, 1)),
  planted_total INTEGER NOT NULL CHECK (planted_total >= 0),
  -- REPAIRED, not merely flagged.  §3.A3: "Flagging is recognition; repairing is
  -- construction.  This is what keeps the instrument on the right side of the
  -- no-recognition-items gate."  The two counts are separate columns precisely so
  -- that a pool drifting toward flag-only credit is visible instead of pooled
  -- into one "found" number.
  planted_repaired INTEGER NOT NULL CHECK (planted_repaired >= 0),
  planted_flagged_not_repaired INTEGER NOT NULL CHECK (planted_flagged_not_repaired >= 0),
  planted_missed INTEGER NOT NULL CHECK (planted_missed >= 0),
  -- Errors the learner reported that were never planted.  On a seeded solution
  -- this is noise; on a CLEAN one it is the misconception the spec is after.
  false_positive_reports INTEGER NOT NULL CHECK (false_positive_reports >= 0),
  -- The `misconception_candidates` row a clean-solution false positive minted.
  -- Null on every other arm.  Not a foreign key by choice: the candidate store
  -- is promotable and mergeable, and a hard reference would make this history
  -- undeletable rather than merely honest.
  misconception_candidate_id TEXT,
  -- The explicit record that the clean-solution path took no facet negative.
  -- §10's line is about what did NOT happen, and an invariant nobody can query is
  -- an invariant nobody can regress-test.
  facet_failure_suppressed INTEGER NOT NULL DEFAULT 0
    CHECK (facet_failure_suppressed IN (0, 1)),
  grading_prompt_version TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(attempt_id)
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
