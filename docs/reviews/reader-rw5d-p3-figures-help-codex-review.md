# Reader RW5d P3: figures as a help kind (Codex review and fixes)

- **Stage:** `reader-rw5d-p3-figures-help`, branch `reader/rw5d-p3-figures-help` in `learnanything-merge2`; stage record `docs/reviews/reader-rw5d-p3-figures-help.md`.
- **Review:** Codex (gpt-6.1-sol), job `20261101-204152-5rvAyd`, on the stage head `3c24c95401`. It reported 4 High and 5 Medium findings.
- **Live calls:** none. Every model in the tests is a fake: the figure author, the rich author and renderer, the retrieval, the Decider and the hint writer. Outside pytest, two things ran under `env -i` with an empty, existing HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR: the head-fixture rebuild on a backup-API scratch copy under `fixtures-local/rw5d-p3-fix/`, and the reference scripts.
- **Reproduced first:** each finding has a test in `tests/test_figures_help_codex_review.py` (21 tests), plus the migration tests in `tests/test_help_assist_figures_migration.py`. I ran these against the pre-fix source and migration (`git checkout 3c24c95401 -- src migrations fixtures/migration_head_232`, restored afterwards). All 21 new tests and the 3 migration tests that read the new 232 failed: 24 failed, 3 passed. The vitest cases for F4 and F8 test calls the pre-fix panel never made.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Unverified session references let displayed figures escape the Submit fold | fixed | `09380802a8`, tests `61d4bb1264` | `test_f1_an_unknown_or_ended_session_is_refused_before_any_job`, `test_f1_a_key_already_in_another_session_is_refused_so_no_row_escapes_the_fold`, `test_f1_a_take_step_token_from_another_session_is_not_this_attempts` |
| F2 | High | The reveal scan misses answers visibly present in figures | fixed | `09380802a8`, tests `61d4bb1264` | `test_f2_a_manim_figure_reveals_its_shown_words_and_narration`, `test_f2_a_manim_figure_stating_the_key_overlaps_it_and_a_neutral_one_does_not`, `test_f2_a_js_animation_reads_its_html_and_js_literals`, `test_f2_numbers_are_formatted_as_the_desktop_panels_format_them`, `test_f2_a_grammar_figures_shaded_area_is_read_as_shown` |
| F3 | High | Moving into Work in Steps can count the same figure twice | fixed | `09380802a8`, tests `61d4bb1264` | `test_f3_the_same_figure_opened_on_the_answer_box_and_in_work_in_steps_counts_once` |
| F4 | High | Revising a chooser figure loses its current attempt binding | fixed | `09380802a8`, tests `61d4bb1264` | `test_f4_revising_a_reader_figure_opened_in_practice_is_recorded_and_reveal_checked_there`, `test_f4_a_revision_names_an_attempt_host_or_none`; vitest "not right? asks the new version on the host the figure is open on now (F4)" |
| F5 | Medium | Disabling figure help does not stop pending delivery | fixed | `09380802a8`, tests `61d4bb1264` | `test_f5_switched_off_between_the_build_and_the_delivery_nothing_is_shown_or_counted`, `test_f5_an_attempt_builds_admission_key_carries_the_switch`, `test_f5_a_chooser_figure_line_switched_off_before_delivery_is_not_shown` |
| F6 | Medium | Figure help is reported as unaided continuation | fixed | `09380802a8`, tests `61d4bb1264` | `test_f6_hint_then_figure_then_check_is_more_help_not_unaided_progress`, `test_f6_a_workbench_figure_row_keeps_the_work_it_was_opened_against` |
| F7 | Medium | Diagnosis reads predictions outside the attempt being diagnosed | fixed | `b49f7df5c8` | `test_f7_the_trace_reads_only_what_this_attempt_wrote_as_it_stood_at_submit`, `test_f7_predictions_made_before_the_attempt_are_not_its_trace`, `test_232_rebuilds_figure_predictions_with_every_row_and_the_attempt_link` |
| F8 | Medium | Attempt requests suppress supported rich builds | fixed | `c131a916c3` | `test_f8_a_rich_only_build_on_the_answer_box_is_read_by_its_job_and_recorded_when_opened`, `test_f8_a_quick_figures_fuller_version_opened_on_the_attempt_is_the_same_figure`; vitest "a rich-only build shows its pending line…", "opening a quick figure's fuller version is recorded on the attempt first" |
| F9 | Medium | Ungrounded attempt figures silently lose valid predictions | fixed | `b49f7df5c8` | `test_f9_a_homeless_attempt_illustration_keeps_its_predictions_with_no_invented_home` |

Rejected: none.

## What changed, per finding

- **F1.**
  - `_attempt_host` resolves the answer box's practice session on the server with `require_owned_session`, the same acceptance boundary a hint request uses: the session exists, is open and this device owns it. A made-up session gets `not_found`, an ended one `validation_error`, and another device's `session_moved`.
  - The submission key may not already be another session's (`help_assists.submission_session_conflict`). The attach matches on the key alone and the fold also matches on the session, so a row under a second session would attach without being counted.
  - A take-step token must be a row of this item, unattached, under one of the attempt's identities (its aliases included). An answer-box token must also be in the request's session (`_token_row_matches`).
  - What remains: two genuinely open sessions on one device, where the first row of a fresh key goes to the wrong one. That is the hint service's existing trust boundary for `practice.request_hint`, and it is unchanged here.
- **F2.** `figures.help.reveal_text` reads each tier's displayed words:
  - **Manim:** `title` and `narration_md`, plus the string literals (f-string parts included) and number literals in the arguments of Manim's text and number mobjects (`Text`, `MathTex`, `Tex`, `DecimalNumber`, `Integer`, tables, braces, labelled mobjects) and of `*_label(s)`/`add_coordinates` calls. These are found by AST (`manim_shown_text`). Program structure such as class names and `Circle(radius=…)` is never read.
  - **JS animation:** the literals in `html` and `js`.
  - **Any tier:** `alt_text`.
  - **Grammar figures:** readouts, shaded areas (value and bounds), a bar chart's highlighted mass and a linear map's determinant at the defaults. They are formatted by `format_value`, a port of `FigurePanels.tsx` `formatValue`: `toPrecision(5)` then `String(Number(...))`, `toExponential(3)` and `toFixed(1)%`, with JavaScript's tie rule. `0.12345` now reads `0.12345`; before, it read `0.1235`.
  - The chooser's leak filter (`span_leaks_expected(reveal_text(row), …)`) reads the same text.
- **F3.**
  - The figure row lookup (`open_figure_rows`) takes the attempt's identity sets, from CA2's `reader.workbench.attempt_identities` via `handlers.figures.attempt_aliases`. Chain-root deduplication therefore covers every host of the attempt.
  - The take step's idempotence uses the same sets.
  - Alias resolution happens at recording time, inside the delivery's failure handling. An unreadable handoff refuses the record, so the figure is not shown.
- **F4.**
  - `reader.figure_revise` takes an optional `hostRef` and `takeStepToken`. It accepts only an attempt host, verified like a request's. With one, the revision is asked under that host: its caller and policy, the take step on a cold check, the item's own blocks refused, and the help switch.
  - The delivered version is recorded on that attempt. It is the same figure for the count (chain root) and gets its own reveal check (basis `figure:<new id>`).
  - The panel (`askFigures.tsx`) sends the host and token. Without them, the behaviour is the one before this fix: the host the figure was asked on, as it stands now.
- **F5.** The live switch is checked at every point:
  - **Build admission:** `FS.key_for` adds `figures.help_kind_enabled` to the key of an attempt-hosted build, so a build switched off midway asks nothing more.
  - **Every delivery:** `deliver_figure` and `record_attempt_figure` (and through it `figure.open`) answer `status: disabled` with no figure and no row.
  - **The chooser's prepared figure line:** `handlers.hints._deliver` checks `_figure_deliverable` before marking it shown (switch on, figure not withheld, item not cold). Otherwise it answers `not_deliverable` and the row stays unshown, so nothing is counted.
- **F6.**
  - `hints.report_workbench.WORKBENCH_HELP_KINDS` gains `figure`. A figure between a hint and the next check is now further help (`more_help`), on the one shared definition.
  - A workbench figure row keeps `step_snapshot_json`: step ids, numbers and content hashes, never text. Its own continuation therefore reads like an example's: its snapshot, and the last check before it for verdicts.
  - With the switch off, help outcomes still leave every figure row out, so RW2c's read is unchanged.
- **F7.** Migration 232 also rebuilds `figure_predictions`:
  - **The link:** a prediction made while its figure (any version in the chain) is open on an unfinished attempt gets that attempt's figure row in `assist_id` (`figures.help.open_assist_for`, derived on the server when it is recorded).
  - **The freeze:** `explained_at` is set once with the explanation. The diagnoser's trace (`diagnosis/split/figure_trace.py`) reads only the predictions linked to the attempt's own figure rows, made at or before its Submit, with "what changed?" only if written by then. A later prediction or explanation never changes an earlier attempt's trace, and one made in the Reader before the attempt is not its trace.
  - **Versions:** each version a linked prediction was made on is listed, so every delivered version (F4) has its trace association.
- **F8.**
  - On an attempt host, the build gets the rich spawner (§11.4b: every tier).
  - **Rich-only builds:** the pending line goes to the panel, which shows `RichPendingLine` with cancel. The panel reads the build by its job: `figure.open` with `richJobId` answers the line and records nothing until the figure is stored. It refuses a job of another item or one with a quick figure. Once the figure is stored it is opened and recorded like any figure: one hint-equivalent, its reveal, and the take step when cold.
  - **Quick figure with a fuller version:** the panel refreshes the fuller line through the idempotent `figure.open` of the quick figure.
  - **Expanding a fuller version:** `FiguresCtl.openFuller`, a new optional hook that the Reader's controller does not set, records the expansion first. It is the same figure for the count, with the Manim figure's own reveal (F2), and it shows only once recorded.
  - Manim rows open through the new `FS.openable_rich_figure`: shown, rich tiers on, not withheld, the author's learner state not protected now.
- **F9.**
  - `figure_predictions.extraction_id` is nullable, so a homeless illustration (grounding `none`) built on an attempt host shows its predictions and records them with no invented home, linked to the attempt's row (F7).
  - The learner-text gap path already accepts a figure with no source (its provenance lists no source for it).
  - The AD material classification gains the two new columns as values (`adaptive_difficulty/protected_tables.py`).

## Migration and head fixture

- `232_help_assist_figures.sql` (not yet landed) now rebuilds `figure_predictions` too, temp-then-rename under `foreign_keys = OFF`. No foreign key names that table. The rebuild makes `extraction_id` nullable and adds `assist_id` and `explained_at`. It recreates the explanation trigger (it also fixes `assist_id`) and adds `idx_figure_predictions_assist`.
- Table roles are unchanged: it stays RAW_LEDGER, with no new table.
- `P3_ALTERED_TABLES` and `P3_ADDED_OBJECTS` gain the new objects, so the earlier migrations' "nothing else changed" diffs know them.
- `fixtures/migration_head_232/state.sqlite` was rebuilt as follows:
  1. The source was main's exact `migration_head_230` blob at `c0017b5740`, as a backup-API scratch copy in `fixtures-local/rw5d-p3-fix/`.
  2. The revised 232 was applied under `UPGRADE_SCRATCH_COPY`.
  3. The checks: checkpoint (0, 0, 0), `journal_mode=DELETE`, header bytes 1/1, `integrity_check` ok, `foreign_key_check` empty, and 218 applied migrations (head 232).
  4. It was copied into place with the backup API. Its README records this.
- The DB reference was regenerated: `figure_predictions` and `help_assists` notes, plus the stamps. The desktop catalog was regenerated too: 303 TS / 6 Rust, ACTIVE 309.

## Gate (this step; the full suite runs once at landing)

Every pytest, vitest and npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`. pytest ran at `-n 6`, and vitest at `--maxWorkers=4`.

GATE_TABLE_PLACEHOLDER
