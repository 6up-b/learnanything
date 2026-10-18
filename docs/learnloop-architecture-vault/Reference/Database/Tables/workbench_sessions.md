---
title: "workbench_sessions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "50aa2ec9a49698dc2c08be71acbd0e109778f1a0"
source_commit_timestamp: "2026-10-17T23:52:53-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite workbench_sessions"
  - "table workbench_sessions"
schema_head: 210
table_name: "workbench_sessions"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "207_workbench.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/207_workbench.sql"
  - "src/learnloop/db/stores/workbench.py"
  - "src/learnloop/reader/recap.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `workbench_sessions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Holds each problem worked in steps (reader workbench RW2a, migration 207): beside the source in the Reader or full width on the practice screen, opened at once with its verbatim stem before the exercise import binds it to an item (import_status, the batch and its request for try again), how it was opened (origin, entry), the book's visibility and when it first counted as one hint-equivalent (source_shown_at), and its lifecycle (open, submitted with its attempt, abandoned and reopened). Lifecycle state, updated in place; replay never reads it, because the submitted attempt carries the evidence (hints_used, entry_surface). Kill switch workbench.enabled. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `practice_item_id`, `import_batch_id`, `parent_session_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/207_workbench.sql`.
- **Schema touched by:** `207_workbench.sql`, `210_help_assists.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `stem_md` | `TEXT` | yes | — | — | Stored value |
| `import_status` | `TEXT` | yes | `'none'` | — | Stored value |
| `import_batch_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `import_request_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `import_error` | `TEXT` | no | — | — | Stored value |
| `origin` | `TEXT` | yes | — | — | Stored value |
| `entry` | `TEXT` | yes | — | — | Stored value |
| `parent_session_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/workbench_sessions\|workbench_sessions.id]] | Stored value |
| `extraction_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `span_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `source_visible` | `INTEGER` | yes | `0` | — | Stored value |
| `source_hidden_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `source_shown_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `practice_session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `assessment_contract_version_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `carried_hints` | `INTEGER` | yes | `0` | — | Stored value |
| `scheduler_candidate_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `plan_presentation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `help_style` | `TEXT` | no | — | — | Stored value |
| `status` | `TEXT` | yes | `'open'` | — | Stored value |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `client_idempotency_key` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `closed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `parent_session_id` → [[Reference/Database/Tables/workbench_sessions|`workbench_sessions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_workbench_sessions_attempt` on `attempt_id`.
- `idx_workbench_sessions_extraction` on `extraction_id`, `status`, `updated_at`.
- `idx_workbench_sessions_item` on `practice_item_id`, `status`, `updated_at`.
- `sqlite_autoindex_workbench_sessions_2` on `client_idempotency_key` (unique).
- `sqlite_autoindex_workbench_sessions_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/reader/recap.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_architecture.py`
- `tests/test_library_ask_review.py`
- `tests/test_reader_find_sources_callers.py`
- `tests/test_reader_recap.py`
- `tests/test_reader_workbench_rw2a.py`

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
CREATE TABLE workbench_sessions (
  id TEXT PRIMARY KEY,
  -- NULL until the import binds (or from the start when opened on an item).
  practice_item_id TEXT,
  -- The verbatim stem shown before binding (and kept after it).
  stem_md TEXT NOT NULL,
  import_status TEXT NOT NULL DEFAULT 'none'
    CHECK (import_status IN ('none', 'pending', 'bound', 'failed')),
  -- The exercise-import batch the session waits on, and the request it was
  -- enqueued with, so "try again" re-enqueues it after a restart.
  import_batch_id TEXT,
  import_request_json TEXT,
  import_error TEXT,
  -- Where the session is worked now. A resume on another surface moves it
  -- (the practice card resuming a Reader problem, the Reader resuming a
  -- practice-screen one), so the submit records the surface it was sent from.
  origin TEXT NOT NULL CHECK (origin IN ('reader', 'practice', 'plan')),
  -- How it was opened; it sets the default book visibility (UX S7, D9).
  entry TEXT NOT NULL CHECK (entry IN (
    'work_through', 'resume', 'check_me', 'practice_this', 'path_exercise',
    'discriminating_problem', 'practice_screen', 'plan'
  )),
  -- A "short problem instead" session's original problem (RW2b, D32).
  parent_session_id TEXT REFERENCES workbench_sessions(id),
  extraction_id TEXT,
  span_ids_json TEXT NOT NULL DEFAULT '[]',
  -- Whether the book is shown now (the learner's one-key choice).
  source_visible INTEGER NOT NULL DEFAULT 0 CHECK (source_visible IN (0, 1)),
  -- When the learner last hid the book (NULL: never hidden).
  source_hidden_at TEXT,
  -- When the book first counted: the first step written with it shown, or
  -- its first showing after a step (spec §5.4: one hint-equivalent from then
  -- on). NULL: the attempt is the learner's own.
  source_shown_at TEXT,
  -- The practice session the submit ran in (filled at submit).
  practice_session_id TEXT,
  -- The assessment contract the learner was shown (snapshotted when the
  -- session opens on its item or binds to it), so a problem resumed after its
  -- rubric or required method changed is graded against what it showed.
  assessment_contract_version_id TEXT,
  -- Hints the learner revealed on the practice screen's answer box before
  -- working in steps. Never taken back; the submit counts them with the book.
  carried_hints INTEGER NOT NULL DEFAULT 0 CHECK (carried_hints >= 0),
  -- The serve the problem answers: the scheduler offer and the daily-plan
  -- presentation it was opened from ("check me", the practice screen), kept
  -- so a resumed problem still submits as that serve. A later serve of the
  -- same item replaces them; a resume without one keeps them.
  scheduler_candidate_id TEXT,
  plan_presentation_id TEXT,
  -- The help style's per-session override (RW2b, D31); NULL until then.
  help_style TEXT CHECK (help_style IS NULL OR help_style IN ('let_me_struggle', 'balanced', 'guide_me')),
  -- open -> submitted, or open -> abandoned -> open on reopen (UX S13).
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'submitted', 'abandoned')),
  attempt_id TEXT,
  client_idempotency_key TEXT UNIQUE,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  closed_at TEXT,
  CHECK ((status = 'submitted') = (attempt_id IS NOT NULL)),
  CHECK ((import_status = 'bound') <= (practice_item_id IS NOT NULL))
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
