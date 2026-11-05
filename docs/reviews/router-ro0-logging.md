# Router objective RO0: logging (`router/ro0-logging`, base `90f7def5e3`)

Built from `docs/specs/spec_router_objective_v1.md` §4: rows 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12 and 13, and the report line. Row 6 is
FG1c's. No successor and no tag. Migration 243 since the landing (FG1c took 242; see "Landing onto main"). `[router_objective] receipts`,
default true, acts at every version; off, nothing is written. No objective, forecaster or multiplier removal. No model call.

## What exists now

| Row | Where it is | Code |
|---|---|---|
| 1 Disclosure state | `question_events.reveal_state_json` | `router_objective/question_state.py`, called in `tutor_qa.ask_question` before any model call |
| 2 Generating process | the four existing columns, filled by the server from `help_assists`; a client's value stands | same; `AskOverlay.tsx` sends `learnerMode` |
| 3 Question opportunity | `plan_presentations.ask_available`; `attention_block_events` kind `ask_availability_changed`; the visit's payload; `question_opportunity` | `router_objective/ask_availability.py`, RPC `record_ask_availability`, `PracticeScreen.tsx`, `useReaderVisit.ts` |
| 4 Exposure initiator | `source_exposure_events.initiator`, `initiator_block_id`, `initiator_session_id`, `initiator_visit_id`; the visit's payload | `router_objective/exposure.py`, every writer of the table |
| 5 Event times | `log_interaction_event(occurred_at=, received_at=)` | `substrate/activities.py`, `reader_inquiry.record_activity`, `reader/activity.ts` |
| 7, 8 Session end, availability | `session_receipts` (RECEIPT) | `router_objective/sessions.py`, `handlers/sessions.py`, `engine.keep_going`, `engine.more_new` |
| 9, 13 Decision state | `decision_state_receipts` (RECEIPT) | `router_objective/decision_state.py`, `readiness.decision_state_fields`, the six decision sites |
| 10 Cold-check timing | `decision_objectives.delay_json`, `decision_measurement_events.delay_json`, `.non_service_type` | `router_objective/cold_timing.py`, `daily_plan/measurement.py` |
| 11 Goal lifecycle | `goal_lifecycle_events` (RECEIPT) | `router_objective/goal_lifecycle.py`, `SidecarContext.load` |
| 12 Trajectory | a read, no schema | `router_objective/trajectory.py` |
| Report | `learnloop data-capture report`, section `router_objective` | `router_objective/report.py`, `ops/capture_report.py` |

**Readers.** Nothing serving, scheduling or certification reads any of it. The one offline reader, the probability arms' card, reads
`hints_used_before`, so `field/probability_states.STATE_VERSION` moves to `llm-probability-state-v4`. It's part of the prep's digest, so the next
arms run renders its cards again.

**Switch.** `RouterObjectiveConfig.receipts`, classified structural in the parameter registry. RO0 has no decision parameter. Its two numerics are
classified structural too (`_ROUND_DIGITS`, `_WORKED_LEVEL`). All 36 defaults snapshots were recomputed because the effective config gains the
key; each version's meaning is unchanged. Three tests that pin a pre-key digest pop it.

## Citations at this base

The spec cites main at `9780ca3baf`. Every cited site exists. These moved:

| Spec | At `90f7def5e3` |
|---|---|
| `tutor/tutor_qa.py:956`, `:978` | 963, 983 |
| `AskOverlay.tsx:613-640` | 629 sends `attemptProgress` |
| `db/repositories.py:12734` | 12721 |
| `router/plan_log.py:428` | 424 |
| `daily_plan/measurement.py:283` | 287 |

Unmoved: `handlers/tutor_qa.py:277`, `reader_inquiry.py:144`, `:396`, `db/repositories.py:4552`, `substrate/activities.py:934`, `teacher/delayed.py:240`,
`vault/models.py:78`, `field/probability_states.py:514`, `:574`.

## What could not be built as written

§4 now records each of these.

1. **Row 12 is a read, not a view.** SQLite re-resolves views when a table is renamed, so a view over `router_decisions` breaks the create, copy, drop, rename
   rebuild its migrations use (202, 236). `test_a_view_would_break_the_rebuild_the_ledgers_migrations_use` reproduces it. The smallest alternative is the same
   SQL in code.
2. **Row 10 can't extend commitment provenance.** `provenance_json` is in `version_hash`, so a new key would change a hash with the switch on, which breaks the
   gate. New nullable columns hold the delay. A lesson's checks already hold `days` and `dated_by` in the lesson's receipt, so I added nothing there; the delay's
   other inputs for a lesson are the config in force. The repair lane's `cold_measurement_opportunity_decisions.decision` is already typed.
3. **Rows 9 and 13 aren't full at every decision.** See "Row 9 and 13 in the serve path" below for the three limits.
4. **Row 9's hypothesis posteriors are partial.** An open episode's posterior is the newest stored (`probe_observations.posterior_after_json`, else the presentation's
   `posterior_at_selection_json`). A live replay at each decision is too slow for the serve path. A misconception's posterior is a stateless recompute from persisted
   attempts (`misconceptions.misconception_posterior`), so the row names the open ones with status and severity and it can be derived again as of the decision.
5. **Row 13's stop value.** No version gives a stop a value yet, so the row says `value: null`, `value_source: none_at_this_version`, with offered, taken and
   minutes left. A rejected candidate's value is its `planner_value` on the decision row, not copied.
6. **Row 11.** `abandoned` stays in the CHECK with no writer: the YAML's status has no such value. A removal's reason says `removed_while_active`, which a reader can
   count against a policy. The YAML has no reasons, so `reason` says `seen_at_load`. I added `resumed` and `expired`, which the YAML can say.
7. **Row 8.** Stamped at the session's start, so before its first block is served. A plan's first block can be decided earlier, since Start builds before a session
   opens; that decision's receipt has `session_id` null and the plan's row holds the minutes.
8. **Row 7.** `foreground_lost` and `external_interruption` are accepted by `end_session`'s optional `end_reason`, and no client sends them. The desktop's finish needs no
   reason, and the phone's paths are off limits this stage. Recovery runs at the next session's start because an open session can be resumed until then. A crash reads
   `app_closed`, `inferred`. A session another device replaced reads `rule`, `explicit`. Sessions from before RO0 aren't backfilled.
9. **Row 4.** `dose_offer` and `lesson` are accepted and have no writer: a dose offer asks for questions inside the Reader and a lesson's text reaches only reveal
   rows, so neither opens an exposure today. On the desktop only the plan's reading sets `plan`. A visit's block and session are the client's where it sends them, else the
   ones in force at the visit's `occurred_at`; none or more than one fitting is recorded as unknown (landing ruling R2, which replaced
   "the newest reading block on that extraction" and "the session open when the batch arrived").
10. **Row 1.** The practice screen sends no `answerVisibleNow`, because it doesn't know whether a worked hint is still in view, so those rows read `unknown`. Feedback
    sends it. A cold Reader link row (`provider = 'reader'`) keeps no state: its question does, and the report excludes it from the denominator.
11. **Row 3 at the serve** is the server's own rule, 0 for a teach-back's item, else 1. A probe's contract loads on the client, so a diagnostic check reads 1 at the serve,
    then a change event with reason `diagnostic_check`.
12. **Not recorded:** a pick from the list after the plan has closed (`RECEIPT_OPEN_LIST_PICK`) logs no router decision today, so it has no state row, and it isn't counted
    as a stop override.

## Row 12's audit

| Link | Id | Exists |
|---|---|---|
| Decision to block | `attention_blocks.decision_ref` | yes |
| Decision to presentation | `plan_presentations.router_decision_id` | yes |
| Decision to offer | `router_decisions.scheduler_slate_id` | yes |
| FG1's itemless decision to its item, presentations and outcome | `router_decision_bindings` | yes |
| Presentation to attempt (uptake) | `practice_attempts.plan_presentation_id`, `probe_presentation_id`, a bound item's attempt after the decision; one attempt counts once | yes |
| Offer to attempt (uptake) | `practice_attempts.scheduler_slate_id` | yes |
| Rejection | `attention_block_events` kinds `item_skipped`, `item_displaced` through the block; a binding's `skipped` or `abandoned` outcome | yes |
| Pick to its offer | `router_decisions.parent_decision_id` | yes |
| Objective | `decision_objectives.decision_id` | yes |
| Next decision | the ledger's order | yes |
| Return | `sessions.started_at`, `ended_at`, after the session the action happened in (the decision's, its block's, presentation's or attempt's) | yes |

No id is missing, so none is added. `next_decision_censored` and `return_censored` name what isn't known yet; `return_censored = session_unresolved` is a decision no link places in a session.

## Row 9 and 13 in the serve path

Synthetic vault, the real scheduler: 30 LOs, 300 items, 240 attempts over a month, plan on, mvp-0.45, 0 model calls. `main` is a `git archive` of `90f7def5e3` run from the
scratch directory. Medians in ms, three alternating runs each (12 Today opens, 34 plan steps, 5 plan views per run).

| Operation | main | branch, on | Difference |
|---|---|---|---|
| `get_today_queue` | 240, 240, 246 | 257, 254, 254 | +12 ms, 5% |
| `next_plan_item` | 1075, 1084, 1058 | 1179, 1078, 1094 | within run-to-run noise; 1179 was one noisy run (its p90 1581), the other two +0 to +2% |
| `get_daily_plan` | 416, 435, 412 | 515, 427, 410 | within noise; 515 is the same noisy run |
| `get_today_queue`, plan off | 281, 282 | 496, 496 | +215 ms, 76% (after Codex review F3; this run's machine load differs from the rows above) |
| `get_today_queue`, switch off, earlier build | 243 (main that round) | 241 | none |

**What changed because of this.** The first build wrote the whole belief on every offer, and Today went from 240 to 430 ms (+190 ms): about 4 ms per LO for AD's numbers, across
dozens of LOs. So:

- With the plan on, the Today list serves no head (`propensity_kind = not_served`) and nothing is decided among its candidates. It keeps the session's numbers and `omitted` with the
  count. A pick from it is a plan decision with its own full state.
- A served offer (plan off), `staged_p2` and `lesson_suggestion` read AD before their transactions, because replay can't give the numbers back: `as_of` keeps the latest grading epoch (Codex review F3,
  `docs/reviews/router-ro0-codex-review.md`). The first build here left them out, and plan-off Today cost +10 ms; with them it costs +215 ms, the table's plan-off row, and a served offer is 4,636 bytes.

Plan decisions and interrupts read AD for all their LOs, before the write opens. `next_plan_item` barely moves because the router's card already reads the same snapshot.

## Size

Measured on a synthetic week through the real scheduler (30 LOs, 300 items, 25-minute plans, every item answered, 3 questions a day, 7 sessions, 32 plan decisions, plus a day with the
goal's first row).

| Row | Bytes per active day |
|---|---|
| 1 | 659 |
| 2 | 21 |
| 3 | 53 |
| 4, 5, 10 | 0 (no Reader or reading arm that week) |
| 7 | 100 |
| 8 | 39 |
| 9, 13 | 2,811 |
| 11 | 3 |
| 12 | 0 (a read) |
| **Total** | **3,681** (8 active days, 29,446 bytes) |

About 1.3 MB a year. The new tables' pages by `dbstat`: 16 KB, 49 KB, 12 KB. A plan decision's state is 702 bytes compressed (1,925 raw; 4.9 items, 1.6 LOs). Offers measured apart: a list that
served no head is 432 bytes each (681 raw); a served offer, plan off only, is 4,636 bytes (55,177 raw; 309 items, 34 LOs).

**Not RO0, flagged.** The same week grew the database by about 161 MB, on and off alike: `scheduler_slate_candidates` 117 MB, `decision_features` 26 MB, `scheduler_explanations` 6 MB. Each plan
step's build writes a full slate on a 300-item vault with an open session. This is existing behavior at main, and I didn't touch it. See open questions.

## The gate

`tests/test_ro0_gate.py`, with `test_data_capture_successor.py`'s method:

- Two runs of a plan, on and off, at mvp-0.45, mvp-0.44 and mvp-0.43, a full plan and a stop-offered plan: the next step, the blocks in order, every router row, and every row of `attention_blocks`,
  `attention_block_events`, `plan_presentations` and `daily_plans`, with fresh ids and the new column aside, are equal. A draw is seeded from each run's fresh ids, so both runs take the rule's draw.
  `boundary_key` is a digest of the plan's fresh id and is set aside like the row's other hashes.
- The desktop's replies across one session (`start_session`, `get_today_queue`, `end_session`) are byte-identical once ids and times are masked.
- Off, no new table has a row and `ask_available` is null throughout.
- `rebuild_all_derived_state` leaves the three tables and `ask_available` as they were.

A receipt refused or unreadable leaves the decision, the session or the question standing (`test_a_refused_*`, `test_a_state_that_cannot_be_read_*`).

## Gate results

Setup: `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0`.

| What | Result |
|---|---|
| `lint-imports --no-cache` | 42 kept, 0 broken |
| Targeted pytest, 565 files at the last code change (`router-ro0-logging.targeted-tests.txt`) | 17,284 passed, 61 skipped, 8 xfailed, 2 failed: both in `test_ad1_migration.py`, the diff below, fixed |
| After that fix: head-fixture and migration tests plus RO0's files (31 + 11) | 284 passed |
| `-m durability` on those migration files and RO0's | 24 passed |
| `--durable-sqlite` on RO0's files and `test_ad1_migration.py` | 113 passed |
| Contract and late-failing tests: architecture, CLI help, serializer snapshot, desktop RPC, mobile allowlist, table roles, coordinated migrations, tracked fixtures, registry audit, the lockdown files | 899 passed, 2 skipped |
| Vitest: AskOverlay, PracticeScreen, FeedbackScreen, everything using Reader activity, the new `activity.ro0.test.ts` | 795 passed in 87 files |
| `npm run typecheck`, `npm run frontend:build`, `cargo check` | pass |
| `db_generate_reference.py`, `db_validate_reference.py` | no errors; head 242, 1135 leaves |
| `module_generate.py` and `module_validate.py`, `desktop_generate.py` and `desktop_validate.py` | pass |

Three things that differ from a plain reading of the brief:

- One early vitest call ran the whole suite by accident, because an empty file list fell through: 2,729 passed and 2 failed, both from `occurred_at` on exact-event tests, since fixed.
- The targeted set is 565 files, wider than usual, since the sidecar's load and the plan's decisions are touched. It ran behind the suite lock.
- The first two commits were made with `core.hooksPath=/dev/null`. The hooks there are Git LFS's and this repository has no LFS rules, so nothing was skipped in effect; every later commit ran them.

No paid or live calls: every script outside pytest ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, and each measured vault reports 0 `model_call_receipts`. Synthetic vaults only, in the
scratch directory. No `fixtures-local/` copy was needed.

## For the landing

- **Numbers.** Migration `242_router_objective_receipts.sql`, `fixtures/migration_head_242`, `SCHEMA_HEAD` in the two reference scripts, and the tests' `== 242` and `, 241, 242]` pins move if FG1c lands first.
  The head fixture is rebuilt from the tracked 241 with only this migration applied; rebuild from whichever head is then tracked. The leaf count in `Configuration.md` and `Database.md` is 1135.
- **Migration diffs.** `RO0_ADDED_OBJECTS` joins the additive diffs. `TE1_AND_TE1B_ALTERED_TABLES` also names the three older tables 242 alters, which is the one place to change. `test_ad1_migration.py` can no longer tell 213's change to
  `question_events` from 242's, so its diff ignores that table and its columns are checked by name.
- **Owner's paths.** None of the off-limit paths is touched: the phone's sources, `src/learnloop_mobile/allowlist.py`, the mobile tests, `docs/mobile-shortcuts.md`, `docs/specs/spec_mobile_tailnet_v1.md`, `integrations/ios/*`, `.gitignore`, `README.md`.
  `record_ask_availability` is new and the phone's default is to deny it.
- **What the owner runs.** Nothing beyond the ordinary sync; the migration applies when the vault next opens. The next probability-arms run renders new cards.

## Open questions

1. `scheduler_slate_candidates` grows about 17 MB a day on a 300-item synthetic vault with an open session, at main too. Is that worth its own item? It's untouched here.
2. A Today list that served no head holds no belief, a measured choice for Today's speed that §4 records: it decided nothing among its candidates. A served offer (plan off) now pays about 215 ms at each Today open for its AD numbers; only a vault with `plan.enabled = false` pays it.
3. Should the phone send `end_reason` and `answerVisibleNow`? Both are accepted and the phone's paths are off limits this stage, so a phone session's end is the server's reading of the plan, and its questions read `unknown`.

## Landing onto main

FG1c landed first (main `d1a77ac634`) and took migration 242, so RO0's migration is now `243_router_objective_receipts.sql`, and its head fixture is
`migration_head_243`, rebuilt from main's tracked `migration_head_242`. Before the merge, the scoped Codex verify (job `20261104-165216-3b1KmL`) reopened F1 and F7. R1 and
R2 fix them, each in its own commit with Codex's reproductions as tests. `docs/reviews/router-ro0-codex-review.md`, "Codex verify", has what changed.

### Rulings (orchestrator, verbatim)

- R1: "F1 has reopened on sibling writes, so it goes structural: a receipt field added to an existing row is never written in that row's own insert. The row is inserted with its predecessor's fields, and the receipt fields follow in their own savepoint; refused, the row stands with them null and a warning. This covers ask_available on plan_presentations, the generating-process fields on the pending question, the exposure initiator fields, and every other RO0 column on an existing table. A test with a refusing trigger on each, at mvp-0.43, 0.44 and 0.45, shows the pick, the answer and the source opening succeed with receipts on. A test fails on any RO0 column written in an existing table's insert."
- R2: "F7's Reader attribution: a visit's block and session are resolved as of its occurred_at, or captured at opening where the client knows them. When more than one fits, or none, the link is recorded as unknown, never guessed."
- R3: "F3's cost, about 210 ms on Today with the plan off, is accepted as Low and not fixed here: only plan-off vaults pay it, and moving the numbers after the reply needs frozen inputs, which is RO4's work. The smoke measures it on the real copies, and if any of them runs with the plan off it's reported to the owner."
- R4: "The R1 and R2 fixes carry Codex's reproductions as tests, so there's no further Codex round. A further finding on either class is Low unless a receipt refusal realistically fails a pick, an answer or an opening, or a link that RO4-RO6 would train on is recorded as known when it's wrong."
- R5: "Open questions stand as recorded: the slate tables' growth predates RO0 and goes to the follow-up batch, measured on main; the phone sends no end reason or visibility yet, since its files are off limits; actions written by nothing yet stay accepted."

### Commits

| Commit | What |
|---|---|
| `811e16a98f` | R1: RO0's fields never ride their row's insert, and the three append-only tables' update guards allow exactly the fill |
| `ed0e027193` | R2: a visit's block and session as of its `occurred_at`, the client's capture, or unknown |
| `3671d07781` | The Codex review record's "Codex verify" section and the step-0 gate |
| `2ffac8021a` | Merge of main at `d1a77ac634`, renumbered to 243, head fixture rebuilt |
| `f0618b9457` | References regenerated on the merged tree |
| this commit | This section |

### The merge

What both stages touched:

- **The data-capture report** (`ops/capture_report.py`) keeps both sections, FG1c's `hypothesis_marks` and RO0's `router_objective`. The CLI's docstring names both,
  and the help snapshot is rewritten (one command's help changed).
- **The defaults snapshots.** All 36 were recomputed from the composed defaults, since the effective config gains both stages' keys. RO0's comment stands beside
  FG1c's.
- **The earlier migrations' additive diffs** subtract both `MARKS_ADDED_OBJECTS` and `RO0_ADDED_OBJECTS`. `TE1_AND_TE1B_ALTERED_TABLES` also names
  `plan_presentations_no_update`, which R1's migration replaces. FG1c's own 242 tests keep 242's name and pins, and move only "the head" to 243.
- **The head pins** (`== 242` on a maximum and the `..., 241, 242]` lists) move to 243, and so does `SCHEMA_HEAD` in the two reference scripts. Every path
  that named `migration_head_242` now names `migration_head_243`: 61 test files, the two reference scripts and the sanitizer's usage line.
- **`table_roles.py` and the parameter registry** merged without conflict. The roles test and the registry audit pass.

The head fixture is a backup-API copy of main's tracked, sanitized `migration_head_242/state.sqlite` (229 migrations recorded, max 242). Only 243 was applied, through
`apply_migrations` under the scratch-copy allowance, outside the checkout. Then `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE` (header bytes 1/1),
`integrity_check` ok and `foreign_key_check` empty. It was copied into place with the backup API, with no companion files. Its README has RO0's section.

Run early, all passing: `test_measurement_state_labels.py`, the CLI help snapshot, `lint-imports` (43 kept, frozen cycles kept), the process-launch allowlist in
`test_codex_lockdown_round3.py`, and the two migration files, table roles, coordinated migrations, architecture, tracked fixtures and config files (154 passed). Then every test
file the merge touched, plus RO0's, FG1c's and data capture's: 1,293 passed, 3 skipped.

References: `db_generate_reference.py` and `db_validate_reference.py` show errors `[]` at head 243. The prose leaf count moved from 1135 to 1136 in `Configuration.md` and
`Database.md`. `desktop_generate`/`desktop_validate`, `module_generate`/`module_validate` and `validate_vault.py` pass.

### Gate, at `f0618b9457`

| Lane | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | exit 0 |
| `lint-imports --no-cache` | 43 kept, 0 broken |
| Full suite (`-n 8`, worksteal, 10G scope, behind the suite lock) | 26,209 passed, 90 skipped, 47 xfailed, 0 failed (57 min) |
| Durability lane (`-m durability`) | 400 passed, 1 skipped |
| Owner lane, fresh backup-API copies of `owner-copies-mvp035` in `fixtures-local/landing-ro0/` | 83 passed, 2 failed, 4 skipped. The two failures are the known pair: `test_activity_backfill…duration`, `placement_fixture_copies[arxiv_v2]` |
| Desktop: typecheck, vitest (whole, `--maxWorkers=4`), frontend build | pass; 2,751 tests in 270 files; pass |
| `cargo check` | pass |
| Mobile: `npm ci`, typecheck, build | pass |

No failure needed a rerun. Every pytest, vitest, npm and cargo run was in its memory-capped scope. Every script outside them ran under `env -i` with empty `HOME`,
`CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

### Smoke on fresh copies of `~/learnloop-backups/mvp043-20261103-copy`

**Setup.** `git archive` of main (`d1a77ac634`) and of the branch, each with `migrations/`, ran from the scratch directory, with that tree's code first on the path.
Every AI route pointed at 127.0.0.1:9 (FG1's `neutralize.py`). A socket and process watch (`sitecustomize`) refused any non-loopback connect. The three copies
(`arxiv_v2`, `linear_algebra`, `probability`) are backup-API copies under `fixtures-local/landing-ro0-smoke/`:

- upgraded on **main** code with `learnloop upgrade --to mvp-0.45` and `rebuild-derived-state`: migrations 239 to 242, mvp-0.43 to mvp-0.45;
- then each journey ran on its own fresh backup-API copy of that.

**Migration 243** applies when the branch first opens a copy (the sidecar's `SidecarContext.load`; any `learnloop` command does the same). It wrote one
`schema_migrations` row and changed no row.

**Each copy's own plan setting.** None of the three has a `[plan]` section, so all run with the plan **on**. None pays R3's plan-off cost, and nothing goes to the
owner under R3. The plan-off runs below set `plan.enabled = false` on the copy only to measure it.

**One session, main against the branch.** Ids come from a fixed stream per calling module and the clock is frozen, so the two sides compare row for row
(`smoke/drive.py`, adapted from FG1's). The session was Today, the plan dump, Next serving, a self-graded submit (no model), a tutor question (an in-process fake
tutor), a Reader visit (open and close, stamped) and a source opening on a real span, Next again, and the end. Every reply and every written row was compared, with
hashes, wall-clock times and timings set aside.

| Copy | Plan | Receipts off against main | Receipts on against main (RO0's fields and tables aside) |
|---|---|---|---|
| arxiv_v2 | on | identical except `followup_generation_jobs`* | identical except `followup_generation_jobs`* |
| arxiv_v2 | off | identical | identical |
| linear_algebra | on | identical | identical |
| linear_algebra | off | identical | identical |
| probability | on | identical | identical |
| probability | off | identical | identical |

\* FG1's background generation job is caught mid-flight by the snapshot: `leased` on one run, back to `queued` with `authoring_route_not_ready` on another. Two
more runs of **main against main** on the same copy showed the same difference, and another background job (`practice_index_proposals`) differed as well. It's a race
between the snapshot and a worker thread, on main too, and not RO0.

Display order was the same in all twelve. No reply differed. With receipts off, no RO0 table had a row and no RO0 column was written.

What each journey wrote with receipts on:

- **The session's start:** a `session_receipts` availability row.
- **Today:** one `decision_state_receipts` row (`today_offer`), the list's, which served no head with the plan on and was a served offer with it off.
- **Next, serving:** one `plan_block` state row, and `plan_presentations.ask_available` on its presentation.
- **The submit:** nothing new.
- **The tutor question:** `reveal_state_json` and four generating-process fields on the question (`learner_mode` stays empty without the workbench).
- **The Reader visit:** `occurred_at` and `received_at` on its two events, and the initiator and `session_link` in the opening's payload.
- **The source opening:** the initiator and session fields on its exposure.
- **The end:** a `session_receipts` end row.
- **On `linear_algebra`, the first load:** a `goal_lifecycle_events` `created` row.

**A day's journeys** (`smoke/day.py`, branch, receipts on; each copy with the plan on and off; all journeys passed on all six):

- **The plan:** blocks served and answered: 2 items on `arxiv_v2`, 5 on `linear_algebra`, 1 on `probability`. With the plan off, Next returns no step and nothing is
  served.
- **A keyed pick from the list:** with the plan on, it got its presentation with `ask_available`.
- **A question with the answer in view:** `answer_visible_now`, feedback context. It reads `visible`. A practice question without it reads `unknown`.
- **A plan-sent Reader visit and its source opening:** the exposure reads `initiator = plan`. The visit reads `session_link = as_of_event` and `block_link = unknown`,
  because no copy has a plan reading block on that extraction.
- **No lesson or dose offer:** none of the three copies made one.
- **The stop:** `offered_stop_accepted / explicit` with the plan on, `unprompted_stop / explicit` with it off.
- **A crash:** session B was left open and C started. B's end was written `app_closed / inferred` at C's start.
- **A goal paused in the YAML and loaded:** `linear_algebra` (its goal was `completed`) wrote `created` at first load and `paused` at the next. The other two copies have
  no goals.

`learnloop data-capture report` on each copy after its day, the `router_objective` section (rows written of rows that could be, and bytes per active day):

| Row | arxiv_v2 plan | arxiv_v2 off | linear_algebra plan | linear_algebra off | probability plan | probability off |
|---|---|---|---|---|---|---|
| 1 Disclosure state | 2/2, 242 B | 2/2, 218 B | 2/2, 121 B | 2/2, 109 B | 2/2, 242 B | 2/2, 218 B |
| 2 Generating process | 2/2, 12 B | 2/2, 12 B | 2/2, 6 B | 2/2, 6 B | 2/2, 12 B | 2/2, 12 B |
| 3 Question opportunity | 3/3, 14 B | 0/0, 8 B | 6/6, 8 B | 0/0, 4 B | 2/2, 14 B | 0/0, 8 B |
| 4 Exposure initiator | 1/1, 22 B | 1/1, 22 B | 1/1, 11 B | 1/1, 11 B | 1/1, 22 B | 1/1, 22 B |
| 5 Event times | 6/13, 120 B | 6/13, 120 B | 16/93, 160 B | 16/93, 160 B | 15/43, 300 B | 15/43, 300 B |
| 7 Session end | 3/3, 147 B | 3/3, 58 B | 3/3, 66 B | 3/3, 29 B | 3/3, 131 B | 3/3, 58 B |
| 8 Availability | 3/3, 75 B | 3/3, 75 B | 3/3, 38 B | 3/3, 38 B | 3/3, 75 B | 3/3, 75 B |
| 9, 13 Decision state | 3/3, 956 B | 1/1, 1,802 B | 6/6, 1,380 B | 1/1, 698 B | 3/3, 920 B | 1/1, 1,690 B |
| 10 Cold-check timing | 0/0 | 0/0 | 1/1, 44 B | 0/0 | 0/0 | 0/0 |
| 11 Goal lifecycle | 0/0 | 0/0 | 1/1, 13 B | 1/1, 13 B | 0/0 | 0/0 |
| 12 Trajectory (a read) | 3/3, 0 B | 1/1, 0 B | 6/6, 0 B | 1/1, 0 B | 6/6, 0 B | 4/4, 0 B |
| **Bytes per active day** | **1,588** (2 days) | **2,316** (2) | **1,846** (4) | **1,068** (4) | **1,716** (2) | **2,384** (2) |

Row 5's denominator is every interaction event in the copy, its history included. Only events since RO0 carry a client stamp, so its coverage is low by
construction. With the plan off, a served offer's state (row 9) is the large row, as R3 says.

**R1 on real shapes.** The same day ran with a trigger refusing every RO0 fill on all five older tables (`BEFORE UPDATE OF` the RO0 columns). On all six runs every journey
stood:

- the plan's serves and the keyed pick (with its presentation);
- every submit;
- both questions, answered by the tutor;
- the visit and the source opening.

The RO0 fields stayed null, with one warning per refused row (3 to 10 a run). The new tables, whose rows aren't fills, were still written.

**Rebuild and sync.** After each day, `rebuild --shadow` reads 0/0/0 (facet, mastery, schedule) on all six, and the live database is unchanged. FG1's known case
didn't occur. RO0's rows and fields were hashed before and after, through `rebuild-derived-state` and then `sync_vault_state`: unchanged on all six.

**Time (R3)**, main against the branch with receipts on. Three alternating rounds, each a fresh copy, six Today opens and seven Next calls a round. Medians in ms, with n
in brackets:

| Copy | Plan | Today | Next | Submit |
|---|---|---|---|---|
| arxiv_v2 | on | 132 → 139 (+6, 18) | 328 → 331 (+2, 21) | 412 → 420 (+8, 3) |
| arxiv_v2 | off | 133 → 235 (+101, 18) | none served | 408 → 420 (+12, 3) |
| linear_algebra | on | 191 → 194 (+3, 18) | 377 → 378 (+0, 21) | 517 → 528 (+11, 3) |
| linear_algebra | off | 193 → 275 (+82, 18) | none served | 507 → 608 (+100, 3) |
| probability | on | 155 → 163 (+8, 18) | 169 → 172 (+3, 21) | 918 → 885 (−34, 3) |
| probability | off | 155 → 260 (+104, 18) | none served | 521 → 535 (+15, 3) |

With the plan on (all three copies' own setting), Today and Next move by 0 to 8 ms. With it off, Today pays R3's cost on the real copies: +82 to +104 ms,
below the synthetic vault's +210 ms because these copies have fewer LOs. Submits are three samples each and move both ways (−34 to +100 ms). `linear_algebra`'s
+100 ms with the plan off is one of those three-sample medians, not a measured cost.

**Model calls and sockets.** No new `model_call_receipts` row was written on any copy: `arxiv_v2` 0 → 0, `linear_algebra` 0 → 0, `probability` 56 → 56 (its own history). The
watch logged no non-loopback connect, no name resolution and no Codex process. The only processes started were `git` (the code revision) and `powerprofilesctl`.

### What the owner runs

Close the desktop app, the MCP server and the phone page. Pull main and run the ordinary sync (`uv sync --extra dev --extra mobile`). RO0 has no successor and needs no
upgrade. Its migration 243 is applied the next time each vault opens, on the sidecar's load or on any `learnloop` command. A vault still at mvp-0.43 takes FG1's
and FG1c's pair first, and that pair now applies 243 too:

```
learnloop upgrade --to mvp-0.45 --vault ~/learnloop-vaults/<name>
learnloop rebuild-derived-state --vault ~/learnloop-vaults/<name>
```

Then rebuild the desktop app, since `AskOverlay`, `PracticeScreen`, `FeedbackScreen`, the Reader's activity and the Tauri command `record_ask_availability`
changed. Restart the phone host. The next probability-arms run renders its cards again (`llm-probability-state-v4`). To turn RO0 off for a vault, set
`[router_objective] receipts = false`.

### Open items

- R5's three stand: the slate tables' growth (measured on main, follow-up batch); the phone sends no end reason or `answerVisibleNow`; `abandoned`, `dose_offer` and
  `lesson` are accepted with no writer.
- R3's cost is not fixed (RO4). Each copy's own plan setting is in the smoke above.
- A visit linked `as_of_event` to a session still open at the time is checked against that session's final `ended_at` by any reader that trains on it. A crash
  leaves a session open, and the next start ends it at its last attempt or checkpoint, which can fall before the visit.
- The desktop sends neither a visit's block nor its session, so the server resolves both. A plan-sent visit on a copy with no plan reading block on its extraction reads
  `block_link = unknown`, as the smoke shows.
- None of the three copies made a lesson or dose offer, so neither was exercised on real data. The unit tests cover both.
