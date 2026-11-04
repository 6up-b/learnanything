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

# Final verify (job 20261103-154719-CtSvk6): F1 reopened, F11

The verify confirmed F2-F10 fixed, reopened F1 and found F11. Orchestrator ruling R1 (recorded verbatim under "Landing onto
main" in `data-capture-a1-a6.md`) replaced F1's fix: the timing dependence goes. This supersedes two lines of the re-review's
"calls for the landing" above: the report no longer waits for the next prepare, and a section with no LO when swept is retried.

## F1 [High]: one read of Reader exposures

**Reproduced first**, AD off and data capture on, no sweep: Monday's practice, Wednesday 10:00's completed section, 10:30's correct
answer read `observed`, 1.0, skip reasons `{insufficient_delay: 1}`, and a first delayed success. After a sweep the same data read
`pending`, `{insufficient_delay: 2}`, and no success. The re-review's own helper had hidden this: it answered in one session, so
`same_session` rejected the answer before any exposure mattered. The new tests answer in a second session, and a control test with
no section read shows the same answer is the cold success.

**The fix.** `data_capture.reading_exposures.read(connection, vault, repository)` is the one read: the stored receipts (data
capture's and AD's) plus the source activity not yet swept, through the sweep's collectors, mapping and source time. Router v3's
derivation, the time metric, the report, the scoreboard, similar decisions, `router log` and `router report`, `settle` and a rebuild
all pass it (`reader_exposures=`). `sweep` writes exactly the list `read` adds, so it only freezes. The window is gone from the sweep
too: a row stamped before an earlier sweep but committed after it, or a section whose LOs appear later, would otherwise be read and
never frozen. A test derives everything before and after a sweep and compares whole results.

**Without a vault** a derivation can't map, so `reader_exposures=None` means the stored receipts alone. A test walks `src/` and fails
on any production call that doesn't name it.

**If the read itself fails in `settle`,** an answer waits for the next pass rather than being judged on less. The sweep's failure
still never stops the states.

**The module moved** from `daily_plan/` to `data_capture/`: the scoreboard and the rebuild must read it, and `diagnosis` importing
`daily_plan` breaks the TUI's contract. `reading_learning_objects` moved with it (the objective's freeze imports it), and
`OUTCOME_VERSION_V3` moved to `data_capture.gates` (`router.outcomes` still exports it), since `data_capture -> router` would cycle.
Two function-local edges join the frozen-cycles ignore list, with the reason: to `adaptive_difficulty.reading` and
`reader.reader_progression`.

**Cost**, measured with the read on copies of the owner's mvp-0.43 vaults: 300 to 430 ms with nothing swept (`linear_algebra` 79
exposures, `probability` 75), 2 to 70 ms after a sweep, 25 ms on `arxiv_v2` with no activity. One indexed lookup per Reader source row,
plus a document load and an LO scan (about 20 ms) per distinct section or span not on record, cached for the call. The database hash
was unchanged after the read under a read-only repository. Today's path reads it in `settle` only when an open check has an answer, and in similar decisions only at version 3 with that feature on.

**What stays, Low under R1.** A row on record is never mapped again, which is what freezing means. So if a section's LOs change
between its sweep and a later answer, the LO added reads differently with and without that sweep. Reaching a warm answer with a cold
label needs an existing LO with older practice, newly named on a section (a coverage row) read under 24 hours before the answer, with a
sweep in between. An LO created from the section cannot reach it: it has no older exposure, and an unobserved delay never qualifies.

## F11 [Medium]: a shared check measures its frozen objective

**Reproduced first:** a broad check on A's item and B's item was shared with A's warm measurement, and B's delayed answer wrote
`answered` on A, with A's outcome still pending and no duty left.

**The fix.** A check is shared only when all its candidates are on the objective's LO, for a new decision and a replacement alike. A
broader one keeps its own decision and its items stay held, since a new commitment on them would replace it. `settle` also validates
the satisfying attempt's LO before `answered`, because a check's candidates can widen after it was shared: another LO's answer reads
`answer_other_objective` (the answered LO in the detail), and the duty stays. It takes the same one replacement a warm answer takes
(R4's reasoning: each one costs a question), and a second one ends it as `replacement:answer_other_objective`.

## Rename

`problems_to_cold_success` is `problems_to_first_unassisted_success`, in `b5_scoreboard_v2` with its companion. B5's order is
unchanged. Specs keep the name they were written with. The two frontend comments are comments only; `npm run typecheck` exits 0.

## Gate for this step

Memory-capped scope, `-n 6`. Full suite not run (landing gate only).

* `lint-imports --no-cache`: **42 kept, 0 broken**.
* Targeted `pytest` (12 `test_data_capture_*` files, `test_router_outcomes`, `test_scoreboard`, `test_table_roles`,
  `test_coordinated_migrations`, `test_architecture`, and the other derivation callers: `test_router_r2c_retrieval`,
  `test_router_r2b_agreement`, `test_router_r2bc_landing`, `test_router_coldness_covariates`, `test_router_presentations`,
  `test_router_g4_restraint`, `test_rebuild_orchestrator`, `test_shadow_rebuild`, `test_held_grade_composition`,
  `test_teacher_te1b_suggestions`, `test_teacher_te1b_review_fixes`, `test_followups_batch6_review_fixes`, `test_reader_rw3a_landing`,
  `test_daily_plan_replay`, `test_voi_forecasts`, `test_mvp015_upgrade`): **441 passed, 0 failed**.
* `--durable-sqlite` on the 12 `test_data_capture_*` files: **190 passed, 0 failed**.
* Frontend: `npm run typecheck` in `apps/learnloop-tauri`: exit 0.

# Scoped verify (job 20261103-190644-2tE7S8): rulings R6 and R7

The verify found F1 and F11 closed, with one Medium and one Low. Rulings R6 and R7 are recorded under "Landing onto main" in
`data-capture-a1-a6.md`. The section above still describes step 0; these four changes supersede the parts they name: the
sweep's window, the module's exemptions, and the `None` fallback.

## Finding 1 [Medium] (R6): the sweep on the foreground path

**Reproduced first:** 100 mapping calls on every sweep of 100 unmapped sections, with no receipt written.

**The fix.** The sweep reads from the newest recorded source time less `SWEEP_OVERLAP` (AD's constant, moved with the collectors),
and takes the write lock only with rows to write. A repeat sweep with nothing new makes 0 mapping calls, tested by counting,
including empty results. Correctness rests on the live read, which still lists everything: a row past the window stays readable,
tested. Mappings, empty results included, are kept per process against a revision of the vault's content and of the extraction
runs, artifacts, aliases and coverage rows they read. A read failure is not kept, so a passing lock can't lose an exposure.

**Foreground callers**, each on Today's build, a plan read or the deciding poll, through `prepare_queue_build` or the chooser:

* `measurement.settle`'s sweep: windowed, as above.
* `measurement.settle` judging an answer: `read_for_answer`, only when an open check has an answer. It lists activity since the
  earlier of the sweep's window and the delay before the answer, since an older exposure can't make that answer warm.
* `router_retrieval._matured` (similar decisions, version 3 with that feature on): stored receipts plus the sweep's window.

Everything else that reads is off the foreground and reads everything: `data-capture report`, the scoreboard, `router log`,
`router report` and a rebuild.

**Measured** on fresh copies of the mvp-0.43 vaults, before (step 0's tip) and after. The whole read is what settling an answer and
similar decisions used before; the foreground read is what they use now.

| | `arxiv_v2` | `linear_algebra` | `probability` |
|---|---|---|---|
| First sweep ever, before / after (one time, writes the receipts) | 10 / 31 ms | 131 / 500 ms | 118 / 357 ms |
| Repeat sweep, before | 7 ms, 1 mapping | 19 to 30 ms, 3 mappings | 5 ms, 0 |
| Repeat sweep, after | 5 ms, 0 | 6 ms, 0 | 5 ms, 0 |
| First sweep in a new process, after | 30 ms, 1 mapping | 76 ms, 3 mappings | 5 ms, 0 |
| Whole read after a sweep, before | 24 ms, 1 mapping | 67 ms, 3 mappings | 2 ms, 0 |
| Whole read after a sweep, after | 2 ms | 3 ms | 2 ms |
| Foreground and answer read, after | 2 ms | 2 ms | 2 ms |

The revision itself costs about 1 ms. The first-sweep times moved on the same code path, so I read that row as cold-start and machine
noise, not a regression, but I did not establish that; it happens once per vault. A new process maps again the rows the window can't
exclude: unmapped tutor exchanges, which that collector lists regardless of time, and with no receipts at all, everything once.
Today's time against main below mvp-0.44 is in the landing record's smoke.

## Finding 2 [Low]: one recorded LO hid a later one

**Reproduced first** with Sol's case: Monday's practice on B, Wednesday 10:00's section mapped to A, a sweep, 10:15's coverage row
naming B, 10:30's answer on B read `completed`. Now `not_delayed`, pending, no first delayed success, and the same after another sweep.

**The fix** is the small one the brief named: `read` unions a section's coverage rows through one progress-and-coverage join.

**What stays Low:** the join covers coverage rows on completed sections. A provenance link added to the vault after a section was
recorded still reads differently with and without a sweep, and so does a question or passage view whose section gains a coverage row.
Sol's fuller fix, remapping provenance by content revision, would make the freeze meaningless, so I left it (R6: later cases on this
class are Low).

## `reader_exposures` is required

It is a required keyword on `derive_router_outcomes`, `rebuild_router_outcomes`, `trajectories` and `answer_completion`, and `None` at
version 3 raises `ValueError`. The rebuild with no decisions passes `[]`. A test replaces the AST walk. `similar_decisions` with a
vault and no repository at version 3 now fails closed into its existing "unavailable" path.

## R7: the frozen-cycles list stays frozen

Two dependency-light helpers, with no switch, write or clock:

* `learnloop.reading_sources`: the list of Reader sources, moved from `adaptive_difficulty.reading`, which imports it back. The
  firewall's three vocabulary constants moved with it and the firewall imports them back, since the list can't import `attempts`.
* `learnloop.section_map`: the Reader's section-to-LO mapping, moved from `reader_guidance` and `reader_progression`, which keep their
  names.

The two exemptions are gone, so the frozen-cycles list equals main's. `lint-imports`: 42 kept. `section_map`'s import of the alias
authority isn't graphed, because `learnloop.content` is a namespace package; at import time that module reads only the clock, the
connection and `ingest`, so it adds no real cycle.
