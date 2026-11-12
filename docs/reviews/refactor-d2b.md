# Refactor D2b (part 1): tests that name old tags

Step D2b of arc D (`docs/specs/refactor_strategy_v3.md` §2.6), on branch `refactor/d2b-old-tag-tests`, based on main `72ace2968a` (D2a landed: `create_basic_vault` builds at the head, `mvp-0.58`, and D2a pinned its old-path tests with `tests.helpers.pin_old_basic_vault`).

Rules held: no change under `src/`; no live model call; no migration; no identity pin moved (`tests/test_identity_pins.py` passes unchanged); no assertion edited to what the code says without reading why (each difference below says why); no test deleted. K3.4's and K3.5's files are untouched.

This is **part 1**. Batches 1-4 finish D2a's pins and helper items; batches 5-6 re-tag two shared builders that named an old tag only to get a feature (a third, `create_daily_plan_vault`, was tried and reverted: §5). The rest of D2b proper (single test files that call `set_algorithm_version` or name a tag at or below `mvp-0.42`) is too large for this landing and is listed in §8.

## 1. Summary

| | count |
|---|---|
| D2a's old-vault tests (its §5; parametrized cases counted, as D2a did) | 113 |
| ported to the head path (same behaviour asserted) | 33 |
| moved off the old vault onto the head with their kill switch off (predecessor tests; D7 removes them with the switch) | 35 |
| still on the old vault, each waiting on a tag (no switch) | 45 |
| deleted | 0 |
| re-tagged to the head through a shared builder (batches 5-6): `split_vault`'s default (114 call sites in 74 files) and the two source-set synthesis builders (31 files) | 105 files |
| findings (strict xfail) | 1 |

One test D2a did not list was passing vacuously at the head and now tests its subject (`test_tutor_promotion_w2::test_core_recall_gap_on_solid_facet_still_applies`, §3 batch 2); one D2a did list as vacuous (`test_deferred_regrade_validates_repaired_trace_against_learner_answer`) tests its subject again on the head with its switch off.

## 2. New and changed test helpers

- `tests/http_provider_double.py`: `serve_structured(monkeypatch)` turns one test's `HttpProviderDouble` into a structured, isolated transport. `execute_structured_operation` never sends a legacy endpoint adapter an isolated turn, so the double could not be a split vault's learner-blind grader. Under `serve_structured` each request's context is read back from the prompt envelope (`render_structured_prompt` appends `{"context": ...}`, the same `prompt_safe` value the legacy adapter posted) and posted to the operation's endpoint; the blind grader posts its `BlindGradingContext` (rubric, ids, answer; no history) to the server's joint grading endpoint and the joint answer is cut to the blind contract, as `structured_ai.JointGraderAlsoBlind` does for in-process fakes. A purpose with no endpoint (the diagnoser) is refused before any request. Opt-in per test, so the 20 files that use the double's legacy form are unchanged.
- `tests/canonical_facet_helpers.py` (new): `seed_canonical_facet_recall(repository, facet_id=, mean=, mass=, ...)` writes one canonical recall cell through `Repository.replace_canonical_facet_state`, the projection's own writer, keeping every other cell and every capability row. D2a's §5 suggested building canonical state from real observations instead, because a re-projection overwrites seeded rows. I did not: the legacy seeds these tests used were equally a derived cache that a rebuild rewrites, and the readers under test (goal projection, measurement labels, the scheduler's facet boundary, the band planner, tutor gap signals) take the belief as input; producing an exact mean and mass from observations is not possible with one item (independent mass is per surface group) and would have rewritten every scenario. Every port seeds after the last step that re-projects (the one test that submits an attempt, `test_known_gap_facet_is_never_on_track`, stays pinned for another reason). Two ports were checked to depend on the seed (removing it fails the band test and the transfer-gap test); the others assert numbers only the seed can produce (`current_recall == 0.95`, the measured label, the canonical id in the ability vector).
- `tests/helpers.py`: `set_config_switch(root, "table.key", value)` sets one boolean inside its table whether or not the template renders the table (checked by parsing); `seed_due_item(paths, version=...)` stamps its mastery row with a given tag.
- `tests/probe_episodes_helpers.py`: `_setup(switched_off=...)` and the fragments `VOI_STOPPING_OFF`, `PLACEMENT_OFF`.
- `tests/split_live_helpers.py`: `split_vault` sets its tag before seeding the history (batch 4) and defaults to the head (batch 5).
- `tests/source_set_synthesis_helpers.py`: `_setup` and `_setup_two_chapters` keep the head tag `init_vault` writes instead of rewriting it to `mvp-0.7` (batch 6; `mvp07=False` still pins `mvp-0.6` for its one legacy test).

## 3. D2a's pins, test by test

"Port" asserts the same behaviour on the head path. "Switch" runs the test on the head vault with the named kill switch off, because its subject is the predecessor that switch serves exactly; it no longer needs the old vault, and D7 deletes it with the switch. "Old vault" keeps `pin_old_basic_vault` because only a tag (no switch) restores its path.

### Batch 1: the HTTP double (`24bbd5bcc5`)

| test | action | why it now asserts what it does |
|---|---|---|
| test_sidecar_teach_back:: conversation_checkpoints_and_grades, finish_early_grades_only_asked_criteria, finish_under_manual_grading_is_typed_and_preserves_checkpoint, finish_survives_post_step_failure, finish_retry_returns_same_attempt, from_a_queue_offer_links_the_graded_attempt (6) | port | `serve_structured`: the head grades the transcript blind through the double. Assertions unchanged, including that the grading request's rubric holds only the asked criteria (the blind context carries the same rubric) |
| test_cli_attempt::test_cli_attempt_uses_codex_http_when_runtime_ready | port | same |
| test_sidecar_tutor_qa::test_sidecar_submit_attempt_counts_question_hint_equivalents | port | same |
| test_field_signal_production_paths::test_practice_screen_payload_marks_help_before_work (3 params) | port | same |
| test_model_call_receipt_owners::test_each_cli_run_is_its_own_owner, ::test_tui_grading_records_receipts_with_usage | port | same; the receipts carry the server's reported usage as before |
| test_tui_feedback::test_feedback_submit_uses_codex_grading_when_runtime_ready | port | same |
| test_deferred_regrade::test_startup_maintenance_regrades_pending_self_grade_when_codex_ready | port | same (the regrade is blind) |
| test_sidecar_contract::test_sidecar_canonical_codex_profile_wins_when_legacy_input_differs | port | same |

16 ported.

### Batch 2: facet-belief readers (`08aa9f3722`)

| test | action | why |
|---|---|---|
| test_goal_projection:: solid_facet_above_target_no_decay_info_is_on_track, solid_facet_decays_below_target_lands_on_frontier, projection_is_monotonically_non_increasing_with_horizon, high_mastery_low_mass_is_on_track_but_uncertified_and_at_risk, attempts_to_certify_inverts_the_mass_equation, decayed_certified_facet_reports_a_floor_not_zero, attainment_aggregates (7) | port | the goal report reads facet belief through `facet_state_reader` (canonical at the head); the same mean and mass are seeded in the canonical cell the basic item observes (`schema_interpretation`), so every number asserted is unchanged |
| test_measurement_state_labels:: measured_label…, sub_threshold_direct_mass…, capability_grid_labels_the_ready_number, labelling_writes_nothing, label_does_not_move… (5) | port | same seed; the capability grid reads the canonical belief too |
| test_difficulty_band_guards::test_diagnostic_plan_band_is_never_degenerate | port | canonical seed alpha 0.2 / beta 9.8 / mass 4.0; the band is (0.0, 0.10) as before (without the seed it is (0.46, 0.54)) |
| test_scheduler::test_scheduler_selects_item_on_weak_canonical_facet_boundary | port | each facet's canonical belief seeded under the canonical id the projection resolves aliases to (the item still names the alias, which the demand vector canonicalizes, as asserted) |
| test_tutor_promotion_w2::test_transfer_gap_on_solid_facet_is_skipped | port | canonical seed; its sibling `test_core_recall_gap_on_solid_facet_still_applies` had been passing vacuously at the head (its legacy seed was ignored, so the facet was not solid) and now reads the seeded belief too |
| test_recall_coverage_interventions::test_second_same_facet_failure_counts_across_different_items | port | the VOI minutes seam (`voi_stopping_helpers._minutes`, as D2a used for the same rule) keeps the repeated-failure follow-up on the head path; the severity trace key is KM4's `retrieval_failure` |
| test_facet_diagnostics_v03::test_subthreshold_noisy_item_creates_single_facet_generation_need_and_logs_slate | old vault | D2a blamed the VOI gate; the real cause is that the overlap gate (`gate_applies` in `select_followup`) needs per-LO facet uncertainty states, which the head never reads. With the minutes pinned low the noisy item passes and is served. Dead at the head (D2a finding 5's seam) |

16 ported (+1 vacuous sibling repaired).

### Batch 3: predecessors behind a kill switch (`d5aaa1de3c`)

Each "switch" test failed at the head with the switch on (D2a's runs; re-checked here for `hints.fold_follows_attach` and `diagnosis.split_enabled`) and passes with it off.

| test | action | switch (D7) |
|---|---|---|
| test_teach_back::test_scheduler_caps_teach_back_items_per_queue | switch | `voi_stopping.enabled` |
| test_probe_episodes:: two_independent_surfaces_complete_a_stable_episode, next_probe_item_peeks_the_unused_surface_without_committing, exhausted_instrument_pool_parks_episode_with_generation_need | switch | `voi_stopping.enabled` |
| test_probe_episodes:: missing_instruments_park_episode_with_one_deduplicated_need, pending_items_episode_keeps_lo_schedulable_with_belief_updates, scheduler_slate_atomically_commits_its_selected_probe_presentation | switch | `placement.enabled` |
| test_scheduler_probe_eig::test_probe_eig_uses_prospective_familiarity_discount | switch | `voi_stopping.enabled` (the discount is head code; only the stop rule's predecessor runs) |
| test_probe_block_end::test_block_end_releases_feedback_and_routes_ordinary_practice | switch | `voi_stopping.enabled` |
| test_probe_orchestration_remainder::test_session_cap_blocks_further_probe_serving | switch | `voi_stopping.enabled` |
| test_state_sync:: enters_probe_for_new_active_goal_learning_object, …without_goal, …when_practice_item_arrives_after_learning_object (3) | switch | `placement.enabled` |
| test_probe_instance_generation (3), test_probe_llm_instances:: gate_rejected…, provider_failure…, llm_surfaces_config_disable (3), test_probe_longform_families::test_generation_produces_derivation_instance_with_obligation_rubric | switch | `followup.generate_and_serve` |
| test_irt_end_to_end::test_fsrs_interval_factor_stretches_on_positive_surprise, ::…compresses_on_negative_surprise | switch | `scheduler.surprise.remove_interval_factor` (false) |
| test_daily_loop_reentry_cap::test_reentry_session_serves_exactly_the_refreshers_the_panel_shows | switch | `plan.enabled` |
| test_reader_rw1c_review::test_a_cold_bound_ask_is_a_hint_whatever_its_type_and_its_cold_row (4 params) | switch | `ask.cold_help_converts` |
| test_hint_h2b_fix3::test_r1_f10_an_interrupted_answer_box_attach_never_lets_a_problem_take_the_hint | switch | `hints.fold_follows_attach` |
| test_ux_phase4_landing::test_a_cold_check_on_a_direct_open_is_served_as_on_main_unless_a_routine_display_covers_it | switch | `eligibility.enabled` |
| test_contract_commissioning::test_legacy_learning_object_keeps_the_mastery_band_rung | switch | `adaptive_difficulty.generation_contract` |
| test_cli_generate_practice::test_populate_goal_dry_run_waives_probe_gate_and_ignores_reserved_supply | switch | `adaptive_difficulty.generation_contract` |
| test_diagnostic_augmentation::test_a_receipt_that_cannot_be_written_commits_no_augmented_grade | switch | `diagnosis.split_enabled` (restores the joint door, Q14's subject) |
| test_diagnosis_input_provenance_landing::test_q14_on_a_vault_the_coordinator_upgrades_the_receipt_commits_with_the_grade | switch | `diagnosis.split_enabled` |
| test_deferred_regrade::test_deferred_regrade_validates_repaired_trace_against_learner_answer | switch | `diagnosis.split_enabled`. D2a noted it passed at the head only because the blind grade drops the repair; with the joint grader back it tests the validation again |
| test_sidecar_contract::test_sidecar_counts_queued_intervention_followups_in_session_summary | switch | `stuck_prompt.enabled`, `followup.generate_and_serve` and `voi_stopping.enabled` (all three predecessors; with only the first two off the VOI price still declines) |
| test_attempt_completion::test_resumed_completion_routes_to_the_episode_the_attempt_was_applied_under | port | the route recovery is head code; `placement.initial_probes` (placement's narrower switch, as D2a's group C ports) keeps the opening episode servable |
| test_probe_episodes::test_budget_exhaustion_completes_episode | old vault | with `voi_stopping.enabled` off the mvp-0.8 robust gate (a pinned calibration channel, no switch) still ends the episode first (`couldnt_reliably_distinguish`) |
| sim_probe_validation_helpers (test_sim_probe_validation × 2, test_ux_phase4_feedback::test_f1l_the_sim_skips_a_covered_instrument_instead_of_aborting_the_run) | old vault | with `placement.enabled`, `followup.generate_and_serve` and `voi_stopping.enabled` all off the sim runs on the head but diagnoses `surface_only` 2 times in 5 (tag-gated rules differ) |

35 switch, 1 ported.

### Batch 4: helper open items (`98518b9cc6`)

- `split_vault` seeds its history after setting its explicit tag, so the seeded rows are what a vault at that tag records (74 importing files: all pass unchanged).
- `seed_due_item(paths, version=...)`; the three old-vault tests that seed it (`test_goal_projection`/`test_goal_frontier`'s `_loaded_old_path`, `test_ux_phase4_feedback::test_f5_…`) pass `OLD_BASIC_VAULT_TAG`, and `test_facet_diagnostics_v03._wrong_attempt` stamps the loaded vault's own tag, so these old-vault seeds are the pre-D2a ones again. Other files seeding `MasteryState(..., ALGORITHM_VERSION, ...)` run on the head and stamp the head tag, which is right for them.

### Still on the old vault (45)

Each comment names the tag; none has a switch that restores its path.

| tests | waits on |
|---|---|
| facet uncertainty readers, dead at the head (the `facet_uncertainty_states_for_lo` KM4 seam): test_teach_back::test_plan_orders_uncertain_core_first_then_escalates, ::test_plan_reserves_final_slot_for_transfer_when_core_would_crowd_it_out; test_goal_frontier::test_known_gap_and_uncertain_facets_are_both_on_frontier; test_goal_projection::test_known_gap_facet_is_never_on_track; test_facet_diagnostics_v03 (5: single_facet_probe…, open_facet_restriction…, hedged_learner_confidence…, facet_uncertainty_rebuilds…, mastery_diagnostic_view…) and ::test_subthreshold_noisy_item… ; test_predictive_eig::test_followup_slate_logs_predictive_fields_and_ranking_unchanged_at_weight_zero; test_recall_coverage_interventions::test_high_unfamiliar_probe_posterior_records_intervention_need (12) | D5 (pre-canonical path and the uncertainty writers), or a KM4 successor that reads uncertainty canonically (owner) |
| legacy per-LO facet masses: test_recall_coverage_interventions::test_dont_know_keeps_full_coverage_and_updates_facet_recall (D2a finding 7); test_doctor::test_doctor_fix_state_merges_registered_facet_alias_state (doctor's mvp-0.6 alias merge) (2) | D5 |
| an mvp-0.6 vault or an upgrade from it, by name: test_km2_activation (7), test_p0_cutover_mvp08 (2), test_km1_doctor (2), test_km4_taxonomy (3), test_generated_item_gate::test_legacy_vault_allows_unregistered_facet, test_value_candidates::test_below_the_robust_cutover_instruments_are_ordinary_items, test_assessment_contracts::test_legacy_attempt_records_no_observation_lineage (17) | D3 (the upgrade table) / the floor (D1) |
| below mvp-0.7 (contracts) or mvp-0.8 (P0): test_regrade_contract_successor::test_a_first_grade_made_before_contracts_keeps_its_compatibility_reading, test_ux_phase4_feedback::test_f5_an_answer_with_no_contract_is_unrecorded, test_family_memory_projection::test_dont_know_is_an_observed_failure_review, test_probe_episodes::test_budget_exhaustion_completes_episode, the planted-type sim (3) (7) | the floor (D1/D3) |
| immediate misconception normalization (KM's promotion discipline from mvp-0.7): test_misconception_registry (7) | D3; retire with the tag, or port to candidates (their subject would change) |

Not counted as pins: `test_roles_switch_off`, `rw2c_base_sequence` and `rw5c_golden_source` keep their fixed `mvp-0.6` input on purpose (cross-commit identity goldens, D2a §3 D).

## 4. Findings (strict xfail, named `D2b finding:`)

1. **A diagnose drain's dry run under-counts retrieval embeddings when recurrence groups are on** (`test_diagnosis_reports::test_retrieval_embeddings_are_admitted_and_charged_on_the_command_budget`). From `mvp-0.12` (recurrence groups, on at the head) the run makes one more embedding request than the dry run estimates (3 against 2); bisected over tags (passes at `mvp-0.11`, fails from `mvp-0.12`) and confirmed with `recurrence.enabled = false` at the head (passes). The command's admission estimate is meant to be a ceiling (the test's last assertion); at the head it is not, so a budget sized from the dry run can be exceeded by one embedding.

Facts recorded, not xfailed:
- The follow-up overlap gate (`subthreshold_overlap`, `missing_dominant_facet`) never applies at the head: it needs per-LO facet uncertainty states (D2a finding 5's seam). A noisy item a predecessor vault filtered is served as a follow-up at the head.
- The planted-type probe simulation, with all three predecessor switches off at the head, completes episodes but diagnoses `surface_only` correctly 2 times in 5; its checkpoint gate needs 0.6. The sim's honest head report is a design question for D7 (the sim needs the opening episode and parametric instances, both predecessors).

## 5. Batches 5-6: shared builders that named an old tag

**Batch 5 (`a9fa7f47f1`): `split_vault` defaults to the head.** `split_live_helpers.split_vault` defaulted to `mvp-0.10`, named only to get a split vault (its docstring: "a graded vault"); the head keeps the split. 114 calls use the default. Run over its 74 importing files: 9 failures, each read:

| test | head difference | action |
|---|---|---|
| test_grading_support::test_live_blind_grade_records_grading_support_and_its_calibration_identity | the head grades with the method-explicit successor's rules, whose suffix (`grading_support.METHOD_ROUTE_RULES_SUFFIX`, `+own-route-v2`) names the prompt and the calibration identity whether or not the item has a required method (its constant's comment) | port: expect the suffixed identities |
| test_diagnosis_card (6: submit_reports_pending…, card_tap…, forwarding…, not_same_mistake…, repairs_first_displayed…, card_kill_switch…) | from mvp-0.45 (FG1 §6.0) a miss opens the follow-up workflow, which holds the card (`diagnosis_status` answers `pending`) until the follow-up is answered or shown anyway; the diagnosis itself completes | port: `_Sidecar.diagnose` runs the worker, then takes `followup_show_anyway` (as D2a ported the phone's full-answer display); every card assertion unchanged |
| test_stuck_prompt::test_cli_refuses_stuck_where_it_is_not_offered | its subject is "not offered", which it got from the old default tag | switch: `stuck_prompt.enabled` off on the head (D7) |
| test_diagnosis_reports::test_retrieval_embeddings_are_admitted_and_charged_on_the_command_budget | finding 1 | strict xfail |

Then 1,804 passed, 3 xfailed over the 74 files. I also scanned the default users' test names for an old-tag subject (legacy, predecessor, switch, joint, before...): the 20 hits are switch tests that set their switch themselves, or seed old rows by hand; none had relied on `mvp-0.10`.

**Batch 6 (`446ddb879f`): source-set synthesis.** `source_set_synthesis_helpers._setup` and `_setup_two_chapters` rewrote `init_vault`'s head tag down to `mvp-0.7`, named only for a canonical-state vault. They keep the head now; `mvp07=False` still pins `mvp-0.6` for `test_source_set_synthesis::test_legacy_vault_acceptance_refused`. 31 importing files: 553 passed, no change needed.

**Tried and reverted: `create_daily_plan_vault` at the head.** Its default is `mvp-0.14` (up to 81 call sites name no version on their first line; 46 files use the builder). At the head, 29 tests in 11 files fail (`test_daily_plan_review_regressions` 8, `test_ux_phase4_feedback` 4, `test_daily_plan_reading` 4, `test_mobile_v4_plan` 3, `test_daily_plan_build` 3, `test_daily_plan_owner_decisions` 2, and one each in `test_mobile_two_process`, `test_mcp_tools`, `test_mcp_c1a_narrow`, `test_daily_plan_kill_switch`, `test_block_chooser_interface`). The causes were not read (the plan's later successors, the router objective, AD selection, IH's lessons and phone V2-V4, are the likely ones); reading 29 differences is a batch of its own, so the default stays `mvp-0.14` here and the list is D2b part 2's first item (§8).

## 6. Counts and timing

- Landing selection on `446ddb879f` (all six batches): 856.8 s wall (14:17), 30,896 collected. For reference, D2a's run 2 took 826.9 s on its tip; the difference is inside run-to-run spread and no base run was made. The ported tests run the head path; the switch tests run the head with one switch off; neither adds a fixture of note (`serve_structured` adds one local HTTP round trip per graded request, as the legacy double already did).
- Durability lane: 178.3 s (D2a: 166.7 s).
- Targeted runs while iterating: each batch's files plus every importer of a changed helper (batch 3: 969 tests in 27 files, 55 s; batch 4 and 5: the 74 `split_vault` files, about 2 min each; batch 6: 31 files, 22 s).

## 7. Gates run

- Landing selection, `flock /tmp/learnloop-fullsuite.lock`, 10 GB scope, `-n 8 --dist worksteal -m "not arc_close" -p no:cacheprovider`, empty-home wrapper, on `446ddb879f`: **1 failed, 30,775 passed, 104 skipped, 16 xfailed** (D2a's 15 plus finding 1). The failure, `test_instruct_handoff_ih1::test_no_new_draw_joins_an_open_item` (`'done' == 'item'`: the first plan decision drew a stop), is a flake in a file and helpers this step did not touch (`router_mixture_helpers`, `te3b_offers_helpers`; `tests/helpers.py` only gained a function and a keyword with the old default): it passed 3 of 3 alone and 5 of 5 as a whole file under xdist. It fits D2a §7's open item (the head's seeded arms on fresh ids, here RO5's stop coin); not chased here. One of three allowed landing runs used.
- Durability lane, `-m durability -n 4`, 5 GB scope: 417 passed, 1 skipped.
- Arc-close lane: not run (no `arc_close` test was touched; checked by grepping the changed files for the marker).
- `tests/test_identity_pins.py`, `test_architecture`, `test_test_layout`, `test_cli_help_snapshot`, `test_effective_defaults_golden`, `test_vault_template`: 254 passed. No identity pin moved.
- `ruff check`: clean. `lint-imports --no-cache`: 42 kept, 0 broken. `scripts/check_gate_partition.py`: 30,956 collected, landing 30,896 + arc_close 60.
- Vault: the Testing note (`Architecture/Testing and Invariants.md`) states the switch-off convention and the two new helpers (batch 6). References regenerated once after the test commits (`_scripts/generate_all.py`: 21 generated notes changed, test lists of the modules, tables and config fields whose tests D2b edited, plus `_generated.md`'s rows at `446ddb879f`), committed as `42e7415bc8`; a second run on the clean tree changed nothing (a fixed point). The four validators: `db_validate_reference.py`, `module_validate.py`, `desktop_validate.py` and `validate_vault.py` all pass.
- Not run (the orchestrator's): `--fresh-connections`, vitest.

## 8. Open items

For **D1**: `pin_old_basic_vault` must be retired before the floor is enforced. **45 tests** remain on it (§3, last table); all wait on a tag: 17 on D3 (an mvp-0.6 vault or its upgrade by name), 14 on D5 (legacy per-LO facet state; 12 of them read facet uncertainty, dead at the head), 7 on misconception normalization (D3), 7 on tags below mvp-0.7/mvp-0.8. None waits on a switch. The 35 switch tests no longer hold D1 back; D7 removes them with their switches (it must also delete or port them, since each runs the off-branch).

For **D2b part 2** (the strategy's D2b proper, not done here):
- `create_daily_plan_vault`'s default (`mvp-0.14`): the 29 head-path differences of §5, to read one by one.
- Single test files that call `set_algorithm_version` with an old tag, or name a tag at or below `mvp-0.42`: by a fresh count at this tip, 129 test files call `set_algorithm_version` and 231 put a quoted tag at or below `mvp-0.42` in code (comments excluded), 263 files in all (the strategy's 190 counted differently). Many are upgrade or successor tests whose subject is the old tag (D3/D7's), many name a tag in a comment only; each needs reading.
- `create_placement_vault` still defaults to `mvp-0.11` (2 default call sites; the rest pass explicit tags, mostly the predecessor of a successor test).
- `test_source_set_synthesis::test_legacy_vault_acceptance_refused` (`mvp07=False`, mvp-0.6 by name): D3.

For **D7**: the 35 switch tests of batch 3 (switches: `voi_stopping.enabled`, `placement.enabled`, `followup.generate_and_serve`, `scheduler.surprise.remove_interval_factor`, `plan.enabled`, `ask.cold_help_converts`, `hints.fold_follows_attach`, `eligibility.enabled`, `adaptive_difficulty.generation_contract`, `diagnosis.split_enabled`, `stuck_prompt.enabled`), plus `test_stuck_prompt::test_cli_refuses_stuck_where_it_is_not_offered` (batch 5), plus D2a's 15 `placement.initial_probes` ports and 8 `[plan] enabled = false` router tests.

For the **owner**: finding 1; whether facet uncertainty should be read canonically (14 dead-at-head tests, D2a finding 5).
