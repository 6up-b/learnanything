---
title: "lapse_episodes"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite lapse_episodes"
  - "table lapse_episodes"
schema_head: 156
table_name: "lapse_episodes"
table_role: "workflow"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "079_progression_and_lapse.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/079_progression_and_lapse.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/scheduling/progression.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `lapse_episodes`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives lapse episode a stable database identity so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `card_lineage_id`, `learner_id`, `opened_administration_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/079_progression_and_lapse.sql`.
- **Schema touched by:** `079_progression_and_lapse.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `card_lineage_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/card_lineages\|card_lineages.id]] | Stored value |
| `learner_id` | `TEXT` | yes | `'local'` | — | Application-validated soft reference |
| `opened_administration_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `status` | `TEXT` | yes | — | — | Stored value |
| `retry_observations_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `derived_retrievability` | `REAL` | no | — | — | Stored value |
| `followup_due_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `opened_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `closed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `card_lineage_id` → [[Reference/Database/Tables/card_lineages|`card_lineages.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_lapse_lineage` on `card_lineage_id`, `status`.
- `sqlite_autoindex_lapse_episodes_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.lapse_episode()`
- `Repository.lapse_episodes_for_lineage()`
- `Repository.open_lapse_episode()`
- `Repository.update_lapse_episode()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/scheduling/progression.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_journey6.py`
- `tests/test_progression.py`

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
CREATE TABLE lapse_episodes (
  id TEXT PRIMARY KEY,
  card_lineage_id TEXT NOT NULL REFERENCES card_lineages(id),
  learner_id TEXT NOT NULL DEFAULT 'local',
  opened_administration_id TEXT,
  -- §5.5: a failed eligible practice administration opens a durable lapse. Same-session
  -- retries are LINKED observations that never overwrite the original failure; before
  -- give_up they update a derived retrievability but stack no independent evidence.
  status TEXT NOT NULL CHECK (status IN ('open', 'given_up', 'recovered')),
  retry_observations_json TEXT,
  derived_retrievability REAL,
  followup_due_at TEXT,
  opened_at TEXT NOT NULL,
  closed_at TEXT
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
