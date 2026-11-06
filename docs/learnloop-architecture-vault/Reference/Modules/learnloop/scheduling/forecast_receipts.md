---
title: "learnloop.scheduling.forecast_receipts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/forecast_receipts.py"
source_paths:
  - "src/learnloop/scheduling/forecast_receipts.py"
source_commit: "workspace/uncommitted @ HEAD 271a042fd6e7c418c6abdb96d8eb08fd1d8e595a"
source_commit_timestamp: "2026-11-06T11:32:04-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.scheduling.forecast_receipts module"
  - "src/learnloop/scheduling/forecast_receipts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.forecast_receipts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.forecast_receipts` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: Saved forecasts: one receipt family for every expectation a decision states.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py) |
| Source lines | 327 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 271a042fd6e7c418c6abdb96d8eb08fd1d8e595a` |
| Commit timestamp | `2026-11-06T11:32:04-05:00` |

## Public API

- `class ForecastReceipt` ([source](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 125) — One forecast, ready to append (the store fills its id).
- `valid_for_serve(receipt: Mapping[str, Any], served_at: str | None) -> bool` ([source](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 145) — AD1's validity rule (spec_adaptive_difficulty_v1 §8.1): a forecast is valid for a presentation iff the inputs it read are no later than the serve (``inputs_as_of <= served_at``), whenever it arrived.
- `receipts_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 158) — The ``diagnosis.forecast_receipts`` kill switch (on without a vault config).
- `inputs_digest(inputs: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 165)
- `categorical_body(likelihood: Mapping[str, Mapping[str, float]], prior: Mapping[str, float], *, alphabet: Sequence[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 170) — The Part B body of a categorical forecast over ``alphabet``.
- `clamped_as_of(value: str | None, created_at: str) -> str` ([source](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 204) — ``inputs_as_of`` in the receipt's own format, never after the receipt.
- `record_receipts(repository: Repository | None, receipts: Sequence[ForecastReceipt], *, vault: Any=None, clock: Clock | None=None, created_at: str | None=None) -> list[str]` ([source](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 228) — Append ``receipts`` in the caller's transaction; never raises.

### Module constants

- `RECEIPT_SHAPE_VERSION` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 60)
- `DIAGNOSIS_NEXT_OBSERVATION` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 64)
- `REPAIR_COLD_OUTCOME` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 65)
- `CHECK_OUTCOME` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 66)
- `ITEM_UNASSISTED_SUCCESS` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 71)
- `LESSON_CHECK_CORRECT` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 77)
- `LESSON_STEP_RETAINED` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 78)
- `LESSON_NODE_HELD` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 83)
- `LO_COLD_SUCCESS` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 88)
- `LESSON_PROBE_CORRECT` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 92)
- `FORECAST_KINDS` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 93)
- `SCOPES` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 96)
- `PRESENTED_ATTEMPT_ON_FACET` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 99)
- `FOLLOWUP_TASK` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 100)
- `FIRST_PRESENTATION` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 103)
- `LESSON_CHECK_ATTEMPT` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 106)
- `LESSON_COLD_OUTCOME` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 107)
- `LO_COLD_AFTER_BLOCK` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 110)
- `LESSON_PROBE_ATTEMPT` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 112)
- `NO_BINDING` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 113)
- `BINDING_KINDS` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 114)
- `DECISION_KINDS` ([src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 121)

### Explicit exports

`__all__` declares:

- `BINDING_KINDS`
- `CHECK_OUTCOME`
- `DECISION_KINDS`
- `DIAGNOSIS_NEXT_OBSERVATION`
- `FIRST_PRESENTATION`
- `FOLLOWUP_TASK`
- `FORECAST_KINDS`
- `ITEM_UNASSISTED_SUCCESS`
- `LESSON_CHECK_ATTEMPT`
- `LESSON_CHECK_CORRECT`
- `LESSON_COLD_OUTCOME`
- `LESSON_NODE_HELD`
- `LESSON_PROBE_ATTEMPT`
- `LESSON_PROBE_CORRECT`
- `LESSON_STEP_RETAINED`
- `LO_COLD_AFTER_BLOCK`
- `LO_COLD_SUCCESS`
- `ForecastReceipt`
- `NO_BINDING`
- `PRESENTED_ATTEMPT_ON_FACET`
- `RECEIPT_SHAPE_VERSION`
- `REPAIR_COLD_OUTCOME`
- `SCOPES`
- `categorical_body`
- `clamped_as_of`
- `inputs_digest`
- `receipts_enabled`
- `record_receipts`
- `valid_for_serve`

## Internal implementation anchors

- `_validated(receipt: ForecastReceipt) -> None` ([source](../../../../../../src/learnloop/scheduling/forecast_receipts.py), line 214)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]] — imports `ForecastReceipt`, `ITEM_UNASSISTED_SUCCESS`; statically calls `ForecastReceipt`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]] — imports `ForecastReceipt`, `ITEM_UNASSISTED_SUCCESS`, `LO_COLD_AFTER_BLOCK`, `LO_COLD_SUCCESS`, `NO_BINDING`, `record_receipts`; statically calls `ForecastReceipt`, `record_receipts`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]] — imports `LO_COLD_SUCCESS`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `FIRST_PRESENTATION`, `ForecastReceipt`, `ITEM_UNASSISTED_SUCCESS`, `record_receipts`; statically calls `ForecastReceipt`, `record_receipts`
- [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]] — imports `valid_for_serve`; statically calls `valid_for_serve`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]] — imports `record_receipts`; statically calls `record_receipts`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `ForecastReceipt`, `ITEM_UNASSISTED_SUCCESS`; statically calls `ForecastReceipt`
- [[Reference/Modules/learnloop/diagnosis/forecast_receipts|learnloop.diagnosis.forecast_receipts]] — imports `module`; statically calls `ForecastReceipt`, `categorical_body`, `receipts_enabled`, `record_receipts`
- [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]] — imports `module`
- [[Reference/Modules/learnloop/teacher/episodes|learnloop.teacher.episodes]] — imports `ForecastReceipt`, `LESSON_COLD_OUTCOME`, `LESSON_NODE_HELD`; statically calls `ForecastReceipt`
- [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]] — imports `ForecastReceipt`, `LESSON_PROBE_ATTEMPT`, `LESSON_PROBE_CORRECT`, `record_receipts`; statically calls `ForecastReceipt`, `record_receipts`
- [[Reference/Modules/learnloop/teacher/report|learnloop.teacher.report]] — imports `LESSON_NODE_HELD`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `ForecastReceipt`, `LESSON_CHECK_ATTEMPT`, `LESSON_COLD_OUTCOME`, `record_receipts`; statically calls `ForecastReceipt`, `record_receipts`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/forecast_receipts|learnloop.db.stores.forecast_receipts]] — imports `module`; calls `has_table`, `insert_receipt`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]], [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]], [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]], [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]], [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]] and 8 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_fix_r8.py](../../../../../../tests/test_ad23_fix_r8.py) — direct import
  - `test_z_v1_calibration_never_reads_a_withheld_items_forecast`
- [tests/test_ad_epoch.py](../../../../../../tests/test_ad_epoch.py) — direct import
  - `test_frozen_serve_signals_trained_on_a_newly_protected_answer_are_not_replayed`
- [tests/test_adaptive_difficulty_ad1.py](../../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
  - `test_forecast_receipt_written_in_serve_transaction`
  - `test_forecast_with_post_serve_inputs_is_invalid`
  - `test_late_outside_forecast_is_valid_if_inputs_predate_serve`
- [tests/test_cold_retry_reschedule.py](../../../../../../tests/test_cold_retry_reschedule.py) — direct import
  - `test_the_fresh_retry_records_its_own_repair_forecast_which_resolves_when_it_is_measured`
- [tests/test_forecast_receipts.py](../../../../../../tests/test_forecast_receipts.py) — direct import
  - `test_a_completed_diagnosis_writes_its_forecast_in_its_own_transaction`
  - `test_a_held_grade_resolves_nothing_until_a_regrade_releases_it`
  - `test_a_repair_without_an_independent_surface_is_censored_at_birth`
  - `test_a_scheduled_cold_check_records_its_repair_forecast_and_resolves_on_its_task`
  - `test_attempts_visible_when_the_receipt_was_written_are_never_its_observation`
  - `test_f1_an_error_on_another_facet_is_not_the_forecast_facets_recurrence`
  - `test_f1_an_unassessed_target_facet_censors_whatever_errors_another_facet_shows`
  - `test_replay_neither_reads_nor_writes_forecast_receipts`
  - `test_the_calibration_report_on_a_seeded_vault`
- [tests/test_forecast_receipts_landing.py](../../../../../../tests/test_forecast_receipts_landing.py) — direct import
  - `test_the_provenance_record_the_diagnosis_and_its_forecasts_commit_as_one_transaction`
- [tests/test_teacher_te2log_node_held.py](../../../../../../tests/test_teacher_te2log_node_held.py) — direct import
  - `test_each_p_held_is_a_lesson_node_held_forecast_on_its_lo`
  - `test_one_refused_node_forecast_leaves_its_siblings`
  - `test_switch_off_has_no_p_held_and_writes_no_forecast`
  - `test_the_forecast_report_resolves_it_on_the_first_cold_outcome`

## Modification guidance

- Change forecast receipts policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/forecast_receipts.py](../../../../../../src/learnloop/scheduling/forecast_receipts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
