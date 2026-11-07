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

## Landing onto main

Base `8b0738499d`. While the landing ran, main moved four times and each was merged into the branch:
`1c12763372` (the phone v2 spec and the owner's M2a follow-ups), `23ce859c16` (phone V1), `8853cd6b74` (the router
speed stage: switch `[router_objective] held_ad_link`) and `14b2ed09ab` (phone V2). None of them has a successor or a
migration, so TE3b stays **mvp-0.53 <- mvp-0.52** (`LESSON_OFFERS_ALGORITHM_VERSION`), with no migration. The tip
this record was written on is named in the commit that adds it.

### Orchestrator rulings (verbatim)

- R1: "The final verify is clean; no further Codex round. If the speed stage has landed before you, TE3b's offer branch runs on its held AD link when held_ad_link is on and on the landing code's link when off: TE3b's value tests run with held_ad_link on and off."
- R2: "The builder's finding that two identically built mvp-0.52 vaults serve differently with seeds pinned is the deadline-bound refinement (the numeric policy refines until the LLM answers or the deadline, so the completed draw count depends on timing; Codex showed the same at the follow-up batch and the speed stage). Byte-identity below the tag and with the switch off is therefore shown on one database valued under the configs, as built; the smoke's identity pairs pin the boundary key and the generator key as earlier landings did. Recorded, not a TE3b defect."
- R3: "Accepted for landing and queued for the follow-up batch with their smallest finishes: p as a moment-matched Beta, one simulated retention check at the seeded 3 days, the lesson's own checks and probes not simulated as observations, a fixed duration spread, and no router.outcomes record for offer decisions."
- R4: "With the switch on, lesson minutes count on every reader of the objective's clock, including RO5's realized cost of closed windows, so flipping the switch moves a closed window's cost where a lesson happened. Accepted: the switch is in RO6's generator payload (a change point), the copies have no lessons, and a config flip is not later data; the record says so and the report names the switch state its scores were computed under."
- R5: "Owner, Nov 5: the old item difficulty scalar is to be retired in the refactor. TE3b adds no new reader or writer of it; the landing checks this with a grep of the diff against main and records the result."

Coordinator instructions during the landing (Nov 6-7), followed: merge phone V1 and rerun `test_mobile_*`,
`test_desktop_rpc_contract` and `test_sidecar_serializer_snapshot`; merge the speed stage per R1, recompute the
defaults snapshots and rerun the targeted set with `test_rospeed_*`; merge phone V2, make a phone step hold a lesson
offer for the desktop like a reading block (with a test), and rerun the targeted set with `test_mobile_*` and
`test_te3b_*`; run the full suite once on the final merged tree. The full gate below ran once, on the final tree (two
earlier full-suite starts, on the speed merge and before it, were stopped when main moved).

### Commits

| Step | Commit | What |
|---|---|---|
| Merge | `e55f322850` | Main `1c12763372` (no overlap with TE3b's files) |
| References | `b0b7a17ccc` | Regenerated (source stamps, line citations, test counts) |
| Merge | `bd1bcd9c95` | Main `23ce859c16` (phone V1); two generated module notes took main's side |
| References | `59c873a5e0` | Regenerated |
| Test | `4b581e2666` | The two drawn-offer tests pin a decision seed on the stop coin's `policy` arm (below) |
| Merge | `246bdfc0b7` | Main `8853cd6b74` (the speed stage); the resolutions below |
| R1 | `7844c25890` | The offer's value on the held link and on the landing link, bit for bit |
| Pin | `931e2aa677` | TE3b's frozen mvp-0.52 digest drops `held_ad_link` too |
| References | `3e76ae4f34`, `bf84a858c9` | Regenerated; the two prose leaf counts 1182 -> 1183 (`3e76ae4f34`'s message says every validator passed; `db_validate_reference` had failed on those two counts until `bf84a858c9`) |
| Merge | `a7fdc90e67` | Main `14b2ed09ab` (phone V2); `desktop_validate.py` counts both new files |
| Phone | `cec9749e3a` | A phone step holds a drawn lesson offer for the desktop |
| References | `f40f417565` | Regenerated (323 TS/TSX desktop files) |

**The resolutions.**
- **`adaptive_difficulty/history_resolve.py`** (speed item 2 against TE3b's forecast binding). TE3b's `anchor_at`
  branch (an accepted offer's lesson close, with no plan presentation of its own) is kept. It now reads the speed
  stage's per-presentation and per-LO indexes, so both branches read the same rows in the same order.
- **`config/template.py`.**
  - The speed stage's `held_ad_link` note is kept beside TE3b's.
  - Every defaults snapshot was recomputed on the merged defaults: 44 of 44.
  - 41 conflicts were hash lines only. A script took either side of each, matching the exact
    `"<version>": "<sha256>",` pattern, and the recompute rewrote all 44.
- **Frozen digests.** `test_te3a_successor` and `test_te3b_successor` drop both TE3b's key and `held_ad_link` to
  reproduce their frozen mvp-0.51 and mvp-0.52 values.
- **R1** (`tests/test_te3b_value.py::test_the_offer_runs_on_the_held_link_with_it_on_and_on_the_landing_link_with_it_off`).
  - The test values a lesson offer beside the speed stage's decision shapes, with AD's link.
  - The offer's accepted branch commits a delayed check, whose graded attempt reads the link through `_practice`.
  - It runs under each of the speed stage's three rollout options.
  - `held_ad_link` on and off give the same values and terms bit for bit, and the held run equals the landing code
    put back (`tests/test_rospeed_ad_link._landing_code`).
  - TE3b's existing value tests carry no AD link, so the switch cannot reach them.
- **Phone V2.**
  - Before V6 a phone never serves a lesson offer. The device's block walk passes an offer block over, as it does a
    reading block.
  - When a phone's Next crosses a boundary that draws an offer, the step is the held step. It counts the offer
    (`held_lesson_offers`, in the step filter's own set).
  - The offer stays unshown and unanswered, so a phone serve never records `ignored`. The desktop's Next then shows
    its card on the same decision (`tests/test_te3b_offers.py::test_a_phone_step_holds_a_drawn_offer_for_the_desktop`).
  - The phone's own wording (`waitingForDesktop`) is unchanged, so it names no waiting lesson.
- **`desktop_validate.py`.** Both sides added one file: TE3b's `LessonOfferBlock.tsx` and V2's
  `answerExposureGate.ts`. The merged counts are 323 TS/TSX files, 312 entry-build and ACTIVE 329. This was an
  exact-string script edit.
- **A test flake fixed** (`4b581e2666`).
  - `test_moving_on_without_an_answer_is_ignored_at_the_next_boundary` failed in 2 of 4 runs alone.
  - With the seed unpinned, RO5's stop coin draws its arm per run, and its `offer_stop` arm (5%) serves stop at the
    first decision. A 12-run probe showed the arm varying across runs.
  - The two tests that need a drawn offer served now pin a seed on the coin's `policy` arm. After the fix,
    `test_te3b_offers.py` passed 6 runs of 6.

**R5.**
- `git diff 8853cd6b74 HEAD -- src migrations` (1546 added lines, 172 removed) has no added or removed line naming
  `difficulty`, `irt`, `surprise` or `difficulty_from_prior`.
- The same grep against `1c12763372`: the only lines naming `difficulty` are context lines, so none was added or
  removed. Those context lines are the `adaptive_difficulty` package's paths and comments, and FSRS's `d` median.
- No migration. TE3b adds no reader or writer of the old item difficulty scalar.

**R2, R3, R4.**
- R2 is recorded, and the smoke's identity pairs set aside the keys it names (below).
- R3's five items are queued for the follow-up batch, as written.
- R4 is recorded. The objective report's `lesson_offers` section is computed under the vault's switch state at the
  time of the report. On the week copies below, a closed window that held a lesson costs its lesson minutes with the
  switch on.

### Gate

**Rules.**
- Every pytest, vitest, npm and cargo command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p
  MemorySwapMax=1G`. The full suite ran in 10G/2G under `flock /tmp/learnloop-fullsuite.lock`.
- Every other Python or CLI command ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.
- No model call or paid call was made.

| Command | Result |
|---|---|
| Step 1 on the first merge (`e55f322850`): targeted pytest, 163 files, `-n 6` (`test_te3b_*`, `test_te3a_*`, `test_teacher_te1b*`, every `lesson_suggestion` file, `test_ro4_*`, `test_ro5_*`, `test_ro6_*`, `test_rofu_*`, `test_ro0_*`, `test_ro1_availability*`, `test_ro2_ad_raw_document_reads`, `test_followup_*`, the defaults-snapshot and version-pin files, the display-label audit, the CLI help snapshot, architecture, registry audit, desktop RPC contract, mobile allowlist, module catalog, sidecar registry, table roles) | 3045 passed, 13 skipped, 6 xfailed, 1 failed: `test_rofu_carried::test_an_early_publication_served_keeps_its_carried_valuation` (the known timing-sensitive test, under the week smoke's load; alone 2 of 3 then, 3 of 3 after the gate) |
| After phone V1: `test_mobile_*`, `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`, module catalog, architecture, `test_te3b_*` | 724 passed, 1 failed (the stop-coin flake, fixed in `4b581e2666`; `test_te3b_offers.py` then 6 runs of 6) |
| After the speed stage: the 163 files with `test_rospeed_*`, the serializer snapshot, `test_mobile_*` and every file naming `held_ad_link` (181 files) | 3488 passed, 13 skipped, 6 xfailed, 1 failed (TE3b's frozen mvp-0.52 digest, `931e2aa677`; then the snapshot, pin, CLI help and registry files 37 passed) |
| After phone V2, on the final tree (`f40f417565`): the 181 files with every `test_mobile_*`, `test_te3b_*` and every file naming the device filter (190 files) | **3658 passed, 13 skipped, 6 xfailed** |
| Step 2 (final tree): `db_generate_reference` + `db_validate_reference` | errors [] (1183 effective leaves after the two prose counts) |
| Step 2: `desktop_generate` / `desktop_validate` | passed (323 TS/TSX + 6 Rust; ACTIVE 329) |
| Step 2: `module_generate` / `module_validate` | PASS (1250 modules, 1440 test files) |
| Step 2: `validate_vault.py` | passed (2243 notes) |
| Step 2: config fingerprints | 44 of 44 snapshots equal to their recomputation on the merged defaults |
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| `lint-imports --no-cache` | 43 kept, 0 broken |
| Full pytest (`-n 8 --dist worksteal`), final tree `f40f417565` | **30101 passed, 90 skipped, 47 xfailed, 1 failed** (57:43). The failure passed alone 3 times: `test_ro0_rows9_13_decision_state::test_receipts_hold_ids_and_numbers` (its check that no LO title is in a receipt matched the title "M2" inside a random id; the builder's record names the same with "P1") |
| Durability lane (`-m durability`) | 408 passed, 1 skipped |
| Owner lane on fresh backup-API copies of `owner-copies-mvp035` | 83 passed, 4 skipped, and the 2 known failures (`test_activity_backfill`, `test_placement_fixture_copies[arxiv_v2]`) |
| Desktop: typecheck, whole vitest (`--maxWorkers=4`), `frontend:build`, `cargo check` | ok, 2778 passed, ok, ok |
| Mobile: typecheck, build | ok, ok |

The full suite ran once, on the final merged tree, after the speed stage and phone V2 (both change `daily_plan`).

### Smoke

**Setup.**
- **Copies.** Fresh backup-API copies of `~/learnloop-backups/mvp043-20261103-copy` (arxiv_v2, linear_algebra,
  probability), neutralized (every AI route at 127.0.0.1:9), under `fixtures-local/landing-te3b-smoke/` (deleted).
- **Upgrades.**
  - On main code: mvp-0.45, rebuild, mvp-0.46, mvp-0.47, rebuild, then the default (main's latest, mvp-0.52; head
    249).
  - On branch code: that copy opened once (no migration), then the default upgrade (mvp-0.52 -> mvp-0.53).
- **Code.** `git archive` of both trees with `migrations/`, in three passes:
  - pass 1: main `1c12763372` against the branch at `e55f322850`;
  - pass 2: main `8853cd6b74` against `7844c25890`;
  - pass 3: main `14b2ed09ab` against `f40f417565`.
- **Fakes.** The router LLM, the Decider, the teacher (`TeacherFake`) and its grader are in-process fakes.
  `fakes4.py`, the tests' `BlindRivalClient` and `AuthorFake` serve the rest.
- **Driver.** The follow-up batch's driver, extended with `lesson.suggestion` at Today's open, the offer step, and an
  accepted offer's lesson through the real handlers. Every Python run used an empty `HOME`, `CODEX_HOME` and
  `LEARNLOOP_CONFIG_DIR`.

**The week (pass 2, on the speed merge; at the tag with the switch on).**

Per copy:
- **Day 0 (Nov 5)** ran with the switch off: the predecessor's features version.
- **Then seven days (Nov 6-12)** with the switch on:
  - The plan was in use.
  - A seeded synthetic learner answered about 70% right.
  - Offered stops were kept going or accepted at random, with at most 3 keep-goings a day.
  - Every miss opened FG1's follow-up, whose probe `AuthorFake` wrote.
- **The fake LLM policy.** It gives an offer 0.5 of its mass when one is among its options, so a week draws enough
  offers to answer each way. This raises the offer's `μ` (below) to about 0.37. Without the lean, the builder's
  synthetic run measured 0.06-0.09.
- **Answers.** The drawn offers were answered in turn: Start, then "Not now", then moving on without an answer.
- **An accepted lesson** ran through the real handlers: `lesson.suggestion_respond` `accepted`, then `lesson.turn`
  `open` with `origin = router_suggestion`. A check was answered right, and the lesson landed and closed
  `goal_reached`. `lesson.activity` reported 12 foreground minutes and a 2-minute background gap.
- **The answer is scripted**, not drawn at `P(accept)`. The acceptance sensors are each offer's logged posterior.

| | arxiv_v2 | linear_algebra | probability |
|---|---|---|---|
| Objective decisions in the week (and on day 0) | 52 (1) | 64 (2) | 41 (1) |
| Decisions with an offer in the support, per day Nov 6-12 | 7, 6, 3, 8, 1, 3, 0 | 10, 10, 1, 14, 13, 6, 4 | 3, 3, 2, 11, 3, 4, 7 |
| Offers drawn, per day | 2, 3, 3, 3, 0, 1, 0 | 2, 3, 0, 2, 2, 3, 0 | 1, 1, 0, 3, 1, 1, 1 |
| Responses (one per decision; none with two) | 4 accepted, 4 declined, 4 ignored | 4, 4, 4 (and TE1b's day-0 card `ignored` at the next day's open) | 3, 3, 2 |
| The support with the offer | staged's top-k blocks, the offer, then stop (e.g. `new:…`×3, `lesson_offer:lo_trace_recursive_relu_folding`, `stop_for_today`) | e.g. `repair`×3, `maintain`×2, `new`, `lesson_offer:lo_orient_to_the_vector_space_idea`, `stop_for_today` | e.g. `new`×3, `repair`, `lesson_offer:…`, `stop_for_today` |
| `μ`(offer) when in the support: median (range) | 0.380 (0.372-0.396) | 0.364 (0.020-0.560) | 0.380 (0.364-0.396) |
| G3: `μ` recomputed from every logged trace (and the stop coin's served distribution) | 53 of 53 equal (1e-9) | 66 of 66 | 42 of 42 |
| Acceptance sensors of the drawn offers (posterior predictive mean; Beta matched) | 0.36-0.89 (sd 0.16-0.23) | 0.28-0.79 (sd 0.17-0.27) | 0.46-0.91 (sd 0.13-0.28) |
| Ceiling binds (3 a day, each logged `none:ceiling_bound`) | 19 | 4 | 5 |
| Decisions with forced items (a follow-up, a request, a randomized check) / with an offer beside them | 7 / 0 | 8 / 0 | 9 / 0 |
| Accepted lessons, and each next decision's clock (the trace's session minutes = the price's clock with lessons; without) | 4: 13.5 (1.5), 12.0 (0.0), 18.0 (6.0), 24.0 (12.0) | 4: 16.5 (4.5), 37.5 (25.5), 22.5 (10.5), 15.0 (3.0) | 3: 21.0 (9.0), 31.5 (19.5), 31.5 (19.5) |
| LOs with a pending lesson check in the population | none pending (TE1 marked each lesson's checks `missing`: no eligible item on that copy) | on 70 decisions, 138 of 138 pending LOs in the population | on 48 decisions, 48 of 48 |
| RO6's features version | `ro6_belief_features_v3_lesson` at the tag; one change point (day 0 -> day 1, censored `change_point`) | the same | the same |
| Generated probes written / served / served twice / refused when reopened | 17 / 17 / 0 / 17 of 17 | 33 / 33 / 0 / 33 of 33 | 21 / 21 / 0 / 21 of 21 |
| Offers taken back (`expired`) | 0 | 0 | 0 |

- **The clock.** Each accepted lesson added exactly its 12 foreground minutes to the next decision's clock (the
  2-minute gap not counted). The trace's session minutes equal the price's clock read with lessons.
- **The report.** The objective report's `lesson_offers` agrees with the table: 28, 58 and 33 decisions with an
  offer; 12, 12 and 8 drawn; 4, 4 and 3 lessons opened and closed; `μ` mean 0.382, 0.353 and 0.381.
- **Pass 1** (pre-speed) gave the same picture: 11, 14 and 10 offers drawn, G3 equal on every decision, no forced
  decision with an offer, every response single.
- **The probes.** No generated probe stranded inside an offer block or was served twice.

**The deadlines on real copies.**
- **Setup.** Main at mvp-0.52 against the branch at mvp-0.53 (switch on), three days each, the same seed and
  learner. Next was pressed right after feedback (0 s) or after a 3 s dwell.
- **"Next at a boundary"** is every Next that crossed a block boundary, item or not. Medians, p90 and the share
  above 2 s are in ms.
- **The paths diverge.** The sessions differ once an offer is in the support, so the n differ.
- **Load.** The machine's 1-minute load average is given per row.

Pass 1, branch with the offer-build spans (load about 3):

| Copy | Next after | Side | Next at a boundary (median, p90, >2 s) | Numeric policy per decision (median, p90, >2 s, max) |
|---|---|---|---|---|
| arxiv_v2 | 0 s | main | 2090, 3590, 6/10 | 2238, 3129, 5/9, 3255 |
| arxiv_v2 | 0 s | branch | 3640, 4728, 8/10 | 2921, 5814, 8/10, 6656 |
| linear_algebra | 0 s | main | 2178, 3678, 19/36 | 1460, 2030, 4/30, 2951 |
| linear_algebra | 0 s | branch | 3794, 4858, 23/36 | 1631, 2422, 9/28, 2942 |
| probability | 0 s | main | 1845, 2508, 9/18 | 743, 863, 0/15, 1474 |
| probability | 0 s | branch | 2037, 2459, 7/13 | 719, 898, 0/11, 1284 |
| arxiv_v2 | 3 s | main / branch (load 7) | 638 / 1176, 3861 / 5253, 2/10 / 4/10 | 2266 / 2976 |
| linear_algebra | 3 s | main / branch (load 8) | 822 / 1001, 1131 / 1910, 0/36 / 4/36 | 1390 / 1689 |
| probability | 3 s | main / branch | 698 / 721, 900 / 931, 1/18 / 1/13 | 708 / 723 |

Pass 2, on the speed merge (load about 2.5 for arxiv_v2 and linear_algebra at 0 s; 9 to 12 for the rest):

| Copy | Next after | Side | Next at a boundary (median, p90, >2 s) | Numeric policy per decision (median, p90, >2 s, max) |
|---|---|---|---|---|
| arxiv_v2 | 0 s | main | 2537, 3135, 5/7 | 1970, 2777, 2/5, 2820 |
| arxiv_v2 | 0 s | branch | 1889, 3789, 10/21 | 843, 2494, 5/25, 3050 |
| arxiv_v2 | 3 s | main | 527, 3153, 2/7 | 1986, 2749, 2/5, 2783 |
| arxiv_v2 | 3 s | branch | 856, 3755, 5/21 | 709, 2437, 5/25, 3113 |
| linear_algebra | 0 s | main | 2698, 3686, 13/24 | 1196, 1641, 0/16, 1765 |
| linear_algebra | 0 s | branch | 1008, 4665, 4/9 | 1415, 2257, 2/4, 2285 |
| linear_algebra | 3 s | main | 961, 1162, 0/24 | 1385, 1691, 0/16, 1984 |
| linear_algebra | 3 s | branch | 1024, 1451, 0/9 | 1452, 2607, 2/4, 2644 |
| probability | 0 s | main | 2505, 3040, 8/13 | 886, 959, 0/12, 1943 |
| probability | 0 s | branch | 2602, 3377, 7/12 | 883, 1138, 0/11, 1865 |
| probability | 3 s | main | 813, 1240, 1/13 | 894, 945, 0/12, 1003 |
| probability | 3 s | branch | 1176, 1299, 1/12 | 875, 990, 0/11, 1201 |

- **The offer's own cost** at a boundary, median: its build 81-200 ms, of which TE1b's candidates are 63-203 ms, the
  check mass 4-8 ms and the Beta under 1 ms.
- **The cost before the speed stage.** The pre-speed branch's boundary was about 1.5 s slower at the median on
  arxiv_v2 and linear_algebra (pass 1), mostly in the numeric policy. That is one more valued action (the lesson with
  its sampled duration and committed check), deadline-bound as R2 says.
- **The worst decision.** The slowest numeric decision seen was 7.96 s on the first, more loaded arxiv_v2 run, under
  `router.timeout_seconds` 8 s. With the speed stage merged, the arxiv_v2 branch's numeric median fell to 0.7-0.8 s.
- **The LLM card's size.** The card's JSON is held to `llm_card_token_budget` (48 000, compared in bytes).
  - linear_algebra: the card hit the budget on every decision on both sides (main 47 963 bytes max, 14 of 14
    trimmed; branch 47 881, 4 of 4).
  - probability: under the budget (branch 44 566, main 33 867).
  - arxiv_v2: small (branch 13 745, main 3 163).
  - The whole request was up to 51 086 bytes.

**Below the tag, and at the tag with the switch off** (Today, TE1b's daily card, every Next, the follow-up gate,
every router LLM and Decider request, every written row; one day, seed pinned, the second item missed with FG1's
follow-up, the first stop declined):
- **Below the tag:** identical to main on all three copies in every pass, with nothing set aside, but for one run:
  - In pass 2, probability's first main run differed from the branch's.
  - A second main run differed from main's own first run and was identical to a second branch run.
  - So that was main's run-to-run variation under load (about 8), R2's deadline-bound refinement.
- **At the tag with `in_objective = false`:** identical to main on all three copies in every pass, with these set
  aside on both sides:
  - R2's two named keys: the boundary key's version string (`SMOKE_PIN_KEY`) and the trace's generator key.
  - **A third version-named seed.** TE1b's daily draw seeds its uniforms from a snapshot hash whose inputs include
    `algorithm_version` (`lesson_suggestion.today_suggestion`, main's code). Without it set aside, linear_algebra's
    TE1b card was drawn and shown with the same candidate at the same propensity, and only its logged `u1`/`u2`
    differed.
  - The receipts' config record, which now carries the `in_objective` key itself.
  - Main's copies were opened once on main code before driving, as the branch's were. Pass 1's first try did not,
    and RO0's `seen_at_load` goal row was then written at different times.
- **Rebuild.** `rebuild --shadow` after each week (lessons included) changes facet 0 and schedule 0. Mastery changes
  only by the `algorithm_version` stamp (mvp-0.47 -> mvp-0.53: 5, 14 and 9 rows), with nothing beyond the stamp.
- **Survival.** The objective's traces, every router decision, every suggestion response, RO5's assignments, the
  lessons, their receipts and their activity intervals are the same before and after `rebuild-derived-state` and a
  state sync, on each copy.
- **Calls and processes.**
  - No new `model_call_receipts` from a real model: every new row names a fake model.
  - The socket watch logged no connect, no non-loopback address and no resolve, over 257 subprocess records across the three passes.
  - The only subprocesses were `powerprofilesctl get` and `git -C <archived tree>`. No Codex process ran.

### What the owner runs after the fast-forward

For each vault (`~/learnloop-vaults/<name>`), once the earlier records' steps are done (mvp-0.52):

```
learnloop upgrade --vault ~/learnloop-vaults/<name>        # mvp-0.52 -> mvp-0.53 (the default); no migration
```

Then rebuild the desktop app and restart the phone host, as for every landing. A vault still at an older tag reaches
mvp-0.53 through the chain with the same command.

To turn lesson offers off in a vault (TE1b's Today-open card returns; the objective serves mvp-0.52's support), add
to its `learnloop.toml`:

```
[router.lesson_suggestions]
in_objective = false
```

Flipping it is a change point for RO6 (R4), and it also moves the realized cost of closed windows that held a lesson.

### Open items

- **TE1b's daily-draw seed names the algorithm version** (the third key above). With the switch off at the tag, the
  card's uniforms differ from mvp-0.52's, as the boundary key's noise does. The card served in the smoke was the same.
  This is for the orchestrator to add to R2's named keys or to send to the follow-up batch.
- **Next at a boundary.** Before the speed stage it was about 1.5 s slower at the median on arxiv_v2 and
  linear_algebra with offers on. The numeric policy's slowest decision was 7.96 s against the 8 s timeout, under load.
  Worth a look once the speed stage is on real vaults.
- **The LLM card.** It is at its 48 000-byte budget on linear_algebra on both trees. The budget is compared in
  bytes, though it is named a token budget.
- **A phone-crossed boundary can draw a second offer** while one waits for the desktop. An offer waiting for the
  desktop is neither ended nor answered, so the next boundary does not sweep it. The ceiling bounds the count.
- **R3's five items** go to the follow-up batch, as ruled.
- **Known flakes, both passing alone.** `test_rofu_carried::test_an_early_publication_served_keeps_its_carried_valuation`
  (timing under load) and `test_ro0_rows9_13_decision_state::test_receipts_hold_ids_and_numbers` (a two-letter LO
  title inside a random id).
- **The earlier open questions above stand.**
