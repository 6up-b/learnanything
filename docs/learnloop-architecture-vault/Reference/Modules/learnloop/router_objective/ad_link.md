---
title: "learnloop.router_objective.ad_link"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/ad_link.py"
source_paths:
  - "src/learnloop/router_objective/ad_link.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router_objective.ad_link module"
  - "src/learnloop/router_objective/ad_link.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.ad_link`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.ad_link` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: The rollouts' link to adaptive difficulty: AD's own predicted success as a function of its latent ability (:class:`AdLink`), and AD's lesson dose curve as the decision read it (:class:`LessonCurve`).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/ad_link.py](../../../../../../src/learnloop/router_objective/ad_link.py) |
| Source lines | 190 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class AdLink` ([source](../../../../../../src/learnloop/router_objective/ad_link.py), line 24) — Landing ruling R9: AD's own predicted success ``F(η) = g + (1 − g − λ)·E_ε[σ(η − a·τ0·ε)]`` (``adaptive_difficulty.model.residual_success``), with ``g = 0`` (a valued topic's unseen constructed item), lapse ``λ``, and ``ε`` integrated by AD's own Gauss-Hermite rule; the caller h…
  - `__post_init__(self) -> None` (line 42; internal)
  - `quadrature(self, eta: np.ndarray, *, slope: bool=True) -> tuple[np.ndarray, np.ndarray | None]` (line 48; public) — ``F(η)`` and (``slope``) ``dF/dη`` from **one** evaluation of the quadrature's sigmoids, elementwise over any array of ``η`` (router speed, item 1: a caller stacks every ``η`` it needs, the draws' and the belief's, into one array).
  - `p(self, eta: np.ndarray) -> np.ndarray` (line 59; public)
  - `slope(self, eta: np.ndarray) -> np.ndarray` (line 62; public) — ``dF/dη``.
  - `p_integrated(self, mean: np.ndarray, variance: np.ndarray) -> np.ndarray` (line 67; public) — ``E[F(η)]`` for ``η ~ N(mean, variance)``: ``F`` with the residual's spread widened to ``√(a²τ0² + variance)``, AD's own ``expected_success`` (R10).
  - `inverse(self, p: np.ndarray, variance: np.ndarray | float=0.0) -> np.ndarray` (line 76; public) — The mean whose variance-integrated predictive is ``p`` (``F⁻¹(p)`` at variance 0), by bisection on AD's range (a ``p`` at or past ``1 − λ`` is held just inside it).
  - `logit_and_slope(self, eta: np.ndarray) -> tuple[np.ndarray, np.ndarray]` (line 92; public) — ``logit F(η)`` (AD's predictive on the combiner's scale) and its derivative in ``η``, never clipped (landing ruling R11: the combiner's own probability-logit, not FSRS's), the derivative the one of the transformation applied, ``F'/F + F'/(1 − F)``.
  - `logit_and_slope_from(self, eta: np.ndarray, f: np.ndarray, df: np.ndarray) -> tuple[np.ndarray, np.ndarray]` (line 102; public) — :meth:`logit_and_slope` from ``F(η)`` and ``dF/dη`` already computed (:meth:`quadrature`).
  - `logit_p(self, eta: np.ndarray) -> np.ndarray` (line 116; public) — ``logit F(η)`` alone, as :meth:`logit_and_slope` computes it (the rollouts' forecast path).
  - `logit_p_from(self, eta: np.ndarray, f: np.ndarray) -> np.ndarray` (line 121; public) — :meth:`logit_p` from ``F(η)`` already computed (:meth:`quadrature`).
  - `_logit_and_slope_logspace(self, eta: np.ndarray) -> tuple[np.ndarray, np.ndarray]` (line 132; internal) — The same in log space: ``log F``, ``log(1 − F) = log(λ + (1 − λ)·E[σ(−e)])`` and ``log F'``.
- `class LessonCurve` ([source](../../../../../../src/learnloop/router_objective/ad_link.py), line 154) — Teacher TE3a (spec_teacher_v1 rev 5 §14.2): AD's ``lesson`` dose curve per ``landed`` dose, as the decision read it (``readiness.decision_state_fields``' ``lesson_curve``): its two coefficients' posterior mean and covariance on :attr:`Learning.dose_scales`, their seeded prior's…
  - `deviation(self, n: np.ndarray, scales: tuple[float, float]) -> tuple[np.ndarray, np.ndarray]` (line 175; public) — ``(Δμ(n), Δv(n))`` per draw at positions ``n``: zero (exactly) while the curve is at its prior.

### Module constants

- `AD_LINK_VERSION` ([src/learnloop/router_objective/ad_link.py](../../../../../../src/learnloop/router_objective/ad_link.py), line 20)

### Explicit exports

`__all__` declares:

- `AD_LINK_VERSION`
- `AdLink`
- `LessonCurve`

## Internal implementation anchors

- `_logsumexp(x: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/router_objective/ad_link.py), line 146) — ``log Σ exp(x)`` over the last axis, stably.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`; statically calls `AdLink`, `LessonCurve`
- [[Reference/Modules/learnloop/router_objective/trace_assembly|learnloop.router_objective.trace_assembly]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/types|learnloop.router_objective.types]] — imports `AdLink`, `LessonCurve`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router_objective/memory|learnloop.router_objective.memory]] — imports `sigmoid`; calls `sigmoid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `math`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]], [[Reference/Modules/learnloop/router_objective/trace_assembly|learnloop.router_objective.trace_assembly]], [[Reference/Modules/learnloop/router_objective/types|learnloop.router_objective.types]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/rospeed_ad_link_helpers.py](../../../../../../tests/rospeed_ad_link_helpers.py) — direct import
- [tests/test_rofu_ad_latent.py](../../../../../../tests/test_rofu_ad_latent.py) — direct import
- [tests/test_rofu_ad_link.py](../../../../../../tests/test_rofu_ad_link.py) — direct import
  - `test_the_numeric_policy_reads_ads_own_predictive_only_with_its_switch`
- [tests/test_rofu_ad_stable.py](../../../../../../tests/test_rofu_ad_stable.py) — direct import
- [tests/test_rospeed2_connections.py](../../../../../../tests/test_rospeed2_connections.py) — direct import
- [tests/test_rospeed_ad_link.py](../../../../../../tests/test_rospeed_ad_link.py) — direct import
- [tests/test_te3a_lesson_opportunity.py](../../../../../../tests/test_te3a_lesson_opportunity.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains ad link within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/ad_link.py](../../../../../../src/learnloop/router_objective/ad_link.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
