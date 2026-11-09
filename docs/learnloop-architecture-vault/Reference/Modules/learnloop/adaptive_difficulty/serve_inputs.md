---
title: "learnloop.adaptive_difficulty.serve_inputs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/serve_inputs.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/serve_inputs.py"
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
  - "learnloop.adaptive_difficulty.serve_inputs module"
  - "src/learnloop/adaptive_difficulty/serve_inputs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.serve_inputs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.serve_inputs` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: Frozen serve inputs (spec_adaptive_difficulty_v1 §7.5, §7.3; AD1, switch ``forecast_receipts``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/serve_inputs.py](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py) |
| Source lines | 317 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `never_attempted(connection: Any, practice_item_id: str, served_at: str, *, view: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 62) — No attempt of any kind on the item before (or at) the serve (read through the operation's material view: the served item is visible, or nothing reaches here).
- `pre_exposed(repository: Any, item: Any, served_at: str, *, view: Any, connection: Any=None) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 72) — §5.3: the item's reveal sum before ``served_at`` already reaches the auto-prime threshold.
- `z_v1_recalibration(connection: Any, served_at: str, *, view: Any, exclude_hash: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 186) — The logit intercept fitted on past items only: item-scoped ``llm_v1:item`` receipts received before the serve whose revision's first presentation was answered before it.
- `signal_vector(connection: Any, item: Any, content_hash: str, served_at: str, *, view: Any) -> tuple[dict[str, Any], str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 245)
- `feature_inputs(connection: Any, item: Any, content_hash: str, served_at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 265)
- `build_row(repository: Any, connection: Any, item: Any, *, presentation_kind: str, presentation_id: str, served_at: str, created_at: str, view: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 282)

### Module constants

- `RESOLUTION_VERSION` ([src/learnloop/adaptive_difficulty/serve_inputs.py](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 37)
- `Z_V1_RECALIBRATION` ([src/learnloop/adaptive_difficulty/serve_inputs.py](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 40)
- `LLM_ESTIMATE` ([src/learnloop/adaptive_difficulty/serve_inputs.py](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 41)
- `SOLVER_PANEL` ([src/learnloop/adaptive_difficulty/serve_inputs.py](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 42)
- `_SUCCESS` ([src/learnloop/adaptive_difficulty/serve_inputs.py](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 43)
- `_CLIP` ([src/learnloop/adaptive_difficulty/serve_inputs.py](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 44)

### Explicit exports

`__all__` declares:

- `RESOLUTION_VERSION`
- `Z_V1_RECALIBRATION`
- `build_row`
- `feature_inputs`
- `never_attempted`
- `pre_exposed`
- `signal_vector`
- `z_v1_recalibration`

## Internal implementation anchors

- `_logit(p: float) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 47)
- `_sigmoid(x: float) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 52)
- `_before(value: Any, served_at: str) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 56)
- `_z_llm(item: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 116)
- `_smoothed(rate: Any) -> float | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 124)
- `_z_panel(connection: Any, item: Any, served_at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 134)
- `_outcome_of_first_presentation(connection: Any, content_hash: str, served_at: str, *, attempts: Any) -> float | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 161) — §5.3's binary event on a revision's first bound plan presentation, if it completed before ``served_at``; None when there is none or it was pre-exposed.
- `_z_v1(connection: Any, content_hash: str, served_at: str, recalibration: Mapping[str, Any], *, view: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 219)
- `_z_origin(item: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 239)
- `_audited_value(dimension: str, value: str) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py), line 261)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/predict|learnloop.adaptive_difficulty.predict]] — imports `feature_inputs`, `signal_vector`; statically calls `feature_inputs`, `signal_vector`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]] — imports `build_row`, `never_attempted`; statically calls `build_row`, `never_attempted`
- [[Reference/Modules/learnloop/daily_plan/ad_slot|learnloop.daily_plan.ad_slot]] — imports `pre_exposed`; statically calls `pre_exposed`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `DIMENSIONS`, `canonical_audits`, `item_revision`; calls `canonical_audits`, `item_revision`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `current_view`; calls `current_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/switches|learnloop.adaptive_difficulty.switches]] — imports `LLM_V1`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/ad_receipts|learnloop.db.stores.ad_receipts]] — imports `module`; calls `has_table`, `insert_item_snapshot`
- [[Reference/Modules/learnloop/field/probability_arms|learnloop.field.probability_arms]] — imports `fit_intercept`; calls `fit_intercept`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `EligibilityInputs`, `RevealRow`, `submit_exposure`; calls `EligibilityInputs`, `submit_exposure`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/predict|learnloop.adaptive_difficulty.predict]], [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]], [[Reference/Modules/learnloop/daily_plan/ad_slot|learnloop.daily_plan.ad_slot]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_fix_r7.py](../../../../../../tests/test_ad23_fix_r7.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains serve inputs within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/serve_inputs.py](../../../../../../src/learnloop/adaptive_difficulty/serve_inputs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
