# LP-min (a) claim fixes: Codex review and fix round

Stage `lp-claim-fixes`, branch `lp/claim-fixes` (worktree
`learnanything-lr1`), reviewed at `2275a00af` (Codex job
`20261025-123334-xQ3Jit`). Stage record: `docs/reviews/lp-min-claim-fixes.md`.
Spec: `docs/specs/spec_learned_parameters_v1.md` §3.0b items 1 and 7, LPQ9.

Every finding reproduced. Each fix has a test in
`tests/test_lp_claim_fixes_review.py`. Those tests were run against the
pre-fix sources (the six changed modules restored from `2275a00af`, then
put back): **10 failed, 6 passed**. The 6 that passed are the guards that
must hold before and after the fixes: the off-switch parity tests, the
rung-request ordering and the gap-then-attempt ordering. F6 was absent
before, so its tests were written with the feature.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Gap application is neither atomic nor retry-safe | fixed | `ade1d9e89` | `test_f1_a_gap_promotion_interrupted_before_its_row_applies_its_claim_once_on_retry`, `test_f1_a_concurrent_writer_cannot_land_between_the_gap_read_and_write`, `test_f1_off_the_predecessor_writes_a_plain_claim` |
| F2 | High | Upgrade can publish the successor without committing its state | fixed | `ade1d9e89` (+ `6d07710e1`) | `test_f2_a_death_between_publication_and_commit_is_completed_from_the_journal[upgrade_again, desktop_start]` (real fault injection: a forked process `os._exit`s after the rename), `test_f2_failures_before_or_after_the_rename_leave_the_predecessor_and_no_journal`, `test_f2_a_journal_left_after_the_commit_is_just_removed` |
| F3 | Medium | Upgrade skips existing claims on LOs without attempts | fixed | `ade1d9e89` | `test_f3_activation_reseeds_claimed_los_without_attempts_as_a_rebuild_does[True, False]` (with attempts elsewhere, and an attempt-free vault) |
| F4 | Medium | Newly activated cold gap handling reduces variance | fixed | `ade1d9e89` | `test_f4_a_gap_on_a_cold_lo_moves_the_mean_and_keeps_the_cold_variance`, `test_f4_a_claim_seed_never_starts_below_the_cold_variance_and_replay_agrees`, `test_f4_off_the_predecessor_seed_variance_is_kept`; `test_defect1_on_a_gap_declaration_reanchors_a_materialized_lo` now asserts the variance is kept |
| F5 | Medium | Equal-second timestamps can replay claims before earlier attempts | fixed | `ade1d9e89` | `test_f5_a_gap_and_an_attempt_in_the_same_second_replay_in_written_order[attempt_then_gap, gap_then_attempt]`, `test_f5_a_rung_request_claim_still_precedes_its_same_second_attempt` |
| F6 | Medium | Accepted claim-resolution feedback (LPQ9) is missing | fixed | `0a3288aa4` | `test_f6_the_resolving_review_carries_one_quiet_claim_line_and_no_other_does[passed, missed]`, `test_f6_get_feedback_attaches_the_line_to_the_resolving_review_only`, `test_f6_off_no_claim_line[switch_off, below_tag]`; vitest `ClaimCheckFeedback.test.tsx` |

No finding was rejected.

## What changed

**F1: one transaction, one application per question event**
(`tutor/promotions.py::_write_gap_claim`, `learner/mastery.py::reanchor_mastery_from_claim`).
Under the successor the gap claim's id is `<ULID>_gap_<question event id>`.
The ULID keeps the shared `(created_at, id)` row order that replay uses (F5).
The suffix is the idempotency key. One `BEGIN IMMEDIATE` transaction looks
for that claim and either returns it (an interrupted earlier run already
applied it) or inserts it and re-anchors the LO. A retry after a crash
before `insert_question_promotion` therefore reuses the claim and merges
nothing a second time. Under the successor, `reanchor_mastery_from_claim`
also reads and writes the mastery row inside one transaction (a savepoint
when called inside the gap transaction). A concurrent sidecar attempt's
mastery write now waits for it; the test shows a `timeout=0` writer gets
"database is locked" at the point between the read and the write. No model
work runs inside the transaction: the analysis runs before it and diagnostic
generation after. Off, or below the tag: the predecessor's single insert
with a plain id.

**F2: a journalled activation, completed on the next start or upgrade**
(`claim_fixes_upgrade.py`, `learnloop_sidecar/context.py`). Before the
config is published, inside the activation transaction, a journal
`<database>.claim-fixes-activation` (predecessor and target) is written:
temporary file, fsync, rename, directory fsync. Then the config is
published durably, and the journal is removed after the commit. What each
failure leaves:

- a failure before the rename: rollback, no journal;
- a failure after the rename: rollback, the predecessor's label is
  restored, no journal. If the restore itself fails, the journal stays;
- process death between the publication and the commit: the successor's
  label, the predecessor's database and the journal. This is what the
  review describes, and the test reproduces it by forking a process that
  `os._exit`s right after the rename.

`complete_interrupted_activation` finishes the database side from the
journal. It runs in two places: `SidecarContext.load`, on every desktop
start before state sync, the startup projection or any serve reads the
vault; and `learnloop upgrade --to <tag>`, which no longer answers "already
mvp-0.32" while a journal stands. A journal whose activation did commit
(death between the commit and the removal) is recognised by the committed
`p0_projection_activation` receipt at the target and removed.

**F3: activation covers every LO a rebuild can change.** The activation
now takes all claim-covered LOs. Those with attempts are replayed, as
before. Those without attempts get the cold row a full rebuild writes for
them: `initial_mastery_state_for_learning_object` at the orchestrator's
baseline stamp, now the shared constant
`rebuild_orchestrator.COLD_MASTERY_BASELINE_AT`. The test runs the upgrade
and then a full same-version rebuild, and checks that every mastery row is
unchanged by the rebuild, both with attempts elsewhere and in an
attempt-free vault. The upgrade's notes name the re-seeded LOs.

**F4: a claim never lowers a variance** (`learner/mastery.py`). Under the
successor:
- a claim seed is floored at the configured cold-start variance:
  `max(1/pc, claim_prior_min_variance, cold_start_prior_logit_variance)`;
- a zero-evidence re-anchor of an existing row keeps the row's own variance
  if it is larger.

This is the spec's rule (§3.0b table: "the variance never drops below the
prior's"; AD §5.5). The seed is floored as well as the re-anchor, because
replay resets the row and re-seeds it. A floor on the live re-anchor alone
would make live mastery (3.0) and replayed mastery (2.0) disagree.
`test_f4_a_claim_seed_never_starts_below_the_cold_variance_and_replay_agrees`
pins that live and replay agree. The floor is an existing configured value,
so there is no new constant. This supersedes the stage record's note that
the cold seed stayed at `max(1/pc, 2.0)` (the spec's as-built note is
updated). Off, or below the tag: the predecessor's seed.

**F5: claims and attempts share one order, `(created_at, id)`**
(`substrate/replay.py::_ClaimStream`, `learner/mastery.py::covering_learner_claim`).
Stamps have one-second resolution. Ids minted in one process sort in
creation order (`learnloop.ids`: "Rows are ordered by (created_at, id)"),
and placement already orders its ledger this way. The claim stream now
sorts claims by `(created_at, id)` and places each before an attempt only
if it sorts before the attempt's `(created_at, id)`. The seed reads the
claims made before the first attempt by the same key (`claims_as_of_id`).
Outcomes:
- a gap declared just after an attempt in the same second replays after it,
  as it ran live;
- a rung-variant request (claim, then its own self-report attempt) still
  replays claim first.

No rule is imposed by claim source. Each row's own mint order decides.

**F6: the claim line (LPQ9)** (`placement/claim_check.py`,
`learnloop_sidecar/handlers/feedback.py::get_feedback`,
`apps/learnloop-tauri/src/components/ClaimCheckFeedback.tsx`, `FeedbackScreen`).
Some assumptions are the learner's own "I know this" or "too easy" (source
`self_report`). When placement names a review as the resolving attempt of
such an assumption, `get_feedback` carries
`claimCheck: {claim: "marked_known", check: "passed" | "missed", line}`.
The feedback screen shows the line quietly, beside DL2's "Your check on
your own." line: "You marked this as known; this check: missed." There is
no score, no calibration figure and no trait label.

The line is read after grading from the placement ledger. It is never an
input to grading, mastery or the resolution, and it never repeats: the
tests check that an unrelated LO's review and a later review of the same LO
carry no line. It runs under the same successor and kill switch. A miss
whose diagnosis has not landed has no resolving attempt yet, so its line
appears on the next open of that review once the diagnosis decides it.

## Residuals (not defects of this round)

- **F2 is completed on the desktop start and on upgrade, not by every
  process.** A CLI command other than `upgrade`, or the MCP server, opening
  a vault in the interrupted state serves it until the next desktop start
  or upgrade. Doctor reports the stale rebuild meanwhile, and any full
  rebuild completes the mastery side. This is a narrow window (a crash
  inside the upgrade, then a non-desktop open), so it stays here under the
  proportionate-protection rule (owner, 2026-10-24).
- **F5 orders rows by when they were written, not when they committed.** An
  attempt whose id was minted before a claim, but whose mastery update
  committed after it (a long grading run during a gap promotion), replays
  before the claim. Attempts already replay this way among themselves. A
  commit sequence would need a migration, which is outside this stage.
- `docs/learnloop-architecture-vault/_scripts/desktop_validate.py` fails on
  `apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticBook.ts`
  ("add explicit activation or lifecycle evidence"). That file was last
  changed by main's `b1087be0a`, and no test runs this script. The new
  `ClaimCheckFeedback.tsx` is entry-reachable through `FeedbackScreen`.

## Gate

Run in this worktree after the fixes. The owner's rule applies: there is no
full suite, durability lane or full vitest here; the landing gate on the
merged tree runs those. Every test command ran inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`,
with pytest at `-n 6`, vitest at `--maxWorkers=4`, and one test run at a
time. Scripts outside pytest ran under `env -i` with empty
HOME/CODEX_HOME/LEARNLOOP_CONFIG_DIR. No live or paid calls were made.

| step | result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| reproduction: `tests/test_lp_claim_fixes_review.py` (F1-F5 tests) against the pre-fix sources from `2275a00af` | 10 failed, 6 passed (guards), as expected |
| targeted pytest `-n 6`, 133 files (listed below) | 2882 passed, 24 skipped, 1 failed: `test_plan_first_transport_offer_grants.py::test_p1_after_a_yes_to_one_method_only_its_requests_and_units_use_openrouter` (`KeyError` on a background batch id in the harness's `seen` map, a T1 timing race with no claim code on its path) |
| rerun `tests/test_plan_first_transport_offer_grants.py` alone | 14 passed |
| rerun, after the line-neutral comment/rationale edit in `schema.py` and `parameter_registry.py`: every test file naming `parameter_registry`/`classify_config_path` (36 files), plus `test_config_refactor.py`, `test_cli_help_snapshot.py`, `test_sidecar_serializer_snapshot.py` | 590 passed, 9 skipped |
| durability: `pytest -n 6 --durable-sqlite tests/test_lp_claim_fixes_review.py tests/test_lp_claim_fixes.py` (WAL + `synchronous=FULL`) | 42 passed, 3 skipped (owner-vault lane, no copies) |
| `npm install`, `npm run typecheck` (apps/learnloop-tauri) | ok |
| vitest `--maxWorkers=4`: `ClaimCheckFeedback.test.tsx`, `IntentCheckFeedback.test.tsx`, `FeedbackScreen.test.tsx`, `FeedbackScreen.phase4.test.tsx`, `FeedbackScreen.liveQueue.test.tsx`, `FeedbackScreen.plan.test.tsx`, `copy/denyList.test.tsx`, `copy/denyList.phase4.test.tsx` | 8 files, 139 tests passed |
| `npm run frontend:build` | built |
| `cargo check` | not run: nothing under `src-tauri` changed |
| `db_generate_reference.py` + `db_validate_reference.py` (no schema change; the config reference cites `learnloop_sidecar/context.py` lines that moved) | 351 table notes, `errors: []` |
| `module_validate.py` | wikilinks 14712/14712, source/test links 11795/11795 |
| `desktop_validate.py` | fails on the pre-existing `pdfSelection/testing/syntheticBook.ts` (see Residuals) |

No migration, no new table, no new top-level module, no new model route,
no new number (the F4 floor is the configured cold-start variance; the F1
key and the F5 order use existing ids).

Targeted pytest files (133):

- `tests/test_activity_families.py`
- `tests/test_ad23_fix_r5.py`
- `tests/test_ad23_fix_r6.py`
- `tests/test_ad23_fix_review.py`
- `tests/test_ad23_successor.py`
- `tests/test_ad2_model.py`
- `tests/test_ad2_serving.py`
- `tests/test_adaptive_difficulty_ad1.py`
- `tests/test_ad_guard.py`
- `tests/test_approach_map_replay.py`
- `tests/test_approach_maps.py`
- `tests/test_architecture.py`
- `tests/test_assumed_known.py`
- `tests/test_attempt_completion.py`
- `tests/test_calibration.py`
- `tests/test_canonical_projection_rollout.py`
- `tests/test_causal_attribution_p0.py`
- `tests/test_causal_attribution_p1.py`
- `tests/test_causal_trace_consistency_p2.py`
- `tests/test_characterization_mastery_reliability.py`
- `tests/test_chatgpt_plan_workspace.py`
- `tests/test_cli_help_snapshot.py`
- `tests/test_config_refactor.py`
- `tests/test_coordinated_migrations.py`
- `tests/test_daily_loop_reader_retire.py`
- `tests/test_daily_plan_composition.py`
- `tests/test_daily_plan_replay.py`
- `tests/test_desktop_rpc_contract.py`
- `tests/test_diagnosis_card.py`
- `tests/test_diagnosis_input_provenance.py`
- `tests/test_diagnosis_pipeline.py`
- `tests/test_diagnosis_replay.py`
- `tests/test_diagnostic_probe_single_use.py`
- `tests/test_embedding_store.py`
- `tests/test_evsi_router_composition.py`
- `tests/test_exam_protection_review.py`
- `tests/test_family_memory_projection.py`
- `tests/test_field_priors.py`
- `tests/test_field_workbench_signals.py`
- `tests/test_figures_migration.py`
- `tests/test_forecast_receipts.py`
- `tests/test_grading_cli.py`
- `tests/test_held_grade_composition.py`
- `tests/test_held_grade_evidence.py`
- `tests/test_hint_telemetry.py`
- `tests/test_ingest_jobs.py`
- `tests/test_ingest_queue_store.py`
- `tests/test_ingest_runner.py`
- `tests/test_init.py`
- `tests/test_intent_codex_rereview.py`
- `tests/test_intent_exclusion.py`
- `tests/test_intent_rpc.py`
- `tests/test_intervention_outcomes_replayer.py`
- `tests/test_item_authoring.py`
- `tests/test_item_fingerprints.py`
- `tests/test_lp_claim_fixes.py`
- `tests/test_lp_claim_fixes_review.py`
- `tests/test_mastery.py`
- `tests/test_method_explicit_upgrade.py`
- `tests/test_misconception_resolution.py`
- `tests/test_mobile_allowlist.py`
- `tests/test_mvp010_upgrade.py`
- `tests/test_mvp011_upgrade.py`
- `tests/test_mvp013_upgrade.py`
- `tests/test_mvp014_upgrade.py`
- `tests/test_mvp015_upgrade.py`
- `tests/test_mvp016_upgrade.py`
- `tests/test_mvp017_route_check_replay.py`
- `tests/test_mvp017_upgrade.py`
- `tests/test_mvp018_upgrade.py`
- `tests/test_mvp020_upgrade.py`
- `tests/test_mvp021_upgrade.py`
- `tests/test_mvp022_upgrade.py`
- `tests/test_mvp023_upgrade.py`
- `tests/test_mvp024_upgrade.py`
- `tests/test_pfc_unassessed_readers.py`
- `tests/test_pfc_unverified_unassessed.py`
- `tests/test_placement_diagnosis_decides.py`
- `tests/test_placement_fixture_copies.py`
- `tests/test_placement_opening_probes.py`
- `tests/test_placement_report.py`
- `tests/test_placement_sidecar.py`
- `tests/test_placement_signals.py`
- `tests/test_placement_split_grades.py`
- `tests/test_plan_determinism.py`
- `tests/test_plan_first_transport_offer_grants.py`
- `tests/test_plan_first_transport_offer_grants_r5.py`
- `tests/test_practice_index_dossiers.py`
- `tests/test_practice_index_find.py`
- `tests/test_public_tip_guards.py`
- `tests/test_question_promotions.py`
- `tests/test_quick_check.py`
- `tests/test_reader_workbench_rw2a.py`
- `tests/test_reading_step_switch.py`
- `tests/test_rebuild_orchestrator.py`
- `tests/test_recurrence_commands.py`
- `tests/test_recurrence_live.py`
- `tests/test_regrade_contract_replay.py`
- `tests/test_regrade_contract_successor.py`
- `tests/test_regrade_contract_upgrade.py`
- `tests/test_replay.py`
- `tests/test_required_method_authority.py`
- `tests/test_required_method_grading.py`
- `tests/test_retrieval_spaces_migration.py`
- `tests/test_reveal_ledger.py`
- `tests/test_router_coldness_covariates.py`
- `tests/test_router_outcomes.py`
- `tests/test_router_r1_composition.py`
- `tests/test_router_r2a_serving.py`
- `tests/test_route_rules_in_grader.py`
- `tests/test_serve_eligibility_review.py`
- `tests/test_sidecar_contract.py`
- `tests/test_sidecar_reader_p3_slice2.py`
- `tests/test_sidecar_serializer_snapshot.py`
- `tests/test_sidecar_teach_back.py`
- `tests/test_sidecar_tutor_qa.py`
- `tests/test_source_block_fts.py`
- `tests/test_source_retrieval_tutor.py`
- `tests/test_source_space_resolver.py`
- `tests/test_sqlite_file_copies.py`
- `tests/test_sqlite_wal_lifecycle.py`
- `tests/test_state_sync.py`
- `tests/test_stuck_prompt.py`
- `tests/test_stuck_prompt_replay.py`
- `tests/test_table_roles.py`
- `tests/test_tracked_fixture_databases.py`
- `tests/test_tui_feedback.py`
- `tests/test_tutor_promotion_service.py`
- `tests/test_tutor_promotion_w2.py`
- `tests/test_ux_phase1_connect_ai.py`
- `tests/test_ux_phase4_feedback.py`
- `tests/test_voi_stopping.py`
- `tests/test_workbench_assistance.py`
