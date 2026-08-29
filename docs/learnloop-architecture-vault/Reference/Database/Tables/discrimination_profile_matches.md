---
title: "discrimination_profile_matches"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite discrimination_profile_matches"
  - "table discrimination_profile_matches"
schema_head: 156
table_name: "discrimination_profile_matches"
table_role: "receipt"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "143_instrument_classes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/143_instrument_classes.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/discrimination_profiles.py"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/attempts/grading.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `discrimination_profile_matches`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives discrimination profile matche a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `attempt_id`, `practice_item_id`, `profile_id`, making the operational relationship explicit. ^table-purpose

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
| `outcome` | `TEXT` | yes | — | — | Stored value |
| `profile_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `misconception_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `evidence` | `TEXT` | no | — | — | Stored value |
| `attempt_failed` | `INTEGER` | yes | — | — | Stored value |
| `grading_prompt_version` | `TEXT` | no | — | — | Stored value |
| `agent_run_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_discrimination_profile_matches_profile` on `profile_id`, `outcome`.
- `idx_discrimination_profile_matches_outcome` on `outcome`, `created_at`.
- `sqlite_autoindex_discrimination_profile_matches_2` on `attempt_id` (unique).
- `sqlite_autoindex_discrimination_profile_matches_1` on `id` (unique).

Database triggers:

- `discrimination_profile_matches_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.discrimination_profile_match()`
- `Repository.discrimination_profile_match_rows()`
- `Repository.insert_discrimination_profile_match()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/attempts/grading.py`
- `src/learnloop/diagnosis/discrimination_profiles.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_discrimination_profiles.py`

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
CREATE TABLE discrimination_profile_matches (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id) ON DELETE CASCADE,
  practice_item_id TEXT NOT NULL,
  outcome TEXT NOT NULL CHECK (outcome IN (
    -- The trace matched one authored profile.  `profile_id` is required.
    'matched',
    -- Profiles were offered and the diagnostician rejected all of them.  This is
    -- the arm §3.A5 protects; standing constraint 2 says watch BOTH tails, and a
    -- rate that collapses toward zero here is the model matching the nearest
    -- authored profile rather than reading the trace.
    'no_profile_applies',
    -- The item authored no profiles, so no judgement was asked for.  Kept
    -- separate from `no_profile_applies` because pooling them would let an
    -- unauthored pool look like a healthy rejection rate.
    'no_profiles_offered',
    -- Profiles were offered and the grader returned nothing at all (an older
    -- prompt version, a provider that dropped the field).  An abstention arm the
    -- vocabulary owes itself: silence is not rejection.
    'not_reported'
  )),
  -- The authored profile id, present exactly on the `matched` arm.  Not a foreign
  -- key: profiles live in vault YAML on the item, and the vault is not in this
  -- database.  The id is validated against the item's authored profiles before
  -- the row is written.
  profile_id TEXT,
  -- The registry belief the matched profile names, when it has one.  Denormalized
  -- deliberately: a profile can be retired or reworded on the item, and a match
  -- record that could no longer say WHICH belief it meant would be unreadable
  -- history.
  misconception_id TEXT,
  -- The grader's citation from the trace.  Required on a match for the same
  -- reason A6 requires one: a match with no citation is an assertion, and this
  -- channel exists because the model is reporting rather than deciding.
  evidence TEXT,
  -- Whether the attempt was ultimately graded as a failure.  The two-tailed rate
  -- is only meaningful over failures -- a profile describing what a WRONG answer
  -- looks like has nothing to say about a correct one -- and recomputing this
  -- from the attempt later would key on a `rubric_score` that a regrade can move.
  attempt_failed INTEGER NOT NULL CHECK (attempt_failed IN (0, 1)),
  grading_prompt_version TEXT,
  agent_run_id TEXT,
  created_at TEXT NOT NULL,
  -- One judgement per attempt.  A regrade re-reports and is ignored by the
  -- INSERT OR IGNORE writer, so the first judgement survives -- the record is of
  -- what the grader said, and a record that can be rewritten is not evidence.
  UNIQUE(attempt_id)
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
