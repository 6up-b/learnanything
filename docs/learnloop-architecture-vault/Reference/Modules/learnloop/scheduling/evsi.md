---
title: "learnloop.scheduling.evsi"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/evsi.py"
source_paths:
  - "src/learnloop/scheduling/evsi.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.evsi module"
  - "src/learnloop/scheduling/evsi.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.evsi`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.evsi` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 step 3 -- robust expected value of sample information (EVSI), spec §6.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/evsi.py](../../../../../../src/learnloop/scheduling/evsi.py) |
| Source lines | 672 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class EVSIInputError(ValueError)` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 68) — An EVSI input is missing or fabricated; the value must not be computed.
  - `__init__(self, reason: str, detail: Sequence[str]=()) -> None` (line 78; internal)
- `shared_optimal_action(loss_table: AL.LossTable, *, tol: float=1e-09) -> str | None` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 99) — The action that is argmin loss for EVERY hypothesis individually (§6.2).
- `class MemberEVSI` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 118)
- `evsi_for_conditionals(conditionals: Mapping[str, Mapping[str, float]], prior: Mapping[str, float], loss_table: AL.LossTable) -> MemberEVSI` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 124) — EVSI over one ``P(E|H)`` table (spec §6.3).
- `class RobustEVSI` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 173) — Robust EVSI products for one candidate question (spec §6.3/§6.5), persistable.
  - `as_dict(self) -> dict[str, Any]` (line 185; public)
- `robust_evsi(members: Sequence[Mapping[str, Mapping[str, float]]], prior: Mapping[str, float], loss_table: AL.LossTable, *, quantile: float=ROBUST_QUANTILE) -> RobustEVSI` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 199) — Robust EVSI over a credible set of ``P(E|H)`` matrices.
- `stress_matrices(conditionals: Mapping[str, Mapping[str, float]], delta: float=PERTURBATION_DELTA) -> list[dict[str, dict[str, float]]]` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 276) — Two deterministic ±``delta`` per-row perturbations of a ``P(E|H)`` table (§6.5).
- `class DiagnosticCandidate` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 293) — One feasible diagnostic question, already admitted by the constraint engine.
- `class RankedCandidate` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 310)
- `class RankResult` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 320)
  - `as_dict(self) -> dict[str, Any]` (line 334; public)
- `rank_feasible(candidates: Sequence[DiagnosticCandidate], loss_table: AL.LossTable, *, quantile: float=ROBUST_QUANTILE, lambda_time: float=LAMBDA_TIME, burden_cost: float=BURDEN_COST, perturbation_delta: float=PERTURBATION_DELTA) -> RankResult` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 366) — Rank feasible diagnostic questions by robust EVSI per minute and apply the LCB stop rule (spec §6.4).
- `joint_conditionals(tables: Sequence[Mapping[str, Mapping[Any, float]]], hypotheses: Sequence[str]) -> dict[str, dict[tuple[Any, ...], float]]` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 512) — ``P(e_1, ..., e_k | h)`` for checks conditionally independent given the hypothesis: the product of their ``P(E | H)`` rows.
- `class BatchEVSI` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 535) — The robust EVSI of k checks asked together (minutes), persistable.
  - `k(self) -> int` (line 556; public)
  - `pays(self) -> bool` (line 560; public)
  - `as_dict(self) -> dict[str, Any]` (line 563; public)
- `robust_batch_evsi(candidates: Sequence[DiagnosticCandidate], loss_table: AL.LossTable, *, k: int, quantile: float=ROBUST_QUANTILE, lambda_time: float=LAMBDA_TIME, burden_cost: float=BURDEN_COST) -> BatchEVSI` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 580) — Robust EVSI of the first ``k`` candidates asked together.

### Module constants

- `EVSI_SCHEMA_VERSION` ([src/learnloop/scheduling/evsi.py](../../../../../../src/learnloop/scheduling/evsi.py), line 50)
- `PERTURBATION_DELTA` ([src/learnloop/scheduling/evsi.py](../../../../../../src/learnloop/scheduling/evsi.py), line 54)
- `LIVE_VALUE_PRIOR_BASES` ([src/learnloop/scheduling/evsi.py](../../../../../../src/learnloop/scheduling/evsi.py), line 65)

## Internal implementation anchors

- `_normalized_prior(prior: Mapping[str, float], hypotheses: Sequence[str]) -> dict[str, float]` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 89)
- `_perturb_row(row: Mapping[str, float], delta: float, *, toward_mode: bool) -> dict[str, float]` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 254) — Move ``delta`` probability mass between the modal and the least-likely emission of a row, then renormalize (bounded ±0.15, renormalized per row, §6.5).
- `_rank_value(ev: RobustEVSI, expected_minutes: float, burden_minutes: float) -> float` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 353)
- `_stop_threshold(c: 'DiagnosticCandidate', lambda_time: float, burden_cost: float) -> float` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 358) — Minutes the robust EVSI must clear to be worth measuring (spec §6.4): the minutes-numeraire time cost PLUS this candidate's own administration burden (matching the ranking denominator), plus the global burden floor.
- `_action_flips_under_stress(best: DiagnosticCandidate, loss_table: AL.LossTable, delta: float) -> bool` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 459) — Does the winning candidate's per-emission recommended action flip between its nominal mean-member table and either ±``delta`` stressed table?
- `_winner_flips_under_stress(scored: Sequence[tuple[DiagnosticCandidate, RobustEVSI, float]], loss_table: AL.LossTable, quantile: float, delta: float, lambda_time: float, burden_cost: float) -> bool` ([source](../../../../../../src/learnloop/scheduling/evsi.py), line 485)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/causal_diagnostic_selector|learnloop.diagnosis.causal_diagnostic_selector]] — imports `module`; statically calls `DiagnosticCandidate`, `EVSIInputError`, `evsi_for_conditionals`, `rank_feasible`
- [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]] — imports `module`; statically calls `DiagnosticCandidate`, `rank_feasible`, `robust_batch_evsi`
- [[Reference/Modules/learnloop/evsi_calibration/experiments|learnloop.evsi_calibration.experiments]] — imports `module`
- [[Reference/Modules/learnloop/evsi_calibration/multisim|learnloop.evsi_calibration.multisim]] — imports `module`; statically calls `evsi_for_conditionals`
- [[Reference/Modules/learnloop/evsi_calibration/policies|learnloop.evsi_calibration.policies]] — imports `module`; statically calls `DiagnosticCandidate`, `evsi_for_conditionals`, `rank_feasible`
- [[Reference/Modules/learnloop/evsi_calibration/simulate|learnloop.evsi_calibration.simulate]] — imports `module`; statically calls `evsi_for_conditionals`
- [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]] — imports `module`; statically calls `DiagnosticCandidate`, `EVSIInputError`, `evsi_for_conditionals`, `rank_feasible`, `shared_optimal_action`, `stress_matrices`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `module`; statically calls `DiagnosticCandidate`, `rank_feasible`
- [[Reference/Modules/learnloop/scheduling/voi_forecasts|learnloop.scheduling.voi_forecasts]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/diagnosis/robust_composition|learnloop.diagnosis.robust_composition]] — imports `BURDEN_COST`, `LAMBDA_TIME`, `ROBUST_QUANTILE`, `robust_quantile`; calls `robust_quantile`
- [[Reference/Modules/learnloop/scheduling/action_loss|learnloop.scheduling.action_loss]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/causal_diagnostic_selector|learnloop.diagnosis.causal_diagnostic_selector]], [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]], [[Reference/Modules/learnloop/evsi_calibration/experiments|learnloop.evsi_calibration.experiments]], [[Reference/Modules/learnloop/evsi_calibration/multisim|learnloop.evsi_calibration.multisim]], [[Reference/Modules/learnloop/evsi_calibration/policies|learnloop.evsi_calibration.policies]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_evsi.py](../../../../../../tests/test_evsi.py) — direct import
  - `test_burden_can_make_net_value_non_positive_without_negative_evsi`
  - `test_downstream_action_flip_across_members_abstains`
  - `test_evsi_is_positive_on_a_separating_question`
  - `test_evsi_is_zero_when_hypotheses_share_optimal_action`
  - `test_lcb_stop_directionality`
  - `test_members_that_agree_on_action_do_not_abstain`
  - `test_no_pze_substitution_uses_composed_pe_given_h`
  - `test_perturbation_flip_causes_abstention`
  - `test_ranking_uses_per_minute_while_stop_uses_absolute_value`
  - `test_stop_rule_uses_per_candidate_burden`
  - `test_stress_that_reverses_recommended_action_abstains`
- [tests/test_evsi_calibration_sim.py](../../../../../../tests/test_evsi_calibration_sim.py) — direct import
  - `test_simulation_runs_every_policy_on_common_random_numbers`
- [tests/test_evsi_fail_closed.py](../../../../../../tests/test_evsi_fail_closed.py) — direct import
  - `test_all_candidates_excluded_is_an_abstention_never_a_confident_stop`
  - `test_incomplete_candidate_is_excluded_and_the_rest_still_rank`
  - `test_positive_mass_hypothesis_missing_from_the_loss_table_aborts_the_value`
  - `test_positive_mass_hypothesis_without_a_likelihood_row_aborts_the_value`
  - `test_uniform_fallback_prior_is_excluded_from_live_value_ranking`
  - `test_zero_mass_hypothesis_may_be_absent_without_aborting`
  - `test_zero_mass_prior_is_refused_not_replaced_with_a_uniform`
- [tests/test_voi_v2.py](../../../../../../tests/test_voi_v2.py) — direct import
  - `test_rank_feasible_values_the_episode_at_the_configured_quantile`
  - `test_robust_batch_evsi_is_the_robust_quantile_of_the_joint_evsi_per_member`
  - `test_the_batch_value_equals_the_product_tables_evsi_on_the_real_credible_sets`

## Modification guidance

- Change evsi policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/evsi.py](../../../../../../src/learnloop/scheduling/evsi.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
