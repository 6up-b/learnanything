# Reader RW5d P5: figures ahead of need (stage record)

- **Spec:** `docs/specs/spec_reader_show_me_figures_v1.md` rev 2, phase P5: §6.9, §10b, §12.3, §13.2b, §14, §15, gates G-SM27..G-SM30. The as-built note is in §14.
- **Branch:** `reader/rw5d-p5-prefetch` in `learnanything-dl2`, base `1a33bb5db3` (main: TE1 + C4, mvp-0.41, migration 234).
- **Migration:** `236_figure_prefetch.sql`. followups-nov2 claims 235; the runner is set-based, so this keeps 236 or renumbers at landing.
- **Head fixture:** `fixtures/migration_head_236`, renamed from `migration_head_234` (README section added; every hard-coded path, 55 files, renamed; `SCHEMA_HEAD = 236` in both DB reference scripts).
- **Switch:** `figures.prefetch_enabled`, **default off** (the stage brief's decision; the spec's Q21 recommends on: the owner turns it on at the P5 checkpoint). Caps `[figures.prefetch] max_daily_builds = 10`, `max_daily_render_minutes = 30` (`keep`).
- **New route:** `ai.routing.figure_prefetch_judge` (unset: the active provider, the plan under T1). Not in `METERED_PRICE_SETTINGS`, so never offered OpenRouter; a non-subscription route is never called.
- **Successor:** none (§1).
- **Live calls:** none. Every model in the tests is a fake (the judge, the figure author, the power reader, the pause reader). No paid or CLI command ran against any vault. The only database work outside pytest was the head-fixture rebuild on a backup-API copy under `fixtures-local/p5-head236/` and the DB reference scripts, all under `env -i` with empty, existing HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR.

## 1. Successor decision (`docs/algorithm-change-playbook.md` step 1): no successor

| Change | Persisted meaning? |
|---|---|
| Background builds (origin `prefetch`, `build_mode` prefetch) | **No.** They change *when* a figure exists. Figures are content: scoring, scheduling, projection, serving, grading and evidence read none of them (the `evidence-never-reads-figures` contract). An opened prebuilt figure is any figure (tier 1 outside an attempt, P3's hint-equivalent inside one). |
| `figure_prefetch_decisions`, `plan_usage_pauses` | **No.** RAW_LEDGER, read only by `learnloop.figures` (the decision model, the report). `tests/test_figures_prefetch_boundary.py` pins that no evidence, scheduling, plan, hint or AD module names them (AD's table classes name them only to deny them). The decision model predicts opening behaviour, outside the learner model (SM8). |
| The plan trigger | **No.** `get_daily_plan` builds and returns the plan exactly as before; afterwards a background trigger reads the stored plan. The plan never reads figures. |
| A prebuilt figure making P3's `explore_figure` precondition true sooner | **No:** which help is offered, not evidence (P3's ruling). |

The defaults snapshots moved, all 32, only because the effective config gains the keys; recomputed with `defaults_fingerprint_for_version` (a second pass changes none).

## 2. What P5 ships

### 2.1 The service (`src/learnloop/figures/prefetch.py`, a composition layer)
One pass per trigger: candidates → filters → decide → log → builds → outcomes. Nothing imports it back but `learnloop_sidecar/prefetch_runtime.py` (pinned; the frozen-cycles contract ignores its two function-local reads of the stored day plan and a lesson's stored plan on that promise).

**Triggers (§10b.2)**, queued by `prefetch_runtime.notify` (returns at once; one drain thread per context on `ctx.background_jobs`, so a close cancels and joins it):

| Trigger | Hook | Candidates | Goal |
|---|---|---|---|
| `plan` | `get_daily_plan`, after the view is built (`_schedule_prefetch`) | the stored plan's reading block's section | section judge |
| `section` | `reader.mark_section_progress` (after keep-ahead) | the next section in book order with no withheld span | section judge |
| `offer` | `reader.ask` (tutor; not on a cold administration) and `reader.library_job` when done (organizer) | `offered_spans` (the press's own ledger-confirmed check), anchor-only, once per offer | none |
| `lesson` | `lesson.turn` when the lesson has a plan | plan nodes not in `state.landed`, on their delivered passages (≤ 8 spans of the first passage's reading) | the node's `visual.goal_text` when it carries one (`goal_author` teacher), else anchor-only |
| `gap` | the plan and lesson hooks, and `PostAttemptWorker.after_gaps` after a gap drain | open misconceptions and learner-text gaps on the stored plan's and open lessons' topics (`learner_state.open_gap_statements`: the author's protection-filtered read, with ids) | gap judge |

**The judge (`figure_prefetch_judge`)**: listwise; section mode gets one section's blocks with exam and held-out spans removed (`withheld_message` per block) and no learner data; returns at most `PREFETCH_SECTION_CANDIDATES` (3) blocks with an optional goal and `p_open`. Unknown ids, duplicates, more than three, or `p_open` outside 0..1 are refused and asked once more with the problems in the context; a second bad answer decides nothing. Cached as a `judgment_ledger` receipt (task `figure_prefetch_judge`, keyed by the section's content hash and prompt version). Gap mode gets the statement, the topic and the passage text; never an attempt, item, key or rubric.

**Filters (code)**: the switches (`show_me` for goals); `withheld_message` on every span; the blocks of any unresolved item of today's stored plan (`item_exclusions`); a shown figure already on this passage and goal; a request already decided whose horizon is open (`request_key`). The build repeats the protection (`check_request`).

**The decision (`figures/prefetch_model.py`, pure numerics)**: `EU = P(open) · W − C` in learner minutes (u.minute scales both terms, so the sign never depends on it).
- `logit P = m + d_kind + α·logit(p_open_content) + β_src`, ADF (`adf_numeric.adf_update`) over closed, built decisions in time order; `α ~ N(1,1)` (llm_content), `m ~ N(0,1.5²)` (legacy, debt), `d_kind ~ N(0,τ²)` and `β_src ~ N(0,σ²)` with τ, σ a posterior over `POOLING_GRID` (25 grid points, weights by each filter's log normalizer).
- `W`: log-normal mean of measured pressed latencies (rich tiers: request → stored row; quick tiers: the figure author's completed call durations in `model_call_receipts`), mixed by the trigger kind's measured prebuild tier mix, else the pressed mix; with no mix yet, the author call's duration (the wait every press has at least). Nothing measured: no W, decision `skip` (structural: no data, no prebuild).
- `C = P(pause | today's plan requests + this build) · blocked minutes per pause`; pause logistic priors −3 and 1.5, sd 2 (legacy, debt), filtered from `plan_usage_pauses` and the days' plan requests; blocked minutes measured (pressed plan calls failed inside pause windows × mean plan call latency). No pause measured: no cost (so until a pause is seen, every candidate with a W has EU > 0 and the caps alone cut the queue, in sampled-EU order).
- One Thompson draw decides; `propensity` = share of `POSTERIOR_DRAWS` (64) further draws with EU > 0; `posterior_digest` (sha256 of the posterior's state) and `model_version` logged.
- Then, in sampled-EU order: off mains → `deferred_power`; plan paused or the author route not the plan → `deferred_plan`; daily builds or render minutes used up → `capped`.

**Builds**: one at a time (`PREFETCH_CONCURRENT_BUILDS`); each waits for no foreground work (`figures/foreground.py`: the server marks the learner-facing methods in `FOREGROUND_METHODS`; the figure handler marks a pressed build's job), up to `FOREGROUND_WAIT_SECONDS`, then leaves the rest: decisions still to build are retried by the next pass (`pending_builds`). Each build rechecks the switch (the vault as loaded now) and the power, then calls `service.build_prefetch_figure` (origin `prefetch` under `quiet()`; its `FiguresGate` key adds the switch and its hold is `power.background_hold`, so the switch or unplugging stops it before its next request). The rich spawner is the background one (no grant) and only when `figure_rich_author` is a plan route; a prebuild's rich job holds on the same condition (`rich.run_rich_job`). The decision gets `request_id` and the figure's `input_hash`, set once.

**Outcomes (§10b.5)** at each pass: plan → the plan's day ended or it closed; section → `completed_at` on that section; lesson → `closed_at`; offer → the local day it was made has ended (see §4); gap → no longer open, or a newer plan was built. `opened` (a `figure_opened`/`attempt_figure_opened` event on the decision's figures after it), `asked` (unbuilt, and a pressed request later on the same passage), `neither`, `void` (the passage withheld now).

**Pauses**: each pass appends the plan session's latest usage limit to `plan_usage_pauses` once (by hit time), with the day's plan requests and known tokens.

### 2.2 The figure service and the rich job
- `build_prefetch_figure`; origin `prefetch` refused everywhere else (a ContextVar set only there); `_validated_prefetch` (an anchor of a book, no attempt host, region or revision; goal by `prefetch` or `teacher`).
- The `figure_requests` row: `build_mode` prefetch and `prefetch_decision_id`; the rich payload's `build_mode` prefetch (P2b's niced, capped render).
- Listing: with the switch off a prebuilt figure nobody pressed for is not listed; once a press reused it, it is listed like any figure. While on, a prebuilt figure is listed under its passage with the existing collapsed line ("▸ interactive version", §6.9): no frontend change.
- "Not right?" on a prebuilt figure is the learner's request on its passage (origin `selection`, keeping the stored goal and who wrote it).

### 2.3 `power_state()` (`figures/power.py`)
Linux sysfs (a machine battery discharging, or no mains/USB supply online, is battery; device-scope batteries ignored), power-profiles-daemon `power-saver` counts as battery, macOS `pmset`, Windows `GetSystemPowerStatus`; anything unreadable is battery (fail closed). `LEARNLOOP_POWER_STATE=mains|battery` pins it for copy runs.

### 2.4 Hosts
Desktop sidecar only: `notify` refuses a secondary context (the phone host and the hub service attach with `load_secondary`) and a vault with the switch off; then no runtime is made and nothing is read or written.

### 2.5 The report
`learnloop reader report --json` gains `figures.prefetch` with the switch on (composed by the CLI, `prefetch_ledger.add_report_block`; `reader_report.py` is untouched, so no `reader → figures` edge): decisions and outcomes by trigger, the opening and pause posteriors (prior → posterior), measured waits and tier mixes, blocked minutes per pause, pauses with and without prebuilds earlier that day, skipped for power, plan and caps, the mean propensity.

### 2.6 Registry, roles, references
- `params/parameter_registry.py`: inventory `figure_prefetch`, `figure_prefetch_model`, `figure_power`; every module constant registered (priors as `prior` with treatment, prior_basis and scale in the rationale; the rest `keep`); `_ConfigRule`s for the switch and the two caps.
- `db/table_roles.py`: both tables RAW_LEDGER; AD's `protected_tables`: both DENIED.
- Disclosure row `figures_prefetch` for the judge.
- DB/config references regenerated; leaf count 1123, table notes 371.

## 3. Gate

See the stage's structured result for the exact commands and counts; the test files run are listed there.

## 4. Deviations from the spec, and why
1. **Default off**, not Q21's on: the stage brief's instruction. Off is rev 1 exactly.
2. **The gap passage** comes from the topic's own provenance spans (`build_cross_source_spans`, the explain intent's first list), not `find_sources_for_caller`: retrieval can make hosted (metered) embedding or rewrite calls, and a prebuild is never metered.
3. **The offer horizon** is the end of the local day the offer was made (the reading session ends by then at the latest); the reader has no durable "thread closed" record to read.
4. **The plan load** is the day's plan requests; known tokens are recorded with each pause but not yet in the model (tokens are reported for some routes only, §10b.3).
5. **`void` for the switch going off** is not written: with the switch off nothing runs, so nothing is written (byte-identical); a row whose horizon passed meanwhile closes at the next pass by its horizon.
6. **Lesson planned visuals**: TE1's `PlanNodeV1` has no `visual` field yet (P4b, in flight, adds teacher visuals). The trigger prebuilds a node's passages anchor-only, and takes `visual.goal_text` whenever a stored node carries it.
7. **RW7b's path** is not consulted for the next section (book order only, skipping withheld sections).

## 5. Owner items
- The P5 checkpoint: a week of prefetch on the desktop with the report's `prefetch` block (opens versus builds, pauses, skipped for power) before turning `figures.prefetch_enabled` on by default (Q21).
- The legacy priors (`KIND_PRIOR_*`, `PAUSE_*`) are LP debt (LP §3.3).

## 6. Open items
- With no pause yet observed, C = 0, so every candidate with a measured wait builds up to the daily cap; the Thompson draw then orders rather than gates (spec-faithful; the caps are the guardrail).
- Quick-tier W is read from every completed `figure_author` call in `model_call_receipts` (the paid-call wrapper records each one, owner `figure_author`, pressed or prebuilt alike: the same call, the same wait). A prebuilt call therefore also measures W; that is the duration a press would have waited, so it is kept.
- P4b (teacher visuals) and followups-nov2 both touch `figures/service.py`; merge at landing.
