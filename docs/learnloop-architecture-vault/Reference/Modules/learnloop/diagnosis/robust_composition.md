---
title: "learnloop.diagnosis.robust_composition"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/robust_composition.py"
source_paths:
  - "src/learnloop/diagnosis/robust_composition.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.robust_composition module"
  - "src/learnloop/diagnosis/robust_composition.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.robust_composition`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.robust_composition` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Robust diagnostic composition (spec_p0_measurement_correctness §4.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/robust_composition.py](../../../../../../src/learnloop/diagnosis/robust_composition.py) |
| Source lines | 501 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `decision_context_hash(*, episode_id: str | None, candidate_card_version: str | None, resolved_slot_map: Mapping[str, str] | None, posterior_at_selection: Mapping[str, float] | None, projection_algorithm_version: str, draw_count: int=ROBUST_DRAW_COUNT, quantile: float=ROBUST_QUANTILE, perturbation_concentration: float=INSTRUMENT_PERTURBATION_CONCENTRATION) -> str` ([source](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 71) — Canonical 32-char hash pinning the decision inputs + registered params so the ensemble is a pure function of the pinned decision (§1.4).
- `robust_quantile(values: Sequence[float], quantile: float=ROBUST_QUANTILE) -> float` ([source](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 107) — Empirical lower quantile (§4.2).
- `compose_emission_over_hypotheses(emission_given_z: Mapping[str, Mapping[str, float]], instrument_rows: Mapping[str, Mapping[str, float]]) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 124) — ``P(E | H) = sum_z P(E | Z) P(Z | H, card)`` (§1.2).
- `class Ensemble` ([source](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 191) — A deterministic ensemble of composed ``P(E | H)`` tables (member 0 = the posterior-mean, un-perturbed decision; members 1..N = draws).
  - `mean_member(self) -> dict[str, dict[str, float]]` (line 206; public)
- `build_ensemble(*, joint_alpha: Mapping[str, Mapping[str, float]], instrument_rows: Mapping[str, Mapping[str, float]], calibration_model_hash: str, decision_context_hash: str, draw_count: int=ROBUST_DRAW_COUNT, quantile: float=ROBUST_QUANTILE, perturbation_concentration: float=INSTRUMENT_PERTURBATION_CONCENTRATION) -> Ensemble` ([source](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 210) — Build the deterministic composition ensemble (§1.3).
- `expected_information_gain(conditionals: Mapping[str, Mapping[str, float]], posterior: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 260) — Hypothesis EIG in nats over a composed ``P(E | H)`` table -- the same math as ``probe_families.instrument_expected_information_gain`` but over emissions.
- `observed_update(conditionals: Mapping[str, Mapping[str, float]], posterior: Mapping[str, float], observed_emission: str) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 293) — One Bayes step ``P(H | E) ∝ P(E | H) P(H)`` at the realized emission.
- `class RobustDecision` ([source](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 316) — Robust products of one selection decision, snapshotted so historical replay never re-runs the ensemble (§2.1/§3.3).
- `robust_eig_per_second(ensemble: Ensemble, posterior: Mapping[str, float], expected_seconds: float, quantile: float | None=None) -> float` ([source](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 341) — 10th-percentile of per-draw EIG per expected second (the robust rank score).
- `evaluate_selection(*, candidates: Sequence[tuple[str, Ensemble, float]], posterior: Mapping[str, float], lambda_time: float=LAMBDA_TIME, burden_cost: float=BURDEN_COST, value_per_nat_minutes: float=VALUE_PER_NAT_MINUTES, agreement_threshold: float=ENSEMBLE_ACTION_AGREEMENT_THRESHOLD) -> RobustDecision` ([source](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 353) — Robust selection over candidate instruments (§3.1/§3.2).
- `certainty_lcb(*, joint_alpha: Mapping[str, Mapping[str, float]], observed_emission: str, calibration_model_hash: str, decision_context_hash: str, prior: Mapping[str, float] | None=None, draw_count: int=ROBUST_DRAW_COUNT, quantile: float=ROBUST_QUANTILE) -> float` ([source](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 455) — Lower credible bound of ``certainty = 1 - H(P(Z|E))/log K`` across the calibration ensemble (§4.3).

### Module constants

- `ROBUST_DRAW_COUNT` ([src/learnloop/diagnosis/robust_composition.py](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 43)
- `ROBUST_QUANTILE` ([src/learnloop/diagnosis/robust_composition.py](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 44)
- `INSTRUMENT_PERTURBATION_CONCENTRATION` ([src/learnloop/diagnosis/robust_composition.py](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 45)
- `ENSEMBLE_ACTION_AGREEMENT_THRESHOLD` ([src/learnloop/diagnosis/robust_composition.py](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 46)
- `ABSTENTION_BUDGET_FRACTION` ([src/learnloop/diagnosis/robust_composition.py](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 47)
- `LAMBDA_TIME` ([src/learnloop/diagnosis/robust_composition.py](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 48)
- `BURDEN_COST` ([src/learnloop/diagnosis/robust_composition.py](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 49)
- `VALUE_PER_NAT_MINUTES` ([src/learnloop/diagnosis/robust_composition.py](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 55)

## Internal implementation anchors

- `_seed_int(calibration_model_hash: str, decision_context_hash: str) -> int` ([source](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 58) — Stable, platform-independent seed from the pinned hashes (§1.4).
- `_dirichlet(rng: random.Random, alpha: Sequence[float]) -> list[float]` ([source](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 101)
- `_normalized_mean_emission(joint_alpha: Mapping[str, Mapping[str, float]]) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 148) — Posterior-mean ``P(E | Z)`` = normalized alpha rows (member 0).
- `_draw_emission(rng: random.Random, joint_alpha: Mapping[str, Mapping[str, float]]) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 160) — One Dirichlet draw of ``P(E | Z)`` per true class Z.
- `_perturb_instrument(rng: random.Random, instrument_rows: Mapping[str, Mapping[str, float]], concentration: float) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 173) — Dirichlet perturbation around each authored instrument row (§4.2).
- `_ensemble_eig_per_second(ensemble: Ensemble, posterior: Mapping[str, float], expected_seconds: float) -> list[float]` ([source](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 329)
- `_certainty(posterior: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/diagnosis/robust_composition.py), line 444)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/effective_observation|learnloop.attempts.effective_observation]] — imports `module`; statically calls `certainty_lcb`, `decision_context_hash`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `robust_eig_per_second`; statically calls `robust_eig_per_second`
- [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] — imports `module`; statically calls `build_ensemble`, `decision_context_hash`, `evaluate_selection`, `observed_update`
- [[Reference/Modules/learnloop/scheduling/evsi|learnloop.scheduling.evsi]] — imports `BURDEN_COST`, `LAMBDA_TIME`, `ROBUST_QUANTILE`, `robust_quantile`; statically calls `robust_quantile`
- [[Reference/Modules/learnloop/sim/grader_confusion|learnloop.sim.grader_confusion]] — imports `module`; statically calls `build_ensemble`, `decision_context_hash`, `observed_update`
- [[Reference/Modules/learnloop/sim/interval_width_viability|learnloop.sim.interval_width_viability]] — imports `module`; statically calls `build_ensemble`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`; calls `canonical_hash`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `math`, `random`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/effective_observation|learnloop.attempts.effective_observation]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]], [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]], [[Reference/Modules/learnloop/scheduling/evsi|learnloop.scheduling.evsi]], [[Reference/Modules/learnloop/sim/grader_confusion|learnloop.sim.grader_confusion]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_effective_observation.py](../../../../../../tests/test_effective_observation.py) — direct import
  - `test_uniform_posterior_yields_zero_certification_mass`
- [tests/test_evsi.py](../../../../../../tests/test_evsi.py) — direct import
  - `test_no_pze_substitution_uses_composed_pe_given_h`
- [tests/test_interval_width_viability.py](../../../../../../tests/test_interval_width_viability.py) — direct import
  - `test_heuristic_width_keeps_abstention_within_budget`
- [tests/test_p0_projection_cutover.py](../../../../../../tests/test_p0_projection_cutover.py) — direct import
  - `test_mvp08_mastery_reliability_sources_certainty_lcb`
- [tests/test_probe_robust_cutover.py](../../../../../../tests/test_probe_robust_cutover.py) — direct import
  - `test_episode_pins_channel_and_products_are_deterministic`
- [tests/test_robust_composition.py](../../../../../../tests/test_robust_composition.py) — direct import
  - `test_composition_marginalizes_true_class`
  - `test_discriminating_instrument_wins_and_acts`
  - `test_ensemble_is_deterministic_and_byte_stable`
  - `test_indistinguishable_candidates_abstain`
  - `test_robust_quantile_is_lower_tail`
  - `test_robust_quantile_uses_nearest_rank_ceil`
  - `test_uninformative_instrument_triggers_stop`
- [tests/test_robust_composition_bench.py](../../../../../../tests/test_robust_composition_bench.py) — direct import

## Modification guidance

- Change robust composition policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/robust_composition.py](../../../../../../src/learnloop/diagnosis/robust_composition.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
