# Teacher TE2: Codex review and fixes

Stage `teacher-te2`, branch `teacher/te2`, base main `5565bede25`. The review (gpt-6.1-sol, codex-job
`20261106-044533-daXcGn`) read `5565bede25..teacher/te2` at `dc9daca78e` statically. Its runtime checks were blocked
because `systemd-run` could not reach the user scope bus. Here the wrapper worked, so every finding was reproduced with
a failing test before it was fixed. Every test uses fakes only. No model call, paid request or live vault was used.

## Review

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Lesson probes get zero reliable canonical evidence | fixed | `a6fd6615fe` | `test_teacher_te2_review_fixes.py::test_f1_a_probe_answer_carries_reliable_canonical_mass_live_and_after_a_rebuild` |
| F2 | High | Topic exposure is labelled but does not contaminate the recorded attempt | fixed | `a6fd6615fe` | `::test_f2_an_answer_after_teaching_on_its_topic_is_instructional_and_no_cold_outcome` |
| F3 | Medium | An interrupted answer can leave the probe permanently unsubmitable | fixed | `a6fd6615fe` | `::test_f3_a_fault_after_the_attempt_rolls_everything_back_and_the_answer_can_be_sent_again[retire,result,episode]`, `::test_f3_an_answer_already_recorded_is_finished_without_a_second_grade`, `::test_f3_a_view_after_a_half_recorded_answer_delivers_its_result_instead_of_dropping_the_probe`, `::test_f3_a_second_submit_of_an_answered_probe_returns_its_result` |
| F4 | Medium | "Try again" cannot resume the teacher after a probe completes or is retired | fixed | `a6fd6615fe` | `::test_f4_resume_after_a_probe_result_whose_teacher_call_never_ran`, `::test_f4_resume_after_the_follow_up_call_failed`, `::test_f4_resume_after_teach_it_anyway_whose_teacher_call_never_ran` |
| F5 | Medium | TE2's new calls are not restricted to the approved plan routes | fixed | `a6fd6615fe` | `::test_f5_a_metered_probe_author_is_sent_nothing`, `::test_f5_a_metered_typed_goal_resolver_is_sent_nothing` |
| F6 | Low | Spec-conformance row §11.8: Today lists older TE1 lessons, but their "Close it" is rejected | fixed | `a6fd6615fe` | `::test_f6_today_can_close_a_te1_lesson_left_open_before_te2_was_switched_on` |

The reference was regenerated in `2a501c21d9`. Stamp-only churn was left out.

### How each was reproduced, and the fix

**F1. Reproduced.** A correct answer to an admitted probe left every canonical recall cell of the probe item at
`raw_coverage_mass` 0. No `raw_grade_events` row existed for the attempt, so a rebuild also read 0. The existing
rebuild-equivalence test passed only because live and rebuilt state were both zero.

**Fix.** A presentationless `diagnostic_probe` with `evidence_origin = lesson_probe` now goes through
`attempts._record_lesson_probe`. This runs live only, after `_dual_write_grade_channel` and before the attempt's
canonical projection. It writes the calibrated grade interpretation on a diagnostic administration, using the
probe path's own dual-write without an instrument (`probe_episodes.dual_write_presentationless_probe_grade`).

- Both rows are RAW_LEDGER, so replay folds the same ledger. The new test checks that the probe's cells are positive
  live and after `rebuild_all_derived_state`, and that the cells are identical on both sides.
- Exactly one `raw_grade_events` row exists before and after the rebuild.
- FG1d's case is unchanged: an FG1 answer sent without its presentation is still incidental.
- The teacher still writes evidence only through the attempts path, as the import contract requires.

**F2. Reproduced.** After a reveal on a sibling item of the probe's LO, `causal_activity_classification` had no row
for the attempt, so the policy default treated it as a pure diagnostic. `lesson_weight.qualifying_outcomes` also
returned the attempt as a cold outcome, so it could resolve the lesson's own lesson checks and its
`lesson_step_retained` forecasts.

**Fix.** The same writer records the attempt's class before the projection:

- `pure_diagnostic` (source `lesson_probe`) when the reveal ledger's topic-wide check admits the answer;
- `instructional_diagnostic` (source `lesson_probe_exposed`) when it does not. In the policy matrix this is "assisted",
  which matches how FG1's presentation path classifies a diagnostic that instruction leaked into.

The exposure reaches the attempts path as `ApplyAttemptInput.diagnostic_exposure`. The check is now read inside the
answer's write transaction, so no reveal can land between the check and the attempt.

`qualifying_outcomes` drops attempts that carry the `lesson_probe_exposed` source. Only TE2 writes that source, so
nothing recorded before TE2 resolves differently: TE1 and TE2-log weight replay is unchanged.

Not adopted: forcing `primed = True`. Priming means "the answer was handed over", and would record the answer as a
`repair_activity`. §11.3 asks for "not independent", which the instructional class records exactly.

**F3. Reproduced.** Raising at the item's retirement, at the `probe_result` append, or at the episode close left the
attempt committed and the probe still served. The next submit then failed with
`UNIQUE constraint failed: practice_attempts.id`. A view after a half-recorded answer whose item was already retired
retired the probe as `not_servable` and dropped its result.

**Fix.** `probes.record_answer` now commits the attempt, the retirement, `probe_result` and the episode close in one
transaction. It grades outside that transaction, and grades only when no attempt exists yet. It is idempotent:

- A probe that is already answered returns its stored result. This covers a second, concurrent submit.
- An attempt already stored under the probe's attempt id is finished from that row, with no second grade and no
  second insert.

`probes.serve` no longer retires a served probe whose attempt exists. `lesson.view` finishes such a probe through
`probes.finish_recorded`, which makes no model call, so its result reaches the feed and the teacher.

**F4. Reproduced.** In each case, `resume` made no teacher call and the lesson sat unchanged:

- after the probe's result was committed and `clients.teacher()` raised;
- after the follow-up teacher call failed;
- after *Teach it anyway* when the teacher client raised.

**Fix.** `probe_result`, and a `probe_retired` whose reason is `teach_anyway`, are now teacher-call boundaries
(`service._boundary`). A boundary is consumed only when an accepted teacher turn commits after it. Retirements at the
lesson's close, or of an unservable item, owe no call: the lesson goes on at the learner's next step.

**F5. Reproduced.** Two metered clients were each sent one request:

- a probe author with `provider_type = openai_compatible` (`author.calls == 1`);
- a typed-goal resolver on a metered route with a price set (`status == "ready"`).

**Fix.**

- `lesson_probe.run` checks the exact client that would send (`ai.spend.is_subscription_transport`). A metered client
  is sent nothing, and the probe is refused with `route_unavailable`, so the teacher is told "couldn't prepare that
  question".
- `resolve_typed_goal` uses `ChatRoute(..., subscription_only=True)`. This is a new flag that applies `plan_only`'s
  two checks (the planned route and the resolved client) to any subscription transport. A metered route or client is
  `not_subscription_route`, nothing is sent, and the learner reads "Your lesson's goal is read on your ChatGPT plan
  only, and the plan isn't ready."
- The rule is the subscription transport (the plan or Codex), not the plan alone. The owner's Oct 12 decision lets
  Codex on the subscription run every paid role, and §24's "nothing metered" is the binding property.
- The test author fake now declares `chatgpt_plan`.

**F6. Reproduced and fixed.** The review lists this in its §11.8 conformance row, not as a numbered finding. With TE2
switched on, `open_lessons` lists a TE1 lesson left open from before. Its "Close it" raised "Unknown lesson action
'close'", which is a button that errors for the learner. `close` is now accepted on any open lesson once TE2 serves.
It writes a `learner_stop`, closes with no teacher call, and commits the lesson's delayed checks, as for a TE2 lesson.
The probe actions are still accepted only on TE2 lessons.

### What the review's other notes leave open (not changed here)

- **§11.5 gaps the review names:** the library lookup for a typed goal, a mid-lesson `create_goal_lo`, and the close
  card's "Add to my goals".
  - The smallest way to finish them: a `lesson.add_goal` RPC over `topics.plan_open`'s create step, plus a close-card
    button calling it. The library lookup would be a search over `vault.learning_objects` titles before the resolver
    call.
- **Text-gap judge on a metered route.** The per-gap text-gap judge keeps its existing route. That route includes the
  owner's Decider on OpenRouter, which is metered by owner decision. So §24's "nothing metered" holds for the author
  and the resolver, while the gap pipeline is unchanged from before TE2.
- **Delayed checks.** The review points out that leaving every generated probe out of the delayed-check candidates
  (`delayed_checks.candidates`) also applies to FG1's own probes and below the tag. That was the build's deliberate
  choice: it closes a door FG1 §4.2 already requires to be closed. It is recorded in `docs/reviews/teacher-te2.md`.

### Rows a lesson probe now writes (on fakes)

A probe answered right adds these rows to the build record's table (`docs/reviews/teacher-te2.md`):

- one `raw_grade_events` row (purpose `diagnostic`; the F1 test counts exactly one, live and after a rebuild);
- its `grade_interpretations` head;
- the administration identity that `ensure_administration_identity` resolves for the attempt;
- one `causal_activity_classification_events` row (`lesson_probe` or `lesson_probe_exposed`; the F2 test reads it).

Calls per probe are unchanged: 1 author call (at most 2) and 1 grader call. A metered author or resolver now gets 0.

## Gate

Run in the worktree at `2a501c21d9`. Every pytest command ran inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G --`, with `-n 6`. Ad-hoc tools ran under
`env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install --offline pypdfium2==5.14.0` | ok |
| `lint-imports --no-cache` | 43 kept, 0 broken |
| pytest, the new file before the fixes | 13 failed (each finding reproduced) |
| pytest, the new file and the TE2 files after the fixes | 58 passed |
| pytest, the targeted set (130 files, listed below) on the fixes before F6 | 2909 passed, 7 skipped, 4 xfailed, 1 failed: `test_architecture::test_runtime_packages_import_only_public_cross_boundary_names` (a private cross-package import), fixed with the public `dual_write_presentationless_probe_grade` |
| pytest after that fix: `test_architecture`, the six TE2 files, `test_teacher_te1_lesson`, `test_teacher_te1_review_fixes`, `test_teacher_te2log_episodes`, `test_probe_episodes`, `test_followup_fg1d_probe_shadow`, `test_grade_resolution_pipeline` | 222 passed |
| `module_generate.py`, `module_validate.py` | regenerated (`2a501c21d9`), PASS (1242 modules) |
| pytest, the targeted set again at `2a501c21d9` (132 files: the 130 plus `test_teacher_te2_review_fixes`, `test_teacher_te2_migration`) | 2929 passed, 7 skipped, 4 xfailed, 1 failed: `test_ro5_landing::test_r5_1_no_room_to_wait_asks_now_deterministically_and_asks_no_model`. This is RO5's router test: it opens no lesson and touches nothing this step changed, and it passed in the first run. Rerun alone, its file gives 22 passed (a load-timing flake in the 16-minute run) |

No migration, schema, DB/connection, frontend or `src-tauri` change in this step. So there was no durability lane,
npm, vitest, cargo or DB reference run.

**Test files** (the targeted set). The selection was:

- every test file naming `learnloop.teacher`, `teacher_fakes`, `lesson_weight` or `forecast_report`;
- every file naming the deliverables resolver (`source_retrieval.deliverables`, `deliverable_fixtures`, `ChatRoute`),
  `followup_run` or `lesson_probe`;
- every file naming the causal activity policy or classification, or the grade-channel and probe dual-writes;
- `test_followup_fg1d_*`, `test_rebuild_equivalence*`, `test_rebuild_orchestrator`, `test_shadow_rebuild`,
  `test_km2_write_path`, `test_p0_cutover_mvp08`, `test_anti_double_count`, `test_projection_evidence_polarity`;
- the contract set:
  - `test_architecture` (frozen cycles), `test_table_roles`, `test_registry_audit`, `test_module_catalog_inventory`,
    `test_ad_protected_tables`, `test_cli_help_snapshot`;
  - the display-label audit: `test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`,
    `test_rw5c_labels`;
  - the process-launch allowlist: `test_ai_tool_isolation`, `test_e0_isolation`, `test_codex_tool_lockdown`,
    `test_codex_lockdown_round3`;
  - `test_sqlite_file_copies`, `test_public_tip_guards`, `test_config_refactor`, `test_desktop_rpc_contract`,
    `test_sidecar_serializer_snapshot`, `test_sidecar_contract`, `test_sidecar_registry`, `test_mobile_allowlist`,
    `test_desktop_activation_audit`, `test_coordinated_migrations`, `test_tracked_fixture_databases`,
    `test_migrations`.

The full list:

`test_ad_protected_tables`, `test_ai_tool_isolation`, `test_anti_double_count`, `test_architecture`, `test_causal_activity_policy`, `test_causal_attribution_p2`, `test_causal_factor_deferral`, `test_causal_p2_acceptance`, `test_causal_repair_mapping_p2`, `test_cli_help_snapshot`, `test_codex_lockdown_round3`, `test_codex_tool_lockdown`, `test_cold_retry_reschedule`, `test_config_refactor`, `test_coordinated_migrations`, `test_coverage_on_extract`, `test_curriculum_c0b_landing`, `test_curriculum_c1_codex_review_fixes`, `test_curriculum_c1_fix_round2`, `test_curriculum_c1_fix_round3`, `test_curriculum_c1_fix_round4`, `test_curriculum_c1_fix_round5`, `test_curriculum_c1_plan_follows_path`, `test_curriculum_c1_round5_followups`, `test_curriculum_c2b_past_papers`, `test_curriculum_c3_codex_review`, `test_curriculum_c3_exam_scoping`, `test_data_capture_a6_delayed_pick`, `test_data_capture_successor`, `test_deliverable_codex_review`, `test_deliverable_path`, `test_deliverable_rpcs`, `test_deliverable_scope`, `test_desktop_activation_audit`, `test_desktop_rpc_contract`, `test_e0_isolation`, `test_facet_evidence_timeline`, `test_figures_prefetch`, `test_figures_prefetch_review_fixes`, `test_followup_codex_review`, `test_followup_fg1c_codex_review`, `test_followup_fg1c_r1_exposure_independence`, `test_followup_fg1d_panel_read`, `test_followup_fg1d_probe_shadow`, `test_followup_generate_e2e`, `test_followup_journey`, `test_followup_live_shape`, `test_followup_next_matrix`, `test_followup_reserved_only`, `test_followup_rival_factor`, `test_followup_router`, `test_followups_batch5_lesson`, `test_followups_batch5_recap_dependencies`, `test_followups_batch5_recap_protection`, `test_followups_batch6_review_fixes`, `test_followups_batch6_router_report`, `test_followups_batch7_prefetch_capped_resume`, `test_followup_single_use`, `test_followups_nov2_figure_provenance`, `test_followup_successor`, `test_followup_workflow`, `test_forecast_receipts`, `test_grade_resolution_pipeline`, `test_hint_evidence`, `test_hint_h2a_review_round2`, `test_hypothesis_marks_context`, `test_hypothesis_marks`, `test_intent_fix_round4`, `test_key_ladder_labels`, `test_km2_write_path`, `test_measurement_state_labels`, `test_migrations`, `test_mobile_allowlist`, `test_mobile_handoff`, `test_module_catalog_inventory`, `test_notes_as_learner_text`, `test_notes_c2b_review5`, `test_notes_linked`, `test_notes_never_read`, `test_notes_vault_search`, `test_observation_ledger_bulk`, `test_p0_cutover_mvp08`, `test_probe_episodes`, `test_projection_evidence_polarity`, `test_public_tip_guards`, `test_reader_rw5d_p4b_teacher_visuals`, `test_reader_workbench_rw2a`, `test_rebuild_equivalence`, `test_rebuild_equivalence_review`, `test_rebuild_orchestrator`, `test_receipt_exactness`, `test_reference_gate_imports`, `test_registry_audit`, `test_regrade_contract_successor`, `test_ro0_codex_review`, `test_ro1_availability_reads`, `test_ro1_successor`, `test_ro4_successor`, `test_ro5_landing`, `test_ro5_successor`, `test_ro6_successor`, `test_router_why_copy`, `test_rw5c_labels`, `test_shadow_rebuild`, `test_sidecar_contract`, `test_sidecar_registry`, `test_sidecar_serializer_snapshot`, `test_sqlite_file_copies`, `test_table_roles`, `test_teacher_te1b_landing_r2`, `test_teacher_te1b_rereview_fixes`, `test_teacher_te1b_review_fixes`, `test_teacher_te1b_suggestions`, `test_teacher_te1_curriculum_c4`, `test_teacher_te1_lesson`, `test_teacher_te1_migration`, `test_teacher_te1_review_fixes`, `test_teacher_te1_successor`, `test_teacher_te1_weight`, `test_teacher_te2_lessons`, `test_teacher_te2log_activity`, `test_teacher_te2log_episodes`, `test_teacher_te2log_node_held`, `test_teacher_te2log_receipt`, `test_teacher_te2log_report`, `test_teacher_te2_migration`, `test_teacher_te2_probes`, `test_teacher_te2_review_fixes`, `test_teacher_te2_sidecar`, `test_teacher_te2_successor`, `test_tracked_fixture_databases`, `test_workbench_assistance`.

New test file: `tests/test_teacher_te2_review_fixes.py` (12 tests, 14 cases). F6's test was written after the
13-failure reproduction run. With the fix temporarily reverted it failed (`LessonError: Unknown lesson action
'close'`). With the fix back, the whole file passed: 14 passed. Changed: `tests/test_teacher_te2_probes.py` (the author
fake declares the subscription plan).

## Re-review

The re-review (gpt-6.1-sol, codex-job `20261106-054620-utKkR3`) read `dc9daca78e..teacher/te2` at `1831c669f9`. It
confirmed F1 and F2 fixed and reopened the stage on one new finding, F7. Every test uses fakes only. No model call,
paid request or live vault was used.

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Lesson probes get zero reliable canonical evidence | confirmed fixed | `a6fd6615fe` | unchanged |
| F2 | High | Topic exposure is labelled but does not contaminate the recorded attempt | confirmed fixed | `a6fd6615fe` | unchanged |
| F7 | Medium | Blind lesson-probe grades use the joint grader's calibration | fixed | `6e0b13cf61` | `test_teacher_te2_review_fixes.py::test_f7_a_blind_lesson_probe_grade_keeps_the_blind_calibration_identity` |

**F7. Reproduced.** The test seeds two `grader_identity`-scope calibration models: one for the blind grader
(`grading_prompt_v2_blind` / `blind_grading_proposal_v1`) and one for the joint grader (`grading_prompt_v1` /
`grading_proposal_v1`). It then answers an admitted probe in a split vault (`split_grading_active` is true at the TE2
tag). Before the fix, the attempt's `raw_grade_events` row stamped `grading_prompt_v1`, because
`_record_lesson_probe` dropped `ApplyAttemptInput.grader_identity`. The probe path's dual-write then resolved the
joint grader's identity hash and models.

**Fix.** `_record_lesson_probe` now passes `attempt.grader_identity` through
`dual_write_presentationless_probe_grade` and `_dual_write_probe_grade` into `record_grade_dual_write`, as
`grading_prompt_version` and `grader_output_schema_version`. Both new parameters default to None, which is the joint
grader's identity, so every other caller stamps what it did before. The test asserts three things:

- the persisted prompt, schema and `grader_identity_hash` are the blind grader's;
- the interpretation's `reference_prior_ids_json` contains the blind model and not the joint one;
- the canonical cells are equal before and after `rebuild_all_derived_state`. Replay reads the blind identity back
  from the raw grade event (`replay_grader_identity`).

**Left open (outside this stage).** FG1's presentation path (`_record_presentation_observation`) also calls
`_dual_write_probe_grade` with no identity, so in a split vault its probe grades are stamped with the joint
identity too. That predates TE2 and was not changed here. The smallest way to finish it is to pass the submission's
`grader_identity` at that one call site, with a matching FG1 test.

### Gate (re-review step)

Run in the worktree at `6e0b13cf61`. Every pytest command ran inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G --`. Ad-hoc tools ran under `env -i`, with
empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install --offline pypdfium2==5.14.0` | ok |
| `lint-imports --no-cache` | 43 kept, 0 broken |
| pytest `-k f7` on `test_teacher_te2_review_fixes.py`, before the fix | 1 failed (`'grading_prompt_v1' != 'grading_prompt_v2_blind'`) |
| pytest `test_teacher_te2_review_fixes.py`, after the fix | 15 passed |
| pytest `-n 6`, the targeted set (42 files, listed below) | 875 passed, 1 skipped, 4 xfailed |
| `module_validate.py` | PASS (the catalog records no signatures, so it was not regenerated) |

This step changed no migration, schema, DB/connection code, frontend or `src-tauri`. So there was no durability
lane, npm, vitest, cargo or DB reference run.

**Test files:** `test_teacher_te2_lessons`, `test_teacher_te2_migration`, `test_teacher_te2_probes`,
`test_teacher_te2_review_fixes`, `test_teacher_te2_sidecar`, `test_teacher_te2_successor`,
`test_teacher_te2log_activity`, `test_teacher_te2log_episodes`, `test_teacher_te2log_migration`,
`test_teacher_te2log_node_held`, `test_teacher_te2log_receipt`, `test_teacher_te2log_report`,
`test_teacher_te1_lesson`, `test_teacher_te1_review_fixes`, `test_probe_episodes`,
`test_characterization_probe_family_em`, `test_characterization_probe_regrade`,
`test_characterization_probe_replay`, `test_characterization_probe_submission`, `test_grade_resolution_pipeline`,
`test_blind_grading_contract`, `test_placement_split_grades`, `test_regrade_contract_replay`,
`test_rebuild_equivalence`, `test_rebuild_equivalence_review`, `test_rebuild_orchestrator`,
`test_followup_fg1d_panel_read`, `test_followup_fg1d_probe_shadow`, `test_followup_codex_review`, and the contract
tests:

- frozen cycles: `test_architecture`;
- `test_cli_help_snapshot`;
- the display-label audit: `test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`,
  `test_rw5c_labels`;
- the process-launch allowlist: `test_ai_tool_isolation`, `test_e0_isolation`, `test_codex_tool_lockdown`,
  `test_codex_lockdown_round3`;
- `test_table_roles`, `test_registry_audit`, `test_module_catalog_inventory`.

Changed test file: `tests/test_teacher_te2_review_fixes.py`, which gains one test (13 tests, 15 cases). Calls per
probe and rows per kind are unchanged from the table above.

## Final verify and the landing's rulings R1-R3

The final verify (gpt-6.1-sol, codex-job `20261106-055937-v8K8dy`) read `1831c669f9..teacher/te2`. It confirmed F1
and F2 fixed and reopened F7 on regrades. By the orchestrator's ruling there was no further Codex round. The rulings
are quoted verbatim in `docs/reviews/teacher-te2.md` ("Landing onto main"). Every test uses fakes only.

| Id | Verdict | Commit | Test |
|---|---|---|---|
| F1 | confirmed fixed | `a6fd6615fe` | unchanged |
| F2 | confirmed fixed | `a6fd6615fe` | unchanged |
| F7 (regrades) | fixed at regrade publication (R1) | `5564387090`, `af3a975871` | `tests/test_teacher_te2_landing_r1.py` (4) |

**F7 on regrades. Reproduced.** A probe answer's raw grade event and interpretation are written once, by its
submission's probe path. Replay never re-mints them: `_dual_write_grade_channel` skips `diagnostic_probe`, and
`_record_lesson_probe` skips a replay. So a regrade's replay left the active interpretation on the original grader's
identity and calibration, and later rebuilds kept it. Codex's two reproductions are the first two tests. Both failed on
the pre-fix source:

- `test_a_lesson_probe_regraded_blind_after_split_is_switched_on_carries_the_blind_calibration`: the probe is
  answered with `diagnosis.split_enabled = false` (the joint grader), split is switched on, and the probe is regraded
  blind. The active interpretation was still `grading_prompt_v1` where the regrade's
  `grading_prompt_v2_1_blind_reference_policy+own-route-v2` was expected.
- `test_a_lesson_probe_regraded_blind_under_a_newer_prompt_carries_the_newer_calibration`: split is on throughout. The
  probe's first grade is the mvp-2.0 blind identity, and its regrade uses the practice door's reference-policy prompt.
  The active interpretation was still `grading_prompt_v2_blind`.

**Fix.** `regrade._publish_regrade`, before its replay, calls `attempts.publish_regraded_probe_grade`. That is the
attempts package's door to `probe_episodes.dual_write_regraded_probe_grade`, over the edge `attempts.attempts`
already has, so the frozen-cycles contract is unchanged. It appends and activates the same dual-write the submission
made, with the replacement grade's (prompt, schema) identity: the new blind record's calibration identity, or else
the joint door's `vault_grading_calibration_identity`. The grader identity hash and the calibration model follow from
that identity. Replay reads the new pair back and mints no duplicate: each test counts exactly 2 grade events after
the regrade and after `rebuild_all_derived_state`, and the canonical cells are equal before and after the rebuild.

A grade is written only where the submission wrote one:

- a lesson probe (observed `graded`, as on its first write);
- an FG1 presentation whose observation recorded an outcome and whose new grade is not held. Its outcome is
  reclassified from the new score and the regrade's attributed error types. The probe observation's posterior is the
  submission's and is not changed.

FG1d's incidental, presentationless answer wrote none and gets none.

**FG1's presentation path.** `record_episode_evidence` now takes the submission's `grader_identity` and passes it
through `_record_presentation_observation` to `_dual_write_probe_grade`. This was the re-review's open question.
`test_fg1s_presentation_path_stamps_the_submissions_identity_and_its_regrade_the_replacements` failed on the pre-fix
source (`grading_prompt_v1` stamped on a blind submission). It now checks the first write and the regrade.

**The ordinary, non-probe regrade.** It does not have this defect.
`test_an_ordinary_practice_regrade_already_carries_the_newer_calibration` passes on the pre-fix source: the replay
re-applies the attempt, and `_dual_write_grade_channel` re-mints its grade event under the identity the new blind
record names. That re-mint happens on every replay of an ordinary AI-graded attempt, so each rebuild appends one more
raw grade event and interpretation for it. On the test vault, 2 events after the regrade became 3 after one rebuild.
This predates TE2 and lives outside the regrade's publication. It is recorded for the follow-up batch. The smallest
fix: in `_dual_write_grade_channel`, skip a replay (`attempt.replace_existing`) when the attempt's active
interpretation already comes from a raw grade event with the same identity, class and score.

**R2 and R3** are in `docs/reviews/teacher-te2.md`: the library lookup at `73b4784e41`, and the content-hash stamp
at `1a7e274d14`.
