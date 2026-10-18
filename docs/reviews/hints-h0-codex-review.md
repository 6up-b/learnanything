# Adaptive hints H0: Codex review and fixes (stage `hints-h0`)

Branch `hints/h0` (worktree `learnanything-merge4`), reviewed at `824d0a023`
(codex job `/home/saturn/.cache/codex-agent/jobs/20261017-232444-EVRJuR`).
Stage record: `docs/reviews/adaptive-hints-H0.md` (its §1, §4, §8, §9 now
read as fixed below). Six findings: five Medium, one Low, no High. All six
fixed; none rejected.

## Review

### Reproduction (before any fix)

F1-F4 were reproduced on `824d0a023` with a scratch test (deleted after; its
assertions pinned the defective behaviour, and all four passed): A's reveal,
whose attach failed, stayed unattached after `recover_practice_submission`
and was then attached to B's attempt; with a fake grader that moved the clock
30 s, the report gave 40 s reveal-to-submit (should be 10) and 20 s into the
attempt (should be 50); `UPDATE help_assists SET practice_session_id = 's1'`
on a workbench row with a NULL session raised "identity columns and an
attached attempt are fixed"; an ungraded next independent attempt was
counted as `fail`. F5 and F6 are missing report output: the report listed
`unaided_next_progress` as unmeasured, and no share or summary carried an
interval.

### Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | Medium | Failed attachment contaminates a later attempt's telemetry | fixed | `50aa2ec9a` | `tests/test_hint_telemetry.py::test_a_failed_attach_is_repaired_by_recovery_and_never_given_to_the_next_attempt`, `::test_a_retried_submit_repairs_a_failed_attach`, `::test_an_attempt_without_its_receipt_is_attached_when_its_completion_resumes`; `tests/test_help_assists_schema.py::test_the_store_attach_matches_the_submission_key_only`; vitest `PracticeScreen.hintTelemetry.test.tsx` "sends the submission key the attempt then submits with" |
| F2 | Medium | Reported solution time includes model grading latency | fixed | `50aa2ec9a` | `::test_reveal_to_submit_ends_at_the_submit_not_at_the_graded_attempt` (delayed fake grader: 10 s and 50 s), `::test_a_grading_fallback_keeps_the_first_submit_time`, `::test_a_row_without_a_submit_time_is_timed_unknown_not_from_the_grade` |
| F3 | Medium | Schema prevents the workbench's deferred session binding | fixed | `50aa2ec9a` | `tests/test_help_assists_schema.py::test_the_workbench_lifecycle_binds_each_deferred_column_once`, `::test_the_ledger_keeps_rows_and_an_attached_attempt` |
| F4 | Medium | An ungraded later attempt is reported as failure | fixed | `50aa2ec9a` | `::test_an_ungraded_next_attempt_is_reported_ungraded_never_fail` (and a later pass is not taken instead), `::test_an_ungraded_hinted_attempt_and_no_later_attempt` |
| F5 | Medium | H0 omits progress outcomes that its existing data can establish | fixed | `50aa2ec9a` | `::test_unaided_next_progress_is_settled_by_the_grade_where_it_can_be` |
| F6 | Low | Descriptive estimates omit required uncertainty intervals | fixed | `50aa2ec9a` | `::test_shares_and_summaries_carry_intervals_with_explicit_small_sample_behaviour` |

### What changed

- **F1.** `help_assists.submission_id` (new column; migration 210 is
  unlanded, so it was edited in place). `practice.record_hint_reveal` now
  requires `submissionId`, the screen's stable key for the attempt in
  progress (`submissionId.current`, the same key the submit sends and the
  draft checkpoint keeps across a restart). The attach
  (`store.attach_submission`) matches on the key and item alone, never on the
  session and item, so a row whose attach failed can never be swept into a
  later submission. The attach is idempotent and is repeated by every path
  that answers for a committed submission: a retried submit answered from its
  receipt, a resumed completion (attempt committed, receipt missing), and
  `recover_practice_submission`. The report also resolves an unattached row to
  the attempt committed under its key (`practice_attempts.submission_id`;
  `totals.resolved_by_submission` counts them), so a failed attach loses
  nothing even before it is repaired.
- **F2.** `help_assists.submitted_at` (new column): the sidecar's clock when
  the submit request reached it, before grading, stamped on the submission's
  unattached rows at once (`store.stamp_submitted`, first stamp kept, so a
  grading fallback answered by a self-grade keeps the learner's first submit)
  and filled by the attach where the stamp failed. The report times
  reveal-to-submit and seconds-into-the-attempt from it and never from
  `practice_attempts.created_at`; a row without it is counted in
  `timing_unknown`. Limitation, recorded: a submit that fails validation
  inside the grader and is resent much later under the same key keeps the
  first stamp.
- **F3.** The identity trigger keeps `id`, `surface`, `assist_kind` and
  `requested_at` fixed and lets each binding (`practice_session_id`,
  `workbench_session_id`, `submission_id`, `submitted_at`, `attempt_id`) go
  from NULL to a value once; replacing or clearing a binding is refused. The
  new test walks a workbench row through its lifecycle (written with no
  practice session, the item bound, Submit filling the practice session,
  submission and submit time, then the attempt) and checks every rebinding is
  refused.
- **F4.** Later independent success takes the next independent attempt
  (`hints_used = 0`, not primed) and keeps it: `pass` when fully correct,
  `fail` when graded and not, `ungraded` when it has no grade (no later
  attempt is searched for instead), `pending` when none exists. Each block
  carries `pass_rate` over the resolved pass/fail cases.
- **F5.** `unaided_next_progress` per kind: `reached` (a share of the
  resolved rows) when the attempt is fully correct, not primed, no further
  help followed the hint, and the attempt counts no more help than its
  recorded reveals; otherwise `unknown` by reason (`more_help_followed`,
  `primed`, `help_not_ordered`, `ungraded`, `not_fully_correct`), never a
  failure. `not_yet_measured` now names only
  `unaided_next_progress_unknown_cases` (H2's hint and outcome placements).
  Spec §6.1's grade clause ("a correct answer reaches the goal") is exactly
  the case settled.
- **F6.** Every share (`_share`) carries a 95% Wilson score interval (`None`
  when its denominator is 0). Every p50/p95 (`_percentiles`: per item, per
  session, per attempt, both timings) carries a distribution-free 95%
  interval from the order statistics (binomial coverage of [X(j), X(k)]);
  when no pair reaches 95% (the median needs n >= 6, p95 n >= 59) it is
  `None` with `reason: "too_few"` and the coverage reached, and `"empty"` at
  n = 0. Documented in `learnloop/hints/report.py`'s module docstring.
  `attempt_correct` adds the correct share among graded attempts.

### Claims corrected in the stage record

`docs/reviews/adaptive-hints-H0.md` §1.1 (60 columns, five indexes, the
once-set bindings), §1.2 (the store's functions), §1.3 (the reveal's
`submissionId`, the stamp and the repeated attach), §1.6 (reveal to submit
ends at `submitted_at`; outcomes never imputed; unaided progress where the
grade settles it; intervals), §4 (the attach and the submit time), §8 Q3
(unattached rows), §9 friction 2 and 5 (H2's fold and RW2b key on
`submission_id`; RW2b fills the session once); spec §15's H0 note (the two
submission columns and the once-set bindings).

### Head fixture and references

- `fixtures/migration_head_210/state.sqlite` rebuilt: the base's
  `migration_head_209` database (git `610e61dc0`) copied with the backup API,
  only the edited 210 applied under `upgrade_allowance(UPGRADE_TEST_HELPER)`,
  `wal_checkpoint(TRUNCATE)` -> `(0, 0, 0)`, `journal_mode=DELETE` (header
  bytes 18-19 = 1/1), `integrity_check` ok, `foreign_key_check` empty, copied
  into place with the backup API, no companion files. Against the previous
  fixture only `help_assists`, its identity trigger and the new
  `idx_help_assists_submission` differ, plus 210's `applied_at` in
  `schema_migrations`. README updated.
- References regenerated on `50aa2ec9a` in `0e6c57264` (commit labels; the
  two new columns and the index in `Tables/help_assists.md`);
  `db_validate_reference.py` 0 errors; `validate_vault.py` passed (1124
  notes).

### Gate (this step; the full suite, the whole durability lane and the whole vitest run are the landing gate's)

Run in the worktree with `TMPDIR=fixtures-local/tmp`.

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **25 kept, 0 broken**.
- Targeted pytest, `uv run pytest -n auto <72 files>`: **1579 passed**
  (294.4 s). The files: the stage's 72-file list (every new or changed test
  file, every file that drives `submit_attempt` / `submit_dont_know` /
  `recover_practice_submission` / the practice handler through the sidecar,
  every file naming the head fixture, the config-defaults-snapshot files, and
  the contract tests); a `git grep` for `submit_attempt`, `submit_dont_know`,
  `recover_practice_submission`, `handlers.practice`, `migration_head_210`
  and `help_assists` added no file outside it:
  `tests/test_architecture.py` `tests/test_causal_p2_acceptance.py` `tests/test_causal_repair_sidecar_rpcs.py` `tests/test_cli_help_snapshot.py` `tests/test_config_refactor.py` `tests/test_coordinated_migrations.py` `tests/test_daily_plan_composition.py` `tests/test_daily_plan_replay.py` `tests/test_daily_plan_review_regressions.py` `tests/test_daily_plan_rpc.py` `tests/test_desktop_rpc_contract.py` `tests/test_diagnosis_async_router.py` `tests/test_diagnosis_card.py` `tests/test_diagnosis_input_provenance.py` `tests/test_diagnosis_replay.py` `tests/test_exam_protection_review.py` `tests/test_facet_identity_actions.py` `tests/test_field_signal_production_paths.py` `tests/test_forecast_receipts_landing.py` `tests/test_forecast_receipts.py` `tests/test_help_assists_schema.py` `tests/test_hint_telemetry.py` `tests/test_import_split_parity.py` `tests/test_instructional_layering.py` `tests/test_learner_text_source_widening.py` `tests/test_library_asks_migration.py` `tests/test_method_explicit_upgrade.py` `tests/test_migrations.py` `tests/test_mobile_allowlist.py` `tests/test_mvp010_upgrade.py` `tests/test_mvp011_upgrade.py` `tests/test_mvp013_upgrade.py` `tests/test_mvp014_upgrade.py` `tests/test_mvp015_upgrade.py` `tests/test_mvp016_upgrade.py` `tests/test_mvp017_route_check_replay.py` `tests/test_mvp017_upgrade.py` `tests/test_mvp018_upgrade.py` `tests/test_mvp020_upgrade.py` `tests/test_mvp021_upgrade.py` `tests/test_mvp022_upgrade.py` `tests/test_mvp023_upgrade.py` `tests/test_mvp024_upgrade.py` `tests/test_pfc_unverified_unassessed.py` `tests/test_placement_opening_probes.py` `tests/test_plan_determinism.py` `tests/test_reader_rw3a_landing.py` `tests/test_reader_workbench_rw2a.py` `tests/test_reading_step_switch.py` `tests/test_rebuild_orchestrator.py` `tests/test_recurrence_commands.py` `tests/test_recurrence_live.py` `tests/test_regrade_contract_successor.py` `tests/test_regrade_contract_upgrade.py` `tests/test_router_r1_composition.py` `tests/test_router_r2a_serving.py` `tests/test_router_r2bc_landing.py` `tests/test_route_rules_in_grader.py` `tests/test_serve_eligibility_review.py` `tests/test_shadow_rebuild.py` `tests/test_sidecar_contract.py` `tests/test_sidecar_item_authoring.py` `tests/test_sidecar_serializer_snapshot.py` `tests/test_sidecar_trace_and_clarification.py` `tests/test_sidecar_tutor_qa.py` `tests/test_source_block_fts.py` `tests/test_sqlite_file_copies.py` `tests/test_stuck_prompt.py` `tests/test_stuck_prompt_replay.py` `tests/test_table_roles.py` `tests/test_tracked_fixture_databases.py` `tests/test_ux_phase4_feedback.py`
- Durability: `uv run pytest -m durability tests/test_help_assists_schema.py tests/test_library_asks_migration.py tests/test_learner_text_source_widening.py tests/test_migrations.py tests/test_tracked_fixture_databases.py tests/test_daily_plan_replay.py`: **5 passed** (62 deselected); `uv run pytest -n auto --durable-sqlite tests/test_help_assists_schema.py tests/test_hint_telemetry.py`: **45 passed**.
- Frontend (`apps/learnloop-tauri`): `npm install` ok; `npm run typecheck` ok (exit 0); `npx vitest run src/screens/PracticeScreen.hintTelemetry.test.tsx src/screens/PracticeScreen.test.tsx src/screens/PracticeScreen.phase4.test.tsx src/screens/PracticeScreen.workbench.test.tsx src/api`: **69 passed** (6 files); `npm run frontend:build`: ok.
- `cargo check`: not run (nothing under `src-tauri` changed in this step).
- References: `db_generate_reference.py` and `db_validate_reference.py` **0 errors**; `validate_vault.py` passed.
- Snapshots: config defaults, CLI help, serializer and RPC pins unchanged (no config key, CLI option or RPC name changed; `record_hint_reveal` gained a required input field, covered by `test_hint_telemetry.py`), and their tests are in the targeted run.

**Model calls made in this step: 0** (fakes only; no vault copy was opened and
no sidecar smoke run was made).

### Commits

- `50aa2ec9a` the fixes (migration 210 and the rebuilt head fixture, the
  store, `learnloop.hints.telemetry` and `.report`, the sidecar, the screen's
  `submissionId`, tests, the stage record and spec §15).
- `0e6c57264` the references regenerated on `50aa2ec9a`.
- this record.
