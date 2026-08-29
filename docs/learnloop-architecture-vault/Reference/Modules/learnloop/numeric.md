---
title: "learnloop.numeric"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/numeric.py"
source_paths:
  - "src/learnloop/numeric.py"
source_commit: "49f8dc415492edd91c09d47c911fc1530c675242"
source_commit_timestamp: "2026-07-27T02:40:21-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop"
layer: "primitive"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.numeric module"
  - "src/learnloop/numeric.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/primitive"
  - "package/learnloop"
---

# `learnloop.numeric`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps numeric behavior inside its owning package, [[Reference/Modules/learnloop/_package|learnloop]]. Its public surface centers on `clamp`, `sigmoid`, `empirical_quantile`, `percentiles`, `beta_mean`, `regularized_incomplete_beta`, `beta_quantile`, `binomial_two_sided_p`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/numeric.py](../../../../../src/learnloop/numeric.py) |
| Source lines | 169 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `primitive` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `49f8dc415492edd91c09d47c911fc1530c675242` |
| Commit timestamp | `2026-07-27T02:40:21-04:00` |

## Public API

- `clamp(value: float, low: float=0.0, high: float=1.0) -> float` ([source](../../../../../src/learnloop/numeric.py), line 7)
- `sigmoid(x: float) -> float` ([source](../../../../../src/learnloop/numeric.py), line 11)
- `empirical_quantile(values: Sequence[float], q: float) -> float` ([source](../../../../../src/learnloop/numeric.py), line 18) — Linear-interpolation empirical quantile (matches numpy's 'linear' method).
- `percentiles(values: Sequence[float], qs: Sequence[float]=(0.1, 0.25, 0.5, 0.75, 0.9)) -> dict[float, float]` ([source](../../../../../src/learnloop/numeric.py), line 34)
- `beta_mean(alpha: float, beta: float) -> float` ([source](../../../../../src/learnloop/numeric.py), line 43) — Mean of a Beta(alpha, beta) distribution.
- `regularized_incomplete_beta(x: float, a: float, b: float) -> float` ([source](../../../../../src/learnloop/numeric.py), line 51) — Regularized incomplete beta function I_x(a, b) = Beta CDF at x.
- `beta_quantile(q: float, alpha: float, beta: float) -> float` ([source](../../../../../src/learnloop/numeric.py), line 115) — Inverse Beta CDF (ppf) by bisection on the monotone regularized I_x.
- `binomial_two_sided_p(successes: int, trials: int, p: float=0.5) -> float` ([source](../../../../../src/learnloop/numeric.py), line 142) — Exact two-sided binomial tail probability under ``p`` (small ``trials``).

## Internal implementation anchors

- `_beta_continued_fraction(x: float, a: float, b: float) -> float` ([source](../../../../../src/learnloop/numeric.py), line 72) — Lentz continued fraction for the incomplete beta (NR §6.4, betacf).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/ability_transition|learnloop.attempts.ability_transition]] — imports `clamp`; statically calls `clamp`
- [[Reference/Modules/learnloop/attempts/surprise|learnloop.attempts.surprise]] — imports `clamp`; statically calls `clamp`
- [[Reference/Modules/learnloop/content/authoring/conjunctive_items|learnloop.content.authoring.conjunctive_items]] — imports `clamp`; statically calls `clamp`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `beta_mean`, `beta_quantile`; statically calls `beta_mean`, `beta_quantile`
- [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]] — imports `binomial_two_sided_p`; statically calls `binomial_two_sided_p`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_gate|learnloop.diagnosis.diagnostic_gate]] — imports `beta_quantile`; statically calls `beta_quantile`
- [[Reference/Modules/learnloop/diagnosis/gate_fit|learnloop.diagnosis.gate_fit]] — imports `sigmoid`; statically calls `sigmoid`
- [[Reference/Modules/learnloop/diagnosis/gate_score|learnloop.diagnosis.gate_score]] — imports `sigmoid`; statically calls `sigmoid`
- [[Reference/Modules/learnloop/diagnosis/signal_quantiles|learnloop.diagnosis.signal_quantiles]] — imports `empirical_quantile`; statically calls `empirical_quantile`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `clamp`; statically calls `clamp`
- [[Reference/Modules/learnloop/learner/blueprint_projection|learnloop.learner.blueprint_projection]] — imports `clamp`; statically calls `clamp`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `clamp`; statically calls `clamp`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `clamp`; statically calls `clamp`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `clamp`; statically calls `clamp`
- [[Reference/Modules/learnloop/scheduling/evaluation|learnloop.scheduling.evaluation]] — imports `percentiles`; statically calls `percentiles`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `clamp`; statically calls `clamp`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `clamp`; statically calls `clamp`
- [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]] — imports `clamp`; statically calls `clamp`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/ability_transition|learnloop.attempts.ability_transition]], [[Reference/Modules/learnloop/attempts/surprise|learnloop.attempts.surprise]], [[Reference/Modules/learnloop/content/authoring/conjunctive_items|learnloop.content.authoring.conjunctive_items]], [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]] and 13 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_numeric.py](../../../../../tests/test_numeric.py) — direct import
  - `test_beta_mean`
  - `test_beta_quantile_high_evidence_tracks_mean`
  - `test_beta_quantile_rejects_bad_inputs`
  - `test_beta_quantile_uniform`
  - `test_clamp_bounds`
  - `test_empirical_quantile_even_n_interpolates`
  - `test_empirical_quantile_odd_n`
  - `test_empirical_quantile_rejects_bad_inputs`
  - `test_empirical_quantile_single_element`
  - `test_empirical_quantile_unsorted_input`
  - `test_percentiles_custom_qs`
  - `test_percentiles_defaults_and_empty`
  - `test_regularized_incomplete_beta_matches_uniform_cdf`
  - `test_sigmoid_symmetry_and_bounds`
- [tests/test_signal_quantiles.py](../../../../../tests/test_signal_quantiles.py) — direct import
  - `test_quantile_resolution_with_enough_samples`
  - `test_severity_quantile_reads_gate_diagnostics`

## Modification guidance

- Make changes here when the responsibility remains numeric within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/numeric.py](../../../../../src/learnloop/numeric.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
