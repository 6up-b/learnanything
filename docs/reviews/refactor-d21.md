# D-21: the seeded draws under `create_daily_plan_vault` at the head

Ledger row D-21 (`docs/reviews/refactor-bug-ledger.md`), on branch `refactor/d21-plan-vault-draws`, based on main `832fcb9abc`. Tests and test helpers only: no production change. Method and tools as in `refactor-dfd.md` (D-14, D-15): scratch plugins (not tracked) that wrap each production seed derivation, log which tests reach it, force it to an extreme, or repeat a test N times.

## File list

249 test files reach the builder `create_daily_plan_vault` or the `plan_world` fixture: 68 name them directly (`grep -l`), and 181 more import, at any depth, a `tests/*_helpers.py` / `*_fakes.py` module that calls the builder (53 such helper modules, followed through imports; `tests/helpers.py` itself, which defines the builder, was not followed, or every file would count). Under `-m "not arc_close"` they ran 4,553 tests in three chunks of about 90 files at `-n 4` behind the lock: 0 failures (the census doubles as the clean baseline).

## Census (which tests reach each seed source)

| Source (the wrapped derivation) | Files | Tests |
|---|---|---|
| decision (`router.mixture.seed_for`, `router_objective.mix.seed_for`; the stop coin shares it) | 55 | 313 |
| numeric (`objective_chooser.numeric_seed`) | 51 | 353 |
| check (`router_objective.checks.day_seed`) | 65 | 413 |
| lesson (`router.lesson_suggestions.seed_for`) | 2 | 4 |
| pick (`router_objective.picks.seed_for`) | 0 | 0 |

## Forcing

Each source forced over the files that reach it: decision to stop offered, `present_next`, the floor's last and first option, the last component; numeric to three other seeds; check to three other days; lesson low and high; pick not run (no test reaches it). Every failure read:

| Forced | Failing tests | Verdict |
|---|---|---|
| stop offered | `test_daily_plan_rpc::test_next_plan_item_serves…` (the row's test), `test_mobile_v2_feedback::test_j2_the_full_answers_display…` (D-26, found by a one-file forcing) | **draw, fixed** |
| floor last | the two above, `test_daily_plan_rpc::test_skipping_moves_on…`, `test_mobile_two_process::test_the_phone_and_the_desktop_take_turns…`, `test_mobile_v2_plan::test_a_none_origin…` | **draw, fixed** |
| stop offered, `present_next`, floor first/last, last component | `test_plan_determinism_landing` (the mixture draws per session), `test_ih5_successor` replay | by construction: they assert seed variety |
| numeric a/b/c | `test_ih_numeric_seed`, `test_rospeed2_connections::test_r2…` | by construction: tests of the seed function |
| numeric a/b/c, check a | `test_ih4_preferences_inform_router` (4 twins), `test_sg_slip_vs_gap` sg2 | D-19, unchanged (twins diverge at other seeds); left alone |
| check b/c | 20 tests in `test_ih3_phone_host`, `test_ih6_workbench_open_item`, `test_mobile_v2_landing_fixes`, `_plan` (j1, j5), `_rereview_fixes`, `_review_fixes`, `test_mobile_v3_codex_review`, `test_mobile_v3_probes`, plus `test_ro6_tail_data` (check c) | deterministic: the check day is the frozen `DAY`, so the one day passes; a different day places the check block these tests do not account for. Not flaky; they would move if their date moved. Left alone, listed |
| check a/b/c | `test_ro5_checks::test_the_draw_is_uniform_over_topics_across_dates` | by construction |
| lesson low/high | none | |

## Repetition

The 249 files unforced at `-n 4` behind the lock: **2 complete runs and a third that finished its chunks as the sweep was stopped** (the machine's lock was held by other gates for long stretches, and the cap on machine time came first; 10 runs were not done). One failure in those runs: `test_mobile_v2_plan::test_a_none_origin…` once, already in the forced list. So repetition found nothing that forcing had not, in the runs it got. It is a weaker net than the 10 runs asked for.

## Tests fixed

Failures over 100 unforced repeats (`-n 4`), before on a copy of the base tests (`git archive`), after on the worktree:

| Test | Before | After | Means |
|---|---|---|---|
| `test_daily_plan_rpc::test_next_plan_item_serves_with_the_offer_that_ranked_it_and_advances` | 12 (8 on an earlier 100) | 0 | the `vault` fixture takes `never_stop_or_offer_draws` and `QUIET` (`stop_coin = 0`) |
| `test_daily_plan_rpc::test_skipping_moves_on_and_counts_the_estimate` | 5 | 0 | same fixture |
| `test_mobile_v2_plan::test_a_none_origin_never_enters_the_device_branch` | 16 | 0 | the staged frame (`STAGED_ROUTER`, as `plan_world` has it) |
| `test_mobile_two_process::test_the_phone_and_the_desktop_take_turns_on_one_plan` | 4 | 0 | `never_stop_or_offer_draws` in the test and in the spawned host process |
| `test_mobile_v2_feedback::test_j2_the_full_answers_display_is_recorded_once_per_display_id` (ledger D-26) | 4 | 0 | the `answered` fixtures take the ih2 `draw` (`never_stop`, no lesson offer), and the test no longer asserts `released is True` |

After the fixes the four files (31 tests) pass under stop offered and under floor last (the none-origin test runs on the staged frame, which the objective's draws do not reach).

**Why the residual failures after the first pin.** A block-drawing runtime seed did not hold: the sidecar's and the host's process runtime has no model, so the numeric policy holds the whole mix and its draw, on a fresh plan id, lands on a stop or an offer. The helper therefore wraps `mix.draw` (a drawn stop or offer goes to the next option with its own propensity, as the ih2 `draw` fixture does), and for the rpc test the stop coin is set to 0 as well: the day then closed after one answer (`day.complete`) through the coin, which the wrap on `mix.draw` does not reach. `test_a_none_origin` was not a stop: the held item was not among its first eight steps because the objective's block order varies run to run (the rollouts' deadline, as `refactor-d2b2.md` says). The draw pins (stop, offer, a fixed numeric seed, stop coin 0) left it at 3 in 100; the staged frame gives a definite order, 0 in 100.

**D-26 (`test_j2_the_full_answers_display…`).** Two causes. The mix draw (forcing: stop offered and floor last fail it; `draw` fixes those). And a residual 2 to 5 in 100 after that pin: the follow-up's generation job runs beside the test with no model behind it, and when it ends first it has already released the held answer, so `followup_show_anyway` says `released: false`. This second cause is inferred from the job's code and the warnings in the failing runs, not isolated by forcing. The test's subject is recording a display once per display id; the assertion on the release reply was incidental, and the recording that follows fails while the answer is still held, so no behaviour check was loosened.

## Shared helper

`tests/router_model_fakes.py::never_stop_or_offer_draws(monkeypatch=None, *, fixed_numeric_seed=False)`: a plain function (a spawned host process has no fixtures). Used by the rpc fixture and the two-process test (host and desktop); the D-14 pins stay as they were.

## Seed sources and what pins each

The starting point for pinning draws by default with a guard.

| Seed source | Derived from | Pins that exist (helper or fixture) |
|---|---|---|
| decision seed: the mix's draw and, on the same seed, the stop coin (`router_objective.mix.seed_for`, `router.mixture.seed_for`) | fresh decision id | `fake_runtime(seed=…)` with `block_drawing_seed()` (`tests/router_model_fakes.py`; only where both models answer); `_policy_arm_seed` in `instruct_handoff_ih0_helpers`; ih2 `draw` fixture (`never_stop`, `prefer`, `avoid`) and `QUIET` / `NO_CHECKS` (`stop_coin = 0`) in `tests/ih2_lessons_compete_helpers.py`; `never_stop_or_offer_draws` (new); `plan_world`'s staged frame (`STAGED_ROUTER` in `tests/mobile_v2_plan_helpers.py`); F21's `_displaced_probe` sets the process runtime seed |
| numeric policy's Monte Carlo (`objective_chooser.numeric_seed`) | the boundary identity, which holds the plan's fresh id | `block_drawing_seed()` (staged rule serves); `ih4_preferences_inform_router_helpers._pin` (removes plan id and attempt from the key); `never_stop_or_offer_draws(fixed_numeric_seed=True)` (new, unused by a test now: the one test that needed an order took the staged frame); tests of the seed itself leave it live |
| open pick (`router_objective.picks.seed_for`) | factor id | card tests at the arm's zero (D2a); no test reaches it unpinned |
| randomized check (`router_objective.checks.day_seed`) | the local date | `RANDOMIZED_CHECKS_OFF` (`tests/helpers.py`, `check_rate = "off"`); `NO_CHECKS`; a frozen `DAY` |
| lesson suggestions (`router.lesson_suggestions.seed_for`) | fresh ids | ih2 `draw.avoid = ("lesson_offer:",)` / `prefer`; `never_stop_or_offer_draws` |
| not wrapped here | | AD's selection and dose seeds, `delayed_checks`, `router_retrieval` (as in D-14) |

## Left alone

By construction (their subject is the draw or the seed function): `test_plan_determinism_landing`, `test_ih5_successor` replay, `test_ih_numeric_seed`, `test_rospeed2_connections::test_r2…`, `test_ro5_checks::test_the_draw_is_uniform…`. D-19's `test_ih4_preferences_inform_router` twins and `test_sg_slip_vs_gap` sg1/sg2: unchanged, still a possible real behaviour gap. The 20 check-day tests above: deterministic at their frozen day.

## Anything that looks real

No new behaviour difference. The d-19 twins stay open. Not isolated: whether the follow-up's job releasing the held answer before the learner asks is intended (it is a legitimate release path; only the test assumed it had not happened).

## What was not covered

10 unforced repetitions of the file list (2 complete runs and most of a third); `arc_close` tests; the three seed sources not wrapped; the `pick` family (no test reaches it).
