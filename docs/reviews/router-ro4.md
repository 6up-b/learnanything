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
