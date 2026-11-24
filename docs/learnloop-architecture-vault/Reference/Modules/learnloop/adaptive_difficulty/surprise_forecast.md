---
title: "learnloop.adaptive_difficulty.surprise_forecast"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/surprise_forecast.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/surprise_forecast.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.adaptive_difficulty.surprise_forecast module"
  - "src/learnloop/adaptive_difficulty/surprise_forecast.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.surprise_forecast`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.surprise_forecast` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: What an answer's surprise is scored against, from the difficulty label's retirement on (``docs/reviews/algorithm-mvp-0.72.md``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/surprise_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/surprise_forecast.py) |
| Source lines | 116 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SurpriseForecast` ([source](../../../../../../src/learnloop/adaptive_difficulty/surprise_forecast.py), line 46) — AD's ``p̄`` (an unassisted success) for the answer, before it, and where it was read.
- `with_grade_forecast(vault: Any, repository: Any, attempt: Any, *, clock: Any=None) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/surprise_forecast.py), line 60) — A live answer from the label's retirement on, with adaptive difficulty's forecast of it (``ApplyAttemptInput.grade_forecast``), computed read-only before the grade's write transaction, so it sees exactly what was committed before the answer, which is not yet written.
- `record_grade_forecast(repository: Any, receipt: Any) -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/surprise_forecast.py), line 74) — Append the live forecast with its attempt, in the grade's transaction (a savepoint: a failed receipt rolls back alone).
- `read_surprise_forecast(vault: Any, repository: Any, draft: Any, *, attempt_id: str, live_receipt: Any=None, replay: bool) -> SurpriseForecast | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/surprise_forecast.py), line 84) — The forecast this answer's surprise is scored against, or None (mastery's own prediction).

### Module constants

- `SERVE_RECEIPT` ([src/learnloop/adaptive_difficulty/surprise_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/surprise_forecast.py), line 38)
- `GRADE_RECEIPT` ([src/learnloop/adaptive_difficulty/surprise_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/surprise_forecast.py), line 39)
- `MASTERY` ([src/learnloop/adaptive_difficulty/surprise_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/surprise_forecast.py), line 40)
- `SERVE_FORECASTERS` ([src/learnloop/adaptive_difficulty/surprise_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/surprise_forecast.py), line 42)

### Explicit exports

`__all__` declares:

- `GRADE_RECEIPT`
- `MASTERY`
- `SERVE_FORECASTERS`
- `SERVE_RECEIPT`
- `SurpriseForecast`
- `read_surprise_forecast`
- `record_grade_forecast`
- `with_grade_forecast`

## Internal implementation anchors

- `_usable(row: dict[str, Any] | None, practice_item_id: str) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/surprise_forecast.py), line 55)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `read_surprise_forecast`, `record_grade_forecast`, `with_grade_forecast`; statically calls `read_surprise_forecast`, `record_grade_forecast`, `with_grade_forecast`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/grade_forecast|learnloop.adaptive_difficulty.grade_forecast]] — imports `receipt_id`, `safe_grade_receipt`; calls `receipt_id`, `safe_grade_receipt`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `label_retired`; calls `label_retired`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/forecast_receipts|learnloop.db.stores.forecast_receipts]] — imports `module`; calls `attempt_forecast`, `presentation_forecasts`
- [[Reference/Modules/learnloop/db/stores/plan_presentations|learnloop.db.stores.plan_presentations]] — imports `bindable_presentation`, `presentation_by_id`; calls `bindable_presentation`, `presentation_by_id`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `ITEM_UNASSISTED_SUCCESS`, `ITEM_UNASSISTED_SUCCESS_AT_GRADE`, `record_receipts`, `valid_for_serve`; calls `record_receipts`, `valid_for_serve`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/ad23_contract_helpers.py](../../../../../../tests/ad23_contract_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/ad23_fakes.py](../../../../../../tests/ad23_fakes.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/assumed_known_helpers.py](../../../../../../tests/assumed_known_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/causal_cold_outcomes_helpers.py](../../../../../../tests/causal_cold_outcomes_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/causal_factor_deferral_helpers.py](../../../../../../tests/causal_factor_deferral_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/causal_p2_acceptance_helpers.py](../../../../../../tests/causal_p2_acceptance_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/certification_cold_probe_helpers.py](../../../../../../tests/certification_cold_probe_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/cold_retry_reschedule_helpers.py](../../../../../../tests/cold_retry_reschedule_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnosis_journey_helpers.py](../../../../../../tests/diagnosis_journey_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnosis_split_helpers.py](../../../../../../tests/diagnosis_split_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnostic_augmentation_helpers.py](../../../../../../tests/diagnostic_augmentation_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnostic_probe_single_use_helpers.py](../../../../../../tests/diagnostic_probe_single_use_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]

## Modification guidance

- Make changes here when the responsibility remains surprise forecast within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/surprise_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/surprise_forecast.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
