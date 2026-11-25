---
title: "learnloop.adaptive_difficulty.grade_forecast"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/grade_forecast.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/grade_forecast.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.adaptive_difficulty.grade_forecast module"
  - "src/learnloop/adaptive_difficulty/grade_forecast.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.grade_forecast`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.grade_forecast` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: AD's forecast of a graded answer, as AD stood before it (``docs/reviews/algorithm-mvp-0.71.md``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/grade_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/grade_forecast.py) |
| Source lines | 169 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `receipt_id(attempt_id: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/grade_forecast.py), line 40) — A grade-time receipt's id, a function of its attempt (:func:`learnloop.ids.keyed_ulid`): drawn from ``ids.new_ulid`` it would shift every id the grade mints after it, and drawn from a stream of its own it would differ between two runs of the same history.
- `receipt_key(attempt_id: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/grade_forecast.py), line 48)
- `grade_receipt(vault: Any, repository: Any, *, practice_item_id: str, attempt_id: str, at: str, answered_item: Any=None, answered_revision: str | None=None, view: Any=None, answered: Any=None) -> ForecastReceipt | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/grade_forecast.py), line 65) — AD's subject-view forecast for the answer ``attempt_id`` to ``practice_item_id`` at ``at``, from AD's state over everything recorded before it; None when AD is off, the item is protected or unknown to AD's view.
- `safe_grade_receipt(vault: Any, repository: Any, **kwargs: Any) -> ForecastReceipt | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/grade_forecast.py), line 158) — :func:`grade_receipt`, never raising: a forecast never costs the grade.

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/grade_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/grade_forecast.py), line 33)
- `GRADE_FORECASTER` ([src/learnloop/adaptive_difficulty/grade_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/grade_forecast.py), line 35)
- `GRADE_FORECAST_VERSION` ([src/learnloop/adaptive_difficulty/grade_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/grade_forecast.py), line 36)
- `GRADED_ATTEMPT` ([src/learnloop/adaptive_difficulty/grade_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/grade_forecast.py), line 38)

### Explicit exports

`__all__` declares:

- `GRADED_ATTEMPT`
- `GRADE_FORECASTER`
- `GRADE_FORECAST_VERSION`
- `grade_receipt`
- `receipt_id`
- `receipt_key`
- `safe_grade_receipt`

## Internal implementation anchors

- `_evidence_after(events: Any, at: str) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/grade_forecast.py), line 52) — Whether AD's evidence holds anything dated after the answer's cutoff ``at`` (an attempt, a claim or a reading opportunity).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/surprise_forecast|learnloop.adaptive_difficulty.surprise_forecast]] — imports `receipt_id`, `receipt_key`, `safe_grade_receipt`; statically calls `receipt_id`, `receipt_key`, `safe_grade_receipt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]] — imports `EVENT`
- [[Reference/Modules/learnloop/adaptive_difficulty/logs|learnloop.adaptive_difficulty.logs]] — imports `warn_failure`; calls `warn_failure`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `material_view`; calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `entry`; calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/predict|learnloop.adaptive_difficulty.predict]] — imports `module`; calls `category_mixture`, `predict`
- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `module`; calls `versions`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; calls `days`, `events_fingerprint`, `snapshot`
- [[Reference/Modules/learnloop/adaptive_difficulty/selection|learnloop.adaptive_difficulty.selection]] — imports `module`; calls `constants_from_config`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `_spec`, `_warmth`, `served_item`; calls `_spec`, `_warmth`, `served_item`
- [[Reference/Modules/learnloop/adaptive_difficulty/snapshot_parts|learnloop.adaptive_difficulty.snapshot_parts]] — imports `threshold_snapshot`; calls `threshold_snapshot`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `successor_active`; calls `successor_active`
- [[Reference/Modules/learnloop/adaptive_difficulty/switches|learnloop.adaptive_difficulty.switches]] — imports `receipts_enabled`; calls `receipts_enabled`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `cutoff_reads_the_view`; calls `cutoff_reads_the_view`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/evidence_cutoff|learnloop.db.evidence_cutoff]] — imports `Cutoff`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `keyed_ulid`; calls `keyed_ulid`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `ForecastReceipt`, `ITEM_UNASSISTED_SUCCESS_AT_GRADE`; calls `ForecastReceipt`
- [[Reference/Modules/learnloop/scheduling/voi_forecasts|learnloop.scheduling.voi_forecasts]] — imports `parameter`; calls `parameter`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `item_revision`; calls `item_revision`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/surprise_forecast|learnloop.adaptive_difficulty.surprise_forecast]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_surprise_reads_ad_forecast.py](../../../../../../tests/test_surprise_reads_ad_forecast.py) — direct import
  - `test_a_writer_committing_between_the_read_and_the_write_leaves_the_recorded_forecast_standing`
  - `test_grade_snapshot_names_the_answer_and_its_cutoff`

## Modification guidance

- Make changes here when the responsibility remains grade forecast within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/grade_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/grade_forecast.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
