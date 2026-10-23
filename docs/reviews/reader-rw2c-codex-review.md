# Reader RW2c: Codex review and fixes

Stage `reader-rw2c`, branch `reader/rw2c` in `learnanything-dl2`. Reviewed range `7e7bdff1b..dd8aa4420`
(Codex job `20261021-130058-VhHlvc`, read-only). Fix commit `a73f013ca`. No migration, no schema change, no new
config key, no new model route; migration head stays 217.

## Findings

Every finding was reproduced first: each test below fails on the reviewed code (run against a `git archive` of
`dd8aa4420`'s `src/` and `migrations/` under `fixtures-local/tmp/rw2c-base`, with `-o pythonpath=` pointing at
it; the Reader test by reverting its one-line routing change) and passes on `a73f013ca`.

| id | severity | title | verdict | commit | test |
|---|---|---|---|---|---|
| F1 | Medium | Cross-book examples cannot open their referenced passage | fixed | a73f013ca | `ReaderScreen.rw2cExample.test.tsx` (two real Reader sources: Book B's example opens Book B; Book A's is a peek, as before); `test_workbench_route_example.py::test_review_f1_an_example_in_another_book_carries_that_books_identity` |
| F2 | Medium | Comparison verdicts never reach judgment_ledger | fixed | a73f013ca | `test_compare_methods.py::test_f2_the_comparison_verdict_is_a_judgment_with_its_lines` |
| F3 | Medium | Explicitly chosen hints disappear from help history | fixed | a73f013ca | `test_help_outcomes.py::test_f3_hints_the_learner_picked_stay_in_the_history_passage_picks_do_not_count_twice` |
| F4 | Medium | Existing valid work is reported as unaided progress | fixed | a73f013ca | `test_help_outcomes.py::test_f4_a_step_already_on_the_page_that_a_later_check_validates_is_not_progress`, `::test_f4_no_work_recorded_at_delivery_stays_unknown`, `::test_f4_an_intervening_example_is_further_help_but_the_hints_own_bridge_is_not` (control: `::test_f4_a_step_written_after_the_hint_that_the_check_validates_is_progress`) |
| F5 | Medium | Comparisons get credit for outcomes before they opened | fixed | a73f013ca | `test_help_outcomes.py::test_f5_a_comparison_gets_no_credit_for_an_attempt_before_it_was_opened` |
| F6 | Medium | Historical outcome reads change after a future regrade | fixed | a73f013ca | `test_help_outcomes.py::test_f6_a_later_regrade_never_changes_what_as_of_said`, `::test_f6_a_hold_released_after_as_of_still_held_then` |
| F7 | Medium | Reopening a pending comparison starts duplicate paid jobs | fixed | a73f013ca | `test_compare_methods.py::test_f7_reopening_a_pending_comparison_starts_no_second_generation` (blocked fake model, threaded jobs, overlapping opens), `::test_f7_only_the_claims_holder_settles_and_a_stale_claim_can_be_taken_over` |
| F8 | Medium | The comparison kill switch does not stop pending-result delivery | fixed | a73f013ca | `test_compare_methods.py::test_f8_switching_compare_methods_off_while_its_lines_are_written_delivers_nothing` |
| F9 | Medium | Cached comparison lines are paired with a different reference after edits | fixed | a73f013ca | `test_compare_methods.py::test_f9_a_changed_reference_opens_a_new_comparison_with_its_own_reveal`, `::test_f9_lines_are_never_written_against_a_reference_other_than_the_rows` |
| F10 | Medium | S5 outcomes are added alongside independently derived passage outcomes | fixed | a73f013ca | `test_help_outcomes.py::test_f10_an_s5_record_naming_a_passage_is_its_outcome_and_is_not_counted_again` |

No High finding was raised. None was rejected.

## What changed, per finding

* **F1.** The worked example's hit already carried `source_id` (find_sources' hits); it is now kept on the example
  row's placement, its result, `example_view`, each draw option (`passage_draw.option_record`, only when present)
  and an "another passage" pick, and `bridge_view` shows it only when a row has one (an RW2b bridge's view is
  unchanged). In the app, `onPeek` / `onPeekPassage` take an optional `PassageTarget` (`extractionId`,
  `sourceId`); the example line always passes it, a picked bridge only when it names a book (RW2b's bridge peeks
  exactly as before). `ReaderScreen` routes the workbench's peeks through `peekWorkbenchPassage`: another book
  opens there through `openLibraryHit` (RW4a's detour: Alt+← returns, and the problem keeps its ✎ resume mark;
  the working posture belongs to its book, so it folds while Book B is open), the open book is a peek as before.
* **F2.** `compare_lines` appends one `judgment_ledger` row in the same transaction as the lines: task
  `workbench_compare_methods`, left the comparison's `help_assist`, right the `practice_attempt`, judge `llm`
  with the route's model, the prompt version and the prompt's input hash; verdict `same_method` /
  `valid_other_route` / `route_not_valid`; rationale the two booleans, differences kept, their kinds, the number
  returned and dropped, the reference kind and identity (never a line's text or the reference).
* **F3.** Only a passage pick (`bridge`/`example` with `chooser = 'learner_pick'`, "another passage") is not a help
  kind of its own; a hint the learner picked ("a smaller step", "the book's way") is a hint with its continuation,
  grade, later outcome and replies. help_outcomes computes no propensity-weighted estimate, so nothing else is
  excluded; RW2d's note (exclude picks from any IPS estimate) stands.
* **F4.** The per-help continuation is now the hint service's: `learnloop.hints.report_workbench.
  workbench_unaided_progress(row, session_rows, maps=)`, which `help_outcomes` reads (C13: defined once, there).
  The work at delivery is the row's step snapshot (a hint's own; a passage under a hint uses its hint's; a worked
  example now records the steps it was searched with, ids and hashes only), and progress is a valid step at the
  next check whose `(chain_id, hash)` was not on the page at delivery. No snapshot: `unknown`. Any other shown help
  before that check (a hint, a bridge, an example, a pick, a comparison) is `more_help`, except what was delivered
  with the help (its hint, and the bridge and example that delivery started); when the further help is the next
  hint and both sit on one map, the next hint's placement settles it (`report_adaptive.progress_by_next_placement`,
  §6.1's rule). The practice screen's `learnloop hints report` is unchanged (its workbench rows still read
  `workbench_state_unknown`, its own documented case); it can adopt the function at its next change.
* **F5.** For each help, the later-independent window starts at the later of its attempt and the help's own display.
* **F6.** `help_outcomes(..., vault=)` reads each attempt as graded at `as_of`: unchanged since then (no grading row
  or blind record written or superseded after it), its stored correctness and today's held predicate; otherwise
  the rows standing at `as_of` (RW6a's `snapshot_as_of` reading), their current epoch
  (`grading_epochs.current_epoch`) summed over the rubric maximum (the regrade's own division), the route-rule hold
  from the blind records written by then and that epoch's assessed criteria, and replay's unrecorded-contract hold
  decided from that epoch (`facet_evidence_timeline.epoch_held_as_of`, now a public alias of RW6a's helper). Without
  a vault such an attempt reads as ungraded at `as_of`, never as its later grade. `lines_for_item` passes the vault.
  The fold's residual is RW6a's (a fatal-error cap or PF-c rescale is not re-applied to the summed points).
* **F7.** The lines are claimed on the row (`placement.lines_claim`, token and time, in a `BEGIN IMMEDIATE`
  transaction) before the model is called; a worker that finds a live claim calls nothing (`in_progress`); only
  the claim's holder settles; a failure releases the claim; a claim older than `CLAIM_SECONDS` (960 s, the
  sidecar's per-request timeout) can be taken over. The handler keeps the job per comparison and hands a reopen
  the pending (or finished-with-lines) job.
* **F8.** `_payload` cancels an undelivered `compare` job while `workbench.compare_methods_enabled` is off, as the
  bridge and example jobs do; `compare_lines` refuses `disabled` before claiming, and checks the job's cancel flag
  before calling the model.
* **F9.** A comparison row records `reference_hash` (kind, text, extraction and span ids of what it showed). A
  reopen reuses only a row with the current reference's identity; otherwise it writes a new row (noting
  `replaces_assist_id`) with its own reveal of the matching kind (`source_review` for the book's solution,
  `answer_display` for the key). `compare_lines` refuses `reference_changed` for a row whose reference is no longer
  the current one, so lines are never written against another reference.
* **F10.** A workbench passage named by an S5 record **by its assist id** (the record's `caller_ref`, or
  `assets.help_assist_id`; never a match on time, item or spans) takes its later outcome from that record (S5's
  `R_cold` with censoring) and the record is not counted again as a separate retrieval help; the continuation stays
  the workbench's next check (S5 records no workbench check). Today neither the bridge nor the worked example writes
  an S5 record, so on main nothing is double-counted yet; this is the association the spec's §18 item 5 (S5 copying
  the draw's propensity and seed into its record) will use.

## Spec-conformance notes not raised as findings

Left as the stage record states them (`reader-workbench-RW2c.md` §2, §6): tutor exchanges, library asks and figure
views are not yet help kinds (deferred to RW2d/RW6b, not approximated); the report's "Interventions → outcomes" block
is not yet a `help_outcomes` consumer (RW6b's narrative is its first); compare methods is not offered in the classic
feedback view (default kept). Horizon-specific history is not split out (the rows' `horizon` is not read).

## Process notes

* No live or paid model calls; everything model-backed ran on fakes. No CLI or app run against a vault.
* Two short local scripts ran as plain `python3` before the `env -i` wrapper was set up: one read `pyproject.toml`
  with `tomllib` to list import contracts, one rewrote text in four source files. Neither imported the app or made a
  network call. Every later script ran under `env -i PATH HOME=<empty> CODEX_HOME=<empty>
  LEARNLOOP_CONFIG_DIR=<empty>`.
* The threaded F7/F8 tests were run alone three times (3/3 passed each time) under the machine's load.
* `/tmp/learnloop-fullsuite.lock` was held by another worktree's targeted run (UX2), not a landing gate; targeted
  runs need no lock, so none was taken.

## Gate (targeted; the full suite runs once, in the landing gate)

Environment: `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`, `TMPDIR=<worktree>/fixtures-local/tmp`.
No migration, no DB/connection code, no schema change: no durability lane, head fixture, table_roles or DB reference
work. Nothing under `src-tauri` changed in this step, so no `cargo check`.

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 29 kept, 0 broken |
| `uv run pytest -n auto` on the 91 files below | **1980 passed, 1 skipped** (RW4e's base-tree-only golden recorder) |
| fail-before: the 15 new review tests on the `dd8aa4420` archive | 15 failed (the F4 control passed, as it should) |
| `npm install`, `npm run typecheck` | clean |
| `npx vitest run` on the 36 files below | **398 passed** |
| fail-before: `ReaderScreen.rw2cExample.test.tsx` with the routing change reverted | 1 failed, 1 passed (the same-book control) |
| `npm run frontend:build` | built |

**Pytest files (91).** Contract pins: `test_sqlite_file_copies`, `test_cli_help_snapshot`,
`test_sidecar_serializer_snapshot`, `test_desktop_rpc_contract`, `test_mobile_allowlist`, `test_architecture`,
`test_table_roles`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_config_refactor`. RW2c:
`test_help_outcomes`, `test_workbench_passage_draw`, `test_workbench_route_example`, `test_compare_methods`,
`test_rw2c_switch_off`. RW2b/H3 and the hint service: `test_reader_rw2b_review`, `test_reader_rw2b_fix3` … `fix15`,
`test_workbench_assistance`, `_check`, `_check_map`, `_chooser`, `_discriminate`, `_help_kill_switch`,
`_hint_service`, `_hints`, `_in_session_gaps`, `_report`, `_step_graph`, `_text_gaps`, `_trace`, `test_hint_service`,
`test_hint_h2a_review` (+ rounds 2–4), `test_hint_h2b_review`, `_rereview`, `_fix3`, `_fix4`, `test_hint_kill_switch`,
`test_hint_report`, `test_hint_telemetry`, `test_hint_feedback_texts`, `test_hint_feedback_widening`,
`test_hint_authored_reveal_ruling`, `test_help_assists_schema`, `test_approach_maps`, `test_approach_map_replay`.
RW4b: `test_reader_rw4b_fix6`, `test_reader_rw4b_admission_idempotency`, `test_dl2_rw4b_keyed_pick_check`,
`test_library_exercises`, `test_rw4_kill_switches`, `test_exam_protection`, `test_exam_protection_review`,
`test_reader_intentions`. Other readers and switch-off pins: `test_ad1_attempt_columns`, `test_ad1_migration`,
`test_adaptive_difficulty_ad1`, `test_figure_predictions`, `test_figures_migration`, `test_library_asks_migration`,
`test_reader_recap`, `test_reader_recap_review`, `test_reader_recap_review_r3` (RW6a's as-of hold, now also read by
help_outcomes), `test_reader_wrap_up`, `test_ux_phase4_feedback`, `test_compare_keep_switch_off`,
`test_figures_switch_off`, `test_reader_rw3b_switch_off`, `test_reader_tutor_switch_off`, `test_roles_switch_off`,
`test_roles_switch_off_legacy_parity`. Grades, reveals, the cold lane and the sources spec: `test_held_grade_evidence`,
`test_reveal_ledger`, `test_remediation_cold_retry`, `test_serve_eligibility`, `test_find_sources_intents`,
`test_reader_find_sources_callers`.

**Vitest files (36).** New: `screens/ReaderScreen.rw2cExample.test.tsx` (2). RW2c: `screens/workbench/RouteExample`
(one pin re-recorded for this stage's own key: the example's peek now names its target),
`screens/feedback/CompareMethods`, `screens/FeedbackScreen.phase4`. The workbench: `screens/workbench/` `HelpLadder`,
`Workbench`, `reviewFixes`, `switchOff`, `symbolicOff`, `fingerprint`, `stepModel`; `PracticeScreen.workbench`,
`reader/readerWorkbenchExercise`, `reader/readerWorkbenchQueue`. Every `ReaderScreen.*` file (`branches`,
`checkOffer`, `cuesSwitchOff`, `discoveredCues`, `discoveredCuesReview`, `followsLearner`, `guide`, `inquiry`,
`inquiryOff`, `k7`, `marginMarks`, `marginMarksReview`, `parity`, `pdfSelection`, `preparing`, `quickcheck`, `recap`,
`recapReview`, `review`, `workbench`). Feedback exposure: `feedback/answerExposure`, `answerExposure.shell`.

**For the landing gate.** The module reference (`_scripts/module_generate.py`) is regenerated at landing, as for the
stage's own new modules; this step adds `report_workbench.workbench_unaided_progress` and
`facet_evidence_timeline.epoch_held_as_of`.

## Fix round 2 (orchestrator)

The orchestrator's pre-landing verify of `bf7f9926c` (Codex job `20261021-140135-len1zH`, read-only) confirmed:
no evidence, mastery, scheduling or certification writes; item-only, transactional comparison reveals, written
before the reference is delivered; compare lines on `CheckRoute` through `PaidCalls`; and no Codex bypass. It
reopened the stage with 3 High and 5 Medium findings. All eight are fixed in `e575da4c2`. None was rejected. No
migration, no schema change, no new config key, no new route, and no model call. Migration head stays 217.

**Fail-before.** Every new test failed on `bf7f9926c` for its own reason:

* Python: run against a `git archive bf7f9926c src migrations` under `fixtures-local/tmp/rw2c-fr2-base`, using
  `-o pythonpath=<it>/src`. 14 of 14 failed.
* Vitest: run against the old `apps/learnloop-tauri` extracted to `fixtures-local/tmp/rw2c-fr2-apps`, with the
  worktree's `node_modules` linked in. 3 failed; the fourth test is a control and passed.

All of them pass on `e575da4c2`.

| # | severity | finding | test(s) (fail on `bf7f9926c`) |
|---|---|---|---|
| 1 | High | A cancelled or switched-off example could search after its bridge wait | `test_rw2c_fix_round2.py::test_fr2_1_…[switches_off]`, `[cancelled]`: before the fix, the held bridge was released, then the example searched (find called, a row was written) |
| 2 | High | "another passage" could deliver a passage held out since the draw | `::test_fr2_2_another_passage_skips_an_option_held_out_since_the_draw`, `::test_fr2_2_…refused_when_every_other_option_is_withheld_now`, `::test_fr2_2_…items_own_passage_or_reproduces_its_answer_is_withheld` |
| 3 | High | Stored draws broke all-switches-off payload parity | `::test_fr2_3_with_every_switch_off_a_problem_with_rw2c_history_restores_the_base_payload`: `help_state` and `workbench.get` run by `tests/rw2c_state_parity.py` under `7e7bdff1b` and under the tip, on the same database |
| 4 | Medium | Bridge draws included referenced blocks the judge never saw | `::test_fr2_4_a_referenced_block_appended_after_verification_is_never_a_draw_option`, `::test_fr2_4_the_draw_is_between_the_judged_spans_only` |
| 5 | Medium | S5 outcomes did not replay at `as_of` | `::test_fr2_5_an_s5_record_read_before_its_censoring_horizon_is_pending_not_expired`, `::test_fr2_5_a_later_regrade_never_changes_s5s_outcome_at_as_of_linked_or_standalone`; the guard `::test_fr2_5_the_s5_historical_read_leaves_current_behaviour_alone` (an ImportError before the fix) |
| 6 | Medium | Unrelated edits counted as recovery | `::test_fr2_6_an_unrelated_edit_to_an_earlier_valid_step_is_not_progress_after_a_waypoint` (through `help_outcomes`), `::test_fr2_6_progress_is_measured_where_the_hint_was_placed` (the shared function directly, with controls) |
| 7 | Medium | Cross-book bridge navigation lost the book | `::test_fr2_7_a_drawn_bridge_in_book_b_names_book_b_initially_and_after_a_resumed_pick`; `rw2cFixRound2.test.tsx` "7: … from the bridge job's first result", "7: a resumed problem whose last pick was in Book B opens Book B" |
| 8 | Medium | Explicit example requests could read unsaved work | `rw2cFixRound2.test.tsx` "8: show me a similar example waits for the steps to save and refuses while a save is failing" (before the fix the search was asked); control "8: with the steps saved …" |

### What changed

1. **The example re-reads the live vault after its wait.** The example worker started after a hint waits for its
   sibling bridge. After that wait, it checks two things before it reserves its place or searches:
   * its job's cancel flag;
   * the sidecar's CURRENT vault (`workbench_rw2c._live_example_vault`): the same database; help, examples and the
     sources spec's S3 all on; the item still there; and the problem statement not withheld.

   It then runs on that vault, with its daily envelope, `max_calls_per_session` and `passage_draw_enabled`, never
   the captured ones. `route_example.example_for` takes the cancel flag and reads it again just before the
   reservation and again before the search. A cancel there settles the row `cancelled`.
2. **"another passage" revalidates the cached option.** `passage_draw.option_withheld` checks a cached option again
   against what holds now. It makes no search and no model call, and it refuses an option when:
   * the session's caller is no longer `assisted_practice` (a cold administration);
   * the one exam predicate (`exam_withheld`: exam and held-out material) covers it;
   * `teaching_exclusions` covers it;
   * `item_exclusions` covers it (the item's own passages and whole extractions);
   * its role is exercise or solution;
   * its stored block, when it can be read, leads as an exercise or solution, or reproduces the item's answer.

   The handler computes the withheld set before the pick's transaction. `another_passage` skips a withheld option
   and moves to the next, never returning to the passage on screen. When none is left, it refuses `no_alternatives`
   with reason `withheld`, and no pick row is written.
3. **RW2c serialization follows the current switches.** Each RW2c field is serialized only while its switch is on
   at read time:
   * `ladder.bridge_view(row, passage_draw=)` adds `source_id` and the draw fields (`alternatives`, `option_id`,
     `draw_assist_id`) only while `workbench.passage_draw_enabled` is on;
   * `route_example.example_view(row, passage_draw=)` adds its draw fields under the same rule;
   * `workbench_help._rw2c_fields_now` drops the bridge's `RW2C_BRIDGE_FIELDS` and the example's `alternatives` from
     a cached job result read after the draw is switched off, and drops a hint result's `example_job_id` after
     examples are switched off.

   The parity test builds a problem with RW2c on: a drawn bridge in Book B, a pick on it, a drawn example under the
   hint and a "show me" example. It then switches all four RW2c switches off. On that database, the tip and
   `7e7bdff1b` serialize `help_state` and `workbench.get` identically.
4. **Bridge draws use judged spans only.** A bridge draws only among `bridge.verified_spans(eligible, manifest)`, the
   spans the manifest's `span_keys` name (`extraction_id/span_id`). A referenced block that `with_references`
   appends after verification is never an option. With no `span_keys` there is no draw (fail closed). The test
   fakes of T6's provider now return `span_keys`, as T6 does.
5. **S5 has a historical read, and `help_outcomes` uses it.** The new read is
   `substrate.intervention_outcomes.outcomes_as_of(vault, connection, as_of, *, grades)`. It runs S5's own
   `outcome_for` over only what was written by `as_of`: the interventions, attempts, reveals, source exposures,
   coldness receipts and the learner's taps. Each attempt carries its grade and hold as they stood then (from
   `help_outcomes`' grading-history read), and expiry is judged at `as_of`.

   Current-time behaviour is unchanged:
   * The replayer and its reference time are unchanged. `exposure_evidence` and `_signals` only gained an optional
     cutoff.
   * The guard test checks that at the replayer's own `as_of`, with today's grades, the read reproduces the
     persisted rows.

   `help_outcomes` reads every S5 outcome through `outcomes_as_of`, for both a linked passage (by its assist id) and
   a standalone record. Without a vault, S5 cannot judge its targets or exposures. Those outcomes then read
   `unknown` / `unmeasured`, and `sources` reads `read_without_vault`. The two existing S5 tests had faked the
   derived table directly; they now seed S5's real inputs and pass the vault.
6. **Progress counts only where the help was placed.** `hints.report_workbench.workbench_unaided_progress` is the
   shared definition. Its last step is now `_progress_at_placement`, read from the help's placement, which is a
   hint's own or a passage's hint. A new or changed valid step counts as progress when any of these holds:
   * it lands on the help's target node: the hint's target, or for a kind without one the next node
     (`report_adaptive.hint_target`);
   * it is the step the help was about, or the first questionable step;
   * it comes after the step the help continues from (with neither recorded, any step counts).

   A step that was already valid at delivery and was only edited does not count, unless it lands on the target.
   *(Corrected in fix round 3, L1: only `help_outcomes` calls this function. The hint service's report does not:
   `hints/report.py` still reports its workbench rows as `workbench_state_unknown`.)* The targeted gate also ran
   the hint report's tests: `test_hint_report`, `test_workbench_report` and the H2a/H2b review files. Earlier F4 behaviour is unchanged (its four tests pass).
7. **A bridge keeps its book.** The bridge stores the chosen span's `source_id` in its placement and returns it on
   its result. The views send it under the rule in 3. In the app, `drawnFields` in `useWorkbenchHelp.ts` carries
   `sourceId` into the bridge state, on the first result and on resume. The hint view DTO's `bridge` gained
   `sourceId`. `StepHints` already peeks with a target whenever a bridge names its book.
8. **"Show me a similar example" waits for saves.** `useRouteExamples` takes `beforeRequest`; `Workbench` passes the
   same `flushEdits()` + `drained()` barrier that checks and hints use. While a save is failing, the search is
   refused with "Your latest steps aren't saved yet, so no example was looked for", and nothing is asked.

### Process notes

* No live or paid model calls: everything ran on fakes. No CLI or app run against a vault, and no owner vault
  opened.
* One text-edit heredoc (a one-line replacement in `workbench_rw2c.py`) ran as plain `python3` before the `env -i`
  wrapper was set up. It imported nothing from the app and made no network call. Every later script and every
  pytest/npm run used `env -i PATH HOME=<empty> CODEX_HOME=<empty> LEARNLOOP_CONFIG_DIR=<empty>`.
* One vitest invocation hit a zsh glob miss, which emptied its file list, so it ran the whole vitest suite:
  173 files, 1,489 passed. That run is recorded here for completeness; the targeted run is in the table below.
* No `git stash`. `/tmp/learnloop-fullsuite.lock` was free, and targeted runs take no lock.

### Gate (targeted; the full suite runs once, in the landing gate)

Environment: `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`, `TMPDIR=<worktree>/fixtures-local/tmp`.
No migration and no DB/connection or schema change, so there is no durability lane and no head fixture or DB
reference work. Nothing under `src-tauri` changed, so there is no `cargo check`.

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 29 kept, 0 broken |
| `uv run pytest -n auto` on the 97 files below | **2,032 passed, 1 skipped** (RW4e's base-tree-only golden recorder) |
| fail-before: `tests/test_rw2c_fix_round2.py` on the `bf7f9926c` archive | 14 failed |
| `npm run typecheck` | clean |
| `npx vitest run --maxWorkers=6` on the 41 files below | **423 passed** |
| fail-before: `rw2cFixRound2.test.tsx` on the old `apps/` | 3 failed, 1 passed (the control) |
| `npm run frontend:build` | built |

**Pytest files (97):**
* the 91 of the round above;
* `test_rw2c_fix_round2` (new; `test_sqlite_file_copies` audits its helper-script copy);
* S5's: `test_intervention_outcomes_replayer`, `test_retrieval_interventions_write_points`,
  `test_sources_merge_composition`, `test_valuation_calibration_fields`, `test_rebuild_orchestrator`.

The hint service's report tests (`test_hint_report`, `test_workbench_report`) were already among the 91.

**Vitest files (41):**
* every `screens/ReaderScreen.*` test;
* every `screens/workbench/*` test (`rw2cFixRound2.test.tsx` new);
* every `screens/feedback/*` test;
* every `screens/FeedbackScreen*` test;
* `PracticeScreen.workbench`, `reader/readerWorkbench*`, `app/practiceFeedback`.

**For the landing gate.** `_scripts/module_generate.py` regenerates the module reference at landing. This round adds:
* `intervention_outcomes.outcomes_as_of`;
* `bridge.verified_spans`;
* `passage_draw.option_withheld`;
* `ladder.passage_draw_enabled` and `ladder.RW2C_BRIDGE_FIELDS`.

## Fix round 3 (orchestrator)

An adversarial Opus reviewer verified `a1027ed04` (Codex is out of quota until Oct 27). It confirmed:

* evidence is untouched;
* reveal timing and the cold lane are correct;
* leak control holds;
* the draw is logged;
* help outcomes are pure as-of reads;
* the switch-off payload matches the base;
* there is no new Codex path, and the caps hold.

It raised one Medium (M1) and eight Low (L1–L8). M1, L4, L6 and L8 are fixed in `5825048f7`. L1 corrects this record.
L2, L3, L5 and L7 are recorded as open items, with no change. No migration, no new route, no model call.

**Fail-before.** `tests/test_rw2c_fix_round3.py` was run against a `git archive a1027ed04 src migrations`, using
`-o pythonpath`. All 7 tests failed, each for its own reason. All pass on `5825048f7`.

| id | finding | fix | test(s) |
|---|---|---|---|
| M1 (Medium) | Example rows had no `step_verdicts_json`, so an unrelated edit counted as `continued` | `report_workbench._valid_at_delivery` (below); example rows now store their verdicts | `test_m1_rewording_an_already_valid_step_is_progress_for_neither_the_hint_nor_its_example` (the reviewer's probe), `test_m1_a_show_me_example_with_no_verdicts_on_record_is_unknown_never_continued`, `test_m1_a_show_me_example_reads_its_own_verdicts_or_the_last_check_before_it`, `test_m1_example_rows_store_the_verdicts_they_were_searched_against` |
| L4 | The compare worker used the vault captured at open | It runs on the CURRENT vault and checks the switch again just before the call | `test_l4_switching_compare_methods_off_after_the_open_makes_no_call` |
| L8 | A failing `start_example_after_hint` failed the read of a delivered hint | The call is wrapped: logged (`workbench_example_start_failed`), recorded as `example_job_id: None` | `test_l8_an_example_that_cannot_start_never_fails_the_delivered_hints_read` |
| L6 | The compare RPCs were not pinned to the withheld-exercise gate | `workbench.compare_offer` / `workbench.compare_methods` call `_refuse_withheld_exercise`, and `compare_methods.offer` refuses `exercise_withheld` | `test_l6_the_compare_rpcs_refuse_a_problem_whose_exercise_is_withheld_now` |
| L1 | This record overstated the function's readers | Corrected above, and below | (record only) |

### What changed

* **M1: progress needs the verdicts that stood at delivery.**
  * `workbench_unaided_progress` now reads which steps were valid at delivery through `_valid_at_delivery`, in this
    order:
    1. the row's own verdicts;
    2. for a hint without verdicts, the last shown check at or before it, or none (no check had been shown);
    3. for a passage under a hint, that hint's verdicts, by the same rule;
    4. for a "show me" example without verdicts, the last shown check at or before it.
  * When nothing is on record, the result is `unknown`, never `continued`.
  * New example rows store their verdicts: after a hint, a copy of the hint's record; on "show me", the workbench
    context's verdicts.
  * The presence check goes through the one accessor: the new `symbolic_view.has_verdict_record`, kept under the
    architecture pin.
  * One existing test changed. Round 1's F4 example ("an intervening example is further help") was a "show me"
    example with no verdicts and no earlier check, so it now gives its row the verdicts new rows carry.
* **L4: the compare worker uses the live vault.** `workbench_rw2c._live_compare_vault` gives the current vault while
  help and compare methods are on and the database is the same. The worker runs on it. `compare_lines` gains
  `still_enabled()`, checked again after the claim and before `route.ask`; when it fails, the claim is released and
  the result reads `disabled`.
* **L8: an example that fails to start no longer breaks the hint.** In `_payload`, an exception from
  `start_example_after_hint` is logged and recorded as no example. The delivered hint's read returns as usual.
* **L6: the compare RPCs pass the withheld-exercise gate.** `_refuse_withheld_attempt` runs the workbench's gate on
  the attempt's problem before either compare RPC reads or writes anything. The domain `offer` also checks
  `WB.statement_cleared`, so `open_comparison` refuses before any reveal or row. The test checks four things:
  * both RPCs refuse with `exercise_withheld`;
  * the domain `offer` and `open_comparison` refuse too;
  * no reveal is written;
  * no comparison row is written.

  An explicit pin was preferred to arguing that `_exam_item` covers this case. `_exam_item` judges the item; the gate
  judges the problem's picked region.
* **L1: record correction.** Only `help_outcomes` calls `workbench_unaided_progress`. The hint service's report
  (`hints/report.py`) still reports its workbench rows as `workbench_state_unknown`.
  * **Deviation against C13:** the workbench continuation has no "time to the next valid step" (adaptive hints §6.1
    lists it).
  * The hint service's report can adopt the shared function, together with that time, at its next change.

### Open items (recorded, no change)

* **L2.** `workbench.max_calls_per_session` is not cumulative for examples, the same as for RW2b's bridge. Each
  search is bounded by the source service's own daily cap.
* **L3.** A switch-off leaves residue in stored rows: a bridge's `placement.source_id`, the draw columns, and the
  examples that `session_calls_on` counts. All of it is serialized only while the switches are on (round 2, item 3).
* **L5.** `help_outcomes` runs synchronously on the hint-request path, at n = 1 scale. A facet-filtered query or a
  cached read is a follow-up if latency shows.
* **L7.** Cross-book bridge navigation (`source_id` on bridge views) works only while `passage_draw_enabled` is on.
  With the draw off, a bridge is RW2b's, which opens the passage in the book already open.

### Process notes

* No live or paid model calls; fakes only.
* All scripts and tests ran under `env -i` with empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR. No stash. No owner
  vault opened.
* A session restart interrupted the round. The resumed run inspected the uncommitted work, kept all of it, and
  finished.
* `/tmp/learnloop-fullsuite.lock` was held by another process when the gate ran. The targeted run went ahead
  without waiting for it (targeted runs take no lock), and it passed.

### Gate (targeted)

No frontend file changed in this round, so vitest, typecheck and build were not re-run. Their round-2 results stand.

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 29 kept, 0 broken |
| `uv run pytest -n auto` on 98 files (round 2's 97 + `test_rw2c_fix_round3`) | **2,039 passed, 1 skipped** |
| fail-before: `tests/test_rw2c_fix_round3.py` on the `a1027ed04` archive | 7 failed |
