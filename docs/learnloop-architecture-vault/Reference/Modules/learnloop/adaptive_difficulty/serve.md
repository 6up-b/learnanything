---
title: "learnloop.adaptive_difficulty.serve"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/serve.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/serve.py"
source_commit: "f44a2201c4ba1360ab15ba2f003266c04b175356"
source_commit_timestamp: "2026-11-04T21:18:14-05:00"
source_worktree_state: "clean"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.serve` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: AD1's serve hook (spec_adaptive_difficulty_v1 §7.5, §8.1, §5.11).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/serve.py](../../../../../../src/learnloop/adaptive_difficulty/serve.py) |
| Source lines | 165 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `f44a2201c4ba1360ab15ba2f003266c04b175356` |
| Commit timestamp | `2026-11-04T21:18:14-05:00` |

## Public API

- `class ServeRecord` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve.py), line 58)
- `record_plan_serve(vault: Any, repository: Any, *, presentation_id: str, practice_item_id: str, served_at: str) -> ServeRecord | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve.py), line 77) — Record AD1's serve-time receipts for one plan presentation, in the caller's transaction.

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/serve.py](../../../../../../src/learnloop/adaptive_difficulty/serve.py), line 52)
- `PLAN_PRESENTATION` ([src/learnloop/adaptive_difficulty/serve.py](../../../../../../src/learnloop/adaptive_difficulty/serve.py), line 54)

### Explicit exports

`__all__` declares:

- `PLAN_PRESENTATION`
- `ServeRecord`
- `record_plan_serve`

## Internal implementation anchors

- `_serve_unrecorded(arguments: Any) -> 'ServeRecord'` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve.py), line 68)
- `_recorded(connection: Any, presentation_id: str) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve.py), line 149)
- `_with_version(receipt: Any, algorithm_version: str, epoch: str | None) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve.py), line 157)

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
- [[Reference/Modules/learnloop/adaptive_difficulty/serve_inputs|learnloop.adaptive_difficulty.serve_inputs]] — imports `build_row`, `never_attempted`; calls `build_row`, `never_attempted`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `frozen_loadings`, `threshold_receipts`; calls `frozen_loadings`, `threshold_receipts`
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

- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
- [tests/test_ad_guard.py](../../../../../../tests/test_ad_guard.py) — direct import
- [tests/test_adaptive_difficulty_ad1.py](../../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
  - `test_a_failed_ad_write_never_breaks_the_serve`
  - `test_forecast_receipt_written_in_serve_transaction`
  - `test_held_out_sentinel_never_reaches_ad_inputs`
  - `test_serve_inputs_frozen_against_later_audit_and_edit`
- [tests/test_ro2_history_protection.py](../../../../../../tests/test_ro2_history_protection.py) — direct import
  - `test_content_held_out_after_the_serve_is_never_sent`
- [tests/test_ro2_history_resolve.py](../../../../../../tests/test_ro2_history_resolve.py) — direct import
  - `test_the_dry_run_estimates_the_runs_own_output_budget_and_retry`
  - `test_the_permuted_run_sends_another_presentations_history`
  - `test_the_serve_transactions_added_cost_is_measured`

## Modification guidance

- Make changes here when the responsibility remains serve within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/serve.py](../../../../../../src/learnloop/adaptive_difficulty/serve.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
