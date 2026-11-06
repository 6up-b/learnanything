# Router TE3b (lesson offers in the router objective): Codex review and fixes

Branch `router/te3b-lesson-offers`, worktree `learnanything-te3b`, base main `8b0738499d`. The Codex review
(gpt-6.1-sol, job `20261106-150824-KcRMNf`) made four findings against the stage tip `f37a77599b`. Each was reproduced
with a failing test on the pre-fix sources (the fixed `src/` files set aside, `git checkout -- src`, the new tests run,
the fixed files restored; no stash), then fixed.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | A late generated probe becomes stranded inside an offer block | fixed | `02ca6dafac` | `tests/test_te3b_codex_review.py::test_f1_*` (5 cases). Pre-fix: the probe was written into the offer block and the card served (`'lesson_offer' == 'item'`) |
| F2 | Medium | The kill switch does not withdraw prefetched offers | fixed | `02ca6dafac` | `tests/test_te3b_codex_review.py::test_f2_switching_off_takes_back_a_prefetched_offer_and_its_card`. Pre-fix: the plan view still carried the waiting card with the switch off |
| F3 | Medium | Switch-off daily draws still learn from TE3b offer history | fixed | `02ca6dafac` | `tests/test_te3b_codex_review.py::test_f3_with_the_switch_off_the_daily_draw_never_learns_from_offer_responses`. Pre-fix: the day's draw logged `updates: 1` and moved means where the predecessor's ledger has none |
| F4 | Medium | The duration sensor reads receipts unknown at its cutoff | fixed | `02ca6dafac` | `tests/test_te3b_value.py::test_the_duration_sensor_reads_only_intervals_received_by_its_decision` (pre-fix `[30.0] == []`), `tests/test_te3b_clock.py::test_the_serving_clock_reads_only_lesson_intervals_received_by_now` (pre-fix `20.0 == 0.0`) |

## What changed

**F1 and F2: an unanswered offer is taken back (`lesson_offer.withdraw`).** An offer block never holds items. In
`engine._insert_followups` and `engine._place_followup_probes`, an offer block is now a boundary, like a reading
block, so a follow-up or a probe that FG1 makes ready while the offer waits is returned as forced, not written into
the block. In `advance_with_context`, an offer block that nobody answered is withdrawn when forced items arrived
(`forced_items`) or when lesson offers no longer serve (`offers_off`: the switch, the objective or the tag, read by
`lesson_offer.offers_on`). The plan then crosses the next boundary at once, with the forced items first (F1) or with
the predecessor's support (F2). A withdrawal:

- ends the block with outcome `withdrawn` (its reason on the `block_ended` event; it counts no minutes);
- writes an `expired` row on the offer's decision, with `{"withdrawn": <why>, "plan_offer": true, "block_id": ...}`.
  This is an existing release kind, so there is no migration and no schema change. It is not one of the learner's
  responses: the acceptance model (`LS.observations` reads only responses), the decline recovery (it reads
  `released`), the forecast binding (it stays censored as `offer_unanswered`) and the offer report never read it as
  an answer. `lesson_offer.sweep_ignored` and TE1b's `_sweep_ignored` skip a decision that has one, so a withdrawn
  offer is never later recorded as `ignored`. A TE1b daily card can only get a release after a Start, so TE1b's sweep
  behaves exactly as before.

`lesson_suggestion.respond` refuses an answer (`not_found`, "That suggestion is no longer in your plan.") to an
unanswered offer that was withdrawn, or to any unanswered offer while offers are off. A Start recorded before the
plan reads again is kept, and the probe is served at the next boundary (tested). A Start that never opened (TE1b
ruling R2) is still honoured either way: `_recovered` and the race check still read every decision.

The plan view's row shows an offer's card while the block waits only when offers serve. An ended block keeps its card,
which records what was answered (`view._offer_card_shown`).

A shown card is withdrawn too when a probe becomes ready. The probe comes first, and the card was not the learner's
answer, so it is neither `ignored` nor declined.

**F3: the daily draw's ledger.** `lesson_suggestion._model(connection, with_offers=...)`. With lesson offers on
(`router_objective_switches.lesson_offers_on`), offers and cards share one acceptance model, as built. Off, or below
the tag, it reads `store.decisions` only: TE1b's own ledger. The model, the context's "days since last", the decline
days and the ceiling count are then the predecessor's. The test checks the logged `P(accept)` of every candidate
against the priors' model, and it checks `model`, `days_since_last` and `shown_today`.

**F4: decision-time receipts.** `lesson_offer.lesson_active_minutes` (the duration sensor) reads only intervals with
`received_at <= at`. `price.lesson_spans` and `price.activity_spans` take `received_by`, and the serving clock
(`session_active_minutes`) passes `now` when lessons are on. Outcome windows read after the fact (RO5's realized cost,
RO6's rewards in `scores._sessions`) still count every interval that happened in the window: this is deliberate,
because those are outcomes and not features. With lessons off, the reads are the predecessor's exactly. The test
fixture `test_te3b_value._lesson_db` now carries migration 247's receipt columns (`occurred_at`, `received_at`,
`receipt_version`).

No new model request, route, table, column, migration, config key or decision parameter. `withdrawn` is a structural
outcome, not a constant. Below the tag, and with the switch off and no offer ever drawn, every touched path is
unchanged: an offer block cannot exist, `all_decisions == decisions`, and `lessons=False` bypasses the receipt filter.

## Claims in the review that no longer hold

- "Off restores TE1b's card and predecessor support exactly": F2 (a waiting offer is withdrawn and the next boundary
  is the predecessor's) and F3 (the off ledger is TE1b's) are tested.
- "No offer beside a probe": F1's asynchronous case is tested for Next, Start, decline, the shown card and a Start
  answered before the plan's next read.
- "Duration sensors reflect information available at the decision": F4 is tested on the receipt columns.

Not changed (outside these findings, and already recorded as unbuilt in `docs/reviews/teacher-te3b.md`): the
in-lesson checks and probes as observations, the transfer check, the learned spread of the duration.

## Commits

- `02ca6dafac`: F1 to F4, the code with its reproduce-first tests, and the As-built note in `spec_teacher_v1.md`
  §15.1a ("Responses"). One commit, because `lesson_offer.py` carries both F1/F2's withdrawal and F4's receipt
  cutoff.
- The commit that adds this file: the review record.

## Gate

Owner rule (2026-10-17): no full suite here. Every pytest run was inside `systemd-run --user --scope --quiet -p
MemoryMax=5G -p MemorySwapMax=1G`, at `-n 6` or fewer, one run at a time; the large run was also behind `flock
/tmp/learnloop-fullsuite.lock`. `TMPDIR` was outside the worktree. lint-imports ran under `env -i` with empty `HOME`,
`CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. No live or paid call was made.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install --offline pypdfium2==5.14.0` | ok |
| `uv run lint-imports --no-cache` | 43 contracts kept, 0 broken (including "Existing deferred cross-package cycles are frozen") |
| Reproduce-first: the new tests (7 in `test_te3b_codex_review.py`, 1 in `test_te3b_value.py`, 1 in `test_te3b_clock.py`) against the pre-fix `src/` | 9 failed (each finding's behavioral assertion; for F3 the logged model `updates: 1` against the predecessor's 0). With the fixes: 16 passed (those three files) |
| Targeted run: every test file that exercises a changed module (`daily_plan.engine`, `lesson_offer`, `lesson_suggestion`, `daily_plan.view`, `router_objective.price`/`activity_spans`/`session_active_minutes`), every follow-up and TE3b file, plus the contract tests (CLI help snapshot, Codex lockdown frozen list and tool lockdown, plain-words and "why" copy audits, architecture, registry audit, desktop RPC contract, serializer snapshot, table roles, tracked fixture databases, module catalog, mobile allowlist, sidecar registry). 192 files, `-n 6` (list below) | 3949 passed, 13 skipped, 3 failed (47 min). The three failures are below |
| The three failures, rerun | `test_ro0_rows9_13_decision_state.py` (all) and `test_followup_next_matrix.py::test_f21_*`: passed. `test_te3b_codex_review.py`: 6 passed, 1 failed (another case, same cause as below) |
| After the test-helper fix: `test_te3b_codex_review.py` five times | 7 passed each time (35 of 35) |
| `test_followup_next_matrix.py` six times | 71 passed each time (426 of 426) |

The three failures:

1. `test_te3b_codex_review.py::test_f3_*` (and, on the rerun, `test_f1_a_shown_card_*`). The test helper's first
   objective boundary was served `stop` by RO5's stop coin (a seeded draw; the `offer_drawn` fixture forces only the
   mix's draw). The helper `_env` now sets `[router_objective] stop_coin = 0.0`, as `test_ro5_checks.py` does. This
   was a test flake, not a code defect.
2. `test_followup_next_matrix.py::test_f21_a_displaced_unserved_probe_makes_next_open_it`: the plan was closed (a
   `reentry` plan, built from a wall-clock gap under load). That vault is at `FOLLOWUP_SERVE_ALGORITHM_VERSION`, below
   TE3b's tag, so no offer block can exist and none of this step's changes run there. The test passed 6 of 6 reruns
   of its file. It is a pre-existing timing flake.
3. `test_ro0_rows9_13_decision_state.py::test_receipts_hold_ids_and_numbers`: the known check where the title "M2"
   can occur inside a random ULID (recorded in `docs/reviews/teacher-te3b.md`'s gate). It passed on rerun.

Not run, and why:

- npm/vitest/frontend build: no frontend file changed. The plan view only drops its `lesson_offer` key on a waiting
  offer's row while offers are off, and `DailyPlanView`/`TodayPlace` already render that row without a card.
- cargo check: nothing under `src-tauri` changed.
- Durability lane, DB reference scripts: no migration and no schema, DB or connection code change.

Test files of the 192-file run: test_ad1_codex_rereview_fixes.py test_ad1_codex_review_fixes.py
test_ad1_outside_and_cli.py test_ad23_contract.py test_ad23_fix_r5.py test_ad23_fix_r8.py test_ad23_fix_review.py
test_ad23_intent_compose.py test_ad23_inversion.py test_ad23_owner_decisions.py test_ad23_pool_membership.py
test_ad2_model.py test_ad2_serving.py test_ad3_monitoring.py test_ad3_reading.py test_ad3_subject_view.py
test_adaptive_difficulty_ad1.py test_ad_epoch.py test_ad_guard_offer_receipts.py test_ad_guard.py
test_ad_guard_reachable_reads.py test_architecture.py test_block_chooser_interface.py test_cli_help_snapshot.py
test_codex_lockdown_frozen.py test_codex_tool_lockdown.py test_curriculum_c1_codex_review_fixes.py
test_curriculum_c1_fix_round2.py test_curriculum_c1_fix_round3.py test_curriculum_c1_fix_round4.py
test_curriculum_c1_plan_follows_path.py test_curriculum_c1_round5_followups.py test_daily_plan_build.py
test_daily_plan_composition.py test_daily_plan_kill_switch.py test_daily_plan_owner_decisions.py
test_daily_plan_reentry.py test_daily_plan_replay.py test_daily_plan_review_regressions.py test_daily_plan_rpc.py
test_data_capture_a1_prefilter.py test_data_capture_a2_measurement.py test_data_capture_a4_delayed_completion.py
test_data_capture_a5_not_ready_floor.py test_data_capture_report.py test_data_capture_successor.py
test_desktop_rpc_contract.py test_dl2_rw4b_keyed_pick_check.py test_evsi_staged_binding.py
test_exam_protection_landing.py test_followup_codex_review.py test_followup_diagnostic_selection.py
test_followup_fg1c_codex_review.py test_followup_fg1c_r1_exposure_independence.py test_followup_fg1d_panel_read.py
test_followup_fg1d_probe_shadow.py test_followup_generate_e2e.py test_followup_journey.py test_followup_live_shape.py
test_followup_migration.py test_followup_next_matrix.py test_followup_reserved_only.py test_followup_rival_factor.py
test_followup_router.py test_followups_batch5_c5_ledger.py test_followups_batch5_lesson.py
test_followups_batch5_recap_dependencies.py test_followups_batch5_recap_protection.py
test_followups_batch6_power_probe_cache.py test_followups_batch6_prefetch_decided_once.py
test_followups_batch6_prefetch_next_section.py test_followups_batch6_prefetch_plan_wait.py
test_followups_batch6_review_fixes.py test_followups_batch6_router_report.py test_followups_batch6_te1b_card.py
test_followups_batch6_verify_fixes.py test_followups_batch7_note_titles.py
test_followups_batch7_prefetch_capped_resume.py test_followups_batch7_prefetch_link_served.py
test_followup_single_use.py test_followups_nov2_figure_provenance.py test_followups_nov2_help_fold.py
test_followups_nov2_note_gap_unlinked.py test_followups.py test_followup_successor.py test_followup_workflow.py
test_intent_codex_rereview.py test_intent_codex_review.py test_intent_exclusion.py test_intent_fix_round4.py
test_intent_fix_round5.py test_intent_fix_round6.py test_intent_fix_round7.py test_intent_goal_deadline.py
test_intent_plan.py test_learner_pick_proposal.py test_mcp_c1a_narrow.py test_mcp_tools.py
test_method_explicit_landing.py test_method_explicit_upgrade.py test_mobile_allowlist.py
test_module_catalog_inventory.py test_mvp011_upgrade.py test_mvp014_upgrade.py test_mvp015_upgrade.py
test_mvp016_upgrade.py test_mvp017_upgrade.py test_mvp018_upgrade.py test_mvp020_upgrade.py test_mvp021_upgrade.py
test_mvp023_upgrade.py test_mvp024_upgrade.py test_plan_determinism_landing.py test_plan_determinism.py
test_plan_follows_path.py test_reader_rw4b_admission_idempotency.py test_reader_rw4b_fix6.py
test_reader_rw6b_p2_landing.py test_reading_step_switch.py test_registry_audit.py test_ro0_codex_review.py
test_ro0_codex_verify.py test_ro0_gate.py test_ro0_report.py test_ro0_row10_cold_timing.py
test_ro0_row12_trajectory.py test_ro0_row3_ask_availability.py test_ro0_rows7_8_sessions.py
test_ro0_rows9_13_decision_state.py test_ro1_availability_reads.py test_ro1_successor.py test_ro1_upgrade_report.py
test_ro2_ad_raw_document_reads.py test_ro2_history_forecaster.py test_ro2_history_resolve.py test_ro4_codex_review.py
test_ro4_objective_serving.py test_ro4_price.py test_ro4_successor.py test_ro4_trace_report.py test_ro5_checks.py
test_ro5_codex_rereview.py test_ro5_landing.py test_ro5_successor.py test_ro6_landing.py test_ro6_successor.py
test_rofu_carried.py test_rofu_review_draw.py test_rofu_successor.py test_router_card.py test_router_g1_feasibility.py
test_router_g4_restraint.py test_router_g7_fallback.py test_router_presentations.py test_router_r1_composition.py
test_router_r2a_landing.py test_router_r2a_serving.py test_router_r2b_serving.py test_router_r2c_retrieval.py
test_router_r2c_teach_back.py test_router_reader_activity.py test_router_why_copy.py test_rw5c_plain_words.py
test_rw7b_codex_review_fixes.py test_rw7b_fix_round2.py test_serve_eligibility.py test_serve_eligibility_review.py
test_sidecar_registry.py test_sidecar_serializer_snapshot.py test_table_roles.py test_te3a_successor.py
test_te3b_binding.py test_te3b_clock.py test_te3b_codex_review.py test_te3b_features.py test_te3b_offers.py
test_te3b_population.py test_te3b_successor.py test_te3b_value.py test_teacher_te1b_landing_r2.py
test_teacher_te1b_migration.py test_teacher_te1b_rereview_fixes.py test_teacher_te1b_review_fixes.py
test_teacher_te1b_suggestions.py test_teacher_te1_successor.py test_teacher_te2_successor.py
test_tracked_fixture_databases.py test_ux_phase4_feedback.py test_ux_phase4_landing.py test_voi_merge_composition.py
test_voi_stopping.py test_voi_v2.py

## Re-review

The Codex re-review (gpt-6.1-sol, job `20261106-163121-c2hoHo`) of `0baa4ab39c` confirmed F1, F2 and F4 fixed and
reopened F3. It found no new defect in the fix commits.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | A late generated probe becomes stranded inside an offer block | confirmed fixed | `02ca6dafac` | (re-review: confirmed) |
| F2 | Medium | The kill switch does not withdraw prefetched offers | confirmed fixed | `02ca6dafac` | (re-review: confirmed) |
| F3 (reopened) | Medium | Switch-off decline recovery still reads offer responses | fixed | `7e43d795e1` | `tests/test_te3b_codex_review.py::test_f3_reopened_switch_off_decline_recovery_never_reads_an_offer_response[declined]` and `[released]`. Pre-fix: both failed, the offered LO's logged candidate carried `days_since_decline: 2.0` where the predecessor logs `None` |
| F4 | Medium | The duration sensor reads receipts unknown at its cutoff | confirmed fixed | `02ca6dafac` | (re-review: confirmed) |

**What changed (F3).** `router.lesson_suggestions.declines_by_learning_object` took a decision map and ignored it.
Now it reads only the response and release rows whose `decision_id` is in that map, as `observations` already did.
With lesson offers off, the daily draw passes TE1b's own decisions (`_model(with_offers=False)`), so neither an
offer's "Not now" (`declined`) nor a Start let go on its pending card (`released`) dates a switch-off candidate. With
offers on, both callers (the daily draw and `lesson_offer`) pass every decision (`store.all_decisions`), so they read
exactly what they read before. Below TE3b's tag no offer decision exists, so every response is on a daily decision and
mvp-0.52's ledger reads byte-identically. No schema change, no new parameter, no model request.

**The test.** For each response kind, an offer is drawn and answered, then the switch is turned off and a draw two days
later runs. The test asserts three things. First, the offered LO is a candidate of that draw. Second, on the same
ledger, the decline map holds the LO when it is read with every decision and is empty when it is read with TE1b's
decisions only. Third, every logged candidate has `days_since_decline: None`, and its logged `p_accept` equals the
priors' acceptance computed from the logged context with no decline term, which is what the predecessor logs. Unlike
the first F3 test, this one recomputes from a candidate with the decline age cleared, so it no longer inherits a
contaminated input.

### Re-review gate

Every pytest run was inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at `-n 6`, one
run at a time, with `TMPDIR` outside the worktree. lint-imports ran under `env -i` with empty `HOME`, `CODEX_HOME` and
`LEARNLOOP_CONFIG_DIR`. No live or paid call was made, and no full suite was run (owner rule, 2026-10-17).

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install --offline pypdfium2==5.14.0` | ok |
| `uv run lint-imports --no-cache` | 43 contracts kept, 0 broken (including "Existing deferred cross-package cycles are frozen") |
| Reproduce-first: `pytest tests/test_te3b_codex_review.py -k f3` on the pre-fix `src/` | 2 failed (the new `[declined]` and `[released]` cases), 1 passed (the first F3 test) |
| The same, with the fix | 3 passed |
| Targeted run, 28 files, `-n 6` (list below) | 556 passed, 1 skipped, 0 failed (100 s) |

Not run, and why: no frontend, `src-tauri`, migration, schema, DB or connection code changed (so no npm/vitest/cargo,
no durability lane, no DB reference scripts).

Test files of the targeted run: every test file that names `lesson_suggestions`, `lesson_suggestion` or
`declines_by_learning_object` (test_data_capture_a4_delayed_completion.py test_data_capture_successor.py
test_followups_batch6_review_fixes.py test_followups_batch6_router_report.py test_followups_batch6_te1b_card.py
test_ro0_codex_review.py test_te3b_binding.py test_te3b_clock.py test_te3b_codex_review.py test_te3b_features.py
test_te3b_offers.py test_te3b_population.py test_te3b_successor.py test_te3b_value.py test_teacher_te1b_landing_r2.py
test_teacher_te1b_migration.py test_teacher_te1b_rereview_fixes.py test_teacher_te1b_review_fixes.py
test_teacher_te1b_suggestions.py test_teacher_te1_successor.py), plus the contract tests: test_cli_help_snapshot.py,
test_codex_lockdown_frozen.py, test_codex_tool_lockdown.py (process-launch lockdown), test_architecture.py,
test_rw5c_plain_words.py and test_router_why_copy.py (copy and display-label audits), test_registry_audit.py and
test_sidecar_serializer_snapshot.py.
