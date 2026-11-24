# Refactor D2b (fourth pass): the tests that still name old tags

Step D2b's fourth pass, on branch `refactor/d2b-fourth-pass`, based on `b20394c179` (floor `mvp-0.58`, head `mvp-0.68`). The third pass's record is `docs/reviews/refactor-d2b5.md`; its count of what was left (2,043 cases) and its "kept, and why" classes are this pass's starting point. Tests and test helpers only: nothing under `src/` changed, no migration, tag or config change, no test deleted, no test function renamed, no golden regenerated, no assertion changed. The tests that other work owns were not touched: `tests/test_reader_rd*`, `tests/test_notebook_*`, `tests/test_menu_*`, `tests/test_pad_*`, the ink tests and every file added since `mvp-0.67` (commit `1af1ab2a5e`, 30 files).

## 1. Summary

| | before | after |
|---|---|---|
| test cases that write or open a vault at a tag below the head (census over 633 candidate files, then a record-only re-run of the 187 files that import a changed module) | 2,071 in 261 files | 1,705 in 224 files |
| in a successor, upgrade, migration or golden file (a) | 540 | 540 |
| fail at the head when the tag is taken there (a) | 526 | 526 |
| tag-parametrized arms (a) | 325 | 327 (2 arms of `test_rofu_ad_link`, outside the first census, §2) |
| the test's name names the tag, a predecessor or a switch (a) | 106 | 83 |
| built by a helper or constant whose name is the tag or the predecessor (a) | 60 | 60 |
| compare tags in one body, run a switch-off arm beside the successor, or a tag arm without the tag in its id (a) | 32 (9 of them built through `teacher_fakes` by local builders whose own default was the tag: read and moved) | 23 |
| the learner-gap builders' own tag reader (a; third pass §2) | 7 | 7 |
| open a vault whose tag is written by hand (a hand-written config, a copied fixture): not sorted (c) | 84 | 84 |
| pass at the head, nothing names the tag | 390 | **54** (c), §4 |
| skipped in the run (c) | 1 | 1 |
| moved to the head by this pass | | **368 cases** in 84 files (336 unnamed, 23 named for a switch but setting it themselves, 9 of the row above) |
| static uses of an old tag string or old `*_ALGORITHM_VERSION` name in `tests/*.py` (comments and docstrings excluded) | 1,537 in 335 files | 1,452 in 315 files |
| assertions changed | | 0 |
| ledger rows | | 0 |

The before census counts 2,071, not the third pass's 2,043: tests landed since then (D7, K-arc steps) and `set_config`-written vaults are now sorted (§2). Every moved case passed in a plain run at the head: the after re-run had 3,045 passed, 12 skipped and 1 failure (an edit error, fixed: §3, §8).

## 2. Method

The third pass's method (static scan, census and experiment through a scratch pytest plugin, sort, edit by helper, plain run at the head), with two changes:

- **`set_config` is sorted now.** The plugin also swaps `tests.ux_phase1_support.set_config`: with the experiment on, an `("algorithms", "algorithm_version")` value below the head is written as the head. This sorts the 247 cases the third pass left as "written another way"; `reader_followups_helpers._seeded` (130) was the largest. What is still unsorted (84) opens a vault whose tag sits in a hand-written `learnloop.toml` or a copied fixture.
- **Where the tag is chosen.** For each tag the plugin saw written, a scratch script walks the recorded frames outward from the writer: on each frame's line it finds the call into the next frame's function and the argument that carries the tag. While that argument is a parameter of the enclosing function it goes one frame further out; when the call passes none, the tag is the callee's default. This gives each old tag one origin: a literal at a call, a builder's default or a module constant. An origin all of whose cases passed under the experiment is a move candidate. An origin shared with failing cases is moved only by making the builder's default the head and writing the old tag at the failing callers.

Sort, per case: a successor, upgrade, migration or golden file is (a); failing under the experiment is (a); a case whose parameter id holds a tag is (a); a case whose name names the tag, a predecessor, a switch, an upgrade or legacy history is (a). Otherwise it is a candidate, and it was read before it moved. Read and kept as (a): builders and constants named for the tag or the predecessor (`_mvp010`, `_mvp07`, `_mvp06`, `_at_the_tag`, `_tag_env`, `_upgraded`, `BLUEPRINT_OLD_TAG`, `KM2_OLD_TAG`, `PREDECESSOR`, `BEFORE_*`, `OLD`); bodies that compare two tags (`test_voi_stopping::test_a_joint_attempts_lane_is_unchanged`, `test_stuck_prompt`'s `mvp-0.12`/`mvp-0.13` pairs, `test_forecast_receipts::test_f3_...` moving a vault onto the route rules); switch-off arms kept at their tag beside the successor (the D4/D6 rule: `test_voi_stopping`'s VOI-off vault and lane switch, `test_probe_records::test_a_value_stop_omits_the_robust_rule_when_its_gate_is_off`, `test_plan_follows_path`); the tag-armed `test_ro2_ad_document_ir` (ids `fg1_tag`/`ro1_successor`); the seven learner-gap Tier-1 callers (the third pass's limit: `serve_pre_tier1` reads the tag).

Every move was checked by a plain run at the head, not by the experiment: first batch's importers (21 files: 235 passed), second batch's (98 files: 1,536 passed, 3 skipped), then the record-only re-run of the 187 files that import any changed module on the final tree, which also gives the after census (§8). Its single failure was an edit error (a builder with a required `version` keyword lost it, §3); after the fix that file passed (11).

## 3. What moved, and what stayed by name

Every new default is `LATEST_ALGORITHM_VERSION`, never a literal. Edits were made by small scratch scripts: exact-string replacements asserting one occurrence, plus AST-located keyword removals and additions asserting the call is on the named line. Then `ruff check --select F401 --fix` dropped the imports the removed tags left unused. "Named" means a test that fails at the head (or is a switch-off arm), so it keeps its tag, written at its call.

**Commit 1 (`67384ec647`), reader builders written through `set_config`:**

| builder | was | cases moved | named |
|---|---|---|---|
| `reader_followups_helpers._seeded` | `READER_FOLLOWUPS_ALGORITHM_VERSION` (`mvp-0.39`) | 128 (follow-ups and their review rounds, digest narrative, RW6b, router reader activity, blindness relax, chat transport deadline) | `test_reader_followups_successor` (both tests pass `version=TAG`) |
| `reader_ca2_codex_rereview_helpers._steps_sidecar` | `ONE_ASK_ALGORITHM_VERSION` (`mvp-0.35`) | 13 (CA2 re-review, fix orchestrator) | `test_batch3_landing::_workbench_submit_shadow` (fails at the head; passes `version=TAG`). The builder gains a `version` keyword |
| `test_reader_ca2_one_ask._vault`, `._repair_at` | `TAG` (`mvp-0.35`) | 13 | none |

The 19 reader cases whose names say "switched off" or "off" moved with `_seeded`. They set the switch in their own config and pass at the head. They are not predecessor baselines, since nothing in them compares with the earlier tag.

**Commit 2 (`9604fb514e`), `router_mixture_helpers.mixture_env`:** the default goes from `B` (`ROUTER_MIXTURE_ALGORITHM_VERSION`, `mvp-0.24`) to the head: 54 cases moved (the RO0 rows, refusal, forced-withdrawal and decision records, R2b/R2c, teach-back summaries, arc B's close fixes). Thirty calls whose tests fail at the head now pass `version=B` (`test_router_r2b_serving` 15, `test_router_g3_propensity`, `test_router_g7_fallback`, `test_router_r2b_agreement`, `test_router_r2b_requests`, `test_router_r2bc_landing`, `test_router_r2c_retrieval` with `_embedded_env`, `test_ro0_codex_review`, `test_arcb_close_fixes`, `test_refusal_records._router_day`, `test_ux_phase4_landing._r2b_env_with_a_lifting_hold`). `router_g4_restraint_helpers._followup_env` now defaults to `B` (all nine of its default callers fail at the head). `test_ro0_rows9_13_decision_state._plan` passes a `version` through and its five failing tests pass `B`.

**Commit 3 (`811dbc39d0`), grading and diagnosis:** `version=VERSION` (the route rules' `mvp-0.20`) dropped from 11 `split_vault` calls of `test_held_grade_evidence`, 6 of `test_ux_phase4_feedback` and 1 of `test_intent_codex_review`. `forecast_receipts_helpers._diagnosed`'s tags dropped at 4 calls of `test_forecast_receipts` and 3 of `test_ux_phase4_landing`. `reader_guidance_helpers._graded_vault_with_extraction` gains a head default and 6 calls of `test_reader_guidance` drop `mvp-0.10`. Lines lowering a head vault to `mvp-0.8`/`mvp-0.10` now set the head: `test_exam_session` 2, `test_diagnosis_async_router` 1, `test_teach_back` 1. Single calls: `test_lp_claim_fixes_rereview`, `test_stuck_prompt_composition`, and `test_ux_phase4_feedback`'s placement setup (`mvp-0.27`).

**Commit 4 (`8921fe7e2c`), probes and value of information:** `mvp-0.21` and `mvp-0.15` calls of `_probe_vault`/`_long_probe_vault` at the head in `test_voi_stopping` (10 calls; 9 cases moved, the tenth test keeps its VOI-off vault at the tag), `test_voi_v2` (6, and `_gate_vault`'s default; its switch-row parametrization keeps `mvp-0.21`), `test_voi_merge_composition` 4, `test_router_probe_ties` 3, `test_evsi_router_composition` 3 (one docstring no longer says "A mvp-0.15 vault"), `test_router_r1_composition` 2, `test_data_capture_codex_review`, `test_attempt_chain_records`. `mvp-0.7`/`mvp-0.8`/`mvp-0.12`/`mvp-0.22` lines in `test_value_candidates` (its comment now says "past the robust probe cutover"), `test_probe_episodes`, `test_probe_targeting`, `test_instrument_servability_journeys`, `test_reader_rw4b_fix6`, `test_recurrence_deferral`; `test_robust_completion_gate::test_the_gate_does_not_end_a_planted_episode_whose_next_probe_pays` passes the head to `_planted_run` (whose `version` is required; dropping it was the after re-run's one failure). Kept: `test_voi_stopping::test_at_the_successor_...` (names the successor), the lane comparison, the VOI-off and lane-switch arms, the lane-pending matrix with its switch values; `test_robust_completion_gate::test_the_gate_no_longer_reads_...` (its name is the predecessor contrast).

**Commit 5 (`b9c2e72d84`), knowledge-model tests:** `set_algorithm_version(paths, "mvp-0.7")` after a head vault now sets the head in `test_assessment_contracts` (3), `test_generated_item_gate` (2), `test_km4_taxonomy::test_promotion_on_independent_surface`; `test_attempt_completion` and `test_hot_path_eligibility_cutover` build at the head. `_mvp07`, `_mvp06` and every `BLUEPRINT_OLD_TAG`/`KM2_OLD_TAG` use stay (named).

**Commit 6 (`b65dced103`), local builder defaults with named failing callers:**

| builder | was | moved | named (passes the old tag) |
|---|---|---|---|
| `test_lp_claim_fixes._vault` | `TAG` (`CLAIM_FIXES_ALGORITHM_VERSION`) | 7 | the four `defect*_off_*` switch-off tests (one fails at the head) |
| `test_field_workbench_signals._vault` | `TAG` | 7 | the predecessor and off-arm tests and the fast-track one (fails) |
| `test_rebuild_closed_row_answer._with_an_application_item` | `AT` | 11 | `test_an_attempt_applied_at_the_tag_...`; the three failing below-tag/upgrade tests already named their tags |
| `test_data_capture_a6_delayed_pick._vault` | `TAG` | 6 | none |
| `test_teacher_te2_sidecar._ctx` | `TEACHER_PROBES_ALGORITHM_VERSION` | 2 | none |
| `test_router_r2a_serving._rpc_vault` | hard-coded `A` | 4 | its two failing tests pass `version=A` (the builder gains a `version` keyword) |
| `test_reader_rw4b_admission_idempotency._env` | hard-coded `mvp-0.22` | 3 | its failing test passes `version="mvp-0.22"` (the builder gains a `version` keyword) |

Explicit successor tags at calls whose tests pass at the head: `test_untaken_repair_episode` 7 `AT` calls (`BEFORE` stays), `test_same_second_order` 2, `test_ro2_ad_raw_document_reads` 2, `test_ro4_goals`, `test_ro6_codex_review`, `test_ro6_codex_rereview`, `test_rospeed2_connections`, `test_teacher_te1b_suggestions` (its on and off vaults, both at the successor's tag before), `test_curriculum_c1_fix_round2`, `test_curriculum_c0b_landing._with_checks` (its comment no longer says "at the tag"), `test_learner_report_superseded`, `test_intent_fix_round4`, `test_router_r2b_serving::test_the_deciders_route_never_resolves_to_a_chat_model` (`version=B` dropped).

## 4. What stays, by reason

- **(a) successor, upgrade, migration and golden files** (540): the tag is what they compare.
- **(a) fail at the head** (526): the tag is load-bearing (a stamp, a policy version, a predecessor's serving). Sorted by the experiment, not read one by one; each kept case that this pass touched names its tag at the call now.
- **(a) tag-parametrized arms** (327), **named tests** (83), **named builders and constants** (60), **comparisons and switch arms** (23), **the learner-gap reader** (7): §2.
- **(c) not sorted** (84): a hand-written config or a copied tracked fixture holds the tag (the golden-path fixture at `mvp-0.8` and the migration-head fixture at `mvp-0.6` are (a)). The experiment cannot move them.
- **(c) pass at the head, left** (54). By origin: 30 through `daily_plan_build_helpers._wide_vault`'s pass-through `version`, from explicit successor tags in the data-capture, RO4-RO6, R2a/R2c, check-credit, rofu and why-reader files (one to four cases per file; in each of these files most cases fail at the head through the same local wrapper); 24 more in nineteen builders with one or two passing users beside failing ones (`test_router_g1_feasibility._world`, `test_ro1_projection._vault`, `test_plan_determinism._template`/`_pair_template`, `voi_restore_scenarios._gate_probe_vault`, `test_voi_v2._requested_plan`, `test_router_r1_composition._plan_env`, `test_intent_plan._many_checks_vault` and single cases). Each would need a per-caller edit for one or two cases.
- **(a) static uses with no vault behind them**: a stored row's own tag passed to a writer, tag constants and chain positions asserted, upgrade tables, identity pins. The third pass's decision stands.

**Would another pass pay?** No. At most 54 cases (3% of what remains) can still move, and each needs a call-by-call edit in a file where most cases keep their tag for a reason. The 84 unsorted cases need a different tool (rewriting hand-written configs and fixtures), and the third pass ruled the two fixtures (a). Everything else left is (a): the tag is what the test is about.

## 5. Every assertion changed, and why

None. No expected value, comparison or `assert` line was edited. Non-assertion changes beyond the tag arguments: four local builders gained a `version` keyword (`_steps_sidecar`, `_rpc_vault`, `_env`, `test_ro0_rows9_13_decision_state._plan`); `_followup_env` and `reader_guidance_helpers._graded_vault_with_extraction` changed defaults; three docstrings and two comments no longer name a tag the code no longer uses.

## 6. Findings and ledger

No new bug found and no ledger row added. The after re-run's one failure was this pass's own edit error (a dropped required keyword), fixed before the last commit. Not a finding, but for the owner: the 19 reader "switched off" cases and three RO0 "off" cases now run their switch-off arm at the head, not at the successor's tag (§3).

## 7. Every file

"Census cases" are test cases that wrote or opened a vault below the head. "After" is the record-only re-run for the 187 files that import a changed module, and the before count for every other file. "Static uses" are §2's names. Decisions: (a) the tag is the subject, kept; moved = (b); (c) kept, with the reason. `test_rofu_ad_link.py` was outside the first census (the ink-test exclusion glob matched "link"); it entered the re-run by importing a changed helper, and its two cases are tag-parametrized (a). No file of it changed.

| file | census cases before | after | static uses before | after | decision |
|---|---|---|---|---|---|
| `ad23_contract_helpers.py` | 0 | 0 | 6 | 6 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `check_credit_report_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `cli_generate_practice_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `data_capture_a2_measurement_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `diagnosis_journey_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `followup_fg1d_probe_shadow_helpers.py` | 0 | 0 | 4 | 4 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `followup_journey_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `followup_serve_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `followups_nov2_help_fold_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `helpers.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `identity_pins_helpers.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `ih2_lessons_compete_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `km2_write_path_helpers.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `km3_projections_helpers.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `learner_pick_proposal_helpers.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `learner_report_superseded_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `learner_text_gaps_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `lp_claim_fixes_review_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `reader_ca2_codex_rereview_helpers.py` | 0 | 0 | 2 | 0 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `reader_followups_helpers.py` | 0 | 0 | 2 | 0 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `reading_paths_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `regrade_contract_successor_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `regrade_contract_upgrade_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `required_method_grading_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `ro6_codex_review_helpers.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `route_rules_in_grader_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `router_mixture_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `router_outcomes_helpers.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `rw2c_base_sequence.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `serve_eligibility_helpers.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `simulation_helpers.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `source_exercise_rpcs_helpers.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `source_set_synthesis_helpers.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `successor_switches.py` | 0 | 0 | 22 | 22 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_ad23_fix_r5.py` | 1 | 1 | 1 | 1 | 1 fail at the head (a) |
| `test_ad23_migration.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_ad23_owner_decisions.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_ad23_successor.py` | 2 | 2 | 12 | 12 | 2 in a successor/upgrade/migration/golden file (a) |
| `test_ad2_serving.py` | 2 | 2 | 2 | 2 | 2 fail at the head (a) |
| `test_ad3_relatedness.py` | 1 | 1 | 1 | 1 | 1 fail at the head (a) |
| `test_ad_denial_log.py` | 90 | 90 | 0 | 0 | 75 fail at the head (a); 15 tag-parametrized arms (a) |
| `test_ai_config.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_answer_calibration_duel.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_arcb_close_fixes.py` | 5 | 1 | 0 | 0 | moved 4; 1 fail at the head (a) |
| `test_assessment_contracts.py` | 4 | 1 | 4 | 1 | moved 3; 1 name the tag, a predecessor or a switch (a) |
| `test_assessment_enforcement.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_assumed_known.py` | 5 | 5 | 6 | 6 | 4 tag-parametrized arms (a); 1 fail at the head (a) |
| `test_attempt_application_order_migration.py` | 0 | 0 | 4 | 4 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_attempt_chain_records.py` | 1 | 0 | 2 | 1 | moved 1 |
| `test_attempt_completion.py` | 2 | 0 | 1 | 0 | moved 2 |
| `test_attempt_content_state_race.py` | 2 | 2 | 2 | 2 | 2 built by a helper or constant whose name is the tag or the predecessor (a) |
| `test_attempt_content_state_successor.py` | 2 | 2 | 9 | 9 | 2 in a successor/upgrade/migration/golden file (a) |
| `test_attempt_order.py` | 0 | 0 | 7 | 7 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_batch3_landing.py` | 3 | 3 | 41 | 41 | 2 open a vault whose tag is written another way (hand-written config or copied fixture): not sorted (c); 1 fail at the head (a) |
| `test_calibration.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_canonical_projection_rollout.py` | 3 | 3 | 3 | 3 | 2 name the tag, a predecessor or a switch (a); 1 fail at the head (a) |
| `test_causal_activity_policy.py` | 0 | 0 | 3 | 3 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_causal_factor_deferral.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_causal_trace_consistency_p2.py` | 4 | 4 | 7 | 7 | 3 tag-parametrized arms (a); 1 fail at the head (a) |
| `test_certification_cold_probe.py` | 2 | 2 | 1 | 1 | 2 fail at the head (a) |
| `test_characterization_mastery_reliability.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_characterization_probe_regrade.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_chat_total_transport_deadline.py` | 1 | 0 | 0 | 0 | moved 1 |
| `test_check_credit_activation.py` | 5 | 5 | 10 | 10 | 2 fail at the head (a); 2 tag-parametrized arms (a); 1 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_check_credit_characterization.py` | 3 | 3 | 4 | 4 | 2 fail at the head (a); 1 tag-parametrized arms (a) |
| `test_check_credit_report.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_choose.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_cli_attempt.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_cli_fit.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_cold_retry_reschedule.py` | 0 | 0 | 9 | 9 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_cold_start_revision.py` | 0 | 0 | 11 | 11 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_config_refactor.py` | 0 | 0 | 3 | 3 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_contract_commissioning.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_coverage_rollup.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_curriculum_c0b_landing.py` | 2 | 0 | 2 | 0 | moved 2 |
| `test_curriculum_c1_codex_review_fixes.py` | 2 | 2 | 3 | 3 | 1 name the tag, a predecessor or a switch (a); 1 fail at the head (a) |
| `test_curriculum_c1_fix_round2.py` | 2 | 1 | 3 | 2 | moved 1; 1 fail at the head (a) |
| `test_curriculum_c1_landing.py` | 0 | 0 | 9 | 9 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_curriculum_c1_plan_follows_path.py` | 3 | 3 | 40 | 40 | 2 name the tag, a predecessor or a switch (a); 1 built by a helper or constant whose name is the tag or the predecessor (a) |
| `test_curriculum_locks.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_daily_plan_kill_switch.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_data_capture_a1_prefilter.py` | 8 | 8 | 4 | 4 | 5 fail at the head (a); 3 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_data_capture_a2_measurement.py` | 19 | 19 | 2 | 2 | 12 fail at the head (a); 4 pass at the head through a builder whose other users fail there, left unsplit (c); 2 name the tag, a predecessor or a switch (a); 1 skipped in the run (c) |
| `test_data_capture_a4_delayed_completion.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_data_capture_a5_not_ready_floor.py` | 7 | 7 | 2 | 2 | 5 fail at the head (a); 2 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_data_capture_a6_delayed_pick.py` | 6 | 0 | 2 | 2 | moved 6 |
| `test_data_capture_codex_rereview.py` | 23 | 23 | 0 | 0 | 23 fail at the head (a) |
| `test_data_capture_codex_review.py` | 8 | 7 | 2 | 1 | moved 1; 7 fail at the head (a) |
| `test_data_capture_landing_review.py` | 24 | 24 | 0 | 0 | 24 fail at the head (a) |
| `test_data_capture_phone.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_data_capture_report.py` | 3 | 3 | 2 | 2 | 3 fail at the head (a) |
| `test_data_capture_successor.py` | 1 | 1 | 6 | 6 | 1 in a successor/upgrade/migration/golden file (a) |
| `test_decider_landing.py` | 0 | 0 | 4 | 4 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_diagnosis_async_router.py` | 1 | 0 | 1 | 0 | moved 1 |
| `test_diagnosis_journey_golden.py` | 6 | 6 | 0 | 0 | 6 in a successor/upgrade/migration/golden file (a) |
| `test_discriminating_search.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_doctor.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_evidence_reading_successor.py` | 49 | 49 | 6 | 6 | 49 in a successor/upgrade/migration/golden file (a) |
| `test_evsi_router_composition.py` | 5 | 0 | 3 | 0 | moved 5 |
| `test_evsi_staged_binding.py` | 2 | 2 | 2 | 2 | 2 fail at the head (a) |
| `test_exam_protection.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_exam_session.py` | 2 | 0 | 2 | 0 | moved 2 |
| `test_facet_belief_successor.py` | 6 | 6 | 16 | 16 | 6 in a successor/upgrade/migration/golden file (a) |
| `test_facet_belief_successor_derivation.py` | 7 | 7 | 7 | 7 | 7 in a successor/upgrade/migration/golden file (a) |
| `test_facet_state_write_on_change.py` | 0 | 0 | 13 | 13 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_family_memory_projection.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_field_workbench_signals.py` | 13 | 6 | 6 | 6 | moved 7; 3 fail at the head (a); 3 name the tag, a predecessor or a switch (a) |
| `test_figure_wait_estimate.py` | 3 | 3 | 5 | 5 | 2 name the tag, a predecessor or a switch (a); 1 fail at the head (a) |
| `test_figure_wait_successor.py` | 1 | 1 | 16 | 16 | 1 in a successor/upgrade/migration/golden file (a) |
| `test_fitted_parameters.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_followup_fg1d_panel_read.py` | 8 | 8 | 0 | 0 | 8 tag-parametrized arms (a) |
| `test_followup_fg1d_probe_shadow.py` | 12 | 12 | 0 | 0 | 12 tag-parametrized arms (a) |
| `test_followup_generate_e2e.py` | 1 | 1 | 2 | 2 | 1 fail at the head (a) |
| `test_followup_journey.py` | 1 | 1 | 2 | 2 | 1 fail at the head (a) |
| `test_followup_live_shape.py` | 1 | 1 | 1 | 1 | 1 fail at the head (a) |
| `test_followup_reserved_only.py` | 1 | 1 | 1 | 1 | 1 fail at the head (a) |
| `test_followup_rival_factor.py` | 1 | 1 | 1 | 1 | 1 fail at the head (a) |
| `test_followup_successor.py` | 2 | 2 | 6 | 6 | 2 in a successor/upgrade/migration/golden file (a) |
| `test_followup_workflow.py` | 1 | 1 | 1 | 1 | 1 fail at the head (a) |
| `test_followups_batch6_prefetch_decided_once.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_followups_batch6_review_fixes.py` | 2 | 2 | 3 | 3 | 2 fail at the head (a) |
| `test_followups_batch6_router_report.py` | 1 | 1 | 2 | 2 | 1 fail at the head (a) |
| `test_followups_batch6_te1b_card.py` | 3 | 3 | 4 | 4 | 3 fail at the head (a) |
| `test_followups_nov2_help_fold.py` | 6 | 6 | 0 | 0 | 6 open a vault whose tag is written another way (hand-written config or copied fixture): not sorted (c) |
| `test_followups_nov2_note_gap_unlinked.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_forced_withdrawal_records.py` | 6 | 4 | 0 | 0 | moved 2; 4 fail at the head (a) |
| `test_forecast_ledger.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_forecast_receipts.py` | 5 | 1 | 4 | 0 | moved 4; 1 compare tags, run a switch arm or a tag arm (a) |
| `test_generated_item_gate.py` | 2 | 0 | 2 | 0 | moved 2 |
| `test_golden_path_fixture.py` | 4 | 4 | 1 | 1 | 4 in a successor/upgrade/migration/golden file (a) |
| `test_grader_channel_prior_knobs.py` | 0 | 0 | 3 | 3 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_grading_cli.py` | 1 | 1 | 3 | 3 | 1 fail at the head (a) |
| `test_graph_correction.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_held_grade_evidence.py` | 13 | 1 | 0 | 0 | moved 12; 1 open a vault whose tag is written another way (hand-written config or copied fixture): not sorted (c) |
| `test_help_fold_attach_successor.py` | 4 | 4 | 6 | 6 | 4 in a successor/upgrade/migration/golden file (a) |
| `test_hint_feedback_widening.py` | 0 | 0 | 4 | 4 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_hot_path_eligibility_cutover.py` | 2 | 1 | 2 | 1 | moved 1; 1 name the tag, a predecessor or a switch (a) |
| `test_hypothesis_claim_dispatcher.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_hypothesis_marks_context.py` | 1 | 1 | 0 | 0 | 1 fail at the head (a) |
| `test_ih2_lessons_compete.py` | 3 | 3 | 0 | 0 | 3 fail at the head (a) |
| `test_ih2_offer_ceiling_and_unseen.py` | 2 | 2 | 1 | 1 | 1 name the tag, a predecessor or a switch (a); 1 fail at the head (a) |
| `test_ih3_learner_preferences.py` | 2 | 2 | 2 | 2 | 2 fail at the head (a) |
| `test_ih3_migration.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_ih4_preferences_inform_router.py` | 4 | 4 | 2 | 2 | 4 fail at the head (a) |
| `test_ih5_successor.py` | 6 | 6 | 18 | 18 | 6 in a successor/upgrade/migration/golden file (a) |
| `test_ih6_workbench_open_item.py` | 5 | 5 | 2 | 2 | 5 fail at the head (a) |
| `test_ih7_lesson_sources_follow_diagnosis.py` | 3 | 3 | 5 | 5 | 3 fail at the head (a) |
| `test_ih_lesson_candidate_after_cold_miss.py` | 5 | 5 | 3 | 3 | 5 fail at the head (a) |
| `test_instrument_servability_journeys.py` | 1 | 0 | 1 | 0 | moved 1 |
| `test_intent_codex_rereview.py` | 0 | 0 | 5 | 5 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_intent_codex_review.py` | 3 | 2 | 2 | 2 | moved 1; 2 fail at the head (a) |
| `test_intent_fix_round4.py` | 2 | 1 | 4 | 3 | moved 1; 1 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_intent_fix_round6.py` | 1 | 1 | 2 | 2 | 1 fail at the head (a) |
| `test_intent_plan.py` | 2 | 2 | 2 | 2 | 1 fail at the head (a); 1 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_irt_difficulty.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_irt_end_to_end.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_judge_routes.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_k1_remediation_cold_reservation.py` | 1 | 1 | 2 | 2 | 1 fail at the head (a) |
| `test_km1_doctor.py` | 3 | 3 | 3 | 3 | 3 name the tag, a predecessor or a switch (a) |
| `test_km2_canonical.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_km2_write_path.py` | 1 | 1 | 0 | 0 | 1 built by a helper or constant whose name is the tag or the predecessor (a) |
| `test_km3_projections.py` | 4 | 4 | 0 | 0 | 4 built by a helper or constant whose name is the tag or the predecessor (a) |
| `test_km4_taxonomy.py` | 7 | 6 | 3 | 2 | moved 1; 6 built by a helper or constant whose name is the tag or the predecessor (a) |
| `test_large_practice_flow.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_learner_blindness_relax.py` | 2 | 0 | 0 | 0 | moved 2 |
| `test_learner_gap_unlinked_migration.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_learner_note_source_kind_migration.py` | 0 | 0 | 4 | 4 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_learner_pick_proposal.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_learner_report_superseded.py` | 5 | 4 | 44 | 44 | moved 1; 3 fail at the head (a); 1 tag-parametrized arms (a) |
| `test_learner_review_system_entries.py` | 0 | 0 | 8 | 8 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_learner_text_gaps.py` | 4 | 4 | 5 | 5 | 4 the learner-gap builders' own tag reader (a, third pass §2) |
| `test_learner_text_gaps_composition.py` | 1 | 1 | 4 | 4 | 1 name the tag, a predecessor or a switch (a) |
| `test_learner_text_gaps_flow.py` | 2 | 2 | 3 | 3 | 1 name the tag, a predecessor or a switch (a); 1 the learner-gap builders' own tag reader (a, third pass §2) |
| `test_learner_text_gaps_review.py` | 3 | 3 | 5 | 5 | 2 the learner-gap builders' own tag reader (a, third pass §2); 1 name the tag, a predecessor or a switch (a) |
| `test_learner_text_source_widening.py` | 0 | 0 | 4 | 4 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_lp_claim_fixes.py` | 13 | 6 | 6 | 6 | moved 7; 5 name the tag, a predecessor or a switch (a); 1 fail at the head (a) |
| `test_lp_claim_fixes_rereview.py` | 1 | 0 | 1 | 0 | moved 1 |
| `test_lp_claim_fixes_review.py` | 2 | 2 | 3 | 3 | 2 name the tag, a predecessor or a switch (a) |
| `test_map_untested.py` | 3 | 3 | 0 | 0 | 3 built by a helper or constant whose name is the tag or the predecessor (a) |
| `test_mastery.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_mastery_seed_replay.py` | 0 | 0 | 6 | 6 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_mcp_c1a_landing.py` | 1 | 0 | 0 | 0 | moved 1 |
| `test_mcp_runtime.py` | 1 | 1 | 0 | 0 | 1 open a vault whose tag is written another way (hand-written config or copied fixture): not sorted (c) |
| `test_measurement_corrections.py` | 1 | 1 | 5 | 5 | 1 fail at the head (a) |
| `test_method_explicit_landing.py` | 1 | 1 | 5 | 5 | 1 fail at the head (a) |
| `test_mobile_v3_successor.py` | 0 | 0 | 6 | 6 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_mvp017_route_check_replay.py` | 2 | 2 | 2 | 2 | 2 open a vault whose tag is written another way (hand-written config or copied fixture): not sorted (c) |
| `test_p0_projection_cutover.py` | 6 | 6 | 4 | 4 | 3 built by a helper or constant whose name is the tag or the predecessor (a); 2 fail at the head (a); 1 name the tag, a predecessor or a switch (a) |
| `test_pfc_unverified_unassessed.py` | 229 | 229 | 2 | 2 | 228 tag-parametrized arms (a); 1 open a vault whose tag is written another way (hand-written config or copied fixture): not sorted (c) |
| `test_placement_diagnosis_decides.py` | 1 | 1 | 1 | 1 | 1 name the tag, a predecessor or a switch (a) |
| `test_placement_fixture_copies.py` | 0 | 0 | 10 | 10 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_placement_opening_probes.py` | 17 | 17 | 5 | 5 | 11 built by a helper or constant whose name is the tag or the predecessor (a); 4 name the tag, a predecessor or a switch (a); 2 fail at the head (a) |
| `test_placement_unevidenced_return.py` | 15 | 15 | 7 | 7 | 12 built by a helper or constant whose name is the tag or the predecessor (a); 3 name the tag, a predecessor or a switch (a) |
| `test_plan_determinism.py` | 12 | 12 | 2 | 2 | 9 fail at the head (a); 3 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_plan_determinism_landing.py` | 16 | 16 | 3 | 3 | 13 fail at the head (a); 3 name the tag, a predecessor or a switch (a) |
| `test_plan_follows_path.py` | 4 | 4 | 12 | 12 | 2 name the tag, a predecessor or a switch (a); 1 compare tags, run a switch arm or a tag arm (a); 1 fail at the head (a) |
| `test_practice_leakage.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_primed_attempts.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_probe_attempt_updates.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_probe_episodes.py` | 1 | 0 | 1 | 0 | moved 1 |
| `test_probe_migration.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_probe_records.py` | 1 | 1 | 1 | 1 | 1 compare tags, run a switch arm or a tag arm (a) |
| `test_probe_targeting.py` | 1 | 0 | 1 | 0 | moved 1 |
| `test_provenance.py` | 1 | 1 | 2 | 2 | 1 open a vault whose tag is written another way (hand-written config or copied fixture): not sorted (c) |
| `test_reader_ca2_codex_rereview.py` | 5 | 0 | 0 | 0 | moved 5 |
| `test_reader_ca2_fix_orchestrator.py` | 8 | 0 | 0 | 0 | moved 8 |
| `test_reader_ca2_one_ask.py` | 15 | 2 | 6 | 6 | moved 13; 2 fail at the head (a) |
| `test_reader_digest_narrative.py` | 25 | 0 | 0 | 0 | moved 25 |
| `test_reader_followups.py` | 35 | 0 | 0 | 0 | moved 35 |
| `test_reader_followups_rereview.py` | 6 | 0 | 0 | 0 | moved 6 |
| `test_reader_followups_review.py` | 18 | 0 | 0 | 0 | moved 18 |
| `test_reader_followups_round3.py` | 6 | 0 | 0 | 0 | moved 6 |
| `test_reader_followups_round4.py` | 2 | 0 | 0 | 0 | moved 2 |
| `test_reader_followups_round5.py` | 3 | 0 | 0 | 0 | moved 3 |
| `test_reader_followups_round6.py` | 3 | 0 | 0 | 0 | moved 3 |
| `test_reader_followups_round7.py` | 3 | 0 | 0 | 0 | moved 3 |
| `test_reader_followups_round8.py` | 4 | 0 | 0 | 0 | moved 4 |
| `test_reader_followups_successor.py` | 2 | 2 | 6 | 6 | 2 in a successor/upgrade/migration/golden file (a) |
| `test_reader_guidance.py` | 7 | 1 | 7 | 1 | moved 6; 1 tag-parametrized arms (a) |
| `test_reader_recap_review_r2.py` | 1 | 1 | 1 | 1 | 1 tag-parametrized arms (a) |
| `test_reader_recap_review_r3.py` | 5 | 5 | 4 | 4 | 2 tag-parametrized arms (a); 1 name the tag, a predecessor or a switch (a); 1 pass at the head through a builder whose other users fail there, left unsplit (c); 1 built by a helper or constant whose name is the tag or the predecessor (a) |
| `test_reader_rw1b_review.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_reader_rw3a_landing.py` | 3 | 3 | 2 | 2 | 2 fail at the head (a); 1 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_reader_rw4b_admission_idempotency.py` | 5 | 2 | 1 | 1 | moved 3; 2 fail at the head (a) |
| `test_reader_rw4b_fix6.py` | 4 | 3 | 3 | 2 | moved 1; 3 fail at the head (a) |
| `test_reader_rw6b_landing.py` | 5 | 0 | 0 | 0 | moved 5 |
| `test_reader_seen_passages.py` | 1 | 1 | 1 | 1 | 1 fail at the head (a) |
| `test_reading_paths.py` | 2 | 2 | 6 | 6 | 1 name the tag, a predecessor or a switch (a); 1 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_reading_step_switch.py` | 1 | 1 | 5 | 5 | 1 name the tag, a predecessor or a switch (a) |
| `test_rebuild_closed_row_answer.py` | 15 | 4 | 7 | 7 | moved 11; 3 fail at the head (a); 1 name the tag, a predecessor or a switch (a) |
| `test_rebuild_equivalence.py` | 1 | 1 | 2 | 2 | 1 tag-parametrized arms (a) |
| `test_rebuild_equivalence_review.py` | 1 | 1 | 6 | 6 | 1 name the tag, a predecessor or a switch (a) |
| `test_rebuild_history_appends.py` | 5 | 5 | 4 | 4 | 4 fail at the head (a); 1 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_rebuild_orchestrator.py` | 6 | 6 | 0 | 0 | 6 open a vault whose tag is written another way (hand-written config or copied fixture): not sorted (c) |
| `test_recall_calibration.py` | 2 | 2 | 2 | 2 | 2 open a vault whose tag is written another way (hand-written config or copied fixture): not sorted (c) |
| `test_receipt_derivation.py` | 2 | 2 | 1 | 1 | 2 open a vault whose tag is written another way (hand-written config or copied fixture): not sorted (c) |
| `test_receipt_exactness.py` | 2 | 2 | 0 | 0 | 2 tag-parametrized arms (a) |
| `test_recurrence_commands.py` | 13 | 13 | 57 | 57 | 8 built by a helper or constant whose name is the tag or the predecessor (a); 5 name the tag, a predecessor or a switch (a) |
| `test_recurrence_deferral.py` | 3 | 1 | 2 | 1 | moved 2; 1 name the tag, a predecessor or a switch (a) |
| `test_refactor_measures.py` | 0 | 0 | 10 | 10 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_reference_gate_imports.py` | 4 | 4 | 10 | 10 | 3 fail at the head (a); 1 name the tag, a predecessor or a switch (a) |
| `test_refusal_records.py` | 3 | 1 | 0 | 0 | moved 2; 1 fail at the head (a) |
| `test_regrade_contract_successor.py` | 36 | 36 | 4 | 4 | 36 in a successor/upgrade/migration/golden file (a) |
| `test_remaining_decision_records.py` | 2 | 1 | 0 | 0 | moved 1; 1 fail at the head (a) |
| `test_required_method_grading.py` | 2 | 2 | 4 | 4 | 2 name the tag, a predecessor or a switch (a) |
| `test_ro0_codex_review.py` | 5 | 2 | 2 | 2 | moved 3; 2 fail at the head (a) |
| `test_ro0_codex_verify.py` | 16 | 16 | 6 | 6 | 16 tag-parametrized arms (a) |
| `test_ro0_gate.py` | 5 | 4 | 4 | 4 | moved 1; 4 tag-parametrized arms (a) |
| `test_ro0_report.py` | 3 | 0 | 0 | 0 | moved 3 |
| `test_ro0_row10_cold_timing.py` | 3 | 3 | 0 | 0 | 2 pass at the head through a builder whose other users fail there, left unsplit (c); 1 name the tag, a predecessor or a switch (a) |
| `test_ro0_row12_trajectory.py` | 3 | 0 | 0 | 0 | moved 3 |
| `test_ro0_row3_ask_availability.py` | 7 | 0 | 0 | 0 | moved 7 |
| `test_ro0_rows7_8_sessions.py` | 4 | 0 | 0 | 0 | moved 4 |
| `test_ro0_rows9_13_decision_state.py` | 13 | 5 | 0 | 0 | moved 8; 5 fail at the head (a) |
| `test_ro1_availability.py` | 2 | 2 | 2 | 2 | 2 fail at the head (a) |
| `test_ro1_availability_reads.py` | 7 | 7 | 2 | 2 | 6 fail at the head (a); 1 name the tag, a predecessor or a switch (a) |
| `test_ro1_interval_factor.py` | 4 | 4 | 7 | 7 | 3 fail at the head (a); 1 name the tag, a predecessor or a switch (a) |
| `test_ro1_projection.py` | 15 | 15 | 5 | 5 | 11 fail at the head (a); 2 pass at the head through a builder whose other users fail there, left unsplit (c); 1 name the tag, a predecessor or a switch (a); 1 compare tags, run a switch arm or a tag arm (a) |
| `test_ro1_self_report.py` | 1 | 1 | 2 | 2 | 1 fail at the head (a) |
| `test_ro1_successor.py` | 3 | 3 | 7 | 7 | 3 in a successor/upgrade/migration/golden file (a) |
| `test_ro1_upgrade_report.py` | 3 | 3 | 4 | 4 | 3 in a successor/upgrade/migration/golden file (a) |
| `test_ro2_ad_document_ir.py` | 6 | 6 | 2 | 2 | 6 compare tags, run a switch arm or a tag arm (a) |
| `test_ro2_ad_raw_document_reads.py` | 2 | 0 | 3 | 0 | moved 2 |
| `test_ro2_history_protection.py` | 2 | 2 | 2 | 2 | 1 name the tag, a predecessor or a switch (a); 1 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_ro4_codex_review.py` | 2 | 2 | 3 | 3 | 2 fail at the head (a) |
| `test_ro4_goals.py` | 4 | 3 | 8 | 7 | moved 1; 3 fail at the head (a) |
| `test_ro4_objective_serving.py` | 6 | 6 | 4 | 4 | 4 fail at the head (a); 2 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_ro4_successor.py` | 1 | 1 | 7 | 7 | 1 in a successor/upgrade/migration/golden file (a) |
| `test_ro4_trace_report.py` | 1 | 1 | 2 | 2 | 1 name the tag, a predecessor or a switch (a) |
| `test_ro4_traces_migration.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_ro5_landing.py` | 9 | 9 | 6 | 6 | 6 pass at the head through a builder whose other users fail there, left unsplit (c); 2 name the tag, a predecessor or a switch (a); 1 fail at the head (a) |
| `test_ro5_picks.py` | 1 | 1 | 2 | 2 | 1 fail at the head (a) |
| `test_ro5_stop_coin.py` | 1 | 1 | 4 | 4 | 1 fail at the head (a) |
| `test_ro5_successor.py` | 1 | 1 | 7 | 7 | 1 in a successor/upgrade/migration/golden file (a) |
| `test_ro6_codex_rereview.py` | 2 | 1 | 8 | 6 | moved 1; 1 fail at the head (a) |
| `test_ro6_codex_review.py` | 1 | 0 | 2 | 0 | moved 1 |
| `test_ro6_landing.py` | 4 | 4 | 9 | 9 | 3 fail at the head (a); 1 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_ro6_serving.py` | 5 | 5 | 4 | 4 | 2 name the tag, a predecessor or a switch (a); 2 pass at the head through a builder whose other users fail there, left unsplit (c); 1 fail at the head (a) |
| `test_ro6_successor.py` | 1 | 1 | 7 | 7 | 1 in a successor/upgrade/migration/golden file (a) |
| `test_ro6_tail_data.py` | 6 | 6 | 2 | 2 | 3 built by a helper or constant whose name is the tag or the predecessor (a); 1 fail at the head (a); 1 pass at the head through a builder whose other users fail there, left unsplit (c); 1 name the tag, a predecessor or a switch (a) |
| `test_robust_completion_gate.py` | 6 | 5 | 6 | 6 | moved 1; 4 fail at the head (a); 1 compare tags, run a switch arm or a tag arm (a) |
| `test_robust_composition.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_robust_composition_bench.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_robust_selection_twin_candidates.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_rofu_ad_link.py` | 0 | 2 | 3 | 3 | 2 tag-parametrized arms (a) |
| `test_rofu_carried.py` | 1 | 1 | 2 | 2 | 1 fail at the head (a) |
| `test_rofu_generator_switches.py` | 11 | 11 | 4 | 4 | 10 fail at the head (a); 1 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_rofu_learning.py` | 1 | 1 | 2 | 2 | 1 fail at the head (a) |
| `test_rofu_monotone.py` | 2 | 2 | 3 | 3 | 2 tag-parametrized arms (a) |
| `test_rofu_review_draw.py` | 2 | 2 | 2 | 2 | 2 fail at the head (a) |
| `test_rofu_scope.py` | 0 | 0 | 3 | 3 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_rofu_speed.py` | 2 | 2 | 4 | 4 | 2 fail at the head (a) |
| `test_rofu_successor.py` | 10 | 10 | 7 | 7 | 10 in a successor/upgrade/migration/golden file (a) |
| `test_rofu_weeks.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_roles_switch_off.py` | 1 | 1 | 0 | 0 | 1 name the tag, a predecessor or a switch (a) |
| `test_rospeed2_connections.py` | 5 | 4 | 10 | 8 | moved 1; 3 fail at the head (a); 1 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_rospeed_ad_link.py` | 0 | 0 | 5 | 5 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_route_rules_in_grader.py` | 1 | 1 | 9 | 9 | 1 open a vault whose tag is written another way (hand-written config or copied fixture): not sorted (c) |
| `test_router_card.py` | 3 | 3 | 4 | 4 | 3 fail at the head (a) |
| `test_router_coldness_covariates.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_router_failure_records.py` | 9 | 9 | 2 | 2 | 9 fail at the head (a) |
| `test_router_g1_feasibility.py` | 8 | 8 | 13 | 13 | 6 fail at the head (a); 2 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_router_g3_propensity.py` | 2 | 2 | 0 | 0 | 2 fail at the head (a) |
| `test_router_g4_restraint.py` | 11 | 9 | 4 | 4 | moved 2; 9 fail at the head (a) |
| `test_router_g7_fallback.py` | 3 | 3 | 0 | 0 | 3 fail at the head (a) |
| `test_router_offer_log.py` | 0 | 0 | 3 | 3 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_router_presentations.py` | 6 | 6 | 1 | 1 | 5 fail at the head (a); 1 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_router_probe_ties.py` | 3 | 0 | 6 | 3 | moved 3 |
| `test_router_r1_composition.py` | 8 | 6 | 5 | 3 | moved 2; 3 fail at the head (a); 2 pass at the head through a builder whose other users fail there, left unsplit (c); 1 name the tag, a predecessor or a switch (a) |
| `test_router_r2a_landing.py` | 4 | 4 | 4 | 4 | 4 fail at the head (a) |
| `test_router_r2a_serving.py` | 10 | 6 | 4 | 4 | moved 4; 5 fail at the head (a); 1 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_router_r2b_agreement.py` | 3 | 3 | 0 | 0 | 3 fail at the head (a) |
| `test_router_r2b_requests.py` | 1 | 1 | 0 | 0 | 1 fail at the head (a) |
| `test_router_r2b_serving.py` | 20 | 15 | 4 | 4 | moved 5; 15 fail at the head (a) |
| `test_router_r2bc_landing.py` | 6 | 5 | 3 | 3 | moved 1; 5 fail at the head (a) |
| `test_router_r2c_retrieval.py` | 8 | 5 | 1 | 1 | moved 3; 4 fail at the head (a); 1 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_router_r2c_teach_back.py` | 6 | 1 | 2 | 2 | moved 5; 1 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_router_reader_activity.py` | 16 | 1 | 2 | 2 | moved 15; 1 fail at the head (a) |
| `test_router_why_copy.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_rw2d_receipts_migration.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_rw7b_codex_review_fixes.py` | 2 | 2 | 3 | 3 | 2 fail at the head (a) |
| `test_rw7b_fix_round2.py` | 2 | 2 | 3 | 3 | 1 name the tag, a predecessor or a switch (a); 1 fail at the head (a) |
| `test_same_second_order.py` | 16 | 14 | 8 | 8 | moved 2; 8 fail at the head (a); 5 tag-parametrized arms (a); 1 name the tag, a predecessor or a switch (a) |
| `test_scheduler.py` | 0 | 0 | 7 | 7 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_scheduler_golden.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_scheduler_requested_floor.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_section_end.py` | 21 | 21 | 10 | 10 | 16 fail at the head (a); 4 tag-parametrized arms (a); 1 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_serve_eligibility.py` | 16 | 16 | 0 | 0 | 16 open a vault whose tag is written another way (hand-written config or copied fixture): not sorted (c) |
| `test_serve_eligibility_review.py` | 10 | 10 | 5 | 5 | 10 open a vault whose tag is written another way (hand-written config or copied fixture): not sorted (c) |
| `test_sg_slip_vs_gap.py` | 5 | 5 | 12 | 12 | 5 fail at the head (a) |
| `test_sg_successor.py` | 2 | 2 | 6 | 6 | 2 in a successor/upgrade/migration/golden file (a) |
| `test_shadow_rebuild.py` | 4 | 4 | 9 | 9 | 4 open a vault whose tag is written another way (hand-written config or copied fixture): not sorted (c) |
| `test_sidecar_contract.py` | 1 | 1 | 0 | 0 | 1 built by a helper or constant whose name is the tag or the predecessor (a) |
| `test_sidecar_goals.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_sidecar_knowledge_model.py` | 3 | 3 | 2 | 2 | 2 fail at the head (a); 1 built by a helper or constant whose name is the tag or the predecessor (a) |
| `test_sidecar_stops_serving.py` | 1 | 1 | 0 | 0 | 1 open a vault whose tag is written another way (hand-written config or copied fixture): not sorted (c) |
| `test_sim_goals.py` | 3 | 3 | 0 | 0 | 3 open a vault whose tag is written another way (hand-written config or copied fixture): not sorted (c) |
| `test_sim_teach_back.py` | 4 | 4 | 0 | 0 | 4 open a vault whose tag is written another way (hand-written config or copied fixture): not sorted (c) |
| `test_simulation.py` | 4 | 4 | 0 | 0 | 4 open a vault whose tag is written another way (hand-written config or copied fixture): not sorted (c) |
| `test_slate_record.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_source_first_needs.py` | 1 | 1 | 3 | 3 | 1 name the tag, a predecessor or a switch (a) |
| `test_state_sync_scheduling_race.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_stuck_prompt.py` | 3 | 3 | 5 | 5 | 3 compare tags, run a switch arm or a tag arm (a) |
| `test_stuck_prompt_composition.py` | 1 | 0 | 1 | 0 | moved 1 |
| `test_stuck_prompt_replay.py` | 3 | 3 | 1 | 1 | 2 built by a helper or constant whose name is the tag or the predecessor (a); 1 fail at the head (a) |
| `test_successor_switches.py` | 4 | 4 | 10 | 10 | 4 in a successor/upgrade/migration/golden file (a) |
| `test_surfaced_belief_corrections.py` | 0 | 0 | 4 | 4 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_surprise.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_te3a_lesson_opportunity.py` | 3 | 3 | 2 | 2 | 3 fail at the head (a) |
| `test_te3a_successor.py` | 1 | 1 | 6 | 6 | 1 in a successor/upgrade/migration/golden file (a) |
| `test_te3b_binding.py` | 0 | 0 | 4 | 4 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_te3b_codex_review.py` | 4 | 4 | 4 | 4 | 4 fail at the head (a) |
| `test_te3b_offers.py` | 1 | 1 | 4 | 4 | 1 fail at the head (a) |
| `test_te3b_successor.py` | 1 | 1 | 6 | 6 | 1 in a successor/upgrade/migration/golden file (a) |
| `test_te3b_value.py` | 0 | 0 | 4 | 4 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_teach_back.py` | 3 | 2 | 3 | 2 | moved 1; 2 tag-parametrized arms (a) |
| `test_teacher_exam_question_guard.py` | 2 | 2 | 4 | 4 | 2 compare tags, run a switch arm or a tag arm (a) |
| `test_teacher_te0_confidence_events.py` | 3 | 3 | 4 | 4 | 3 fail at the head (a) |
| `test_teacher_te0_review_fixes.py` | 3 | 3 | 5 | 5 | 3 fail at the head (a) |
| `test_teacher_te1_migration.py` | 0 | 0 | 3 | 3 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_teacher_te1_successor.py` | 2 | 2 | 61 | 61 | 2 in a successor/upgrade/migration/golden file (a) |
| `test_teacher_te1b_landing_r2.py` | 8 | 8 | 9 | 9 | 8 fail at the head (a) |
| `test_teacher_te1b_migration.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_teacher_te1b_rereview_fixes.py` | 4 | 4 | 5 | 5 | 4 fail at the head (a) |
| `test_teacher_te1b_review_fixes.py` | 6 | 6 | 7 | 7 | 6 fail at the head (a) |
| `test_teacher_te1b_suggestions.py` | 15 | 14 | 27 | 25 | moved 1; 14 fail at the head (a) |
| `test_teacher_te2_migration.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_teacher_te2_sidecar.py` | 2 | 0 | 2 | 0 | moved 2 |
| `test_teacher_te2_successor.py` | 1 | 1 | 6 | 6 | 1 in a successor/upgrade/migration/golden file (a) |
| `test_teacher_te2log_migration.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_tier1_decider.py` | 0 | 0 | 7 | 7 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_today_headline.py` | 1 | 1 | 0 | 0 | 1 built by a helper or constant whose name is the tag or the predecessor (a) |
| `test_tui_app.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_untaken_repair_episode.py` | 17 | 7 | 5 | 5 | moved 10; 4 fail at the head (a); 3 name the tag, a predecessor or a switch (a) |
| `test_upgrades.py` | 382 | 382 | 19 | 19 | 382 in a successor/upgrade/migration/golden file (a) |
| `test_ux_phase1_round2_rereview.py` | 2 | 2 | 1 | 1 | 2 tag-parametrized arms (a) |
| `test_ux_phase4_feedback.py` | 10 | 1 | 1 | 0 | moved 9; 1 compare tags, run a switch arm or a tag arm (a) |
| `test_ux_phase4_landing.py` | 5 | 2 | 1 | 0 | moved 3; 1 fail at the head (a); 1 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_valuation_calibration_fields.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_value_candidates.py` | 2 | 0 | 1 | 0 | moved 2 |
| `test_vault_report.py` | 0 | 0 | 18 | 18 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_version_floor.py` | 21 | 21 | 11 | 11 | 17 open a vault whose tag is written another way (hand-written config or copied fixture): not sorted (c); 4 tag-parametrized arms (a) |
| `test_voi_merge_composition.py` | 8 | 4 | 17 | 13 | moved 4; 2 fail at the head (a); 2 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_voi_stopping.py` | 28 | 19 | 57 | 47 | moved 9; 8 name the tag, a predecessor or a switch (a); 6 compare tags, run a switch arm or a tag arm (a); 3 fail at the head (a); 2 tag-parametrized arms (a) |
| `test_voi_v2.py` | 21 | 10 | 19 | 12 | moved 11; 4 fail at the head (a); 3 pass at the head through a builder whose other users fail there, left unsplit (c); 3 tag-parametrized arms (a) |
| `test_why_cases.py` | 1 | 1 | 0 | 0 | 1 fail at the head (a) |
| `test_why_reader.py` | 4 | 4 | 0 | 0 | 3 fail at the head (a); 1 pass at the head through a builder whose other users fail there, left unsplit (c) |
| `test_workbench_in_session_gaps.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `voi_restore_scenarios.py` | 0 | 0 | 3 | 3 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `voi_stopping_helpers.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `why_cases_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |

## 8. Gates run

All through the scratch wrapper (empty home, isolated config dir), in a 3 GB scope at `-n 1`, one at a time, `-m "not arc_close"`.

- The experiment (§2), 16 chunks over 633 files: 966 failed, 10,030 passed (each failure a test that writes an old tag, except 9 cases with no recorded write: 6 `test_upgrades` cases and 3 IH2 tag arms, upgrade and tag-parametrized tests, (a) either way).
- Commit 1's importers (21 files): 235 passed.
- Commit 2's importers (98 files): 1,536 passed, 3 skipped.
- After census, record-only plain run of the 187 files that import any changed module, on the final tree, 6 chunks: 3,045 passed, 12 skipped, 1 failed (`test_robust_completion_gate::test_the_gate_does_not_end_a_planted_episode_whose_next_probe_pays`: `_planted_run() missing 1 required keyword-only argument: 'version'`, this pass's edit; fixed by passing the head) and then that file alone: 11 passed.
- `tests/test_identity_pins.py`, `test_structure_ratchets.py`, `test_effective_defaults_golden.py`, `test_cli_help_snapshot.py`, `test_kill_switches.py`, `test_sqlite_file_copies.py`: 398 passed. No pin, ratchet or golden moved.
- `tests/test_test_layout.py` alone: 3 passed. `tests/test_architecture.py` alone: 18 passed.
- `ruff check`: all checks passed. `lint-imports --no-cache`: 52 kept, 0 broken. `scripts/check_gate_partition.py`: 33,540 collected, landing 33,474 + arc_close 66.
- Not run (the orchestrator's): the landing selection as a whole, the arc-close and durability lanes, `--fresh-connections`, vitest, the vault references (the landing regenerates them).

## 9. Open items

- **The 54 (c) cases** (§4): per-call edits in the data-capture, RO4-RO6 and router files through `_wide_vault`'s pass-through, and nineteen small builders. Low yield; not recommended as a pass of its own.
- **The 84 unsorted cases** (§4): hand-written configs and copied fixtures; a tool that rewrites them would sort them, the two tracked fixtures stay (a).
- **Switch-off arms at the head** (§3): 22 reader and RO0 cases that turn their switch off in config now do so at the head. If the owner reads the D4/D6 rule as covering every switch-off arm, not only predecessor baselines, they go back to their successor's tag by a keyword at their call.
- **Row stamps** stay by the third pass's decision.
- **The experiment's limit** (third pass §2) holds: a builder that reads its own `version` hides a dependency. The seven learner-gap calls were kept for it. Every move here was verified by a plain run, not the experiment.
