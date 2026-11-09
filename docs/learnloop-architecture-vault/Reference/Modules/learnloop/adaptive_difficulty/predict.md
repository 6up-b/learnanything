---
title: "learnloop.adaptive_difficulty.predict"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/predict.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/predict.py"
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
  - "learnloop.adaptive_difficulty.predict module"
  - "src/learnloop/adaptive_difficulty/predict.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.predict`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.predict` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: Predictive quantities for decisions and receipts (spec_adaptive_difficulty_v1 §5.7).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/predict.py](../../../../../../src/learnloop/adaptive_difficulty/predict.py) |
| Source lines | 172 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `mixture_weights(view: View, *, uniform: bool=False) -> np.ndarray` ([source](../../../../../../src/learnloop/adaptive_difficulty/predict.py), line 33)
- `class Prediction` ([source](../../../../../../src/learnloop/adaptive_difficulty/predict.py), line 44)
  - `as_dict(self) -> dict[str, Any]` (line 49; public)
- `predict(view: View, spec: ItemSpec, *, warmth: float=0.0, weights: np.ndarray | None=None, band: tuple[float, float]=(0.7, 0.8)) -> Prediction` ([source](../../../../../../src/learnloop/adaptive_difficulty/predict.py), line 53) — ``p̄(x)`` and ``P_band(x)`` (mixtures in the subject view).
- `score(view: View, specs: Sequence[ItemSpec], *, warmth: float=0.0, constants: SelectionConstants=SelectionConstants(), weights: np.ndarray | None=None, information: bool=True) -> list[Scored]` ([source](../../../../../../src/learnloop/adaptive_difficulty/predict.py), line 65) — Each candidate's ``Scored`` (``P_band``, ``p̄`` and the cell information ``I_c``).
- `item_subject(vault: Any, item: Any) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/predict.py), line 94)
- `facet_weights(vault: Any, item: Any) -> dict[str, float]` ([source](../../../../../../src/learnloop/adaptive_difficulty/predict.py), line 99)
- `capability(item: Any) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/predict.py), line 108)
- `guess(vault: Any, item: Any) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/predict.py), line 121)
- `current_spec(vault: Any, connection: Any, item: Any, *, at: str, view: Any, loadings: Mapping[str, float] | None=None, outside: bool=False) -> ItemSpec` ([source](../../../../../../src/learnloop/adaptive_difficulty/predict.py), line 130) — The item as a decision now reads it: the audit where answered, else the stamped features; the signals the serve-input receipt would freeze (their calibration history read through ``view``, the operation's material view); the loadings in force.
- `point_spec(point: Mapping[str, Any], *, learning_object_id: str, subject: str, facet: str, capability_name: str) -> ItemSpec` ([source](../../../../../../src/learnloop/adaptive_difficulty/predict.py), line 152) — A not-yet-written feature point (``z = 0``, the cell's own facet only).

### Module constants

- `VIEW_SUBJECT` ([src/learnloop/adaptive_difficulty/predict.py](../../../../../../src/learnloop/adaptive_difficulty/predict.py), line 30)

### Explicit exports

`__all__` declares:

- `Prediction`
- `VIEW_SUBJECT`
- `capability`
- `current_spec`
- `facet_weights`
- `guess`
- `item_subject`
- `mixture_weights`
- `point_spec`
- `predict`
- `score`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]] — imports `module`; statically calls `point_spec`, `predict`
- [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]] — imports `module`; statically calls `capability`, `current_spec`, `facet_weights`, `point_spec`, `predict`
- [[Reference/Modules/learnloop/adaptive_difficulty/readiness|learnloop.adaptive_difficulty.readiness]] — imports `module`; statically calls `capability`, `facet_weights`, `item_subject`, `mixture_weights`, `point_spec`, `predict`, `score`
- [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]] — imports `module`; statically calls `current_spec`, `score`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `module`; statically calls `capability`, `current_spec`, `facet_weights`, `mixture_weights`, `point_spec`, `predict`, `score`
- [[Reference/Modules/learnloop/daily_plan/ad_slot|learnloop.daily_plan.ad_slot]] — imports `module`; statically calls `capability`, `facet_weights`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `item_revision`; calls `item_revision`
- [[Reference/Modules/learnloop/adaptive_difficulty/model|learnloop.adaptive_difficulty.model]] — imports `module`; calls `band_probability`, `cell_information`, `expected_success`
- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `module`
- [[Reference/Modules/learnloop/adaptive_difficulty/selection|learnloop.adaptive_difficulty.selection]] — imports `Scored`, `SelectionConstants`, `point_key`; calls `Scored`, `SelectionConstants`, `point_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve_inputs|learnloop.adaptive_difficulty.serve_inputs]] — imports `feature_inputs`, `signal_vector`; calls `feature_inputs`, `signal_vector`
- [[Reference/Modules/learnloop/adaptive_difficulty/state|learnloop.adaptive_difficulty.state]] — imports `ItemSpec`, `View`, `normalized_weights`; calls `ItemSpec`, `normalized_weights`
- [[Reference/Modules/learnloop/learner/blueprint_projection|learnloop.learner.blueprint_projection]] — imports `guess_floor_for_item`; calls `guess_floor_for_item`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `default_capability_for`; calls `default_capability_for`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]], [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]], [[Reference/Modules/learnloop/adaptive_difficulty/readiness|learnloop.adaptive_difficulty.readiness]], [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]], [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
  - `test_goal_focus_follows_the_live_decision_view_with_promoted_predictor_off`
- [tests/test_ad23_fix_r7.py](../../../../../../tests/test_ad23_fix_r7.py) — direct import
  - `test_a_protected_item_never_steers_the_commissioned_cell_or_readiness`
- [tests/test_ad23_fix_r8.py](../../../../../../tests/test_ad23_fix_r8.py) — direct import
  - `test_a_claim_moves_no_forecast_through_a_withheld_items_facet`
  - `test_report_sensitivity_never_re_forecasts_a_withheld_item`
- [tests/test_ad3_subject_view.py](../../../../../../tests/test_ad3_subject_view.py) — direct import
  - `test_coupling_is_prediction_only`
  - `test_subject_view_mixture_keeps_propensities_exact`

## Modification guidance

- Make changes here when the responsibility remains predict within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/predict.py](../../../../../../src/learnloop/adaptive_difficulty/predict.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
