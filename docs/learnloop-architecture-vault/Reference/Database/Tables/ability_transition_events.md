---
title: "ability_transition_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite ability_transition_events"
  - "table ability_transition_events"
schema_head: 157
table_name: "ability_transition_events"
table_role: "derived"
functionality_status: "active"
domain_family: "operations"
introduced_in: "008_ability_transition_events.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/008_ability_transition_events.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/substrate/replay.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `ability_transition_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Materializes the replayed ability-state transition attributed to each attempt. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `attempt_id`, `learning_object_id`, `practice_item_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/008_ability_transition_events.sql`.
- **Schema touched by:** `008_ability_transition_events.sql`.
- **Rebuild owner:** `learning_state`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `attempt_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `transition_type` | `TEXT` | yes | — | — | Stored value |
| `expected_skill_gain` | `REAL` | yes | `0.0` | — | Stored value |
| `target_facets_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `reason` | `TEXT` | yes | — | — | Stored value |
| `applied_to_belief_counts` | `INTEGER` | yes | `0` | — | Stored value |
| `applied_to_mastery` | `INTEGER` | yes | `0` | — | Stored value |
| `applied_to_facet_recall` | `INTEGER` | yes | `0` | — | Stored value |
| `process_noise` | `REAL` | no | — | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_ability_transition_events_lo` on `learning_object_id`, `created_at`.
- `sqlite_autoindex_ability_transition_events_1` on `attempt_id` (unique).

## Who calls it

### Repository access surface

- `Repository._upsert_ability_transition_event()`
- `Repository.ability_transition_event()`
- `Repository.replace_attempt_derived_outcome()`
- `Repository.reset_learning_object_derived_state()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/substrate/replay.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_rebuild_orchestrator.py`
- `tests/test_item_parameters.py`
- `tests/test_recall_coverage_interventions.py`
- `tests/test_replay.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.
5. Update the single owner in `DERIVED_STATE_REPLAYERS`, then prove same-version rebuild equivalence and shadow isolation.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE TABLE ability_transition_events (
  attempt_id TEXT PRIMARY KEY REFERENCES practice_attempts(id) ON DELETE CASCADE,
  learning_object_id TEXT NOT NULL,
  practice_item_id TEXT NOT NULL,
  transition_type TEXT NOT NULL,
  expected_skill_gain REAL NOT NULL DEFAULT 0.0,
  target_facets_json TEXT NOT NULL,
  reason TEXT NOT NULL,
  applied_to_belief_counts INTEGER NOT NULL DEFAULT 0 CHECK (applied_to_belief_counts IN (0, 1)),
  applied_to_mastery INTEGER NOT NULL DEFAULT 0 CHECK (applied_to_mastery IN (0, 1)),
  applied_to_facet_recall INTEGER NOT NULL DEFAULT 0 CHECK (applied_to_facet_recall IN (0, 1)),
  process_noise REAL,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
