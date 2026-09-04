---
title: "trace_exercised_facets"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite trace_exercised_facets"
  - "table trace_exercised_facets"
schema_head: 157
table_name: "trace_exercised_facets"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "141_conjunctive_instruments.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/141_conjunctive_instruments.sql"
  - "src/learnloop/attempts/trace_evidence.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop_sidecar/handlers/feedback.py"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/attempts/regrade.py"
  - "src/learnloop/learner/facet_evidence_timeline.py"
  - "src/learnloop/substrate/canonical_projection.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `trace_exercised_facets`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives trace exercised facet a stable database identity so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `attempt_id`, `facet_id`, `criterion_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/141_conjunctive_instruments.sql`.
- **Schema touched by:** `141_conjunctive_instruments.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `facet_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `observation_scope` | `TEXT` | yes | — | — | Stored value |
| `role` | `TEXT` | yes | `'supporting'` | — | Stored value |
| `evidence` | `TEXT` | yes | — | — | Stored value |
| `criterion_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `source` | `TEXT` | yes | `'grader_trace'` | — | Stored value |
| `agent_run_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `grading_prompt_version` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_trace_exercised_facets_facet` on `facet_id`, `observation_scope`, `created_at`.
- `idx_trace_exercised_facets_attempt` on `attempt_id`, `facet_id`.
- `sqlite_autoindex_trace_exercised_facets_2` on `attempt_id`, `facet_id`, `source` (unique).
- `sqlite_autoindex_trace_exercised_facets_1` on `id` (unique).

Database triggers:

- `trace_exercised_facets_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.all_trace_exercised_facets()`
- `Repository.insert_trace_exercised_facets()`
- `Repository.trace_exercised_facets()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/attempts/regrade.py`
- `src/learnloop/attempts/trace_evidence.py`
- `src/learnloop/learner/facet_evidence_timeline.py`
- `src/learnloop/substrate/canonical_projection.py`
- `src/learnloop_sidecar/handlers/feedback.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_conjunctive_instruments.py`
- `tests/test_projection_evidence_polarity.py`
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
CREATE TABLE trace_exercised_facets (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id) ON DELETE CASCADE,
  facet_id TEXT NOT NULL,
  -- 'declared' when the facet is already in the item's contract (the grader
  -- confirming what the item intended to measure), 'opportunistic' when it is
  -- not.  Kept separate because the A6 revert criterion -- "opportunistic
  -- credit concentrates on a few facets" -- is a statement about the second
  -- population only.
  observation_scope TEXT NOT NULL CHECK (observation_scope IN ('declared', 'opportunistic')),
  role TEXT NOT NULL DEFAULT 'supporting' CHECK (role = 'supporting'),
  -- The grader's own words for what in the trace showed the facet exercised.
  -- Required: an observation with no citation is an assertion, and this channel
  -- exists precisely because the model is reporting rather than deciding.
  evidence TEXT NOT NULL,
  -- Which criterion's work the observation was seen in, when the grader
  -- localizes it.  Null is honest and common: the trace is one artifact.
  criterion_id TEXT,
  -- Where the observation came from.  'grader_trace' is A6; the column exists
  -- so a later channel (a teach-back artifact, a probe dialogue turn) is
  -- separable rather than pooled into A6's revert criterion.
  source TEXT NOT NULL DEFAULT 'grader_trace',
  agent_run_id TEXT,
  grading_prompt_version TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(attempt_id, facet_id, source)
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
