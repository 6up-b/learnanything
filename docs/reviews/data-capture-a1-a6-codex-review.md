# Data capture A1-A6: Codex re-review (job 20261103-145106-nGX6Yc)

Reviewed `9cd91ef176..e2ddd03c64` on `data/capture-a1-a6`. Fixes are in `81c99679c0`; each was reproduced first with a failing
test in `tests/test_data_capture_codex_rereview.py`, run against the unfixed code. No model call, no spend, no GUI, no owner vault opened.
The record the review found absent (the F1-F8 round's edits to `docs/reviews/data-capture-a1-a6.md`) was uncommitted in the
worktree and went in with `81c99679c0`.

## Findings

| id | severity | title | verdict | commit | test or reason |
| --- | --- | --- | --- | --- | --- |
| F1 | High | With AD's forecast logging off, a completed section supplied no exposure, so a warm answer got a cold label (router and time metric) | fixed | 81c99679c0 | `test_f1_a_completed_section_is_an_exposure_with_ad_off` (reproduced: `observed`, 1.0) and 8 more `test_f1_*` |
| F2-F6, F8 | - | Confirmed fixed by the reviewer | no change | e2ddd03c64 | `tests/test_data_capture_codex_review.py` rerun, all passing |
| F7 | - | Reopened by the reviewer as F10 | fixed under F10 | 81c99679c0 | see F10 |
| F9 | Medium | Decisions sharing a check got a replacement question each | fixed | 81c99679c0 | `test_f9_two_decisions_on_one_warm_check_share_one_replacement` (reproduced: two commitments), `test_f9_the_one_replacement_answered_cold_measures_both`, `test_f9_a_later_settlement_reads_the_pending_replacement_from_serving`, `test_f9_a_pending_check_due_too_soon_is_not_the_replacement` |
| F10 | Medium | A re-offered measurement stayed `unavailable` | fixed | 81c99679c0 | `test_f10_an_offer_after_a_postponement_and_a_lost_plan_restores_it` (reproduced), `test_f10_the_same_reason_after_another_offer_is_a_new_transition` (reproduced) and 5 more `test_f10_*` |

No finding was rejected.

## What changed

**F1.** AD's spec keeps its own receipt under `forecast_receipts` (G-AD1-11: off, no row), so the sweep was not switched on
for it. Data capture has its own record, `reading_exposure_receipts` (RECEIPT, in the unlanded migration 239), written by
`learnloop.daily_plan.reading_exposures`. It reads AD's list of sources through AD's collectors (`reading.listed_events`,
factored out; AD's sweep calls it too, unchanged in behaviour) over a plain row reader and map: no AD operation opens, no daily cap
(the delay runs from the newest exposure), no withholding, no doses. It maps a section as the objective's freeze does
(`reading_learning_objects`), so both name the same LOs. It runs first in `measurement.settle`, under either data capture switch
at every version, and fails soft. Its first sweep reads the whole history. The router's ledger and the time metric read it beside AD's receipts.

**F9.** A replacement shares a pending check on the LO that opens past the window, as `_arrange` does for a new decision. `settle`
keeps the replacements made in its pass by LO, since `serving` predates them.

**F10.** `decision_measurement_events` gains `episode` in its uniqueness: a due date opens an episode, each presentation opens one, a
loss belongs to the newest. Every presentation since the check came due is now written, not only the first. A plan's unplanned
reason now counts on any day the check was not offered, not only when it was never offered since coming due. A `due` for a check found
already satisfied keeps one row and is stamped at the answer, so it cannot tie with the warm answer's event in the fold.

## Calls for the landing to check

* Migration 239 was edited in place because it has not landed; the head fixture was rebuilt from the tracked 238 with the earlier
  stage script (`applied [239]`, checkpoint (0, 0, 0), `delete`, `integrity_check` ok, `foreign_key_check` empty, header 1/1).
* **Not changed: AD's dose outcomes** still read AD's receipts and the exposure events through the material view, which is its
  protection boundary. Dose rows exist only for AD's own draws. If `forecast_receipts` is turned off after draws were logged, Reader
  activity in the off period is not seen by those outcomes. Router and time metric are not affected.
* **`learnloop data-capture report` stays read-only**, so a section read since Today last prepared counts only after the next prepare.
  The source time is kept and outcomes derive at read time, so the next sweep corrects it.
* A section with no mapped LO when swept is not retried once the window has passed, as with AD's sweep.

## Gate

Every test command inside the memory-capped scope, at most `-n 6`; every Python or CLI run outside pytest under `env -i` with
empty, existing `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR` and routes off. Full suite not run (owner rule, landing gate only).

* `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`.
* `lint-imports --no-cache`: **42 kept, 0 broken**.
* Targeted `pytest -n 6` over the 114 files below: **7487 passed, 6 skipped, 0 failed** (33:48).
* `pytest -n 6 -m durability` on `test_data_capture_migration`, `test_coordinated_migrations`, `test_table_roles`,
  `test_tracked_fixture_databases`: **3 passed**.
* `pytest -n 6 --durable-sqlite` on `test_data_capture_codex_rereview`, `test_data_capture_codex_review`,
  `test_data_capture_a2_measurement`, `test_data_capture_migration`, `test_data_capture_report`: **98 passed**.
* `db_generate_reference.py`, `db_validate_reference.py`: **errors []** (schema head 239, 378 table notes).
* Frontend and `src-tauri`: unchanged, so no npm or cargo step.

The targeted run was against `81c99679c0`; the only later changes are this record, `docs/reviews/data-capture-a1-a6.md` and the
regenerated references.

Test files of the targeted run:

```
test_ad1_fix_round4.py
test_ad1_migration.py
test_ad1_reading_opportunities.py
test_ad23_contract.py
test_ad23_fix_r8.py
test_ad23_fix_review.py
test_ad23_migration.py
test_ad23_successor.py
test_ad3_dose_arm.py
test_ad3_reading.py
test_ad_epoch.py
test_ad_guard_offer_receipts.py
test_ad_guard.py
test_ad_guard_reachable_reads.py
test_ad_projection.py
test_ad_protected_readings.py
test_ad_protected_tables.py
test_approach_maps_schema.py
test_architecture.py
test_block_chooser_interface.py
test_commitment_arcs.py
test_coordinated_migrations.py
test_daily_plan_build.py
test_data_capture_a1_prefilter.py
test_data_capture_a2_measurement.py
test_data_capture_a3_time_metric.py
test_data_capture_a4_delayed_completion.py
test_data_capture_a5_not_ready_floor.py
test_data_capture_a6_delayed_pick.py
test_data_capture_codex_rereview.py
test_data_capture_codex_review.py
test_data_capture_migration.py
test_data_capture_report.py
test_data_capture_successor.py
test_deliverable_curriculum_migration.py
test_diagnosis_replay.py
test_dl2_rw4b_keyed_pick_check.py
test_exam_protection_review.py
test_figure_prefetch_migration.py
test_followups_batch6_review_fixes.py
test_held_grade_composition.py
test_help_assist_figures_migration.py
test_help_assists_schema.py
test_help_assist_work_md_migration.py
test_hint_telemetry.py
test_intent_checks.py
test_intent_codex_rereview.py
test_intent_codex_review.py
test_intent_fix_round4.py
test_intent_orchestrator_rulings.py
test_learner_claim_application_migration.py
test_learner_claim_superseded_migration.py
test_learner_gap_unlinked_migration.py
test_learner_notes_migration.py
test_learner_note_source_kind_migration.py
test_learner_notes_vault_origin_migration.py
test_library_asks_migration.py
test_method_explicit_upgrade.py
test_migrations.py
test_mobile_allowlist.py
test_mvp010_upgrade.py
test_mvp011_upgrade.py
test_mvp013_upgrade.py
test_mvp014_upgrade.py
test_mvp015_upgrade.py
test_mvp016_upgrade.py
test_mvp017_upgrade.py
test_mvp018_upgrade.py
test_mvp020_upgrade.py
test_mvp021_upgrade.py
test_mvp022_upgrade.py
test_mvp023_upgrade.py
test_mvp024_upgrade.py
test_p3_journeys.py
test_pfc_unverified_unassessed.py
test_plan_determinism.py
test_plan_follows_path.py
test_public_tip_guards.py
test_reader_ca2_fix_orchestrator.py
test_reader_rw3a_landing.py
test_reader_rw3b_migration.py
test_reader_rw7a_migration.py
test_reader_session_digests_migration.py
test_reading_step_switch.py
test_rebuild_orchestrator.py
test_recurrence_commands.py
test_registry_audit.py
test_regrade_contract_upgrade.py
test_retrieval_spaces_migration.py
test_router_coldness_covariates.py
test_router_g1_feasibility.py
test_router_g4_restraint.py
test_router_outcomes.py
test_router_presentations.py
test_router_r2b_agreement.py
test_router_r2bc_landing.py
test_router_r2c_retrieval.py
test_route_rules_in_grader.py
test_rw2d_receipts_migration.py
test_rw5c_migration.py
test_salience_firewall.py
test_section_coverage_migration.py
test_session_ownership_migration.py
test_shadow_rebuild.py
test_sqlite_file_copies.py
test_t1_batch_origin_migration.py
test_table_roles.py
test_teacher_te1b_landing_r2.py
test_teacher_te1b_migration.py
test_teacher_te1b_review_fixes.py
test_teacher_te1b_suggestions.py
test_teacher_te1_migration.py
test_teacher_te1_successor.py
test_tracked_fixture_databases.py
```
