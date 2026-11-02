---
title: "learnloop.adaptive_difficulty.state"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/state.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/state.py"
source_commit: "2778e23fe57cb9e86780e5e1e0b93ad814872e6e"
source_commit_timestamp: "2026-10-19T00:49:53-04:00"
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
  - "learnloop.adaptive_difficulty.state module"
  - "src/learnloop/adaptive_difficulty/state.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.state`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.state` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: The events of §5.6 on a :class:`~learnloop.adaptive_difficulty.model.Bank` (spec_adaptive_difficulty_v1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/state.py](../../../../../../src/learnloop/adaptive_difficulty/state.py) |
| Source lines | 382 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2778e23fe57cb9e86780e5e1e0b93ad814872e6e` |
| Commit timestamp | `2026-10-19T00:49:53-04:00` |

## Public API

- `class ItemSpec` ([source](../../../../../../src/learnloop/adaptive_difficulty/state.py), line 38) — An item (or a not-yet-written feature point, §5.7) as AD reads it.
  - `primary_facet(self) -> str` (line 55; public) — The highest-weight facet, ties by facet id (§6.1).
  - `cell(self) -> tuple[str, str]` (line 60; public)
- `normalized_weights(weights: Mapping[str, float] | None, facets: Sequence[str]=()) -> dict[str, float]` ([source](../../../../../../src/learnloop/adaptive_difficulty/state.py), line 64) — ``evidence_weights`` normalized, falling back to equal weights over ``evidence_facets`` (§5.1).
- `class View` ([source](../../../../../../src/learnloop/adaptive_difficulty/state.py), line 77) — One view's state: the subject view (a bank over the grid) or one LO's view (one filter).
  - `__init__(self, bank: M.Bank, *, subject_view: bool, reading: bool=False, verdicts: bool=False, signals: Sequence[str]=P.BASE_SIGNALS) -> None` (line 80; internal)
  - `_extended_weights(self, spec: ItemSpec) -> dict[str, np.ndarray]` (line 92; internal) — ``w̃``: the own weights, less the loadings' share, plus the loaded facets (§5.4).
  - `projection(self, spec: ItemSpec, warmth: float | np.ndarray=0.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]` (line 106; public) — ``ũ`` over the existing coordinates, plus the mean and variance not-yet-created coordinates would bring, created as they would be now (never created by a prediction).
  - `prediction(self, spec: ItemSpec, warmth: float | np.ndarray=0.0) -> tuple[np.ndarray, np.ndarray]` (line 159; public) — ``(m(x), v_e(x))`` per row (§5.7).
  - `with_cell(self, subject: str, facet: str, capability: str) -> 'View'` (line 165; public) — A copy of this view with one cell's coordinates created as they would be now (the selection's ``I_c`` reads the cell ability; nothing is created in this view).
  - `cell_vector(self, subject: str, facet: str, capability: str) -> np.ndarray` (line 179; public) — The projection of the cell ability ``θ_{f,k}`` (its coordinates must exist).
  - `cell_moments(self, spec: ItemSpec) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]` (line 190; public) — ``(m, v_e, Cov(η_e, θ_c), Var(θ_c))`` for the spec's cell.
  - `point_moments(self, spec: ItemSpec, codings: np.ndarray, names: Sequence[str], *, warmth: float | np.ndarray=0.0) -> tuple[np.ndarray, np.ndarray]` (line 203; public) — ``(m, v_e)`` of ``K`` feature points at the spec's cell, shape ``(B, K)``.
  - `point_cell_covariance(self, spec: ItemSpec, codings: np.ndarray, names: Sequence[str]) -> tuple[np.ndarray, np.ndarray]` (line 226; public) — ``(Cov(η_e, θ_c), Var(θ_c))`` per row and point (the calibrate rule's ``I_c``, §5.7).
  - `observe_points(self, spec: ItemSpec, coding_rows: np.ndarray, names: Sequence[str], category: np.ndarray, at: float, *, rows: np.ndarray | None=None, learn: bool=True) -> M.UpdateRecord` (line 240; public) — :meth:`observe` with each row's own feature point (``coding_rows``: ``(B, len(names))``).
  - `ensure(self, spec: ItemSpec, at: float) -> None` (line 258; public)
  - `ensure_facet(self, subject: str, facet: str, at: float) -> None` (line 266; public)
  - `observe(self, spec: ItemSpec, category: int | np.ndarray, at: float, *, warmth: float | np.ndarray=0.0, rows: np.ndarray | None=None, in_passage_kind: str | None=None, rating: str | None=None, log_latency_ratio: float | None=None, learn: bool=True) -> M.UpdateRecord` (line 272; public) — §5.6 steps 3-5 for one eligible attempt.
  - `learn(self, spec: ItemSpec, *, rows: np.ndarray | None=None, in_passage_kind: str | None=None) -> None` (line 292; public) — §5.6 step 5: a practice opportunity for every topic the item draws on, with the coupled transfer; an in-passage answer takes its kind's increment in place of ``γ``.
  - `_reading_transition(self, doses: Mapping[str, np.ndarray], kind: str) -> None` (line 315; internal)
  - `reading(self, subject: str, kind: str, facet_doses: Mapping[str, float | np.ndarray], at: float) -> None` (line 338; public) — A reading opportunity (§5.11): its kind's next dose-curve increment on each facet.
  - `verdict(self, subject: str, verdict_class: str, facet_doses: Mapping[str, float | np.ndarray], at: float) -> None` (line 347; public) — A self-check verdict (D22): ``θ_f ← θ_f + λ_v·D_f``, with the coupled transfer.
  - `close_windows(self, facets: Sequence[str], rows: np.ndarray | None=None) -> None` (line 368; public) — §5.6 step 5: a graded attempt on a facet resets its reading windows.
  - `claim(self, coordinate: str, mean: float, prior_variance: np.ndarray | float) -> None` (line 378; public)

### Explicit exports

`__all__` declares:

- `ItemSpec`
- `View`
- `normalized_weights`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]] — imports `View`
- [[Reference/Modules/learnloop/adaptive_difficulty/predict|learnloop.adaptive_difficulty.predict]] — imports `ItemSpec`, `View`, `normalized_weights`; statically calls `ItemSpec`, `normalized_weights`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `ItemSpec`, `View`, `normalized_weights`; statically calls `ItemSpec`, `View`, `normalized_weights`
- [[Reference/Modules/learnloop/sim/ad_synthetic|learnloop.sim.ad_synthetic]] — imports `ItemSpec`, `View`; statically calls `ItemSpec`, `View`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/model|learnloop.adaptive_difficulty.model]] — imports `module`; calls `capability_name`, `cell_name`, `dose_increments`, `facet_name`, `subject_name`
- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `module`; calls `feature_coding`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]], [[Reference/Modules/learnloop/adaptive_difficulty/predict|learnloop.adaptive_difficulty.predict]], [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]], [[Reference/Modules/learnloop/sim/ad_synthetic|learnloop.sim.ad_synthetic]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_the_grid_arm_never_reads_a_later_answer`
- [tests/test_ad2_model.py](../../../../../../tests/test_ad2_model.py) — direct import
  - `test_joint_attempt_factor_integrates_residual_once`
  - `test_rating_subarm_off_is_identical_to_base`
- [tests/test_ad3_dose_arm.py](../../../../../../tests/test_ad3_dose_arm.py) — direct import
- [tests/test_ad3_reading.py](../../../../../../tests/test_ad3_reading.py) — direct import
- [tests/test_ad3_subject_view.py](../../../../../../tests/test_ad3_subject_view.py) — direct import
  - `test_a_proposal_recorded_after_a_coordinate_exists_changes_no_earlier_state`
  - `test_hyperparameters_learned_and_replayable`
  - `test_subject_view_mixture_keeps_propensities_exact`

## Modification guidance

- Make changes here when the responsibility remains state within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/state.py](../../../../../../src/learnloop/adaptive_difficulty/state.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
