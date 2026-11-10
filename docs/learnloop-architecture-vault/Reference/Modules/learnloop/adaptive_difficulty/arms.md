---
title: "learnloop.adaptive_difficulty.arms"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/arms.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/arms.py"
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
  - "learnloop.adaptive_difficulty.arms module"
  - "src/learnloop/adaptive_difficulty/arms.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.arms`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.arms` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: The harness arms (spec_adaptive_difficulty_v1 §10.4), scored prequentially on AD's own replay.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/arms.py](../../../../../../src/learnloop/adaptive_difficulty/arms.py) |
| Source lines | 245 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `hyper_fixed_name(point: P.HyperPoint) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/arms.py), line 56)
- `class Record` ([source](../../../../../../src/learnloop/adaptive_difficulty/arms.py), line 61)
  - `as_dict(self) -> dict[str, Any]` (line 80; public)
- `prequential(vault: Any, repository: Any, connection: Any, *, arms: Sequence[str]=DEFAULT_ARMS, view: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/arms.py), line 201) — Every arm's prequential predictions, keyed by attempt (zero model calls).

### Module constants

- `SUBJECT` ([src/learnloop/adaptive_difficulty/arms.py](../../../../../../src/learnloop/adaptive_difficulty/arms.py), line 41)
- `UNIFORM` ([src/learnloop/adaptive_difficulty/arms.py](../../../../../../src/learnloop/adaptive_difficulty/arms.py), line 42)
- `LO` ([src/learnloop/adaptive_difficulty/arms.py](../../../../../../src/learnloop/adaptive_difficulty/arms.py), line 43)
- `NOREAD` ([src/learnloop/adaptive_difficulty/arms.py](../../../../../../src/learnloop/adaptive_difficulty/arms.py), line 44)
- `NOVERDICT` ([src/learnloop/adaptive_difficulty/arms.py](../../../../../../src/learnloop/adaptive_difficulty/arms.py), line 45)
- `NOLESSON` ([src/learnloop/adaptive_difficulty/arms.py](../../../../../../src/learnloop/adaptive_difficulty/arms.py), line 47)
- `HYPER_FINE` ([src/learnloop/adaptive_difficulty/arms.py](../../../../../../src/learnloop/adaptive_difficulty/arms.py), line 48)
- `GRID` ([src/learnloop/adaptive_difficulty/arms.py](../../../../../../src/learnloop/adaptive_difficulty/arms.py), line 49)
- `FIELD_ARMS` ([src/learnloop/adaptive_difficulty/arms.py](../../../../../../src/learnloop/adaptive_difficulty/arms.py), line 50)
- `DEFAULT_ARMS` ([src/learnloop/adaptive_difficulty/arms.py](../../../../../../src/learnloop/adaptive_difficulty/arms.py), line 51)
- `GRID_POINTS` ([src/learnloop/adaptive_difficulty/arms.py](../../../../../../src/learnloop/adaptive_difficulty/arms.py), line 53)

### Explicit exports

`__all__` declares:

- `DEFAULT_ARMS`
- `FIELD_ARMS`
- `GRID`
- `HYPER_FINE`
- `LO`
- `NOLESSON`
- `NOREAD`
- `NOVERDICT`
- `Record`
- `SUBJECT`
- `UNIFORM`
- `hyper_fixed_name`
- `prequential`

## Internal implementation anchors

- `_p(view: View, spec: Any, warmth: float, weights: np.ndarray | None=None) -> tuple[float, np.ndarray]` ([source](../../../../../../src/learnloop/adaptive_difficulty/arms.py), line 91)
- `_uniform_weights(view: View) -> np.ndarray` ([source](../../../../../../src/learnloop/adaptive_difficulty/arms.py), line 99)
- `_run(events: RP.Events, settings: RP.ReplaySettings, *, base: bool, sink: dict[str, Record], names: Mapping[str, str], grid: '_GridArm | None'=None) -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/arms.py), line 104)
- `class _GridArm` ([source](../../../../../../src/learnloop/adaptive_difficulty/arms.py), line 132) — ``:grid``: a QUEST+-exact grid for each cell's ability (cold-start prior), demand from the subject view's posterior feature effects and signal weights, learning at ``E[γ]``.
- `_field_arms(connection: Any, vault: Any, view: Any, sink: dict[str, Record]) -> dict[str, int]` ([source](../../../../../../src/learnloop/adaptive_difficulty/arms.py), line 170) — Field's ``mastery_ekf`` and ``lo_general`` on field's rows (read through AD's history fallback), prequentially (predict, observe).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]] — imports `module`; statically calls `prequential`
- [[Reference/Modules/learnloop/cli/ad|learnloop.cli.ad]] — imports `module`; statically calls `prequential`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `material_view`; calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/model|learnloop.adaptive_difficulty.model]] — imports `module`; calls `category_likelihood`, `expected_success`, `residual_success`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `entry`; calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `module`; calls `feature_coding`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; calls `load_events`, `run`
- [[Reference/Modules/learnloop/adaptive_difficulty/state|learnloop.adaptive_difficulty.state]] — imports `View`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `history_fallback`; calls `history_fallback`
- [[Reference/Modules/learnloop/field/predictors|learnloop.field.predictors]] — imports `create_predictor`; calls `create_predictor`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]], [[Reference/Modules/learnloop/cli/ad|learnloop.cli.ad]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_fix_r5.py](../../../../../../tests/test_ad23_fix_r5.py) — direct import
  - `test_the_report_forecasts_with_the_configured_coupling`
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_readiness_errors_read_each_report_window`
  - `test_the_grid_arm_never_reads_a_later_answer`
- [tests/test_ad3_monitoring.py](../../../../../../tests/test_ad3_monitoring.py) — direct import
  - `test_monitoring_applies_field_rule_as_monitor_never_gate`

## Modification guidance

- Make changes here when the responsibility remains arms within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/arms.py](../../../../../../src/learnloop/adaptive_difficulty/arms.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
