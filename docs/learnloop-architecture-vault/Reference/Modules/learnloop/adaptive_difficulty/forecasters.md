---
title: "learnloop.adaptive_difficulty.forecasters"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/forecasters.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/forecasters.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.adaptive_difficulty.forecasters module"
  - "src/learnloop/adaptive_difficulty/forecasters.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.forecasters`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.forecasters` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: The in-process forecasters (spec_adaptive_difficulty_v1 §8.1-8.2; AD1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/forecasters.py](../../../../../../src/learnloop/adaptive_difficulty/forecasters.py) |
| Source lines | 160 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `receipt_key(presentation_kind: str, presentation_id: str, forecaster: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/forecasters.py), line 47)
- `in_process_receipts(vault: Any, repository: Any, connection: Any, item: Any, *, presentation_kind: str, presentation_id: str, served_at: str, view: Any) -> list[ForecastReceipt]` ([source](../../../../../../src/learnloop/adaptive_difficulty/forecasters.py), line 118) — The two in-process forecasts of one presentation (each skipped alone on failure).

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/forecasters.py](../../../../../../src/learnloop/adaptive_difficulty/forecasters.py), line 34)
- `EVENT` ([src/learnloop/adaptive_difficulty/forecasters.py](../../../../../../src/learnloop/adaptive_difficulty/forecasters.py), line 36)
- `INCUMBENT` ([src/learnloop/adaptive_difficulty/forecasters.py](../../../../../../src/learnloop/adaptive_difficulty/forecasters.py), line 37)
- `CHALLENGER` ([src/learnloop/adaptive_difficulty/forecasters.py](../../../../../../src/learnloop/adaptive_difficulty/forecasters.py), line 38)
- `INCUMBENT_VERSION` ([src/learnloop/adaptive_difficulty/forecasters.py](../../../../../../src/learnloop/adaptive_difficulty/forecasters.py), line 39)
- `CHALLENGER_VERSION` ([src/learnloop/adaptive_difficulty/forecasters.py](../../../../../../src/learnloop/adaptive_difficulty/forecasters.py), line 40)

### Explicit exports

`__all__` declares:

- `CHALLENGER`
- `EVENT`
- `INCUMBENT`
- `in_process_receipts`
- `receipt_key`

## Internal implementation anchors

- `_digest(value: Any) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/forecasters.py), line 43)
- `_incumbent(vault: Any, repository: Any, item: Any, served_at: str) -> tuple[float, dict[str, Any], str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/forecasters.py), line 51)
- `_features(vault: Any, item: Any, served_at: str) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/forecasters.py), line 70)
- `_challenger(vault: Any, connection: Any, item: Any, served_at: str, *, view: Any) -> tuple[float, dict[str, Any], str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/forecasters.py), line 93)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/history_audit|learnloop.adaptive_difficulty.history_audit]] — imports `INCUMBENT`, `receipt_key`; statically calls `receipt_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]] — imports `EVENT`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `EVENT`, `INCUMBENT`, `receipt_key`; statically calls `receipt_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]] — imports `in_process_receipts`; statically calls `in_process_receipts`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `EVENT`, `receipt_key`; statically calls `receipt_key`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/logs|learnloop.adaptive_difficulty.logs]] — imports `warn_failure`; calls `warn_failure`
- [[Reference/Modules/learnloop/adaptive_difficulty/switches|learnloop.adaptive_difficulty.switches]] — imports `IN_PROCESS_FORECASTERS`
- [[Reference/Modules/learnloop/field/predictors|learnloop.field.predictors]] — imports `create_predictor`; calls `create_predictor`
- [[Reference/Modules/learnloop/field/types|learnloop.field.types]] — imports `ItemFeatures`; calls `ItemFeatures`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `resolve_item_irt_params`; calls `resolve_item_irt_params`
- [[Reference/Modules/learnloop/placement/predictor|learnloop.placement.predictor]] — imports `LiveMasteryPredictor`; calls `LiveMasteryPredictor`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `ForecastReceipt`, `ITEM_UNASSISTED_SUCCESS`; calls `ForecastReceipt`
- [[Reference/Modules/learnloop/scheduling/voi_forecasts|learnloop.scheduling.voi_forecasts]] — imports `parameter`; calls `parameter`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/history_audit|learnloop.adaptive_difficulty.history_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]], [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]], [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]], [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_ro2_history_resolve.py](../../../../../../tests/test_ro2_history_resolve.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/history_audit|learnloop.adaptive_difficulty.history_audit]]
- [tests/test_ro2_history_forecaster.py](../../../../../../tests/test_ro2_history_forecaster.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]]
- [tests/test_ro2_history_protection.py](../../../../../../tests/test_ro2_history_protection.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]]
- [tests/ad1_codex_rereview_fixes_helpers.py](../../../../../../tests/ad1_codex_rereview_fixes_helpers.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]]
- [tests/ad23_contract_helpers.py](../../../../../../tests/ad23_contract_helpers.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]]
- [tests/test_ad1_codex_rereview_fixes.py](../../../../../../tests/test_ad1_codex_rereview_fixes.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]]
- [tests/test_ad1_codex_review_fixes.py](../../../../../../tests/test_ad1_codex_review_fixes.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]]
- [tests/test_ad1_fix_round4.py](../../../../../../tests/test_ad1_fix_round4.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]]
- [tests/test_ad1_fix_round5.py](../../../../../../tests/test_ad1_fix_round5.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]]
- [tests/test_ad1_fix_round6.py](../../../../../../tests/test_ad1_fix_round6.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]]
- [tests/test_ad1_fix_round7.py](../../../../../../tests/test_ad1_fix_round7.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]]
- [tests/test_ad1_fix_round8.py](../../../../../../tests/test_ad1_fix_round8.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]]

## Modification guidance

- Make changes here when the responsibility remains forecasters within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/forecasters.py](../../../../../../src/learnloop/adaptive_difficulty/forecasters.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
