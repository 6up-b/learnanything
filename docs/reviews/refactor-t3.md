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

**A fixed draw count.** The default also wraps `objective_chooser.run_numeric` so its `keep_going` is `None`: the evaluation runs one batch of `rollout_theta_draws` (8 by default) and does not refine while the LLM policy is out. Refinement is what made the count follow the wall clock (the prefetch job's `keep_going` reads the LLM's event and the clock); the no-model branch already passes `None`. The deadline stays: a first batch that cannot finish by `router.timeout_seconds` (180 s) is still a timeout, which the tests of timeouts set up with their own clocks and timeouts. A test of refinement or of the draw count takes the marker.

**The marker.** `@pytest.mark.real_draws` (declared in `pyproject.toml`): every wrapper calls production's function unchanged and `run_numeric` keeps its `keep_going`. For tests whose subject is the draw or the seed function (the lists in `refactor-dfd.md` and `refactor-d21.md`: seed variety, the seed functions' own tests, the identity pins of seed functions, refinement).

**Wider-scoped fixtures.** Under `-n 8 --dist worksteal` the test that first builds a module- or class-scoped fixture varies by run. A fixture of wider scope than a function is therefore keyed on its own definition (its base id and name, and its parameter), with its own count, while it is set up; the test's key and count resume after it (a `pytest_fixture_setup` wrapper). A session-scoped template built before any test (`basic_vault_template`) draws nothing.

**Choices the brief asked to be named.**

- *The stop coin.* It flips on the decision's own seed (`SC.flip(seed, ...)`), so it is pinned with the `objective_mix` family and is not forced: it still offers stops at the configured rate wherever the fixed seed lands. `QUIET` / `NO_CHECKS` (`stop_coin = 0`) stay the way to turn it off.
- *The check day.* Production's seed is already a pure function of the local date, so a suite with a frozen `DAY` was deterministic and a test on the real date moved with the calendar. Pinned, the first date a test checks on is `n = 0`, the next distinct date `n = 1`, and so on: a multi-day journey still gets a different draw each day, and no test depends on the calendar. The cost: a frozen-`DAY` suite now draws at `n = 0` instead of at production's seed for its `DAY`, so a test that passed only because its `DAY`'s seed placed no check where it looks can now meet one; step 3 finds those and pins `RANDOMIZED_CHECKS_OFF` where the check is not the subject.
- *Spawned processes.* The wrappers live in the test process; a child process (multiprocessing `spawn`, or a CLI subprocess) does not load conftest. `pinned_draws.pin_this_process()` installs the same default in a child from `PYTEST_CURRENT_TEST`, which the child inherits, keyed on the parent's node id plus a label so the child's counts are its own; `tests/test_mobile_two_process.py`'s host calls it. A child that does not call it draws as production does; no other test spawns a process that reaches the objective path (the census ran in-process; this is stated, not measured, for CLI subprocesses).
- *The sidecar's and the phone host's runtimes with no model* (in process). Their process runtime has `seed = None`, so their decisions take `mix.seed_for` and the numeric policy holds the whole mix on `numeric_seed`, both wrapped: their draws are fixed per test. The no-model branch calls `run_numeric` with no refinement already, so its draw count was fixed; what moved there was the seed. A test that needs no stop or offer keeps `never_stop_or_offer_draws`.
- *Background jobs whose timing decides an outcome* (D-26: the follow-up's generation job releasing a held answer before the learner asks). A fixed seed does not fix a race and the default does not try: it changes no timing. Such a test waits for the work it reads (joins the job through its owner, or reads after the job's completion event), or turns the job off when the job is not its subject, as `CLAUDE.md` "## Tests" already asks. What is left that the default does not pin: the published-early versus corrected numeric answer (which one a serve takes depends on when the LLM fake answers), and the seeds D-14 did not wrap (AD's selection and dose seeds, `delayed_checks`, `router_retrieval`).

**What it leaves to arc E.** The seams are production's module attributes; E2's `choose(ChoiceInputs)` and E3's seed module will let a test pass its seed and draw count as plain inputs, and this module then shrinks to what remains.
