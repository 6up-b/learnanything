# Refactor D2b (third pass): the tests that still name old tags

Step D2b's third pass, on branch `refactor/d2b-third-pass`, based on main `245f8cbd09` (floor `mvp-0.58`, head `mvp-0.67`; D4, D5, D6 and D7's first batches landed since the second pass, `docs/reviews/refactor-d2b4.md`). Tests and test helpers only: nothing under `src/` changed, no migration, tag or config change, no test deleted, no test function renamed, no golden regenerated, no assertion changed. The method is the earlier passes' (census, experiment, classification, edit by helper), with one difference: the tags counted are every tag below the head, not only those below the floor, because the successors `mvp-0.59` to `mvp-0.66` have their own test vaults now.

## 1. Summary

| | before | after |
|---|---|---|
| test cases that write or open a vault at a tag below the head (census, 589 candidate files run) | 2,493 in 289 files | 2,043 in 269 files |
| of which (disjoint, in this order): in a successor, upgrade, migration or golden file (a) | 521 | 521 |
| fail at the head when the tag is taken there: the tag is load-bearing (a) | 527 (520 by the experiment, 7 more by the real run, §2) | 527 |
| tag-parametrized arms (a) | 316 | 315 |
| the tag is written another way (`set_config`, a hand-written config, a copied fixture): not sorted (c) | 247 | 247 |
| pass at the head; the test names the tag, a predecessor or a switch (a) | 246 | 246 |
| pass at the head; nothing in the test names it | 636 | 187, not moved (c), §4 |
| moved to the head by this pass | | **450 cases** (351 clean, 98 that named a feature word, 1 parametrized) in 42 files |
| static uses of an old tag string or old `*_ALGORITHM_VERSION` name in `tests/*.py` (comments and docstrings excluded) | 1,533 in 346 files | 1,513 in 335 files |
| assertions changed | | 0 |
| ledger rows | | 0 |

No case appeared in the after census that was not in the before census (checked: 0 new node ids in the 103 re-run files).

## 2. Method

- **Static scan** (scratch `inventory_scan.py`): every string token of `tests/*.py` holding `mvp-X.Y` below the head (not followed by another word character, so `mvp-0.7-source-set-synthesis-bootstrap` and other prompt versions are not tags) and every name of `learnloop.algorithm_versions` ending `_ALGORITHM_VERSION` whose value is below the head; comments and docstrings excluded. It counts names, not vaults: row stamps (`algorithm_version="mvp-0.1"` passed to a repository writer), tag constants asserted (`SUCCESSOR_CHAIN[...] == "mvp-0.36"`), upgrade tables and identity pins are uses too.
- **Census and experiment** (scratch pytest plugin, not committed). It replaces the code of `tests.helpers._set_algorithm_version_at`, the one writer `set_algorithm_version`, `pin_old_basic_vault` and every builder reach (a code swap, so imports by name are covered too), records each tag below the head a test writes and the call stack's test-file frames, and records every vault the loader opens below the head (`learnloop.vault.loader.refuse_below_floor` wrapped). With the experiment on, every tag below the head that writer is given is written as the head instead, and `pin_old_basic_vault` returns its vault unchanged. Candidates: the 310 test files the static scan names, the 265 test files that import (at any depth) one of the 38 helper modules it names (`helpers`, `successor_switches` and `identity_pins_helpers` left out as seeds, since every file imports `helpers`), and the 14 more that call a tag writer by name: 589 files, run in 6 chunks at `-n 1`, `-m "not arc_close"`, under the 3 GB scope, about 76 minutes in all. No test that writes no old tag failed under the experiment (0 of the untouched cases), so the run is a clean sort.
- **Sort, per test**: failing at the head: (a). Passing: (a) when the file is a successor, upgrade, migration or golden file, when the case is parametrized over tags, or when the test's name or body names the tag, a predecessor, a switch, an upgrade or legacy history (the D4/D6 rule: a predecessor keeps its old tag beside the switch that now serves it); otherwise a move candidate, read before it moved.
- **Limit of the experiment**: it only moves what the shared writer writes. A builder that also reads its `version` argument itself is still served the old tag. One such reader exists: `learner_text_gaps_helpers.serve_pre_tier1` turns the two learner-gap Tier-1 switches off below `mvp-0.22`. Seven tests passed under the experiment for that reason and failed when their builders' default really moved; they went back to their tag (§3) and count as (a). Every move was therefore checked by a plain run at the head, not by the experiment: the 34 files that import the first batch's helpers (819 passed), the 73 that import the second batch's (1,716 passed), and the after census over the 103 files of both (2,371 passed, 6 skipped, the census plugin recording only).

## 3. What moved, and what stayed by name

Every new default is `LATEST_ALGORITHM_VERSION`, never a literal. "Named" is a test that failed at the head and so keeps its tag, written at its call.

**Commit 1 (`9096c7bfd5`), builder defaults:**

| builder | was | cases moved | named |
|---|---|---|---|
| `assumed_known_helpers._setup` | `mvp-0.11` | 33 (test_assumed_known), 19 test_quick_check, 5 + 5 placement report and signals | `test_assumed_known::test_fast_track_receipt_recomputes_its_decision` (`"mvp-0.11"`: it asserts the decision row's stamp, which is the vault's tag) |
| `certification_cold_probe_helpers._vault` | a hard-coded `mvp-0.7` | 23 + 19 (cold probe, serving reservation) + 1 + 1 (exam protection) | `test_probe_records_a_durable_versioned_label` (2 cases, `version="mvp-0.7"`: its policy stamp is `certification_cold_probe_policy_v1` there and `_v2` at the head). The builder gains a `version` keyword |
| `goal_certification_any_of_helpers.build_vault` | a hard-coded `mvp-0.7` | 14 + 4 + 2 (any-of, recap reviews) | none (the r2/r3 tests set their own tags after building) |
| the four learner-text-gap builders (`learner_text_gaps_helpers._vault`, `..._review_helpers._vault`, `..._flow_helpers._setup`, `test_learner_text_gaps_composition._vault`) | `mvp-0.16` | 24 + 18 + 26 + 10 + 6 | 7 tests (`LEARNER_TEXT_GAP_ALGORITHM_VERSION`; §2's limit: below Tier 1's tag the gap judges run without the Decider, which they read), and `diagnosis_journey_helpers.gap_case` (`version="mvp-0.16"`: the golden records that tag's writes) |
| `learner_report_superseded_helpers._vault` | `TAG` (`mvp-0.36`) | 34 | none new (the two `test_below_mvp067_...` cases pass their tags) |
| local builders of `test_placement_sidecar` (`mvp-0.11`), `test_unresolved_cause_gate` (`mvp-0.8`), `test_projection_evidence_polarity` and `test_observation_ledger_bulk` (`mvp-0.7`) | | 8 + 6 + 3 + 4 | none. `test_placement_sidecar::test_map_labels_assumed_points...` also lost its line that lowered a head vault to `mvp-0.11` (and the reload after it) |

**Commit 2 (`79373d76da`), explicit tags that were the successor's own:**

- `test_intent_fix_round6._random_world`, `test_intent_fix_round4._random_vault`, `test_intent_codex_review._reading_intent_vault`, `test_intent_plan._new_material_vault`: `version=INTENT_ALGORITHM_VERSION` dropped (24 + 16 + 8 + 1). `test_intent_plan._many_checks_vault` keeps it (one of its cases fails at the head).
- `test_reference_gate_imports`: the `gated` fixture builds at the head (11 moved); the three tests that shadow-rebuild "at the tag" against the predecessor take a new fixture `gated_at_tag` that puts the vault at `SOURCE_REFERENCE_GATE_ALGORITHM_VERSION` (their assignment names that tag, which is below the floor, so the vault must be there for the allowance).
- `test_source_first_needs`'s `active` fixture (16), `test_recurrence_groups`' history builder (11), `test_quick_add._setup` and `test_subject_registry`'s vault (`mvp-0.7` after `init_vault`: 6 + 4), `test_recurrence_commands._history` / `_merged_history` defaults and `test_the_backlog_needs_embeddings` (`mvp-0.12`: 10), `test_stuck_prompt_composition._assumed` (`mvp-0.13`: 4), `required_method_grading_helpers._method_vault`'s default and three `version=VERSION` lines of `test_required_method_grading` (11), nineteen `version=VERSION` lines of `test_route_rules_in_grader` including `_weightless_vault` (23), `test_attempt_content_state_race._fresh_vault`'s default (3; `_at_the_tag` keeps its tag by name).
- `causal_p2_acceptance_helpers._acceptance_vault` defaults to the head (15 causal acceptance, 6 probe records, 3 PFC readers); `diagnosis_journey_helpers`' two recorded journeys that build it now name `KM2_OLD_TAG` (their goldens were recorded there).
- In-memory configs lowered to an old tag that no gate reads since D6: `test_tier1_decider` (`_config()` and one test build `LearnLoopConfig()` and now set the head instead of `mvp-0.22`; four tests that loaded a head vault and lowered it to `mvp-0.22` lose that line), `test_decider_landing::test_the_tier1_disclosure...` (head instead of `mvp-0.22`), `test_today_headline`'s fake config (head instead of `mvp-0.14`; `daily_plan/headline.py` reads no tag). These are not in the census (no vault is written), so they are not in the 450. Kept: the transition tests of `test_tier1_decider` (`mvp-0.21` then `mvp-0.22` in one body) and `test_decider_landing::test_tier1_judgments_move_at_mvp022_with_their_switches` (its name is the tag).

Edits were exact-string replacements by small scripts, each asserting its pattern occurs once (a line-number variant for the `version=VERSION` lines, asserting each line changed), then `ruff check --select F401 --fix` on four files whose imports the removed lines left unused.

## 4. What stays, by reason

- **(a) the tag is load-bearing** (527 cases outside the successor files, 930 with them): they fail at the head with the tag taken there. Not read one by one in this pass (the second pass's and D6's lists already name most of them, by successor); the seven of §2 and the three `test_reference_gate_imports` shadow tests were read.
- **(a) successor, upgrade, migration and golden files** (521 cases, among them `test_upgrades` 344, the `*_successor` files, `test_diagnosis_journey_golden`, `test_attempt_application_order_migration`): the tag is what they compare.
- **(a) tag-parametrized arms** (315; the largest is `test_pfc_unverified_unassessed`, one case per tag of the split family, and `test_followup_fg1d_*` at `mvp-0.45`/`mvp-0.46`).
- **(a) arms that name a predecessor, a switch or the tag** (246 cases; the D4/D6 rule: the baseline keeps its old tag beside the switch that serves it), and builders whose name is the tag (`_mvp010`, `_mvp07`, `_p0_vault`, `_at_the_tag`, `_tag_env`, `test_placement_opening_probes._upgraded`).
- **(a) static uses with no vault behind them** (130 files): a stored row's own tag passed to a writer or an `INSERT` (`learner/facet_state_reader.py` compares a facet row's tag with `FACET_BELIEF_FIX_VERSIONS`, and a head vault holds rows written at earlier tags, so these are data, not the vault's tag), tag constants and chain positions asserted, upgrade tables, identity pins.
- **(c) not sorted** (247 cases outside the successor files, 285 with them): the vault's tag is written by `ux_phase1_support.set_config` (`reader_followups_helpers._seeded` at `mvp-0.39`, 130 of them, and the `mvp-0.35`, `mvp-0.27` and `mvp-0.42` reader files), a hand-written `learnloop.toml`, or a copied tracked fixture (the golden-path fixture at `mvp-0.8`, the migration-head fixture at `mvp-0.6`; those two are (a)). The experiment does not move these, so whether they pass at the head is not known.
- **(c) pass at the head, not moved** (187 cases): the tag comes from a shared builder whose other users fail at the head, or an explicit tag in a file not read this pass. By origin: `daily_plan_build_helpers` (about 70: mostly `mixture_env`'s default `mvp-0.24`, through which 199 cases that fail at the head also build; the RO0, data-capture and router R2 files), `split_live_helpers.split_vault` callers (about 20), `test_untaken_repair_episode._world` and `rebuild_equivalence_helpers` (10 + 10, the `mvp-0.64` and `mvp-0.66` successors' own files), `teacher_fakes` (8), `test_lp_claim_fixes._vault` (8), `test_field_workbench_signals._vault` (6), and single sites. Each needs a per-caller edit (pass the head at the call) or a per-builder read of its failing users; the table names the file.

## 5. Every assertion changed, and why

None. No expected value, comparison or `assert` line was edited. Non-assertion changes beyond the tag arguments: one fixture added (`test_reference_gate_imports.gated_at_tag`, §3), the lines lowering a head vault to an old tag removed (§3), and comments saying why a test keeps its tag.

## 6. Findings and ledger

No new bug found and no ledger row added. The failures read in this pass are explained by tag-dependent behaviour the tests pin (a stamp, a policy version, the pre-Tier-1 judges, a shadow assignment below the floor). The 923 failures of the experiment were sorted, not read; a defect among them would show as a test whose subject is not its tag.

## 7. Every file

"Census cases" are test cases that wrote or opened a vault below the head; "after" is the re-run for the 103 files that import a changed module, and the before count for every other file. "Static uses" are §2's names. Decisions: (a) the tag is the subject, kept; (b) moved; (c) kept, with the reason.

| file | census cases before | after | static uses before | after | decision |
|---|---|---|---|---|---|
| `ad23_contract_helpers.py` | 0 | 0 | 6 | 6 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `assumed_known_helpers.py` | 0 | 0 | 1 | 0 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `certification_cold_probe_helpers.py` | 0 | 0 | 1 | 0 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `check_credit_report_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `cli_generate_practice_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `data_capture_a2_measurement_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `diagnosis_journey_helpers.py` | 0 | 0 | 1 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `followup_fg1d_probe_shadow_helpers.py` | 0 | 0 | 4 | 4 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `followup_journey_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `followup_serve_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `followups_nov2_help_fold_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `goal_certification_any_of_helpers.py` | 0 | 0 | 1 | 0 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `helpers.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `identity_pins_helpers.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `ih2_lessons_compete_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `km2_write_path_helpers.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `km3_projections_helpers.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `learner_pick_proposal_helpers.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `learner_report_superseded_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `learner_text_gaps_flow_helpers.py` | 0 | 0 | 1 | 0 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `learner_text_gaps_helpers.py` | 0 | 0 | 3 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `learner_text_gaps_review_helpers.py` | 0 | 0 | 1 | 0 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `lp_claim_fixes_review_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `reader_ca2_codex_rereview_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `reader_followups_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
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
| `source_set_synthesis_helpers.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `successor_switches.py` | 0 | 0 | 22 | 22 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_ad23_fix_r5.py` | 1 | 1 | 1 | 1 | 1 fail at the head (a) |
| `test_ad23_migration.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_ad23_owner_decisions.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_ad23_successor.py` | 2 | 2 | 12 | 12 | 2 in a successor/upgrade/golden file (subject) |
| `test_ad2_serving.py` | 2 | 2 | 2 | 2 | 2 fail at the head (a) |
| `test_ad3_relatedness.py` | 1 | 1 | 1 | 1 | 1 fail at the head (a) |
| `test_ad_denial_log.py` | 81 | 81 | 0 | 0 | 67 fail at the head (a); 14 tag-parametrized arms (a) |
| `test_ai_compare.py` | 1 | 0 | 0 | 0 | moved 1 |
| `test_ai_config.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_answer_calibration_duel.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_arcb_close_fixes.py` | 5 | 5 | 0 | 0 | 1 fail at the head (a); 4 pass at the head, not moved (c) |
| `test_assessment_contracts.py` | 4 | 4 | 4 | 4 | 4 name the tag, a predecessor or a switch (a) |
| `test_assessment_enforcement.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_assumed_known.py` | 38 | 5 | 5 | 6 | moved 33; 1 fail at the head (a); 4 tag-parametrized arms (a) |
| `test_attempt_application_order_migration.py` | 0 | 0 | 4 | 4 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_attempt_chain_records.py` | 1 | 1 | 2 | 2 | 1 name the tag, a predecessor or a switch (a) |
| `test_attempt_completion.py` | 2 | 2 | 1 | 1 | 2 name the tag, a predecessor or a switch (a) |
| `test_attempt_content_state_race.py` | 5 | 2 | 3 | 2 | moved 3; 2 name the tag, a predecessor or a switch (a) |
| `test_attempt_content_state_successor.py` | 2 | 2 | 9 | 9 | 2 in a successor/upgrade/golden file (subject) |
| `test_attempt_order.py` | 0 | 0 | 7 | 7 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_batch3_landing.py` | 3 | 3 | 40 | 40 | 3 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_calibration.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_canonical_projection_rollout.py` | 3 | 3 | 3 | 3 | 1 fail at the head (a); 1 name the tag, a predecessor or a switch (a); 1 pass at the head, not moved (c) |
| `test_causal_activity_policy.py` | 0 | 0 | 3 | 3 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_causal_factor_deferral.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_causal_p2_acceptance.py` | 15 | 0 | 0 | 0 | moved 15 |
| `test_causal_trace_consistency_p2.py` | 4 | 4 | 7 | 7 | 1 fail at the head (a); 3 tag-parametrized arms (a) |
| `test_certification_cold_probe.py` | 25 | 2 | 0 | 1 | moved 23; 2 fail at the head (a) |
| `test_certification_serving_reservation.py` | 19 | 0 | 0 | 0 | moved 19 |
| `test_characterization_mastery_reliability.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_characterization_probe_regrade.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_chat_total_transport_deadline.py` | 1 | 1 | 0 | 0 | 1 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_check_credit_activation.py` | 5 | 5 | 9 | 9 | 2 fail at the head (a); 2 tag-parametrized arms (a); 1 name the tag, a predecessor or a switch (a) |
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
| `test_curriculum_c0b_landing.py` | 2 | 2 | 2 | 2 | 2 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_curriculum_c1_codex_review_fixes.py` | 2 | 2 | 3 | 3 | 1 fail at the head (a); 1 name the tag, a predecessor or a switch (a) |
| `test_curriculum_c1_fix_round2.py` | 2 | 2 | 3 | 3 | 1 fail at the head (a); 1 pass at the head, not moved (c) |
| `test_curriculum_c1_landing.py` | 0 | 0 | 9 | 9 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_curriculum_c1_plan_follows_path.py` | 3 | 3 | 39 | 39 | 3 name the tag, a predecessor or a switch (a) |
| `test_curriculum_locks.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_daily_plan_kill_switch.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_data_capture_a1_prefilter.py` | 8 | 8 | 4 | 4 | 5 fail at the head (a); 3 pass at the head, not moved (c) |
| `test_data_capture_a2_measurement.py` | 19 | 19 | 2 | 2 | 12 fail at the head (a); 5 name the tag, a predecessor or a switch (a); 2 pass at the head, not moved (c) |
| `test_data_capture_a4_delayed_completion.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_data_capture_a5_not_ready_floor.py` | 7 | 7 | 2 | 2 | 5 fail at the head (a); 2 name the tag, a predecessor or a switch (a) |
| `test_data_capture_a6_delayed_pick.py` | 6 | 6 | 2 | 2 | 1 name the tag, a predecessor or a switch (a); 5 pass at the head, not moved (c) |
| `test_data_capture_codex_rereview.py` | 23 | 23 | 0 | 0 | 23 fail at the head (a) |
| `test_data_capture_codex_review.py` | 8 | 8 | 2 | 2 | 7 fail at the head (a); 1 name the tag, a predecessor or a switch (a) |
| `test_data_capture_landing_review.py` | 24 | 24 | 0 | 0 | 24 fail at the head (a) |
| `test_data_capture_phone.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_data_capture_report.py` | 3 | 3 | 2 | 2 | 3 fail at the head (a) |
| `test_data_capture_successor.py` | 1 | 1 | 6 | 6 | 1 in a successor/upgrade/golden file (subject) |
| `test_decider_landing.py` | 0 | 0 | 5 | 4 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_diagnosis_async_router.py` | 1 | 1 | 1 | 1 | 1 name the tag, a predecessor or a switch (a) |
| `test_diagnosis_journey_golden.py` | 6 | 6 | 0 | 0 | 6 in a successor/upgrade/golden file (subject) |
| `test_diagnosis_replay.py` | 1 | 1 | 0 | 0 | 1 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_diagnostic_pack.py` | 10 | 10 | 0 | 0 | 10 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_discriminating_search.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_doctor.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_embedding_store.py` | 1 | 1 | 0 | 0 | 1 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_evidence_reading_successor.py` | 49 | 49 | 6 | 6 | 49 in a successor/upgrade/golden file (subject) |
| `test_evsi_router_composition.py` | 5 | 5 | 3 | 3 | 2 name the tag, a predecessor or a switch (a); 3 pass at the head, not moved (c) |
| `test_evsi_staged_binding.py` | 2 | 2 | 2 | 2 | 2 fail at the head (a) |
| `test_exam_protection.py` | 1 | 0 | 2 | 2 | moved 1 |
| `test_exam_protection_review.py` | 1 | 0 | 0 | 0 | moved 1 |
| `test_exam_session.py` | 2 | 2 | 2 | 2 | 2 name the tag, a predecessor or a switch (a) |
| `test_facet_belief_successor.py` | 6 | 6 | 15 | 15 | 6 in a successor/upgrade/golden file (subject) |
| `test_facet_belief_successor_derivation.py` | 7 | 7 | 7 | 7 | 7 in a successor/upgrade/golden file (subject) |
| `test_facet_state_write_on_change.py` | 0 | 0 | 13 | 13 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_family_memory_projection.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_field_workbench_signals.py` | 13 | 13 | 6 | 6 | 3 fail at the head (a); 4 name the tag, a predecessor or a switch (a); 6 pass at the head, not moved (c) |
| `test_figure_wait_estimate.py` | 3 | 3 | 5 | 5 | 1 fail at the head (a); 2 name the tag, a predecessor or a switch (a) |
| `test_figure_wait_successor.py` | 1 | 1 | 15 | 15 | 1 in a successor/upgrade/golden file (subject) |
| `test_fitted_parameters.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_followup_fg1d_panel_read.py` | 8 | 8 | 0 | 0 | 8 tag-parametrized arms (a) |
| `test_followup_fg1d_probe_shadow.py` | 12 | 12 | 0 | 0 | 12 tag-parametrized arms (a) |
| `test_followup_generate_e2e.py` | 1 | 1 | 2 | 2 | 1 fail at the head (a) |
| `test_followup_journey.py` | 1 | 1 | 2 | 2 | 1 fail at the head (a) |
| `test_followup_live_shape.py` | 1 | 1 | 1 | 1 | 1 fail at the head (a) |
| `test_followup_reserved_only.py` | 1 | 1 | 1 | 1 | 1 fail at the head (a) |
| `test_followup_rival_factor.py` | 1 | 1 | 1 | 1 | 1 fail at the head (a) |
| `test_followup_successor.py` | 2 | 2 | 6 | 6 | 2 in a successor/upgrade/golden file (subject) |
| `test_followup_workflow.py` | 1 | 1 | 1 | 1 | 1 fail at the head (a) |
| `test_followups_batch6_prefetch_decided_once.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_followups_batch6_review_fixes.py` | 2 | 2 | 3 | 3 | 2 fail at the head (a) |
| `test_followups_batch6_router_report.py` | 1 | 1 | 2 | 2 | 1 fail at the head (a) |
| `test_followups_batch6_te1b_card.py` | 3 | 3 | 4 | 4 | 3 fail at the head (a) |
| `test_followups_nov2_help_fold.py` | 6 | 6 | 0 | 0 | 6 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_followups_nov2_note_gap_unlinked.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_forced_withdrawal_records.py` | 6 | 6 | 0 | 0 | 4 fail at the head (a); 2 pass at the head, not moved (c) |
| `test_forecast_ledger.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_forecast_receipts.py` | 5 | 5 | 4 | 4 | 3 name the tag, a predecessor or a switch (a); 2 pass at the head, not moved (c) |
| `test_generated_item_gate.py` | 2 | 2 | 2 | 2 | 2 name the tag, a predecessor or a switch (a) |
| `test_goal_certification_any_of.py` | 14 | 0 | 0 | 0 | moved 14 |
| `test_golden_path_fixture.py` | 4 | 4 | 1 | 1 | 4 in a successor/upgrade/golden file (subject) |
| `test_grader_channel_prior_knobs.py` | 0 | 0 | 3 | 3 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_grading_cli.py` | 1 | 1 | 3 | 3 | 1 fail at the head (a) |
| `test_graph_correction.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_held_grade_evidence.py` | 16 | 13 | 0 | 0 | moved 3; 1 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c); 3 name the tag, a predecessor or a switch (a); 9 pass at the head, not moved (c) |
| `test_help_fold_attach_successor.py` | 4 | 4 | 6 | 6 | 4 in a successor/upgrade/golden file (subject) |
| `test_hint_feedback_widening.py` | 0 | 0 | 4 | 4 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_hot_path_eligibility_cutover.py` | 2 | 2 | 2 | 2 | 2 name the tag, a predecessor or a switch (a) |
| `test_hypothesis_claim_dispatcher.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_hypothesis_marks_context.py` | 1 | 1 | 0 | 0 | 1 fail at the head (a) |
| `test_ih2_lessons_compete.py` | 3 | 3 | 0 | 0 | 3 fail at the head (a) |
| `test_ih2_offer_ceiling_and_unseen.py` | 2 | 2 | 1 | 1 | 1 fail at the head (a); 1 name the tag, a predecessor or a switch (a) |
| `test_ih3_learner_preferences.py` | 2 | 2 | 2 | 2 | 2 fail at the head (a) |
| `test_ih3_migration.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_ih4_preferences_inform_router.py` | 4 | 4 | 2 | 2 | 4 fail at the head (a) |
| `test_ih5_successor.py` | 6 | 6 | 17 | 17 | 6 in a successor/upgrade/golden file (subject) |
| `test_ih6_workbench_open_item.py` | 5 | 5 | 2 | 2 | 5 fail at the head (a) |
| `test_ih7_lesson_sources_follow_diagnosis.py` | 3 | 3 | 5 | 5 | 3 fail at the head (a) |
| `test_ih_lesson_candidate_after_cold_miss.py` | 5 | 5 | 3 | 3 | 5 fail at the head (a) |
| `test_instrument_servability_journeys.py` | 1 | 1 | 1 | 1 | 1 name the tag, a predecessor or a switch (a) |
| `test_intent_codex_rereview.py` | 0 | 0 | 5 | 5 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_intent_codex_review.py` | 11 | 3 | 3 | 2 | moved 8; 2 fail at the head (a); 1 pass at the head, not moved (c) |
| `test_intent_fix_round4.py` | 18 | 2 | 5 | 4 | moved 16; 2 pass at the head, not moved (c) |
| `test_intent_fix_round6.py` | 25 | 1 | 3 | 2 | moved 24; 1 fail at the head (a) |
| `test_intent_plan.py` | 3 | 2 | 3 | 2 | moved 1; 1 fail at the head (a); 1 pass at the head, not moved (c) |
| `test_irt_difficulty.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_irt_end_to_end.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_judge_routes.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_k1_remediation_cold_reservation.py` | 1 | 1 | 2 | 2 | 1 fail at the head (a) |
| `test_km1_doctor.py` | 3 | 3 | 3 | 3 | 3 name the tag, a predecessor or a switch (a) |
| `test_km2_canonical.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_km2_write_path.py` | 1 | 1 | 0 | 0 | 1 name the tag, a predecessor or a switch (a) |
| `test_km3_projections.py` | 4 | 4 | 0 | 0 | 4 name the tag, a predecessor or a switch (a) |
| `test_km4_taxonomy.py` | 7 | 7 | 3 | 3 | 7 name the tag, a predecessor or a switch (a) |
| `test_large_practice_flow.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_learner_blindness_relax.py` | 2 | 2 | 0 | 0 | 2 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_learner_gap_unlinked_migration.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_learner_note_source_kind_migration.py` | 0 | 0 | 4 | 4 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_learner_pick_proposal.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_learner_report_superseded.py` | 38 | 4 | 39 | 39 | moved 34; 2 fail at the head (a); 1 tag-parametrized arms (a); 1 name the tag, a predecessor or a switch (a) |
| `test_learner_review_system_entries.py` | 0 | 0 | 8 | 8 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_learner_text_gaps.py` | 28 | 4 | 0 | 5 | moved 24; 4 fail at the head (a) |
| `test_learner_text_gaps_composition.py` | 7 | 1 | 5 | 4 | moved 6; 1 name the tag, a predecessor or a switch (a) |
| `test_learner_text_gaps_flow.py` | 12 | 2 | 1 | 3 | moved 10; 1 fail at the head (a); 1 name the tag, a predecessor or a switch (a) |
| `test_learner_text_gaps_rereview.py` | 18 | 0 | 0 | 0 | moved 18 |
| `test_learner_text_gaps_review.py` | 29 | 3 | 2 | 5 | moved 26; 2 fail at the head (a); 1 name the tag, a predecessor or a switch (a) |
| `test_learner_text_source_widening.py` | 0 | 0 | 4 | 4 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_lp_claim_fixes.py` | 13 | 13 | 6 | 6 | 1 fail at the head (a); 4 name the tag, a predecessor or a switch (a); 8 pass at the head, not moved (c) |
| `test_lp_claim_fixes_rereview.py` | 1 | 1 | 1 | 1 | 1 name the tag, a predecessor or a switch (a) |
| `test_lp_claim_fixes_review.py` | 2 | 2 | 3 | 3 | 1 name the tag, a predecessor or a switch (a); 1 pass at the head, not moved (c) |
| `test_map_untested.py` | 3 | 3 | 0 | 0 | 3 name the tag, a predecessor or a switch (a) |
| `test_mastery.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_mastery_seed_replay.py` | 4 | 4 | 3 | 3 | 3 fail at the head (a); 1 tag-parametrized arms (a) |
| `test_mcp_c1a_landing.py` | 1 | 1 | 0 | 0 | 1 pass at the head, not moved (c) |
| `test_measurement_corrections.py` | 1 | 1 | 5 | 5 | 1 fail at the head (a) |
| `test_method_explicit_landing.py` | 1 | 1 | 5 | 5 | 1 fail at the head (a) |
| `test_mobile_v3_successor.py` | 0 | 0 | 6 | 6 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_mvp017_route_check_replay.py` | 2 | 2 | 2 | 2 | 2 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_observation_ledger_bulk.py` | 4 | 0 | 1 | 0 | moved 4 |
| `test_p0_projection_cutover.py` | 6 | 6 | 4 | 4 | 2 fail at the head (a); 2 name the tag, a predecessor or a switch (a); 2 pass at the head, not moved (c) |
| `test_p2_acceptance.py` | 3 | 3 | 0 | 0 | 3 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_p2_leakage_suite.py` | 2 | 2 | 0 | 0 | 2 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_pfc_unassessed_readers.py` | 3 | 0 | 0 | 0 | moved 3 |
| `test_pfc_unverified_unassessed.py` | 225 | 225 | 2 | 2 | 224 tag-parametrized arms (a); 1 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_placement_diagnosis_decides.py` | 1 | 1 | 1 | 1 | 1 name the tag, a predecessor or a switch (a) |
| `test_placement_fixture_copies.py` | 0 | 0 | 10 | 10 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_placement_opening_probes.py` | 17 | 17 | 5 | 5 | 2 fail at the head (a); 15 name the tag, a predecessor or a switch (a) |
| `test_placement_report.py` | 5 | 0 | 0 | 0 | moved 5 |
| `test_placement_sidecar.py` | 8 | 0 | 2 | 0 | moved 8 |
| `test_placement_signals.py` | 5 | 0 | 0 | 0 | moved 5 |
| `test_placement_unevidenced_return.py` | 15 | 15 | 7 | 7 | 14 name the tag, a predecessor or a switch (a); 1 pass at the head, not moved (c) |
| `test_plan_determinism.py` | 12 | 12 | 2 | 2 | 9 fail at the head (a); 2 name the tag, a predecessor or a switch (a); 1 pass at the head, not moved (c) |
| `test_plan_determinism_landing.py` | 16 | 16 | 3 | 3 | 13 fail at the head (a); 3 name the tag, a predecessor or a switch (a) |
| `test_plan_follows_path.py` | 4 | 4 | 12 | 12 | 1 fail at the head (a); 2 name the tag, a predecessor or a switch (a); 1 pass at the head, not moved (c) |
| `test_practice_information.py` | 3 | 3 | 0 | 0 | 3 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_practice_leakage.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_primed_attempts.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_probe_attempt_updates.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_probe_episodes.py` | 1 | 1 | 1 | 1 | 1 name the tag, a predecessor or a switch (a) |
| `test_probe_migration.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_probe_records.py` | 7 | 1 | 1 | 1 | moved 6; 1 name the tag, a predecessor or a switch (a) |
| `test_probe_targeting.py` | 1 | 1 | 1 | 1 | 1 pass at the head, not moved (c) |
| `test_projection_evidence_polarity.py` | 3 | 0 | 1 | 0 | moved 3 |
| `test_provenance.py` | 1 | 1 | 2 | 2 | 1 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_quick_add.py` | 6 | 0 | 1 | 0 | moved 6 |
| `test_quick_check.py` | 19 | 0 | 0 | 0 | moved 19 |
| `test_reader_ca2_codex_rereview.py` | 5 | 5 | 0 | 0 | 5 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_reader_ca2_fix_orchestrator.py` | 8 | 8 | 0 | 0 | 8 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_reader_ca2_one_ask.py` | 15 | 15 | 6 | 6 | 15 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_reader_dialogue.py` | 1 | 1 | 0 | 0 | 1 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_reader_digest_narrative.py` | 25 | 25 | 0 | 0 | 25 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_reader_followups.py` | 35 | 35 | 0 | 0 | 35 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_reader_followups_rereview.py` | 6 | 6 | 0 | 0 | 6 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_reader_followups_review.py` | 18 | 18 | 0 | 0 | 18 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_reader_followups_round3.py` | 6 | 6 | 0 | 0 | 6 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_reader_followups_round4.py` | 2 | 2 | 0 | 0 | 2 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_reader_followups_round5.py` | 3 | 3 | 0 | 0 | 3 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_reader_followups_round6.py` | 3 | 3 | 0 | 0 | 3 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_reader_followups_round7.py` | 3 | 3 | 0 | 0 | 3 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_reader_followups_round8.py` | 4 | 4 | 0 | 0 | 4 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_reader_followups_successor.py` | 2 | 2 | 6 | 6 | 2 in a successor/upgrade/golden file (subject) |
| `test_reader_guidance.py` | 7 | 7 | 7 | 7 | 1 tag-parametrized arms (a); 6 name the tag, a predecessor or a switch (a) |
| `test_reader_recap_review.py` | 4 | 0 | 0 | 0 | moved 4 |
| `test_reader_recap_review_r2.py` | 3 | 1 | 1 | 1 | moved 2; 1 tag-parametrized arms (a) |
| `test_reader_recap_review_r3.py` | 5 | 5 | 4 | 4 | 2 tag-parametrized arms (a); 2 name the tag, a predecessor or a switch (a); 1 pass at the head, not moved (c) |
| `test_reader_rw1b_review.py` | 2 | 0 | 1 | 1 | moved 2 |
| `test_reader_rw3a_landing.py` | 3 | 3 | 2 | 2 | 2 fail at the head (a); 1 pass at the head, not moved (c) |
| `test_reader_rw4b_admission_idempotency.py` | 5 | 5 | 1 | 1 | 2 fail at the head (a); 3 pass at the head, not moved (c) |
| `test_reader_rw4b_fix6.py` | 4 | 4 | 3 | 3 | 3 fail at the head (a); 1 name the tag, a predecessor or a switch (a) |
| `test_reader_rw6b_landing.py` | 5 | 5 | 0 | 0 | 5 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_reader_seen_passages.py` | 1 | 1 | 1 | 1 | 1 fail at the head (a) |
| `test_reading_paths.py` | 2 | 2 | 6 | 6 | 2 name the tag, a predecessor or a switch (a) |
| `test_reading_step_switch.py` | 1 | 1 | 5 | 5 | 1 name the tag, a predecessor or a switch (a) |
| `test_rebuild_closed_row_answer.py` | 15 | 15 | 6 | 6 | 3 fail at the head (a); 2 name the tag, a predecessor or a switch (a); 10 pass at the head, not moved (c) |
| `test_rebuild_equivalence.py` | 1 | 1 | 2 | 2 | 1 tag-parametrized arms (a) |
| `test_rebuild_equivalence_review.py` | 1 | 1 | 6 | 6 | 1 name the tag, a predecessor or a switch (a) |
| `test_rebuild_history_appends.py` | 5 | 5 | 4 | 4 | 4 fail at the head (a); 1 name the tag, a predecessor or a switch (a) |
| `test_rebuild_orchestrator.py` | 6 | 6 | 0 | 0 | 6 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_recall_calibration.py` | 2 | 2 | 2 | 2 | 2 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_receipt_derivation.py` | 2 | 2 | 1 | 1 | 2 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_receipt_exactness.py` | 2 | 2 | 0 | 0 | 2 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_recurrence_commands.py` | 23 | 13 | 60 | 57 | moved 10; 13 name the tag, a predecessor or a switch (a) |
| `test_recurrence_deferral.py` | 3 | 3 | 2 | 2 | 3 name the tag, a predecessor or a switch (a) |
| `test_recurrence_groups.py` | 11 | 0 | 1 | 0 | moved 11 |
| `test_refactor_measures.py` | 0 | 0 | 8 | 8 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_reference_gate_imports.py` | 15 | 4 | 10 | 10 | moved 11; 3 fail at the head (a); 1 name the tag, a predecessor or a switch (a) |
| `test_refusal_records.py` | 3 | 3 | 0 | 0 | 1 fail at the head (a); 2 pass at the head, not moved (c) |
| `test_regrade_contract_successor.py` | 36 | 36 | 4 | 4 | 36 in a successor/upgrade/golden file (subject) |
| `test_remaining_decision_records.py` | 2 | 2 | 0 | 0 | 1 fail at the head (a); 1 pass at the head, not moved (c) |
| `test_required_method_grading.py` | 13 | 2 | 4 | 4 | moved 11; 2 name the tag, a predecessor or a switch (a) |
| `test_ro0_codex_review.py` | 5 | 5 | 2 | 2 | 2 fail at the head (a); 3 pass at the head, not moved (c) |
| `test_ro0_codex_verify.py` | 16 | 16 | 6 | 6 | 16 tag-parametrized arms (a) |
| `test_ro0_gate.py` | 5 | 5 | 4 | 4 | 4 tag-parametrized arms (a); 1 pass at the head, not moved (c) |
| `test_ro0_report.py` | 3 | 3 | 0 | 0 | 3 pass at the head, not moved (c) |
| `test_ro0_row10_cold_timing.py` | 3 | 3 | 0 | 0 | 3 pass at the head, not moved (c) |
| `test_ro0_row12_trajectory.py` | 3 | 3 | 0 | 0 | 3 pass at the head, not moved (c) |
| `test_ro0_row3_ask_availability.py` | 7 | 7 | 0 | 0 | 7 pass at the head, not moved (c) |
| `test_ro0_rows7_8_sessions.py` | 4 | 4 | 0 | 0 | 4 pass at the head, not moved (c) |
| `test_ro0_rows9_13_decision_state.py` | 13 | 13 | 0 | 0 | 5 fail at the head (a); 8 pass at the head, not moved (c) |
| `test_ro1_availability.py` | 2 | 2 | 2 | 2 | 2 fail at the head (a) |
| `test_ro1_availability_reads.py` | 7 | 7 | 2 | 2 | 6 fail at the head (a); 1 pass at the head, not moved (c) |
| `test_ro1_interval_factor.py` | 4 | 4 | 7 | 7 | 3 fail at the head (a); 1 pass at the head, not moved (c) |
| `test_ro1_projection.py` | 15 | 15 | 5 | 5 | 11 fail at the head (a); 4 name the tag, a predecessor or a switch (a) |
| `test_ro1_self_report.py` | 1 | 1 | 2 | 2 | 1 fail at the head (a) |
| `test_ro1_successor.py` | 3 | 3 | 7 | 7 | 3 in a successor/upgrade/golden file (subject) |
| `test_ro1_upgrade_report.py` | 3 | 3 | 4 | 4 | 3 in a successor/upgrade/golden file (subject) |
| `test_ro2_ad_document_ir.py` | 6 | 6 | 2 | 2 | 6 pass at the head, not moved (c) |
| `test_ro2_ad_raw_document_reads.py` | 2 | 2 | 3 | 3 | 2 name the tag, a predecessor or a switch (a) |
| `test_ro2_history_protection.py` | 2 | 2 | 2 | 2 | 2 pass at the head, not moved (c) |
| `test_ro4_codex_review.py` | 2 | 2 | 3 | 3 | 2 fail at the head (a) |
| `test_ro4_goals.py` | 4 | 4 | 8 | 8 | 3 fail at the head (a); 1 pass at the head, not moved (c) |
| `test_ro4_objective_serving.py` | 6 | 6 | 4 | 4 | 4 fail at the head (a); 2 name the tag, a predecessor or a switch (a) |
| `test_ro4_successor.py` | 1 | 1 | 7 | 7 | 1 in a successor/upgrade/golden file (subject) |
| `test_ro4_trace_report.py` | 1 | 1 | 2 | 2 | 1 name the tag, a predecessor or a switch (a) |
| `test_ro4_traces_migration.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_ro5_landing.py` | 9 | 9 | 6 | 6 | 1 fail at the head (a); 6 name the tag, a predecessor or a switch (a); 2 pass at the head, not moved (c) |
| `test_ro5_picks.py` | 1 | 1 | 2 | 2 | 1 fail at the head (a) |
| `test_ro5_stop_coin.py` | 1 | 1 | 4 | 4 | 1 fail at the head (a) |
| `test_ro5_successor.py` | 1 | 1 | 7 | 7 | 1 in a successor/upgrade/golden file (subject) |
| `test_ro6_codex_rereview.py` | 2 | 2 | 8 | 8 | 1 fail at the head (a); 1 pass at the head, not moved (c) |
| `test_ro6_codex_review.py` | 1 | 1 | 2 | 2 | 1 pass at the head, not moved (c) |
| `test_ro6_landing.py` | 4 | 4 | 9 | 9 | 3 fail at the head (a); 1 pass at the head, not moved (c) |
| `test_ro6_serving.py` | 5 | 5 | 4 | 4 | 1 fail at the head (a); 4 name the tag, a predecessor or a switch (a) |
| `test_ro6_successor.py` | 1 | 1 | 7 | 7 | 1 in a successor/upgrade/golden file (subject) |
| `test_ro6_tail_data.py` | 6 | 6 | 2 | 2 | 1 fail at the head (a); 5 name the tag, a predecessor or a switch (a) |
| `test_robust_completion_gate.py` | 6 | 6 | 6 | 6 | 4 fail at the head (a); 2 name the tag, a predecessor or a switch (a) |
| `test_robust_composition.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_robust_composition_bench.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_robust_selection_twin_candidates.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_rofu_ad_link.py` | 2 | 2 | 3 | 3 | 2 fail at the head (a) |
| `test_rofu_carried.py` | 1 | 1 | 2 | 2 | 1 fail at the head (a) |
| `test_rofu_generator_switches.py` | 11 | 11 | 4 | 4 | 10 fail at the head (a); 1 name the tag, a predecessor or a switch (a) |
| `test_rofu_learning.py` | 1 | 1 | 2 | 2 | 1 fail at the head (a) |
| `test_rofu_monotone.py` | 2 | 2 | 3 | 3 | 2 tag-parametrized arms (a) |
| `test_rofu_review_draw.py` | 2 | 2 | 2 | 2 | 2 fail at the head (a) |
| `test_rofu_scope.py` | 0 | 0 | 3 | 3 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_rofu_speed.py` | 2 | 2 | 4 | 4 | 2 fail at the head (a) |
| `test_rofu_successor.py` | 10 | 10 | 7 | 7 | 10 in a successor/upgrade/golden file (subject) |
| `test_rofu_weeks.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_roles_switch_off.py` | 1 | 1 | 0 | 0 | 1 name the tag, a predecessor or a switch (a) |
| `test_rospeed2_connections.py` | 5 | 5 | 10 | 10 | 3 fail at the head (a); 2 pass at the head, not moved (c) |
| `test_rospeed_ad_link.py` | 1 | 1 | 5 | 5 | 1 fail at the head (a) |
| `test_route_rules_in_grader.py` | 24 | 1 | 9 | 9 | moved 23; 1 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_router_card.py` | 3 | 3 | 4 | 4 | 3 fail at the head (a) |
| `test_router_coldness_covariates.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_router_failure_records.py` | 9 | 9 | 2 | 2 | 9 fail at the head (a) |
| `test_router_g1_feasibility.py` | 8 | 8 | 13 | 13 | 6 fail at the head (a); 2 pass at the head, not moved (c) |
| `test_router_g3_propensity.py` | 2 | 2 | 0 | 0 | 2 fail at the head (a) |
| `test_router_g4_restraint.py` | 11 | 11 | 4 | 4 | 9 fail at the head (a); 2 pass at the head, not moved (c) |
| `test_router_g7_fallback.py` | 3 | 3 | 0 | 0 | 3 fail at the head (a) |
| `test_router_offer_log.py` | 0 | 0 | 3 | 3 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_router_presentations.py` | 6 | 6 | 1 | 1 | 5 fail at the head (a); 1 pass at the head, not moved (c) |
| `test_router_probe_ties.py` | 3 | 3 | 6 | 6 | 3 name the tag, a predecessor or a switch (a) |
| `test_router_r1_composition.py` | 8 | 8 | 5 | 5 | 3 fail at the head (a); 2 name the tag, a predecessor or a switch (a); 3 pass at the head, not moved (c) |
| `test_router_r2a_landing.py` | 4 | 4 | 4 | 4 | 4 fail at the head (a) |
| `test_router_r2a_serving.py` | 10 | 10 | 4 | 4 | 5 fail at the head (a); 5 pass at the head, not moved (c) |
| `test_router_r2b_agreement.py` | 3 | 3 | 0 | 0 | 3 fail at the head (a) |
| `test_router_r2b_requests.py` | 1 | 1 | 0 | 0 | 1 fail at the head (a) |
| `test_router_r2b_serving.py` | 20 | 20 | 4 | 4 | 15 fail at the head (a); 5 pass at the head, not moved (c) |
| `test_router_r2bc_landing.py` | 6 | 6 | 3 | 3 | 5 fail at the head (a); 1 pass at the head, not moved (c) |
| `test_router_r2c_retrieval.py` | 8 | 8 | 1 | 1 | 4 fail at the head (a); 1 name the tag, a predecessor or a switch (a); 3 pass at the head, not moved (c) |
| `test_router_r2c_teach_back.py` | 6 | 6 | 2 | 2 | 6 pass at the head, not moved (c) |
| `test_router_reader_activity.py` | 16 | 16 | 2 | 2 | 1 fail at the head (a); 15 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_router_why_copy.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_rw2d_receipts_migration.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_rw7b_codex_review_fixes.py` | 2 | 2 | 3 | 3 | 2 fail at the head (a) |
| `test_rw7b_fix_round2.py` | 2 | 2 | 3 | 3 | 1 fail at the head (a); 1 name the tag, a predecessor or a switch (a) |
| `test_same_second_order.py` | 16 | 16 | 7 | 7 | 8 fail at the head (a); 5 tag-parametrized arms (a); 1 name the tag, a predecessor or a switch (a); 2 pass at the head, not moved (c) |
| `test_scheduler.py` | 0 | 0 | 7 | 7 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_scheduler_golden.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_scheduler_requested_floor.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_section_end.py` | 21 | 21 | 9 | 9 | 16 fail at the head (a); 4 tag-parametrized arms (a); 1 pass at the head, not moved (c) |
| `test_serve_eligibility.py` | 16 | 16 | 0 | 0 | 16 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_serve_eligibility_review.py` | 10 | 10 | 5 | 5 | 10 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_sg_slip_vs_gap.py` | 5 | 5 | 12 | 12 | 5 fail at the head (a) |
| `test_sg_successor.py` | 2 | 2 | 6 | 6 | 2 in a successor/upgrade/golden file (subject) |
| `test_shadow_rebuild.py` | 4 | 4 | 9 | 9 | 4 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_sidecar_contract.py` | 1 | 1 | 0 | 0 | 1 name the tag, a predecessor or a switch (a) |
| `test_sidecar_goals.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_sidecar_knowledge_model.py` | 3 | 3 | 2 | 2 | 2 fail at the head (a); 1 name the tag, a predecessor or a switch (a) |
| `test_sim_goals.py` | 3 | 3 | 0 | 0 | 3 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_sim_teach_back.py` | 4 | 4 | 0 | 0 | 4 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_simulation.py` | 4 | 4 | 0 | 0 | 4 open a vault whose tag is written another way (set_config, a hand-written config, a copied fixture): not sorted (c) |
| `test_slate_record.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_source_exercise_rpcs.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_source_first_needs.py` | 17 | 1 | 4 | 3 | moved 16; 1 name the tag, a predecessor or a switch (a) |
| `test_state_sync_scheduling_race.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_stuck_prompt.py` | 3 | 3 | 5 | 5 | 3 name the tag, a predecessor or a switch (a) |
| `test_stuck_prompt_composition.py` | 5 | 1 | 2 | 1 | moved 4; 1 name the tag, a predecessor or a switch (a) |
| `test_stuck_prompt_replay.py` | 3 | 3 | 1 | 1 | 1 fail at the head (a); 2 name the tag, a predecessor or a switch (a) |
| `test_subject_registry.py` | 4 | 0 | 1 | 0 | moved 4 |
| `test_successor_switches.py` | 4 | 4 | 10 | 10 | 4 in a successor/upgrade/golden file (subject) |
| `test_surfaced_belief_corrections.py` | 0 | 0 | 4 | 4 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_surprise.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_te3a_lesson_opportunity.py` | 3 | 3 | 2 | 2 | 3 fail at the head (a) |
| `test_te3a_successor.py` | 1 | 1 | 6 | 6 | 1 in a successor/upgrade/golden file (subject) |
| `test_te3b_binding.py` | 0 | 0 | 4 | 4 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_te3b_codex_review.py` | 4 | 4 | 4 | 4 | 4 fail at the head (a) |
| `test_te3b_offers.py` | 1 | 1 | 4 | 4 | 1 fail at the head (a) |
| `test_te3b_successor.py` | 1 | 1 | 6 | 6 | 1 in a successor/upgrade/golden file (subject) |
| `test_te3b_value.py` | 0 | 0 | 4 | 4 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_teach_back.py` | 3 | 3 | 3 | 3 | 2 tag-parametrized arms (a); 1 name the tag, a predecessor or a switch (a) |
| `test_teacher_exam_question_guard.py` | 2 | 2 | 4 | 4 | 1 name the tag, a predecessor or a switch (a); 1 pass at the head, not moved (c) |
| `test_teacher_te0_confidence_events.py` | 3 | 3 | 4 | 4 | 3 fail at the head (a) |
| `test_teacher_te0_review_fixes.py` | 3 | 3 | 5 | 5 | 3 fail at the head (a) |
| `test_teacher_te1_migration.py` | 0 | 0 | 3 | 3 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_teacher_te1_successor.py` | 2 | 2 | 59 | 59 | 2 in a successor/upgrade/golden file (subject) |
| `test_teacher_te1b_landing_r2.py` | 8 | 8 | 9 | 9 | 8 fail at the head (a) |
| `test_teacher_te1b_migration.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_teacher_te1b_rereview_fixes.py` | 4 | 4 | 5 | 5 | 4 fail at the head (a) |
| `test_teacher_te1b_review_fixes.py` | 6 | 6 | 7 | 7 | 6 fail at the head (a) |
| `test_teacher_te1b_suggestions.py` | 15 | 15 | 27 | 27 | 14 fail at the head (a); 1 pass at the head, not moved (c) |
| `test_teacher_te2_migration.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_teacher_te2_sidecar.py` | 2 | 2 | 2 | 2 | 2 pass at the head, not moved (c) |
| `test_teacher_te2_successor.py` | 1 | 1 | 6 | 6 | 1 in a successor/upgrade/golden file (subject) |
| `test_teacher_te2log_migration.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_tier1_decider.py` | 0 | 0 | 13 | 7 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_today_headline.py` | 1 | 1 | 1 | 0 | 1 name the tag, a predecessor or a switch (a) |
| `test_tui_app.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_unresolved_cause_gate.py` | 6 | 0 | 1 | 0 | moved 6 |
| `test_untaken_repair_episode.py` | 17 | 17 | 5 | 5 | 4 fail at the head (a); 3 name the tag, a predecessor or a switch (a); 10 pass at the head, not moved (c) |
| `test_upgrades.py` | 344 | 344 | 17 | 17 | 344 in a successor/upgrade/golden file (subject) |
| `test_ux_phase1_round2_rereview.py` | 2 | 2 | 1 | 1 | 2 tag-parametrized arms (a) |
| `test_ux_phase4_feedback.py` | 10 | 10 | 1 | 1 | 5 name the tag, a predecessor or a switch (a); 5 pass at the head, not moved (c) |
| `test_ux_phase4_landing.py` | 5 | 5 | 1 | 1 | 1 fail at the head (a); 1 name the tag, a predecessor or a switch (a); 3 pass at the head, not moved (c) |
| `test_valuation_calibration_fields.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_value_candidates.py` | 2 | 2 | 1 | 1 | 2 name the tag, a predecessor or a switch (a) |
| `test_vault_report.py` | 0 | 0 | 18 | 18 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `test_version_floor.py` | 19 | 19 | 10 | 10 | 19 in a successor/upgrade/golden file (subject) |
| `test_voi_merge_composition.py` | 8 | 8 | 17 | 17 | 2 fail at the head (a); 6 name the tag, a predecessor or a switch (a) |
| `test_voi_stopping.py` | 28 | 28 | 57 | 57 | 3 fail at the head (a); 2 tag-parametrized arms (a); 23 name the tag, a predecessor or a switch (a) |
| `test_voi_v2.py` | 21 | 21 | 19 | 19 | 4 fail at the head (a); 3 tag-parametrized arms (a); 7 name the tag, a predecessor or a switch (a); 7 pass at the head, not moved (c) |
| `test_why_cases.py` | 8 | 1 | 0 | 0 | moved 7; 1 fail at the head (a) |
| `test_why_reader.py` | 4 | 4 | 0 | 0 | 3 fail at the head (a); 1 pass at the head, not moved (c) |
| `test_workbench_in_session_gaps.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `voi_restore_scenarios.py` | 0 | 0 | 3 | 3 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `voi_stopping_helpers.py` | 0 | 0 | 1 | 1 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |
| `why_cases_helpers.py` | 0 | 0 | 2 | 2 | no vault at an old tag: a stored row's tag, a tag constant or string asserted, or tag data (a) |

## 8. Gates run

All through the scratch wrapper (empty home, isolated config dir), in a 3 GB scope at `-n 1`, one at a time.

- The experiment (§2), 6 chunks over 589 files: 923 failed and 9,153 passed in all (each failure a test that writes an old tag; 0 failures in tests that write none).
- Commit 1's importers (34 files): first run 7 failed, 812 passed (the §2 limit); after naming the seven tags: 819 passed, 6 skipped.
- Commit 2's importers (73 files): 1,716 passed (a first attempt was stopped by a shell timeout before it printed, not by memory).
- After census, plain run of the 103 files of both commits on the tip: 2,371 passed, 6 skipped.
- `tests/test_identity_pins.py`, `test_structure_ratchets.py`, `test_effective_defaults_golden.py`, `test_cli_help_snapshot.py`, `test_kill_switches.py`, `test_sqlite_file_copies.py`: 398 passed. No pin, ratchet or golden moved.
- `tests/test_test_layout.py` alone: 3 passed. `tests/test_architecture.py` alone: 18 passed.
- `ruff check`: all checks passed. `lint-imports --no-cache`: 52 kept, 0 broken. `scripts/check_gate_partition.py`: 33,263 collected, landing 33,197 + arc_close 66. `scripts/affected_tests.py --files` (no source file changed): no test file affected.
- Not run (the orchestrator's): the landing selection, the arc-close and durability lanes, `--fresh-connections`, vitest, the vault references (the landing regenerates them).

## 9. Open items

- **The 187 (c) cases that pass at the head** (§4): the next move is per caller of `mixture_env` / `daily_plan_build_helpers` and `split_vault` (pass the head at the call), and a read of `test_untaken_repair_episode`, `rebuild_equivalence_helpers`, `teacher_fakes`, `test_lp_claim_fixes` and `test_field_workbench_signals`.
- **The 285 unsorted cases** (§4): an experiment that also maps `set_config`'s `algorithms.algorithm_version` key would sort them; `reader_followups_helpers._seeded` (130) is the first.
- **Row stamps** stay by decision (§4). If the owner wants test rows stamped at the head where the stored tag is not read, that is a separate, larger edit with its own risk (`facet_state_reader` reads a facet row's tag).
- **The experiment's limit** (§2): a builder that reads its own `version` argument besides writing it hides a dependency from the sort; `serve_pre_tier1` is the one found. A future pass should grep for such readers before trusting the sort.
- **Vacuity**: the moved tests kept every assertion and ran green at the head; no mutation check was run in this pass (the second pass's §5 method), so "still tests its subject" rests on reading the moved builders and the subject scan.
