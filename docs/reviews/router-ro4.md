# Router objective RO4: the objective, live (`router/ro4-objective`)

Spec: `docs/specs/spec_router_objective_v1.md` §8 (as built: §8.11). Base `cf1019a3cf` (RO2's branch: mvp-0.46,
migration 245). Successor **mvp-0.47** (`ROUTER_OBJECTIVE_ALGORITHM_VERSION`) and migration **246**
(`246_router_objective_traces.sql`), both rechecked at landing after RO2 lands. Fakes only: no paid call was made in
this stage, and no real request was sent.

## What exists

| Part | Where |
|---|---|
| Successor, upgrade (projection activation, journalled), defaults snapshot, kill switch `[router_objective] enabled` and the seeds | `algorithm_versions.py`, `router_objective_upgrade.py`, `config/schema.py` (`RouterObjectiveConfig`), `config/template.py`, `router_objective_switches.objective_on` / `objective_scores_on` / `sensors_in_value_on`, `params/parameter_registry.py` |
| §8.1 the value estimator: one cutoff `C`, `R(t,σ]`, the flat-load tail adaptive to the belief, `T_C` as net continuation, θ draws with common random numbers, paired SE, every action interface (review, new practice, reading, probe as a bundle, repair, teach-back, lesson, offer branches, the stop offer's two branches), durations sampled | `router_objective/value.py` |
| §8.4 the memory model: AD's predictive and FSRS R, Bayesian logistic combination (labelled prior, Laplace fit), FSRS vectorized | `router_objective/memory.py` |
| The frozen belief of one decision (topics, goals and use weights, session minutes, `m̄`, return gaps, `p_accept` from §4 row 7, the learner's duration spread, the actions) | `daily_plan/objective_inputs.py` |
| §8.2 the frame: soft budget (no minutes or lane filter, `minutes_left` negative, stop at every reversible boundary), the projection's finite list unchanged, Today's copy | `daily_plan/engine.py` (`_feasibility`, `decide`, `PlanPolicy.soft_budget`), `lanes.py`, `types.py` (`PlanState.soft_budget`), `view.py` (`minutes_past_plan`, `minutes_are_a_suggestion`, `objective_decision_id`), `apps/learnloop-tauri/src/app/todayPlan.ts` |
| §8.3 the two policies and the mix: `π_L` (`router_llm_choice_v3` over the decision-level H3 card, the reference row), `π_Q` (argmax `Q̄`, ties by support order, third prefetch job), staged and the Decider as advice, failure redistribution, `w`, the restraint's two-policy mix | `daily_plan/objective_chooser.py` (`ObjectiveChooser`, `ObjectiveRestraintGate`), `daily_plan/objective_card.py`, `adaptive_difficulty/history_card.decision_sections_entry`, `router/requests.py` (`PolicyRequest`, `parse_llm_policy`), `router_objective/mix.py`, `daily_plan/policy.py` |
| §8.4 card v3: candidates' goal dates and days to date | `router/card.py` (`goal_dates`, `CARD_V3`), `daily_plan/router_card.py` |
| §8.5 goals: `use_weight` in the content hash and out of the support hash, `use_weight_change`, the stated default, copied at creation and confirmation, adjustable | `goals/goal_contracts.py`, `goals/use_weights.py`, `learnloop_sidecar/handlers/goals.create_goal`, `set_goal_use_weight` |
| §8.6 the price: session minutes with the 60-minute gap, the daily seed and its floor, the guard, the grid posterior (built, serves nothing) | `router_objective/price.py`, `objective_chooser.day_price` |
| §8.7 the weight: `D̂`, what carries no score, the Gaussian posterior with `2B`-day bins, no peeking, `w = ℓ_L + (1-ℓ_L-ℓ_Q)·p` | `router_objective/weight.py`, `objective_chooser.current_weight` |
| §8.8 the trace: RECEIPT table, written with the decision; CLI; the why's "how was this chosen?" | migration 246, `db/stores/router_objective.insert_trace`, `router_objective/trace.py`, `cli/router.py` (`trace`), `learnloop_sidecar/handlers/router_objective.py`, `apps/learnloop-tauri/src/screens/today/DailyPlanView.tsx` (`ObjectiveTrace`), `src-tauri` passthroughs |
| §8.9 the report | `router_objective/objective_report.py`, `learnloop router objective-report` |

## For the owner before landing: what it costs and how it is enabled

- **Enabled at the tag by default**, where R2b's mixture already serves (`router.mode = "mixture"`). `learnloop upgrade`
  (default target) moves a vault from mvp-0.46; nothing recorded changes. Off: `[router_objective] enabled = false`
  serves mvp-0.46's mixture and frame exactly (tested against mvp-0.46 with one pinned seed).
- **Calls per decision: one `router_llm` request** (`router_llm_choice_v3`) per plan block decision and one per mid-block
  follow-up decision (`router_llm_restraint_v3`), in the prefetch, as the older chooser made one before; the **Decider**
  is still asked once per decision (advice, the comparator). So the request count per decision is the predecessor's;
  what grows is the LLM's input.
- **Tokens per LLM request:** the card is at most `llm_card_token_budget` = 48,000 UTF-8 bytes (about 12-16k tokens), plus
  the options, the reference row and about 1,500 bytes of instructions in; the output room reserved is the router's
  floor, 16,384 tokens, with one retry at double on truncation (`router_runtime.call_llm`), while the answer itself is a
  probability and three forecasts per option and at most three sentences (a few hundred tokens). A learner with little
  history sends a few kilobytes. The predecessor's card was the learner-state card (typically 2-6k tokens).
- **A typical day:** with 25 suggested minutes and 5-8 minute blocks, about 4-6 plan decisions (each boundary, the last
  one often a stop) and 0-3 follow-up decisions: about 5-9 LLM requests and as many Decider requests, so at most about
  9 x 16k input tokens and a few thousand output tokens a day. On the ChatGPT plan route these are `estimated_only`
  ($0 against `router.max_daily_cost_usd`); on a metered route they count against the router's daily guard ($5 by
  default), which refuses before sending. **No real request was sent in this stage**, so no measured tokens exist; the
  first-day report on a copy measures the timeout rate (§8.3).
- **Latency:** the numeric policy measured 0.49 s at the day's first decision (which also computes the day's price seed
  and frontier at 64 draws) and 0.22-0.31 s at later ones (8 draws, 2 to 6 options with stop, 180-day rollouts) on the
  synthetic test vault (`tests/router_mixture_helpers.mixture_env`, 7 topics); with no model set up it runs on the
  serving thread inside `router.timeout_seconds` (8 s) and reports a timeout past it (tested). The first version of
  the tail looped per topic and took 4.5 s a decision; the session is now one vectorized step per lap over the topics.

## Choices where the spec was open, or the code had moved (the smallest alternative, recorded)

1. **π_Q with no model set up** (§8.3 says a third prefetch job): with no route ready there is no prefetch at all (the
   predecessor's `not_ready` branch), so π_Q runs on the serving thread with `router.timeout_seconds` as its deadline.
2. **"N_θ = 8, more until the deadline"** (§8.1): more draws are added only while the LLM policy is still out (doubling,
   up to `rollout_theta_draws_max` = 64, `keep`), so a decision never waits on its own extra precision.
3. **The staged rule's pick under the soft frame** is stop once fewer than 5 of the plan's minutes are left, so the
   failure fallback (and its floor) keeps the plan's minutes as a suggestion rather than serving without end.
4. **A drawn stop** closes the plan as the predecessor's stop did; "keep going" is the override and RO0 already logs it
   (`stop_response`, `offered_stop_overridden`). No new override UI.
5. **AD's learning parameters**: the rollouts use AD's prior means and variances for `γ` and the reading curve (AD's
   priors module); reading the bank's posterior for them needs an AD entry that exposes it (follow-up).
6. **The combiner's feed**: the Bayesian logistic fit (`memory.fit_combiner`) exists and is tested; joining the traces'
   frozen sensors to resolved cold outcomes (RO2's resolver) is not wired, so the combiner is its labelled prior.
7. **The effect correction's forecast**: `f(a)` uses the 7-day forecast; the 1- and 30-day ones are in the trace.
8. **The probe's branch choice** ~~uses one rollout on the updated belief per draw instead of a nested `Q̄`~~
   (superseded by the Codex re-review's F2): one choice per probe result, on each branch's `Q̄` averaged over the
   belief's own world (all its draws from that result's posterior), two extra rollout batches per result.
9. **Reading's dose**: one dose per LO the section's provenance maps (`section_map.learning_objects_for_section`); a
   section with no mapped LO is valued at its cost alone and the trace says which.
10. **`C⁰`**: the tail's cost at `m̄` (the spec's first-week rule) at every decision; the preceding-window mean is a
    follow-up once RO5's scores need it (none forms before).
11. **The change class** needed a table rebuild (SQLite cannot widen a CHECK): `goal_contract_versions` is rebuilt in
    migration 246, rows and ids preserved, FK-safe as 235's precedent.
12. **"Asked once at goal creation"**: the copy at creation and `set_goal_use_weight` exist; the desktop's goal form
    does not ask the weight yet. Smallest finish: a number field in the goal creation form calling
    `set_goal_use_weight` after `create_goal`.
13. **The overview §9.2** (`docs/brainstorming/LearnLoop After the Queue (overview).md`) is untracked in the main
    checkout and absent from this branch, so it is not amended here; its finite-plan wording should read "the plan's
    minutes are a suggestion" at the landing.
14. **The frontier display** is labelled "predicted gain" in use-equivalents, not a percentage: a per-goal percentage
    needs a per-length recorder of the dated uses (follow-up).

## Not built (RO5 / RO6, by the spec) and what says so

The stop coin, randomized cold checks, the return model and calibration are RO5: until then no score forms (every
closed window is censored `no_valued_use_with_r_positive`), `w` stays at 0.8, and `κ` is the daily seed; every trace
says both (`mixing.weight_note`, `versions.kappa.note`).

## The first-day report (§8.10), on a synthetic vault

`tests/test_ro4_trace_report.py::test_the_first_day_report_against_the_predecessor_on_a_synthetic_vault`: the router
tests' wide vault (7 topics, 25 suggested minutes, no outcomes, no model set up, so the LLM policy's share is staged's),
one day served at mvp-0.46 and at mvp-0.47:

| | Predecessor (mvp-0.46) | Objective (mvp-0.47) |
|---|---|---|
| Blocks served | 5-6 (runs differ by their seeds) | 4 |
| Planned minutes | 22.8-23.2 of 25 | 23.9 of 25 |
| Stop in the support at every boundary | only under 5 minutes left | 1.0 (every boundary) |
| Stop chosen | at the end (minutes used) | 0.2 of decisions (1 of 5: the last) |
| Longest session | (not recorded) | 18 active minutes |
| Policy share of the draws | staged and the floor | staged 0.8-1.0, the floor's uniform the rest (numeric 0.2 of the weight) |
| `κ0` | (none) | the day's seed from `G` (0.0008 per minute in the profiling run; the tail's average, 0.0017, in this run, where the 64-draw marginal at `m̄` came out non-positive) |

On a copy of a real vault with an LLM set up, the shares move to about 0.8 LLM and 0.2 numeric before the floor, and
the report adds the LLM policy's timeout rate. Not run here: no paid call was made and no owner vault was opened.

## The gate (this step)

Recorded below; the full suite, the whole durability lane and the whole vitest run are the landing gate's.

| Step | What ran | Result |
|---|---|---|
| Setup | `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| Import contracts | `uv run lint-imports --no-cache` | 43 kept, 0 broken |
| Version pins | `tests/test_ro4_successor.py` and the 39 files pinning mvp-0.46 (every upgrade and successor test) | 749 passed, 21 failed (chain slices, sets, openers, snapshots); fixed, the 21 rerun with RO4's: passed |
| Head fixture and migrations | the 66 files naming the head, every migration test, table roles, tracked fixtures, public-tip guards | 810 passed, 3 skipped (246 traces only); after 246 gained the contract rebuild, batch B below |
| Batch A: every test touching the plan, the router chooser, card, requests, why, goal contracts, the history card, the sidecar goals, the view, the lanes, the policy (199 files) and RO4's serving and migration tests | `pytest -n 6` in the 5G scope | 9723 passed, 9 failed, 22 skipped; fixed (RO4 reads RO0's row 7 by its spec, so the RO0 gate and the Decider-steered data-capture arms run with the objective off at the tag; RO1's occurrence-time allowlist names the price's session minutes; the reading step may be the first chosen block; the data capture snapshot pin; a chain slice); the 7 files rerun with RO4's and the contract tests: 801 passed, then 2 fixed (CLI help snapshot, the null test's bound) |
| Batch B: every test touching router_objective, table roles, the router CLI, goal lifecycle and contracts, and the migration diffs (79 files) | `pytest -n 6` | 6470 passed, 21 failed (the earlier migrations' diffs on the rebuilt contract table); fixed by the altered-tables fold; the 16 files rerun: 85 passed |
| Durable SQLite | `--durable-sqlite` on `test_ro4_traces_migration`, `test_ro4_goals`, `test_ro4_objective_serving`, `test_ro4_trace_report`, `test_ro4_successor`; `-m durability` on the RO migrations | 47 passed; 1 passed |
| Final targeted set | every `tests/test_ro4_*.py`, `test_router_why_copy`, `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`, `test_sidecar_registry`, `test_mobile_allowlist`, `test_architecture`, `test_table_roles`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_registry_audit`, `test_cli_help_snapshot`, `test_codex_tool_lockdown`, `test_e0_isolation`, `test_module_catalog_inventory`, `test_public_tip_guards`, `test_sqlite_file_copies`, `test_ro0_gate`, `test_data_capture_successor`, `test_ro1_availability_reads`, on the committed tree at `c543abd3b4` | 746 passed, 1 skipped |
| Frontend | `npm install`, `npm run typecheck`, `npx vitest run --maxWorkers=4` on `src/app/todayPlan.test.ts`, `src/screens/today/DailyPlanView.test.tsx`, `src/screens/TodayScreen.plan.test.tsx`, `src/app/App.today.test.tsx` (61 passed) and `src/copy/denyList.test.tsx`, `src/copy/denyList.phase4.test.tsx` (57 passed); `npm run frontend:build` | ok |
| Rust | `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` (two passthroughs) | ok |
| References | `db_generate_reference.py`, `db_validate_reference.py` (head 246, 1159 leaves: errors []), `module_generate.py` / `module_validate.py` (PASS), `desktop_generate.py` / `desktop_validate.py` (passed) | ok |

Every test ran inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, at most `-n 6`, one run at a
time. Every script outside pytest ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. No paid
or real model call was made; no owner vault was opened; no tracked working vault was touched.

## Files RO4 added or changed tests in (for the landing gate)

`tests/test_ro4_successor.py`, `test_ro4_value.py`, `test_ro4_traces_migration.py`, `test_ro4_goals.py`,
`test_ro4_objective_serving.py`, `test_ro4_weight.py`, `test_ro4_price.py`, `test_ro4_trace_report.py`; pins moved in
the upgrade and successor tests, the migration tests (head 246, `RO4_ADDED_OBJECTS`, the altered-tables fold),
`test_ro0_gate.py`, `test_data_capture_a2_measurement.py`, `test_ro1_availability_reads.py`,
`test_ux_phase1_round2_rereview.py`, `test_data_capture_successor.py`, `test_curriculum_c1_landing.py`; vitest
`todayPlan.test.ts`, `DailyPlanView.test.tsx`.

## Landing onto main

Main was `d963f80952` (RO2 landed with its second pass, and FG1d). This branch carries everything RO4 merges.
These steps ran on top of the stage tip `59a0de9832`, in this order:

| Commit | What |
|---|---|
| `ec988ae03e` | R2: the goal form's use-weight field, with its tests |
| `4fbcb07385` | R5: the report counts how often the day's `κ0` seed fell back |
| `944c7ff320` | Merge of main |
| `6b1db34514` | After RO2's R6: the rollouts' reading action maps sections through AD's IR-taking path |
| `6a552b9a17` | `migration_head_246` rebuilt from main's `migration_head_245` |
| `0fe468420b` | The architecture reference regenerated |
| `ad57b3761a` | The gate's one failure, a stale opener pin, fixed (test only) |
| (this commit) | This record |

The full gate ran at `0fe468420b`. After it, only that pin fix and this section were committed; the smoke ran the
branch's code at `0fe468420b`, which `ad57b3761a` does not change.

### Orchestrator rulings (verbatim)

- R1: "Migration 246's rebuild of goal_contract_versions stands; it follows migration 235. The smoke shows on the owner's copies that every existing contract row, content hash and support hash is byte-identical after the upgrade, and that foreign keys check clean."
- R2: "The goal form asks for the use weight as the spec says, in the frictionless way: one optional field on the desktop goal form, prefilled with the default, that can be left alone. Built at landing, with its vitest; the phone's files stay untouched."
- R3: "Rollouts on AD's prior means for the learning increment and the reading curve, and the Bayesian sensor combination not yet fed resolved outcomes, are accepted for landing. Both go first in the follow-up batch, ahead of RO5, because RO5's checks evaluate this model. The report says the rollouts use priors."
- R4: "RO4 reading RO0's session receipts is what §8.1 asks; the RO0 gate test running with the objective off at mvp-0.47 is accepted."
- R5: "κ0's fallback to the tail's average marginal gain is accepted until RO5. The objective report counts how often the day's seed fell back, so the owner can see it."
- R6: "No real router_llm request is sent at landing. The smoke answers π_L with an in-process fake, including a slow fake past Next's wait and a failing one, so the fallback shares and published_uncorrected are measured; the real timeout rate comes from `learnloop router objective-report` after the owner upgrades. The orchestrator tells the owner the calls and real card sizes before landing."
- R7: "The overview's §9.2 is the orchestrator's untracked file; the orchestrator amends it. The memory model's own forecast curve (§8.9) and the whole-day-boundary return-gap reading go to the follow-up batch as recorded."

### Step 0: R2 and R5

- **R2, the goal form** (`ec988ae03e`). The wizard's date step has one optional field, "how much this date counts".
  - It is prefilled with the default, which `goal_feasibility` now returns as `use_weight_default`. The field is
    hidden below the tag, with the objective off, and for an open-ended goal.
  - Left alone, it sends nothing, and `create_goal` copies the default as before. Set, it sends
    `dated_use_weight`, which `create_goal` copies along with the config's undated density. Below the tag the value
    is ignored; below 0 it is refused.
  - Built test-first: 3 RPC tests in `tests/test_ro4_goals.py` and 3 vitest cases in
    `src/components/GoalWizard.test.tsx` failed before the change. No phone file was touched.
- **R5, the fallback count** (`4fbcb07385`). The report's `serving.kappa_seed` counts days by how that day's seed
  was formed: `day_seed`, `floored_at_last_positive`, `tail_average` or `carried_last`. The printed report says
  "fell back on N of D days (to the tail's average on K of D days)". Its test failed before the change.

### Step 1: the merge, the head fixture, and the conflicts

- **Merge** (`944c7ff320`). Every source file merged without conflict. The only conflicts were in the generated
  reference (Configuration, Database tables, Module catalog). I kept the branch's copies and regenerated them later.
  - `history_card.py`: RO4's decision-level sections (`decision_sections`, `decision_sections_entry`) call
    `build_sections`, so they now use RO2's fail-closed inquiry ancestry (F9).
  - The parameter registry, every defaults snapshot and config fingerprint (mvp-0.47's included), `table_roles.py`,
    the AD guard registrations and the CLI help snapshot needed no change. No config field moved, and RO2's second
    pass added none.
- **After RO2's ruling R6** (`6b1db34514`). The rollouts mapped a reading candidate's section to its LOs through the
  raw-loading `section_map.learning_objects_for_section`. Now:
  - With AD on, `objective_inputs._reading_los` asks a new read-only AD entry,
    `adaptive_difficulty.reading.section_learning_objects`. It reads `VaultReadingMap.los_for_section`:
    `MaterialView.document_ir`, after the sweep's withheld rule. A reading's doses therefore land on the LOs that
    AD's reading curve counts, and a withheld reading maps to nothing.
  - With AD off, `_reading_los_outside_ad` keeps the raw wrapper, as every caller outside AD does.
  - `tests/test_ro2_ad_raw_document_reads.py` now also walks from `daily_plan/objective_inputs.py`,
    `objective_chooser.py` and `adaptive_difficulty/readiness.py`. `OUTSIDE_AD` names the AD-off function and says
    why. A new run-time test on the textbook fake at mvp-0.47 sees every IR load inside the chokepoint.
  - Both tests failed on the pre-fix source: `section_map.py:252 learning_objects_for_section calls
    .load_document_ir()`, and a raw load at run time.
  - The walk found no other RO4 path to a raw loader. That includes the decision card, `decision_state_fields` with
    reading doses, and the chooser.
- **The head fixture** (`6a552b9a17`). `fixtures/migration_head_246/state.sqlite` was rebuilt from main's tracked,
  sanitized `migration_head_245`, with only `[246]` applied. The checks: checkpoint (0, 0, 0), rollback mode (header
  1/1), `integrity_check` ok, `foreign_key_check` empty, and no companion files. The fixture has no contract rows
  (0 before and 0 after), and the table's columns are identical. Its schema and every table's row count match the
  branch's earlier build. The README notes the rebuild. `SCHEMA_HEAD` (246), the 5 hard-coded paths, the tests' pins
  and the added-object lists already named 246.

### Step 2: early runs

All of these ran in one 5G scope at `-n 6` and passed: 394 tests.

- `lint-imports --no-cache`: 43 kept, frozen cycles kept.
- `tests/test_measurement_state_labels.py`, `tests/test_cli_help_snapshot.py`,
  `tests/test_codex_lockdown_round3.py` (the process-launch allowlist) and `tests/test_ro1_availability_reads.py`.
- Every `tests/test_ro0_*`, `test_ro2_*` and `test_ro4_*`, and both `tests/test_followup_fg1d_*` (FG1d came with the
  merge).

RO1's structural guard covers RO4's reads:

- The price's session minutes are allowlisted (`price.session_active_minutes`, occurrence time, with its reason).
- RO4's other `practice_attempts` reads have no time cutoff. The duration spread and the decision-state reads run
  at serving time, which is where they are meant to run.

### Step 3: references

All passed: `db_generate_reference.py` (head 246, 393 table notes), `db_validate_reference.py` (errors []),
`desktop_generate`/`desktop_validate` (319/319 TS/TSX, 6/6 Rust), `module_generate`/`module_validate` (1223
modules, 1375 test files, 40221/40221 links: PASS) and `validate_vault.py` (2210 notes). The defaults snapshots and
config fingerprints needed no change.

### Step 4: the gate, at `0fe468420b`

| Lane | Result |
|---|---|
| Setup | `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0`: ok |
| Import contracts | 43 kept, 0 broken |
| Full suite (`-n 8`, 10G scope, the lock held) | 26468 passed, 90 skipped, 47 xfailed, **1 failed**: `test_followup_successor.py::test_the_openers_install_this_links_completion`. It is a stale pin: it still names RO1's `learnloop.interval_factor_upgrade`, but RO4's openers install `learnloop.router_objective_upgrade`, the chain's latest link. It is deterministic, not flaky. Fixed test-only in `ad57b3761a`, and the file now passes (7). |
| Durability (`-m durability`) | 402 passed, 1 skipped |
| Owner lane (fresh backup-API copies of `owner-copies-mvp035` in `fixtures-local/landing-ro4/`, since deleted) | 83 passed, 4 skipped. The same 2 known failures as at RO2's landing and FG1d's: `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and `test_placement_fixture_copies[arxiv_v2]` |
| Desktop | typecheck ok; whole vitest at `--maxWorkers=4`: 271 files, 2756 passed; `frontend:build` ok |
| Rust | `cargo check`: ok |
| Mobile | typecheck ok, build ok (no phone file changed) |

No other test failed, so nothing else was rerun.

### Step 5: smoke

**Setup**

- **Copies.** Fresh backup-API copies of `~/learnloop-backups/mvp043-20261103-copy/{arxiv_v2,linear_algebra,probability}`
  in `fixtures-local/landing-ro4-smoke/`. On each copy every AI route points at `127.0.0.1:9`, and embeddings are
  off. Each copy was upgraded on main code to mvp-0.45, then to mvp-0.46, then rebuilt with
  `rebuild-derived-state` (head 245), as RO1's record says.
- **Code.** `git archive d963f80952` (main) and `git archive` of the branch's code tip, both with `migrations/`. A
  `sitecustomize` watch logs every socket connect and every subprocess, and refuses any non-loopback connect.
- **Driver.** RO2's landing driver, adapted. One day goes through the real sidecar handlers: Today, the plan, and
  Next with serve. Every answer goes through `submit_attempt`, with the tests' grader and diagnoser fake, and the
  diagnosis is drained. The driver never inserts a raw attempt, so the shadow can be compared.
  - Correct answers carry the item's expected answer. The first served item is answered wrong, so FG1's follow-up
    workflow opens and its job runs in-process.
  - After each answer, the prefetch runs (Next without serve) while feedback shows.
  - The first offered stop is declined with "keep going"; the next one is accepted with `end_session`.
  - The clock is frozen, and ids come from per-module streams.
- **The router's models are in-process fakes** (`tests/router_model_fakes`). There is a Decider, and a router LLM
  that answers each request's own schema: v1/v2 on main, `router_llm_choice_v3`, and FG1's gate's (see below).
  - Variants at the tag: `ok`; `slow`, which sleeps 12 s, past `router.timeout_seconds` = 8 s; and `fail`, which
    raises.
  - The identity runs pin the mixture's seed to the decision id on both sides, because the boundary key hashes the
    version string.

**R1, the contract table across 246**

- None of the three copies has a contract row (0 → 0).
- To give the check rows to compare, one contract per goal was confirmed with main's code on a mvp-0.46 copy, from
  the goal's own body and one exemplar. Only linear_algebra has a goal, so that is 1 row there.
- That copy was then opened with branch code. Rows, rowids and both hashes are byte-identical (digest
  `a8bf688a5ad5fda5`), `foreign_key_check` is empty, and the CHECK now admits `use_weight_change`.
- The same holds on the plain copies (0 rows, fk clean).

**Below the tag, and at the tag with the objective off: identical to main**

| Copy | Main vs branch at mvp-0.46 (migration 246) | Main (mvp-0.46) vs branch at mvp-0.47 with `[router_objective] enabled = false` |
|---|---|---|
| arxiv_v2 | IDENTICAL; 0 trace rows | IDENTICAL; 0 trace rows |
| linear_algebra | IDENTICAL; 0 trace rows | IDENTICAL; 0 trace rows |
| probability | IDENTICAL; 0 trace rows | IDENTICAL; 0 trace rows |

Ids and wall-clock times are set aside. Each comparison covers:

- Today, the plan, and every Next step;
- the submit, its feedback, the follow-up workflow and its job;
- the stop offers and their responses;
- every row written in every table (the derived rows rebuilt identically);
- every router_llm prompt and every Decider state, compared as a multiset. The prefetch threads log them in
  completion order.

**At the tag, objective on: one day per copy**

| | arxiv_v2 | linear_algebra | probability |
|---|---|---|---|
| Served | 10 items in 8 blocks (miss on the first) | 33 items in 12 blocks, plus a reading | 5 items in 2 blocks |
| Stop offers | after block 1, declined with "keep going"; then accepted | after block 3, declined; then accepted | after item 1, declined; then accepted (drawn by the objective) |
| Decisions traced | 8 `plan_block` | 13 | 3 |
| Stop in the support | 8/8 | 13/13 | 3/3 |
| Stop drawn | 0 | 0 | 1 |
| Past the plan's minutes | up to 5.0 min | up to 67.7 min (session 42 min of 30 suggested) | 0 |
| Drawn component | llm 4, numeric 3, uniform floor 1 | llm 10, numeric 3 | llm 2, uniform 1 |
| Effective weights | llm 0.8, numeric 0.2, staged 0 | the same | the same |
| G3: μ recomputed from each trace's own values, against the logged μ and propensity | max error 4.4e-7 (the logged values' rounding) | 4.4e-7 | 6e-17 |
| `κ0` | 0.000221, `day_seed` | 0.000492, **`tail_average`** | 0.0, **`tail_average`** |
| Numeric policy per decision (min / median / max, ms) | 1232 / 1621 / 1980 | 404 / 673 / 1013 | 219 / 271 / 371 |

`learnloop router trace <first decision>` (words and `--json`, 7.2-15.6 KB) and `learnloop router objective-report`
(words and `--json`) exited 0 on every copy. On linear_algebra the report reads:

```
decisions 13 (plus 0 follow-up decisions); stop chosen 0.0; policy share {'llm': 0.7692, 'numeric': 0.2308}
- 2026-11-05: 13 decisions, stop 0.0, longest session 42.0 min of 30.0 suggested, kappa0 0.000492 (tail_average), shares {'llm': 0.7692, 'numeric': 0.2308}, guard crossings 0
kappa0 seed: fell back on 1 of 1 days (to the tail's average on 1 of 1 days); by how {'tail_average': 1}
recommendation value: evaluated 0, pending 13, closed scores 0, censored {...}; w None (until RO5's randomized checks no score forms and w stays at its prior)
```

The trace's own words for that decision were:

```
This was chosen by the language model's proposal, which had a 62% chance of picking it.
The estimate preferred: maintain: What Makes a Vector Space? (10 min).
- stop for today: +9.6804, effort 0.0002
- maintain: What Makes a Vector Space? (10 min) (chosen): +9.6293, effort 0.0111
```

Why the numeric policy did not prefer stop there, though stop's `Q̄` was the highest:

- With a fast LLM, a decision has 8 draws.
- The paired SE of the top two was 0.148, larger than every gap between options.
- `argmax_qbar_ties_within_paired_se_by_support_order` therefore breaks the tie by support order, and stop comes
  last.

So on real data `π_Q` mostly follows the staged order, and no policy chose stop on linear_algebra in 13 decisions.
This is the accepted R3/R5 regime (priors, and the tail-average seed), not a defect, but the owner should know it.

**The first-day report (§8.10), beside the predecessor's day.** It is the same journey, on main at mvp-0.46 with the
same fakes:

| Copy | | Blocks | Items | Estimated minutes served | Plan decisions | Stop chosen | Policy share |
|---|---|---|---|---|---|---|---|
| arxiv_v2 | predecessor | 6 | 8 | 28.0 | 8 (mixture 5, staged 3) | 2 | mixture: staged/LLM/Decider ⅓ each |
| | objective | 8 | 10 | 35.0 | 8 | 0 | llm 0.5, numeric 0.375, uniform 0.125 |
| linear_algebra | predecessor | 6 | 8 | 25.4 | 9 (mixture 7, staged 2) | 2 | as above |
| | objective | 12 | 33 | 94.3 | 13 | 0 | llm 0.77, numeric 0.23 |
| probability | predecessor | 3 | 4 | 27.9 | 8 (mixture 3, staged 5) | 3 | as above |
| | objective | 2 | 5 | 24.4 | 3 | 1 | llm 0.67, uniform 0.33 |

- Stop is in the support at every boundary under the objective (1.0), against only at the plan's end before.
- The LLM policy's timeout rate is 0.0 with the fast fake. Its real rate comes from `objective-report` after the
  upgrade (R6).
- The rollouts use AD's prior means (R3), and `κ0` fell back to the tail's average on 2 of the 3 copies (R5).

**π_L: the slow and failing fakes** (the first stop declined; up to 9 and 14 steps)

| Copy | Slow (12 s, past the 8 s wait) | Failing |
|---|---|---|
| arxiv_v2 | 6 decisions: LLM `timeout` 6/6, numeric `published_uncorrected` 6/6 at 64 draws; effective weights staged 0.8, numeric 0.2 (the numeric share kept); drawn staged 4, numeric 2 | 7 decisions: LLM `failed` 7/7, numeric `final`; staged 0.8, numeric 0.2; drawn staged 5, numeric 2 |
| linear_algebra | 4: timeout 4/4, published_uncorrected 4/4; staged 0.8, numeric 0.2 | 6: failed 6/6; staged 0.8, numeric 0.2 |
| probability | 5: timeout 5/5, published_uncorrected 5/5; staged 0.8, numeric 0.2 | 5: failed 5/5; staged 0.8, numeric 0.2 |

- G3 recomputes μ exactly on every slow and failing decision: max error 1.1e-16, with the failed set `llm` read from
  the trace.
- With the slow fake, Next at a block boundary waits 8.7-9.7 s and then serves. Main does the same with the same
  slow fake (8.5-8.6 s, R2b's own wait). No Next stranded and no step failed.
- The numeric policy reached 64 draws while the LLM was out: up to 4.3 s on arxiv_v2. It stays inside the 45 s
  prefetch budget, and it published before the wait.

**Protection on both cards** (`prot.py`)

Scanned: every router_llm prompt and every Decider state of the on, slow and failing journeys (and main's, for
reference). Against:

- every item's reference solution and rubric text;
- the stems, answers and hints of the items AD's material view withholds or covers (linear_algebra: 15 items; the
  others: 0);
- stems of items not attempted before the request;
- attempts cited from after the request's instant.

Results:

- 0 held-out or protected stems, answers or hints.
- 0 unattempted stems. Main's old chooser card had 2.
- 0 attempts cited after the decision.
- Every "reference solution" hit (linear_algebra and probability) sits in a learner-answer field (`answer`,
  `answer_excerpt`, or the Decider's `answer:`). Those are items the driver answered correctly by typing the
  expected answer, so they are the learner's own words, which the cards may carry by the owner's Nov 1 decision.
- One more hit sits in an attempted multiple-choice stem whose option A is its reference answer, 106 days before the
  decision. It is the same false positive as at RO2's landing.
- Exam material: no protected item appeared on any card.

**π_L's real decision cards** (R6: what the orchestrator tells the owner)

Every `router_llm_choice_v3` request of the on, slow and failing journeys was measured. Tokens are estimated at
UTF-8 bytes / 4. Each request reserves 16,384 output tokens and allows one retry at double on truncation. The answer
itself is a few hundred tokens.

| Copy | π_L card, bytes: min / median / max (n) | ≈ tokens | Main's old chooser card, same journey: bytes min / median / max (n) | ≈ tokens | Decider state at the tag vs main, bytes (median) |
|---|---|---|---|---|---|
| arxiv_v2 | 3,000 / 5,581 / 6,973 (20) | 750 / 1,395 / 1,743 | 3,438 / 3,527 / 4,369 (6) | 860 / 882 / 1,092 | 2,300 vs 2,124 |
| linear_algebra | 43,098 / 50,600 / 50,897 (23) | 10,774 / 12,650 / 12,724 | 1,686 / 14,000 / 20,371 (8) | 422 / 3,500 / 5,093 | 21,168 vs 12,730 |
| probability | 17,757 / 30,785 / 37,610 (12) | 4,439 / 7,696 / 9,402 | 6,894 / 8,177 / 8,430 (3) | 1,724 / 2,044 / 2,108 | 6,891 vs 6,874 |

linear_algebra's card is at its budget: `llm_card_token_budget` = 48,000 bytes, plus the options and about 2.9 KB of
instructions.

**Requests per decision.** Each traced decision sends 1 `router_llm` request and 1 Decider request, the
predecessor's count. FG1's follow-up gate adds 1 request of each kind per miss (see the open items: it still uses
the older schema).

**Requests per typical day of each copy's own history.** These copies have little plan history, so the count is
estimated from attempts per active day and each copy's items per decision in the smoke:

| Copy | Its own history | Items per decision (smoke) | Requests a typical day | Input tokens a typical day (π_L) | Busiest day |
|---|---|---|---|---|---|
| linear_algebra | 6 attempt days; median 8, max 25 attempts | 2.5 | ≈ 4 router_llm + 4 Decider (+1 per miss) | ≈ 51,000 | 25 attempts: ≈ 11 requests, ≈ 140,000 tokens |
| probability | 2 attempt days, 1-2 attempts; 3 plan decisions | 1.7 | ≈ 2 + 2 | ≈ 15,000 | ≈ 2 requests |
| arxiv_v2 | no attempt history | 1.25 | a 25-30 minute day as in the smoke: ≈ 8 + 8 | ≈ 11,000 | — |

On the ChatGPT plan route these requests are `estimated_only` ($0 against `router.max_daily_cost_usd`). On a metered
route, the router's daily guard ($5 by default) refuses before sending.

**Shadow, survival, isolation**

- **Shadow.** `rebuild --shadow` after the journeys gives 0/0/0 on main code and on the objective copies
  (facet, schedule, and mastery beyond the version stamp). The objective copies also show 15-25 mastery rows that
  differ only in their `algorithm_version` stamp (mvp-0.46 → mvp-0.47).
  - A copy just upgraded, before any journey, shows the same: 34 rows stamp-only on arxiv_v2.
  - After `rebuild-derived-state` it is 0/0/0. The upgrade activates without rebuilding, so rows nothing touched
    keep the old stamp. That is cosmetic, but the owner can clear it (below).
  - No FG1 rounding case appeared.
- **Trace survival.** RO4's trace rows survive a state sync, a full rebuild and a second sync, byte-identical:
  arxiv_v2 (8, `f92ff730fb4aff38`), linear_algebra (13, `36c752651d222d61`), probability (3, `e4f8777750a7857e`).
- **Model calls.** `model_call_receipts` gained only the fakes' rows (`fake_llm`, `fake_decider`, `fake`): 0 from a
  real model.
- **Network and processes.** The watch log holds only `git` and `powerprofilesctl` subprocesses: no connect at all,
  no non-loopback connect, no name resolution. No Codex process ran.

**Time.** Medians in ms. Each copy ran 3 interleaved rounds of four sides, each on a fresh copy, after the gate:

- main at mvp-0.46;
- the branch at the tag with the objective off;
- the branch with the objective on, Next called right after the prefetch returns;
- the same with 3 s of feedback reading first ("on, dwell").

Today was called 5 extra times per run. Another worktree's test run shared the machine, so the absolute numbers are
noisy; the interleaving keeps the sides comparable.

| Copy | Side | Today | Next at a block boundary (max) | Next within a block | Next after the miss | Submit | FG1 follow-up job | Numeric policy per decision (max) |
|---|---|---|---|---|---|---|---|---|
| arxiv_v2 | main | 156 | 645 (767) | 580 | 406 | 249 | 633 | |
| | off | 156 | 651 (958) | 491 | 415 | 254 | 720 | |
| | on | 159 | **1997** (2219) | 522 | 398 | 241 | 638 | 1396 (1562) |
| | on, dwell | 159 | 715 (1458) | 538 | 418 | 239 | 607 | 1246 (1527) |
| linear_algebra | main | 227 | 846 (1178) | 578 | 706 | 260 | 659 | |
| | off | 228 | 878 (1444) | 858 | 517 | 257 | 644 | |
| | on | 226 | **2473** (2908) | 748 | 670 | 252 | 641 | 765 (948) |
| | on, dwell | 222 | 1099 (2456) | 740 | 634 | 251 | 619 | 771 (934) |
| probability | main | 159 | 748 (843) | 528 | | 224 | 570 | |
| | off | 160 | 810 (1568) | 615 | | 225 | 631 | |
| | on | 159 | 977 (1096) | 601 | | 227 | 653 | 237 (345) |
| | on, dwell | 156 | 974 (1121) | 606 | | 229 | 630 | 270 (351) |

Sample sizes: Today 15 per cell; Next at a block boundary 6-24 per cell; submit 12-45.

- **Next at a block boundary** is where the objective costs time. The serve waits for the numeric policy's job,
  which the prefetch started.
  - Called at once, it is 2.0-2.5 s on arxiv_v2 and linear_algebra, against 0.65-0.85 s on main.
  - After 3 s of feedback reading it is 0.7-1.1 s, close to main's: the job mostly finishes while feedback shows.
  - The slowest boundary step was 2.9 s, well inside `router.timeout_seconds` (8 s).
- **Deadlines.** No deadline was missed, and no Next stranded. With a slow LLM, both main and the branch wait the
  full 8 s at a boundary, which is R2b's wait.
- **The numeric policy at real size** is 0.24 s (probability), 0.77 s (linear_algebra) and 1.25-1.4 s (arxiv_v2) per
  decision, at 8 draws with a fast LLM. RO4's synthetic vault took 0.22-0.31 s. arxiv_v2 is the slowest despite the
  least history. I did not look into why (open items).
- **Today, within-block Next, submit and the FG1 job** are unchanged within their spread on every side.
- **With the objective off** every column matches main within the spread.

No stop condition of the brief was met:

- Serving is identical to main below the tag and with the objective off.
- No contract hash changed.
- μ recomputes from every trace.
- No protected or post-decision material reached a card.
- No deadline was missed and Next never stranded.
- The shadow shows nothing beyond the upgrade's version stamps.
- No real model call was delivered.
- The one failure was a stale pin, fixed.

### What the owner runs after the fast-forward

For each vault (`~/learnloop-vaults/<name>`). The vaults were at mvp-0.43 (arxiv_v2 at migration 239) at the last
record, so take the earlier links first, as their records say:

```bash
learnloop upgrade --to mvp-0.45 --vault ~/learnloop-vaults/<name>   # if below mvp-0.45
learnloop rebuild-derived-state --vault ~/learnloop-vaults/<name>
learnloop upgrade --to mvp-0.46 --vault ~/learnloop-vaults/<name>   # RO1: migration 244 and the whole-vault rebuild
learnloop upgrade --to mvp-0.47 --vault ~/learnloop-vaults/<name>   # RO4: applies any pending migration (245, 246) on open, then the successor
learnloop rebuild-derived-state --vault ~/learnloop-vaults/<name>   # optional: clears the stamp-only shadow rows
```

Then rebuild the desktop app and restart the phone host. After a day of use, check:

```bash
learnloop router objective-report --vault ~/learnloop-vaults/<name>   # the real LLM timeout rate, shares, the kappa0 seed's fallbacks
learnloop router trace <decision id> --vault ~/learnloop-vaults/<name>
```

**To turn the objective off**, set this in the vault's `learnloop.toml`. It then serves mvp-0.46's mixture and frame
exactly, as the smoke shows on all three copies:

```toml
[router_objective]
enabled = false
```

The new goal-form field is optional; leaving it alone keeps the default weight.

### Open items (for the orchestrator)

1. **FG1's follow-up gate is not on the objective.**
   - At the tag, a generated probe's workflow decision (FG1's `FollowupGate`, a `plan_interrupt` with
     `insert_now` / `continue_current` / `no_intervention`) is still decided by R2b's `router_mixture_v1`.
   - It sends the older `RouterLLMAnswerV1` request (4.4-7.6 KB on these copies) and writes no RO4 trace. The smoke
     saw one such decision per copy.
   - Spec §8.3 says mid-block follow-ups use the same two-policy mix. RO4's `ObjectiveRestraintGate` covers only the
     predecessor's diagnosis follow-ups (`_restrained_followups`), and with FG1 on (the default) those are rare.
   - This is not a brief stop condition, so it is recorded for a ruling: build it in the follow-up batch, or accept
     it as FG1's lane.
2. **`learnloop router objective-report` does not pass the weight to the report.** The CLI never calls
   `current_weight`, so the report prints `w None` and an empty posterior, while every trace records `w = 0.8`. It
   is a small CLI fix with a test (follow-up, Low).
3. **The why surface's "how was this chosen?" shows the trace's `weight_note` verbatim**: "no randomized checks
   exist before RO5, so no score forms and w stays at its prior". "RO5" and "w" are internal words on a learner
   surface, and the plain-words test checks other words. A wording fix is needed (follow-up, Low).
4. **`π_Q` rarely picks stop on real data.**
   - With a fast LLM a decision has 8 draws. The paired SE (0.148 on linear_algebra) exceeds every gap, so ties go
     by support order, where stop is last.
   - With `κ0` at the tail's average (0.000492 on linear_algebra, 0.0 on probability), nothing chose stop on
     linear_algebra in 13 decisions, and the day ran 67.7 minutes past the plan.
   - This is the accepted R3/R5 regime. RO5's coin and calibration, and the follow-up batch's posterior learning
     parameters, are where it moves. The owner should expect long sessions until then, and can turn the objective
     off as above.
5. **The upgrade activates without a rebuild.** Untouched mastery rows keep the mvp-0.46 stamp until the next
   rebuild, which is cosmetic (`rebuild-derived-state` clears it).
6. **The numeric policy is 1.25-1.4 s per decision on arxiv_v2**, slower than on linear_algebra. Next at a boundary
   called right after feedback costs about 1.4-1.6 s more than main on arxiv_v2 and linear_algebra; with a few
   seconds of reading it is close to main. Worth profiling with RO5.
7. As ruled:
   - R3: the posterior learning parameters and the combiner's feed go first in the follow-up batch.
   - R7: the memory model's own forecast curve and the whole-day-boundary return gap go to the follow-up batch; the
     overview's §9.2 is the orchestrator's.
