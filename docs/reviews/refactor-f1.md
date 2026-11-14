# Refactor F1: column checks

Step F1 of arc F (strategy §2.8). A read that asks the database whether a column exists runs `PRAGMA table_info(t)`;
a pooled connection (`db/connection.py`, `_PooledSqlite`) closes at release when anything but a read ran in its
checkout, and a PRAGMA with an argument counts. So each such check cost an open, and a job that opened 5
connections opened 17. A `SELECT ... FROM sqlite_master` is a read and never marks: the table-existence helpers
(`table_exists`, `_has_table`, about 480 lines) cost no open and are not this step's subject; they are listed in §4.

## 1. The proof that a check is dead

The strategy's premise was "every writing open migrates, every other attach refuses a mismatch". Reading the open
paths shows it holds for the served doors and not for the rest:

| Open path | Migrates or refuses before reading? |
|---|---|
| `vault.repository.open_vault_repository` (every CLI command that writes, `_repository()` in `cli/runtime.py`) | migrates to the head under the vault lock |
| `vault.repository.vault_repository` | attaches a current database, else opens through the coordinator |
| sidecar `context.py:382`, phone host `host.py:attach`, MCP `remote/runtime.py:check_schema` | refuse a mismatch (`schema_is_current`) before `Repository.attach` |
| `Repository(path)` | `create_or_attach_current`: creates or refuses a mismatch |
| `Repository.attach(path, read_only=True)` and `connect(path, read_only=True)` in CLI reports (`cli/router.py` report, objective-report, card, trace; `cli/ad.py`; `cli/diagnose.py`; doctor; the usage and data-quality readers) | **neither**: nothing checks the schema first |

So "unreachable on an unmigrated database" cannot be proved for the last row. What does hold for every path that
reads a vault's database is the floor (ADR-019): `load_vault`, `run_doctor`, the phone host and MCP attach all refuse
a vault whose tag is below `OLDEST_SUPPORTED` (`mvp-0.58`), and `OLDEST_SUPPORTED` was the chain's head when it
landed (`afd5a257bc`, migrations through `254_decision_records_payload_retention.sql`). The owner upgraded the live
vaults to it with the code tagged `pre-floor`, which opens and migrates the database before it publishes the new tag.
So a database reached through a vault at or above the floor has every migration through 254, whichever door reads it.
The head is 255 (`apply_intents_conflicted`), the only migration above the floor.

**Rule used.** A check is class (a) when (1) the table or column it asks for was created by a migration at or below
254, found by `{SCRATCH}/colidx.py` over `migrations/*.sql` and, for dynamic names, by reading the migration, and
(2) the code runs on a vault's database (reached from a vault, not from an arbitrary file path). That proves the check
dead on any vault the code serves, including a read-only report run before any migrating command. It does not prove
anything for a database that is not a vault's: those are class (b).

This is a judgment call for the orchestrator: the proof rests on "tag at or above the floor implies migrations
through 254". Nothing in the code enforces that relation (a hand-edited tag, or an old database copied under a new
vault's tag, breaks it); `learnloop upgrade` and `doctor --fix-state` keep it true. A check that would now raise
`no such column` on such a database used to read a fallback.

## 2. Step 0: every site

The base (`f623e525ac`) has 56 `PRAGMA table_info` sites in 41 files (the strategy's 54 in 40 files; two more were
added by later work: `recognition/ledger.py` and `db/stores/router_objective.py`'s `fill_receipt`). Two further hits
in `scripts/table_review.py` are docstrings. Lines are at the base.

### Class (a): deleted (45 sites)

| Site | Checks | Absent branch | Table, column (migration) |
|---|---|---|---|
| `db/stores/observation_ledger.py:42` | `reference_status` | select without it | practice_attempts.reference_status (188) |
| `router_objective_switches.py:144` (`_has_received_at`) | `received_at` | `created_at` | practice_attempts.received_at (244) |
| `router_objective/checks.py:563` | `received_at` | `NULL` | 244 |
| `router_objective/scores.py:199, 219` | `received_at` (when a closure) | `NULL` | 244 |
| `daily_plan/router_card.py:447` | `reference_status`, `answer_confidence` | `NULL AS` | 188, 31 |
| `db/stores/router_objective.py:50` (`column_present`) and its 4 callers (`exposure.py`, `question_state.py`, `ask_availability.py` x2) | RO0's columns | return `{}` / False | 243 |
| `db/stores/router_objective.py:110` (`fill_receipt`) | RO0's columns, `active_seconds` | skip the column | 243, 252 |
| `learner/lesson_weight.py:671` | `learner_confidence`, `superseded_at`, `local_grader_id` | `{}` / `NULL` | grading_evidence (12, 1) |
| `confidence_events.py:204` (`_columns`, 3 uses) | `grading_evidence` hedge columns; `answer_confidence`; `probe_presentation_id` | `{}`, `[]`, `None`, `NULL` | 12, 1, 31, 28 |
| `learner_context.py:1328` | `reference_status`, `entry_surface`, `evidence_origin`, `declared_stuck`, `declared_dont_know` | `NULL AS` / `0 AS` | 188, 161, 161, 178, 53 |
| `diagnosis/split/history.py:781` | `answer_confidence` | `NULL AS` | 31 |
| `diagnosis/split/live.py:249` | `answer_confidence` | tap stays unread | 31 |
| `router/outcomes.py:330` | `plan_presentation_id`, `reference_status`, `probe_presentation_id` | `NULL AS` | 202, 188, 28 |
| `router_objective/combiner_data.py:153` | `received_at` | no `received_at` | 244 |
| `adaptive_difficulty/history_card.py:108` (`_columns`) | `received_at` per table | `created_at` | a fixed fact per table, now a constant pinned by `tests/test_f1_schema_facts.py` |
| `recognition/ledger.py:36` | `active_seconds` and 13 others | `NULL AS` | 252, 1-202 |
| `field/outcomes.py:322`, `placement/state.py:583` | `grading_evidence` columns | `{}` / empty | 1, 12, 34 |
| `reader/reader_observations.py:223, 273`, `reader/reader_report.py:424`, `diagnosis/text_gaps/sources.py:699` | `reader_authored_questions` (`scope_kind`, `answer_basis`, ...), `figure_predictions` columns | `[]` / `NULL AS` | 185, 208, 216 |
| `diagnosis/text_gaps/provenance.py:48` | `question_events` columns | `NULL` | 205, 117, 19 |
| `diagnosis/split/figure_trace.py:80, 87` (and the three-table check beside them) | `help_assists.figure_id`, `figure_predictions.assist_id` | `None` / no linked rows | 232, 216 |
| `attempts/stuck.py:264` (`_has_stuck_column`) | `declared_stuck` | `[]` / `None` | 178 |
| `instructional/interventions.py:443`, `adaptive_difficulty/replay.py:554`, `adaptive_difficulty/material_view.py:1644`, `adaptive_difficulty/data_check.py:75, 86`, `field/workbench_signals.py:278`, `learner_protection.py:574` | `reference_status`, `superseded_by`, `source_context_json`, `difficulty_rating`, `first_hint_progress`, `contract_subject_id`, `assessment_contract_version_id` | the older SQL | 188, 225, 117, 213, 219, 205 |
| `db/repositories.py:1812` (`_has_column`), `:6911` (`_has_projection_switches_column`), `:19549` | `reference_status`, `projection_switches_json`, `keep_local` | the older SQL / skip / `[]` | 188, 244, 198 |
| `db/stores/source_service.py:30` (`column_exists`, 4 callers), `:1332`, `:1432`, `:1733`, `:1816` | `reference_status`, `need_id`, `resolved_by`, `legacy`, migration 195's ledger columns, `usage_json`, `budget_json` | return / `NULL` / the pre-195 rule | 188, 191, 195, 163, 165 |
| `db/stores/write_provenance.py:581` (`_columns`) | the five identity tables' columns | skip the part | 1, 144, 170, 205 |

Each row was proved with §1's rule. `db/stores/source_service.py`, `router_objective/scores.py`,
`router_objective/checks.py` and `daily_plan/router_card.py` (the four the strategy named) are all here.

### Class (b)/(d): kept (11 sites)

| Site | Why kept |
|---|---|
| `substrate/data_quality.py:42, 109` | A read-only inspection of a database named by path (`data_quality_report(sqlite_path)`); the generic `rows()` takes any table and column list. Not a vault's database by construction. |
| `substrate/model_usage.py:92` | `usage` reads a database by path with `connect(path, read_only=True)`; its docstring promises older schemas. Not proved to be reached only from a vault. (d) |
| `substrate/dataset.py:648`, `ops/debug_time_store.py:19`, `scripts/table_review.py:747`, `scripts/sanitize_migration_head_fixture.py:181` | Introspection (column lists of a table to export or review), not an existence check; scripts open arbitrary files. |
| `db/stores/collection.py:22`, `adaptive_difficulty/operation.py:360`, `learnloop_sidecar/handlers/sqlite_admin.py:125, 225, 260` | Primary-key and column introspection of any table (a generic browser, the AD foreign-key graph). Nothing absent is handled. |

None of the kept sites is on a job's path (§3), so `db/schema_facts.py` was not added: nothing needs a cached fact.

### Class (c): tests that built a partial schema (1)

`tests/test_ro1_availability_reads.py::test_the_predicate_is_the_predecessors_column_below_the_tag_or_switched_off`
built a two-column `practice_attempts` in memory to prove `attempt_time_sql` falls back to `created_at` without
`received_at`. That branch is gone; the test keeps its other assertions.

## 3. Opens per job

Method: `tests/rospeed_join_helpers._journey` (the router mixture journey, 6 steps, both policies on fakes: three
objective prefetch jobs), with a wrapper on `db.connection._ConnectionPool.close` recording `opened` (real SQLite
opens) and `handed` (connects served) per job scope, and on `_PooledSqlite._wrapped` recording the first statement
that marked each checkout. Fast lane, connection reuse of `tests/connection_reuse.py` replaced inside the job by
production's pool (`reused_connections`).

| | opens per job (mean; each job) | connects handed per job | first marking statement |
|---|---|---|---|
| base `f623e525ac` | 14.7 (12, 16, 16) | 62.7 | `PRAGMA table_info` at `observation_ledger:42` (34), `router_objective_switches:144` (19), `checks:563` (11), `router_objective:50/110` (7), `lesson_weight:671` (3); writes `model_calls.py:23/73` (12) |
| after | 7.7 (7, 8, 8) | 62.7 | writes only: `model_calls.py:23/73` (12), the WAL switch (1) |

What is left is real: the receipt writes (`INSERT`/`UPDATE` of `model_call_receipts`) mark a checkout by the pool's
own rule (R4: anything but a read), which F1 leaves alone. The number is not "back to 5": the strategy's 5 predates
the receipts' writes inside the job.

## 4. Not done, and why

- The `sqlite_master` helpers (`table_exists`, `_has_table`, `has_table`, ...; about 480 lines in 120 files) were not
  touched: they are reads, mark nothing and cost no open. Most guard tables created at or below 254 and are dead by
  §1's rule; deleting them is a mechanical follow-up with no speed in it.
- `Repository.attach(read_only=True)` has no schema check (§1). Adding one would make §1's proof exact but changes
  what a read-only report does on a vault not yet migrated: the owner's call.
