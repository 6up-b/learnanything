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
