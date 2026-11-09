---
title: "learnloop.reader.reader_report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_report.py"
source_paths:
  - "src/learnloop/reader/reader_report.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.reader_report module"
  - "src/learnloop/reader/reader_report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.reader_report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_report` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: `learnloop reader report`: the Reader's workflow funnel (RW1a; spec §4.1, §15).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_report.py](../../../../../../src/learnloop/reader/reader_report.py) |
| Source lines | 969 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `build_reader_report(sqlite_path: Path | str, *, since: str | None=None, now: datetime | None=None, reading_paths_enabled: bool=True, figures_enabled: bool=False, figure_offers_enabled: bool=False, figure_show_me_enabled: bool=False, figure_sketch_enabled: bool=False, figure_rich_enabled: bool=False, skipped_section_los: Mapping[str, Mapping[str, Sequence[str]]] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_report.py), line 344) — Compute the report from the ledgers (pure read).

### Module constants

- `REPORT_VERSION` ([src/learnloop/reader/reader_report.py](../../../../../../src/learnloop/reader/reader_report.py), line 51)
- `OPEN_AFTER` ([src/learnloop/reader/reader_report.py](../../../../../../src/learnloop/reader/reader_report.py), line 52)
- `_ACTIVITY_KINDS` ([src/learnloop/reader/reader_report.py](../../../../../../src/learnloop/reader/reader_report.py), line 54)
- `HOLDOUT_MIN_PER_ARM` ([src/learnloop/reader/reader_report.py](../../../../../../src/learnloop/reader/reader_report.py), line 95)
- `_SKIPPED_PLANNED_LABELS` ([src/learnloop/reader/reader_report.py](../../../../../../src/learnloop/reader/reader_report.py), line 257)

### Explicit exports

`__all__` declares:

- `REPORT_VERSION`
- `build_reader_report`

## Internal implementation anchors

- `_percentiles(values: Iterable[float]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_report.py), line 64)
- `_share(count: int, of: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_report.py), line 75)
- `_payload(row: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_report.py), line 79)
- `_when(value: str | None) -> datetime | None` ([source](../../../../../../src/learnloop/reader/reader_report.py), line 87)
- `_holdout_estimate(units: list[dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_report.py), line 98) — Shown vs held-out discovered cues (Codex review F11).
- `_json_set(raw: Any) -> set[str]` ([source](../../../../../../src/learnloop/reader/reader_report.py), line 169)
- `_holdout_units(connection: Any, rows: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/reader_report.py), line 177) — One unit per (link, arm) from the shown and held-out impressions: its first exposure, its propensity, and the next attempt on its target.
- `_discovered_cues(connection: Any, in_window: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/reader_report.py), line 201) — RW3b's impressions (``reader_cue_impressions``): reasons, kinds, responses against marks shown, the share of new-application marks, and the holdout's estimate.
- `_reading_paths(connection: Any, in_window: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_report.py), line 231) — RW7a (spec §15's reading-path row): judged section labels by kind, the learner's overrides by the label they overrode ("enrichment:read_anyway", "core:skip"), and the Guide's depth choices.
- `_skipped_core(connection: Any, in_window: Any, section_los: Mapping[str, Mapping[str, Sequence[str]]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_report.py), line 260) — RW7b (spec §15's reading-path row, Codex review F4): misses on LOs whose core section was skipped.
- `_role_counts(versions: list[dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_report.py), line 320) — RW4e's proposals: one per object (its head's status), by role and confidence; every version by judge; agreement between judges.
- `_rich_tier_rows(rich_rows: Sequence[Mapping[str, Any]], tier_verdicts: Sequence[Mapping[str, Any]], actions: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_report.py), line 933) — RW5d P2b's report rows (spec §8.4: the tier mix, failures, build latency and ``why_this_tier`` by kind, so a tier doing worse is visible).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]] — imports `build_reader_report`; statically calls `build_reader_report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/figures|learnloop.db.stores.figures]] — imports `shown_verification`; calls `shown_verification`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_for_review_attempts`; calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/substrate/intervention_outcomes|learnloop.substrate.intervention_outcomes]] — imports `SUCCESS_CORRECTNESS`, `is_assisted`; calls `is_assisted`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `datetime`, `json`, `math`, `pathlib`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/rw5c_golden_source.py](../../../../../../tests/rw5c_golden_source.py) — direct import
- [tests/test_compare_sources_keep.py](../../../../../../tests/test_compare_sources_keep.py) — direct import
  - `test_the_report_counts_keeps_takes_and_relations_without_quoting`
- [tests/test_figure_offers.py](../../../../../../tests/test_figure_offers.py) — direct import
  - `test_the_reader_report_counts_offered_figures_only_while_offers_are_on`
- [tests/test_figure_predictions.py](../../../../../../tests/test_figure_predictions.py) — direct import
  - `test_the_reader_report_counts_figures_and_unsupported_kinds`
- [tests/test_figure_rich_job.py](../../../../../../tests/test_figure_rich_job.py) — direct import
  - `test_the_report_shows_the_rich_tier_rows`
- [tests/test_figures_final_round.py](../../../../../../tests/test_figures_final_round.py) — direct import
  - `test_the_report_counts_a_legacy_verified_as_an_illustration`
- [tests/test_figures_prefetch.py](../../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_the_report_block_appears_only_with_the_switch`
- [tests/test_figures_show_me.py](../../../../../../tests/test_figures_show_me.py) — direct import
  - `test_the_reader_report_counts_show_me_without_the_words`
- [tests/test_figures_switch_off.py](../../../../../../tests/test_figures_switch_off.py) — direct import
- [tests/test_library_ask.py](../../../../../../tests/test_library_ask.py) — direct import
  - `test_the_reader_report_counts_library_asks_without_their_words`
- [tests/test_reader_cues.py](../../../../../../tests/test_reader_cues.py) — direct import
  - `test_the_report_counts_marks_shown_taps_and_choices_against_marks_shown`
- [tests/test_reader_cues_cli_report.py](../../../../../../tests/test_reader_cues_cli_report.py) — direct import
  - `test_the_holdout_estimate_weights_by_propensity_and_leaves_other_suppressions_out`
  - `test_the_report_counts_discovered_impressions_only_once_there_are_some`
- [tests/test_reader_intent.py](../../../../../../tests/test_reader_intent.py) — direct import
  - `test_the_report_counts_used_routings_and_corrections_on_them_only`
- [tests/test_reader_report.py](../../../../../../tests/test_reader_report.py) — direct import
  - `test_a_detour_returned_to_again_counts_once_so_the_rate_never_exceeds_one`
  - `test_a_return_whose_opening_is_outside_the_window_is_not_counted`
  - `test_since_narrows_the_window`
  - `test_the_funnel_reports_workflows_with_denominators`
  - `test_the_passage_quick_check_is_a_model_backed_action_in_the_funnel`
  - `test_the_report_carries_no_learner_text`
  - `test_transcript_inquiries_count_like_any_other`
- [tests/test_reader_rw1b_review.py](../../../../../../tests/test_reader_rw1b_review.py) — direct import
  - `test_f12_an_enter_only_use_and_its_correction_are_counted`
- [tests/test_reader_rw3b_fix_round4.py](../../../../../../tests/test_reader_rw3b_fix_round4.py) — direct import
  - `test_shared_outcome_attempts_withhold_the_interval_and_say_why`
  - `test_without_shared_outcomes_the_interval_is_kept`
- [tests/test_reader_rw3b_review_fixes.py](../../../../../../tests/test_reader_rw3b_review_fixes.py) — direct import
  - `test_repeated_visits_never_manufacture_samples`
  - `test_the_report_counts_one_unit_per_link_and_matches_the_targets_facets`
- [tests/test_reader_tutor_offers.py](../../../../../../tests/test_reader_tutor_offers.py) — direct import
  - `test_a_press_is_a_salience_only_reader_event_counted_by_the_report`
  - `test_the_report_counts_modes_abstentions_and_follow_ons`
- [tests/test_reading_paths.py](../../../../../../tests/test_reading_paths.py) — direct import
  - `test_fix_switched_off_the_reader_report_is_a76c8358a`
  - `test_the_reader_report_counts_labels_overrides_and_depth_choices`
- [tests/test_rw7b_codex_review_fixes.py](../../../../../../tests/test_rw7b_codex_review_fixes.py) — direct import
  - `test_f4_the_report_without_the_adapter_and_with_the_guide_off_is_as_before`
- [tests/test_sketch_service.py](../../../../../../tests/test_sketch_service.py) — direct import
  - `test_the_report_counts_tiers_verdicts_and_reasons`
- [tests/test_source_roles.py](../../../../../../tests/test_source_roles.py) — direct import
  - `test_the_reader_report_counts_proposals_by_role_judge_and_agreement`

## Modification guidance

- Change reader report policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_report.py](../../../../../../src/learnloop/reader/reader_report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
