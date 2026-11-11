---
title: "learnloop.router.lesson_suggestions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router/lesson_suggestions.py"
source_paths:
  - "src/learnloop/router/lesson_suggestions.py"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router/_package|learnloop.router]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router.lesson_suggestions` exists within [[Reference/Modules/learnloop/router/_package|learnloop.router]] to own the behavior summarized by its module contract: Teacher TE1b: the router suggests a lesson, the learner opts in (spec_teacher_v1 §15.1, §18.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py) |
| Source lines | 738 |
| Owning package | [[Reference/Modules/learnloop/router/_package|learnloop.router]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Context` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 189) — The day's draw context (stored on the decision row, read back by replay).
  - `as_dict(self) -> dict[str, Any]` (line 197; public)
  - `from_dict(cls, value: Mapping[str, Any]) -> 'Context'` (line 204; public)
- `class Candidate` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 214) — One ``instruct(lesson)`` candidate.
  - `as_dict(self) -> dict[str, Any]` (line 230; public)
  - `from_dict(cls, value: Mapping[str, Any]) -> 'Candidate'` (line 243; public)
- `lesson_ref(learning_object_id: str) -> str` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 255)
- `decline_shape(days: float | None, recovery_days: float) -> float` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 259) — ``g_R(d)``: 1 at the "Not now", 0 from ``R`` days on (``log(1 + d)`` against ``log(1 + R)``).
- `spacing_feature(days: float | None) -> float` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 267) — The days-since-the-last-suggestion feature (codex review F7): ``1/(1 + c) − 1/(1 + d)``.
- `design_vector(context: Context, candidate: Candidate, recovery_days: float) -> np.ndarray` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 282) — ``h`` for one candidate in one context at one recovery grid point.
- `class AcceptanceState` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 302) — The acceptance model's posterior as of some instant.
  - `weights(self) -> np.ndarray` (line 312; public)
  - `design(self, bank: _Bank, context: Context, candidate: Candidate, *, unprompted: bool=False) -> np.ndarray` (line 315; public) — ``h`` in ``bank``'s terms.
  - `p_accept(self, context: Context, candidate: Candidate) -> float` (line 322; public) — The posterior predictive ``P(accept)`` of an offer: the grid mixture of ``E[σ(h · θ)]``.
  - `_open_unprompted(self) -> None` (line 331; internal) — The offset's prior, independent of the rest: earlier responses never set its slot, so adding it now is the same posterior as having held it from the start.
  - `observe(self, context: Context, candidate: Candidate, accepted: bool, *, unprompted: bool=False) -> None` (line 342; public) — One response: AD's assumed-density step in every bank, the grid weights by ``log Z``.
  - `summary(self) -> dict[str, Any]` (line 362; public) — Posterior means (grid-weighted) and the recovery grid's weights, for the decision row.
  - `priors_version(self) -> str` (line 375; public)
- `class Observation` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 385)
- `observations(decisions: Mapping[str, Mapping[str, Any]], responses: Iterable[Mapping[str, Any]]) -> list[Observation]` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 394) — The acceptance observations of a response ledger, in response order.
- `unprompted_observations(preferences: Iterable[Mapping[str, Any]], *, at: str | None=None, responses: Iterable[Mapping[str, Any]]=()) -> list[Observation]` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 437) — IH4 (spec_instruct_handoff_v1 §7 item 1): the learner's requests for a lesson as acceptance observations, oldest first, as of ``at``.
- `with_unprompted(observed: Sequence[Observation], requests: Sequence[Observation]) -> list[Observation]` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 469) — The responses and the requests in one order (by time; a tie keeps a response first).
- `replay(observed: Iterable[Observation]) -> AcceptanceState` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 476)
- `declines_by_learning_object(decisions: Mapping[str, Mapping[str, Any]], responses: Iterable[Mapping[str, Any]]) -> dict[str, str]` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 484) — Per LO, the time of its latest "Not now" not followed by an acceptance of a lesson on it.
- `class ScoredCandidate` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 516)
  - `as_dict(self) -> dict[str, Any]` (line 523; public)
- `class Target` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 529) — The drawn target: the router's design, its exact distribution over the scored candidates (0 off the support) and what it logs (``record``: enough to recompute ``pi``).
- `mixture_target(scored: Sequence[ScoredCandidate], *, weights: Mapping[str, float], epsilon: float, seed: str) -> Target` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 539) — ``router.mode = "mixture"``: the router's ``model_mixture`` over ``scored`` (the top ``k``).
- `tiebreak_target(scored: Sequence[ScoredCandidate], *, chosen_ref: str, tied: Sequence[str], margin: float) -> Target` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 569) — ``router.mode = "staged"``: the randomization layer's ``epsilon_tiebreak`` (the shell runs it).
- `class Draw` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 590) — The day's draw.
  - `arm_propensity(self) -> float` (line 612; public) — The arm's probability given the drawn target (1 when the ceiling binds).
  - `chosen_ref(self) -> str` (line 620; public)
- `score(state: AcceptanceState, context: Context, candidates: Sequence[Candidate], *, k: int) -> list[ScoredCandidate]` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 624) — Each candidate's ``P(accept)``, room and value; the top ``k`` by value (ties by ref).
- `seed_for(day: str, snapshot_hash: str) -> str` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 637)
- `draw(scored: Sequence[ScoredCandidate], *, target: Target, seed: str, ceiling_bound: bool=False) -> Draw` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 653) — The day's draw over ``scored`` (non-empty): the drawn ``target`` (its ``π``), then the show coin.
- `canonical_hash(value: Any) -> str` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 687)
- `days_between(later: Any, earlier: Any) -> float` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 692) — Days between two aware datetimes (never negative).

### Module constants

- `SUGGESTION_VERSION` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 76)
- `PRIORS_VERSION` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 78)
- `DECISION_KIND` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 79)
- `DESIGN` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 82)
- `TARGET_MIXTURE` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 84)
- `TARGET_TIEBREAK` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 85)
- `TARGET_DESIGNS` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 86)
- `MODELS_NOT_ASKED` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 88)
- `POLICY` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 89)
- `SURFACE` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 90)
- `CANDIDATE_KIND` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 91)
- `NO_SUGGESTION` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 93)
- `REASONS` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 94)
- `COLD_MISS_REASONS` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 102)
- `RESPONSES` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 103)
- `TERMS` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 110)
- `LEGACY_DAILY_SHOW` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 118)
- `LEGACY_DECLINED_SHOW` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 121)
- `LEGACY_CADENCE_DAYS` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 124)
- `PRIOR_SD` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 126)
- `UNPROMPTED_TERM` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 133)
- `UNPROMPTED_PRIORS_VERSION` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 134)
- `RECOVERY_DAYS_GRID` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 138)
- `CARD_MINUTES` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 141)
- `MAX_ALTERNATIVES` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 143)
- `_SECONDS_PER_DAY` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 145)
- `LESSON_KIND` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 429)
- `LESSON_INPUTS` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 430)
- `PHONE_SURFACES` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 432)
- `_ANSWERS` ([src/learnloop/router/lesson_suggestions.py](../../../../../../src/learnloop/router/lesson_suggestions.py), line 434)

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
- `COLD_MISS_REASONS`
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

- `_centre_for(target: float, variance: float) -> float` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 148) — The logit centre ``m`` with ``E[σ(N(m, variance))] = target`` (bisection; numerical resolution).
- `_prior_mean() -> np.ndarray` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 161) — The seeded centres: the prior predictive reproduces the legacy targets at the reference context.
- `class _Bank` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 179) — One recovery grid point's Gaussian over the effects.
- `_uniforms(seed: str) -> tuple[float, float, float]` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 641) — The draw's three uniforms from its seed: the mixture's two stages, then the show coin.
- `_propensity(p: float) -> tuple[float, str]` ([source](../../../../../../src/learnloop/router/lesson_suggestions.py), line 647)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/learner_action|learnloop.daily_plan.learner_action]] — imports `module`
- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `module`; statically calls `Context`, `days_between`, `declines_by_learning_object`, `observations`, `replay`, `score`, `unprompted_observations`, `with_unprompted`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `module`; statically calls `Candidate`, `Context`, `canonical_hash`, `days_between`, `declines_by_learning_object`, `draw`, `lesson_ref`, `mixture_target`, `observations`, `replay`, `score`, `seed_for`, `tiebreak_target`
- [[Reference/Modules/learnloop/router_objective/preferences|learnloop.router_objective.preferences]] — imports `module`; statically calls `_centre_for`

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

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/learner_action|learnloop.daily_plan.learner_action]], [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]], [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]], [[Reference/Modules/learnloop/router_objective/preferences|learnloop.router_objective.preferences]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/te3b_offers_helpers.py](../../../../../../tests/te3b_offers_helpers.py) — direct import
- [tests/teacher_te1b_suggestions_helpers.py](../../../../../../tests/teacher_te1b_suggestions_helpers.py) — direct import
- [tests/test_followups_batch6_review_fixes.py](../../../../../../tests/test_followups_batch6_review_fixes.py) — direct import
  - `test_f3_the_cli_labels_the_r_cold_comparison_with_observed_cold_outcomes`
- [tests/test_followups_batch6_router_report.py](../../../../../../tests/test_followups_batch6_router_report.py) — direct import
  - `test_router_report_prints_the_split_from_the_ledgers_read_only`
- [tests/test_ih2_lessons_compete.py](../../../../../../tests/test_ih2_lessons_compete.py) — direct import
  - `test_the_acceptance_model_never_reads_a_superseded_offer`
  - `test_the_journey_on_a_real_miss_lesson_then_not_now_then_the_question`
- [tests/test_ih2_offer_ceiling_and_unseen.py](../../../../../../tests/test_ih2_offer_ceiling_and_unseen.py) — direct import
- [tests/test_ih2_one_open_offer.py](../../../../../../tests/test_ih2_one_open_offer.py) — direct import
- [tests/test_ih4_preferences_inform_router.py](../../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
  - `test_a_learner_asked_lesson_reaches_p_accept_flagged_unprompted`
  - `test_a_request_is_flagged_and_moves_the_offer_only_through_its_posterior`
  - `test_a_row_written_with_the_switch_off_froze_nothing_and_is_not_read`
  - `test_at_w_pref_zero_only_the_acceptance_channel_moves_a_lesson_offers_value`
  - `test_choosing_the_offer_the_plan_drew_is_no_request`
  - `test_the_kinds_are_the_plans_own_names`
  - `test_the_more_offers_have_said_the_more_a_request_goes_to_its_own_offset`
  - `test_the_phone_surfaces_are_the_same_list_in_both_modules`
  - `test_the_requests_join_the_ledgers_order_and_a_tie_keeps_the_response_first`
  - `test_with_no_request_the_model_is_te1bs_exactly`
- [tests/test_ih_lesson_candidate_after_cold_miss.py](../../../../../../tests/test_ih_lesson_candidate_after_cold_miss.py) — direct import
  - `test_a_trivial_slip_and_a_severe_miss_are_both_candidates_and_differ_only_through_the_routers_evidence`
  - `test_the_renamed_reason_enters_the_acceptance_model_through_the_same_effect_with_its_history`
  - `test_the_words_name_the_latest_miss_and_survive_the_record`
- [tests/test_ro0_codex_review.py](../../../../../../tests/test_ro0_codex_review.py) — direct import
  - `test_f3_a_lesson_suggestion_keeps_its_ad_numbers_read_before_its_transaction`
- [tests/test_te3b_codex_review.py](../../../../../../tests/test_te3b_codex_review.py) — direct import
  - `test_f3_reopened_switch_off_decline_recovery_never_reads_an_offer_response`
  - `test_f3_with_the_switch_off_the_daily_draw_never_learns_from_offer_responses`
- [tests/test_te3b_offers.py](../../../../../../tests/test_te3b_offers.py) — direct import
  - `test_a_drawn_offer_is_a_block_answered_on_its_own_decision`
- [tests/test_te3b_value.py](../../../../../../tests/test_te3b_value.py) — direct import
  - `test_the_acceptance_posterior_is_moment_matched_to_a_beta`
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
