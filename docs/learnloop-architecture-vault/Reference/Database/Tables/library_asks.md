---
title: "library_asks"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "b889cd70abe9b4a6f757423c59a5eb265971148c"
source_commit_timestamp: "2026-10-25T14:27:11-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite library_asks"
  - "table library_asks"
schema_head: 220
table_name: "library_asks"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "209_library_asks.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/209_library_asks.sql"
  - "src/learnloop/db/stores/library_asks.py"
  - "src/learnloop/reader/reader_report.py"
  - "src/learnloop/reader/source_objects.py"
  - "src/learnloop/source_retrieval/kept_comparisons.py"
  - "src/learnloop/source_retrieval/library_ask.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `library_asks`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives library ask a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `extraction_id`, `comparison_id`, `question_event_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/209_library_asks.sql`.
- **Schema touched by:** `209_library_asks.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `caller` | `TEXT` | yes | — | — | Stored value |
| `entry` | `TEXT` | yes | — | — | Stored value |
| `query_md` | `TEXT` | yes | — | — | Stored value |
| `query_hash` | `TEXT` | yes | — | — | Stored value |
| `extraction_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `anchor_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `personalized` | `INTEGER` | yes | — | — | Stored value |
| `requested_perspectives_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `manifest_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `organizer_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `comparison_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/source_comparisons\|source_comparisons.id]] | Stored value |
| `kept_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `kept_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `question_event_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `model` | `TEXT` | no | — | — | Stored value |
| `prompt_version` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `comparison_id` → [[Reference/Database/Tables/source_comparisons|`source_comparisons.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_library_asks_extraction` on `extraction_id`, `created_at`.
- `idx_library_asks_created` on `created_at`.
- `sqlite_autoindex_library_asks_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/library_asks.py`
- `src/learnloop/reader/reader_report.py`

### Direct SQL writers

- `src/learnloop/db/stores/library_asks.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/library_ask_fixtures.py`
- `tests/test_architecture.py`
- `tests/test_compare_keep_switch_off.py`
- `tests/test_compare_sources_keep.py`
- `tests/test_figures_rw5b_fix_round2.py`
- `tests/test_figures_rw5b_review.py`
- `tests/test_library_ask_expand.py`
- `tests/test_library_asks_migration.py`
- `tests/test_rw4_kill_switches.py`

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
CREATE TABLE library_asks (
  id TEXT PRIMARY KEY,
  -- Who asked: the learner (the Reader, the library search) or, later, the
  -- tutor's own request (RW1c / the sources spec's S4).
  caller TEXT NOT NULL CHECK (caller IN ('learner', 'tutor')),
  -- Where it was asked from: the library search box, Ctrl+Shift+F in the
  -- Reader, a selection's palette action.
  entry TEXT NOT NULL CHECK (entry IN (
    'library_search', 'reader', 'where_else_explained', 'where_is_this_used', 'what_do_i_need_first'
  )),
  query_md TEXT NOT NULL,
  query_hash TEXT NOT NULL,
  -- The open source and the passage the question was anchored on, if any.
  extraction_id TEXT,
  anchor_json TEXT NOT NULL DEFAULT '{}',
  personalized INTEGER NOT NULL CHECK (personalized IN (0, 1)),
  requested_perspectives_json TEXT NOT NULL DEFAULT '[]',
  manifest_json TEXT NOT NULL DEFAULT '{}',
  organizer_json TEXT NOT NULL DEFAULT '{}',
  comparison_id TEXT REFERENCES source_comparisons(id),
  kept_json TEXT,
  kept_at TEXT,
  question_event_id TEXT,
  model TEXT,
  prompt_version TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
