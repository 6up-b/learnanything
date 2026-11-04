---
title: "learnloop.router.lesson_suggestions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router/lesson_suggestions.py"
source_paths:
  - "src/learnloop/router/lesson_suggestions.py"
source_commit: "6e6bd6afe66bdfe4b5aa19c8e19cb4e05d849b2d"
source_commit_timestamp: "2026-11-02T08:47:44-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router.lesson_suggestions module"
  - "src/learnloop/router/lesson_suggestions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router"
---

# `learnloop.router.lesson_suggestions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router/_package|learnloop.router]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router.lesson_suggestions` exists within [[Reference/Modules/learnloop/router/_package|learnloop.router]] to own the behavior summarized by its module contract: Teacher TE1b: the router suggests a lesson, the learner opts in (spec_teacher_v1 §15.1, §18.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py) |
| Source lines | 624 |
| Owning package | [[Reference/Modules/learnloop/router/_package|learnloop.router]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `6e6bd6afe66bdfe4b5aa19c8e19cb4e05d849b2d` |
| Commit timestamp | `2026-11-02T08:47:44-05:00` |

## Public API

- `class Context` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 171) — The day's draw context (stored on the decision row, read back by replay).
  - `as_dict(self) -> dict[str, Any]` (line 179; public)
  - `from_dict(cls, value: Mapping[str, Any]) -> 'Context'` (line 186; public)
- `class Candidate` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 196) — One ``instruct(lesson)`` candidate.
  - `as_dict(self) -> dict[str, Any]` (line 209; public)
  - `from_dict(cls, value: Mapping[str, Any]) -> 'Candidate'` (line 220; public)
- `lesson_ref(learning_object_id: str) -> str` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 231)
- `decline_shape(days: float | None, recovery_days: float) -> float` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 235) — ``g_R(d)``: 1 at the "Not now", 0 from ``R`` days on (``log(1 + d)`` against ``log(1 + R)``).
- `spacing_feature(days: float | None) -> float` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 243) — The days-since-the-last-suggestion feature (codex review F7): ``1/(1 + c) − 1/(1 + d)``.
- `design_vector(context: Context, candidate: Candidate, recovery_days: float) -> np.ndarray` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 258) — ``h`` for one candidate in one context at one recovery grid point.
- `class AcceptanceState` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 278) — The acceptance model's posterior as of some instant.
  - `weights(self) -> np.ndarray` (line 286; public)
  - `p_accept(self, context: Context, candidate: Candidate) -> float` (line 289; public) — The posterior predictive ``P(accept)``: the grid mixture of ``E[σ(h · θ)]``.
  - `observe(self, context: Context, candidate: Candidate, accepted: bool) -> None` (line 298; public) — One response: AD's assumed-density step in every bank, the grid weights by ``log Z``.
  - `summary(self) -> dict[str, Any]` (line 313; public) — Posterior means (grid-weighted) and the recovery grid's weights, for the decision row.
- `class Observation` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 330)
- `observations(decisions: Mapping[str, Mapping[str, Any]], responses: Iterable[Mapping[str, Any]]) -> list[Observation]` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 337) — The acceptance observations of a response ledger, in response order.
- `replay(observed: Iterable[Observation]) -> AcceptanceState` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 370)
- `declines_by_learning_object(decisions: Mapping[str, Mapping[str, Any]], responses: Iterable[Mapping[str, Any]]) -> dict[str, str]` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 377) — Per LO, the time of its latest "Not now" not followed by an acceptance of a lesson on it.
- `class ScoredCandidate` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 403)
  - `as_dict(self) -> dict[str, Any]` (line 410; public)
- `class Target` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 416) — The drawn target: the router's design, its exact distribution over the scored candidates (0 off the support) and what it logs (``record``: enough to recompute ``pi``).
- `mixture_target(scored: Sequence[ScoredCandidate], *, weights: Mapping[str, float], epsilon: float, seed: str) -> Target` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 426) — ``router.mode = "mixture"``: the router's ``model_mixture`` over ``scored`` (the top ``k``).
- `tiebreak_target(scored: Sequence[ScoredCandidate], *, chosen_ref: str, tied: Sequence[str], margin: float) -> Target` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 456) — ``router.mode = "staged"``: the randomization layer's ``epsilon_tiebreak`` (the shell runs it).
- `class Draw` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 477) — The day's draw.
  - `arm_propensity(self) -> float` (line 499; public) — The arm's probability given the drawn target (1 when the ceiling binds).
  - `chosen_ref(self) -> str` (line 507; public)
- `score(state: AcceptanceState, context: Context, candidates: Sequence[Candidate], *, k: int) -> list[ScoredCandidate]` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 511) — Each candidate's ``P(accept)``, room and value; the top ``k`` by value (ties by ref).
- `seed_for(day: str, snapshot_hash: str) -> str` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 524)
- `draw(scored: Sequence[ScoredCandidate], *, target: Target, seed: str, ceiling_bound: bool=False) -> Draw` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 540) — The day's draw over ``scored`` (non-empty): the drawn ``target`` (its ``π``), then the show coin.
- `canonical_hash(value: Any) -> str` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 574)
- `days_between(later: Any, earlier: Any) -> float` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 579) — Days between two aware datetimes (never negative).

### Module constants

- `SUGGESTION_VERSION` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 74)
- `PRIORS_VERSION` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 76)
- `DECISION_KIND` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 77)
- `DESIGN` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 80)
- `TARGET_MIXTURE` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 82)
- `TARGET_TIEBREAK` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 83)
- `TARGET_DESIGNS` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 84)
- `MODELS_NOT_ASKED` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 86)
- `POLICY` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 87)
- `SURFACE` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 88)
- `CANDIDATE_KIND` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 89)
- `NO_SUGGESTION` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 91)
- `REASONS` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 92)
- `RESPONSES` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 93)
- `TERMS` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 100)
- `LEGACY_DAILY_SHOW` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 108)
- `LEGACY_DECLINED_SHOW` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 111)
- `LEGACY_CADENCE_DAYS` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 114)
- `PRIOR_SD` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 116)
- `RECOVERY_DAYS_GRID` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 120)
- `CARD_MINUTES` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 123)
- `MAX_ALTERNATIVES` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 125)
- `_SECONDS_PER_DAY` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 127)

### Explicit exports

`__all__` declares:

- `AcceptanceState`
- `CANDIDATE_KIND`
- `CARD_MINUTES`
- `Candidate`
- `Context`
- `DECISION_KIND`
- `DESIGN`
- `Draw`
- `MAX_ALTERNATIVES`
- `MODELS_NOT_ASKED`
- `NO_SUGGESTION`
- `Observation`
- `POLICY`
- `PRIORS_VERSION`
- `REASONS`
- `RECOVERY_DAYS_GRID`
- `RESPONSES`
- `SURFACE`
- `SUGGESTION_VERSION`
- `ScoredCandidate`
- `TARGET_DESIGNS`
- `TARGET_MIXTURE`
- `TARGET_TIEBREAK`
- `Target`
- `canonical_hash`
- `days_between`
- `decline_shape`
- `declines_by_learning_object`
- `design_vector`
- `draw`
- `lesson_ref`
- `mixture_target`
- `observations`
- `replay`
- `score`
- `seed_for`
- `spacing_feature`
- `tiebreak_target`

## Internal implementation anchors

- `_centre_for(target: float, variance: float) -> float` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 130) — The logit centre ``m`` with ``E[σ(N(m, variance))] = target`` (bisection; numerical resolution).
- `_prior_mean() -> np.ndarray` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 143) — The seeded centres: the prior predictive reproduces the legacy targets at the reference context.
- `class _Bank` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 161) — One recovery grid point's Gaussian over the effects.
- `_uniforms(seed: str) -> tuple[float, float, float]` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 528) — The draw's three uniforms from its seed: the mixture's two stages, then the show coin.
- `_propensity(p: float) -> tuple[float, str]` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 534)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `module`; statically calls `Candidate`, `Context`, `canonical_hash`, `days_between`, `declines_by_learning_object`, `draw`, `lesson_ref`, `mixture_target`, `observations`, `replay`, `score`, `seed_for`, `tiebreak_target`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adf_numeric|learnloop.adf_numeric]] — imports `adf_update`, `gaussian_sigmoid_mean`, `normalized_log_weights`, `sigmoid`; calls `adf_update`, `gaussian_sigmoid_mean`, `normalized_log_weights`, `sigmoid`
- [[Reference/Modules/learnloop/router/mixture|learnloop.router.mixture]] — imports `module`; calls `component_distributions`, `draw_with_uniforms`, `effective_weights`, `uniform`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followups_batch6_review_fixes.py](../../../../../../tests/test_followups_batch6_review_fixes.py) — direct import
  - `test_f3_the_cli_labels_the_r_cold_comparison_with_observed_cold_outcomes`
- [tests/test_followups_batch6_router_report.py](../../../../../../tests/test_followups_batch6_router_report.py) — direct import
  - `test_router_report_prints_the_split_from_the_ledgers_read_only`
- [tests/test_ro0_codex_review.py](../../../../../../tests/test_ro0_codex_review.py) — direct import
  - `test_f3_a_lesson_suggestion_keeps_its_ad_numbers_read_before_its_transaction`
- [tests/test_teacher_te1b_landing_r2.py](../../../../../../tests/test_teacher_te1b_landing_r2.py) — direct import
  - `test_not_now_on_a_pending_card_releases_the_reservation`
- [tests/test_teacher_te1b_rereview_fixes.py](../../../../../../tests/test_teacher_te1b_rereview_fixes.py) — direct import
  - `test_mixture_mode_draws_the_target_by_the_routers_model_mixture`
  - `test_staged_mode_draws_the_target_by_the_epsilon_tiebreak`
  - `test_the_mixture_floor_draws_a_non_staged_target_with_its_exact_propensity`
  - `test_the_staged_tiebreak_is_deterministic_without_a_near_tie`
- [tests/test_teacher_te1b_review_fixes.py](../../../../../../tests/test_teacher_te1b_review_fixes.py) — direct import
  - `test_an_unshown_decision_has_its_itt_outcome_over_the_same_scope`
  - `test_logged_propensities_give_no_effect_when_targets_differ_and_the_card_does_nothing`
  - `test_the_acceptance_model_learns_that_a_card_after_a_week_is_taken_and_daily_ones_are_not`
  - `test_the_draw_logs_the_joint_target_and_arm_probability`
  - `test_the_spacing_feature_keeps_every_multi_day_gap`
- [tests/test_teacher_te1b_suggestions.py](../../../../../../tests/test_teacher_te1b_suggestions.py) — direct import
  - `test_a_day_with_no_card_is_logged_too`
  - `test_re_acceptance_after_a_decline_teaches_the_recovery_rate`
  - `test_the_card_comes_at_most_once_a_day`
  - `test_the_ceiling_binds_and_is_logged`
  - `test_the_decision_logs_the_draw_with_its_exact_propensity`
  - `test_the_seeded_priors_reproduce_one_a_day_and_a_week_long_mute`

## Modification guidance

- Make changes here when the responsibility remains lesson suggestions within learnloop.router; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
