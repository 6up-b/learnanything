# Reader RW5a: Codex review and fixes

Stage: reader workbench RW5a (explorable figures), branch `reader/rw5a`, worktree
`learnanything-dl2`. Codex reviewed `e14b4e4ff..0b4353fc4` adversarially, read-only (codex job
`20261020-200755-pWDBzQ`). This round reproduced every finding with a failing test first (all in
`tests/test_figures_codex_review.py`, 19 tests: 14 failed before the fix and 5 passed as
regression guards), then fixed all seven. No finding was rejected. No model call, live or paid,
was made. Every model is a fake, and the sandbox's equivalence runner is faked with its documented
result shape.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Held-out context stays deliverable through cached figures | fixed | `4a54bff24` | `test_f1_a_context_neighbour_held_out_after_authoring_withholds_the_figure`, `test_f1_a_neighbour_left_out_at_build_time_does_not_withhold_later` |
| F2 | High | Region-built figures have no anchor and disappear | fixed | `4a54bff24` | `test_f2_a_region_built_figure_is_anchored_under_its_region` |
| F3 | High | Source verification ignores additional equality invariants | fixed | `4a54bff24` | `test_f3_a_second_source_equation_is_never_left_unchecked`, `test_f3_one_named_equation_still_verifies` |
| F4 | Medium | Inconclusive negative controls count as rejected | fixed | `4a54bff24` | `test_f4_an_inconclusive_negative_control_is_not_a_rejection` (4 result shapes), `test_f4_every_control_refused_matches` |
| F5 | Medium | A later explanation never reaches a finished gap reading | fixed | `4a54bff24` | `test_f5_an_explanation_after_the_reading_is_read_as_its_own_text`, `test_f5_an_explanation_before_the_reading_is_read_with_it_once`, `test_f5_an_explained_source_with_no_explanation_reads_nothing` |
| F6 | Medium | The first figure prediction does not start the gap worker | fixed | `4a54bff24` | `test_f6_a_missed_prediction_and_its_explanation_wake_the_worker`, `test_f6_the_stopped_worker_starts_and_reads_the_prediction` |
| F7 | Medium | Concurrent identical requests duplicate paid work and rows | fixed | `4a54bff24` | `test_f7_identical_concurrent_builds_join_one_build`, `test_f7_a_paid_answer_survives_a_crash_before_the_row`, `test_f7_a_stored_failure_is_a_new_generation_that_asks_afresh`, `test_f7_a_second_shown_row_for_one_input_is_refused_by_the_schema`; `test_figures_migration.py::test_figure_checks` |

References were regenerated in `8570f116c`.

## What changed, by finding

**F1.** Reproduced: a figure built from `p3`, with neighbour `p4` sent as context, was still
listed, delivered and predictable after only `p4` was held out. Migration 216 (not yet landed, so
it was edited in place) gains `interactive_figures.input_span_ids_json`. It holds every span the
author was sent: the selection, the paragraphs around it (only those that were open at build time)
and the cropped block. `service._figure_spans` includes this list, so listing, `shown_figure`
(predictions and explanations) and revision checks all read it. Delivery
(`handlers.figures.deliver_figure`) now rechecks the stored row through `FS.figure_withheld`, which
fails closed when the row is gone, instead of reading the view's span list. The formative record's
provenance (`text_gaps.provenance.figure_prediction_record`) lists every input span. Its sources go
to the chat guard, and an unreadable manifest records as incomplete. A neighbour that was already
held out at build time was never sent, so it does not withhold the figure later (second test).

**F2.** Reproduced: a region build (`spanIds: []`) returned `anchorSpanId: null`. `figure_view`
now falls back to the region's block, so the figure is placed under it. Unsupported and failed
region results are placed the same way. `useFigures` already places by the server's
`anchorSpanId`, so the frontend did not change.

**F3.** Reproduced: a spec naming `f` and `g` in `equals_source` was labelled verified when only
`f` was checked. Spec §8.5 allows one verifier call per request, so a figure that names more than
one definition in `equals_source` gets no "matches the book" claim. It is stored `illustrative`
with the reason "the figure names N definitions as the book's equations and one check covers one",
and no verifier call is made. `verify.equals_source_definitions` returns the deduplicated list, and
`equals_source_definition` returns a name only when there is exactly one. Batching several
transcriptions into the one verifier call would change the verifier's output schema and prompt
version. It is left as an open question below and not done here.

**F4.** Reproduced with the sandbox's documented shape: `[True, None, None]` matched. A control now
counts as rejected only when its result is exactly `False`. `None`, an exception marker or any
non-bool rejects nothing. The new reason is "a negative control was inconclusive (the check raised
or gave no answer)".

**F5.** Reproduced: with the prediction's job already `done`, saving "what changed?" queued
nothing, and the explanation was never read. `jobs.enqueue_figure_explanation` now works like
this:

- If the prediction's own job is still `queued`, nothing is added: that reading reads the text as
  it is then, explanation included, once.
- If the reading has started or finished (any other state, or a gap row exists), the explanation
  becomes its own `reader_formative` text, `<prediction id>:explained`
  (`sources.FIGURE_EXPLANATION_SUFFIX`). It is read as the answer plus the explanation, and the
  earlier judgment is kept as it was read.
- If the prediction has no job at all, its base job is queued.

`figure_prediction_row` returns nothing for an explained source until the explanation exists. The
provenance record of an explained source is its prediction's record.

**F6.** Reproduced: `reader.figure_predict` queued the job but never woke the lazily started
worker. `record_prediction` and `record_explanation` now take an `on_queued` callback, and the
handler passes one that calls `ctx.post_attempt_worker.notify()`, following RW1b's and H2b's
handlers. The wire shape is unchanged. Two tests cover it:

- A recorded notify: a matched prediction wakes nothing, a missed one wakes the worker, and an
  explanation saved while that job is still queued wakes nothing more.
- A real stopped worker (`autostart=True`, fake `gap_clients`) starts on the prediction and drains
  it.

`tests/figure_fixtures.context` sets `autostart = False`, so the other figure tests never start a
thread with the configured routes.

**F7.** Reproduced: two overlapping identical builds made two author calls. After a crash between
the paid answer and the row insert, the rerun asked again, because the request id was a fresh ULID.
Three changes fix it:

1. In the process, `_building(repository, input_hash)` serializes builds of one input. A request
   that waited takes the figure stored meanwhile (whatever its verification) with no call.
2. The request identity is `content_key({input_hash, generation})`, where the generation counts the
   rows stored for that input. A rerun after a crash uses the same prompt, so `PaidCalls` recovers
   the checkpointed answer (or its receipt) with no second request. A stored failure starts the
   next generation, so "try again" still asks afresh. The author route's receipt owner is bound
   once the hash is known (`FigureRoute.bind_owner`).
3. Across processes, migration 216's unique partial index `idx_interactive_figures_reuse`
   (`input_hash, spec_version` where verification is verified, illustrative or unsupported) refuses
   a second shown row. A build that loses that race returns the first row. The paid calls it
   already made keep their receipts.

The sidecar is the only figure builder. A durable cross-process build claim (a new table) was not
added: see the open questions.

## Data

Migration 216 was edited before landing:

- added the `input_span_ids_json TEXT NOT NULL DEFAULT '[]'` column;
- added the unique partial index;
- trimmed the header comment to stay under the reference generator's 800-character design-note
  cap.

`RW5A_ADDED_OBJECTS` gains `idx_interactive_figures_reuse`. Table roles are unchanged
(`interactive_figures` WORKFLOW, `figure_predictions` RAW_LEDGER), and there is no DERIVED table.

The head fixture `fixtures/migration_head_216/state.sqlite` was rebuilt from git `e14b4e4ff`'s
`migration_head_213`. The steps were: a backup-API copy, only 216 applied under
`UPGRADE_SCRATCH_COPY`, then `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE`, header
bytes 1/1, `integrity_check` ok, `foreign_key_check` empty, and placement with the backup API with
no companion files. The README paragraph was updated, and the hard-coded paths did not change.

The DB references were regenerated (`db_generate_reference.py`) and validated
(`db_validate_reference.py`): `schema_head` 216, 335 table notes, `errors: []`.

The rebuild, the reference scripts and two measurement scripts ran under
`env -i PATH=… HOME=CODEX_HOME=LEARNLOOP_CONFIG_DIR=<empty fixtures-local/tmp dirs>` with the
worktree's `.venv/bin/python`. One plain file-edit `python3` heredoc (string replacement in
`migrations/216_interactive_figures.sql`, no learnloop import, no network) ran without `env -i`
before the wrapper was set up. No other Python ran outside pytest.

## Gate (this fix step)

- `uv sync --extra dev --extra mobile` (resolved 179 packages), then `uv pip install pypdfium2`.
- `uv run lint-imports --no-cache`: **29 kept, 0 broken**.
- Reproduction: `tests/test_figures_codex_review.py` failed **14 of 19** before the fix. After it,
  the figure files (`test_figures_codex_review.py`, `test_figure_*.py`, `test_figures_*.py`) gave
  **239 passed**.
- Targeted pytest, `TMPDIR=fixtures-local/tmp uv run pytest -n auto <90 files>`: **1,894 passed**
  (final run on `8570f116c`, 8 min 1 s; an identical earlier run before the commits also gave
  1,894 passed). The files:
  - every file that names the figure service or store, `text_gaps.sources/jobs/provenance`,
    `interactive_figures`/`figure_predictions`, `migration_head_216`, the reader report or
    observations, `table_roles` or the post-attempt worker;
  - plus the contract files `test_coordinated_migrations.py`, `test_tracked_fixture_databases.py`
    and `test_sqlite_file_copies.py`.

  test_ad1_migration, test_approach_map_replay, test_approach_maps_schema, test_architecture,
  test_coordinated_migrations, test_daily_plan_replay, test_daily_plan_review_regressions,
  test_daily_plan_rpc, test_diagnosis_async_router, test_diagnosis_card,
  test_diagnosis_input_provenance, test_diagnosis_replay, test_evsi_single_family_unbounded,
  test_exam_protection_review, test_facet_identity_actions, test_figure_grammar,
  test_figure_predictions, test_figure_region, test_figure_revisions, test_figures_codex_review,
  test_figures_migration, test_figures_rpc, test_figures_switch_off, test_figure_verification,
  test_forecast_receipts_landing, test_forecast_receipts, test_held_grade_composition,
  test_help_assists_schema, test_hint_feedback_texts, test_hint_feedback_widening,
  test_hint_h2b_review, test_hint_telemetry, test_learner_text_gaps_composition,
  test_learner_text_gaps_flow, test_learner_text_gaps, test_learner_text_gaps_rereview,
  test_learner_text_gaps_review, test_learner_text_source_widening, test_library_ask,
  test_library_ask_review, test_library_asks_migration, test_method_explicit_upgrade,
  test_migrations, test_mobile_allowlist, test_mvp010_upgrade, test_mvp011_upgrade,
  test_mvp013_upgrade, test_mvp014_upgrade, test_mvp015_upgrade, test_mvp016_upgrade,
  test_mvp017_route_check_replay, test_mvp017_upgrade, test_mvp018_upgrade, test_mvp020_upgrade,
  test_mvp021_upgrade, test_mvp022_upgrade, test_mvp023_upgrade, test_mvp024_upgrade,
  test_pfc_unverified_unassessed, test_plan_determinism, test_post_attempt_worker,
  test_project_report, test_reader_cues, test_reader_formative_texts, test_reader_intentions,
  test_reader_intent, test_reader_observation_records, test_reader_report, test_reader_rw1b_review,
  test_reader_tutor_offers, test_reader_tutor_switch_off, test_reader_workbench_rw2a,
  test_reading_step_switch, test_rebuild_orchestrator, test_recurrence_commands,
  test_recurrence_live, test_regrade_contract_upgrade, test_route_rules_in_grader,
  test_shadow_rebuild, test_source_block_fts, test_source_layer, test_sqlite_file_copies,
  test_stuck_prompt_replay, test_success_head, test_t6_followup_composition, test_table_roles,
  test_tier1_decider, test_tracked_fixture_databases, test_ux_phase4_landing,
  test_workbench_in_session_gaps, test_workbench_text_gaps.
- Durability, for the migration:
  - `uv run pytest -n auto -m durability tests/test_figures_migration.py tests/test_migrations.py
    tests/test_tracked_fixture_databases.py tests/test_coordinated_migrations.py
    tests/test_figures_codex_review.py`: **3 passed** (the durability-marked tests in those files);
  - `--durable-sqlite` over `test_figures_codex_review.py`, `test_figures_migration.py` and
    `test_figure_predictions.py`: **35 passed**, which covers the concurrent build and the worker
    under WAL with production pragmas.
- DB references: generated, then validated with 0 errors (head 216).
- No config key, CLI help, RPC name, wire shape, `apps/` or `src-tauri` change, so the defaults
  snapshots, CLI help, RPC pins, npm and cargo were not rerun. No new `shutil` copy was added.
- The full suite, the whole durability lane and the whole vitest run are left to the landing gate
  (owner rule 2026-10-17).

## Open questions

- **F3 batching.** Should a reconstruction that names several source equations get one batched
  verifier call, so it can verify? That needs a list-shaped `FigureVerifierOutputV1` and a
  `figure_verifier.v2` prompt. Until then such figures are honestly illustrative.
- **F7 cross-process claim.** A durable build-claim table was not added, because the sidecar is
  the only builder. Across processes the unique index prevents a duplicate row but not a duplicate
  paid call.
- **F5 backlog sweep.** The backlog sweep still queues prediction ids only. An explanation saved
  while gaps or `reader_formative` were switched off, after its prediction was read, is not swept
  later.

## Fix round 2 (orchestrator)

The orchestrator's pre-landing verify (codex job `20261020-210429-csgQmt`, on `66250a0ef`) confirmed
corpus parity, the execution-path AST checks, the flagship negative control, import-linter, migration
216 with its head fixture, and the switch-off prompt contract. It reopened the stage with 3 High and
3 Medium findings. This round fixes all six under the orchestrator's binding rulings. Each fix has a
test that fails on `66250a0ef`, checked by running the new tests against `git archive 66250a0ef`
(`src`, `migrations`) with `-o pythonpath=<old>/src`, and the new vitest cases against the old
`apps/learnloop-tauri` (extracted to a scratch directory that uses the worktree's `node_modules`).
No model call was made: every model is a fake (`GapLLMFake`,
`AuthorFake`, `VerifierFake`).

### Findings

| id | severity | title | verdict | test |
|---|---|---|---|---|
| R2-F1 | High | Held-out material reaches the gap reader | fixed | `test_f1_a_held_out_neighbour_keeps_a_missed_prediction_from_the_gap_reader`, `test_f1_a_later_explanation_of_a_held_out_figure_is_skipped_too`, `test_f1_an_unreadable_manifest_fails_closed` (guard: `test_f1_an_open_manifest_still_reads`) |
| R2-F4 | High | The sandbox coerces inconclusive results into rejections | fixed | `test_f4_controls_answered_with_no_boolean_never_verify_a_figure` (None, 0, ""), `test_f4_the_harness_reports_each_answer_as_given` (None, 0, ""), `test_f4_pf_generator_tests_count_an_inconclusive_answer_as_not_passing`, `test_f4_pf_equivalence_confirms_nothing_when_a_control_is_answered_with_no_boolean` (guard: `test_f4_controls_answered_false_still_verify_through_the_same_harness`) |
| R2-F3 | High | "Checked" is not bound to what is displayed | fixed | `test_f3_a_transformed_series_labelled_as_the_book_equation_is_an_illustration`, `test_f3_every_source_labelled_series_and_readout_must_be_the_checked_definition` (4 cases), `test_f3_the_flagship_is_bound` (guards: `test_f3_the_checked_definition_drawn_by_reference_verifies`, 2 cases) |
| R2-B | Medium | Large-integer sum limits and PMF supports freeze the renderer | fixed | golden corpus: `sum_bound_past_safe_integers` (expression and rejected input), `sum_negative_bound_past_safe_integers`, `pmf_support_past_safe_integers` (guard: `sum_bound_near_safe_integers`); `test_a_sum_near_the_safe_integers_counts_its_terms`, `test_pmf_supports_past_the_safe_integers_are_refused`; vitest "integer bounds (fix round 2)" |
| R2-F7 | Medium | A same-process race still duplicates paid work | fixed | `test_f7_a_build_committed_between_the_reads_is_reused_inside_the_lock` |
| R2-F5 | Medium | Explanations saved while gap reading is off are never read | fixed | `test_f5_off_save_on_sweep_reads_the_explanation_once` (guards: `test_f5_an_explanation_the_first_reading_read_is_not_swept_again`, `test_f5_a_prediction_never_read_is_swept_once_with_its_explanation`) |

All the new Python tests are in `tests/test_figures_fix_round2.py`; the shared cases are in
`tests/figure_corpus.py`, which regenerates `figureGoldenCorpus.json`.

### What changed, by finding

**R2-F1 (held-out material, gap reader).** The predicate the figure service uses now lives in
`content/sources/exam_material.spans_withheld(vault, repository, extraction_id, span_ids)`:
`exam_material(...).covers(...)` or `.withheld(...)`, with the same refusal text.
`figures.service.withheld_message` delegates to it, so there is one predicate and no second check.
`text_gaps.sources.figure_prediction_text` calls it on the figure's complete manifest before it
builds anything. The manifest comes from `figure_input_manifest`: the selection, the region's
block, the crop's block and `input_span_ids_json`. `figure_prediction_row` now reads those
columns. The provenance record uses the same manifest helper. An unreadable manifest fails
closed. A withheld text raises `sources.SourceWithheld`, and `jobs.process_next_gap_job` ends
the job `skipped` with `last_error` "held out: ...". So nothing reaches `reader_prompt`, and
neither the backlog sweep nor a retry reads it again. Both the prediction source and its
`:explained` source are covered.

**R2-F4 (the sandbox keeps inconclusive results).** The PF-b harness
(`content/authoring/pf_sandbox._HARNESS`) no longer calls `bool()` on a check's answer. Its
`verdict()` returns True or False only for a boolean and None for anything else (None, 0, "", a
number, an unevaluated relation). Python's `True` and `False` count as booleans, and so do
numpy's and sympy's boolean singletons. This applies in `test`, `check` and `equivalence` mode.
In equivalence mode the standard controls also report `inconclusive_controls` per program. The
figure verifier (`figures/verify.run_source_match`) needs four things to verify:

- the candidate's answer is exactly True;
- each of its two mandatory controls (×8/7 and halved) is exactly False;
- the check is not degenerate;
- no standard control is inconclusive.

The composition is tested end to end: the real harness in the real bubblewrap sandbox, a
`VerifierFake` check that answers its controls with None, 0 or "", and the figure service. The
figure is `illustrative`, and the same harness with `False` still verifies.

How each other PF sandbox caller behaves now (inconclusive counts as not passing everywhere):

- `ops/pf_generation` generator tests: `self_check` is True, False or None, and only True
  passes, as before for booleans. `negative_controls_rejected` is now
  `all(control is False)`, where it was `not any(...)`. A check that answers a wrong answer
  with None or 0 used to be counted as rejecting it and now fails the program, with
  `negative_controls_inconclusive` and a message saying so. A check that *raises* on a wrong
  answer still rejects it: that exception rule was explicit in the harness, not a coercion, so
  it is kept on purpose. The same holds for the equivalence mode's standard controls.
- `ops/pf_generation` panel checks (`check_generator_answers`): the values were already mapped
  through `{True, False, None}`. A non-boolean answer is now `None` ("error"), where it used to
  be coerced to agree or disagree.
- `ops/pf_verify` and `ops/embedding_compare` go through `equivalence_confirmations`, which
  already mapped non-booleans to None. It now also returns `[None] * n` (confirms nothing, not
  degenerate) when the check answered a standard control with a non-boolean.
- `workbench/symbolic.py` runs its own fixed harness, not the PF one, and is unchanged.

No caller needed the coercion kept: their test files are all in the gate and pass.

**R2-F3 (bound to what is displayed).** `verify.displayed_source_problem(compiled, name, claims)`
is a structural check over the compiled spec and makes no model call. `service._source_match`
runs it before the verifier call. A figure with a problem is `illustrative` (the reason is
stored, the label is "not checked against the book"), and the verifier is never asked. The
figure passes only if both of these hold:

1. At least one series, readout or map cell is the checked definition itself.
2. Every plotted series and readout whose label names the source equation is exactly that
   definition: a bare reference to it, with no transform and no inlined copy. A label names the
   source equation when the definition's name is its first word (`f`, `f(x)`, `f_X(x)`, but not
   `frequency`), or when it is a verified quote's left-hand side (`f_X(x)` of "f_X(x) = ...").

So `f(x) = x` verified but `2*f` plotted under the label `f(x)` is an illustration (the ruling's
test), and so are these: a quote-LHS label on a transformed series, a readout labelled `f(p)`
that is not `f`, a figure that draws nothing that is `f`, and `x` written out instead of `f`.
The flagship stays bound: its series `f` is labelled "density", and its readout `P(X ≤ 0)` is
not a source label.

**R2-B (integer bounds, both evaluators).** `grammar.MAX_SAFE_INTEGER = 2**53 - 1` in Python, and
`MAX_SAFE_INTEGER = Number.MAX_SAFE_INTEGER` in `figureGrammar.ts`. Both evaluators apply the
same rules in the same order:

- **When parsed:** a `sum` whose literal bound (or negated literal) lies past ±MAX_SAFE_INTEGER is
  refused.
- **When evaluated:** `exact_sum`/`exactSum` gives NaN for a computed bound past it. The loop
  counts its terms (`low + index`, at most `MAX_SUM_TERMS`) instead of stepping `k += 1`, which
  could never advance past 2^53 in a double.
- **When compiled:** a PMF support must be whole numbers within ±MAX_SAFE_INTEGER and at most
  `MAX_BARS` (200) bars. The TypeScript `compileSpec` now has these checks; it had none for PMF
  supports.
- **When the bars are drawn:** `bar_ks`/`barKs` count at most `MAX_BARS` bars.

The shared corpus cases run in both pytest and vitest. On the old frontend, the expression case
`sum(1, k, n, n + 2)` with `n = 1e20` hangs vitest; it was killed by `timeout 60`.

**R2-F7 (the race).** `build_figure` now rereads `store.reusable` inside the `_building` lock and
returns any reusable row before authoring. The ruling asked for a deterministic interleaving
test. Its first `reusable` read is patched to return nothing, as if it ran before another build
committed, while `latest_for_input` sees the committed row. On `66250a0ef` that made one more
author call. Now it makes none and reuses the row.

**R2-F5 (the backlog).** `sweep_backlog` now also queues `<id>:explained` for every missed
prediction with an explanation, when its prediction's reading is finished (done, skipped or
failed, or only a gap row exists) and no `:explained` job or gap exists yet. Two cases are left
out:

- the reading's gap row already carries the explanation, because it was saved while that job
  waited, so the original reading consumed it;
- the prediction itself was never read, so the sweep queues the prediction and its one reading
  reads the explanation too.

`sources.explained_predictions` lists the candidates by SQL; the job and gap state is read before
the sweep queues anything. The off → save → on → sweep sequence reads the explanation once as its
own text, and a second sweep queues nothing.

### Fail-before counts (on `66250a0ef`)

- `tests/test_figures_fix_round2.py`: **21 of 27 failed**. The 6 that passed are the guards named
  above (an open manifest still reads, `False` controls still verify, two drawn-by-reference
  figures still verify, a consumed explanation is not swept, a never-read prediction is swept
  once).
- `tests/test_figure_grammar.py` on the new corpus: **5 failed**:
  - `test_the_corpus_file_is_the_cases_as_generated`;
  - the NaN expression case;
  - the two rejected literals;
  - the rejected PMF support.

  The near-safe guard passed.
- `figureGrammar.test.ts` on the old frontend: the 6 new cases all failed or hung. 4 failed in
  the filtered run (two rejected literals, the rejected PMF figure, the PMF/bars test). The
  expression case hung (killed by `timeout 60`, exit 124). The counted-sum test failed when run
  alone. The near-safe expression case passed.

### Gate (this fix round)

- Setup: `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2`, with
  `TMPDIR=<worktree>/fixtures-local/tmp`. `/tmp/learnloop-fullsuite.lock` was free at each run.
- `uv run lint-imports --no-cache`: **29 kept, 0 broken**.
- Targeted pytest, `pytest -n auto` over **144 files**. These are round 1's 90-file list plus:
  - every test file that names a PF sandbox caller (`pf_sandbox`, `pf_verify`, `pf_generation`,
    `embedding_compare`, `workbench.symbolic`);
  - every test file that names `text_gaps` or the figure package;
  - `tests/test_figures_fix_round2.py`.

  Result: **2,812 passed, 2 xfailed, 0 failed** (13 min 16 s).

  The first run (2,811 passed, 1 failed) caught one thing:
  `test_architecture.py::test_function_local_domain_imports_match_the_frozen_edge_inventory`
  refused a new function-local import of `exam_material` in `text_gaps.sources`. The import was
  moved to module level (`diagnosis` already imports `exam_material` there, in `remediation`), and
  the rerun above is on that tree.

  The one warning is an unrelated existing thread leak: a `learnloop-reading-sweep` thread hit
  `test_success_head`'s `sqlite3.connect` trap.
- `--durable-sqlite` over `test_figures_migration.py`, `test_figure_predictions.py`,
  `test_figures_codex_review.py` and `test_figures_fix_round2.py`: **62 passed**.
- `-m durability` over `test_figures_migration.py`, `test_migrations.py`,
  `test_tracked_fixture_databases.py` and `test_coordinated_migrations.py`: **3 passed**.
- `apps/learnloop-tauri`:
  - `npm run typecheck`: clean.
  - `vitest run src/screens/reader`: **62 files, 615 passed**, including the figure files'
    169. An earlier run made while the pytest gate loaded the machine timed out in unrelated
    Reader tests at about 5.5 s each; the run on an idle machine passed.
  - `npm run frontend:build`: built.
- DB references: `db_generate_reference.py`, then `db_validate_reference.py`, under `env -i`
  (empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` in `fixtures-local/tmp/r2`; they stayed
  empty). Result: 335 table notes, `errors: []`. Line citations moved in `text_gaps.jobs`, so the
  references are committed separately.
- The golden corpus was regenerated with `python -m tests.figure_corpus --write` under the same
  `env -i`. The diff is additions only, and the fuzz verdicts are unchanged.
- No migration, config key, RPC, wire shape or `src-tauri` change, so cargo, the defaults
  snapshots and the RPC pins were not rerun. The full suite, the whole durability lane and the
  whole vitest run are left to the landing gate (owner rule).
- **Rule deviations:** two Python invocations ran outside `env -i`. One was a `python3 -` with an
  empty heredoc (no code ran). The other was a stray `uv run python -c "print(1)"`. Neither
  imported learnloop or touched the network, a config or a vault. Every other Python run outside
  pytest used the `env -i` wrapper.


### Residual notes

- R2-F3 decides "names the source equation" by structure only: the definition's name as the
  label's first word, or a verified quote's left-hand side. A label that names the book's equation
  in prose ("the book's density") is not recognised. The coverage rule (something drawn *is* the
  checked definition) is what bounds that case.
- R2-B refuses literal (and negated literal) sum bounds when parsed. A constant expression past the
  safe integers (`0 - 1e20`) parses, and both evaluators give NaN for it, so the structural step
  refuses the figure as not finite.
- R2-F4 keeps one deliberate rule: a check that raises on a sandbox standard control
  (`""`, nonsense, a far number) rejects it, as before. The figure's own two controls must be
  exactly `False`.

## Fix round 3 (orchestrator)

The orchestrator's verify of `1dde8ddf0` (codex job `20261020-220610-kYPQCn`) confirmed several things:
F1's manifest guard, F4's boolean handling, the integer-loop bounds, F7's reread, and that the PF
callers had no regression. It reopened the stage with 2 High and 4 Medium findings. Three of those
were Python/TypeScript/SymPy parity divergences. Per the binding ruling, that class is closed
structurally, by narrowing the grammar and adding a differential property test, not case by case.
Each fix has a test that fails on `1dde8ddf0`. Python was checked with `git archive 1dde8ddf0`
(`src`, `migrations`) and `-o pythonpath`. The frontend was checked on an old
`apps/learnloop-tauri` in a scratch directory that uses the worktree's `node_modules`. No model call
was made.

### Findings

| id | severity | title | verdict | test |
|---|---|---|---|---|
| R3-1 | High | SymPy verifies a different sum than the renderer evaluates | fixed (class) | `test_a_sum_the_renderer_shows_differently_never_matches_the_book` (empty and fractional ranges, real sandbox), `test_a_sum_matches_the_book_when_the_renderer_shows_the_same`, `test_a_definition_sympy_cannot_read_exactly_is_never_checked`; property test |
| R3-2 | High | Switch-off output differs from base (the report's `figures` block) | fixed | `test_figures_off_is_the_base_reader_report` (golden recorded on an export of `e14b4e4ff`), `test_figures_on_adds_only_the_figures_block_to_the_report`, `test_the_report_cli_follows_the_switch` |
| R3-3 | Medium | F5 still drops a late explanation that repeats the reading's text | fixed | `test_f5_an_explanation_repeating_the_answer_is_still_read` (the verify's "it rises" case), `test_f5_the_reading_records_whether_it_read_the_explanation` |
| R3-4 | Medium | Python and TypeScript disagree on signed zero | fixed (class) | `test_no_value_is_negative_zero`; property corpus (signed-zero family) |
| R3-5 | Medium | Accepted identifiers vanish in TypeScript (`__proto__`) | fixed (class) | `test_prototype_and_underscore_names_are_refused_when_parsed`, `test_a_parameter_named_like_the_prototype_is_refused`; property corpus (reserved family) |
| R3-6 | Medium | Structural verification omits displayed matrix results | fixed | `test_a_map_whose_shown_values_overflow_fails_structure` (determinant, corner, padded reach), guard `test_a_finite_map_and_the_flagship_still_pass_structure` |

The new tests are in these files:

- `tests/test_figures_fix_round3.py`;
- `tests/test_figure_property.py` with `tests/figure_property_corpus.py`, which writes
  `figurePropertyCorpus.json`;
- the "property corpus (fix round 3)" block in `figureGrammar.test.ts`;
- three report tests appended to `tests/test_figures_switch_off.py`, with the golden at
  `tests/fixtures/figures_switch_off_report.json`.

### What changed

**Parity by construction (R3-1, R3-4, R3-5).** The grammar was narrowed so the three readings
cannot disagree.

- **Names.** In both tokenizers and both `is_name`/`isName`, a name is
  `^[A-Za-z][A-Za-z0-9]*$`: there is no underscore, so no `__proto__`. Object.prototype's other
  own names are refused when parsed (`PROTOTYPE_NAMES`: `constructor`, `hasOwnProperty`,
  `isPrototypeOf`, `propertyIsEnumerable`, `toLocaleString`, `toString`, `valueOf`) and are
  reserved, so no parameter, definition or variable can use them. The TypeScript environments are
  `Object.create(null)` (`newEnv`) all the same. The author prompt's grammar line states the rule.
- **Signed zero.** Every node's value is canonical in both evaluators: `evaluate` wraps the node
  evaluator with `canonical` (-0 becomes +0), and so does every shown value (`_num`/`num`) and the
  plot's x samples. `1/min(0, -0)` is +Infinity in both.
- **Sums.** A sum's bounds follow one rule: `ceil(a - 1e-9) .. floor(b + 1e-9)`, and an empty range
  is 0. Both evaluators already applied it. `to_sympy` now writes it out:
  `Piecewise((Sum(body, (k, ceiling(a - 1/10^9), floor(b + 1/10^9))), Ge(high, low)), (0, True))`.
  SymPy's own `Sum` summed a reversed range negatively (Karr) and kept fractional bounds.
- **What is not source-verifiable.** Where SymPy cannot reproduce the evaluator's value exactly,
  `grammar.sympy_problem` names the reason, and `service._source_match` keeps the figure
  illustrative without a verifier call. Three constructs qualify:
  - an equality test (`==`, `!=`);
  - `floor`, whose steps floating point places differently at the renderer's own samples;
  - `integral`, which is the fixed Simpson rule. The property generator found that at a jump it
    parts from SymPy's exact `Integral` by about 5e-4 relative.

  Ordered comparisons and sums translate exactly, apart from boundaries that rounding decides,
  which are a set of measure zero.

**The differential property test, the parity contract from now on (R3-1, R3-4, R3-5).**
`tests/figure_property_corpus.py` generates 3,000 random grammar expressions with a seeded
generator and adds 152 cases from fixed families: signed zeros (also under a -0 environment), empty
and fractional sum ranges, reserved-looking identifiers, piecewise comparisons, and large and small
magnitudes. Each case is stored with the Python evaluator's verdict, value and scale (the largest
magnitude of any subexpression) in `figurePropertyCorpus.json`: 3,152 cases, 3,131 accepted.

- **`tests/test_figure_property.py`** checks four things:
  - the file is the generator's output;
  - no value is -0;
  - SymPy's reading has the evaluator's value on every translatable accepted case with a finite
    value (2,208 cases);
  - the sum-rule and unverifiable-construct units.

  Literals are read as the doubles the evaluator uses, as integers or 60-digit floats holding the
  exact binary value. `to_sympy` keeps the book's exact decimals for the real check. 1,770 cases
  are compared within 1e-9 of the case's scale. 438 are set aside by measured rules, never by id:
  - a comparison or sum bound that rounding decides;
  - a cancellation (a sum or difference 1e-6 smaller than its operands);
  - an infinite or NaN subexpression of a finite value (IEEE's 1/0, which SymPy has as zoo).
- **vitest** holds the TypeScript parser and evaluator to every case: the same verdict, the same
  value within the case's scale, the same non-finite kind, and never -0.

**R3-2 (report switch-off).** `build_reader_report` takes `figures_enabled` (default `False`). Only
when it is true does the report read the figure tables and carry its `figures` block. The CLI
passes `vault.config.figures.enabled`. The golden is `build_reader_report` on
`tests/test_reader_report._seed`, recorded on an export of `e14b4e4ff` (`RW5A_WRITE_GOLDEN=1`,
`-o pythonpath=<export>/src`). The test seeds one figure and one missed, explained prediction
before comparing. Switched off, the report equals that golden. Switched on, removing `figures`
gives the golden back.

**R3-6 (displayed derived values).** `verify._shown_values` now walks every number in the panel
data at any depth: inputs, a map's determinant and transformed corners, a shaded area's bounds and
value, readouts, and any future field. It also checks the scales the renderer derives: a plot's
value range and a map's reach, each padded by 10%. Every one must be finite on the parameter grid.
`[[1e200, 0], [0, 1e200]]` now fails structure, with its determinant of 1e400 not finite.

**R3-3 (F5 by marker).** `LearnerText` gains `markers`, which is never sent to a model. A figure
prediction's text sets `explanation_read`. When the reading is done, `process_next_gap_job`
records the text's markers on its job (`payload_json.markers`). `sweep_backlog` treats an
explanation as consumed only when the prediction's job carries `explanation_read: true`; nothing
searches the text. The verify's case: the reading read "it rises", then "it rises" was saved as
the explanation while gap reading was off. The sweep now queues `:explained`.

### Fail-before counts (on `1dde8ddf0`)

- `tests/test_figures_fix_round3.py`: **24 of 27 failed**. The 3 that pass are guards or cases
  Python already got right:
  - the finite map and the flagship;
  - `piecewise((1/min(0, -0) < 0, 1), 2)` and `1/floor(-0)` on Python's side. Their divergence
    was in TypeScript, and the vitest property test catches it.
- `tests/test_figure_property.py`: **8 of 11 failed**:
  - the corpus is not the old evaluator's output, because the old evaluator yields -0;
  - all three sum-rule units;
  - all three unverifiable-construct units;
  - the SymPy check. On the old grammar it claims integrals are translatable, and SymPy's exact
    integrals of the generated bodies do not finish in pytest within 15 minutes. The same helpers,
    run outside pytest under `env -i` with integrals skipped, find **96 mismatching cases, 92 of
    them generated**. Examples: `sum(1, k, 2.5, -2.5)` is 0 vs SymPy's -4, and
    `sum(1, k, 0.5, 2.5)` is 2 vs 3.
- `tests/test_figures_switch_off.py`: the **3 new report tests failed**; the 2 existing ones pass.
- vitest on the old frontend: the property test **failed on 167 cases, 111 of them generated**.
  Examples: `1/min(0, -0)` is -Infinity vs Python's inf, `piecewise((1/min(0, -0) < 0, 1), 2)` is
  1 vs 2, and `__proto__` cases were accepted although the corpus refuses them.

### Gate (this fix round)

- Setup as in round 2: `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`, and
  `TMPDIR=<worktree>/fixtures-local/tmp`. `/tmp/learnloop-fullsuite.lock` was free.
- `uv run lint-imports --no-cache`: **29 kept, 0 broken**.
- Targeted pytest, `pytest -n auto` over **146 files**: round 2's 144 plus
  `test_figure_property.py` and `test_figures_fix_round3.py`, with every file that names the reader
  report already among them. Result: **2,853 passed, 2 xfailed, 0 failed** (14 min 28 s).
- `--durable-sqlite` over `test_figures_migration.py`, `test_figure_predictions.py`,
  `test_figures_codex_review.py`, `test_figures_fix_round2.py` and `test_figures_fix_round3.py`:
  **89 passed**.
- `-m durability` over the migration files: **3 passed**.
- `apps/learnloop-tauri`:
  - `npm run typecheck`: clean.
  - `vitest run src/screens/reader`: **62 files, 616 passed**. This includes the figure files and
    the property test over all 3,152 cases.
  - `npm run frontend:build`: built.
- The golden corpus is unchanged. The property corpus was generated with
  `python -m tests.figure_property_corpus --write` under `env -i`. The report golden was recorded
  by pytest on the `e14b4e4ff` export.
- DB references were regenerated and validated under `env -i`, and committed separately.
- No migration, config key, RPC or `src-tauri` change, so cargo, the defaults snapshots and the RPC
  pins were not rerun. The full suite is left to the landing gate (owner rule).


### Residual notes

- The contract is now the property corpus. A new construct, or a change in either evaluator, must
  regenerate it under `env -i` (`python -m tests.figure_property_corpus --write`) and pass both
  suites.
- `floor`, `==`/`!=` and `integral` remain drawable, but a definition using one is never "matches
  the book's equation (checked)".
- One more `python3 --version` ran outside `env -i` while I edited the TypeScript twin (no code,
  no learnloop import). Every other Python run outside pytest in this round used the `env -i`
  wrapper with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

## Fix round 4 (orchestrator)

The orchestrator's verify of `e330926e4` (codex job `20261020-233018-22IDaO`) confirmed several
things: the corpus is fresh (3,152 cases regenerated and matched, 1,770 SymPy comparisons); F1, F4,
the loop bounds, F7, migration 216 and the write boundaries are intact; and the prompt-contract and
report gates are repaired. It found 2 High and 3 Medium. This is the third round with a false
"checked" from a semantic divergence, so the ruling closes it with a narrower rule instead of
another patch: "checked" is now certified by display agreement. Each fix has a test that fails on
`e330926e4`. Python was checked with `git archive e330926e4` (`src`, `migrations`) and
`-o pythonpath`. The frontend was checked on an old `apps/learnloop-tauri` in a scratch directory
that uses the worktree's `node_modules`. No model call was made.

### Findings

| id | severity | title | verdict | test |
|---|---|---|---|---|
| R4-1 | High | "Checked" still verifies a different value from the renderer | fixed (rule) | `test_a_literal_that_is_not_a_small_exact_decimal_is_never_checked` (`sin(10000000000000001)`), `test_rule_a_on_literals`, `test_display_agreement_catches_a_branch_rounding_decides` (`piecewise((0.1 + 0.2 > 0.3, 1), 2)` and the near-boundary `piecewise((x*10 < 3, 1), 2)`), `test_the_flagship_stays_checked_with_its_display_certified`, `test_every_corpus_exclusion_rule_is_illustrative_at_runtime` (4 rules) |
| R4-2 | High | Switch-off still changes the backlog CLI and permits figure-derived model work | fixed | `test_figures_off_backlog_dry_run_is_the_base_output` (golden recorded on an export of `e14b4e4ff`), `test_figures_off_queues_and_reads_no_figure_text` |
| R4-3 | Medium | F5's marker can claim a cached reading read an explanation | fixed | `test_f5_an_explanation_after_a_checkpointed_reading_is_its_own_text` (the verify's checkpoint, explanation, retry sequence) |
| R4-4 | Medium | Structure accepts non-finite displayed coordinates | fixed | `test_a_plot_domain_whose_samples_overflow_is_refused` (the 1e308 domain), `test_structure_requires_every_numeric_leaf_finite` (NaN, ±inf); vitest "refuses a plot domain whose samples would overflow" |
| R4-5 | Medium | An in-cap definition chain crashes compilation | fixed | `test_the_verifys_seven_level_chain_compiles_and_evaluates`, `test_a_chain_past_the_depth_cap_is_a_validation_error`, `test_the_depth_cap_is_the_same_in_typescript`; vitest "bounded compilation (fix round 4)" |

The Python tests are in `tests/test_figures_fix_round4.py`, plus two in
`tests/test_figures_switch_off.py` with the golden at `tests/fixtures/figures_switch_off_backlog.json`.
The TypeScript tests are in `figureGrammar.test.ts`.

### What changed

**R4-1: "checked" is certified by display agreement.** A figure earns "matches the book's
equation (checked)" only when all four rules hold. `service._source_match` applies them in order,
after the binding and translatability checks of rounds 2 and 3:

- **(a) Small, exact literals.** `verify.literal_problem` requires every numeric literal of the
  expanded checked definition to be a small exact decimal: |x| ≤ 1e6 with at most 9 significant
  digits, by `Decimal`. `pi` and `e` are allowed. This rule needs no verifier call, so a failing
  definition is illustrative with none.
- **(b) Exact translation.** `to_sympy` already writes each literal as its exact decimal
  `Rational('…')`, not as a double, and that stays the production translation.
- **(c) Equality.** The sandboxed check must pass, as before: the candidate exactly True and the
  controls exactly False.
- **(d) Display agreement.** `verify.display_agreement` runs in code after the check passes, with
  no model call. It finds every place the checked definition is drawn by reference (a series, a
  readout or a map cell). At every point of the parameter grid, it takes the production
  evaluator's own displayed data (`evaluate_figure`): for a plot, every plotted x (or k) sample.
  - A fixed harness evaluates the unmodified production translation (`to_sympy`) in the PF-b
    sandbox. It reads the text only there, and evaluates with mpmath at 50 digits on the exact
    binary values of the samples.
  - The comparison is made here. Each displayed value must equal the reference to a relative or
    absolute 1e-9.
  - Every piecewise condition must choose the same branch at every sample: the harness's truth
    is compared with the evaluator's `_truth`.

  Any disagreement, a value that is not finite, a SymPy evaluation that fails, a sandbox that
  cannot run, or a piecewise choice inside a sum's body (chosen per term, which the samples cannot
  pin down) makes the figure illustrative. The report records `display_agreement`. For the
  flagship, 1,089 samples agree.

The corpus's exclusion rules decide nothing at runtime. A test builds each one at a plotted sample
and the runtime finds it illustrative:

- a comparison rounding decides: `x*10 < 3` at x = 0.3;
- a sum bound rounding decides;
- a cancellation, `(x + 10^12) - 10^12`;
- a non-finite subexpression.

**R4-2: switch-off covers figure-derived learner text.** With `figures.enabled` off
(`sources.figures_enabled`), every figure-derived path stops:

- backlog discovery (`missed_formative_ids(figures=False)`) finds no figure prediction;
- the `:explained` reconciliation does not run;
- `enqueue_figure_prediction` and `enqueue_figure_explanation` queue nothing;
- the processing adapter (`reader_formative_text`) builds no figure text.

A figure job already queued is deferred by `process_next_gap_job` before any text is built and
before any model call. It is released to the next day with `last_error` "deferred:
figures.enabled is off", its attempt refunded, so it is neither failed nor skipped. Neither
`run_pending` nor the sidecar's gap worker stops draining for it.

`learnloop gaps run --backlog --dry-run --json` with figures off equals the golden recorded on an
export of `e14b4e4ff` (`RW5A_WRITE_GOLDEN=1`), although the vault holds an unread missed,
explained prediction. With figures on, the same vault owes that prediction.

**R4-3: the marker is checkpointed with the reading.** `process_next_gap_job`'s `save_progress`
adds the text's markers to the job's first checkpoint, which is the reading or the decision.
Later checkpoints keep them, so a retry that reuses the reading keeps the checkpoint's marker
whatever the text says now.

A job that already holds a reading counts as started (`_reading_checkpointed`), in both the live
`enqueue_figure_explanation` and the backlog sweep. So an explanation written after the checkpoint
becomes its own `<id>:explained` text.

The verify's sequence now plays out like this: the reading is checkpointed, the attempt fails, the
explanation is saved, and the retry runs. The base job completes on the cached reading, so it reads
once, with marker `explanation_read: false`. The explanation is then read as its own text, and the
sweep owes nothing.

**R4-4: every numeric leaf finite, and the domain bounded.** `verify.structural` now rejects any
leaf that is None or not `math.isfinite`, which covers NaN and ±inf. A function plot's x range may
span at most 1e12 (`MAX_DOMAIN_SPAN`, in both `spec.py` and `figureSpec.ts`), so the samples cannot
overflow. The 1e308 domain is a validation error.

**R4-5: compilation never recurses unboundedly.** The passes over expanded definitions are now
iterative in both evaluators:

- `walk` and `free_names`;
- `node_count`, `has_bound_form`, and the new `expansion` and `expanded_depth`;
- `spec.expanded_free` and `expandedFree`.

`check_names` caps the expanded depth at 700 (`MAX_EXPANDED_DEPTH`, the same in TypeScript),
checked before any other pass, and refuses it as a grammar error, which becomes a `SpecError` or
`FigureSpecError`.

The Python evaluator now takes one frame per level, so the recursive evaluator and translator stay
far inside the recursion limit. `parse_spec` and `compileSpec` turn a residual `RecursionError` or
`RangeError` into a validation error, as a safety net only.

The verify's 7-level chain is 1,261 nodes and 631 levels deep once expanded. It compiles and
evaluates in both evaluators. A 9-level chain is refused: "nests deeper than 700".

The grammar changed (the depth cap), so both corpora were regenerated under `env -i`. They are byte
for byte unchanged.

### Fail-before counts (on `e330926e4`)

- `tests/test_figures_fix_round4.py`: **24 of 24 failed**. That includes the flagship
  certification test, because the old report has no `display_agreement`.
- `tests/test_figures_switch_off.py`: the **2 new tests failed**; the 5 existing ones pass.
- vitest on the old frontend: **2 of the 3 new tests failed** (the depth cap and the domain span).
  The 7-level chain already ran in JavaScript, and it stays as a guard.

### Gate (this fix round)

- Setup as in rounds 2 and 3. `/tmp/learnloop-fullsuite.lock` was free.
- `uv run lint-imports --no-cache`: **29 kept, 0 broken**.
- Targeted pytest, `pytest -n auto` over **147 files** (round 3's 146 plus
  `test_figures_fix_round4.py`): **2,879 passed, 2 xfailed, 0 failed** (9 min 3 s).
- `--durable-sqlite` over the figure migration and prediction tests and the four review test files:
  **113 passed**.
- `-m durability` over the migration files: **3 passed**.
- `apps/learnloop-tauri`:
  - `npm run typecheck`: clean.
  - `vitest run src/screens/reader`: **62 files, 619 passed**. This includes the figure files, the
    property corpus and the bounded-compilation tests.
  - `npm run frontend:build`: built.
- Both corpora were regenerated under `env -i` and are unchanged. The backlog golden was recorded by
  pytest on the `e14b4e4ff` export.
- DB references were regenerated and validated under `env -i`, and committed separately.
- No migration, config key, RPC or `src-tauri` change, so cargo, the defaults snapshots and the RPC
  pins were not rerun. The full suite is left to the landing gate (owner rule).
- Every Python run outside pytest this round, version checks included, used the `env -i` wrapper.

