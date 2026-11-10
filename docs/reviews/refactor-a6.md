# Refactor A6: a shorter gate without losing what it catches

Step A6 of `docs/specs/refactor_strategy_v3.md` (§2.3). Owner, Nov 9: "sims should run at each arc's close instead of every landing". Branch `refactor/a6-shorter-gate`, based on main `9a623e3d9c` (A1-A4 and S0 landed).

**Result.** The landing gate (`-n 8 --dist worksteal -m "not arc_close"`, 10 GB scope) went from **16:58 to 12:06** (1,018 s to 725.6 s, 29% less), with every test still run by one of the two gates and no assertion removed. The arc-close gate (`-m arc_close`) takes 6:39 at `-n 8`. The target was 8-10 minutes; the remaining floor is the long tail, not the slowest tests (below, "Why not 8-10 minutes").

## What changed

1. **An `arc_close` marker** (`pyproject.toml`), on 60 tests: the pre-registered simulations and the journeys whose size is the point. `tests/conftest.py` adds `slow` to every `arc_close` test at collection (`pytest_itemcollected`, which runs before `-m` deselects), so `-m "not slow"` while iterating leaves them out too.
2. **A shorter rollout horizon for the mixture tests.** `tests/router_mixture_helpers.py`'s `mixture_env` (65 test files) now writes `horizon_days = 30.0` into the vault's `[router_objective]` table. Each rollout simulates every day to `C + H`, so the 90-day horizon was most of those files' seconds. Eight tests keep the served 90 days through the new `served_horizon` fixture (table below).
3. **Two sweeps split into shards**, every case in exactly one: `test_every_command_prints_its_help` (6 shards, round-robin over the command paths) and P1 in `test_plan_first_transport_offer_grants` (4 shards over the registered RPCs, the answered method in each).
4. **A per-step selector**, `scripts/affected_tests.py`, and a **partition check**, `scripts/check_gate_partition.py`.
5. `scripts/refactor_measures.py` gains the `landing` and `arc_close` timed lanes. `n8` stays the whole suite, so S0 and Z2 still compare like with like.
6. Commands: `CLAUDE.md`, `README.md`, the Developer Map's safe change sequence, Testing and Invariants' verification commands and test table. `docs/algorithm-change-playbook.md` names no suite command, so it is unchanged.

### `slow` and `arc_close`

`arc_close` is a subset of `slow`. `slow` means "leave it out while iterating"; the landing gate still runs a `slow` test. `arc_close` means "only the arc-close gate runs it". A test belongs in `arc_close` only when it is a pre-registered statistical simulation or a journey whose size is the point. Anything else that is slow is shrunk or split, and replay, durability and end-to-end-journey shaped tests stay in the landing gate.

## Marker membership

Seconds are from the orchestrator's full-suite JUnit on `9a623e3d9c` (`-n 8`, the whole suite), and in the arc-close lane on this branch (`-n 8`, those 60 alone).

| Test | Why it is arc_close | Full run (s) | Arc-close lane (s) |
|---|---|---:|---:|
| `test_ad23_sim` (all 56: 20 pass, 36 strict xfail) | AD2+AD3's pre-registered gates at their pre-registered n (`docs/reviews/adaptive-difficulty-ad23.md` §1.5-1.9). Their size can't shrink. `test_ad23_sim_smoke` stays in the landing gate as their stand-in: every scenario, small | 682.6 | 1,479.0 |
| `test_evsi_multisim::test_cli_multisim_quick_fits_every_family_and_reports_claims` | The multi-family study end to end at its quick size, fitted, rerun from saved fits, and re-analysed | 166.6 | 160.6 |
| `test_rofu_weeks::test_two_weeks_after_the_batch` | Two weeks of the follow-up batch on the copy-shaped vault; the test-suite audit's F8 restored it to 15 days because the length is what it shows | 127.7 | 190.3 |
| `test_ro6_tail_data::test_a_few_weeks_on_a_copy_shaped_synthetic_vault` | RO6's few-weeks journey, printed for the stage record | 81.9 | 95.3 |
| `test_ro5_calibration::test_the_first_week_on_a_copy_shaped_synthetic_vault` | RO5's first week at the default arms; its assertions are the week's accounting | 32.4 | 38.6 |
| **60 tests** | | **1,091.2** | **1,963.8** |

In the arc-close lane the sims run side by side, eight at once, and each takes about twice as long as it does among the suite's short tests (CPU contention). The lane's wall is 398.7 s.

**Not split, though the strategy named them.** "The 215 s and 168 s ones" were `test_rofu_weeks` and the multisim CLI test at `a810f628d8`. Both are now `arc_close`, so they no longer bound the landing gate. The multisim test's second half reruns the study from the first half's saved fits and compares them; split in two, the second test would have to fit again (under `--dist worksteal` a module fixture is rebuilt on each worker that runs one of its tests), so the split would cost more than it saves. `test_rofu_weeks` is one journey.

## Times

Every run: `flock /tmp/learnloop-fullsuite.lock`, the empty-home `env -i` wrapper, `systemd-run --user --scope --quiet -p MemoryMax=10G -p MemorySwapMax=2G uv run pytest -q -p no:cacheprovider -n <N> --dist worksteal [-m ...] --junitxml=<scratch>`, `TMPDIR` on the home disk. Wall clock is pytest's own.

| Lane | Tip | Wall | Result | Test seconds |
|---|---|---:|---|---:|
| Before: the whole suite, `-n 8` (the landing gate until now) | main `9a623e3d9c` (orchestrator's run) | 16:58 (1,018 s) | 30,872 passed | 7,779.5 |
| **After: `-m "not arc_close"`, `-n 8`** | this branch, `1fcce2517e` | **12:06 (725.6 s)** | 30,867 passed, 96 skipped, 11 xfailed | **5,588.8** |
| Arc-close gate: `-m arc_close`, `-n 8` | `1fcce2517e` | 6:39 (398.7 s) | 24 passed, 36 xfailed | 1,963.8 |
| Workers: `-m "not arc_close"`, `-n 10` | `1fcce2517e` | stopped at 9:49 (589 s), 99% | 30,869 run, none failed; stopped by hand (below) | not written |

The before figure is the orchestrator's gate on main's tip, used as the brief allows instead of a fourth full run. The after lane ran on a busy machine: another agent's targeted runs (`-n 6`) were under way beside it for part of it.

### Why not 8-10 minutes

At `-n 8` the wall clock is about test seconds / 8 + 45 s (collection, worker start and the session template). After this step the slowest 300 tests hold 1,741 of the landing gate's 5,589 test seconds; the other 30,674 hold 3,848, about 8 minutes of wall clock by themselves. So no work on the slowest tests could bring the gate under about 9 minutes (3,848 / 8 + 45 s), and 9-10 minutes would need the whole slowest 300 to cost almost nothing. What would move it further, each outside this step:

- **The phone-host and two-process tests** (`test_mobile_*`, `test_instruct_handoff_ih0`, `test_ih3_phone_host`): their time is SQLite statements in the host, about 80,000 for `test_mobile_v4_plan`'s six tests. Fewer connection opens per job (F1) is the lever.
- **E1's harness** (`test_e1_harness`, 61 s): `experiments/contextual_embeddings/budget.py` rewrites its whole JSON ledger on every call, quadratic in the calls. That is production code in `experiments/`, which C7 may remove.
- **The objective chooser's day price** computes 64 draws over the horizon once a day for every env; the 30-day horizon took most of it, and the tests that keep 90 days are listed below.

## The slowest 300 remaining tests

The 300 slowest tests outside `arc_close` in the orchestrator's JUnit (`9a623e3d9c`), each measured again in this branch's landing run. **137 shrunk** (1,108 to 448 test seconds), **2 split** (96 to 95 test seconds, but the slowest case went from 52 s to 10.5 s and from 44 s to 11.5 s), **161 kept** (1,179 to 1,130). "Shrunk" means the 30-day horizon took at least a fifth off; a mixture-env test it moved less is listed as kept. Every assertion is unchanged.

**The eight tests that keep the served 90-day horizon** (`@pytest.mark.usefixtures("served_horizon")`):

| Test | Why |
|---|---|
| `test_ro6_codex_rereview::test_f3_the_chooser_values_the_candidates_again_at_the_carried_cutoff` | asserts `cutoff_span == cutoff / 90.0` |
| `test_rofu_learning::test_the_combiner_is_fitted_on_trace_outcomes_at_the_tag_and_the_trace_names_it` | appends its own `[router_objective]` table after the env is built (`append_config_toml` refuses a second one) |
| `test_ih4_preferences_inform_router::test_with_no_preference_the_trace_gains_nothing_and_the_numbers_are_the_predecessors` | a twin comparison. At 14 days the twins diverged intermittently: a different test of these four failed in each of three runs (one twin had a 6th trace, the other 5). They passed twice at 30 days, but a test whose result depends on how fast a rollout finishes stays where it was measured to hold |
| `test_ih4_preferences_inform_router::test_w_pref_at_zero_changes_nothing_bit_for_bit_with_preferences_on_record` | the same |
| `test_ih4_preferences_inform_router::test_the_staged_pick_inside_the_objective_is_the_same_with_preferences_on_record` | the same |
| `test_ih4_preferences_inform_router::test_a_late_carry_thread_in_one_twin_no_longer_moves_the_comparison` | the same |
| `test_ih2_lessons_compete::test_a_requested_item_is_placed_at_the_build_with_no_offer_beside_it` | failed once at 30 days among 65 files at `-n 6`; passed alone three times at 30 and 14 days. Kept at 90 rather than risk a flake |
| `test_ro5_landing::test_r5_1_no_room_to_wait_asks_now_deterministically_and_asks_no_model` | the same |

**A finding for the owner, not fixed here:** IH4's twin tests compare residual numbers across serves after review 3's m5 joined the carried-valuation thread. That they diverge when rollouts get faster suggests a timing dependence the join didn't remove (a refinement batch or a carry that lands in one twin and not the other). They pass at the served horizon, as before. It is worth a look in arc F (speed), where faster rollouts will expose it anyway.

The table (seconds: "before" from the orchestrator's run, "after" from this branch's landing run; for a split test, "after" is the shards' sum):

| # | Test | Before (s) | After (s) | Decision | Reason |
|---:|---|---:|---:|---|---|
| 1 | `test_cli_help_snapshot::test_every_command_prints_its_help` | 52.4 | 50.6 | split | into 6 shards, every case in exactly one; slowest shard 10.5 s |
| 2 | `test_plan_first_transport_offer_grants::test_p1_after_a_yes_to_one_method_only_its_requests_and_units_use_openrouter` | 44.1 | 44.3 | split | into 4 shards, every case in exactly one; slowest shard 11.5 s |
| 3 | `test_sg_slip_vs_gap::test_sg1_freezes_the_sensor_and_every_number_is_the_predecessors` | 31.1 | 13.8 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 4 | `test_ih4_preferences_inform_router::test_a_late_carry_thread_in_one_twin_no_longer_moves_the_comparison` | 27.0 | 27.0 | kept | served horizon: twin comparison; diverged intermittently at 14 days |
| 5 | `test_sketch_verify::test_scenes_at_the_point_cap_over_the_largest_grid_hit_the_output_budget` | 23.7 | 23.2 | kept | the sandbox's output budget at the point cap: the size is the claim, and a sandbox guard belongs in every landing |
| 6 | `test_ro6_tail_data::test_refitting_on_a_later_version_does_not_change_version_ks_evaluation` | 23.6 | 29.2 | kept | its time isn't the wide vault's rollout (another env, or the horizon is a small share) |
| 7 | `test_ih4_preferences_inform_router::test_the_staged_pick_inside_the_objective_is_the_same_with_preferences_on_record` | 23.2 | 23.0 | kept | served horizon: twin comparison; diverged intermittently at 14 days |
| 8 | `test_ih_numeric_seed::test_an_offer_changes_the_identity_and_so_the_seed` | 22.2 | 7.5 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 9 | `test_ro2_ad_raw_document_reads::test_no_code_reached_from_ads_operation_calls_a_raw_document_loader` | 22.0 | 21.1 | kept | static reachability scan over src |
| 10 | `test_sg_slip_vs_gap::test_sg2_moves_only_the_diagnosed_topics_values_and_the_logged_mu_replays` | 21.1 | 9.4 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 11 | `test_ih4_preferences_inform_router::test_with_no_preference_the_trace_gains_nothing_and_the_numbers_are_the_predecessors` | 21.1 | 20.8 | kept | served horizon: twin comparison; diverged intermittently at 14 days (rollout-speed dependence) |
| 12 | `test_ih4_preferences_inform_router::test_w_pref_at_zero_changes_nothing_bit_for_bit_with_preferences_on_record` | 21.1 | 21.1 | kept | served horizon: twin comparison; diverged intermittently at 14 days |
| 13 | `test_rospeed2_connections::test_the_pool_completes_more_draws_by_one_deadline_and_switched_off_is_mains` | 20.6 | 7.8 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 14 | `test_ih_numeric_seed::test_the_workflows_arm_with_no_room_to_wait_seeds_from_its_identity` | 17.8 | 6.2 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 15 | `test_ad_guard_reachable_reads::test_every_table_the_code_running_inside_an_operation_names_is_classified` | 17.6 | 17.8 | kept | static reachability scan over src |
| 16 | `test_ad3_dose_arm::test_cant_tell_exactly_when_the_interval_is_wide_or_minutes_unknown` | 17.3 | 17.2 | kept | fitted-curve reports on fixed synthetic states; the posterior fit is the claim |
| 17 | `test_ad3_dose_arm::test_dose_report_recommendation_follows_fitted_curves` | 17.2 | 17.2 | kept | fitted-curve reports on fixed synthetic states; the posterior fit is the claim |
| 18 | `test_rospeed2_connections::test_every_build_card_and_fit_of_the_jobs_is_the_same_with_the_pool` | 17.2 | 9.2 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 19 | `test_ro6_tail_data::test_a_row_received_after_the_moment_never_enters_a_feature` | 16.9 | 3.4 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 20 | `test_rospeed_ad_link::test_the_switch_off_costs_the_landing_codes_work_on_every_shape` | 16.3 | 15.6 | kept | bit-for-bit identity on every shape, and its speed claim |
| 21 | `test_ro6_tail_data::test_the_transitions_carry_the_objectives_reward_with_named_censoring` | 15.8 | 9.2 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 22 | `test_rw2c_switch_off::test_with_all_four_switches_off_the_sequence_equals_the_base_codes` | 15.6 | 16.2 | kept | switch-off parity with the base code (replay shaped) |
| 23 | `test_mobile_two_process::test_the_desktop_and_the_host_coexist_with_no_lost_writes` | 14.9 | 18.4 | kept | two-process journey (desktop and host): end-to-end and concurrency shaped |
| 24 | `test_mobile_two_process::test_the_phone_and_the_desktop_take_turns_on_one_plan` | 14.8 | 15.9 | kept | two-process journey (desktop and host): end-to-end and concurrency shaped |
| 25 | `test_ih2_lessons_compete::test_a_stuck_miss_changes_no_support_and_the_draw_is_the_mix` | 14.8 | 5.8 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 26 | `test_ih4_preferences_inform_router::test_the_llm_reads_the_card_and_the_trace_names_it` | 14.5 | 8.0 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 27 | `test_ih4_preferences_inform_router::test_a_planted_w_pref_moves_the_argmax_and_leaves_the_tails_values` | 14.1 | 5.7 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 28 | `test_ih4_preferences_inform_router::test_a_failed_sensor_leaves_the_numeric_policy_as_it_was` | 13.5 | 4.8 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 29 | `test_reader_rw6b_p2_landing::test_i_the_narrative_lands_after_a_c1_plan_and_c1s_reading_does_not_move` | 13.2 | 14.3 | kept | landing parity check |
| 30 | `test_ro0_codex_review::test_f7_every_writer_of_the_table_passes_the_initiators_fields` | 12.8 | 9.2 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 31 | `test_ih4_preferences_inform_router::test_w_itself_never_reads_a_preference_or_a_pick` | 12.3 | 4.9 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 32 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[job-job-other-other]` | 11.9 | 4.4 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 33 | `test_ro5_checks::test_the_draw_does_not_change_with_the_action_or_either_policys_output` | 11.7 | 5.1 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 34 | `test_ih4_preferences_inform_router::test_the_sensor_is_frozen_in_the_trace_and_w_pref_starts_at_zero` | 11.3 | 5.3 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 35 | `test_reader_rw2b_fix10::test_item4_with_help_off_and_no_rw2b_assist_the_counts_equal_the_base_codes` | 11.3 | 11.8 | kept | switch-off parity with the base code |
| 36 | `test_coordinated_migrations::test_only_the_coordinator_upgrades_a_vault_database` | 11.1 | 9.5 | kept | multi-process migration |
| 37 | `test_ih2_one_open_offer::test_a_read_drawing_an_offer_during_a_jobs_decision_leaves_one_offer[declined]` | 10.9 | 3.8 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 38 | `test_diagnose_review::test_review_round_trip_under_production_durability` | 10.9 | 10.6 | kept | round trip under production durability |
| 39 | `test_e1_harness::test_the_whole_pilot_with_fakes` | 10.8 | 10.5 | kept | E1 pilot replay with fakes; the time is the experiment's own budget ledger rewriting JSON on every call (`experiments/contextual_embeddings/budget.py`), not the test's size |
| 40 | `test_ad23_contract::test_protected_material_is_indistinguishable_from_absent_material[default]` | 10.7 | 10.2 | kept | AD contract property over protected material |
| 41 | `test_ih2_one_open_offer::test_a_read_drawing_an_offer_during_a_jobs_decision_leaves_one_offer[accepted]` | 10.5 | 3.8 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 42 | `test_ro6_tail_data::test_the_report_states_the_claim_and_lists_versions_and_w_hats_history` | 10.5 | 8.4 | kept | its time isn't the wide vault's rollout (another env, or the horizon is a small share) |
| 43 | `test_rospeed2_connections::test_r2_the_numeric_seed_is_mains_whatever_the_speed_switches[off]` | 10.4 | 4.3 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 44 | `test_ro5_codex_rereview::test_f2_the_same_assignment_administers_the_same_item_whatever_the_policies_answer` | 10.2 | 4.9 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 45 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[job-read-lesson-other]` | 9.9 | 3.1 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 46 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[job-job-lesson-lesson]` | 9.9 | 3.6 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 47 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[job-job-lesson-other]` | 9.8 | 3.5 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 48 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[job-job-other-lesson]` | 9.8 | 3.6 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 49 | `test_facet_locks_landing::test_the_bypass_test_parses_the_sources_track_and_none_of_it_writes_facet_meaning` | 9.5 | 10.6 | kept | static scan of the sources |
| 50 | `test_reader_rw2b_fix11::test_item3_a_book_opened_during_grading_leaves_the_count_and_type_as_the_base_stores_them` | 9.5 | 9.4 | kept | parity with the base code |
| 51 | `test_rofu_learning::test_the_combiner_is_fitted_on_trace_outcomes_at_the_tag_and_the_trace_names_it` | 9.4 | 10.0 | kept | served horizon: appends its own `[router_objective]` table after the env is built |
| 52 | `test_rospeed2_connections::test_r2_the_numeric_seed_is_mains_whatever_the_speed_switches[on]` | 9.4 | 3.9 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 53 | `test_ro6_landing::test_r7_a_planted_slope_on_supported_terms_is_recovered_beside_many_unsupported_at_the_draw` | 9.4 | 9.1 | kept | its time isn't the wide vault's rollout (another env, or the horizon is a small share) |
| 54 | `test_rofu_learning::test_the_report_says_what_the_rollouts_read` | 9.4 | 4.0 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 55 | `test_rofu_learning::test_the_rollouts_read_ads_posterior_and_the_trace_holds_the_numbers_at_the_tag` | 9.4 | 4.0 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 56 | `test_ro1_availability_reads::test_every_time_cutoff_read_of_attempts_uses_the_predicate_or_is_allowlisted` | 9.4 | 6.8 | kept | static scan of every read in src |
| 57 | `test_ih2_offer_ceiling_and_unseen::test_offers_nobody_saw_use_up_nothing_and_a_lesson_keeps_competing_past_the_ceiling` | 9.3 | 3.4 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 58 | `test_recurrence_commands::test_rebuild_makes_no_model_call_and_is_a_fixed_point` | 9.3 | 9.9 | kept | rebuild fixed point and replay |
| 59 | `test_ih2_one_open_offer::test_a_job_that_draws_the_followup_leaves_the_read_offer_alone` | 9.1 | 3.1 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 60 | `test_rofu_carried::test_the_no_model_branch_defers_its_carried_valuation_off_the_serving_path` | 9.1 | 4.0 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 61 | `test_rofu_carried::test_an_early_publication_served_keeps_its_carried_valuation` | 9.1 | 4.6 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 62 | `test_rofu_generator_switches::test_flipping_a_serving_switch_is_a_new_generator_version[held_ad_link]` | 9.1 | 3.7 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 63 | `test_e0_review_round1::test_f4_f11_the_paid_cli_keeps_receipts_in_its_own_repository_and_resumes` | 9.1 | 8.3 | kept | E0 paid-run fakes and receipts |
| 64 | `test_ih_numeric_seed::test_the_boundary_contest_seeds_from_its_identity[both_models]` | 9.0 | 3.5 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 65 | `test_e0_relabel_round::test_a_reused_run_resends_only_the_changed_requests_and_keeps_its_own_results` | 9.0 | 7.2 | kept | E0 fakes |
| 66 | `test_evsi_single_family_unbounded::test_the_bound_attribution_needs_the_bound_the_other_report_applied` | 9.0 | 9.0 | kept | EVSI on the fixed synthetic bank; the bound needs the bank |
| 67 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[job-read-other-lesson]` | 8.9 | 3.1 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 68 | `test_ad23_fix_review::test_density_lowerings_join_offers_to_their_visits` | 8.9 | 8.9 | kept | AD fix property |
| 69 | `test_rw5c_labels::test_every_other_code_owned_label_template_renders_in_katex` | 8.9 | 8.8 | kept | label sweep |
| 70 | `test_ih2_one_open_offer::test_an_unwritten_workflow_waits_on_the_offer_that_replaced_the_one_it_lost_to` | 8.8 | 3.2 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 71 | `test_plan_determinism::test_a_contrast_pair_plans_the_same_staged_block_in_every_session[one_fits]` | 8.8 | 7.8 | kept | replay-shaped: the same plan in every session |
| 72 | `test_ih2_one_open_offer::test_a_superseded_offer_passing_a_later_day_is_not_read_as_a_decline` | 8.8 | 3.0 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 73 | `test_evsi_single_family_unbounded::test_the_single_family_path_defaults_to_no_count_bound` | 8.7 | 8.6 | kept | EVSI on the fixed synthetic bank; the bound needs the bank |
| 74 | `test_ad3_dose_arm::test_recommendations_never_act` | 8.6 | 8.6 | kept | fitted-curve reports on fixed synthetic states; the posterior fit is the claim |
| 75 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[job-read-other-other]` | 8.6 | 3.1 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 76 | `test_sketch_verify::test_the_largest_legal_grid_is_verified_one_point_read_at_a_time` | 8.6 | 7.5 | kept | the sandbox's output budget at the point cap: the size is the claim, and a sandbox guard belongs in every landing |
| 77 | `test_rofu_switch_key::test_flipping_a_switch_between_prefetch_and_serve_starts_a_new_job[held_ad_link]` | 8.6 | 3.4 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 78 | `test_rofu_generator_switches::test_flipping_a_serving_switch_is_a_new_generator_version[combiner_trace_outcomes]` | 8.5 | 3.6 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 79 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[job-read-lesson-lesson]` | 8.4 | 3.1 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 80 | `test_rofu_generator_switches::test_flipping_a_serving_switch_is_a_new_generator_version[merged_sessions]` | 8.4 | 3.6 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 81 | `test_recurrence_commands::test_a_vault_with_no_merges_rebuilds_with_an_empty_projection` | 8.4 | 7.4 | kept | rebuild fixed point and replay |
| 82 | `test_rofu_generator_switches::test_flipping_a_serving_switch_is_a_new_generator_version[pooled_connections]` | 8.4 | 3.6 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 83 | `test_rofu_switch_key::test_flipping_a_switch_between_prefetch_and_serve_starts_a_new_job[merged_sessions]` | 8.4 | 3.5 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 84 | `test_rofu_generator_switches::test_flipping_a_serving_switch_is_a_new_generator_version[held_reading_map]` | 8.4 | 3.6 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 85 | `test_rofu_switch_key::test_flipping_a_switch_between_prefetch_and_serve_starts_a_new_job[combiner_trace_outcomes]` | 8.4 | 3.4 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 86 | `test_reading_request_sweep::test_the_sweep_acts_once_the_books_work_ends_on_the_sidecars_own_worker` | 8.3 | 9.8 | kept | a sweep over every reading request kind |
| 87 | `test_rofu_generator_switches::test_flipping_a_serving_switch_is_a_new_generator_version[monotone_combiner]` | 8.3 | 3.7 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 88 | `test_rofu_ad_link::test_the_probe_with_ads_own_predictive_is_pinned[512]` | 8.3 | 8.5 | kept | its time isn't the wide vault's rollout (another env, or the horizon is a small share) |
| 89 | `test_rofu_generator_switches::test_flipping_a_serving_switch_is_a_new_generator_version[scope_extension]` | 8.3 | 3.7 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 90 | `test_ih_numeric_seed::test_the_boundary_contest_seeds_from_its_identity[no_models]` | 8.2 | 3.0 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 91 | `test_plan_determinism::test_the_same_vault_state_plans_the_same_staged_blocks_in_every_session` | 8.2 | 7.8 | kept | replay-shaped: the same plan in every session |
| 92 | `test_ih2_offer_ceiling_and_unseen::test_draws_on_reads_are_bounded_by_the_followups_that_became_ready` | 8.2 | 2.8 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 93 | `test_plan_determinism::test_a_contrast_pair_plans_the_same_staged_block_in_every_session[both_fit]` | 8.1 | 8.5 | kept | replay-shaped: the same plan in every session |
| 94 | `test_ro6_serving::test_at_the_tag_the_trace_carries_the_residual_and_its_terms_recompute` | 8.1 | 0.8 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 95 | `test_rofu_switch_key::test_flipping_a_switch_between_prefetch_and_serve_starts_a_new_job[held_reading_map]` | 8.1 | 3.3 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 96 | `test_ro1_availability_reads::test_table_named_cutoff_reads_of_attempts_ask_the_predicate` | 8.1 | 6.3 | kept | static scan of every read in src |
| 97 | `test_rofu_switch_key::test_flipping_a_switch_between_prefetch_and_serve_starts_a_new_job[monotone_combiner]` | 8.1 | 3.3 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 98 | `test_rofu_switch_key::test_flipping_a_switch_between_prefetch_and_serve_starts_a_new_job[carried_in_prefetch]` | 8.1 | 3.3 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 99 | `test_ro6_codex_rereview::test_f3_the_chooser_values_the_candidates_again_at_the_carried_cutoff` | 8.1 | 8.0 | kept | served horizon: asserts the served 90-day horizon (`/ 90.0`) |
| 100 | `test_rofu_switch_key::test_flipping_a_switch_between_prefetch_and_serve_starts_a_new_job[pooled_connections]` | 8.1 | 3.3 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 101 | `test_rofu_carried::test_with_models_the_wait_returns_and_the_next_prefetch_runs_it` | 8.1 | 3.4 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 102 | `test_rofu_switch_key::test_flipping_a_switch_between_prefetch_and_serve_starts_a_new_job[scope_extension]` | 8.0 | 3.3 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 103 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[boundary_read-job-lesson-lesson]` | 8.0 | 2.9 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 104 | `test_ih2_one_open_offer::test_a_boundary_drawing_a_block_leaves_the_jobs_offer_first_and_its_own_block_next` | 8.0 | 3.1 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 105 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[boundary_serve-job-lesson-lesson]` | 8.0 | 3.0 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 106 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[boundary_serve-job-other-other]` | 7.9 | 3.1 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 107 | `test_ih2_one_open_offer::test_a_boundary_drawing_an_offer_replaces_the_jobs_offer_placed_under_it` | 7.9 | 2.9 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 108 | `test_rofu_generator_switches::test_flipping_a_serving_switch_is_a_new_generator_version[consistent_review_draw]` | 7.9 | 3.5 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 109 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[boundary_read-job-other-lesson]` | 7.9 | 2.9 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 110 | `test_ro6_serving::test_below_the_tag_and_switched_off_serve_mvp_048_exactly[switch_off]` | 7.9 | 4.2 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 111 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[boundary_read-job-lesson-other]` | 7.9 | 2.9 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 112 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[boundary_serve-job-lesson-other]` | 7.9 | 3.0 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 113 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[boundary_read-job-other-other]` | 7.9 | 3.0 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 114 | `test_ih3_phone_host::test_a_lesson_kept_at_a_finished_block_draws_nothing_through_its_reply` | 7.8 | 7.7 | kept | its time isn't the wide vault's rollout (another env, or the horizon is a small share) |
| 115 | `test_graph_nomination_ingest::test_structuring_sees_registry_definitions_and_decides_a_registry_merge` | 7.8 | 7.5 | kept | under 10 s, one case; no repeated structure to shrink |
| 116 | `test_e1_harness::test_a_smoke_only_local_run_loads_checks_and_stores_nothing` | 7.8 | 7.6 | kept | E1 pilot replay with fakes; the time is the experiment's own budget ledger rewriting JSON on every call (`experiments/contextual_embeddings/budget.py`), not the test's size |
| 117 | `test_rofu_switch_key::test_flipping_a_switch_between_prefetch_and_serve_starts_a_new_job[consistent_review_draw]` | 7.7 | 3.2 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 118 | `test_e1_harness::test_the_replay_reproduces_e0_without_any_call_and_the_plan_is_frozen` | 7.6 | 7.0 | kept | E1 pilot replay with fakes; the time is the experiment's own budget ledger rewriting JSON on every call (`experiments/contextual_embeddings/budget.py`), not the test's size |
| 119 | `test_rofu_generator_switches::test_flipping_a_serving_switch_is_a_new_generator_version[ad_predictive_link]` | 7.6 | 3.2 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 120 | `test_mobile_v2_checks::test_j6_a_check_the_phone_can_show_is_served_on_the_phone_as_an_ordinary_item` | 7.6 | 3.9 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 121 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[boundary_serve-job-other-lesson]` | 7.6 | 3.0 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 122 | `test_evsi_multisim::test_the_package_with_every_piece_put_back_is_the_successor` | 7.5 | 7.3 | kept | the module's fitted-family fixture, shared by its other tests |
| 123 | `test_rofu_generator_switches::test_carried_in_prefetch_is_not_part_of_the_generator` | 7.5 | 3.4 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 124 | `test_ih4_preferences_inform_router::test_with_the_learned_tail_off_the_sensor_freezes_and_w_pref_is_not_fitted` | 7.4 | 0.9 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 125 | `test_rofu_switch_key::test_flipping_a_switch_between_prefetch_and_serve_starts_a_new_job[ad_predictive_link]` | 7.4 | 3.1 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 126 | `test_e1_harness::test_preflight_reports_every_check_and_is_not_ready_without_the_model` | 7.3 | 6.9 | kept | E1 pilot replay with fakes; the time is the experiment's own budget ledger rewriting JSON on every call (`experiments/contextual_embeddings/budget.py`), not the test's size |
| 127 | `test_ih_numeric_seed::test_the_serve_without_a_prefetch_starts_the_same_job_the_prefetch_would` | 7.2 | 7.2 | kept | its time isn't the wide vault's rollout (another env, or the horizon is a small share) |
| 128 | `test_instruct_handoff_ih0::test_a_slow_llm_within_the_wait_is_served_and_does_not_fall_back` | 7.1 | 7.3 | kept | phone-host journey over the real host (end-to-end shaped) |
| 129 | `test_ro5_stop_coin::test_every_arm_off_at_the_tag_is_mvp_047_exactly` | 7.1 | 4.2 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 130 | `test_reading_request_sweep::test_b_a_start_deferred_behind_a_queued_build_runs_that_build_and_then_acts` | 7.1 | 6.3 | kept | a sweep over every reading request kind |
| 131 | `test_rofu_carried::test_the_switch_turned_off_after_carriers_exist_reads_the_predecessors_transitions` | 7.1 | 3.1 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 132 | `test_e1_harness::test_the_cli_plans_from_e0_manifests_offline` | 7.1 | 6.2 | kept | E1 pilot replay with fakes; the time is the experiment's own budget ledger rewriting JSON on every call (`experiments/contextual_embeddings/budget.py`), not the test's size |
| 133 | `test_e1_harness::test_a_wrong_label_pool_misses_e0s_checkpoints_and_the_replay_is_unverified` | 7.0 | 6.4 | kept | E1 pilot replay with fakes; the time is the experiment's own budget ledger rewriting JSON on every call (`experiments/contextual_embeddings/budget.py`), not the test's size |
| 134 | `test_e0_review_round4::test_h3_two_paid_runs_with_different_run_directories_share_one_budget` | 7.0 | 6.3 | kept | under 10 s, one case; no repeated structure to shrink |
| 135 | `test_ih4_preferences_inform_router::test_a_new_preference_starts_a_new_job_and_moves_no_seed` | 6.9 | 6.8 | kept | its time isn't the wide vault's rollout (another env, or the horizon is a small share) |
| 136 | `test_rospeed_join::test_a_regrade_or_hold_between_the_jobs_card_and_numeric_builds_reaches_the_numeric_policy[hold]` | 6.9 | 2.7 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 137 | `test_ro1_availability_reads::test_the_decision_time_readers_ask_the_predicate` | 6.9 | 5.3 | kept | static scan of every read in src |
| 138 | `test_e1_harness::test_a_provisional_plan_runs_no_stage` | 6.9 | 5.9 | kept | E1 pilot replay with fakes; the time is the experiment's own budget ledger rewriting JSON on every call (`experiments/contextual_embeddings/budget.py`), not the test's size |
| 139 | `test_rospeed_ad_link::test_the_linear_algebra_shaped_evaluation_is_faster` | 6.8 | 6.6 | kept | bit-for-bit identity on every shape, and its speed claim |
| 140 | `test_ih2_one_open_offer::test_off_a_draw_racing_a_draw_is_the_predecessors` | 6.8 | 2.4 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 141 | `test_rospeed_join::test_a_regrade_or_hold_between_the_jobs_card_and_numeric_builds_reaches_the_numeric_policy[regrade]` | 6.8 | 2.7 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 142 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[boundary_serve-read-lesson-other]` | 6.8 | 2.6 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 143 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[boundary_serve-read-other-lesson]` | 6.7 | 2.4 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 144 | `test_pf_reports::test_suspect_acceptance_is_descriptive_and_never_ranks_a_tier` | 6.7 | 5.3 | kept | practice-family reports over a seeded vault with fakes |
| 145 | `test_ih2_lessons_compete::test_replay_gives_every_logged_decision_its_logged_mu` | 6.6 | 2.5 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 146 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[boundary_serve-read-other-other]` | 6.6 | 2.5 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 147 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[boundary_serve-read-lesson-lesson]` | 6.6 | 2.5 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 148 | `test_codex_lockdown_round3::test_every_process_launch_site_is_approved` | 6.6 | 3.4 | kept | under 10 s, one case; no repeated structure to shrink |
| 149 | `test_source_service_spend_accounting::test_a_killed_owner_process_is_recovered_while_a_live_ones_lease_holds` | 6.6 | 6.5 | kept | under 10 s, one case; no repeated structure to shrink |
| 150 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[boundary_read-read-other-other]` | 6.5 | 2.5 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 151 | `test_codex_lockdown_round2::test_every_codex_turn_app_server_and_transport_in_the_source_is_the_locked_down_one` | 6.5 | 6.5 | kept | under 10 s, one case; no repeated structure to shrink |
| 152 | `test_e1_harness::test_an_unfinished_e0_run_is_not_imported_and_the_manifest_plan_is_provisional` | 6.5 | 5.9 | kept | E1 pilot replay with fakes; the time is the experiment's own budget ledger rewriting JSON on every call (`experiments/contextual_embeddings/budget.py`), not the test's size |
| 153 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[boundary_read-read-lesson-lesson]` | 6.5 | 2.5 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 154 | `test_followup_codex_review::test_f7_verify_no_other_writer_of_a_terminal_state` | 6.5 | 6.3 | kept | under 10 s, one case; no repeated structure to shrink |
| 155 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[boundary_read-read-other-lesson]` | 6.5 | 2.4 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 156 | `test_ih2_one_open_offer::test_at_most_one_open_offer_across_read_and_job_interleavings[boundary_read-read-lesson-other]` | 6.5 | 2.5 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 157 | `test_ih_numeric_seed::test_the_workflows_lesson_arm_seeds_from_its_identity[no_models]` | 6.5 | 2.4 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 158 | `test_reader_rw2b_review::test_f3r_an_operator_is_checked_on_its_written_operand_and_names_on_their_definitions` | 6.4 | 5.9 | kept | parity with the base code |
| 159 | `test_planted_misgrade::test_abstention_budget_loop_chooses_or_alarms` | 6.4 | 6.5 | kept | under 10 s, one case; no repeated structure to shrink |
| 160 | `test_narrative_rollback_overlap::test_a_reader_arriving_after_the_claim_delays_the_narrative_by_the_lease_and_doesnt_lose_it` | 6.4 | 5.0 | kept | rollback and overlap (durability shaped) |
| 161 | `test_pf_reports::test_scaling_check_reports_each_tier_and_component` | 6.4 | 5.6 | kept | practice-family reports over a seeded vault with fakes |
| 162 | `test_ih2_offer_ceiling_and_unseen::test_an_offer_nobody_saw_leaves_the_days_ceiling_free_at_the_next_fresh_boundary` | 6.4 | 2.4 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 163 | `test_ih_numeric_seed::test_the_workflows_lesson_arm_seeds_from_its_identity[both_models]` | 6.4 | 2.4 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 164 | `test_ih_numeric_seed::test_the_need_paths_lesson_arm_seeds_from_its_identity[both_models]` | 6.3 | 2.5 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 165 | `test_evsi_single_family_unbounded::test_every_recorded_value_is_compared` | 6.3 | 6.1 | kept | EVSI on the fixed synthetic bank; the bound needs the bank |
| 166 | `test_ih_numeric_seed::test_with_the_switch_off_the_block_still_seeds_from_its_identity` | 6.3 | 2.4 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 167 | `test_ih2_offer_ceiling_and_unseen::test_a_need_followups_draw_stands_at_the_boundary` | 6.2 | 1.9 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 168 | `test_evsi_calibration_sim::test_cli_simulate_quick_writes_a_report` | 6.2 | 6.0 | kept | under 10 s, one case; no repeated structure to shrink |
| 169 | `test_te3b_offers::test_g3_mu_recomputes_with_an_offer_in_the_support_on_every_path` | 6.1 | 2.7 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 170 | `test_narrative_rollback_overlap::test_a_reader_past_the_busy_timeout_doesnt_lose_the_narrative` | 6.1 | 5.6 | kept | rollback and overlap (durability shaped) |
| 171 | `test_stuck_prompt_replay::test_a_stuck_vault_rebuilds_to_a_fixed_point_with_no_model_call` | 6.1 | 6.8 | kept | under 10 s, one case; no repeated structure to shrink |
| 172 | `test_ih2_lessons_compete::test_taking_the_lesson_settles_the_followup_honestly` | 6.1 | 2.3 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 173 | `test_ad_guard::test_the_ad_pipeline_runs_with_zero_denials` | 6.1 | 5.7 | kept | AD guard scans |
| 174 | `test_narrative_rollback_overlap::test_a_reader_shorter_than_the_busy_timeout_only_delays_the_narrative` | 6.0 | 5.7 | kept | rollback and overlap (durability shaped) |
| 175 | `test_mobile_host_auth::test_every_method_outside_the_m2_row_is_http_denied` | 5.9 | 5.2 | kept | under 10 s, one case; no repeated structure to shrink |
| 176 | `test_pf_reports::test_report_dry_runs_price_and_admit_the_blind_judge` | 5.8 | 4.7 | kept | practice-family reports over a seeded vault with fakes |
| 177 | `test_pf_reports::test_pilot_recommends_only_from_agreed_comparisons_on_the_same_families` | 5.8 | 4.4 | kept | practice-family reports over a seeded vault with fakes |
| 178 | `test_ih2_lessons_compete::test_with_no_room_to_wait_a_lesson_makes_it_a_real_draw_and_with_none_it_stays_deterministic` | 5.7 | 2.1 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 179 | `test_ad23_sim_smoke::test_the_scenario_runs_and_reports_its_conditions_and_finite_figures[AD3-7 practice]` | 5.7 | 5.9 | kept | the landing gate's stand-in for the arc_close sims: every scenario, small |
| 180 | `test_collection_dataset::test_production_lane_and_live_backup_preserve_committed_state` | 5.7 | 6.0 | kept | under 10 s, one case; no repeated structure to shrink |
| 181 | `test_ih2_offer_ceiling_and_unseen::test_a_followups_draw_stands_only_while_no_offer_has_been_drawn_since` | 5.7 | 2.2 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 182 | `test_recurrence_commands::test_the_upgrade_command_defaults_to_the_latest` | 5.7 | 5.1 | kept | rebuild fixed point and replay |
| 183 | `test_coordinated_migrations::test_only_the_vault_opener_constructs_a_repository` | 5.6 | 4.5 | kept | multi-process migration |
| 184 | `test_evsi_single_family_unbounded::test_cli_simulate_passes_an_explicit_bound_through` | 5.6 | 5.6 | kept | EVSI on the fixed synthetic bank; the bound needs the bank |
| 185 | `test_ad_guard::test_every_ad_entry_point_declares_its_write_form_and_writers_use_the_savepoint_form` | 5.6 | 4.7 | kept | AD guard scans |
| 186 | `test_mobile_v2_plan::test_j5_the_plan_ends_and_the_phone_stops_or_keeps_going` | 5.5 | 4.9 | kept | phone-host journey |
| 187 | `test_plan_first_transport_offer_grants::test_the_dispatch_alone_opens_a_request_and_one_site_inherits` | 5.5 | 5.2 | kept | under 10 s, one case; no repeated structure to shrink |
| 188 | `test_ih3_phone_host::test_a_phone_agreement_draws_nothing_either` | 5.5 | 5.3 | kept | its time isn't the wide vault's rollout (another env, or the horizon is a small share) |
| 189 | `test_ih_numeric_seed::test_the_workflows_decision_with_no_lesson_keeps_the_predecessors_identity` | 5.4 | 2.1 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 190 | `test_mobile_v4_plan::test_the_phones_plan_reading_ended_is_the_desktops[skipped]` | 5.4 | 4.5 | kept | phone-host journey; the time is SQLite work in the host |
| 191 | `test_narrative_rollback_overlap::test_with_no_reader_the_narrative_lands_on_a_rollback_vault` | 5.4 | 5.4 | kept | rollback and overlap (durability shaped) |
| 192 | `test_ih_numeric_seed::test_the_need_paths_lesson_arm_seeds_from_its_identity[no_models]` | 5.4 | 2.1 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 193 | `test_pf_generation::test_an_interrupted_run_resumes_without_repaying_finished_work` | 5.4 | 4.0 | kept | practice-family generation with fakes |
| 194 | `test_architecture::test_only_the_hint_context_reads_its_raw_verdicts` | 5.4 | 3.1 | kept | static architecture scans over src |
| 195 | `test_ih2_lessons_compete::test_not_now_with_the_ceiling_reached_the_followup_serves` | 5.4 | 2.0 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 196 | `test_mobile_rpc::test_every_other_registered_method_answers_403` | 5.3 | 5.5 | kept | under 10 s, one case; no repeated structure to shrink |
| 197 | `test_ih2_offer_ceiling_and_unseen::test_reads_alone_never_redraw_two_followups_against_each_other` | 5.3 | 2.1 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 198 | `test_ih2_lessons_compete::test_not_now_leaves_a_ready_probe_available_to_the_next_decision` | 5.3 | 2.0 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 199 | `test_architecture::test_runtime_packages_import_only_public_cross_boundary_names` | 5.3 | 6.8 | kept | static architecture scans over src |
| 200 | `test_evsi_multisim::test_the_calibrated_systems_average_responses_over_the_item_pool` | 5.3 | 5.3 | kept | the module's fitted-family fixture, shared by its other tests |
| 201 | `test_mobile_v4_plan::test_the_phone_takes_a_reading_block_and_ends_it_as_the_desktop_does` | 5.3 | 5.2 | kept | phone-host journey; the time is SQLite work in the host |
| 202 | `test_ad23_sim_smoke::test_the_scenario_runs_and_reports_its_conditions_and_finite_figures[AD3-11 base]` | 5.3 | 5.1 | kept | the landing gate's stand-in for the arc_close sims: every scenario, small |
| 203 | `test_rofu_switch_key::test_a_served_cached_answer_names_the_generator_that_produced_it[monotone_combiner]` | 5.2 | 2.2 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 204 | `test_rofu_switch_key::test_a_served_cached_answer_names_the_generator_that_produced_it[consistent_review_draw]` | 5.2 | 2.2 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 205 | `test_ih3_phone_host::test_a_served_choice_replies_with_its_step_and_a_retry_says_the_same` | 5.2 | 5.1 | kept | its time isn't the wide vault's rollout (another env, or the horizon is a small share) |
| 206 | `test_mobile_v4_plan::test_a_reading_the_phone_may_not_show_stays_held` | 5.2 | 4.2 | kept | phone-host journey; the time is SQLite work in the host |
| 207 | `test_ih2_lessons_compete::test_the_journey_on_a_real_miss_lesson_then_not_now_then_the_question[True]` | 5.2 | 5.1 | kept | its time isn't the wide vault's rollout (another env, or the horizon is a small share) |
| 208 | `test_ingest_queue_store::test_ingest_queue_sql_has_one_persistence_owner` | 5.1 | 4.6 | kept | under 10 s, one case; no repeated structure to shrink |
| 209 | `test_mobile_v4_plan::test_a_cached_v3_app_keeps_every_reading_for_the_desktop` | 5.1 | 4.3 | kept | phone-host journey; the time is SQLite work in the host |
| 210 | `test_e0_paid_fakes::test_resume_pays_only_for_what_is_missing` | 5.1 | 4.8 | kept | under 10 s, one case; no repeated structure to shrink |
| 211 | `test_chatgpt_plan_workspace::test_an_interrupt_mid_turn_stops_it_and_keeps_what_was_served` | 5.1 | 5.1 | kept | under 10 s, one case; no repeated structure to shrink |
| 212 | `test_ih2_lessons_compete::test_a_probe_mode_item_in_a_contest_is_valued_by_the_probe_bundle` | 5.1 | 1.9 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 213 | `test_ih2_lessons_compete::test_a_probe_whose_decision_already_beat_the_lesson_is_not_contested_twice` | 5.1 | 2.0 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 214 | `test_e0_isolation::test_no_production_module_imports_the_experiments` | 5.0 | 3.6 | kept | under 10 s, one case; no repeated structure to shrink |
| 215 | `test_mobile_v4_plan::test_the_phones_decisions_name_its_reader_and_the_media_rules` | 5.0 | 4.1 | kept | phone-host journey; the time is SQLite work in the host |
| 216 | `test_pf_reports::test_pilot_compares_all_three_arms_and_the_blind_judge_is_two_pass` | 5.0 | 4.2 | kept | practice-family reports over a seeded vault with fakes |
| 217 | `test_ih2_lessons_compete::test_not_now_on_the_need_path_leaves_the_item_in_the_pool` | 5.0 | 1.9 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 218 | `test_connection_reuse::test_src_reads_no_rowid_counter_a_kept_connection_would_carry_over` | 5.0 | 3.6 | kept | under 10 s, one case; no repeated structure to shrink |
| 219 | `test_sidecar_contract::test_sidecar_proposals_get_accept_reject_undo` | 5.0 | 3.6 | kept | under 10 s, one case; no repeated structure to shrink |
| 220 | `test_diagnosis_replay::test_replay_makes_zero_model_and_embedding_calls` | 5.0 | 3.9 | kept | replay |
| 221 | `test_ih6_workbench_open_item::test_a_phone_read_holds_says_so_and_a_phone_serve_still_decides` | 4.9 | 5.0 | kept | its time isn't the wide vault's rollout (another env, or the horizon is a small share) |
| 222 | `test_te3b_offers::test_moving_on_without_an_answer_is_ignored_at_the_next_boundary` | 4.9 | 1.9 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 223 | `test_ih2_one_open_offer::test_a_need_decision_replacing_an_interrupting_offer_keeps_its_place_and_what_it_beat` | 4.9 | 2.0 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 224 | `test_ih2_offer_ceiling_and_unseen::test_replacing_again_at_the_ceiling_still_contests` | 4.9 | 1.9 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 225 | `test_ad23_contract::test_request_authoring_proposal_is_called_from_the_guarded_dispatch_only` | 4.9 | 5.0 | kept | AD contract property over protected material |
| 226 | `test_mobile_v3_carried::test_more_new_confirmed_on_a_finished_plan_refused_mid_build_leaves_no_override_receipt` | 4.8 | 4.9 | kept | phone-host journey |
| 227 | `test_mobile_v2_plan::test_j1_a_read_never_crosses_past_held_work_and_next_does_once` | 4.8 | 4.8 | kept | phone-host journey |
| 228 | `test_ro4_objective_serving::test_a_numeric_timeout_is_a_failure_and_both_failed_keeps_the_floor` | 4.8 | 2.3 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 229 | `test_mobile_v3_carried::test_keep_going_on_a_finished_plan_commits_its_override_with_the_extension` | 4.8 | 5.1 | kept | phone-host journey |
| 230 | `test_te3b_population::test_switch_off_or_below_the_tag_values_the_same_database_as_mvp052` | 4.8 | 1.9 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 231 | `test_mobile_v2_plan::test_j1_the_phones_boundary_decisions_record_phone_plan_and_the_device_rules` | 4.8 | 4.2 | kept | phone-host journey |
| 232 | `test_voi_v2::test_in_the_real_probe_vault_the_gate_no_longer_ends_a_paying_episode` | 4.8 | 4.7 | kept | under 10 s, one case; no repeated structure to shrink |
| 233 | `test_ih4_preferences_inform_router::test_a_real_choice_freezes_its_inputs_and_the_next_decision_reads_it` | 4.7 | 2.0 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 234 | `test_reader_rw2b_review::test_f3r_the_whole_written_relation_is_what_is_checked` | 4.7 | 4.2 | kept | parity with the base code |
| 235 | `test_ro5_landing::test_r8_each_arm_can_be_drawn_with_its_logged_probability_and_no_intervention_serves_no_probe` | 4.7 | 2.0 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 236 | `test_plan_first_transport_offer_grants_r5::test_m1_every_unit_is_opened_with_its_vault` | 4.7 | 4.3 | kept | under 10 s, one case; no repeated structure to shrink |
| 237 | `test_mobile_v3_carried::test_keep_going_on_a_finished_plan_refused_mid_build_leaves_no_override_receipt` | 4.7 | 4.7 | kept | phone-host journey |
| 238 | `test_mobile_v4_plan::test_the_phones_plan_reading_ended_is_the_desktops[left_reader]` | 4.6 | 4.5 | kept | phone-host journey; the time is SQLite work in the host |
| 239 | `test_ih2_lessons_compete::test_an_interrupting_offer_never_comes_over_an_open_item` | 4.6 | 1.1 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 240 | `test_diagnosis_replay::test_split_vault_rebuild_is_a_fixed_point_and_keeps_diagnosis_sourced_causes` | 4.6 | 4.0 | kept | replay |
| 241 | `test_library_ask_review::test_two_organizer_requests_in_flight_cannot_both_pass_the_cap` | 4.6 | 4.5 | kept | under 10 s, one case; no repeated structure to shrink |
| 242 | `test_instruct_handoff_ih0::test_it_is_idempotent` | 4.6 | 4.6 | kept | phone-host journey over the real host (end-to-end shaped) |
| 243 | `test_mobile_v3_carried::test_the_desktops_keep_going_on_a_finished_plan_records_as_before` | 4.6 | 4.7 | kept | phone-host journey |
| 244 | `test_plan_determinism_landing::test_different_seeds_still_draw_different_blocks_and_the_switch_leaves_the_draw_alone` | 4.6 | 4.7 | kept | replay-shaped |
| 245 | `test_instruct_handoff_ih0::test_the_serve_finds_the_job_and_makes_no_second_llm_call` | 4.6 | 4.6 | kept | phone-host journey over the real host (end-to-end shaped) |
| 246 | `test_ih3_phone_host::test_a_retry_of_a_kept_lesson_still_says_it_waits` | 4.6 | 4.6 | kept | its time isn't the wide vault's rollout (another env, or the horizon is a small share) |
| 247 | `test_evsi_single_family_unbounded::test_the_comparison_tools_ordering_is_stable` | 4.6 | 4.6 | kept | EVSI on the fixed synthetic bank; the bound needs the bank |
| 248 | `test_architecture::test_stored_symbolic_results_are_read_only_through_the_one_accessor` | 4.6 | 4.6 | kept | static architecture scans over src |
| 249 | `test_rofu_speed::test_a_deadline_admits_more_draws_merged_so_the_default_is_the_per_block_loop` | 4.6 | 4.5 | kept | its time isn't the wide vault's rollout (another env, or the horizon is a small share) |
| 250 | `test_instruct_handoff_ih0::test_the_prefetch_leaves_the_answered_items_plan_events_to_the_serve` | 4.6 | 4.5 | kept | phone-host journey over the real host (end-to-end shaped) |
| 251 | `test_instruct_handoff_ih0::test_the_key_survives_the_learner_reading_feedback` | 4.5 | 4.6 | kept | phone-host journey over the real host (end-to-end shaped) |
| 252 | `test_ih_numeric_seed::test_the_start_only_prefetch_and_its_serve_compute_one_key_and_one_seed` | 4.5 | 5.0 | kept | its time isn't the wide vault's rollout (another env, or the horizon is a small share) |
| 253 | `test_required_method_authority::test_a_variant_with_no_verdict_or_an_edited_stem_is_not_published` | 4.5 | 3.3 | kept | under 10 s, one case; no repeated structure to shrink |
| 254 | `test_ih4_preferences_inform_router::test_the_start_only_prefetch_and_its_serve_compute_one_key_with_preferences_on_record` | 4.5 | 4.5 | kept | its time isn't the wide vault's rollout (another env, or the horizon is a small share) |
| 255 | `test_coordinated_migrations::test_f8_only_the_coordinator_and_the_scratch_copy_enter_an_allowance` | 4.5 | 3.9 | kept | multi-process migration |
| 256 | `test_ih2_offer_ceiling_and_unseen::test_the_ceiling_still_binds_on_seen_offers_at_a_boundary_with_none_open` | 4.5 | 2.1 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 257 | `test_sketch_verify::test_a_follows_claim_past_the_cap_is_stopped_where_the_cap_is` | 4.5 | 4.5 | kept | the sandbox's output budget at the point cap: the size is the claim, and a sandbox guard belongs in every landing |
| 258 | `test_mobile_v2_checks::test_j6_the_check_waits_for_the_desktop_is_recorded_once_and_never_redrawn` | 4.5 | 2.1 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 259 | `test_rospeed2_connections::test_the_job_opens_a_handful_of_connections` | 4.5 | 2.2 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 260 | `test_mvp011_upgrade::test_existing_vaults_keep_their_version_until_the_owner_upgrades` | 4.4 | 4.1 | kept | under 10 s, one case; no repeated structure to shrink |
| 261 | `test_ih2_lessons_compete::test_a_phone_follow_up_stays_forced_beside_an_open_desktop_offer` | 4.4 | 1.8 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 262 | `test_mobile_v2_plan::test_j1_the_phone_never_gets_a_held_item_and_the_desktop_serves_it_next` | 4.4 | 4.3 | kept | phone-host journey |
| 263 | `test_instruct_handoff_ih0::test_the_prefetch_writes_nothing_and_returns_no_step` | 4.4 | 4.4 | kept | phone-host journey over the real host (end-to-end shaped) |
| 264 | `test_ih6_workbench_open_item::test_off_or_below_the_tag_a_read_is_the_predecessors_exactly[switch_off]` | 4.4 | 1.9 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 265 | `test_instruct_handoff_ih0::test_the_call_returns_while_the_model_is_out_and_the_serve_waits_for_that_answer` | 4.4 | 4.5 | kept | phone-host journey over the real host (end-to-end shaped) |
| 266 | `test_plan_determinism::test_with_the_switch_off_a_contrast_pair_follows_the_session_again` | 4.4 | 4.1 | kept | replay-shaped: the same plan in every session |
| 267 | `test_ih4_preferences_inform_router::test_at_w_pref_zero_only_the_acceptance_channel_moves_a_lesson_offers_value` | 4.4 | 1.8 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 268 | `test_ih6_workbench_open_item::test_off_or_below_the_tag_a_read_is_the_predecessors_exactly[below_the_tag]` | 4.4 | 1.9 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 269 | `test_roles_concurrency::test_a_review_between_a_judges_read_and_its_write_stands` | 4.4 | 4.1 | kept | under 10 s, one case; no repeated structure to shrink |
| 270 | `test_facet_authority::test_every_writer_of_facet_meaning_goes_through_the_authority_chokepoint` | 4.4 | 4.8 | kept | under 10 s, one case; no repeated structure to shrink |
| 271 | `test_rw2c_fix_round2::test_fr2_3_with_every_switch_off_a_problem_with_rw2c_history_restores_the_base_payload` | 4.4 | 3.7 | kept | under 10 s, one case; no repeated structure to shrink |
| 272 | `test_ro4_trace_report::test_the_first_day_report_against_the_predecessor_on_a_synthetic_vault` | 4.4 | 2.7 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 273 | `test_ih3_phone_host::test_a_question_in_progress_is_in_the_reply_the_phone_reads` | 4.3 | 4.4 | kept | its time isn't the wide vault's rollout (another env, or the horizon is a small share) |
| 274 | `test_host_queue_revision::test_an_owed_bump_belongs_to_its_vault` | 4.3 | 4.2 | kept | phone-host queue journey |
| 275 | `test_ro5_landing::test_r5_3_how_was_this_chosen_is_plain_words_with_no_stage_names_or_symbols[ro4]` | 4.3 | 1.9 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 276 | `test_ih_numeric_seed::test_the_need_paths_decision_with_no_lesson_seeds_from_its_identity` | 4.3 | 1.7 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 277 | `test_ih6_workbench_open_item::test_closing_the_workbench_lets_the_next_prefetch_start_the_job` | 4.3 | 4.2 | kept | its time isn't the wide vault's rollout (another env, or the horizon is a small share) |
| 278 | `test_ad23_successor::test_the_upgrade_takes_the_predecessor_or_the_chain_and_refuses_the_rest` | 4.2 | 3.9 | kept | under 10 s, one case; no repeated structure to shrink |
| 279 | `test_rospeed2_connections::test_switched_off_the_job_opens_a_connection_at_every_connect` | 4.2 | 2.2 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 280 | `test_pf_generation::test_publish_cap_holds_per_utc_day_and_the_backlog_publishes_next_day` | 4.2 | 3.3 | kept | practice-family generation with fakes |
| 281 | `test_pf_generation::test_owner_seed_item_creates_an_authored_family_first` | 4.2 | 3.0 | kept | practice-family generation with fakes |
| 282 | `test_architecture::test_function_local_domain_imports_match_the_frozen_edge_inventory` | 4.2 | 3.7 | kept | static architecture scans over src |
| 283 | `test_desktop_activation_audit::test_every_desktop_source_has_activation_evidence` | 4.2 | 4.2 | kept | vault-wide audit scan |
| 284 | `test_ro6_landing::test_r12_with_the_carried_evaluation_blocked_the_choosers_wait_returns` | 4.2 | 2.1 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 285 | `test_facet_identity::test_dedupe_regression_set_merges_the_agreed_pairs_and_keeps_the_distinct_ones` | 4.2 | 4.1 | kept | under 10 s, one case; no repeated structure to shrink |
| 286 | `test_ro5_codex_review::test_f1_a_held_grade_is_no_check_observation_and_no_completion` | 4.2 | 1.0 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 287 | `test_compare_sources_keep::test_the_pin_catches_a_second_raw_reader` | 4.2 | 2.6 | kept | under 10 s, one case; no repeated structure to shrink |
| 288 | `test_ro5_codex_rereview::test_f10_an_answer_after_the_cutoff_is_not_a_completion_as_of_it` | 4.2 | 2.1 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 289 | `test_ih2_lessons_compete::test_not_now_after_a_miss_goes_back_to_a_new_decision_and_the_block_resumes` | 4.1 | 1.7 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 290 | `test_desktop_activation_audit::test_test_support_is_never_reached_from_the_app_entry` | 4.1 | 4.1 | kept | vault-wide audit scan |
| 291 | `test_instruct_handoff_ih0::test_the_serve_reads_the_job_with_the_plan_view_the_prefetch_computed` | 4.1 | 4.3 | kept | phone-host journey over the real host (end-to-end shaped) |
| 292 | `test_rofu_ad_link::test_the_numeric_policy_reads_ads_own_predictive_only_at_the_tag_with_its_switch[mvp-0.50-True-True]` | 4.1 | 1.8 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 293 | `test_rofu_review_draw::test_the_numeric_policy_draws_consistently_only_at_the_tag_with_its_switch[tag-True-True]` | 4.1 | 1.8 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 294 | `test_host_queue_revision::test_each_committed_phone_mutation_bumps_once_and_is_visible_with_it` | 4.1 | 2.6 | kept | phone-host queue journey |
| 295 | `test_rofu_speed::test_the_numeric_policy_merges_only_at_the_tag_with_its_switch[tag-True-True]` | 4.1 | 1.8 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 296 | `test_mvp016_upgrade::test_upgrade_command_defaults_to_the_latest` | 4.1 | 3.4 | kept | under 10 s, one case; no repeated structure to shrink |
| 297 | `test_rofu_monotone::test_the_numeric_policy_reads_the_monotone_combiner_only_at_the_tag_with_its_switch[mvp-0.50-True-True]` | 4.1 | 1.8 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 298 | `test_pf_generation::test_a_new_round_asks_the_proposers_again_with_its_own_generation_seed` | 4.1 | 3.2 | kept | practice-family generation with fakes |
| 299 | `test_rofu_speed::test_the_numeric_policy_merges_only_at_the_tag_with_its_switch[tag-False-False]` | 4.1 | 1.8 | shrunk | 30-day rollout horizon (`tests/router_mixture_helpers.py`) |
| 300 | `test_recurrence_commands::test_the_upgrade_command_prints_the_advisory_guard_status` | 4.1 | 3.8 | kept | rebuild fixed point and replay |

## The per-step selector

`scripts/affected_tests.py` prints the test files a change is likely to affect, from the import graph, or the single line `tests` when it falls back to the whole suite. Deterministic: the same tree, changed paths and depth give the same list; nothing is imported or run. Rules, in order:

1. **Whole suite** for `tests/conftest.py`, the modules it names in an import (the ones it patches: `db.connection`, `db.copies`, `db.migrate`, `db.repositories`, `db.storage`, `vault.yaml_io`, `ai.providers.codex_lockdown`, their packages), `tests/helpers.py`, `tests/connection_reuse.py`, `pyproject.toml`, `uv.lock`, `.python-version`, `migrations/`, `fixtures/`, and a non-Python file under `src/` with no module in its directory or above it.
2. A changed module: the test files importing it through at most `--depth` other `src` modules (default 1). Test helper modules (`tests/*.py` not named `test_*`) are glue and cost nothing to pass through. Imports are read with `ast`, function-local ones included, plus string constants that name a module (`importlib`, `monkeypatch.setattr("learnloop.x.y", ...)`).
3. A non-Python file under `src/`: a change to the modules in the nearest directory holding any.
4. Anything else: the test files whose text names its path or file name; none is a valid answer (a doc-only change runs no pytest; the vault validators are their own gate step).

**Why a depth and not the whole closure.** Through `db.repositories`, `config` and `tests/helpers.py` nearly every module reaches nearly every test: the full reverse closure of the median `src` module is 70% of the suite's seconds, which is no per-step gate. Over all 1,285 `src` modules, in `9a623e3d9c`'s test seconds:

| Depth | Median test seconds | 75th percentile | 90th percentile | Modules at or under 960 s |
|---:|---:|---:|---:|---:|
| 0 (tests importing it) | 16 | 83 | 551 | 92% |
| **1 (default)** | **865** | 2,404 | 4,015 | 51% |
| 2 | 2,844 | 4,542 | 6,633 | 14% |
| whole closure | 5,524 | 7,646 | 7,648 | 2% |

At `-n 6` the median depth-1 selection is about 2.5 minutes plus collection; a leaf module's is under a minute. A change to `config` or another hub selects about 1,200 files, which is the whole suite in all but name. The selector is a pre-filter: the landing gate runs everything else.

**On this branch's recent commits** (`--files` from each commit, seconds from this branch's landing JUnit):

| Commit | Subject | Files | Selection | Test seconds |
|---|---|---:|---|---:|
| `1fcce2517e` | A6: a per-step test selector from the import graph, and the... | 5 | 3 files | 13.2 |
| `09e09d5133` | A6: split the two long sweeps into shards, every case in exa... | 2 | 3 files | 112.0 |
| `bbda40fc28` | A6: the mixture tests' vaults roll the objective out 30 days... | 6 | 65 files | 985.6 |
| `bcd6ae8eee` | A6: an arc_close marker for the pre-registered sims and the... | 7 | whole suite (pyproject.toml) | 5588.8 |
| `ffa8bcb7b1` | A3 record: what was deleted, how each test was handled, the... | 1 | 0 files | 0 |
| `afedfb0b7a` | A3: references regenerated on the committed source (config f... | 100 | 2 files | 8.9 |
| `7430827a40` | A3: config/schema.py's comments and docstrings say what and... | 1 | 1216 files | 5117.5 |
| `00d1a77885` | A3: one readable file of defaults replaces the 48 frozen dig... | 64 | whole suite (tests/helpers.py) | 5588.8 |
| `9ce90f7e96` | A4: what leaves the computer, rechecked; S0's suite times; w... | 6 | 0 files | 0 |
| `7e7d68c123` | A2: _generated.md regenerated (generated_provenance.py is a... | 1 | 1 files | 8.4 |
| `86b3f47440` | A2 record; generated_provenance lists a dirty input's path w... | 2 | 0 files | 0 |
| `fc29b87ecb` | A2: references regenerated on the committed source (catalog... | 5 | 1 files | 8.4 |
| `f52d13b937` | A2: the head fixture loses its number; tests read MIGRATION_... | 104 | whole suite (fixtures/migration_head/AGENTS.md) | 5588.8 |
| `56e192990b` | Developer Map: the objective is _Ledger.q, not _terms; 48 di... | 1 | 0 files | 0 |
| `7a2b108e16` | Refactor S0: baseline on the landed tip and the map's correc... | 2 | 0 files | 0 |
| `e6023ad7b1` | Refactor strategy: A6, a shorter gate; pre-registered sims r... | 1 | 0 files | 0 |

Run it from bash (zsh doesn't split a variable into words, and an empty list runs the whole suite):

```bash
mapfile -t paths < <(uv run python scripts/affected_tests.py --base main)
[ ${#paths[@]} -gt 0 ] && uv run pytest -m "not arc_close" -n 6 "${paths[@]}"
```

`tests/test_affected_tests.py` pins the fallback, determinism, the depth ordering, the helper pass-through and the name rule.

## Workers

The landing run at `-n 8` reached the scope's 10 GB limit: anonymous memory peaked at **8.49 GB**, the rest was page cache, and the scope used 1.46 GB of swap (`memory.events`: 253,629 `max` events, no OOM kill). So eight workers already use about 1 GB each, and ten would need about 10.6 GB of anonymous memory, over the limit.

**`-n 10`** ran with a watchdog set to stop the scope if anonymous memory passed 9.4 GB. It got to 99% in 9:49 (30,869 of 30,974 tests, none failed), against 12:06 at `-n 8`. Anonymous memory peaked at **9.30 GB**, and the scope's swap reached its **2 GB cap** (2,147,340,288 bytes) with memory at its 10 GB limit (492,497 `max` events, no OOM kill yet). With both limits reached, the next allocation was an OOM kill inside the scope, and swap that full also drives systemd-oomd, which has killed the owner's terminal before. So I stopped it by hand at that point. Its JUnit wasn't written, and the time to 99% is only indicative: another agent's targeted run was beside it.

**`-n 12` was not run.** At about 0.9-1 GB per worker it would need 11-12 GB of anonymous memory, past the 10 GB limit before any page cache.

**Answer: 10 workers do not fit in the 10 GB scope; 8 is the most that does, and with little room** (8.49 GB anonymous, 1.46 GB swapped). Ten would save about 2 minutes but needs a scope of about 12 GB (the machine has 30 GB). That is the owner's call; the scope limits are unchanged here.

## Proof

- **Union check.** `scripts/check_gate_partition.py` on `1fcce2517e`: 31,034 collected = landing 30,974 + arc_close 60, the two disjoint, and no `arc_close` test without `slow`. PARTITION2
- **No assertion removed.** `git diff 9a623e3d9c -- tests` removes one assert line, `assert len(methods) > 300` in P1, which became `assert len(every) > 300` when the methods were sharded. Every edited test file:
  - `tests/conftest.py`: the `pytest_itemcollected` hook.
  - `tests/router_mixture_helpers.py`: `HORIZON_DAYS`, `served_horizon`, `_with_horizon`.
  - `tests/test_ad23_sim.py`, `test_evsi_multisim.py`, `test_rofu_weeks.py`, `test_ro6_tail_data.py`, `test_ro5_calibration.py`: `slow` became `arc_close`.
  - `tests/test_ih2_lessons_compete.py`, `test_ih4_preferences_inform_router.py`, `test_ro5_landing.py`, `test_ro6_codex_rereview.py`, `test_rofu_learning.py`: `served_horizon` on the eight tests above.
  - `tests/test_cli_help_snapshot.py`, `test_plan_first_transport_offer_grants.py`: the shards.
  - `tests/test_codex_lockdown_round3.py`: the two new scripts' `subprocess.run` sites, reviewed (read-only `git`, and `pytest --collect-only`).
  - `tests/test_affected_tests.py`: new.
- **The landing gate's time** before and after: above.
- **The arc-close lane passes** on `1fcce2517e`: 24 passed, 36 strict xfails as pre-registered.
- **Targeted:** the 65 mixture-env files plus every edited file, 1,076 passed and 3 skipped at `-n 6` (one failure in the new selector test, fixed before the full runs); the guard files that scan `scripts/` (`test_codex_lockdown_round3`, `test_public_tip_guards`, `test_sqlite_file_copies`, `test_refactor_measures`, `test_coordinated_migrations`, `test_architecture`, `test_s0_landing`) 110 passed; `validate_vault.py` passes.
