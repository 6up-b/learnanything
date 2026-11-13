# Refactor D2b (part 2a): the plan and placement test vaults move to the head

Step D2b part 2a of arc D (`docs/specs/refactor_strategy_v3.md` §2.6), on branch `refactor/d2b2-plan-vault-head`, based on main `16a9e3fd48` (K3.5 and D2b part 1 landed). Part 1 (`docs/reviews/refactor-d2b.md` §5) tried `create_daily_plan_vault` at the head, measured 29 failures in 11 files and reverted it; this part reads each one.

Rules held: no change under `src/`; no live model call; no migration; no identity pin moved (`tests/test_identity_pins.py` passes unchanged); no assertion edited to what the code says without reading why (each difference below says why); no test deleted; no test pinned to an old tag. The default tag is `LATEST_ALGORITHM_VERSION` (no tag literal), so the builders follow the head when a successor lands.

## 1. Summary

| | count |
|---|---|
| `create_daily_plan_vault` default | `mvp-0.14` → the head (61 call sites name no version, plus `daily_plan_build_helpers._wide_vault`'s pass-through; 63 files call the builder) |
| `create_placement_vault` default | `mvp-0.11` → the head (1 call site names no version: `test_slate_record._setup`, 9 tests, all passing unchanged at the head) |
| failing at the head, first measure (the 63 builder files and `test_slate_record`) | 27 tests in 9 files; 24 fail every time (3 reruns), the rest at random |
| failing at the head, second measure (the first 100 of the 203 further test files that import, at any depth, a helper module calling the builder; the rest ran in the landing selection) | 5 tests in 3 files (2 deterministic, 3 random); repeated runs of the 7 `plan_world` files then showed 6 more random ones |
| ported (same behaviour asserted on the head path) | 3 tests (5 with parameters) |
| RO5's randomized check taken at its declared zero (`check_rate = "off"`, which serves the predecessor exactly) | 21 tests, one of them also ported (+1 passing sibling parameter sharing its helper) |
| the mix's draw pinned (no drawn stop or lesson offer, stop coin at zero) | 9 test functions, 11 with parameters (every reading test of `test_daily_plan_reading` and `test_mobile_v4_plan`; 2 of them also ported) |
| the phone-host fixture `plan_world` on the router's staged frame | 72 tests in 7 files (the fixture's default; 9 had failed at random over 11 runs) |
| moved behind a kill switch | 1 test (2 parameters): `test_learner_pick_proposal::test_the_delivery_carries_r1s_decision_of_the_block_that_served_it`, `router.enabled` |
| pinned to an old tag | 0 |
| deleted | 0 |
| findings (strict xfail, ledger) | 1 (D-17) |

D2b part 1 listed 29 failures; the first measure here found 27. The difference is random ones (`test_mobile_two_process`, two of `test_daily_plan_reading`), which depend on the mix's draws.

## 2. Why the head differs

The 21 deterministic failures of the first measure were run at every tag from `mvp-0.14` to the head (`create_daily_plan_vault`'s default overridden through a scratch environment variable, never committed): all pass through `mvp-0.20`; `test_daily_plan_build::test_project_probes_stay_outside_the_new_item_cap` fails from `mvp-0.21` (VOI stopping); the other 20 fail from `mvp-0.48` (`ROUTER_CALIBRATION`, RO5's arms). At the head with only `[router_objective] check_rate = "off"` added, all 20 pass. So one cause covers 20 of them:

**RO5's randomized cold check** (`router_objective/checks.py`, from `mvp-0.48`, on by default as `check_rate = "embedded"`). At the day's first boundary the frame administers a seeded cold check (the seed is the date) of an unseen, unrevealed, unassisted item of a valued topic, as its own block placed by the rules before that boundary's decision, with origin `randomized_check`, outside the mix. It is designed to be outside lanes, re-entry limits and new-material admission (`PlanConfig.new_admission_enabled`: "learner requests and scheduled checks still serve"), and a check carries no "why" for the learner. In these tests that block is the plan's first: `(block,) = record.blocks` finds two, the chooser under test is never called at the first boundary, a stop drawn by a fake router leaves the plan open, the never-attempted sibling the test keeps out of re-entry is planned as the check, and the cold retry or computed why the test reads is behind it. None of these tests is about the check; each takes the arm at its declared zero through `helpers.RANDOMIZED_CHECKS_OFF`, the fragment `[router_objective] check_rate = "off"`, with a comment saying what the check would do in it. The check itself is tested at the head in `test_ro5_*`. These tests pass a fake chooser or DL1's pair through `make_env`, yet the check still acts: it is gated on `[router_objective]` alone, which led to finding D-17 (§5).

The rest:

- **VOI stopping** (`mvp-0.21`): due project probes are valued by information, with no count cap. The test's fake probes carried no `probe_eig_total`, so the head admitted none.
- **The objective decides one block at a time, and its mix draws** (`mvp-0.47`, `mvp-0.48`). At `mvp-0.14` the plan built every block up front; at the head each boundary draws from the mix, seeded on fresh decision ids, and its support holds `stop_for_today` (the exploration floor `router.epsilon_min` gives it a share at every boundary) and lesson offers. The reading tests skip items until the reading block comes; at the head the draw sometimes stops or offers a lesson first (1 run in 5 locally for one desktop test, most runs for the phone's). Ending a reading block also crosses a boundary, which at the head may decide the next block at once.
- **The phone-host journeys** (`mobile_v2_plan_helpers.plan_world`, 7 files): bisected over tags with three runs each, they pass at `mvp-0.44` and `mvp-0.46` and fail at random from `mvp-0.47` (the objective). The plan ended early or took another order, and the stop that `mobile_v2_review_fixes_helpers._stop_past_held_work` forces at `engine.decide` was sometimes not the stop a boundary recorded (a staged stop with no candidates instead), or no boundary past held work was crossed and the test skipped itself. The objective also reaches `engine.decide` from the phone's boundary prefetch (`engine.prefetch_boundary`, a read-only job), and its rollouts' draw count follows a deadline, so its choices depend on timing as well as seeds; I read this path but did not trace a failing run end to end. Taking the stop coin and `router.epsilon_min` to zero did not settle it (4 of 6 runs of the 7 files still failed one test).
- **DL1's chooser pair inside the plan** (`test_learner_pick_proposal`): the helper says its vault "is at mvp-0.14, where the plan's pool keeps the scheduler's seeded draw". From `mvp-0.23` the staged frame's pool ignores that draw (the promoted case fails), and from `mvp-0.44` the greedy block's propensity is no longer 1; at the head the objective plans one block at a time, so the pick is never inside the plan.

## 3. Every test touched

"Arm" = `RANDOMIZED_CHECKS_OFF` (§2). "Draw" = `tests/ih2_lessons_compete_helpers.draw` with `never_stop` and `avoid = ("lesson_offer:",)` plus `QUIET` (`stop_coin = 0.0`): a drawn stop or offer is redirected to another option in the support, with its exact propensity; every other draw is the real one.

| test | head difference (read) | action |
|---|---|---|
| test_block_chooser_interface::test_every_decision_is_logged_with_its_candidate_set | the check's block is the plan's first, so there are two blocks | arm |
| test_daily_plan_build::test_project_probes_stay_outside_the_new_item_cap | VOI stopping: no count cap, and probes with no information are never admitted | port (§4) and arm |
| test_daily_plan_build::test_a_3_5_minute_item_is_served_with_4_minutes_left | the check's block comes first and takes minutes off the four | arm |
| test_daily_plan_build::test_a_learner_pick_is_logged_without_propensity_and_displaces_the_tail | the build plans only the check (3.5 minutes), so there is no tail to displace | arm |
| test_daily_plan_kill_switch::test_plan_on_router_on_keeps_the_containers_invariants | the check's block is a routed block that is neither the model's nor a fallback | arm |
| test_daily_plan_owner_decisions::test_reentry_stays_short_and_keep_going_leads_with_new_material[extension] (and [remaining-minutes], through `_reentry_env`, which only this test uses) | the check in the re-entry changes the minutes it spends, so keep going's kind | arm |
| test_daily_plan_owner_decisions::test_router_r1_logs_plan_block_decisions_through_the_boundary_hook | the check's block is first and logs no plan-block decision | arm |
| test_daily_plan_review_regressions::test_f1_reentry_never_plans_an_unseen_sibling_of_an_old_error, ::test_f1_an_open_diagnosis_repairs_the_failed_item_and_the_unseen_one_is_new, ::test_f1_admission_off_serves_no_never_attempted_item (through `_failed_and_unseen`, whose three users these are) | with no goals `lo_err` is the only valued topic, so the check is `pi_unseen`, the item under test: planned in re-entry, planned without new admission, and served with admission off | arm |
| test_daily_plan_review_regressions::test_f3_plan_reads_never_call_the_live_chooser | the first step makes no chooser decision (the check is first) | arm |
| test_daily_plan_review_regressions::test_f4_followups_keep_a_reentry_plan_within_its_item_cap_and_lanes, ::test_f4_a_followup_that_cannot_fit_is_declined_not_appended | the check (one of the never-answered items) is the first block, so the plan the follow-ups arrive in is another | arm |
| test_daily_plan_review_regressions::test_f6_a_router_stop_keeps_its_propensity_and_candidates, ::test_f7_malformed_choices_fall_back_and_are_flagged (via `_small_plan_env(plan_toml=)`, a new keyword; its two other users are unchanged) | the check's block is placed before the fake router's decision: the plan stays open, and `blocks[0]` is the check | arm |
| test_ux_phase4_feedback::test_f1j_a_planned_cold_check_revealed_before_it_is_served_is_not_served, ::test_f1k_a_routine_display_hold_clears_by_itself (via `_plan_with_a_cold_check(plan_toml=)`, a new keyword; the 5 property cases keep the arm on and pass) | the check is `pi_b` (checked), served first, so the control never serves the cold retry and the four steps end before it | arm |
| test_ux_phase4_feedback::test_f1m_a_valid_stop_with_work_feasible_is_kept[verifier], [landing_agent] | the check's block is placed before the stop is drawn, so the plan stays open | arm |
| test_mcp_tools::test_today_shows_the_stored_plan_and_writes_nothing | today's first block is the check, which carries no why | arm |
| test_mcp_c1a_narrow::test_today_and_progress_never_show_a_generated_topic_s_name | today's stored block is the check (one item, one topic), not the maintain block over both topics | arm |
| test_daily_plan_reading: test_a_typed_reading_step…, test_leaving_or_skipping…[left_reader, skipped], test_an_interrupted_block…, test_a_partial_block… (through `reading_vault` and `_reaching_the_reading`) | the mix may draw a stop or a lesson offer before the reading block | draw; and the planned-minutes port (§4) |
| test_mobile_v4_plan: all 6 tests of the `world` fixture | the same, on the phone's plan and the desktop's (a lesson offer on the phone is held for the desktop, a step with no item to skip) | draw; and the planned-minutes port (§4) |
| `mobile_v2_plan_helpers.plan_world` (72 tests: test_mobile_v2_plan, _landing_fixes, _review_fixes, _rereview_fixes, test_mobile_v3_carried, _codex_review, _probes). Seen failing at random: test_mobile_v2_review_fixes::test_f4_a_stop_drawn_past_held_work…, ::test_f6_nothing_changes_for_a_step_whose_session_stayed; test_mobile_v2_rereview_fixes::test_f7_the_stop_drawn_past_held_work_is_offered_on_the_phone, ::test_f7_keep_going_overrides…, ::test_f7_done_for_today…; test_mobile_v2_landing_fixes::test_r3_a_refused_keep_going_leaves_no_override_receipt; test_mobile_v2_plan::test_j5_the_plan_ends_and_the_phone_stops_or_keeps_going, ::test_a_none_origin_never_enters_the_device_branch; test_mobile_v2_review_fixes::test_f4_the_pending_stop_lapses… (at `mvp-0.48` in the bisection) | the objective's choices depend on seeds and timing (§2), and these journeys need a definite order and the forced stop | the fixture's default `plan_toml` is `STAGED_ROUTER` (`[router] mode = "staged"`): the head's staged frame, router on, the objective's failure fallback, which decides inline. The tests are about the device's side (what it serves, holds, stops and hands back); the objective on the phone is `test_ih3_phone_host`'s. 6 of 6 runs of the 7 files green after |
| test_learner_pick_proposal::test_the_delivery_carries_r1s_decision_of_the_block_that_served_it[None, pi_svd_define_001] | its two branches are DL1's chooser pair building the plan up front from the scheduler's pool (§2) | switch: `router.enabled = false` (D7), plus the arm at zero, because the check still acts with the router off (D-17). The delivery's contract on the head is the file's next test, which passes there |

`test_slate_record` (the placement default): 9 passed at the head unchanged. Its assertions are not vacuous there (a retired item excluded and counted, the placement check's `out_of_timing` exclusion named, the CLI `why`).

## 4. Every changed assertion and why

1. **`test_daily_plan_build::test_project_probes_stay_outside_the_new_item_cap`**. Old: exactly `pi_probe_0..3` planned (the count cap of 4). New: the probes carry `probe_eig_total=0.2` (as `voi_stopping_helpers._probe_items` does), and exactly the probes the plan's value admission put in the maintain lane (`record.split["pool"]`) are planned, all maintain, none new-admitted; `admitted == ["pi_eig_easy"]` is unchanged. The subject (project probes stay outside the new-item cap) is asserted as before. From `mvp-0.21` the count cap is gone (`classify_pool`'s docstring: "With it there is no count cap: exactly the admitted probes take the maintain lane"); `test_voi_stopping::test_the_plan_values_project_probes_at_the_successor_and_counts_them_below` pins that 5 are admitted at the successor. At `mvp-0.14` the same assertions hold (the pool holds the 4 capped probes).
2. **`test_daily_plan_reading::test_leaving_or_skipping_ends_the_block_and_counts_its_estimate` and `test_mobile_v4_plan::test_the_phones_plan_reading_ended_is_the_desktops`**. Old: the plan's total planned minutes are equal before and after ending the reading. New: the minutes of the blocks the plan held before are equal (`daily_plan_reading_helpers._planned_minutes_of`). Ending a block crosses a boundary, and at the head the boundary decides the next block at once, which adds its own minutes (seen: 27.5 against 20.5, one block of two 3.5-minute items). What the assertion checked, that an ended reading keeps its estimate charged, is checked on the same blocks. At `mvp-0.14` the plan was built up front, so the two readings agree.

No other assertion changed: every other edit adds a config fragment, the draw pin or the switch, with a comment.

## 5. Findings

1. **D-17: RO5's randomized check acts with the router's kill switch off** (`test_daily_plan_kill_switch::test_router_off_places_no_randomized_check`, strict xfail, named `D2b2 finding`). `router.enabled` is documented as the router's kill switch, off serving "exactly as the predecessor" (`daily_plan/policy.py`: "DL1's pair exactly"). But `router_objective_switches.check_mode` gates the check on `objective_on` (the tag and `[router_objective] enabled`), not on the objective serving (`daily_plan.policy.objective_active`, which also needs the router on in mixture mode), so `engine._randomized_check_block` still places a check block ahead of DL1's first decision. The test builds Today through `policy_for` twice: with the router on a check is placed (passes), with it off the plan is DL1's pair (passes) and still holds the check (fails). Serving-only; no persisted meaning, but every check placed so is a randomized-check assignment and a sensor record written while the router was meant to be off. Ledger row D-17, a small fix due at arc D's close.

Facts recorded for the owner, not xfailed:

- **RO5's randomized check plans a never-attempted item into a re-entry plan, and serves one with `plan.new_admission_enabled = false`.** Both are by design as written (the check is a scheduled check placed by its own rule; the switch's comment says scheduled checks still serve), but they meet two rules the DL1 tests pinned ("re-entry stays short: nothing new", "admission off admits no system-chosen new material"). If the check should respect re-entry or the admission switch, that is a decision, not a test fix.
- **The objective's boundary choices depend on timing as well as seeds** (§2, the phone journeys). Not called a defect: the rollouts' deadline is designed. It means a head-path test that needs a definite block order uses the staged frame or a pinned draw.

## 6. Helper changes

- `tests/helpers.py`: `create_daily_plan_vault(version=LATEST_ALGORITHM_VERSION)` and `create_placement_vault(version=LATEST_ALGORITHM_VERSION)`; `RANDOMIZED_CHECKS_OFF`, the arm-at-zero fragment, with its reason.
- `tests/daily_plan_reading_helpers.py`: `_planned_minutes_of(plan, before)`.
- `tests/mobile_v2_plan_helpers.py`: `STAGED_ROUTER`, `plan_world`'s default fragment, with its reason; `plan_world` takes another fragment by indirect parametrization.
- Test-local helpers gained a `plan_toml` keyword (`test_daily_plan_review_regressions._small_plan_env`, `test_ux_phase4_feedback._plan_with_a_cold_check`); `_failed_and_unseen` and `_reentry_env` always add the fragment (all their users needed it).
- `tests/test_daily_plan_reading.py` and `tests/test_mobile_v4_plan.py` import `draw` and `QUIET` from `tests/ih2_lessons_compete_helpers.py` (the existing pin, as `test_ih3_phone_host` and `test_why_reader` do).
- Vault: `Architecture/Testing and Invariants.md` states that the plan builders are at the head and how a test takes an arm at zero, pins a draw or uses the staged frame.

Five exact-string replacements in `test_daily_plan_kill_switch.py` and `test_block_chooser_interface.py` were applied by a small script (each asserted to match once); the rest with the Edit tool.

## 7. Gates run

- Landing selection, `flock /tmp/learnloop-fullsuite.lock`, 10 GB scope, `-n 8 --dist worksteal -m "not arc_close" -p no:cacheprovider`, empty-home wrapper, on `7b28816b1b` (every test change; the later commits are generated notes and this record): **30,799 passed, 104 skipped, 17 xfailed, 0 failed**, 892.8 s (D2b part 1's 16 xfails plus D-17). One of the two allowed landing runs used.
- Before it, targeted: the 63 builder files and `test_slate_record` at the head (first measure, then 3 reruns of the failures and 3 runs of the edited files); the 21 deterministic failures at every tag from `mvp-0.14` to the head; the first 100 of the 203 transitive importers of the builder's helper modules at `-n 4` behind the lock (1,732 passed, 5 failed: the 5 of §1's second measure; the other 103 ran only in the landing selection); 6 runs of the two reading files after the draw pin (13 passed each); 6 runs of the 7 `plan_world` files on the staged frame (72 passed each, none skipped); 11 runs of `test_mobile_two_process::test_the_phone_and_the_desktop_take_turns_on_one_plan` (all passed); the edited files with `test_identity_pins`, `test_retired_config_identities`, `test_architecture`, `test_test_layout`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_vault_template` and the `plan_world` files: 658 passed, 3 skipped, 1 xfailed. No identity pin moved.
- `scripts/affected_tests.py --base 16a9e3fd48`: the full suite (`tests/helpers.py` changed), so the landing selection is the affected set.
- Arc-close lane: not run; no `arc_close` test was touched (grep of the changed test files for the marker).
- `ruff check`: clean. `lint-imports --no-cache`: 42 kept, 0 broken. `scripts/check_gate_partition.py`: 30,980 collected, landing 30,920 + arc_close 60.
- Vault: the Testing note states the head plan builders and how a test handles the arms and the draws (`d0a977a908`). References regenerated once after the test commits (`_scripts/generate_all.py`: 7 generated notes changed, the test lists of `daily_plan/_package`, `engine`, `policy`, `db/repositories`, `vault/_package`, `vault/loader`, plus `_generated.md`'s rows), committed as `eecf145b8e`; a second run on the clean tree changed nothing (a fixed point). The four validators pass: `db_validate_reference.py`, `module_validate.py`, `desktop_validate.py`, `validate_vault.py`.
- Not run (the orchestrator's): the durability lane, `--fresh-connections`, vitest.

## 8. Open items

For **D7** (switch and arm removals): the 21 arm tests and `RANDOMIZED_CHECKS_OFF` depend on `check_rate = "off"` serving the predecessor; if RO5's check becomes unconditional, these tests need the check's block accounted for instead. `test_learner_pick_proposal::test_the_delivery_carries_r1s_decision…` goes with `router.enabled`. `plan_world`'s 72 tests run on `router.mode = "staged"`: if D7 makes the staged frame unreachable as a mode (it stays as the failure fallback), they need a deterministic way onto the objective's path (a pinned runtime and draw, as `router_mixture_helpers.mixture_env` does).

For **D1**: nothing new. These builders no longer hold the floor back; callers that pass an explicit old tag (24 files pass `version=` to `create_daily_plan_vault`, 56 other files call `create_placement_vault`, mostly with explicit tags in successor and upgrade tests) are D2b part 2's single-file batch.

For **D3**: nothing new.

For the **RO5 seeded-arm sweep** (ledger D-14, `learnanything-dfd`): this step touched `tests/test_daily_plan_reading.py`, `tests/test_mobile_v4_plan.py` (the mix's stop and offer draws, fixture-level pin), `tests/mobile_v2_plan_helpers.py` (the staged default) and the 9 files of §3 for the check arm. `test_mobile_v2_*` test files themselves are unchanged. `test_mobile_two_process::test_the_phone_and_the_desktop_take_turns_on_one_plan` (D2b part 1 saw it fail once, at `mvp-0.14`) runs its host in a spawned process; it passed 11 of 11 here and is untouched.

For the **fix of D-17**: when `check_mode` reads the objective serving, `test_learner_pick_proposal`'s extra `RANDOMIZED_CHECKS_OFF` can go and the xfail turns green.

For the **owner**: §5's first fact (the check against re-entry and the admission switch).
