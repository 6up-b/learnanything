---
title: "learnloop.db.stores.figures"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/figures.py"
source_paths:
  - "src/learnloop/db/stores/figures.py"
source_commit: "18e1b00c392cd1b2aba022d40f8a35b4fddef20f"
source_commit_timestamp: "2026-11-02T19:33:12-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.figures module"
  - "src/learnloop/db/stores/figures.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.figures`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.figures` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Reader workbench RW5a: ``interactive_figures`` and ``figure_predictions`` (migration 216); Reader RW5d P1: ``figure_requests`` and the rebuilt ``interactive_figures`` (migration 224).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/figures.py](../../../../../../../src/learnloop/db/stores/figures.py) |
| Source lines | 412 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `18e1b00c392cd1b2aba022d40f8a35b4fddef20f` |
| Commit timestamp | `2026-11-02T19:33:12-05:00` |

## Public API

- `shown_verification(verification: str | None) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 47) — A stored verification as RW5a shows and counts it: ``verified`` (never written by RW5a or RW5c, whose result is its own ledger's) is an illustration.
- `insert_source_check(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 62) — One ``figure_source_checks`` row (RAW_LEDGER, append-only by trigger), in the caller's transaction, with its judgment.
- `has_source_checks(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 89)
- `latest_source_check(connection: sqlite3.Connection, figure_id: str, certification_version: int) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 94) — The newest check of a figure at this certification version (the shown state, §10.2).
- `source_checks(connection: sqlite3.Connection, figure_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 106) — Every check of a figure, oldest first.
- `latest_source_checks(connection: sqlite3.Connection, certification_version: int) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 116) — The newest check of each figure at this certification version (the report, §12).
- `has_tables(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 129)
- `insert_figure(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 136)
- `figure(connection: sqlite3.Connection, figure_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 169)
- `insert_request(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 174) — One ``figure_requests`` row (RW5d): what was asked, before the figure.
- `set_request_figure(connection: sqlite3.Connection, request_id: str, figure_id: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 196) — Name the figure a request built or reused, once (the trigger refuses any other update).
- `request(connection: sqlite3.Connection, request_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 217)
- `requests(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 222) — Every figure request, oldest first (the Reader report's show-me block).
- `figures_for_extraction(connection: sqlite3.Connection, extraction_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 230)
- `shown_figures(connection: sqlite3.Connection, spec_versions: tuple[str, ...], *, limit: int) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 237) — Reader RW5d P3: the newest shown figures of the given spec versions (a quick figure's own row, never a fuller version's), newest first, at most ``limit``: what the hint chooser's ``explore_figure`` precondition scans (the figure help module checks each).
- `reusable(connection: sqlite3.Connection, input_hash: str, spec_version: str | tuple[str, ...]) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 260) — The newest figure built from the same input under the same spec version(s) that is shown or recorded as unsupported (a failed build is retried, so it is never reused).
- `latest_for_input(connection: sqlite3.Connection, input_hash: str, spec_version: str | tuple[str, ...]) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 274) — The newest figure stored for this input under this spec version, whatever its verification.
- `builds_for_input(connection: sqlite3.Connection, input_hash: str, spec_version: str | tuple[str, ...]) -> int` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 285) — How many figures were stored for this input: a build's retry generation (a stored failure starts the next one; a crash before the row does not).
- `fuller_rows(connection: sqlite3.Connection, figure_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 295) — RW5d P2b: the rich figures stored as the fuller version of ``figure_id``, oldest first.
- `superseding(connection: sqlite3.Connection, figure_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 304)
- `insert_prediction(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 311)
- `prediction(connection: sqlite3.Connection, prediction_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 330)
- `prediction_for(connection: sqlite3.Connection, figure_id: str, index: int) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 335)
- `predictions_for_figure(connection: sqlite3.Connection, figure_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 341)
- `set_explanation(connection: sqlite3.Connection, prediction_id: str, text: str, *, at: str | None=None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 348) — Set "what changed?" once, with when (``explained_at``, RW5d P3); False when it was already set (the trigger refuses any other update).
- `missed_prediction_ids(connection: sqlite3.Connection) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 359) — Every missed prediction with an answer, oldest first (the formative backlog).
- `figure_verdicts(connection: sqlite3.Connection, task: str, figure_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 369) — RW5d P2 (Codex review F8): a figure's ``judgment_ledger`` verdicts for one task in the order they were appended (the build's, then any engine re-verification).

### Module constants

- `FIGURE_COLUMNS` ([src/learnloop/db/stores/figures.py](../../../../../../../src/learnloop/db/stores/figures.py), line 20)
- `REQUEST_COLUMNS` ([src/learnloop/db/stores/figures.py](../../../../../../../src/learnloop/db/stores/figures.py), line 31)
- `PREDICTION_COLUMNS` ([src/learnloop/db/stores/figures.py](../../../../../../../src/learnloop/db/stores/figures.py), line 34)
- `SHOWN` ([src/learnloop/db/stores/figures.py](../../../../../../../src/learnloop/db/stores/figures.py), line 40)
- `VERIFIED_RW5C` ([src/learnloop/db/stores/figures.py](../../../../../../../src/learnloop/db/stores/figures.py), line 44)
- `SOURCE_CHECK_COLUMNS` ([src/learnloop/db/stores/figures.py](../../../../../../../src/learnloop/db/stores/figures.py), line 57)

### Explicit exports

`__all__` declares:

- `SOURCE_CHECK_COLUMNS`
- `has_source_checks`
- `insert_source_check`
- `latest_source_check`
- `latest_source_checks`
- `source_checks`
- `FIGURE_COLUMNS`
- `PREDICTION_COLUMNS`
- `REQUEST_COLUMNS`
- `SHOWN`
- `VERIFIED_RW5C`
- `shown_verification`
- `builds_for_input`
- `figure`
- `figure_verdicts`
- `figures_for_extraction`
- `shown_figures`
- `has_tables`
- `insert_figure`
- `insert_prediction`
- `insert_request`
- `request`
- `requests`
- `set_request_figure`
- `latest_for_input`
- `missed_prediction_ids`
- `prediction`
- `prediction_for`
- `predictions_for_figure`
- `reusable`
- `set_explanation`
- `superseding`

## Internal implementation anchors

- `_source_check(row: sqlite3.Row | tuple | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 79)
- `_figure(row: sqlite3.Row | tuple | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 155)
- `_request(row: sqlite3.Row | tuple | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 204)
- `_versions(spec_version: str | tuple[str, ...]) -> tuple[tuple[str, ...], str]` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 252) — RW5d P2: one input may be answered under either spec version (a grammar spec or a sketch), so lookups take one version or several.
- `_prediction(row: sqlite3.Row | tuple | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/figures.py), line 321)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]] — imports `module`; statically calls `has_tables`, `shown_figures`
- [[Reference/Modules/learnloop/figures/labels|learnloop.figures.labels]] — imports `VERIFIED_RW5C`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `SHOWN`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `module`; statically calls `has_tables`, `insert_figure`, `request`, `reusable`, `set_request_figure`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; statically calls `builds_for_input`, `figure`, `figure_verdicts`, `figures_for_extraction`, `fuller_rows`, `has_tables`, `insert_figure`, `insert_prediction`, `insert_request`, `latest_for_input`, `prediction`, `prediction_for`, `predictions_for_figure`, `request`, `reusable`, `set_explanation`, `set_request_figure`, `shown_verification`
- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `module`; statically calls `figure_verdicts`, `has_source_checks`, `insert_source_check`, `latest_source_check`, `latest_source_checks`, `shown_figures`
- [[Reference/Modules/learnloop/reader/reader_report|learnloop.reader.reader_report]] — imports `shown_verification`; statically calls `shown_verification`
- [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]] — imports `module`; statically calls `figure`, `has_tables`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `module`; statically calls `figure`, `has_tables`, `superseding`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `module`; statically calls `figure`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]], [[Reference/Modules/learnloop/figures/labels|learnloop.figures.labels]], [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]], [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_rich_rereview_fixes.py](../../../../../../../tests/test_figure_rich_rereview_fixes.py) — direct import
- [tests/test_figure_rich_review_fixes.py](../../../../../../../tests/test_figure_rich_review_fixes.py) — direct import
- [tests/test_figures_codex_review.py](../../../../../../../tests/test_figures_codex_review.py) — direct import
  - `test_f7_a_paid_answer_survives_a_crash_before_the_row`
- [tests/test_figures_fix_round2.py](../../../../../../../tests/test_figures_fix_round2.py) — direct import
  - `test_f7_a_build_committed_between_the_reads_is_reused_inside_the_lock`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
- [tests/test_figures_show_me_codex_review.py](../../../../../../../tests/test_figures_show_me_codex_review.py) — direct import
  - `test_f7_a_reuse_whose_request_cannot_be_recorded_fails_retryably_and_the_retry_reuses`
- [tests/test_followups_batch7_prefetch_capped_resume.py](../../../../../../../tests/test_followups_batch7_prefetch_capped_resume.py) — direct import
- [tests/test_followups_nov2_figure_provenance.py](../../../../../../../tests/test_followups_nov2_figure_provenance.py) — direct import
  - `test_a_fresh_figure_for_a_marked_row_is_reused_after_the_panels_are_switched`
  - `test_a_lesson_figure_keeps_its_record_and_is_rechecked_by_its_learner_inputs`
  - `test_a_press_of_the_same_input_never_backfills_the_marked_row_and_builds_afresh`
  - `test_a_revision_inherits_its_bases_learner_state_protection`
  - `test_a_rich_revision_with_nothing_inherited_carries_no_record`
- [tests/test_help_assist_figures_migration.py](../../../../../../../tests/test_help_assist_figures_migration.py) — direct import
  - `test_232_rebuilds_figure_predictions_with_every_row_and_the_attempt_link`
- [tests/test_learner_data_relax_2.py](../../../../../../../tests/test_learner_data_relax_2.py) — direct import
- [tests/test_reader_rw5d_p4a_figures_follow.py](../../../../../../../tests/test_reader_rw5d_p4a_figures_follow.py) — direct import
  - `test_the_quiet_read_never_reverifies_an_outdated_sketch_or_writes`
- [tests/test_rw5c_judgments.py](../../../../../../../tests/test_rw5c_judgments.py) — direct import
  - `test_a_failure_between_the_two_inserts_leaves_neither`
  - `test_a_recheck_supersedes_the_previous_verdict_of_the_same_figure`
  - `test_at_build_a_failure_leaves_no_figure_row_and_no_verdict`
- [tests/test_rw5c_recheck.py](../../../../../../../tests/test_rw5c_recheck.py) — direct import
  - `test_a_certification_bump_rechecks_at_no_paid_cost`
  - `test_a_difference_found_at_recheck_gives_the_failed_state_with_rebuild`
  - `test_a_prebuilt_figure_nobody_pressed_for_that_differs_lists_nothing`
  - `test_a_recheck_with_the_switch_off_or_turned_off_before_its_write_writes_nothing`
  - `test_pressing_rebuild_calls_the_author_and_stores_a_new_version`
  - `test_rebuild_is_not_offered_with_revisions_off`
  - `test_section_figures_leave_a_rejected_figure_out`
- [tests/test_rw5c_switch_off.py](../../../../../../../tests/test_rw5c_switch_off.py) — direct import
  - `test_a_row_written_just_before_a_switch_off_is_never_shown_while_it_is_off`
  - `test_nothing_reads_the_ledger_while_the_switch_is_off`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/figures.py](../../../../../../../src/learnloop/db/stores/figures.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
