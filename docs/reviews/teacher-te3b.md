# Teacher TE3b: lesson offers as candidates of the router objective (`router/te3b-lesson-offers`, base `8b0738499d`)

Built from `docs/specs/spec_teacher_v1.md` revision 5: §15.1a (the scope), §24's TE3b row, §23.1 decisions 1 and 5
(owner, Nov 5: accepted). One router successor (`mvp-0.53`: one constant, `LESSON_OFFERS_ALGORITHM_VERSION`; renumbered
at landing if another successor lands first), switch `router.lesson_suggestions.in_objective` (default true). **No
migration.** **No model request is added**: the LLM policy's existing `router_llm_choice_v3` request gains one option
(0 paid calls a day added; no paid call was made by this stage). No reader or writer of the old item difficulty scalar
is added.

## Commits

| Part | Commit | What |
|---|---|---|
| 0 | `8d0cf22296` | The successor, its switch, upgrade, gates, defaults snapshots, CLI and openers; version pins |
| 1, 2, 4, 5 (and 9's backend) | `e4131322b0` | The offer in `plan_block`'s support with its sensors and value; the LLM policy's option; the trace's offer fields, the report and binding; the offer block, its one response, `ignored`; TE1b's gate split |
| 3 | `6681b88cea` | RO6's `lesson` feature, the features version a change point |
| 6 | `42a0fe5251` | The forecast binding (`te3b-lesson-offer-forecast-binding-v1`) |
| 7 | `e133e961a7` | Lesson minutes on the objective's clock |
| 8 | `a16ea7f9d9` | LOs with a pending lesson check in the population |
| 9 | (next) | The offer card as a block of Today's plan in the desktop |
| — | (last) | Spec §15.1a and §20 "As built", the router objective spec's §8.11 and §13, this file, regenerated references |

## What exists now

| Spec (§15.1a) | Where |
|---|---|
| Where | `daily_plan/policy.py` installs `PlanPolicy.lesson_offer` (`lesson_offer.build`) only where `router_objective_switches.lesson_offers_on` holds (the tag, the objective serving, TE1b's suggestions with the router, its log and lessons, the switch); `engine._boundary` builds the offer before `decide`, `decide` appends it to the feasible set when the source has one, `ObjectiveChooser.choose` keeps it out of staged's pick and order and puts it after the blocks, before stop. Not in `plan_interrupt` |
| Which LOs | TE1b's `build_candidates` (its three reasons and its exclusions: an open lesson, taught since the last attempt; a typed-goal LO with a pending lesson check is the latter) |
| How many | One offer a decision (its best by TE1b's staged value); two alternatives on its card, never valued |
| The acceptance model | TE1b's, replayed over the daily decisions and the drawn offers together (`router_suggestions.all_decisions`); its posterior predictive mean and sd (`lesson_offer.accept_moments`, AD's quadrature over each recovery-grid bank) moment-matched to a Beta (`beta_from_moments`): each θ draw's `p` |
| The value | `value.Action(kind=LESSON, accept=(a, b), mass, minutes, minutes_log_sd, commitments)` (`objective_inputs.action_for`): RO4's offer branches as built; accepted = the lesson action at the learned lesson-check mass with TE3a's curve, its duration sampled, its retention check committed (`run_tail`'s `commitments`: a graded attempt at the first day boundary past its date); declined = the tail's next block. The tail's block means exclude the offer. `branch_terms` carries each branch's terms |
| The draw | RO4's mix over the support with the offer (G3); `π_L` from the existing request (`requests.lesson_offer_description`); `π_Q` argmax of `Ṽ`; the stop coin unchanged; the ceiling across the day's cards and offers, each bind logged (`lesson_offers.ceiling.bound` on the decision) |
| The response | TE1b's `lesson.suggestion_respond` answers a `plan_block` offer decision (`router_suggestions.offer_decision`), ends its block (`lesson_offer.end_block`); a serve after the card was shown with no answer records `ignored` and moves on; each boundary records `ignored` on an unanswered offer whose plan closed or day passed (`lesson_offer.sweep_ignored`). An accepted lesson has `origin = router` and `origin_ref` the decision id (TE1's `open_lesson` reads the response by decision id, any kind) |
| The trace | `candidates[offer].offer` (`objective_chooser._offer_trace`): sensors, terms, split, alternatives, the action; `learnloop router trace --json` adds `offer_binding` (`router_objective.offer_report.binding`); the plain-words "why" a line |
| Lesson minutes | `price.lesson_spans` in `price.activity_spans(lessons=)`, for the serving clock, RO5's realized cost, RO6's rewards and the return model |
| The population | `db.stores.lessons.pending_delayed_checks` in `objective_inputs.population` and `build` |
| RO6 | `learned_tail.FEATURES_VERSION_LESSON` / `NAMES_LESSON`; `tail_data.features_version(config)` |
| Evaluation | `router_objective.offer_report.build` in `learnloop router objective-report` (`lesson_offers` at the tag) |
| TE1b's daily draw | `lesson_suggestion.suggestions_active` = `suggestions_enabled` and not `offers_in_objective`; `today_suggestion` still shows a pending Start (a card's or an offer's) |
| The desktop | `screens/today/LessonOfferBlock.tsx` in `TodayPlace` and `DailyPlanView`; `todayPlan.ts` names the block; `dailyPlan.ts` the key label; DTOs `PlanLessonOfferDto`, `PlanLessonOfferStepDto` |
| Successor | `LESSON_OFFERS_ALGORITHM_VERSION`, `learnloop.lesson_offers_upgrade`, every defaults snapshot recomputed |

## Built differently from the text, or read (with the smallest way to finish)

1. **The response goes through TE1b's RPC.** A drawn offer is answered with `lesson.suggestion_respond` on its
   `plan_block` decision; no new RPC, so the Tauri commands, the desktop RPC contract and the mobile allowlist (whose
   files the owner is editing in the main checkout) are untouched. A separate `plan.lesson_offer_respond` would only
   rename it.
2. **`p` per θ draw** is a draw from a Beta moment-matched to the acceptance model's posterior predictive (its mean
   and sd over TE1b's recovery grid and each bank's Gaussian, AD's quadrature), which RO4's built offer interface
   takes (`Action.accept`). Smallest way to the exact form: give `Action` a logit-normal mixture (the banks' `(w, m,
   v)`) and draw `σ(m + √v·z)` per draw on `offer_u`'s stream.
3. **The accepted branch's checks**: one retention check on the target at `teacher.delayed.fallback_retention_days`
   (3), a graded attempt at the first day boundary past it, charged no minutes. The lesson's own date is set from
   retrievability at its close, after this decision, and a transfer check's LO is not known before the lesson, so it
   is not simulated. Smallest way: date the check with `delayed_checks.due_days` on the target's FSRS state, and add
   a transfer commitment on the first downstream LO when one exists.
4. **The lesson's in-lesson checks and probes are not simulated as observations of their own** (§15.1a "observes");
   its effect is TE3a's curve on the target at the learned mass. Smallest way: one `_observe` per landed node at the
   lesson's end, at the lesson-check mass, before the curve's step.
5. **The duration's within-lesson spread** (`DURATION_LOG_SD`, 0.7) is a labelled prior, not learned; the log median
   is (normal posterior, labelled prior centred on the card's 15 minutes). Smallest way: a normal-inverse-gamma on the
   log minutes.
6. **`ignored`**: the offer's block holds the plan until it is answered; a serve after the card was shown with no
   answer is the learner moving on (`ignored`, recorded `moved_on_without_an_answer`), and each boundary records
   `ignored` on an unanswered offer whose plan closed or day passed (`next_boundary_step`); TE1b's own sweep records an
   earlier day's at Today's open.
7. **Lesson minutes on every reader of the clock**: the serving clock, RO5's realized cost (`scores.window_cost`),
   RO6's rewards and the return model all read `activity_spans` with the same flag. A flip of the switch therefore
   also changes the realized cost of a closed window that held a lesson (none exist in the copies); the flag is the
   config's, as every other serving switch's.
8. **The forecast binding** anchors at the accepted lesson's close through an `anchor_at` group in AD's
   `history_resolve.resolve_curves` (an additive branch; every plan-presentation group is resolved as before).
9. **Not built: the router's ITT outcome** (`router.outcomes`) for an offer decision: it reads as a block with no
   plan presentation (`nothing served`). The spec's evaluation is RO §8.7's common return, which the trace carries.
   Smallest way: an `offer` binding in `outcomes._binding` that reads the decision's response and the lesson's close.
10. **The context's hour resolution**: TE1b's context (the local hour, the days since the last suggestion and since a
   "Not now") is read at one hour for the offer (`CONTEXT_RESOLUTION_DAYS`, registered as numerical resolution), so a
   prefetch and its serve share one boundary key; TE1b's daily draw keeps its own exact context.
11. **An observation, not a change**: two identically built synthetic vaults at `mvp-0.52` (the predecessor's code,
   seeds pinned through `fake_runtime(seed=...)`) do not choose the same numeric argmax at every boundary (two runs
   differed at their third decision): the predecessor's boundary key reads the latest attempt's id and other
   run-specific values. The byte-identity test therefore values **one** database under the three configs (switch off,
   below the tag, on): off and below are identical in every input, every `Q̄` draw, the population, the session and the
   gates (`tests/test_te3b_population.py`).

## The §24 tests

| §24's TE3b row | Test |
|---|---|
| G3 recomputes `μ` with an offer in the support, including each failure path | `tests/test_te3b_offers.py::test_g3_mu_recomputes_with_an_offer_in_the_support_on_every_path` (both policies answering, no model, the numeric policy failing too; under the stop coin through its served distribution) |
| Offer branches against a hand-computed case | `tests/test_te3b_value.py::test_offer_branches_match_a_hand_computed_case_for_a_lesson` (and RO4's own `tests/test_ro4_value.py::test_offer_branches_match_a_hand_computed_case`, unchanged) |
| The eve-of-exam regression unchanged | `tests/test_te3b_value.py::test_the_eve_of_exam_regression_holds_with_a_lesson_offer_beside_the_block` (and RO4's, unchanged) |
| One response per decision, `ignored` at the next boundary | `tests/test_te3b_offers.py::test_a_drawn_offer_is_a_block_answered_on_its_own_decision`, `::test_moving_on_without_an_answer_is_ignored_at_the_next_boundary` |
| The ceiling binds and is logged | `::test_the_ceiling_binds_across_the_days_offers_and_is_logged` |
| No offer during a cold check, a probe or a randomized-check block | `::test_no_offer_beside_forced_items`, `::test_the_randomized_check_block_carries_no_offer` (offers exist only at a block boundary with no forced item; a cold check or a probe is an item inside a block, a randomized check its own rules-placed block) |
| κ counts a lesson's active minutes | `tests/test_te3b_clock.py` |
| The population holds LOs with a pending lesson check | `tests/test_te3b_population.py::test_the_population_holds_los_with_a_pending_lesson_check` |
| RO6's features version is a change point | `tests/test_te3b_features.py` |
| Switch off or below the tag identical | `tests/test_te3b_population.py::test_switch_off_or_below_the_tag_values_the_same_database_as_mvp052` (one database under the three configs: inputs, `Q̄` draws, population, session, features version, the offer builder, TE1b's gate), `tests/test_te3b_offers.py::test_te1bs_daily_card_is_drawn_only_where_the_objective_does_not_serve`; every earlier link's tests (below) |
| The deadlines hold on a copy | The synthetic run below (the numeric policy's slowest answer 3.8 s against `router.timeout_seconds` 8 s); the copy itself is the landing's smoke |
| The forecast binding | `tests/test_te3b_binding.py` |
| The LLM policy's one request | `tests/test_te3b_offers.py::test_the_llm_policy_sees_the_offer_in_its_existing_request` |
| The desktop card | `apps/learnloop-tauri/src/screens/today/LessonOfferBlock.test.tsx` |

## Numbers on a copy-shaped synthetic vault (fakes only; `docs/reviews` measurement, not a test of record)

The wide daily-plan vault (`tests/test_daily_plan_build._wide_vault`: seven LOs, ten items, one repair LO with an open
problem, due reviews) with one active goal over its concept (so its unstarted LOs are TE1b `new_goal` candidates),
the fake router LLM answering every request (`tests/test_ro4_objective_serving.policy_answer`), four simulated days
of serving and answering, each drawn offer answered with a draw at its `P(accept)` (seed 7), an accepted lesson
written as a 20-minute closed lesson with its foreground interval; once at `mvp-0.52` and once at `mvp-0.53`.

| | `mvp-0.52` | `mvp-0.53` |
|---|---|---|
| Objective decisions over 4 days | 14 | 18 |
| Decisions with an offer in the support | 0 | 7 (all on days 1-2; from then on `none:no_candidate`: the two LOs taught were excluded by TE1b's rule and no other candidate remained) |
| Offers drawn (shown) | 0 | 2 (one on each of the first two days), both accepted (draws `u` 0.32 and 0.15 at `P(accept)` 0.90 and 0.92) |
| The offer's `μ` when in the support | | 0.063-0.088 (the floor, the LLM's share and staged's none; the numeric policy did not prefer it) |
| Ceiling binds | | 0 |
| Serving time per step (advance, mean / max) | 2.29 s / 5.88 s | 2.79 s / 6.63 s (+22% mean: the offer's build, its Beta, its duration read, one more valued action) |
| The numeric policy's latency (mean / max) | 2.28 s / 3.64 s | 2.56 s / 3.82 s, inside `router.timeout_seconds` (8 s) |
| The LLM policy's prompt (max bytes) | 14 264 | 16 301 (the offer's option row, at most 240 characters, and its LO's history on the shared card, inside `llm_card_token_budget` 48 000) |
| Model requests | one per decision | one per decision (no new request) |

One drawn offer's trace (`candidates["lesson_offer:lo_svd_definition"].offer`), abridged:
`sensors.p_accept` {mean 0.90, sd 0.124, Beta (4.35, 0.48), `suggestion_priors_v1`, 0 updates}; `reason` `new_goal`;
`ad_p_bar` 0.079; `lesson_curve` {`ad_lesson_priors_v1`, mean (0.093, 0.186), position 0}; `check_mass` {0.50, sd
0.21, `lp_priors_v1`, 0 updates}; `duration` {median 15, log-sd 0.99, `seed`}; `checks` [retention on the target at 3
days]; `terms` {`q_accepted` 9.4351, `q_declined` 9.4891, `p` 0.937, `kappa_integral_accepted` 0.0504,
`after_accepted` 9.4846, `terminal_accepted` 4.9678, `q_minus_stop` −0.0202, `v_residual` 0}; `split` display only;
`alternatives` two.

## Paid calls

None. No model request is added: the LLM policy's existing `router_llm_choice_v3` request gains one option at a
decision with an offer. Every test uses fakes.

## Gate (this step)

Owner rule (2026-10-17): no full suite here; targeted runs only, each inside `systemd-run --user --scope --quiet -p
MemoryMax=5G -p MemorySwapMax=1G`, pytest at `-n 6`, vitest at `--maxWorkers=4`, one run at a time. Every ad-hoc
command (the snapshot recomputation, the reference scripts, lint-imports) under `env -i` with empty `HOME`,
`CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| `uv run lint-imports --no-cache` | 43 contracts kept, 0 broken; the frozen deferred cycles kept |
| The successor and upgrade test files of every earlier link (59 files, `-n 6`) | first run 869 passed, 9 failed (version pins this stage moves); after the pins, the 10 files again: 155 passed, 6 skipped, 1 xfailed |
| Every test file that exercises a changed module, with the contract tests (207 files, list below, `-n 6`) | 12 141 passed, 15 skipped, 4 failed: `test_module_catalog_inventory` (the new modules' notes untracked until the references commit), `test_ro1_availability_reads` and `test_architecture` (fixed in `67ea2c899b`), `test_ro0_rows9_13_decision_state::test_receipts_hold_ids_and_numbers` (its check that no LO title appears in a receipt matched the title "P1" inside a random ULID; passes on rerun; pre-existing, unrelated) |
| The fixed files and every TE3b test again (10 files) | 86 passed |
| The contract tests (module catalog, CLI help snapshot, registry audit, table roles, desktop RPC contract, Codex lockdown and its frozen list, architecture, tracked fixture databases, sidecar registry, the "why" copy and the plain-words audits; 14 files) | 407 passed, 1 skipped, 1 failed (the module catalog, before the references commit) |
| After the references commit: the module catalog, every TE3b test file, RO1's availability reads and the architecture tests (10 files) | 81 passed |
| `npm install`; `npm run typecheck`; `npx vitest run --maxWorkers=4` on the touched and related files (11 files: `LessonOfferBlock`, `LessonSuggestionCard`, `TodayPlace`, `DailyPlanView`, `TodayScreen.plan`, `TodayScreen.suggestion`, `App.lessonSuggestion`, `dailyPlan`, `todayPlan`, the two deny-list audits); `npm run frontend:build` | typecheck clean; 164 tests passed; built |
| `cargo check` | not run: nothing under `src-tauri` changed (no new RPC) |
| Durability lane | not run: no migration, no DB or connection code changed |
| `db_generate_reference.py`, `desktop_generate.py`, `module_generate.py` and their validators, `validate_vault.py` | regenerated (1182 effective configuration leaves; the two prose counts and the desktop validator's inventory counts moved by the new key and the new component); every validator passes |

Test files of the 207-file run:
daily_plan_fakes.py router_mixture_helpers.py router_model_fakes.py test_ad1_codex_rereview_fixes.py test_ad1_codex_review_fixes.py test_ad1_outside_and_cli.py test_ad23_contract.py test_ad23_fix_r5.py test_ad23_fix_r8.py test_ad23_fix_review.py test_ad23_intent_compose.py test_ad23_inversion.py test_ad23_owner_decisions.py test_ad23_pool_membership.py test_ad2_model.py test_ad2_serving.py test_ad3_monitoring.py test_ad3_reading.py test_ad3_subject_view.py test_adaptive_difficulty_ad1.py test_ad_epoch.py test_ad_guard_offer_receipts.py test_ad_guard.py test_ad_guard_reachable_reads.py test_architecture.py test_block_chooser_interface.py test_cli_help_snapshot.py test_compare_sources_keep.py test_curriculum_c1_codex_review_fixes.py test_curriculum_c1_fix_round2.py test_curriculum_c1_fix_round3.py test_curriculum_c1_fix_round4.py test_curriculum_c1_plan_follows_path.py test_curriculum_c1_round5_followups.py test_daily_plan_admission.py test_daily_plan_build.py test_daily_plan_composition.py test_daily_plan_kill_switch.py test_daily_plan_owner_decisions.py test_daily_plan_reading.py test_daily_plan_reentry.py test_daily_plan_replay.py test_daily_plan_review_regressions.py test_daily_plan_rpc.py test_daily_plan_split.py test_data_capture_a1_prefilter.py test_data_capture_a2_measurement.py test_data_capture_a4_delayed_completion.py test_data_capture_a5_not_ready_floor.py test_data_capture_codex_rereview.py test_data_capture_codex_review.py test_data_capture_landing_review.py test_data_capture_phone.py test_data_capture_report.py test_data_capture_successor.py test_desktop_rpc_contract.py test_dl2_rw4b_keyed_pick_check.py test_duration_estimates.py test_evsi_staged_binding.py test_exam_protection_identity.py test_exam_protection_landing.py test_field_workbench_signals.py test_followup_codex_review.py test_followup_next_matrix.py test_followup_router.py test_followups_batch6_review_fixes.py test_followups_batch6_router_report.py test_followups_batch6_te1b_card.py test_followups_batch6_verify_fixes.py test_hypothesis_marks_context.py test_intent_codex_rereview.py test_intent_codex_review.py test_intent_exclusion.py test_intent_fix_round4.py test_intent_fix_round5.py test_intent_fix_round6.py test_intent_fix_round7.py test_intent_goal_deadline.py test_intent_plan.py test_intent_resolution.py test_learner_pick_proposal.py test_learner_text_gaps_composition.py test_mcp_c1a_landing.py test_mcp_c1a_narrow.py test_mcp_tools.py test_method_explicit_landing.py test_method_explicit_upgrade.py test_module_catalog_inventory.py test_mvp011_upgrade.py test_mvp014_upgrade.py test_mvp015_upgrade.py test_mvp016_upgrade.py test_mvp017_upgrade.py test_mvp018_upgrade.py test_mvp020_upgrade.py test_mvp021_upgrade.py test_mvp023_upgrade.py test_mvp024_upgrade.py test_plan_determinism_landing.py test_plan_determinism.py test_plan_follows_path.py test_reader_question_note_id_placement.py test_reader_rw4b_admission_idempotency.py test_reader_rw4b_fix6.py test_reader_rw6b_p2_landing.py test_reading_step_switch.py test_registry_audit.py test_reread_safety_landing.py test_ro0_codex_review.py test_ro0_codex_verify.py test_ro0_gate.py test_ro0_question_state.py test_ro0_report.py test_ro0_row10_cold_timing.py test_ro0_row11_goal_lifecycle.py test_ro0_row12_trajectory.py test_ro0_row3_ask_availability.py test_ro0_row4_exposure_initiator.py test_ro0_rows7_8_sessions.py test_ro0_rows9_13_decision_state.py test_ro1_availability.py test_ro1_availability_reads.py test_ro1_upgrade_report.py test_ro2_ad_raw_document_reads.py test_ro2_history_forecaster.py test_ro2_history_resolve.py test_ro4_codex_review.py test_ro4_objective_serving.py test_ro4_price.py test_ro4_trace_report.py test_ro4_value.py test_ro4_weight.py test_ro5_calibration.py test_ro5_checks.py test_ro5_codex_rereview.py test_ro5_codex_review.py test_ro5_landing.py test_ro5_picks.py test_ro5_stop_coin.py test_ro6_codex_rereview.py test_ro6_codex_review.py test_ro6_landing.py test_ro6_learned_tail.py test_ro6_serving.py test_ro6_tail_data.py test_rofu_ad_latent.py test_rofu_ad_link.py test_rofu_ad_stable.py test_rofu_carried.py test_rofu_generator_switches.py test_rofu_learning.py test_rofu_monotone.py test_rofu_review_draw.py test_rofu_scope.py test_rofu_speed.py test_rofu_switch_key.py test_rofu_weeks.py test_router_card.py test_router_g1_feasibility.py test_router_g4_restraint.py test_router_g7_fallback.py test_router_p2_bridge.py test_router_presentations.py test_router_r1_composition.py test_router_r2a_landing.py test_router_r2a_serving.py test_router_r2b_agreement.py test_router_r2bc_landing.py test_router_r2b_requests.py test_router_r2b_serving.py test_router_r2c_retrieval.py test_router_r2c_teach_back.py test_router_reader_activity.py test_router_why_copy.py test_rw5c_plain_words.py test_rw7b_codex_review_fixes.py test_rw7b_fix_round2.py test_salience_firewall.py test_serve_eligibility.py test_serve_eligibility_review.py test_sidecar_registry.py test_source_exercise_rpcs.py test_table_roles.py test_te3a_lesson_opportunity.py test_te3b_offers.py test_te3b_successor.py test_te3b_value_clock.py test_teacher_te0_confidence_events.py test_teacher_te0_review_fixes.py test_teacher_te1b_landing_r2.py test_teacher_te1b_migration.py test_teacher_te1b_rereview_fixes.py test_teacher_te1b_review_fixes.py test_teacher_te1b_suggestions.py test_teacher_te1_successor.py test_teacher_te2log_episodes.py test_teacher_te2log_report.py test_today_headline.py test_tracked_fixture_databases.py test_ux_phase1_landing.py test_ux_phase1_round2_review.py test_ux_phase1_usability_round1.py test_ux_phase4_feedback.py test_ux_phase4_landing.py test_voi_merge_composition.py test_voi_stopping.py test_voi_v2.py 

(`test_te3b_value_clock.py` in that run was split afterwards into `test_te3b_value.py`, `test_te3b_clock.py`,
`test_te3b_population.py`, `test_te3b_features.py` and `test_te3b_binding.py`, each with its part's commit.)

## Owner actions

- Upgrade each working vault to the chain's head (`learnloop upgrade`, default target `mvp-0.53`), as for every link.
- Nothing to configure: `router.lesson_suggestions.in_objective` is on at the tag; off restores TE1b's Today-open
  card and the objective's predecessor support.

## Open questions

1. The predecessor's own serving is not reproducible across two identically built synthetic vaults (seeds pinned;
   item 11 above): worth a look by the router owner, since "byte-identical below the tag" can then only be shown on
   one database.
2. The offer's accepted branch simplifications (items 2-5 above): the exact logit-normal `p`, the dated and transfer
   checks, the lesson's own observations, a learned duration spread. Each has its smallest way written above.
3. Should an offer decision get the router's ITT outcome (`router.outcomes`, item 9)?
