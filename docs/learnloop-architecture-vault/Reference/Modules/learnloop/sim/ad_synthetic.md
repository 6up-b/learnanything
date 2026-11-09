---
title: "learnloop.sim.ad_synthetic"
type: "module-reference"
status: "current"
refactor_status: "EVALUATION"
version: "1.0.0"
source_path: "src/learnloop/sim/ad_synthetic.py"
source_paths:
  - "src/learnloop/sim/ad_synthetic.py"
source_commit: "1660b0b1e8b64cecb10c97b68cace57e816f127f"
source_commit_timestamp: "2026-10-19T00:57:40-04:00"
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
  - "learnloop.sim.ad_synthetic module"
  - "src/learnloop/sim/ad_synthetic.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/evaluation"
  - "layer/simulation"
  - "package/learnloop-sim"
---

# `learnloop.sim.ad_synthetic`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.sim.ad_synthetic` exists within [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] to own the behavior summarized by its module contract: Synthetic learners, vaults with known structure and synthetic readers (spec_adaptive_difficulty_v1 §14).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/sim/ad_synthetic.py](../../../../../../src/learnloop/sim/ad_synthetic.py) |
| Source lines | 1289 |
| Owning package | [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] |
| Architecture layer | `simulation` |
| Refactor status | `EVALUATION` |
| Worktree state | `clean` |
| Source commit | `1660b0b1e8b64cecb10c97b68cace57e816f127f` |
| Commit timestamp | `2026-10-19T00:57:40-04:00` |

> [!note] Evaluation-only authority
> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.

## Public API

- `rng_for(text: str) -> np.random.Generator` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 59) — A generator from a seed string (the pre-registered ``g-ad2-18:<scenario>:<i>`` form).
- `coding(point: Mapping[str, Any] | None) -> np.ndarray` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 67) — ``φ(x)`` over :data:`BETA` (cumulative dummy coding relative to ``x_ref``).
- `waypoint_points() -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 74) — The default trajectory's four waypoint tuples (the incumbent ladder's points).
- `pool_points(capability: str, *, waypoints: bool=False) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 80) — ``X_c`` of the capability's default ladder (§6.1), with the incumbent's waypoints when asked (amendment A4: the incumbent comparator serves its waypoints' items).
- `true_success(eta_e: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 91) — The family-expected success: ``ε`` integrated, lapse (guess 0).
- `sample_category(eta: np.ndarray, u: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 97) — §5.4's graded response at the realized ``η`` (residual included), from uniforms ``u``.
- `cell_spec(lo: str, facet: str, capability: str, *, loadings: Mapping[str, float] | None=None, subject: str=SUBJECT) -> ItemSpec` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 105) — A generated pool item at the reference tuple of a cell (``z_origin = 1``).
- `class Truth` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 116) — ``n`` learners' true parameters (known to the simulation, never to AD).
  - `ability(self, facet: str, capability: str) -> np.ndarray` (line 132; public)
  - `item_ability(self, lo: str, facet: str, capability: str) -> np.ndarray` (line 136; public)
  - `demand(self, codings: np.ndarray) -> np.ndarray` (line 140; public) — ``β·φ(x) + α_origin`` per learner (``codings`` ``(n, len(BETA))``).
  - `learn(self, lo: str, facet: str, capability: str, *, rows: np.ndarray | None=None) -> None` (line 145; public)
- `draw_truth(rng: np.random.Generator, n: int, *, facets: Sequence[str], capabilities: Sequence[str], split: float=P.LO_VIEW_SPLIT, gamma_sd: float=0.1) -> Truth` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 157) — Independent truths from ``ad_priors_v1`` at the split (the learner's own ``γ`` floored at 0).
- `class Arm` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 178) — ``n`` learners' AD filters (``n`` x grid points rows) of one view, with its draws.
  - `__init__(self, name: str, n: int, points: Sequence[P.HyperPoint], *, subject_view: bool=True, structure: Any=None, reading: bool=False, verdicts: bool=False, updates: bool=True, constants: S.SelectionConstants=S.SelectionConstants()) -> None` (line 181; internal)
  - `bank(self) -> M.Bank` (line 195; public)
  - `rows(self, values: np.ndarray) -> np.ndarray` (line 198; public)
  - `weights(self) -> np.ndarray` (line 201; public)
  - `mix(self, values: np.ndarray, weights: np.ndarray | None=None) -> np.ndarray` (line 204; public) — Mixture over each learner's grid points: ``(n*P, ...) -> (n, ...)``.
  - `ensure(self, spec: ItemSpec, at: float=0.0) -> None` (line 211; public)
  - `score(self, spec: ItemSpec, codings: np.ndarray, *, information: bool=False, weights: np.ndarray | None=None) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]` (line 214; public) — ``(P_band, p̄, I_c)`` of each learner at each point, ``(n, K)`` (mixtures, §5.7).
  - `predict(self, spec: ItemSpec, codings_rows: np.ndarray, weights: np.ndarray | None=None) -> np.ndarray` (line 230; public) — ``p̄`` of each learner's own served point (``codings_rows`` ``(n, len(BETA))``).
  - `draw(self, spec: ItemSpec, codings: np.ndarray, available: np.ndarray, keys: Sequence[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray]` (line 240; public) — Each learner's draw (``ad_select_v1``) over the points it still has items at: ``(chosen point index, band mode, propensity)``.
  - `observe(self, spec: ItemSpec, coding_rows: np.ndarray, category: np.ndarray, at: float, active: np.ndarray | None=None) -> None` (line 267; public)
- `class Incumbent` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 277) — ``select_rung``'s band ladder and optimism step on the mastery EKF, per LO; uniform among the waypoint's items.
  - `__init__(self, n: int) -> None` (line 283; internal)
  - `_state(self, lo: str) -> list[Any]` (line 288; internal)
  - `waypoint(self, lo: str) -> np.ndarray` (line 295; public)
  - `observe(self, lo: str, category: np.ndarray, at_index: int) -> None` (line 307; public)
- `class Pool` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 325) — Each learner's items at each point of one cell: 8 a point, used once.
  - `build(cls, rng: np.random.Generator, n: int, points: Sequence[Mapping[str, Any]]) -> 'Pool'` (line 333; public)
  - `copy(self) -> 'Pool'` (line 338; public)
  - `codings(self) -> np.ndarray` (line 342; public)
  - `available(self) -> np.ndarray` (line 345; public)
  - `take(self, chosen: np.ndarray) -> np.ndarray` (line 348; public) — Serve each learner the next unused item at its chosen point; its residual.
- `class StepLog` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 359) — One answer per learner: what was served and how it went.
- `serve_step(arm: Arm | Incumbent, truth: Truth, pool: Pool, *, lo: str, facet: str, capability: str, keys: Sequence[str], uniforms: np.ndarray, at: float, loadings: Mapping[str, float] | None=None, predict_with: Sequence[Arm]=()) -> StepLog` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 373) — One answer per learner: the arm's draw (or the incumbent's waypoint), the outcome under the truth, the arm's update and the truth's learning.
- `copy_truth(truth: Truth) -> Truth` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 409)
- `class UsableResult` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 419)
  - `band_hit_rate(self, arm: str, start: int=16, end: int=30, *, mask: Callable[[StepLog], bool] | None=None) -> float` (line 423; public)
  - `reachable_rate(self, arm: str, start: int=16, end: int=30) -> float` (line 428; public) — An oracle's bound on the band-hit rate: some pool point was in the band.
  - `engaged_by(self, arm: str, t: int=15) -> float` (line 434; public)
  - `trivial_success_rate(self, arm: str) -> float` (line 441; public)
- `time_to_usable(scenario: str, *, n: int=200, answers: int=30, seed: str='g-ad2-18') -> UsableResult` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 450) — G-AD2-18's three scenarios (``one_cell``, ``wrong_prior``, ``plan_flow``).
- `own_answers_before_band(logs: Sequence[StepLog], cell: tuple[str, str]) -> np.ndarray` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 499) — Per learner, the own answers a cell needed before its first band-mode draw (inf: never).
- `feature_time_correlation(points: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 518) — §5.8's first diagnostic on a served sequence (the report's own function).
- `class RecoveryResult` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 527)
- `recovery(*, policy: str, n: int=200, answers: int=60, seed: str='g-ad2-8', no_feature_effect: bool=False) -> RecoveryResult` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 535) — One cell, the LO view, 60 answers; ``policy`` ``ad_select_v1`` (live draw) or ``monotone`` (the ladder's points in ascending prior demand, one step every answers/len points).
- `class CensoringResult` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 586)
- `censoring(*, n: int=200, answers: int=60, seed: str='g-ad2-14') -> CensoringResult` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 593) — Help with probability ``σ(-m - 1)``, a reveal with ``σ(-m - 2)`` (``m`` the item's true margin, residual included), at uniformly drawn ladder points (amendment A8); AD's censored update against a filter that drops every assisted attempt.
- `class Cluster` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 655) — A vault of clusters of three LOs (A, B, C), one facet each, capability retrieval.
  - `los(self) -> list[str]` (line 661; public)
  - `facet(self, lo: str) -> str` (line 664; public)
  - `cluster_of(self, lo: str) -> int` (line 667; public)
  - `mates(self, lo: str) -> list[str]` (line 670; public)
  - `maps(self) -> tuple[dict[str, list[str]], dict[str, list[str]]]` (line 674; public)
  - `true_loadings(self, lo: str) -> dict[str, float]` (line 677; public) — B's items load 0.5 onto A's facet, C's onto B's (the true implication structure).
- `proposal(vault: Cluster, kind: str, rng: np.random.Generator | None=None) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, float]]]` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 688) — The simulated proposal (``correct``, ``noisy``, ``wrong``): couplings LO -> {LO: C} and loadings by LO (frozen per item) -> {facet: Q}.
- `structure_for(vault: Cluster, couplings: Mapping[str, Mapping[str, float]], loadings_by_lo: Mapping[str, Mapping[str, float]]) -> VaultStructure` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 755)
- `cluster_truth(rng: np.random.Generator, n: int, vault: Cluster, *, correlation: float=0.8, transfer: float=0.8) -> Truth` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 762) — G-AD3-7's truth: subject level N(0, 1.5); facet and cell offsets N(0, 0.75) correlated 0.8 within a cluster and 0 across; true loadings (implication 0.5); learning transferring to cluster mates at 0.8 of the increment.
- `class RelatedResult` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 790)
  - `first_attempt_loss(self, arm: str, lo: str) -> np.ndarray` (line 797; public)
  - `own_answers_before_band(self, arm: str, lo: str) -> np.ndarray` (line 803; public)
  - `band_hit_rate(self, arm: str, lo: str) -> float` (line 807; public)
- `related_topics(*, flow: str, proposal_kind: str, n: int=200, seed: str='g-ad3-7', own: int=15, chunk: int=50) -> RelatedResult` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 812) — G-AD3-7: 15 answers on cluster 1's A (``practice``) or 5 sections read on it (``reading``), then its never-seen mates B and C, then cluster 2's A, each up to 15 own answers; under ``@subject`` (the 36-point mixture with the proposal) and ``@subject_uniform``, common random numbe…
- `wrong_proposal_shrinks(*, proposal_kind: str, n: int=200, seed: str='g-ad3-7:shrink', chunk: int=25, first_attempts: int=200) -> dict[str, np.ndarray]` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 880) — 70 clusters of three (210 LOs): 15 answers on one LO, then one first attempt on each never-seen LO in a fixed shuffled order at a fixed mid-ladder point.
- `hyperparameters_learned(point: P.HyperPoint, *, seeds: int=25, answers: int=300, seed: str='g-ad3-6') -> np.ndarray` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 978) — G-AD3-6: per seed, the posterior weight on the generating point and its grid neighbours (Chebyshev distance 1) after 300 first-surface answers over the 12 LOs of the cluster vault (correct proposal), the truth drawn from the model at that point (amendment A9: every LO's coordina…
- `true_curve(c: tuple[float, float], n: float) -> float` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 1050)
- `class ReaderResult` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 1056) — Per reader: the fitted coefficient moments, the offers, visits and the prequential log.
- `readers(*, scenario: str, n: int=200, los: int=1250, windows: int=4, floor: float=0.1, seed: str='g-ad3-11', reading_only: bool=False, rise: float | None=None, verdicts: str | None=None, arms: Sequence[str]=('on',)) -> ReaderResult` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 1071) — Synthetic readers working through ``los`` LOs, one facet each, ``windows`` windows per LO.
- `fitted_useful_dose(result: ReaderResult, kind: str, reader: int, *, draws: int=400, seed: str='ad-dose-v1') -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 1206) — The report's useful dose for one reader (``dose_report.useful_dose``): posterior draws of the kind's coefficients and of ``γ``, the kind's minutes by NNLS on the reader's visits.
- `true_useful_dose(curve: tuple[float, float], minutes: float, *, gamma: float=0.2, practice_minutes: float=PRACTICE_MINUTES) -> int` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 1234) — ``n*`` of a true curve: the largest dose whose own event still adds at least one more practice question's gain per minute (both at the band's centre, warmth 0).

### Module constants

- `ITEMS_PER_POINT` ([src/learnloop/sim/ad_synthetic.py](../../../../../../src/learnloop/sim/ad_synthetic.py), line 51)
- `SUBJECT` ([src/learnloop/sim/ad_synthetic.py](../../../../../../src/learnloop/sim/ad_synthetic.py), line 52)
- `BAND` ([src/learnloop/sim/ad_synthetic.py](../../../../../../src/learnloop/sim/ad_synthetic.py), line 53)
- `TRIVIAL` ([src/learnloop/sim/ad_synthetic.py](../../../../../../src/learnloop/sim/ad_synthetic.py), line 54)
- `BETA` ([src/learnloop/sim/ad_synthetic.py](../../../../../../src/learnloop/sim/ad_synthetic.py), line 55)
- `WAYPOINT_SLUGS` ([src/learnloop/sim/ad_synthetic.py](../../../../../../src/learnloop/sim/ad_synthetic.py), line 56)
- `KINDS` ([src/learnloop/sim/ad_synthetic.py](../../../../../../src/learnloop/sim/ad_synthetic.py), line 1041)
- `MINUTES` ([src/learnloop/sim/ad_synthetic.py](../../../../../../src/learnloop/sim/ad_synthetic.py), line 1042)
- `PRACTICE_MINUTES` ([src/learnloop/sim/ad_synthetic.py](../../../../../../src/learnloop/sim/ad_synthetic.py), line 1043)
- `BASE_CURVES` ([src/learnloop/sim/ad_synthetic.py](../../../../../../src/learnloop/sim/ad_synthetic.py), line 1044)
- `DOWNTURN` ([src/learnloop/sim/ad_synthetic.py](../../../../../../src/learnloop/sim/ad_synthetic.py), line 1046)
- `OFFER_KIND` ([src/learnloop/sim/ad_synthetic.py](../../../../../../src/learnloop/sim/ad_synthetic.py), line 1047)

### Explicit exports

`__all__` declares:

- `Arm`
- `BASE_CURVES`
- `CensoringResult`
- `Cluster`
- `DOWNTURN`
- `Incumbent`
- `KINDS`
- `MINUTES`
- `Pool`
- `ReaderResult`
- `RecoveryResult`
- `RelatedResult`
- `StepLog`
- `Truth`
- `UsableResult`
- `cell_spec`
- `censoring`
- `cluster_truth`
- `coding`
- `draw_truth`
- `feature_time_correlation`
- `fitted_useful_dose`
- `hyperparameters_learned`
- `own_answers_before_band`
- `pool_points`
- `proposal`
- `readers`
- `recovery`
- `related_topics`
- `rng_for`
- `sample_category`
- `serve_step`
- `time_to_usable`
- `true_curve`
- `true_success`
- `true_useful_dose`
- `waypoint_points`
- `wrong_proposal_shrinks`

## Internal implementation anchors

- `_predictive_with_sd(arm: Arm, spec: ItemSpec, codings: np.ndarray) -> tuple[np.ndarray, np.ndarray]` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 640) — ``p̄`` at each point and the posterior sd of ``p_θ`` (``ε`` integrated, state uncertain).
- `_across_partner(vault: Cluster, rng: np.random.Generator) -> dict[str, str]` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 730)
- `_across_pairs(vault: Cluster, rng: np.random.Generator, *, order: Sequence[str] | None=None) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 739) — Every pair across clusters: each LO names two partners of other clusters (near it in ``order`` when given, so a long vault's live coordinates stay few).
- `_join(a: StepLog, b: StepLog) -> StepLog` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 831)
- `_related_chunk(vault: Cluster, flow: str, proposal_kind: str, n: int, seed: str, start: int, own: int) -> dict[str, list[StepLog]]` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 838)
- `_last_needed(order: Sequence[str], couplings: Mapping[str, Mapping[str, float]]) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 961) — After which LO's first attempt each LO's coordinates are read no more (exact marginalization: no later observation, and every LO that couples to it exists).
- `_chebyshev(a: P.HyperPoint, b: P.HyperPoint) -> int` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 1031)
- `_predict_reference(view: View, spec: ItemSpec) -> np.ndarray` ([source](../../../../../../src/learnloop/sim/ad_synthetic.py), line 1229)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/sim/ad_gates|learnloop.sim.ad_gates]] — imports `module`; statically calls `censoring`, `coding`, `feature_time_correlation`, `fitted_useful_dose`, `hyperparameters_learned`, `own_answers_before_band`, `readers`, `recovery`, `related_topics`, `rng_for`, `time_to_usable`, `true_curve`, `true_useful_dose`, `wrong_proposal_shrinks`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/dose_report|learnloop.adaptive_difficulty.dose_report]] — imports `MAX_DOSE`, `OfferOutcome`, `module`, `points_gain`; calls `OfferOutcome`, `nnls`, `points_gain`, `useful_dose`
- [[Reference/Modules/learnloop/adaptive_difficulty/model|learnloop.adaptive_difficulty.model]] — imports `module`; calls `Bank`, `Structure`, `band_probability`, `cell_information`, `cell_name`, `dose_basis`, `expected_success`, `facet_name`, `residual_success`, `sigmoid`
- [[Reference/Modules/learnloop/adaptive_difficulty/monitoring|learnloop.adaptive_difficulty.monitoring]] — imports `module`; calls `comparison_flag`, `log_loss_difference`
- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `module`; calls `feature_coding`, `hyper_grid`, `offset_variance`, `uniform_points`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `VaultStructure`
- [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]] — imports `aliased_coordinates`, `feature_time_correlation`; calls `aliased_coordinates`, `feature_time_correlation`
- [[Reference/Modules/learnloop/adaptive_difficulty/selection|learnloop.adaptive_difficulty.selection]] — imports `module`; calls `Scored`, `SelectionConstants`, `commission_candidates`, `draw`, `ladder`, `point_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/state|learnloop.adaptive_difficulty.state]] — imports `ItemSpec`, `View`; calls `ItemSpec`, `View`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `MasteryConfig`; calls `MasteryConfig`
- [[Reference/Modules/learnloop/curriculum/depth_rungs|learnloop.curriculum.depth_rungs]] — imports `DEFAULT_TRAJECTORY`, `UNCERTAIN_EVIDENCE_COUNT`, `UNCERTAIN_OPTIMISM_STEPS`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `MasteryObservation`, `display_mastery`, `initial_mastery_state`, `update_mastery`; calls `MasteryObservation`, `display_mastery`, `initial_mastery_state`, `update_mastery`
- [[Reference/Modules/learnloop/scheduling/randomization_layer|learnloop.scheduling.randomization_layer]] — imports `draw_from`, `reading_dose_propensities`; calls `draw_from`, `reading_dose_propensities`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `hashlib`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

No direct learner/operator workflow is assigned. This module is offline, shadow-only, dormant, or a dependency reached only through the static consumers below.

Static participation evidence comes from [[Reference/Modules/learnloop/sim/ad_gates|learnloop.sim.ad_gates]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_ad23_sim.py](../../../../../../tests/test_ad23_sim.py) — imports consumer [[Reference/Modules/learnloop/sim/ad_gates|learnloop.sim.ad_gates]]
- [tests/test_ad23_sim_smoke.py](../../../../../../tests/test_ad23_sim_smoke.py) — imports consumer [[Reference/Modules/learnloop/sim/ad_gates|learnloop.sim.ad_gates]]

## Modification guidance

- Make changes here when the responsibility remains ad synthetic within learnloop.sim; otherwise move the behavior to its owning boundary.
- Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/sim/ad_synthetic.py](../../../../../../src/learnloop/sim/ad_synthetic.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
