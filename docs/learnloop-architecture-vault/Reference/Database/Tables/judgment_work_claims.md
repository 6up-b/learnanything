---
title: "judgment_work_claims"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "9dbe585eb1b7e798d93de67e1d5badfba2a3c754"
source_commit_timestamp: "2026-10-18T19:24:02-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite judgment_work_claims"
  - "table judgment_work_claims"
schema_head: 213
table_name: "judgment_work_claims"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "176_recurrence_groups.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/176_recurrence_groups.sql"
  - "src/learnloop/adaptive_difficulty/background.py"
  - "src/learnloop/adaptive_difficulty/claims.py"
  - "src/learnloop/content/authoring/source_exercise_import.py"
  - "src/learnloop/db/stores/judgment_claims.py"
  - "src/learnloop/hints/map_builder.py"
  - "src/learnloop/hints/outcome.py"
  - "src/learnloop/matching/judge.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `judgment_work_claims`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives judgment work claim a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `judgment_id`, `prompt_version`, `input_hash`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Work claims of the shared "same or different?" judge (learnloop.matching): one row per (task, producer, prompt version, input) question. A worker claims it in a short write transaction BEFORE the model call (the call itself runs outside any transaction); a live lease held by another worker makes it skip the pair, an expired lease is re-claimed with a new epoch, and the verdict is appended only while the worker's epoch still holds (completion fencing), so two workers never pay for, or append, the same verdict twice. Mutable workflow state, never replayed.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/176_recurrence_groups.sql`.
- **Schema touched by:** `176_recurrence_groups.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `claim_key` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `task` | `TEXT` | yes | — | — | Stored value |
| `producer` | `TEXT` | yes | — | — | Stored value |
| `prompt_version` | `TEXT` | no | — | — | Stored value |
| `input_hash` | `TEXT` | yes | — | — | Stored value |
| `state` | `TEXT` | yes | — | — | Stored value |
| `lease_owner` | `TEXT` | no | — | — | Stored value |
| `lease_expires_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `lease_epoch` | `INTEGER` | yes | `0` | — | Stored value |
| `judgment_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_judgment_work_claims_1` on `claim_key` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/content/authoring/source_exercise_import.py`
- `src/learnloop/db/stores/judgment_claims.py`
- `src/learnloop/reader/reader_intent.py`

### Direct SQL writers

- `src/learnloop/db/stores/judgment_claims.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_ad1_fix_round5.py`
- `tests/test_approach_maps.py`
- `tests/test_hint_feedback_texts.py`
- `tests/test_hint_outcome.py`
- `tests/test_reader_active_reading.py`
- `tests/test_reader_formative_texts.py`
- `tests/test_recurrence_merge_composition.py`

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
CREATE TABLE judgment_work_claims (
  claim_key TEXT PRIMARY KEY,
  task TEXT NOT NULL,
  producer TEXT NOT NULL,
  prompt_version TEXT,
  input_hash TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('leased', 'done', 'released')),
  lease_owner TEXT,
  lease_expires_at TEXT,
  lease_epoch INTEGER NOT NULL DEFAULT 0,
  judgment_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
