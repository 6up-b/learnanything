---
title: "learnloop.adaptive_difficulty.serve"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/serve.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/serve.py"
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
  - "learnloop.adaptive_difficulty.serve module"
  - "src/learnloop/adaptive_difficulty/serve.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.serve`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.serve` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: AD1's serve hook (spec_adaptive_difficulty_v1 §7.5, §8.1, §5.11).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/serve.py](../../../../../../src/learnloop/adaptive_difficulty/serve.py) |
| Source lines | 184 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ServeRecord` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve.py), line 61)
- `record_plan_serve(vault: Any, repository: Any, *, presentation_id: str, practice_item_id: str, served_at: str) -> ServeRecord | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve.py), line 82) — Record AD1's serve-time receipts for one plan presentation, in the caller's transaction.

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/serve.py](../../../../../../src/learnloop/adaptive_difficulty/serve.py), line 55)
- `PLAN_PRESENTATION` ([src/learnloop/adaptive_difficulty/serve.py](../../../../../../src/learnloop/adaptive_difficulty/serve.py), line 57)

### Explicit exports

`__all__` declares:

- `PLAN_PRESENTATION`
- `ServeRecord`
- `record_plan_serve`

## Internal implementation anchors

- `_serve_unrecorded(arguments: Any) -> 'ServeRecord'` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve.py), line 73)
- `_recorded(connection: Any, presentation_id: str) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve.py), line 168)
- `_with_version(receipt: Any, algorithm_version: str, epoch: str | None) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve.py), line 176)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `record_plan_serve`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]] — imports `in_process_receipts`; calls `in_process_receipts`
- [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]] — imports `record_landed_commissions`; calls `record_landed_commissions`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]] — imports `freeze_history_inputs`; calls `freeze_history_inputs`
- [[Reference/Modules/learnloop/adaptive_difficulty/logs|learnloop.adaptive_difficulty.logs]] — imports `warn_failure`; calls `warn_failure`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `current_view`, `material_view`; calls `current_view`, `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `entry`; calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `freeze_presentation_inputs`; calls `freeze_presentation_inputs`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `sweep`; calls `sweep`
- [[Reference/Modules/learnloop/adaptive_difficulty/repeat_receipts|learnloop.adaptive_difficulty.repeat_receipts]] — imports `new_receipt_id`, `repeat_receipts`; calls `repeat_receipts`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve_inputs|learnloop.adaptive_difficulty.serve_inputs]] — imports `build_row`, `never_attempted`; calls `build_row`, `never_attempted`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `frozen_loadings`, `served_item`, `threshold_receipts`; calls `frozen_loadings`, `served_item`, `threshold_receipts`
- [[Reference/Modules/learnloop/adaptive_difficulty/switches|learnloop.adaptive_difficulty.switches]] — imports `receipts_enabled`; calls `receipts_enabled`
- [[Reference/Modules/learnloop/db/stores/ad_receipts|learnloop.db.stores.ad_receipts]] — imports `module`; calls `has_table`, `insert_serve_inputs`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `record_receipts`; calls `record_receipts`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/difficulty_replay_helpers.py](../../../../../../tests/difficulty_replay_helpers.py) — direct import
- [tests/epp_repeat_helpers.py](../../../../../../tests/epp_repeat_helpers.py) — direct import
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
- [tests/test_ad_guard.py](../../../../../../tests/test_ad_guard.py) — direct import
- [tests/test_adaptive_difficulty_ad1.py](../../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
  - `test_a_failed_ad_write_never_breaks_the_serve`
  - `test_forecast_receipt_written_in_serve_transaction`
  - `test_held_out_sentinel_never_reaches_ad_inputs`
  - `test_serve_inputs_frozen_against_later_audit_and_edit`
- [tests/test_epp_repeat_receipts.py](../../../../../../tests/test_epp_repeat_receipts.py) — direct import
  - `test_a_guard_refusal_is_never_bypassed`
  - `test_a_protected_item_gets_no_repeat_receipt`
  - `test_a_reopened_presentation_records_nothing_again`
  - `test_repeat_receipt_ids_come_from_their_own_stream`
  - `test_repeat_receipts_roll_back_with_the_serve_transaction`
  - `test_the_repeat_path_writes_no_frozen_inputs_and_no_revision_snapshot`
- [tests/test_ro2_ad_document_ir.py](../../../../../../tests/test_ro2_ad_document_ir.py) — direct import
  - `test_the_serve_records_its_ad_rows_with_a_span_anchored_question`
- [tests/test_ro2_ad_raw_document_reads.py](../../../../../../tests/test_ro2_ad_raw_document_reads.py) — direct import
  - `test_a_guard_denial_in_ads_serve_leaves_the_learners_serve_unchanged`
  - `test_at_run_time_ad_loads_a_reading_only_through_its_chokepoint`
- [tests/test_ro2_history_protection.py](../../../../../../tests/test_ro2_history_protection.py) — direct import
  - `test_content_held_out_after_the_serve_is_never_sent`
- [tests/test_ro2_history_resolve.py](../../../../../../tests/test_ro2_history_resolve.py) — direct import
  - `test_the_dry_run_estimates_the_runs_own_output_budget_and_retry`
  - `test_the_permuted_run_sends_another_presentations_history`
  - `test_the_serve_transactions_added_cost_is_measured`
- [tests/test_selected_forecast.py](../../../../../../tests/test_selected_forecast.py) — direct import
  - `test_selection_view_and_missing_selection_live_and_rebuilt`

## Modification guidance

- Make changes here when the responsibility remains serve within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/serve.py](../../../../../../src/learnloop/adaptive_difficulty/serve.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
