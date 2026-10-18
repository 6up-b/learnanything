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

## Fix round 2 (orchestrator, after Codex job 20261018-000003-fesMOi)

The orchestrator's Codex verify (job `20261018-000003-fesMOi`, on
`b4d87cbed`) found that F1, F3 and F4 hold and reopened the stage on three
Medium problems, V1-V3. All three are fixed in `04d06282f`; references are
regenerated in `a107e9a13`. Migration 210 has not landed, so it was edited
in place.

**Fail first.** The round's tests were copied into a detached worktree at
`b4d87cbed` (removed after) and run against its code. **11 failed**: V1 x4
(`OverflowError: int too large to convert to float` at n = 1030 and 20000,
in `_percentiles` and in a full report); V2 x5 (`reached` counted where it
should not be: 2 vs 1, 4 vs 2, and 1 vs 0 in the capped-tutor, at-cap and
workbench cases); V3 x2 (`(1, 110.0) == (1, 50.0)`, and an into-attempt time
taken from the attempt's latency where the submission sent none). On the old
code the small-n cases (n = 1, 2, 5) and the missing-`submissionId` pin
already passed. That is expected: the first must match, and the second pins
behaviour that already held.

| ID | Severity | Title | Verdict | Commit | Tests |
|---|---|---|---|---|---|
| V1 | Medium | Order-statistic interval overflows from n = 1030 | fixed | `04d06282f` | `tests/test_hint_telemetry.py::test_order_statistic_intervals_hold_at_any_sample_size[1,2,5,1030,20000]`, `::test_the_report_summarises_any_number_of_rows[1,2,5,1030,20000]`, `::test_the_stable_terms_reproduce_every_exact_interval_below_the_overflow` |
| V2 | Medium | "Reached" despite help hidden by the hint cap | fixed | `04d06282f` | `::test_capped_tutor_help_never_reads_as_unaided_progress` (Codex's case), `::test_unaided_progress_is_reached_only_when_the_uncapped_records_show_no_other_help`, `::test_a_count_at_the_cap_with_nothing_else_recorded_is_still_unknown`, `::test_a_workbench_problem_holding_a_hint_is_other_help`; `::test_unaided_next_progress_is_settled_by_the_grade_where_it_can_be` and `::test_an_ungraded_hinted_attempt_and_no_later_attempt` updated (their items now have two hints, and the report gets the caps) |
| V3 | Medium | Time into the attempt mixes a retry's latency with the first submit's time | fixed | `04d06282f` | `::test_seconds_into_the_attempt_after_a_grading_fallback_is_the_first_submits` (the exact scenario), `::test_seconds_into_the_attempt_is_unknown_without_the_submits_latency`; `tests/test_help_assists_schema.py` (column set, CHECK, trigger, store stamp/attach) |

### What changed

- **V1.** `learnloop/hints/report.py` gains `_binomial_pmf`. It computes each
  term as `exp(lgamma(n+1) - (lgamma(i+1) + lgamma(n-i+1)) + (i log q + (n-i)
  log(1-q)))`. The two log-factorials are added before they are subtracted,
  and the two powers are added to each other first. So at q = 0.5, P(i) and
  P(n-i) are the same float, and the interval's tie-break (`above >= below`)
  behaves exactly as it did with exact coefficients. The test compares the
  result, dict for dict, with the `b4d87cbed` computation (copied into the
  test as the reference) for n = 1, 2, 5 and for every 7th n below 1030, at
  both quantiles. A scratch run checked every n from 0 to 1029: 0
  mismatches. At n = 1030 and 20000 the interval brackets the estimate with
  coverage in [0.95, 0.96) and a width within the binomial's spread. n =
  20000 takes about 10 ms.
- **V2.** `unaided` returns `reached` only when completeness is established
  from records no cap applies to. `_other_assistance(connection, attempt)`
  reads three things over the attempt's window. The window runs from the
  item's previous attempt to this one, the same window as
  `tutor_qa.hint_equivalents_for_attempt`. The three reads:
  - a `question_events` row on the item that was answered or counted as a
    hint;
  - a `reveal_events` row with `amount > 0`, including a post-attempt display
    linked to the previous attempt, and excluding only this submission's own
    plain self-grade disclosure, matched by the disclosure identity's
    submission key (a trace changed after it already makes the attempt
    primed);
  - a `workbench_sessions` problem on the item that was open at the attempt
    and holding the book or carried hints (`reader.workbench.session_hints`'
    terms).

  Any of these gives `help_not_ordered`. Then the cap: `build_hints_report`
  takes `item_caps` (new `item_caps(practice_items)`: each item's
  `practice_item_hash` and `max_useful_hints`), and the CLI passes the
  vault's. A count at or above a cap greater than 0 gives
  `help_count_capped`, because the client's count may have been larger. A cap
  that cannot be known gives `help_cap_unknown`: either no caps were given, or
  the item's hash differs from the row's `practice_item_hash`, so the item
  changed since the hint. `UNAIDED_UNKNOWN_REASONS` is now `more_help_followed,
  primed, help_not_ordered, help_count_capped, help_cap_unknown, ungraded,
  not_fully_correct`. `learnloop.attempts` is closed to `learnloop.hints`
  (G-H13), so the disclosure basis prefix (`self_grade_disclosure:`) is named
  in the report with its source cited. The grading count is unchanged, as is
  everything submit stores in the attempt: Codex's test asserts
  `hints_used == 1` (1 + 1 capped at 1) and correctness 1.0.
- **V3.** `help_assists.submit_latency_seconds REAL` (nullable). It has a
  CHECK of `>= 0` and is allowed only when `submitted_at` is set. The
  identity trigger refuses any change to it once `submitted_at` is set, so it
  is written in the same update as the submit time or never.
  `store.stamp_submitted` writes both together, first stamp kept.
  `store.attach_submission` fills the latency only where it also fills the
  submit time; a recovery attach knows no submit time and writes neither. A
  negative client latency is not believed (NULL), so the stamp still keeps
  the time. `telemetry.stamp_submission` / `attach_reveals_to_attempt` and
  the sidecar's `_stamp_hint_submission` / `_attach_hint_reveals` pass the
  request's `latency_seconds` (submit, "I don't know", the empty stuck
  answer). The report times "seconds into the attempt" as
  `submit_latency_seconds - (submitted_at - shown_at)` and never from
  `practice_attempts.latency_seconds`. Each kind gains
  `seconds_into_attempt_unknown: {no_submit_time, no_submit_latency}`.
  `timing_unknown` (reveal to submit) is unchanged. In the exact scenario
  (open 09:00:00, reveal 09:00:50, first submit 09:01:00 with latency 60,
  fallback, retry 09:02:00 with latency 120), the report gives 10 s reveal to
  submit and 50 s into the attempt. The attempt keeps `latency_seconds = 120`
  and the row keeps `09:01:00.000Z` and 60.
- **Older clients without `submissionId`.** Pinned by
  `test_an_older_client_without_a_submission_key_is_refused_and_nothing_else_changes`:
  a `practice.record_hint_reveal` call with no `submissionId` is refused
  (validation error), writes no row, and the following submit records the
  client's count unchanged (`hinted_attempt`, `hints_used = 1`). The reveal
  itself is client-side and fire-and-forget. The vitest
  `PracticeScreen.hintTelemetry.test.tsx` "ignores a failed call, a no-op
  answer and a sidecar without the RPC" and "never reports a telemetry
  failure to the learner" pin that a rejected call changes nothing on
  screen. This is acceptable, as the orchestrator ruled.

### Head fixture and references

- `fixtures/migration_head_210/state.sqlite` was rebuilt again the same way:
  the base's `migration_head_209` (git `610e61dc0`) copied with the backup
  API, only the edited 210 applied under `upgrade_allowance(UPGRADE_TEST_HELPER)`,
  `wal_checkpoint(TRUNCATE)` -> `(0, 0, 0)`, `journal_mode=DELETE` (header
  bytes 18-19 = 1/1), `integrity_check` ok, `foreign_key_check` empty, then
  copied into place with the backup API, with no companion files. The
  README says so.
- `db_generate_reference.py` was rerun on `04d06282f`. It changed commit
  labels, `help_assists`' new column and DDL, and the report as a direct SQL
  reader of `workbench_sessions` (and of `question_events` and
  `reveal_events`). `db_validate_reference.py` reports **0 errors**, and
  `validate_vault.py` passed (1124 notes).
- The stage record's §1.1 (61 columns, the three submission columns) and
  §1.6 (timing and unaided progress) were updated, along with the G-H17 row
  and spec §15's H0 note.

### Gate (targeted, owner rule; `TMPDIR` = the worktree's `fixtures-local/tmp`)

- `uv run pytest -n auto` over the same 72 files as the first fix round.
  A `git grep` of `tests/` for `submit_attempt`, `submit_dont_know`,
  `recover_practice_submission`, `handlers.practice`, `migration_head_210`,
  `help_assists`, `hints.report`, `stamp_submission` and
  `attach_reveals` found no test file outside them. Result: **1597 passed**
  (290.6 s; 1579 before plus this round's 18 new tests). After the final
  line wrapping, `tests/test_hint_telemetry.py` and
  `tests/test_help_assists_schema.py` were rerun: **63 passed**.
- Durability: `uv run pytest -m durability tests/test_help_assists_schema.py
  tests/test_library_asks_migration.py tests/test_learner_text_source_widening.py
  tests/test_migrations.py tests/test_tracked_fixture_databases.py
  tests/test_daily_plan_replay.py` gave **5 passed** (62 deselected), and
  `uv run pytest -n auto --durable-sqlite tests/test_help_assists_schema.py
  tests/test_hint_telemetry.py` gave **63 passed**.
- `uv run lint-imports --no-cache`: **25 kept, 0 broken**.
- Frontend and `cargo check`: not run, because nothing under `apps/` changed.
- Snapshots: the CLI help, serializer and RPC pins are unchanged (no option,
  help text or RPC changed), and their tests are in the targeted run.

**Model calls made in this round: 0** (fakes and self-grade only).

### Open questions (defaults taken)

1. **Items whose cap equals their hint count.** On such an item
   (`max_useful_hints == len(hints)`, as in the tests' basic vault), an
   attempt that reveals every authored hint is never `reached`: it is
   `help_count_capped`, as the ruling says. *Default: the ruling.* A
   successor could treat recorded distinct authored indexes == cap ==
   `len(hints)` as complete once the client's count is known to hold only
   authored reveals.
2. **Which tutor questions count.** Any tutor question on the item in the
   window that was answered (or counted as a hint) is other help, not only
   the `hint_equivalent` ones. The window is not limited to the session.
   *Default: the conservative one.*
3. **Workbench held hints are judged after the fact.** They count from the
   problem being open at the attempt's `created_at` and holding the book or
   carried hints (the submit itself reads `held_hints` live). *Default:
   conservative overlap.*
4. **The report always needs the vault's caps.** `build_hints_report`
   without `item_caps` reports every case as `help_cap_unknown`. Only the
   CLI calls it, and it always passes them.

### Commits

- `04d06282f`: the fixes (migration 210 and the rebuilt head fixture, the
  store, `learnloop.hints.telemetry` and `.report`, the CLI, the sidecar,
  tests, the stage record and spec §15).
- `a107e9a13`: the references regenerated on `04d06282f`.
- this record.

## Fix round 3 (after Codex job 20261018-002703-ixJaw2)

The Codex verify of `f2c34c928` found V1 and V3 fixed and three Medium
defects still in V2's other-assistance window in `learnloop/hints/report.py`,
W1-W3, each reproduced through the full report. All three are fixed in
`bea7af2a0`. Report inference only: no schema change (so no fixture or
reference regeneration; `db_validate_reference.py` still reports 0 errors),
and nothing in grading, `hints_used` or anything submit stores changes.

**Fail first.** The round's tests were run against `f2c34c928`'s code in a
detached worktree (removed after). **6 failed.** The 4 new tests failed on
behaviour:
- W1: `help_not_ordered` where `reached` was expected;
- W2: the same;
- W3, lower boundary: `reached` where `help_order_ambiguous` was expected;
- W3, upper boundary: `help_not_ordered` where `help_order_ambiguous` was
  expected.

The 2 round-2 tests failed only because their expected reason dict now
names `help_order_ambiguous: 0`.

| ID | Severity | Title | Verdict | Commit | Tests |
|---|---|---|---|---|---|
| W1 | Medium | The attempt's own same-second feedback display counted as help before it | fixed | `bea7af2a0` | `tests/test_hint_telemetry.py::test_the_attempts_own_feedback_display_in_its_second_is_not_help_before_it` |
| W2 | Medium | A later revisit of the previous attempt's feedback flips the next attempt | fixed | `bea7af2a0` | `::test_a_later_revisit_of_the_previous_attempts_feedback_is_not_help` (and A's feedback before B still counts) |
| W3 | Medium | A same-second tutor answer at a window boundary gives a false "reached" | fixed | `bea7af2a0` | `::test_help_in_a_boundarys_second_is_order_ambiguous_never_reached` (lower boundary; attributed to A it is help), `::test_help_in_the_attempts_own_second_is_order_ambiguous` (upper boundary, a reveal and a tutor answer) |

### What changed

`_other_assistance` now returns `"help"`, `"ambiguous"` or None. A new
`_window_position(event, ...)` places each tutor event (answered or counted
as a hint) and each reveal (`amount > 0`, other than this submission's own
self-grade disclosure, an exemption kept separate) against the attempt's
window, from the item's previous attempt up to this one. The window is now
evaluated in Python over the item's rows, at whole-second resolution
(`_second`).

- **W1.** An event attributed to the evaluated attempt (`attempt_id`) was
  written after that attempt existed. It is `outside` whatever its second.
- **W2.** An event attributed to the previous attempt is after the window
  opened. That relaxes only the lower bound: the upper bound still applies,
  so a revisit after the evaluated attempt is `outside`.
- **W3.** Without attribution, the whole-second time decides. An event in
  the same second as either boundary, or with an unparseable time, is
  `ambiguous`. Any `inside` event (or a held workbench hint) gives
  `help_not_ordered`. Otherwise any `ambiguous` event gives the new reason
  `help_order_ambiguous`, never `reached`. `UNAIDED_UNKNOWN_REASONS` is now
  `more_help_followed, primed, help_not_ordered, help_order_ambiguous,
  help_count_capped, help_cap_unknown, ungraded, not_fully_correct`.

**Pre-existing, not in H0's scope.** Grading's tutor-count fold
(`tutor_qa.hint_equivalents_for_submission` /
`count_hint_equivalent_question_events`, `created_at > since`) has the same
whole-second boundary. A hint-equivalent question stamped in the previous
attempt's second is not counted into the next attempt's `hints_used`. It is
left unchanged, as ruled: the W3 test asserts `hints_used == 1` there. It is
a candidate for a successor.

### Gate (targeted; `TMPDIR` = the worktree's `fixtures-local/tmp`)

- `uv run pytest -n auto tests/test_hint_telemetry.py
  tests/test_help_assists_schema.py tests/test_cli_help_snapshot.py`:
  **68 passed**. Only `report.py` and its test file changed. The report has
  no other test file, and the CLI help snapshot is unchanged.
- `uv run pytest -n auto --durable-sqlite tests/test_hint_telemetry.py
  tests/test_help_assists_schema.py`: **67 passed**.
- `uv run lint-imports --no-cache`: **25 kept, 0 broken**.
- `db_validate_reference.py`: **0 errors**, with no schema change and no
  regeneration.

**Model calls made in this round: 0.**

### Commits

- `bea7af2a0`: the fixes (`learnloop/hints/report.py`, tests).
- this record.
