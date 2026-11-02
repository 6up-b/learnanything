---
title: "learnloop.sim.ad_gates"
type: "module-reference"
status: "current"
refactor_status: "EVALUATION"
version: "1.0.0"
source_path: "src/learnloop/sim/ad_gates.py"
source_paths:
  - "src/learnloop/sim/ad_gates.py"
source_commit: "2778e23fe57cb9e86780e5e1e0b93ad814872e6e"
source_commit_timestamp: "2026-10-19T00:49:53-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.sim"
layer: "simulation"
concepts:
  - "Learning System"
workflows:
  []
aliases:
  - "learnloop.sim.ad_gates module"
  - "src/learnloop/sim/ad_gates.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/evaluation"
  - "layer/simulation"
  - "package/learnloop-sim"
---

# `learnloop.sim.ad_gates`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.sim.ad_gates` exists within [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] to own the behavior summarized by its module contract: AD2+AD3's simulation gates as metrics (spec_adaptive_difficulty_v1 §14; pre-registration §1.5-1.9).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/sim/ad_gates.py](../../../../../../src/learnloop/sim/ad_gates.py) |
| Source lines | 394 |
| Owning package | [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] |
| Architecture layer | `simulation` |
| Refactor status | `EVALUATION` |
| Worktree state | `clean` |
| Source commit | `2778e23fe57cb9e86780e5e1e0b93ad814872e6e` |
| Commit timestamp | `2026-10-19T00:49:53-04:00` |

> [!note] Evaluation-only authority
> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.

## Public API

- `g_ad2_18(scenario: str, *, n: int=200) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/ad_gates.py), line 38)
- `g_ad2_7(*, n: int=200) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/ad_gates.py), line 81)
- `g_ad2_8(*, n: int=200) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/ad_gates.py), line 89)
- `g_ad2_14(*, n: int=200) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/ad_gates.py), line 109)
- `g_ad3_6(point: P.HyperPoint, *, seeds: int=25) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/ad_gates.py), line 122)
- `g_ad3_7(flow: str, proposal_kind: str, *, n: int=200) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/ad_gates.py), line 131)
- `g_ad3_7_shrink(proposal_kind: str, *, n: int=200) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/ad_gates.py), line 167)
- `g_ad3_8(*, n: int=200) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/ad_gates.py), line 195)
- `g_ad3_11(scenario: str, *, floor: float=0.1, n: int=200) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/ad_gates.py), line 220)
- `g_ad3_15(*, n: int=200) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/ad_gates.py), line 268)
- `g_ad3_9(*, seeds: int=200, attempts: int=300) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/ad_gates.py), line 285) — Flags on synthetic logs: the worse model 0.15 nats worse per first attempt over 300 first attempts (and the other flags' stated conditions); none fires when nothing is worse.
- `main(argv: list[str]) -> int` ([source](../../../../../../src/learnloop/sim/ad_gates.py), line 378)

### Module constants

- `SUBJECT` ([src/learnloop/sim/ad_gates.py](../../../../../../src/learnloop/sim/ad_gates.py), line 25)
- `UNIFORM` ([src/learnloop/sim/ad_gates.py](../../../../../../src/learnloop/sim/ad_gates.py), line 26)
- `GATES` ([src/learnloop/sim/ad_gates.py](../../../../../../src/learnloop/sim/ad_gates.py), line 354)

### Explicit exports

`__all__` declares:

- `GATES`
- `g_ad2_14`
- `g_ad2_18`
- `g_ad2_7`
- `g_ad2_8`
- `g_ad3_11`
- `g_ad3_15`
- `g_ad3_6`
- `g_ad3_7`
- `g_ad3_7_shrink`
- `g_ad3_8`
- `g_ad3_9`
- `main`

## Internal implementation anchors

- `_bootstrap_mean(values: np.ndarray, *, samples: int=2000, seed: str='ad-sim-bootstrap') -> list[float]` ([source](../../../../../../src/learnloop/sim/ad_gates.py), line 29)
- `_reading_flag_and_losses(result: A.ReaderResult) -> tuple[np.ndarray, np.ndarray]` ([source](../../../../../../src/learnloop/sim/ad_gates.py), line 182)
- `_curve_coverage(result: A.ReaderResult, kind: str) -> np.ndarray` ([source](../../../../../../src/learnloop/sim/ad_gates.py), line 210)
- `_shift_for_excess_loss(target: float) -> float` ([source](../../../../../../src/learnloop/sim/ad_gates.py), line 334) — The logit shift whose expected excess log loss over the truth (p ~ U(0.3, 0.9)) is ``target``.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/dose_report|learnloop.adaptive_difficulty.dose_report]] — imports `module`; calls `label`, `offer_effect`
- [[Reference/Modules/learnloop/adaptive_difficulty/model|learnloop.adaptive_difficulty.model]] — imports `module`; calls `dose_basis`
- [[Reference/Modules/learnloop/adaptive_difficulty/monitoring|learnloop.adaptive_difficulty.monitoring]] — imports `module`; calls `band_missed_flag`, `band_region_error`, `comparison_flag`, `dose_burden_flag`, `log_loss_difference`, `readiness_flag`
- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `module`; calls `hyper_grid`
- [[Reference/Modules/learnloop/sim/ad_synthetic|learnloop.sim.ad_synthetic]] — imports `module`; calls `censoring`, `coding`, `feature_time_correlation`, `fitted_useful_dose`, `hyperparameters_learned`, `own_answers_before_band`, `readers`, `recovery`, `related_topics`, `rng_for`, `time_to_usable`, `true_curve`, `true_useful_dose`, `wrong_proposal_shrinks`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `math`, `sys`, `typing`
- Third party: `numpy`

## Larger workflow participation

No direct learner/operator workflow is assigned. This module is offline, shadow-only, dormant, or a dependency reached only through the static consumers below.

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_sim.py](../../../../../../tests/test_ad23_sim.py) — direct import
  - `test_auto_flags_fire_on_synthetic_logs`
  - `test_confound_detected_under_monotone_schedule`
  - `test_correct_proposal_raises_no_coupling_flag`
  - `test_feature_effects_recovered_under_overlap`
  - `test_help_and_reveal_are_censored_not_dropped`
  - `test_hyperparameters_learned_on_synthetic_vaults`
  - `test_randomized_offers_unconfounded`
  - `test_reading_downturn_found`
  - `test_reading_kind_effects_and_saturation_recovered`
  - `test_reading_raises_prediction_synthetic`
  - `test_related_topics_adapt_faster_practice_correct`
  - `test_related_topics_after_reading`
  - `test_self_check_verdicts_learned_synthetic`
  - `test_time_to_usable_one_cell`
  - `test_time_to_usable_plan_flow`
  - `test_time_to_usable_wrong_prior`
  - `test_unrelated_topics_not_dragged`
  - `test_wrong_proposal_shrinks`

## Modification guidance

- Make changes here when the responsibility remains ad gates within learnloop.sim; otherwise move the behavior to its owning boundary.
- Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/sim/ad_gates.py](../../../../../../src/learnloop/sim/ad_gates.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
