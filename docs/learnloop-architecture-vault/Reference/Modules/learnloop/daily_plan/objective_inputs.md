---
title: "learnloop.daily_plan.objective_inputs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/objective_inputs.py"
source_paths:
  - "src/learnloop/daily_plan/objective_inputs.py"
source_commit: "23b3b5d9482bdbd2652c8c50fb3e672f879d23f0"
source_commit_timestamp: "2026-11-05T21:28:04-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.objective_inputs module"
  - "src/learnloop/daily_plan/objective_inputs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.objective_inputs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.objective_inputs` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Router objective RO4 (spec §8.1, §8.4-§8.6): the frozen belief one block decision values its candidates on.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/objective_inputs.py](../../../../../../src/learnloop/daily_plan/objective_inputs.py) |
| Source lines | 573 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `23b3b5d9482bdbd2652c8c50fb3e672f879d23f0` |
| Commit timestamp | `2026-11-05T21:28:04-05:00` |

## Public API

- `plan_minutes(repository: Any, plan_id: str | None) -> tuple[float, str]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 55) — ``m̄`` and where it came from (the plan's remembered minutes: the learner's choice, carried, or a default).
- `population(vault: Any, repository: Any, now_iso: str) -> dict[str, float]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 259) — §8.7's population at ``now_iso`` with each LO's undated density: the active goals' scopes and the retention commitments (LOs with FSRS memory), never the candidates (RO5's checks draw over it, the traces' uses freeze it).
- `check_eligible_items(vault: Any, repository: Any, los: Sequence[str], exclude: Any=()) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 273) — RO5 §9 item 2's eligibility rule, per LO in id order: unseen (never attempted), unrevealed (no reveal row at all), unassisted so far (no help row), not exam-reserved, held out or protected, nor in any routine serving exclusion, and servable (the delayed checks' candidate rule).
- `check_sensors(vault: Any, repository: Any, lo: str, now_iso: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 300) — RO5: a topic's sensors at a randomized check's administration (§9 item 7: the combiner is fitted on these against the check's outcome): AD's predictive on the logit scale and the FSRS retrievability of the LO's practised items (the decisions' own reads).
- `action_for(vault: Any, repository: Any, candidate: BlockCandidate, *, practiced: set[str], spread: float) -> V.Action` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 395) — §8.1's interface for one candidate block.
- `build(vault: Any, repository: Any, *, state: PlanState, support: Sequence[str], candidates: Mapping[str, BlockCandidate], now_iso: str, kappa0: float=0.0, kappa_how: str='unset', sequences: Mapping[str, Sequence[BlockCandidate]] | None=None) -> tuple[V.Inputs, list[V.Action], dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 435) — The decision's frozen inputs, its actions in support order, and the sources the trace records.

### Module constants

- `LOG` ([src/learnloop/daily_plan/objective_inputs.py](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 36)
- `TOPIC_LIMIT` ([src/learnloop/daily_plan/objective_inputs.py](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 39)
- `RETURN_GAP_LIMIT` ([src/learnloop/daily_plan/objective_inputs.py](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 41)
- `DURATION_LIMIT` ([src/learnloop/daily_plan/objective_inputs.py](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 42)
- `_PROBE_MODES` ([src/learnloop/daily_plan/objective_inputs.py](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 43)

### Explicit exports

`__all__` declares:

- `DURATION_LIMIT`
- `RETURN_GAP_LIMIT`
- `TOPIC_LIMIT`
- `action_for`
- `build`
- `plan_minutes`

## Internal implementation anchors

- `_logit(p: float) -> float` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 46)
- `_days(later: datetime, earlier: datetime) -> float` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 51)
- `_goal_uses(vault: Any, repository: Any, now: datetime) -> tuple[dict[str, float], list[V.DatedUse], dict[str, Any], list[str]]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 67)
- `_practiced(connection: Any, vault: Any) -> tuple[dict[str, list[dict[str, Any]]], list[str]]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 96)
- `_mastery(connection: Any, los: Sequence[str]) -> dict[str, tuple[float, float]]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 113)
- `_ad(vault: Any, repository: Any, los: Sequence[str], *, learning_moments: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 122)
- `_return_gaps(connection: Any, gap_minutes: float) -> list[float]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 135)
- `_stop_accept(connection: Any, prior: tuple[float, float]) -> tuple[tuple[float, float], dict[str, int]]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 147) — §4 row 7: an offered stop the learner took (an end, ``offered_stop_accepted``) or overrode (a ``stop_response``); Beta(a + taken, b + overridden).
- `_learning(ad: Mapping[str, Any], fitted: bool, gamma_prior: Any, reading_priors: Any, dose_scales: Any) -> V.Learning` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 165) — AD's learning parameters for the rollouts: RO4's prior means and variances, or (RO5 §9 item 7, at the tag with ``fitted_models``) the subject view's fitted posterior moments of ``γ`` and the reading curve, each parameter falling back to its prior where AD has none.
- `_combiner(repository: Any, now_iso: str, vault: Any=None) -> M.Combiner` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 185) — RO5 §9 item 7: the memory model's Bayesian logistic combination fitted on resolved randomized checks (each check's sensors frozen at its administration against §6.2's label); with none resolved, the labelled prior.
- `_combiner_with_traces(vault: Any, repository: Any, now_iso: str, check_rows: list[tuple[float, Any, int]], check_attempts: set[str]) -> M.Combiner` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 218) — The follow-up batch's item 2 (RO4's item 6): the checks' rows plus the traces' frozen sensors joined to resolved cold outcomes (``router_objective.combiner_data``: RO2's resolver, per protocol, as of ``now_iso`` through the availability predicate), refitted with the labelled pri…
- `_return_model(connection: Any, config: Any) -> tuple[tuple[float, float] | None, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 330) — RO5 §9 item 1: stop's return model, from the sessions a stop coin was drawn in.
- `_duration_spread(connection: Any) -> tuple[float, int]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 354) — The pooled spread of the learner's own durations on the log scale (none observed: 0, the mean only).
- `_reading_los(vault: Any, repository: Any, candidate: BlockCandidate) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 365)
- `_reading_los_outside_ad(vault: Any, repository: Any, reading: Any) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 385) — AD off: no AD operation, no reading curve; the plan's own mapping (the raw-loading wrapper, as every caller outside AD).
- `_step(action: V.Action) -> V.Action` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 428) — A block as one step of a sequence: a probe step is its observation alone (what follows it in the sequence, then the tail, is what uses the information), never a nested repair bundle.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `check_eligible_items`, `check_sensors`, `population`
- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `build`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]] — imports `resolve_curves`; calls `resolve_curves`
- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `COLD_START_VARIANCE`, `DOSE_SCALES`, `GAMMA_PRIOR`, `READING_PRIORS`
- [[Reference/Modules/learnloop/adaptive_difficulty/readiness|learnloop.adaptive_difficulty.readiness]] — imports `decision_state_fields`; calls `decision_state_fields`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `section_learning_objects`; calls `section_learning_objects`
- [[Reference/Modules/learnloop/adaptive_difficulty/switches|learnloop.adaptive_difficulty.switches]] — imports `ad_enabled`; calls `ad_enabled`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `BlockCandidate`, `PlanState`, `STOP_FOR_TODAY`
- [[Reference/Modules/learnloop/delayed_checks|learnloop.delayed_checks]] — imports `module`; calls `candidates`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `resolve_goal_scope`; calls `resolve_goal_scope`
- [[Reference/Modules/learnloop/goals/use_weights|learnloop.goals.use_weights]] — imports `for_goal`; calls `for_goal`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `withheld_items`; calls `withheld_items`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_fsrs_weights`; calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]] — imports `module`; calls `resolve`
- [[Reference/Modules/learnloop/router_objective/combiner_data|learnloop.router_objective.combiner_data]] — imports `module`; calls `groups`, `rows`
- [[Reference/Modules/learnloop/router_objective/memory|learnloop.router_objective.memory]] — imports `module`; calls `Combiner`, `Fsrs`, `fit_combiner`
- [[Reference/Modules/learnloop/router_objective/price|learnloop.router_objective.price]] — imports `module`; calls `session_active_minutes`
- [[Reference/Modules/learnloop/router_objective/stop_coin|learnloop.router_objective.stop_coin]] — imports `module`; calls `fit_return_slope`, `return_rows`
- [[Reference/Modules/learnloop/router_objective/value|learnloop.router_objective.value]] — imports `module`; calls `Action`, `DatedUse`, `Inputs`, `Learning`, `Price`, `Topic`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `fitted_models_on`, `followup_on`, `followups_tag`, `known_at`, `stop_coin_rate`; calls `fitted_models_on`, `followup_on`, `followups_tag`, `known_at`, `stop_coin_rate`
- [[Reference/Modules/learnloop/scheduling/serving_exclusions|learnloop.scheduling.serving_exclusions]] — imports `routine_serving_exclusions`; calls `routine_serving_exclusions`
- [[Reference/Modules/learnloop/section_map|learnloop.section_map]] — imports `learning_objects_for_section`; calls `learning_objects_for_section`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `json`, `logging`, `math`, `statistics`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro2_ad_raw_document_reads.py](../../../../../../tests/test_ro2_ad_raw_document_reads.py) — direct import
  - `test_ro4s_reading_action_maps_its_section_through_the_chokepoint`
- [tests/test_ro4_codex_review.py](../../../../../../tests/test_ro4_codex_review.py) — direct import
  - `test_f8_a_reading_candidate_starts_from_ads_dose_position`
- [tests/test_ro5_calibration.py](../../../../../../tests/test_ro5_calibration.py) — direct import
  - `test_the_combiner_is_fitted_on_resolved_checks_and_is_its_prior_with_none`
  - `test_the_rollouts_read_ads_fitted_learning_posterior_at_the_tag_and_priors_otherwise`
- [tests/test_ro5_checks.py](../../../../../../tests/test_ro5_checks.py) — direct import
  - `test_a_topic_with_no_eligible_item_has_r_zero_and_raises_a_generation_need`
  - `test_no_protected_or_exam_reserved_item_is_ever_eligible`
  - `test_off_draws_nothing_and_a_day_with_no_session_counts_toward_the_completion_gap`
- [tests/test_rofu_learning.py](../../../../../../tests/test_rofu_learning.py) — direct import
  - `test_below_the_tag_the_combiner_reads_no_trace`
  - `test_the_combiner_is_fitted_on_trace_outcomes_at_the_tag_and_the_trace_names_it`
- [tests/test_rofu_weeks.py](../../../../../../tests/test_rofu_weeks.py) — direct import
  - `test_two_weeks_before_and_after_the_batch`

## Modification guidance

- Make changes here when the responsibility remains objective inputs within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/objective_inputs.py](../../../../../../src/learnloop/daily_plan/objective_inputs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
