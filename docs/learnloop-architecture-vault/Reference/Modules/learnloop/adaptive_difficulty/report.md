---
title: "learnloop.adaptive_difficulty.report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/report.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/report.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.report module"
  - "src/learnloop/adaptive_difficulty/report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.report` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: The AD report (``learnloop ad report``; spec_adaptive_difficulty_v1 §10.4, §5.8, §5.9, §7.4, §9.6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/report.py](../../../../../../src/learnloop/adaptive_difficulty/report.py) |
| Source lines | 796 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `arm_scores(records: Sequence[A.Record], arm: str, split: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 74)
- `feature_time_correlation(points: Sequence[Mapping[str, Any] | None]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 140) — §5.8's first diagnostic: per dimension, the correlation between the served feature level and time (the order served); ``confounded`` when ``|r| > 0.6``.
- `aliased_coordinates(posterior: np.ndarray, prior_variances: Sequence[float], names: Sequence[str]) -> set[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 160) — §5.8's aliased directions: eigenvectors of the data's contribution to the posterior precision of ``(β, α)``, in prior-sd units, with eigenvalue below 5% of the prior precision; the coordinates loading on them (``|v| > 0.5``) are "prior-dependent".
- `readiness_errors(records: Sequence[A.Record], selection_times: Sequence[str], *, every: int=REPORT_EVERY_SELECTIONS) -> list[float | None]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 538) — The band-region error of ``@subject`` at each report, oldest first (Codex review F8).
- `density_lowerings(connection: Any, *, view: Any) -> list[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 561) — When the learner lowered the cue density within a visit after an extra offer (§10.4, F8).
- `build(vault: Any, repository: Any, connection: Any, *, arms: Sequence[str]=A.DEFAULT_ARMS, previous_errors: Sequence[float | None] | None=None, sensitivity: bool=True, now: str | None=None, report_every: int=REPORT_EVERY_SELECTIONS) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 621) — The whole report (a pure read; zero model calls).
- `render_markdown(report: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 763) — A plain rendering for the owner (the JSON is the record).

### Module constants

- `REPORT_VERSION` ([src/learnloop/adaptive_difficulty/report.py](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 54)
- `HONEST_STATEMENT` ([src/learnloop/adaptive_difficulty/report.py](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 55)
- `SPLITS` ([src/learnloop/adaptive_difficulty/report.py](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 63)
- `COMPARISONS` ([src/learnloop/adaptive_difficulty/report.py](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 64)
- `LESSON_COMPARISON` ([src/learnloop/adaptive_difficulty/report.py](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 70)
- `FAST_TRACK_Q` ([src/learnloop/adaptive_difficulty/report.py](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 71)
- `CONFOUNDED_R` ([src/learnloop/adaptive_difficulty/report.py](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 136)
- `ALIASED_SHARE` ([src/learnloop/adaptive_difficulty/report.py](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 137)
- `REPORT_EVERY_SELECTIONS` ([src/learnloop/adaptive_difficulty/report.py](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 533)
- `CUE_DENSITIES` ([src/learnloop/adaptive_difficulty/report.py](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 535)

### Explicit exports

`__all__` declares:

- `HONEST_STATEMENT`
- `REPORT_EVERY_SELECTIONS`
- `REPORT_VERSION`
- `SPLITS`
- `aliased_coordinates`
- `arm_scores`
- `build`
- `density_lowerings`
- `feature_time_correlation`
- `readiness_errors`
- `render_markdown`

## Internal implementation anchors

- `_arm_names(records: Sequence[A.Record]) -> list[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 89)
- `_field_rule(records: Sequence[A.Record], challenger: str, comparator: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 96)
- `_flags_and_lines(records: Sequence[A.Record], previous_errors: Sequence[float | None], *, selected_outcomes: Sequence[float], delivered: Sequence[Mapping[str, Any]], lowerings: Sequence[str], now: str, lessons: bool=False) -> tuple[list[dict[str, Any]], list[str]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 112)
- `_identifiability(snapshot: RP.Snapshot, records: Sequence[A.Record]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 178)
- `_sensitivity(vault: Any, repository: Any, connection: Any, snapshot: RP.Snapshot, selections: Sequence[Mapping[str, Any]], *, view: Any, limit: int=50) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 217) — Each β prior mean shifted ±1 sd: how many of the latest serve draws' modes or near-tie sets change (re-scored on the current state; a bounded check, §5.8).
- `_selection_stats(connection: Any, snapshot: RP.Snapshot, *, view: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 259) — The selection and commission cohorts, read through the material view (Codex verify F29): a commission result on a withheld item or revision is not counted, and with the predicate unavailable the section is suppressed (no draw, result or outcome is read).
- `_trivial_success(connection: Any, snapshot: RP.Snapshot) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 320) — §9.6: the share of successes on items whose p̄ at serve exceeded 0.95 (``ad_threshold@subject``).
- `_visits(connection: Any, snapshot: RP.Snapshot, *, view: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 338) — Reader visits with their active minutes (a cost, read as the Reader report reads it) and the count of each kind of opportunity inside them.
- `_delayed_exposures(connection: Any, snapshot: RP.Snapshot, *, view: Any) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 371) — Each LO's exposure and practice times for the shared delayed definition, read through the view: its attempts and reveals (the warmth rule's own), its reading receipts and LO-linked source exposures (the same two the router's ledger reads; a capped second passage view has only th…
- `_offer_outcomes(connection: Any, snapshot: RP.Snapshot, *, view: Any, delayed_definition: bool=False) -> dict[str, list[DR.OfferOutcome]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 399) — Each dose draw's matured cold outcome (§5.12): the first graded attempt on an item of one of the section's LOs at least one day after the decision, with no reveal of that item in between.
- `_dose_arm(connection: Any, *, view: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 462) — The dose arm's draws and uptake through the material view (Codex verify F29).
- `_self_check(records: Sequence[A.Record]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 481)
- `_lesson_inputs(snapshot: RP.Snapshot, records: Sequence[A.Record]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 497) — Teacher TE3a: what the dose report's lesson row is computed from: the lesson opportunities the replay applied, by subkind, and the first attempts after a lesson with their realized and predicted success.
- `_median_doses(records: Sequence[A.Record]) -> dict[str, float]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 515)
- `_answer_minutes(connection: Any, *, view: Any) -> float | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 523) — The median minutes of the practice cohort (Codex verify F27): visible, graded practice answers with a recorded latency (``MaterialView.practice_minutes``); a withheld item's answer, a skip or a self-report never counts, and an unavailable predicate counts nothing.
- `_history(vault: Any, repository: Any, connection: Any, now: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 703)
- `_history_lines(history: Mapping[str, Any] | None) -> list[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 714) — RO2's block, plainly: each comparison's mean paired log-loss difference and its interval.
- `_guard_lines(guard: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/report.py), line 740) — The guard block's lines: the live log's count (since the last upgrade once one has archived a log; "so far" before), by entry point, and the archives' total.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/ad|learnloop.cli.ad]] — imports `SPLITS`, `arm_scores`, `build`, `render_markdown`; statically calls `arm_scores`, `build`, `render_markdown`
- [[Reference/Modules/learnloop/sim/ad_synthetic|learnloop.sim.ad_synthetic]] — imports `aliased_coordinates`, `feature_time_correlation`; statically calls `aliased_coordinates`, `feature_time_correlation`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]] — imports `module`; calls `prequential`
- [[Reference/Modules/learnloop/adaptive_difficulty/denial_log|learnloop.adaptive_difficulty.denial_log]] — imports `module`; calls `summary`
- [[Reference/Modules/learnloop/adaptive_difficulty/dose_report|learnloop.adaptive_difficulty.dose_report]] — imports `module`; calls `OfferOutcome`, `analyse`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `current_view`; calls `current_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/monitoring|learnloop.adaptive_difficulty.monitoring]] — imports `module`; calls `band_missed_flag`, `band_region_error`, `bootstrap_interval`, `comparison_flag`, `confidence_sequence`, `difference_terms`, `dose_burden_flag`, `honest_line`, `log_loss`, `readiness_flag`, `reliability`, `verdict`, `wilson`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `entry`; calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/predict|learnloop.adaptive_difficulty.predict]] — imports `module`; calls `current_spec`, `score`
- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `module`; calls `versions`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; calls `run`
- [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]] — imports `history_report`; calls `history_report`
- [[Reference/Modules/learnloop/adaptive_difficulty/selection|learnloop.adaptive_difficulty.selection]] — imports `module`; calls `constants_from_config`, `feature_level`, `point_key`, `propensities`
- [[Reference/Modules/learnloop/adaptive_difficulty/switches|learnloop.adaptive_difficulty.switches]] — imports `LLM_HISTORY`, `outside_forecasters`; calls `outside_forecasters`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/data_capture/gates|learnloop.data_capture.gates]] — imports `serving_on`; calls `serving_on`
- [[Reference/Modules/learnloop/db/stores/ad_serving|learnloop.db.stores.ad_serving]] — imports `module`; calls `has_table`
- [[Reference/Modules/learnloop/delayed_completion|learnloop.delayed_completion]] — imports `module`; calls `Presentation`, `classify`, `last_before`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `json`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/ad|learnloop.cli.ad]], [[Reference/Modules/learnloop/sim/ad_synthetic|learnloop.sim.ad_synthetic]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_contract_helpers.py](../../../../../../tests/ad23_contract_helpers.py) — direct import
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
  - `test_withheld_dose_offers_neither_spend_the_budget_nor_count_as_taken`
- [tests/test_ad23_fix_r5.py](../../../../../../tests/test_ad23_fix_r5.py) — direct import
  - `test_an_item_that_lands_after_expiry_gets_a_marked_receipt_and_a_later_draw_owns_later_items`
  - `test_the_report_forecasts_with_the_configured_coupling`
- [tests/test_ad23_fix_r7.py](../../../../../../tests/test_ad23_fix_r7.py) — direct import
  - `test_features_match_reads_the_audited_features_the_receipt_records`
- [tests/test_ad23_fix_r8.py](../../../../../../tests/test_ad23_fix_r8.py) — direct import
  - `test_practice_minutes_come_from_the_visible_practice_cohort`
  - `test_report_sensitivity_never_re_forecasts_a_withheld_item`
  - `test_with_the_predicate_unavailable_the_report_discloses_zero_observations`
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_density_lowerings_join_offers_to_their_visits`
  - `test_readiness_errors_read_each_report_window`
  - `test_repeated_reports_fire_the_readiness_flag_through_build`
- [tests/test_ad3_monitoring.py](../../../../../../tests/test_ad3_monitoring.py) — direct import
  - `test_monitoring_applies_field_rule_as_monitor_never_gate`
  - `test_no_flag_edits_the_vault_config`
  - `test_report_cli_is_read_only_dry_run_first`
- [tests/test_ad_denial_log.py](../../../../../../tests/test_ad_denial_log.py) — direct import
  - `test_old_format_lines_stay_readable_and_are_grouped_as_unrecorded`
  - `test_the_report_renders_a_guard_block_without_entries`
  - `test_v2_f2_a_report_without_the_lock_does_not_count_archives`
- [tests/test_ad_guard_offer_receipts.py](../../../../../../tests/test_ad_guard_offer_receipts.py) — direct import
  - `test_the_serving_snapshot_and_the_report_run_with_zero_denials`
- [tests/test_ad_guard_reachable_reads.py](../../../../../../tests/test_ad_guard_reachable_reads.py) — direct import
- [tests/test_ad_protected_readings.py](../../../../../../tests/test_ad_protected_readings.py) — direct import
- [tests/test_data_capture_a4_delayed_completion.py](../../../../../../tests/test_data_capture_a4_delayed_completion.py) — direct import
- [tests/test_data_capture_codex_review.py](../../../../../../tests/test_data_capture_codex_review.py) — direct import
- [tests/test_te3a_lesson_opportunity.py](../../../../../../tests/test_te3a_lesson_opportunity.py) — direct import
  - `test_the_reports_lesson_row_at_the_prior_and_after_lessons`

## Modification guidance

- Make changes here when the responsibility remains report within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/report.py](../../../../../../src/learnloop/adaptive_difficulty/report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
