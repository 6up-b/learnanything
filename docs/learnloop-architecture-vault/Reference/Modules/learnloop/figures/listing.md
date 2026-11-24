---
title: "learnloop.figures.listing"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/listing.py"
source_paths:
  - "src/learnloop/figures/listing.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.figures"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.figures.listing module"
  - "src/learnloop/figures/listing.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.listing`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.listing` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Which stored figures a source lists now, and the lines for builds still under way.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/listing.py](../../../../../../src/learnloop/figures/listing.py) |
| Source lines | 503 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `prefetch_pending(vault: Any, repository: Repository, extraction_id: str, *, pass_running: bool=False) -> bool` ([source](../../../../../../src/learnloop/figures/listing.py), line 166) — RW5d P5 (Codex review F11): whether a prebuild for this source is coming now: the Reader then reads its figures again, paced, so a completed prebuild appears without a reopen.
- `prefetch_plan_waits(vault: Any, repository: Repository, extraction_id: str | None, *, request_ids: Collection[str] | None=None, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/figures/listing.py), line 209) — RW5d P5 (Codex re-review F17): this source's speculative prebuild rich jobs waiting for the plan, newest per input, whose retry is admissible now: figures ahead of need on, this machine on mains, and the passage not held out.
- `list_figures(vault: Any, repository: Repository, extraction_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/listing.py), line 261) — The figures of one source as the Reader shows them: per version chain, the newest shown version (else the newest failed or unsupported one), of the current spec version, and never one whose passage is held out now.
- `section_figures(vault: Any, repository: Repository, extraction_id: str, section_of: Callable[[str], str | None]) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/figures/listing.py), line 279) — RW5d P4a (spec §10.2): the kept figures of one reading by the section their anchor is in, for the correspondents read (figures follow the section).
- `rich_pending(vault: Any, repository: Repository, extraction_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/listing.py), line 339) — RW5d P2b (spec §6.8): the rich builds with no quick figure for this source that have not ended (pending, or waiting for the plan), each as the pending line under its passage; empty while the rich tiers are off.
- `shown_figure(vault: Any, repository: Repository, figure_id: str) -> tuple[dict[str, Any], Any]` ([source](../../../../../../src/learnloop/figures/listing.py), line 461) — A figure that may be shown now: shown verification, a current spec version, its passage not held out.

### Explicit exports

`__all__` declares:

- `list_figures`
- `prefetch_pending`
- `prefetch_plan_waits`
- `rich_pending`
- `section_figures`
- `shown_figure`

## Internal implementation anchors

- `_root(rows_by_id: Mapping[str, Mapping[str, Any]], row: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/figures/listing.py), line 53)
- `_listed(vault: Any, repository: Repository, extraction_id: str, withheld: list[str] | None=None) -> list[tuple[Mapping[str, Any], int, list[dict[str, Any] | None]]]` ([source](../../../../../../src/learnloop/figures/listing.py), line 62) — The rows :func:`list_figures` presents, with no presentation (RW5d P4a, Codex review F3): per version chain, the pick, the chain's length and its placements in this source.
- `_prebuilt_within_budget(vault: Any, repository: Repository, extraction_id: str, picks: list[tuple[Mapping[str, Any], int, list[dict[str, Any] | None]]]) -> list[tuple[Mapping[str, Any], int, list[dict[str, Any] | None]]]` ([source](../../../../../../src/learnloop/figures/listing.py), line 111) — RW5d P5 (spec §6.9; Codex review F11): a prebuilt figure nobody pressed for takes its place in the Reader's cue budget (``[cues] density``, per section; cues off: none), the earliest built first; once pressed it is the learner's like any figure (never cut).
- `_prebuilt_listed(vault: Any, repository: Repository, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/listing.py), line 152) — RW5d P5: a prebuilt figure lists while figures ahead of need are on, or once a pressed request took it (then it is the learner's like any figure).
- `_rich_line(request: FigureRequest, job: Mapping[str, Any], state: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/listing.py), line 327)
- `_failed_correction(payload: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/figures/listing.py), line 437) — Codex re-review F14: the failure a correction job stored (its request's row, ``failed``) while it is still the newest version of the figure it corrects: nothing supersedes it and no later correction of that figure was stored.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/build|learnloop.figures.build]] — imports `_failed_correction`, `_rich_line`; statically calls `_failed_correction`, `_rich_line`
- [[Reference/Modules/learnloop/figures/predictions|learnloop.figures.predictions]] — imports `shown_figure`; statically calls `shown_figure`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `prefetch_plan_waits`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `module`; statically calls `section_figures`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `module`; statically calls `list_figures`, `prefetch_pending`, `prefetch_plan_waits`, `rich_pending`, `shown_figure`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/figures|learnloop.db.stores.figures]] — imports `module`; calls `figure`, `figures_for_extraction`, `has_tables`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `figures_enabled`, `rich_tiers_enabled`; calls `figures_enabled`, `rich_tiers_enabled`
- [[Reference/Modules/learnloop/figures/power|learnloop.figures.power]] — imports `power_state`, `prefetch_switch`; calls `power_state`, `prefetch_switch`
- [[Reference/Modules/learnloop/figures/prefetch_ledger|learnloop.figures.prefetch_ledger]] — imports `module`; calls `capacity_left`
- [[Reference/Modules/learnloop/figures/protection|learnloop.figures.protection]] — imports `_withheld`, `figure_homes`, `item_passages`, `rich_base_keys`, `row_withheld`, `show_me_row`; calls `_withheld`, `figure_homes`, `item_passages`, `rich_base_keys`, `row_withheld`, `show_me_row`
- [[Reference/Modules/learnloop/figures/records|learnloop.figures.records]] — imports `module`; calls `write_withheld_once`
- [[Reference/Modules/learnloop/figures/request|learnloop.figures.request]] — imports `FigureRefused`, `FigureRequest`; calls `FigureRefused`, `FigureRequest`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `module`; calls `job_state`, `rich_job_for_figure`, `rich_job_for_request`, `rich_jobs`
- [[Reference/Modules/learnloop/figures/sketch|learnloop.figures.sketch]] — imports `module`; calls `parse_sketch`
- [[Reference/Modules/learnloop/figures/spec|learnloop.figures.spec]] — imports `ALL_SPEC_VERSIONS`, `RICH_SPEC_VERSIONS`, `SPEC_VERSIONS`, `module`; calls `parse_spec`
- [[Reference/Modules/learnloop/figures/view|learnloop.figures.view]] — imports `SKETCH_OFF_KIND`, `_anchor_span`, `_figure_request`, `_label`, `_prebuilt_pressed`, `_presented_row`, `available_row`, `drawable_now`, `figure_view`, `sketch_rechecked`, `sketch_row`, `source_rejected`; calls `_anchor_span`, `_figure_request`, `_label`, `_prebuilt_pressed`, `_presented_row`, `available_row`, `drawable_now`, `figure_view`, `sketch_rechecked`, `sketch_row`, `source_rejected`
- [[Reference/Modules/learnloop/reader/reader_cues|learnloop.reader.reader_cues]] — imports `cue_density`, `cues_enabled`, `density_budget`; calls `cue_density`, `cues_enabled`, `density_budget`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `extraction_sections`; calls `extraction_sections`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/build|learnloop.figures.build]], [[Reference/Modules/learnloop/figures/predictions|learnloop.figures.predictions]], [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]], [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/figure_rich_job_helpers.py](../../../../../../tests/figure_rich_job_helpers.py) — direct import
- [tests/test_figure_label_wording.py](../../../../../../tests/test_figure_label_wording.py) — direct import
  - `test_f3_a_stored_label_like_sketch_is_presented_without_that_text`
  - `test_f3_a_stored_label_like_spec_is_presented_without_that_text_listed_and_reused`
- [tests/test_figure_request_records.py](../../../../../../tests/test_figure_request_records.py) — direct import
  - `test_a_listed_chain_whose_pick_is_withheld_is_recorded_once_per_figure`
  - `test_a_listed_figure_whose_spec_no_longer_parses_is_recorded_once`
- [tests/test_figure_rich_failed_correction_durable.py](../../../../../../tests/test_figure_rich_failed_correction_durable.py) — direct import
  - `test_codex_f4_a_newer_cancelled_correction_still_speaks_for_the_figure_after_500_newer_rich_jobs`
  - `test_r1_a_failed_correction_of_a_fuller_version_outside_the_window_says_so_too`
  - `test_r1_a_failed_correction_outside_the_job_window_still_says_so`
  - `test_r1_a_newer_correction_in_the_window_still_speaks_for_the_figure`
  - `test_r1_a_replaced_failed_correction_lists_nothing_outside_the_window`
- [tests/test_figure_rich_job.py](../../../../../../tests/test_figure_rich_job.py) — direct import
  - `test_rich_only_shows_the_pending_line_and_never_asks_twice`
- [tests/test_figure_rich_rereview_fixes.py](../../../../../../tests/test_figure_rich_rereview_fixes.py) — direct import
  - `test_a_failed_animation_correction_keeps_the_earlier_version_and_says_so`
  - `test_a_failed_correction_of_a_fuller_version_says_so_too`
  - `test_a_later_correction_replaces_the_failed_line`
- [tests/test_figure_rich_review_fixes.py](../../../../../../tests/test_figure_rich_review_fixes.py) — direct import
  - `test_a_cancelled_rich_only_build_leaves_no_line_and_cannot_be_retried`
  - `test_a_stored_rich_only_failure_lists_once`
  - `test_an_interrupted_rich_only_build_stays_as_a_failed_line_and_can_be_tried_again`
- [tests/test_figures_prefetch.py](../../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_a_prebuilt_figure_lists_only_while_on_or_once_pressed`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f10_a_rich_only_prebuild_shows_no_pending_or_failure_line`
  - `test_f11_unpressed_prebuilt_lines_keep_to_the_cue_budget`
  - `test_f17_a_plan_wait_is_not_retried_off_mains_or_switched_off`
  - `test_f17_a_speculative_prebuilds_plan_wait_is_retried_by_the_reader_read`
  - `test_f18_a_prebuilds_rich_job_is_pending_on_mains_only`
  - `test_f18_an_unstarted_decision_is_pending_only_while_a_pass_runs_and_never_on_battery`
- [tests/test_followups_batch6_prefetch_plan_wait.py](../../../../../../tests/test_followups_batch6_prefetch_plan_wait.py) — direct import
  - `test_the_runtime_wires_the_paced_requeue`
- [tests/test_followups_batch6_review_fixes.py](../../../../../../tests/test_followups_batch6_review_fixes.py) — direct import
  - `test_f1_the_readers_read_never_requeues_it_either`
  - `test_f1_the_worker_rechecks_before_the_store`
  - `test_f1_the_worker_stops_a_requeued_prebuild_before_any_request`
- [tests/test_followups_batch6_verify_fixes.py](../../../../../../tests/test_followups_batch6_verify_fixes.py) — direct import
  - `test_v1_an_answered_planned_item_lets_the_retry_through`
  - `test_v1_an_unreadable_stored_plan_fails_closed_everywhere`
  - `test_v1_only_todays_plan_holds_an_item`
  - `test_v1_the_reader_and_the_pass_read_the_same_rule`
  - `test_v1_the_readers_read_never_requeues_a_prebuild_a_later_plan_holds`
  - `test_v1_the_worker_rechecks_the_plan_before_the_store`
  - `test_v1_the_worker_stops_a_requeued_prebuild_a_later_plan_holds_before_any_request`
- [tests/test_followups_batch7_prefetch_capped_resume.py](../../../../../../tests/test_followups_batch7_prefetch_capped_resume.py) — direct import
  - `test_a_capped_decision_is_coming_only_while_the_budget_has_room`
- [tests/test_followups_nov2_figure_provenance.py](../../../../../../tests/test_followups_nov2_figure_provenance.py) — direct import
  - `test_a_marked_quick_figure_with_no_record_is_withheld`
  - `test_a_press_of_the_same_input_never_backfills_the_marked_row_and_builds_afresh`
  - `test_a_quick_figure_whose_learner_inputs_became_protected_is_not_presented`
- [tests/test_rw5c_recheck.py](../../../../../../tests/test_rw5c_recheck.py) — direct import
  - `test_a_difference_found_at_recheck_gives_the_failed_state_with_rebuild`
  - `test_section_figures_leave_a_rejected_figure_out`

## Modification guidance

- Make changes here when the responsibility remains listing within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/listing.py](../../../../../../src/learnloop/figures/listing.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
