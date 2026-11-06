---
title: "learnloop.adaptive_difficulty.model"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/model.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/model.py"
source_commit: "04d1b40e19aa935b9233c007868ca3c58d217e99"
source_commit_timestamp: "2026-11-06T04:58:47-05:00"
source_worktree_state: "clean"
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
  - "learnloop.adaptive_difficulty.model module"
  - "src/learnloop/adaptive_difficulty/model.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.model`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.model` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: AD's model: a bank of Gaussian filters over one event skeleton (spec_adaptive_difficulty_v1 §5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/model.py](../../../../../../src/learnloop/adaptive_difficulty/model.py) |
| Source lines | 763 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `04d1b40e19aa935b9233c007868ca3c58d217e99` |
| Commit timestamp | `2026-11-06T04:58:47-05:00` |

## Public API

- `category_likelihood(eta: np.ndarray, guess: np.ndarray, category: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 69) — ``P(Y = category | η)`` (§5.4's graded response), broadcasting over trailing nodes.
- `category_probabilities(m: np.ndarray, v_total: np.ndarray, guess: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 86) — ``P(Y = 0, 1, 2)`` with ``η ~ N(m, v_total)`` (the residual already in ``v_total``).
- `residual_success(eta_e: np.ndarray | float, guess: float=0.0) -> np.ndarray` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 99) — ``F_x(η_e) = E_ε[g + (1 - g - λ)σ(η_e - aε)]``: success given the epistemic state.
- `success_inverse(p: float, guess: float=0.0) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 110) — ``F_x⁻¹(p)``: ±inf outside ``F_x``'s range ``(g, 1 - λ)`` (a band edge it cannot reach).
- `normal_cdf(x: np.ndarray | float) -> np.ndarray` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 147) — ``Φ(x)``, vectorized (see :func:`_erfc`).
- `band_probability(m: np.ndarray, v_e: np.ndarray, guess: float, band: tuple[float, float]) -> np.ndarray` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 158) — ``P_band = P(p_θ ∈ band)``, exact because ``F_x`` is monotone (§5.7).
- `expected_success(m: np.ndarray, v_e: np.ndarray, guess: float) -> np.ndarray` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 175) — ``p̄``: the posterior predictive unassisted success, ``η ~ N(m, v_e + a²τ0²)``.
- `class Regression` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 184) — How a new topic-specific coordinate is created (§5.10): its regressors and raw weights.
- `class Structure` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 192) — The relatedness a bank reads when it creates a coordinate: none (the LO view, uniform sharing).
  - `facet_regression(self, facet: str, existing: Callable[[str], bool]) -> Regression` (line 195; public)
  - `cell_regression(self, facet: str, capability: str, existing: Callable[[str], bool]) -> Regression` (line 198; public)
  - `coupled_facets(self, facet: str) -> tuple[str, ...]` (line 201; public)
- `class UpdateRecord` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 206) — One factor's trace (§5.6 step 6), per row.
- `facet_name(facet: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 218)
- `cell_name(facet: str, capability: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 222)
- `subject_name(subject: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 226)
- `capability_name(subject: str, capability: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 230)
- `class Bank` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 234) — ``B = groups x len(points)`` filters sharing one event skeleton (see the module docstring).
  - `__init__(self, points: Sequence[P.HyperPoint], *, groups: int=1, structure: Structure | None=None, reading: bool=False, verdict: bool=False, rating: bool=False, timing: bool=False, outside: bool=False, capacity: int=64) -> None` (line 237; internal)
  - `_reserve(self, capacity: int) -> None` (line 279; internal)
  - `_views(self) -> None` (line 293; internal)
  - `_append(self, name: str, mean: np.ndarray, var: np.ndarray, *, cov: np.ndarray | None=None, s0_row: np.ndarray | None=None, s0_var: np.ndarray | None=None, topic: bool=False) -> int` (line 298; internal)
  - `has(self, name: str) -> bool` (line 326; public)
  - `copy(self) -> 'Bank'` (line 329; public)
  - `marginalize(self, names: Iterable[str]) -> None` (line 344; public) — Drop coordinates (exact for a Gaussian); only for coordinates no later event touches (sims).
  - `ensure_subject(self, subject: str, at: float | None=None) -> int` (line 371; public)
  - `ensure_lessons(self) -> None` (line 378; public) — The lesson curves' coefficients (``ad_lesson_priors_v1``; spec_teacher_v1 §14.2), created at the subject view's first lesson opportunity, as a subject or a facet is at its first observation: a bank no lesson has reached has exactly its predecessor's coordinates, means and covari…
  - `ensure_capability(self, subject: str, capability: str) -> int | None` (line 388; public)
  - `_regressed(self, name: str, regression: Regression) -> int` (line 397; internal)
  - `ensure_facet(self, facet: str, at: float | None=None) -> int` (line 415; public)
  - `ensure_cell(self, facet: str, capability: str, at: float | None=None) -> int` (line 422; public)
  - `virtual(self, name: str, regression: Regression | None, *, mean: float=0.0, variance: np.ndarray | None=None) -> tuple[np.ndarray, np.ndarray, np.ndarray]` (line 430; public) — A coordinate that does not exist yet, as it would be created now, without creating it: ``(coefficients over existing coordinates (B, d), mean (B,), own variance (B,))``.
  - `corr0(self, a: str, b: str) -> np.ndarray` (line 450; public) — The a-priori correlation a coupling set between two topic coordinates (§5.10's ``corr₀``).
  - `add_linear(self, target: str, coefficients: Mapping[str, np.ndarray | float]) -> None` (line 461; public) — ``s_target ← s_target + Σ c_j s_j`` (a linear map: the covariance propagates exactly).
  - `drift(self, name: str, at: float) -> None` (line 480; public) — §5.6 step 3: ``Var(e_{f,k}) += σ²_drift · Δdays`` since the cell's last update.
  - `reanchor_mean(self, name: str, mean: np.ndarray | float, prior_variance: np.ndarray | float) -> None` (line 490; public) — A claim moves a mean and never shrinks a variance (§5.5, Claims).
  - `moments(self, u: np.ndarray, extra_mean: np.ndarray | None=None, extra_var: np.ndarray | None=None) -> tuple[np.ndarray, np.ndarray]` (line 500; public) — ``(m, v_e)`` of ``η_e = ũᵀs`` (plus a virtual coordinates' contribution).
  - `update(self, u: np.ndarray, category: np.ndarray | int, guess: np.ndarray | float=0.0, *, rows: np.ndarray | None=None) -> UpdateRecord` (line 513; public) — One base-arm factor: §5.3's category (or the censored ``{0, 1}``) on ``η_e = ũᵀs``.
  - `update_joint(self, u: np.ndarray, *, category: int, guess: float=0.0, rating: str | None=None, log_latency_ratio: float | None=None) -> UpdateRecord` (line 551; public) — The joint factor with the sub-arms (§5.4, §5.6 step 4): outcome, rating and timing share ``η`` and the residual, integrated once by tensor quadrature (32 nodes on ``η``, 5 per link).
  - `weights(self) -> np.ndarray` (line 599; public) — ``W(ξ)``, normalized within each group: shape ``(groups, points)``.
  - `restricted_weights(self, mask: np.ndarray) -> np.ndarray` (line 607; public) — Weights renormalized over the points where ``mask`` (``(points,)``) holds.
  - `mean(self, name: str) -> np.ndarray` (line 616; public)
  - `variance(self, name: str) -> np.ndarray` (line 619; public)
  - `state_hash(self) -> str` (line 623; public)
- `rating_likelihood(eta: np.ndarray, rho: np.ndarray, c1: np.ndarray, c2: np.ndarray, rating: str) -> np.ndarray` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 668) — ``+rating``'s ordinal link (§5.4): valid for every value of ``(c_1, d̃, ρ̃)``.
- `rating_probabilities(eta: float, rho_t: float, c1: float, d_t: float) -> dict[str, float]` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 680)
- `cell_information(m: np.ndarray, v_e: np.ndarray, cov_c: np.ndarray, var_c: np.ndarray, guess: float=0.0, *, chunk: int=4096) -> np.ndarray` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 689) — ``I(θ_c; Y | x)`` per row: 24 outer nodes over ``θ_c``, 24 inner over the rest plus ``ε`` (the pre-registered rule, ``docs/reviews/adaptive-difficulty-ad23.md`` §1.1).
- `dose_basis(n: float) -> tuple[float, float]` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 719)
- `dose_increments(n: np.ndarray, dose: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 723) — :func:`dose_increment` per row, vectorized: ``(B, 2)``.
- `dose_increment(n: float, dose: float) -> tuple[float, float]` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 732) — ``b_m(n + D) - b_m(n)`` for both scales: the known weights of a reading transition.

### Module constants

- `_NORMAL` ([src/learnloop/adaptive_difficulty/model.py](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 51)
- `CENSORED` ([src/learnloop/adaptive_difficulty/model.py](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 54)
- `CATEGORIES` ([src/learnloop/adaptive_difficulty/model.py](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 55)
- `_INVERSE_CACHE` ([src/learnloop/adaptive_difficulty/model.py](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 107)

### Explicit exports

`__all__` declares:

- `Bank`
- `CENSORED`
- `Regression`
- `Structure`
- `UpdateRecord`
- `band_probability`
- `capability_name`
- `category_likelihood`
- `category_probabilities`
- `cell_information`
- `cell_name`
- `dose_basis`
- `dose_increment`
- `dose_increments`
- `expected_success`
- `facet_name`
- `normal_cdf`
- `rating_likelihood`
- `rating_probabilities`
- `residual_success`
- `sigmoid`
- `subject_name`
- `success_inverse`

## Internal implementation anchors

- `_erfc(x: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 136) — ``erfc`` by the Chebyshev fit of Numerical Recipes (fractional error < 1.2e-7 everywhere).
- `_phi(x: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 154)
- `_joint_moments(mu_q: np.ndarray, S_q: np.ndarray, links: Sequence[str], *, category: int, guess: float, rating: str | None, log_latency_ratio: float | None) -> tuple[float, np.ndarray, np.ndarray]` ([source](../../../../../../src/learnloop/adaptive_difficulty/model.py), line 634) — ``Z`` and the posterior moments of ``q = (η, links)`` by tensor Gauss-Hermite quadrature.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]] — imports `module`; statically calls `category_likelihood`, `expected_success`, `residual_success`
- [[Reference/Modules/learnloop/adaptive_difficulty/dose_report|learnloop.adaptive_difficulty.dose_report]] — imports `module`; statically calls `dose_basis`, `residual_success`, `success_inverse`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]] — imports `CENSORED`
- [[Reference/Modules/learnloop/adaptive_difficulty/outcomes|learnloop.adaptive_difficulty.outcomes]] — imports `CENSORED`
- [[Reference/Modules/learnloop/adaptive_difficulty/predict|learnloop.adaptive_difficulty.predict]] — imports `module`; statically calls `band_probability`, `cell_information`, `expected_success`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `module`; statically calls `Regression`, `cell_name`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; statically calls `Bank`, `Structure`, `facet_name`, `subject_name`
- [[Reference/Modules/learnloop/adaptive_difficulty/state|learnloop.adaptive_difficulty.state]] — imports `module`; statically calls `capability_name`, `cell_name`, `dose_increments`, `facet_name`, `subject_name`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`
- [[Reference/Modules/learnloop/sim/ad_gates|learnloop.sim.ad_gates]] — imports `module`; statically calls `dose_basis`
- [[Reference/Modules/learnloop/sim/ad_synthetic|learnloop.sim.ad_synthetic]] — imports `module`; statically calls `Bank`, `Structure`, `band_probability`, `cell_information`, `cell_name`, `dose_basis`, `expected_success`, `facet_name`, `residual_success`, `sigmoid`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `module`
- [[Reference/Modules/learnloop/adf_numeric|learnloop.adf_numeric]] — imports `gauss_hermite`, `sigmoid`; calls `sigmoid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `math`, `statistics`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]], [[Reference/Modules/learnloop/adaptive_difficulty/dose_report|learnloop.adaptive_difficulty.dose_report]], [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]], [[Reference/Modules/learnloop/adaptive_difficulty/outcomes|learnloop.adaptive_difficulty.outcomes]], [[Reference/Modules/learnloop/adaptive_difficulty/predict|learnloop.adaptive_difficulty.predict]] and 6 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad2_model.py](../../../../../../tests/test_ad2_model.py) — direct import
  - `test_band_probability_exact`
  - `test_joint_attempt_factor_integrates_residual_once`
  - `test_link_parameters_always_valid`
  - `test_rating_subarm_off_is_identical_to_base`
  - `test_unknown_hint_timing_never_read_as_after_work`
  - `test_unknown_hint_timing_through_the_replay`
- [tests/test_ad3_dose_arm.py](../../../../../../tests/test_ad3_dose_arm.py) — direct import
- [tests/test_ad3_reading.py](../../../../../../tests/test_ad3_reading.py) — direct import
  - `test_each_kind_raises_the_next_draw_by_its_next_increment`
- [tests/test_ad3_subject_view.py](../../../../../../tests/test_ad3_subject_view.py) — direct import
  - `test_a_proposal_recorded_after_a_coordinate_exists_changes_no_earlier_state`
  - `test_hyperparameters_learned_and_replayable`
  - `test_subject_view_mixture_keeps_propensities_exact`
- [tests/test_ro2_history_resolve.py](../../../../../../tests/test_ro2_history_resolve.py) — direct import
  - `test_a_helped_answer_of_unknown_timing_scores_as_a_delayed_failure`
- [tests/test_ro4_codex_review.py](../../../../../../tests/test_ro4_codex_review.py) — direct import
  - `test_f8_a_reading_candidate_starts_from_ads_dose_position`
- [tests/test_rofu_ad_latent.py](../../../../../../tests/test_rofu_ad_latent.py) — direct import
  - `test_ads_entry_point_hands_the_latent_moments_only_when_asked`
  - `test_codexs_reproductions_start_at_ads_p_bar`
  - `test_the_integrated_predictive_is_ads_expected_success`
  - `test_zero_variance_stays_equal`
- [tests/test_rofu_ad_link.py](../../../../../../tests/test_rofu_ad_link.py) — direct import
  - `test_the_link_is_ads_own_predictive_and_inverts_it`
- [tests/test_rofu_ad_stable.py](../../../../../../tests/test_rofu_ad_stable.py) — direct import
  - `test_codexs_case_gives_one_outcome_on_every_path_all_at_f`
  - `test_the_logit_is_stable_and_its_slope_matches_the_transformation`
- [tests/test_rospeed_ad_link.py](../../../../../../tests/test_rospeed_ad_link.py) — direct import
- [tests/test_te3a_lesson_opportunity.py](../../../../../../tests/test_te3a_lesson_opportunity.py) — direct import
  - `test_the_objective_reads_the_curve_through_ads_entry_only_at_the_tag_with_the_switch_on`
  - `test_the_prior_is_centred_and_spread_on_ro4s_placeholder_with_ads_shape`
  - `test_the_reports_lesson_row_at_the_prior_and_after_lessons`
- [tests/test_teacher_te1_weight.py](../../../../../../tests/test_teacher_te1_weight.py) — direct import
  - `test_the_adf_quadrature_is_ads`

## Modification guidance

- Make changes here when the responsibility remains model within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/model.py](../../../../../../src/learnloop/adaptive_difficulty/model.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
