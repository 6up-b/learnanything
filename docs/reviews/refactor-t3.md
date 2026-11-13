# T3: seeded draws pinned by default

Strategy §2.19 T3, on branch `refactor/t3-pinned-draws`, based on main `5f0d44269e` plus D-21's branch (`a1a5f220af`). Tests, test support and conftest only: no production change. The production cause (seeds derived from fresh ids, a draw count that follows a wall-clock deadline) is arc E's (E2, E3); this step makes the suite deterministic until then.

## Design (written before the code)

**What a test gets without asking.** `tests/pinned_draws.py`, installed by `tests/conftest.py` at import, wraps the five seed derivations D-14 and D-21 named, at the module attribute production looks up at call time:

| Family | Wrapped | Production derives it from |
|---|---|---|
| `objective_mix` | `router_objective.mix.seed_for` | boundary key and fresh decision id (the stop coin flips on the same seed) |
| `mixture` | `router.mixture.seed_for` (R2b's mix, through `RouterRuntime.seed_for`) | the same |
| `numeric` | `daily_plan.objective_chooser.numeric_seed` | the boundary identity, which holds the plan's fresh id and the latest attempt's |
| `pick` | `router_objective.picks.seed_for` | the factor's fresh id |
| `check` | `router_objective.checks.day_seed` | the local date |
| `lesson` | `router.lesson_suggestions.seed_for` | the day and a snapshot hash |

While a test without the `real_draws` marker runs, each wrapper calls production's function and returns, instead of its value, `sha256("pinned-draws|<key>|<family>|<n>")` cut to the same length, where `<key>` is the test's node id and `n` counts the distinct production seeds this family has returned so far in the test (the first distinct seed is 0). So:

- a test draws the same values on every run: the seeds no longer carry a fresh id, only the test's name and the order in which its distinct boundaries arrive;
- equal production seeds stay equal and different ones stay different within a test (the map is one-to-one), so every test that compares two seeds, or a logged seed against `seed_for(...)` of its row, still holds; a test that needs production's exact value (an identity pin of the seed function, a test of the seed function) takes the marker;
- nothing is forced: the pinned seeds are as uniform as production's, so ordinary tests still see stops, offers, checks and lesson offers wherever their fixed seed draws them. A test whose assertion needs one arm keeps or gains its own pin (`RANDOMIZED_CHECKS_OFF`, the ih2 `draw` fixture, `QUIET`, `block_drawing_seed()`, `never_stop_or_offer_draws`), which wins over the default because it replaces the function or the runtime seed the default wraps.

Why an order count rather than the call's inputs: every input here holds an id the run minted (plan, decision, attempt, item ids of items a test creates, the factor id), so no function of the inputs alone is the same on two runs. The order in which a test reaches its distinct boundaries is: tests drive the plan from one thread, and the derivations run on the serving thread (the decision seed and the coin in `_decide_objective`, the numeric seed in `choose` before the job starts).

**A fixed draw count.** The default also wraps `objective_chooser.run_numeric` so its `keep_going` is `None`: the evaluation runs one batch of `rollout_theta_draws` (8 by default) and does not refine while the LLM policy is out. Refinement is what made the count follow the wall clock (the prefetch job's `keep_going` reads the LLM's event and the clock); the no-model branch already passes `None`. The deadline stays: a first batch that cannot finish by `router.timeout_seconds` (40 s) is still a timeout, which the tests of timeouts set up with their own clocks and timeouts. A test of refinement or of the draw count takes the marker.

**The marker.** `@pytest.mark.real_draws` (declared in `pyproject.toml`): every wrapper calls production's function unchanged and `run_numeric` keeps its `keep_going`. For tests whose subject is the draw or the seed function (the lists in `refactor-dfd.md` and `refactor-d21.md`: seed variety, the seed functions' own tests, the identity pins of seed functions, refinement).

**Wider-scoped fixtures.** Under `-n 8 --dist worksteal` the test that first builds a module- or class-scoped fixture varies by run. A fixture of wider scope than a function is therefore keyed on its own definition (its base id and name, and its parameter), with its own count, while it is set up; the test's key and count resume after it (a `pytest_fixture_setup` wrapper). A session-scoped template built before any test (`basic_vault_template`) draws nothing.

**Choices the brief asked to be named.**

- *The stop coin.* It flips on the decision's own seed (`SC.flip(seed, ...)`), so it is pinned with the `objective_mix` family and is not forced: it still offers stops at the configured rate wherever the fixed seed lands. `QUIET` / `NO_CHECKS` (`stop_coin = 0`) stay the way to turn it off.
- *The check day.* Production's seed is already a pure function of the local date, so a suite with a frozen `DAY` was deterministic and a test on the real date moved with the calendar. Pinned, the first date a test checks on is `n = 0`, the next distinct date `n = 1`, and so on: a multi-day journey still gets a different draw each day, and no test depends on the calendar. The cost: a frozen-`DAY` suite now draws at `n = 0` instead of at production's seed for its `DAY`, so a test that passed only because its `DAY`'s seed placed no check where it looks can now meet one; step 3 finds those and pins `RANDOMIZED_CHECKS_OFF` where the check is not the subject. *(Changed by step 3; see below: the check keeps production's seed of a fixed date plus the test's offset.)*
- *Spawned processes.* The wrappers live in the test process; a child process (multiprocessing `spawn`, or a CLI subprocess) does not load conftest. `pinned_draws.pin_this_process(label)` installs the same default in a child, keyed on the parent's node id (conftest exports it as `LEARNLOOP_TEST_PINNED_DRAWS` while a pinned test runs, and a child inherits the environment; under `real_draws` it is unset and the child draws as production does) plus a label, so the child's counts are its own; `tests/test_mobile_two_process.py`'s host calls it. A child that does not call it draws as production does; no other test spawns a process that reaches the objective path (the census ran in-process; this is stated, not measured, for CLI subprocesses).
- *The sidecar's and the phone host's runtimes with no model* (in process). Their process runtime has `seed = None`, so their decisions take `mix.seed_for` and the numeric policy holds the whole mix on `numeric_seed`, both wrapped: their draws are fixed per test. The no-model branch calls `run_numeric` with no refinement already, so its draw count was fixed; what moved there was the seed. A test that needs no stop or offer keeps `never_stop_or_offer_draws`.
- *Background jobs whose timing decides an outcome* (D-26: the follow-up's generation job releasing a held answer before the learner asks). A fixed seed does not fix a race and the default does not try: it changes no timing. Such a test waits for the work it reads (joins the job through its owner, or reads after the job's completion event), or turns the job off when the job is not its subject, as `CLAUDE.md` "## Tests" already asks. What is left that the default does not pin: the published-early versus final numeric answer (a serve takes the uncorrected publication only when the job's numeric component timed out), the carried valuation's thread (which earlier decision's value a later trace carries; `router-speed2.md` saw it differ between runs of main), and the seeds D-14 did not wrap (AD's selection and dose seeds, `delayed_checks`, `router_retrieval`).

**What it leaves to arc E.** The seams are production's module attributes; E2's `choose(ChoiceInputs)` and E3's seed module will let a test pass its seed and draw count as plain inputs, and this module then shrinks to what remains.

## What was built

- `tests/pinned_draws.py` (new, test support): the six wrappers, `begin`/`end`, `push`/`pop` for wider-scoped fixtures, `pin_this_process`, and `production(module, name)` for a test or helper that needs production's own function behind a wrapper.
- `tests/conftest.py`: installs the wrappers at import (about 0.2 s more per process: it imports the objective chooser); `pytest_runtest_setup` (tryfirst) begins a test's pins unless it carries `real_draws`, `pytest_runtest_teardown` (trylast, after fixture finalizers) ends them, and a `pytest_fixture_setup` wrapper keys a module-, class-, package- or session-scoped fixture's draws on the fixture.
- `pyproject.toml`: the `real_draws` marker.
- `tests/test_pinned_draws.py` (new): the default's own tests (proof (a) below).

## What the default changed (step 3)

The first landing run with the default (the brief's command, `-n 8 --dist worksteal -m "not arc_close"`, under the lock in a 10 GB scope, with a scratch census plugin logging every seed call): **11 failed, 30,497 passed, 104 skipped, 12 xfailed** in 852 s. Every one of the 11 passed with the check family alone left to production (a scratch plugin restoring one family at a time), and every one draws its check on 2026-10-12:

`test_mobile_v2_plan::test_j1_the_phone_never_gets_a_held_item…`, `test_mobile_v2_landing_fixes::test_r2_keep_going_after_done…`, `::test_r3_a_refused_keep_going…`, `test_mobile_v2_rereview_fixes::test_f7_…` (three), `test_mobile_v3_codex_review::test_f3_a_v2_apps_plan_step_holds…`, `test_ih6_workbench_open_item::test_plan_prefetch_reports_the_workbench…`, `test_ih4_preferences_inform_router::test_with_no_preference…`, `test_sg_slip_vs_gap::test_sg1_…`, `test_rospeed2_connections::test_the_job_opens_a_handful_of_connections`.

The census (calls under the default, whole landing selection; D-21's was the builder's 249 files):

| Family | Files | Tests | Calls |
|---|---|---|---|
| `check` | 73 | 451 | 4,595 |
| `numeric` | 53 | 358 | 1,054 |
| `objective_mix` | 38 | 246 | 1,518 |
| `mixture` | 23 | 135 | 351 |
| `lesson` | 10 | 47 | 6,501 |
| `pick` | 1 | 3 | 4 |

These were not flaky: D-21 listed most of them as "deterministic at the frozen `DAY`; a different day places the check block these tests do not account for". So the ordinal check of the design moved them off the one date they were written against. Of the census's 595 check-seed calls on a date, 447 were on 2026-10-12, 135 on 15 other frozen dates (from 2026-01-01 to 2026-11-05), and 13 on the real date (13 tests in `test_library_exercises`, `test_mobile_phone_contract`, `test_mobile_v3_codex_review`, `test_ro0_rows7_8_sessions`: the tests that moved with the calendar); 4,000 more were non-dates from tests of the seed's spread. Rather than pin the check off in 11 tests and lose the check interplay they exercise, **the pinned check keeps production's seed of a date: the test's first date stands for 2026-10-12 (`CHECK_ANCHOR`), and each later date keeps its offset**. A suite frozen at that date draws exactly as before, a multi-day journey still draws a new day each day, a test on the real date stops moving with the calendar, and a suite frozen at another date now draws as if it were 2026-10-12 (none failed). A non-date input (`test_ro5_checks`' spread over `d0…d999`) takes the ordinal map.

With that, 10 of the 11 passed; `test_sg_slip_vs_gap::test_sg1_…` still failed. Its helper `ih4_preferences_inform_router_helpers._pin` seeds the twins alike by hashing an identity without the plan id, the version and the attempt, but it does that through `_hash`, under `numeric_seed`, so the default's map sat on top and put the twins on another numeric seed. There, at one fixed seed, sg1 failed 6 of 10 and 7 of 12 repeats (the production seed sequence was identical in passing and failing runs; one twin made a sixth decision): the divergence at that seed is timing, not the seed (ledger D-19, below). `_pin` now names production's `numeric_seed` itself (`pinned_draws.production(...)`), so the twins keep the seed they were written at: 20 of 20 repeats of sg1 and the ih4 twin test passed. The design's claim that a test's own pin wins held for pins that replace a wrapped function or the runtime seed; `_pin` did neither, and is the one helper changed for that reason.

**Tests touched and why**

| Test or helper | Change | Why |
|---|---|---|
| `test_identity_pins::test_identity_pin` | `real_draws` | C3 pins the numeric seed and C6 the lesson seed: production's exact values |
| `test_rospeed2_connections::test_r2_the_numeric_seed_is_mains…` | `real_draws` | its subject is production's numeric seed (D-14/D-21: by construction) |
| `test_rospeed2_connections::test_the_pool_completes_more_draws_by_one_deadline…` | `real_draws` | its subject is how many draws refinement completes by a deadline |
| `ih4_preferences_inform_router_helpers._pin` (IH4 twins, sg1, sg2) | names production's `numeric_seed` | above |
| `test_mobile_two_process` host | `pin_this_process("host")` | the spawned host pins its own draws |

No assertion changed. No per-test pin was removed: proof (b) below found that the D-21 pins in four of the five tests do the same job as the default, but each is a one-line fixture or call naming the arm its test assumes, and keeping it costs nothing; the fifth still needs its pin. Tests that `real_draws` would fit but that pass under the default were left unmarked (`test_ih_numeric_seed`, `test_plan_determinism_landing`, `test_ih5_successor`, `test_ro5_picks`, `test_ro5_checks`, the `te1b` spread tests): they compare seeds with seeds, which the one-to-one map keeps.

## Proof

**(a) The default itself** (`tests/test_pinned_draws.py`). The objective path at the head with no model set up (the sidecar's runtime, where the numeric policy holds the whole mix: D-21's case), four served steps answered "I don't know" on a fresh `create_daily_plan_vault`:

- `test_the_same_scenario_built_twice_draws_the_same_choices` (`slow`, about 20 s): built twice in one test on two fresh vaults, with `begin(node id)` between them (what the next run of the test starts from), every plan-block decision's policy, item and learning object and every seed are equal, and each decision still has its own seed.
- `test_with_the_marker_seeds_are_productions_and_vary` (`real_draws`): the same journey twice shares no seed, and in the run that wrote it the two journeys made 3 and 2 decisions (the draw varying, as production's does).
- `test_the_map_keeps_productions_equalities_and_differences`, `test_the_check_day_keeps_the_offset_from_the_tests_first_date_and_loses_the_calendar`, `test_the_numeric_policy_runs_one_batch`: the map is one-to-one and counts per family; the check keeps offsets from the anchor; `run_numeric` gets `keep_going=None`.

**(b) The sweeps' hand pins removed** (D-21's five; a temporary edit of the worktree, reverted with `git checkout`, each test repeated 5 times at `-n 5` with a scratch plugin that keys every repeat on the test's real node id, so each repeat draws as one run of the test does):

| Test | Pin removed | Result | Means |
|---|---|---|---|
| `test_daily_plan_rpc::test_next_plan_item_serves…` | `vault` fixture's `never_stop_or_offer_draws` and `QUIET` | 5/5 pass | the default does the job |
| `test_daily_plan_rpc::test_skipping_moves_on…` | same fixture | 5/5 pass | the default does the job |
| `test_mobile_two_process::test_the_phone_and_the_desktop_take_turns…` | `never_stop_or_offer_draws` in the test and the host (the host keeps `pin_this_process`) | 5/5 pass | the default does the job, in both processes |
| `test_mobile_v2_feedback::test_j2_…` (D-26) | the `answered` fixtures' `draw.never_stop` and `draw.avoid` | 5/5 pass | the default does the job for the draw; the follow-up job's race (D-26's second cause) is answered by the test no longer asserting the release reply, not by a seed |
| `test_mobile_v2_plan::test_a_none_origin_never_enters_the_device_branch` | `plan_toml=STAGED_ROUTER` | **2 of 5 fail** (`pi_a1` not among the first eight steps) | still needs its pin: at one fixed seed and a fixed draw count the objective's block order varies run to run, so the variation is not the seed and not refinement (the no-model branch never refines); see D-28 |

The pins stay (above). D-14's three and D-15 were not rerun without their pins.

**(c) The landing selection three times running** (the brief's command under the lock, `-n 8 --dist worksteal -m "not arc_close"`, 10 GB scope; runs 1-2 on `3a3383a9d4`, run 3 on `061ff2ea7e`, which changes only documents):

- run 1: 30509 passed, 104 skipped, 12 xfailed, 70 warnings in 825.28s (0:13:45)
- run 2: 30509 passed, 104 skipped, 12 xfailed, 70 warnings in 838.97s (0:13:58)
- run 3: 30509 passed, 104 skipped, 12 xfailed, 70 warnings in 844.56s (0:14:04)

**(d) The arc-close lane once** (`-m arc_close -n 8 --dist worksteal`, same scope, with the census plugin): 24 passed, 36 xfailed, 2 warnings in 500.10s. The default applies there as everywhere (conftest does not look at the lane). Three arc-close tests reach a seed source, all three on `numeric`, `objective_mix` and `check`: `test_ro5_calibration::test_the_first_week_on_a_copy_shaped_synthetic_vault`, `test_ro6_tail_data::test_a_few_weeks_on_a_copy_shaped_synthetic_vault` and `test_rofu_weeks::test_two_weeks_after_the_batch` (164 decisions between them). They pass under the default and pass with every test's draws left to production (a scratch plugin marking every test `real_draws`: 3 passed). No other arc-close test (the AD sims, the EVSI multisim, the xfailed pre-registered sims) reaches a wrapped source, so the default changes nothing in them; the AD sims draw on their own seeds, which this step does not wrap.

## Ledger

- **D-19** (open, not closed): the twins hold at their own seed and `_pin` now keeps them there under the default. At the seed the default would have given them, sg1's twin made a sixth decision in 6 of 10 runs with the same seeds: the divergence D-19 records is, at least at that seed, not a function of the seed. Row updated with this.
- **D-28** (new, open, due at arc D's close): block order under the objective varies with every wrapped seed fixed and one batch of draws; the source is not isolated (what is ruled out is in the row). `test_a_none_origin` keeps its staged frame and the IH4 twins their own seed until then.

## Gates

(Filled in at hand-back.)

## What was not verified

- That no spawned CLI subprocess reaches the objective path: the census ran in-process.
- D-14's three hand-pinned tests and D-15's were not rerun without their pins.
- The pinned check's anchor makes suites frozen at other dates draw as if on 2026-10-12; none failed, but their check placement is not the one their date gave before.
- Wider-scoped fixtures that draw: the census logged no draw during a module- or class-scoped fixture's setup that I could tell from a test's own draws (the census keys on the test), so the fixture branch is exercised only by its own logic, not by a test that needed it.
- A test marked `real_draws` that shares a module-scoped fixture with pinned tests gets that fixture in whichever mode its first consumer built it.
