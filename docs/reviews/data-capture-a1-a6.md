# Data capture A1-A6 and A8 (`data/capture-a1-a6`, base `6cf7a91ba8`)

The owner's long-horizon target (2026-11-02): delayed cold performance and time to goal, with a dataset that can test
policy offline and optimize online by the goal's end. Data not logged cannot be recovered, so this stage records what
later evaluation needs. It builds no planner, valuator or new policy. Owner approval: 2026-11-03. Source: Astra's report,
job `20261102-233208-oM6dy1` (static inspection at `9c594465a8`).

Out of scope and untouched: `measured_loss_enabled`, `VALUE_PER_NAT_MINUTES`, census, R3, A7, A9, TE2/TE3 logging.

## What each citation says at this base

Re-checked against `6cf7a91ba8`. Astra was right on every one; between its base and this one only
`scheduling/scheduler.py` changed (mobile PR-6's device filter), which moved its line numbers. Nothing else moved.

| Item | Astra's citation | At this base | Finding |
|---|---|---|---|
| A1 | `daily_plan/engine.py:799`, the plan's build has no `OfferTrace` | same line | confirmed |
| A1 | `scheduling/scheduler.py:665`, gate receipts need a session | **line 690** | confirmed |
| A1 | `daily_plan/engine.py:2751`, the block keeps project-probe valuations only | same | confirmed |
| A1 | `diagnosis/voi_stopping.py:900`, candidates cut to six | same | confirmed; the lookahead's `ranking` and `skipped_same_surface` (lines 1236-1237) were cut too, and are fixed with it |
| A2 | `router/plan_log.py:590`, waiting has no chosen item | same | confirmed |
| A2 | `router/outcomes.py:874`, `not_applicable` | **line 875** (the comment) | confirmed |
| A3 | `diagnosis/scoreboard.py:334`, stops at the first unassisted success | same region (330-358) | confirmed |
| A3 | `goals/goal_contracts.py:194`, due dates in versioned contracts | 198 (`due_at`) | confirmed |
| A4 | `router/outcomes.py:195`, hinted attempts excluded | same | confirmed |
| A4 | `adaptive_difficulty/outcomes.py:120`, any help is 0 | line 109 (`unassisted_success`) | confirmed |
| A4 | `adaptive_difficulty/report.py:382`, a day since the offer | same | confirmed |
| A5 | `daily_plan/router_chooser.py:401` | 404 (the return) | confirmed; `RestraintGate.decide` has the same branch, and A5 covers both |
| A6 | `teacher/delayed.py:193`, `teacher/brief.py:287` | 194, 287 | confirmed |
| A8 | `scheduling/randomization_layer.py:161`, `:209` | 161, 213 | confirmed; the same clamp fed `micro_randomize` and `commitment_parallel_assign`, and all three are fixed |
| (A7) | `scheduling/scheduler.py:3257` | 3302 | not built here |

## Serving, versions, switches

Serving changes (A2's measurement slots, A5, A6, and the outcome version they read) are the successor **mvp-0.44** on
mvp-0.43 (`DATA_CAPTURE_ALGORITHM_VERSION`, `learnloop.data_capture_upgrade`; `LATEST_ALGORITHM_VERSION` follows). Kill
switch `[data_capture] serving` (default true). Below the tag, or off, the plan and its router rows are mvp-0.43's:
`tests/test_data_capture_successor.py` runs both and compares the blocks and every row (ids aside), and each item's own
tests repeat it. Receipts (A1) are additive at every version behind `[data_capture] receipts` (default true); they write
only their own tables.

Migration **239** (five RECEIPT tables: `prefilter_payloads`, `prefilter_receipts`, `decision_objectives`, `reading_exposure_receipts`,
`decision_measurement_events`), head fixture `migration_head_240` (239 on the branch, renumbered at landing) rebuilt from the tracked 238, no other object or row
changed. M2a may claim 240 and mvp-0.45.

No new decision constant. A4's delay is the outcome contract's `RETENTION_MIN_DELAY_SECONDS`; A5's floor is
`router.epsilon_min`; A2's and A6's pitch and dates are `adaptive_difficulty.practice_band` and `teacher.delayed.*`. Two
structural numerics are classified in the registry: `data_capture_prefilter:_ROUND_DIGITS` (receipt size) and
`delayed_checks:_EXACT_TIE` (floating-point resolution, not a margin).

## A1, the prefilter receipt

`learnloop.data_capture.prefilter`, one receipt per committed decision, in the decision's transaction: `plan_block` (a
block, a stop, a learner pick), `plan_interrupt`, `today_offer`. `staged_p2` and `lesson_suggestion` keep no scheduler
build, so theirs come from their own row and say so (`scheduler_trace = 0`). A `learner_pick` from Today's offer inherits
its parent offer's. The report shows coverage by kind, so any gap is visible.

Five parts, each stored once by hash, compressed:

* `gates`: every scheduler exclusion by reason, with ids; the probe block; the cold deferrals. The plan's build now keeps
  an `OfferTrace`, so this holds with no session (Start builds before one opens).
* `classification`: each item, its lane and reason, and the **admission**: `probability_1`, or `probability_0` by reason.
  `router_probability` says `conditional_on_admission`; `admission_probability()` reads it.
* `upstream`: all VOI decisions of the build (probe episodes, further teach-backs, due project probes), the likelihood
  rows of in-episode probes, every evaluated probe's whole forecast whether or not it paid (`candidate_forecasts`: its
  likelihood rows, prior and minutes; about 3.8 KB raw and 0.5 KB compressed per candidate on the synthetic probe vault,
  unmeasured on real probes), their hash in `versions_json`, any upstream draw. No likelihood version exists today, so the
  rows themselves are the record.
* `inputs`: each considered item's priority, the session, minutes, requests, deadlines, open problems.
* `config`: the configuration snapshot.

The row itself holds counts, hashes, `code_revision` (`LEARNLOOP_CODE_REVISION`, else the checkout's commit, else the
package version), versions. From mvp-0.44 VOI receipts keep every candidate summary (`SiteDecision.record_all_candidates`);
below it they stay as they were, so existing rows do not change. A receipt never blocks a plan: refused, it rolls back
alone with a warning.

**Size.** Measured on a synthetic week through the real scheduler (30 LOs, 300 items, all considered; 25-minute plans,
every item answered): **13 rows a day** (4.6 receipts, 8.4 new parts) and **about 16 KB a day** stored, 180 KB
uncompressed; 59 parts stored for 160 references, the configuration once. That is about 6 MB a year. `inputs` and
`classification` change with each build, because priorities do. Today offers in heavier use add a similar amount per
offer at most. `learnloop data-capture report` states the actual numbers. Inline VOI receipts at the tag grow by about
300 bytes per candidate per decision; that is unmeasured on real probes (the synthetic week has none).

## A2, outcomes for reading, wait and stop arms

`learnloop.daily_plan.measurement`. A decision has an objective when an arm of its support has no action of its own, or
it drew one. **Frozen before the draw**: `RouterChooser` freezes it from pre-draw inputs and the draw follows; the rule
is the reading section's LO when a reading is in the support, else the staged pick's, else the support's first. A
follow-up's is its own LO. A test forces two different arms and compares the rows.

Outcome: `router_outcomes_v3` reads the lesson suggestion's ITT adapter for the reading, wait and stop arms (`R_cold`,
`S = R_cold`, `R_next` not applicable, arm, scope, measurement states on the detail). A practice or insert arm of the same
decision keeps its action-bound outcome and adds the same record under `objective_itt`, so every arm compares. A decision
logged before an objective could be frozen stays `not_applicable` (`no_frozen_objective`): it cannot be recovered.

Measurement: a `test_me_later` commitment (Check once), with `learnloop.delayed_checks`, the candidate rule, picker and
dates the teacher's delayed checks use (extracted so the plan need not import the teacher). Its minutes come off the
maintain lane's load first, so it replaces an ordinary slot and the other lanes keep theirs (`split_json.measurement_slots`).
States (`due`, `offered`, `answered`, `unavailable` with a reason) are written where Today prepares
(`measurement.settle`), once per reason and episode, idempotently: a due date opens an episode, each presentation opens one,
and a loss belongs to the newest of those.

A check is shared only where it can measure the decision: it comes due no earlier than `RETENTION_MIN_DELAY_SECONDS` from
it. A new check is dated at the first local midnight past that delay, whatever a short FSRS interval or the date's
truncation would say; one already due is left to its own decision and another item is asked. A check answered warm (the
learner practised the LO just before) satisfies the check but not the decision's outcome: it reads `unavailable`
(`answer_not_delayed`), and one replacement check is arranged from that moment, its states under a `replacement:` reason.
Decisions that shared the check share its replacement, as they would any pending check that opens past the window, so one
question measures them all. A replacement answered warm too ends the arrangement, since each one costs the learner a
question; ordinary retrievals still reach the outcome. Every reader folds the states chronologically: a replaced check
stops reading `due`, a later offer restores it, the same loss after that offer is a new transition, an answer is terminal.

**For A7:** `freeze`/`freeze_followup`, `record(..., experiment_id=...)` and the adapter take any decision; a test does it.

## A3, the honest time metric

`learnloop.router.first_delayed_success` (`first_delayed_success_proxy_v1`, labelled "first-delayed-success proxy, not goal
attainment"). From enrollment (the first contract version whose own recorded scope holds the LO, or a goal's creation where it has no
contract, or a learner's commitment on it, the earliest of those; with neither, the first exposure, and it
says so; a system-dated check is never one) to the first presentation the shared definition calls a completed delayed
attempt at the board's existing success threshold. The goal contract in force is pinned by id, version and due date, only when that version
covers the LO; no goal model. `active` (attempt latency, Reader active seconds) and `elapsed` (serve to answer, a visit's open to close, the part of a
reading block no visit of that LO already holds) are separate fields, never blended. Unfinished trajectories stay counted; missing latency is
coverage, not zero; a visit no reading names is `unattributed`, reported. Lessons' durations join with TE3.

`learner_minutes_to_cold_success` is renamed `learner_minutes_to_first_unassisted_success` (`b5_scoreboard_v2`), and the
two proxies join it as companions on the board.

## A4, failed independent completion and one delayed definition

`learnloop.delayed_completion` (`delayed_completion_v1`), read by `router_outcomes_v3` and AD's dose outcomes. The delay is
since the last exposure or practice before the attempt's own presentation (attempt, reveal, tutor question, reading), and
since the decision for an ITT outcome. Requested help on a delayed, unexposed presentation is `R_cold = 0`. A pre-exposed
presentation (AD's frozen flag, or a primed attempt with a reveal before its serve) and an abandoned one stay separate; a
primed attempt with no bound presentation is `primed_unbound`, AD's own exclusion. AD's value rule stays its own (`Y = 2`
is 1). Reading is an exposure on both sides. `reading_exposure_receipts` (RECEIPT, 239) is data capture's own record, whatever
AD's switches say: AD's list of sources, read by AD's collectors, with no cap, no material view and no doses, swept where Today
prepares under either data capture switch and first thing in `settle`. The source time is kept and outcomes derive at read
time, so a section read since the last sweep counts once Today next prepares. The router and the time metric read it beside
AD's `ad_reading_opportunities` and the LO-linked `source_exposure_events`. AD's dose outcomes read AD's receipts and the
exposure events through the material view, its boundary; they exist only for AD's own draws, which forecast logging writes.
Outcome version only: no certification, mastery, grading, FSRS or projection reads it. Below the tag, v2 exactly.

## A5, exploration floor when not_ready

Both `not_ready` branches (a block's, and the restraint's) now draw from the existing fallback distribution: every model's
weight on the staged rule, `router.epsilon_min` floor, logged seed and exact propensity, no model asked.

**Reachable under default config, from code.** Defaults: `router.enabled = true`, `router.mode = "mixture"`, so
`RouterChooser` chooses at the latest tag (`daily_plan/policy.py:53-64`). `router_decider` unset resolves to the code-default
`openrouter_decider` profile, which needs `OPENROUTER_API_KEY`; `router_llm` unset resolves to `ai.active_provider`
(`ai/routing.py:376-380, 409`). `RouteModels.readiness` reports each through `runtime_for_provider`, so the branch is taken
when **neither** route is ready: a new install with no key and no provider signed in, an expired sign-in on a machine with
no OpenRouter key, or `LEARNLOOP_ROUTER_MODELS=off`. With either model ready it is not taken. The owner's own routes were
not read (no credentials or vaults opened), so how often it fires for them is unverified; the report counts it.

## A6, the delayed-check picker

`delayed_checks.pick_with_receipt`: each item's own prediction (`predicted_item_success`, the `resolve_item_irt_params`
seam), the nearest the band's middle, a uniform draw over exact ties with seed, draw and `1/n`, on the check's row and its
commitment's provenance. Below the tag or off: the smallest id, as before. `teacher.brief.lo_prediction` is unchanged.

## A8, the tie-break propensity

Done (well under an hour). The uniform draws log `1/n`; a support below the dormant floor is flagged (`thin_support`) and
bind-logged, never clamped. Unconditional: it corrects a logged number and changes no draw.

## The report

`learnloop data-capture report --vault <path> [--json]`, read-only: receipts by kind with coverage, rows and bytes per
active day; objectives by arm with each arm's measurement states and why any is unavailable; R_cold on the frozen objective by arm (one
endpoint for every arm), each served action's own outcome apart; the proxy with
its coverage; the not_ready floor's draws, the delayed picks' ties, thin supports.

## Calls worth the owner's eye

1. **A measurement can ask an item already attempted.** The teacher's rule wants an unseen item, and a well-practiced LO
   often has none. With none, a check takes one of the LO's own that can still be taken cold, and the receipt says
   `pool: attempted`. The alternative was `unavailable` on exactly the LOs practiced most.
2. **A stop with nothing else feasible spends no question.** It keeps its objective (the plan's last LO) and reads ordinary
   retrievals (`natural`): no alternative was at stake.
3. **A6 reaches a lesson check's recorded mass.** `teacher.checks.cold_reference` asks the picker for the item the retention
   check would commit (its forecast's IRT parameters), sharing the check's seed so they agree. At the tag a new lesson
   check's mass can differ because the reference is now the real pick. Replay reads the recorded mass, so nothing past moves.
4. **`problems_to_cold_success` had the same flaw as the minutes metric** (no delay required). The landing renamed it
   `problems_to_first_unassisted_success`, in the same `b5_scoreboard_v2`.
5. **Stale names:** two comments in `apps/learnloop-tauri` (`DialogueProbe.tsx`, `PracticeScreen.tsx`) said
   `learner_minutes_to_cold_success`. The landing fixed them (comments only).
6. **The `router_outcomes` cache follows at `learnloop rebuild-derived-state`.** Every live reader (the router log and report,
   similar decisions, this report) derives under the vault's version; the upgrade itself does not rebuild the table.
7. **A check-only block is no learner pick.** A block holding only measurement checks is logged as the rules' placement
   and reads "a short check on something you studied comes first", not "the delayed check you asked for".

## Gate (implementation step; the full suite runs once at the landing)

Every pytest inside the memory-capped scope, at most `-n 6`.

* `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`.
* `lint-imports --no-cache`: **42 kept, 0 broken**.
* **Targeted: 11603 passed, 0 failed, 47 skipped, 6 xfailed** over every test file that names a changed module or function
  (the `daily_plan.engine`, `router.outcomes`, `router_chooser`, `voi_stopping`, `teacher.delayed`, `teacher.brief`,
  `randomization_layer`, `scoreboard`, AD report and outcomes, `plan_log`, `handlers.queue`, `held_grades`,
  `canonical_projection`, `build_due_queue`, `commit_checks` and `rebuild_all_derived_state` readers and tests, by
  `git grep`), plus `test_table_roles`, `test_coordinated_migrations`, `test_tracked_fixture_databases`,
  `test_cli_help_snapshot`, `test_sidecar_serializer_snapshot`, `test_config_refactor`, `test_architecture`,
  `test_registry_audit`, `test_ad_protected_tables`, `test_public_tip_guards`, `test_mobile_allowlist`, and the 59 files
  that pin the successor chain. After three last small edits (the freeze moved to just before the draw, the
  `check_replaced` state, the `counts` key): 107 passed 3 skipped on the router and A1/A2 files, then the 9
  `tests/test_data_capture_*.py` files, **111 passed**.
* Durability: `-m durability` over the 27 migration and schema test files, **28 passed**; `--durable-sqlite` on the A1, A2,
  migration and report files, **50 passed**.
* DB reference: `db_generate_reference.py`, `db_validate_reference.py`, **errors []** (schema head 239, 378 table notes since the re-review,
  1131 config leaves). The module and desktop catalogs are regenerated at the landing, as for other stages.
* Frontend and `src-tauri`: unchanged, so no npm or cargo step.
* No live call: every Python or CLI run outside pytest ran under `env -i` with empty, existing `HOME`, `CODEX_HOME`,
  `LEARNLOOP_CONFIG_DIR` and `LEARNLOOP_ROUTER_MODELS=off`. No model call, no spend, no GUI, no owner vault opened.

Test files added: `tests/test_data_capture_{a1_prefilter,a2_measurement,a3_time_metric,a4_delayed_completion,a5_not_ready_floor,a6_delayed_pick,migration,report,successor}.py`.

## Landing onto main

Main was `02f7cbec2d` (M2a with migration 239, and the owner's mobile patches). It was merged, not rebased. This stage is now
migration 240 and head fixture `migration_head_240`, rebuilt from main's `migration_head_239` with only 240 applied (`[240]`,
`integrity_check` ok, `foreign_key_check` empty, header bytes 1/1, no companion files). mvp-0.44 stays this stage's.

### Rulings

- R1: "F1 has now reopened twice on when Reader activity gets frozen, so under the stuck-loop rule the timing dependence goes: the router's outcomes, the time metric and the report read Reader exposures through one read-only function over the stored receipts and the source activity not yet swept. The sweep only freezes; no answer depends on whether Today has run. After this, a further timing case on this class is Low unless it realistically gives a warm answer a cold label in ordinary use."
- R2: "A measurement falling back to an already-attempted item when an objective has no unseen one is accepted; the receipt's pool says so, and the delay still runs since the last exposure or practice, so later analysis can filter it."
- R3: "A stop with nothing else feasible keeps its objective and spends no question."
- R4: "A warm-answered measurement gets at most one replacement check. Each one costs the learner a question, and the report's counts show how often it runs out. The owner is told."
- R5: "M2a lands first and takes migration 239, so this stage renumbers to migration 240 and head fixture migration_head_240 from main's head fixture. mvp-0.44 stays this stage's."
- R6: "Scoped verify job 20261103-190644-2tE7S8 found F1 and F11 closed. Its Medium, the sweep's whole-history remapping slowing ordinary Today reads, is fixed at landing with tests. Correctness rests on the shared live read, so the sweep gets its window back. There is no further Codex round; later cases on this class are Low."
- R7: "The frozen-cycles list stays frozen: the shared collectors and mapping move to a dependency-light read helper, and the two new exemptions go."

### Gate

At `6fe77d2f1b`, in the isolated environment, memory-capped:

| Lane | Result |
|---|---|
| `lint-imports --no-cache` | 42 kept, 0 broken; the frozen-cycles list equals main's |
| Full `pytest -n 8` | 25582 passed, 0 failed, 90 skipped, 47 xfailed (45:25) |
| Durability (`-m durability`) | 399 passed, 1 skipped |
| Owner lane, on fresh backup-API copies of `owner-copies-mvp035` | 83 passed, 2 known failures (`test_activity_backfill...duration`, `placement_fixture_copies[arxiv_v2]`), 4 skipped |
| Desktop | typecheck exit 0; vitest 2720 passed; `frontend:build` exit 0 |
| Mobile | `npm ci`, typecheck and build exit 0 |
| Generators | DB reference 379 table notes, errors `[]`; desktop 317 TS and 6 Rust notes; module catalog 1172 notes and 64 package maps; vault validation passes |

`cargo check` was not run: `src-tauri` is unchanged. No default changed, so no config fingerprint moved.

The first full run, before the fixes in `6fe77d2f1b`, was the stage's first whole-suite run: 7 failed, 25575 passed. One came from the
renumber (the phone's migration test). Two came from R7's helpers (AD's module no longer exporting two names, and the helpers missing from the
experiments contract's module list). Four had been hidden by targeted runs: the display label's blast-radius audit matching
`measurement_state` (now `fold_measurement`), the board's metric count, the CLI help snapshot after the rename, and the prefilter's
`git rev-parse` not on the approved process-launch list (now on it, beside the Codex provider's).

### Smoke

Fresh backup-API copies of `~/learnloop-backups/mvp043-20261103-copy`, every AI route at `127.0.0.1:9` (a resolver check over every
task found only those two profiles, plus `embedding`, disabled and keyless). Main's and the branch's code came from `git archive`
with `migrations/`. Today, the plan and the plan's steps went through the real handlers in process, with the clock frozen, each
calling module's ids from its own deterministic stream, and AD's background work off on both sides, since it races the snapshot.
Attempts in the walks are stubs. The walks ran on `19939c66a7`; the code changes after it are renames, one re-export and the
approved-list entry, and the before-upgrade comparison was rerun on the final tip: identical again.

**Before upgrading.** The copies are at head 238, so main's primary load applies `[239]` and the branch's `[239, 240]`: 240 is all this
stage adds. On all three vaults Today, the plan, its steps and every row written to main's tables are byte-identical to main, ids and
times aside. The only additions are data capture's own receipts (receipts default on): 3 to 4 prefilter receipts on the first day, 79
and 85 exposure receipts on `linear_algebra` and `probability`.

**Upgrade.** `learnloop upgrade --to mvp-0.44`, then `rebuild-derived-state`, succeeded on each copy, with no notes: "Upgraded vault:
mvp-0.43 -> mvp-0.44", then 3 LOs and 3 attempts (`arxiv_v2`), 8 LOs and 70 attempts (`linear_algebra`), 1 LO and 3 attempts
(`probability`).

**Upgraded, `[data_capture] serving` off.** Identical to mvp-0.43 on all three, version strings aside, lesson-check picks included.

**Upgraded, on: what differs over a stubbed week** (7 days, up to 8 answered steps a day), against main on the same walk:

| | `arxiv_v2` | `linear_algebra` | `probability` |
|---|---|---|---|
| Day 1, Today and steps | same | same, block's `chosenBy` reads `mixture`, propensity 0.96 not 1.0 | same |
| Order of the day's steps | 2 of 7 days moved one item | same every day | 1 of 7 days, one item inserted |
| `not_ready` draws | 41, 2 not the rule's pick | 18, 0 not the rule's pick | 17, 1 not the rule's pick |
| Today's list | same | one item (`pi_what_makes_capstone_02`) gone from the third day: a measurement check holds it until its date | same |
| Measurement checks arranged | 0 | 1, shared by 9 more decisions | 0 |
| Objectives | 1 stop (natural) | 10 practice, 1 stop | 2 stop (natural) |

A lesson check's item, on the owner's history: of the 19 LOs with two or more candidates, 14 pick a different item (the pitch rule, A6).
No lesson ran in the walk, so nothing here was served that way.

*Would a learner notice?* Rarely on any one day. The floor's draw occasionally moves one item in the day's order. The visible change is the check: on `linear_algebra`, walked on to its date (Nov 14),
the item came back as the day's first step, replacing 2.3 maintenance minutes, and its one answer closed all ten decisions. The learner
would see one question they haven't been shown for a while, leading the day, and an item missing from the list until then.

**Receipts off.** Both switches off: no rows in any of the five tables. Receipts off with serving on: no prefilter rows; objectives and
exposure rows are still written, because those are the serving side's.

**A week's records.** Every committed decision has its receipt and link: coverage 1.0 for `plan_block` and `today_offer` on all three (the
3 `probability` decisions without one predate the first receipt). Rows and bytes per active day: 16.6 and 11.2 KB (`arxiv_v2`), 9.9 and
7.0 KB (`linear_algebra`), 10.0 and 8.9 KB (`probability`).

**Inline VOI on real probe episodes stays unmeasured.** All 58 real episodes (31, 9 and 18) are `pending_items`, so the walk evaluated no
probe and `candidate_forecasts` is empty on every real receipt. What did run is teach-back's inline VOI: at most 14.9 KB raw and 1.9 KB
stored in one part. An evaluated probe's forecast in the receipt is shown only by the synthetic tests.

**The report.** `learnloop data-capture report` left the database hash and the WAL's size unchanged on each copy. On real history, before
any walk: `first_delayed_success` carries its proxy label, and `linear_algebra` reads 0 of 21 reached, `probability` 0 of 17, `arxiv_v2` 0 of 3,
all counted as unfinished. That reading is right: no attempt on these vaults qualifies. On `linear_algebra` all 70 attempts fall in six days in
July and read `not_delayed` (61) or excluded (9). Coverage reads 11 of 62 attempts timed, 3 of 3 and 0 of 0, in the same order. After the week's
stubs: 3 of 21, 3 of 17 and 7 of 8 reached.

**A section read with no Today preparation since**, on a real mapped section of `probability`: practice on its LO, the section completed two
days later, the answer 30 minutes after that, with no sweep. The answer reads `not_delayed` and there is no first delayed success. After a sweep:
the same, with the receipt on record. `linear_algebra` agrees.

**The rest.** `rebuild --shadow`: 0/0/0 on all three, for facets, mastery and schedule. `model_call_receipts`: 0 new. Non-loopback sockets:
0. Processes: `git rev-parse` once per process (the prefilter's revision) and `powerprofilesctl`; no Codex process.

**Today's time against main, below mvp-0.44 and with serving off, receipts on** (`get_today_queue` in ms, a second process on each copy, 15
repeats):

| | main, median (min) | branch at mvp-0.43 | mvp-0.44, serving off |
|---|---|---|---|
| `linear_algebra` | 163 (153) | 166 (141) | 172 (160) |
| `probability` | 121 (117) | 125 (122) | 126 (123) |
| `arxiv_v2` | 107 (104) | 113 (111) | 112 (110) |

So +3 to +9 ms. `settle` is 5 to 6 ms of it and the offer's prefilter 0.2 ms. That is about main's own median-to-minimum spread (3 to 10 ms),
but it is a consistent small cost, not zero. Each process's first Today pays more (+7 to +86 ms, its first mappings and the `git` call),
and the first Today after this lands pays about +390 to +530 ms once on the vaults with Reader history, to write the receipts.

### The phone (M2a)

Tested in `tests/test_data_capture_phone.py`, and on a `linear_algebra` copy through `acting_as`. A phone has no plan, so at a request origin:

* **`settle` still runs**, through `prepare_queue_build`: the sweep, the states, and any replacement a warm answer earned.
* **No objective is frozen and no measurement slot exists:** the phone's `today_offer` decisions have none, and it builds no plan row.
* **A measurement check the phone can't show is held back**, and stays `due` for the desktop, where it is served. It reads
  `intent_check_held`, not `device_ineligible`, because the check's own gate asks the device's. So the phone's "waiting for the desktop" count
  doesn't include it. That is M2a's behaviour for any Check once.
* **A check it can show is in its list**, at the rank the build gives it (21 of 40 on the copy), not first: a phone has no slot to lead with.
  An answer on the phone measures the objective.
* **The offer's receipt is linked**, with surface `today_offer`; the decision's surface is `phone_queue`, and so is the offer's
  `entry_surface`. The held-back item has admission probability 0.
* **A check the phone showed reads `due` until answered.** `offered` means a plan presentation, and a phone has none, so `offered` undercounts
  phone use. Open below.

### What the owner must run

Close the app, MCP and the phone page first. Then, on each vault: `learnloop upgrade --to mvp-0.44`, then `learnloop rebuild-derived-state`,
so `router_outcomes` moves to v3. The first Today after that writes the Reader's receipts once. `[data_capture] serving = false` is the kill
switch, and `receipts = false` stops the prefilter.

### Open items

* AD's dose outcomes with `forecast_receipts` turned off still read only AD's receipts, so they miss Reader activity in the off period. The
  router and the time metric aren't affected.
* A7 is the next stage on `experiment_id`.
* R3's router report and the census.
* R4: the report's counts show how often a replacement runs out. The owner is told here.
* A phone's offer writes no `offered` state (above). Counting it needs a rule for what a list row means, since every poll writes an offer.
* A check the phone holds back isn't in its "waiting for the desktop" count (M2a's, for any Check once).
* Timing classes that stay Low under R1 and R6: a provenance link added after a section was recorded, and a question or passage view whose
  section gains a coverage row, read differently with and without a sweep between.
* Inline VOI on real probe episodes stays unmeasured until one is evaluated.
