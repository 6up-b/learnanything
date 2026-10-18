---
title: "help_assists"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "04d06282fa869bb214533f6f93a25c96ea13040e"
source_commit_timestamp: "2026-10-18T00:22:56-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite help_assists"
  - "table help_assists"
schema_head: 210
table_name: "help_assists"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "210_help_assists.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/210_help_assists.sql"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/config/template.py"
  - "src/learnloop/db/stores/help_assists.py"
  - "src/learnloop/hints/report.py"
  - "src/learnloop/hints/telemetry.py"
  - "src/learnloop/reader/reader_observations.py"
  - "src/learnloop/reader/recap.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `help_assists`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives help assist a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `practice_item_id`, `practice_session_id`, `workbench_session_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/210_help_assists.sql`.
- **Schema touched by:** `210_help_assists.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `surface` | `TEXT` | yes | — | — | Stored value |
| `assist_kind` | `TEXT` | yes | — | — | Stored value |
| `practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `practice_item_hash` | `TEXT` | no | — | — | Stored value |
| `practice_session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `workbench_session_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/workbench_sessions\|workbench_sessions.id]] | Stored value |
| `attempt_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `submission_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `hint_kind` | `TEXT` | no | — | — | Stored value |
| `level` | `INTEGER` | no | — | — | Stored value |
| `offered_level` | `INTEGER` | no | — | — | Stored value |
| `level_source` | `TEXT` | no | — | — | Stored value |
| `horizon` | `INTEGER` | no | — | — | Stored value |
| `route_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `from_node_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `target_node_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `map_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `strategy` | `TEXT` | no | — | — | Stored value |
| `body_md` | `TEXT` | no | — | — | Stored value |
| `authored_index` | `INTEGER` | no | — | — | Stored value |
| `work_hash` | `TEXT` | no | — | — | Stored value |
| `work_chars` | `INTEGER` | no | — | — | Stored value |
| `placement_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `chooser` | `TEXT` | yes | — | — | Stored value |
| `options_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `probabilities_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `drawn_option_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `propensity` | `REAL` | no | — | — | Stored value |
| `seed` | `TEXT` | no | — | — | Stored value |
| `policy_version` | `TEXT` | no | — | — | Stored value |
| `question_set_version` | `TEXT` | no | — | — | Stored value |
| `state_hash` | `TEXT` | no | — | — | Stored value |
| `request` | `TEXT` | no | — | — | Stored value |
| `feedback_text` | `TEXT` | no | — | — | Stored value |
| `feedback_shortcut` | `TEXT` | no | — | — | Stored value |
| `contract_failures_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `leak_flags_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `shown` | `INTEGER` | yes | — | — | Stored value |
| `counted_by` | `TEXT` | no | — | — | Stored value |
| `model` | `TEXT` | no | — | — | Stored value |
| `prompt_version` | `TEXT` | no | — | — | Stored value |
| `input_hash` | `TEXT` | no | — | — | Stored value |
| `latency_ms` | `INTEGER` | no | — | — | Stored value |
| `requested_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `shown_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `submitted_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `submit_latency_seconds` | `REAL` | no | — | — | Stored value |
| `step_snapshot_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `step_verdicts_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `first_questionable_step_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `error_kind_guess` | `TEXT` | no | — | — | Stored value |
| `about_step_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `continue_from_step_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `rivals_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `predicted_answers_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `eig_nats` | `REAL` | no | — | — | Stored value |
| `feedback_step_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `cited_span_ids_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `retrieval_manifest_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `alternatives_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

Declared SQLite foreign keys:

- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `workbench_session_id` → [[Reference/Database/Tables/workbench_sessions|`workbench_sessions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_help_assists_requested` on `surface`, `requested_at`.
- `idx_help_assists_workbench` on `workbench_session_id`, `requested_at`.
- `idx_help_assists_submission` on `submission_id`, `practice_item_id`.
- `idx_help_assists_attempt` on `attempt_id`.
- `idx_help_assists_session_item` on `practice_session_id`, `practice_item_id`, `requested_at`.
- `sqlite_autoindex_help_assists_1` on `id` (unique).

Database triggers:

- `help_assists_identity_fixed` — schema-enforced lifecycle or immutability constraint.
- `help_assists_no_delete` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/hints/report.py`

### Direct SQL writers

- `src/learnloop/db/stores/help_assists.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_architecture.py`
- `tests/test_help_assists_schema.py`
- `tests/test_hint_telemetry.py`
- `tests/test_library_asks_migration.py`

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
CREATE TABLE help_assists (
  id TEXT PRIMARY KEY,
  surface TEXT NOT NULL CHECK (surface IN ('practice', 'workbench', 'guided_redo', 'tutor')),
  -- The Reader's assist kind (its §5.7). Outside the workbench the hint
  -- service writes 'hint' and, for an answer to a discriminating question,
  -- 'discriminate_answer' (hints spec §16.4 item 1); 'bridge', 'example' and
  -- 'compare_methods' are RW2c's.
  assist_kind TEXT NOT NULL CHECK (assist_kind IN (
    'hint', 'check', 'discriminate_answer', 'bridge', 'example', 'compare_methods', 'feedback'
  )),
  -- NULL only for a workbench problem not yet bound to an item (RW2a's
  -- workbench_sessions.practice_item_id, UX S2).
  practice_item_id TEXT,
  practice_item_hash TEXT,
  -- The workbench's practice session is filled at Submit (NULL until then,
  -- set once); every other surface writes it with the row.
  practice_session_id TEXT,
  workbench_session_id TEXT REFERENCES workbench_sessions(id),
  -- The attempt the assist was part of, filled at submit (submit_attempt,
  -- submit_dont_know); NULL while the attempt is open or if it never was.
  attempt_id TEXT REFERENCES practice_attempts(id),
  -- The client's stable submission key for the attempt the assist belongs to
  -- (practice_attempts.submission_id once it commits). The attach at submit,
  -- and its repair on a retried submit or a recovery, match on this key
  -- alone, so a row is never swept into another submission's attempt.
  submission_id TEXT,
  -- The form the help took (hints spec §4.2's table: its eleven plus
  -- continuation). NULL on rows that are not hints (a check, a bridge).
  hint_kind TEXT CHECK (hint_kind IS NULL OR hint_kind IN (
    'approach_question', 'discriminating', 'localize', 'waypoint', 'subgoal_plan', 'next_step',
    'error_specific', 'worked_parallel', 'authored', 'continuation', 'worked_chunk', 'walkthrough'
  )),
  -- The Reader's ladder: how much of the solution the help does (1-5). The
  -- level alone decides evidence (hints spec §5).
  level INTEGER CHECK (level IS NULL OR level BETWEEN 1 AND 5),
  -- The workbench's suggested rung, and whose level it was.
  offered_level INTEGER CHECK (offered_level IS NULL OR offered_level BETWEEN 1 AND 5),
  level_source TEXT CHECK (level_source IS NULL OR level_source IN ('offered', 'learner_pick')),
  -- Map edges ahead of the placement a waypoint points (hints spec §4.2).
  horizon INTEGER CHECK (horizon IS NULL OR horizon >= 1),
  route_id TEXT,
  from_node_id TEXT,
  target_node_id TEXT,
  -- approach_maps.id (H1); each map row is one version.
  map_id TEXT,
  strategy TEXT,
  -- NULL for an authored reveal: the item has the text.
  body_md TEXT,
  -- 0-based index into the item's authored hints (an authored reveal).
  authored_index INTEGER CHECK (authored_index IS NULL OR authored_index >= 0),
  -- The learner's work when the help was requested: a sha256 of the text and
  -- its length (the text itself is never stored here).
  work_hash TEXT,
  work_chars INTEGER CHECK (work_chars IS NULL OR work_chars >= 0),
  placement_json TEXT,
  chooser TEXT NOT NULL CHECK (chooser IN ('decider', 'fallback', 'learner_pick', 'none')),
  options_json TEXT,
  probabilities_json TEXT,
  -- The option the chooser drew, kept apart from the served kind so a
  -- contract downgrade keeps both (hints spec §4.2, §6.2).
  drawn_option_json TEXT,
  -- The probability the drawn option was drawn with (the chooser's joint or
  -- conditional draw; on a bridge or example row, RW2c's passage draw).
  propensity REAL CHECK (propensity IS NULL OR (propensity >= 0.0 AND propensity <= 1.0)),
  seed TEXT,
  policy_version TEXT,
  question_set_version TEXT,
  state_hash TEXT,
  request TEXT CHECK (request IS NULL OR request IN ('more', 'feedback', 'book_way', 'smaller_step')),
  feedback_text TEXT,
  -- The "doesn't connect" shortcut (the first draft's different_approach is
  -- withdrawn: it read the opposite way; hints spec §4.2, Reader C2).
  feedback_shortcut TEXT CHECK (feedback_shortcut IS NULL OR feedback_shortcut IN (
    'not_where_stuck', 'too_big', 'learner_route', 'notation'
  )),
  contract_failures_json TEXT,
  leak_flags_json TEXT,
  shown INTEGER NOT NULL CHECK (shown IN (0, 1)),
  -- Who counts the assist into the attempt's hints_used: the client (the
  -- authored hints it revealed itself) or the server's fold at submit. NULL:
  -- counted by neither (a discriminating answer, a feedback row).
  counted_by TEXT CHECK (counted_by IS NULL OR counted_by IN ('client', 'server')),
  model TEXT,
  prompt_version TEXT,
  input_hash TEXT,
  latency_ms INTEGER CHECK (latency_ms IS NULL OR latency_ms >= 0),
  requested_at TEXT NOT NULL,
  shown_at TEXT,
  -- When the submission reached the sidecar, before any grading: the end of
  -- "hint shown -> submit" (practice_attempts.created_at is stamped when the
  -- grade is applied, after the grader's latency). NULL when unknown.
  submitted_at TEXT,
  -- The client's open-to-submit seconds that same submission sent, stamped
  -- with submitted_at and only with it, so "seconds into the attempt" is
  -- measured on one basis: a grading fallback's retry sends a later latency
  -- (practice_attempts.latency_seconds keeps the retry's) and replaces
  -- neither. NULL when the submission sent none or its time is unknown.
  submit_latency_seconds REAL CHECK (
    submit_latency_seconds IS NULL OR (submit_latency_seconds >= 0 AND submitted_at IS NOT NULL)
  ),
  -- The Reader workbench's columns (its §5.7).
  step_snapshot_json TEXT,
  step_verdicts_json TEXT,
  first_questionable_step_id TEXT,
  error_kind_guess TEXT,
  about_step_id TEXT,
  continue_from_step_id TEXT,
  rivals_json TEXT,
  predicted_answers_json TEXT,
  eig_nats REAL,
  feedback_step_id TEXT,
  cited_span_ids_json TEXT,
  retrieval_manifest_json TEXT,
  alternatives_json TEXT
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
