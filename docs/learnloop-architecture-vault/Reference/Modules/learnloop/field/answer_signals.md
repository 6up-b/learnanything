---
title: "learnloop.field.answer_signals"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/field/answer_signals.py"
source_paths:
  - "src/learnloop/field/answer_signals.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.field"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.field.answer_signals module"
  - "src/learnloop/field/answer_signals.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-field"
---

# `learnloop.field.answer_signals`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/field/_package|learnloop.field]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.field.answer_signals` exists within [[Reference/Modules/learnloop/field/_package|learnloop.field]] to own the behavior summarized by its module contract: Offline answer-signal arms for the learner field's predictor duel.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/field/answer_signals.py](../../../../../../src/learnloop/field/answer_signals.py) |
| Source lines | 391 |
| Owning package | [[Reference/Modules/learnloop/field/_package|learnloop.field]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `stacked_name(base: str, signal: str, *, control: bool=False) -> str` ([source](../../../../../../src/learnloop/field/answer_signals.py), line 78)
- `signal_feature(signal: str, signals: AnswerSignals | None) -> float | None` ([source](../../../../../../src/learnloop/field/answer_signals.py), line 98) — The arm's covariate, or None where the learner gave no such signal.
- `fit_logistic(features: list[float], offsets: list[float], outcomes: list[float], *, prior_mean: tuple[float, float], prior_variance: float=1.0, intercept: bool=True, max_steps: int=_NEWTON_STEPS) -> tuple[float, float]` ([source](../../../../../../src/learnloop/field/answer_signals.py), line 131) — MAP ``(a, b)`` of ``logit p = offset + a + b * x`` under N(prior, v) priors.
- `class AnswerSignalArm` ([source](../../../../../../src/learnloop/field/answer_signals.py), line 212) — A point predictor over one answer signal, optionally on a base arm.
  - `__init__(self, *, signal: str, base_name: str | None=None, control: bool=False, **base_inputs) -> None` (line 219; internal)
  - `_make_base(self)` (line 255; internal)
  - `_reset_fit(self) -> None` (line 260; internal)
  - `covers_answer(self, signals: AnswerSignals | None) -> bool` (line 266; public)
  - `_covariate(self, signals: AnswerSignals | None) -> float | None` (line 269; internal)
  - `_offset(self, features: ItemFeatures) -> float` (line 273; internal)
  - `predict(self, features: ItemFeatures) -> float` (line 276; public) — Without an answer signal: the base arm's prediction (1/2 alone).
  - `predict_answer(self, features: ItemFeatures, signals: AnswerSignals | None) -> float` (line 287; public)
  - `observe(self, row) -> None` (line 296; public)
  - `rebuild(self, rows: Iterable) -> None` (line 320; public)
  - `snapshot_bytes(self) -> bytes` (line 326; public)
- `stacked_arm(base: str, signal: str, *, control: bool=False, **inputs) -> AnswerSignalArm` ([source](../../../../../../src/learnloop/field/answer_signals.py), line 334) — ``<base>+answer_<signal>`` (or its ``:control``) for any attempt-level arm.
- `default_pairs() -> tuple[tuple[str, str], ...]` ([source](../../../../../../src/learnloop/field/answer_signals.py), line 360) — The duel's pairs for every registered stack: (base, stack), what the stack adds over its base; and (control, stack), what the signal adds over recalibrating the base on the same attempts.

### Module constants

- `CONFIDENCE` ([src/learnloop/field/answer_signals.py](../../../../../../src/learnloop/field/answer_signals.py), line 58)
- `HEDGING` ([src/learnloop/field/answer_signals.py](../../../../../../src/learnloop/field/answer_signals.py), line 59)
- `SIGNALS` ([src/learnloop/field/answer_signals.py](../../../../../../src/learnloop/field/answer_signals.py), line 60)
- `ARM_NAMES` ([src/learnloop/field/answer_signals.py](../../../../../../src/learnloop/field/answer_signals.py), line 61)
- `DEFAULT_STACK_BASES` ([src/learnloop/field/answer_signals.py](../../../../../../src/learnloop/field/answer_signals.py), line 64)
- `FIT` ([src/learnloop/field/answer_signals.py](../../../../../../src/learnloop/field/answer_signals.py), line 67)
- `CLIP` ([src/learnloop/field/answer_signals.py](../../../../../../src/learnloop/field/answer_signals.py), line 68)
- `_NEWTON_STEPS` ([src/learnloop/field/answer_signals.py](../../../../../../src/learnloop/field/answer_signals.py), line 69)
- `_GRADIENT_TOLERANCE` ([src/learnloop/field/answer_signals.py](../../../../../../src/learnloop/field/answer_signals.py), line 70)
- `SIGNAL_SOURCES` ([src/learnloop/field/answer_signals.py](../../../../../../src/learnloop/field/answer_signals.py), line 72)
- `CONTROL_SUFFIX` ([src/learnloop/field/answer_signals.py](../../../../../../src/learnloop/field/answer_signals.py), line 85)

### Explicit exports

`__all__` declares:

- `ARM_NAMES`
- `AnswerSignalArm`
- `CONFIDENCE`
- `CONTROL_SUFFIX`
- `DEFAULT_STACK_BASES`
- `FIT`
- `HEDGING`
- `SIGNALS`
- `SIGNAL_SOURCES`
- `default_pairs`
- `fit_logistic`
- `signal_feature`
- `stacked_arm`
- `stacked_name`

## Internal implementation anchors

- `_logit(p: float) -> float` ([source](../../../../../../src/learnloop/field/answer_signals.py), line 88)
- `_sigmoid(x: float) -> float` ([source](../../../../../../src/learnloop/field/answer_signals.py), line 93)
- `_log_sigmoid(z: float) -> float` ([source](../../../../../../src/learnloop/field/answer_signals.py), line 114) — ``log(sigmoid(z))`` without overflow or a saturated ``log(0)``.
- `_log_posterior(a: float, b: float, features: list[float], offsets: list[float], outcomes: list[float], prior_mean: tuple[float, float], precision: float) -> float` ([source](../../../../../../src/learnloop/field/answer_signals.py), line 120)
- `_hash(value: object) -> str` ([source](../../../../../../src/learnloop/field/answer_signals.py), line 195)
- `_ability_row(row) -> bool` ([source](../../../../../../src/learnloop/field/answer_signals.py), line 199) — The rows the harness scores ability arms on (``evaluation._eligible``).
- `_register() -> None` ([source](../../../../../../src/learnloop/field/answer_signals.py), line 340)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]] — imports `default_pairs`; statically calls `default_pairs`
- [[Reference/Modules/learnloop/field/evaluation|learnloop.field.evaluation]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/field/predictors|learnloop.field.predictors]] — imports `_EKF_INPUTS`, `_order`, `create_predictor`, `register_predictor`, `registered_predictors`; calls `create_predictor`, `register_predictor`, `registered_predictors`
- [[Reference/Modules/learnloop/field/types|learnloop.field.types]] — imports `ANSWER_CONFIDENCE_PROBABILITY`, `AnswerSignals`, `AttemptRow`, `FacetRow`, `ItemFeatures`, `SignalRow`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `math`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]], [[Reference/Modules/learnloop/field/evaluation|learnloop.field.evaluation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/test_answer_signal_arms.py](../../../../../../tests/test_answer_signal_arms.py) — direct import
  - `test_a_control_twin_separates_the_signal_from_recalibration`
  - `test_a_fit_that_cannot_converge_says_so`
  - `test_a_prediction_never_sees_its_own_outcome`
  - `test_signal_arms_are_registered_offline_and_can_never_be_active`
  - `test_signal_features_follow_the_duel_mapping_and_abstain_when_absent`
  - `test_the_fit_converges_where_an_undamped_newton_step_oscillates`
  - `test_the_loader_reads_the_tap_and_the_graders_tone_reading`
  - `test_the_map_fit_learns_an_overconfident_learner`
  - `test_the_stack_keeps_its_base_exactly_on_every_row`
- [tests/test_eval_harness.py](../../../../../../tests/test_eval_harness.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains answer signals within learnloop.field; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/field/answer_signals.py](../../../../../../src/learnloop/field/answer_signals.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
