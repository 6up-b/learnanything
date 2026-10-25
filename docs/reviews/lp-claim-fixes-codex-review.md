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

## Re-review (Codex job `20261025-134749-TKbnIL`)

The re-review confirmed F1 fixed, reopened F2 and found three new defects
in the fix commits (F7-F9). Each was reproduced before it was fixed. The tests
are in `tests/test_lp_claim_fixes_rereview.py` (committed failing first, in
`5d33349b1`: 20 failed, 1 passed) and `tests/test_learner_claim_application_migration.py`.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Gap application is neither atomic nor retry-safe | confirmed fixed (no change) | `ade1d9e89` | the round-one tests still pass |
| F2 | High | Incomplete activation is still served outside the desktop's happy path | fixed | `4422791dd` (+ the record commit's docstring) | `test_f2_every_opener_that_may_write_completes_the_activation_first[open_vault_repository, vault_repository, sidecar_start, cli_command]`, `test_f2_a_real_death_is_completed_by_the_next_cli_command` (forked `os._exit` after the rename), `test_f2_an_activation_that_cannot_complete_stops_the_opener[...4]`, `test_f2_an_opener_in_a_process_that_cannot_complete_refuses[...2]`, `test_f2_the_cli_and_the_sidecar_install_the_completion[...3]`, `test_f2_attaches_that_never_write_refuse_while_the_journal_stands`, `test_f2_an_mcp_server_already_attached_stops_serving_when_a_journal_appears`, `test_f2_the_phone_host_refuses_to_start_while_the_journal_stands`; the round-one `desktop_start` case now goes through `SidecarContext.load` |
| F7 | Medium | Reserved attempt ids can reverse the live claim/attempt order | fixed | `4422791dd` | `test_f7_an_attempt_reserved_before_a_gap_and_graded_after_it_replays_after_it`, `test_f7_the_claim_records_how_many_of_its_los_attempts_it_was_applied_after`, `test_f7_every_reanchoring_writer_records_its_point[too_easy_report, rung_variant_request]`, `test_f7_off_the_claim_records_nothing`; migration tests in `test_learner_claim_application_migration.py` |
| F8 | Medium | Preserved cold variance is lost during rebuild | fixed | `4422791dd` | `test_f8_two_claims_with_differing_pseudo_counts_keep_the_weak_claims_variance_in_a_rebuild`, `test_f8_the_first_replayed_attempt_starts_from_the_retained_variance`, `test_f8_activation_reseeds_with_the_retained_variance_as_a_rebuild_does` |
| F9 | Medium | Timeout-resolved reviews omit claim feedback | fixed | `149efccd1` | `test_f9_a_miss_the_diagnosis_timeout_decides_carries_its_line_reopened_after_the_deadline` |

No finding was rejected.

### Reproduction

- **F2.** With the interrupted state built directly (the successor's label,
  the predecessor's database, the journal), `open_vault_repository`,
  `vault_repository` and a CLI command (`backfill-originals`) all served the
  predecessor's mastery under the successor's label. `RemoteRuntime.attach`,
  a read-only `Repository.attach` and the phone host's `attach` all attached.
  A failing completion in `SidecarContext.load` was logged, and the load went on.
- **F7.** The production gap writer and the self-grade path were used. The
  attempt's id was minted before the gap, and its grade was committed in the
  gap's second. Live mastery was `(-1.0230, 2.1541)`; the rebuild gave
  `(-0.9278, 1.8859)`.
- **F8.** A `learner_report` claim at pseudo-count 0.25 (variance 4.0) was
  followed by a `rung_variant_request` at 2.0. Live kept 4.0. The rebuild
  seeded 3.0, both attempt-free and before the first replayed attempt. The
  activation re-seeded 3.0 as well.
- **F9.** A missed review of an "I know this" LO had its diagnose job queued
  past `DIAGNOSIS_WAIT_DAYS`. Placement now reads the assumption as `failed`
  with that review as the resolving attempt. `claim_check` still returned `None`.

### What changed

**F2: every opener completes the activation, or nothing is served**
(`learnloop/activation_journal.py`, new leaf module;
`vault/repository.py`, `db/repositories.py`, `claim_fixes_upgrade.py`,
`cli/runtime.py`, `learnloop_sidecar/context.py`, `remote/runtime.py`,
`learnloop_mobile/host.py`).

- The journal's path is derived from the database's path alone, so the
  database layer can check it.
- `open_vault_repository` (every CLI command, the sidecar and the TUI) and
  `vault_repository` (the services below them) complete the activation before
  they attach, under the vault mutation lock. If the completion fails, they
  raise `InterruptedActivation`, which names `learnloop upgrade --to <tag>`.
  The journal stays for the next try.
- The completion belongs to the upgrade module, which sits above the vault
  layer. Calling it directly broke two import contracts (`tui` reached
  `daily_plan_upgrade`, and the frozen cycles changed). So the entry points
  that may complete it, the CLI (`cli/runtime.py`) and the desktop sidecar,
  install it at import (`install_completer`). An opener in a process that
  installed nothing (the TUI, a script) raises instead.
- Every other attach refuses while the journal stands. `Repository.__init__`
  and `Repository.attach` call `refuse_if_interrupted`, which covers a
  read-only CLI report. The MCP runtime refuses on attach and on every
  request (`RemoteRuntime.vault()`), and the phone host refuses at start. The
  MCP runtime and the phone host raise their own `SchemaMismatch` (exit 78),
  so a supervisor does not restart in a loop.
- The completion's own opens run inside `completing_activation()` (a
  `ContextVar`), so they are neither refused nor recursive.
- The sidecar's catch-and-continue hook is gone. `SidecarContext.load` binds
  the new vault only after its opener has returned.

**F7: the claim's place is recorded where it was applied** (migration
`221_learner_claim_application_point.sql`, `learner_claims.applied_after_attempts`;
`learner/mastery.py::reanchor_mastery_from_claim`,
`Repository.record_learner_claim_application`, `substrate/replay.py::_ClaimStream`).

- Under the successor, the live re-anchor records how many of the LO's
  attempts were already applied. It does this inside the claim's own
  `BEGIN IMMEDIATE` transaction, for the claim the writer passes as
  `claim_id`. Every re-anchoring writer passes it: the gap promotion, the
  rung-variant request and the too-easy/too-hard report.
- Replay applies the claim after that many attempts. Claims at the same point
  keep their `(created_at, id)` order. A claim without the record (written
  below the successor, by a non-re-anchoring source, or before 221) is placed
  by the round-one `(created_at, id)` rule.
- No order is inferred from an attempt id that was reserved before grading.
- The claim-reading functions now take an explicit set of the claims made by
  a point (`claims_made`) instead of a stamp and id.
- No new number: the record is a count.

**F8: the cold seed keeps the variance earlier re-anchors left**
(`learner/mastery.py::initial_mastery_state_for_learning_object`).

- Under the successor, the seed takes the covering claim's mean with the
  largest variance that any re-anchoring claim's own seed had at its point,
  in the order the claims were made. This is the `max(current, seed)` that
  live keeps.
- The attempt-free rebuild, the seed before the first replayed attempt and
  the activation's re-seed all read this function. It is a structural `max`
  over seeds already computed, so there is no new number.

**F9: the claim line reads placement as it stands now**
(`placement/claim_check.py`). Placement is evaluated at the wall clock (an
optional `now_iso` exists for callers), and the review is matched by
`resolving_attempt_id`.

### The schema change (F7)

- Migration 221 adds one nullable column with a `>= 0` check. It is numbered
  after main's 220. RW7b may take the same number, and the landing renumbers.
- `fixtures/migration_head_220` was renamed to `migration_head_221`. Its
  database is a backup-API copy of the sanitized head with only 221 applied
  under `UPGRADE_SCRATCH_COPY`:
  - `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE`, header bytes 1/1;
  - `integrity_check` ok, `foreign_key_check` empty, no companion files;
  - the size is unchanged (6,696,960 bytes), and the README records the rebuild.
- The head path is named in 37 test files, `scripts/sanitize_migration_head_fixture.py`
  and both `db_*_reference.py` scripts, with `SCHEMA_HEAD = 221`.
- The earlier migrations' "nothing else changed" diffs subtract
  `CLAIM_POINT_ALTERED_TABLES = {learner_claims}`, and their head asserts read 221.
- The AD column classes list `applied_after_attempts` as metadata.
- `table_roles` is unchanged: no new table.
- `learnloop.activation_journal` is in the experiments-stay-outside-production
  contract.

### Residuals

- A long-lived sidecar that loaded the vault before another process's
  upgrade died keeps serving its own loaded state until it reloads. That state
  is the predecessor's label and the predecessor's database, so it is
  consistent. The reload then completes the activation or fails.
- Two attempts on one LO do not rebuild to their live mastery row in this test
  harness (`create_placement_vault` + self-grades), even with no claims at all.
  This is unrelated to the claim stream, and main has it too. So
  `test_f7_the_claim_records...` compares the raced rebuild with the rebuild
  of the same history where the second attempt's id was minted after the gap,
  not with the live row.
- The F5 residual about attempts among themselves still holds: they replay in
  `(created_at, id)` order, not in commit order.

### Gate (re-review)

Run in this worktree after the fixes. The owner's rule applies: there is no
full suite, durability lane or full vitest here; the landing gate on the
merged tree runs those. Every test command ran inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`,
with pytest at `-n 6` and one test run at a time. Scripts outside pytest
(the head-fixture rebuild and the reference scripts) ran under `env -i`
with empty HOME/CODEX_HOME/LEARNLOOP_CONFIG_DIR. No live or paid calls were made.

| step | result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken (the first draft of F2, a direct call from `vault.repository` into the upgrade, broke 2; the installed completion replaced it) |
| reproduction: `tests/test_lp_claim_fixes_rereview.py` at `5d33349b1` (before the fixes) | 20 failed, 1 passed (the passing one, `test_f2_every_opener..._first[sidecar_start]`, is the happy path round one already covered; its failure case `...cannot_complete_stops_the_opener[sidecar_start]` failed) |
| reproduction of F7 under the round-one rule (the recorded point ignored) | `test_f7_*` replay cases: 2 failed |
| targeted pytest `-n 6`, 111 files (listed below) | **10515 passed, 66 skipped, 2 xfailed, 0 failed** (48m42s) |
| durability: `pytest -n 6 --durable-sqlite tests/test_learner_claim_application_migration.py tests/test_lp_claim_fixes_rereview.py tests/test_lp_claim_fixes_review.py tests/test_lp_claim_fixes.py` (WAL + `synchronous=FULL`) | 71 passed, 3 skipped (owner-vault lane, no copies) |
| frontend (npm, vitest, build) | not run: nothing under `apps/` changed |
| `cargo check` | not run: nothing under `src-tauri` changed |
| `db_generate_reference.py` + `db_validate_reference.py` (schema head 221) | 351 table notes, `errors: []`, 4,751 wikilinks checked |
| `module_validate.py` | wikilinks 14712/14712, source/test links 11795/11795 |

Migration 221 (one column); head fixture `migration_head_221`; one new
top-level module (`learnloop.activation_journal`, in the E0 contract); no new
table, model route, config key or number (the F7 record is a count, the F8
seed a `max` over seeds already computed).

Targeted pytest files (111):

- `tests/test_ad1_codex_rereview_fixes.py`
- `tests/test_ad1_codex_review_fixes.py`
- `tests/test_ad1_outside_and_cli.py`
- `tests/test_ad23_contract.py`
- `tests/test_ad23_fix_r5.py`
- `tests/test_ad23_fix_r8.py`
- `tests/test_ad23_fix_review.py`
- `tests/test_ad23_intent_compose.py`
- `tests/test_ad23_inversion.py`
- `tests/test_ad23_owner_decisions.py`
- `tests/test_ad23_pool_membership.py`
- `tests/test_ad2_model.py`
- `tests/test_ad2_serving.py`
- `tests/test_ad3_monitoring.py`
- `tests/test_ad3_reading.py`
- `tests/test_ad3_subject_view.py`
- `tests/test_adaptive_difficulty_ad1.py`
- `tests/test_ad_epoch.py`
- `tests/test_ad_guard.py`
- `tests/test_architecture.py`
- `tests/test_block_chooser_interface.py`
- `tests/test_cli_help_snapshot.py`
- `tests/test_config_refactor.py`
- `tests/test_daily_loop_golden_path_lifecycle.py`
- `tests/test_daily_loop_lo_lifecycle_serving.py`
- `tests/test_daily_loop_reader_authored_practice.py`
- `tests/test_daily_loop_reader_retire.py`
- `tests/test_daily_loop_reentry_break.py`
- `tests/test_daily_loop_reentry_cap.py`
- `tests/test_daily_loop_reference_adoption.py`
- `tests/test_daily_loop_start_minutes.py`
- `tests/test_daily_loop_start_postpone.py`
- `tests/test_daily_plan_admission.py`
- `tests/test_daily_plan_build.py`
- `tests/test_daily_plan_composition.py`
- `tests/test_daily_plan_kill_switch.py`
- `tests/test_daily_plan_owner_decisions.py`
- `tests/test_daily_plan_reading.py`
- `tests/test_daily_plan_reentry.py`
- `tests/test_daily_plan_replay.py`
- `tests/test_daily_plan_review_regressions.py`
- `tests/test_daily_plan_rpc.py`
- `tests/test_daily_plan_split.py`
- `tests/test_desktop_rpc_contract.py`
- `tests/test_dl2_rw4b_keyed_pick_check.py`
- `tests/test_evsi_staged_binding.py`
- `tests/test_exam_protection_landing.py`
- `tests/test_integration_daily_loop_field.py`
- `tests/test_intent_codex_rereview.py`
- `tests/test_intent_codex_review.py`
- `tests/test_intent_exclusion.py`
- `tests/test_intent_fix_round4.py`
- `tests/test_intent_fix_round5.py`
- `tests/test_intent_fix_round6.py`
- `tests/test_intent_fix_round7.py`
- `tests/test_intent_goal_deadline.py`
- `tests/test_intent_plan.py`
- `tests/test_learner_pick_proposal.py`
- `tests/test_mcp_c1a_landing.py`
- `tests/test_mcp_c1a_narrow.py`
- `tests/test_mcp_tools.py`
- `tests/test_method_explicit_landing.py`
- `tests/test_method_explicit_upgrade.py`
- `tests/test_mobile_allowlist.py`
- `tests/test_mvp011_upgrade.py`
- `tests/test_mvp014_upgrade.py`
- `tests/test_mvp015_upgrade.py`
- `tests/test_mvp016_upgrade.py`
- `tests/test_mvp017_upgrade.py`
- `tests/test_mvp018_upgrade.py`
- `tests/test_mvp020_upgrade.py`
- `tests/test_mvp021_upgrade.py`
- `tests/test_mvp023_upgrade.py`
- `tests/test_mvp024_upgrade.py`
- `tests/test_plan_determinism_landing.py`
- `tests/test_plan_determinism.py`
- `tests/test_plan_follows_path.py`
- `tests/test_reader_report.py`
- `tests/test_reader_rw4b_admission_idempotency.py`
- `tests/test_reader_rw4b_fix6.py`
- `tests/test_reader_rw7a_migration.py`
- `tests/test_reading_paths.py`
- `tests/test_reading_step_switch.py`
- `tests/test_reference_gate_imports.py`
- `tests/test_router_card.py`
- `tests/test_router_g1_feasibility.py`
- `tests/test_router_g4_restraint.py`
- `tests/test_router_g7_fallback.py`
- `tests/test_router_presentations.py`
- `tests/test_router_r1_composition.py`
- `tests/test_router_r2a_landing.py`
- `tests/test_router_r2a_serving.py`
- `tests/test_router_r2b_agreement.py`
- `tests/test_router_r2bc_landing.py`
- `tests/test_router_r2b_serving.py`
- `tests/test_router_r2c_retrieval.py`
- `tests/test_router_r2c_teach_back.py`
- `tests/test_router_why_copy.py`
- `tests/test_rw7b_codex_review_fixes.py`
- `tests/test_rw7b_fix_round2.py`
- `tests/test_serve_eligibility.py`
- `tests/test_serve_eligibility_review.py`
- `tests/test_sidecar_serializer_snapshot.py`
- `tests/test_table_roles.py`
- `tests/test_today_headline.py`
- `tests/test_tracked_fixture_databases.py`
- `tests/test_ux_phase4_feedback.py`
- `tests/test_ux_phase4_landing.py`
- `tests/test_voi_merge_composition.py`
- `tests/test_voi_stopping.py`
- `tests/test_voi_v2.py`
