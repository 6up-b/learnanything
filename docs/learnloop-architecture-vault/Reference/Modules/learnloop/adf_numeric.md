---
title: "learnloop.adf_numeric"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adf_numeric.py"
source_paths:
  - "src/learnloop/adf_numeric.py"
source_commit: "9d62ab7f53d6bb534f5dc95bd840178ee1aba8a4"
source_commit_timestamp: "2026-11-01T18:45:27-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adf_numeric module"
  - "src/learnloop/adf_numeric.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.adf_numeric`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adf_numeric` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Assumed-density filtering primitives shared by adaptive difficulty and the lesson-check weight.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adf_numeric.py](../../../../../src/learnloop/adf_numeric.py) |
| Source lines | 118 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `9d62ab7f53d6bb534f5dc95bd840178ee1aba8a4` |
| Commit timestamp | `2026-11-01T18:45:27-05:00` |

## Public API

- `gauss_hermite(n: int) -> tuple[np.ndarray, np.ndarray]` ([source](../../../../../src/learnloop/adf_numeric.py), line 32) — ``n`` probabilists' Gauss-Hermite nodes and their weights, normalized to sum to 1.
- `sigmoid(x: np.ndarray | float) -> np.ndarray` ([source](../../../../../src/learnloop/adf_numeric.py), line 43)
- `logit(p: float) -> float` ([source](../../../../../src/learnloop/adf_numeric.py), line 48)
- `class FactorUpdate` ([source](../../../../../src/learnloop/adf_numeric.py), line 54) — One factor's effect: the projection's moments before and after, and ``log Z``.
- `adf_update(mean: np.ndarray, cov: np.ndarray, h: np.ndarray, log_likelihood: Callable[[np.ndarray], np.ndarray]) -> tuple[np.ndarray, np.ndarray, FactorUpdate]` ([source](../../../../../src/learnloop/adf_numeric.py), line 64) — One factor ``exp(log_likelihood(eta))`` on ``eta = h .
- `normalized_log_weights(log_w: np.ndarray) -> np.ndarray` ([source](../../../../../src/learnloop/adf_numeric.py), line 94) — Grid weights ``exp(log_w)`` normalized to sum to 1.
- `gaussian_sigmoid_mean(m: float, v: float) -> float` ([source](../../../../../src/learnloop/adf_numeric.py), line 102) — ``E[sigmoid(eta)]`` for ``eta ~ N(m, v)``, by the same quadrature.

### Explicit exports

`__all__` declares:

- `FactorUpdate`
- `NODES`
- `WEIGHTS`
- `adf_update`
- `gauss_hermite`
- `gaussian_sigmoid_mean`
- `logit`
- `normalized_log_weights`
- `sigmoid`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/model|learnloop.adaptive_difficulty.model]] — imports `gauss_hermite`, `sigmoid`; statically calls `sigmoid`
- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `NODES`, `WEIGHTS`, `sigmoid`; statically calls `sigmoid`
- [[Reference/Modules/learnloop/figures/prefetch_model|learnloop.figures.prefetch_model]] — imports `adf_update`, `normalized_log_weights`; statically calls `adf_update`, `normalized_log_weights`
- [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]] — imports `NODES`, `WEIGHTS`, `adf_update`, `gaussian_sigmoid_mean`, `logit`, `normalized_log_weights`, `sigmoid`; statically calls `adf_update`, `gaussian_sigmoid_mean`, `logit`, `normalized_log_weights`, `sigmoid`
- [[Reference/Modules/learnloop/router/lesson_suggestions|learnloop.router.lesson_suggestions]] — imports `adf_update`, `gaussian_sigmoid_mean`, `normalized_log_weights`, `sigmoid`; statically calls `adf_update`, `gaussian_sigmoid_mean`, `normalized_log_weights`, `sigmoid`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `sigmoid`; statically calls `sigmoid`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/model|learnloop.adaptive_difficulty.model]], [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]], [[Reference/Modules/learnloop/figures/prefetch_model|learnloop.figures.prefetch_model]], [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]], [[Reference/Modules/learnloop/router/lesson_suggestions|learnloop.router.lesson_suggestions]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_teacher_te1_weight.py](../../../../../tests/test_teacher_te1_weight.py) — direct import
  - `test_the_adf_quadrature_is_ads`

## Modification guidance

- Make changes here when the responsibility remains adf numeric within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adf_numeric.py](../../../../../src/learnloop/adf_numeric.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
